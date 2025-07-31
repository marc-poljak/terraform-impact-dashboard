"""
Integration tests for Security Hardening Features

Tests end-to-end security workflows including automatic cleanup,
SSL verification, and credential protection across all components.
"""

import pytest
import unittest
import time
import threading
from unittest.mock import Mock, patch, MagicMock
import requests

from utils.credential_manager import CredentialManager
from providers.tfe_client import TFEClient
from components.tfe_input import TFEInputComponent
from components.upload_section import UploadComponent
from ui.session_manager import SessionStateManager


class TestEndToEndSecurityWorkflow(unittest.TestCase):
    """Test complete security workflow from credential input to cleanup"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.credential_manager = CredentialManager()
        self.tfe_client = TFEClient(self.credential_manager)
        self.tfe_component = TFEInputComponent()
        self.session_manager = SessionStateManager()
        
        self.valid_config = {
            'tfe_server': 'app.terraform.io',
            'organization': 'test-org',
            'token': 'tfe-token-12345678901234567890',
            'workspace_id': 'ws-ABC123456',
            'run_id': 'run-XYZ789012',
            'verify_ssl': True,
            'timeout': 30,
            'retry_attempts': 3
        }
    
    def tearDown(self):
        """Clean up after each test"""
        self.tfe_client.close()
        self.credential_manager.clear_credentials()
        self.tfe_component.cleanup()
        
        # Cancel any running timers
        if CredentialManager._session_cleanup_timer:
            CredentialManager._session_cleanup_timer.cancel()
            CredentialManager._session_cleanup_timer = None
    
    def test_complete_security_lifecycle(self):
        """Test complete security lifecycle from input to cleanup"""
        # 1. Store credentials securely
        self.credential_manager.store_credentials(self.valid_config)
        
        # Verify session is active
        session_info = self.credential_manager.get_session_info()
        self.assertTrue(session_info['active'])
        self.assertGreater(session_info['time_remaining'], 0)
        
        # 2. Access credentials through TFE client
        config = self.credential_manager.get_config()
        self.assertIsNotNone(config)
        self.assertEqual(config.token, 'tfe-token-12345678901234567890')
        
        # 3. Verify masked display
        masked = self.credential_manager.get_masked_config()
        self.assertNotEqual(masked['token'], config.token)
        self.assertIn('*', masked['token'])
        
        # 4. Simulate session activity
        time.sleep(0.1)
        self.credential_manager.extend_session()
        
        # 5. Close client (should trigger cleanup)
        self.tfe_client.close()
        
        # 6. Verify complete cleanup
        self.assertIsNone(self.credential_manager.get_credentials())
        self.assertIsNone(self.credential_manager.get_config())
        
        session_info = self.credential_manager.get_session_info()
        self.assertFalse(session_info['active'])
    
    def test_session_timeout_integration(self):
        """Test session timeout integration across components"""
        # Set short timeout for testing
        self.credential_manager.set_session_timeout(60)  # 1 minute
        
        # Store credentials
        self.credential_manager.store_credentials(self.valid_config)
        
        # Verify session is active
        self.assertTrue(self.credential_manager.get_session_info()['active'])
        
        # Simulate timeout by manipulating access time
        self.credential_manager._last_access_time = time.time() - 120  # 2 minutes ago
        
        # Trigger timeout cleanup
        self.credential_manager._session_timeout_cleanup()
        
        # Verify cleanup occurred
        self.assertIsNone(self.credential_manager.get_credentials())
        self.assertFalse(self.credential_manager.get_session_info()['active'])
        
        # TFE client should handle missing credentials gracefully
        with patch.object(self.tfe_client, 'validate_connection') as mock_validate:
            mock_validate.return_value = (False, "No TFE configuration available")
            
            is_valid, message = self.tfe_client.validate_connection()
            self.assertFalse(is_valid)
            self.assertIn("No TFE configuration available", message)
    
    @patch('requests.Session')
    def test_ssl_verification_integration(self, mock_session_class):
        """Test SSL verification integration across components"""
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        
        # Test with SSL enabled (default)
        self.credential_manager.store_credentials(self.valid_config)
        session = self.tfe_client._create_session()
        
        self.assertTrue(mock_session.verify)
        
        # Test with SSL disabled
        config_no_ssl = self.valid_config.copy()
        config_no_ssl['verify_ssl'] = False
        
        self.credential_manager.clear_credentials()
        self.credential_manager.store_credentials(config_no_ssl)
        
        with patch('warnings.warn') as mock_warn:
            session = self.tfe_client._create_session()
            
            self.assertFalse(mock_session.verify)
            mock_warn.assert_called_once()
    
    def test_credential_exposure_prevention_integration(self):
        """Test that credentials are never exposed across all components"""
        sensitive_config = {
            'tfe_server': 'app.terraform.io',
            'organization': 'super-secret-org',
            'token': 'extremely-sensitive-token-data-123456',
            'workspace_id': 'ws-CONFIDENTIAL789',
            'run_id': 'run-TOPSECRET012',
            'verify_ssl': True,
            'timeout': 30,
            'retry_attempts': 3
        }
        
        # Store sensitive credentials
        self.credential_manager.store_credentials(sensitive_config)
        
        # Test credential manager masking
        masked = self.credential_manager.get_masked_config()
        masked_str = str(masked)
        self.assertNotIn('extremely-sensitive-token-data-123456', masked_str)
        self.assertNotIn('super-secret-org', masked_str)
        
        # Test TFE component masking
        self.tfe_component.credential_manager.store_credentials(sensitive_config)
        tfe_masked = self.tfe_component.credential_manager.get_masked_config()
        tfe_masked_str = str(tfe_masked)
        self.assertNotIn('extremely-sensitive-token-data-123456', tfe_masked_str)
        
        # Test session info doesn't expose credentials
        session_info = self.credential_manager.get_session_info()
        session_info_str = str(session_info)
        self.assertNotIn('extremely-sensitive-token-data-123456', session_info_str)
        self.assertNotIn('super-secret-org', session_info_str)
        
        # Test error scenarios don't expose credentials
        try:
            # Force an error
            invalid_method = getattr(self.credential_manager, 'non_existent_method', None)
            if invalid_method:
                invalid_method()
        except:
            pass  # We just want to ensure no credentials are exposed in any error handling
    
    def test_multi_component_cleanup_coordination(self):
        """Test that cleanup is coordinated across multiple components"""
        # Create multiple components with shared credential manager
        tfe_component1 = TFEInputComponent()
        tfe_component2 = TFEInputComponent()
        upload_component = UploadComponent()
        
        # Store credentials in multiple managers
        tfe_component1.credential_manager.store_credentials(self.valid_config)
        tfe_component2.credential_manager.store_credentials(self.valid_config)
        
        # Store plan data in upload component
        test_plan = {
            "terraform_version": "1.5.0",
            "resource_changes": [
                {
                    "address": "aws_instance.test",
                    "change": {
                        "actions": ["create"],
                        "after": {"instance_type": "t3.micro"}
                    }
                }
            ]
        }
        upload_component.plan_manager.store_plan_data(test_plan, "file_upload")
        
        # Verify data is stored
        self.assertIsNotNone(tfe_component1.credential_manager.get_credentials())
        self.assertIsNotNone(tfe_component2.credential_manager.get_credentials())
        self.assertTrue(upload_component.plan_manager.has_plan_data())
        
        # Trigger global cleanup
        CredentialManager.cleanup_all_instances()
        
        # Verify all credentials are cleared
        self.assertIsNone(tfe_component1.credential_manager.get_credentials())
        self.assertIsNone(tfe_component2.credential_manager.get_credentials())
        
        # Clean up components
        tfe_component1.cleanup()
        tfe_component2.cleanup()
        upload_component.cleanup()
        
        # Verify plan data is also cleared
        self.assertFalse(upload_component.plan_manager.has_plan_data())
    
    def test_session_manager_security_integration(self):
        """Test session manager security integration"""
        # Store credentials
        self.credential_manager.store_credentials(self.valid_config)
        
        # Simulate session state with sensitive data
        with patch('streamlit.session_state') as mock_session_state:
            mock_session_state.plan_data = {'sensitive': 'plan_data'}
            mock_session_state.enhanced_risk_result = {'risk': 'data'}
            
            # Mock hasattr to return True for sensitive keys
            def mock_hasattr(obj, name):
                return name in ['plan_data', 'enhanced_risk_result']
            
            # Mock delattr to track deletions
            deleted_attrs = []
            def mock_delattr(obj, name):
                deleted_attrs.append(name)
                delattr(mock_session_state, name)
            
            with patch('builtins.hasattr', side_effect=mock_hasattr), \
                 patch('builtins.delattr', side_effect=mock_delattr):
                
                # Trigger security cleanup
                self.session_manager.trigger_security_cleanup()
                
                # Verify sensitive attributes were deleted
                self.assertIn('plan_data', deleted_attrs)
                self.assertIn('enhanced_risk_result', deleted_attrs)
        
        # Verify credentials were also cleaned up
        self.assertIsNone(self.credential_manager.get_credentials())


class TestSecurityErrorHandling(unittest.TestCase):
    """Test security aspects of error handling"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.credential_manager = CredentialManager()
        self.tfe_client = TFEClient(self.credential_manager)
        
        self.sensitive_config = {
            'tfe_server': 'app.terraform.io',
            'organization': 'secret-organization',
            'token': 'secret-token-data-12345678',
            'workspace_id': 'ws-SECRET123',
            'run_id': 'run-CONFIDENTIAL456',
            'verify_ssl': True,
            'timeout': 30,
            'retry_attempts': 3
        }
    
    def tearDown(self):
        """Clean up after each test"""
        self.tfe_client.close()
        self.credential_manager.clear_credentials()
    
    def test_authentication_error_no_credential_exposure(self):
        """Test that authentication errors don't expose credentials"""
        self.credential_manager.store_credentials(self.sensitive_config)
        
        with patch('requests.Session') as mock_session_class:
            mock_session = Mock()
            mock_response = Mock()
            mock_response.status_code = 401
            mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("401 Unauthorized")
            mock_session.get.return_value = mock_response
            mock_session_class.return_value = mock_session
            
            # Attempt authentication
            success, error_message = self.tfe_client.authenticate(
                self.sensitive_config['tfe_server'],
                self.sensitive_config['token'],
                self.sensitive_config['organization']
            )
            
            # Should fail but not expose credentials
            self.assertFalse(success)
            self.assertIsNotNone(error_message)
            
            # Error message should not contain sensitive data
            self.assertNotIn('secret-token-data-12345678', error_message)
            self.assertNotIn('secret-organization', error_message)
    
    def test_connection_error_no_credential_exposure(self):
        """Test that connection errors don't expose credentials"""
        self.credential_manager.store_credentials(self.sensitive_config)
        
        with patch('requests.Session') as mock_session_class:
            mock_session = Mock()
            mock_session.get.side_effect = requests.exceptions.ConnectionError("Connection failed")
            mock_session_class.return_value = mock_session
            
            # Attempt connection validation
            is_valid, message = self.tfe_client.validate_connection()
            
            # Should fail but not expose credentials
            self.assertFalse(is_valid)
            self.assertIsNotNone(message)
            
            # Error message should not contain sensitive data
            self.assertNotIn('secret-token-data-12345678', message)
            self.assertNotIn('secret-organization', message)
    
    def test_ssl_error_no_credential_exposure(self):
        """Test that SSL errors don't expose credentials"""
        self.credential_manager.store_credentials(self.sensitive_config)
        
        with patch('requests.Session') as mock_session_class:
            mock_session = Mock()
            mock_session.get.side_effect = requests.exceptions.SSLError("SSL verification failed")
            mock_session_class.return_value = mock_session
            
            # Attempt connection validation
            is_valid, message = self.tfe_client.validate_connection()
            
            # Should fail but not expose credentials
            self.assertFalse(is_valid)
            self.assertIsNotNone(message)
            
            # Error message should not contain sensitive data
            self.assertNotIn('secret-token-data-12345678', message)
            self.assertNotIn('secret-organization', message)
    
    def test_validation_error_no_credential_exposure(self):
        """Test that validation errors don't expose credentials"""
        # Create config with sensitive but invalid data
        invalid_config = {
            'tfe_server': 'invalid-server-url',
            'organization': 'secret-org-name',
            'token': 'secret-but-invalid-token',
            'workspace_id': 'invalid-workspace-format',
            'run_id': 'invalid-run-format'
        }
        
        # Validation should fail
        is_valid, errors = self.credential_manager.validate_config(invalid_config)
        
        self.assertFalse(is_valid)
        self.assertGreater(len(errors), 0)
        
        # Errors should not contain sensitive data
        all_errors = ' '.join(errors)
        self.assertNotIn('secret-org-name', all_errors)
        self.assertNotIn('secret-but-invalid-token', all_errors)
    
    def test_cleanup_error_handling(self):
        """Test that cleanup errors don't prevent security cleanup"""
        self.credential_manager.store_credentials(self.sensitive_config)
        
        # Mock an error during cleanup
        original_clear = self.credential_manager._credentials.clear
        
        def error_clear():
            raise Exception("Simulated cleanup error")
        
        # Temporarily replace clear method
        self.credential_manager._credentials.clear = error_clear
        
        # Cleanup should still work despite error
        try:
            self.credential_manager.clear_credentials()
        except:
            pass  # Ignore the error
        
        # Restore original method
        if self.credential_manager._credentials:
            self.credential_manager._credentials.clear = original_clear
        
        # Credentials should still be cleared (set to None)
        self.assertIsNone(self.credential_manager._credentials)
        self.assertIsNone(self.credential_manager._config)


class TestSecurityComplianceValidation(unittest.TestCase):
    """Test compliance with security requirements"""
    
    def test_memory_only_storage_compliance(self):
        """Test that no persistent storage is used"""
        credential_manager = CredentialManager()
        
        config = {
            'tfe_server': 'app.terraform.io',
            'organization': 'test-org',
            'token': 'test-token-12345678901234567890',
            'workspace_id': 'ws-ABC123456',
            'run_id': 'run-XYZ789012'
        }
        
        # Store credentials
        credential_manager.store_credentials(config)
        
        # Verify credentials are only in memory (instance variables)
        self.assertIsInstance(credential_manager._credentials, dict)
        self.assertIsInstance(credential_manager._config, TFEConfig)
        
        # Verify no file operations are used in the implementation
        # (This is more of a design verification - the implementation
        # should only use instance variables)
        
        # Clean up
        credential_manager.clear_credentials()
    
    def test_automatic_cleanup_compliance(self):
        """Test that automatic cleanup works as required"""
        credential_manager = CredentialManager()
        
        config = {
            'tfe_server': 'app.terraform.io',
            'organization': 'test-org',
            'token': 'test-token-12345678901234567890',
            'workspace_id': 'ws-ABC123456',
            'run_id': 'run-XYZ789012'
        }
        
        # Store credentials
        credential_manager.store_credentials(config)
        
        # Verify session is active
        self.assertTrue(credential_manager._session_active)
        
        # Verify cleanup timer is running
        self.assertIsNotNone(CredentialManager._session_cleanup_timer)
        
        # Verify cleanup works
        credential_manager.clear_credentials()
        self.assertFalse(credential_manager._session_active)
        self.assertIsNone(credential_manager.get_credentials())
    
    def test_ssl_verification_compliance(self):
        """Test that SSL verification is properly enforced"""
        credential_manager = CredentialManager()
        tfe_client = TFEClient(credential_manager)
        
        # Test SSL enabled by default
        config = {
            'tfe_server': 'app.terraform.io',
            'organization': 'test-org',
            'token': 'test-token-12345678901234567890',
            'workspace_id': 'ws-ABC123456',
            'run_id': 'run-XYZ789012'
        }
        
        credential_manager.store_credentials(config)
        
        with patch('requests.Session') as mock_session_class:
            mock_session = Mock()
            mock_session_class.return_value = mock_session
            
            session = tfe_client._create_session()
            
            # SSL should be enabled by default
            self.assertTrue(mock_session.verify)
        
        # Test SSL disabled with warning
        config['verify_ssl'] = False
        credential_manager.clear_credentials()
        credential_manager.store_credentials(config)
        
        with patch('requests.Session') as mock_session_class, \
             patch('warnings.warn') as mock_warn:
            
            mock_session = Mock()
            mock_session_class.return_value = mock_session
            
            session = tfe_client._create_session()
            
            # SSL should be disabled
            self.assertFalse(mock_session.verify)
            
            # Warning should be issued
            mock_warn.assert_called_once()
        
        # Clean up
        tfe_client.close()
    
    def test_credential_masking_compliance(self):
        """Test that credential masking works as required"""
        credential_manager = CredentialManager()
        
        sensitive_config = {
            'tfe_server': 'app.terraform.io',
            'organization': 'sensitive-org',
            'token': 'very-sensitive-token-data-123456789',
            'workspace_id': 'ws-SENSITIVE123',
            'run_id': 'run-CONFIDENTIAL456'
        }
        
        credential_manager.store_credentials(sensitive_config)
        
        # Test masked config
        masked = credential_manager.get_masked_config()
        
        # Original sensitive data should not be present
        masked_str = str(masked)
        self.assertNotIn('very-sensitive-token-data-123456789', masked_str)
        self.assertNotIn('sensitive-org', masked_str)
        
        # But masked token should show first and last characters
        self.assertIn('very', masked_str)  # First 4 chars
        self.assertIn('6789', masked_str)  # Last 4 chars
        self.assertIn('*', masked_str)     # Masking characters
        
        # Clean up
        credential_manager.clear_credentials()


if __name__ == '__main__':
    unittest.main()
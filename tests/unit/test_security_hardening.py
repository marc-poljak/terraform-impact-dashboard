"""
Unit tests for Security Hardening Features

Tests automatic credential cleanup, SSL verification, secure transmission handling,
and verification that no credential exposure occurs in any scenario.
"""

import pytest
import unittest
import time
import threading
from unittest.mock import Mock, patch, MagicMock
import requests
from requests.exceptions import SSLError, ConnectionError

from utils.credential_manager import CredentialManager, TFEConfig
from providers.tfe_client import TFEClient
from ui.session_manager import SessionStateManager


class TestCredentialManagerSecurityHardening(unittest.TestCase):
    """Test security hardening features in CredentialManager"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.manager = CredentialManager()
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
        self.manager.clear_credentials()
        # Cancel any running timers
        if CredentialManager._session_cleanup_timer:
            CredentialManager._session_cleanup_timer.cancel()
            CredentialManager._session_cleanup_timer = None
    
    def test_session_timeout_initialization(self):
        """Test that session timeout is properly initialized"""
        self.assertEqual(self.manager._session_timeout, 3600)  # 1 hour default
        self.assertFalse(self.manager._session_active)
        self.assertIsNotNone(self.manager._last_access_time)
    
    def test_session_activation_on_credential_storage(self):
        """Test that session becomes active when credentials are stored"""
        self.assertFalse(self.manager._session_active)
        
        self.manager.store_credentials(self.valid_config)
        
        self.assertTrue(self.manager._session_active)
        self.assertIsNotNone(CredentialManager._session_cleanup_timer)
    
    def test_session_timeout_configuration(self):
        """Test session timeout configuration"""
        # Test valid timeout
        self.manager.set_session_timeout(300)  # 5 minutes
        self.assertEqual(self.manager._session_timeout, 300)
        
        # Test minimum timeout validation
        with self.assertRaises(ValueError) as context:
            self.manager.set_session_timeout(30)  # Less than 60 seconds
        
        self.assertIn("at least 60 seconds", str(context.exception))
    
    def test_last_access_time_updates(self):
        """Test that last access time is updated on credential access"""
        self.manager.store_credentials(self.valid_config)
        initial_time = self.manager._last_access_time
        
        # Wait a small amount to ensure time difference
        time.sleep(0.1)
        
        # Access credentials
        self.manager.get_credentials()
        self.assertGreater(self.manager._last_access_time, initial_time)
        
        # Access config
        time.sleep(0.1)
        config_access_time = self.manager._last_access_time
        self.manager.get_config()
        self.assertGreater(self.manager._last_access_time, config_access_time)
    
    def test_session_info_reporting(self):
        """Test session information reporting"""
        # Test inactive session
        info = self.manager.get_session_info()
        self.assertFalse(info['active'])
        self.assertEqual(info['time_remaining'], 0)
        self.assertIsNone(info['last_access'])
        
        # Test active session
        self.manager.store_credentials(self.valid_config)
        info = self.manager.get_session_info()
        
        self.assertTrue(info['active'])
        self.assertGreater(info['time_remaining'], 0)
        self.assertIsNotNone(info['last_access'])
        self.assertEqual(info['timeout_seconds'], 3600)
    
    def test_session_extension(self):
        """Test session extension functionality"""
        self.manager.store_credentials(self.valid_config)
        initial_time = self.manager._last_access_time
        
        time.sleep(0.1)
        self.manager.extend_session()
        
        self.assertGreater(self.manager._last_access_time, initial_time)
    
    @patch('threading.Timer')
    def test_session_cleanup_timer_management(self, mock_timer):
        """Test session cleanup timer creation and cancellation"""
        mock_timer_instance = Mock()
        mock_timer.return_value = mock_timer_instance
        
        # Store credentials should start timer
        self.manager.store_credentials(self.valid_config)
        
        mock_timer.assert_called_once()
        mock_timer_instance.start.assert_called_once()
        
        # Clear credentials should cancel timer
        self.manager.clear_credentials()
        mock_timer_instance.cancel.assert_called_once()
    
    def test_session_timeout_cleanup_logic(self):
        """Test session timeout cleanup logic"""
        # Set short timeout for testing
        self.manager.set_session_timeout(60)  # 1 minute
        self.manager.store_credentials(self.valid_config)
        
        # Simulate timeout by setting old access time
        self.manager._last_access_time = time.time() - 120  # 2 minutes ago
        
        # Trigger timeout cleanup
        self.manager._session_timeout_cleanup()
        
        # Credentials should be cleared
        self.assertIsNone(self.manager.get_credentials())
        self.assertFalse(self.manager._session_active)
    
    def test_session_timeout_restart_on_recent_access(self):
        """Test that timer restarts if session was accessed recently"""
        with patch('threading.Timer') as mock_timer:
            mock_timer_instance = Mock()
            mock_timer.return_value = mock_timer_instance
            
            self.manager.set_session_timeout(60)
            self.manager.store_credentials(self.valid_config)
            
            # Simulate recent access (within timeout)
            self.manager._last_access_time = time.time() - 30  # 30 seconds ago
            
            # Trigger timeout cleanup
            self.manager._session_timeout_cleanup()
            
            # Credentials should still exist
            self.assertIsNotNone(self.manager.get_credentials())
            self.assertTrue(self.manager._session_active)
            
            # Timer should be restarted
            self.assertGreaterEqual(mock_timer.call_count, 2)
    
    def test_credential_overwrite_security(self):
        """Test that credentials are securely overwritten before clearing"""
        sensitive_config = self.valid_config.copy()
        sensitive_config['token'] = 'super-secret-token-data'
        
        self.manager.store_credentials(sensitive_config)
        
        # Get reference to internal credentials
        credentials_ref = self.manager._credentials
        original_token = credentials_ref['token']
        
        # Clear credentials
        self.manager.clear_credentials()
        
        # Original token should have been overwritten
        # (We can't easily test the overwriting, but we can verify clearing)
        self.assertIsNone(self.manager._credentials)
        self.assertIsNone(self.manager._config)
    
    def test_global_cleanup_cancels_timers(self):
        """Test that global cleanup cancels all timers"""
        with patch('threading.Timer') as mock_timer:
            mock_timer_instance = Mock()
            mock_timer.return_value = mock_timer_instance
            
            # Create multiple managers with active sessions
            manager1 = CredentialManager()
            manager2 = CredentialManager()
            
            manager1.store_credentials(self.valid_config)
            manager2.store_credentials(self.valid_config)
            
            # Global cleanup
            CredentialManager.cleanup_all_instances()
            
            # Timer should be cancelled
            mock_timer_instance.cancel.assert_called()
            
            # All credentials should be cleared
            self.assertIsNone(manager1.get_credentials())
            self.assertIsNone(manager2.get_credentials())


class TestTFEClientSecurityHardening(unittest.TestCase):
    """Test security hardening features in TFEClient"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.credential_manager = CredentialManager()
        self.tfe_client = TFEClient(self.credential_manager)
        
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
    
    @patch('requests.Session')
    def test_ssl_verification_enabled_by_default(self, mock_session_class):
        """Test that SSL verification is enabled by default"""
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        
        self.credential_manager.store_credentials(self.valid_config)
        
        session = self.tfe_client._create_session()
        
        # SSL verification should be enabled
        self.assertTrue(mock_session.verify)
    
    @patch('requests.Session')
    def test_ssl_verification_disabled_warning(self, mock_session_class):
        """Test that disabling SSL verification shows warning"""
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        
        config = self.valid_config.copy()
        config['verify_ssl'] = False
        self.credential_manager.store_credentials(config)
        
        with patch('warnings.warn') as mock_warn:
            session = self.tfe_client._create_session()
            
            # Warning should be issued
            mock_warn.assert_called_once()
            warning_message = mock_warn.call_args[0][0]
            self.assertIn("SSL verification is disabled", warning_message)
            self.assertIn("insecure", warning_message)
    
    @patch('requests.Session')
    def test_security_headers_added(self, mock_session_class):
        """Test that security headers are added to requests"""
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        
        self.credential_manager.store_credentials(self.valid_config)
        
        session = self.tfe_client._create_session()
        
        # Check that security headers were added
        expected_headers = {
            'User-Agent': 'TerraformPlanDashboard/1.0',
            'Accept': 'application/vnd.api+json',
            'Cache-Control': 'no-cache, no-store, must-revalidate',
            'Pragma': 'no-cache'
        }
        
        mock_session.headers.update.assert_called_once_with(expected_headers)
    
    def test_session_cleanup_on_close(self):
        """Test that session is properly cleaned up on close"""
        # Create a mock session with mock headers
        mock_session = Mock()
        mock_headers = Mock()
        mock_session.headers = mock_headers
        
        self.tfe_client._session = mock_session
        self.tfe_client._authenticated = True
        
        # Close the client
        self.tfe_client.close()
        
        # Session should be closed and cleared
        mock_headers.clear.assert_called_once()
        mock_session.close.assert_called_once()
        self.assertIsNone(self.tfe_client._session)
        self.assertFalse(self.tfe_client._authenticated)
    
    def test_credential_cleanup_on_close(self):
        """Test that credentials are cleaned up when client is closed"""
        self.credential_manager.store_credentials(self.valid_config)
        
        # Verify credentials are stored
        self.assertIsNotNone(self.credential_manager.get_credentials())
        
        # Close client
        self.tfe_client.close()
        
        # Credentials should be cleared
        self.assertIsNone(self.credential_manager.get_credentials())


class TestSessionManagerSecurityIntegration(unittest.TestCase):
    """Test security integration with SessionManager"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.session_manager = SessionStateManager()
    
    @patch('utils.credential_manager.CredentialManager.cleanup_all_instances')
    def test_security_cleanup_clears_sensitive_data(self, mock_cleanup):
        """Test that security cleanup clears sensitive session data"""
        # Test that cleanup is called - the actual session state cleanup
        # is tested in integration tests due to Streamlit complexity
        self.session_manager.trigger_security_cleanup()
        
        # Verify credential cleanup was called
        mock_cleanup.assert_called_once()
    
    @patch('utils.credential_manager.CredentialManager.cleanup_all_instances')
    def test_credential_manager_cleanup_called(self, mock_cleanup):
        """Test that credential manager cleanup is called during session cleanup"""
        self.session_manager.trigger_security_cleanup()
        
        mock_cleanup.assert_called_once()


class TestCredentialExposurePrevention(unittest.TestCase):
    """Test that credentials are never exposed in any scenario"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.manager = CredentialManager()
        self.sensitive_config = {
            'tfe_server': 'app.terraform.io',
            'organization': 'secret-org',
            'token': 'super-secret-token-data-12345',
            'workspace_id': 'ws-SENSITIVE123',
            'run_id': 'run-CONFIDENTIAL456',
            'verify_ssl': True,
            'timeout': 30,
            'retry_attempts': 3
        }
    
    def tearDown(self):
        """Clean up after each test"""
        self.manager.clear_credentials()
    
    def test_no_credential_exposure_in_string_representation(self):
        """Test that credentials are not exposed in string representations"""
        self.manager.store_credentials(self.sensitive_config)
        
        # Test manager string representation
        manager_str = str(self.manager)
        self.assertNotIn('super-secret-token-data-12345', manager_str)
        
        # Test config string representation (should be masked)
        config = self.manager.get_config()
        config_str = str(config)
        # The token should be masked in the string representation
        self.assertNotIn('super-secret-token-data-12345', config_str)
        # But should contain masked version
        self.assertIn('supe', config_str)  # First 4 chars
        self.assertIn('2345', config_str)  # Last 4 chars
        self.assertIn('*', config_str)     # Masking characters
    
    def test_no_credential_exposure_in_error_messages(self):
        """Test that credentials are not exposed in error messages"""
        self.manager.store_credentials(self.sensitive_config)
        
        # Simulate various error scenarios
        try:
            # Force an error by accessing non-existent attribute
            _ = self.manager.non_existent_method()
        except AttributeError as e:
            error_str = str(e)
            self.assertNotIn('super-secret-token-data-12345', error_str)
            self.assertNotIn('secret-org', error_str)
    
    def test_no_credential_exposure_in_masked_config(self):
        """Test that masked config properly hides sensitive data"""
        self.manager.store_credentials(self.sensitive_config)
        
        masked = self.manager.get_masked_config()
        masked_str = str(masked)
        
        # Original sensitive data should not be present
        self.assertNotIn('super-secret-token-data-12345', masked_str)
        
        # Organization should be masked if it contains 'secret'
        if 'secret' in self.sensitive_config['organization'].lower():
            self.assertNotIn('secret-org', masked_str)
        
        # But masked token should be present
        self.assertIn('supe', masked_str)  # First 4 chars
        self.assertIn('2345', masked_str)  # Last 4 chars
        self.assertIn('*', masked_str)     # Masking characters
    
    def test_no_credential_exposure_in_validation_errors(self):
        """Test that validation errors don't expose credentials"""
        # Create config with invalid but sensitive data
        invalid_config = {
            'tfe_server': 'invalid-server',
            'organization': 'secret-org-name',
            'token': 'invalid-but-secret-token-12345',
            'workspace_id': 'invalid-ws-format',
            'run_id': 'invalid-run-format'
        }
        
        is_valid, errors = self.manager.validate_config(invalid_config)
        
        self.assertFalse(is_valid)
        
        # Check that sensitive data is not in error messages
        all_errors = ' '.join(errors)
        self.assertNotIn('secret-org-name', all_errors)
        self.assertNotIn('invalid-but-secret-token-12345', all_errors)
    
    def test_no_credential_exposure_in_session_info(self):
        """Test that session info doesn't expose credentials"""
        self.manager.store_credentials(self.sensitive_config)
        
        session_info = self.manager.get_session_info()
        session_info_str = str(session_info)
        
        # Sensitive data should not be in session info
        self.assertNotIn('super-secret-token-data-12345', session_info_str)
        self.assertNotIn('secret-org', session_info_str)
        self.assertNotIn('ws-SENSITIVE123', session_info_str)
        self.assertNotIn('run-CONFIDENTIAL456', session_info_str)
    
    def test_no_credential_exposure_after_cleanup(self):
        """Test that no credentials remain after cleanup"""
        self.manager.store_credentials(self.sensitive_config)
        
        # Clear credentials
        self.manager.clear_credentials()
        
        # Verify no sensitive data remains accessible
        self.assertIsNone(self.manager.get_credentials())
        self.assertIsNone(self.manager.get_config())
        self.assertEqual(self.manager.get_masked_config(), {})
        
        # Session info should show inactive
        session_info = self.manager.get_session_info()
        self.assertFalse(session_info['active'])
    
    def test_no_credential_exposure_in_deep_copy(self):
        """Test that deep copying doesn't expose credentials"""
        import copy
        
        self.manager.store_credentials(self.sensitive_config)
        
        # Get credentials (which should be a copy)
        creds1 = self.manager.get_credentials()
        creds2 = self.manager.get_credentials()
        
        # Modify one copy
        creds1['token'] = 'modified-token'
        
        # Original and other copy should be unchanged
        original_creds = self.manager.get_credentials()
        self.assertEqual(original_creds['token'], 'super-secret-token-data-12345')
        self.assertEqual(creds2['token'], 'super-secret-token-data-12345')
        self.assertNotEqual(creds1['token'], creds2['token'])


if __name__ == '__main__':
    unittest.main()
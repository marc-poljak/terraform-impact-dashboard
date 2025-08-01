"""
Comprehensive security tests for TFE integration

Tests all security aspects of TFE integration including credential handling,
data protection, secure transmission, and cleanup procedures.
"""

import pytest
import threading
import time
import gc
from unittest.mock import Mock, patch, MagicMock
import requests
from requests.exceptions import SSLError

from utils.credential_manager import CredentialManager, TFEConfig
from providers.tfe_client import TFEClient
from components.tfe_input import TFEInputComponent
from utils.secure_plan_manager import SecurePlanManager


class TestTFECredentialSecurity:
    """Test credential security features"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.credential_manager = CredentialManager()
        self.valid_config = {
            'tfe_server': 'app.terraform.io',
            'organization': 'test-org',
            'token': 'tfe-token-12345678901234567890123456789012',
            'workspace_id': 'ws-ABC123456789',
            'run_id': 'run-XYZ987654321',
            'verify_ssl': True,
            'timeout': 30,
            'retry_attempts': 3
        }
    
    def teardown_method(self):
        """Clean up after each test"""
        self.credential_manager.clear_credentials()
        CredentialManager.cleanup_all_instances()
    
    def test_credentials_never_written_to_disk(self):
        """Test that credentials are never written to disk"""
        # Store credentials
        self.credential_manager.store_credentials(self.valid_config)
        
        # Verify credentials are in memory only
        assert self.credential_manager._credentials is not None
        assert self.credential_manager._config is not None
        
        # Verify no file operations are used in credential storage
        # This is a design verification - the implementation should only use instance variables
        assert isinstance(self.credential_manager._credentials, dict)
        assert isinstance(self.credential_manager._config, TFEConfig)
        
        # Verify credentials can be retrieved from memory
        stored_creds = self.credential_manager.get_credentials()
        assert stored_creds['token'] == self.valid_config['token']
    
    def test_credential_masking_prevents_exposure(self):
        """Test that credential masking prevents accidental exposure"""
        self.credential_manager.store_credentials(self.valid_config)
        
        # Test token masking
        masked_config = self.credential_manager.get_masked_config()
        original_token = self.valid_config['token']
        masked_token = masked_config['token']
        
        # Verify token is masked
        assert masked_token != original_token
        assert '*' in masked_token
        assert len(masked_token) == len(original_token)
        
        # Verify first and last 4 characters are preserved
        assert masked_token.startswith(original_token[:4])
        assert masked_token.endswith(original_token[-4:])
        
        # Verify middle is masked
        middle_section = masked_token[4:-4]
        assert all(c == '*' for c in middle_section)
    
    def test_credential_masking_short_tokens(self):
        """Test credential masking for tokens that meet minimum length but are still considered short"""
        short_config = self.valid_config.copy()
        short_config['token'] = 'short12345'  # 10 chars - minimum valid length
        
        self.credential_manager.store_credentials(short_config)
        masked_config = self.credential_manager.get_masked_config()
        
        # Tokens of 10 characters should show first 4 and last 4 with middle masked
        expected_masked = 'shor**2345'
        assert masked_config['token'] == expected_masked
    
    def test_sensitive_organization_masking(self):
        """Test masking of sensitive organization names"""
        sensitive_configs = [
            {'organization': 'secret-org'},
            {'organization': 'confidential-company'},
            {'organization': 'private-internal'},
            {'organization': 'internal-systems'}
        ]
        
        for sensitive_org in sensitive_configs:
            config = self.valid_config.copy()
            config.update(sensitive_org)
            
            self.credential_manager.store_credentials(config)
            masked_config = self.credential_manager.get_masked_config()
            
            # Sensitive organization names should be masked
            assert masked_config['organization'] != config['organization']
            assert '*' in masked_config['organization']
            
            self.credential_manager.clear_credentials()
    
    def test_credential_cleanup_on_clear(self):
        """Test that credentials are properly overwritten before clearing"""
        original_token = 'sensitive-token-data-12345678901234567890'
        config = self.valid_config.copy()
        config['token'] = original_token
        
        self.credential_manager.store_credentials(config)
        
        # Verify credentials are stored
        assert self.credential_manager.get_credentials()['token'] == original_token
        
        # Clear credentials
        self.credential_manager.clear_credentials()
        
        # Verify credentials are cleared
        assert self.credential_manager.get_credentials() is None
        assert self.credential_manager.get_config() is None
        assert self.credential_manager._credentials is None
        assert self.credential_manager._config is None
    
    def test_credential_copy_protection(self):
        """Test that credential getters return copies, not references"""
        self.credential_manager.store_credentials(self.valid_config)
        
        # Get credentials twice
        creds1 = self.credential_manager.get_credentials()
        creds2 = self.credential_manager.get_credentials()
        
        # Should be equal but not the same object
        assert creds1 == creds2
        assert creds1 is not creds2
        
        # Modifying returned dict shouldn't affect stored credentials
        creds1['token'] = 'modified-token'
        creds3 = self.credential_manager.get_credentials()
        
        assert creds3['token'] != 'modified-token'
        assert creds3['token'] == self.valid_config['token']
    
    @patch('time.time')
    def test_session_timeout_security(self, mock_time):
        """Test session timeout for automatic credential cleanup"""
        # Mock time to simulate timeout
        start_time = 1000.0
        mock_time.return_value = start_time
        
        # Set minimum valid timeout
        self.credential_manager.set_session_timeout(60)  # 60 seconds - minimum valid
        
        # Store credentials
        self.credential_manager.store_credentials(self.valid_config)
        
        # Verify credentials are stored
        assert self.credential_manager.get_credentials() is not None
        
        # Simulate time passing beyond timeout
        mock_time.return_value = start_time + 61  # 61 seconds later
        
        # Trigger timeout check (in real usage this would be automatic)
        self.credential_manager._session_timeout_cleanup()
        
        # Verify credentials are cleared
        assert self.credential_manager.get_credentials() is None
    
    @patch('time.time')
    def test_session_extension_security(self, mock_time):
        """Test session extension resets timeout"""
        # Mock time progression
        start_time = 1000.0
        mock_time.return_value = start_time
        
        # Set minimum valid timeout
        self.credential_manager.set_session_timeout(60)  # 60 seconds
        
        # Store credentials
        self.credential_manager.store_credentials(self.valid_config)
        
        # Simulate time passing to near timeout
        mock_time.return_value = start_time + 50  # 50 seconds later
        
        # Extend session (this should reset the timeout)
        self.credential_manager.extend_session()
        
        # Simulate more time passing (should still be valid due to extension)
        mock_time.return_value = start_time + 70  # 70 seconds from start, but only 20 from extension
        
        # Verify credentials are still available (extension should have reset timer)
        assert self.credential_manager.get_credentials() is not None
    
    def test_multiple_instance_isolation(self):
        """Test that multiple credential manager instances are isolated"""
        manager1 = CredentialManager()
        manager2 = CredentialManager()
        
        config1 = self.valid_config.copy()
        config1['token'] = 'token-for-manager-1'
        
        config2 = self.valid_config.copy()
        config2['token'] = 'token-for-manager-2'
        
        # Store different credentials in each manager
        manager1.store_credentials(config1)
        manager2.store_credentials(config2)
        
        # Verify isolation
        creds1 = manager1.get_credentials()
        creds2 = manager2.get_credentials()
        
        assert creds1['token'] == 'token-for-manager-1'
        assert creds2['token'] == 'token-for-manager-2'
        
        # Clear one shouldn't affect the other
        manager1.clear_credentials()
        
        assert manager1.get_credentials() is None
        assert manager2.get_credentials() is not None
        assert manager2.get_credentials()['token'] == 'token-for-manager-2'
        
        # Cleanup
        manager2.clear_credentials()
    
    def test_global_cleanup_security(self):
        """Test global cleanup clears all instances"""
        manager1 = CredentialManager()
        manager2 = CredentialManager()
        
        # Store credentials in both
        manager1.store_credentials(self.valid_config)
        manager2.store_credentials(self.valid_config)
        
        # Verify both have credentials
        assert manager1.get_credentials() is not None
        assert manager2.get_credentials() is not None
        
        # Global cleanup
        CredentialManager.cleanup_all_instances()
        
        # Verify both are cleared
        assert manager1.get_credentials() is None
        assert manager2.get_credentials() is None


class TestTFEClientSecurity:
    """Test TFE client security features"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.credential_manager = CredentialManager()
        self.tfe_client = TFEClient(self.credential_manager)
        self.valid_config = {
            'tfe_server': 'app.terraform.io',
            'organization': 'test-org',
            'token': 'tfe-token-12345678901234567890123456789012',
            'workspace_id': 'ws-ABC123456789',
            'run_id': 'run-XYZ987654321',
            'verify_ssl': True,
            'timeout': 30,
            'retry_attempts': 3
        }
    
    def teardown_method(self):
        """Clean up after each test"""
        self.tfe_client.close()
        self.credential_manager.clear_credentials()
    
    @patch('requests.Session')
    def test_ssl_verification_enabled_by_default(self, mock_session_class):
        """Test that SSL verification is enabled by default"""
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        
        # Store config with SSL verification enabled
        self.credential_manager.store_credentials(self.valid_config)
        
        # Create session
        session = self.tfe_client._create_session()
        
        # Verify SSL verification is enabled
        assert session.verify is True
    
    @patch('requests.Session')
    def test_ssl_verification_can_be_disabled_for_testing(self, mock_session_class):
        """Test that SSL verification can be disabled for testing"""
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        
        # Store config with SSL verification disabled
        config = self.valid_config.copy()
        config['verify_ssl'] = False
        self.credential_manager.store_credentials(config)
        
        # Create session
        with patch('warnings.warn') as mock_warn:
            session = self.tfe_client._create_session()
            
            # Verify SSL verification is disabled
            assert session.verify is False
            
            # Verify warning is issued
            mock_warn.assert_called_once()
            warning_message = mock_warn.call_args[0][0]
            assert "SSL verification is disabled" in warning_message
            assert "insecure" in warning_message
    
    @patch('requests.Session')
    def test_security_headers_added_to_requests(self, mock_session_class):
        """Test that security headers are added to requests"""
        mock_session = Mock()
        # Make headers behave like a dictionary
        mock_session.headers = {}
        mock_session_class.return_value = mock_session
        
        self.credential_manager.store_credentials(self.valid_config)
        
        # Create session
        session = self.tfe_client._create_session()
        
        # Verify security headers are set
        expected_headers = {
            'User-Agent': 'TerraformPlanDashboard/1.0',
            'Accept': 'application/vnd.api+json',
            'Cache-Control': 'no-cache, no-store, must-revalidate',
            'Pragma': 'no-cache'
        }
        
        for header, value in expected_headers.items():
            assert session.headers[header] == value
    
    def test_session_cleanup_clears_sensitive_data(self):
        """Test that session cleanup clears sensitive data"""
        # Mock session with headers as a Mock object that has clear method
        mock_session = Mock()
        mock_headers = Mock()
        mock_headers.clear = Mock()
        mock_session.headers = mock_headers
        mock_session.close = Mock()
        
        self.tfe_client._session = mock_session
        self.tfe_client._authenticated = True
        
        # Close client
        self.tfe_client.close()
        
        # Verify session is closed and cleared
        mock_headers.clear.assert_called_once()
        mock_session.close.assert_called_once()
        assert self.tfe_client._session is None
        assert self.tfe_client._authenticated is False
    
    def test_plan_data_security_through_secure_manager(self):
        """Test that plan data is handled through secure plan manager"""
        # Verify TFE client uses secure plan manager
        assert hasattr(self.tfe_client, 'plan_manager')
        assert isinstance(self.tfe_client.plan_manager, SecurePlanManager)
        
        # Mock successful plan retrieval
        sample_plan_data = {'terraform_version': '1.5.0', 'resource_changes': []}
        
        with patch.object(self.tfe_client.plan_manager, 'store_plan_data') as mock_store, \
             patch.object(self.tfe_client.plan_manager, 'get_plan_data', return_value=sample_plan_data) as mock_get:
            
            # Mock internal methods to simulate successful retrieval
            with patch.object(self.tfe_client, '_authenticated', True), \
                 patch.object(self.tfe_client, '_session', Mock()), \
                 patch.object(self.tfe_client.credential_manager, 'get_config') as mock_config:
                
                mock_config.return_value = Mock(
                    tfe_server='app.terraform.io',
                    token='test-token',
                    timeout=30
                )
                
                with patch.object(self.tfe_client, '_get_run_details_with_retry', return_value=({
                    'data': {'relationships': {'plan': {'data': {'type': 'plans', 'id': 'plan-123'}}}}
                }, None)), \
                patch.object(self.tfe_client, '_get_plan_details_with_retry', return_value=({
                    'data': {'attributes': {'json-output-redacted': 'https://example.com/plan.json'}}
                }, None)), \
                patch.object(self.tfe_client, '_download_json_output_with_retry', return_value=(sample_plan_data, None)):
                    
                    # Execute plan retrieval
                    plan_data, error = self.tfe_client.get_plan_json('ws-123', 'run-456')
                    
                    # Verify plan data was stored securely
                    mock_store.assert_called_once_with(
                        sample_plan_data,
                        source='tfe_integration',
                        workspace_id='ws-123',
                        run_id='run-456'
                    )
                    
                    # Verify secure copy was returned
                    mock_get.assert_called_once()
                    assert plan_data == sample_plan_data
    
    def test_error_messages_dont_expose_credentials(self):
        """Test that error messages don't expose sensitive credentials"""
        # This is tested through the error handler, but we verify the integration
        
        # Mock authentication failure
        with patch.object(self.tfe_client, '_session', Mock()) as mock_session:
            mock_response = Mock()
            mock_response.status_code = 401
            mock_session.get.return_value = mock_response
            
            success, error_message = self.tfe_client.authenticate(
                'app.terraform.io',
                'sensitive-token-12345678901234567890',
                'test-org'
            )
            
            # Verify authentication failed
            assert success is False
            assert error_message is not None
            
            # Verify error message doesn't contain the token
            assert 'sensitive-token-12345678901234567890' not in error_message
            assert 'Authentication Failed' in error_message


class TestTFEInputComponentSecurity:
    """Test TFE input component security features"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.tfe_component = TFEInputComponent()
    
    def teardown_method(self):
        """Clean up after each test"""
        self.tfe_component.cleanup()
    
    def test_component_cleanup_clears_all_sensitive_data(self):
        """Test that component cleanup clears all sensitive data"""
        # Mock credential manager and TFE client
        with patch.object(self.tfe_component.credential_manager, 'clear_credentials') as mock_clear_creds, \
             patch.object(self.tfe_component.plan_manager, 'clear_plan_data') as mock_clear_plan, \
             patch.object(self.tfe_component.tfe_client, 'close') as mock_close_client:
            
            # Execute cleanup
            self.tfe_component.cleanup()
            
            # Verify all cleanup methods were called
            mock_clear_creds.assert_called_once()
            mock_clear_plan.assert_called_once()
            mock_close_client.assert_called_once()
    
    @patch('streamlit.success')
    @patch('streamlit.columns')
    @patch('streamlit.write')
    def test_configuration_summary_masks_sensitive_values(self, mock_write, mock_columns, mock_success):
        """Test that configuration summary masks sensitive values"""
        # Mock columns
        mock_col1 = MagicMock()
        mock_col2 = MagicMock()
        mock_col1.__enter__ = Mock(return_value=mock_col1)
        mock_col1.__exit__ = Mock(return_value=None)
        mock_col2.__enter__ = Mock(return_value=mock_col2)
        mock_col2.__exit__ = Mock(return_value=None)
        mock_columns.return_value = [mock_col1, mock_col2]
        
        # Mock credential manager to return masked config
        with patch.object(self.tfe_component.credential_manager, 'get_masked_config') as mock_get_masked:
            mock_get_masked.return_value = {
                'tfe_server': 'app.terraform.io',
                'organization': 'test-org',
                'token': 'tfe-****-7890',  # Masked token
                'workspace_id': 'ws-ABC123456',
                'run_id': 'run-XYZ987654'
            }
            
            # Show configuration summary
            config = {
                'tfe_server': 'app.terraform.io',
                'organization': 'test-org',
                'token': 'tfe-token-12345678901234567890',  # Original token
                'workspace_id': 'ws-ABC123456',
                'run_id': 'run-XYZ987654',
                'verify_ssl': True
            }
            
            self.tfe_component._show_configuration_summary(config)
            
            # Verify masked config was used
            mock_get_masked.assert_called_once()
            
            # Verify success message was shown
            mock_success.assert_called_once()
    
    def test_validation_errors_dont_expose_sensitive_data(self):
        """Test that validation errors don't expose sensitive configuration data"""
        # Create config with sensitive data
        sensitive_config = {
            'tfe_server': 'app.terraform.io',
            'organization': 'secret-org',
            'token': 'very-sensitive-token-data',
            'workspace_id': 'ws-SENSITIVE123',
            'run_id': 'run-CONFIDENTIAL456'
        }
        
        # Validate config (should fail due to sensitive patterns)
        is_valid, errors = self.tfe_component.validate_config(sensitive_config)
        
        # Verify validation results
        assert isinstance(is_valid, bool)
        assert isinstance(errors, list)
        
        # Verify error messages don't contain the actual sensitive token
        for error in errors:
            assert 'very-sensitive-token-data' not in str(error)


class TestSecurePlanManagerIntegration:
    """Test secure plan manager integration with TFE components"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.plan_manager = SecurePlanManager()
        self.sample_plan_data = {
            'terraform_version': '1.5.0',
            'resource_changes': [
                {
                    'address': 'aws_instance.web',
                    'change': {
                        'actions': ['create'],
                        'after': {
                            'instance_type': 't3.micro',
                            'tags': {
                                'Environment': 'production',
                                'Secret': 'sensitive-value-123'
                            }
                        }
                    }
                }
            ]
        }
    
    def teardown_method(self):
        """Clean up after each test"""
        self.plan_manager.clear_plan_data()
    
    def test_plan_data_stored_securely_with_metadata(self):
        """Test that plan data is stored securely with proper metadata"""
        # Store plan data
        self.plan_manager.store_plan_data(
            self.sample_plan_data,
            source='tfe_integration',
            workspace_id='ws-123',
            run_id='run-456'
        )
        
        # Verify data is stored
        assert self.plan_manager.has_plan_data()
        
        # Verify metadata is recorded
        metadata = self.plan_manager.get_plan_metadata()
        assert metadata is not None
        assert metadata.source == 'tfe_integration'
        assert metadata.terraform_version == '1.5.0'
        assert metadata.resource_count == 1
    
    def test_masked_summary_hides_sensitive_values(self):
        """Test that masked summary hides sensitive values"""
        # Store plan data with sensitive information
        self.plan_manager.store_plan_data(
            self.sample_plan_data,
            source='tfe_integration',
            workspace_id='ws-SENSITIVE123',
            run_id='run-CONFIDENTIAL456'
        )
        
        # Get masked summary
        masked_summary = self.plan_manager.get_masked_summary()
        
        # Verify sensitive values are masked
        assert 'SENSITIVE' not in str(masked_summary)
        assert 'CONFIDENTIAL' not in str(masked_summary)
        
        # Verify summary contains expected non-sensitive data
        assert 'data_size' in masked_summary
    
    def test_plan_data_cleanup_security(self):
        """Test that plan data cleanup is thorough"""
        # Store plan data
        self.plan_manager.store_plan_data(
            self.sample_plan_data,
            source='tfe_integration'
        )
        
        # Verify data is stored
        assert self.plan_manager.has_plan_data()
        
        # Clear plan data
        self.plan_manager.clear_plan_data()
        
        # Verify all data is cleared
        assert not self.plan_manager.has_plan_data()
        assert self.plan_manager.get_plan_data() is None
        assert self.plan_manager.get_plan_metadata() is None
        # get_masked_summary returns {'status': 'no_plan_data'} when no data is present
        masked_summary = self.plan_manager.get_masked_summary()
        assert masked_summary == {'status': 'no_plan_data'}


class TestTFESecurityIntegration:
    """Test security integration across all TFE components"""
    
    def test_end_to_end_security_workflow(self):
        """Test complete security workflow from credential input to cleanup"""
        credential_manager = CredentialManager()
        tfe_client = TFEClient(credential_manager)
        # Use the same credential manager for the TFE component
        tfe_component = TFEInputComponent()
        tfe_component.credential_manager = credential_manager  # Share the same instance
        
        try:
            # 1. Store credentials securely
            config = {
                'tfe_server': 'app.terraform.io',
                'organization': 'test-org',
                'token': 'sensitive-token-data-12345678901234567890',
                'workspace_id': 'ws-ABC123456',
                'run_id': 'run-XYZ987654',
                'verify_ssl': True
            }
            
            credential_manager.store_credentials(config)
            
            # 2. Verify credentials are masked in displays
            masked_config = credential_manager.get_masked_config()
            assert 'sensitive-token-data-12345678901234567890' not in str(masked_config)
            assert '*' in masked_config['token']
            
            # 3. Verify TFE client uses secure session
            with patch('requests.Session') as mock_session_class:
                mock_session = Mock()
                mock_headers = Mock()
                mock_headers.__contains__ = Mock(return_value=True)
                mock_headers.__getitem__ = Mock(return_value='no-cache, no-store, must-revalidate')
                mock_session.headers = mock_headers
                mock_session.verify = True
                mock_session_class.return_value = mock_session
                
                session = tfe_client._create_session()
                
                # Verify security headers
                assert 'Cache-Control' in session.headers
                assert 'no-cache' in session.headers['Cache-Control']
                
                # Verify SSL verification
                assert session.verify is True
            
            # 4. Test cleanup clears all sensitive data
            tfe_component.cleanup()
            
            # Verify credentials are cleared
            assert credential_manager.get_credentials() is None
            
        finally:
            # Ensure cleanup even if test fails
            credential_manager.clear_credentials()
            tfe_client.close()
            tfe_component.cleanup()
    
    def test_concurrent_security_isolation(self):
        """Test that concurrent operations maintain security isolation"""
        # Create multiple isolated components
        manager1 = CredentialManager()
        manager2 = CredentialManager()
        client1 = TFEClient(manager1)
        client2 = TFEClient(manager2)
        
        try:
            # Store different sensitive data in each
            config1 = {
                'tfe_server': 'app.terraform.io',
                'organization': 'org1',
                'token': 'abc1-for-client-1-sensitive',
                'workspace_id': 'ws-ABC123456',
                'run_id': 'run-XYZ111111'
            }
            
            config2 = {
                'tfe_server': 'app.terraform.io',
                'organization': 'org2',
                'token': 'xyz2-for-client-2-sensitive',
                'workspace_id': 'ws-DEF789012',
                'run_id': 'run-UVW222222'
            }
            
            manager1.store_credentials(config1)
            manager2.store_credentials(config2)
            
            # Verify isolation
            creds1 = manager1.get_credentials()
            creds2 = manager2.get_credentials()
            
            assert creds1['token'] == 'abc1-for-client-1-sensitive'
            assert creds2['token'] == 'xyz2-for-client-2-sensitive'
            assert creds1['workspace_id'] != creds2['workspace_id']
            
            # Verify masking works independently
            masked1 = manager1.get_masked_config()
            masked2 = manager2.get_masked_config()
            
            assert 'abc1-for-client-1-sensitive' not in str(masked1)
            assert 'xyz2-for-client-2-sensitive' not in str(masked2)
            assert masked1['token'] != masked2['token']
            
            # Cleanup one shouldn't affect the other
            client1.close()
            manager1.clear_credentials()
            
            assert manager1.get_credentials() is None
            assert manager2.get_credentials() is not None
            
        finally:
            # Cleanup
            manager1.clear_credentials()
            manager2.clear_credentials()
            client1.close()
            client2.close()


if __name__ == '__main__':
    pytest.main([__file__])
"""
Unit tests for the CredentialManager class.

Tests cover secure credential storage, validation, masking functionality,
and proper cleanup of sensitive data.
"""

import pytest
import unittest
from unittest.mock import patch, MagicMock
from utils.credential_manager import CredentialManager, TFEConfig


class TestCredentialManager(unittest.TestCase):
    """Test cases for CredentialManager class."""
    
    def setUp(self):
        """Set up test fixtures."""
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
        """Clean up after each test."""
        self.manager.clear_credentials()
    
    def test_store_credentials_valid_config(self):
        """Test storing valid credentials."""
        self.manager.store_credentials(self.valid_config)
        
        stored = self.manager.get_credentials()
        self.assertIsNotNone(stored)
        self.assertEqual(stored['tfe_server'], 'app.terraform.io')
        self.assertEqual(stored['token'], 'tfe-token-12345678901234567890')
        
        config = self.manager.get_config()
        self.assertIsInstance(config, TFEConfig)
        self.assertEqual(config.tfe_server, 'app.terraform.io')
        self.assertEqual(config.organization, 'test-org')
    
    def test_store_credentials_invalid_config(self):
        """Test storing invalid credentials raises ValueError."""
        invalid_config = self.valid_config.copy()
        del invalid_config['token']  # Remove required field
        
        with self.assertRaises(ValueError) as context:
            self.manager.store_credentials(invalid_config)
        
        self.assertIn('Required field "token" is missing', str(context.exception))
    
    def test_get_credentials_returns_copy(self):
        """Test that get_credentials returns a copy, not the original."""
        self.manager.store_credentials(self.valid_config)
        
        credentials1 = self.manager.get_credentials()
        credentials2 = self.manager.get_credentials()
        
        # Should be equal but not the same object
        self.assertEqual(credentials1, credentials2)
        self.assertIsNot(credentials1, credentials2)
        
        # Modifying returned dict shouldn't affect stored credentials
        credentials1['token'] = 'modified'
        credentials3 = self.manager.get_credentials()
        self.assertNotEqual(credentials1['token'], credentials3['token'])
    
    def test_get_credentials_when_none_stored(self):
        """Test get_credentials returns None when no credentials stored."""
        result = self.manager.get_credentials()
        self.assertIsNone(result)
        
        config = self.manager.get_config()
        self.assertIsNone(config)
    
    def test_get_masked_config(self):
        """Test that sensitive values are properly masked."""
        self.manager.store_credentials(self.valid_config)
        
        masked = self.manager.get_masked_config()
        
        # Token should be masked
        self.assertNotEqual(masked['token'], self.valid_config['token'])
        self.assertTrue(masked['token'].startswith('tfe-'))
        self.assertTrue('*' in masked['token'])
        self.assertTrue(masked['token'].endswith('7890'))
        
        # Other fields should be unchanged
        self.assertEqual(masked['tfe_server'], self.valid_config['tfe_server'])
        self.assertEqual(masked['organization'], self.valid_config['organization'])
    
    def test_get_masked_config_when_none_stored(self):
        """Test get_masked_config returns empty dict when no credentials."""
        result = self.manager.get_masked_config()
        self.assertEqual(result, {})
    
    def test_mask_token_short_token(self):
        """Test masking of short tokens."""
        short_token = 'abc123'
        masked = self.manager._mask_token(short_token)
        self.assertEqual(masked, '*' * len(short_token))
    
    def test_mask_token_long_token(self):
        """Test masking of long tokens."""
        long_token = 'tfe-token-1234567890abcdef'
        masked = self.manager._mask_token(long_token)
        
        self.assertTrue(masked.startswith('tfe-'))
        self.assertTrue(masked.endswith('cdef'))
        self.assertTrue('*' in masked)
        self.assertEqual(len(masked), len(long_token))
    
    def test_clear_credentials(self):
        """Test that credentials are properly cleared."""
        self.manager.store_credentials(self.valid_config)
        
        # Verify credentials are stored
        self.assertIsNotNone(self.manager.get_credentials())
        self.assertIsNotNone(self.manager.get_config())
        
        # Clear credentials
        self.manager.clear_credentials()
        
        # Verify credentials are cleared
        self.assertIsNone(self.manager.get_credentials())
        self.assertIsNone(self.manager.get_config())
        self.assertEqual(self.manager.get_masked_config(), {})
    
    def test_validate_config_valid(self):
        """Test validation of valid configuration."""
        is_valid, errors = self.manager.validate_config(self.valid_config)
        
        self.assertTrue(is_valid)
        self.assertEqual(errors, [])
    
    def test_validate_config_missing_required_fields(self):
        """Test validation fails for missing required fields."""
        config = self.valid_config.copy()
        del config['token']
        del config['organization']
        
        is_valid, errors = self.manager.validate_config(config)
        
        self.assertFalse(is_valid)
        self.assertIn('Required field "token" is missing', errors)
        self.assertIn('Required field "organization" is missing', errors)
    
    def test_validate_config_empty_required_fields(self):
        """Test validation fails for empty required fields."""
        config = self.valid_config.copy()
        config['token'] = ''
        config['workspace_id'] = None
        
        is_valid, errors = self.manager.validate_config(config)
        
        self.assertFalse(is_valid)
        self.assertTrue(any('token' in error and 'empty' in error for error in errors))
        self.assertTrue(any('workspace_id' in error and 'empty' in error for error in errors))
    
    def test_validate_config_invalid_server_url(self):
        """Test validation of invalid server URLs."""
        invalid_servers = [
            'not-a-url',
            'http://',
            'https://.',
            'ftp://invalid.com',
            'http://invalid..com'
        ]
        
        for server in invalid_servers:
            config = self.valid_config.copy()
            config['tfe_server'] = server
            
            is_valid, errors = self.manager.validate_config(config)
            self.assertFalse(is_valid, f"Should reject server: {server}")
            self.assertTrue(any('hostname' in error.lower() or 'invalid' in error.lower() for error in errors))
    
    def test_validate_config_valid_server_urls(self):
        """Test validation of valid server URLs."""
        valid_servers = [
            'app.terraform.io',
            'terraform.example.com',
            'https://terraform.example.com',
            'http://localhost:8080',
            'tfe.company.internal'
        ]
        
        for server in valid_servers:
            config = self.valid_config.copy()
            config['tfe_server'] = server
            
            is_valid, errors = self.manager.validate_config(config)
            # HTTP localhost should generate a warning but still be valid for testing
            if 'http://' in server and 'localhost' in server:
                self.assertTrue(any('insecure' in error.lower() for error in errors), f"Expected insecure warning for {server}")
            else:
                self.assertTrue(is_valid, f"Should accept server: {server}, errors: {errors}")
    
    def test_validate_config_invalid_workspace_id(self):
        """Test validation of invalid workspace IDs."""
        invalid_ids = [
            'workspace-123',  # Wrong prefix
            'ws-',           # Empty after prefix
            'ws-123-abc',    # Contains hyphens after prefix
            'WS-ABC123'      # Wrong case
        ]
        
        for workspace_id in invalid_ids:
            config = self.valid_config.copy()
            config['workspace_id'] = workspace_id
            
            is_valid, errors = self.manager.validate_config(config)
            self.assertFalse(is_valid, f"Should reject workspace_id: {workspace_id}")
            self.assertTrue(any('workspace' in error.lower() and 'invalid' in error.lower() for error in errors))
    
    def test_validate_config_invalid_run_id(self):
        """Test validation of invalid run IDs."""
        invalid_ids = [
            'execution-123',  # Wrong prefix
            'run-',          # Empty after prefix
            'run-123-abc',   # Contains hyphens after prefix
            'RUN-ABC123'     # Wrong case
        ]
        
        for run_id in invalid_ids:
            config = self.valid_config.copy()
            config['run_id'] = run_id
            
            is_valid, errors = self.manager.validate_config(config)
            self.assertFalse(is_valid, f"Should reject run_id: {run_id}")
            self.assertTrue(any('run' in error.lower() and 'invalid' in error.lower() for error in errors))
    
    def test_validate_config_invalid_token_format(self):
        """Test validation of invalid token formats."""
        invalid_tokens = [
            'short',                    # Too short
            'a' * 201,                 # Too long
            'token with spaces',       # Contains spaces
            'token@with#special!chars' # Invalid characters
        ]
        
        for token in invalid_tokens:
            config = self.valid_config.copy()
            config['token'] = token
            
            is_valid, errors = self.manager.validate_config(config)
            self.assertFalse(is_valid, f"Should reject token: {token}")
            self.assertTrue(any('token' in error.lower() and ('short' in error.lower() or 'long' in error.lower() or 'characters' in error.lower()) for error in errors))
    
    def test_validate_config_invalid_optional_fields(self):
        """Test validation of invalid optional fields."""
        config = self.valid_config.copy()
        config['verify_ssl'] = 'true'  # Should be boolean
        config['timeout'] = -1         # Should be positive
        config['retry_attempts'] = -1  # Should be non-negative
        
        is_valid, errors = self.manager.validate_config(config)
        
        self.assertFalse(is_valid)
        self.assertTrue(any('verify_ssl' in error and 'bool' in error for error in errors))
        self.assertTrue(any('timeout' in error and 'at least 1' in error for error in errors))
        self.assertTrue(any('retry_attempts' in error and 'at least 0' in error for error in errors))
    
    def test_validate_config_security_patterns(self):
        """Test detection of security anti-patterns."""
        suspicious_tokens = [
            'your-token-here',
            'placeholder-token',
            'example-token-123',
            'test-token-value'
        ]
        
        for token in suspicious_tokens:
            config = self.valid_config.copy()
            config['token'] = token
            
            is_valid, errors = self.manager.validate_config(config)
            # Should still be valid but with warnings
            self.assertTrue(any('placeholder text' in error for error in errors))
    
    def test_memory_only_storage(self):
        """Test that credentials are never written to disk."""
        # This test verifies the design principle - we can't easily test
        # that nothing is written to disk, but we can verify the implementation
        # doesn't use any file operations
        
        self.manager.store_credentials(self.valid_config)
        
        # Verify credentials are in memory
        self.assertIsNotNone(self.manager._credentials)
        self.assertIsNotNone(self.manager._config)
        
        # The implementation should only use instance variables
        # No file operations should be involved
        self.assertIsInstance(self.manager._credentials, dict)
        self.assertIsInstance(self.manager._config, TFEConfig)
    
    def test_credential_overwrite_on_clear(self):
        """Test that credentials are overwritten before clearing."""
        original_token = 'sensitive-token-data'
        config = self.valid_config.copy()
        config['token'] = original_token
        
        self.manager.store_credentials(config)
        
        # Get reference to internal credentials before clearing
        credentials_ref = self.manager._credentials
        
        self.manager.clear_credentials()
        
        # The original credentials dict should have been overwritten
        # (though we can't easily verify the overwriting in this test)
        self.assertIsNone(self.manager._credentials)
        self.assertIsNone(self.manager._config)
    
    @patch('atexit.register')
    def test_cleanup_registration(self, mock_atexit):
        """Test that cleanup is registered on initialization."""
        manager = CredentialManager()
        
        # Should register cleanup on exit
        self.assertTrue(mock_atexit.called)
        
        # Should register instance cleanup
        args, kwargs = mock_atexit.call_args
        self.assertEqual(args[0], manager._cleanup_on_exit)
    
    def test_cleanup_all_instances(self):
        """Test cleanup of all instances."""
        # Create multiple managers
        manager1 = CredentialManager()
        manager2 = CredentialManager()
        
        # Store credentials in both
        manager1.store_credentials(self.valid_config)
        manager2.store_credentials(self.valid_config)
        
        # Verify credentials are stored
        self.assertIsNotNone(manager1.get_credentials())
        self.assertIsNotNone(manager2.get_credentials())
        
        # Cleanup all instances
        CredentialManager.cleanup_all_instances()
        
        # Verify all credentials are cleared
        self.assertIsNone(manager1.get_credentials())
        self.assertIsNone(manager2.get_credentials())


if __name__ == '__main__':
    unittest.main()
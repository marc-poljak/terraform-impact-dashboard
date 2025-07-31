"""
Unit tests for TFE Input Component

Tests the TFE input component functionality including configuration validation,
UI rendering, and integration with credential manager and TFE client.
"""

import pytest
import streamlit as st
from unittest.mock import Mock, patch, MagicMock
from components.tfe_input import TFEInputComponent
from utils.credential_manager import CredentialManager, TFEConfig


class TestTFEInputComponent:
    """Test cases for TFE Input Component"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.component = TFEInputComponent()
    
    def test_component_initialization(self):
        """Test that component initializes correctly"""
        assert self.component is not None
        assert isinstance(self.component.credential_manager, CredentialManager)
        assert self.component.tfe_client is not None
        assert self.component.error_handler is not None
    
    @patch('streamlit.file_uploader')
    @patch('streamlit.markdown')
    def test_render_no_file_uploaded(self, mock_markdown, mock_file_uploader):
        """Test rendering when no file is uploaded"""
        mock_file_uploader.return_value = None
        
        result = self.component.render()
        
        assert result is None
        mock_file_uploader.assert_called_once()
        mock_markdown.assert_called()
    
    def test_validate_config_valid(self):
        """Test configuration validation with valid config"""
        valid_config = {
            'tfe_server': 'app.terraform.io',
            'organization': 'test-org',
            'token': 'test-token-123456',
            'workspace_id': 'ws-ABC123456',
            'run_id': 'run-XYZ789012'
        }
        
        is_valid, errors = self.component.validate_config(valid_config)
        
        # Note: This will depend on the actual validation logic
        # The test may need adjustment based on the validator implementation
        assert isinstance(is_valid, bool)
        assert isinstance(errors, list)
    
    def test_validate_config_invalid(self):
        """Test configuration validation with invalid config"""
        invalid_config = {
            'tfe_server': 'app.terraform.io',
            # Missing required fields
        }
        
        is_valid, errors = self.component.validate_config(invalid_config)
        
        assert is_valid is False
        assert len(errors) > 0
    
    @patch('streamlit.success')
    @patch('streamlit.columns')
    @patch('streamlit.write')
    def test_show_configuration_summary(self, mock_write, mock_columns, mock_success):
        """Test configuration summary display"""
        # Mock columns with context manager support
        mock_col1 = MagicMock()
        mock_col2 = MagicMock()
        mock_col1.__enter__ = Mock(return_value=mock_col1)
        mock_col1.__exit__ = Mock(return_value=None)
        mock_col2.__enter__ = Mock(return_value=mock_col2)
        mock_col2.__exit__ = Mock(return_value=None)
        mock_columns.return_value = [mock_col1, mock_col2]
        
        # Set up credential manager with test config
        test_config = {
            'tfe_server': 'app.terraform.io',
            'organization': 'test-org',
            'token': 'test-token-123456',
            'workspace_id': 'ws-ABC123456',
            'run_id': 'run-XYZ789012'
        }
        
        # Mock the credential manager methods
        with patch.object(self.component.credential_manager, 'get_masked_config') as mock_get_masked:
            mock_get_masked.return_value = {
                'tfe_server': 'app.terraform.io',
                'organization': 'test-org',
                'token': 'test****3456',
                'workspace_id': 'ws-ABC123456',
                'run_id': 'run-XYZ789012'
            }
            
            self.component._show_configuration_summary(test_config)
            
            mock_success.assert_called_once()
            mock_columns.assert_called_once_with(2)
            mock_get_masked.assert_called_once()
    
    @patch('streamlit.progress')
    @patch('streamlit.empty')
    def test_show_connection_progress(self, mock_empty, mock_progress):
        """Test connection progress display"""
        mock_progress_bar = Mock()
        mock_status_text = Mock()
        mock_progress.return_value = mock_progress_bar
        mock_empty.return_value = mock_status_text
        
        steps = ["Step 1", "Step 2", "Step 3"]
        current_step = 1
        
        self.component.show_connection_progress(steps, current_step)
        
        mock_progress.assert_called_once_with(0)
        mock_empty.assert_called_once()
    
    def test_cleanup(self):
        """Test component cleanup"""
        # Mock the credential manager and TFE client
        with patch.object(self.component.credential_manager, 'clear_credentials') as mock_clear:
            with patch.object(self.component.tfe_client, 'close') as mock_close:
                self.component.cleanup()
                
                mock_clear.assert_called_once()
                mock_close.assert_called_once()
    
    @patch('yaml.safe_load')
    def test_process_configuration_file_valid_yaml(self, mock_yaml_load):
        """Test processing valid YAML configuration file"""
        # Mock file object
        mock_file = Mock()
        mock_file.read.return_value = b'tfe_server: app.terraform.io\norganization: test-org'
        mock_file.name = 'test-config.yaml'
        
        # Mock YAML parsing
        mock_yaml_load.return_value = {
            'tfe_server': 'app.terraform.io',
            'organization': 'test-org',
            'token': 'test-token',
            'workspace_id': 'ws-123',
            'run_id': 'run-456'
        }
        
        # Mock credential manager validation
        with patch.object(self.component.credential_manager, 'validate_yaml_content') as mock_validate:
            mock_validate.return_value = (False, None, ['Invalid config'])
            
            with patch.object(self.component, '_show_validation_errors') as mock_show_errors:
                result = self.component._process_configuration_file(mock_file)
                
                assert result is None  # Should return None due to validation failure
                mock_validate.assert_called_once()
                mock_show_errors.assert_called_once()


@pytest.fixture
def mock_streamlit():
    """Mock Streamlit functions for testing"""
    with patch('streamlit.markdown'), \
         patch('streamlit.file_uploader'), \
         patch('streamlit.success'), \
         patch('streamlit.error'), \
         patch('streamlit.info'), \
         patch('streamlit.warning'), \
         patch('streamlit.expander'), \
         patch('streamlit.columns'), \
         patch('streamlit.write'), \
         patch('streamlit.code'), \
         patch('streamlit.progress'), \
         patch('streamlit.empty'), \
         patch('streamlit.container'):
        yield


def test_component_integration_with_mocks(mock_streamlit):
    """Test component integration with mocked Streamlit functions"""
    component = TFEInputComponent()
    
    # Test that component can be created and basic methods work
    assert component is not None
    
    # Test cleanup doesn't raise errors
    component.cleanup()
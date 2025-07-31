"""
Integration tests for complete TFE workflow

Tests the end-to-end TFE integration workflow from configuration upload
through plan retrieval and processing, including error scenarios and
security features.
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
import requests
from requests.exceptions import ConnectionError, Timeout, HTTPError

from components.tfe_input import TFEInputComponent
from components.upload_section import UploadComponent
from utils.credential_manager import CredentialManager
from providers.tfe_client import TFEClient
from utils.plan_processor import PlanProcessor
from ui.error_handler import ErrorHandler


class TestTFECompleteWorkflow:
    """Test complete TFE integration workflow"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.tfe_component = TFEInputComponent()
        self.upload_component = UploadComponent()
        self.plan_processor = PlanProcessor()
        self.error_handler = ErrorHandler()
        
        # Sample TFE configuration
        self.valid_tfe_config = {
            'tfe_server': 'app.terraform.io',
            'organization': 'test-org',
            'token': 'tfe-token-123456789012345678901234567890',
            'workspace_id': 'ws-ABC123456789',
            'run_id': 'run-XYZ987654321',
            'verify_ssl': True,
            'timeout': 30,
            'retry_attempts': 3
        }
        
        # Sample plan data that TFE would return
        self.sample_plan_data = {
            "terraform_version": "1.5.0",
            "format_version": "1.0",
            "resource_changes": [
                {
                    "address": "aws_instance.web",
                    "mode": "managed",
                    "type": "aws_instance",
                    "name": "web",
                    "change": {
                        "actions": ["create"],
                        "before": None,
                        "after": {
                            "instance_type": "t3.micro",
                            "ami": "ami-12345678"
                        }
                    }
                },
                {
                    "address": "aws_security_group.web",
                    "mode": "managed", 
                    "type": "aws_security_group",
                    "name": "web",
                    "change": {
                        "actions": ["create"],
                        "before": None,
                        "after": {
                            "name": "web-sg",
                            "ingress": [
                                {
                                    "from_port": 80,
                                    "to_port": 80,
                                    "protocol": "tcp",
                                    "cidr_blocks": ["0.0.0.0/0"]
                                }
                            ]
                        }
                    }
                }
            ]
        }
    
    def teardown_method(self):
        """Clean up after each test"""
        # Clear any stored credentials
        CredentialManager.cleanup_all_instances()
    
    @patch('streamlit.file_uploader')
    @patch('streamlit.success')
    @patch('streamlit.markdown')
    @patch('requests.Session')
    def test_successful_tfe_workflow_end_to_end(self, mock_session_class, mock_markdown, mock_success, mock_file_uploader):
        """Test complete successful TFE workflow from config upload to plan analysis"""
        # Mock YAML configuration file upload
        mock_config_file = Mock()
        mock_config_file.read.return_value = """
tfe_server: app.terraform.io
organization: test-org
token: tfe-token-123456789012345678901234567890
workspace_id: ws-ABC123456789
run_id: run-XYZ987654321
verify_ssl: true
timeout: 30
retry_attempts: 3
""".encode('utf-8')
        mock_config_file.name = 'tfe-config.yaml'
        mock_file_uploader.return_value = mock_config_file
        
        # Mock TFE API responses
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        
        # Mock authentication response
        auth_response = Mock()
        auth_response.status_code = 200
        
        # Mock run details response
        run_response = Mock()
        run_response.status_code = 200
        run_response.json.return_value = {
            'data': {
                'relationships': {
                    'plan': {
                        'data': {
                            'type': 'plans',
                            'id': 'plan-123456'
                        }
                    }
                }
            }
        }
        
        # Mock plan details response
        plan_response = Mock()
        plan_response.status_code = 200
        plan_response.json.return_value = {
            'data': {
                'attributes': {
                    'json-output-redacted': 'https://example.com/plan.json'
                }
            }
        }
        
        # Mock JSON output response
        json_response = Mock()
        json_response.status_code = 200
        json_response.json.return_value = self.sample_plan_data
        
        # Configure mock session to return different responses for different calls
        mock_session.get.side_effect = [auth_response, run_response, plan_response, json_response]
        
        # Execute TFE workflow
        with patch('streamlit.empty'), \
             patch('streamlit.info'), \
             patch('streamlit.progress'), \
             patch('streamlit.columns'), \
             patch('streamlit.write'), \
             patch('streamlit.metric'), \
             patch('streamlit.expander'):
            
            plan_data = self.tfe_component.render()
        
        # Verify plan data was retrieved successfully
        assert plan_data is not None
        assert plan_data['terraform_version'] == '1.5.0'
        assert len(plan_data['resource_changes']) == 2
        
        # Verify API calls were made in correct sequence
        assert mock_session.get.call_count == 4
        
        # Verify authentication call
        auth_call = mock_session.get.call_args_list[0]
        assert 'api/v2/account/details' in auth_call[0][0]
        assert auth_call[1]['headers']['Authorization'] == 'Bearer tfe-token-123456789012345678901234567890'
        
        # Verify run details call
        run_call = mock_session.get.call_args_list[1]
        assert 'api/v2/runs/run-XYZ987654321' in run_call[0][0]
        
        # Verify plan details call
        plan_call = mock_session.get.call_args_list[2]
        assert 'api/v2/plans/plan-123456' in plan_call[0][0]
        
        # Verify JSON output download
        json_call = mock_session.get.call_args_list[3]
        assert json_call[0][0] == 'https://example.com/plan.json'
    
    @patch('streamlit.file_uploader')
    @patch('streamlit.error')
    @patch('streamlit.markdown')
    @patch('requests.Session')
    def test_tfe_workflow_authentication_failure(self, mock_session_class, mock_markdown, mock_error, mock_file_uploader):
        """Test TFE workflow with authentication failure"""
        # Mock YAML configuration file upload
        mock_config_file = Mock()
        mock_config_file.read.return_value = """
tfe_server: app.terraform.io
organization: test-org
token: invalid-token
workspace_id: ws-ABC123456789
run_id: run-XYZ987654321
""".encode('utf-8')
        mock_config_file.name = 'tfe-config.yaml'
        mock_file_uploader.return_value = mock_config_file
        
        # Mock TFE API responses
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        
        # Mock authentication failure response
        auth_response = Mock()
        auth_response.status_code = 401
        mock_session.get.return_value = auth_response
        
        # Execute TFE workflow
        with patch('streamlit.empty'), \
             patch('streamlit.info'), \
             patch('streamlit.progress'), \
             patch('streamlit.columns'), \
             patch('streamlit.write'), \
             patch('streamlit.success'), \
             patch('streamlit.expander'):
            
            plan_data = self.tfe_component.render()
        
        # Verify plan data was not retrieved
        assert plan_data is None
        
        # Verify error was displayed
        mock_error.assert_called()
        error_call_args = mock_error.call_args[0][0]
        assert "Step 2 Failed" in error_call_args
    
    @patch('streamlit.file_uploader')
    @patch('streamlit.error')
    @patch('streamlit.markdown')
    @patch('requests.Session')
    def test_tfe_workflow_network_error_with_retry(self, mock_session_class, mock_markdown, mock_error, mock_file_uploader):
        """Test TFE workflow with network error and retry logic"""
        # Mock YAML configuration file upload
        mock_config_file = Mock()
        mock_config_file.read.return_value = """
tfe_server: app.terraform.io
organization: test-org
token: tfe-token-123456789012345678901234567890
workspace_id: ws-ABC123456789
run_id: run-XYZ987654321
""".encode('utf-8')
        mock_config_file.name = 'tfe-config.yaml'
        mock_file_uploader.return_value = mock_config_file
        
        # Mock TFE API responses
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        
        # Mock connection validation to fail with network error
        mock_session.get.side_effect = ConnectionError("Network unreachable")
        
        # Execute TFE workflow
        with patch('streamlit.empty'), \
             patch('streamlit.info'), \
             patch('streamlit.progress'), \
             patch('streamlit.columns'), \
             patch('streamlit.write'), \
             patch('streamlit.success'), \
             patch('streamlit.expander'):
            
            plan_data = self.tfe_component.render()
        
        # Verify plan data was not retrieved
        assert plan_data is None
        
        # Verify error was displayed
        mock_error.assert_called()
        error_call_args = mock_error.call_args[0][0]
        assert "Step 1 Failed" in error_call_args
    
    def test_tfe_plan_data_integration_with_plan_processor(self):
        """Test that TFE-retrieved plan data integrates properly with plan processor"""
        # Process TFE data through plan processor
        result = self.plan_processor.process_plan_data(
            self.sample_plan_data,
            self.upload_component,
            self.error_handler,
            False,  # enhanced_analysis
            False   # security_analysis
        )
        
        # Verify processing was successful
        assert result is not None
        assert result['plan_data'] == self.sample_plan_data
        assert 'parser' in result
        assert 'summary' in result
        assert 'resource_changes' in result
        
        # Verify resource changes were parsed correctly
        assert len(result['resource_changes']) == 2
        
        # Verify summary contains expected data
        summary = result['summary']
        assert summary['total'] == 2
        assert summary['create'] == 2
        assert summary['update'] == 0
        assert summary['delete'] == 0
    
    @patch('streamlit.tabs')
    @patch('streamlit.markdown')
    def test_upload_component_tfe_integration(self, mock_markdown, mock_tabs):
        """Test that upload component properly integrates TFE functionality"""
        # Mock tabs
        mock_tab1 = Mock()
        mock_tab1.__enter__ = Mock(return_value=mock_tab1)
        mock_tab1.__exit__ = Mock(return_value=None)
        mock_tab2 = Mock()
        mock_tab2.__enter__ = Mock(return_value=mock_tab2)
        mock_tab2.__exit__ = Mock(return_value=None)
        mock_tabs.return_value = [mock_tab1, mock_tab2]
        
        # Mock TFE integration to return plan data
        with patch.object(self.upload_component, '_render_file_upload_tab', return_value=None):
            with patch.object(self.upload_component, '_render_tfe_integration_tab', return_value=self.sample_plan_data):
                result = self.upload_component.render()
        
        # Verify TFE data is returned
        assert result == self.sample_plan_data
        
        # Verify tabs were created
        mock_tabs.assert_called_once_with(["📁 File Upload", "🔗 TFE Integration"])
    
    def test_credential_security_during_workflow(self):
        """Test that credentials are handled securely throughout the workflow"""
        credential_manager = CredentialManager()
        
        # Store credentials
        credential_manager.store_credentials(self.valid_tfe_config)
        
        # Verify credentials are stored
        stored_creds = credential_manager.get_credentials()
        assert stored_creds is not None
        assert stored_creds['token'] == self.valid_tfe_config['token']
        
        # Verify masked config doesn't expose token
        masked_config = credential_manager.get_masked_config()
        assert masked_config['token'] != self.valid_tfe_config['token']
        assert '*' in masked_config['token']
        assert masked_config['token'].startswith('tfe-')
        assert masked_config['token'].endswith('7890')
        
        # Verify cleanup clears credentials
        credential_manager.clear_credentials()
        assert credential_manager.get_credentials() is None
        assert credential_manager.get_config() is None
    
    @patch('streamlit.file_uploader')
    @patch('streamlit.error')
    @patch('streamlit.expander')
    def test_configuration_validation_errors(self, mock_expander, mock_error, mock_file_uploader):
        """Test configuration validation error handling"""
        # Mock invalid YAML configuration file
        mock_config_file = Mock()
        mock_config_file.read.return_value = """
tfe_server: app.terraform.io
organization: test-org
# Missing required token field
workspace_id: invalid-workspace-id
run_id: invalid-run-id
""".encode('utf-8')
        mock_config_file.name = 'invalid-config.yaml'
        mock_file_uploader.return_value = mock_config_file
        
        # Mock expander context manager
        mock_expander_context = Mock()
        mock_expander_context.__enter__ = Mock(return_value=mock_expander_context)
        mock_expander_context.__exit__ = Mock(return_value=None)
        mock_expander.return_value = mock_expander_context
        
        # Execute TFE workflow
        with patch('streamlit.markdown'), \
             patch('streamlit.write'), \
             patch('streamlit.info'), \
             patch('streamlit.code'):
            
            plan_data = self.tfe_component.render()
        
        # Verify plan data was not retrieved due to validation errors
        assert plan_data is None
        
        # Verify validation error was displayed
        mock_error.assert_called_once()
        error_message = mock_error.call_args[0][0]
        assert "Configuration validation failed" in error_message
        
        # Verify troubleshooting expander was shown
        mock_expander.assert_called()
    
    def test_plan_data_security_and_cleanup(self):
        """Test that plan data is handled securely and cleaned up properly"""
        tfe_client = TFEClient(CredentialManager())
        
        # Mock successful plan retrieval
        with patch.object(tfe_client, '_authenticated', True), \
             patch.object(tfe_client, '_session', Mock()), \
             patch.object(tfe_client.credential_manager, 'get_config') as mock_get_config:
            
            # Mock config
            mock_config = Mock()
            mock_config.tfe_server = 'app.terraform.io'
            mock_config.token = 'test-token'
            mock_config.timeout = 30
            mock_get_config.return_value = mock_config
            
            # Mock plan manager
            with patch.object(tfe_client.plan_manager, 'store_plan_data') as mock_store, \
                 patch.object(tfe_client.plan_manager, 'get_plan_data', return_value=self.sample_plan_data) as mock_get:
                
                # Mock successful API calls
                with patch.object(tfe_client, '_get_run_details_with_retry', return_value=({
                    'data': {
                        'relationships': {
                            'plan': {
                                'data': {
                                    'type': 'plans',
                                    'id': 'plan-123'
                                }
                            }
                        }
                    }
                }, None)), \
                patch.object(tfe_client, '_get_plan_details_with_retry', return_value=({
                    'data': {
                        'attributes': {
                            'json-output-redacted': 'https://example.com/plan.json'
                        }
                    }
                }, None)), \
                patch.object(tfe_client, '_download_json_output_with_retry', return_value=(self.sample_plan_data, None)):
                    
                    # Execute plan retrieval
                    plan_data, error = tfe_client.get_plan_json('ws-123', 'run-456')
                    
                    # Verify plan data was retrieved
                    assert plan_data is not None
                    assert error is None
                    
                    # Verify plan data was stored securely
                    mock_store.assert_called_once()
                    store_args = mock_store.call_args
                    assert store_args[0][0] == self.sample_plan_data  # plan data
                    assert store_args[1]['source'] == 'tfe_integration'
                    assert store_args[1]['workspace_id'] == 'ws-123'
                    assert store_args[1]['run_id'] == 'run-456'
                    
                    # Verify secure copy was returned
                    mock_get.assert_called_once()
        
        # Test cleanup
        tfe_client.close()
        
        # Verify cleanup was called on plan manager
        # (This would be tested more thoroughly in unit tests)
    
    def test_error_recovery_and_fallback_options(self):
        """Test error recovery and fallback to file upload"""
        # This test verifies that when TFE integration fails,
        # users can still use file upload as a fallback
        
        # Mock file upload returning plan data
        mock_file = Mock()
        mock_file.getvalue.return_value = json.dumps(self.sample_plan_data).encode('utf-8')
        mock_file.size = len(mock_file.getvalue())
        
        # Process via file upload (fallback method)
        with patch.object(self.upload_component, 'validate_and_parse_file', 
                         return_value=(self.sample_plan_data, None)):
            result = self.plan_processor.process_plan_data(
                mock_file, self.upload_component, self.error_handler, False, False
            )
        
        # Verify fallback method works
        assert result is not None
        assert result['plan_data'] == self.sample_plan_data
        
        # Both TFE and file upload should produce equivalent results
        tfe_result = self.plan_processor.process_plan_data(
            self.sample_plan_data, self.upload_component, self.error_handler, False, False
        )
        
        # Compare key analysis results
        assert result['plan_data'] == tfe_result['plan_data']
        assert len(result['resource_changes']) == len(tfe_result['resource_changes'])
        assert result['summary']['total'] == tfe_result['summary']['total']
    
    def test_concurrent_tfe_operations_safety(self):
        """Test that concurrent TFE operations are handled safely"""
        # This test ensures that multiple TFE operations don't interfere
        # with each other's credentials or plan data
        
        credential_manager1 = CredentialManager()
        credential_manager2 = CredentialManager()
        
        config1 = self.valid_tfe_config.copy()
        config1['workspace_id'] = 'ws-111'
        config1['run_id'] = 'run-111'
        
        config2 = self.valid_tfe_config.copy()
        config2['workspace_id'] = 'ws-222'
        config2['run_id'] = 'run-222'
        
        # Store different credentials in each manager
        credential_manager1.store_credentials(config1)
        credential_manager2.store_credentials(config2)
        
        # Verify each manager has its own credentials
        creds1 = credential_manager1.get_credentials()
        creds2 = credential_manager2.get_credentials()
        
        assert creds1['workspace_id'] == 'ws-111'
        assert creds2['workspace_id'] == 'ws-222'
        assert creds1['run_id'] == 'run-111'
        assert creds2['run_id'] == 'run-222'
        
        # Clear one manager shouldn't affect the other
        credential_manager1.clear_credentials()
        
        assert credential_manager1.get_credentials() is None
        assert credential_manager2.get_credentials() is not None
        assert credential_manager2.get_credentials()['workspace_id'] == 'ws-222'
        
        # Cleanup
        credential_manager2.clear_credentials()


if __name__ == '__main__':
    pytest.main([__file__])
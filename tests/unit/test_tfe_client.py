"""
Unit tests for TFE client functionality.

Tests authentication, plan retrieval, connection validation, and error handling
with mocked API responses.
"""

import json
import pytest
from unittest.mock import Mock, patch, MagicMock
import requests
from requests.exceptions import ConnectionError, Timeout, SSLError

from providers.tfe_client import TFEClient
from utils.credential_manager import CredentialManager, TFEConfig


class TestTFEClient:
    """Test cases for TFE client functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.credential_manager = Mock(spec=CredentialManager)
        self.tfe_config = TFEConfig(
            tfe_server="app.terraform.io",
            organization="test-org",
            token="test-token-123",
            workspace_id="ws-123",
            run_id="run-456",
            verify_ssl=True,
            timeout=30,
            retry_attempts=3
        )
        self.credential_manager.get_config.return_value = self.tfe_config
        self.client = TFEClient(self.credential_manager)
    
    @patch('providers.tfe_client.requests.Session')
    def test_authenticate_success(self, mock_session_class):
        """Test successful authentication."""
        # Setup mock session
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_session.get.return_value = mock_response
        
        # Test authentication
        success, error = self.client.authenticate("app.terraform.io", "test-token", "test-org")
        
        assert success is True
        assert error is None
        assert self.client._authenticated is True
        
        # Verify API call
        mock_session.get.assert_called_once()
        call_args = mock_session.get.call_args
        assert "api/v2/account/details" in call_args[0][0]
        assert call_args[1]['headers']['Authorization'] == 'Bearer test-token'
    
    @patch('providers.tfe_client.requests.Session')
    def test_authenticate_invalid_token(self, mock_session_class):
        """Test authentication with invalid token."""
        # Setup mock session
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        
        # Mock 401 response
        mock_response = Mock()
        mock_response.status_code = 401
        mock_session.get.return_value = mock_response
        
        # Test authentication
        success, error = self.client.authenticate("app.terraform.io", "invalid-token", "test-org")
        
        assert success is False
        assert "Authentication Failed" in error
        assert self.client._authenticated is False
    
    @patch('providers.tfe_client.requests.Session')
    def test_authenticate_connection_error(self, mock_session_class):
        """Test authentication with connection error."""
        # Setup mock session
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        
        # Mock connection error
        mock_session.get.side_effect = ConnectionError("Connection failed")
        
        # Test authentication
        success, error = self.client.authenticate("app.terraform.io", "test-token", "test-org")
        
        assert success is False
        assert "TFE Server Unreachable" in error
        assert self.client._authenticated is False
    
    @patch('providers.tfe_client.requests.Session')
    def test_authenticate_normalizes_server_url(self, mock_session_class):
        """Test that server URL is properly normalized."""
        # Setup mock session
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_session.get.return_value = mock_response
        
        # Test with server without protocol
        success, error = self.client.authenticate("app.terraform.io", "test-token", "test-org")
        
        assert success is True
        assert error is None
        
        # Verify URL was normalized to HTTPS
        call_args = mock_session.get.call_args
        assert call_args[0][0].startswith("https://app.terraform.io")
    
    def test_get_plan_json_not_authenticated(self):
        """Test plan retrieval when not authenticated."""
        self.client._authenticated = False
        
        result, error = self.client.get_plan_json("ws-123", "run-456")
        
        assert result is None
        assert "Not authenticated" in error
    
    def test_get_plan_json_no_config(self):
        """Test plan retrieval with no configuration."""
        self.client._authenticated = True
        self.client._session = Mock()
        self.credential_manager.get_config.return_value = None
        
        result, error = self.client.get_plan_json("ws-123", "run-456")
        
        assert result is None
        assert "No TFE configuration available" in error
    
    @patch('providers.tfe_client.requests.Session')
    def test_get_plan_json_success(self, mock_session_class):
        """Test successful plan JSON retrieval."""
        # Setup authenticated client
        self.client._authenticated = True
        mock_session = Mock()
        self.client._session = mock_session
        
        # Mock run details response
        run_response = Mock()
        run_response.status_code = 200
        run_response.json.return_value = {
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
        json_response.json.return_value = {
            'resource_changes': [],
            'planned_values': {}
        }
        
        # Configure mock session to return different responses for different calls
        mock_session.get.side_effect = [run_response, plan_response, json_response]
        
        # Test plan retrieval
        result, error = self.client.get_plan_json("ws-123", "run-456")
        
        assert error is None
        assert result is not None
        assert 'resource_changes' in result
        assert mock_session.get.call_count == 3
    
    @patch('providers.tfe_client.requests.Session')
    def test_get_plan_json_run_not_found(self, mock_session_class):
        """Test plan retrieval with run not found."""
        # Setup authenticated client
        self.client._authenticated = True
        mock_session = Mock()
        self.client._session = mock_session
        
        # Mock 404 response for run
        run_response = Mock()
        run_response.status_code = 404
        mock_session.get.return_value = run_response
        
        # Test plan retrieval
        result, error = self.client.get_plan_json("ws-123", "run-nonexistent")
        
        assert result is None
        assert "Plan Not Found" in error
    
    @patch('providers.tfe_client.requests.Session')
    def test_get_plan_json_no_plan_in_run(self, mock_session_class):
        """Test plan retrieval when run has no plan."""
        # Setup authenticated client
        self.client._authenticated = True
        mock_session = Mock()
        self.client._session = mock_session
        
        # Mock run response without plan
        run_response = Mock()
        run_response.status_code = 200
        run_response.json.return_value = {
            'data': {
                'relationships': {}
            }
        }
        mock_session.get.return_value = run_response
        
        # Test plan retrieval
        result, error = self.client.get_plan_json("ws-123", "run-456")
        
        assert result is None
        assert "No plan found" in error
    
    @patch('providers.tfe_client.requests.Session')
    def test_get_plan_json_no_json_output(self, mock_session_class):
        """Test plan retrieval when plan has no JSON output."""
        # Setup authenticated client
        self.client._authenticated = True
        mock_session = Mock()
        self.client._session = mock_session
        
        # Mock run details response
        run_response = Mock()
        run_response.status_code = 200
        run_response.json.return_value = {
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
        }
        
        # Mock plan details response without JSON output
        plan_response = Mock()
        plan_response.status_code = 200
        plan_response.json.return_value = {
            'data': {
                'attributes': {}
            }
        }
        
        mock_session.get.side_effect = [run_response, plan_response]
        
        # Test plan retrieval
        result, error = self.client.get_plan_json("ws-123", "run-456")
        
        assert result is None
        assert error is not None  # The error handling will provide appropriate message
    
    def test_validate_connection_no_config(self):
        """Test connection validation with no configuration."""
        self.credential_manager.get_config.return_value = None
        
        is_valid, message = self.client.validate_connection()
        
        assert is_valid is False
        assert "No TFE configuration available" in message
    
    @patch('providers.tfe_client.requests.Session')
    def test_validate_connection_success(self, mock_session_class):
        """Test successful connection validation."""
        # Setup mock session
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        
        # Mock successful response (200 or 401 both indicate connectivity)
        mock_response = Mock()
        mock_response.status_code = 401  # Expected without auth
        mock_session.get.return_value = mock_response
        
        # Test connection validation
        is_valid, message = self.client.validate_connection()
        
        assert is_valid is True
        assert "Connection successful" in message
    
    @patch('providers.tfe_client.requests.Session')
    def test_validate_connection_timeout(self, mock_session_class):
        """Test connection validation with timeout."""
        # Setup mock session
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        
        # Mock timeout error
        mock_session.get.side_effect = Timeout("Request timeout")
        
        # Test connection validation
        is_valid, message = self.client.validate_connection()
        
        assert is_valid is False
        assert "timeout" in message.lower()
    
    @patch('providers.tfe_client.requests.Session')
    def test_validate_connection_ssl_error(self, mock_session_class):
        """Test connection validation with SSL error."""
        # Setup mock session
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        
        # Mock SSL error
        mock_session.get.side_effect = SSLError("SSL verification failed")
        
        # Test connection validation
        is_valid, message = self.client.validate_connection()
        
        assert is_valid is False
        assert "SSL Certificate Error" in message
    
    @patch('providers.tfe_client.requests.Session')
    def test_validate_connection_connection_error(self, mock_session_class):
        """Test connection validation with connection error."""
        # Setup mock session
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        
        # Mock connection error
        mock_session.get.side_effect = ConnectionError("Cannot connect")
        
        # Test connection validation
        is_valid, message = self.client.validate_connection()
        
        assert is_valid is False
        assert "TFE Server Unreachable" in message
    
    def test_close_session(self):
        """Test closing the HTTP session."""
        # Setup mock session
        mock_session = Mock()
        self.client._session = mock_session
        self.client._authenticated = True
        
        # Test close
        self.client.close()
        
        assert self.client._session is None
        assert self.client._authenticated is False
        mock_session.close.assert_called_once()
    
    @patch('providers.tfe_client.requests.Session')
    def test_create_session_with_retry_strategy(self, mock_session_class):
        """Test that session is created with proper retry strategy."""
        # Setup mock session
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        
        # Create client and trigger session creation
        client = TFEClient(self.credential_manager)
        session = client._create_session()
        
        # Verify session configuration
        assert session is not None
        mock_session.mount.assert_called()
        
        # Verify SSL configuration
        assert session.verify == self.tfe_config.verify_ssl
    
    def test_extract_plan_id_success(self):
        """Test successful plan ID extraction."""
        run_data = {
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
        }
        
        plan_id = self.client._extract_plan_id(run_data)
        assert plan_id == 'plan-123'
    
    def test_extract_plan_id_no_plan(self):
        """Test plan ID extraction when no plan exists."""
        run_data = {
            'data': {
                'relationships': {}
            }
        }
        
        plan_id = self.client._extract_plan_id(run_data)
        assert plan_id is None
    
    def test_extract_plan_id_invalid_data(self):
        """Test plan ID extraction with invalid data structure."""
        run_data = {'invalid': 'structure'}
        
        plan_id = self.client._extract_plan_id(run_data)
        assert plan_id is None
    
    def test_extract_json_output_url_success(self):
        """Test successful JSON output URL extraction."""
        plan_data = {
            'data': {
                'attributes': {
                    'json-output-redacted': 'https://example.com/plan.json'
                }
            }
        }
        
        url = self.client._extract_json_output_url(plan_data)
        assert url == 'https://example.com/plan.json'
    
    def test_extract_json_output_url_no_output(self):
        """Test JSON output URL extraction when no output exists."""
        plan_data = {
            'data': {
                'attributes': {}
            }
        }
        
        url = self.client._extract_json_output_url(plan_data)
        assert url is None
    
    def test_extract_json_output_url_invalid_data(self):
        """Test JSON output URL extraction with invalid data."""
        plan_data = {'invalid': 'structure'}
        
        url = self.client._extract_json_output_url(plan_data)
        assert url is None
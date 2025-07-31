"""
Unit tests for TFE Error Handler

Tests comprehensive error handling for TFE integration including error classification,
retry logic with exponential backoff, and user-friendly error messages with
troubleshooting guidance.
"""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock
import requests
from requests.exceptions import ConnectionError, Timeout, SSLError, HTTPError

from utils.tfe_error_handler import TFEErrorHandler, TFEErrorType, TFEErrorContext


class TestTFEErrorHandler:
    """Test cases for TFE Error Handler"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.error_handler = TFEErrorHandler(max_retries=3, base_delay=0.1)
    
    def test_error_handler_initialization(self):
        """Test error handler initialization with custom parameters"""
        handler = TFEErrorHandler(max_retries=5, base_delay=2.0)
        
        assert handler.max_retries == 5
        assert handler.base_delay == 2.0
        assert handler.workspace_id_pattern is not None
        assert handler.run_id_pattern is not None
    
    def test_classify_ssl_error(self):
        """Test classification of SSL errors"""
        ssl_error = SSLError("SSL certificate verification failed")
        
        error_type = self.error_handler.classify_error(ssl_error)
        
        assert error_type == TFEErrorType.SSL_ERROR
    
    def test_classify_timeout_error(self):
        """Test classification of timeout errors"""
        timeout_error = Timeout("Request timed out")
        
        error_type = self.error_handler.classify_error(timeout_error)
        
        assert error_type == TFEErrorType.TIMEOUT
    
    def test_classify_connection_error(self):
        """Test classification of connection errors"""
        connection_error = ConnectionError("Connection refused")
        
        error_type = self.error_handler.classify_error(connection_error)
        
        assert error_type == TFEErrorType.SERVER_UNREACHABLE
    
    def test_classify_http_error_401(self):
        """Test classification of 401 HTTP errors"""
        mock_response = Mock()
        mock_response.status_code = 401
        http_error = HTTPError("Unauthorized", response=mock_response)
        
        error_type = self.error_handler.classify_error(http_error)
        
        assert error_type == TFEErrorType.AUTHENTICATION
    
    def test_classify_http_error_403(self):
        """Test classification of 403 HTTP errors"""
        mock_response = Mock()
        mock_response.status_code = 403
        http_error = HTTPError("Forbidden", response=mock_response)
        
        error_type = self.error_handler.classify_error(http_error)
        
        assert error_type == TFEErrorType.PERMISSION_DENIED
    
    def test_classify_http_error_404(self):
        """Test classification of 404 HTTP errors"""
        mock_response = Mock()
        mock_response.status_code = 404
        http_error = HTTPError("Not Found", response=mock_response)
        
        error_type = self.error_handler.classify_error(http_error)
        
        assert error_type == TFEErrorType.PLAN_NOT_FOUND
    
    def test_classify_http_error_429(self):
        """Test classification of 429 HTTP errors"""
        mock_response = Mock()
        mock_response.status_code = 429
        http_error = HTTPError("Too Many Requests", response=mock_response)
        
        error_type = self.error_handler.classify_error(http_error)
        
        assert error_type == TFEErrorType.API_RATE_LIMIT
    
    def test_classify_http_error_500(self):
        """Test classification of 500+ HTTP errors"""
        mock_response = Mock()
        mock_response.status_code = 500
        http_error = HTTPError("Internal Server Error", response=mock_response)
        
        error_type = self.error_handler.classify_error(http_error)
        
        assert error_type == TFEErrorType.SERVER_UNREACHABLE
    
    def test_classify_rate_limit_string_error(self):
        """Test classification of rate limit errors by string content"""
        rate_limit_error = Exception("Rate limit exceeded")
        
        error_type = self.error_handler.classify_error(rate_limit_error)
        
        assert error_type == TFEErrorType.API_RATE_LIMIT
    
    def test_classify_unknown_error(self):
        """Test classification of unknown errors"""
        unknown_error = Exception("Some unexpected error")
        
        error_type = self.error_handler.classify_error(unknown_error)
        
        assert error_type == TFEErrorType.UNKNOWN
    
    def test_validate_workspace_id_valid(self):
        """Test validation of valid workspace IDs"""
        valid_ids = [
            "ws-ABC123456",
            "ws-xyz789012",
            "ws-1234567890",
            "ws-abcDEF123456"
        ]
        
        for workspace_id in valid_ids:
            is_valid, error = self.error_handler.validate_workspace_id(workspace_id)
            assert is_valid is True, f"Should accept workspace_id: {workspace_id}"
            assert error is None
    
    def test_validate_workspace_id_invalid(self):
        """Test validation of invalid workspace IDs"""
        invalid_ids = [
            "",
            None,
            "workspace-123",
            "ws-",
            "ws-123-abc",
            "WS-ABC123",
            "ws-abc def"
        ]
        
        for workspace_id in invalid_ids:
            is_valid, error = self.error_handler.validate_workspace_id(workspace_id)
            assert is_valid is False, f"Should reject workspace_id: {workspace_id}"
            assert error is not None
            assert "workspace" in error.lower()
    
    def test_validate_run_id_valid(self):
        """Test validation of valid run IDs"""
        valid_ids = [
            "run-XYZ789012",
            "run-abc123456",
            "run-1234567890",
            "run-abcDEF123456"
        ]
        
        for run_id in valid_ids:
            is_valid, error = self.error_handler.validate_run_id(run_id)
            assert is_valid is True, f"Should accept run_id: {run_id}"
            assert error is None
    
    def test_validate_run_id_invalid(self):
        """Test validation of invalid run IDs"""
        invalid_ids = [
            "",
            None,
            "execution-123",
            "run-",
            "run-123-abc",
            "RUN-ABC123",
            "run-abc def"
        ]
        
        for run_id in invalid_ids:
            is_valid, error = self.error_handler.validate_run_id(run_id)
            assert is_valid is False, f"Should reject run_id: {run_id}"
            assert error is not None
            assert "run" in error.lower()
    
    def test_handle_authentication_error(self):
        """Test handling of authentication errors"""
        context = TFEErrorContext(
            error_type=TFEErrorType.AUTHENTICATION,
            original_error=Exception("Authentication failed"),
            operation="authentication"
        )
        
        should_retry, error_message = self.error_handler.handle_error(context)
        
        assert should_retry is False  # Don't retry auth errors
        assert "Authentication Failed" in error_message
        assert "API token" in error_message
    
    def test_handle_rate_limit_error_with_retries(self):
        """Test handling of rate limit errors with retries available"""
        context = TFEErrorContext(
            error_type=TFEErrorType.API_RATE_LIMIT,
            original_error=Exception("Rate limit exceeded"),
            operation="plan_retrieval",
            retry_count=1,
            max_retries=3
        )
        
        should_retry, error_message = self.error_handler.handle_error(context)
        
        assert should_retry is True
        assert "Rate limited" in error_message
    
    def test_handle_rate_limit_error_exhausted_retries(self):
        """Test handling of rate limit errors with exhausted retries"""
        context = TFEErrorContext(
            error_type=TFEErrorType.API_RATE_LIMIT,
            original_error=Exception("Rate limit exceeded"),
            operation="plan_retrieval",
            retry_count=3,
            max_retries=3
        )
        
        should_retry, error_message = self.error_handler.handle_error(context)
        
        assert should_retry is False
        assert "API Rate Limit Exceeded" in error_message
    
    def test_handle_network_error_with_retries(self):
        """Test handling of network errors with retries available"""
        context = TFEErrorContext(
            error_type=TFEErrorType.NETWORK_CONNECTIVITY,
            original_error=ConnectionError("Network error"),
            operation="connection_validation",
            retry_count=1,
            max_retries=3
        )
        
        should_retry, error_message = self.error_handler.handle_error(context)
        
        assert should_retry is True
        assert "Network connectivity issue" in error_message
    
    def test_handle_ssl_error(self):
        """Test handling of SSL errors"""
        context = TFEErrorContext(
            error_type=TFEErrorType.SSL_ERROR,
            original_error=SSLError("SSL verification failed"),
            operation="authentication"
        )
        
        should_retry, error_message = self.error_handler.handle_error(context)
        
        assert should_retry is False  # Don't retry SSL errors
        assert "SSL Certificate Error" in error_message
        assert "verify_ssl: false" in error_message
    
    def test_handle_timeout_error_with_retries(self):
        """Test handling of timeout errors with retries available"""
        context = TFEErrorContext(
            error_type=TFEErrorType.TIMEOUT,
            original_error=Timeout("Request timeout"),
            operation="plan_retrieval",
            retry_count=1,
            max_retries=3
        )
        
        should_retry, error_message = self.error_handler.handle_error(context)
        
        assert should_retry is True
        assert "Request timed out" in error_message
    
    def test_handle_permission_error(self):
        """Test handling of permission errors"""
        context = TFEErrorContext(
            error_type=TFEErrorType.PERMISSION_DENIED,
            original_error=Exception("Permission denied"),
            operation="plan_retrieval",
            workspace_id="ws-123",
            run_id="run-456"
        )
        
        should_retry, error_message = self.error_handler.handle_error(context)
        
        assert should_retry is False  # Don't retry permission errors
        assert "Permission Denied" in error_message
        assert "API token" in error_message
    
    def test_handle_plan_not_found_error(self):
        """Test handling of plan not found errors"""
        context = TFEErrorContext(
            error_type=TFEErrorType.PLAN_NOT_FOUND,
            original_error=Exception("Plan not found"),
            operation="plan_retrieval",
            workspace_id="ws-123",
            run_id="run-456"
        )
        
        should_retry, error_message = self.error_handler.handle_error(context)
        
        assert should_retry is False  # Don't retry not found errors
        assert "Plan Not Found" in error_message
        assert "workspace ID" in error_message
    
    def test_handle_unknown_error_with_retries(self):
        """Test handling of unknown errors with retries available"""
        context = TFEErrorContext(
            error_type=TFEErrorType.UNKNOWN,
            original_error=Exception("Unknown error"),
            operation="plan_retrieval",
            retry_count=1,
            max_retries=3
        )
        
        should_retry, error_message = self.error_handler.handle_error(context)
        
        assert should_retry is True
        assert "Unexpected error occurred" in error_message
    
    @patch('time.sleep')
    def test_retry_with_backoff_success_on_retry(self, mock_sleep):
        """Test retry with backoff succeeds on retry"""
        # Mock operation that fails once then succeeds
        call_count = 0
        def mock_operation():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ConnectionError("Network error")
            return "success"
        
        context = TFEErrorContext(
            error_type=TFEErrorType.UNKNOWN,
            original_error=None,
            operation="test_operation"
        )
        
        result, error = self.error_handler.retry_with_backoff(mock_operation, context)
        
        assert result == "success"
        assert error is None
        assert call_count == 2  # Failed once, succeeded on retry
        mock_sleep.assert_called_once()  # Should have slept before retry
    
    @patch('time.sleep')
    def test_retry_with_backoff_exhausted_retries(self, mock_sleep):
        """Test retry with backoff exhausts all retries"""
        # Mock operation that always fails
        def mock_operation():
            raise ConnectionError("Network error")
        
        context = TFEErrorContext(
            error_type=TFEErrorType.UNKNOWN,
            original_error=None,
            operation="test_operation"
        )
        
        result, error = self.error_handler.retry_with_backoff(mock_operation, context)
        
        assert result is None
        assert error is not None
        # The error handler returns formatted error messages, so check for key content
        assert "TFE Server Unreachable" in error or "failed after" in error
        assert mock_sleep.call_count == 3  # Should have slept before each retry
    
    @patch('time.sleep')
    def test_retry_with_backoff_exponential_delay(self, mock_sleep):
        """Test that retry uses exponential backoff delay"""
        # Mock operation that always fails
        def mock_operation():
            raise ConnectionError("Network error")
        
        context = TFEErrorContext(
            error_type=TFEErrorType.UNKNOWN,
            original_error=None,
            operation="test_operation"
        )
        
        self.error_handler.retry_with_backoff(mock_operation, context)
        
        # Verify exponential backoff (with jitter, so check ranges)
        sleep_calls = mock_sleep.call_args_list
        assert len(sleep_calls) == 3
        
        # First retry: base_delay * 2^0 + jitter = 0.1 + jitter
        assert 0.1 <= sleep_calls[0][0][0] <= 0.13
        
        # Second retry: base_delay * 2^1 + jitter = 0.2 + jitter
        assert 0.2 <= sleep_calls[1][0][0] <= 0.26
        
        # Third retry: base_delay * 2^2 + jitter = 0.4 + jitter
        assert 0.4 <= sleep_calls[2][0][0] <= 0.52
    
    @patch('time.sleep')
    def test_retry_with_backoff_no_retry_for_auth_error(self, mock_sleep):
        """Test that authentication errors are not retried"""
        def mock_operation():
            raise Exception("Authentication failed")
        
        context = TFEErrorContext(
            error_type=TFEErrorType.AUTHENTICATION,
            original_error=None,
            operation="authentication"
        )
        
        # Mock handle_error to return no retry for auth errors
        with patch.object(self.error_handler, 'handle_error', return_value=(False, "Auth failed")):
            result, error = self.error_handler.retry_with_backoff(mock_operation, context)
        
        assert result is None
        assert error == "Auth failed"
        mock_sleep.assert_not_called()  # Should not sleep/retry for auth errors
    
    @patch('streamlit.error')
    @patch('streamlit.expander')
    def test_show_error_with_troubleshooting(self, mock_expander, mock_error):
        """Test showing error with troubleshooting guidance"""
        # Mock expander context manager
        mock_expander_context = Mock()
        mock_expander_context.__enter__ = Mock(return_value=mock_expander_context)
        mock_expander_context.__exit__ = Mock(return_value=None)
        mock_expander.return_value = mock_expander_context
        
        context = TFEErrorContext(
            error_type=TFEErrorType.NETWORK_CONNECTIVITY,
            original_error=ConnectionError("Network error"),
            operation="connection_validation",
            server_url="app.terraform.io"
        )
        
        self.error_handler.show_error_with_troubleshooting(
            TFEErrorType.NETWORK_CONNECTIVITY,
            "Network error occurred",
            context
        )
        
        # Verify error message is displayed
        mock_error.assert_called_once_with("Network error occurred")
        
        # Verify troubleshooting expander is shown
        mock_expander.assert_called()
    
    def test_error_context_creation(self):
        """Test TFEErrorContext creation and attributes"""
        context = TFEErrorContext(
            error_type=TFEErrorType.AUTHENTICATION,
            original_error=Exception("Test error"),
            operation="test_operation",
            server_url="app.terraform.io",
            workspace_id="ws-123",
            run_id="run-456",
            retry_count=2,
            max_retries=3
        )
        
        assert context.error_type == TFEErrorType.AUTHENTICATION
        assert str(context.original_error) == "Test error"
        assert context.operation == "test_operation"
        assert context.server_url == "app.terraform.io"
        assert context.workspace_id == "ws-123"
        assert context.run_id == "run-456"
        assert context.retry_count == 2
        assert context.max_retries == 3
    
    def test_error_context_defaults(self):
        """Test TFEErrorContext default values"""
        context = TFEErrorContext(
            error_type=TFEErrorType.UNKNOWN,
            original_error=Exception("Test error"),
            operation="test_operation"
        )
        
        assert context.server_url is None
        assert context.workspace_id is None
        assert context.run_id is None
        assert context.retry_count == 0
        assert context.max_retries == 3
    
    def test_error_type_enum_values(self):
        """Test that all expected error types are defined"""
        expected_types = [
            "authentication",
            "api_rate_limit", 
            "network_connectivity",
            "invalid_id_format",
            "server_unreachable",
            "plan_not_found",
            "permission_denied",
            "ssl_error",
            "timeout",
            "unknown"
        ]
        
        for expected_type in expected_types:
            # Verify enum value exists and has correct string value
            error_type = TFEErrorType(expected_type)
            assert error_type.value == expected_type


if __name__ == '__main__':
    pytest.main([__file__])
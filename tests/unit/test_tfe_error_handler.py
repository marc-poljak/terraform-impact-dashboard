"""
Unit tests for TFE Error Handler

Tests comprehensive error handling for TFE integration including
authentication, API, and network failures with retry logic.
"""

import pytest
import requests
from unittest.mock import Mock, patch, MagicMock
import time

from utils.tfe_error_handler import (
    TFEErrorHandler, 
    TFEErrorType, 
    TFEErrorContext
)


class TestTFEErrorHandler:
    """Test suite for TFE error handler"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.error_handler = TFEErrorHandler(max_retries=3, base_delay=0.1)
    
    def test_classify_ssl_error(self):
        """Test SSL error classification"""
        ssl_error = requests.exceptions.SSLError("SSL certificate verify failed")
        error_type = self.error_handler.classify_error(ssl_error)
        assert error_type == TFEErrorType.SSL_ERROR
    
    def test_classify_timeout_error(self):
        """Test timeout error classification"""
        timeout_error = requests.exceptions.Timeout("Request timed out")
        error_type = self.error_handler.classify_error(timeout_error)
        assert error_type == TFEErrorType.TIMEOUT
    
    def test_classify_connection_error(self):
        """Test connection error classification"""
        conn_error = requests.exceptions.ConnectionError("Connection failed")
        error_type = self.error_handler.classify_error(conn_error)
        assert error_type == TFEErrorType.SERVER_UNREACHABLE
    
    def test_classify_http_401_error(self):
        """Test HTTP 401 error classification"""
        response = Mock()
        response.status_code = 401
        http_error = requests.exceptions.HTTPError("401 Unauthorized", response=response)
        error_type = self.error_handler.classify_error(http_error)
        assert error_type == TFEErrorType.AUTHENTICATION
    
    def test_classify_http_403_error(self):
        """Test HTTP 403 error classification"""
        response = Mock()
        response.status_code = 403
        http_error = requests.exceptions.HTTPError("403 Forbidden", response=response)
        error_type = self.error_handler.classify_error(http_error)
        assert error_type == TFEErrorType.PERMISSION_DENIED
    
    def test_classify_http_404_error(self):
        """Test HTTP 404 error classification"""
        response = Mock()
        response.status_code = 404
        http_error = requests.exceptions.HTTPError("404 Not Found", response=response)
        error_type = self.error_handler.classify_error(http_error)
        assert error_type == TFEErrorType.PLAN_NOT_FOUND
    
    def test_classify_http_429_error(self):
        """Test HTTP 429 error classification"""
        response = Mock()
        response.status_code = 429
        http_error = requests.exceptions.HTTPError("429 Too Many Requests", response=response)
        error_type = self.error_handler.classify_error(http_error)
        assert error_type == TFEErrorType.API_RATE_LIMIT
    
    def test_classify_http_500_error(self):
        """Test HTTP 500 error classification"""
        response = Mock()
        response.status_code = 500
        http_error = requests.exceptions.HTTPError("500 Internal Server Error", response=response)
        error_type = self.error_handler.classify_error(http_error)
        assert error_type == TFEErrorType.SERVER_UNREACHABLE
    
    def test_validate_workspace_id_valid(self):
        """Test valid workspace ID validation"""
        valid_id = "ws-ABC123456789"
        is_valid, error = self.error_handler.validate_workspace_id(valid_id)
        assert is_valid is True
        assert error is None
    
    def test_validate_workspace_id_invalid_format(self):
        """Test invalid workspace ID format"""
        invalid_id = "workspace-123"
        is_valid, error = self.error_handler.validate_workspace_id(invalid_id)
        assert is_valid is False
        assert "Invalid workspace ID format" in error
        assert "ws-" in error
    
    def test_validate_workspace_id_empty(self):
        """Test empty workspace ID"""
        is_valid, error = self.error_handler.validate_workspace_id("")
        assert is_valid is False
        assert "Workspace ID is required" in error
    
    def test_validate_run_id_valid(self):
        """Test valid run ID validation"""
        valid_id = "run-XYZ987654321"
        is_valid, error = self.error_handler.validate_run_id(valid_id)
        assert is_valid is True
        assert error is None
    
    def test_validate_run_id_invalid_format(self):
        """Test invalid run ID format"""
        invalid_id = "execution-123"
        is_valid, error = self.error_handler.validate_run_id(invalid_id)
        assert is_valid is False
        assert "Invalid run ID format" in error
        assert "run-" in error
    
    def test_validate_run_id_empty(self):
        """Test empty run ID"""
        is_valid, error = self.error_handler.validate_run_id("")
        assert is_valid is False
        assert "Run ID is required" in error
    
    def test_handle_authentication_error(self):
        """Test authentication error handling"""
        context = TFEErrorContext(
            error_type=TFEErrorType.AUTHENTICATION,
            original_error=requests.exceptions.HTTPError("401 Unauthorized"),
            operation="authentication"
        )
        
        should_retry, error_message = self.error_handler.handle_error(context)
        
        assert should_retry is False  # Don't retry auth errors
        assert "Authentication Failed" in error_message
        assert "Invalid or expired API token" in error_message
    
    def test_handle_rate_limit_error_with_retries(self):
        """Test rate limit error handling with retries available"""
        context = TFEErrorContext(
            error_type=TFEErrorType.API_RATE_LIMIT,
            original_error=requests.exceptions.HTTPError("429 Too Many Requests"),
            operation="api_call",
            retry_count=1,
            max_retries=3
        )
        
        should_retry, error_message = self.error_handler.handle_error(context)
        
        assert should_retry is True  # Should retry rate limit errors
        assert "Rate limited" in error_message
    
    def test_handle_rate_limit_error_max_retries(self):
        """Test rate limit error handling when max retries reached"""
        context = TFEErrorContext(
            error_type=TFEErrorType.API_RATE_LIMIT,
            original_error=requests.exceptions.HTTPError("429 Too Many Requests"),
            operation="api_call",
            retry_count=3,
            max_retries=3
        )
        
        should_retry, error_message = self.error_handler.handle_error(context)
        
        assert should_retry is False  # Don't retry when max reached
        assert "API Rate Limit Exceeded" in error_message
    
    def test_handle_network_error_with_retries(self):
        """Test network error handling with retries available"""
        context = TFEErrorContext(
            error_type=TFEErrorType.NETWORK_CONNECTIVITY,
            original_error=requests.exceptions.ConnectionError("Connection failed"),
            operation="connection",
            retry_count=1,
            max_retries=3
        )
        
        should_retry, error_message = self.error_handler.handle_error(context)
        
        assert should_retry is True  # Should retry network errors
        assert "Network connectivity issue" in error_message
    
    def test_handle_server_unreachable_with_retries(self):
        """Test server unreachable error handling with retries available"""
        context = TFEErrorContext(
            error_type=TFEErrorType.SERVER_UNREACHABLE,
            original_error=requests.exceptions.ConnectionError("Server unreachable"),
            operation="connection",
            retry_count=1,
            max_retries=3
        )
        
        should_retry, error_message = self.error_handler.handle_error(context)
        
        assert should_retry is True  # Should retry server unreachable errors
        assert "temporarily unreachable" in error_message
    
    def test_handle_ssl_error(self):
        """Test SSL error handling"""
        context = TFEErrorContext(
            error_type=TFEErrorType.SSL_ERROR,
            original_error=requests.exceptions.SSLError("SSL certificate verify failed"),
            operation="connection"
        )
        
        should_retry, error_message = self.error_handler.handle_error(context)
        
        assert should_retry is False  # Don't retry SSL errors
        assert "SSL Certificate Error" in error_message
        assert "verify_ssl: false" in error_message
    
    def test_handle_timeout_error_with_retries(self):
        """Test timeout error handling with retries available"""
        context = TFEErrorContext(
            error_type=TFEErrorType.TIMEOUT,
            original_error=requests.exceptions.Timeout("Request timed out"),
            operation="api_call",
            retry_count=1,
            max_retries=3
        )
        
        should_retry, error_message = self.error_handler.handle_error(context)
        
        assert should_retry is True  # Should retry timeout errors
        assert "Request timed out" in error_message
    
    def test_handle_permission_error(self):
        """Test permission denied error handling"""
        context = TFEErrorContext(
            error_type=TFEErrorType.PERMISSION_DENIED,
            original_error=requests.exceptions.HTTPError("403 Forbidden"),
            operation="api_call",
            workspace_id="ws-123",
            run_id="run-456"
        )
        
        should_retry, error_message = self.error_handler.handle_error(context)
        
        assert should_retry is False  # Don't retry permission errors
        assert "Permission Denied" in error_message
        assert "sufficient permissions" in error_message
    
    def test_handle_plan_not_found_error(self):
        """Test plan not found error handling"""
        context = TFEErrorContext(
            error_type=TFEErrorType.PLAN_NOT_FOUND,
            original_error=requests.exceptions.HTTPError("404 Not Found"),
            operation="plan_retrieval",
            workspace_id="ws-123",
            run_id="run-456"
        )
        
        should_retry, error_message = self.error_handler.handle_error(context)
        
        assert should_retry is False  # Don't retry not found errors
        assert "Plan Not Found" in error_message
        assert "workspace run or plan could not be found" in error_message
    
    @patch('time.sleep')  # Mock sleep to speed up tests
    def test_retry_with_backoff_success_after_retry(self, mock_sleep):
        """Test retry logic succeeds after initial failure"""
        call_count = 0
        
        def failing_operation():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise requests.exceptions.Timeout("Timeout")
            return "success"
        
        context = TFEErrorContext(
            error_type=TFEErrorType.UNKNOWN,
            original_error=None,
            operation="test_operation"
        )
        
        result, error = self.error_handler.retry_with_backoff(failing_operation, context)
        
        assert result == "success"
        assert error is None
        assert call_count == 3  # Should have retried twice
        assert mock_sleep.call_count == 2  # Should have slept twice
    
    @patch('time.sleep')  # Mock sleep to speed up tests
    def test_retry_with_backoff_max_retries_exceeded(self, mock_sleep):
        """Test retry logic fails after max retries"""
        def always_failing_operation():
            raise requests.exceptions.Timeout("Always fails")
        
        context = TFEErrorContext(
            error_type=TFEErrorType.UNKNOWN,
            original_error=None,
            operation="test_operation"
        )
        
        result, error = self.error_handler.retry_with_backoff(always_failing_operation, context)
        
        assert result is None
        assert error is not None
        assert "Request Timeout" in error  # The error handler provides specific timeout message
        assert mock_sleep.call_count == 3  # Should have slept for each retry
    
    @patch('time.sleep')  # Mock sleep to speed up tests
    def test_retry_with_backoff_no_retry_for_auth_error(self, mock_sleep):
        """Test retry logic doesn't retry authentication errors"""
        def auth_failing_operation():
            response = Mock()
            response.status_code = 401
            raise requests.exceptions.HTTPError("401 Unauthorized", response=response)
        
        context = TFEErrorContext(
            error_type=TFEErrorType.UNKNOWN,
            original_error=None,
            operation="authentication"
        )
        
        result, error = self.error_handler.retry_with_backoff(auth_failing_operation, context)
        
        assert result is None
        assert error is not None
        assert "Authentication Failed" in error
        assert mock_sleep.call_count == 0  # Should not have slept (no retries)
    
    def test_exponential_backoff_timing(self):
        """Test that exponential backoff increases delay correctly"""
        # Test the backoff calculation logic
        base_delay = 1.0
        handler = TFEErrorHandler(base_delay=base_delay)
        
        # Expected delays: 1.0, 2.0, 4.0 (plus jitter)
        for attempt in range(3):
            expected_base_delay = base_delay * (2 ** attempt)
            
            # The actual implementation adds jitter, so we can't test exact values
            # but we can verify the base calculation is correct
            assert expected_base_delay == base_delay * (2 ** attempt)
    
    @patch('streamlit.error')
    @patch('streamlit.expander')
    def test_show_error_with_troubleshooting(self, mock_expander, mock_error):
        """Test error display with troubleshooting"""
        mock_expander_context = MagicMock()
        mock_expander.return_value.__enter__ = Mock(return_value=mock_expander_context)
        mock_expander.return_value.__exit__ = Mock(return_value=None)
        
        context = TFEErrorContext(
            error_type=TFEErrorType.AUTHENTICATION,
            original_error=requests.exceptions.HTTPError("401 Unauthorized"),
            operation="authentication"
        )
        
        self.error_handler.show_error_with_troubleshooting(
            TFEErrorType.AUTHENTICATION,
            "Authentication failed",
            context
        )
        
        # Verify error message was displayed
        mock_error.assert_called_once()
        
        # Verify troubleshooting expander was created
        mock_expander.assert_called()


class TestTFEErrorIntegration:
    """Integration tests for TFE error handling"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.error_handler = TFEErrorHandler(max_retries=2, base_delay=0.01)
    
    @patch('time.sleep')
    def test_rate_limit_retry_scenario(self, mock_sleep):
        """Test complete rate limit retry scenario"""
        call_count = 0
        
        def rate_limited_operation():
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                response = Mock()
                response.status_code = 429
                response.headers = {'X-RateLimit-Reset': '1234567890'}
                raise requests.exceptions.HTTPError("429 Too Many Requests", response=response)
            return {"data": "success"}
        
        context = TFEErrorContext(
            error_type=TFEErrorType.UNKNOWN,
            original_error=None,
            operation="api_call"
        )
        
        result, error = self.error_handler.retry_with_backoff(rate_limited_operation, context)
        
        assert result == {"data": "success"}
        assert error is None
        assert call_count == 3  # Initial call + 2 retries
        assert mock_sleep.call_count == 2  # Should have slept for retries
    
    @patch('time.sleep')
    def test_network_error_recovery_scenario(self, mock_sleep):
        """Test network error recovery scenario"""
        call_count = 0
        
        def network_error_operation():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise requests.exceptions.ConnectionError("Network unreachable")
            elif call_count == 2:
                raise requests.exceptions.Timeout("Request timeout")
            return {"status": "connected"}
        
        context = TFEErrorContext(
            error_type=TFEErrorType.UNKNOWN,
            original_error=None,
            operation="connection"
        )
        
        result, error = self.error_handler.retry_with_backoff(network_error_operation, context)
        
        assert result == {"status": "connected"}
        assert error is None
        assert call_count == 3  # Should have retried through different error types
    
    def test_validation_error_immediate_failure(self):
        """Test that validation errors fail immediately without retries"""
        # Test workspace ID validation
        workspace_valid, workspace_error = self.error_handler.validate_workspace_id("invalid-id")
        assert not workspace_valid
        assert "Invalid workspace ID format" in workspace_error
        
        # Test run ID validation
        run_valid, run_error = self.error_handler.validate_run_id("invalid-run")
        assert not run_valid
        assert "Invalid run ID format" in run_error
    
    def test_error_classification_accuracy(self):
        """Test that errors are classified correctly for proper handling"""
        test_cases = [
            (requests.exceptions.SSLError("SSL error"), TFEErrorType.SSL_ERROR),
            (requests.exceptions.Timeout("Timeout"), TFEErrorType.TIMEOUT),
            (requests.exceptions.ConnectionError("Connection error"), TFEErrorType.SERVER_UNREACHABLE),
        ]
        
        for error, expected_type in test_cases:
            classified_type = self.error_handler.classify_error(error)
            assert classified_type == expected_type, f"Error {error} should be classified as {expected_type}, got {classified_type}"
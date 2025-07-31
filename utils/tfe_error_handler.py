"""
TFE Error Handler

Comprehensive error handling for TFE integration with specific handlers for
authentication, API, and network failures. Includes retry logic with exponential
backoff and user-friendly error messages with troubleshooting guidance.
"""

import time
import re
from typing import Dict, Any, Optional, Tuple, Callable
from dataclasses import dataclass
from enum import Enum
import requests
import streamlit as st


class TFEErrorType(Enum):
    """Types of TFE errors for categorized handling"""
    AUTHENTICATION = "authentication"
    API_RATE_LIMIT = "api_rate_limit"
    NETWORK_CONNECTIVITY = "network_connectivity"
    INVALID_ID_FORMAT = "invalid_id_format"
    SERVER_UNREACHABLE = "server_unreachable"
    PLAN_NOT_FOUND = "plan_not_found"
    PERMISSION_DENIED = "permission_denied"
    SSL_ERROR = "ssl_error"
    TIMEOUT = "timeout"
    UNKNOWN = "unknown"


@dataclass
class TFEErrorContext:
    """Context information for TFE errors"""
    error_type: TFEErrorType
    original_error: Exception
    operation: str
    server_url: Optional[str] = None
    workspace_id: Optional[str] = None
    run_id: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3


class TFEErrorHandler:
    """
    Comprehensive error handler for TFE integration.
    
    Provides specific error handling for authentication, API, and network failures
    with retry logic, exponential backoff, and user-friendly error messages.
    """
    
    def __init__(self, max_retries: int = 3, base_delay: float = 1.0):
        """
        Initialize TFE error handler.
        
        Args:
            max_retries: Maximum number of retry attempts
            base_delay: Base delay for exponential backoff (seconds)
        """
        self.max_retries = max_retries
        self.base_delay = base_delay
        
        # Workspace ID pattern: ws-[alphanumeric string]
        self.workspace_id_pattern = re.compile(r'^ws-[a-zA-Z0-9]+$')
        
        # Run ID pattern: run-[alphanumeric string]
        self.run_id_pattern = re.compile(r'^run-[a-zA-Z0-9]+$')
    
    def classify_error(self, error: Exception, operation: str = "") -> TFEErrorType:
        """
        Classify the type of TFE error for appropriate handling.
        
        Args:
            error: The exception that occurred
            operation: The operation that was being performed
            
        Returns:
            TFEErrorType: The classified error type
        """
        error_str = str(error).lower()
        
        if isinstance(error, requests.exceptions.SSLError):
            return TFEErrorType.SSL_ERROR
        elif isinstance(error, requests.exceptions.Timeout):
            return TFEErrorType.TIMEOUT
        elif isinstance(error, requests.exceptions.ConnectionError):
            return TFEErrorType.SERVER_UNREACHABLE
        elif isinstance(error, requests.exceptions.HTTPError):
            if hasattr(error, 'response') and error.response is not None:
                status_code = error.response.status_code
                if status_code == 401:
                    return TFEErrorType.AUTHENTICATION
                elif status_code == 403:
                    return TFEErrorType.PERMISSION_DENIED
                elif status_code == 404:
                    return TFEErrorType.PLAN_NOT_FOUND
                elif status_code == 429:
                    return TFEErrorType.API_RATE_LIMIT
                elif status_code >= 500:
                    return TFEErrorType.SERVER_UNREACHABLE
        elif "rate limit" in error_str or "too many requests" in error_str:
            return TFEErrorType.API_RATE_LIMIT
        elif "network" in error_str or "connection" in error_str:
            return TFEErrorType.NETWORK_CONNECTIVITY
        elif "authentication" in error_str or "unauthorized" in error_str:
            return TFEErrorType.AUTHENTICATION
        
        return TFEErrorType.UNKNOWN
    
    def validate_workspace_id(self, workspace_id: str) -> Tuple[bool, Optional[str]]:
        """
        Validate workspace ID format.
        
        Args:
            workspace_id: The workspace ID to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not workspace_id:
            return False, "Workspace ID is required"
        
        if not self.workspace_id_pattern.match(workspace_id):
            return False, (
                f"Invalid workspace ID format: '{workspace_id}'. "
                "Workspace IDs should start with 'ws-' followed by alphanumeric characters "
                "(e.g., 'ws-ABC123456789')"
            )
        
        return True, None
    
    def validate_run_id(self, run_id: str) -> Tuple[bool, Optional[str]]:
        """
        Validate run ID format.
        
        Args:
            run_id: The run ID to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not run_id:
            return False, "Run ID is required"
        
        if not self.run_id_pattern.match(run_id):
            return False, (
                f"Invalid run ID format: '{run_id}'. "
                "Run IDs should start with 'run-' followed by alphanumeric characters "
                "(e.g., 'run-XYZ987654321')"
            )
        
        return True, None
    
    def handle_error(self, context: TFEErrorContext) -> Tuple[bool, Optional[str]]:
        """
        Handle TFE error with appropriate response based on error type.
        
        Args:
            context: Error context information
            
        Returns:
            Tuple of (should_retry, error_message)
        """
        if context.error_type == TFEErrorType.AUTHENTICATION:
            return self._handle_authentication_error(context)
        elif context.error_type == TFEErrorType.API_RATE_LIMIT:
            return self._handle_rate_limit_error(context)
        elif context.error_type == TFEErrorType.NETWORK_CONNECTIVITY:
            return self._handle_network_error(context)
        elif context.error_type == TFEErrorType.SERVER_UNREACHABLE:
            return self._handle_server_unreachable_error(context)
        elif context.error_type == TFEErrorType.SSL_ERROR:
            return self._handle_ssl_error(context)
        elif context.error_type == TFEErrorType.TIMEOUT:
            return self._handle_timeout_error(context)
        elif context.error_type == TFEErrorType.PERMISSION_DENIED:
            return self._handle_permission_error(context)
        elif context.error_type == TFEErrorType.PLAN_NOT_FOUND:
            return self._handle_plan_not_found_error(context)
        else:
            return self._handle_unknown_error(context)
    
    def retry_with_backoff(self, operation: Callable, context: TFEErrorContext) -> Tuple[Any, Optional[str]]:
        """
        Execute operation with exponential backoff retry logic.
        
        Args:
            operation: The operation to retry
            context: Error context for tracking retries
            
        Returns:
            Tuple of (result, error_message)
        """
        last_error = None
        
        for attempt in range(self.max_retries + 1):
            try:
                context.retry_count = attempt
                result = operation()
                return result, None
                
            except Exception as e:
                last_error = e
                context.original_error = e
                context.error_type = self.classify_error(e, context.operation)
                
                # Check if we should retry
                should_retry, error_message = self.handle_error(context)
                
                if not should_retry or attempt >= self.max_retries:
                    return None, error_message
                
                # Calculate delay with exponential backoff
                delay = self.base_delay * (2 ** attempt)
                
                # Add jitter to prevent thundering herd
                import random
                jitter = random.uniform(0.1, 0.3) * delay
                total_delay = delay + jitter
                
                # Show retry message to user
                if context.error_type == TFEErrorType.API_RATE_LIMIT:
                    st.info(f"⏳ Rate limited. Waiting {total_delay:.1f} seconds before retry {attempt + 1}/{self.max_retries}...")
                else:
                    st.info(f"🔄 Retrying operation in {total_delay:.1f} seconds (attempt {attempt + 1}/{self.max_retries})...")
                
                time.sleep(total_delay)
        
        # All retries exhausted
        return None, f"Operation failed after {self.max_retries} retries: {str(last_error)}"
    
    def _handle_authentication_error(self, context: TFEErrorContext) -> Tuple[bool, str]:
        """Handle authentication errors."""
        error_message = (
            "❌ **Authentication Failed**\n\n"
            "**Common causes:**\n"
            "• Invalid or expired API token\n"
            "• Incorrect organization name\n"
            "• Token lacks required permissions\n\n"
            "**Solutions:**\n"
            "• Verify your API token is correct and hasn't expired\n"
            "• Check organization name spelling\n"
            "• Ensure token has read access to the organization\n"
            "• Generate a new API token if needed"
        )
        
        # Show detailed troubleshooting in Streamlit
        with st.expander("🔧 **Authentication Troubleshooting**", expanded=True):
            st.markdown("""
            **To generate a new API token:**
            1. Go to your TFE user settings
            2. Navigate to 'Tokens' section  
            3. Create a new API token with appropriate permissions
            4. Copy the token immediately (it won't be shown again)
            
            **Required permissions:**
            - Read access to the organization
            - Read access to workspaces
            - Read access to runs and plans
            """)
        
        return False, error_message  # Don't retry authentication errors
    
    def _handle_rate_limit_error(self, context: TFEErrorContext) -> Tuple[bool, str]:
        """Handle API rate limit errors."""
        if context.retry_count < self.max_retries:
            # Extract rate limit info if available
            rate_limit_info = ""
            if hasattr(context.original_error, 'response') and context.original_error.response:
                headers = context.original_error.response.headers
                reset_time = headers.get('X-RateLimit-Reset')
                if reset_time:
                    rate_limit_info = f" (resets at {reset_time})"
            
            return True, f"Rate limited{rate_limit_info}. Will retry automatically."
        
        error_message = (
            "❌ **API Rate Limit Exceeded**\n\n"
            "The TFE API rate limit has been exceeded and retries were unsuccessful.\n\n"
            "**What this means:**\n"
            "• Too many requests sent to TFE API in a short time\n"
            "• Rate limits protect the TFE service from overload\n\n"
            "**Solutions:**\n"
            "• Wait a few minutes and try again\n"
            "• Reduce concurrent operations if running multiple processes\n"
            "• Contact your TFE administrator if limits seem too restrictive"
        )
        
        return False, error_message
    
    def _handle_network_error(self, context: TFEErrorContext) -> Tuple[bool, str]:
        """Handle network connectivity errors."""
        if context.retry_count < self.max_retries:
            return True, "Network connectivity issue. Will retry automatically."
        
        error_message = (
            "❌ **Network Connectivity Issue**\n\n"
            "Unable to establish connection to TFE server after multiple attempts.\n\n"
            "**Common causes:**\n"
            "• Internet connectivity problems\n"
            "• Firewall blocking connections\n"
            "• Proxy configuration issues\n"
            "• DNS resolution problems\n\n"
            "**Solutions:**\n"
            "• Check your internet connection\n"
            "• Verify firewall settings allow HTTPS connections\n"
            "• Check proxy configuration if applicable\n"
            "• Try accessing the TFE server in a web browser\n"
            "• Contact your network administrator if issues persist"
        )
        
        with st.expander("🔧 **Network Troubleshooting**", expanded=True):
            st.markdown(f"""
            **Quick connectivity test:**
            Try accessing your TFE server directly: {context.server_url or 'your TFE server'}
            
            **Network diagnostics:**
            - Can you access other websites normally?
            - Are you behind a corporate firewall?
            - Do you use a proxy server?
            - Is your DNS working correctly?
            
            **Advanced troubleshooting:**
            - Try from a different network (mobile hotspot)
            - Check if specific ports (443 for HTTPS) are blocked
            - Verify TLS/SSL certificate chain is valid
            """)
        
        return False, error_message
    
    def _handle_server_unreachable_error(self, context: TFEErrorContext) -> Tuple[bool, str]:
        """Handle server unreachable errors."""
        if context.retry_count < self.max_retries:
            return True, "TFE server temporarily unreachable. Will retry automatically."
        
        error_message = (
            "❌ **TFE Server Unreachable**\n\n"
            "The TFE server is not responding after multiple attempts.\n\n"
            "**Possible causes:**\n"
            "• TFE server is down for maintenance\n"
            "• Incorrect server URL\n"
            "• Server experiencing high load\n"
            "• Network routing issues\n\n"
            "**Solutions:**\n"
            "• Verify the TFE server URL is correct\n"
            "• Check TFE service status page if available\n"
            "• Try again in a few minutes\n"
            "• Switch to file upload method as alternative\n"
            "• Contact your TFE administrator"
        )
        
        with st.expander("🔧 **Server Troubleshooting**", expanded=True):
            st.markdown(f"""
            **Server URL verification:**
            Current server: `{context.server_url or 'Not specified'}`
            
            **Common URL formats:**
            - Terraform Cloud: `app.terraform.io`
            - Enterprise: `tfe.company.com` or `terraform.company.com`
            - Custom port: `tfe.company.com:8443`
            
            **Alternative options:**
            - Use file upload method instead
            - Download plan manually from TFE web interface
            - Try again during off-peak hours
            """)
        
        return False, error_message
    
    def _handle_ssl_error(self, context: TFEErrorContext) -> Tuple[bool, str]:
        """Handle SSL certificate errors."""
        error_message = (
            "❌ **SSL Certificate Error**\n\n"
            "SSL certificate verification failed for the TFE server.\n\n"
            "**Common causes:**\n"
            "• Self-signed certificate on custom TFE instance\n"
            "• Expired SSL certificate\n"
            "• Certificate chain issues\n"
            "• Corporate proxy interfering with SSL\n\n"
            "**Solutions:**\n"
            "• For testing: Set `verify_ssl: false` in configuration (not recommended for production)\n"
            "• Contact TFE administrator to fix certificate issues\n"
            "• Add custom CA certificate to system trust store\n"
            "• Check if corporate proxy requires special configuration"
        )
        
        with st.expander("🔧 **SSL Troubleshooting**", expanded=True):
            st.markdown(f"""
            **SSL Configuration Options:**
            
            **For testing only (not secure):**
            ```yaml
            verify_ssl: false
            ```
            
            **Production solutions:**
            - Fix certificate on TFE server
            - Install proper CA certificates
            - Configure corporate proxy correctly
            
            **Security warning:**
            Disabling SSL verification makes connections vulnerable to man-in-the-middle attacks.
            Only use for testing with trusted networks.
            """)
        
        return False, error_message  # Don't retry SSL errors
    
    def _handle_timeout_error(self, context: TFEErrorContext) -> Tuple[bool, str]:
        """Handle timeout errors."""
        if context.retry_count < self.max_retries:
            return True, "Request timed out. Will retry with longer timeout."
        
        error_message = (
            "❌ **Request Timeout**\n\n"
            "TFE server did not respond within the timeout period.\n\n"
            "**Common causes:**\n"
            "• Server is experiencing high load\n"
            "• Large plan data taking time to process\n"
            "• Network latency issues\n"
            "• Server temporarily overloaded\n\n"
            "**Solutions:**\n"
            "• Increase timeout value in configuration\n"
            "• Try again during off-peak hours\n"
            "• Use file upload for very large plans\n"
            "• Contact TFE administrator if timeouts persist"
        )
        
        with st.expander("🔧 **Timeout Configuration**", expanded=True):
            st.markdown("""
            **Increase timeout in your configuration:**
            ```yaml
            timeout: 60  # seconds (default: 30)
            ```
            
            **Recommended timeouts:**
            - Small plans: 30 seconds (default)
            - Medium plans: 60 seconds  
            - Large plans: 120 seconds
            - Very large plans: Consider file upload instead
            """)
        
        return False, error_message
    
    def _handle_permission_error(self, context: TFEErrorContext) -> Tuple[bool, str]:
        """Handle permission denied errors."""
        error_message = (
            "❌ **Permission Denied**\n\n"
            "Your API token does not have sufficient permissions for this operation.\n\n"
            "**Required permissions:**\n"
            "• Read access to the organization\n"
            "• Read access to the workspace\n"
            "• Read access to runs and plans\n\n"
            "**Solutions:**\n"
            "• Contact workspace administrator to grant permissions\n"
            "• Use a different API token with appropriate permissions\n"
            "• Verify you're accessing the correct workspace\n"
            "• Check if workspace has restricted access policies"
        )
        
        with st.expander("🔧 **Permission Troubleshooting**", expanded=True):
            st.markdown(f"""
            **Current context:**
            - Workspace ID: `{context.workspace_id or 'Not specified'}`
            - Run ID: `{context.run_id or 'Not specified'}`
            
            **Permission requirements:**
            - Organization member or collaborator
            - Workspace read access (minimum)
            - Plan read permissions
            
            **How to check permissions:**
            1. Log into TFE web interface
            2. Navigate to the workspace
            3. Check if you can view runs and plans
            4. Contact admin if access is needed
            """)
        
        return False, error_message  # Don't retry permission errors
    
    def _handle_plan_not_found_error(self, context: TFEErrorContext) -> Tuple[bool, str]:
        """Handle plan not found errors."""
        error_message = (
            "❌ **Plan Not Found**\n\n"
            "The specified workspace run or plan could not be found.\n\n"
            "**Common causes:**\n"
            "• Incorrect workspace ID or run ID\n"
            "• Run does not exist or has been deleted\n"
            "• Plan has not been generated yet\n"
            "• No structured JSON output available\n\n"
            "**Solutions:**\n"
            "• Verify workspace ID and run ID are correct\n"
            "• Check if the run exists in TFE web interface\n"
            "• Ensure the run has completed successfully\n"
            "• Verify the plan has JSON output available"
        )
        
        with st.expander("🔧 **ID Verification**", expanded=True):
            st.markdown(f"""
            **Current IDs:**
            - Workspace ID: `{context.workspace_id or 'Not specified'}`
            - Run ID: `{context.run_id or 'Not specified'}`
            
            **How to find correct IDs:**
            
            **Workspace ID:**
            - Found in workspace settings URL
            - Format: `ws-` followed by alphanumeric characters
            - Example: `ws-ABC123456789`
            
            **Run ID:**
            - Found in run details URL
            - Format: `run-` followed by alphanumeric characters  
            - Example: `run-XYZ987654321`
            
            **Verification steps:**
            1. Go to TFE web interface
            2. Navigate to your workspace
            3. Find the specific run
            4. Copy IDs from the URL or API
            """)
        
        return False, error_message  # Don't retry not found errors
    
    def _handle_unknown_error(self, context: TFEErrorContext) -> Tuple[bool, str]:
        """Handle unknown/unexpected errors."""
        if context.retry_count < self.max_retries:
            return True, f"Unexpected error occurred: {str(context.original_error)}. Will retry."
        
        error_message = (
            f"❌ **Unexpected Error**\n\n"
            f"An unexpected error occurred: {str(context.original_error)}\n\n"
            "**What you can do:**\n"
            "• Try the operation again\n"
            "• Use file upload as an alternative\n"
            "• Check TFE server status\n"
            "• Contact support if the issue persists"
        )
        
        return False, error_message
    
    def show_error_with_troubleshooting(self, error_type: TFEErrorType, error_message: str, 
                                      context: Optional[TFEErrorContext] = None) -> None:
        """
        Display error message with appropriate troubleshooting guidance.
        
        Args:
            error_type: Type of error that occurred
            error_message: Error message to display
            context: Optional error context for additional details
        """
        # Display main error message
        st.error(error_message)
        
        # Show context-specific troubleshooting
        if error_type == TFEErrorType.NETWORK_CONNECTIVITY:
            self._show_network_troubleshooting(context)
        elif error_type == TFEErrorType.AUTHENTICATION:
            self._show_authentication_troubleshooting(context)
        elif error_type == TFEErrorType.SERVER_UNREACHABLE:
            self._show_server_troubleshooting(context)
        elif error_type == TFEErrorType.INVALID_ID_FORMAT:
            self._show_id_format_troubleshooting(context)
        
        # Always show alternative options
        self._show_alternative_options()
    
    def _show_network_troubleshooting(self, context: Optional[TFEErrorContext]) -> None:
        """Show network-specific troubleshooting guidance."""
        with st.expander("🌐 **Network Troubleshooting**", expanded=False):
            st.markdown("""
            **Quick checks:**
            - ✅ Can you access other websites?
            - ✅ Are you connected to the internet?
            - ✅ Is your firewall blocking connections?
            
            **Corporate network issues:**
            - Check if you're behind a corporate firewall
            - Verify proxy settings if applicable
            - Contact IT support for network access
            
            **Advanced diagnostics:**
            - Try from a different network (mobile hotspot)
            - Check DNS resolution
            - Verify TLS/SSL connectivity
            """)
    
    def _show_authentication_troubleshooting(self, context: Optional[TFEErrorContext]) -> None:
        """Show authentication-specific troubleshooting guidance."""
        with st.expander("🔐 **Authentication Troubleshooting**", expanded=False):
            st.markdown("""
            **Token verification:**
            - Ensure token is copied correctly (no extra spaces)
            - Check if token has expired
            - Verify token has required permissions
            
            **Organization verification:**
            - Check organization name spelling
            - Ensure you're a member of the organization
            - Verify organization exists and is accessible
            
            **Generate new token:**
            1. Go to TFE user settings
            2. Navigate to 'Tokens' section
            3. Create new API token
            4. Copy immediately (won't be shown again)
            """)
    
    def _show_server_troubleshooting(self, context: Optional[TFEErrorContext]) -> None:
        """Show server-specific troubleshooting guidance."""
        with st.expander("🖥️ **Server Troubleshooting**", expanded=False):
            server_url = context.server_url if context else "your TFE server"
            st.markdown(f"""
            **Server verification:**
            - Current server: `{server_url}`
            - Try accessing in web browser
            - Check for typos in server URL
            
            **Common server formats:**
            - Terraform Cloud: `app.terraform.io`
            - Enterprise: `tfe.company.com`
            - With port: `tfe.company.com:8443`
            
            **Service status:**
            - Check TFE service status page
            - Contact TFE administrator
            - Try again during off-peak hours
            """)
    
    def _show_id_format_troubleshooting(self, context: Optional[TFEErrorContext]) -> None:
        """Show ID format troubleshooting guidance."""
        with st.expander("🆔 **ID Format Troubleshooting**", expanded=False):
            st.markdown("""
            **Workspace ID format:**
            - Must start with `ws-`
            - Followed by alphanumeric characters
            - Example: `ws-ABC123456789`
            
            **Run ID format:**
            - Must start with `run-`
            - Followed by alphanumeric characters
            - Example: `run-XYZ987654321`
            
            **How to find IDs:**
            1. Go to TFE web interface
            2. Navigate to workspace/run
            3. Copy ID from URL or settings
            4. Verify format matches examples above
            """)
    
    def _show_alternative_options(self) -> None:
        """Show alternative options when TFE integration fails."""
        with st.expander("🔄 **Alternative Options**", expanded=False):
            st.markdown("""
            **If TFE integration continues to fail:**
            
            **Option 1: File Upload**
            - Download plan JSON from TFE web interface
            - Use the file upload tab instead
            - All analysis features remain available
            
            **Option 2: Manual Plan Generation**
            ```bash
            # Generate plan locally
            terraform plan -out=tfplan
            terraform show -json tfplan > plan.json
            ```
            
            **Option 3: Try Again Later**
            - Server issues may be temporary
            - Network conditions may improve
            - Rate limits reset over time
            """)
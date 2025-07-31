"""
Terraform Cloud/Enterprise API client for plan retrieval.

This module provides a client for interacting with Terraform Cloud/Enterprise
API endpoints to authenticate and retrieve plan data from workspace runs.
"""

import json
import time
from typing import Dict, Any, Optional, Tuple
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from utils.credential_manager import CredentialManager, TFEConfig
from utils.tfe_error_handler import TFEErrorHandler, TFEErrorContext, TFEErrorType
from utils.secure_plan_manager import SecurePlanManager


class TFEClient:
    """
    Client for Terraform Cloud/Enterprise API interactions.
    
    Handles authentication, plan retrieval, and connection validation
    with proper error handling and retry logic.
    """
    
    def __init__(self, credential_manager: CredentialManager):
        """
        Initialize TFE client with credential manager.
        
        Args:
            credential_manager: CredentialManager instance for secure credential access
        """
        self.credential_manager = credential_manager
        self._session: Optional[requests.Session] = None
        self._config: Optional[TFEConfig] = None
        self._authenticated = False
        self.error_handler = TFEErrorHandler()
        self.plan_manager = SecurePlanManager()
    
    def authenticate(self, server: str, token: str, organization: str) -> Tuple[bool, Optional[str]]:
        """
        Authenticate with TFE server with comprehensive error handling.
        
        Args:
            server: TFE server URL
            token: API token for authentication
            organization: Organization name
            
        Returns:
            Tuple of (success, error_message)
        """
        # Normalize server URL
        if not server.startswith(('http://', 'https://')):
            server = f"https://{server}"
        server = server.rstrip('/')
        
        def _authenticate_operation():
            # Create session with retry strategy
            self._session = self._create_session()
            
            # Test authentication with account details endpoint
            url = f"{server}/api/v2/account/details"
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/vnd.api+json'
            }
            
            response = self._session.get(url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                self._authenticated = True
                return True
            elif response.status_code == 401:
                raise requests.exceptions.HTTPError("Authentication failed", response=response)
            else:
                response.raise_for_status()
                return True
        
        # Create error context
        context = TFEErrorContext(
            error_type=TFEErrorType.UNKNOWN,
            original_error=None,
            operation="authentication",
            server_url=server
        )
        
        # Execute with retry logic
        result, error_message = self.error_handler.retry_with_backoff(_authenticate_operation, context)
        
        if result:
            return True, None
        else:
            self._authenticated = False
            return False, error_message
    
    def get_plan_json(self, workspace_id: str, run_id: str) -> Tuple[Optional[Dict], Optional[str]]:
        """
        Retrieve plan JSON data from TFE with comprehensive error handling.
        
        Args:
            workspace_id: Workspace identifier
            run_id: Run identifier
            
        Returns:
            Tuple of (plan_data, error_message)
            plan_data is None if error occurred
        """
        if not self._authenticated or not self._session:
            return None, "Not authenticated with TFE server"
        
        config = self.credential_manager.get_config()
        if not config:
            return None, "No TFE configuration available"
        
        # Validate workspace and run ID formats
        workspace_valid, workspace_error = self.error_handler.validate_workspace_id(workspace_id)
        if not workspace_valid:
            return None, workspace_error
        
        run_valid, run_error = self.error_handler.validate_run_id(run_id)
        if not run_valid:
            return None, run_error
        
        def _get_plan_operation():
            # Step 1: Get run details to find the plan
            run_data, error = self._get_run_details_with_retry(run_id)
            if error:
                raise Exception(error)
            
            # Step 2: Extract plan ID from run data
            plan_id = self._extract_plan_id(run_data)
            if not plan_id:
                raise Exception("No plan found in run data")
            
            # Step 3: Get plan details to find JSON output link
            plan_data, error = self._get_plan_details_with_retry(plan_id)
            if error:
                raise Exception(error)
            
            # Step 4: Extract and download JSON output
            json_output_url = self._extract_json_output_url(plan_data)
            if not json_output_url:
                raise Exception("No structured JSON output available for this plan")
            
            # Step 5: Download the JSON output
            json_data, error = self._download_json_output_with_retry(json_output_url)
            if error:
                raise Exception(error)
            
            return json_data
        
        # Create error context
        context = TFEErrorContext(
            error_type=TFEErrorType.UNKNOWN,
            original_error=None,
            operation="plan_retrieval",
            server_url=config.tfe_server,
            workspace_id=workspace_id,
            run_id=run_id
        )
        
        # Execute with retry logic
        result, error_message = self.error_handler.retry_with_backoff(_get_plan_operation, context)
        
        if result:
            # Store plan data securely
            self.plan_manager.store_plan_data(
                result, 
                source="tfe_integration",
                workspace_id=workspace_id,
                run_id=run_id
            )
            
            # Return secure copy
            return self.plan_manager.get_plan_data(), None
        
        return None, error_message
    
    def validate_connection(self) -> Tuple[bool, str]:
        """
        Test connection to TFE server with comprehensive error handling.
        
        Returns:
            Tuple of (is_valid, message)
        """
        config = self.credential_manager.get_config()
        if not config:
            return False, "No TFE configuration available"
        
        # Normalize server URL
        server = config.tfe_server
        if not server.startswith(('http://', 'https://')):
            server = f"https://{server}"
        
        def _validate_connection_operation():
            # Create a simple session for testing
            session = requests.Session()
            session.verify = config.verify_ssl
            
            # Test basic connectivity (without auth)
            response = session.get(f"{server}/api/v2", timeout=config.timeout)
            
            if response.status_code in [200, 401]:  # 401 is expected without auth
                return True
            else:
                raise requests.exceptions.HTTPError(f"Server returned status code: {response.status_code}", response=response)
        
        # Create error context
        context = TFEErrorContext(
            error_type=TFEErrorType.UNKNOWN,
            original_error=None,
            operation="connection_validation",
            server_url=server
        )
        
        try:
            result, error_message = self.error_handler.retry_with_backoff(_validate_connection_operation, context)
            
            if result:
                return True, "Connection successful"
            else:
                # Show detailed error with troubleshooting
                error_type = self.error_handler.classify_error(context.original_error, "connection_validation")
                self.error_handler.show_error_with_troubleshooting(error_type, error_message, context)
                return False, error_message
                
        except Exception as e:
            error_type = self.error_handler.classify_error(e, "connection_validation")
            context.original_error = e
            context.error_type = error_type
            
            should_retry, error_message = self.error_handler.handle_error(context)
            self.error_handler.show_error_with_troubleshooting(error_type, error_message, context)
            
            return False, error_message
    
    def _create_session(self) -> requests.Session:
        """Create HTTP session with retry strategy and enhanced security."""
        session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # Configure SSL verification and security settings
        config = self.credential_manager.get_config()
        if config:
            session.verify = config.verify_ssl
            
            # Enhanced security headers
            session.headers.update({
                'User-Agent': 'TerraformPlanDashboard/1.0',
                'Accept': 'application/vnd.api+json',
                'Cache-Control': 'no-cache, no-store, must-revalidate',
                'Pragma': 'no-cache'
            })
            
            # Warn about insecure connections
            if not config.verify_ssl:
                import warnings
                warnings.warn(
                    "SSL verification is disabled. This is insecure and should only be used for testing.",
                    UserWarning,
                    stacklevel=2
                )
        
        return session
    
    def _get_run_details_with_retry(self, run_id: str) -> Tuple[Optional[Dict], Optional[str]]:
        """Get run details from TFE API with error handling."""
        config = self.credential_manager.get_config()
        if not config:
            return None, "No configuration available"
        
        server = config.tfe_server
        if not server.startswith(('http://', 'https://')):
            server = f"https://{server}"
        
        url = f"{server}/api/v2/runs/{run_id}"
        headers = {
            'Authorization': f'Bearer {config.token}',
            'Content-Type': 'application/vnd.api+json'
        }
        
        response = self._session.get(url, headers=headers, timeout=config.timeout)
        
        if response.status_code == 200:
            return response.json(), None
        elif response.status_code == 404:
            raise requests.exceptions.HTTPError(f"Run {run_id} not found", response=response)
        elif response.status_code == 403:
            raise requests.exceptions.HTTPError("Access denied. Check permissions for this run.", response=response)
        elif response.status_code == 429:
            raise requests.exceptions.HTTPError("Rate limit exceeded", response=response)
        else:
            response.raise_for_status()
            return response.json(), None
    
    def _extract_plan_id(self, run_data: Dict) -> Optional[str]:
        """Extract plan ID from run data."""
        try:
            relationships = run_data.get('data', {}).get('relationships', {})
            plan_data = relationships.get('plan', {}).get('data')
            
            if plan_data and plan_data.get('type') == 'plans':
                return plan_data.get('id')
            
            return None
        except (KeyError, TypeError):
            return None
    
    def _get_plan_details_with_retry(self, plan_id: str) -> Tuple[Optional[Dict], Optional[str]]:
        """Get plan details from TFE API with error handling."""
        config = self.credential_manager.get_config()
        if not config:
            return None, "No configuration available"
        
        server = config.tfe_server
        if not server.startswith(('http://', 'https://')):
            server = f"https://{server}"
        
        url = f"{server}/api/v2/plans/{plan_id}"
        headers = {
            'Authorization': f'Bearer {config.token}',
            'Content-Type': 'application/vnd.api+json'
        }
        
        response = self._session.get(url, headers=headers, timeout=config.timeout)
        
        if response.status_code == 200:
            return response.json(), None
        elif response.status_code == 404:
            raise requests.exceptions.HTTPError(f"Plan {plan_id} not found", response=response)
        elif response.status_code == 403:
            raise requests.exceptions.HTTPError("Access denied. Check permissions for this plan.", response=response)
        elif response.status_code == 429:
            raise requests.exceptions.HTTPError("Rate limit exceeded", response=response)
        else:
            response.raise_for_status()
            return response.json(), None
    
    def _extract_json_output_url(self, plan_data: Dict) -> Optional[str]:
        """Extract JSON output URL from plan data."""
        try:
            attributes = plan_data.get('data', {}).get('attributes', {})
            return attributes.get('json-output-redacted')
        except (KeyError, TypeError):
            return None
    
    def _download_json_output_with_retry(self, json_url: str) -> Tuple[Optional[Dict], Optional[str]]:
        """Download and parse JSON output from URL with error handling."""
        config = self.credential_manager.get_config()
        if not config:
            return None, "No configuration available"
        
        headers = {
            'Authorization': f'Bearer {config.token}'
        }
        
        response = self._session.get(json_url, headers=headers, timeout=config.timeout)
        
        if response.status_code == 200:
            try:
                return response.json(), None
            except json.JSONDecodeError as e:
                raise Exception(f"Failed to parse JSON output: {str(e)}")
        elif response.status_code == 403:
            raise requests.exceptions.HTTPError("Access denied. Check permissions for plan JSON output.", response=response)
        elif response.status_code == 404:
            raise requests.exceptions.HTTPError("Plan JSON output not found or expired.", response=response)
        elif response.status_code == 429:
            raise requests.exceptions.HTTPError("Rate limit exceeded", response=response)
        else:
            response.raise_for_status()
            return response.json(), None
    
    def close(self):
        """Close the HTTP session and clear sensitive data."""
        if self._session:
            # Clear session headers that might contain sensitive data
            if hasattr(self._session, 'headers'):
                self._session.headers.clear()
            
            self._session.close()
            self._session = None
        
        self._authenticated = False
        
        # Clear any stored plan data
        self.plan_manager.clear_plan_data()
        
        # Trigger credential cleanup
        self.credential_manager.clear_credentials()
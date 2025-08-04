"""
Standalone TFE Client for Terraform Plan Impact Dashboard

This module provides a reliable TFE client implementation that directly
integrates with Terraform Cloud/Enterprise APIs without complex dependencies.
It serves as the primary TFE integration for the dashboard.
"""

import json
import yaml
import requests
from urllib3.exceptions import InsecureRequestWarning
from typing import Dict, Any, Optional, Tuple
import re

# Disable SSL warnings when SSL verification is disabled
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


class StandaloneTFEClient:
    """
    Standalone TFE client for reliable Terraform Cloud/Enterprise integration.
    
    This client provides direct API access to TFE without complex module
    dependencies, ensuring reliable plan data retrieval.
    """
    
    def __init__(self):
        """Initialize the standalone TFE client."""
        self.config = None
        self.authenticated = False
        self.verify_ssl = True  # Default to secure
    
    def load_config_from_yaml(self, yaml_content: str) -> Tuple[bool, Optional[str]]:
        """
        Load configuration from YAML content.
        
        Args:
            yaml_content: YAML configuration as string
            
        Returns:
            Tuple of (success, error_message)
        """
        try:
            config = yaml.safe_load(yaml_content)
            
            # Validate required fields
            required_fields = ['tfe_server', 'organization', 'token', 'workspace_id', 'run_id']
            missing_fields = [field for field in required_fields if not config.get(field)]
            
            if missing_fields:
                return False, f"Missing required fields: {', '.join(missing_fields)}"
            
            # Validate field formats
            if not re.match(r'^ws-[a-zA-Z0-9]{6,}$', config['workspace_id']):
                return False, f"Invalid workspace ID format: {config['workspace_id']}"
            
            if not re.match(r'^run-[a-zA-Z0-9]{6,}$', config['run_id']):
                return False, f"Invalid run ID format: {config['run_id']}"
            
            self.config = config
            self.verify_ssl = config.get('verify_ssl', True)
            
            # Disable SSL warnings if SSL verification is disabled
            if not self.verify_ssl:
                import warnings
                warnings.warn(
                    "SSL verification is disabled. This is insecure and should only be used for testing.",
                    UserWarning
                )
            
            return True, None
            
        except yaml.YAMLError as e:
            return False, f"Invalid YAML: {e}"
        except Exception as e:
            return False, f"Configuration error: {e}"
    
    def authenticate(self) -> Tuple[bool, Optional[str]]:
        """
        Authenticate with TFE server.
        
        Returns:
            Tuple of (success, error_message)
        """
        if not self.config:
            return False, "No configuration loaded"
        
        server = self.config['tfe_server']
        token = self.config['token']
        
        # Test authentication with account details endpoint
        url = f"https://{server}/api/v2/account/details"
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/vnd.api+json'
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=30, verify=self.verify_ssl)
            
            if response.status_code == 200:
                self.authenticated = True
                return True, None
            elif response.status_code == 401:
                return False, "Authentication failed - invalid token"
            else:
                return False, f"Authentication failed - server returned {response.status_code}"
                
        except requests.exceptions.RequestException as e:
            return False, f"Authentication request failed: {e}"
        except Exception as e:
            return False, f"Authentication error: {e}"
    
    def get_plan_json(self) -> Tuple[Optional[Dict], Optional[str]]:
        """
        Retrieve plan JSON data from TFE.
        
        Returns:
            Tuple of (plan_data, error_message)
        """
        if not self.config:
            return None, "No configuration loaded"
        
        if not self.authenticated:
            return None, "Not authenticated - call authenticate() first"
        
        try:
            # Step 1: Get run status to check for failures
            run_info, run_error = self._get_run_info()
            if run_error:
                return None, run_error
            
            # Check run status
            run_status_warning = self._check_run_status(run_info)
            
            # Step 2: Get plan info from run
            plan_info, error = self._get_plan_info_from_run()
            if error:
                return None, error
            
            # Check plan status
            plan_status_warning = self._check_plan_status(plan_info)
            
            # Step 3: Extract JSON output URL
            json_output_url = self._extract_json_output_url(plan_info)
            if not json_output_url:
                return None, "No structured JSON output available for this plan"
            
            # Step 4: Download JSON data
            json_data, error = self._download_json_output(json_output_url)
            if error:
                return None, error
            
            # Step 5: Add status information to the plan data
            if json_data:
                json_data['_tfe_status'] = {
                    'run_status_warning': run_status_warning,
                    'plan_status_warning': plan_status_warning,
                    'run_info': run_info,
                    'plan_info': plan_info
                }
            
            return json_data, None
            
        except Exception as e:
            return None, f"Plan retrieval error: {e}"
    
    def _get_run_info(self) -> Tuple[Optional[Dict], Optional[str]]:
        """Get run information to check status."""
        server = self.config['tfe_server']
        token = self.config['token']
        run_id = self.config['run_id']
        
        url = f"https://{server}/api/v2/runs/{run_id}"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/vnd.api+json"
        }
        
        try:
            response = requests.get(url, headers=headers, verify=self.verify_ssl, timeout=30)
            
            if response.status_code == 200:
                return response.json(), None
            elif response.status_code == 404:
                return None, f"Run {run_id} not found"
            elif response.status_code == 403:
                return None, "Access denied. Check permissions for this run."
            else:
                return None, f"Run info request failed: {response.status_code}"
                
        except requests.exceptions.RequestException as e:
            return None, f"Run info request error: {e}"
        except Exception as e:
            return None, f"Run info error: {e}"
    
    def _get_plan_info_from_run(self) -> Tuple[Optional[Dict], Optional[str]]:
        """Get plan info from run endpoint."""
        server = self.config['tfe_server']
        token = self.config['token']
        run_id = self.config['run_id']
        
        url = f"https://{server}/api/v2/runs/{run_id}/plan"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/vnd.api+json"
        }
        
        try:
            response = requests.get(url, headers=headers, verify=self.verify_ssl, timeout=30)
            
            if response.status_code == 200:
                return response.json(), None
            elif response.status_code == 404:
                return None, f"Plan for run {run_id} not found"
            elif response.status_code == 403:
                return None, "Access denied. Check permissions for this run."
            else:
                return None, f"Plan info request failed: {response.status_code}"
                
        except requests.exceptions.RequestException as e:
            return None, f"Plan info request error: {e}"
        except Exception as e:
            return None, f"Plan info error: {e}"
    
    def _extract_json_output_url(self, plan_info: Dict) -> Optional[str]:
        """Extract JSON output URL from plan info."""
        try:
            links = plan_info.get('data', {}).get('links', {})
            json_link = links.get('json-output-redacted')
            
            if json_link:
                server = self.config['tfe_server']
                return f"https://{server}{json_link}"
            
            return None
            
        except (KeyError, TypeError):
            return None
    
    def _download_json_output(self, json_url: str) -> Tuple[Optional[Dict], Optional[str]]:
        """Download JSON output from URL."""
        token = self.config['token']
        
        headers = {
            "Authorization": f"Bearer {token}"
        }
        
        try:
            response = requests.get(json_url, headers=headers, verify=self.verify_ssl, timeout=60)
            
            if response.status_code == 200:
                try:
                    return response.json(), None
                except json.JSONDecodeError as e:
                    return None, f"Failed to parse JSON output: {str(e)}"
            elif response.status_code == 403:
                return None, "Access denied. Check permissions for plan JSON output."
            elif response.status_code == 404:
                return None, "Plan JSON output not found or expired."
            else:
                return None, f"JSON download failed: {response.status_code}"
                
        except requests.exceptions.RequestException as e:
            return None, f"JSON download request error: {e}"
        except Exception as e:
            return None, f"JSON download error: {e}"
    
    def _check_run_status(self, run_info: Dict) -> Optional[str]:
        """Check run status and return warning if there are issues."""
        try:
            attributes = run_info.get('data', {}).get('attributes', {})
            status = attributes.get('status')
            has_changes = attributes.get('has-changes')
            
            # Check for various status conditions
            if status == 'errored':
                return f"⚠️ Run failed with errors. Status: {status}"
            elif status == 'canceled':
                return f"⚠️ Run was canceled. Status: {status}"
            elif status == 'force_canceled':
                return f"⚠️ Run was force canceled. Status: {status}"
            elif status in ['planning', 'plan_queued']:
                return f"ℹ️ Run is still planning. Status: {status}"
            elif status == 'planned' and not has_changes:
                return f"ℹ️ Plan completed with no changes. Status: {status}"
            elif status in ['applying', 'apply_queued']:
                return f"ℹ️ Run is currently applying changes. Status: {status}"
            elif status == 'applied':
                return f"✅ Run completed successfully. Status: {status}"
            elif status == 'planned_and_finished':
                return f"✅ Plan completed (plan-only run). Status: {status}"
            
            return None
            
        except (KeyError, TypeError):
            return "⚠️ Could not determine run status"
    
    def _check_plan_status(self, plan_info: Dict) -> Optional[str]:
        """Check plan status and return warning if there are issues."""
        try:
            attributes = plan_info.get('data', {}).get('attributes', {})
            status = attributes.get('status')
            has_changes = attributes.get('has-changes')
            resource_additions = attributes.get('resource-additions', 0)
            resource_changes = attributes.get('resource-changes', 0)
            resource_destructions = attributes.get('resource-destructions', 0)
            
            # Check for plan status issues
            if status == 'errored':
                return f"❌ Plan failed with errors. Status: {status}"
            elif status == 'canceled':
                return f"⚠️ Plan was canceled. Status: {status}"
            elif status == 'running':
                return f"ℹ️ Plan is still running. Status: {status}"
            elif status == 'finished' and not has_changes:
                return f"ℹ️ Plan completed with no changes to apply"
            elif status == 'finished' and has_changes:
                total_changes = resource_additions + resource_changes + resource_destructions
                return f"✅ Plan completed successfully with {total_changes} changes (+{resource_additions} ~{resource_changes} -{resource_destructions})"
            
            return None
            
        except (KeyError, TypeError):
            return "⚠️ Could not determine plan status"
    
    def get_masked_config(self) -> Dict[str, Any]:
        """Get configuration with sensitive values masked."""
        if not self.config:
            return {}
        
        masked_config = self.config.copy()
        
        # Mask token
        if 'token' in masked_config:
            token = masked_config['token']
            if len(token) > 8:
                masked_config['token'] = f"{token[:4]}{'*' * (len(token) - 8)}{token[-4:]}"
            else:
                masked_config['token'] = '*' * len(token)
        
        return masked_config


def process_tfe_yaml_upload(yaml_content: str) -> Tuple[Optional[Dict], Optional[str]]:
    """
    Process TFE YAML upload and return plan data.
    
    This is the main integration function used by the dashboard components.
    
    Args:
        yaml_content: YAML configuration content
        
    Returns:
        Tuple of (plan_data, error_message)
    """
    client = StandaloneTFEClient()
    
    # Load configuration
    config_loaded, config_error = client.load_config_from_yaml(yaml_content)
    if not config_loaded:
        return None, f"Configuration error: {config_error}"
    
    # Authenticate
    authenticated, auth_error = client.authenticate()
    if not authenticated:
        return None, f"Authentication error: {auth_error}"
    
    # Get plan data
    plan_data, plan_error = client.get_plan_json()
    if plan_error:
        return None, f"Plan retrieval error: {plan_error}"
    
    return plan_data, None
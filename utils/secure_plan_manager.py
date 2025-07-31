"""
Secure Plan Manager

Handles Terraform plan JSON data with the same security principles as credentials.
Provides memory-only storage, automatic cleanup, and secure handling of sensitive
plan data throughout the application lifecycle.
"""

import weakref
import atexit
from typing import Dict, Any, Optional
from dataclasses import dataclass
import json


@dataclass
class PlanMetadata:
    """Metadata about a plan without sensitive content"""
    terraform_version: str
    format_version: str
    resource_count: int
    action_summary: Dict[str, int]
    source: str  # 'file_upload' or 'tfe_integration'
    workspace_id: Optional[str] = None
    run_id: Optional[str] = None


class SecurePlanManager:
    """
    Secure manager for Terraform plan JSON data.
    
    Handles plan data with the same security principles as credentials:
    - Memory-only storage (never persisted to disk)
    - Automatic cleanup on session end
    - Masked values in error messages and logs
    - Secure handling throughout lifecycle
    """
    
    # Class-level registry to track all instances for cleanup
    _instances = weakref.WeakSet()
    
    def __init__(self):
        """Initialize secure plan manager with memory-only storage."""
        self._plan_data: Optional[Dict[str, Any]] = None
        self._plan_metadata: Optional[PlanMetadata] = None
        self._is_sensitive = True  # Always treat plan data as sensitive
        
        # Register this instance for cleanup
        SecurePlanManager._instances.add(self)
        
        # Register cleanup on exit
        atexit.register(self._cleanup_on_exit)
    
    def store_plan_data(self, plan_data: Dict[str, Any], source: str = "unknown", 
                       workspace_id: Optional[str] = None, run_id: Optional[str] = None) -> None:
        """
        Store plan data securely in memory only.
        
        Args:
            plan_data: The Terraform plan JSON data
            source: Source of the plan data ('file_upload' or 'tfe_integration')
            workspace_id: Optional workspace ID for TFE plans
            run_id: Optional run ID for TFE plans
        """
        # Store plan data in memory only (even empty dict is valid plan data)
        self._plan_data = plan_data.copy() if plan_data is not None else None
        
        # Extract and store non-sensitive metadata
        if plan_data is not None:
            self._plan_metadata = self._extract_metadata(plan_data, source, workspace_id, run_id)
        else:
            self._plan_metadata = None
    
    def get_plan_data(self) -> Optional[Dict[str, Any]]:
        """
        Retrieve stored plan data.
        
        Returns:
            Deep copy of plan data or None if not stored
        """
        if self._plan_data is None:
            return None
        
        # Return deep copy to prevent external modification
        return json.loads(json.dumps(self._plan_data))
    
    def get_plan_metadata(self) -> Optional[PlanMetadata]:
        """
        Get non-sensitive plan metadata.
        
        Returns:
            PlanMetadata object or None if no plan stored
        """
        return self._plan_metadata
    
    def has_plan_data(self) -> bool:
        """
        Check if plan data is currently stored.
        
        Returns:
            True if plan data is available, False otherwise
        """
        return self._plan_data is not None
    
    def get_masked_summary(self) -> Dict[str, Any]:
        """
        Get plan summary with sensitive values masked.
        
        Returns:
            Dictionary with plan summary and masked sensitive data
        """
        if not self._plan_metadata:
            return {"status": "no_plan_data"}
        
        return {
            "terraform_version": self._plan_metadata.terraform_version,
            "format_version": self._plan_metadata.format_version,
            "resource_count": self._plan_metadata.resource_count,
            "actions": self._plan_metadata.action_summary,
            "source": self._plan_metadata.source,
            "workspace_id": self._mask_id(self._plan_metadata.workspace_id) if self._plan_metadata.workspace_id else None,
            "run_id": self._mask_id(self._plan_metadata.run_id) if self._plan_metadata.run_id else None,
            "data_size": f"~{len(str(self._plan_data)) // 1024}KB" if self._plan_data else "0KB"
        }
    
    def clear_plan_data(self) -> None:
        """Clear all stored plan data from memory."""
        if self._plan_data:
            # Overwrite sensitive data before clearing (defense in depth)
            self._overwrite_sensitive_data(self._plan_data)
            self._plan_data = None
        
        self._plan_metadata = None
    
    def get_safe_error_context(self, error_context: str = "") -> str:
        """
        Get error context without exposing sensitive plan data.
        
        Args:
            error_context: Additional context for the error
            
        Returns:
            Safe error context string without sensitive data
        """
        if not self._plan_metadata:
            return f"No plan data available. {error_context}".strip()
        
        safe_context = (
            f"Plan processing error. "
            f"Source: {self._plan_metadata.source}, "
            f"Resources: {self._plan_metadata.resource_count}, "
            f"Terraform: {self._plan_metadata.terraform_version}"
        )
        
        if error_context:
            safe_context += f". {error_context}"
        
        return safe_context
    
    def _extract_metadata(self, plan_data: Dict[str, Any], source: str, 
                         workspace_id: Optional[str], run_id: Optional[str]) -> PlanMetadata:
        """
        Extract non-sensitive metadata from plan data.
        
        Args:
            plan_data: The plan JSON data
            source: Source of the plan data
            workspace_id: Optional workspace ID
            run_id: Optional run ID
            
        Returns:
            PlanMetadata object with non-sensitive information
        """
        # Extract basic information
        terraform_version = plan_data.get('terraform_version', 'unknown')
        format_version = plan_data.get('format_version', 'unknown')
        
        # Count resources and actions
        resource_changes = plan_data.get('resource_changes', [])
        resource_count = len(resource_changes)
        
        # Summarize actions without exposing resource details
        action_summary = {}
        for change in resource_changes:
            actions = change.get('change', {}).get('actions', [])
            for action in actions:
                action_summary[action] = action_summary.get(action, 0) + 1
        
        return PlanMetadata(
            terraform_version=terraform_version,
            format_version=format_version,
            resource_count=resource_count,
            action_summary=action_summary,
            source=source,
            workspace_id=workspace_id,
            run_id=run_id
        )
    
    def _mask_id(self, id_value: str) -> str:
        """
        Mask ID for safe display.
        
        Args:
            id_value: ID to mask
            
        Returns:
            Masked ID string
        """
        if not id_value or len(id_value) <= 8:
            return '*' * len(id_value) if id_value else ''
        
        # Show prefix and suffix, mask the middle
        return f"{id_value[:4]}{'*' * (len(id_value) - 8)}{id_value[-4:]}"
    
    def _overwrite_sensitive_data(self, data: Any) -> None:
        """
        Recursively overwrite sensitive data in memory.
        
        Args:
            data: Data structure to overwrite
        """
        if isinstance(data, dict):
            for key in data:
                if isinstance(data[key], (dict, list)):
                    self._overwrite_sensitive_data(data[key])
                elif isinstance(data[key], str):
                    data[key] = '*' * len(data[key])
                else:
                    data[key] = None
        elif isinstance(data, list):
            for i, item in enumerate(data):
                if isinstance(item, (dict, list)):
                    self._overwrite_sensitive_data(item)
                elif isinstance(item, str):
                    data[i] = '*' * len(item)
                else:
                    data[i] = None
    
    def _cleanup_on_exit(self) -> None:
        """Cleanup plan data on application exit."""
        self.clear_plan_data()
    
    @classmethod
    def cleanup_all_instances(cls) -> None:
        """Clean up all plan manager instances."""
        for instance in cls._instances:
            try:
                instance.clear_plan_data()
            except Exception:
                # Ignore errors during cleanup
                pass


# Register global cleanup
atexit.register(SecurePlanManager.cleanup_all_instances)
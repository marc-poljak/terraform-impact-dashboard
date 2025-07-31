"""
Secure credential manager for TFE integration.

This module provides secure handling of TFE credentials with memory-only storage,
credential validation, and masking functionality to prevent accidental exposure
of sensitive information.
"""

import re
import weakref
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
import atexit
import threading
import time


@dataclass
class TFEConfig:
    """Configuration data class for TFE connection details."""
    tfe_server: str
    organization: str
    token: str
    workspace_id: str
    run_id: str
    verify_ssl: bool = True
    timeout: int = 30
    retry_attempts: int = 3
    
    def __repr__(self) -> str:
        """Return a safe string representation without exposing credentials."""
        # Mask sensitive fields
        masked_token = self._mask_token(self.token)
        masked_org = self._mask_sensitive_field(self.organization) if any(
            pattern in self.organization.lower() for pattern in ['secret', 'confidential', 'private', 'internal']
        ) else self.organization
        
        return (f"TFEConfig(tfe_server='{self.tfe_server}', "
                f"organization='{masked_org}', "
                f"token='{masked_token}', "
                f"workspace_id='{self.workspace_id}', "
                f"run_id='{self.run_id}', "
                f"verify_ssl={self.verify_ssl}, "
                f"timeout={self.timeout}, "
                f"retry_attempts={self.retry_attempts})")
    
    def _mask_token(self, token: str) -> str:
        """Mask token for safe display."""
        if len(token) <= 8:
            return '*' * len(token)
        return f"{token[:4]}{'*' * (len(token) - 8)}{token[-4:]}"
    
    def _mask_sensitive_field(self, value: str) -> str:
        """Mask sensitive field values for safe display."""
        if len(value) <= 6:
            return '*' * len(value)
        return f"{value[:2]}{'*' * (len(value) - 4)}{value[-2:]}"


class CredentialManager:
    """
    Secure credential manager for TFE integration.
    
    Handles secure storage of TFE credentials in memory only, provides
    credential validation and masking functionality, and ensures proper
    cleanup of sensitive data.
    """
    
    # Class-level registry to track all instances for cleanup
    _instances = weakref.WeakSet()
    # Session cleanup tracking
    _session_cleanup_timer: Optional[threading.Timer] = None
    _session_timeout = 3600  # 1 hour default session timeout
    
    def __init__(self):
        """Initialize credential manager with memory-only storage."""
        self._credentials: Optional[Dict[str, Any]] = None
        self._config: Optional[TFEConfig] = None
        self._last_access_time = time.time()
        self._session_active = False
        
        # Register this instance for cleanup
        CredentialManager._instances.add(self)
        
        # Register cleanup on exit
        atexit.register(self._cleanup_on_exit)
    
    def store_credentials(self, config: Dict[str, Any]) -> None:
        """
        Store credentials securely in memory only.
        
        Args:
            config: Dictionary containing TFE configuration data
            
        Raises:
            ValueError: If configuration validation fails
        """
        # Validate configuration first
        is_valid, errors = self.validate_config(config)
        if not is_valid:
            raise ValueError(f"Invalid configuration: {', '.join(errors)}")
        
        # Store credentials in memory only
        self._credentials = config.copy()
        
        # Create TFEConfig object for structured access
        self._config = TFEConfig(
            tfe_server=config['tfe_server'],
            organization=config['organization'],
            token=config['token'],
            workspace_id=config['workspace_id'],
            run_id=config['run_id'],
            verify_ssl=config.get('verify_ssl', True),
            timeout=config.get('timeout', 30),
            retry_attempts=config.get('retry_attempts', 3)
        )
        
        # Update session tracking
        self._last_access_time = time.time()
        self._session_active = True
        
        # Start session cleanup timer
        self._start_session_cleanup_timer()
    
    def get_credentials(self) -> Optional[Dict[str, Any]]:
        """
        Retrieve stored credentials.
        
        Returns:
            Dictionary containing credentials or None if not stored
        """
        if self._credentials:
            self._update_last_access()
        return self._credentials.copy() if self._credentials else None
    
    def get_config(self) -> Optional[TFEConfig]:
        """
        Get structured configuration object.
        
        Returns:
            TFEConfig object or None if not stored
        """
        if self._config:
            self._update_last_access()
        return self._config
    
    def get_masked_config(self) -> Dict[str, Any]:
        """
        Get configuration with sensitive values masked.
        
        Returns:
            Dictionary with sensitive values masked for safe display
        """
        if not self._credentials:
            return {}
        
        masked_config = self._credentials.copy()
        
        # Mask sensitive fields
        if 'token' in masked_config:
            masked_config['token'] = self._mask_token(masked_config['token'])
        
        # Mask organization name if it contains sensitive patterns
        if 'organization' in masked_config:
            org = masked_config['organization']
            if any(pattern in org.lower() for pattern in ['secret', 'confidential', 'private', 'internal']):
                masked_config['organization'] = self._mask_sensitive_field(org)
        
        # Mask workspace and run IDs if they contain sensitive patterns
        for field in ['workspace_id', 'run_id']:
            if field in masked_config:
                value = masked_config[field]
                if any(pattern in value.upper() for pattern in ['SECRET', 'CONFIDENTIAL', 'SENSITIVE', 'PRIVATE']):
                    masked_config[field] = self._mask_sensitive_field(value)
        
        return masked_config
    
    def clear_credentials(self) -> None:
        """Clear all stored credentials from memory."""
        if self._credentials:
            # Overwrite sensitive data before clearing
            for key in self._credentials:
                if isinstance(self._credentials[key], str):
                    self._credentials[key] = '*' * len(self._credentials[key])
            
            self._credentials.clear()
            self._credentials = None
        
        self._config = None
        self._session_active = False
        
        # Cancel session cleanup timer
        self._cancel_session_cleanup_timer()
    
    def validate_config(self, config: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate TFE configuration structure and values.
        
        Args:
            config: Configuration dictionary to validate
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        from utils.tfe_config_validator import TFEConfigValidator
        
        validator = TFEConfigValidator()
        is_valid = validator.validate_config_schema(config)
        
        # Convert ValidationError objects to simple error messages
        error_messages = [error.message for error in validator.errors]
        
        return is_valid, error_messages
    
    def validate_yaml_content(self, yaml_content: str) -> Tuple[bool, Optional[Dict[str, Any]], List[str]]:
        """
        Validate YAML content and return parsed configuration.
        
        Args:
            yaml_content: Raw YAML content as string
            
        Returns:
            Tuple of (is_valid, parsed_config, error_messages)
        """
        from utils.tfe_config_validator import TFEConfigValidator
        
        validator = TFEConfigValidator()
        is_valid, config, validation_errors = validator.validate_yaml_content(yaml_content)
        
        # Convert ValidationError objects to simple error messages
        error_messages = [error.message for error in validation_errors]
        
        return is_valid, config, error_messages
    
    def _mask_token(self, token: str) -> str:
        """
        Mask token for safe display.
        
        Args:
            token: Token to mask
            
        Returns:
            Masked token string
        """
        if len(token) <= 8:
            return '*' * len(token)
        
        # Show first 4 and last 4 characters, mask the middle
        return f"{token[:4]}{'*' * (len(token) - 8)}{token[-4:]}"
    
    def _mask_sensitive_field(self, value: str) -> str:
        """
        Mask sensitive field values for safe display.
        
        Args:
            value: Value to mask
            
        Returns:
            Masked value string
        """
        if len(value) <= 6:
            return '*' * len(value)
        
        # Show first 2 and last 2 characters, mask the middle
        return f"{value[:2]}{'*' * (len(value) - 4)}{value[-2:]}"
    
    def _update_last_access(self) -> None:
        """Update last access time for session management."""
        self._last_access_time = time.time()
        
        # Restart session cleanup timer if session is active
        if self._session_active:
            self._start_session_cleanup_timer()
    
    def _start_session_cleanup_timer(self) -> None:
        """Start or restart the session cleanup timer."""
        # Cancel existing timer
        self._cancel_session_cleanup_timer()
        
        # Start new timer
        CredentialManager._session_cleanup_timer = threading.Timer(
            self._session_timeout, 
            self._session_timeout_cleanup
        )
        CredentialManager._session_cleanup_timer.daemon = True
        CredentialManager._session_cleanup_timer.start()
    
    def _cancel_session_cleanup_timer(self) -> None:
        """Cancel the session cleanup timer."""
        if CredentialManager._session_cleanup_timer:
            CredentialManager._session_cleanup_timer.cancel()
            CredentialManager._session_cleanup_timer = None
    
    def _session_timeout_cleanup(self) -> None:
        """Cleanup credentials when session times out."""
        current_time = time.time()
        
        # Check if session has actually timed out
        if current_time - self._last_access_time >= self._session_timeout:
            self.clear_credentials()
        else:
            # Session was accessed recently, restart timer
            remaining_time = self._session_timeout - (current_time - self._last_access_time)
            CredentialManager._session_cleanup_timer = threading.Timer(
                remaining_time, 
                self._session_timeout_cleanup
            )
            CredentialManager._session_cleanup_timer.daemon = True
            CredentialManager._session_cleanup_timer.start()
    
    def set_session_timeout(self, timeout_seconds: int) -> None:
        """
        Set session timeout for automatic credential cleanup.
        
        Args:
            timeout_seconds: Timeout in seconds (minimum 60 seconds)
        """
        if timeout_seconds < 60:
            raise ValueError("Session timeout must be at least 60 seconds")
        
        self._session_timeout = timeout_seconds
        
        # Restart timer with new timeout if session is active
        if self._session_active:
            self._start_session_cleanup_timer()
    
    def get_session_info(self) -> Dict[str, Any]:
        """
        Get information about current session.
        
        Returns:
            Dictionary containing session information
        """
        if not self._session_active:
            return {
                'active': False,
                'time_remaining': 0,
                'last_access': None
            }
        
        current_time = time.time()
        time_since_access = current_time - self._last_access_time
        time_remaining = max(0, self._session_timeout - time_since_access)
        
        return {
            'active': True,
            'time_remaining': int(time_remaining),
            'last_access': self._last_access_time,
            'timeout_seconds': self._session_timeout
        }
    
    def extend_session(self) -> None:
        """Extend the current session by updating last access time."""
        if self._session_active:
            self._update_last_access()
    
    def _cleanup_on_exit(self) -> None:
        """Cleanup credentials on application exit."""
        self.clear_credentials()
    
    @classmethod
    def cleanup_all_instances(cls) -> None:
        """Clean up all credential manager instances."""
        # Cancel global session timer
        if cls._session_cleanup_timer:
            cls._session_cleanup_timer.cancel()
            cls._session_cleanup_timer = None
        
        for instance in cls._instances:
            try:
                instance.clear_credentials()
            except Exception:
                # Ignore errors during cleanup
                pass


# Register global cleanup
atexit.register(CredentialManager.cleanup_all_instances)
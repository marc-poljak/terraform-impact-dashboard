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


class CredentialManager:
    """
    Secure credential manager for TFE integration.
    
    Handles secure storage of TFE credentials in memory only, provides
    credential validation and masking functionality, and ensures proper
    cleanup of sensitive data.
    """
    
    # Class-level registry to track all instances for cleanup
    _instances = weakref.WeakSet()
    
    def __init__(self):
        """Initialize credential manager with memory-only storage."""
        self._credentials: Optional[Dict[str, Any]] = None
        self._config: Optional[TFEConfig] = None
        
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
    
    def get_credentials(self) -> Optional[Dict[str, Any]]:
        """
        Retrieve stored credentials.
        
        Returns:
            Dictionary containing credentials or None if not stored
        """
        return self._credentials.copy() if self._credentials else None
    
    def get_config(self) -> Optional[TFEConfig]:
        """
        Get structured configuration object.
        
        Returns:
            TFEConfig object or None if not stored
        """
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
    
    def _cleanup_on_exit(self) -> None:
        """Cleanup credentials on application exit."""
        self.clear_credentials()
    
    @classmethod
    def cleanup_all_instances(cls) -> None:
        """Clean up all credential manager instances."""
        for instance in cls._instances:
            try:
                instance.clear_credentials()
            except Exception:
                # Ignore errors during cleanup
                pass


# Register global cleanup
atexit.register(CredentialManager.cleanup_all_instances)
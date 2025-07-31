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
        errors = []
        
        # Required fields
        required_fields = ['tfe_server', 'organization', 'token', 'workspace_id', 'run_id']
        
        for field in required_fields:
            if field not in config:
                errors.append(f"Missing required field: {field}")
            elif not config[field] or not isinstance(config[field], str):
                errors.append(f"Field '{field}' must be a non-empty string")
        
        # Validate specific field formats if present
        if 'tfe_server' in config and config['tfe_server']:
            if not self._validate_server_url(config['tfe_server']):
                errors.append("Invalid tfe_server format. Must be a valid URL or hostname")
        
        if 'workspace_id' in config and config['workspace_id']:
            if not self._validate_workspace_id(config['workspace_id']):
                errors.append("Invalid workspace_id format. Must start with 'ws-'")
        
        if 'run_id' in config and config['run_id']:
            if not self._validate_run_id(config['run_id']):
                errors.append("Invalid run_id format. Must start with 'run-'")
        
        if 'token' in config and config['token']:
            if not self._validate_token_format(config['token']):
                errors.append("Invalid token format")
        
        # Validate optional fields
        if 'verify_ssl' in config and not isinstance(config['verify_ssl'], bool):
            errors.append("Field 'verify_ssl' must be a boolean")
        
        if 'timeout' in config:
            if not isinstance(config['timeout'], int) or config['timeout'] <= 0:
                errors.append("Field 'timeout' must be a positive integer")
        
        if 'retry_attempts' in config:
            if not isinstance(config['retry_attempts'], int) or config['retry_attempts'] < 0:
                errors.append("Field 'retry_attempts' must be a non-negative integer")
        
        # Check for security anti-patterns
        security_errors = self._check_security_patterns(config)
        errors.extend(security_errors)
        
        return len(errors) == 0, errors
    
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
    
    def _validate_server_url(self, server: str) -> bool:
        """Validate TFE server URL format."""
        # Check for protocol prefix
        has_protocol = server.startswith(('http://', 'https://'))
        if has_protocol:
            # Remove protocol for validation
            server_part = server.split('://', 1)[1]
            # Don't allow ftp or other protocols
            if not server.startswith(('http://', 'https://')):
                return False
        else:
            server_part = server
        
        # Remove trailing slash and port for domain validation
        server_part = server_part.rstrip('/')
        port = None
        if ':' in server_part:
            server_part, port = server_part.rsplit(':', 1)
            # Validate port
            try:
                port_num = int(port)
                if not (1 <= port_num <= 65535):
                    return False
            except ValueError:
                return False
        
        # Allow localhost and IP addresses
        if server_part.lower() in ['localhost', '127.0.0.1']:
            return True
        
        # Must contain at least one dot for domain
        if '.' not in server_part:
            return False
        
        # Validate domain format
        domain_pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)+$'
        return bool(re.match(domain_pattern, server_part))
    
    def _validate_workspace_id(self, workspace_id: str) -> bool:
        """Validate workspace ID format."""
        # Terraform workspace IDs start with 'ws-' followed by alphanumeric characters
        return bool(re.match(r'^ws-[a-zA-Z0-9]+$', workspace_id))
    
    def _validate_run_id(self, run_id: str) -> bool:
        """Validate run ID format."""
        # Terraform run IDs start with 'run-' followed by alphanumeric characters
        return bool(re.match(r'^run-[a-zA-Z0-9]+$', run_id))
    
    def _validate_token_format(self, token: str) -> bool:
        """Validate token format."""
        # Basic validation - token should be reasonable length and contain valid characters
        if len(token) < 10 or len(token) > 200:
            return False
        
        # Should contain only alphanumeric characters, dots, and hyphens
        return bool(re.match(r'^[a-zA-Z0-9\.\-_]+$', token))
    
    def _check_security_patterns(self, config: Dict[str, Any]) -> List[str]:
        """
        Check for obvious security anti-patterns.
        
        Args:
            config: Configuration to check
            
        Returns:
            List of security warnings
        """
        warnings = []
        
        # Check for obviously fake or placeholder tokens
        if 'token' in config:
            token = config['token'].lower()
            suspicious_patterns = [
                'your-token-here', 'placeholder', 'example', 'test-token',
                'fake-token', 'dummy', 'sample', 'xxx', 'yyy', 'zzz'
            ]
            
            for pattern in suspicious_patterns:
                if pattern in token:
                    warnings.append(f"Token appears to contain placeholder text: {pattern}")
                    break
        
        return warnings
    
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
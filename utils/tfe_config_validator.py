"""
TFE Configuration Validator

This module provides comprehensive validation for TFE configuration files,
including YAML schema validation, format validation for workspace and run IDs,
and detailed error messages to help users troubleshoot configuration issues.
"""

import re
import yaml
from typing import Dict, Any, List, Tuple, Optional, Union
from dataclasses import dataclass
from urllib.parse import urlparse


@dataclass
class ValidationError:
    """Represents a configuration validation error with detailed information."""
    field: str
    message: str
    suggestion: Optional[str] = None
    error_code: Optional[str] = None


class TFEConfigValidator:
    """
    Comprehensive validator for TFE configuration files.
    
    Provides schema validation, format validation, and detailed error messages
    to help users create valid TFE configurations.
    """
    
    # Configuration schema definition
    SCHEMA = {
        'required_fields': {
            'tfe_server': {
                'type': str,
                'description': 'TFE server URL (e.g., app.terraform.io)',
                'example': 'app.terraform.io'
            },
            'organization': {
                'type': str,
                'description': 'TFE organization name',
                'example': 'my-organization'
            },
            'token': {
                'type': str,
                'description': 'TFE API token',
                'example': 'your-api-token-here'
            },
            'workspace_id': {
                'type': str,
                'description': 'Workspace identifier (starts with ws-)',
                'example': 'ws-ABC123456789'
            },
            'run_id': {
                'type': str,
                'description': 'Run identifier (starts with run-)',
                'example': 'run-XYZ987654321'
            }
        },
        'optional_fields': {
            'verify_ssl': {
                'type': bool,
                'default': True,
                'description': 'Enable SSL certificate verification'
            },
            'timeout': {
                'type': int,
                'default': 30,
                'min': 1,
                'max': 300,
                'description': 'Request timeout in seconds'
            },
            'retry_attempts': {
                'type': int,
                'default': 3,
                'min': 0,
                'max': 10,
                'description': 'Number of retry attempts for failed requests'
            }
        }
    }
    
    def __init__(self):
        """Initialize the validator."""
        self.errors: List[ValidationError] = []
    
    def validate_yaml_content(self, yaml_content: str) -> Tuple[bool, Optional[Dict[str, Any]], List[ValidationError]]:
        """
        Validate YAML content and parse configuration.
        
        Args:
            yaml_content: Raw YAML content as string
            
        Returns:
            Tuple of (is_valid, parsed_config, validation_errors)
        """
        self.errors = []
        
        # Step 1: Parse YAML
        try:
            config = yaml.safe_load(yaml_content)
        except yaml.YAMLError as e:
            self.errors.append(ValidationError(
                field='yaml_syntax',
                message=f'Invalid YAML syntax: {str(e)}',
                suggestion='Check YAML formatting, indentation, and special characters',
                error_code='YAML_PARSE_ERROR'
            ))
            return False, None, self.errors
        
        # Step 2: Validate parsed configuration
        if config is None:
            self.errors.append(ValidationError(
                field='yaml_content',
                message='YAML file is empty or contains only comments',
                suggestion='Add configuration fields to the YAML file',
                error_code='EMPTY_CONFIG'
            ))
            return False, None, self.errors
        
        if not isinstance(config, dict):
            self.errors.append(ValidationError(
                field='yaml_structure',
                message='Configuration must be a YAML object/dictionary',
                suggestion='Ensure the YAML file contains key-value pairs, not a list or scalar value',
                error_code='INVALID_STRUCTURE'
            ))
            return False, None, self.errors
        
        # Step 3: Validate configuration schema
        is_valid = self.validate_config_schema(config)
        
        return is_valid, config if is_valid else None, self.errors
    
    def validate_config_schema(self, config: Dict[str, Any]) -> bool:
        """
        Validate configuration against schema.
        
        Args:
            config: Parsed configuration dictionary
            
        Returns:
            True if valid, False otherwise (errors stored in self.errors)
        """
        self.errors = []
        
        # Validate required fields
        self._validate_required_fields(config)
        
        # Validate optional fields
        self._validate_optional_fields(config)
        
        # Validate field formats
        self._validate_field_formats(config)
        
        # Check for unknown fields
        self._check_unknown_fields(config)
        
        # Perform security checks
        self._perform_security_checks(config)
        
        return len(self.errors) == 0
    
    def _validate_required_fields(self, config: Dict[str, Any]) -> None:
        """Validate all required fields are present and have correct types."""
        for field_name, field_spec in self.SCHEMA['required_fields'].items():
            if field_name not in config:
                self.errors.append(ValidationError(
                    field=field_name,
                    message=f'Required field "{field_name}" is missing',
                    suggestion=f'Add {field_name}: {field_spec["example"]} to your configuration',
                    error_code='MISSING_REQUIRED_FIELD'
                ))
                continue
            
            value = config[field_name]
            
            # Check for empty values
            if value is None or (isinstance(value, str) and not value.strip()):
                self.errors.append(ValidationError(
                    field=field_name,
                    message=f'Required field "{field_name}" cannot be empty',
                    suggestion=f'Provide a valid value for {field_name}. Example: {field_spec["example"]}',
                    error_code='EMPTY_REQUIRED_FIELD'
                ))
                continue
            
            # Check type
            expected_type = field_spec['type']
            if not isinstance(value, expected_type):
                self.errors.append(ValidationError(
                    field=field_name,
                    message=f'Field "{field_name}" must be of type {expected_type.__name__}, got {type(value).__name__}',
                    suggestion=f'Ensure {field_name} is a {expected_type.__name__}. Example: {field_spec["example"]}',
                    error_code='INVALID_FIELD_TYPE'
                ))
    
    def _validate_optional_fields(self, config: Dict[str, Any]) -> None:
        """Validate optional fields if present."""
        for field_name, field_spec in self.SCHEMA['optional_fields'].items():
            if field_name not in config:
                continue
            
            value = config[field_name]
            expected_type = field_spec['type']
            
            # Check type
            if not isinstance(value, expected_type):
                self.errors.append(ValidationError(
                    field=field_name,
                    message=f'Optional field "{field_name}" must be of type {expected_type.__name__}, got {type(value).__name__}',
                    suggestion=f'Ensure {field_name} is a {expected_type.__name__} or remove it to use default value ({field_spec["default"]})',
                    error_code='INVALID_OPTIONAL_FIELD_TYPE'
                ))
                continue
            
            # Check range constraints for numeric fields
            if expected_type == int:
                min_val = field_spec.get('min')
                max_val = field_spec.get('max')
                
                if min_val is not None and value < min_val:
                    self.errors.append(ValidationError(
                        field=field_name,
                        message=f'Field "{field_name}" must be at least {min_val}, got {value}',
                        suggestion=f'Set {field_name} to a value between {min_val} and {max_val}',
                        error_code='VALUE_TOO_LOW'
                    ))
                
                if max_val is not None and value > max_val:
                    self.errors.append(ValidationError(
                        field=field_name,
                        message=f'Field "{field_name}" must be at most {max_val}, got {value}',
                        suggestion=f'Set {field_name} to a value between {min_val} and {max_val}',
                        error_code='VALUE_TOO_HIGH'
                    ))
    
    def _validate_field_formats(self, config: Dict[str, Any]) -> None:
        """Validate specific field formats."""
        # Validate TFE server URL (only if it's a string)
        if 'tfe_server' in config and config['tfe_server'] and isinstance(config['tfe_server'], str):
            self._validate_tfe_server(config['tfe_server'])
        
        # Validate workspace ID (only if it's a string)
        if 'workspace_id' in config and config['workspace_id'] and isinstance(config['workspace_id'], str):
            self._validate_workspace_id(config['workspace_id'])
        
        # Validate run ID (only if it's a string)
        if 'run_id' in config and config['run_id'] and isinstance(config['run_id'], str):
            self._validate_run_id(config['run_id'])
        
        # Validate token format (only if it's a string)
        if 'token' in config and config['token'] and isinstance(config['token'], str):
            self._validate_token_format(config['token'])
        
        # Validate organization name (only if it's a string)
        if 'organization' in config and config['organization'] and isinstance(config['organization'], str):
            self._validate_organization_name(config['organization'])
    
    def _validate_tfe_server(self, server: str) -> None:
        """Validate TFE server URL format."""
        # Remove protocol if present for validation
        server_clean = server
        has_protocol = False
        
        if server.startswith(('http://', 'https://')):
            has_protocol = True
            protocol, server_clean = server.split('://', 1)
            
            # Warn about http (insecure)
            if protocol == 'http':
                self.errors.append(ValidationError(
                    field='tfe_server',
                    message='Using insecure HTTP protocol',
                    suggestion='Use HTTPS for secure communication with TFE server',
                    error_code='INSECURE_PROTOCOL'
                ))
        
        # Remove trailing slash and path
        server_clean = server_clean.rstrip('/').split('/')[0]
        
        # Handle port
        if ':' in server_clean:
            host, port = server_clean.rsplit(':', 1)
            try:
                port_num = int(port)
                if not (1 <= port_num <= 65535):
                    self.errors.append(ValidationError(
                        field='tfe_server',
                        message=f'Invalid port number: {port}',
                        suggestion='Use a port number between 1 and 65535',
                        error_code='INVALID_PORT'
                    ))
                    return
            except ValueError:
                self.errors.append(ValidationError(
                    field='tfe_server',
                    message=f'Invalid port format: {port}',
                    suggestion='Port must be a number (e.g., example.com:443)',
                    error_code='INVALID_PORT_FORMAT'
                ))
                return
        else:
            host = server_clean
        
        # Validate hostname
        if not self._is_valid_hostname(host):
            self.errors.append(ValidationError(
                field='tfe_server',
                message=f'Invalid hostname format: {host}',
                suggestion='Use a valid hostname (e.g., app.terraform.io) or IP address',
                error_code='INVALID_HOSTNAME'
            ))
    
    def _validate_workspace_id(self, workspace_id: str) -> None:
        """Validate workspace ID format."""
        if not re.match(r'^ws-[a-zA-Z0-9]{6,}$', workspace_id):
            self.errors.append(ValidationError(
                field='workspace_id',
                message=f'Invalid workspace ID format: {workspace_id}',
                suggestion='Workspace ID must start with "ws-" followed by at least 6 alphanumeric characters (e.g., ws-ABC123456789)',
                error_code='INVALID_WORKSPACE_ID'
            ))
    
    def _validate_run_id(self, run_id: str) -> None:
        """Validate run ID format."""
        if not re.match(r'^run-[a-zA-Z0-9]{6,}$', run_id):
            self.errors.append(ValidationError(
                field='run_id',
                message=f'Invalid run ID format: {run_id}',
                suggestion='Run ID must start with "run-" followed by at least 6 alphanumeric characters (e.g., run-XYZ987654321)',
                error_code='INVALID_RUN_ID'
            ))
    
    def _validate_token_format(self, token: str) -> None:
        """Validate API token format."""
        # Check length
        if len(token) < 10:
            self.errors.append(ValidationError(
                field='token',
                message='API token is too short',
                suggestion='API tokens should be at least 10 characters long',
                error_code='TOKEN_TOO_SHORT'
            ))
            return
        
        if len(token) > 200:
            self.errors.append(ValidationError(
                field='token',
                message='API token is too long',
                suggestion='API tokens should not exceed 200 characters',
                error_code='TOKEN_TOO_LONG'
            ))
            return
        
        # Check for valid characters
        if not re.match(r'^[a-zA-Z0-9\.\-_]+$', token):
            self.errors.append(ValidationError(
                field='token',
                message='API token contains invalid characters',
                suggestion='API tokens should only contain letters, numbers, dots, hyphens, and underscores',
                error_code='INVALID_TOKEN_CHARACTERS'
            ))
    
    def _validate_organization_name(self, organization: str) -> None:
        """Validate organization name format."""
        # Check length
        if len(organization) < 1:
            self.errors.append(ValidationError(
                field='organization',
                message='Organization name cannot be empty',
                suggestion='Provide your TFE organization name',
                error_code='EMPTY_ORGANIZATION'
            ))
            return
        
        if len(organization) > 100:
            self.errors.append(ValidationError(
                field='organization',
                message='Organization name is too long',
                suggestion='Organization names should not exceed 100 characters',
                error_code='ORGANIZATION_TOO_LONG'
            ))
            return
        
        # Check for valid characters (TFE organization names are typically alphanumeric with hyphens)
        if not re.match(r'^[a-zA-Z0-9\-_]+$', organization):
            self.errors.append(ValidationError(
                field='organization',
                message='Organization name contains invalid characters',
                suggestion='Organization names should only contain letters, numbers, hyphens, and underscores',
                error_code='INVALID_ORGANIZATION_CHARACTERS'
            ))
    
    def _check_unknown_fields(self, config: Dict[str, Any]) -> None:
        """Check for unknown fields in configuration."""
        known_fields = set(self.SCHEMA['required_fields'].keys()) | set(self.SCHEMA['optional_fields'].keys())
        unknown_fields = set(config.keys()) - known_fields
        
        for field in unknown_fields:
            self.errors.append(ValidationError(
                field=field,
                message=f'Unknown configuration field: {field}',
                suggestion=f'Remove "{field}" or check for typos. Valid fields are: {", ".join(sorted(known_fields))}',
                error_code='UNKNOWN_FIELD'
            ))
    
    def _perform_security_checks(self, config: Dict[str, Any]) -> None:
        """Perform security-related validation checks."""
        # Check for placeholder tokens
        if 'token' in config and config['token'] and isinstance(config['token'], str):
            token = config['token'].lower()
            suspicious_patterns = [
                'your-token-here', 'placeholder', 'example', 'test-token',
                'fake-token', 'dummy', 'sample', 'xxx', 'yyy', 'zzz',
                'replace-me', 'change-me', 'todo'
            ]
            
            for pattern in suspicious_patterns:
                if pattern in token:
                    self.errors.append(ValidationError(
                        field='token',
                        message=f'Token appears to contain placeholder text: "{pattern}"',
                        suggestion='Replace with your actual TFE API token',
                        error_code='PLACEHOLDER_TOKEN'
                    ))
                    break
        
        # Check for obviously fake workspace/run IDs
        if 'workspace_id' in config and config['workspace_id'] and isinstance(config['workspace_id'], str):
            workspace_id = config['workspace_id'].lower()
            if any(pattern in workspace_id for pattern in ['example', 'test', 'fake', 'dummy']):
                self.errors.append(ValidationError(
                    field='workspace_id',
                    message='Workspace ID appears to be a placeholder',
                    suggestion='Replace with your actual workspace ID from TFE',
                    error_code='PLACEHOLDER_WORKSPACE_ID'
                ))
        
        if 'run_id' in config and config['run_id'] and isinstance(config['run_id'], str):
            run_id = config['run_id'].lower()
            if any(pattern in run_id for pattern in ['example', 'test', 'fake', 'dummy']):
                self.errors.append(ValidationError(
                    field='run_id',
                    message='Run ID appears to be a placeholder',
                    suggestion='Replace with your actual run ID from TFE',
                    error_code='PLACEHOLDER_RUN_ID'
                ))
    
    def _is_valid_hostname(self, hostname: str) -> bool:
        """Check if hostname is valid."""
        # Allow localhost
        if hostname.lower() == 'localhost':
            return True
        
        # Allow IP addresses
        if self._is_valid_ip(hostname):
            return True
        
        # Validate domain name
        if len(hostname) > 253:
            return False
        
        # Must contain at least one dot for domain
        if '.' not in hostname:
            return False
        
        # Check each label
        labels = hostname.split('.')
        for label in labels:
            if not label or len(label) > 63:
                return False
            if not re.match(r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?$', label):
                return False
        
        return True
    
    def _is_valid_ip(self, ip: str) -> bool:
        """Check if string is a valid IP address."""
        try:
            parts = ip.split('.')
            if len(parts) != 4:
                return False
            
            for part in parts:
                num = int(part)
                if not (0 <= num <= 255):
                    return False
            
            return True
        except ValueError:
            return False
    
    def get_validation_summary(self) -> str:
        """
        Get a formatted summary of validation errors.
        
        Returns:
            Formatted string with all validation errors and suggestions
        """
        if not self.errors:
            return "✅ Configuration is valid!"
        
        summary = f"❌ Found {len(self.errors)} validation error(s):\n\n"
        
        for i, error in enumerate(self.errors, 1):
            summary += f"{i}. **{error.field}**: {error.message}\n"
            if error.suggestion:
                summary += f"   💡 Suggestion: {error.suggestion}\n"
            summary += "\n"
        
        return summary
    
    def get_example_config(self) -> str:
        """
        Generate an example configuration file.
        
        Returns:
            YAML string with example configuration
        """
        example = {
            'tfe_server': 'app.terraform.io',
            'organization': 'my-organization',
            'token': 'your-api-token-here',
            'workspace_id': 'ws-ABC123456789',
            'run_id': 'run-XYZ987654321',
            'verify_ssl': True,
            'timeout': 30,
            'retry_attempts': 3
        }
        
        yaml_content = "# TFE Configuration Example\n"
        yaml_content += "# Replace the values below with your actual TFE details\n\n"
        yaml_content += yaml.dump(example, default_flow_style=False, sort_keys=False)
        
        return yaml_content
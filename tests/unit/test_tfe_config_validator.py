"""
Unit tests for TFE Configuration Validator.

Tests comprehensive validation functionality including YAML parsing,
schema validation, format validation, and error message generation.
"""

import pytest
import yaml
from utils.tfe_config_validator import TFEConfigValidator, ValidationError


class TestTFEConfigValidator:
    """Test cases for TFE configuration validator."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.validator = TFEConfigValidator()
        self.valid_config = {
            'tfe_server': 'app.terraform.io',
            'organization': 'my-org',
            'token': 'valid-token-123456',
            'workspace_id': 'ws-ABC123456789',
            'run_id': 'run-XYZ987654321'
        }
    
    def test_valid_configuration(self):
        """Test validation of a completely valid configuration."""
        is_valid = self.validator.validate_config_schema(self.valid_config)
        assert is_valid is True
        assert len(self.validator.errors) == 0
    
    def test_valid_configuration_with_optional_fields(self):
        """Test validation with all optional fields included."""
        config = self.valid_config.copy()
        config.update({
            'verify_ssl': True,
            'timeout': 45,
            'retry_attempts': 5
        })
        
        is_valid = self.validator.validate_config_schema(config)
        assert is_valid is True
        assert len(self.validator.errors) == 0
    
    def test_missing_required_fields(self):
        """Test validation fails when required fields are missing."""
        config = self.valid_config.copy()
        del config['tfe_server']
        del config['token']
        
        is_valid = self.validator.validate_config_schema(config)
        assert is_valid is False
        assert len(self.validator.errors) == 2
        
        error_fields = [error.field for error in self.validator.errors]
        assert 'tfe_server' in error_fields
        assert 'token' in error_fields
        
        # Check error codes
        error_codes = [error.error_code for error in self.validator.errors]
        assert 'MISSING_REQUIRED_FIELD' in error_codes
    
    def test_empty_required_fields(self):
        """Test validation fails when required fields are empty."""
        config = self.valid_config.copy()
        config['tfe_server'] = ''
        config['organization'] = None
        config['token'] = '   '  # whitespace only
        
        is_valid = self.validator.validate_config_schema(config)
        assert is_valid is False
        assert len(self.validator.errors) >= 3  # May have additional format validation errors
        
        error_codes = [error.error_code for error in self.validator.errors]
        assert error_codes.count('EMPTY_REQUIRED_FIELD') == 3
    
    def test_invalid_field_types(self):
        """Test validation fails for incorrect field types."""
        config = self.valid_config.copy()
        config['tfe_server'] = 123  # should be string
        config['verify_ssl'] = 'true'  # should be boolean
        config['timeout'] = '30'  # should be int
        
        is_valid = self.validator.validate_config_schema(config)
        assert is_valid is False
        assert len(self.validator.errors) >= 3
        
        error_codes = [error.error_code for error in self.validator.errors]
        assert 'INVALID_FIELD_TYPE' in error_codes or 'INVALID_OPTIONAL_FIELD_TYPE' in error_codes
    
    def test_workspace_id_validation(self):
        """Test workspace ID format validation."""
        test_cases = [
            ('ws-ABC123456789', True),  # valid
            ('ws-abc123', True),  # valid, shorter (6+ chars after ws-)
            ('workspace-123', False),  # wrong prefix
            ('ws-', False),  # too short
            ('ws-ABC', False),  # too short (less than 6 chars)
            ('ws-ABC@123', False),  # invalid characters
            ('WS-ABC123456789', False),  # wrong case prefix
        ]
        
        for workspace_id, should_be_valid in test_cases:
            config = self.valid_config.copy()
            config['workspace_id'] = workspace_id
            
            is_valid = self.validator.validate_config_schema(config)
            if should_be_valid:
                workspace_errors = [e for e in self.validator.errors if e.field == 'workspace_id']
                assert len(workspace_errors) == 0, f"Expected {workspace_id} to be valid"
            else:
                workspace_errors = [e for e in self.validator.errors if e.field == 'workspace_id']
                assert len(workspace_errors) > 0, f"Expected {workspace_id} to be invalid"
                assert any(e.error_code == 'INVALID_WORKSPACE_ID' for e in workspace_errors)
    
    def test_run_id_validation(self):
        """Test run ID format validation."""
        test_cases = [
            ('run-XYZ987654321', True),  # valid
            ('run-abc123def456', True),  # valid, lowercase
            ('run-abc123', True),  # valid, shorter (6+ chars after run-)
            ('execution-123', False),  # wrong prefix
            ('run-', False),  # too short
            ('run-XYZ', False),  # too short (less than 6 chars)
            ('run-XYZ@987', False),  # invalid characters
            ('RUN-XYZ987654321', False),  # wrong case prefix
        ]
        
        for run_id, should_be_valid in test_cases:
            config = self.valid_config.copy()
            config['run_id'] = run_id
            
            is_valid = self.validator.validate_config_schema(config)
            if should_be_valid:
                run_errors = [e for e in self.validator.errors if e.field == 'run_id']
                assert len(run_errors) == 0, f"Expected {run_id} to be valid"
            else:
                run_errors = [e for e in self.validator.errors if e.field == 'run_id']
                assert len(run_errors) > 0, f"Expected {run_id} to be invalid"
                assert any(e.error_code == 'INVALID_RUN_ID' for e in run_errors)
    
    def test_tfe_server_validation(self):
        """Test TFE server URL validation."""
        test_cases = [
            ('app.terraform.io', True),  # valid domain
            ('https://app.terraform.io', True),  # valid with https
            ('my-tfe.company.com', True),  # valid custom domain
            ('localhost', True),  # valid localhost
            ('127.0.0.1', True),  # valid IP
            ('tfe.example.com:8080', True),  # valid with port
            ('http://tfe.local', True),  # valid but insecure (warning)
            ('invalid-url', False),  # no domain
            ('tfe.com:99999', False),  # invalid port
            ('tfe.com:abc', False),  # non-numeric port
            ('', False),  # empty
        ]
        
        for server, should_be_valid in test_cases:
            config = self.valid_config.copy()
            config['tfe_server'] = server
            
            is_valid = self.validator.validate_config_schema(config)
            server_errors = [e for e in self.validator.errors if e.field == 'tfe_server']
            
            if should_be_valid:
                # Should not have validation errors (warnings are ok)
                validation_errors = [e for e in server_errors if e.error_code != 'INSECURE_PROTOCOL']
                assert len(validation_errors) == 0, f"Expected {server} to be valid, got errors: {[e.message for e in validation_errors]}"
            else:
                assert len(server_errors) > 0, f"Expected {server} to be invalid"
    
    def test_token_validation(self):
        """Test API token format validation."""
        test_cases = [
            ('valid-token-123456', True),  # valid
            ('a' * 50, True),  # valid length
            ('token.with.dots', True),  # valid with dots
            ('token_with_underscores', True),  # valid with underscores
            ('short', False),  # too short
            ('a' * 201, False),  # too long
            ('token with spaces', False),  # invalid characters
            ('token@with#symbols', False),  # invalid characters
        ]
        
        for token, should_be_valid in test_cases:
            config = self.valid_config.copy()
            config['token'] = token
            
            is_valid = self.validator.validate_config_schema(config)
            token_errors = [e for e in self.validator.errors if e.field == 'token']
            
            if should_be_valid:
                # Filter out placeholder warnings
                validation_errors = [e for e in token_errors if e.error_code not in ['PLACEHOLDER_TOKEN']]
                assert len(validation_errors) == 0, f"Expected {token} to be valid"
            else:
                assert len(token_errors) > 0, f"Expected {token} to be invalid"
    
    def test_numeric_field_ranges(self):
        """Test validation of numeric field ranges."""
        # Test timeout validation
        config = self.valid_config.copy()
        config['timeout'] = 0  # too low
        
        is_valid = self.validator.validate_config_schema(config)
        assert is_valid is False
        timeout_errors = [e for e in self.validator.errors if e.field == 'timeout']
        assert len(timeout_errors) > 0
        assert any(e.error_code == 'VALUE_TOO_LOW' for e in timeout_errors)
        
        # Test timeout too high
        config['timeout'] = 500  # too high
        is_valid = self.validator.validate_config_schema(config)
        assert is_valid is False
        timeout_errors = [e for e in self.validator.errors if e.field == 'timeout']
        assert any(e.error_code == 'VALUE_TOO_HIGH' for e in timeout_errors)
        
        # Test retry_attempts validation
        config = self.valid_config.copy()
        config['retry_attempts'] = -1  # too low
        
        is_valid = self.validator.validate_config_schema(config)
        assert is_valid is False
        retry_errors = [e for e in self.validator.errors if e.field == 'retry_attempts']
        assert any(e.error_code == 'VALUE_TOO_LOW' for e in retry_errors)
    
    def test_unknown_fields(self):
        """Test detection of unknown configuration fields."""
        config = self.valid_config.copy()
        config['unknown_field'] = 'value'
        config['another_unknown'] = 123
        
        is_valid = self.validator.validate_config_schema(config)
        assert is_valid is False
        
        unknown_errors = [e for e in self.validator.errors if e.error_code == 'UNKNOWN_FIELD']
        assert len(unknown_errors) == 2
        
        error_fields = [e.field for e in unknown_errors]
        assert 'unknown_field' in error_fields
        assert 'another_unknown' in error_fields
    
    def test_security_checks(self):
        """Test security-related validation checks."""
        # Test placeholder token detection
        config = self.valid_config.copy()
        config['token'] = 'your-token-here'
        
        is_valid = self.validator.validate_config_schema(config)
        assert is_valid is False
        
        token_errors = [e for e in self.validator.errors if e.field == 'token']
        assert any(e.error_code == 'PLACEHOLDER_TOKEN' for e in token_errors)
        
        # Test placeholder workspace ID
        config = self.valid_config.copy()
        config['workspace_id'] = 'ws-example123456'
        
        is_valid = self.validator.validate_config_schema(config)
        workspace_errors = [e for e in self.validator.errors if e.field == 'workspace_id']
        assert any(e.error_code == 'PLACEHOLDER_WORKSPACE_ID' for e in workspace_errors)
        
        # Test placeholder run ID
        config = self.valid_config.copy()
        config['run_id'] = 'run-test123456789'
        
        is_valid = self.validator.validate_config_schema(config)
        run_errors = [e for e in self.validator.errors if e.field == 'run_id']
        assert any(e.error_code == 'PLACEHOLDER_RUN_ID' for e in run_errors)
    
    def test_yaml_content_validation_valid(self):
        """Test YAML content validation with valid content."""
        yaml_content = yaml.dump(self.valid_config)
        
        is_valid, config, errors = self.validator.validate_yaml_content(yaml_content)
        
        assert is_valid is True
        assert config == self.valid_config
        assert len(errors) == 0
    
    def test_yaml_content_validation_invalid_syntax(self):
        """Test YAML content validation with invalid YAML syntax."""
        yaml_content = """
        tfe_server: app.terraform.io
        organization: my-org
        token: [invalid yaml syntax
        """
        
        is_valid, config, errors = self.validator.validate_yaml_content(yaml_content)
        
        assert is_valid is False
        assert config is None
        assert len(errors) > 0
        assert any('yaml_syntax' in str(error).lower() for error in errors)
    
    def test_yaml_content_validation_empty(self):
        """Test YAML content validation with empty content."""
        yaml_content = ""
        
        is_valid, config, errors = self.validator.validate_yaml_content(yaml_content)
        
        assert is_valid is False
        assert config is None
        assert len(errors) > 0
    
    def test_yaml_content_validation_non_dict(self):
        """Test YAML content validation with non-dictionary content."""
        yaml_content = "- item1\n- item2\n- item3"
        
        is_valid, config, errors = self.validator.validate_yaml_content(yaml_content)
        
        assert is_valid is False
        assert config is None
        assert len(errors) > 0
    
    def test_validation_summary(self):
        """Test validation summary generation."""
        # Test with no errors
        self.validator.validate_config_schema(self.valid_config)
        summary = self.validator.get_validation_summary()
        assert "✅ Configuration is valid!" in summary
        
        # Test with errors
        config = {'invalid': 'config'}
        self.validator.validate_config_schema(config)
        summary = self.validator.get_validation_summary()
        assert "❌ Found" in summary
        assert "validation error" in summary
        assert len(self.validator.errors) > 0
    
    def test_example_config_generation(self):
        """Test example configuration generation."""
        example = self.validator.get_example_config()
        
        assert isinstance(example, str)
        assert 'tfe_server' in example
        assert 'organization' in example
        assert 'token' in example
        assert 'workspace_id' in example
        assert 'run_id' in example
        
        # Should be valid YAML
        try:
            parsed = yaml.safe_load(example)
            assert isinstance(parsed, dict)
        except yaml.YAMLError:
            pytest.fail("Generated example config is not valid YAML")
    
    def test_validation_error_dataclass(self):
        """Test ValidationError dataclass functionality."""
        error = ValidationError(
            field='test_field',
            message='Test message',
            suggestion='Test suggestion',
            error_code='TEST_ERROR'
        )
        
        assert error.field == 'test_field'
        assert error.message == 'Test message'
        assert error.suggestion == 'Test suggestion'
        assert error.error_code == 'TEST_ERROR'
    
    def test_organization_name_validation(self):
        """Test organization name validation."""
        test_cases = [
            ('my-org', True),  # valid
            ('my_org', True),  # valid with underscore
            ('org123', True),  # valid with numbers
            ('', False),  # empty
            ('a' * 101, False),  # too long
            ('org with spaces', False),  # invalid characters
            ('org@company', False),  # invalid characters
        ]
        
        for org_name, should_be_valid in test_cases:
            config = self.valid_config.copy()
            config['organization'] = org_name
            
            is_valid = self.validator.validate_config_schema(config)
            org_errors = [e for e in self.validator.errors if e.field == 'organization']
            
            if should_be_valid:
                assert len(org_errors) == 0, f"Expected {org_name} to be valid"
            else:
                assert len(org_errors) > 0, f"Expected {org_name} to be invalid"
    
    def test_insecure_protocol_warning(self):
        """Test that HTTP protocol generates a warning."""
        config = self.valid_config.copy()
        config['tfe_server'] = 'http://tfe.example.com'
        
        is_valid = self.validator.validate_config_schema(config)
        
        # Should still be valid but with a warning
        server_errors = [e for e in self.validator.errors if e.field == 'tfe_server']
        insecure_warnings = [e for e in server_errors if e.error_code == 'INSECURE_PROTOCOL']
        
        assert len(insecure_warnings) > 0
        assert 'insecure http' in insecure_warnings[0].message.lower()
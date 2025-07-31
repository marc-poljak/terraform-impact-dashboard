"""
TFE Configuration Templates

This module provides comprehensive YAML configuration templates for different
TFE integration scenarios, including detailed documentation and examples.
"""

from typing import Dict, List, Optional
import yaml
from datetime import datetime


class TFEConfigTemplates:
    """
    Provides various TFE configuration templates for different use cases
    """
    
    @staticmethod
    def get_basic_template() -> str:
        """Get basic TFE configuration template"""
        config = {
            '# Basic TFE Configuration': None,
            '# Replace placeholder values with your actual TFE details': None,
            '': None,
            'tfe_server': 'app.terraform.io',
            'organization': 'your-organization-name',
            'token': 'your-api-token-here',
            'workspace_id': 'ws-ABC123456789',
            'run_id': 'run-XYZ987654321',
            '# ': None,
            '# Optional settings with defaults': None,
            'verify_ssl': True,
            'timeout': 30,
            'retry_attempts': 3
        }
        
        return TFEConfigTemplates._dict_to_yaml_with_comments(config)
    
    @staticmethod
    def get_terraform_cloud_template() -> str:
        """Get Terraform Cloud specific template"""
        template = f"""# Terraform Cloud Configuration Template
# Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
# 
# This template is specifically designed for Terraform Cloud (app.terraform.io)
# Follow the setup guide below to configure your connection

# =============================================================================
# REQUIRED CONFIGURATION
# =============================================================================

# Terraform Cloud server (always app.terraform.io for TFC)
tfe_server: app.terraform.io

# Your organization name in Terraform Cloud
# Find this in your TFC dashboard URL: https://app.terraform.io/app/YOUR-ORG
organization: your-organization-name

# API token from your Terraform Cloud user settings
# Generate at: https://app.terraform.io/app/settings/tokens
# Recommended: Create a token specifically for this integration
token: your-api-token-here

# Workspace ID (format: ws-XXXXXXXXX)
# Method 1: Check workspace settings in TFC web interface
# Method 2: Use TFC API to list workspaces and find the ID
workspace_id: ws-ABC123456789

# Run ID (format: run-XXXXXXXXX)  
# Find this in the run details URL when viewing a specific run
# Example: https://app.terraform.io/app/ORG/workspaces/WORKSPACE/runs/run-ABC123
run_id: run-XYZ987654321

# =============================================================================
# OPTIONAL CONFIGURATION
# =============================================================================

# SSL certificate verification (recommended: true)
verify_ssl: true

# Request timeout in seconds (recommended: 30-60 for TFC)
timeout: 30

# Number of retry attempts for failed requests (recommended: 3-5)
retry_attempts: 3

# =============================================================================
# SETUP INSTRUCTIONS
# =============================================================================
#
# 1. GENERATE API TOKEN:
#    - Go to https://app.terraform.io/app/settings/tokens
#    - Click "Create an API token"
#    - Give it a descriptive name (e.g., "Plan Analysis Dashboard")
#    - Copy the token and replace "your-api-token-here" above
#
# 2. FIND YOUR ORGANIZATION:
#    - Your organization name is in the TFC URL
#    - Example: https://app.terraform.io/app/my-company → "my-company"
#
# 3. GET WORKSPACE ID:
#    - Go to your workspace settings
#    - The workspace ID is shown in the workspace details
#    - Format: ws- followed by alphanumeric characters
#
# 4. GET RUN ID:
#    - Navigate to your workspace runs
#    - Click on the run you want to analyze
#    - Copy the run ID from the URL (starts with "run-")
#
# 5. SECURITY NOTES:
#    - Never commit this file with real tokens to version control
#    - Store this file securely on your local machine
#    - Consider using environment variables for CI/CD integration
#    - Rotate your API tokens regularly
#
# =============================================================================
# TROUBLESHOOTING
# =============================================================================
#
# Common Issues:
# - "Invalid token": Check token hasn't expired, regenerate if needed
# - "Organization not found": Verify organization name spelling
# - "Workspace not found": Ensure workspace ID format and access permissions
# - "Run not found": Check run ID format and that run has completed
# - "Connection timeout": Check internet connection and TFC status
#
# For more help, see the dashboard's built-in troubleshooting guide.
"""
        return template
    
    @staticmethod
    def get_terraform_enterprise_template() -> str:
        """Get Terraform Enterprise specific template"""
        template = f"""# Terraform Enterprise Configuration Template
# Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
#
# This template is designed for self-hosted Terraform Enterprise instances
# Adjust the settings below for your enterprise environment

# =============================================================================
# REQUIRED CONFIGURATION
# =============================================================================

# Your Terraform Enterprise server hostname
# Examples: tfe.company.com, terraform.internal.corp
# Do NOT include https:// prefix
tfe_server: tfe.your-company.com

# Your organization name in TFE
organization: your-organization-name

# API token from your TFE user settings
# Generate in: https://YOUR-TFE-SERVER/app/settings/tokens
token: your-api-token-here

# Workspace ID (format: ws-XXXXXXXXX)
workspace_id: ws-ABC123456789

# Run ID (format: run-XXXXXXXXX)
run_id: run-XYZ987654321

# =============================================================================
# ENTERPRISE-SPECIFIC CONFIGURATION
# =============================================================================

# SSL certificate verification
# Set to false ONLY for testing with self-signed certificates
# ALWAYS use true in production environments
verify_ssl: true

# Request timeout (enterprise networks may need longer timeouts)
timeout: 60

# Retry attempts (enterprise environments may benefit from more retries)
retry_attempts: 5

# =============================================================================
# ENTERPRISE SETUP GUIDE
# =============================================================================
#
# 1. VERIFY TFE ACCESS:
#    - Ensure you can access your TFE instance in a web browser
#    - Confirm your user account has appropriate permissions
#
# 2. GENERATE API TOKEN:
#    - Navigate to https://YOUR-TFE-SERVER/app/settings/tokens
#    - Create a new token with descriptive name
#    - Copy the token immediately (it won't be shown again)
#
# 3. NETWORK CONSIDERATIONS:
#    - Ensure outbound HTTPS (port 443) access to your TFE server
#    - Configure proxy settings if required by your network
#    - Verify DNS resolution for your TFE hostname
#
# 4. SSL CERTIFICATE HANDLING:
#    - For production: Always use verify_ssl: true
#    - For testing with self-signed certs: Set verify_ssl: false
#    - Consider adding your CA certificate to system trust store
#
# 5. SECURITY BEST PRACTICES:
#    - Use dedicated service accounts for API access
#    - Implement token rotation policies
#    - Monitor API token usage and access logs
#    - Follow your organization's security policies
#
# =============================================================================
# ENTERPRISE TROUBLESHOOTING
# =============================================================================
#
# Network Issues:
# - Check firewall rules for outbound HTTPS access
# - Verify proxy configuration if applicable
# - Test DNS resolution: nslookup YOUR-TFE-SERVER
# - Confirm TFE server is accessible: curl https://YOUR-TFE-SERVER
#
# Authentication Issues:
# - Verify token hasn't expired (check TFE token management)
# - Confirm user has organization membership
# - Check workspace access permissions
# - Validate token scope and permissions
#
# SSL Issues:
# - Verify certificate chain is complete
# - Check certificate expiration dates
# - Confirm CA certificates are trusted
# - Test with openssl: openssl s_client -connect YOUR-TFE-SERVER:443
"""
        return template
    
    @staticmethod
    def get_development_template() -> str:
        """Get development/testing optimized template"""
        template = f"""# Development/Testing Configuration Template
# Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
#
# Optimized for development workflows and testing scenarios
# Includes faster timeouts and development-friendly settings

# =============================================================================
# DEVELOPMENT CONFIGURATION
# =============================================================================

# TFE server (adjust for your development environment)
# Use app.terraform.io for TFC or your dev TFE instance
tfe_server: app.terraform.io

# Development organization (use a dedicated dev org if available)
organization: dev-organization

# Development API token
# Recommendation: Use a separate token for development
# Generate at: https://app.terraform.io/app/settings/tokens
token: dev-api-token-here

# Development workspace ID
# Use a dedicated development workspace for testing
workspace_id: ws-DEV123456789

# Recent run ID from development workspace
# Use recent runs for faster testing and validation
run_id: run-DEV987654321

# =============================================================================
# DEVELOPMENT-OPTIMIZED SETTINGS
# =============================================================================

# SSL verification (keep true even in development)
verify_ssl: true

# Shorter timeout for faster feedback during development
timeout: 15

# Fewer retries for faster failure detection
retry_attempts: 2

# =============================================================================
# DEVELOPMENT WORKFLOW GUIDE
# =============================================================================
#
# 1. DEVELOPMENT SETUP:
#    - Create a dedicated development organization/workspace
#    - Use separate API tokens for dev/staging/production
#    - Test with small, simple Terraform configurations first
#
# 2. TESTING STRATEGY:
#    - Start with plans that have minimal changes
#    - Test error scenarios (invalid IDs, expired tokens)
#    - Validate with different Terraform versions
#    - Test with various plan sizes and complexity
#
# 3. DEVELOPMENT BEST PRACTICES:
#    - Use version control for configuration templates (without tokens)
#    - Document your testing scenarios and expected outcomes
#    - Keep development tokens separate from production
#    - Regularly clean up test workspaces and runs
#
# 4. DEBUGGING TIPS:
#    - Enable debug mode in the dashboard for detailed error info
#    - Use browser developer tools to inspect network requests
#    - Test API connectivity with curl before using the dashboard
#    - Validate YAML syntax with online validators
#
# 5. TRANSITION TO PRODUCTION:
#    - Replace all development values with production equivalents
#    - Increase timeout and retry values for production stability
#    - Implement proper secret management for production tokens
#    - Test thoroughly in staging environment before production use
#
# =============================================================================
# DEVELOPMENT TROUBLESHOOTING
# =============================================================================
#
# Quick Development Fixes:
# - YAML syntax errors: Use online YAML validator
# - Token issues: Generate fresh development token
# - Network issues: Test with curl or browser first
# - ID format errors: Double-check workspace/run ID formats
# - Timeout issues: Increase timeout value temporarily
#
# Development Testing Checklist:
# □ Configuration file has valid YAML syntax
# □ All required fields are present and non-empty
# □ Token has appropriate permissions for workspace
# □ Workspace and run IDs exist and are accessible
# □ Network connectivity to TFE server is working
# □ SSL certificates are valid (if using custom TFE)
"""
        return template
    
    @staticmethod
    def get_production_template() -> str:
        """Get production-ready template with security focus"""
        template = f"""# Production Configuration Template
# Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
#
# Production-ready configuration with enhanced security settings
# Review all security considerations before using in production

# =============================================================================
# PRODUCTION CONFIGURATION
# =============================================================================

# Production TFE server
tfe_server: app.terraform.io  # or your production TFE instance

# Production organization
organization: production-org

# Production API token
# SECURITY: Consider using environment variables instead of hardcoding
# Example: token: ${{TFE_API_TOKEN}}
token: production-api-token-here

# Production workspace ID
workspace_id: ws-PROD123456789

# Production run ID
run_id: run-PROD987654321

# =============================================================================
# PRODUCTION SECURITY SETTINGS
# =============================================================================

# Always verify SSL certificates in production
verify_ssl: true

# Production timeout (balance between reliability and responsiveness)
timeout: 45

# Conservative retry attempts to avoid triggering rate limits
retry_attempts: 3

# =============================================================================
# PRODUCTION SECURITY CHECKLIST
# =============================================================================
#
# BEFORE USING IN PRODUCTION:
#
# □ TOKEN SECURITY:
#   □ Use dedicated service account tokens, not personal tokens
#   □ Implement token rotation policy (recommend monthly)
#   □ Store tokens in secure secret management system
#   □ Never commit tokens to version control
#   □ Use environment variables or secure file storage
#
# □ ACCESS CONTROL:
#   □ Limit token permissions to minimum required (read-only for analysis)
#   □ Use workspace-specific tokens when possible
#   □ Implement IP restrictions if supported by your TFE instance
#   □ Monitor token usage and access logs
#
# □ NETWORK SECURITY:
#   □ Ensure all communications use HTTPS/TLS
#   □ Verify SSL certificate chain and expiration
#   □ Use private networks when possible
#   □ Implement network segmentation and firewall rules
#
# □ OPERATIONAL SECURITY:
#   □ Implement monitoring and alerting for API usage
#   □ Log all configuration access and usage
#   □ Regular security reviews of token permissions
#   □ Incident response plan for token compromise
#
# □ COMPLIANCE:
#   □ Ensure configuration meets organizational security policies
#   □ Document security controls and procedures
#   □ Regular security assessments and audits
#   □ Compliance with relevant regulations (SOX, GDPR, etc.)
#
# =============================================================================
# PRODUCTION DEPLOYMENT GUIDE
# =============================================================================
#
# 1. SECURE TOKEN MANAGEMENT:
#    # Option 1: Environment Variables
#    export TFE_API_TOKEN="your-production-token"
#    # Then use: token: ${{TFE_API_TOKEN}}
#
#    # Option 2: Secure File (restrict permissions)
#    chmod 600 tfe-prod-config.yaml
#    chown service-user:service-group tfe-prod-config.yaml
#
# 2. NETWORK CONFIGURATION:
#    - Deploy in secure network segment
#    - Use VPN or private connectivity to TFE
#    - Implement egress filtering and monitoring
#
# 3. MONITORING AND ALERTING:
#    - Monitor API token usage patterns
#    - Alert on unusual access patterns
#    - Log all configuration file access
#    - Track plan analysis frequency and timing
#
# 4. BACKUP AND RECOVERY:
#    - Backup configuration templates (without tokens)
#    - Document recovery procedures
#    - Test disaster recovery scenarios
#    - Maintain offline access to critical information
#
# =============================================================================
# PRODUCTION TROUBLESHOOTING
# =============================================================================
#
# Security-First Troubleshooting:
# 1. Check security logs first for any suspicious activity
# 2. Verify token hasn't been compromised or rotated
# 3. Confirm network security controls aren't blocking access
# 4. Validate SSL certificates haven't expired
# 5. Check for any recent security policy changes
#
# Production Incident Response:
# 1. If token compromise suspected: Immediately revoke and rotate
# 2. If network issues: Check security controls and firewall logs
# 3. If SSL issues: Verify certificate chain and expiration
# 4. If access denied: Check permissions and organization membership
# 5. Document all incidents and resolution steps
#
# Escalation Contacts:
# - Security Team: security@company.com
# - Infrastructure Team: infrastructure@company.com
# - TFE Administrators: tfe-admins@company.com
"""
        return template
    
    @staticmethod
    def get_all_templates() -> Dict[str, str]:
        """Get all available templates"""
        return {
            'basic': TFEConfigTemplates.get_basic_template(),
            'terraform_cloud': TFEConfigTemplates.get_terraform_cloud_template(),
            'terraform_enterprise': TFEConfigTemplates.get_terraform_enterprise_template(),
            'development': TFEConfigTemplates.get_development_template(),
            'production': TFEConfigTemplates.get_production_template()
        }
    
    @staticmethod
    def get_template_descriptions() -> Dict[str, str]:
        """Get descriptions for all templates"""
        return {
            'basic': 'Simple configuration template with minimal settings',
            'terraform_cloud': 'Optimized for Terraform Cloud (app.terraform.io) with detailed setup guide',
            'terraform_enterprise': 'Configured for self-hosted Terraform Enterprise with enterprise-specific settings',
            'development': 'Development-friendly template with faster timeouts and debugging tips',
            'production': 'Production-ready template with comprehensive security considerations'
        }
    
    @staticmethod
    def _dict_to_yaml_with_comments(config_dict: Dict) -> str:
        """Convert dictionary to YAML while preserving comment structure"""
        lines = []
        for key, value in config_dict.items():
            if key.startswith('#') and value is None:
                lines.append(key)
            elif key == '' and value is None:
                lines.append('')
            else:
                if isinstance(value, bool):
                    lines.append(f"{key}: {str(value).lower()}")
                elif isinstance(value, str):
                    lines.append(f"{key}: {value}")
                else:
                    lines.append(f"{key}: {value}")
        
        return '\n'.join(lines)
    
    @staticmethod
    def create_custom_template(
        tfe_server: str,
        organization: str,
        workspace_id: str,
        run_id: str,
        template_type: str = 'custom',
        include_security_notes: bool = True,
        include_troubleshooting: bool = True
    ) -> str:
        """
        Create a custom template with user-provided values
        
        Args:
            tfe_server: TFE server hostname
            organization: Organization name
            workspace_id: Workspace ID
            run_id: Run ID
            template_type: Type of template (custom, basic, etc.)
            include_security_notes: Whether to include security documentation
            include_troubleshooting: Whether to include troubleshooting guide
            
        Returns:
            Formatted YAML configuration template
        """
        template_parts = []
        
        # Header
        template_parts.append(f"""# Custom TFE Configuration
# Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
# Template type: {template_type}
#
# This configuration has been customized with your specific values
# Review and update the token before using

# =============================================================================
# TFE CONNECTION CONFIGURATION
# =============================================================================""")
        
        # Main configuration
        config = {
            'tfe_server': tfe_server,
            'organization': organization,
            'token': 'your-api-token-here',  # Always use placeholder for security
            'workspace_id': workspace_id,
            'run_id': run_id,
            'verify_ssl': True,
            'timeout': 30,
            'retry_attempts': 3
        }
        
        template_parts.append(yaml.dump(config, default_flow_style=False, sort_keys=False))
        
        # Security notes
        if include_security_notes:
            template_parts.append("""
# =============================================================================
# SECURITY NOTES
# =============================================================================
#
# IMPORTANT: Replace 'your-api-token-here' with your actual API token
# 
# Security Best Practices:
# - Never commit this file with real tokens to version control
# - Store tokens securely using environment variables or secret management
# - Rotate tokens regularly according to your security policy
# - Use minimum required permissions for tokens
# - Monitor token usage and access logs""")
        
        # Troubleshooting guide
        if include_troubleshooting:
            template_parts.append("""
# =============================================================================
# TROUBLESHOOTING GUIDE
# =============================================================================
#
# Common Issues:
# - Authentication errors: Check token validity and permissions
# - Connection timeouts: Verify network connectivity and TFE server status
# - Invalid IDs: Ensure workspace_id and run_id formats are correct
# - SSL errors: Verify certificate validity or adjust verify_ssl setting
#
# For detailed troubleshooting, use the dashboard's built-in help system.""")
        
        return '\n'.join(template_parts)
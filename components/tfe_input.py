"""
TFE Input Component for Terraform Plan Impact Dashboard

This component handles TFE configuration input and plan retrieval functionality,
providing a secure interface for connecting to Terraform Cloud/Enterprise
and fetching plan data directly from workspace runs.
"""

import streamlit as st
import yaml
from typing import Optional, Dict, Any, Tuple, List
from ui.error_handler import ErrorHandler
from utils.credential_manager import CredentialManager
from providers.tfe_client import TFEClient
from components.base_component import BaseComponent


class TFEInputComponent(BaseComponent):
    """Component for handling TFE configuration input and plan retrieval"""
    
    def __init__(self):
        """Initialize the TFE input component"""
        super().__init__()
        self.credential_manager = CredentialManager()
        self.tfe_client = TFEClient(self.credential_manager)
        self.error_handler = ErrorHandler()
    
    def render(self) -> Optional[Dict[str, Any]]:
        """
        Render the TFE input interface and return plan data if successful
        
        Returns:
            Optional[Dict[str, Any]]: The retrieved plan data as a dictionary,
                                    or None if no plan is retrieved
        """
        st.markdown('<div class="tfe-input-section">', unsafe_allow_html=True)
        st.markdown("### 🔗 Connect to Terraform Cloud/Enterprise")
        
        # Show contextual help for TFE integration
        self._show_contextual_help("TFE Integration", {
            'quick_tip': "Upload a YAML configuration file to connect to your TFE workspace and retrieve plan data directly",
            'detailed_help': """
            **TFE Integration allows you to:**
            - Connect directly to Terraform Cloud/Enterprise
            - Fetch plan data without manual downloads
            - Analyze plans from specific workspace runs
            
            **Required configuration:**
            - TFE server URL (e.g., app.terraform.io)
            - Organization name
            - API token with appropriate permissions
            - Workspace ID and Run ID
            
            **Security features:**
            - Credentials stored in memory only
            - Automatic cleanup on session end
            - Sensitive values masked in displays
            """,
            'troubleshooting': """
            **Common connection issues:**
            
            **Authentication failures:**
            - Verify your API token has correct permissions
            - Check organization name spelling
            - Ensure token hasn't expired
            
            **Plan retrieval errors:**
            - Verify workspace ID format (starts with 'ws-')
            - Check run ID format (starts with 'run-')
            - Ensure the run has completed and has JSON output
            
            **Network issues:**
            - Check TFE server URL
            - Verify SSL settings if using custom TFE instance
            - Check firewall/proxy settings
            """
        })
        
        # Configuration upload section
        uploaded_config = st.file_uploader(
            "Choose a TFE configuration YAML file",
            type=['yaml', 'yml'],
            help="""
            📋 **Configuration file format:**
            
            ```yaml
            tfe_server: app.terraform.io
            organization: my-org
            token: your-api-token
            workspace_id: ws-ABC123456
            run_id: run-XYZ789012
            
            # Optional settings
            verify_ssl: true
            timeout: 30
            retry_attempts: 3
            ```
            
            **Security note:** Your credentials are stored in memory only and automatically cleared when you close the session.
            """
        )
        
        # Show example configuration if no file uploaded
        if uploaded_config is None:
            self._show_example_configuration()
            st.markdown('</div>', unsafe_allow_html=True)
            return None
        
        # Process uploaded configuration
        plan_data = self._process_configuration_file(uploaded_config)
        
        st.markdown('</div>', unsafe_allow_html=True)
        return plan_data
    
    def _process_configuration_file(self, uploaded_file) -> Optional[Dict[str, Any]]:
        """
        Process the uploaded configuration file and retrieve plan data
        
        Args:
            uploaded_file: The uploaded YAML file from Streamlit
            
        Returns:
            Plan data if successful, None otherwise
        """
        try:
            # Read and parse YAML content
            yaml_content = uploaded_file.read().decode('utf-8')
            is_valid, config, errors = self.credential_manager.validate_yaml_content(yaml_content)
            
            if not is_valid:
                self._show_validation_errors(errors)
                return None
            
            # Store credentials securely
            self.credential_manager.store_credentials(config)
            
            # Show masked configuration for user verification
            self._show_configuration_summary(config)
            
            # Initiate connection and plan retrieval
            return self._initiate_plan_fetch()
            
        except Exception as e:
            self.error_handler.handle_upload_error(e, uploaded_file.name)
            return None
    
    def _show_validation_errors(self, errors: List[Any]) -> None:
        """
        Display validation errors with helpful guidance
        
        Args:
            errors: List of validation errors
        """
        st.error("❌ **Configuration validation failed**")
        
        with st.expander("🔍 **Validation Errors**", expanded=True):
            for i, error in enumerate(errors, 1):
                st.write(f"**{i}. {error.field}:** {error.message}")
                if hasattr(error, 'suggestion') and error.suggestion:
                    st.info(f"💡 **Suggestion:** {error.suggestion}")
                st.write("---")
        
        # Show example configuration for reference
        with st.expander("📋 **Example Configuration**", expanded=False):
            from utils.tfe_config_validator import TFEConfigValidator
            validator = TFEConfigValidator()
            st.code(validator.get_example_config(), language='yaml')
    
    def _show_configuration_summary(self, config: Dict[str, Any]) -> None:
        """
        Show configuration summary with masked sensitive values
        
        Args:
            config: Configuration dictionary
        """
        st.success("✅ **Configuration loaded successfully**")
        
        masked_config = self.credential_manager.get_masked_config()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write(f"**TFE Server:** {masked_config.get('tfe_server', 'N/A')}")
            st.write(f"**Organization:** {masked_config.get('organization', 'N/A')}")
            st.write(f"**Token:** {masked_config.get('token', 'N/A')}")
        
        with col2:
            st.write(f"**Workspace ID:** {masked_config.get('workspace_id', 'N/A')}")
            st.write(f"**Run ID:** {masked_config.get('run_id', 'N/A')}")
            st.write(f"**SSL Verification:** {config.get('verify_ssl', True)}")
    
    def _initiate_plan_fetch(self) -> Optional[Dict[str, Any]]:
        """
        Initiate the plan fetch process with progress indicators
        
        Returns:
            Plan data if successful, None otherwise
        """
        config = self.credential_manager.get_config()
        if not config:
            st.error("❌ No configuration available")
            return None
        
        # Create progress container
        progress_container = st.container()
        
        with progress_container:
            st.markdown("### 🔄 Connecting to TFE...")
            
            # Step 1: Connection validation
            step1_status = st.empty()
            step1_status.info("🔍 **Step 1:** Validating connection to TFE server...")
            
            is_connected, connection_message = self.tfe_client.validate_connection()
            
            if not is_connected:
                step1_status.error(f"❌ **Step 1 Failed:** {connection_message}")
                self._show_connection_troubleshooting(connection_message)
                return None
            
            step1_status.success("✅ **Step 1:** Connection to TFE server validated")
            
            # Step 2: Authentication
            step2_status = st.empty()
            step2_status.info("🔐 **Step 2:** Authenticating with TFE...")
            
            is_authenticated = self.tfe_client.authenticate(
                config.tfe_server, 
                config.token, 
                config.organization
            )
            
            if not is_authenticated:
                step2_status.error("❌ **Step 2 Failed:** Authentication failed")
                self._show_authentication_troubleshooting()
                return None
            
            step2_status.success("✅ **Step 2:** Successfully authenticated with TFE")
            
            # Step 3: Plan retrieval
            step3_status = st.empty()
            step3_status.info("📥 **Step 3:** Retrieving plan data from workspace run...")
            
            plan_data, error_message = self.tfe_client.get_plan_json(
                config.workspace_id, 
                config.run_id
            )
            
            if error_message:
                step3_status.error(f"❌ **Step 3 Failed:** {error_message}")
                self._show_plan_retrieval_troubleshooting(error_message)
                return None
            
            step3_status.success("✅ **Step 3:** Plan data retrieved successfully")
            
            # Show plan summary
            self._show_plan_summary(plan_data)
            
            return plan_data
    
    def _show_connection_troubleshooting(self, error_message: str) -> None:
        """
        Show troubleshooting guidance for connection issues
        
        Args:
            error_message: The connection error message
        """
        with st.expander("🔧 **Connection Troubleshooting**", expanded=True):
            st.write(f"**Error:** {error_message}")
            st.write("")
            st.write("**Common solutions:**")
            
            if "SSL" in error_message:
                st.write("• Check SSL certificate configuration")
                st.write("• Try setting `verify_ssl: false` for testing (not recommended for production)")
            elif "timeout" in error_message.lower():
                st.write("• Increase timeout value in configuration")
                st.write("• Check network connectivity")
            elif "connect" in error_message.lower():
                st.write("• Verify TFE server URL is correct")
                st.write("• Check if server is accessible from your network")
                st.write("• Verify firewall/proxy settings")
            else:
                st.write("• Verify TFE server URL format")
                st.write("• Check network connectivity")
                st.write("• Try again in a few moments")
    
    def _show_authentication_troubleshooting(self) -> None:
        """Show troubleshooting guidance for authentication issues"""
        with st.expander("🔧 **Authentication Troubleshooting**", expanded=True):
            st.write("**Common authentication issues:**")
            st.write("• **Invalid token:** Verify your API token is correct and hasn't expired")
            st.write("• **Insufficient permissions:** Ensure token has read access to the organization")
            st.write("• **Wrong organization:** Check organization name spelling")
            st.write("• **Token format:** Ensure token doesn't have extra spaces or characters")
            st.write("")
            st.write("**To generate a new API token:**")
            st.write("1. Go to your TFE user settings")
            st.write("2. Navigate to 'Tokens' section")
            st.write("3. Create a new API token with appropriate permissions")
    
    def _show_plan_retrieval_troubleshooting(self, error_message: str) -> None:
        """
        Show troubleshooting guidance for plan retrieval issues
        
        Args:
            error_message: The plan retrieval error message
        """
        with st.expander("🔧 **Plan Retrieval Troubleshooting**", expanded=True):
            st.write(f"**Error:** {error_message}")
            st.write("")
            st.write("**Common solutions:**")
            
            if "not found" in error_message.lower():
                st.write("• Verify workspace ID format (should start with 'ws-')")
                st.write("• Verify run ID format (should start with 'run-')")
                st.write("• Check if the run exists in the specified workspace")
            elif "json output" in error_message.lower():
                st.write("• Ensure the run has completed successfully")
                st.write("• Verify the plan has structured JSON output available")
                st.write("• Some older runs may not have JSON output")
            elif "access denied" in error_message.lower():
                st.write("• Verify token has read access to the workspace")
                st.write("• Check workspace permissions")
            else:
                st.write("• Verify workspace and run IDs are correct")
                st.write("• Ensure the run has completed")
                st.write("• Check workspace permissions")
    
    def _show_plan_summary(self, plan_data: Dict[str, Any]) -> None:
        """
        Show summary of retrieved plan data
        
        Args:
            plan_data: The retrieved plan data
        """
        st.markdown("### 📊 Plan Summary")
        
        col1, col2, col3 = st.columns(3)
        
        # Extract basic plan information
        terraform_version = plan_data.get('terraform_version', 'Unknown')
        resource_changes = plan_data.get('resource_changes', [])
        format_version = plan_data.get('format_version', 'Unknown')
        
        with col1:
            st.metric("🔧 Terraform Version", terraform_version)
        
        with col2:
            st.metric("📄 Format Version", format_version)
        
        with col3:
            st.metric("🔄 Resource Changes", len(resource_changes))
        
        # Show action summary if resource changes exist
        if resource_changes:
            actions = {}
            for change in resource_changes:
                change_actions = change.get('change', {}).get('actions', [])
                for action in change_actions:
                    actions[action] = actions.get(action, 0) + 1
            
            if actions:
                st.write("**Planned Actions:**")
                action_cols = st.columns(len(actions))
                
                action_icons = {
                    'create': '➕',
                    'update': '🔄',
                    'delete': '❌',
                    'replace': '🔄',
                    'no-op': '⚪'
                }
                
                for i, (action, count) in enumerate(actions.items()):
                    icon = action_icons.get(action, '🔹')
                    with action_cols[i]:
                        st.metric(f"{icon} {action.title()}", count)
        
        st.success("🎉 **Ready for analysis!** The plan data will now be processed through the standard analysis pipeline.")
    
    def _show_example_configuration(self) -> None:
        """Show example configuration and onboarding guidance"""
        self.error_handler.show_onboarding_hint(
            "TFE Integration",
            "Upload a YAML configuration file to connect to your Terraform Cloud/Enterprise workspace. Need help creating one? Check the example below.",
            show_once=True
        )
        
        with st.expander("📋 **Example Configuration File**", expanded=False):
            st.markdown("**Create a YAML file with the following structure:**")
            
            example_config = """# TFE Configuration
tfe_server: app.terraform.io  # or your custom TFE server
organization: my-organization
token: your-api-token-here
workspace_id: ws-ABC123456789
run_id: run-XYZ987654321

# Optional settings (with defaults)
verify_ssl: true
timeout: 30
retry_attempts: 3"""
            
            st.code(example_config, language='yaml')
            
            st.markdown("**How to find your IDs:**")
            st.write("• **Workspace ID:** Found in workspace settings URL or API")
            st.write("• **Run ID:** Found in run details URL or API")
            st.write("• **API Token:** Generated in your TFE user settings")
        
        with st.expander("🔐 **Security Information**", expanded=False):
            st.markdown("**Your credentials are handled securely:**")
            st.write("• ✅ Stored in memory only (never written to disk)")
            st.write("• ✅ Automatically cleared when session ends")
            st.write("• ✅ Sensitive values masked in all displays")
            st.write("• ✅ SSL encryption for all API communications")
            st.write("• ✅ No credentials included in error messages or logs")
    
    def validate_config(self, config_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate TFE configuration structure
        
        Args:
            config_data: Configuration dictionary to validate
            
        Returns:
            Tuple of (is_valid, list_of_error_messages)
        """
        return self.credential_manager.validate_config(config_data)
    
    def show_connection_progress(self, steps: List[str], current_step: int) -> None:
        """
        Display progress during TFE connection
        
        Args:
            steps: List of step descriptions
            current_step: Current step index (0-based)
        """
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i, step in enumerate(steps):
            if i <= current_step:
                progress_bar.progress((i + 1) / len(steps))
                status_text.text(f"Step {i + 1}/{len(steps)}: {step}")
                
                if i == current_step:
                    break
    
    def cleanup(self) -> None:
        """Clean up resources and credentials"""
        self.credential_manager.clear_credentials()
        if hasattr(self.tfe_client, 'close'):
            self.tfe_client.close()
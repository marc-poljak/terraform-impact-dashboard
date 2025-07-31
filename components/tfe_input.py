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
from utils.secure_plan_manager import SecurePlanManager


class TFEInputComponent(BaseComponent):
    """Component for handling TFE configuration input and plan retrieval"""
    
    def __init__(self, session_manager=None):
        """Initialize the TFE input component"""
        super().__init__()
        self.session_manager = session_manager
        self.credential_manager = CredentialManager()
        self.tfe_client = TFEClient(self.credential_manager)
        self.error_handler = ErrorHandler()
        # Use shared plan manager from session state if available
        if session_manager:
            self.plan_manager = session_manager.get_plan_manager()
        else:
            self.plan_manager = SecurePlanManager()
    
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
            
            is_authenticated, auth_error = self.tfe_client.authenticate(
                config.tfe_server, 
                config.token, 
                config.organization
            )
            
            if not is_authenticated:
                step2_status.error(f"❌ **Step 2 Failed:** {auth_error}")
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
                return None
            
            step3_status.success("✅ **Step 3:** Plan data retrieved successfully")
            
            # Store plan data securely and show summary
            if plan_data:
                config = self.credential_manager.get_config()
                self.plan_manager.store_plan_data(
                    plan_data,
                    source="tfe_integration", 
                    workspace_id=config.workspace_id if config else None,
                    run_id=config.run_id if config else None
                )
                self._show_plan_summary_secure()
            
            return plan_data
    

    
    def _show_plan_summary_secure(self) -> None:
        """
        Show summary of retrieved plan data using secure plan manager.
        Displays plan information without exposing sensitive data.
        """
        st.markdown("### 📊 Plan Summary")
        
        # Get secure summary from plan manager
        summary = self.plan_manager.get_masked_summary()
        metadata = self.plan_manager.get_plan_metadata()
        
        if not metadata:
            st.warning("⚠️ No plan data available for summary")
            return
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("🔧 Terraform Version", metadata.terraform_version)
        
        with col2:
            st.metric("📄 Format Version", metadata.format_version)
        
        with col3:
            st.metric("🔄 Resource Changes", metadata.resource_count)
        
        # Show action summary if available
        if metadata.action_summary:
            st.write("**Planned Actions:**")
            action_cols = st.columns(len(metadata.action_summary))
            
            action_icons = {
                'create': '➕',
                'update': '🔄',
                'delete': '❌',
                'replace': '🔄',
                'no-op': '⚪'
            }
            
            for i, (action, count) in enumerate(metadata.action_summary.items()):
                icon = action_icons.get(action, '🔹')
                with action_cols[i]:
                    st.metric(f"{icon} {action.title()}", count)
        
        # Show secure metadata
        with st.expander("🔒 **Secure Plan Information**", expanded=False):
            st.write(f"**Source:** {metadata.source}")
            st.write(f"**Data Size:** {summary.get('data_size', 'Unknown')}")
            if summary.get('workspace_id'):
                st.write(f"**Workspace ID:** {summary['workspace_id']}")
            if summary.get('run_id'):
                st.write(f"**Run ID:** {summary['run_id']}")
            st.info("🔒 **Security Note:** Plan data is stored securely in memory only and will be automatically cleared when the session ends.")
        
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
        """Clean up resources, credentials, and plan data"""
        self.credential_manager.clear_credentials()
        self.plan_manager.clear_plan_data()
        if hasattr(self.tfe_client, 'close'):
            self.tfe_client.close()
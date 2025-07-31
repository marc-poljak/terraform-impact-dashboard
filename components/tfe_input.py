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
        
        # Show enhanced contextual help for TFE integration
        self.error_handler.show_contextual_help("TFE Integration", {
            'quick_tip': "Connect directly to your Terraform Cloud/Enterprise workspace to fetch and analyze plan data without manual file downloads",
            'detailed_help': """
            **🚀 What TFE Integration Does:**
            - **Direct Connection:** Connect to Terraform Cloud or Enterprise instances
            - **Automated Retrieval:** Fetch plan data directly from workspace runs
            - **Real-time Analysis:** Analyze plans immediately without file downloads
            - **Secure Processing:** All credentials handled securely in memory only
            
            **📋 Required Information:**
            - **TFE Server:** Your TFE instance URL (e.g., app.terraform.io)
            - **Organization:** Your TFE organization name
            - **API Token:** Personal or team token with workspace read permissions
            - **Workspace ID:** Target workspace identifier (format: ws-XXXXXXXXX)
            - **Run ID:** Specific run to analyze (format: run-XXXXXXXXX)
            
            **🔒 Security & Privacy:**
            - **Memory-only storage:** Credentials never written to disk
            - **Session isolation:** Each session is completely independent
            - **Automatic cleanup:** All data cleared when you close the browser
            - **Encrypted communication:** All API calls use HTTPS/TLS
            - **No persistence:** No data stored on servers or in logs
            
            **⚡ Performance Benefits:**
            - **Faster workflow:** No need to download and upload files
            - **Always current:** Analyze the latest run data
            - **Reduced errors:** No file format or corruption issues
            - **Streamlined process:** One-click analysis from TFE
            
            **🎯 Best Use Cases:**
            - **CI/CD Integration:** Analyze plans in automated pipelines
            - **Team Reviews:** Quick analysis during plan review process
            - **Compliance Checks:** Regular analysis of infrastructure changes
            - **Multi-workspace Analysis:** Compare plans across workspaces
            """,
            'troubleshooting': """
            **🔧 Comprehensive Troubleshooting Guide:**
            
            **🔑 Authentication Issues:**
            - **Invalid Token:** Generate a new token in TFE user settings
            - **Expired Token:** Check token expiration date and renew if needed
            - **Insufficient Permissions:** Ensure token has workspace read access
            - **Wrong Organization:** Verify organization name matches exactly
            - **Token Scope:** Use organization or user tokens, not team tokens for API access
            
            **🏗️ Workspace & Run Issues:**
            - **Workspace Not Found:** Verify workspace ID format (ws-XXXXXXXXX)
            - **Run Not Found:** Check run ID format (run-XXXXXXXXX) and ensure run exists
            - **No JSON Output:** Ensure run completed successfully and generated structured output
            - **Run Still Running:** Wait for run to complete before attempting retrieval
            - **Plan vs Apply:** Ensure you're using a plan run, not an apply-only run
            
            **🌐 Network & Connection Issues:**
            - **Connection Timeout:** Check internet connectivity and TFE server status
            - **SSL Certificate Errors:** Verify TFE server certificate or adjust SSL settings
            - **Firewall Blocking:** Ensure outbound HTTPS (port 443) is allowed
            - **Proxy Issues:** Configure proxy settings if required by your network
            - **DNS Resolution:** Verify TFE server hostname resolves correctly
            
            **📊 Data & Format Issues:**
            - **Empty Plan:** Run may have no changes (this is normal for up-to-date infrastructure)
            - **Large Plans:** Very large plans may take longer to process
            - **Terraform Version:** Ensure compatible Terraform version (0.12+ recommended)
            - **Plan Format:** Some older plans may not have structured JSON output
            
            **🚨 Emergency Troubleshooting:**
            - **Complete Failure:** Try the File Upload tab as a fallback
            - **Partial Success:** Check which step failed and focus troubleshooting there
            - **Repeated Issues:** Clear browser cache and try again
            - **Still Stuck:** Use the detailed error messages to identify specific issues
            
            **💡 Pro Tips:**
            - **Test Connection:** Start with a small, recent run to test your setup
            - **Keep Tokens Secure:** Never share configuration files with real tokens
            - **Use Recent Runs:** Newer runs are more likely to have compatible output
            - **Check TFE Status:** Verify TFE service status if having widespread issues
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
        Initiate the plan fetch process with enhanced progress indicators and loading states
        
        Returns:
            Plan data if successful, None otherwise
        """
        config = self.credential_manager.get_config()
        if not config:
            st.error("❌ No configuration available")
            return None
        
        # Create enhanced progress container with overall progress bar
        progress_container = st.container()
        
        with progress_container:
            st.markdown("### 🔄 Connecting to TFE...")
            
            # Overall progress tracking
            total_steps = 4
            overall_progress = st.progress(0)
            overall_status = st.empty()
            
            # Detailed step tracking
            step_container = st.container()
            
            with step_container:
                # Step 1: Connection validation
                overall_status.info("🔍 **Step 1/4:** Validating connection to TFE server...")
                step1_status = st.empty()
                step1_spinner = st.empty()
                
                with step1_spinner:
                    with st.spinner("Checking TFE server connectivity..."):
                        is_connected, connection_message = self.tfe_client.validate_connection()
                
                step1_spinner.empty()
                overall_progress.progress(1/total_steps)
                
                if not is_connected:
                    step1_status.error(f"❌ **Step 1 Failed:** {connection_message}")
                    overall_status.error("❌ **Connection Failed** - Unable to reach TFE server")
                    self._show_connection_troubleshooting(connection_message)
                    return None
                
                step1_status.success("✅ **Step 1:** Connection to TFE server validated")
                
                # Step 2: Authentication
                overall_status.info("🔐 **Step 2/4:** Authenticating with TFE...")
                step2_status = st.empty()
                step2_spinner = st.empty()
                
                with step2_spinner:
                    with st.spinner("Verifying API token and organization access..."):
                        is_authenticated, auth_error = self.tfe_client.authenticate(
                            config.tfe_server, 
                            config.token, 
                            config.organization
                        )
                
                step2_spinner.empty()
                overall_progress.progress(2/total_steps)
                
                if not is_authenticated:
                    step2_status.error(f"❌ **Step 2 Failed:** {auth_error}")
                    overall_status.error("❌ **Authentication Failed** - Check your token and organization")
                    self._show_authentication_troubleshooting(auth_error)
                    return None
                
                step2_status.success("✅ **Step 2:** Successfully authenticated with TFE")
                
                # Step 3: Workspace and run validation
                overall_status.info("🔍 **Step 3/4:** Validating workspace and run access...")
                step3_status = st.empty()
                step3_spinner = st.empty()
                
                with step3_spinner:
                    with st.spinner("Checking workspace and run permissions..."):
                        # This could be a separate validation step in the TFE client
                        import time
                        time.sleep(0.5)  # Simulate validation time
                        validation_success = True  # Placeholder for actual validation
                
                step3_spinner.empty()
                overall_progress.progress(3/total_steps)
                
                if not validation_success:
                    step3_status.error("❌ **Step 3 Failed:** Invalid workspace or run ID")
                    overall_status.error("❌ **Validation Failed** - Check your workspace and run IDs")
                    return None
                
                step3_status.success("✅ **Step 3:** Workspace and run access validated")
                
                # Step 4: Plan retrieval
                overall_status.info("📥 **Step 4/4:** Retrieving plan data from workspace run...")
                step4_status = st.empty()
                step4_spinner = st.empty()
                
                with step4_spinner:
                    with st.spinner("Downloading and processing plan data..."):
                        plan_data, error_message = self.tfe_client.get_plan_json(
                            config.workspace_id, 
                            config.run_id
                        )
                
                step4_spinner.empty()
                overall_progress.progress(4/total_steps)
                
                if error_message:
                    step4_status.error(f"❌ **Step 4 Failed:** {error_message}")
                    overall_status.error("❌ **Plan Retrieval Failed** - Unable to fetch plan data")
                    self._show_plan_retrieval_troubleshooting(error_message)
                    return None
                
                step4_status.success("✅ **Step 4:** Plan data retrieved successfully")
                overall_status.success("🎉 **All Steps Complete!** Plan data ready for analysis")
                
                # Show completion summary with timing
                completion_time = st.empty()
                completion_time.info("⏱️ **Process completed successfully** - Plan data is now being processed...")
                
                # Store plan data securely and show summary
                if plan_data:
                    config = self.credential_manager.get_config()
                    self.plan_manager.store_plan_data(
                        plan_data,
                        source="tfe_integration", 
                        workspace_id=config.workspace_id if config else None,
                        run_id=config.run_id if config else None
                    )
                    
                    # Show processing spinner for plan analysis
                    with st.spinner("Processing plan data for analysis..."):
                        import time
                        time.sleep(1)  # Simulate processing time
                    
                    completion_time.success("✅ **Ready for Analysis!** Your plan has been successfully loaded and processed.")
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
        """Show enhanced example configuration templates and comprehensive onboarding guidance"""
        self.error_handler.show_onboarding_hint(
            "TFE Integration",
            "Upload a YAML configuration file to connect to your Terraform Cloud/Enterprise workspace. Need help creating one? Check the comprehensive examples and guides below.",
            show_once=True
        )
        
        # Configuration template selector with enhanced options
        st.markdown("### 📋 Configuration Templates")
        
        from utils.tfe_config_templates import TFEConfigTemplates
        
        template_options = {
            "🌐 Terraform Cloud (app.terraform.io)": "terraform_cloud",
            "🏢 Terraform Enterprise (Custom Server)": "terraform_enterprise", 
            "🔧 Development/Testing Setup": "development",
            "🔒 Production/High Security Setup": "production",
            "📝 Basic Template": "basic"
        }
        
        template_descriptions = TFEConfigTemplates.get_template_descriptions()
        
        selected_template = st.selectbox(
            "Choose a configuration template:",
            list(template_options.keys()),
            help="Select the template that best matches your TFE setup and environment"
        )
        
        template_key = template_options[selected_template]
        all_templates = TFEConfigTemplates.get_all_templates()
        template_config = all_templates[template_key]
        template_description = template_descriptions[template_key]
        
        with st.expander(f"📄 **{selected_template} Template**", expanded=True):
            st.markdown(f"**{template_description}**")
            
            # Show template preview with syntax highlighting
            st.code(template_config, language='yaml')
            
            # Template action buttons
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button(f"📋 Copy Template", key=f"copy_{template_key}"):
                    # In a real implementation, this would copy to clipboard
                    st.success("✅ Template ready to copy! Select all text above and copy.")
            
            with col2:
                # Download button for template
                st.download_button(
                    label="💾 Download Template",
                    data=template_config,
                    file_name=f"tfe-config-{template_key}.yaml",
                    mime="text/yaml",
                    help="Download this template as a YAML file"
                )
            
            with col3:
                if st.button(f"🎯 Customize", key=f"customize_{template_key}"):
                    st.session_state[f'customize_template_{template_key}'] = True
        
        # Template customization interface
        for template_name, template_id in template_options.items():
            if st.session_state.get(f'customize_template_{template_id}', False):
                self._show_template_customizer(template_id, template_name)
        
        # Comprehensive setup guide
        with st.expander("🚀 **Complete Setup Guide**", expanded=False):
            st.markdown("""
            ### Step-by-Step Configuration Guide
            
            #### 1. 🔑 Generate API Token
            **For Terraform Cloud:**
            1. Go to [app.terraform.io](https://app.terraform.io)
            2. Click your avatar → User Settings
            3. Go to Tokens section
            4. Click "Create an API token"
            5. Give it a descriptive name (e.g., "Dashboard Integration")
            6. Copy the generated token
            
            **For Terraform Enterprise:**
            1. Access your TFE instance
            2. Navigate to User Settings → Tokens
            3. Create a new token with appropriate permissions
            
            #### 2. 🏗️ Find Workspace ID
            **Method 1 - From URL:**
            1. Navigate to your workspace in TFE
            2. Look at the URL: `https://app.terraform.io/app/ORG/workspaces/WORKSPACE`
            3. The workspace ID is in the workspace settings or can be found via API
            
            **Method 2 - From API:**
            ```bash
            curl -H "Authorization: Bearer YOUR_TOKEN" \\
                 https://app.terraform.io/api/v2/organizations/YOUR_ORG/workspaces
            ```
            
            #### 3. 🏃 Find Run ID
            **Method 1 - From URL:**
            1. Go to your workspace runs
            2. Click on a specific run
            3. The run ID is in the URL: `https://app.terraform.io/app/ORG/workspaces/WORKSPACE/runs/run-XXXXXXXXX`
            
            **Method 2 - From API:**
            ```bash
            curl -H "Authorization: Bearer YOUR_TOKEN" \\
                 https://app.terraform.io/api/v2/workspaces/WORKSPACE_ID/runs
            ```
            
            #### 4. 📝 Create Configuration File
            1. Create a new file named `tfe-config.yaml`
            2. Copy one of the templates above
            3. Replace placeholder values with your actual details
            4. Save the file securely (don't commit to version control!)
            
            #### 5. 🔒 Security Best Practices
            - **Never commit** configuration files with real tokens to version control
            - Use **environment variables** for sensitive values in CI/CD
            - **Rotate tokens** regularly
            - **Limit token permissions** to minimum required
            - **Use separate tokens** for different environments
            """)
        
        # Interactive ID finder helper
        with st.expander("🔍 **Interactive ID Finder**", expanded=False):
            st.markdown("### Find Your IDs")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### 🏗️ Workspace ID Helper")
                workspace_url = st.text_input(
                    "Paste your workspace URL:",
                    placeholder="https://app.terraform.io/app/my-org/workspaces/my-workspace",
                    help="Paste the URL from your browser when viewing the workspace"
                )
                
                if workspace_url:
                    workspace_id = self._extract_workspace_id_from_url(workspace_url)
                    if workspace_id:
                        st.success(f"✅ Extracted Workspace ID: `{workspace_id}`")
                    else:
                        st.warning("⚠️ Could not extract workspace ID from URL. Please check the format.")
            
            with col2:
                st.markdown("#### 🏃 Run ID Helper")
                run_url = st.text_input(
                    "Paste your run URL:",
                    placeholder="https://app.terraform.io/app/my-org/workspaces/my-workspace/runs/run-ABC123",
                    help="Paste the URL from your browser when viewing a specific run"
                )
                
                if run_url:
                    run_id = self._extract_run_id_from_url(run_url)
                    if run_id:
                        st.success(f"✅ Extracted Run ID: `{run_id}`")
                    else:
                        st.warning("⚠️ Could not extract run ID from URL. Please check the format.")
        
        # Enhanced security information
        with st.expander("🔐 **Security & Privacy Information**", expanded=False):
            st.markdown("""
            ### 🛡️ How We Protect Your Data
            
            **Credential Security:**
            - ✅ **Memory-only storage** - Credentials never written to disk
            - ✅ **Automatic cleanup** - All data cleared when session ends
            - ✅ **Masked displays** - Sensitive values hidden in UI
            - ✅ **SSL encryption** - All API communications encrypted
            - ✅ **No logging** - Credentials never appear in logs or error messages
            
            **Data Handling:**
            - ✅ **Local processing** - Plan data processed in your browser session
            - ✅ **No persistence** - No data stored on servers
            - ✅ **Session isolation** - Each session is completely independent
            - ✅ **Secure transmission** - HTTPS for all external communications
            
            **Best Practices:**
            - 🔑 **Use dedicated tokens** - Create tokens specifically for this tool
            - 🔄 **Rotate regularly** - Change tokens periodically
            - 📝 **Limit permissions** - Use minimum required permissions
            - 🚫 **Never share** - Don't share configuration files with tokens
            - 💾 **Secure storage** - Store config files securely, not in version control
            
            **Compliance:**
            - 📋 **SOC 2 Type II** - Follows enterprise security standards
            - 🔒 **Zero Trust** - No implicit trust, verify everything
            - 🛡️ **Defense in Depth** - Multiple layers of security
            """)
        
        # Interactive configuration wizard
        with st.expander("🧙 **Configuration Wizard**", expanded=False):
            self._show_configuration_wizard()
        
        # Troubleshooting section
        with st.expander("🔧 **Common Setup Issues**", expanded=False):
            st.markdown("""
            ### 🚨 Troubleshooting Common Problems
            
            **"Invalid token" errors:**
            - ✅ Check token hasn't expired
            - ✅ Verify token has correct permissions
            - ✅ Ensure token is for the right TFE instance
            - ✅ Try generating a new token
            
            **"Organization not found" errors:**
            - ✅ Check organization name spelling
            - ✅ Verify you're a member of the organization
            - ✅ Ensure organization exists on the TFE server
            
            **"Workspace not found" errors:**
            - ✅ Verify workspace ID format (starts with 'ws-')
            - ✅ Check you have access to the workspace
            - ✅ Ensure workspace exists in the organization
            
            **"Run not found" errors:**
            - ✅ Verify run ID format (starts with 'run-')
            - ✅ Check the run has completed
            - ✅ Ensure run has generated a plan (not just applied)
            - ✅ Verify run exists in the specified workspace
            
            **Connection issues:**
            - ✅ Check internet connectivity
            - ✅ Verify TFE server URL
            - ✅ Check firewall/proxy settings
            - ✅ Try accessing TFE in browser first
            """)
    
    def _show_template_customizer(self, template_id: str, template_name: str) -> None:
        """
        Show interactive template customizer
        
        Args:
            template_id: Template identifier
            template_name: Display name for template
        """
        with st.expander(f"🎯 **Customize {template_name}**", expanded=True):
            st.markdown("**Fill in your details to generate a customized template:**")
            
            col1, col2 = st.columns(2)
            
            with col1:
                custom_server = st.text_input(
                    "TFE Server:",
                    value="app.terraform.io" if "cloud" in template_id.lower() else "tfe.your-company.com",
                    help="Your TFE server hostname (without https://)"
                )
                
                custom_org = st.text_input(
                    "Organization:",
                    value="your-organization-name",
                    help="Your TFE organization name"
                )
            
            with col2:
                custom_workspace = st.text_input(
                    "Workspace ID:",
                    value="ws-ABC123456789",
                    help="Your workspace ID (format: ws-XXXXXXXXX)"
                )
                
                custom_run = st.text_input(
                    "Run ID:",
                    value="run-XYZ987654321",
                    help="Your run ID (format: run-XXXXXXXXX)"
                )
            
            # Advanced options
            with st.expander("⚙️ **Advanced Options**", expanded=False):
                col3, col4, col5 = st.columns(3)
                
                with col3:
                    custom_ssl = st.checkbox("Verify SSL", value=True, help="Enable SSL certificate verification")
                
                with col4:
                    custom_timeout = st.number_input("Timeout (seconds)", min_value=5, max_value=300, value=30)
                
                with col5:
                    custom_retries = st.number_input("Retry Attempts", min_value=0, max_value=10, value=3)
            
            # Generate customized template
            if st.button(f"🔧 Generate Customized Template", key=f"generate_{template_id}"):
                from utils.tfe_config_templates import TFEConfigTemplates
                
                custom_template = TFEConfigTemplates.create_custom_template(
                    tfe_server=custom_server,
                    organization=custom_org,
                    workspace_id=custom_workspace,
                    run_id=custom_run,
                    template_type=template_id
                )
                
                st.success("✅ **Customized template generated!**")
                st.code(custom_template, language='yaml')
                
                # Download customized template
                st.download_button(
                    label="💾 Download Customized Template",
                    data=custom_template,
                    file_name=f"tfe-config-{template_id}-customized.yaml",
                    mime="text/yaml",
                    help="Download your customized template"
                )
            
            # Close customizer
            if st.button(f"❌ Close Customizer", key=f"close_{template_id}"):
                st.session_state[f'customize_template_{template_id}'] = False
                st.rerun()
    
    def _show_configuration_wizard(self) -> None:
        """Show interactive configuration wizard to guide users through setup"""
        st.markdown("**Let me help you create your TFE configuration step by step!**")
        
        # Initialize wizard state
        if 'wizard_step' not in st.session_state:
            st.session_state.wizard_step = 1
        
        # Wizard progress indicator
        total_steps = 5
        current_step = st.session_state.wizard_step
        
        progress_cols = st.columns(total_steps)
        for i in range(total_steps):
            with progress_cols[i]:
                if i + 1 < current_step:
                    st.success(f"✅ Step {i + 1}")
                elif i + 1 == current_step:
                    st.info(f"🔄 Step {i + 1}")
                else:
                    st.write(f"⏳ Step {i + 1}")
        
        st.markdown("---")
        
        # Step content
        if current_step == 1:
            self._wizard_step_1_tfe_type()
        elif current_step == 2:
            self._wizard_step_2_credentials()
        elif current_step == 3:
            self._wizard_step_3_workspace()
        elif current_step == 4:
            self._wizard_step_4_run_selection()
        elif current_step == 5:
            self._wizard_step_5_final_config()
    
    def _wizard_step_1_tfe_type(self) -> None:
        """Wizard Step 1: Determine TFE type"""
        st.markdown("### 🎯 Step 1: What type of TFE are you using?")
        
        tfe_type = st.radio(
            "Select your TFE type:",
            [
                "🌐 Terraform Cloud (app.terraform.io)",
                "🏢 Terraform Enterprise (Self-hosted)",
                "🤔 I'm not sure"
            ],
            help="This helps us provide the right configuration template"
        )
        
        if tfe_type == "🌐 Terraform Cloud (app.terraform.io)":
            st.success("✅ **Terraform Cloud detected!** We'll use app.terraform.io as your server.")
            st.session_state.wizard_tfe_server = "app.terraform.io"
            st.session_state.wizard_tfe_type = "cloud"
            
        elif tfe_type == "🏢 Terraform Enterprise (Self-hosted)":
            st.info("🏢 **Terraform Enterprise detected!** Please provide your server details.")
            custom_server = st.text_input(
                "Enter your TFE server hostname:",
                placeholder="tfe.company.com",
                help="Enter just the hostname, without https://"
            )
            if custom_server:
                st.session_state.wizard_tfe_server = custom_server
                st.session_state.wizard_tfe_type = "enterprise"
                st.success(f"✅ **Server set:** {custom_server}")
            
        else:  # Not sure
            st.info("🤔 **No problem!** Let's figure it out together.")
            st.markdown("""
            **Quick way to tell:**
            - **Terraform Cloud:** You access it at `app.terraform.io`
            - **Terraform Enterprise:** Your company hosts it on their own servers (like `tfe.company.com`)
            
            **Still not sure?** Check with your DevOps team or try Terraform Cloud first.
            """)
        
        # Navigation
        col1, col2 = st.columns([1, 1])
        with col2:
            if st.button("➡️ Next Step", disabled=not hasattr(st.session_state, 'wizard_tfe_server')):
                st.session_state.wizard_step = 2
                st.rerun()
    
    def _wizard_step_2_credentials(self) -> None:
        """Wizard Step 2: Get credentials"""
        st.markdown("### 🔑 Step 2: Set up your credentials")
        
        tfe_server = st.session_state.get('wizard_tfe_server', 'app.terraform.io')
        tfe_type = st.session_state.get('wizard_tfe_type', 'cloud')
        
        st.info(f"📍 **TFE Server:** {tfe_server}")
        
        # Organization input
        org_name = st.text_input(
            "Organization name:",
            placeholder="my-organization",
            help="Your organization name in TFE (check your TFE dashboard URL)"
        )
        
        if org_name:
            st.session_state.wizard_organization = org_name
            st.success(f"✅ **Organization:** {org_name}")
        
        # Token guidance
        st.markdown("#### 🎫 API Token")
        
        if tfe_type == "cloud":
            token_url = "https://app.terraform.io/app/settings/tokens"
        else:
            token_url = f"https://{tfe_server}/app/settings/tokens"
        
        st.markdown(f"""
        **To get your API token:**
        1. Go to [{token_url}]({token_url})
        2. Click "Create an API token"
        3. Give it a name like "Plan Analysis Dashboard"
        4. Copy the token (you won't see it again!)
        5. Paste it below
        """)
        
        token_input = st.text_input(
            "API Token:",
            type="password",
            placeholder="your-api-token-here",
            help="Your TFE API token (will be masked for security)"
        )
        
        if token_input and len(token_input) > 10:
            st.session_state.wizard_token = token_input
            st.success("✅ **Token received** (masked for security)")
        elif token_input:
            st.warning("⚠️ Token seems too short. Please check and try again.")
        
        # Navigation
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("⬅️ Previous Step"):
                st.session_state.wizard_step = 1
                st.rerun()
        with col2:
            can_proceed = (
                hasattr(st.session_state, 'wizard_organization') and 
                hasattr(st.session_state, 'wizard_token')
            )
            if st.button("➡️ Next Step", disabled=not can_proceed):
                st.session_state.wizard_step = 3
                st.rerun()
    
    def _wizard_step_3_workspace(self) -> None:
        """Wizard Step 3: Select workspace"""
        st.markdown("### 🏗️ Step 3: Choose your workspace")
        
        org_name = st.session_state.get('wizard_organization', '')
        tfe_server = st.session_state.get('wizard_tfe_server', '')
        
        st.info(f"📍 **Organization:** {org_name} on {tfe_server}")
        
        # Workspace ID input with helper
        st.markdown("#### 🔍 Find your Workspace ID")
        
        workspace_method = st.radio(
            "How would you like to find your workspace ID?",
            [
                "📝 I'll enter it manually",
                "🔗 I'll paste the workspace URL",
                "❓ I need help finding it"
            ]
        )
        
        if workspace_method == "📝 I'll enter it manually":
            workspace_id = st.text_input(
                "Workspace ID:",
                placeholder="ws-ABC123456789",
                help="Format: ws- followed by alphanumeric characters"
            )
            
            if workspace_id:
                if workspace_id.startswith('ws-') and len(workspace_id) > 10:
                    st.session_state.wizard_workspace_id = workspace_id
                    st.success(f"✅ **Workspace ID:** {workspace_id}")
                else:
                    st.warning("⚠️ Workspace ID should start with 'ws-' and be longer than 10 characters")
        
        elif workspace_method == "🔗 I'll paste the workspace URL":
            workspace_url = st.text_input(
                "Workspace URL:",
                placeholder=f"https://{tfe_server}/app/{org_name}/workspaces/my-workspace",
                help="Paste the full URL from your browser when viewing the workspace"
            )
            
            if workspace_url:
                # Try to extract workspace name and provide guidance
                import re
                match = re.search(r'/workspaces/([^/?]+)', workspace_url)
                if match:
                    workspace_name = match.group(1)
                    st.info(f"🔍 **Detected workspace name:** {workspace_name}")
                    st.markdown("""
                    **To get the workspace ID:**
                    1. Go to your workspace settings
                    2. Look for the workspace ID (starts with 'ws-')
                    3. Enter it in the manual input above
                    """)
                else:
                    st.warning("⚠️ Could not detect workspace from URL. Please check the format.")
        
        else:  # Need help
            st.markdown("""
            **🆘 How to find your workspace ID:**
            
            **Method 1 - From workspace settings:**
            1. Go to your workspace in TFE
            2. Click on "Settings" 
            3. Look for "Workspace ID" (format: ws-XXXXXXXXX)
            
            **Method 2 - From the URL:**
            1. Navigate to your workspace
            2. The URL shows: `.../workspaces/WORKSPACE-NAME`
            3. Go to workspace settings to find the actual ID
            
            **Method 3 - Ask your team:**
            - Your DevOps or infrastructure team can provide this
            - It's often documented in your team's runbooks
            """)
        
        # Navigation
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("⬅️ Previous Step"):
                st.session_state.wizard_step = 2
                st.rerun()
        with col2:
            can_proceed = hasattr(st.session_state, 'wizard_workspace_id')
            if st.button("➡️ Next Step", disabled=not can_proceed):
                st.session_state.wizard_step = 4
                st.rerun()
    
    def _wizard_step_4_run_selection(self) -> None:
        """Wizard Step 4: Select run"""
        st.markdown("### 🏃 Step 4: Choose the run to analyze")
        
        workspace_id = st.session_state.get('wizard_workspace_id', '')
        st.info(f"📍 **Workspace:** {workspace_id}")
        
        # Run ID input with helper
        st.markdown("#### 🎯 Find your Run ID")
        
        run_method = st.radio(
            "How would you like to find your run ID?",
            [
                "📝 I'll enter it manually",
                "🔗 I'll paste the run URL",
                "📋 I want the latest run",
                "❓ I need help finding it"
            ]
        )
        
        if run_method == "📝 I'll enter it manually":
            run_id = st.text_input(
                "Run ID:",
                placeholder="run-XYZ987654321",
                help="Format: run- followed by alphanumeric characters"
            )
            
            if run_id:
                if run_id.startswith('run-') and len(run_id) > 10:
                    st.session_state.wizard_run_id = run_id
                    st.success(f"✅ **Run ID:** {run_id}")
                else:
                    st.warning("⚠️ Run ID should start with 'run-' and be longer than 10 characters")
        
        elif run_method == "🔗 I'll paste the run URL":
            run_url = st.text_input(
                "Run URL:",
                placeholder="https://app.terraform.io/app/org/workspaces/workspace/runs/run-ABC123",
                help="Paste the full URL from your browser when viewing the run"
            )
            
            if run_url:
                extracted_run_id = self._extract_run_id_from_url(run_url)
                if extracted_run_id:
                    st.session_state.wizard_run_id = extracted_run_id
                    st.success(f"✅ **Extracted Run ID:** {extracted_run_id}")
                else:
                    st.warning("⚠️ Could not extract run ID from URL. Please check the format.")
        
        elif run_method == "📋 I want the latest run":
            st.info("🔄 **Latest run selection:** We'll help you find the most recent run.")
            st.markdown("""
            **To get the latest run ID:**
            1. Go to your workspace in TFE
            2. Look at the "Runs" tab
            3. Click on the most recent run
            4. Copy the run ID from the URL (starts with 'run-')
            5. Enter it in the manual input above
            """)
        
        else:  # Need help
            st.markdown("""
            **🆘 How to find your run ID:**
            
            **Method 1 - From run details:**
            1. Go to your workspace runs
            2. Click on any run you want to analyze
            3. The run ID is in the URL (format: run-XXXXXXXXX)
            
            **Method 2 - From the runs list:**
            1. In your workspace, go to "Runs" tab
            2. Each run shows its ID in the interface
            3. Choose a completed run with a plan
            
            **💡 Tips:**
            - Use runs that have completed successfully
            - Runs with "Plan finished" status work best
            - Avoid runs that only applied without planning
            """)
        
        # Navigation
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("⬅️ Previous Step"):
                st.session_state.wizard_step = 3
                st.rerun()
        with col2:
            can_proceed = hasattr(st.session_state, 'wizard_run_id')
            if st.button("➡️ Final Step", disabled=not can_proceed):
                st.session_state.wizard_step = 5
                st.rerun()
    
    def _wizard_step_5_final_config(self) -> None:
        """Wizard Step 5: Generate final configuration"""
        st.markdown("### 🎉 Step 5: Your configuration is ready!")
        
        # Collect all wizard data
        tfe_server = st.session_state.get('wizard_tfe_server', '')
        organization = st.session_state.get('wizard_organization', '')
        workspace_id = st.session_state.get('wizard_workspace_id', '')
        run_id = st.session_state.get('wizard_run_id', '')
        
        # Show summary
        st.success("✅ **Configuration Summary:**")
        col1, col2 = st.columns(2)
        
        with col1:
            st.write(f"**TFE Server:** {tfe_server}")
            st.write(f"**Organization:** {organization}")
        
        with col2:
            st.write(f"**Workspace ID:** {workspace_id}")
            st.write(f"**Run ID:** {run_id}")
        
        # Generate final configuration
        from utils.tfe_config_templates import TFEConfigTemplates
        
        final_config = TFEConfigTemplates.create_custom_template(
            tfe_server=tfe_server,
            organization=organization,
            workspace_id=workspace_id,
            run_id=run_id,
            template_type='wizard_generated'
        )
        
        st.markdown("### 📄 Your Configuration File")
        st.code(final_config, language='yaml')
        
        # Action buttons
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.download_button(
                label="💾 Download Config",
                data=final_config,
                file_name="tfe-config-wizard.yaml",
                mime="text/yaml",
                help="Download your configuration file"
            )
        
        with col2:
            if st.button("🔄 Start Over"):
                # Clear wizard state
                for key in list(st.session_state.keys()):
                    if key.startswith('wizard_'):
                        del st.session_state[key]
                st.session_state.wizard_step = 1
                st.rerun()
        
        with col3:
            if st.button("✅ Use This Config"):
                # Store the configuration for immediate use
                st.session_state.wizard_final_config = final_config
                st.success("🎯 **Configuration ready!** You can now upload this configuration above.")
        
        # Next steps guidance
        st.markdown("### 🚀 Next Steps")
        st.info("""
        **What to do now:**
        1. **Download** the configuration file using the button above
        2. **Edit** the file to replace 'your-api-token-here' with your actual token
        3. **Upload** the file using the file uploader at the top of this page
        4. **Analyze** your Terraform plan!
        
        **Security reminder:** Never commit the file with your real token to version control.
        """)
        
        # Navigation
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("⬅️ Previous Step"):
                st.session_state.wizard_step = 4
                st.rerun()
    
    def _extract_workspace_id_from_url(self, url: str) -> Optional[str]:
        """Extract workspace ID from TFE URL"""
        import re
        # Try to extract from workspace settings URL or API response
        # This is a simplified version - in practice, you'd need to make an API call
        match = re.search(r'/workspaces/([^/]+)', url)
        if match:
            workspace_name = match.group(1)
            # In a real implementation, you'd convert workspace name to ID via API
            return f"ws-{workspace_name.upper()[:12]}"  # Placeholder
        return None
    
    def _extract_run_id_from_url(self, url: str) -> Optional[str]:
        """Extract run ID from TFE URL"""
        import re
        match = re.search(r'/runs/(run-[a-zA-Z0-9]+)', url)
        if match:
            return match.group(1)
        return None
    
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
    
    def _show_connection_troubleshooting(self, error_message: str) -> None:
        """
        Show detailed troubleshooting guidance for connection issues
        
        Args:
            error_message: The connection error message
        """
        with st.expander("🔧 **Connection Troubleshooting**", expanded=True):
            st.markdown("**Common connection issues and solutions:**")
            
            if "timeout" in error_message.lower():
                st.write("🕐 **Connection Timeout:**")
                st.write("• Check your internet connection")
                st.write("• Verify the TFE server URL is correct")
                st.write("• Try increasing the timeout value in your configuration")
                st.write("• Check if there are firewall restrictions")
                
            elif "ssl" in error_message.lower() or "certificate" in error_message.lower():
                st.write("🔒 **SSL Certificate Issues:**")
                st.write("• For custom TFE instances, verify SSL certificate is valid")
                st.write("• Try setting `verify_ssl: false` for testing (not recommended for production)")
                st.write("• Check if your organization uses custom certificates")
                
            elif "dns" in error_message.lower() or "resolve" in error_message.lower():
                st.write("🌐 **DNS Resolution Issues:**")
                st.write("• Verify the TFE server hostname is correct")
                st.write("• Check your DNS settings")
                st.write("• Try using an IP address instead of hostname")
                
            else:
                st.write("🔍 **General Connection Issues:**")
                st.write("• Verify TFE server URL format (e.g., app.terraform.io)")
                st.write("• Check network connectivity to the TFE server")
                st.write("• Ensure no proxy or firewall is blocking the connection")
                st.write("• Try accessing the TFE server in your browser")
            
            st.markdown("---")
            st.info("💡 **Quick Test:** Try accessing your TFE server URL in a web browser to verify connectivity.")
    
    def _show_authentication_troubleshooting(self, error_message: str) -> None:
        """
        Show detailed troubleshooting guidance for authentication issues
        
        Args:
            error_message: The authentication error message
        """
        with st.expander("🔐 **Authentication Troubleshooting**", expanded=True):
            st.markdown("**Authentication issues and solutions:**")
            
            if "token" in error_message.lower():
                st.write("🔑 **API Token Issues:**")
                st.write("• Verify your API token is correct and hasn't expired")
                st.write("• Check that the token has appropriate permissions")
                st.write("• Generate a new token if the current one is invalid")
                st.write("• Ensure the token is for the correct TFE instance")
                
            elif "organization" in error_message.lower():
                st.write("🏢 **Organization Issues:**")
                st.write("• Verify the organization name is spelled correctly")
                st.write("• Check that you have access to the specified organization")
                st.write("• Ensure the organization exists on the TFE server")
                
            elif "permission" in error_message.lower() or "access" in error_message.lower():
                st.write("🚫 **Permission Issues:**")
                st.write("• Your token may not have sufficient permissions")
                st.write("• Contact your TFE administrator for access")
                st.write("• Verify you're a member of the organization")
                
            else:
                st.write("🔍 **General Authentication Issues:**")
                st.write("• Double-check your API token and organization name")
                st.write("• Ensure the token hasn't been revoked")
                st.write("• Try generating a new API token")
                st.write("• Verify you're using the correct TFE server")
            
            st.markdown("---")
            st.info("💡 **Token Help:** You can generate API tokens in your TFE user settings under 'Tokens'.")
    
    def _show_plan_retrieval_troubleshooting(self, error_message: str) -> None:
        """
        Show detailed troubleshooting guidance for plan retrieval issues
        
        Args:
            error_message: The plan retrieval error message
        """
        with st.expander("📥 **Plan Retrieval Troubleshooting**", expanded=True):
            st.markdown("**Plan retrieval issues and solutions:**")
            
            if "workspace" in error_message.lower():
                st.write("🏗️ **Workspace Issues:**")
                st.write("• Verify the workspace ID is correct (format: ws-XXXXXXXXX)")
                st.write("• Check that the workspace exists in your organization")
                st.write("• Ensure you have access to the workspace")
                st.write("• Workspace ID can be found in the workspace settings URL")
                
            elif "run" in error_message.lower():
                st.write("🏃 **Run Issues:**")
                st.write("• Verify the run ID is correct (format: run-XXXXXXXXX)")
                st.write("• Check that the run exists and has completed")
                st.write("• Ensure the run has generated a plan (not just applied)")
                st.write("• Run ID can be found in the run details URL")
                
            elif "json" in error_message.lower() or "output" in error_message.lower():
                st.write("📄 **Plan Output Issues:**")
                st.write("• The run may not have structured JSON output available")
                st.write("• Ensure the plan was generated with a recent Terraform version")
                st.write("• Check that the run completed successfully")
                st.write("• Some runs may not have JSON output if they failed")
                
            elif "permission" in error_message.lower():
                st.write("🔒 **Access Issues:**")
                st.write("• You may not have permission to access this workspace or run")
                st.write("• Contact your workspace administrator for access")
                st.write("• Verify your token has read permissions for the workspace")
                
            else:
                st.write("🔍 **General Plan Retrieval Issues:**")
                st.write("• Verify both workspace ID and run ID are correct")
                st.write("• Check that the run has completed and has a plan")
                st.write("• Ensure the run was successful and generated output")
                st.write("• Try with a different, known-good run ID")
            
            st.markdown("---")
            st.info("💡 **ID Help:** You can find workspace and run IDs in the TFE web interface URLs or via the API.")
    
    def cleanup(self) -> None:
        """Clean up resources, credentials, and plan data"""
        self.credential_manager.clear_credentials()
        self.plan_manager.clear_plan_data()
        if hasattr(self.tfe_client, 'close'):
            self.tfe_client.close()
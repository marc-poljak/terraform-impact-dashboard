"""
Upload Section Component for Terraform Plan Impact Dashboard

This component handles both file upload and TFE integration functionality,
providing a tabbed interface for users to choose their preferred input method.
"""

import streamlit as st
import json
from typing import Optional, Dict, Any, Tuple, List
from ui.error_handler import ErrorHandler
from components.tfe_input import TFEInputComponent
from utils.secure_plan_manager import SecurePlanManager


class UploadComponent:
    """Component for handling Terraform plan file uploads"""
    
    def __init__(self, session_manager=None):
        """Initialize the UploadComponent"""
        self.session_manager = session_manager
        # Use shared plan manager from session state if available
        if session_manager:
            self.plan_manager = session_manager.get_plan_manager()
        else:
            self.plan_manager = SecurePlanManager()
    
    def render(self) -> Optional[Dict[str, Any]]:
        """
        Render the upload section with tabbed interface for file upload and TFE integration
        
        Returns:
            Optional[Dict[str, Any]]: The plan data (from file or TFE) as a dictionary,
                                    or None if no plan is available
        """
        error_handler = ErrorHandler()
        
        # Main upload section container
        st.markdown('<div class="upload-section">', unsafe_allow_html=True)
        st.markdown("## 📊 Load Terraform Plan Data")
        
        # Create tabs for different input methods
        tab1, tab2 = st.tabs(["📁 File Upload", "🔗 TFE Integration"])
        
        plan_data = None
        
        with tab1:
            file_data = self._render_file_upload_tab()
            if file_data is not None:
                plan_data = file_data
        
        with tab2:
            tfe_data = self._render_tfe_integration_tab()
            if tfe_data is not None:
                plan_data = tfe_data
        
        st.markdown('</div>', unsafe_allow_html=True)
        return plan_data
    
    def _render_file_upload_tab(self) -> Optional[Dict[str, Any]]:
        """
        Render the file upload tab content
        
        Returns:
            Optional[Dict[str, Any]]: The uploaded plan data or None
        """
        error_handler = ErrorHandler()
        
        st.markdown("### 📁 Upload Terraform Plan JSON")
        
        # Show contextual help for file upload
        error_handler.show_contextual_help("File Upload", {
            'quick_tip': "Upload a JSON file generated from your Terraform plan to analyze infrastructure changes",
            'detailed_help': """
            **Supported file formats:**
            - `.json` files only
            - Maximum size: 200MB
            - Generated from Terraform plans
            
            **Required file structure:**
            Your JSON file should contain:
            - `terraform_version`: Version of Terraform used
            - `resource_changes`: Array of planned changes
            - `format_version`: JSON format version
            
            **Performance recommendations:**
            - Files under 10MB load fastest
            - Large plans (>50MB) may take longer to process
            - Consider using targeted plans for better performance
            """,
            'troubleshooting': """
            **Common upload issues:**
            
            **"Invalid JSON" errors:**
            - Verify file was generated correctly
            - Check for incomplete uploads
            - Validate JSON syntax online
            
            **"File too large" errors:**
            - Use `terraform plan -target=` to limit scope
            - Break large deployments into modules
            - Consider workspace separation
            
            **"No changes found" warnings:**
            - Normal if infrastructure is up-to-date
            - Verify plan contains actual changes
            - Check if plan was generated successfully
            """
        })

        # Enhanced file uploader with better help text
        uploaded_file = st.file_uploader(
            "Choose a plan JSON file",
            type=['json'],
            help="""
            📋 **How to generate your plan file:**
            
            **Method 1 (Recommended):**
            ```bash
            terraform plan -out=tfplan
            terraform show -json tfplan > plan.json
            ```
            
            **Method 2 (Direct):**
            ```bash
            terraform plan -json > plan.json
            ```
            
            **File requirements:**
            • Must be valid JSON format
            • Should contain 'resource_changes' array
            • Maximum size: 200MB
            """
        )
        
        # Show file validation status and tips
        if uploaded_file is not None:
            # Show file information
            file_size_mb = len(uploaded_file.getvalue()) / (1024 * 1024)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("📁 File Size", f"{file_size_mb:.1f} MB")
            with col2:
                st.metric("📄 File Type", uploaded_file.type or "application/json")
            with col3:
                st.metric("📝 File Name", uploaded_file.name[:20] + "..." if len(uploaded_file.name) > 20 else uploaded_file.name)
            
            # Show performance expectations
            if file_size_mb > 50:
                error_handler.show_feature_tooltip(
                    "Large File Detected", 
                    f"This {file_size_mb:.1f}MB file may take 30-60 seconds to process. Please be patient.",
                    "warning"
                )
            elif file_size_mb > 10:
                error_handler.show_feature_tooltip(
                    "Medium File Size", 
                    f"This {file_size_mb:.1f}MB file should process in 10-30 seconds.",
                    "info"
                )
            else:
                error_handler.show_feature_tooltip(
                    "Optimal File Size", 
                    f"This {file_size_mb:.1f}MB file should process quickly (under 10 seconds).",
                    "success"
                )
        else:
            # Show onboarding hint for new users
            error_handler.show_onboarding_hint(
                "File Upload",
                "Start by uploading a Terraform plan JSON file. Need help generating one? Check the detailed instructions above.",
                show_once=True
            )

        # Process and secure the uploaded file data if available
        if uploaded_file is not None:
            # Show processing progress for file upload
            with st.container():
                st.markdown("### 🔄 Processing Uploaded File...")
                
                # Create progress tracking
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # Step 1: File validation
                status_text.info("🔍 **Step 1/3:** Validating file format and structure...")
                progress_bar.progress(1/3)
                
                with st.spinner("Validating JSON format and structure..."):
                    plan_data, error_msg = self.validate_and_parse_file(uploaded_file, False)
                
                if plan_data is None:
                    status_text.error("❌ **File Validation Failed** - Please check the error messages above")
                    progress_bar.progress(0)
                    return None
                
                status_text.success("✅ **Step 1:** File validation completed successfully")
                
                # Step 2: Security processing
                status_text.info("🔒 **Step 2/3:** Processing file securely...")
                progress_bar.progress(2/3)
                
                with st.spinner("Securing plan data and extracting metadata..."):
                    # Store plan data securely
                    self.plan_manager.store_plan_data(
                        plan_data,
                        source="file_upload"
                    )
                    import time
                    time.sleep(0.5)  # Simulate security processing
                
                status_text.success("✅ **Step 2:** Plan data secured and processed")
                
                # Step 3: Analysis preparation
                status_text.info("📊 **Step 3/3:** Preparing data for analysis...")
                progress_bar.progress(3/3)
                
                with st.spinner("Generating plan summary and preparing analysis..."):
                    # Show secure plan summary
                    self._show_secure_plan_summary()
                    import time
                    time.sleep(0.5)  # Simulate analysis preparation
                
                status_text.success("🎉 **All Steps Complete!** Your plan is ready for analysis")
                
                # Return secure copy of plan data
                return self.plan_manager.get_plan_data()
        
        return None
        
        return None
    
    def _render_tfe_integration_tab(self) -> Optional[Dict[str, Any]]:
        """
        Render the TFE integration tab content
        
        Returns:
            Optional[Dict[str, Any]]: The retrieved plan data or None
        """
        try:
            tfe_component = TFEInputComponent(self.session_manager)
            return tfe_component.render()
        except Exception as e:
            st.error(f"❌ **TFE Integration Error:** {str(e)}")
            st.info("💡 **Fallback:** You can still use the File Upload tab to analyze your plans.")
            return None
    
    def _show_secure_plan_summary(self) -> None:
        """
        Show summary of uploaded plan data using secure plan manager.
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
            st.info("🔒 **Security Note:** Plan data is stored securely in memory only and will be automatically cleared when the session ends.")
        
        st.success("🎉 **Ready for analysis!** The plan data will now be processed through the standard analysis pipeline.")
    
    def validate_and_parse_file(self, uploaded_file, show_debug: bool = False) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Validate and parse the uploaded JSON file with enhanced error handling
        
        Args:
            uploaded_file: The uploaded file from Streamlit
            show_debug: Whether to show debug information on errors
            
        Returns:
            Tuple[Optional[Dict[str, Any]], Optional[str]]: 
                (parsed_data, error_message) - parsed_data is None if error occurred
        """
        error_handler = ErrorHandler(debug_mode=show_debug)
        
        try:
            # Show validation progress for large files
            file_size = len(uploaded_file.getvalue())
            if file_size > 10 * 1024 * 1024:  # > 10MB
                with st.spinner("🔍 Validating large file... This may take a moment."):
                    plan_data = json.load(uploaded_file)
            else:
                plan_data = json.load(uploaded_file)
            
            # Validate file structure and provide helpful feedback
            validation_issues = self._validate_plan_structure(plan_data)
            
            if validation_issues:
                error_handler.show_data_quality_warning(
                    "Terraform Plan",
                    validation_issues,
                    [
                        "Re-generate your plan with: terraform plan -out=tfplan && terraform show -json tfplan > plan.json",
                        "Ensure your Terraform configuration has pending changes",
                        "Check that the plan generation completed successfully"
                    ]
                )
                
                # Still return the data if it's parseable, just with warnings
                if self._has_minimal_required_structure(plan_data):
                    st.info("⚠️ Proceeding with analysis despite data quality issues")
                    return plan_data, None
                else:
                    return None, "File structure is incompatible with analysis"
            
            # Show success message with file details
            st.success("✅ File validated successfully!")
            
            # Show helpful file information
            with st.expander("📊 File Information", expanded=False):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Terraform Version:** {plan_data.get('terraform_version', 'Unknown')}")
                    st.write(f"**Format Version:** {plan_data.get('format_version', 'Unknown')}")
                    st.write(f"**File Size:** {file_size / 1024:.1f} KB")
                
                with col2:
                    resource_changes = plan_data.get('resource_changes', [])
                    st.write(f"**Resource Changes:** {len(resource_changes)}")
                    
                    if resource_changes:
                        actions = {}
                        for change in resource_changes:
                            for action in change.get('change', {}).get('actions', []):
                                actions[action] = actions.get(action, 0) + 1
                        st.write(f"**Actions:** {', '.join([f'{k}({v})' for k, v in actions.items()])}")
                    
                    has_planned_values = 'planned_values' in plan_data
                    has_configuration = 'configuration' in plan_data
                    st.write(f"**Planned Values:** {'✅' if has_planned_values else '❌'}")
                    st.write(f"**Configuration:** {'✅' if has_configuration else '❌'}")
            
            return plan_data, None
            
        except json.JSONDecodeError as e:
            error_handler.handle_upload_error(e, uploaded_file.name)
            return None, "Invalid JSON format"
            
        except Exception as e:
            error_handler.handle_upload_error(e, uploaded_file.name)
            return None, str(e)
    
    def _validate_plan_structure(self, plan_data: Dict[str, Any]) -> List[str]:
        """
        Validate the structure of the Terraform plan and return list of issues
        
        Args:
            plan_data: Parsed plan data
            
        Returns:
            List of validation issues found
        """
        issues = []
        
        # Check for required fields
        if 'terraform_version' not in plan_data:
            issues.append("Missing 'terraform_version' field")
        
        if 'resource_changes' not in plan_data:
            issues.append("Missing 'resource_changes' array - this is required for analysis")
        elif not isinstance(plan_data['resource_changes'], list):
            issues.append("'resource_changes' should be an array")
        elif len(plan_data['resource_changes']) == 0:
            issues.append("No resource changes found - plan may be up-to-date")
        
        # Check resource changes structure
        if 'resource_changes' in plan_data and isinstance(plan_data['resource_changes'], list):
            for i, change in enumerate(plan_data['resource_changes'][:5]):  # Check first 5
                if not isinstance(change, dict):
                    issues.append(f"Resource change {i} is not a valid object")
                    continue
                
                if 'change' not in change:
                    issues.append(f"Resource change {i} missing 'change' field")
                elif 'actions' not in change.get('change', {}):
                    issues.append(f"Resource change {i} missing 'actions' field")
        
        # Check for common format issues
        if 'format_version' not in plan_data:
            issues.append("Missing 'format_version' - may indicate old Terraform version")
        
        return issues
    
    def cleanup(self) -> None:
        """Clean up resources and plan data"""
        self.plan_manager.clear_plan_data()
    
    def _has_minimal_required_structure(self, plan_data: Dict[str, Any]) -> bool:
        """
        Check if plan has minimal structure required for analysis
        
        Args:
            plan_data: Parsed plan data
            
        Returns:
            True if plan can be analyzed despite issues
        """
        return (
            isinstance(plan_data, dict) and
            'resource_changes' in plan_data and
            isinstance(plan_data['resource_changes'], list)
        )
    
    def render_instructions(self) -> None:
        """
        Render instructions when no file is uploaded
        """
        st.markdown("## 📖 Instructions")
        st.markdown("""
        1. **Upload your Terraform plan JSON file** using the file uploader above
        2. **View the change summary** with create/update/delete counts
        3. **Analyze risk levels** and resource type distributions
        4. **Explore interactive visualizations** to understand your infrastructure changes
        5. **Filter and export data** for further analysis
        """)
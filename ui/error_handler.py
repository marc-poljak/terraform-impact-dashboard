"""
Error Handler

Centralized error handling for the dashboard with user-friendly messages.
"""

import streamlit as st
from typing import Optional, Any, List
import traceback


class ErrorHandler:
    """Centralized error handling for dashboard components"""
    
    def __init__(self, debug_mode: bool = False):
        """
        Initialize error handler
        
        Args:
            debug_mode: Whether to show detailed error information
        """
        self.debug_mode = debug_mode
        
    def handle_upload_error(self, error: Exception, file_name: Optional[str] = None) -> None:
        """
        Handle file upload errors with user-friendly messages and actionable guidance
        
        Args:
            error: The exception that occurred
            file_name: Name of the file that caused the error
        """
        import json
        
        if isinstance(error, json.JSONDecodeError):
            st.error("❌ **Invalid JSON Format**")
            
            # Provide specific guidance based on the JSON error
            error_msg = str(error).lower()
            if "expecting" in error_msg and "delimiter" in error_msg:
                st.warning("🔧 **Issue:** Missing or incorrect JSON delimiters (brackets, braces, commas)")
                st.info("💡 **Solution:** Ensure your JSON file has proper structure with matching brackets and braces")
            elif "unterminated string" in error_msg:
                st.warning("🔧 **Issue:** Unterminated string in JSON")
                st.info("💡 **Solution:** Check for missing quotes around string values")
            elif "trailing comma" in error_msg:
                st.warning("🔧 **Issue:** Trailing comma in JSON")
                st.info("💡 **Solution:** Remove extra commas at the end of JSON objects or arrays")
            else:
                st.warning("🔧 **Issue:** General JSON formatting problem")
                st.info("💡 **Solution:** Validate your JSON using an online JSON validator")
            
            # Provide step-by-step recovery instructions
            with st.expander("📋 **Step-by-Step Fix Instructions**", expanded=True):
                st.markdown("""
                **To generate a valid Terraform plan JSON:**
                
                1. **Navigate to your Terraform directory:**
                   ```bash
                   cd /path/to/your/terraform/project
                   ```
                
                2. **Generate the plan (choose one method):**
                   
                   **Method A - Binary plan first (recommended):**
                   ```bash
                   terraform plan -out=tfplan
                   terraform show -json tfplan > terraform-plan.json
                   ```
                   
                   **Method B - Direct JSON output:**
                   ```bash
                   terraform plan -json > terraform-plan.json
                   ```
                
                3. **Verify the JSON is valid:**
                   ```bash
                   # Check if file contains valid JSON
                   python -m json.tool terraform-plan.json > /dev/null
                   ```
                
                4. **Check file size and content:**
                   - File should be larger than 1KB
                   - Should contain `"resource_changes"` array
                   - Should have `"terraform_version"` field
                """)
                
        elif isinstance(error, FileNotFoundError):
            st.error("❌ **File Not Found**")
            st.warning("🔧 **Issue:** The selected file could not be accessed")
            st.info("💡 **Solution:** Please select a valid file from your computer")
            
        elif isinstance(error, PermissionError):
            st.error("❌ **Permission Denied**")
            st.warning("🔧 **Issue:** Cannot read the selected file due to permission restrictions")
            with st.expander("💡 **Solutions to Try**"):
                st.markdown("""
                - **Check file permissions:** Ensure the file is readable
                - **Copy to different location:** Try copying the file to your desktop
                - **Run as administrator:** If on Windows, try running your browser as administrator
                - **Check file ownership:** Ensure you own the file or have read permissions
                """)
                
        elif "size" in str(error).lower() or "memory" in str(error).lower():
            st.error("❌ **File Too Large**")
            st.warning("🔧 **Issue:** The uploaded file exceeds size limits or available memory")
            
            with st.expander("💡 **Solutions for Large Files**", expanded=True):
                st.markdown("""
                **Reduce file size by filtering your plan:**
                
                1. **Target specific resources:**
                   ```bash
                   terraform plan -target=aws_instance.example -out=tfplan
                   terraform show -json tfplan > filtered-plan.json
                   ```
                
                2. **Use resource addressing:**
                   ```bash
                   terraform plan -target=module.vpc -out=tfplan
                   terraform show -json tfplan > module-plan.json
                   ```
                
                3. **Split large deployments:**
                   - Break your Terraform into smaller modules
                   - Plan and analyze each module separately
                   - Use workspaces for environment separation
                
                **File size limits:**
                - **Recommended:** Under 10MB for best performance
                - **Maximum:** 200MB supported
                - **Current file:** {:.1f}MB
                """.format(len(str(error)) / (1024*1024) if hasattr(error, '__len__') else 0))
                
        elif "resource_changes" in str(error).lower():
            st.error("❌ **Missing Resource Changes**")
            st.warning("🔧 **Issue:** The JSON file doesn't contain the expected `resource_changes` array")
            
            with st.expander("💡 **Common Causes and Solutions**", expanded=True):
                st.markdown("""
                **Possible causes:**
                - No changes in your Terraform plan (everything up-to-date)
                - Wrong JSON format (not a Terraform plan)
                - Incomplete plan generation
                
                **Solutions:**
                1. **Check if there are actually changes:**
                   ```bash
                   terraform plan
                   # Look for "No changes" message
                   ```
                
                2. **Force plan generation:**
                   ```bash
                   terraform plan -refresh=true -out=tfplan
                   terraform show -json tfplan > plan.json
                   ```
                
                3. **Verify JSON structure:**
                   Your file should contain:
                   ```json
                   {
                     "terraform_version": "1.x.x",
                     "resource_changes": [...]
                   }
                   ```
                """)
        else:
            st.error(f"❌ **Upload Error:** {str(error)}")
            if file_name:
                st.info(f"📁 **File:** {file_name}")
            
            # Provide general troubleshooting steps
            with st.expander("🔧 **General Troubleshooting Steps**"):
                st.markdown("""
                1. **Verify file format:** Ensure it's a `.json` file
                2. **Check file size:** Should be between 1KB and 200MB
                3. **Validate JSON:** Use an online JSON validator
                4. **Re-generate plan:** Create a fresh Terraform plan JSON
                5. **Try different browser:** Some browsers handle large files better
                6. **Clear browser cache:** Refresh the page and try again
                """)
            
        self._show_error_details(error)
        
    def handle_processing_error(self, error: Exception, context: str = "processing") -> None:
        """
        Handle plan processing errors with graceful degradation and actionable guidance
        
        Args:
            error: The exception that occurred
            context: Context where the error occurred
        """
        if "risk assessment" in context.lower():
            st.warning("⚠️ **Enhanced Risk Assessment Failed**")
            st.info("🔄 **Automatic Fallback:** Switching to basic risk assessment mode")
            
            with st.expander("🔧 **What This Means**"):
                st.markdown("""
                **Impact on your analysis:**
                - ✅ Basic risk scoring still available
                - ✅ Resource change analysis continues
                - ❌ Multi-cloud risk insights unavailable
                - ❌ Advanced provider-specific recommendations disabled
                
                **Why this happened:**
                - Enhanced features may not be fully installed
                - Plan format may be incompatible with advanced analysis
                - Temporary processing issue
                
                **What you can do:**
                - Continue using the dashboard (basic features work fine)
                - Check if enhanced features are properly installed
                - Try re-uploading your plan file
                """)
                
        elif "parsing" in context.lower():
            st.error("❌ **Plan Parsing Failed**")
            st.warning("🔧 **Issue:** Cannot understand the structure of your Terraform plan")
            
            error_msg = str(error).lower()
            if "version" in error_msg:
                st.info("💡 **Likely Cause:** Terraform version compatibility issue")
                with st.expander("🔧 **Version Compatibility Solutions**"):
                    st.markdown("""
                    **Supported Terraform versions:** 0.12+ (recommended: 1.0+)
                    
                    **Solutions:**
                    1. **Check your Terraform version:**
                       ```bash
                       terraform version
                       ```
                    
                    2. **Update Terraform if needed:**
                       - Download latest from terraform.io
                       - Or use version manager like tfenv
                    
                    3. **Re-generate plan with current version:**
                       ```bash
                       terraform plan -out=tfplan
                       terraform show -json tfplan > new-plan.json
                       ```
                    """)
            elif "format" in error_msg:
                st.info("💡 **Likely Cause:** Unexpected JSON format or structure")
                with st.expander("🔧 **Format Issue Solutions**"):
                    st.markdown("""
                    **Common format issues:**
                    - File is not a Terraform plan JSON
                    - Plan was generated with unsupported flags
                    - JSON structure is corrupted
                    
                    **Solutions:**
                    1. **Verify file is a Terraform plan:**
                       ```bash
                       head -20 your-plan.json
                       # Should show terraform_version, format_version, etc.
                       ```
                    
                    2. **Re-generate with standard commands:**
                       ```bash
                       terraform plan -out=tfplan
                       terraform show -json tfplan > plan.json
                       ```
                    """)
            else:
                with st.expander("🔧 **General Parsing Solutions**"):
                    st.markdown("""
                    **Try these steps:**
                    1. **Verify JSON validity:** Use `python -m json.tool plan.json`
                    2. **Check file completeness:** Ensure upload finished completely
                    3. **Re-generate plan:** Create a fresh plan file
                    4. **Try smaller plan:** Use `-target` to limit scope
                    """)
                    
        elif "provider" in context.lower():
            st.warning("⚠️ **Provider Detection Failed**")
            st.info("🔄 **Automatic Fallback:** Continuing with single-provider analysis")
            
            with st.expander("💡 **What This Means**"):
                st.markdown("""
                **Impact on your analysis:**
                - ✅ Core functionality remains available
                - ✅ Resource analysis continues normally
                - ❌ Multi-cloud insights unavailable
                - ❌ Provider-specific risk analysis disabled
                
                **Common causes:**
                - Plan contains only one cloud provider
                - Provider information not in expected format
                - Enhanced multi-cloud features not available
                
                **This is usually not a problem** - most Terraform plans use a single provider.
                """)
                
        elif "recommendation" in context.lower():
            st.warning("⚠️ **Recommendation Generation Failed**")
            st.info("📋 **Alternative:** Manual review of plan details is recommended")
            
            with st.expander("💡 **Manual Review Checklist**"):
                st.markdown("""
                **Key areas to review manually:**
                
                **🔍 High-Risk Changes:**
                - Resource deletions (especially data stores)
                - Security group modifications
                - IAM role/policy changes
                - Network configuration updates
                
                **⚠️ Deployment Considerations:**
                - Check for resource dependencies
                - Verify backup procedures for critical resources
                - Plan for potential downtime
                - Review change timing and coordination needs
                
                **📊 Use Dashboard Features:**
                - Filter by risk level to focus on critical changes
                - Export data for detailed offline review
                - Use visualizations to understand change patterns
                """)
                
        elif "chart" in context.lower() or "visualization" in context.lower():
            st.warning("⚠️ **Visualization Generation Failed**")
            st.info("📊 **Alternative:** Data is still available in table format below")
            
            with st.expander("🔧 **Visualization Troubleshooting**"):
                st.markdown("""
                **Common causes:**
                - Large dataset causing rendering issues
                - Missing or invalid data for chart type
                - Browser compatibility issues
                
                **Alternatives:**
                - Use the data table for detailed analysis
                - Export data as CSV for external visualization
                - Try refreshing the page
                - Use a different browser if issues persist
                """)
        else:
            st.error(f"❌ **Processing Error in {context.title()}**")
            st.warning(f"🔧 **Issue:** {str(error)}")
            
            with st.expander("🔧 **General Recovery Steps**"):
                st.markdown("""
                **Immediate actions:**
                1. **Refresh the page** and try again
                2. **Check your internet connection**
                3. **Try uploading a different/smaller file**
                4. **Clear browser cache** if issues persist
                
                **If problems continue:**
                - Some features may be temporarily unavailable
                - Core functionality should still work
                - Try using basic mode (disable enhanced features)
                - Consider breaking large plans into smaller chunks
                """)
            
        self._show_error_details(error)
        
    def handle_visualization_error(self, error: Exception, chart_type: str = "chart") -> None:
        """
        Handle visualization errors with fallback options and actionable guidance
        
        Args:
            error: The exception that occurred
            chart_type: Type of chart that failed to render
        """
        if "plotly" in str(error).lower() or "chart" in str(error).lower():
            st.warning(f"⚠️ **{chart_type.title()} Rendering Failed**")
            st.info("📊 **Alternative:** Data is available in table format below")
            
            with st.expander("🔧 **Chart Troubleshooting**"):
                st.markdown(f"""
                **Why {chart_type} failed to render:**
                - Large dataset may be causing performance issues
                - Browser compatibility problems with interactive charts
                - Data format incompatible with chart requirements
                
                **What you can do:**
                1. **Use data table:** All information is available in table format
                2. **Export data:** Download CSV for external visualization tools
                3. **Try filters:** Reduce data size using sidebar filters
                4. **Refresh page:** Sometimes resolves temporary rendering issues
                5. **Different browser:** Try Chrome, Firefox, or Edge
                
                **Alternative visualization tools:**
                - Excel/Google Sheets for basic charts
                - Tableau/Power BI for advanced analysis
                - Python/R for custom visualizations
                """)
                
        elif "data" in str(error).lower() or "empty" in str(error).lower():
            st.info(f"📊 **No Data for {chart_type.title()}**")
            
            with st.expander("💡 **Why This Happens**"):
                st.markdown(f"""
                **This is usually normal and means:**
                - Your plan doesn't contain resources relevant to this {chart_type}
                - All resources are of the same type (for distribution charts)
                - Filters have excluded all data points
                
                **What to check:**
                1. **Review your plan:** Ensure it contains the expected changes
                2. **Check filters:** Clear filters to see if data appears
                3. **Verify plan scope:** Your plan might be targeting specific resources
                
                **This doesn't indicate a problem** - it just means this particular visualization isn't applicable to your current plan.
                """)
                
        elif "provider" in str(error).lower():
            st.warning(f"⚠️ **Multi-Cloud {chart_type.title()} Unavailable**")
            st.info("🔄 **Fallback:** Continuing with single-provider analysis")
            
            with st.expander("💡 **Multi-Cloud Chart Requirements**"):
                st.markdown("""
                **For multi-cloud charts to work, you need:**
                - Enhanced features enabled (check sidebar)
                - Plan with resources from multiple providers
                - Compatible Terraform plan format
                
                **Common scenarios:**
                - **Single provider:** Most plans use only AWS, Azure, or GCP
                - **Mixed resources:** Some resources may not have clear provider attribution
                - **Feature disabled:** Multi-cloud features may be turned off
                
                **Single-provider analysis still provides:**
                - Resource type distributions
                - Risk assessments
                - Change action breakdowns
                """)
                
        elif "memory" in str(error).lower() or "performance" in str(error).lower():
            st.warning(f"⚠️ **{chart_type.title()} Too Large to Render**")
            st.info("📊 **Alternative:** Use filters to reduce data size, then try again")
            
            with st.expander("🔧 **Large Dataset Solutions**"):
                st.markdown("""
                **Your plan is too large for interactive visualization:**
                
                **Immediate solutions:**
                1. **Use sidebar filters** to reduce data size
                2. **Focus on specific resource types** or actions
                3. **Export data** for analysis in external tools
                
                **For future large plans:**
                - Break Terraform into smaller modules
                - Use targeted plans: `terraform plan -target=module.vpc`
                - Consider workspace separation for different environments
                
                **Performance tips:**
                - Filter before viewing charts
                - Use basic mode for very large plans
                - Export data for offline analysis
                """)
        else:
            st.error(f"❌ **{chart_type.title()} Generation Error**")
            st.warning(f"🔧 **Technical Issue:** {str(error)}")
            st.info("📊 **Good News:** Other dashboard features remain fully available")
            
            with st.expander("🔧 **Recovery Options**"):
                st.markdown(f"""
                **What you can do right now:**
                1. **Continue using other features** - tables, filters, exports all work
                2. **Try refreshing the page** - may resolve temporary issues
                3. **Use different chart types** - other visualizations may work
                4. **Export data** - analyze in your preferred tool
                
                **If this keeps happening:**
                - Your plan may have unusual data that's hard to visualize
                - Try using basic mode (disable enhanced features)
                - Consider filtering to smaller data subsets
                - The core analysis functionality is unaffected
                """)
            
        self._show_error_details(error)
    
    def handle_table_error(self, error: Exception) -> None:
        """
        Handle data table creation errors
        
        Args:
            error: The exception that occurred
        """
        st.error(f"❌ Error creating resource table: {str(error)}")
        st.info("💡 The resource details table could not be generated. Raw data may still be available for download.")
        self._show_error_details(error)
    
    def handle_filter_error(self, error: Exception) -> None:
        """
        Handle filter application errors
        
        Args:
            error: The exception that occurred
        """
        st.warning("⚠️ Error applying filters. Showing unfiltered results.")
        st.info("💡 Try adjusting your filter selections or refreshing the page.")
        self._show_error_details(error)
        
    def handle_enhanced_features_error(self, error: Exception) -> None:
        """
        Handle enhanced features errors with fallback to basic mode
        
        Args:
            error: The exception that occurred
        """
        if isinstance(error, ImportError):
            st.warning("⚙️ Enhanced multi-cloud features are not available.")
            st.info("💡 To enable enhanced features, ensure all provider files are in place. Continuing in basic mode.")
        else:
            st.warning(f"⚠️ Enhanced features encountered an error: {str(error)}")
            st.info("💡 Falling back to basic mode. Core functionality remains available.")
            
        self._show_error_details(error)
    
    def handle_import_fallback(self, feature_name: str, error: ImportError) -> bool:
        """
        Handle ImportError for enhanced features with graceful fallback
        
        Args:
            feature_name: Name of the feature that failed to import
            error: The ImportError that occurred
            
        Returns:
            bool: False to indicate enhanced features are not available
        """
        if self.debug_mode:
            st.warning(f"⚙️ {feature_name} not available: {str(error)}")
        else:
            st.warning(f"⚙️ {feature_name} not available - using basic mode")
        
        st.info("💡 To enable enhanced features, ensure all required dependencies are installed.")
        self._show_error_details(error)
        return False
    
    def handle_feature_degradation(self, feature_name: str, error: Exception, fallback_message: str = None) -> None:
        """
        Handle feature degradation with user-friendly messaging
        
        Args:
            feature_name: Name of the feature that failed
            error: The exception that occurred
            fallback_message: Optional custom fallback message
        """
        st.warning(f"⚠️ {feature_name} failed, falling back to basic functionality")
        
        if fallback_message:
            st.info(f"💡 {fallback_message}")
        else:
            st.info("💡 Core functionality remains available.")
            
        self._show_error_details(error)
    
    def get_safe_fallback_value(self, primary_value: Any, fallback_value: Any, context: str = "") -> Any:
        """
        Safely return a fallback value if primary value is None or causes issues
        
        Args:
            primary_value: The preferred value to use
            fallback_value: The fallback value if primary fails
            context: Context for error reporting
            
        Returns:
            Either the primary value or fallback value
        """
        try:
            if primary_value is not None:
                return primary_value
            else:
                if context and self.debug_mode:
                    st.info(f"🔄 Using fallback value for {context}")
                return fallback_value
        except Exception as e:
            if context:
                st.warning(f"⚠️ Error accessing {context}, using fallback")
            self._show_error_details(e)
            return fallback_value
    
    def with_fallback(self, primary_func, fallback_func, context: str = "operation"):
        """
        Execute a function with automatic fallback on failure
        
        Args:
            primary_func: Primary function to try
            fallback_func: Fallback function if primary fails
            context: Context for error reporting
            
        Returns:
            Result from either primary or fallback function
        """
        try:
            return primary_func()
        except Exception as e:
            st.warning(f"⚠️ {context.title()} failed, using fallback approach")
            self._show_error_details(e)
            try:
                return fallback_func()
            except Exception as fallback_error:
                st.error(f"❌ Both primary and fallback {context} failed")
                self._show_error_details(fallback_error)
                return None
        
    def show_contextual_help(self, feature_name: str, help_content: dict) -> None:
        """
        Show contextual help for complex features with progressive disclosure
        
        Args:
            feature_name: Name of the feature to show help for
            help_content: Dictionary containing help information
        """
        help_key = f"help_{feature_name.lower().replace(' ', '_')}"
        
        # Create help button/expander based on content complexity
        if help_content.get('quick_tip'):
            st.info(f"💡 **Quick Tip:** {help_content['quick_tip']}")
        
        if help_content.get('detailed_help'):
            with st.expander(f"❓ Learn more about {feature_name}", expanded=False):
                st.markdown(help_content['detailed_help'])
        
        if help_content.get('troubleshooting'):
            with st.expander(f"🔧 Troubleshooting {feature_name}", expanded=False):
                st.markdown(help_content['troubleshooting'])
    
    def show_feature_tooltip(self, feature_name: str, tooltip_text: str, tooltip_type: str = "info") -> None:
        """
        Show tooltip for features with different styling based on type
        
        Args:
            feature_name: Name of the feature
            tooltip_text: Tooltip content
            tooltip_type: Type of tooltip (info, warning, success, error)
        """
        icon_map = {
            "info": "💡",
            "warning": "⚠️", 
            "success": "✅",
            "error": "❌",
            "tip": "🔍",
            "security": "🔒",
            "performance": "⚡"
        }
        
        icon = icon_map.get(tooltip_type, "💡")
        
        if tooltip_type == "warning":
            st.warning(f"{icon} **{feature_name}:** {tooltip_text}")
        elif tooltip_type == "success":
            st.success(f"{icon} **{feature_name}:** {tooltip_text}")
        elif tooltip_type == "error":
            st.error(f"{icon} **{feature_name}:** {tooltip_text}")
        else:
            st.info(f"{icon} **{feature_name}:** {tooltip_text}")
    
    def show_progressive_disclosure(self, basic_content: str, advanced_content: str, 
                                  title: str = "Advanced Options", expanded: bool = False) -> None:
        """
        Implement progressive disclosure for advanced features
        
        Args:
            basic_content: Content always visible
            advanced_content: Content shown in expandable section
            title: Title for the advanced section
            expanded: Whether advanced section starts expanded
        """
        # Show basic content
        st.markdown(basic_content)
        
        # Show advanced content in expander
        with st.expander(title, expanded=expanded):
            st.markdown(advanced_content)
    
    def show_onboarding_hint(self, feature_name: str, hint_text: str, show_once: bool = False) -> None:
        """
        Show onboarding hints for new users with smart defaults
        
        Args:
            feature_name: Name of the feature to show hint for
            hint_text: The hint text to display
            show_once: Whether to show this hint only once per session
        """
        hint_key = f"onboarding_hint_{feature_name.lower().replace(' ', '_')}"
        
        if show_once and st.session_state.get(f"{hint_key}_shown", False):
            return
        
        # Show hint with contextual styling
        st.info(f"💡 **{feature_name}:** {hint_text}")
        
        if show_once:
            st.session_state[f"{hint_key}_shown"] = True
    
    def show_data_quality_warning(self, data_type: str, issues: List[str], suggestions: List[str]) -> None:
        """
        Show data quality warnings with actionable suggestions
        
        Args:
            data_type: Type of data with quality issues
            issues: List of identified issues
            suggestions: List of actionable suggestions
        """
        st.warning(f"⚠️ **Data Quality Issues in {data_type}**")
        
        with st.expander("📋 **Issues Found**", expanded=True):
            for issue in issues:
                st.write(f"• {issue}")
        
        if suggestions:
            with st.expander("💡 **Suggested Actions**", expanded=True):
                for i, suggestion in enumerate(suggestions, 1):
                    st.write(f"{i}. {suggestion}")
    
    def show_interactive_onboarding(self) -> None:
        """Show interactive onboarding for new users"""
        if not st.session_state.get('onboarding_completed', False):
            onboarding_step = st.session_state.get('onboarding_step', 0)
            
            if onboarding_step == 0:
                # Welcome step
                st.success("🎉 **Welcome to the Terraform Plan Impact Dashboard!**")
                
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown("""
                    This interactive guide will help you get started with analyzing your Terraform plans.
                    You'll learn how to upload files, interpret results, and use advanced features.
                    """)
                
                with col2:
                    if st.button("🚀 Start Guide", type="primary"):
                        st.session_state['onboarding_step'] = 1
                        st.rerun()
                
                if st.button("⏭️ Skip Onboarding"):
                    st.session_state['onboarding_completed'] = True
                    st.rerun()
                    
            elif onboarding_step == 1:
                # File upload guidance
                self._show_onboarding_step(
                    step=1,
                    title="Upload Your Terraform Plan",
                    content="""
                    **First, you need a Terraform plan in JSON format.**
                    
                    Generate one using these commands:
                    ```bash
                    terraform plan -out=tfplan
                    terraform show -json tfplan > plan.json
                    ```
                    
                    Then upload the `plan.json` file using the file uploader above.
                    """,
                    next_action="Upload a file to continue"
                )
                
            elif onboarding_step == 2:
                # Analysis interpretation
                self._show_onboarding_step(
                    step=2,
                    title="Understanding Your Analysis",
                    content="""
                    **After uploading, you'll see several sections:**
                    
                    📊 **Summary Cards** - Quick overview of changes and risk levels
                    📈 **Visualizations** - Interactive charts showing resource patterns  
                    📋 **Data Table** - Detailed resource information with filtering
                    ⚠️ **Risk Assessment** - Intelligent scoring of deployment risks
                    """,
                    next_action="Explore the analysis sections"
                )
                
            elif onboarding_step == 3:
                # Feature discovery
                self._show_onboarding_step(
                    step=3,
                    title="Discover Advanced Features",
                    content="""
                    **Enhance your analysis with these features:**
                    
                    🔍 **Smart Filtering** - Focus on specific resources or risk levels
                    🌐 **Multi-Cloud Analysis** - Cross-provider insights (when available)
                    📄 **Report Generation** - Export comprehensive reports
                    🔒 **Security Analysis** - Security-focused resource highlighting
                    """,
                    next_action="Try using the sidebar filters"
                )
    
    def _show_onboarding_step(self, step: int, title: str, content: str, next_action: str) -> None:
        """Show individual onboarding step with navigation"""
        with st.container():
            st.info(f"**Step {step}/3: {title}**")
            st.markdown(content)
            
            col1, col2, col3 = st.columns([1, 2, 1])
            
            with col1:
                if step > 1 and st.button("⬅️ Previous"):
                    st.session_state['onboarding_step'] = step - 1
                    st.rerun()
            
            with col2:
                st.caption(f"💡 {next_action}")
            
            with col3:
                if step < 3:
                    if st.button("➡️ Next"):
                        st.session_state['onboarding_step'] = step + 1
                        st.rerun()
                else:
                    if st.button("✅ Complete"):
                        st.session_state['onboarding_completed'] = True
                        st.success("🎉 Onboarding completed! You're ready to analyze Terraform plans.")
                        st.rerun()
    
    def show_feature_discovery_popup(self, feature_name: str, description: str, 
                                   benefits: List[str], how_to_use: str) -> None:
        """
        Show feature discovery popup for newly discovered features
        
        Args:
            feature_name: Name of the discovered feature
            description: Description of what the feature does
            benefits: List of benefits this feature provides
            how_to_use: Instructions on how to use the feature
        """
        discovery_key = f"discovered_{feature_name.lower().replace(' ', '_')}"
        
        if not st.session_state.get(discovery_key, False):
            with st.expander(f"✨ **New Feature Discovered: {feature_name}**", expanded=True):
                st.markdown(f"**{description}**")
                
                if benefits:
                    st.markdown("**🎯 Benefits:**")
                    for benefit in benefits:
                        st.write(f"• {benefit}")
                
                st.info(f"**💡 How to use:** {how_to_use}")
                
                col1, col2 = st.columns([1, 1])
                with col1:
                    if st.button("🚀 Try It Now", key=f"try_{discovery_key}"):
                        st.session_state[discovery_key] = True
                        st.session_state[f"{discovery_key}_activated"] = True
                        st.rerun()
                
                with col2:
                    if st.button("✅ Got It", key=f"dismiss_{discovery_key}"):
                        st.session_state[discovery_key] = True
                        st.rerun()
    
    def apply_smart_defaults_for_use_case(self, use_case: str) -> None:
        """
        Apply smart defaults based on common use cases
        
        Args:
            use_case: The selected use case scenario
        """
        defaults = {
            'Security Review': {
                'risk_filter': ['High', 'Critical'],
                'search_focus': 'security|iam|policy|role|group|firewall',
                'show_help': True,
                'message': 'Applied security-focused defaults: showing high-risk changes and security-related resources'
            },
            'Production Deployment': {
                'risk_filter': ['Medium', 'High', 'Critical'],
                'action_filter': ['delete', 'replace', 'update'],
                'show_help': True,
                'message': 'Applied production defaults: focusing on potentially disruptive changes'
            },
            'Development Testing': {
                'action_filter': ['create', 'update', 'delete', 'replace'],
                'risk_filter': ['Low', 'Medium', 'High', 'Critical'],
                'debug_mode': True,
                'message': 'Applied development defaults: showing all changes with debug information'
            },
            'Multi-Cloud Migration': {
                'multi_cloud_enabled': True,
                'show_help': True,
                'message': 'Applied multi-cloud defaults: enabled cross-provider analysis features'
            },
            'Cost Optimization': {
                'search_focus': 'instance|compute|storage|database|rds|ec2|vm|disk',
                'action_filter': ['create', 'update', 'replace'],
                'message': 'Applied cost optimization defaults: focusing on compute and storage resources'
            }
        }
        
        if use_case in defaults:
            config = defaults[use_case]
            
            # Apply the defaults to session state
            for key, value in config.items():
                if key != 'message':
                    st.session_state[key] = value
            
            # Show confirmation message
            st.success(f"✅ {config['message']}")
    
    def show_contextual_tips(self, context: str, tips: List[str]) -> None:
        """
        Show contextual tips based on current user context
        
        Args:
            context: Current context (e.g., 'file_upload', 'analysis', 'filtering')
            tips: List of relevant tips to show
        """
        tip_key = f"tips_{context}"
        
        if not st.session_state.get(f"{tip_key}_dismissed", False):
            with st.expander(f"💡 **Tips for {context.replace('_', ' ').title()}**", expanded=False):
                for i, tip in enumerate(tips, 1):
                    st.write(f"{i}. {tip}")
                
                if st.button("✅ Got it!", key=f"dismiss_{tip_key}"):
                    st.session_state[f"{tip_key}_dismissed"] = True
                    st.rerun()
    
    def track_user_progress(self, milestone: str) -> None:
        """
        Track user progress through the application for better onboarding
        
        Args:
            milestone: The milestone achieved (e.g., 'file_uploaded', 'filters_used')
        """
        milestones = st.session_state.get('user_milestones', [])
        
        if milestone not in milestones:
            milestones.append(milestone)
            st.session_state['user_milestones'] = milestones
            
            # Show progress-based hints
            self._show_progress_based_hints(milestone, len(milestones))
    
    def _show_progress_based_hints(self, latest_milestone: str, total_milestones: int) -> None:
        """Show hints based on user progress"""
        hints = {
            'file_uploaded': "Great! Your file is uploaded. Next, explore the summary cards below to understand your changes.",
            'summary_viewed': "Nice! You've seen the overview. Try the interactive charts for visual insights.",
            'charts_viewed': "Excellent! Now check out the detailed data table for specific resource information.",
            'filters_used': "Perfect! You're using filters effectively. Consider exporting your filtered results.",
            'data_exported': "Outstanding! You're making full use of the dashboard's capabilities."
        }
        
        if latest_milestone in hints and total_milestones <= 3:  # Only show for early users
            st.info(f"🎯 **Progress Update:** {hints[latest_milestone]}")
    
    def show_keyboard_shortcuts_guide(self) -> None:
        """Show keyboard shortcuts and accessibility features"""
        with st.expander("⌨️ **Keyboard Shortcuts & Accessibility**", expanded=False):
            st.markdown("""
            **Navigation Shortcuts:**
            - `Tab` / `Shift+Tab` - Navigate between interactive elements
            - `Enter` / `Space` - Activate buttons and controls
            - `Esc` - Close modals and expandable sections
            
            **Filter Shortcuts:**
            - `Ctrl+F` / `Cmd+F` - Focus search box (when available)
            - `Arrow Keys` - Navigate dropdown options
            - `Enter` - Apply selected filters
            
            **Accessibility Features:**
            - Screen reader compatible
            - High contrast mode support
            - Keyboard-only navigation
            - Focus indicators on all interactive elements
            
            **Export Shortcuts:**
            - `Ctrl+S` / `Cmd+S` - Quick save/export (when export is active)
            """)
    
    def _show_error_details(self, error: Exception) -> None:
        """
        Show error details in debug mode with enhanced troubleshooting
        
        Args:
            error: The exception to show details for
        """
        if self.debug_mode:
            with st.expander("🐛 **Debug Information**", expanded=False):
                st.code(f"Error Type: {type(error).__name__}")
                st.code(f"Error Message: {str(error)}")
                
                # Show stack trace for debugging
                if hasattr(error, '__traceback__'):
                    st.code("Stack Trace:")
                    st.code(traceback.format_exc())
                
                # Show troubleshooting suggestions based on error type
                self._show_error_specific_troubleshooting(error)
    
    def _show_error_specific_troubleshooting(self, error: Exception) -> None:
        """Show specific troubleshooting based on error type"""
        error_type = type(error).__name__
        
        troubleshooting = {
            'JSONDecodeError': [
                "Validate JSON syntax using an online JSON validator",
                "Re-generate the Terraform plan JSON file",
                "Check if the file upload completed successfully"
            ],
            'KeyError': [
                "Verify the Terraform plan contains the expected structure",
                "Check if the plan was generated with a compatible Terraform version",
                "Try generating the plan with different output options"
            ],
            'ImportError': [
                "Check if all required dependencies are installed",
                "Verify the Python environment has necessary packages",
                "Try refreshing the page to reload modules"
            ],
            'MemoryError': [
                "Try uploading a smaller plan file",
                "Use targeted Terraform plans with -target flag",
                "Close other browser tabs to free memory"
            ]
        }
        
        if error_type in troubleshooting:
            st.markdown("**🔧 Specific Troubleshooting Steps:**")
            for step in troubleshooting[error_type]:
                st.write(f"• {step}")
    
    def show_onboarding_hint(self, feature_name: str, hint_text: str, 
                           show_once: bool = True) -> None:
        """
        Show onboarding hints for new users with option to show only once
        
        Args:
            feature_name: Name of the feature
            hint_text: Hint text to display
            show_once: Whether to show this hint only once per session
        """
        hint_key = f"hint_shown_{feature_name.lower().replace(' ', '_')}"
        
        # Check if hint should be shown
        if show_once and st.session_state.get(hint_key, False):
            return
        
        # Show hint with dismiss option
        col1, col2 = st.columns([4, 1])
        
        with col1:
            st.info(f"🎯 **New to {feature_name}?** {hint_text}")
        
        with col2:
            if st.button("Got it!", key=f"dismiss_{hint_key}"):
                if show_once:
                    st.session_state[hint_key] = True
                st.rerun()
    
    def show_feature_status(self, feature_name: str, is_available: bool, 
                          reason: str = "", help_text: str = "") -> None:
        """
        Show feature availability status with helpful context
        
        Args:
            feature_name: Name of the feature
            is_available: Whether the feature is available
            reason: Reason why feature is/isn't available
            help_text: Additional help text
        """
        if is_available:
            st.success(f"✅ **{feature_name}** is available")
            if help_text:
                st.caption(help_text)
        else:
            st.warning(f"⚠️ **{feature_name}** is not available")
            if reason:
                st.caption(f"**Reason:** {reason}")
            if help_text:
                with st.expander(f"💡 How to enable {feature_name}"):
                    st.markdown(help_text)
    
    def show_data_quality_warning(self, data_type: str, issues: list, 
                                suggestions: list = None) -> None:
        """
        Show warnings about data quality issues with suggestions
        
        Args:
            data_type: Type of data with issues
            issues: List of issues found
            suggestions: List of suggestions to fix issues
        """
        st.warning(f"⚠️ **Data Quality Issues in {data_type}**")
        
        with st.expander("🔍 Details and Suggestions", expanded=True):
            st.markdown("**Issues found:**")
            for issue in issues:
                st.write(f"• {issue}")
            
            if suggestions:
                st.markdown("**Suggestions:**")
                for suggestion in suggestions:
                    st.write(f"💡 {suggestion}")
    
    def _show_error_details(self, error: Exception) -> None:
        """
        Show detailed error information in debug mode with enhanced formatting
        
        Args:
            error: The exception to show details for
        """
        if self.debug_mode:
            with st.expander("🔍 **Debug Information**", expanded=False):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**Error Details:**")
                    st.text(f"Type: {type(error).__name__}")
                    st.text(f"Message: {str(error)}")
                
                with col2:
                    st.markdown("**Context:**")
                    st.text(f"Module: {error.__class__.__module__}")
                    if hasattr(error, 'filename'):
                        st.text(f"File: {error.filename}")
                    if hasattr(error, 'lineno'):
                        st.text(f"Line: {error.lineno}")
                
                st.markdown("**Full Traceback:**")
                st.code(traceback.format_exc(), language="python")
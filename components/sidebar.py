"""
Sidebar component for the Terraform Plan Impact Dashboard.

This component handles the sidebar title, controls, and basic functionality
extracted from the main app.py file.
"""

import streamlit as st
from ui.session_manager import SessionStateManager
from ui.error_handler import ErrorHandler


class SidebarComponent:
    """Component for rendering the dashboard sidebar with controls and status."""
    
    def __init__(self):
        """Initialize the SidebarComponent."""
        self.session_manager = SessionStateManager()
    
    def render(self, enhanced_features_available: bool, enhanced_risk_result=None, enable_multi_cloud=True) -> dict:
        """
        Render the sidebar with enhanced guidance, title, controls, and status information.
        
        Args:
            enhanced_features_available (bool): Whether enhanced multi-cloud features are available
            enhanced_risk_result: Enhanced risk assessment result for provider filter options
            enable_multi_cloud (bool): Whether multi-cloud features are enabled
            
        Returns:
            dict: Dictionary containing the current state of sidebar controls
        """
        error_handler = ErrorHandler()
        
        # Sidebar title and header
        st.sidebar.title("📊 Dashboard Controls")
        st.sidebar.markdown("---")
        
        # Enhanced features status with detailed explanation
        st.sidebar.markdown("### 🌟 Feature Status")
        
        if enhanced_features_available:
            st.sidebar.success("✅ Enhanced Multi-Cloud Features Available")
            error_handler.show_onboarding_hint(
                "Multi-Cloud Features",
                "Advanced provider detection and cross-cloud analysis are enabled for comprehensive multi-cloud insights.",
                show_once=True
            )
        else:
            st.sidebar.info("ℹ️ Basic Features Available")
            error_handler.show_onboarding_hint(
                "Basic Mode",
                "Core functionality is available. Enhanced features require additional dependencies.",
                show_once=True
            )
            
            # Show detailed help about missing features
            with st.sidebar.expander("❓ About Enhanced Features", expanded=False):
                st.markdown("""
                **To enable enhanced features:**
                
                1. **Check file structure:** Ensure all provider files are in the `providers/` directory
                2. **Verify dependencies:** Enhanced features require additional Python packages
                3. **Restart application:** After installing dependencies, restart the dashboard
                
                **What you're missing:**
                - Advanced provider detection
                - Cross-cloud risk analysis
                - Multi-cloud visualizations
                - Provider-specific recommendations
                
                **Basic features still available:**
                - Core risk assessment
                - Resource change analysis
                - Standard visualizations
                - Data export functionality
                """)
        
        st.sidebar.markdown("---")
        st.sidebar.markdown("### ⚙️ Analysis Options")
        
        # Debug toggle with enhanced help
        show_debug = st.sidebar.checkbox(
            "🔍 Show Debug Information", 
            value=False,
            help="""
            **Debug mode shows:**
            • Detailed parsing information
            • Plan structure analysis
            • Error diagnostics and stack traces
            • Performance metrics
            • Cache statistics
            
            **When to enable:**
            • Troubleshooting upload issues
            • Understanding plan processing
            • Performance analysis
            • Reporting bugs or issues
            
            **Note:** Debug information appears throughout the dashboard when enabled.
            """
        )
        
        # Show debug mode explanation when enabled
        if show_debug:
            st.sidebar.info("🔍 Debug mode active - detailed information will be shown throughout the dashboard")
        
        # Multi-cloud features toggle with progressive disclosure
        enable_multi_cloud_toggle = True
        if enhanced_features_available:
            enable_multi_cloud_toggle = st.sidebar.checkbox(
                "🌐 Enable Multi-Cloud Features", 
                value=True,
                help="""
                **Multi-cloud features include:**
                • Cross-provider risk assessment
                • Provider-specific insights
                • Multi-cloud visualizations
                • Cloud service usage patterns
                • Cross-cloud security analysis
                
                **Performance impact:**
                • Slightly slower processing for large plans
                • Additional memory usage
                • More detailed analysis
                
                **Disable if:**
                • Using single cloud provider only
                • Need faster processing
                • Experiencing performance issues
                """
            )
            
            # Show status and guidance based on toggle state
            if enable_multi_cloud_toggle:
                st.sidebar.success("🌐 Multi-cloud analysis enabled")
                
                # Show onboarding hint for multi-cloud features
                error_handler.show_onboarding_hint(
                    "Multi-Cloud Analysis",
                    "Look for provider-specific sections and cross-cloud insights in your analysis results.",
                    show_once=True
                )
            else:
                st.sidebar.info("🌐 Using basic single-provider mode")
                error_handler.show_progressive_disclosure(
                    "**Basic mode active:** Analysis will focus on single-provider insights.",
                    """
                    **What's different in basic mode:**
                    - Faster processing for large plans
                    - Single-provider risk assessment
                    - Standard visualizations only
                    - No cross-cloud insights
                    
                    **To get multi-cloud features:**
                    - Enable the checkbox above
                    - Ensure your plan contains multiple providers
                    - Allow extra processing time for large plans
                    """,
                    "Multi-Cloud Mode Benefits"
                )
        else:
            st.sidebar.info("🌐 Multi-cloud features unavailable - using basic mode")
        
        # Show feature comparison for new users
        if st.sidebar.button("❓ Compare Feature Modes", help="See the differences between basic and enhanced modes"):
            with st.sidebar.expander("📊 Feature Comparison", expanded=True):
                st.markdown("""
                **Basic Mode:**
                ✅ Core risk assessment
                ✅ Resource change analysis  
                ✅ Standard charts
                ✅ Data filtering & export
                ❌ Multi-cloud insights
                ❌ Provider-specific analysis
                
                **Enhanced Mode:**
                ✅ Everything in Basic Mode
                ✅ Advanced provider detection
                ✅ Cross-cloud risk analysis
                ✅ Multi-cloud visualizations
                ✅ Provider-specific recommendations
                ✅ Security compliance checks
                """)
        
        # Return the current state
        return {
            'show_debug': show_debug,
            'enable_multi_cloud': enable_multi_cloud_toggle
        }
    
    def render_filters(self, enhanced_features_available: bool, enhanced_risk_result=None, enable_multi_cloud=True) -> dict:
        """
        Render the filter controls in the sidebar.
        
        Args:
            enhanced_features_available (bool): Whether enhanced multi-cloud features are available
            enhanced_risk_result: Enhanced risk assessment result for provider filter options
            enable_multi_cloud (bool): Whether multi-cloud features are enabled
            
        Returns:
            dict: Dictionary containing the current filter states
        """
        # Filters section header
        st.sidebar.markdown("### 🔍 Filters")
        
        # Get current filter state from session manager
        current_filter_state = self.session_manager.get_filter_state()
        
        # Action filter with tooltip
        action_filter = st.sidebar.multiselect(
            "Filter by Action",
            options=['create', 'update', 'delete', 'replace'],
            default=current_filter_state.get('action_filter', ['create', 'update', 'delete', 'replace']),
            help="Filter resources by Terraform action type:\n• Create: New resources being added\n• Update: Existing resources being modified\n• Delete: Resources being removed\n• Replace: Resources being destroyed and recreated"
        )
        
        # Risk filter with tooltip
        risk_filter = st.sidebar.multiselect(
            "Filter by Risk Level",
            options=['Low', 'Medium', 'High'],
            default=current_filter_state.get('risk_filter', ['Low', 'Medium', 'High']),
            help="Filter resources by calculated risk level:\n• Low: Safe changes with minimal impact\n• Medium: Changes requiring attention\n• High: Potentially dangerous changes requiring careful review"
        )
        
        # Provider filter (if multi-cloud enabled and data available)
        provider_filter = None
        if enhanced_features_available and enable_multi_cloud:
            try:
                if isinstance(enhanced_risk_result, dict) and enhanced_risk_result.get('provider_risk_summary'):
                    available_providers = list(enhanced_risk_result['provider_risk_summary'].keys())
                    if available_providers:
                        current_provider_filter = current_filter_state.get('provider_filter', available_providers)
                        # Ensure current provider filter only contains available providers
                        valid_provider_filter = [p for p in current_provider_filter if p in available_providers]
                        if not valid_provider_filter:
                            valid_provider_filter = available_providers
                        
                        provider_filter = st.sidebar.multiselect(
                            "Filter by Provider",
                            options=available_providers,
                            default=valid_provider_filter,
                            help="Filter resources by cloud provider. Shows only providers detected in your Terraform plan. Useful for focusing on specific cloud environments in multi-cloud deployments."
                        )
            except:
                pass
        
        # Advanced filter combination logic
        st.sidebar.markdown("#### 🔗 Advanced Filter Logic")
        
        # Basic AND/OR logic
        current_filter_logic = self.session_manager.get_filter_logic()
        filter_logic_index = 0 if current_filter_logic == "AND" else 1
        filter_logic = st.sidebar.radio(
            "Basic Logic:",
            options=["AND", "OR"],
            index=filter_logic_index,
            help="AND: Show resources that match ALL selected filters\nOR: Show resources that match ANY selected filter",
            horizontal=True
        )
        
        # Advanced filter expression builder
        with st.sidebar.expander("🔧 Advanced Filter Builder", expanded=False):
            st.markdown("**Build Complex Filter Expressions**")
            
            # Enable advanced mode
            use_advanced_filters = st.checkbox(
                "Enable Advanced Filter Expressions",
                help="Create complex filter combinations using custom expressions"
            )
            
            if use_advanced_filters:
                # Filter expression input
                filter_expression = st.text_area(
                    "Filter Expression",
                    value=self.session_manager.get_session_value('filter_expression', ''),
                    placeholder="(action='create' OR action='update') AND risk='High'",
                    help="""
                    **Expression Syntax:**
                    • Use field names: action, risk, provider, type, name
                    • Operators: =, !=, IN, NOT IN
                    • Logic: AND, OR, NOT, ( )
                    • Values: 'create', 'High', etc.
                    
                    **Examples:**
                    • action='create' AND risk='High'
                    • (action='delete' OR action='replace') AND provider='aws'
                    • risk IN ('Medium', 'High') AND type LIKE 'aws_instance'
                    """,
                    height=100
                )
                
                # Save expression to session state
                self.session_manager.set_session_value('filter_expression', filter_expression)
                
                # Validate expression
                validation_result = self._validate_filter_expression(filter_expression)
                
                if filter_expression and filter_expression.strip():
                    if validation_result['valid']:
                        st.success("✅ Expression is valid")
                        
                        # Show parsed expression preview
                        with st.expander("📋 Expression Preview", expanded=False):
                            st.code(validation_result['parsed'], language='text')
                    else:
                        st.error(f"❌ Invalid expression: {validation_result['error']}")
                        
                        # Show syntax help
                        with st.expander("❓ Syntax Help", expanded=True):
                            st.markdown("""
                            **Common Issues:**
                            • Use single quotes for values: 'create' not create
                            • Check parentheses balance: ( )
                            • Use correct field names: action, risk, provider
                            • Separate conditions with AND/OR
                            
                            **Valid Field Names:**
                            • action: 'create', 'update', 'delete', 'replace'
                            • risk: 'Low', 'Medium', 'High'
                            • provider: 'aws', 'azure', 'gcp'
                            • type: resource type (e.g., 'aws_instance')
                            • name: resource name
                            """)
                
                # Expression templates
                st.markdown("**Quick Templates:**")
                template_col1, template_col2 = st.columns(2)
                
                with template_col1:
                    if st.button("High Risk Creates", help="New high-risk resources"):
                        template = "action='create' AND risk='High'"
                        self.session_manager.set_session_value('filter_expression', template)
                        st.rerun()
                    
                    if st.button("AWS Deletions", help="AWS resources being deleted"):
                        template = "action='delete' AND provider='aws'"
                        self.session_manager.set_session_value('filter_expression', template)
                        st.rerun()
                
                with template_col2:
                    if st.button("Critical Changes", help="High-risk updates or replacements"):
                        template = "(action='update' OR action='replace') AND risk='High'"
                        self.session_manager.set_session_value('filter_expression', template)
                        st.rerun()
                    
                    if st.button("Multi-Cloud Risk", help="Medium/High risk across providers"):
                        template = "risk IN ('Medium', 'High') AND provider IN ('aws', 'azure', 'gcp')"
                        self.session_manager.set_session_value('filter_expression', template)
                        st.rerun()
                
                # Clear expression
                if st.button("🗑️ Clear Expression", help="Clear the filter expression"):
                    self.session_manager.set_session_value('filter_expression', '')
                    st.rerun()
            
            else:
                # Clear advanced expression when disabled
                self.session_manager.set_session_value('filter_expression', '')
        
        # Store advanced filter settings
        advanced_filter_settings = {
            'use_advanced_filters': use_advanced_filters if 'use_advanced_filters' in locals() else False,
            'filter_expression': self.session_manager.get_session_value('filter_expression', '') if 'use_advanced_filters' in locals() and use_advanced_filters else ''
        }
        
        # Filter presets
        st.sidebar.markdown("#### 📋 Filter Presets")
        
        preset_options = [
            "Custom",
            "High Risk Only",
            "New Resources",
            "Deletions Only",
            "Updates & Changes",
            "All Actions"
        ]
        
        selected_preset = st.sidebar.selectbox(
            "Quick Filter Presets",
            options=preset_options,
            index=0,
            help="Select a preset filter configuration for common use cases"
        )
        
        # Apply preset if selected
        if selected_preset != "Custom":
            preset_filters = self._get_preset_filters(selected_preset, enhanced_risk_result, enable_multi_cloud)
            if preset_filters:
                action_filter = preset_filters.get('action_filter', action_filter)
                risk_filter = preset_filters.get('risk_filter', risk_filter)
                if preset_filters.get('provider_filter') is not None:
                    provider_filter = preset_filters.get('provider_filter')
        
        # Save/Load custom filter configurations
        st.sidebar.markdown("#### 💾 Save/Load Filters")
        
        try:
            col1, col2 = st.sidebar.columns(2)
        except (ValueError, AttributeError):
            # Handle test environment where columns might not work properly
            class MockColumn:
                def __enter__(self):
                    return st.sidebar
                def __exit__(self, *args):
                    pass
            col1 = col2 = MockColumn()
        
        with col1:
            save_name = st.text_input(
                "Config Name",
                placeholder="my-filters",
                help="Enter a name to save current filter configuration"
            )
            
            if st.button("💾 Save", help="Save current filter configuration"):
                if save_name.strip():
                    # Update session state with current filters before saving
                    current_filters = {
                        'action_filter': action_filter,
                        'risk_filter': risk_filter,
                        'provider_filter': provider_filter if provider_filter is not None else [],
                        'filter_logic': filter_logic
                    }
                    self.session_manager.update_filter_state(current_filters)
                    self.session_manager.set_filter_logic(filter_logic)
                    
                    if self.session_manager.save_current_filter_configuration(save_name.strip()):
                        st.success(f"✅ Saved '{save_name}'")
                    else:
                        st.error("❌ Failed to save configuration")
                else:
                    st.error("Please enter a name")
        
        with col2:
            # Get saved configurations from session manager
            saved_configs = self.session_manager.get_saved_filter_configurations()
            
            if saved_configs:
                selected_config = st.selectbox(
                    "Load Config",
                    options=[""] + saved_configs,
                    help="Load a previously saved filter configuration"
                )
                
                if st.button("📂 Load", help="Load selected filter configuration"):
                    if selected_config:
                        if self.session_manager.restore_saved_filter_configuration(selected_config):
                            st.success(f"✅ Loaded '{selected_config}'")
                            st.rerun()
                        else:
                            st.error("❌ Failed to load configuration")
                    else:
                        st.error("Please select a configuration")
            else:
                st.info("No saved configurations")
        
        # Reset filters button
        if st.sidebar.button("🔄 Reset All Filters", help="Reset all filters to default values"):
            self.session_manager.reset_filters_to_default()
            self.session_manager.clear_search()
            self.session_manager.set_filter_logic('AND')
            self.session_manager.set_selected_preset('Custom')
            st.rerun()
        
        # Update session state with current filter values
        current_filters = {
            'action_filter': action_filter,
            'risk_filter': risk_filter,
            'provider_filter': provider_filter if provider_filter is not None else [],
        }
        self.session_manager.update_filter_state(current_filters)
        self.session_manager.set_filter_logic(filter_logic)
        
        return {
            'action_filter': action_filter,
            'risk_filter': risk_filter,
            'provider_filter': provider_filter,
            'filter_logic': filter_logic,
            'selected_preset': selected_preset,
            'save_name': save_name if 'save_name' in locals() else "",
            'advanced_filter_settings': advanced_filter_settings
        }
    
    def _get_preset_filters(self, preset_name: str, enhanced_risk_result=None, enable_multi_cloud=True) -> dict:
        """
        Get filter configuration for a given preset.
        
        Args:
            preset_name: Name of the preset
            enhanced_risk_result: Enhanced risk assessment result for provider options
            enable_multi_cloud: Whether multi-cloud features are enabled
            
        Returns:
            Dictionary containing filter configuration for the preset
        """
        presets = {
            "High Risk Only": {
                'action_filter': ['create', 'update', 'delete', 'replace'],
                'risk_filter': ['High'],
                'provider_filter': None
            },
            "New Resources": {
                'action_filter': ['create'],
                'risk_filter': ['Low', 'Medium', 'High'],
                'provider_filter': None
            },
            "Deletions Only": {
                'action_filter': ['delete'],
                'risk_filter': ['Low', 'Medium', 'High'],
                'provider_filter': None
            },
            "Updates & Changes": {
                'action_filter': ['update', 'replace'],
                'risk_filter': ['Low', 'Medium', 'High'],
                'provider_filter': None
            },
            "All Actions": {
                'action_filter': ['create', 'update', 'delete', 'replace'],
                'risk_filter': ['Low', 'Medium', 'High'],
                'provider_filter': None
            }
        }
        
        preset_config = presets.get(preset_name, {})
        
        # Set provider filter to all available providers if multi-cloud is enabled
        if preset_config and enhanced_risk_result and enable_multi_cloud:
            try:
                if isinstance(enhanced_risk_result, dict) and enhanced_risk_result.get('provider_risk_summary'):
                    available_providers = list(enhanced_risk_result['provider_risk_summary'].keys())
                    if available_providers:
                        preset_config['provider_filter'] = available_providers
            except:
                pass
        
        return preset_config
    
    def _validate_filter_expression(self, expression: str) -> dict:
        """
        Validate a filter expression for syntax and field names.
        
        Args:
            expression: Filter expression string to validate
            
        Returns:
            Dictionary with validation result and error message if invalid
        """
        if not expression or not expression.strip():
            return {'valid': True, 'parsed': '', 'error': ''}
        
        try:
            # Basic validation - check for balanced parentheses
            if expression.count('(') != expression.count(')'):
                return {'valid': False, 'error': 'Unbalanced parentheses', 'parsed': ''}
            
            # Check for valid field names
            valid_fields = ['action', 'risk', 'provider', 'type', 'name']
            valid_operators = ['=', '!=', 'IN', 'NOT IN', 'LIKE', 'NOT LIKE']
            valid_logic = ['AND', 'OR', 'NOT']
            
            # Simple parsing - this is a basic implementation
            # In a production system, you'd want a proper expression parser
            expression_upper = expression.upper()
            
            # Check for valid operators
            has_valid_operator = any(op in expression_upper for op in valid_operators)
            if not has_valid_operator and expression.strip():
                return {'valid': False, 'error': 'No valid operators found (=, !=, IN, LIKE)', 'parsed': ''}
            
            # Check for valid field names (basic check)
            has_valid_field = any(field in expression.lower() for field in valid_fields)
            if not has_valid_field and expression.strip():
                return {'valid': False, 'error': f'No valid field names found. Use: {", ".join(valid_fields)}', 'parsed': ''}
            
            # Basic syntax validation passed
            parsed_expression = self._parse_filter_expression(expression)
            
            return {
                'valid': True,
                'parsed': parsed_expression,
                'error': ''
            }
            
        except Exception as e:
            return {
                'valid': False,
                'error': f'Syntax error: {str(e)}',
                'parsed': ''
            }
    
    def _parse_filter_expression(self, expression: str) -> str:
        """
        Parse and format a filter expression for display.
        
        Args:
            expression: Filter expression to parse
            
        Returns:
            Formatted expression string
        """
        if not expression.strip():
            return ''
        
        # Simple formatting - add line breaks for readability
        formatted = expression.replace(' AND ', '\n  AND ')
        formatted = formatted.replace(' OR ', '\n  OR ')
        formatted = formatted.replace('(', '(\n    ')
        formatted = formatted.replace(')', '\n  )')
        
        return formatted.strip()
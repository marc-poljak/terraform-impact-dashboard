"""
Sidebar component for the Terraform Plan Impact Dashboard.

This component handles the sidebar title, controls, and basic functionality
extracted from the main app.py file.
"""

import streamlit as st
from ui.session_manager import SessionStateManager


class SidebarComponent:
    """Component for rendering the dashboard sidebar with controls and status."""
    
    def __init__(self):
        """Initialize the SidebarComponent."""
        self.session_manager = SessionStateManager()
    
    def render(self, enhanced_features_available: bool, enhanced_risk_result=None, enable_multi_cloud=True) -> dict:
        """
        Render the sidebar with title, controls, and status information.
        
        Args:
            enhanced_features_available (bool): Whether enhanced multi-cloud features are available
            enhanced_risk_result: Enhanced risk assessment result for provider filter options
            enable_multi_cloud (bool): Whether multi-cloud features are enabled
            
        Returns:
            dict: Dictionary containing the current state of sidebar controls
        """
        # Sidebar title and header
        st.sidebar.title("📊 Dashboard Controls")
        st.sidebar.markdown("---")
        
        # Show enhanced features status
        if enhanced_features_available:
            st.sidebar.success("🌟 Enhanced multi-cloud features available!")
        else:
            st.sidebar.warning("⚙️ Basic mode - Enhanced features unavailable")
            st.sidebar.info("To enable multi-cloud features, ensure all provider files are in place")
        
        # Debug toggle checkbox with tooltip
        show_debug = st.sidebar.checkbox(
            "🔍 Show Debug Information", 
            value=False,
            help="Enable to see detailed parsing information, plan structure analysis, and error diagnostics. Useful for troubleshooting issues with plan processing."
        )
        
        # Multi-cloud features toggle (only show if enhanced features are available)
        enable_multi_cloud_toggle = True
        if enhanced_features_available:
            enable_multi_cloud_toggle = st.sidebar.checkbox(
                "🌐 Enable Multi-Cloud Features", 
                value=True,
                help="Enable advanced multi-cloud analysis including cross-provider risk assessment, provider-specific insights, and multi-cloud visualizations. Requires enhanced features to be available."
            )
            if not enable_multi_cloud_toggle:
                st.sidebar.info("Multi-cloud features disabled - using basic mode")
        
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
        
        # Action filter with tooltip
        action_filter = st.sidebar.multiselect(
            "Filter by Action",
            options=['create', 'update', 'delete', 'replace'],
            default=['create', 'update', 'delete', 'replace'],
            help="Filter resources by Terraform action type:\n• Create: New resources being added\n• Update: Existing resources being modified\n• Delete: Resources being removed\n• Replace: Resources being destroyed and recreated"
        )
        
        # Risk filter with tooltip
        risk_filter = st.sidebar.multiselect(
            "Filter by Risk Level",
            options=['Low', 'Medium', 'High'],
            default=['Low', 'Medium', 'High'],
            help="Filter resources by calculated risk level:\n• Low: Safe changes with minimal impact\n• Medium: Changes requiring attention\n• High: Potentially dangerous changes requiring careful review"
        )
        
        # Provider filter (if multi-cloud enabled and data available)
        provider_filter = None
        if enhanced_features_available and enable_multi_cloud:
            try:
                if isinstance(enhanced_risk_result, dict) and enhanced_risk_result.get('provider_risk_summary'):
                    available_providers = list(enhanced_risk_result['provider_risk_summary'].keys())
                    if available_providers:
                        provider_filter = st.sidebar.multiselect(
                            "Filter by Provider",
                            options=available_providers,
                            default=available_providers,
                            help="Filter resources by cloud provider. Shows only providers detected in your Terraform plan. Useful for focusing on specific cloud environments in multi-cloud deployments."
                        )
            except:
                pass
        
        # Filter combination logic
        st.sidebar.markdown("#### 🔗 Filter Logic")
        filter_logic = st.sidebar.radio(
            "Combine filters using:",
            options=["AND", "OR"],
            index=0,
            help="AND: Show resources that match ALL selected filters\nOR: Show resources that match ANY selected filter",
            horizontal=True
        )
        
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
        
        col1, col2 = st.sidebar.columns(2)
        
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
        
        return {
            'action_filter': action_filter,
            'risk_filter': risk_filter,
            'provider_filter': provider_filter,
            'filter_logic': filter_logic,
            'selected_preset': selected_preset,
            'save_name': save_name if 'save_name' in locals() else ""
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
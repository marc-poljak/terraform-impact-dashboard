"""
Session State Manager

Manages Streamlit session state for the dashboard application.
Provides centralized session state initialization and management for components.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
import streamlit as st
import atexit


class SessionStateManager:
    """Manages session state for the dashboard application"""
    
    def __init__(self):
        """Initialize the session state manager"""
        self.initialize_session_state()
        
        # Register cleanup on session end
        atexit.register(self._cleanup_on_session_end)
    
    def initialize_session_state(self) -> None:
        """
        Initialize session state variables used across components.
        Preserves existing session state structure and behavior.
        """
        # Debug and feature toggles
        if not hasattr(st.session_state, 'show_debug'):
            st.session_state.show_debug = False
            
        if not hasattr(st.session_state, 'enable_multi_cloud'):
            st.session_state.enable_multi_cloud = True
            
        # Filter states - preserve existing multiselect default values
        if not hasattr(st.session_state, 'action_filter'):
            st.session_state.action_filter = ['create', 'update', 'delete', 'replace']
            
        if not hasattr(st.session_state, 'risk_filter'):
            st.session_state.risk_filter = ['Low', 'Medium', 'High']
            
        if not hasattr(st.session_state, 'provider_filter'):
            st.session_state.provider_filter = []
            
        # Search state
        if not hasattr(st.session_state, 'search_query'):
            st.session_state.search_query = ""
            
        if not hasattr(st.session_state, 'search_results_count'):
            st.session_state.search_results_count = 0
            
        if not hasattr(st.session_state, 'search_result_indices'):
            st.session_state.search_result_indices = []
            
        if not hasattr(st.session_state, 'current_search_result_index'):
            st.session_state.current_search_result_index = 0
            
        # Filter logic and presets
        if not hasattr(st.session_state, 'filter_logic'):
            st.session_state.filter_logic = 'AND'
            
        if not hasattr(st.session_state, 'selected_preset'):
            st.session_state.selected_preset = 'Custom'
            
        # Advanced filter settings
        if not hasattr(st.session_state, 'use_advanced_filters'):
            st.session_state.use_advanced_filters = False
            
        if not hasattr(st.session_state, 'filter_expression'):
            st.session_state.filter_expression = ''
            
        # Saved filter configurations
        if not hasattr(st.session_state, 'saved_filter_configs'):
            st.session_state.saved_filter_configs = {}
            
        # File processing state
        if not hasattr(st.session_state, 'uploaded_file_processed'):
            st.session_state.uploaded_file_processed = False
            
        if not hasattr(st.session_state, 'plan_data'):
            st.session_state.plan_data = None
            
        if not hasattr(st.session_state, 'parser'):
            st.session_state.parser = None
            
        # Processing results cache
        if not hasattr(st.session_state, 'summary'):
            st.session_state.summary = None
            
        if not hasattr(st.session_state, 'resource_changes'):
            st.session_state.resource_changes = None
            
        if not hasattr(st.session_state, 'resource_types'):
            st.session_state.resource_types = None
            
        if not hasattr(st.session_state, 'risk_summary'):
            st.session_state.risk_summary = None
            
        if not hasattr(st.session_state, 'enhanced_risk_result'):
            st.session_state.enhanced_risk_result = None
            
        if not hasattr(st.session_state, 'enhanced_risk_assessor'):
            st.session_state.enhanced_risk_assessor = None
    
    def get_filter_state(self) -> Dict[str, Any]:
        """
        Get current filter settings from session state.
        
        Returns:
            Dictionary containing current filter configurations
        """
        return {
            'action_filter': st.session_state.action_filter if hasattr(st.session_state, 'action_filter') else ['create', 'update', 'delete', 'replace'],
            'risk_filter': st.session_state.risk_filter if hasattr(st.session_state, 'risk_filter') else ['Low', 'Medium', 'High'],
            'provider_filter': st.session_state.provider_filter if hasattr(st.session_state, 'provider_filter') else []
        }
    
    def update_filter_state(self, filters: Dict[str, Any]) -> None:
        """
        Update filter settings in session state.
        
        Args:
            filters: Dictionary containing filter configurations to update
        """
        for key, value in filters.items():
            if key in ['action_filter', 'risk_filter', 'provider_filter']:
                st.session_state[key] = value
    
    def get_debug_state(self) -> bool:
        """
        Get debug mode state.
        
        Returns:
            Current debug mode setting
        """
        return st.session_state.show_debug if hasattr(st.session_state, 'show_debug') else False
    
    def set_debug_state(self, enabled: bool) -> None:
        """
        Set debug mode state.
        
        Args:
            enabled: Whether debug mode should be enabled
        """
        st.session_state.show_debug = enabled
    
    def get_multi_cloud_state(self) -> bool:
        """
        Get multi-cloud features state.
        
        Returns:
            Current multi-cloud features setting
        """
        return st.session_state.enable_multi_cloud if hasattr(st.session_state, 'enable_multi_cloud') else True
    
    def set_multi_cloud_state(self, enabled: bool) -> None:
        """
        Set multi-cloud features state.
        
        Args:
            enabled: Whether multi-cloud features should be enabled
        """
        st.session_state.enable_multi_cloud = enabled
    
    def get_processing_state(self) -> Dict[str, Any]:
        """
        Get current file processing state and cached results.
        
        Returns:
            Dictionary containing processing state and cached data
        """
        return {
            'uploaded_file_processed': st.session_state.get('uploaded_file_processed', False),
            'plan_data': st.session_state.get('plan_data'),
            'parser': st.session_state.get('parser'),
            'summary': st.session_state.get('summary'),
            'resource_changes': st.session_state.get('resource_changes'),
            'resource_types': st.session_state.get('resource_types'),
            'risk_summary': st.session_state.get('risk_summary'),
            'enhanced_risk_result': st.session_state.get('enhanced_risk_result'),
            'enhanced_risk_assessor': st.session_state.get('enhanced_risk_assessor')
        }
    
    def update_processing_state(self, processing_data: Dict[str, Any]) -> None:
        """
        Update file processing state and cache results.
        
        Args:
            processing_data: Dictionary containing processing results to cache
        """
        valid_keys = [
            'uploaded_file_processed', 'plan_data', 'parser', 'summary',
            'resource_changes', 'resource_types', 'risk_summary',
            'enhanced_risk_result', 'enhanced_risk_assessor'
        ]
        
        for key, value in processing_data.items():
            if key in valid_keys:
                st.session_state[key] = value
    
    def clear_processing_state(self) -> None:
        """Clear all cached processing data when a new file is uploaded."""
        processing_keys = [
            'uploaded_file_processed', 'plan_data', 'parser', 'summary',
            'resource_changes', 'resource_types', 'risk_summary',
            'enhanced_risk_result', 'enhanced_risk_assessor'
        ]
        
        for key in processing_keys:
            if key in st.session_state:
                del st.session_state[key]
    
    def get_session_value(self, key: str, default: Any = None) -> Any:
        """
        Get a value from session state with optional default.
        
        Args:
            key: Session state key
            default: Default value if key doesn't exist
            
        Returns:
            Value from session state or default
        """
        return getattr(st.session_state, key, default) if hasattr(st.session_state, key) else default
    
    def set_session_value(self, key: str, value: Any) -> None:
        """
        Set a value in session state.
        
        Args:
            key: Session state key
            value: Value to set
        """
        setattr(st.session_state, key, value)
    
    def has_session_key(self, key: str) -> bool:
        """
        Check if a key exists in session state.
        
        Args:
            key: Session state key to check
            
        Returns:
            True if key exists, False otherwise
        """
        return hasattr(st.session_state, key)
    
    def remove_session_key(self, key: str) -> None:
        """
        Remove a key from session state if it exists.
        
        Args:
            key: Session state key to remove
        """
        if hasattr(st.session_state, key):
            delattr(st.session_state, key)
    
    # Filter state persistence methods
    
    def save_filter_configuration(self, config_name: str) -> None:
        """
        Save current filter configuration with a name for later restoration.
        Maintains filter state across component interactions.
        
        Args:
            config_name: Name to save the configuration under
        """
        current_filters = self.get_filter_state()
        
        # Initialize saved configurations if not exists
        if 'saved_filter_configs' not in st.session_state:
            st.session_state.saved_filter_configs = {}
        
        st.session_state.saved_filter_configs[config_name] = current_filters.copy()
    
    def restore_filter_configuration(self, config_name: str) -> bool:
        """
        Restore a previously saved filter configuration.
        Preserves existing multiselect default values and behavior.
        
        Args:
            config_name: Name of the configuration to restore
            
        Returns:
            True if configuration was restored, False if not found
        """
        saved_configs = st.session_state.get('saved_filter_configs', {})
        
        if config_name in saved_configs:
            self.update_filter_state(saved_configs[config_name])
            return True
        return False
    
    def get_saved_filter_configurations(self) -> List[str]:
        """
        Get list of saved filter configuration names.
        
        Returns:
            List of saved configuration names
        """
        saved_configs = st.session_state.get('saved_filter_configs', {})
        return list(saved_configs.keys())
    
    def delete_filter_configuration(self, config_name: str) -> bool:
        """
        Delete a saved filter configuration.
        
        Args:
            config_name: Name of the configuration to delete
            
        Returns:
            True if configuration was deleted, False if not found
        """
        saved_configs = st.session_state.get('saved_filter_configs', {})
        
        if config_name in saved_configs:
            del saved_configs[config_name]
            st.session_state.saved_filter_configs = saved_configs
            return True
        return False
    
    def reset_filters_to_default(self) -> None:
        """
        Reset all filters to their default values.
        Preserves existing multiselect default values and behavior.
        """
        default_filters = {
            'action_filter': ['create', 'update', 'delete', 'replace'],
            'risk_filter': ['Low', 'Medium', 'High'],
            'provider_filter': []
        }
        self.update_filter_state(default_filters)
    
    def get_filter_summary(self) -> Dict[str, Any]:
        """
        Get a summary of current filter state for display purposes.
        
        Returns:
            Dictionary containing filter summary information
        """
        filters = self.get_filter_state()
        
        return {
            'total_action_filters': len(filters['action_filter']),
            'total_risk_filters': len(filters['risk_filter']),
            'total_provider_filters': len(filters['provider_filter']),
            'has_active_filters': (
                len(filters['action_filter']) < 4 or  # Less than all 4 actions
                len(filters['risk_filter']) < 3 or    # Less than all 3 risk levels
                len(filters['provider_filter']) > 0   # Any provider filters active
            ),
            'active_filters': filters
        }
    
    def update_provider_filter_options(self, available_providers: List[str]) -> None:
        """
        Update available provider filter options and maintain current selection.
        Maintains filter state across component interactions.
        
        Args:
            available_providers: List of currently available provider options
        """
        current_provider_filter = st.session_state.get('provider_filter', [])
        
        # Keep only providers that are still available
        updated_provider_filter = [
            provider for provider in current_provider_filter 
            if provider in available_providers
        ]
        
        # If no providers are selected and providers are available, select all by default
        if not updated_provider_filter and available_providers:
            updated_provider_filter = available_providers.copy()
        
        st.session_state.provider_filter = updated_provider_filter
    
    def is_filter_active(self, filter_type: str) -> bool:
        """
        Check if a specific filter type has active (non-default) filtering.
        
        Args:
            filter_type: Type of filter to check ('action', 'risk', 'provider')
            
        Returns:
            True if filter is actively filtering (not showing all options)
        """
        filters = self.get_filter_state()
        
        if filter_type == 'action':
            return len(filters['action_filter']) < 4  # Less than all 4 actions
        elif filter_type == 'risk':
            return len(filters['risk_filter']) < 3    # Less than all 3 risk levels
        elif filter_type == 'provider':
            return len(filters['provider_filter']) > 0  # Any provider filters active
        
        return False
    
    # Search functionality methods
    
    def get_search_query(self) -> str:
        """
        Get current search query from session state.
        
        Returns:
            Current search query string
        """
        return st.session_state.get('search_query', "")
    
    def set_search_query(self, query: str) -> None:
        """
        Set search query in session state.
        
        Args:
            query: Search query string
        """
        st.session_state.search_query = query
    
    def get_search_results_count(self) -> int:
        """
        Get current search results count from session state.
        
        Returns:
            Number of search results
        """
        return st.session_state.get('search_results_count', 0)
    
    def set_search_results_count(self, count: int) -> None:
        """
        Set search results count in session state.
        
        Args:
            count: Number of search results
        """
        st.session_state.search_results_count = count
    
    def clear_search(self) -> None:
        """
        Clear search query and results count.
        """
        st.session_state.search_query = ""
        st.session_state.search_results_count = 0
        st.session_state.search_result_indices = []
        st.session_state.current_search_result_index = 0
    
    def is_search_active(self) -> bool:
        """
        Check if search is currently active (has a query).
        
        Returns:
            True if search query is not empty
        """
        return bool(st.session_state.get('search_query', "").strip())
    
    def get_search_result_indices(self) -> List[int]:
        """
        Get list of search result indices from session state.
        
        Returns:
            List of dataframe indices that match the search
        """
        return st.session_state.get('search_result_indices', [])
    
    def set_search_result_indices(self, indices: List[int]) -> None:
        """
        Set search result indices in session state.
        
        Args:
            indices: List of dataframe indices that match the search
        """
        st.session_state.search_result_indices = indices
        # Reset current index when new search results are set
        st.session_state.current_search_result_index = 0
    
    def get_current_search_result_index(self) -> int:
        """
        Get current search result index for navigation.
        
        Returns:
            Current search result index (0-based)
        """
        return st.session_state.get('current_search_result_index', 0)
    
    def set_current_search_result_index(self, index: int) -> None:
        """
        Set current search result index for navigation.
        
        Args:
            index: Search result index to navigate to (0-based)
        """
        indices = self.get_search_result_indices()
        if indices and 0 <= index < len(indices):
            st.session_state.current_search_result_index = index
    
    def navigate_search_results(self, direction: str) -> bool:
        """
        Navigate to next or previous search result.
        
        Args:
            direction: 'next' or 'previous'
            
        Returns:
            True if navigation was successful, False if at boundary
        """
        indices = self.get_search_result_indices()
        if not indices:
            return False
        
        current_index = self.get_current_search_result_index()
        
        if direction == 'next':
            if current_index < len(indices) - 1:
                self.set_current_search_result_index(current_index + 1)
                return True
        elif direction == 'previous':
            if current_index > 0:
                self.set_current_search_result_index(current_index - 1)
                return True
        
        return False
    
    def get_current_search_result_info(self) -> Dict[str, Any]:
        """
        Get information about current search result position.
        
        Returns:
            Dictionary with current position and total count
        """
        indices = self.get_search_result_indices()
        current_index = self.get_current_search_result_index()
        
        return {
            'current_position': current_index + 1 if indices else 0,
            'total_results': len(indices),
            'has_results': len(indices) > 0,
            'can_go_previous': current_index > 0,
            'can_go_next': current_index < len(indices) - 1 if indices else False
        }
    
    # Filter logic and preset methods
    
    def get_filter_logic(self) -> str:
        """
        Get current filter logic (AND/OR) from session state.
        
        Returns:
            Current filter logic ('AND' or 'OR')
        """
        return st.session_state.get('filter_logic', 'AND')
    
    def set_filter_logic(self, logic: str) -> None:
        """
        Set filter logic in session state.
        
        Args:
            logic: Filter logic ('AND' or 'OR')
        """
        if logic in ['AND', 'OR']:
            st.session_state.filter_logic = logic
    
    def get_selected_preset(self) -> str:
        """
        Get currently selected filter preset from session state.
        
        Returns:
            Current preset name
        """
        return st.session_state.get('selected_preset', 'Custom')
    
    def set_selected_preset(self, preset: str) -> None:
        """
        Set selected filter preset in session state.
        
        Args:
            preset: Preset name
        """
        st.session_state.selected_preset = preset
    
    def apply_filter_preset(self, preset_name: str, enhanced_risk_result=None, enable_multi_cloud=True) -> bool:
        """
        Apply a filter preset configuration.
        
        Args:
            preset_name: Name of the preset to apply
            enhanced_risk_result: Enhanced risk assessment result for provider options
            enable_multi_cloud: Whether multi-cloud features are enabled
            
        Returns:
            True if preset was applied successfully
        """
        presets = {
            "High Risk Only": {
                'action_filter': ['create', 'update', 'delete', 'replace'],
                'risk_filter': ['High'],
                'provider_filter': []
            },
            "New Resources": {
                'action_filter': ['create'],
                'risk_filter': ['Low', 'Medium', 'High'],
                'provider_filter': []
            },
            "Deletions Only": {
                'action_filter': ['delete'],
                'risk_filter': ['Low', 'Medium', 'High'],
                'provider_filter': []
            },
            "Updates & Changes": {
                'action_filter': ['update', 'replace'],
                'risk_filter': ['Low', 'Medium', 'High'],
                'provider_filter': []
            },
            "All Actions": {
                'action_filter': ['create', 'update', 'delete', 'replace'],
                'risk_filter': ['Low', 'Medium', 'High'],
                'provider_filter': []
            }
        }
        
        if preset_name not in presets:
            return False
        
        preset_config = presets[preset_name].copy()
        
        # Set provider filter to all available providers if multi-cloud is enabled
        if enhanced_risk_result and enable_multi_cloud:
            try:
                if isinstance(enhanced_risk_result, dict) and enhanced_risk_result.get('provider_risk_summary'):
                    available_providers = list(enhanced_risk_result['provider_risk_summary'].keys())
                    if available_providers:
                        preset_config['provider_filter'] = available_providers
            except:
                pass
        
        # Apply the preset configuration
        self.update_filter_state(preset_config)
        self.set_selected_preset(preset_name)
        
        return True
    
    def save_current_filter_configuration(self, config_name: str) -> bool:
        """
        Save current filter configuration including logic and search.
        
        Args:
            config_name: Name to save the configuration under
            
        Returns:
            True if saved successfully
        """
        if not config_name.strip():
            return False
        
        current_config = {
            **self.get_filter_state(),
            'filter_logic': self.get_filter_logic(),
            'search_query': self.get_search_query(),
            **self.get_advanced_filter_settings()
        }
        
        # Initialize saved configurations if not exists
        if 'saved_filter_configs' not in st.session_state:
            st.session_state.saved_filter_configs = {}
        
        st.session_state.saved_filter_configs[config_name] = current_config
        return True
    
    def restore_saved_filter_configuration(self, config_name: str) -> bool:
        """
        Restore a saved filter configuration including logic and search.
        
        Args:
            config_name: Name of the configuration to restore
            
        Returns:
            True if restored successfully
        """
        saved_configs = st.session_state.get('saved_filter_configs', {})
        
        if config_name not in saved_configs:
            return False
        
        config = saved_configs[config_name]
        
        # Restore filter state
        filter_state = {
            'action_filter': config.get('action_filter', ['create', 'update', 'delete', 'replace']),
            'risk_filter': config.get('risk_filter', ['Low', 'Medium', 'High']),
            'provider_filter': config.get('provider_filter', [])
        }
        self.update_filter_state(filter_state)
        
        # Restore filter logic
        if 'filter_logic' in config:
            self.set_filter_logic(config['filter_logic'])
        
        # Restore search query
        if 'search_query' in config:
            self.set_search_query(config['search_query'])
        
        # Restore advanced filter settings
        advanced_settings = {
            'use_advanced_filters': config.get('use_advanced_filters', False),
            'filter_expression': config.get('filter_expression', '')
        }
        self.set_advanced_filter_settings(advanced_settings)
        
        # Set preset to custom since we're loading a saved config
        self.set_selected_preset('Custom')
        
        return True
    
    def _cleanup_on_session_end(self) -> None:
        """Cleanup sensitive data when session ends."""
        try:
            # Import here to avoid circular imports
            from utils.credential_manager import CredentialManager
            
            # Cleanup all credential manager instances
            CredentialManager.cleanup_all_instances()
            
            # Clear sensitive session state
            sensitive_keys = [
                'plan_data', 'parser', 'enhanced_risk_result', 
                'enhanced_risk_assessor', 'generated_report'
            ]
            
            for key in sensitive_keys:
                if hasattr(st.session_state, key):
                    delattr(st.session_state, key)
                    
        except Exception:
            # Ignore errors during cleanup to prevent application crashes
            pass
    
    def trigger_security_cleanup(self) -> None:
        """Manually trigger security cleanup of sensitive data."""
        self._cleanup_on_session_end()
    
    def get_advanced_filter_settings(self) -> Dict[str, Any]:
        """
        Get advanced filter settings from session state.
        
        Returns:
            Dictionary containing advanced filter settings
        """
        return {
            'use_advanced_filters': st.session_state.get('use_advanced_filters', False),
            'filter_expression': st.session_state.get('filter_expression', '')
        }
    
    def set_advanced_filter_settings(self, settings: Dict[str, Any]) -> None:
        """
        Set advanced filter settings in session state.
        
        Args:
            settings: Dictionary containing advanced filter settings
        """
        if 'use_advanced_filters' in settings:
            st.session_state.use_advanced_filters = settings['use_advanced_filters']
        
        if 'filter_expression' in settings:
            st.session_state.filter_expression = settings['filter_expression']
    
    def clear_advanced_filters(self) -> None:
        """
        Clear advanced filter settings.
        """
        st.session_state.use_advanced_filters = False
        st.session_state.filter_expression = ''
    
    def get_filter_configuration_summary(self) -> Dict[str, Any]:
        """
        Get a comprehensive summary of current filter configuration.
        
        Returns:
            Dictionary containing complete filter configuration summary
        """
        base_summary = self.get_filter_summary()
        
        return {
            **base_summary,
            'filter_logic': self.get_filter_logic(),
            'selected_preset': self.get_selected_preset(),
            'search_active': self.is_search_active(),
            'search_query': self.get_search_query(),
            'search_results_count': self.get_search_results_count(),
            'saved_configs_count': len(self.get_saved_filter_configurations()),
            **self.get_advanced_filter_settings()
        }   
 
    # Report generation methods
    
    def get_generated_report(self) -> Optional[Dict[str, str]]:
        """
        Get previously generated report from session state.
        
        Returns:
            Dictionary containing report sections or None if no report exists
        """
        return st.session_state.get('generated_report', None)
    
    def set_generated_report(self, report_data: Dict[str, str]) -> None:
        """
        Store generated report in session state.
        
        Args:
            report_data: Dictionary containing report sections
        """
        st.session_state.generated_report = report_data
        st.session_state.report_generated_at = datetime.now().isoformat()
    
    def clear_generated_report(self) -> None:
        """Clear stored report from session state."""
        if 'generated_report' in st.session_state:
            del st.session_state['generated_report']
        if 'report_generated_at' in st.session_state:
            del st.session_state['report_generated_at']
    
    def has_generated_report(self) -> bool:
        """
        Check if a report has been generated and stored.
        
        Returns:
            True if a report exists in session state
        """
        return 'generated_report' in st.session_state and st.session_state.generated_report is not None
    
    def get_report_generation_time(self) -> Optional[str]:
        """
        Get the timestamp when the current report was generated.
        
        Returns:
            ISO format timestamp string or None if no report exists
        """
        return st.session_state.get('report_generated_at', None)
"""
Unit tests for SessionStateManager

Tests the session state manager functionality.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))


class TestSessionStateManager:
    """Test cases for SessionStateManager"""
    
    def setup_method(self):
        """Set up test fixtures before each test method"""
        # Create a mock session state that supports both dict and attribute access
        class MockSessionState(dict):
            def __getattr__(self, name):
                try:
                    return self[name]
                except KeyError:
                    raise AttributeError(f"'MockSessionState' object has no attribute '{name}'")
            
            def __setattr__(self, name, value):
                self[name] = value
            
            def __delattr__(self, name):
                try:
                    del self[name]
                except KeyError:
                    raise AttributeError(f"'MockSessionState' object has no attribute '{name}'")
        
        self.mock_session_state = MockSessionState()
        
        with patch('streamlit.session_state', self.mock_session_state):
            from ui.session_manager import SessionStateManager
            self.session_manager = SessionStateManager()
    
    def test_component_creation(self):
        """Test that SessionStateManager can be created successfully"""
        assert self.session_manager is not None
        from ui.session_manager import SessionStateManager
        assert isinstance(self.session_manager, SessionStateManager)
    
    def test_initialize_session_state(self):
        """Test that session state is initialized with default values"""
        # Session state should be initialized during __init__
        expected_keys = [
            'show_debug', 'enable_multi_cloud', 'action_filter', 'risk_filter',
            'provider_filter', 'search_query', 'search_results_count',
            'filter_logic', 'selected_preset'
        ]
        
        for key in expected_keys:
            assert key in self.mock_session_state, f"Missing session state key: {key}"
    
    def test_get_filter_state(self):
        """Test get_filter_state method"""
        # Set some test values after initialization
        with patch('streamlit.session_state', self.mock_session_state):
            self.mock_session_state['action_filter'] = ['create', 'update']
            self.mock_session_state['risk_filter'] = ['High']
            self.mock_session_state['provider_filter'] = ['aws']
            
            result = self.session_manager.get_filter_state()
            
            assert isinstance(result, dict)
            assert result['action_filter'] == ['create', 'update']
            assert result['risk_filter'] == ['High']
            assert result['provider_filter'] == ['aws']
    
    def test_update_filter_state(self):
        """Test update_filter_state method"""
        with patch('streamlit.session_state', self.mock_session_state):
            new_filters = {
                'action_filter': ['delete'],
                'risk_filter': ['Low', 'Medium'],
                'provider_filter': ['azure', 'gcp']
            }
            
            self.session_manager.update_filter_state(new_filters)
            
            assert self.mock_session_state['action_filter'] == ['delete']
            assert self.mock_session_state['risk_filter'] == ['Low', 'Medium']
            assert self.mock_session_state['provider_filter'] == ['azure', 'gcp']
    
    def test_get_debug_state(self):
        """Test get_debug_state method"""
        with patch('streamlit.session_state', self.mock_session_state):
            # Test default value
            result = self.session_manager.get_debug_state()
            assert result == False
            
            # Test with set value
            self.mock_session_state['show_debug'] = True
            result = self.session_manager.get_debug_state()
            assert result == True
    
    def test_set_debug_state(self):
        """Test set_debug_state method"""
        with patch('streamlit.session_state', self.mock_session_state):
            self.session_manager.set_debug_state(True)
            assert self.mock_session_state['show_debug'] == True
            
            self.session_manager.set_debug_state(False)
            assert self.mock_session_state['show_debug'] == False
    
    def test_get_multi_cloud_state(self):
        """Test get_multi_cloud_state method"""
        with patch('streamlit.session_state', self.mock_session_state):
            # Test default value
            result = self.session_manager.get_multi_cloud_state()
            assert result == True
            
            # Test with set value
            self.mock_session_state['enable_multi_cloud'] = False
            result = self.session_manager.get_multi_cloud_state()
            assert result == False
    
    def test_set_multi_cloud_state(self):
        """Test set_multi_cloud_state method"""
        with patch('streamlit.session_state', self.mock_session_state):
            self.session_manager.set_multi_cloud_state(False)
            assert self.mock_session_state['enable_multi_cloud'] == False
            
            self.session_manager.set_multi_cloud_state(True)
            assert self.mock_session_state['enable_multi_cloud'] == True
    
    def test_get_session_value(self):
        """Test get_session_value method"""
        with patch('streamlit.session_state', self.mock_session_state):
            # Test with existing key
            self.mock_session_state['test_key'] = 'test_value'
            result = self.session_manager.get_session_value('test_key')
            assert result == 'test_value'
            
            # Test with non-existing key and default
            result = self.session_manager.get_session_value('non_existing', 'default')
            assert result == 'default'
            
            # Test with non-existing key and no default
            result = self.session_manager.get_session_value('non_existing')
            assert result is None
    
    def test_set_session_value(self):
        """Test set_session_value method"""
        with patch('streamlit.session_state', self.mock_session_state):
            self.session_manager.set_session_value('test_key', 'test_value')
            assert self.mock_session_state['test_key'] == 'test_value'
    
    def test_has_session_key(self):
        """Test has_session_key method"""
        with patch('streamlit.session_state', self.mock_session_state):
            # Test with existing key
            self.mock_session_state['existing_key'] = 'value'
            assert self.session_manager.has_session_key('existing_key') == True
            
            # Test with non-existing key
            assert self.session_manager.has_session_key('non_existing_key') == False
    
    def test_remove_session_key(self):
        """Test remove_session_key method"""
        with patch('streamlit.session_state', self.mock_session_state):
            # Add a key
            self.mock_session_state['key_to_remove'] = 'value'
            assert 'key_to_remove' in self.mock_session_state
            
            # Remove the key
            self.session_manager.remove_session_key('key_to_remove')
            assert 'key_to_remove' not in self.mock_session_state
            
            # Test removing non-existing key (should not raise error)
            self.session_manager.remove_session_key('non_existing_key')
    
    def test_reset_filters_to_default(self):
        """Test reset_filters_to_default method"""
        with patch('streamlit.session_state', self.mock_session_state):
            # Set some non-default values
            self.mock_session_state['action_filter'] = ['create']
            self.mock_session_state['risk_filter'] = ['High']
            self.mock_session_state['provider_filter'] = ['aws']
            
            # Reset to defaults
            self.session_manager.reset_filters_to_default()
            
            # Verify defaults are restored
            assert self.mock_session_state['action_filter'] == ['create', 'update', 'delete', 'replace']
            assert self.mock_session_state['risk_filter'] == ['Low', 'Medium', 'High']
            assert self.mock_session_state['provider_filter'] == []
    
    def test_get_filter_summary(self):
        """Test get_filter_summary method"""
        with patch('streamlit.session_state', self.mock_session_state):
            # Set some filter values
            self.mock_session_state['action_filter'] = ['create', 'update']
            self.mock_session_state['risk_filter'] = ['High']
            self.mock_session_state['provider_filter'] = ['aws']
            
            result = self.session_manager.get_filter_summary()
            
            assert isinstance(result, dict)
            assert result['total_action_filters'] == 2
            assert result['total_risk_filters'] == 1
            assert result['total_provider_filters'] == 1
            assert result['has_active_filters'] == True
    
    def test_is_filter_active(self):
        """Test is_filter_active method"""
        with patch('streamlit.session_state', self.mock_session_state):
            # Test with default filters (should not be active)
            assert self.session_manager.is_filter_active('action') == False
            assert self.session_manager.is_filter_active('risk') == False
            assert self.session_manager.is_filter_active('provider') == False
            
            # Set some active filters
            self.mock_session_state['action_filter'] = ['create']  # Less than 4
            self.mock_session_state['risk_filter'] = ['High']      # Less than 3
            self.mock_session_state['provider_filter'] = ['aws']   # More than 0
            
            assert self.session_manager.is_filter_active('action') == True
            assert self.session_manager.is_filter_active('risk') == True
            assert self.session_manager.is_filter_active('provider') == True
    
    def test_search_functionality(self):
        """Test search-related methods"""
        # Test initial search state
        assert self.session_manager.get_search_query() == ""
        assert self.session_manager.get_search_results_count() == 0
        assert self.session_manager.is_search_active() == False
        
        # Set search query
        self.session_manager.set_search_query("test query")
        assert self.session_manager.get_search_query() == "test query"
        assert self.session_manager.is_search_active() == True
        
        # Set search results count
        self.session_manager.set_search_results_count(5)
        assert self.session_manager.get_search_results_count() == 5
        
        # Clear search
        self.session_manager.clear_search()
        assert self.session_manager.get_search_query() == ""
        assert self.session_manager.get_search_results_count() == 0
        assert self.session_manager.is_search_active() == False
    
    def test_filter_logic_methods(self):
        """Test filter logic methods"""
        # Test default filter logic
        assert self.session_manager.get_filter_logic() == 'AND'
        
        # Set filter logic
        self.session_manager.set_filter_logic('OR')
        assert self.session_manager.get_filter_logic() == 'OR'
        
        # Test invalid filter logic (should not change)
        self.session_manager.set_filter_logic('INVALID')
        assert self.session_manager.get_filter_logic() == 'OR'  # Should remain unchanged
    
    def test_preset_methods(self):
        """Test preset-related methods"""
        # Test default preset
        assert self.session_manager.get_selected_preset() == 'Custom'
        
        # Set preset
        self.session_manager.set_selected_preset('High Risk Only')
        assert self.session_manager.get_selected_preset() == 'High Risk Only'
    
    def test_processing_state_methods(self):
        """Test processing state methods"""
        # Test initial processing state
        state = self.session_manager.get_processing_state()
        assert isinstance(state, dict)
        assert state['uploaded_file_processed'] == False
        assert state['plan_data'] is None
        
        # Update processing state
        new_state = {
            'uploaded_file_processed': True,
            'plan_data': {'test': 'data'},
            'summary': {'changes': 5}
        }
        self.session_manager.update_processing_state(new_state)
        
        updated_state = self.session_manager.get_processing_state()
        assert updated_state['uploaded_file_processed'] == True
        assert updated_state['plan_data'] == {'test': 'data'}
        assert updated_state['summary'] == {'changes': 5}
        
        # Clear processing state
        self.session_manager.clear_processing_state()
        cleared_state = self.session_manager.get_processing_state()
        assert cleared_state['uploaded_file_processed'] == False
        assert cleared_state['plan_data'] is None
    
    def test_saved_filter_configurations(self):
        """Test saved filter configuration methods"""
        with patch('streamlit.session_state', self.mock_session_state):
            # Test initial state
            configs = self.session_manager.get_saved_filter_configurations()
            assert isinstance(configs, list)
            assert len(configs) == 0
            
            # Save a configuration
            self.mock_session_state['action_filter'] = ['create']
            success = self.session_manager.save_current_filter_configuration('test_config')
            assert success == True
            
            # Verify configuration was saved
            configs = self.session_manager.get_saved_filter_configurations()
            assert 'test_config' in configs
            
            # Restore configuration
            self.mock_session_state['action_filter'] = ['delete']  # Change current state
            success = self.session_manager.restore_saved_filter_configuration('test_config')
            assert success == True
            assert self.mock_session_state['action_filter'] == ['create']  # Should be restored
            
            # Test restoring non-existing configuration
            success = self.session_manager.restore_saved_filter_configuration('non_existing')
            assert success == False
    
    def test_advanced_filter_settings(self):
        """Test advanced filter settings methods"""
        # Test initial settings
        settings = self.session_manager.get_advanced_filter_settings()
        assert settings['use_advanced_filters'] == False
        assert settings['filter_expression'] == ''
        
        # Set advanced settings
        new_settings = {
            'use_advanced_filters': True,
            'filter_expression': "action='create'"
        }
        self.session_manager.set_advanced_filter_settings(new_settings)
        
        updated_settings = self.session_manager.get_advanced_filter_settings()
        assert updated_settings['use_advanced_filters'] == True
        assert updated_settings['filter_expression'] == "action='create'"
        
        # Clear advanced filters
        self.session_manager.clear_advanced_filters()
        cleared_settings = self.session_manager.get_advanced_filter_settings()
        assert cleared_settings['use_advanced_filters'] == False
        assert cleared_settings['filter_expression'] == ''


if __name__ == '__main__':
    pytest.main([__file__])
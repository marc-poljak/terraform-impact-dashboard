"""
Unit tests for SidebarComponent

Tests the sidebar component creation and basic functionality.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))


class TestSidebarComponent:
    """Test cases for SidebarComponent"""
    
    def setup_method(self):
        """Set up test fixtures before each test method"""
        # Mock the SessionStateManager to avoid Streamlit dependencies
        with patch('components.sidebar.SessionStateManager') as mock_session_manager:
            mock_session_manager.return_value = Mock()
            from components.sidebar import SidebarComponent
            self.sidebar_component = SidebarComponent()
    
    def test_component_creation(self):
        """Test that SidebarComponent can be created successfully"""
        assert self.sidebar_component is not None
        from components.sidebar import SidebarComponent
        assert isinstance(self.sidebar_component, SidebarComponent)
    
    @patch('streamlit.sidebar')
    @patch('components.sidebar.ErrorHandler')
    def test_render_method_exists(self, mock_error_handler, mock_sidebar):
        """Test that render method exists and can be called"""
        # Mock the error handler
        mock_error_handler.return_value = Mock()
        
        # Mock sidebar components
        mock_sidebar.title = Mock()
        mock_sidebar.markdown = Mock()
        mock_sidebar.success = Mock()
        mock_sidebar.info = Mock()
        mock_sidebar.checkbox = Mock(return_value=False)
        mock_sidebar.button = Mock(return_value=False)
        mock_sidebar.expander = Mock()
        
        # Test that render method exists
        assert hasattr(self.sidebar_component, 'render')
        assert callable(getattr(self.sidebar_component, 'render'))
        
        # Test that render method can be called without errors
        result = self.sidebar_component.render(enhanced_features_available=True)
        
        # Verify it returns a dictionary
        assert isinstance(result, dict)
        assert 'show_debug' in result
        assert 'enable_multi_cloud' in result
    
    @patch('streamlit.sidebar')
    @patch('components.sidebar.ErrorHandler')
    def test_render_with_enhanced_features_available(self, mock_error_handler, mock_sidebar):
        """Test render method when enhanced features are available"""
        # Mock the error handler
        mock_error_handler.return_value = Mock()
        
        # Mock sidebar components
        mock_sidebar.title = Mock()
        mock_sidebar.markdown = Mock()
        mock_sidebar.success = Mock()
        mock_sidebar.checkbox = Mock(side_effect=[False, True])  # debug=False, multi_cloud=True
        mock_sidebar.button = Mock(return_value=False)
        mock_sidebar.expander = Mock()
        
        result = self.sidebar_component.render(enhanced_features_available=True)
        
        # Verify enhanced features success message is shown
        # The component shows the initial message and then the multi-cloud enabled message
        success_calls = [call[0][0] for call in mock_sidebar.success.call_args_list]
        assert "✅ Enhanced Multi-Cloud Features Available" in success_calls
        
        # Verify result contains expected keys
        assert result['show_debug'] == False
        assert result['enable_multi_cloud'] == True
    
    @patch('streamlit.sidebar')
    @patch('components.sidebar.ErrorHandler')
    def test_render_with_enhanced_features_unavailable(self, mock_error_handler, mock_sidebar):
        """Test render method when enhanced features are unavailable"""
        # Mock the error handler
        mock_error_handler.return_value = Mock()
        
        # Mock sidebar components
        mock_sidebar.title = Mock()
        mock_sidebar.markdown = Mock()
        mock_sidebar.info = Mock()
        mock_sidebar.checkbox = Mock(return_value=False)
        mock_sidebar.button = Mock(return_value=False)
        # Mock expander to support context manager protocol
        mock_expander = Mock()
        mock_expander.__enter__ = Mock(return_value=mock_expander)
        mock_expander.__exit__ = Mock(return_value=None)
        mock_sidebar.expander = Mock(return_value=mock_expander)
        
        result = self.sidebar_component.render(enhanced_features_available=False)
        
        # Verify basic features info message is shown
        # The component shows the initial message and then the multi-cloud unavailable message
        info_calls = [call[0][0] for call in mock_sidebar.info.call_args_list]
        assert "ℹ️ Basic Features Available" in info_calls
        
        # Verify result contains expected keys
        assert 'show_debug' in result
        assert 'enable_multi_cloud' in result
    
    @patch('streamlit.sidebar')
    @patch('components.sidebar.ErrorHandler')
    def test_render_filters_method_exists(self, mock_error_handler, mock_sidebar):
        """Test that render_filters method exists and can be called"""
        # Mock the error handler
        mock_error_handler.return_value = Mock()
        
        # Mock sidebar components
        mock_sidebar.markdown = Mock()
        mock_sidebar.multiselect = Mock(side_effect=[
            ['create', 'update'],  # action_filter
            ['High'],              # risk_filter
        ])
        mock_sidebar.radio = Mock(return_value='AND')
        mock_sidebar.selectbox = Mock(return_value='Custom')
        mock_sidebar.text_input = Mock(return_value='')
        # Mock columns to support context manager protocol
        mock_col1 = Mock()
        mock_col1.__enter__ = Mock(return_value=mock_col1)
        mock_col1.__exit__ = Mock(return_value=None)
        mock_col2 = Mock()
        mock_col2.__enter__ = Mock(return_value=mock_col2)
        mock_col2.__exit__ = Mock(return_value=None)
        mock_sidebar.columns = Mock(return_value=[mock_col1, mock_col2])
        mock_sidebar.button = Mock(return_value=False)
        # Mock expander to support context manager protocol
        mock_expander = Mock()
        mock_expander.__enter__ = Mock(return_value=mock_expander)
        mock_expander.__exit__ = Mock(return_value=None)
        mock_sidebar.expander = Mock(return_value=mock_expander)
        # Mock additional components needed for advanced filters
        mock_sidebar.checkbox = Mock(return_value=False)
        mock_sidebar.text_area = Mock(return_value='')
        mock_sidebar.selectbox = Mock(return_value='Custom')
        
        # Mock session manager methods that return lists
        self.sidebar_component.session_manager.get_saved_filter_configurations = Mock(return_value=[])
        
        # Test that render_filters method exists
        assert hasattr(self.sidebar_component, 'render_filters')
        assert callable(getattr(self.sidebar_component, 'render_filters'))
        
        # Test that render_filters method can be called without errors
        result = self.sidebar_component.render_filters(enhanced_features_available=True)
        
        # Verify it returns a dictionary with filter settings
        assert isinstance(result, dict)
        assert 'action_filter' in result
        assert 'risk_filter' in result
        assert 'provider_filter' in result
        assert 'filter_logic' in result
    
    @patch('streamlit.sidebar')
    @patch('components.sidebar.ErrorHandler')
    def test_render_filters_with_mock_data(self, mock_error_handler, mock_sidebar):
        """Test render_filters with mock enhanced risk result data"""
        # Mock the error handler
        mock_error_handler.return_value = Mock()
        
        # Mock sidebar components
        mock_sidebar.markdown = Mock()
        mock_sidebar.multiselect = Mock(side_effect=[
            ['create', 'update', 'delete'],  # action_filter
            ['Low', 'Medium', 'High'],       # risk_filter
            ['aws', 'azure']                 # provider_filter
        ])
        mock_sidebar.radio = Mock(return_value='AND')
        mock_sidebar.selectbox = Mock(return_value='Custom')
        mock_sidebar.text_input = Mock(return_value='')
        # Mock columns to support context manager protocol
        mock_col1 = Mock()
        mock_col1.__enter__ = Mock(return_value=mock_col1)
        mock_col1.__exit__ = Mock(return_value=None)
        mock_col2 = Mock()
        mock_col2.__enter__ = Mock(return_value=mock_col2)
        mock_col2.__exit__ = Mock(return_value=None)
        mock_sidebar.columns = Mock(return_value=[mock_col1, mock_col2])
        mock_sidebar.button = Mock(return_value=False)
        # Mock expander to support context manager protocol
        mock_expander = Mock()
        mock_expander.__enter__ = Mock(return_value=mock_expander)
        mock_expander.__exit__ = Mock(return_value=None)
        mock_sidebar.expander = Mock(return_value=mock_expander)
        # Mock additional components needed for advanced filters
        mock_sidebar.checkbox = Mock(return_value=False)
        mock_sidebar.text_area = Mock(return_value='')
        
        # Mock session manager methods that return lists
        self.sidebar_component.session_manager.get_saved_filter_configurations = Mock(return_value=[])
        self.sidebar_component.session_manager.get_filter_state = Mock(return_value={
            'action_filter': ['create', 'update', 'delete'],
            'risk_filter': ['Low', 'Medium', 'High'],
            'provider_filter': ['aws', 'azure']
        })
        self.sidebar_component.session_manager.get_filter_logic = Mock(return_value='AND')
        self.sidebar_component.session_manager.update_filter_state = Mock()
        self.sidebar_component.session_manager.set_filter_logic = Mock()
        self.sidebar_component.session_manager.get_session_value = Mock(return_value='')
        self.sidebar_component.session_manager.set_session_value = Mock()
        
        # Mock enhanced risk result with provider data
        enhanced_risk_result = {
            'provider_risk_summary': {
                'aws': {'high_risk_count': 5},
                'azure': {'high_risk_count': 2}
            }
        }
        
        result = self.sidebar_component.render_filters(
            enhanced_features_available=True,
            enhanced_risk_result=enhanced_risk_result,
            enable_multi_cloud=True
        )
        
        # Verify provider filter is included when enhanced features are available
        assert result['provider_filter'] == ['aws', 'azure']
        assert result['action_filter'] == ['create', 'update', 'delete']
        assert result['risk_filter'] == ['Low', 'Medium', 'High']
        assert result['filter_logic'] == 'AND'
    
    def test_get_preset_filters_method(self):
        """Test the _get_preset_filters private method"""
        # Test that the method exists
        assert hasattr(self.sidebar_component, '_get_preset_filters')
        
        # Test with a known preset
        preset_config = self.sidebar_component._get_preset_filters("High Risk Only")
        
        assert isinstance(preset_config, dict)
        assert preset_config['action_filter'] == ['create', 'update', 'delete', 'replace']
        assert preset_config['risk_filter'] == ['High']
        assert preset_config['provider_filter'] is None
    
    def test_get_preset_filters_all_presets(self):
        """Test _get_preset_filters with all available presets"""
        presets_to_test = [
            "High Risk Only",
            "New Resources", 
            "Deletions Only",
            "Updates & Changes",
            "All Actions"
        ]
        
        for preset_name in presets_to_test:
            preset_config = self.sidebar_component._get_preset_filters(preset_name)
            
            # Verify each preset returns a valid configuration
            assert isinstance(preset_config, dict)
            assert 'action_filter' in preset_config
            assert 'risk_filter' in preset_config
            assert 'provider_filter' in preset_config
            
            # Verify action_filter is a list
            assert isinstance(preset_config['action_filter'], list)
            assert len(preset_config['action_filter']) > 0
            
            # Verify risk_filter is a list
            assert isinstance(preset_config['risk_filter'], list)
            assert len(preset_config['risk_filter']) > 0
    
    def test_validate_filter_expression_method(self):
        """Test the _validate_filter_expression private method"""
        # Test that the method exists
        assert hasattr(self.sidebar_component, '_validate_filter_expression')
        
        # Test with valid expression
        result = self.sidebar_component._validate_filter_expression("action='create'")
        assert isinstance(result, dict)
        assert 'valid' in result
        assert 'error' in result
        assert 'parsed' in result
        
        # Test with empty expression
        result = self.sidebar_component._validate_filter_expression("")
        assert result['valid'] == True
        assert result['error'] == ''
    
    def test_validate_filter_expression_invalid_syntax(self):
        """Test _validate_filter_expression with invalid syntax"""
        # Test with unbalanced parentheses
        result = self.sidebar_component._validate_filter_expression("(action='create'")
        assert result['valid'] == False
        assert 'parentheses' in result['error'].lower()
        
        # Test with no operators
        result = self.sidebar_component._validate_filter_expression("just some text")
        assert result['valid'] == False
        assert 'operator' in result['error'].lower()
    
    def test_parse_filter_expression_method(self):
        """Test the _parse_filter_expression private method"""
        # Test that the method exists
        assert hasattr(self.sidebar_component, '_parse_filter_expression')
        
        # Test with simple expression
        result = self.sidebar_component._parse_filter_expression("action='create' AND risk='High'")
        assert isinstance(result, str)
        assert 'AND' in result
        
        # Test with empty expression
        result = self.sidebar_component._parse_filter_expression("")
        assert result == ''
    
    @patch('streamlit.sidebar')
    @patch('components.sidebar.ErrorHandler')
    def test_component_handles_session_manager_errors(self, mock_error_handler, mock_sidebar):
        """Test that component handles SessionStateManager errors gracefully"""
        # Mock the error handler
        mock_error_handler.return_value = Mock()
        
        # Mock sidebar components
        mock_sidebar.title = Mock()
        mock_sidebar.markdown = Mock()
        mock_sidebar.info = Mock()
        mock_sidebar.checkbox = Mock(return_value=False)
        mock_sidebar.button = Mock(return_value=False)
        # Mock expander to support context manager protocol
        mock_expander = Mock()
        mock_expander.__enter__ = Mock(return_value=mock_expander)
        mock_expander.__exit__ = Mock(return_value=None)
        mock_sidebar.expander = Mock(return_value=mock_expander)
        
        # Make session manager raise an exception
        self.sidebar_component.session_manager = Mock()
        self.sidebar_component.session_manager.get_session_value.side_effect = Exception("Session error")
        
        # Component should still work despite session manager errors
        try:
            result = self.sidebar_component.render(enhanced_features_available=False)
            # If we get here, the component handled the error gracefully
            assert isinstance(result, dict)
        except Exception:
            # If an exception is raised, it should be handled by the component
            pytest.fail("Component should handle session manager errors gracefully")
    
    def test_component_initialization_with_session_manager(self):
        """Test that component initializes with SessionStateManager"""
        # Verify that the component has a session_manager attribute
        assert hasattr(self.sidebar_component, 'session_manager')
        assert self.sidebar_component.session_manager is not None


if __name__ == '__main__':
    pytest.main([__file__])
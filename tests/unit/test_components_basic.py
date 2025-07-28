"""
Basic unit tests for dashboard components

Tests component creation and basic functionality with minimal mocking.
"""

import pytest
from unittest.mock import Mock, patch
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))


class TestHeaderComponent:
    """Test cases for HeaderComponent"""
    
    def test_component_creation(self):
        """Test that HeaderComponent can be created successfully"""
        from components.header import HeaderComponent
        component = HeaderComponent()
        assert component is not None
        assert isinstance(component, HeaderComponent)
    
    def test_component_has_required_methods(self):
        """Test that HeaderComponent has all required methods"""
        from components.header import HeaderComponent
        component = HeaderComponent()
        
        # Check that required methods exist
        assert hasattr(component, 'render')
        assert callable(getattr(component, 'render'))
        assert hasattr(component, 'render_css')
        assert callable(getattr(component, 'render_css'))
    
    @patch('streamlit.markdown')
    def test_render_method_basic_functionality(self, mock_markdown):
        """Test that render method can be called and outputs content"""
        from components.header import HeaderComponent
        component = HeaderComponent()
        
        # Call render method
        result = component.render()
        
        # Verify streamlit.markdown was called
        mock_markdown.assert_called_once()
        
        # Verify the call contains expected header content
        call_args = mock_markdown.call_args
        assert 'Terraform Plan Impact Dashboard' in call_args[0][0]
        assert call_args[1]['unsafe_allow_html'] == True
        
        # Verify method returns None (outputs via Streamlit)
        assert result is None
    
    @patch('streamlit.markdown')
    def test_render_css_basic_functionality(self, mock_markdown):
        """Test that render_css method can be called and outputs CSS"""
        from components.header import HeaderComponent
        component = HeaderComponent()
        
        # Call render_css method
        result = component.render_css()
        
        # Verify streamlit.markdown was called
        mock_markdown.assert_called_once()
        
        # Verify the call contains CSS content
        call_args = mock_markdown.call_args
        css_content = call_args[0][0]
        assert '<style>' in css_content
        assert '.main-header' in css_content
        assert call_args[1]['unsafe_allow_html'] == True
        
        # Verify method returns None
        assert result is None


class TestUploadComponent:
    """Test cases for UploadComponent"""
    
    def test_component_creation(self):
        """Test that UploadComponent can be created successfully"""
        from components.upload_section import UploadComponent
        component = UploadComponent()
        assert component is not None
        assert isinstance(component, UploadComponent)
    
    def test_component_has_required_methods(self):
        """Test that UploadComponent has all required methods"""
        from components.upload_section import UploadComponent
        component = UploadComponent()
        
        # Check that required methods exist
        expected_methods = [
            'render',
            'validate_and_parse_file',
            'render_instructions',
            '_validate_plan_structure',
            '_has_minimal_required_structure'
        ]
        
        for method_name in expected_methods:
            assert hasattr(component, method_name), f"Missing method: {method_name}"
            assert callable(getattr(component, method_name)), f"Method not callable: {method_name}"
    
    def test_validate_plan_structure_with_valid_data(self):
        """Test _validate_plan_structure with valid plan data"""
        from components.upload_section import UploadComponent
        component = UploadComponent()
        
        valid_plan = {
            "terraform_version": "1.0.0",
            "format_version": "1.0",
            "resource_changes": [
                {
                    "change": {
                        "actions": ["create"]
                    }
                }
            ]
        }
        
        issues = component._validate_plan_structure(valid_plan)
        
        # Should return empty list for valid plan
        assert isinstance(issues, list)
        assert len(issues) == 0
    
    def test_validate_plan_structure_with_missing_fields(self):
        """Test _validate_plan_structure with missing required fields"""
        from components.upload_section import UploadComponent
        component = UploadComponent()
        
        invalid_plan = {
            "some_field": "value"
        }
        
        issues = component._validate_plan_structure(invalid_plan)
        
        # Should return list of issues
        assert isinstance(issues, list)
        assert len(issues) > 0
        
        # Check for specific missing field issues
        issue_text = " ".join(issues)
        assert "terraform_version" in issue_text
        assert "resource_changes" in issue_text
    
    def test_has_minimal_required_structure_valid(self):
        """Test _has_minimal_required_structure with valid minimal structure"""
        from components.upload_section import UploadComponent
        component = UploadComponent()
        
        minimal_plan = {
            "resource_changes": []
        }
        
        result = component._has_minimal_required_structure(minimal_plan)
        assert result == True
    
    def test_has_minimal_required_structure_invalid(self):
        """Test _has_minimal_required_structure with invalid structures"""
        from components.upload_section import UploadComponent
        component = UploadComponent()
        
        invalid_structures = [
            None,
            "not a dict",
            {},
            {"resource_changes": "not a list"},
            {"other_field": "value"}
        ]
        
        for invalid_structure in invalid_structures:
            result = component._has_minimal_required_structure(invalid_structure)
            assert result == False, f"Should return False for {invalid_structure}"


class TestSidebarComponent:
    """Test cases for SidebarComponent"""
    
    @patch('components.sidebar.SessionStateManager')
    def test_component_creation(self, mock_session_manager):
        """Test that SidebarComponent can be created successfully"""
        # Mock the SessionStateManager to avoid Streamlit dependencies
        mock_session_manager.return_value = Mock()
        
        from components.sidebar import SidebarComponent
        component = SidebarComponent()
        assert component is not None
        assert isinstance(component, SidebarComponent)
    
    @patch('components.sidebar.SessionStateManager')
    def test_component_has_required_methods(self, mock_session_manager):
        """Test that SidebarComponent has all required methods"""
        # Mock the SessionStateManager
        mock_session_manager.return_value = Mock()
        
        from components.sidebar import SidebarComponent
        component = SidebarComponent()
        
        # Check that required methods exist
        expected_methods = [
            'render',
            'render_filters',
            '_get_preset_filters',
            '_validate_filter_expression',
            '_parse_filter_expression'
        ]
        
        for method_name in expected_methods:
            assert hasattr(component, method_name), f"Missing method: {method_name}"
            assert callable(getattr(component, method_name)), f"Method not callable: {method_name}"
    
    @patch('components.sidebar.SessionStateManager')
    def test_get_preset_filters_method(self, mock_session_manager):
        """Test the _get_preset_filters private method"""
        # Mock the SessionStateManager
        mock_session_manager.return_value = Mock()
        
        from components.sidebar import SidebarComponent
        component = SidebarComponent()
        
        # Test with a known preset
        preset_config = component._get_preset_filters("High Risk Only")
        
        assert isinstance(preset_config, dict)
        assert preset_config['action_filter'] == ['create', 'update', 'delete', 'replace']
        assert preset_config['risk_filter'] == ['High']
        assert preset_config['provider_filter'] is None
    
    @patch('components.sidebar.SessionStateManager')
    def test_validate_filter_expression_basic(self, mock_session_manager):
        """Test the _validate_filter_expression method with basic cases"""
        # Mock the SessionStateManager
        mock_session_manager.return_value = Mock()
        
        from components.sidebar import SidebarComponent
        component = SidebarComponent()
        
        # Test with empty expression
        result = component._validate_filter_expression("")
        assert isinstance(result, dict)
        assert 'valid' in result
        assert 'error' in result
        assert 'parsed' in result
        assert result['valid'] == True
        assert result['error'] == ''
    
    @patch('components.sidebar.SessionStateManager')
    def test_parse_filter_expression_basic(self, mock_session_manager):
        """Test the _parse_filter_expression method"""
        # Mock the SessionStateManager
        mock_session_manager.return_value = Mock()
        
        from components.sidebar import SidebarComponent
        component = SidebarComponent()
        
        # Test with empty expression
        result = component._parse_filter_expression("")
        assert result == ''
        
        # Test with simple expression
        result = component._parse_filter_expression("action='create'")
        assert isinstance(result, str)


class TestSessionStateManagerBasic:
    """Basic test cases for SessionStateManager without complex mocking"""
    
    def test_session_manager_import(self):
        """Test that SessionStateManager can be imported"""
        from ui.session_manager import SessionStateManager
        assert SessionStateManager is not None
    
    @patch('streamlit.session_state', {})
    def test_session_manager_creation_with_mock(self):
        """Test SessionStateManager creation with mocked session state"""
        # Create a mock session state that supports both dict and attribute access
        class MockSessionState(dict):
            def __getattr__(self, name):
                try:
                    return self[name]
                except KeyError:
                    # Return a default value instead of raising AttributeError
                    if name in ['show_debug', 'uploaded_file_processed']:
                        return False
                    elif name in ['enable_multi_cloud']:
                        return True
                    elif name in ['action_filter']:
                        return ['create', 'update', 'delete', 'replace']
                    elif name in ['risk_filter']:
                        return ['Low', 'Medium', 'High']
                    elif name in ['provider_filter', 'search_result_indices', 'saved_filter_configs']:
                        return []
                    elif name in ['search_query', 'filter_expression']:
                        return ''
                    elif name in ['search_results_count', 'current_search_result_index']:
                        return 0
                    elif name in ['filter_logic']:
                        return 'AND'
                    elif name in ['selected_preset']:
                        return 'Custom'
                    elif name in ['use_advanced_filters']:
                        return False
                    else:
                        return None
            
            def __setattr__(self, name, value):
                self[name] = value
        
        mock_session_state = MockSessionState()
        
        with patch('streamlit.session_state', mock_session_state):
            from ui.session_manager import SessionStateManager
            session_manager = SessionStateManager()
            assert session_manager is not None
            assert isinstance(session_manager, SessionStateManager)


if __name__ == '__main__':
    pytest.main([__file__])
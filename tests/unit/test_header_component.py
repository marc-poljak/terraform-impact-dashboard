"""
Unit tests for HeaderComponent

Tests the header component creation and basic functionality.
"""

import pytest
from unittest.mock import Mock, patch
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from components.header import HeaderComponent


class TestHeaderComponent:
    """Test cases for HeaderComponent"""
    
    def setup_method(self):
        """Set up test fixtures before each test method"""
        self.header_component = HeaderComponent()
    
    def test_component_creation(self):
        """Test that HeaderComponent can be created successfully"""
        assert self.header_component is not None
        assert isinstance(self.header_component, HeaderComponent)
    
    @patch('streamlit.markdown')
    def test_render_method_exists(self, mock_markdown):
        """Test that render method exists and can be called"""
        # Test that render method exists
        assert hasattr(self.header_component, 'render')
        assert callable(getattr(self.header_component, 'render'))
        
        # Test that render method can be called without errors
        self.header_component.render()
        
        # Verify that streamlit.markdown was called
        mock_markdown.assert_called()
    
    @patch('streamlit.markdown')
    def test_render_outputs_header(self, mock_markdown):
        """Test that render method outputs the expected header content"""
        self.header_component.render()
        
        # Check that markdown was called with header content
        mock_markdown.assert_called_with(
            '<div class="main-header">🚀 Terraform Plan Impact Dashboard</div>', 
            unsafe_allow_html=True
        )
    
    @patch('streamlit.markdown')
    def test_render_css_method_exists(self, mock_markdown):
        """Test that render_css method exists and can be called"""
        # Test that render_css method exists
        assert hasattr(self.header_component, 'render_css')
        assert callable(getattr(self.header_component, 'render_css'))
        
        # Test that render_css method can be called without errors
        self.header_component.render_css()
        
        # Verify that streamlit.markdown was called
        mock_markdown.assert_called()
    
    @patch('streamlit.markdown')
    def test_render_css_contains_required_styles(self, mock_markdown):
        """Test that render_css outputs CSS with required style classes"""
        self.header_component.render_css()
        
        # Get the CSS content that was passed to markdown
        call_args = mock_markdown.call_args
        css_content = call_args[0][0]  # First positional argument
        
        # Verify required CSS classes are present
        required_classes = [
            '.main-header',
            '.metric-card',
            '.risk-low',
            '.risk-medium', 
            '.risk-high',
            '.provider-aws',
            '.provider-azure',
            '.provider-google',
            '.upload-section',
            '.debug-info',
            '.multi-cloud-alert',
            '.feature-unavailable'
        ]
        
        for css_class in required_classes:
            assert css_class in css_content, f"Required CSS class {css_class} not found"
    
    @patch('streamlit.markdown')
    def test_render_css_has_multi_cloud_styling(self, mock_markdown):
        """Test that CSS includes multi-cloud provider styling classes"""
        self.header_component.render_css()
        
        # Get the CSS content
        call_args = mock_markdown.call_args
        css_content = call_args[0][0]
        
        # Verify multi-cloud provider classes are present with gradients
        assert '.provider-aws' in css_content
        assert '.provider-azure' in css_content
        assert '.provider-google' in css_content
        
        # Verify they contain gradient styling
        assert 'linear-gradient' in css_content
        assert '#FF9900' in css_content  # AWS orange
        assert '#0078D4' in css_content  # Azure blue
        assert '#4285F4' in css_content  # Google blue
    
    @patch('streamlit.markdown')
    def test_render_css_preserves_existing_styles(self, mock_markdown):
        """Test that CSS preserves all existing styling from original app.py"""
        self.header_component.render_css()
        
        # Get the CSS content
        call_args = mock_markdown.call_args
        css_content = call_args[0][0]
        
        # Verify key styling properties are preserved
        assert 'font-size: 2.5rem' in css_content  # Main header size
        assert 'color: #1f77b4' in css_content     # Header color
        assert 'text-align: center' in css_content # Header alignment
        assert 'border: 2px dashed' in css_content # Upload section border
        assert 'border-radius: 10px' in css_content # Rounded corners
        assert 'background-color: #f8f9fa' in css_content # Background colors
    
    def test_component_has_no_dependencies_on_streamlit_state(self):
        """Test that component can be created without Streamlit session state"""
        # This test ensures the component doesn't depend on st.session_state during initialization
        component = HeaderComponent()
        assert component is not None
    
    @patch('streamlit.markdown')
    def test_multiple_render_calls_work(self, mock_markdown):
        """Test that render method can be called multiple times without issues"""
        # Call render multiple times
        self.header_component.render()
        self.header_component.render()
        self.header_component.render()
        
        # Verify markdown was called each time
        assert mock_markdown.call_count == 3
        
        # Verify each call had the same content
        for call in mock_markdown.call_args_list:
            assert call[0][0] == '<div class="main-header">🚀 Terraform Plan Impact Dashboard</div>'
            assert call[1]['unsafe_allow_html'] == True
    
    @patch('streamlit.markdown')
    def test_css_render_multiple_calls(self, mock_markdown):
        """Test that render_css can be called multiple times without issues"""
        # Call render_css multiple times
        self.header_component.render_css()
        self.header_component.render_css()
        
        # Verify markdown was called each time
        assert mock_markdown.call_count == 2
        
        # Verify both calls had the same CSS content
        first_call_css = mock_markdown.call_args_list[0][0][0]
        second_call_css = mock_markdown.call_args_list[1][0][0]
        assert first_call_css == second_call_css
    
    def test_component_methods_return_none(self):
        """Test that component methods return None (they output via Streamlit)"""
        with patch('streamlit.markdown'):
            result = self.header_component.render()
            assert result is None
            
            css_result = self.header_component.render_css()
            assert css_result is None


if __name__ == '__main__':
    pytest.main([__file__])
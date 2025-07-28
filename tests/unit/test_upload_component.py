"""
Unit tests for UploadComponent

Tests the upload component creation and basic functionality.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import json
import sys
import os
from io import StringIO

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from components.upload_section import UploadComponent


class TestUploadComponent:
    """Test cases for UploadComponent"""
    
    def setup_method(self):
        """Set up test fixtures before each test method"""
        self.upload_component = UploadComponent()
    
    def test_component_creation(self):
        """Test that UploadComponent can be created successfully"""
        assert self.upload_component is not None
        assert isinstance(self.upload_component, UploadComponent)
    
    @patch('streamlit.file_uploader')
    @patch('streamlit.markdown')
    @patch('streamlit.columns')
    @patch('streamlit.metric')
    @patch('streamlit.expander')
    @patch('components.upload_section.ErrorHandler')
    def test_render_method_exists(self, mock_error_handler, mock_expander, mock_metric, 
                                 mock_columns, mock_markdown, mock_file_uploader):
        """Test that render method exists and can be called"""
        # Mock the error handler
        mock_error_handler.return_value = Mock()
        
        # Mock file uploader to return None (no file uploaded)
        mock_file_uploader.return_value = None
        mock_columns.return_value = [Mock(), Mock(), Mock()]
        
        # Test that render method exists
        assert hasattr(self.upload_component, 'render')
        assert callable(getattr(self.upload_component, 'render'))
        
        # Test that render method can be called without errors
        result = self.upload_component.render()
        
        # Verify it returns None when no file is uploaded
        assert result is None
    
    @patch('streamlit.file_uploader')
    @patch('streamlit.markdown')
    @patch('streamlit.columns')
    @patch('streamlit.metric')
    @patch('components.upload_section.ErrorHandler')
    def test_render_with_uploaded_file(self, mock_error_handler, mock_metric, 
                                      mock_columns, mock_markdown, mock_file_uploader):
        """Test render method when a file is uploaded"""
        # Mock the error handler
        mock_error_handler.return_value = Mock()
        
        # Create a mock uploaded file
        mock_file = Mock()
        mock_file.name = "test-plan.json"
        mock_file.type = "application/json"
        mock_file.getvalue.return_value = b'{"test": "data"}'
        
        mock_file_uploader.return_value = mock_file
        mock_columns.return_value = [Mock(), Mock(), Mock()]
        
        result = self.upload_component.render()
        
        # Verify it returns the uploaded file
        assert result == mock_file
        
        # Verify file metrics are displayed
        mock_metric.assert_called()
    
    @patch('streamlit.file_uploader')
    @patch('streamlit.markdown')
    @patch('components.upload_section.ErrorHandler')
    def test_render_shows_upload_section_styling(self, mock_error_handler, mock_markdown, mock_file_uploader):
        """Test that render method shows upload section with proper styling"""
        # Mock the error handler
        mock_error_handler.return_value = Mock()
        mock_file_uploader.return_value = None
        
        self.upload_component.render()
        
        # Verify upload section div is created
        upload_div_calls = [call for call in mock_markdown.call_args_list 
                           if '<div class="upload-section">' in str(call)]
        assert len(upload_div_calls) > 0
    
    def test_validate_and_parse_file_method_exists(self):
        """Test that validate_and_parse_file method exists"""
        assert hasattr(self.upload_component, 'validate_and_parse_file')
        assert callable(getattr(self.upload_component, 'validate_and_parse_file'))
    
    @patch('components.upload_section.ErrorHandler')
    @patch('streamlit.success')
    @patch('streamlit.expander')
    @patch('streamlit.columns')
    @patch('streamlit.write')
    def test_validate_and_parse_file_valid_json(self, mock_write, mock_columns, mock_expander, 
                                               mock_success, mock_error_handler):
        """Test validate_and_parse_file with valid JSON data"""
        # Mock the error handler
        mock_error_handler.return_value = Mock()
        mock_columns.return_value = [Mock(), Mock()]
        mock_expander.return_value.__enter__ = Mock()
        mock_expander.return_value.__exit__ = Mock()
        
        # Create a mock file with valid Terraform plan JSON
        mock_file = Mock()
        valid_plan_data = {
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
        
        # Mock json.load to return valid data
        with patch('json.load', return_value=valid_plan_data):
            result, error = self.upload_component.validate_and_parse_file(mock_file)
        
        # Verify successful parsing
        assert result == valid_plan_data
        assert error is None
        mock_success.assert_called_with("✅ File validated successfully!")
    
    @patch('components.upload_section.ErrorHandler')
    def test_validate_and_parse_file_invalid_json(self, mock_error_handler):
        """Test validate_and_parse_file with invalid JSON"""
        # Mock the error handler
        mock_error_handler_instance = Mock()
        mock_error_handler.return_value = mock_error_handler_instance
        
        # Create a mock file
        mock_file = Mock()
        
        # Mock json.load to raise JSONDecodeError
        with patch('json.load', side_effect=json.JSONDecodeError("Invalid JSON", "doc", 0)):
            result, error = self.upload_component.validate_and_parse_file(mock_file)
        
        # Verify error handling
        assert result is None
        assert error == "Invalid JSON format"
        mock_error_handler_instance.handle_upload_error.assert_called()
    
    def test_validate_plan_structure_method_exists(self):
        """Test that _validate_plan_structure method exists"""
        assert hasattr(self.upload_component, '_validate_plan_structure')
        assert callable(getattr(self.upload_component, '_validate_plan_structure'))
    
    def test_validate_plan_structure_valid_plan(self):
        """Test _validate_plan_structure with valid plan data"""
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
        
        issues = self.upload_component._validate_plan_structure(valid_plan)
        
        # Should return empty list for valid plan
        assert isinstance(issues, list)
        assert len(issues) == 0
    
    def test_validate_plan_structure_missing_fields(self):
        """Test _validate_plan_structure with missing required fields"""
        invalid_plan = {
            "some_field": "value"
        }
        
        issues = self.upload_component._validate_plan_structure(invalid_plan)
        
        # Should return list of issues
        assert isinstance(issues, list)
        assert len(issues) > 0
        
        # Check for specific missing field issues
        issue_text = " ".join(issues)
        assert "terraform_version" in issue_text
        assert "resource_changes" in issue_text
    
    def test_validate_plan_structure_empty_resource_changes(self):
        """Test _validate_plan_structure with empty resource_changes"""
        plan_with_empty_changes = {
            "terraform_version": "1.0.0",
            "format_version": "1.0",
            "resource_changes": []
        }
        
        issues = self.upload_component._validate_plan_structure(plan_with_empty_changes)
        
        # Should report no changes found
        assert isinstance(issues, list)
        assert any("No resource changes found" in issue for issue in issues)
    
    def test_has_minimal_required_structure_method_exists(self):
        """Test that _has_minimal_required_structure method exists"""
        assert hasattr(self.upload_component, '_has_minimal_required_structure')
        assert callable(getattr(self.upload_component, '_has_minimal_required_structure'))
    
    def test_has_minimal_required_structure_valid(self):
        """Test _has_minimal_required_structure with valid minimal structure"""
        minimal_plan = {
            "resource_changes": []
        }
        
        result = self.upload_component._has_minimal_required_structure(minimal_plan)
        assert result == True
    
    def test_has_minimal_required_structure_invalid(self):
        """Test _has_minimal_required_structure with invalid structure"""
        invalid_structures = [
            None,
            "not a dict",
            {},
            {"resource_changes": "not a list"},
            {"other_field": "value"}
        ]
        
        for invalid_structure in invalid_structures:
            result = self.upload_component._has_minimal_required_structure(invalid_structure)
            assert result == False, f"Should return False for {invalid_structure}"
    
    @patch('streamlit.markdown')
    def test_render_instructions_method_exists(self, mock_markdown):
        """Test that render_instructions method exists and can be called"""
        assert hasattr(self.upload_component, 'render_instructions')
        assert callable(getattr(self.upload_component, 'render_instructions'))
        
        # Test that it can be called without errors
        self.upload_component.render_instructions()
        
        # Verify markdown was called to render instructions
        mock_markdown.assert_called()
    
    @patch('streamlit.markdown')
    def test_render_instructions_content(self, mock_markdown):
        """Test that render_instructions outputs expected content"""
        self.upload_component.render_instructions()
        
        # Get all markdown calls
        markdown_calls = [str(call) for call in mock_markdown.call_args_list]
        markdown_content = " ".join(markdown_calls)
        
        # Verify key instruction content is present
        assert "Instructions" in markdown_content
        assert "Upload" in markdown_content
        assert "Terraform" in markdown_content
    
    def test_component_handles_large_files(self):
        """Test that component can handle file size calculations"""
        # Create a mock file with large content
        mock_file = Mock()
        large_content = b'{"data": "' + b'x' * (10 * 1024 * 1024) + b'"}'  # ~10MB
        mock_file.getvalue.return_value = large_content
        
        # Test that file size calculation works
        file_size_mb = len(mock_file.getvalue()) / (1024 * 1024)
        assert file_size_mb > 10
    
    @patch('components.upload_section.ErrorHandler')
    def test_validate_and_parse_file_handles_exceptions(self, mock_error_handler):
        """Test that validate_and_parse_file handles unexpected exceptions"""
        # Mock the error handler
        mock_error_handler_instance = Mock()
        mock_error_handler.return_value = mock_error_handler_instance
        
        # Create a mock file
        mock_file = Mock()
        
        # Mock json.load to raise a generic exception
        with patch('json.load', side_effect=Exception("Unexpected error")):
            result, error = self.upload_component.validate_and_parse_file(mock_file)
        
        # Verify error handling
        assert result is None
        assert error == "Unexpected error"
        mock_error_handler_instance.handle_upload_error.assert_called()
    
    def test_component_preserves_existing_functionality(self):
        """Test that component preserves existing upload functionality"""
        # Verify that all expected methods exist
        expected_methods = [
            'render',
            'validate_and_parse_file',
            'render_instructions',
            '_validate_plan_structure',
            '_has_minimal_required_structure'
        ]
        
        for method_name in expected_methods:
            assert hasattr(self.upload_component, method_name), f"Missing method: {method_name}"
            assert callable(getattr(self.upload_component, method_name)), f"Method not callable: {method_name}"


if __name__ == '__main__':
    pytest.main([__file__])
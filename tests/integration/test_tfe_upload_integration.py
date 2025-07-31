"""
Integration tests for TFE and file upload integration with plan processing pipeline.

This module tests the complete workflow from both input methods (file upload and TFE)
through the plan processing pipeline to ensure seamless integration.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import json
import io

from components.upload_section import UploadComponent
from utils.plan_processor import PlanProcessor
from ui.error_handler import ErrorHandler


class TestTFEUploadIntegration:
    """Test integration between TFE input, file upload, and plan processing"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.upload_component = UploadComponent()
        self.plan_processor = PlanProcessor()
        self.error_handler = ErrorHandler()
        
        # Sample plan data that both file upload and TFE would provide
        self.sample_plan_data = {
            "terraform_version": "1.0.0",
            "format_version": "1.0",
            "resource_changes": [
                {
                    "address": "aws_instance.example",
                    "mode": "managed",
                    "type": "aws_instance",
                    "name": "example",
                    "change": {
                        "actions": ["create"],
                        "before": None,
                        "after": {
                            "instance_type": "t2.micro",
                            "ami": "ami-12345678"
                        }
                    }
                }
            ]
        }
    
    @patch('streamlit.tabs')
    @patch('streamlit.markdown')
    @patch('components.upload_section.ErrorHandler')
    def test_upload_component_returns_plan_data_from_either_tab(self, mock_error_handler, mock_markdown, mock_tabs):
        """Test that upload component can return plan data from either file upload or TFE tab"""
        # Mock error handler
        mock_error_handler.return_value = Mock()
        
        # Mock tabs
        mock_tab1 = Mock()
        mock_tab1.__enter__ = Mock(return_value=mock_tab1)
        mock_tab1.__exit__ = Mock(return_value=None)
        mock_tab2 = Mock()
        mock_tab2.__enter__ = Mock(return_value=mock_tab2)
        mock_tab2.__exit__ = Mock(return_value=None)
        mock_tabs.return_value = [mock_tab1, mock_tab2]
        
        # Test 1: File upload returns data
        with patch.object(self.upload_component, '_render_file_upload_tab', return_value="file_data"):
            with patch.object(self.upload_component, '_render_tfe_integration_tab', return_value=None):
                result = self.upload_component.render()
                assert result == "file_data"
        
        # Test 2: TFE integration returns data
        with patch.object(self.upload_component, '_render_file_upload_tab', return_value=None):
            with patch.object(self.upload_component, '_render_tfe_integration_tab', return_value="tfe_data"):
                result = self.upload_component.render()
                assert result == "tfe_data"
        
        # Test 3: Both return data (TFE takes precedence as it's processed last)
        with patch.object(self.upload_component, '_render_file_upload_tab', return_value="file_data"):
            with patch.object(self.upload_component, '_render_tfe_integration_tab', return_value="tfe_data"):
                result = self.upload_component.render()
                assert result == "tfe_data"
    
    def test_plan_processor_handles_file_upload_data(self):
        """Test that plan processor can handle file upload data"""
        # Create a mock uploaded file
        mock_file = Mock()
        mock_file.getvalue.return_value = json.dumps(self.sample_plan_data).encode('utf-8')
        mock_file.size = len(mock_file.getvalue())
        
        # Mock the upload component's validate_and_parse_file method
        with patch.object(self.upload_component, 'validate_and_parse_file', 
                         return_value=(self.sample_plan_data, None)):
            
            result = self.plan_processor.process_plan_data(
                mock_file, self.upload_component, self.error_handler, False, False
            )
            
            # Verify processing was successful
            assert result is not None
            assert result['plan_data'] == self.sample_plan_data
            assert 'parser' in result
            assert 'summary' in result
            assert 'resource_changes' in result
    
    def test_plan_processor_handles_tfe_data(self):
        """Test that plan processor can handle TFE-retrieved data"""
        # TFE data comes as a dictionary (already parsed JSON)
        tfe_data = self.sample_plan_data
        
        result = self.plan_processor.process_plan_data(
            tfe_data, self.upload_component, self.error_handler, False, False
        )
        
        # Verify processing was successful
        assert result is not None
        assert result['plan_data'] == self.sample_plan_data
        assert 'parser' in result
        assert 'summary' in result
        assert 'resource_changes' in result
    
    def test_both_input_methods_produce_same_analysis_results(self):
        """Test that both file upload and TFE produce equivalent analysis results"""
        # Process via file upload simulation
        mock_file = Mock()
        mock_file.getvalue.return_value = json.dumps(self.sample_plan_data).encode('utf-8')
        mock_file.size = len(mock_file.getvalue())
        
        with patch.object(self.upload_component, 'validate_and_parse_file', 
                         return_value=(self.sample_plan_data, None)):
            file_result = self.plan_processor.process_plan_data(
                mock_file, self.upload_component, self.error_handler, False, False
            )
        
        # Process via TFE simulation
        tfe_result = self.plan_processor.process_plan_data(
            self.sample_plan_data, self.upload_component, self.error_handler, False, False
        )
        
        # Both should produce equivalent results
        assert file_result is not None
        assert tfe_result is not None
        
        # Compare key analysis results
        assert file_result['plan_data'] == tfe_result['plan_data']
        assert len(file_result['resource_changes']) == len(tfe_result['resource_changes'])
        assert file_result['summary']['total'] == tfe_result['summary']['total']
    
    @patch('streamlit.tabs')
    @patch('streamlit.markdown')
    @patch('components.upload_section.ErrorHandler')
    def test_error_handling_in_integrated_workflow(self, mock_error_handler, mock_markdown, mock_tabs):
        """Test error handling when TFE integration fails but file upload is available"""
        # Mock error handler
        mock_error_handler.return_value = Mock()
        
        # Mock tabs
        mock_tab1 = Mock()
        mock_tab1.__enter__ = Mock(return_value=mock_tab1)
        mock_tab1.__exit__ = Mock(return_value=None)
        mock_tab2 = Mock()
        mock_tab2.__enter__ = Mock(return_value=mock_tab2)
        mock_tab2.__exit__ = Mock(return_value=None)
        mock_tabs.return_value = [mock_tab1, mock_tab2]
        
        # Simulate TFE failure but file upload success
        with patch.object(self.upload_component, '_render_file_upload_tab', return_value="file_data"):
            with patch.object(self.upload_component, '_render_tfe_integration_tab', return_value=None):
                result = self.upload_component.render()
                
                # Should still get file data even if TFE fails
                assert result == "file_data"
    
    def test_plan_processor_input_type_detection(self):
        """Test that plan processor correctly detects input type"""
        # Test file input detection
        mock_file = Mock()
        mock_file.getvalue.return_value = b'{"test": "data"}'
        mock_file.size = 100
        
        # This should be detected as file upload
        with patch.object(self.upload_component, 'validate_and_parse_file', 
                         return_value=(self.sample_plan_data, None)):
            result = self.plan_processor.process_plan_data(
                mock_file, self.upload_component, self.error_handler, False, False
            )
            assert result is not None
        
        # Test TFE data detection (dictionary input)
        tfe_data = {"test": "data"}
        
        # This should be detected as TFE data
        result = self.plan_processor.process_plan_data(
            tfe_data, self.upload_component, self.error_handler, False, False
        )
        # Should process but with empty resource changes due to invalid structure
        assert result is not None  # Plan processor is robust and handles invalid data
        assert len(result['resource_changes']) == 0  # No valid resource changes
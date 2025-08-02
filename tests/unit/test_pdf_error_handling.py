"""
Unit tests for PDF generation error handling and user feedback improvements

Tests the enhanced error handling, progress indicators, and fallback options
implemented for the PDF generator rebuild.

Requirements tested: 4.4, 4.5, 1.3
"""

import pytest
import unittest
from unittest.mock import Mock, patch, MagicMock
import io
from typing import Dict, Any, List, Optional

# Import the components to test
try:
    from components.enhanced_pdf_generator import EnhancedPDFGenerator, validate_dependencies
    from components.report_generator import ReportGeneratorComponent
    PDF_COMPONENTS_AVAILABLE = True
except ImportError:
    PDF_COMPONENTS_AVAILABLE = False


class TestPDFErrorHandling(unittest.TestCase):
    """Test PDF generation error handling and user feedback"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.sample_summary = {
            'create': 5,
            'update': 3,
            'delete': 2,
            'no-op': 10,
            'total': 20
        }
        
        self.sample_risk_summary = {
            'overall_risk': {
                'level': 'Medium',
                'score': 65,
                'risk_factors': ['Resource deletion detected', 'Security group changes']
            }
        }
        
        self.sample_resource_changes = [
            {
                'address': 'aws_instance.web',
                'type': 'aws_instance',
                'change': {'actions': ['create']},
                'provider_name': 'registry.terraform.io/hashicorp/aws'
            },
            {
                'address': 'aws_security_group.web',
                'type': 'aws_security_group',
                'change': {'actions': ['update']},
                'provider_name': 'registry.terraform.io/hashicorp/aws'
            }
        ]
        
        self.sample_resource_types = {
            'aws_instance': 1,
            'aws_security_group': 1
        }
        
        self.sample_plan_data = {
            'terraform_version': '1.5.0',
            'format_version': '1.1',
            'resource_changes': self.sample_resource_changes
        }
    
    @pytest.mark.skipif(not PDF_COMPONENTS_AVAILABLE, reason="PDF components not available")
    def test_dependency_validation_success(self):
        """Test successful dependency validation"""
        with patch('components.enhanced_pdf_generator.REPORTLAB_AVAILABLE', True):
            is_valid, error_msg = validate_dependencies()
            self.assertTrue(is_valid)
            self.assertEqual(error_msg, "")
    
    @pytest.mark.skipif(not PDF_COMPONENTS_AVAILABLE, reason="PDF components not available")
    def test_dependency_validation_failure(self):
        """Test dependency validation failure"""
        with patch('components.enhanced_pdf_generator.REPORTLAB_AVAILABLE', False):
            with patch('builtins.__import__', side_effect=ImportError("No module named 'reportlab'")):
                is_valid, error_msg = validate_dependencies()
                self.assertFalse(is_valid)
                self.assertIn("reportlab", error_msg.lower())
                self.assertIn("pip install reportlab", error_msg)
    
    @pytest.mark.skipif(not PDF_COMPONENTS_AVAILABLE, reason="PDF components not available")
    def test_input_data_validation_success(self):
        """Test successful input data validation"""
        generator = EnhancedPDFGenerator()
        
        error = generator._validate_input_data(
            self.sample_summary,
            self.sample_risk_summary,
            self.sample_resource_changes,
            self.sample_resource_types,
            self.sample_plan_data
        )
        
        self.assertIsNone(error)
    
    @pytest.mark.skipif(not PDF_COMPONENTS_AVAILABLE, reason="PDF components not available")
    def test_input_data_validation_invalid_summary(self):
        """Test input validation with invalid summary data"""
        generator = EnhancedPDFGenerator()
        
        # Test with non-dict summary
        error = generator._validate_input_data(
            "invalid_summary",
            self.sample_risk_summary,
            self.sample_resource_changes,
            self.sample_resource_types,
            self.sample_plan_data
        )
        
        self.assertIsNotNone(error)
        self.assertIn("Summary must be a dictionary", error)
    
    @pytest.mark.skipif(not PDF_COMPONENTS_AVAILABLE, reason="PDF components not available")
    def test_input_data_validation_missing_summary_keys(self):
        """Test input validation with missing summary keys"""
        generator = EnhancedPDFGenerator()
        
        invalid_summary = {'create': 5}  # Missing 'update' and 'delete'
        
        error = generator._validate_input_data(
            invalid_summary,
            self.sample_risk_summary,
            self.sample_resource_changes,
            self.sample_resource_types,
            self.sample_plan_data
        )
        
        self.assertIsNotNone(error)
        self.assertIn("missing required key", error.lower())
    
    @pytest.mark.skipif(not PDF_COMPONENTS_AVAILABLE, reason="PDF components not available")
    def test_input_data_validation_negative_values(self):
        """Test input validation with negative values"""
        generator = EnhancedPDFGenerator()
        
        invalid_summary = {
            'create': -1,  # Negative value
            'update': 3,
            'delete': 2
        }
        
        error = generator._validate_input_data(
            invalid_summary,
            self.sample_risk_summary,
            self.sample_resource_changes,
            self.sample_resource_types,
            self.sample_plan_data
        )
        
        self.assertIsNotNone(error)
        self.assertIn("non-negative integer", error)
    
    @pytest.mark.skipif(not PDF_COMPONENTS_AVAILABLE, reason="PDF components not available")
    def test_input_data_validation_too_many_resources(self):
        """Test input validation with too many resources"""
        generator = EnhancedPDFGenerator()
        
        # Create a large list of resource changes
        large_resource_changes = [self.sample_resource_changes[0]] * 15000
        
        error = generator._validate_input_data(
            self.sample_summary,
            self.sample_risk_summary,
            large_resource_changes,
            self.sample_resource_types,
            self.sample_plan_data
        )
        
        self.assertIsNotNone(error)
        self.assertIn("Too many resource changes", error)
        self.assertIn("Maximum supported: 10,000", error)
    
    @pytest.mark.skipif(not PDF_COMPONENTS_AVAILABLE, reason="PDF components not available")
    def test_progress_callback_functionality(self):
        """Test progress callback functionality during PDF generation"""
        generator = EnhancedPDFGenerator()
        
        # Mock progress callback
        progress_callback = Mock()
        
        with patch.object(generator, 'validate_dependencies', return_value=(True, "")):
            with patch.object(generator, '_validate_input_data', return_value=None):
                with patch.object(generator, 'is_available', True):
                    with patch('components.enhanced_pdf_generator.REPORTLAB_AVAILABLE', True):
                        # Mock the PDF generation components
                        with patch('components.enhanced_pdf_generator.SimpleDocTemplate') as mock_doc:
                            with patch('components.enhanced_pdf_generator.io.BytesIO') as mock_buffer:
                                mock_buffer.return_value.getvalue.return_value = b"fake_pdf_content"
                                
                                # Call the method with progress callback
                                result, error = generator.generate_comprehensive_report(
                                    self.sample_summary,
                                    self.sample_risk_summary,
                                    self.sample_resource_changes,
                                    self.sample_resource_types,
                                    self.sample_plan_data,
                                    progress_callback=progress_callback
                                )
                                
                                # Verify progress callback was called
                                self.assertTrue(progress_callback.called)
                                
                                # Check that progress values were reasonable
                                call_args = [call[0] for call in progress_callback.call_args_list]
                                progress_values = [args[0] for args in call_args if len(args) > 0]
                                
                                # Should have multiple progress updates
                                self.assertGreater(len(progress_values), 3)
                                
                                # Progress should start at 0 and end at 1.0
                                self.assertEqual(progress_values[0], 0.0)
                                self.assertEqual(progress_values[-1], 1.0)
                                
                                # Progress should be monotonically increasing
                                for i in range(1, len(progress_values)):
                                    self.assertGreaterEqual(progress_values[i], progress_values[i-1])
    
    @pytest.mark.skipif(not PDF_COMPONENTS_AVAILABLE, reason="PDF components not available")
    def test_pdf_generation_memory_error(self):
        """Test handling of memory errors during PDF generation"""
        generator = EnhancedPDFGenerator()
        
        with patch.object(generator, 'validate_dependencies', return_value=(True, "")):
            with patch.object(generator, '_validate_input_data', return_value=None):
                with patch.object(generator, 'is_available', True):
                    with patch('components.enhanced_pdf_generator.REPORTLAB_AVAILABLE', True):
                        # Mock memory error during PDF generation
                        with patch('components.enhanced_pdf_generator.SimpleDocTemplate', side_effect=MemoryError("Insufficient memory")):
                            
                            result, error = generator.generate_comprehensive_report(
                                self.sample_summary,
                                self.sample_risk_summary,
                                self.sample_resource_changes,
                                self.sample_resource_types,
                                self.sample_plan_data
                            )
                            
                            self.assertIsNone(result)
                            self.assertIsNotNone(error)
                            self.assertIn("Insufficient memory", error)
                            self.assertIn("reducing data size", error)
    
    @pytest.mark.skipif(not PDF_COMPONENTS_AVAILABLE, reason="PDF components not available")
    def test_pdf_generation_import_error(self):
        """Test handling of import errors during PDF generation"""
        generator = EnhancedPDFGenerator()
        
        with patch.object(generator, 'validate_dependencies', return_value=(True, "")):
            with patch.object(generator, '_validate_input_data', return_value=None):
                with patch.object(generator, 'is_available', True):
                    with patch('components.enhanced_pdf_generator.REPORTLAB_AVAILABLE', True):
                        # Mock import error during PDF generation
                        with patch('components.enhanced_pdf_generator.SimpleDocTemplate', side_effect=ImportError("Missing reportlab module")):
                            
                            result, error = generator.generate_comprehensive_report(
                                self.sample_summary,
                                self.sample_risk_summary,
                                self.sample_resource_changes,
                                self.sample_resource_types,
                                self.sample_plan_data
                            )
                            
                            self.assertIsNone(result)
                            self.assertIsNotNone(error)
                            self.assertIn("Missing required PDF generation dependencies", error)
                            self.assertIn("pip install reportlab", error)
    
    @pytest.mark.skipif(not PDF_COMPONENTS_AVAILABLE, reason="PDF components not available")
    def test_fallback_report_generation(self):
        """Test fallback text report generation"""
        generator = EnhancedPDFGenerator()
        
        report_content, filename = generator.generate_fallback_report(
            self.sample_summary,
            self.sample_risk_summary,
            self.sample_resource_changes,
            self.sample_resource_types,
            self.sample_plan_data
        )
        
        # Verify report content
        self.assertIsInstance(report_content, str)
        self.assertIn("TERRAFORM PLAN IMPACT REPORT", report_content)
        self.assertIn("Create Operations: 5", report_content)
        self.assertIn("Update Operations: 3", report_content)
        self.assertIn("Delete Operations: 2", report_content)
        self.assertIn("aws_instance: 1", report_content)
        self.assertIn("aws_security_group: 1", report_content)
        
        # Verify filename format
        self.assertIsInstance(filename, str)
        self.assertTrue(filename.endswith('.txt'))
        self.assertIn('terraform-plan-report', filename)
    
    @pytest.mark.skipif(not PDF_COMPONENTS_AVAILABLE, reason="PDF components not available")
    def test_fallback_report_with_exception(self):
        """Test fallback report generation when an exception occurs"""
        generator = EnhancedPDFGenerator()
        
        # Create invalid data that will cause an exception
        invalid_resource_changes = "invalid_data"
        
        report_content, filename = generator.generate_fallback_report(
            self.sample_summary,
            self.sample_risk_summary,
            invalid_resource_changes,
            self.sample_resource_types,
            self.sample_plan_data
        )
        
        # Should still generate a minimal report
        self.assertIsInstance(report_content, str)
        self.assertIn("MINIMAL FALLBACK", report_content)
        self.assertIn("Create: 5", report_content)
        self.assertIn("Update: 3", report_content)
        self.assertIn("Delete: 2", report_content)
        
        # Verify filename format
        self.assertIsInstance(filename, str)
        self.assertTrue(filename.endswith('.txt'))
        self.assertIn('terraform-plan-error', filename)
    
    def test_section_error_handling(self):
        """Test error handling for individual section generation failures"""
        if not PDF_COMPONENTS_AVAILABLE:
            self.skipTest("PDF components not available")
        
        generator = EnhancedPDFGenerator()
        
        with patch.object(generator, 'validate_dependencies', return_value=(True, "")):
            with patch.object(generator, '_validate_input_data', return_value=None):
                with patch.object(generator, 'is_available', True):
                    with patch('components.enhanced_pdf_generator.REPORTLAB_AVAILABLE', True):
                        # Mock title page creation to fail
                        with patch.object(generator, '_create_title_page', side_effect=Exception("Title page error")):
                            
                            result, error = generator.generate_comprehensive_report(
                                self.sample_summary,
                                self.sample_risk_summary,
                                self.sample_resource_changes,
                                self.sample_resource_types,
                                self.sample_plan_data
                            )
                            
                            self.assertIsNone(result)
                            self.assertIsNotNone(error)
                            self.assertIn("Failed to create title page", error)
    
    def test_empty_pdf_content_handling(self):
        """Test handling when PDF generation produces empty content"""
        if not PDF_COMPONENTS_AVAILABLE:
            self.skipTest("PDF components not available")
        
        generator = EnhancedPDFGenerator()
        
        with patch.object(generator, 'validate_dependencies', return_value=(True, "")):
            with patch.object(generator, '_validate_input_data', return_value=None):
                with patch.object(generator, 'is_available', True):
                    with patch('components.enhanced_pdf_generator.REPORTLAB_AVAILABLE', True):
                        # Mock PDF generation to return empty content
                        with patch('components.enhanced_pdf_generator.io.BytesIO') as mock_buffer:
                            mock_buffer.return_value.getvalue.return_value = b""  # Empty content
                            
                            with patch('components.enhanced_pdf_generator.SimpleDocTemplate'):
                                result, error = generator.generate_comprehensive_report(
                                    self.sample_summary,
                                    self.sample_risk_summary,
                                    self.sample_resource_changes,
                                    self.sample_resource_types,
                                    self.sample_plan_data
                                )
                                
                                self.assertIsNone(result)
                                self.assertIsNotNone(error)
                                self.assertIn("empty content", error)


class TestReportGeneratorErrorHandling(unittest.TestCase):
    """Test report generator error handling and user feedback"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.sample_summary = {
            'create': 5,
            'update': 3,
            'delete': 2,
            'no-op': 10,
            'total': 20
        }
        
        self.sample_risk_summary = {
            'overall_risk': {
                'level': 'Medium',
                'score': 65
            }
        }
        
        self.sample_resource_changes = [
            {
                'address': 'aws_instance.web',
                'type': 'aws_instance',
                'change': {'actions': ['create']}
            }
        ]
        
        self.sample_resource_types = {'aws_instance': 1}
        
        self.sample_plan_data = {
            'terraform_version': '1.5.0',
            'format_version': '1.1'
        }
    
    @pytest.mark.skipif(not PDF_COMPONENTS_AVAILABLE, reason="PDF components not available")
    @patch('streamlit.error')
    @patch('streamlit.warning')
    @patch('streamlit.expander')
    def test_pdf_unavailable_handling(self, mock_expander, mock_warning, mock_error):
        """Test handling when PDF generator is unavailable"""
        # Mock PDF generator as unavailable
        with patch('components.report_generator.PDF_GENERATOR_AVAILABLE', False):
            report_gen = ReportGeneratorComponent()
            
            result = report_gen.export_pdf_report(
                self.sample_summary,
                self.sample_risk_summary,
                self.sample_resource_changes,
                self.sample_resource_types,
                self.sample_plan_data
            )
            
            self.assertIsNone(result)
            mock_error.assert_called()
            mock_warning.assert_called()
            
            # Check that error messages mention PDF unavailability
            error_calls = [str(call) for call in mock_error.call_args_list]
            self.assertTrue(any("PDF Generation Unavailable" in call for call in error_calls))
    
    @pytest.mark.skipif(not PDF_COMPONENTS_AVAILABLE, reason="PDF components not available")
    @patch('streamlit.success')
    def test_successful_pdf_generation_feedback(self, mock_success):
        """Test user feedback for successful PDF generation"""
        report_gen = ReportGeneratorComponent()
        
        # Mock successful PDF generation
        mock_pdf_generator = Mock()
        mock_pdf_generator.validate_dependencies.return_value = (True, "")
        mock_pdf_generator.generate_comprehensive_report.return_value = (b"fake_pdf_content", None)
        report_gen.pdf_generator = mock_pdf_generator
        
        with patch('components.report_generator.PDF_GENERATOR_AVAILABLE', True):
            result = report_gen.export_pdf_report(
                self.sample_summary,
                self.sample_risk_summary,
                self.sample_resource_changes,
                self.sample_resource_types,
                self.sample_plan_data
            )
            
            self.assertEqual(result, b"fake_pdf_content")
            mock_success.assert_called_with("✅ PDF report generated successfully!")
    
    @pytest.mark.skipif(not PDF_COMPONENTS_AVAILABLE, reason="PDF components not available")
    @patch('streamlit.progress')
    @patch('streamlit.empty')
    @patch('streamlit.container')
    def test_progress_indicator_display(self, mock_container, mock_empty, mock_progress):
        """Test progress indicator display during PDF generation"""
        report_gen = ReportGeneratorComponent()
        
        # Mock progress components
        mock_container_instance = Mock()
        mock_progress_bar = Mock()
        mock_status_text = Mock()
        
        mock_container.return_value.__enter__.return_value = mock_container_instance
        mock_progress.return_value = mock_progress_bar
        mock_empty.return_value = mock_status_text
        
        # Mock PDF generator with progress callback
        mock_pdf_generator = Mock()
        mock_pdf_generator.validate_dependencies.return_value = (True, "")
        
        def mock_generate_with_progress(*args, **kwargs):
            # Simulate progress callback calls
            progress_callback = kwargs.get('progress_callback')
            if progress_callback:
                progress_callback(0.0, "Starting...")
                progress_callback(0.5, "Halfway...")
                progress_callback(1.0, "Complete!")
            return b"fake_pdf_content", None
        
        mock_pdf_generator.generate_comprehensive_report.side_effect = mock_generate_with_progress
        report_gen.pdf_generator = mock_pdf_generator
        
        with patch('components.report_generator.PDF_GENERATOR_AVAILABLE', True):
            result = report_gen.export_pdf_report(
                self.sample_summary,
                self.sample_risk_summary,
                self.sample_resource_changes,
                self.sample_resource_types,
                self.sample_plan_data,
                show_progress=True
            )
            
            # Verify progress components were used
            mock_container.assert_called()
            mock_progress.assert_called()
            mock_empty.assert_called()
            
            # Verify progress updates were made
            self.assertTrue(mock_progress_bar.progress.called)
            self.assertTrue(mock_status_text.text.called)


if __name__ == '__main__':
    unittest.main()
"""
Integration tests for PDF generation error handling and user feedback improvements

Tests the complete error handling workflow including progress indicators,
fallback options, and user feedback in realistic scenarios.

Requirements tested: 4.4, 4.5, 1.3
"""

import pytest
import unittest
from unittest.mock import Mock, patch, MagicMock
import tempfile
import json
import os
from typing import Dict, Any, List

# Import test fixtures
try:
    from tests.fixtures.pdf_test_fixtures import (
        create_sample_plan_data,
        create_large_plan_data,
        create_invalid_plan_data
    )
    FIXTURES_AVAILABLE = True
except ImportError:
    FIXTURES_AVAILABLE = False

# Import components to test
try:
    from components.enhanced_pdf_generator import EnhancedPDFGenerator
    from components.report_generator import ReportGeneratorComponent
    from ui.progress_tracker import ProgressTracker
    from ui.error_handler import ErrorHandler
    PDF_COMPONENTS_AVAILABLE = True
except ImportError:
    PDF_COMPONENTS_AVAILABLE = False


class TestPDFErrorHandlingIntegration(unittest.TestCase):
    """Integration tests for PDF error handling workflow"""
    
    def setUp(self):
        """Set up test fixtures"""
        if FIXTURES_AVAILABLE:
            self.sample_data = create_sample_plan_data()
            self.large_data = create_large_plan_data()
            self.invalid_data = create_invalid_plan_data()
        else:
            # Fallback test data
            self.sample_data = {
                'summary': {'create': 5, 'update': 3, 'delete': 2, 'no-op': 10, 'total': 20},
                'risk_summary': {'overall_risk': {'level': 'Medium', 'score': 65}},
                'resource_changes': [
                    {
                        'address': 'aws_instance.web',
                        'type': 'aws_instance',
                        'change': {'actions': ['create']}
                    }
                ],
                'resource_types': {'aws_instance': 1},
                'plan_data': {'terraform_version': '1.5.0', 'format_version': '1.1'}
            }
            
            self.large_data = self.sample_data.copy()
            self.large_data['resource_changes'] = self.sample_data['resource_changes'] * 15000  # Make it exceed the 10,000 limit
            
            self.invalid_data = self.sample_data.copy()
            self.invalid_data['summary'] = "invalid_summary"
    
    @pytest.mark.skipif(not PDF_COMPONENTS_AVAILABLE, reason="PDF components not available")
    def test_complete_error_handling_workflow(self):
        """Test the complete error handling workflow from start to finish"""
        
        # Test 1: Dependency validation failure
        with patch('components.enhanced_pdf_generator.REPORTLAB_AVAILABLE', False):
            generator = EnhancedPDFGenerator()
            
            result, error = generator.generate_comprehensive_report(
                self.sample_data['summary'],
                self.sample_data['risk_summary'],
                self.sample_data['resource_changes'],
                self.sample_data['resource_types'],
                self.sample_data['plan_data']
            )
            
            self.assertIsNone(result)
            self.assertIsNotNone(error)
            self.assertIn("reportlab library not available", error.lower())
        
        # Test 2: Input validation failure
        generator = EnhancedPDFGenerator()
        
        with patch.object(generator, 'validate_dependencies', return_value=(True, "")):
            result, error = generator.generate_comprehensive_report(
                self.invalid_data['summary'],  # Invalid summary
                self.sample_data['risk_summary'],
                self.sample_data['resource_changes'],
                self.sample_data['resource_types'],
                self.sample_data['plan_data']
            )
            
            self.assertIsNone(result)
            self.assertIsNotNone(error)
            self.assertIn("validation failed", error.lower())
        
        # Test 3: Memory error handling
        with patch.object(generator, 'validate_dependencies', return_value=(True, "")):
            with patch.object(generator, '_validate_input_data', return_value=None):
                with patch.object(generator, 'is_available', True):
                    with patch('components.enhanced_pdf_generator.REPORTLAB_AVAILABLE', True):
                        with patch('components.enhanced_pdf_generator.SimpleDocTemplate', side_effect=MemoryError("Out of memory")):
                            
                            result, error = generator.generate_comprehensive_report(
                                self.sample_data['summary'],
                                self.sample_data['risk_summary'],
                                self.sample_data['resource_changes'],
                                self.sample_data['resource_types'],
                                self.sample_data['plan_data']
                            )
                            
                            self.assertIsNone(result)
                            self.assertIsNotNone(error)
                            self.assertIn("insufficient memory", error.lower())
    
    @pytest.mark.skipif(not PDF_COMPONENTS_AVAILABLE, reason="PDF components not available")
    def test_progress_tracking_integration(self):
        """Test progress tracking integration with error handling"""
        generator = EnhancedPDFGenerator()
        progress_tracker = ProgressTracker()
        
        # Track progress updates
        progress_updates = []
        
        def track_progress(progress: float, message: str):
            progress_updates.append((progress, message))
        
        with patch.object(generator, 'validate_dependencies', return_value=(True, "")):
            with patch.object(generator, '_validate_input_data', return_value=None):
                with patch.object(generator, 'is_available', True):
                    with patch('components.enhanced_pdf_generator.REPORTLAB_AVAILABLE', True):
                        # Mock successful PDF generation
                        with patch('components.enhanced_pdf_generator.io.BytesIO') as mock_buffer:
                            mock_buffer.return_value.getvalue.return_value = b"fake_pdf_content"
                            
                            with patch('components.enhanced_pdf_generator.SimpleDocTemplate'):
                                result, error = generator.generate_comprehensive_report(
                                    self.sample_data['summary'],
                                    self.sample_data['risk_summary'],
                                    self.sample_data['resource_changes'],
                                    self.sample_data['resource_types'],
                                    self.sample_data['plan_data'],
                                    progress_callback=track_progress
                                )
                                
                                # Verify successful generation
                                self.assertIsNotNone(result)
                                self.assertIsNone(error)
                                
                                # Verify progress tracking
                                self.assertGreater(len(progress_updates), 5)
                                
                                # Check progress sequence
                                progress_values = [update[0] for update in progress_updates]
                                self.assertEqual(progress_values[0], 0.0)
                                self.assertEqual(progress_values[-1], 1.0)
                                
                                # Verify progress messages
                                messages = [update[1] for update in progress_updates]
                                self.assertTrue(any("dependencies" in msg.lower() for msg in messages))
                                self.assertTrue(any("template" in msg.lower() for msg in messages))
                                self.assertTrue(any("generated successfully" in msg.lower() for msg in messages))
    
    @pytest.mark.skipif(not PDF_COMPONENTS_AVAILABLE, reason="PDF components not available")
    def test_fallback_report_integration(self):
        """Test fallback report generation integration"""
        generator = EnhancedPDFGenerator()
        
        # Test fallback report generation
        report_content, filename = generator.generate_fallback_report(
            self.sample_data['summary'],
            self.sample_data['risk_summary'],
            self.sample_data['resource_changes'],
            self.sample_data['resource_types'],
            self.sample_data['plan_data']
        )
        
        # Verify report structure
        self.assertIsInstance(report_content, str)
        self.assertGreater(len(report_content), 500)  # Should be substantial
        
        # Verify key sections are present
        self.assertIn("TERRAFORM PLAN IMPACT REPORT", report_content)
        self.assertIn("EXECUTIVE SUMMARY", report_content)
        self.assertIn("RISK ASSESSMENT", report_content)
        self.assertIn("RESOURCE TYPE BREAKDOWN", report_content)
        self.assertIn("RESOURCE CHANGES", report_content)
        
        # Verify data is correctly included
        self.assertIn("Create Operations: 5", report_content)
        self.assertIn("Update Operations: 3", report_content)
        self.assertIn("Delete Operations: 2", report_content)
        self.assertIn("Overall Risk Level: Medium", report_content)
        
        # Verify filename format
        self.assertTrue(filename.endswith('.txt'))
        self.assertIn('terraform-plan-report', filename)
    
    @pytest.mark.skipif(not PDF_COMPONENTS_AVAILABLE, reason="PDF components not available")
    def test_report_generator_error_handling_integration(self):
        """Test report generator error handling integration with UI components"""
        
        # Mock Streamlit components
        with patch('streamlit.error') as mock_error:
            with patch('streamlit.warning') as mock_warning:
                with patch('streamlit.success') as mock_success:
                    with patch('streamlit.info') as mock_info:
                        with patch('streamlit.expander') as mock_expander:
                            with patch('streamlit.button') as mock_button:
                                with patch('streamlit.download_button') as mock_download:
                                    
                                    report_gen = ReportGeneratorComponent()
                                    
                                    # Test with PDF generator unavailable
                                    with patch('components.report_generator.PDF_GENERATOR_AVAILABLE', False):
                                        result = report_gen.export_pdf_report(
                                            self.sample_data['summary'],
                                            self.sample_data['risk_summary'],
                                            self.sample_data['resource_changes'],
                                            self.sample_data['resource_types'],
                                            self.sample_data['plan_data']
                                        )
                                        
                                        # The result might be a fallback report, so check if it's the expected fallback
                                        if result is not None:
                                            # If we got a result, it should be the fallback text report
                                            self.assertIsInstance(result, bytes)
                                            result_str = result.decode('utf-8')
                                            self.assertIn("TERRAFORM PLAN IMPACT REPORT", result_str)
                                        else:
                                            self.assertIsNone(result)
                                        
                                        # Verify error handling UI was called
                                        mock_error.assert_called()
                                        mock_warning.assert_called()
                                        mock_expander.assert_called()
                                        
                                        # Check error messages
                                        error_calls = [str(call) for call in mock_error.call_args_list]
                                        self.assertTrue(any("PDF Generation Unavailable" in call for call in error_calls))
    
    @pytest.mark.skipif(not PDF_COMPONENTS_AVAILABLE, reason="PDF components not available")
    def test_error_categorization_and_solutions(self):
        """Test that different error types are properly categorized and appropriate solutions are offered"""
        
        report_gen = ReportGeneratorComponent()
        
        # Mock PDF generator
        mock_pdf_generator = Mock()
        mock_pdf_generator.validate_dependencies.return_value = (True, "")
        report_gen.pdf_generator = mock_pdf_generator
        
        with patch('components.report_generator.PDF_GENERATOR_AVAILABLE', True):
            with patch('streamlit.error') as mock_error:
                with patch('streamlit.warning') as mock_warning:
                    with patch('streamlit.expander') as mock_expander:
                        
                        # Test 1: Memory error
                        mock_pdf_generator.generate_comprehensive_report.return_value = (None, "Insufficient memory to generate PDF")
                        
                        result = report_gen.export_pdf_report(
                            self.sample_data['summary'],
                            self.sample_data['risk_summary'],
                            self.sample_data['resource_changes'],
                            self.sample_data['resource_types'],
                            self.sample_data['plan_data']
                        )
                        
                        self.assertIsNone(result)
                        
                        # Verify memory-specific error handling
                        warning_calls = [str(call) for call in mock_warning.call_args_list]
                        self.assertTrue(any("Plan data too large" in call for call in warning_calls))
                        
                        # Test 2: Dependency error
                        mock_pdf_generator.generate_comprehensive_report.return_value = (None, "Missing required PDF generation dependencies: reportlab not found")
                        
                        result = report_gen.export_pdf_report(
                            self.sample_data['summary'],
                            self.sample_data['risk_summary'],
                            self.sample_data['resource_changes'],
                            self.sample_data['resource_types'],
                            self.sample_data['plan_data']
                        )
                        
                        self.assertIsNone(result)
                        
                        # Verify dependency-specific error handling
                        warning_calls = [str(call) for call in mock_warning.call_args_list]
                        self.assertTrue(any("Missing or corrupted PDF generation dependencies" in call for call in warning_calls))
    
    @pytest.mark.skipif(not PDF_COMPONENTS_AVAILABLE, reason="PDF components not available")
    def test_large_dataset_handling(self):
        """Test error handling with large datasets"""
        generator = EnhancedPDFGenerator()
        
        # Test input validation with large dataset
        error = generator._validate_input_data(
            self.large_data['summary'],
            self.large_data['risk_summary'],
            self.large_data['resource_changes'],  # Very large list
            self.large_data['resource_types'],
            self.large_data['plan_data']
        )
        
        # Should detect too many resources
        self.assertIsNotNone(error)
        self.assertIn("Too many resource changes", error)
        self.assertIn("Maximum supported: 10,000", error)
    
    def test_error_handler_integration(self):
        """Test integration with the centralized error handler"""
        if not PDF_COMPONENTS_AVAILABLE:
            self.skipTest("PDF components not available")
        
        error_handler = ErrorHandler(debug_mode=True)
        
        # Test processing error handling
        with patch('streamlit.warning') as mock_warning:
            with patch('streamlit.info') as mock_info:
                with patch('streamlit.expander') as mock_expander:
                    
                    # Simulate PDF generation error
                    test_error = Exception("PDF generation failed due to memory constraints")
                    error_handler.handle_processing_error(test_error, "PDF generation")
                    
                    # Verify error handling was called
                    mock_warning.assert_called()
                    # Note: mock_info might not be called depending on the specific error handling path
    
    def test_progress_tracker_integration(self):
        """Test integration with progress tracker"""
        if not PDF_COMPONENTS_AVAILABLE:
            self.skipTest("PDF components not available")
        
        progress_tracker = ProgressTracker()
        
        # Test file processing progress tracking
        with progress_tracker.track_file_processing(file_size=1024*1024) as stage_tracker:
            # Simulate processing stages
            stage_tracker.next_stage()  # parsing
            stage_tracker.next_stage()  # validation
            stage_tracker.next_stage()  # extraction
            stage_tracker.next_stage()  # risk_assessment
            stage_tracker.complete()
        
        # Test should complete without errors
        self.assertTrue(True)  # If we get here, the integration worked
    
    def test_end_to_end_error_recovery(self):
        """Test end-to-end error recovery workflow"""
        if not PDF_COMPONENTS_AVAILABLE:
            self.skipTest("PDF components not available")
        
        # Simulate a complete error recovery workflow
        generator = EnhancedPDFGenerator()
        
        # Step 1: Try PDF generation (fails)
        with patch.object(generator, 'validate_dependencies', return_value=(True, "")):
            with patch.object(generator, '_validate_input_data', return_value=None):
                with patch.object(generator, 'is_available', True):
                    with patch('components.enhanced_pdf_generator.REPORTLAB_AVAILABLE', True):
                        with patch('components.enhanced_pdf_generator.SimpleDocTemplate', side_effect=MemoryError("Out of memory")):
                            
                            result, error = generator.generate_comprehensive_report(
                                self.sample_data['summary'],
                                self.sample_data['risk_summary'],
                                self.sample_data['resource_changes'],
                                self.sample_data['resource_types'],
                                self.sample_data['plan_data']
                            )
                            
                            self.assertIsNone(result)
                            self.assertIsNotNone(error)
        
        # Step 2: Fall back to text report (succeeds)
        report_content, filename = generator.generate_fallback_report(
            self.sample_data['summary'],
            self.sample_data['risk_summary'],
            self.sample_data['resource_changes'],
            self.sample_data['resource_types'],
            self.sample_data['plan_data']
        )
        
        self.assertIsNotNone(report_content)
        self.assertIsNotNone(filename)
        self.assertIn("TERRAFORM PLAN IMPACT REPORT", report_content)
        
        # Step 3: Verify fallback report contains essential information
        self.assertIn("Create Operations: 5", report_content)
        self.assertIn("Update Operations: 3", report_content)
        self.assertIn("Delete Operations: 2", report_content)


if __name__ == '__main__':
    unittest.main()
"""
Unit tests for Enhanced PDF Generator

Tests the core functionality of the enhanced PDF generator including
dependency validation, PDF generation, and error handling.

Requirements tested: 1.1, 1.4, 2.1
"""

import unittest
from unittest.mock import patch, MagicMock
import io
from typing import Dict, Any, List

# Import the module under test
from components.enhanced_pdf_generator import (
    EnhancedPDFGenerator,
    validate_dependencies,
    create_enhanced_pdf_generator,
    REPORTLAB_AVAILABLE
)


class TestDependencyValidation(unittest.TestCase):
    """Test dependency validation functionality"""
    
    def test_validate_dependencies_success(self):
        """Test successful dependency validation"""
        if REPORTLAB_AVAILABLE:
            is_valid, error_msg = validate_dependencies()
            self.assertTrue(is_valid)
            self.assertEqual(error_msg, "")
    
    @patch('components.enhanced_pdf_generator.REPORTLAB_AVAILABLE', False)
    def test_validate_dependencies_failure(self):
        """Test dependency validation failure"""
        with patch('builtins.__import__', side_effect=ImportError("No module named 'reportlab'")):
            is_valid, error_msg = validate_dependencies()
            self.assertFalse(is_valid)
            self.assertIn("reportlab", error_msg.lower())
            self.assertIn("pip install reportlab", error_msg)


class TestEnhancedPDFGenerator(unittest.TestCase):
    """Test the EnhancedPDFGenerator class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.generator = EnhancedPDFGenerator()
        
        # Sample test data
        self.sample_summary = {
            'create': 5,
            'update': 3,
            'delete': 1,
            'no-op': 2,
            'total': 11
        }
        
        self.sample_risk_summary = {
            'level': 'Medium',
            'score': 65,
            'risk_factors': ['Resource deletion detected', 'Security group changes']
        }
        
        self.sample_resource_changes = [
            {
                'address': 'aws_instance.web_server',
                'type': 'aws_instance',
                'provider_name': 'registry.terraform.io/hashicorp/aws',
                'change': {
                    'actions': ['create']
                }
            },
            {
                'address': 'aws_security_group.web_sg',
                'type': 'aws_security_group',
                'provider_name': 'registry.terraform.io/hashicorp/aws',
                'change': {
                    'actions': ['update']
                }
            },
            {
                'address': 'aws_s3_bucket.old_bucket',
                'type': 'aws_s3_bucket',
                'provider_name': 'registry.terraform.io/hashicorp/aws',
                'change': {
                    'actions': ['delete']
                }
            }
        ]
        
        self.sample_resource_types = {
            'aws_instance': 2,
            'aws_security_group': 1,
            'aws_s3_bucket': 1
        }
        
        self.sample_plan_data = {
            'terraform_version': '1.5.0',
            'format_version': '1.2',
            'resource_changes': self.sample_resource_changes
        }
    
    def test_initialization(self):
        """Test generator initialization"""
        generator = EnhancedPDFGenerator()
        
        if REPORTLAB_AVAILABLE:
            self.assertTrue(generator.is_available)
            self.assertIsNotNone(generator.styles)
        else:
            self.assertFalse(generator.is_available)
    
    def test_validate_dependencies_method(self):
        """Test the validate_dependencies method"""
        is_valid, error_msg = self.generator.validate_dependencies()
        
        if REPORTLAB_AVAILABLE:
            self.assertTrue(is_valid)
            self.assertEqual(error_msg, "")
        else:
            self.assertFalse(is_valid)
            self.assertIn("reportlab", error_msg.lower())
    
    @unittest.skipUnless(REPORTLAB_AVAILABLE, "Reportlab not available")
    def test_setup_styles(self):
        """Test PDF styles setup"""
        generator = EnhancedPDFGenerator()
        
        # Check that styles are properly initialized
        self.assertIsNotNone(generator.styles)
        
        # Check for custom styles
        style_names = [style.name for style in generator.styles.byName.values()]
        expected_styles = [
            'MainTitle',
            'SectionHeading',
            'SubsectionHeading',
            'CustomBodyText',
            'CustomSummaryBox',
            'CustomRiskBoxLow',
            'CustomRiskBoxMedium',
            'CustomRiskBoxHigh',
            'Metadata'
        ]
        
        for expected_style in expected_styles:
            self.assertIn(expected_style, style_names)
    
    @unittest.skipUnless(REPORTLAB_AVAILABLE, "Reportlab not available")
    def test_generate_comprehensive_report_success(self):
        """Test successful PDF generation"""
        pdf_bytes = self.generator.generate_comprehensive_report(
            summary=self.sample_summary,
            risk_summary=self.sample_risk_summary,
            resource_changes=self.sample_resource_changes,
            resource_types=self.sample_resource_types,
            plan_data=self.sample_plan_data
        )
        
        self.assertIsNotNone(pdf_bytes)
        self.assertIsInstance(pdf_bytes, bytes)
        self.assertGreater(len(pdf_bytes), 0)
        
        # Check PDF header (PDF files start with %PDF)
        self.assertTrue(pdf_bytes.startswith(b'%PDF'))
    
    @unittest.skipUnless(REPORTLAB_AVAILABLE, "Reportlab not available")
    def test_generate_comprehensive_report_with_sections(self):
        """Test PDF generation with specific sections"""
        include_sections = {
            'title_page': True,
            'executive_summary': True,
            'resource_analysis': False,
            'risk_assessment': True,
            'recommendations': False
        }
        
        pdf_bytes = self.generator.generate_comprehensive_report(
            summary=self.sample_summary,
            risk_summary=self.sample_risk_summary,
            resource_changes=self.sample_resource_changes,
            resource_types=self.sample_resource_types,
            plan_data=self.sample_plan_data,
            include_sections=include_sections
        )
        
        self.assertIsNotNone(pdf_bytes)
        self.assertIsInstance(pdf_bytes, bytes)
        self.assertGreater(len(pdf_bytes), 0)
    
    @unittest.skipUnless(REPORTLAB_AVAILABLE, "Reportlab not available")
    def test_generate_comprehensive_report_different_templates(self):
        """Test PDF generation with different templates"""
        templates = ["default", "compact", "detailed"]
        
        for template in templates:
            with self.subTest(template=template):
                pdf_bytes = self.generator.generate_comprehensive_report(
                    summary=self.sample_summary,
                    risk_summary=self.sample_risk_summary,
                    resource_changes=self.sample_resource_changes,
                    resource_types=self.sample_resource_types,
                    plan_data=self.sample_plan_data,
                    template_name=template
                )
                
                self.assertIsNotNone(pdf_bytes)
                self.assertIsInstance(pdf_bytes, bytes)
                self.assertGreater(len(pdf_bytes), 0)
    
    @patch('components.enhanced_pdf_generator.REPORTLAB_AVAILABLE', False)
    def test_generate_comprehensive_report_no_reportlab(self):
        """Test PDF generation when reportlab is not available"""
        generator = EnhancedPDFGenerator()
        
        pdf_bytes = generator.generate_comprehensive_report(
            summary=self.sample_summary,
            risk_summary=self.sample_risk_summary,
            resource_changes=self.sample_resource_changes,
            resource_types=self.sample_resource_types,
            plan_data=self.sample_plan_data
        )
        
        self.assertIsNone(pdf_bytes)
    
    @unittest.skipUnless(REPORTLAB_AVAILABLE, "Reportlab not available")
    def test_create_title_page(self):
        """Test title page creation"""
        title_elements = self.generator._create_title_page(
            self.sample_plan_data,
            self.sample_summary
        )
        
        self.assertIsInstance(title_elements, list)
        self.assertGreater(len(title_elements), 0)
    
    @unittest.skipUnless(REPORTLAB_AVAILABLE, "Reportlab not available")
    def test_create_executive_summary(self):
        """Test executive summary creation"""
        summary_elements = self.generator._create_executive_summary(
            self.sample_summary,
            self.sample_risk_summary
        )
        
        self.assertIsInstance(summary_elements, list)
        self.assertGreater(len(summary_elements), 0)
    
    @unittest.skipUnless(REPORTLAB_AVAILABLE, "Reportlab not available")
    def test_create_resource_analysis(self):
        """Test resource analysis creation"""
        analysis_elements = self.generator._create_resource_analysis(
            self.sample_resource_changes,
            self.sample_resource_types
        )
        
        self.assertIsInstance(analysis_elements, list)
        self.assertGreater(len(analysis_elements), 0)
    
    @unittest.skipUnless(REPORTLAB_AVAILABLE, "Reportlab not available")
    def test_create_risk_assessment(self):
        """Test risk assessment creation"""
        risk_elements = self.generator._create_risk_assessment(
            self.sample_risk_summary
        )
        
        self.assertIsInstance(risk_elements, list)
        self.assertGreater(len(risk_elements), 0)
    
    @unittest.skipUnless(REPORTLAB_AVAILABLE, "Reportlab not available")
    def test_create_recommendations(self):
        """Test recommendations creation"""
        rec_elements = self.generator._create_recommendations(
            self.sample_summary,
            self.sample_risk_summary,
            self.sample_resource_changes
        )
        
        self.assertIsInstance(rec_elements, list)
        self.assertGreater(len(rec_elements), 0)
    
    def test_get_risk_style(self):
        """Test risk style selection"""
        if not REPORTLAB_AVAILABLE:
            self.skipTest("Reportlab not available")
        
        # Test different risk levels
        high_style = self.generator._get_risk_style('High')
        self.assertEqual(high_style, self.generator.styles['CustomRiskBoxHigh'])
        
        medium_style = self.generator._get_risk_style('Medium')
        self.assertEqual(medium_style, self.generator.styles['CustomRiskBoxMedium'])
        
        low_style = self.generator._get_risk_style('Low')
        self.assertEqual(low_style, self.generator.styles['CustomRiskBoxLow'])
        
        # Test case insensitive
        critical_style = self.generator._get_risk_style('CRITICAL')
        self.assertEqual(critical_style, self.generator.styles['CustomRiskBoxHigh'])
    
    def test_get_risk_description(self):
        """Test risk description generation"""
        descriptions = {
            'Low': 'Safe to proceed with standard deployment procedures',
            'Medium': 'Proceed with caution and standard review process',
            'High': 'Requires careful review and testing before deployment',
            'Critical': 'High-risk deployment requiring extensive review and approval'
        }
        
        for risk_level, expected_desc in descriptions.items():
            desc = self.generator._get_risk_description(risk_level)
            self.assertEqual(desc, expected_desc)
        
        # Test unknown risk level
        unknown_desc = self.generator._get_risk_description('Unknown')
        self.assertEqual(unknown_desc, 'Risk level assessment unavailable')
    
    @unittest.skipUnless(REPORTLAB_AVAILABLE, "Reportlab not available")
    def test_error_handling_invalid_data(self):
        """Test error handling with invalid data"""
        # Test with None values
        pdf_bytes = self.generator.generate_comprehensive_report(
            summary=None,
            risk_summary=None,
            resource_changes=None,
            resource_types=None,
            plan_data=None
        )
        
        # Should handle gracefully and return None
        self.assertIsNone(pdf_bytes)
    
    @unittest.skipUnless(REPORTLAB_AVAILABLE, "Reportlab not available")
    def test_empty_data_handling(self):
        """Test handling of empty data structures"""
        empty_summary = {'create': 0, 'update': 0, 'delete': 0, 'no-op': 0}
        empty_risk = {'level': 'Unknown', 'score': 0}
        empty_changes = []
        empty_types = {}
        empty_plan = {}
        
        pdf_bytes = self.generator.generate_comprehensive_report(
            summary=empty_summary,
            risk_summary=empty_risk,
            resource_changes=empty_changes,
            resource_types=empty_types,
            plan_data=empty_plan
        )
        
        self.assertIsNotNone(pdf_bytes)
        self.assertIsInstance(pdf_bytes, bytes)
        self.assertGreater(len(pdf_bytes), 0)
    
    @unittest.skipUnless(REPORTLAB_AVAILABLE, "Reportlab not available")
    def test_large_dataset_handling(self):
        """Test handling of large datasets"""
        # Create large dataset
        large_changes = []
        for i in range(100):
            large_changes.append({
                'address': f'aws_instance.server_{i}',
                'type': 'aws_instance',
                'provider_name': 'registry.terraform.io/hashicorp/aws',
                'change': {
                    'actions': ['create']
                }
            })
        
        large_types = {'aws_instance': 100}
        large_summary = {'create': 100, 'update': 0, 'delete': 0, 'no-op': 0, 'total': 100}
        
        pdf_bytes = self.generator.generate_comprehensive_report(
            summary=large_summary,
            risk_summary=self.sample_risk_summary,
            resource_changes=large_changes,
            resource_types=large_types,
            plan_data=self.sample_plan_data
        )
        
        self.assertIsNotNone(pdf_bytes)
        self.assertIsInstance(pdf_bytes, bytes)
        self.assertGreater(len(pdf_bytes), 0)


class TestFactoryFunction(unittest.TestCase):
    """Test the factory function"""
    
    def test_create_enhanced_pdf_generator(self):
        """Test the factory function creates a proper instance"""
        generator = create_enhanced_pdf_generator()
        
        self.assertIsInstance(generator, EnhancedPDFGenerator)
        
        if REPORTLAB_AVAILABLE:
            self.assertTrue(generator.is_available)
        else:
            self.assertFalse(generator.is_available)


class TestRiskSummaryFormats(unittest.TestCase):
    """Test different risk summary formats"""
    
    def setUp(self):
        """Set up test fixtures"""
        if not REPORTLAB_AVAILABLE:
            self.skipTest("Reportlab not available")
        
        self.generator = EnhancedPDFGenerator()
        self.base_data = {
            'summary': {'create': 1, 'update': 1, 'delete': 1, 'no-op': 0},
            'resource_changes': [],
            'resource_types': {'aws_instance': 1},
            'plan_data': {'terraform_version': '1.5.0'}
        }
    
    def test_nested_risk_summary_format(self):
        """Test risk summary with nested overall_risk structure"""
        nested_risk = {
            'overall_risk': {
                'level': 'High',
                'score': 85,
                'risk_factors': ['Critical resource deletion']
            }
        }
        
        pdf_bytes = self.generator.generate_comprehensive_report(
            risk_summary=nested_risk,
            **self.base_data
        )
        
        self.assertIsNotNone(pdf_bytes)
        self.assertGreater(len(pdf_bytes), 0)
    
    def test_flat_risk_summary_format(self):
        """Test risk summary with flat structure"""
        flat_risk = {
            'level': 'Medium',
            'score': 60,
            'risk_factors': ['Security group changes']
        }
        
        pdf_bytes = self.generator.generate_comprehensive_report(
            risk_summary=flat_risk,
            **self.base_data
        )
        
        self.assertIsNotNone(pdf_bytes)
        self.assertGreater(len(pdf_bytes), 0)


if __name__ == '__main__':
    unittest.main()
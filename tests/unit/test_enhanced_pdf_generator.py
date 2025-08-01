"""
Unit tests for Enhanced PDF Generator

Tests the core functionality of the enhanced PDF generator including
dependency validation, PDF generation, error handling, styling system,
and template functionality.

Requirements tested: 1.1, 1.4, 2.1, 2.2, 2.4, 3.5
"""

import unittest
from unittest.mock import patch, MagicMock
import io
from typing import Dict, Any, List

# Import the module under test
from components.enhanced_pdf_generator import (
    EnhancedPDFGenerator,
    PDFStyleConfig,
    PDFSectionConfig,
    PDFTemplateConfig,
    PDFTemplateManager,
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
            self.assertIsNotNone(generator.template_manager)
            # Styles are now set up when a template is selected, not during initialization
            self.assertIsNone(generator.styles)
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
        
        # Set up a template to trigger style initialization
        default_template = generator.template_manager.get_template("default")
        generator.current_template = default_template
        generator._setup_template_styles(default_template.style_config)
        
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
        # Set up template and styles first
        default_template = self.generator.template_manager.get_template("default")
        self.generator.current_template = default_template
        self.generator._setup_template_styles(default_template.style_config)
        
        title_elements = self.generator._create_title_page(
            self.sample_plan_data,
            self.sample_summary
        )
        
        self.assertIsInstance(title_elements, list)
        self.assertGreater(len(title_elements), 0)
        
        # Verify that title page contains expected elements
        # Should have header, title, metadata table, summary table, footer, and page break
        self.assertGreaterEqual(len(title_elements), 8)
    
    @unittest.skipUnless(REPORTLAB_AVAILABLE, "Reportlab not available")
    def test_create_title_page_with_empty_data(self):
        """Test title page creation with empty data"""
        # Set up template and styles first
        default_template = self.generator.template_manager.get_template("default")
        self.generator.current_template = default_template
        self.generator._setup_template_styles(default_template.style_config)
        
        empty_plan_data = {}
        empty_summary = {'create': 0, 'update': 0, 'delete': 0, 'no-op': 0}
        
        title_elements = self.generator._create_title_page(empty_plan_data, empty_summary)
        
        self.assertIsInstance(title_elements, list)
        self.assertGreater(len(title_elements), 0)
    
    @unittest.skipUnless(REPORTLAB_AVAILABLE, "Reportlab not available")
    def test_create_title_page_with_comprehensive_data(self):
        """Test title page creation with comprehensive data"""
        # Set up template and styles first
        default_template = self.generator.template_manager.get_template("default")
        self.generator.current_template = default_template
        self.generator._setup_template_styles(default_template.style_config)
        
        comprehensive_plan_data = {
            'terraform_version': '1.6.0',
            'format_version': '1.3',
            'resource_changes': [
                {'address': 'aws_instance.web1', 'type': 'aws_instance', 'change': {'actions': ['create']}},
                {'address': 'aws_instance.web2', 'type': 'aws_instance', 'change': {'actions': ['update']}},
                {'address': 'aws_s3_bucket.old', 'type': 'aws_s3_bucket', 'change': {'actions': ['delete']}},
            ]
        }
        
        comprehensive_summary = {
            'create': 10,
            'update': 5,
            'delete': 2,
            'no-op': 15,
            'total': 32
        }
        
        title_elements = self.generator._create_title_page(
            comprehensive_plan_data,
            comprehensive_summary
        )
        
        self.assertIsInstance(title_elements, list)
        self.assertGreater(len(title_elements), 0)
    
    @unittest.skipUnless(REPORTLAB_AVAILABLE, "Reportlab not available")
    def test_create_professional_header(self):
        """Test professional header creation"""
        # Set up template and styles first
        default_template = self.generator.template_manager.get_template("default")
        self.generator.current_template = default_template
        self.generator._setup_template_styles(default_template.style_config)
        
        header_elements = self.generator._create_professional_header()
        
        self.assertIsInstance(header_elements, list)
        self.assertGreater(len(header_elements), 0)
        # Should contain header table and spacer
        self.assertGreaterEqual(len(header_elements), 2)
    
    @unittest.skipUnless(REPORTLAB_AVAILABLE, "Reportlab not available")
    def test_create_professional_footer(self):
        """Test professional footer creation"""
        # Set up template and styles first
        default_template = self.generator.template_manager.get_template("default")
        self.generator.current_template = default_template
        self.generator._setup_template_styles(default_template.style_config)
        
        footer_elements = self.generator._create_professional_footer()
        
        self.assertIsInstance(footer_elements, list)
        self.assertGreater(len(footer_elements), 0)
        # Should contain spacer, paragraph, spacer, and footer table
        self.assertGreaterEqual(len(footer_elements), 4)
    
    def test_generate_config_hash(self):
        """Test configuration hash generation"""
        plan_data = {
            'terraform_version': '1.5.0',
            'resource_changes': [{'test': 'data'}]
        }
        
        config_hash = self.generator._generate_config_hash(plan_data)
        
        self.assertIsInstance(config_hash, str)
        self.assertEqual(len(config_hash), 8)
        self.assertTrue(config_hash.isupper())
        
        # Test with empty data
        empty_hash = self.generator._generate_config_hash({})
        self.assertIsInstance(empty_hash, str)
        self.assertEqual(len(empty_hash), 8)
        
        # Test consistency - same input should produce same hash
        same_hash = self.generator._generate_config_hash(plan_data)
        self.assertEqual(config_hash, same_hash)
    
    def test_get_impact_level(self):
        """Test impact level determination for different change types"""
        test_cases = [
            ('create', 'Low'),
            ('update', 'Medium'),
            ('delete', 'High'),
            ('no-op', 'None'),
            ('unknown_type', 'Unknown')
        ]
        
        for change_type, expected_impact in test_cases:
            with self.subTest(change_type=change_type):
                impact = self.generator._get_impact_level(change_type)
                self.assertEqual(impact, expected_impact)
    
    @unittest.skipUnless(REPORTLAB_AVAILABLE, "Reportlab not available")
    def test_title_page_metadata_completeness(self):
        """Test that title page includes all required metadata"""
        # Set up template and styles first
        default_template = self.generator.template_manager.get_template("default")
        self.generator.current_template = default_template
        self.generator._setup_template_styles(default_template.style_config)
        
        plan_data_with_version = {
            'terraform_version': '1.5.0',
            'format_version': '1.2',
            'resource_changes': [
                {'address': 'test.resource', 'type': 'test_resource'}
            ]
        }
        
        summary_with_changes = {
            'create': 3,
            'update': 2,
            'delete': 1,
            'no-op': 5,
            'total': 11
        }
        
        title_elements = self.generator._create_title_page(
            plan_data_with_version,
            summary_with_changes
        )
        
        # Verify we have all expected elements
        self.assertIsInstance(title_elements, list)
        self.assertGreater(len(title_elements), 5)
        
        # The last element should be a PageBreak
        from reportlab.platypus import PageBreak
        self.assertIsInstance(title_elements[-1], PageBreak)
    
    @unittest.skipUnless(REPORTLAB_AVAILABLE, "Reportlab not available")
    def test_title_page_with_different_templates(self):
        """Test title page generation with different templates"""
        templates = ["default", "compact", "detailed"]
        
        for template_name in templates:
            with self.subTest(template=template_name):
                template = self.generator.template_manager.get_template(template_name)
                self.generator.current_template = template
                self.generator._setup_template_styles(template.style_config)
                
                title_elements = self.generator._create_title_page(
                    self.sample_plan_data,
                    self.sample_summary
                )
                
                self.assertIsInstance(title_elements, list)
                self.assertGreater(len(title_elements), 0)
    
    @unittest.skipUnless(REPORTLAB_AVAILABLE, "Reportlab not available")
    def test_title_page_timestamp_format(self):
        """Test that title page includes properly formatted timestamp"""
        # Set up template and styles first
        default_template = self.generator.template_manager.get_template("default")
        self.generator.current_template = default_template
        self.generator._setup_template_styles(default_template.style_config)
        
        # Mock datetime to test timestamp format
        with patch('components.enhanced_pdf_generator.datetime') as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = "2024-01-15 14:30:45"
            
            title_elements = self.generator._create_title_page(
                self.sample_plan_data,
                self.sample_summary
            )
            
            # Verify datetime.now() was called for timestamp generation
            mock_datetime.now.assert_called()
            self.assertIsInstance(title_elements, list)
            self.assertGreater(len(title_elements), 0)
    
    @unittest.skipUnless(REPORTLAB_AVAILABLE, "Reportlab not available")
    def test_create_executive_summary(self):
        """Test executive summary creation"""
        # Set up template and styles first
        default_template = self.generator.template_manager.get_template("default")
        self.generator.current_template = default_template
        self.generator._setup_template_styles(default_template.style_config)
        
        summary_elements = self.generator._create_executive_summary(
            self.sample_summary,
            self.sample_risk_summary
        )
        
        self.assertIsInstance(summary_elements, list)
        self.assertGreater(len(summary_elements), 0)
    
    @unittest.skipUnless(REPORTLAB_AVAILABLE, "Reportlab not available")
    def test_create_resource_analysis(self):
        """Test resource analysis creation"""
        # Set up template and styles first
        default_template = self.generator.template_manager.get_template("default")
        self.generator.current_template = default_template
        self.generator._setup_template_styles(default_template.style_config)
        
        analysis_elements = self.generator._create_resource_analysis(
            self.sample_resource_changes,
            self.sample_resource_types
        )
        
        self.assertIsInstance(analysis_elements, list)
        self.assertGreater(len(analysis_elements), 0)
    
    @unittest.skipUnless(REPORTLAB_AVAILABLE, "Reportlab not available")
    def test_create_risk_assessment(self):
        """Test risk assessment creation"""
        # Set up template and styles first
        default_template = self.generator.template_manager.get_template("default")
        self.generator.current_template = default_template
        self.generator._setup_template_styles(default_template.style_config)
        
        risk_elements = self.generator._create_risk_assessment(
            self.sample_risk_summary
        )
        
        self.assertIsInstance(risk_elements, list)
        self.assertGreater(len(risk_elements), 0)
    
    @unittest.skipUnless(REPORTLAB_AVAILABLE, "Reportlab not available")
    def test_create_recommendations(self):
        """Test recommendations creation"""
        # Set up template and styles first
        default_template = self.generator.template_manager.get_template("default")
        self.generator.current_template = default_template
        self.generator._setup_template_styles(default_template.style_config)
        
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
        
        # Set up template and styles first
        default_template = self.generator.template_manager.get_template("default")
        self.generator.current_template = default_template
        self.generator._setup_template_styles(default_template.style_config)
        
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


class TestPDFStyleConfig(unittest.TestCase):
    """Test PDF style configuration"""
    
    def test_default_style_config(self):
        """Test default style configuration values"""
        config = PDFStyleConfig()
        
        self.assertEqual(config.primary_color, "#1f77b4")
        self.assertEqual(config.secondary_color, "#2c3e50")
        self.assertEqual(config.accent_color, "#3498db")
        self.assertEqual(config.font_family, "Helvetica")
        self.assertEqual(config.page_size, "A4")
        self.assertIsInstance(config.margins, dict)
        self.assertEqual(config.margins["top"], 72)
    
    def test_custom_style_config(self):
        """Test custom style configuration"""
        custom_margins = {"top": 50, "bottom": 50, "left": 50, "right": 50}
        config = PDFStyleConfig(
            primary_color="#ff0000",
            font_family="Times-Roman",
            page_size="LETTER",
            margins=custom_margins
        )
        
        self.assertEqual(config.primary_color, "#ff0000")
        self.assertEqual(config.font_family, "Times-Roman")
        self.assertEqual(config.page_size, "LETTER")
        self.assertEqual(config.margins, custom_margins)


class TestPDFSectionConfig(unittest.TestCase):
    """Test PDF section configuration"""
    
    def test_default_section_config(self):
        """Test default section configuration"""
        config = PDFSectionConfig()
        
        self.assertTrue(config.title_page)
        self.assertTrue(config.executive_summary)
        self.assertTrue(config.resource_analysis)
        self.assertTrue(config.risk_assessment)
        self.assertTrue(config.recommendations)
        self.assertFalse(config.appendix)
    
    def test_custom_section_config(self):
        """Test custom section configuration"""
        config = PDFSectionConfig(
            title_page=False,
            appendix=True,
            risk_assessment=False
        )
        
        self.assertFalse(config.title_page)
        self.assertTrue(config.appendix)
        self.assertFalse(config.risk_assessment)


class TestPDFTemplateConfig(unittest.TestCase):
    """Test PDF template configuration"""
    
    def test_template_config_creation(self):
        """Test template configuration creation"""
        style_config = PDFStyleConfig(primary_color="#123456")
        section_config = PDFSectionConfig(appendix=True)
        
        template = PDFTemplateConfig(
            name="test_template",
            style_config=style_config,
            section_config=section_config,
            compact_mode=True,
            max_resources_shown=15
        )
        
        self.assertEqual(template.name, "test_template")
        self.assertEqual(template.style_config.primary_color, "#123456")
        self.assertTrue(template.section_config.appendix)
        self.assertTrue(template.compact_mode)
        self.assertEqual(template.max_resources_shown, 15)


class TestPDFTemplateManager(unittest.TestCase):
    """Test PDF template manager"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.manager = PDFTemplateManager()
    
    def test_default_templates_creation(self):
        """Test that default templates are created properly"""
        templates = self.manager.get_available_templates()
        
        expected_templates = ["default", "compact", "detailed"]
        for template_name in expected_templates:
            self.assertIn(template_name, templates)
    
    def test_get_template_default(self):
        """Test getting default template"""
        template = self.manager.get_template("default")
        
        self.assertEqual(template.name, "default")
        self.assertFalse(template.compact_mode)
        self.assertFalse(template.detailed_mode)
        self.assertEqual(template.max_resources_shown, 20)
    
    def test_get_template_compact(self):
        """Test getting compact template"""
        template = self.manager.get_template("compact")
        
        self.assertEqual(template.name, "compact")
        self.assertTrue(template.compact_mode)
        self.assertFalse(template.detailed_mode)
        self.assertEqual(template.max_resources_shown, 10)
        self.assertFalse(template.section_config.risk_assessment)
        self.assertFalse(template.section_config.recommendations)
    
    def test_get_template_detailed(self):
        """Test getting detailed template"""
        template = self.manager.get_template("detailed")
        
        self.assertEqual(template.name, "detailed")
        self.assertFalse(template.compact_mode)
        self.assertTrue(template.detailed_mode)
        self.assertEqual(template.max_resources_shown, 50)
        self.assertTrue(template.section_config.appendix)
    
    def test_get_nonexistent_template(self):
        """Test getting non-existent template returns default"""
        template = self.manager.get_template("nonexistent")
        
        self.assertEqual(template.name, "default")
    
    def test_get_available_templates(self):
        """Test getting list of available templates"""
        templates = self.manager.get_available_templates()
        
        self.assertIsInstance(templates, list)
        self.assertIn("default", templates)
        self.assertIn("compact", templates)
        self.assertIn("detailed", templates)


class TestEnhancedPDFGeneratorTemplates(unittest.TestCase):
    """Test enhanced PDF generator template functionality"""
    
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
            'risk_factors': ['Resource deletion detected']
        }
        
        self.sample_resource_changes = [
            {
                'address': 'aws_instance.web_server',
                'type': 'aws_instance',
                'provider_name': 'registry.terraform.io/hashicorp/aws',
                'change': {'actions': ['create']}
            }
        ]
        
        self.sample_resource_types = {'aws_instance': 1}
        
        self.sample_plan_data = {
            'terraform_version': '1.5.0',
            'format_version': '1.2',
            'resource_changes': self.sample_resource_changes,
            'variables': {
                'instance_type': {'value': 't2.micro'},
                'region': {'value': 'us-west-2'}
            },
            'configuration': {
                'provider_config': {
                    'aws': {'name': 'aws'}
                }
            }
        }
    
    def test_template_manager_initialization(self):
        """Test that template manager is properly initialized"""
        self.assertIsNotNone(self.generator.template_manager)
        self.assertIsInstance(self.generator.template_manager, PDFTemplateManager)
    
    def test_get_available_templates(self):
        """Test getting available templates"""
        templates = self.generator.get_available_templates()
        
        self.assertIsInstance(templates, list)
        self.assertIn("default", templates)
        self.assertIn("compact", templates)
        self.assertIn("detailed", templates)
    
    def test_get_template_info(self):
        """Test getting template information"""
        info = self.generator.get_template_info("default")
        
        self.assertIsInstance(info, dict)
        self.assertEqual(info['name'], "default")
        self.assertIn('sections', info)
        self.assertIn('style', info)
        self.assertFalse(info['compact_mode'])
        self.assertFalse(info['detailed_mode'])
    
    def test_get_template_info_compact(self):
        """Test getting compact template information"""
        info = self.generator.get_template_info("compact")
        
        self.assertEqual(info['name'], "compact")
        self.assertTrue(info['compact_mode'])
        self.assertFalse(info['sections']['risk_assessment'])
        self.assertEqual(info['max_resources_shown'], 10)
    
    def test_get_template_info_detailed(self):
        """Test getting detailed template information"""
        info = self.generator.get_template_info("detailed")
        
        self.assertEqual(info['name'], "detailed")
        self.assertTrue(info['detailed_mode'])
        self.assertTrue(info['sections']['appendix'])
        self.assertEqual(info['max_resources_shown'], 50)
    
    @unittest.skipUnless(REPORTLAB_AVAILABLE, "Reportlab not available")
    def test_template_style_setup(self):
        """Test that template styles are set up correctly"""
        # Generate PDF with default template to trigger style setup
        self.generator.generate_comprehensive_report(
            summary=self.sample_summary,
            risk_summary=self.sample_risk_summary,
            resource_changes=self.sample_resource_changes,
            resource_types=self.sample_resource_types,
            plan_data=self.sample_plan_data,
            template_name="default"
        )
        
        # Check that styles were set up
        self.assertIsNotNone(self.generator.styles)
        self.assertIn('MainTitle', self.generator.styles.byName)
        self.assertIn('SectionHeading', self.generator.styles.byName)
    
    @unittest.skipUnless(REPORTLAB_AVAILABLE, "Reportlab not available")
    def test_compact_template_generation(self):
        """Test PDF generation with compact template"""
        pdf_bytes = self.generator.generate_comprehensive_report(
            summary=self.sample_summary,
            risk_summary=self.sample_risk_summary,
            resource_changes=self.sample_resource_changes,
            resource_types=self.sample_resource_types,
            plan_data=self.sample_plan_data,
            template_name="compact"
        )
        
        self.assertIsNotNone(pdf_bytes)
        self.assertIsInstance(pdf_bytes, bytes)
        self.assertGreater(len(pdf_bytes), 0)
    
    @unittest.skipUnless(REPORTLAB_AVAILABLE, "Reportlab not available")
    def test_detailed_template_generation(self):
        """Test PDF generation with detailed template"""
        pdf_bytes = self.generator.generate_comprehensive_report(
            summary=self.sample_summary,
            risk_summary=self.sample_risk_summary,
            resource_changes=self.sample_resource_changes,
            resource_types=self.sample_resource_types,
            plan_data=self.sample_plan_data,
            template_name="detailed"
        )
        
        self.assertIsNotNone(pdf_bytes)
        self.assertIsInstance(pdf_bytes, bytes)
        self.assertGreater(len(pdf_bytes), 0)
    
    @unittest.skipUnless(REPORTLAB_AVAILABLE, "Reportlab not available")
    def test_appendix_creation(self):
        """Test appendix section creation"""
        # Set up detailed template and styles first
        detailed_template = self.generator.template_manager.get_template("detailed")
        self.generator.current_template = detailed_template
        self.generator._setup_template_styles(detailed_template.style_config)
        
        appendix_elements = self.generator._create_appendix(
            self.sample_plan_data,
            self.sample_resource_changes
        )
        
        self.assertIsInstance(appendix_elements, list)
        self.assertGreater(len(appendix_elements), 0)
    
    def test_create_custom_template(self):
        """Test creating custom template"""
        custom_style = PDFStyleConfig(primary_color="#ff0000")
        custom_sections = PDFSectionConfig(appendix=True)
        
        success = self.generator.create_custom_template(
            template_name="custom_test",
            style_config=custom_style,
            section_config=custom_sections,
            compact_mode=True,
            max_resources_shown=25
        )
        
        self.assertTrue(success)
        
        # Verify template was created
        templates = self.generator.get_available_templates()
        self.assertIn("custom_test", templates)
        
        # Verify template properties
        info = self.generator.get_template_info("custom_test")
        self.assertEqual(info['name'], "custom_test")
        self.assertTrue(info['compact_mode'])
        self.assertEqual(info['max_resources_shown'], 25)
        self.assertEqual(info['style']['primary_color'], "#ff0000")
    
    @unittest.skipUnless(REPORTLAB_AVAILABLE, "Reportlab not available")
    def test_custom_style_config_usage(self):
        """Test using custom style configuration"""
        custom_style = PDFStyleConfig(
            primary_color="#123456",
            font_family="Times-Roman",
            margins={"top": 50, "bottom": 50, "left": 50, "right": 50}
        )
        
        pdf_bytes = self.generator.generate_comprehensive_report(
            summary=self.sample_summary,
            risk_summary=self.sample_risk_summary,
            resource_changes=self.sample_resource_changes,
            resource_types=self.sample_resource_types,
            plan_data=self.sample_plan_data,
            custom_style_config=custom_style
        )
        
        self.assertIsNotNone(pdf_bytes)
        self.assertIsInstance(pdf_bytes, bytes)
        self.assertGreater(len(pdf_bytes), 0)
    
    @unittest.skipUnless(REPORTLAB_AVAILABLE, "Reportlab not available")
    def test_template_max_resources_limit(self):
        """Test that templates respect max_resources_shown limit"""
        # Create many resource changes
        many_changes = []
        for i in range(30):
            many_changes.append({
                'address': f'aws_instance.server_{i}',
                'type': 'aws_instance',
                'provider_name': 'registry.terraform.io/hashicorp/aws',
                'change': {'actions': ['create']}
            })
        
        # Test compact template (should show only 10)
        self.generator.generate_comprehensive_report(
            summary={'create': 30, 'update': 0, 'delete': 0, 'no-op': 0},
            risk_summary=self.sample_risk_summary,
            resource_changes=many_changes,
            resource_types={'aws_instance': 30},
            plan_data=self.sample_plan_data,
            template_name="compact"
        )
        
        # Verify current template is set correctly
        self.assertEqual(self.generator.current_template.max_resources_shown, 10)
    
    @unittest.skipUnless(REPORTLAB_AVAILABLE, "Reportlab not available")
    def test_template_section_configuration(self):
        """Test that templates respect section configuration"""
        # Test compact template (should exclude risk assessment and recommendations)
        pdf_bytes = self.generator.generate_comprehensive_report(
            summary=self.sample_summary,
            risk_summary=self.sample_risk_summary,
            resource_changes=self.sample_resource_changes,
            resource_types=self.sample_resource_types,
            plan_data=self.sample_plan_data,
            template_name="compact"
        )
        
        self.assertIsNotNone(pdf_bytes)
        
        # Verify template configuration
        template = self.generator.template_manager.get_template("compact")
        self.assertFalse(template.section_config.risk_assessment)
        self.assertFalse(template.section_config.recommendations)


class TestPDFStylingSystem(unittest.TestCase):
    """Test PDF styling system functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        if not REPORTLAB_AVAILABLE:
            self.skipTest("Reportlab not available")
        
        self.generator = EnhancedPDFGenerator()
    
    def test_color_scheme_application(self):
        """Test that color schemes are applied correctly"""
        # Create custom style with specific colors
        custom_style = PDFStyleConfig(
            primary_color="#ff0000",
            secondary_color="#00ff00",
            accent_color="#0000ff"
        )
        
        # Set up template with custom style
        template = PDFTemplateConfig(
            name="color_test",
            style_config=custom_style,
            section_config=PDFSectionConfig()
        )
        
        self.generator.current_template = template
        self.generator._setup_template_styles(custom_style)
        
        # Verify colors are applied to styles
        main_title_style = self.generator.styles['MainTitle']
        # Color is stored as a Color object, check the RGB values
        self.assertEqual(main_title_style.textColor.red, 1.0)
        self.assertEqual(main_title_style.textColor.green, 0.0)
        self.assertEqual(main_title_style.textColor.blue, 0.0)
    
    def test_typography_management(self):
        """Test typography management"""
        custom_style = PDFStyleConfig(
            font_family="Times-Roman",
            font_family_bold="Times-Bold"
        )
        
        template = PDFTemplateConfig(
            name="font_test",
            style_config=custom_style,
            section_config=PDFSectionConfig()
        )
        
        self.generator.current_template = template
        self.generator._setup_template_styles(custom_style)
        
        # Verify fonts are applied
        body_style = self.generator.styles['CustomBodyText']
        self.assertEqual(body_style.fontName, "Times-Roman")
    
    def test_compact_mode_styling(self):
        """Test that compact mode affects styling"""
        compact_template = self.generator.template_manager.get_template("compact")
        self.generator.current_template = compact_template
        self.generator._setup_template_styles(compact_template.style_config)
        
        # Verify compact mode affects font sizes and spacing
        main_title = self.generator.styles['MainTitle']
        self.assertEqual(main_title.fontSize, 24)  # Smaller than default 28
        
        section_heading = self.generator.styles['SectionHeading']
        self.assertEqual(section_heading.fontSize, 16)  # Smaller than default 18
    
    def test_detailed_mode_styling(self):
        """Test that detailed mode includes additional styles"""
        detailed_template = self.generator.template_manager.get_template("detailed")
        self.generator.current_template = detailed_template
        self.generator._setup_template_styles(detailed_template.style_config)
        
        # Verify detailed mode includes additional styles
        self.assertIn('DetailedBodyText', self.generator.styles.byName)
        self.assertIn('AppendixHeading', self.generator.styles.byName)


if __name__ == '__main__':
    unittest.main()
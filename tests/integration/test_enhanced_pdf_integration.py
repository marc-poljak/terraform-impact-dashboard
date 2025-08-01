"""
Integration tests for enhanced PDF generator integration with report generator component

Tests the integration between ReportGeneratorComponent and EnhancedPDFGenerator
to ensure seamless PDF generation functionality.
"""

import pytest
import tempfile
import os
from typing import Dict, Any, List
from unittest.mock import Mock, patch, MagicMock

# Import the components to test
from components.report_generator import ReportGeneratorComponent
from components.enhanced_pdf_generator import EnhancedPDFGenerator


def _is_reportlab_available() -> bool:
    """Check if reportlab is available for testing"""
    try:
        import reportlab
        return True
    except ImportError:
        return False


class TestEnhancedPDFIntegration:
    """Test suite for enhanced PDF generator integration"""
    
    @pytest.fixture
    def sample_summary(self) -> Dict[str, int]:
        """Sample change summary data"""
        return {
            'create': 5,
            'update': 3,
            'delete': 2,
            'no-op': 10,
            'total': 20
        }
    
    @pytest.fixture
    def sample_risk_summary(self) -> Dict[str, Any]:
        """Sample risk assessment data"""
        return {
            'overall_risk': {
                'level': 'Medium',
                'score': 65,
                'estimated_time': '30-45 minutes',
                'high_risk_count': 2,
                'risk_factors': [
                    'Resource deletion detected',
                    'Security group modifications'
                ]
            }
        }
    
    @pytest.fixture
    def sample_resource_changes(self) -> List[Dict]:
        """Sample resource changes data"""
        return [
            {
                'address': 'aws_instance.web_server',
                'type': 'aws_instance',
                'provider_name': 'registry.terraform.io/hashicorp/aws',
                'change': {
                    'actions': ['create'],
                    'before': None,
                    'after': {
                        'instance_type': 't3.micro',
                        'ami': 'ami-12345678'
                    }
                }
            },
            {
                'address': 'aws_security_group.web_sg',
                'type': 'aws_security_group',
                'provider_name': 'registry.terraform.io/hashicorp/aws',
                'change': {
                    'actions': ['update'],
                    'before': {
                        'ingress': [{'from_port': 80, 'to_port': 80}]
                    },
                    'after': {
                        'ingress': [
                            {'from_port': 80, 'to_port': 80},
                            {'from_port': 443, 'to_port': 443}
                        ]
                    }
                }
            },
            {
                'address': 'aws_s3_bucket.old_bucket',
                'type': 'aws_s3_bucket',
                'provider_name': 'registry.terraform.io/hashicorp/aws',
                'change': {
                    'actions': ['delete'],
                    'before': {
                        'bucket': 'old-bucket-name'
                    },
                    'after': None
                }
            }
        ]
    
    @pytest.fixture
    def sample_resource_types(self) -> Dict[str, int]:
        """Sample resource types data"""
        return {
            'aws_instance': 1,
            'aws_security_group': 1,
            'aws_s3_bucket': 1
        }
    
    @pytest.fixture
    def sample_plan_data(self) -> Dict[str, Any]:
        """Sample Terraform plan data"""
        return {
            'terraform_version': '1.5.0',
            'format_version': '1.1',
            'resource_changes': []
        }
    
    @pytest.fixture
    def report_generator(self) -> ReportGeneratorComponent:
        """Create a report generator component instance"""
        return ReportGeneratorComponent()
    
    def test_report_generator_initialization_with_pdf_generator(self, report_generator):
        """Test that report generator initializes with enhanced PDF generator"""
        # Check that PDF generator is initialized
        assert hasattr(report_generator, 'pdf_generator')
        
        # Check that PDF generator is available (if reportlab is installed)
        try:
            import reportlab
            assert report_generator.pdf_generator is not None
            assert isinstance(report_generator.pdf_generator, EnhancedPDFGenerator)
        except ImportError:
            # If reportlab is not available, pdf_generator should be None
            assert report_generator.pdf_generator is None
    
    @pytest.mark.skipif(
        not _is_reportlab_available(),
        reason="reportlab not available"
    )
    def test_export_pdf_report_integration(self, report_generator, sample_summary, 
                                         sample_risk_summary, sample_resource_changes,
                                         sample_resource_types, sample_plan_data):
        """Test PDF export integration with enhanced PDF generator"""
        # Test PDF generation
        pdf_bytes = report_generator.export_pdf_report(
            summary=sample_summary,
            risk_summary=sample_risk_summary,
            resource_changes=sample_resource_changes,
            resource_types=sample_resource_types,
            plan_data=sample_plan_data,
            template_name="default"
        )
        
        # Verify PDF was generated
        assert pdf_bytes is not None
        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 0
        
        # Verify PDF header (PDF files start with %PDF)
        assert pdf_bytes.startswith(b'%PDF')
    
    @pytest.mark.skipif(
        not _is_reportlab_available(),
        reason="reportlab not available"
    )
    def test_export_pdf_report_with_different_templates(self, report_generator, 
                                                       sample_summary, sample_risk_summary,
                                                       sample_resource_changes, sample_resource_types,
                                                       sample_plan_data):
        """Test PDF export with different templates"""
        templates = ["default", "compact", "detailed"]
        
        for template in templates:
            pdf_bytes = report_generator.export_pdf_report(
                summary=sample_summary,
                risk_summary=sample_risk_summary,
                resource_changes=sample_resource_changes,
                resource_types=sample_resource_types,
                plan_data=sample_plan_data,
                template_name=template
            )
            
            # Verify PDF was generated for each template
            assert pdf_bytes is not None
            assert isinstance(pdf_bytes, bytes)
            assert len(pdf_bytes) > 0
            assert pdf_bytes.startswith(b'%PDF')
    
    @pytest.mark.skipif(
        not _is_reportlab_available(),
        reason="reportlab not available"
    )
    def test_export_pdf_report_with_custom_sections(self, report_generator, 
                                                   sample_summary, sample_risk_summary,
                                                   sample_resource_changes, sample_resource_types,
                                                   sample_plan_data):
        """Test PDF export with custom section configuration"""
        # Test with minimal sections
        minimal_sections = {
            'title_page': True,
            'executive_summary': True,
            'resource_analysis': False,
            'risk_assessment': False,
            'recommendations': False,
            'appendix': False
        }
        
        pdf_bytes = report_generator.export_pdf_report(
            summary=sample_summary,
            risk_summary=sample_risk_summary,
            resource_changes=sample_resource_changes,
            resource_types=sample_resource_types,
            plan_data=sample_plan_data,
            include_sections=minimal_sections
        )
        
        assert pdf_bytes is not None
        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 0
        
        # Test with all sections
        all_sections = {
            'title_page': True,
            'executive_summary': True,
            'resource_analysis': True,
            'risk_assessment': True,
            'recommendations': True,
            'appendix': True
        }
        
        pdf_bytes_full = report_generator.export_pdf_report(
            summary=sample_summary,
            risk_summary=sample_risk_summary,
            resource_changes=sample_resource_changes,
            resource_types=sample_resource_types,
            plan_data=sample_plan_data,
            include_sections=all_sections
        )
        
        assert pdf_bytes_full is not None
        assert len(pdf_bytes_full) > len(pdf_bytes)  # Full report should be larger
    
    def test_export_pdf_report_without_reportlab(self, report_generator, sample_summary,
                                                sample_risk_summary, sample_resource_changes,
                                                sample_resource_types, sample_plan_data):
        """Test PDF export behavior when reportlab is not available"""
        # Mock the PDF generator to simulate missing reportlab
        with patch.object(report_generator, 'pdf_generator', None):
            pdf_bytes = report_generator.export_pdf_report(
                summary=sample_summary,
                risk_summary=sample_risk_summary,
                resource_changes=sample_resource_changes,
                resource_types=sample_resource_types,
                plan_data=sample_plan_data
            )
            
            # Should return None when PDF generator is not available
            assert pdf_bytes is None
    
    @pytest.mark.skipif(
        not _is_reportlab_available(),
        reason="reportlab not available"
    )
    def test_pdf_generation_error_handling(self, report_generator, sample_summary,
                                         sample_risk_summary, sample_resource_changes,
                                         sample_resource_types, sample_plan_data):
        """Test error handling in PDF generation"""
        # Mock the PDF generator to raise an exception
        with patch.object(report_generator.pdf_generator, 'generate_comprehensive_report') as mock_generate:
            mock_generate.side_effect = Exception("Test error")
            
            pdf_bytes = report_generator.export_pdf_report(
                summary=sample_summary,
                risk_summary=sample_risk_summary,
                resource_changes=sample_resource_changes,
                resource_types=sample_resource_types,
                plan_data=sample_plan_data
            )
            
            # Should return None when generation fails
            assert pdf_bytes is None
    
    @pytest.mark.skipif(
        not _is_reportlab_available(),
        reason="reportlab not available"
    )
    def test_pdf_validation_and_content_verification(self, report_generator, sample_summary,
                                                   sample_risk_summary, sample_resource_changes,
                                                   sample_resource_types, sample_plan_data):
        """Test PDF validation and basic content verification"""
        pdf_bytes = report_generator.export_pdf_report(
            summary=sample_summary,
            risk_summary=sample_risk_summary,
            resource_changes=sample_resource_changes,
            resource_types=sample_resource_types,
            plan_data=sample_plan_data
        )
        
        assert pdf_bytes is not None
        
        # Basic PDF structure validation
        assert pdf_bytes.startswith(b'%PDF')
        assert b'%%EOF' in pdf_bytes
        
        # Check for reasonable file size (should be at least a few KB)
        assert len(pdf_bytes) > 1024  # At least 1KB
        
        # Verify PDF can be written to file without errors
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            tmp_file.write(pdf_bytes)
            tmp_file.flush()
            
            # Verify file exists and has content
            assert os.path.exists(tmp_file.name)
            assert os.path.getsize(tmp_file.name) > 0
            
            # Clean up
            os.unlink(tmp_file.name)
    
    def test_dependency_validation_integration(self, report_generator):
        """Test dependency validation integration"""
        if report_generator.pdf_generator:
            is_valid, error_msg = report_generator.pdf_generator.validate_dependencies()
            
            # If PDF generator exists, dependencies should be valid
            assert is_valid is True
            assert error_msg == ""
        else:
            # If PDF generator doesn't exist, it means reportlab is not available
            # This is expected behavior
            pass
    
    @pytest.mark.skipif(
        not _is_reportlab_available(),
        reason="reportlab not available"
    )
    def test_large_dataset_pdf_generation(self, report_generator, sample_summary,
                                        sample_risk_summary, sample_resource_types,
                                        sample_plan_data):
        """Test PDF generation with large datasets"""
        # Create a large dataset
        large_resource_changes = []
        for i in range(100):  # Create 100 resource changes
            large_resource_changes.append({
                'address': f'aws_instance.server_{i}',
                'type': 'aws_instance',
                'provider_name': 'registry.terraform.io/hashicorp/aws',
                'change': {
                    'actions': ['create'],
                    'before': None,
                    'after': {
                        'instance_type': 't3.micro',
                        'ami': f'ami-{i:08d}'
                    }
                }
            })
        
        # Update summary to match large dataset
        large_summary = {
            'create': 100,
            'update': 0,
            'delete': 0,
            'no-op': 0,
            'total': 100
        }
        
        pdf_bytes = report_generator.export_pdf_report(
            summary=large_summary,
            risk_summary=sample_risk_summary,
            resource_changes=large_resource_changes,
            resource_types={'aws_instance': 100},
            plan_data=sample_plan_data
        )
        
        # Should handle large datasets without issues
        assert pdf_bytes is not None
        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 0


# Additional integration test for UI components (would require Streamlit testing framework)
class TestReportGeneratorUIIntegration:
    """Test suite for UI integration (placeholder for future Streamlit testing)"""
    
    def test_ui_pdf_generation_workflow(self):
        """Test the complete UI workflow for PDF generation"""
        # This would require a Streamlit testing framework
        # For now, we'll mark it as a placeholder
        pytest.skip("UI testing requires Streamlit testing framework")
    
    def test_ui_error_handling_display(self):
        """Test UI error handling and message display"""
        # This would test the Streamlit error messages and UI feedback
        pytest.skip("UI testing requires Streamlit testing framework")
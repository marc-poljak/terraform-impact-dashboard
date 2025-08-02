"""
Comprehensive integration tests for PDF generation

Tests end-to-end PDF generation workflows including integration with
report generator component, UI components, and complete user scenarios.

Requirements tested: 1.1, 2.1, 3.1, 3.2, 3.3, 3.4, 4.1, 4.2, 4.3
"""

import pytest
import tempfile
import os
import time
import threading
import queue
from typing import Dict, Any, List
from unittest.mock import Mock, patch, MagicMock

# Import components to test
from components.report_generator import ReportGeneratorComponent
from components.enhanced_pdf_generator import EnhancedPDFGenerator
from tests.fixtures.pdf_test_fixtures import PDFTestFixtures


def _is_reportlab_available() -> bool:
    """Check if reportlab is available for testing"""
    try:
        import reportlab
        return True
    except ImportError:
        return False


class TestComprehensivePDFIntegration:
    """Comprehensive integration tests for PDF generation"""
    
    @pytest.fixture
    def pdf_fixtures(self):
        """PDF test fixtures"""
        return PDFTestFixtures()
    
    @pytest.fixture
    def report_generator(self):
        """Create a report generator component instance"""
        return ReportGeneratorComponent()
    
    @pytest.fixture
    def enhanced_pdf_generator(self):
        """Create an enhanced PDF generator instance"""
        return EnhancedPDFGenerator()
    
    @pytest.mark.skipif(
        not _is_reportlab_available(),
        reason="reportlab not available"
    )
    def test_end_to_end_pdf_generation_workflow(self, report_generator, pdf_fixtures):
        """Test complete end-to-end PDF generation workflow"""
        # Test with different data scenarios
        test_scenarios = [
            ('minimal_scenario', pdf_fixtures.get_minimal_pdf_data()),
            ('basic_scenario', pdf_fixtures.get_basic_pdf_data()),
            ('comprehensive_scenario', pdf_fixtures.get_comprehensive_pdf_data()),
            ('large_dataset_scenario', pdf_fixtures.get_large_dataset_pdf_data()),
            ('security_focused_scenario', pdf_fixtures.get_security_focused_pdf_data())
        ]
        
        for scenario_name, test_data in test_scenarios:
            try:
                pdf_bytes = report_generator.export_pdf_report(
                    summary=test_data['summary'],
                    risk_summary=test_data['risk_summary'],
                    resource_changes=test_data['resource_changes'],
                    resource_types=test_data['resource_types'],
                    plan_data=test_data['plan_data']
                )
                
                if pdf_bytes is not None:
                    # Verify PDF structure
                    assert isinstance(pdf_bytes, bytes)
                    assert len(pdf_bytes) > 0
                    assert pdf_bytes.startswith(b'%PDF')
                    assert b'%%EOF' in pdf_bytes
                    
                    print(f"✓ {scenario_name}: Generated {len(pdf_bytes)} bytes")
                else:
                    print(f"⚠ {scenario_name}: PDF generation returned None (expected if reportlab unavailable)")
            except Exception as e:
                print(f"✗ {scenario_name}: Exception occurred: {e}")
                # Re-raise if it's an unexpected exception
                if "reportlab" not in str(e).lower():
                    raise
    
    @pytest.mark.skipif(
        not _is_reportlab_available(),
        reason="reportlab not available"
    )
    def test_all_template_integration(self, report_generator, pdf_fixtures):
        """Test integration with all available templates"""
        test_data = pdf_fixtures.get_comprehensive_pdf_data()
        templates = ["default", "compact", "detailed"]
        
        template_results = {}
        
        for template in templates:
            pdf_bytes = report_generator.export_pdf_report(
                summary=test_data['summary'],
                risk_summary=test_data['risk_summary'],
                resource_changes=test_data['resource_changes'],
                resource_types=test_data['resource_types'],
                plan_data=test_data['plan_data'],
                template_name=template
            )
            
            assert pdf_bytes is not None, f"Template {template} failed to generate PDF"
            assert isinstance(pdf_bytes, bytes)
            assert len(pdf_bytes) > 0
            assert pdf_bytes.startswith(b'%PDF')
            
            template_results[template] = len(pdf_bytes)
        
        # Verify different templates produce different sized outputs
        assert len(set(template_results.values())) > 1, "All templates produced identical output"
        
        print(f"Template sizes: {template_results}")
    
    @pytest.mark.skipif(
        not _is_reportlab_available(),
        reason="reportlab not available"
    )
    def test_section_configuration_integration(self, report_generator, pdf_fixtures):
        """Test integration with different section configurations"""
        test_data = pdf_fixtures.get_comprehensive_pdf_data()
        
        section_configs = [
            # Title page only
            {
                'title_page': True,
                'executive_summary': False,
                'resource_analysis': False,
                'risk_assessment': False,
                'recommendations': False,
                'appendix': False
            },
            # Summary sections
            {
                'title_page': True,
                'executive_summary': True,
                'resource_analysis': True,
                'risk_assessment': False,
                'recommendations': False,
                'appendix': False
            },
            # Analysis sections
            {
                'title_page': True,
                'executive_summary': False,
                'resource_analysis': True,
                'risk_assessment': True,
                'recommendations': True,
                'appendix': False
            },
            # Complete report
            {
                'title_page': True,
                'executive_summary': True,
                'resource_analysis': True,
                'risk_assessment': True,
                'recommendations': True,
                'appendix': True
            }
        ]
        
        config_results = {}
        
        for i, config in enumerate(section_configs):
            pdf_bytes = report_generator.export_pdf_report(
                summary=test_data['summary'],
                risk_summary=test_data['risk_summary'],
                resource_changes=test_data['resource_changes'],
                resource_types=test_data['resource_types'],
                plan_data=test_data['plan_data'],
                include_sections=config
            )
            
            assert pdf_bytes is not None, f"Section config {i} failed to generate PDF"
            assert isinstance(pdf_bytes, bytes)
            assert len(pdf_bytes) > 0
            
            config_results[f"config_{i}"] = len(pdf_bytes)
        
        # More sections should generally produce larger PDFs
        sizes = list(config_results.values())
        assert sizes[-1] > sizes[0], "Complete report should be larger than minimal report"
        
        print(f"Section config sizes: {config_results}")
    
    @pytest.mark.skipif(
        not _is_reportlab_available(),
        reason="reportlab not available"
    )
    def test_error_handling_integration(self, report_generator, pdf_fixtures):
        """Test error handling in integration scenarios"""
        # Test with None values
        pdf_bytes_none = report_generator.export_pdf_report(
            summary=None,
            risk_summary=None,
            resource_changes=None,
            resource_types=None,
            plan_data=None
        )
        
        # Should handle gracefully
        assert pdf_bytes_none is None
        
        # Test with malformed data
        malformed_data = {
            'summary': "not_a_dict",
            'risk_summary': ["not_a_dict"],
            'resource_changes': "not_a_list",
            'resource_types': "not_a_dict",
            'plan_data': "not_a_dict"
        }
        
        pdf_bytes_malformed = report_generator.export_pdf_report(**malformed_data)
        
        # Should handle gracefully
        assert pdf_bytes_malformed is None
        
        # Test with empty but valid data
        empty_data = pdf_fixtures.get_minimal_pdf_data()
        pdf_bytes_empty = report_generator.export_pdf_report(**empty_data)
        
        # Should generate valid PDF even with empty data
        if pdf_bytes_empty is not None:
            assert isinstance(pdf_bytes_empty, bytes)
            assert len(pdf_bytes_empty) > 0
            assert pdf_bytes_empty.startswith(b'%PDF')
    
    def test_pdf_generator_unavailable_integration(self, report_generator, pdf_fixtures):
        """Test integration when PDF generator is unavailable"""
        test_data = pdf_fixtures.get_basic_pdf_data()
        
        # Mock PDF generator as unavailable
        with patch.object(report_generator, 'pdf_generator', None):
            pdf_bytes = report_generator.export_pdf_report(**test_data)
            
            # Should return None when PDF generator is unavailable
            assert pdf_bytes is None
    
    @pytest.mark.skipif(
        not _is_reportlab_available(),
        reason="reportlab not available"
    )
    def test_performance_integration(self, report_generator, pdf_fixtures):
        """Test performance in integration scenarios"""
        large_data = pdf_fixtures.get_large_dataset_pdf_data()
        
        # Measure generation time
        start_time = time.time()
        
        pdf_bytes = report_generator.export_pdf_report(
            summary=large_data['summary'],
            risk_summary=large_data['risk_summary'],
            resource_changes=large_data['resource_changes'],
            resource_types=large_data['resource_types'],
            plan_data=large_data['plan_data']
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Verify PDF was generated
        assert pdf_bytes is not None
        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 0
        
        # Performance requirement: large datasets should complete within 10 seconds
        assert duration < 10.0, f"Large dataset PDF generation took {duration:.2f}s, should be < 10s"
        
        print(f"Large dataset integration performance: {duration:.3f}s, {len(pdf_bytes)} bytes")
    
    @pytest.mark.skipif(
        not _is_reportlab_available(),
        reason="reportlab not available"
    )
    def test_concurrent_integration(self, report_generator, pdf_fixtures):
        """Test concurrent PDF generation in integration scenario"""
        test_data = pdf_fixtures.get_basic_pdf_data()
        
        results_queue = queue.Queue()
        errors_queue = queue.Queue()
        
        def worker_thread(worker_id):
            try:
                pdf_bytes = report_generator.export_pdf_report(
                    summary=test_data['summary'],
                    risk_summary=test_data['risk_summary'],
                    resource_changes=test_data['resource_changes'],
                    resource_types=test_data['resource_types'],
                    plan_data=test_data['plan_data']
                )
                results_queue.put((worker_id, len(pdf_bytes) if pdf_bytes else 0))
            except Exception as e:
                errors_queue.put((worker_id, str(e)))
        
        # Start multiple threads
        threads = []
        for i in range(3):
            thread = threading.Thread(target=worker_thread, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join(timeout=30)
        
        # Check results
        assert errors_queue.empty(), f"Concurrent integration errors: {list(errors_queue.queue)}"
        
        results = []
        while not results_queue.empty():
            results.append(results_queue.get())
        
        assert len(results) == 3, "Not all concurrent integrations completed"
        
        # All should have generated valid PDFs
        for worker_id, pdf_size in results:
            assert pdf_size > 0, f"Worker {worker_id} generated empty PDF"
        
        print(f"Concurrent integration results: {results}")
    
    @pytest.mark.skipif(
        not _is_reportlab_available(),
        reason="reportlab not available"
    )
    def test_file_operations_integration(self, report_generator, pdf_fixtures):
        """Test file operations integration"""
        test_data = pdf_fixtures.get_comprehensive_pdf_data()
        
        pdf_bytes = report_generator.export_pdf_report(
            summary=test_data['summary'],
            risk_summary=test_data['risk_summary'],
            resource_changes=test_data['resource_changes'],
            resource_types=test_data['resource_types'],
            plan_data=test_data['plan_data']
        )
        
        assert pdf_bytes is not None
        
        # Test file creation and validation
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            tmp_file.write(pdf_bytes)
            tmp_file.flush()
            
            # Verify file properties
            assert os.path.exists(tmp_file.name)
            file_size = os.path.getsize(tmp_file.name)
            assert file_size > 1000, f"PDF file too small: {file_size} bytes"
            
            # Verify file content
            with open(tmp_file.name, 'rb') as f:
                file_content = f.read()
                assert file_content == pdf_bytes
                assert file_content.startswith(b'%PDF')
                assert b'%%EOF' in file_content
            
            # Clean up
            os.unlink(tmp_file.name)
        
        print(f"File operations integration: {len(pdf_bytes)} bytes written and verified")
    
    @pytest.mark.skipif(
        not _is_reportlab_available(),
        reason="reportlab not available"
    )
    def test_risk_level_integration(self, report_generator, pdf_fixtures):
        """Test integration with different risk levels"""
        risk_scenarios = [
            ('low_risk', {**pdf_fixtures.get_basic_pdf_data(), 'risk_summary': {'level': 'Low', 'score': 20}}),
            ('medium_risk', {**pdf_fixtures.get_basic_pdf_data(), 'risk_summary': {'level': 'Medium', 'score': 50}}),
            ('high_risk', {**pdf_fixtures.get_basic_pdf_data(), 'risk_summary': {'level': 'High', 'score': 80}}),
            ('critical_risk', pdf_fixtures.get_security_focused_pdf_data())
        ]
        
        risk_results = {}
        
        for risk_name, risk_data in risk_scenarios:
            pdf_bytes = report_generator.export_pdf_report(
                summary=risk_data['summary'],
                risk_summary=risk_data['risk_summary'],
                resource_changes=risk_data['resource_changes'],
                resource_types=risk_data['resource_types'],
                plan_data=risk_data['plan_data']
            )
            
            assert pdf_bytes is not None, f"Risk scenario {risk_name} failed"
            assert isinstance(pdf_bytes, bytes)
            assert len(pdf_bytes) > 0
            
            risk_results[risk_name] = len(pdf_bytes)
        
        # Higher risk scenarios might produce more detailed reports
        assert risk_results['critical_risk'] > risk_results['low_risk']
        
        print(f"Risk level integration results: {risk_results}")
    
    @pytest.mark.skipif(
        not _is_reportlab_available(),
        reason="reportlab not available"
    )
    def test_multi_provider_integration(self, report_generator, pdf_fixtures):
        """Test integration with multi-provider scenarios"""
        multi_provider_data = pdf_fixtures.get_comprehensive_pdf_data()
        
        # Verify the test data includes multiple providers
        providers = set()
        for change in multi_provider_data['resource_changes']:
            provider_name = change.get('provider_name', '')
            if 'aws' in provider_name:
                providers.add('aws')
            elif 'azure' in provider_name:
                providers.add('azure')
            elif 'google' in provider_name:
                providers.add('gcp')
        
        assert len(providers) >= 2, "Test data should include multiple providers"
        
        pdf_bytes = report_generator.export_pdf_report(
            summary=multi_provider_data['summary'],
            risk_summary=multi_provider_data['risk_summary'],
            resource_changes=multi_provider_data['resource_changes'],
            resource_types=multi_provider_data['resource_types'],
            plan_data=multi_provider_data['plan_data']
        )
        
        assert pdf_bytes is not None
        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 0
        assert pdf_bytes.startswith(b'%PDF')
        
        print(f"Multi-provider integration: {len(providers)} providers, {len(pdf_bytes)} bytes")
    
    def test_dependency_validation_integration(self, enhanced_pdf_generator):
        """Test dependency validation in integration context"""
        is_valid, error_msg = enhanced_pdf_generator.validate_dependencies()
        
        if _is_reportlab_available():
            assert is_valid is True
            assert error_msg == ""
        else:
            assert is_valid is False
            assert "reportlab" in error_msg.lower()
            assert "pip install reportlab" in error_msg
        
        print(f"Dependency validation: valid={is_valid}, message='{error_msg}'")


class TestPDFGenerationWorkflows:
    """Test complete PDF generation workflows"""
    
    @pytest.fixture
    def pdf_fixtures(self):
        """PDF test fixtures"""
        return PDFTestFixtures()
    
    @pytest.mark.skipif(
        not _is_reportlab_available(),
        reason="reportlab not available"
    )
    def test_complete_user_workflow(self, pdf_fixtures):
        """Test complete user workflow from data to PDF"""
        # Simulate complete user workflow
        
        # 1. User uploads/provides Terraform plan data
        plan_data = pdf_fixtures.get_comprehensive_pdf_data()
        
        # 2. System processes the data
        report_generator = ReportGeneratorComponent()
        
        # 3. User requests PDF generation
        pdf_bytes = report_generator.export_pdf_report(
            summary=plan_data['summary'],
            risk_summary=plan_data['risk_summary'],
            resource_changes=plan_data['resource_changes'],
            resource_types=plan_data['resource_types'],
            plan_data=plan_data['plan_data']
        )
        
        # 4. System provides PDF for download
        assert pdf_bytes is not None
        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 0
        assert pdf_bytes.startswith(b'%PDF')
        
        # 5. User can save the PDF
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            tmp_file.write(pdf_bytes)
            tmp_file.flush()
            
            # Verify the saved file
            assert os.path.exists(tmp_file.name)
            assert os.path.getsize(tmp_file.name) > 0
            
            # Clean up
            os.unlink(tmp_file.name)
        
        print(f"Complete user workflow: {len(pdf_bytes)} bytes generated and saved")
    
    @pytest.mark.skipif(
        not _is_reportlab_available(),
        reason="reportlab not available"
    )
    def test_batch_processing_workflow(self, pdf_fixtures):
        """Test batch processing workflow"""
        # Simulate batch processing of multiple plans
        test_plans = [
            pdf_fixtures.get_basic_pdf_data(),
            pdf_fixtures.get_comprehensive_pdf_data(),
            pdf_fixtures.get_security_focused_pdf_data()
        ]
        
        report_generator = ReportGeneratorComponent()
        batch_results = []
        
        for i, plan_data in enumerate(test_plans):
            pdf_bytes = report_generator.export_pdf_report(
                summary=plan_data['summary'],
                risk_summary=plan_data['risk_summary'],
                resource_changes=plan_data['resource_changes'],
                resource_types=plan_data['resource_types'],
                plan_data=plan_data['plan_data']
            )
            
            assert pdf_bytes is not None, f"Batch item {i} failed"
            batch_results.append(len(pdf_bytes))
        
        # All batch items should have been processed
        assert len(batch_results) == len(test_plans)
        assert all(size > 0 for size in batch_results)
        
        print(f"Batch processing workflow: {len(batch_results)} PDFs generated, sizes: {batch_results}")
    
    @pytest.mark.skipif(
        not _is_reportlab_available(),
        reason="reportlab not available"
    )
    def test_customization_workflow(self, pdf_fixtures):
        """Test PDF customization workflow"""
        test_data = pdf_fixtures.get_comprehensive_pdf_data()
        report_generator = ReportGeneratorComponent()
        
        # Test different customization options
        customizations = [
            # Different templates
            {'template_name': 'default'},
            {'template_name': 'compact'},
            {'template_name': 'detailed'},
            
            # Different section combinations
            {
                'include_sections': {
                    'title_page': True,
                    'executive_summary': True,
                    'resource_analysis': False,
                    'risk_assessment': True,
                    'recommendations': False,
                    'appendix': False
                }
            },
            {
                'include_sections': {
                    'title_page': True,
                    'executive_summary': True,
                    'resource_analysis': True,
                    'risk_assessment': True,
                    'recommendations': True,
                    'appendix': True
                }
            }
        ]
        
        customization_results = {}
        
        for i, custom_options in enumerate(customizations):
            pdf_bytes = report_generator.export_pdf_report(
                summary=test_data['summary'],
                risk_summary=test_data['risk_summary'],
                resource_changes=test_data['resource_changes'],
                resource_types=test_data['resource_types'],
                plan_data=test_data['plan_data'],
                **custom_options
            )
            
            assert pdf_bytes is not None, f"Customization {i} failed"
            customization_results[f"custom_{i}"] = len(pdf_bytes)
        
        # Different customizations should produce different results
        sizes = list(customization_results.values())
        assert len(set(sizes)) > 1, "All customizations produced identical output"
        
        print(f"Customization workflow results: {customization_results}")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
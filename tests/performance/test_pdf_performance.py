"""
Performance tests for PDF generation

Tests PDF generation performance with various dataset sizes and complexity levels.
Includes memory usage monitoring, generation time benchmarks, and scalability testing.

Requirements tested: 1.1, 2.1, 3.1, 3.2, 3.3, 3.4
"""

import pytest
import time
import gc
import psutil
import statistics
from typing import Dict, Any, List, Tuple
from dataclasses import dataclass
import threading
import queue

# Import components for testing
from components.enhanced_pdf_generator import EnhancedPDFGenerator
from components.report_generator import ReportGeneratorComponent
from tests.fixtures.pdf_test_fixtures import PDFTestFixtures


def _is_reportlab_available() -> bool:
    """Check if reportlab is available for testing"""
    try:
        import reportlab
        return True
    except ImportError:
        return False


@dataclass
class PerformanceResult:
    """Container for performance test results"""
    test_name: str
    duration_seconds: float
    memory_mb: float
    pdf_size_bytes: int
    success: bool
    error_message: str = ""
    metadata: Dict[str, Any] = None


class PDFPerformanceTester:
    """PDF generation performance testing utility"""
    
    def __init__(self):
        self.process = psutil.Process()
        self.fixtures = PDFTestFixtures()
        self.results = []
        
        # Performance thresholds based on requirements
        self.thresholds = {
            'small_dataset': {'max_duration': 2.0, 'max_memory_mb': 50},
            'medium_dataset': {'max_duration': 5.0, 'max_memory_mb': 150},
            'large_dataset': {'max_duration': 10.0, 'max_memory_mb': 500},
            'very_large_dataset': {'max_duration': 15.0, 'max_memory_mb': 1000}
        }
    
    def measure_performance(self, test_name: str, operation_func, *args, **kwargs) -> PerformanceResult:
        """Measure performance of a PDF generation operation"""
        # Force garbage collection before test
        gc.collect()
        initial_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        
        start_time = time.time()
        success = True
        error_message = ""
        pdf_size = 0
        
        try:
            pdf_bytes = operation_func(*args, **kwargs)
            if pdf_bytes:
                pdf_size = len(pdf_bytes)
            else:
                success = False
                error_message = "PDF generation returned None"
        except Exception as e:
            success = False
            error_message = str(e)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Measure peak memory usage
        peak_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        memory_used = peak_memory - initial_memory
        
        result = PerformanceResult(
            test_name=test_name,
            duration_seconds=duration,
            memory_mb=memory_used,
            pdf_size_bytes=pdf_size,
            success=success,
            error_message=error_message,
            metadata={
                'initial_memory_mb': initial_memory,
                'peak_memory_mb': peak_memory
            }
        )
        
        self.results.append(result)
        return result
    
    def generate_dataset(self, size: str, complexity: str = 'medium') -> Dict[str, Any]:
        """Generate test dataset of specified size and complexity"""
        if size == 'small':
            num_resources = 10
        elif size == 'medium':
            num_resources = 50
        elif size == 'large':
            num_resources = 200
        elif size == 'very_large':
            num_resources = 500
        else:
            num_resources = 100
        
        # Generate resource changes
        resource_changes = []
        resource_types = {}
        plan_resources = []
        
        providers = [
            ('aws', ['aws_instance', 'aws_s3_bucket', 'aws_security_group', 'aws_rds_instance']),
            ('azure', ['azurerm_virtual_machine', 'azurerm_storage_account', 'azurerm_network_security_group']),
            ('gcp', ['google_compute_instance', 'google_storage_bucket', 'google_compute_firewall'])
        ]
        
        actions = ['create', 'update', 'delete']
        create_count = update_count = delete_count = 0
        
        for i in range(num_resources):
            provider_name, resource_type_list = providers[i % len(providers)]
            resource_type = resource_type_list[i % len(resource_type_list)]
            action = actions[i % len(actions)]
            
            # Count actions
            if action == 'create':
                create_count += 1
            elif action == 'update':
                update_count += 1
            elif action == 'delete':
                delete_count += 1
            
            # Count resource types
            if resource_type not in resource_types:
                resource_types[resource_type] = 0
            resource_types[resource_type] += 1
            
            # Create resource configuration based on complexity
            if complexity == 'simple':
                config = {'id': f'resource-{i}', 'name': f'resource-{i}'}
            elif complexity == 'medium':
                config = {
                    'id': f'resource-{i}',
                    'name': f'resource-{i}',
                    'tags': {'Environment': 'test', 'ResourceId': str(i)}
                }
            else:  # complex
                config = {
                    'id': f'resource-{i}',
                    'name': f'resource-{i}',
                    'tags': {
                        'Environment': 'test',
                        'ResourceId': str(i),
                        'Owner': f'team-{i % 5}',
                        'Project': f'project-{i % 10}'
                    },
                    'metadata': {
                        'created_by': 'terraform',
                        'version': '1.0.0',
                        'dependencies': [f'resource-{j}' for j in range(max(0, i-2), i)]
                    }
                }
            
            # Create resource change
            resource_change = {
                'address': f'{resource_type}.resource_{i}',
                'type': resource_type,
                'provider_name': f'registry.terraform.io/hashicorp/{provider_name}',
                'change': {
                    'actions': [action],
                    'before': config if action in ['update', 'delete'] else None,
                    'after': config if action in ['create', 'update'] else None
                }
            }
            resource_changes.append(resource_change)
            
            # Add to plan resources
            plan_resources.append({
                'address': f'{resource_type}.resource_{i}',
                'type': resource_type
            })
        
        # Generate appropriate risk level based on size
        if size == 'small':
            risk_level, risk_score = 'Low', 25
        elif size == 'medium':
            risk_level, risk_score = 'Medium', 55
        elif size == 'large':
            risk_level, risk_score = 'High', 78
        else:  # very_large
            risk_level, risk_score = 'Critical', 92
        
        return {
            'summary': {
                'create': create_count,
                'update': update_count,
                'delete': delete_count,
                'no-op': max(10, num_resources // 10),
                'total': create_count + update_count + delete_count + max(10, num_resources // 10)
            },
            'risk_summary': {
                'overall_risk': {
                    'level': risk_level,
                    'score': risk_score,
                    'estimated_time': f'{risk_score // 20 * 15}-{risk_score // 20 * 20} minutes',
                    'high_risk_count': max(1, risk_score // 20),
                    'risk_factors': [
                        f'Dataset contains {num_resources} resource changes',
                        f'Multiple provider modifications detected',
                        f'Risk level: {risk_level}'
                    ]
                }
            },
            'resource_changes': resource_changes,
            'resource_types': resource_types,
            'plan_data': {
                'terraform_version': '1.6.0',
                'format_version': '1.2',
                'resource_changes': plan_resources
            }
        }


class TestPDFGenerationPerformance:
    """Performance tests for PDF generation"""
    
    @pytest.fixture
    def performance_tester(self):
        """Create performance tester instance"""
        return PDFPerformanceTester()
    
    @pytest.fixture
    def pdf_generator(self):
        """Create PDF generator instance"""
        return EnhancedPDFGenerator()
    
    @pytest.fixture
    def report_generator(self):
        """Create report generator instance"""
        return ReportGeneratorComponent()
    
    @pytest.mark.skipif(
        not _is_reportlab_available(),
        reason="reportlab not available"
    )
    def test_dataset_size_performance(self, performance_tester, pdf_generator):
        """Test performance with different dataset sizes"""
        dataset_sizes = ['small', 'medium', 'large', 'very_large']
        
        for size in dataset_sizes:
            test_data = performance_tester.generate_dataset(size, 'medium')
            
            def generate_pdf():
                return pdf_generator.generate_comprehensive_report(
                    summary=test_data['summary'],
                    risk_summary=test_data['risk_summary'],
                    resource_changes=test_data['resource_changes'],
                    resource_types=test_data['resource_types'],
                    plan_data=test_data['plan_data']
                )
            
            result = performance_tester.measure_performance(
                f"{size}_dataset_performance",
                generate_pdf
            )
            
            # Verify success
            assert result.success, f"{size} dataset failed: {result.error_message}"
            assert result.pdf_size_bytes > 0, f"{size} dataset produced empty PDF"
            
            # Check performance thresholds
            threshold = performance_tester.thresholds.get(f"{size}_dataset", {})
            if 'max_duration' in threshold:
                assert result.duration_seconds <= threshold['max_duration'], \
                    f"{size} dataset took {result.duration_seconds:.3f}s, max allowed: {threshold['max_duration']}s"
            
            if 'max_memory_mb' in threshold:
                assert result.memory_mb <= threshold['max_memory_mb'], \
                    f"{size} dataset used {result.memory_mb:.1f}MB, max allowed: {threshold['max_memory_mb']}MB"
            
            print(f"{size} dataset: {result.duration_seconds:.3f}s, {result.memory_mb:.1f}MB, {result.pdf_size_bytes} bytes")
    
    @pytest.mark.skipif(
        not _is_reportlab_available(),
        reason="reportlab not available"
    )
    def test_complexity_performance(self, performance_tester, pdf_generator):
        """Test performance with different data complexity levels"""
        complexity_levels = ['simple', 'medium', 'complex']
        
        for complexity in complexity_levels:
            test_data = performance_tester.generate_dataset('medium', complexity)
            
            def generate_pdf():
                return pdf_generator.generate_comprehensive_report(
                    summary=test_data['summary'],
                    risk_summary=test_data['risk_summary'],
                    resource_changes=test_data['resource_changes'],
                    resource_types=test_data['resource_types'],
                    plan_data=test_data['plan_data']
                )
            
            result = performance_tester.measure_performance(
                f"{complexity}_complexity_performance",
                generate_pdf
            )
            
            # Verify success
            assert result.success, f"{complexity} complexity failed: {result.error_message}"
            assert result.pdf_size_bytes > 0, f"{complexity} complexity produced empty PDF"
            
            # Complex data should generally take longer but not excessively
            assert result.duration_seconds < 8.0, \
                f"{complexity} complexity took {result.duration_seconds:.3f}s, should be < 8s"
            
            print(f"{complexity} complexity: {result.duration_seconds:.3f}s, {result.memory_mb:.1f}MB, {result.pdf_size_bytes} bytes")
    
    @pytest.mark.skipif(
        not _is_reportlab_available(),
        reason="reportlab not available"
    )
    def test_template_performance(self, performance_tester, pdf_generator):
        """Test performance with different templates"""
        templates = ['default', 'compact', 'detailed']
        test_data = performance_tester.generate_dataset('large', 'medium')
        
        template_results = {}
        
        for template in templates:
            def generate_pdf():
                return pdf_generator.generate_comprehensive_report(
                    summary=test_data['summary'],
                    risk_summary=test_data['risk_summary'],
                    resource_changes=test_data['resource_changes'],
                    resource_types=test_data['resource_types'],
                    plan_data=test_data['plan_data'],
                    template_name=template
                )
            
            result = performance_tester.measure_performance(
                f"{template}_template_performance",
                generate_pdf
            )
            
            # Verify success
            assert result.success, f"{template} template failed: {result.error_message}"
            assert result.pdf_size_bytes > 0, f"{template} template produced empty PDF"
            
            template_results[template] = {
                'duration': result.duration_seconds,
                'memory': result.memory_mb,
                'size': result.pdf_size_bytes
            }
            
            print(f"{template} template: {result.duration_seconds:.3f}s, {result.memory_mb:.1f}MB, {result.pdf_size_bytes} bytes")
        
        # All templates should perform within reasonable bounds
        for template, metrics in template_results.items():
            assert metrics['duration'] < 12.0, f"{template} template too slow: {metrics['duration']:.3f}s"
            assert metrics['memory'] < 600, f"{template} template uses too much memory: {metrics['memory']:.1f}MB"
    
    @pytest.mark.skipif(
        not _is_reportlab_available(),
        reason="reportlab not available"
    )
    def test_concurrent_performance(self, performance_tester, pdf_generator):
        """Test performance under concurrent load"""
        test_data = performance_tester.generate_dataset('medium', 'medium')
        
        results_queue = queue.Queue()
        errors_queue = queue.Queue()
        
        def worker_thread(worker_id):
            try:
                start_time = time.time()
                
                pdf_bytes = pdf_generator.generate_comprehensive_report(
                    summary=test_data['summary'],
                    risk_summary=test_data['risk_summary'],
                    resource_changes=test_data['resource_changes'],
                    resource_types=test_data['resource_types'],
                    plan_data=test_data['plan_data']
                )
                
                end_time = time.time()
                duration = end_time - start_time
                
                results_queue.put((worker_id, duration, len(pdf_bytes) if pdf_bytes else 0))
            except Exception as e:
                errors_queue.put((worker_id, str(e)))
        
        # Start multiple concurrent threads
        num_threads = 4
        threads = []
        
        overall_start = time.time()
        
        for i in range(num_threads):
            thread = threading.Thread(target=worker_thread, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join(timeout=60)
        
        overall_end = time.time()
        overall_duration = overall_end - overall_start
        
        # Check for errors
        assert errors_queue.empty(), f"Concurrent errors: {list(errors_queue.queue)}"
        
        # Collect results
        results = []
        while not results_queue.empty():
            results.append(results_queue.get())
        
        assert len(results) == num_threads, f"Expected {num_threads} results, got {len(results)}"
        
        # Analyze concurrent performance
        durations = [r[1] for r in results]
        pdf_sizes = [r[2] for r in results]
        
        avg_duration = statistics.mean(durations)
        max_duration = max(durations)
        
        # All PDFs should be generated successfully
        assert all(size > 0 for size in pdf_sizes), "Some concurrent generations failed"
        
        # Concurrent performance should be reasonable
        assert overall_duration < 20.0, f"Overall concurrent test took {overall_duration:.3f}s, should be < 20s"
        assert avg_duration < 8.0, f"Average concurrent duration {avg_duration:.3f}s, should be < 8s"
        assert max_duration < 12.0, f"Max concurrent duration {max_duration:.3f}s, should be < 12s"
        
        print(f"Concurrent performance: {num_threads} threads, overall={overall_duration:.3f}s, avg={avg_duration:.3f}s, max={max_duration:.3f}s")
    
    @pytest.mark.skipif(
        not _is_reportlab_available(),
        reason="reportlab not available"
    )
    def test_memory_efficiency(self, performance_tester, pdf_generator):
        """Test memory efficiency across multiple generations"""
        test_data = performance_tester.generate_dataset('medium', 'medium')
        
        initial_memory = performance_tester.process.memory_info().rss / 1024 / 1024
        memory_measurements = [initial_memory]
        
        # Generate multiple PDFs and track memory
        for i in range(10):
            pdf_bytes = pdf_generator.generate_comprehensive_report(
                summary=test_data['summary'],
                risk_summary=test_data['risk_summary'],
                resource_changes=test_data['resource_changes'],
                resource_types=test_data['resource_types'],
                plan_data=test_data['plan_data']
            )
            
            assert pdf_bytes is not None, f"Generation {i} failed"
            
            # Explicitly delete reference and force garbage collection
            del pdf_bytes
            gc.collect()
            
            current_memory = performance_tester.process.memory_info().rss / 1024 / 1024
            memory_measurements.append(current_memory)
        
        final_memory = memory_measurements[-1]
        memory_growth = final_memory - initial_memory
        max_memory = max(memory_measurements)
        
        # Memory growth should be reasonable
        assert memory_growth < 200, f"Memory grew by {memory_growth:.1f}MB after 10 generations, should be < 200MB"
        assert max_memory < initial_memory + 300, f"Peak memory {max_memory:.1f}MB too high"
        
        print(f"Memory efficiency: initial={initial_memory:.1f}MB, final={final_memory:.1f}MB, growth={memory_growth:.1f}MB, peak={max_memory:.1f}MB")
    
    @pytest.mark.skipif(
        not _is_reportlab_available(),
        reason="reportlab not available"
    )
    def test_scalability_performance(self, performance_tester, pdf_generator):
        """Test scalability with increasing dataset sizes"""
        sizes = [10, 25, 50, 100, 200]
        scalability_results = {}
        
        for size in sizes:
            # Generate custom dataset of specific size
            test_data = performance_tester.generate_dataset('custom', 'medium')
            # Override with specific size
            test_data['resource_changes'] = test_data['resource_changes'][:size]
            test_data['summary']['total'] = size
            
            def generate_pdf():
                return pdf_generator.generate_comprehensive_report(
                    summary=test_data['summary'],
                    risk_summary=test_data['risk_summary'],
                    resource_changes=test_data['resource_changes'],
                    resource_types=test_data['resource_types'],
                    plan_data=test_data['plan_data']
                )
            
            result = performance_tester.measure_performance(
                f"scalability_{size}_resources",
                generate_pdf
            )
            
            assert result.success, f"Scalability test with {size} resources failed: {result.error_message}"
            
            scalability_results[size] = {
                'duration': result.duration_seconds,
                'memory': result.memory_mb,
                'size': result.pdf_size_bytes
            }
            
            print(f"{size} resources: {result.duration_seconds:.3f}s, {result.memory_mb:.1f}MB, {result.pdf_size_bytes} bytes")
        
        # Analyze scalability
        sizes_list = list(scalability_results.keys())
        durations = [scalability_results[s]['duration'] for s in sizes_list]
        
        # Performance should scale reasonably (not exponentially)
        # Check that doubling the size doesn't more than triple the time
        for i in range(1, len(sizes_list)):
            prev_size, curr_size = sizes_list[i-1], sizes_list[i]
            prev_duration, curr_duration = durations[i-1], durations[i]
            
            size_ratio = curr_size / prev_size
            duration_ratio = curr_duration / max(prev_duration, 0.001)  # Avoid division by zero
            
            # Duration ratio should not be excessively higher than size ratio
            assert duration_ratio <= size_ratio * 2.5, \
                f"Poor scalability: {prev_size}->{curr_size} resources, duration ratio {duration_ratio:.2f} vs size ratio {size_ratio:.2f}"
        
        print(f"Scalability analysis: sizes={sizes_list}, durations={durations}")
    
    def test_performance_regression_detection(self, performance_tester, pdf_generator):
        """Test for performance regressions against baseline expectations"""
        if not _is_reportlab_available():
            pytest.skip("reportlab not available")
        
        # Define baseline performance expectations
        baseline_expectations = {
            'small_dataset': {'max_duration': 2.0, 'max_memory': 50},
            'medium_dataset': {'max_duration': 5.0, 'max_memory': 150},
            'large_dataset': {'max_duration': 10.0, 'max_memory': 500}
        }
        
        regression_results = {}
        
        for dataset_size, expectations in baseline_expectations.items():
            size_key = dataset_size.split('_')[0]  # Extract 'small', 'medium', 'large'
            test_data = performance_tester.generate_dataset(size_key, 'medium')
            
            def generate_pdf():
                return pdf_generator.generate_comprehensive_report(
                    summary=test_data['summary'],
                    risk_summary=test_data['risk_summary'],
                    resource_changes=test_data['resource_changes'],
                    resource_types=test_data['resource_types'],
                    plan_data=test_data['plan_data']
                )
            
            result = performance_tester.measure_performance(
                f"regression_{dataset_size}",
                generate_pdf
            )
            
            # Check against baseline expectations
            duration_ok = result.duration_seconds <= expectations['max_duration']
            memory_ok = result.memory_mb <= expectations['max_memory']
            
            regression_results[dataset_size] = {
                'duration': result.duration_seconds,
                'duration_ok': duration_ok,
                'duration_limit': expectations['max_duration'],
                'memory': result.memory_mb,
                'memory_ok': memory_ok,
                'memory_limit': expectations['max_memory'],
                'success': result.success
            }
            
            # Assert performance requirements
            assert result.success, f"Regression test {dataset_size} failed: {result.error_message}"
            assert duration_ok, f"Duration regression in {dataset_size}: {result.duration_seconds:.3f}s > {expectations['max_duration']}s"
            assert memory_ok, f"Memory regression in {dataset_size}: {result.memory_mb:.1f}MB > {expectations['max_memory']}MB"
            
            print(f"Regression {dataset_size}: {result.duration_seconds:.3f}s/{expectations['max_duration']}s, {result.memory_mb:.1f}MB/{expectations['max_memory']}MB")
        
        # Print summary
        print(f"Performance regression results: {regression_results}")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
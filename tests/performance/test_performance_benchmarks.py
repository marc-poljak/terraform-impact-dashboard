"""
Performance benchmarks and regression testing

Comprehensive performance benchmarks to establish baselines and detect regressions.
Includes automated performance reporting and threshold validation.
"""

import pytest
import time
import json
import statistics
import psutil
import gc
from typing import Dict, Any, List, Tuple
from dataclasses import dataclass
from pathlib import Path
import tempfile
import os

# Import components for benchmarking
from parsers.plan_parser import PlanParser
from ui.performance_optimizer import PerformanceOptimizer
from ui.session_manager import SessionStateManager
from ui.progress_tracker import ProgressTracker
from components.data_table import DataTableComponent
from components.visualizations import VisualizationsComponent
from visualizers.charts import ChartGenerator
from tests.integration.test_fixtures import TestFixtures


@dataclass
class BenchmarkResult:
    """Container for benchmark results"""
    name: str
    duration_seconds: float
    memory_mb: float
    operations_per_second: float
    success: bool
    error_message: str = ""
    metadata: Dict[str, Any] = None


class PerformanceBenchmarkSuite:
    """Comprehensive performance benchmark suite"""
    
    def __init__(self):
        # Create sample plan data for parser initialization
        sample_plan_data = {
            "format_version": "1.0",
            "terraform_version": "1.0.0",
            "resource_changes": []
        }
        self.parser = PlanParser(sample_plan_data)
        self.optimizer = PerformanceOptimizer()
        self.session_manager = SessionStateManager()
        self.progress_tracker = ProgressTracker()
        self.chart_generator = ChartGenerator()
        self.process = psutil.Process()
        
        # Performance thresholds based on requirements
        self.thresholds = {
            'large_file_processing': {'max_duration': 10.0, 'max_memory_mb': 500},
            'filter_operations': {'max_duration': 2.0, 'max_memory_mb': 100},
            'chart_rendering': {'max_duration': 5.0, 'max_memory_mb': 200},
            'small_file_processing': {'max_duration': 1.0, 'max_memory_mb': 50},
            'medium_file_processing': {'max_duration': 3.0, 'max_memory_mb': 150}
        }
        
        self.benchmark_results = []
    
    def run_benchmark(self, name: str, operation_func, *args, **kwargs) -> BenchmarkResult:
        """Run a single benchmark operation"""
        # Force garbage collection before benchmark
        gc.collect()
        initial_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        
        start_time = time.time()
        success = True
        error_message = ""
        operations_count = 1
        
        try:
            result = operation_func(*args, **kwargs)
            if isinstance(result, tuple) and len(result) == 2:
                # If operation returns (result, operations_count)
                _, operations_count = result
        except Exception as e:
            success = False
            error_message = str(e)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Measure peak memory usage
        peak_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        memory_used = peak_memory - initial_memory
        
        # Calculate operations per second
        ops_per_second = operations_count / max(duration, 0.001)
        
        benchmark_result = BenchmarkResult(
            name=name,
            duration_seconds=duration,
            memory_mb=memory_used,
            operations_per_second=ops_per_second,
            success=success,
            error_message=error_message,
            metadata={
                'operations_count': operations_count,
                'initial_memory_mb': initial_memory,
                'peak_memory_mb': peak_memory
            }
        )
        
        self.benchmark_results.append(benchmark_result)
        return benchmark_result
    
    def generate_test_plan(self, num_resources: int, complexity: str = 'medium') -> Dict[str, Any]:
        """Generate test plan with specified complexity"""
        base_plan = {
            "terraform_version": "1.6.0",
            "format_version": "1.2",
            "resource_changes": []
        }
        
        if complexity == 'simple':
            resource_types = ['aws_instance']
            actions = ['create']
        elif complexity == 'medium':
            resource_types = ['aws_instance', 'aws_s3_bucket', 'aws_security_group']
            actions = ['create', 'update']
        else:  # complex
            resource_types = [
                'aws_instance', 'aws_s3_bucket', 'aws_security_group', 'aws_rds_instance',
                'azurerm_virtual_machine', 'azurerm_storage_account',
                'google_compute_instance', 'google_storage_bucket'
            ]
            actions = ['create', 'update', 'delete']
        
        for i in range(num_resources):
            resource_type = resource_types[i % len(resource_types)]
            action = actions[i % len(actions)]
            
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
            
            resource_change = {
                "address": f"{resource_type}.resource_{i}",
                "mode": "managed",
                "type": resource_type,
                "name": f"resource_{i}",
                "provider_name": f"registry.terraform.io/hashicorp/{resource_type.split('_')[0]}",
                "change": {
                    "actions": [action],
                    "before": config if action in ["update", "delete"] else None,
                    "after": config if action in ["create", "update"] else None
                }
            }
            
            base_plan["resource_changes"].append(resource_change)
        
        return base_plan
    
    def benchmark_file_processing(self):
        """Benchmark file processing operations"""
        test_cases = [
            ('small_file_simple', 10, 'simple'),
            ('small_file_complex', 10, 'complex'),
            ('medium_file_simple', 100, 'simple'),
            ('medium_file_complex', 100, 'complex'),
            ('large_file_simple', 500, 'simple'),
            ('large_file_complex', 500, 'complex'),
            ('very_large_file', 1000, 'medium')
        ]
        
        for test_name, num_resources, complexity in test_cases:
            def process_file():
                plan_data = self.generate_test_plan(num_resources, complexity)
                parsed_data = self.parser.parse_plan(plan_data)
                df = self.optimizer.optimize_dataframe_creation(
                    parsed_data['resource_changes'], 
                    self.parser
                )
                return df, num_resources
            
            result = self.run_benchmark(f"file_processing_{test_name}", process_file)
            
            # Validate against thresholds
            if 'large' in test_name:
                threshold = self.thresholds['large_file_processing']
            elif 'medium' in test_name:
                threshold = self.thresholds['medium_file_processing']
            else:
                threshold = self.thresholds['small_file_processing']
            
            assert result.success, f"File processing benchmark failed: {result.error_message}"
            assert result.duration_seconds <= threshold['max_duration'], \
                f"{test_name} took {result.duration_seconds:.3f}s, max allowed: {threshold['max_duration']}s"
    
    def benchmark_filter_operations(self):
        """Benchmark filtering operations"""
        # Create large dataset for filtering
        plan_data = self.generate_test_plan(1000, 'complex')
        parsed_data = self.parser.parse_plan(plan_data)
        df = self.optimizer.optimize_dataframe_creation(
            parsed_data['resource_changes'], 
            self.parser
        )
        
        filter_operations = [
            ('action_filter', lambda: df[df['action'] == 'create']),
            ('type_filter', lambda: df[df['resource_type'] == 'aws_instance']),
            ('provider_filter', lambda: df[df['provider'] == 'aws']),
            ('combined_filter', lambda: df[
                (df['action'] == 'create') & 
                (df['resource_type'].str.contains('instance', case=False, na=False))
            ]),
            ('text_search', lambda: df[
                df['resource_address'].str.contains('resource_1', case=False, na=False)
            ]),
            ('complex_filter', lambda: df[
                (df['action'].isin(['create', 'update'])) &
                (df['resource_type'].str.contains('aws', case=False, na=False)) &
                (df['resource_address'].str.len() > 10)
            ])
        ]
        
        for filter_name, filter_func in filter_operations:
            result = self.run_benchmark(f"filter_{filter_name}", filter_func)
            
            threshold = self.thresholds['filter_operations']
            assert result.success, f"Filter benchmark failed: {result.error_message}"
            assert result.duration_seconds <= threshold['max_duration'], \
                f"{filter_name} took {result.duration_seconds:.3f}s, max allowed: {threshold['max_duration']}s"
    
    def benchmark_chart_operations(self):
        """Benchmark chart rendering operations"""
        # Prepare chart data
        resource_types = {f'aws_instance_{i}': i * 10 for i in range(20)}
        action_counts = {'create': 150, 'update': 100, 'delete': 50}
        risk_data = {'Low': 100, 'Medium': 80, 'High': 40, 'Critical': 20}
        
        chart_operations = [
            ('pie_chart_optimization', lambda: self.optimizer.optimize_chart_data_preparation(
                resource_types, 'pie_chart'
            )),
            ('bar_chart_optimization', lambda: self.optimizer.optimize_chart_data_preparation(
                action_counts, 'bar_chart'
            )),
            ('heatmap_optimization', lambda: self.optimizer.optimize_chart_data_preparation(
                risk_data, 'heatmap'
            )),
            ('large_dataset_chart', lambda: self.optimizer.optimize_chart_data_preparation(
                {f'type_{i}': i for i in range(100)}, 'pie_chart'
            ))
        ]
        
        for chart_name, chart_func in chart_operations:
            result = self.run_benchmark(f"chart_{chart_name}", chart_func)
            
            threshold = self.thresholds['chart_rendering']
            assert result.success, f"Chart benchmark failed: {result.error_message}"
            assert result.duration_seconds <= threshold['max_duration'], \
                f"{chart_name} took {result.duration_seconds:.3f}s, max allowed: {threshold['max_duration']}s"
    
    def benchmark_caching_performance(self):
        """Benchmark caching system performance"""
        plan_data = self.generate_test_plan(300, 'medium')
        parsed_data = self.parser.parse_plan(plan_data)
        
        # Benchmark without cache
        def process_without_cache():
            return self.optimizer.optimize_dataframe_creation(
                parsed_data['resource_changes'], 
                self.parser,
                use_cache=False
            )
        
        # Benchmark with cache (first run)
        def process_with_cache_first():
            self.optimizer.clear_cache()
            return self.optimizer.optimize_dataframe_creation(
                parsed_data['resource_changes'], 
                self.parser,
                use_cache=True
            )
        
        # Benchmark with cache (second run - should be faster)
        def process_with_cache_second():
            return self.optimizer.optimize_dataframe_creation(
                parsed_data['resource_changes'], 
                self.parser,
                use_cache=True
            )
        
        result_no_cache = self.run_benchmark("caching_no_cache", process_without_cache)
        result_cache_first = self.run_benchmark("caching_first_run", process_with_cache_first)
        result_cache_second = self.run_benchmark("caching_second_run", process_with_cache_second)
        
        # Verify caching improves performance
        if result_cache_first.duration_seconds > 0.001:
            improvement_ratio = result_cache_first.duration_seconds / max(result_cache_second.duration_seconds, 0.001)
            assert improvement_ratio > 1.2, f"Caching didn't improve performance enough: {improvement_ratio:.2f}x"
    
    def benchmark_concurrent_operations(self):
        """Benchmark concurrent processing performance"""
        import threading
        import queue
        
        def concurrent_processing():
            results_queue = queue.Queue()
            errors_queue = queue.Queue()
            
            def worker_thread(thread_id):
                try:
                    plan_data = self.generate_test_plan(100, 'medium')
                    parsed_data = self.parser.parse_plan(plan_data)
                    df = self.optimizer.optimize_dataframe_creation(
                        parsed_data['resource_changes'], 
                        self.parser
                    )
                    results_queue.put(len(df))
                except Exception as e:
                    errors_queue.put(str(e))
            
            # Start multiple threads
            threads = []
            for i in range(3):
                thread = threading.Thread(target=worker_thread, args=(i,))
                threads.append(thread)
                thread.start()
            
            # Wait for completion
            for thread in threads:
                thread.join(timeout=15)
            
            # Check results
            if not errors_queue.empty():
                raise Exception(f"Concurrent processing errors: {list(errors_queue.queue)}")
            
            results = []
            while not results_queue.empty():
                results.append(results_queue.get())
            
            return results, len(results)
        
        result = self.run_benchmark("concurrent_processing", concurrent_processing)
        assert result.success, f"Concurrent processing benchmark failed: {result.error_message}"
    
    def benchmark_memory_efficiency(self):
        """Benchmark memory efficiency across operations"""
        def memory_intensive_operations():
            operations_count = 0
            
            # Process multiple files
            for i in range(5):
                plan_data = self.generate_test_plan(200, 'medium')
                parsed_data = self.parser.parse_plan(plan_data)
                df = self.optimizer.optimize_dataframe_creation(
                    parsed_data['resource_changes'], 
                    self.parser
                )
                
                # Apply filters
                filtered_df = df[df['action'] == 'create']
                
                # Generate chart data
                chart_data = {'type_a': 50, 'type_b': 30}
                optimized_data = self.optimizer.optimize_chart_data_preparation(
                    chart_data, 'pie_chart'
                )
                
                operations_count += 4  # parse, dataframe, filter, chart
                
                # Clean up explicitly
                del plan_data, parsed_data, df, filtered_df, chart_data, optimized_data
                gc.collect()
            
            return None, operations_count
        
        result = self.run_benchmark("memory_efficiency", memory_intensive_operations)
        
        # Memory usage should be reasonable for multiple operations
        assert result.memory_mb < 300, f"Memory efficiency test used too much memory: {result.memory_mb:.2f}MB"
    
    def run_all_benchmarks(self):
        """Run all performance benchmarks"""
        print("Running performance benchmarks...")
        
        # File processing benchmarks
        print("  - File processing benchmarks...")
        self.benchmark_file_processing()
        
        # Filter operation benchmarks
        print("  - Filter operation benchmarks...")
        self.benchmark_filter_operations()
        
        # Chart operation benchmarks
        print("  - Chart operation benchmarks...")
        self.benchmark_chart_operations()
        
        # Caching performance benchmarks
        print("  - Caching performance benchmarks...")
        self.benchmark_caching_performance()
        
        # Concurrent operation benchmarks
        print("  - Concurrent operation benchmarks...")
        self.benchmark_concurrent_operations()
        
        # Memory efficiency benchmarks
        print("  - Memory efficiency benchmarks...")
        self.benchmark_memory_efficiency()
        
        print(f"Completed {len(self.benchmark_results)} benchmarks")
    
    def generate_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report"""
        if not self.benchmark_results:
            return {"error": "No benchmark results available"}
        
        # Calculate statistics
        successful_results = [r for r in self.benchmark_results if r.success]
        failed_results = [r for r in self.benchmark_results if not r.success]
        
        durations = [r.duration_seconds for r in successful_results]
        memory_usage = [r.memory_mb for r in successful_results]
        
        # Group results by category
        categories = {}
        for result in self.benchmark_results:
            category = result.name.split('_')[0]
            if category not in categories:
                categories[category] = []
            categories[category].append(result)
        
        # Generate report
        report = {
            "summary": {
                "total_benchmarks": len(self.benchmark_results),
                "successful": len(successful_results),
                "failed": len(failed_results),
                "success_rate": len(successful_results) / len(self.benchmark_results) * 100
            },
            "performance_stats": {
                "avg_duration_seconds": statistics.mean(durations) if durations else 0,
                "max_duration_seconds": max(durations) if durations else 0,
                "min_duration_seconds": min(durations) if durations else 0,
                "avg_memory_mb": statistics.mean(memory_usage) if memory_usage else 0,
                "max_memory_mb": max(memory_usage) if memory_usage else 0
            },
            "categories": {},
            "threshold_violations": [],
            "failed_benchmarks": [
                {"name": r.name, "error": r.error_message} for r in failed_results
            ],
            "detailed_results": [
                {
                    "name": r.name,
                    "duration_seconds": r.duration_seconds,
                    "memory_mb": r.memory_mb,
                    "ops_per_second": r.operations_per_second,
                    "success": r.success
                } for r in self.benchmark_results
            ]
        }
        
        # Add category statistics
        for category, results in categories.items():
            successful_category_results = [r for r in results if r.success]
            if successful_category_results:
                category_durations = [r.duration_seconds for r in successful_category_results]
                category_memory = [r.memory_mb for r in successful_category_results]
                
                report["categories"][category] = {
                    "count": len(results),
                    "successful": len(successful_category_results),
                    "avg_duration": statistics.mean(category_durations),
                    "avg_memory": statistics.mean(category_memory)
                }
        
        # Check threshold violations
        for result in successful_results:
            for threshold_name, threshold_values in self.thresholds.items():
                if threshold_name in result.name:
                    if result.duration_seconds > threshold_values['max_duration']:
                        report["threshold_violations"].append({
                            "benchmark": result.name,
                            "metric": "duration",
                            "value": result.duration_seconds,
                            "threshold": threshold_values['max_duration']
                        })
                    if result.memory_mb > threshold_values['max_memory_mb']:
                        report["threshold_violations"].append({
                            "benchmark": result.name,
                            "metric": "memory",
                            "value": result.memory_mb,
                            "threshold": threshold_values['max_memory_mb']
                        })
        
        return report
    
    def save_benchmark_results(self, filepath: str = None):
        """Save benchmark results to file"""
        if filepath is None:
            filepath = f"performance_benchmark_results_{int(time.time())}.json"
        
        report = self.generate_performance_report()
        
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2)
        
        return filepath


class TestPerformanceBenchmarks:
    """Test class for running performance benchmarks"""
    
    def setup_method(self):
        """Set up benchmark suite"""
        self.benchmark_suite = PerformanceBenchmarkSuite()
    
    def test_run_all_benchmarks(self):
        """Run all performance benchmarks and validate results"""
        # Run all benchmarks
        self.benchmark_suite.run_all_benchmarks()
        
        # Generate report
        report = self.benchmark_suite.generate_performance_report()
        
        # Validate results
        assert report["summary"]["total_benchmarks"] > 0, "No benchmarks were run"
        assert report["summary"]["success_rate"] >= 90, f"Too many benchmark failures: {report['summary']['success_rate']:.1f}% success rate"
        
        # Check for threshold violations
        if report["threshold_violations"]:
            violation_details = "\n".join([
                f"  - {v['benchmark']}: {v['metric']} = {v['value']:.3f}, threshold = {v['threshold']}"
                for v in report["threshold_violations"]
            ])
            pytest.fail(f"Performance threshold violations:\n{violation_details}")
        
        # Print summary for visibility
        print(f"\nPerformance Benchmark Summary:")
        print(f"  Total benchmarks: {report['summary']['total_benchmarks']}")
        print(f"  Success rate: {report['summary']['success_rate']:.1f}%")
        print(f"  Average duration: {report['performance_stats']['avg_duration_seconds']:.3f}s")
        print(f"  Average memory usage: {report['performance_stats']['avg_memory_mb']:.1f}MB")
        
        if report["failed_benchmarks"]:
            print(f"  Failed benchmarks:")
            for failure in report["failed_benchmarks"]:
                print(f"    - {failure['name']}: {failure['error']}")
    
    def test_performance_regression_detection(self):
        """Test for performance regressions against baseline"""
        # This test would compare against saved baseline results
        # For now, we'll just ensure current performance meets requirements
        
        self.benchmark_suite.run_all_benchmarks()
        report = self.benchmark_suite.generate_performance_report()
        
        # Key performance requirements from the spec
        requirements = [
            ("Large file processing should complete within 10 seconds", 
             lambda r: all(res['duration_seconds'] <= 10.0 
                          for res in r['detailed_results'] 
                          if 'large_file' in res['name'] and res['success'])),
            
            ("Filter operations should complete within 2 seconds",
             lambda r: all(res['duration_seconds'] <= 2.0 
                          for res in r['detailed_results'] 
                          if 'filter' in res['name'] and res['success'])),
            
            ("Chart operations should complete within 5 seconds",
             lambda r: all(res['duration_seconds'] <= 5.0 
                          for res in r['detailed_results'] 
                          if 'chart' in res['name'] and res['success']))
        ]
        
        for requirement_desc, requirement_check in requirements:
            assert requirement_check(report), f"Performance requirement not met: {requirement_desc}"
    
    def test_save_benchmark_results(self):
        """Test saving benchmark results to file"""
        self.benchmark_suite.run_all_benchmarks()
        
        # Save results to temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_filepath = f.name
        
        try:
            saved_filepath = self.benchmark_suite.save_benchmark_results(temp_filepath)
            
            # Verify file was created and contains valid JSON
            assert os.path.exists(saved_filepath), "Benchmark results file was not created"
            
            with open(saved_filepath, 'r') as f:
                loaded_report = json.load(f)
            
            # Verify report structure
            assert "summary" in loaded_report, "Report missing summary section"
            assert "performance_stats" in loaded_report, "Report missing performance stats"
            assert "detailed_results" in loaded_report, "Report missing detailed results"
            
        finally:
            # Clean up temporary file
            try:
                os.unlink(temp_filepath)
            except OSError:
                pass
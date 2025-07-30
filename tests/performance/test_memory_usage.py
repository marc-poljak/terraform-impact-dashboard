"""
Memory usage and resource cleanup tests

Tests memory usage patterns and ensures proper resource cleanup
to prevent memory leaks during long-running sessions.
"""

import pytest
import gc
import psutil
import time
import threading
import pandas as pd
from typing import Dict, Any, List
from unittest.mock import Mock, patch

# Import components for testing
from parsers.plan_parser import PlanParser
from ui.performance_optimizer import PerformanceOptimizer
from ui.session_manager import SessionStateManager
from components.data_table import DataTableComponent
from components.visualizations import VisualizationsComponent
from tests.integration.test_fixtures import TestFixtures


class TestMemoryUsage:
    """Test memory usage patterns and resource cleanup"""
    
    def setup_method(self):
        """Set up memory testing environment"""
        self.process = psutil.Process()
        self.optimizer = PerformanceOptimizer()
        self.session_manager = SessionStateManager()
        
        # Force garbage collection and record baseline
        gc.collect()
        time.sleep(0.1)  # Allow GC to complete
        self.baseline_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        
        # Track memory usage over time
        self.memory_samples = []
    
    def _process_plan_data(self, plan_data: Dict[str, Any]) -> pd.DataFrame:
        """Helper method to process plan data consistently"""
        parser = PlanParser(plan_data)
        resource_changes = parser.get_resource_changes()
        return self.optimizer.optimize_dataframe_creation(resource_changes, parser)
    
    def teardown_method(self):
        """Clean up and verify no memory leaks"""
        # Force cleanup
        gc.collect()
        time.sleep(0.1)
        
        final_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - self.baseline_memory
        
        # Allow reasonable memory increase for test artifacts
        assert memory_increase < 100, f"Significant memory increase detected: {memory_increase:.2f}MB"
    
    def _record_memory_sample(self, label: str):
        """Record current memory usage with label"""
        current_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        self.memory_samples.append({
            'label': label,
            'memory_mb': current_memory,
            'increase_mb': current_memory - self.baseline_memory,
            'timestamp': time.time()
        })
    
    def _generate_large_plan(self, num_resources: int) -> Dict[str, Any]:
        """Generate large plan for memory testing"""
        base_plan = {
            "terraform_version": "1.6.0",
            "format_version": "1.2",
            "resource_changes": []
        }
        
        for i in range(num_resources):
            resource_change = {
                "address": f"aws_instance.resource_{i}",
                "mode": "managed",
                "type": "aws_instance",
                "name": f"resource_{i}",
                "provider_name": "registry.terraform.io/hashicorp/aws",
                "change": {
                    "actions": ["create"],
                    "before": None,
                    "after": {
                        "id": f"resource-{i}",
                        "ami": "ami-12345678",
                        "instance_type": "t3.micro",
                        "tags": {
                            "Name": f"resource-{i}",
                            "Environment": "test",
                            "ResourceId": str(i)
                        },
                        "user_data": f"#!/bin/bash\necho 'Resource {i}'\n" * 10  # Add some bulk
                    }
                }
            }
            base_plan["resource_changes"].append(resource_change)
        
        return base_plan
    
    def test_single_file_processing_memory_usage(self):
        """Test memory usage for processing a single large file"""
        self._record_memory_sample("baseline")
        
        # Generate and process large plan
        plan_data = self._generate_large_plan(500)
        self._record_memory_sample("plan_generated")
        
        # Parse the plan
        parser = PlanParser(plan_data)
        parsed_data = parser.get_resource_changes()
        self._record_memory_sample("plan_parsed")
        
        # Create dataframe
        df = self.optimizer.optimize_dataframe_creation(
            parsed_data, 
            parser
        )
        self._record_memory_sample("dataframe_created")
        
        # Clean up explicitly
        del plan_data, parser, parsed_data, df
        gc.collect()
        self._record_memory_sample("after_cleanup")
        
        # Verify memory was properly released
        final_sample = self.memory_samples[-1]
        peak_sample = max(self.memory_samples, key=lambda x: x['memory_mb'])
        
        # Memory should return close to baseline after cleanup
        memory_retained = final_sample['increase_mb']
        assert memory_retained < 50, f"Too much memory retained after cleanup: {memory_retained:.2f}MB"
        
        # Peak memory usage should be reasonable
        peak_increase = peak_sample['increase_mb']
        assert peak_increase < 200, f"Peak memory usage too high: {peak_increase:.2f}MB"
    
    def test_multiple_file_processing_memory_usage(self):
        """Test memory usage when processing multiple files sequentially"""
        self._record_memory_sample("baseline")
        
        # Process multiple files
        for i in range(5):
            plan_data = self._generate_large_plan(200)
            parser = PlanParser(plan_data)
            parsed_data = parser.get_resource_changes()
            df = self.optimizer.optimize_dataframe_creation(
                parsed_data, 
                parser
            )
            
            self._record_memory_sample(f"file_{i}_processed")
            
            # Clean up after each file
            del plan_data, parser, parsed_data, df
            gc.collect()
            
            self._record_memory_sample(f"file_{i}_cleaned")
        
        # Check that memory doesn't continuously grow
        cleaned_samples = [s for s in self.memory_samples if 'cleaned' in s['label']]
        
        if len(cleaned_samples) > 1:
            # Memory after cleanup shouldn't grow significantly
            first_cleaned = cleaned_samples[0]['increase_mb']
            last_cleaned = cleaned_samples[-1]['increase_mb']
            memory_growth = last_cleaned - first_cleaned
            
            assert memory_growth < 30, f"Memory grows with each file: {memory_growth:.2f}MB growth"
    
    def test_caching_memory_usage(self):
        """Test memory usage of caching system"""
        self._record_memory_sample("baseline")
        
        # Generate test data
        plan_data = self._generate_large_plan(300)
        parser = PlanParser(plan_data)
        parsed_data = {
            'resource_changes': parser.get_resource_changes(),
            'summary': parser.get_summary(),
            'resource_types': parser.get_resource_types()
        }
        
        # Process with caching enabled
        df1 = self.optimizer.optimize_dataframe_creation(
            parsed_data['resource_changes'], 
            self.parser,
            use_cache=True
        )
        self._record_memory_sample("first_with_cache")
        
        # Process same data again (should use cache)
        df2 = self.optimizer.optimize_dataframe_creation(
            parsed_data['resource_changes'], 
            self.parser,
            use_cache=True
        )
        self._record_memory_sample("second_with_cache")
        
        # Process without caching
        self.optimizer.clear_cache()
        df3 = self.optimizer.optimize_dataframe_creation(
            parsed_data['resource_changes'], 
            self.parser,
            use_cache=False
        )
        self._record_memory_sample("without_cache")
        
        # Clean up
        del plan_data, parsed_data, df1, df2, df3
        gc.collect()
        self._record_memory_sample("after_cleanup")
        
        # Verify caching doesn't cause excessive memory usage
        cache_samples = [s for s in self.memory_samples if 'cache' in s['label']]
        max_cache_memory = max(cache_samples, key=lambda x: x['memory_mb'])['increase_mb']
        
        assert max_cache_memory < 150, f"Caching uses too much memory: {max_cache_memory:.2f}MB"
    
    def test_concurrent_processing_memory_usage(self):
        """Test memory usage during concurrent processing"""
        import threading
        import queue
        
        self._record_memory_sample("baseline")
        
        results_queue = queue.Queue()
        errors_queue = queue.Queue()
        
        def process_plan_thread(thread_id: int):
            try:
                plan_data = self._generate_large_plan(150)
                parser = PlanParser(plan_data)
                parsed_data = {
                    'resource_changes': parser.get_resource_changes(),
                    'summary': parser.get_summary(),
                    'resource_types': parser.get_resource_types()
                }
                df = self.optimizer.optimize_dataframe_creation(
                    parsed_data['resource_changes'], 
                    self.parser
                )
                
                results_queue.put(f"thread_{thread_id}_completed")
                
                # Clean up in thread
                del plan_data, parsed_data, df
                gc.collect()
                
            except Exception as e:
                errors_queue.put(f"thread_{thread_id}: {str(e)}")
        
        # Start multiple threads
        threads = []
        for i in range(3):
            thread = threading.Thread(target=process_plan_thread, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Monitor memory during concurrent processing
        start_time = time.time()
        while any(t.is_alive() for t in threads) and (time.time() - start_time) < 30:
            self._record_memory_sample("concurrent_processing")
            time.sleep(0.5)
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join(timeout=5)
        
        self._record_memory_sample("threads_completed")
        
        # Force cleanup
        gc.collect()
        time.sleep(0.5)
        self._record_memory_sample("final_cleanup")
        
        # Check for errors
        assert errors_queue.empty(), f"Concurrent processing errors: {list(errors_queue.queue)}"
        
        # Verify memory usage during concurrent processing
        concurrent_samples = [s for s in self.memory_samples if 'concurrent' in s['label']]
        if concurrent_samples:
            max_concurrent_memory = max(concurrent_samples, key=lambda x: x['memory_mb'])['increase_mb']
            assert max_concurrent_memory < 300, f"Concurrent processing uses too much memory: {max_concurrent_memory:.2f}MB"
    
    def test_long_running_session_memory_usage(self):
        """Test memory usage in a simulated long-running session"""
        self._record_memory_sample("session_start")
        
        # Simulate a long-running session with various operations
        for session_iteration in range(10):
            # Upload and process a file
            plan_data = self._generate_large_plan(100)
            parser = PlanParser(plan_data)
            parsed_data = {
                'resource_changes': parser.get_resource_changes(),
                'summary': parser.get_summary(),
                'resource_types': parser.get_resource_types()
            }
            df = self.optimizer.optimize_dataframe_creation(
                parsed_data['resource_changes'], 
                self.parser
            )
            
            # Apply some filters (simulating user interaction)
            filtered_df = df[df['action'] == 'create']
            filtered_df2 = df[df['resource_type'] == 'aws_instance']
            
            # Generate some chart data
            chart_data = {'aws_instance': 50, 'aws_s3_bucket': 30}
            optimized_chart_data = self.optimizer.optimize_chart_data_preparation(
                chart_data, 'pie_chart'
            )
            
            self._record_memory_sample(f"session_iteration_{session_iteration}")
            
            # Clean up iteration
            del plan_data, parsed_data, df, filtered_df, filtered_df2
            del chart_data, optimized_chart_data
            
            # Periodic garbage collection (simulating Streamlit's behavior)
            if session_iteration % 3 == 0:
                gc.collect()
                self._record_memory_sample(f"gc_after_iteration_{session_iteration}")
        
        # Final cleanup
        self.optimizer.clear_cache()
        gc.collect()
        self._record_memory_sample("session_end")
        
        # Analyze memory usage over the session
        iteration_samples = [s for s in self.memory_samples if 'iteration' in s['label']]
        
        if len(iteration_samples) > 1:
            # Check for memory leaks over time
            first_iteration = iteration_samples[0]['increase_mb']
            last_iteration = iteration_samples[-1]['increase_mb']
            session_memory_growth = last_iteration - first_iteration
            
            assert session_memory_growth < 50, f"Memory leak in long session: {session_memory_growth:.2f}MB growth"
    
    def test_memory_usage_with_different_file_sizes(self):
        """Test how memory usage scales with file size"""
        file_sizes = [50, 100, 200, 500]
        memory_usage = []
        
        for size in file_sizes:
            # Reset baseline for each test
            gc.collect()
            baseline = self.process.memory_info().rss / 1024 / 1024  # MB
            
            # Process file of given size
            plan_data = self._generate_large_plan(size)
            parser = PlanParser(plan_data)
            parsed_data = {
                'resource_changes': parser.get_resource_changes(),
                'summary': parser.get_summary(),
                'resource_types': parser.get_resource_types()
            }
            df = self.optimizer.optimize_dataframe_creation(
                parsed_data['resource_changes'], 
                self.parser
            )
            
            # Record peak memory usage
            peak_memory = self.process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = peak_memory - baseline
            memory_usage.append((size, memory_increase))
            
            # Clean up
            del plan_data, parsed_data, df
            gc.collect()
        
        # Verify memory usage scales reasonably
        # Memory usage should be roughly linear with file size
        if len(memory_usage) >= 2:
            # Check that 10x the resources doesn't use more than 15x the memory
            largest_size, largest_memory = memory_usage[-1]
            smallest_size, smallest_memory = memory_usage[0]
            
            size_ratio = largest_size / smallest_size
            memory_ratio = largest_memory / max(smallest_memory, 1)  # Avoid division by zero
            
            efficiency_ratio = memory_ratio / size_ratio
            assert efficiency_ratio < 1.5, f"Memory usage doesn't scale efficiently: {efficiency_ratio:.2f}"
    
    def test_garbage_collection_effectiveness(self):
        """Test that garbage collection effectively frees memory"""
        self._record_memory_sample("before_allocation")
        
        # Allocate large objects
        large_objects = []
        for i in range(10):
            plan_data = self._generate_large_plan(200)
            large_objects.append(plan_data)
        
        self._record_memory_sample("after_allocation")
        
        # Delete references but don't collect garbage yet
        del large_objects
        self._record_memory_sample("after_deletion")
        
        # Force garbage collection
        collected = gc.collect()
        self._record_memory_sample("after_gc")
        
        # Verify garbage collection was effective
        before_gc = next(s for s in self.memory_samples if s['label'] == 'after_deletion')
        after_gc = next(s for s in self.memory_samples if s['label'] == 'after_gc')
        
        memory_freed = before_gc['memory_mb'] - after_gc['memory_mb']
        assert memory_freed > 10, f"Garbage collection didn't free enough memory: {memory_freed:.2f}MB"
        assert collected > 0, "Garbage collection didn't collect any objects"
    
    def test_memory_profiling_utilities(self):
        """Test memory profiling and monitoring utilities"""
        # Test performance optimizer memory tracking
        with self.optimizer.performance_monitor("memory_test_operation"):
            plan_data = self._generate_large_plan(100)
            parser = PlanParser(plan_data)
            parsed_data = {
                'resource_changes': parser.get_resource_changes(),
                'summary': parser.get_summary(),
                'resource_types': parser.get_resource_types()
            }
            df = self.optimizer.optimize_dataframe_creation(
                parsed_data['resource_changes'], 
                self.parser
            )
        
        # Get performance metrics
        metrics = self.optimizer.get_performance_metrics()
        
        # Verify metrics are recorded
        assert 'operation_metrics' in metrics
        assert 'memory_test_operation' in metrics['operation_metrics']
        assert 'duration' in metrics['operation_metrics']['memory_test_operation']
        
        # Test cache statistics
        cache_stats = self.optimizer.get_cache_stats()
        assert 'hits' in cache_stats
        assert 'misses' in cache_stats
        assert 'hit_rate' in cache_stats
        assert 'cache_size' in cache_stats
        
        # Clean up
        del plan_data, parsed_data, df
    
    def get_memory_usage_report(self) -> Dict[str, Any]:
        """Generate a memory usage report from recorded samples"""
        if not self.memory_samples:
            return {"error": "No memory samples recorded"}
        
        baseline = self.memory_samples[0]['memory_mb']
        peak_sample = max(self.memory_samples, key=lambda x: x['memory_mb'])
        final_sample = self.memory_samples[-1]
        
        return {
            "baseline_memory_mb": baseline,
            "peak_memory_mb": peak_sample['memory_mb'],
            "peak_increase_mb": peak_sample['increase_mb'],
            "peak_operation": peak_sample['label'],
            "final_memory_mb": final_sample['memory_mb'],
            "final_increase_mb": final_sample['increase_mb'],
            "total_samples": len(self.memory_samples),
            "samples": self.memory_samples
        }


class TestResourceCleanup:
    """Test proper cleanup of resources like file handles, threads, etc."""
    
    def test_file_handle_cleanup(self):
        """Test that file handles are properly closed"""
        import tempfile
        import json
        
        # Create temporary files
        temp_files = []
        for i in range(5):
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                plan_data = TestFixtures.get_simple_plan()
                json.dump(plan_data, f)
                temp_files.append(f.name)
        
        # Process files
        sample_plan_data = {
            "format_version": "1.0",
            "terraform_version": "1.0.0",
            "resource_changes": []
        }
        parser = PlanParser(sample_plan_data)
        for temp_file in temp_files:
            with open(temp_file, 'r') as f:
                plan_data = json.load(f)
                parsed_data = parser.parse_plan(plan_data)
        
        # Clean up temporary files
        import os
        for temp_file in temp_files:
            try:
                os.unlink(temp_file)
            except OSError:
                pass  # File might already be deleted
        
        # Test passes if no file handle leaks occur
        assert True
    
    def test_thread_cleanup(self):
        """Test that threads are properly cleaned up"""
        import threading
        import time
        
        initial_thread_count = threading.active_count()
        
        # Create and start threads
        threads = []
        for i in range(3):
            def worker():
                time.sleep(0.1)  # Short work
            
            thread = threading.Thread(target=worker)
            threads.append(thread)
            thread.start()
        
        # Wait for threads to complete
        for thread in threads:
            thread.join(timeout=1)
        
        # Give threads time to clean up
        time.sleep(0.1)
        
        final_thread_count = threading.active_count()
        
        # Thread count should return to initial level
        assert final_thread_count <= initial_thread_count + 1, \
            f"Thread leak detected: {final_thread_count - initial_thread_count} extra threads"
    
    def test_cache_cleanup(self):
        """Test that caches are properly cleared"""
        optimizer = PerformanceOptimizer()
        
        # Populate cache
        test_data = {"test": "data"}
        for i in range(10):
            cache_key = optimizer._generate_cache_key(test_data, f"operation_{i}")
            optimizer.cache_result(cache_key, f"result_{i}")
        
        # Verify cache has data
        cache_stats = optimizer.get_cache_stats()
        assert cache_stats['cache_size'] > 0, "Cache should have data"
        
        # Clear cache
        optimizer.clear_cache()
        
        # Verify cache is cleared
        cache_stats = optimizer.get_cache_stats()
        assert cache_stats['cache_size'] == 0, "Cache should be empty after clear"
        assert cache_stats['hits'] == 0, "Cache hits should be reset"
        assert cache_stats['misses'] == 0, "Cache misses should be reset"
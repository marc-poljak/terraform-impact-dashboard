"""
Performance tests for large file processing

Tests file processing performance to ensure it meets the requirement of
completing within 10 seconds for large files.
"""

import pytest
import time
import json
import tempfile
import os
import psutil
import gc
import pandas as pd
from typing import Dict, Any, List
from unittest.mock import Mock, patch

# Import the components and utilities we need to test
from parsers.plan_parser import PlanParser
from ui.performance_optimizer import PerformanceOptimizer
from ui.progress_tracker import ProgressTracker
from tests.integration.test_fixtures import TestFixtures


class TestLargeFilePerformance:
    """Test performance with large Terraform plan files"""
    
    def setup_method(self):
        """Set up test environment"""
        self.optimizer = PerformanceOptimizer()
        self.progress_tracker = ProgressTracker()
        self.process = psutil.Process()
        
        # Record initial memory usage
        self.initial_memory = self.process.memory_info().rss / 1024 / 1024  # MB
    
    def _process_plan_data(self, plan_data: Dict[str, Any]) -> pd.DataFrame:
        """Helper method to process plan data consistently"""
        parser = PlanParser(plan_data)
        resource_changes = parser.get_resource_changes()
        return self.optimizer.optimize_dataframe_creation(resource_changes, parser)
        
    def teardown_method(self):
        """Clean up after tests"""
        # Force garbage collection
        gc.collect()
        
        # Check for memory leaks
        final_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - self.initial_memory
        
        # Allow up to 50MB memory increase per test (reasonable for caching)
        assert memory_increase < 50, f"Memory leak detected: {memory_increase:.2f}MB increase"
    
    def generate_large_plan(self, num_resources: int) -> Dict[str, Any]:
        """Generate a large Terraform plan with specified number of resources"""
        base_plan = {
            "terraform_version": "1.6.0",
            "format_version": "1.2",
            "resource_changes": []
        }
        
        providers = [
            ("aws", ["aws_instance", "aws_s3_bucket", "aws_security_group", "aws_rds_instance", "aws_vpc", "aws_subnet"]),
            ("azure", ["azurerm_virtual_machine", "azurerm_storage_account", "azurerm_network_security_group", "azurerm_resource_group"]),
            ("gcp", ["google_compute_instance", "google_storage_bucket", "google_compute_firewall", "google_compute_network"])
        ]
        
        actions = ["create", "update", "delete"]
        
        for i in range(num_resources):
            provider_name, resource_types = providers[i % len(providers)]
            resource_type = resource_types[i % len(resource_types)]
            action = actions[i % len(actions)]
            
            # Create more complex resource configurations
            resource_change = {
                "address": f"{resource_type}.resource_{i}",
                "mode": "managed",
                "type": resource_type,
                "name": f"resource_{i}",
                "provider_name": f"registry.terraform.io/hashicorp/{provider_name}",
                "change": {
                    "actions": [action],
                    "before": self._generate_resource_config(resource_type, f"old-{i}") if action in ["update", "delete"] else None,
                    "after": self._generate_resource_config(resource_type, f"new-{i}") if action in ["create", "update"] else None
                }
            }
            
            base_plan["resource_changes"].append(resource_change)
        
        return base_plan
    
    def _generate_resource_config(self, resource_type: str, resource_id: str) -> Dict[str, Any]:
        """Generate realistic resource configuration based on type"""
        base_config = {
            "id": resource_id,
            "name": f"resource-{resource_id}",
            "tags": {
                "Environment": "test",
                "ManagedBy": "terraform",
                "ResourceId": resource_id
            }
        }
        
        # Add type-specific configurations
        if "instance" in resource_type:
            base_config.update({
                "instance_type": "t3.micro",
                "ami": "ami-12345678",
                "security_groups": [f"sg-{resource_id}"],
                "user_data": "#!/bin/bash\necho 'Hello World'"
            })
        elif "bucket" in resource_type or "storage" in resource_type:
            base_config.update({
                "versioning": [{"enabled": True}],
                "encryption": [{"sse_algorithm": "AES256"}],
                "lifecycle_rule": [{"enabled": True, "expiration": [{"days": 30}]}]
            })
        elif "security_group" in resource_type or "firewall" in resource_type:
            base_config.update({
                "ingress": [
                    {
                        "from_port": 80,
                        "to_port": 80,
                        "protocol": "tcp",
                        "cidr_blocks": ["0.0.0.0/0"]
                    },
                    {
                        "from_port": 443,
                        "to_port": 443,
                        "protocol": "tcp",
                        "cidr_blocks": ["0.0.0.0/0"]
                    }
                ],
                "egress": [
                    {
                        "from_port": 0,
                        "to_port": 65535,
                        "protocol": "tcp",
                        "cidr_blocks": ["0.0.0.0/0"]
                    }
                ]
            })
        
        return base_config
    
    def test_small_file_processing_performance(self):
        """Test processing performance with small files (baseline)"""
        plan_data = TestFixtures.get_simple_plan()
        
        start_time = time.time()
        df = self._process_plan_data(plan_data)
        end_time = time.time()
        
        processing_time = end_time - start_time
        
        # Small files should process very quickly (< 1 second)
        assert processing_time < 1.0, f"Small file processing took {processing_time:.2f}s, expected < 1s"
        
        # Verify data integrity
        assert not df.empty
    
    def test_medium_file_processing_performance(self):
        """Test processing performance with medium files (100 resources)"""
        plan_data = self.generate_large_plan(100)
        
        start_time = time.time()
        df = self._process_plan_data(plan_data)
        end_time = time.time()
        
        processing_time = end_time - start_time
        
        # Medium files should process within 3 seconds
        assert processing_time < 3.0, f"Medium file processing took {processing_time:.2f}s, expected < 3s"
        
        # Verify data integrity
        assert not df.empty
    
    def test_large_file_processing_performance(self):
        """Test processing performance with large files (500 resources)"""
        plan_data = self.generate_large_plan(500)
        
        start_time = time.time()
        df = self._process_plan_data(plan_data)
        end_time = time.time()
        
        processing_time = end_time - start_time
        
        # Large files should process within 10 seconds (requirement)
        assert processing_time < 10.0, f"Large file processing took {processing_time:.2f}s, expected < 10s"
        
        # Verify data integrity
        assert not df.empty
    
    def test_very_large_file_processing_performance(self):
        """Test processing performance with very large files (1000 resources)"""
        plan_data = self.generate_large_plan(1000)
        
        start_time = time.time()
        
        # Parse the plan
        parsed_data = self.parser.parse_plan(plan_data)
        
        # Create dataframe with optimization and chunking
        df = self.optimizer.optimize_dataframe_creation(
            parsed_data['resource_changes'], 
            self.parser
        )
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Very large files should still process within 10 seconds with optimization
        assert processing_time < 10.0, f"Very large file processing took {processing_time:.2f}s, expected < 10s"
        
        # Verify data integrity
        assert len(df) == len(parsed_data['resource_changes'])
        assert not df.empty
    
    def test_memory_usage_with_large_files(self):
        """Test memory usage doesn't grow excessively with large files"""
        initial_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        
        # Process multiple large files to test memory cleanup
        for i in range(3):
            plan_data = self.generate_large_plan(300)
            parsed_data = self.parser.parse_plan(plan_data)
            df = self.optimizer.optimize_dataframe_creation(
                parsed_data['resource_changes'], 
                self.parser
            )
            
            # Force garbage collection after each iteration
            del df, parsed_data, plan_data
            gc.collect()
        
        final_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (< 100MB for multiple large files)
        assert memory_increase < 100, f"Excessive memory usage: {memory_increase:.2f}MB increase"
    
    def test_caching_performance_improvement(self):
        """Test that caching improves performance for repeated operations"""
        plan_data = self.generate_large_plan(200)
        parsed_data = self.parser.parse_plan(plan_data)
        
        # First run (no cache)
        start_time = time.time()
        df1 = self.optimizer.optimize_dataframe_creation(
            parsed_data['resource_changes'], 
            self.parser,
            use_cache=True
        )
        first_run_time = time.time() - start_time
        
        # Second run (with cache)
        start_time = time.time()
        df2 = self.optimizer.optimize_dataframe_creation(
            parsed_data['resource_changes'], 
            self.parser,
            use_cache=True
        )
        second_run_time = time.time() - start_time
        
        # Second run should be significantly faster (at least 50% improvement)
        improvement_ratio = first_run_time / max(second_run_time, 0.001)  # Avoid division by zero
        assert improvement_ratio > 1.5, f"Caching didn't improve performance enough: {improvement_ratio:.2f}x"
        
        # Results should be identical
        assert df1.equals(df2), "Cached results don't match original results"
        
        # Check cache statistics
        cache_stats = self.optimizer.get_cache_stats()
        assert cache_stats['hits'] > 0, "Cache hits should be recorded"
        assert cache_stats['hit_rate'] > 0, "Cache hit rate should be positive"
    
    def test_chunked_processing_performance(self):
        """Test that chunked processing works correctly for large datasets"""
        plan_data = self.generate_large_plan(600)
        parsed_data = self.parser.parse_plan(plan_data)
        
        start_time = time.time()
        
        # Process in chunks
        all_chunks = []
        for chunk in self.optimizer.chunk_process_resources(parsed_data['resource_changes'], chunk_size=100):
            all_chunks.append(chunk)
        
        processing_time = time.time() - start_time
        
        # Chunked processing should be fast
        assert processing_time < 1.0, f"Chunked processing took {processing_time:.2f}s, expected < 1s"
        
        # Verify all resources are included
        total_resources = sum(len(chunk) for chunk in all_chunks)
        assert total_resources == len(parsed_data['resource_changes'])
        
        # Verify chunk sizes
        for chunk in all_chunks[:-1]:  # All but last chunk
            assert len(chunk) == 100, f"Chunk size should be 100, got {len(chunk)}"
        
        # Last chunk can be smaller
        assert len(all_chunks[-1]) <= 100, f"Last chunk too large: {len(all_chunks[-1])}"
    
    def test_progress_tracking_performance(self):
        """Test that progress tracking doesn't significantly impact performance"""
        plan_data = self.generate_large_plan(300)
        
        # Test without progress tracking
        start_time = time.time()
        parsed_data = self.parser.parse_plan(plan_data)
        df_no_progress = self.optimizer.optimize_dataframe_creation(
            parsed_data['resource_changes'], 
            self.parser
        )
        time_without_progress = time.time() - start_time
        
        # Test with progress tracking
        start_time = time.time()
        with self.progress_tracker.track_progress("Processing large file", len(parsed_data['resource_changes'])):
            df_with_progress = self.optimizer.optimize_dataframe_creation(
                parsed_data['resource_changes'], 
                self.parser
            )
        time_with_progress = time.time() - start_time
        
        # Progress tracking should add minimal overhead (< 20%)
        overhead_ratio = time_with_progress / max(time_without_progress, 0.001)
        assert overhead_ratio < 1.2, f"Progress tracking adds too much overhead: {overhead_ratio:.2f}x"
        
        # Results should be identical
        assert df_no_progress.equals(df_with_progress), "Progress tracking affected results"
    
    def test_file_size_scaling(self):
        """Test how processing time scales with file size"""
        file_sizes = [50, 100, 200, 400]
        processing_times = []
        
        for size in file_sizes:
            plan_data = self.generate_large_plan(size)
            
            start_time = time.time()
            parsed_data = self.parser.parse_plan(plan_data)
            df = self.optimizer.optimize_dataframe_creation(
                parsed_data['resource_changes'], 
                self.parser
            )
            processing_time = time.time() - start_time
            processing_times.append(processing_time)
            
            # Clean up
            del df, parsed_data, plan_data
            gc.collect()
        
        # Processing time should scale reasonably (not exponentially)
        # Check that 8x the data doesn't take more than 10x the time
        time_ratio = processing_times[-1] / max(processing_times[0], 0.001)
        size_ratio = file_sizes[-1] / file_sizes[0]  # 8x
        
        efficiency_ratio = time_ratio / size_ratio
        assert efficiency_ratio < 1.25, f"Processing doesn't scale well: {efficiency_ratio:.2f}"
    
    def test_concurrent_processing_safety(self):
        """Test that concurrent processing doesn't cause issues"""
        import threading
        import queue
        
        plan_data = self.generate_large_plan(200)
        results_queue = queue.Queue()
        errors_queue = queue.Queue()
        
        def process_plan():
            try:
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
            thread = threading.Thread(target=process_plan)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join(timeout=15)  # 15 second timeout
        
        # Check results
        assert errors_queue.empty(), f"Concurrent processing errors: {list(errors_queue.queue)}"
        
        results = []
        while not results_queue.empty():
            results.append(results_queue.get())
        
        assert len(results) == 3, f"Expected 3 results, got {len(results)}"
        
        # All results should be the same
        assert all(r == results[0] for r in results), "Concurrent processing gave different results"


class TestPerformanceBenchmarks:
    """Performance benchmarks and regression tests"""
    
    def setup_method(self):
        """Set up benchmarking environment"""
        self.parser = PlanParser()
        self.optimizer = PerformanceOptimizer()
        self.benchmarks = {}
    
    def test_baseline_performance_benchmarks(self):
        """Establish baseline performance benchmarks"""
        test_cases = [
            ("small", 10),
            ("medium", 100),
            ("large", 500),
            ("very_large", 1000)
        ]
        
        for case_name, num_resources in test_cases:
            plan_data = self._generate_benchmark_plan(num_resources)
            
            # Measure parsing time
            start_time = time.time()
            parsed_data = self.parser.parse_plan(plan_data)
            parse_time = time.time() - start_time
            
            # Measure dataframe creation time
            start_time = time.time()
            df = self.optimizer.optimize_dataframe_creation(
                parsed_data['resource_changes'], 
                self.parser
            )
            df_time = time.time() - start_time
            
            # Store benchmark
            self.benchmarks[case_name] = {
                'resources': num_resources,
                'parse_time': parse_time,
                'df_time': df_time,
                'total_time': parse_time + df_time,
                'memory_mb': psutil.Process().memory_info().rss / 1024 / 1024
            }
        
        # Verify benchmarks meet requirements
        assert self.benchmarks['large']['total_time'] < 10.0, "Large file benchmark exceeds 10s requirement"
        assert self.benchmarks['very_large']['total_time'] < 10.0, "Very large file benchmark exceeds 10s requirement"
        
        # Print benchmarks for reference
        print("\nPerformance Benchmarks:")
        for case_name, metrics in self.benchmarks.items():
            print(f"{case_name}: {metrics['resources']} resources, "
                  f"{metrics['total_time']:.3f}s total, "
                  f"{metrics['memory_mb']:.1f}MB memory")
    
    def _generate_benchmark_plan(self, num_resources: int) -> Dict[str, Any]:
        """Generate standardized plan for benchmarking"""
        base_plan = {
            "terraform_version": "1.6.0",
            "format_version": "1.2",
            "resource_changes": []
        }
        
        # Use consistent resource types for benchmarking
        resource_types = [
            "aws_instance",
            "aws_s3_bucket", 
            "aws_security_group",
            "azurerm_virtual_machine",
            "google_compute_instance"
        ]
        
        actions = ["create", "update", "delete"]
        
        for i in range(num_resources):
            resource_type = resource_types[i % len(resource_types)]
            action = actions[i % len(actions)]
            
            resource_change = {
                "address": f"{resource_type}.resource_{i}",
                "mode": "managed",
                "type": resource_type,
                "name": f"resource_{i}",
                "provider_name": f"registry.terraform.io/hashicorp/{resource_type.split('_')[0]}",
                "change": {
                    "actions": [action],
                    "before": {"id": f"old-{i}"} if action in ["update", "delete"] else None,
                    "after": {"id": f"new-{i}", "name": f"resource-{i}"} if action in ["create", "update"] else None
                }
            }
            
            base_plan["resource_changes"].append(resource_change)
        
        return base_plan
    
    def test_performance_regression_detection(self):
        """Test for performance regressions"""
        # Define acceptable performance thresholds based on requirements
        thresholds = {
            'small': {'max_time': 0.5, 'max_memory_mb': 50},
            'medium': {'max_time': 2.0, 'max_memory_mb': 100},
            'large': {'max_time': 8.0, 'max_memory_mb': 200},  # Under 10s requirement
            'very_large': {'max_time': 9.5, 'max_memory_mb': 300}  # Under 10s requirement
        }
        
        for case_name, threshold in thresholds.items():
            if case_name in self.benchmarks:
                benchmark = self.benchmarks[case_name]
                
                assert benchmark['total_time'] <= threshold['max_time'], \
                    f"Performance regression in {case_name}: {benchmark['total_time']:.3f}s > {threshold['max_time']}s"
                
                assert benchmark['memory_mb'] <= threshold['max_memory_mb'], \
                    f"Memory regression in {case_name}: {benchmark['memory_mb']:.1f}MB > {threshold['max_memory_mb']}MB"
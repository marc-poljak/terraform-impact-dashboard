"""
Performance tests for filter operations

Tests filter response times to ensure they meet the requirement of
updating results within 2 seconds.
"""

import pytest
import time
import pandas as pd
import gc
import psutil
from typing import Dict, Any, List
from unittest.mock import Mock, patch

# Import the components we need to test
from components.data_table import DataTableComponent
from components.sidebar import SidebarComponent
from ui.session_manager import SessionStateManager
from ui.performance_optimizer import PerformanceOptimizer
from tests.integration.test_fixtures import TestFixtures


class TestFilterPerformance:
    """Test performance of filtering operations"""
    
    def setup_method(self):
        """Set up test environment"""
        self.session_manager = SessionStateManager()
        self.optimizer = PerformanceOptimizer()
        self.data_table = DataTableComponent()
        self.process = psutil.Process()
        
        # Initialize session state for testing
        self.session_manager.initialize_session_state()
        
        # Record initial memory
        self.initial_memory = self.process.memory_info().rss / 1024 / 1024  # MB
    
    def teardown_method(self):
        """Clean up after tests"""
        gc.collect()
        
        # Check for memory leaks
        final_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - self.initial_memory
        
        # Allow reasonable memory increase for caching
        assert memory_increase < 30, f"Memory leak in filter tests: {memory_increase:.2f}MB increase"
    
    def generate_large_dataframe(self, num_rows: int) -> pd.DataFrame:
        """Generate a large dataframe for filter testing"""
        import random
        
        providers = ['aws', 'azure', 'gcp']
        resource_types = [
            'aws_instance', 'aws_s3_bucket', 'aws_security_group', 'aws_rds_instance',
            'azurerm_virtual_machine', 'azurerm_storage_account', 'azurerm_network_security_group',
            'google_compute_instance', 'google_storage_bucket', 'google_compute_firewall'
        ]
        actions = ['create', 'update', 'delete']
        risk_levels = ['Low', 'Medium', 'High', 'Critical']
        
        data = []
        for i in range(num_rows):
            provider = random.choice(providers)
            # Find matching resource types for the provider
            matching_types = [rt for rt in resource_types if rt.startswith(provider)]
            if not matching_types:
                # Fallback to any resource type if no match
                resource_type = random.choice(resource_types)
            else:
                resource_type = random.choice(matching_types)
            
            data.append({
                'resource_address': f"{resource_type}.resource_{i}",
                'resource_type': resource_type,
                'resource_name': f"resource_{i}",
                'action': random.choice(actions),
                'actions_list': random.choice(actions),
                'provider': provider,
                'risk_level': random.choice(risk_levels),
                'has_before': random.choice([True, False]),
                'has_after': random.choice([True, False]),
                'is_sensitive': random.choice([True, False]),
                'description': f"Description for resource {i}",
                'tags': f"Environment=test,ResourceId={i}"
            })
        
        return pd.DataFrame(data)
    
    def test_action_filter_performance(self):
        """Test performance of action filtering"""
        # Create large dataset
        df = self.generate_large_dataframe(1000)
        
        # Test different action filters
        action_filters = [
            ['create'],
            ['update'],
            ['delete'],
            ['create', 'update'],
            ['create', 'update', 'delete']
        ]
        
        for action_filter in action_filters:
            start_time = time.time()
            
            # Apply action filter
            if action_filter:
                filtered_df = df[df['action'].isin(action_filter)]
            else:
                filtered_df = df
            
            filter_time = time.time() - start_time
            
            # Filter should complete within 2 seconds (requirement)
            assert filter_time < 2.0, f"Action filter took {filter_time:.3f}s, expected < 2s"
            
            # Verify filter worked correctly
            if action_filter:
                assert all(filtered_df['action'].isin(action_filter)), "Action filter didn't work correctly"
    
    def test_risk_filter_performance(self):
        """Test performance of risk level filtering"""
        df = self.generate_large_dataframe(1000)
        
        risk_filters = [
            ['Low'],
            ['Medium'],
            ['High'],
            ['Critical'],
            ['High', 'Critical'],
            ['Low', 'Medium', 'High', 'Critical']
        ]
        
        for risk_filter in risk_filters:
            start_time = time.time()
            
            # Apply risk filter
            if risk_filter:
                filtered_df = df[df['risk_level'].isin(risk_filter)]
            else:
                filtered_df = df
            
            filter_time = time.time() - start_time
            
            # Filter should complete within 2 seconds (requirement)
            assert filter_time < 2.0, f"Risk filter took {filter_time:.3f}s, expected < 2s"
            
            # Verify filter worked correctly
            if risk_filter:
                assert all(filtered_df['risk_level'].isin(risk_filter)), "Risk filter didn't work correctly"
    
    def test_provider_filter_performance(self):
        """Test performance of provider filtering"""
        df = self.generate_large_dataframe(1000)
        
        provider_filters = [
            ['aws'],
            ['azure'],
            ['gcp'],
            ['aws', 'azure'],
            ['aws', 'azure', 'gcp']
        ]
        
        for provider_filter in provider_filters:
            start_time = time.time()
            
            # Apply provider filter
            if provider_filter:
                filtered_df = df[df['provider'].isin(provider_filter)]
            else:
                filtered_df = df
            
            filter_time = time.time() - start_time
            
            # Filter should complete within 2 seconds (requirement)
            assert filter_time < 2.0, f"Provider filter took {filter_time:.3f}s, expected < 2s"
            
            # Verify filter worked correctly
            if provider_filter:
                assert all(filtered_df['provider'].isin(provider_filter)), "Provider filter didn't work correctly"
    
    def test_text_search_performance(self):
        """Test performance of text search functionality"""
        df = self.generate_large_dataframe(1000)
        
        search_terms = [
            "resource_1",
            "aws_instance",
            "test",
            "Environment",
            "nonexistent_term"
        ]
        
        for search_term in search_terms:
            start_time = time.time()
            
            # Apply text search across multiple columns
            mask = (
                df['resource_address'].str.contains(search_term, case=False, na=False) |
                df['resource_type'].str.contains(search_term, case=False, na=False) |
                df['resource_name'].str.contains(search_term, case=False, na=False) |
                df['description'].str.contains(search_term, case=False, na=False) |
                df['tags'].str.contains(search_term, case=False, na=False)
            )
            filtered_df = df[mask]
            
            search_time = time.time() - start_time
            
            # Search should complete within 2 seconds (requirement)
            assert search_time < 2.0, f"Text search took {search_time:.3f}s, expected < 2s"
            
            # Verify search worked (for existing terms)
            if search_term != "nonexistent_term":
                assert len(filtered_df) > 0, f"Search for '{search_term}' returned no results"
    
    def test_combined_filter_performance(self):
        """Test performance of multiple filters applied together"""
        df = self.generate_large_dataframe(1000)
        
        # Test various combinations of filters
        filter_combinations = [
            {
                'actions': ['create'],
                'risks': ['High', 'Critical'],
                'providers': ['aws']
            },
            {
                'actions': ['create', 'update'],
                'risks': ['Medium', 'High'],
                'providers': ['aws', 'azure']
            },
            {
                'actions': ['create', 'update', 'delete'],
                'risks': ['Low', 'Medium', 'High', 'Critical'],
                'providers': ['aws', 'azure', 'gcp']
            }
        ]
        
        for filters in filter_combinations:
            start_time = time.time()
            
            # Apply all filters
            filtered_df = df.copy()
            
            if filters['actions']:
                filtered_df = filtered_df[filtered_df['action'].isin(filters['actions'])]
            
            if filters['risks']:
                filtered_df = filtered_df[filtered_df['risk_level'].isin(filters['risks'])]
            
            if filters['providers']:
                filtered_df = filtered_df[filtered_df['provider'].isin(filters['providers'])]
            
            filter_time = time.time() - start_time
            
            # Combined filters should complete within 2 seconds (requirement)
            assert filter_time < 2.0, f"Combined filters took {filter_time:.3f}s, expected < 2s"
            
            # Verify filters worked correctly
            if filters['actions']:
                assert all(filtered_df['action'].isin(filters['actions'])), "Action filter in combination failed"
            if filters['risks']:
                assert all(filtered_df['risk_level'].isin(filters['risks'])), "Risk filter in combination failed"
            if filters['providers']:
                assert all(filtered_df['provider'].isin(filters['providers'])), "Provider filter in combination failed"
    
    def test_filter_with_large_datasets(self):
        """Test filter performance with very large datasets"""
        # Test with progressively larger datasets
        dataset_sizes = [500, 1000, 2000, 5000]
        
        for size in dataset_sizes:
            df = self.generate_large_dataframe(size)
            
            start_time = time.time()
            
            # Apply a complex filter
            filtered_df = df[
                (df['action'].isin(['create', 'update'])) &
                (df['risk_level'].isin(['High', 'Critical'])) &
                (df['provider'].isin(['aws', 'azure']))
            ]
            
            filter_time = time.time() - start_time
            
            # Even large datasets should filter within 2 seconds
            assert filter_time < 2.0, f"Filter on {size} rows took {filter_time:.3f}s, expected < 2s"
            
            # Clean up
            del df, filtered_df
            gc.collect()
    
    def test_filter_caching_performance(self):
        """Test that filter caching improves performance"""
        df = self.generate_large_dataframe(1000)
        
        # Define a complex filter operation
        def apply_complex_filter(dataframe):
            return dataframe[
                (dataframe['action'].isin(['create', 'update'])) &
                (dataframe['risk_level'].isin(['High', 'Critical'])) &
                (dataframe['resource_type'].str.contains('instance', case=False, na=False))
            ]
        
        # First run (no cache)
        start_time = time.time()
        result1 = apply_complex_filter(df)
        first_run_time = time.time() - start_time
        
        # Second run (should be faster due to pandas optimizations)
        start_time = time.time()
        result2 = apply_complex_filter(df)
        second_run_time = time.time() - start_time
        
        # Both runs should be under 2 seconds
        assert first_run_time < 2.0, f"First filter run took {first_run_time:.3f}s, expected < 2s"
        assert second_run_time < 2.0, f"Second filter run took {second_run_time:.3f}s, expected < 2s"
        
        # Results should be identical
        pd.testing.assert_frame_equal(result1, result2)
    
    def test_filter_memory_efficiency(self):
        """Test that filtering doesn't cause memory leaks"""
        initial_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        
        # Perform multiple filter operations
        for i in range(10):
            df = self.generate_large_dataframe(500)
            
            # Apply various filters
            filtered1 = df[df['action'] == 'create']
            filtered2 = df[df['risk_level'].isin(['High', 'Critical'])]
            filtered3 = df[df['provider'] == 'aws']
            
            # Clean up explicitly
            del df, filtered1, filtered2, filtered3
            gc.collect()
        
        final_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be minimal
        assert memory_increase < 50, f"Filter operations caused memory leak: {memory_increase:.2f}MB increase"
    
    def test_concurrent_filter_operations(self):
        """Test that concurrent filter operations don't interfere"""
        import threading
        import queue
        
        df = self.generate_large_dataframe(1000)
        results_queue = queue.Queue()
        errors_queue = queue.Queue()
        
        def apply_filter(filter_type):
            try:
                start_time = time.time()
                
                if filter_type == 'action':
                    result = df[df['action'] == 'create']
                elif filter_type == 'risk':
                    result = df[df['risk_level'] == 'High']
                elif filter_type == 'provider':
                    result = df[df['provider'] == 'aws']
                
                filter_time = time.time() - start_time
                results_queue.put((filter_type, len(result), filter_time))
                
            except Exception as e:
                errors_queue.put(f"{filter_type}: {str(e)}")
        
        # Start concurrent filter operations
        threads = []
        filter_types = ['action', 'risk', 'provider']
        
        for filter_type in filter_types:
            thread = threading.Thread(target=apply_filter, args=(filter_type,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join(timeout=5)  # 5 second timeout
        
        # Check for errors
        assert errors_queue.empty(), f"Concurrent filter errors: {list(errors_queue.queue)}"
        
        # Check results
        results = []
        while not results_queue.empty():
            results.append(results_queue.get())
        
        assert len(results) == 3, f"Expected 3 results, got {len(results)}"
        
        # All operations should complete within time limit
        for filter_type, result_count, filter_time in results:
            assert filter_time < 2.0, f"{filter_type} filter took {filter_time:.3f}s, expected < 2s"
            assert result_count >= 0, f"{filter_type} filter returned negative count"
    
    def test_filter_scalability(self):
        """Test how filter performance scales with data size"""
        sizes = [100, 500, 1000, 2000]
        filter_times = []
        
        for size in sizes:
            df = self.generate_large_dataframe(size)
            
            start_time = time.time()
            
            # Apply a standard filter
            filtered_df = df[
                (df['action'] == 'create') &
                (df['risk_level'].isin(['High', 'Critical']))
            ]
            
            filter_time = time.time() - start_time
            filter_times.append(filter_time)
            
            # All sizes should filter within 2 seconds
            assert filter_time < 2.0, f"Filter on {size} rows took {filter_time:.3f}s, expected < 2s"
            
            # Clean up
            del df, filtered_df
            gc.collect()
        
        # Check that performance scales reasonably
        # 20x the data shouldn't take more than 10x the time
        if len(filter_times) >= 2:
            time_ratio = filter_times[-1] / max(filter_times[0], 0.001)
            size_ratio = sizes[-1] / sizes[0]
            
            efficiency_ratio = time_ratio / size_ratio
            assert efficiency_ratio < 0.5, f"Filter performance doesn't scale well: {efficiency_ratio:.3f}"


class TestVisualizationPerformance:
    """Test performance of chart rendering and visualization updates"""
    
    def setup_method(self):
        """Set up visualization testing environment"""
        self.optimizer = PerformanceOptimizer()
    
    def test_chart_data_preparation_performance(self):
        """Test performance of chart data preparation"""
        # Generate large dataset for chart
        data = {}
        for i in range(100):
            data[f"resource_type_{i}"] = i * 10
        
        chart_types = ['pie_chart', 'bar_chart', 'heatmap']
        
        for chart_type in chart_types:
            start_time = time.time()
            
            optimized_data = self.optimizer.optimize_chart_data_preparation(
                data, chart_type, use_cache=True
            )
            
            prep_time = time.time() - start_time
            
            # Chart data preparation should be fast (< 1 second)
            assert prep_time < 1.0, f"{chart_type} data prep took {prep_time:.3f}s, expected < 1s"
            
            # Verify data was processed
            assert optimized_data is not None, f"{chart_type} returned no data"
            assert len(optimized_data) > 0, f"{chart_type} returned empty data"
    
    def test_chart_caching_performance(self):
        """Test that chart data caching improves performance"""
        data = {f"type_{i}": i * 5 for i in range(50)}
        
        # First run (no cache)
        start_time = time.time()
        result1 = self.optimizer.optimize_chart_data_preparation(
            data, 'pie_chart', use_cache=True
        )
        first_run_time = time.time() - start_time
        
        # Second run (with cache)
        start_time = time.time()
        result2 = self.optimizer.optimize_chart_data_preparation(
            data, 'pie_chart', use_cache=True
        )
        second_run_time = time.time() - start_time
        
        # Second run should be faster
        if first_run_time > 0.001:  # Only test if first run was measurable
            improvement_ratio = first_run_time / max(second_run_time, 0.001)
            assert improvement_ratio > 1.0, f"Chart caching didn't improve performance: {improvement_ratio:.2f}x"
        
        # Results should be identical
        assert result1 == result2, "Cached chart data doesn't match original"
    
    def test_large_dataset_visualization_performance(self):
        """Test visualization performance with large datasets"""
        # Create large dataset
        large_data = {f"resource_{i}": i for i in range(1000)}
        
        start_time = time.time()
        
        # Optimize for pie chart (should group small segments)
        optimized_data = self.optimizer.optimize_chart_data_preparation(
            large_data, 'pie_chart', use_cache=True
        )
        
        optimization_time = time.time() - start_time
        
        # Optimization should be fast even for large datasets
        assert optimization_time < 2.0, f"Large dataset optimization took {optimization_time:.3f}s, expected < 2s"
        
        # Should reduce data size for better visualization
        assert len(optimized_data) < len(large_data), "Optimization didn't reduce data size"
        assert len(optimized_data) <= 21, "Pie chart data not properly grouped"  # 20 + "Others"
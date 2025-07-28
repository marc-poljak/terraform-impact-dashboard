"""
Performance Optimizer

Provides performance optimizations for large dataset processing including
chunked processing, caching, and optimized rendering.
"""

import streamlit as st
import pandas as pd
import hashlib
import json
from typing import Dict, List, Any, Optional, Iterator, Tuple
from functools import lru_cache
import time
from contextlib import contextmanager


class PerformanceOptimizer:
    """Handles performance optimizations for large dataset processing"""
    
    def __init__(self, cache_size: int = 128):
        """
        Initialize the performance optimizer
        
        Args:
            cache_size: Maximum number of items to cache
        """
        self.cache_size = cache_size
        self._cache = {}
        self._cache_hits = 0
        self._cache_misses = 0
        
    def get_cache_stats(self) -> Dict[str, int]:
        """Get cache performance statistics"""
        total_requests = self._cache_hits + self._cache_misses
        hit_rate = (self._cache_hits / max(total_requests, 1)) * 100
        
        return {
            'hits': self._cache_hits,
            'misses': self._cache_misses,
            'total_requests': total_requests,
            'hit_rate': round(hit_rate, 2),
            'cache_size': len(self._cache)
        }
    
    def _generate_cache_key(self, data: Any, operation: str) -> str:
        """Generate a cache key for the given data and operation"""
        if isinstance(data, dict):
            data_str = json.dumps(data, sort_keys=True)
        elif isinstance(data, list):
            data_str = json.dumps(data, sort_keys=True)
        else:
            data_str = str(data)
        
        combined = f"{operation}:{data_str}"
        return hashlib.md5(combined.encode()).hexdigest()
    
    def get_cached_result(self, cache_key: str) -> Optional[Any]:
        """Get cached result if available"""
        if cache_key in self._cache:
            self._cache_hits += 1
            return self._cache[cache_key]
        else:
            self._cache_misses += 1
            return None
    
    def cache_result(self, cache_key: str, result: Any) -> None:
        """Cache a result with LRU eviction"""
        # Simple LRU: remove oldest if cache is full
        if len(self._cache) >= self.cache_size:
            # Remove the first (oldest) item
            oldest_key = next(iter(self._cache))
            del self._cache[oldest_key]
        
        self._cache[cache_key] = result
    
    def chunk_process_resources(self, 
                              resource_changes: List[Dict[str, Any]], 
                              chunk_size: int = 100) -> Iterator[List[Dict[str, Any]]]:
        """
        Process resources in chunks for better performance
        
        Args:
            resource_changes: List of resource changes to process
            chunk_size: Size of each chunk
            
        Yields:
            Chunks of resource changes
        """
        for i in range(0, len(resource_changes), chunk_size):
            yield resource_changes[i:i + chunk_size]
    
    def optimize_dataframe_creation(self, 
                                  resource_changes: List[Dict[str, Any]], 
                                  parser: Any,
                                  use_cache: bool = True) -> pd.DataFrame:
        """
        Create dataframe with caching and chunked processing for large datasets
        
        Args:
            resource_changes: List of resource changes
            parser: PlanParser instance
            use_cache: Whether to use caching
            
        Returns:
            Optimized pandas DataFrame
        """
        # Generate cache key
        cache_key = self._generate_cache_key(resource_changes, "dataframe_creation")
        
        # Check cache first
        if use_cache:
            cached_result = self.get_cached_result(cache_key)
            if cached_result is not None:
                return cached_result
        
        # Determine if we need chunked processing
        if len(resource_changes) > 500:
            # Use chunked processing for large datasets
            df_chunks = []
            chunk_size = 100
            
            for chunk in self.chunk_process_resources(resource_changes, chunk_size):
                chunk_df = self._create_dataframe_chunk(chunk)
                df_chunks.append(chunk_df)
            
            # Combine all chunks
            result_df = pd.concat(df_chunks, ignore_index=True) if df_chunks else pd.DataFrame()
        else:
            # Use standard processing for smaller datasets
            result_df = parser.create_detailed_dataframe(resource_changes)
        
        # Cache the result
        if use_cache:
            self.cache_result(cache_key, result_df)
        
        return result_df
    
    def _create_dataframe_chunk(self, chunk: List[Dict[str, Any]]) -> pd.DataFrame:
        """Create dataframe from a chunk of resource changes"""
        rows = []
        
        for change in chunk:
            rows.append({
                'resource_address': change['address'],
                'resource_type': change['type'],
                'resource_name': change['name'] or change['address'].split('.')[-1],
                'action': change['action'],
                'actions_list': ', '.join(change['actions']),
                'provider': change.get('provider', 'unknown'),
                'has_before': change['before'] is not None,
                'has_after': change['after'] is not None,
                'is_sensitive': self._has_sensitive_values(change['after']) if change['after'] else False
            })
        
        return pd.DataFrame(rows)
    
    def _has_sensitive_values(self, obj: Any) -> bool:
        """Check for sensitive values in an object (optimized version)"""
        if isinstance(obj, dict):
            for key, value in obj.items():
                if value == "(sensitive)" or key.lower() in ['password', 'secret', 'key', 'token']:
                    return True
                if isinstance(value, (dict, list)):
                    if self._has_sensitive_values(value):
                        return True
        elif isinstance(obj, list):
            for item in obj:
                if self._has_sensitive_values(item):
                    return True
        elif isinstance(obj, str) and obj == "(sensitive)":
            return True
        
        return False
    
    def optimize_risk_assessment(self, 
                                resource_changes: List[Dict[str, Any]], 
                                risk_assessor: Any,
                                plan_data: Dict[str, Any],
                                use_cache: bool = True) -> List[str]:
        """
        Optimize risk assessment with caching and chunked processing
        
        Args:
            resource_changes: List of resource changes
            risk_assessor: Risk assessor instance
            plan_data: Original plan data
            use_cache: Whether to use caching
            
        Returns:
            List of risk levels
        """
        # Generate cache key
        cache_key = self._generate_cache_key(
            [resource_changes, str(type(risk_assessor))], 
            "risk_assessment"
        )
        
        # Check cache first
        if use_cache:
            cached_result = self.get_cached_result(cache_key)
            if cached_result is not None:
                return cached_result
        
        risk_levels = []
        
        # Use chunked processing for large datasets
        if len(resource_changes) > 200:
            chunk_size = 50
            for chunk in self.chunk_process_resources(resource_changes, chunk_size):
                chunk_risks = self._assess_chunk_risks(chunk, risk_assessor, plan_data)
                risk_levels.extend(chunk_risks)
        else:
            # Process all at once for smaller datasets
            for change in resource_changes:
                risk_level = self._assess_single_resource_risk(change, risk_assessor, plan_data)
                risk_levels.append(risk_level)
        
        # Cache the result
        if use_cache:
            self.cache_result(cache_key, risk_levels)
        
        return risk_levels
    
    def _assess_chunk_risks(self, 
                           chunk: List[Dict[str, Any]], 
                           risk_assessor: Any, 
                           plan_data: Dict[str, Any]) -> List[str]:
        """Assess risks for a chunk of resources"""
        chunk_risks = []
        for change in chunk:
            risk_level = self._assess_single_resource_risk(change, risk_assessor, plan_data)
            chunk_risks.append(risk_level)
        return chunk_risks
    
    def _assess_single_resource_risk(self, 
                                   change: Dict[str, Any], 
                                   risk_assessor: Any, 
                                   plan_data: Dict[str, Any]) -> str:
        """Assess risk for a single resource"""
        try:
            resource_data = {
                'type': change['type'],
                'change': {'actions': [change['action']]}
            }
            
            if hasattr(risk_assessor, 'assess_resource_risk'):
                risk_result = risk_assessor.assess_resource_risk(resource_data, plan_data)
                return risk_result.get('level', 'Medium')
            else:
                # Fallback for basic risk assessor
                risk_result = risk_assessor.assess_resource_risk(resource_data)
                return risk_result.get('level', 'Medium')
        except Exception:
            return 'Medium'  # Fallback
    
    def optimize_chart_data_preparation(self, 
                                      data: Dict[str, Any], 
                                      chart_type: str,
                                      use_cache: bool = True) -> Dict[str, Any]:
        """
        Optimize chart data preparation with caching
        
        Args:
            data: Raw data for chart
            chart_type: Type of chart being created
            use_cache: Whether to use caching
            
        Returns:
            Optimized chart data
        """
        # Generate cache key
        cache_key = self._generate_cache_key(data, f"chart_data_{chart_type}")
        
        # Check cache first
        if use_cache:
            cached_result = self.get_cached_result(cache_key)
            if cached_result is not None:
                return cached_result
        
        # Optimize data based on chart type
        if chart_type == 'pie_chart':
            optimized_data = self._optimize_pie_chart_data(data)
        elif chart_type == 'bar_chart':
            optimized_data = self._optimize_bar_chart_data(data)
        elif chart_type == 'heatmap':
            optimized_data = self._optimize_heatmap_data(data)
        else:
            optimized_data = data
        
        # Cache the result
        if use_cache:
            self.cache_result(cache_key, optimized_data)
        
        return optimized_data
    
    def _optimize_pie_chart_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize data for pie charts by grouping small segments"""
        if not isinstance(data, dict):
            return data
        
        # Group small segments (< 2% of total) into "Others"
        total = sum(data.values())
        threshold = total * 0.02  # 2% threshold
        
        optimized = {}
        others_count = 0
        
        for key, value in data.items():
            if value >= threshold:
                optimized[key] = value
            else:
                others_count += value
        
        if others_count > 0:
            optimized['Others'] = others_count
        
        return optimized
    
    def _optimize_bar_chart_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize data for bar charts"""
        # For bar charts, we typically don't need to group data
        return data
    
    def _optimize_heatmap_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize data for heatmaps by limiting dimensions"""
        if not isinstance(data, dict):
            return data
        
        # Limit to top 20 items for better visualization
        if len(data) > 20:
            sorted_items = sorted(data.items(), key=lambda x: x[1], reverse=True)
            return dict(sorted_items[:20])
        
        return data
    
    @contextmanager
    def performance_monitor(self, operation_name: str):
        """
        Context manager to monitor performance of operations
        
        Args:
            operation_name: Name of the operation being monitored
        """
        start_time = time.time()
        try:
            yield
        finally:
            end_time = time.time()
            duration = end_time - start_time
            
            # Store performance metrics in session state for debugging
            if 'performance_metrics' not in st.session_state:
                st.session_state.performance_metrics = {}
            
            st.session_state.performance_metrics[operation_name] = {
                'duration': round(duration, 3),
                'timestamp': time.time()
            }
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for debugging"""
        metrics = getattr(st.session_state, 'performance_metrics', {})
        cache_stats = self.get_cache_stats()
        
        return {
            'operation_metrics': metrics,
            'cache_stats': cache_stats,
            'total_operations': len(metrics)
        }
    
    def optimize_table_rendering(self, 
                                df: pd.DataFrame, 
                                max_rows: int = 1000) -> Tuple[pd.DataFrame, bool]:
        """
        Optimize table rendering for large datasets
        
        Args:
            df: DataFrame to optimize
            max_rows: Maximum rows to display at once
            
        Returns:
            Tuple of (optimized_df, is_truncated)
        """
        if len(df) <= max_rows:
            return df, False
        
        # For large datasets, show first N rows with pagination info
        truncated_df = df.head(max_rows).copy()
        return truncated_df, True
    
    def clear_cache(self) -> None:
        """Clear all cached data"""
        self._cache.clear()
        self._cache_hits = 0
        self._cache_misses = 0
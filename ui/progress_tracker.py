"""
Progress Tracker

Provides progress indicators and loading states for dashboard operations.
"""

import streamlit as st
from typing import Optional, Any, Dict, List
import time
from contextlib import contextmanager


class ProgressTracker:
    """Manages progress indicators and loading states"""
    
    def __init__(self):
        """Initialize progress tracker"""
        self.progress_container = None
        self.progress_bar = None
        self.status_text = None
        
    @contextmanager
    def track_operation(self, message: str, show_spinner: bool = True):
        """
        Context manager for tracking long-running operations
        
        Args:
            message: Message to display during operation
            show_spinner: Whether to show a spinner
        """
        if show_spinner:
            with st.spinner(message):
                yield
        else:
            st.info(message)
            yield
            
    def show_progress_bar(self, current: int, total: int, message: str = "") -> None:
        """
        Show a progress bar for operations with known progress
        
        Args:
            current: Current progress value
            total: Total progress value
            message: Optional message to display
        """
        progress = current / max(total, 1)
        st.progress(progress)
        if message:
            st.text(f"{message} ({current}/{total})")
    
    def initialize_progress_container(self) -> None:
        """Initialize a container for detailed progress tracking"""
        if self.progress_container is None:
            self.progress_container = st.container()
            with self.progress_container:
                self.progress_bar = st.progress(0)
                self.status_text = st.empty()
    
    def update_progress(self, progress: float, message: str) -> None:
        """
        Update progress bar and status message
        
        Args:
            progress: Progress value between 0.0 and 1.0
            message: Status message to display
        """
        if self.progress_bar is not None:
            self.progress_bar.progress(progress)
        if self.status_text is not None:
            self.status_text.text(message)
    
    def clear_progress(self) -> None:
        """Clear progress indicators"""
        if self.progress_container is not None:
            self.progress_container.empty()
            self.progress_container = None
            self.progress_bar = None
            self.status_text = None
            
    def show_file_processing_progress(self, file_size: int, stage: str) -> None:
        """
        Show progress for file processing operations with detailed feedback
        
        Args:
            file_size: Size of file being processed in bytes
            stage: Current processing stage
        """
        # Initialize progress container if not already done
        self.initialize_progress_container()
        
        # Define processing stages and their relative weights
        stages = {
            'parsing': {'weight': 0.3, 'message': '📄 Parsing JSON structure...'},
            'validation': {'weight': 0.2, 'message': '✅ Validating plan format...'},
            'extraction': {'weight': 0.3, 'message': '🔍 Extracting resource changes...'},
            'risk_assessment': {'weight': 0.2, 'message': '⚠️ Analyzing risks...'}
        }
        
        if stage in stages:
            stage_info = stages[stage]
            
            # Calculate file size category for progress estimation
            if file_size < 100 * 1024:  # < 100KB
                size_category = "small"
                base_progress = 0.8  # Fast processing
            elif file_size < 1024 * 1024:  # < 1MB
                size_category = "medium"
                base_progress = 0.6  # Moderate processing
            elif file_size < 10 * 1024 * 1024:  # < 10MB
                size_category = "large"
                base_progress = 0.4  # Slower processing
            else:  # >= 10MB
                size_category = "very_large"
                base_progress = 0.2  # Much slower processing
            
            # Calculate progress based on stage and file size
            stage_progress = base_progress * stage_info['weight']
            
            # Format file size for display
            if file_size < 1024:
                size_str = f"{file_size} bytes"
            elif file_size < 1024 * 1024:
                size_str = f"{file_size / 1024:.1f} KB"
            else:
                size_str = f"{file_size / (1024 * 1024):.1f} MB"
            
            message = f"{stage_info['message']} ({size_str}, {size_category} file)"
            self.update_progress(stage_progress, message)
        
    def show_chart_loading(self, chart_type: str, data_size: int = 0) -> None:
        """
        Show loading indicator for chart rendering with detailed feedback
        
        Args:
            chart_type: Type of chart being rendered
            data_size: Number of data points being processed
        """
        # Chart type specific messages and estimated complexity
        chart_configs = {
            'pie_chart': {'icon': '🥧', 'name': 'Pie Chart', 'complexity': 0.3},
            'bar_chart': {'icon': '📊', 'name': 'Bar Chart', 'complexity': 0.4},
            'heatmap': {'icon': '🔥', 'name': 'Risk Heatmap', 'complexity': 0.7},
            'multi_cloud_distribution': {'icon': '☁️', 'name': 'Multi-Cloud Distribution', 'complexity': 0.6},
            'dependency_graph': {'icon': '🔗', 'name': 'Dependency Graph', 'complexity': 0.9}
        }
        
        config = chart_configs.get(chart_type, {'icon': '📈', 'name': 'Chart', 'complexity': 0.5})
        
        # Estimate processing time based on data size and complexity
        if data_size > 1000:
            complexity_modifier = 1.5
            size_note = f" ({data_size} data points)"
        elif data_size > 100:
            complexity_modifier = 1.2
            size_note = f" ({data_size} data points)"
        else:
            complexity_modifier = 1.0
            size_note = ""
        
        message = f"{config['icon']} Rendering {config['name']}{size_note}..."
        
        # Show spinner for chart rendering
        with st.spinner(message):
            # Simulate processing time based on complexity
            estimated_time = config['complexity'] * complexity_modifier * 0.5
            time.sleep(min(estimated_time, 2.0))  # Cap at 2 seconds for UX
    
    @contextmanager
    def track_file_processing(self, file_size: int):
        """
        Context manager for tracking complete file processing workflow
        
        Args:
            file_size: Size of file being processed in bytes
        """
        self.initialize_progress_container()
        
        # Create a stage tracker object that can be used to update progress
        class StageTracker:
            def __init__(self, progress_tracker, file_size):
                self.progress_tracker = progress_tracker
                self.file_size = file_size
                self.current_stage = 0
                self.stages = ['parsing', 'validation', 'extraction', 'risk_assessment']
            
            def next_stage(self):
                """Move to the next processing stage"""
                if self.current_stage < len(self.stages):
                    stage_name = self.stages[self.current_stage]
                    self.progress_tracker.show_file_processing_progress(self.file_size, stage_name)
                    self.current_stage += 1
                    return stage_name
                return None
            
            def complete(self):
                """Mark processing as complete"""
                self.progress_tracker.update_progress(1.0, "✅ Processing complete!")
                time.sleep(0.5)  # Brief pause to show completion
        
        stage_tracker = StageTracker(self, file_size)
        
        try:
            yield stage_tracker
        finally:
            self.clear_progress()
    
    @contextmanager
    def track_chart_rendering(self, charts: List[Dict[str, Any]]):
        """
        Context manager for tracking multiple chart rendering operations
        
        Args:
            charts: List of chart configurations with 'type' and optional 'data_size'
        """
        total_charts = len(charts)
        
        try:
            for i, chart_config in enumerate(charts):
                chart_type = chart_config.get('type', 'unknown')
                data_size = chart_config.get('data_size', 0)
                
                progress = (i + 1) / total_charts
                message = f"Rendering chart {i + 1} of {total_charts}..."
                
                if self.progress_bar is not None:
                    self.update_progress(progress, message)
                
                # Show detailed chart loading
                self.show_chart_loading(chart_type, data_size)
                
                yield chart_config
                
        finally:
            if self.progress_container is not None:
                self.clear_progress()
    
    def show_data_processing_progress(self, operation: str, current: int, total: int) -> None:
        """
        Show progress for data processing operations like filtering or sorting
        
        Args:
            operation: Description of the operation being performed
            current: Current item being processed
            total: Total items to process
        """
        if total > 0:
            progress = current / total
            message = f"{operation}: {current}/{total} items processed"
            
            if self.progress_bar is not None:
                self.update_progress(progress, message)
            else:
                # Fallback to simple progress bar
                st.progress(progress)
                st.text(message)
"""
Plan Processor Utility Module

This module contains the PlanProcessor class that handles the centralized plan data processing workflow.
Extracted from app.py to improve code organization and maintainability.
"""

import streamlit as st
from parsers.plan_parser import PlanParser
from visualizers.charts import ChartGenerator
from ui.progress_tracker import ProgressTracker
from ui.performance_optimizer import PerformanceOptimizer

# Try to import enhanced features, fall back to basic if not available
try:
    from utils.enhanced_risk_assessment import EnhancedRiskAssessment
    ENHANCED_FEATURES_AVAILABLE = True
except ImportError:
    from utils.risk_assessment import RiskAssessment
    ENHANCED_FEATURES_AVAILABLE = False


class PlanProcessor:
    """
    Centralized plan data processing workflow with enhanced progress tracking and performance optimization.
    Maintains compatibility with existing parsers, risk assessors, and chart generators.
    """
    
    def __init__(self):
        """Initialize the PlanProcessor with required components."""
        self.progress_tracker = ProgressTracker()
        self.performance_optimizer = PerformanceOptimizer()
    
    def process_plan_data(self, plan_input, upload_component, error_handler, show_debug, enable_multi_cloud):
        """
        Centralized plan data processing workflow with enhanced progress tracking and performance optimization.
        Handles both uploaded files and TFE-retrieved plan data.
        
        Args:
            plan_input: Either an uploaded file from Streamlit or plan data dict from TFE
            upload_component: UploadComponent instance
            error_handler: ErrorHandler instance
            show_debug: Whether debug mode is enabled
            enable_multi_cloud: Whether multi-cloud features are enabled
            
        Returns:
            Dict containing processed data or None if processing failed
        """
        # Determine if we have a file or plan data already
        import json
        
        # Use progress tracking context manager for file processing
        file_size = 1024  # Default size
        
        with self.progress_tracker.track_file_processing(file_size) as stage_tracker:
            try:
                # Stage 1: Data extraction/validation
                stage_tracker.next_stage()  # Show parsing progress
                with self.performance_optimizer.performance_monitor("plan_data_validation"):
                    # Check if we have plan data directly or need to extract from file
                    if isinstance(plan_input, dict):
                        # Plan data is already provided (e.g., from TFE)
                        plan_data = plan_input
                        file_size = len(json.dumps(plan_data))
                    else:
                        # We have a file object, need to validate and parse it
                        plan_data, error_msg = upload_component.validate_and_parse_file(plan_input)
                        if plan_data is None:
                            if error_msg:
                                error_handler.handle_processing_error(
                                    ValueError(error_msg), 
                                    "plan data validation"
                                )
                            return None
                        file_size = len(json.dumps(plan_data))
                    
                    # Plan data is now validated and secured
                    st.success("✅ **Plan data processed successfully!**")
                
                # Stage 2: Validation - Parse the uploaded file using existing PlanParser
                stage_tracker.next_stage()  # Show validation progress
                with self.performance_optimizer.performance_monitor("plan_parser_init"):
                    parser = PlanParser(plan_data)
                
                # Stage 3: Extraction - Extract metrics using existing data structures
                stage_tracker.next_stage()  # Show extraction progress
                with self.performance_optimizer.performance_monitor("data_extraction"):
                    summary = parser.get_summary()
                    resource_changes = parser.get_resource_changes()
                    resource_types = parser.get_resource_types()
                    debug_info = parser.get_debug_info()
                
                # Stage 4: Risk Assessment - Risk assessment with error handling and fallback
                stage_tracker.next_stage()  # Show risk assessment progress
                with self.performance_optimizer.performance_monitor("risk_assessment"):
                    enhanced_risk_assessor = None
                    if ENHANCED_FEATURES_AVAILABLE and enable_multi_cloud:
                        try:
                            enhanced_risk_assessor = EnhancedRiskAssessment()
                            enhanced_risk_result = enhanced_risk_assessor.assess_plan_risk(resource_changes, plan_data)
                            risk_summary = enhanced_risk_result  # For compatibility
                        except Exception as e:
                            error_handler.handle_processing_error(e, "enhanced risk assessment")
                            from utils.risk_assessment import RiskAssessment
                            risk_assessor = RiskAssessment()
                            risk_summary = risk_assessor.assess_plan_risk(resource_changes)
                            enhanced_risk_result = risk_summary
                            enhanced_risk_assessor = None
                    else:
                        # Use basic risk assessment
                        from utils.risk_assessment import RiskAssessment
                        risk_assessor = RiskAssessment()
                        risk_summary = risk_assessor.assess_plan_risk(resource_changes)
                        enhanced_risk_result = risk_summary

                    # Chart generator using existing ChartGenerator
                    chart_gen = ChartGenerator()
                
                # Mark processing as complete
                stage_tracker.complete()
            
            except Exception as e:
                error_handler.handle_processing_error(e, "plan processing")
                return None
        
        # Show performance metrics for large files in debug mode
        if show_debug and file_size > 1024 * 1024:  # > 1MB
            with st.expander("⚡ Performance Metrics", expanded=False):
                metrics = self.performance_optimizer.get_performance_metrics()
                
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("**Processing Times:**")
                    for operation, data in metrics['operation_metrics'].items():
                        st.write(f"• {operation}: {data['duration']}s")
                
                with col2:
                    st.markdown("**Cache Performance:**")
                    cache_stats = metrics['cache_stats']
                    st.write(f"• Hit Rate: {cache_stats['hit_rate']:.1f}%")
                    st.write(f"• Cache Size: {cache_stats['cache_size']} items")
        
        return {
            'plan_data': plan_data,
            'parser': parser,
            'summary': summary,
            'resource_changes': resource_changes,
            'resource_types': resource_types,
            'debug_info': debug_info,
            'enhanced_risk_assessor': enhanced_risk_assessor,
            'enhanced_risk_result': enhanced_risk_result,
            'risk_summary': risk_summary,
            'chart_gen': chart_gen,
            'performance_optimizer': self.performance_optimizer  # Include for components to use
        }
"""
Visualizations Component

Handles the rendering of charts and visualizations for the Terraform Plan Impact Dashboard.
Extracted from the main app.py file to improve code organization.
"""

from typing import Dict, Any, Optional, List
import streamlit as st
from .base_component import BaseComponent
from ui.progress_tracker import ProgressTracker
from ui.performance_optimizer import PerformanceOptimizer


class VisualizationsComponent(BaseComponent):
    """Component for rendering plan visualizations and charts"""
    
    def __init__(self, session_manager: Optional[Any] = None):
        """
        Initialize the VisualizationsComponent
        
        Args:
            session_manager: Optional session state manager
        """
        super().__init__(session_manager)
        self.performance_optimizer = PerformanceOptimizer()
        
    def render(self, 
               summary: Dict[str, int], 
               resource_types: Dict[str, int], 
               resource_changes: list,
               plan_data: Dict[str, Any],
               chart_gen: Any,
               parser: Any = None,
               enhanced_risk_assessor: Any = None,
               enhanced_features_available: bool = False,
               enable_multi_cloud: bool = False,
               show_debug: bool = False) -> None:
        """
        Render the main visualizations section with progress tracking
        
        Args:
            summary: Change summary with create/update/delete counts
            resource_types: Dictionary of resource types and their counts
            resource_changes: List of resource changes
            plan_data: Full plan data dictionary
            chart_gen: ChartGenerator instance
            parser: PlanParser instance (optional, for enhanced features)
            enhanced_risk_assessor: Enhanced risk assessor instance (optional)
            enhanced_features_available: Whether enhanced features are available
            enable_multi_cloud: Whether multi-cloud features are enabled
            show_debug: Whether to show debug information
        """
        # Only show visualizations if we have data
        if summary['total'] > 0:
            # Visualizations Section
            st.markdown("---")
            st.markdown("## 📈 Visualizations")
            st.caption("Interactive charts showing resource distributions and change patterns in your Terraform plan")

            # Initialize progress tracker for chart rendering
            progress_tracker = ProgressTracker()
            
            # Prepare chart configurations for progress tracking
            charts_to_render = []
            
            # Basic charts
            if resource_types:
                charts_to_render.append({
                    'type': 'pie_chart',
                    'data_size': len(resource_types),
                    'name': 'Resource Types Distribution'
                })
            
            charts_to_render.append({
                'type': 'bar_chart', 
                'data_size': len(summary),
                'name': 'Change Actions'
            })
            
            # Multi-cloud chart if applicable
            if enhanced_features_available and enable_multi_cloud:
                if hasattr(parser, 'get_actions_by_provider'):
                    try:
                        actions_by_provider = parser.get_actions_by_provider()
                        if actions_by_provider and len(actions_by_provider) > 1:
                            charts_to_render.append({
                                'type': 'multi_cloud_distribution',
                                'data_size': len(actions_by_provider),
                                'name': 'Multi-Cloud Action Distribution'
                            })
                    except Exception:
                        pass  # Skip if not available
            
            # Risk assessment chart
            charts_to_render.append({
                'type': 'heatmap',
                'data_size': len(resource_changes),
                'name': 'Risk Assessment by Resource Type'
            })

            # Render basic charts with progress tracking
            col1, col2 = st.columns(2)
            
            # Track and render pie chart
            for chart_config in charts_to_render:
                if chart_config.get('type') == 'pie_chart':
                    progress_tracker.show_chart_loading('pie_chart', chart_config.get('data_size', 0))
                    with col1:
                        self._render_pie_chart(resource_types, chart_gen)
                    break
            
            # Track and render bar chart
            for chart_config in charts_to_render:
                if chart_config.get('type') == 'bar_chart':
                    progress_tracker.show_chart_loading('bar_chart', chart_config.get('data_size', 0))
                    with col2:
                        self._render_bar_chart(summary, chart_gen)
                    break

            # Enhanced Multi-Cloud Visualizations (only if enabled)
            if enhanced_features_available and enable_multi_cloud:
                for chart_config in charts_to_render:
                    if chart_config.get('type') == 'multi_cloud_distribution':
                        progress_tracker.show_chart_loading('multi_cloud_distribution', chart_config.get('data_size', 0))
                        self._render_multi_cloud_visualizations(parser, chart_gen, show_debug)
                        break

            # Risk Assessment Chart
            for chart_config in charts_to_render:
                if chart_config.get('type') == 'heatmap':
                    progress_tracker.show_chart_loading('heatmap', chart_config.get('data_size', 0))
                    self._render_risk_assessment_visualization(
                        resource_changes, plan_data, chart_gen, enhanced_risk_assessor,
                        enhanced_features_available, enable_multi_cloud
                    )
                    break
        else:
            st.info("🎉 No changes detected in this plan! All resources are up to date.")
    
    def _render_pie_chart(self, resource_types: Dict[str, int], chart_gen: Any) -> None:
        """Render resource types pie chart with performance optimization"""
        st.markdown("### 🏷️ Resource Types Distribution")
        st.caption("Shows the distribution of different resource types (e.g., aws_instance, aws_s3_bucket) in your plan")
        if resource_types:
            try:
                # Optimize chart data for better performance and visualization
                with self.performance_optimizer.performance_monitor("pie_chart_data_prep"):
                    optimized_data = self.performance_optimizer.optimize_chart_data_preparation(
                        resource_types, 'pie_chart', use_cache=True
                    )
                
                fig_pie = chart_gen.create_resource_type_pie(optimized_data)
                st.plotly_chart(fig_pie, use_container_width=True)
                
                # Show optimization info for large datasets
                if len(resource_types) > len(optimized_data):
                    st.caption(f"💡 Showing top {len(optimized_data)} resource types (grouped {len(resource_types) - len(optimized_data)} smaller types into 'Others')")
                else:
                    st.caption("💡 Hover over chart segments to see exact counts and percentages")
            except Exception as e:
                self._render_error("Failed to create resource type pie chart", str(e))
        else:
            st.info("No resource type data available")
    
    def _render_bar_chart(self, summary: Dict[str, int], chart_gen: Any) -> None:
        """Render change actions bar chart"""
        st.markdown("### 🔄 Change Actions")
        st.caption("Breakdown of Terraform actions: create (new), update (modify), delete (remove)")
        try:
            fig_bar = chart_gen.create_change_actions_bar(summary)
            st.plotly_chart(fig_bar, use_container_width=True)
            st.caption("💡 Click on legend items to show/hide specific action types")
        except Exception as e:
            self._render_error("Failed to create change actions bar chart", str(e))
            
    def _render_multi_cloud_visualizations(self, 
                                         parser: Any, 
                                         chart_gen: Any, 
                                         show_debug: bool) -> None:
        """
        Render enhanced multi-cloud visualizations
        
        Args:
            parser: PlanParser instance
            chart_gen: ChartGenerator instance
            show_debug: Whether to show debug information
        """
        try:
            # Check if parser has enhanced methods
            if hasattr(parser, 'get_actions_by_provider'):
                actions_by_provider = parser.get_actions_by_provider()
                if actions_by_provider and len(actions_by_provider) > 1:
                    st.markdown("### 🌐 Multi-Cloud Action Distribution")
                    st.caption("Shows how Terraform actions are distributed across different cloud providers in your multi-cloud deployment")
                    if hasattr(chart_gen, 'create_provider_actions_stacked_bar'):
                        try:
                            fig_provider_actions = chart_gen.create_provider_actions_stacked_bar(
                                actions_by_provider)
                            st.plotly_chart(fig_provider_actions, use_container_width=True)
                            st.caption("💡 This chart helps identify which providers have the most changes and potential coordination needs")
                        except Exception as e:
                            self._render_error("Failed to create provider actions chart", str(e))
        except Exception as e:
            if show_debug:
                st.warning(f"Could not create provider action chart: {e}")
                
    def _render_risk_assessment_visualization(self,
                                            resource_changes: list,
                                            plan_data: Dict[str, Any],
                                            chart_gen: Any,
                                            enhanced_risk_assessor: Any,
                                            enhanced_features_available: bool,
                                            enable_multi_cloud: bool) -> None:
        """
        Render risk assessment heatmap visualization
        
        Args:
            resource_changes: List of resource changes
            plan_data: Full plan data dictionary
            chart_gen: ChartGenerator instance
            enhanced_risk_assessor: Enhanced risk assessor instance (optional)
            enhanced_features_available: Whether enhanced features are available
            enable_multi_cloud: Whether multi-cloud features are enabled
        """
        st.markdown("### ⚠️ Risk Assessment by Resource Type")
        st.caption("Heatmap showing risk levels for different resource types. Darker colors indicate higher risk.")
        if resource_changes:
            try:
                if enhanced_features_available and enable_multi_cloud and enhanced_risk_assessor:
                    risk_by_type = enhanced_risk_assessor.get_risk_by_resource_type(resource_changes, plan_data)
                else:
                    from utils.risk_assessment import RiskAssessment
                    basic_risk_assessor = RiskAssessment()
                    risk_by_type = basic_risk_assessor.get_risk_by_resource_type(resource_changes)

                if risk_by_type:
                    fig_risk = chart_gen.create_risk_heatmap(risk_by_type)
                    st.plotly_chart(fig_risk, use_container_width=True)
                    st.caption("💡 Use this chart to identify which resource types require the most attention during deployment")
                else:
                    st.info("No risk data available")
            except Exception as e:
                self._render_error("Failed to create risk assessment chart", str(e))
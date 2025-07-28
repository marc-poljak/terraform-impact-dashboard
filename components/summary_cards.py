"""
Summary Cards Component

Handles the display of change summary metrics and detailed plan information.
Extracted from the main app.py file to improve code organization.
"""

from typing import Dict, Any, Optional
import streamlit as st
from .base_component import BaseComponent


class SummaryCardsComponent(BaseComponent):
    """Component for displaying summary cards and detailed metrics"""
    
    def __init__(self, session_manager: Optional[Any] = None):
        """
        Initialize the SummaryCardsComponent
        
        Args:
            session_manager: Optional session state manager
        """
        super().__init__(session_manager)
    
    def render_change_summary(self, summary: Dict[str, int], risk_summary: Dict[str, Any]) -> None:
        """
        Render the change summary section with create/update/delete metrics
        
        Args:
            summary: Dictionary containing create, update, delete counts
            risk_summary: Risk assessment results (enhanced or basic format)
        """
        st.markdown("## 📊 Change Summary")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label="🟢 Create",
                value=summary['create'],
                delta=f"{summary['create']} resources",
                help="Number of new resources that will be created. These are resources that don't currently exist in your infrastructure."
            )
        
        with col2:
            st.metric(
                label="🔵 Update", 
                value=summary['update'],
                delta=f"{summary['update']} resources",
                help="Number of existing resources that will be modified. These changes update configuration of resources already in your infrastructure."
            )
        
        with col3:
            st.metric(
                label="🔴 Delete",
                value=summary['delete'],
                delta=f"{summary['delete']} resources",
                help="Number of resources that will be destroyed. These resources will be permanently removed from your infrastructure."
            )
        
        with col4:
            # Handle both enhanced and basic risk assessment formats
            if isinstance(risk_summary, dict) and 'overall_risk' in risk_summary:
                risk_level = risk_summary['overall_risk'].get('level', 'Unknown')
                risk_score = risk_summary['overall_risk'].get('score', 0)
            else:
                risk_level = risk_summary.get('level', 'Unknown')
                risk_score = risk_summary.get('score', 0)
            
            risk_color = "🟢" if risk_level == "Low" else "🟡" if risk_level == "Medium" else "🔴"
            
            # Create risk level help text
            risk_help = {
                "Low": "Low risk deployment. Changes are safe with minimal impact on your infrastructure.",
                "Medium": "Medium risk deployment. Changes require attention and careful review before applying.",
                "High": "High risk deployment. Changes are potentially dangerous and require thorough review.",
                "Critical": "Critical risk deployment. Changes could cause significant disruption or data loss."
            }.get(risk_level, "Risk assessment helps you understand the potential impact of your Terraform changes.")
            
            st.metric(
                label=f"{risk_color} Risk Level",
                value=risk_level,
                delta=f"Score: {risk_score}",
                help=f"{risk_help} Risk score ranges from 0-100, with higher scores indicating greater potential impact."
            )
    
    def render_detailed_metrics(self, summary: Dict[str, int], risk_summary: Dict[str, Any], 
                              resource_types: Dict[str, int], plan_data: Dict[str, Any], 
                              debug_info: Dict[str, Any]) -> None:
        """
        Render the detailed metrics section with three columns
        
        Args:
            summary: Dictionary containing create, update, delete counts
            risk_summary: Risk assessment results (enhanced or basic format)
            resource_types: Dictionary of resource types and their counts
            plan_data: Original plan data
            debug_info: Debug information from parser
        """
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("### 📈 Plan Details")
            with st.container():
                st.write(f"**Total Changes:** {summary['total']}")
                st.caption("Number of resources that will be modified by this plan")
                
                st.write(f"**Total Resources in Plan:** {debug_info.get('total_resource_changes', 'Unknown')}")
                st.caption("Total resources found in the Terraform plan JSON")
                
                st.write(f"**Terraform Version:** {plan_data.get('terraform_version', 'Unknown')}")
                st.caption("Version of Terraform used to generate this plan")
                
                st.write(f"**Plan Format:** {plan_data.get('format_version', 'Unknown')}")
                st.caption("JSON format version of the plan output")
        
        with col2:
            st.markdown("### ⚠️ Risk Analysis")
            
            # Handle both enhanced and basic risk assessment formats
            if isinstance(risk_summary, dict) and 'overall_risk' in risk_summary:
                risk_level = risk_summary['overall_risk'].get('level', 'Unknown')
                risk_score = risk_summary['overall_risk'].get('score', 0)
                high_risk_count = risk_summary['overall_risk'].get('high_risk_count', 0)
                estimated_time = risk_summary['overall_risk'].get('estimated_time', 'Unknown')
            else:
                risk_level = risk_summary.get('level', 'Unknown')
                risk_score = risk_summary.get('score', 0)
                high_risk_count = risk_summary.get('high_risk_count', 0)
                estimated_time = risk_summary.get('estimated_time', 'Unknown')
            
            with st.container():
                st.write(f"**Risk Level:** {risk_level}")
                st.caption("Overall risk assessment for this deployment")
                
                st.write(f"**Risk Score:** {risk_score}/100")
                st.caption("Numerical risk score (0=safe, 100=critical)")
                
                st.write(f"**High Risk Resources:** {high_risk_count}")
                st.caption("Number of resources flagged as high risk")
                
                st.write(f"**Estimated Time:** {estimated_time}")
                st.caption("Estimated deployment time based on resource complexity")
        
        with col3:
            st.markdown("### 📋 Resource Types")
            with st.container():
                st.write(f"**Unique Types:** {len(resource_types)}")
                st.caption("Number of different resource types in this plan")
                
                if resource_types:
                    st.write("**Top Resource Types:**")
                    top_types = dict(sorted(resource_types.items(), key=lambda x: x[1], reverse=True)[:3])
                    for rtype, count in top_types.items():
                        st.write(f"**{rtype}:** {count}")
                    st.caption("Most common resource types in your plan")
                else:
                    st.write("No resource types found")
                    st.caption("No resources detected in the plan")
    
    def render(self, summary: Dict[str, int], risk_summary: Dict[str, Any], 
               resource_types: Dict[str, int], plan_data: Dict[str, Any], 
               debug_info: Dict[str, Any], show_detailed: bool = True) -> None:
        """
        Render the complete summary cards component
        
        Args:
            summary: Dictionary containing create, update, delete counts
            risk_summary: Risk assessment results (enhanced or basic format)
            resource_types: Dictionary of resource types and their counts
            plan_data: Original plan data
            debug_info: Debug information from parser
            show_detailed: Whether to show detailed metrics section
        """
        try:
            # Render change summary cards
            self.render_change_summary(summary, risk_summary)
            
            # Render detailed metrics if requested
            if show_detailed:
                self.render_detailed_metrics(summary, risk_summary, resource_types, plan_data, debug_info)
                
        except Exception as e:
            self._render_error(f"Error rendering summary cards: {str(e)}")
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
                help="""
                **Create Actions:**
                • New resources that will be added to your infrastructure
                • These resources don't currently exist
                • Generally safe operations with low risk
                • May incur additional costs
                
                **What to review:**
                • Resource configurations are correct
                • Naming conventions are followed
                • Required dependencies exist
                • Cost implications are acceptable
                """
            )
        
        with col2:
            st.metric(
                label="🔵 Update", 
                value=summary['update'],
                delta=f"{summary['update']} resources",
                help="""
                **Update Actions:**
                • Existing resources that will be modified
                • Configuration changes to current infrastructure
                • Risk varies based on what's being changed
                • May cause temporary service disruption
                
                **What to review:**
                • Changes are intentional and necessary
                • No breaking configuration changes
                • Backup/rollback plans if needed
                • Impact on dependent resources
                """
            )
        
        with col3:
            st.metric(
                label="🔴 Delete",
                value=summary['delete'],
                delta=f"{summary['delete']} resources",
                help="""
                **Delete Actions:**
                • Resources that will be permanently removed
                • Highest risk operations - data may be lost
                • Cannot be easily undone
                • May affect dependent resources
                
                **Critical review points:**
                • Confirm deletions are intentional
                • Backup important data first
                • Check for resource dependencies
                • Consider impact on other systems
                """
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
            
            # Enhanced risk level help text
            risk_help_detailed = {
                "Low": """
                **Low Risk Deployment** (Score: 0-30)
                • Changes are generally safe
                • Minimal impact on existing infrastructure
                • Low probability of service disruption
                • Recommended: Standard deployment process
                """,
                "Medium": """
                **Medium Risk Deployment** (Score: 31-70)
                • Changes require careful review
                • Moderate impact on infrastructure
                • Some risk of service disruption
                • Recommended: Staged deployment with monitoring
                """,
                "High": """
                **High Risk Deployment** (Score: 71-90)
                • Changes are potentially dangerous
                • Significant impact on infrastructure
                • High probability of service disruption
                • Recommended: Extensive testing and backup plans
                """,
                "Critical": """
                **Critical Risk Deployment** (Score: 91-100)
                • Changes could cause major disruption
                • Potential for data loss or system outages
                • Requires immediate attention and review
                • Recommended: Manual review and approval process
                """
            }.get(risk_level, "Risk assessment helps you understand the potential impact of your Terraform changes.")
            
            st.metric(
                label=f"{risk_color} Risk Level",
                value=risk_level,
                delta=f"Score: {risk_score}/100",
                help=f"""
                {risk_help_detailed}
                
                **Risk factors considered:**
                • Resource types and their criticality
                • Action types (create/update/delete)
                • Dependencies between resources
                • Security and compliance implications
                
                **How to reduce risk:**
                • Review high-risk resources carefully
                • Use targeted deployments for critical changes
                • Implement proper backup and rollback procedures
                • Test changes in non-production environments first
                """
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
    
    def render_recommendations_section(self, summary: Dict[str, int], risk_summary: Dict[str, Any], 
                                     enhanced_risk_result: Dict[str, Any], enhanced_risk_assessor: Any,
                                     resource_changes: list, plan_data: Dict[str, Any], 
                                     enhanced_features_available: bool, enable_multi_cloud: bool) -> None:
        """
        Render the recommendations and summary section
        
        Args:
            summary: Dictionary containing create, update, delete counts
            risk_summary: Risk assessment results (enhanced or basic format)
            enhanced_risk_result: Enhanced risk assessment results
            enhanced_risk_assessor: Enhanced risk assessor instance
            resource_changes: List of resource changes
            plan_data: Original plan data
            enhanced_features_available: Whether enhanced features are available
            enable_multi_cloud: Whether multi-cloud features are enabled
        """
        st.markdown("---")
        st.markdown("### 📚 Summary & Recommendations")

        if summary['total'] > 0:
            # Extract risk level and score for display
            if isinstance(risk_summary, dict) and 'overall_risk' in risk_summary:
                risk_level = risk_summary['overall_risk'].get('level', 'Unknown')
                risk_score = risk_summary['overall_risk'].get('score', 0)
                estimated_time = risk_summary['overall_risk'].get('estimated_time', 'Unknown')
            else:
                risk_level = risk_summary.get('level', 'Unknown')
                risk_score = risk_summary.get('score', 0)
                estimated_time = risk_summary.get('estimated_time', 'Unknown')

            # Generate recommendations
            try:
                if enhanced_features_available and enable_multi_cloud and enhanced_risk_assessor:
                    recommendations = enhanced_risk_assessor.generate_recommendations(resource_changes, plan_data)
                    if isinstance(enhanced_risk_result, dict) and enhanced_risk_result.get('provider_risk_summary'):
                        provider_count = len(enhanced_risk_result['provider_risk_summary'])
                        is_multi_cloud = enhanced_risk_result.get('is_multi_cloud', False)
                    else:
                        provider_count = 1
                        is_multi_cloud = False
                else:
                    from utils.risk_assessment import RiskAssessment
                    basic_assessor = RiskAssessment()
                    recommendations = basic_assessor.generate_recommendations(resource_changes)
                    provider_count = 1
                    is_multi_cloud = False
            except Exception as e:
                recommendations = [f"Error generating recommendations: {e}"]
                provider_count = 1
                is_multi_cloud = False

            st.info(f"""
            **Plan Summary:**
            - Total changes: {summary['total']} resources
            - Risk level: {risk_level} ({risk_score}/100)
            - Estimated deployment time: {estimated_time}
            - Cloud providers: {provider_count}
            - Multi-cloud: {'Yes' if is_multi_cloud else 'No'}
            """)

            if recommendations:
                st.markdown("**🎯 Recommendations:**")
                for rec in recommendations:
                    st.write(f"- {rec}")
        else:
            st.success("✅ No changes required - your infrastructure is up to date!")

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
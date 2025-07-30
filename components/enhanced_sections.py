"""
Enhanced sections component for multi-cloud dashboard features.

This module contains the EnhancedSectionsComponent class that handles
the rendering of enhanced multi-cloud sections extracted from the main app.py.
"""

import streamlit as st
import pandas as pd

# Try to import enhanced features, fall back to basic if not available
try:
    from utils.enhanced_risk_assessment import EnhancedRiskAssessment
    from providers.cloud_detector import CloudProviderDetector
    from visualizers.charts import ChartGenerator
    ENHANCED_FEATURES_AVAILABLE = True
except ImportError as e:
    print(f"Enhanced features not available: {e}")
    from utils.risk_assessment import RiskAssessment
    ENHANCED_FEATURES_AVAILABLE = False


class EnhancedSectionsComponent:
    """Component for rendering enhanced multi-cloud dashboard sections."""
    
    def __init__(self):
        """Initialize the enhanced sections component."""
        self.enhanced_features_available = ENHANCED_FEATURES_AVAILABLE
    
    def render_enhanced_dashboard_section(self, plan_data, parser, enhanced_risk_assessor):
        """
        Create enhanced dashboard section with multi-cloud support.
        
        Args:
            plan_data: The parsed Terraform plan data
            parser: PlanParser instance
            enhanced_risk_assessor: EnhancedRiskAssessment instance
        """
        if not self.enhanced_features_available:
            st.markdown('<div class="feature-unavailable">🔧 Enhanced multi-cloud features require additional files</div>',
                        unsafe_allow_html=True)
            return

        try:
            # Multi-cloud detection and analysis
            detector = CloudProviderDetector()
            detection_results = detector.detect_providers_from_plan(plan_data)

            st.markdown("---")
            st.markdown("## 🌐 Multi-Cloud Analysis")
            st.caption("Advanced analysis for multi-cloud Terraform deployments. Detects cloud providers and analyzes cross-provider dependencies.")

            # Provider Detection Section
            col1, col2 = st.columns([2, 1])

            with col1:
                st.markdown("### 🔍 Provider Detection")
                st.caption("Automatically detects cloud providers based on resource types in your Terraform plan")

                # Display provider summary
                summary = detector.get_provider_summary(detection_results)
                if detection_results['multi_cloud']:
                    st.markdown(f'<div class="multi-cloud-alert">🌐 {summary}</div>', unsafe_allow_html=True)
                else:
                    st.info(f"☁️ {summary}")

                # Provider confidence breakdown
                if detection_results['provider_confidence']:
                    st.markdown("**Provider Confidence Scores:**")
                    for provider, confidence in detection_results['provider_confidence'].items():
                        confidence_pct = f"{confidence['score']:.1%}"
                        resource_count = confidence['resource_count']

                        # Create a progress bar for confidence
                        col_provider, col_conf, col_resources = st.columns([1, 1, 1])
                        with col_provider:
                            st.write(f"**{provider.upper()}**")
                        with col_conf:
                            st.write(confidence_pct)
                        with col_resources:
                            st.write(f"{resource_count} resources")

                        # Progress bar
                        st.progress(confidence['score'])

            with col2:
                st.markdown("### 📊 Provider Distribution")

                # Create a simple pie chart for provider distribution
                if detection_results['resource_distribution']:
                    chart_gen = ChartGenerator()
                    fig = chart_gen.create_provider_distribution_pie(detection_results['resource_distribution'])
                    st.plotly_chart(fig, use_container_width=True)

        except Exception as e:
            st.error(f"Error in enhanced dashboard: {e}")

    def render_multi_cloud_risk_section(self, enhanced_risk_result, resource_changes):
        """
        Create multi-cloud specific risk analysis section.
        
        Args:
            enhanced_risk_result: Risk assessment results from enhanced or basic assessor
            resource_changes: List of resource changes from the plan
        """
        if not self.enhanced_features_available:
            return

        try:
            st.markdown("---")
            st.markdown("## ⚠️ Enhanced Multi-Cloud Risk Analysis")
            st.caption("Comprehensive risk analysis across multiple cloud providers with provider-specific risk scoring and recommendations.")

            # Handle both enhanced and basic risk assessment formats
            if isinstance(enhanced_risk_result, dict) and 'overall_risk' in enhanced_risk_result:
                overall_risk = enhanced_risk_result['overall_risk']
                provider_risk_summary = enhanced_risk_result.get('provider_risk_summary', {})
                is_multi_cloud = enhanced_risk_result.get('is_multi_cloud', False)
            else:
                # Fallback for basic risk assessment
                overall_risk = enhanced_risk_result
                provider_risk_summary = {}
                is_multi_cloud = False

            # Overall risk with multi-cloud context
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                risk_level = overall_risk.get('level', 'Unknown')
                risk_score = overall_risk.get('score', 0)
                risk_color = "🟢" if risk_level == "Low" else "🟡" if risk_level == "Medium" else "🔴"
                st.metric(
                    label=f"{risk_color} Overall Risk",
                    value=risk_level,
                    delta=f"Score: {risk_score}"
                )

            with col2:
                total_resources = overall_risk.get('total_resources', 0)
                high_risk_count = overall_risk.get('high_risk_count', 0)
                st.metric(
                    label="🏗️ Total Resources",
                    value=total_resources,
                    delta=f"High Risk: {high_risk_count}"
                )

            with col3:
                provider_count = len(provider_risk_summary)
                st.metric(
                    label="☁️ Cloud Providers",
                    value=provider_count if provider_count > 0 else 1,
                    delta="Multi-Cloud" if is_multi_cloud else "Single Cloud"
                )

            with col4:
                estimated_time = overall_risk.get('estimated_time', 'Unknown')
                avg_risk_score = overall_risk.get('average_risk_score', 0)
                st.metric(
                    label="⏱️ Est. Deployment Time",
                    value=estimated_time,
                    delta=f"Avg Risk: {avg_risk_score}"
                )

            # Provider Risk Breakdown
            if provider_risk_summary:
                st.markdown("### 📈 Provider Risk Breakdown")

                # Create DataFrame for provider risk summary
                provider_data = []
                for provider, summary in provider_risk_summary.items():
                    avg_risk = summary['total_risk_score'] / max(summary['total_resources'], 1)
                    provider_data.append({
                        'Provider': provider.upper(),
                        'Total Resources': summary['total_resources'],
                        'High Risk': summary['high_risk_count'],
                        'Medium Risk': summary['medium_risk_count'],
                        'Low Risk': summary['low_risk_count'],
                        'Avg Risk Score': round(avg_risk, 1)
                    })

                if provider_data:
                    provider_df = pd.DataFrame(provider_data)
                    st.dataframe(provider_df, use_container_width=True)

                    # Provider risk visualization
                    if len(provider_data) > 1:
                        st.markdown("### 📊 Provider Risk Comparison")
                        chart_gen = ChartGenerator()
                        if hasattr(chart_gen, 'create_provider_risk_comparison'):
                            fig = chart_gen.create_provider_risk_comparison(provider_risk_summary)
                            st.plotly_chart(fig, use_container_width=True)

        except Exception as e:
            st.error(f"Error in multi-cloud risk section: {e}")

    def render_cross_cloud_insights_section(self, enhanced_risk_assessor, resource_changes, plan_data):
        """
        Create cross-cloud insights and recommendations section.
        
        Args:
            enhanced_risk_assessor: EnhancedRiskAssessment instance
            resource_changes: List of resource changes from the plan
            plan_data: The parsed Terraform plan data
        """
        if not self.enhanced_features_available:
            return

        try:
            st.markdown("---")
            st.markdown("## 🔗 Cross-Cloud Insights")
            st.caption("Analysis of cross-provider dependencies, optimization opportunities, and security considerations for multi-cloud deployments.")

            # Get cross-cloud insights
            insights = enhanced_risk_assessor.get_cross_cloud_insights(resource_changes, plan_data)

            if insights.get('is_multi_cloud', False):
                st.markdown('<div class="multi-cloud-alert">🌐 Multi-cloud deployment detected</div>',
                            unsafe_allow_html=True)

                # Cross-cloud risks
                if insights.get('cross_cloud_risks'):
                    st.markdown("### ⚠️ Cross-Cloud Risks")
                    for risk in insights['cross_cloud_risks']:
                        st.write(f"• {risk}")

                col1, col2 = st.columns(2)

                with col1:
                    # Optimization opportunities
                    if insights.get('optimization_opportunities'):
                        st.markdown("### 🎯 Optimization Opportunities")
                        for opportunity in insights['optimization_opportunities']:
                            st.write(f"• {opportunity}")

                with col2:
                    # Security considerations
                    if insights.get('security_considerations'):
                        st.markdown("### 🔒 Security Considerations")
                        for consideration in insights['security_considerations']:
                            st.write(f"• {consideration}")

            else:
                st.info("✅ Single cloud provider deployment - no cross-cloud complexity")

        except Exception as e:
            st.error(f"Error in cross-cloud insights: {e}")

    def render_debug_section(self, debug_info, resource_changes, summary, enhanced_features_available, enable_multi_cloud):
        """
        Render debug information section.
        
        Args:
            debug_info: Debug information from the plan parser
            resource_changes: List of resource changes from the plan
            summary: Summary data from the plan parser
            enhanced_features_available: Whether enhanced features are available
            enable_multi_cloud: Whether multi-cloud features are enabled
        """
        st.markdown("## 🔍 Debug Information")
        st.markdown('<div class="debug-info">', unsafe_allow_html=True)

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**📊 Parsing Details:**")
            st.write(f"Total resource_changes in JSON: {debug_info.get('total_resource_changes', 'Unknown')}")
            st.write(f"Filtered resource_changes: {len(resource_changes)}")
            st.write(f"Summary total: {summary['total']}")
            st.write(f"Enhanced features: {'Available' if enhanced_features_available else 'Unavailable'}")
            if enhanced_features_available:
                st.write(f"Multi-cloud enabled: {'Yes' if enable_multi_cloud else 'No'}")
                st.write(f"Detected providers: {debug_info.get('detected_providers', {})}")

        with col2:
            st.markdown("**🎯 Action Patterns:**")
            action_patterns = debug_info.get('action_patterns', {})
            for pattern, count in action_patterns.items():
                st.write(f"`{pattern}`: {count} resources")

        st.markdown("**📁 Plan Structure:**")
        st.write(f"Has planned_values: {debug_info.get('has_planned_values', False)}")
        st.write(f"Has configuration: {debug_info.get('has_configuration', False)}")
        st.write(f"Has prior_state: {debug_info.get('has_prior_state', False)}")
        st.write(f"Plan keys: {', '.join(debug_info.get('plan_keys', []))}")

        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown("---")
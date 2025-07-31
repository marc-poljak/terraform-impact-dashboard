import streamlit as st
import json
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import components
from components.header import HeaderComponent
from components.sidebar import SidebarComponent
from components.upload_section import UploadComponent
from components.summary_cards import SummaryCardsComponent
from components.visualizations import VisualizationsComponent
from components.data_table import DataTableComponent
from components.enhanced_sections import EnhancedSectionsComponent
from components.report_generator import ReportGeneratorComponent
from components.security_analysis import SecurityAnalysisComponent
from components.help_system import HelpSystemComponent
from components.onboarding_checklist import OnboardingChecklistComponent

# Import UI utilities
from ui.session_manager import SessionStateManager
from ui.error_handler import ErrorHandler
from ui.progress_tracker import ProgressTracker
from ui.performance_optimizer import PerformanceOptimizer

# Import existing modules
from parsers.plan_parser import PlanParser
from visualizers.charts import ChartGenerator
from utils.plan_processor import PlanProcessor

# Try to import enhanced features, fall back to basic if not available
try:
    from utils.enhanced_risk_assessment import EnhancedRiskAssessment
    from providers.cloud_detector import CloudProviderDetector
    ENHANCED_FEATURES_AVAILABLE = True
except ImportError as e:
    print(f"Enhanced features not available: {e}")
    from utils.risk_assessment import RiskAssessment
    ENHANCED_FEATURES_AVAILABLE = False

st.set_page_config(page_title="Terraform Plan Impact Dashboard", page_icon="🚀", layout="wide", initial_sidebar_state="expanded")


def initialize_components(session_manager):
    """Initialize all dashboard components."""
    return {
        'header': HeaderComponent(),
        'sidebar': SidebarComponent(),
        'upload': UploadComponent(session_manager),
        'summary_cards': SummaryCardsComponent(session_manager),
        'visualizations': VisualizationsComponent(session_manager),
        'data_table': DataTableComponent(),
        'enhanced_sections': EnhancedSectionsComponent(),
        'report_generator': ReportGeneratorComponent(session_manager),
        'security_analysis': SecurityAnalysisComponent(session_manager),
        'help_system': HelpSystemComponent(session_manager),
        'onboarding_checklist': OnboardingChecklistComponent(session_manager)
    }


def process_plan_data(plan_input, components, session_manager, error_handler, plan_processor, show_debug, enable_multi_cloud):
    """Process plan data (from file upload or TFE) and coordinate data flow between components."""
    processed_data = plan_processor.process_plan_data(plan_input, components['upload'], error_handler, show_debug, enable_multi_cloud)
    if processed_data is None:
        return
    
    # Extract processed data
    plan_data = processed_data['plan_data']
    parser = processed_data['parser']
    summary = processed_data['summary']
    resource_changes = processed_data['resource_changes']
    resource_types = processed_data['resource_types']
    debug_info = processed_data['debug_info']
    enhanced_risk_assessor = processed_data['enhanced_risk_assessor']
    enhanced_risk_result = processed_data['enhanced_risk_result']
    risk_summary = processed_data['risk_summary']
    chart_gen = processed_data['chart_gen']

    error_handler.debug_mode = show_debug
    st.success("✅ **Plan processed successfully!**")
    
    error_handler.show_onboarding_hint(
        "Dashboard Navigation",
        "Your plan analysis is ready! Scroll down to explore summary cards, visualizations, and detailed resource tables.",
        show_once=True
    )
    
    if len(resource_changes) > 100:
        error_handler.show_feature_tooltip(
            "Large Plan Detected",
            f"Your plan contains {len(resource_changes)} resource changes. Some features may take longer to load.",
            "performance"
        )

    # Enhanced Multi-Cloud Sections
    if ENHANCED_FEATURES_AVAILABLE and enable_multi_cloud and enhanced_risk_assessor:
        components['enhanced_sections'].render_enhanced_dashboard_section(plan_data, parser, enhanced_risk_assessor)
        components['enhanced_sections'].render_multi_cloud_risk_section(enhanced_risk_result, resource_changes)
        components['enhanced_sections'].render_cross_cloud_insights_section(enhanced_risk_assessor, resource_changes, plan_data)

    if show_debug:
        components['enhanced_sections'].render_debug_section(debug_info, resource_changes, summary, ENHANCED_FEATURES_AVAILABLE, enable_multi_cloud)

    components['summary_cards'].render(summary, risk_summary, resource_types, plan_data, debug_info)
    components['help_system'].render_contextual_help_panel('analysis')
    components['onboarding_checklist'].render_contextual_hints('analysis')
    error_handler.track_user_progress('summary_viewed')
    components['onboarding_checklist'].mark_item_completed('summary_reviewed')

    components['visualizations'].render(
        summary=summary, resource_types=resource_types, resource_changes=resource_changes,
        plan_data=plan_data, chart_gen=chart_gen, parser=parser,
        enhanced_risk_assessor=enhanced_risk_assessor, enhanced_features_available=ENHANCED_FEATURES_AVAILABLE,
        enable_multi_cloud=enable_multi_cloud, show_debug=show_debug
    )
    error_handler.track_user_progress('charts_viewed')
    components['onboarding_checklist'].mark_item_completed('charts_explored')

    components['security_analysis'].render_security_highlighting(resource_changes)
    components['security_analysis'].render_compliance_checks(resource_changes)
    security_dashboard_data = components['security_analysis'].render_security_dashboard(resource_changes)

    components['data_table'].render(
        parser=parser, resource_changes=resource_changes, plan_data=plan_data,
        enhanced_risk_assessor=enhanced_risk_assessor, enhanced_risk_result=enhanced_risk_result,
        enable_multi_cloud=enable_multi_cloud
    )
    components['help_system'].render_contextual_help_panel('filters')
    components['onboarding_checklist'].render_contextual_hints('filtering')
    components['onboarding_checklist'].mark_item_completed('table_browsed')

    components['report_generator'].render_report_generator(
        summary=summary, risk_summary=risk_summary, resource_changes=resource_changes,
        resource_types=resource_types, plan_data=plan_data, enhanced_risk_assessor=enhanced_risk_assessor
    )

    components['summary_cards'].render_recommendations_section(
        summary, risk_summary, enhanced_risk_result, enhanced_risk_assessor, 
        resource_changes, plan_data, ENHANCED_FEATURES_AVAILABLE, enable_multi_cloud
    )


def main():
    """Main application function that orchestrates component rendering."""
    # Initialize core services and components
    session_manager = SessionStateManager()
    error_handler = ErrorHandler(debug_mode=session_manager.get_debug_state())
    plan_processor = PlanProcessor()
    components = initialize_components(session_manager)
    
    # Render header and sidebar
    components['header'].render_css()
    components['header'].render()
    sidebar_state = components['sidebar'].render(ENHANCED_FEATURES_AVAILABLE)
    show_debug, enable_multi_cloud = sidebar_state['show_debug'], sidebar_state['enable_multi_cloud']
    
    # Render help system and onboarding in sidebar
    components['help_system'].render_help_sidebar()
    components['help_system'].render_feature_discovery_hints()
    components['help_system'].render_smart_defaults_guide()
    components['help_system'].render_guided_tour_controls()
    components['onboarding_checklist'].render_progress_indicator()
    
    # Update service states
    error_handler.debug_mode = show_debug
    session_manager.set_debug_state(show_debug)
    session_manager.set_multi_cloud_state(enable_multi_cloud)
    
    # Render upload section with contextual help (supports both file upload and TFE)
    plan_input = components['upload'].render()
    components['help_system'].render_contextual_help_panel('upload')
    components['onboarding_checklist'].render_contextual_hints('file_upload')
    
    if plan_input is not None:
        # Both upload methods now return secure plan data dictionaries
        # Track progress for successful plan data retrieval
        error_handler.track_user_progress('plan_data_loaded')
        components['onboarding_checklist'].mark_item_completed('file_uploaded')

    if plan_input is not None:
        process_plan_data(plan_input, components, session_manager, error_handler, plan_processor, show_debug, enable_multi_cloud)
    else:
        components['onboarding_checklist'].render()
        components['onboarding_checklist'].render_enhanced_instructions()
        if st.session_state.get('show_accessibility_docs', False):
            components['help_system'].render_accessibility_documentation()
        components['help_system'].render_onboarding_checklist()


if __name__ == "__main__":
    main()
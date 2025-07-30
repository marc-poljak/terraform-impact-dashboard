import streamlit as st
import json
import sys
import os

# Add the current directory to the path so we can import our modules
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

# Page configuration
st.set_page_config(
    page_title="Terraform Plan Impact Dashboard",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)












def main():
    """
    Main application function that orchestrates component rendering.
    Preserves existing page configuration and feature detection logic.
    """
    # Initialize session manager and error handler
    session_manager = SessionStateManager()
    error_handler = ErrorHandler(debug_mode=session_manager.get_debug_state())
    
    # Initialize plan processor
    plan_processor = PlanProcessor()
    
    # Initialize components
    header = HeaderComponent()
    sidebar = SidebarComponent()
    upload = UploadComponent()
    summary_cards = SummaryCardsComponent(session_manager)
    visualizations = VisualizationsComponent(session_manager)
    data_table = DataTableComponent()
    enhanced_sections = EnhancedSectionsComponent()
    report_generator = ReportGeneratorComponent(session_manager)
    security_analysis = SecurityAnalysisComponent(session_manager)
    help_system = HelpSystemComponent(session_manager)
    onboarding_checklist = OnboardingChecklistComponent(session_manager)
    
    # Render CSS and header
    header.render_css()
    header.render()
    
    # Render sidebar and get control states
    sidebar_state = sidebar.render(ENHANCED_FEATURES_AVAILABLE)
    show_debug = sidebar_state['show_debug']
    enable_multi_cloud = sidebar_state['enable_multi_cloud']
    
    # Render help system in sidebar with enhanced onboarding
    help_system.render_help_sidebar()
    help_system.render_feature_discovery_hints()
    help_system.render_smart_defaults_guide()
    help_system.render_guided_tour_controls()
    
    # Render onboarding progress in sidebar
    onboarding_checklist.render_progress_indicator()
    
    # Update error handler debug mode and session state
    error_handler.debug_mode = show_debug
    session_manager.set_debug_state(show_debug)
    session_manager.set_multi_cloud_state(enable_multi_cloud)
    
    # Render upload section with onboarding integration
    uploaded_file = upload.render()
    
    # Show contextual help for upload section
    help_system.render_contextual_help_panel('upload')
    
    # Show contextual onboarding hints
    onboarding_checklist.render_contextual_hints('file_upload')
    
    # Track user progress for onboarding
    if uploaded_file is not None:
        error_handler.track_user_progress('file_uploaded')
        onboarding_checklist.mark_item_completed('file_uploaded')

    if uploaded_file is not None:
        # Process plan data using centralized workflow with enhanced progress tracking
        processed_data = plan_processor.process_plan_data(uploaded_file, upload, error_handler, show_debug, enable_multi_cloud)
        
        if processed_data is None:
            return  # Error already handled by process_plan_data
        
        # Extract processed data for component coordination
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

        # Enhanced success message with guidance
        # Update error handler debug mode
        error_handler.debug_mode = show_debug
        
        st.success("✅ **Plan processed successfully!**")
        
        # Show onboarding guidance for new users
        error_handler.show_onboarding_hint(
            "Dashboard Navigation",
            "Your plan analysis is ready! Scroll down to explore summary cards, visualizations, and detailed resource tables.",
            show_once=True
        )
        
        # Show performance info for large plans
        if len(resource_changes) > 100:
            error_handler.show_feature_tooltip(
                "Large Plan Detected",
                f"Your plan contains {len(resource_changes)} resource changes. Some features may take longer to load.",
                "performance"
            )

        # Enhanced Multi-Cloud Sections (only if enhanced features enabled)
        if ENHANCED_FEATURES_AVAILABLE and enable_multi_cloud and enhanced_risk_assessor:
            enhanced_sections.render_enhanced_dashboard_section(plan_data, parser, enhanced_risk_assessor)
            enhanced_sections.render_multi_cloud_risk_section(enhanced_risk_result, resource_changes)
            enhanced_sections.render_cross_cloud_insights_section(enhanced_risk_assessor, resource_changes, plan_data)

        # Debug Information Section
        if show_debug:
            enhanced_sections.render_debug_section(debug_info, resource_changes, summary, ENHANCED_FEATURES_AVAILABLE, enable_multi_cloud)

        # Summary Cards Section using component
        summary_cards.render(summary, risk_summary, resource_types, plan_data, debug_info)
        
        # Show contextual help for analysis results
        help_system.render_contextual_help_panel('analysis')
        
        # Show contextual onboarding hints
        onboarding_checklist.render_contextual_hints('analysis')
        
        # Track progress for onboarding
        error_handler.track_user_progress('summary_viewed')
        onboarding_checklist.mark_item_completed('summary_reviewed')

        # Visualizations Section using component
        visualizations.render(
            summary=summary,
            resource_types=resource_types,
            resource_changes=resource_changes,
            plan_data=plan_data,
            chart_gen=chart_gen,
            parser=parser,
            enhanced_risk_assessor=enhanced_risk_assessor,
            enhanced_features_available=ENHANCED_FEATURES_AVAILABLE,
            enable_multi_cloud=enable_multi_cloud,
            show_debug=show_debug
        )
        
        # Track progress for onboarding
        error_handler.track_user_progress('charts_viewed')
        onboarding_checklist.mark_item_completed('charts_explored')

        # Security Analysis Section using component
        security_analysis.render_security_highlighting(resource_changes)
        security_analysis.render_compliance_checks(resource_changes)
        security_dashboard_data = security_analysis.render_security_dashboard(resource_changes)

        # Data Table Section using component
        data_table.render(
            parser=parser,
            resource_changes=resource_changes,
            plan_data=plan_data,
            enhanced_risk_assessor=enhanced_risk_assessor,
            enhanced_risk_result=enhanced_risk_result,
            enable_multi_cloud=enable_multi_cloud
        )
        
        # Show contextual help for filtering and search
        help_system.render_contextual_help_panel('filters')
        
        # Show contextual onboarding hints for filtering
        onboarding_checklist.render_contextual_hints('filtering')
        onboarding_checklist.mark_item_completed('table_browsed')

        # Report Generator Section using component
        report_generator.render_report_generator(
            summary=summary,
            risk_summary=risk_summary,
            resource_changes=resource_changes,
            resource_types=resource_types,
            plan_data=plan_data,
            enhanced_risk_assessor=enhanced_risk_assessor
        )

        # Footer with Enhanced Recommendations
        summary_cards.render_recommendations_section(
            summary, risk_summary, enhanced_risk_result, enhanced_risk_assessor, 
            resource_changes, plan_data, ENHANCED_FEATURES_AVAILABLE, enable_multi_cloud
        )

    else:
        # Show comprehensive onboarding checklist
        onboarding_checklist.render()
        
        # Show enhanced instructions when no file is uploaded
        onboarding_checklist.render_enhanced_instructions()
        
        # Show accessibility documentation if requested
        if st.session_state.get('show_accessibility_docs', False):
            help_system.render_accessibility_documentation()
        
        # Show onboarding checklist for new users
        help_system.render_onboarding_checklist()


if __name__ == "__main__":
    main()
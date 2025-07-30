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


def render_debug_section(debug_info, resource_changes, summary, enhanced_features_available, enable_multi_cloud):
    """Render debug information section"""
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





def render_recommendations_section(summary, risk_summary, enhanced_risk_result, enhanced_risk_assessor, 
                                 resource_changes, plan_data, enhanced_features_available, enable_multi_cloud):
    """Render the recommendations and summary section"""
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


def process_plan_data(uploaded_file, upload_component, error_handler, show_debug, enable_multi_cloud):
    """
    Centralized plan data processing workflow with enhanced progress tracking and performance optimization.
    Maintains compatibility with existing parsers, risk assessors, and chart generators.
    
    Args:
        uploaded_file: The uploaded file from Streamlit
        upload_component: UploadComponent instance
        error_handler: ErrorHandler instance
        show_debug: Whether debug mode is enabled
        enable_multi_cloud: Whether multi-cloud features are enabled
        
    Returns:
        Dict containing processed data or None if processing failed
    """
    # Initialize progress tracker and performance optimizer
    progress_tracker = ProgressTracker()
    performance_optimizer = PerformanceOptimizer()
    file_size = uploaded_file.size if hasattr(uploaded_file, 'size') else len(uploaded_file.getvalue())
    
    # Use progress tracking context manager for file processing
    with progress_tracker.track_file_processing(file_size) as stage_tracker:
        try:
            # Stage 1: Parsing - Validate and parse the uploaded file
            stage_tracker.next_stage()  # Show parsing progress
            with performance_optimizer.performance_monitor("file_parsing"):
                plan_data, error_msg = upload_component.validate_and_parse_file(uploaded_file, show_debug)
                if plan_data is None:
                    return None
            
            # Stage 2: Validation - Parse the uploaded file using existing PlanParser
            stage_tracker.next_stage()  # Show validation progress
            with performance_optimizer.performance_monitor("plan_parser_init"):
                parser = PlanParser(plan_data)
            
            # Stage 3: Extraction - Extract metrics using existing data structures
            stage_tracker.next_stage()  # Show extraction progress
            with performance_optimizer.performance_monitor("data_extraction"):
                summary = parser.get_summary()
                resource_changes = parser.get_resource_changes()
                resource_types = parser.get_resource_types()
                debug_info = parser.get_debug_info()
            
            # Stage 4: Risk Assessment - Risk assessment with error handling and fallback
            stage_tracker.next_stage()  # Show risk assessment progress
            with performance_optimizer.performance_monitor("risk_assessment"):
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
            metrics = performance_optimizer.get_performance_metrics()
            
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
        'performance_optimizer': performance_optimizer  # Include for components to use
    }


def main():
    """
    Main application function that orchestrates component rendering.
    Preserves existing page configuration and feature detection logic.
    """
    # Initialize session manager and error handler
    session_manager = SessionStateManager()
    error_handler = ErrorHandler(debug_mode=session_manager.get_debug_state())
    
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
        processed_data = process_plan_data(uploaded_file, upload, error_handler, show_debug, enable_multi_cloud)
        
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
            render_debug_section(debug_info, resource_changes, summary, ENHANCED_FEATURES_AVAILABLE, enable_multi_cloud)

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
        render_recommendations_section(
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
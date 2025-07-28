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


def render_enhanced_instructions():
    """
    Render enhanced instructions and onboarding for new users.
    Provides detailed guidance on file format, usage, and features.
    """
    # Welcome section with clear overview
    st.markdown("## 🚀 Welcome to Terraform Plan Impact Dashboard")
    st.markdown("""
    This dashboard helps you analyze and visualize Terraform plan changes before deployment. 
    Get insights into resource changes, risk assessment, and multi-cloud impacts.
    """)
    
    # Getting started section with detailed steps
    st.markdown("---")
    st.markdown("## 📖 Getting Started")
    
    # Step-by-step instructions with more detail
    with st.expander("📋 **Step 1: Generate Your Terraform Plan JSON**", expanded=True):
        st.markdown("""
        First, you need to generate a Terraform plan in JSON format:
        
        ```bash
        # Navigate to your Terraform project directory
        cd /path/to/your/terraform/project
        
        # Generate the plan and save as JSON
        terraform plan -out=tfplan
        terraform show -json tfplan > terraform-plan.json
        ```
        
        **Alternative method (direct JSON output):**
        ```bash
        terraform plan -json > terraform-plan.json
        ```
        
        ⚠️ **Important:** The JSON file should contain a `resource_changes` array with your planned infrastructure changes.
        """)
    
    with st.expander("📁 **Step 2: Upload Your Plan File**"):
        st.markdown("""
        - Use the file uploader above to select your JSON file
        - Supported formats: `.json` files only
        - File size: Up to 200MB supported
        - The file will be validated automatically upon upload
        
        **Expected file structure:**
        ```json
        {
          "terraform_version": "1.5.0",
          "format_version": "1.2",
          "resource_changes": [
            {
              "address": "aws_instance.example",
              "type": "aws_instance",
              "change": {
                "actions": ["create"],
                "before": null,
                "after": { ... }
              }
            }
          ]
        }
        ```
        """)
    
    with st.expander("📊 **Step 3: Analyze Your Results**"):
        st.markdown("""
        Once uploaded, you'll see several analysis sections:
        
        **📈 Summary Cards:** Overview of changes (create/update/delete counts)
        **⚠️ Risk Assessment:** Intelligent scoring of deployment risks
        **📊 Visualizations:** Interactive charts showing resource distributions
        **📋 Detailed Table:** Filterable list of all resource changes
        **🔍 Multi-Cloud Analysis:** Cross-provider insights (if enabled)
        
        **Pro Tips:**
        - Use filters in the sidebar to focus on specific resources
        - Enable debug mode for detailed parsing information
        - Export filtered data as CSV for further analysis
        """)
    
    # Sample data section with better explanation
    st.markdown("---")
    st.markdown("## 🧪 Try with Sample Data")
    st.markdown("""
    New to the dashboard? Try it out with sample data to explore all features without uploading your own files.
    """)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        **Sample data includes:**
        - AWS EC2 instance creation
        - Security group configuration
        - S3 bucket versioning update
        - Demonstrates create, update, and delete actions
        """)
    
    with col2:
        if st.button("🔧 Generate Sample Plan", type="primary"):
            sample_data = {
                "terraform_version": "1.5.0",
                "format_version": "1.2",
                "planned_values": {
                    "root_module": {
                        "resources": []
                    }
                },
                "resource_changes": [
                    {
                        "address": "aws_instance.web_server",
                        "mode": "managed",
                        "type": "aws_instance",
                        "name": "web_server",
                        "provider_name": "registry.terraform.io/hashicorp/aws",
                        "change": {
                            "actions": ["create"],
                            "before": None,
                            "after": {
                                "instance_type": "t3.micro",
                                "ami": "ami-0abcdef1234567890",
                                "availability_zone": "us-west-2a",
                                "tags": {
                                    "Name": "WebServer",
                                    "Environment": "Production"
                                }
                            }
                        }
                    },
                    {
                        "address": "aws_security_group.web_sg",
                        "mode": "managed", 
                        "type": "aws_security_group",
                        "name": "web_sg",
                        "provider_name": "registry.terraform.io/hashicorp/aws",
                        "change": {
                            "actions": ["create"],
                            "before": None,
                            "after": {
                                "name": "web-security-group",
                                "description": "Security group for web server",
                                "ingress": [
                                    {
                                        "from_port": 80,
                                        "to_port": 80,
                                        "protocol": "tcp",
                                        "cidr_blocks": ["0.0.0.0/0"]
                                    }
                                ]
                            }
                        }
                    },
                    {
                        "address": "aws_s3_bucket.data_bucket",
                        "mode": "managed",
                        "type": "aws_s3_bucket", 
                        "name": "data_bucket",
                        "provider_name": "registry.terraform.io/hashicorp/aws",
                        "change": {
                            "actions": ["update"],
                            "before": {
                                "versioning": [{"enabled": False}],
                                "bucket": "my-data-bucket-12345"
                            },
                            "after": {
                                "versioning": [{"enabled": True}],
                                "bucket": "my-data-bucket-12345"
                            }
                        }
                    },
                    {
                        "address": "aws_iam_role.deprecated_role",
                        "mode": "managed",
                        "type": "aws_iam_role",
                        "name": "deprecated_role",
                        "provider_name": "registry.terraform.io/hashicorp/aws",
                        "change": {
                            "actions": ["delete"],
                            "before": {
                                "name": "deprecated-service-role",
                                "assume_role_policy": "{...}"
                            },
                            "after": None
                        }
                    }
                ]
            }
            
            # Convert to JSON and offer download
            import json
            sample_json = json.dumps(sample_data, indent=2)
            st.download_button(
                label="📥 Download Sample Plan JSON",
                data=sample_json,
                file_name="sample-terraform-plan.json",
                mime="application/json",
                help="Download this sample file and upload it above to test the dashboard"
            )
            
            st.success("✅ Sample data generated! Download the file and upload it above to explore the dashboard features.")

    # Feature highlights with better organization
    st.markdown("---")
    st.markdown("## ✨ Dashboard Features")
    
    # Create tabs for better organization
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Analytics", "⚠️ Risk Assessment", "🔍 Advanced Features", "🛠️ Troubleshooting"])
    
    with tab1:
        st.markdown("""
        ### Visual Analytics
        
        **📈 Resource Distribution Charts**
        - Pie charts showing resource types in your plan
        - Bar charts displaying action types (create/update/delete)
        - Interactive charts with hover details
        
        **📊 Change Summary Cards**
        - Quick overview of total changes
        - Color-coded metrics for easy scanning
        - Resource type breakdowns
        
        **🎯 Multi-Cloud Visualizations** *(Enhanced Features)*
        - Cross-provider resource distribution
        - Provider-specific risk analysis
        - Cloud service usage patterns
        """)
    
    with tab2:
        st.markdown("""
        ### Risk Assessment
        
        **🔍 Intelligent Risk Scoring**
        - Automated risk level calculation (Low/Medium/High/Critical)
        - Deployment time estimation
        - Resource-specific risk factors
        
        **⚠️ Security Analysis** *(Enhanced Features)*
        - Security-focused resource highlighting
        - Compliance framework checks
        - Cross-cloud security considerations
        
        **📋 Risk Recommendations**
        - Actionable suggestions for risk mitigation
        - Best practice recommendations
        - Deployment strategy guidance
        """)
    
    with tab3:
        st.markdown("""
        ### Advanced Features
        
        **🔍 Interactive Filtering**
        - Filter by action type (create/update/delete)
        - Filter by risk level
        - Filter by cloud provider *(Enhanced Features)*
        - Text search across resource names and types
        
        **📤 Data Export**
        - Export filtered results as CSV
        - Include all resource details and risk scores
        - Perfect for reporting and further analysis
        
        **🐛 Debug Information**
        - Detailed parsing information
        - Plan structure analysis
        - Error diagnostics and troubleshooting
        """)
    
    with tab4:
        st.markdown("""
        ### Troubleshooting
        
        **❌ Common Issues**
        
        **"Invalid JSON file" error:**
        - Ensure your file is valid JSON format
        - Check that `terraform show -json` completed successfully
        - Verify the file isn't corrupted during transfer
        
        **"No resource changes found" message:**
        - Your plan might not contain any changes
        - Check that you ran `terraform plan` before generating JSON
        - Verify your Terraform configuration has pending changes
        
        **Missing enhanced features:**
        - Some features require additional dependencies
        - Basic functionality will still work without enhanced features
        - Check the sidebar for feature availability status
        
        **Performance issues with large files:**
        - Files over 10MB may take longer to process
        - Consider filtering your plan to specific resources
        - Enable debug mode to see processing details
        
        **🆘 Need Help?**
        - Enable debug mode in the sidebar for detailed information
        - Check the console for error messages
        - Ensure your Terraform plan JSON follows the expected format
        """)

    # Quick tips section
    st.markdown("---")
    st.markdown("## 💡 Quick Tips")
    
    tip_col1, tip_col2 = st.columns(2)
    
    with tip_col1:
        st.info("""
        **🚀 Pro Tips:**
        - Use `terraform plan -detailed-exitcode` to check if changes exist
        - Large plans process faster with multi-cloud features disabled
        - Export filtered data for stakeholder reports
        - Enable debug mode when troubleshooting issues
        """)
    
    with tip_col2:
        st.warning("""
        **⚠️ Important Notes:**
        - This tool analyzes plans only - it doesn't modify your infrastructure
        - Always review changes carefully before running `terraform apply`
        - Risk scores are estimates - use your judgment for critical deployments
        - Keep your Terraform plans secure and don't share sensitive data
        """)


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
    
    # Render CSS and header
    header.render_css()
    header.render()
    
    # Render sidebar and get control states
    sidebar_state = sidebar.render(ENHANCED_FEATURES_AVAILABLE)
    show_debug = sidebar_state['show_debug']
    enable_multi_cloud = sidebar_state['enable_multi_cloud']
    
    # Update error handler debug mode and session state
    error_handler.debug_mode = show_debug
    session_manager.set_debug_state(show_debug)
    session_manager.set_multi_cloud_state(enable_multi_cloud)
    
    # Render upload section
    uploaded_file = upload.render()

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

        # Display success message
        st.success("✅ Plan processed successfully!")

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

        # Data Table Section using component
        data_table.render(
            parser=parser,
            resource_changes=resource_changes,
            plan_data=plan_data,
            enhanced_risk_assessor=enhanced_risk_assessor,
            enhanced_risk_result=enhanced_risk_result,
            enable_multi_cloud=enable_multi_cloud
        )

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
        # Show enhanced instructions when no file is uploaded
        render_enhanced_instructions()


if __name__ == "__main__":
    main()
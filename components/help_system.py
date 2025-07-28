"""
Help System Component

Provides comprehensive contextual help and onboarding for the Terraform Plan Impact Dashboard.
"""

import streamlit as st
from typing import Dict, List, Optional, Any
from .base_component import BaseComponent


class HelpSystemComponent(BaseComponent):
    """Component for providing contextual help and onboarding guidance"""
    
    def __init__(self, session_manager: Optional[Any] = None):
        """
        Initialize the HelpSystemComponent
        
        Args:
            session_manager: Optional session state manager
        """
        super().__init__(session_manager)
        self.help_content = self._load_help_content()
    
    def render(self, *args, **kwargs) -> Any:
        """
        Main render method - delegates to specific render methods
        
        Returns:
            None - this component renders UI elements directly
        """
        # This component doesn't have a single main render method
        # Instead it provides multiple render methods for different contexts
        pass
    
    def render_help_sidebar(self) -> None:
        """Render help options in the sidebar"""
        st.sidebar.markdown("---")
        st.sidebar.markdown("### 📚 Help & Guidance")
        
        # Quick help toggle
        show_help = st.sidebar.checkbox(
            "💡 Show Contextual Help",
            value=False,
            help="Enable to see helpful tooltips and guidance throughout the dashboard"
        )
        
        if show_help:
            st.sidebar.success("💡 Contextual help enabled")
            self._set_session_state('show_contextual_help', True)
        else:
            self._set_session_state('show_contextual_help', False)
        
        # Help topics dropdown
        help_topics = [
            "Getting Started",
            "File Upload Guide", 
            "Understanding Risk Levels",
            "Using Filters",
            "Reading Visualizations",
            "Multi-Cloud Features",
            "Troubleshooting"
        ]
        
        selected_topic = st.sidebar.selectbox(
            "📖 Help Topics",
            options=["Select a topic..."] + help_topics,
            help="Choose a topic to get detailed help information"
        )
        
        if selected_topic != "Select a topic...":
            self.show_help_topic(selected_topic)
        
        # Quick actions
        st.sidebar.markdown("#### 🚀 Quick Actions")
        
        col1, col2 = st.sidebar.columns(2)
        
        with col1:
            if st.button("🎯 Tour", help="Take a guided tour of the dashboard"):
                self.start_guided_tour()
        
        with col2:
            if st.button("❓ FAQ", help="View frequently asked questions"):
                self.show_faq()
    
    def show_help_topic(self, topic: str) -> None:
        """
        Show detailed help for a specific topic
        
        Args:
            topic: The help topic to display
        """
        help_data = self.help_content.get(topic.lower().replace(' ', '_'), {})
        
        if help_data:
            with st.sidebar.expander(f"📖 {topic}", expanded=True):
                if help_data.get('summary'):
                    st.markdown(f"**{help_data['summary']}**")
                
                if help_data.get('content'):
                    st.markdown(help_data['content'])
                
                if help_data.get('tips'):
                    st.markdown("**💡 Tips:**")
                    for tip in help_data['tips']:
                        st.write(f"• {tip}")
    
    def show_contextual_tooltip(self, feature: str, context: str = "general") -> None:
        """
        Show contextual tooltip if help is enabled
        
        Args:
            feature: The feature to show help for
            context: The context where help is shown
        """
        if self._get_session_state('show_contextual_help', False):
            help_key = f"{feature.lower().replace(' ', '_')}_{context}"
            tooltip_data = self.help_content.get('tooltips', {}).get(help_key, {})
            
            if tooltip_data:
                st.info(f"💡 **{feature}:** {tooltip_data.get('text', 'Help information not available')}")
    
    def start_guided_tour(self) -> None:
        """Start a guided tour of the dashboard"""
        st.sidebar.info("🎯 **Guided Tour Started!**")
        st.sidebar.markdown("""
        **Welcome to your dashboard tour:**
        
        1. **📁 Upload Section** - Start by uploading your Terraform plan JSON
        2. **📊 Summary Cards** - View change counts and risk levels  
        3. **📈 Visualizations** - Explore interactive charts
        4. **📋 Data Table** - Filter and search detailed resource information
        5. **🔍 Filters** - Use sidebar controls to focus your analysis
        
        **Tour Tips:**
        • Look for 💡 icons for contextual help
        • Use the help topics dropdown for detailed guidance
        • Enable debug mode for troubleshooting
        """)
        
        # Set tour state
        self._set_session_state('guided_tour_active', True)
        self._set_session_state('tour_step', 1)
    
    def show_faq(self) -> None:
        """Show frequently asked questions"""
        with st.sidebar.expander("❓ **Frequently Asked Questions**", expanded=True):
            st.markdown("""
            **Q: What file format do I need?**
            A: Upload a JSON file generated from `terraform show -json plan.tfplan`
            
            **Q: Why are enhanced features unavailable?**
            A: Enhanced features require additional dependencies. Check the feature status in the sidebar.
            
            **Q: How is risk level calculated?**
            A: Risk is based on resource types, actions, and potential impact. Delete operations have higher risk.
            
            **Q: Can I analyze multiple plans?**
            A: Upload one plan at a time. Use browser tabs for multiple analyses.
            
            **Q: What if my plan is very large?**
            A: Large plans (>50MB) may take longer to process. Consider using targeted plans.
            
            **Q: How do I export my analysis?**
            A: Use the CSV download button in the data table section.
            """)
    
    def show_feature_announcement(self, feature_name: str, description: str, 
                                is_new: bool = True) -> None:
        """
        Show announcement for new or updated features
        
        Args:
            feature_name: Name of the feature
            description: Description of the feature
            is_new: Whether this is a new feature
        """
        announcement_key = f"announcement_{feature_name.lower().replace(' ', '_')}"
        
        if not self._get_session_state(f"{announcement_key}_dismissed", False):
            icon = "🆕" if is_new else "🔄"
            status = "New" if is_new else "Updated"
            
            col1, col2 = st.columns([4, 1])
            
            with col1:
                st.info(f"{icon} **{status} Feature: {feature_name}** - {description}")
            
            with col2:
                if st.button("✕", key=f"dismiss_{announcement_key}", help="Dismiss this announcement"):
                    self._set_session_state(f"{announcement_key}_dismissed", True)
                    st.rerun()
    
    def _load_help_content(self) -> Dict:
        """Load help content for various topics"""
        return {
            'getting_started': {
                'summary': 'Learn how to use the Terraform Plan Impact Dashboard',
                'content': """
                **Step 1:** Generate your Terraform plan JSON file
                **Step 2:** Upload the file using the file uploader
                **Step 3:** Review the analysis results
                **Step 4:** Use filters to focus on specific resources
                **Step 5:** Export data for further analysis
                """,
                'tips': [
                    "Start with small plans to get familiar with the interface",
                    "Enable debug mode if you encounter issues",
                    "Use the sidebar filters to focus your analysis"
                ]
            },
            'file_upload_guide': {
                'summary': 'How to generate and upload Terraform plan files',
                'content': """
                **Generate plan file:**
                ```bash
                terraform plan -out=tfplan
                terraform show -json tfplan > plan.json
                ```
                
                **File requirements:**
                • Valid JSON format
                • Contains 'resource_changes' array
                • Maximum size: 200MB
                """,
                'tips': [
                    "Use binary plan first, then convert to JSON for best results",
                    "Validate JSON syntax if upload fails",
                    "Consider targeted plans for large infrastructures"
                ]
            },
            'understanding_risk_levels': {
                'summary': 'How risk assessment works in the dashboard',
                'content': """
                **Risk Levels:**
                • **Low (0-30):** Safe changes with minimal impact
                • **Medium (31-70):** Changes requiring attention
                • **High (71-90):** Potentially dangerous changes
                • **Critical (91-100):** High risk of disruption
                
                **Risk Factors:**
                • Resource type criticality
                • Action type (delete > update > create)
                • Dependencies and relationships
                • Security implications
                """,
                'tips': [
                    "Always review high-risk resources carefully",
                    "Delete operations automatically get higher risk scores",
                    "Use filters to focus on high-risk resources first"
                ]
            },
            'tooltips': {
                'file_upload_general': {
                    'text': 'Upload your Terraform plan JSON file to begin analysis'
                },
                'risk_assessment_general': {
                    'text': 'Risk levels help you understand the potential impact of your changes'
                },
                'filters_general': {
                    'text': 'Use filters to focus on specific resources or change types'
                },
                'visualizations_general': {
                    'text': 'Interactive charts show patterns in your infrastructure changes'
                }
            }
        }
    
    def render_onboarding_checklist(self) -> None:
        """Render an onboarding checklist for new users"""
        if not self._get_session_state('onboarding_completed', False):
            with st.expander("🎯 **Getting Started Checklist**", expanded=True):
                st.markdown("**Complete these steps to get the most from your analysis:**")
                
                # Checklist items
                checklist_items = [
                    ("Upload Terraform plan JSON file", 'file_uploaded'),
                    ("Review summary cards for overview", 'summary_reviewed'),
                    ("Explore visualizations", 'charts_viewed'),
                    ("Use filters to focus analysis", 'filters_used'),
                    ("Export data if needed", 'data_exported')
                ]
                
                completed_count = 0
                for item_text, item_key in checklist_items:
                    is_completed = self._get_session_state(item_key, False)
                    if is_completed:
                        completed_count += 1
                        st.success(f"✅ {item_text}")
                    else:
                        st.info(f"⏳ {item_text}")
                
                # Progress indicator
                progress = completed_count / len(checklist_items)
                st.progress(progress)
                st.caption(f"Progress: {completed_count}/{len(checklist_items)} steps completed")
                
                # Mark as completed if all done
                if completed_count == len(checklist_items):
                    if st.button("🎉 Mark Onboarding Complete"):
                        self._set_session_state('onboarding_completed', True)
                        st.success("🎉 Onboarding completed! You're ready to analyze Terraform plans.")
                        st.rerun()
    
    def render_interactive_tutorial(self) -> None:
        """Render interactive tutorial for new users"""
        if not self._get_session_state('tutorial_completed', False):
            tutorial_step = self._get_session_state('tutorial_step', 0)
            
            if tutorial_step == 0:
                # Welcome step
                st.info("🎓 **Welcome to the Interactive Tutorial!**")
                st.markdown("""
                This tutorial will guide you through the key features of the Terraform Plan Impact Dashboard.
                You'll learn how to upload files, interpret results, and use advanced features.
                """)
                
                col1, col2 = st.columns([1, 1])
                with col1:
                    if st.button("🚀 Start Tutorial", type="primary"):
                        self._set_session_state('tutorial_step', 1)
                        st.rerun()
                with col2:
                    if st.button("⏭️ Skip Tutorial"):
                        self._set_session_state('tutorial_completed', True)
                        st.rerun()
                        
            elif tutorial_step == 1:
                # File upload tutorial
                st.success("📁 **Step 1: File Upload**")
                st.markdown("""
                **What you'll learn:** How to generate and upload Terraform plan files
                
                **Key points:**
                - Generate JSON from Terraform plans using `terraform show -json`
                - Supported file formats and size limits
                - File validation and error handling
                
                **Try it:** Look at the file upload section above and try uploading a plan file.
                """)
                
                # Show sample command
                with st.expander("📋 **Sample Commands**", expanded=True):
                    st.code("""
# Generate Terraform plan
terraform plan -out=tfplan

# Convert to JSON
terraform show -json tfplan > plan.json

# Upload the plan.json file above
                    """, language="bash")
                
                col1, col2 = st.columns([1, 1])
                with col1:
                    if st.button("⬅️ Previous"):
                        self._set_session_state('tutorial_step', 0)
                        st.rerun()
                with col2:
                    if st.button("➡️ Next Step"):
                        self._set_session_state('tutorial_step', 2)
                        st.rerun()
                        
            elif tutorial_step == 2:
                # Analysis tutorial
                st.success("📊 **Step 2: Understanding Analysis Results**")
                st.markdown("""
                **What you'll learn:** How to interpret dashboard results
                
                **Key sections:**
                - **Summary Cards:** Quick overview of changes and risk levels
                - **Visualizations:** Interactive charts showing resource distributions
                - **Data Table:** Detailed resource information with filtering
                - **Risk Assessment:** Intelligent scoring of deployment risks
                
                **Interactive elements:**
                - Hover over charts for details
                - Click on legend items to filter
                - Use sidebar controls to focus analysis
                """)
                
                col1, col2 = st.columns([1, 1])
                with col1:
                    if st.button("⬅️ Previous"):
                        self._set_session_state('tutorial_step', 1)
                        st.rerun()
                with col2:
                    if st.button("➡️ Next Step"):
                        self._set_session_state('tutorial_step', 3)
                        st.rerun()
                        
            elif tutorial_step == 3:
                # Filtering tutorial
                st.success("🔍 **Step 3: Advanced Filtering**")
                st.markdown("""
                **What you'll learn:** How to use filters effectively
                
                **Filter types:**
                - **Action Filter:** Focus on create/update/delete operations
                - **Risk Filter:** Show only high-risk or low-risk changes
                - **Provider Filter:** Multi-cloud analysis (if available)
                - **Text Search:** Find specific resources by name or type
                
                **Pro tips:**
                - Combine multiple filters for precise analysis
                - Save filter combinations for reuse
                - Export filtered results as CSV
                """)
                
                # Show filter examples
                with st.expander("💡 **Filter Examples**", expanded=True):
                    st.markdown("""
                    **Common filter combinations:**
                    - **High-risk deletions:** Risk=High + Action=Delete
                    - **New resources:** Action=Create
                    - **Database changes:** Search="database" or "rds" or "sql"
                    - **Security resources:** Search="security" or "iam" or "policy"
                    """)
                
                col1, col2 = st.columns([1, 1])
                with col1:
                    if st.button("⬅️ Previous"):
                        self._set_session_state('tutorial_step', 2)
                        st.rerun()
                with col2:
                    if st.button("➡️ Next Step"):
                        self._set_session_state('tutorial_step', 4)
                        st.rerun()
                        
            elif tutorial_step == 4:
                # Advanced features tutorial
                st.success("✨ **Step 4: Advanced Features**")
                st.markdown("""
                **What you'll learn:** Advanced dashboard capabilities
                
                **Enhanced features (when available):**
                - **Multi-cloud Analysis:** Cross-provider insights
                - **Security Analysis:** Security-focused resource highlighting
                - **Dependency Visualization:** Resource relationship graphs
                - **Report Generation:** PDF/HTML export capabilities
                
                **Debug mode:**
                - Enable in sidebar for troubleshooting
                - Shows detailed parsing information
                - Helps diagnose file format issues
                """)
                
                col1, col2 = st.columns([1, 1])
                with col1:
                    if st.button("⬅️ Previous"):
                        self._set_session_state('tutorial_step', 3)
                        st.rerun()
                with col2:
                    if st.button("🎉 Complete Tutorial"):
                        self._set_session_state('tutorial_completed', True)
                        self._set_session_state('tutorial_step', 0)
                        st.success("🎉 Tutorial completed! You're now ready to use the dashboard effectively.")
                        st.balloons()
                        st.rerun()
    
    def render_feature_discovery_hints(self) -> None:
        """Render contextual feature discovery hints"""
        # Show hints based on current context and user progress
        hints_shown = self._get_session_state('discovery_hints_shown', [])
        
        # Hint about multi-cloud features
        if 'multi_cloud_hint' not in hints_shown and not self._get_session_state('multi_cloud_discovered', False):
            if st.sidebar.button("💡 Discover Multi-Cloud Features"):
                self._show_discovery_hint('multi_cloud', {
                    'title': 'Multi-Cloud Analysis',
                    'description': 'Analyze Terraform plans that span multiple cloud providers (AWS, Azure, GCP)',
                    'benefits': [
                        'Cross-provider risk assessment',
                        'Provider-specific recommendations',
                        'Multi-cloud security insights',
                        'Resource distribution across clouds'
                    ],
                    'how_to_enable': 'Enable "Multi-cloud features" in the sidebar when analyzing plans with multiple providers'
                })
                self._mark_hint_shown('multi_cloud_hint')
                self._set_session_state('multi_cloud_discovered', True)
        
        # Hint about advanced filtering
        if 'advanced_filtering_hint' not in hints_shown and not self._get_session_state('advanced_filtering_discovered', False):
            if st.sidebar.button("🔍 Discover Advanced Filtering"):
                self._show_discovery_hint('advanced_filtering', {
                    'title': 'Advanced Filtering & Search',
                    'description': 'Powerful filtering capabilities to focus your analysis',
                    'benefits': [
                        'Text search across resource names and types',
                        'Combine multiple filter criteria',
                        'Save and reuse filter configurations',
                        'Export filtered results'
                    ],
                    'how_to_enable': 'Use the filter controls in the sidebar and try the search box in the data table'
                })
                self._mark_hint_shown('advanced_filtering_hint')
                self._set_session_state('advanced_filtering_discovered', True)
        
        # Hint about report generation
        if 'report_generation_hint' not in hints_shown and not self._get_session_state('report_generation_discovered', False):
            if st.sidebar.button("📄 Discover Report Generation"):
                self._show_discovery_hint('report_generation', {
                    'title': 'Comprehensive Report Generation',
                    'description': 'Generate detailed reports for stakeholders and documentation',
                    'benefits': [
                        'Executive summary with key metrics',
                        'Risk analysis and recommendations',
                        'Visual charts and graphs included',
                        'PDF and HTML export formats'
                    ],
                    'how_to_enable': 'Look for the "Generate Report" section after uploading a plan file'
                })
                self._mark_hint_shown('report_generation_hint')
                self._set_session_state('report_generation_discovered', True)
    
    def _show_discovery_hint(self, feature_key: str, hint_data: Dict) -> None:
        """Show a feature discovery hint with detailed information"""
        with st.expander(f"✨ **New Feature Discovered: {hint_data['title']}**", expanded=True):
            st.markdown(f"**{hint_data['description']}**")
            
            if hint_data.get('benefits'):
                st.markdown("**🎯 Benefits:**")
                for benefit in hint_data['benefits']:
                    st.write(f"• {benefit}")
            
            if hint_data.get('how_to_enable'):
                st.info(f"**How to use:** {hint_data['how_to_enable']}")
            
            if st.button(f"✅ Got it!", key=f"dismiss_{feature_key}"):
                self._set_session_state(f'{feature_key}_discovered', True)
                st.rerun()
    
    def _mark_hint_shown(self, hint_key: str) -> None:
        """Mark a hint as shown to avoid repetition"""
        hints_shown = self._get_session_state('discovery_hints_shown', [])
        if hint_key not in hints_shown:
            hints_shown.append(hint_key)
            self._set_session_state('discovery_hints_shown', hints_shown)
    
    def render_smart_defaults_guide(self) -> None:
        """Render guide for smart defaults based on common use cases"""
        st.sidebar.markdown("---")
        st.sidebar.markdown("### 🎯 Smart Defaults")
        
        use_case = st.sidebar.selectbox(
            "Choose your use case:",
            [
                "General Analysis",
                "Security Review", 
                "Production Deployment",
                "Development Testing",
                "Multi-Cloud Migration",
                "Cost Optimization"
            ],
            help="Select your primary use case to apply smart default settings"
        )
        
        if st.sidebar.button("🔧 Apply Smart Defaults"):
            self._apply_smart_defaults(use_case)
            st.sidebar.success(f"✅ Applied defaults for: {use_case}")
    
    def _apply_smart_defaults(self, use_case: str) -> None:
        """Apply smart defaults based on selected use case"""
        if use_case == "Security Review":
            # Focus on security-related resources and high-risk changes
            self._set_session_state('risk_filter', ['High', 'Critical'])
            self._set_session_state('search_query', 'security|iam|policy|role|group')
            self._set_session_state('show_contextual_help', True)
            
        elif use_case == "Production Deployment":
            # Focus on high-risk changes and deletions
            self._set_session_state('risk_filter', ['Medium', 'High', 'Critical'])
            self._set_session_state('action_filter', ['delete', 'replace', 'update'])
            self._set_session_state('show_contextual_help', True)
            
        elif use_case == "Development Testing":
            # Show all changes, enable debug mode
            self._set_session_state('action_filter', ['create', 'update', 'delete', 'replace'])
            self._set_session_state('risk_filter', ['Low', 'Medium', 'High', 'Critical'])
            self._set_session_state('show_debug', True)
            
        elif use_case == "Multi-Cloud Migration":
            # Enable multi-cloud features, focus on cross-provider analysis
            self._set_session_state('enable_multi_cloud', True)
            self._set_session_state('show_contextual_help', True)
            
        elif use_case == "Cost Optimization":
            # Focus on resource types that impact cost
            self._set_session_state('search_query', 'instance|compute|storage|database|rds|ec2')
            self._set_session_state('action_filter', ['create', 'update', 'replace'])
            
        else:  # General Analysis
            # Balanced defaults for general use
            self._set_session_state('action_filter', ['create', 'update', 'delete', 'replace'])
            self._set_session_state('risk_filter', ['Low', 'Medium', 'High'])
            self._set_session_state('show_contextual_help', False)
    
    def render_guided_tour_controls(self) -> None:
        """Render controls for guided tour functionality"""
        if self._get_session_state('guided_tour_active', False):
            tour_step = self._get_session_state('tour_step', 1)
            
            with st.sidebar.container():
                st.markdown("---")
                st.markdown("### 🎯 Guided Tour")
                st.info(f"**Step {tour_step} of 5**")
                
                # Tour navigation
                col1, col2, col3 = st.sidebar.columns([1, 1, 1])
                
                with col1:
                    if tour_step > 1 and st.button("⬅️", help="Previous step"):
                        self._set_session_state('tour_step', tour_step - 1)
                        st.rerun()
                
                with col2:
                    if st.button("⏸️", help="Pause tour"):
                        self._set_session_state('guided_tour_active', False)
                        st.rerun()
                
                with col3:
                    if tour_step < 5 and st.button("➡️", help="Next step"):
                        self._set_session_state('tour_step', tour_step + 1)
                        st.rerun()
                    elif tour_step == 5 and st.button("✅", help="Complete tour"):
                        self._set_session_state('guided_tour_active', False)
                        self._set_session_state('tour_completed', True)
                        st.sidebar.success("🎉 Tour completed!")
                        st.rerun()
                
                # Show current step guidance
                self._show_tour_step_guidance(tour_step)
    
    def _show_tour_step_guidance(self, step: int) -> None:
        """Show guidance for current tour step"""
        guidance = {
            1: {
                'title': 'File Upload',
                'instruction': 'Upload your Terraform plan JSON file using the file uploader above.',
                'tip': 'Look for the dashed border upload area'
            },
            2: {
                'title': 'Summary Cards',
                'instruction': 'Review the summary cards showing change counts and risk levels.',
                'tip': 'Cards appear after successful file upload'
            },
            3: {
                'title': 'Visualizations',
                'instruction': 'Explore the interactive charts showing resource distributions.',
                'tip': 'Hover over chart elements for details'
            },
            4: {
                'title': 'Data Table',
                'instruction': 'Use the detailed table to filter and search specific resources.',
                'tip': 'Try the search box and filter controls'
            },
            5: {
                'title': 'Sidebar Controls',
                'instruction': 'Use sidebar filters to focus your analysis on specific criteria.',
                'tip': 'Experiment with different filter combinations'
            }
        }
        
        current = guidance.get(step, {})
        if current:
            st.sidebar.markdown(f"**{current['title']}**")
            st.sidebar.write(current['instruction'])
            if current.get('tip'):
                st.sidebar.caption(f"💡 {current['tip']}")
    
    def show_welcome_guide(self) -> None:
        """Show welcome guide for first-time users"""
        if not self._get_session_state('welcome_guide_dismissed', False):
            st.info("👋 **Welcome to the Terraform Plan Impact Dashboard!**")
            
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                st.markdown("""
                This dashboard helps you analyze Terraform plan changes before deployment.
                Get started by uploading a plan file or taking the interactive tutorial.
                """)
            
            with col2:
                if st.button("🎓 Start Tutorial"):
                    self._set_session_state('tutorial_step', 0)
                    st.rerun()
            
            with col3:
                if st.button("✕ Dismiss"):
                    self._set_session_state('welcome_guide_dismissed', True)
                    st.rerun()
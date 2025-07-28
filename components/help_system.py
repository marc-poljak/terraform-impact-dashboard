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
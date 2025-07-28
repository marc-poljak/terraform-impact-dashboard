"""
Onboarding Checklist Component

Provides a comprehensive onboarding checklist for new users with progress tracking
and contextual guidance throughout the dashboard experience.
"""

import streamlit as st
from typing import Dict, List, Optional, Any
from .base_component import BaseComponent


class OnboardingChecklistComponent(BaseComponent):
    """Component for comprehensive onboarding with progress tracking"""
    
    def __init__(self, session_manager: Optional[Any] = None):
        """
        Initialize the OnboardingChecklistComponent
        
        Args:
            session_manager: Optional session state manager
        """
        super().__init__(session_manager)
        self.checklist_items = self._define_checklist_items()
    
    def render(self, *args, **kwargs) -> Any:
        """
        Render the comprehensive onboarding checklist
        
        Returns:
            None - this component renders UI elements directly
        """
        if not self._get_session_state('onboarding_completed', False):
            self._render_main_checklist()
        else:
            self._render_advanced_features_discovery()
    
    def _define_checklist_items(self) -> List[Dict[str, Any]]:
        """Define the comprehensive onboarding checklist items"""
        return [
            {
                'id': 'welcome_acknowledged',
                'title': 'Welcome & Overview',
                'description': 'Understand what the dashboard does and how it helps',
                'action': 'Read the welcome message and dashboard overview',
                'help_text': 'The dashboard analyzes Terraform plan changes to help you understand deployment risks and impacts.',
                'category': 'getting_started'
            },
            {
                'id': 'file_format_understood',
                'title': 'File Format Requirements',
                'description': 'Learn how to generate compatible Terraform plan files',
                'action': 'Review file generation instructions',
                'help_text': 'You need a JSON file generated from your Terraform plan using specific commands.',
                'category': 'getting_started'
            },
            {
                'id': 'file_uploaded',
                'title': 'Upload First Plan File',
                'description': 'Successfully upload a Terraform plan JSON file',
                'action': 'Upload a plan file using the file uploader',
                'help_text': 'Try the sample data if you don\'t have a plan file ready.',
                'category': 'basic_usage'
            },
            {
                'id': 'summary_reviewed',
                'title': 'Review Summary Cards',
                'description': 'Understand the change summary and risk overview',
                'action': 'Examine the summary cards showing change counts and risk levels',
                'help_text': 'Summary cards provide a quick overview of your deployment changes.',
                'category': 'basic_usage'
            },
            {
                'id': 'charts_explored',
                'title': 'Explore Visualizations',
                'description': 'Interact with charts to understand resource patterns',
                'action': 'Hover over charts and explore interactive elements',
                'help_text': 'Charts show resource distributions and change patterns visually.',
                'category': 'basic_usage'
            },
            {
                'id': 'table_browsed',
                'title': 'Browse Data Table',
                'description': 'Explore detailed resource information in table format',
                'action': 'Scroll through the resource details table',
                'help_text': 'The table shows detailed information about each resource change.',
                'category': 'basic_usage'
            },
            {
                'id': 'filters_used',
                'title': 'Use Filtering Features',
                'description': 'Apply filters to focus on specific resources or risk levels',
                'action': 'Try different filter combinations in the sidebar',
                'help_text': 'Filters help you focus on specific types of changes or risk levels.',
                'category': 'advanced_usage'
            },
            {
                'id': 'search_tried',
                'title': 'Try Text Search',
                'description': 'Use text search to find specific resources',
                'action': 'Search for specific resource names or types',
                'help_text': 'Text search helps you quickly find specific resources in large plans.',
                'category': 'advanced_usage'
            },
            {
                'id': 'risk_assessment_understood',
                'title': 'Understand Risk Assessment',
                'description': 'Learn how risk levels are calculated and what they mean',
                'action': 'Review risk level explanations and tooltips',
                'help_text': 'Risk assessment helps you prioritize which changes need careful review.',
                'category': 'advanced_usage'
            },
            {
                'id': 'data_exported',
                'title': 'Export Data',
                'description': 'Download filtered results for external analysis',
                'action': 'Use the CSV download button to export data',
                'help_text': 'Exporting data allows you to analyze results in spreadsheet applications.',
                'category': 'advanced_usage'
            },
            {
                'id': 'help_system_explored',
                'title': 'Explore Help System',
                'description': 'Discover contextual help and guidance features',
                'action': 'Try the help topics and contextual tooltips',
                'help_text': 'The help system provides detailed guidance for all dashboard features.',
                'category': 'mastery'
            },
            {
                'id': 'advanced_features_discovered',
                'title': 'Discover Advanced Features',
                'description': 'Learn about multi-cloud analysis and enhanced features',
                'action': 'Explore enhanced features if available',
                'help_text': 'Advanced features provide deeper insights for complex deployments.',
                'category': 'mastery'
            }
        ]
    
    def _render_main_checklist(self) -> None:
        """Render the main onboarding checklist"""
        st.markdown("### 🎯 Getting Started Checklist")
        st.markdown("Complete these steps to master the Terraform Plan Impact Dashboard:")
        
        # Group items by category
        categories = {
            'getting_started': '🚀 Getting Started',
            'basic_usage': '📊 Basic Usage',
            'advanced_usage': '🔍 Advanced Features',
            'mastery': '🏆 Mastery'
        }
        
        total_completed = 0
        total_items = len(self.checklist_items)
        
        for category_id, category_name in categories.items():
            category_items = [item for item in self.checklist_items if item['category'] == category_id]
            if not category_items:
                continue
                
            with st.expander(f"{category_name} ({len(category_items)} items)", expanded=category_id == 'getting_started'):
                category_completed = 0
                
                for item in category_items:
                    is_completed = self._get_session_state(item['id'], False)
                    
                    col1, col2, col3 = st.columns([1, 4, 1])
                    
                    with col1:
                        if is_completed:
                            st.success("✅")
                            total_completed += 1
                            category_completed += 1
                        else:
                            st.info("⏳")
                    
                    with col2:
                        st.markdown(f"**{item['title']}**")
                        st.caption(item['description'])
                        
                        if not is_completed:
                            st.markdown(f"*{item['action']}*")
                            
                            # Show help text
                            if st.button(f"💡 Help", key=f"help_{item['id']}", help=item['help_text']):
                                st.info(item['help_text'])
                    
                    with col3:
                        if not is_completed and st.button("✓", key=f"mark_{item['id']}", help="Mark as completed"):
                            self._set_session_state(item['id'], True)
                            st.rerun()
                
                # Category progress
                category_progress = category_completed / len(category_items)
                st.progress(category_progress)
                st.caption(f"Category progress: {category_completed}/{len(category_items)} completed")
        
        # Overall progress
        st.markdown("---")
        overall_progress = total_completed / total_items
        st.progress(overall_progress)
        st.markdown(f"**Overall Progress: {total_completed}/{total_items} steps completed ({overall_progress:.0%})**")
        
        # Completion check
        if total_completed == total_items:
            st.balloons()
            st.success("🎉 **Congratulations!** You've completed the onboarding checklist!")
            
            if st.button("🏆 Mark Onboarding Complete", type="primary"):
                self._set_session_state('onboarding_completed', True)
                st.success("🎉 Onboarding completed! You're now a dashboard expert.")
                st.rerun()
        elif total_completed >= total_items * 0.8:  # 80% completion
            st.info("🌟 **Almost there!** You're nearly done with the onboarding process.")
        elif total_completed >= total_items * 0.5:  # 50% completion
            st.info("👍 **Great progress!** You're halfway through the onboarding checklist.")
    
    def _render_advanced_features_discovery(self) -> None:
        """Render advanced features discovery for completed users"""
        if st.button("🔄 Show Onboarding Checklist Again"):
            self._set_session_state('onboarding_completed', False)
            st.rerun()
        
        # Show advanced tips for experienced users
        with st.expander("🚀 **Advanced Tips for Power Users**", expanded=False):
            st.markdown("""
            **Keyboard Shortcuts:**
            - `Tab` / `Shift+Tab` - Navigate between elements
            - `Ctrl+F` - Focus search (when available)
            - `Enter` - Apply filters or activate buttons
            
            **Pro Tips:**
            - Use filter presets for common analysis patterns
            - Save custom filter configurations for reuse
            - Export data for advanced analysis in external tools
            - Enable debug mode for troubleshooting complex plans
            
            **Advanced Workflows:**
            - Compare multiple plan versions by opening in separate tabs
            - Use targeted Terraform plans for focused analysis
            - Combine dashboard insights with your CI/CD pipeline
            - Create custom reports for stakeholder communication
            """)
    
    def mark_item_completed(self, item_id: str) -> None:
        """
        Mark a specific checklist item as completed
        
        Args:
            item_id: ID of the checklist item to mark as completed
        """
        self._set_session_state(item_id, True)
    
    def is_item_completed(self, item_id: str) -> bool:
        """
        Check if a specific checklist item is completed
        
        Args:
            item_id: ID of the checklist item to check
            
        Returns:
            True if the item is completed, False otherwise
        """
        return self._get_session_state(item_id, False)
    
    def get_completion_percentage(self) -> float:
        """
        Get the overall completion percentage
        
        Returns:
            Completion percentage as a float between 0 and 1
        """
        completed_count = sum(1 for item in self.checklist_items if self.is_item_completed(item['id']))
        return completed_count / len(self.checklist_items) if self.checklist_items else 0.0
    
    def get_next_recommended_step(self) -> Optional[Dict[str, Any]]:
        """
        Get the next recommended step for the user
        
        Returns:
            Dictionary containing the next recommended step, or None if all completed
        """
        for item in self.checklist_items:
            if not self.is_item_completed(item['id']):
                return item
        return None
    
    def render_progress_indicator(self) -> None:
        """Render a compact progress indicator for the sidebar"""
        if not self._get_session_state('onboarding_completed', False):
            completion_percentage = self.get_completion_percentage()
            completed_count = int(completion_percentage * len(self.checklist_items))
            
            st.sidebar.markdown("### 🎯 Onboarding Progress")
            st.sidebar.progress(completion_percentage)
            st.sidebar.caption(f"{completed_count}/{len(self.checklist_items)} steps completed")
            
            # Show next step
            next_step = self.get_next_recommended_step()
            if next_step:
                st.sidebar.info(f"**Next:** {next_step['title']}")
                st.sidebar.caption(next_step['action'])
    
    def render_contextual_hints(self, context: str) -> None:
        """
        Render contextual hints based on current page context
        
        Args:
            context: Current context (e.g., 'file_upload', 'analysis', 'filtering')
        """
        context_hints = {
            'file_upload': {
                'relevant_items': ['file_format_understood', 'file_uploaded'],
                'hint': 'Upload a Terraform plan JSON file to begin your analysis'
            },
            'analysis': {
                'relevant_items': ['summary_reviewed', 'charts_explored', 'table_browsed'],
                'hint': 'Explore the analysis results to understand your deployment changes'
            },
            'filtering': {
                'relevant_items': ['filters_used', 'search_tried'],
                'hint': 'Use filters and search to focus on specific resources or risk levels'
            },
            'export': {
                'relevant_items': ['data_exported'],
                'hint': 'Export your filtered results for further analysis'
            }
        }
        
        if context in context_hints:
            hint_data = context_hints[context]
            
            # Check if any relevant items are incomplete
            incomplete_items = [
                item_id for item_id in hint_data['relevant_items'] 
                if not self.is_item_completed(item_id)
            ]
            
            if incomplete_items and not self._get_session_state('onboarding_completed', False):
                st.info(f"💡 **Onboarding Tip:** {hint_data['hint']}")
"""
Help System Component

Provides comprehensive contextual help and onboarding for the Terraform Plan Impact Dashboard.
"""

import streamlit as st
import time
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
        
        # Quick help toggle with enhanced accessibility
        show_help = st.sidebar.checkbox(
            "💡 Show Contextual Help",
            value=self._get_session_state('show_contextual_help', False),
            help="Enable to see helpful tooltips and guidance throughout the dashboard. Use Tab to navigate between help elements."
        )
        
        if show_help:
            st.sidebar.success("💡 Contextual help enabled")
            self._set_session_state('show_contextual_help', True)
            
            # Show keyboard shortcuts when help is enabled
            with st.sidebar.expander("⌨️ Keyboard Shortcuts", expanded=False):
                st.markdown("""
                **Navigation:**
                - `Tab` / `Shift+Tab` - Navigate between elements
                - `Enter` / `Space` - Activate buttons and checkboxes
                - `Escape` - Close modals and expandable sections
                
                **Search & Filtering:**
                - `Ctrl+F` / `Cmd+F` - Focus search box (when available)
                - `Ctrl+Enter` - Apply filters
                - `Ctrl+R` - Reset all filters
                
                **Data Table:**
                - `Arrow Keys` - Navigate table cells
                - `Page Up/Down` - Scroll through large tables
                - `Ctrl+A` - Select all (for export)
                
                **Accessibility:**
                - Screen reader compatible
                - High contrast mode supported
                - Keyboard-only navigation available
                """)
        else:
            self._set_session_state('show_contextual_help', False)
        
        # Enhanced help topics dropdown with accessibility
        help_topics = [
            "Getting Started",
            "File Upload Guide", 
            "Understanding Risk Levels",
            "Using Filters",
            "Reading Visualizations",
            "Multi-Cloud Features",
            "Accessibility Features",
            "Keyboard Shortcuts",
            "Troubleshooting"
        ]
        
        selected_topic = st.sidebar.selectbox(
            "📖 Help Topics",
            options=["Select a topic..."] + help_topics,
            help="Choose a topic to get detailed help information. Use arrow keys to navigate options."
        )
        
        if selected_topic != "Select a topic...":
            self.show_help_topic(selected_topic)
        
        # Quick actions
        st.sidebar.markdown("#### 🚀 Quick Actions")
        
        col1, col2 = st.sidebar.columns(2)
        
        with col1:
            if st.button("🎯 Tour", help="Take a guided tour of the dashboard"):
                self._set_session_state('show_tour_setup', True)
                st.rerun()
        
        with col2:
            if st.button("❓ FAQ", help="View frequently asked questions"):
                self.show_faq()
        
        # Accessibility documentation button
        if st.sidebar.button("♿ Accessibility Guide", help="View comprehensive accessibility documentation"):
            self._set_session_state('show_accessibility_docs', True)
            st.rerun()
        
        # Show tour setup if requested
        if self._get_session_state('show_tour_setup', False):
            self.show_tour_setup()
        
        # Feature announcement center
        self.render_feature_announcement_center()
        
        # Bookmarked features
        self.render_bookmarked_features()
    
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
    
    def render_expandable_help_section(self, section_title: str, help_content: Dict, 
                                     expanded: bool = False, show_tips: bool = True) -> None:
        """
        Render an expandable help section for complex features
        
        Args:
            section_title: Title of the help section
            help_content: Dictionary containing help content (summary, content, tips)
            expanded: Whether the section should be expanded by default
            show_tips: Whether to show tips section
        """
        with st.expander(f"❓ **{section_title}**", expanded=expanded):
            if help_content.get('summary'):
                st.markdown(f"**Overview:** {help_content['summary']}")
                st.markdown("---")
            
            if help_content.get('content'):
                st.markdown(help_content['content'])
            
            if show_tips and help_content.get('tips'):
                st.markdown("---")
                st.markdown("**💡 Pro Tips:**")
                for tip in help_content['tips']:
                    st.write(f"• {tip}")
            
            # Add accessibility note for complex features
            if section_title.lower() in ['visualizations', 'data table', 'filters']:
                st.markdown("---")
                st.caption("♿ **Accessibility:** This feature is fully keyboard navigable and screen reader compatible.")
    
    def render_contextual_help_panel(self, feature_area: str) -> None:
        """
        Render a contextual help panel for specific feature areas
        
        Args:
            feature_area: The feature area to show help for (e.g., 'upload', 'analysis', 'filters')
        """
        if not self._get_session_state('show_contextual_help', False):
            return
        
        help_panels = {
            'upload': {
                'title': 'File Upload Help',
                'content': """
                **Supported Formats:**
                • JSON files from `terraform show -json plan.tfplan`
                • Maximum file size: 200MB
                • UTF-8 encoding required
                
                **Common Issues:**
                • Invalid JSON format - validate your file first
                • Missing resource_changes array - ensure plan was generated correctly
                • Large files - may take longer to process
                
                **Accessibility:**
                • Drag-and-drop or click to browse
                • Screen reader announces upload progress
                • Keyboard accessible file selection
                """,
                'shortcuts': [
                    "Tab to file upload area",
                    "Enter to open file browser",
                    "Escape to cancel upload"
                ]
            },
            'analysis': {
                'title': 'Analysis Results Help',
                'content': """
                **Understanding Results:**
                • Summary cards show change counts and risk levels
                • Visualizations reveal patterns in your changes
                • Data table provides detailed resource information
                
                **Risk Assessment:**
                • Low (0-30): Safe changes with minimal impact
                • Medium (31-70): Changes requiring attention
                • High (71-90): Potentially dangerous changes
                • Critical (91-100): High risk of disruption
                
                **Accessibility:**
                • All charts have text alternatives
                • Tables include proper headers
                • Screen reader announces important changes
                """,
                'shortcuts': [
                    "Tab through summary cards",
                    "Arrow keys in data table",
                    "Enter to expand chart details"
                ]
            },
            'filters': {
                'title': 'Filtering and Search Help',
                'content': """
                **Filter Types:**
                • Action filters: Focus on create/update/delete operations
                • Risk filters: Show only specific risk levels
                • Provider filters: Multi-cloud analysis (when available)
                • Text search: Find resources by name or type
                
                **Combining Filters:**
                • Multiple filters work together (AND logic)
                • Search works across all visible columns
                • Filters apply to visualizations and exports
                
                **Accessibility:**
                • All filter controls are keyboard accessible
                • Screen reader announces filter changes
                • Clear visual focus indicators
                """,
                'shortcuts': [
                    "Ctrl+F to focus search",
                    "Ctrl+R to reset filters",
                    "Tab between filter controls"
                ]
            }
        }
        
        panel_data = help_panels.get(feature_area)
        if panel_data:
            with st.container():
                st.markdown(f"### 💡 {panel_data['title']}")
                st.markdown(panel_data['content'])
                
                if panel_data.get('shortcuts'):
                    with st.expander("⌨️ Keyboard Shortcuts", expanded=False):
                        for shortcut in panel_data['shortcuts']:
                            st.write(f"• {shortcut}")
                
                st.markdown("---")
    
    def show_tour_setup(self) -> None:
        """Show guided tour setup and configuration"""
        st.sidebar.info("🎯 **Configure Your Guided Tour**")
        
        # Tour type selection
        tour_type = st.sidebar.radio(
            "Choose your tour type:",
            [
                "🚀 Quick Tour (5 minutes)",
                "📚 Comprehensive Tour (15 minutes)",
                "🎯 Feature-Focused Tour"
            ],
            help="Select the type of tour that best fits your needs"
        )
        
        if tour_type == "🚀 Quick Tour (5 minutes)":
            self._set_session_state('tour_type', 'quick')
            tour_steps = [
                "📁 File Upload",
                "📊 Summary Overview", 
                "📈 Key Visualizations",
                "🔍 Basic Filtering",
                "📋 Results Review"
            ]
        elif tour_type == "📚 Comprehensive Tour (15 minutes)":
            self._set_session_state('tour_type', 'comprehensive')
            tour_steps = [
                "📁 File Upload & Validation",
                "📊 Summary Cards Deep Dive",
                "📈 Interactive Visualizations",
                "🔍 Advanced Filtering",
                "📋 Data Table Features",
                "🔒 Security Analysis",
                "📄 Report Generation",
                "⚙️ Settings & Preferences"
            ]
        else:  # Feature-Focused Tour
            self._set_session_state('tour_type', 'feature_focused')
            
            # Let user choose which features to focus on
            focus_features = st.sidebar.multiselect(
                "Select features to explore:",
                [
                    "Multi-Cloud Analysis",
                    "Security Features",
                    "Advanced Filtering",
                    "Report Generation",
                    "Accessibility Features"
                ],
                default=["Multi-Cloud Analysis", "Advanced Filtering"]
            )
            
            self._set_session_state('tour_focus_features', focus_features)
            tour_steps = [f"✨ {feature}" for feature in focus_features]
        
        st.sidebar.markdown(f"""
        **Your {tour_type.split()[1]} tour includes:**
        """)
        
        for i, step in enumerate(tour_steps, 1):
            st.sidebar.write(f"{i}. {step}")
        
        st.sidebar.markdown("""
        **Interactive Tour Features:**
        • 🎮 Hands-on demonstrations
        • 💡 Contextual tips and tricks
        • ⌨️ Keyboard shortcuts training
        • 🎯 Personalized recommendations
        • 📝 Progress tracking
        """)
        
        # Add start tour button
        col1, col2 = st.sidebar.columns([1, 1])
        
        with col1:
            if st.button("🚀 Start Tour", type="primary", help="Begin the interactive guided tour"):
                # Set tour state and hide setup
                self._set_session_state('show_tour_setup', False)
                self._set_session_state('guided_tour_active', True)
                self._set_session_state('tour_step', 1)
                self._set_session_state('tour_steps', tour_steps)
                self._set_session_state('tour_start_time', time.time())
                st.rerun()
        
        with col2:
            if st.button("❌ Cancel", help="Cancel tour setup"):
                # Reset tour setup state
                self._set_session_state('show_tour_setup', False)
                self._set_session_state('guided_tour_active', False)
                st.rerun()
    
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
                                is_new: bool = True, priority: str = "normal",
                                demo_available: bool = False, learn_more_url: str = None) -> None:
        """
        Show enhanced announcement for new or updated features
        
        Args:
            feature_name: Name of the feature
            description: Description of the feature
            is_new: Whether this is a new feature
            priority: Priority level (low, normal, high, critical)
            demo_available: Whether a demo is available
            learn_more_url: URL for additional information
        """
        announcement_key = f"announcement_{feature_name.lower().replace(' ', '_')}"
        
        if not self._get_session_state(f"{announcement_key}_dismissed", False):
            icon = "🆕" if is_new else "🔄"
            status = "New" if is_new else "Updated"
            
            # Choose announcement style based on priority
            if priority == "critical":
                announcement_func = st.error
                priority_icon = "🚨"
            elif priority == "high":
                announcement_func = st.warning
                priority_icon = "⚠️"
            elif priority == "low":
                announcement_func = st.info
                priority_icon = "ℹ️"
            else:  # normal
                announcement_func = st.success
                priority_icon = "✨"
            
            with st.container():
                col1, col2 = st.columns([5, 1])
                
                with col1:
                    announcement_func(f"{priority_icon} {icon} **{status} Feature: {feature_name}** - {description}")
                
                with col2:
                    if st.button("✕", key=f"dismiss_{announcement_key}", help="Dismiss this announcement"):
                        self._set_session_state(f"{announcement_key}_dismissed", True)
                        st.rerun()
                
                # Action buttons if available
                if demo_available or learn_more_url:
                    action_cols = st.columns([1, 1, 1, 2])
                    
                    if demo_available:
                        with action_cols[0]:
                            if st.button("🎮 Try Demo", key=f"demo_btn_{announcement_key}"):
                                self._start_feature_demo(feature_name.lower().replace(' ', '_'))
                    
                    if learn_more_url:
                        with action_cols[1]:
                            st.markdown(f"[📖 Learn More]({learn_more_url})")
                    
                    with action_cols[2]:
                        if st.button("🔖 Bookmark", key=f"bookmark_{announcement_key}"):
                            self._bookmark_feature(feature_name)
                            st.success("Feature bookmarked!")
    
    def render_feature_announcement_center(self) -> None:
        """Render a comprehensive feature announcement center"""
        if st.sidebar.button("📢 Feature Updates", help="View latest feature announcements and updates"):
            self._set_session_state('show_announcement_center', True)
            st.rerun()
        
        if self._get_session_state('show_announcement_center', False):
            with st.expander("📢 **Feature Announcement Center**", expanded=True):
                st.markdown("### 🆕 Latest Updates")
                
                # Sample announcements - in a real app, these would come from a data source
                announcements = [
                    {
                        'name': 'Enhanced Accessibility',
                        'description': 'Full keyboard navigation and screen reader support',
                        'is_new': True,
                        'priority': 'high',
                        'demo_available': True,
                        'date': '2024-01-15'
                    },
                    {
                        'name': 'Interactive Feature Discovery',
                        'description': 'Discover features as you use the dashboard',
                        'is_new': True,
                        'priority': 'normal',
                        'demo_available': True,
                        'date': '2024-01-10'
                    },
                    {
                        'name': 'Smart Defaults',
                        'description': 'Optimized settings based on your use case',
                        'is_new': False,
                        'priority': 'normal',
                        'demo_available': False,
                        'date': '2024-01-05'
                    }
                ]
                
                for announcement in announcements:
                    with st.container():
                        col1, col2 = st.columns([4, 1])
                        
                        with col1:
                            icon = "🆕" if announcement['is_new'] else "🔄"
                            st.markdown(f"{icon} **{announcement['name']}** - {announcement['description']}")
                            st.caption(f"📅 {announcement['date']}")
                        
                        with col2:
                            if announcement['demo_available']:
                                if st.button("🎮 Demo", key=f"demo_{announcement['name'].replace(' ', '_')}"):
                                    self._start_feature_demo(announcement['name'].lower().replace(' ', '_'))
                        
                        st.markdown("---")
                
                # Close button
                if st.button("✅ Close Announcement Center"):
                    self._set_session_state('show_announcement_center', False)
                    st.rerun()
    
    def _bookmark_feature(self, feature_name: str) -> None:
        """Bookmark a feature for later reference"""
        bookmarks = self._get_session_state('bookmarked_features', [])
        if feature_name not in bookmarks:
            bookmarks.append(feature_name)
            self._set_session_state('bookmarked_features', bookmarks)
    
    def render_bookmarked_features(self) -> None:
        """Render bookmarked features section"""
        bookmarks = self._get_session_state('bookmarked_features', [])
        
        if bookmarks:
            with st.sidebar.expander("🔖 **Bookmarked Features**", expanded=False):
                for feature in bookmarks:
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.write(f"• {feature}")
                    
                    with col2:
                        if st.button("🗑️", key=f"remove_bookmark_{feature.replace(' ', '_')}", help="Remove bookmark"):
                            bookmarks.remove(feature)
                            self._set_session_state('bookmarked_features', bookmarks)
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
                
                **Accessibility Note:** This dashboard is fully keyboard navigable and screen reader compatible.
                """,
                'tips': [
                    "Start with small plans to get familiar with the interface",
                    "Enable debug mode if you encounter issues",
                    "Use the sidebar filters to focus your analysis",
                    "Enable contextual help for additional guidance throughout the interface"
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
            'accessibility_features': {
                'summary': 'Accessibility and inclusive design features',
                'content': """
                **Screen Reader Support:**
                • All interactive elements have proper labels
                • Tables include headers and descriptions
                • Charts provide text alternatives
                • Status messages are announced
                
                **Keyboard Navigation:**
                • Full keyboard accessibility
                • Logical tab order throughout interface
                • Skip links for main content areas
                • Focus indicators on all interactive elements
                
                **Visual Accessibility:**
                • High contrast color schemes
                • Scalable text and interface elements
                • Color is not the only way information is conveyed
                • Sufficient color contrast ratios (WCAG AA compliant)
                
                **Motor Accessibility:**
                • Large click targets (minimum 44px)
                • No time-based interactions required
                • Drag and drop alternatives available
                • Hover states don't hide essential information
                """,
                'tips': [
                    "Use Tab and Shift+Tab to navigate between elements",
                    "Press Enter or Space to activate buttons and checkboxes",
                    "Use arrow keys to navigate within components like tables",
                    "Screen readers will announce all important status changes"
                ]
            },
            'keyboard_shortcuts': {
                'summary': 'Complete keyboard shortcuts reference',
                'content': """
                **Global Navigation:**
                • `Tab` - Move to next interactive element
                • `Shift+Tab` - Move to previous interactive element
                • `Enter` - Activate buttons, links, and checkboxes
                • `Space` - Toggle checkboxes and buttons
                • `Escape` - Close modals, dropdowns, and expandable sections
                
                **Search and Filtering:**
                • `Ctrl+F` (Windows) / `Cmd+F` (Mac) - Focus search box
                • `Ctrl+Enter` - Apply current filter settings
                • `Ctrl+R` - Reset all filters to default
                • `Alt+C` - Clear current search
                
                **Data Table Navigation:**
                • `Arrow Keys` - Navigate between table cells
                • `Page Up/Down` - Scroll through large tables
                • `Home/End` - Jump to first/last row
                • `Ctrl+A` - Select all rows (for export)
                
                **Help System:**
                • `F1` - Open help sidebar
                • `Ctrl+H` - Toggle contextual help
                • `Ctrl+?` - Show this shortcuts reference
                
                **Accessibility:**
                • `Alt+1` - Skip to main content
                • `Alt+2` - Skip to navigation
                • `Alt+3` - Skip to search
                """,
                'tips': [
                    "Most shortcuts work in combination with standard browser shortcuts",
                    "Screen readers will announce shortcut availability",
                    "Shortcuts are designed to not conflict with browser defaults",
                    "Custom shortcuts can be disabled in browser settings if needed"
                ]
            },
            'tooltips': {
                'file_upload_general': {
                    'text': 'Upload your Terraform plan JSON file to begin analysis. Supports drag-and-drop or click to browse.'
                },
                'risk_assessment_general': {
                    'text': 'Risk levels help you understand the potential impact of your changes. Higher risk requires more careful review.'
                },
                'filters_general': {
                    'text': 'Use filters to focus on specific resources or change types. Multiple filters can be combined.'
                },
                'visualizations_general': {
                    'text': 'Interactive charts show patterns in your infrastructure changes. Hover for details, click legend to filter.'
                },
                'data_table_general': {
                    'text': 'Detailed resource information with sorting, filtering, and export capabilities. Use keyboard navigation for accessibility.'
                },
                'sidebar_controls_general': {
                    'text': 'Main dashboard controls and settings. All controls are keyboard accessible and screen reader compatible.'
                },
                'summary_cards_general': {
                    'text': 'Quick overview of changes and risk metrics. Cards update automatically when filters are applied.'
                },
                'enhanced_features_general': {
                    'text': 'Advanced multi-cloud analysis features. Requires additional dependencies for full functionality.'
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
        """Render enhanced interactive feature discovery hints"""
        # Show hints based on current context and user progress
        hints_shown = self._get_session_state('discovery_hints_shown', [])
        
        # Feature discovery section in sidebar
        st.sidebar.markdown("---")
        st.sidebar.markdown("### ✨ Discover Features")
        
        # Interactive feature discovery mode
        discovery_mode = st.sidebar.checkbox(
            "🔍 Interactive Discovery Mode",
            value=self._get_session_state('discovery_mode_active', False),
            help="Enable to see contextual feature hints and suggestions as you use the dashboard"
        )
        
        if discovery_mode:
            self._set_session_state('discovery_mode_active', True)
            st.sidebar.success("🔍 Discovery mode active")
            
            # Show progressive feature hints
            self._show_progressive_feature_hints()
        else:
            self._set_session_state('discovery_mode_active', False)
        
        # Feature spotlight section
        self._render_feature_spotlight()
        
        # Quick discovery buttons for major features
        st.sidebar.markdown("**🚀 Quick Discovery:**")
        
        col1, col2 = st.sidebar.columns(2)
        
        with col1:
            # Hint about multi-cloud features
            if 'multi_cloud_hint' not in hints_shown and not self._get_session_state('multi_cloud_discovered', False):
                if st.button("☁️ Multi-Cloud", help="Discover multi-cloud analysis features"):
                    self._show_discovery_hint('multi_cloud', {
                        'title': 'Multi-Cloud Analysis',
                        'description': 'Analyze Terraform plans that span multiple cloud providers (AWS, Azure, GCP)',
                        'benefits': [
                            'Cross-provider risk assessment',
                            'Provider-specific recommendations',
                            'Multi-cloud security insights',
                            'Resource distribution across clouds'
                        ],
                        'how_to_enable': 'Enable "Multi-cloud features" in the sidebar when analyzing plans with multiple providers',
                        'demo_available': True
                    })
                    self._mark_hint_shown('multi_cloud_hint')
                    self._set_session_state('multi_cloud_discovered', True)
        
        with col2:
            # Hint about advanced filtering
            if 'advanced_filtering_hint' not in hints_shown and not self._get_session_state('advanced_filtering_discovered', False):
                if st.button("🔍 Filtering", help="Discover advanced filtering capabilities"):
                    self._show_discovery_hint('advanced_filtering', {
                        'title': 'Advanced Filtering & Search',
                        'description': 'Powerful filtering capabilities to focus your analysis',
                        'benefits': [
                            'Text search across resource names and types',
                            'Combine multiple filter criteria',
                            'Save and reuse filter configurations',
                            'Export filtered results'
                        ],
                        'how_to_enable': 'Use the filter controls in the sidebar and try the search box in the data table',
                        'demo_available': True
                    })
                    self._mark_hint_shown('advanced_filtering_hint')
                    self._set_session_state('advanced_filtering_discovered', True)
        
        # Additional discovery buttons in a new row
        col3, col4 = st.sidebar.columns(2)
        
        with col3:
            # Hint about report generation
            if 'report_generation_hint' not in hints_shown and not self._get_session_state('report_generation_discovered', False):
                if st.button("📄 Reports", help="Discover report generation features"):
                    self._show_discovery_hint('report_generation', {
                        'title': 'Comprehensive Report Generation',
                        'description': 'Generate detailed reports for stakeholders and documentation',
                        'benefits': [
                            'Executive summary with key metrics',
                            'Risk analysis and recommendations',
                            'Visual charts and graphs included',
                            'PDF and HTML export formats'
                        ],
                        'how_to_enable': 'Look for the "Generate Report" section after uploading a plan file',
                        'demo_available': True
                    })
                    self._mark_hint_shown('report_generation_hint')
                    self._set_session_state('report_generation_discovered', True)
        
        with col4:
            # Hint about security analysis
            if 'security_analysis_hint' not in hints_shown and not self._get_session_state('security_analysis_discovered', False):
                if st.button("🔒 Security", help="Discover security analysis features"):
                    self._show_discovery_hint('security_analysis', {
                        'title': 'Enhanced Security Analysis',
                        'description': 'Comprehensive security-focused analysis of your infrastructure changes',
                        'benefits': [
                            'Security-related resource highlighting',
                            'Compliance framework checks',
                            'Security risk scoring',
                            'Best practice recommendations'
                        ],
                        'how_to_enable': 'Security analysis runs automatically when you upload a plan file',
                        'demo_available': True
                    })
                    self._mark_hint_shown('security_analysis_hint')
                    self._set_session_state('security_analysis_discovered', True)
    
    def _show_discovery_hint(self, feature_key: str, hint_data: Dict) -> None:
        """Show an enhanced feature discovery hint with detailed information"""
        with st.expander(f"✨ **New Feature Discovered: {hint_data['title']}**", expanded=True):
            st.markdown(f"**{hint_data['description']}**")
            
            if hint_data.get('benefits'):
                st.markdown("**🎯 Benefits:**")
                for benefit in hint_data['benefits']:
                    st.write(f"• {benefit}")
            
            if hint_data.get('how_to_enable'):
                st.info(f"**How to use:** {hint_data['how_to_enable']}")
            
            # Interactive demo button if available
            if hint_data.get('demo_available'):
                col1, col2, col3 = st.columns([1, 1, 1])
                
                with col1:
                    if st.button(f"🎮 Try Demo", key=f"demo_{feature_key}"):
                        self._start_feature_demo(feature_key)
                
                with col2:
                    if st.button(f"📖 Learn More", key=f"learn_{feature_key}"):
                        self._show_detailed_feature_guide(feature_key)
                
                with col3:
                    if st.button(f"✅ Got it!", key=f"dismiss_{feature_key}"):
                        self._set_session_state(f'{feature_key}_discovered', True)
                        st.rerun()
            else:
                if st.button(f"✅ Got it!", key=f"dismiss_{feature_key}"):
                    self._set_session_state(f'{feature_key}_discovered', True)
                    st.rerun()
    
    def _show_progressive_feature_hints(self) -> None:
        """Show progressive feature hints based on user progress"""
        user_progress = self._get_session_state('user_progress', {})
        
        # Show hints based on what the user has accomplished
        if user_progress.get('file_uploaded') and not user_progress.get('filters_used'):
            st.sidebar.info("💡 **Next:** Try using the filters to focus your analysis!")
            
        elif user_progress.get('filters_used') and not user_progress.get('charts_explored'):
            st.sidebar.info("💡 **Next:** Explore the interactive charts for visual insights!")
            
        elif user_progress.get('charts_explored') and not user_progress.get('report_generated'):
            st.sidebar.info("💡 **Next:** Generate a comprehensive report for stakeholders!")
    
    def _render_feature_spotlight(self) -> None:
        """Render a rotating feature spotlight"""
        import time
        import random
        
        # Rotate featured feature daily
        day_of_year = int(time.strftime("%j"))
        
        features = [
            {
                'name': 'Smart Defaults',
                'icon': '🎯',
                'description': 'Apply optimized settings based on your use case',
                'action': 'Try the Smart Defaults section below'
            },
            {
                'name': 'Keyboard Navigation',
                'icon': '⌨️',
                'description': 'Navigate the entire dashboard using only your keyboard',
                'action': 'Press Tab to start navigating'
            },
            {
                'name': 'Export Capabilities',
                'icon': '📊',
                'description': 'Export your analysis data in multiple formats',
                'action': 'Look for export buttons in the data table'
            },
            {
                'name': 'Debug Mode',
                'icon': '🔍',
                'description': 'Get detailed insights into plan processing',
                'action': 'Enable debug mode in the sidebar'
            }
        ]
        
        featured_feature = features[day_of_year % len(features)]
        
        with st.sidebar.expander(f"🌟 **Feature Spotlight: {featured_feature['name']}**", expanded=False):
            st.markdown(f"{featured_feature['icon']} {featured_feature['description']}")
            st.caption(f"💡 {featured_feature['action']}")
    
    def _start_feature_demo(self, feature_key: str) -> None:
        """Start an interactive demo for a specific feature"""
        self._set_session_state(f'demo_active_{feature_key}', True)
        self._set_session_state('demo_step', 1)
        
        demo_messages = {
            'multi_cloud': "🎮 **Multi-Cloud Demo Started!** Upload a plan with multiple providers to see cross-cloud analysis.",
            'advanced_filtering': "🎮 **Filtering Demo Started!** Try combining different filters in the sidebar.",
            'report_generation': "🎮 **Report Demo Started!** Upload a plan file to see report generation options.",
            'security_analysis': "🎮 **Security Demo Started!** Upload a plan to see security-focused analysis."
        }
        
        st.sidebar.success(demo_messages.get(feature_key, "🎮 **Demo Started!**"))
    
    def _show_detailed_feature_guide(self, feature_key: str) -> None:
        """Show detailed guide for a specific feature"""
        self._set_session_state(f'show_guide_{feature_key}', True)
        
        guides = {
            'multi_cloud': 'multi_cloud_features',
            'advanced_filtering': 'using_filters',
            'report_generation': 'understanding_risk_levels',
            'security_analysis': 'getting_started'
        }
        
        guide_topic = guides.get(feature_key, 'getting_started')
        self.show_help_topic(guide_topic.replace('_', ' ').title())
    
    def _mark_hint_shown(self, hint_key: str) -> None:
        """Mark a hint as shown to avoid repetition"""
        hints_shown = self._get_session_state('discovery_hints_shown', [])
        if hint_key not in hints_shown:
            hints_shown.append(hint_key)
            self._set_session_state('discovery_hints_shown', hints_shown)
    
    def render_accessibility_documentation(self) -> None:
        """Render comprehensive accessibility documentation"""
        st.markdown("## ♿ Accessibility Documentation")
        
        # Overview section
        st.markdown("""
        The Terraform Plan Impact Dashboard is designed to be fully accessible to users with disabilities.
        We follow WCAG 2.1 AA guidelines and provide multiple ways to interact with the interface.
        """)
        
        # Keyboard navigation section
        with st.expander("⌨️ **Keyboard Navigation**", expanded=True):
            st.markdown("""
            **Basic Navigation:**
            - `Tab` - Move forward through interactive elements
            - `Shift+Tab` - Move backward through interactive elements
            - `Enter` - Activate buttons and links
            - `Space` - Toggle checkboxes and activate buttons
            - `Escape` - Close modals, dropdowns, and expandable sections
            
            **Skip Links:**
            - `Alt+1` - Skip to main content
            - `Alt+2` - Skip to sidebar navigation
            - `Alt+3` - Skip to search functionality
            
            **Data Table Navigation:**
            - `Arrow Keys` - Navigate between table cells
            - `Page Up/Down` - Scroll through large tables
            - `Home/End` - Jump to first/last row
            - `Ctrl+A` - Select all (for export operations)
            
            **Search and Filtering:**
            - `Ctrl+F` (Windows) / `Cmd+F` (Mac) - Focus search box
            - `Ctrl+Enter` - Apply current filter settings
            - `Ctrl+R` - Reset all filters
            """)
        
        # Screen reader section
        with st.expander("🔊 **Screen Reader Support**", expanded=False):
            st.markdown("""
            **Compatibility:**
            - NVDA (Windows) - Fully supported
            - JAWS (Windows) - Fully supported
            - VoiceOver (macOS) - Fully supported
            - Orca (Linux) - Supported
            
            **Features:**
            - All interactive elements have descriptive labels
            - Tables include proper headers and captions
            - Charts provide text alternatives and data tables
            - Status changes are announced automatically
            - Progress indicators are announced
            
            **Navigation Landmarks:**
            - Main content area clearly marked
            - Sidebar navigation properly labeled
            - Search functionality identified
            - Help sections clearly structured
            """)
        
        # Visual accessibility section
        with st.expander("👁️ **Visual Accessibility**", expanded=False):
            st.markdown("""
            **Color and Contrast:**
            - High contrast color schemes available
            - Color contrast ratios meet WCAG AA standards (4.5:1 minimum)
            - Information is not conveyed by color alone
            - Risk levels use both color and text indicators
            
            **Text and Layout:**
            - Text can be scaled up to 200% without loss of functionality
            - Responsive design adapts to different screen sizes
            - Clear visual hierarchy with proper heading structure
            - Sufficient spacing between interactive elements
            
            **Focus Indicators:**
            - Clear focus indicators on all interactive elements
            - Focus order follows logical reading sequence
            - Focus is never trapped or lost
            """)
        
        # Motor accessibility section
        with st.expander("🖱️ **Motor Accessibility**", expanded=False):
            st.markdown("""
            **Click Targets:**
            - All interactive elements are at least 44px in size
            - Adequate spacing between clickable elements
            - No precision clicking required
            
            **Interaction Methods:**
            - Full keyboard alternatives to mouse interactions
            - No time-based interactions required
            - Drag-and-drop has keyboard alternatives
            - Hover information is also available on focus
            
            **Error Prevention:**
            - Clear error messages with suggestions
            - Confirmation dialogs for destructive actions
            - Undo functionality where appropriate
            """)
        
        # Cognitive accessibility section
        with st.expander("🧠 **Cognitive Accessibility**", expanded=False):
            st.markdown("""
            **Clear Interface:**
            - Consistent navigation and layout
            - Clear, simple language in all text
            - Logical information hierarchy
            - Contextual help available throughout
            
            **Error Handling:**
            - Clear, actionable error messages
            - Suggestions for fixing problems
            - No jargon or technical terms without explanation
            
            **User Control:**
            - Users can control timing of interactions
            - Auto-updating content can be paused
            - Multiple ways to complete tasks
            - Progress indicators for long operations
            """)
        
        # Getting help section
        st.markdown("---")
        st.markdown("### 🆘 Getting Accessibility Help")
        st.markdown("""
        If you encounter accessibility barriers or need assistance:
        
        1. **Enable contextual help** in the sidebar for additional guidance
        2. **Use the help topics** dropdown for specific feature assistance
        3. **Try the interactive tutorial** for guided learning
        4. **Check the troubleshooting section** for common issues
        
        **Feedback:** We continuously improve accessibility. Your feedback helps us identify and fix barriers.
        """)
    
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
        # Regular guided tour
        if self._get_session_state('guided_tour_active', False):
            tour_steps = self._get_session_state('tour_steps', [])
            tour_step = self._get_session_state('tour_step', 1)
            
            with st.sidebar.container():
                st.markdown("---")
                st.markdown("### 🎯 Guided Tour")
                st.info(f"**Step {tour_step} of {len(tour_steps)}**")
                
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
                    if tour_step < len(tour_steps) and st.button("➡️", help="Next step"):
                        self._set_session_state('tour_step', tour_step + 1)
                        st.rerun()
                    elif tour_step == len(tour_steps) and st.button("✅", help="Complete tour"):
                        self._set_session_state('guided_tour_active', False)
                        self._set_session_state('tour_completed', True)
                        st.sidebar.success("🎉 Tour completed!")
                        st.rerun()
                
                # Show current step guidance
                self._show_tour_step_guidance(tour_step)
        
        # Workflow-specific guided tours
        self.render_workflow_tour_controls()
        
        # Workflow tour launcher
        if not self._get_session_state('guided_tour_active', False) and not self._get_session_state('workflow_tour_active', False):
            st.sidebar.markdown("---")
            st.sidebar.markdown("### 🎯 Workflow Tours")
            
            workflow_tour = st.sidebar.selectbox(
                "Choose a workflow tour:",
                [
                    "Select a workflow...",
                    "Security Review Workflow",
                    "Production Deployment Workflow", 
                    "Multi-Cloud Analysis Workflow"
                ],
                help="Select a specific workflow to get guided step-by-step instructions"
            )
            
            if workflow_tour != "Select a workflow...":
                workflow_key = workflow_tour.lower().replace(' workflow', '').replace(' ', '_')
                
                if st.sidebar.button(f"🚀 Start {workflow_tour}"):
                    self.create_workflow_guided_tour(workflow_key)
                    st.rerun()
    
    def create_workflow_guided_tour(self, workflow_name: str) -> None:
        """Create a guided tour for specific workflows"""
        workflows = {
            'security_review': {
                'name': 'Security Review Workflow',
                'description': 'Learn how to conduct a thorough security review of your Terraform changes',
                'steps': [
                    {
                        'title': 'Enable Security Focus',
                        'instruction': 'Apply security review smart defaults',
                        'action': 'Click "Security Review" in smart defaults and apply'
                    },
                    {
                        'title': 'Review High-Risk Changes',
                        'instruction': 'Focus on high and critical risk resources',
                        'action': 'Check the filtered summary cards for security-related changes'
                    },
                    {
                        'title': 'Analyze Security Resources',
                        'instruction': 'Look for IAM, security groups, and policy changes',
                        'action': 'Use the search to find "security", "iam", "policy" resources'
                    },
                    {
                        'title': 'Review Compliance',
                        'instruction': 'Check the security analysis section',
                        'action': 'Scroll to the security dashboard for compliance insights'
                    },
                    {
                        'title': 'Generate Security Report',
                        'instruction': 'Create a report for security stakeholders',
                        'action': 'Use the report generator with security focus'
                    }
                ]
            },
            'production_deployment': {
                'name': 'Production Deployment Workflow',
                'description': 'Best practices for reviewing production-bound changes',
                'steps': [
                    {
                        'title': 'Apply Production Defaults',
                        'instruction': 'Set filters for production review',
                        'action': 'Select "Production Deployment" in smart defaults'
                    },
                    {
                        'title': 'Review Deletion Operations',
                        'instruction': 'Carefully examine all delete operations',
                        'action': 'Filter by "delete" actions and review each resource'
                    },
                    {
                        'title': 'Check Dependencies',
                        'instruction': 'Look for resource dependencies that might be affected',
                        'action': 'Use the dependency visualization if available'
                    },
                    {
                        'title': 'Validate Risk Levels',
                        'instruction': 'Ensure all high-risk changes are intentional',
                        'action': 'Review the risk assessment explanations'
                    },
                    {
                        'title': 'Export for Review',
                        'instruction': 'Create documentation for the deployment',
                        'action': 'Export filtered data and generate a comprehensive report'
                    }
                ]
            },
            'multi_cloud_analysis': {
                'name': 'Multi-Cloud Analysis Workflow',
                'description': 'Analyze changes across multiple cloud providers',
                'steps': [
                    {
                        'title': 'Enable Multi-Cloud Features',
                        'instruction': 'Turn on enhanced multi-cloud analysis',
                        'action': 'Check "Multi-cloud features" in the sidebar'
                    },
                    {
                        'title': 'Review Provider Distribution',
                        'instruction': 'See how resources are distributed across providers',
                        'action': 'Check the enhanced dashboard section for provider breakdown'
                    },
                    {
                        'title': 'Analyze Cross-Cloud Risks',
                        'instruction': 'Look for risks that span multiple providers',
                        'action': 'Review the multi-cloud risk analysis section'
                    },
                    {
                        'title': 'Check Cross-Cloud Insights',
                        'instruction': 'Identify optimization opportunities',
                        'action': 'Explore the cross-cloud insights section'
                    },
                    {
                        'title': 'Filter by Provider',
                        'instruction': 'Focus on specific cloud providers',
                        'action': 'Use the provider filter to analyze each cloud separately'
                    }
                ]
            }
        }
        
        workflow = workflows.get(workflow_name)
        if workflow:
            self._set_session_state('workflow_tour_active', True)
            self._set_session_state('workflow_tour_name', workflow_name)
            self._set_session_state('workflow_tour_step', 1)
            self._set_session_state('workflow_tour_data', workflow)
            
            st.sidebar.success(f"🎯 **{workflow['name']} Started!**")
            st.sidebar.markdown(f"*{workflow['description']}*")
    
    def render_workflow_tour_controls(self) -> None:
        """Render controls for workflow-specific guided tours"""
        if self._get_session_state('workflow_tour_active', False):
            workflow_data = self._get_session_state('workflow_tour_data', {})
            current_step = self._get_session_state('workflow_tour_step', 1)
            total_steps = len(workflow_data.get('steps', []))
            
            with st.sidebar.container():
                st.markdown("---")
                st.markdown(f"### 🎯 {workflow_data.get('name', 'Workflow Tour')}")
                st.info(f"**Step {current_step} of {total_steps}**")
                
                if current_step <= total_steps:
                    current_step_data = workflow_data['steps'][current_step - 1]
                    
                    st.markdown(f"**{current_step_data['title']}**")
                    st.write(current_step_data['instruction'])
                    
                    if current_step_data.get('action'):
                        st.caption(f"👉 {current_step_data['action']}")
                
                # Navigation controls
                col1, col2, col3 = st.sidebar.columns([1, 1, 1])
                
                with col1:
                    if current_step > 1 and st.button("⬅️", help="Previous step"):
                        self._set_session_state('workflow_tour_step', current_step - 1)
                        st.rerun()
                
                with col2:
                    if st.button("⏸️", help="Pause workflow tour"):
                        self._set_session_state('workflow_tour_active', False)
                        st.rerun()
                
                with col3:
                    if current_step < total_steps and st.button("➡️", help="Next step"):
                        self._set_session_state('workflow_tour_step', current_step + 1)
                        st.rerun()
                    elif current_step == total_steps and st.button("✅", help="Complete workflow tour"):
                        self._set_session_state('workflow_tour_active', False)
                        self._set_session_state(f'workflow_{workflow_data.get("name", "").lower().replace(" ", "_")}_completed', True)
                        st.sidebar.success("🎉 Workflow tour completed!")
                        st.rerun()
    
    def _show_tour_step_guidance(self, step: int) -> None:
        """Show guidance for current tour step"""
        tour_type = self._get_session_state('tour_type', 'quick')
        tour_steps = self._get_session_state('tour_steps', [])
        
        if step <= len(tour_steps):
            current_step = tour_steps[step - 1]
            
            guidance = {
                '📁 File Upload': {
                    'instruction': 'Upload your Terraform plan JSON file using the file uploader above.',
                    'tip': 'Look for the dashed border upload area',
                    'keyboard_tip': 'Press Tab to navigate to the upload area, then Enter to open file browser'
                },
                '📊 Summary Cards': {
                    'instruction': 'Review the summary cards showing change counts and risk levels.',
                    'tip': 'Cards appear after successful file upload',
                    'keyboard_tip': 'Use Tab to navigate between summary cards'
                },
                '📈 Visualizations': {
                    'instruction': 'Explore the interactive charts showing resource distributions.',
                    'tip': 'Hover over chart elements for details',
                    'keyboard_tip': 'Charts are keyboard accessible - use Tab and arrow keys'
                },
                '📋 Data Table': {
                    'instruction': 'Use the detailed table to filter and search specific resources.',
                    'tip': 'Try the search box and filter controls',
                    'keyboard_tip': 'Use Ctrl+F to focus search, arrow keys to navigate table'
                },
                '🔍 Filters': {
                    'instruction': 'Use sidebar controls to focus your analysis on specific resources.',
                    'tip': 'Combine multiple filters for precise results',
                    'keyboard_tip': 'All filter controls are keyboard accessible'
                }
            }
            
            step_guidance = guidance.get(current_step, {
                'instruction': f'Explore the {current_step} section.',
                'tip': 'Look for interactive elements and helpful information'
            })
            
            st.sidebar.markdown(f"**Current Step: {current_step}**")
            st.sidebar.write(step_guidance['instruction'])
            
            if step_guidance.get('tip'):
                st.sidebar.info(f"💡 **Tip:** {step_guidance['tip']}")
            
            if step_guidance.get('keyboard_tip'):
                st.sidebar.caption(f"⌨️ **Keyboard:** {step_guidance['keyboard_tip']}")
        
        # Show progress
        progress = step / len(tour_steps) if tour_steps else 0
        st.sidebar.progress(progress)
        st.sidebar.caption(f"Progress: {step}/{len(tour_steps)} steps completed")
    
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
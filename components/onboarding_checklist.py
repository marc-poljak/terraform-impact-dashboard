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
    
    def render_enhanced_instructions(self) -> None:
        """
        Render enhanced instructions and onboarding for new users.
        Provides detailed guidance on file format, usage, and features with interactive tutorials.
        """
        # Import required modules at method level to avoid circular imports
        from components.help_system import HelpSystemComponent
        from ui.error_handler import ErrorHandler
        import json
        
        # Initialize help system for onboarding
        help_system = HelpSystemComponent()
        error_handler = ErrorHandler()
        
        # Show welcome guide for first-time users
        help_system.show_welcome_guide()
        
        # Show interactive onboarding if not completed
        error_handler.show_interactive_onboarding()
        
        # Welcome section with clear overview
        st.markdown("## 🚀 Welcome to Terraform Plan Impact Dashboard")
        st.markdown("""
        This dashboard helps you analyze and visualize Terraform plan changes before deployment. 
        Get insights into resource changes, risk assessment, and multi-cloud impacts.
        """)
        
        # Interactive tutorial section
        if st.button("🎓 Start Interactive Tutorial"):
            st.session_state['tutorial_step'] = 0
            st.rerun()
        
        # Show tutorial if active
        if st.session_state.get('tutorial_step', -1) >= 0:
            help_system.render_interactive_tutorial()
        
        # Smart defaults section
        st.markdown("---")
        st.markdown("### 🎯 Quick Start with Smart Defaults")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("""
            **New to the dashboard?** Choose your primary use case to apply optimized settings:
            """)
            
            use_case = st.selectbox(
                "Select your use case:",
                [
                    "General Analysis",
                    "Security Review", 
                    "Production Deployment",
                    "Development Testing",
                    "Multi-Cloud Migration",
                    "Cost Optimization"
                ],
                help="This will configure filters and settings optimized for your specific needs"
            )
        
        with col2:
            if st.button("🔧 Apply Smart Defaults", type="primary"):
                error_handler.apply_smart_defaults_for_use_case(use_case)
                
                # Show contextual tips for the selected use case
                use_case_tips = {
                    'Security Review': [
                        "Focus on IAM roles, policies, and security groups",
                        "Pay special attention to high-risk deletions",
                        "Use the security analysis section for detailed insights"
                    ],
                    'Production Deployment': [
                        "Review all medium and high-risk changes carefully",
                        "Check for potential downtime-causing operations",
                        "Consider deployment timing and rollback plans"
                    ],
                    'Development Testing': [
                        "Debug mode is enabled for detailed information",
                        "All change types are visible for comprehensive testing",
                        "Use filters to focus on specific areas of interest"
                    ],
                    'Multi-Cloud Migration': [
                        "Multi-cloud features are enabled for cross-provider analysis",
                        "Look for provider-specific recommendations",
                        "Check the cross-cloud insights section"
                    ],
                    'Cost Optimization': [
                        "Focus on compute and storage resources",
                        "Look for resource size changes and new instances",
                        "Consider the cost impact of create and replace operations"
                    ]
                }
                
                if use_case in use_case_tips:
                    error_handler.show_contextual_tips(
                        f"{use_case.lower().replace(' ', '_')}_tips",
                        use_case_tips[use_case]
                    )
        
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
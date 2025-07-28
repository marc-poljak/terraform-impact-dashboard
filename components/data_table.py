import streamlit as st
import pandas as pd
import re
from typing import Dict, List, Any, Optional
from ui.progress_tracker import ProgressTracker
from ui.performance_optimizer import PerformanceOptimizer
from ui.session_manager import SessionStateManager

# Try to import enhanced features, fall back to basic if not available
try:
    from utils.enhanced_risk_assessment import EnhancedRiskAssessment
    ENHANCED_FEATURES_AVAILABLE = True
except ImportError:
    from utils.risk_assessment import RiskAssessment
    ENHANCED_FEATURES_AVAILABLE = False


class DataTableComponent:
    """Component for displaying resource change details table with filtering and export functionality"""
    
    def __init__(self):
        self.enhanced_features_available = ENHANCED_FEATURES_AVAILABLE
        self.performance_optimizer = PerformanceOptimizer()
        self.session_manager = SessionStateManager()
    
    def render(self, parser, resource_changes: List[Dict[str, Any]], plan_data: Dict[str, Any], 
               enhanced_risk_assessor=None, enhanced_risk_result=None, enable_multi_cloud: bool = True) -> None:
        """
        Render the resource change details table with filtering and export functionality with progress tracking
        
        Args:
            parser: PlanParser instance
            resource_changes: List of resource changes
            plan_data: Original plan data
            enhanced_risk_assessor: Enhanced risk assessor instance (optional)
            enhanced_risk_result: Enhanced risk assessment result (optional)
            enable_multi_cloud: Whether multi-cloud features are enabled
        """
        st.markdown("---")
        st.markdown("## 📋 Resource Change Details")
        
        if not resource_changes:
            st.info("No resource changes found in the plan.")
            return
        
        # Initialize progress tracker for data processing
        progress_tracker = ProgressTracker()
        
        # Create detailed dataframe with performance optimization
        try:
            # Use performance optimizer for dataframe creation
            with self.performance_optimizer.performance_monitor("dataframe_creation"):
                detailed_df = self.performance_optimizer.optimize_dataframe_creation(
                    resource_changes, parser, use_cache=True
                )
            
            # Add risk assessment with performance optimization
            total_resources = len(detailed_df)
            
            with self.performance_optimizer.performance_monitor("risk_assessment"):
                if total_resources > 50:  # Use optimized processing for larger datasets
                    progress_tracker.initialize_progress_container()
                    
                    # Use performance optimizer for risk assessment
                    risk_assessor = enhanced_risk_assessor if (self.enhanced_features_available and enable_multi_cloud and enhanced_risk_assessor) else RiskAssessment()
                    
                    # Convert DataFrame rows to list format for optimizer
                    resource_list = []
                    for _, row in detailed_df.iterrows():
                        resource_list.append({
                            'type': row['resource_type'],
                            'action': row['action'],
                            'address': row['resource_address']
                        })
                    
                    # Use optimized risk assessment
                    risk_levels = self.performance_optimizer.optimize_risk_assessment(
                        resource_list, risk_assessor, plan_data, use_cache=True
                    )
                    
                    # Update progress during assignment
                    for i in range(len(risk_levels)):
                        if i % 50 == 0 or i == len(risk_levels) - 1:
                            progress_tracker.show_data_processing_progress(
                                "🔍 Applying risk assessments", i + 1, len(risk_levels)
                            )
                    
                    detailed_df['risk_level'] = risk_levels
                    progress_tracker.clear_progress()
                else:
                    # For smaller datasets, use standard processing
                    detailed_df['risk_level'] = detailed_df.apply(
                        lambda row: self._get_risk_level(row, enhanced_risk_assessor, plan_data, enable_multi_cloud), 
                        axis=1
                    )
            
            # Apply filters and display table
            filtered_df = self._apply_filters(detailed_df, enhanced_risk_result, enable_multi_cloud)
            
            if not filtered_df.empty:
                # Show progress for table rendering if dataset is large
                if len(filtered_df) > 100:
                    with st.spinner("📋 Rendering data table..."):
                        self._display_table(filtered_df)
                else:
                    self._display_table(filtered_df)
                    
                self._display_download_button(filtered_df)
            else:
                st.info("No resources match the current filters.")
                
        except Exception as e:
            st.error(f"Error creating resource table: {e}")
    
    def _get_risk_level(self, row: pd.Series, enhanced_risk_assessor, plan_data: Dict[str, Any], 
                       enable_multi_cloud: bool) -> str:
        """
        Get risk level for a resource row
        
        Args:
            row: DataFrame row containing resource information
            enhanced_risk_assessor: Enhanced risk assessor instance
            plan_data: Original plan data
            enable_multi_cloud: Whether multi-cloud features are enabled
            
        Returns:
            Risk level string ('Low', 'Medium', 'High')
        """
        try:
            resource_data = {
                'type': row['resource_type'],
                'change': {'actions': [row['action']]}
            }
            
            if self.enhanced_features_available and enable_multi_cloud and enhanced_risk_assessor:
                risk_result = enhanced_risk_assessor.assess_resource_risk(resource_data, plan_data)
                return risk_result['level']
            else:
                basic_assessor = RiskAssessment()
                risk_result = basic_assessor.assess_resource_risk(resource_data)
                return risk_result['level']
        except Exception:
            return 'Medium'  # Fallback
    
    def _apply_filters(self, detailed_df: pd.DataFrame, enhanced_risk_result, 
                      enable_multi_cloud: bool) -> pd.DataFrame:
        """
        Apply filters to the dataframe based on sidebar controls
        
        Args:
            detailed_df: Original dataframe
            enhanced_risk_result: Enhanced risk assessment result
            enable_multi_cloud: Whether multi-cloud features are enabled
            
        Returns:
            Filtered dataframe
        """
        # Enhanced search functionality with contextual help
        st.markdown("### 🔍 Search Resources")
        
        # Show contextual help for search
        from ui.error_handler import ErrorHandler
        error_handler = ErrorHandler()
        
        error_handler.show_contextual_help("Resource Search", {
            'quick_tip': "Search across resource names, types, and addresses using partial matches",
            'detailed_help': """
            **Search capabilities:**
            - **Resource names:** Find resources by their Terraform names
            - **Resource types:** Search by AWS/Azure/GCP resource types
            - **Resource addresses:** Search by full Terraform addresses
            - **Provider names:** Search by cloud provider
            
            **Search features:**
            - Case-insensitive matching
            - Partial string matching
            - Real-time filtering as you type
            - Search result highlighting
            
            **Search examples:**
            - `aws_instance` - Find all EC2 instances
            - `bucket` - Find S3 buckets or storage accounts
            - `vpc` - Find VPC or virtual network resources
            - `security` - Find security groups or policies
            """,
            'troubleshooting': """
            **If search isn't working:**
            - Check spelling and try partial matches
            - Clear search and try different terms
            - Use the data table filters as an alternative
            - Export data to search externally
            
            **Performance tips:**
            - Search is faster with fewer results
            - Use filters to narrow down before searching
            - Clear search when not needed
            """
        })
        
        # Search input with clear button
        col1, col2 = st.columns([4, 1])
        with col1:
            search_query = st.text_input(
                "Search by resource name, type, or address",
                value=self.session_manager.get_search_query(),
                placeholder="e.g., aws_instance, my-bucket, vpc",
                help="""
                **Search tips:**
                • Type any part of resource name, type, or address
                • Search is case-insensitive and supports partial matches
                • Results update automatically as you type
                • Use filters in sidebar for more precise control
                
                **Examples:**
                • `aws_instance` → Find all EC2 instances
                • `bucket` → Find storage buckets
                • `security` → Find security-related resources
                """,
                key="resource_search_input"
            )
        
        with col2:
            if st.button("Clear", help="Clear search query and show all resources"):
                self.session_manager.clear_search()
                st.rerun()
        
        # Update search query in session state
        if search_query != self.session_manager.get_search_query():
            self.session_manager.set_search_query(search_query)
        
        # Filters in sidebar
        st.sidebar.markdown("### 🔍 Filters")
        
        # Action filter with tooltip
        action_filter = st.sidebar.multiselect(
            "Filter by Action",
            options=['create', 'update', 'delete', 'replace'],
            default=['create', 'update', 'delete', 'replace'],
            help="Filter resources by Terraform action type:\n• Create: New resources being added\n• Update: Existing resources being modified\n• Delete: Resources being removed\n• Replace: Resources being destroyed and recreated"
        )
        
        # Risk filter with tooltip
        risk_filter = st.sidebar.multiselect(
            "Filter by Risk Level",
            options=['Low', 'Medium', 'High'],
            default=['Low', 'Medium', 'High'],
            help="Filter resources by calculated risk level:\n• Low: Safe changes with minimal impact\n• Medium: Changes requiring attention\n• High: Potentially dangerous changes requiring careful review"
        )
        
        # Provider filter (if multi-cloud enabled and data available)
        provider_filter = None
        if self.enhanced_features_available and enable_multi_cloud:
            try:
                # Use the same logic as app.py - check enhanced_risk_result for provider_risk_summary
                if isinstance(enhanced_risk_result, dict) and enhanced_risk_result.get('provider_risk_summary'):
                    available_providers = list(enhanced_risk_result['provider_risk_summary'].keys())
                    if available_providers:
                        provider_filter = st.sidebar.multiselect(
                            "Filter by Provider",
                            options=available_providers,
                            default=available_providers,
                            help="Filter resources by cloud provider. Shows only providers detected in your Terraform plan. Useful for focusing on specific cloud environments in multi-cloud deployments."
                        )
            except Exception:
                pass
        
        # Get filter logic from sidebar (default to AND if not available)
        filter_logic = st.session_state.get('filter_logic', 'AND')
        
        # Apply filters based on logic
        if filter_logic == 'AND':
            # AND logic: resource must match ALL selected filters
            filtered_df = detailed_df[
                (detailed_df['action'].isin(action_filter)) &
                (detailed_df['risk_level'].isin(risk_filter))
            ]
            
            # Apply provider filter if enabled
            if provider_filter is not None and 'provider' in detailed_df.columns:
                filtered_df = filtered_df[filtered_df['provider'].isin(provider_filter)]
        else:
            # OR logic: resource must match ANY selected filter
            action_mask = detailed_df['action'].isin(action_filter)
            risk_mask = detailed_df['risk_level'].isin(risk_filter)
            
            # Start with action OR risk
            combined_mask = action_mask | risk_mask
            
            # Add provider filter to OR logic if enabled
            if provider_filter is not None and 'provider' in detailed_df.columns:
                provider_mask = detailed_df['provider'].isin(provider_filter)
                combined_mask = combined_mask | provider_mask
            
            filtered_df = detailed_df[combined_mask]
        
        # Apply search filter
        if search_query.strip():
            filtered_df = self._apply_search_filter(filtered_df, search_query)
        
        # Update search results count
        self.session_manager.set_search_results_count(len(filtered_df))
        
        # Enhanced search results summary with guidance
        if search_query.strip():
            if len(filtered_df) > 0:
                st.success(f"🔍 **Found {len(filtered_df)} resource(s)** matching '{search_query}'")
                
                # Show search performance tip for large result sets
                if len(filtered_df) > 100:
                    error_handler.show_feature_tooltip(
                        "Large Search Results",
                        f"Found {len(filtered_df)} matches. Consider using more specific search terms or sidebar filters for better performance.",
                        "tip"
                    )
            else:
                st.warning(f"🔍 **No resources found** matching '{search_query}'")
                
                # Provide helpful suggestions for no results
                error_handler.show_progressive_disclosure(
                    "**Try these search improvements:**",
                    f"""
                    **Broaden your search:**
                    - Try shorter, more general terms
                    - Check for typos in '{search_query}'
                    - Use partial matches (e.g., 'aws' instead of 'aws_instance')
                    
                    **Alternative approaches:**
                    - Use sidebar filters instead of search
                    - Clear all filters and search again
                    - Browse the full table below
                    - Export data for external search tools
                    
                    **Common search terms:**
                    - Resource types: `aws_instance`, `azurerm_`, `google_`
                    - Actions: `create`, `update`, `delete`
                    - Services: `bucket`, `database`, `network`, `security`
                    """,
                    "Search Suggestions",
                    expanded=False
                )
        
        return filtered_df
    
    def _apply_search_filter(self, df: pd.DataFrame, search_query: str) -> pd.DataFrame:
        """
        Apply search filter to dataframe based on search query
        
        Args:
            df: Dataframe to search
            search_query: Search query string
            
        Returns:
            Filtered dataframe containing only rows matching the search query
        """
        if not search_query.strip():
            return df
        
        # Clean and prepare search query
        query = search_query.strip().lower()
        
        # Create search mask - search across multiple columns
        search_columns = ['resource_name', 'resource_type', 'resource_address']
        
        # Initialize mask as False for all rows
        search_mask = pd.Series([False] * len(df), index=df.index)
        
        # Search in each available column
        for column in search_columns:
            if column in df.columns:
                # Case-insensitive partial match
                column_mask = df[column].astype(str).str.lower().str.contains(
                    re.escape(query), na=False, regex=True
                )
                search_mask = search_mask | column_mask
        
        # Also search in provider column if available
        if 'provider' in df.columns:
            provider_mask = df['provider'].astype(str).str.lower().str.contains(
                re.escape(query), na=False, regex=True
            )
            search_mask = search_mask | provider_mask
        
        return df[search_mask]
    
    def _highlight_search_results(self, df: pd.DataFrame, search_query: str) -> pd.DataFrame:
        """
        Add highlighting to search results in the dataframe
        
        Args:
            df: Dataframe to highlight
            search_query: Search query to highlight
            
        Returns:
            Dataframe with highlighted search terms
        """
        if not search_query.strip():
            return df
        
        # Create a copy to avoid modifying original
        highlighted_df = df.copy()
        query = search_query.strip()
        
        # Columns to highlight
        highlight_columns = ['resource_name', 'resource_type', 'resource_address']
        
        for column in highlight_columns:
            if column in highlighted_df.columns:
                # Use HTML highlighting for search terms
                highlighted_df[column] = highlighted_df[column].astype(str).str.replace(
                    f'(?i)({re.escape(query)})',
                    r'<mark style="background-color: yellow; padding: 1px 2px;">\1</mark>',
                    regex=True
                )
        
        return highlighted_df
    
    def _display_table(self, filtered_df: pd.DataFrame) -> None:
        """
        Display the filtered dataframe as a table with optimization for large datasets
        
        Args:
            filtered_df: Filtered dataframe to display
        """
        # Use performance optimizer for table rendering
        with self.performance_optimizer.performance_monitor("table_rendering"):
            optimized_df, is_truncated = self.performance_optimizer.optimize_table_rendering(
                filtered_df, max_rows=1000
            )
            
            # Apply search highlighting if there's an active search
            search_query = self.session_manager.get_search_query()
            if search_query.strip():
                # Note: Streamlit dataframe doesn't support HTML rendering for highlighting
                # So we'll show the search results count instead
                pass
            
            # Show truncation warning if applicable
            if is_truncated:
                st.warning(f"⚠️ Showing first 1,000 rows of {len(filtered_df):,} total resources. Use filters to narrow results or download CSV for complete data.")
            
            # Column configuration
            column_config = {
                "action": st.column_config.TextColumn("Action", width="small"),
                "resource_type": st.column_config.TextColumn("Resource Type", width="medium"),
                "resource_name": st.column_config.TextColumn("Resource Name", width="large"),
                "risk_level": st.column_config.TextColumn("Risk Level", width="small"),
            }
            
            if 'provider' in optimized_df.columns:
                column_config["provider"] = st.column_config.TextColumn("Provider", width="small")
            
            # Display performance info for large datasets
            if len(filtered_df) > 500:
                with st.expander("📊 Performance Information", expanded=False):
                    metrics = self.performance_optimizer.get_performance_metrics()
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.metric("Total Resources", f"{len(filtered_df):,}")
                        st.metric("Displayed Rows", f"{len(optimized_df):,}")
                        
                    with col2:
                        cache_stats = metrics['cache_stats']
                        st.metric("Cache Hit Rate", f"{cache_stats['hit_rate']:.1f}%")
                        st.metric("Cache Size", cache_stats['cache_size'])
            
            st.dataframe(
                optimized_df,
                use_container_width=True,
                column_config=column_config
            )
    
    def _display_download_button(self, filtered_df: pd.DataFrame) -> None:
        """
        Display download button for filtered data
        
        Args:
            filtered_df: Filtered dataframe to export
        """
        csv = filtered_df.to_csv(index=False)
        st.download_button(
            label="📥 Download Filtered Data as CSV",
            data=csv,
            file_name="terraform_plan_changes.csv",
            mime="text/csv",
            help="Download the currently filtered resource changes as a CSV file. Includes all visible columns with resource details, actions, and risk assessments. Perfect for reporting or further analysis in spreadsheet applications."
        )
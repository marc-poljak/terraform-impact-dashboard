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
            # Track filter usage for onboarding
            from ui.error_handler import ErrorHandler
            error_handler = ErrorHandler()
            
            # Check if filters are being used
            current_filters = self.session_manager.get_filter_state()
            default_filters = {
                'action_filter': ['create', 'update', 'delete', 'replace'],
                'risk_filter': ['Low', 'Medium', 'High'],
                'provider_filter': []
            }
            
            filters_modified = (
                current_filters['action_filter'] != default_filters['action_filter'] or
                current_filters['risk_filter'] != default_filters['risk_filter'] or
                len(current_filters['provider_filter']) > 0
            )
            
            if filters_modified:
                error_handler.track_user_progress('filters_used')
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
            - Search result highlighting and navigation
            
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
        
        # Search input with navigation controls
        search_col1, search_col2, nav_col1, nav_col2, clear_col = st.columns([3, 1, 0.5, 0.5, 0.5])
        
        with search_col1:
            search_query = st.text_input(
                "Search by resource name, type, or address",
                value=self.session_manager.get_search_query(),
                placeholder="e.g., aws_instance, my-bucket, vpc",
                help="""
                **Search tips:**
                • Type any part of resource name, type, or address
                • Search is case-insensitive and supports partial matches
                • Results update automatically as you type
                • Use navigation buttons to jump between results
                
                **Examples:**
                • `aws_instance` → Find all EC2 instances
                • `bucket` → Find storage buckets
                • `security` → Find security-related resources
                """,
                key="resource_search_input"
            )
        
        # Update search query in session state
        if search_query != self.session_manager.get_search_query():
            self.session_manager.set_search_query(search_query)
        
        # Search result navigation controls
        search_info = self.session_manager.get_current_search_result_info()
        
        with search_col2:
            if search_info['has_results']:
                st.markdown(f"**{search_info['current_position']}/{search_info['total_results']}**")
            else:
                st.markdown("")
        
        with nav_col1:
            if st.button("◀", 
                        disabled=not search_info['can_go_previous'],
                        help="Previous search result",
                        key="search_prev"):
                self.session_manager.navigate_search_results('previous')
                st.rerun()
        
        with nav_col2:
            if st.button("▶", 
                        disabled=not search_info['can_go_next'],
                        help="Next search result",
                        key="search_next"):
                self.session_manager.navigate_search_results('next')
                st.rerun()
        
        with clear_col:
            if st.button("Clear", help="Clear search query and show all resources"):
                self.session_manager.clear_search()
                st.rerun()
        
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
        
        # Get filter logic and advanced settings from session state
        filter_logic = st.session_state.get('filter_logic', 'AND')
        use_advanced_filters = st.session_state.get('use_advanced_filters', False)
        filter_expression = st.session_state.get('filter_expression', '')
        
        # Apply filters based on logic
        if use_advanced_filters and filter_expression.strip():
            # Use advanced filter expression
            try:
                filtered_df = self._apply_advanced_filter_expression(detailed_df, filter_expression)
            except Exception as e:
                # Fall back to basic filtering if expression fails
                st.warning(f"⚠️ Advanced filter expression failed: {e}. Using basic filters.")
                filtered_df = self._apply_basic_filters(detailed_df, action_filter, risk_filter, provider_filter, filter_logic)
        else:
            # Use basic filter logic
            filtered_df = self._apply_basic_filters(detailed_df, action_filter, risk_filter, provider_filter, filter_logic)
        
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
        
        # Store search result indices for navigation
        search_result_indices = df[search_mask].index.tolist()
        self.session_manager.set_search_result_indices(search_result_indices)
        
        return df[search_mask]
    
    def _add_search_highlighting(self, df: pd.DataFrame, search_query: str) -> pd.DataFrame:
        """
        Add search highlighting indicators to the dataframe
        
        Args:
            df: Dataframe to add indicators to
            search_query: Search query to match
            
        Returns:
            Dataframe with search match indicators
        """
        if not search_query.strip():
            return df
        
        # Create a copy to avoid modifying original
        highlighted_df = df.copy()
        query = search_query.strip().lower()
        
        # Add search indicator column
        highlighted_df['search_indicator'] = ''
        
        # Check each row for matches and add indicators
        search_columns = ['resource_name', 'resource_type', 'resource_address']
        if 'provider' in highlighted_df.columns:
            search_columns.append('provider')
        
        for idx, row in highlighted_df.iterrows():
            matches = []
            for column in search_columns:
                if column in highlighted_df.columns:
                    cell_value = str(row[column]).lower()
                    if query in cell_value:
                        # Determine which part matched
                        if column == 'resource_name':
                            matches.append('NAME')
                        elif column == 'resource_type':
                            matches.append('TYPE')
                        elif column == 'resource_address':
                            matches.append('ADDR')
                        elif column == 'provider':
                            matches.append('PROV')
            
            if matches:
                highlighted_df.loc[idx, 'search_indicator'] = '🔍 ' + '+'.join(matches)
        
        return highlighted_df
    
    def _apply_basic_filters(self, df: pd.DataFrame, action_filter: List[str], 
                           risk_filter: List[str], provider_filter: Optional[List[str]], 
                           filter_logic: str) -> pd.DataFrame:
        """
        Apply basic filter logic (AND/OR) to the dataframe.
        
        Args:
            df: Dataframe to filter
            action_filter: List of actions to include
            risk_filter: List of risk levels to include
            provider_filter: List of providers to include (optional)
            filter_logic: 'AND' or 'OR' logic
            
        Returns:
            Filtered dataframe
        """
        if filter_logic == 'AND':
            # AND logic: resource must match ALL selected filters
            filtered_df = df[
                (df['action'].isin(action_filter)) &
                (df['risk_level'].isin(risk_filter))
            ]
            
            # Apply provider filter if enabled
            if provider_filter is not None and 'provider' in df.columns:
                filtered_df = filtered_df[filtered_df['provider'].isin(provider_filter)]
        else:
            # OR logic: resource must match ANY selected filter
            action_mask = df['action'].isin(action_filter)
            risk_mask = df['risk_level'].isin(risk_filter)
            
            # Start with action OR risk
            combined_mask = action_mask | risk_mask
            
            # Add provider filter to OR logic if enabled
            if provider_filter is not None and 'provider' in df.columns:
                provider_mask = df['provider'].isin(provider_filter)
                combined_mask = combined_mask | provider_mask
            
            filtered_df = df[combined_mask]
        
        return filtered_df
    
    def _apply_advanced_filter_expression(self, df: pd.DataFrame, expression: str) -> pd.DataFrame:
        """
        Apply advanced filter expression to the dataframe.
        
        Args:
            df: Dataframe to filter
            expression: Filter expression string
            
        Returns:
            Filtered dataframe
        """
        if not expression.strip():
            return df
        
        try:
            # Parse and apply the filter expression
            # This is a simplified implementation - in production you'd want a proper parser
            filter_mask = self._evaluate_filter_expression(df, expression)
            return df[filter_mask]
            
        except Exception as e:
            # Log error and return original dataframe
            st.error(f"Error applying advanced filter: {e}")
            return df
    
    def _evaluate_filter_expression(self, df: pd.DataFrame, expression: str) -> pd.Series:
        """
        Evaluate a filter expression against the dataframe.
        
        Args:
            df: Dataframe to evaluate against
            expression: Filter expression string
            
        Returns:
            Boolean series indicating which rows match the expression
        """
        # This is a simplified implementation
        # In production, you'd want a proper expression parser/evaluator
        
        # Initialize result mask as all True
        result_mask = pd.Series([True] * len(df), index=df.index)
        
        try:
            # Simple expression evaluation
            # Replace field names with actual column references
            eval_expression = expression.lower()
            
            # Map field names to actual column names
            field_mapping = {
                'action': 'action',
                'risk': 'risk_level',
                'provider': 'provider',
                'type': 'resource_type',
                'name': 'resource_name'
            }
            
            # This is a very basic implementation
            # For production use, implement a proper expression parser
            if 'action=' in eval_expression:
                # Extract action value
                import re
                action_match = re.search(r"action\s*=\s*['\"]([^'\"]+)['\"]", eval_expression)
                if action_match:
                    action_value = action_match.group(1)
                    action_mask = df['action'] == action_value
                    
                    if 'and' in eval_expression.lower():
                        result_mask = result_mask & action_mask
                    elif 'or' in eval_expression.lower():
                        result_mask = result_mask | action_mask
                    else:
                        result_mask = action_mask
            
            if 'risk=' in eval_expression:
                # Extract risk value
                risk_match = re.search(r"risk\s*=\s*['\"]([^'\"]+)['\"]", eval_expression)
                if risk_match:
                    risk_value = risk_match.group(1).title()  # Convert to title case
                    risk_mask = df['risk_level'] == risk_value
                    
                    if 'and' in eval_expression.lower():
                        result_mask = result_mask & risk_mask
                    elif 'or' in eval_expression.lower():
                        result_mask = result_mask | risk_mask
                    else:
                        result_mask = risk_mask
            
            if 'provider=' in eval_expression and 'provider' in df.columns:
                # Extract provider value
                provider_match = re.search(r"provider\s*=\s*['\"]([^'\"]+)['\"]", eval_expression)
                if provider_match:
                    provider_value = provider_match.group(1)
                    provider_mask = df['provider'] == provider_value
                    
                    if 'and' in eval_expression.lower():
                        result_mask = result_mask & provider_mask
                    elif 'or' in eval_expression.lower():
                        result_mask = result_mask | provider_mask
                    else:
                        result_mask = provider_mask
            
            # Handle IN expressions
            if ' in ' in eval_expression.lower():
                in_matches = re.findall(r"(\w+)\s+in\s*\(([^)]+)\)", eval_expression.lower())
                for field, values_str in in_matches:
                    # Parse values
                    values = [v.strip().strip("'\"") for v in values_str.split(',')]
                    
                    if field in field_mapping and field_mapping[field] in df.columns:
                        column_name = field_mapping[field]
                        if field == 'risk':
                            values = [v.title() for v in values]  # Convert to title case for risk
                        
                        in_mask = df[column_name].isin(values)
                        
                        if 'and' in eval_expression.lower():
                            result_mask = result_mask & in_mask
                        elif 'or' in eval_expression.lower():
                            result_mask = result_mask | in_mask
                        else:
                            result_mask = in_mask
            
            return result_mask
            
        except Exception as e:
            # Return all True if evaluation fails
            st.warning(f"Filter expression evaluation failed: {e}")
            return pd.Series([True] * len(df), index=df.index)
    
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
            
            # Apply search highlighting and current result indication
            search_query = self.session_manager.get_search_query()
            display_df = optimized_df.copy()
            
            if search_query.strip():
                # Add search highlighting indicators
                display_df = self._add_search_highlighting(display_df, search_query)
                
                # Highlight current search result if navigation is active
                search_info = self.session_manager.get_current_search_result_info()
                if search_info['has_results']:
                    current_result_index = self.session_manager.get_current_search_result_index()
                    search_indices = self.session_manager.get_search_result_indices()
                    
                    if current_result_index < len(search_indices):
                        current_row_index = search_indices[current_result_index]
                        # Add indicator for current search result
                        if current_row_index in display_df.index:
                            display_df.loc[current_row_index, 'search_indicator'] = '🎯 CURRENT'
            
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
            
            if 'provider' in display_df.columns:
                column_config["provider"] = st.column_config.TextColumn("Provider", width="small")
            
            # Add search indicator column if search is active
            if search_query.strip() and 'search_indicator' in display_df.columns:
                column_config["search_indicator"] = st.column_config.TextColumn("Match", width="small")
            
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
                display_df,
                use_container_width=True,
                column_config=column_config
            )
    
    def _display_download_button(self, filtered_df: pd.DataFrame) -> None:
        """
        Display download button for filtered data with progress tracking
        
        Args:
            filtered_df: Filtered dataframe to export
        """
        csv = filtered_df.to_csv(index=False)
        
        # Track export usage for onboarding
        if st.download_button(
            label="📥 Download Filtered Data as CSV",
            data=csv,
            file_name="terraform_plan_changes.csv",
            mime="text/csv",
            help="Download the currently filtered resource changes as a CSV file. Includes all visible columns with resource details, actions, and risk assessments. Perfect for reporting or further analysis in spreadsheet applications."
        ):
            # Track data export for onboarding progress
            from ui.error_handler import ErrorHandler
            error_handler = ErrorHandler()
            error_handler.track_user_progress('data_exported')
            
            # Show export success hint
            st.success("✅ Data exported successfully! The CSV file contains all filtered resource details.")
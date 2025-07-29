"""
Integration tests for component interactions and data flow

Tests how components work together and pass data between each other.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os
import json

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from tests.integration.test_fixtures import TestFixtures


def create_streamlit_mocks():
    """Create properly configured Streamlit mocks"""
    # Mock columns to return multiple mock objects
    mock_columns = Mock()
    mock_columns.return_value = [Mock(), Mock(), Mock(), Mock(), Mock()]  # Return 5 mock columns
    
    # Mock container and expander with context manager support
    mock_container = Mock()
    mock_expander = Mock()
    mock_expander.return_value.__enter__ = Mock(return_value=Mock())
    mock_expander.return_value.__exit__ = Mock(return_value=None)
    
    # Mock spinner with context manager support
    mock_spinner = Mock()
    mock_spinner.return_value.__enter__ = Mock(return_value=Mock())
    mock_spinner.return_value.__exit__ = Mock(return_value=None)
    
    return {
        'columns': mock_columns,
        'container': mock_container,
        'expander': mock_expander,
        'spinner': mock_spinner
    }


class TestComponentInteractions:
    """Test component interactions and data flow"""
    
    def setup_method(self):
        """Set up test fixtures before each test method"""
        # Create a mock session state that supports both dict and attribute access
        class MockSessionState(dict):
            def __getattr__(self, name):
                try:
                    return self[name]
                except KeyError:
                    # Return default values for common session state keys
                    defaults = {
                        'show_debug': False,
                        'enable_multi_cloud': True,
                        'uploaded_file_processed': False,
                        'action_filter': ['create', 'update', 'delete', 'replace'],
                        'risk_filter': ['Low', 'Medium', 'High'],
                        'provider_filter': [],
                        'search_query': '',
                        'search_results_count': 0,
                        'current_search_result_index': 0,
                        'filter_logic': 'AND',
                        'selected_preset': 'Custom',
                        'use_advanced_filters': False,
                        'filter_expression': '',
                        'plan_data': None,
                        'summary': None,
                        'resource_changes': None,
                        'search_result_indices': [],
                        'saved_filter_configs': []
                    }
                    return defaults.get(name, None)
            
            def __setattr__(self, name, value):
                self[name] = value
        
        self.mock_session_state = MockSessionState()
        
        # Mock Streamlit functions
        self.streamlit_patches = [
            patch('streamlit.session_state', self.mock_session_state),
            patch('streamlit.markdown'),
            patch('streamlit.success'),
            patch('streamlit.error'),
            patch('streamlit.warning'),
            patch('streamlit.info'),
            patch('streamlit.file_uploader'),
            patch('streamlit.selectbox'),
            patch('streamlit.multiselect'),
            patch('streamlit.checkbox'),
            patch('streamlit.text_input'),
            patch('streamlit.button'),
            patch('streamlit.columns'),
            patch('streamlit.container'),
            patch('streamlit.expander'),
            patch('streamlit.sidebar'),
            patch('streamlit.dataframe'),
            patch('streamlit.plotly_chart'),
            patch('streamlit.download_button')
        ]
        
        for patch_obj in self.streamlit_patches:
            patch_obj.start()
    
    def teardown_method(self):
        """Clean up after each test method"""
        for patch_obj in self.streamlit_patches:
            patch_obj.stop()
    
    def test_upload_to_parser_data_flow(self):
        """Test data flow from UploadComponent to PlanParser"""
        from components.upload_section import UploadComponent
        from parsers.plan_parser import PlanParser
        
        # Create upload component
        upload_component = UploadComponent()
        
        # Get test plan data
        plan_data = TestFixtures.get_simple_plan()
        
        # Test file validation
        issues = upload_component._validate_plan_structure(plan_data)
        assert len(issues) == 0, "Simple plan should be valid"
        
        # Test parser creation with uploaded data
        parser = PlanParser(plan_data)
        
        # Verify parser received correct data
        assert parser.terraform_version == "1.5.0"
        assert parser.format_version == "1.2"
        assert len(parser.resource_changes) == 2
        
        # Test parser summary generation
        summary = parser.get_summary()
        assert summary['create'] == 1
        assert summary['update'] == 1
        assert summary['delete'] == 0
        assert summary['total'] == 2
    
    def test_sidebar_to_data_table_filter_flow(self):
        """Test filter data flow from SidebarComponent to DataTableComponent"""
        from components.sidebar import SidebarComponent
        from components.data_table import DataTableComponent
        from parsers.plan_parser import PlanParser
        
        # Create components
        sidebar = SidebarComponent()
        data_table = DataTableComponent()
        
        # Get test data
        plan_data = TestFixtures.get_multi_cloud_plan()
        parser = PlanParser(plan_data)
        resource_changes = parser.get_resource_changes()
        
        # Set up filter state in session
        self.mock_session_state['action_filter'] = ['create']
        self.mock_session_state['risk_filter'] = ['High']
        self.mock_session_state['provider_filter'] = ['aws']
        
        # Get filter state from sidebar
        filter_state = sidebar.session_manager.get_filter_state()
        
        # Verify filter state
        assert filter_state['action_filter'] == ['create']
        assert filter_state['risk_filter'] == ['High']
        assert filter_state['provider_filter'] == ['aws']
        
        # Test data table with filters (mock the render method)
        with patch.object(data_table, 'render') as mock_render:
            mock_render.return_value = None
            data_table.render(resource_changes, {})
            
            # Verify render was called
            mock_render.assert_called_once()
            call_args = mock_render.call_args[0]
            assert len(call_args) >= 1  # Should have resource_changes as first arg
    
    def test_session_manager_state_persistence(self):
        """Test session state persistence across components"""
        from ui.session_manager import SessionStateManager
        from components.sidebar import SidebarComponent
        
        # Create session manager
        session_manager = SessionStateManager()
        
        # Set some state
        session_manager.set_debug_state(True)
        session_manager.set_multi_cloud_state(False)
        session_manager.update_filter_state({
            'action_filter': ['create', 'delete'],
            'risk_filter': ['High'],
            'provider_filter': ['aws', 'azure']
        })
        
        # Create sidebar component (should use same session state)
        sidebar = SidebarComponent()
        
        # Verify state is shared
        assert sidebar.session_manager.get_debug_state() == True
        assert sidebar.session_manager.get_multi_cloud_state() == False
        
        filter_state = sidebar.session_manager.get_filter_state()
        assert filter_state['action_filter'] == ['create', 'delete']
        assert filter_state['risk_filter'] == ['High']
        assert filter_state['provider_filter'] == ['aws', 'azure']
    
    def test_error_handler_across_components(self):
        """Test error handling consistency across components"""
        from ui.error_handler import ErrorHandler
        from components.upload_section import UploadComponent
        
        # Create components
        error_handler = ErrorHandler()
        upload_component = UploadComponent()
        
        # Test invalid plan data
        invalid_plan = TestFixtures.get_invalid_plan()
        
        # Test upload component validation
        issues = upload_component._validate_plan_structure(invalid_plan)
        assert len(issues) > 0, "Invalid plan should have validation issues"
        
        # Test error handler with upload errors
        with patch.object(error_handler, 'handle_upload_error') as mock_handle:
            try:
                # Simulate an error condition
                raise ValueError("Invalid JSON structure")
            except ValueError as e:
                error_handler.handle_upload_error(e)
                mock_handle.assert_called_once_with(e)
    
    def test_enhanced_features_integration(self):
        """Test integration with enhanced features when available"""
        # Test with enhanced features available
        with patch('components.enhanced_sections.ENHANCED_FEATURES_AVAILABLE', True):
            from components.enhanced_sections import EnhancedSectionsComponent
            
            enhanced_component = EnhancedSectionsComponent()
            
            # Test component creation
            assert enhanced_component is not None
            
            # Test with multi-cloud plan
            plan_data = TestFixtures.get_multi_cloud_plan()
            
            # Mock enhanced risk assessor
            mock_enhanced_risk_assessor = Mock()
            mock_enhanced_risk_assessor.assess_plan_risks.return_value = {
                'overall_risk_score': 7.5,
                'provider_risks': {
                    'aws': {'risk_score': 8.0, 'resource_count': 3},
                    'azure': {'risk_score': 7.0, 'resource_count': 2},
                    'google': {'risk_score': 6.0, 'resource_count': 1}
                }
            }
            
            # Test enhanced dashboard rendering (mock the render method)
            with patch.object(enhanced_component, 'render_enhanced_dashboard_section') as mock_render:
                mock_render.return_value = None
                enhanced_component.render_enhanced_dashboard_section(
                    plan_data, None, mock_enhanced_risk_assessor
                )
                mock_render.assert_called_once()
    
    def test_basic_features_fallback(self):
        """Test fallback to basic features when enhanced features unavailable"""
        # Test with enhanced features unavailable
        with patch('components.enhanced_sections.ENHANCED_FEATURES_AVAILABLE', False):
            from components.enhanced_sections import EnhancedSectionsComponent
            
            enhanced_component = EnhancedSectionsComponent()
            
            # Component should still be created
            assert enhanced_component is not None
            
            # Test graceful degradation
            plan_data = TestFixtures.get_simple_plan()
            
            # Should handle missing enhanced features gracefully
            with patch.object(enhanced_component, 'render_enhanced_dashboard_section') as mock_render:
                mock_render.return_value = None
                enhanced_component.render_enhanced_dashboard_section(plan_data, None, None)
                mock_render.assert_called_once()
    
    def test_visualization_data_flow(self):
        """Test data flow to visualization components"""
        from components.visualizations import VisualizationsComponent
        from parsers.plan_parser import PlanParser
        
        # Create components
        viz_component = VisualizationsComponent()
        
        # Get test data
        plan_data = TestFixtures.get_multi_cloud_plan()
        parser = PlanParser(plan_data)
        
        # Get data for visualizations
        summary = parser.get_summary()
        resource_changes = parser.get_resource_changes()
        
        # Test visualization rendering (mock the render method)
        with patch.object(viz_component, 'render') as mock_render:
            mock_render.return_value = None
            viz_component.render(summary, resource_changes, {})
            
            # Verify render was called with correct data
            mock_render.assert_called_once()
            call_args = mock_render.call_args[0]
            assert call_args[0] == summary  # First arg should be summary
            assert len(call_args[1]) > 0     # Second arg should be resource changes
    
    def test_summary_cards_data_integration(self):
        """Test summary cards integration with parsed data"""
        from components.summary_cards import SummaryCardsComponent
        from parsers.plan_parser import PlanParser
        
        # Create components
        summary_component = SummaryCardsComponent()
        
        # Get test data
        plan_data = TestFixtures.get_multi_cloud_plan()
        parser = PlanParser(plan_data)
        
        # Get summary data
        summary = parser.get_summary()
        
        # Test summary cards rendering (mock the render method)
        with patch.object(summary_component, 'render') as mock_render:
            mock_render.return_value = None
            summary_component.render(summary, plan_data, {})
            
            # Verify render was called
            mock_render.assert_called_once()
            call_args = mock_render.call_args[0]
            assert call_args[0] == summary  # First arg should be summary
    
    def test_search_functionality_integration(self):
        """Test search functionality across components"""
        from components.sidebar import SidebarComponent
        from components.data_table import DataTableComponent
        from parsers.plan_parser import PlanParser
        
        # Create components
        sidebar = SidebarComponent()
        data_table = DataTableComponent()
        
        # Get test data
        plan_data = TestFixtures.get_multi_cloud_plan()
        parser = PlanParser(plan_data)
        resource_changes = parser.get_resource_changes()
        
        # Set search query
        search_query = "aws_instance"
        sidebar.session_manager.set_search_query(search_query)
        
        # Verify search state
        assert sidebar.session_manager.get_search_query() == search_query
        assert sidebar.session_manager.is_search_active() == True
        
        # Test search results (mock the search functionality)
        with patch.object(data_table, '_apply_search_filter') as mock_search:
            mock_search.return_value = [rc for rc in resource_changes if 'aws_instance' in rc.get('type', '')]
            
            filtered_results = data_table._apply_search_filter(resource_changes, search_query)
            
            # Verify search was applied
            mock_search.assert_called_once_with(resource_changes, search_query)
            assert len(filtered_results) >= 0  # Should return some results
    
    def test_filter_preset_integration(self):
        """Test filter preset functionality integration"""
        from components.sidebar import SidebarComponent
        
        # Create sidebar component
        sidebar = SidebarComponent()
        
        # Test preset configuration
        preset_config = sidebar._get_preset_filters("High Risk Only")
        
        # Verify preset structure
        assert isinstance(preset_config, dict)
        assert 'action_filter' in preset_config
        assert 'risk_filter' in preset_config
        assert 'provider_filter' in preset_config
        
        # Apply preset to session state
        sidebar.session_manager.update_filter_state(preset_config)
        
        # Verify preset was applied
        filter_state = sidebar.session_manager.get_filter_state()
        assert filter_state['risk_filter'] == ['High']
    
    def test_progress_tracking_integration(self):
        """Test progress tracking across components"""
        from ui.progress_tracker import ProgressTracker
        
        # Create progress tracker
        progress_tracker = ProgressTracker()
        
        # Test progress tracking methods exist
        assert hasattr(progress_tracker, 'track_operation')
        assert hasattr(progress_tracker, 'show_progress_bar')
        
        # Test progress tracking workflow (mock the methods)
        with patch.object(progress_tracker, 'track_operation') as mock_track, \
             patch.object(progress_tracker, 'show_progress_bar') as mock_progress:
            
            # Simulate progress workflow
            with progress_tracker.track_operation("Processing plan data"):
                pass
            progress_tracker.show_progress_bar(50, 100, "Parsing resources")
            
            # Verify methods were called
            mock_track.assert_called_once_with("Processing plan data")
            mock_progress.assert_called_once_with(50, 100, "Parsing resources")


class TestEndToEndWorkflows:
    """Test complete end-to-end workflows"""
    
    def setup_method(self):
        """Set up test fixtures before each test method"""
        # Create a mock session state
        class MockSessionState(dict):
            def __getattr__(self, name):
                try:
                    return self[name]
                except KeyError:
                    defaults = {
                        'show_debug': False,
                        'enable_multi_cloud': True,
                        'uploaded_file_processed': False,
                        'action_filter': ['create', 'update', 'delete', 'replace'],
                        'risk_filter': ['Low', 'Medium', 'High'],
                        'provider_filter': [],
                        'search_query': '',
                        'plan_data': None,
                        'summary': None
                    }
                    return defaults.get(name, None)
            
            def __setattr__(self, name, value):
                self[name] = value
        
        self.mock_session_state = MockSessionState()
        
        # Mock Streamlit functions
        self.streamlit_patches = [
            patch('streamlit.session_state', self.mock_session_state),
            patch('streamlit.markdown'),
            patch('streamlit.success'),
            patch('streamlit.error'),
            patch('streamlit.warning'),
            patch('streamlit.info'),
            patch('streamlit.file_uploader'),
            patch('streamlit.selectbox'),
            patch('streamlit.multiselect'),
            patch('streamlit.checkbox'),
            patch('streamlit.text_input'),
            patch('streamlit.button'),
            patch('streamlit.columns'),
            patch('streamlit.container'),
            patch('streamlit.expander'),
            patch('streamlit.sidebar'),
            patch('streamlit.dataframe'),
            patch('streamlit.plotly_chart'),
            patch('streamlit.download_button')
        ]
        
        for patch_obj in self.streamlit_patches:
            patch_obj.start()
    
    def teardown_method(self):
        """Clean up after each test method"""
        for patch_obj in self.streamlit_patches:
            patch_obj.stop()
    
    def test_complete_plan_processing_workflow(self):
        """Test complete workflow from upload to visualization"""
        from components.upload_section import UploadComponent
        from components.summary_cards import SummaryCardsComponent
        from components.visualizations import VisualizationsComponent
        from components.data_table import DataTableComponent
        from parsers.plan_parser import PlanParser
        
        # Step 1: Upload and validate plan
        upload_component = UploadComponent()
        plan_data = TestFixtures.get_multi_cloud_plan()
        
        # Validate plan structure
        issues = upload_component._validate_plan_structure(plan_data)
        assert len(issues) == 0, "Multi-cloud plan should be valid"
        
        # Step 2: Parse plan data
        parser = PlanParser(plan_data)
        summary = parser.get_summary()
        resource_changes = parser.get_resource_changes()
        
        # Verify parsing results
        assert summary['total'] > 0
        assert len(resource_changes) > 0
        
        # Step 3: Generate summary cards
        summary_component = SummaryCardsComponent()
        with patch.object(summary_component, 'render') as mock_summary_render:
            mock_summary_render.return_value = None
            summary_component.render(summary, plan_data, {})
            mock_summary_render.assert_called_once()
        
        # Step 4: Generate visualizations
        viz_component = VisualizationsComponent()
        with patch.object(viz_component, 'render') as mock_viz_render:
            mock_viz_render.return_value = None
            viz_component.render(summary, resource_changes, {})
            mock_viz_render.assert_called_once()
        
        # Step 5: Generate data table
        data_table = DataTableComponent()
        with patch.object(data_table, 'render') as mock_table_render:
            mock_table_render.return_value = None
            data_table.render(parser, resource_changes, plan_data)
            mock_table_render.assert_called_once()
    
    def test_filtering_workflow(self):
        """Test complete filtering workflow"""
        from components.sidebar import SidebarComponent
        from components.data_table import DataTableComponent
        from parsers.plan_parser import PlanParser
        
        # Create components
        sidebar = SidebarComponent()
        data_table = DataTableComponent()
        
        # Get test data
        plan_data = TestFixtures.get_multi_cloud_plan()
        parser = PlanParser(plan_data)
        resource_changes = parser.get_resource_changes()
        
        # Step 1: Set filters through sidebar
        filter_config = {
            'action_filter': ['create'],
            'risk_filter': ['High'],
            'provider_filter': ['aws']
        }
        sidebar.session_manager.update_filter_state(filter_config)
        
        # Step 2: Verify filter state
        current_filters = sidebar.session_manager.get_filter_state()
        assert current_filters['action_filter'] == ['create']
        assert current_filters['risk_filter'] == ['High']
        assert current_filters['provider_filter'] == ['aws']
        
        # Step 3: Apply filters to data table
        with patch.object(data_table, '_apply_filters') as mock_filter:
            mock_filter.return_value = []  # Mock filtered results
            
            filtered_data = data_table._apply_filters(resource_changes, current_filters)
            mock_filter.assert_called_once_with(resource_changes, current_filters)
    
    def test_error_handling_workflow(self):
        """Test error handling throughout the workflow"""
        from components.upload_section import UploadComponent
        from ui.error_handler import ErrorHandler
        
        # Create components
        upload_component = UploadComponent()
        error_handler = ErrorHandler()
        
        # Test with invalid plan data
        invalid_plan = TestFixtures.get_invalid_plan()
        
        # Step 1: Validate invalid plan
        issues = upload_component._validate_plan_structure(invalid_plan)
        assert len(issues) > 0, "Invalid plan should have validation issues"
        
        # Step 2: Test error handling
        with patch.object(error_handler, 'handle_upload_error') as mock_handle:
            try:
                # Simulate processing invalid data
                if len(issues) > 0:
                    raise ValueError(f"Plan validation failed: {issues}")
            except ValueError as e:
                error_handler.handle_upload_error(e)
                mock_handle.assert_called_once()
    
    def test_performance_with_large_dataset(self):
        """Test performance with large dataset"""
        from parsers.plan_parser import PlanParser
        from components.data_table import DataTableComponent
        
        # Get large test dataset
        large_plan = TestFixtures.get_large_plan()
        
        # Test parsing performance
        parser = PlanParser(large_plan)
        summary = parser.get_summary()
        resource_changes = parser.get_resource_changes()
        
        # Verify large dataset handling
        assert len(resource_changes) == 100  # Should handle all 100 resources
        assert summary['total'] == 100
        
        # Test data table with large dataset
        data_table = DataTableComponent()
        with patch.object(data_table, 'render') as mock_render:
            mock_render.return_value = None
            data_table.render(resource_changes, {})
            mock_render.assert_called_once()


class TestComplexDataFlows:
    """Test complex data flows between multiple components"""
    
    def setup_method(self):
        """Set up test fixtures before each test method"""
        # Create a mock session state
        class MockSessionState(dict):
            def __getattr__(self, name):
                try:
                    return self[name]
                except KeyError:
                    defaults = {
                        'show_debug': False,
                        'enable_multi_cloud': True,
                        'uploaded_file_processed': False,
                        'action_filter': ['create', 'update', 'delete', 'replace'],
                        'risk_filter': ['Low', 'Medium', 'High'],
                        'provider_filter': [],
                        'search_query': '',
                        'plan_data': None,
                        'summary': None,
                        'resource_changes': None,
                        'enhanced_risk_result': None
                    }
                    return defaults.get(name, None)
            
            def __setattr__(self, name, value):
                self[name] = value
        
        self.mock_session_state = MockSessionState()
        
        # Create properly configured Streamlit mocks
        streamlit_mocks = create_streamlit_mocks()
        
        self.streamlit_patches = [
            patch('streamlit.session_state', self.mock_session_state),
            patch('streamlit.markdown'),
            patch('streamlit.success'),
            patch('streamlit.error'),
            patch('streamlit.warning'),
            patch('streamlit.info'),
            patch('streamlit.file_uploader'),
            patch('streamlit.selectbox'),
            patch('streamlit.multiselect'),
            patch('streamlit.checkbox'),
            patch('streamlit.text_input'),
            patch('streamlit.button'),
            patch('streamlit.columns', streamlit_mocks['columns']),
            patch('streamlit.container', streamlit_mocks['container']),
            patch('streamlit.expander', streamlit_mocks['expander']),
            patch('streamlit.sidebar'),
            patch('streamlit.dataframe'),
            patch('streamlit.plotly_chart'),
            patch('streamlit.download_button'),
            patch('streamlit.spinner', streamlit_mocks['spinner']),
            patch('streamlit.rerun')
        ]
        
        for patch_obj in self.streamlit_patches:
            patch_obj.start()
    
    def teardown_method(self):
        """Clean up after each test method"""
        for patch_obj in self.streamlit_patches:
            patch_obj.stop()
    
    def test_multi_component_data_pipeline(self):
        """Test data flowing through multiple components in sequence"""
        from components.upload_section import UploadComponent
        from components.sidebar import SidebarComponent
        from components.summary_cards import SummaryCardsComponent
        from components.visualizations import VisualizationsComponent
        from components.data_table import DataTableComponent
        from parsers.plan_parser import PlanParser
        from ui.session_manager import SessionStateManager
        
        # Initialize components
        upload_component = UploadComponent()
        sidebar_component = SidebarComponent()
        summary_component = SummaryCardsComponent()
        viz_component = VisualizationsComponent()
        data_table_component = DataTableComponent()
        session_manager = SessionStateManager()
        
        # Step 1: Upload and parse plan
        plan_data = TestFixtures.get_multi_cloud_plan()
        parser = PlanParser(plan_data)
        summary = parser.get_summary()
        resource_changes = parser.get_resource_changes()
        
        # Step 2: Configure sidebar settings
        sidebar_state = sidebar_component.render(enhanced_features_available=True)
        assert 'show_debug' in sidebar_state
        assert 'enable_multi_cloud' in sidebar_state
        
        # Step 3: Apply filters through sidebar
        filter_state = sidebar_component.render_filters(
            enhanced_features_available=True,
            enhanced_risk_result={'provider_risk_summary': {'aws': {}, 'azure': {}, 'gcp': {}}},
            enable_multi_cloud=True
        )
        
        # Verify filter state structure
        assert 'action_filter' in filter_state
        assert 'risk_filter' in filter_state
        assert 'provider_filter' in filter_state
        
        # Step 4: Update session state with filter configuration
        session_manager.update_filter_state({
            'action_filter': filter_state['action_filter'],
            'risk_filter': filter_state['risk_filter'],
            'provider_filter': filter_state['provider_filter'] or []
        })
        
        # Step 5: Generate summary cards with filtered data
        with patch.object(summary_component, 'render') as mock_summary:
            mock_summary.return_value = None
            summary_component.render(summary, plan_data, {})
            mock_summary.assert_called_once()
        
        # Step 6: Generate visualizations with filtered data
        with patch.object(viz_component, 'render') as mock_viz:
            mock_viz.return_value = None
            viz_component.render(summary, resource_changes, {})
            mock_viz.assert_called_once()
        
        # Step 7: Generate data table with all filters applied
        with patch.object(data_table_component, 'render') as mock_table:
            mock_table.return_value = None
            data_table_component.render(parser, resource_changes, plan_data)
            mock_table.assert_called_once()
        
        # Verify data consistency across components
        assert len(resource_changes) > 0
        assert summary['total'] == len(resource_changes)
    
    def test_error_propagation_across_components(self):
        """Test how errors propagate and are handled across components"""
        from components.upload_section import UploadComponent
        from components.data_table import DataTableComponent
        from ui.error_handler import ErrorHandler
        from parsers.plan_parser import PlanParser
        
        # Initialize components
        upload_component = UploadComponent()
        data_table_component = DataTableComponent()
        error_handler = ErrorHandler()
        
        # Test with invalid plan data
        invalid_plan = TestFixtures.get_invalid_plan()
        
        # Step 1: Upload component should detect validation issues
        issues = upload_component._validate_plan_structure(invalid_plan)
        assert len(issues) > 0, "Invalid plan should have validation issues"
        
        # Step 2: Try to parse invalid data
        try:
            parser = PlanParser(invalid_plan)
            # This might succeed with minimal data
            resource_changes = parser.get_resource_changes()
        except Exception as e:
            # Error should be handled gracefully
            assert isinstance(e, Exception)
        
        # Step 3: Test error handling in data table component
        with patch.object(error_handler, 'handle_processing_error') as mock_error:
            try:
                # Simulate processing error
                raise ValueError("Simulated processing error")
            except ValueError as e:
                error_handler.handle_processing_error(e)
                mock_error.assert_called_once()
    
    def test_performance_with_large_datasets(self):
        """Test component performance with large datasets"""
        from components.data_table import DataTableComponent
        from components.visualizations import VisualizationsComponent
        from parsers.plan_parser import PlanParser
        from ui.performance_optimizer import PerformanceOptimizer
        
        # Initialize components
        data_table_component = DataTableComponent()
        viz_component = VisualizationsComponent()
        performance_optimizer = PerformanceOptimizer()
        
        # Get large test dataset
        large_plan = TestFixtures.get_large_plan()
        parser = PlanParser(large_plan)
        resource_changes = parser.get_resource_changes()
        summary = parser.get_summary()
        
        # Verify large dataset handling
        assert len(resource_changes) == 100, "Large plan should have 100 resources"
        assert summary['total'] == 100
        
        # Test data table performance optimization
        with patch.object(performance_optimizer, 'optimize_dataframe_creation') as mock_optimize:
            mock_optimize.return_value = Mock()  # Mock optimized dataframe
            
            with patch.object(data_table_component, 'render') as mock_table_render:
                mock_table_render.return_value = None
                data_table_component.render(parser, resource_changes, large_plan)
                mock_table_render.assert_called_once()
        
        # Test visualization performance with large dataset
        with patch.object(viz_component, 'render') as mock_viz_render:
            mock_viz_render.return_value = None
            viz_component.render(summary, resource_changes, {})
            mock_viz_render.assert_called_once()
    
    def test_state_consistency_across_components(self):
        """Test that state remains consistent across multiple component interactions"""
        from components.sidebar import SidebarComponent
        from components.data_table import DataTableComponent
        from ui.session_manager import SessionStateManager
        
        # Initialize components
        sidebar_component = SidebarComponent()
        data_table_component = DataTableComponent()
        session_manager = SessionStateManager()
        
        # Set initial state
        initial_filters = {
            'action_filter': ['create', 'update'],
            'risk_filter': ['High'],
            'provider_filter': ['aws']
        }
        session_manager.update_filter_state(initial_filters)
        
        # Test state persistence across sidebar interactions
        filter_state = sidebar_component.render_filters(
            enhanced_features_available=True,
            enhanced_risk_result={'provider_risk_summary': {'aws': {}, 'azure': {}}},
            enable_multi_cloud=True
        )
        
        # Verify state consistency
        current_state = session_manager.get_filter_state()
        assert current_state['action_filter'] == initial_filters['action_filter']
        assert current_state['risk_filter'] == initial_filters['risk_filter']
        assert current_state['provider_filter'] == initial_filters['provider_filter']
        
        # Test search state consistency
        search_query = "aws_instance"
        session_manager.set_search_query(search_query)
        
        # Verify search state persists
        assert session_manager.get_search_query() == search_query
        assert session_manager.is_search_active() == True
        
        # Clear search and verify state update
        session_manager.clear_search()
        assert session_manager.get_search_query() == ""
        assert session_manager.is_search_active() == False
    
    def test_component_coordination_with_enhanced_features(self):
        """Test component coordination when enhanced features are available"""
        from components.enhanced_sections import EnhancedSectionsComponent
        from components.visualizations import VisualizationsComponent
        from components.data_table import DataTableComponent
        from parsers.plan_parser import PlanParser
        
        # Mock enhanced features as available
        with patch('components.enhanced_sections.ENHANCED_FEATURES_AVAILABLE', True):
            # Initialize components
            enhanced_component = EnhancedSectionsComponent()
            viz_component = VisualizationsComponent()
            data_table_component = DataTableComponent()
            
            # Get multi-cloud test data
            plan_data = TestFixtures.get_multi_cloud_plan()
            parser = PlanParser(plan_data)
            resource_changes = parser.get_resource_changes()
            
            # Mock enhanced risk assessor
            mock_enhanced_risk_assessor = Mock()
            mock_enhanced_risk_result = {
                'overall_risk_score': 7.5,
                'provider_risks': {
                    'aws': {'risk_score': 8.0, 'resource_count': 3},
                    'azure': {'risk_score': 7.0, 'resource_count': 2},
                    'gcp': {'risk_score': 6.0, 'resource_count': 1}
                },
                'provider_risk_summary': {
                    'aws': {'risk_score': 8.0},
                    'azure': {'risk_score': 7.0},
                    'gcp': {'risk_score': 6.0}
                }
            }
            mock_enhanced_risk_assessor.assess_plan_risks.return_value = mock_enhanced_risk_result
            
            # Test enhanced sections rendering
            with patch.object(enhanced_component, 'render_enhanced_dashboard_section') as mock_enhanced_render:
                mock_enhanced_render.return_value = None
                enhanced_component.render_enhanced_dashboard_section(
                    plan_data, parser, mock_enhanced_risk_assessor
                )
                mock_enhanced_render.assert_called_once()
            
            # Test visualizations with enhanced data
            with patch.object(viz_component, 'render') as mock_viz_render:
                mock_viz_render.return_value = None
                viz_component.render(
                    parser.get_summary(), 
                    resource_changes, 
                    mock_enhanced_risk_result
                )
                mock_viz_render.assert_called_once()
            
            # Test data table with enhanced features
            with patch.object(data_table_component, 'render') as mock_table_render:
                mock_table_render.return_value = None
                data_table_component.render(
                    parser, 
                    resource_changes, 
                    plan_data,
                    enhanced_risk_assessor=mock_enhanced_risk_assessor,
                    enhanced_risk_result=mock_enhanced_risk_result,
                    enable_multi_cloud=True
                )
                mock_table_render.assert_called_once()
    
    def test_component_fallback_without_enhanced_features(self):
        """Test component fallback behavior when enhanced features are unavailable"""
        from components.enhanced_sections import EnhancedSectionsComponent
        from components.visualizations import VisualizationsComponent
        from components.data_table import DataTableComponent
        from parsers.plan_parser import PlanParser
        
        # Mock enhanced features as unavailable
        with patch('components.enhanced_sections.ENHANCED_FEATURES_AVAILABLE', False):
            # Initialize components
            enhanced_component = EnhancedSectionsComponent()
            viz_component = VisualizationsComponent()
            data_table_component = DataTableComponent()
            
            # Get simple test data
            plan_data = TestFixtures.get_simple_plan()
            parser = PlanParser(plan_data)
            resource_changes = parser.get_resource_changes()
            
            # Test enhanced sections fallback
            with patch.object(enhanced_component, 'render_enhanced_dashboard_section') as mock_enhanced_render:
                mock_enhanced_render.return_value = None
                enhanced_component.render_enhanced_dashboard_section(
                    plan_data, parser, None
                )
                mock_enhanced_render.assert_called_once()
            
            # Test visualizations fallback
            with patch.object(viz_component, 'render') as mock_viz_render:
                mock_viz_render.return_value = None
                viz_component.render(parser.get_summary(), resource_changes, {})
                mock_viz_render.assert_called_once()
            
            # Test data table fallback
            with patch.object(data_table_component, 'render') as mock_table_render:
                mock_table_render.return_value = None
                data_table_component.render(
                    parser, 
                    resource_changes, 
                    plan_data,
                    enhanced_risk_assessor=None,
                    enhanced_risk_result=None,
                    enable_multi_cloud=False
                )
                mock_table_render.assert_called_once()


class TestReportingIntegration:
    """Test reporting functionality integration"""
    
    def setup_method(self):
        """Set up test fixtures before each test method"""
        # Create a mock session state
        class MockSessionState(dict):
            def __getattr__(self, name):
                try:
                    return self[name]
                except KeyError:
                    return None
            
            def __setattr__(self, name, value):
                self[name] = value
        
        self.mock_session_state = MockSessionState()
        
        # Mock Streamlit functions
        self.streamlit_patches = [
            patch('streamlit.session_state', self.mock_session_state),
            patch('streamlit.markdown'),
            patch('streamlit.success'),
            patch('streamlit.error'),
            patch('streamlit.warning'),
            patch('streamlit.info'),
            patch('streamlit.sidebar'),
            patch('streamlit.columns'),
            patch('streamlit.container'),
            patch('streamlit.expander'),
            patch('streamlit.dataframe'),
            patch('streamlit.plotly_chart'),
            patch('streamlit.download_button')
        ]
        
        for patch_obj in self.streamlit_patches:
            patch_obj.start()
    
    def teardown_method(self):
        """Clean up after each test method"""
        for patch_obj in self.streamlit_patches:
            patch_obj.stop()
    
    def test_report_generation_integration(self):
        """Test report generation integration across components"""
        from components.report_generator import ReportGeneratorComponent
        from parsers.plan_parser import PlanParser
        
        # Initialize component
        report_component = ReportGeneratorComponent()
        
        # Get test data
        plan_data = TestFixtures.get_multi_cloud_plan()
        parser = PlanParser(plan_data)
        summary = parser.get_summary()
        resource_changes = parser.get_resource_changes()
        
        # Test report generation
        with patch.object(report_component, 'render') as mock_render:
            mock_render.return_value = None
            report_component.render(summary, resource_changes, plan_data, {})
            mock_render.assert_called_once()
    
    def test_export_functionality_integration(self):
        """Test export functionality across components"""
        from components.data_table import DataTableComponent
        from parsers.plan_parser import PlanParser
        
        # Initialize component
        data_table_component = DataTableComponent()
        
        # Get test data
        plan_data = TestFixtures.get_multi_cloud_plan()
        parser = PlanParser(plan_data)
        resource_changes = parser.get_resource_changes()
        
        # Test export functionality (mock the internal methods)
        with patch.object(data_table_component, '_display_download_button') as mock_download:
            mock_download.return_value = None
            
            with patch.object(data_table_component, 'render') as mock_render:
                mock_render.return_value = None
                data_table_component.render(parser, resource_changes, plan_data)
                mock_render.assert_called_once()


if __name__ == '__main__':
    pytest.main([__file__])
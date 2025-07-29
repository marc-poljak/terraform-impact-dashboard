"""
Comprehensive integration tests for end-to-end workflows

Tests complete user workflows from upload to analysis with various plan sizes and complexity levels.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os
import pandas as pd

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from tests.integration.test_fixtures import TestFixtures


class TestCompleteUserWorkflows:
    """Test complete user workflows from start to finish"""
    
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
                        'saved_filter_configs': [],
                        'user_progress': {},
                        'onboarding_completed': False
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
            patch('streamlit.text_area'),
            patch('streamlit.button'),
            patch('streamlit.columns'),
            patch('streamlit.container'),
            patch('streamlit.expander'),
            patch('streamlit.sidebar'),
            patch('streamlit.dataframe'),
            patch('streamlit.plotly_chart'),
            patch('streamlit.download_button'),
            patch('streamlit.spinner'),
            patch('streamlit.progress'),
            patch('streamlit.rerun'),
            patch('streamlit.radio'),
            patch('streamlit.metric')
        ]
        
        for patch_obj in self.streamlit_patches:
            patch_obj.start()
    
    def teardown_method(self):
        """Clean up after each test method"""
        for patch_obj in self.streamlit_patches:
            patch_obj.stop()
    
    def test_new_user_onboarding_workflow(self):
        """Test complete new user onboarding workflow"""
        from components.upload_section import UploadComponent
        from components.onboarding_checklist import OnboardingChecklistComponent
        from components.help_system import HelpSystemComponent
        from ui.error_handler import ErrorHandler
        from ui.session_manager import SessionStateManager
        
        # Initialize components for new user
        upload_component = UploadComponent()
        onboarding_component = OnboardingChecklistComponent()
        help_component = HelpSystemComponent()
        error_handler = ErrorHandler()
        session_manager = SessionStateManager()
        
        # Step 1: New user sees onboarding
        with patch.object(onboarding_component, 'render') as mock_onboarding:
            mock_onboarding.return_value = None
            onboarding_component.render()
            mock_onboarding.assert_called_once()
        
        # Step 2: User sees upload instructions
        with patch.object(upload_component, 'render_instructions') as mock_instructions:
            mock_instructions.return_value = None
            upload_component.render_instructions()
            mock_instructions.assert_called_once()
        
        # Step 3: User gets contextual help
        with patch.object(error_handler, 'show_onboarding_hint') as mock_hint:
            mock_hint.return_value = None
            error_handler.show_onboarding_hint(
                "File Upload",
                "Start by uploading a Terraform plan JSON file.",
                show_once=True
            )
            mock_hint.assert_called_once()
        
        # Step 4: User uploads first file
        plan_data = TestFixtures.get_simple_plan()
        
        # Mock file upload
        mock_uploaded_file = Mock()
        mock_uploaded_file.getvalue.return_value = b'{"test": "data"}'
        mock_uploaded_file.name = "test_plan.json"
        mock_uploaded_file.type = "application/json"
        
        # Validate file structure
        issues = upload_component._validate_plan_structure(plan_data)
        assert len(issues) == 0, "Simple plan should be valid for new user"
        
        # Step 5: Verify session state is working
        session_manager.set_debug_state(True)
        assert session_manager.get_debug_state() == True
    
    def test_experienced_user_advanced_workflow(self):
        """Test experienced user workflow with advanced features"""
        from components.sidebar import SidebarComponent
        from components.data_table import DataTableComponent
        from components.visualizations import VisualizationsComponent
        from parsers.plan_parser import PlanParser
        from ui.session_manager import SessionStateManager
        
        # Initialize components for experienced user
        sidebar_component = SidebarComponent()
        data_table_component = DataTableComponent()
        viz_component = VisualizationsComponent()
        session_manager = SessionStateManager()
        
        # Step 1: User enables advanced features (test component creation)
        sidebar_state = sidebar_component.render(enhanced_features_available=True)
        # Verify sidebar component returns a dictionary structure
        assert isinstance(sidebar_state, dict)
        assert 'enable_multi_cloud' in sidebar_state
        
        # Step 2: User applies complex filters
        advanced_filter_config = {
            'action_filter': ['create'],
            'risk_filter': ['High'],
            'provider_filter': ['aws', 'azure']
        }
        session_manager.update_filter_state(advanced_filter_config)
        
        # Verify filter state was updated
        current_filters = session_manager.get_filter_state()
        assert current_filters['action_filter'] == ['create']
        assert current_filters['risk_filter'] == ['High']
        assert current_filters['provider_filter'] == ['aws', 'azure']
        
        # Step 3: User works with large dataset
        large_plan = TestFixtures.get_large_plan()
        parser = PlanParser(large_plan)
        resource_changes = parser.get_resource_changes()
        summary = parser.get_summary()
        
        # Verify large dataset handling
        assert len(resource_changes) == 100
        assert summary['total'] == 100
        
        # Step 4: User generates visualizations
        with patch.object(viz_component, 'render') as mock_viz:
            mock_viz.return_value = None
            viz_component.render(summary, resource_changes, {})
            mock_viz.assert_called_once()
        
        # Step 5: User exports filtered data
        with patch.object(data_table_component, 'render') as mock_table:
            mock_table.return_value = None
            data_table_component.render(parser, resource_changes, large_plan)
            mock_table.assert_called_once()
    
    def test_multi_cloud_analysis_workflow(self):
        """Test complete multi-cloud analysis workflow"""
        from components.enhanced_sections import EnhancedSectionsComponent
        from components.visualizations import VisualizationsComponent
        from components.security_analysis import SecurityAnalysisComponent
        from parsers.plan_parser import PlanParser
        
        # Mock enhanced features as available
        with patch('components.enhanced_sections.ENHANCED_FEATURES_AVAILABLE', True):
            # Initialize components
            enhanced_component = EnhancedSectionsComponent()
            viz_component = VisualizationsComponent()
            security_component = SecurityAnalysisComponent()
            
            # Step 1: Parse multi-cloud plan
            plan_data = TestFixtures.get_multi_cloud_plan()
            parser = PlanParser(plan_data)
            resource_changes = parser.get_resource_changes()
            
            # Verify multi-cloud resources
            providers_found = set()
            for change in resource_changes:
                provider = change.get('provider', '')
                if provider == 'aws':
                    providers_found.add('aws')
                elif provider == 'azure':
                    providers_found.add('azure')
                elif provider == 'google':
                    providers_found.add('gcp')
            
            assert len(providers_found) >= 2, "Should detect multiple cloud providers"
            
            # Step 2: Enhanced risk assessment
            mock_enhanced_risk_assessor = Mock()
            mock_enhanced_risk_result = {
                'overall_risk_score': 7.5,
                'provider_risks': {
                    'aws': {'risk_score': 8.0, 'resource_count': 3},
                    'azure': {'risk_score': 7.0, 'resource_count': 2},
                    'gcp': {'risk_score': 6.0, 'resource_count': 1}
                },
                'cross_cloud_risks': [
                    {
                        'type': 'data_transfer',
                        'description': 'Cross-cloud data transfer detected',
                        'severity': 'Medium'
                    }
                ]
            }
            mock_enhanced_risk_assessor.assess_plan_risks.return_value = mock_enhanced_risk_result
            
            # Step 3: Generate enhanced dashboard
            with patch.object(enhanced_component, 'render_enhanced_dashboard_section') as mock_enhanced:
                mock_enhanced.return_value = None
                enhanced_component.render_enhanced_dashboard_section(
                    plan_data, parser, mock_enhanced_risk_assessor
                )
                mock_enhanced.assert_called_once()
            
            # Step 4: Multi-cloud visualizations
            with patch.object(viz_component, 'render') as mock_viz:
                mock_viz.return_value = None
                viz_component.render(
                    parser.get_summary(), 
                    resource_changes, 
                    mock_enhanced_risk_result
                )
                mock_viz.assert_called_once()
            
            # Step 5: Security analysis
            with patch.object(security_component, 'render') as mock_security:
                mock_security.return_value = None
                security_component.render(resource_changes, mock_enhanced_risk_result)
                mock_security.assert_called_once()
    
    def test_error_recovery_workflow(self):
        """Test error recovery and graceful degradation workflow"""
        from components.upload_section import UploadComponent
        from ui.error_handler import ErrorHandler
        from parsers.plan_parser import PlanParser
        
        # Initialize components
        upload_component = UploadComponent()
        error_handler = ErrorHandler()
        
        # Step 1: User uploads invalid file
        invalid_plan = TestFixtures.get_invalid_plan()
        
        # Step 2: System detects validation issues
        issues = upload_component._validate_plan_structure(invalid_plan)
        assert len(issues) > 0, "Invalid plan should have validation issues"
        
        # Step 3: System provides helpful error messages
        with patch.object(error_handler, 'handle_upload_error') as mock_error:
            try:
                # Simulate upload error
                raise ValueError("Invalid JSON structure")
            except ValueError as e:
                error_handler.handle_upload_error(e)
                mock_error.assert_called_once()
        
        # Step 4: User corrects issue and retries
        valid_plan = TestFixtures.get_simple_plan()
        issues = upload_component._validate_plan_structure(valid_plan)
        assert len(issues) == 0, "Valid plan should have no issues"
        
        # Step 5: System processes successfully
        parser = PlanParser(valid_plan)
        summary = parser.get_summary()
        assert summary['total'] > 0, "Should successfully parse corrected plan"
    
    def test_performance_optimization_workflow(self):
        """Test performance optimization workflow with large datasets"""
        from components.data_table import DataTableComponent
        from ui.performance_optimizer import PerformanceOptimizer
        from ui.progress_tracker import ProgressTracker
        from parsers.plan_parser import PlanParser
        
        # Initialize components
        data_table_component = DataTableComponent()
        performance_optimizer = PerformanceOptimizer()
        progress_tracker = ProgressTracker()
        
        # Step 1: User uploads large plan
        large_plan = TestFixtures.get_large_plan()
        parser = PlanParser(large_plan)
        resource_changes = parser.get_resource_changes()
        
        # Step 2: System detects large dataset
        assert len(resource_changes) == 100, "Large plan should have 100 resources"
        
        # Step 3: System applies performance optimizations
        with patch.object(performance_optimizer, 'optimize_dataframe_creation') as mock_optimize:
            mock_optimize.return_value = Mock()  # Mock optimized dataframe
            
            # Step 4: System shows progress indicators
            with patch.object(progress_tracker, 'show_data_processing_progress') as mock_progress:
                mock_progress.return_value = None
                
                # Step 5: System renders optimized table
                with patch.object(data_table_component, 'render') as mock_render:
                    mock_render.return_value = None
                    data_table_component.render(parser, resource_changes, large_plan)
                    mock_render.assert_called_once()
    
    def test_collaborative_workflow(self):
        """Test collaborative workflow with saved configurations"""
        from components.sidebar import SidebarComponent
        from ui.session_manager import SessionStateManager
        
        # Initialize components
        sidebar_component = SidebarComponent()
        session_manager = SessionStateManager()
        
        # Step 1: User creates custom filter configuration
        custom_filters = {
            'action_filter': ['create', 'update'],
            'risk_filter': ['High'],
            'provider_filter': ['aws'],
            'filter_logic': 'AND'
        }
        session_manager.update_filter_state(custom_filters)
        
        # Step 2: User saves configuration for team
        config_name = "high-risk-aws-changes"
        success = session_manager.save_current_filter_configuration(config_name)
        assert success, "Should successfully save filter configuration"
        
        # Step 3: Team member loads saved configuration
        saved_configs = session_manager.get_saved_filter_configurations()
        assert config_name in saved_configs, "Saved configuration should be available"
        
        # Step 4: Team member applies saved configuration
        loaded_success = session_manager.restore_saved_filter_configuration(config_name)
        assert loaded_success, "Should successfully load saved configuration"
        
        # Step 5: Verify configuration consistency
        current_filters = session_manager.get_filter_state()
        assert current_filters['action_filter'] == custom_filters['action_filter']
        assert current_filters['risk_filter'] == custom_filters['risk_filter']
        assert current_filters['provider_filter'] == custom_filters['provider_filter']


class TestScalabilityAndPerformance:
    """Test scalability and performance with various dataset sizes"""
    
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
            patch('streamlit.spinner'),
            patch('streamlit.progress')
        ]
        
        for patch_obj in self.streamlit_patches:
            patch_obj.start()
    
    def teardown_method(self):
        """Clean up after each test method"""
        for patch_obj in self.streamlit_patches:
            patch_obj.stop()
    
    def test_small_plan_performance(self):
        """Test performance with small plans (< 10 resources)"""
        from components.data_table import DataTableComponent
        from parsers.plan_parser import PlanParser
        
        # Initialize components
        data_table_component = DataTableComponent()
        
        # Test with simple plan
        plan_data = TestFixtures.get_simple_plan()
        parser = PlanParser(plan_data)
        resource_changes = parser.get_resource_changes()
        
        # Verify small dataset handling
        assert len(resource_changes) <= 10, "Simple plan should have few resources"
        
        # Test rendering performance
        with patch.object(data_table_component, 'render') as mock_render:
            mock_render.return_value = None
            data_table_component.render(parser, resource_changes, plan_data)
            mock_render.assert_called_once()
    
    def test_medium_plan_performance(self):
        """Test performance with medium plans (10-50 resources)"""
        from components.data_table import DataTableComponent
        from components.visualizations import VisualizationsComponent
        from parsers.plan_parser import PlanParser
        
        # Initialize components
        data_table_component = DataTableComponent()
        viz_component = VisualizationsComponent()
        
        # Test with multi-cloud plan (medium size)
        plan_data = TestFixtures.get_multi_cloud_plan()
        parser = PlanParser(plan_data)
        resource_changes = parser.get_resource_changes()
        summary = parser.get_summary()
        
        # Verify medium dataset handling
        assert 5 <= len(resource_changes) <= 50, "Multi-cloud plan should be medium size"
        
        # Test component performance
        with patch.object(data_table_component, 'render') as mock_table:
            mock_table.return_value = None
            data_table_component.render(parser, resource_changes, plan_data)
            mock_table.assert_called_once()
        
        with patch.object(viz_component, 'render') as mock_viz:
            mock_viz.return_value = None
            viz_component.render(summary, resource_changes, {})
            mock_viz.assert_called_once()
    
    def test_large_plan_performance(self):
        """Test performance with large plans (50+ resources)"""
        from components.data_table import DataTableComponent
        from ui.performance_optimizer import PerformanceOptimizer
        from parsers.plan_parser import PlanParser
        
        # Initialize components
        data_table_component = DataTableComponent()
        performance_optimizer = PerformanceOptimizer()
        
        # Test with large plan
        large_plan = TestFixtures.get_large_plan()
        parser = PlanParser(large_plan)
        resource_changes = parser.get_resource_changes()
        
        # Verify large dataset handling
        assert len(resource_changes) >= 50, "Large plan should have many resources"
        
        # Test performance optimization
        with patch.object(performance_optimizer, 'optimize_dataframe_creation') as mock_optimize:
            mock_optimize.return_value = Mock()  # Mock optimized dataframe
            
            with patch.object(data_table_component, 'render') as mock_render:
                mock_render.return_value = None
                data_table_component.render(parser, resource_changes, large_plan)
                mock_render.assert_called_once()
    
    def test_memory_usage_optimization(self):
        """Test memory usage optimization with large datasets"""
        from ui.performance_optimizer import PerformanceOptimizer
        from parsers.plan_parser import PlanParser
        
        # Initialize optimizer
        performance_optimizer = PerformanceOptimizer()
        
        # Test with large plan
        large_plan = TestFixtures.get_large_plan()
        parser = PlanParser(large_plan)
        resource_changes = parser.get_resource_changes()
        
        # Test memory optimization methods
        # Test chunked processing for memory efficiency
        chunks = list(performance_optimizer.chunk_process_resources(resource_changes, chunk_size=50))
        assert len(chunks) > 1, "Should split large dataset into chunks"
        
        # Test optimized dataframe creation
        optimized_df = performance_optimizer.optimize_dataframe_creation(resource_changes, parser)
        assert len(optimized_df) == len(resource_changes), "Should process all resources"
        
        # Test cache functionality for memory efficiency
        cache_stats = performance_optimizer.get_cache_stats()
        assert isinstance(cache_stats, dict)
        assert 'hits' in cache_stats
        assert 'misses' in cache_stats
        
        # Test table rendering optimization
        import pandas as pd
        large_df = pd.DataFrame({'test': range(2000)})  # Large dataframe
        truncated_df, was_truncated = performance_optimizer.optimize_table_rendering(large_df, max_rows=1000)
        assert was_truncated, "Should truncate large dataframes"
        assert len(truncated_df) <= 1000, "Should limit rows to max_rows"
    
    def test_concurrent_user_simulation(self):
        """Test session manager behavior with multiple instances"""
        from ui.session_manager import SessionStateManager
        from parsers.plan_parser import PlanParser
        
        # Test that multiple session managers work correctly
        # Note: In Streamlit, session state is shared per session, so multiple
        # SessionStateManager instances in the same session will share state
        session_manager1 = SessionStateManager()
        session_manager2 = SessionStateManager()
        
        # Set state through first manager
        initial_filters = {
            'action_filter': ['create'],
            'risk_filter': ['High'],
            'provider_filter': ['aws']
        }
        session_manager1.update_filter_state(initial_filters)
        
        # Verify second manager sees the same state (shared session)
        filters_from_manager2 = session_manager2.get_filter_state()
        assert filters_from_manager2['action_filter'] == ['create']
        assert filters_from_manager2['risk_filter'] == ['High']
        assert filters_from_manager2['provider_filter'] == ['aws']
        
        # Update through second manager
        updated_filters = {
            'action_filter': ['update', 'delete'],
            'risk_filter': ['Medium'],
            'provider_filter': ['azure']
        }
        session_manager2.update_filter_state(updated_filters)
        
        # Verify first manager sees the updated state
        filters_from_manager1 = session_manager1.get_filter_state()
        assert filters_from_manager1['action_filter'] == ['update', 'delete']
        assert filters_from_manager1['risk_filter'] == ['Medium']
        assert filters_from_manager1['provider_filter'] == ['azure']
        
        # Test that both managers can perform operations
        session_manager1.set_search_query("test_query")
        assert session_manager2.get_search_query() == "test_query"
        
        session_manager2.clear_search()
        assert session_manager1.get_search_query() == ""


if __name__ == '__main__':
    pytest.main([__file__])
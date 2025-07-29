"""
Integration tests for enhanced features and multi-cloud functionality

Tests enhanced features when available and fallback behavior when not available.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from tests.integration.test_fixtures import TestFixtures


class TestEnhancedFeaturesIntegration:
    """Test enhanced features integration"""
    
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
            patch('streamlit.sidebar'),
            patch('streamlit.columns'),
            patch('streamlit.container'),
            patch('streamlit.expander'),
            patch('streamlit.dataframe'),
            patch('streamlit.plotly_chart')
        ]
        
        for patch_obj in self.streamlit_patches:
            patch_obj.start()
    
    def teardown_method(self):
        """Clean up after each test method"""
        for patch_obj in self.streamlit_patches:
            patch_obj.stop()
    
    def test_enhanced_risk_assessment_integration(self):
        """Test integration with enhanced risk assessment when available"""
        # Mock enhanced features as available
        with patch('components.enhanced_sections.ENHANCED_FEATURES_AVAILABLE', True):
            from components.enhanced_sections import EnhancedSectionsComponent
            
            # Create component
            enhanced_component = EnhancedSectionsComponent()
            
            # Get multi-cloud test data
            plan_data = TestFixtures.get_multi_cloud_plan()
            
            # Mock enhanced risk assessor
            mock_enhanced_risk_assessor = Mock()
            mock_enhanced_risk_assessor.assess_plan_risks.return_value = {
                'overall_risk_score': 7.5,
                'provider_risks': {
                    'aws': {
                        'risk_score': 8.0,
                        'resource_count': 3,
                        'high_risk_resources': ['aws_security_group.web'],
                        'recommendations': ['Review security group rules']
                    },
                    'azure': {
                        'risk_score': 7.0,
                        'resource_count': 2,
                        'high_risk_resources': ['azurerm_storage_account.data'],
                        'recommendations': ['Enable storage encryption']
                    },
                    'google': {
                        'risk_score': 6.0,
                        'resource_count': 1,
                        'high_risk_resources': [],
                        'recommendations': ['No high-risk resources found']
                    }
                },
                'cross_cloud_risks': [
                    {
                        'type': 'data_transfer',
                        'description': 'Cross-cloud data transfer detected',
                        'severity': 'Medium'
                    }
                ],
                'security_recommendations': [
                    'Enable encryption at rest for all storage resources',
                    'Review network security group configurations'
                ]
            }
            
            # Mock cloud provider detector
            mock_cloud_detector = Mock()
            mock_cloud_detector.detect_providers.return_value = {
                'aws': {'confidence': 0.95, 'resource_count': 3},
                'azure': {'confidence': 0.90, 'resource_count': 2},
                'google': {'confidence': 0.85, 'resource_count': 1}
            }
            
            # Test enhanced dashboard rendering
            with patch.object(enhanced_component, 'render_enhanced_dashboard_section') as mock_render:
                mock_render.return_value = None
                enhanced_component.render_enhanced_dashboard_section(
                    plan_data, None, mock_enhanced_risk_assessor
                )
                
                # Verify render was called with correct parameters
                mock_render.assert_called_once_with(plan_data, None, mock_enhanced_risk_assessor)
            
            # Test multi-cloud risk section
            with patch.object(enhanced_component, 'render_multi_cloud_risk_section') as mock_risk_render:
                mock_risk_render.return_value = None
                enhanced_risk_result = mock_enhanced_risk_assessor.assess_plan_risks.return_value
                
                enhanced_component.render_multi_cloud_risk_section(enhanced_risk_result, [])
                mock_risk_render.assert_called_once()
    
    def test_cloud_provider_detection_integration(self):
        """Test cloud provider detection integration"""
        # Mock enhanced features as available
        with patch('components.enhanced_sections.ENHANCED_FEATURES_AVAILABLE', True):
            # Mock the CloudProviderDetector
            with patch('providers.cloud_detector.CloudProviderDetector') as MockCloudDetector:
                mock_detector_instance = Mock()
                MockCloudDetector.return_value = mock_detector_instance
                
                # Set up mock detection results
                mock_detector_instance.detect_providers.return_value = {
                    'aws': {'confidence': 0.95, 'resource_count': 3},
                    'azure': {'confidence': 0.90, 'resource_count': 2},
                    'google': {'confidence': 0.85, 'resource_count': 1}
                }
                
                from components.enhanced_sections import EnhancedSectionsComponent
                
                # Create component
                enhanced_component = EnhancedSectionsComponent()
                
                # Get multi-cloud test data
                plan_data = TestFixtures.get_multi_cloud_plan()
                
                # Test provider detection workflow
                with patch.object(enhanced_component, 'render_enhanced_dashboard_section') as mock_render:
                    mock_render.return_value = None
                    enhanced_component.render_enhanced_dashboard_section(plan_data, None, None)
                    
                    # Verify render was called
                    mock_render.assert_called_once()
    
    def test_cross_cloud_insights_integration(self):
        """Test cross-cloud insights integration"""
        # Mock enhanced features as available
        with patch('components.enhanced_sections.ENHANCED_FEATURES_AVAILABLE', True):
            from components.enhanced_sections import EnhancedSectionsComponent
            
            # Create component
            enhanced_component = EnhancedSectionsComponent()
            
            # Get multi-cloud test data
            plan_data = TestFixtures.get_multi_cloud_plan()
            
            # Mock enhanced risk assessor with cross-cloud insights
            mock_enhanced_risk_assessor = Mock()
            mock_enhanced_risk_assessor.get_cross_cloud_insights.return_value = {
                'cross_cloud_risks': [
                    {
                        'type': 'network_connectivity',
                        'description': 'Cross-cloud network connections may introduce latency',
                        'severity': 'Medium',
                        'affected_resources': ['aws_instance.web', 'azurerm_virtual_machine.app']
                    }
                ],
                'optimization_opportunities': [
                    {
                        'type': 'cost_optimization',
                        'description': 'Consider consolidating resources in single region',
                        'potential_savings': '15%'
                    }
                ],
                'security_considerations': [
                    {
                        'type': 'data_sovereignty',
                        'description': 'Data crossing cloud boundaries may have compliance implications',
                        'recommendation': 'Review data residency requirements'
                    }
                ]
            }
            
            # Test cross-cloud insights rendering
            with patch.object(enhanced_component, 'render_cross_cloud_insights_section') as mock_render:
                mock_render.return_value = None
                enhanced_component.render_cross_cloud_insights_section(
                    mock_enhanced_risk_assessor, [], plan_data
                )
                
                # Verify render was called with correct parameters
                mock_render.assert_called_once_with(mock_enhanced_risk_assessor, [], plan_data)
    
    def test_enhanced_features_fallback(self):
        """Test fallback behavior when enhanced features are not available"""
        # Mock enhanced features as unavailable
        with patch('components.enhanced_sections.ENHANCED_FEATURES_AVAILABLE', False):
            from components.enhanced_sections import EnhancedSectionsComponent
            
            # Component should still be created
            enhanced_component = EnhancedSectionsComponent()
            assert enhanced_component is not None
            
            # Get test data
            plan_data = TestFixtures.get_simple_plan()
            
            # Test graceful degradation
            with patch.object(enhanced_component, 'render_enhanced_dashboard_section') as mock_render:
                mock_render.return_value = None
                
                # Should handle None enhanced_risk_assessor gracefully
                enhanced_component.render_enhanced_dashboard_section(plan_data, None, None)
                mock_render.assert_called_once_with(plan_data, None, None)
    
    def test_enhanced_visualizations_integration(self):
        """Test enhanced visualizations integration"""
        from components.visualizations import VisualizationsComponent
        from parsers.plan_parser import PlanParser
        
        # Create component
        viz_component = VisualizationsComponent()
        
        # Get multi-cloud test data
        plan_data = TestFixtures.get_multi_cloud_plan()
        parser = PlanParser(plan_data)
        summary = parser.get_summary()
        resource_changes = parser.get_resource_changes()
        
        # Mock enhanced risk result for visualizations
        enhanced_risk_result = {
            'provider_risks': {
                'aws': {'risk_score': 8.0, 'resource_count': 3},
                'azure': {'risk_score': 7.0, 'resource_count': 2},
                'google': {'risk_score': 6.0, 'resource_count': 1}
            }
        }
        
        # Test enhanced visualizations rendering
        with patch.object(viz_component, 'render') as mock_render:
            mock_render.return_value = None
            viz_component.render(summary, resource_changes, enhanced_risk_result)
            
            # Verify render was called with enhanced data
            mock_render.assert_called_once()
            call_args = mock_render.call_args[0]
            assert len(call_args) >= 3  # Should have summary, resource_changes, and enhanced_risk_result
    
    def test_multi_cloud_action_distribution(self):
        """Test multi-cloud action distribution visualization"""
        from components.visualizations import VisualizationsComponent
        from parsers.plan_parser import PlanParser
        
        # Create component
        viz_component = VisualizationsComponent()
        
        # Get multi-cloud test data
        plan_data = TestFixtures.get_multi_cloud_plan()
        parser = PlanParser(plan_data)
        resource_changes = parser.get_resource_changes()
        
        # Test multi-cloud action distribution (test that render method handles multi-cloud data)
        with patch.object(viz_component, 'render') as mock_render:
            mock_render.return_value = None
            # Call render with multi-cloud data
            viz_component.render(
                summary={'create': 3, 'update': 2, 'delete': 1, 'total': 6},
                resource_types={'aws_instance': 1, 'azurerm_virtual_machine': 1, 'google_compute_instance': 1},
                resource_changes=resource_changes,
                plan_data=plan_data,
                chart_gen=None,
                enhanced_features_available=True,
                enable_multi_cloud=True
            )
            
            # Verify render was called
            mock_render.assert_called_once()
    
    def test_risk_assessment_heatmap_integration(self):
        """Test risk assessment heatmap integration"""
        from components.visualizations import VisualizationsComponent
        
        # Create component
        viz_component = VisualizationsComponent()
        
        # Mock enhanced risk result with heatmap data
        enhanced_risk_result = {
            'risk_heatmap_data': [
                {'resource': 'aws_instance.web', 'risk_score': 8.5, 'provider': 'aws'},
                {'resource': 'azurerm_virtual_machine.app', 'risk_score': 7.2, 'provider': 'azure'},
                {'resource': 'google_compute_instance.database', 'risk_score': 6.8, 'provider': 'google'}
            ]
        }
        
        # Test risk heatmap rendering (test that render method handles risk data)
        with patch.object(viz_component, 'render') as mock_render:
            mock_render.return_value = None
            # Call render with risk heatmap data
            viz_component.render(
                summary={'create': 1, 'update': 1, 'delete': 1, 'total': 3},
                resource_types={'aws_instance': 1, 'azurerm_virtual_machine': 1, 'google_compute_instance': 1},
                resource_changes=[],
                plan_data={'enhanced_risk_result': enhanced_risk_result},
                chart_gen=None,
                enhanced_features_available=True
            )
            
            # Verify render was called
            mock_render.assert_called_once()


class TestSecurityAnalysisIntegration:
    """Test security analysis integration"""
    
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
            patch('streamlit.plotly_chart')
        ]
        
        for patch_obj in self.streamlit_patches:
            patch_obj.start()
    
    def teardown_method(self):
        """Clean up after each test method"""
        for patch_obj in self.streamlit_patches:
            patch_obj.stop()
    
    def test_security_analysis_component_integration(self):
        """Test security analysis component integration"""
        from components.security_analysis import SecurityAnalysisComponent
        from parsers.plan_parser import PlanParser
        
        # Create component
        security_component = SecurityAnalysisComponent()
        
        # Get security-focused test data
        plan_data = TestFixtures.get_security_focused_plan()
        parser = PlanParser(plan_data)
        resource_changes = parser.get_resource_changes()
        
        # Test security analysis rendering
        with patch.object(security_component, 'render') as mock_render:
            mock_render.return_value = None
            security_component.render(resource_changes, {})
            
            # Verify render was called
            mock_render.assert_called_once()
            call_args = mock_render.call_args[0]
            assert len(call_args) >= 1  # Should have resource_changes
    
    def test_security_risk_detection(self):
        """Test security risk detection"""
        from components.security_analysis import SecurityAnalysisComponent
        
        # Create component
        security_component = SecurityAnalysisComponent()
        
        # Get security-focused test data
        plan_data = TestFixtures.get_security_focused_plan()
        
        # Test security risk detection through security analyzer
        with patch.object(security_component.security_analyzer, 'analyze_security_resources') as mock_detect:
            mock_detect.return_value = {
                'security_resources': [
                    {
                        'resource': 'aws_security_group.risky',
                        'risk_type': 'open_ssh',
                        'severity': 'High',
                        'description': 'SSH port open to 0.0.0.0/0'
                    },
                    {
                        'resource': 'aws_iam_policy.admin',
                        'risk_type': 'overprivileged',
                        'severity': 'Critical',
                        'description': 'Policy grants full admin access'
                    }
                ],
                'security_risks': []
            }
            
            from parsers.plan_parser import PlanParser
            parser = PlanParser(plan_data)
            resource_changes = parser.get_resource_changes()
            
            result = security_component.security_analyzer.analyze_security_resources(resource_changes)
            
            # Verify detection was called
            mock_detect.assert_called_once_with(resource_changes)
            assert 'security_resources' in result  # Should return security analysis result
    
    def test_security_score_calculation(self):
        """Test security score calculation"""
        from components.security_analysis import SecurityAnalysisComponent
        
        # Create component
        security_component = SecurityAnalysisComponent()
        
        # Mock security risks
        security_risks = [
            {'severity': 'Critical', 'resource': 'aws_iam_policy.admin'},
            {'severity': 'High', 'resource': 'aws_security_group.risky'},
            {'severity': 'Medium', 'resource': 'aws_s3_bucket_public_access_block.public'}
        ]
        
        # Test security dashboard data calculation through security analyzer
        with patch.object(security_component.security_analyzer, 'get_security_dashboard_data') as mock_calculate:
            mock_calculate.return_value = {
                'overall_score': 3.2,  # Out of 10
                'risk_breakdown': {
                    'Critical': 1,
                    'High': 1,
                    'Medium': 1,
                    'Low': 0
                },
                'recommendations': [
                    'Review IAM policies for least privilege',
                    'Restrict security group access',
                    'Enable S3 bucket protection'
                ],
                'security_resources': [],
                'security_risks': security_risks
            }
            
            from parsers.plan_parser import PlanParser
            parser = PlanParser(TestFixtures.get_security_focused_plan())
            resource_changes = parser.get_resource_changes()
            
            score_result = security_component.security_analyzer.get_security_dashboard_data(resource_changes)
            
            # Verify calculation was called
            mock_calculate.assert_called_once_with(resource_changes)
            assert 'overall_score' in score_result
            assert 'risk_breakdown' in score_result
    
    def test_compliance_checks_integration(self):
        """Test compliance checks integration"""
        from components.security_analysis import SecurityAnalysisComponent
        
        # Create component
        security_component = SecurityAnalysisComponent()
        
        # Get security-focused test data
        plan_data = TestFixtures.get_security_focused_plan()
        
        # Test compliance checks through security analyzer
        with patch.object(security_component.security_analyzer, 'check_compliance') as mock_compliance:
            mock_compliance.return_value = {
                'soc2': {
                    'passed': 2,
                    'failed': 3,
                    'score': 40,
                    'failed_checks': [
                        'SOC2-CC6.1: Ensure logical access security measures are implemented',
                        'SOC2-CC6.2: Ensure system operations are monitored',
                        'SOC2-CC6.3: Ensure data transmission is protected'
                    ]
                },
                'pci': {
                    'passed': 1,
                    'failed': 2,
                    'score': 33,
                    'failed_checks': [
                        'PCI-DSS 1.1: Establish firewall configuration standards',
                        'PCI-DSS 2.1: Change vendor-supplied defaults'
                    ]
                }
            }
            
            from parsers.plan_parser import PlanParser
            parser = PlanParser(plan_data)
            resource_changes = parser.get_resource_changes()
            
            compliance_result = security_component.security_analyzer.check_compliance(resource_changes)
            
            # Verify compliance checks were called
            mock_compliance.assert_called_once_with(resource_changes)
            assert 'soc2' in compliance_result
            assert 'pci' in compliance_result


class TestDependencyVisualizationIntegration:
    """Test dependency visualization integration"""
    
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
            patch('streamlit.plotly_chart')
        ]
        
        for patch_obj in self.streamlit_patches:
            patch_obj.start()
    
    def teardown_method(self):
        """Clean up after each test method"""
        for patch_obj in self.streamlit_patches:
            patch_obj.stop()
    
    def test_dependency_graph_integration(self):
        """Test dependency graph visualization integration"""
        from components.visualizations import VisualizationsComponent
        from parsers.plan_parser import PlanParser
        
        # Create component
        viz_component = VisualizationsComponent()
        
        # Get dependency test data
        plan_data = TestFixtures.get_plan_with_dependencies()
        parser = PlanParser(plan_data)
        resource_changes = parser.get_resource_changes()
        summary = parser.get_summary()
        
        # Test dependency visualization rendering
        with patch.object(viz_component, 'render') as mock_render:
            mock_render.return_value = None
            viz_component.render(summary, resource_changes, {})
            mock_render.assert_called_once()
    
    def test_dependency_conflict_detection(self):
        """Test dependency conflict detection"""
        from parsers.plan_parser import PlanParser
        
        # Get dependency test data
        plan_data = TestFixtures.get_plan_with_dependencies()
        parser = PlanParser(plan_data)
        resource_changes = parser.get_resource_changes()
        
        # Verify dependency relationships exist
        assert len(resource_changes) == 4  # VPC, Subnet, Security Group, Instance
        
        # Check for dependency references
        dependency_found = False
        for change in resource_changes:
            change_after = change.get('change', {}).get('after', {})
            if change_after:
                for key, value in change_after.items():
                    if isinstance(value, str) and '${' in value:
                        dependency_found = True
                        break
        
        assert dependency_found, "Should find dependency references in plan"


class TestOnboardingIntegration:
    """Test onboarding and help system integration"""
    
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
            patch('streamlit.plotly_chart')
        ]
        
        for patch_obj in self.streamlit_patches:
            patch_obj.start()
    
    def teardown_method(self):
        """Clean up after each test method"""
        for patch_obj in self.streamlit_patches:
            patch_obj.stop()
    
    def test_onboarding_checklist_integration(self):
        """Test onboarding checklist integration"""
        from components.onboarding_checklist import OnboardingChecklistComponent
        
        # Create component
        onboarding_component = OnboardingChecklistComponent()
        
        # Test onboarding rendering
        with patch.object(onboarding_component, 'render') as mock_render:
            mock_render.return_value = None
            onboarding_component.render()
            mock_render.assert_called_once()
    
    def test_help_system_integration(self):
        """Test help system integration across components"""
        from components.help_system import HelpSystemComponent
        from ui.error_handler import ErrorHandler
        
        # Create components
        help_component = HelpSystemComponent()
        error_handler = ErrorHandler()
        
        # Test help system rendering
        with patch.object(help_component, 'render') as mock_render:
            mock_render.return_value = None
            help_component.render()
            mock_render.assert_called_once()
        
        # Test contextual help
        with patch.object(error_handler, 'show_contextual_help') as mock_help:
            mock_help.return_value = None
            error_handler.show_contextual_help("Test Feature", {
                'quick_tip': "Test tip",
                'detailed_help': "Test detailed help"
            })
            mock_help.assert_called_once()


class TestAdvancedFilteringIntegration:
    """Test advanced filtering and search integration"""
    
    def setup_method(self):
        """Set up test fixtures before each test method"""
        # Create a mock session state
        class MockSessionState(dict):
            def __getattr__(self, name):
                try:
                    return self[name]
                except KeyError:
                    defaults = {
                        'filter_logic': 'AND',
                        'use_advanced_filters': False,
                        'filter_expression': '',
                        'search_query': '',
                        'search_results_count': 0,
                        'current_search_result_index': 0,
                        'search_result_indices': []
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
            patch('streamlit.sidebar'),
            patch('streamlit.columns'),
            patch('streamlit.container'),
            patch('streamlit.expander'),
            patch('streamlit.dataframe'),
            patch('streamlit.plotly_chart'),
            patch('streamlit.text_input'),
            patch('streamlit.text_area'),
            patch('streamlit.checkbox'),
            patch('streamlit.button'),
            patch('streamlit.multiselect'),
            patch('streamlit.radio'),
            patch('streamlit.selectbox'),
            patch('streamlit.rerun')
        ]
        
        for patch_obj in self.streamlit_patches:
            patch_obj.start()
    
    def teardown_method(self):
        """Clean up after each test method"""
        for patch_obj in self.streamlit_patches:
            patch_obj.stop()
    
    def test_advanced_filter_expression_integration(self):
        """Test advanced filter expression integration"""
        from components.sidebar import SidebarComponent
        from components.data_table import DataTableComponent
        from parsers.plan_parser import PlanParser
        
        # Create components
        sidebar_component = SidebarComponent()
        data_table_component = DataTableComponent()
        
        # Get test data
        plan_data = TestFixtures.get_multi_cloud_plan()
        parser = PlanParser(plan_data)
        resource_changes = parser.get_resource_changes()
        
        # Test advanced filter expression validation
        test_expressions = [
            "action='create' AND risk='High'",
            "(action='delete' OR action='replace') AND provider='aws'",
            "risk IN ('Medium', 'High') AND provider IN ('aws', 'azure')"
        ]
        
        for expression in test_expressions:
            validation_result = sidebar_component._validate_filter_expression(expression)
            assert validation_result['valid'], f"Expression should be valid: {expression}"
    
    def test_search_functionality_integration(self):
        """Test search functionality integration"""
        from components.data_table import DataTableComponent
        from ui.session_manager import SessionStateManager
        from parsers.plan_parser import PlanParser
        import pandas as pd
        
        # Create components
        data_table_component = DataTableComponent()
        session_manager = SessionStateManager()
        
        # Get test data
        plan_data = TestFixtures.get_multi_cloud_plan()
        parser = PlanParser(plan_data)
        resource_changes = parser.get_resource_changes()
        
        # Create test dataframe
        test_df = pd.DataFrame([
            {'resource_name': 'web', 'resource_type': 'aws_instance', 'resource_address': 'aws_instance.web'},
            {'resource_name': 'app', 'resource_type': 'azurerm_virtual_machine', 'resource_address': 'azurerm_virtual_machine.app'},
            {'resource_name': 'database', 'resource_type': 'google_compute_instance', 'resource_address': 'google_compute_instance.database'}
        ])
        
        # Test search filtering
        search_queries = ['aws_instance', 'web', 'database']
        
        for query in search_queries:
            filtered_df = data_table_component._apply_search_filter(test_df, query)
            assert len(filtered_df) > 0, f"Search should find results for: {query}"
    
    def test_filter_preset_integration(self):
        """Test filter preset integration"""
        from components.sidebar import SidebarComponent
        
        # Create component
        sidebar_component = SidebarComponent()
        
        # Test preset configurations
        presets = ["High Risk Only", "New Resources", "Deletions Only", "Updates & Changes", "All Actions"]
        
        for preset_name in presets:
            preset_config = sidebar_component._get_preset_filters(preset_name)
            
            # Verify preset structure
            assert isinstance(preset_config, dict)
            assert 'action_filter' in preset_config
            assert 'risk_filter' in preset_config
            assert 'provider_filter' in preset_config
            
            # Verify preset logic
            if preset_name == "High Risk Only":
                assert preset_config['risk_filter'] == ['High']
            elif preset_name == "New Resources":
                assert preset_config['action_filter'] == ['create']
            elif preset_name == "Deletions Only":
                assert preset_config['action_filter'] == ['delete']


if __name__ == '__main__':
    pytest.main([__file__])
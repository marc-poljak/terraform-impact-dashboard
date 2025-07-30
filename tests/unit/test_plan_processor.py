"""
Unit tests for the PlanProcessor utility class.
Tests the plan processing workflow extracted from app.py.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import json
import io

from utils.plan_processor import PlanProcessor


class TestPlanProcessor:
    """Test cases for PlanProcessor class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.plan_processor = PlanProcessor()
        
        # Mock uploaded file
        self.mock_uploaded_file = Mock()
        self.mock_uploaded_file.size = 1024
        self.mock_uploaded_file.getvalue.return_value = b'{"test": "data"}'
        
        # Mock components
        self.mock_upload_component = Mock()
        self.mock_error_handler = Mock()
        
        # Sample plan data
        self.sample_plan_data = {
            "format_version": "1.0",
            "terraform_version": "1.0.0",
            "resource_changes": [
                {
                    "address": "aws_instance.example",
                    "change": {
                        "actions": ["create"],
                        "before": None,
                        "after": {"instance_type": "t2.micro"}
                    }
                }
            ]
        }
    
    def test_plan_processor_creation(self):
        """Test that PlanProcessor can be created successfully."""
        processor = PlanProcessor()
        assert processor is not None
        assert hasattr(processor, 'progress_tracker')
        assert hasattr(processor, 'performance_optimizer')
    
    def test_plan_processor_has_required_methods(self):
        """Test that PlanProcessor has the required methods."""
        processor = PlanProcessor()
        assert hasattr(processor, 'process_plan_data')
        assert callable(getattr(processor, 'process_plan_data'))
    
    def _setup_context_manager_mocks(self):
        """Helper method to set up context manager mocks."""
        # Mock progress tracker context manager
        mock_stage_tracker = Mock()
        mock_stage_tracker.next_stage = Mock()
        mock_stage_tracker.complete = Mock()
        mock_context_manager = Mock()
        mock_context_manager.__enter__ = Mock(return_value=mock_stage_tracker)
        mock_context_manager.__exit__ = Mock(return_value=None)
        self.plan_processor.progress_tracker.track_file_processing = Mock(return_value=mock_context_manager)
        
        # Mock performance monitor context manager
        mock_perf_context = Mock()
        mock_perf_context.__enter__ = Mock()
        mock_perf_context.__exit__ = Mock(return_value=None)
        self.plan_processor.performance_optimizer.performance_monitor = Mock(return_value=mock_perf_context)
    
    @patch('utils.risk_assessment.RiskAssessment')
    @patch('utils.plan_processor.PlanParser')
    @patch('utils.plan_processor.ChartGenerator')
    def test_process_plan_data_success(self, mock_chart_gen, mock_plan_parser, mock_risk_assessment):
        """Test successful plan data processing."""
        # Setup mocks
        self.mock_upload_component.validate_and_parse_file.return_value = (self.sample_plan_data, None)
        
        mock_parser_instance = Mock()
        mock_parser_instance.get_summary.return_value = {"total_changes": 1}
        mock_parser_instance.get_resource_changes.return_value = [{"address": "aws_instance.example"}]
        mock_parser_instance.get_resource_types.return_value = {"aws_instance": 1}
        mock_parser_instance.get_debug_info.return_value = {"debug": "info"}
        mock_plan_parser.return_value = mock_parser_instance
        
        # Mock basic risk assessment
        mock_risk_instance = Mock()
        mock_risk_instance.assess_plan_risk.return_value = {"risk_level": "low"}
        mock_risk_assessment.return_value = mock_risk_instance
        
        # Setup context manager mocks
        self._setup_context_manager_mocks()
        
        # Execute
        result = self.plan_processor.process_plan_data(
            self.mock_uploaded_file,
            self.mock_upload_component,
            self.mock_error_handler,
            show_debug=False,
            enable_multi_cloud=False
        )
        
        # Verify
        assert result is not None
        assert 'plan_data' in result
        assert 'parser' in result
        assert 'summary' in result
        assert 'resource_changes' in result
        assert 'resource_types' in result
        assert 'debug_info' in result
        assert 'chart_gen' in result
        assert result['plan_data'] == self.sample_plan_data
    
    def test_process_plan_data_upload_failure(self):
        """Test plan data processing when upload validation fails."""
        # Setup mock to return None (validation failure)
        self.mock_upload_component.validate_and_parse_file.return_value = (None, "Invalid JSON")
        
        # Setup context manager mocks
        self._setup_context_manager_mocks()
        
        # Execute
        result = self.plan_processor.process_plan_data(
            self.mock_uploaded_file,
            self.mock_upload_component,
            self.mock_error_handler,
            show_debug=False,
            enable_multi_cloud=False
        )
        
        # Verify
        assert result is None
    
    @patch('utils.plan_processor.PlanParser')
    def test_process_plan_data_parser_exception(self, mock_plan_parser):
        """Test plan data processing when parser raises exception."""
        # Setup mocks
        self.mock_upload_component.validate_and_parse_file.return_value = (self.sample_plan_data, None)
        mock_plan_parser.side_effect = Exception("Parser error")
        
        # Setup context manager mocks
        self._setup_context_manager_mocks()
        
        # Execute
        result = self.plan_processor.process_plan_data(
            self.mock_uploaded_file,
            self.mock_upload_component,
            self.mock_error_handler,
            show_debug=False,
            enable_multi_cloud=False
        )
        
        # Verify
        assert result is None
        self.mock_error_handler.handle_processing_error.assert_called_once()
    
    @patch('utils.plan_processor.ENHANCED_FEATURES_AVAILABLE', True)
    @patch('utils.plan_processor.EnhancedRiskAssessment')
    @patch('utils.plan_processor.PlanParser')
    @patch('utils.plan_processor.ChartGenerator')
    def test_process_plan_data_with_enhanced_features(self, mock_chart_gen, mock_plan_parser, mock_enhanced_risk):
        """Test plan data processing with enhanced features enabled."""
        # Setup mocks
        self.mock_upload_component.validate_and_parse_file.return_value = (self.sample_plan_data, None)
        
        mock_parser_instance = Mock()
        mock_parser_instance.get_summary.return_value = {"total_changes": 1}
        mock_parser_instance.get_resource_changes.return_value = [{"address": "aws_instance.example"}]
        mock_parser_instance.get_resource_types.return_value = {"aws_instance": 1}
        mock_parser_instance.get_debug_info.return_value = {"debug": "info"}
        mock_plan_parser.return_value = mock_parser_instance
        
        mock_enhanced_risk_instance = Mock()
        mock_enhanced_risk_instance.assess_plan_risk.return_value = {"risk_level": "medium"}
        mock_enhanced_risk.return_value = mock_enhanced_risk_instance
        
        # Setup context manager mocks
        self._setup_context_manager_mocks()
        
        # Execute
        result = self.plan_processor.process_plan_data(
            self.mock_uploaded_file,
            self.mock_upload_component,
            self.mock_error_handler,
            show_debug=False,
            enable_multi_cloud=True
        )
        
        # Verify
        assert result is not None
        assert 'enhanced_risk_assessor' in result
        assert 'enhanced_risk_result' in result
        assert result['enhanced_risk_assessor'] is not None
        mock_enhanced_risk_instance.assess_plan_risk.assert_called_once()
"""
Unit tests for Upload Component Security

Tests that file upload uses the same security principles as TFE integration,
ensuring plan data is handled securely regardless of input method.
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from io import StringIO

from components.upload_section import UploadComponent


class TestUploadComponentSecurity:
    """Test suite for upload component security"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.upload_component = UploadComponent()
        
        # Sample plan data for testing
        self.sample_plan_data = {
            "terraform_version": "1.5.0",
            "format_version": "1.2",
            "resource_changes": [
                {
                    "address": "aws_instance.web",
                    "change": {
                        "actions": ["create"],
                        "before": None,
                        "after": {
                            "instance_type": "t3.micro",
                            "ami": "ami-12345678",
                            "user_data": "sensitive_startup_script"
                        }
                    }
                },
                {
                    "address": "aws_db_instance.main",
                    "change": {
                        "actions": ["create"],
                        "before": None,
                        "after": {
                            "password": "super_secret_password",
                            "username": "admin",
                            "endpoint": "prod-db.company.com"
                        }
                    }
                }
            ]
        }
    
    def test_secure_plan_manager_initialization(self):
        """Test that upload component initializes secure plan manager"""
        assert hasattr(self.upload_component, 'plan_manager')
        assert self.upload_component.plan_manager is not None
    
    @patch('streamlit.success')
    @patch('streamlit.metric')
    @patch('streamlit.columns')
    @patch('streamlit.markdown')
    def test_secure_plan_summary_display(self, mock_markdown, mock_columns, mock_metric, mock_success):
        """Test that plan summary displays securely without sensitive data"""
        # Store plan data
        self.upload_component.plan_manager.store_plan_data(
            self.sample_plan_data,
            source="file_upload"
        )
        
        # Mock Streamlit columns with context manager support
        mock_col1 = MagicMock()
        mock_col1.__enter__ = Mock(return_value=mock_col1)
        mock_col1.__exit__ = Mock(return_value=None)
        mock_col2 = MagicMock()
        mock_col2.__enter__ = Mock(return_value=mock_col2)
        mock_col2.__exit__ = Mock(return_value=None)
        mock_col3 = MagicMock()
        mock_col3.__enter__ = Mock(return_value=mock_col3)
        mock_col3.__exit__ = Mock(return_value=None)
        mock_columns.return_value = [mock_col1, mock_col2, mock_col3]
        
        # Show secure summary
        self.upload_component._show_secure_plan_summary()
        
        # Verify summary was displayed
        mock_markdown.assert_called()
        mock_success.assert_called()
        
        # Verify no sensitive data in any calls
        all_calls = str(mock_markdown.call_args_list) + str(mock_metric.call_args_list) + str(mock_success.call_args_list)
        
        # Ensure sensitive data is not exposed
        assert "super_secret_password" not in all_calls
        assert "admin" not in all_calls
        assert "prod-db.company.com" not in all_calls
        assert "sensitive_startup_script" not in all_calls
        assert "ami-12345678" not in all_calls
    
    def test_plan_data_secure_storage(self):
        """Test that plan data is stored securely"""
        # Store plan data
        self.upload_component.plan_manager.store_plan_data(
            self.sample_plan_data,
            source="file_upload"
        )
        
        # Verify data is stored
        assert self.upload_component.plan_manager.has_plan_data()
        
        # Verify metadata is extracted safely
        metadata = self.upload_component.plan_manager.get_plan_metadata()
        assert metadata.source == "file_upload"
        assert metadata.terraform_version == "1.5.0"
        assert metadata.resource_count == 2
        assert metadata.action_summary == {"create": 2}
        
        # Verify sensitive data is not in metadata
        metadata_str = str(metadata)
        assert "super_secret_password" not in metadata_str
        assert "admin" not in metadata_str
        assert "prod-db.company.com" not in metadata_str
    
    def test_secure_error_context(self):
        """Test that error context doesn't expose sensitive data"""
        # Store plan data
        self.upload_component.plan_manager.store_plan_data(
            self.sample_plan_data,
            source="file_upload"
        )
        
        # Get safe error context
        error_context = self.upload_component.plan_manager.get_safe_error_context("test error")
        
        # Verify context contains safe information
        assert "Plan processing error" in error_context
        assert "Source: file_upload" in error_context
        assert "Resources: 2" in error_context
        assert "Terraform: 1.5.0" in error_context
        assert "test error" in error_context
        
        # Verify no sensitive data is exposed
        assert "super_secret_password" not in error_context
        assert "admin" not in error_context
        assert "prod-db.company.com" not in error_context
        assert "sensitive_startup_script" not in error_context
    
    def test_cleanup_functionality(self):
        """Test that cleanup properly clears sensitive data"""
        # Store plan data
        self.upload_component.plan_manager.store_plan_data(
            self.sample_plan_data,
            source="file_upload"
        )
        
        # Verify data is stored
        assert self.upload_component.plan_manager.has_plan_data()
        
        # Cleanup
        self.upload_component.cleanup()
        
        # Verify data is cleared
        assert not self.upload_component.plan_manager.has_plan_data()
        assert self.upload_component.plan_manager.get_plan_data() is None
        assert self.upload_component.plan_manager.get_plan_metadata() is None
    
    @patch('components.upload_section.st.success')
    @patch('components.upload_section.st.metric')
    @patch('components.upload_section.st.columns')
    @patch('components.upload_section.st.markdown')
    def test_file_upload_tab_security_integration(self, mock_markdown, mock_columns, mock_metric, mock_success):
        """Test that file upload tab integrates security properly"""
        # Create mock uploaded file
        mock_file = Mock()
        mock_file.getvalue.return_value = json.dumps(self.sample_plan_data).encode()
        mock_file.name = "test-plan.json"
        
        # Mock Streamlit components with context manager support
        mock_col1 = MagicMock()
        mock_col1.__enter__ = Mock(return_value=mock_col1)
        mock_col1.__exit__ = Mock(return_value=None)
        mock_col2 = MagicMock()
        mock_col2.__enter__ = Mock(return_value=mock_col2)
        mock_col2.__exit__ = Mock(return_value=None)
        mock_col3 = MagicMock()
        mock_col3.__enter__ = Mock(return_value=mock_col3)
        mock_col3.__exit__ = Mock(return_value=None)
        mock_columns.return_value = [mock_col1, mock_col2, mock_col3]
        
        # Mock the validate_and_parse_file method to return our test data
        with patch.object(self.upload_component, 'validate_and_parse_file') as mock_validate:
            mock_validate.return_value = (self.sample_plan_data, None)
            
            # Process the file upload (simulating the file upload tab logic)
            plan_data, error_msg = self.upload_component.validate_and_parse_file(mock_file, False)
            
            if plan_data is not None:
                # Store plan data securely (as done in _render_file_upload_tab)
                self.upload_component.plan_manager.store_plan_data(
                    plan_data,
                    source="file_upload"
                )
                
                # Show secure plan summary
                self.upload_component._show_secure_plan_summary()
                
                # Get secure copy of plan data
                secure_plan_data = self.upload_component.plan_manager.get_plan_data()
        
        # Verify plan data was processed securely
        assert secure_plan_data is not None
        assert secure_plan_data["terraform_version"] == "1.5.0"
        assert len(secure_plan_data["resource_changes"]) == 2
        
        # Verify secure summary was displayed
        mock_success.assert_called()
        
        # Verify plan manager has the data
        assert self.upload_component.plan_manager.has_plan_data()
    
    def test_memory_only_storage_compliance(self):
        """Test that file upload complies with memory-only storage requirement"""
        # Store plan data
        self.upload_component.plan_manager.store_plan_data(
            self.sample_plan_data,
            source="file_upload"
        )
        
        # Verify data is accessible in memory
        plan_data = self.upload_component.plan_manager.get_plan_data()
        assert plan_data is not None
        assert plan_data["terraform_version"] == "1.5.0"
        
        # Verify data is deep copied (not same object)
        plan_data["terraform_version"] = "modified"
        original_data = self.upload_component.plan_manager.get_plan_data()
        assert original_data["terraform_version"] == "1.5.0"  # Should be unchanged
    
    def test_masked_summary_security(self):
        """Test that masked summary doesn't expose sensitive data"""
        # Store plan data
        self.upload_component.plan_manager.store_plan_data(
            self.sample_plan_data,
            source="file_upload"
        )
        
        # Get masked summary
        summary = self.upload_component.plan_manager.get_masked_summary()
        
        # Verify summary contains safe information
        assert summary["terraform_version"] == "1.5.0"
        assert summary["resource_count"] == 2
        assert summary["actions"] == {"create": 2}
        assert summary["source"] == "file_upload"
        
        # Verify no sensitive data in summary
        summary_str = str(summary)
        assert "super_secret_password" not in summary_str
        assert "admin" not in summary_str
        assert "prod-db.company.com" not in summary_str
        assert "sensitive_startup_script" not in summary_str
    
    def test_security_parity_with_tfe_integration(self):
        """Test that file upload has same security features as TFE integration"""
        # Store plan data via file upload
        self.upload_component.plan_manager.store_plan_data(
            self.sample_plan_data,
            source="file_upload"
        )
        
        # Test all security features that TFE integration has
        
        # 1. Memory-only storage
        assert self.upload_component.plan_manager.has_plan_data()
        
        # 2. Masked summary
        summary = self.upload_component.plan_manager.get_masked_summary()
        assert "source" in summary
        assert "data_size" in summary
        
        # 3. Safe error context
        error_context = self.upload_component.plan_manager.get_safe_error_context("test")
        assert "Plan processing error" in error_context
        assert "super_secret_password" not in error_context
        
        # 4. Secure cleanup
        self.upload_component.cleanup()
        assert not self.upload_component.plan_manager.has_plan_data()
        
        # 5. Deep copying
        self.upload_component.plan_manager.store_plan_data(self.sample_plan_data, "file_upload")
        data1 = self.upload_component.plan_manager.get_plan_data()
        data2 = self.upload_component.plan_manager.get_plan_data()
        data1["test"] = "modified"
        assert "test" not in data2  # Should be independent copies


class TestUploadSecurityIntegration:
    """Integration tests for upload security"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.upload_component = UploadComponent()
    
    def test_end_to_end_security_workflow(self):
        """Test complete security workflow from upload to cleanup"""
        sensitive_plan = {
            "terraform_version": "1.5.0",
            "resource_changes": [
                {
                    "address": "aws_rds_cluster.prod",
                    "change": {
                        "actions": ["create"],
                        "after": {
                            "master_password": "extremely_secret_password",
                            "master_username": "root",
                            "database_name": "production_db",
                            "endpoint": "prod-cluster.xyz.rds.amazonaws.com"
                        }
                    }
                }
            ]
        }
        
        # 1. Store plan data securely
        self.upload_component.plan_manager.store_plan_data(
            sensitive_plan,
            source="file_upload"
        )
        
        # 2. Verify data is accessible but secure
        assert self.upload_component.plan_manager.has_plan_data()
        
        # 3. Verify masked summary is safe
        summary = self.upload_component.plan_manager.get_masked_summary()
        summary_str = str(summary)
        assert "extremely_secret_password" not in summary_str
        assert "root" not in summary_str
        assert "production_db" not in summary_str
        assert "prod-cluster.xyz.rds.amazonaws.com" not in summary_str
        
        # 4. Verify error context is safe
        error_context = self.upload_component.plan_manager.get_safe_error_context("processing failed")
        assert "extremely_secret_password" not in error_context
        assert "root" not in error_context
        assert "production_db" not in error_context
        assert "prod-cluster.xyz.rds.amazonaws.com" not in error_context
        
        # 5. Verify cleanup works
        self.upload_component.cleanup()
        assert not self.upload_component.plan_manager.has_plan_data()
    
    def test_security_consistency_across_input_methods(self):
        """Test that both file upload and TFE integration have consistent security"""
        from components.tfe_input import TFEInputComponent
        
        test_plan = {
            "terraform_version": "1.5.0",
            "resource_changes": [
                {
                    "address": "sensitive_resource",
                    "change": {
                        "actions": ["create"],
                        "after": {"secret": "confidential_data"}
                    }
                }
            ]
        }
        
        # Test file upload security
        upload_component = UploadComponent()
        upload_component.plan_manager.store_plan_data(test_plan, "file_upload")
        upload_summary = upload_component.plan_manager.get_masked_summary()
        upload_error_context = upload_component.plan_manager.get_safe_error_context("test")
        
        # Test TFE integration security
        tfe_component = TFEInputComponent()
        tfe_component.plan_manager.store_plan_data(test_plan, "tfe_integration")
        tfe_summary = tfe_component.plan_manager.get_masked_summary()
        tfe_error_context = tfe_component.plan_manager.get_safe_error_context("test")
        
        # Verify both have same security features
        assert "confidential_data" not in str(upload_summary)
        assert "confidential_data" not in str(tfe_summary)
        assert "confidential_data" not in upload_error_context
        assert "confidential_data" not in tfe_error_context
        
        # Verify both have same structure (except source)
        upload_summary_copy = upload_summary.copy()
        tfe_summary_copy = tfe_summary.copy()
        upload_summary_copy.pop('source', None)
        tfe_summary_copy.pop('source', None)
        
        # Should have same keys and security features
        assert set(upload_summary_copy.keys()) == set(tfe_summary_copy.keys())
        
        # Cleanup both
        upload_component.cleanup()
        tfe_component.cleanup()
        
        assert not upload_component.plan_manager.has_plan_data()
        assert not tfe_component.plan_manager.has_plan_data()
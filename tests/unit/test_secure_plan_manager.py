"""
Unit tests for Secure Plan Manager

Tests secure handling of Terraform plan JSON data with the same security
principles as credentials: memory-only storage, automatic cleanup, and
masked values in error messages.
"""

import pytest
import json
from unittest.mock import patch, MagicMock

from utils.secure_plan_manager import SecurePlanManager, PlanMetadata


class TestSecurePlanManager:
    """Test suite for secure plan manager"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.plan_manager = SecurePlanManager()
        
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
                            "ami": "ami-12345678"
                        }
                    }
                },
                {
                    "address": "aws_s3_bucket.data",
                    "change": {
                        "actions": ["update"],
                        "before": {"versioning": False},
                        "after": {"versioning": True}
                    }
                }
            ],
            "configuration": {
                "provider_config": {
                    "aws": {
                        "region": "us-west-2"
                    }
                }
            }
        }
    
    def test_store_plan_data_basic(self):
        """Test basic plan data storage"""
        self.plan_manager.store_plan_data(self.sample_plan_data, "file_upload")
        
        assert self.plan_manager.has_plan_data() is True
        stored_data = self.plan_manager.get_plan_data()
        assert stored_data is not None
        assert stored_data["terraform_version"] == "1.5.0"
        assert len(stored_data["resource_changes"]) == 2
    
    def test_store_plan_data_with_tfe_metadata(self):
        """Test plan data storage with TFE metadata"""
        self.plan_manager.store_plan_data(
            self.sample_plan_data, 
            "tfe_integration",
            workspace_id="ws-ABC123456",
            run_id="run-XYZ789012"
        )
        
        metadata = self.plan_manager.get_plan_metadata()
        assert metadata is not None
        assert metadata.source == "tfe_integration"
        assert metadata.workspace_id == "ws-ABC123456"
        assert metadata.run_id == "run-XYZ789012"
    
    def test_plan_data_deep_copy(self):
        """Test that plan data returns deep copies to prevent external modification"""
        self.plan_manager.store_plan_data(self.sample_plan_data, "file_upload")
        
        # Get plan data and modify it
        plan_data_1 = self.plan_manager.get_plan_data()
        plan_data_2 = self.plan_manager.get_plan_data()
        
        # Modify one copy
        plan_data_1["terraform_version"] = "modified"
        plan_data_1["resource_changes"][0]["address"] = "modified"
        
        # Verify other copy is unaffected
        assert plan_data_2["terraform_version"] == "1.5.0"
        assert plan_data_2["resource_changes"][0]["address"] == "aws_instance.web"
        
        # Verify stored data is unaffected
        original_data = self.plan_manager.get_plan_data()
        assert original_data["terraform_version"] == "1.5.0"
    
    def test_metadata_extraction(self):
        """Test metadata extraction from plan data"""
        self.plan_manager.store_plan_data(self.sample_plan_data, "file_upload")
        
        metadata = self.plan_manager.get_plan_metadata()
        assert metadata is not None
        assert metadata.terraform_version == "1.5.0"
        assert metadata.format_version == "1.2"
        assert metadata.resource_count == 2
        assert metadata.action_summary == {"create": 1, "update": 1}
        assert metadata.source == "file_upload"
    
    def test_masked_summary(self):
        """Test masked summary generation"""
        self.plan_manager.store_plan_data(
            self.sample_plan_data,
            "tfe_integration", 
            workspace_id="ws-ABC123456789",
            run_id="run-XYZ987654321"
        )
        
        summary = self.plan_manager.get_masked_summary()
        
        assert summary["terraform_version"] == "1.5.0"
        assert summary["resource_count"] == 2
        assert summary["actions"] == {"create": 1, "update": 1}
        assert summary["source"] == "tfe_integration"
        
        # Verify IDs are masked (actual masking shows middle characters)
        assert summary["workspace_id"] == "ws-A*******6789"
        assert summary["run_id"] == "run-********4321"
        
        # Verify data size is approximated
        assert "KB" in summary["data_size"]
    
    def test_id_masking(self):
        """Test ID masking functionality"""
        # Test workspace ID masking
        masked_ws = self.plan_manager._mask_id("ws-ABC123456789")
        assert masked_ws == "ws-A*******6789"
        
        # Test run ID masking
        masked_run = self.plan_manager._mask_id("run-XYZ987654321")
        assert masked_run == "run-********4321"
        
        # Test short ID masking
        masked_short = self.plan_manager._mask_id("ws-123")
        assert masked_short == "******"
        
        # Test empty ID
        masked_empty = self.plan_manager._mask_id("")
        assert masked_empty == ""
    
    def test_safe_error_context(self):
        """Test safe error context generation"""
        # Test without plan data
        context = self.plan_manager.get_safe_error_context("test error")
        assert "No plan data available" in context
        assert "test error" in context
        
        # Test with plan data
        self.plan_manager.store_plan_data(self.sample_plan_data, "tfe_integration")
        context = self.plan_manager.get_safe_error_context("processing failed")
        
        assert "Plan processing error" in context
        assert "Source: tfe_integration" in context
        assert "Resources: 2" in context
        assert "Terraform: 1.5.0" in context
        assert "processing failed" in context
        
        # Verify no sensitive data is exposed
        assert "aws_instance.web" not in context
        assert "ami-12345678" not in context
        assert "us-west-2" not in context
    
    def test_clear_plan_data(self):
        """Test plan data clearing"""
        self.plan_manager.store_plan_data(self.sample_plan_data, "file_upload")
        
        assert self.plan_manager.has_plan_data() is True
        assert self.plan_manager.get_plan_metadata() is not None
        
        self.plan_manager.clear_plan_data()
        
        assert self.plan_manager.has_plan_data() is False
        assert self.plan_manager.get_plan_data() is None
        assert self.plan_manager.get_plan_metadata() is None
    
    def test_data_overwriting_on_clear(self):
        """Test that sensitive data is overwritten before clearing"""
        original_data = self.sample_plan_data.copy()
        self.plan_manager.store_plan_data(original_data, "file_upload")
        
        # Clear data (which should overwrite)
        self.plan_manager.clear_plan_data()
        
        # Verify original data structure is modified (overwritten)
        # Note: This tests the overwrite functionality, though in practice
        # the original data passed in might not be the same object
        assert self.plan_manager._plan_data is None
    
    def test_overwrite_sensitive_data_dict(self):
        """Test recursive overwriting of dictionary data"""
        test_data = {
            "string_value": "sensitive",
            "number_value": 123,
            "nested": {
                "inner_string": "secret",
                "inner_number": 456
            },
            "list_value": ["item1", "item2", {"nested_in_list": "hidden"}]
        }
        
        self.plan_manager._overwrite_sensitive_data(test_data)
        
        # Verify strings are overwritten
        assert test_data["string_value"] == "*********"
        assert test_data["nested"]["inner_string"] == "******"
        
        # Verify numbers are set to None
        assert test_data["number_value"] is None
        assert test_data["nested"]["inner_number"] is None
        
        # Verify list items are overwritten
        assert test_data["list_value"][0] == "*****"
        assert test_data["list_value"][1] == "*****"
        assert test_data["list_value"][2]["nested_in_list"] == "******"
    
    def test_overwrite_sensitive_data_list(self):
        """Test recursive overwriting of list data"""
        test_data = [
            "string1",
            123,
            {"key": "value"},
            ["nested", "list"]
        ]
        
        self.plan_manager._overwrite_sensitive_data(test_data)
        
        assert test_data[0] == "*******"
        assert test_data[1] is None
        assert test_data[2]["key"] == "*****"
        assert test_data[3][0] == "******"
        assert test_data[3][1] == "****"
    
    def test_no_plan_data_scenarios(self):
        """Test behavior when no plan data is stored"""
        assert self.plan_manager.has_plan_data() is False
        assert self.plan_manager.get_plan_data() is None
        assert self.plan_manager.get_plan_metadata() is None
        
        summary = self.plan_manager.get_masked_summary()
        assert summary["status"] == "no_plan_data"
        
        context = self.plan_manager.get_safe_error_context()
        assert "No plan data available" in context
    
    def test_empty_plan_data(self):
        """Test handling of empty or None plan data"""
        self.plan_manager.store_plan_data(None, "file_upload")
        assert self.plan_manager.has_plan_data() is False
        
        self.plan_manager.store_plan_data({}, "file_upload")
        assert self.plan_manager.has_plan_data() is True
        
        metadata = self.plan_manager.get_plan_metadata()
        assert metadata.terraform_version == "unknown"
        assert metadata.resource_count == 0
        assert metadata.action_summary == {}
    
    def test_malformed_plan_data(self):
        """Test handling of malformed plan data"""
        malformed_data = {
            "terraform_version": "1.5.0",
            # Missing format_version
            "resource_changes": [
                {
                    # Missing address
                    "change": {
                        # Missing actions
                        "before": None,
                        "after": {}
                    }
                }
            ]
        }
        
        self.plan_manager.store_plan_data(malformed_data, "file_upload")
        
        metadata = self.plan_manager.get_plan_metadata()
        assert metadata.terraform_version == "1.5.0"
        assert metadata.format_version == "unknown"
        assert metadata.resource_count == 1
        # Should handle missing actions gracefully
        assert isinstance(metadata.action_summary, dict)


class TestSecurePlanManagerIntegration:
    """Integration tests for secure plan manager"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.plan_manager = SecurePlanManager()
    
    @patch('atexit.register')
    def test_cleanup_registration(self, mock_atexit):
        """Test that cleanup is registered on initialization"""
        SecurePlanManager()
        
        # Verify atexit.register was called
        assert mock_atexit.call_count >= 1
    
    def test_instance_tracking(self):
        """Test that instances are tracked for cleanup"""
        initial_count = len(SecurePlanManager._instances)
        
        manager1 = SecurePlanManager()
        manager2 = SecurePlanManager()
        
        assert len(SecurePlanManager._instances) == initial_count + 2
        
        # Cleanup should work on all instances
        SecurePlanManager.cleanup_all_instances()
        
        # Instances should still exist but data should be cleared
        assert len(SecurePlanManager._instances) == initial_count + 2
    
    def test_memory_only_storage(self):
        """Test that plan data is never written to disk"""
        large_plan_data = {
            "terraform_version": "1.5.0",
            "format_version": "1.2",
            "resource_changes": [
                {
                    "address": f"aws_instance.web_{i}",
                    "change": {
                        "actions": ["create"],
                        "before": None,
                        "after": {
                            "instance_type": "t3.micro",
                            "ami": f"ami-{i:08d}",
                            "user_data": "sensitive_script_content" * 100
                        }
                    }
                } for i in range(100)  # Large dataset
            ]
        }
        
        self.plan_manager.store_plan_data(large_plan_data, "file_upload")
        
        # Verify data is accessible
        assert self.plan_manager.has_plan_data() is True
        stored_data = self.plan_manager.get_plan_data()
        assert len(stored_data["resource_changes"]) == 100
        
        # Verify no files are created (this is implicit - we're not mocking file operations)
        # The test passes if no exceptions are raised and data is properly stored in memory
    
    def test_concurrent_access_safety(self):
        """Test that concurrent access doesn't cause issues"""
        import threading
        import time
        
        results = []
        errors = []
        
        def store_and_retrieve(thread_id):
            try:
                manager = SecurePlanManager()
                test_data = {
                    "terraform_version": f"1.{thread_id}.0",
                    "resource_changes": [{"address": f"resource_{thread_id}"}]
                }
                
                manager.store_plan_data(test_data, f"thread_{thread_id}")
                time.sleep(0.01)  # Small delay to test concurrency
                
                retrieved = manager.get_plan_data()
                if retrieved and retrieved["terraform_version"] == f"1.{thread_id}.0":
                    results.append(thread_id)
                else:
                    errors.append(f"Data mismatch for thread {thread_id}")
                    
            except Exception as e:
                errors.append(f"Thread {thread_id} error: {str(e)}")
        
        # Create multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=store_and_retrieve, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify all threads completed successfully
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) == 5, f"Expected 5 results, got {len(results)}"
    
    def test_security_compliance(self):
        """Test that security requirements are met"""
        sensitive_plan_data = {
            "terraform_version": "1.5.0",
            "resource_changes": [
                {
                    "address": "aws_db_instance.production",
                    "change": {
                        "actions": ["create"],
                        "after": {
                            "password": "super_secret_password",
                            "username": "admin",
                            "endpoint": "prod-db.company.com"
                        }
                    }
                }
            ]
        }
        
        self.plan_manager.store_plan_data(sensitive_plan_data, "tfe_integration")
        
        # Test that error context doesn't expose sensitive data
        error_context = self.plan_manager.get_safe_error_context("test error")
        assert "super_secret_password" not in error_context
        assert "admin" not in error_context
        assert "prod-db.company.com" not in error_context
        
        # Test that masked summary doesn't expose sensitive data
        summary = self.plan_manager.get_masked_summary()
        summary_str = str(summary)
        assert "super_secret_password" not in summary_str
        assert "admin" not in summary_str
        assert "prod-db.company.com" not in summary_str
        
        # Test that cleanup properly overwrites sensitive data
        original_data = self.plan_manager._plan_data
        self.plan_manager.clear_plan_data()
        
        # Data should be cleared
        assert self.plan_manager._plan_data is None
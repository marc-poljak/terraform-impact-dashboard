"""
Test validation for integration test fixtures

Validates that test fixtures provide correct data structures.
"""

import pytest
from tests.integration.test_fixtures import TestFixtures


class TestFixturesValidation:
    """Test that fixtures provide valid data structures"""
    
    def test_simple_plan_structure(self):
        """Test simple plan fixture structure"""
        plan = TestFixtures.get_simple_plan()
        
        # Verify required fields
        assert 'terraform_version' in plan
        assert 'format_version' in plan
        assert 'resource_changes' in plan
        
        # Verify data types
        assert isinstance(plan['resource_changes'], list)
        assert len(plan['resource_changes']) > 0
        
        # Verify resource change structure
        for change in plan['resource_changes']:
            assert 'address' in change
            assert 'type' in change
            assert 'change' in change
            assert 'actions' in change['change']
    
    def test_multi_cloud_plan_structure(self):
        """Test multi-cloud plan fixture structure"""
        plan = TestFixtures.get_multi_cloud_plan()
        
        # Verify required fields
        assert 'terraform_version' in plan
        assert 'resource_changes' in plan
        assert len(plan['resource_changes']) >= 3  # Should have multiple providers
        
        # Verify multiple providers are present
        providers = set()
        for change in plan['resource_changes']:
            provider_name = change.get('provider_name', '')
            if 'aws' in provider_name:
                providers.add('aws')
            elif 'azure' in provider_name:
                providers.add('azure')
            elif 'google' in provider_name:
                providers.add('gcp')
        
        assert len(providers) >= 2, "Multi-cloud plan should have multiple providers"
    
    def test_large_plan_structure(self):
        """Test large plan fixture structure"""
        plan = TestFixtures.get_large_plan()
        
        # Verify size
        assert len(plan['resource_changes']) == 100, "Large plan should have 100 resources"
        
        # Verify variety of actions
        actions = set()
        for change in plan['resource_changes']:
            actions.update(change['change']['actions'])
        
        assert len(actions) >= 2, "Large plan should have variety of actions"
    
    def test_security_focused_plan_structure(self):
        """Test security-focused plan fixture structure"""
        plan = TestFixtures.get_security_focused_plan()
        
        # Verify security-related resources
        security_resources = []
        for change in plan['resource_changes']:
            resource_type = change.get('type', '')
            if any(keyword in resource_type.lower() for keyword in ['security', 'iam', 'policy']):
                security_resources.append(change)
        
        assert len(security_resources) > 0, "Security plan should have security-related resources"
    
    def test_invalid_plan_structure(self):
        """Test invalid plan fixture structure"""
        plan = TestFixtures.get_invalid_plan()
        
        # Should be missing required fields or have invalid structure
        assert 'format_version' not in plan or not isinstance(plan.get('resource_changes'), list)
    
    def test_dependency_plan_structure(self):
        """Test dependency plan fixture structure"""
        plan = TestFixtures.get_plan_with_dependencies()
        
        # Verify dependency references
        dependency_found = False
        for change in plan['resource_changes']:
            change_after = change.get('change', {}).get('after', {})
            if change_after:
                for key, value in change_after.items():
                    if isinstance(value, str) and '${' in value:
                        dependency_found = True
                        break
        
        assert dependency_found, "Dependency plan should have resource references"


if __name__ == '__main__':
    pytest.main([__file__])
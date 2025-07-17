import json
import pandas as pd
from typing import Dict, List, Any, Optional
from collections import defaultdict, Counter


class PlanParser:
    """Parser for Terraform plan JSON files"""

    def __init__(self, plan_data: Dict[str, Any]):
        self.plan_data = plan_data
        self.resource_changes = plan_data.get('resource_changes', [])
        self.terraform_version = plan_data.get('terraform_version', 'Unknown')
        self.format_version = plan_data.get('format_version', 'Unknown')

    def get_summary(self) -> Dict[str, int]:
        """Get summary of planned changes"""
        summary = {
            'create': 0,
            'update': 0,
            'delete': 0,
            'total': 0
        }

        for change in self.resource_changes:
            actions = change.get('change', {}).get('actions', [])

            if 'create' in actions:
                summary['create'] += 1
            elif 'update' in actions:
                summary['update'] += 1
            elif 'delete' in actions:
                summary['delete'] += 1

            summary['total'] += 1

        return summary

    def get_resource_changes(self) -> List[Dict[str, Any]]:
        """Get list of all resource changes with normalized structure"""
        changes = []

        for change in self.resource_changes:
            change_actions = change.get('change', {}).get('actions', [])

            # Normalize the action to a single primary action
            primary_action = 'create'
            if 'delete' in change_actions:
                primary_action = 'delete'
            elif 'update' in change_actions:
                primary_action = 'update'

            changes.append({
                'address': change.get('address', ''),
                'type': change.get('type', ''),
                'name': change.get('name', ''),
                'action': primary_action,
                'actions': change_actions,
                'before': change.get('change', {}).get('before'),
                'after': change.get('change', {}).get('after'),
                'change': change.get('change', {})
            })

        return changes

    def get_resource_types(self) -> Dict[str, int]:
        """Get count of resource types being changed"""
        resource_types = Counter()

        for change in self.resource_changes:
            resource_type = change.get('type', 'unknown')
            resource_types[resource_type] += 1

        return dict(resource_types)

    def get_actions_by_type(self) -> Dict[str, Dict[str, int]]:
        """Get breakdown of actions by resource type"""
        actions_by_type = defaultdict(lambda: {'create': 0, 'update': 0, 'delete': 0})

        for change in self.resource_changes:
            resource_type = change.get('type', 'unknown')
            actions = change.get('change', {}).get('actions', [])

            if 'create' in actions:
                actions_by_type[resource_type]['create'] += 1
            elif 'update' in actions:
                actions_by_type[resource_type]['update'] += 1
            elif 'delete' in actions:
                actions_by_type[resource_type]['delete'] += 1

        return dict(actions_by_type)

    def get_sensitive_changes(self) -> List[Dict[str, Any]]:
        """Identify changes involving sensitive values"""
        sensitive_changes = []

        for change in self.resource_changes:
            change_data = change.get('change', {})
            before = change_data.get('before', {})
            after = change_data.get('after', {})

            # Check for sensitive values in before/after
            has_sensitive = False
            if isinstance(before, dict):
                has_sensitive = self._has_sensitive_values(before)
            if isinstance(after, dict) and not has_sensitive:
                has_sensitive = self._has_sensitive_values(after)

            if has_sensitive:
                sensitive_changes.append({
                    'address': change.get('address', ''),
                    'type': change.get('type', ''),
                    'actions': change_data.get('actions', [])
                })

        return sensitive_changes

    def _has_sensitive_values(self, obj: Any) -> bool:
        """Recursively check for sensitive values in an object"""
        if isinstance(obj, dict):
            for key, value in obj.items():
                if value == "(sensitive)" or key.lower() in ['password', 'secret', 'key', 'token']:
                    return True
                if isinstance(value, (dict, list)):
                    if self._has_sensitive_values(value):
                        return True
        elif isinstance(obj, list):
            for item in obj:
                if self._has_sensitive_values(item):
                    return True
        elif isinstance(obj, str) and obj == "(sensitive)":
            return True

        return False

    def create_detailed_dataframe(self, resource_changes: List[Dict[str, Any]]) -> pd.DataFrame:
        """Create a detailed pandas DataFrame from resource changes"""
        rows = []

        for change in resource_changes:
            rows.append({
                'resource_address': change['address'],
                'resource_type': change['type'],
                'resource_name': change['name'] or change['address'].split('.')[-1],
                'action': change['action'],
                'actions_list': ', '.join(change['actions']),
                'has_before': change['before'] is not None,
                'has_after': change['after'] is not None,
                'is_sensitive': self._has_sensitive_values(change['after']) if change['after'] else False
            })

        return pd.DataFrame(rows)

    def get_plan_metadata(self) -> Dict[str, Any]:
        """Get metadata about the plan"""
        return {
            'terraform_version': self.terraform_version,
            'format_version': self.format_version,
            'total_resources': len(self.resource_changes),
            'has_planned_values': 'planned_values' in self.plan_data,
            'has_configuration': 'configuration' in self.plan_data,
            'has_prior_state': 'prior_state' in self.plan_data
        }

    def get_dependency_info(self) -> Dict[str, List[str]]:
        """Extract basic dependency information from configuration"""
        dependencies = {}

        # Try to extract from configuration if available
        config = self.plan_data.get('configuration', {})
        root_module = config.get('root_module', {})
        resources = root_module.get('resources', [])

        for resource in resources:
            address = resource.get('address', '')
            depends_on = resource.get('depends_on', [])

            if depends_on:
                dependencies[address] = depends_on

        return dependencies

    def analyze_blast_radius(self) -> Dict[str, Any]:
        """Analyze the potential blast radius of changes"""
        summary = self.get_summary()
        resource_types = self.get_resource_types()

        # High-impact resource types
        high_impact_types = {
            'aws_security_group', 'aws_vpc', 'aws_subnet', 'aws_route_table',
            'aws_rds_instance', 'aws_rds_cluster', 'aws_elasticsearch_domain',
            'aws_iam_role', 'aws_iam_policy', 'aws_s3_bucket'
        }

        high_impact_count = 0
        for resource_type, count in resource_types.items():
            if any(hit in resource_type for hit in high_impact_types):
                high_impact_count += count

        return {
            'total_changes': summary['total'],
            'high_impact_resources': high_impact_count,
            'blast_radius_score': min(100, (high_impact_count / max(summary['total'], 1)) * 100),
            'delete_operations': summary['delete'],
            'unique_resource_types': len(resource_types)
        }

    def validate_plan_structure(self) -> Dict[str, Any]:
        """Validate the structure of the plan JSON"""
        validation = {
            'is_valid': True,
            'issues': [],
            'warnings': []
        }

        # Check required fields
        if 'resource_changes' not in self.plan_data:
            validation['is_valid'] = False
            validation['issues'].append('Missing resource_changes field')

        if 'terraform_version' not in self.plan_data:
            validation['warnings'].append('Missing terraform_version field')

        # Check resource_changes structure
        if self.resource_changes:
            for i, change in enumerate(self.resource_changes):
                if 'change' not in change:
                    validation['issues'].append(f'Resource change {i} missing change field')
                    validation['is_valid'] = False

                if 'type' not in change:
                    validation['warnings'].append(f'Resource change {i} missing type field')

        return validation
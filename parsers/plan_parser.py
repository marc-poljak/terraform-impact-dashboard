import json
import pandas as pd
from typing import Dict, List, Any, Optional
from collections import defaultdict, Counter


class PlanParser:
    """Enhanced parser for Terraform plan JSON files with multi-cloud support"""

    def __init__(self, plan_data: Dict[str, Any]):
        self.plan_data = plan_data
        self.resource_changes = plan_data.get('resource_changes', [])
        self.terraform_version = plan_data.get('terraform_version', 'Unknown')
        self.format_version = plan_data.get('format_version', 'Unknown')

        # Multi-cloud detection
        self.detected_providers = self._detect_providers()

    def _detect_providers(self) -> Dict[str, int]:
        """Detect cloud providers from resource types"""
        providers = Counter()

        for change in self.resource_changes:
            resource_type = change.get('type', '')
            if resource_type.startswith('aws_'):
                providers['aws'] += 1
            elif resource_type.startswith('azurerm_') or resource_type.startswith('azuread_'):
                providers['azure'] += 1
            elif resource_type.startswith('google_'):
                providers['google'] += 1
            elif resource_type.startswith('kubernetes_'):
                providers['kubernetes'] += 1
            else:
                providers['other'] += 1

        return dict(providers)

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

            # Skip no-op actions (unchanged resources)
            if not actions or actions == ['no-op']:
                continue

            # Handle different action combinations
            if actions == ['create']:
                summary['create'] += 1
            elif actions == ['delete']:
                summary['delete'] += 1
            elif actions == ['update']:
                summary['update'] += 1
            elif set(actions) == {'create', 'delete'}:
                # This is a replacement: destroy old, create new
                # Count as both create and delete for action totals
                summary['create'] += 1
                summary['delete'] += 1
            elif 'update' in actions:
                summary['update'] += 1
            elif 'create' in actions:
                summary['create'] += 1
            elif 'delete' in actions:
                summary['delete'] += 1

        # Calculate total as actual changed resources (not sum of actions)
        # Count replacements as single resources, not double
        total_changed = 0
        for change in self.resource_changes:
            actions = change.get('change', {}).get('actions', [])
            if actions and actions != ['no-op']:
                total_changed += 1

        summary['total'] = total_changed

        return summary

    def get_resource_changes(self) -> List[Dict[str, Any]]:
        """Get list of all resource changes with normalized structure"""
        changes = []

        for change in self.resource_changes:
            change_actions = change.get('change', {}).get('actions', [])

            # Skip no-op actions (unchanged resources)
            if not change_actions or change_actions == ['no-op']:
                continue

            # Normalize the action to a single primary action for display
            if set(change_actions) == {'create', 'delete'}:
                # This is a replacement
                primary_action = 'replace'
            elif 'delete' in change_actions:
                primary_action = 'delete'
            elif 'update' in change_actions:
                primary_action = 'update'
            elif 'create' in change_actions:
                primary_action = 'create'
            else:
                primary_action = 'update'  # Default for unknown actions

            # Extract provider from resource type
            resource_type = change.get('type', '')
            provider = self._extract_provider_from_resource_type(resource_type)

            changes.append({
                'address': change.get('address', ''),
                'type': resource_type,
                'name': change.get('name', ''),
                'action': primary_action,
                'actions': change_actions,
                'before': change.get('change', {}).get('before'),
                'after': change.get('change', {}).get('after'),
                'change': change.get('change', {}),
                'provider': provider  # NEW: Provider information
            })

        return changes

    def _extract_provider_from_resource_type(self, resource_type: str) -> str:
        """Extract provider name from resource type"""
        if resource_type.startswith('aws_'):
            return 'aws'
        elif resource_type.startswith('azurerm_') or resource_type.startswith('azuread_'):
            return 'azure'
        elif resource_type.startswith('google_'):
            return 'google'
        elif resource_type.startswith('kubernetes_'):
            return 'kubernetes'
        else:
            return 'unknown'

    def get_resource_types(self) -> Dict[str, int]:
        """Get count of resource types being changed"""
        resource_types = Counter()

        for change in self.resource_changes:
            actions = change.get('change', {}).get('actions', [])
            # Only count resources that have actual changes (skip no-op)
            if actions and actions != ['no-op']:
                resource_type = change.get('type', 'unknown')
                resource_types[resource_type] += 1

        return dict(resource_types)

    def get_resource_types_by_provider(self) -> Dict[str, Dict[str, int]]:
        """Get resource types grouped by cloud provider"""
        provider_resources = defaultdict(lambda: Counter())

        for change in self.resource_changes:
            actions = change.get('change', {}).get('actions', [])
            if actions and actions != ['no-op']:
                resource_type = change.get('type', 'unknown')
                provider = self._extract_provider_from_resource_type(resource_type)
                provider_resources[provider][resource_type] += 1

        # Convert to regular dicts
        return {provider: dict(resources) for provider, resources in provider_resources.items()}

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

    def get_actions_by_provider(self) -> Dict[str, Dict[str, int]]:
        """Get breakdown of actions by cloud provider"""
        actions_by_provider = defaultdict(lambda: {'create': 0, 'update': 0, 'delete': 0, 'total': 0})

        for change in self.resource_changes:
            actions = change.get('change', {}).get('actions', [])
            if not actions or actions == ['no-op']:
                continue

            resource_type = change.get('type', 'unknown')
            provider = self._extract_provider_from_resource_type(resource_type)

            actions_by_provider[provider]['total'] += 1

            if 'create' in actions:
                actions_by_provider[provider]['create'] += 1
            elif 'update' in actions:
                actions_by_provider[provider]['update'] += 1
            elif 'delete' in actions:
                actions_by_provider[provider]['delete'] += 1

        return dict(actions_by_provider)

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
                provider = self._extract_provider_from_resource_type(change.get('type', ''))
                sensitive_changes.append({
                    'address': change.get('address', ''),
                    'type': change.get('type', ''),
                    'actions': change_data.get('actions', []),
                    'provider': provider  # NEW: Provider information
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
        """Create a detailed pandas DataFrame from resource changes with provider info"""
        rows = []

        for change in resource_changes:
            rows.append({
                'resource_address': change['address'],
                'resource_type': change['type'],
                'resource_name': change['name'] or change['address'].split('.')[-1],
                'action': change['action'],
                'actions_list': ', '.join(change['actions']),
                'provider': change.get('provider', 'unknown'),  # NEW: Provider column
                'has_before': change['before'] is not None,
                'has_after': change['after'] is not None,
                'is_sensitive': self._has_sensitive_values(change['after']) if change['after'] else False
            })

        return pd.DataFrame(rows)

    def get_plan_metadata(self) -> Dict[str, Any]:
        """Get metadata about the plan including multi-cloud info"""
        return {
            'terraform_version': self.terraform_version,
            'format_version': self.format_version,
            'total_resources': len(self.resource_changes),
            'detected_providers': self.detected_providers,  # NEW: Provider detection
            'is_multi_cloud': len([p for p in self.detected_providers.keys() if p in ['aws', 'azure', 'google']]) > 1,
            # NEW
            'primary_provider': max(self.detected_providers.items(), key=lambda x: x[1])[
                0] if self.detected_providers else None,  # NEW
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
        """Analyze the potential blast radius of changes with multi-cloud context"""
        summary = self.get_summary()
        resource_types = self.get_resource_types()
        actions_by_provider = self.get_actions_by_provider()

        # High-impact resource types by provider
        high_impact_types = {
            'aws': [
                'aws_security_group', 'aws_vpc', 'aws_subnet', 'aws_route_table',
                'aws_rds_instance', 'aws_rds_cluster', 'aws_elasticsearch_domain',
                'aws_iam_role', 'aws_iam_policy', 'aws_s3_bucket', 'aws_kms_key'
            ],
            'azure': [
                'azurerm_network_security_group', 'azurerm_virtual_network', 'azurerm_subnet',
                'azurerm_sql_server', 'azurerm_cosmosdb_account', 'azurerm_role_assignment',
                'azurerm_key_vault', 'azurerm_kubernetes_cluster'
            ],
            'google': [
                'google_compute_firewall', 'google_compute_network', 'google_compute_subnetwork',
                'google_sql_database_instance', 'google_spanner_instance', 'google_project_iam_policy',
                'google_kms_crypto_key', 'google_container_cluster'
            ]
        }

        high_impact_count = 0
        high_impact_by_provider = {}

        for provider, types in high_impact_types.items():
            provider_high_impact = 0
            for resource_type, count in resource_types.items():
                if resource_type in types:
                    provider_high_impact += count
            high_impact_by_provider[provider] = provider_high_impact
            high_impact_count += provider_high_impact

        # Multi-cloud complexity factor
        cloud_providers = [p for p in self.detected_providers.keys() if p in ['aws', 'azure', 'google']]
        multi_cloud_complexity = len(cloud_providers) if len(cloud_providers) > 1 else 0

        return {
            'total_changes': summary['total'],
            'high_impact_resources': high_impact_count,
            'high_impact_by_provider': high_impact_by_provider,  # NEW
            'blast_radius_score': min(100, (high_impact_count / max(summary['total'], 1)) * 100),
            'delete_operations': summary['delete'],
            'unique_resource_types': len(resource_types),
            'detected_providers': self.detected_providers,  # NEW
            'multi_cloud_complexity': multi_cloud_complexity,  # NEW
            'actions_by_provider': actions_by_provider  # NEW
        }

    def get_cross_provider_dependencies(self) -> List[Dict[str, Any]]:
        """Identify potential cross-provider dependencies (NEW METHOD)"""
        cross_deps = []

        # Look for resources that might depend on other providers
        for change in self.resource_changes:
            resource_type = change.get('type', '')
            provider = self._extract_provider_from_resource_type(resource_type)

            # Check if resource configuration references other providers
            after_config = change.get('change', {}).get('after', {})
            if isinstance(after_config, dict):
                for key, value in after_config.items():
                    if isinstance(value, str):
                        # Look for references to other cloud providers
                        other_providers = []
                        if provider != 'aws' and ('aws' in value.lower() or '.amazonaws.com' in value):
                            other_providers.append('aws')
                        if provider != 'azure' and ('azure' in value.lower() or '.azure.com' in value):
                            other_providers.append('azure')
                        if provider != 'google' and ('gcp' in value.lower() or '.googleapis.com' in value):
                            other_providers.append('google')

                        if other_providers:
                            cross_deps.append({
                                'resource': change.get('address', ''),
                                'resource_type': resource_type,
                                'primary_provider': provider,
                                'referenced_providers': other_providers,
                                'config_key': key,
                                'potential_dependency': True
                            })

        return cross_deps

    def get_provider_risk_distribution(self) -> Dict[str, Dict[str, Any]]:
        """Get risk distribution by provider (NEW METHOD)"""
        provider_distribution = {}
        actions_by_provider = self.get_actions_by_provider()

        for provider, actions in actions_by_provider.items():
            if provider == 'unknown':
                continue

            # Calculate basic risk metrics per provider
            delete_ratio = actions['delete'] / max(actions['total'], 1)
            update_ratio = actions['update'] / max(actions['total'], 1)

            # Simple risk score based on operations
            risk_score = (delete_ratio * 3) + (update_ratio * 1.5) + 1
            risk_score = min(10, risk_score)

            if risk_score >= 7:
                risk_level = 'High'
            elif risk_score >= 4:
                risk_level = 'Medium'
            else:
                risk_level = 'Low'

            provider_distribution[provider] = {
                'total_resources': actions['total'],
                'create_count': actions['create'],
                'update_count': actions['update'],
                'delete_count': actions['delete'],
                'risk_score': round(risk_score, 1),
                'risk_level': risk_level,
                'delete_ratio': round(delete_ratio * 100, 1),
                'update_ratio': round(update_ratio * 100, 1)
            }

        return provider_distribution

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

        # Multi-cloud validation
        if len(self.detected_providers) > 3:
            validation['warnings'].append(
                f'Many providers detected ({len(self.detected_providers)}), verify plan accuracy')

        return validation

    def get_debug_info(self) -> Dict[str, Any]:
        """Get debug information for troubleshooting with multi-cloud context"""
        action_patterns = {}
        total_resource_changes = len(self.resource_changes)

        for change in self.resource_changes:
            actions = change.get('change', {}).get('actions', [])
            pattern = str(sorted(actions))
            action_patterns[pattern] = action_patterns.get(pattern, 0) + 1

        return {
            'total_resource_changes': total_resource_changes,
            'action_patterns': action_patterns,
            'detected_providers': self.detected_providers,  # NEW
            'provider_breakdown': self.get_actions_by_provider(),  # NEW
            'cross_provider_deps': len(self.get_cross_provider_dependencies()),  # NEW
            'has_planned_values': 'planned_values' in self.plan_data,
            'has_configuration': 'configuration' in self.plan_data,
            'has_prior_state': 'prior_state' in self.plan_data,
            'plan_keys': list(self.plan_data.keys())
        }
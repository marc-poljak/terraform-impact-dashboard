from typing import Dict, List, Any, Optional, Union
from providers.base_provider import BaseCloudProvider
from providers.aws_provider import AWSProvider
from providers.azure_provider import AzureProvider
from providers.gcp_provider import GCPProvider
from providers.cloud_detector import CloudProviderDetector


class MultiCloudProviderFactory:
    """Factory for creating and managing multiple cloud providers"""

    def __init__(self):
        self.detector = CloudProviderDetector()
        self.providers = {
            'aws': AWSProvider,
            'azure': AzureProvider,
            'google': GCPProvider
        }
        self._provider_instances = {}

    def detect_and_create_providers(self, plan_data: Dict) -> Dict[str, Any]:
        """Detect providers from plan and create appropriate provider instances"""
        detection_results = self.detector.detect_providers_from_plan(plan_data)

        # Create provider instances for detected cloud providers
        active_providers = {}
        cloud_providers = [p for p in detection_results['all_providers'] if p in self.providers]

        for provider_name in cloud_providers:
            if provider_name not in self._provider_instances:
                self._provider_instances[provider_name] = self.providers[provider_name]()
            active_providers[provider_name] = self._provider_instances[provider_name]

        return {
            'detection_results': detection_results,
            'active_providers': active_providers,
            'primary_provider': detection_results['primary_provider'],
            'is_multi_cloud': detection_results['multi_cloud']
        }

    def get_provider_for_resource(self, resource_type: str, active_providers: Dict[str, BaseCloudProvider]) -> Optional[
        BaseCloudProvider]:
        """Get the appropriate provider for a specific resource type"""
        for provider_name, provider_instance in active_providers.items():
            if provider_instance.supports_resource_type(resource_type):
                return provider_instance

        # Fallback: try to extract provider from resource type
        provider_name = self._extract_provider_name(resource_type)
        if provider_name in active_providers:
            return active_providers[provider_name]

        return None

    def _extract_provider_name(self, resource_type: str) -> Optional[str]:
        """Extract provider name from resource type"""
        if resource_type.startswith('aws_'):
            return 'aws'
        elif resource_type.startswith('azurerm_') or resource_type.startswith('azuread_'):
            return 'azure'
        elif resource_type.startswith('google_'):
            return 'google'
        return None


class MultiCloudRiskAssessment:
    """Multi-cloud aware risk assessment"""

    def __init__(self, provider_factory: MultiCloudProviderFactory):
        self.factory = provider_factory
        self.base_action_multipliers = {
            'create': 1.0,
            'update': 1.5,
            'delete': 2.5
        }

    def assess_multi_cloud_plan_risk(self, plan_data: Dict) -> Dict[str, Any]:
        """Assess risk for a multi-cloud Terraform plan"""
        # Detect providers and create instances
        provider_info = self.factory.detect_and_create_providers(plan_data)

        resource_changes = plan_data.get('resource_changes', [])
        if not resource_changes:
            return self._empty_risk_assessment()

        # Assess each resource with its appropriate provider
        risk_assessments = []
        provider_risk_summary = {}

        for change in resource_changes:
            if not self._is_actionable_change(change):
                continue

            resource_type = change.get('type', '')
            provider = self.factory.get_provider_for_resource(resource_type, provider_info['active_providers'])

            if provider:
                risk_assessment = self._assess_resource_with_provider(change, provider)
                risk_assessment['provider'] = provider.provider_name
                risk_assessments.append(risk_assessment)

                # Track by provider
                provider_name = provider.provider_name
                if provider_name not in provider_risk_summary:
                    provider_risk_summary[provider_name] = {
                        'total_resources': 0,
                        'high_risk_count': 0,
                        'medium_risk_count': 0,
                        'low_risk_count': 0,
                        'total_risk_score': 0.0
                    }

                provider_risk_summary[provider_name]['total_resources'] += 1
                provider_risk_summary[provider_name]['total_risk_score'] += risk_assessment['score']

                if risk_assessment['level'] == 'High':
                    provider_risk_summary[provider_name]['high_risk_count'] += 1
                elif risk_assessment['level'] == 'Medium':
                    provider_risk_summary[provider_name]['medium_risk_count'] += 1
                else:
                    provider_risk_summary[provider_name]['low_risk_count'] += 1
            else:
                # Fallback for unknown providers
                risk_assessment = self._assess_unknown_resource(change)
                risk_assessment['provider'] = 'unknown'
                risk_assessments.append(risk_assessment)

        # Calculate overall risk
        overall_risk = self._calculate_overall_risk(risk_assessments, provider_info)

        # Generate multi-cloud specific recommendations
        recommendations = self._generate_multi_cloud_recommendations(
            risk_assessments, provider_info, provider_risk_summary
        )

        return {
            'overall_risk': overall_risk,
            'provider_detection': provider_info['detection_results'],
            'provider_risk_summary': provider_risk_summary,
            'resource_assessments': risk_assessments,
            'recommendations': recommendations,
            'is_multi_cloud': provider_info['is_multi_cloud'],
            'primary_provider': provider_info['primary_provider']
        }

    def _is_actionable_change(self, change: Dict[str, Any]) -> bool:
        """Check if change has actionable operations"""
        actions = change.get('change', {}).get('actions', [])
        return actions and actions != ['no-op']

    def _assess_resource_with_provider(self, change: Dict[str, Any], provider: BaseCloudProvider) -> Dict[str, Any]:
        """Assess resource risk using appropriate provider"""
        resource_type = change.get('type', '')
        actions = change.get('change', {}).get('actions', [])

        # Get base risk score from provider
        base_risk = provider.get_resource_risk_score(resource_type)

        # Get action multiplier from provider
        action_multipliers = provider.get_action_multipliers()
        action_multiplier = max([action_multipliers.get(action, 1.0) for action in actions])

        # Apply provider-specific deployment time multiplier
        deployment_multiplier = provider.get_deployment_time_multiplier()

        # Calculate final risk score
        risk_score = min(10, base_risk * action_multiplier)

        # Determine risk level
        if risk_score >= 7:
            risk_level = "High"
        elif risk_score >= 4:
            risk_level = "Medium"
        else:
            risk_level = "Low"

        # Identify risk factors
        risk_factors = self._identify_risk_factors(change, provider)

        return {
            'address': change.get('address', ''),
            'type': resource_type,
            'actions': actions,
            'score': round(risk_score, 1),
            'level': risk_level,
            'base_score': base_risk,
            'action_multiplier': action_multiplier,
            'deployment_multiplier': deployment_multiplier,
            'risk_factors': risk_factors,
            'category': provider.categorize_resource(resource_type).value
        }

    def _assess_unknown_resource(self, change: Dict[str, Any]) -> Dict[str, Any]:
        """Assess resource risk for unknown providers"""
        actions = change.get('change', {}).get('actions', [])

        # Use default risk assessment
        base_risk = 4.0  # Medium default risk
        action_multiplier = max([self.base_action_multipliers.get(action, 1.0) for action in actions])
        risk_score = min(10, base_risk * action_multiplier)

        if risk_score >= 7:
            risk_level = "High"
        elif risk_score >= 4:
            risk_level = "Medium"
        else:
            risk_level = "Low"

        return {
            'address': change.get('address', ''),
            'type': change.get('type', ''),
            'actions': actions,
            'score': round(risk_score, 1),
            'level': risk_level,
            'base_score': base_risk,
            'action_multiplier': action_multiplier,
            'deployment_multiplier': 1.0,
            'risk_factors': ['Unknown provider'],
            'category': 'unknown'
        }

    def _identify_risk_factors(self, change: Dict[str, Any], provider: BaseCloudProvider) -> List[str]:
        """Identify risk factors for a resource change"""
        factors = []

        resource_type = change.get('type', '')
        actions = change.get('change', {}).get('actions', [])

        # Action-based factors
        if 'delete' in actions:
            factors.append("Resource deletion")
        if 'update' in actions:
            factors.append("Configuration changes")

        # Provider-specific critical resource check
        if provider.is_critical_resource(resource_type):
            factors.append("Critical infrastructure resource")

        # Check for sensitive values
        if self._has_sensitive_changes(change):
            factors.append("Sensitive data involved")

        return factors

    def _has_sensitive_changes(self, change: Dict[str, Any]) -> bool:
        """Check if resource change involves sensitive data"""
        change_data = change.get('change', {})
        after = change_data.get('after', {})

        if isinstance(after, dict):
            for key, value in after.items():
                if value == "(sensitive)" or key.lower() in ['password', 'secret', 'key', 'token']:
                    return True
        return False

    def _calculate_overall_risk(self, risk_assessments: List[Dict[str, Any]], provider_info: Dict) -> Dict[str, Any]:
        """Calculate overall risk for the multi-cloud plan"""
        if not risk_assessments:
            return {
                'level': 'Low',
                'score': 0,
                'total_resources': 0,
                'high_risk_count': 0,
                'medium_risk_count': 0,
                'low_risk_count': 0,
                'estimated_time': '< 5 minutes'
            }

        # Count risk levels
        risk_counts = {'High': 0, 'Medium': 0, 'Low': 0}
        total_score = 0

        for assessment in risk_assessments:
            risk_counts[assessment['level']] += 1
            total_score += assessment['score']

        # Calculate weighted risk score
        total_resources = len(risk_assessments)
        max_possible_score = total_resources * 10
        overall_score = (total_score / max_possible_score) * 100 if max_possible_score > 0 else 0

        # Adjust for multi-cloud complexity
        if provider_info['is_multi_cloud']:
            overall_score *= 1.15  # 15% increase for multi-cloud complexity

        # Adjust for high-risk resource concentration
        high_risk_ratio = risk_counts['High'] / total_resources
        if high_risk_ratio > 0.3:
            overall_score *= 1.2

        overall_score = min(100, overall_score)

        # Determine overall level
        if overall_score >= 70 or risk_counts['High'] > 0:
            overall_level = "High"
        elif overall_score >= 40 or risk_counts['Medium'] > 2:
            overall_level = "Medium"
        else:
            overall_level = "Low"

        # Estimate deployment time
        estimated_time = self._estimate_multi_cloud_deployment_time(risk_assessments, provider_info)

        return {
            'level': overall_level,
            'score': round(overall_score),
            'total_resources': total_resources,
            'high_risk_count': risk_counts['High'],
            'medium_risk_count': risk_counts['Medium'],
            'low_risk_count': risk_counts['Low'],
            'estimated_time': estimated_time,
            'average_risk_score': round(total_score / total_resources, 1) if total_resources > 0 else 0
        }

    def _estimate_multi_cloud_deployment_time(self, risk_assessments: List[Dict[str, Any]], provider_info: Dict) -> str:
        """Estimate deployment time for multi-cloud setup"""
        base_time_per_resource = 30  # seconds

        total_time = 0
        provider_multipliers = {}

        # Get deployment multipliers from active providers
        for provider_name, provider_instance in provider_info['active_providers'].items():
            provider_multipliers[provider_name] = provider_instance.get_deployment_time_multiplier()

        # Calculate time per resource with provider-specific multipliers
        for assessment in risk_assessments:
            provider = assessment.get('provider', 'unknown')
            risk_multiplier = {'Low': 1.0, 'Medium': 1.5, 'High': 2.0}[assessment['level']]
            provider_multiplier = provider_multipliers.get(provider, 1.0)

            resource_time = base_time_per_resource * risk_multiplier * provider_multiplier
            total_time += resource_time

        # Add multi-cloud coordination overhead
        if provider_info['is_multi_cloud']:
            total_time *= 1.3  # 30% overhead for multi-cloud coordination

        # Convert to human-readable format
        if total_time < 300:
            return "< 5 minutes"
        elif total_time < 900:
            return "5-15 minutes"
        elif total_time < 1800:
            return "15-30 minutes"
        elif total_time < 3600:
            return "30-60 minutes"
        else:
            hours = total_time // 3600
            return f"{int(hours)}+ hours"

    def _generate_multi_cloud_recommendations(self, risk_assessments: List[Dict[str, Any]],
                                              provider_info: Dict,
                                              provider_risk_summary: Dict) -> List[str]:
        """Generate multi-cloud specific recommendations"""
        recommendations = []

        # Multi-cloud specific recommendations
        if provider_info['is_multi_cloud']:
            cloud_providers = [p for p in provider_info['active_providers'].keys()]
            recommendations.append(
                f"🌐 Multi-cloud deployment with {len(cloud_providers)} providers: {', '.join([p.upper() for p in cloud_providers])}")
            recommendations.append("🔗 Verify cross-cloud networking and data transfer configurations")
            recommendations.append("💰 Consider data egress costs between cloud providers")
            recommendations.append("🔒 Ensure consistent security policies across all providers")

        # Provider-specific recommendations
        for provider_name, provider_instance in provider_info['active_providers'].items():
            provider_resources = [r for r in risk_assessments if r.get('provider') == provider_name]
            if provider_resources:
                provider_recommendations = provider_instance.get_provider_specific_recommendations(
                    [{'type': r['type'], 'action': r['actions'][0] if r['actions'] else 'update',
                      'address': r['address']}
                     for r in provider_resources]
                )
                recommendations.extend([f"[{provider_name.upper()}] {rec}" for rec in provider_recommendations])

        # Risk-based recommendations
        high_risk_count = sum(1 for r in risk_assessments if r['level'] == 'High')
        if high_risk_count > 0:
            recommendations.append(f"⚠️ {high_risk_count} high-risk resources require careful review")

        if high_risk_count > 5:
            recommendations.append("📊 Consider staging deployment across multiple phases")

        # Provider risk distribution
        if len(provider_risk_summary) > 1:
            riskiest_provider = max(provider_risk_summary.keys(),
                                    key=lambda p: provider_risk_summary[p]['high_risk_count'])
            if provider_risk_summary[riskiest_provider]['high_risk_count'] > 0:
                recommendations.append(f"🎯 Highest risk concentration in {riskiest_provider.upper()}")

        return recommendations

    def _empty_risk_assessment(self) -> Dict[str, Any]:
        """Return empty risk assessment for plans with no changes"""
        return {
            'overall_risk': {
                'level': 'Low',
                'score': 0,
                'total_resources': 0,
                'high_risk_count': 0,
                'medium_risk_count': 0,
                'low_risk_count': 0,
                'estimated_time': '< 5 minutes'
            },
            'provider_detection': {
                'primary_provider': None,
                'all_providers': [],
                'multi_cloud': False
            },
            'provider_risk_summary': {},
            'resource_assessments': [],
            'recommendations': ["✅ No changes detected in this plan"],
            'is_multi_cloud': False,
            'primary_provider': None
        }
from typing import Dict, List, Set, Optional, Tuple
from collections import Counter
import re


class CloudProviderDetector:
    """Automatically detect cloud providers from Terraform plan data"""

    def __init__(self):
        self.provider_patterns = {
            'aws': {
                'prefixes': ['aws_'],
                'patterns': [
                    r'aws_.*',
                    r'data\.aws_.*'
                ],
                'keywords': ['amazon', 'aws', 'ec2', 's3', 'rds', 'lambda']
            },
            'azure': {
                'prefixes': ['azurerm_', 'azuread_', 'azurestack_'],
                'patterns': [
                    r'azurerm_.*',
                    r'azuread_.*',
                    r'azurestack_.*',
                    r'data\.azurerm_.*'
                ],
                'keywords': ['azure', 'microsoft', 'azurerm', 'resource_group']
            },
            'google': {
                'prefixes': ['google_', 'google-beta_'],
                'patterns': [
                    r'google_.*',
                    r'google-beta_.*',
                    r'data\.google_.*'
                ],
                'keywords': ['google', 'gcp', 'compute', 'project_id', 'googleapis']
            },
            'kubernetes': {
                'prefixes': ['kubernetes_', 'helm_'],
                'patterns': [
                    r'kubernetes_.*',
                    r'helm_.*'
                ],
                'keywords': ['kubernetes', 'k8s', 'helm', 'namespace']
            },
            'terraform': {
                'prefixes': ['terraform_', 'tfe_', 'tls_', 'random_', 'local_', 'null_'],
                'patterns': [
                    r'terraform_.*',
                    r'tfe_.*',
                    r'tls_.*',
                    r'random_.*',
                    r'local_.*',
                    r'null_.*'
                ],
                'keywords': ['terraform', 'provider', 'backend']
            }
        }

    def detect_providers_from_plan(self, plan_data: Dict) -> Dict[str, Dict]:
        """Detect cloud providers from Terraform plan data"""
        resource_changes = plan_data.get('resource_changes', [])
        configuration = plan_data.get('configuration', {})

        results = {
            'primary_provider': None,
            'all_providers': {},
            'resource_distribution': {},
            'multi_cloud': False,
            'provider_confidence': {},
            'recommendations': []
        }

        # Analyze resource changes
        provider_counts = Counter()
        resource_by_provider = {}

        for change in resource_changes:
            resource_type = change.get('type', '')
            if not resource_type:
                continue

            detected_provider = self._detect_provider_from_resource_type(resource_type)
            if detected_provider:
                provider_counts[detected_provider] += 1
                if detected_provider not in resource_by_provider:
                    resource_by_provider[detected_provider] = []
                resource_by_provider[detected_provider].append(resource_type)

        # Analyze configuration for additional provider info
        config_providers = self._detect_providers_from_configuration(configuration)

        # Combine results
        all_providers = set(provider_counts.keys()) | set(config_providers.keys())

        # Calculate confidence scores
        total_resources = sum(provider_counts.values())
        confidence_scores = {}

        for provider in all_providers:
            resource_count = provider_counts.get(provider, 0)
            config_presence = 1.0 if provider in config_providers else 0.0

            # Calculate confidence based on resource count and config presence
            resource_confidence = resource_count / max(total_resources, 1) if total_resources > 0 else 0
            overall_confidence = (resource_confidence * 0.8) + (config_presence * 0.2)

            confidence_scores[provider] = {
                'score': overall_confidence,
                'resource_count': resource_count,
                'config_detected': provider in config_providers,
                'percentage': (resource_count / max(total_resources, 1)) * 100 if total_resources > 0 else 0
            }

        # Determine primary provider
        if confidence_scores:
            primary_provider = max(confidence_scores.keys(), key=lambda p: confidence_scores[p]['score'])
            results['primary_provider'] = primary_provider

        # Check if multi-cloud
        cloud_providers = [p for p in all_providers if p in ['aws', 'azure', 'google']]
        results['multi_cloud'] = len(cloud_providers) > 1

        # Set results
        results['all_providers'] = list(all_providers)
        results['resource_distribution'] = dict(provider_counts)
        results['provider_confidence'] = confidence_scores

        # Generate recommendations
        results['recommendations'] = self._generate_detection_recommendations(
            confidence_scores, results['multi_cloud'], cloud_providers
        )

        return results

    def _detect_provider_from_resource_type(self, resource_type: str) -> Optional[str]:
        """Detect provider from a single resource type"""
        for provider, config in self.provider_patterns.items():
            # Check prefixes
            for prefix in config['prefixes']:
                if resource_type.startswith(prefix):
                    return provider

            # Check patterns
            for pattern in config['patterns']:
                if re.match(pattern, resource_type):
                    return provider

        return None

    def _detect_providers_from_configuration(self, configuration: Dict) -> Dict[str, bool]:
        """Detect providers from Terraform configuration"""
        providers = {}

        # Check provider blocks
        provider_configs = configuration.get('provider_config', {})
        for provider_name in provider_configs.keys():
            # Map Terraform provider names to our internal names
            if provider_name.startswith('registry.terraform.io/hashicorp/'):
                provider_name = provider_name.split('/')[-1]

            if provider_name == 'aws':
                providers['aws'] = True
            elif provider_name in ['azurerm', 'azuread']:
                providers['azure'] = True
            elif provider_name in ['google', 'google-beta']:
                providers['google'] = True
            elif provider_name == 'kubernetes':
                providers['kubernetes'] = True
            else:
                providers[provider_name] = True

        return providers

    def _generate_detection_recommendations(self, confidence_scores: Dict,
                                            is_multi_cloud: bool,
                                            cloud_providers: List[str]) -> List[str]:
        """Generate recommendations based on provider detection"""
        recommendations = []

        if is_multi_cloud:
            recommendations.append(
                f"🌐 Multi-cloud deployment detected with {len(cloud_providers)} providers: {', '.join(cloud_providers)}"
            )
            recommendations.append(
                "🔍 Consider reviewing cross-cloud networking and security configurations"
            )
            recommendations.append(
                "💰 Multi-cloud setups may have additional data transfer costs"
            )

        # Check for low confidence detections
        low_confidence_providers = [
            provider for provider, data in confidence_scores.items()
            if data['score'] < 0.1 and data['resource_count'] > 0
        ]

        if low_confidence_providers:
            recommendations.append(
                f"⚠️ Low confidence detection for: {', '.join(low_confidence_providers)}"
            )

        # Check for infrastructure utility providers
        utility_providers = [p for p in confidence_scores.keys() if p in ['terraform', 'kubernetes']]
        if utility_providers:
            recommendations.append(
                f"🔧 Infrastructure utilities detected: {', '.join(utility_providers)}"
            )

        return recommendations

    def get_provider_summary(self, detection_results: Dict) -> str:
        """Generate a human-readable summary of provider detection"""
        if not detection_results['all_providers']:
            return "No cloud providers detected"

        primary = detection_results['primary_provider']
        total_providers = len(detection_results['all_providers'])

        if detection_results['multi_cloud']:
            cloud_providers = [p for p in detection_results['all_providers'] if p in ['aws', 'azure', 'google']]
            return f"Multi-cloud setup: Primary {primary.upper()}, {total_providers} total providers ({', '.join(cloud_providers)})"
        else:
            if primary in ['aws', 'azure', 'google']:
                return f"Single cloud provider: {primary.upper()}"
            else:
                return f"Primary provider: {primary}, {total_providers} total providers"

    def get_detailed_analysis(self, detection_results: Dict) -> Dict[str, any]:
        """Get detailed analysis of the provider detection"""
        analysis = {
            'summary': self.get_provider_summary(detection_results),
            'provider_breakdown': [],
            'risks_and_considerations': [],
            'optimization_opportunities': []
        }

        # Provider breakdown
        for provider, confidence_data in detection_results['provider_confidence'].items():
            analysis['provider_breakdown'].append({
                'provider': provider.upper(),
                'confidence': f"{confidence_data['score']:.1%}",
                'resources': confidence_data['resource_count'],
                'percentage': f"{confidence_data['percentage']:.1f}%"
            })

        # Sort by confidence
        analysis['provider_breakdown'].sort(key=lambda x: float(x['confidence'].rstrip('%')), reverse=True)

        # Risks and considerations
        if detection_results['multi_cloud']:
            analysis['risks_and_considerations'].extend([
                "Cross-cloud data transfer costs",
                "Complex networking and security configuration",
                "Multiple provider expertise required",
                "Increased operational complexity"
            ])

        # Optimization opportunities
        primary_provider = detection_results['primary_provider']
        if primary_provider in ['aws', 'azure', 'google']:
            analysis['optimization_opportunities'].append(
                f"Consider consolidating resources within {primary_provider.upper()} ecosystem"
            )

        return analysis
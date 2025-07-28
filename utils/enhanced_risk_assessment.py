from typing import Dict, List, Any
from collections import defaultdict
from .provider_factory import MultiCloudProviderFactory, MultiCloudRiskAssessment


class EnhancedRiskAssessment:
    """Enhanced risk assessment that replaces the original RiskAssessment class"""

    def __init__(self):
        self.provider_factory = MultiCloudProviderFactory()
        self.multi_cloud_assessment = MultiCloudRiskAssessment(self.provider_factory)

    def assess_resource_risk(self, resource_change: Dict[str, Any], plan_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Assess risk for a single resource change (compatibility method)"""
        # For backward compatibility, we'll do a mini assessment
        if plan_data:
            provider_info = self.provider_factory.detect_and_create_providers(plan_data)
            provider = self.provider_factory.get_provider_for_resource(
                resource_change.get('type', ''),
                provider_info['active_providers']
            )

            if provider:
                return self.multi_cloud_assessment._assess_resource_with_provider(resource_change, provider)

        # Fallback to unknown resource assessment
        return self.multi_cloud_assessment._assess_unknown_resource(resource_change)

    def assess_plan_risk(self, resource_changes: List[Dict[str, Any]], plan_data: Dict[str, Any] = None) -> Dict[
        str, Any]:
        """Assess overall risk for the entire plan"""
        if plan_data is None:
            # Create minimal plan data from resource changes
            plan_data = {'resource_changes': resource_changes}

        # Use multi-cloud assessment
        multi_cloud_result = self.multi_cloud_assessment.assess_multi_cloud_plan_risk(plan_data)

        # Transform to match original interface
        return {
            'level': multi_cloud_result['overall_risk']['level'],
            'score': multi_cloud_result['overall_risk']['score'],
            'high_risk_count': multi_cloud_result['overall_risk']['high_risk_count'],
            'medium_risk_count': multi_cloud_result['overall_risk']['medium_risk_count'],
            'low_risk_count': multi_cloud_result['overall_risk']['low_risk_count'],
            'estimated_time': multi_cloud_result['overall_risk']['estimated_time'],
            'average_risk_score': multi_cloud_result['overall_risk']['average_risk_score'],

            # Enhanced multi-cloud specific data
            'provider_detection': multi_cloud_result['provider_detection'],
            'provider_risk_summary': multi_cloud_result['provider_risk_summary'],
            'is_multi_cloud': multi_cloud_result['is_multi_cloud'],
            'primary_provider': multi_cloud_result['primary_provider'],
            'detailed_assessments': multi_cloud_result['resource_assessments']
        }

    def get_risk_by_resource_type(self, resource_changes: List[Dict[str, Any]], plan_data: Dict[str, Any] = None) -> \
    Dict[str, Dict[str, int]]:
        """Get risk level breakdown by resource type"""
        full_assessment = self.assess_plan_risk(resource_changes, plan_data)

        risk_by_type = defaultdict(lambda: {'Low': 0, 'Medium': 0, 'High': 0})

        if 'detailed_assessments' in full_assessment:
            for assessment in full_assessment['detailed_assessments']:
                resource_type = assessment['type']
                risk_level = assessment['level']
                risk_by_type[resource_type][risk_level] += 1
        else:
            # Fallback for backward compatibility
            for change in resource_changes:
                resource_type = change.get('type', 'unknown')
                risk_assessment = self.assess_resource_risk(change, plan_data)
                risk_level = risk_assessment['level']
                risk_by_type[resource_type][risk_level] += 1

        return dict(risk_by_type)

    def get_high_risk_resources(self, resource_changes: List[Dict[str, Any]], plan_data: Dict[str, Any] = None) -> List[
        Dict[str, Any]]:
        """Get list of high-risk resource changes"""
        full_assessment = self.assess_plan_risk(resource_changes, plan_data)

        high_risk_resources = []

        if 'detailed_assessments' in full_assessment:
            for assessment in full_assessment['detailed_assessments']:
                if assessment['level'] == 'High':
                    high_risk_resources.append({
                        'address': assessment['address'],
                        'type': assessment['type'],
                        'action': assessment['actions'][0] if assessment['actions'] else 'update',
                        'risk_score': assessment['score'],
                        'risk_factors': assessment['risk_factors'],
                        'provider': assessment.get('provider', 'unknown'),
                        'category': assessment.get('category', 'unknown')
                    })
        else:
            # Fallback for backward compatibility
            for change in resource_changes:
                risk_assessment = self.assess_resource_risk(change, plan_data)
                if risk_assessment['level'] == 'High':
                    high_risk_resources.append({
                        'address': change.get('address', ''),
                        'type': change.get('type', ''),
                        'action': change.get('action', ''),
                        'risk_score': risk_assessment['score'],
                        'risk_factors': risk_assessment.get('risk_factors', [])
                    })

        return high_risk_resources

    def generate_recommendations(self, resource_changes: List[Dict[str, Any]], plan_data: Dict[str, Any] = None) -> \
    List[str]:
        """Generate deployment recommendations based on risk assessment"""
        full_assessment = self.multi_cloud_assessment.assess_multi_cloud_plan_risk(
            plan_data or {'resource_changes': resource_changes}
        )

        return full_assessment['recommendations']

    def get_provider_breakdown(self, resource_changes: List[Dict[str, Any]], plan_data: Dict[str, Any] = None) -> Dict[
        str, Any]:
        """Get breakdown of resources by cloud provider"""
        full_assessment = self.assess_plan_risk(resource_changes, plan_data)

        return {
            'provider_detection': full_assessment.get('provider_detection', {}),
            'provider_risk_summary': full_assessment.get('provider_risk_summary', {}),
            'is_multi_cloud': full_assessment.get('is_multi_cloud', False),
            'primary_provider': full_assessment.get('primary_provider')
        }

    def get_cross_cloud_insights(self, resource_changes: List[Dict[str, Any]], plan_data: Dict[str, Any] = None) -> \
    Dict[str, Any]:
        """Get insights specific to multi-cloud deployments"""
        provider_breakdown = self.get_provider_breakdown(resource_changes, plan_data)

        insights = {
            'is_multi_cloud': provider_breakdown['is_multi_cloud'],
            'provider_count': len(provider_breakdown['provider_risk_summary']),
            'cross_cloud_risks': [],
            'optimization_opportunities': [],
            'security_considerations': []
        }

        if provider_breakdown['is_multi_cloud']:
            # Cross-cloud risks
            insights['cross_cloud_risks'] = [
                "Data transfer costs between cloud providers",
                "Network latency and connectivity complexity",
                "Inconsistent security models and compliance requirements",
                "Multiple vendor relationships and support channels",
                "Increased operational complexity and monitoring overhead"
            ]

            # Optimization opportunities
            insights['optimization_opportunities'] = [
                "Consider workload consolidation within primary provider",
                "Evaluate cross-cloud networking solutions (VPN, dedicated connections)",
                "Implement unified monitoring and logging strategy",
                "Standardize deployment pipelines across providers"
            ]

            # Security considerations
            insights['security_considerations'] = [
                "Ensure consistent identity and access management",
                "Implement unified secrets management",
                "Review cross-cloud data encryption requirements",
                "Establish consistent backup and disaster recovery procedures"
            ]

        return insights

    # Additional methods for enhanced functionality
    def get_resource_category_analysis(self, resource_changes: List[Dict[str, Any]],
                                       plan_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Analyze resources by category (compute, networking, storage, etc.)"""
        full_assessment = self.assess_plan_risk(resource_changes, plan_data)

        category_analysis = defaultdict(lambda: {
            'count': 0,
            'high_risk': 0,
            'medium_risk': 0,
            'low_risk': 0,
            'avg_risk_score': 0.0,
            'resources': []
        })

        if 'detailed_assessments' in full_assessment:
            for assessment in full_assessment['detailed_assessments']:
                category = assessment.get('category', 'unknown')
                category_analysis[category]['count'] += 1
                category_analysis[category]['resources'].append(assessment['type'])

                if assessment['level'] == 'High':
                    category_analysis[category]['high_risk'] += 1
                elif assessment['level'] == 'Medium':
                    category_analysis[category]['medium_risk'] += 1
                else:
                    category_analysis[category]['low_risk'] += 1

        # Calculate average risk scores
        for category in category_analysis:
            if category_analysis[category]['count'] > 0:
                total_score = sum(
                    assessment['score'] for assessment in full_assessment.get('detailed_assessments', [])
                    if assessment.get('category') == category
                )
                category_analysis[category]['avg_risk_score'] = round(
                    total_score / category_analysis[category]['count'], 1
                )

        return dict(category_analysis)

    def get_deployment_timeline_estimate(self, resource_changes: List[Dict[str, Any]],
                                         plan_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Get detailed deployment timeline estimate"""
        full_assessment = self.assess_plan_risk(resource_changes, plan_data)
        provider_breakdown = self.get_provider_breakdown(resource_changes, plan_data)

        timeline = {
            'total_estimated_time': full_assessment['estimated_time'],
            'parallel_execution_possible': True,
            'sequential_dependencies': [],
            'provider_specific_times': {},
            'risk_based_phases': {
                'low_risk_phase': [],
                'medium_risk_phase': [],
                'high_risk_phase': []
            }
        }

        # Provider-specific timing
        for provider, summary in provider_breakdown['provider_risk_summary'].items():
            timeline['provider_specific_times'][provider] = {
                'resource_count': summary['total_resources'],
                'estimated_time': f"{summary['total_resources'] * 0.5}-{summary['total_resources'] * 2} minutes"
            }

        # Risk-based phasing
        if 'detailed_assessments' in full_assessment:
            for assessment in full_assessment['detailed_assessments']:
                phase_key = f"{assessment['level'].lower()}_risk_phase"
                timeline['risk_based_phases'][phase_key].append({
                    'resource': assessment['address'],
                    'type': assessment['type'],
                    'provider': assessment.get('provider', 'unknown')
                })

        return timeline
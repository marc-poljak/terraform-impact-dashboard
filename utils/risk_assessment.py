from typing import Dict, List, Any
from collections import defaultdict


class RiskAssessment:
    """Assess risk levels for Terraform plan changes"""

    def __init__(self):
        # Define risk weights for different resource types
        self.resource_risk_weights = {
            # High risk resources (infrastructure critical)
            'aws_security_group': 8,
            'aws_vpc': 9,
            'aws_subnet': 7,
            'aws_route_table': 7,
            'aws_internet_gateway': 8,
            'aws_nat_gateway': 7,
            'aws_network_acl': 8,

            # Database resources (data critical)
            'aws_rds_instance': 9,
            'aws_rds_cluster': 9,
            'aws_dynamodb_table': 8,
            'aws_elasticsearch_domain': 8,
            'aws_elasticache_cluster': 7,

            # Identity and Access Management (security critical)
            'aws_iam_role': 8,
            'aws_iam_policy': 8,
            'aws_iam_user': 7,
            'aws_iam_group': 6,
            'aws_iam_role_policy_attachment': 7,

            # Storage (data critical)
            'aws_s3_bucket': 7,
            'aws_s3_bucket_policy': 8,
            'aws_ebs_volume': 6,
            'aws_efs_file_system': 7,

            # Compute resources (medium risk)
            'aws_instance': 5,
            'aws_launch_template': 6,
            'aws_autoscaling_group': 6,
            'aws_load_balancer': 6,
            'aws_lb_target_group': 5,

            # DNS and CDN (medium risk)
            'aws_route53_record': 6,
            'aws_route53_zone': 7,
            'aws_cloudfront_distribution': 6,

            # Monitoring and Logging (low-medium risk)
            'aws_cloudwatch_metric_alarm': 4,
            'aws_cloudwatch_log_group': 3,
            'aws_sns_topic': 4,
            'aws_sqs_queue': 4,

            # Lambda and serverless (medium risk)
            'aws_lambda_function': 5,
            'aws_api_gateway_rest_api': 6,
            'aws_api_gateway_deployment': 5,

            # Low risk resources
            'aws_s3_bucket_object': 2,
            'aws_cloudwatch_dashboard': 2,
            'data.aws_*': 1,  # Data sources are generally low risk
        }

        # Action risk multipliers
        self.action_risk_multipliers = {
            'create': 1.0,  # Creating new resources is generally safe
            'update': 1.5,  # Updates can break existing functionality
            'delete': 2.5  # Deletions are highest risk
        }

        # Critical resource patterns that always warrant high attention
        self.critical_patterns = [
            'security_group',
            'iam_',
            'rds_',
            'vpc',
            'subnet'
        ]

    def assess_resource_risk(self, resource_change: Dict[str, Any]) -> Dict[str, Any]:
        """Assess risk for a single resource change"""
        resource_type = resource_change.get('type', '')
        actions = resource_change.get('change', {}).get('actions', [])

        # Get base risk score for resource type
        base_risk = self._get_base_risk_score(resource_type)

        # Apply action multiplier
        action_multiplier = max([self.action_risk_multipliers.get(action, 1.0) for action in actions])

        # Calculate final risk score
        risk_score = min(10, base_risk * action_multiplier)

        # Determine risk level
        if risk_score >= 7:
            risk_level = "High"
        elif risk_score >= 4:
            risk_level = "Medium"
        else:
            risk_level = "Low"

        # Additional risk factors
        risk_factors = self._identify_risk_factors(resource_change)

        return {
            'score': round(risk_score, 1),
            'level': risk_level,
            'base_score': base_risk,
            'action_multiplier': action_multiplier,
            'risk_factors': risk_factors
        }

    def assess_plan_risk(self, resource_changes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Assess overall risk for the entire plan"""
        if not resource_changes:
            return {
                'level': 'Low',
                'score': 0,
                'high_risk_count': 0,
                'medium_risk_count': 0,
                'low_risk_count': 0,
                'estimated_time': '< 5 minutes'
            }

        risk_scores = []
        risk_levels = {'High': 0, 'Medium': 0, 'Low': 0}

        for change in resource_changes:
            risk_assessment = self.assess_resource_risk(change)
            risk_scores.append(risk_assessment['score'])
            risk_levels[risk_assessment['level']] += 1

        # Calculate overall risk score (weighted average with emphasis on high-risk items)
        total_score = sum(risk_scores)
        max_possible_score = len(resource_changes) * 10
        overall_score = (total_score / max_possible_score) * 100 if max_possible_score > 0 else 0

        # Adjust for high-risk resource concentration
        high_risk_ratio = risk_levels['High'] / len(resource_changes)
        if high_risk_ratio > 0.3:  # More than 30% high-risk
            overall_score *= 1.2

        overall_score = min(100, overall_score)

        # Determine overall risk level
        if overall_score >= 70 or risk_levels['High'] > 0:
            overall_level = "High"
        elif overall_score >= 40 or risk_levels['Medium'] > 2:
            overall_level = "Medium"
        else:
            overall_level = "Low"

        # Estimate deployment time based on risk and resource count
        estimated_time = self._estimate_deployment_time(len(resource_changes), overall_level, risk_levels)

        return {
            'level': overall_level,
            'score': round(overall_score),
            'high_risk_count': risk_levels['High'],
            'medium_risk_count': risk_levels['Medium'],
            'low_risk_count': risk_levels['Low'],
            'estimated_time': estimated_time,
            'average_risk_score': round(sum(risk_scores) / len(risk_scores), 1) if risk_scores else 0
        }

    def get_risk_by_resource_type(self, resource_changes: List[Dict[str, Any]]) -> Dict[str, Dict[str, int]]:
        """Get risk level breakdown by resource type"""
        risk_by_type = defaultdict(lambda: {'Low': 0, 'Medium': 0, 'High': 0})

        for change in resource_changes:
            resource_type = change.get('type', 'unknown')
            risk_assessment = self.assess_resource_risk(change)
            risk_level = risk_assessment['level']

            risk_by_type[resource_type][risk_level] += 1

        return dict(risk_by_type)

    def get_high_risk_resources(self, resource_changes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Get list of high-risk resource changes"""
        high_risk_resources = []

        for change in resource_changes:
            risk_assessment = self.assess_resource_risk(change)
            if risk_assessment['level'] == 'High':
                high_risk_resources.append({
                    'address': change.get('address', ''),
                    'type': change.get('type', ''),
                    'action': change.get('action', ''),
                    'risk_score': risk_assessment['score'],
                    'risk_factors': risk_assessment['risk_factors']
                })

        return high_risk_resources

    def _get_base_risk_score(self, resource_type: str) -> float:
        """Get base risk score for a resource type"""
        # Direct match
        if resource_type in self.resource_risk_weights:
            return self.resource_risk_weights[resource_type]

        # Pattern matching for unknown resource types
        for pattern, score in self.resource_risk_weights.items():
            if pattern.endswith('*') and resource_type.startswith(pattern[:-1]):
                return score

        # Check for critical patterns
        for pattern in self.critical_patterns:
            if pattern in resource_type:
                return 7  # Default high risk for critical patterns

        # Default risk for unknown resources
        if resource_type.startswith('aws_'):
            return 3  # Medium-low risk for AWS resources
        elif resource_type.startswith('data.'):
            return 1  # Low risk for data sources
        else:
            return 4  # Medium risk for unknown providers

    def _identify_risk_factors(self, resource_change: Dict[str, Any]) -> List[str]:
        """Identify specific risk factors for a resource change"""
        factors = []

        resource_type = resource_change.get('type', '')
        actions = resource_change.get('change', {}).get('actions', [])
        before = resource_change.get('change', {}).get('before')
        after = resource_change.get('change', {}).get('after')

        # Action-based factors
        if 'delete' in actions:
            factors.append("Resource deletion")

        if 'update' in actions and before and after:
            factors.append("Configuration changes")

        # Resource-type specific factors
        if 'security_group' in resource_type:
            factors.append("Network security impact")

        if 'iam_' in resource_type:
            factors.append("Access control changes")

        if 'rds_' in resource_type or 'dynamodb' in resource_type:
            factors.append("Database modification")

        if 'vpc' in resource_type or 'subnet' in resource_type:
            factors.append("Network infrastructure change")

        # Check for sensitive values
        if self._has_sensitive_changes(resource_change):
            factors.append("Sensitive data involved")

        return factors

    def _has_sensitive_changes(self, resource_change: Dict[str, Any]) -> bool:
        """Check if the resource change involves sensitive data"""
        change_data = resource_change.get('change', {})
        after = change_data.get('after', {})

        if isinstance(after, dict):
            for key, value in after.items():
                if value == "(sensitive)" or key.lower() in ['password', 'secret', 'key', 'token']:
                    return True

        return False

    def _estimate_deployment_time(self, resource_count: int, risk_level: str, risk_breakdown: Dict[str, int]) -> str:
        """Estimate deployment time based on resource count and risk"""
        base_time_per_resource = 30  # seconds per resource

        # Risk multipliers
        risk_multipliers = {
            'Low': 1.0,
            'Medium': 1.5,
            'High': 2.0
        }

        # Calculate weighted time
        total_time = 0
        for level, count in risk_breakdown.items():
            total_time += count * base_time_per_resource * risk_multipliers[level]

        # Convert to human-readable format
        if total_time < 300:  # Less than 5 minutes
            return "< 5 minutes"
        elif total_time < 900:  # Less than 15 minutes
            return "5-15 minutes"
        elif total_time < 1800:  # Less than 30 minutes
            return "15-30 minutes"
        elif total_time < 3600:  # Less than 1 hour
            return "30-60 minutes"
        else:
            hours = total_time // 3600
            return f"{int(hours)}+ hours"

    def generate_recommendations(self, resource_changes: List[Dict[str, Any]]) -> List[str]:
        """Generate deployment recommendations based on risk assessment"""
        recommendations = []

        plan_risk = self.assess_plan_risk(resource_changes)
        high_risk_resources = self.get_high_risk_resources(resource_changes)

        if plan_risk['level'] == 'High':
            recommendations.append("⚠️ HIGH RISK: Review all changes carefully before deployment")
            recommendations.append("🔍 Consider deploying in stages to minimize blast radius")

        if high_risk_resources:
            recommendations.append(f"🎯 {len(high_risk_resources)} high-risk resources require special attention")

        if plan_risk['high_risk_count'] > 5:
            recommendations.append("📊 Large number of high-risk changes - consider breaking into smaller deployments")

        # Check for deletions
        delete_count = sum(1 for change in resource_changes if 'delete' in change.get('change', {}).get('actions', []))
        if delete_count > 0:
            recommendations.append(f"🗑️ {delete_count} resources will be deleted - ensure backups are available")

        if plan_risk['level'] == 'Low':
            recommendations.append("✅ Low risk deployment - safe to proceed")

        return recommendations
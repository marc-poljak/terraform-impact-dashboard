from typing import Dict, List, Any
from .base_provider import BaseCloudProvider, ResourceCategory


class AWSProvider(BaseCloudProvider):
    """AWS-specific provider implementation"""

    def __init__(self):
        super().__init__("aws")

    def _get_resource_mappings(self) -> Dict[str, ResourceCategory]:
        """Map AWS resource types to unified categories"""
        return {
            # Compute
            'aws_instance': ResourceCategory.COMPUTE,
            'aws_launch_template': ResourceCategory.COMPUTE,
            'aws_autoscaling_group': ResourceCategory.COMPUTE,
            'aws_launch_configuration': ResourceCategory.COMPUTE,

            # Networking
            'aws_vpc': ResourceCategory.NETWORKING,
            'aws_subnet': ResourceCategory.NETWORKING,
            'aws_security_group': ResourceCategory.NETWORKING,
            'aws_route_table': ResourceCategory.NETWORKING,
            'aws_internet_gateway': ResourceCategory.NETWORKING,
            'aws_nat_gateway': ResourceCategory.NETWORKING,
            'aws_network_acl': ResourceCategory.NETWORKING,
            'aws_load_balancer': ResourceCategory.NETWORKING,
            'aws_lb': ResourceCategory.NETWORKING,
            'aws_lb_target_group': ResourceCategory.NETWORKING,
            'aws_cloudfront_distribution': ResourceCategory.NETWORKING,

            # Storage
            'aws_s3_bucket': ResourceCategory.STORAGE,
            'aws_s3_bucket_policy': ResourceCategory.STORAGE,
            'aws_ebs_volume': ResourceCategory.STORAGE,
            'aws_efs_file_system': ResourceCategory.STORAGE,
            'aws_fsx_file_system': ResourceCategory.STORAGE,

            # Database
            'aws_rds_instance': ResourceCategory.DATABASE,
            'aws_rds_cluster': ResourceCategory.DATABASE,
            'aws_dynamodb_table': ResourceCategory.DATABASE,
            'aws_elasticache_cluster': ResourceCategory.DATABASE,
            'aws_elasticsearch_domain': ResourceCategory.DATABASE,
            'aws_opensearch_domain': ResourceCategory.DATABASE,

            # Security & Identity
            'aws_iam_role': ResourceCategory.IDENTITY,
            'aws_iam_policy': ResourceCategory.IDENTITY,
            'aws_iam_user': ResourceCategory.IDENTITY,
            'aws_iam_group': ResourceCategory.IDENTITY,
            'aws_iam_role_policy_attachment': ResourceCategory.IDENTITY,
            'aws_kms_key': ResourceCategory.SECURITY,
            'aws_secrets_manager_secret': ResourceCategory.SECURITY,

            # Serverless
            'aws_lambda_function': ResourceCategory.SERVERLESS,
            'aws_api_gateway_rest_api': ResourceCategory.SERVERLESS,
            'aws_api_gateway_deployment': ResourceCategory.SERVERLESS,
            'aws_api_gateway_v2_api': ResourceCategory.SERVERLESS,

            # Container
            'aws_ecs_cluster': ResourceCategory.CONTAINER,
            'aws_ecs_service': ResourceCategory.CONTAINER,
            'aws_eks_cluster': ResourceCategory.CONTAINER,
            'aws_eks_node_group': ResourceCategory.CONTAINER,

            # Monitoring
            'aws_cloudwatch_metric_alarm': ResourceCategory.MONITORING,
            'aws_cloudwatch_log_group': ResourceCategory.MONITORING,
            'aws_cloudwatch_dashboard': ResourceCategory.MONITORING,
            'aws_sns_topic': ResourceCategory.MONITORING,
            'aws_sqs_queue': ResourceCategory.MONITORING,

            # Analytics
            'aws_kinesis_stream': ResourceCategory.ANALYTICS,
            'aws_kinesis_firehose_delivery_stream': ResourceCategory.ANALYTICS,
            'aws_glue_job': ResourceCategory.ANALYTICS,
            'aws_redshift_cluster': ResourceCategory.ANALYTICS,
        }

    def _get_risk_weights(self) -> Dict[str, float]:
        """Get AWS-specific risk weights"""
        return {
            # High risk resources (infrastructure critical)
            'aws_security_group': 8.0,
            'aws_vpc': 9.0,
            'aws_subnet': 7.0,
            'aws_route_table': 7.0,
            'aws_internet_gateway': 8.0,
            'aws_nat_gateway': 7.0,
            'aws_network_acl': 8.0,

            # Database resources (data critical)
            'aws_rds_instance': 9.0,
            'aws_rds_cluster': 9.0,
            'aws_dynamodb_table': 8.0,
            'aws_elasticsearch_domain': 8.0,
            'aws_opensearch_domain': 8.0,
            'aws_elasticache_cluster': 7.0,

            # Identity and Access Management (security critical)
            'aws_iam_role': 8.0,
            'aws_iam_policy': 8.0,
            'aws_iam_user': 7.0,
            'aws_iam_group': 6.0,
            'aws_iam_role_policy_attachment': 7.0,
            'aws_kms_key': 9.0,

            # Storage (data critical)
            'aws_s3_bucket': 7.0,
            'aws_s3_bucket_policy': 8.0,
            'aws_ebs_volume': 6.0,
            'aws_efs_file_system': 7.0,

            # Compute resources (medium risk)
            'aws_instance': 5.0,
            'aws_launch_template': 6.0,
            'aws_autoscaling_group': 6.0,
            'aws_load_balancer': 6.0,
            'aws_lb_target_group': 5.0,

            # DNS and CDN (medium risk)
            'aws_route53_record': 6.0,
            'aws_route53_zone': 7.0,
            'aws_cloudfront_distribution': 6.0,

            # Monitoring and Logging (low-medium risk)
            'aws_cloudwatch_metric_alarm': 4.0,
            'aws_cloudwatch_log_group': 3.0,
            'aws_sns_topic': 4.0,
            'aws_sqs_queue': 4.0,

            # Lambda and serverless (medium risk)
            'aws_lambda_function': 5.0,
            'aws_api_gateway_rest_api': 6.0,
            'aws_api_gateway_deployment': 5.0,

            # Container services
            'aws_ecs_cluster': 6.0,
            'aws_ecs_service': 5.0,
            'aws_eks_cluster': 8.0,
            'aws_eks_node_group': 6.0,

            # Low risk resources
            'aws_s3_bucket_object': 2.0,
            'aws_cloudwatch_dashboard': 2.0,
        }

    def _get_critical_patterns(self) -> List[str]:
        """Get AWS-specific critical resource patterns"""
        return [
            'security_group',
            'iam_',
            'rds_',
            'vpc',
            'subnet',
            'kms_',
            'eks_cluster'
        ]

    def get_action_multipliers(self) -> Dict[str, float]:
        """Get AWS-specific action risk multipliers"""
        return {
            'create': 1.0,
            'update': 1.5,
            'delete': 2.5,
            'replace': 2.0  # AWS replacement operations
        }

    def get_provider_specific_recommendations(self, resource_changes: List[Dict[str, Any]]) -> List[str]:
        """Generate AWS-specific recommendations"""
        recommendations = []

        # Check for specific AWS patterns
        security_group_changes = [r for r in resource_changes if 'security_group' in r.get('type', '')]
        iam_changes = [r for r in resource_changes if 'iam_' in r.get('type', '')]
        vpc_changes = [r for r in resource_changes if r.get('type', '') in ['aws_vpc', 'aws_subnet']]
        rds_changes = [r for r in resource_changes if 'rds_' in r.get('type', '')]

        if security_group_changes:
            recommendations.append("🛡️ AWS Security Groups detected - review ingress/egress rules carefully")
            if any(r.get('action') == 'delete' for r in security_group_changes):
                recommendations.append("⚠️ Deleting Security Groups may break EC2 instance connectivity")

        if iam_changes:
            recommendations.append("🔐 IAM changes detected - verify permissions and access policies")
            recommendations.append("📋 Consider using AWS IAM Access Analyzer to validate policies")

        if vpc_changes:
            recommendations.append("🌐 VPC/Subnet changes detected - may affect network routing")
            recommendations.append("🔍 Check for dependent resources (EC2, RDS, Lambda) in affected subnets")

        if rds_changes:
            recommendations.append("💾 RDS changes detected - ensure database backups are current")
            delete_rds = [r for r in rds_changes if r.get('action') == 'delete']
            if delete_rds:
                recommendations.append("🚨 RDS deletion detected - verify final snapshot configuration")

        # Check for EKS cluster changes
        eks_changes = [r for r in resource_changes if 'eks_' in r.get('type', '')]
        if eks_changes:
            recommendations.append("⚓ EKS changes detected - may affect running workloads")
            recommendations.append("📊 Consider draining nodes before making changes")

        return recommendations

    def get_aws_specific_insights(self, resource_changes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get AWS-specific insights for the plan"""
        insights = {
            'multi_az_resources': [],
            'cross_region_resources': [],
            'compliance_considerations': [],
            'cost_implications': []
        }

        # Detect multi-AZ deployments
        for change in resource_changes:
            resource_type = change.get('type', '')
            if resource_type in ['aws_rds_instance', 'aws_rds_cluster']:
                insights['multi_az_resources'].append(change.get('address', ''))

        # Detect potential compliance issues
        for change in resource_changes:
            if 'kms' in change.get('type', '') and change.get('action') == 'delete':
                insights['compliance_considerations'].append(
                    f"KMS key deletion: {change.get('address', '')}"
                )

        return insights
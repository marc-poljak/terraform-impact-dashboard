from typing import Dict, List, Any
from .base_provider import BaseCloudProvider, ResourceCategory


class GCPProvider(BaseCloudProvider):
    """Google Cloud Platform provider implementation"""

    def __init__(self):
        super().__init__("google")

    def _get_resource_mappings(self) -> Dict[str, ResourceCategory]:
        """Map GCP resource types to unified categories"""
        return {
            # Compute
            'google_compute_instance': ResourceCategory.COMPUTE,
            'google_compute_instance_template': ResourceCategory.COMPUTE,
            'google_compute_instance_group': ResourceCategory.COMPUTE,
            'google_compute_instance_group_manager': ResourceCategory.COMPUTE,
            'google_compute_autoscaler': ResourceCategory.COMPUTE,

            # Networking
            'google_compute_network': ResourceCategory.NETWORKING,
            'google_compute_subnetwork': ResourceCategory.NETWORKING,
            'google_compute_firewall': ResourceCategory.NETWORKING,
            'google_compute_route': ResourceCategory.NETWORKING,
            'google_compute_router': ResourceCategory.NETWORKING,
            'google_compute_vpn_gateway': ResourceCategory.NETWORKING,
            'google_compute_forwarding_rule': ResourceCategory.NETWORKING,
            'google_compute_global_forwarding_rule': ResourceCategory.NETWORKING,
            'google_compute_backend_service': ResourceCategory.NETWORKING,
            'google_compute_url_map': ResourceCategory.NETWORKING,
            'google_compute_target_http_proxy': ResourceCategory.NETWORKING,
            'google_compute_target_https_proxy': ResourceCategory.NETWORKING,
            'google_compute_ssl_certificate': ResourceCategory.SECURITY,

            # Storage
            'google_storage_bucket': ResourceCategory.STORAGE,
            'google_storage_bucket_object': ResourceCategory.STORAGE,
            'google_compute_disk': ResourceCategory.STORAGE,
            'google_filestore_instance': ResourceCategory.STORAGE,

            # Database
            'google_sql_database_instance': ResourceCategory.DATABASE,
            'google_sql_database': ResourceCategory.DATABASE,
            'google_sql_user': ResourceCategory.DATABASE,
            'google_bigtable_instance': ResourceCategory.DATABASE,
            'google_firestore_database': ResourceCategory.DATABASE,
            'google_spanner_instance': ResourceCategory.DATABASE,
            'google_spanner_database': ResourceCategory.DATABASE,
            'google_redis_instance': ResourceCategory.DATABASE,

            # Security & Identity
            'google_project_iam_member': ResourceCategory.IDENTITY,
            'google_project_iam_binding': ResourceCategory.IDENTITY,
            'google_project_iam_policy': ResourceCategory.IDENTITY,
            'google_service_account': ResourceCategory.IDENTITY,
            'google_service_account_key': ResourceCategory.SECURITY,
            'google_kms_key_ring': ResourceCategory.SECURITY,
            'google_kms_crypto_key': ResourceCategory.SECURITY,
            'google_secret_manager_secret': ResourceCategory.SECURITY,

            # Serverless
            'google_cloudfunctions_function': ResourceCategory.SERVERLESS,
            'google_cloud_run_service': ResourceCategory.SERVERLESS,
            'google_app_engine_application': ResourceCategory.SERVERLESS,
            'google_app_engine_version': ResourceCategory.SERVERLESS,

            # Container
            'google_container_cluster': ResourceCategory.CONTAINER,
            'google_container_node_pool': ResourceCategory.CONTAINER,
            'google_artifact_registry_repository': ResourceCategory.CONTAINER,
            'google_container_registry': ResourceCategory.CONTAINER,

            # Monitoring
            'google_monitoring_alert_policy': ResourceCategory.MONITORING,
            'google_monitoring_notification_channel': ResourceCategory.MONITORING,
            'google_logging_metric': ResourceCategory.MONITORING,
            'google_logging_sink': ResourceCategory.MONITORING,

            # Analytics
            'google_bigquery_dataset': ResourceCategory.ANALYTICS,
            'google_bigquery_table': ResourceCategory.ANALYTICS,
            'google_dataflow_job': ResourceCategory.ANALYTICS,
            'google_pubsub_topic': ResourceCategory.ANALYTICS,
            'google_pubsub_subscription': ResourceCategory.ANALYTICS,
            'google_dataproc_cluster': ResourceCategory.ANALYTICS,
        }

    def _get_risk_weights(self) -> Dict[str, float]:
        """Get GCP-specific risk weights"""
        return {
            # High risk networking resources
            'google_compute_network': 9.0,
            'google_compute_subnetwork': 7.0,
            'google_compute_firewall': 8.0,
            'google_compute_route': 7.0,
            'google_compute_router': 7.0,
            'google_compute_vpn_gateway': 8.0,

            # Database resources (data critical)
            'google_sql_database_instance': 9.0,
            'google_sql_database': 8.0,
            'google_bigtable_instance': 8.0,
            'google_firestore_database': 8.0,
            'google_spanner_instance': 9.0,
            'google_spanner_database': 9.0,
            'google_redis_instance': 7.0,

            # Identity and Security (critical)
            'google_project_iam_member': 8.0,
            'google_project_iam_binding': 8.0,
            'google_project_iam_policy': 9.0,
            'google_service_account': 7.0,
            'google_service_account_key': 8.0,
            'google_kms_key_ring': 9.0,
            'google_kms_crypto_key': 9.0,
            'google_secret_manager_secret': 8.0,

            # Storage (data critical)
            'google_storage_bucket': 7.0,
            'google_compute_disk': 6.0,
            'google_filestore_instance': 7.0,

            # Compute resources (medium risk)
            'google_compute_instance': 5.0,
            'google_compute_instance_template': 6.0,
            'google_compute_instance_group': 6.0,
            'google_compute_instance_group_manager': 6.0,
            'google_compute_autoscaler': 6.0,

            # Load balancing (medium-high risk)
            'google_compute_backend_service': 6.0,
            'google_compute_url_map': 6.0,
            'google_compute_forwarding_rule': 6.0,
            'google_compute_global_forwarding_rule': 7.0,

            # Container services
            'google_container_cluster': 8.0,
            'google_container_node_pool': 6.0,
            'google_artifact_registry_repository': 5.0,

            # Serverless (medium risk)
            'google_cloudfunctions_function': 5.0,
            'google_cloud_run_service': 5.0,
            'google_app_engine_application': 6.0,
            'google_app_engine_version': 5.0,

            # Monitoring (low-medium risk)
            'google_monitoring_alert_policy': 4.0,
            'google_logging_metric': 4.0,
            'google_logging_sink': 5.0,

            # Analytics (medium risk)
            'google_bigquery_dataset': 6.0,
            'google_bigquery_table': 5.0,
            'google_dataflow_job': 5.0,
            'google_pubsub_topic': 5.0,
            'google_dataproc_cluster': 6.0,

            # Low risk resources
            'google_storage_bucket_object': 2.0,
            'google_monitoring_notification_channel': 3.0,
            'google_pubsub_subscription': 3.0,
        }

    def _get_critical_patterns(self) -> List[str]:
        """Get GCP-specific critical resource patterns"""
        return [
            'compute_firewall',
            'iam_',
            'kms_',
            'sql_',
            'spanner_',
            'compute_network',
            'container_cluster',
            'service_account'
        ]

    def get_action_multipliers(self) -> Dict[str, float]:
        """Get GCP-specific action risk multipliers"""
        return {
            'create': 1.0,
            'update': 1.3,  # GCP updates are often less disruptive
            'delete': 2.5,
            'replace': 1.8  # GCP replacements can be more efficient
        }

    def get_provider_specific_recommendations(self, resource_changes: List[Dict[str, Any]]) -> List[str]:
        """Generate GCP-specific recommendations"""
        recommendations = []

        # Check for specific GCP patterns
        firewall_changes = [r for r in resource_changes if 'compute_firewall' in r.get('type', '')]
        iam_changes = [r for r in resource_changes if 'iam_' in r.get('type', '')]
        network_changes = [r for r in resource_changes if
                           r.get('type', '') in ['google_compute_network', 'google_compute_subnetwork']]
        sql_changes = [r for r in resource_changes if 'sql_' in r.get('type', '')]
        kms_changes = [r for r in resource_changes if 'kms_' in r.get('type', '')]

        if firewall_changes:
            recommendations.append("🛡️ Compute Firewall changes detected - review ingress/egress rules")
            recommendations.append("🔍 Consider using VPC Flow Logs to analyze traffic patterns")

        if iam_changes:
            recommendations.append("🔐 IAM changes detected - verify role bindings and permissions")
            recommendations.append("📋 Use Cloud Asset Inventory to track permission changes")
            recommendations.append("🔒 Consider using IAM Conditions for fine-grained access control")

        if network_changes:
            recommendations.append("🌐 VPC Network changes detected - may affect connectivity")
            recommendations.append("🔗 Check for VPC peering and shared VPC configurations")

        if sql_changes:
            recommendations.append("💾 Cloud SQL changes detected - ensure automated backups are enabled")
            recommendations.append("🔒 Verify SSL/TLS encryption settings for database connections")

        if kms_changes:
            recommendations.append("🔑 Cloud KMS changes detected - critical for data encryption")
            recommendations.append("🚨 Ensure proper key rotation policies are in place")

        # Check for GKE cluster changes
        gke_changes = [r for r in resource_changes if 'container_cluster' in r.get('type', '')]
        if gke_changes:
            recommendations.append("⚓ GKE changes detected - may affect running workloads")
            recommendations.append("📊 Consider using GKE maintenance windows for updates")
            recommendations.append("🔒 Verify Workload Identity is properly configured")

        # Check for BigQuery changes
        bq_changes = [r for r in resource_changes if 'bigquery_' in r.get('type', '')]
        if bq_changes:
            recommendations.append("📊 BigQuery changes detected - verify data governance policies")
            recommendations.append("💰 Check for cost implications of schema or partition changes")

        # Check for service account changes
        sa_changes = [r for r in resource_changes if 'service_account' in r.get('type', '')]
        if sa_changes:
            recommendations.append("🤖 Service Account changes detected - review application authentication")
            recommendations.append("🔑 Avoid using service account keys when possible - prefer Workload Identity")

        return recommendations

    def get_gcp_specific_insights(self, resource_changes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get GCP-specific insights for the plan"""
        insights = {
            'projects': set(),
            'regions': set(),
            'zones': set(),
            'security_features': [],
            'cost_optimization': [],
            'compliance_considerations': []
        }

        # Extract project, region, and zone info from resource addresses
        for change in resource_changes:
            address = change.get('address', '')
            # GCP resource addresses often contain project/region/zone info
            if 'project' in address.lower():
                insights['projects'].add(address)

        # Detect security-related resources
        for change in resource_changes:
            resource_type = change.get('type', '')
            if resource_type in ['google_kms_crypto_key', 'google_secret_manager_secret',
                                 'google_compute_ssl_certificate']:
                insights['security_features'].append(change.get('address', ''))

        # Cost optimization suggestions
        compute_changes = [r for r in resource_changes if 'compute_instance' in r.get('type', '')]
        if compute_changes:
            insights['cost_optimization'].extend([
                "Consider using Committed Use Discounts for long-running instances",
                "Evaluate Preemptible VMs for fault-tolerant workloads"
            ])

        # Compliance considerations
        logging_changes = [r for r in resource_changes if 'logging_' in r.get('type', '')]
        if logging_changes:
            insights['compliance_considerations'].append(
                "Logging configuration changes detected - ensure audit trail compliance"
            )

        return insights

    def get_deployment_time_multiplier(self) -> float:
        """GCP deployments are generally fast and efficient"""
        return 0.9  # 10% faster deployment times on average due to efficient APIs

    def get_gcp_best_practices(self, resource_changes: List[Dict[str, Any]]) -> List[str]:
        """Get GCP-specific best practices recommendations"""
        best_practices = []

        # Check for organization-level best practices
        project_iam_changes = [r for r in resource_changes if 'project_iam' in r.get('type', '')]
        if project_iam_changes:
            best_practices.extend([
                "Use Google Groups for role assignments instead of individual users",
                "Implement least privilege principle with custom roles",
                "Enable Cloud Audit Logs for all IAM changes"
            ])

        # Network security best practices
        firewall_changes = [r for r in resource_changes if 'compute_firewall' in r.get('type', '')]
        if firewall_changes:
            best_practices.extend([
                "Use network tags for firewall rule targeting",
                "Implement defense in depth with multiple security layers",
                "Regular review and cleanup of unused firewall rules"
            ])

        # Data protection best practices
        storage_changes = [r for r in resource_changes if 'storage_bucket' in r.get('type', '')]
        if storage_changes:
            best_practices.extend([
                "Enable uniform bucket-level access for better security",
                "Use Customer-Managed Encryption Keys (CMEK) for sensitive data",
                "Implement lifecycle policies for cost optimization"
            ])

        return best_practices
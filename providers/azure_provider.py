from typing import Dict, List, Any
from .base_provider import BaseCloudProvider, ResourceCategory


class AzureProvider(BaseCloudProvider):
    """Azure-specific provider implementation"""

    def __init__(self):
        super().__init__("azure")

    def _get_resource_mappings(self) -> Dict[str, ResourceCategory]:
        """Map Azure resource types to unified categories"""
        return {
            # Compute
            'azurerm_virtual_machine': ResourceCategory.COMPUTE,
            'azurerm_linux_virtual_machine': ResourceCategory.COMPUTE,
            'azurerm_windows_virtual_machine': ResourceCategory.COMPUTE,
            'azurerm_virtual_machine_scale_set': ResourceCategory.COMPUTE,
            'azurerm_availability_set': ResourceCategory.COMPUTE,

            # Networking
            'azurerm_virtual_network': ResourceCategory.NETWORKING,
            'azurerm_subnet': ResourceCategory.NETWORKING,
            'azurerm_network_security_group': ResourceCategory.NETWORKING,
            'azurerm_network_security_rule': ResourceCategory.NETWORKING,
            'azurerm_route_table': ResourceCategory.NETWORKING,
            'azurerm_route': ResourceCategory.NETWORKING,
            'azurerm_virtual_network_gateway': ResourceCategory.NETWORKING,
            'azurerm_network_interface': ResourceCategory.NETWORKING,
            'azurerm_public_ip': ResourceCategory.NETWORKING,
            'azurerm_load_balancer': ResourceCategory.NETWORKING,
            'azurerm_application_gateway': ResourceCategory.NETWORKING,
            'azurerm_firewall': ResourceCategory.NETWORKING,

            # Storage
            'azurerm_storage_account': ResourceCategory.STORAGE,
            'azurerm_storage_container': ResourceCategory.STORAGE,
            'azurerm_storage_blob': ResourceCategory.STORAGE,
            'azurerm_managed_disk': ResourceCategory.STORAGE,

            # Database
            'azurerm_sql_server': ResourceCategory.DATABASE,
            'azurerm_sql_database': ResourceCategory.DATABASE,
            'azurerm_mysql_server': ResourceCategory.DATABASE,
            'azurerm_postgresql_server': ResourceCategory.DATABASE,
            'azurerm_cosmosdb_account': ResourceCategory.DATABASE,
            'azurerm_redis_cache': ResourceCategory.DATABASE,

            # Security & Identity
            'azurerm_role_assignment': ResourceCategory.IDENTITY,
            'azurerm_role_definition': ResourceCategory.IDENTITY,
            'azurerm_user_assigned_identity': ResourceCategory.IDENTITY,
            'azurerm_key_vault': ResourceCategory.SECURITY,
            'azurerm_key_vault_key': ResourceCategory.SECURITY,
            'azurerm_key_vault_secret': ResourceCategory.SECURITY,

            # Serverless
            'azurerm_function_app': ResourceCategory.SERVERLESS,
            'azurerm_app_service': ResourceCategory.SERVERLESS,
            'azurerm_app_service_plan': ResourceCategory.SERVERLESS,
            'azurerm_logic_app_workflow': ResourceCategory.SERVERLESS,

            # Container
            'azurerm_kubernetes_cluster': ResourceCategory.CONTAINER,
            'azurerm_kubernetes_cluster_node_pool': ResourceCategory.CONTAINER,
            'azurerm_container_group': ResourceCategory.CONTAINER,
            'azurerm_container_registry': ResourceCategory.CONTAINER,

            # Monitoring
            'azurerm_monitor_metric_alert': ResourceCategory.MONITORING,
            'azurerm_log_analytics_workspace': ResourceCategory.MONITORING,
            'azurerm_application_insights': ResourceCategory.MONITORING,
            'azurerm_monitor_action_group': ResourceCategory.MONITORING,

            # Analytics
            'azurerm_data_factory': ResourceCategory.ANALYTICS,
            'azurerm_synapse_workspace': ResourceCategory.ANALYTICS,
            'azurerm_stream_analytics_job': ResourceCategory.ANALYTICS,
            'azurerm_eventhub': ResourceCategory.ANALYTICS,
        }

    def _get_risk_weights(self) -> Dict[str, float]:
        """Get Azure-specific risk weights"""
        return {
            # High risk networking resources
            'azurerm_virtual_network': 9.0,
            'azurerm_subnet': 7.0,
            'azurerm_network_security_group': 8.0,
            'azurerm_network_security_rule': 8.0,
            'azurerm_route_table': 7.0,
            'azurerm_firewall': 9.0,
            'azurerm_virtual_network_gateway': 8.0,

            # Database resources (data critical)
            'azurerm_sql_server': 9.0,
            'azurerm_sql_database': 8.0,
            'azurerm_mysql_server': 8.0,
            'azurerm_postgresql_server': 8.0,
            'azurerm_cosmosdb_account': 9.0,
            'azurerm_redis_cache': 7.0,

            # Identity and Security (critical)
            'azurerm_role_assignment': 8.0,
            'azurerm_role_definition': 9.0,
            'azurerm_key_vault': 9.0,
            'azurerm_key_vault_key': 8.0,
            'azurerm_key_vault_secret': 8.0,
            'azurerm_user_assigned_identity': 7.0,

            # Storage (data critical)
            'azurerm_storage_account': 7.0,
            'azurerm_storage_container': 6.0,
            'azurerm_managed_disk': 6.0,

            # Compute resources (medium risk)
            'azurerm_virtual_machine': 5.0,
            'azurerm_linux_virtual_machine': 5.0,
            'azurerm_windows_virtual_machine': 5.0,
            'azurerm_virtual_machine_scale_set': 6.0,
            'azurerm_availability_set': 5.0,

            # Load balancing (medium-high risk)
            'azurerm_load_balancer': 6.0,
            'azurerm_application_gateway': 7.0,

            # Container services
            'azurerm_kubernetes_cluster': 8.0,
            'azurerm_kubernetes_cluster_node_pool': 6.0,
            'azurerm_container_registry': 6.0,
            'azurerm_container_group': 5.0,

            # Serverless (medium risk)
            'azurerm_function_app': 5.0,
            'azurerm_app_service': 5.0,
            'azurerm_app_service_plan': 6.0,
            'azurerm_logic_app_workflow': 5.0,

            # Monitoring (low-medium risk)
            'azurerm_monitor_metric_alert': 4.0,
            'azurerm_log_analytics_workspace': 5.0,
            'azurerm_application_insights': 4.0,
            'azurerm_monitor_action_group': 4.0,

            # Analytics (medium risk)
            'azurerm_data_factory': 6.0,
            'azurerm_synapse_workspace': 7.0,
            'azurerm_stream_analytics_job': 5.0,

            # Low risk resources
            'azurerm_storage_blob': 2.0,
            'azurerm_public_ip': 3.0,
            'azurerm_network_interface': 3.0,
        }

    def _get_critical_patterns(self) -> List[str]:
        """Get Azure-specific critical resource patterns"""
        return [
            'network_security',
            'role_',
            'key_vault',
            'sql_',
            'cosmosdb',
            'virtual_network',
            'firewall',
            'kubernetes_cluster'
        ]

    def get_action_multipliers(self) -> Dict[str, float]:
        """Get Azure-specific action risk multipliers"""
        return {
            'create': 1.0,
            'update': 1.4,  # Azure updates often require fewer restarts
            'delete': 2.5,
            'replace': 2.2  # Azure replacements sometimes less disruptive
        }

    def get_provider_specific_recommendations(self, resource_changes: List[Dict[str, Any]]) -> List[str]:
        """Generate Azure-specific recommendations"""
        recommendations = []

        # Check for specific Azure patterns
        nsg_changes = [r for r in resource_changes if 'network_security' in r.get('type', '')]
        rbac_changes = [r for r in resource_changes if 'role_' in r.get('type', '')]
        vnet_changes = [r for r in resource_changes if
                        r.get('type', '') in ['azurerm_virtual_network', 'azurerm_subnet']]
        sql_changes = [r for r in resource_changes if 'sql_' in r.get('type', '')]
        keyvault_changes = [r for r in resource_changes if 'key_vault' in r.get('type', '')]

        if nsg_changes:
            recommendations.append("🛡️ Network Security Group changes detected - review security rules")
            recommendations.append("🔍 Consider using Azure Security Center recommendations")

        if rbac_changes:
            recommendations.append("🔐 RBAC changes detected - verify role assignments and permissions")
            recommendations.append("📋 Use Azure AD Privileged Identity Management for sensitive roles")

        if vnet_changes:
            recommendations.append("🌐 Virtual Network changes detected - may affect connectivity")
            recommendations.append("🔗 Check for peering relationships and dependent resources")

        if sql_changes:
            recommendations.append("💾 Azure SQL changes detected - ensure backups are configured")
            recommendations.append("🔒 Verify Transparent Data Encryption (TDE) settings")

        if keyvault_changes:
            recommendations.append("🔑 Key Vault changes detected - critical for application security")
            recommendations.append("🚨 Ensure proper access policies and audit logging")

        # Check for AKS cluster changes
        aks_changes = [r for r in resource_changes if 'kubernetes_cluster' in r.get('type', '')]
        if aks_changes:
            recommendations.append("⚓ AKS changes detected - may affect running workloads")
            recommendations.append("📊 Consider using Blue-Green deployment strategies")

        # Check for storage account changes
        storage_changes = [r for r in resource_changes if 'storage_account' in r.get('type', '')]
        if storage_changes:
            recommendations.append("💿 Storage Account changes detected - verify data replication settings")

        return recommendations

    def get_azure_specific_insights(self, resource_changes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get Azure-specific insights for the plan"""
        insights = {
            'resource_groups': set(),
            'regions': set(),
            'availability_zones': [],
            'compliance_features': [],
            'cost_optimization': []
        }

        # Extract resource groups and regions from resource addresses
        for change in resource_changes:
            address = change.get('address', '')
            # Azure resource addresses often contain resource group info
            if 'resource_group' in address.lower():
                insights['resource_groups'].add(address)

        # Detect compliance-related resources
        for change in resource_changes:
            resource_type = change.get('type', '')
            if resource_type in ['azurerm_key_vault', 'azurerm_log_analytics_workspace']:
                insights['compliance_features'].append(change.get('address', ''))

        # Cost optimization suggestions
        vm_changes = [r for r in resource_changes if 'virtual_machine' in r.get('type', '')]
        if vm_changes:
            insights['cost_optimization'].append(
                "Consider using Azure Reserved Instances for long-running VMs"
            )

        return insights

    def get_deployment_time_multiplier(self) -> float:
        """Azure deployments can be slower than AWS in some cases"""
        return 1.2  # 20% longer deployment times on average
"""
Risk profiles for different cloud providers and deployment scenarios
"""

from typing import Dict, Any, Optional

# Default risk profiles for different cloud providers
RISK_PROFILES = {
    'aws': {
        'name': 'AWS Enterprise',
        'description': 'Risk profile optimized for AWS enterprise deployments',
        'base_risk_multiplier': 1.0,
        'action_multipliers': {
            'create': 1.0,
            'update': 1.5,
            'delete': 2.5,
            'replace': 2.0
        },
        'deployment_time_multiplier': 1.0,
        'critical_resource_types': [
            'aws_security_group',
            'aws_iam_role',
            'aws_iam_policy',
            'aws_vpc',
            'aws_rds_instance',
            'aws_kms_key'
        ],
        'compliance_requirements': [
            'SOC2',
            'HIPAA',
            'PCI-DSS'
        ]
    },

    'azure': {
        'name': 'Azure Enterprise',
        'description': 'Risk profile optimized for Azure enterprise deployments',
        'base_risk_multiplier': 1.0,
        'action_multipliers': {
            'create': 1.0,
            'update': 1.4,  # Azure updates often less disruptive
            'delete': 2.5,
            'replace': 2.2
        },
        'deployment_time_multiplier': 1.2,  # Azure can be slower
        'critical_resource_types': [
            'azurerm_network_security_group',
            'azurerm_role_assignment',
            'azurerm_key_vault',
            'azurerm_virtual_network',
            'azurerm_sql_server',
            'azurerm_kubernetes_cluster'
        ],
        'compliance_requirements': [
            'SOC2',
            'ISO27001',
            'GDPR'
        ]
    },

    'google': {
        'name': 'Google Cloud Enterprise',
        'description': 'Risk profile optimized for GCP enterprise deployments',
        'base_risk_multiplier': 1.0,
        'action_multipliers': {
            'create': 1.0,
            'update': 1.3,  # GCP updates generally efficient
            'delete': 2.5,
            'replace': 1.8  # GCP replacements often optimized
        },
        'deployment_time_multiplier': 0.9,  # GCP APIs are fast
        'critical_resource_types': [
            'google_compute_firewall',
            'google_project_iam_policy',
            'google_kms_crypto_key',
            'google_compute_network',
            'google_sql_database_instance',
            'google_container_cluster'
        ],
        'compliance_requirements': [
            'SOC2',
            'ISO27001',
            'FedRAMP'
        ]
    },

    'startup': {
        'name': 'Startup/Development',
        'description': 'Risk profile for startups and development environments',
        'base_risk_multiplier': 0.8,  # Lower risk tolerance
        'action_multipliers': {
            'create': 1.0,
            'update': 1.2,  # More aggressive updates acceptable
            'delete': 2.0,  # Still careful with deletions
            'replace': 1.5
        },
        'deployment_time_multiplier': 0.8,  # Faster deployments acceptable
        'critical_resource_types': [
            # Fewer critical resources for startups
            'security_group',
            'iam_',
            'database'
        ],
        'compliance_requirements': []
    },

    'conservative': {
        'name': 'Conservative/Financial',
        'description': 'High-security risk profile for financial institutions',
        'base_risk_multiplier': 1.3,  # Higher baseline risk
        'action_multipliers': {
            'create': 1.2,
            'update': 2.0,  # Very careful with updates
            'delete': 3.0,  # Extremely careful with deletions
            'replace': 2.5
        },
        'deployment_time_multiplier': 1.5,  # Slower, more careful deployments
        'critical_resource_types': [
            # More resources considered critical
            'security',
            'iam',
            'network',
            'database',
            'storage',
            'encryption'
        ],
        'compliance_requirements': [
            'SOX',
            'PCI-DSS',
            'SOC2',
            'NIST'
        ]
    }
}


def get_risk_profile(profile_name: str) -> Optional[Dict[str, Any]]:
    """Get a risk profile by name"""
    return RISK_PROFILES.get(profile_name.lower())


def get_provider_risk_profile(provider: str, environment: str = 'enterprise') -> Dict[str, Any]:
    """Get risk profile for a specific provider and environment"""

    # Try provider-specific profile first
    if provider.lower() in RISK_PROFILES:
        return RISK_PROFILES[provider.lower()]

    # Fall back to environment-based profile
    env_profiles = {
        'startup': 'startup',
        'dev': 'startup',
        'development': 'startup',
        'staging': 'startup',
        'prod': 'conservative',
        'production': 'conservative',
        'enterprise': 'conservative',
        'financial': 'conservative'
    }

    profile_name = env_profiles.get(environment.lower(), 'conservative')
    return RISK_PROFILES[profile_name]


def create_custom_risk_profile(name: str, base_profile: str, overrides: Dict[str, Any]) -> Dict[str, Any]:
    """Create a custom risk profile based on an existing one"""
    if base_profile not in RISK_PROFILES:
        raise ValueError(f"Base profile '{base_profile}' not found")

    # Deep copy base profile
    import copy
    custom_profile = copy.deepcopy(RISK_PROFILES[base_profile])

    # Apply overrides
    for key, value in overrides.items():
        if key in custom_profile:
            if isinstance(custom_profile[key], dict) and isinstance(value, dict):
                custom_profile[key].update(value)
            else:
                custom_profile[key] = value
        else:
            custom_profile[key] = value

    custom_profile['name'] = name
    return custom_profile
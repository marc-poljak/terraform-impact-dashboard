"""
Provider-specific settings and configuration
"""

import os
from typing import Dict, Any, Optional

# Default provider settings
PROVIDER_SETTINGS = {
    'aws': {
        'display_name': 'Amazon Web Services',
        'color_primary': '#FF9900',
        'color_secondary': '#232F3E',
        'deployment_time_multiplier': 1.0,
        'enable_cost_optimization_hints': True,
        'enable_security_best_practices': True,
        'enable_compliance_warnings': True,
        'default_regions': ['us-east-1', 'us-west-2', 'eu-west-1'],
        'documentation_base_url': 'https://docs.aws.amazon.com/',
        'pricing_calculator_url': 'https://calculator.aws/',
        'well_architected_framework': True,
        'support_levels': ['Basic', 'Developer', 'Business', 'Enterprise'],
        'features': {
            'auto_scaling': True,
            'serverless': True,
            'managed_databases': True,
            'machine_learning': True,
            'iot': True
        }
    },

    'azure': {
        'display_name': 'Microsoft Azure',
        'color_primary': '#0078D4',
        'color_secondary': '#FFFFFF',
        'deployment_time_multiplier': 1.2,
        'enable_cost_optimization_hints': True,
        'enable_security_best_practices': True,
        'enable_compliance_warnings': True,
        'default_regions': ['East US', 'West Europe', 'Southeast Asia'],
        'documentation_base_url': 'https://docs.microsoft.com/azure/',
        'pricing_calculator_url': 'https://azure.microsoft.com/pricing/calculator/',
        'well_architected_framework': True,
        'support_levels': ['Basic', 'Standard', 'Professional Direct', 'Premier'],
        'features': {
            'auto_scaling': True,
            'serverless': True,
            'managed_databases': True,
            'machine_learning': True,
            'iot': True,
            'hybrid_cloud': True
        }
    },

    'google': {
        'display_name': 'Google Cloud Platform',
        'color_primary': '#4285F4',
        'color_secondary': '#34A853',
        'deployment_time_multiplier': 0.9,
        'enable_cost_optimization_hints': True,
        'enable_security_best_practices': True,
        'enable_compliance_warnings': True,
        'default_regions': ['us-central1', 'europe-west1', 'asia-southeast1'],
        'documentation_base_url': 'https://cloud.google.com/docs/',
        'pricing_calculator_url': 'https://cloud.google.com/products/calculator',
        'well_architected_framework': False,
        'support_levels': ['Basic', 'Standard', 'Enhanced', 'Premium'],
        'features': {
            'auto_scaling': True,
            'serverless': True,
            'managed_databases': True,
            'machine_learning': True,
            'iot': True,
            'kubernetes_native': True,
            'big_data': True
        }
    }
}

# Global dashboard settings
DASHBOARD_SETTINGS = {
    'multi_cloud': {
        'enable_cross_cloud_insights': True,
        'enable_cost_comparison': True,
        'enable_feature_comparison': True,
        'default_view': 'unified',  # 'unified', 'separated', 'primary_focus'
        'show_provider_confidence': True,
        'highlight_multi_cloud_risks': True
    },
    'visualization': {
        'default_chart_height': 400,
        'enable_interactive_charts': True,
        'color_scheme': 'provider_specific',  # 'provider_specific', 'unified', 'risk_based'
        'show_resource_counts': True,
        'enable_drill_down': True
    },
    'risk_assessment': {
        'default_profile': 'conservative',
        'enable_custom_weights': False,
        'show_confidence_intervals': True,
        'enable_what_if_analysis': False
    },
    'export': {
        'enable_csv_export': True,
        'enable_json_export': True,
        'enable_pdf_reports': False,
        'include_charts_in_export': True
    }
}


def get_provider_settings(provider: str) -> Optional[Dict[str, Any]]:
    """Get settings for a specific provider"""
    return PROVIDER_SETTINGS.get(provider.lower())


def get_dashboard_settings() -> Dict[str, Any]:
    """Get global dashboard settings"""
    return DASHBOARD_SETTINGS


def get_provider_color(provider: str, secondary: bool = False) -> str:
    """Get the primary or secondary color for a provider"""
    settings = get_provider_settings(provider)
    if not settings:
        return '#666666'  # Default gray

    color_key = 'color_secondary' if secondary else 'color_primary'
    return settings.get(color_key, '#666666')


def get_provider_display_name(provider: str) -> str:
    """Get the human-friendly display name for a provider"""
    settings = get_provider_settings(provider)
    if not settings:
        return provider.title()

    return settings.get('display_name', provider.title())


def is_feature_enabled(feature: str, provider: str = None) -> bool:
    """Check if a feature is enabled globally or for a specific provider"""

    # Check global dashboard settings first
    if provider is None:
        for category, settings in DASHBOARD_SETTINGS.items():
            if feature in settings:
                return settings[feature]
        return False

    # Check provider-specific settings
    settings = get_provider_settings(provider)
    if not settings:
        return False

    # Check in features dict
    if 'features' in settings and feature in settings['features']:
        return settings['features'][feature]

    # Check in top-level settings
    return settings.get(feature, False)


def get_environment_settings() -> Dict[str, Any]:
    """Get environment-specific settings from environment variables"""
    return {
        'default_provider': os.getenv('TERRAFORM_DASHBOARD_DEFAULT_PROVIDER', 'aws'),
        'enable_multi_cloud': os.getenv('TERRAFORM_DASHBOARD_ENABLE_MULTI_CLOUD', 'true').lower() == 'true',
        'show_provider_confidence': os.getenv('TERRAFORM_DASHBOARD_SHOW_PROVIDER_CONFIDENCE', 'true').lower() == 'true',
        'debug_mode': os.getenv('TERRAFORM_DASHBOARD_DEBUG', 'false').lower() == 'true',
        'risk_profile': os.getenv('TERRAFORM_DASHBOARD_RISK_PROFILE', 'conservative'),
        'theme': os.getenv('TERRAFORM_DASHBOARD_THEME', 'light'),
        'max_file_size_mb': int(os.getenv('TERRAFORM_DASHBOARD_MAX_FILE_SIZE', '50'))
    }


def get_provider_documentation_url(provider: str, resource_type: str = None) -> str:
    """Get documentation URL for a provider or specific resource type"""
    settings = get_provider_settings(provider)
    if not settings:
        return ''

    base_url = settings.get('documentation_base_url', '')

    if not resource_type:
        return base_url

    # Provider-specific documentation URL patterns
    if provider == 'aws':
        service = resource_type.replace('aws_', '').split('_')[0]
        return f"{base_url}services/{service}/"
    elif provider == 'azure':
        service = resource_type.replace('azurerm_', '').split('_')[0]
        return f"{base_url}services/{service}/"
    elif provider == 'google':
        service = resource_type.replace('google_', '').split('_')[0]
        return f"{base_url}products/{service}/"

    return base_url
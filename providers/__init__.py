"""
Multi-cloud provider support for Terraform Plan Dashboard

This package provides cloud provider abstractions and implementations
for AWS, Azure, and Google Cloud Platform.
"""

from .base_provider import BaseCloudProvider, ResourceCategory, RiskLevel
from .aws_provider import AWSProvider
from .azure_provider import AzureProvider
from .gcp_provider import GCPProvider
from .cloud_detector import CloudProviderDetector

__version__ = "1.0.0"

__all__ = [
    "BaseCloudProvider",
    "ResourceCategory",
    "RiskLevel",
    "AWSProvider",
    "AzureProvider",
    "GCPProvider",
    "CloudProviderDetector"
]

# Provider registry for easy access
AVAILABLE_PROVIDERS = {
    'aws': AWSProvider,
    'azure': AzureProvider,
    'google': GCPProvider
}

def get_provider(provider_name: str):
    """Get a provider instance by name"""
    if provider_name.lower() in AVAILABLE_PROVIDERS:
        return AVAILABLE_PROVIDERS[provider_name.lower()]()
    raise ValueError(f"Unknown provider: {provider_name}")

def list_supported_providers():
    """List all supported cloud providers"""
    return list(AVAILABLE_PROVIDERS.keys())
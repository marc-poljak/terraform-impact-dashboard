"""
Configuration management for multi-cloud Terraform dashboard
"""

from .risk_profiles import RISK_PROFILES, get_risk_profile
from .provider_settings import PROVIDER_SETTINGS, get_provider_settings

__all__ = [
    "RISK_PROFILES",
    "get_risk_profile",
    "PROVIDER_SETTINGS",
    "get_provider_settings"
]
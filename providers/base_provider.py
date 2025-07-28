from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from enum import Enum


class ResourceCategory(Enum):
    """Unified resource categories across all cloud providers"""
    COMPUTE = "compute"
    NETWORKING = "networking"
    STORAGE = "storage"
    DATABASE = "database"
    SECURITY = "security"
    IDENTITY = "identity"
    MONITORING = "monitoring"
    SERVERLESS = "serverless"
    CONTAINER = "container"
    ANALYTICS = "analytics"
    UNKNOWN = "unknown"


class RiskLevel(Enum):
    """Risk levels for resources"""
    LOW = 1
    MEDIUM = 5
    HIGH = 8
    CRITICAL = 10


class BaseCloudProvider(ABC):
    """Abstract base class for cloud provider implementations"""

    def __init__(self, provider_name: str):
        self.provider_name = provider_name
        self.resource_mappings = self._get_resource_mappings()
        self.risk_weights = self._get_risk_weights()
        self.critical_patterns = self._get_critical_patterns()

    @abstractmethod
    def _get_resource_mappings(self) -> Dict[str, ResourceCategory]:
        """Map provider-specific resource types to unified categories"""
        pass

    @abstractmethod
    def _get_risk_weights(self) -> Dict[str, float]:
        """Get provider-specific risk weights for resource types"""
        pass

    @abstractmethod
    def _get_critical_patterns(self) -> List[str]:
        """Get patterns that indicate critical resources for this provider"""
        pass

    @abstractmethod
    def get_action_multipliers(self) -> Dict[str, float]:
        """Get action risk multipliers (may vary by provider)"""
        pass

    @abstractmethod
    def get_provider_specific_recommendations(self, resource_changes: List[Dict[str, Any]]) -> List[str]:
        """Generate provider-specific recommendations"""
        pass

    def categorize_resource(self, resource_type: str) -> ResourceCategory:
        """Categorize a resource type into unified taxonomy"""
        # Direct mapping
        if resource_type in self.resource_mappings:
            return self.resource_mappings[resource_type]

        # Pattern matching for unknown resources
        resource_lower = resource_type.lower()

        # Compute patterns
        if any(pattern in resource_lower for pattern in ['vm', 'instance', 'compute', 'server']):
            return ResourceCategory.COMPUTE

        # Networking patterns
        if any(pattern in resource_lower for pattern in ['network', 'vpc', 'subnet', 'gateway', 'lb', 'firewall']):
            return ResourceCategory.NETWORKING

        # Storage patterns
        if any(pattern in resource_lower for pattern in ['storage', 'disk', 'volume', 'bucket', 'blob']):
            return ResourceCategory.STORAGE

        # Database patterns
        if any(pattern in resource_lower for pattern in ['database', 'db', 'sql', 'nosql', 'redis', 'mongo']):
            return ResourceCategory.DATABASE

        # Security patterns
        if any(pattern in resource_lower for pattern in ['security', 'firewall', 'policy', 'role', 'iam']):
            return ResourceCategory.SECURITY

        return ResourceCategory.UNKNOWN

    def get_resource_risk_score(self, resource_type: str) -> float:
        """Get risk score for a resource type"""
        # Direct mapping
        if resource_type in self.risk_weights:
            return self.risk_weights[resource_type]

        # Category-based fallback
        category = self.categorize_resource(resource_type)
        category_risks = {
            ResourceCategory.SECURITY: 8.0,
            ResourceCategory.NETWORKING: 7.0,
            ResourceCategory.DATABASE: 8.0,
            ResourceCategory.IDENTITY: 8.0,
            ResourceCategory.COMPUTE: 5.0,
            ResourceCategory.STORAGE: 6.0,
            ResourceCategory.SERVERLESS: 5.0,
            ResourceCategory.MONITORING: 3.0,
            ResourceCategory.ANALYTICS: 4.0,
            ResourceCategory.CONTAINER: 5.0,
            ResourceCategory.UNKNOWN: 4.0
        }

        return category_risks.get(category, 4.0)

    def is_critical_resource(self, resource_type: str) -> bool:
        """Check if resource type matches critical patterns"""
        return any(pattern in resource_type.lower() for pattern in self.critical_patterns)

    def get_deployment_time_multiplier(self) -> float:
        """Get provider-specific deployment time multiplier"""
        # Override in subclasses if providers have different deployment speeds
        return 1.0

    def supports_resource_type(self, resource_type: str) -> bool:
        """Check if this provider supports the given resource type"""
        return resource_type.startswith(f"{self.provider_name.lower()}_") or \
            resource_type in self.resource_mappings

    def extract_provider_from_resource_type(self, resource_type: str) -> Optional[str]:
        """Extract provider name from resource type"""
        parts = resource_type.split('_')
        if len(parts) >= 2:
            return parts[0]
        return None
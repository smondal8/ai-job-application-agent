from typing import Dict, List, Optional
from app.core.errors import NotFoundError
from app.schemas.discovery import AdapterInfoResponse
from app.services.discovery.base import BaseJobDiscoveryAdapter
from app.services.discovery.adapters.greenhouse import GreenhouseDiscoveryAdapter
from app.services.discovery.adapters.lever import LeverDiscoveryAdapter
from app.services.discovery.adapters.remote_tech import RemoteTechDiscoveryAdapter
from app.services.discovery.adapters.protected_fallback import ProtectedPortalFallbackAdapter


class DiscoveryAdapterRegistry:
    """Central Registry for Source-Agnostic Job Discovery Adapters."""

    def __init__(self):
        self._adapters: Dict[str, BaseJobDiscoveryAdapter] = {}
        # Register standard built-in adapters
        self.register_adapter(GreenhouseDiscoveryAdapter())
        self.register_adapter(LeverDiscoveryAdapter())
        self.register_adapter(RemoteTechDiscoveryAdapter())
        self.register_adapter(ProtectedPortalFallbackAdapter())

    def register_adapter(self, adapter: BaseJobDiscoveryAdapter) -> None:
        """Register a new discovery adapter instance."""
        self._adapters[adapter.source_name] = adapter

    def get_adapter(self, source_name: str) -> Optional[BaseJobDiscoveryAdapter]:
        """Retrieve adapter by unique source name."""
        return self._adapters.get(source_name)

    def get_adapter_or_raise(self, source_name: str) -> BaseJobDiscoveryAdapter:
        """Retrieve adapter by name or raise 404 NotFoundError."""
        adapter = self.get_adapter(source_name)
        if not adapter:
            raise NotFoundError(f"Discovery adapter for source '{source_name}' is not registered.")
        return adapter

    def list_adapters(self) -> List[AdapterInfoResponse]:
        """Return list of all registered discovery adapters and their capabilities."""
        return [
            AdapterInfoResponse(
                source_name=a.source_name,
                display_name=a.display_name,
                description=a.description,
                is_reliable=a.is_reliable,
                requires_auth=a.requires_auth,
                supports_search_criteria=a.supports_search_criteria,
                rate_limit_per_minute=a.rate_limit_per_minute,
                fallback_mode=a.fallback_mode,
                status="active",
            )
            for a in self._adapters.values()
        ]

    def get_all_adapters(self) -> Dict[str, BaseJobDiscoveryAdapter]:
        """Get copy of all registered adapters dictionary."""
        return dict(self._adapters)


discovery_registry = DiscoveryAdapterRegistry()

from typing import Any, Dict, List, Optional
from app.services.preparation.adapter_base import BasePortalPreparationAdapter
from app.services.preparation.adapters.generic_adapter import GenericPortalPreparationAdapter
from app.services.preparation.adapters.greenhouse_adapter import GreenhousePreparationAdapter
from app.services.preparation.adapters.lever_adapter import LeverPreparationAdapter
from app.services.preparation.adapters.ashby_adapter import AshbyPreparationAdapter


class PreparationAdapterRegistry:
    """Registry of Playwright browser preparation adapters."""

    def __init__(self):
        self._adapters: List[BasePortalPreparationAdapter] = []
        self._register_default_adapters()

    def _register_default_adapters(self) -> None:
        self.register(GreenhousePreparationAdapter())
        self.register(LeverPreparationAdapter())
        self.register(AshbyPreparationAdapter())
        self.register(GenericPortalPreparationAdapter())

    def register(self, adapter: BasePortalPreparationAdapter) -> None:
        self._adapters.append(adapter)

    def get_adapter(self, portal_type: Optional[str] = None, url: Optional[str] = None) -> BasePortalPreparationAdapter:
        pt = portal_type or ""
        u = url or ""
        for adapter in self._adapters:
            if adapter.can_handle(pt, u):
                return adapter
        return GenericPortalPreparationAdapter()

    def list_adapters(self) -> List[Dict[str, Any]]:
        return [
            {"portal_name": a.portal_name, "class": a.__class__.__name__}
            for a in self._adapters
        ]


preparation_adapter_registry = PreparationAdapterRegistry()

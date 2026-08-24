from typing import Any
from app.services.preparation.adapters.generic_adapter import GenericPortalPreparationAdapter


class GreenhousePreparationAdapter(GenericPortalPreparationAdapter):
    """Specialized preparation adapter for Greenhouse (boards.greenhouse.io) application forms."""

    @property
    def portal_name(self) -> str:
        return "greenhouse"

    def can_handle(self, portal_type: str, url: str) -> bool:
        if portal_type and portal_type.lower() == "greenhouse":
            return True
        if url and "greenhouse.io" in url.lower():
            return True
        return False

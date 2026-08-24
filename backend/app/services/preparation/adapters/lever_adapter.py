from typing import Any
from app.services.preparation.adapters.generic_adapter import GenericPortalPreparationAdapter


class LeverPreparationAdapter(GenericPortalPreparationAdapter):
    """Specialized preparation adapter for Lever (jobs.lever.co) application forms."""

    @property
    def portal_name(self) -> str:
        return "lever"

    def can_handle(self, portal_type: str, url: str) -> bool:
        if portal_type and portal_type.lower() == "lever":
            return True
        if url and "lever.co" in url.lower():
            return True
        return False

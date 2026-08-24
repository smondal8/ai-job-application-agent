from typing import Any
from app.services.preparation.adapters.generic_adapter import GenericPortalPreparationAdapter


class AshbyPreparationAdapter(GenericPortalPreparationAdapter):
    """Specialized preparation adapter for Ashby (jobs.ashbyhq.com) application forms."""

    @property
    def portal_name(self) -> str:
        return "ashby"

    def can_handle(self, portal_type: str, url: str) -> bool:
        if portal_type and portal_type.lower() == "ashby":
            return True
        if url and "ashbyhq.com" in url.lower():
            return True
        return False

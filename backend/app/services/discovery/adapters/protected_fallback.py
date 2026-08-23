from typing import Any, Dict, List
from urllib.parse import quote_plus

from app.core.logging import get_logger
from app.schemas.discovery import SearchCriteria
from app.services.discovery.base import BaseJobDiscoveryAdapter

logger = get_logger("app.services.discovery.protected_fallback")


class ProtectedPortalFallbackAdapter(BaseJobDiscoveryAdapter):
    """Safe Failure / Manual Fallback Adapter for CAPTCHA/Bot-Protected Sources.
    
    COMPLIANCE GUARANTEE:
    This adapter strictly refuses to bypass CAPTCHAs, spoof sessions, or perform bot bypasses.
    Instead, it builds standardized search navigation links and logs a safe fallback instruction
    enabling the user to browse compliant listings directly and import jobs into the Phase 3 Ingestion Hub.
    """

    source_name: str = "protected_portal_fallback"
    display_name: str = "Protected Portals (Safe Manual Fallback)"
    description: str = "Generates safe, compliant manual search entrypoints for bot-protected job platforms."
    rate_limit_per_minute: int = 120
    is_reliable: bool = True
    requires_auth: bool = True
    supports_search_criteria: bool = True
    fallback_mode: str = "direct_search_links"

    def _generate_manual_search_urls(self, criteria: SearchCriteria) -> List[Dict[str, str]]:
        """Construct compliant search URLs without scraping."""
        keywords_str = " ".join(criteria.keywords) if criteria.keywords else "Software Engineer"
        location_str = criteria.locations[0] if criteria.locations else ("Remote" if criteria.remote_only else "")

        kw_encoded = quote_plus(keywords_str)
        loc_encoded = quote_plus(location_str)

        return [
            {
                "portal": "LinkedIn Jobs (Compliant Search)",
                "url": f"https://www.linkedin.com/jobs/search/?keywords={kw_encoded}&location={loc_encoded}"
                + ("&f_WT=2" if criteria.remote_only else ""),
                "instructions": "Browse matching listings and paste discovered job links or text into the Phase 3 Ingestion Hub.",
            },
            {
                "portal": "Indeed (Compliant Search)",
                "url": f"https://www.indeed.com/jobs?q={kw_encoded}&l={loc_encoded}"
                + ("&remotejob=032b3046-06a3-489e-8fa2-cee3271ccb5d" if criteria.remote_only else ""),
                "instructions": "Export or copy job descriptions into the Phase 3 Ingestion Hub.",
            },
        ]

    async def fetch_jobs(self, criteria: SearchCriteria) -> List[Dict[str, Any]]:
        """Emit fallback descriptor entries for manual review rather than illegal scraping."""
        logger.info(
            "ProtectedPortalFallbackAdapter invoked: Generating %d compliant manual search links.",
            len(self._generate_manual_search_urls(criteria)),
        )
        # Does not return synthetic fake jobs; returns zero raw scrape records
        # and relies on orchestrator logging the compliant fallback links.
        return []

    def get_fallback_links(self, criteria: SearchCriteria) -> List[Dict[str, str]]:
        return self._generate_manual_search_urls(criteria)

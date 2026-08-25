import asyncio
from typing import Any, Dict, List
import httpx

from app.core.logging import get_logger
from app.schemas.discovery import SearchCriteria
from app.services.discovery.base import BaseJobDiscoveryAdapter

logger = get_logger("app.services.discovery.lever")

DEFAULT_LEVER_COMPANIES = [
    "palantir",
    "spotify",
    "mindtickle",
]


class LeverDiscoveryAdapter(BaseJobDiscoveryAdapter):
    """Reliable Public Lever Postings API Discovery Adapter."""

    source_name: str = "lever"
    display_name: str = "Lever Public Feed"
    description: str = "Discovers job postings from public Lever API endpoints with clean structured JSON."
    rate_limit_per_minute: int = 60
    max_retries: int = 3
    is_reliable: bool = True
    requires_auth: bool = False
    supports_search_criteria: bool = True

    async def _fetch_company_jobs(self, client: httpx.AsyncClient, company: str) -> List[Dict[str, Any]]:
        """Fetch listings for a single Lever company account."""
        url = f"https://api.lever.co/v0/postings/{company}?mode=json"
        await self._throttle()

        for attempt in range(1, self.max_retries + 1):
            try:
                response = await client.get(url, timeout=10.0)
                if response.status_code == 200:
                    raw_postings = response.json()
                    if not isinstance(raw_postings, list):
                        return []

                    standardized = []
                    for posting in raw_postings:
                        categories = posting.get("categories") or {}
                        location_str = categories.get("location") or ""
                        team_name = categories.get("team")
                        commitment = categories.get("commitment") or "full-time"

                        standardized.append({
                            "external_id": str(posting.get("id")),
                            "source": "discovery_lever",
                            "title": posting.get("text", ""),
                            "company": company.capitalize(),
                            "location": location_str,
                            "department": team_name,
                            "url": posting.get("hostedUrl"),
                            "description_raw": posting.get("descriptionPlain") or posting.get("description"),
                            "remote_type": "remote" if "remote" in location_str.lower() else "unspecified",
                            "job_type": str(commitment).lower(),
                        })
                    return standardized
                elif response.status_code == 404:
                    logger.warning("Lever company '%s' not found (404)", company)
                    return []
                elif response.status_code in [429, 500, 502, 503, 504]:
                    await asyncio.sleep(self.retry_backoff_base_sec * (2 ** (attempt - 1)))
                else:
                    logger.error("Lever HTTP %d for company '%s'", response.status_code, company)
                    return []
            except Exception as exc:
                if attempt == self.max_retries:
                    logger.warning("Failed to fetch Lever company '%s': %s", company, exc)
                    return []
                await asyncio.sleep(self.retry_backoff_base_sec * (2 ** (attempt - 1)))
        return []

    async def fetch_jobs(self, criteria: SearchCriteria) -> List[Dict[str, Any]]:
        """Discover jobs from Lever public APIs matching criteria."""
        companies_to_query = (
            criteria.target_companies
            if criteria.target_companies
            else DEFAULT_LEVER_COMPANIES
        )

        all_raw_jobs: List[Dict[str, Any]] = []

        async with httpx.AsyncClient() as client:
            tasks = [self._fetch_company_jobs(client, comp.lower().strip()) for comp in companies_to_query]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            for res in results:
                if isinstance(res, list):
                    all_raw_jobs.extend(res)

        return self.filter_by_criteria(all_raw_jobs, criteria)

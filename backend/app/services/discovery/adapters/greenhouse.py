import asyncio
import re
from typing import Any, Dict, List
import httpx

from app.core.logging import get_logger
from app.schemas.discovery import SearchCriteria
from app.services.discovery.base import BaseJobDiscoveryAdapter

logger = get_logger("app.services.discovery.greenhouse")

DEFAULT_GREENHOUSE_BOARDS = [
    "stripe",
    "figma",
    "anthropic",
    "datadog",
    "cloudflare",
    "affirm",
    "pinterest",
    "dropbox",
    "discord",
]


class GreenhouseDiscoveryAdapter(BaseJobDiscoveryAdapter):
    """Reliable Public Greenhouse Job Board API Discovery Adapter."""

    source_name: str = "greenhouse"
    display_name: str = "Greenhouse Public Feed"
    description: str = "Discovers job postings from public Greenhouse board APIs without authentication or CAPTCHAs."
    rate_limit_per_minute: int = 60
    max_retries: int = 3
    is_reliable: bool = True
    requires_auth: bool = False
    supports_search_criteria: bool = True

    def _strip_html(self, text: str) -> str:
        """Strip HTML tags from Greenhouse job description content."""
        if not text:
            return ""
        clean = re.sub(r"<[^>]+>", " ", text)
        clean = re.sub(r"&[a-z]+;", " ", clean)
        clean = re.sub(r"\s+", " ", clean).strip()
        return clean

    async def _fetch_board_jobs(self, client: httpx.AsyncClient, board: str) -> List[Dict[str, Any]]:
        """Fetch listings for a single Greenhouse board token."""
        url = f"https://boards-api.greenhouse.io/v1/boards/{board}/jobs?content=true"
        await self._throttle()

        for attempt in range(1, self.max_retries + 1):
            try:
                response = await client.get(url, timeout=10.0)
                if response.status_code == 200:
                    data = response.json()
                    raw_jobs = data.get("jobs", [])
                    standardized = []
                    for rj in raw_jobs:
                        loc_obj = rj.get("location") or {}
                        location_str = loc_obj.get("name") if isinstance(loc_obj, dict) else str(loc_obj)
                        depts = rj.get("departments") or []
                        dept_name = depts[0].get("name") if depts and isinstance(depts[0], dict) else None
                        
                        raw_content = rj.get("content") or ""
                        clean_desc = self._strip_html(raw_content)

                        standardized.append({
                            "external_id": str(rj.get("id")),
                            "source": "greenhouse",
                            "title": rj.get("title", ""),
                            "company": board.capitalize(),
                            "location": location_str,
                            "department": dept_name,
                            "url": rj.get("absolute_url"),
                            "description_raw": clean_desc or raw_content,
                            "remote_type": "remote" if "remote" in (location_str or "").lower() else "unspecified",
                            "job_type": "full-time",
                        })
                    return standardized
                elif response.status_code == 404:
                    logger.warning("Greenhouse board '%s' not found (404)", board)
                    return []
                elif response.status_code in [429, 500, 502, 503, 504]:
                    await asyncio.sleep(self.retry_backoff_base_sec * (2 ** (attempt - 1)))
                else:
                    logger.error("Greenhouse HTTP %d for board '%s'", response.status_code, board)
                    return []
            except Exception as exc:
                if attempt == self.max_retries:
                    logger.warning("Failed to fetch Greenhouse board '%s': %s", board, exc)
                    return []
                await asyncio.sleep(self.retry_backoff_base_sec * (2 ** (attempt - 1)))
        return []

    async def fetch_jobs(self, criteria: SearchCriteria) -> List[Dict[str, Any]]:
        """Discover jobs from Greenhouse public boards matching criteria."""
        boards_to_query = (
            criteria.target_companies
            if criteria.target_companies
            else DEFAULT_GREENHOUSE_BOARDS
        )

        all_raw_jobs: List[Dict[str, Any]] = []

        async with httpx.AsyncClient() as client:
            tasks = [self._fetch_board_jobs(client, board.lower().strip()) for board in boards_to_query]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            for res in results:
                if isinstance(res, list):
                    all_raw_jobs.extend(res)

        return self.filter_by_criteria(all_raw_jobs, criteria)

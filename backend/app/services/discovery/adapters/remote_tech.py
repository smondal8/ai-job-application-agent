from typing import Any, Dict, List
import httpx

from app.core.logging import get_logger
from app.schemas.discovery import SearchCriteria
from app.services.discovery.base import BaseJobDiscoveryAdapter

logger = get_logger("app.services.discovery.remote_tech")


class RemoteTechDiscoveryAdapter(BaseJobDiscoveryAdapter):
    """Reliable Public Remote Tech & Engineering Listings Feed Adapter."""

    source_name: str = "remote_tech"
    display_name: str = "Remote Tech Feeds"
    description: str = "Discovers remote software engineering opportunities from public aggregated developer feeds."
    rate_limit_per_minute: int = 30
    max_retries: int = 2
    is_reliable: bool = True
    requires_auth: bool = False
    supports_search_criteria: bool = True

    async def fetch_jobs(self, criteria: SearchCriteria) -> List[Dict[str, Any]]:
        """Fetch remote tech jobs matching criteria."""
        await self._throttle()
        url = "https://remoteok.com/api"

        try:
            async with httpx.AsyncClient() as client:
                headers = {"User-Agent": "AIJobAgent/0.3.0 (Operational; dev)"}
                response = await client.get(url, headers=headers, timeout=12.0)
                if response.status_code == 200:
                    data = response.json()
                    # First element in remoteok API is legal disclaimer
                    raw_items = [d for d in data if isinstance(d, dict) and d.get("position")]
                    
                    standardized = []
                    for item in raw_items:
                        skills = item.get("tags") or []
                        standardized.append({
                            "external_id": str(item.get("id")),
                            "source": "discovery_remote_tech",
                            "title": item.get("position", ""),
                            "company": item.get("company", "Unknown"),
                            "location": item.get("location") or "Remote",
                            "url": item.get("url"),
                            "description_raw": item.get("description"),
                            "remote_type": "remote",
                            "job_type": "full-time",
                            "skills_raw": skills if isinstance(skills, list) else [str(skills)],
                            "salary_min": item.get("salary_min"),
                            "salary_max": item.get("salary_max"),
                        })
                    return self.filter_by_criteria(standardized, criteria)
                else:
                    logger.warning("RemoteTech feed returned status %d", response.status_code)
                    return []
        except Exception as exc:
            logger.warning("RemoteTech feed unreachable: %s", exc)
            return []

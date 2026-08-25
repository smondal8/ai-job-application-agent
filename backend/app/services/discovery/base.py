import abc
import asyncio
import time
from typing import Any, Dict, List, Optional
from app.core.logging import get_logger
from app.schemas.discovery import SearchCriteria

logger = get_logger("app.services.discovery.base")


class BaseJobDiscoveryAdapter(abc.ABC):
    """Abstract Base Class for Source-Agnostic Job Discovery Adapters."""

    source_name: str = "base"
    display_name: str = "Base Adapter"
    description: str = "Abstract base adapter interface"
    rate_limit_per_minute: int = 60
    max_retries: int = 3
    retry_backoff_base_sec: float = 0.5
    is_reliable: bool = True
    requires_auth: bool = False
    supports_search_criteria: bool = True
    fallback_mode: Optional[str] = None

    def __init__(self):
        self._last_request_timestamp: float = 0.0

    async def _throttle(self):
        """Enforce rate limits per adapter."""
        if self.rate_limit_per_minute > 0:
            min_interval = 60.0 / self.rate_limit_per_minute
            now = time.time()
            elapsed = now - self._last_request_timestamp
            if elapsed < min_interval:
                sleep_time = min_interval - elapsed
                await asyncio.sleep(sleep_time)
            self._last_request_timestamp = time.time()

    @staticmethod
    def _expand_location_aliases(search_location: str) -> List[str]:
        """Expand regional and city aliases for intelligent, high-precision matching."""
        loc = search_location.lower().strip()
        if loc in ["bangalore", "bengaluru", "blr"]:
            return ["bangalore", "bengaluru", "blr", "india", "karnataka"]
        if loc in ["india", "in"]:
            return [
                "india",
                "bangalore",
                "bengaluru",
                "blr",
                "hyderabad",
                "pune",
                "delhi",
                "mumbai",
                "chennai",
                "noida",
                "gurgaon",
                "gurugram",
            ]
        if loc in ["remote", "anywhere", "worldwide", "distributed"]:
            return ["remote", "anywhere", "worldwide", "distributed"]
        return [loc]

    def filter_by_criteria(self, jobs: List[Dict[str, Any]], criteria: SearchCriteria) -> List[Dict[str, Any]]:
        """Filter standardized job records against user search criteria."""
        filtered = []
        keywords = [k.lower().strip() for k in criteria.keywords if k.strip()]
        locations = [loc.lower().strip() for loc in criteria.locations if loc.strip()]
        target_companies = [c.lower().strip() for c in criteria.target_companies if c.strip()]
        seniority_levels = [s.lower().strip() for s in criteria.seniority_levels if s.strip()]

        for job in jobs:
            title = str(job.get("title") or "").lower()
            company = str(job.get("company") or "").lower()
            location = str(job.get("location") or "").lower()
            description = str(job.get("description_raw") or "").lower()
            remote_type = str(job.get("remote_type") or "").lower()
            seniority = str(job.get("seniority_level") or "").lower()

            # 1. Company filter
            if target_companies and not any(tc in company for tc in target_companies):
                continue

            # 2. Remote filter
            if criteria.remote_only and remote_type != "remote":
                if "remote" not in location and "remote" not in title:
                    continue

            # 3. Location filter with intelligent aliasing
            if locations:
                matches_location = False
                for loc_query in locations:
                    clean_query = loc_query.lower().strip()
                    if not clean_query:
                        continue

                    if clean_query in ["remote", "anywhere", "worldwide", "distributed"]:
                        if remote_type == "remote" or any(
                            r in location or r in title for r in ["remote", "anywhere", "worldwide", "distributed"]
                        ):
                            matches_location = True
                            break
                    else:
                        aliases = self._expand_location_aliases(clean_query)
                        if any(alias in location for alias in aliases):
                            matches_location = True
                            break

                if not matches_location:
                    continue

            # 4. Keyword filter (match against title or description)
            if keywords:
                matches_keyword = any(k in title or k in description for k in keywords)
                if not matches_keyword:
                    continue

            # 5. Seniority filter
            if seniority_levels:
                matches_seniority = any(s in seniority or s in title for s in seniority_levels)
                if not matches_seniority:
                    continue

            # 6. Salary filter
            if criteria.min_salary and job.get("salary_min"):
                try:
                    if float(job["salary_min"]) < float(criteria.min_salary):
                        continue
                except (ValueError, TypeError):
                    pass

            filtered.append(job)
            if len(filtered) >= criteria.max_results_per_source:
                break

        return filtered

    @abc.abstractmethod
    async def fetch_jobs(self, criteria: SearchCriteria) -> List[Dict[str, Any]]:
        """Fetch and standardize job records from source."""
        raise NotImplementedError("Subclasses must implement fetch_jobs")

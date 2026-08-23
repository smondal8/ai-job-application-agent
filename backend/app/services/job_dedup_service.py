import hashlib
import re
from typing import Any, Dict, Optional, Tuple
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from sqlalchemy.orm import Session

from app.models.job import Job
from app.core.logging import get_logger

logger = get_logger("app.services.job_dedup")

# Common corporate suffixes to normalize
COMPANY_SUFFIX_REGEX = re.compile(
    r"\b(inc\.?|incorporated|llc\.?|corp\.?|corporation|ltd\.?|limited|gmbh|co\.?|company|pvt\.?|technologies|solutions|group)\b",
    re.IGNORECASE,
)

# Common tracking URL query parameters to strip
TRACKING_PARAMS = {
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_term",
    "utm_content",
    "ref",
    "refId",
    "source",
    "gh_jid",
    "gh_src",
    "lever-source",
    "sessionId",
    "token",
    "fbclid",
    "gclid",
    "trk",
    "position",
    "pageNum",
}

# Requisition ID pattern in job titles:
# Must be bracketed (e.g. [Req 123], (12345), (Req #abc)) OR explicitly prefixed with req/requisition/job id/#
REQ_CODE_REGEX = re.compile(
    r"(?:\s*[\(\[\{]\s*(?:req(?:uisition)?|job\s*id|id)?\s*#?\s*[A-Za-z0-9_-]+\s*[\)\]\}]|\s*[-–—]\s*(?:req(?:uisition)?|job\s*id|id)\s*#?\s*[A-Za-z0-9_-]+|\s*#(?:req-)?[0-9]{4,})$",
    re.IGNORECASE,
)


class JobDeduplicationService:
    """Deterministic and Conservative Job Deduplication Subsystem.
    
    GUARANTEES:
    1. Deterministic hashing: Identical jobs produce the exact same deduplication hash.
    2. Conservative matching: NEVER discard a potentially different job merely because
       titles look similar or share keywords.
    3. Location-aware: Same title at same company in different locations (e.g. London vs NYC)
       are preserved as distinct separate positions.
    4. Seniority-aware: "Senior Engineer" vs "Staff Engineer" are distinct jobs.
    """

    def normalize_company(self, company: str) -> str:
        """Standardize company name (lowercase, strip legal suffixes, normalize whitespace)."""
        if not company:
            return ""
        s = company.strip().lower()
        # Remove punctuation except alphanumeric and spaces
        s = re.sub(r"[^\w\s]", " ", s)
        # Remove corporate suffixes
        s = COMPANY_SUFFIX_REGEX.sub(" ", s)
        # Collapse whitespace
        s = re.sub(r"\s+", " ", s).strip()
        return s or company.strip().lower()

    def normalize_title(self, title: str) -> str:
        """Standardize title while strictly preserving seniority and functional role differences."""
        if not title:
            return ""
        s = title.strip().lower()
        # Strip trailing requisition IDs only if specifically formatted
        s = REQ_CODE_REGEX.sub("", s).strip()
        # Normalize punctuation and whitespace
        s = re.sub(r"[^\w\s/+-]", " ", s)
        s = re.sub(r"\s+", " ", s).strip()
        return s or title.strip().lower()

    def normalize_location(self, location: Optional[str]) -> str:
        """Standardize location string (lowercase, normalize remote indicators)."""
        if not location or not location.strip():
            return "unspecified"
        loc = location.strip().lower()
        if any(r in loc for r in ["remote", "work from home", "wfh", "anywhere", "virtual"]):
            return "remote"
        # Normalize punctuation
        loc = re.sub(r"[^\w\s,]", " ", loc)
        loc = re.sub(r"\s+", " ", loc).strip()
        return loc

    def normalize_url(self, url: Optional[str]) -> Optional[str]:
        """Strip tracking parameters and fragments to produce a canonical URL."""
        if not url or not url.strip():
            return None
        try:
            parsed = urlparse(url.strip())
            if not parsed.scheme or not parsed.netloc:
                return url.strip()
            
            # Filter query params
            query_dict = parse_qs(parsed.query, keep_blank_values=False)
            filtered_query = {k: v for k, v in query_dict.items() if k.lower() not in TRACKING_PARAMS}
            
            # Reconstruct clean url
            clean_query = urlencode(filtered_query, doseq=True)
            clean_path = parsed.path.rstrip("/")
            
            clean_tuple = (
                parsed.scheme.lower(),
                parsed.netloc.lower(),
                clean_path,
                "",  # params
                clean_query,
                "",  # fragment
            )
            return urlunparse(clean_tuple)
        except Exception:
            return url.strip()

    def compute_dedup_hash(
        self,
        company: str,
        title: str,
        location: Optional[str] = None,
        source: str = "manual",
        external_id: Optional[str] = None,
        url: Optional[str] = None,
    ) -> Tuple[str, str, str, str]:
        """Compute deterministic deduplication hash and return normalized tuple.
        
        Returns:
            Tuple of (dedup_hash, norm_company, norm_title, norm_location)
        """
        norm_company = self.normalize_company(company)
        norm_title = self.normalize_title(title)
        norm_location = self.normalize_location(location)
        clean_url = self.normalize_url(url)
        src = source.strip().lower()

        # Priority 1: Exact Source + External ID
        if external_id and external_id.strip():
            signature = f"ext:{src}:{external_id.strip()}"
        # Priority 2: Clean Canonical URL
        elif clean_url:
            signature = f"url:{clean_url}"
        # Priority 3: Exact Natural Key Tuple (Company + Title + Location + Source)
        else:
            signature = f"natural:{norm_company}:{norm_title}:{norm_location}:{src}"

        dedup_hash = hashlib.sha256(signature.encode("utf-8")).hexdigest()
        return dedup_hash, norm_company, norm_title, norm_location

    def find_existing_duplicate(
        self, db: Session, job_dict: Dict[str, Any]
    ) -> Optional[Job]:
        """Check if an exact duplicate already exists in the database.
        
        Conservative Strategy:
        1. Check by calculated dedup_hash.
        2. Check by source + external_id (if external_id exists).
        3. Check by normalized canonical URL (if url exists).
        4. Check by exact match of (normalized_company, normalized_title, normalized_location).
        """
        company = job_dict.get("company", "")
        title = job_dict.get("title", "")
        location = job_dict.get("location")
        source = job_dict.get("source", "manual")
        external_id = job_dict.get("external_id")
        url = job_dict.get("url")

        dedup_hash, norm_comp, norm_tit, norm_loc = self.compute_dedup_hash(
            company=company,
            title=title,
            location=location,
            source=source,
            external_id=external_id,
            url=url,
        )

        # 1. Direct hash match
        existing = db.query(Job).filter(Job.dedup_hash == dedup_hash).first()
        if existing:
            return existing

        # 2. Source + External ID match
        if external_id and external_id.strip():
            existing = (
                db.query(Job)
                .filter(Job.source == source, Job.external_id == external_id.strip())
                .first()
            )
            if existing:
                return existing

        # 3. Canonical URL match
        clean_url = self.normalize_url(url)
        if clean_url:
            existing = db.query(Job).filter(Job.url == clean_url).first()
            if existing:
                return existing

        # 4. Strict natural tuple match
        if norm_comp and norm_tit:
            query = db.query(Job).filter(
                Job.normalized_company == norm_comp,
                Job.normalized_title == norm_tit,
            )
            if norm_loc and norm_loc != "unspecified":
                query = query.filter(Job.normalized_location == norm_loc)
            
            existing = query.first()
            if existing:
                return existing

        return None


job_dedup_service = JobDeduplicationService()

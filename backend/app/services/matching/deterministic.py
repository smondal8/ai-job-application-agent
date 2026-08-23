import re
from typing import Any, Dict, List, Set, Tuple


COMMON_SKILL_ALIASES: Dict[str, Set[str]] = {
    "python": {"python", "py", "python3"},
    "javascript": {"javascript", "js", "ecmascript"},
    "typescript": {"typescript", "ts"},
    "react": {"react", "react.js", "reactjs"},
    "fastapi": {"fastapi", "fast-api"},
    "django": {"django", "django-rest-framework", "drf"},
    "postgresql": {"postgresql", "postgres", "psql"},
    "sqlite": {"sqlite", "sqlite3"},
    "docker": {"docker", "docker-compose"},
    "kubernetes": {"kubernetes", "k8s"},
    "aws": {"aws", "amazon web services"},
    "gcp": {"gcp", "google cloud", "google cloud platform"},
    "distributed systems": {"distributed systems", "distributed computing", "consensus"},
    "machine learning": {"machine learning", "ml", "deep learning", "ai"},
    "node": {"node", "node.js", "nodejs"},
    "golang": {"golang", "go"},
    "rust": {"rust", "rustlang"},
}


class DeterministicMatcher:
    """Deterministic, rule-based matching engine for candidate profiles and job descriptions."""

    def normalize_term(self, term: str) -> str:
        """Normalize a skill/keyword term (lowercase, punctuation stripped)."""
        return re.sub(r"[^\w\s#+.-]", "", term.strip().lower())

    def match_skills(
        self,
        candidate_skills: List[Dict[str, Any]],
        job_skills_raw: List[str],
        job_description_text: str,
    ) -> Tuple[List[str], List[str], float]:
        """Perform exact and alias-based deterministic matching between verified candidate skills and JD.

        Returns:
            (matched_skills, missing_skills, deterministic_score_0_to_100)
        """
        # 1. Normalize candidate verified skills
        candidate_term_map: Dict[str, str] = {}  # normalized_term -> display_name
        for s in candidate_skills:
            name = s.get("name", "")
            if not name:
                continue
            norm = self.normalize_term(name)
            candidate_term_map[norm] = name
            # Also expand known aliases
            for canonical, aliases in COMMON_SKILL_ALIASES.items():
                if norm in aliases or norm == canonical:
                    for alias in aliases:
                        candidate_term_map[alias] = name

        # 2. Extract job skills to check (from job_skills_raw + high-signal mentions in JD)
        job_terms_to_check: Dict[str, str] = {}  # normalized -> display_name
        for raw_s in job_skills_raw:
            norm = self.normalize_term(raw_s)
            if norm:
                job_terms_to_check[norm] = raw_s

        # Also search description for common technical skills if job_skills_raw is sparse
        desc_lower = job_description_text.lower()
        for canonical, aliases in COMMON_SKILL_ALIASES.items():
            for alias in aliases:
                # Word boundary check
                pattern = r"\b" + re.escape(alias) + r"\b"
                if re.search(pattern, desc_lower):
                    job_terms_to_check[canonical] = canonical.title()
                    break

        if not job_terms_to_check:
            # If no skills could be identified in JD, give neutral score
            return (list(candidate_term_map.values())[:5], [], 70.0)

        matched: Set[str] = set()
        missing: Set[str] = set()

        for j_norm, j_display in job_terms_to_check.items():
            if j_norm in candidate_term_map:
                matched.add(candidate_term_map[j_norm])
            else:
                # Check substring match
                is_sub = False
                for c_norm, c_display in candidate_term_map.items():
                    if c_norm in j_norm or j_norm in c_norm:
                        matched.add(c_display)
                        is_sub = True
                        break
                if not is_sub:
                    missing.add(j_display)

        matched_list = sorted(list(matched))
        missing_list = sorted(list(missing))

        total_checked = len(matched_list) + len(missing_list)
        if total_checked == 0:
            score = 50.0
        else:
            score = round((len(matched_list) / total_checked) * 100.0, 1)

        return (matched_list, missing_list, score)

    def evaluate_criteria(
        self,
        candidate_facts: Dict[str, Any],
        job_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Evaluate deterministic criteria like experience years, remote policy, and location."""
        candidate_skills = candidate_facts.get("skills", [])
        experiences = candidate_facts.get("experiences", [])

        # Calculate rough verified candidate experience years
        total_exp_years = len(experiences) * 2.0  # Conservative estimate if exact dates not parsed

        req_years_min = job_data.get("experience_years_min")
        req_years_max = job_data.get("experience_years_max")

        experience_meets_min = True
        if req_years_min is not None and req_years_min > 0:
            experience_meets_min = total_exp_years >= req_years_min

        # Remote / Location match
        cand_loc = (candidate_facts.get("candidate", {}).get("location") or "").lower()
        job_loc = (job_data.get("location") or "").lower()
        job_remote = (job_data.get("remote_type") or "unspecified").lower()

        remote_compatible = True
        if job_remote in ["on_site", "hybrid"] and cand_loc and job_loc:
            # Check if cities/states match
            if cand_loc not in job_loc and job_loc not in cand_loc:
                remote_compatible = False

        return {
            "total_candidate_exp_years_est": total_exp_years,
            "experience_meets_min": experience_meets_min,
            "remote_compatible": remote_compatible,
        }


deterministic_matcher = DeterministicMatcher()

from typing import Any, Dict, List, Optional, Set
from pydantic import BaseModel, Field

from app.services.tailoring.fact_registry import AtomicFactRegistry


class UntracedClaim(BaseModel):
    """Details of a claim that failed fact attribution."""
    section: str
    text: str
    invalid_fact_ids: List[str] = Field(default_factory=list)
    reason: str


class ValidationResult(BaseModel):
    """Comprehensive traceability validation report for tailored application materials."""
    is_valid: bool
    status: str  # "valid", "requires_human_review", "rejected"
    traceability_score: float  # 0.0 to 100.0
    total_claims_count: int
    verified_claims_count: int
    untraced_claims: List[UntracedClaim] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    traceability_matrix: Dict[str, List[str]] = Field(default_factory=dict)


class TraceabilityValidator:
    """Validates that all tailored resume and cover letter claims trace directly to verified candidate facts."""

    def validate(
        self,
        tailored_data: Dict[str, Any],
        fact_registry: AtomicFactRegistry,
    ) -> ValidationResult:
        all_facts = fact_registry.all_fact_ids()
        traceability_matrix: Dict[str, List[str]] = {}
        untraced_claims: List[UntracedClaim] = []
        warnings: List[str] = []

        total_claims = 0
        verified_claims = 0

        # Helper to validate a list of fact_ids for a given claim
        def check_claim(section_name: str, claim_text: str, fact_ids: List[str]):
            nonlocal total_claims, verified_claims
            total_claims += 1

            if not claim_text or not claim_text.strip():
                return

            if not fact_ids:
                untraced_claims.append(
                    UntracedClaim(
                        section=section_name,
                        text=claim_text,
                        invalid_fact_ids=[],
                        reason="Missing source_fact_ids attribution",
                    )
                )
                return

            valid_ids = []
            invalid_ids = []

            for fid in fact_ids:
                fid_clean = fid.strip()
                if fact_registry.has(fid_clean):
                    valid_ids.append(fid_clean)
                    traceability_matrix.setdefault(fid_clean, []).append(f"[{section_name}] {claim_text}")
                else:
                    # Check prefix match fallback (e.g. "skill:python" or "exp:1")
                    matched_prefix = False
                    for existing_fid in all_facts:
                        if existing_fid.startswith(fid_clean) or fid_clean.startswith(existing_fid):
                            valid_ids.append(existing_fid)
                            traceability_matrix.setdefault(existing_fid, []).append(f"[{section_name}] {claim_text}")
                            matched_prefix = True
                            break
                    if not matched_prefix:
                        invalid_ids.append(fid_clean)

            if invalid_ids:
                warnings.append(f"Section '{section_name}' referenced unverified fact IDs: {invalid_ids}")

            if valid_ids:
                verified_claims += 1
            else:
                untraced_claims.append(
                    UntracedClaim(
                        section=section_name,
                        text=claim_text,
                        invalid_fact_ids=invalid_ids,
                        reason="None of the referenced source_fact_ids match verified candidate facts",
                    )
                )

        # 1. Validate Executive Summary
        summary_obj = tailored_data.get("tailored_summary")
        if isinstance(summary_obj, dict):
            summary_text = summary_obj.get("text", "")
            summary_fids = summary_obj.get("source_fact_ids", [])
            check_claim("summary", summary_text, summary_fids)
        elif isinstance(summary_obj, str) and summary_obj.strip():
            check_claim("summary", summary_obj, [])

        # 2. Validate Tailored Experience Highlights
        for exp in tailored_data.get("tailored_experience", []):
            company = exp.get("company", "Experience")
            highlights = exp.get("tailored_highlights", [])
            for h in highlights:
                if isinstance(h, dict):
                    h_text = h.get("text", "")
                    h_fids = h.get("source_fact_ids", [])
                    check_claim(f"experience:{company}", h_text, h_fids)
                elif isinstance(h, str) and h.strip():
                    check_claim(f"experience:{company}", h, [])

        # 3. Validate Highlighted Skills
        for sk in tailored_data.get("highlighted_skills", []):
            if isinstance(sk, dict):
                sk_name = sk.get("name", "")
                sk_fids = sk.get("source_fact_ids", [])
                check_claim(f"skill:{sk_name}", sk_name, sk_fids)
            elif isinstance(sk, str) and sk.strip():
                check_claim(f"skill:{sk}", sk, [f"skill:{sk.lower()}"])

        # 4. Validate Cover Letter Paragraphs
        for p in tailored_data.get("cover_letter_paragraphs", []):
            if isinstance(p, dict):
                p_type = p.get("paragraph_type", "body")
                p_text = p.get("text", "")
                p_fids = p.get("source_fact_ids", [])
                check_claim(f"cover_letter:{p_type}", p_text, p_fids)
            elif isinstance(p, str) and p.strip():
                check_claim("cover_letter:paragraph", p, [])

        # Calculate Score & Status
        if total_claims == 0:
            score = 100.0
            status = "valid"
            is_valid = True
        else:
            score = round((verified_claims / total_claims) * 100.0, 1)
            if score == 100.0 and len(untraced_claims) == 0:
                status = "valid"
                is_valid = True
            elif score >= 75.0:
                status = "requires_human_review"
                is_valid = False
            else:
                status = "rejected"
                is_valid = False

        return ValidationResult(
            is_valid=is_valid,
            status=status,
            traceability_score=score,
            total_claims_count=total_claims,
            verified_claims_count=verified_claims,
            untraced_claims=untraced_claims,
            warnings=warnings,
            traceability_matrix=traceability_matrix,
        )


traceability_validator = TraceabilityValidator()

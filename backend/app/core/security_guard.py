import re
from typing import Any, Dict, List, Optional
from app.core.errors import ForbiddenError, SecurityViolationError
from app.core.logging import get_logger

logger = get_logger("app.core.security_guard")


class ApplicationSecurityGuard:
    """Enterprise-wide security policy enforcer.
    
    Treats all job descriptions, job pages, employer text, form labels, and web content as UNTRUSTED.
    Enforces that LLM outputs or adversarial DOM directives can NEVER:
    1. Change approval requirements
    2. Authorize application submission
    3. Disable safety checks
    4. Request secrets / credentials
    5. Reinterpret system instructions or mutate state transitions
    """

    ADVERSARIAL_PATTERNS = [
        re.compile(r"ignore\s+(all\s+)?previous\s+instructions", re.IGNORECASE),
        re.compile(r"bypass\s+(human\s+)?approval", re.IGNORECASE),
        re.compile(r"auto[- ]?submit\s+immediately", re.IGNORECASE),
        re.compile(r"grant\s+submission\s+authorization", re.IGNORECASE),
        re.compile(r"disable\s+(safety|submit)\s+guard", re.IGNORECASE),
        re.compile(r"reveal\s+(api\s+key|secret|token|password)", re.IGNORECASE),
        re.compile(r"print\s+system\s+prompt", re.IGNORECASE),
        re.compile(r"system:\s*override", re.IGNORECASE),
    ]

    FORBIDDEN_LLM_KEYS = {
        "is_approved",
        "approval_token",
        "submit_authorized",
        "skip_human_review",
        "disable_safety_guard",
        "execute_submission",
    }

    @classmethod
    def sanitize_untrusted_input(cls, text: Optional[str], context_label: str = "untrusted_content") -> str:
        """Sanitizes untrusted input (e.g. JD, portal HTML, employer message) ensuring it remains passive data."""
        if not text or not isinstance(text, str):
            return ""

        # Normalize unicode and strip non-printable control characters except standard whitespace
        cleaned = "".join(ch for ch in text if ch.isprintable() or ch in "\n\r\t")
        return cleaned

    @classmethod
    def assert_llm_output_boundaries(cls, llm_response_dict: Dict[str, Any]) -> None:
        """Validates that structured LLM output does NOT contain forbidden authorization or safety override keys."""
        if not isinstance(llm_response_dict, dict):
            return

        for forbidden_key in cls.FORBIDDEN_LLM_KEYS:
            if forbidden_key in llm_response_dict:
                logger.error(f"Security violation: LLM attempted to produce forbidden key '{forbidden_key}'")
                raise SecurityViolationError(
                    f"LLM output violated security boundary by producing restricted property '{forbidden_key}'."
                )

    @classmethod
    def validate_action_authorization(cls, is_human_authorized: bool, action_name: str) -> None:
        """Enforces that destructive or state-altering actions (e.g., preparation, submission) require human authorization."""
        if not is_human_authorized:
            logger.error(f"Security rejection: Attempted '{action_name}' without valid server-side human approval.")
            raise ForbiddenError(f"Action '{action_name}' is forbidden without valid human approval authorization.")

    @classmethod
    def detect_prompt_injection_threats(cls, text: str) -> List[str]:
        """Detects known prompt injection indicators in untrusted texts for audit and logging."""
        detected = []
        if not text:
            return detected
        for pattern in cls.ADVERSARIAL_PATTERNS:
            if pattern.search(text):
                detected.append(pattern.pattern)
        return detected


application_security_guard = ApplicationSecurityGuard()

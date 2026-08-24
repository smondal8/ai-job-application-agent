import re
from typing import Any, Dict, List, Union

REDACTED_TEXT = "[REDACTED]"

# Regex patterns for sensitive credentials, keys, and PII
SECRET_PATTERNS = [
    # Bearer tokens & auth headers
    (re.compile(r"(Bearer\s+)[A-Za-z0-9\-\._~\+\/]+=*", re.IGNORECASE), r"\1[REDACTED_TOKEN]"),
    # API Keys & Secrets
    (re.compile(r"(sk-[a-zA-Z0-9]{20,})", re.IGNORECASE), "[REDACTED_API_KEY]"),
    (re.compile(r"(ghp_[a-zA-Z0-9]{36,})", re.IGNORECASE), "[REDACTED_GITHUB_TOKEN]"),
    (re.compile(r"(token=)[^\s&'\"]+", re.IGNORECASE), r"\1[REDACTED]"),
    (re.compile(r"(password[\"']?\s*[:=]\s*[\"'])[^\"']+", re.IGNORECASE), r"\1[REDACTED]"),
    (re.compile(r"(secret[\"']?\s*[:=]\s*[\"'])[^\"']+", re.IGNORECASE), r"\1[REDACTED]"),
    (re.compile(r"(api_key[\"']?\s*[:=]\s*[\"'])[^\"']+", re.IGNORECASE), r"\1[REDACTED]"),
    (re.compile(r"(private_key[\"']?\s*[:=]\s*[\"'])[^\"']+", re.IGNORECASE), r"\1[REDACTED]"),
    # Private Key blocks
    (re.compile(r"-----BEGIN [A-Z ]+PRIVATE KEY-----[^-]+-----END [A-Z ]+PRIVATE KEY-----", re.DOTALL), "[REDACTED_PRIVATE_KEY]"),
    # Credit Card numbers
    (re.compile(r"\b(?:\d[ -]*?){13,16}\b"), "[REDACTED_CARD]"),
    # US Social Security Number
    (re.compile(r"\b\d{3}-\d{2}-\d{4}\b"), "[REDACTED_SSN]"),
]

SENSITIVE_KEY_NAMES = {
    "password",
    "passwd",
    "secret",
    "api_key",
    "apikey",
    "token",
    "access_token",
    "refresh_token",
    "authorization",
    "private_key",
    "ssn",
    "credit_card",
    "cvv",
}


class RedactionService:
    """Enterprise-grade sensitive data and credential redaction service."""

    @classmethod
    def redact_text(cls, text: str) -> str:
        """Sanitizes raw strings by masking secrets, tokens, passwords, and sensitive identifiers."""
        if not text or not isinstance(text, str):
            return text

        sanitized = text
        for pattern, replacement in SECRET_PATTERNS:
            sanitized = pattern.sub(replacement, sanitized)

        return sanitized

    @classmethod
    def redact_structure(cls, data: Any) -> Any:
        """Recursively traverses dictionaries, lists, and primitives, redacting sensitive keys and values."""
        if isinstance(data, dict):
            redacted_dict: Dict[str, Any] = {}
            for k, v in data.items():
                k_lower = str(k).lower().replace("_", "").replace("-", "")
                if any(sens in k_lower for sens in SENSITIVE_KEY_NAMES):
                    redacted_dict[k] = REDACTED_TEXT
                else:
                    redacted_dict[k] = cls.redact_structure(v)
            return redacted_dict
        elif isinstance(data, list):
            return [cls.redact_structure(item) for item in data]
        elif isinstance(data, str):
            return cls.redact_text(data)
        else:
            return data


redaction_service = RedactionService()

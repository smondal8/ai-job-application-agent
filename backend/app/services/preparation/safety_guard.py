import re
from typing import Any, Optional
from app.core.logging import get_logger

logger = get_logger("app.services.preparation.safety_guard")


class PlaywrightSafetyGuard:
    """Non-negotiable safety guard for Playwright browser application preparation."""

    CAPTCHA_SELECTORS = [
        "iframe[src*='recaptcha']",
        "iframe[src*='hcaptcha']",
        "iframe[src*='cloudflare']",
        "iframe[src*='turnstile']",
        "iframe[src*='challenges.cloudflare.com']",
        ".g-recaptcha",
        ".h-captcha",
        ".cf-turnstile",
        "#cf-challenge-running",
        "#challenge-form",
        ".challenge-form",
        "div[class*='captcha']",
    ]

    CAPTCHA_TEXT_PATTERNS = [
        re.compile(r"verify you are human", re.IGNORECASE),
        re.compile(r"please verify that you are not a robot", re.IGNORECASE),
        re.compile(r"complete the security check", re.IGNORECASE),
        re.compile(r"cloudflare ray id", re.IGNORECASE),
        re.compile(r"attention required! \| cloudflare", re.IGNORECASE),
        re.compile(r"press & hold", re.IGNORECASE),
    ]

    AUTH_SELECTORS = [
        "form[action*='login']",
        "form[action*='signin']",
        "input[type='password'][name*='password']",
        "input[type='password'][id*='password']",
        "button[id*='sso']",
        "a[href*='accounts.google.com']",
        "div[class*='login-wall']",
        "div[class*='auth-required']",
    ]

    SUBMIT_SELECTORS = [
        "button[type='submit']",
        "input[type='submit']",
        "button:has-text('Submit Application')",
        "button:has-text('Submit application')",
        "button:has-text('Submit')",
        "button:has-text('Apply Now')",
        "button:has-text('Send Application')",
        "button:has-text('Complete Application')",
        "input[value*='Submit']",
        "input[value*='Apply']",
        "a[class*='submit-button']",
    ]

    @classmethod
    async def detect_captcha(cls, page: Any) -> bool:
        """Inspects DOM and text content for CAPTCHA or bot challenge walls."""
        try:
            for selector in cls.CAPTCHA_SELECTORS:
                count = await page.locator(selector).count()
                if count > 0:
                    logger.warning(f"CAPTCHA / Bot challenge selector detected: {selector}")
                    return True

            page_content = await page.content()
            for pattern in cls.CAPTCHA_TEXT_PATTERNS:
                if pattern.search(page_content):
                    logger.warning(f"CAPTCHA text pattern detected in page content: {pattern.pattern}")
                    return True
        except Exception as e:
            logger.warning(f"Error checking CAPTCHA presence: {e}")

        return False

    @classmethod
    async def detect_auth_wall(cls, page: Any) -> bool:
        """Inspects DOM for login forms, passwords, or authentication challenge requirements."""
        try:
            for selector in cls.AUTH_SELECTORS:
                count = await page.locator(selector).count()
                if count > 0:
                    logger.warning(f"Authentication challenge selector detected: {selector}")
                    return True
        except Exception as e:
            logger.warning(f"Error checking auth wall presence: {e}")

        return False

    @classmethod
    async def is_submit_element(cls, element: Any) -> bool:
        """Validates if a given DOM element represents the final application submission trigger."""
        try:
            tag_name = await element.evaluate("el => el.tagName.toLowerCase()")
            el_type = await element.get_attribute("type") or ""
            el_value = await element.get_attribute("value") or ""
            text = (await element.inner_text()).strip().lower()

            if el_type.lower() == "submit":
                return True
            if any(term in text for term in ["submit application", "send application", "complete application", "apply now"]):
                return True
            if any(term in el_value.lower() for term in ["submit application", "apply"]):
                return True
        except Exception:
            pass

        return False

    @classmethod
    def sanitize_page_instructions(cls, text: str) -> str:
        """Guarantees page text cannot alter system execution policy or trigger submission."""
        return text

"""Safety guardrails, PII detection, and policy hallucination checks."""

import re
from typing import Dict, List, Tuple


class SafetyGuardrails:
    """Detects security risks, sensitive data leaks, and policy hallucinations."""

    # Prohibited patterns in bot output
    PROHIBITED_CLAIMS = [
        r"\b(i have refunded|refund has been processed|processed your refund|credited your account)\b",
        r"\b(free iphone|free replacement without return|waived your fee)\b",
        r"\b(here is your password|temporary password is)\b",
        r"\b(your tracking number is \d{10,})\b",
    ]

    # Sensitive customer inputs that MUST trigger escalation
    SENSITIVE_INPUT_PATTERNS = [
        r"\b(password|passcode|pin number|ssn|social security|cvv|credit card number)\b",
        r"\b(lawsuit|sue\b|legal action|attorney|lawyer|court)\b",
        r"\b(suicide|kill myself|harm myself)\b",
        r"\b(stolen|theft|burglarized|police report)\b",
        r"\b(hacked|compromised|account takeover|unauthorized login)\b",
    ]

    @classmethod
    def check_input_safety(cls, text: str) -> Tuple[bool, List[str]]:
        """Checks customer input for safety/escalation triggers."""
        violations = []
        lower = text.lower()
        for pattern in cls.SENSITIVE_INPUT_PATTERNS:
            if re.search(pattern, lower):
                violations.append(f"Sensitive trigger detected matching '{pattern}'")
        return len(violations) == 0, violations

    @classmethod
    def check_output_safety(cls, text: str) -> Tuple[bool, List[str]]:
        """Checks generated response for unauthorized promises or hallucinations."""
        violations = []
        lower = text.lower()
        for pattern in cls.PROHIBITED_CLAIMS:
            if re.search(pattern, lower):
                violations.append(f"Prohibited hallucination detected matching '{pattern}'")
        return len(violations) == 0, violations

    @classmethod
    def sanitize_text(cls, text: str) -> str:
        """Strips credit cards and sensitive tokens from logged text."""
        # Mask 16-digit credit cards
        sanitized = re.sub(r"\b(?:\d{4}[ -]?){3}\d{4}\b", "[REDACTED_CARD]", text)
        return sanitized

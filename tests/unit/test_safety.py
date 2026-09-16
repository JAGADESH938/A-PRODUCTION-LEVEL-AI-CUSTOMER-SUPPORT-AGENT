"""Unit tests for safety guardrails and sensitive input detection."""

import pytest
from src.safety.guardrails import SafetyGuardrails


def test_sensitive_input_triggers():
    is_safe, violations = SafetyGuardrails.check_input_safety("Here is my password: secret123")
    assert is_safe is False
    assert len(violations) > 0

    is_safe, violations = SafetyGuardrails.check_input_safety("I will sue your company in court")
    assert is_safe is False
    assert len(violations) > 0

    is_safe, violations = SafetyGuardrails.check_input_safety("How do I update my iPhone to iOS 11?")
    assert is_safe is True
    assert len(violations) == 0


def test_prohibited_output_claims():
    is_safe, violations = SafetyGuardrails.check_output_safety("I have refunded $50 to your account.")
    assert is_safe is False

    is_safe, violations = SafetyGuardrails.check_output_safety("Here is a free iPhone replacement without return.")
    assert is_safe is False

    is_safe, violations = SafetyGuardrails.check_output_safety("Please visit Settings > Battery to view usage.")
    assert is_safe is True


def test_credit_card_sanitization():
    raw = "My card number is 4111 2222 3333 4444 please charge it."
    sanitized = SafetyGuardrails.sanitize_text(raw)
    assert "4111" not in sanitized
    assert "[REDACTED_CARD]" in sanitized

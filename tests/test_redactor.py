"""
Tests for the PIIRedactor and the module-level redact_pii bridge.
"""

import scraper.redactor     # Module under test containing the PIIRedactor class and redact_pii function


def test_redact_pii_technical_tokens():
    text = "Contact email is test@example.com, mobile is 07700 900111. Health ID: 111 222 3333 and Ref: AA 11 22 33 B."
    result = scraper.redactor.redact_pii(text)

    assert "[EMAIL_REDACTED]" in result
    assert "[PHONE_REDACTED]" in result
    assert "[HEALTH_ID_REDACTED]" in result
    assert "[REF_NUM_REDACTED]" in result
    assert "test@example.com" not in result
    assert "07700 900111" not in result


def test_redact_pii_whitespace_normalisation():
    text = "CONFIDENTIAL:\xa0SOCIAL\nCARE\nCASE\nFILE\n-\nREF:\nSC-00000-X"
    result = scraper.redactor.redact_pii(text)
    assert "CONFIDENTIAL: SOCIAL CARE CASE FILE - REF: SC-00000-X" in result


def test_redact_pii_dynamic_name_sweep():
    text = "Subject: John Smith. Later on, John Smith reported that the care team was helpful."
    result = scraper.redactor.redact_pii(text)

    assert "John Smith" not in result
    assert "Subject: [NAME_REDACTED]." in result
    assert "Later on, [NAME_REDACTED] reported" in result


def test_redact_pii_edge_cases():
    text = "test@example.com is first string. Last string is 07700 900111"
    result = scraper.redactor.redact_pii(text)

    assert result.startswith("[EMAIL_REDACTED]"), "PII at start of string failed redaction."
    assert result.endswith("[PHONE_REDACTED]"), "PII at end of string failed redaction."


def test_redact_pii_no_pii_text_unchanged():
    text = "The council office opens at 9am on weekdays."
    result = scraper.redactor.redact_pii(text)
    assert result == text


def test_redact_pii_empty_string():
    assert scraper.redactor.redact_pii("") == ""


def test_redact_pii_none_input():
    # None should pass through safely (the implementation returns it as-is)
    assert scraper.redactor.redact_pii(None) is None


def test_redact_pii_dr_prefix():
    text = "Dr. Emily Chen will handle the case."
    result = scraper.redactor.redact_pii(text)
    assert "Emily Chen" not in result
    assert "[NAME_REDACTED]" in result


def test_redact_pii_coordinator_prefix():
    text = "Coordinator: Sarah Johnson will lead the meeting."
    result = scraper.redactor.redact_pii(text)
    assert "Sarah Johnson" not in result
    assert "[NAME_REDACTED]" in result


def test_redact_pii_multiple_emails():
    text = "Send to admin@council.gov.uk and support@salford.gov.uk for review."
    result = scraper.redactor.redact_pii(text)
    assert "admin@council.gov.uk" not in result
    assert "support@salford.gov.uk" not in result
    assert result.count("[EMAIL_REDACTED]") == 2


def test_module_level_bridge_is_callable():
    """The backward-compatibility redact_pii function at module level should work."""
    result = scraper.redactor.redact_pii("Call us at 07700 900222.")
    assert "[PHONE_REDACTED]" in result
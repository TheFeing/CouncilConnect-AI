import pytest
import scraper.redactor

def test_redaction_boundaries():
    """
    Rationale: Assures that fallback data protection functions handle edge text locations cleanly.
    """
    text = "jane.doe@private.com is first string. Last string is 07123456789"
    result = scraper.redactor.redact_pii(text)
    
    assert result.startswith("[EMAIL_REDACTED]"), "PII at start of string failed redaction."
    assert result.endswith("[PHONE_REDACTED]"), "PII at end of string failed redaction."
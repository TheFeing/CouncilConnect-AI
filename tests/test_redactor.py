import pytest
import scraper.redactor

def test_pii_redaction_and_preservation(): # Ensures public council details are kept but private PII is removed.

    raw_text = (
        "Contact me at private@gmail.com or 07712345678. "
        "Official: salford.direct@salford.gov.uk and 0161 793 2500."
    )
    result = scraper.redactor.redact_pii(raw_text)
    
    assert "[EMAIL_REDACTED]" in result, "Private email was not redacted."
    assert "[PHONE_REDACTED]" in result, "Private phone number was not redacted."
    
    assert "salford.direct@salford.gov.uk" in result, "Official council email incorrectly redacted."
    assert "0161 793 2500" in result, "Official council phone line incorrectly redacted."

def test_varied_formats_and_false_positives(): # Tests regex robustness against different spacing and numeric formats.

    text = "Intl: +44 7712 345 678. Short code: 01234. Non-email: user@domain"
    result = scraper.redactor.redact_pii(text)
    
    assert "[PHONE_REDACTED]" in result, "International mobile format failed redaction."
    assert "01234" in result, "Short numeric code was incorrectly flagged as PII."
    assert "user@domain" in result, "Incomplete email string was incorrectly flagged as PII."

def test_edge_cases(): # Verifies PII detection at string boundaries.

    text = "jane.doe@private.com is first string. Last string is 07123456789"
    result = scraper.redactor.redact_pii(text)
    
    assert result.startswith("[EMAIL_REDACTED]"), "PII at start of string failed redaction."
    assert result.endswith("[PHONE_REDACTED]"), "PII at end of string failed redaction."
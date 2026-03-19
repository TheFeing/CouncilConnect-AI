import pytest
from scraper.redactor import redact_pii1


def test_pii_redaction_and_preservation1():

    raw_text1 = (
        "Contact me at private@gmail.com or 07712345678. "
        "Official: salford.direct@salford.gov.uk and 0161 793 2500."
    )
    result1 = redact_pii1(raw_text1)

    assert "[EMAIL_REDACTED]" in result1, "Private email was not redacted."
    assert "[PHONE_REDACTED]" in result1, "Private phone number was not redacted."

    # Assertions for Preservation
    assert (
        "salford.direct@salford.gov.uk" in result1
    ), "Official council email was incorrectly redacted."
    assert (
        "0161 793 2500" in result1
    ), "Official council phone line was incorrectly redacted."


def test_varied_formats_and_false_positives1():

    text1 = "Intl: +44 7712 345 678. Short code: 01234. Non-email: user@domain"
    result1 = redact_pii1(text1)

    assert (
        "[PHONE_REDACTED]" in result1
    ), "International mobile format failed redaction."
    assert "01234" in result1, "Short numeric code was incorrectly flagged as PII."
    assert (
        "user@domain" in result1
    ), "Incomplete email string was incorrectly flagged as PII."


def test_edge_cases1():

    text1 = "jane.doe@private.com is first string. Last string is 07123456789"
    result1 = redact_pii1(text1)

    assert result1.startswith(
        "[EMAIL_REDACTED]"
    ), "PII at start of string failed redaction."
    assert result1.endswith(
        "[PHONE_REDACTED]"
    ), "PII at end of string failed redaction."
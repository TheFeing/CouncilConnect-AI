import re       # Regular expressions
import json     # JSON parsing
import os       # OS interfaces for file path management
import logging  # Telemetry infrastructure for pipeline observability

# Configure operational logging infrastructure for the redaction subsystem.
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_comprehensive_allow_list():
    """
    Loads official data exceptions from disk to establish PII preservation rules.
    Supports dual-path resolution for both containerised pipelines and local test environments.
    """
    # Define primary path (relative to this module file) and secondary path (relative to workspace root during testing)
    primary_path = os.path.join(os.path.dirname(__file__), "pii_allow_list.json")
    secondary_path = os.path.join(os.getcwd(), "scraper", "pii_allow_list.json")
    
    # Select the path that actually contains the target asset on the active host filesystem
    resolved_path = primary_path if os.path.exists(primary_path) else secondary_path
    
    try:
        logger.info(f"Loading comprehensive validation allow-list from path: {resolved_path}")
        with open(resolved_path, "r") as allow_file: # Open and read JSON file with auto-closing context manager
            data = json.load(allow_file)  # Parse JSON into a Python dictionary
            
            logger.info("Successfully populated memory cache with local council exception metrics.")
            return {
                "emails": set(e.lower() for e in data.get("emails", [])), 
                "phones": set(str(p).replace(" ", "") for p in data.get("phone_numbers", [])),
                "domains": set(d.lower() for d in data.get("domains", []))
            }
    except FileNotFoundError: # Built-in error channel
        logger.error(f"Critical configuration failure: PII allow-list asset missing. Looked at {primary_path} and {secondary_path}. Defaulting to empty baseline.")
        return {"emails": set(), "phones": set(), "domains": set()} # Fallback to empty sets if the config is missing
    except json.JSONDecodeError as parse_error:
        logger.error(f"Malformed structural syntax encountered in allow-list: {str(parse_error)}. Defaulting to empty baseline.")
        return {"emails": set(), "phones": set(), "domains": set()}


# Pre-load in global scope to avoid repeated disk I/O operations during large-scale ingestion (S12).
ALLOW_LIST = load_comprehensive_allow_list()


def redact_pii(text: str) -> str: # Inputs and returns a string
    """
    Scans ingested council content blocks and redacts unauthorised private personal data points.
    """
    # 1. Redact Emails: Match standard email patterns using a Raw string (r'...')
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    def email_replacer(match):
        email = match.group(0).lower()
        return email if email in ALLOW_LIST["emails"] else "[EMAIL_REDACTED]"
    text = re.sub(email_pattern, email_replacer, text) 

    # 2. Redact UK Phone Numbers: Match common mobile and landline formats
    # Hardened to capture solid continuous digits as well as normalised space sequences
    phone_pattern = r'(?:\+44\s?7\d{3}|\(?07\d{3}\)?|0\d{4}|\(?0161\)?)\s?\d{3,4}\s?\d{3,4}'
    def phone_replacer(match):
        clean_phone = match.group(0).replace(" ", "").replace("(", "").replace(")", "")
        return match.group(0) if clean_phone in ALLOW_LIST["phones"] else "[PHONE_REDACTED]"
    text = re.sub(phone_pattern, phone_replacer, text)

    return text
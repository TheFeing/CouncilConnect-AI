import re       # Regular expressions
import json     # JSON parsing
import os       # OS interfaces for file path management

def load_comprehensive_allow_list():

    # Construct the absolute path to the JSON file relative to this script
    path = os.path.join(os.path.dirname(__file__), "pii_allow_list.json") 
    try:
        with open(path, "r") as allow_file: # Open (open) & read ("r") JSON file with auto-closing (with), proper resource management
            data = json.load(allow_file)  # Parse JSON into a Python dictionary
            return {
                "emails": set(e.lower() for e in data.get("emails", [])), 
                "phones": set(p.replace(" ", "") for p in data.get("phone_numbers", [])),
                "domains": set(d.lower() for d in data.get("domains", []))
                # Future address expansion. Difficult task for regex, may need Spacy/NER model.
            }
    except FileNotFoundError: # Built-in error channel
        return {"emails": set(), "phones": set(), "domains": set()} # Fallback to empty sets if the config is missing

# Pre-load in global scope to avoid repeated disk I/O operations during large-scale ingestion (S12).
ALLOW_LIST = load_comprehensive_allow_list()

def redact_pii(text: str) -> str: # Inputs and returns a string
    
    # 1. Redact Emails: Match standard email patterns using a Raw string (r'...')
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    def email_replacer(match):
        email = match.group(0).lower()
        return email if email in ALLOW_LIST["emails"] else "[EMAIL_REDACTED]"
    text = re.sub(email_pattern, email_replacer, text) 

    # 2. Redact UK Phone Numbers: Match common mobile and landline formats (S10)
    # Includes support for international prefixes (+44) and internal spacing
    phone_pattern = r'(\+44\s?7\d{3}|\(?07\d{3}\)?|0\d{4})\s?\d{3}\s?\d{3}'
    def phone_replacer(match):
        clean_phone = match.group(0).replace(" ", "")
        return match.group(0) if clean_phone in ALLOW_LIST["phones"] else "[PHONE_REDACTED]"
    text = re.sub(phone_pattern, phone_replacer, text)

    return text
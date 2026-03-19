import re       # Regular expressions
import json     # JSON parsing
import os       # OS interfaces for file path management

def load_comprehensive_allow_list1():

    # Construct the absolute path to the JSON file relative to this script
    path1 = os.path.join(os.path.dirname(__file__), "pii_allow_list.json") # Dunder variable (__file__) gives the current script's path
    try:
        with open(path1, "r") as allow_file1: # Open (open) & read ("r") JSON file with auto-closing (with), proper resource management
            data1 = json.load(allow_file1) # Parse JSON into a Python dictionary
            return {
                "emails": set(e1.lower() for e1 in data1.get("emails", [])), # Fast lookups wit set(): Unordered, unique
                "phones": set(p1.replace(" ", "") for p1 in data1.get("phone_numbers", [])),
                "domains": set(d1.lower() for d1 in data1.get("domains", []))
                # Future address expansion. Difficult task for regex, may need Spacy/NER model.
                # "addresses": set(a1.lower() for a1 in data1.get("physical_addresses", []))
            }
    except FileNotFoundError: # Built-in error channel
        return {"emails": set(), "phones": set(), "domains": set()} # Fallback to empty sets if the config is missing

# Pre-load in global scope to avoid repeated disk I/O operations during large-scale ingestion (S12).
ALLOW_LIST1 = load_comprehensive_allow_list1()

def redact_pii1(text1: str) -> str: # Inputs and returns a string
   
     # 1. Redact Emails: Match standard email patterns using a Raw string (r'...')
    email_pattern1 = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    def email_replacer1(match1):
        email1 = match1.group(0).lower()
        return email1 if email1 in ALLOW_LIST1["emails"] else "[EMAIL_REDACTED]"
    text1 = re.sub(email_pattern1, email_replacer1, text1) # String substitution

    # 2. Redact UK Phone Numbers: Match common mobile and landline formats (S10)
    # Includes support for international prefixes (+44) and internal spacing
    phone_pattern1 = r'(\+44\s?7\d{3}|\(?07\d{3}\)?|0\d{4})\s?\d{3}\s?\d{3}'
    def phone_replacer1(match1):
        clean_phone1 = match1.group(0).replace(" ", "")
        return match1.group(0) if clean_phone1 in ALLOW_LIST1["phones"] else "[PHONE_REDACTED]"
    text1 = re.sub(phone_pattern1, phone_replacer1, text1)

    # def address_replacer1(match1):
    pass

    return text1
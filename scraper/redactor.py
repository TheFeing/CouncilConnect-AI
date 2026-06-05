import os           # Accessing system environment parameters natively
import re           # String cleaning via regex matching patterns
import logging      # Logging activity and errors

# After other imports
try:
    from app.telemetry import get_pii_redaction_counter
except ImportError:
    # Keyword lambda is used to create an anonymous function that takes no arguments and returns None when called.
    # lambda is a placeholder that returns None if telemetry is not available to avoid breaking the redaction logic when telemetry is not set up.
    get_pii_redaction_counter = lambda: None

# Configure operational logging infrastructure for the redaction subsystem.
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PIIRedactor:
    """
    Data hygiene utility engineered to scrub Personal Identifiable Information (PII).
    Addresses irregular spacing, non-breaking character boundaries, and multi-line artifacts
    by combining static structural patterns with dynamic entity tracking discovery.
    """

    def __init__(self):
        # Flexible pattern layouts supporting irregular whitespace distributions natively
        
        # Email: Matches standard structures even if nested among lingering spaces
        self.email_regex = re.compile(r'[\w\.-]+@[\w\.-]+\.\w+')
        
        # UK Mobile/Landline: Accounts for variable grouping gaps (e.g., 07700  900111 or 07700900111)
        self.phone_regex = re.compile(r'(?:0|\+44)\s*\d{2,5}\s*\d{3,5}\s*\d{3,6}')
        
        # Health Identifier: Matches 10-digit spaced structures (e.g., 111 222 3333)
        self.health_id_regex = re.compile(r'\b\d{3}\s*\d{3}\s*\d{4}\b')
        
        # Reference Number: Matches National Insurance style structural profiles (e.g., AA 11 22 33 B)
        self.ref_num_regex = re.compile(r'\b[A-Z]{2}\s*\d{2}\s*\d{2}\s*\d{2}\s*[A-Z]\b', re.IGNORECASE)

    def _normalise_whitespace(self, text):
        """
        Sanitises structural text anomalies by expanding non-breaking tokens,
        collapsing redundant vertical breaks, and realigning staggered word arrays.
        """
        if not text:
            return ""
        # Convert non-breaking space variants to standard functional spaces
        text = text.replace('\xa0', ' ')
        # Collapse multi-line layout steps into linear strings to capture fragmented fields
        text = re.sub(r'\s*\n\s*', ' ', text)
        # Compress multi-space sequences down to uniform singular spaces
        return re.sub(r' +', ' ', text)

    def redact_pii(self, text):
        """
        Executes multi-stage redaction sequences across normalised inputs.
        Discovers entity values dynamically on the first pass to scrub loose mentions later.
        """
        if not text:
            return text

        # Step 1: Normalise layout structure to resolve space-evasion issues
        cleaned_text = self._normalise_whitespace(text)
        
        # Step 2: Redact absolute technical tokens
        cleaned_text = self.email_regex.sub('[EMAIL_REDACTED]', cleaned_text)
        cleaned_text = self.phone_regex.sub('[PHONE_REDACTED]', cleaned_text)
        cleaned_text = self.health_id_regex.sub('[HEALTH_ID_REDACTED]', cleaned_text)
        cleaned_text = self.ref_num_regex.sub('[REF_NUM_REDACTED]', cleaned_text)

        # Step 3: Contextual keyword discovery pass for names
        # Captures target strings via capture groups to seed the dynamic extraction cache
        context_patterns = [
            (r'(Subject:\s*)([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)', r'\1[NAME_REDACTED]'),
            (r'(Coordinator:\s*)([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)', r'\1[NAME_REDACTED]'),
            (r'(Kin Contact:\s*)([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)', r'\1[NAME_REDACTED]'),
            (r'(Dr\.\s*)([A-Z][a-z]+)', r'\1[NAME_REDACTED]')
        ]

        discovered_names = set()

        for pattern, replacement in context_patterns:
            # Search for name string patterns before swapping them out
            for match in re.finditer(pattern, cleaned_text):
                # Group 2 isolates the literal text string containing the discovered name
                name_str = match.group(2).strip()
                if name_str:
                    discovered_names.add(name_str)
            
            # Execute standard contextual replacement
            cleaned_text = re.sub(pattern, replacement, cleaned_text)

        # Step 4: Dynamic global matching pass
        # Sweeps up unstructured references to names discovered in Step 3
        if discovered_names:
            logger.info(f"Dynamic tracking engine discovered identity tokens for global erasure: {discovered_names}")
            for name in discovered_names:
                # Use a word-boundary pattern to avoid matching partial strings inside larger words
                escaped_name = re.escape(name)
                global_name_regex = re.compile(rf'\b{escaped_name}\b')
                cleaned_text = global_name_regex.sub('[NAME_REDACTED]', cleaned_text)

        # Step 5: Increment telemetry counter for redactions performed (if telemetry is available)
        pii_redaction_counter = get_pii_redaction_counter()
        if pii_redaction_counter is not None:
            pii_redaction_counter.add(1)

        return cleaned_text


# --- BACKWARD COMPATIBILITY BRIDGE ---
"""
Instantiate a module-level singleton instance to match the legacy functional interface hook 
accessed by main pipeline controllers (scraper.redactor.redact_pii) without breaking object layouts.
"""
_global_redactor_instance = PIIRedactor()
redact_pii = _global_redactor_instance.redact_pii
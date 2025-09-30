
from typing import Tuple
import re

# Try presidio first
try:
    from presidio_analyzer import AnalyzerEngine
    from presidio_anonymizer import AnonymizerEngine, AnonymizerRequest
    PRESIDIO_AVAILABLE = True
except Exception:
    PRESIDIO_AVAILABLE = False

# Fallback to spaCy
try:
    import spacy
    SPACY_AVAILABLE = True
    nlp = spacy.load("en_core_web_sm")
except Exception:
    SPACY_AVAILABLE = False
    nlp = None

def mask_pii(text: str) -> Tuple[str, int]:
    """
    Mask PII and return (masked_text, entity_count).
    Uses Presidio if installed, otherwise uses spaCy + regex.
    """
    if not text:
        return "", 0

    if PRESIDIO_AVAILABLE:
        analyzer = AnalyzerEngine()
        anonymizer = AnonymizerEngine()

        results = analyzer.analyze(text=text, language="en")
        if not results:
            # still mask emails/phones via regex
            masked = re.sub(r"\b[\w\.-]+@[\w\.-]+\.\w+\b", "[EMAIL]", text)
            masked = re.sub(r"\b\d{10}\b", "[PHONE]", masked)
            return masked, 0

        # anonymize using default anonymizers (replace with tag)
        anonymized = anonymizer.anonymize(text=text, analyzer_results=results)
        return anonymized.text, len(results)

    # PRESIDIO not available, fallback
    masked_text = text
    entity_count = 0
    if SPACY_AVAILABLE and nlp is not None:
        doc = nlp(text)
        for ent in doc.ents:
            
            if ent.label_ in ("PERSON",):
                masked_text = masked_text.replace(ent.text, "[NAME]")
                entity_count += 1

    # always mask emails and phone patterns
    emails_found = re.findall(r"\b[\w\.-]+@[\w\.-]+\.\w+\b", masked_text)
    phones_found = re.findall(r"\b\d{10}\b", masked_text)
    entity_count += len(emails_found) + len(phones_found)

    masked_text = re.sub(r"\b[\w\.-]+@[\w\.-]+\.\w+\b", "[EMAIL]", masked_text)
    masked_text = re.sub(r"\b\d{10}\b", "[PHONE]", masked_text)

    return masked_text, entity_count

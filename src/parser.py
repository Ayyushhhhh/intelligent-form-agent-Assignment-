# src/parser.py
import io
import pdfplumber
from typing import List, Dict

def extract_text(file_bytes: bytes) -> Dict:
    """
    Extract text and per-page text from PDF bytes.
    Returns a dict { "full_text": str, "pages": [str, ...] }.
    """
    pages = []
    full = []
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            try:
                text = page.extract_text() or ""
            except Exception:
                text = ""
            pages.append(text)
            full.append(text)
    return {"full_text": "\n".join(full).strip(), "pages": pages}

# src/summarizer.py
from transformers import pipeline
from typing import List

# pick a smaller summarizer for deployability
SUMMARIZER_MODEL = "sshleifer/distilbart-cnn-12-6"
summarizer_pipeline = pipeline("summarization", model=SUMMARIZER_MODEL, device=-1)

def chunk_text(text: str, max_chars: int = 1200) -> List[str]:
    chunks = []
    start = 0
    length = len(text)
    while start < length:
        end = start + max_chars
        # try to break at newline or sentence end for readability
        if end < length:
            # backtrack to last newline or dot within window
            last_newline = text.rfind("\n", start, end)
            last_dot = text.rfind(".", start, end)
            cut = max(last_newline, last_dot)
            if cut > start:
                end = cut + 1
        chunks.append(text[start:end].strip())
        start = end
    return [c for c in chunks if c]

def summarize_text(text: str) -> str:
    if not text:
        return ""
    chunks = chunk_text(text, max_chars=1200)
    summaries = []
    for chunk in chunks:
        try:
            out = summarizer_pipeline(chunk, max_length=200, min_length=60, do_sample=False)
            summaries.append(out[0]["summary_text"])
        except Exception:
            # fallback: if model fails, append the chunk's first 400 chars
            summaries.append(chunk[:400])
    # join with double newline to separate chunk summaries
    return "\n\n".join(summaries)

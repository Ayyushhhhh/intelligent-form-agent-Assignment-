
import time
import uuid
import io
import sys
from pathlib import Path

from fastapi import FastAPI, UploadFile, Form, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .parser import extract_text
from .anonymizer import mask_pii
from .summarizer import summarize_text
from .rag import build_index, load_index
from .qa_engine import answer_question

# === Directories ===
APP_DIR = Path(__file__).parent
STATIC_DIR = APP_DIR / "static"
VECTOR_STORE_DIR = Path(__file__).parent.parent / "vector_store"
VECTOR_STORE_DIR.mkdir(exist_ok=True)

# === FastAPI app ===
app = FastAPI(title="FormMind AI — Intelligent Form Agent")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
async def serve_index():
    return FileResponse(STATIC_DIR / "index.html")


# === Utility: Normalize extract_text output ===
def normalize_doc(raw, filename="unknown.pdf", pages=1):
    """Ensure we always return dicts with 'text' + metadata."""
    if isinstance(raw, dict):
        if "text" in raw:
            text = raw["text"]
        elif "full_text" in raw:
            text = raw["full_text"]
        else:
            text = str(raw)
    elif isinstance(raw, str):
        text = raw
    else:
        text = str(raw)

    return {
        "id": str(uuid.uuid4()),
        "text": text,
        "meta": {"filename": filename, "pages": pages},
    }


# --- Single Form Processing ---
@app.post("/process")
async def process_form(file: UploadFile, question: str = Form(None)):
    start = time.time()
    try:
        content = await file.read()
        parsed = extract_text(content)
        pages = len(parsed.get("pages", []))
        doc = normalize_doc(parsed, filename=file.filename, pages=pages)

        # anonymize only for display
        masked_text, entity_count = mask_pii(doc["text"])

        # summarise original text
        summary = summarize_text(doc["text"])

        # load + update vectorstore
        index, docs = load_index()
        docs.append(doc)
        index, docs = build_index(docs, rebuild=True)

        # optional Q&A
        answer = None
        if question:
            answer = answer_question(question, (index, docs), top_k=3)

        processing_time_ms = int((time.time() - start) * 1000)

        return JSONResponse({
            "text": masked_text,
            "summary": summary,
            "answer": answer,
            "stats": {
                "processing_time_ms": processing_time_ms,
                "doc_count": len(docs),
                "entity_count": entity_count
            }
        })
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


# --- Multi-Form Processing ---
@app.post("/process_multi")
async def process_multi_form(files: list[UploadFile], question: str = Form(None)):
    start = time.time()
    try:
        docs, texts = [], []
        total_entities = 0

        for f in files:
            content = await f.read()
            parsed = extract_text(content)
            pages = len(parsed.get("pages", []))
            doc = normalize_doc(parsed, filename=f.filename, pages=pages)

            masked_text, entity_count = mask_pii(doc["text"])
            total_entities += entity_count

            docs.append(doc)
            texts.append(doc["text"])

        # Build index for all uploaded docs
        index, docs = build_index(docs, rebuild=True)

        # Generate merged summary
        merged_summary = summarize_text(" ".join(texts))

        # Optional Q&A
        answer = None
        if question:
            answer = answer_question(question, (index, docs), top_k=3)

        processing_time_ms = int((time.time() - start) * 1000)

        return JSONResponse({
            "text": f"Processed {len(files)} documents successfully.",
            "summary": merged_summary,
            "answer": answer,
            "stats": {
                "processing_time_ms": processing_time_ms,
                "doc_count": len(docs),
                "entity_count": total_entities
            }
        })
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


# --- Demo Launcher ---
@app.post("/run_demo")
async def run_demo(background_tasks: BackgroundTasks):
    from demo import demo_single_qa, demo_entity_masking, demo_multi_form

    buffer = io.StringIO()
    sys_stdout = sys.stdout
    sys.stdout = buffer

    try:
        print("=== 🚀 Running Prebuilt Demo ===")
        demo_single_qa()
        demo_entity_masking()
        demo_multi_form()
        print("=== ✅ Demo Finished ===")
    finally:
        sys.stdout = sys_stdout

    output = buffer.getvalue()
    return {"demo_output": output}

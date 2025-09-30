# src/qa_engine.py
from transformers import pipeline
from .rag import similarity_search, load_index
from typing import Optional

# choose flan-t5-base or flan-t5-small for smaller footprint
QA_MODEL = "google/flan-t5-base"
qa_generator = pipeline("text2text-generation", model=QA_MODEL, device=-1)

def answer_question(question: str, index_data: Optional[tuple], top_k: int = 3) -> str:
    """
    RAG-style answer. index_data is (index, docs) from rag.load_index() or build_index()
    """
    if not question:
        return ""

    index, docs = index_data
    # if no index, fall back to returning helpful fallback
    if index is None or not docs:
        # just return instruction to upload docs
        return "No documents indexed. Upload a form first."

    # retrieve top-k documents
    context_docs = similarity_search(index, docs, question, k=top_k)
    # join contexts with separators
    contexts = "\n\n".join([f"Document: {d.get('meta', {}).get('filename','unknown')}\n{d['text'][:1500]}" for d in context_docs])
    prompt = f"Answer the question using the context below. If the answer is not present, say 'Not found in documents.'\n\nContext:\n{contexts}\n\nQuestion: {question}\nAnswer:"
    out = qa_generator(prompt, max_length=256, do_sample=False)
    return out[0]["generated_text"].strip()

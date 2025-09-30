# src/rag.py
import os
import pickle
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss
from pathlib import Path
from typing import List, Dict, Tuple

VECTOR_DIR = Path(__file__).parent.parent / "vector_store"
VECTOR_DIR.mkdir(exist_ok=True)

EMBED_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
embedder = SentenceTransformer(EMBED_MODEL_NAME)

INDEX_FILE = VECTOR_DIR / "faiss.index"
TEXTS_FILE = VECTOR_DIR / "texts.pkl"

def build_index(docs: List[Dict], rebuild: bool = True) -> Tuple[faiss.Index, List[Dict]]:
    """
    Build or update FAISS index from docs.
    docs: list of {'id': str, 'text': str, 'meta': {...}}
    If rebuild True, recreate index from provided docs and persist.
    Returns (index, docs)
    """
    texts = [d["text"] for d in docs]
    embeddings = embedder.encode(texts, convert_to_numpy=True)
    dim = embeddings.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(np.array(embeddings).astype("float32"))

    # persist
    faiss.write_index(index, str(INDEX_FILE))
    with open(TEXTS_FILE, "wb") as f:
        pickle.dump(docs, f)
    return index, docs

def load_index() -> Tuple:
    if INDEX_FILE.exists() and TEXTS_FILE.exists():
        index = faiss.read_index(str(INDEX_FILE))
        with open(TEXTS_FILE, "rb") as f:
            docs = pickle.load(f)
        return index, docs
    return None, []

def similarity_search(index: faiss.Index, docs: List[Dict], query: str, k: int = 3) -> List[Dict]:
    """
    Return top-k docs for the query
    """
    q_emb = embedder.encode([query], convert_to_numpy=True).astype("float32")
    D, I = index.search(q_emb, k)
    results = []
    for idx in I[0]:
        if idx < 0 or idx >= len(docs):
            continue
        results.append(docs[idx])
    return results

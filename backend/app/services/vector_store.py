"""
FAISS-based vector store for RAG retrieval.
Persists index to disk for durability across restarts.
"""
import os
import json
import logging
import numpy as np
from pathlib import Path

logger = logging.getLogger(__name__)

# In-memory store: {document_id: {chunks: [...], index: faiss.Index}}
_stores: dict = {}


def _get_faiss():
    import faiss
    return faiss


def add_document_chunks(document_id: str, chunks: list[dict], embeddings: list[list[float]], index_dir: str):
    """
    Add chunks and their embeddings to the FAISS index for a document.
    chunks: list of {content, token_count, chunk_index}
    embeddings: parallel list of embedding vectors
    """
    faiss = _get_faiss()
    if not embeddings:
        logger.warning(f"No embeddings provided for document {document_id}")
        return

    dim = len(embeddings[0])
    index = faiss.IndexFlatL2(dim)
    vectors = np.array(embeddings, dtype=np.float32)
    index.add(vectors)

    _stores[document_id] = {
        "index": index,
        "chunks": chunks,
        "dim": dim,
    }

    # Persist to disk
    _persist(document_id, index, chunks, dim, index_dir)
    logger.info(f"FAISS: added {len(chunks)} chunks for document {document_id}")


def retrieve_top_k(document_id: str, query_embedding: list[float], k: int = 5, index_dir: str = "./faiss_index") -> list[str]:
    """
    Retrieve top-k most similar chunks for a query embedding.
    Returns list of chunk content strings.
    """
    faiss = _get_faiss()
    store = _stores.get(document_id)
    if store is None:
        store = _load(document_id, index_dir)
        if store is None:
            logger.warning(f"No FAISS index found for document {document_id}")
            return []

    index = store["index"]
    chunks = store["chunks"]
    q = np.array([query_embedding], dtype=np.float32)
    k = min(k, index.ntotal)
    distances, indices = index.search(q, k)
    results = []
    for idx in indices[0]:
        if 0 <= idx < len(chunks):
            results.append(chunks[idx]["content"])
    return results


def delete_document_index(document_id: str, index_dir: str):
    """Remove FAISS index and metadata for a document."""
    _stores.pop(document_id, None)
    doc_dir = Path(index_dir) / document_id
    if doc_dir.exists():
        import shutil
        shutil.rmtree(doc_dir)


def _persist(document_id: str, index, chunks: list[dict], dim: int, index_dir: str):
    import faiss
    doc_dir = Path(index_dir) / document_id
    doc_dir.mkdir(parents=True, exist_ok=True)
    faiss.write_index(index, str(doc_dir / "index.faiss"))
    with open(doc_dir / "chunks.json", "w") as f:
        json.dump({"chunks": chunks, "dim": dim}, f)


def _load(document_id: str, index_dir: str) -> dict | None:
    import faiss
    doc_dir = Path(index_dir) / document_id
    index_path = doc_dir / "index.faiss"
    chunks_path = doc_dir / "chunks.json"
    if not index_path.exists() or not chunks_path.exists():
        return None
    index = faiss.read_index(str(index_path))
    with open(chunks_path) as f:
        meta = json.load(f)
    store = {"index": index, "chunks": meta["chunks"], "dim": meta["dim"]}
    _stores[document_id] = store
    return store

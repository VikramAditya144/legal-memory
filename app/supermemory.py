"""
Supermemory integration layer.

Mirrors chunks into Supermemory alongside Qdrant so lawyers get two
complementary retrieval engines: Qdrant (local vector similarity) and
Supermemory (cloud semantic search with reranking + query rewriting).

Container tag convention:
  - PDFs       → "legal-pdf"
  - WhatsApp   → "legal-whatsapp"
"""

from __future__ import annotations

import os
from functools import lru_cache

_CONTAINER_PDF = "legal-pdf"
_CONTAINER_WHATSAPP = "legal-whatsapp"


@lru_cache(maxsize=1)
def _get_client():
    try:
        from supermemory import Supermemory
    except ImportError:
        return None
    api_key = os.getenv("SUPERMEMORY_API_KEY", "")
    if not api_key:
        return None
    return Supermemory(api_key=api_key)


def is_available() -> bool:
    return _get_client() is not None


def add_chunks(chunks: list[dict]) -> int:
    """
    Push a list of ingested chunks to Supermemory.

    Each chunk must have "text" and "metadata" keys (same shape as
    produced by chunk_pdf / chunk_messages).  Returns count stored.
    Falls back silently if Supermemory is unavailable.
    """
    client = _get_client()
    if client is None:
        return 0

    stored = 0
    for chunk in chunks:
        meta = chunk.get("metadata", {})
        source_type = meta.get("source_type", "pdf")
        container = _CONTAINER_WHATSAPP if source_type == "whatsapp" else _CONTAINER_PDF

        # Build flat metadata (Supermemory requires str/float/bool values)
        sm_meta: dict = {
            "source_name": str(meta.get("source_name", "")),
            "source_type": source_type,
        }
        if meta.get("pages"):
            sm_meta["pages"] = str(meta["pages"])
        if meta.get("start_time"):
            sm_meta["start_time"] = str(meta["start_time"])
        if meta.get("senders"):
            sm_meta["senders"] = str(meta["senders"])

        try:
            client.documents.add(
                content=chunk["text"],
                container_tag=container,
                metadata=sm_meta,
                task_type="superrag",
            )
            stored += 1
        except Exception:
            pass

    return stored


def search(query: str, top_k: int = 5) -> list[dict]:
    """
    Search Supermemory and return results in the same shape as store.search().

    Falls back to [] if Supermemory is unavailable.
    """
    client = _get_client()
    if client is None:
        return []

    try:
        response = client.search.documents(
            q=query,
            container_tags=[_CONTAINER_PDF, _CONTAINER_WHATSAPP],
            limit=top_k,
            rerank=True,
            rewrite_query=True,
            chunk_threshold=0.3,
        )
    except Exception:
        return []

    results = []
    for doc in getattr(response, "results", []):
        # Each result may have multiple chunks; use the top chunk
        chunks = getattr(doc, "chunks", [])
        text = chunks[0].content if chunks else getattr(doc, "content", "")
        score = getattr(chunks[0], "score", 0.0) if chunks else 0.0
        metadata = getattr(doc, "metadata", {}) or {}

        results.append({
            "score": round(float(score), 3),
            "text": text or "",
            "source_type": metadata.get("source_type", ""),
            "source_name": metadata.get("source_name", ""),
            "start_time": metadata.get("start_time", ""),
            "pages": metadata.get("pages", ""),
            "senders": metadata.get("senders", ""),
        })

    return results

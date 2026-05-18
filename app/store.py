"""
Qdrant storage layer.

Manages a single collection that holds all ingested chunks.
Each point stores: embedding vector + payload (text + metadata).
"""

import os
import uuid

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    PointStruct,
    VectorParams,
)

from app.embeddings import EMBEDDING_DIMENSIONS

_DEFAULT_COLLECTION = "legal_memory"


def get_client() -> QdrantClient:
    host = os.getenv("QDRANT_HOST", "localhost")
    port = int(os.getenv("QDRANT_PORT", "6333"))
    return QdrantClient(host=host, port=port, timeout=30)


def ensure_collection(client: QdrantClient, collection: str = _DEFAULT_COLLECTION) -> None:
    existing = {c.name for c in client.get_collections().collections}
    if collection not in existing:
        client.create_collection(
            collection_name=collection,
            vectors_config=VectorParams(
                size=EMBEDDING_DIMENSIONS,
                distance=Distance.COSINE,
            ),
        )


def upsert_chunks(
    chunks: list[dict],
    embeddings: list[list[float]],
    client: QdrantClient,
    collection: str = _DEFAULT_COLLECTION,
) -> int:
    """
    Insert chunks with their embeddings into Qdrant.

    Returns the number of points inserted.
    """
    ensure_collection(client, collection)

    points = []
    for chunk, vector in zip(chunks, embeddings):
        payload = {
            "text": chunk["text"],
            **chunk["metadata"],
        }
        # Convert list fields to strings for Qdrant payload compatibility
        if "senders" in payload and isinstance(payload["senders"], list):
            payload["senders"] = ", ".join(payload["senders"])
        if "pages" in payload and isinstance(payload["pages"], list):
            payload["pages"] = ", ".join(str(p) for p in payload["pages"])

        points.append(PointStruct(
            id=str(uuid.uuid4()),
            vector=vector,
            payload=payload,
        ))

    if points:
        client.upsert(collection_name=collection, points=points)

    return len(points)


def search(
    query_vector: list[float],
    client: QdrantClient,
    collection: str = _DEFAULT_COLLECTION,
    top_k: int = 5,
    source_filter: str | None = None,
) -> list[dict]:
    """
    Semantic search. Returns top_k results as dicts with text + metadata + score.
    """
    ensure_collection(client, collection)

    from qdrant_client.models import Filter, FieldCondition, MatchValue

    query_filter = None
    if source_filter:
        query_filter = Filter(
            must=[FieldCondition(key="source_name", match=MatchValue(value=source_filter))]
        )

    hits = client.search(
        collection_name=collection,
        query_vector=query_vector,
        limit=top_k,
        query_filter=query_filter,
        with_payload=True,
    )

    results = []
    for hit in hits:
        results.append({
            "score": round(hit.score, 3),
            "text": hit.payload.get("text", ""),
            "source_type": hit.payload.get("source_type", ""),
            "source_name": hit.payload.get("source_name", ""),
            "start_time": hit.payload.get("start_time", ""),
            "pages": hit.payload.get("pages", ""),
            "senders": hit.payload.get("senders", ""),
        })

    return results


def collection_stats(
    client: QdrantClient,
    collection: str = _DEFAULT_COLLECTION,
) -> dict:
    """Return point count and indexed source names."""
    try:
        ensure_collection(client, collection)
        info = client.get_collection(collection)
        count = info.points_count or 0

        # Scroll to collect distinct source names (sample first 1000 points)
        records, _ = client.scroll(
            collection_name=collection,
            limit=1000,
            with_payload=["source_name", "source_type"],
        )
        sources: dict[str, set] = {"pdf": set(), "whatsapp": set()}
        for rec in records:
            stype = rec.payload.get("source_type", "other")
            sname = rec.payload.get("source_name", "unknown")
            sources.setdefault(stype, set()).add(sname)

        return {
            "total_chunks": count,
            "pdf_sources": sorted(sources.get("pdf", set())),
            "whatsapp_sources": sorted(sources.get("whatsapp", set())),
        }
    except Exception:
        return {"total_chunks": 0, "pdf_sources": [], "whatsapp_sources": []}

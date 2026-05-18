"""
Embedding layer using OpenAI text-embedding-3-small.

Batches requests to stay within API limits and handles retries.
"""

import os
import time

from openai import OpenAI

_MODEL = "text-embedding-3-small"
_BATCH_SIZE = 100  # OpenAI allows up to 2048 inputs per request; 100 is safe
_DIMENSIONS = 1536  # text-embedding-3-small output size


def get_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not set in environment")
    return OpenAI(api_key=api_key)


def embed_texts(texts: list[str], client: OpenAI | None = None) -> list[list[float]]:
    """
    Return embeddings for a list of texts.

    Batches into groups of _BATCH_SIZE and retries once on rate-limit errors.
    """
    if client is None:
        client = get_client()

    all_embeddings: list[list[float]] = []

    for i in range(0, len(texts), _BATCH_SIZE):
        batch = texts[i : i + _BATCH_SIZE]
        # Clean: replace empty strings with a single space (API rejects empty input)
        batch = [t if t.strip() else " " for t in batch]

        for attempt in range(2):
            try:
                response = client.embeddings.create(model=_MODEL, input=batch)
                batch_embeddings = [item.embedding for item in sorted(response.data, key=lambda x: x.index)]
                all_embeddings.extend(batch_embeddings)
                break
            except Exception as e:
                if attempt == 0 and "rate" in str(e).lower():
                    time.sleep(5)
                    continue
                raise

    return all_embeddings


EMBEDDING_DIMENSIONS = _DIMENSIONS

"""
Embedding layer using fastembed with paraphrase-multilingual-mpnet-base-v2.

Local model — no API key required. Supports English, Hindi, and 50+ other
languages. 768-dimensional output vectors.
"""

from __future__ import annotations

import warnings
from functools import lru_cache

# Suppress fastembed pooling migration warning — we're fine with mean pooling
warnings.filterwarnings("ignore", category=UserWarning, module="fastembed")

_MODEL_NAME = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
EMBEDDING_DIMENSIONS = 768


@lru_cache(maxsize=1)
def _get_model():
    from fastembed import TextEmbedding
    return TextEmbedding(_MODEL_NAME)


def embed_texts(texts: list[str], **_kwargs) -> list[list[float]]:
    """
    Return embeddings for a list of texts using the local multilingual model.

    The **_kwargs signature is kept for drop-in compatibility with callers
    that pass an openai client argument.
    """
    model = _get_model()
    # Replace empty strings — model may produce degenerate vectors for them
    cleaned = [t if t.strip() else "empty" for t in texts]
    return [vec.tolist() for vec in model.embed(cleaned)]

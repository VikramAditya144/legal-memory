"""
PDF ingestion pipeline.

Extracts text page-by-page using pdfplumber, then chunks into
~500-token segments with 50-token overlap using a simple word-count
approximation (1 token ≈ 0.75 words).
"""

from pathlib import Path

import pdfplumber

_TARGET_TOKENS = 500
_OVERLAP_TOKENS = 50
_WORDS_PER_TOKEN = 0.75  # rough approximation


def _word_count_to_tokens(words: int) -> int:
    return int(words / _WORDS_PER_TOKEN)


def _tokens_to_words(tokens: int) -> int:
    return int(tokens * _WORDS_PER_TOKEN)


TARGET_WORDS = _tokens_to_words(_TARGET_TOKENS)
OVERLAP_WORDS = _tokens_to_words(_OVERLAP_TOKENS)


def extract_pages(path: str | Path) -> list[dict]:
    """Return list of {page_num, text} dicts from a PDF."""
    path = Path(path)
    pages = []
    with pdfplumber.open(path) as pdf:
        for i, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""
            text = text.strip()
            if text:
                pages.append({"page_num": i, "text": text})
    return pages


def chunk_pdf(path: str | Path) -> list[dict]:
    """
    Extract and chunk a PDF into overlapping word-window segments.

    Returns list of dicts: {text, metadata}.
    """
    path = Path(path)
    pages = extract_pages(path)

    # Flatten all words with their page origin
    word_entries: list[tuple[str, int]] = []
    for page in pages:
        for word in page["text"].split():
            word_entries.append((word, page["page_num"]))

    if not word_entries:
        return []

    chunks = []
    step = max(1, TARGET_WORDS - OVERLAP_WORDS)
    total = len(word_entries)

    for start in range(0, total, step):
        end = min(start + TARGET_WORDS, total)
        batch = word_entries[start:end]

        text = " ".join(w for w, _ in batch)
        pages_covered = sorted({p for _, p in batch})

        chunks.append({
            "text": text,
            "metadata": {
                "source_type": "pdf",
                "source_name": path.name,
                "pages": pages_covered,
                "chunk_index": len(chunks),
                "total_words": len(batch),
            },
        })

        if end == total:
            break

    return chunks

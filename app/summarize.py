"""
Claude-powered one-sentence summaries for search results.

Uses claude-haiku-4-5 for speed and cost efficiency. Falls back to
the raw excerpt if the API key is missing or the call fails.
"""

from __future__ import annotations

import os
from functools import lru_cache

_MODEL = "claude-haiku-4-5-20251001"
_MAX_TOKENS = 120


@lru_cache(maxsize=1)
def _get_client():
    import anthropic
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key:
        return None
    return anthropic.Anthropic(api_key=api_key)


def summarize_result(query: str, result_text: str) -> str:
    """
    Return a one-sentence summary of result_text in the context of query.

    Returns empty string if Claude is unavailable — caller shows raw excerpt.
    """
    client = _get_client()
    if client is None:
        return ""

    prompt = (
        f"A lawyer searched for: \"{query}\"\n\n"
        f"Retrieved document excerpt:\n{result_text[:1200]}\n\n"
        "In ONE sentence, explain what this excerpt contains and why it is "
        "relevant to the search. Be specific — mention clause types, party "
        "names, or dates if present. Do not start with 'This excerpt'."
    )

    try:
        response = client.messages.create(
            model=_MODEL,
            max_tokens=_MAX_TOKENS,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text.strip()
    except Exception:
        return ""


def summarize_results_batch(query: str, results: list[dict]) -> list[str]:
    """Summarize multiple results. Returns list of summary strings (may be empty)."""
    return [summarize_result(query, r["text"]) for r in results]

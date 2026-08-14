"""Thin embedding-provider wrapper (spec §7.4: one configured provider,
no orchestration framework for this few call sites). Voyage AI today —
swapping providers later means changing this module only, callers are
unaffected.
"""

import math

import voyageai

from app.config import settings

_client: voyageai.Client | None = None


def _get_client() -> voyageai.Client:
    global _client
    if _client is None:
        _client = voyageai.Client(api_key=settings.voyage_api_key)
    return _client


def embed_documents(texts: list[str]) -> list[list[float]]:
    """Embeds job/resume text (input_type="document") in batches of <=128."""
    if not texts:
        return []
    client = _get_client()
    result = client.embed(texts, model=settings.embedding_model, input_type="document")
    return result.embeddings


def embed_query(text: str) -> list[float]:
    """Embeds a query-side text (e.g. a candidate profile) for similarity search."""
    client = _get_client()
    result = client.embed([text], model=settings.embedding_model, input_type="query")
    return result.embeddings[0]


def cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)

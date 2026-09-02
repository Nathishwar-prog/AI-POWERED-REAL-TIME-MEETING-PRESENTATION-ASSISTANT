"""Query-time retrieval: embed a question and pull the best document chunks.

The :class:`Retriever` ties an :class:`~app.rag.embeddings.Embedder` to a
:class:`~app.rag.vector_store.VectorStore` and applies the relevance floor
(``settings.min_score``) so that a question the document does not cover simply
returns nothing instead of forcing an irrelevant "match".
"""

from __future__ import annotations

from app.config import settings
from app.models import RetrievedChunk
from app.rag.embeddings import Embedder
from app.rag.vector_store import VectorStore


class Retriever:
    """Retrieves relevant chunks for a natural-language query.

    Args:
        store: The populated vector store to search.
        embedder: Embedder used for the query. A shared default is created if omitted.
    """

    def __init__(self, store: VectorStore, embedder: Embedder | None = None) -> None:
        self._store = store
        self._embedder = embedder or Embedder()

    def retrieve(self, query: str, k: int | None = None) -> list[RetrievedChunk]:
        """Return up to ``k`` chunks scoring at least ``settings.min_score``.

        Args:
            query: The question text.
            k: Max results. Defaults to ``settings.top_k``.

        Returns:
            Chunks sorted by descending similarity; empty if nothing clears the floor.
        """
        query = (query or "").strip()
        if not query:
            return []
        k = k or settings.top_k
        query_vector = self._embedder.encode_one(query)
        hits = self._store.search(query_vector, k)
        return [hit for hit in hits if hit.score >= settings.min_score]

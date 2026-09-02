"""The vector-store contract shared by every retrieval backend.

Both the default NumPy store and the FAISS store implement this, so
:class:`~app.rag.retriever.Retriever` and the ingestion code depend only on the
interface (Dependency Inversion) and the backend is a config switch.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

import numpy as np

from app.models import RetrievedChunk
from app.rag.chunker import Chunk


class VectorStoreBase(ABC):
    """Stores chunk vectors + metadata and does top-k similarity search.

    Every vector passed in is assumed L2-normalized (as produced by
    :class:`app.rag.embeddings.Embedder`), so an inner product equals cosine
    similarity and scores lie in ``[-1, 1]``.
    """

    @abstractmethod
    def add(self, chunks: list[Chunk], vectors: np.ndarray) -> None:
        """Append ``chunks`` and their row-aligned ``vectors``."""

    @abstractmethod
    def __len__(self) -> int:
        """Number of vectors currently stored."""

    @abstractmethod
    def search(self, query_vector: np.ndarray, k: int) -> list[RetrievedChunk]:
        """Return up to ``k`` :class:`RetrievedChunk`, highest cosine score first."""

    @abstractmethod
    def save(self, directory: str | Path) -> None:
        """Persist the store under ``directory`` (created if missing)."""

    @classmethod
    @abstractmethod
    def load(cls, directory: str | Path) -> "VectorStoreBase":
        """Rebuild a store previously written by :meth:`save`."""

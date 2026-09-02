"""A FAISS-backed vector store (opt-in via ``VECTOR_STORE=faiss``).

Uses a flat inner-product index (``IndexFlatIP``): exact search, and because the
embeddings are L2-normalized the inner product is cosine similarity, so scores
and the ``settings.min_score`` floor behave exactly as with the NumPy backend.
Chunk text / section / index are kept in a parallel Python list and persisted
next to the FAISS index file.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from app.models import RetrievedChunk
from app.rag.base_store import VectorStoreBase
from app.rag.chunker import Chunk

_INDEX_FILE = "index.faiss"
_META_FILE = "meta.json"


class FaissVectorStore(VectorStoreBase):
    """Exact cosine search over a ``faiss.IndexFlatIP``."""

    def __init__(self) -> None:
        self._index = None  # faiss.IndexFlatIP, created on first add
        self._texts: list[str] = []
        self._sections: list[str] = []
        self._indices: list[int] = []

    @staticmethod
    def _as_matrix(vectors: np.ndarray) -> np.ndarray:
        """Coerce to the C-contiguous float32 2-D array FAISS requires."""
        matrix = np.ascontiguousarray(np.asarray(vectors, dtype=np.float32))
        return matrix.reshape(1, -1) if matrix.ndim == 1 else matrix

    # -- construction -------------------------------------------------------
    def add(self, chunks: list[Chunk], vectors: np.ndarray) -> None:
        """See :meth:`VectorStoreBase.add`."""
        if len(chunks) != len(vectors):
            raise ValueError("chunks and vectors must be the same length")
        if not chunks:
            return
        import faiss

        matrix = self._as_matrix(vectors)
        if self._index is None:
            self._index = faiss.IndexFlatIP(matrix.shape[1])
        self._index.add(matrix)
        self._texts.extend(c.text for c in chunks)
        self._sections.extend(c.section_title for c in chunks)
        self._indices.extend(c.index for c in chunks)

    # -- query ------------------------------------------------------------
    def __len__(self) -> int:
        return len(self._texts)

    def search(self, query_vector: np.ndarray, k: int) -> list[RetrievedChunk]:
        """See :meth:`VectorStoreBase.search`."""
        if self._index is None or len(self) == 0:
            return []
        scores, ids = self._index.search(self._as_matrix(query_vector), min(k, len(self)))
        results: list[RetrievedChunk] = []
        for score, idx in zip(scores[0], ids[0]):
            if idx < 0:  # FAISS pads with -1 when k > ntotal
                continue
            results.append(
                RetrievedChunk(
                    text=self._texts[idx],
                    section_title=self._sections[idx],
                    score=float(score),
                    chunk_index=self._indices[idx],
                )
            )
        return results

    # -- persistence ----------------------------------------------------
    def save(self, directory: str | Path) -> None:
        """See :meth:`VectorStoreBase.save`."""
        import faiss

        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)
        index = self._index if self._index is not None else faiss.IndexFlatIP(1)
        faiss.write_index(index, str(directory / _INDEX_FILE))
        (directory / _META_FILE).write_text(
            json.dumps(
                {"texts": self._texts, "sections": self._sections, "indices": self._indices},
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

    @classmethod
    def load(cls, directory: str | Path) -> "FaissVectorStore":
        """See :meth:`VectorStoreBase.load`."""
        import faiss

        directory = Path(directory)
        store = cls()
        meta = json.loads((directory / _META_FILE).read_text(encoding="utf-8"))
        store._texts = list(meta["texts"])
        store._sections = list(meta["sections"])
        store._indices = list(meta["indices"])
        if store._texts:
            store._index = faiss.read_index(str(directory / _INDEX_FILE))
        return store

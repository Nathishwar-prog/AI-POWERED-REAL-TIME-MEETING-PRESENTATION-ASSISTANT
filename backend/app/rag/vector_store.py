"""An in-memory vector store with brute-force cosine search and disk persistence.

For a single uploaded document (hundreds of chunks at most) a NumPy matrix and a
dot product are faster and far simpler than any vector database.  Each store is
persisted under ``<data_dir>/<doc_id>/`` as ``vectors.npz`` + ``meta.json`` so it
survives a server restart.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from app.models import RetrievedChunk
from app.rag.chunker import Chunk

_VECTORS_FILE = "vectors.npz"
_META_FILE = "meta.json"


class VectorStore:
    """Holds chunk vectors plus their text and section titles.

    The store assumes every stored vector is already L2-normalized (as produced by
    :class:`app.rag.embeddings.Embedder`), so ``matrix @ query`` is cosine
    similarity.
    """

    def __init__(self) -> None:
        self._matrix: np.ndarray | None = None
        self._texts: list[str] = []
        self._sections: list[str] = []
        self._indices: list[int] = []

    # -- construction -------------------------------------------------------
    def add(self, chunks: list[Chunk], vectors: np.ndarray) -> None:
        """Append ``chunks`` and their matching ``vectors`` (row-aligned)."""
        if len(chunks) != len(vectors):
            raise ValueError("chunks and vectors must be the same length")
        if len(chunks) == 0:
            return
        vectors = np.asarray(vectors, dtype=np.float32)
        self._matrix = vectors if self._matrix is None else np.vstack([self._matrix, vectors])
        self._texts.extend(chunk.text for chunk in chunks)
        self._sections.extend(chunk.section_title for chunk in chunks)
        self._indices.extend(chunk.index for chunk in chunks)

    # -- query ------------------------------------------------------------
    def __len__(self) -> int:
        return len(self._texts)

    def search(self, query_vector: np.ndarray, k: int) -> list[RetrievedChunk]:
        """Return the ``k`` most similar chunks to ``query_vector``, best first.

        Args:
            query_vector: A 1-D unit-norm vector of the store's dimension.
            k: Maximum number of results.

        Returns:
            Up to ``k`` :class:`RetrievedChunk` sorted by descending score.
        """
        if self._matrix is None or len(self) == 0:
            return []
        scores = self._matrix @ np.asarray(query_vector, dtype=np.float32)
        k = min(k, len(self))
        top = np.argpartition(-scores, k - 1)[:k]
        top = top[np.argsort(-scores[top])]
        return [
            RetrievedChunk(
                text=self._texts[i],
                section_title=self._sections[i],
                score=float(scores[i]),
                chunk_index=self._indices[i],
            )
            for i in top
        ]

    # -- persistence ----------------------------------------------------
    def save(self, directory: str | Path) -> None:
        """Persist the store to ``directory`` (created if missing)."""
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)
        matrix = self._matrix if self._matrix is not None else np.zeros((0, 0), np.float32)
        np.savez_compressed(directory / _VECTORS_FILE, matrix=matrix)
        (directory / _META_FILE).write_text(
            json.dumps(
                {"texts": self._texts, "sections": self._sections, "indices": self._indices},
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

    @classmethod
    def load(cls, directory: str | Path) -> "VectorStore":
        """Rebuild a store previously written by :meth:`save`."""
        directory = Path(directory)
        store = cls()
        meta = json.loads((directory / _META_FILE).read_text(encoding="utf-8"))
        store._texts = list(meta["texts"])
        store._sections = list(meta["sections"])
        store._indices = list(meta["indices"])
        with np.load(directory / _VECTORS_FILE) as data:
            matrix = data["matrix"]
        store._matrix = matrix.astype(np.float32) if matrix.size else None
        return store

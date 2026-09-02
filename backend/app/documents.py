"""Document ingestion and the "currently active document" registry.

This module is the seam between the pure RAG helpers (``app.rag.*``) and the rest
of the app.  It builds a persisted :class:`~app.rag.vector_store.VectorStore` from
an uploaded ``.docx`` and remembers which document the running meeting session
should retrieve from.  The MVP tracks exactly one active document at a time.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from app.config import settings
from app.models import DocumentInfo
from app.rag.chunker import chunk_sections
from app.rag.docx_loader import load_docx
from app.rag.embeddings import Embedder
from app.rag.retriever import Retriever
from app.rag.vector_store import VectorStore


def _doc_id_for(data: bytes) -> str:
    """Deterministic short id for a document's bytes (first 16 hex of SHA-256)."""
    return hashlib.sha256(data).hexdigest()[:16]


class DocumentRegistry:
    """Owns document ingestion and exposes a retriever for the active document."""

    def __init__(self, embedder: Embedder | None = None) -> None:
        self._embedder = embedder or Embedder()
        self._active_doc_id: str | None = None
        self._active_store: VectorStore | None = None

    # -- ingestion ------------------------------------------------------
    def ingest_bytes(self, data: bytes, *, filename: str = "upload.docx") -> DocumentInfo:
        """Ingest a ``.docx`` from raw bytes and make it the active document.

        The uploaded file is written under ``<data_dir>/<doc_id>/`` alongside its
        vector store so an ingest can be inspected or re-loaded later.

        Args:
            data: The ``.docx`` file contents.
            filename: Original name, used only for the saved copy's suffix.

        Returns:
            A :class:`DocumentInfo` summarising the ingest.
        """
        doc_id = _doc_id_for(data)
        doc_dir = settings.data_dir / doc_id
        doc_dir.mkdir(parents=True, exist_ok=True)

        source_path = doc_dir / f"source{Path(filename).suffix or '.docx'}"
        source_path.write_bytes(data)

        sections = load_docx(source_path)
        chunks = chunk_sections(sections)
        vectors = self._embedder.encode([chunk.text for chunk in chunks])

        store = VectorStore()
        store.add(chunks, vectors)
        store.save(doc_dir)

        self._active_doc_id = doc_id
        self._active_store = store
        return DocumentInfo(doc_id=doc_id, sections=len(sections), chunks=len(chunks))

    def ingest_path(self, path: str | Path) -> DocumentInfo:
        """Ingest a ``.docx`` from a filesystem path (used by the CLI script)."""
        path = Path(path)
        return self.ingest_bytes(path.read_bytes(), filename=path.name)

    # -- access -------------------------------------------------------
    @property
    def active_doc_id(self) -> str | None:
        """Id of the active document, or ``None`` if nothing has been ingested."""
        return self._active_doc_id

    @property
    def has_active_document(self) -> bool:
        """Whether a document is ready to be retrieved from."""
        return self._active_store is not None

    def get_retriever(self) -> Retriever:
        """Return a :class:`Retriever` bound to the active document's store.

        Raises:
            RuntimeError: If no document has been ingested yet.
        """
        if self._active_store is None:
            raise RuntimeError("no active document; ingest a .docx first")
        return Retriever(self._active_store, self._embedder)

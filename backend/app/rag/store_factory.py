"""Selects the vector-store backend from configuration.

``settings.vector_store`` is ``"numpy"`` (default, zero extra dependencies) or
``"faiss"`` (exact search via ``faiss-cpu``).  Adding a backend = one entry here.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from app.config import settings
from app.rag.base_store import VectorStoreBase


def _numpy() -> type[VectorStoreBase]:
    from app.rag.vector_store import VectorStore

    return VectorStore


def _faiss() -> type[VectorStoreBase]:
    from app.rag.faiss_store import FaissVectorStore

    return FaissVectorStore


_BACKENDS: dict[str, Callable[[], type[VectorStoreBase]]] = {
    "numpy": _numpy,
    "faiss": _faiss,
}


def _backend_class() -> type[VectorStoreBase]:
    key = settings.vector_store.lower()
    try:
        return _BACKENDS[key]()
    except KeyError:
        known = ", ".join(sorted(_BACKENDS))
        raise ValueError(f"unknown VECTOR_STORE {key!r}; expected one of: {known}") from None


def create_vector_store() -> VectorStoreBase:
    """Return a fresh, empty store of the configured backend."""
    return _backend_class()()


def load_vector_store(directory: str | Path) -> VectorStoreBase:
    """Load a persisted store of the configured backend from ``directory``."""
    return _backend_class().load(directory)

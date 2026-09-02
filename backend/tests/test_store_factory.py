"""Tests for :mod:`app.rag.store_factory` backend selection."""

from __future__ import annotations

import pytest

from app.config import settings
from app.rag.store_factory import create_vector_store
from app.rag.vector_store import VectorStore


def test_default_backend_is_numpy(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "vector_store", "numpy")
    assert isinstance(create_vector_store(), VectorStore)


def test_faiss_backend_selected_by_config(monkeypatch: pytest.MonkeyPatch) -> None:
    pytest.importorskip("faiss")
    from app.rag.faiss_store import FaissVectorStore

    monkeypatch.setattr(settings, "vector_store", "faiss")
    assert isinstance(create_vector_store(), FaissVectorStore)


def test_unknown_backend_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "vector_store", "pinecone")
    with pytest.raises(ValueError):
        create_vector_store()

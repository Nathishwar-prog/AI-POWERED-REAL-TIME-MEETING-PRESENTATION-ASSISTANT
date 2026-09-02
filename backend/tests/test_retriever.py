"""Tests for :mod:`app.rag.retriever` using the keyword FakeEmbedder."""

from __future__ import annotations

from app.config import settings
from app.rag.chunker import Chunk
from app.rag.retriever import Retriever
from app.rag.vector_store import VectorStore

from tests.conftest import FakeEmbedder


def _retriever(embedder: FakeEmbedder) -> Retriever:
    chunks = [
        Chunk(text="Refunds are issued within five days to the original payment.", section_title="Refund Policy", index=0),
        Chunk(text="Express shipping is delivered next day for an extra fee.", section_title="Shipping", index=1),
        Chunk(text="Support hours are Monday to Friday.", section_title="Support Hours", index=2),
    ]
    store = VectorStore()
    store.add(chunks, embedder.encode([c.text for c in chunks]))
    return Retriever(store, embedder)


def test_retrieves_the_relevant_section(fake_embedder: FakeEmbedder) -> None:
    hits = _retriever(fake_embedder).retrieve("what is the refund payment window in days")
    assert hits
    assert hits[0].section_title == "Refund Policy"


def test_unrelated_query_returns_nothing(fake_embedder: FakeEmbedder) -> None:
    hits = _retriever(fake_embedder).retrieve("what is the capital of France")
    assert hits == []


def test_respects_top_k(fake_embedder: FakeEmbedder, monkeypatch) -> None:
    monkeypatch.setattr(settings, "top_k", 1)
    hits = _retriever(fake_embedder).retrieve("shipping refund support days")
    assert len(hits) == 1


def test_blank_query_returns_nothing(fake_embedder: FakeEmbedder) -> None:
    assert _retriever(fake_embedder).retrieve("   ") == []

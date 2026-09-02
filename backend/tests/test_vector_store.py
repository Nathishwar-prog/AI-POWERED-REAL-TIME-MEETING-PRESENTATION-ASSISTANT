"""Tests for :mod:`app.rag.vector_store`."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from app.rag.chunker import Chunk
from app.rag.vector_store import VectorStore


def _unit(*values: float) -> np.ndarray:
    vec = np.array(values, dtype=np.float32)
    return vec / np.linalg.norm(vec)


def _store() -> VectorStore:
    chunks = [
        Chunk(text="refund text", section_title="Refunds", index=0),
        Chunk(text="shipping text", section_title="Shipping", index=1),
        Chunk(text="support text", section_title="Support", index=2),
    ]
    vectors = np.vstack([_unit(1, 0, 0), _unit(0, 1, 0), _unit(0, 0, 1)])
    store = VectorStore()
    store.add(chunks, vectors)
    return store


def test_search_ranks_by_cosine_similarity() -> None:
    hits = _store().search(_unit(0.9, 0.1, 0.0), k=3)
    assert [hit.section_title for hit in hits] == ["Refunds", "Shipping", "Support"]
    assert hits[0].score > hits[1].score > hits[2].score


def test_search_respects_k() -> None:
    assert len(_store().search(_unit(1, 1, 1), k=2)) == 2


def test_empty_store_returns_no_hits() -> None:
    assert VectorStore().search(_unit(1, 0, 0), k=5) == []


def test_save_and_load_round_trip(tmp_path: Path) -> None:
    original = _store()
    original.save(tmp_path)
    restored = VectorStore.load(tmp_path)

    assert len(restored) == len(original)
    query = _unit(0, 1, 0.2)
    assert [h.section_title for h in restored.search(query, 3)] == [
        h.section_title for h in original.search(query, 3)
    ]

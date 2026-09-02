"""Tests for :mod:`app.rag.chunker`."""

from __future__ import annotations

from app.rag.chunker import chunk_sections
from app.rag.docx_loader import Section


def _section(title: str, sentences: int) -> Section:
    body = " ".join(f"Sentence number {i} about the topic." for i in range(sentences))
    return Section(title=title, lines=[body])


def test_every_chunk_keeps_its_section_title() -> None:
    sections = [_section("Alpha", 20), _section("Beta", 20)]
    chunks = chunk_sections(sections, size=200, overlap=40)
    assert {c.section_title for c in chunks} == {"Alpha", "Beta"}


def test_chunks_are_globally_indexed_in_order() -> None:
    chunks = chunk_sections([_section("Alpha", 30)], size=150, overlap=30)
    assert [c.index for c in chunks] == list(range(len(chunks)))
    assert len(chunks) > 1  # 30 sentences must not fit in one 150-char chunk


def test_short_section_is_a_single_chunk() -> None:
    chunks = chunk_sections([Section(title="Tiny", lines=["One short line."])])
    assert len(chunks) == 1
    assert chunks[0].text == "One short line."


def test_overlap_repeats_tail_context() -> None:
    chunks = chunk_sections([_section("Alpha", 12)], size=120, overlap=60)
    assert len(chunks) >= 2
    # The start of chunk 2 should echo some words from the end of chunk 1.
    tail_words = set(chunks[0].text.split()[-4:])
    assert tail_words & set(chunks[1].text.split())

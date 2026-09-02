"""Split loaded sections into overlapping, retrieval-sized chunks.

Chunking is section-aware: a chunk never crosses a section boundary and always
carries its section title, so the retriever can tell the presenter exactly which
part of the document an answer came from.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.config import settings
from app.rag.docx_loader import Section

# Split on sentence-ending punctuation followed by whitespace.  Deliberately
# simple: good enough to avoid cutting mid-sentence without a heavy NLP dependency.
_SENTENCE_RE = re.compile(r"(?<=[.!?])\s+")


@dataclass
class Chunk:
    """A retrieval unit: a short span of text tagged with its origin.

    Attributes:
        text: The chunk content.
        section_title: Title of the section this chunk was taken from.
        index: Zero-based position of the chunk in the whole document.
    """

    text: str
    section_title: str
    index: int


def _split_sentences(text: str) -> list[str]:
    """Break ``text`` into sentence-ish fragments, preserving order."""
    return [part.strip() for part in _SENTENCE_RE.split(text) if part.strip()]


def _pack(sentences: list[str], size: int, overlap: int) -> list[str]:
    """Greedily pack sentences into ~``size``-char windows overlapping by ``overlap``.

    A sentence longer than ``size`` becomes its own (oversized) chunk rather than
    being hard-split, which keeps chunks human-readable.
    """
    chunks: list[str] = []
    current: list[str] = []
    current_len = 0

    for sentence in sentences:
        addition = len(sentence) + (1 if current else 0)
        if current and current_len + addition > size:
            chunks.append(" ".join(current))
            # Start the next window with a tail of the previous one for context.
            tail: list[str] = []
            tail_len = 0
            for prev in reversed(current):
                if tail_len + len(prev) + 1 > overlap:
                    break
                tail.insert(0, prev)
                tail_len += len(prev) + 1
            current = tail
            current_len = tail_len
        current.append(sentence)
        current_len += addition

    if current:
        chunks.append(" ".join(current))
    return chunks


def chunk_sections(
    sections: list[Section],
    *,
    size: int | None = None,
    overlap: int | None = None,
) -> list[Chunk]:
    """Turn ``sections`` into a flat, document-ordered list of :class:`Chunk`.

    Args:
        sections: Output of :func:`app.rag.docx_loader.load_docx`.
        size: Target chunk length in characters. Defaults to ``settings.chunk_size``.
        overlap: Characters of trailing context repeated at the start of the next
            chunk. Defaults to ``settings.chunk_overlap``.

    Returns:
        The chunks, each with a globally increasing ``index``.
    """
    size = size or settings.chunk_size
    overlap = overlap or settings.chunk_overlap

    chunks: list[Chunk] = []
    for section in sections:
        sentences = _split_sentences(section.body)
        for piece in _pack(sentences, size, overlap):
            chunks.append(Chunk(text=piece, section_title=section.title, index=len(chunks)))
    return chunks

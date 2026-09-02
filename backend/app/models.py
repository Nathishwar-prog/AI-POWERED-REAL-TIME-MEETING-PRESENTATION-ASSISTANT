"""Pydantic data models shared across every layer of the pipeline.

These types are the single source of truth for the shapes that flow between the
audio, question-detection, retrieval and LLM layers, and for the JSON pushed to
the presenter UI over WebSocket.  The frontend mirrors the wire-facing subset in
``frontend/src/types/api.ts``.
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from pydantic import BaseModel, Field


def _utcnow() -> datetime:
    """Timezone-aware current UTC timestamp (used as a default factory)."""
    return datetime.now(timezone.utc)


class TranscriptChunk(BaseModel):
    """A single fragment of text emitted by a :class:`~app.audio.base.Transcriber`.

    ``start``/``end`` are seconds from the start of the audio stream and are used
    by the pipeline to detect the silence gaps that separate utterances.
    """

    text: str
    start: float
    end: float
    speaker: str = "participant"


class Utterance(BaseModel):
    """One complete spoken turn, assembled from one or more transcript chunks."""

    text: str
    start: float
    end: float
    speaker: str = "participant"


class Question(BaseModel):
    """A detected question awaiting a suggested answer."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    text: str
    asked_at: datetime = Field(default_factory=_utcnow)
    speaker: str = "participant"


class RetrievedChunk(BaseModel):
    """A document chunk returned by the retriever, with its similarity score."""

    text: str
    section_title: str
    score: float
    chunk_index: int


class SourceRef(BaseModel):
    """A citation shown to the presenter: which document section was used."""

    section_title: str
    snippet: str
    score: float


class SuggestedAnswer(BaseModel):
    """The LLM's grounded answer plus the sources it relied on.

    ``grounded`` is ``False`` when the model reports that the uploaded document
    does not contain the information needed to answer.
    """

    text: str
    sources: list[SourceRef] = Field(default_factory=list)
    grounded: bool = True


class QAEvent(BaseModel):
    """Question + suggested answer, pushed to the presenter UI as one unit."""

    question: Question
    answer: SuggestedAnswer


class DocumentInfo(BaseModel):
    """Summary of an ingested document, returned by ``POST /api/documents``."""

    doc_id: str
    sections: int
    chunks: int

"""The meeting-session orchestrator.

:class:`MeetingSession` is the single place that wires the layers together:

    transcriber -> utterance assembly -> question detection -> retrieval -> LLM -> event callback

It owns no transport concerns; it just calls an ``on_event`` coroutine with plain
dicts, which :mod:`app.main` forwards over WebSocket.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable

from app.audio.base import Transcriber
from app.config import settings
from app.llm.base import LLMClient
from app.models import QAEvent, Question, TranscriptChunk, Utterance
from app.questions.detector import is_question
from app.rag.retriever import Retriever

logger = logging.getLogger(__name__)

#: Signature of the sink the session pushes events to.
EventCallback = Callable[[dict], Awaitable[None]]

#: Predicate deciding whether an utterance is a question.
QuestionPredicate = Callable[[str], bool]

_SENTENCE_ENDINGS = (".", "?", "!")


class UtteranceAssembler:
    """Groups transcript chunks into complete spoken turns.

    A buffered utterance is flushed when any of these hold:

    * the accumulated text ends with sentence punctuation;
    * a silence gap larger than ``settings.utterance_gap_s`` separates the next
      chunk from the previous one;
    * the buffer grows past ``settings.utterance_max_chars``.
    """

    def __init__(self) -> None:
        self._parts: list[str] = []
        self._start: float | None = None
        self._last_end: float = 0.0
        self._speaker: str = "participant"

    @property
    def _text(self) -> str:
        return " ".join(self._parts).strip()

    def _take(self) -> Utterance | None:
        """Emit and clear the current buffer, or ``None`` if it is empty."""
        text = self._text
        if not text:
            return None
        utterance = Utterance(
            text=text,
            start=self._start or 0.0,
            end=self._last_end,
            speaker=self._speaker,
        )
        self._parts.clear()
        self._start = None
        return utterance

    def add(self, chunk: TranscriptChunk) -> list[Utterance]:
        """Add a chunk and return any utterances completed as a result."""
        flushed: list[Utterance] = []

        gap = chunk.start - self._last_end
        if self._parts and gap > settings.utterance_gap_s:
            if (done := self._take()) is not None:
                flushed.append(done)

        if not self._parts:
            self._start = chunk.start
            self._speaker = chunk.speaker
        self._parts.append(chunk.text.strip())
        self._last_end = chunk.end

        if self._text.endswith(_SENTENCE_ENDINGS) or len(self._text) >= settings.utterance_max_chars:
            if (done := self._take()) is not None:
                flushed.append(done)

        return flushed

    def flush(self) -> Utterance | None:
        """Return whatever remains buffered (call once the stream ends)."""
        return self._take()


class MeetingSession:
    """Runs one meeting's transcription-to-answer loop as an asyncio task.

    Args:
        transcriber: Source of transcript chunks.
        retriever: Retriever bound to the active document.
        llm: Answer generator.
        on_event: Coroutine called with each ``transcript`` / ``qa`` event dict.
        question_predicate: Override for question detection (defaults to
            :func:`app.questions.detector.is_question`).
    """

    def __init__(
        self,
        transcriber: Transcriber,
        retriever: Retriever,
        llm: LLMClient,
        on_event: EventCallback,
        *,
        question_predicate: QuestionPredicate = is_question,
    ) -> None:
        self._transcriber = transcriber
        self._retriever = retriever
        self._llm = llm
        self._on_event = on_event
        self._is_question = question_predicate
        self._assembler = UtteranceAssembler()
        self._task: asyncio.Task[None] | None = None

    # -- lifecycle ----------------------------------------------------
    def start(self) -> None:
        """Schedule the session loop on the running event loop."""
        if self._task is not None:
            raise RuntimeError("session already started")
        self._task = asyncio.create_task(self._run(), name="meeting-session")

    async def wait(self) -> None:
        """Await natural completion of the loop (used by tests and finite sources)."""
        if self._task is not None:
            await self._task

    async def stop(self) -> None:
        """Cancel the loop and wait for it to unwind."""
        if self._task is None:
            return
        self._task.cancel()
        try:
            await self._task
        except asyncio.CancelledError:
            pass
        finally:
            self._task = None

    @property
    def running(self) -> bool:
        """Whether the session task is active."""
        return self._task is not None and not self._task.done()

    # -- loop ---------------------------------------------------------
    async def _run(self) -> None:
        try:
            async for chunk in self._transcriber.stream():
                await self._emit_transcript(chunk)
                for utterance in self._assembler.add(chunk):
                    await self._handle_utterance(utterance)
            if (tail := self._assembler.flush()) is not None:
                await self._handle_utterance(tail)
        except asyncio.CancelledError:
            raise
        except Exception:  # noqa: BLE001 - a session failure must not crash the server
            logger.exception("meeting session failed")

    async def _handle_utterance(self, utterance: Utterance) -> None:
        """Detect a question in ``utterance`` and, if found, produce a QA event."""
        if not self._is_question(utterance.text):
            return
        question = Question(text=utterance.text, speaker=utterance.speaker)
        logger.info("question detected: %s", question.text)

        contexts = await asyncio.to_thread(self._retriever.retrieve, question.text)
        answer = await asyncio.to_thread(self._llm.generate_answer, question.text, contexts)

        await self._on_event(QAEvent(question=question, answer=answer).model_dump(mode="json") | {"type": "qa"})

    async def _emit_transcript(self, chunk: TranscriptChunk) -> None:
        await self._on_event(
            {
                "type": "transcript",
                "text": chunk.text,
                "speaker": chunk.speaker,
                "start": chunk.start,
                "end": chunk.end,
            }
        )

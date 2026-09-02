"""End-to-end test of :class:`app.pipeline.MeetingSession` with fakes only."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.audio.mock_transcriber import MockTranscriber
from app.llm.echo_client import EchoLLMClient
from app.models import RetrievedChunk
from app.pipeline import MeetingSession, UtteranceAssembler
from app.models import TranscriptChunk


class StubRetriever:
    """Returns one canned chunk for questions that mention 'refund', else nothing."""

    def retrieve(self, query: str, k: int | None = None) -> list[RetrievedChunk]:
        if "refund" in query.lower():
            return [
                RetrievedChunk(
                    text="Refunds are available within 30 days.",
                    section_title="Refund Policy",
                    score=0.82,
                    chunk_index=0,
                )
            ]
        return []


@pytest.fixture
def script(tmp_path: Path) -> Path:
    path = tmp_path / "script.txt"
    path.write_text(
        "\n".join(
            [
                "# a scripted meeting",
                "Alice: What is the refund window?",
                "Bob: Thanks, that is really helpful.",
                "Carol: Can you clarify the refund process?",
            ]
        ),
        encoding="utf-8",
    )
    return path


async def _run(script_path: Path) -> list[dict]:
    events: list[dict] = []

    async def sink(event: dict) -> None:
        events.append(event)

    session = MeetingSession(
        transcriber=MockTranscriber(script_path, line_delay_s=0.0),
        retriever=StubRetriever(),
        llm=EchoLLMClient(),
        on_event=sink,
    )
    session.start()
    await session.wait()
    return events


async def test_questions_produce_qa_events_statements_do_not(script: Path) -> None:
    events = await _run(script)

    qa_events = [e for e in events if e["type"] == "qa"]
    transcript_events = [e for e in events if e["type"] == "transcript"]

    assert len(transcript_events) == 3
    assert len(qa_events) == 2
    assert all("refund" in e["question"]["text"].lower() for e in qa_events)


async def test_qa_event_carries_a_grounded_answer_with_source(script: Path) -> None:
    events = await _run(script)
    first_qa = next(e for e in events if e["type"] == "qa")

    assert first_qa["answer"]["grounded"] is True
    assert first_qa["answer"]["sources"][0]["section_title"] == "Refund Policy"


async def test_unanswerable_question_is_marked_not_grounded(tmp_path: Path) -> None:
    path = tmp_path / "s.txt"
    path.write_text("Dana: What is the meaning of life?\n", encoding="utf-8")

    events = await _run(path)
    qa = next(e for e in events if e["type"] == "qa")
    assert qa["answer"]["grounded"] is False
    assert qa["answer"]["sources"] == []


def test_utterance_assembler_splits_on_sentence_end() -> None:
    assembler = UtteranceAssembler()
    out = assembler.add(TranscriptChunk(text="This is done.", start=0.0, end=1.0))
    assert [u.text for u in out] == ["This is done."]


def test_utterance_assembler_splits_on_silence_gap() -> None:
    assembler = UtteranceAssembler()
    assert assembler.add(TranscriptChunk(text="first part", start=0.0, end=1.0)) == []
    flushed = assembler.add(TranscriptChunk(text="second part", start=5.0, end=6.0))
    assert [u.text for u in flushed] == ["first part"]

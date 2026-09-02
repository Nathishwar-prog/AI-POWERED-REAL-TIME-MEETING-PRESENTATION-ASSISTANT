"""Prompt templates for grounded answer generation.

Kept in one module so the wording can be tuned without hunting through client
code, and so every provider implementation shares exactly the same instructions.
"""

from __future__ import annotations

from app.models import RetrievedChunk, SourceRef, SuggestedAnswer

#: How many characters of a chunk to show the presenter as the source snippet.
SNIPPET_CHARS = 300

#: Marker the model is told to append; parsed back out to identify the source section.
SECTION_MARKER = "Section:"

#: Phrase the model is told to use when the document cannot answer the question.
NOT_COVERED_MARKER = "NOT_IN_DOCUMENT"

SYSTEM_PROMPT = f"""You assist a presenter during a live meeting. A participant has \
asked a question and you are given numbered excerpts from the presenter's uploaded \
document.

Rules:
- Answer using ONLY the excerpts. Never add facts from outside knowledge.
- Keep the answer to 2-4 sentences the presenter can say out loud.
- If the excerpts do not contain the answer, reply with a single sentence that \
starts with "{NOT_COVERED_MARKER}" and names what the presenter should ask the \
participant to clarify.
- On the final line, when you did use an excerpt, write "{SECTION_MARKER} <section title>" \
for the excerpt you relied on most.
"""


def build_user_prompt(question: str, contexts: list[RetrievedChunk]) -> str:
    """Render the user turn: the question followed by numbered excerpts.

    Args:
        question: The detected question.
        contexts: Retrieved chunks in rank order.

    Returns:
        A single string ready to send as the user message content.
    """
    if not contexts:
        excerpt_block = "(no relevant excerpts were found in the document)"
    else:
        excerpt_block = "\n\n".join(
            f"[{i + 1}] (Section: {chunk.section_title}) {chunk.text}"
            for i, chunk in enumerate(contexts)
        )
    return f"Question: {question}\n\nDocument excerpts:\n{excerpt_block}"


def _snippet(text: str) -> str:
    """Trim ``text`` to a presenter-friendly snippet length."""
    text = " ".join(text.split())
    return text if len(text) <= SNIPPET_CHARS else text[:SNIPPET_CHARS].rstrip() + "..."


def parse_model_answer(raw: str, contexts: list[RetrievedChunk]) -> SuggestedAnswer:
    """Convert a raw model reply into a :class:`SuggestedAnswer`.

    Handles the two shapes the system prompt asks for:

    * A "not covered" reply beginning with :data:`NOT_COVERED_MARKER` -> an answer
      with ``grounded=False`` and no sources.
    * A normal answer, optionally ending with a ``Section: <title>`` line -> the
      trailing marker is stripped from the text and the named section (falling
      back to the top-ranked chunk) becomes the :class:`SourceRef`.

    Args:
        raw: The model's message text.
        contexts: The chunks that were supplied to the model.

    Returns:
        A populated :class:`SuggestedAnswer`.
    """
    text = (raw or "").strip()

    if text.upper().startswith(NOT_COVERED_MARKER):
        cleaned = text[len(NOT_COVERED_MARKER):].lstrip(" :-").strip() or text
        return SuggestedAnswer(text=cleaned, sources=[], grounded=False)

    cited_title: str | None = None
    lines = text.splitlines()
    if lines and lines[-1].strip().startswith(SECTION_MARKER):
        cited_title = lines[-1].split(SECTION_MARKER, 1)[1].strip() or None
        text = "\n".join(lines[:-1]).strip()

    sources: list[SourceRef] = []
    if contexts:
        chosen = next(
            (c for c in contexts if cited_title and c.section_title.lower() == cited_title.lower()),
            contexts[0],
        )
        sources.append(
            SourceRef(
                section_title=chosen.section_title,
                snippet=_snippet(chosen.text),
                score=chosen.score,
            )
        )

    return SuggestedAnswer(text=text, sources=sources, grounded=bool(contexts))

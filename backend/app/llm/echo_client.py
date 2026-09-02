"""Offline :class:`LLMClient` used for tests and key-free local development.

It performs no network calls: it stitches the top retrieved chunk into a short
canned answer.  This keeps the whole pipeline runnable (and deterministic) with
no ``ANTHROPIC_API_KEY``.
"""

from __future__ import annotations

from app.llm.base import LLMClient
from app.llm.prompts import _snippet
from app.models import RetrievedChunk, SourceRef, SuggestedAnswer


class EchoLLMClient(LLMClient):
    """Returns the best-matching excerpt as a pseudo-answer."""

    def generate_answer(
        self, question: str, contexts: list[RetrievedChunk]
    ) -> SuggestedAnswer:
        """See :meth:`LLMClient.generate_answer`."""
        if not contexts:
            return SuggestedAnswer(
                text=(
                    "The uploaded document does not appear to cover this. Ask the "
                    f"participant to clarify what they mean by: {question}"
                ),
                sources=[],
                grounded=False,
            )
        top = contexts[0]
        return SuggestedAnswer(
            text=f"Based on the document: {top.text}",
            sources=[
                SourceRef(
                    section_title=top.section_title,
                    snippet=_snippet(top.text),
                    score=top.score,
                )
            ],
            grounded=True,
        )

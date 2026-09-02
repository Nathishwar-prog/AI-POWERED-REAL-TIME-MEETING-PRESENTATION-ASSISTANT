"""Anthropic Claude implementation of :class:`~app.llm.base.LLMClient`.

Uses the official ``anthropic`` SDK with a single non-streaming ``messages.create``
call - responses are short (a 2-4 sentence answer) so streaming is unnecessary.
Adaptive thinking is left on with ``effort="low"`` to favour latency during a
live meeting.
"""

from __future__ import annotations

import logging

from app.config import settings
from app.llm.base import LLMClient
from app.llm.prompts import SYSTEM_PROMPT, build_user_prompt, parse_model_answer
from app.models import RetrievedChunk, SuggestedAnswer

logger = logging.getLogger(__name__)

#: Comfortably above a 2-4 sentence answer plus the trailing Section line.
_MAX_TOKENS = 1024


class ClaudeLLMClient(LLMClient):
    """Generates grounded answers with a Claude model.

    Args:
        model: Model id. Defaults to ``settings.llm_model``.
        api_key: Explicit key. Normally omitted so the SDK resolves credentials
            from ``ANTHROPIC_API_KEY`` or an ``ant auth login`` profile.
    """

    def __init__(self, model: str | None = None, api_key: str | None = None) -> None:
        # Imported here so environments running only the "echo" provider never
        # need the anthropic package installed.
        import anthropic

        self._model = model or settings.llm_model
        self._client = anthropic.Anthropic(api_key=api_key or settings.anthropic_api_key or None)

    def generate_answer(
        self, question: str, contexts: list[RetrievedChunk]
    ) -> SuggestedAnswer:
        """See :meth:`LLMClient.generate_answer`."""
        response = self._client.messages.create(
            model=self._model,
            max_tokens=_MAX_TOKENS,
            thinking={"type": "adaptive"},
            output_config={"effort": "low"},
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": build_user_prompt(question, contexts)}],
        )

        if response.stop_reason == "refusal":
            detail = getattr(response.stop_details, "explanation", None) or "safety refusal"
            logger.warning("Claude refused to answer: %s", detail)
            return SuggestedAnswer(
                text="Could not generate a suggested answer for this question.",
                sources=[],
                grounded=False,
            )

        raw_text = "".join(
            block.text for block in response.content if getattr(block, "type", None) == "text"
        )
        return parse_model_answer(raw_text, contexts)

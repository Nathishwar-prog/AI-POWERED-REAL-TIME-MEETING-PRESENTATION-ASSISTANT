"""LLM client for any OpenAI-compatible ``/chat/completions`` endpoint.

This is the "free API key" path.  Several providers offer a genuinely free tier
behind the same wire format - Groq, Google Gemini, OpenRouter, Cerebras - so one
small HTTP client covers all of them, plus local model servers (Ollama, LM
Studio, llama.cpp) that expose the same route.

It deliberately does **not** use a vendor SDK: a single ``POST`` with an
``Authorization: Bearer`` header is all that is needed, and the grounding logic
(system prompt, answer parsing) is shared with the Claude client via
:mod:`app.llm.prompts`.
"""

from __future__ import annotations

import logging

import httpx

from app.llm.base import LLMClient
from app.llm.prompts import SYSTEM_PROMPT, build_user_prompt, parse_model_answer
from app.models import RetrievedChunk, SuggestedAnswer

logger = logging.getLogger(__name__)

_MAX_TOKENS = 400
_TIMEOUT_S = 30.0


class OpenAICompatLLMClient(LLMClient):
    """Calls an OpenAI-style chat completions API to generate grounded answers.

    Args:
        base_url: API root, e.g. ``https://api.groq.com/openai/v1`` (no trailing
            ``/chat/completions``).
        api_key: Bearer token for the provider.
        model: Model id understood by that provider.
    """

    def __init__(self, *, base_url: str, api_key: str | None, model: str) -> None:
        if not base_url:
            raise ValueError("LLM base URL is required for the OpenAI-compatible provider")
        self._url = base_url.rstrip("/") + "/chat/completions"
        self._headers = {"Content-Type": "application/json"}
        if api_key:
            self._headers["Authorization"] = f"Bearer {api_key}"
        self._model = model

    def generate_answer(
        self, question: str, contexts: list[RetrievedChunk]
    ) -> SuggestedAnswer:
        """See :meth:`LLMClient.generate_answer`.

        Network / API failures are logged and returned as a non-grounded answer so
        a single hiccup never stops the meeting session.
        """
        payload = {
            "model": self._model,
            "temperature": 0.2,
            "max_tokens": _MAX_TOKENS,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": build_user_prompt(question, contexts)},
            ],
        }
        try:
            response = httpx.post(
                self._url, json=payload, headers=self._headers, timeout=_TIMEOUT_S
            )
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
        except (httpx.HTTPError, KeyError, IndexError, ValueError) as exc:
            detail = exc
            if isinstance(exc, httpx.HTTPStatusError):
                detail = f"{exc.response.status_code} {exc.response.text[:200]}"
            logger.warning("LLM request failed: %s", detail)
            return SuggestedAnswer(
                text="Could not reach the language model to draft an answer.",
                sources=[],
                grounded=False,
            )

        return parse_model_answer(content, contexts)

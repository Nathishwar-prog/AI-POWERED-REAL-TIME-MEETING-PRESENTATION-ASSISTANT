"""Tests for the OpenAI-compatible (free-tier) LLM client and its factory wiring."""

from __future__ import annotations

import httpx
import pytest

from app.llm.factory import build_llm_client
from app.llm.openai_compat_client import OpenAICompatLLMClient
from app.models import RetrievedChunk

_CONTEXTS = [
    RetrievedChunk(text="Refunds are available within 30 days.", section_title="Refunds", score=0.8, chunk_index=0)
]


class _FakeResponse:
    def __init__(self, content: str) -> None:
        self._content = content

    def raise_for_status(self) -> None:  # noqa: D401
        return None

    def json(self) -> dict:
        return {"choices": [{"message": {"content": self._content}}]}


def test_factory_builds_groq_preset() -> None:
    client = build_llm_client("groq")
    assert isinstance(client, OpenAICompatLLMClient)
    assert client._url == "https://api.groq.com/openai/v1/chat/completions"
    # A preset default model is used, not the Claude default.
    assert client._model and client._model != "claude-opus-5"


def test_generate_answer_parses_a_normal_reply(monkeypatch: pytest.MonkeyPatch) -> None:
    reply = "Refunds are available within 30 days of purchase.\nSection: Refunds"
    monkeypatch.setattr(httpx, "post", lambda *a, **k: _FakeResponse(reply))

    client = OpenAICompatLLMClient(base_url="https://x/v1", api_key="k", model="m")
    answer = client.generate_answer("what is the refund window?", _CONTEXTS)

    assert answer.grounded is True
    assert answer.sources[0].section_title == "Refunds"
    assert "Section:" not in answer.text


def test_generate_answer_falls_back_on_http_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def boom(*_a, **_k):
        raise httpx.ConnectError("no network")

    monkeypatch.setattr(httpx, "post", boom)

    client = OpenAICompatLLMClient(base_url="https://x/v1", api_key="k", model="m")
    answer = client.generate_answer("anything?", _CONTEXTS)

    assert answer.grounded is False
    assert answer.sources == []


def test_missing_base_url_is_rejected() -> None:
    with pytest.raises(ValueError):
        OpenAICompatLLMClient(base_url="", api_key="k", model="m")

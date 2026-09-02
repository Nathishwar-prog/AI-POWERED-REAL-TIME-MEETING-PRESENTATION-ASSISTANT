"""Factory that builds the configured :class:`~app.llm.base.LLMClient`.

Adding a provider means adding a builder to :data:`_BUILDERS` - no other code
changes.  Builders are lazy (called only for the selected provider) so unused
providers' dependencies never need to be importable.
"""

from __future__ import annotations

from collections.abc import Callable

from app.config import settings
from app.llm.base import LLMClient

#: OpenAI-compatible providers with a free tier: provider -> (base_url, default model).
#: Selecting one of these needs only ``LLM_API_KEY`` (``LLM_MODEL`` is optional).
_OPENAI_PRESETS: dict[str, tuple[str, str]] = {
    "groq": ("https://api.groq.com/openai/v1", "openai/gpt-oss-20b"),
    "gemini": ("https://generativelanguage.googleapis.com/v1beta/openai", "gemini-2.0-flash"),
    "openrouter": ("https://openrouter.ai/api/v1", "meta-llama/llama-3.3-70b-instruct:free"),
    "cerebras": ("https://api.cerebras.ai/v1", "llama-3.1-8b"),
}


def _build_claude() -> LLMClient:
    from app.llm.claude_client import ClaudeLLMClient

    return ClaudeLLMClient()


def _build_echo() -> LLMClient:
    from app.llm.echo_client import EchoLLMClient

    return EchoLLMClient()


def _build_openai_compatible(provider: str) -> LLMClient:
    """Build the OpenAI-compatible client for the generic ``openai`` provider or a preset."""
    from app.llm.openai_compat_client import OpenAICompatLLMClient

    if provider in _OPENAI_PRESETS:
        base_url, default_model = _OPENAI_PRESETS[provider]
        base_url = settings.llm_base_url or base_url
        # Fall back to the preset model unless the user set a non-Claude LLM_MODEL.
        model = settings.llm_model if settings.llm_model != "claude-opus-5" else default_model
    else:  # "openai" - fully generic (also covers Ollama / LM Studio / vLLM)
        base_url = settings.llm_base_url or "https://api.openai.com/v1"
        model = settings.llm_model if settings.llm_model != "claude-opus-5" else "gpt-4o-mini"

    return OpenAICompatLLMClient(base_url=base_url, api_key=settings.llm_api_key, model=model)


_BUILDERS: dict[str, Callable[[], LLMClient]] = {
    "claude": _build_claude,
    "echo": _build_echo,
    "openai": lambda: _build_openai_compatible("openai"),
    **{name: (lambda n=name: _build_openai_compatible(n)) for name in _OPENAI_PRESETS},
}


def build_llm_client(provider: str | None = None) -> LLMClient:
    """Return an LLM client for ``provider`` (default: ``settings.llm_provider``).

    Raises:
        ValueError: If ``provider`` is not a known key of :data:`_BUILDERS`.
    """
    key = (provider or settings.llm_provider).lower()
    try:
        return _BUILDERS[key]()
    except KeyError:
        known = ", ".join(sorted(_BUILDERS))
        raise ValueError(f"unknown LLM provider {key!r}; expected one of: {known}") from None

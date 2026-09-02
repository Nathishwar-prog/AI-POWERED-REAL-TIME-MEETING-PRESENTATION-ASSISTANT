"""Central application configuration.

Every tunable value in the system lives here so behaviour can be changed through
environment variables (or a ``.env`` file) without touching code.  Import the
module-level :data:`settings` singleton wherever configuration is needed::

    from app.config import settings

    model_name = settings.embed_model
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Strongly-typed application settings loaded from the environment.

    Field names are lower_snake_case; the matching environment variables are the
    upper-case form (``LLM_PROVIDER``, ``TOP_K`` ...).  See ``backend/.env.example``
    for the full list with descriptions.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- LLM ---------------------------------------------------------------
    #: One of: claude | echo | openai | groq | gemini | openrouter | cerebras.
    #: The last five all speak the OpenAI-compatible chat API; groq/gemini/...
    #: preset the base URL so you only supply LLM_API_KEY (+ optionally LLM_MODEL).
    llm_provider: str = Field(default="claude")
    llm_model: str = Field(default="claude-opus-5")
    #: API key for the OpenAI-compatible providers (Groq, Gemini, OpenRouter, ...).
    llm_api_key: str | None = Field(default=None)
    #: Base URL for the generic ``openai`` provider (e.g. a local model server).
    llm_base_url: str | None = Field(default=None)
    anthropic_api_key: str | None = Field(default=None)

    # --- Speech to text -------------------------------------------------------
    whisper_model: str = Field(default="base.en")

    # --- Retrieval (RAG) ----------------------------------------------------
    embed_model: str = Field(default="all-MiniLM-L6-v2")
    #: Vector-search backend: "numpy" (default, no extra deps) or "faiss".
    vector_store: str = Field(default="numpy")
    top_k: int = Field(default=4, ge=1)
    min_score: float = Field(default=0.15, ge=0.0, le=1.0)
    chunk_size: int = Field(default=800, ge=100)
    chunk_overlap: int = Field(default=150, ge=0)

    # --- Question detection -----------------------------------------------
    question_llm_fallback: bool = Field(default=False)

    # --- Utterance assembly ---------------------------------------------
    utterance_gap_s: float = Field(default=1.2, ge=0.0)
    utterance_max_chars: int = Field(default=400, ge=50)

    # --- Storage & CORS --------------------------------------------------
    data_dir: Path = Field(default=Path("./data"))
    cors_origins: str = Field(default="http://localhost:5173")

    # --- Zoom App (free, development-mode side panel) ---------------------
    #: Space-separated CSP ``frame-ancestors`` allowed to embed the app. The
    #: defaults let the Zoom desktop/web client host the panel.
    zoom_frame_ancestors: str = Field(
        default="'self' https://*.zoom.us https://*.zoomgov.com",
    )
    #: Public HTTPS origin the app is reached at (the tunnel URL). Informational
    #: only - used for a startup log line so you can copy it into the Zoom app.
    public_base_url: str | None = Field(default=None)

    @property
    def cors_origin_list(self) -> list[str]:
        """CORS origins parsed into a list of trimmed, non-empty strings."""
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the process-wide :class:`Settings` singleton (cached)."""
    return Settings()


settings: Settings = get_settings()

"""Ping the configured LLM provider and print exactly what happened.

Run from the ``backend/`` directory::

    python -m scripts.check_llm

Prints the resolved provider / model / key status, then makes one real request
so you see the actual HTTP status and error body (401 = bad key, 400 =
model/params, connection error = network/proxy) instead of the generic
"could not reach the model" the UI shows.
"""

from __future__ import annotations

from app.config import settings
from app.llm.factory import build_llm_client
from app.models import RetrievedChunk

_OPENAI_LIKE = {"openai", "groq", "gemini", "openrouter", "cerebras"}


def _list_models(httpx, client) -> None:
    """Print the model ids the current key can use (``GET /models``)."""
    models_url = client._url.replace("/chat/completions", "/models")
    try:
        resp = httpx.get(models_url, headers=client._headers, timeout=15.0)
        ids = sorted(m["id"] for m in resp.json().get("data", []))
    except Exception as exc:  # noqa: BLE001 - diagnostic
        print(f"(could not list models: {exc!r})")
        return
    if ids:
        print("\nmodels your key CAN use — put one in .env as LLM_MODEL=<id>:")
        for model_id in ids:
            print(f"  {model_id}")


def main() -> int:
    key = settings.llm_api_key or ""
    print(f"provider  = {settings.llm_provider}")
    if settings.llm_base_url:
        print(f"base_url  = {settings.llm_base_url}")
    if key:
        print(f"api_key   = set, {len(key)} chars, starts {key[:4]!r}")
    else:
        print("api_key   = MISSING  <-- set LLM_API_KEY in backend/.env")
    print("-" * 48)

    if settings.llm_provider.lower() in _OPENAI_LIKE:
        import httpx

        client = build_llm_client()
        print(f"model     = {client._model}")
        try:
            resp = httpx.post(
                client._url,
                headers=client._headers,
                json={
                    "model": client._model,
                    "max_tokens": 20,
                    "messages": [{"role": "user", "content": "Say hello in three words."}],
                },
                timeout=30.0,
            )
        except Exception as exc:  # noqa: BLE001 - diagnostic
            print(f"request error: {exc!r}")
            print("\n-> network/proxy/DNS problem, or wrong base URL.")
            return 1

        print(f"HTTP {resp.status_code} {client._url}")
        if resp.status_code == 200:
            print("reply:", resp.json()["choices"][0]["message"]["content"])
            print("\n-> OK. The key and model work; restart the backend and try again.")
            return 0
        print("body:", resp.text[:800])
        hint = {
            401: "bad or missing API key",
            403: "key lacks access / region blocked",
            404: "wrong model id or base URL",
            429: "rate limited - wait a minute",
        }.get(resp.status_code, "see body above (often a decommissioned model id)")
        print(f"\n-> {hint}")

        if resp.status_code in (403, 404):
            _list_models(httpx, client)
        return 1

    # claude / echo
    print(f"model     = {settings.llm_model}")
    answer = build_llm_client().generate_answer(
        "Say hello.",
        [RetrievedChunk(text="hello", section_title="Greeting", score=1.0, chunk_index=0)],
    )
    print("answer:", answer.text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

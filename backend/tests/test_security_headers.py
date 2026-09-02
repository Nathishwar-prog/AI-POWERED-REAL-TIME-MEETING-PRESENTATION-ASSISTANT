"""Tests for :mod:`app.security_headers`."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.security_headers import SecurityHeadersMiddleware


def _client() -> TestClient:
    app = FastAPI()
    app.add_middleware(SecurityHeadersMiddleware)

    @app.get("/ping")
    def ping() -> dict[str, str]:
        return {"ok": "yes"}

    return TestClient(app)


def test_sets_csp_with_zoom_frame_ancestors_and_no_xfo() -> None:
    response = _client().get("/ping")
    csp = response.headers["content-security-policy"]
    assert "frame-ancestors 'self' https://*.zoom.us https://*.zoomgov.com" in csp
    assert "default-src 'self'" in csp
    assert "x-frame-options" not in {k.lower() for k in response.headers}


def test_sets_the_other_owasp_headers() -> None:
    headers = _client().get("/ping").headers
    assert headers["x-content-type-options"] == "nosniff"
    assert headers["referrer-policy"] == "strict-origin-when-cross-origin"
    assert headers["strict-transport-security"].startswith("max-age=")

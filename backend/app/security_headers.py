"""HTTP security-header middleware.

Zoom validates the Zoom App **Home URL** for a set of OWASP secure headers and
refuses to save it without them; the panel also has to be embeddable by the Zoom
client, which means a permissive ``frame-ancestors`` and **no** ``X-Frame-Options``.
This middleware adds those headers to every response.

The ``Content-Security-Policy`` allows inline ``<style>`` because MUI / emotion
inject style tags at runtime; it otherwise keeps everything same-origin.
"""

from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.config import settings


def _build_csp() -> str:
    """Assemble the Content-Security-Policy string from settings."""
    return "; ".join(
        [
            "default-src 'self'",
            "script-src 'self'",
            "style-src 'self' 'unsafe-inline'",
            "img-src 'self' data:",
            "font-src 'self' data:",
            "connect-src 'self' https: wss:",
            f"frame-ancestors {settings.zoom_frame_ancestors}",
            "base-uri 'self'",
            "form-action 'self'",
        ]
    )


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Adds Zoom-required security headers to every response."""

    def __init__(self, app) -> None:  # noqa: D107 - see class docstring
        super().__init__(app)
        self._csp = _build_csp()

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        # Don't apply restrictive CSP on /docs or /redoc so Swagger UI / ReDoc can load CDN assets and inline scripts
        if not request.url.path.startswith(("/docs", "/redoc")):
            response.headers.setdefault("Content-Security-Policy", self._csp)
        response.headers.setdefault(
            "Strict-Transport-Security", "max-age=31536000; includeSubDomains"
        )
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        # X-Frame-Options would block the Zoom client from embedding the panel.
        if "x-frame-options" in response.headers:
            del response.headers["x-frame-options"]
        return response

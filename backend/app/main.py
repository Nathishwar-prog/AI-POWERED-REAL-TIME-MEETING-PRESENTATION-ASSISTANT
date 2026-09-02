"""FastAPI application: REST endpoints + the presenter WebSocket.

Routes are intentionally thin - they validate input and delegate to
:class:`app.runtime.AppRuntime`.  The built React app (``frontend/dist``) is
served at ``/`` when present so the whole MVP can run from one process in
production; in development the Vite dev server proxies here instead.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app.config import settings
from app.models import DocumentInfo
from app.runtime import AppRuntime
from app.security_headers import SecurityHeadersMiddleware

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)

_FRONTEND_DIST = Path(__file__).resolve().parents[2] / "frontend" / "dist"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create the runtime on startup and tear the session down on shutdown."""
    app.state.runtime = AppRuntime()
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    logger.info("runtime ready (llm_provider=%s)", settings.llm_provider)
    if settings.public_base_url:
        logger.info("Zoom App Home URL -> %s", settings.public_base_url)
    try:
        yield
    finally:
        await app.state.runtime.shutdown()


app = FastAPI(title="AI Meeting Assistant", version="0.1.0", lifespan=lifespan)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_runtime() -> AppRuntime:
    """Return the process-wide :class:`AppRuntime` (populated by ``lifespan``)."""
    return app.state.runtime


# --- request models -------------------------------------------------------
class StartSessionRequest(BaseModel):
    """Body for ``POST /api/session/start``."""

    source: str = Field(description="'mock', 'file' or 'loopback'")
    path: str | None = Field(
        default=None,
        description="mock: script path; file: audio path; loopback: input device name/index",
    )


class SessionStatus(BaseModel):
    """Current session / document status."""

    session_running: bool
    active_doc_id: str | None


# --- REST ---------------------------------------------------------------
@app.get("/api/health")
def health() -> dict[str, str]:
    """Liveness probe."""
    return {"status": "ok"}


@app.get("/api/audio/devices")
def audio_devices() -> list[dict]:
    """List input devices usable by the ``loopback`` source (index, name, ...)."""
    from app.audio.loopback_source import list_input_devices

    try:
        return list_input_devices()
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"could not list audio devices: {exc}") from exc


@app.get("/api/status", response_model=SessionStatus)
def status() -> SessionStatus:
    """Report whether a document is loaded and a session is running."""
    runtime = get_runtime()
    return SessionStatus(
        session_running=runtime.session_running,
        active_doc_id=runtime.registry.active_doc_id,
    )


@app.post("/api/documents", response_model=DocumentInfo)
async def upload_document(file: UploadFile = File(...)) -> DocumentInfo:  # noqa: B008
    """Ingest a ``.docx`` and make it the active document."""
    if not (file.filename or "").lower().endswith(".docx"):
        raise HTTPException(status_code=400, detail="please upload a .docx file")
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="uploaded file is empty")
    try:
        return get_runtime().registry.ingest_bytes(data, filename=file.filename or "upload.docx")
    except Exception as exc:  # noqa: BLE001
        logger.exception("document ingest failed")
        raise HTTPException(status_code=422, detail=f"could not read document: {exc}") from exc


@app.post("/api/session/start", response_model=SessionStatus)
async def start_session(body: StartSessionRequest) -> SessionStatus:
    """Start the transcription-to-answer pipeline."""
    runtime = get_runtime()
    try:
        await runtime.start_session(body.source, body.path)
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return SessionStatus(session_running=runtime.session_running, active_doc_id=runtime.registry.active_doc_id)


@app.post("/api/session/stop", response_model=SessionStatus)
async def stop_session() -> SessionStatus:
    """Stop the active pipeline (idempotent)."""
    runtime = get_runtime()
    await runtime.stop_session()
    return SessionStatus(session_running=runtime.session_running, active_doc_id=runtime.registry.active_doc_id)


# --- WebSocket --------------------------------------------------------
@app.websocket("/ws/presenter")
async def presenter_ws(websocket: WebSocket) -> None:
    """Private presenter channel: receives ``transcript`` and ``qa`` events."""
    runtime = get_runtime()
    await runtime.hub.connect(websocket)
    try:
        while True:
            # The presenter UI never sends messages; this keeps the socket open
            # and surfaces disconnects promptly.
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        await runtime.hub.disconnect(websocket)


# --- static frontend (production) ---------------------------------------
if _FRONTEND_DIST.is_dir():
    app.mount("/", StaticFiles(directory=str(_FRONTEND_DIST), html=True), name="frontend")

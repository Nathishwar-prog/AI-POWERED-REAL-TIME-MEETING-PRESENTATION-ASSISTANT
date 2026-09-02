"""Process-wide runtime state: the presenter hub and the single meeting session.

Keeping this out of :mod:`app.main` lets the route handlers stay thin and makes
the moving parts (connected sockets, the active session) easy to test in
isolation.  The MVP supports one meeting at a time.
"""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path

from fastapi import WebSocket

from app.audio.base import Transcriber
from app.audio.file_source import FileAudioSource
from app.audio.loopback_source import (
    SYSTEM_PLUS_MIC,
    LoopbackAudioSource,
    default_input_index,
)
from app.audio.mixed_source import MixedAudioSource
from app.audio.mock_transcriber import MockTranscriber
from app.audio.whisper_transcriber import WhisperTranscriber
from app.documents import DocumentRegistry
from app.llm.factory import build_llm_client
from app.pipeline import MeetingSession

logger = logging.getLogger(__name__)

#: Default script used by the "mock" source when no path is supplied.
DEFAULT_MOCK_SCRIPT = Path(__file__).resolve().parents[1] / "sample_data" / "sample_transcript.txt"


class PresenterHub:
    """Fan-out of pipeline events to every connected presenter WebSocket."""

    def __init__(self) -> None:
        self._connections: set[WebSocket] = set()
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket) -> None:
        """Accept ``websocket`` and start delivering events to it."""
        await websocket.accept()
        async with self._lock:
            self._connections.add(websocket)

    async def disconnect(self, websocket: WebSocket) -> None:
        """Stop delivering events to ``websocket``."""
        async with self._lock:
            self._connections.discard(websocket)

    async def broadcast(self, event: dict) -> None:
        """Send ``event`` as JSON to all connections, dropping dead ones."""
        async with self._lock:
            targets = list(self._connections)
        stale: list[WebSocket] = []
        for connection in targets:
            try:
                await connection.send_json(event)
            except Exception:  # noqa: BLE001 - a broken socket must not stop the fan-out
                stale.append(connection)
        if stale:
            async with self._lock:
                self._connections.difference_update(stale)


def _build_transcriber(source: str, path: str | None) -> Transcriber:
    """Construct the transcriber for a ``session/start`` request.

    Args:
        source: ``"mock"``, ``"file"`` or ``"loopback"``.
        path: Meaning depends on ``source`` -
            ``mock``: script path (optional, defaults to the sample script);
            ``file``: audio file path (required);
            ``loopback``: input device name substring or index (optional,
            defaults to the system default input device).

    Raises:
        ValueError: For an unknown source or a missing/absent ``file`` path.
    """
    if source == "mock":
        script = Path(path) if path else DEFAULT_MOCK_SCRIPT
        if not script.exists():
            raise ValueError(f"mock script not found: {script}")
        return MockTranscriber(script)
    if source == "file":
        if not path:
            raise ValueError("source 'file' requires 'path' to an audio file")
        audio_path = Path(path)
        if not audio_path.exists():
            raise ValueError(f"audio file not found: {audio_path}")
        return WhisperTranscriber(FileAudioSource(audio_path))
    if source == "loopback":
        if path == SYSTEM_PLUS_MIC:
            mixed = MixedAudioSource(
                LoopbackAudioSource(None),  # system output
                LoopbackAudioSource(default_input_index()),  # default mic
            )
            return WhisperTranscriber(mixed)
        device: str | int | None = None
        if path:
            device = int(path) if path.isdigit() else path
        return WhisperTranscriber(LoopbackAudioSource(device))
    raise ValueError(f"unknown source {source!r}; expected 'mock', 'file' or 'loopback'")


class AppRuntime:
    """Holds the document registry, the presenter hub and the active session."""

    def __init__(self) -> None:
        self.registry = DocumentRegistry()
        self.hub = PresenterHub()
        self._session: MeetingSession | None = None

    @property
    def session_running(self) -> bool:
        """Whether a meeting session is currently active."""
        return self._session is not None and self._session.running

    async def start_session(self, source: str, path: str | None) -> None:
        """Start a meeting session for the active document.

        Raises:
            RuntimeError: If no document is ingested or a session already runs.
            ValueError: If the source/path combination is invalid.
        """
        if not self.registry.has_active_document:
            raise RuntimeError("no active document; upload a .docx first")
        if self.session_running:
            raise RuntimeError("a meeting session is already running")

        transcriber = _build_transcriber(source, path)
        session = MeetingSession(
            transcriber=transcriber,
            retriever=self.registry.get_retriever(),
            llm=build_llm_client(),
            on_event=self.hub.broadcast,
        )
        session.start()
        self._session = session
        logger.info("meeting session started (source=%s)", source)

    async def stop_session(self) -> None:
        """Stop the active session if there is one (idempotent)."""
        if self._session is not None:
            await self._session.stop()
            self._session = None
            logger.info("meeting session stopped")

    async def shutdown(self) -> None:
        """Tear down on application shutdown."""
        await self.stop_session()

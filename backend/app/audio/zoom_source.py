"""Placeholder for a future Zoom-backed :class:`~app.audio.base.AudioSource`.

Direct Zoom capture is intentionally **not** implemented in this MVP.  Because the
pipeline only depends on :class:`~app.audio.base.AudioSource`, adding Zoom later is
purely a matter of implementing :meth:`ZoomAudioSource.frames` - no pipeline,
retriever, or LLM code changes.

Integration routes, easiest first:

1. **Virtual audio device** (BlackHole on macOS, VB-CABLE on Windows).
   Route Zoom's speaker output into a virtual input device and read it the same
   way :class:`~app.audio.file_source.FileAudioSource` reads a file. No Zoom
   credentials or SDK required; best for the first real end-to-end test.
2. **Zoom Meeting SDK bot.** A headless client joins the meeting and exposes the
   raw mixed-audio callback (`onMixedAudioRawDataReceived`). Feed those PCM
   buffers straight into :meth:`frames`. Requires Zoom SDK credentials and the
   native SDK.
3. **Zoom RTMS / cloud media streams.** Zoom streams meeting media to an endpoint
   you host; convert the incoming audio to 16 kHz mono PCM and yield it here.

Whichever route is chosen, pair the source with
:class:`~app.audio.whisper_transcriber.WhisperTranscriber` exactly as
:class:`~app.audio.file_source.FileAudioSource` is today.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

from app.audio.base import SAMPLE_RATE, AudioSource


class ZoomAudioSource(AudioSource):
    """Not implemented yet - see the module docstring for integration routes."""

    sample_rate = SAMPLE_RATE

    def __init__(self, *args: object, **kwargs: object) -> None:  # noqa: D401,ARG002
        raise NotImplementedError(
            "Zoom audio capture is not part of this MVP. Use FileAudioSource or "
            "MockTranscriber, or implement ZoomAudioSource.frames() following the "
            "routes in app/audio/zoom_source.py."
        )

    def frames(self) -> AsyncIterator[bytes]:  # pragma: no cover - unreachable
        raise NotImplementedError

"""faster-whisper implementation of :class:`~app.audio.base.Transcriber`.

Consumes PCM frames from an :class:`~app.audio.base.AudioSource`, buffers them
into fixed windows and transcribes each window in a worker thread (the model call
is blocking).  Whisper segments become :class:`~app.models.TranscriptChunk`
objects with timestamps shifted to their absolute position in the stream.

Windows are non-overlapping for simplicity; this can clip a word at a boundary
but is adequate for the MVP and keeps the logic easy to follow.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator

import numpy as np

from app.audio.base import SAMPLE_RATE, AudioSource, Transcriber
from app.config import settings
from app.models import TranscriptChunk

#: Seconds of audio transcribed per model call. Larger = better accuracy, more lag.
_WINDOW_SECONDS = 5.0


class WhisperTranscriber(Transcriber):
    """Transcribes an :class:`AudioSource` with a local faster-whisper model.

    Args:
        source: The audio source to consume.
        model_name: faster-whisper model id. Defaults to ``settings.whisper_model``.
        window_seconds: Audio buffered before each transcription call.
    """

    def __init__(
        self,
        source: AudioSource,
        *,
        model_name: str | None = None,
        window_seconds: float = _WINDOW_SECONDS,
    ) -> None:
        self._source = source
        self._model_name = model_name or settings.whisper_model
        self._window_samples = int(window_seconds * SAMPLE_RATE)
        self._model = None  # lazily constructed on first use

    def _ensure_model(self):
        """Construct the ``WhisperModel`` on first use (import kept local)."""
        if self._model is None:
            from faster_whisper import WhisperModel

            self._model = WhisperModel(self._model_name, device="cpu", compute_type="int8")
        return self._model

    def _transcribe_window(self, audio: np.ndarray, offset_s: float) -> list[TranscriptChunk]:
        """Blocking transcription of one float32 window; returns absolute-timed chunks."""
        model = self._ensure_model()
        segments, _info = model.transcribe(audio, language="en", vad_filter=True)
        chunks: list[TranscriptChunk] = []
        for segment in segments:
            text = segment.text.strip()
            if text:
                chunks.append(
                    TranscriptChunk(
                        text=text,
                        start=offset_s + float(segment.start),
                        end=offset_s + float(segment.end),
                    )
                )
        return chunks

    async def stream(self) -> AsyncIterator[TranscriptChunk]:
        """See :meth:`app.audio.base.Transcriber.stream`."""
        buffer = bytearray()
        processed_samples = 0

        async def flush() -> AsyncIterator[TranscriptChunk]:
            nonlocal buffer, processed_samples
            audio = np.frombuffer(bytes(buffer), dtype="<i2").astype(np.float32) / 32768.0
            offset_s = processed_samples / SAMPLE_RATE
            chunks = await asyncio.to_thread(self._transcribe_window, audio, offset_s)
            processed_samples += len(audio)
            buffer = bytearray()
            for chunk in chunks:
                yield chunk

        async for frame in self._source.frames():
            buffer.extend(frame)
            if len(buffer) >= self._window_samples * 2:  # 2 bytes per int16 sample
                async for chunk in flush():
                    yield chunk

        if buffer:
            async for chunk in flush():
                yield chunk

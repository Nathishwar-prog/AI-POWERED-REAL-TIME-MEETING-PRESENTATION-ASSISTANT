"""An :class:`~app.audio.base.AudioSource` backed by an audio file on disk.

Decodes a ``.wav`` / ``.flac`` / ``.ogg`` file with ``soundfile``, down-mixes to
mono, resamples to :data:`~app.audio.base.SAMPLE_RATE` and yields ~1-second PCM
frames paced in real time.  This is the "real STT, no Zoom" path: pair it with
:class:`~app.audio.whisper_transcriber.WhisperTranscriber`.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from pathlib import Path

import numpy as np

from app.audio.base import SAMPLE_RATE, AudioSource
from app.audio.pcm import float_to_pcm16_bytes, to_mono_16k

#: Emitted frame length in seconds.
_FRAME_SECONDS = 1.0


class FileAudioSource(AudioSource):
    """Streams an audio file as real-time PCM frames.

    Args:
        path: Path to a libsndfile-readable audio file.
        realtime: When ``True`` (default) sleep between frames so playback is
            wall-clock accurate. Set ``False`` in tests for instant iteration.
    """

    sample_rate = SAMPLE_RATE

    def __init__(self, path: str | Path, *, realtime: bool = True) -> None:
        self._path = Path(path)
        self._realtime = realtime

    async def frames(self) -> AsyncIterator[bytes]:
        """See :meth:`app.audio.base.AudioSource.frames`."""
        import soundfile as sf

        data, source_rate = sf.read(str(self._path), dtype="float32", always_2d=False)
        mono = to_mono_16k(np.asarray(data), int(source_rate))
        pcm16 = np.frombuffer(float_to_pcm16_bytes(mono), dtype="<i2")

        frame_len = int(_FRAME_SECONDS * SAMPLE_RATE)
        for start in range(0, len(pcm16), frame_len):
            frame = pcm16[start : start + frame_len]
            if frame.size == 0:
                break
            if self._realtime:
                await asyncio.sleep(_FRAME_SECONDS)
            yield frame.tobytes()

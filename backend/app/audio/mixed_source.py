"""Combine several :class:`~app.audio.base.AudioSource` streams into one.

Used for the "system audio + your microphone" capture option so the assistant
hears both the remote participants and the local presenter.  Frames from each
source are summed sample-wise; alignment is best-effort (the sources have
independent clocks), which is fine for speech recognition on ~5 s windows.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator

import numpy as np

from app.audio.base import SAMPLE_RATE, AudioSource

_END = object()  # sentinel put on a queue when a source is exhausted


class MixedAudioSource(AudioSource):
    """Sample-wise sum of two or more equal-rate PCM sources.

    Args:
        *sources: The sources to mix. All must emit 16 kHz mono ``int16`` PCM.
    """

    sample_rate = SAMPLE_RATE

    def __init__(self, *sources: AudioSource) -> None:
        if len(sources) < 2:
            raise ValueError("MixedAudioSource needs at least two sources")
        self._sources = sources

    async def frames(self) -> AsyncIterator[bytes]:
        """See :meth:`app.audio.base.AudioSource.frames`."""
        queues: list[asyncio.Queue] = [asyncio.Queue(maxsize=32) for _ in self._sources]

        async def pump(source: AudioSource, queue: asyncio.Queue) -> None:
            try:
                async for frame in source.frames():
                    await queue.put(frame)
            finally:
                await queue.put(_END)

        tasks = [asyncio.create_task(pump(s, q)) for s, q in zip(self._sources, queues)]
        try:
            while True:
                chunks = [await q.get() for q in queues]
                if any(c is _END for c in chunks):
                    return
                arrays = [np.frombuffer(c, dtype="<i2").astype(np.int32) for c in chunks]
                width = min(a.size for a in arrays)
                mixed = np.clip(sum(a[:width] for a in arrays), -32768, 32767).astype("<i2")
                yield mixed.tobytes()
        finally:
            for task in tasks:
                task.cancel()

"""Interfaces for audio input and speech-to-text.

Two small abstractions keep the rest of the system independent of Zoom:

* :class:`AudioSource` - yields raw PCM audio frames from *somewhere*
  (a file today, a Zoom bot later).
* :class:`Transcriber` - yields :class:`~app.models.TranscriptChunk` objects.

A transcriber may wrap an :class:`AudioSource` (real STT) or produce chunks
directly (the scripted mock).  Both are async so a live source never blocks the
event loop.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator

from app.models import TranscriptChunk

#: PCM sample rate every :class:`AudioSource` in this project produces.
SAMPLE_RATE = 16_000


class AudioSource(ABC):
    """A source of 16-bit, mono, ``SAMPLE_RATE`` PCM audio frames."""

    #: Sample rate of the frames produced by :meth:`frames`.
    sample_rate: int = SAMPLE_RATE

    @abstractmethod
    def frames(self) -> AsyncIterator[bytes]:
        """Yield little-endian ``int16`` PCM byte chunks until the audio ends."""
        raise NotImplementedError


class Transcriber(ABC):
    """Turns audio (or a script) into a stream of transcript chunks."""

    @abstractmethod
    def stream(self) -> AsyncIterator[TranscriptChunk]:
        """Yield :class:`~app.models.TranscriptChunk` objects in time order."""
        raise NotImplementedError

"""Tests for :class:`app.audio.mixed_source.MixedAudioSource`."""

from __future__ import annotations

from collections.abc import AsyncIterator

import numpy as np
import pytest

from app.audio.base import AudioSource
from app.audio.mixed_source import MixedAudioSource


class _CannedSource(AudioSource):
    def __init__(self, frames: list[bytes]) -> None:
        self._frames = frames

    async def frames(self) -> AsyncIterator[bytes]:
        for frame in self._frames:
            yield frame


def _pcm(*values: int) -> bytes:
    return np.array(values, dtype="<i2").tobytes()


async def _collect(source: AudioSource) -> list[bytes]:
    return [frame async for frame in source.frames()]


async def test_frames_are_summed_sample_wise() -> None:
    a = _CannedSource([_pcm(100, 200), _pcm(1, 2)])
    b = _CannedSource([_pcm(10, 20), _pcm(3, 4)])
    out = await _collect(MixedAudioSource(a, b))
    assert [np.frombuffer(f, dtype="<i2").tolist() for f in out] == [[110, 220], [4, 6]]


async def test_stops_when_the_shorter_source_ends() -> None:
    a = _CannedSource([_pcm(1), _pcm(2), _pcm(3)])
    b = _CannedSource([_pcm(10)])
    out = await _collect(MixedAudioSource(a, b))
    assert len(out) == 1


async def test_summation_is_clipped_to_int16_range() -> None:
    a = _CannedSource([_pcm(30000)])
    b = _CannedSource([_pcm(30000)])
    out = await _collect(MixedAudioSource(a, b))
    assert np.frombuffer(out[0], dtype="<i2")[0] == 32767


def test_requires_at_least_two_sources() -> None:
    with pytest.raises(ValueError):
        MixedAudioSource(_CannedSource([]))

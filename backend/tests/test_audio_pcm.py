"""Tests for :mod:`app.audio.pcm` and the transcriber factory's audio sources."""

from __future__ import annotations

import numpy as np

from app.audio.base import SAMPLE_RATE
from app.audio.pcm import float_to_pcm16_bytes, to_mono_16k


def test_to_mono_16k_downmixes_stereo() -> None:
    stereo = np.zeros((100, 2), dtype=np.float32)
    stereo[:, 0] = 1.0
    stereo[:, 1] = -1.0
    mono = to_mono_16k(stereo, SAMPLE_RATE)
    assert mono.ndim == 1
    assert np.allclose(mono, 0.0)


def test_to_mono_16k_resamples_length() -> None:
    one_second_48k = np.zeros(48_000, dtype=np.float32)
    out = to_mono_16k(one_second_48k, 48_000)
    assert abs(len(out) - SAMPLE_RATE) <= 1


def test_float_to_pcm16_bytes_is_two_bytes_per_sample_and_clipped() -> None:
    signal = np.array([0.0, 1.0, -1.0, 2.0, -2.0], dtype=np.float32)
    raw = float_to_pcm16_bytes(signal)
    assert len(raw) == 2 * len(signal)
    ints = np.frombuffer(raw, dtype="<i2")
    assert ints[1] == 32767 and ints[3] == 32767  # +1.0 and +2.0 both clip high
    assert ints[2] == -32767 and ints[4] == -32767  # -1.0 and -2.0 both clip low


def test_build_transcriber_accepts_loopback_without_opening_a_device() -> None:
    from app.audio.whisper_transcriber import WhisperTranscriber
    from app.runtime import _build_transcriber

    transcriber = _build_transcriber("loopback", None)
    assert isinstance(transcriber, WhisperTranscriber)

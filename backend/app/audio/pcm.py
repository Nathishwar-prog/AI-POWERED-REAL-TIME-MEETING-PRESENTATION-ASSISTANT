"""Small PCM conversion helpers shared by the audio sources.

Every :class:`~app.audio.base.AudioSource` must emit little-endian 16-bit mono
PCM at :data:`~app.audio.base.SAMPLE_RATE`.  Real inputs (files, sound devices,
Zoom) rarely arrive in that exact shape, so these helpers do the down-mix,
resample and int16 packing in one place.
"""

from __future__ import annotations

import numpy as np

from app.audio.base import SAMPLE_RATE


def to_mono_16k(samples: np.ndarray, source_rate: int) -> np.ndarray:
    """Down-mix to mono and linearly resample to :data:`SAMPLE_RATE`.

    Args:
        samples: 1-D ``(n,)`` or 2-D ``(n, channels)`` float array.
        source_rate: Sample rate of ``samples`` in Hz.

    Returns:
        A 1-D float32 array at :data:`SAMPLE_RATE`.
    """
    if samples.ndim == 2:
        samples = samples.mean(axis=1)
    if source_rate != SAMPLE_RATE and samples.shape[0] > 0:
        target_len = int(samples.shape[0] / source_rate * SAMPLE_RATE)
        if target_len > 0:
            old_x = np.linspace(0.0, 1.0, num=samples.shape[0], endpoint=False)
            new_x = np.linspace(0.0, 1.0, num=target_len, endpoint=False)
            samples = np.interp(new_x, old_x, samples)
    return samples.astype(np.float32)


def float_to_pcm16_bytes(mono: np.ndarray) -> bytes:
    """Clip a mono float32 signal to [-1, 1] and pack it as little-endian int16."""
    clipped = np.clip(mono, -1.0, 1.0)
    return (clipped * 32767.0).astype("<i2").tobytes()

"""Live audio capture for the ``loopback`` source.

Two capture modes, both yielding 16 kHz mono PCM:

* **System audio (default)** — a WASAPI *loopback* recording of the current
  output device via the :mod:`soundcard` library, i.e. exactly what you hear (the
  other meeting participants). No "Stereo Mix" and no virtual cable, and it works
  with Bluetooth headsets. Windows/macOS.
* **A named input device** — a microphone, "Stereo Mix", or a virtual-cable input,
  captured via :mod:`sounddevice`, selected by name substring or index.

Pair either with :class:`~app.audio.whisper_transcriber.WhisperTranscriber`.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncIterator

import numpy as np

from app.audio.base import SAMPLE_RATE, AudioSource
from app.audio.pcm import float_to_pcm16_bytes, to_mono_16k

logger = logging.getLogger(__name__)

#: Capture block length in seconds (also the approximate yield cadence).
_BLOCK_SECONDS = 0.5
#: Never capture more than this many channels even if the device offers more.
_MAX_CHANNELS = 2
#: Host APIs worth showing on Windows - MME and WASAPI are the reliable ones;
#: DirectSound / WDM-KS mostly duplicate them and WDM-KS often fails to open.
_GOOD_HOSTAPIS = ("MME", "Windows WASAPI", "Core Audio", "ALSA")

#: Sentinel/blank device meaning "capture system output".
SYSTEM_OUTPUT = ""
#: Sentinel meaning "system output + the default microphone, mixed".
SYSTEM_PLUS_MIC = "both"


def list_input_devices() -> list[dict]:
    """Return selectable capture options as ``{value, name, channels, rate, hostapi}``.

    ``value`` is what to send as ``path`` to ``/api/session/start``.  Two synthetic
    entries come first ("System audio", "System audio + your microphone"); then
    real input devices, trimmed to reliable host APIs and de-duplicated by name so
    the UI dropdown stays short.
    """
    import sounddevice as sd

    devices: list[dict] = [
        {
            "value": SYSTEM_OUTPUT,
            "name": "System audio — what you hear (recommended)",
            "channels": 1,
            "rate": SAMPLE_RATE,
            "hostapi": "loopback",
        },
        {
            "value": SYSTEM_PLUS_MIC,
            "name": "System audio + your microphone",
            "channels": 1,
            "rate": SAMPLE_RATE,
            "hostapi": "loopback+mic",
        },
    ]
    seen: set[str] = set()
    hostapis = sd.query_hostapis()
    for info in sd.query_devices():
        if info["max_input_channels"] <= 0:
            continue
        api = str(hostapis[info["hostapi"]]["name"])
        if api not in _GOOD_HOSTAPIS or info["name"] in seen:
            continue
        seen.add(info["name"])
        devices.append(
            {
                "value": info["name"],
                "name": info["name"],
                "channels": info["max_input_channels"],
                "rate": int(info["default_samplerate"]),
                "hostapi": api,
            }
        )
    return devices


def default_input_index() -> int:
    """Index of the system default input device (for the mixed capture mode)."""
    import sounddevice as sd

    return int(sd.query_devices(kind="input")["index"])


class LoopbackAudioSource(AudioSource):
    """Streams live audio as 16 kHz mono PCM frames.

    Args:
        device: ``None`` / ``""`` → capture system output (loopback). Otherwise an
            input-device name substring or integer index.
        block_seconds: Capture block size; smaller = lower latency, more wake-ups.
    """

    sample_rate = SAMPLE_RATE

    def __init__(
        self, device: str | int | None = None, *, block_seconds: float = _BLOCK_SECONDS
    ) -> None:
        self._device = None if device in (None, SYSTEM_OUTPUT) else device
        self._system_output = self._device is None
        self._block_seconds = block_seconds

    async def frames(self) -> AsyncIterator[bytes]:
        """See :meth:`app.audio.base.AudioSource.frames`."""
        if self._system_output:
            async for frame in self._system_frames():
                yield frame
        else:
            async for frame in self._device_frames():
                yield frame

    # -- system output (soundcard WASAPI/CoreAudio loopback) --------------
    async def _system_frames(self) -> AsyncIterator[bytes]:
        import soundcard as sc

        speaker = sc.default_speaker()
        loopback_mic = sc.get_microphone(speaker.name, include_loopback=True)
        block = int(self._block_seconds * SAMPLE_RATE)
        logger.info("loopback capture: system output '%s' [loopback]", speaker.name)

        recorder = loopback_mic.recorder(samplerate=SAMPLE_RATE, channels=1, blocksize=block)
        recorder.__enter__()
        try:
            while True:
                data = await asyncio.to_thread(recorder.record, block)
                yield float_to_pcm16_bytes(np.asarray(data).reshape(-1))
        finally:
            recorder.__exit__(None, None, None)

    # -- named input device (sounddevice) --------------------------------
    async def _device_frames(self) -> AsyncIterator[bytes]:
        import sounddevice as sd

        info = sd.query_devices(self._device, "input")
        source_rate = int(info["default_samplerate"])
        channels = min(int(info["max_input_channels"]), _MAX_CHANNELS) or 1
        logger.info("loopback capture: input '%s' (%d Hz, %d ch)", info["name"], source_rate, channels)

        loop = asyncio.get_running_loop()
        queue: asyncio.Queue[bytes] = asyncio.Queue(maxsize=64)

        def on_audio(indata, _frames, _time, status) -> None:  # PortAudio thread
            if status:
                logger.debug("sounddevice status: %s", status)
            pcm = float_to_pcm16_bytes(to_mono_16k(indata.copy(), source_rate))
            try:
                loop.call_soon_threadsafe(queue.put_nowait, pcm)
            except RuntimeError:
                pass  # event loop is shutting down

        stream = sd.InputStream(
            samplerate=source_rate,
            channels=channels,
            dtype="float32",
            blocksize=int(self._block_seconds * source_rate),
            device=info["index"],
            callback=on_audio,
        )
        with stream:
            while True:
                yield await queue.get()

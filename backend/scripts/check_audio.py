"""Measure the live level of a capture source.

Run from the ``backend/`` directory::

    python -m scripts.check_audio                 # system audio (what you hear)
    python -m scripts.check_audio "Stereo Mix"    # a named input device
    python -m scripts.check_audio 7                # an input device by index

Play some meeting audio (or speak, for a mic) during the check. If the level
stays at "-- silent --" that source receives no sound and the assistant will
never transcribe from it.
"""

from __future__ import annotations

import asyncio
import math
import sys
import time

import numpy as np

from app.audio.loopback_source import LoopbackAudioSource

_SECONDS = 8.0
_SILENCE_DBFS = -60.0


async def _run(device: str | int | None) -> int:
    source = LoopbackAudioSource(device, block_seconds=0.25)
    peak_overall = 0.0
    deadline = time.monotonic() + _SECONDS
    print(f"listening for {_SECONDS:.0f}s — make some noise...\n")

    async for frame in source.frames():
        samples = np.frombuffer(frame, dtype="<i2").astype(np.float32) / 32768.0
        peak = float(np.abs(samples).max()) if samples.size else 0.0
        peak_overall = max(peak_overall, peak)
        dbfs = 20 * math.log10(peak) if peak > 1e-7 else -120.0
        bar = "#" * max(0, int((dbfs + 60) / 2))
        print("  -- silent --" if dbfs < _SILENCE_DBFS else f"  {dbfs:6.1f} dBFS {bar}")
        if time.monotonic() > deadline:
            break

    print()
    if peak_overall < 10 ** (_SILENCE_DBFS / 20):
        print("RESULT: SILENT — this source receives no audio.")
        if device in (None, ""):
            print("  Make sure meeting audio is actually playing on the current")
            print("  Windows output device while the check runs.")
        else:
            print("  Pick a different device, or use 'System audio' (no argument).")
        return 1
    print("RESULT: signal detected — this source works for the loopback source.")
    return 0


def main() -> int:
    arg = sys.argv[1] if len(sys.argv) > 1 else None
    device: str | int | None = int(arg) if arg and arg.isdigit() else arg
    return asyncio.run(_run(device))


if __name__ == "__main__":
    raise SystemExit(main())

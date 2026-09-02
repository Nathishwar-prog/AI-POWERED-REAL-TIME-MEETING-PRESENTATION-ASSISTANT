"""List the input audio devices available for the ``loopback`` source.

Usage (from the ``backend/`` directory)::

    python -m scripts.list_audio_devices

Send a row's ``value`` as the ``path`` field of ``POST /api/session/start`` when
``source`` is ``loopback`` (it is also what the UI dropdown submits).
"""

from __future__ import annotations

from app.audio.loopback_source import list_input_devices


def main() -> int:
    devices = list_input_devices()
    if not devices:
        print("No input devices found.")
        return 1
    width = max(len(d["name"]) for d in devices)
    for device in devices:
        value = device["value"] or "(blank)"
        print(
            f"{device['name']:<{width}}  {device['channels']} ch  "
            f"{device['rate']} Hz   value={value!r}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""A scripted :class:`~app.audio.base.Transcriber` for tests and demos.

Reads a plain-text file and emits one :class:`~app.models.TranscriptChunk` per
non-empty line, with a short pause between lines so the pipeline behaves as it
would during a live meeting.  No model download, no audio libraries, no API key.

Line format (all parts optional except the text)::

    Alice: What is the refund window? @12.5

* ``Alice:``  -> speaker label (defaults to ``"participant"``)
* ``@12.5``   -> stream timestamp in seconds (defaults to an auto-incrementing clock)
* lines beginning with ``#`` are treated as comments and skipped
"""

from __future__ import annotations

import asyncio
import re
from collections.abc import AsyncIterator
from pathlib import Path

from app.audio.base import Transcriber
from app.models import TranscriptChunk

#: Simulated wall-clock pause between scripted lines (seconds).
_LINE_DELAY_S = 0.6
#: Assumed spoken duration of one line when no explicit timestamp is given.
_LINE_DURATION_S = 2.5

_SPEAKER_RE = re.compile(r"^(?P<speaker>[A-Za-z][\w '-]{0,40}):\s+(?P<rest>.*)$")
_TIMESTAMP_RE = re.compile(r"\s*@(?P<ts>\d+(?:\.\d+)?)\s*$")


class MockTranscriber(Transcriber):
    """Replays transcript lines from ``script_path`` on a simulated clock.

    Args:
        script_path: Path to the script file.
        line_delay_s: Real seconds to sleep between emitted lines.
    """

    def __init__(self, script_path: str | Path, line_delay_s: float = _LINE_DELAY_S) -> None:
        self._script_path = Path(script_path)
        self._line_delay_s = line_delay_s

    def _parse_line(self, line: str, fallback_start: float) -> TranscriptChunk | None:
        """Parse one raw line into a chunk, or ``None`` for blanks/comments."""
        text = line.strip()
        if not text or text.startswith("#"):
            return None

        speaker = "participant"
        if match := _SPEAKER_RE.match(text):
            speaker = match.group("speaker")
            text = match.group("rest").strip()

        start = fallback_start
        if match := _TIMESTAMP_RE.search(text):
            start = float(match.group("ts"))
            text = text[: match.start()].strip()

        if not text:
            return None
        return TranscriptChunk(
            text=text, start=start, end=start + _LINE_DURATION_S, speaker=speaker
        )

    async def stream(self) -> AsyncIterator[TranscriptChunk]:
        """See :meth:`app.audio.base.Transcriber.stream`."""
        lines = self._script_path.read_text(encoding="utf-8").splitlines()
        clock = 0.0
        for raw in lines:
            chunk = self._parse_line(raw, fallback_start=clock)
            if chunk is None:
                continue
            await asyncio.sleep(self._line_delay_s)
            yield chunk
            clock = chunk.end + 1.0

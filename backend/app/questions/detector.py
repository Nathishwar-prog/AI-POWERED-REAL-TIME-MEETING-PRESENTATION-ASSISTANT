"""Rule-based detection of "the speaker wants information".

Transcribed speech often loses its question mark, and in meetings people ask for
things without grammatical questions at all ("tell me about the refund policy",
"walk us through pricing").  :func:`is_question` therefore treats both real
questions *and* information-request imperatives as a hit, using a handful of
cheap signals - trailing ``?``, a leading interrogative / auxiliary verb, a
leading request verb, and common request phrases.  It is a pure function: no
I/O, easy to unit test.
"""

from __future__ import annotations

import re

#: WH-words and other interrogatives that, in first position, signal a question.
_INTERROGATIVES = frozenset(
    {"who", "what", "when", "where", "why", "how", "which", "whose", "whom"}
)

#: Auxiliary / modal verbs that front a yes-no question ("can you...", "is it...").
_AUXILIARIES = frozenset(
    {
        "is", "are", "am", "was", "were", "do", "does", "did", "can", "could",
        "would", "should", "will", "shall", "has", "have", "had", "may", "might",
    }
)

#: Subject words expected after a fronted auxiliary in a genuine question.
_SUBJECTS = frozenset(
    {
        "i", "you", "we", "they", "he", "she", "it", "this", "that", "these",
        "those", "there", "the", "a", "an", "my", "your", "our", "their", "any",
        "some", "someone", "anyone", "everyone",
    }
)

#: Verbs that, when they start an utterance, make it an information request
#: ("explain the refund flow", "summarize the pricing").
_REQUEST_VERBS = frozenset(
    {"explain", "describe", "clarify", "elaborate", "summarize", "summarise", "define"}
)

#: Multi-word cues that indicate an information request regardless of structure.
_REQUEST_PHRASES = (
    "can you explain",
    "could you explain",
    "can you clarify",
    "could you clarify",
    "can you tell",
    "tell me about",
    "tell us about",
    "tell me more",
    "tell us more",
    "talk about",
    "talk us through",
    "walk me through",
    "walk us through",
    "go over",
    "give me an overview",
    "give us an overview",
    "give me a rundown",
    "more on",
    "what about",
    "how about",
    "i have a question",
    "quick question",
    "any thoughts on",
    "any idea",
    "what if",
    "i'd like to know",
    "i would like to know",
    "i want to know",
    "let me know",
    "curious about",
    "wondering about",
    "wondering if",
)

_WORD_RE = re.compile(r"[a-z']+")
_MIN_WORDS = 3


def _words(text: str) -> list[str]:
    """Lowercased alphabetic tokens of ``text``."""
    return _WORD_RE.findall(text.lower())


def is_question(text: str) -> bool:
    """Return ``True`` when ``text`` reads as a question.

    Args:
        text: A single assembled utterance.

    Returns:
        ``True`` if any question signal fires; ``False`` otherwise (including for
        very short fragments of fewer than three words).
    """
    stripped = (text or "").strip()
    if not stripped:
        return False

    if stripped.endswith("?"):
        return True

    lowered = stripped.lower()
    if any(phrase in lowered for phrase in _REQUEST_PHRASES):
        return True

    tokens = _words(stripped)
    if len(tokens) < _MIN_WORDS:
        return False

    first = tokens[0]
    if first in _INTERROGATIVES:
        return True

    if first in _REQUEST_VERBS:
        return True

    if first == "tell" and len(tokens) > 1 and tokens[1] in {"me", "us"}:
        return True

    if first in _AUXILIARIES and any(tok in _SUBJECTS for tok in tokens[1:4]):
        return True

    return False

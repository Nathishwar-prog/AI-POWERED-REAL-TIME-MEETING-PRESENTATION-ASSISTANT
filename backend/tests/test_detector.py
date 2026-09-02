"""Tests for :mod:`app.questions.detector`."""

from __future__ import annotations

import pytest

from app.questions.detector import is_question

QUESTIONS = [
    "What is the refund window?",
    "how long does shipping take",  # no question mark, WH-word lead
    "Can you clarify the support hours",  # request phrase
    "Is there an express option for delivery",  # auxiliary + subject
    "Do we offer refunds on digital goods",
    "I have a question about billing",
    "tell me about the refund policy",  # imperative request
    "Tell us about the pricing tiers",
    "explain the onboarding process",  # leading request verb
    "walk me through the security section",
    "go over the roadmap for me",
    "I'd like to know more about the Team plan",
]

NOT_QUESTIONS = [
    "Thanks, that makes sense.",
    "The refund window is thirty days.",
    "Let's move on to the next slide.",
    "Right.",  # too short
    "So the shipping team handles that.",
    "Tell everyone the meeting starts at noon.",  # "tell" not followed by me/us
]


@pytest.mark.parametrize("text", QUESTIONS)
def test_detects_questions(text: str) -> None:
    assert is_question(text) is True


@pytest.mark.parametrize("text", NOT_QUESTIONS)
def test_ignores_statements(text: str) -> None:
    assert is_question(text) is False


def test_blank_input_is_not_a_question() -> None:
    assert is_question("") is False
    assert is_question("   ") is False

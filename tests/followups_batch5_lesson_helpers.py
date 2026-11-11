"""What other test files use from ``tests/test_followups_batch5_lesson.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations


class _MeteredRequest:
    """A physical metered request (an OpenRouter-like client with no owner price)."""

    provider_name = "openrouter_test"
    provider_type = "openrouter"


def lesson_envelope_refuses(_context):
    """The figure author's physical request goes through the active request gates: with a per-lesson cap
    and no price, the LESSON's envelope refuses it (``refusal`` recorded) before anything is sent."""

    from learnloop.ai.execution import model_call

    with model_call(_MeteredRequest(), purpose="figure_author", prompt="draw it"):
        raise AssertionError("the lesson's envelope admitted a request it should refuse")

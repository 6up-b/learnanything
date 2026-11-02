"""Reader RW5d P5: what the learner is waiting for now (spec_reader_show_me_figures_v1 §10b.4, "Yield to the learner").

A process-wide count of foreground work in flight: a pressed figure, a lesson
turn, a tutor answer, a grading call. The sidecar marks each one with
:func:`foreground`; the prefetch service never starts a prebuild while
:func:`busy` is true, and pauses its queue at the next build while it is.
A prebuild already running continues (a render niced). Pure bookkeeping: no
vault, no model, never evidence; a neutral module so the sidecar and the
figure handlers mark work without importing the prefetch service.
"""

from __future__ import annotations

import threading
import time
from collections import Counter
from collections.abc import Callable, Iterator
from contextlib import contextmanager

_LOCK = threading.Lock()
_IN_FLIGHT: Counter[str] = Counter()
_IDLE = threading.Condition(_LOCK)


@contextmanager
def foreground(kind: str) -> Iterator[None]:
    """Mark one piece of foreground work (``kind``: a figure, a lesson turn, a tutor answer, grading)."""

    with _LOCK:
        _IN_FLIGHT[kind] += 1
    try:
        yield
    finally:
        with _LOCK:
            _IN_FLIGHT[kind] -= 1
            if _IN_FLIGHT[kind] <= 0:
                del _IN_FLIGHT[kind]
            if not _IN_FLIGHT:
                _IDLE.notify_all()


def busy() -> bool:
    with _LOCK:
        return bool(_IN_FLIGHT)


def in_flight() -> dict[str, int]:
    with _LOCK:
        return dict(_IN_FLIGHT)


def wait_idle(timeout: float, *, cancelled: Callable[[], bool] | None = None, poll: float = 0.5) -> bool:
    """Wait up to ``timeout`` seconds for no foreground work; True when idle.
    ``cancelled()`` (a close, a switch) ends the wait early with False."""

    deadline = time.monotonic() + max(0.0, timeout)
    with _LOCK:
        while _IN_FLIGHT:
            if cancelled is not None and cancelled():
                return False
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return False
            _IDLE.wait(min(poll, remaining))
        return True


#: The sidecar methods that are foreground work while they run (a pressed
#: figure's own build job is marked where it runs, by the figure handler).
FOREGROUND_METHODS: dict[str, str] = {
    "figure.request": "figure", "reader.figure_request": "figure", "reader.figure_revise": "figure",
    "figure.rich_retry": "figure", "figure.take_step": "figure",
    "lesson.turn": "lesson",
    "ask_tutor_question": "tutor", "reader.ask": "tutor", "reader.library_ask": "tutor",
    "reader.library_ask_tutor": "tutor",
    "submit_attempt": "grading", "submit_exam_answer": "grading", "submit_teach_back_turn": "grading",
    "submit_eliciting_response": "grading", "submit_dont_know": "grading",
}


__all__ = ["FOREGROUND_METHODS", "busy", "foreground", "in_flight", "wait_idle"]

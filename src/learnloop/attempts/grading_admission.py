"""Optional spend admission around each practice grading call.

The practice door's grading calls (each blind sample, each joint sample) run
inside :func:`admit_grading_call`. Nothing is installed by default, so the
desktop, TUI and sidecar doors behave exactly as before. A COMMAND that grades
(``learnloop attempt``) installs a guard with :func:`grading_admission`: the
guard is a context manager factory ``guard(purpose, prompt)`` that admits the
call against the command's caps before it is sent (Slice A §5.6; the Phase 1
spend framework, ``learnloop.ai.spend``) and meters it afterwards. A refusal
raises before anything is sent.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator
from contextlib import AbstractContextManager, contextmanager
from contextvars import ContextVar
from typing import Any

Guard = Callable[[str, str], AbstractContextManager[Any]]

_GUARD: ContextVar[Guard | None] = ContextVar("learnloop_grading_admission", default=None)


@contextmanager
def grading_admission(guard: Guard | None) -> Iterator[None]:
    """Admit every practice grading call made inside this block through ``guard``."""

    token = _GUARD.set(guard)
    try:
        yield
    finally:
        _GUARD.reset(token)


@contextmanager
def admit_grading_call(purpose: str, prompt: str) -> Iterator[None]:
    """Wrap ONE logical grading call (one sample); a no-op without a guard."""

    guard = _GUARD.get()
    if guard is None:
        yield
        return
    with guard(purpose, prompt):
        yield


def estimated_prompt_tokens(prompt: str) -> int:
    """The same bytes/4 input estimate the diagnosis plans use."""

    return (len(prompt.encode("utf-8")) + 3) // 4


__all__ = ["Guard", "admit_grading_call", "estimated_prompt_tokens", "grading_admission"]

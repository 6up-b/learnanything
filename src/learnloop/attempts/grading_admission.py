"""Optional spend admission around each practice grading call.

The practice door's grading calls (each blind sample, each joint sample, and
``mvp-0.15``'s proof-like reading and route check) run inside
:func:`admit_grading_call`. Nothing is installed by default, so the desktop,
TUI and sidecar doors behave exactly as before. A COMMAND that grades
(``learnloop attempt``) installs a guard with :func:`grading_admission`: the
guard is a context manager factory ``guard(purpose, prompt, route=, client=)``
that admits the call against the command's caps before it is sent (Slice A
§5.6; the Phase 1 spend framework, ``learnloop.ai.spend``) and meters it
afterwards, on the named spend ``route`` (``grading``, or ``proof_check`` for
the route check, whose client may bill differently; review F3). A refusal
raises before anything is sent.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator
from contextlib import AbstractContextManager, contextmanager
from contextvars import ContextVar
from typing import Any

Guard = Callable[..., AbstractContextManager[Any]]
#: The spend route of the grader's own calls.
GRADING_ROUTE = "grading"

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
def admit_grading_call(
    purpose: str, prompt: str, *, route: str = GRADING_ROUTE, client: Any = None,
) -> Iterator[None]:
    """Wrap ONE logical grading call (one sample); a no-op without a guard.

    ``route`` names the spend route the call is admitted on and ``client`` the
    client that will send it, so a guard can classify a route it has not seen
    (metered or subscription) before admitting it.
    """

    guard = _GUARD.get()
    if guard is None:
        yield
        return
    with guard(purpose, prompt, route=route, client=client):
        yield


def estimated_prompt_tokens(prompt: str) -> int:
    """The same bytes/4 input estimate the diagnosis plans use."""

    return (len(prompt.encode("utf-8")) + 3) // 4


__all__ = ["GRADING_ROUTE", "Guard", "admit_grading_call", "estimated_prompt_tokens", "grading_admission"]

"""Close the background owners a test constructs, at the test's end.

A test that builds a :class:`~learnloop_sidecar.context.SidecarContext` (or a
bare ingest host or post-attempt worker) stands in for a sidecar process; the
process would stop them on ``shutdown`` or EOF (``SidecarContext.close``), but
a test that just returns used to leave their threads polling its vault for the
rest of the run (test-thread-leak: ~5 threads per test, ~800 in one xdist
worker). Rather than edit two hundred construction sites, the classes'
constructors record each instance a *test module* constructs (the caller's
frame is under ``tests/``), and the autouse ``close_test_background_owners``
fixture in ``conftest.py`` closes them when the test ends.

Only instances constructed directly by test code are closed here. One that
production code builds (a host building its own contexts, a context's own
ingest host) is its owner's to stop, so a production owner without a stop
path still fails the thread-leak guard (``tests/thread_guard.py``).
"""
from __future__ import annotations

import functools
import importlib
import sys
import weakref
from dataclasses import dataclass
from pathlib import Path

_TESTS_DIR = str(Path(__file__).resolve().parent) + "/"

# (module, class, the method that stops every thread the instance owns, and
# the (attribute, stop method) pairs of the parts that own threads)
OWNERS: tuple[tuple[str, str, str, tuple[tuple[str, str], ...]], ...] = (
    ("learnloop_sidecar.context", "SidecarContext", "close", (
        ("ingest_jobs", "shutdown"), ("post_attempt_worker", "shutdown"),
        ("exam_grading", "shutdown"), ("map_builds", "close"), ("background_jobs", "close"))),
    ("learnloop.content.pipeline.jobs", "DurableIngestJobs", "shutdown", ()),
    ("learnloop_sidecar.post_attempt_worker", "PostAttemptWorker", "shutdown", ()),
    ("learnloop_sidecar.exam_grading", "ExamGradingManager", "shutdown", ()),
)


@dataclass
class _Constructed:
    # A weak reference: recording an instance must not keep it alive (a test
    # may drop its host and check that the host's threads end on their own).
    instance: weakref.ref
    stop: str
    # Its thread-owning parts, held strongly: a test that drops a context
    # (rebinding a fresh one, say) still has that context's threads stopped,
    # since a running thread keeps its part alive anyway.
    parts: list[tuple[object, str]]


_constructed: list[_Constructed] = []


def _record(cls, stop: str, parts: tuple[tuple[str, str], ...]) -> None:
    original = cls.__init__
    if getattr(original, "_records_test_instances", False):
        return

    @functools.wraps(original)
    def __init__(self, *args, **kwargs):
        original(self, *args, **kwargs)
        caller = sys._getframe(1).f_code.co_filename
        if caller.startswith(_TESTS_DIR) and not any(seen.instance() is self for seen in _constructed):
            _constructed.append(_Constructed(weakref.ref(self), stop,
                                             [(getattr(self, name), method) for name, method in parts]))

    __init__._records_test_instances = True  # type: ignore[attr-defined]
    cls.__init__ = __init__


def install() -> None:
    for module_name, class_name, stop, parts in OWNERS:
        _record(getattr(importlib.import_module(module_name), class_name), stop, parts)


def mark() -> int:
    return len(_constructed)


def close_since(start: int) -> None:
    """Stop what test code constructed since ``start``, newest first."""

    owners = _constructed[start:]
    del _constructed[start:]
    errors: list[BaseException] = []
    for owner in reversed(owners):
        instance = owner.instance()
        stops = [] if instance is None else [getattr(instance, owner.stop)]
        stops += [getattr(part, method) for part, method in owner.parts]
        for stop in stops:
            try:
                stop()
            except BaseException as exc:  # noqa: BLE001 - close the rest, then report
                errors.append(exc)
    if errors:
        raise errors[0]

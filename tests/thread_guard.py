"""Thread-leak guard: a test that leaves a thread running fails, naming it.

Loaded by ``tests/conftest.py`` (``pytest_plugins``). Every ``Thread.start``
in the test process records which test, phase and fixture started it, and a
stack of where; after each test's teardown (and after each wider-scoped
fixture's finalizer) every thread that the finished owner started and that is
still alive gets a short bounded join, and any survivor fails the test's
teardown with its name, target, CPU time and creation stack.

Why: in the landing full suite one xdist worker collected ~800 leaked threads
that busy-polled (~17 cores, load average 400+) until the run stalled. A
thread that outlives the test that started it is either a production
ownership bug (a background owner with no stop/close path) or a test that
forgot to close what it started; either way the next thousand tests pay for
it. Daemon threads are not exempt: a daemon that keeps running after its test
still burns the worker.

Ownership is by scope. A thread started during a test's call or a
function-scoped fixture belongs to that test; one started while a module-,
class-, package- or session-scoped fixture was being set up belongs to that
fixture and is checked when the fixture finalizes. Threads started outside any
test (import time, collection, xdist's own channel) are process-level and not
checked.

``ALLOWED`` is the reviewed allowlist of process-lifetime singletons: each
entry names the creation site and why living for the whole process is the
design. Keep it short; anything that can be stopped should be.

Diagnostics: ``LEARNLOOP_THREAD_LEAK_REPORT=<file>`` appends one JSON line per
leaking test (with the full creation stacks and each thread's CPU seconds)
and reports instead of failing, so a whole shard can be surveyed in one run.
"""
from __future__ import annotations

import json
import os
import sys
import threading
import time
import traceback
from dataclasses import dataclass, field

import pytest

# The join grace a finished owner's threads get before they count as leaked
# (a guardrail, not a model parameter): long enough for a worker that was
# told to stop to notice its Event and return, short enough that a real leak
# costs the suite little.
JOIN_GRACE_SECONDS = 2.0

REPORT_ENV = "LEARNLOOP_THREAD_LEAK_REPORT"
GRACE_ENV = "LEARNLOOP_THREAD_LEAK_GRACE"


@dataclass(frozen=True)
class Allowed:
    """A process-lifetime singleton thread, reviewed."""

    # A substring of a frame "path:function" in the creation stack.
    site: str
    reason: str


# Reviewed allowlist (see the module docstring). Empty by design until a
# documented process-lifetime singleton needs an entry.
ALLOWED: tuple[Allowed, ...] = ()


@dataclass
class _Origin:
    nodeid: str | None
    phase: str | None
    # The non-function fixture being set up when the thread started (its
    # FixtureDef), or None when the test owns the thread.
    fixturedef: object | None
    stack: traceback.StackSummary
    started_at: float = field(default_factory=time.monotonic)
    reported: bool = False


_current_nodeid: str | None = None
_current_phase: str | None = None
# Stack of fixture setups in progress (non-function scope ones only matter).
_fixture_stack: list[object] = []
_origins: dict[threading.Thread, _Origin] = {}
_origins_lock = threading.Lock()
_pending_failures: list[str] = []

_real_start = threading.Thread.start


def _recording_start(self, *args, **kwargs):
    # A thread started by a tracked thread belongs to that thread's owner
    # (a leaked worker spawning more must not be charged to a later test).
    with _origins_lock:
        parent = _origins.get(threading.current_thread())
    if parent is not None:
        nodeid, phase, owner = parent.nodeid, parent.phase, parent.fixturedef
    else:
        nodeid, phase = _current_nodeid, _current_phase
        owner = next((fd for fd in reversed(_fixture_stack) if getattr(fd, "scope", "function") != "function"), None)
    if nodeid is not None:
        stack = traceback.StackSummary.extract(traceback.walk_stack(sys._getframe(1)), limit=40, lookup_lines=False)
        stack.reverse()
        with _origins_lock:
            _origins[self] = _Origin(nodeid=nodeid, phase=phase, fixturedef=owner, stack=stack)
    return _real_start(self, *args, **kwargs)


threading.Thread.start = _recording_start


def _thread_cpu_seconds(thread: threading.Thread) -> float | None:
    native = getattr(thread, "native_id", None)
    if native is None:
        return None
    try:
        with open(f"/proc/self/task/{native}/stat", encoding="ascii") as handle:
            fields = handle.read().rsplit(")", 1)[1].split()
        return (int(fields[11]) + int(fields[12])) / os.sysconf("SC_CLK_TCK")
    except (OSError, IndexError, ValueError):
        return None


def _target_name(thread: threading.Thread) -> str:
    target = getattr(thread, "_target", None)
    if target is None:
        return f"{type(thread).__module__}.{type(thread).__qualname__}.run"
    return f"{getattr(target, '__module__', '?')}.{getattr(target, '__qualname__', repr(target))}"


_SKIP_FRAMES = ("/threading.py", "/concurrent/futures/", "thread_guard.py")


def _creation_site(stack: traceback.StackSummary) -> str:
    for frame in reversed(stack):
        if not any(part in frame.filename for part in _SKIP_FRAMES):
            return f"{frame.filename}:{frame.lineno}:{frame.name}"
    return "?"


def _allowed(origin: _Origin) -> Allowed | None:
    frames = [f"{frame.filename}:{frame.name}" for frame in origin.stack]
    return next((entry for entry in ALLOWED if any(entry.site in frame for frame in frames)), None)


def _grace() -> float:
    # A survey (report mode) may shorten the grace to cover a whole shard fast.
    try:
        return float(os.environ.get(GRACE_ENV, JOIN_GRACE_SECONDS))
    except ValueError:
        return JOIN_GRACE_SECONDS


def _survivors(threads: list[threading.Thread]) -> list[threading.Thread]:
    deadline = time.monotonic() + _grace()
    for thread in threads:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            break
        thread.join(remaining)
    return [thread for thread in threads if thread.is_alive()]


def _check(owned: list[tuple[threading.Thread, _Origin]], owner_label: str, item) -> None:
    candidates = [(t, o) for t, o in owned if t.is_alive() and not o.reported and _allowed(o) is None]
    if not candidates:
        return
    alive = set(_survivors([t for t, _ in candidates]))
    leaked = [(t, o) for t, o in candidates if t in alive]
    if not leaked:
        return
    for _, origin in leaked:
        origin.reported = True
    records = [
        {
            "name": thread.name,
            "daemon": thread.daemon,
            "target": _target_name(thread),
            "site": _creation_site(origin.stack),
            "phase": origin.phase,
            "cpu_seconds": _thread_cpu_seconds(thread),
            "stack": "".join(origin.stack.format()),
        }
        for thread, origin in leaked
    ]
    report_path = os.environ.get(REPORT_ENV)
    if report_path:
        with open(report_path, "a", encoding="utf-8") as handle:
            handle.write(json.dumps({
                "owner": owner_label,
                "test": item.nodeid,
                "worker": os.environ.get("PYTEST_XDIST_WORKER"),
                "alive_total": threading.active_count(),
                "leaked": records,
            }) + "\n")
        return
    lines = [
        f"{owner_label} left {len(leaked)} thread(s) running after a {_grace():g}s join grace "
        "(close/stop what the test started, or give the production owner a stop path; "
        "tests/thread_guard.py):"
    ]
    for record in records:
        lines.append(
            f"  - {record['name']!r} daemon={record['daemon']} target={record['target']} "
            f"cpu={record['cpu_seconds']}s started during {record['phase']} at {record['site']}"
        )
        lines.append("    created at:\n" + "".join("      " + line for line in record["stack"].splitlines(True)[-12:]))
    _pending_failures.append("\n".join(lines))


@pytest.hookimpl(wrapper=True, tryfirst=True)
def pytest_fixture_setup(fixturedef, request):
    _fixture_stack.append(fixturedef)
    try:
        return (yield)
    finally:
        _fixture_stack.pop()


@pytest.hookimpl(wrapper=True)
def pytest_fixture_post_finalizer(fixturedef, request):
    try:
        return (yield)
    finally:
        if getattr(fixturedef, "scope", "function") != "function":
            with _origins_lock:
                owned = [(t, o) for t, o in _origins.items() if o.fixturedef is fixturedef]
            if owned:
                label = f"fixture {fixturedef.argname!r} ({fixturedef.scope} scope)"
                _check(owned, label, request.node)
                with _origins_lock:
                    for thread, _ in owned:
                        _origins.pop(thread, None)


def _phase(name):
    @pytest.hookimpl(wrapper=True, tryfirst=True)
    def hook(item, *args, **kwargs):
        global _current_nodeid, _current_phase
        _current_nodeid, _current_phase = item.nodeid, name
        try:
            return (yield)
        finally:
            _current_phase = None
    return hook


pytest_runtest_setup = _phase("setup")
pytest_runtest_call = _phase("call")


@pytest.hookimpl(wrapper=True, tryfirst=True)
def pytest_runtest_teardown(item, nextitem):
    global _current_nodeid, _current_phase
    _current_nodeid, _current_phase = item.nodeid, "teardown"
    try:
        result = yield
    finally:
        _current_phase = None
        with _origins_lock:
            owned = [(t, o) for t, o in _origins.items() if o.fixturedef is None and o.nodeid == item.nodeid]
        _check(owned, f"test {item.nodeid}", item)
        with _origins_lock:
            for thread, _ in owned:
                _origins.pop(thread, None)
            # Forget threads that finished (their owners' checks passed).
            for thread in [t for t in _origins if not t.is_alive()]:
                del _origins[thread]
        _current_nodeid = None
    if _pending_failures:
        message = "\n\n".join(_pending_failures)
        _pending_failures.clear()
        pytest.fail(message, pytrace=False)
    return result

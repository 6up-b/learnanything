"""The router's seeded draws, pinned by default in tests (refactor step T3; ``docs/reviews/refactor-t3.md``).

Production seeds the objective's draws on ids minted at run time (a decision id, the plan id inside a boundary
identity, a factor id) and on the local date, and the numeric policy refines for as long as the LLM policy is out. So
a test that reaches those draws without pinning them passes most runs and fails some. ``tests/conftest.py`` installs
the wrappers below; while a test without ``@pytest.mark.real_draws`` runs, each seed derivation returns a seed that
depends only on the test's node id, the family, and how many distinct production seeds that family has returned so far
in the test, and the numeric policy runs one batch of draws. A test whose subject is the draw takes the marker and
gets production's seeds and refinement unchanged.

The map from production's seed to the pinned one is one-to-one within a test, so two derivations that production
makes equal stay equal and different ones stay different: a test comparing seeds, or a logged seed against
``seed_for(...)`` of its row, still holds. Nothing is forced: the pinned seeds are as uniform as production's.

A test's own pin (a replaced ``seed_for``/``numeric_seed``/``mix.draw``, a runtime ``seed``, ``check_rate = "off"``)
wins: it replaces what these wrappers wrap, or production never calls them.
"""

from __future__ import annotations

from collections.abc import Callable
import hashlib
import importlib
import os
import threading
from typing import Any

#: (family, module, attribute): the derivations production looks up as module attributes at call time, so wrapping
#: the attribute reaches every production call (none of them is imported by name at import time).
SEED_SOURCES: tuple[tuple[str, str, str], ...] = (
    ("objective_mix", "learnloop.router_objective.mix", "seed_for"),
    ("mixture", "learnloop.router.mixture", "seed_for"),
    ("numeric", "learnloop.daily_plan.objective_chooser", "numeric_seed"),
    ("pick", "learnloop.router_objective.picks", "seed_for"),
    ("check", "learnloop.router_objective.checks", "day_seed"),
    ("lesson", "learnloop.router.lesson_suggestions", "seed_for"),
)
#: The numeric policy's entry: its ``keep_going`` is what lets the wall clock decide how many draws it makes.
NUMERIC_POLICY = ("learnloop.daily_plan.objective_chooser", "run_numeric")

#: Set while a pinned test runs (to its node id), so a process the test spawns can pin its own draws the same way.
KEY_ENV = "LEARNLOOP_TEST_PINNED_DRAWS"

_lock = threading.Lock()
# A global rather than a context variable: the prefetch job and the sidecar's workers run on threads a test starts,
# and a context variable set in the test's thread does not reach them.
_scopes: list[tuple[str, dict[str, dict[str, str]]]] = []
_production: dict[tuple[str, str], Callable[..., Any]] = {}


def pinned_seed(key: str, family: str, index: int, length: int) -> str:
    """The seed a pinned test gets for its ``index``-th distinct production seed of ``family``."""

    digest = hashlib.sha256(f"pinned-draws|{key}|{family}|{index}".encode("utf-8")).hexdigest()
    return digest[:length] if length else digest


def _pin(family: str, production: str) -> str:
    with _lock:
        if not _scopes:
            return production
        key, seen = _scopes[-1]
        table = seen.setdefault(family, {})
        pinned = table.get(production)
        if pinned is None:
            pinned = table[production] = pinned_seed(key, family, len(table), len(production))
        return pinned


def active() -> bool:
    with _lock:
        return bool(_scopes)


def begin(key: str) -> None:
    """Pin draws for one test (or, with :func:`push`, one wider-scoped fixture) keyed on ``key``; the counts start at
    zero, as on a fresh run of that test."""

    with _lock:
        _scopes.clear()
        _scopes.append((key, {}))


def end() -> None:
    with _lock:
        _scopes.clear()


def push(key: str) -> bool:
    """While a module- or class-scoped fixture is set up, its draws are keyed on the fixture, not on whichever test
    happened to build it first on this worker. Returns whether anything was pushed (draws were pinned)."""

    with _lock:
        if not _scopes:
            return False
        _scopes.append((key, {}))
        return True


def pop() -> None:
    with _lock:
        if len(_scopes) > 1:
            _scopes.pop()


def _seed_wrapper(family: str, production: Callable[..., str]) -> Callable[..., str]:
    def pinned(*args: Any, **kwargs: Any) -> str:
        return _pin(family, production(*args, **kwargs))

    pinned.__wrapped__ = production  # type: ignore[attr-defined]
    pinned.__name__ = getattr(production, "__name__", "seed")
    pinned.__doc__ = production.__doc__
    return pinned


def _numeric_wrapper(production: Callable[..., Any]) -> Callable[..., Any]:
    def one_batch(*args: Any, **kwargs: Any) -> Any:
        if active():
            # One batch of ``rollout_theta_draws``: refinement continues while the LLM fake has not answered and the
            # clock allows, so its draw count, and with it the argmax, would follow the machine's load.
            kwargs["keep_going"] = None
        return production(*args, **kwargs)

    one_batch.__wrapped__ = production  # type: ignore[attr-defined]
    one_batch.__name__ = getattr(production, "__name__", "run_numeric")
    one_batch.__doc__ = production.__doc__
    return one_batch


def install() -> None:
    """Wrap each source once per process; the wrappers pass production's values through until :func:`begin`."""

    if _production:
        return
    for family, module_name, attribute in SEED_SOURCES:
        module = importlib.import_module(module_name)
        production = getattr(module, attribute)
        _production[(module_name, attribute)] = production
        setattr(module, attribute, _seed_wrapper(family, production))
    module_name, attribute = NUMERIC_POLICY
    module = importlib.import_module(module_name)
    production = getattr(module, attribute)
    _production[(module_name, attribute)] = production
    setattr(module, attribute, _numeric_wrapper(production))


def production(module_name: str, attribute: str) -> Callable[..., Any]:
    """Production's own function behind a wrapper (for a test of the default itself)."""

    return _production[(module_name, attribute)]


def pin_this_process(label: str) -> None:
    """In a process a test spawned (it does not load conftest): the same default, keyed on the parent test's node id
    (:data:`KEY_ENV`, which the child inherits) and ``label``, so the child's counts are its own. Under a
    ``real_draws`` test, or outside a test, it does nothing."""

    key = os.environ.get(KEY_ENV)
    if not key:
        return
    install()
    begin(f"{key}|{label}")

"""The oldest supported tag: a vault below it is refused where it is opened.

``algorithm_versions.OLDEST_SUPPORTED`` is the floor (ADR-019). A vault whose
``learnloop.toml`` names a tag below it, or names none, is not served: every
door raises :class:`BelowOldestSupported`, which names the vault's tag, the
floor and the commands that bring the vault there. The doors that check:

* ``vault.loader.load_vault``: every CLI command, the desktop sidecar, the TUI,
  scripts, the MCP server's and the phone host's per-request loads;
* ``ops.doctor.run_doctor``, before ``--fix-state`` writes anything;
* the phone host's and the MCP server's attach, as their own ``SchemaMismatch``
  so a supervisor does not restart them in a loop;
* ``activation_journal.complete``: a journal whose upgrade starts below the
  floor is refused the same way, since completing it runs that link's code;
* ``substrate.shadow_rebuild.build_candidate_config``: a shadow rebuild cannot
  be forced below the floor.

This code has no upgrade below the floor (``learnloop.ops.upgrades`` starts at
it), so nothing here opens such a vault, ``learnloop upgrade`` included: the
code tagged ``pre-floor`` still has the whole chain, and the refusal names that
route (:func:`upgrade_commands`). Tests that still build an old vault on purpose
register it through ``tests/helpers.py``'s ``allow_below_floor``, the only
caller of :func:`allow_below_floor_in_tests` (``tests/test_version_floor.py``
pins that nothing in ``src/`` or ``scripts/`` calls it).

The route is ``pre-floor``'s ``learnloop upgrade`` alone: at that tag only the upgrade opens a vault below the
floor, so no other command it might ask for first can run there. The one link that asks for one is mvp-0.12's
same-cause guard (``recurrence guard``) when ``recurrence.require_guard`` is true; the refusal then names the
tag's documented switch that makes the guard advisory.

This module is a leaf: it imports only ``algorithm_versions``.
"""

from __future__ import annotations

import re
import shlex
from pathlib import Path

from learnloop.algorithm_versions import OLDEST_SUPPORTED, RECURRENCE_GROUP_ALGORITHM_VERSION

_TAG = re.compile(r"^mvp-0\.(\d+)$")

#: The annotated git tag whose code still has every upgrade below the floor (ADR-019).
PRE_FLOOR_TAG = "pre-floor"
#: Where the route checks that code out: beside the LearnLoop checkout its commands run in.
_PRE_FLOOR_WORKTREE = "../learnloop-pre-floor"

#: On ``pre-floor``'s code, a vault below the chain's first tag (mvp-0.9) takes one ``--to`` step per tag before
#: the chained upgrade accepts it: the chain's links refuse anything older than mvp-0.9.
_PRE_CHAIN_STEPS: tuple[str, ...] = ("mvp-0.7", "mvp-0.8", "mvp-0.9")

#: Vault roots a test built below the floor on purpose. Only ``tests/helpers.py`` adds to it. A process-wide set,
#: not a context variable, because the vault is opened later from worker threads that start with an empty context.
#: A root stays registered after its test, for a fixture that outlives one test.
_TEST_ROOTS: set[Path] = set()
#: Whether the running test registered a vault below the floor. While it is set, every vault opens: such a test
#: also opens copies of its vault (its own, or production's scratch copies, such as an apply's dry run) at roots
#: nothing registered. ``tests/conftest.py`` clears it after each test.
_TEST_OPEN: list[bool] = [False]


def _number(tag: str) -> int | None:
    match = _TAG.match(tag)
    return int(match.group(1)) if match else None


def is_below_floor(tag: str | None) -> bool:
    """Whether a vault at ``tag`` is below the floor. ``None`` (no tag named) is: such a vault predates the key.

    A tag of another shape, or one newer than this code knows, is not judged here."""

    if tag is None:
        return True
    number = _number(tag)
    floor = _number(OLDEST_SUPPORTED)
    assert floor is not None
    return number is not None and number < floor


def upgrade_commands(vault_root: Path, tag: str | None) -> tuple[str, ...]:
    """The commands that bring a vault at ``tag`` to the floor, in order, run in a LearnLoop checkout.

    The one place that names the route. This code upgrades only from the floor up, so the route runs the code
    tagged ``pre-floor`` in a worktree of its own (``uv run`` builds its environment there); the vault then opens
    here, at that code's latest tag."""

    root = shlex.quote(str(vault_root))
    number = _number(tag) if tag is not None else None
    upgrade = f"uv run --directory {_PRE_FLOOR_WORKTREE} learnloop upgrade"
    steps = tuple(
        f"{upgrade} --to {step} --vault {root}"
        for step in _PRE_CHAIN_STEPS
        if number is None or number < _number(step)  # type: ignore[operator]
    )
    return (f"git worktree add {_PRE_FLOOR_WORKTREE} {PRE_FLOOR_TAG}", *steps, f"{upgrade} --vault {root}")


#: ``pre-floor``'s link to this tag refuses until the same-cause guard passes when ``recurrence.require_guard`` is
#: true, and asks for ``learnloop recurrence guard``, which there (as here) refuses a vault below the floor: only
#: ``learnloop upgrade`` opens one. The tag's own documented switch makes the guard advisory.
_GUARDED_TAG = RECURRENCE_GROUP_ALGORITHM_VERSION
_GUARD_ROUTE = (
    f" Its config sets recurrence.require_guard = true, so {PRE_FLOOR_TAG}'s upgrade refuses at {_GUARDED_TAG} "
    "until the same-cause guard passes, and `learnloop recurrence guard` cannot run on a vault below the floor "
    f"there or here: set `recurrence.require_guard = false` under [recurrence] (the default) first, and the "
    "upgrade reports the guard's status instead of refusing."
)


class BelowOldestSupported(RuntimeError):
    """A vault (or an unfinished upgrade's journal) below the oldest supported tag: it is not opened."""

    def __init__(self, vault_root: Path, tag: str | None, *, journal: tuple[str, str] | None = None,
                 guard_required: bool = False) -> None:
        self.vault_root = Path(vault_root)
        self.tag = tag
        self.floor = OLDEST_SUPPORTED
        self.journal = journal
        start = tag if journal is None else journal[0]
        self.commands = upgrade_commands(self.vault_root, start)
        # Only a route that crosses the guarded link meets the guard.
        self.guard_gates_route = guard_required and (start is None or _number(start) is None
                                                     or _number(start) < _number(_GUARDED_TAG))  # type: ignore[operator]
        super().__init__(self._message())

    def _message(self) -> str:
        then = ", then ".join(f"`{command}`" for command in self.commands)
        route = (
            f"This LearnLoop has no upgrade below {self.floor}; the code tagged {PRE_FLOOR_TAG} has it. In your "
            f"LearnLoop checkout, run {then}; then open the vault here."
        ) + (_GUARD_ROUTE if self.guard_gates_route else "")
        if self.journal is not None:
            predecessor, target = self.journal
            return (
                f"{self.vault_root} has an unfinished upgrade from {predecessor} to {target}, which starts below "
                f"{self.floor}, the oldest version this LearnLoop opens. {route}"
            )
        if self.tag is None:
            return (
                f"{self.vault_root}'s learnloop.toml names no algorithm_version, so the vault is older than "
                f"{self.floor}, the oldest version this LearnLoop opens. Add `algorithm_version = \"mvp-0.6\"` "
                f"under [algorithms] first. {route}"
            )
        return (
            f"{self.vault_root} is at {self.tag}, older than {self.floor}, the oldest version this LearnLoop "
            f"opens. {route}"
        )


def may_open_below_floor(vault_root: Path) -> bool:
    """Whether this vault opens below the floor here: only a test that built it on purpose (or its copies)."""

    return _TEST_OPEN[0] or Path(vault_root).resolve() in _TEST_ROOTS


def refuse_below_floor(vault_root: Path, config) -> None:
    """Raise :class:`BelowOldestSupported` if the vault's config (a ``LearnLoopConfig`` loaded from its
    ``learnloop.toml``) is below the floor, or names no tag, unless this vault may be opened anyway."""

    algorithms = config.algorithms
    # The field has a default for configs built in code; a vault's file must say which tag it is at.
    tag = algorithms.algorithm_version if "algorithm_version" in algorithms.model_fields_set else None
    if is_below_floor(tag) and not may_open_below_floor(vault_root):
        recurrence = getattr(config, "recurrence", None)
        raise BelowOldestSupported(Path(vault_root).resolve(), tag,
                                   guard_required=bool(getattr(recurrence, "require_guard", False)))


def refuse_journal_below_floor(vault_root: Path, predecessor: str, target: str) -> None:
    """Raise :class:`BelowOldestSupported` for a journalled upgrade from below the floor, unless allowed."""

    if is_below_floor(predecessor) and not may_open_below_floor(vault_root):
        raise BelowOldestSupported(Path(vault_root).resolve(), target, journal=(predecessor, target))


def allow_below_floor_in_tests(vault_root: Path) -> None:
    """Let a test's vault below the floor, and for the rest of that test any vault, open
    (``tests/helpers.py``'s ``allow_below_floor`` only)."""

    _TEST_ROOTS.add(Path(vault_root).resolve())
    _TEST_OPEN[0] = True


def end_test_allowance() -> None:
    """Close the running test's allowance (``tests/conftest.py``, after each test)."""

    _TEST_OPEN[0] = False


__all__ = [
    "PRE_FLOOR_TAG",
    "BelowOldestSupported",
    "allow_below_floor_in_tests",
    "end_test_allowance",
    "is_below_floor",
    "may_open_below_floor",
    "refuse_below_floor",
    "refuse_journal_below_floor",
    "upgrade_commands",
]

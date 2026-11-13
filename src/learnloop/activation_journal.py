"""An activation that did not commit: its journal, and what may open the vault meanwhile.

Every activation in ``learnloop.ops.upgrades`` journals its link across the
config file and the database at one path (the journal names its target; the
installed completion is the table's). A process
that dies after it publishes the successor's config and before it commits the
database leaves the successor's label over the predecessor's state, with a
journal beside the database. Nothing may serve the vault in that state:

* the openers that may write (``learnloop.vault.repository``: every CLI
  command, the desktop sidecar, the TUI, scripts, and the services below
  them) first complete the activation from the journal (:func:`complete`),
  under the vault mutation lock, and raise :class:`InterruptedActivation` if
  they cannot. The completion is the upgrade table's, which sits far above
  the vault layer, so the entry points that may complete it (the CLI and the
  desktop sidecar) install it here (:func:`install_completer`); an opener in
  a process that installed none (the TUI, a script) cannot complete it and
  raises, naming the command that does;
* every other attach refuses with :class:`InterruptedActivation`
  (:func:`refuse_if_interrupted`, run by the database layer's ``Repository``).
  That covers a read-only CLI report, the MCP server and the phone host, which
  never migrate or write learner state; the MCP server and the phone host also
  say so as their own ``SchemaMismatch``.

A journal whose upgrade starts below the oldest supported tag is not completed
by an opener: :func:`complete` raises
:class:`learnloop.version_floor.BelowOldestSupported`, naming the code tagged
``pre-floor``, which finishes it.

The journal's path follows from the database's alone, so the database layer
can refuse without knowing the vault. This module is a leaf: it imports
nothing of LearnLoop but the version floor (itself a leaf).
"""

from __future__ import annotations

import json
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from pathlib import Path

from learnloop.version_floor import refuse_journal_below_floor

#: The journal's name beside the vault database (``<database>.claim-fixes-activation``).
JOURNAL_SUFFIX = ".claim-fixes-activation"

#: Set while this context completes (or runs) the journalled activation itself.
_COMPLETING: ContextVar[bool] = ContextVar("learnloop_activation_completing", default=False)

#: The installed completion: ``vault_root -> None``, raising when it cannot complete.
_COMPLETER: Callable[[Path], object] | None = None


class InterruptedActivation(RuntimeError):
    """The vault's activation did not commit; it is not served until it completes."""


def journal_path(sqlite_path: Path) -> Path:
    """The activation journal beside ``sqlite_path``."""

    path = Path(sqlite_path)
    return path.with_name(path.name + JOURNAL_SUFFIX)


def pending(sqlite_path: Path) -> bool:
    """Whether an activation journal stands beside ``sqlite_path``."""

    return journal_path(sqlite_path).exists()


def completing() -> bool:
    """Whether this context is completing (or running) the activation itself."""

    return _COMPLETING.get()


@contextmanager
def completing_activation() -> Iterator[None]:
    """Mark this context as the activation's own writer, so its opens are not refused."""

    token = _COMPLETING.set(True)
    try:
        yield
    finally:
        _COMPLETING.reset(token)


def message(sqlite_path: Path) -> str:
    """What to tell the learner: which upgrade did not finish, and the command that completes it."""

    target = "the latest version"
    try:
        payload = json.loads(journal_path(sqlite_path).read_text(encoding="utf-8"))
        target = str(payload.get("target") or target)
    except (OSError, ValueError, AttributeError):
        pass
    return (
        f"The upgrade to {target} did not finish ({journal_path(sqlite_path).name} is beside the database), "
        f"so this vault is not served until it does: open the desktop app or run "
        f"`learnloop upgrade --to {target}` to complete it."
    )


def _link(sqlite_path: Path) -> tuple[str, str] | None:
    """The journalled upgrade's ``(predecessor, target)``, or None for a torn journal (its completion decides)."""

    try:
        payload = json.loads(journal_path(sqlite_path).read_text(encoding="utf-8"))
        return (str(payload["predecessor"]), str(payload["target"]))
    except (OSError, ValueError, KeyError, TypeError):
        return None


def install_completer(completer: Callable[[Path], object] | None) -> None:
    """Install the process's completion (an entry point does, at import); None removes it."""

    global _COMPLETER
    _COMPLETER = completer


def complete(vault_root: Path, sqlite_path: Path) -> None:
    """Complete a journalled activation before an opener attaches, or raise :class:`InterruptedActivation`.

    Without a journal (or inside the completion itself) this is one ``stat``."""

    if completing() or not pending(sqlite_path):
        return
    link = _link(sqlite_path)
    if link is not None:
        # Completing a journal runs its link's upgrade code, so one starting below the floor waits for
        # ``learnloop upgrade``, like a vault below it.
        refuse_journal_below_floor(Path(vault_root), *link)
    if _COMPLETER is None:
        raise InterruptedActivation(message(sqlite_path))
    try:
        _COMPLETER(Path(vault_root))
    except Exception as error:
        raise InterruptedActivation(message(sqlite_path)) from error
    if pending(sqlite_path):
        raise InterruptedActivation(message(sqlite_path))


def refuse_if_interrupted(sqlite_path: Path) -> None:
    """Raise :class:`InterruptedActivation` while a journal stands (unless this context completes it)."""

    if not completing() and pending(sqlite_path):
        raise InterruptedActivation(message(sqlite_path))


__all__ = [
    "JOURNAL_SUFFIX",
    "InterruptedActivation",
    "complete",
    "completing",
    "completing_activation",
    "install_completer",
    "journal_path",
    "message",
    "pending",
    "refuse_if_interrupted",
]

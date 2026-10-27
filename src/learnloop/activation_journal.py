"""An activation that did not commit: its journal, and what may open the vault meanwhile.

LP-min (a) (claim-fixes review F2, re-review): ``learnloop.claim_fixes_upgrade``
journals its activation across the config file and the database, and so do
the next links', rebuild equivalence's ``learnloop.replay_ledger_upgrade`` and
Reader CA2's ``learnloop.one_ask_upgrade`` (mvp-0.35) and
``learnloop.superseded_claims_upgrade`` (mvp-0.36), at the same path (the journal names its target; the installed completion is the
chain's latest upgrade's, which hands an earlier link's journal to that link).
A process
that dies after it publishes the successor's config and before it commits the
database leaves the successor's label over the predecessor's state, with a
journal beside the database. Nothing may serve the vault in that state:

* the openers that may write (``learnloop.vault.repository``: every CLI
  command, the desktop sidecar, the TUI, scripts, and the services below
  them) first complete the activation from the journal (:func:`complete`),
  under the vault mutation lock, and raise :class:`InterruptedActivation` if
  they cannot. The completion is the upgrade module's, which sits far above
  the vault layer, so the entry points that may complete it (the CLI and the
  desktop sidecar) install it here (:func:`install_completer`); an opener in
  a process that installed none (the TUI, a script) cannot complete it and
  raises, naming the command that does;
* every other attach refuses with :class:`InterruptedActivation`
  (:func:`refuse_if_interrupted`, run by the database layer's ``Repository``).
  That covers a read-only CLI report, the MCP server and the phone host, which
  never migrate or write learner state; the MCP server and the phone host also
  say so as their own ``SchemaMismatch``.

The journal's path follows from the database's alone, so the database layer
can refuse without knowing the vault. This module is a leaf: it imports
nothing of LearnLoop.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from pathlib import Path

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


def install_completer(completer: Callable[[Path], object] | None) -> None:
    """Install the process's completion (an entry point does, at import); None removes it."""

    global _COMPLETER
    _COMPLETER = completer


def complete(vault_root: Path, sqlite_path: Path) -> None:
    """Complete a journalled activation before an opener attaches, or raise :class:`InterruptedActivation`.

    Without a journal (or inside the completion itself) this is one ``stat``."""

    if completing() or not pending(sqlite_path):
        return
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

"""``learnloop upgrade --to <ONE_ASK_ALGORITHM_VERSION>``: Reader CA2, one Ask.

Reader CA2 (``docs/specs/ux_reader_compare_ask_v1.md`` §7.7, K10 and §15
Q3-Q4; ``docs/reviews/reader-ca2-one-ask.md``): one help rule on a check on
your own. It is the next link of the linear chain: everything the
predecessor means PLUS this:

* a question asked during a cold administration counts as help only when
  the tutor model's ``question_type`` is substantive
  (``tutor_qa.HINT_EQUIVALENT_TYPES``) on every cold path: the Reader's cold
  Ask (bound to a workbench item, or naming a client-reported cold attempt)
  no longer counts every question (the predecessor's L6 rule);
* help taken on a cold follow-up (``cold_retry``,
  ``certification_cold_probe``) makes the attempt practice with help: submit
  admits it instead of refusing it, it never answers the cold measurement,
  and the next serve withdraws the measurement as practised since scheduled;
  the practice view shows the help ladder's take step instead of "no hints on
  this one".

The tag is ONE constant (``ONE_ASK_ALGORITHM_VERSION``, ``mvp-0.35``). Built
on main at ``mvp-0.32`` as ``mvp-0.34`` while the LP claim fixes held
``mvp-0.33``; the batch landing (2026-10-26) chained it after rebuild
equivalence's ``mvp-0.34``, so :data:`PREDECESSOR` is that tag and its
upgrade.

The upgrade:

* accepts the immediate predecessor, or ``mvp-0.9`` up to it by running the
  predecessor's own upgrade first (with its own activation and notes, a
  refusal's included). If the chained steps succeed and this step then fails,
  the vault is left at the valid predecessor. Anything older is refused;
* changes how new attempts are classified and what submit admits, never the
  authority-propagation projection: its activation is the idempotent
  rebuild of the same projection namespace, the registry refresh and the
  config's publication.

**Activation is journalled like its predecessors' (batch landing onto
main).** The predecessors (``learnloop.claim_fixes_upgrade``,
``learnloop.replay_ledger_upgrade``) activate in ONE ``BEGIN IMMEDIATE``
transaction under the vault mutation lock with the config's durable
publication as its LAST step, journalled across the config file and the
database (``learnloop.activation_journal``), and no entry point serves a
vault while a journal stands. This activation does the same: the
predecessor's manifest, the projection activation (whose receipt under the
tag is the completion marker), the registry refresh, the journal
(``predecessor``, ``target``) and the publication, then the commit and the
journal's removal. A death between the publication and the commit is
completed by the next guarded open (every CLI command and the desktop
sidecar install :func:`complete_interrupted_activation`, the chain's latest
completion) or refused with the upgrade message. A journal naming this tag
is completed here, and any other is handed to the predecessor's completion
(which hands an earlier link's on in turn).

Nothing is rewritten: attempts and question rows recorded below the tag keep
the flags they were written with (replay reads the stored ``hint_equivalent``
and ``hints_used``, never this rule). Kill switch: ``ask.cold_help_converts =
false`` restores both predecessor rules for new questions and submits
without a downgrade; rolling the version back is restore-only.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from learnloop import activation_journal
from learnloop.algorithm_versions import (
    ONE_ASK_ALGORITHM_VERSION,
    REPLAY_LEDGER_ALGORITHM_VERSION,
    SUCCESSOR_CHAIN,
)
from learnloop.claim_fixes_upgrade import write_activation_journal as _write_journal
from learnloop.clock import Clock
from learnloop.ops.vault_upgrade import UpgradeResult
from learnloop.params import parameter_registry as registry_service
from learnloop.regrade_contract_upgrade import publish_algorithm_version as _publish_algorithm_version
from learnloop.replay_ledger_upgrade import complete_interrupted_activation as _complete_predecessor_activation
from learnloop.replay_ledger_upgrade import upgrade_to_replay_ledger
from learnloop.substrate.p0_projection import activate_p0_projection
from learnloop.vault.loader import load_vault
from learnloop.vault.paths import VaultPaths
from learnloop.vault.repository import open_vault_repository
from learnloop.vault_lock import vault_mutation_lock

#: The immediate predecessor and its upgrade.
PREDECESSOR = REPLAY_LEDGER_ALGORITHM_VERSION
_upgrade_to_predecessor = upgrade_to_replay_ledger

#: Versions the upgrade accepts through the existing chain: mvp-0.9 up to the predecessor's own predecessor.
_CHAINED_PREDECESSORS = SUCCESSOR_CHAIN[:SUCCESSOR_CHAIN.index(PREDECESSOR)]

#: An earlier link's refusal already names its own step; it passes through unprefixed.
_STEP_REFUSAL = re.compile(r"^mvp-0\.\d+ step refused: ")


def upgrade_to_one_ask(root: Path, *, clock: Clock | None = None) -> UpgradeResult:
    """The predecessor (or mvp-0.9 onwards, through the chain) -> Reader CA2's tag: one help rule.

    On a vault already at the tag whose activation did not commit (the process
    died after publishing the config), it completes the activation."""

    with vault_mutation_lock(Path(root), purpose="upgrade_one_ask"):
        return _upgrade(Path(root), clock=clock)


def complete_interrupted_activation(root: Path, *, vault=None, clock: Clock | None = None) -> str | None:
    """Finish any journalled activation of the chain a dead process left; None when there is none.

    Returns the version whose activation it completed. A journal naming this
    tag is completed here; any other is handed to the predecessor's own
    completion (which completes its journal or hands an earlier link's on).
    Safe to call on every vault open: without a journal it checks one path and
    returns. Runs under the vault mutation lock (re-entrant), so it waits for
    an upgrade still running in another process."""

    root = Path(root)
    if not _journal_path(vault if vault is not None else load_vault(root)).exists():
        return None
    with vault_mutation_lock(root, purpose="upgrade_one_ask_recovery"):
        with activation_journal.completing_activation():
            vault = load_vault(root)
            journal_path = _journal_path(vault)
            journal = _read_journal(journal_path)
            version = vault.config.algorithms.algorithm_version
            if journal is None:
                return None
            if journal == "torn":
                if version == PREDECESSOR:
                    # Torn before its fsync, which precedes this activation's
                    # publication (the config still names the predecessor, so
                    # the predecessor's own activation had committed): nothing
                    # of this activation is in force.
                    journal_path.unlink(missing_ok=True)
                    return None
            elif journal[1] == ONE_ASK_ALGORITHM_VERSION:
                predecessor, target = journal
                if version != target:
                    # The publication never landed (the transaction rolled
                    # back with it), or the config names another version since.
                    journal_path.unlink(missing_ok=True)
                    return None
                # False: the process died between the commit and the
                # journal's removal, so the activation is already complete.
                activated = _activate(root, predecessor=predecessor, target=target, publish=False, clock=clock)
                journal_path.unlink(missing_ok=True)
                return target if activated else None
        # An earlier link's journal (or a torn one at an earlier version).
        return _complete_predecessor_activation(root, clock=clock)


def _journal_path(vault) -> Path:
    """The activation journal beside the vault database (``learnloop.activation_journal``)."""

    return activation_journal.journal_path(VaultPaths(vault.root, vault.config).sqlite_path)


def _read_journal(path: Path) -> tuple[str, str] | str | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        return (str(payload["predecessor"]), str(payload["target"]))
    except FileNotFoundError:
        return None
    except (OSError, ValueError, KeyError, TypeError):
        return "torn"


def _upgrade(root: Path, *, clock: Clock | None) -> UpgradeResult:
    target = ONE_ASK_ALGORITHM_VERSION
    predecessor = PREDECESSOR
    # Any journalled activation first: this tag's (a death between its
    # publication and its commit) or an earlier link's, so the version read
    # below is one whose database is in force.
    completed = complete_interrupted_activation(root, clock=clock)
    vault = load_vault(root)
    original = vault.config.algorithms.algorithm_version
    if original == target and completed == target:
        return UpgradeResult(upgraded=True, from_version=target, to_version=target,
                             notes=[f"completed the interrupted activation of {target}"])
    if original == target:
        if not _activate(root, predecessor=predecessor, target=target, publish=False, clock=clock):
            return UpgradeResult(upgraded=False, from_version=original, to_version=target,
                                 problems=[f"vault is already {target}"])
        return UpgradeResult(upgraded=True, from_version=target, to_version=target,
                             notes=[f"completed the activation of {target} (its projection activation)"])
    if original != predecessor and original not in _CHAINED_PREDECESSORS:
        return UpgradeResult(
            upgraded=False, from_version=original, to_version=target,
            problems=[
                f"cannot upgrade from {original!r}; only {predecessor!r} (or "
                f"{_CHAINED_PREDECESSORS[0]!r} to {_CHAINED_PREDECESSORS[-1]!r}, through it) may activate {target}"
            ],
        )
    chained_notes: list[str] = []
    if original != predecessor:
        # The chain's predecessor step (with its own activation) refuses
        # before it takes any step of its own; a refusal there leaves the
        # vault where it was.
        chained = _upgrade_to_predecessor(root, clock=clock)
        chained_notes = list(chained.notes or [])
        if not chained.upgraded:
            return UpgradeResult(
                upgraded=False, from_version=original, to_version=target, notes=chained_notes,
                problems=[
                    problem if _STEP_REFUSAL.match(problem) else f"{predecessor} step refused: {problem}"
                    for problem in chained.problems
                ],
            )
    _activate(root, predecessor=predecessor, target=target, publish=True, clock=clock)
    return UpgradeResult(upgraded=True, from_version=original, to_version=target, notes=chained_notes)


def _activate(root: Path, *, predecessor: str, target: str, publish: bool, clock: Clock | None) -> bool:
    """Activate ``target`` in one transaction.

    ``publish``: the vault is at ``predecessor``; the config's publication is
    the transaction's last step. Otherwise the vault is already labelled
    ``target``: this completes an activation that did not commit, and does
    nothing (returning False) once the projection activation under ``target``
    has committed (its receipt is written in this transaction, so it exists
    exactly when the activation committed).

    The journal (``publish``) is written before the publication and removed
    once the transaction has committed; a failure that restores the
    predecessor's label removes it too."""

    with activation_journal.completing_activation():
        return _activate_as_writer(root, predecessor=predecessor, target=target, publish=publish, clock=clock)


def _activation_committed(repository, target: str) -> bool:
    """Whether an activation of ``target`` committed: its projection receipt is on record."""

    with repository.connection() as connection:
        row = connection.execute(
            "SELECT 1 FROM derived_state_rebuilds WHERE scope = 'p0_projection_activation' "
            "AND algorithm_version = ? LIMIT 1",
            (target,),
        ).fetchone()
    return row is not None


def _activate_as_writer(root: Path, *, predecessor: str, target: str, publish: bool, clock: Clock | None) -> bool:
    vault = load_vault(root)
    expected = predecessor if publish else target
    if vault.config.algorithms.algorithm_version != expected:  # pragma: no cover - the caller read it under the lock
        raise RuntimeError(f"{root}: algorithm_version changed during the upgrade to {target}")
    sqlite_path = VaultPaths(vault.root, vault.config).sqlite_path
    repository = open_vault_repository(vault.root, sqlite_path)
    config_path = root / "learnloop.toml"
    journal_path = _journal_path(vault)
    published = False
    try:
        with repository.atomic():
            if not publish and _activation_committed(repository, target):
                return False
            # The predecessor's manifest, frozen from its own config (only the
            # version line differs) exactly as a clean upgrade freezes it.
            vault.config.algorithms.algorithm_version = predecessor
            registry_service.freeze_manifest(vault, repository, algorithm_version=predecessor, clock=clock)
            vault.config.algorithms.algorithm_version = target
            activate_p0_projection(vault, repository, from_version=predecessor, clock=clock)
            registry_service.refresh(vault, repository, clock=clock)
            if publish:
                # Last: the journal, then the publication; the commit follows,
                # so a label without its database is always journalled.
                _write_journal(journal_path, predecessor, target)

                def renamed() -> None:
                    nonlocal published
                    published = True

                _publish_algorithm_version(config_path, predecessor, target, renamed=renamed)
    except BaseException as failure:
        if not publish:
            raise
        restored = True
        if published:
            try:
                _publish_algorithm_version(config_path, target, predecessor)
            except Exception as restore_failure:  # pragma: no cover - a second failure on the same file
                restored = False
                failure.add_note(
                    f"{config_path} still names {target} over the {predecessor} database "
                    f"({restore_failure}); the activation journal stays, so the next start or "
                    f"`learnloop upgrade --to {target}` completes it"
                )
        if restored:
            journal_path.unlink(missing_ok=True)
        raise
    journal_path.unlink(missing_ok=True)
    return True


__all__ = ["PREDECESSOR", "complete_interrupted_activation", "upgrade_to_one_ask"]

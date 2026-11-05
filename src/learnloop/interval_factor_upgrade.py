"""``learnloop upgrade --to <INTERVAL_FACTOR_ALGORITHM_VERSION>``: router objective RO1.

RO1 (owner decisions 2026-11-03 and 2026-11-04; ``docs/specs/spec_router_objective_v1.md`` §5). It is the
next link of the linear chain: everything the predecessor means PLUS this:

* the surprise interval factor is not applied to the FSRS interval: ``due_at`` follows
  ``interval_for_retention(S)``, and the surprise row records 1.0, what was applied
  (``[scheduler.surprise] remove_interval_factor``);
* decision-time attempt reads (the router card, the diagnoser's history, AD's frozen history card, the
  learner contexts: ``router_objective_switches.attempt_time_sql`` / ``known_at``) use the availability
  time ``coalesce(received_at, created_at)`` (``[router_objective] available_at_reads``);
* a learner's misconception pick is not counted as validated evidence for the diagnoser
  (``[router_objective] self_report_not_validated``).

The upgrade:

* accepts the immediate predecessor, or ``mvp-0.9`` up to it by running the predecessor's own upgrade first
  (with its own activation and notes, a refusal's included). If the chained steps succeed and this step
  then fails, the vault is left at the valid predecessor. Anything older is refused;
* changes learner state when it activates: existing due dates move within the old factor's range
  ([f_min, f_max] of the interval), so like the rebuild-equivalence successor it activates in ONE
  ``BEGIN IMMEDIATE`` transaction under the vault mutation lock: the predecessor's manifest, the whole-vault
  rebuild under the tag (whose receipt records the switch, the projection's defaults snapshot), the
  registry refresh, and the config's durable publication as its LAST step. Completion is read from that
  whole-vault rebuild's receipt under the tag, never from the latest receipt. Run
  ``learnloop rebuild --shadow --set algorithms.algorithm_version=<tag> --json`` on a copy first: its
  ``schedule_effects`` is this upgrade's report (item and activity-card due-date shifts, the queue due now
  and admission's projected review load, before and after).

Nothing is rewritten: attempts, grades and every ledger keep their rows; migration 244's
``practice_attempts.received_at`` is additive (imported exam rows backfilled from their ids, marked
``inferred``).

**Activation is journalled like its predecessors'.** The journal (``predecessor``, ``target``) is written
before the publication and removed after the commit, so a death between the two is completed by the next
guarded open (every CLI command and the desktop sidecar install :func:`complete_interrupted_activation`,
the chain's latest completion) or refused with the upgrade message. A journal naming this tag is completed
here, and any other is handed to the predecessor's completion (which hands an earlier link's on in turn).

Kill switches: each of the three restores mvp-0.45's behaviour without a downgrade (the factor's on
persisted due dates at the next whole-vault rebuild; ``doctor`` warns until then); rolling the version back
is restore-only.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from learnloop import activation_journal
from learnloop.algorithm_versions import (
    FOLLOWUP_SERVE_ALGORITHM_VERSION,
    INTERVAL_FACTOR_ALGORITHM_VERSION,
    SUCCESSOR_CHAIN,
)
from learnloop.claim_fixes_upgrade import write_activation_journal as _write_journal
from learnloop.clock import Clock
from learnloop.followup_serve_upgrade import complete_interrupted_activation as _complete_predecessor_activation
from learnloop.followup_serve_upgrade import upgrade_to_followup_serve as upgrade_to_followup_serve_step
from learnloop.ops.vault_upgrade import UpgradeResult
from learnloop.params import parameter_registry as registry_service
from learnloop.regrade_contract_upgrade import publish_algorithm_version as _publish_algorithm_version
from learnloop.substrate.rebuild_orchestrator import rebuild_all_derived_state
from learnloop.vault.loader import load_vault
from learnloop.vault.paths import VaultPaths
from learnloop.vault.repository import open_vault_repository
from learnloop.vault_lock import vault_mutation_lock

#: The immediate predecessor and its upgrade.
PREDECESSOR = FOLLOWUP_SERVE_ALGORITHM_VERSION
_upgrade_to_predecessor = upgrade_to_followup_serve_step

#: Versions the upgrade accepts through the existing chain: mvp-0.9 up to the predecessor's own predecessor.
_CHAINED_PREDECESSORS = SUCCESSOR_CHAIN[:SUCCESSOR_CHAIN.index(PREDECESSOR)]

#: An earlier link's refusal already names its own step; it passes through unprefixed.
_STEP_REFUSAL = re.compile(r"^mvp-0\.\d+ step refused: ")


def upgrade_to_interval_factor(root: Path, *, clock: Clock | None = None) -> UpgradeResult:
    """The predecessor (or mvp-0.9 onwards, through the chain) -> RO1's tag.

    On a vault already at the tag whose activation did not commit (the process died after publishing the
    config), or that never had a whole-vault rebuild under it, it completes the activation."""

    with vault_mutation_lock(Path(root), purpose="upgrade_interval_factor"):
        return _upgrade(Path(root), clock=clock)


def complete_interrupted_activation(root: Path, *, vault=None, clock: Clock | None = None) -> str | None:
    """Finish any journalled activation of the chain a dead process left; None when there is none.

    Returns the version whose activation it completed. A journal naming this tag is completed here; any
    other is handed to the predecessor's own completion (which completes its journal or hands an earlier
    link's on). Safe to call on every vault open: without a journal it checks one path and returns. Runs
    under the vault mutation lock (re-entrant), so it waits for an upgrade still running in another
    process."""

    root = Path(root)
    if not _journal_path(vault if vault is not None else load_vault(root)).exists():
        return None
    with vault_mutation_lock(root, purpose="upgrade_interval_factor_recovery"):
        with activation_journal.completing_activation():
            vault = load_vault(root)
            journal_path = _journal_path(vault)
            journal = _read_journal(journal_path)
            version = vault.config.algorithms.algorithm_version
            if journal is None:
                return None
            if journal == "torn":
                if version == PREDECESSOR:
                    # Torn before its fsync, which precedes this activation's publication (the config
                    # still names the predecessor, so the predecessor's own activation had committed):
                    # nothing of this activation is in force.
                    journal_path.unlink(missing_ok=True)
                    return None
            elif journal[1] == INTERVAL_FACTOR_ALGORITHM_VERSION:
                predecessor, target = journal
                if version != target:
                    # The publication never landed (the transaction rolled back with it), or the config
                    # names another version since.
                    journal_path.unlink(missing_ok=True)
                    return None
                # False: the process died between the commit and the journal's removal, so the
                # activation is already complete.
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
    target = INTERVAL_FACTOR_ALGORITHM_VERSION
    predecessor = PREDECESSOR
    # Any journalled activation first: this tag's (a death between its publication and its commit) or an
    # earlier link's, so the version read below is one whose database is in force.
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
                             notes=[f"completed the activation of {target} (a whole-vault rebuild under it)"])
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
        # The chain's predecessor step (with its own activation) refuses before it takes any step of its
        # own; a refusal there leaves the vault where it was.
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
    """Rebuild the vault under ``target`` in one transaction.

    ``publish``: the vault is at ``predecessor``; the config's publication is the transaction's last step.
    Otherwise the vault is already labelled ``target``: this completes an activation that did not commit,
    and does nothing (returning False) once a whole-vault rebuild under ``target`` has committed (its
    receipt is written in this transaction, so it exists exactly when the activation committed; a startup
    or per-LO receipt is no marker). A vault labelled the tag that never had a whole-vault rebuild under
    it (a fresh one included) gets one, which at the tag reproduces the live state.

    The journal (``publish``) is written before the publication and removed once the transaction has
    committed; a failure that restores the predecessor's label removes it too."""

    with activation_journal.completing_activation():
        return _activate_as_writer(root, predecessor=predecessor, target=target, publish=publish, clock=clock)


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
            if not publish and repository.has_whole_vault_rebuild(algorithm_version=target):
                return False
            # The predecessor's manifest, frozen from its own config (only the version line differs)
            # exactly as a clean upgrade freezes it.
            vault.config.algorithms.algorithm_version = predecessor
            registry_service.freeze_manifest(vault, repository, algorithm_version=predecessor, clock=clock)
            vault.config.algorithms.algorithm_version = target
            # Every learning object replays: every reviewed item's due date may move (§5.5).
            rebuild_all_derived_state(vault, repository, clock=clock)
            registry_service.refresh(vault, repository, clock=clock)
            if publish:
                # Last: the journal, then the publication; the commit follows, so the database never
                # holds the successor's state under the predecessor's label, and a label without its
                # database is always journalled.
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


__all__ = ["PREDECESSOR", "complete_interrupted_activation", "upgrade_to_interval_factor"]

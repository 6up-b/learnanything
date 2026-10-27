"""``learnloop upgrade --to <ATTEMPT_CONTENT_STATE_ALGORITHM_VERSION>``: mobile PR-4's attempt write.

Mobile PR-4 (``docs/specs/spec_mobile_tailnet_v1.md`` §3.3 PR-2/PR-4, §9.3;
``docs/reviews/mobile-pr3-pr4.md`` and its Codex review F4): content sync
owns a practice item row's ``active`` flag and ``content_hash``, and an
attempt owns the memory state. It is the next link of the linear chain:
everything the predecessor means PLUS this:

* a live attempt's write to its item's existing ``practice_item_state`` row
  takes only the scheduling columns (difficulty, stability, retrievability,
  due time) and the last-attempt time; ``active`` can only close (a
  diagnostic probe's single use still lands) and ``content_hash`` is never
  written. A missing row is inserted whole, as before;
* so a content sync another process committed while the answer was graded
  is kept (PR-2's reverse race: a retired item no longer reopens, an edited
  one keeps its new hash), and, without any concurrent writer, a row the sync
  rule keeps closed while its YAML is active (review-parked,
  measurement-superseded, a microprobe, a deactivation replay keeps) stays
  out of serving instead of reopening until the next sync.

The tag is ONE constant (``ATTEMPT_CONTENT_STATE_ALGORITHM_VERSION``,
``mvp-0.37``). Built on main at ``mvp-0.35`` (Reader CA2) as ``mvp-0.36``;
the kept replaced claims' successor (``learnloop.superseded_claims_upgrade``,
``mvp-0.36``) landed first, so the landing renumbered it after that one, and
:data:`PREDECESSOR` and its upgrade follow.

The upgrade:

* accepts the immediate predecessor, or ``mvp-0.9`` up to it by running the
  predecessor's own upgrade first (with its own activation and notes, a
  refusal's included). If the chained steps succeed and this step then fails,
  the vault is left at the valid predecessor. Anything older is refused;
* changes which columns a live attempt writes, never evidence, FSRS, the
  authority-propagation projection or replay (replay rebuilds the whole row
  and re-closes what was closed outside the ledger): its activation is the
  idempotent rebuild of the same projection namespace, the registry refresh
  and the config's publication.

**Activation is journalled like its predecessors'.** One ``BEGIN
IMMEDIATE`` transaction under the vault mutation lock with the config's
durable publication as its LAST step, journalled across the config file and
the database (``learnloop.activation_journal``): the predecessor's manifest,
the projection activation (whose receipt under the tag is the completion
marker), the registry refresh, the journal (``predecessor``, ``target``) and
the publication, then the commit and the journal's removal. A death between
the publication and the commit is completed by the next guarded open (every
CLI command and the desktop sidecar install
:func:`complete_interrupted_activation`, the chain's latest completion) or
refused with the upgrade message. A journal naming this tag is completed
here, and any other is handed to the predecessor's completion (which hands
an earlier link's on in turn).

Nothing is rewritten: rows written below the tag keep their values. Kill
switch: ``practice.attempt_keeps_content_state = false`` restores the
predecessor's whole-row write for new attempts without a downgrade; rolling
the version back is restore-only.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from learnloop import activation_journal
from learnloop.algorithm_versions import (
    ATTEMPT_CONTENT_STATE_ALGORITHM_VERSION,
    SUCCESSOR_CHAIN,
    SUPERSEDED_CLAIMS_ALGORITHM_VERSION,
)
from learnloop.claim_fixes_upgrade import write_activation_journal as _write_journal
from learnloop.clock import Clock
from learnloop.ops.vault_upgrade import UpgradeResult
from learnloop.params import parameter_registry as registry_service
from learnloop.regrade_contract_upgrade import publish_algorithm_version as _publish_algorithm_version
from learnloop.superseded_claims_upgrade import complete_interrupted_activation as _complete_predecessor_activation
from learnloop.superseded_claims_upgrade import upgrade_to_superseded_claims
from learnloop.substrate.p0_projection import activate_p0_projection
from learnloop.vault.loader import load_vault
from learnloop.vault.paths import VaultPaths
from learnloop.vault.repository import open_vault_repository
from learnloop.vault_lock import vault_mutation_lock

#: The immediate predecessor and its upgrade.
PREDECESSOR = SUPERSEDED_CLAIMS_ALGORITHM_VERSION
_upgrade_to_predecessor = upgrade_to_superseded_claims

#: Versions the upgrade accepts through the existing chain: mvp-0.9 up to the predecessor's own predecessor.
_CHAINED_PREDECESSORS = SUCCESSOR_CHAIN[:SUCCESSOR_CHAIN.index(PREDECESSOR)]

#: An earlier link's refusal already names its own step; it passes through unprefixed.
_STEP_REFUSAL = re.compile(r"^mvp-0\.\d+ step refused: ")


def upgrade_to_attempt_content_state(root: Path, *, clock: Clock | None = None) -> UpgradeResult:
    """The predecessor (or mvp-0.9 onwards, through the chain) -> mobile PR-4's tag: the attempt
    writes only its scheduling columns.

    On a vault already at the tag whose activation did not commit (the process
    died after publishing the config), it completes the activation."""

    with vault_mutation_lock(Path(root), purpose="upgrade_attempt_content_state"):
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
    with vault_mutation_lock(root, purpose="upgrade_attempt_content_state_recovery"):
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
            elif journal[1] == ATTEMPT_CONTENT_STATE_ALGORITHM_VERSION:
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
    target = ATTEMPT_CONTENT_STATE_ALGORITHM_VERSION
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


__all__ = ["PREDECESSOR", "complete_interrupted_activation", "upgrade_to_attempt_content_state"]

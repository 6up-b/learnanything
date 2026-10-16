"""``learnloop upgrade --to mvp-0.26``: regrade contracts.

The algorithm successor to the regrade and replay contract mismatch (UX
Phase 4 Codex review §8.4, queued 2026-10-16;
``docs/reviews/regrade-contract-replay.md``). It is the next link of the
linear chain: everything ``mvp-0.25`` means PLUS this:

* every regrade (ordinary, contested, deferred, a clarification's) cites the
  assessment contract it graded against on every row it writes, in its own
  transaction (the frozen contract for a method-explicit answer, else a
  snapshot of the item it read), carries the attempt's next grading revision
  and supersedes every live row, so its grade is the attempt's only current
  grading epoch (an adjudication's evidence revision does the same);
* replay, the canonical projection and the grade dual-write read the CURRENT
  grading epoch (``learnloop.grading_epochs``) under the contract it cites,
  never the first live row's;
* a current epoch citing no contract (rows written before the tag) is never
  read against today's item: unless it is the attempt's only grade, made
  before contracts (the compatibility reading, while its score fits), it is
  held for review (``grade_contract_unrecorded``) with the correctness of the
  maximum recorded with it (a blind record) where one exists, else the
  correctness the attempt row carries; a regrade or an adjudication releases
  it.

The upgrade:

* accepts the immediate predecessor (``mvp-0.25``), or ``mvp-0.9`` to
  ``mvp-0.24`` by running :func:`learnloop.method_explicit_upgrade.upgrade_to_mvp025`
  first (below ``mvp-0.12`` through T1's guarded step, whose advisory notes
  pass through, a refusal's included). If the chained steps succeed and this
  step then fails, the vault is left at the valid ``mvp-0.25``. Anything older
  is refused;
* replays exactly the learning objects holding an attempt whose current
  grading epoch it reinterprets (an uncited epoch it now holds), then
  re-projects the same projection namespace. Every other attempt replays as
  it did under ``mvp-0.25`` (its current epoch cites the contract its first
  live row did), so nothing else is rebuilt. Its notes name the attempts it
  holds.

**Activation is one step across the database and the config file** (review
F1). Unlike the successors before it, this one changes learner state when it
activates (it records holds and replays their learning objects), and the
held-grade predicate reads a recorded hold at any label. So the activation
never commits that state under the predecessor's label:

* under the vault mutation lock, ONE ``BEGIN IMMEDIATE`` transaction covers
  the predecessor's manifest, the scan of the attempts it holds, the replay,
  the re-projection and the registry refresh, and the config's publication
  (write, fsync, atomic rename, fsync of the directory) is its LAST step, so
  no regrade, adjudication or item edit lands between what it read and what
  it publishes;
* a failure before or at the publication rolls the transaction back: the
  predecessor's database is exactly as it was and its config still names it;
* a commit that fails after the publication rolls back too, and the config
  is restored to the predecessor;
* a process that dies after the publication and before the commit leaves the
  successor's label over the predecessor's untouched database: the transient
  state every successor leaves until a rebuild (doctor reports it as
  ``sql:derived_state_rebuild_stale``), never a successor's state under the
  predecessor's label. Running the upgrade again completes the activation
  (:func:`upgrade_to_mvp026` on a vault already at the tag), as does any
  rebuild.

Nothing is rewritten: evidence rows, contracts and blind records keep their
rows; replay records the hold on the attempt's derived review reason. There is
no kill switch (the earlier writer is the defect); rolling the version back is
restore-only.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

from learnloop.algorithm_versions import (
    METHOD_EXPLICIT_ALGORITHM_VERSION,
    REGRADE_CONTRACT_ALGORITHM_VERSION,
    SUCCESSOR_CHAIN,
)
from learnloop.attempts.attempts import unrecorded_epoch_attempts
from learnloop.clock import Clock
from learnloop.held_grades import contract_unrecorded_attempts
from learnloop.method_explicit_upgrade import upgrade_to_mvp025
from learnloop.ops.vault_upgrade import UpgradeResult, rewrite_algorithm_version
from learnloop.params import parameter_registry as registry_service
from learnloop.substrate.p0_projection import activate_p0_projection
from learnloop.substrate.rebuild_orchestrator import rebuild_all_derived_state
from learnloop.vault.loader import load_vault
from learnloop.vault.paths import VaultPaths
from learnloop.vault.repository import open_vault_repository
from learnloop.vault_lock import vault_mutation_lock

#: Versions the upgrade accepts through the existing chain (mvp-0.25's own
#: upgrade takes them to the immediate predecessor first): mvp-0.9 to mvp-0.24.
_CHAINED_PREDECESSORS = SUCCESSOR_CHAIN[:SUCCESSOR_CHAIN.index(METHOD_EXPLICIT_ALGORITHM_VERSION)]

#: An earlier link's refusal already names its own step; it passes through unprefixed.
_STEP_REFUSAL = re.compile(r"^mvp-0\.\d+ step refused: ")

_HELD_NOTE = (
    "{count} attempt(s) whose current grade cites no assessment contract are held for review "
    "(grade_contract_unrecorded) until a regrade or an adjudication records one: {ids}"
)


def upgrade_to_mvp026(root: Path, *, clock: Clock | None = None) -> UpgradeResult:
    """mvp-0.25 (or mvp-0.9 to mvp-0.24, through the chain) -> mvp-0.26: regrade contracts.

    On a vault already at mvp-0.26 whose activation did not commit (the
    process died after publishing the config), it completes the activation."""

    # The whole upgrade runs under the vault mutation lock (re-entrant in this
    # thread: opening the repository takes it again), so an item edit, a
    # proposal accept or another upgrade lands wholly before it or after it.
    with vault_mutation_lock(Path(root), purpose="upgrade_mvp026"):
        return _upgrade(Path(root), clock=clock)


def _upgrade(root: Path, *, clock: Clock | None) -> UpgradeResult:
    vault = load_vault(root)
    original = vault.config.algorithms.algorithm_version
    target = REGRADE_CONTRACT_ALGORITHM_VERSION
    predecessor = METHOD_EXPLICIT_ALGORITHM_VERSION
    if original == target:
        resumed = _activate(root, predecessor=predecessor, target=target, publish=False, clock=clock)
        if resumed is None:
            return UpgradeResult(upgraded=False, from_version=original, to_version=target,
                                 problems=[f"vault is already {target}"])
        note = f"completed the interrupted activation of {target}"
        if resumed:
            note += ": " + _held_note(resumed)
        return UpgradeResult(upgraded=True, from_version=target, to_version=target, notes=[note])
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
        chained = upgrade_to_mvp025(root, clock=clock)
        chained_notes = list(chained.notes or [])
        if not chained.upgraded:
            return UpgradeResult(
                upgraded=False, from_version=original, to_version=target, notes=chained_notes,
                problems=[
                    problem if _STEP_REFUSAL.match(problem) else f"{predecessor} step refused: {problem}"
                    for problem in chained.problems
                ],
            )
    held = _activate(root, predecessor=predecessor, target=target, publish=True, clock=clock) or []
    notes = list(chained_notes)
    if held:
        notes.append(_held_note(held))
    return UpgradeResult(upgraded=True, from_version=original, to_version=target, notes=notes)


def _held_note(held: list[dict[str, Any]]) -> str:
    return _HELD_NOTE.format(count=len(held), ids=", ".join(sorted(str(row["attempt_id"]) for row in held)))


def _activate(
    root: Path, *, predecessor: str, target: str, publish: bool, clock: Clock | None
) -> list[dict[str, Any]] | None:
    """Activate ``target`` over the vault at ``root`` in one transaction.

    ``publish``: the vault is at ``predecessor``; the config's publication is
    the transaction's last step. Otherwise the vault is already labelled
    ``target`` and this completes an activation that did not commit: it does
    nothing (and returns None) unless the predecessor's state is still there,
    which shows as an attempt the successor holds without its recorded hold,
    or as the predecessor's rebuild receipt being the latest.

    Returns the attempts the activation holds."""

    vault = load_vault(root)
    expected = predecessor if publish else target
    if vault.config.algorithms.algorithm_version != expected:  # pragma: no cover - the caller read it under the lock
        raise RuntimeError(f"{root}: algorithm_version changed during the upgrade to {target}")
    sqlite_path = VaultPaths(vault.root, vault.config).sqlite_path
    repository = open_vault_repository(vault.root, sqlite_path)
    config_path = root / "learnloop.toml"
    published = False
    try:
        with repository.atomic():
            vault.config.algorithms.algorithm_version = target
            # The attempts this successor reinterprets: their current grading
            # epoch cites no contract, so replay now holds them. Only their
            # learning objects are replayed; every other attempt reads as it
            # did. Read inside the transaction: nothing writes between this
            # scan and the publication.
            held = unrecorded_epoch_attempts(vault, repository)
            if not publish:
                with repository.connection() as connection:
                    recorded = contract_unrecorded_attempts(connection, [row["attempt_id"] for row in held])
                held = [row for row in held if row["attempt_id"] not in recorded]
                latest = repository.latest_derived_state_rebuild()
                pending = bool(held) and bool({str(row["learning_object_id"]) for row in held} & set(vault.learning_objects))
                if not pending and (latest is None or latest.get("algorithm_version") != predecessor):
                    return None
            # The predecessor's manifest, frozen from its own config (only
            # the version line differs) exactly as a clean upgrade freezes it.
            vault.config.algorithms.algorithm_version = predecessor
            registry_service.freeze_manifest(vault, repository, algorithm_version=predecessor, clock=clock)
            vault.config.algorithms.algorithm_version = target
            # Only learning objects the vault still holds can be replayed (an
            # attempt on a removed one never is, by any rebuild).
            replayable = sorted({str(row["learning_object_id"]) for row in held} & set(vault.learning_objects))
            if replayable:
                rebuild_all_derived_state(vault, repository, learning_object_ids=replayable, clock=clock)
            activate_p0_projection(vault, repository, from_version=predecessor, clock=clock)
            registry_service.refresh(vault, repository, clock=clock)
            if publish:
                # Last: the commit follows the publication, so the database
                # never holds the successor's state under the predecessor's label.
                _publish_algorithm_version(config_path, predecessor, target)
                published = True
    except BaseException as failure:
        if published:
            # The transaction rolled back after the config named the
            # successor: name the predecessor again. Should that fail too, the
            # vault is left in the resumable state (the successor's label over
            # the predecessor's database).
            try:
                _publish_algorithm_version(config_path, target, predecessor)
            except Exception as restore_failure:  # pragma: no cover - a second failure on the same file
                failure.add_note(
                    f"{config_path} still names {target} over the {predecessor} database "
                    f"({restore_failure}); run `learnloop upgrade --to {target}` again to complete it"
                )
        raise
    return held


def _publish_algorithm_version(config_path: Path, from_version: str, to_version: str) -> None:
    """The atomic config rename (``ops.vault_upgrade.rewrite_algorithm_version``),
    made durable before the caller commits: the file and its directory are
    fsynced, so after a power loss the rename is never older than the commit."""

    rewrite_algorithm_version(config_path, from_version, to_version)
    with open(config_path, "rb") as handle:
        os.fsync(handle.fileno())
    directory = os.open(config_path.parent, os.O_RDONLY)
    try:
        os.fsync(directory)
    finally:
        os.close(directory)


#: A descriptive name for the same upgrade.
upgrade_to_regrade_contracts = upgrade_to_mvp026

__all__ = ["upgrade_to_mvp026", "upgrade_to_regrade_contracts"]

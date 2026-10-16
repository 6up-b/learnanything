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
* replays, in one transaction and before the atomic config rename, exactly
  the learning objects holding an attempt whose current grading epoch it
  reinterprets (an uncited epoch it now holds), then re-projects the same
  projection namespace. Every other attempt replays as it did under
  ``mvp-0.25`` (its current epoch cites the contract its first live row did),
  so nothing else is rebuilt. Its notes name the attempts it holds.

Nothing is rewritten: evidence rows, contracts and blind records keep their
rows; replay records the hold on the attempt's derived review reason. There is
no kill switch (the earlier writer is the defect); rolling the version back is
restore-only.
"""

from __future__ import annotations

import re
from pathlib import Path

from learnloop.algorithm_versions import (
    METHOD_EXPLICIT_ALGORITHM_VERSION,
    REGRADE_CONTRACT_ALGORITHM_VERSION,
    SUCCESSOR_CHAIN,
)
from learnloop.attempts.attempts import unrecorded_epoch_attempts
from learnloop.clock import Clock
from learnloop.method_explicit_upgrade import upgrade_to_mvp025
from learnloop.ops.vault_upgrade import UpgradeResult, rewrite_algorithm_version
from learnloop.params import parameter_registry as registry_service
from learnloop.substrate.p0_projection import activate_p0_projection
from learnloop.substrate.rebuild_orchestrator import rebuild_all_derived_state
from learnloop.vault.loader import load_vault
from learnloop.vault.paths import VaultPaths
from learnloop.vault.repository import open_vault_repository

#: Versions the upgrade accepts through the existing chain (mvp-0.25's own
#: upgrade takes them to the immediate predecessor first): mvp-0.9 to mvp-0.24.
_CHAINED_PREDECESSORS = SUCCESSOR_CHAIN[:SUCCESSOR_CHAIN.index(METHOD_EXPLICIT_ALGORITHM_VERSION)]

#: An earlier link's refusal already names its own step; it passes through unprefixed.
_STEP_REFUSAL = re.compile(r"^mvp-0\.\d+ step refused: ")


def upgrade_to_mvp026(root: Path, *, clock: Clock | None = None) -> UpgradeResult:
    """mvp-0.25 (or mvp-0.9 to mvp-0.24, through the chain) -> mvp-0.26: regrade contracts."""

    vault = load_vault(root)
    original = vault.config.algorithms.algorithm_version
    target = REGRADE_CONTRACT_ALGORITHM_VERSION
    predecessor = METHOD_EXPLICIT_ALGORITHM_VERSION
    if original == target:
        return UpgradeResult(upgraded=False, from_version=original, to_version=target,
                             problems=[f"vault is already {target}"])
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
        vault = load_vault(root)
    current = vault.config.algorithms.algorithm_version

    sqlite_path = VaultPaths(vault.root, vault.config).sqlite_path
    repository = open_vault_repository(vault.root, sqlite_path)
    registry_service.freeze_manifest(vault, repository, algorithm_version=current, clock=clock)
    vault.config.algorithms.algorithm_version = target
    # The attempts this successor reinterprets: their current grading epoch
    # cites no contract, so replay now holds them. Only their learning
    # objects are replayed; every other attempt reads as it did.
    held = unrecorded_epoch_attempts(vault, repository)
    # Only learning objects the vault still holds can be replayed (an attempt
    # on a removed one never is, by any rebuild).
    replayable = sorted({str(row["learning_object_id"]) for row in held} & set(vault.learning_objects))
    if replayable:
        rebuild_all_derived_state(vault, repository, learning_object_ids=replayable, clock=clock)
    activate_p0_projection(vault, repository, from_version=current, clock=clock)
    registry_service.refresh(vault, repository, clock=clock)
    rewrite_algorithm_version(root / "learnloop.toml", current, target)
    notes = list(chained_notes)
    if held:
        notes.append(
            f"{len(held)} attempt(s) whose current grade cites no assessment contract are held for review "
            "(grade_contract_unrecorded) until a regrade or an adjudication records one: "
            + ", ".join(sorted(str(row["attempt_id"]) for row in held))
        )
    return UpgradeResult(upgraded=True, from_version=original, to_version=target, notes=notes)


#: A descriptive name for the same upgrade.
upgrade_to_regrade_contracts = upgrade_to_mvp026

__all__ = ["upgrade_to_mvp026", "upgrade_to_regrade_contracts"]

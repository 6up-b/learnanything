"""``learnloop upgrade --to mvp-0.13``: "Write what you can" replaces "I don't know".

The stuck prompt was built as ``mvp-0.11`` over ``mvp-0.10``; it merged after
Phase 6 placement took ``mvp-0.11`` and Slice 2 T1 recurrence groups took
``mvp-0.12``, so it is ``mvp-0.13``, the next link of the linear chain (the
split PLUS placement PLUS recurrence groups PLUS the stuck prompt).

The upgrade:

* accepts the immediate predecessor (``mvp-0.12``), or ``mvp-0.9`` /
  ``mvp-0.10`` / ``mvp-0.11`` by running
  :func:`learnloop.diagnosis.recurrence.upgrade.upgrade_to_mvp012` first. That
  step carries T1's same-answer/different-cause guard and checks it BEFORE any
  chained step, so a guard refusal refuses this upgrade too and leaves the
  vault at its original version; if the chained steps succeed and this step
  then fails, the vault is left at the valid ``mvp-0.12``. Anything older is
  refused;
* changes what NEW answers persist (``practice_attempts.declared_stuck``,
  migration 178; the grader's stuck reading on the blind record and in
  ``judgment_ledger``; the ``answer_display`` reveal kind, migration 179) and
  never the authority-propagation projection, so like every successor it is
  a tag change plus an idempotent rebuild of the same projection namespace,
  prepared before the atomic config rename.

Nothing is rewritten: historical ``dont_know`` attempts keep their meaning and
mass, and recurrence groups stay in force (``RECURRENCE_GROUP_VERSIONS`` is
chain-derived). Kill switch: ``stuck_prompt.enabled = false`` restores "I don't
know" for new answers without a downgrade; rolling the version back is
restore-only.

This module sits at the top level because it composes ``ops.vault_upgrade``
with ``diagnosis.recurrence.upgrade``: ``attempts`` (the stuck prompt's own
package) and ``ops`` are both reachable from ``diagnosis``, so importing the
mvp-0.12 step from either would add a cross-package cycle.
"""

from __future__ import annotations

from pathlib import Path

from learnloop.algorithm_versions import (
    DIAGNOSIS_SPLIT_ALGORITHM_VERSION,
    PLACEMENT_ALGORITHM_VERSION,
    RECURRENCE_GROUP_ALGORITHM_VERSION,
    REVEAL_LEDGER_ALGORITHM_VERSION,
    STUCK_PROMPT_ALGORITHM_VERSION,
)
from learnloop.clock import Clock
from learnloop.db.repositories import Repository
from learnloop.diagnosis.recurrence.upgrade import upgrade_to_mvp012
from learnloop.ops.vault_upgrade import UpgradeResult, rewrite_algorithm_version
from learnloop.params import parameter_registry as registry_service
from learnloop.substrate.p0_projection import activate_p0_projection
from learnloop.vault.loader import load_vault
from learnloop.vault.paths import VaultPaths

#: Versions the upgrade accepts through the existing chain (mvp-0.12's own
#: upgrade, with its guard, takes them to the immediate predecessor first).
_CHAINED_PREDECESSORS = (
    REVEAL_LEDGER_ALGORITHM_VERSION,
    DIAGNOSIS_SPLIT_ALGORITHM_VERSION,
    PLACEMENT_ALGORITHM_VERSION,
)


def upgrade_to_mvp013(root: Path, *, clock: Clock | None = None) -> UpgradeResult:
    vault = load_vault(root)
    original = vault.config.algorithms.algorithm_version
    target = STUCK_PROMPT_ALGORITHM_VERSION
    if original == target:
        return UpgradeResult(upgraded=False, from_version=original, to_version=target,
                             problems=[f"vault is already {target}"])
    if original != RECURRENCE_GROUP_ALGORITHM_VERSION and original not in _CHAINED_PREDECESSORS:
        return UpgradeResult(
            upgraded=False, from_version=original, to_version=target,
            problems=[
                f"cannot upgrade from {original!r}; only {RECURRENCE_GROUP_ALGORITHM_VERSION!r} (or "
                f"{PLACEMENT_ALGORITHM_VERSION!r} / {DIAGNOSIS_SPLIT_ALGORITHM_VERSION!r} / "
                f"{REVEAL_LEDGER_ALGORITHM_VERSION!r}, through it) may activate {target}"
            ],
        )
    chained_notes: list[str] = []
    if original != RECURRENCE_GROUP_ALGORITHM_VERSION:
        # The chain's mvp-0.12 step checks T1's guard before it takes any
        # step of its own; a refusal there leaves the vault where it was.
        # The guard is advisory by default (owner batch 2), so its status
        # comes back as notes, which this result passes on.
        chained = upgrade_to_mvp012(root, clock=clock)
        chained_notes = list(chained.notes or [])
        if not chained.upgraded:
            return UpgradeResult(
                upgraded=False, from_version=original, to_version=target,
                problems=[
                    f"{RECURRENCE_GROUP_ALGORITHM_VERSION} step refused: {problem}"
                    for problem in chained.problems
                ],
            )
        vault = load_vault(root)
    current = vault.config.algorithms.algorithm_version

    sqlite_path = VaultPaths(vault.root, vault.config).sqlite_path
    # Construction applies the migrations the stuck answer needs (178; 179 for
    # the worked-answer reveal kind).
    repository = Repository(sqlite_path)
    registry_service.freeze_manifest(vault, repository, algorithm_version=current, clock=clock)
    vault.config.algorithms.algorithm_version = target
    activate_p0_projection(vault, repository, from_version=current, clock=clock)
    registry_service.refresh(vault, repository, clock=clock)
    rewrite_algorithm_version(root / "learnloop.toml", current, target)
    return UpgradeResult(upgraded=True, from_version=original, to_version=target, notes=chained_notes)


__all__ = ["upgrade_to_mvp013"]

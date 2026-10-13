"""``learnloop upgrade --to mvp-0.14``: daily-loop DL1, the finite daily plan.

DL1 (``daily_plan_v1``, spec_daily_loop_v1.md §11) was built as ``mvp-0.12``
over ``mvp-0.11``; it merged after Slice 2 T1 recurrence groups took
``mvp-0.12`` and the stuck prompt took ``mvp-0.13``, so it is ``mvp-0.14``, the
next link of the linear chain (the split PLUS placement PLUS recurrence groups
PLUS the stuck prompt PLUS the plan).

The upgrade:

* accepts the immediate predecessor (``mvp-0.13``), or ``mvp-0.9`` to
  ``mvp-0.12`` by running :func:`learnloop.stuck_prompt_upgrade.upgrade_to_mvp013`
  first. Below ``mvp-0.12`` that step runs T1's
  :func:`~learnloop.diagnosis.recurrence.upgrade.upgrade_to_mvp012`, whose
  same-answer/different-cause guard is checked BEFORE any chained step, so a
  guard refusal refuses this upgrade too and leaves the vault at its original
  version; if the chained steps succeed and this step then fails, the vault is
  left at the valid ``mvp-0.13``. Anything older is refused;
* changes what Today SERVES (a finite plan of remembered minutes, split across
  repair, maintain, new and push and chosen block by block; goal-optional
  re-entry; reading blocks) and never the authority-propagation projection, so
  like every successor it is a tag change plus an idempotent rebuild of the
  same projection namespace, prepared before the atomic config rename.

Nothing is rewritten: the plan tables (migration 180) start empty and replay
never reads them. Kill switch: ``plan.enabled = false`` restores mvp-0.13's
Today exactly without a downgrade; rolling the version back is restore-only.

This module sits at the top level beside ``stuck_prompt_upgrade`` for the same
reason: it composes the chain's earlier links, which live in ``ops`` and
``diagnosis.recurrence``.
"""

from __future__ import annotations

from pathlib import Path

from learnloop.algorithm_versions import (
    DAILY_PLAN_ALGORITHM_VERSION,
    DIAGNOSIS_SPLIT_ALGORITHM_VERSION,
    PLACEMENT_ALGORITHM_VERSION,
    RECURRENCE_GROUP_ALGORITHM_VERSION,
    REVEAL_LEDGER_ALGORITHM_VERSION,
    STUCK_PROMPT_ALGORITHM_VERSION,
)
from learnloop.clock import Clock
from learnloop.db.repositories import Repository
from learnloop.ops.vault_upgrade import UpgradeResult, rewrite_algorithm_version
from learnloop.params import parameter_registry as registry_service
from learnloop.stuck_prompt_upgrade import upgrade_to_mvp013
from learnloop.substrate.p0_projection import activate_p0_projection
from learnloop.vault.loader import load_vault
from learnloop.vault.paths import VaultPaths

#: Versions the upgrade accepts through the existing chain (mvp-0.13's own
#: upgrade takes them to the immediate predecessor first; below mvp-0.12 it
#: runs mvp-0.12's, with T1's guard checked before any chained step).
_CHAINED_PREDECESSORS = (
    REVEAL_LEDGER_ALGORITHM_VERSION,
    DIAGNOSIS_SPLIT_ALGORITHM_VERSION,
    PLACEMENT_ALGORITHM_VERSION,
    RECURRENCE_GROUP_ALGORITHM_VERSION,
)


def upgrade_to_mvp014(root: Path, *, clock: Clock | None = None) -> UpgradeResult:
    vault = load_vault(root)
    original = vault.config.algorithms.algorithm_version
    target = DAILY_PLAN_ALGORITHM_VERSION
    if original == target:
        return UpgradeResult(upgraded=False, from_version=original, to_version=target,
                             problems=[f"vault is already {target}"])
    if original != STUCK_PROMPT_ALGORITHM_VERSION and original not in _CHAINED_PREDECESSORS:
        return UpgradeResult(
            upgraded=False, from_version=original, to_version=target,
            problems=[
                f"cannot upgrade from {original!r}; only {STUCK_PROMPT_ALGORITHM_VERSION!r} (or "
                f"{RECURRENCE_GROUP_ALGORITHM_VERSION!r} / {PLACEMENT_ALGORITHM_VERSION!r} / "
                f"{DIAGNOSIS_SPLIT_ALGORITHM_VERSION!r} / {REVEAL_LEDGER_ALGORITHM_VERSION!r}, "
                f"through it) may activate {target}"
            ],
        )
    if original != STUCK_PROMPT_ALGORITHM_VERSION:
        # The chain's mvp-0.13 step (and, below mvp-0.12, T1's guarded
        # mvp-0.12 step before it) refuses before it takes any step of its own;
        # a refusal there leaves the vault where it was.
        chained = upgrade_to_mvp013(root, clock=clock)
        if not chained.upgraded:
            return UpgradeResult(
                upgraded=False, from_version=original, to_version=target,
                problems=[
                    problem if problem.startswith(f"{RECURRENCE_GROUP_ALGORITHM_VERSION} step refused: ")
                    else f"{STUCK_PROMPT_ALGORITHM_VERSION} step refused: {problem}"
                    for problem in chained.problems
                ],
            )
        vault = load_vault(root)
    current = vault.config.algorithms.algorithm_version

    sqlite_path = VaultPaths(vault.root, vault.config).sqlite_path
    # Construction applies the additive migration the plan needs (180's
    # daily_plans and attention_blocks columns) before anything reads them.
    repository = Repository(sqlite_path)
    registry_service.freeze_manifest(vault, repository, algorithm_version=current, clock=clock)
    vault.config.algorithms.algorithm_version = target
    activate_p0_projection(vault, repository, from_version=current, clock=clock)
    registry_service.refresh(vault, repository, clock=clock)
    rewrite_algorithm_version(root / "learnloop.toml", current, target)
    return UpgradeResult(upgraded=True, from_version=original, to_version=target)


__all__ = ["upgrade_to_mvp014"]

"""``learnloop upgrade --to mvp-0.15``: UX Phase 1's reading step.

``mvp-0.15`` here is a PLACEHOLDER tag: the branch ``ux/phase1-first-run``
built it over ``mvp-0.14`` while main's chain moved on past ``mvp-0.15``, and
the merge relabels it to the next free tag (the module and its function with
it), as every branch-built successor before it. It is the next link of the
linear chain: the split PLUS placement PLUS recurrence groups PLUS the stuck
prompt PLUS the plan PLUS the reading step (round-2 re-review F2;
spec_daily_loop_v1 L6, §11).

The upgrade:

* accepts the immediate predecessor (``mvp-0.14``), or ``mvp-0.9`` to
  ``mvp-0.13`` by running :func:`learnloop.daily_plan_upgrade.upgrade_to_mvp014`
  first, whose own chain checks T1's same-answer/different-cause guard before
  any chained step (a refusal there leaves the vault where it was; if the
  chained steps succeed and this step then fails, the vault is left at the
  valid ``mvp-0.14``). Anything older is refused;
* changes what the plan's reading block SERVES (the section to continue: from
  the furthest section read, never front or back matter while a chapter is
  left) and never the authority-propagation projection, so like every
  successor it is a tag change plus an idempotent rebuild of the same
  projection namespace, prepared before the atomic config rename.

Nothing is rewritten: plans already composed keep their rows, and replay never
reads the selection. Kill switch: ``plan.reading_from_furthest = false``
restores mvp-0.14's reading block exactly without a downgrade; rolling the
version back is restore-only.
"""

from __future__ import annotations

from pathlib import Path

from learnloop.algorithm_versions import (
    DAILY_PLAN_ALGORITHM_VERSION,
    DIAGNOSIS_SPLIT_ALGORITHM_VERSION,
    PLACEMENT_ALGORITHM_VERSION,
    READING_FROM_FURTHEST_ALGORITHM_VERSION,
    RECURRENCE_GROUP_ALGORITHM_VERSION,
    REVEAL_LEDGER_ALGORITHM_VERSION,
    STUCK_PROMPT_ALGORITHM_VERSION,
)
from learnloop.clock import Clock
from learnloop.daily_plan_upgrade import upgrade_to_mvp014
from learnloop.db.repositories import Repository
from learnloop.ops.vault_upgrade import UpgradeResult, rewrite_algorithm_version
from learnloop.params import parameter_registry as registry_service
from learnloop.substrate.p0_projection import activate_p0_projection
from learnloop.vault.loader import load_vault
from learnloop.vault.paths import VaultPaths

#: Versions the upgrade accepts through the existing chain (mvp-0.14's own
#: upgrade takes them to the immediate predecessor first).
_CHAINED_PREDECESSORS = (
    REVEAL_LEDGER_ALGORITHM_VERSION,
    DIAGNOSIS_SPLIT_ALGORITHM_VERSION,
    PLACEMENT_ALGORITHM_VERSION,
    RECURRENCE_GROUP_ALGORITHM_VERSION,
    STUCK_PROMPT_ALGORITHM_VERSION,
)


def upgrade_to_mvp015(root: Path, *, clock: Clock | None = None) -> UpgradeResult:
    vault = load_vault(root)
    original = vault.config.algorithms.algorithm_version
    target = READING_FROM_FURTHEST_ALGORITHM_VERSION
    if original == target:
        return UpgradeResult(upgraded=False, from_version=original, to_version=target,
                             problems=[f"vault is already {target}"])
    if original != DAILY_PLAN_ALGORITHM_VERSION and original not in _CHAINED_PREDECESSORS:
        return UpgradeResult(
            upgraded=False, from_version=original, to_version=target,
            problems=[
                f"cannot upgrade from {original!r}; only {DAILY_PLAN_ALGORITHM_VERSION!r} (or "
                f"{STUCK_PROMPT_ALGORITHM_VERSION!r} / {RECURRENCE_GROUP_ALGORITHM_VERSION!r} / "
                f"{PLACEMENT_ALGORITHM_VERSION!r} / {DIAGNOSIS_SPLIT_ALGORITHM_VERSION!r} / "
                f"{REVEAL_LEDGER_ALGORITHM_VERSION!r}, through it) may activate {target}"
            ],
        )
    chained_notes: list[str] = []
    if original != DAILY_PLAN_ALGORITHM_VERSION:
        # The chain's mvp-0.14 step (and its own chain below it) refuses
        # before it takes any step of its own; a refusal there leaves the
        # vault where it was. Its problems already name the refusing step.
        chained = upgrade_to_mvp014(root, clock=clock)
        chained_notes = list(chained.notes or [])
        if not chained.upgraded:
            return UpgradeResult(
                upgraded=False, from_version=original, to_version=target,
                problems=[
                    problem if " step refused: " in problem
                    else f"{DAILY_PLAN_ALGORITHM_VERSION} step refused: {problem}"
                    for problem in chained.problems
                ],
            )
        vault = load_vault(root)
    current = vault.config.algorithms.algorithm_version

    sqlite_path = VaultPaths(vault.root, vault.config).sqlite_path
    repository = Repository(sqlite_path)
    registry_service.freeze_manifest(vault, repository, algorithm_version=current, clock=clock)
    vault.config.algorithms.algorithm_version = target
    activate_p0_projection(vault, repository, from_version=current, clock=clock)
    registry_service.refresh(vault, repository, clock=clock)
    rewrite_algorithm_version(root / "learnloop.toml", current, target)
    return UpgradeResult(upgraded=True, from_version=original, to_version=target, notes=chained_notes)


__all__ = ["upgrade_to_mvp015"]

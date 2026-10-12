"""``learnloop upgrade --to mvp-0.11``: activate recurrence with authority (Slice 2 §3.4).

The playbook's explicit upgrade, owner-run (implementation_goal.md §1a):

* refuses anything but the immediate predecessor (``mvp-0.10``);
* refuses unless the same-answer/different-cause guard passes FOR THE
  CONFIGURED JUDGE: every required negative (the built-in suite plus every
  registered M1 case) judged by the model AND reasoning effort the
  ``same_cause_judge`` route resolves to, under the current prompt and input, and none of its standing
  verdicts ``same`` (§3.6: any false merge blocks the switch);
* PREPARES the groups (built from the ledgers already recorded, not yet in
  force) and the P0 projection receipt BEFORE the atomic config rename, and
  puts the groups in force only AFTER it: a failure anywhere before the
  rename leaves ``mvp-0.10`` with no group read by any consumer.

Raw history is never rewritten. The switch applies groups to every grouping
from the next normalization on; a full rebuild (``learnloop rebuild``)
re-applies them to past promotions and escalations, which is what the shadow
rebuild previews. Kill switch: ``recurrence.enabled = false``. Rolling the
version back is restore-only.
"""

from __future__ import annotations

import logging
from pathlib import Path

from learnloop.algorithm_versions import (
    DIAGNOSIS_SPLIT_ALGORITHM_VERSION,
    RECURRENCE_GROUP_ALGORITHM_VERSION,
)
from learnloop.clock import Clock
from learnloop.db.repositories import Repository
from learnloop.diagnosis.recurrence.guard import configured_judge_model, guard_status
from learnloop.ops.vault_upgrade import UpgradeResult, rewrite_algorithm_version
from learnloop.params import parameter_registry as registry_service
from learnloop.substrate.p0_projection import activate_p0_projection
from learnloop.substrate.recurrence_groups import activate_recurrence_groups, prepare_recurrence_groups
from learnloop.vault.loader import load_vault
from learnloop.vault.paths import VaultPaths

LOG = logging.getLogger(__name__)


def upgrade_to_mvp011(root: Path, *, clock: Clock | None = None) -> UpgradeResult:
    vault = load_vault(root)
    current = vault.config.algorithms.algorithm_version
    target = RECURRENCE_GROUP_ALGORITHM_VERSION
    if current == target:
        return UpgradeResult(upgraded=False, from_version=current, to_version=target,
                             problems=[f"vault is already {target}"])
    if current != DIAGNOSIS_SPLIT_ALGORITHM_VERSION:
        return UpgradeResult(
            upgraded=False, from_version=current, to_version=target,
            problems=[f"cannot upgrade from {current!r}; only {DIAGNOSIS_SPLIT_ALGORITHM_VERSION!r} may activate {target}"],
        )
    sqlite_path = VaultPaths(vault.root, vault.config).sqlite_path
    # Construction applies the additive migration the successor needs.
    repository = Repository(sqlite_path)
    expected_model = configured_judge_model(vault)
    if not expected_model:
        return UpgradeResult(
            upgraded=False, from_version=current, to_version=target,
            problems=[
                "cannot tell which model the same-cause judge route resolves to (its profile names no model); "
                "set the model on the ai.routing.same_cause_judge profile so the guard can be checked for it"
            ],
        )
    guard = guard_status(repository, judge_model=expected_model)
    if not guard["passed"]:
        problems = []
        if guard["false_merges"]:
            problems.append(
                f"the same-answer/different-cause guard has {len(guard['false_merges'])} false merge(s) from "
                f"{expected_model!r} under the current judge prompt; fix the judge (route or prompt) and rerun "
                "`learnloop recurrence guard` before switching"
            )
        if guard["missing"]:
            seen = guard_status(repository)["judge_models_seen"]
            other = [model for model in seen if model != expected_model]
            note = f" (verdicts exist from {other}, which do not count)" if other else ""
            problems.append(
                f"{expected_model!r}, the judge (model@effort) the same-cause route resolves to, has not judged "
                f"{len(guard['missing'])} of {guard['negatives']} required planted pairs under prompt "
                f"{guard['prompt_version']}{note}; rerun `learnloop recurrence guard` for this judge "
                "(`--dry-run` first)"
            )
        return UpgradeResult(upgraded=False, from_version=current, to_version=target, problems=problems)
    registry_service.freeze_manifest(vault, repository, algorithm_version=current, clock=clock)
    vault.config.algorithms.algorithm_version = target
    # Prepared, NOT in force: no consumer reads these groups until activation.
    prepare_recurrence_groups(repository)
    activate_p0_projection(vault, repository, from_version=current, clock=clock)
    registry_service.refresh(vault, repository, clock=clock)
    rewrite_algorithm_version(root / "learnloop.toml", current, target)
    try:
        activate_recurrence_groups(load_vault(root), repository)
    except Exception:  # noqa: BLE001 - the next normalization or vault open activates them
        LOG.warning("recurrence groups were prepared but not yet activated", exc_info=True)
    return UpgradeResult(upgraded=True, from_version=current, to_version=target)


__all__ = ["upgrade_to_mvp011"]

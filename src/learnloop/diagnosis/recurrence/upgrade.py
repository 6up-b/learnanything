"""``learnloop upgrade --to mvp-0.11``: activate recurrence with authority (Slice 2 §3.4).

The playbook's explicit upgrade, owner-run (implementation_goal.md §1a):

* refuses anything but the immediate predecessor (``mvp-0.10``);
* refuses while the same-answer/different-cause guard has a false merge or
  has not judged every negative pair under the current judge prompt (§3.6:
  any false merge blocks the switch);
* prepares the candidate projection (the recurrence groups, built from the
  ledgers already recorded) and the P0 projection receipt BEFORE the atomic
  config rename, so a failed preparation leaves ``mvp-0.10`` readable.

Raw history is never rewritten. The switch applies groups to every grouping
from the next normalization on; a full rebuild (``learnloop rebuild``)
re-applies them to past promotions and escalations, which is what the shadow
rebuild previews. Kill switch: ``recurrence.enabled = false``. Rolling the
version back is restore-only.
"""

from __future__ import annotations

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
from learnloop.substrate.recurrence_groups import refresh_recurrence_groups
from learnloop.vault.loader import load_vault
from learnloop.vault.paths import VaultPaths


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
    guard = guard_status(repository)
    if not guard["passed"]:
        problems = []
        if guard["false_merges"]:
            problems.append(
                f"the same-answer/different-cause guard has {len(guard['false_merges'])} false merge(s) "
                "under the current judge prompt; fix the judge (route or prompt) and rerun "
                "`learnloop recurrence guard` before switching"
            )
        if guard["missing"]:
            problems.append(
                f"the guard has not judged {len(guard['missing'])} of {guard['negatives']} planted pairs under "
                f"prompt {guard['prompt_version']}; run `learnloop recurrence guard --dry-run`, then without it"
            )
        return UpgradeResult(upgraded=False, from_version=current, to_version=target, problems=problems)
    expected_model = configured_judge_model(vault)
    if expected_model and guard["judge_models_seen"] and expected_model not in guard["judge_models_seen"]:
        return UpgradeResult(
            upgraded=False, from_version=current, to_version=target,
            problems=[
                f"the guard verdicts came from {guard['judge_models_seen']}, but the same-cause judge route now "
                f"resolves to {expected_model!r}; rerun `learnloop recurrence guard` for this judge"
            ],
        )
    registry_service.freeze_manifest(vault, repository, algorithm_version=current, clock=clock)
    vault.config.algorithms.algorithm_version = target
    refresh_recurrence_groups(vault, repository, force=True)
    activate_p0_projection(vault, repository, from_version=current, clock=clock)
    registry_service.refresh(vault, repository, clock=clock)
    rewrite_algorithm_version(root / "learnloop.toml", current, target)
    return UpgradeResult(upgraded=True, from_version=current, to_version=target)


__all__ = ["upgrade_to_mvp011"]

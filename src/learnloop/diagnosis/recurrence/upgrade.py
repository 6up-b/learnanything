"""``learnloop upgrade --to mvp-0.12``: activate recurrence with authority (Slice 2 §3.4).

T1 was built as ``mvp-0.11`` over ``mvp-0.10``; it merged after Phase 6 took
``mvp-0.11`` (placement), so it is ``mvp-0.12``, the next link of the linear
chain (the split PLUS placement PLUS recurrence groups).

The playbook's explicit upgrade, owner-run (implementation_goal.md §1a):

* accepts the immediate predecessor (``mvp-0.11``), or ``mvp-0.10`` /
  ``mvp-0.9`` by running :func:`learnloop.ops.vault_upgrade.upgrade_to_mvp011`
  first (which itself chains through ``mvp-0.10``); anything else is refused.
  The guard below is checked BEFORE any chained step, so a refusal leaves the
  vault at its original version; if a chained step succeeds and this step
  then fails, the vault is left at the valid ``mvp-0.11``;
* refuses unless the same-answer/different-cause guard passes FOR THE
  CONFIGURED JUDGE: every required negative (the built-in suite plus every
  registered M1 case) judged by the model AND reasoning effort the
  ``same_cause_judge`` route resolves to, under the current prompt and input, and none of its standing
  verdicts ``same`` (§3.6: any false merge blocks the switch);
* and refuses unless the citation path was checked too (second review F2):
  at least one registered M1 run case whose diagnoser link was recorded
  under the current diagnosis prompt in the vault's history mode, and no
  validated M1 citation linking a planted B answer to its A answer;
* PREPARES the groups (built from the ledgers already recorded, not yet in
  force) and the P0 projection receipt BEFORE the atomic config rename, and
  puts the groups in force only AFTER it: a failure anywhere before the
  rename leaves the predecessor with no group read by any consumer.

Raw history is never rewritten. The switch applies groups to every grouping
from the next normalization on. Promotions, deferral exits and escalation
receipts are decisions recorded when they were made: a rebuild never re-takes
them (replay never re-normalizes). It recomputes only the group projection
from the ledgers, which the live path refreshes on every verdict, so a
same-version rebuild reproduces the live projection; a verdict recorded later
regroups FUTURE decisions only (second review F5). Kill switch:
``recurrence.enabled = false``. Rolling the version back is restore-only.
"""

from __future__ import annotations

import logging
from pathlib import Path

from learnloop.algorithm_versions import (
    DIAGNOSIS_SPLIT_ALGORITHM_VERSION,
    PLACEMENT_ALGORITHM_VERSION,
    RECURRENCE_GROUP_ALGORITHM_VERSION,
    REVEAL_LEDGER_ALGORITHM_VERSION,
)
from learnloop.clock import Clock
from learnloop.db.repositories import Repository
from learnloop.diagnosis.recurrence.guard import configured_judge_model, guard_status
from learnloop.ops.vault_upgrade import UpgradeResult, rewrite_algorithm_version, upgrade_to_mvp011
from learnloop.params import parameter_registry as registry_service
from learnloop.substrate.p0_projection import activate_p0_projection
from learnloop.substrate.recurrence_groups import activate_recurrence_groups, prepare_recurrence_groups
from learnloop.vault.loader import load_vault
from learnloop.vault.paths import VaultPaths

LOG = logging.getLogger(__name__)


#: Versions the upgrade accepts: the immediate predecessor and, through the
#: existing chain, the two before it.
_CHAINED_PREDECESSORS = (REVEAL_LEDGER_ALGORITHM_VERSION, DIAGNOSIS_SPLIT_ALGORITHM_VERSION)


def upgrade_to_mvp012(root: Path, *, clock: Clock | None = None) -> UpgradeResult:
    vault = load_vault(root)
    original = vault.config.algorithms.algorithm_version
    target = RECURRENCE_GROUP_ALGORITHM_VERSION
    if original == target:
        return UpgradeResult(upgraded=False, from_version=original, to_version=target,
                             problems=[f"vault is already {target}"])
    if original != PLACEMENT_ALGORITHM_VERSION and original not in _CHAINED_PREDECESSORS:
        return UpgradeResult(
            upgraded=False, from_version=original, to_version=target,
            problems=[
                f"cannot upgrade from {original!r}; only {PLACEMENT_ALGORITHM_VERSION!r} (or "
                f"{DIAGNOSIS_SPLIT_ALGORITHM_VERSION!r} / {REVEAL_LEDGER_ALGORITHM_VERSION!r}, through it) "
                f"may activate {target}"
            ],
        )
    current = original
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
    from learnloop.diagnosis.split.live import settings_from_config

    history_mode = settings_from_config(vault).history_mode
    guard = guard_status(repository, judge_model=expected_model, history_mode=history_mode)
    if not guard["switch_ready"]:
        problems = []
        if guard["diagnoser_false_merges"]:
            problems.append(
                f"the M1 diagnoser's validated citations linked {len(guard['diagnoser_false_merges'])} planted "
                "same-answer/different-cause B answer(s) to their A answer: citations merge groups at the judge's "
                "authority, so this is a false merge on the citation path; fix the diagnoser and rerun M1, then "
                "`learnloop recurrence guard --from-run <run>`"
            )
        if guard["passed"] and not guard["diagnoser"]["m1_cases_checked"]:
            problems.append(
                "no M1 review run's planted same-answer/different-cause case has been checked for the citation "
                f"path under the current diagnosis prompt in history mode {history_mode!r} (S1.0's planted pairs "
                "are the standing suite, §3.6): run `learnloop recurrence guard --from-run <M1 run dir>` "
                "(`--dry-run` first)"
            )
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
        if original != PLACEMENT_ALGORITHM_VERSION:
            problems.append(
                f"the vault stays at {original}; `learnloop upgrade --to {PLACEMENT_ALGORITHM_VERSION}` "
                "activates placement without recurrence groups"
            )
        return UpgradeResult(upgraded=False, from_version=original, to_version=target, problems=problems)
    if original != PLACEMENT_ALGORITHM_VERSION:
        # The guard passed: take the existing chain to the immediate
        # predecessor first (it freezes, rebuilds and renames per link).
        chained = upgrade_to_mvp011(root, clock=clock)
        if not chained.upgraded:
            return UpgradeResult(
                upgraded=False, from_version=original, to_version=target,
                problems=[f"{PLACEMENT_ALGORITHM_VERSION} step refused: {problem}" for problem in chained.problems],
            )
        vault = load_vault(root)
        current = vault.config.algorithms.algorithm_version
        repository = Repository(VaultPaths(vault.root, vault.config).sqlite_path)
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
    return UpgradeResult(upgraded=True, from_version=original, to_version=target)


__all__ = ["upgrade_to_mvp012"]

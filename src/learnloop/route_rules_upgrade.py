"""``learnloop upgrade --to mvp-0.18``: route rules in the grader.

route-check-in-grader (owner decision 2026-10-13) folded mvp-0.17's separate
proofs-and-explanations route check (an item reading, an independent
re-derivation call and a deterministic gate) into the blind grader's prompt.
``mvp-0.18`` is a PLACEHOLDER tag: the sources track takes ``mvp-0.18`` and
``mvp-0.19`` on main, so this successor is relabelled at its merge, as the
stuck prompt, DL1, R1, learner-text gaps and the route check were at theirs.
It is the next link of the linear chain (the split PLUS placement PLUS
recurrence groups PLUS the stuck prompt PLUS the plan PLUS probe ties PLUS the
sooner check PLUS this).

The upgrade:

* accepts the immediate predecessor (``mvp-0.17``), or ``mvp-0.9`` to
  ``mvp-0.16`` by running :func:`learnloop.proof_check_upgrade.upgrade_to_mvp017`
  first. Below ``mvp-0.12`` that chain runs T1's
  :func:`~learnloop.diagnosis.recurrence.upgrade.upgrade_to_mvp012`, whose
  same-answer/different-cause guard is advisory by default (owner batch 2: it
  reports its status as notes, which this upgrade passes on) and refuses only
  under ``recurrence.require_guard = true``; a refusal there refuses this
  upgrade too and leaves the vault at its original version. If the chained
  steps succeed and this step then fails, the vault is left at the valid
  ``mvp-0.17``. Anything older is refused;
* changes what NEW blind grades persist (the own-route rules in the prompt
  and its ``+own-route-v1`` identity, the rule's outcome on the blind record)
  and never the authority-propagation projection, so like every successor it
  is a tag change plus an idempotent rebuild of the same projection
  namespace, prepared before the atomic config rename.

Nothing is rewritten: grades recorded before the upgrade, mvp-0.17's
route-checked grades included, keep their meaning (replay reads every record
as written). Kill switch: ``proof_check.enabled = false`` grades new answers
as ``mvp-0.17`` now does (as ``mvp-0.16``) without a downgrade; rolling the
version back is restore-only.
"""

from __future__ import annotations

from pathlib import Path

from learnloop.algorithm_versions import (
    DAILY_PLAN_ALGORITHM_VERSION,
    DIAGNOSIS_SPLIT_ALGORITHM_VERSION,
    LEARNER_TEXT_GAP_ALGORITHM_VERSION,
    PLACEMENT_ALGORITHM_VERSION,
    PROBE_TIE_ALGORITHM_VERSION,
    PROOF_ROUTE_CHECK_ALGORITHM_VERSION,
    RECURRENCE_GROUP_ALGORITHM_VERSION,
    REVEAL_LEDGER_ALGORITHM_VERSION,
    ROUTE_RULES_ALGORITHM_VERSION,
    STUCK_PROMPT_ALGORITHM_VERSION,
)
from learnloop.clock import Clock
from learnloop.db.repositories import Repository
from learnloop.ops.vault_upgrade import UpgradeResult, rewrite_algorithm_version
from learnloop.params import parameter_registry as registry_service
from learnloop.proof_check_upgrade import upgrade_to_mvp017
from learnloop.substrate.p0_projection import activate_p0_projection
from learnloop.vault.loader import load_vault
from learnloop.vault.paths import VaultPaths

#: Versions the upgrade accepts through the existing chain (mvp-0.17's own
#: upgrade takes them to the immediate predecessor first).
_CHAINED_PREDECESSORS = (
    REVEAL_LEDGER_ALGORITHM_VERSION,
    DIAGNOSIS_SPLIT_ALGORITHM_VERSION,
    PLACEMENT_ALGORITHM_VERSION,
    RECURRENCE_GROUP_ALGORITHM_VERSION,
    STUCK_PROMPT_ALGORITHM_VERSION,
    DAILY_PLAN_ALGORITHM_VERSION,
    PROBE_TIE_ALGORITHM_VERSION,
    LEARNER_TEXT_GAP_ALGORITHM_VERSION,
)


def upgrade_to_mvp018(root: Path, *, clock: Clock | None = None) -> UpgradeResult:
    vault = load_vault(root)
    original = vault.config.algorithms.algorithm_version
    target = ROUTE_RULES_ALGORITHM_VERSION
    if original == target:
        return UpgradeResult(upgraded=False, from_version=original, to_version=target,
                             problems=[f"vault is already {target}"])
    if original != PROOF_ROUTE_CHECK_ALGORITHM_VERSION and original not in _CHAINED_PREDECESSORS:
        return UpgradeResult(
            upgraded=False, from_version=original, to_version=target,
            problems=[
                f"cannot upgrade from {original!r}; only {PROOF_ROUTE_CHECK_ALGORITHM_VERSION!r} (or "
                f"{LEARNER_TEXT_GAP_ALGORITHM_VERSION!r} / {PROBE_TIE_ALGORITHM_VERSION!r} / "
                f"{DAILY_PLAN_ALGORITHM_VERSION!r} / {STUCK_PROMPT_ALGORITHM_VERSION!r} / "
                f"{RECURRENCE_GROUP_ALGORITHM_VERSION!r} / {PLACEMENT_ALGORITHM_VERSION!r} / "
                f"{DIAGNOSIS_SPLIT_ALGORITHM_VERSION!r} / {REVEAL_LEDGER_ALGORITHM_VERSION!r}, "
                f"through it) may activate {target}"
            ],
        )
    chained_notes: list[str] = []
    if original != PROOF_ROUTE_CHECK_ALGORITHM_VERSION:
        # The chain's mvp-0.17 step (and, below mvp-0.12, T1's guarded
        # mvp-0.12 step first) refuses before it takes any step of its own; a
        # refusal there leaves the vault where it was.
        chained = upgrade_to_mvp017(root, clock=clock)
        # The chain's advisory guard status (owner batch 2) comes back as notes.
        chained_notes = list(chained.notes or [])
        if not chained.upgraded:
            prefixes = (
                f"{RECURRENCE_GROUP_ALGORITHM_VERSION} step refused: ",
                f"{STUCK_PROMPT_ALGORITHM_VERSION} step refused: ",
                f"{DAILY_PLAN_ALGORITHM_VERSION} step refused: ",
                f"{PROBE_TIE_ALGORITHM_VERSION} step refused: ",
                f"{LEARNER_TEXT_GAP_ALGORITHM_VERSION} step refused: ",
            )
            return UpgradeResult(
                upgraded=False, from_version=original, to_version=target,
                problems=[
                    problem if problem.startswith(prefixes)
                    else f"{PROOF_ROUTE_CHECK_ALGORITHM_VERSION} step refused: {problem}"
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


__all__ = ["upgrade_to_mvp018"]

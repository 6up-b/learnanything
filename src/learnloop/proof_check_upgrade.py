"""``learnloop upgrade --to mvp-0.17``: the valid-alternative gate for proofs.

The branch grading/proof-alternatives built this successor as ``mvp-0.15`` (a
placeholder tag) over ``mvp-0.14``; it merged after router R1's probe ties
(``mvp-0.15``) and learner-text gaps (``mvp-0.16``), so the route check is
``mvp-0.17``, the next link of the linear chain (the split PLUS placement PLUS
recurrence groups PLUS the stuck prompt PLUS the plan PLUS probe ties PLUS the
sooner check PLUS this), as the stuck prompt, DL1, R1 and learner-text gaps
were relabelled at theirs.

The upgrade:

* accepts the immediate predecessor (``mvp-0.16``), or ``mvp-0.9`` to
  ``mvp-0.15`` by running
  :func:`learnloop.learner_text_gap_upgrade.upgrade_to_mvp016` first. Below
  ``mvp-0.12`` that chain runs T1's
  :func:`~learnloop.diagnosis.recurrence.upgrade.upgrade_to_mvp012`, whose
  same-answer/different-cause guard is advisory by default (owner batch 2: it
  reports its status as notes, which this upgrade passes on) and refuses only
  under ``recurrence.require_guard = true``; a refusal there refuses this
  upgrade too and leaves the vault at its original version. If the chained
  steps succeed and this step then fails, the vault is left at the valid
  ``mvp-0.16``. Anything older is refused;
* changes what NEW blind grades persist on proof-like items (the blind
  record's ``grading_support.proof_route_check``, restored points, the
  route-check verdict in ``judgment_ledger`` and, migration 186, a
  clarification licensed by a dispute that turns on the learner's meaning)
  and never the authority-propagation projection, so like every successor it
  is a tag change plus an idempotent rebuild of the same projection namespace,
  prepared before the atomic config rename.

Nothing is rewritten: grades recorded before the upgrade keep their meaning
(replay reads every record as written). Kill switch: ``proof_check.enabled =
false`` grades new answers exactly as ``mvp-0.16`` without a downgrade;
rolling the version back is restore-only.

This module sits at the top level beside ``learner_text_gap_upgrade`` for the
same reason: it composes the chain's earlier links.
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
    STUCK_PROMPT_ALGORITHM_VERSION,
)
from learnloop.clock import Clock
from learnloop.db.repositories import Repository
from learnloop.learner_text_gap_upgrade import upgrade_to_mvp016
from learnloop.ops.vault_upgrade import UpgradeResult, rewrite_algorithm_version
from learnloop.params import parameter_registry as registry_service
from learnloop.substrate.p0_projection import activate_p0_projection
from learnloop.vault.loader import load_vault
from learnloop.vault.paths import VaultPaths

#: Versions the upgrade accepts through the existing chain (mvp-0.16's own
#: upgrade takes them to the immediate predecessor first).
_CHAINED_PREDECESSORS = (
    REVEAL_LEDGER_ALGORITHM_VERSION,
    DIAGNOSIS_SPLIT_ALGORITHM_VERSION,
    PLACEMENT_ALGORITHM_VERSION,
    RECURRENCE_GROUP_ALGORITHM_VERSION,
    STUCK_PROMPT_ALGORITHM_VERSION,
    DAILY_PLAN_ALGORITHM_VERSION,
    PROBE_TIE_ALGORITHM_VERSION,
)


def upgrade_to_mvp017(root: Path, *, clock: Clock | None = None) -> UpgradeResult:
    vault = load_vault(root)
    original = vault.config.algorithms.algorithm_version
    target = PROOF_ROUTE_CHECK_ALGORITHM_VERSION
    if original == target:
        return UpgradeResult(upgraded=False, from_version=original, to_version=target,
                             problems=[f"vault is already {target}"])
    if original != LEARNER_TEXT_GAP_ALGORITHM_VERSION and original not in _CHAINED_PREDECESSORS:
        return UpgradeResult(
            upgraded=False, from_version=original, to_version=target,
            problems=[
                f"cannot upgrade from {original!r}; only {LEARNER_TEXT_GAP_ALGORITHM_VERSION!r} (or "
                f"{PROBE_TIE_ALGORITHM_VERSION!r} / {DAILY_PLAN_ALGORITHM_VERSION!r} / "
                f"{STUCK_PROMPT_ALGORITHM_VERSION!r} / {RECURRENCE_GROUP_ALGORITHM_VERSION!r} / "
                f"{PLACEMENT_ALGORITHM_VERSION!r} / {DIAGNOSIS_SPLIT_ALGORITHM_VERSION!r} / "
                f"{REVEAL_LEDGER_ALGORITHM_VERSION!r}, through it) may activate {target}"
            ],
        )
    chained_notes: list[str] = []
    if original != LEARNER_TEXT_GAP_ALGORITHM_VERSION:
        # The chain's mvp-0.16 step (and, below mvp-0.12, T1's guarded
        # mvp-0.12 step first) refuses before it takes any step of its own; a
        # refusal there leaves the vault where it was.
        chained = upgrade_to_mvp016(root, clock=clock)
        # The chain's advisory guard status (owner batch 2) comes back as notes.
        chained_notes = list(chained.notes or [])
        if not chained.upgraded:
            prefixes = (
                f"{RECURRENCE_GROUP_ALGORITHM_VERSION} step refused: ",
                f"{STUCK_PROMPT_ALGORITHM_VERSION} step refused: ",
                f"{DAILY_PLAN_ALGORITHM_VERSION} step refused: ",
                f"{PROBE_TIE_ALGORITHM_VERSION} step refused: ",
            )
            return UpgradeResult(
                upgraded=False, from_version=original, to_version=target,
                problems=[
                    problem if problem.startswith(prefixes)
                    else f"{LEARNER_TEXT_GAP_ALGORITHM_VERSION} step refused: {problem}"
                    for problem in chained.problems
                ],
            )
        vault = load_vault(root)
    current = vault.config.algorithms.algorithm_version

    sqlite_path = VaultPaths(vault.root, vault.config).sqlite_path
    # Construction applies migration 186 (the clarification trigger) before
    # anything can record a route-check question.
    repository = Repository(sqlite_path)
    registry_service.freeze_manifest(vault, repository, algorithm_version=current, clock=clock)
    vault.config.algorithms.algorithm_version = target
    activate_p0_projection(vault, repository, from_version=current, clock=clock)
    registry_service.refresh(vault, repository, clock=clock)
    rewrite_algorithm_version(root / "learnloop.toml", current, target)
    return UpgradeResult(upgraded=True, from_version=original, to_version=target, notes=chained_notes)


__all__ = ["upgrade_to_mvp017"]

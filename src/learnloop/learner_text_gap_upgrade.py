"""``learnloop upgrade --to mvp-0.16``: sooner checks from learner-text gaps.

Learner-text gaps (implementation_handoffs §4, owner-directed 2026-10-12) were
built as ``mvp-0.13`` over ``mvp-0.12``; they merged after the stuck prompt
(``mvp-0.13``), the daily plan (``mvp-0.14``) and router R1's probe ties
(``mvp-0.15``), so the sooner check is ``mvp-0.16``, the next link of the
linear chain (the split PLUS placement PLUS recurrence groups PLUS the stuck
prompt PLUS the plan PLUS probe ties PLUS this).

The upgrade:

* accepts the immediate predecessor (``mvp-0.15``), or ``mvp-0.9`` to
  ``mvp-0.14`` by running :func:`learnloop.probe_tie_upgrade.upgrade_to_mvp015`
  first. Below ``mvp-0.12`` that chain runs T1's
  :func:`~learnloop.diagnosis.recurrence.upgrade.upgrade_to_mvp012`, whose
  same-answer/different-cause guard is advisory by default (owner batch 2: it
  reports its status as notes, which this upgrade passes on) and refuses only
  under ``recurrence.require_guard = true``; a refusal there refuses this
  upgrade too and leaves the vault at its original version. If the chained
  steps succeed and this step then fails, the vault is left at the valid
  ``mvp-0.15``. Anything older is refused;
* changes what is SERVED and never the authority-propagation projection: a
  prerequisite gap named in the learner's own text and matched to an LO
  assumed known or in maintenance brings that LO's next check forward (no
  sooner than ``learner_text_gaps.sooner_check_delay_hours`` after the gap,
  never later than it was), and the gap's target is a weak interaction
  signal on that LO. So like every successor it is a tag change plus an
  idempotent rebuild of the same projection namespace, prepared before the
  atomic config rename.

Nothing is rewritten: below the version the pipeline writes no advance
(migration 182's ``learner_gap_check_advances``), so the upgrade itself serves
the same queue. Kill switch: ``learner_text_gaps.sooner_check_enabled = false``
restores mvp-0.15's serving exactly without a downgrade; rolling the version
back is restore-only. The rest of the pipeline (named gaps, matches, edges,
created prerequisites, holding-pen sightings) is a live change behind its own
switches at every version.

This module sits at the top level beside ``probe_tie_upgrade`` for the same
reason: it composes the chain's earlier links.
"""

from __future__ import annotations

from pathlib import Path

from learnloop.algorithm_versions import (
    DAILY_PLAN_ALGORITHM_VERSION,
    DIAGNOSIS_SPLIT_ALGORITHM_VERSION,
    LEARNER_TEXT_GAP_ALGORITHM_VERSION,
    PLACEMENT_ALGORITHM_VERSION,
    PROBE_TIE_ALGORITHM_VERSION,
    RECURRENCE_GROUP_ALGORITHM_VERSION,
    REVEAL_LEDGER_ALGORITHM_VERSION,
    STUCK_PROMPT_ALGORITHM_VERSION,
)
from learnloop.clock import Clock
from learnloop.vault.repository import open_vault_repository
from learnloop.ops.vault_upgrade import UpgradeResult, rewrite_algorithm_version
from learnloop.params import parameter_registry as registry_service
from learnloop.probe_tie_upgrade import upgrade_to_mvp015
from learnloop.substrate.p0_projection import activate_p0_projection
from learnloop.vault.loader import load_vault
from learnloop.vault.paths import VaultPaths

#: Versions the upgrade accepts through the existing chain (mvp-0.15's own
#: upgrade takes them to the immediate predecessor first).
_CHAINED_PREDECESSORS = (
    REVEAL_LEDGER_ALGORITHM_VERSION,
    DIAGNOSIS_SPLIT_ALGORITHM_VERSION,
    PLACEMENT_ALGORITHM_VERSION,
    RECURRENCE_GROUP_ALGORITHM_VERSION,
    STUCK_PROMPT_ALGORITHM_VERSION,
    DAILY_PLAN_ALGORITHM_VERSION,
)


def upgrade_to_mvp016(root: Path, *, clock: Clock | None = None) -> UpgradeResult:
    vault = load_vault(root)
    original = vault.config.algorithms.algorithm_version
    target = LEARNER_TEXT_GAP_ALGORITHM_VERSION
    if original == target:
        return UpgradeResult(upgraded=False, from_version=original, to_version=target,
                             problems=[f"vault is already {target}"])
    if original != PROBE_TIE_ALGORITHM_VERSION and original not in _CHAINED_PREDECESSORS:
        return UpgradeResult(
            upgraded=False, from_version=original, to_version=target,
            problems=[
                f"cannot upgrade from {original!r}; only {PROBE_TIE_ALGORITHM_VERSION!r} (or "
                f"{DAILY_PLAN_ALGORITHM_VERSION!r} / {STUCK_PROMPT_ALGORITHM_VERSION!r} / "
                f"{RECURRENCE_GROUP_ALGORITHM_VERSION!r} / {PLACEMENT_ALGORITHM_VERSION!r} / "
                f"{DIAGNOSIS_SPLIT_ALGORITHM_VERSION!r} / {REVEAL_LEDGER_ALGORITHM_VERSION!r}, through it) "
                f"may activate {target}"
            ],
        )
    chained_notes: list[str] = []
    if original != PROBE_TIE_ALGORITHM_VERSION:
        # The chain's mvp-0.15 step (and, below mvp-0.12, T1's guarded mvp-0.12
        # step first) refuses before it takes any step of its own; a refusal
        # there leaves the vault where it was.
        chained = upgrade_to_mvp015(root, clock=clock)
        # The chain's advisory guard status (owner batch 2) comes back as notes.
        chained_notes = list(chained.notes or [])
        if not chained.upgraded:
            return UpgradeResult(
                upgraded=False, from_version=original, to_version=target,
                problems=[
                    problem
                    if problem.startswith(
                        (f"{RECURRENCE_GROUP_ALGORITHM_VERSION} step refused: ",
                         f"{STUCK_PROMPT_ALGORITHM_VERSION} step refused: ",
                         f"{DAILY_PLAN_ALGORITHM_VERSION} step refused: ")
                    )
                    else f"{PROBE_TIE_ALGORITHM_VERSION} step refused: {problem}"
                    for problem in chained.problems
                ],
            )
        vault = load_vault(root)
    current = vault.config.algorithms.algorithm_version

    sqlite_path = VaultPaths(vault.root, vault.config).sqlite_path
    # Opening the vault (through its coordinator) applies the additive migration the pipeline needs (182's
    # learner-text gap tables) before anything reads them.
    repository = open_vault_repository(vault.root, sqlite_path)
    registry_service.freeze_manifest(vault, repository, algorithm_version=current, clock=clock)
    vault.config.algorithms.algorithm_version = target
    activate_p0_projection(vault, repository, from_version=current, clock=clock)
    registry_service.refresh(vault, repository, clock=clock)
    rewrite_algorithm_version(root / "learnloop.toml", current, target)
    return UpgradeResult(upgraded=True, from_version=original, to_version=target, notes=chained_notes)


__all__ = ["upgrade_to_mvp016"]

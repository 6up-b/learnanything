"""``learnloop upgrade --to mvp-0.21``: value-of-information stopping.

Owner-directed 2026-10-12/13. The branch built it on mvp-0.16 as ``mvp-0.17``
(a placeholder tag) and it was relabelled ``mvp-0.21`` when it merged after
the route check (``mvp-0.17``), the sources track (``mvp-0.18``, the
answer-key gate, and ``mvp-0.19``, source-first needs) and the route rules in
the grader (``mvp-0.20``), as every earlier successor was at its merge. It is
the next link of the linear chain: the split PLUS placement PLUS recurrence
groups PLUS the stuck prompt PLUS the plan PLUS probe ties PLUS the sooner
check PLUS the answer-key gate PLUS source-first needs PLUS the route rules
PLUS this.

The upgrade:

* accepts the immediate predecessor (``mvp-0.20``), or ``mvp-0.9`` to
  ``mvp-0.19`` by running
  :func:`learnloop.route_rules_upgrade.upgrade_to_mvp020` first. Below
  ``mvp-0.12`` that chain runs T1's guarded ``mvp-0.12`` step, whose
  same-answer/different-cause guard is advisory by default (owner batch 2: it
  reports its status as notes, which this upgrade passes on) and refuses only
  under ``recurrence.require_guard = true``; a refusal there refuses this
  upgrade too and leaves the vault at its original version. If the chained
  steps succeed and this step then fails, the vault is left at the valid
  ``mvp-0.20``. Anything older is refused;
* changes what is SERVED and never the authority-propagation projection.
  Part 1 (kill switch ``voi_stopping.enabled``, a sub-switch per site) lifts
  four count caps onto value of information
  (:mod:`learnloop.diagnosis.voi_stopping`); Part 2 (kill switch
  ``diagnosis.probe_lane_reads_diagnosis``) makes the probe hypothesis lane
  read the diagnoser's verdict through the diagnosis overlay. So like every
  successor it is a tag change plus an idempotent rebuild of the same
  projection namespace, prepared before the atomic config rename.

Nothing is rewritten: migration 200 (applied by any repository open, at
every version) rebuilds ``probe_episodes`` data-preservingly so it can record
the new ``value_of_information_stop`` completion and its decision
(``completion_detail_json``), and migration 201 adds the
``followup_value_decisions`` receipt; only this version writes either, and no
persisted row changes meaning. Both switches off restore mvp-0.20's serving
exactly without a downgrade; rolling the version back is restore-only.

This module sits at the top level beside ``route_rules_upgrade`` for the same
reason: it composes the chain's earlier links.
"""

from __future__ import annotations

import re
from pathlib import Path

from learnloop.algorithm_versions import (
    ROUTE_RULES_ALGORITHM_VERSION,
    SUCCESSOR_CHAIN,
    VOI_STOPPING_ALGORITHM_VERSION,
)
from learnloop.clock import Clock
from learnloop.db.repositories import Repository
from learnloop.ops.vault_upgrade import UpgradeResult, rewrite_algorithm_version
from learnloop.params import parameter_registry as registry_service
from learnloop.route_rules_upgrade import upgrade_to_mvp020
from learnloop.substrate.p0_projection import activate_p0_projection
from learnloop.vault.loader import load_vault
from learnloop.vault.paths import VaultPaths

#: Versions the upgrade accepts through the existing chain (mvp-0.20's own
#: upgrade takes them to the immediate predecessor first): mvp-0.9 to mvp-0.19.
_CHAINED_PREDECESSORS = SUCCESSOR_CHAIN[:SUCCESSOR_CHAIN.index(ROUTE_RULES_ALGORITHM_VERSION)]

#: An earlier link's refusal already names its own step; it passes through
#: unprefixed (as ``route_rules_upgrade`` passes the chain's refusals on).
_STEP_REFUSAL = re.compile(r"^mvp-0\.\d+ step refused: ")


def upgrade_to_mvp021(root: Path, *, clock: Clock | None = None) -> UpgradeResult:
    """mvp-0.20 (or mvp-0.9 to mvp-0.19, through the chain) -> mvp-0.21."""

    vault = load_vault(root)
    original = vault.config.algorithms.algorithm_version
    target = VOI_STOPPING_ALGORITHM_VERSION
    predecessor = ROUTE_RULES_ALGORITHM_VERSION
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
        # The chain's mvp-0.20 step (and, below mvp-0.12, T1's guarded
        # mvp-0.12 step first) refuses before it takes any step of its own; a
        # refusal there leaves the vault where it was.
        chained = upgrade_to_mvp020(root, clock=clock)
        # The chain's advisory guard status (owner batch 2) comes back as notes.
        chained_notes = list(chained.notes or [])
        if not chained.upgraded:
            return UpgradeResult(
                upgraded=False, from_version=original, to_version=target,
                problems=[
                    problem if _STEP_REFUSAL.match(problem) else f"{predecessor} step refused: {problem}"
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


__all__ = ["upgrade_to_mvp021"]

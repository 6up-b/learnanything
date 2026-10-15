"""``learnloop upgrade --to mvp-0.22``: Tier 1, the Decider migration.

Owner decision 2026-10-13. The branch decider/tier1-migration built it on
mvp-0.19 as ``mvp-0.20`` (a placeholder tag, its upgrade in
``sources_upgrade``) and it was relabelled ``mvp-0.22`` when it merged after
the route rules in the grader (``mvp-0.20``) and value-of-information
stopping (``mvp-0.21``), as every earlier successor was at its merge. It is
the next link of the linear chain: everything ``mvp-0.21`` means PLUS the
Decider deciding the small judgments ``[decider_routes]`` names
(:mod:`learnloop.decider_judgments`).

The upgrade:

* accepts the immediate predecessor (``mvp-0.21``), or ``mvp-0.9`` to
  ``mvp-0.20`` by running
  :func:`learnloop.voi_stopping_upgrade.upgrade_to_mvp021` first. Below
  ``mvp-0.12`` that chain runs T1's guarded ``mvp-0.12`` step, whose
  same-answer/different-cause guard is advisory by default (owner batch 2: it
  reports its status as notes, which this upgrade passes on, through a
  refusal too) and refuses only under ``recurrence.require_guard = true``; a
  refusal there refuses this upgrade too and leaves the vault at its original
  version. If the chained steps succeed and this step then fails, the vault
  is left at the valid ``mvp-0.21``. Anything older is refused;
* changes what is SERVED from now on (gaps created, misconceptions matched,
  links, classifications, contamination verdicts), each judgment behind its
  own ``[decider_routes]`` kill switch, and never the authority-propagation
  projection. So like every successor it is a tag change plus an idempotent
  rebuild of the same projection namespace, prepared before the atomic config
  rename.

Nothing is migrated or rewritten: raw ledgers keep their rows and meaning.
Every switch off restores mvp-0.21's serving exactly without a downgrade;
rolling the version back is restore-only.

This module sits at the top level beside ``voi_stopping_upgrade`` for the
same reason: it composes the chain's earlier links.
"""

from __future__ import annotations

import re
from pathlib import Path

from learnloop.algorithm_versions import (
    DECIDER_TIER1_ALGORITHM_VERSION,
    SUCCESSOR_CHAIN,
    VOI_STOPPING_ALGORITHM_VERSION,
)
from learnloop.clock import Clock
from learnloop.vault.repository import open_vault_repository
from learnloop.ops.vault_upgrade import UpgradeResult, rewrite_algorithm_version
from learnloop.params import parameter_registry as registry_service
from learnloop.substrate.p0_projection import activate_p0_projection
from learnloop.vault.loader import load_vault
from learnloop.vault.paths import VaultPaths
from learnloop.voi_stopping_upgrade import upgrade_to_mvp021

#: Versions the upgrade accepts through the existing chain (mvp-0.21's own
#: upgrade takes them to the immediate predecessor first): mvp-0.9 to mvp-0.20.
_CHAINED_PREDECESSORS = SUCCESSOR_CHAIN[:SUCCESSOR_CHAIN.index(VOI_STOPPING_ALGORITHM_VERSION)]

#: An earlier link's refusal already names its own step; it passes through
#: unprefixed (as ``voi_stopping_upgrade`` passes the chain's refusals on).
_STEP_REFUSAL = re.compile(r"^mvp-0\.\d+ step refused: ")


def upgrade_to_mvp022(root: Path, *, clock: Clock | None = None) -> UpgradeResult:
    """mvp-0.21 (or mvp-0.9 to mvp-0.20, through the chain) -> mvp-0.22: Tier 1, the Decider's judgments."""

    vault = load_vault(root)
    original = vault.config.algorithms.algorithm_version
    target = DECIDER_TIER1_ALGORITHM_VERSION
    predecessor = VOI_STOPPING_ALGORITHM_VERSION
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
        # The chain's mvp-0.21 step (and, below mvp-0.12, T1's guarded
        # mvp-0.12 step first) refuses before it takes any step of its own; a
        # refusal there leaves the vault where it was.
        chained = upgrade_to_mvp021(root, clock=clock)
        # The chain's advisory guard status (owner batch 2) comes back as
        # notes, passed on through a refusal too.
        chained_notes = list(chained.notes or [])
        if not chained.upgraded:
            return UpgradeResult(
                upgraded=False, from_version=original, to_version=target, notes=chained_notes,
                problems=[
                    problem if _STEP_REFUSAL.match(problem) else f"{predecessor} step refused: {problem}"
                    for problem in chained.problems
                ],
            )
        vault = load_vault(root)
    current = vault.config.algorithms.algorithm_version

    sqlite_path = VaultPaths(vault.root, vault.config).sqlite_path
    repository = open_vault_repository(vault.root, sqlite_path)
    registry_service.freeze_manifest(vault, repository, algorithm_version=current, clock=clock)
    vault.config.algorithms.algorithm_version = target
    activate_p0_projection(vault, repository, from_version=current, clock=clock)
    registry_service.refresh(vault, repository, clock=clock)
    rewrite_algorithm_version(root / "learnloop.toml", current, target)
    return UpgradeResult(upgraded=True, from_version=original, to_version=target, notes=chained_notes)


__all__ = ["upgrade_to_mvp022"]

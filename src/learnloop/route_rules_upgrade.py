"""``learnloop upgrade --to mvp-0.20``: route rules in the grader.

route-check-in-grader (owner decision 2026-10-13) folded mvp-0.17's separate
proofs-and-explanations route check (an item reading, an independent
re-derivation call and a deterministic gate) into the blind grader's prompt.
The branch built it as ``mvp-0.18`` (a placeholder tag) and it was relabelled
``mvp-0.20`` when it merged after the sources track (``mvp-0.18``, the
answer-key gate, and ``mvp-0.19``, source-first needs), as the stuck prompt,
DL1, R1, learner-text gaps, the route check and the sources successors were
at theirs. It is the next link of the linear chain (the split PLUS placement
PLUS recurrence groups PLUS the stuck prompt PLUS the plan PLUS probe ties
PLUS the sooner check PLUS the answer-key gate PLUS source-first needs PLUS
this).

The upgrade:

* accepts the immediate predecessor (``mvp-0.19``), or ``mvp-0.9`` to
  ``mvp-0.18`` by running :func:`learnloop.sources_upgrade.upgrade_to_mvp019`
  first. Below ``mvp-0.12`` that chain runs T1's
  :func:`~learnloop.diagnosis.recurrence.upgrade.upgrade_to_mvp012`, whose
  same-answer/different-cause guard is advisory by default (owner batch 2: it
  reports its status as notes, which this upgrade passes on) and refuses only
  under ``recurrence.require_guard = true``; a refusal there refuses this
  upgrade too and leaves the vault at its original version. If the chained
  steps succeed and this step then fails, the vault is left at the valid
  ``mvp-0.19``. Anything older is refused;
* changes what NEW blind grades persist (the own-route rules in the prompt
  and its ``+own-route-v1`` identity, the rule's outcome on the blind record)
  and never the authority-propagation projection, so like every successor it
  is a tag change plus an idempotent rebuild of the same projection
  namespace, prepared before the atomic config rename.

Nothing is rewritten: grades recorded before the upgrade, mvp-0.17's
route-checked grades included, keep their meaning (replay reads every record
as written). Kill switch: ``proof_check.enabled = false`` grades new answers
as ``mvp-0.19`` now does (whose grading is ``mvp-0.16``'s) without a
downgrade; rolling the version back is restore-only.
"""

from __future__ import annotations

import re
from pathlib import Path

from learnloop.algorithm_versions import (
    ROUTE_RULES_ALGORITHM_VERSION,
    SOURCE_FIRST_NEEDS_ALGORITHM_VERSION,
    SUCCESSOR_CHAIN,
)
from learnloop.clock import Clock
from learnloop.db.repositories import Repository
from learnloop.ops.vault_upgrade import UpgradeResult, rewrite_algorithm_version
from learnloop.params import parameter_registry as registry_service
from learnloop.sources_upgrade import upgrade_to_mvp019
from learnloop.substrate.p0_projection import activate_p0_projection
from learnloop.vault.loader import load_vault
from learnloop.vault.paths import VaultPaths

#: Versions the upgrade accepts through the existing chain (mvp-0.19's own
#: upgrade takes them to the immediate predecessor first): mvp-0.9 to mvp-0.18.
_CHAINED_PREDECESSORS = SUCCESSOR_CHAIN[:SUCCESSOR_CHAIN.index(SOURCE_FIRST_NEEDS_ALGORITHM_VERSION)]

#: An earlier link's refusal already names its own step; it passes through
#: unprefixed (as ``sources_upgrade`` passes the chain's refusals on).
_STEP_REFUSAL = re.compile(r"^mvp-0\.\d+ step refused: ")


def upgrade_to_mvp020(root: Path, *, clock: Clock | None = None) -> UpgradeResult:
    """mvp-0.19 (or mvp-0.9 to mvp-0.18, through the chain) -> mvp-0.20."""

    vault = load_vault(root)
    original = vault.config.algorithms.algorithm_version
    target = ROUTE_RULES_ALGORITHM_VERSION
    predecessor = SOURCE_FIRST_NEEDS_ALGORITHM_VERSION
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
        # The chain's mvp-0.19 step (and, below mvp-0.12, T1's guarded
        # mvp-0.12 step first) refuses before it takes any step of its own; a
        # refusal there leaves the vault where it was.
        chained = upgrade_to_mvp019(root, clock=clock)
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


__all__ = ["upgrade_to_mvp020"]

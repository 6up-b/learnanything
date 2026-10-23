"""``learnloop upgrade --to mvp-0.30``: adaptive difficulty AD2+AD3 (one successor).

Spec ``docs/specs/spec_adaptive_difficulty_v1.md`` §14 AD2/AD3 and §11.1;
``docs/reviews/adaptive-difficulty-ad23.md``. The next link of the linear chain:
everything ``mvp-0.29`` (daily-loop DL2, intent) means PLUS this. DL2 landed on
main first, so ``mvp-0.28`` is never used (orchestrator decision 2026-10-20):

* a planned new-material slot is served by AD's draw over its support
  (practice in the 70-80% band, calibration within acceptable difficulty,
  exact logged propensities); a slot with an empty support is displaced and
  its item deferred until its blocking condition clears; a commission names a
  feature point (``selection``);
* generation writes AT a commissioned feature point, with no difficulty band
  (``generation_contract``);
* live decisions and the readiness numbers read the subject view
  (``promoted_predictor``), with the learned relatedness
  (``learned_coupling``), reading (``reading_opportunities``) and the
  self-check verdict term (``reading_self_check``).

The upgrade:

* accepts the immediate predecessor (``mvp-0.29``), or ``mvp-0.9`` to
  ``mvp-0.27`` by running :func:`learnloop.intent_upgrade.upgrade_to_mvp029`
  first (with its own activation and chain; refusals pass through). If the
  chained steps succeed and this step then fails, the vault is left at the valid
  ``mvp-0.29``. Anything older is refused;
* changes what is SERVED and the derived AD state, never the
  authority-propagation projection, evidence, mastery, FSRS or certification
  (A2, A11, A12): a tag change plus an idempotent rebuild of the same
  projection namespace and AD's own DERIVED state, prepared before the atomic
  config rename.

The relatedness proposal's first coupling version is adopted by the owner's
backfill (``learnloop ad relatedness``, dry-run first), never here. Each
switch false restores its part of ``mvp-0.29`` exactly; rolling the version
back is restore-only.
"""

from __future__ import annotations

import re
from pathlib import Path

from learnloop.algorithm_versions import (
    ADAPTIVE_DIFFICULTY_ALGORITHM_VERSION,
    INTENT_ALGORITHM_VERSION,
    SUCCESSOR_CHAIN,
)
from learnloop.clock import Clock
from learnloop.intent_upgrade import upgrade_to_mvp029
from learnloop.ops.vault_upgrade import UpgradeResult, rewrite_algorithm_version
from learnloop.params import parameter_registry as registry_service
from learnloop.substrate.p0_projection import activate_p0_projection
from learnloop.vault.loader import load_vault
from learnloop.vault.paths import VaultPaths
from learnloop.vault.repository import open_vault_repository

#: The immediate predecessor (daily-loop DL2's intent tag).
PREDECESSOR = INTENT_ALGORITHM_VERSION
#: Versions the upgrade accepts through the existing chain: mvp-0.9 to mvp-0.27.
_CHAINED_PREDECESSORS = SUCCESSOR_CHAIN[:SUCCESSOR_CHAIN.index(PREDECESSOR)]

#: An earlier link's refusal already names its own step; it passes through unprefixed.
_STEP_REFUSAL = re.compile(r"^mvp-0\.\d+ step refused: ")


def upgrade_to_mvp030(root: Path, *, clock: Clock | None = None) -> UpgradeResult:
    """mvp-0.29 (or mvp-0.9 to mvp-0.27, through the chain) -> mvp-0.30: adaptive difficulty AD2+AD3."""

    vault = load_vault(root)
    original = vault.config.algorithms.algorithm_version
    target = ADAPTIVE_DIFFICULTY_ALGORITHM_VERSION
    predecessor = PREDECESSOR
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
        chained = upgrade_to_mvp029(root, clock=clock)
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
    # AD's own DERIVED state, prepared before the rename (zero model calls).
    from learnloop.adaptive_difficulty.replay import rebuild as rebuild_ad_state
    from learnloop.adaptive_difficulty.scoring import rebuild as rebuild_ad_scores

    rebuild_ad_state(vault, repository)
    rebuild_ad_scores(vault, repository)
    registry_service.refresh(vault, repository, clock=clock)
    rewrite_algorithm_version(root / "learnloop.toml", current, target)
    return UpgradeResult(upgraded=True, from_version=original, to_version=target, notes=chained_notes)


#: The successor's descriptive name for the same upgrade.
upgrade_to_adaptive_difficulty = upgrade_to_mvp030

__all__ = ["PREDECESSOR", "upgrade_to_adaptive_difficulty", "upgrade_to_mvp030"]

"""``learnloop upgrade --to mvp-0.24``: router R2b + R2c, the model mixture on Today.

docs/specs/plan_router_r2_v1.md §8.1 (successor B), owner decisions 2026-10-13
(Q3: R2b and R2c share one new successor; built as a placeholder label,
relabelled at its merge). It is the next link of the linear chain: everything
``mvp-0.23`` means PLUS Today's blocks drawn from the logged model mixture
(the staged rule, the Decider and the router LLM, exact propensities) and
mid-block follow-ups decided by the restraint (``plan_interrupt``).

The upgrade:

* accepts the immediate predecessor (``mvp-0.23``), or ``mvp-0.9`` to
  ``mvp-0.22`` by running :func:`learnloop.router_staged_upgrade.upgrade_to_mvp023`
  first. Below ``mvp-0.12`` that chain runs T1's guarded ``mvp-0.12`` step,
  whose same-answer/different-cause guard is advisory by default (owner
  batch 2: it reports its status as notes, which this upgrade passes on,
  through a refusal too) and refuses only under ``recurrence.require_guard =
  true``; a refusal there refuses this upgrade too and leaves the vault at its
  original version. If the chained steps succeed and this step then fails,
  the vault is left at the valid ``mvp-0.23``. Anything older is refused;
* changes what is SERVED from now on (which block is served next, and when a
  follow-up joins), behind ``router.mode`` and ``router.restraint``, and never
  the authority-propagation projection. So like every successor it is a tag
  change plus an idempotent rebuild of the same projection namespace,
  prepared before the atomic config rename.

Nothing is migrated or rewritten: raw ledgers keep their rows and meaning.
``router.mode = "staged"`` restores mvp-0.23's serving exactly without a
downgrade; rolling the version back is restore-only.
"""

from __future__ import annotations

import re
from pathlib import Path

from learnloop.algorithm_versions import (
    ROUTER_MIXTURE_ALGORITHM_VERSION,
    ROUTER_STAGED_FRAME_ALGORITHM_VERSION,
    SUCCESSOR_CHAIN,
)
from learnloop.clock import Clock
from learnloop.db.repositories import Repository
from learnloop.ops.vault_upgrade import UpgradeResult, rewrite_algorithm_version
from learnloop.params import parameter_registry as registry_service
from learnloop.router_staged_upgrade import upgrade_to_mvp023
from learnloop.substrate.p0_projection import activate_p0_projection
from learnloop.vault.loader import load_vault
from learnloop.vault.paths import VaultPaths

#: Versions the upgrade accepts through the existing chain (mvp-0.23's own
#: upgrade takes them to the immediate predecessor first): mvp-0.9 to mvp-0.22.
_CHAINED_PREDECESSORS = SUCCESSOR_CHAIN[:SUCCESSOR_CHAIN.index(ROUTER_STAGED_FRAME_ALGORITHM_VERSION)]

#: An earlier link's refusal already names its own step; it passes through unprefixed.
_STEP_REFUSAL = re.compile(r"^mvp-0\.\d+ step refused: ")


def upgrade_to_mvp024(root: Path, *, clock: Clock | None = None) -> UpgradeResult:
    """mvp-0.23 (or mvp-0.9 to mvp-0.22, through the chain) -> mvp-0.24: router R2b + R2c."""

    vault = load_vault(root)
    original = vault.config.algorithms.algorithm_version
    target = ROUTER_MIXTURE_ALGORITHM_VERSION
    predecessor = ROUTER_STAGED_FRAME_ALGORITHM_VERSION
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
        chained = upgrade_to_mvp023(root, clock=clock)
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
    repository = Repository(sqlite_path)
    registry_service.freeze_manifest(vault, repository, algorithm_version=current, clock=clock)
    vault.config.algorithms.algorithm_version = target
    activate_p0_projection(vault, repository, from_version=current, clock=clock)
    registry_service.refresh(vault, repository, clock=clock)
    rewrite_algorithm_version(root / "learnloop.toml", current, target)
    return UpgradeResult(upgraded=True, from_version=original, to_version=target, notes=chained_notes)


__all__ = ["upgrade_to_mvp024"]

"""``learnloop upgrade --to mvp-0.25``: method-explicit items.

Owner rule 2026-10-13: rubric criteria name the fact a step establishes, not
the method used; an item whose target IS a method states it ("Use {method} in
your answer.", rendered from the field) and records it as
``PracticeItem.required_method``. The grading side ships as this successor:
the own-route rules gain the required method (``own-route-v2``), so a
criterion tied to the item's required method is graded on use of that method
and another route fails it without a quoted wrong step. It is the next link of
the linear chain: everything ``mvp-0.24`` means PLUS this.

The branch built it as ``mvp-0.22-placeholder`` (a placeholder tag, no
migration) and it was relabelled ``mvp-0.25`` at its merge after VOI v2
(``mvp-0.21``), the Decider migration (``mvp-0.22``) and router R2a / R2b + R2c
(``mvp-0.23``, ``mvp-0.24``).

The upgrade:

* accepts the immediate predecessor (``mvp-0.24``), or ``mvp-0.9`` to
  ``mvp-0.23`` by running :func:`learnloop.router_mixture_upgrade.upgrade_to_mvp024`
  first. Below ``mvp-0.12`` that chain runs T1's guarded step, whose
  same-answer/different-cause guard is advisory by default (its status comes
  back as notes, which this upgrade passes on, through a refusal too:
  ``chained_notes = list(chained.notes or [])``) and refuses only under
  ``recurrence.require_guard = true``; a refusal there refuses this upgrade
  too and leaves the vault at its original version. If the chained steps
  succeed and this step then fails, the vault is left at the valid
  ``mvp-0.24``. Anything older is refused;
* changes what NEW blind grades persist (the ``own-route-v2`` prompt and
  identity, a required-method item's method criteria on the blind record) and
  never the authority-propagation projection, so like every successor it is a
  tag change plus an idempotent rebuild of the same projection namespace,
  prepared before the atomic config rename.

Nothing is rewritten: grades recorded before the upgrade keep their meaning
(replay reads every record as written), and no item is edited (method-phrased
criteria are flagged and repaired only through proposals the owner confirms).
Kill switch: ``required_method.enabled = false`` grades new answers exactly as
``mvp-0.24`` without a downgrade; rolling the version back is restore-only.
"""

from __future__ import annotations

import re
from pathlib import Path

from learnloop.algorithm_versions import (
    METHOD_EXPLICIT_ALGORITHM_VERSION,
    ROUTER_MIXTURE_ALGORITHM_VERSION,
    SUCCESSOR_CHAIN,
)
from learnloop.clock import Clock
from learnloop.db.repositories import Repository
from learnloop.ops.vault_upgrade import UpgradeResult, rewrite_algorithm_version
from learnloop.params import parameter_registry as registry_service
from learnloop.router_mixture_upgrade import upgrade_to_mvp024
from learnloop.substrate.p0_projection import activate_p0_projection
from learnloop.vault.loader import load_vault
from learnloop.vault.paths import VaultPaths

#: Versions the upgrade accepts through the existing chain (mvp-0.24's own
#: upgrade takes them to the immediate predecessor first): mvp-0.9 to mvp-0.23.
_CHAINED_PREDECESSORS = SUCCESSOR_CHAIN[:SUCCESSOR_CHAIN.index(ROUTER_MIXTURE_ALGORITHM_VERSION)]

#: An earlier link's refusal already names its own step; it passes through
#: unprefixed (as ``router_mixture_upgrade`` passes the chain's refusals on).
_STEP_REFUSAL = re.compile(r"^mvp-0\.\d+ step refused: ")


def upgrade_to_mvp025(root: Path, *, clock: Clock | None = None) -> UpgradeResult:
    """mvp-0.24 (or mvp-0.9 to mvp-0.23, through the chain) -> mvp-0.25: method-explicit items."""

    vault = load_vault(root)
    original = vault.config.algorithms.algorithm_version
    target = METHOD_EXPLICIT_ALGORITHM_VERSION
    predecessor = ROUTER_MIXTURE_ALGORITHM_VERSION
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
        # The chain's mvp-0.24 step (and, below mvp-0.12, T1's guarded
        # mvp-0.12 step first) refuses before it takes any step of its own; a
        # refusal there leaves the vault where it was.
        chained = upgrade_to_mvp024(root, clock=clock)
        # The chain's advisory guard status (owner batch 2) comes back as notes.
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


#: The branch's name for the same upgrade (kept so its callers need no change).
upgrade_to_method_explicit = upgrade_to_mvp025

__all__ = ["upgrade_to_method_explicit", "upgrade_to_mvp025"]

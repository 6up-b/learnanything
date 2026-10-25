"""``learnloop upgrade --to <READING_PATH_PLAN_ALGORITHM_VERSION>``: RW7b.

Reader workbench RW7b (spec_reader_workbench_v1 §10.2, G47;
``docs/reviews/reader-workbench-RW7b.md``): the plan follows the reading path.
It is the next link of the linear chain: everything the predecessor means
PLUS this:

* DL1's reading block opens the next unfinished core or prerequisite section
  of the source's reading path (RW7a's judged labels at the learner's depth,
  honest labels re-applied when the plan is built, "read it anyway" as core,
  "skip it" left out) instead of the next section in the predecessor's order;
  enrichment, already shown and assumed sections are never planned, and a
  source with no path keeps the predecessor's order (F3: what is served
  changes, never evidence or the projection);
* every plan the successor builds records, in ``split_json["reading_path"]``,
  the section the predecessor's order would have chosen.

The tag is ONE constant (``READING_PATH_PLAN_ALGORITHM_VERSION``,
``mvp-0.32``) after RW2d's ``mvp-0.31``, so :data:`PREDECESSOR` is RW2d's
tag with RW2d's chained upgrade, and nothing else names a number; a landing
that finds another number free renumbers the constant and, if the
predecessor moved, these two names.

The upgrade:

* accepts the immediate predecessor, or ``mvp-0.9`` up to it by running the
  predecessor's own upgrade first (with its own activation and notes, a
  refusal's included). If the chained steps succeed and this step then fails,
  the vault is left at the valid predecessor. Anything older is refused;
* changes what is SERVED, never the authority-propagation projection, so like
  the serving successors before it it is a tag change plus an idempotent
  rebuild of the same projection namespace, prepared before the atomic config
  rename.

Nothing is rewritten: reading paths, depths and overrides recorded below the
tag are read by the plan from the tag on (the tables are append-only and
their meaning is unchanged). Kill switch: ``reading_paths.plan_uses_path =
false`` plans exactly as the predecessor without a downgrade; rolling the
version back is restore-only.
"""

from __future__ import annotations

import re
from pathlib import Path

from learnloop.algorithm_versions import (
    READING_PATH_PLAN_ALGORITHM_VERSION,
    SUCCESSOR_CHAIN,
    WORKBENCH_FIELD_SIGNALS_ALGORITHM_VERSION,
)
from learnloop.clock import Clock
from learnloop.ops.vault_upgrade import UpgradeResult, rewrite_algorithm_version
from learnloop.params import parameter_registry as registry_service
from learnloop.substrate.p0_projection import activate_p0_projection
from learnloop.vault.loader import load_vault
from learnloop.vault.paths import VaultPaths
from learnloop.vault.repository import open_vault_repository
from learnloop.workbench_field_signals_upgrade import upgrade_to_workbench_field_signals

#: The immediate predecessor and its upgrade.
PREDECESSOR = WORKBENCH_FIELD_SIGNALS_ALGORITHM_VERSION
_upgrade_to_predecessor = upgrade_to_workbench_field_signals

#: Versions the upgrade accepts through the existing chain: mvp-0.9 up to the predecessor's own predecessor.
_CHAINED_PREDECESSORS = SUCCESSOR_CHAIN[:SUCCESSOR_CHAIN.index(PREDECESSOR)]

#: An earlier link's refusal already names its own step; it passes through unprefixed.
_STEP_REFUSAL = re.compile(r"^mvp-0\.\d+ step refused: ")


def upgrade_to_reading_path_plan(root: Path, *, clock: Clock | None = None) -> UpgradeResult:
    """The predecessor (or mvp-0.9 onwards, through the chain) -> RW7b's tag: the plan follows the path."""

    vault = load_vault(root)
    original = vault.config.algorithms.algorithm_version
    target = READING_PATH_PLAN_ALGORITHM_VERSION
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
        # The chain's predecessor step (with its own activation) refuses
        # before it takes any step of its own; a refusal there leaves the
        # vault where it was.
        chained = _upgrade_to_predecessor(root, clock=clock)
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


__all__ = ["PREDECESSOR", "upgrade_to_reading_path_plan"]

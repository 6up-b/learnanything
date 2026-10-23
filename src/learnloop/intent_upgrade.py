"""``learnloop upgrade --to mvp-0.29``: the learner's intent (daily-loop DL2).

DL2 (``docs/reviews/daily-loop-dl2.md``) shipped as a live change behind
``intent.enabled``; its Codex re-review (F2) required a tag under the
2026-10-17 rule (``docs/algorithm-change-playbook.md``), because intent
changes which items are served as measurements: a paused item's pending cold
retry waits, and a "Check once" is a cold measurement of its own. It is the
next link of the linear chain: everything the predecessor means PLUS this:

* excluded items (Pause, Reference, Let go, an answered "Check once") are
  never served, requested or rebuilt as a follow-up; a "Check once" holds its
  items until its date, is served cold only when the one eligibility decision
  allows it, and is answered only by an attempt that decision would have
  served cold;
* effective dues at the recall targets, push, admission, re-entry and the
  Today plan's reading by intent; the desktop intent control and deadlines.

The predecessor is ``mvp-0.27`` (one constant, :data:`PREDECESSOR`, and its
chained upgrade). DL2 landed on main before adaptive difficulty AD2+AD3, so
``mvp-0.28`` is never used on main; AD2+AD3 lands as ``mvp-0.30`` with this
tag as its predecessor.

The upgrade:

* accepts the immediate predecessor, or ``mvp-0.9`` up to it by running the
  predecessor's own upgrade first (with its own activation and notes, a
  refusal's included). If the chained steps succeed and this step then fails,
  the vault is left at the valid predecessor. Anything older is refused;
* changes what is SERVED, never the authority-propagation projection, so like
  the serving successors before it it is a tag change plus an idempotent
  rebuild of the same projection namespace, prepared before the atomic config
  rename.

Nothing is rewritten: commitments recorded below the tag keep their rows and
are read as intent from the tag on. Kill switch: ``intent.enabled = false``
serves exactly as the predecessor without a downgrade; rolling the version
back is restore-only.
"""

from __future__ import annotations

import re
from pathlib import Path

from learnloop.algorithm_versions import (
    ELIGIBILITY_DECISION_ALGORITHM_VERSION,
    INTENT_ALGORITHM_VERSION,
    SUCCESSOR_CHAIN,
)
from learnloop.clock import Clock
from learnloop.eligibility_decision_upgrade import upgrade_to_mvp027
from learnloop.ops.vault_upgrade import UpgradeResult, rewrite_algorithm_version
from learnloop.params import parameter_registry as registry_service
from learnloop.substrate.p0_projection import activate_p0_projection
from learnloop.vault.loader import load_vault
from learnloop.vault.paths import VaultPaths
from learnloop.vault.repository import open_vault_repository

#: The immediate predecessor and its upgrade.
PREDECESSOR = ELIGIBILITY_DECISION_ALGORITHM_VERSION
_upgrade_to_predecessor = upgrade_to_mvp027

#: Versions the upgrade accepts through the existing chain: mvp-0.9 up to the predecessor's own predecessor.
_CHAINED_PREDECESSORS = SUCCESSOR_CHAIN[:SUCCESSOR_CHAIN.index(PREDECESSOR)]

#: An earlier link's refusal already names its own step; it passes through unprefixed.
_STEP_REFUSAL = re.compile(r"^mvp-0\.\d+ step refused: ")


def upgrade_to_mvp029(root: Path, *, clock: Clock | None = None) -> UpgradeResult:
    """The predecessor (or mvp-0.9 onwards, through the chain) -> mvp-0.29: the learner's intent."""

    vault = load_vault(root)
    original = vault.config.algorithms.algorithm_version
    target = INTENT_ALGORITHM_VERSION
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


#: The successor's descriptive name for the same upgrade.
upgrade_to_intent = upgrade_to_mvp029

__all__ = ["PREDECESSOR", "upgrade_to_intent", "upgrade_to_mvp029"]

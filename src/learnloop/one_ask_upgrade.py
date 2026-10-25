"""``learnloop upgrade --to <ONE_ASK_ALGORITHM_VERSION>``: Reader CA2, one Ask.

Reader CA2 (``docs/specs/ux_reader_compare_ask_v1.md`` §7.7, K10 and §15
Q3-Q4; ``docs/reviews/reader-ca2-one-ask.md``): one help rule on a check on
your own. It is the next link of the linear chain: everything the
predecessor means PLUS this:

* a question asked during a cold administration counts as help only when
  the tutor model's ``question_type`` is substantive
  (``tutor_qa.HINT_EQUIVALENT_TYPES``) on every cold path: the Reader's cold
  Ask (bound to a workbench item, or naming a client-reported cold attempt)
  no longer counts every question (the predecessor's L6 rule);
* help taken on a cold follow-up (``cold_retry``,
  ``certification_cold_probe``) makes the attempt practice with help: submit
  admits it instead of refusing it, it never answers the cold measurement,
  and the next serve withdraws the measurement as practised since scheduled;
  the practice view shows the help ladder's take step instead of "no hints on
  this one".

The tag is ONE constant (``ONE_ASK_ALGORITHM_VERSION``, ``mvp-0.34``) after
RW7b's ``mvp-0.32`` (the LP claim fixes hold ``mvp-0.33`` on their own
branch), so :data:`PREDECESSOR` is RW7b's tag with RW7b's chained upgrade,
and nothing else names a number; a landing that finds another number free,
or the predecessor moved, renumbers the constant and these two names.

The upgrade:

* accepts the immediate predecessor, or ``mvp-0.9`` up to it by running the
  predecessor's own upgrade first (with its own activation and notes, a
  refusal's included). If the chained steps succeed and this step then fails,
  the vault is left at the valid predecessor. Anything older is refused;
* changes how new attempts are classified and what submit admits, never the
  authority-propagation projection, so like the successors before it it is a
  tag change plus an idempotent rebuild of the same projection namespace,
  prepared before the atomic config rename.

Nothing is rewritten: attempts and question rows recorded below the tag keep
the flags they were written with (replay reads the stored ``hint_equivalent``
and ``hints_used``, never this rule). Kill switch: ``ask.cold_help_converts =
false`` restores both predecessor rules for new questions and submits
without a downgrade; rolling the version back is restore-only.
"""

from __future__ import annotations

import re
from pathlib import Path

from learnloop.algorithm_versions import (
    ONE_ASK_ALGORITHM_VERSION,
    READING_PATH_PLAN_ALGORITHM_VERSION,
    SUCCESSOR_CHAIN,
)
from learnloop.clock import Clock
from learnloop.ops.vault_upgrade import UpgradeResult, rewrite_algorithm_version
from learnloop.params import parameter_registry as registry_service
from learnloop.substrate.p0_projection import activate_p0_projection
from learnloop.vault.loader import load_vault
from learnloop.vault.paths import VaultPaths
from learnloop.vault.repository import open_vault_repository
from learnloop.reading_path_plan_upgrade import upgrade_to_reading_path_plan

#: The immediate predecessor and its upgrade.
PREDECESSOR = READING_PATH_PLAN_ALGORITHM_VERSION
_upgrade_to_predecessor = upgrade_to_reading_path_plan

#: Versions the upgrade accepts through the existing chain: mvp-0.9 up to the predecessor's own predecessor.
_CHAINED_PREDECESSORS = SUCCESSOR_CHAIN[:SUCCESSOR_CHAIN.index(PREDECESSOR)]

#: An earlier link's refusal already names its own step; it passes through unprefixed.
_STEP_REFUSAL = re.compile(r"^mvp-0\.\d+ step refused: ")


def upgrade_to_one_ask(root: Path, *, clock: Clock | None = None) -> UpgradeResult:
    """The predecessor (or mvp-0.9 onwards, through the chain) -> Reader CA2's tag: one help rule."""

    vault = load_vault(root)
    original = vault.config.algorithms.algorithm_version
    target = ONE_ASK_ALGORITHM_VERSION
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


__all__ = ["PREDECESSOR", "upgrade_to_one_ask"]

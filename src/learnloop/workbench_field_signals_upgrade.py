"""``learnloop upgrade --to <WORKBENCH_FIELD_SIGNALS_ALGORITHM_VERSION>``: RW2d.

Reader workbench RW2d (spec_reader_workbench_v1 §5.11, G41;
``docs/reviews/reader-workbench-RW2d.md``): workbench signals in the learner
field. It is the next link of the linear chain: everything the predecessor
means PLUS this:

* the field's interaction-signal derivation reads two more sources, a
  mid-work workbench stuck step with text and help asked for before the
  first step (``learnloop.field.workbench_signals``); both are zero-mass rows
  linked to no attempt, so the record never changes (F2);
* they keep their LO out of fast-track and teach it first, so Phase 6's
  fast-track, the quick check's split, the new-material order and the plans
  built on them change (F3); ``field_signal_receipts`` (migration 219) and the
  candidate component ``taught_first_predecessor`` record what the
  predecessor would have decided where it differs.

The tag is ONE constant (``WORKBENCH_FIELD_SIGNALS_ALGORITHM_VERSION``,
``mvp-0.31``). Built on main at ``mvp-0.29`` (DL2's intent) while adaptive
difficulty AD2+AD3 held ``mvp-0.30``; its landing chained it after AD2+AD3,
so :data:`PREDECESSOR` is ``mvp-0.30`` with AD2+AD3's chained upgrade, and
nothing else names a number.

The upgrade:

* accepts the immediate predecessor, or ``mvp-0.9`` up to it by running the
  predecessor's own upgrade first (with its own activation and notes, a
  refusal's included). If the chained steps succeed and this step then fails,
  the vault is left at the valid predecessor. Anything older is refused;
* changes what is SERVED, never the authority-propagation projection, so like
  the serving successors before it it is a tag change plus an idempotent
  rebuild of the same projection namespace, prepared before the atomic config
  rename.

Nothing is rewritten: workbench sessions, steps and help rows recorded below
the tag are read as signals from the tag on (the ledgers are append-only and
their meaning is unchanged). Kill switch: ``workbench.field_signals_enabled =
false`` derives, serves and plans exactly as the predecessor without a
downgrade; rolling the version back is restore-only.
"""

from __future__ import annotations

import re
from pathlib import Path

from learnloop.ad_successor_upgrade import upgrade_to_mvp030
from learnloop.algorithm_versions import (
    ADAPTIVE_DIFFICULTY_ALGORITHM_VERSION,
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

#: The immediate predecessor and its upgrade.
PREDECESSOR = ADAPTIVE_DIFFICULTY_ALGORITHM_VERSION
_upgrade_to_predecessor = upgrade_to_mvp030

#: Versions the upgrade accepts through the existing chain: mvp-0.9 up to the predecessor's own predecessor.
_CHAINED_PREDECESSORS = SUCCESSOR_CHAIN[:SUCCESSOR_CHAIN.index(PREDECESSOR)]

#: An earlier link's refusal already names its own step; it passes through unprefixed.
_STEP_REFUSAL = re.compile(r"^mvp-0\.\d+ step refused: ")


def upgrade_to_workbench_field_signals(root: Path, *, clock: Clock | None = None) -> UpgradeResult:
    """The predecessor (or mvp-0.9 onwards, through the chain) -> RW2d's tag: workbench field signals."""

    vault = load_vault(root)
    original = vault.config.algorithms.algorithm_version
    target = WORKBENCH_FIELD_SIGNALS_ALGORITHM_VERSION
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


__all__ = ["PREDECESSOR", "upgrade_to_workbench_field_signals"]

"""``learnloop upgrade --to <CLAIM_FIXES_ALGORITHM_VERSION>``: LP-min (a).

Learned parameters LP-min (a) (spec_learned_parameters_v1 §3.0b item 1;
``docs/reviews/lp-min-claim-fixes.md``): the four claim-defect fixes. It is
the next link of the linear chain: everything the predecessor means PLUS
this:

* a tutor gap declaration re-anchors its LO's mastery when it is written
  (``tutor.promotions._write_gap_claim``), as a rung-variant request and a
  too-easy/too-hard report already did;
* replay applies each claim at its own ``created_at`` in the attempt stream
  (``substrate.replay._ClaimStream``): the seed reads only the claims made by
  the first attempt, and a later re-anchoring claim merges at its own time;
* a claim merged into a state that has evidence moves the mean only: the
  variance never drops below the state's own (AD §5.5);
* among equally specific covering claims the most recent wins, then the
  larger pseudo-count; the claimed level never breaks a tie.

The tag is ONE constant (``CLAIM_FIXES_ALGORITHM_VERSION``, built as
``mvp-0.32`` beside reader workbench RW7b's successor; the landing renumbers
it there and nothing else names a number).

The upgrade:

* accepts the immediate predecessor, or ``mvp-0.9`` up to it by running the
  predecessor's own upgrade first (with its own activation and notes, a
  refusal's included). If the chained steps succeed and this step then fails,
  the vault is left at the valid predecessor. Anything older is refused;
* changes learner state when it activates (the mastery rows of LOs a claim
  covers are replayed under the new claim semantics), so, under the vault
  mutation lock, ONE transaction covers the predecessor's manifest, the
  replay of exactly the LOs with attempts that a claim covers (no other LO's
  replay can change), the re-projection, the registry refresh and, last, the
  config's durable publication. A failure rolls the transaction back and, if
  the config was already renamed, names the predecessor again. A process that
  dies between the rename and the commit leaves the successor's label over
  the predecessor's mastery, which any rebuild completes (doctor reports the
  stale rebuild).

Nothing is rewritten: claims and attempts are raw ledgers and keep their
rows. Kill switch: ``mastery.claim_fixes_enabled = false`` seeds, re-anchors,
merges, ranks and replays exactly as the predecessor without a downgrade (a
rebuild then restores the predecessor's mastery); rolling the version back is
restore-only.
"""

from __future__ import annotations

import re
from pathlib import Path

from learnloop.algorithm_versions import (
    CLAIM_FIXES_ALGORITHM_VERSION,
    SUCCESSOR_CHAIN,
    WORKBENCH_FIELD_SIGNALS_ALGORITHM_VERSION,
)
from learnloop.clock import Clock
from learnloop.learner.mastery import learning_objects_with_covering_claims
from learnloop.ops.vault_upgrade import UpgradeResult, rewrite_algorithm_version
from learnloop.params import parameter_registry as registry_service
from learnloop.substrate.p0_projection import activate_p0_projection
from learnloop.substrate.rebuild_orchestrator import rebuild_all_derived_state
from learnloop.vault.loader import load_vault
from learnloop.vault.paths import VaultPaths
from learnloop.vault.repository import open_vault_repository
from learnloop.vault_lock import vault_mutation_lock
from learnloop.workbench_field_signals_upgrade import upgrade_to_workbench_field_signals

#: The immediate predecessor and its upgrade.
PREDECESSOR = WORKBENCH_FIELD_SIGNALS_ALGORITHM_VERSION
_upgrade_to_predecessor = upgrade_to_workbench_field_signals

#: Versions the upgrade accepts through the existing chain: mvp-0.9 up to the predecessor's own predecessor.
_CHAINED_PREDECESSORS = SUCCESSOR_CHAIN[:SUCCESSOR_CHAIN.index(PREDECESSOR)]

#: An earlier link's refusal already names its own step; it passes through unprefixed.
_STEP_REFUSAL = re.compile(r"^mvp-0\.\d+ step refused: ")


def upgrade_to_claim_fixes(root: Path, *, clock: Clock | None = None) -> UpgradeResult:
    """The predecessor (or mvp-0.9 onwards, through the chain) -> LP-min (a)'s tag: the claim fixes."""

    with vault_mutation_lock(Path(root), purpose="upgrade_claim_fixes"):
        return _upgrade(Path(root), clock=clock)


def _upgrade(root: Path, *, clock: Clock | None) -> UpgradeResult:
    vault = load_vault(root)
    original = vault.config.algorithms.algorithm_version
    target = CLAIM_FIXES_ALGORITHM_VERSION
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
    replayed = _activate(root, predecessor=predecessor, target=target, clock=clock)
    notes = list(chained_notes)
    if replayed:
        notes.append(
            f"replayed {len(replayed)} learning object(s) a learner claim covers, with each claim "
            f"at its own time: {', '.join(replayed)}"
        )
    return UpgradeResult(upgraded=True, from_version=original, to_version=target, notes=notes)


def _activate(root: Path, *, predecessor: str, target: str, clock: Clock | None) -> list[str]:
    """Activate ``target`` over the predecessor's vault in one transaction; the replayed LOs."""

    vault = load_vault(root)
    if vault.config.algorithms.algorithm_version != predecessor:  # pragma: no cover - read under the lock
        raise RuntimeError(f"{root}: algorithm_version changed during the upgrade to {target}")
    sqlite_path = VaultPaths(vault.root, vault.config).sqlite_path
    repository = open_vault_repository(vault.root, sqlite_path)
    config_path = root / "learnloop.toml"
    published = False
    try:
        with repository.atomic():
            registry_service.freeze_manifest(vault, repository, algorithm_version=predecessor, clock=clock)
            vault.config.algorithms.algorithm_version = target
            replayable = learning_objects_with_covering_claims(
                vault, repository, repository.learning_object_ids_with_attempts()
            )
            if replayable:
                rebuild_all_derived_state(vault, repository, learning_object_ids=replayable, clock=clock)
            activate_p0_projection(vault, repository, from_version=predecessor, clock=clock)
            registry_service.refresh(vault, repository, clock=clock)
            # Last: the commit follows the publication, so the database never
            # holds the successor's mastery under the predecessor's label.
            rewrite_algorithm_version(config_path, predecessor, target, durable=True)
            published = True
    except BaseException:
        if published:
            rewrite_algorithm_version(config_path, target, predecessor)
        raise
    return replayable


__all__ = ["PREDECESSOR", "upgrade_to_claim_fixes"]

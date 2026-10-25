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
  covers are rebuilt under the new claim semantics), so, under the vault
  mutation lock, ONE transaction covers the predecessor's manifest, the
  replay of the claim-covered LOs with attempts, the cold re-seed of the
  claim-covered LOs without any (exactly what a full rebuild writes for them,
  review F3), the re-projection, the registry refresh and, last, the config's
  durable publication. Every LO a full rebuild under the successor could
  change is in that set: with no covering claim there is no seed, no
  re-anchor and no tie to break.

**Activation is journalled across the config file and the database** (review
F2). Before the config is published an activation journal
(``<database>.claim-fixes-activation``, written and fsynced) names the
predecessor and the target; it is removed once the transaction commits. So:

* a failure before the publication rolls back, and the journal goes;
* a failure after the rename rolls back, the predecessor's label is restored
  and the journal goes (should the restore fail, the journal stays and the
  vault is in the recoverable state below);
* a process that dies after the publication and before the commit leaves the
  successor's label over the predecessor's database WITH the journal. The
  next desktop start (``learnloop_sidecar.context``, before state sync and
  the startup projection read the vault) and ``learnloop upgrade --to`` the
  tag both complete the activation from it
  (:func:`complete_interrupted_activation`); the upgrade never answers
  "already upgraded" while the journal stands. A journal whose activation
  had committed (the process died between the commit and the removal) is
  recognised by the activation's committed receipt and just removed.

Nothing is rewritten: claims and attempts are raw ledgers and keep their
rows. Kill switch: ``mastery.claim_fixes_enabled = false`` seeds, re-anchors,
merges, ranks and replays exactly as the predecessor without a downgrade (a
rebuild then restores the predecessor's mastery); rolling the version back is
restore-only.
"""

from __future__ import annotations

import json
import os
import re
from collections.abc import Callable
from pathlib import Path
from typing import NamedTuple

from learnloop.algorithm_versions import (
    CLAIM_FIXES_ALGORITHM_VERSION,
    SUCCESSOR_CHAIN,
    WORKBENCH_FIELD_SIGNALS_ALGORITHM_VERSION,
)
from learnloop.clock import Clock
from learnloop.learner.mastery import (
    initial_mastery_state_for_learning_object,
    learning_objects_with_covering_claims,
)
from learnloop.ops.vault_upgrade import UpgradeResult, rewrite_algorithm_version
from learnloop.params import parameter_registry as registry_service
from learnloop.substrate.p0_projection import activate_p0_projection
from learnloop.substrate.rebuild_orchestrator import COLD_MASTERY_BASELINE_AT, rebuild_all_derived_state
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
    """The predecessor (or mvp-0.9 onwards, through the chain) -> LP-min (a)'s tag: the claim fixes.

    On a vault already at the tag whose activation did not commit (the
    process died after publishing the config), it completes the activation."""

    with vault_mutation_lock(Path(root), purpose="upgrade_claim_fixes"):
        return _upgrade(Path(root), clock=clock)


def _upgrade(root: Path, *, clock: Clock | None) -> UpgradeResult:
    vault = load_vault(root)
    original = vault.config.algorithms.algorithm_version
    target = CLAIM_FIXES_ALGORITHM_VERSION
    predecessor = PREDECESSOR
    if original == target:
        resumed = _complete(root, clock=clock)
        if resumed is None:
            return UpgradeResult(upgraded=False, from_version=original, to_version=target,
                                 problems=[f"vault is already {target}"])
        notes = [f"completed the interrupted activation of {target}"] + _notes(resumed)
        return UpgradeResult(upgraded=True, from_version=target, to_version=target, notes=notes)
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
    activated = _activate(root, predecessor=predecessor, target=target, publish=True, clock=clock)
    return UpgradeResult(upgraded=True, from_version=original, to_version=target,
                         notes=list(chained_notes) + _notes(activated))


def complete_interrupted_activation(
    root: Path, *, vault=None, clock: Clock | None = None
) -> _Activated | None:
    """Finish an activation a dead process left journalled; None when there is none.

    Safe to call on every vault open: without a journal it checks one path
    (beside the database of ``vault``, the loaded vault at ``root`` when the
    caller has it) and returns. Runs under the vault mutation lock
    (re-entrant), so it waits for an upgrade still running in another process
    rather than racing it."""

    root = Path(root)
    if not _journal_path(vault if vault is not None else load_vault(root)).exists():
        return None
    with vault_mutation_lock(root, purpose="upgrade_claim_fixes_recovery"):
        return _complete(root, clock=clock)


def _complete(root: Path, *, clock: Clock | None) -> _Activated | None:
    vault = load_vault(root)
    journal_path = _journal_path(vault)
    journal = _read_journal(journal_path)
    if journal is None:
        return None
    predecessor, target = journal
    version = vault.config.algorithms.algorithm_version
    if version != target or target != CLAIM_FIXES_ALGORITHM_VERSION:
        # The config never named the successor (the publication had not
        # landed, so the transaction rolled back with it), or names another
        # version since: nothing of this activation is in force.
        journal_path.unlink(missing_ok=True)
        return None
    sqlite_path = VaultPaths(vault.root, vault.config).sqlite_path
    repository = open_vault_repository(vault.root, sqlite_path)
    if _activation_committed(repository, target):
        # The process died between the commit and the journal's removal: the
        # activation is complete, so there is nothing to finish.
        journal_path.unlink(missing_ok=True)
        return None
    return _activate(root, predecessor=predecessor, target=target, publish=False, clock=clock)


class _Activated(NamedTuple):
    replayed: tuple[str, ...]
    reseeded: tuple[str, ...]


def _notes(activated: _Activated) -> list[str]:
    notes: list[str] = []
    if activated.replayed:
        notes.append(
            f"replayed {len(activated.replayed)} learning object(s) a learner claim covers, with each claim "
            f"at its own time: {', '.join(activated.replayed)}"
        )
    if activated.reseeded:
        notes.append(
            f"re-seeded {len(activated.reseeded)} learning object(s) without attempts from the claim that "
            f"covers them, as a rebuild does: {', '.join(activated.reseeded)}"
        )
    return notes


def _activate(
    root: Path, *, predecessor: str, target: str, publish: bool, clock: Clock | None
) -> _Activated:
    """Activate ``target`` in one transaction; ``publish``: the config still names ``predecessor``.

    Without ``publish`` the config already names ``target`` (a journalled,
    uncommitted activation) and this completes the database side."""

    vault = load_vault(root)
    expected = predecessor if publish else target
    if vault.config.algorithms.algorithm_version != expected:  # pragma: no cover - read under the lock
        raise RuntimeError(f"{root}: algorithm_version changed during the upgrade to {target}")
    sqlite_path = VaultPaths(vault.root, vault.config).sqlite_path
    repository = open_vault_repository(vault.root, sqlite_path)
    config_path = root / "learnloop.toml"
    journal_path = _journal_path(vault)
    published = False
    try:
        with repository.atomic():
            # The predecessor's manifest, frozen from its own config (only the
            # version line differs) exactly as a clean upgrade freezes it.
            vault.config.algorithms.algorithm_version = predecessor
            registry_service.freeze_manifest(vault, repository, algorithm_version=predecessor, clock=clock)
            vault.config.algorithms.algorithm_version = target
            with_attempts = set(repository.learning_object_ids_with_attempts())
            covered = learning_objects_with_covering_claims(vault, repository, vault.learning_objects)
            replayable = [lo for lo in covered if lo in with_attempts]
            reseeded = [lo for lo in covered if lo not in with_attempts]
            if replayable:
                rebuild_all_derived_state(vault, repository, learning_object_ids=replayable, clock=clock)
            for learning_object_id in reseeded:
                # A claim-covered LO with no attempt: the cold row a full
                # rebuild writes for it (review F3), so activation and a later
                # same-version rebuild agree.
                repository.upsert_mastery_state(
                    initial_mastery_state_for_learning_object(
                        vault, repository, learning_object_id, COLD_MASTERY_BASELINE_AT
                    )
                )
            activate_p0_projection(vault, repository, from_version=predecessor, clock=clock)
            registry_service.refresh(vault, repository, clock=clock)
            if publish:
                # Last: the journal, then the publication; the commit follows,
                # so the database never holds the successor's mastery under
                # the predecessor's label, and a label without its database is
                # always journalled.
                _write_journal(journal_path, predecessor, target)

                def renamed() -> None:
                    nonlocal published
                    published = True

                _publish_algorithm_version(config_path, predecessor, target, renamed=renamed)
    except BaseException as failure:
        if not publish:
            raise
        restored = True
        if published:
            # The transaction rolled back after the config named the
            # successor: name the predecessor again.
            try:
                _publish_algorithm_version(config_path, target, predecessor)
            except Exception as restore_failure:  # pragma: no cover - a second failure on the same file
                restored = False
                failure.add_note(
                    f"{config_path} still names {target} over the {predecessor} database "
                    f"({restore_failure}); the activation journal stays, so the next start or "
                    f"`learnloop upgrade --to {target}` completes it"
                )
        if restored:
            journal_path.unlink(missing_ok=True)
        raise
    journal_path.unlink(missing_ok=True)
    return _Activated(tuple(replayable), tuple(reseeded))


#: The activation journal's name beside the vault database.
_JOURNAL_SUFFIX = ".claim-fixes-activation"


def _journal_path(vault) -> Path:
    sqlite_path = VaultPaths(vault.root, vault.config).sqlite_path
    return sqlite_path.with_name(sqlite_path.name + _JOURNAL_SUFFIX)


def _read_journal(path: Path) -> tuple[str, str] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None
    except (OSError, ValueError):
        # A torn journal can only come from a death before its fsync, which
        # precedes the publication: the config still names the predecessor.
        return (PREDECESSOR, CLAIM_FIXES_ALGORITHM_VERSION)
    return (str(payload.get("predecessor")), str(payload.get("target")))


def _write_journal(path: Path, predecessor: str, target: str) -> None:
    """Write the journal durably (temporary file, fsync, rename, directory fsync)."""

    tmp = path.with_name(path.name + ".tmp")
    try:
        with open(tmp, "w", encoding="utf-8") as handle:
            handle.write(json.dumps({"predecessor": predecessor, "target": target}, sort_keys=True))
            handle.flush()
            os.fsync(handle.fileno())
    except BaseException:
        tmp.unlink(missing_ok=True)
        raise
    tmp.replace(path)
    _fsync_directory(path.parent)


def _activation_committed(repository, target: str) -> bool:
    """Whether an activation of ``target`` committed: its projection receipt is on record."""

    with repository.connection() as connection:
        row = connection.execute(
            "SELECT 1 FROM derived_state_rebuilds WHERE scope = 'p0_projection_activation' "
            "AND algorithm_version = ? LIMIT 1",
            (target,),
        ).fetchone()
    return row is not None


def _publish_algorithm_version(
    config_path: Path, from_version: str, to_version: str, *, renamed: Callable[[], None] | None = None
) -> None:
    """The durable config rename, as ``regrade_contract_upgrade`` publishes it.

    ``renamed`` is called once the rename has landed (before the directory's
    fsync, which can still fail): from then on the config names ``to_version``."""

    rewrite_algorithm_version(config_path, from_version, to_version, durable=True)
    if renamed is not None:
        renamed()
    _fsync_directory(config_path.parent)


def _fsync_directory(directory: Path) -> None:
    handle = os.open(directory, os.O_RDONLY)
    try:
        os.fsync(handle)
    finally:
        os.close(handle)


__all__ = ["PREDECESSOR", "complete_interrupted_activation", "upgrade_to_claim_fixes"]

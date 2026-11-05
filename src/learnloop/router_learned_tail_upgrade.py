"""``learnloop upgrade --to <ROUTER_LEARNED_TAIL_ALGORITHM_VERSION>``: router objective RO6, a learned tail.

RO6 (owner decisions 2026-11-03 and 2026-11-04; ``docs/specs/spec_router_objective_v1.md`` §10). It is the next
link of the linear chain: everything the predecessor (RO5's mvp-0.48) means PLUS this:

* **fitted Q evaluation of a frozen logger version** (``router_objective.learned_tail``): low-dimensional belief
  features from RO0's decision-time snapshots, days to go and pending reports; the backup
  ``y_i = R_i + Σ_a′ π_ref(a′|x′_i)·Q̂(x′_i, a′)`` with the objective's own ``R`` and §3.2's carried cutoff; the
  logger version's own transitions only, generator versions as change points;
* **its entry as a residual** inside the numeric policy's value, ``Ṽ = V_tail + ŵ·V_residual``, ``ŵ`` a learned
  weight starting at zero that only RO5's randomized stop-coin contrasts (observed through its randomized checks)
  move, by slope and rank; the trace shows ``ŵ``, ``V_tail`` and ``V_residual`` per candidate.

The upgrade changes nothing already recorded: RO6 adds no table and no column, and nothing replays its fit (it
is recomputed from the traces and receipts as of each decision, and frozen into that decision's trace). Its
activation is the idempotent rebuild of the same projection namespace, the registry refresh and the config's
publication, journalled exactly as its predecessors' (one ``BEGIN IMMEDIATE`` transaction under the vault
mutation lock with the publication LAST; a death between the publication and the commit is completed by the next
guarded open, which installs :func:`complete_interrupted_activation`, the chain's latest; a journal naming an
earlier link is handed to the predecessor's completion).

``learned_tail = false`` serves mvp-0.48 exactly; rolling the version back is restore-only.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from learnloop import activation_journal
from learnloop.algorithm_versions import (
    ROUTER_CALIBRATION_ALGORITHM_VERSION,
    ROUTER_LEARNED_TAIL_ALGORITHM_VERSION,
    SUCCESSOR_CHAIN,
)
from learnloop.claim_fixes_upgrade import write_activation_journal as _write_journal
from learnloop.clock import Clock
from learnloop.ops.vault_upgrade import UpgradeResult
from learnloop.params import parameter_registry as registry_service
from learnloop.regrade_contract_upgrade import publish_algorithm_version as _publish_algorithm_version
from learnloop.router_calibration_upgrade import complete_interrupted_activation as _complete_predecessor_activation
from learnloop.router_calibration_upgrade import upgrade_to_router_calibration
from learnloop.substrate.p0_projection import activate_p0_projection
from learnloop.vault.loader import load_vault
from learnloop.vault.paths import VaultPaths
from learnloop.vault.repository import open_vault_repository
from learnloop.vault_lock import vault_mutation_lock

#: The immediate predecessor and its upgrade.
PREDECESSOR = ROUTER_CALIBRATION_ALGORITHM_VERSION
_upgrade_to_predecessor = upgrade_to_router_calibration

#: Versions the upgrade accepts through the existing chain: mvp-0.9 up to the predecessor's own predecessor.
_CHAINED_PREDECESSORS = SUCCESSOR_CHAIN[:SUCCESSOR_CHAIN.index(PREDECESSOR)]

#: An earlier link's refusal already names its own step; it passes through unprefixed.
_STEP_REFUSAL = re.compile(r"^mvp-0\.\d+ step refused: ")


def upgrade_to_router_learned_tail(root: Path, *, clock: Clock | None = None) -> UpgradeResult:
    """The predecessor (or mvp-0.9 onwards, through the chain) -> RO6's tag.

    On a vault already at the tag whose activation did not commit (the process died after publishing the
    config), it completes the activation."""

    with vault_mutation_lock(Path(root), purpose="upgrade_router_learned_tail"):
        return _upgrade(Path(root), clock=clock)


def complete_interrupted_activation(root: Path, *, vault=None, clock: Clock | None = None) -> str | None:
    """Finish any journalled activation of the chain a dead process left; None when there is none.

    A journal naming this tag is completed here; any other is handed to the predecessor's own completion. Safe
    to call on every vault open: without a journal it checks one path and returns."""

    root = Path(root)
    if not _journal_path(vault if vault is not None else load_vault(root)).exists():
        return None
    with vault_mutation_lock(root, purpose="upgrade_router_learned_tail_recovery"):
        with activation_journal.completing_activation():
            vault = load_vault(root)
            journal_path = _journal_path(vault)
            journal = _read_journal(journal_path)
            version = vault.config.algorithms.algorithm_version
            if journal is None:
                return None
            if journal == "torn":
                if version == PREDECESSOR:
                    # Torn before its fsync, which precedes this activation's publication: nothing of this
                    # activation is in force.
                    journal_path.unlink(missing_ok=True)
                    return None
            elif journal[1] == ROUTER_LEARNED_TAIL_ALGORITHM_VERSION:
                predecessor, target = journal
                if version != target:
                    journal_path.unlink(missing_ok=True)
                    return None
                activated = _activate(root, predecessor=predecessor, target=target, publish=False, clock=clock)
                journal_path.unlink(missing_ok=True)
                return target if activated else None
        # An earlier link's journal (or a torn one at an earlier version).
        return _complete_predecessor_activation(root, clock=clock)


def _journal_path(vault) -> Path:
    return activation_journal.journal_path(VaultPaths(vault.root, vault.config).sqlite_path)


def _read_journal(path: Path) -> tuple[str, str] | str | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        return (str(payload["predecessor"]), str(payload["target"]))
    except FileNotFoundError:
        return None
    except (OSError, ValueError, KeyError, TypeError):
        return "torn"


def _upgrade(root: Path, *, clock: Clock | None) -> UpgradeResult:
    target = ROUTER_LEARNED_TAIL_ALGORITHM_VERSION
    predecessor = PREDECESSOR
    completed = complete_interrupted_activation(root, clock=clock)
    vault = load_vault(root)
    original = vault.config.algorithms.algorithm_version
    if original == target and completed == target:
        return UpgradeResult(upgraded=True, from_version=target, to_version=target,
                             notes=[f"completed the interrupted activation of {target}"])
    if original == target:
        if not _activate(root, predecessor=predecessor, target=target, publish=False, clock=clock):
            return UpgradeResult(upgraded=False, from_version=original, to_version=target,
                                 problems=[f"vault is already {target}"])
        return UpgradeResult(upgraded=True, from_version=target, to_version=target,
                             notes=[f"completed the activation of {target} (its projection activation)"])
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
    _activate(root, predecessor=predecessor, target=target, publish=True, clock=clock)
    return UpgradeResult(upgraded=True, from_version=original, to_version=target, notes=chained_notes)


def _activate(root: Path, *, predecessor: str, target: str, publish: bool, clock: Clock | None) -> bool:
    """Activate ``target`` in one transaction (the predecessor's contract: the journal before the
    publication, the publication last, the journal removed once committed)."""

    with activation_journal.completing_activation():
        return _activate_as_writer(root, predecessor=predecessor, target=target, publish=publish, clock=clock)


def _activation_committed(repository, target: str) -> bool:
    with repository.connection() as connection:
        row = connection.execute(
            "SELECT 1 FROM derived_state_rebuilds WHERE scope = 'p0_projection_activation' "
            "AND algorithm_version = ? LIMIT 1",
            (target,),
        ).fetchone()
    return row is not None


def _activate_as_writer(root: Path, *, predecessor: str, target: str, publish: bool, clock: Clock | None) -> bool:
    vault = load_vault(root)
    expected = predecessor if publish else target
    if vault.config.algorithms.algorithm_version != expected:  # pragma: no cover - the caller read it under the lock
        raise RuntimeError(f"{root}: algorithm_version changed during the upgrade to {target}")
    sqlite_path = VaultPaths(vault.root, vault.config).sqlite_path
    repository = open_vault_repository(vault.root, sqlite_path)
    config_path = root / "learnloop.toml"
    journal_path = _journal_path(vault)
    published = False
    try:
        with repository.atomic():
            if not publish and _activation_committed(repository, target):
                return False
            vault.config.algorithms.algorithm_version = predecessor
            registry_service.freeze_manifest(vault, repository, algorithm_version=predecessor, clock=clock)
            vault.config.algorithms.algorithm_version = target
            activate_p0_projection(vault, repository, from_version=predecessor, clock=clock)
            registry_service.refresh(vault, repository, clock=clock)
            if publish:
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
    return True


__all__ = ["PREDECESSOR", "complete_interrupted_activation", "upgrade_to_router_learned_tail"]

"""``learnloop upgrade --to <SLIP_GAP_ALGORITHM_VERSION>``: slip or gap, the router weighs what a miss was.

Slip or gap SG1 + SG2 (owner decisions 2026-11-09; ``docs/specs/spec_slip_vs_gap_v1.md``). It is the next link of the
linear chain: everything the predecessor (the placement hole's mvp-0.56) means PLUS this:

* **SG1, the miss-cause sensor** (``[router_objective] miss_cause_sensor``, default true): each candidate topic's latest
  missed cold check's diagnosis cause-class probabilities (gap, slip, unknown), stored surprise and status are frozen in
  the objective's trace, on the lesson offer's card record and on the LLM policy's card. No numeric value moves.
* **SG2, the numeric policy weighs the cause** (``[router_objective] miss_cause_in_value``, default true, needs SG1): a
  lesson's and a repair's effect slope on a diagnosed topic is ``p_gap·γ_gap + p_slip·γ_slip + p_unknown·γ``, with
  ``p_gap`` calibrated by a learned surprise coefficient (prior 0) and ``γ_slip``'s seeded prior centred at 0.

Nothing already recorded changes meaning and no migration is needed: the sensor and the fits are computed from the
ledgers at each decision, and a logged decision replays to its own logged ``mu`` (the mix is unchanged). Its activation
is the idempotent rebuild of the same projection namespace, the registry refresh and the config's publication,
journalled exactly as its predecessors' (one ``BEGIN IMMEDIATE`` transaction under the vault mutation lock with the
publication LAST; a death between the publication and the commit is completed by the next guarded open, which installs
:func:`complete_interrupted_activation`, the chain's latest; a journal naming an earlier link is handed to the
predecessor's completion).

``miss_cause_sensor = false`` serves mvp-0.56's trace, card and values exactly; rolling the version back is
restore-only. Built on instruct/handoff as mvp-0.57: at its landing the placement fix's mvp-0.56 became
:data:`PREDECESSOR` (one import and one assignment).
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from learnloop import activation_journal
from learnloop.algorithm_versions import (
    SLIP_GAP_ALGORITHM_VERSION,
    SUCCESSOR_CHAIN,
    UNEVIDENCED_RETURN_ALGORITHM_VERSION,
)
from learnloop.claim_fixes_upgrade import write_activation_journal as _write_journal
from learnloop.clock import Clock
from learnloop.ops.vault_upgrade import UpgradeResult
from learnloop.params import parameter_registry as registry_service
from learnloop.regrade_contract_upgrade import publish_algorithm_version as _publish_algorithm_version
from learnloop.substrate.p0_projection import activate_p0_projection
from learnloop.unevidenced_return_upgrade import complete_interrupted_activation as _complete_predecessor_activation
from learnloop.unevidenced_return_upgrade import upgrade_to_unevidenced_return
from learnloop.vault.loader import load_vault
from learnloop.vault.paths import VaultPaths
from learnloop.vault.repository import open_vault_repository
from learnloop.vault_lock import vault_mutation_lock

#: The immediate predecessor and its upgrade.
PREDECESSOR = UNEVIDENCED_RETURN_ALGORITHM_VERSION
_upgrade_to_predecessor = upgrade_to_unevidenced_return

#: Versions the upgrade accepts through the existing chain: mvp-0.9 up to the predecessor's own predecessor.
_CHAINED_PREDECESSORS = SUCCESSOR_CHAIN[:SUCCESSOR_CHAIN.index(PREDECESSOR)]

#: An earlier link's refusal already names its own step; it passes through unprefixed.
_STEP_REFUSAL = re.compile(r"^mvp-0\.\d+ step refused: ")


def upgrade_to_slip_gap(root: Path, *, clock: Clock | None = None) -> UpgradeResult:
    """The predecessor (or mvp-0.9 onwards, through the chain) -> the slip-or-gap tag.

    On a vault already at the tag whose activation did not commit (the process died after publishing the
    config), it completes the activation."""

    with vault_mutation_lock(Path(root), purpose="upgrade_slip_gap"):
        return _upgrade(Path(root), clock=clock)


def complete_interrupted_activation(root: Path, *, vault=None, clock: Clock | None = None) -> str | None:
    """Finish any journalled activation of the chain a dead process left; None when there is none.

    A journal naming this tag is completed here; any other is handed to the predecessor's own completion. Safe
    to call on every vault open: without a journal it checks one path and returns."""

    root = Path(root)
    if not _journal_path(vault if vault is not None else load_vault(root)).exists():
        return None
    with vault_mutation_lock(root, purpose="upgrade_slip_gap_recovery"):
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
            elif journal[1] == SLIP_GAP_ALGORITHM_VERSION:
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
    target = SLIP_GAP_ALGORITHM_VERSION
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


__all__ = ["PREDECESSOR", "complete_interrupted_activation", "upgrade_to_slip_gap"]

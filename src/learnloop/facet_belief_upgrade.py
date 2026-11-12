"""``learnloop upgrade --to <FACET_BELIEF_FIX_ALGORITHM_VERSION>``: the facet-belief fixes.

Refactor bug ledger rows D-1, D-3, D-5 and D-6 (owner rule 2026-11-12: every bug a refactor step finds is fixed by its
landing or its arc's close; ``docs/reviews/refactor-dfb.md``). It is the next link of the linear chain: everything the
predecessor (the figure wait estimate's mvp-0.58) means PLUS this, behind ``facet_diagnostic.canonical_belief_fixes``
(default true):

* **the canonical facet belief** (``substrate/canonical_projection``): a success at or above the failure threshold ends
  the cell's failure streak (D-1); a transfer-tier criterion's evidence mass is ``teach_back.transfer_evidence_multiplier``
  of a core one's, success and failure alike (D-3); a total failure books coverage (independent and raw mass) on the
  targets its failure mass lands on, at their share (D-6). The facet evidence timeline applies the same D-3 scale;
* **per-LO facet uncertainty on canonical vaults** (D-5): the uncertainty the attempt path computes is written again
  (``facet_uncertainty``, per learning object, canonical facet ids, tagged), read back as the next attempt's prior and
  by ``facet_state_reader.facet_uncertainty_states_for_lo``, so the follow-up slate's facet-EIG ranking and overlap
  gate, the goal labels and the diagnostic view read it. The table is DERIVED, owned by learner replay.

The belief is re-projected over the whole ledger on every attempt, but what each attempt derived from it (mastery,
surprise, the follow-up decision, the uncertainty rows) is stored per attempt. So, like RO1's link, this one changes
learner state when it activates and does so in ONE ``BEGIN IMMEDIATE`` transaction under the vault mutation lock: the
predecessor's manifest, the whole-vault rebuild under the tag (whose receipt records the switch,
``projection_switches_json``), the registry refresh and the config's publication LAST. Completion is read from that
whole-vault rebuild's receipt under the tag. Run ``learnloop rebuild --shadow --set
algorithms.algorithm_version=<tag> --json`` on a copy first: its mastery, facet and schedule diffs are this upgrade's
report. Nothing recorded is rewritten and no migration is needed.

**Activation is journalled like its predecessors'.** The journal (``predecessor``, ``target``) is written before the
publication and removed after the commit, so a death between the two is completed by the next guarded open (every CLI
command and the desktop sidecar install :func:`complete_interrupted_activation`, the chain's latest completion) or
refused with the upgrade message. A journal naming this tag is completed here, and any other is handed to the
predecessor's completion.

``facet_diagnostic.canonical_belief_fixes = false`` serves mvp-0.58 exactly (the belief at once; what attempts stored
from it at the next whole-vault rebuild, ``doctor`` warning until then); rolling the version back is restore-only.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from learnloop import activation_journal
from learnloop.algorithm_versions import (
    FACET_BELIEF_FIX_ALGORITHM_VERSION,
    FIGURE_WAIT_ALGORITHM_VERSION,
    SUCCESSOR_CHAIN,
)
from learnloop.claim_fixes_upgrade import write_activation_journal as _write_journal
from learnloop.clock import Clock
from learnloop.figure_wait_upgrade import complete_interrupted_activation as _complete_predecessor_activation
from learnloop.figure_wait_upgrade import upgrade_to_figure_wait
from learnloop.ops.vault_upgrade import UpgradeResult
from learnloop.params import parameter_registry as registry_service
from learnloop.regrade_contract_upgrade import publish_algorithm_version as _publish_algorithm_version
from learnloop.substrate.rebuild_orchestrator import rebuild_all_derived_state
from learnloop.vault.loader import load_vault
from learnloop.vault.paths import VaultPaths
from learnloop.vault.repository import open_vault_repository
from learnloop.vault_lock import vault_mutation_lock

#: The immediate predecessor and its upgrade.
PREDECESSOR = FIGURE_WAIT_ALGORITHM_VERSION
_upgrade_to_predecessor = upgrade_to_figure_wait

#: Versions the upgrade accepts through the existing chain: mvp-0.9 up to the predecessor's own predecessor.
_CHAINED_PREDECESSORS = SUCCESSOR_CHAIN[:SUCCESSOR_CHAIN.index(PREDECESSOR)]

#: An earlier link's refusal already names its own step; it passes through unprefixed.
_STEP_REFUSAL = re.compile(r"^mvp-0\.\d+ step refused: ")


def upgrade_to_facet_belief(root: Path, *, clock: Clock | None = None) -> UpgradeResult:
    """The predecessor (or mvp-0.9 onwards, through the chain) -> the facet-belief fixes' tag.

    On a vault already at the tag whose activation did not commit (the process died after publishing the
    config), or that never had a whole-vault rebuild under it, it completes the activation."""

    with vault_mutation_lock(Path(root), purpose="upgrade_facet_belief"):
        return _upgrade(Path(root), clock=clock)


def complete_interrupted_activation(root: Path, *, vault=None, clock: Clock | None = None) -> str | None:
    """Finish any journalled activation of the chain a dead process left; None when there is none.

    A journal naming this tag is completed here; any other is handed to the predecessor's own completion. Safe
    to call on every vault open: without a journal it checks one path and returns."""

    root = Path(root)
    if not _journal_path(vault if vault is not None else load_vault(root)).exists():
        return None
    with vault_mutation_lock(root, purpose="upgrade_facet_belief_recovery"):
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
            elif journal[1] == FACET_BELIEF_FIX_ALGORITHM_VERSION:
                predecessor, target = journal
                if version != target:
                    journal_path.unlink(missing_ok=True)
                    return None
                # False: the process died between the commit and the journal's removal (already complete).
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
    target = FACET_BELIEF_FIX_ALGORITHM_VERSION
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
                             notes=[f"completed the activation of {target} (a whole-vault rebuild under it)"])
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
    """Rebuild the vault under ``target`` in one transaction (the predecessor's contract: the journal before the
    publication, the publication last, the journal removed once committed).

    Without ``publish`` the vault is already labelled ``target``: this completes an activation that did not commit
    and does nothing (returning False) once a whole-vault rebuild under ``target`` has committed (its receipt is
    written in this transaction, so it exists exactly when the activation committed)."""

    with activation_journal.completing_activation():
        return _activate_as_writer(root, predecessor=predecessor, target=target, publish=publish, clock=clock)


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
            if not publish and repository.has_whole_vault_rebuild(algorithm_version=target):
                return False
            vault.config.algorithms.algorithm_version = predecessor
            registry_service.freeze_manifest(vault, repository, algorithm_version=predecessor, clock=clock)
            vault.config.algorithms.algorithm_version = target
            # Every learning object replays: the belief, what each attempt derived from it and the per-LO
            # facet uncertainty may all move.
            rebuild_all_derived_state(vault, repository, clock=clock)
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


__all__ = ["PREDECESSOR", "complete_interrupted_activation", "upgrade_to_facet_belief"]

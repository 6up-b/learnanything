"""``learnloop upgrade --to <REPLAY_LEDGER_ALGORITHM_VERSION>``: rebuild equivalence.

Rebuild equivalence (``docs/reviews/rebuild-equivalence-fix.md``, its Codex
review F4): replay reads the ledger as the live write saw it. It is the next
link of the linear chain: everything the predecessor means PLUS this:

* replay bounds the recent-attempt windows (familiarity, event severity, item
  quality) and the canonical facet cache it reads (prediction, the variance
  floor, facet updates) at the replayed attempt's ledger position, so a
  rebuild reproduces the state the live writes left. A live write is
  unchanged: below the tag a rebuild read the attempts recorded after the one
  it recomputed.

The tag is ONE constant (``REPLAY_LEDGER_ALGORITHM_VERSION``, ``mvp-0.34``).
Built on main at ``mvp-0.31`` while RW7b and the LP claim fixes take
``mvp-0.32`` and ``mvp-0.33``; the landing chains it after them, so
:data:`PREDECESSOR` and its upgrade are the only names to move.

The upgrade:

* accepts the immediate predecessor, or ``mvp-0.9`` up to it by running the
  predecessor's own upgrade first (with its own activation and notes, a
  refusal's included). If the chained steps succeed and this step then fails,
  the vault is left at the valid predecessor. Anything older is refused;
* changes learner state when it activates (the rebuilt mastery, surprise,
  item quality and schedules of multi-attempt histories move to the live
  values), so like the regrade-contract successor it activates in ONE
  ``BEGIN IMMEDIATE`` transaction under the vault mutation lock: the
  predecessor's manifest, the whole-vault rebuild under the tag, the registry
  refresh, and the config's durable publication as its LAST step. A failure
  rolls everything back and the config still names the predecessor; a
  process that dies after the publication and before the commit leaves the
  tag over the predecessor's database, which running the upgrade again (or
  a whole-vault rebuild) completes. Completion is read from that whole-vault
  rebuild's receipt under the tag, never from the latest receipt (a startup
  or per-LO receipt can follow an unfinished activation).

Nothing is rewritten: attempts, grades and every ledger keep their rows. Kill
switch: ``replay.ledger_bounded = false`` replays exactly as the predecessor
without a downgrade; rolling the version back is restore-only.
"""

from __future__ import annotations

import re
from pathlib import Path

from learnloop.algorithm_versions import (
    REPLAY_LEDGER_ALGORITHM_VERSION,
    SUCCESSOR_CHAIN,
    WORKBENCH_FIELD_SIGNALS_ALGORITHM_VERSION,
)
from learnloop.clock import Clock
from learnloop.ops.vault_upgrade import UpgradeResult
from learnloop.params import parameter_registry as registry_service
from learnloop.regrade_contract_upgrade import _publish_algorithm_version
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


def upgrade_to_replay_ledger(root: Path, *, clock: Clock | None = None) -> UpgradeResult:
    """The predecessor (or mvp-0.9 onwards, through the chain) -> the rebuild-equivalence tag.

    On a vault already at the tag whose activation did not commit (the process
    died after publishing the config), it completes the activation."""

    with vault_mutation_lock(Path(root), purpose="upgrade_replay_ledger"):
        return _upgrade(Path(root), clock=clock)


def _upgrade(root: Path, *, clock: Clock | None) -> UpgradeResult:
    vault = load_vault(root)
    original = vault.config.algorithms.algorithm_version
    target = REPLAY_LEDGER_ALGORITHM_VERSION
    predecessor = PREDECESSOR
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
    _activate(root, predecessor=predecessor, target=target, publish=True, clock=clock)
    return UpgradeResult(upgraded=True, from_version=original, to_version=target, notes=chained_notes)


def _activate(root: Path, *, predecessor: str, target: str, publish: bool, clock: Clock | None) -> bool:
    """Rebuild the vault under ``target`` in one transaction.

    ``publish``: the vault is at ``predecessor``; the config's publication is
    the transaction's last step. Otherwise the vault is already labelled
    ``target``: this completes an activation that did not commit, and does
    nothing (returning False) once a whole-vault rebuild under ``target`` has
    committed.

    That receipt is the activation's own completion marker (re-review F5):
    ``rebuild_all_derived_state`` writes it in this transaction, so it exists
    exactly when the rebuild committed. The LATEST receipt is no marker: a
    desktop restart stamps a canonical-projection startup receipt under the
    tag without replaying mastery or schedules, a per-LO rebuild replays only
    its own LOs, and a vault may have no receipt at all. A vault labelled the
    tag that never had a whole-vault rebuild under it (a fresh one included)
    gets one, which at the tag reproduces the live state."""

    vault = load_vault(root)
    expected = predecessor if publish else target
    if vault.config.algorithms.algorithm_version != expected:  # pragma: no cover - the caller read it under the lock
        raise RuntimeError(f"{root}: algorithm_version changed during the upgrade to {target}")
    sqlite_path = VaultPaths(vault.root, vault.config).sqlite_path
    repository = open_vault_repository(vault.root, sqlite_path)
    config_path = root / "learnloop.toml"
    published = False
    try:
        with repository.atomic():
            if not publish:
                if repository.has_whole_vault_rebuild(algorithm_version=target):
                    return False
            # The predecessor's manifest, frozen from its own config (only the
            # version line differs) exactly as a clean upgrade freezes it.
            vault.config.algorithms.algorithm_version = predecessor
            registry_service.freeze_manifest(vault, repository, algorithm_version=predecessor, clock=clock)
            vault.config.algorithms.algorithm_version = target
            # Every learning object replays: any multi-attempt history may move.
            rebuild_all_derived_state(vault, repository, clock=clock)
            registry_service.refresh(vault, repository, clock=clock)
            if publish:
                # Last: the commit follows the publication, so the database
                # never holds the successor's state under the predecessor's label.
                def renamed() -> None:
                    nonlocal published
                    published = True

                _publish_algorithm_version(config_path, predecessor, target, renamed=renamed)
    except BaseException as failure:
        if published:
            try:
                _publish_algorithm_version(config_path, target, predecessor)
            except Exception as restore_failure:  # pragma: no cover - a second failure on the same file
                failure.add_note(
                    f"{config_path} still names {target} over the {predecessor} database "
                    f"({restore_failure}); run `learnloop upgrade --to {target}` again to complete it"
                )
        raise
    return True


__all__ = ["PREDECESSOR", "upgrade_to_replay_ledger"]

"""``learnloop upgrade``: the vault upgrade table, from the oldest supported tag up.

Each successor tag that changes persisted meaning has one row here, :class:`Link`: its tag and how it activates
(:data:`idempotent_projection`, :data:`whole_vault_rebuild`, or an :class:`Activation` of its own). A link's
predecessor is the tag before it in ``SUCCESSOR_CHAIN``; the table starts at the floor (``OLDEST_SUPPORTED``,
ADR-019), so the first row's predecessor is the floor. The upgrade from below the floor is the code tagged
``pre-floor`` (``version_floor.upgrade_commands``).

Every link activates the same way (playbook step 3), in ONE ``BEGIN IMMEDIATE`` transaction under the vault
mutation lock: the predecessor's parameter manifest is frozen, the link's activation runs under the tag, the
registry is refreshed, the journal (``predecessor``, ``target``) is written durably beside the database, and the
config's tag is published LAST by an atomic rename; the commit follows. So the database never holds the
successor's state under the predecessor's label, and a label without its database is always journalled: a death
between the publication and the commit leaves the journal, and the next opener that may write completes the
activation from it (``activation_journal`` runs :func:`complete_interrupted_activation`, which the CLI and the
desktop sidecar install). A failure before the commit restores the predecessor's label and removes the journal,
so the old config stays readable. Completion is read from the activation's own receipt, written in its
transaction, so a re-run after a committed activation does nothing.

A vault at a tag behind ``--to`` walks the rows from its own tag, one activation per row.
"""

from __future__ import annotations

import json
import os
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from pathlib import Path

from learnloop import activation_journal
from learnloop.algorithm_versions import (
    FACET_BELIEF_FIX_ALGORITHM_VERSION,
    LATEST_ALGORITHM_VERSION,
    SUCCESSOR_CHAIN,
)
from learnloop.clock import Clock
from learnloop.db.repositories import Repository
from learnloop.params import parameter_registry as registry_service
from learnloop.substrate.p0_projection import activate_p0_projection
from learnloop.substrate.rebuild_orchestrator import rebuild_all_derived_state
from learnloop.vault.loader import load_vault
from learnloop.vault.models import LoadedVault
from learnloop.vault.paths import VaultPaths
from learnloop.vault.repository import open_vault_repository
from learnloop.vault_lock import vault_mutation_lock
from learnloop.version_floor import BelowOldestSupported, refuse_journal_below_floor


@dataclass
class UpgradeResult:
    upgraded: bool
    from_version: str
    to_version: str
    problems: list[str] = field(default_factory=list)
    # Advisory lines printed with the result; never a refusal reason.
    notes: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class Activation:
    """How a link activates: ``run`` derives the tag's state inside the activation's transaction, and
    ``committed`` reads the receipt that transaction writes, so it is true exactly when an activation committed."""

    description: str
    run: Callable[[LoadedVault, Repository, str, Clock | None], None]
    committed: Callable[[Repository, str], bool]


def _project(vault: LoadedVault, repository: Repository, predecessor: str, clock: Clock | None) -> None:
    activate_p0_projection(vault, repository, from_version=predecessor, clock=clock)


def _projection_committed(repository: Repository, tag: str) -> bool:
    with repository.connection() as connection:
        row = connection.execute(
            "SELECT 1 FROM derived_state_rebuilds WHERE scope = 'p0_projection_activation' "
            "AND algorithm_version = ? LIMIT 1",
            (tag,),
        ).fetchone()
    return row is not None


def _rebuild(vault: LoadedVault, repository: Repository, predecessor: str, clock: Clock | None) -> None:
    rebuild_all_derived_state(vault, repository, clock=clock)


def _rebuild_committed(repository: Repository, tag: str) -> bool:
    return repository.has_whole_vault_rebuild(algorithm_version=tag)


#: A link that changes nothing already derived: the idempotent rebuild of the projection namespace, recorded
#: under the tag. Most successors are this (new behaviour behind the tag for new events only).
idempotent_projection = Activation("its projection activation", _project, _projection_committed)

#: A link that changes what is derived from history (a projection, or what each attempt stored from it): every
#: learning object replays under the tag, and the rebuild's receipt records the switches it derived under.
whole_vault_rebuild = Activation("a whole-vault rebuild under it", _rebuild, _rebuild_committed)


@dataclass(frozen=True)
class Link:
    tag: str
    activate: Activation

    @property
    def predecessor(self) -> str:
        return SUCCESSOR_CHAIN[SUCCESSOR_CHAIN.index(self.tag) - 1]


#: The upgrade table, oldest first: one row per successor from the floor up. A successor adds its row.
UPGRADES: tuple[Link, ...] = (
    # The facet-belief fixes move the belief and what each attempt derived from it.
    Link(FACET_BELIEF_FIX_ALGORITHM_VERSION, whole_vault_rebuild),
)


def targets(links: Sequence[Link] | None = None) -> tuple[str, ...]:
    """The tags ``learnloop upgrade --to`` accepts."""

    return tuple(link.tag for link in (UPGRADES if links is None else links))


def upgrade(
    root: Path, *, to: str = LATEST_ALGORITHM_VERSION, clock: Clock | None = None, links: Sequence[Link] | None = None
) -> UpgradeResult:
    """Bring the vault at ``root`` to ``to`` through the table, one activation per row from its own tag.

    On a vault already at ``to`` whose activation did not commit (the process died after publishing the config,
    or the vault was born at the tag), it completes the activation. A vault below the floor is refused with the
    route through ``pre-floor``."""

    root = Path(root)
    with vault_mutation_lock(root, purpose="upgrade"):
        try:
            return _upgrade(root, to=to, clock=clock, links=UPGRADES if links is None else links)
        except BelowOldestSupported as refused:
            return UpgradeResult(upgraded=False, from_version=refused.tag or "no algorithm_version", to_version=to,
                                 problems=[str(refused)])


def _upgrade(root: Path, *, to: str, clock: Clock | None, links: Sequence[Link]) -> UpgradeResult:
    by_tag = {link.tag: link for link in links}
    if to not in by_tag:
        raise ValueError(f"no upgrade to {to!r}; this LearnLoop upgrades to {', '.join(by_tag)}")
    completed = complete_interrupted_activation(root, clock=clock, links=links)
    vault = load_vault(root)
    original = vault.config.algorithms.algorithm_version
    sqlite_path = VaultPaths(vault.root, vault.config).sqlite_path
    if activation_journal.pending(sqlite_path):
        return UpgradeResult(upgraded=False, from_version=original, to_version=to,
                             problems=[_unknown_journal(sqlite_path)])
    if original == to:
        if completed == to:
            return UpgradeResult(upgraded=True, from_version=to, to_version=to,
                                 notes=[f"completed the interrupted activation of {to}"])
        link = by_tag[to]
        if not _activate(root, link, publish=False, clock=clock):
            return UpgradeResult(upgraded=False, from_version=original, to_version=to,
                                 problems=[f"vault is already {to}"])
        return UpgradeResult(upgraded=True, from_version=to, to_version=to,
                             notes=[f"completed the activation of {to} ({link.activate.description})"])
    walk = _walk(links, original, to)
    if walk is None:
        return UpgradeResult(
            upgraded=False, from_version=original, to_version=to,
            problems=[
                f"cannot upgrade from {original!r} to {to!r}: only {links[0].predecessor!r} to "
                f"{by_tag[to].predecessor!r} upgrade to it"
            ],
        )
    for link in walk:
        _activate(root, link, publish=True, clock=clock)
    return UpgradeResult(upgraded=True, from_version=original, to_version=to)


def _walk(links: Sequence[Link], original: str, to: str) -> list[Link] | None:
    """The rows from the one whose predecessor is ``original`` through ``to``; None when there is no such path (a
    jump: ``original`` is no predecessor in the table, or is past ``to``)."""

    tags = [link.tag for link in links]
    start = next((index for index, link in enumerate(links) if link.predecessor == original), None)
    end = tags.index(to)
    if start is None or start > end:
        return None
    return list(links[start:end + 1])


def _unknown_journal(sqlite_path: Path) -> str:
    return (
        f"{activation_journal.journal_path(sqlite_path).name} beside the database names an upgrade this LearnLoop "
        f"has no row for ({activation_journal.message(sqlite_path)})"
    )


def complete_interrupted_activation(
    root: Path, *, vault: LoadedVault | None = None, clock: Clock | None = None, links: Sequence[Link] | None = None
) -> str | None:
    """Finish an activation a dead process left journalled; the tag it completed, or None.

    Safe to call on every vault open: without a journal it checks one path (beside the database of ``vault``, the
    loaded vault at ``root`` when the caller has it) and returns. Under the vault mutation lock (re-entrant), so
    it waits for an upgrade still running in another process rather than racing it. A journal naming a tag the
    table has no row for is left standing, so the opener refuses with the upgrade message."""

    root = Path(root)
    if not _journal_path(vault if vault is not None else load_vault(root)).exists():
        return None
    with vault_mutation_lock(root, purpose="upgrade_recovery"):
        # This context is the activation's own writer: its opens complete nothing and are not refused while the
        # journal stands.
        with activation_journal.completing_activation():
            vault = load_vault(root)
            journal_path = _journal_path(vault)
            journal = _read_journal(journal_path)
            if journal is None:
                return None
            if journal == "torn":
                # Torn before its fsync, which precedes the publication: the config never named the target, so
                # nothing of that activation is in force.
                journal_path.unlink(missing_ok=True)
                return None
            predecessor, target = journal
            # Completing it would run a link this code no longer has.
            refuse_journal_below_floor(root, predecessor, target)
            if vault.config.algorithms.algorithm_version != target:
                # The publication never took effect (the transaction rolled back with it), or the vault names another
                # tag since: nothing of that activation is in force.
                journal_path.unlink(missing_ok=True)
                return None
            link = next((link for link in (UPGRADES if links is None else links) if link.tag == target), None)
            if link is None:
                return None
            # False: the process died between the commit and the journal's removal (already complete).
            activated = _activate(root, link, publish=False, clock=clock)
            journal_path.unlink(missing_ok=True)
            return target if activated else None


def _activate(root: Path, link: Link, *, publish: bool, clock: Clock | None) -> bool:
    """Activate ``link`` in one transaction; ``publish``: the config still names its predecessor.

    Without ``publish`` the config already names the tag: this completes an activation that did not commit, and
    does nothing (returning False) once one has."""

    with activation_journal.completing_activation():
        return _activate_as_writer(root, link, publish=publish, clock=clock)


def _activate_as_writer(root: Path, link: Link, *, publish: bool, clock: Clock | None) -> bool:
    vault = load_vault(root)
    predecessor, target = link.predecessor, link.tag
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
            if not publish and link.activate.committed(repository, target):
                return False
            # The predecessor's manifest, frozen from its own config (only the version line differs).
            vault.config.algorithms.algorithm_version = predecessor
            registry_service.freeze_manifest(vault, repository, algorithm_version=predecessor, clock=clock)
            vault.config.algorithms.algorithm_version = target
            link.activate.run(vault, repository, predecessor, clock)
            registry_service.refresh(vault, repository, clock=clock)
            if publish:
                write_activation_journal(journal_path, predecessor, target)

                def renamed() -> None:
                    nonlocal published
                    published = True

                publish_algorithm_version(config_path, predecessor, target, renamed=renamed)
    except BaseException as failure:
        if not publish:
            raise
        restored = True
        if published:
            # The transaction rolled back after the config named the successor: name the predecessor again.
            try:
                publish_algorithm_version(config_path, target, predecessor)
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


def _journal_path(vault: LoadedVault) -> Path:
    return activation_journal.journal_path(VaultPaths(vault.root, vault.config).sqlite_path)


def _read_journal(path: Path) -> tuple[str, str] | str | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        return (str(payload["predecessor"]), str(payload["target"]))
    except FileNotFoundError:
        return None
    except (OSError, ValueError, KeyError, TypeError):
        return "torn"


def write_activation_journal(path: Path, predecessor: str, target: str) -> None:
    """Write the journal durably: temporary file, fsync, rename, directory fsync."""

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


def publish_algorithm_version(
    config_path: Path, from_version: str, to_version: str, *, renamed: Callable[[], None] | None = None
) -> None:
    """The config's durable publication: the rename lands before the caller commits, and after a power loss it is
    never older than the commit (the temporary file is fsynced before the rename, the directory after it).

    ``renamed`` is called once the rename has landed and before the directory's fsync, which can still fail: from
    then on the config names ``to_version``."""

    rewrite_algorithm_version(config_path, from_version, to_version, durable=True)
    if renamed is not None:
        renamed()
    _fsync_directory(config_path.parent)


def rewrite_algorithm_version(
    config_path: Path, from_version: str, to_version: str, *, durable: bool = False
) -> None:
    """Atomically replace the config's one ``algorithm_version = "<from_version>"`` line (write-temp + rename).

    ``durable`` fsyncs the temporary file before the rename (a failure there removes it and leaves the config
    untouched), so the rename is the last step and anything that can fail after it is the caller's."""

    text = config_path.read_text(encoding="utf-8")
    needle = f'algorithm_version = "{from_version}"'
    if needle not in text:
        raise ValueError(f"algorithm_version = \"{from_version}\" not found in {config_path}")
    updated = text.replace(needle, f'algorithm_version = "{to_version}"', 1)
    tmp = config_path.with_suffix(config_path.suffix + ".tmp")
    if not durable:
        tmp.write_text(updated, encoding="utf-8")
        tmp.replace(config_path)
        return
    try:
        with open(tmp, "w", encoding="utf-8") as handle:
            handle.write(updated)
            handle.flush()
            os.fsync(handle.fileno())
    except BaseException:
        tmp.unlink(missing_ok=True)
        raise
    tmp.replace(config_path)


def _fsync_directory(directory: Path) -> None:
    handle = os.open(directory, os.O_RDONLY)
    try:
        os.fsync(handle)
    finally:
        os.close(handle)


__all__ = [
    "UPGRADES",
    "Activation",
    "Link",
    "UpgradeResult",
    "complete_interrupted_activation",
    "idempotent_projection",
    "publish_algorithm_version",
    "rewrite_algorithm_version",
    "targets",
    "upgrade",
    "whole_vault_rebuild",
    "write_activation_journal",
]

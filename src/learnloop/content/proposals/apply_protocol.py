"""Write-ahead apply protocol for proposal acceptance (source-ingestion §10.2).

Accepting a dependency closure is ONE logical YAML/DB transaction. A filesystem
and SQLite cannot commit atomically together, so acceptance uses a write-ahead
protocol:

1. Under the vault mutation lock, compute the transitive dependency closure of the
   accepted items. A dependent whose prerequisite is rejected/unaccepted becomes
   ``blocked`` (typed reason), never partially applied.
2. Compute the final target file contents by replaying the compiled writers
   against a throwaway staging copy of the vault — the real tree is untouched.
3. Commit a durable ``apply_intents`` record (accepted closure + target file
   contents/hashes + the DB side-effect plan) to SQLite FIRST.
4. Write each target to a staged temp file, fsync, and atomically rename into
   place.
5. Sync derived state, perform the DB side effects (proposal decisions, content
   events, entity_source_links), stamp the content recalibration, and mark the
   intent applied (the mark comes last, so a crash before it is recovered whole).

The vault mutation lock closes races; this protocol closes crashes. Recovery
(:func:`recover_apply_intents`) completes any intent left mid-flight: the sidecar
runs it at every primary bind, beside facet-identity recovery, and ``doctor
--fix-state`` runs it too. Application is idempotent at every boundary.

Recovery never writes over a newer file (K3.5). Each target records the hash of
the file it replaces (``pre_hash``; ``None`` when the file did not exist), and a
file is written only while it still holds that pre-image or already holds the
post-image. Any other content means something changed the file after the intent
was written: nothing of that intent is written, it is marked ``conflicted`` with
the files that differ, and it stays for the owner (doctor reports it; the
maintenance feed offers "Keep the files as they are", which sets it aside). While
an intent is pending or conflicted, ``patches.apply_accepted_items`` and
``patches.reject_applied_items`` refuse (``OutstandingApplyIntentError``), so no
accept or undo builds on a half-applied vault.
"""

from __future__ import annotations

import hashlib
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any

from learnloop.clock import Clock, utc_now_iso
from learnloop.db.copies import copy_tree_without_databases
from learnloop.db.repositories import Repository
from learnloop.ids import new_ulid
from learnloop.substrate.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault
from learnloop.vault.models import LoadedVault

# Directories never copied into the staging vault: derived caches and raw
# fetched bytes. Databases and their -wal/-shm/-journal companions are left out
# by copy_tree_without_databases. The staging run only replays YAML writers
# (which read YAML + config, never SQLite), so none of them are needed.
_STAGING_IGNORE = shutil.ignore_patterns(".learnloop", "canonical-sources")

_VALID_LINK_RELATIONS = frozenset(
    {"primary", "support", "alternate", "exercise", "assessment_alignment"}
)


def _sha256_bytes(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


# --- dependency closure -----------------------------------------------------


def compute_dependency_closure(
    repository: Repository, requested: list[dict[str, Any]]
) -> tuple[list[str], dict[str, dict[str, Any]]]:
    """Split the requested items into an applyable ordered closure and a blocked
    set (source-ingestion §10.2).

    An item is blocked when any prerequisite is rejected, is pending but not part
    of this acceptance set, or is itself blocked (transitive). Returns
    ``(ordered_apply_ids, blocked_by_id)`` where ``blocked_by_id`` maps a blocked
    item id to a typed ``{reason, blocking_item_id}`` payload.
    """

    requested_by_id = {item["id"]: item for item in requested}
    accepted_ids = set(requested_by_id)
    deps: dict[str, list[str]] = {
        item_id: repository.proposal_item_dependencies(item_id) for item_id in accepted_ids
    }

    blocked: dict[str, dict[str, Any]] = {}

    def block_reason(dep_id: str) -> dict[str, Any] | None:
        dep_item = repository.proposal_item(dep_id)
        decision = (dep_item or {}).get("decision")
        if decision == "accepted":
            return None  # prerequisite already applied
        if decision == "rejected":
            return {"reason": "prerequisite_rejected", "blocking_item_id": dep_id}
        if dep_id not in accepted_ids:
            return {"reason": "prerequisite_not_accepted", "blocking_item_id": dep_id}
        return None  # pending and in this acceptance set — provisionally satisfied

    # Fixed-point propagation: seed direct blocks, then propagate to dependents.
    changed = True
    while changed:
        changed = False
        for item_id in accepted_ids:
            if item_id in blocked:
                continue
            for dep_id in deps.get(item_id, []):
                reason = block_reason(dep_id)
                if reason is None and dep_id in blocked:
                    reason = {"reason": "prerequisite_blocked", "blocking_item_id": dep_id}
                if reason is not None:
                    blocked[item_id] = reason
                    changed = True
                    break

    applyable = [item_id for item_id in accepted_ids if item_id not in blocked]
    ordered = _topological_order(repository, requested_by_id, applyable, deps)
    return ordered, blocked


def _topological_order(
    repository: Repository,
    requested_by_id: dict[str, dict[str, Any]],
    applyable: list[str],
    deps: dict[str, list[str]],
) -> list[str]:
    from learnloop.content.proposals.patches import _proposal_apply_order

    apply_set = set(applyable)
    order_key = {
        item_id: _proposal_apply_order(requested_by_id[item_id]) for item_id in apply_set
    }
    result: list[str] = []
    placed: set[str] = set()
    remaining = set(apply_set)
    while remaining:
        progressed = False
        for item_id in list(sorted(remaining, key=lambda i: order_key[i])):
            intra_deps = set(deps.get(item_id, [])) & apply_set
            if intra_deps <= placed:
                result.append(item_id)
                placed.add(item_id)
                remaining.discard(item_id)
                progressed = True
        if not progressed:
            # Should not happen (cycles are rejected by the gates), but never loop
            # forever: fall back to the stable apply order.
            result.extend(sorted(remaining, key=lambda i: order_key[i]))
            break
    return result


# --- staging: compute final target contents ---------------------------------


def stage_target_contents(
    root: Path,
    vault: LoadedVault,
    ordered_items: list[dict[str, Any]],
    origin: str,
    patch_id: str,
    *,
    clock: Clock | None,
    facet_authority: Any = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Replay the compiled writers against a throwaway staging copy and capture
    the final target file contents plus the DB side-effect plan.

    ``facet_authority`` (``facet_identity.authority.ProposalAuthority``) checks
    each facet item's meaning write; a facet item compiled without it is
    refused. The real vault tree is never mutated here. Returns
    ``(targets, db_plan)``.
    """

    from learnloop.content.proposals.patches import PatchApplicationError, compile_proposal_item

    real_root = Path(vault.root)
    db_plan: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory(prefix="learnloop-apply-") as tmp:
        staging_root = Path(tmp) / "vault"
        copy_tree_without_databases(
            real_root,
            staging_root,
            database_names={_database_name(vault)},
            ignore=_STAGING_IGNORE,
        )
        staging_vault = load_vault(staging_root)
        for item in ordered_items:
            if item["validation_status"] == "invalid":
                raise PatchApplicationError(
                    f"Proposal item {item['id']} is invalid and cannot be accepted"
                )
            compiled = compile_proposal_item(staging_vault, item, facet_authority=facet_authority)
            compiled.apply(staging_vault.root, clock)
            staging_vault = load_vault(staging_root)
            now = utc_now_iso(clock)
            payload = item["edited_payload"] if item.get("edited_payload") is not None else item["payload"]
            db_plan.append(
                {
                    "item_id": item["id"],
                    "entity_type": compiled.entity_type,
                    "entity_id": compiled.entity_id,
                    "subject": compiled.subject,
                    "event_type": compiled.event_type,
                    "summary": compiled.summary,
                    "origin": origin,
                    "created_at": now,
                    "change_batch_id": new_ulid(),
                    "content_event_id": new_ulid(),
                    "source_links": _entity_source_link_rows(
                        compiled.entity_type,
                        compiled.entity_id,
                        compiled.link_payload if compiled.link_payload is not None else payload,
                        patch_id,
                    ),
                    "db_side_effect": _stamp_side_effect(compiled.db_side_effect, patch_id),
                }
            )
        targets = _diff_targets(real_root, staging_root)
    return targets, db_plan


def _stamp_side_effect(side_effect: dict[str, Any] | None, patch_id: str) -> dict[str, Any] | None:
    """Stamp the accepting patch id onto a specialized additive side effect (§10.2)."""

    if not side_effect:
        return None
    stamped = {"kind": side_effect["kind"], "row": dict(side_effect["row"])}
    stamped["row"]["patch_id"] = patch_id
    return stamped


def _diff_targets(real_root: Path, staging_root: Path) -> list[dict[str, Any]]:
    targets: list[dict[str, Any]] = []
    for staged_path in sorted(staging_root.rglob("*")):
        if not staged_path.is_file():
            continue
        rel = staged_path.relative_to(staging_root)
        if _is_ignored(rel):
            continue
        staged_bytes = staged_path.read_bytes()
        real_path = real_root / rel
        if real_path.exists():
            real_bytes = real_path.read_bytes()
            if real_bytes == staged_bytes:
                continue
            pre_hash: str | None = _sha256_bytes(real_bytes)
        else:
            pre_hash = None
        targets.append(
            {
                "rel_path": rel.as_posix(),
                "pre_hash": pre_hash,
                "post_content": staged_bytes.decode("utf-8"),
                "post_hash": _sha256_bytes(staged_bytes),
            }
        )
    return targets


def _database_name(vault: LoadedVault) -> str:
    return Path(vault.config.storage.sqlite_path).name


def _is_ignored(rel: Path) -> bool:
    parts = rel.parts
    if ".learnloop" in parts or "canonical-sources" in parts:
        return True
    return rel.name.startswith("state.sqlite") or rel.suffix == ".sqlite"


def _entity_source_link_rows(
    entity_type: str, entity_id: str, payload: Any, patch_id: str
) -> list[dict[str, Any]]:
    """Map a created entity's YAML ``provenance.source_refs`` snapshot into
    entity_source_links rows (source-ingestion §9.1).

    Only refs carrying a locator (the schema's NOT NULL column) become rows; a
    plain note/manual-context ref without a source span is skipped. Relation
    defaults to ``support``; the row status is ``current``.
    """

    if not isinstance(payload, dict):
        return []
    provenance = payload.get("provenance")
    if not isinstance(provenance, dict):
        return []
    refs = provenance.get("source_refs")
    if not isinstance(refs, list):
        return []
    rows: list[dict[str, Any]] = []
    for ref in refs:
        if not isinstance(ref, dict):
            continue
        locator = ref.get("locator")
        if not locator:
            continue
        relation = ref.get("relation") or "support"
        if relation not in _VALID_LINK_RELATIONS:
            relation = "support"
        source_id = ref.get("source_id")
        if source_id is None and ref.get("ref_type") == "canonical_source":
            source_id = ref.get("ref_id")
        rows.append(
            {
                "id": new_ulid(),
                "entity_type": entity_type,
                "entity_id": entity_id,
                "source_id": source_id,
                "revision_id": ref.get("revision_id"),
                "locator": str(locator),
                "locator_scheme": ref.get("locator_scheme") or ref.get("scheme"),
                "relation": relation,
                "extraction_id": ref.get("extraction_id"),
                "asset_hash": ref.get("asset_hash"),
                "span_hash": ref.get("span_hash") or ref.get("quote_hash"),
                "patch_id": patch_id,
                "status": "current",
            }
        )
    return rows


def entity_source_link_rows(
    entity_type: str, entity_id: str, payload: Any, patch_id: str
) -> list[dict[str, Any]]:
    """The entity_source_links rows a payload's ``provenance.source_refs`` record (fixed ids).

    The rows a proposal apply installs for a written entity; a confirmed facet
    reword (``facet_identity.actions.confirm_reword``) installs its validated
    citations the same way, write-ahead.
    """

    return _entity_source_link_rows(entity_type, entity_id, payload, patch_id)


# --- materialize: staged temp -> fsync -> atomic rename ----------------------


class ApplyTargetConflict(Exception):
    """Target files hold neither the intent's pre-image nor its post-image (K3.5).

    Raised by :func:`materialize_targets` before it writes anything.
    ``conflicts`` lists ``{rel_path, pre_hash, post_hash, found_hash}`` per file
    (``found_hash`` is ``None`` for a file that is gone).
    """

    def __init__(self, conflicts: list[dict[str, Any]]) -> None:
        self.conflicts = conflicts
        paths = ", ".join(conflict["rel_path"] for conflict in conflicts)
        super().__init__(f"changed since the apply was planned: {paths}")


def target_conflicts(root: Path, targets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """The targets whose file holds neither ``pre_hash`` (absent when ``None``) nor ``post_hash``.

    Only a target that carries a ``pre_hash`` key is checked. Every apply intent's
    targets do (``_diff_targets`` always writes it, ``None`` for a new file); the
    other callers of :func:`materialize_targets` use it as a plain atomic write
    under the vault lock (facet registry saves, doctor's content fixes) and pass
    no pre-image, so they write as before.
    """

    conflicts: list[dict[str, Any]] = []
    for target in targets:
        if "pre_hash" not in target:
            continue
        dest = Path(root) / target["rel_path"]
        found = _sha256_bytes(dest.read_bytes()) if dest.exists() else None
        if found == target["post_hash"] or found == target.get("pre_hash"):
            continue
        conflicts.append(
            {
                "rel_path": target["rel_path"],
                "pre_hash": target.get("pre_hash"),
                "post_hash": target["post_hash"],
                "found_hash": found,
            }
        )
    return conflicts


def materialize_targets(root: Path, targets: list[dict[str, Any]]) -> None:
    """Write each target via a staged fsynced temp file and an atomic rename.

    Idempotent: a target whose on-disk content already matches ``post_hash`` is
    skipped, so recovery re-runs harmlessly. A target that carries ``pre_hash``
    is written only over that pre-image (no file when it is ``None``): every
    such target is checked first, and if any file holds something else (it
    changed after the intent was written) :class:`ApplyTargetConflict` is
    raised and nothing is written (K3.5). See :func:`target_conflicts`.
    """

    root = Path(root)
    conflicts = target_conflicts(root, targets)
    if conflicts:
        raise ApplyTargetConflict(conflicts)
    touched_dirs: set[Path] = set()
    for target in targets:
        dest = root / target["rel_path"]
        post_bytes = target["post_content"].encode("utf-8")
        if dest.exists() and _sha256_bytes(dest.read_bytes()) == target["post_hash"]:
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp_name = tempfile.mkstemp(prefix=".apply-", dir=str(dest.parent))
        try:
            with os.fdopen(fd, "wb") as handle:
                handle.write(post_bytes)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(tmp_name, dest)
            touched_dirs.add(dest.parent)
        except BaseException:
            if os.path.exists(tmp_name):
                os.unlink(tmp_name)
            raise
    for directory in touched_dirs:
        _fsync_dir(directory)


def _fsync_dir(directory: Path) -> None:
    try:
        dir_fd = os.open(str(directory), os.O_RDONLY)
    except OSError:
        return
    try:
        os.fsync(dir_fd)
    except OSError:
        pass
    finally:
        os.close(dir_fd)


# --- DB side effects (shared by the normal path and recovery) ---------------


def perform_db_effects(
    repository: Repository, db_plan: list[dict[str, Any]], *, clock: Clock | None
) -> list[str]:
    """Record proposal decisions, content events, and provenance links.

    Idempotent: an item already accepted (recovery after a partial DB write) is
    not re-recorded, and entity_source_links insert with INSERT OR IGNORE.
    Returns the change-batch ids in plan order.
    """

    change_batch_ids: list[str] = []
    for entry in db_plan:
        change_batch_ids.append(entry["change_batch_id"])
        existing = repository.proposal_item(entry["item_id"])
        already_accepted = bool(existing) and existing.get("decision") == "accepted"
        if not already_accepted:
            # Specialized side effect FIRST + idempotently: if a crash lands between
            # it and the accept mark, recovery re-runs both harmlessly (§10.2).
            _perform_side_effect(repository, entry.get("db_side_effect"), entry["created_at"], clock)
            repository.record_applied_proposal_item(
                proposal_item_id=entry["item_id"],
                change_batch={
                    "id": entry["change_batch_id"],
                    "reason": "proposal_accept",
                    "origin": entry["origin"],
                    "summary": entry["summary"],
                    "created_at": entry["created_at"],
                },
                content_events=[
                    {
                        "id": entry["content_event_id"],
                        "event_type": entry["event_type"],
                        "subject": entry["subject"],
                        "entity_type": entry["entity_type"],
                        "entity_id": entry["entity_id"],
                        "origin": entry["origin"],
                        "review_status": "accepted",
                        "summary": entry["summary"],
                        "created_at": entry["created_at"],
                    }
                ],
                clock=clock,
            )
        for link in entry.get("source_links", []):
            repository.insert_entity_source_link(
                link_id=link["id"],
                entity_type=link["entity_type"],
                entity_id=link["entity_id"],
                locator=link["locator"],
                relation=link["relation"],
                source_id=link.get("source_id"),
                revision_id=link.get("revision_id"),
                locator_scheme=link.get("locator_scheme"),
                extraction_id=link.get("extraction_id"),
                asset_hash=link.get("asset_hash"),
                span_hash=link.get("span_hash"),
                patch_id=link.get("patch_id"),
                status=link.get("status", "current"),
                created_at=entry["created_at"],
            )
    return change_batch_ids


def _perform_side_effect(
    repository: Repository, side_effect: dict[str, Any] | None, created_at: str, clock: Clock | None
) -> None:
    """Apply a specialized additive item's DB write (§10.2). Runs only inside the
    not-already-accepted guard, so recovery re-runs harmlessly; ids are fixed in the
    durable intent, and the specialized tables' inserts are keyed on those ids."""

    if not side_effect:
        return
    kind = side_effect["kind"]
    row = side_effect["row"]
    if kind == "facet_version":
        # An existing facet's meaning changed: keep the entry it replaced as a
        # ``reword`` action with an undo (facet locks removed, owner 2026-10-12).
        # A title or worked-example change is recorded the same way, with its
        # sources, but is not a version (owner, 2026-10-13).
        from learnloop.content.facet_identity.actions import record_reword

        patch_id = row.get("patch_id")
        record_reword(
            repository,
            action_id=str(row["id"]),
            facet_id=str(row["facet_id"]),
            before=row["before"],
            after=row["after"],
            run_id=_run_id_for_patch(repository, patch_id),
            proposal_id=patch_id,
            proposal_item_id=row.get("proposal_item_id"),
            sources=row.get("sources"),
            presentation=bool(row.get("presentation")),
            fields=row.get("fields"),
            span_support=row.get("span_support") or None,
            clock=clock,
        )
    elif kind == "facet_reword_confirm":
        # A reword with no explanatory support: held for the owner's confirm,
        # nothing written to facets.yaml (owner, 2026-10-13).
        from learnloop.content.facet_identity.actions import record_reword_confirm

        patch_id = row.get("patch_id")
        record_reword_confirm(
            repository,
            action_id=str(row["id"]),
            facet_id=str(row["facet_id"]),
            before=row["before"],
            after=row["after"],
            fields=row.get("fields") or [],
            sources=row.get("sources") or [],
            unresolved=row.get("unresolved") or [],
            meaning_support=row.get("meaning_support") or [],
            message=str(row.get("message") or ""),
            span_support=row.get("span_support") or {},
            run_id=_run_id_for_patch(repository, patch_id),
            proposal_id=patch_id,
            proposal_item_id=row.get("proposal_item_id"),
            clock=clock,
        )
    elif kind == "required_method_owner_verdict":
        # The owner's accepted required-method override (review F16): their
        # verdict in judgment_ledger, keyed on the fixed id in the intent.
        from learnloop.content.proposals.required_method_override import record_owner_verdict

        record_owner_verdict(repository, row, created_at)
    elif kind == "provenance_link":
        repository.insert_entity_source_link(
            link_id=row["id"],
            entity_type=row["entity_type"],
            entity_id=row["entity_id"],
            locator=row["locator"],
            relation=row["relation"],
            source_id=row.get("source_id"),
            revision_id=row.get("revision_id"),
            locator_scheme=row.get("locator_scheme"),
            extraction_id=row.get("extraction_id"),
            asset_hash=row.get("asset_hash"),
            span_hash=row.get("span_hash"),
            patch_id=row.get("patch_id"),
            status=row.get("status", "current"),
            created_at=created_at,
        )
    elif kind == "notation_mapping":
        existing = repository.notation_mappings_for_entity(row["entity_type"], row["entity_id"])
        if any(m["id"] == row["id"] for m in existing):
            return
        repository.insert_notation_mapping(
            mapping_id=row["id"],
            entity_type=row["entity_type"],
            entity_id=row["entity_id"],
            canonical_notation=row["canonical_notation"],
            alternate_notation=row["alternate_notation"],
            subject_id=row.get("subject_id"),
            context=row.get("context"),
            source_id=row.get("source_id"),
            revision_id=row.get("revision_id"),
            locator=row.get("locator"),
            patch_id=row.get("patch_id"),
            status=row.get("status", "active"),
            clock=clock,
        )
    elif kind == "source_conflict":
        if repository.source_conflict(row["id"]) is not None:
            return
        repository.insert_source_conflict(
            conflict_id=row["id"],
            entity_type=row["entity_type"],
            entity_id=row["entity_id"],
            statement=row["statement"],
            subject_id=row.get("subject_id"),
            left_source_id=row.get("left_source_id"),
            left_revision_id=row.get("left_revision_id"),
            left_locator=row.get("left_locator"),
            right_source_id=row.get("right_source_id"),
            right_revision_id=row.get("right_revision_id"),
            right_locator=row.get("right_locator"),
            status=row.get("status", "open"),
            patch_id=row.get("patch_id"),
            clock=clock,
        )


def _run_id_for_patch(repository: Repository, patch_id: str | None) -> str:
    """The synthesis run that produced a proposal, so its job lists the reword."""

    if not patch_id:
        return "proposal"
    try:
        batch = repository.proposal_batch(patch_id) or {}
        run = repository.synthesis_run_for_agent_run(str(batch.get("agent_run_id") or "")) or {}
    except Exception:  # noqa: BLE001 - a label lookup never fails an apply
        return str(patch_id)
    return str(run.get("id") or patch_id)


# --- recovery ---------------------------------------------------------------


def complete_apply_intent(
    root: Path, repository: Repository, intent: dict[str, Any], *, clock: Clock | None = None
) -> bool:
    """Finish one pending (or re-checked conflicted) intent; False when it is conflicted.

    Re-materializes the targets (each only over its pre-image or already at its
    post-image), syncs derived state, performs any not-yet-applied DB effects,
    recalibrates, and marks the intent applied. A target holding anything else
    writes nothing and marks the intent ``conflicted`` with the files that
    differ (K3.5). The caller holds the vault mutation lock.
    """

    from learnloop.content.proposals.patches import recalibrate_applied_content

    try:
        materialize_targets(root, intent["targets"])
    except ApplyTargetConflict as exc:
        repository.mark_apply_intent_conflicted(intent["id"], exc.conflicts, clock=clock)
        return False
    vault_after = load_vault(root)
    sync_vault_state(vault_after, repository, clock=clock)
    perform_db_effects(repository, intent["db_plan"], clock=clock)
    items = [item for item in (repository.proposal_item(item_id) for item_id in intent["item_ids"]) if item]
    recalibrate_applied_content(vault_after, repository, items, clock=clock)
    repository.mark_apply_intent_applied(intent["id"], clock=clock)
    return True


def recover_apply_intents(
    root: Path, repository: Repository, *, clock: Clock | None = None
) -> list[str]:
    """Complete any apply intent left mid-flight (sidecar bind and doctor recovery, §10.2).

    Idempotent and safe at every crash boundary (see :func:`complete_apply_intent`);
    an intent whose files changed since is marked ``conflicted`` and left for the
    owner, never written over. With nothing pending it reads one query and
    touches nothing (not even the lock file); otherwise it runs under the vault
    mutation lock (re-entrant, so a caller may already hold it). Returns the ids
    of the intents it completed; conflicted ones are read back with
    ``repository.outstanding_apply_intents()``.
    """

    from learnloop.vault_lock import vault_mutation_lock

    if not repository.pending_apply_intents():
        return []
    recovered: list[str] = []
    with vault_mutation_lock(Path(root), purpose="recover_apply_intents"):
        for intent in repository.pending_apply_intents():
            if complete_apply_intent(root, repository, intent, clock=clock):
                recovered.append(intent["id"])
    return recovered


class ApplyIntentResolutionError(ValueError):
    """An owner's resolution that does not fit the intent's state."""


def resolve_apply_intent(
    root: Path, repository: Repository, intent_id: str, resolution: str, *, clock: Clock | None = None
) -> dict[str, Any]:
    """The maintenance feed's action on an outstanding intent (K3.5).

    * ``complete``: finish a pending intent, or re-check a conflicted one (a
      file the owner put back to its pre- or post-image completes it); a file
      that still differs leaves it ``conflicted``.
    * ``keep_files``: set a conflicted intent aside. The files stay as they
      are, the intent's DB effects are never performed and its proposal items
      stay pending; derived state is synced to the files.

    Runs under the vault mutation lock. Returns the intent as it now stands.
    """

    from learnloop.vault_lock import vault_mutation_lock

    with vault_mutation_lock(Path(root), purpose="resolve_apply_intent"):
        intent = repository.apply_intent(intent_id)
        if intent is None:
            raise ApplyIntentResolutionError(f"No apply intent {intent_id}")
        status = intent["status"]
        if resolution == "complete":
            if status not in {"pending", "conflicted"}:
                raise ApplyIntentResolutionError(f"Apply intent {intent_id} is {status}; nothing to complete")
            complete_apply_intent(root, repository, intent, clock=clock)
        elif resolution == "keep_files":
            if status != "conflicted":
                raise ApplyIntentResolutionError(
                    f"Apply intent {intent_id} is {status}; only a conflicted intent is set aside"
                )
            repository.mark_apply_intent_set_aside(intent_id, clock=clock)
            sync_vault_state(load_vault(root), repository, clock=clock)
        else:
            raise ApplyIntentResolutionError(f"Unknown resolution {resolution!r}")
        return repository.apply_intent(intent_id) or {}

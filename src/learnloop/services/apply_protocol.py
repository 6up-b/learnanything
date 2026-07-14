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
   events, entity_source_links), and mark the intent applied.

The vault mutation lock closes races; this protocol closes crashes. Startup/doctor
recovery (:func:`recover_apply_intents`) completes any intent left mid-flight, and
application is idempotent at every boundary.
"""

from __future__ import annotations

import hashlib
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any

from learnloop.clock import Clock, utc_now_iso
from learnloop.db.repositories import Repository
from learnloop.ids import new_ulid
from learnloop.services.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault
from learnloop.vault.models import LoadedVault
from learnloop.vault.paths import VaultPaths

# Directories/files never copied into the staging vault: derived caches, raw
# fetched bytes, and the SQLite database. The staging run only replays YAML
# writers (which read YAML + config, never SQLite), so none are needed.
_STAGING_IGNORE = shutil.ignore_patterns(
    ".learnloop",
    "canonical-sources",
    "state.sqlite",
    "state.sqlite-shm",
    "state.sqlite-wal",
    "*.sqlite",
    "*.sqlite-shm",
    "*.sqlite-wal",
)

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
    from learnloop.services.patches import _proposal_apply_order

    apply_set = set(applyable)
    order_key = {
        item_id: _proposal_apply_order(requested_by_id[item_id]) for item_id in apply_set
    }
    ready = sorted(
        (i for i in apply_set if not (set(deps.get(i, [])) & apply_set)),
        key=lambda i: order_key[i],
    )
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
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Replay the compiled writers against a throwaway staging copy and capture
    the final target file contents plus the DB side-effect plan.

    The real vault tree is never mutated here. Returns ``(targets, db_plan)``.
    """

    from learnloop.services.patches import PatchApplicationError, compile_proposal_item

    real_root = Path(vault.root)
    db_plan: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory(prefix="learnloop-apply-") as tmp:
        staging_root = Path(tmp) / "vault"
        shutil.copytree(real_root, staging_root, ignore=_STAGING_IGNORE)
        staging_vault = load_vault(staging_root)
        for item in ordered_items:
            if item["validation_status"] == "invalid":
                raise PatchApplicationError(
                    f"Proposal item {item['id']} is invalid and cannot be accepted"
                )
            compiled = compile_proposal_item(staging_vault, item)
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
                        compiled.entity_type, compiled.entity_id, payload, patch_id
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


# --- materialize: staged temp -> fsync -> atomic rename ----------------------


def materialize_targets(root: Path, targets: list[dict[str, Any]]) -> None:
    """Write each target via a staged fsynced temp file and an atomic rename.

    Idempotent: a target whose on-disk content already matches ``post_hash`` is
    skipped, so recovery re-runs harmlessly.
    """

    root = Path(root)
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
    if kind == "provenance_link":
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


# --- recovery ---------------------------------------------------------------


def recover_apply_intents(
    root: Path, repository: Repository, *, clock: Clock | None = None
) -> list[str]:
    """Complete any apply intent left mid-flight (startup/doctor recovery, §10.2).

    Idempotent and safe at both crash boundaries: it re-materializes target files
    (skipping any already at ``post_hash``), performs any not-yet-applied DB
    effects, syncs derived state, and marks the intent applied. Returns the ids of
    the intents it recovered.
    """

    pending = repository.pending_apply_intents()
    if not pending:
        return []
    recovered: list[str] = []
    for intent in pending:
        materialize_targets(root, intent["targets"])
        sync_vault_state(load_vault(root), repository, clock=clock)
        perform_db_effects(repository, intent["db_plan"], clock=clock)
        repository.mark_apply_intent_applied(intent["id"], clock=clock)
        recovered.append(intent["id"])
    return recovered

"""Applied facet-identity actions, the vault-level merge, and one-tap undo.

An action is one judged set: a survivor facet plus the facets merged or
absorbed into it. Every reference to a retired facet (recipe components,
criterion targets, evidence facets, goals, database rows) keeps its id on
disk: the retired id becomes an alias of the survivor, and the loader and the
projections resolve aliases (``vault.facet_aliases``, then ``facet_merges``).
So an action changes only ``facets.yaml`` (and, for registered facets, the
``facet_merges`` map), and it records exactly what it replaced:

* the ``facets.yaml`` entries before and after (the survivor's entry, and
  each retired facet's entry, which the action removed, with its position);
* the ``facet_merges`` rows it inserted (vault scope only: a retired facet
  that already existed may carry evidence, and that map is how projections
  re-key it).

Three scopes share the record:

* ``vault``: two registered facets (``learnloop facets dedupe``), applied
  here by :func:`merge_registered_facets`;
* ``in_run``: candidates of one synthesis or append run, merged before the
  proposal existed; the proposal carries the survivor;
* ``attach``: a candidate aliased or absorbed into a registered facet.

In-run and attach actions are recorded ``proposed`` with their proposal; they
are undoable once the proposal is applied (the vault then shows exactly what
they wrote). An undo refuses when the survivor's entry changed since (a later
action or an edit), naming the later action, rather than overwrite it.
Evidence is re-keyed by the standard content recalibration of the affected
learning objects after both the merge and the undo, so derived state returns
to exactly what it was; attempts made after a merge stay with the survivor.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
import copy
import json
from pathlib import Path
from typing import Any

from learnloop.clock import Clock, utc_now_iso
from learnloop.content.facet_identity.views import union_payload
from learnloop.curriculum.curriculum_locks import Operation, can_apply
from learnloop.db.repositories import Repository
from learnloop.db.stores import facet_identity as store
from learnloop.ids import new_ulid
from learnloop.substrate.replay import record_content_recalibration
from learnloop.substrate.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault
from learnloop.vault.models import EvidenceFacet, LoadedVault, learning_object_facet_union
from learnloop.vault.paths import VaultPaths
from learnloop.vault.facet_fingerprint import semantic_fingerprint
from learnloop.vault.yaml_io import read_yaml, write_yaml

class FacetIdentityActionError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


# --- the ledger ---------------------------------------------------------------


def insert_action(connection: Any, record: Mapping[str, Any]) -> str:
    return store.insert_action(connection, {**dict(record), "id": record.get("id") or new_ulid()},
                               created_at=utc_now_iso())


def action_by_id(repository: Repository, action_id: str) -> dict[str, Any] | None:
    with repository.connection() as connection:
        return store.action_by_id(connection, action_id)


def list_actions(
    repository: Repository, *, run_id: str | None = None, status: str | None = None, limit: int | None = 200,
) -> list[dict[str, Any]]:
    with repository.connection() as connection:
        return store.list_actions(connection, run_id=run_id, status=status, limit=limit)


# --- facets.yaml ----------------------------------------------------------------


def normalized_entry(entry: Mapping[str, Any] | None) -> dict[str, Any] | None:
    """An entry as ``facets.yaml`` stores it, minus the recomputed fingerprint."""

    if entry is None:
        return None
    dumped = EvidenceFacet.model_validate(dict(entry)).model_dump(mode="json", exclude_none=False)
    dumped.pop("semantic_fingerprint", None)
    return dumped


def stored_entry(entry: Mapping[str, Any]) -> dict[str, Any]:
    """The entry to write: validated, with its deterministic fingerprint."""

    validated = EvidenceFacet.model_validate(dict(entry))
    dumped = validated.model_dump(mode="json", exclude_none=False)
    dumped["semantic_fingerprint"] = semantic_fingerprint(validated)
    return dumped


def _facets_document(paths: VaultPaths) -> dict[str, Any]:
    data = read_yaml(paths.facets_path) if paths.facets_path.exists() else {}
    if not isinstance(data, dict):
        raise FacetIdentityActionError("invalid_registry", "facets.yaml must contain a mapping")
    data.setdefault("schema_version", 2)
    facets = data.setdefault("facets", [])
    if not isinstance(facets, list):
        raise FacetIdentityActionError("invalid_registry", "facets.yaml must contain a facets list")
    return data


def _index(facets: Sequence[Any], facet_id: str) -> int | None:
    for index, entry in enumerate(facets):
        if isinstance(entry, Mapping) and str(entry.get("id") or "") == facet_id:
            return index
    return None


# --- locks and affected learning objects ---------------------------------------------


def lock_reasons(vault: LoadedVault, repository: Repository, facet_ids: Iterable[str]) -> dict[str, list[dict[str, str]]]:
    out: dict[str, list[dict[str, str]]] = {}
    for facet_id in sorted(set(facet_ids)):
        if facet_id not in vault.evidence_facets:
            continue
        result = can_apply(vault, repository, Operation(
            op_type="facet_merge", entity_type="facet", entity_id=facet_id, facet_ids=(facet_id,),
        ))
        if not result.legal:
            out[facet_id] = [
                {"source": reason.source, "entity_type": reason.entity_type,
                 "entity_id": reason.entity_id, "detail": reason.detail}
                for reason in result.lock_reasons
            ]
    return out


def affected_learning_objects(vault: LoadedVault, facet_ids: Iterable[str]) -> list[str]:
    wanted = {vault.canonical_facet_id(facet_id) for facet_id in facet_ids} | set(facet_ids)
    affected: set[str] = set()
    for lo in vault.learning_objects.values():
        if wanted & set(learning_object_facet_union(lo)):
            affected.add(lo.id)
    for item in vault.practice_items.values():
        if wanted & set(item.evidence_facets):
            affected.add(item.learning_object_id)
    return sorted(affected)


def refresh_derived_state(root: Path, repository: Repository, affected: Iterable[str], *, clock: Clock | None = None) -> None:
    """Re-sync and re-fold the affected learning objects (evidence re-keyed)."""

    vault_after = load_vault(root)
    sync_vault_state(vault_after, repository, clock=clock)
    record_content_recalibration(
        vault_after, repository, affected_learning_object_ids=sorted(set(affected)), clock=clock,
    )


# --- vault scope: merge registered facets ---------------------------------------------


def merge_registered_facets(
    root: Path,
    repository: Repository,
    *,
    survivor: str,
    retired: Sequence[str],
    action: str,
    absorb_as: str | None,
    origin: str,
    run_id: str,
    judge: str,
    judge_model: str | None,
    prompt_version: str | None,
    judgment_ids: Sequence[str] = (),
    detail: Mapping[str, Any] | None = None,
    merge_locked: bool | None = None,
    clock: Clock | None = None,
) -> dict[str, Any]:
    """Merge or absorb registered facets into ``survivor``, live, with an undo record.

    Returns ``{"status": "applied" | "refused", ...}``. A refusal (an unknown
    or already-aliased facet, a locked facet under the strict policy, or a
    ``facet_merges`` conflict) writes nothing.
    """

    from learnloop.vault_lock import vault_mutation_lock

    retired = [facet_id for facet_id in dict.fromkeys(retired) if facet_id != survivor]
    if not retired:
        return {"status": "refused", "reason": "nothing_to_merge"}
    with vault_mutation_lock(root, purpose="facet_identity_merge"):
        vault = load_vault(root)
        paths = VaultPaths(vault.root, vault.config)
        unknown = [facet_id for facet_id in (survivor, *retired) if facet_id not in vault.evidence_facets]
        if unknown:
            return {"status": "refused", "reason": "unknown_facet", "facet_ids": unknown}
        locks = lock_reasons(vault, repository, (survivor, *retired))
        policy = vault.config.facet_identity.merge_locked_facets if merge_locked is None else merge_locked
        if locks and not policy:
            return {"status": "refused", "reason": "identity_locked", "lock_reasons": locks}
        merge_map = repository.facet_merge_map()
        already = [facet_id for facet_id in retired if facet_id in merge_map]
        if already:
            return {"status": "refused", "reason": "already_merged", "facet_ids": already}
        affected_before = affected_learning_objects(vault, (survivor, *retired))

        document = _facets_document(paths)
        facets = document["facets"]
        before: dict[str, Any] = {}
        order: dict[str, int] = {}
        for facet_id in (survivor, *retired):
            index = _index(facets, facet_id)
            if index is None:
                return {"status": "refused", "reason": "not_in_registry_file", "facet_ids": [facet_id]}
            before[facet_id] = copy.deepcopy(facets[index])
            order[facet_id] = index
        new_survivor = stored_entry(union_payload(
            before[survivor], [before[facet_id] for facet_id in retired],
            action=action, absorb_as=absorb_as, alias_ids=retired,
        ))
        facets[order[survivor]] = new_survivor
        document["facets"] = [entry for entry in facets
                              if not (isinstance(entry, Mapping) and str(entry.get("id") or "") in set(retired))]
        original_facets_text = paths.facets_path.read_text(encoding="utf-8")
        write_yaml(paths.facets_path, document)

        now = utc_now_iso(clock)
        inserted: list[list[str]] = []
        try:
            for facet_id in retired:
                repository.insert_facet_merge(
                    retired_facet_id=facet_id, surviving_facet_id=survivor,
                    rationale=json.dumps({"origin": "facet_identity", "run_id": run_id, "action": action}, sort_keys=True),
                    clock=clock,
                )
                inserted.append([facet_id, survivor])
            record = {
                "origin": origin, "scope": "vault", "run_id": run_id, "action": action,
                "survivor_facet_id": survivor, "retired_facet_ids": retired,
                "before": {"facets": before, "order": order},
                "after": {"facets": {survivor: new_survivor, **{facet_id: None for facet_id in retired}}},
                "merge_rows": inserted, "judgment_ids": list(judgment_ids), "judge": judge,
                "judge_model": judge_model, "prompt_version": prompt_version,
                "detail": {**dict(detail or {}), "absorb_as": absorb_as, "lock_reasons": locks},
                "status": "applied", "applied_at": now, "created_at": now,
            }
            with repository.atomic():
                action_id = insert_action(repository.connection(), record)
        except Exception:
            # Compensate: nothing half-applied survives a failure here.
            _delete_merge_rows(repository, inserted)
            paths.facets_path.write_text(original_facets_text, encoding="utf-8")
            raise
        refresh_derived_state(vault.root, repository, affected_before, clock=clock)
    return {
        "status": "applied", "action_id": action_id, "action": action, "survivor_facet_id": survivor,
        "retired_facet_ids": retired, "absorb_as": absorb_as,
        "locked": bool(locks), "lock_reasons": locks, "affected_learning_objects": affected_before,
    }


def _delete_merge_rows(repository: Repository, rows: Iterable[Sequence[str]]) -> int:
    with repository.atomic():
        return store.delete_merge_rows(repository.connection(), rows)


# --- ingest scopes: record proposed actions --------------------------------------------


def record_proposed_actions(
    repository: Repository, actions: Sequence[Mapping[str, Any]], *, origin: str, run_id: str,
    proposal_id: str | None, clock: Clock | None = None,
) -> list[str]:
    """Persist a run's in-run and attach actions with the proposal that carries them."""

    if not actions:
        return []
    now = utc_now_iso(clock)
    ids: list[str] = []
    with repository.atomic():
        connection = repository.connection()
        for action in actions:
            ids.append(insert_action(connection, {
                **dict(action), "origin": origin, "run_id": run_id, "proposal_id": proposal_id,
                "status": "proposed", "created_at": now,
            }))
    return ids


def _current_entries(paths: VaultPaths) -> dict[str, Any]:
    document = _facets_document(paths)
    return {str(entry.get("id")): entry for entry in document["facets"] if isinstance(entry, Mapping)}


def effective_status(record: Mapping[str, Any], vault: LoadedVault) -> str:
    """``proposed`` until the vault shows what the action wrote, then ``applied``."""

    if record["status"] != "proposed":
        return str(record["status"])
    paths = VaultPaths(vault.root, vault.config)
    try:
        current = _current_entries(paths)
    except FacetIdentityActionError:
        return "proposed"
    survivor = str(record["survivor_facet_id"])
    after = ((record.get("after") or {}).get("facets") or {}).get(survivor)
    entry = current.get(survivor)
    if entry is None or after is None:
        return "proposed"
    aliases = set(entry.get("aliases") or [])
    retired = set(record.get("retired_facet_ids") or [])
    return "applied" if retired <= aliases and not (retired & set(current)) else "proposed"


def describe(record: Mapping[str, Any], vault: LoadedVault | None = None) -> dict[str, Any]:
    """A compact view for results, the CLI and the desktop app."""

    before = (record.get("before") or {}).get("facets") or {}

    def claim(facet_id: str) -> str:
        entry = before.get(facet_id) or {}
        if not entry and vault is not None and facet_id in vault.evidence_facets:
            entry = vault.evidence_facets[facet_id].model_dump(mode="json")
        return str(entry.get("claim") or entry.get("title") or facet_id)

    detail = record.get("detail") or {}
    status = effective_status(record, vault) if vault is not None else record["status"]
    return {
        "id": record["id"],
        "origin": record["origin"],
        "scope": record["scope"],
        "run_id": record["run_id"],
        "proposal_id": record.get("proposal_id"),
        "action": record["action"],
        "absorb_as": detail.get("absorb_as"),
        "survivor": {"id": record["survivor_facet_id"], "claim": claim(record["survivor_facet_id"])},
        "retired": [{"id": facet_id, "claim": claim(facet_id)} for facet_id in record.get("retired_facet_ids") or []],
        "rationale": detail.get("rationale") or "",
        "locked": bool(detail.get("lock_reasons")),
        "judge": record["judge"],
        "judge_model": record.get("judge_model"),
        "status": status,
        "undoable": status == "applied",
        "created_at": record["created_at"],
        "undone_at": record.get("undone_at"),
    }


# --- undo ----------------------------------------------------------------------------------


def _later_actions(repository: Repository, record: Mapping[str, Any]) -> list[str]:
    facets = {record["survivor_facet_id"], *(record.get("retired_facet_ids") or [])}
    later = []
    for other in list_actions(repository, limit=None):
        if other["id"] == record["id"] or other["status"] == "undone" or other["created_at"] < record["created_at"]:
            continue
        if facets & {other["survivor_facet_id"], *(other.get("retired_facet_ids") or [])}:
            later.append(other["id"])
    return later


def undo_action(root: Path, repository: Repository, action_id: str, *, clock: Clock | None = None) -> dict[str, Any]:
    """Restore the facets.yaml entries and ``facet_merges`` rows one action replaced.

    Refuses (writing nothing) when the action is unknown, already undone, not
    applied yet, or when the survivor's entry has changed since.
    """

    from learnloop.vault_lock import vault_mutation_lock

    with vault_mutation_lock(root, purpose="facet_identity_undo"):
        record = action_by_id(repository, action_id)
        if record is None:
            raise FacetIdentityActionError("unknown_action", f"No facet identity action {action_id!r}.")
        if record["status"] == "undone":
            raise FacetIdentityActionError("already_undone", f"Action {action_id} was already undone.")
        vault = load_vault(root)
        status = effective_status(record, vault)
        if status == "proposed":
            raise FacetIdentityActionError(
                "not_applied",
                f"Action {action_id} is part of proposal {record.get('proposal_id') or '(unknown)'}, which has "
                "not been applied; it takes effect only when that proposal is applied.",
            )
        paths = VaultPaths(vault.root, vault.config)
        document = _facets_document(paths)
        facets = document["facets"]
        survivor = str(record["survivor_facet_id"])
        retired = [str(facet_id) for facet_id in record.get("retired_facet_ids") or []]
        before = (record.get("before") or {}).get("facets") or {}
        order = (record.get("before") or {}).get("order") or {}
        after = (record.get("after") or {}).get("facets") or {}

        index = _index(facets, survivor)
        if index is None or normalized_entry(facets[index]) != normalized_entry(after.get(survivor)):
            later = _later_actions(repository, record)
            raise FacetIdentityActionError(
                "changed_since",
                f"Facet {survivor} changed after action {action_id}"
                + (f" (later action(s): {', '.join(later)}; undo those first)." if later else " (edited since)."),
            )
        present = [facet_id for facet_id in retired if _index(facets, facet_id) is not None]
        if present:
            raise FacetIdentityActionError(
                "changed_since", f"Facet(s) {', '.join(present)} exist again; nothing to restore.",
            )
        affected_before = affected_learning_objects(vault, (survivor, *retired))

        facets[index] = stored_entry(before[survivor]) if before.get(survivor) else facets[index]
        for facet_id in sorted(retired, key=lambda key: int(order.get(key, len(facets) + 1))):
            entry = before.get(facet_id)
            if not entry:
                continue
            position = order.get(facet_id)
            restored = stored_entry(entry)
            if isinstance(position, int) and 0 <= position <= len(facets):
                facets.insert(position, restored)
            else:
                survivor_at = _index(facets, survivor)
                facets.insert((survivor_at + 1) if survivor_at is not None else len(facets), restored)
        original_facets_text = paths.facets_path.read_text(encoding="utf-8")
        try:
            write_yaml(paths.facets_path, document)
            deleted = _delete_merge_rows(repository, record.get("merge_rows") or [])
            now = utc_now_iso(clock)
            with repository.atomic():
                store.mark_undone(repository.connection(), action_id, undone_at=now,
                                  detail={"merge_rows_deleted": deleted, "restored_facet_ids": retired})
        except Exception:
            paths.facets_path.write_text(original_facets_text, encoding="utf-8")
            raise
        refresh_derived_state(vault.root, repository, affected_before, clock=clock)
    return {
        "status": "undone", "action_id": action_id, "survivor_facet_id": survivor,
        "restored_facet_ids": retired, "merge_rows_deleted": deleted,
        "affected_learning_objects": affected_before,
    }


__all__ = [
    "FacetIdentityActionError",
    "action_by_id",
    "affected_learning_objects",
    "describe",
    "effective_status",
    "insert_action",
    "list_actions",
    "lock_reasons",
    "merge_registered_facets",
    "normalized_entry",
    "record_proposed_actions",
    "refresh_derived_state",
    "stored_entry",
    "undo_action",
]

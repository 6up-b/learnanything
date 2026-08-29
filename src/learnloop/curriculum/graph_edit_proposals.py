"""User-authored graph/knowledge-map edits (graph editor, spec §8/§12).

Every learner edit to the three graphs compiles to proposal items in the
EXISTING proposals machinery — no handler writes vault YAML directly (design
non-negotiable 1). Representable edits (concept / concept_edge / learning_object)
run through the identical Codex-authoring validation/persistence seam
(``proposals.proposal_item_row``); ``task_blueprint`` — which has no
``AuthoringProposalItem`` payload model — is persisted the same way synthesis
persists it, as a directly-built row. Items land pending in the inbox; the
review/apply flow is unchanged.

Also owns two review surfaces layered on the same seam: ``queue_restructure_request``
(durable intent for LOCKED facets, spec §17 machinery does not exist yet) and
``resolve_edge_direction`` (compiles a ``concept_edge`` proposal via the same
service and resolves the ``ambiguous_edge_direction`` maintenance notice).
"""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Any

from learnloop.clock import Clock, utc_now_iso
from learnloop.content.proposals.ai_contracts import AuthoringProposal, AuthoringProposalItem
from learnloop.db.repositories import Repository
from learnloop.ids import new_ulid
from learnloop.curriculum.curriculum_locks import Operation, can_apply
from learnloop.content.proposals.patches import compute_target_hash
from learnloop.content.proposals.proposals import auto_apply_rows, proposal_item_row
from learnloop.vault.loader import load_vault
from learnloop.vault.models import LoadedVault
from learnloop.vault.paths import VaultPaths

# Item types the graph editor can edit (design "Write path"). ``concept_edge`` /
# ``learning_object`` / ``concept`` compile to AuthoringProposalItems; the
# learnable-map ``task_blueprint`` type has no authoring payload model and is
# persisted as a raw row (the synthesis convention).
_GRAPH_EDIT_ITEM_TYPES = frozenset({"concept_edge", "learning_object", "concept", "task_blueprint"})
_AUTHORING_ITEM_TYPES = frozenset({"concept_edge", "learning_object", "concept"})
_EDIT_OPERATIONS = frozenset({"create", "update", "delete"})
# The graph editor's "delete" maps onto the proposal vocabulary's "deactivate"
# (AuthoringProposalItem has no "delete" operation).
_OPERATION_MAP = {"create": "create", "update": "update", "delete": "deactivate"}

_GRAPH_EDITOR_PURPOSE = "graph_editor"
_GRAPH_EDITOR_PROVIDER = "user"

_EDGE_RESOLUTIONS = frozenset({"keep", "flip", "retype_related", "retire"})

AMBIGUOUS_EDGE_DIRECTION_NOTICE = "ambiguous_edge_direction"
RESTRUCTURE_REQUEST_NOTICE = "restructure_request"
RESTRUCTURE_REQUEST_NEED_KIND = "restructure_request"


class GraphEditError(ValueError):
    """A user graph-edit request that cannot be compiled (maps to a SidecarError)."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


# --- propose_graph_edits ----------------------------------------------------


def propose_graph_edits(
    root: Path,
    rationale: str,
    edits: list[dict[str, Any]],
    *,
    clock: Clock | None = None,
) -> dict[str, Any]:
    """Compile a batch of user graph edits into ONE pending proposal batch.

    Provider ``user``, purpose ``graph_editor``, summary = ``rationale``; one
    proposal item per edit, validated identically to Codex-authored items.
    Returns ``{batch_id, items}``.
    """

    if not (rationale or "").strip():
        raise GraphEditError("invalid_request", "A non-empty rationale is required.")
    if not edits:
        raise GraphEditError("invalid_request", "At least one edit is required.")

    vault = load_vault(root)
    repository = Repository(VaultPaths(vault.root, vault.config).sqlite_path)
    batch_id, items = _persist_graph_edit_batch(
        root, vault, repository, rationale, edits, clock=clock
    )
    return {"batch_id": batch_id, "items": items}


def _persist_graph_edit_batch(
    root: Path,
    vault: LoadedVault,
    repository: Repository,
    rationale: str,
    edits: list[dict[str, Any]],
    *,
    clock: Clock | None,
) -> tuple[str, list[dict[str, Any]]]:
    now = utc_now_iso(clock)
    authoring_items: list[AuthoringProposalItem] = []
    authoring_index: list[int] = []
    raw_rows: list[dict[str, Any]] = []

    for index, edit in enumerate(edits):
        item_type = str(edit.get("item_type") or "")
        operation = str(edit.get("operation") or "")
        if item_type not in _GRAPH_EDIT_ITEM_TYPES:
            raise GraphEditError("invalid_request", f"Unsupported item_type '{item_type}'.")
        if operation not in _EDIT_OPERATIONS:
            raise GraphEditError("invalid_request", f"Unsupported operation '{operation}'.")
        # A concept "delete" maps to a deactivate that patches.py cannot forward-apply
        # (deleting a concept would leave referencing LOs/edges/goals dangling), so it
        # is refused at filing time rather than entering the inbox as a dead end.
        if item_type == "concept" and operation == "delete":
            raise GraphEditError(
                "unsupported_operation",
                "Deleting a concept is not supported: it may leave referencing learning "
                "objects, edges, or goals dangling. Retire its edges or reassign its "
                "learning objects first.",
            )
        if item_type in _AUTHORING_ITEM_TYPES:
            authoring_items.append(_authoring_item(edit, index, vault))
            authoring_index.append(index)
        else:
            raw_rows.append(_raw_row(edit, index, now))

    proposal = AuthoringProposal(summary=rationale, source_refs=[], items=authoring_items)
    authoring_rows: list[dict[str, Any]] = []
    for item in proposal.items:
        row = proposal_item_row(item, now, vault=vault, proposal=proposal, provider=_GRAPH_EDITOR_PROVIDER)
        _stamp_expected_target_hash(row, vault)
        authoring_rows.append(row)

    rows = authoring_rows + raw_rows
    agent_run_id = repository.insert_agent_run(
        {
            "id": new_ulid(),
            "purpose": _GRAPH_EDITOR_PURPOSE,
            "provider": _GRAPH_EDITOR_PROVIDER,
            "provider_type": _GRAPH_EDITOR_PROVIDER,
            "prompt_template": _GRAPH_EDITOR_PURPOSE,
            "started_at": now,
            "completed_at": now,
            "status": "completed",
        }
    )
    batch_id = repository.persist_proposal_batch(
        {
            "id": new_ulid(),
            "agent_run_id": agent_run_id,
            "purpose": _GRAPH_EDITOR_PURPOSE,
            "source_refs": [],
            "summary": rationale,
            "created_at": now,
            "updated_at": now,
        },
        rows,
    )
    # Mirrors the authoring flow: user edits carry no source refs, so the review
    # policy never routes them to auto_apply — this stays a no-op, but keeps the
    # seam identical rather than forking it.
    auto_apply_rows(root, batch_id, rows)
    return batch_id, [_item_dto(row) for row in rows]


def _authoring_item(edit: dict[str, Any], index: int, vault: LoadedVault) -> AuthoringProposalItem:
    item_type = str(edit["item_type"])
    operation = _OPERATION_MAP[str(edit["operation"])]
    payload = dict(edit.get("payload") or {})
    target_entity_id = edit.get("target_entity_id")

    if item_type == "concept_edge":
        # Accept both the on-disk ``source``/``target`` keys and the authoring
        # payload's ``source_concept_id``/``target_concept_id``.
        if "source" in payload and "source_concept_id" not in payload:
            payload["source_concept_id"] = payload.pop("source")
        if "target" in payload and "target_concept_id" not in payload:
            payload["target_concept_id"] = payload.pop("target")
        if operation == "deactivate":
            # Snapshot the live edge's fields into the payload so a rejected-after
            # apply deactivate can restore the edge exactly (mirrors the filing-time
            # ``expected_target_hash`` snapshot for other update/deactivate items).
            _snapshot_edge_for_deactivate(payload, target_entity_id, vault)

    data: dict[str, Any] = {
        "client_item_id": f"graph_edit_{index}_{new_ulid()}",
        "item_type": item_type,
        "operation": operation,
        "rationale": str(edit.get("rationale") or "user graph edit"),
        "review_route": "review_required",
        "payload": payload,
    }
    if operation in {"update", "deactivate"}:
        entity_id = target_entity_id or payload.get("id")
        if not entity_id:
            raise GraphEditError("invalid_request", f"{item_type} {edit['operation']} requires a target entity id.")
        data["target"] = {"entity_type": item_type, "entity_id": str(entity_id)}
    elif item_type != "concept_edge" and payload.get("id") is None and target_entity_id:
        data["proposed_entity_id"] = str(target_entity_id)

    try:
        return AuthoringProposalItem.model_validate(data)
    except Exception as exc:  # pydantic ValidationError -> typed graph-edit error
        raise GraphEditError("invalid_request", f"Invalid {item_type} edit payload: {exc}") from exc


def _snapshot_edge_for_deactivate(
    payload: dict[str, Any], target_entity_id: Any, vault: LoadedVault
) -> None:
    """Fill a concept_edge deactivate payload from the live edge.

    ``ConceptEdgePatchPayload`` requires source/target/relation_type, so a bare
    retire gesture (just a target id) would fail validation; this also captures
    strength/rationale so the revert restores the edge's prior fields."""

    edge_id = target_entity_id or payload.get("id")
    edge = next((candidate for candidate in vault.edges if candidate.id == edge_id), None) if edge_id else None
    if edge is None:
        return
    payload.setdefault("source_concept_id", edge.source)
    payload.setdefault("target_concept_id", edge.target)
    payload.setdefault("relation_type", edge.relation_type)
    if edge.strength is not None:
        payload.setdefault("strength", edge.strength)
    if edge.rationale is not None:
        payload.setdefault("rationale", edge.rationale)


def _raw_row(edit: dict[str, Any], index: int, now: str) -> dict[str, Any]:
    """A directly-built proposal row for a learnable-map type with no authoring
    payload model (``task_blueprint``) — persisted the way synthesis persists it."""

    operation = _OPERATION_MAP[str(edit["operation"])]
    payload = dict(edit.get("payload") or {})
    target_entity_id = edit.get("target_entity_id")
    if operation in {"update", "deactivate"} and payload.get("id") is None and target_entity_id:
        payload["id"] = str(target_entity_id)
    return {
        "id": new_ulid(),
        "client_item_id": f"graph_edit_{index}_{new_ulid()}",
        "item_type": str(edit["item_type"]),
        "operation": operation,
        "target_entity_type": str(edit["item_type"]) if operation in {"update", "deactivate"} else None,
        "target_entity_id": str(target_entity_id) if target_entity_id else None,
        "payload": payload,
        "source_ref_ids": [],
        "audit": None,
        "decision": "pending",
        "validation_status": "valid",
        "validation_errors": [],
        "created_at": now,
        "updated_at": now,
    }


def _stamp_expected_target_hash(row: dict[str, Any], vault: LoadedVault) -> None:
    """Stamp the §8.2 accept-time staleness hash on update/deactivate rows.

    Mirrors the synthesis/append flow so an edit whose target changed after the
    edit was filed is refused at accept time. ``compute_target_hash`` returns
    ``None`` for types it does not hash (e.g. ``concept_edge``), leaving no stamp.
    """

    if row["operation"] not in {"update", "deactivate"}:
        return
    payload = row.get("payload")
    if not isinstance(payload, dict) or payload.get("expected_target_hash") is not None:
        return
    entity_id = row.get("target_entity_id") or payload.get("id")
    if not entity_id:
        return
    current = compute_target_hash(vault, row["item_type"], str(entity_id))
    if current is not None:
        payload["expected_target_hash"] = current


def _item_dto(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": row["id"],
        "client_item_id": row.get("client_item_id"),
        "item_type": row["item_type"],
        "operation": row["operation"],
        "decision": row.get("decision", "pending"),
        "validation_status": row.get("validation_status", "valid"),
        "validation_errors": row.get("validation_errors") or [],
        "target_entity_id": row.get("target_entity_id"),
    }


# --- queue_restructure_request ----------------------------------------------


def queue_restructure_request(
    root: Path,
    facet_ids: list[str],
    requested_operation: str,
    rationale: str,
    *,
    clock: Clock | None = None,
) -> dict[str, Any]:
    """Queue a durable restructure-intent record for LOCKED facets (spec §17).

    The §17 restructure-with-history machinery does not exist yet, so this only
    records intent — reusing the generation-needs queue with kind
    ``restructure_request`` (the closest existing durable queue) and surfacing it
    in the maintenance feed. At least one named facet must actually be locked;
    otherwise the normal merge/split flow (``propose_facet_merge``) applies.
    """

    if requested_operation not in {"merge", "split"}:
        raise GraphEditError("invalid_request", "requested_operation must be 'merge' or 'split'.")
    if not facet_ids:
        raise GraphEditError("invalid_request", "At least one facet id is required.")

    vault = load_vault(root)
    repository = Repository(VaultPaths(vault.root, vault.config).sqlite_path)

    canonical = [vault.canonical_facet_id(str(facet)) for facet in facet_ids]
    for facet_id in canonical:
        if facet_id not in vault.evidence_facets:
            raise GraphEditError("facet_not_found", f"Facet '{facet_id}' does not exist.")

    op_type = f"facet_{requested_operation}"
    locked = [
        facet_id
        for facet_id in canonical
        if not can_apply(
            vault,
            repository,
            Operation(op_type=op_type, entity_type="facet", entity_id=facet_id, facet_ids=(facet_id,)),
        ).legal
    ]
    if not locked:
        raise GraphEditError(
            "facets_not_locked",
            "None of the named facets are locked; use the normal merge/split flow "
            "(propose_facet_merge) instead of queueing a restructure request.",
        )

    subject_id = _subject_for_facets(vault, canonical)
    target_key = f"{requested_operation}:{','.join(sorted(canonical))}"
    need_id = repository.upsert_synthesis_generation_need(
        subject_id=subject_id,
        need_kind=RESTRUCTURE_REQUEST_NEED_KIND,
        target_key=target_key,
        missing_capability=requested_operation,
        facet_ids=canonical,
        detail=rationale,
        clock=clock,
    )
    return {
        "need_id": need_id,
        "subject_id": subject_id,
        "facet_ids": canonical,
        "locked_facet_ids": locked,
        "requested_operation": requested_operation,
        "rationale": rationale,
        "status": "pending",
    }


def _subject_for_facets(vault: LoadedVault, facet_ids: list[str]) -> str:
    facet_set = set(facet_ids)
    for item in vault.practice_items.values():
        if any(vault.canonical_facet_id(str(facet)) in facet_set for facet in item.evidence_facets):
            subjects = vault.subjects_for_item(item)
            if subjects:
                return subjects[0]
    return sorted(vault.subjects)[0] if vault.subjects else "unknown"


# --- resolve_edge_direction -------------------------------------------------


def resolve_edge_direction(
    root: Path,
    edge_id: str,
    resolution: str,
    rationale: str,
    *,
    clock: Clock | None = None,
) -> dict[str, Any]:
    """Resolve an ``ambiguous_edge_direction`` notice into a concept_edge edit.

    ``keep`` files no edit (just resolves the notice); ``flip`` swaps
    source/target; ``retype_related`` retypes the relation to ``related``;
    ``retire`` deactivates the edge — compiled through the SAME service as
    ``propose_graph_edits``. The corresponding maintenance notice is resolved.
    """

    if resolution not in _EDGE_RESOLUTIONS:
        raise GraphEditError("invalid_request", f"Unsupported resolution '{resolution}'.")

    vault = load_vault(root)
    repository = Repository(VaultPaths(vault.root, vault.config).sqlite_path)
    edge = next((candidate for candidate in vault.edges if candidate.id == edge_id), None)

    batch_id: str | None = None
    items: list[dict[str, Any]] = []
    if resolution != "keep":
        if edge is None:
            raise GraphEditError("edge_not_found", f"Concept edge '{edge_id}' does not exist.")
        edit = _edge_resolution_edit(edge, resolution)
        batch_id, items = _persist_graph_edit_batch(
            root, vault, repository, rationale, [edit], clock=clock
        )

    resolved_notice_ids = _resolve_edge_direction_notices(repository, edge_id, clock=clock)
    return {
        "edge_id": edge_id,
        "resolution": resolution,
        "batch_id": batch_id,
        "filed_edit": batch_id is not None,
        "items": items,
        "resolved_notice_ids": resolved_notice_ids,
    }


def _edge_resolution_edit(edge: Any, resolution: str) -> dict[str, Any]:
    if resolution == "flip":
        payload = {
            "source_concept_id": edge.target,
            "target_concept_id": edge.source,
            "relation_type": edge.relation_type,
        }
        return {"item_type": "concept_edge", "operation": "update", "target_entity_id": edge.id, "payload": payload}
    if resolution == "retype_related":
        payload = {
            "source_concept_id": edge.source,
            "target_concept_id": edge.target,
            "relation_type": "related",
        }
        return {"item_type": "concept_edge", "operation": "update", "target_entity_id": edge.id, "payload": payload}
    # retire
    payload = {
        "source_concept_id": edge.source,
        "target_concept_id": edge.target,
        "relation_type": edge.relation_type,
    }
    return {"item_type": "concept_edge", "operation": "delete", "target_entity_id": edge.id, "payload": payload}


def _resolve_edge_direction_notices(
    repository: Repository, edge_id: str, *, clock: Clock | None
) -> list[str]:
    resolved: list[str] = []
    for notice in repository.maintenance_notices(include_hidden=True):
        if notice["notice_type"] != AMBIGUOUS_EDGE_DIRECTION_NOTICE:
            continue
        if notice.get("entity_id") != edge_id and notice.get("dedup_key") != edge_id:
            continue
        if notice.get("status") in {"resolved", "dismissed", "expired"}:
            continue
        repository.set_maintenance_notice_status(notice["id"], status="resolved", clock=clock)
        resolved.append(notice["id"])
    return resolved


# --- ambiguous_edge_direction notices (called by maintenance_feed) ----------


def ambiguous_edge_direction_notices(vault: LoadedVault, repository: Repository) -> list[dict[str, Any]]:
    """Deterministic ambiguous-direction notices (design "Write path" heuristics).

    (a) prerequisite edges on a cycle, (b) A->B & B->A prerequisite pairs (a
    2-cycle), (c) pending (``proposed``) prerequisite concept_edge proposal items.
    Each notice carries both concept titles, the edge provenance/rationale, and
    attempt-ordering evidence (sparse data -> evidence omitted, not fabricated).
    """

    notices: list[dict[str, Any]] = []
    prereq = [edge for edge in vault.edges if edge.relation_type == "prerequisite"]
    adjacency: dict[str, set[str]] = defaultdict(set)
    pairs: set[tuple[str, str]] = set()
    for edge in prereq:
        adjacency[edge.source].add(edge.target)
        pairs.add((edge.source, edge.target))

    for edge in prereq:
        reverse = (edge.target, edge.source) in pairs
        if reverse:
            reason = "bidirectional"
        elif _reachable(adjacency, edge.target, edge.source):
            reason = "cycle"
        else:
            continue
        notices.append(
            _edge_notice(
                vault,
                repository,
                dedup_key=edge.id,
                entity_id=edge.id,
                edge_id=edge.id,
                source=edge.source,
                target=edge.target,
                relation_type=edge.relation_type,
                rationale=edge.rationale,
                reason=reason,
            )
        )

    for item in _pending_prerequisite_edge_items(repository):
        payload = item.get("payload") or {}
        source = payload.get("source") or payload.get("source_concept_id")
        target = payload.get("target") or payload.get("target_concept_id")
        if not source or not target:
            continue
        notices.append(
            _edge_notice(
                vault,
                repository,
                dedup_key=f"proposed:{item['id']}",
                entity_id=None,
                edge_id=payload.get("id"),
                source=str(source),
                target=str(target),
                relation_type="prerequisite",
                rationale=payload.get("rationale"),
                reason="proposed",
                proposal_item_id=item["id"],
            )
        )
    return notices


def _edge_notice(
    vault: LoadedVault,
    repository: Repository,
    *,
    dedup_key: str,
    entity_id: str | None,
    edge_id: str | None,
    source: str,
    target: str,
    relation_type: str,
    rationale: str | None,
    reason: str,
    proposal_item_id: str | None = None,
) -> dict[str, Any]:
    source_title = _concept_title(vault, source)
    target_title = _concept_title(vault, target)
    detail = {
        "edge_id": edge_id,
        "reason": reason,
        "relation_type": relation_type,
        "source_concept": {"id": source, "title": source_title},
        "target_concept": {"id": target, "title": target_title},
        "rationale": rationale,
        "evidence": _direction_evidence(vault, repository, source, target),
        "resolution_options": ["keep", "flip", "retype_related", "retire"],
        "proposal_item_id": proposal_item_id,
    }
    return {
        "notice_type": AMBIGUOUS_EDGE_DIRECTION_NOTICE,
        "dedup_key": dedup_key,
        "title": f"Ambiguous prerequisite direction: {source_title} -> {target_title}",
        "action": {
            "action": "resolve_edge_direction",
            "label": "Resolve direction",
            "edge_id": edge_id,
        },
        "entity_type": "concept_edge",
        "entity_id": entity_id,
        "detail": detail,
    }


def _direction_evidence(
    vault: LoadedVault, repository: Repository, source_concept: str, target_concept: str
) -> dict[str, Any] | None:
    """Success on the target's items before vs after the first correct attempt on
    any source item. Sparse data -> ``None`` (omit rather than fabricate)."""

    source_items = _items_for_concept(vault, source_concept)
    target_items = _items_for_concept(vault, target_concept)
    if not source_items or not target_items:
        return None
    source_outcomes = repository.practice_attempt_outcomes_for_items(source_items)
    first_correct_at = next((o["created_at"] for o in source_outcomes if _is_correct(o)), None)
    if first_correct_at is None:
        return None
    target_outcomes = repository.practice_attempt_outcomes_for_items(target_items)
    before = [o for o in target_outcomes if str(o["created_at"]) < str(first_correct_at)]
    after = [o for o in target_outcomes if str(o["created_at"]) >= str(first_correct_at)]
    if not before or not after:
        return None

    def _rate(bucket: list[dict[str, Any]]) -> float:
        return round(sum(1 for o in bucket if _is_correct(o)) / len(bucket), 3)

    return {
        "first_correct_source_at": first_correct_at,
        "target_success_before": _rate(before),
        "target_success_after": _rate(after),
        "target_attempts_before": len(before),
        "target_attempts_after": len(after),
    }


def _items_for_concept(vault: LoadedVault, concept_id: str) -> list[str]:
    return sorted(
        item.id
        for item in vault.practice_items.values()
        if (lo := vault.learning_objects.get(item.learning_object_id)) is not None
        and lo.concept == concept_id
    )


def _is_correct(outcome: dict[str, Any]) -> bool:
    correctness = outcome.get("correctness")
    if correctness is not None:
        return float(correctness) >= 0.6
    rubric_score = outcome.get("rubric_score")
    return rubric_score is not None and float(rubric_score) >= 3.0


def _concept_title(vault: LoadedVault, concept_id: str) -> str:
    concept = vault.concepts.get(concept_id)
    return concept.title if concept is not None else concept_id


def _reachable(adjacency: dict[str, set[str]], start: str, goal: str) -> bool:
    stack = [start]
    seen: set[str] = set()
    while stack:
        node = stack.pop()
        if node == goal:
            return True
        if node in seen:
            continue
        seen.add(node)
        stack.extend(adjacency.get(node, ()))
    return False


def _pending_prerequisite_edge_items(repository: Repository) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for batch in repository.proposal_batches():
        for item in repository.proposal_items(batch["id"]):
            if item.get("item_type") != "concept_edge" or item.get("decision") != "pending":
                continue
            if item.get("operation") not in {"create", "update"}:
                continue
            payload = item.get("edited_payload") if item.get("edited_payload") is not None else item.get("payload")
            if not isinstance(payload, dict) or payload.get("relation_type") != "prerequisite":
                continue
            out.append({"id": item["id"], "payload": payload})
    return out


def restructure_request_notices(vault: LoadedVault, repository: Repository) -> list[dict[str, Any]]:
    """Surface queued restructure-intent records in the maintenance feed (§17)."""

    notices: list[dict[str, Any]] = []
    for need in repository.synthesis_generation_needs(
        need_kind=RESTRUCTURE_REQUEST_NEED_KIND, status="pending"
    ):
        facet_ids = need.get("facet_ids") or []
        operation = need.get("missing_capability") or "merge"
        notices.append(
            {
                "notice_type": RESTRUCTURE_REQUEST_NOTICE,
                "dedup_key": need["id"],
                "title": f"Restructure request ({operation}) queued for {len(facet_ids)} locked facet(s)",
                "action": {
                    "action": "review_restructure_request",
                    "label": "Review restructure request",
                    "need_id": need["id"],
                },
                "subject_id": need.get("subject_id"),
                "entity_type": "facet",
                "entity_id": facet_ids[0] if facet_ids else None,
                "detail": {
                    "facet_ids": facet_ids,
                    "operation": operation,
                    "rationale": need.get("detail"),
                },
            }
        )
    return notices

"""Compose a real, registrable golden-path blueprint draft from vault items.

The P2 spec deferred the library exemplar picker; this closes it. Discovery
lists each learning object's active practice items (the natural exemplar pool
on a fresh vault -- the golden-path fixture itself uses practice items as
exemplar refs). The owner picks familiar anchors + one unseen sibling; the
composer projects them into a §3.2 blueprint spec plus the matching §1.2 goal
contract body using conservative template defaults (single conjunctive recipe,
default administration conditions, empty depth edges). The template is a
DRAFT: it goes through the existing register -> owner-review -> confirm chain
unchanged, so nothing here bypasses review.
"""

from __future__ import annotations

from typing import Any, Mapping, Sequence

from learnloop.clock import Clock
from learnloop.db.repositories import Repository
from learnloop.vault.models import LoadedVault, PracticeItem

DEFAULT_ADMINISTRATION = {"tools": "none", "open_book": False, "time_minutes": 15}


class ComposeError(ValueError):
    """The picker selection cannot compose into a valid single-unit blueprint."""


def discover_exemplar_pool(
    vault: LoadedVault,
    repository: Repository,
    *,
    learning_object_id: str | None = None,
) -> list[dict[str, Any]]:
    """The picker data: learning objects with their active items and freshness.

    ``attempted`` matters because the held-out sibling should be UNSEEN --
    confirmation independently enforces reservability, but the picker should
    steer the choice before that."""

    states = repository.practice_item_states()
    pool: dict[str, dict[str, Any]] = {}
    for item in vault.practice_items.values():
        if item.status != "active":
            continue
        if learning_object_id is not None and item.learning_object_id != learning_object_id:
            continue
        lo = vault.learning_objects.get(item.learning_object_id)
        entry = pool.setdefault(
            item.learning_object_id,
            {
                "learning_object_id": item.learning_object_id,
                "title": getattr(lo, "title", None) or item.learning_object_id,
                "items": [],
            },
        )
        state = states.get(item.id)
        entry["items"].append(
            {
                "practice_item_id": item.id,
                "prompt": item.prompt,
                "practice_mode": item.practice_mode,
                "evidence_facets": list(item.evidence_facets),
                "attempted": bool(state and state.last_attempt_at),
            }
        )
    out = sorted(pool.values(), key=lambda e: e["learning_object_id"])
    for entry in out:
        entry["items"].sort(key=lambda i: (i["attempted"], i["practice_item_id"]))
    return out


def compose_blueprint_draft(
    vault: LoadedVault,
    repository: Repository,
    *,
    learning_object_id: str,
    anchor_item_ids: Sequence[str],
    held_out_item_id: str,
    title: str | None = None,
    source_rev: str | None = None,
    unit_id: str | None = None,
    family_key: str | None = None,
    clock: Clock | None = None,
) -> dict[str, Any]:
    """Project a picker selection into ``{spec, contract_body, ...}`` ready for
    ``register_blueprint_version`` + ``confirm_exemplar_and_start``."""

    lo = vault.learning_objects.get(learning_object_id)
    if lo is None:
        raise ComposeError(f"unknown learning object {learning_object_id!r}")
    if not anchor_item_ids:
        raise ComposeError("pick at least one familiar-anchor exemplar")
    if held_out_item_id in set(anchor_item_ids):
        raise ComposeError("the held-out sibling cannot also be a selected exemplar")

    def _item(item_id: str) -> PracticeItem:
        item = vault.practice_items.get(item_id)
        if item is None:
            raise ComposeError(f"unknown practice item {item_id!r}")
        if item.status != "active":
            raise ComposeError(f"item {item_id!r} is retired")
        if item.learning_object_id != learning_object_id:
            raise ComposeError(
                f"item {item_id!r} is on {item.learning_object_id!r}, not "
                f"{learning_object_id!r} (mixed-unit)"
            )
        return item

    anchors = [_item(i) for i in anchor_item_ids]
    held_out = _item(held_out_item_id)

    warnings: list[str] = []
    state = repository.practice_item_states().get(held_out.id)
    if state is not None and state.last_attempt_at:
        warnings.append(
            f"held-out item {held_out.id} has prior attempts -- it is not an unseen "
            "sibling; confirmation may refuse the fresh reservation"
        )

    resolved_unit = unit_id or f"lo:{learning_object_id}"
    resolved_rev = source_rev or f"vault:{learning_object_id}"
    resolved_family = family_key or f"{learning_object_id}:{anchors[0].practice_mode}"
    facets = sorted({f for item in [*anchors, held_out] for f in item.evidence_facets})
    primary_facet = facets[0] if facets else f"{learning_object_id}:core"
    resolved_title = title or f"Master tasks like these ({getattr(lo, 'title', None) or learning_object_id})"

    exemplars: list[dict[str, Any]] = [
        {"exemplar_ref": item.id, "unit_id": resolved_unit, "family_key": resolved_family, "weight": 1.0}
        for item in anchors
    ]
    exemplars.append(
        {
            "exemplar_ref": held_out.id,
            "unit_id": resolved_unit,
            "family_key": resolved_family,
            "weight": 0.0,
            "held_out": True,
            "held_out_weight": 1.0,
        }
    )

    rubric = _rubric_for(anchors[0])
    spec: dict[str, Any] = {
        "source_rev": resolved_rev,
        "unit_id": resolved_unit,
        "family_key": resolved_family,
        "title": resolved_title,
        "exemplars": exemplars,
        "semantic_facets": facets or [primary_facet],
        "required_capabilities": ["procedure_execution"],
        "solution_recipes": [
            {
                "id": f"recipe_{learning_object_id}",
                "composition": "conjunctive",
                "all_of": [
                    {"facet": primary_facet, "capability": "procedure_execution", "modality": "hard"}
                ],
                "any_of": [],
            }
        ],
        "administration_conditions": dict(DEFAULT_ADMINISTRATION),
        "invariants": [],
        "permitted_variation_axes": ["problem_framing"],
        "response_contract": {"mode": anchors[0].practice_mode},
        "outcome_schema": {"coarse": ["correct", "wrong_method", "execution_error", "dont_know"]},
        "rubric": rubric,
        "fatal_errors": [],
        "failure_signature_triage": {},
        "source_neighborhoods": {},
        "target_distribution": {
            "support": [{"cell": f"{primary_facet} x {resolved_family}", "weight": 1.0}]
        },
        "depth_milestones": [],
        "leakage_boundaries": {"assessment_excludes": [item.id for item in anchors]},
        "authoring_version": "picker-template-1",
        "provenance_version": "owner-review-1",
    }

    contract_body: dict[str, Any] = {
        "purpose": resolved_title,
        "facet_scope": {"concepts": [], "facets": facets or [primary_facet]},
        "required_capabilities": ["procedure_execution"],
        "baseline_milestone": f"m_{learning_object_id}_baseline",
        "administration_conditions": dict(DEFAULT_ADMINISTRATION),
        "depth_envelope": {
            "envelope_version": f"denv_{learning_object_id}_v1",
            "bounds": {"target_additions": []},
            "reviewed_edges": [],
        },
        "exemplars": [
            {"id": item.id, "surface_ref": item.id, "weight": 1.0} for item in anchors
        ],
    }

    return {
        "spec": spec,
        "contract_body": contract_body,
        "source_rev": resolved_rev,
        "unit_id": resolved_unit,
        "family_key": resolved_family,
        "held_out_item_id": held_out.id,
        "warnings": warnings,
    }


def _rubric_for(item: PracticeItem) -> dict[str, Any]:
    rubric = item.grading_rubric
    if rubric is None:
        return {"max_points": 4, "criteria": [{"id": "correctness", "points": 4}]}
    return {
        "max_points": rubric.max_points,
        "criteria": [{"id": c.id, "points": c.points} for c in rubric.criteria],
    }

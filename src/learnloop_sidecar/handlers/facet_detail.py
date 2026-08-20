"""Graph/knowledge-map editor read RPCs (§3.4 locks, §8 graphs, §9.6 UI).

Pure reads composing existing services for the facet inspector, autocomplete
pickers, and recipe-tree blast-radius preview:

* ``get_facet_detail`` — the full facet contract + lock reasons + blueprint
  membership + evidence ledger for the FacetInspector panel.
* ``list_facets`` — a lightweight id/title/kind/status/locked list for facet
  autocomplete.
* ``preview_blueprint_readiness`` — current-vs-proposed LO readiness for an
  edited (in-memory, never persisted) blueprint payload, with identifiability
  warnings and affected goals.

All computation is deterministic and adds zero provider tokens. Writes nothing.
"""

from __future__ import annotations

from dataclasses import replace
from typing import Any

from pydantic import Field, ValidationError

from learnloop.learner.capability_grid import lo_blueprint_readiness
from learnloop.goals.certification import is_demonstrated_credit
from learnloop.curriculum.curriculum_locks import Operation, can_apply, identity_locks
from learnloop.learner.facet_state_reader import (
    CanonicalFacetStateReader,
    facet_recall_states_for_lo,
    is_canonical_state_vault,
    resolve_canonical_facet,
)
from learnloop.goals.goal_projection import resolve_goal_scope
from learnloop.learner.identifiability import analyze_identifiability, build_registry_view
from learnloop.scheduling.selection_rewards import predicted_facet_recall
from learnloop.vault.models import LearningObject, recipe_components
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.dto import ParamsModel, versioned
from learnloop_sidecar.errors import SidecarError
from learnloop_sidecar.registry import method


class FacetIdInput(ParamsModel):
    facet_id: str


@method("get_facet_detail", FacetIdInput)
def get_facet_detail(ctx: SidecarContext, params: FacetIdInput) -> dict[str, Any]:
    """Facet contract + lock reasons + blueprint membership + evidence (§9.6).

    The facet id is resolved canonically (aliases + terminal merges) before any
    lookup, so a retired-into-parent id still resolves to the surviving facet.
    ``lock`` mirrors ``can_apply(facet_merge)``; ``membership`` walks every LO
    blueprint recipe that references the facet; ``evidence`` folds the capability
    ledger (``demonstrated`` = ``is_demonstrated_credit``, credit ≥ 1.0).
    """

    vault, repository = ctx.require_vault()

    merge_map = repository.facet_merge_map()
    canonical = resolve_canonical_facet(vault, merge_map, params.facet_id)
    facet = vault.evidence_facets.get(canonical)
    if facet is None:
        raise SidecarError("not_found", f"Facet {params.facet_id} was not found.")

    def resolve(raw: str) -> str:
        return resolve_canonical_facet(vault, merge_map, str(raw))

    # Lock closure for this facet (padlock reasons shown before the gesture).
    lock_result = can_apply(
        vault,
        repository,
        Operation(op_type="facet_merge", entity_type="facet", entity_id=canonical),
    )
    lock = {
        "locked": not lock_result.legal,
        "reasons": [
            {"source": reason.source, "detail": reason.detail}
            for reason in lock_result.lock_reasons
        ],
    }

    # Membership: every blueprint recipe component (all_of / any_of / integration)
    # across every LO that references this canonical facet.
    membership: list[dict[str, Any]] = []
    blueprint_los: set[str] = set()
    for lo_id, learning_object in sorted(vault.learning_objects.items()):
        for blueprint in learning_object.blueprints:
            for recipe in blueprint.recipes:
                for role, component in _components_with_role(recipe):
                    if resolve(component.facet) != canonical:
                        continue
                    membership.append(
                        {
                            "learning_object_id": lo_id,
                            "lo_title": learning_object.title,
                            "blueprint_id": blueprint.id,
                            "recipe_id": recipe.id,
                            "capability": component.capability,
                            "modality": component.modality,
                            "role": role,
                        }
                    )
                    blueprint_los.add(lo_id)

    # LOs whose items exercise the facet (the "also counted toward" set); union
    # with blueprint membership. ``shared_with`` is every such LO beyond the first.
    item_los = sorted(
        {
            item.learning_object_id
            for item in vault.practice_items.values()
            if any(resolve(f) == canonical for f in item.evidence_facets)
        }
    )
    all_los = sorted(set(item_los) | blueprint_los)
    shared_with = all_los[1:]

    evidence = _facet_evidence(vault, repository, canonical, item_los)

    facet_contract = {
        "id": canonical,
        "title": facet.title,
        "kind": facet.kind,
        "claim": facet.claim,
        "preconditions": facet.preconditions,
        "positive_examples": facet.positive_examples,
        "negative_examples": facet.negative_examples,
        "non_goals": facet.non_goals,
        "error_signatures": facet.error_signatures,
        "aliases": facet.aliases,
        "status": facet.status,
    }

    return versioned(
        {
            "facet": facet_contract,
            "lock": lock,
            "membership": membership,
            "evidence": evidence,
            "shared_with": shared_with,
        }
    )


@method("list_facets")
def list_facets(ctx: SidecarContext, _params) -> dict[str, Any]:
    """Lightweight facet list for autocomplete pickers, sorted by id.

    ``locked`` comes from a single ``identity_locks`` closure pass (not a
    per-facet ``can_apply`` loop).
    """

    vault, repository = ctx.require_vault()
    locks = identity_locks(vault, repository)
    facets = [
        {
            "id": facet_id,
            "title": vault.evidence_facets[facet_id].title,
            "kind": vault.evidence_facets[facet_id].kind,
            "status": vault.evidence_facets[facet_id].status,
            "locked": facet_id in locks,
        }
        for facet_id in sorted(vault.evidence_facets)
    ]
    return versioned({"facets": facets})


class PreviewBlueprintReadinessParams(ParamsModel):
    learning_object_id: str
    # Edited blueprints in the LO YAML shape (list of blueprint dicts). Parsed
    # through the same pydantic path vault loading uses (LearningObject).
    blueprints: list[dict[str, Any]] = Field(default_factory=list)


@method("preview_blueprint_readiness", PreviewBlueprintReadinessParams)
def preview_blueprint_readiness(
    ctx: SidecarContext, params: PreviewBlueprintReadinessParams
) -> dict[str, Any]:
    """Current-vs-proposed LO readiness for an edited blueprint payload (§9.2).

    Builds an in-memory hypothetical LO (deep copy of the loaded LO with its
    ``blueprints`` replaced, re-parsed through ``LearningObject``); the loaded
    vault and repository are never mutated. Readiness is the same projection the
    goal report and recipe tree use; identifiability warnings are scoped to the
    LO's facet neighborhood; affected goals are active goals whose resolved
    scope includes this LO.
    """

    vault, repository = ctx.require_vault()

    learning_object = vault.learning_objects.get(params.learning_object_id)
    if learning_object is None:
        raise SidecarError(
            "not_found", f"Learning Object {params.learning_object_id} was not found."
        )

    current = lo_blueprint_readiness(vault, repository, params.learning_object_id)

    hypothetical_payload = learning_object.model_dump()
    hypothetical_payload["blueprints"] = params.blueprints
    try:
        hypothetical_lo = LearningObject.model_validate(hypothetical_payload)
    except ValidationError as exc:
        raise SidecarError(
            "invalid_payload", f"Could not parse the edited blueprints: {exc}."
        ) from exc

    hypothetical_vault = replace(
        vault,
        learning_objects={**vault.learning_objects, learning_object.id: hypothetical_lo},
    )
    proposed = lo_blueprint_readiness(hypothetical_vault, repository, params.learning_object_id)

    return versioned(
        {
            "current": _readiness_summary(current),
            "proposed": _readiness_summary(proposed),
            "identifiability_warnings": _identifiability_warnings(
                hypothetical_vault, hypothetical_lo
            ),
            "affected_goals": _affected_goals(vault, repository, learning_object.id),
        }
    )


def _components_with_role(recipe):
    """(role, component) for every component of a recipe, integration included."""

    for component in recipe.all_of:
        yield "all_of", component
    for component in recipe.any_of:
        yield "any_of", component
    if recipe.integration is not None:
        yield "integration", recipe.integration


def _facet_evidence(
    vault, repository, facet_id: str, item_los: list[str]
) -> dict[str, Any]:
    """Capability ledger + facet-global readiness/evidence-mass for a facet."""

    capability_ledger = [
        {
            "capability": cell.capability,
            "direct_positive_mass": cell.direct_positive_mass,
            "direct_negative_mass": cell.direct_negative_mass,
            "certification_credit": cell.certification_credit,
            "demonstrated": is_demonstrated_credit(cell.certification_credit),
        }
        for cell in repository.facet_capability_evidence_for_facet(facet_id)
    ]
    _surface_groups, evidence_mass = repository.facet_independence_evidence(facet_id)
    ready, ready_ghost = _facet_readiness(vault, repository, facet_id, item_los)
    return {
        "ready": ready,
        "ready_ghost": ready_ghost,
        "evidence_mass": evidence_mass,
        "capability_ledger": capability_ledger,
    }


def _facet_readiness(
    vault, repository, facet_id: str, item_los: list[str]
) -> tuple[float | None, float | None]:
    """Facet-global predicted recall, averaged over LOs exercising the facet.

    ``ready`` blends LO mastery with the facet's accrued recall evidence (the
    sanctioned ``predicted_facet_recall``); ``ready_ghost`` is the same blend
    with the facet evidence removed — the mastery-only prior the learner would
    read at with no direct evidence, so the UI can show how far evidence moved
    the needle. Both ``None`` when no LO exercises the facet.
    """

    if not item_los:
        return None, None
    blend_count = vault.config.recall_coverage.facet_blend_evidence_count
    reader = (
        CanonicalFacetStateReader(vault, repository)
        if is_canonical_state_vault(vault)
        else None
    )
    ready_values: list[float] = []
    ghost_values: list[float] = []
    for lo_id in item_los:
        mastery = repository.mastery_state(lo_id)
        logit = mastery.logit_mean if mastery is not None else None
        count = mastery.evidence_count if mastery is not None else 0
        best = None
        for state in facet_recall_states_for_lo(vault, repository, lo_id, reader=reader):
            if state.practice_item_id is not None:
                continue
            if vault.canonical_facet_id(state.facet_id) != facet_id:
                continue
            if best is None or state.independent_evidence_mass > best.independent_evidence_mass:
                best = state
        facet_mean = best.recall_mean if best is not None else None
        facet_mass = max(best.independent_evidence_mass, 0.0) if best is not None else 0.0
        ready_values.append(
            predicted_facet_recall(logit, count, facet_mean, facet_mass, blend_count)
        )
        ghost_values.append(predicted_facet_recall(logit, count, None, 0.0, blend_count))
    ready = sum(ready_values) / len(ready_values)
    ghost = sum(ghost_values) / len(ghost_values)
    return ready, ghost


def _readiness_summary(readiness) -> dict[str, Any]:
    """The ``{readiness, bottleneck}`` pair the blast-radius panel renders."""

    if readiness is None:
        return {"readiness": None, "bottleneck": None}
    return {
        "readiness": readiness.readiness,
        "bottleneck": readiness.bottleneck.as_dict() if readiness.bottleneck else None,
    }


def _identifiability_warnings(vault, learning_object) -> list[str]:
    """Identifiability findings that touch this LO's facet neighborhood (§11.3)."""

    view = build_registry_view(vault)
    lo_facets = {
        component.facet
        for blueprint in learning_object.blueprints
        for recipe in blueprint.recipes
        for component in recipe_components(recipe)
    }
    lo_facets |= {vault.canonical_facet_id(facet) for facet in lo_facets}
    warnings: list[str] = []
    for finding in analyze_identifiability(view):
        if set(finding.facet_ids) & lo_facets:
            warnings.append(finding.message)
    return warnings


def _affected_goals(vault, repository, learning_object_id: str) -> list[dict[str, str]]:
    """Active goals whose resolved scope includes this LO (or its facets)."""

    affected: list[dict[str, str]] = []
    for goal in vault.goals:
        if goal.status != "active":
            continue
        if learning_object_id in resolve_goal_scope(vault, goal, repository):
            affected.append({"goal_id": goal.id, "title": goal.title})
    return affected

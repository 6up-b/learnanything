"""KM3b provenance-UI RPCs (knowledge-model §9.6).

Thin handlers over the pure read-side services: attempt trace (criterion DAG),
capability grid + recipe tree per LO, and the facet evidence drawer's Demonstrated
timeline (a deterministic non-monotone ledger fold). All computation is
deterministic and adds zero provider tokens.
"""

from __future__ import annotations

from typing import Any

from learnloop.services.attempt_trace import build_attempt_trace
from learnloop.services.capability_grid import capability_grid, lo_blueprint_readiness
from learnloop.services.facet_evidence_timeline import (
    facet_evidence_timeline,
    facet_ready_derivation,
)
from learnloop.services.facet_state_reader import is_canonical_state_vault
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.dto import ParamsModel, versioned
from learnloop_sidecar.errors import SidecarError
from learnloop_sidecar.registry import method


class AttemptIdInput(ParamsModel):
    attempt_id: str


class LearningObjectIdInput(ParamsModel):
    learning_object_id: str


class FacetIdInput(ParamsModel):
    facet_id: str


@method("get_attempt_trace", AttemptIdInput)
def get_attempt_trace(ctx: SidecarContext, params: AttemptIdInput) -> dict[str, Any]:
    """Criterion-DAG trace for one attempt (§9.6 attempt trace view)."""

    vault, repository = ctx.require_vault()
    trace = build_attempt_trace(vault, repository, params.attempt_id)
    if trace is None:
        raise SidecarError("not_found", f"Attempt {params.attempt_id} was not found.")
    return versioned(trace.as_dict())


@method("get_capability_grid", LearningObjectIdInput)
def get_capability_grid(ctx: SidecarContext, params: LearningObjectIdInput) -> dict[str, Any]:
    """Facet × capability grid + blueprint recipe tree for one LO (§9.6)."""

    vault, repository = ctx.require_vault()
    if params.learning_object_id not in vault.learning_objects:
        raise SidecarError("not_found", f"Learning Object {params.learning_object_id} was not found.")
    grid = capability_grid(vault, repository, params.learning_object_id)
    readiness = lo_blueprint_readiness(vault, repository, params.learning_object_id)
    return versioned(
        {
            "grid": grid.as_dict(),
            "readiness": readiness.as_dict() if readiness is not None else None,
        }
    )


@method("get_facet_evidence_timeline", FacetIdInput)
def get_facet_evidence_timeline(ctx: SidecarContext, params: FacetIdInput) -> dict[str, Any]:
    """The Demonstrated curve for a facet + its cross-links (§9.6 phase 1)."""

    vault, repository = ctx.require_vault()
    canonical = vault.canonical_facet_id(params.facet_id)
    series = facet_evidence_timeline(vault, repository, canonical)
    ready = facet_ready_derivation(vault, repository, canonical, series)
    # "Also counted toward X and Y": LOs whose items exercise this canonical facet.
    counted_toward: list[dict[str, str]] = []
    seen: set[str] = set()
    for item in vault.practice_items.values():
        item_facets = {vault.canonical_facet_id(str(f)) for f in item.evidence_facets}
        if canonical not in item_facets:
            continue
        lo = vault.learning_objects.get(item.learning_object_id)
        if lo is None or lo.id in seen:
            continue
        seen.add(lo.id)
        counted_toward.append({"learning_object_id": lo.id, "learning_object_title": lo.title})
    counted_toward.sort(key=lambda entry: entry["learning_object_title"])
    demonstrated = series[-1].demonstrated if series else 0.0
    return versioned(
        {
            "facet_id": canonical,
            "model_version": vault.config.algorithms.algorithm_version,
            "supported": is_canonical_state_vault(vault),
            "demonstrated": demonstrated,
            "points": [point.as_dict() for point in series],
            "counted_toward": counted_toward,
            "ready": ready.as_dict() if ready is not None else None,
        }
    )

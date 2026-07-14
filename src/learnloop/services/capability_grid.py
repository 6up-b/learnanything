"""Capability grid — facet × capability heatmap for an LO neighborhood (KM §9.6).

Each cell encodes the dual axis for a (facet, capability) pair:

* **Demonstrated** — capability-matched direct/embedded certification credit
  meeting the shared certification threshold; the honest answer to
  "certified for retrieval but never tested on selection".
* **Ready** — the pooled expected-performance prediction over the shared facet
  mean (capability-agnostic at launch, §4.2, so the same Ready value tiles a
  facet's row; certification is the axis that discriminates capabilities).
* **untested** — no direct evidence has touched this capability cell at all.

It supersedes the per-LO facet radar as the diagnostic drill-down (the radar
stays for legacy mvp-0.6 vaults, which have no capability ledger). Pure read over
the persisted capability ledger + shared facet state; writes nothing.
"""

from __future__ import annotations

from dataclasses import dataclass

from learnloop.db.repositories import Repository
from learnloop.services.certification import is_demonstrated_credit
from learnloop.services.blueprint_projection import LoReadiness
from learnloop.services.facet_diagnostics import required_facets
from learnloop.services.facet_state_reader import (
    facet_recall_states_for_lo,
    is_canonical_state_vault,
)
from learnloop.services.goal_certification import required_capabilities_for_facet
from learnloop.services.selection_rewards import predicted_facet_recall
from learnloop.vault.models import LoadedVault


@dataclass(frozen=True)
class GridCell:
    facet_id: str
    capability: str
    required: bool                 # this capability is required for the facet on this LO
    demonstrated: bool             # capability-matched certification credit > 0
    certification_credit: float
    direct_positive_mass: float
    direct_negative_mass: float
    ready: float                   # pooled prediction (capability-agnostic)
    tested: bool                   # any direct evidence touched this cell

    def as_dict(self) -> dict[str, object]:
        return {
            "facet_id": self.facet_id,
            "capability": self.capability,
            "required": self.required,
            "demonstrated": self.demonstrated,
            "certification_credit": self.certification_credit,
            "direct_positive_mass": self.direct_positive_mass,
            "direct_negative_mass": self.direct_negative_mass,
            "ready": self.ready,
            "tested": self.tested,
        }


@dataclass(frozen=True)
class CapabilityGrid:
    learning_object_id: str
    facets: list[str]
    capabilities: list[str]
    cells: list[GridCell]
    supported: bool                # False on mvp-0.6 (no capability ledger)

    def as_dict(self) -> dict[str, object]:
        return {
            "learning_object_id": self.learning_object_id,
            "supported": self.supported,
            "facets": list(self.facets),
            "capabilities": list(self.capabilities),
            "cells": [cell.as_dict() for cell in self.cells],
        }


def _lo_required_facets(vault: LoadedVault, repository: Repository, learning_object) -> list[str]:
    facets = {
        vault.canonical_facet_id(str(facet))
        for facet in required_facets(vault, learning_object.id, repository)
    }
    return sorted(facets)


def capability_grid(
    vault: LoadedVault, repository: Repository, learning_object_id: str
) -> CapabilityGrid:
    """Facet × capability grid for one LO (canonical facet keys)."""

    learning_object = vault.learning_objects.get(learning_object_id)
    if learning_object is None:
        return CapabilityGrid(
            learning_object_id=learning_object_id,
            facets=[],
            capabilities=[],
            cells=[],
            supported=False,
        )
    supported = is_canonical_state_vault(vault)
    facets = _lo_required_facets(vault, repository, learning_object)

    # Shared facet recall means (pooled prediction input), keyed by canonical id.
    recall_by_facet = {}
    for state in facet_recall_states_for_lo(vault, repository, learning_object_id):
        if state.practice_item_id is not None:
            continue
        recall_by_facet[vault.canonical_facet_id(state.facet_id)] = state
    mastery = repository.mastery_state(learning_object_id)
    blend_count = vault.config.recall_coverage.facet_blend_evidence_count

    def ready_for(facet: str) -> float:
        state = recall_by_facet.get(facet)
        return predicted_facet_recall(
            mastery.logit_mean if mastery is not None else None,
            mastery.evidence_count if mastery is not None else 0,
            state.recall_mean if state is not None else None,
            max(state.independent_evidence_mass, 0.0) if state is not None else 0.0,
            blend_count,
        )

    capabilities_seen: set[str] = set()
    cells: list[GridCell] = []
    for facet in facets:
        required_caps, _legacy = required_capabilities_for_facet(vault, learning_object, facet)
        evidence_by_cap = {}
        if supported:
            for cell in repository.facet_capability_evidence_for_facet(facet):
                evidence_by_cap[cell.capability] = cell
        cell_caps = sorted(set(required_caps) | set(evidence_by_cap))
        ready = ready_for(facet)
        for capability in cell_caps:
            capabilities_seen.add(capability)
            evidence = evidence_by_cap.get(capability)
            credit = evidence.certification_credit if evidence is not None else 0.0
            pos = evidence.direct_positive_mass if evidence is not None else 0.0
            neg = evidence.direct_negative_mass if evidence is not None else 0.0
            cells.append(
                GridCell(
                    facet_id=facet,
                    capability=capability,
                    required=capability in required_caps,
                    demonstrated=is_demonstrated_credit(credit),
                    certification_credit=credit,
                    direct_positive_mass=pos,
                    direct_negative_mass=neg,
                    ready=ready,
                    tested=(pos + neg) > 0.0,
                )
            )
    return CapabilityGrid(
        learning_object_id=learning_object_id,
        facets=facets,
        capabilities=sorted(capabilities_seen),
        cells=cells,
        supported=supported,
    )


def lo_blueprint_readiness(
    vault: LoadedVault, repository: Repository, learning_object_id: str
) -> LoReadiness | None:
    """Per-LO blueprint recipe readiness (§9.2) for the recipe-tree surface.

    Delegates to the same projection the goal report uses, so the LO-detail
    "why not ready" tree and the goal banner agree. None when the vault has no
    canonical state or the LO has no authored blueprints.
    """

    from learnloop.services.goal_projection import _lo_blueprint_readiness

    if not is_canonical_state_vault(vault):
        return None
    mastery = repository.mastery_state(learning_object_id)
    states = facet_recall_states_for_lo(vault, repository, learning_object_id)
    return _lo_blueprint_readiness(
        vault,
        learning_object_id,
        states,
        mastery,
        blend_count=vault.config.recall_coverage.facet_blend_evidence_count,
    )

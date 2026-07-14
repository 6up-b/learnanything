"""Overconfidence list (spec §4.3, package F5).

Facets the model predicts the learner is Ready on while they have **not** been
Demonstrated — the "you think you know this" set. Deterministic read model over
``goal_report``: no belief writes, no LLM. Sorted by ``ready × blueprint
weight`` and gated on a minimum evidence mass so cold-start noise can't populate
the list.

The Ready/Demonstrated split is never blended (KM3 §9.5): a facet qualifies only
when its predicted recall at the goal horizon clears the goal's own target
(``ready`` is high) *and* it carries no capability-matched certification credit
(``demonstrated`` is false).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from learnloop.clock import Clock
from learnloop.db.repositories import Repository
from learnloop.services.goal_projection import GoalReport, goal_report
from learnloop.vault.models import Goal, LoadedVault


def blueprint_weight_by_facet(
    vault: LoadedVault, report: GoalReport
) -> dict[tuple[str, str], float]:
    """Per-(LO, facet) blueprint weight, defaulting to 1.0 with no blueprints.

    A facet's weight is the summed weight of the LO's blueprints whose recipes
    reference it. LOs without authored blueprints (or facets not named by any
    recipe) fall back to a neutral 1.0 so weighting never silently zeroes a
    facet out of the ranking.
    """

    weights: dict[tuple[str, str], float] = {}
    for lo_id, readiness in report.blueprint_readiness_by_lo.items():
        per_facet: dict[str, float] = {}
        for blueprint in readiness.blueprints:
            facets_in_blueprint: set[str] = set()
            for recipe in blueprint.recipes:
                for component in recipe.components:
                    facets_in_blueprint.add(vault.canonical_facet_id(component.facet))
            for facet_id in facets_in_blueprint:
                per_facet[facet_id] = per_facet.get(facet_id, 0.0) + max(blueprint.weight, 0.0)
        for facet_id, weight in per_facet.items():
            weights[(lo_id, facet_id)] = weight
    return weights


@dataclass(frozen=True)
class OverconfidentFacet:
    learning_object_id: str
    learning_object_title: str
    facet_id: str
    ready: float
    demonstrated: bool
    blueprint_weight: float
    evidence_mass: float
    score: float  # ready × blueprint_weight, the sort key

    def as_dict(self) -> dict[str, Any]:
        return {
            "learning_object_id": self.learning_object_id,
            "learning_object_title": self.learning_object_title,
            "facet_id": self.facet_id,
            "ready": self.ready,
            "demonstrated": self.demonstrated,
            "blueprint_weight": self.blueprint_weight,
            "evidence_mass": self.evidence_mass,
            "score": self.score,
        }


def overconfidence_facets(
    vault: LoadedVault,
    repository: Repository,
    goal: Goal,
    *,
    clock: Clock | None = None,
    min_evidence_mass: float | None = None,
) -> list[OverconfidentFacet]:
    """Ready-high / Demonstrated-false facets for ``goal``, ranked (§4.3)."""

    if min_evidence_mass is None:
        min_evidence_mass = vault.config.hypothesis.overconfidence_min_evidence_mass
    report = goal_report(vault, repository, goal, clock=clock)
    weights = blueprint_weight_by_facet(vault, report)
    target = goal.target_recall

    out: list[OverconfidentFacet] = []
    for facet in report.facets:
        if facet.demonstrated:
            continue  # Demonstrated facets are, by definition, not overconfidence.
        if facet.evidence_mass < min_evidence_mass:
            continue  # Cold-start noise guard.
        if facet.ready < target:
            continue  # Not "Ready high" — nothing to be overconfident about.
        weight = weights.get(
            (facet.learning_object_id, vault.canonical_facet_id(facet.facet_id)), 1.0
        )
        lo = vault.learning_objects.get(facet.learning_object_id)
        out.append(
            OverconfidentFacet(
                learning_object_id=facet.learning_object_id,
                learning_object_title=lo.title if lo is not None else facet.learning_object_id,
                facet_id=facet.facet_id,
                ready=facet.ready,
                demonstrated=facet.demonstrated,
                blueprint_weight=weight,
                evidence_mass=facet.evidence_mass,
                score=facet.ready * weight,
            )
        )
    out.sort(key=lambda f: (f.score, f.ready, f.facet_id), reverse=True)
    return out

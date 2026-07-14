"""Exam-readiness-by-task-family report (source-ingestion §15).

    declared blueprint distribution (exam profiles + blueprint weights)
      ×  facet-capability state (KM2 certification ledger + a KM §9.2 projection)
      per task family,
    with exam-calibration Brier overlays where practice-exam data exists.

The display rule (KM §9.6) is honoured: every row is labelled with a clear
Ready-vs-Demonstrated split — Ready is the projected success probability (predicted
performance), Demonstrated is the certification-ledger credit (evidence actually
banked). We never blend them into one number.

**ING M8 — fully calibrated.** On top of the M7 lightweight table this computes,
Monte-Carlo-free, a predicted SCORE DISTRIBUTION per blueprint family: modelling a
family as ``n`` independent Bernoulli tasks with success probability ``p`` gives an
analytic mean ``p`` and variance ``p(1-p)/n``; the whole-exam predicted score is the
weight-normalized aggregate ``S = Σ wᵢ·pᵢ`` with ``Var(S) = Σ wᵢ²·pᵢ(1-pᵢ)/nᵢ``. That
predicted distribution is overlaid — clearly labelled, never blended — with the
practice-exam Brier calibration from ``exam_calibration.py`` when data exists, so the
learner sees predicted-vs-demonstrated AND how well past predictions held up. Both
the LIGHTWEIGHT M7 table and the M8 distribution are deterministic and add zero
provider tokens (KM §12.9).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from math import sqrt
from typing import Any

from learnloop.services.certification import is_demonstrated_credit

from learnloop.db.repositories import Repository
from learnloop.services.blueprint_projection import project_blueprint
from learnloop.vault.models import LoadedVault

# Ledger credit at/above which a (facet, capability) counts as Demonstrated.


@dataclass
class TaskFamilyReadiness:
    task_family: str
    weight: float
    normalized_weight: float
    learning_object_ids: list[str] = field(default_factory=list)
    ready: float | None = None            # projected P(success) — predicted performance
    demonstrated_fraction: float = 0.0    # ledger-certified share — evidence banked
    facet_capabilities: list[dict[str, Any]] = field(default_factory=list)
    calibration: dict[str, Any] | None = None
    # ING M8: analytic predicted score distribution for this family.
    predicted: dict[str, Any] | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "task_family": self.task_family,
            "weight": self.weight,
            "normalized_weight": self.normalized_weight,
            "learning_object_ids": list(self.learning_object_ids),
            "ready": self.ready,
            "demonstrated_fraction": self.demonstrated_fraction,
            "facet_capabilities": list(self.facet_capabilities),
            "calibration": self.calibration,
            "predicted": self.predicted,
        }


@dataclass
class ExamReadinessReport:
    subject_id: str | None
    rows: list[TaskFamilyReadiness] = field(default_factory=list)
    has_calibration: bool = False
    # ING M8: whole-exam predicted score distribution (mean/variance/std) and the
    # weight-normalized demonstrated fraction, reported side by side (never blended).
    predicted_score: dict[str, Any] | None = None
    demonstrated_score: float | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "subject_id": self.subject_id,
            "display_rule": "ready_vs_demonstrated",
            "rows": [row.as_dict() for row in self.rows],
            "has_calibration": self.has_calibration,
            "predicted_score": self.predicted_score,
            "demonstrated_score": self.demonstrated_score,
        }


def _recipe_components(blueprint) -> list[tuple[str, str]]:
    comps: list[tuple[str, str]] = []
    for recipe in blueprint.recipes or []:
        for comp in [*(recipe.all_of or []), *(recipe.any_of or [])]:
            comps.append((comp.facet, comp.capability))
        if recipe.integration is not None:
            comps.append((recipe.integration.facet, recipe.integration.capability))
    return comps


def exam_readiness_report(
    vault: LoadedVault,
    repository: Repository,
    *,
    subject_id: str | None = None,
    exam_profile: dict[str, Any] | None = None,
    total_exam_items: int | None = None,
) -> ExamReadinessReport:
    """Build the deterministic exam-readiness table + predicted score distribution (§15).

    No LLM. ``total_exam_items`` (optional) sizes each family's Bernoulli item count
    ``nᵢ = max(1, round(normalized_weightᵢ · total_exam_items))`` so the per-family
    variance ``p(1-p)/n`` tightens as the exam allots more items to a family; absent
    it, each family is one representative task (``n = 1``)."""

    # Certification ledger (Demonstrated) keyed by (facet, capability).
    ledger: dict[tuple[str, str], float] = {}
    for row in repository.facet_capability_evidence_all():
        ledger[(row.facet_id, row.capability)] = row.certification_credit

    # Canonical shared-facet recall means (Ready projection input).
    recall_by_facet: dict[str, float] = {}
    for state in repository.canonical_facet_recall_states():
        if state.practice_item_id is not None:
            continue
        key = vault.canonical_facet_id(state.facet_id)
        prior = recall_by_facet.get(key)
        if prior is None or (state.recall_mean or 0.0) > prior:
            recall_by_facet[key] = state.recall_mean or 0.0

    def component_recall(facet: str, _capability: str) -> float:
        return recall_by_facet.get(vault.canonical_facet_id(facet), 0.0)

    slip = float(vault.config.evidence.blueprints.slip)
    # Representative task for LO/blueprint readiness is treated as constructed
    # response (KM §9.2): guess floor 0. Item-level projections pass a format floor.
    guess = 0.0

    profile_weights = (exam_profile or {}).get("task_families") if exam_profile else None

    rows: list[TaskFamilyReadiness] = []
    for lo_id, lo in sorted(vault.learning_objects.items()):
        if subject_id is not None and subject_id not in (lo.subjects or []):
            continue
        if not lo.blueprints:
            continue
        for blueprint in lo.blueprints:
            projection = project_blueprint(blueprint, component_recall, slip=slip, guess=guess)
            comps = _recipe_components(blueprint)
            facet_caps: list[dict[str, Any]] = []
            demonstrated = 0
            for facet, capability in comps:
                credit = ledger.get((vault.canonical_facet_id(facet), capability), 0.0)
                is_demo = is_demonstrated_credit(credit)
                demonstrated += 1 if is_demo else 0
                facet_caps.append(
                    {
                        "facet": facet,
                        "capability": capability,
                        "demonstrated": is_demo,
                        "certification_credit": round(credit, 3),
                        "recall_mean": round(component_recall(facet, capability), 3),
                    }
                )
            # task family: derive from the exam-profile weighting when present, else
            # the blueprint id (the blueprint IS the task family proxy in v2).
            task_family = blueprint.id
            weight = blueprint.weight
            if profile_weights:
                # blend the declared exam distribution in by matching lo/blueprint id.
                weight = float(profile_weights.get(blueprint.id, blueprint.weight))
            rows.append(
                TaskFamilyReadiness(
                    task_family=task_family,
                    weight=weight,
                    normalized_weight=0.0,
                    learning_object_ids=[lo_id],
                    ready=projection.success_probability,
                    demonstrated_fraction=(demonstrated / len(comps)) if comps else 0.0,
                    facet_capabilities=facet_caps,
                )
            )

    total_weight = sum(max(r.weight, 0.0) for r in rows)
    for row in rows:
        row.normalized_weight = (row.weight / total_weight) if total_weight > 0 else 0.0

    # ING M8: analytic predicted score distribution per family and aggregate.
    # Family score ~ mean p, variance p(1-p)/n (n independent Bernoulli tasks).
    agg_mean = 0.0
    agg_variance = 0.0
    demonstrated_score = 0.0
    for row in rows:
        p = row.ready if row.ready is not None else 0.0
        if total_exam_items is not None:
            n_items = max(1, round(row.normalized_weight * total_exam_items))
        else:
            n_items = 1
        variance = p * (1.0 - p) / n_items
        row.predicted = {
            "mean": round(p, 4),
            "variance": round(variance, 6),
            "std": round(sqrt(variance), 4),
            "n_items": n_items,
        }
        agg_mean += row.normalized_weight * p
        agg_variance += (row.normalized_weight ** 2) * variance
        demonstrated_score += row.normalized_weight * row.demonstrated_fraction

    report = ExamReadinessReport(subject_id=subject_id, rows=rows)
    if rows:
        report.predicted_score = {
            "mean": round(agg_mean, 4),
            "variance": round(agg_variance, 6),
            "std": round(sqrt(agg_variance), 4),
        }
        report.demonstrated_score = round(demonstrated_score, 4)

    # Calibration overlay where practice-exam data exists (Brier, exam_calibration).
    try:
        from learnloop.services.exam_calibration import calibration_report

        calib = calibration_report(vault, repository)
        items = (calib or {}).get("items", {}) if calib else {}
        if items and items.get("count", 0) > 0:
            report.has_calibration = True
            for row in report.rows:
                row.calibration = {"brier": items.get("brier"), "sample": items.get("count")}
    except Exception:  # pragma: no cover - calibration is an optional overlay
        pass

    return report

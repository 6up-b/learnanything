"""Lightweight exam-readiness-by-task-family report (source-ingestion M7, §15).

Exam preparation is a primary intent, so its marquee readout ships in the core
release. This report is LIGHTWEIGHT = a DETERMINISTIC table, no LLM:

    declared blueprint distribution (exam profiles + blueprint weights)
      ×  facet-capability state (KM2 certification ledger + a KM §9.2 projection)
      per task family,
    with exam-calibration Brier overlays where practice-exam data exists.

The display rule (KM §9.6) is honoured: every row is labelled with a clear
Ready-vs-Demonstrated split — Ready is the projected success probability (predicted
performance), Demonstrated is the certification-ledger credit (evidence actually
banked). We never blend them into one number. M8 ships the fully calibrated
version (predicted score distributions against Brier calibration).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from learnloop.db.repositories import Repository
from learnloop.services.blueprint_projection import project_blueprint
from learnloop.vault.models import LoadedVault

# Ledger credit at/above which a (facet, capability) counts as Demonstrated.
_DEMONSTRATED_CREDIT = 1.0


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
        }


@dataclass
class ExamReadinessReport:
    subject_id: str | None
    rows: list[TaskFamilyReadiness] = field(default_factory=list)
    has_calibration: bool = False

    def as_dict(self) -> dict[str, Any]:
        return {
            "subject_id": self.subject_id,
            "display_rule": "ready_vs_demonstrated",
            "rows": [row.as_dict() for row in self.rows],
            "has_calibration": self.has_calibration,
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
) -> ExamReadinessReport:
    """Build the deterministic exam-readiness table (§15). No LLM."""

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
                is_demo = credit >= _DEMONSTRATED_CREDIT
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

    report = ExamReadinessReport(subject_id=subject_id, rows=rows)

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

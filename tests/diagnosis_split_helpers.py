"""A small multi-LO vault with graded history for the Slice 1 diagnosis tests.

Graph (concepts): ``matrix_transpose`` is a prerequisite of
``singular_value_decomposition``, which is ``confusable_with``
``eigendecomposition``; ``unrelated_topic`` stands alone. Every attempt is a
real ``apply_attempt`` with a resolved grade, so stored error events, causal
hypotheses and feedback metadata are exactly what the live path writes.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from learnloop.attempts.attempts import (
    ApplyAttemptInput,
    AttemptDraft,
    GradeAttribution,
    ResolvedGrade,
    apply_attempt,
)
from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.vault.loader import load_vault
from learnloop.vault.paths import VaultPaths
from learnloop.vault.yaml_io import write_yaml

from tests.helpers import NOW_ISO, create_basic_vault

BASE_TIME = datetime(2026, 5, 1, 9, 0, tzinfo=UTC)
#: Criterion -> the facet it directly measures (others measure the item's first facet).
TARGETS = {"setup": "compute", "result": "recall"}


def at(offset_hours: float) -> datetime:
    return BASE_TIME + timedelta(hours=offset_hours)


def _concept(title: str) -> dict[str, Any]:
    return {
        "title": title,
        "type": "procedure",
        "aliases": [],
        "description": title,
        "tags": [],
        "created_at": NOW_ISO,
        "updated_at": NOW_ISO,
    }


def _lo(lo_id: str, concept: str, title: str) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "id": lo_id,
        "title": title,
        "subjects": ["linear-algebra"],
        "concept": concept,
        "knowledge_type": "procedural",
        "status": "active",
        "contradicts": None,
        "summary": title,
        "prerequisites": [],
        "confusables": [],
        "difficulty_prior": 0.5,
        "tags": [],
        "provenance": {"origin": "human", "source_refs": []},
        "created_at": NOW_ISO,
        "updated_at": NOW_ISO,
    }


def _item(item_id: str, lo_id: str, prompt: str, expected: str, facets: list[str], criteria: list[tuple[str, int]], surface: str) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "id": item_id,
        "learning_object_id": lo_id,
        "subjects": None,
        "practice_mode": "short_answer",
        "attempt_types_allowed": ["independent_attempt", "hinted_attempt", "dont_know"],
        "evidence_facets": facets,
        "evidence_weights": {facet: 1.0 for facet in facets},
        "prompt": prompt,
        "expected_answer": expected,
        "difficulty": 0.5,
        "tags": [],
        "hints": ["Think about it."],
        "surface_family": surface,
        "grading_rubric": {
            "max_points": sum(points for _id, points in criteria),
            "criteria": [
                {
                    "id": criterion_id,
                    "points": points,
                    "description": f"{criterion_id} is right.",
                    # Authored targets make the passed-facet firewall concrete.
                    "targets": [{"facet": TARGETS.get(criterion_id, facets[0]), "capability": "retrieval" if TARGETS.get(criterion_id, facets[0]) != "compute" else "procedure_execution"}],
                }
                for criterion_id, points in criteria
            ],
            "fatal_errors": [],
        },
        "provenance": {"origin": "human", "source_refs": []},
        "created_at": NOW_ISO,
        "updated_at": NOW_ISO,
    }


def build_diagnosis_vault(root: Path) -> VaultPaths:
    paths = create_basic_vault(root)
    write_yaml(
        paths.concepts_path,
        {
            "schema_version": 1,
            "concepts": {
                "singular_value_decomposition": _concept("Singular Value Decomposition"),
                "matrix_transpose": _concept("Matrix transpose"),
                "eigendecomposition": _concept("Eigendecomposition"),
                "unrelated_topic": _concept("Unrelated topic"),
            },
        },
    )
    write_yaml(
        paths.relations_path,
        {
            "schema_version": 1,
            "edges": [
                {
                    "id": "edge_transpose_svd",
                    "relation_type": "prerequisite",
                    "source": "matrix_transpose",
                    "target": "singular_value_decomposition",
                    "strength": 1.0,
                    "created_at": NOW_ISO,
                    "updated_at": NOW_ISO,
                },
                {
                    "id": "edge_svd_eigen",
                    "relation_type": "confusable_with",
                    "source": "singular_value_decomposition",
                    "target": "eigendecomposition",
                    "strength": 1.0,
                    "created_at": NOW_ISO,
                    "updated_at": NOW_ISO,
                },
            ],
        },
    )
    for lo_id, concept, title in (
        ("lo_svd_compute", "singular_value_decomposition", "Compute an SVD"),
        ("lo_transpose", "matrix_transpose", "Transpose a matrix"),
        ("lo_eigen", "eigendecomposition", "Eigendecomposition"),
        ("lo_unrelated", "unrelated_topic", "Unrelated"),
    ):
        write_yaml(paths.learning_object_path("linear-algebra", lo_id), _lo(lo_id, concept, title))
    for item_id, lo_id, prompt, expected, facets, criteria, surface in (
        ("pi_svd_compute_001", "lo_svd_compute", "Write the SVD of A.", "U Sigma V^T", ["recall", "compute"], [("setup", 2), ("result", 2)], "svd_compute"),
        ("pi_svd_compute_002", "lo_svd_compute", "Factor B with an SVD.", "U Sigma V^T", ["recall", "compute"], [("setup", 2), ("result", 2)], "svd_compute_b"),
        ("pi_transpose_001", "lo_transpose", "Transpose the matrix M.", "M^T", ["transpose"], [("correctness", 4)], "transpose"),
        ("pi_eigen_001", "lo_eigen", "Diagonalize A.", "P D P^{-1}", ["recall"], [("correctness", 4)], "eigen"),
        ("pi_unrelated_001", "lo_unrelated", "Name a prime.", "2", ["other"], [("correctness", 4)], "unrelated"),
    ):
        write_yaml(
            paths.practice_item_path("linear-algebra", item_id),
            _item(item_id, lo_id, prompt, expected, facets, criteria, surface),
        )
    vault = load_vault(root)
    return VaultPaths(vault.root, vault.config)


def seed_attempt(
    vault,
    repository: Repository,
    *,
    attempt_id: str,
    item_id: str,
    answer: str,
    when: datetime,
    points: dict[str, float],
    error: dict[str, Any] | None = None,
    hints_used: int = 0,
    attempt_type: str = "independent_attempt",
):
    """One real graded attempt; ``error`` is a GradeAttribution kwargs dict."""

    item = vault.practice_items[item_id]
    max_points = sum(criterion.points for criterion in item.grading_rubric.criteria)
    score = int(round(sum(points.values())))
    attributions = [GradeAttribution(**error)] if error is not None else []
    grade = ResolvedGrade(
        rubric_score=score,
        criterion_points=dict(points),
        evidence_rows=[
            {
                "id": f"ge_{attempt_id}_{criterion_id}",
                "criterion_id": criterion_id,
                "points_awarded": float(value),
                "evidence": f"{criterion_id} graded",
                "notes": None,
                "local_grader_id": "test",
                "grader_tier": 1,
                "created_at": when.isoformat().replace("+00:00", "Z"),
            }
            for criterion_id, value in points.items()
        ],
        error_attributions=attributions,
        grader_confidence=0.9,
        confidence=4,
        manual_review_reason=None,
        feedback_md="Feedback." if error else "Correct.",
    )
    _ = max_points
    return apply_attempt(
        vault,
        repository,
        ApplyAttemptInput(
            draft=AttemptDraft(
                practice_item_id=item_id,
                learner_answer_md=answer,
                attempt_type=attempt_type,
                hints_used=hints_used,
            ),
            attempt_id=attempt_id,
            grade=grade,
            grading_source="codex",
        ),
        clock=FrozenClock(when),
    )


def transpose_error(statement: str = "The learner treats V and V transpose as identical.", *, cause_scope: str = "learner_state", quote: str = "V") -> dict[str, Any]:
    return {
        "error_type": "conceptual_slip",
        "severity": 0.7,
        "evidence": "The final factor is not transposed.",
        "is_misconception": True,
        "misconception_statement": statement,
        "resolution_status": "unresolved",
        "cause_scope": cause_scope,
        "operation": "transpose_confusion",
        "first_divergence": {"anchor_kind": "span", "criterion_id": "result" , "quote": quote},
        "target_evidence_families": ["recall"],
        "candidate_causes": [
            {
                "statement": statement,
                "cause_scope": "learner_state",
                "target_ref": {"kind": "facet_capability", "facet_id": "recall", "capability": "retrieval"},
            }
        ],
    }


def seed_history(paths: VaultPaths) -> tuple[Any, Repository]:
    """A learner who confuses transposes on SVD items, then passes once."""

    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    # Old failure on the prerequisite LO (one hop), any surface family.
    seed_attempt(
        vault, repository, attempt_id="att_01_transpose_fail", item_id="pi_transpose_001",
        answer="M stays M", when=at(0), points={"correctness": 0},
        error={**transpose_error("The learner thinks transposing changes nothing.", quote="M stays M"),
               "first_divergence": {"anchor_kind": "span", "criterion_id": "correctness", "quote": "M stays M"},
               "target_evidence_families": ["transpose"],
               "candidate_causes": []},
    )
    seed_attempt(
        vault, repository, attempt_id="att_02_svd_fail", item_id="pi_svd_compute_001",
        answer="A = U Sigma V", when=at(1), points={"setup": 2, "result": 0},
        error=transpose_error(quote="U Sigma V"),
    )
    seed_attempt(
        vault, repository, attempt_id="att_03_svd_pass", item_id="pi_svd_compute_002",
        answer="B = U Sigma V^T", when=at(2), points={"setup": 2, "result": 2},
    )
    seed_attempt(
        vault, repository, attempt_id="att_04_unrelated_fail", item_id="pi_unrelated_001",
        answer="4", when=at(3), points={"correctness": 0},
        error={"error_type": "conceptual_slip", "severity": 0.5, "evidence": "4 is not prime.",
               "resolution_status": "unresolved", "cause_scope": "learner_state",
               "first_divergence": {"anchor_kind": "span", "criterion_id": "correctness", "quote": "4"}},
    )
    seed_attempt(
        vault, repository, attempt_id="att_05_eigen_fail", item_id="pi_eigen_001",
        answer="A = P D P", when=at(4), points={"correctness": 1},
        error={"error_type": "conceptual_slip", "severity": 0.6, "evidence": "Missing inverse.",
               "resolution_status": "unresolved", "cause_scope": "learner_state",
               "target_evidence_families": ["recall"],
               "first_divergence": {"anchor_kind": "span", "criterion_id": "correctness", "quote": "P D P"}},
    )
    seed_attempt(
        vault, repository, attempt_id="att_06_svd_fail", item_id="pi_svd_compute_001",
        answer="A = U Sigma V again", when=at(5), points={"setup": 2, "result": 0},
        error=transpose_error(quote="U Sigma V again"),
    )
    # Later than the diagnosed attempt in most tests: must never be shown.
    seed_attempt(
        vault, repository, attempt_id="att_07_svd_future", item_id="pi_svd_compute_002",
        answer="B = U Sigma V (future)", when=at(10), points={"setup": 2, "result": 0},
        error=transpose_error(quote="U Sigma V (future)"),
    )
    return load_vault(paths.root), repository


def blind_record(
    *,
    score: float,
    max_points: float,
    criteria: dict[str, float],
    attributions: list[dict[str, Any]] | None = None,
    local_analysis: str = "The final factor V is not transposed.",
    traces: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return {
        "grader_mode": "blind",
        "rubric_score": score,
        "max_points": max_points,
        "criteria": [
            {"criterion_id": key, "points_awarded": value, "evidence": f"{key} graded"}
            for key, value in criteria.items()
        ],
        "fatal_errors": [],
        "local_analysis_md": local_analysis,
        "repaired_traces": list(traces or []),
        "error_attributions": [
            {"index": index, **row} for index, row in enumerate(attributions or [])
        ],
    }

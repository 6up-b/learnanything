"""What other test files use from ``tests/test_exercise_authoring.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from learnloop.content.authoring.ai_contracts import (
    CriterionFacetWeightsPayload,
    ExerciseAuthoredItem,
    ExerciseAuthoring,
    FacetWeightPayload,
    RubricCriterionPayload,
    RubricPatchPayload,
    TaskFeaturesPayload,
)
from learnloop.vault.yaml_io import write_yaml

from tests.structured_ai import StructuredClientFake


def _write_facet_registry(tmp_path) -> None:
    write_yaml(
        tmp_path / "vault" / "facets.yaml",
        {
            "schema_version": 2,
            "facets": [
                {"id": "facet_svd_shape", "title": "SVD factor shape", "status": "reviewed"},
                {"id": "facet_orthonormal_columns", "title": "Orthonormal columns", "status": "reviewed"},
            ],
        },
    )


def _item(**overrides) -> ExerciseAuthoredItem:
    base = dict(
        # Extra whitespace on purpose: anchoring must be whitespace-tolerant
        # and store the source-owned slice, not this echo.
        statement_md="singular value decomposition   writes A",
        title="Exercise 1",
        learning_object_id="lo_svd_definition",
        practice_mode="short_answer",
        expected_answer_md="A = U Sigma V^T with orthogonal U, V.",
        grading_rubric=RubricPatchPayload(
            max_points=4,
            criteria=[
                RubricCriterionPayload(id="factorization", points=2.0, description="States the factorization."),
                RubricCriterionPayload(id="factors", points=2.0, description="Names all three factors."),
            ],
        ),
        evidence_facets=["facet_svd_shape"],
        evidence_weights=[FacetWeightPayload(facet_id="facet_svd_shape", weight=1.0)],
        criterion_facet_weights=[
            CriterionFacetWeightsPayload(
                criterion_id="factorization",
                weights=[FacetWeightPayload(facet_id="facet_svd_shape", weight=1.0)],
            )
        ],
        hints=["Think factorization.", "Three factors."],
        capability="procedure_execution",
        task_features=TaskFeaturesPayload(
            complexity=2,
            transfer="near",
            response="short_constructed",
            scaffolding="none",
            span="multi_step",
        ),
        difficulty=0.6,
        retrieval_demand=0.7,
        transfer_distance=0.2,
        scaffold_level=0.0,
        classification_reason="Executes the known factorization procedure.",
    )
    base.update(overrides)
    return ExerciseAuthoredItem(**base)


class FakeClient(StructuredClientFake):
    def __init__(self, result: ExerciseAuthoring | None = None) -> None:
        self.calls: list = []
        self.result = result or ExerciseAuthoring(items=[_item()])

    def run_exercise_authoring(self, context):
        self.calls.append(context)
        return self.result

"""Reader exercise import: verbatim anchoring, deterministic validation of the
AI-authored contract (facets, rubric, depth rung), dedupe, and multi-exercise
split (services/exercise_authoring)."""

from __future__ import annotations

from learnloop.codex.schemas import (
    CriterionFacetWeightsPayload,
    ExerciseAuthoredItem,
    ExerciseAuthoring,
    FacetWeightPayload,
    RubricCriterionPayload,
    RubricPatchPayload,
    TaskFeaturesPayload,
)
from learnloop.services import exercise_authoring as EX
from learnloop.vault.loader import load_vault
from learnloop.vault.yaml_io import write_yaml

import pytest

from tests.test_reader_guidance import _setup

RAW_SELECTION = {
    "nodes": [
        {"spanId": "s1", "quote": "singular value decomposition writes A"},
        {"spanId": "s2", "quote": "columns of U and V"},
    ]
}


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


class FakeClient:
    def __init__(self, result: ExerciseAuthoring | None = None) -> None:
        self.calls: list = []
        self.result = result or ExerciseAuthoring(items=[_item()])

    def run_exercise_authoring(self, context):
        self.calls.append(context)
        return self.result


def _run(tmp_path, repository, client, **kwargs):
    return EX.import_exercises(
        tmp_path / "vault",
        repository,
        client,
        extraction_id="ext1",
        raw_selection=RAW_SELECTION,
        source_id="src1",
        **kwargs,
    )


def test_import_writes_verbatim_anchored_item_with_full_contract(tmp_path):
    _vault, repository = _setup(tmp_path)
    _write_facet_registry(tmp_path)
    client = FakeClient()

    result = _run(tmp_path, repository, client)

    assert result["anchor_status"] == "exact"
    assert len(result["items"]) == 1
    summary = result["items"][0]
    assert summary["capability"] == "procedure_execution"
    assert summary["task_features"]["span"] == "multi_step"
    assert summary["evidence_facets"] == ["facet_svd_shape"]

    vault = load_vault(tmp_path / "vault")
    item = vault.practice_items[summary["practice_item_id"]]
    # The prompt is the source-owned slice of the selection, not the echo.
    assert item.prompt == "singular value decomposition writes A"
    assert item.learning_object_id == "lo_svd_definition"
    assert item.status == "active"
    assert item.capability == "procedure_execution"
    assert item.task_features == {
        "complexity": 2,
        "transfer": "near",
        "response": "short_constructed",
        "scaffolding": "none",
        "span": "multi_step",
    }
    assert item.evidence_weights == {"facet_svd_shape": 1.0}
    assert item.criterion_facet_weights["factors"] == {"facet_svd_shape": 1.0}
    assert item.grading_rubric is not None and len(item.grading_rubric.criteria) == 2
    assert item.hints == ["Think factorization.", "Three factors."]
    assert item.difficulty == 0.6 and item.difficulty_source == "llm_estimate"
    assert item.provenance.origin == "canonical_extract"
    locators = [ref.locator for ref in item.provenance.source_refs]
    assert locators == ["span:ext1/s1", "span:ext1/s2"]
    # The model saw the verbatim selection and the LO catalog.
    context = client.calls[0]
    assert "singular value decomposition writes A" in context.exercise_text
    assert any(lo["id"] == "lo_svd_definition" for lo in context.learning_objects)


def test_import_dedupes_identical_prompt_on_second_run(tmp_path):
    _vault, repository = _setup(tmp_path)
    _write_facet_registry(tmp_path)

    first = _run(tmp_path, repository, FakeClient())
    with pytest.raises(EX.ExerciseAuthoringError, match="already in your practice"):
        _run(tmp_path, repository, FakeClient())

    vault = load_vault(tmp_path / "vault")
    exercise_items = [pid for pid in vault.practice_items if pid.startswith("pi_exercise_")]
    assert exercise_items == [first["items"][0]["practice_item_id"]]


def test_multi_exercise_split_skips_paraphrased_statement(tmp_path):
    _vault, repository = _setup(tmp_path)
    _write_facet_registry(tmp_path)
    client = FakeClient(
        ExerciseAuthoring(
            items=[
                _item(),
                _item(
                    title="Exercise 2",
                    statement_md="a completely paraphrased statement",
                    evidence_facets=["facet_orthonormal_columns"],
                ),
            ]
        )
    )

    result = _run(tmp_path, repository, client)

    assert len(result["items"]) == 1
    assert result["skipped"] == [
        {"title": "Exercise 2", "reason": "statement is not a verbatim excerpt of the selection"}
    ]


def test_single_item_paraphrase_falls_back_to_full_selection(tmp_path):
    _vault, repository = _setup(tmp_path)
    _write_facet_registry(tmp_path)
    client = FakeClient(
        ExerciseAuthoring(items=[_item(statement_md="a completely paraphrased statement")])
    )

    result = _run(tmp_path, repository, client)

    vault = load_vault(tmp_path / "vault")
    item = vault.practice_items[result["items"][0]["practice_item_id"]]
    assert item.prompt == "singular value decomposition writes A\n\ncolumns of U and V"
    assert any("not verbatim" in warning for warning in result["warnings"])


def test_invalid_depth_and_rubric_degrade_without_blocking_the_item(tmp_path):
    _vault, repository = _setup(tmp_path)
    _write_facet_registry(tmp_path)
    client = FakeClient(
        ExerciseAuthoring(
            items=[
                _item(
                    capability="galaxy_brain",
                    grading_rubric=RubricPatchPayload(
                        max_points=4,
                        criteria=[
                            RubricCriterionPayload(id="only", points=1.0, description="Sums wrong.")
                        ],
                    ),
                )
            ]
        )
    )

    result = _run(tmp_path, repository, client)

    vault = load_vault(tmp_path / "vault")
    item = vault.practice_items[result["items"][0]["practice_item_id"]]
    assert item.capability is None and item.task_features is None
    assert item.grading_rubric is not None
    assert [criterion.id for criterion in item.grading_rubric.criteria] == ["correctness"]
    assert any("closed vocabulary" in warning for warning in result["warnings"])
    assert any("rubric failed validation" in warning for warning in result["warnings"])


def test_coordination_without_whole_task_is_left_unstamped(tmp_path):
    _vault, repository = _setup(tmp_path)
    _write_facet_registry(tmp_path)
    client = FakeClient(
        ExerciseAuthoring(items=[_item(capability="coordination")])
    )

    result = _run(tmp_path, repository, client)

    vault = load_vault(tmp_path / "vault")
    item = vault.practice_items[result["items"][0]["practice_item_id"]]
    assert item.capability is None and item.task_features is None
    assert any("span=whole_task" in warning for warning in result["warnings"])


def test_unknown_facets_fall_back_and_unknown_lo_uses_hint(tmp_path):
    _vault, repository = _setup(tmp_path)
    _write_facet_registry(tmp_path)
    client = FakeClient(
        ExerciseAuthoring(
            items=[
                _item(
                    learning_object_id="lo_not_real",
                    evidence_facets=["facet_not_in_registry"],
                    evidence_weights=[FacetWeightPayload(facet_id="facet_not_in_registry", weight=1.0)],
                )
            ]
        )
    )

    result = _run(tmp_path, repository, client, learning_object_hint="lo_svd_definition")

    summary = result["items"][0]
    assert summary["learning_object_id"] == "lo_svd_definition"
    # Legacy LO has no blueprint facets: the item stays gradable with an
    # explicit empty facet contract rather than inventing ids.
    assert summary["evidence_facets"] == []
    vault = load_vault(tmp_path / "vault")
    item = vault.practice_items[summary["practice_item_id"]]
    assert item.evidence_facets == [] and item.evidence_weights == {}
    assert any("used the hint" in warning for warning in result["warnings"])


def test_edited_capture_quote_becomes_the_exercise_surface(tmp_path):
    # The learner fixed an OCR mishap in the capture editor: the edited node
    # quote (flagged `edited`) overrides the extraction slice as the practice
    # text, while anchors/provenance stay extraction-owned.
    _vault, repository = _setup(tmp_path)
    _write_facet_registry(tmp_path)
    edited = "singular value decomposition writes A = UΣV^T"
    client = FakeClient(ExerciseAuthoring(items=[_item(statement_md=edited)]))

    result = EX.import_exercises(
        tmp_path / "vault",
        repository,
        client,
        extraction_id="ext1",
        raw_selection={
            "nodes": [
                {"spanId": "s1", "quote": edited, "edited": True},
                {"spanId": "s2", "quote": "columns of U and V"},
            ]
        },
        source_id="src1",
    )

    summary = result["items"][0]
    assert summary["prompt"] == edited
    # The model context also saw the edited surface.
    assert edited in client.calls[0].exercise_text
    # Provenance still points at the source blocks.
    vault = load_vault(tmp_path / "vault")
    item = vault.practice_items[summary["practice_item_id"]]
    assert [ref.locator for ref in item.provenance.source_refs] == ["span:ext1/s1", "span:ext1/s2"]


def test_selection_level_edited_text_overrides_combined_surface(tmp_path):
    # The capture editor presents a multi-block selection as ONE combined
    # passage; the selection-level edit replaces the whole exercise surface
    # while the per-block nodes keep anchoring the original blocks.
    _vault, repository = _setup(tmp_path)
    _write_facet_registry(tmp_path)
    combined = "singular value decomposition writes A = UΣV^T where the columns of U and V are orthonormal"
    client = FakeClient(ExerciseAuthoring(items=[_item(statement_md=combined)]))

    result = EX.import_exercises(
        tmp_path / "vault",
        repository,
        client,
        extraction_id="ext1",
        raw_selection={**RAW_SELECTION, "edited_text": combined},
        source_id="src1",
    )

    summary = result["items"][0]
    assert summary["prompt"] == combined
    assert client.calls[0].exercise_text == combined
    vault = load_vault(tmp_path / "vault")
    item = vault.practice_items[summary["practice_item_id"]]
    assert [ref.locator for ref in item.provenance.source_refs] == ["span:ext1/s1", "span:ext1/s2"]


def test_unresolvable_selection_raises(tmp_path):
    _vault, repository = _setup(tmp_path)
    client = FakeClient()

    with pytest.raises(EX.ExerciseAuthoringError, match="could not be anchored"):
        EX.import_exercises(
            tmp_path / "vault",
            repository,
            client,
            extraction_id="ext1",
            raw_selection={"nodes": [{"spanId": "s1", "quote": "text that is not in the block"}]},
        )
    assert client.calls == []

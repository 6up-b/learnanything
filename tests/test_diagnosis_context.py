"""Slice 1 §5.2: deterministic ``DiagnosisContext`` assembly."""

from __future__ import annotations

import json

import pytest

from learnloop.diagnosis.split.context import (
    assemble_diagnosis_context,
    current_attempt_from,
    stable_prefix,
)
from learnloop.diagnosis.split.history import (
    HistoryAttempt,
    RepairRecord,
    StaticHistoryStore,
    VaultHistoryStore,
    learning_object_neighborhood,
)
from learnloop.diagnosis.split.settings import DiagnosisSettings

from tests.diagnosis_split_helpers import blind_record, build_diagnosis_vault, seed_history

#: Every key a rendered history row may carry: blind-grade-equivalent only (S3).
ALLOWED_ATTEMPT_KEYS = {
    "attempt_id", "date", "learning_object_id", "relation", "practice_item_id", "surface_group",
    "outcome", "score", "failed_criteria", "fatal_errors", "first_divergence_quotes", "error_types",
    "target_facets", "item_facets", "validity_scopes", "assisted", "primed", "grader_mode",
    "item_prompt", "learner_answer_md",
}


@pytest.fixture()
def seeded(tmp_path):
    paths = build_diagnosis_vault(tmp_path / "vault")
    vault, repository = seed_history(paths)
    return vault, repository


def _current(vault, store, attempt_id="att_06_svd_fail"):
    attempt = store.attempt(attempt_id)
    item = vault.practice_items[attempt.practice_item_id]
    record = blind_record(
        score=2, max_points=4, criteria={"setup": 2, "result": 0},
        attributions=[{
            "error_type": "conceptual_slip", "severity": 0.7, "evidence": "Blind evidence here.",
            "first_divergence": {"anchor_kind": "span", "criterion_id": "result", "quote": "U Sigma V"},
            "target_evidence_families": ["recall"], "target_criterion_ids": ["result"],
            "resolution_status": "unresolved", "validity_scope": "valid_measurement",
        }],
        local_analysis="Blind local reading of this answer.",
    )
    return current_attempt_from(
        vault, item, attempt_id=attempt_id, completed_at=attempt.completed_at,
        learner_answer_md=attempt.learner_answer_md, blind_grade=record,
    )


def test_assembly_and_hash_are_deterministic(seeded):
    vault, repository = seeded
    settings = DiagnosisSettings()
    for mode in ("exact", "full"):
        first = assemble_diagnosis_context(vault, VaultHistoryStore(vault, repository), _current(vault, VaultHistoryStore(vault, repository)), settings, mode=mode)
        second = assemble_diagnosis_context(vault, VaultHistoryStore(vault, repository), _current(vault, VaultHistoryStore(vault, repository)), settings, mode=mode)
        assert first.rendered() == second.rendered()
        assert first.context_hash == second.context_hash
        assert first.receipt == second.receipt


def test_exact_mode_selects_neighbourhood_failures_and_successes_as_of(seeded):
    vault, repository = seeded
    store = VaultHistoryStore(vault, repository)
    assembled = assemble_diagnosis_context(vault, store, _current(vault, store), DiagnosisSettings(), mode="exact")
    failures = [row["attempt_id"] for row in assembled.blocks["failure_history"]]
    successes = [row["attempt_id"] for row in assembled.blocks["success_history"]]
    # Most recent first; facet-overlapping (recall) failures on the LO and its
    # one-hop neighbours, any surface family; the transpose failure's facet
    # does not overlap; the unrelated LO never appears; the later attempt is
    # after the cutoff.
    assert failures == ["att_05_eigen_fail", "att_02_svd_fail"]
    assert successes == ["att_03_svd_pass"]
    rendered = assembled.rendered()
    assert "att_04_unrelated_fail" not in rendered
    assert "att_07_svd_future" not in rendered
    assert assembled.receipt["lagged_attempts"] == 1
    assert assembled.receipt["context_as_of_attempt_id"] == "att_06_svd_fail"


def test_legacy_joint_attempts_are_stripped_of_causal_fields(seeded):
    vault, repository = seeded
    store = VaultHistoryStore(vault, repository)
    for mode in ("exact", "full"):
        assembled = assemble_diagnosis_context(vault, store, _current(vault, store), DiagnosisSettings(), mode=mode)
        rows = [*assembled.blocks.get("failure_history", []), *assembled.blocks.get("success_history", []), *assembled.blocks.get("history", [])]
        assert rows
        for row in rows:
            assert set(row) <= ALLOWED_ATTEMPT_KEYS
            assert row["grader_mode"] == "joint"
        rendered = assembled.rendered()
        # The joint grader's prose, operation label and attribution evidence never leak.
        for leaked in ("Feedback.", "transpose_confusion", "The final factor is not transposed.", "candidate_causes", "misconception_statement"):
            assert leaked not in rendered
        # Typed prior hypotheses ARE shown, with lifecycle status and no prose.
        hypotheses = assembled.blocks["prior_hypotheses"]
        assert hypotheses and all(set(row) == {"id", "kind", "statement", "scope", "status", "validated_evidence_count", "last_updated", "learning_object_id", "target_facets"} for row in hypotheses)


def test_truncation_drops_oldest_first_and_discloses(seeded):
    vault, repository = seeded
    store = VaultHistoryStore(vault, repository)
    assembled = assemble_diagnosis_context(vault, store, _current(vault, store), DiagnosisSettings(), mode="exact", token_budget=1)
    disclosures = assembled.blocks["disclosures"]
    assert disclosures["truncated"] is True
    assert disclosures["dropped"]["attempts"] >= 1
    assert assembled.receipt["dropped"] == disclosures["dropped"]
    roomy = assemble_diagnosis_context(vault, store, _current(vault, store), DiagnosisSettings(), mode="exact")
    assert "truncated" not in roomy.blocks["disclosures"]
    # A budget just under the full size drops exactly the OLDEST failure.
    smaller = assemble_diagnosis_context(vault, store, _current(vault, store), DiagnosisSettings(), mode="exact", token_budget=roomy.tokens - 5)
    assert [row["attempt_id"] for row in smaller.blocks["failure_history"]] == ["att_05_eigen_fail"]
    assert [row["attempt_id"] for row in smaller.blocks["success_history"]] == ["att_03_svd_pass"]
    assert smaller.blocks["disclosures"]["dropped"] == {"attempts": 1, "hypotheses": 0, "registry": 0}


def test_repair_chain_source_is_visible_to_the_diagnoser(seeded):
    vault, _repository = seeded
    item = vault.practice_items["pi_svd_compute_001"]
    source = HistoryAttempt(
        attempt_id="src_1", learning_object_id="lo_svd_compute", practice_item_id=item.id,
        completed_at="2026-05-01T08:00:00Z", surface_group="svd_compute", item_prompt=item.prompt,
        learner_answer_md="U S V", attempt_type="independent_attempt", score=0, max_points=4,
        failed_criteria=("result",), first_divergence_quotes=("U S V",), error_types=("conceptual_slip",),
        target_facets=("recall",), validity_scopes=("valid_measurement",), item_facets=("recall", "compute"),
    )
    store = StaticHistoryStore(
        attempts=[source],
        repairs=[RepairRecord("rc_1", "insert_transpose", ("recall",), ("hyp_1",), 1, 0, source_attempt_id="src_1")],
    )
    current = current_attempt_from(
        vault, item, attempt_id="cur_1", completed_at="2026-05-02T08:00:00Z", learner_answer_md="U S V again",
        blind_grade=blind_record(score=0, max_points=4, criteria={"setup": 0, "result": 0}, attributions=[{"error_type": "conceptual_slip", "target_evidence_families": ["recall"], "validity_scope": "valid_measurement"}]),
    )
    assembled = assemble_diagnosis_context(vault, store, current, DiagnosisSettings(), mode="exact")
    assert assembled.blocks["repair_history"][0]["repair_class_id"] == "rc_1"
    assert assembled.blocks["repair_history"][0]["cold_verifications"] == {"succeeded": 1, "failed": 0}
    assert [row["attempt_id"] for row in assembled.blocks["failure_history"]] == ["src_1"]
    assert "src_1" in assembled.known.attempt_ids


def test_neighbourhood_and_as_of_prerequisite_status(seeded):
    vault, repository = seeded
    neighborhood = learning_object_neighborhood(vault, "lo_svd_compute")
    assert neighborhood.prerequisite_ids == ("lo_transpose",)
    assert neighborhood.confusable_ids == ("lo_eigen",)
    assert neighborhood.same_concept_ids == ("lo_svd_definition",)
    assert "lo_unrelated" not in neighborhood.all_ids()
    store = VaultHistoryStore(vault, repository)
    assembled = assemble_diagnosis_context(vault, store, _current(vault, store), DiagnosisSettings(), mode="exact")
    status = {row["learning_object_id"]: row["as_of_status"] for row in assembled.blocks["neighborhood"]["learning_objects"]}
    assert status["lo_transpose"] == "attempted"
    assert status["lo_svd_compute"] == "demonstrated"
    assert status["lo_svd_definition"] == "untested"
    assert assembled.receipt["prerequisite_refs"] == ["lo_transpose"]


def test_current_attempt_renders_last_with_its_blind_grade(seeded):
    vault, repository = seeded
    store = VaultHistoryStore(vault, repository)
    assembled = assemble_diagnosis_context(vault, store, _current(vault, store), DiagnosisSettings(), mode="exact")
    rendered = assembled.rendered()
    prefix = stable_prefix(rendered)
    tail = rendered[len(prefix):]
    assert tail.startswith(', "current_attempt": ')
    current = json.loads(tail[len(', "current_attempt": '):-1])
    assert current["blind_grade"]["local_analysis_md"] == "Blind local reading of this answer."
    assert current["attempt_id"] == "att_06_svd_fail"


def test_a_stored_grade_without_criterion_rows_is_still_a_non_pass(seeded):
    vault, repository = seeded
    with repository.connection() as connection:
        connection.execute("DELETE FROM grading_evidence WHERE attempt_id = 'att_05_eigen_fail'")
    store = VaultHistoryStore(vault, repository)
    attempt = store.attempt("att_05_eigen_fail")
    assert attempt.non_pass
    assert attempt.failed_criteria == ("correctness",)
    assert attempt.failed_criterion_facets == ("recall",)

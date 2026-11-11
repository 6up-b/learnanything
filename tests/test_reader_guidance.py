from __future__ import annotations

import json

import pytest

from learnloop.algorithm_versions import LATEST_ALGORITHM_VERSION
from learnloop.db.repositories import MasteryState, Repository
from learnloop.diagnosis.split.jobs import DONE, FAILED, PENDING, diagnosis_status
from learnloop.reader.reader_guidance import build_guide_plan
from learnloop.reader import reader_dialogue as RD

from tests.helpers import ALGORITHM_VERSION, NOW_ISO
from tests.split_live_helpers import drain_jobs, submit
from tests.reader_guidance_helpers import (
    _DIAGNOSED,
    _StatementFake,
    _cite_extraction,
    _graded_vault_with_extraction,
    _place_question,
    _setup,
)


def test_unplaced_source_item_never_becomes_a_boundary_question(tmp_path):
    vault, repository = _setup(tmp_path)
    plan = build_guide_plan(vault, repository, extraction_id="ext1")

    assert plan["personalized"] is True
    assert plan["goal_context"]["goal_id"] == "goal_linear_algebra_ml"
    section = plan["sections"][0]
    assert section["end_span_id"] == "s2"
    assert section["question"] is None
    assert section["suggested_passages"][0]["span_id"] == "s1"


def test_reviewed_boundary_placement_connects_question_to_active_goal(tmp_path):
    vault, repository = _setup(tmp_path)
    _place_question(repository)
    plan = build_guide_plan(vault, repository, extraction_id="ext1")

    section = plan["sections"][0]
    assert section["question"]["practice_item_id"] == "pi_svd_define_001"
    assert section["question"]["goal_id"] == "goal_linear_algebra_ml"
    assert section["question"]["reading_phase"] == "after_section"
    assert section["question"]["placement"] == "owner_reviewed"


def test_legacy_placement_uses_only_its_reviewed_familiar_exemplar(tmp_path):
    vault, repository = _setup(tmp_path)
    _place_question(repository, explicit=False)
    plan = build_guide_plan(vault, repository, extraction_id="ext1")

    assert plan["sections"][0]["question"]["practice_item_id"] == "pi_svd_define_001"


def test_dont_bring_this_back_suppresses_the_exact_reviewed_placement(tmp_path):
    vault, repository = _setup(tmp_path)
    _place_question(repository)
    first = build_guide_plan(vault, repository, extraction_id="ext1")
    placement_id = first["sections"][0]["question"]["placement_event_id"]

    RD.question_control(
        repository,
        control="dont_bring_this_back",
        subject_id=placement_id,
        subject_type="reader_question_placement",
    )
    revisited = build_guide_plan(vault, repository, extraction_id="ext1")

    assert revisited["sections"][0]["question"] is None


def test_unresolved_misunderstanding_drives_plain_language_passage_reason(tmp_path):
    vault, repository = _setup(tmp_path)
    repository.upsert_mastery_state(MasteryState(
        learning_object_id="lo_svd_definition", logit_mean=-0.8,
        logit_variance=1.4, evidence_count=2, last_evidence_at=NOW_ISO,
        algorithm_version=ALGORITHM_VERSION, updated_at=NOW_ISO,
    ))
    repository.insert_error_event({
        "id": "err-svd", "learning_object_id": "lo_svd_definition",
        "error_type": "conceptual_slip", "severity": 0.9,
        "is_misconception": True, "status": "active", "created_at": NOW_ISO,
        "misconception_statement": "SVD is the same as eigendecomposition",
    })

    plan = build_guide_plan(vault, repository, extraction_id="ext1")
    passage = plan["sections"][0]["suggested_passages"][0]
    assert passage["learner_signal"] == "recent_misunderstanding"
    assert "SVD is the same as eigendecomposition" in passage["reason"]
    # Posterior parameters influence rank but never leak into the response.
    assert "logit" not in str(plan) and "variance" not in str(plan)


def test_timestamp_provenance_anchors_video_transcript_guidance(tmp_path):
    vault, repository = _setup(
        tmp_path, locator="t=11.5-14.0", extractor_block_id="t=10.0-12.0",
    )
    plan = build_guide_plan(vault, repository, extraction_id="ext1")
    assert plan["sections"][0]["question"] is None
    assert plan["sections"][0]["suggested_passages"][0]["span_id"] == "s1"


# -- the diagnosis overlay (Slice 1 M2 split; reader workbench spec G30) ------

def _svd_passage(plan) -> dict:
    passages = [
        passage
        for passage in plan["sections"][0]["suggested_passages"]
        if passage["learning_object_id"] == "lo_svd_compute"
    ]
    assert len(passages) == 1
    return passages[0]


@pytest.mark.parametrize("version", ["mvp-0.10", LATEST_ALGORITHM_VERSION])
def test_split_guide_reason_names_the_diagnosers_statement(tmp_path, version):
    _paths, vault, repository = _graded_vault_with_extraction(tmp_path, version=version)
    client = _StatementFake()
    result = submit(vault, repository, client)
    drain_jobs(vault, repository, client)

    assert diagnosis_status(repository, result.attempt_id)["status"] == DONE
    # The precondition: the raw row carries only the grader's localization.
    raw = repository.raw_error_events_for_attempt(result.attempt_id)
    assert raw and not any(event["misconception_statement"] for event in raw)

    _cite_extraction(vault)
    passage = _svd_passage(build_guide_plan(vault, repository, extraction_id="ext1"))
    assert passage["learner_signal"] == "recent_misunderstanding"
    assert passage["reason"].startswith("Revisit this to resolve: ")
    assert _DIAGNOSED in passage["reason"]
    assert raw[0]["error_type"].replace("_", " ") not in passage["reason"]


def test_split_guide_falls_back_to_the_error_type_while_the_diagnosis_is_pending(tmp_path):
    _paths, vault, repository = _graded_vault_with_extraction(tmp_path, version="mvp-0.10")
    client = _StatementFake()
    result = submit(vault, repository, client)

    assert diagnosis_status(repository, result.attempt_id)["status"] == PENDING
    error_type = repository.raw_error_events_for_attempt(result.attempt_id)[0]["error_type"]
    _cite_extraction(vault)
    passage = _svd_passage(build_guide_plan(vault, repository, extraction_id="ext1"))
    assert passage["learner_signal"] == "recent_misunderstanding"
    assert passage["reason"] == f"Revisit this to resolve: {error_type.replace('_', ' ')}."
    assert client.calls == ["blind_grading"]


def test_split_guide_falls_back_to_the_error_type_when_the_diagnosis_failed(tmp_path):
    _paths, vault, repository = _graded_vault_with_extraction(
        tmp_path, version="mvp-0.10", config="[diagnosis]\nmax_attempts = 1",
    )
    client = _StatementFake(fail_purposes=("diagnosis",))
    result = submit(vault, repository, client)
    drain_jobs(vault, repository, client)

    assert diagnosis_status(repository, result.attempt_id)["status"] == FAILED
    error_type = repository.raw_error_events_for_attempt(result.attempt_id)[0]["error_type"]
    _cite_extraction(vault)
    passage = _svd_passage(build_guide_plan(vault, repository, extraction_id="ext1"))
    assert passage["reason"] == f"Revisit this to resolve: {error_type.replace('_', ' ')}."


def test_joint_guide_plan_is_unchanged_by_the_overlay_read(tmp_path, monkeypatch):
    """mvp-0.9 parity: the overlaid read returns the raw rows, so the plan is byte-identical.

    A shadow diagnosis runs too: it stores no causal view, so it must never
    reach the Guide.
    """

    _paths, vault, repository = _graded_vault_with_extraction(
        tmp_path, version="mvp-0.9", config="[diagnosis]\nshadow = true",
    )
    client = _StatementFake()
    result = submit(vault, repository, client)
    drain_jobs(vault, repository, client)
    assert repository.latest_attempt_diagnosis(result.attempt_id, mode="shadow") is not None
    joint_statement = repository.raw_error_events_for_attempt(result.attempt_id)[0]["misconception_statement"]
    assert joint_statement

    _cite_extraction(vault)
    plan = build_guide_plan(vault, repository, extraction_id="ext1")
    assert _svd_passage(plan)["reason"] == f"Revisit this to resolve: {joint_statement}."
    assert (
        repository.active_errors_by_learning_object_overlaid("lo_svd_compute")
        == repository.active_errors_by_learning_object("lo_svd_compute")
    )

    # The plan the raw read builds (the pre-fix Guide) is byte-identical.
    monkeypatch.setattr(
        Repository,
        "active_errors_by_learning_object_overlaid",
        Repository.active_errors_by_learning_object,
    )
    raw_plan = build_guide_plan(vault, repository, extraction_id="ext1")
    assert json.dumps(plan, sort_keys=True) == json.dumps(raw_plan, sort_keys=True)


def test_guide_plan_writes_nothing(tmp_path):
    """The Guide is display: building a plan on a split vault changes no row."""

    _paths, vault, repository = _graded_vault_with_extraction(tmp_path, version="mvp-0.10")
    client = _StatementFake()
    submit(vault, repository, client)
    drain_jobs(vault, repository, client)
    _cite_extraction(vault)

    def _snapshot():
        with repository.connection() as connection:
            tables = [
                row[0]
                for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table' ORDER BY name"
                )
            ]
            return {
                table: connection.execute(f'SELECT * FROM "{table}"').fetchall()
                for table in tables
            }

    before = _snapshot()
    build_guide_plan(vault, repository, extraction_id="ext1")
    assert _snapshot() == before


# -- the plan names the diagnoses it waits on (Codex review F1) ---------------


def test_split_guide_plan_names_the_pending_diagnosis_until_it_lands(tmp_path):
    """The Reader refreshes a Guide whose reason waits on a diagnosis: the plan says which."""

    _paths, vault, repository = _graded_vault_with_extraction(tmp_path, version="mvp-0.10")
    client = _StatementFake()
    result = submit(vault, repository, client)
    _cite_extraction(vault)

    pending = build_guide_plan(vault, repository, extraction_id="ext1")
    assert diagnosis_status(repository, result.attempt_id)["status"] == PENDING
    assert pending["pending_diagnosis_attempt_ids"] == [result.attempt_id]
    assert _DIAGNOSED not in _svd_passage(pending)["reason"]

    drain_jobs(vault, repository, client)
    landed = build_guide_plan(vault, repository, extraction_id="ext1")
    assert diagnosis_status(repository, result.attempt_id)["status"] == DONE
    assert landed["pending_diagnosis_attempt_ids"] == []
    assert _DIAGNOSED in _svd_passage(landed)["reason"]


def test_split_guide_plan_waits_on_nothing_once_the_diagnosis_failed(tmp_path):
    """A failed diagnosis is final: the Reader must not poll for it."""

    _paths, vault, repository = _graded_vault_with_extraction(
        tmp_path, version="mvp-0.10", config="[diagnosis]\nmax_attempts = 1",
    )
    client = _StatementFake(fail_purposes=("diagnosis",))
    result = submit(vault, repository, client)
    drain_jobs(vault, repository, client)
    assert diagnosis_status(repository, result.attempt_id)["status"] == FAILED

    _cite_extraction(vault)
    assert build_guide_plan(vault, repository, extraction_id="ext1")["pending_diagnosis_attempt_ids"] == []


def test_split_guide_plan_waits_only_on_diagnoses_behind_its_passages(tmp_path):
    """A pending diagnosis of an LO the source never cites changes nothing on this plan."""

    _paths, vault, repository = _graded_vault_with_extraction(tmp_path, version="mvp-0.10")
    client = _StatementFake()
    result = submit(vault, repository, client)
    assert diagnosis_status(repository, result.attempt_id)["status"] == PENDING

    plan = build_guide_plan(vault, repository, extraction_id="ext1")
    assert not any(
        passage["learning_object_id"] == "lo_svd_compute"
        for section in plan["sections"]
        for passage in section["suggested_passages"]
    )
    assert plan["pending_diagnosis_attempt_ids"] == []


def test_joint_guide_plan_never_waits_on_a_shadow_diagnosis(tmp_path):
    """A queued shadow diagnosis stores no overlay, so a joint plan waits on nothing."""

    _paths, vault, repository = _graded_vault_with_extraction(
        tmp_path, version="mvp-0.9", config="[diagnosis]\nshadow = true",
    )
    client = _StatementFake()
    result = submit(vault, repository, client)
    queued = repository.post_attempt_jobs(attempt_id=result.attempt_id, kind="diagnose", states=("queued",))
    assert [job["payload"]["mode"] for job in queued] == ["shadow"]

    _cite_extraction(vault)
    plan = build_guide_plan(vault, repository, extraction_id="ext1")
    assert _svd_passage(plan)["learner_signal"] == "recent_misunderstanding"
    assert plan["pending_diagnosis_attempt_ids"] == []

"""The M1 probe report (spec §8.3, §10 test_project_report)."""

from __future__ import annotations

import pytest

from learnloop.ai.spend import SpendCaps
from learnloop.config import LearnLoopConfig
from learnloop.ids import new_ulid
from learnloop.projects.ai_runtime import PaidCalls
from learnloop.projects.capture import enroll_repo, sweep
from learnloop.projects.experiment_store import ProjectStore
from learnloop.projects.probes import contest_grade, generate_probes, grade_responses, record_response
from learnloop.projects.report import build_report, build_status, outcome_of_record, render_report
from tests.project_support import ProjectFake, clock_at, fake_resolver, isolated_git, make_model_repo  # noqa: F401

CAPS = SpendCaps(max_candidates=100, max_pairs=0, max_retries=2, max_calls=100, max_total_tokens=10**7, max_estimated_usd=100.0)


@pytest.fixture
def populated(isolated_git, tmp_path):
    vault = tmp_path / "vault"
    vault.mkdir()
    config = LearnLoopConfig()
    store = None
    for index in range(2):
        repo = make_model_repo(tmp_path / f"repo{index}")
        enroll_repo(vault, config, repo.path, clock=clock_at(0))
    sweep(vault, config, clock=clock_at(0))
    store = ProjectStore.for_vault(vault)
    fake = ProjectFake()
    resolver = fake_resolver(fake)
    routes = {role: resolver(None, None, role) for role in ("authoring", "closed_book", "grading")}
    generate_probes(store, vault, config, PaidCalls(store, caps=CAPS, run_id="g"), routes, store.diffs(), clock=clock_at(0))
    first_diff, second_diff = store.diffs()
    store.add_provenance({"id": new_ulid(), "diff_id": first_diff["id"], "accept_style": "all_at_once",
                          "usage_tap": None, "created_at": "2026-10-01T12:00:00Z"})
    a1, a2 = [p for p in store.probes_for_diff(first_diff["id"]) if p["selected"]]
    b1, b2 = [p for p in store.probes_for_diff(second_diff["id"]) if p["selected"]]
    good = record_response(store, a1["id"], kind="answer", answer="relu after scaling", clock=clock_at(8))
    record_response(store, a2["id"], kind="dont_know", clock=clock_at(8))
    record_response(store, b1["id"], kind="answer", answer="it scales", declaration="used_ai", clock=clock_at(9))
    record_response(store, b2["id"], kind="unfair", clock=clock_at(9))
    grade_responses(store, PaidCalls(store, caps=CAPS, run_id="r"), routes["grading"], clock=clock_at(9))
    contest_grade(store, good["id"], score=0.6, note="partly", clock=clock_at(10))
    return store, config, {"good": good, "a1": a1, "b2": b2}


def test_report_figures(populated):
    store, config, refs = populated
    report = build_report(store, config, clock=clock_at(10))
    generation, answers, capture = report["generation"], report["answers"], report["capture"]
    assert capture["diffs"] == 2 and capture["by_agent"] == {"claude_code": 2}
    assert generation["candidates"] == 12
    assert generation["citation_resolution_failures"] == {"n": 12, "count": 2, "rate": 0.1667, "small_sample": False}
    assert generation["closed_book_rejection"]["count"] == 2 and generation["closed_book_rejection"]["n"] == 8
    assert generation["selected"] == 4
    assert generation["cost_per_generated_diff"]["n"] == 2
    assert generation["cost_per_generated_diff"]["mean_calls"] == 3
    assert generation["cost_per_generated_diff"]["cost_labels"] == ["estimated_only"]
    assert answers["by_kind"] == {"answer": 2, "dont_know": 1, "unfair": 1}
    assert answers["unfair_or_ambiguous"]["rate"] == 0.25
    assert answers["contest_rate"] == {"n": 2, "count": 1, "rate": 0.5, "small_sample": True}
    assert answers["accuracy_unassisted"]["mean"] == 0.6  # the adjudication is the outcome of record
    assert answers["accuracy_unassisted_dont_know_as_zero"]["mean"] == 0.3
    assert answers["accuracy_assisted"]["mean"] == 0.5
    by_style = report["by_provenance"]["accept_style"]
    assert by_style["all_at_once"]["accuracy_unassisted"]["mean"] == 0.6
    assert by_style["all_at_once"]["dont_know"]["rate"] == 0.5
    assert by_style["not_reported"]["skip"]["count"] == 0
    assert report["unfair_examples"] == [
        {"probe_id": refs["b2"]["id"], "kind": refs["b2"]["kind"], "question": refs["b2"]["question"]}
    ]
    assert report["manifest"]["generator_models"] == ["fake-model"]
    text = render_report(report)
    assert "closed-book rejections: 25% (2/8) (small sample)" in text
    assert "accuracy (unassisted): 0.60" in text


def test_outcome_of_record_prefers_adjudication():
    assert outcome_of_record({"grade_status": "graded", "score": 0.9, "adjudicated_score": 0.2}) == 0.2
    assert outcome_of_record({"grade_status": "graded", "score": 0.9, "adjudicated_score": None}) == 0.9
    assert outcome_of_record({"grade_status": "pending", "score": None, "adjudicated_score": None}) is None


def test_status_counts_without_question_text(populated):
    store, config, refs = populated
    status = build_status(store, clock=clock_at(10), disclosure=True, include_diffs=True)
    flat = repr(status)
    for probe in store.all_probes():
        assert probe["question"] not in flat
    assert sum(repo["probes_answered"] for repo in status["repos"]) == 4
    disclosure = status["disclosure"][0]
    assert disclosure["model_calls"] >= 3 and disclosure["files_sent"] == ["model.py"]

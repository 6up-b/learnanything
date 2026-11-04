"""FG1c, spec §7: where marks go (the learner state card and the diagnoser's context, as attributed
opinion) and how the sensor is measured (``learnloop data-capture report``)."""

from __future__ import annotations

from contextlib import closing
from datetime import timedelta
import json
import sqlite3

import pytest

from learnloop.attempts.attempts import AttemptDraft, SelfGradeInput, complete_self_graded_attempt
from learnloop.attempts.post_attempt import run_post_attempt_pipeline
from learnloop.daily_plan.router_card import CardGatherer
from learnloop.daily_plan.types import BlockCandidate, PlanState
from learnloop.db.connection import connect
from learnloop.followup_run import marks as panel
from learnloop.followup_serve import marks as M
from learnloop.followup_serve import workflow as wf
from learnloop.ops.capture_report import (
    DELAYED_AGREEMENT_LABEL,
    POSITION_LABEL,
    PROBE_AGREEMENT_LABEL,
    build_report,
    hypothesis_marks_section,
    lines,
)
from learnloop.router.card import CARD_VERSION, MARKS_CARD_SUFFIX, MARKS_SECTION, CardInputs, build_card
from learnloop.vault.loader import load_vault
from learnloop.vault.paths import VaultPaths

from tests.followup_serve_helpers import CLOCK
from tests.helpers import append_config_toml
from tests.test_followup_journey import _call, _generate, journey  # noqa: F401 - the fixture
from tests.test_hypothesis_marks import MARKS_OFF, _mark, _released, _serve_and_answer

NOW = "2099-01-01T00:00:00Z"
LATER = type(CLOCK)(CLOCK.now() + timedelta(days=3))


def _feasible(result):
    state = PlanState(plan_id="p", kind="normal", minutes_budget=25.0, minutes_left=25.0,
                      lane_minutes_left={"maintain": 10.0}, days_since_last_activity=0, streak_days=1,
                      current_block_id=None)
    candidate = BlockCandidate(
        candidate_id="maintain:x", lane="maintain", action="maintain", subtype=None,
        learning_object_ids=(result.learning_object_id,), item_ids=(result.practice_item_id,), reading=None, est_minutes=4.0,
        planner_value=1.0, reason="review", annotations={"reason_code": "review", "reversible": True},
    )
    return state, [candidate]


def _card(vault, repository, result, *, now=NOW):
    state, feasible = _feasible(result)
    return build_card(CardGatherer(vault, repository, session_id="s1").inputs(state, feasible, now_iso=now))


def _versions(marks):
    return [row["hypothesisVersionId"] for row in marks["hypotheses"]]


# -- the learner state card --------------------------------------------------------------------------


def test_with_no_mark_the_card_is_what_it_was_and_a_mark_comes_attributed(journey):
    ctx, vault, repository, result, outcome = journey
    marks = _released(ctx, repository, outcome, result)
    plain = _card(vault, repository, result)
    assert MARKS_SECTION not in plain.json["evidence_sections"] and MARKS_CARD_SUFFIX not in plain.card_version
    assert plain.card_version.startswith(CARD_VERSION)

    statement = marks["hypotheses"][0]["statement"]
    _mark(ctx, result.attempt_id, "my_gap", _versions(marks)[0])
    _mark(ctx, result.attempt_id, "none_of_these", freeText="I read the sign backwards")
    card = _card(vault, repository, result)
    assert card.card_version == plain.card_version + MARKS_CARD_SUFFIX
    assert "their opinion, unmeasured" in card.text
    assert f"this is my gap: {statement}" in card.text
    assert "none of these; in their words: I read the sign backwards" in card.text
    assert {entry["mark"] for entry in card.json["evidence_sections"][MARKS_SECTION]} == {"this is my gap", "none of these"}


def test_the_card_counts_the_latest_and_takes_back_what_was_cleared(journey):
    ctx, vault, repository, result, outcome = journey
    marks = _released(ctx, repository, outcome, result)
    plain = _card(vault, repository, result)
    first = _versions(marks)[0]
    _mark(ctx, result.attempt_id, "my_gap", first)
    _mark(ctx, result.attempt_id, "not_it", first)
    entries = _card(vault, repository, result).json["evidence_sections"][MARKS_SECTION]
    assert [entry["mark"] for entry in entries] == ["not it"]
    _mark(ctx, result.attempt_id, "cleared", first)
    assert _card(vault, repository, result).text == plain.text


def test_the_card_reads_no_mark_from_after_its_own_decision(journey):
    ctx, vault, repository, result, outcome = journey
    marks = _released(ctx, repository, outcome, result)
    _mark(ctx, result.attempt_id, "my_gap", _versions(marks)[0])
    assert MARKS_SECTION not in _card(vault, repository, result, now="2000-01-01T00:00:00Z").json["evidence_sections"]


def test_with_the_switch_off_the_card_is_byte_identical_whatever_rows_exist(journey):
    ctx, vault, repository, result, outcome = journey
    marks = _released(ctx, repository, outcome, result)
    plain = _card(load_vault(vault.root), repository, result)
    _mark(ctx, result.attempt_id, "my_gap", _versions(marks)[0])
    append_config_toml(vault.root, MARKS_OFF)
    off = _card(load_vault(vault.root), repository, result)
    assert off.text == plain.text and off.card_hash == plain.card_hash and off.card_version == plain.card_version


def test_marks_on_protected_work_keep_the_mark_and_never_the_words(journey, monkeypatch):
    ctx, vault, repository, result, outcome = journey
    marks = _released(ctx, repository, outcome, result)
    _mark(ctx, result.attempt_id, "my_gap", _versions(marks)[0])
    _mark(ctx, result.attempt_id, "none_of_these", freeText="WORDS_ABOUT_AN_EXAM")
    monkeypatch.setattr("learnloop.learner_protection.PastWork.evidence_reason", lambda *_a, **_k: "exam_material")
    card = _card(vault, repository, result)
    entries = card.json["evidence_sections"][MARKS_SECTION]
    assert {entry["withheld"] for entry in entries} == {"exam_material"}
    assert all(entry["statement"] is None and entry["learner_text"] is None for entry in entries)
    assert "WORDS_ABOUT_AN_EXAM" not in card.text and marks["hypotheses"][0]["statement"] not in card.text


def test_over_budget_the_marks_go_whole_and_the_version_follows():
    section = {MARKS_SECTION: [{"at": "2026-10-01", "topic": "T", "mark": "partly", "statement": "s" * 400}]}
    inputs = CardInputs(decision={}, session={}, evidence_sections=section)
    fits = build_card(inputs)
    assert fits.card_version.endswith(MARKS_CARD_SUFFIX) and "partly" in fits.text
    without = build_card(CardInputs(decision={}, session={}))
    tight = build_card(inputs, token_budget=without.tokens + 1)
    assert tight.card_version == without.card_version and tight.truncation["dropped_marks_section"] == 1
    assert "partly" not in tight.text


# -- the diagnoser's context -------------------------------------------------------------------------


def test_the_opinion_block_says_whose_it_is_and_is_absent_with_none():
    assert M.opinion_block([]) is None
    assert M.opinion_block([{"hypothesis_key": "k", "mark": "cleared", "created_at": "t", "id": "1"}]) is None
    block = M.opinion_block([
        {"hypothesis_key": "k", "mark": "my_gap", "hypothesis_statement": "S", "created_at": "t1", "id": "1", "probe_answered": 0},
        {"hypothesis_key": "k", "mark": "partly", "hypothesis_statement": "S", "created_at": "t2", "id": "2", "probe_answered": 1},
        {"hypothesis_key": None, "mark": "none_of_these", "free_text": "mine", "created_at": "t3", "id": "3", "probe_answered": 1},
    ])
    assert block["attribution"] == M.ATTRIBUTION
    assert block["marks"] == [
        {"mark": "partly", "marked_at": "t2", "after_the_follow_up_question": True, "cause": "S"},
        {"mark": "none of these", "marked_at": "t3", "after_the_follow_up_question": True, "in_their_words": "mine"},
    ]


def test_a_rediagnosis_reads_the_marks_on_its_own_attempt(journey):
    from learnloop.diagnosis.split.live import current_attempt_for

    ctx, vault, repository, result, outcome = journey
    marks = _released(ctx, repository, outcome, result)
    attempt = repository.fetch_practice_attempt(result.attempt_id)
    plain = current_attempt_for(vault, attempt, {"rubric_score": 0, "max_points": 4}, repository=repository)
    assert "learner_marks" not in plain.render()
    _mark(ctx, result.attempt_id, "not_it", _versions(marks)[0])
    marked = current_attempt_for(vault, attempt, {"rubric_score": 0, "max_points": 4}, repository=repository)
    assert marked.render()["learner_marks"]["marks"][0]["mark"] == "not it"
    append_config_toml(vault.root, MARKS_OFF)
    off = current_attempt_for(load_vault(vault.root), attempt, {"rubric_score": 0, "max_points": 4}, repository=repository)
    assert off.render() == plain.render()


# -- the report --------------------------------------------------------------------------------------


def _report(vault):
    path = VaultPaths(vault.root, vault.config).sqlite_path
    from learnloop.db.repositories import Repository

    with closing(connect(path, read_only=True)) as connection:
        connection.execute("BEGIN")
        return hypothesis_marks_section(connection, vault, Repository.attach(path, read_only=True), success_correctness=0.7)


def test_the_report_measures_marks_against_the_probe_each_labelled_conditional(journey):
    ctx, vault, repository, result, outcome = journey
    _generate(ctx, repository)
    probe, row = _serve_and_answer(ctx, repository, result.attempt_id, outcome)
    observation = repository.causal_discriminating_observations(factor_id=row["factor_id"])[0]
    assert observation["outcome"] == "matched_single"
    bundle = _call(ctx, "get_feedback", {"attemptId": probe.attempt_id})["hypothesisMarks"]
    versions = _versions(bundle)
    _call(ctx, "record_hypothesis_exposure", {"attemptId": result.attempt_id, "surface": "marks_probe_feedback",
                                              "hypothesisVersionIds": versions})
    classified = str(json.loads(json.dumps(observation["classified_as"]))[0])
    other = next(version for version in versions if version != classified)
    _mark(ctx, result.attempt_id, "my_gap", classified, surface="marks_probe_feedback")  # agrees
    _mark(ctx, result.attempt_id, "not_it", other, surface="marks_probe_feedback")  # agrees
    _mark(ctx, result.attempt_id, "none_of_these", surface="marks_probe_feedback")  # disagrees: the probe matched a cause
    section = _report(ctx.require_vault()[0])
    agreement = section["agreement_with_probe_outcomes"]
    assert agreement["label"] == PROBE_AGREEMENT_LABEL and "conditional on being observed" in agreement["label"]
    assert (agreement["agree"], agreement["disagree"], agreement["agreement"]) == (2, 1, 0.6667)
    assert agreement["by_mark_outcome_independence_and_timing"][
        "my_gap|probe_supports|independent_answer|marked_after_the_answer"] == 1
    assert section["marks"]["rows"] == 3 and section["marks"]["latest_by_mark"] == {"my_gap": 1, "not_it": 1, "none_of_these": 1}
    position = section["mark_rates_by_display_position"]
    assert position["label"] == POSITION_LABEL and "conditional on being observed" in position["label"]
    assert position["by_position"]["1"]["shown"] == 1 and position["by_position"]["2"]["shown"] == 1
    assert sum(entry["mark_rate"] for entry in position["by_position"].values()) == 2.0
    coverage = section["exposure_coverage"]
    assert coverage["exposures"] == 1 and coverage["by_surface"] == {"marks_probe_feedback": 1}
    assert coverage["attempts_displayed"] == 1 and coverage["rows_per_active_day"] == 1.0 and coverage["bytes_per_active_day"] > 0


def test_a_not_independent_answer_is_counted_apart_and_partly_is_never_scored(journey):
    ctx, vault, repository, result, outcome = journey
    marks = _released(ctx, repository, outcome, result)
    versions = _versions(marks)
    _mark(ctx, result.attempt_id, "partly", versions[0])
    _mark(ctx, result.attempt_id, "my_gap", versions[1])
    _serve_and_answer(ctx, repository, result.attempt_id, outcome)
    agreement = _report(ctx.require_vault()[0])["agreement_with_probe_outcomes"]
    keys = list(agreement["by_mark_outcome_independence_and_timing"])
    assert keys and all("not_independent_answer" in key and "marked_before_the_answer" in key for key in keys)
    assert agreement["agree"] + agreement["disagree"] == 1
    assert any(key.startswith("partly|") for key in keys)


def test_the_report_measures_marks_against_delayed_performance(journey):
    ctx, vault, repository, result, outcome = journey
    marks = _released(ctx, repository, outcome, result)
    _mark(ctx, result.attempt_id, "my_gap", _versions(marks)[0])
    section = _report(ctx.require_vault()[0])
    assert section["agreement_with_delayed_performance"]["marked_answers_with_no_later_delayed_answer"] == 1
    assert section["agreement_with_delayed_performance"]["agreement"] is None
    later = complete_self_graded_attempt(
        ctx.require_vault()[0], repository,
        AttemptDraft(practice_item_id=result.practice_item_id, learner_answer_md="Later.", attempt_type="independent_attempt",
                     evidence_origin="human"),
        SelfGradeInput(criterion_points={}, confidence=3),
        clock=LATER,
    )
    run_post_attempt_pipeline(ctx.require_vault()[0], repository, result=later, followup_surface=None, clock=LATER)
    delayed = _report(ctx.require_vault()[0])["agreement_with_delayed_performance"]
    assert delayed["label"] == DELAYED_AGREEMENT_LABEL and "conditional on being observed" in delayed["label"]
    assert delayed["named_a_gap"]["later_miss"] + delayed["named_a_gap"]["later_success"] == 1
    assert delayed["agree"] + delayed["disagree"] == 1


def test_the_coverage_row_counts_attempts_with_causes_since_the_first_display(journey):
    ctx, vault, repository, result, outcome = journey
    marks = _released(ctx, repository, outcome, result)
    assert _report(ctx.require_vault()[0])["exposure_coverage"]["coverage"] is None
    with repository.connection() as connection:
        # The attempt's causes were written at the frozen clock; the display at the wall clock.
        first = connection.execute("SELECT MIN(created_at) FROM causal_hypotheses").fetchone()[0]
    _call(ctx, "record_hypothesis_exposure", {"attemptId": result.attempt_id, "surface": "marks_feedback",
                                              "hypothesisVersionIds": _versions(marks), "shownAt": first})
    coverage = _report(ctx.require_vault()[0])["exposure_coverage"]
    assert coverage["attempts_displayed"] == 1 and coverage["attempts_with_causes_since_first_display"] == 0
    assert coverage["coverage"] is None


def test_the_whole_report_carries_the_section_in_json_and_in_words(journey):
    ctx, vault, repository, result, outcome = journey
    marks = _released(ctx, repository, outcome, result)
    _call(ctx, "record_hypothesis_exposure", {"attemptId": result.attempt_id, "surface": "marks_feedback",
                                              "hypothesisVersionIds": _versions(marks)})
    _mark(ctx, result.attempt_id, "my_gap", _versions(marks)[0])
    vault = ctx.require_vault()[0]
    path = VaultPaths(vault.root, vault.config).sqlite_path
    from learnloop.db.repositories import Repository

    with closing(connect(path, read_only=True)) as connection:
        connection.execute("BEGIN")
        report = build_report(connection, vault, Repository.attach(path, read_only=True), as_of=NOW, success_correctness=0.7)
    assert report["switches"]["hypothesis_marks"] is True and report["hypothesis_marks"]["available"] is True
    json.dumps(report, default=str)
    text = "\n".join(lines(report))
    assert "Hypothesis-list exposures: 1" in text and "Marks on possible causes: 1 rows" in text
    assert "conditional on being observed" in text


def test_a_database_below_242_says_so(tmp_path):
    database = tmp_path / "old.sqlite"
    with closing(sqlite3.connect(database)) as connection:
        connection.execute("CREATE TABLE unrelated (id TEXT)")
        connection.row_factory = sqlite3.Row
        section = hypothesis_marks_section(connection, None, None, success_correctness=0.7)
    assert section == {"available": False, "reason": "this database predates migration 242"}

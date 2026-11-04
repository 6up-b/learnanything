"""FG1c's Codex review: F1 (a mark's cause is a derived text its diagnosis read), F3 (probe agreement reads
independence and the shared discriminating contract), F4 and F5 (delayed agreement scores the opinion held
before the outcome, and one optional rejection doesn't reject the list)."""

from __future__ import annotations

from contextlib import closing
from datetime import timedelta
import json
import sqlite3

import pytest

from learnloop.attempts.attempts import AttemptDraft, SelfGradeInput, complete_self_graded_attempt
from learnloop.attempts.grading import resolved_rubric
from learnloop.attempts.post_attempt import run_post_attempt_pipeline
from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.db.stores import write_provenance as wp
from learnloop.diagnosis.split.context import assemble_diagnosis_context
from learnloop.diagnosis.split.history import AttemptRef, VaultHistoryStore
from learnloop.diagnosis.split.live import current_attempt_for
from learnloop.diagnosis.split.provenance import attempt_read, diagnosis_record
from learnloop.diagnosis.split.settings import DiagnosisSettings
from learnloop.diagnosis.split.snapshot import export_snapshot
from learnloop.followup_run import marks as panel
from learnloop.followup_serve import workflow as wf
from learnloop.diagnosis import causal_orchestrator
from learnloop.ops import capture_report
from learnloop.ops.capture_report import build_report, lines
from learnloop.vault.paths import VaultPaths

from tests.followup_serve_helpers import CLOCK, live_miss, live_shape_vault
from tests.test_followup_journey import _generate, journey  # noqa: F401 - the fixture
from tests.test_followup_rival_factor import BlindRivalClient
from tests.test_hypothesis_marks import _released
from tests.test_hypothesis_marks_context import _report, _versions

EXAM_ITEM = "pi_exam_protected_001"
LATER_CUTOFF = "2099-01-01T00:00:00Z"


def _at(days: float = 0.0):
    return type(CLOCK)(CLOCK.now() + timedelta(days=days))


# -- F1: what a diagnosis read ------------------------------------------------------------------------


@pytest.fixture
def marked_miss(tmp_path):
    """A released miss whose first cause was written from protected exam material, marked by the learner."""

    _paths, vault, repository = live_shape_vault(tmp_path, task_features=False)
    result, _outcome = live_miss(vault, repository, BlindRivalClient())
    row = wf.attempt_workflow(repository, result.attempt_id)
    wf.finish(repository, str(row["id"]), to_state=wf.SKIPPED, reason="continue_without_it",
              release=wf.RELEASE_CONTINUE_WITHOUT, clock=CLOCK)
    listed = panel.markable_list(vault, repository, result.attempt_id)
    version = listed.order[0]
    statement = str(listed.hypotheses[0]["statement"])
    with repository.atomic(), repository.connection() as connection:
        wp.record_text_write(connection, kind="hypothesis", record_id=version, text=statement, writer="exam_test",
                             record=wp.WriteRecord(wp.Inputs.of(items=[EXAM_ITEM], solution_items=[EXAM_ITEM])),
                             clock=CLOCK)
    panel.record_mark(vault, repository, attempt_id=result.attempt_id, mark="my_gap", hypothesis_version_id=version,
                      clock=CLOCK)
    return vault, repository, result, version, statement


def test_f1_a_rediagnosis_records_the_cause_it_was_shown_through_a_mark(marked_miss):
    vault, repository, result, version, statement = marked_miss
    current = current_attempt_for(vault, repository.fetch_practice_attempt(result.attempt_id),
                                  {"rubric_score": 0, "max_points": 4}, repository=repository)
    assert current.render()["learner_marks"]["marks"][0]["cause"] == statement
    assembled = assemble_diagnosis_context(vault, VaultHistoryStore(vault, repository), current, DiagnosisSettings(), mode="exact")
    assert ("hypothesis", version, statement) in assembled.reads.records
    with repository.connection() as connection:
        record = diagnosis_record(connection, assembled.reads)
    assert EXAM_ITEM in record.inputs.solution_items and ("hypothesis", version) in record.derived_from


def test_f1_a_history_attempt_folds_the_causes_its_marks_show_as_of_its_cutoff(marked_miss):
    vault, repository, result, version, statement = marked_miss
    store = VaultHistoryStore(vault, repository)

    def shown(cutoff):
        return next(row for row in store.attempts_before(AttemptRef("later", cutoff), None)
                    if row.attempt_id == result.attempt_id)

    assert ("hypothesis", version, statement) in attempt_read(shown(LATER_CUTOFF)).records
    mark_time = shown(LATER_CUTOFF).learner_marks[0]["created_at"]
    assert attempt_read(shown(mark_time)).records == ()


def test_f1_only_the_causes_a_context_still_shows_are_folded(marked_miss):
    vault, repository, result, version, _statement = marked_miss
    panel.record_mark(vault, repository, attempt_id=result.attempt_id, mark="cleared", hypothesis_version_id=version, clock=_at(1))
    panel.record_mark(vault, repository, attempt_id=result.attempt_id, mark="none_of_these", free_text="mine", clock=_at(1))
    row = next(row for row in VaultHistoryStore(vault, repository).attempts_before(AttemptRef("later", LATER_CUTOFF), None)
               if row.attempt_id == result.attempt_id)
    assert attempt_read(row).records == ()


def test_f1_the_snapshot_entry_of_a_marked_attempt_carries_the_cause(marked_miss, tmp_path):
    vault, repository, result, version, statement = marked_miss
    manifest = export_snapshot(vault, VaultHistoryStore(vault, repository), AttemptRef("later", LATER_CUTOFF), tmp_path / "export")
    relative = next(path for path in manifest.entries.entries if path.startswith("attempts/") and result.attempt_id in path)
    assert statement in (tmp_path / "export" / relative).read_text(encoding="utf-8")
    assert ("hypothesis", version, statement) in manifest.entries.entries[relative].records
    assert EXAM_ITEM in manifest.entries.records[relative].inputs.solution_items


# -- F3: agreement with probe outcomes ----------------------------------------------------------------


def _observations(*rows):
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    connection.executescript(
        "CREATE TABLE causal_hypotheses (id TEXT, episode_key TEXT);"
        "CREATE TABLE causal_discriminating_observations (id TEXT, factor_id TEXT, probe_attempt_id TEXT, outcome TEXT, "
        "classified_as_json TEXT, admitted INT, admissible_as_independent INT, declared_keys_observed INT, detail_json TEXT, created_at TEXT);"
    )
    connection.executemany("INSERT INTO causal_hypotheses VALUES (?, ?)", [("v_a", "A"), ("v_b", "B"), ("v_c", "C")])
    for index, row in enumerate(rows):
        connection.execute(
            "INSERT INTO causal_discriminating_observations VALUES (?, ?, 'probe', ?, ?, ?, ?, ?, ?, ?)",
            (f"o{index}", row.get("factor", "f"), row["outcome"], json.dumps(row.get("classified", [])), row.get("admitted", 0),
             row.get("independent", 1), row.get("covered", 1),
             json.dumps({"measured_hypothesis_ids": row.get("measured", ["v_a", "v_b", "v_c"])}), f"t{index}"),
        )
    return connection


def _mark_row(mark, key=None, factor="f"):
    return {"factor_id": factor, "mark": mark, "hypothesis_key": key, "probe_answered": 1}


def test_f3_the_report_and_the_orchestrator_share_one_contract():
    assert capture_report.DISCRIMINATING_OUTCOMES is causal_orchestrator.DISCRIMINATING_OUTCOMES
    assert "matched_multiple" not in capture_report.DISCRIMINATING_OUTCOMES


def test_f3_a_matched_multiple_scores_nothing_and_stays_an_independent_answer():
    agreement = capture_report._probe_agreement(
        _observations({"outcome": "matched_multiple", "classified": ["v_a", "v_b"], "admitted": 0, "independent": 1}),
        [_mark_row("my_gap", "A"), _mark_row("not_it", "C")],
    )
    assert agreement["marks_on_a_probe_that_did_not_discriminate"] == 2
    assert agreement["independent_answers"]["agreement"] is None and agreement["not_independent_answers"]["agreement"] is None
    assert agreement["by_mark_outcome_independence_and_timing"] == {}


@pytest.mark.parametrize("independent, admitted, bucket", [
    (1, 1, "independent_answers"),
    # Admission is a different question: the rival's features went unobserved, and the answer was still clean.
    (1, 0, "independent_answers"),
    (0, 0, "not_independent_answers"),
    # Not assessed is no claim of a clean answer.
    (None, 0, "not_independent_answers"),
])
def test_f3_independence_is_read_from_its_own_field(independent, admitted, bucket):
    agreement = capture_report._probe_agreement(
        _observations({"outcome": "matched_single", "classified": ["v_a"], "admitted": admitted, "independent": independent}),
        [_mark_row("my_gap", "A")],
    )
    assert agreement[bucket] == {"agree": 1, "disagree": 0, "agreement": 1.0}


def test_f3_an_incompletely_measured_no_match_doesnt_confirm_none_of_these():
    agreement = capture_report._probe_agreement(
        _observations({"outcome": "no_bundle_matched", "covered": 0, "measured": ["v_a"]}), [_mark_row("none_of_these")])
    assert agreement["independent_answers"]["agreement"] is None
    assert agreement["none_of_these_on_a_probe_that_did_not_measure_every_cause"] == 1
    assert agreement["by_mark_outcome_independence_and_timing"] == {}


@pytest.mark.parametrize("independent, bucket", [(1, "independent_answers"), (0, "not_independent_answers")])
def test_f3_a_fully_measured_no_match_supports_none_of_these(independent, bucket):
    agreement = capture_report._probe_agreement(
        _observations({"outcome": "no_bundle_matched", "covered": 1, "independent": independent, "admitted": independent}),
        [_mark_row("none_of_these")],
    )
    assert agreement[bucket] == {"agree": 1, "disagree": 0, "agreement": 1.0}
    assert agreement["none_of_these_on_a_probe_that_did_not_measure_every_cause"] == 0


# -- F4 and F5: agreement with delayed performance ------------------------------------------------------


def _answer_again(ctx, repository, result, *, days, success=False):
    """A later delayed answer on the topic: a miss unless ``success``, every criterion earning its points."""

    vault = ctx.require_vault()[0]
    clock = _at(days)
    points = ({criterion.id: criterion.points for criterion in resolved_rubric(vault, vault.practice_items[result.practice_item_id]).criteria}
              if success else {})
    later = complete_self_graded_attempt(
        vault, repository,
        AttemptDraft(practice_item_id=result.practice_item_id, learner_answer_md="Later.", attempt_type="independent_attempt",
                     evidence_origin="human"),
        SelfGradeInput(criterion_points=points, confidence=3),
        clock=clock,
    )
    run_post_attempt_pipeline(vault, repository, result=later, followup_surface=None, clock=clock)
    return later


def _record(ctx, repository, result, mark, version=None, *, days, **extra):
    panel.record_mark(ctx.require_vault()[0], repository, attempt_id=result.attempt_id, mark=mark,
                      hypothesis_version_id=version, clock=_at(days), **extra)


def _delayed(ctx):
    return _report(ctx.require_vault()[0])["agreement_with_delayed_performance"]


def test_f4_a_mark_made_after_the_delayed_answer_scores_nothing_and_is_reported_apart(journey):
    ctx, _vault, repository, result, outcome = journey
    versions = _versions(_released(ctx, repository, outcome, result))
    _answer_again(ctx, repository, result, days=3)
    _record(ctx, repository, result, "my_gap", versions[0], days=4)
    delayed = _delayed(ctx)
    assert delayed["agreement"] is None and delayed["agree"] + delayed["disagree"] == 0
    assert delayed["named_a_gap"] == {"later_success": 0, "later_miss": 0}
    assert delayed["marked_answers_with_no_later_delayed_answer"] == 1
    assert delayed["marked_after_a_delayed_answer"]["named_a_gap"] == {"later_success": 0, "later_miss": 1}


def test_f4_a_mark_after_one_delayed_answer_is_bound_to_the_next(journey):
    ctx, _vault, repository, result, outcome = journey
    versions = _versions(_released(ctx, repository, outcome, result))
    _answer_again(ctx, repository, result, days=3)
    _record(ctx, repository, result, "my_gap", versions[0], days=4)
    _answer_again(ctx, repository, result, days=8)
    delayed = _delayed(ctx)
    assert delayed["named_a_gap"]["later_miss"] == 1 and delayed["agree"] == 1 and delayed["agreement"] == 1.0
    assert delayed["marked_answers_with_no_later_delayed_answer"] == 0


def test_f4_changing_a_mark_after_the_outcome_keeps_the_opinion_held_before_it(journey):
    ctx, _vault, repository, result, outcome = journey
    versions = _versions(_released(ctx, repository, outcome, result))
    _record(ctx, repository, result, "partly", versions[0], days=1)
    _answer_again(ctx, repository, result, days=3)
    _record(ctx, repository, result, "my_gap", versions[0], days=4)
    delayed = _delayed(ctx)
    assert delayed["partly"]["later_miss"] == 1 and delayed["agree"] + delayed["disagree"] == 0
    assert delayed["named_a_gap"] == {"later_success": 0, "later_miss": 0}
    assert delayed["marked_after_a_delayed_answer"]["named_a_gap"]["later_miss"] == 1


def test_f4_an_opinion_taken_back_before_the_outcome_is_not_held(journey):
    ctx, _vault, repository, result, outcome = journey
    versions = _versions(_released(ctx, repository, outcome, result))
    _record(ctx, repository, result, "my_gap", versions[0], days=1)
    _record(ctx, repository, result, "cleared", versions[0], days=2)
    _answer_again(ctx, repository, result, days=3)
    delayed = _delayed(ctx)
    assert delayed["agree"] + delayed["disagree"] == 0 and delayed["marked_answers_with_no_later_delayed_answer"] == 0
    assert sum(delayed["marked_after_a_delayed_answer"][kind]["later_miss"]
               for kind in ("named_a_gap", "partly", "ruled_the_list_out", "rejected_some_causes")) == 0


def test_f5_rejecting_one_of_two_causes_rejects_nothing_else(journey):
    ctx, _vault, repository, result, outcome = journey
    versions = _versions(_released(ctx, repository, outcome, result))
    assert len(versions) == 2
    _record(ctx, repository, result, "not_it", versions[0], days=1)
    _answer_again(ctx, repository, result, days=3)
    delayed = _delayed(ctx)
    assert delayed["ruled_the_list_out"] == {"later_success": 0, "later_miss": 0}
    assert delayed["rejected_some_causes"] == {"later_success": 0, "later_miss": 1}
    assert delayed["agree"] + delayed["disagree"] == 0 and delayed["agreement"] is None


def test_f5_rejecting_every_displayed_cause_rules_the_list_out(journey):
    ctx, _vault, repository, result, outcome = journey
    versions = _versions(_released(ctx, repository, outcome, result))
    for version in versions:
        _record(ctx, repository, result, "not_it", version, days=1)
    _answer_again(ctx, repository, result, days=3)
    delayed = _delayed(ctx)
    assert delayed["ruled_the_list_out"]["later_miss"] == 1 and delayed["disagree"] == 1
    assert delayed["rejected_some_causes"] == {"later_success": 0, "later_miss": 0}


def test_f5_none_of_these_rules_the_list_out(journey):
    ctx, _vault, repository, result, outcome = journey
    _released(ctx, repository, outcome, result)
    _record(ctx, repository, result, "none_of_these", days=1)
    _answer_again(ctx, repository, result, days=3)
    delayed = _delayed(ctx)
    assert delayed["ruled_the_list_out"]["later_miss"] == 1 and delayed["disagree"] == 1


@pytest.mark.parametrize("marks, expected", [
    ([("my_gap", "A"), ("not_it", "B")], "named_a_gap"),
    ([("partly", "A"), ("not_it", "B")], "partly"),
    ([("not_it", "A")], "rejected_some_causes"),
    ([("not_it", "A"), ("not_it", "B")], "ruled_the_list_out"),
    ([("none_of_these", None)], "ruled_the_list_out"),
    ([("not_it", "A"), ("not_it", "B"), ("not_it", "C")], "ruled_the_list_out"),
    # Rejecting every cause of an earlier list says nothing about the one added since.
    ([("not_it", "A"), ("not_it", "B"), ("cleared", "C")], "rejected_some_causes"),
])
def test_f5_each_opinion_has_one_reading(marks, expected):
    keys = {"v_a": "A", "v_b": "B", "v_c": "C"}
    displayed = {"A": ["v_a", "v_b"], "B": ["v_a", "v_b"], "C": ["v_a", "v_b", "v_c"], None: ["v_a", "v_b"]}
    rows = [{"mark": mark, "hypothesis_key": key, "display_order_json": json.dumps(displayed[key])} for mark, key in marks]
    assert capture_report._opinion_reading(rows, keys) == expected


def test_f5_a_later_success_agrees_only_with_ruling_the_whole_list_out(journey):
    ctx, _vault, repository, result, outcome = journey
    _released(ctx, repository, outcome, result)
    _record(ctx, repository, result, "none_of_these", days=1)
    _answer_again(ctx, repository, result, days=3, success=True)
    delayed = _delayed(ctx)
    assert delayed["ruled_the_list_out"]["later_success"] == 1 and delayed["agree"] == 1 and delayed["agreement"] == 1.0


def test_f4_a_later_success_disagrees_with_a_named_gap_and_the_plain_report_says_what_came_after(journey):
    ctx, _vault, repository, result, outcome = journey
    versions = _versions(_released(ctx, repository, outcome, result))
    _record(ctx, repository, result, "my_gap", versions[0], days=1)
    _answer_again(ctx, repository, result, days=3, success=True)
    _record(ctx, repository, result, "partly", versions[1], days=4)
    delayed = _delayed(ctx)
    assert delayed["named_a_gap"]["later_success"] == 1 and delayed["disagree"] == 1
    assert delayed["marked_after_a_delayed_answer"]["named_a_gap"]["later_success"] == 1
    vault = ctx.require_vault()[0]
    path = VaultPaths(vault.root, vault.config).sqlite_path
    with closing(connect(path, read_only=True)) as connection:
        connection.execute("BEGIN")
        report = build_report(connection, vault, Repository.attach(path, read_only=True), as_of=_at(5).now().isoformat(),
                              success_correctness=0.7)
    assert "1 marked or changed after a delayed answer, unscored" in "\n".join(lines(report))

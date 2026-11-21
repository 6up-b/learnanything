"""The stored-row report never credits an unobserved answer or exposes learner prose."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

from tests.check_credit_helpers import DRAWS, SEED, fixture_inputs, offer_with_check, typed, typed_offer
from tests.check_credit_report_helpers import EARLY, NOW, SECRET, add_trace, seed_report_vault


@pytest.fixture(scope="module")
def report():
    path = Path(__file__).resolve().parents[1] / "scripts" / "check_credit_report.py"
    spec = importlib.util.spec_from_file_location("check_credit_report", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def vault(tmp_path):
    return seed_report_vault(tmp_path / "vault")


def test_known_populations(report, vault):
    paths, _ = vault
    data = report.build_report(paths.sqlite_path, as_of=NOW)
    p = data["populations"]
    assert p["lesson_candidates_in_support"] == 10
    assert p["offers_drawn"] == 8
    assert p["offers_shown"] == 5
    assert p["offers_without_shown_receipt"] == 3
    assert p["responses"] == dict(accepted=2, declined=1, ignored=1, superseded=1,
                                  never_shown=1, chose_alternative=1, unanswered=1)
    assert p["linked_lessons"] == {"open": 1, "closed": 2, "not_opened": 0}
    assert p["offered_lesson_entries"]["planned_by_purpose"] == {"retention": 4, "transfer": 1}
    e = p["offered_lesson_entries"]
    assert (e["missing"], e["canonical"], e["cold_answered"], e["helped_only"],
            e["terminally_abandoned"], e["censored"]) == (1, 4, 1, 1, 1, 2)
    assert e["cold_correctness"] == {"correct": 0, "partial": 0, "wrong": 1, "unknown": 0}
    assert (e["due"], e["presented"], e["not_a_trial"]) == (3, 2, 0)


def test_alternative_is_bound_but_never_attributed_to_offered_topic(report, vault):
    data = report.build_report(vault[0].sqlite_path, as_of=NOW)
    p = data["populations"]
    assert p["alternative_lesson_entries"]["missing"] == 1
    assert p["offered_lesson_entries"]["missing"] == 1
    assert p["all_receipt_entries"]["missing"] == 2


def test_as_of_statistics_and_seed_sensitivity(report, vault):
    data = report.build_report(vault[0].sqlite_path, as_of=NOW)
    groups = data["delivery"]["decision_time_groups"]
    assert sorted(g["offers"] for g in groups) == [1, 7]
    early = next(g for g in groups if g["offers"] == 7)["retention"]
    later = next(g for g in groups if g["offers"] == 1)["retention"]
    assert (early["S"], early["F"], early["without_seed"]["predictive_mean"]) == (0, 0, None)
    assert (later["S"], later["F"], later["censored"]) == (1, 2, 2)
    assert later["without_seed"]["predictive_mean"] == pytest.approx(1 / 3)
    assert later["seed_if_unavailable"]["predictive_mean"] == 0.25
    assert later["seed_if_available"]["predictive_mean"] == 0.5
    assert data["delivery"]["now"]["transfer"]["F"] == 1


def test_missing_historical_inputs_are_not_a_guessed_correction(report, vault):
    data = report.build_report(vault[0].sqlite_path, as_of=NOW)
    for key in ("exact_historical", "as_of_reconstruction", "current_copy"):
        c = data["comparisons"][key]
        assert c["computable"] == 0
        assert c["not_computable"] == 8
        assert c["missing_inputs"]
        assert c["values"] is None


def test_paired_worked_fixture(report):
    result = report.paired_scenario(fixture_inputs(), [offer_with_check()],
                                    [typed_offer("offer", typed(delivery=(0, 1)))],
                                    draws=DRAWS, seed=SEED)
    # The design pins p=0.5 separately from the sampler's finite Beta draws.
    row = result["offers"][0]
    assert row["old"]["accepted"] == pytest.approx(0.6)
    assert row["proposed"]["accepted"] == pytest.approx(0.5)
    assert row["old"]["at_half_acceptance"] == pytest.approx(0.524744871, abs=1e-9)
    assert row["proposed"]["at_half_acceptance"] == pytest.approx(0.474744871, abs=1e-9)
    assert row["difference_at_half_acceptance"] == pytest.approx(-0.05)
    assert row["expected_completed_checks"] == row["expected_check_minutes"] == 0


def test_database_is_byte_identical_and_query_only(report, vault):
    paths, _ = vault
    before = hashlib.sha256(paths.sqlite_path.read_bytes()).hexdigest()
    siblings = sorted(p.name for p in paths.sqlite_path.parent.iterdir())
    report.build_report(paths.sqlite_path, as_of=NOW)
    assert hashlib.sha256(paths.sqlite_path.read_bytes()).hexdigest() == before
    assert sorted(p.name for p in paths.sqlite_path.parent.iterdir()) == siblings
    with report.open_repository(paths.sqlite_path) as repo, repo.connection() as db:
        with pytest.raises(Exception, match="readonly|read-only|not authorized"):
            db.execute("DELETE FROM lesson_receipts")


def test_no_vault_text_in_either_output(report, vault, capsys, tmp_path):
    paths, _ = vault
    data = report.build_report(paths.sqlite_path, as_of=NOW)
    output = json.dumps(data) + report.render(data)
    for secret in (SECRET, "lo_svd_definition", "decision-0", "answer-cold", str(paths.root)):
        assert secret not in output
    out = tmp_path / "report.json"
    assert report.main(["--vault", str(paths.sqlite_path), "--as-of", NOW, "--json", "--out", str(out)]) == 0
    assert json.loads(out.read_text())["populations"] == data["populations"]
    assert not capsys.readouterr().out


def test_exact_rounded_and_missing_trace_coverage(report, vault):
    from learnloop.router_objective import types as OT

    paths, repo = vault
    stop = OT.Action(ref=OT.STOP_FOR_TODAY, kind=OT.STOP)
    replay = report.replay_record(fixture_inputs(), [offer_with_check("lesson_offer:0"), stop],
                                  [typed_offer("lesson_offer:0", typed(delivery=(0, 1))), stop], seed=SEED, draws=DRAWS,
                                  as_of=EARLY, options={})
    add_trace(repo, "decision-0", {"check_credit_replay": replay})
    add_trace(repo, "decision-1", {"candidates": {"lesson_offer:1": {
        "terms": {"q": 0.524744871}, "offer": {"terms": {"q_accepted": 0.6, "q_declined": 0.449489743}}}}})
    # A lossless payload for somebody else's action is not this decision's exact replay.
    add_trace(repo, "decision-2", {"check_credit_replay": replay})
    incomplete = report.replay_record(fixture_inputs(), [offer_with_check("lesson_offer:4")],
                                      [typed_offer("lesson_offer:4")], seed=SEED, draws=DRAWS, as_of=EARLY, options={})
    add_trace(repo, "decision-4", {"check_credit_replay": incomplete})
    data = report.build_report(paths.sqlite_path, as_of=NOW)
    exact = data["comparisons"]["exact_historical"]
    assert (exact["computable"], exact["not_computable"]) == (1, 7)
    assert exact["coverage_reasons"] == {"rounded_trace_only": 1, "no_trace": 4,
                                         "invalid_or_unsupported_replay_payload": 2}
    assert exact["values"]["difference"]["mean"] == pytest.approx(-0.05, abs=0.0001)
    assert data["recorded_old_values"]["q"] == {"n": 1, "mean": 0.524745}


def test_current_copy_from_real_builders_is_read_only(report, vault, monkeypatch):
    from learnloop.config import loader
    from learnloop.router_objective import types as OT

    paths, repo = vault
    def forbidden(*args, **kwargs):
        raise AssertionError("credentials or settlement must not be read")
    monkeypatch.setattr(loader, "load_dotenv", forbidden)
    from learnloop.intent import checks

    monkeypatch.setattr(checks, "settle_answered_checks", forbidden)
    # A stored contract plus plan price makes a present-day scenario possible, never historical replay.
    with repo.connection() as db:
        columns = {r[1] for r in db.execute("PRAGMA table_info(daily_plans)")}
    assert "remembered_minutes" in columns
    old = offer_with_check("lesson_offer:0")
    from dataclasses import asdict

    action = asdict(old)
    action["commitments"] = [["lo_svd_definition", 3.0]]
    action["minutes_log_sd"] = 0.0
    add_trace(repo, "decision-0", {"candidates": {"lesson_offer:0": {
        "main_lo": "lo_svd_definition", "offer": {"action": action}}}})
    # Let the full present-day input builder run; supply only the plan's remembered minutes and price rows.
    with repo.connection() as db:
        db.execute("INSERT INTO daily_plans(id,local_date,kind,status,config_hash,created_at,updated_at,remembered_minutes, "
                   "minutes_budget,minutes_source,split_json,admission_json,estimator_version,source,chooser,algorithm_version) "
                   "VALUES ('plan-report','2026-11-10','normal','open','h',?,?,10,10,'chip','{}','{}','v','s','c','mvp-0.61')",
                   (NOW, NOW))
        db.execute("UPDATE attention_blocks SET daily_plan_id='plan-report',decision_ref='decision-0' WHERE id='shown-0'")
        db.commit()
    before = paths.sqlite_path.read_bytes()
    data = report.build_report(paths.root, as_of=NOW, draws=2)
    assert paths.sqlite_path.read_bytes() == before
    assert not data["stop_conditions"]["dependency_requested_write"]
    assert data["comparisons"]["current_copy"]["computable"] == 1
    sensor = data["comparisons"]["current_copy"]["delivery_posteriors"][0]
    assert (sensor["purpose"], sensor["S"], sensor["F"], sensor["alpha"], sensor["beta"],
            sensor["predictive_mean"]) == ("retention", 1, 2, 2.0, 2.0, 0.5)
    assert data["comparisons"]["current_copy"]["mixing_computable"] == 0
    assert data["comparisons"]["exact_historical"]["computable"] == 0
    assert OT.LESSON not in json.dumps(data["comparisons"]["current_copy"]["values"])


def test_clipped_check_minutes_are_charged_without_a_completed_answer(report):
    inputs = fixture_inputs(horizon_days=2.001, dated=(), return_gaps_days=(4.0,))
    row = report.paired_scenario(inputs, [offer_with_check()], [typed_offer()], draws=DRAWS, seed=SEED)["offers"][0]
    assert row["accepted_expected_completed_checks"] == 0
    assert row["accepted_expected_check_minutes"] == pytest.approx(2.88)


def test_current_eligibility_is_reported_separately_from_unknown_historical_seed(report, vault):
    data = report.build_report(vault[0].root, as_of=NOW, draws=2)
    assert data["delivery"]["current_eligibility"]["offers"] == 8
    assert sum(data["delivery"]["current_eligibility"][k] for k in ("available", "unavailable")) == 8


def test_paired_replay_rejects_changes_unrelated_to_checks(report):
    from dataclasses import replace

    old = offer_with_check()
    new = replace(typed_offer(), mass=0.9)
    with pytest.raises(ValueError, match="non-check"):
        report.paired_scenario(fixture_inputs(), [old], [new], draws=DRAWS, seed=SEED)


def test_presentation_on_another_commitment_is_not_attributed(report, vault):
    paths, repo = vault
    with repo.connection() as db:
        db.execute("UPDATE attention_blocks SET commitment_id='unrelated' WHERE id='check-cold'")
        db.commit()
    e = report.build_report(paths.sqlite_path, as_of=NOW)["populations"]["offered_lesson_entries"]
    assert e["presented"] == 1
    assert e["presented_without_commitment_binding"] == 1


def test_missing_response_table_is_a_reported_binding_gap(report, vault):
    paths, repo = vault
    with repo.connection() as db:
        db.execute("DROP TABLE router_suggestion_responses")
        db.commit()
    data = report.build_report(paths.sqlite_path, as_of=NOW)
    assert data["populations"]["binding_gaps"]["router_suggestion_responses_table_missing"] == 8
    assert data["stop_conditions"]["binding_gaps"]


def test_a_dependency_cannot_hide_a_request_to_write(report, vault, monkeypatch):
    import sqlite3

    from learnloop.daily_plan import check_inputs

    def try_write(_vault, repo, _topic):
        try:
            with repo.connection() as db:
                db.execute("UPDATE lessons SET goal_text='forbidden'")
        except sqlite3.Error:
            return False
        raise AssertionError("report allowed a write")

    monkeypatch.setattr(check_inputs, "eligible_now", try_write)
    before = vault[0].sqlite_path.read_bytes()
    data = report.build_report(vault[0].root, as_of=NOW)
    assert vault[0].sqlite_path.read_bytes() == before
    assert data["stop_conditions"]["dependency_requested_write"]


def test_help_in_the_presentation_second_does_not_erase_the_presentation(report, tmp_path):
    paths, _ = seed_report_vault(tmp_path / "simultaneous", presentation_at="2026-11-05T09:00:00Z")
    e = report.build_report(paths.sqlite_path, as_of=NOW)["populations"]["offered_lesson_entries"]
    assert (e["presented"], e["cold_answered"], e["helped_only"]) == (2, 1, 1)

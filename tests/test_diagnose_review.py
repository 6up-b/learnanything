"""Slice 1 §12.1: `learnloop diagnose` end to end with fakes, on a vault copy.

The vault database is only ever read by a run: every model output lands in
the run directory's backup-API scratch copy. The spot-check's arm (a) taps are
the one deliberate vault write (genuine owner adjudications), and
``import-links`` the other.
"""

from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from pathlib import Path

import pytest
from typer.testing import CliRunner

from learnloop.ai.spend import SpendCaps
from learnloop.cli import app
from learnloop.db.repositories import Repository
from learnloop.diagnosis.offline_review.links import import_pattern_links
from learnloop.diagnosis.offline_review.report import ARM_LABELS, offline_review_report, render_markdown
from learnloop.diagnosis.offline_review.runner import (
    ReviewClients,
    ReviewOptions,
    eligible_attempts,
    run_review,
    select_sample,
)
from learnloop.diagnosis.offline_review.spot_check import (
    advance_session,
    build_spot_check_plan,
    record_diagnosis_screen,
    record_grade_screen,
    record_links_screen,
    render_screen,
    start_or_resume_session,
)
from learnloop.vault.loader import load_vault

from tests.diagnosis_fakes import FakeEmbeddingClient, ReviewFakeClient
from tests.diagnosis_split_helpers import build_diagnosis_vault, seed_history

CAPS = SpendCaps(max_calls=2000, max_candidates=500, max_total_tokens=10**8, max_estimated_usd=10.0)
OPTIONS = ReviewOptions(sample_size=10, planted_per_shape=1, repeat_subset=2, sweep_budgets=(2_000,), probe_items=2)


def _snapshot_tables(path: Path) -> dict[str, int]:
    with closing(sqlite3.connect(path)) as connection:
        names = [row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")]
        return {name: connection.execute(f'SELECT COUNT(*) FROM "{name}"').fetchone()[0] for name in names}


def _run(paths, vault, run_dir, *, client=None, options=OPTIONS, caps=CAPS, cancelled=None):
    client = client or ReviewFakeClient()
    clients = ReviewClients(grading=client, diagnosis=client, judge=client, generator=client, embedding=FakeEmbeddingClient())
    result = run_review(vault, source_sqlite=paths.sqlite_path, run_dir=run_dir, options=options, clients=clients, caps=caps, cancelled=cancelled)
    return client, result


@pytest.fixture(scope="module")
def reviewed(tmp_path_factory):
    root = tmp_path_factory.mktemp("review")
    paths = build_diagnosis_vault(root / "vault")
    vault, _repository = seed_history(paths)
    before = _snapshot_tables(paths.sqlite_path)
    client, result = _run(paths, vault, root / "run")
    after = _snapshot_tables(paths.sqlite_path)
    return {"paths": paths, "vault": vault, "run": root / "run", "client": client, "result": result, "before": before, "after": after}


def _scratch_rows(run: Path, sql: str, params=()):
    with closing(sqlite3.connect(run / "scratch.sqlite")) as connection:
        return connection.execute(sql, params).fetchall()


def test_run_writes_only_the_scratch_copy(reviewed):
    result = reviewed["result"]
    assert result["status"] == "complete"
    after = reviewed["after"]
    assert not [name for name in after if name.startswith("review_")]
    assert after == reviewed["before"]
    scratch = _snapshot_tables(reviewed["run"] / "scratch.sqlite")
    assert scratch["review_diagnoses"] > 0 and scratch["review_blind_grades"] > 0


def test_every_arm_and_control_ran(reviewed):
    run = reviewed["run"]
    arms = dict(_scratch_rows(run, "SELECT arm, COUNT(*) FROM review_diagnoses WHERE status = 'completed' GROUP BY arm"))
    targets = dict(_scratch_rows(run, "SELECT kind, COUNT(*) FROM review_targets GROUP BY kind"))
    assert targets == {"real": 6, "planted": 3}
    for arm in ("a", "b", "c", "d", "e"):
        assert arms[arm] == 9, arm
    assert arms["b_prime"] == 2
    assert arms["b0"] == 3
    assert arms["d_sweep_2000"] == 3 and arms["d_sweep_100000"] == 3
    # Planted cases are interleaved among the real ones, unlabelled.
    kinds = [row[0] for row in _scratch_rows(run, "SELECT kind FROM review_targets ORDER BY position")]
    assert kinds != sorted(kinds)
    ledger = dict(_scratch_rows(run, "SELECT task, COUNT(*) FROM judgment_ledger GROUP BY task"))
    for task in ("diagnosis_rating", "diagnosis_pairwise", "diagnosis_best", "same_cause", "planted_cause_match"):
        assert ledger.get(task), task
    judge_models = {row[0] for row in _scratch_rows(run, "SELECT DISTINCT judge_model FROM judgment_ledger WHERE judge = 'llm'")}
    assert judge_models == {"fake-model"}
    probes = dict(_scratch_rows(run, "SELECT probe, COUNT(*) FROM review_probes WHERE status = 'graded' GROUP BY probe"))
    assert probes == {"valid_alternative": 2, "synthetic_error": 2, "paraphrase": 2}
    calls = dict(_scratch_rows(run, "SELECT billing, COUNT(*) FROM review_calls GROUP BY billing"))
    assert calls["subscription"] > 0 and calls["metered"] > 0
    basis = {row[0] for row in _scratch_rows(run, "SELECT DISTINCT cost_basis FROM review_calls WHERE billing = 'subscription'")}
    assert basis == {"estimated_only"}
    receipts = _scratch_rows(run, "SELECT COUNT(*) FROM model_call_receipts WHERE owner_kind = 'diagnosis_review'")[0][0]
    assert receipts > 0


def test_resume_pays_for_nothing_twice(reviewed, tmp_path):
    client = ReviewFakeClient()
    _client, result = _run(reviewed["paths"], reviewed["vault"], reviewed["run"], client=client)
    assert result["status"] == "complete"
    assert client.calls == []


def test_report_is_aggregates_only(reviewed):
    report = offline_review_report(reviewed["run"], vault=reviewed["vault"])
    markdown = render_markdown(report)
    assert "## Is the history-aware diagnoser better?" in markdown
    assert report["run"]["targets"] == {"real": 6, "planted": 3}
    assert report["judge"]["noise_floor"]["b_vs_b_prime_decided_share"] is not None
    with closing(sqlite3.connect(reviewed["run"] / "scratch.sqlite")) as connection:
        answers = [row[0] for row in connection.execute("SELECT learner_answer_md FROM practice_attempts")]
        planted = [json.loads(row[0]) for row in connection.execute("SELECT history_json FROM review_planted_cases")]
    texts = [answer for answer in answers if answer and len(answer) > 3]
    texts += [case["target"]["learner_answer_md"] for case in planted]
    for text in texts:
        assert text not in markdown
        assert text not in json.dumps(report)
    assert report["planted"]["cases"] == 3
    assert report["grader"]["probes"]["valid_alternative"]["false_rejection"]["n"] == 2


def test_sampling_is_seeded_and_stratified(reviewed):
    vault = reviewed["vault"]
    repository = Repository.attach(reviewed["paths"].sqlite_path, read_only=True)
    rows = eligible_attempts(vault, repository)
    assert {row["learning_object_id"] for row in rows} >= {"lo_svd_compute", "lo_transpose", "lo_eigen", "lo_unrelated"}
    first = [row["id"] for row in select_sample(rows, 4, 7)]
    assert first == [row["id"] for row in select_sample(rows, 4, 7)]
    # Four strata pick four different learning objects before any repeats.
    by_id = {row["id"]: row["learning_object_id"] for row in rows}
    assert len({by_id[value] for value in first}) == 4


def test_spot_check_hides_labels_and_is_deterministic(reviewed):
    run, vault = reviewed["run"], reviewed["vault"]
    plan = build_spot_check_plan(run, vault, seed=3)
    assert plan == build_spot_check_plan(run, vault, seed=3)
    assert {screen["kind"] for screen in plan} >= {"diagnoses", "links"}
    targets = {screen["target_id"] for screen in plan}
    assert len(targets) <= 10
    diagnosis_ids = {row[0] for row in _scratch_rows(run, "SELECT id FROM review_diagnoses")}
    labels = [label.lower() for label in ARM_LABELS.values()]
    for screen in plan:
        text = render_screen(screen).lower()
        for leaked in (*labels, "exact", "hybrid", "snapshot", "history_mode", "legacy_view", "b_prime", "fake-model", "planted"):
            assert leaked not in text, leaked
        assert not any(diagnosis_id.lower() in text for diagnosis_id in diagnosis_ids)


def test_spot_check_routes_verdicts_and_resumes(reviewed, tmp_path):
    run, vault, paths = reviewed["run"], reviewed["vault"], reviewed["paths"]
    vault_repository = Repository.attach(paths.sqlite_path)
    session, plan, position = start_or_resume_session(run, vault, seed=11, new=True)
    assert position == 0
    arm_of = dict(_scratch_rows(run, "SELECT id, arm FROM review_diagnoses"))
    kind_of = dict(_scratch_rows(run, "SELECT id, kind FROM review_targets"))
    screen = next(
        screen for screen in plan
        if screen["kind"] == "diagnoses" and kind_of[screen["target_id"]] == "real"
        and any(arm_of[option["diagnosis_id"]] == "a" for option in screen["options"])
    )
    label_a = next(option["label"] for option in screen["options"] if arm_of[option["diagnosis_id"]] == "a")
    label_other = next(option["label"] for option in screen["options"] if arm_of[option["diagnosis_id"]] != "a")
    before_vault = _snapshot_tables(paths.sqlite_path)
    record_diagnosis_screen(run, session_id=session, screen=screen, ratings={label_other: "wrong"}, best=None, vault_repository=vault_repository)
    # A verdict on (b)-(e) never touches the vault database.
    assert _snapshot_tables(paths.sqlite_path) == before_vault
    record_diagnosis_screen(run, session_id=session, screen=screen, ratings={label_a: "right"}, best="none", vault_repository=vault_repository)
    with closing(sqlite3.connect(paths.sqlite_path)) as connection:
        rows = connection.execute(
            "SELECT attempt_id, verdict, queue_reason, adjudicator_source FROM diagnosis_adjudications WHERE attempt_id = ?",
            (screen["attempt_id"],),
        ).fetchall()
    assert rows == [(screen["attempt_id"], "correct", "sampled", "human_owner")]
    owner = _scratch_rows(run, "SELECT task, verdict, detail_json FROM review_judgments WHERE session_id = ? ORDER BY created_at", (session,))
    assert [row[:2] for row in owner] == [("diagnosis_rating", "wrong"), ("diagnosis_rating", "right"), ("diagnosis_best", "none")]
    assert json.loads(owner[1][2])["vault_adjudication"]
    links = next(screen for screen in plan if screen["kind"] == "links")
    record_links_screen(run, session_id=session, screen=links, verdicts=["same"] + [None] * (len(links["links"]) - 1))
    assert record_grade_screen(run, session_id=session, screen={"attempt_id": "x", "grades": []}, choice=None) == []
    advance_session(run, session, 2)
    resumed, resumed_plan, resumed_position = start_or_resume_session(run, vault, seed=99)
    assert (resumed, resumed_position) == (session, 2)
    assert resumed_plan == plan
    fresh, _plan, fresh_position = start_or_resume_session(run, vault, seed=99, new=True)
    assert fresh != session and fresh_position == 0


def test_import_links_appends_real_links_once(reviewed):
    run, paths = reviewed["run"], reviewed["paths"]
    repository = Repository.attach(paths.sqlite_path)
    dry = import_pattern_links(run, repository, dry_run=True)
    assert dry["imported"] > 0 and dry["excluded_planted"] > 0
    with closing(sqlite3.connect(paths.sqlite_path)) as connection:
        assert connection.execute("SELECT COUNT(*) FROM judgment_ledger").fetchone()[0] == 0
    report = import_pattern_links(run, repository)
    assert report["imported"] == dry["imported"]
    planted = {row[0] for row in _scratch_rows(run, "SELECT target_attempt_id FROM review_planted_cases")}
    with closing(sqlite3.connect(paths.sqlite_path)) as connection:
        rows = connection.execute("SELECT task, left_id, right_id, judge FROM judgment_ledger").fetchall()
    assert rows and {row[0] for row in rows} == {"same_cause"}
    assert not {row[1] for row in rows} & planted
    again = import_pattern_links(run, repository)
    assert again["imported"] == 0 and again["already_present"] == report["imported"] + report["already_present"]


def test_over_budget_refuses_before_copying(tmp_path):
    paths = build_diagnosis_vault(tmp_path / "vault")
    vault, _repository = seed_history(paths)
    client, result = _run(paths, vault, tmp_path / "run", caps=SpendCaps(max_calls=3))
    assert result["status"] == "over_budget"
    assert not (tmp_path / "run").exists()
    assert client.calls == []
    assert result["estimate"]["admissible"] is False


def test_cancellation_stops_before_the_next_request(tmp_path):
    paths = build_diagnosis_vault(tmp_path / "vault")
    vault, _repository = seed_history(paths)
    client, result = _run(paths, vault, tmp_path / "run", cancelled=lambda: True)
    assert result["status"] == "cancelled"
    assert client.calls == []


def test_metered_route_with_unknown_price_fails_closed(tmp_path):
    paths = build_diagnosis_vault(tmp_path / "vault")
    vault, _repository = seed_history(paths)
    client, result = _run(paths, vault, tmp_path / "run", client=ReviewFakeClient(provider_type="openai_chat"))
    assert result["status"] == "over_budget"
    assert any("unknown price" in reason for reason in result["estimate"]["reasons"])
    assert client.calls == []


def test_snapshot_arm_is_skipped_with_a_note_without_the_capability(tmp_path):
    paths = build_diagnosis_vault(tmp_path / "vault")
    vault, _repository = seed_history(paths)
    options = ReviewOptions(sample_size=2, arms=("b", "e"), planted_per_shape=0, generate_planted=False, probes=False, judge=False, joint_repeat=False, repeat_subset=0)
    client, result = _run(paths, vault, tmp_path / "run", client=ReviewFakeClient(workspace=False), options=options)
    assert result["status"] == "complete"
    assert "arm_e" in result["manifest"]["notes"]
    statuses = dict(_scratch_rows(tmp_path / "run", "SELECT arm, status FROM review_diagnoses"))
    assert statuses["e"] == "skipped"


def test_cli_dry_run_report_review_and_data_check(reviewed, tmp_path):
    paths = build_diagnosis_vault(tmp_path / "vault")
    seed_history(paths)
    runner = CliRunner()
    result = runner.invoke(app, ["diagnose", "run", "--vault", str(paths.root), "--dry-run", "--json"])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["status"] == "dry_run"
    assert payload["data_check"]["graded_wrong_answers"] == 6
    assert payload["calls"]["diagnosis"] > 0
    assert not (paths.root / ".learnloop" / "diagnose-runs").exists()
    check = runner.invoke(app, ["diagnose", "data-check", "--vault", str(paths.root), "--json"])
    assert json.loads(check.output)["meets_threshold"] is False
    run = reviewed["run"]
    out = tmp_path / "report.md"
    report = runner.invoke(app, ["diagnose", "report", "--run", str(run), "--vault", str(reviewed["paths"].root), "--out", str(out)])
    assert report.exit_code == 0, report.output
    assert out.read_text(encoding="utf-8").startswith("# Slice 1 M1 offline review report")
    assert (run / "report.json").exists() and (run / "review_judgments.json").exists()
    review = runner.invoke(app, ["diagnose", "review", "--run", str(run), "--vault", str(reviewed["paths"].root), "--new-session"], input="q\n")
    assert review.exit_code == 0, review.output
    assert "Saved. Rerun to resume." in review.output


@pytest.mark.durability
def test_review_round_trip_under_production_durability(tmp_path):
    """WAL source, backup-API scratch copy, resumable writes: production pragmas."""

    paths = build_diagnosis_vault(tmp_path / "vault")
    vault, _repository = seed_history(paths)
    before = _snapshot_tables(paths.sqlite_path)
    options = ReviewOptions(sample_size=3, arms=("a", "b", "d"), planted_per_shape=0, generate_planted=False, probes=False, repeat_subset=1)
    client, result = _run(paths, vault, tmp_path / "run", options=options)
    assert result["status"] == "complete"
    assert _snapshot_tables(paths.sqlite_path) == before
    statuses = {row[0] for row in _scratch_rows(tmp_path / "run", "SELECT status FROM review_diagnoses")}
    assert statuses == {"completed"}
    resumed, again = _run(paths, vault, tmp_path / "run", client=ReviewFakeClient(), options=options)
    assert again["status"] == "complete" and resumed.calls == []
    report = offline_review_report(tmp_path / "run", vault=vault)
    assert report["run"]["targets"] == {"real": 3}

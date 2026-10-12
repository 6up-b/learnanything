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
    probes = dict(_scratch_rows(run, "SELECT probe, COUNT(*) FROM review_probes WHERE status = 'graded' AND probe != 'synthetic_error' GROUP BY probe"))
    assert probes == {"valid_alternative": 2, "paraphrase": 2}
    # A synthetic error is graded only when its wrongness is verified (a
    # numeric reference here); otherwise it is excluded, never "known".
    synthetic = dict(_scratch_rows(run, "SELECT practice_item_id, status FROM review_probes WHERE probe = 'synthetic_error'"))
    vault = reviewed["vault"]
    assert len(synthetic) == 2
    assert synthetic == {
        item_id: "graded" if str(vault.practice_items[item_id].expected_answer).strip().isdigit() else "unverified"
        for item_id in synthetic
    }
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


def test_a_run_without_grader_or_diagnoser_refuses_before_copying(tmp_path):
    paths = build_diagnosis_vault(tmp_path / "vault")
    vault, _repository = seed_history(paths)
    result = run_review(
        vault, source_sqlite=paths.sqlite_path, run_dir=tmp_path / "run", options=OPTIONS,
        clients=ReviewClients(judge=ReviewFakeClient(), notes={"diagnosis": "not ready: manual"}), caps=CAPS,
    )
    assert result["status"] == "unavailable"
    assert result["reason"] == "no ready route for grading, diagnosis"
    assert not (tmp_path / "run").exists()


def test_rejected_planted_drafts_are_recorded_and_never_redrafted(tmp_path):
    paths = build_diagnosis_vault(tmp_path / "vault")
    vault, _repository = seed_history(paths)
    options = ReviewOptions(sample_size=2, arms=("b",), planted_per_shape=1, probes=False, judge=False, joint_repeat=False, repeat_subset=0)
    client = ReviewFakeClient(fail_purposes=("diagnosis_planted_scenario",))
    client, result = _run(paths, vault, tmp_path / "run", client=client, options=options)
    assert result["status"] == "complete"
    rejected = result["manifest"]["notes"]["planted_rejected"]
    assert len(rejected) == 6  # two drafts per wanted case, three shapes
    assert {row["reason"] for row in rejected} == {"AIProviderUnavailable"}
    assert client.calls.count("diagnosis_planted_scenario") == 6
    resumed, again = _run(paths, vault, tmp_path / "run", client=ReviewFakeClient(), options=options)
    assert again["status"] == "complete"
    assert "diagnosis_planted_scenario" not in resumed.calls


def test_a_diagnosis_repaired_on_resume_is_judged_and_only_the_current_revision_counts(tmp_path):
    """F10: judgment checkpoints are keyed by the exact candidates, not the target."""

    paths = build_diagnosis_vault(tmp_path / "vault")
    vault, _repository = seed_history(paths)
    options = ReviewOptions(sample_size=3, arms=("a", "b", "d"), planted_per_shape=1, probes=False, sweep=False,
                            repeat_subset=0, joint_repeat=False)
    _client, first = _run(paths, vault, tmp_path / "run", client=ReviewFakeClient(fail_modes=("full",)), options=options)
    assert first["status"] == "complete"
    assert {row[0] for row in _scratch_rows(tmp_path / "run", "SELECT status FROM review_diagnoses WHERE arm = 'd'")} == {"failed"}
    _client, resumed = _run(paths, vault, tmp_path / "run", client=ReviewFakeClient(), options=options)
    assert resumed["status"] == "complete"
    d_ids = [row[0] for row in _scratch_rows(tmp_path / "run", "SELECT id FROM review_diagnoses WHERE arm = 'd' AND status = 'completed'")]
    assert d_ids
    for diagnosis_id in d_ids:
        passes = _scratch_rows(tmp_path / "run", "SELECT COUNT(*) FROM judgment_ledger WHERE task = 'diagnosis_rating' AND left_id = ?", (diagnosis_id,))[0][0]
        assert passes == 2, diagnosis_id
    planted_d = _scratch_rows(
        tmp_path / "run",
        "SELECT COUNT(*) FROM judgment_ledger j JOIN review_diagnoses d ON d.id = j.left_id "
        "WHERE j.task = 'planted_cause_match' AND d.arm = 'd'",
    )[0][0]
    assert planted_d >= 1
    report = offline_review_report(tmp_path / "run", vault=vault)
    targets_with_a = _scratch_rows(tmp_path / "run", "SELECT COUNT(*) FROM review_diagnoses WHERE arm = 'a' AND status = 'completed'")[0][0]
    # Arm (a) was rated in both revisions; the report counts only the current one.
    assert sum(report["judge"]["ratings"]["a"]["distribution"].values()) == 2 * targets_with_a
    assert sum(report["judge"]["ratings"]["d"]["distribution"].values()) == 2 * len(d_ids)


def _link_data(passes: dict[int, str]):
    from learnloop.diagnosis.offline_review import judge as judging

    claim = {"hypothesis_ref": "cause:0:0", "relation": "same_mechanism", "cited": [{"attempt_id": "att_x", "quote": "q"}]}
    diagnoses = [
        {"id": "dc", "target_id": "t1", "arm": "c", "status": "completed", "proposal": {"analysis_md": "a", "pattern_claims": [claim]}},
        {"id": "dd", "target_id": "t1", "arm": "d", "status": "completed", "proposal": {"analysis_md": "a", "pattern_claims": []}},
    ]
    revision = judging.link_judgment_revision(["att_x"])
    ledger = [
        {"left_id": "att_t", "right_id": "att_x", "verdict": verdict, "rationale": {"pass": index, "revision": revision, "arms": ["c"]}}
        for index, verdict in passes.items()
    ]
    return {
        "review_targets": [{"id": "t1", "attempt_id": "att_t", "kind": "real"}],
        "review_diagnoses": diagnoses,
        "review_context_receipts": {},
        "ledger:same_cause": ledger,
    }


def test_one_judge_pass_is_never_reported_as_a_confirmed_link():
    """F15: a link is confirmed only when BOTH passes judged it the same."""

    from learnloop.diagnosis.offline_review.report import _links_section

    single = _links_section(_link_data({0: "same"}))
    arm = single["by_arm"]["c"]
    assert arm["judged_same_both_passes"] == 0
    assert arm["incomplete_pairs"] == 1
    assert arm["confirmed_links_unique_to_arm"] == 0
    assert arm["same_share"]["n"] == 0
    both = _links_section(_link_data({0: "same", 1: "same"}))["by_arm"]["c"]
    assert (both["judged_same_both_passes"], both["incomplete_pairs"], both["confirmed_links_unique_to_arm"]) == (1, 0, 1)


def _e4_data(*, blind_order=("B", "A"), extra_blind=False):
    spans = {"A": ("first wrong step", 0, 16, "recall", "mc_a"), "B": ("second wrong step", 20, 37, "compute", "mc_b")}

    def divergence(key):
        quote, start, end, _facet, _mc = spans[key]
        return {"anchor_kind": "span", "quote": quote, "char_start": start, "char_end": end}

    stored = [
        {"misconception_id": spans[key][4], "error_type": "conceptual_slip",
         "repair_plan": {"first_divergence": divergence(key), "target_evidence_families": [spans[key][3]]}}
        for key in ("A", "B")
    ]
    attributions = [
        {"index": index, "error_type": "conceptual_slip", "first_divergence": divergence(key),
         "target_evidence_families": [spans[key][3]], "validity_scope": "valid_measurement"}
        for index, key in enumerate(blind_order)
    ]
    if extra_blind:
        attributions.append({"index": len(attributions), "error_type": "conceptual_slip",
                             "first_divergence": {"anchor_kind": "span", "quote": "elsewhere", "char_start": 50, "char_end": 59},
                             "target_evidence_families": ["other"], "validity_scope": "valid_measurement"})
    events = [
        {"event_index": index, "registry_match": {"kind": "durable", "id": spans[key][4]}}
        for index, key in enumerate(blind_order)
    ]
    if extra_blind:
        events.append({"event_index": len(events), "registry_match": {"kind": "durable", "id": "mc_c"}})
    return {
        "review_targets": [{"id": "t1", "attempt_id": "att_t", "kind": "real"}],
        "review_diagnoses": [{"id": "d1", "target_id": "t1", "arm": "b", "status": "completed", "proposal": {"event_diagnoses": events}}],
        "review_blind_grades": [{"attempt_id": "att_t", "purpose": "primary", "status": "completed", "record": {"error_attributions": attributions}}],
        "stored_misconceptions": {"att_t": [row["misconception_id"] for row in stored]},
        "stored_error_events": {"att_t": stored},
    }


def test_e4_aligns_events_by_localization_and_target_not_list_position():
    """F14: joint A/B vs blind B/A with correct registry matches is full agreement."""

    from learnloop.diagnosis.offline_review.report import _registry_section

    section = _registry_section(_e4_data())["b"]
    assert section["agreement_where_either_linked"]["n"] == 2
    assert section["agreement_where_either_linked"]["rate"] == 1.0
    assert section["disagreements"] == []
    extra = _registry_section(_e4_data(extra_blind=True))["b"]
    assert extra["agreement_where_either_linked"]["n"] == 2
    assert extra["unmatched_blind_events"] == 1


def _prime_item(tmp_path):
    paths = build_diagnosis_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    return vault, vault.practice_items["pi_unrelated_001"]  # reference "2"


def test_a_valid_alternative_is_verified_on_its_submitted_derivation(tmp_path):
    """F4: the derivation the grader sees must state the verified answer and hold."""

    from learnloop.diagnosis.offline_review.probes import ValidAlternativeDraft, verify_alternative

    _vault, item = _prime_item(tmp_path)
    wrong = ValidAlternativeDraft(method_note="m", derivation_md="1+1=99. Therefore 99.", final_answer="2")
    assert verify_alternative(item, wrong)["status"] != "verified"
    false_step = ValidAlternativeDraft(method_note="m", derivation_md="2*3 = 7, and the smallest prime is\n2", final_answer="2")
    assert verify_alternative(item, false_step)["status"] != "verified"
    right = ValidAlternativeDraft(method_note="m", derivation_md="Every even number above 2 is composite, and 1+1 = 2.\nThe answer is 2.", final_answer="2")
    assert verify_alternative(item, right)["status"] == "verified"


def test_a_synthetic_error_is_known_only_when_the_planted_error_is_verified(tmp_path):
    """F4: a generator's declaration never makes a correct answer score zero."""

    from learnloop.diagnosis.offline_review.probes import SyntheticErrorDraft, verify_synthetic_error

    vault, item = _prime_item(tmp_path)
    correct = SyntheticErrorDraft(planted_criterion_id="correctness", error_description="d", answer_md="The answer is 2.", final_answer="2")
    assert verify_synthetic_error(vault, item, correct)["status"] != "verified_wrong"
    planted = SyntheticErrorDraft(planted_criterion_id="correctness", error_description="d", answer_md="4 has no divisors, so the answer is 4.", final_answer="4")
    check = verify_synthetic_error(vault, item, planted)
    assert check["status"] == "verified_wrong"
    assert check["known_full_marks"] is False
    unstated = SyntheticErrorDraft(planted_criterion_id="correctness", error_description="d", answer_md="The answer is 2.", final_answer="4")
    assert verify_synthetic_error(vault, item, unstated)["status"] != "verified_wrong"
    invalid = SyntheticErrorDraft(planted_criterion_id="nope", error_description="d", answer_md="The answer is 4.", final_answer="4")
    assert verify_synthetic_error(vault, item, invalid)["status"] == "invalid_criterion"


def test_sympy_never_sees_model_text_outside_a_safe_math_alphabet():
    from learnloop.diagnosis.offline_review.probes import safe_math_text

    assert safe_math_text("2*x + 1")
    assert safe_math_text("sqrt(2)/2")
    assert not safe_math_text("__import__('os')")
    assert not safe_math_text("open(1)")
    assert not safe_math_text("x.__class__")


PROBE_OPTIONS = ReviewOptions(sample_size=6, arms=("b",), planted_per_shape=0, generate_planted=False, judge=False, sweep=False,
                              joint_repeat=False, repeat_subset=0, probe_items=5)


def test_failed_probes_are_retried_on_resume_without_regenerating_paid_inputs(tmp_path):
    """F12: generation/grading failures are retryable; drafts and probe ids persist."""

    paths = build_diagnosis_vault(tmp_path / "vault")
    vault, _repository = seed_history(paths)
    run = tmp_path / "run"
    first_client = ReviewFakeClient(
        fail_purposes=("diagnosis_paraphrase",),
        fail_when=lambda purpose, prompt: purpose == "blind_grading" and "By another route" in prompt,
    )
    _client, first = _run(paths, vault, run, client=first_client, options=PROBE_OPTIONS)
    assert first["status"] == "complete"
    statuses = dict(_scratch_rows(run, "SELECT probe || ':' || practice_item_id, status FROM review_probes"))
    assert {value for key, value in statuses.items() if key.startswith("valid_alternative")} == {"grading_failed"}
    assert {value for key, value in statuses.items() if key.startswith("paraphrase")} == {"generation_failed"}
    probe_ids = {
        row[0]: json.loads(row[1])["probe_attempt_id"]
        for row in _scratch_rows(run, "SELECT practice_item_id, detail_json FROM review_probes WHERE probe = 'valid_alternative'")
    }
    excluded_before = {key: value for key, value in statuses.items() if value in {"unverified", "invalid_criterion", "not_wrong"}}
    client = ReviewFakeClient()
    _client, resumed = _run(paths, vault, run, client=client, options=PROBE_OPTIONS)
    assert resumed["status"] == "complete"
    after = dict(_scratch_rows(run, "SELECT probe || ':' || practice_item_id, status FROM review_probes"))
    assert {value for key, value in after.items() if key.startswith(("valid_alternative", "paraphrase"))} == {"graded"}
    # The persisted draft was re-graded under its stable probe id: no regeneration.
    assert "diagnosis_valid_alternative" not in client.calls
    assert client.calls.count("diagnosis_paraphrase") == sum(1 for key in statuses if key.startswith("paraphrase"))
    for item_id, probe_id in probe_ids.items():
        detail = json.loads(_scratch_rows(run, "SELECT detail_json FROM review_probes WHERE probe = 'valid_alternative' AND practice_item_id = ?", (item_id,))[0][0])
        assert detail["probe_attempt_id"] == probe_id
    # Deliberately excluded probes stay excluded and are never re-paid.
    assert {key: after[key] for key in excluded_before} == excluded_before
    # The verified synthetic error on the numeric item was graded and is reported.
    assert after.get("synthetic_error:pi_unrelated_001") == "graded"
    report = offline_review_report(run, vault=vault)
    assert report["grader"]["probes"]["real_vs_synthetic"]["synthetic_n"] == 1

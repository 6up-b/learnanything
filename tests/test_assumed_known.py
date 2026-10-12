"""Learner field F2 (Slice A Phase 6): starting new material without ceremony.

Spec: ``spec_learner_field_v1.md`` §5.2, gates G4, G7-G9; §9 ``test_assumed_known``.
"""

from __future__ import annotations

from datetime import timedelta
import json
import sqlite3

import pytest

from learnloop.attempts.attempts import AttemptDraft, SelfGradeInput, complete_self_graded_attempt
from learnloop.clock import FrozenClock
from learnloop.content.authoring.item_authoring import retire_item
from learnloop.db.repositories import Repository
from learnloop.diagnosis.probe_episodes import maybe_reprobe_for_misconception
from learnloop.placement.decisions import (
    PlacementInactive,
    reconcile_fast_track,
    reconcile_predictor_assumptions,
    record_self_report,
)
from learnloop.placement.predictor import LiveMasteryPredictor, active_predictor
from learnloop.placement.rules import AnswerFacts, fast_track_verdict, theta_known
from learnloop.placement.state import load_placement_state, placement_active
from learnloop.scheduling.scheduler import SchedulerSession, build_due_queue
from learnloop.substrate.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault

from tests.helpers import NOW, create_placement_vault

LOW_Q = "[placement]\nfast_track_q = 0.51\n"

EVIDENCE_TABLES = (
    "practice_attempts",
    "grading_evidence",
    "learning_object_mastery",
    "facet_recall_state",
    "facet_capability_evidence",
    "practice_item_state",
    "coldness_receipts",
    "learner_claims",
    "certification_cold_probe_outcomes",
    "error_events",
)


def _setup(tmp_path, *, version="mvp-0.10", placement_toml=None, name="vault"):
    paths = create_placement_vault(tmp_path / name, version=version, placement_toml=placement_toml)
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    sync_vault_state(vault, repository, clock=FrozenClock(NOW))
    return paths, vault, repository


def _at(minutes: float):
    return FrozenClock(NOW + timedelta(minutes=minutes))


def _answer(vault, repository, item_id, points=4.0, *, minutes, hints=0, session_id=None):
    return complete_self_graded_attempt(
        vault,
        repository,
        AttemptDraft(
            practice_item_id=item_id,
            learner_answer_md="An answer.",
            hints_used=hints,
            attempt_type="hinted_attempt" if hints else "independent_attempt",
            session_id=session_id,
        ),
        SelfGradeInput(criterion_points={"correctness": points}, confidence=4),
        clock=_at(minutes),
    )


def _queue(vault, repository, minutes, *, persist=True, session_id=None):
    return build_due_queue(
        vault,
        repository,
        clock=_at(minutes),
        session=SchedulerSession(session_id=session_id),
        persist_explanations=persist,
    )


def _snapshot(paths) -> dict[str, list[tuple]]:
    snapshot = {}
    with sqlite3.connect(paths.sqlite_path) as connection:
        for table in EVIDENCE_TABLES:
            if connection.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)
            ).fetchone() is None:
                continue
            snapshot[table] = sorted(
                tuple(str(value) for value in row) for row in connection.execute(f"SELECT * FROM {table}")
            )
    return snapshot


def _decisions(paths) -> list[dict]:
    with sqlite3.connect(paths.sqlite_path) as connection:
        connection.row_factory = sqlite3.Row
        return [dict(row) for row in connection.execute("SELECT * FROM assumption_decisions ORDER BY created_at, id")]


def _served(queue) -> list[str]:
    return [scheduled.practice_item_id for scheduled in queue]


# ── No opening probes; new material starts as learning ──────────────────────


def test_no_initial_episodes_for_new_los_and_new_material_is_served_in_order(tmp_path):
    _paths, vault, repository = _setup(tmp_path)

    assert placement_active(vault)
    assert repository.open_probe_episodes() == {}
    queue = _queue(vault, repository, 1, persist=False)
    new = [s for s in queue if s.components.get("new_material")]
    # Every never-practised LO outside a goal enters as learning.
    assert {s.learning_object_id for s in new} == {"lo_eigen_basics", "lo_spectral", "lo_diag"}
    assert all(s.priority > 0 for s in new)
    assert all("new material: starts as learning, no opening probe" in s.plain_english for s in new)
    # Prerequisites first: lo_spectral (needs eigenvalues) comes after layer 0;
    # within a layer, easiest first by the incumbent's predicted success.
    layers = [s.components["placement_layer"] for s in new]
    assert layers == sorted(layers)
    assert {s.learning_object_id for s in new if s.components["placement_layer"] == 1.0} == {"lo_spectral"}
    layer0 = [s.components["placement_predicted_success"] for s in new if s.components["placement_layer"] == 0.0]
    assert layer0 == sorted(layer0, reverse=True)


def test_error_driven_episodes_still_open_under_placement(tmp_path):
    _paths, vault, repository = _setup(tmp_path)
    # A wrong answer that leaves a real choice of repair still opens diagnosis.
    episode = maybe_reprobe_for_misconception(vault, repository, "lo_diag", severity=0.9, clock=_at(5))
    assert episode is not None and episode.trigger == "misconception"
    # And an explicitly entered episode keeps its LO on the probe path.
    queue = _queue(vault, repository, 6, persist=False)
    assert not any(s.components.get("new_material") for s in queue if s.learning_object_id == "lo_diag")


def test_initial_probes_switch_restores_opening_episodes_only(tmp_path):
    _paths, vault, repository = _setup(tmp_path, placement_toml="[placement]\ninitial_probes = true\n")
    assert placement_active(vault)
    assert {lo: e.trigger for lo, e in repository.open_probe_episodes().items()} == {
        "lo_diag": "initial", "lo_eigen_basics": "initial", "lo_spectral": "initial", "lo_svd_definition": "initial",
    }


# ── G9: the kill switch restores the predecessor exactly ─────────────────────


def _serving_fingerprint(vault, repository, minutes):
    queue = _queue(vault, repository, minutes, persist=False)
    episodes = sorted(
        (lo, episode.trigger, episode.status, episode.hypothesis_set_id is not None)
        for lo, episode in repository.open_probe_episodes().items()
    )
    return episodes, [
        (s.practice_item_id, s.learning_object_id, round(s.priority, 12),
         sorted((k, round(v, 12)) for k, v in s.components.items()))
        for s in queue
    ]


def test_kill_switch_restores_initial_probes_serving_and_ordering_exactly(tmp_path):
    _p0, baseline_vault, baseline_repo = _setup(tmp_path, version="mvp-0.9", name="baseline")
    paths, vault, repository = _setup(
        tmp_path, placement_toml="[placement]\nenabled = false\n", name="switched_off",
    )
    assert not placement_active(vault)
    assert _serving_fingerprint(vault, repository, 2) == _serving_fingerprint(baseline_vault, baseline_repo, 2)


def test_kill_switch_ignores_assumptions_made_while_on(tmp_path):
    paths, vault, repository = _setup(tmp_path)
    record_self_report(vault, repository, learning_object_ids=["lo_diag"], report="know_this", clock=_at(1))
    assert "pi_diag_easy" not in _served(_queue(vault, repository, 2, persist=False))

    text = (paths.root / "learnloop.toml").read_text()
    (paths.root / "learnloop.toml").write_text(text + "\n[placement]\nenabled = false\n")
    off = load_vault(paths.root)
    sync_vault_state(off, repository, clock=_at(3))
    _b, baseline_vault, baseline_repo = _setup(tmp_path, version="mvp-0.9", name="baseline")
    assert _serving_fingerprint(off, repository, 4) == _serving_fingerprint(baseline_vault, baseline_repo, 4)


# ── Assumed known: each source marks the LO and schedules its first review ────


def test_self_report_marks_assumed_withholds_new_items_and_schedules_the_check(tmp_path):
    paths, vault, repository = _setup(tmp_path)
    before = _snapshot(paths)
    result = record_self_report(
        vault, repository, learning_object_ids=["lo_diag"], report="know_this", clock=_at(1),
    )
    assert [r["status"] for r in result["results"]] == ["assumed"]
    assert _snapshot(paths) == before  # G7: no evidence, mastery or certification write

    (decision,) = _decisions(paths)
    assert decision["source"] == "self_report" and decision["trigger_kind"] == "i_know_this"
    assert decision["first_review_due"] == "2026-06-02T12:01:00Z"  # 14 days after 12:01
    assert decision["predictor"] == "mastery_ekf"
    assert decision["p"] is None  # untested LO: no probability is claimed

    # Not served as new material until the first review falls due.
    early = _queue(vault, repository, 2, persist=False)
    assert not [s for s in early if s.learning_object_id == "lo_diag"]
    due = _queue(vault, repository, 14 * 24 * 60 + 5, persist=False)
    checks = [s for s in due if s.learning_object_id == "lo_diag"]
    assert len(checks) == 1 and checks[0].components["assumed_check"] == 1.0
    # The median predicted success of the never-seen items: a normal cold item.
    assert checks[0].practice_item_id == "pi_diag_mid"
    assert "this is the check" in checks[0].plain_english[0]


def test_self_report_is_idempotent_while_open_and_refused_when_placement_is_off(tmp_path):
    paths, vault, repository = _setup(tmp_path)
    record_self_report(vault, repository, learning_object_ids=["lo_diag"], report="know_this", clock=_at(1))
    again = record_self_report(vault, repository, learning_object_ids=["lo_diag"], report="too_easy", clock=_at(2))
    assert again["results"][0]["status"] == "already_assumed"
    assert len(_decisions(paths)) == 1

    _p, off_vault, off_repo = _setup(tmp_path, version="mvp-0.9", name="pre")
    with pytest.raises(PlacementInactive):
        record_self_report(off_vault, off_repo, learning_object_ids=["lo_diag"], report="know_this")


def test_too_easy_retirement_marks_the_lo_assumed_without_extra_writes(tmp_path):
    paths, vault, repository = _setup(tmp_path)
    off_paths, off_vault, off_repo = _setup(
        tmp_path, placement_toml="[placement]\nenabled = false\n", name="off",
    )
    on = retire_item(paths.root, repository, practice_item_id="pi_diag_easy", reason="too_easy", clock=_at(1))
    off = retire_item(off_paths.root, off_repo, practice_item_id="pi_diag_easy", reason="too_easy", clock=_at(1))

    assert on["placement"]["results"][0]["status"] == "assumed"
    assert "placement" not in off
    (decision,) = _decisions(paths)
    assert (decision["source"], decision["trigger_kind"], decision["trigger_ref"]) == (
        "self_report", "too_easy", "pi_diag_easy",
    )
    # The assumption adds nothing to what the retirement itself writes (its
    # pre-existing self-rating claim): the evidence tables match the switched-off
    # vault row for row, ignoring surrogate ids (G7).
    on_snapshot, off_snapshot = _snapshot(paths), _snapshot(off_paths)
    assert {t: len(rows) for t, rows in on_snapshot.items()} == {t: len(rows) for t, rows in off_snapshot.items()}
    for table in ("learning_object_mastery", "facet_recall_state", "facet_capability_evidence", "grading_evidence"):
        assert on_snapshot[table] == off_snapshot[table], table


def test_fast_track_needs_min_clean_answers_and_the_threshold(tmp_path):
    paths, vault, repository = _setup(tmp_path, placement_toml=LOW_Q)
    _answer(vault, repository, "pi_diag_hard", minutes=1)
    assert reconcile_fast_track(vault, repository, clock=_at(2)) == []  # one answer is not enough
    _answer(vault, repository, "pi_diag_mid", minutes=3)
    before = _snapshot(paths)
    (decision,) = reconcile_fast_track(vault, repository, clock=_at(4))
    assert _snapshot(paths) == before  # G7
    assert decision["source"] == "fast_track" and decision["learning_object_id"] == "lo_diag"
    assert decision["p"] >= 0.51 and decision["q_used"] == 0.51
    assert json.loads(decision["interval_json"])[0] < json.loads(decision["interval_json"])[1]
    assert reconcile_fast_track(vault, repository, clock=_at(5)) == []  # idempotent

    queue = _queue(vault, repository, 6, persist=False)
    assert "pi_diag_easy" not in _served(queue)  # remaining learning items withheld


def test_fast_track_default_threshold_is_not_met_by_two_answers(tmp_path):
    paths, vault, repository = _setup(tmp_path)
    _answer(vault, repository, "pi_diag_hard", minutes=1)
    _answer(vault, repository, "pi_diag_mid", minutes=2)
    assert reconcile_fast_track(vault, repository, clock=_at(3)) == []
    region = active_predictor(vault, repository).region_estimates(["lo_diag"])["lo_diag"]
    verdict = fast_track_verdict(
        _answers(paths, "lo_diag"),
        blocking_signal_ids=(), region=region, min_correct=2, q=0.8, known_threshold=theta_known(0.75),
    )
    # The incumbent's cold-start variance (3.0) keeps two answers well short of
    # P >= 0.8; the probability, not the two-answer floor, is what binds (D6).
    assert verdict.reason == "below_threshold" and verdict.p < 0.8


def _answers(paths, lo):
    from contextlib import closing

    from learnloop.db.connection import connect
    from learnloop.placement.state import evaluate_independence, load_answers

    with closing(connect(paths.sqlite_path, read_only=True)) as connection:
        return evaluate_independence(connection, load_answers(connection, [lo]).get(lo, ()))


@pytest.mark.parametrize(
    ("points", "hints"),
    [(3.0, 0), (4.0, 1)],
    ids=["partial-marks", "hinted"],
)
def test_fast_track_blocked_by_any_unclean_first_answer(tmp_path, points, hints):
    paths, vault, repository = _setup(tmp_path, placement_toml=LOW_Q)
    _answer(vault, repository, "pi_diag_easy", points, hints=hints, minutes=1)
    _answer(vault, repository, "pi_diag_mid", minutes=2)
    _answer(vault, repository, "pi_diag_hard", minutes=3)
    assert reconcile_fast_track(vault, repository, clock=_at(4)) == []


def test_predictor_assumption_is_impossible_under_the_incumbent(tmp_path):
    paths, vault, repository = _setup(tmp_path, placement_toml=LOW_Q)
    # Even a confident claim-seeded prior cannot assume an untested LO: the
    # incumbent shares nothing across LOs (field §5.2, §7.4).
    repository.insert_learner_claim(
        {
            "claim_type": "self_rating", "scope_type": "learning_object", "scope_id": "lo_eigen_basics",
            "evidence_family": "recall", "claimed_level": 0.98, "prior_pseudo_count": 10.0,
            "source": "learner_report",
        },
        clock=_at(1),
    )
    predictor = active_predictor(vault, repository)
    assert isinstance(predictor, LiveMasteryPredictor) and predictor.cross_lo_sharing is False
    assert reconcile_predictor_assumptions(vault, repository, predictor, clock=_at(2)) == []
    assert _decisions(paths) == []


# ── G7: reversible ────────────────────────────────────────────────────────────


def test_failed_first_review_quietly_returns_the_lo_to_learning(tmp_path):
    paths, vault, repository = _setup(tmp_path)
    record_self_report(vault, repository, learning_object_ids=["lo_diag"], report="know_this", clock=_at(1))
    check_minutes = 14 * 24 * 60 + 5
    (check,) = [s for s in _queue(vault, repository, check_minutes, persist=False) if s.learning_object_id == "lo_diag"]
    _answer(vault, repository, check.practice_item_id, 1.0, minutes=check_minutes + 1)

    state = load_placement_state(vault, repository)
    (assumption,) = state.assumptions
    assert assumption.status == "failed" and not state.open_by_lo
    queue = _queue(vault, repository, check_minutes + 2, persist=False)
    returned = {s.practice_item_id for s in queue if s.components.get("new_material")}
    assert {"pi_diag_easy", "pi_diag_hard"} <= returned


def test_passed_first_review_keeps_the_lo_in_maintenance(tmp_path):
    paths, vault, repository = _setup(tmp_path)
    record_self_report(vault, repository, learning_object_ids=["lo_diag"], report="know_this", clock=_at(1))
    check_minutes = 14 * 24 * 60 + 5
    _answer(vault, repository, "pi_diag_mid", 4.0, minutes=check_minutes)
    (assumption,) = load_placement_state(vault, repository).assumptions
    assert assumption.status == "passed"
    queue = _queue(vault, repository, check_minutes + 1, persist=False)
    assert not any(s.components.get("new_material") for s in queue if s.learning_object_id == "lo_diag")


def test_i_dont_know_this_returns_an_assumed_lo_to_learning_immediately(tmp_path):
    paths, vault, repository = _setup(tmp_path)
    record_self_report(vault, repository, learning_object_ids=["lo_diag"], report="know_this", clock=_at(1))
    before = _snapshot(paths)
    result = record_self_report(vault, repository, learning_object_ids=["lo_diag"], report="dont_know_this", clock=_at(2))
    assert result["results"][0]["status"] == "returned_to_learning"
    assert _snapshot(paths) == before
    state = load_placement_state(vault, repository)
    assert state.assumptions[0].status == "returned" and "lo_diag" in state.returned_learning_object_ids
    assert {"pi_diag_easy", "pi_diag_mid", "pi_diag_hard"} <= {
        s.practice_item_id for s in _queue(vault, repository, 3, persist=False) if s.components.get("new_material")
    }
    # An LO the learner said they don't know is never fast-tracked afterwards.
    _answer(vault, repository, "pi_diag_hard", minutes=4)
    _answer(vault, repository, "pi_diag_mid", minutes=5)
    assert reconcile_fast_track(vault, repository, clock=_at(6)) == []


# ── G8: every decision can be recomputed from its receipt ─────────────────────


def test_fast_track_receipt_recomputes_its_decision(tmp_path):
    paths, vault, repository = _setup(tmp_path, placement_toml=LOW_Q)
    _answer(vault, repository, "pi_diag_hard", minutes=1)
    _answer(vault, repository, "pi_diag_mid", minutes=2)
    (decision,) = reconcile_fast_track(vault, repository, clock=_at(3))
    inputs = json.loads(decision["inputs_json"])
    config = json.loads(decision["config_json"])
    from learnloop.field.types import RegionEstimate

    region = RegionEstimate(**inputs["region"])
    verdict = fast_track_verdict(
        [AnswerFacts.from_dict(answer) for answer in inputs["answers"]],
        blocking_signal_ids=inputs["blocking_signal_ids"],
        region=region,
        min_correct=inputs["min_correct"],
        q=inputs["q"],
        known_threshold=inputs["theta_known"],
    )
    assert verdict.fires and verdict.p == pytest.approx(decision["p"])
    assert config["placement"]["fast_track_q"] == decision["q_used"] == 0.51
    assert config["active_predictor"] == "mastery_ekf"
    assert json.loads(decision["trigger_ref"]) == [a["attempt_id"] for a in inputs["answers"]]
    assert decision["algorithm_version"] == "mvp-0.10"


def test_check_item_choice_is_deterministic(tmp_path):
    paths, vault, repository = _setup(tmp_path)
    record_self_report(vault, repository, learning_object_ids=["lo_eigen_basics"], report="know_this", clock=_at(1))
    minutes = 14 * 24 * 60 + 5
    picks = {
        tuple(s.practice_item_id for s in _queue(vault, repository, minutes, persist=False) if s.components.get("assumed_check"))
        for _ in range(3)
    }
    assert picks == {("pi_eig_mid",)}


def test_session_queue_runs_fast_track_before_serving(tmp_path):
    paths, vault, repository = _setup(tmp_path, placement_toml=LOW_Q)
    session_id = repository.create_session(available_minutes=25, clock=_at(0))
    _answer(vault, repository, "pi_diag_hard", minutes=1, session_id=session_id)
    _answer(vault, repository, "pi_diag_mid", minutes=2, session_id=session_id)
    queue = _queue(vault, repository, 3, session_id=session_id)
    assert [d["source"] for d in _decisions(paths)] == ["fast_track"]
    assert "pi_diag_easy" not in _served(queue)


def test_new_vaults_start_at_the_placement_successor(tmp_path):
    from learnloop.vault.loader import init_vault

    init_vault(tmp_path / "fresh", clock=FrozenClock(NOW))
    fresh = load_vault(tmp_path / "fresh")
    assert fresh.config.algorithms.algorithm_version == "mvp-0.10"
    assert placement_active(fresh)


# ── Durability lane: receipts survive replay under production pragmas ───────


@pytest.mark.durability
def test_placement_receipts_survive_rebuild_with_zero_model_calls(tmp_path, monkeypatch):
    from learnloop.ai import client
    from learnloop.diagnosis.calibration_sessions import stop_calibration_session
    from learnloop.diagnosis.quick_check import quick_check_progress, start_quick_check
    from learnloop.substrate.rebuild_orchestrator import rebuild_all_derived_state

    def forbidden(*args, **kwargs):
        raise AssertionError("placement and replay must not construct a model client")

    monkeypatch.setattr(client, "make_ai_provider_client", forbidden)
    monkeypatch.setattr(client, "make_ai_provider_client_from_profile", forbidden)
    paths, vault, repository = _setup(tmp_path, placement_toml=LOW_Q)
    record_self_report(vault, repository, learning_object_ids=["lo_eigen_basics"], report="know_this", clock=_at(1))
    _answer(vault, repository, "pi_diag_hard", minutes=2)
    _answer(vault, repository, "pi_diag_mid", minutes=3)
    assert reconcile_fast_track(vault, repository, clock=_at(4))
    session_id = repository.create_session(available_minutes=25, clock=_at(5))
    progress = start_quick_check(vault, repository, session_id=session_id, learning_object_ids=["lo_spectral"], clock=_at(6))
    stop_calibration_session(repository, progress["calibration_session_id"], clock=_at(7))
    quick_check_progress(vault, repository, progress["calibration_session_id"], clock=_at(8))

    tables = ("assumption_decisions", "assumption_returns", "placement_quick_checks")

    def placement_rows():
        with sqlite3.connect(paths.sqlite_path) as connection:
            return {t: sorted(tuple(r) for r in connection.execute(f"SELECT * FROM {t}")) for t in tables}

    before = placement_rows()
    assert len(before["assumption_decisions"]) == 2 and len(before["placement_quick_checks"]) == 1
    for _ in range(2):
        rebuild_all_derived_state(load_vault(paths.root), repository)
    assert placement_rows() == before
    with sqlite3.connect(paths.sqlite_path) as connection:
        assert connection.execute("PRAGMA journal_mode").fetchone()[0] == "wal"


# ── Codex review fixes (slice-a-phase-6): maintenance, interval, coldness ────

CHECK = 14 * 24 * 60 + 5


def _lo_items(queue, lo="lo_diag") -> set[str]:
    return {s.practice_item_id for s in queue if s.learning_object_id == lo}


def _intent(vault, repository, lo="lo_diag"):
    state = load_placement_state(vault, repository)
    entry = state.intent_by_lo.get(lo)
    return None if entry is None else entry.intent


def test_a_passed_check_keeps_the_remaining_learning_items_withheld(tmp_path):
    """F1: maintenance after a pass withholds the untouched items until a miss
    or "I don't know this" returns the LO to learning."""

    paths, vault, repository = _setup(tmp_path)
    record_self_report(vault, repository, learning_object_ids=["lo_diag"], report="know_this", clock=_at(1))
    (check,) = [s for s in _queue(vault, repository, CHECK, persist=False) if s.learning_object_id == "lo_diag"]
    assert check.practice_item_id == "pi_diag_mid"
    _answer(vault, repository, "pi_diag_mid", 4.0, minutes=CHECK + 1)
    (assumption,) = load_placement_state(vault, repository).assumptions
    assert assumption.status == "passed"
    assert _intent(vault, repository) == "maintenance"

    for minutes in (CHECK + 2, CHECK + 3 * 24 * 60, CHECK + 30 * 24 * 60):
        served = _lo_items(_queue(vault, repository, minutes, persist=False))
        assert served.isdisjoint({"pi_diag_easy", "pi_diag_hard"}), minutes

    # A later miss on the LO is a lapse: back to learning, untouched items return.
    _answer(vault, repository, "pi_diag_mid", 1.0, minutes=CHECK + 31 * 24 * 60)
    assert _intent(vault, repository) == "learning"
    queue = _queue(vault, repository, CHECK + 31 * 24 * 60 + 1, persist=False)
    returned = {s.practice_item_id for s in queue if s.components.get("new_material")}
    assert {"pi_diag_easy", "pi_diag_hard"} <= returned


def test_fast_track_check_waits_for_its_review_interval(tmp_path):
    """F2: nothing routine is served before the check date, and practice before
    it is recorded as early practice, never as the check."""

    paths, vault, repository = _setup(tmp_path, placement_toml=LOW_Q)
    _answer(vault, repository, "pi_diag_hard", minutes=1)
    _answer(vault, repository, "pi_diag_mid", minutes=2)
    (decision,) = reconcile_fast_track(vault, repository, clock=_at(3))
    assert decision["first_review_due"] == "2026-06-02T12:03:00Z"

    for minutes in (4, 60, 3 * 24 * 60, 13 * 24 * 60):
        assert _lo_items(_queue(vault, repository, minutes, persist=False)) == set(), minutes

    # Explicit practice before the check date never passes the check.
    _answer(vault, repository, "pi_diag_hard", minutes=8)
    (assumption,) = load_placement_state(vault, repository).assumptions
    assert assumption.status == "open" and assumption.early_answers == 1
    assert _intent(vault, repository) == "assumed"

    due = 14 * 24 * 60 + 10
    (check,) = [s for s in _queue(vault, repository, due, persist=False) if s.learning_object_id == "lo_diag"]
    assert check.components["assumed_check"] == 1.0 and check.practice_item_id == "pi_diag_easy"
    _answer(vault, repository, check.practice_item_id, minutes=due + 1)
    (assumption,) = load_placement_state(vault, repository).assumptions
    assert assumption.status == "passed" and assumption.resolved_at >= assumption.first_review_due


def test_an_early_miss_still_returns_the_lo_to_learning(tmp_path):
    paths, vault, repository = _setup(tmp_path)
    record_self_report(vault, repository, learning_object_ids=["lo_diag"], report="know_this", clock=_at(1))
    _answer(vault, repository, "pi_diag_easy", 1.0, minutes=5)  # learner-requested practice, missed
    (assumption,) = load_placement_state(vault, repository).assumptions
    assert assumption.status == "failed"
    assert _intent(vault, repository) == "learning"


def _attempt_created_at(paths, attempt_id):
    with sqlite3.connect(paths.sqlite_path) as connection:
        return connection.execute("SELECT created_at FROM practice_attempts WHERE id = ?", (attempt_id,)).fetchone()[0]


def test_a_post_reveal_answer_cannot_pass_the_check(tmp_path):
    """F3: placement reads the existing independence rule; an answer the
    admissibility check rejects cannot pass the assumed-known check."""

    from learnloop.attempts.reveal_ledger import production_admissibility, record_reveal

    paths, vault, repository = _setup(tmp_path)
    record_self_report(vault, repository, learning_object_ids=["lo_diag"], report="know_this", clock=_at(1))
    record_reveal(
        repository, practice_item_id="pi_diag_easy", learning_object_id="lo_diag",
        source_kind="tutor_answer", amount=1.0, clock=_at(CHECK),
    )
    result = _answer(vault, repository, "pi_diag_mid", 4.0, minutes=CHECK + 1)
    produced_at = _attempt_created_at(paths, result.attempt_id)
    admissibility = production_admissibility(
        repository, practice_item_id="pi_diag_mid", learning_object_id="lo_diag", produced_at=produced_at,
    )
    assert admissibility.reason == "post_reveal_not_independent"

    (assumption,) = load_placement_state(vault, repository).assumptions
    assert assumption.status == "open" and assumption.ineligible_answers == 1
    # The next answer on that item is independent again (the attempt closed the
    # reveal window), so the check can still resolve.
    _answer(vault, repository, "pi_diag_mid", 4.0, minutes=CHECK + 2 * 24 * 60)
    (assumption,) = load_placement_state(vault, repository).assumptions
    assert assumption.status == "passed"


def test_a_post_reveal_answer_never_counts_toward_fast_track(tmp_path):
    from learnloop.attempts.reveal_ledger import record_reveal

    paths, vault, repository = _setup(tmp_path, placement_toml=LOW_Q)
    record_reveal(
        repository, practice_item_id="pi_diag_easy", learning_object_id="lo_diag",
        source_kind="repair_display", amount=0.5, clock=_at(0.5),
    )
    _answer(vault, repository, "pi_diag_hard", minutes=1)
    _answer(vault, repository, "pi_diag_mid", minutes=2)
    assert reconcile_fast_track(vault, repository, clock=_at(3)) == []

    # Without the reveal the same answers fire, and the receipt keeps the
    # independence facts it read.
    other_paths, other_vault, other_repo = _setup(tmp_path, placement_toml=LOW_Q, name="clean")
    _answer(other_vault, other_repo, "pi_diag_hard", minutes=1)
    _answer(other_vault, other_repo, "pi_diag_mid", minutes=2)
    (decision,) = reconcile_fast_track(other_vault, other_repo, clock=_at(3))
    answers = json.loads(decision["inputs_json"])["answers"]
    assert [a["independent"] for a in answers] == [True, True]
    assert all(a["independence_reason"] is None for a in answers)


def test_i_dont_know_this_after_a_pass_returns_the_lo_to_learning(tmp_path):
    """F8: a standalone return (no open assumption) still changes routing."""

    paths, vault, repository = _setup(tmp_path)
    record_self_report(vault, repository, learning_object_ids=["lo_diag"], report="know_this", clock=_at(1))
    _answer(vault, repository, "pi_diag_mid", 4.0, minutes=CHECK)
    assert _intent(vault, repository) == "maintenance"
    result = record_self_report(
        vault, repository, learning_object_ids=["lo_diag"], report="dont_know_this", clock=_at(CHECK + 1),
    )
    assert result["results"][0]["status"] == "returned_to_learning"
    assert result["results"][0]["assumption_id"] is None
    assert _intent(vault, repository) == "learning"
    new = {s.practice_item_id for s in _queue(vault, repository, CHECK + 2, persist=False)
           if s.components.get("new_material")}
    assert {"pi_diag_easy", "pi_diag_hard"} <= new

    # A later explicit "I know this" supersedes that intent.
    again = record_self_report(
        vault, repository, learning_object_ids=["lo_diag"], report="know_this", clock=_at(CHECK + 3),
    )
    assert again["results"][0]["status"] == "assumed"
    assert _intent(vault, repository) == "assumed"
    assert _lo_items(_queue(vault, repository, CHECK + 4, persist=False)) == set()


def test_i_dont_know_this_on_a_practised_unassumed_lo_admits_its_new_items(tmp_path):
    paths, vault, repository = _setup(tmp_path)
    _answer(vault, repository, "pi_diag_mid", 2.0, minutes=1)
    record_self_report(vault, repository, learning_object_ids=["lo_diag"], report="dont_know_this", clock=_at(2))
    assert _intent(vault, repository) == "learning"
    new = {s.practice_item_id for s in _queue(vault, repository, 3, persist=False) if s.components.get("new_material")}
    assert {"pi_diag_easy", "pi_diag_hard"} <= new


def _ledger(paths):
    with sqlite3.connect(paths.sqlite_path) as connection:
        connection.row_factory = sqlite3.Row
        return [dict(row) for row in connection.execute(
            "SELECT * FROM judgment_ledger WHERE task = 'placement_override' ORDER BY created_at, id"
        )]


def test_learner_placement_verdicts_append_to_the_judgment_ledger(tmp_path):
    """F10: every learner placement override is an owner verdict in the ledger,
    written in the same transaction as its receipt and linked to it."""

    paths, vault, repository = _setup(tmp_path)
    know = record_self_report(vault, repository, learning_object_ids=["lo_diag"], report="know_this", clock=_at(1))
    back = record_self_report(
        vault, repository, learning_object_ids=["lo_diag"], report="dont_know_this", clock=_at(2),
    )
    retire_item(paths.root, repository, practice_item_id="pi_eig_easy", reason="too_easy", clock=_at(3))

    rows = _ledger(paths)
    assert [(r["left_id"], r["verdict"], r["judge"]) for r in rows] == [
        ("lo_diag", "know_this", "owner"),
        ("lo_diag", "dont_know_this", "owner"),
        ("lo_eigen_basics", "too_easy", "owner"),
    ]
    first, second, third = (json.loads(r["rationale"]) for r in rows)
    assert first["receipt"] == {"table": "assumption_decisions", "id": know["results"][0]["assumption_id"]}
    assert second["receipt"]["table"] == "assumption_returns"
    assert rows[1]["supersedes_id"] == rows[0]["id"]
    assert third["trigger_ref"] == "pi_eig_easy"
    (decision,) = [d for d in _decisions(paths) if d["learning_object_id"] == "lo_eigen_basics"]
    assert third["receipt"] == {"table": "assumption_decisions", "id": decision["id"]}
    assert back["results"][0]["status"] == "returned_to_learning"


def test_a_failed_ledger_append_rolls_back_the_receipt(tmp_path, monkeypatch):
    from learnloop.placement import decisions

    paths, vault, repository = _setup(tmp_path)

    def boom(*args, **kwargs):
        raise RuntimeError("ledger unavailable")

    monkeypatch.setattr(decisions, "append_judgment", boom)
    with pytest.raises(RuntimeError):
        record_self_report(vault, repository, learning_object_ids=["lo_diag"], report="know_this", clock=_at(1))
    assert _decisions(paths) == [] and _ledger(paths) == []


# ── Codex re-review: F3 (receipt qualification) and F11 (same-second order) ──


def _final_coldness_receipt(repository, attempt_id, *, delay="pass", qualifies=True, receipt_id="crf-test"):
    passing = {"status": "pass", "evidence": {}}
    repository.insert_coldness_receipt(
        receipt_id=receipt_id, lane="repair_cold_retry", stage="final", followup_task_id=None,
        remediation_episode_id=None, source_attempt_id=None, cold_attempt_id=attempt_id,
        cold_verification_id=None,
        dimensions={
            "retrieval_delay": {"status": delay, "evidence": {}},
            "unassisted": passing,
            "answer_leakage": passing,
        },
        derived={"qualifies_as_cold_retrieval": qualifies},
        telemetry_coverage={}, receipt_version="test-v1",
    )


@pytest.mark.parametrize(
    ("delay", "qualifies"),
    [("fail", False), ("pass", None)],
    ids=["delay-failed-unqualified", "qualification-unknown"],
)
def test_a_final_receipt_that_does_not_qualify_as_cold_retrieval_cannot_pass_the_check(tmp_path, delay, qualifies):
    """F3 (re-review): the final coldness receipt's own cold-retrieval
    qualification binds, not just its unassisted and answer-leakage dimensions."""

    paths, vault, repository = _setup(tmp_path)
    record_self_report(vault, repository, learning_object_ids=["lo_diag"], report="know_this", clock=_at(1))
    result = _answer(vault, repository, "pi_diag_mid", 4.0, minutes=CHECK + 1)
    _final_coldness_receipt(repository, result.attempt_id, delay=delay, qualifies=qualifies)

    (assumption,) = load_placement_state(vault, repository).assumptions
    assert assumption.status == "open" and assumption.ineligible_answers == 1
    (facts,) = [a for a in _answers(paths, "lo_diag") if a.attempt_id == result.attempt_id]
    assert facts.independent is False
    assert facts.independence_reason == "coldness_receipt_not_cold_retrieval"


def test_a_qualified_final_receipt_still_lets_the_check_pass(tmp_path):
    paths, vault, repository = _setup(tmp_path)
    record_self_report(vault, repository, learning_object_ids=["lo_diag"], report="know_this", clock=_at(1))
    result = _answer(vault, repository, "pi_diag_mid", 4.0, minutes=CHECK + 1)
    _final_coldness_receipt(repository, result.attempt_id)
    (assumption,) = load_placement_state(vault, repository).assumptions
    assert assumption.status == "passed"


def test_i_know_this_in_the_same_second_as_a_return_supersedes_it(tmp_path):
    """F11: created_at has second precision; within one second the durable
    (created_at, id) order decides, so the later "I know this" wins."""

    paths, vault, repository = _setup(tmp_path)
    record_self_report(vault, repository, learning_object_ids=["lo_diag"], report="dont_know_this", clock=_at(1))
    assert _intent(vault, repository) == "learning"
    again = record_self_report(vault, repository, learning_object_ids=["lo_diag"], report="know_this", clock=_at(1))
    assert again["results"][0]["status"] == "assumed"
    assert _intent(vault, repository) == "assumed"
    assert _lo_items(_queue(vault, repository, 2, persist=False)) == set()

    # The new assumption passes its check: maintenance, untouched items withheld.
    _answer(vault, repository, "pi_diag_mid", 4.0, minutes=CHECK + 1)
    (latest,) = [a for a in load_placement_state(vault, repository).assumptions if a.id == again["results"][0]["assumption_id"]]
    assert latest.status == "passed"
    assert _intent(vault, repository) == "maintenance"
    served = _lo_items(_queue(vault, repository, CHECK + 2, persist=False))
    assert served.isdisjoint({"pi_diag_easy", "pi_diag_hard"})


def test_a_return_in_the_same_second_as_i_know_this_still_returns_the_lo(tmp_path):
    paths, vault, repository = _setup(tmp_path)
    know = record_self_report(vault, repository, learning_object_ids=["lo_diag"], report="know_this", clock=_at(1))
    back = record_self_report(vault, repository, learning_object_ids=["lo_diag"], report="dont_know_this", clock=_at(1))
    assert back["results"][0]["assumption_id"] == know["results"][0]["assumption_id"]
    state = load_placement_state(vault, repository)
    assert state.assumptions[0].status == "returned"
    assert _intent(vault, repository) == "learning"


def test_answers_in_the_same_second_as_a_decision_or_return_keep_their_order(tmp_path):
    """The same durable order places answers: a miss right after "I know this"
    fails the assumption; a miss right before "I don't know this" is the miss."""

    paths, vault, repository = _setup(tmp_path)
    record_self_report(vault, repository, learning_object_ids=["lo_diag"], report="know_this", clock=_at(1))
    _answer(vault, repository, "pi_diag_easy", 1.0, minutes=1)
    (assumption,) = load_placement_state(vault, repository).assumptions
    assert assumption.status == "failed"

    other_paths, other_vault, other_repo = _setup(tmp_path, name="miss-then-return")
    record_self_report(other_vault, other_repo, learning_object_ids=["lo_diag"], report="know_this", clock=_at(1))
    _answer(other_vault, other_repo, "pi_diag_easy", 1.0, minutes=2)
    record_self_report(other_vault, other_repo, learning_object_ids=["lo_diag"], report="dont_know_this", clock=_at(2))
    (assumption,) = load_placement_state(other_vault, other_repo).assumptions
    assert assumption.status == "failed"
    assert _intent(other_vault, other_repo) == "learning"

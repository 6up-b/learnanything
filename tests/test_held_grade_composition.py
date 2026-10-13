"""A grade held for review composed with main's later stages.

A grade held for review (re-review F9: nothing assessed and nothing
validated; written by mvp-0.17's route check and, since route-check-in-grader,
by mvp-0.18's own-route rule over the grader alone) is the grader's own,
provisional, and applies no FSRS review. It is read from one recorded fact,
the latest blind record's ``grading_support.proof_route_check.held_for_review``.
Each composition point here reads that fact:

* router R1 (``router_outcomes``): a held attempt is never a scored outcome,
  in R_next/R_cold or in the coldness candidates, and the coldness covariate
  ``predicted_retrievability`` folds the ledger as the live schedule does (a
  held grade applies no review);
* learner-text gaps: a held attempt queues no gap reading as a failure (no
  live diagnosis to read);
* EVSI calibration: a held attempt is no realized outcome in the report;
* the stuck prompt: an empty stuck answer never reaches the grader;
* placement and the learner field: a held attempt is unassessed (no miss, no
  facet outcome);
* the shared output-budget policy: the hard-case harness plans the grader at
  the grading route's policy budget and retries a truncation once at double.

Fakes only; no network.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
import json
import sqlite3

import pytest

from learnloop.ai.execution import output_limit
from learnloop.ai.output_budget import output_budget
from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.db.stores.router import ROUTER_LOG_VERSION, insert_router_decision
from learnloop.vault.loader import load_vault

from tests.helpers import NOW, create_basic_vault
from tests.split_live_helpers import split_vault, submit
from tests.test_route_rules_in_grader import (
    ALTERNATIVE,
    CLOCK,
    ITEM,
    VERSION,
    DivergentUnlocatedGrader,
    _first_scheduled_attempt,
    _support,
)

HELD_SUPPORT = {
    "proof_route_check": {"status": "checked", "held_for_review": True, "version": "proof-route-check-v3"},
    "valid_alternative_gate_applied": True,
    "assessed_shortfall": False,
}


def _held_attempt(vault, repository):
    """A real held grade through the live door (re-review F9's scenario)."""

    _first_scheduled_attempt(vault, repository)
    held = submit(vault, repository, DivergentUnlocatedGrader(), answer=ALTERNATIVE + " (again)",
                  when=CLOCK.now() + timedelta(days=3))
    assert _support(repository, held.attempt_id)["proof_route_check"]["held_for_review"] is True
    return held


# -- router R1 ------------------------------------------------------------------------------

T0 = datetime(2026, 5, 19, 12, 0, tzinfo=UTC)
LO, A, B = "lo_svd_definition", "pi_svd_define_001", "pi_svd_define_002"


def _at(**delta) -> str:
    return (T0 + timedelta(**delta)).strftime("%Y-%m-%dT%H:%M:%SZ")


def _decision(repository, decision_id: str, *, created_at: str, item: str, candidate: str) -> None:
    row = {
        "id": decision_id, "receipt_key": f"today_offer:{decision_id}", "decision_kind": "today_offer",
        "surface": "desktop_queue", "mode": "legacy_queue", "policy": "composed_offer_v2",
        "algorithm_version": VERSION, "log_version": ROUTER_LOG_VERSION, "session_id": "s1",
        "snapshot_hash": "h", "candidates_json": "[]", "exclusions_json": "{}", "candidate_count": 0,
        "chosen_ref": item, "chosen_practice_item_id": item, "chosen_learning_object_id": LO,
        "chosen_scheduler_candidate_id": candidate, "propensity": 1.0, "propensity_kind": "deterministic",
        "learner_pick": 0, "detail_json": "{}", "created_at": created_at,
    }
    with repository.atomic(), repository.connection() as connection:
        insert_router_decision(connection, row)


def _attempt(repository, attempt_id: str, *, item: str, created_at: str, rubric_score: int, session: str,
             candidate: str | None = None, review_reason: str | None = None) -> None:
    with repository.connection() as connection:
        connection.execute(
            """INSERT INTO practice_attempts(
                 id, practice_item_id, learning_object_id, practice_mode, attempt_type, hints_used,
                 correctness, rubric_score, manual_review, manual_review_reason, created_at, session_id,
                 scheduler_candidate_id, primed, evidence_origin, evidence_facets_json)
               VALUES (?,?,?,?,?,0,?,?,?,?,?,?,?,0,'human',?)""",
            (attempt_id, item, LO, "short_answer", "independent_attempt", rubric_score / 4, rubric_score,
             int(review_reason is not None), review_reason, created_at, session, candidate, json.dumps(["f"])),
        )
        connection.commit()


def _hold(repository, attempt_id: str, *, support=None) -> None:
    repository.insert_blind_grade_record(
        attempt_id=attempt_id, agent_run_id=None, grading_prompt_version="blind-test",
        output_schema_version="BlindGradingProposal", context_hash="ctx",
        record={"practice_item_id": A, "grading_support": dict(support or HELD_SUPPORT)},
    )


def test_router_never_scores_a_held_attempt_and_its_fold_applies_no_review(tmp_path):
    from learnloop.attempts.attempts import fsrs_rating_for_attempt
    from learnloop.scheduling.fsrs import FSRS6_DEFAULT_WEIGHTS, Rating, apply_review, forgetting_curve
    from learnloop.substrate.rebuild_orchestrator import rebuild_all_derived_state

    paths = create_basic_vault(tmp_path / "vault")
    repository = Repository(paths.sqlite_path)
    _decision(repository, "d1", created_at=_at(minutes=0), item=A, candidate="c1")
    _attempt(repository, "a0", item=A, created_at=_at(minutes=1), rubric_score=4, session="s1", candidate="c1")
    # Held for review: the grader's own 0/4, nothing assessed or validated.
    _attempt(repository, "h1", item=A, created_at=_at(days=2), rubric_score=0, session="s2",
             review_reason="proof_route_check_flag")
    _hold(repository, "h1")
    _attempt(repository, "a1", item=A, created_at=_at(days=5), rubric_score=4, session="s3")
    vault = load_vault(paths.root)

    rebuild_all_derived_state(vault, repository, clock=FrozenClock(NOW), require_complete_attempt_coverage=False)

    with sqlite3.connect(paths.sqlite_path) as connection:
        connection.row_factory = sqlite3.Row
        row = dict(connection.execute("SELECT * FROM router_outcomes WHERE decision_id = 'd1'").fetchone())
    # Never a scored outcome: the cold retrieval is the next validated answer.
    assert row["r_cold_attempt_id"] == "a1"
    candidates = {entry["attempt_id"]: entry for entry in json.loads(row["coldness_candidates_json"])}
    assert candidates["h1"]["correctness"] is None
    assert "grade_held_for_review" in candidates["h1"]["exclusions"]
    assert candidates["a1"]["correctness"] == 1.0
    # The covariate folds the ledger as the live schedule does: the held grade
    # applied no review, but it was an exposure (last_attempt_at moved).
    item = vault.practice_items[A]
    rubric = vault.rubric_for_item(item)
    rating = fsrs_rating_for_attempt(item, 4, rubric.max_points if rubric is not None else 4, 0)
    first = apply_review(None, Rating(rating), 0.0, FSRS6_DEFAULT_WEIGHTS)
    expected = forgetting_curve(first.stability, 3.0, FSRS6_DEFAULT_WEIGHTS)
    assert row["r_cold_predicted_retrievability"] == pytest.approx(expected)
    # The held answer itself is predicted from the memory before it.
    held_at = forgetting_curve(first.stability, (2 * 86400 - 60) / 86400, FSRS6_DEFAULT_WEIGHTS)
    assert candidates["h1"]["predicted_retrievability"] == pytest.approx(held_at)


def test_a_released_hold_is_an_ordinary_outcome_again(tmp_path):
    """A regrade the check validates writes a record without the hold: the
    answer is scored and folded like any other."""

    from learnloop.router.outcomes import derive_router_outcomes
    from learnloop.substrate.canonical_projection import held_for_review_attempts

    paths = create_basic_vault(tmp_path / "vault")
    repository = Repository(paths.sqlite_path)
    _decision(repository, "d1", created_at=_at(minutes=0), item=A, candidate="c1")
    _attempt(repository, "a0", item=A, created_at=_at(minutes=1), rubric_score=4, session="s1", candidate="c1")
    _attempt(repository, "h1", item=B, created_at=_at(days=2), rubric_score=4, session="s2")
    _hold(repository, "h1")
    _hold(repository, "h1", support={**HELD_SUPPORT, "proof_route_check": {
        "status": "checked", "held_for_review": False, "version": "proof-route-check-v3"}})
    with repository.connection() as connection:
        assert held_for_review_attempts(connection) == frozenset()
        [outcome] = derive_router_outcomes(connection, held_attempt_ids=held_for_review_attempts(connection))
    assert outcome["r_cold_attempt_id"] == "h1"


# -- learner-text gaps --------------------------------------------------------------------


def test_a_held_attempt_queues_no_gap_reading_as_a_failure(tmp_path):
    from learnloop.diagnosis.split.jobs import diagnosis_status, enqueue_diagnosis

    _paths, vault, repository = split_vault(
        tmp_path, version=VERSION, config="[diagnosis]\ncorrect_answer_sample_rate = 1.0",
    )
    held = _held_attempt(vault, repository)
    # No live diagnosis (the only diagnosis a gap reading follows): at most a
    # shadow sample, which is never read for a gap.
    assert diagnosis_status(repository, held.attempt_id)["status"] in {"not_needed", "queued"}
    with repository.connection() as connection:
        jobs = connection.execute(
            "SELECT kind, payload_json FROM post_attempt_jobs WHERE attempt_id = ?", (held.attempt_id,)
        ).fetchall()
        assert all(json.loads(payload).get("mode") != "live" for _kind, payload in jobs)
        enqueue_diagnosis(vault, repository, attempt_id=held.attempt_id, rediagnose=True)
        jobs = connection.execute(
            "SELECT payload_json FROM post_attempt_jobs WHERE attempt_id = ?", (held.attempt_id,)
        ).fetchall()
        assert all(json.loads(payload).get("mode") != "live" for (payload,) in jobs)
        gap_jobs = connection.execute("SELECT source_kind, source_id FROM learner_text_gap_jobs").fetchall()
    assert gap_jobs == []


def test_a_diagnosis_of_a_held_attempt_is_never_read_as_a_wrong_answer(tmp_path):
    """A live diagnosis can still exist for a held grade (one completed before
    a regrade put the attempt on hold, or a grade a gate defect left with a
    standing shortfall). Its gap reading is the diagnosis source's "wrong
    answer" surface, so it is neither queued nor read while the grade is held
    (one helper: ``canonical_projection.held_for_review_attempts``)."""

    from learnloop.diagnosis.text_gaps.jobs import enqueue_after_diagnosis
    from learnloop.diagnosis.text_gaps.sources import diagnosis_text

    _paths, vault, repository = split_vault(tmp_path, version=VERSION)
    held = _held_attempt(vault, repository)
    diagnosis_id = repository.insert_attempt_diagnosis(
        attempt_id=held.attempt_id, diagnosis_prompt_version="diagnosis-test", mode="live",
        history_mode="full", status="completed", proposal={"event_diagnoses": []}, causal_view=None,
        validation_report=None, receipt=None,
    )
    queued = enqueue_after_diagnosis(
        vault, repository, attempt_id=held.attempt_id,
        diagnosis={"id": diagnosis_id, "mode": "live", "status": "completed"},
    )
    assert queued == []
    assert diagnosis_text(vault, repository, diagnosis_id) is None
    with repository.connection() as connection:
        assert connection.execute("SELECT COUNT(*) FROM learner_text_gap_jobs").fetchone()[0] == 0


# -- EVSI calibration -----------------------------------------------------------------------


def test_the_evsi_report_realizes_no_outcome_from_a_held_attempt(tmp_path):
    from learnloop.diagnosis.probe_episodes import enter_episode
    from learnloop.evsi_calibration import live_report as LR

    from tests.test_probe_robust_cutover import CLOCK as PROBE_CLOCK, _load, _record_full_score_probe

    loaded, repository = _load(tmp_path)
    episode = enter_episode(loaded, repository, "lo_svd_definition", clock=PROBE_CLOCK)
    _presentation, attempt_id = _record_full_score_probe(loaded, repository, episode)
    before = LR.calibration_report(loaded)["sites"]["probe_selection"]
    assert before["join_status"] == {"realized": 1}

    # The probe answer's grade is held for review: nothing validated it, so it
    # realizes no outcome (the probe observation still holds the grader's).
    repository.insert_blind_grade_record(
        attempt_id=attempt_id, agent_run_id=None, grading_prompt_version="blind-test",
        output_schema_version="BlindGradingProposal", context_hash="ctx",
        record={"practice_item_id": "pi_svd_define_001", "grading_support": dict(HELD_SUPPORT)},
    )
    forecast = {"site": "probe_selection", "forecast": {"emission_alphabet": []}}
    with repository.connection() as connection:
        assert LR.realized_emission(connection, loaded, forecast, attempt_id) == (None, "grade_held_for_review")
    site = LR.calibration_report(loaded)["sites"]["probe_selection"]
    assert site["join_status"] == {"grade_held_for_review": 1}
    assert site["outcome_reliability"]["realized_forecasts"] == 0


# -- the stuck prompt ---------------------------------------------------------------------


def test_an_empty_stuck_answer_never_reaches_the_grader(tmp_path):
    from learnloop.attempts.attempts import (
        AttemptDraft,
        SelfGradeInput,
        complete_attempt_with_ai_fallback,
        plan_grading_calls,
    )

    from tests.split_live_helpers import ReadyRuntime

    _paths, vault, repository = split_vault(tmp_path, version=VERSION)
    grader = DivergentUnlocatedGrader()
    draft = AttemptDraft(practice_item_id=ITEM, learner_answer_md="", attempt_type="independent_attempt",
                         declared_stuck=True)
    plan = plan_grading_calls(vault, repository, draft)
    assert (plan.kind, plan.calls) == ("empty_stuck", 0)
    result = complete_attempt_with_ai_fallback(
        vault, repository, draft, SelfGradeInput(criterion_points={}, confidence=3), runtime=ReadyRuntime(),
        ai_client=grader, clock=CLOCK,
    )
    assert grader.calls == []
    assert repository.latest_blind_grade_record(result.attempt_id) is None
    assert repository.fetch_practice_attempt(result.attempt_id)["rubric_score"] == 0


# -- placement and the learner field --------------------------------------------------------


def test_placement_and_the_field_read_a_held_attempt_as_unassessed(tmp_path):
    from learnloop.field.outcomes import load_replay_rows
    from learnloop.placement.state import pfc_unverified_attempt_ids

    _paths, vault, repository = split_vault(tmp_path, version=VERSION)
    held = _held_attempt(vault, repository)
    with repository.connection() as connection:
        # Placement: an unassessed answer keeps the topic, never a miss.
        assert held.attempt_id in pfc_unverified_attempt_ids(connection)
        attempts, _facets = load_replay_rows(connection, vault)
        observed = connection.execute(
            "SELECT COUNT(*) FROM facet_outcome_observations WHERE attempt_id = ?", (held.attempt_id,)
        ).fetchone()[0]
    # The field: no replay row and no facet outcome for it.
    assert held.attempt_id not in {row.attempt_id for row in attempts}
    assert observed == 0


# -- the shared output-budget policy --------------------------------------------------------


def test_the_hardcase_harness_plans_the_grader_at_its_routes_policy_budget(tmp_path):
    from learnloop.ai.spend import SpendCaps
    from learnloop.diagnosis.grading_hardcases import HARDCASE_ROUTES, run_hardcases

    from tests.test_grading_hardcases import _vault

    vault = _vault(tmp_path)
    caps = SpendCaps(max_candidates=0, max_pairs=0, max_retries=2, max_calls=500,
                     max_total_tokens=50_000_000, max_estimated_usd=100.0)
    report = run_hardcases(vault, routes=["haiku"], caps=caps, dry_run=True,
                           input_price_per_million=1.0, output_price_per_million=5.0)
    assert HARDCASE_ROUTES == {"grader": "grading"}
    roles = report["plan"]["haiku"]["roles"]
    assert set(roles) == {"grader:reference_shown+check_shown"}
    for label, entry in roles.items():
        route = HARDCASE_ROUTES[label.split(":")[0]]
        assert entry["output_tokens"] == output_budget(vault.config, route, provider="haiku") * entry["calls"], label


def test_the_hardcase_harness_retries_a_truncated_grade_once_at_double(tmp_path):
    from learnloop.ai.errors import AIOutputTruncated
    from learnloop.ai.spend import SpendCaps
    from learnloop.diagnosis.grading_hardcases import run_hardcases

    from tests.test_grading_hardcases import JudgeFake, _vault

    class TruncatingOnce(JudgeFake):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.readings: list[int | None] = []

        def _pf_hardcase_grader(self, request, context):
            self.readings.append(output_limit())
            if len(self.readings) == 1:
                raise AIOutputTruncated("finish_reason = length")
            return super()._pf_hardcase_grader(request, context)

    vault = _vault(tmp_path)
    judge = TruncatingOnce("generous")
    caps = SpendCaps(max_candidates=0, max_pairs=0, max_retries=2, max_calls=500,
                     max_total_tokens=50_000_000, max_estimated_usd=100.0)
    report = run_hardcases(vault, routes=["generous"], caps=caps, clients={"generous": judge})
    assert report["status"] == "complete"
    budget = output_budget(vault.config, "grading", provider="generous")
    assert judge.readings[:2] == [budget, 2 * budget]
    # The retried grade counts: no failed case.
    assert report["by_route"]["generous"]["grader"]["failed_cases"] == 0
    assert not any(key.startswith("grader") for key in report["errors"]["generous"])


def test_the_documented_two_route_run_fits_the_default_caps_at_the_policy_budget(tmp_path):
    """The stage record's two-route hard-case run (two OpenRouter judges at
    $0.10 / $0.50) still fits the command's default caps once every request
    reserves its route's policy budget (the token cap default is 4,000,000)."""

    from typer.testing import CliRunner

    from learnloop.cli import app

    paths = create_basic_vault(tmp_path / "vault")
    config = paths.root / "learnloop.toml"
    config.write_text(config.read_text(encoding="utf-8") + (
        '\n[ai.providers.or_haiku]\ntype = "openrouter"\nmodel = "anthropic/claude-haiku-5.5"\n'
        'api_key_env = "OPENROUTER_API_KEY"\n'
        '[ai.providers.or_luna]\ntype = "openrouter"\nmodel = "openai/gpt-6-luna"\n'
        'api_key_env = "OPENROUTER_API_KEY"\n'
    ), encoding="utf-8")
    result = CliRunner().invoke(app, [
        "grading", "hardcases", "--vault", str(paths.root), "--route", "or_haiku", "--route", "or_luna",
        "--input-price-per-million", "0.10", "--output-price-per-million", "0.50", "--dry-run", "--json",
    ])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["status"] == "dry_run"
    assert payload["estimate"]["metered"]["calls"] == 2 * 16

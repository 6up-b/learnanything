"""`learnloop eval`: metric primitives against hand-computed values, section
builders on seeded data, and empty-vault smoke behavior."""

from __future__ import annotations

import json
from datetime import timedelta

import pytest
from typer.testing import CliRunner

from learnloop.cli import app
from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.attempts.attempts import AttemptDraft, SelfGradeInput, complete_self_graded_attempt
from learnloop.scheduling.evaluation import (
    brier_score,
    build_eval_report,
    ece_equal_width,
    log_loss,
)
from learnloop.scheduling.fsrs import apply_review, forgetting_curve
from learnloop.scheduling.scheduler import build_due_queue
from learnloop.substrate.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault

from tests.helpers import NOW, create_basic_vault, seed_due_item

runner = CliRunner()


# ── metric primitives ────────────────────────────────────────────────────────


def test_brier_hand_computed():
    assert brier_score([(0.8, 1.0)]) == pytest.approx(0.04)
    assert brier_score([(0.8, 1.0), (0.2, 0.0)]) == pytest.approx(0.04)
    assert brier_score([]) == 0.0


def test_log_loss_hand_computed_and_clipped():
    import math

    assert log_loss([(0.5, 1.0)]) == pytest.approx(math.log(2))
    # Confident wrong prediction is clipped, not infinite.
    assert log_loss([(1.0, 0.0)]) < 20


def test_ece_two_known_bins():
    pairs = [(0.05, 0.0), (0.05, 0.0), (0.95, 1.0), (0.95, 0.0)]
    ece, table = ece_equal_width(pairs, bins=10)
    # Low bin perfectly calibrated (pred 0.05, realized 0.0 → gap 0.05);
    # high bin pred 0.95 vs realized 0.5 → gap 0.45. Weighted: 0.5*0.05+0.5*0.45.
    assert ece == pytest.approx(0.25)
    assert len(table) == 2
    assert table[0].count == 2 and table[1].count == 2


def test_ece_empty():
    assert ece_equal_width([], bins=10) == (0.0, [])


# ── report on seeded data ────────────────────────────────────────────────────


def _seeded(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    repository = seed_due_item(paths)
    vault = load_vault(vault_root)
    sync_vault_state(vault, repository, clock=FrozenClock(NOW))
    return vault, repository


def test_report_on_real_session_flow(tmp_path):
    vault, repository = _seeded(tmp_path)
    # A real slate (logs candidates + propensities), then an attempt chosen
    # from it, then a later attempt on the same item (a retention label pair).
    from learnloop.scheduling.scheduler import SchedulerSession

    queue = build_due_queue(
        vault, repository, clock=FrozenClock(NOW), session=SchedulerSession(session_id="s_eval_test")
    )
    assert queue
    from learnloop.diagnosis.followups import evaluate_attempt_intervention_followup

    first = complete_self_graded_attempt(
        vault,
        repository,
        AttemptDraft(practice_item_id="pi_svd_define_001", learner_answer_md="U Sigma V^T"),
        SelfGradeInput(criterion_points={"correctness": 4}, confidence=4),
        clock=FrozenClock(NOW),
    )
    evaluate_attempt_intervention_followup(vault, repository, result=first, session_id=None)
    complete_self_graded_attempt(
        vault,
        repository,
        AttemptDraft(practice_item_id="pi_svd_define_001", learner_answer_md="U Sigma V^T again"),
        SelfGradeInput(criterion_points={"correctness": 4}, confidence=4),
        clock=FrozenClock(NOW + timedelta(days=2)),
    )

    report = build_eval_report(
        vault, repository, sections={"predictions", "gates", "retention", "propensity"}
    )
    gates = report.gates
    assert gates["count"] >= 1  # gate diagnostics persisted on evaluation

    retention = report.retention
    assert retention["count"] >= 1
    # seed_due_item pre-seeds practice_item_state with a hand-set stability the
    # attempt stream can't reproduce — the caveat mechanism must catch it.
    assert retention["reconstruction"]["stability_mismatches"] == 1
    # Reconstructed prediction must match a hand-run of the FSRS chain (which
    # starts from the raw attempt stream, not the seeded state).
    from learnloop.attempts.attempts import fsrs_rating_for_attempt

    item = vault.practice_items["pi_svd_define_001"]
    rating = fsrs_rating_for_attempt(item, 4, 4, 0)
    state = apply_review(None, rating, 0.0)
    expected = forgetting_curve(state.stability, 2.0)
    assert retention["by_elapsed_band"]["1-3d"]["count"] >= 1
    assert any(
        abs(bin_row["mean_predicted"] - expected) < 0.05
        for bin_row in retention["reliability"]
        if bin_row["count"]
    )

    propensity = report.propensity
    assert propensity["slates"] >= 1
    assert propensity["off_policy_readiness"] in ("OK", "DEGENERATE", "NO DATA")

    # Text rendering never raises and mentions every section.
    text = report.format_text()
    assert "Follow-up gate" in text
    assert "Retention" in text
    assert "propensities" in text


def test_gate_section_counts_manual_false_negatives(tmp_path):
    vault, repository = _seeded(tmp_path)
    from learnloop.diagnosis.followups import evaluate_intervention_followup

    result = complete_self_graded_attempt(
        vault,
        repository,
        AttemptDraft(practice_item_id="pi_svd_define_001", learner_answer_md="x"),
        SelfGradeInput(criterion_points={"correctness": 4}, confidence=4),
        clock=FrozenClock(NOW),
    )
    evaluate_intervention_followup(
        vault,
        repository,
        attempt_id=result.attempt_id,
        learning_object_id=result.learning_object_id,
        practice_item_id=result.practice_item_id,
        surprise_direction="positive",
        bayesian_surprise=0.0,
        grader_confidence=0.95,
        error_event_written=False,
        available_minutes=30,
        manual_override=True,
    )
    report = build_eval_report(vault, repository, sections={"gates"})
    assert report.gates["manual_overrides"] >= 1
    assert report.gates["gate_false_negatives"] >= 1


def test_eval_cli_empty_vault_smoke(tmp_path):
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)
    result = runner.invoke(app, ["eval", "--vault", str(vault_root), "--json"])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)["eval"]
    assert payload["predictions"]["count"] == 0
    assert payload["propensity"]["off_policy_readiness"] == "NO DATA"

    text_result = runner.invoke(app, ["eval", "--vault", str(vault_root)])
    assert text_result.exit_code == 0, text_result.output
    assert "no data" in text_result.output


def test_eval_cli_rejects_unknown_section(tmp_path):
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)
    result = runner.invoke(app, ["eval", "--vault", str(vault_root), "--section", "nonsense"])
    assert result.exit_code == 2

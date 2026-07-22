"""P4 step 6 (descoped, U-025) -- prequential held-out scoring of shadow predictive
components (spec_p4 §7.1/§7.3; design §B step 6, §F).

Covers the log-loss/Brier metrics, the primary component report joining pre-outcome
predictions to resolved next-spaced-cold-review outcomes (never immediate success),
by-group splits, and the secondary composed-selector report.
"""

from __future__ import annotations

import math

import pytest

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.services import controller_store as store
from learnloop.services import prequential
from learnloop.vault.loader import load_vault

from tests.helpers import NOW, create_basic_vault

CLOCK = FrozenClock(NOW)


@pytest.fixture
def repo(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    load_vault(paths.root)
    return Repository(paths.sqlite_path)


def _decision(repo, decision_id):
    """Minimal snapshot + decision so the shadow-prediction / outcome-window FKs hold."""

    with repo.connection() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO controller_snapshots(id, snapshot_hash, body_json, "
            "created_at) VALUES (?, ?, '{}', ?)",
            (f"snap_{decision_id}", f"h_{decision_id}", NOW.isoformat()),
        )
        conn.execute(
            "INSERT OR IGNORE INTO controller_decisions(id, snapshot_id, snapshot_hash, "
            "staged_rule, action, trace_json, created_at) VALUES "
            "(?, ?, 'h', 'rule', 'maintain', '{}', ?)",
            (decision_id, f"snap_{decision_id}", NOW.isoformat()),
        )
        conn.commit()


def test_brier_and_log_loss():
    assert prequential.brier([]) is None
    assert prequential.brier([(1.0, 1.0), (0.0, 0.0)]) == 0.0
    assert prequential.brier([(0.0, 1.0)]) == 1.0
    # log-loss of a perfect-ish prediction is near zero; a confident wrong one is large.
    assert prequential.log_loss([(0.9999999, 1.0)]) < 1e-3
    assert prequential.log_loss([(0.0000001, 1.0)]) > 5.0


def _seed_prediction_and_outcome(repo, *, decision_id, component, prob, cold_success, card):
    _decision(repo, decision_id)
    store.persist_shadow_prediction(
        repo, decision_id=decision_id, snapshot_hash="h",
        scorer_kind=f"predictive_component:{component}", model_version="v0",
        prediction={"value": prob}, clock=CLOCK,
    )
    window_id = store.open_outcome_window(
        repo, decision_id=decision_id, assignment_id=None, candidate_ref="c",
        commitment_id=None, card_ref=card, anchor_kind="card", anchor_ref=card, due_at=None, hypothesis_grade=False, clock=CLOCK,
    )
    store.resolve_outcome_window(
        repo, window_id=window_id, outcome={"cold_success": cold_success}, clock=CLOCK
    )


def test_component_report_joins_predictions_to_cold_outcomes(repo):
    # Two decisions: one predicted-high correct, one predicted-low incorrect.
    _seed_prediction_and_outcome(repo, decision_id="d1", component="retrievability",
                                 prob=0.8, cold_success=True, card="fam_a")
    _seed_prediction_and_outcome(repo, decision_id="d2", component="retrievability",
                                 prob=0.3, cold_success=False, card="fam_b")
    report = prequential.component_report(repo, component="retrievability", clock=CLOCK)
    assert report.sample_count == 2
    assert report.horizon_kind == "next_spaced_cold_review"
    assert report.metrics["brier"] is not None
    # Split along BOTH claimed dimensions (§7.2 leakage guard, audit L3): target family
    # (card_ref) and time (calendar-date bucket).
    assert set(report.splits) == {"by_family", "by_time"}
    assert set(report.splits["by_family"]) == {"fam_a", "fam_b"}
    assert report.splits["by_time"]  # at least one time bucket present
    # Persisted + rebuildable.
    rows = prequential.reports_for(repo, target_kind="predictive_component:retrievability")
    assert rows and rows[-1]["report_hash"] == report.report_hash


def test_report_repersist_is_idempotent_on_hash(repo):
    # Audit L5/D9: a report is a rebuildable snapshot keyed by content (report_hash).
    # Re-persisting the same content collapses to one row (UNIQUE(report_hash) +
    # ON CONFLICT DO NOTHING). Pre-fix each rebuild appended a duplicate row.
    _seed_prediction_and_outcome(repo, decision_id="d1", component="retrievability",
                                 prob=0.8, cold_success=True, card="fam_a")
    r1 = prequential.component_report(repo, component="retrievability", clock=CLOCK)
    r2 = prequential.component_report(repo, component="retrievability", clock=CLOCK)
    assert r1.report_hash == r2.report_hash
    rows = prequential.reports_for(repo, target_kind="predictive_component:retrievability")
    matching = [row for row in rows if row["report_hash"] == r1.report_hash]
    assert len(matching) == 1


def test_immediate_outcome_window_is_rejected_by_schema(repo):
    # Audit L9: construct the immediate-outcome LEAKAGE case and assert the schema CHECK
    # fires. An outcome window may only resolve at the next-spaced-cold-review horizon
    # (§9.3); an 'immediate' horizon (scoring on answer success) is rejected at the DB, so
    # the report can never join to an immediate outcome. The prior test only covered the
    # unresolved case and never exercised this last-line guard.
    import sqlite3

    _decision(repo, "d_imm")
    with pytest.raises(sqlite3.IntegrityError):
        with repo.connection() as conn:
            conn.execute(
                "INSERT INTO controller_outcome_windows(id, decision_id, anchor_kind, "
                "horizon_kind, opened_at, status, created_at) "
                "VALUES ('w_imm', 'd_imm', 'card', 'immediate', ?, 'pending', ?)",
                (NOW.isoformat(), NOW.isoformat()),
            )
            conn.commit()


def test_report_ignores_unresolved_and_immediate_outcomes(repo):
    # A prediction whose outcome window is never resolved contributes nothing.
    _decision(repo, "d9")
    store.persist_shadow_prediction(
        repo, decision_id="d9", snapshot_hash="h",
        scorer_kind="predictive_component:expected_success", model_version="v0",
        prediction={"value": 0.7}, clock=CLOCK,
    )
    store.open_outcome_window(
        repo, decision_id="d9", assignment_id=None, candidate_ref="c",
        commitment_id=None, card_ref="fam", anchor_kind="card", anchor_ref="fam", due_at=None, hypothesis_grade=False, clock=CLOCK,
    )
    report = prequential.component_report(repo, component="expected_success", clock=CLOCK)
    assert report.sample_count == 0
    assert report.metrics["log_loss"] is None


def test_composed_selector_report_is_secondary(repo):
    _decision(repo, "d1")
    store.persist_shadow_prediction(
        repo, decision_id="d1", snapshot_hash="h", scorer_kind="composed_selector",
        model_version="v0", prediction={"value": 0.6}, clock=CLOCK,
    )
    window_id = store.open_outcome_window(
        repo, decision_id="d1", assignment_id=None, candidate_ref="c",
        commitment_id=None, card_ref="fam", anchor_kind="card", anchor_ref="fam", due_at=None, hypothesis_grade=False, clock=CLOCK,
    )
    store.resolve_outcome_window(
        repo, window_id=window_id, outcome={"cold_success": True}, clock=CLOCK
    )
    report = prequential.composed_selector_report(repo, clock=CLOCK)
    assert report.target_kind == "composed_selector"
    assert "no promotion path" in report.metrics["note"]

"""P4 step 6 (descoped, U-025) -- shadow predictive components + the deferred scored
selector (spec_p4 §7, §16.2/§16.10; design §B step 6, §F).

Covers: predictions carry ZERO authority (schema firewall); individual component
promotion emits a U-022 promotion-evidence artifact and feeds inputs only; the
monolithic action chooser has NO promotion path (structural guard, always refuses); and
the composed-selector telemetry is TIME-BOXED (retires after its registered horizon).
"""

from __future__ import annotations

import pytest

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.services import controller_snapshot as cs
from learnloop.services import controller_store as store
from learnloop.services import prequential
from learnloop.services import shadow_components as sc
from learnloop.vault.loader import load_vault

from tests.helpers import NOW, create_basic_vault

CLOCK = FrozenClock(NOW)
LATER = FrozenClock(NOW.replace(year=NOW.year + 1))


@pytest.fixture
def repo(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    load_vault(paths.root)
    return Repository(paths.sqlite_path)


def _candidate(ref="c1", minutes=4.0):
    return cs.Candidate(candidate_ref=ref, expected_minutes=minutes, due_at=None)


def test_shadow_predictions_have_zero_authority(repo):
    preds = sc.predict_components(_candidate())
    ids = sc.record_shadow_predictions(
        repo, decision_id=None, snapshot_hash="h", predictions=preds, clock=CLOCK
    )
    assert set(ids) == {"retrievability", "expected_success", "expected_duration",
                        "composed_selector"}
    # The schema CHECK pins authority to 'none'; every persisted row proves the firewall.
    with repo.connection() as conn:
        rows = conn.execute(
            "SELECT scorer_kind, authority FROM controller_shadow_predictions"
        ).fetchall()
    assert rows and all(r["authority"] == "none" for r in rows)


def test_predictions_use_no_post_administration_or_outcome_feature(repo):
    # predict_components takes only a candidate (pre-administration material). It cannot
    # read correctness: passing a candidate is the whole input surface.
    preds = sc.predict_components(_candidate(minutes=2.0))
    assert 0.0 <= preds.retrievability <= 1.0
    assert 0.0 <= preds.expected_success <= 1.0
    assert preds.expected_duration == 2.0


def test_monolithic_action_chooser_has_no_promotion_path(repo):
    assert sc.MONOLITHIC_CHOOSER_PROMOTABLE is False
    outcome = sc.promote_action_chooser(repo)
    assert not outcome.promoted
    assert outcome.reason == "no_reachable_promotion_path_at_n1"


def test_monolithic_action_chooser_refuses_even_a_wide_margin_report(repo):
    # Audit L9: adversarial promotion attempt. Hand the monolithic chooser a report that
    # WOULD promote a component -- crushingly beats the incumbent on log-loss with a large
    # effective sample -- and assert the STRUCTURAL guard still refuses (U-025 §7.4). No
    # amount of evidence can promote the composed action chooser; the previous test only
    # exercised the empty-args path.
    wide_margin = prequential.PrequentialReport(
        target_kind="composed_selector", component=None, horizon_kind=prequential.HORIZON_KIND,
        metrics={"log_loss": 0.01, "effective_sample": 100_000}, splits={},
        sample_count=100_000, report_hash="rh_wide",
    )
    outcome = sc.promote_action_chooser(
        repo, component="composed_selector", report=wide_margin, incumbent_log_loss=0.90, clock=CLOCK
    )
    assert not outcome.promoted
    assert outcome.reason == "no_reachable_promotion_path_at_n1"
    assert outcome.evidence_id is None  # no promotion-evidence artifact was minted.


def test_component_promotion_emits_u022_evidence_and_feeds_inputs_only(repo):
    # A challenger report that clearly beats the incumbent on log-loss.
    report = prequential.PrequentialReport(
        target_kind="predictive_component:retrievability", component="retrievability",
        horizon_kind=prequential.HORIZON_KIND,
        metrics={"log_loss": 0.20, "effective_sample": 40}, splits={},
        sample_count=40, report_hash="rh",
    )
    outcome = sc.promote_component(
        repo, component="retrievability", report=report, incumbent_log_loss=0.50, clock=CLOCK
    )
    assert outcome.promoted and outcome.evidence_id
    # The U-022 promotion-evidence artifact is a real registry certificate row.
    certs = repo.sensitivity_certificates_for_path(sc.PROMOTION_EVIDENCE_PATH)
    assert any(c["id"] == outcome.evidence_id for c in certs)
    # The event records that a promoted component feeds inputs only (never actions).
    events = sc.component_events(repo, "retrievability")
    promo = [e for e in events if e["event_kind"] == "promotion"]
    assert promo and promo[0]["promotion_evidence_id"] == outcome.evidence_id


def test_component_promotion_refuses_without_enough_evidence(repo):
    report = prequential.PrequentialReport(
        target_kind="predictive_component:expected_success", component="expected_success",
        horizon_kind=prequential.HORIZON_KIND,
        metrics={"log_loss": 0.20, "effective_sample": 0}, splits={},
        sample_count=0, report_hash="rh",
    )
    outcome = sc.promote_component(
        repo, component="expected_success", report=report, incumbent_log_loss=0.50, clock=CLOCK
    )
    assert not outcome.promoted and outcome.reason == "insufficient_evidence"


def test_component_promotion_refuses_when_not_beating_incumbent(repo):
    report = prequential.PrequentialReport(
        target_kind="predictive_component:expected_duration", component="expected_duration",
        horizon_kind=prequential.HORIZON_KIND,
        metrics={"log_loss": 0.49, "effective_sample": 50}, splits={},
        sample_count=50, report_hash="rh",
    )
    outcome = sc.promote_component(
        repo, component="expected_duration", report=report, incumbent_log_loss=0.50, clock=CLOCK
    )
    assert not outcome.promoted and outcome.reason == "did_not_beat_incumbent"


def test_composed_selector_telemetry_is_time_boxed(repo):
    horizon_id = sc.open_composed_selector_horizon(repo, horizon_days=30, clock=CLOCK)
    # Idempotent while open.
    assert sc.open_composed_selector_horizon(repo, clock=CLOCK) == horizon_id
    # Not yet expired at NOW.
    assert sc.retire_expired_telemetry(repo, clock=CLOCK) == []
    # A year later it retires.
    retired = sc.retire_expired_telemetry(repo, clock=LATER)
    assert horizon_id in retired
    with repo.connection() as conn:
        row = conn.execute(
            "SELECT status FROM composed_selector_telemetry_horizons WHERE id = ?",
            (horizon_id,),
        ).fetchone()
    assert row["status"] == "retired"


def test_single_open_telemetry_horizon_enforced_at_db(repo):
    # Audit L6/D10: at most ONE composed-selector horizon may be open. The register path
    # guards this in code; the partial unique index (migration 101) enforces it at the DB
    # level against a race. A raw second open-row insert is rejected.
    import sqlite3

    sc.open_composed_selector_horizon(repo, horizon_days=30, clock=CLOCK)
    with pytest.raises(sqlite3.IntegrityError):
        with repo.connection() as conn:
            conn.execute(
                "INSERT INTO composed_selector_telemetry_horizons(id, horizon_days, "
                "opened_at, retires_at, retired_at, status, detail_json) "
                "VALUES ('h2', 30, '2026-01-01T00:00:00Z', '2026-02-01T00:00:00Z', NULL, 'open', '{}')"
            )
            conn.commit()


def test_state_sync_retires_expired_telemetry_horizon(tmp_path):
    # Audit L4/D8: the time-box only fires if a runtime path checks it. State sync is the
    # per-decision maintenance hook, so an expired horizon retires when sync runs. Pre-fix
    # nothing at runtime called retire_expired_telemetry, so retirement never fired.
    from learnloop.services.state_sync import sync_vault_state

    paths = create_basic_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    repo = Repository(paths.sqlite_path)
    horizon_id = sc.open_composed_selector_horizon(repo, horizon_days=30, clock=CLOCK)

    # Sync at NOW does not retire (not yet past the box).
    sync_vault_state(vault, repo, clock=CLOCK)
    with repo.connection() as conn:
        status = conn.execute(
            "SELECT status FROM composed_selector_telemetry_horizons WHERE id = ?",
            (horizon_id,),
        ).fetchone()["status"]
    assert status == "open"

    # A year later, a sync retires the expired horizon through the runtime hook.
    sync_vault_state(vault, repo, clock=LATER)
    with repo.connection() as conn:
        status = conn.execute(
            "SELECT status FROM composed_selector_telemetry_horizons WHERE id = ?",
            (horizon_id,),
        ).fetchone()["status"]
    assert status == "retired"

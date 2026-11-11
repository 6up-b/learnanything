from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository

from tests.helpers import NOW, NOW_ISO, create_basic_vault


def test_session_checkpoint_round_trip(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    repository = Repository(paths.sqlite_path)
    clock = FrozenClock(NOW)

    session_id = repository.create_session(energy="medium", available_minutes=25, clock=clock)
    repository.update_session_checkpoint(
        session_id,
        current_practice_item_id="pi_svd_define_001",
        current_answer="draft answer",
        focus_block_state={"step": "practice"},
        readiness={"energy": "medium"},
        clock=clock,
    )

    checkpoint = repository.fetch_session_checkpoint(session_id)

    assert checkpoint["current_practice_item_id"] == "pi_svd_define_001"
    assert checkpoint["focus_block_state"] == {"step": "practice"}
    assert checkpoint["readiness"] == {"energy": "medium"}
    assert repository.clear_session_checkpoint(session_id) is True
    assert repository.fetch_session_checkpoint(session_id) is None


def test_agent_run_and_proposal_status_derivation(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    repository = Repository(paths.sqlite_path)
    clock = FrozenClock(NOW)

    run_id = repository.insert_agent_run(
        {
            "id": "agent_run_1",
            "purpose": "authoring",
            "provider": "fake",
            "output_schema": "AuthoringProposal",
            "started_at": NOW_ISO,
        }
    )
    assert run_id == "agent_run_1"
    assert repository.complete_agent_run(run_id, clock=clock) is True

    patch_id = repository.persist_proposal_batch(
        {
            "id": "patch_1",
            "agent_run_id": run_id,
            "purpose": "authoring",
            "source_refs": [{"ref_id": "note_1"}],
            "summary": "Create one item",
            "created_at": NOW_ISO,
        },
        [
            {
                "id": "proposal_item_1",
                "client_item_id": "client_1",
                "item_type": "practice_item",
                "operation": "create",
                "target_entity_type": "practice_item",
                "payload": {"id": "pi_new"},
                "created_at": NOW_ISO,
            }
        ],
    )

    assert patch_id == "patch_1"
    assert repository.proposal_batches()[0]["source_refs"] == [{"ref_id": "note_1"}]
    assert repository.proposal_items(patch_id)[0]["payload"] == {"id": "pi_new"}
    assert repository.set_proposal_item_decision(patch_id, "accepted", clock=clock) == 1
    assert repository.proposal_batches()[0]["status_cache"] == "accepted"


def test_session_day_streak_counts_active_and_alive_streaks(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    repository = Repository(paths.sqlite_path)
    today = datetime(2026, 5, 19, 12, 0, tzinfo=UTC)

    assert repository.session_day_streak(clock=FrozenClock(today)) == {
        "current": 0,
        "active_today": False,
        "longest": 0,
    }

    for days_ago in (5, 4, 2, 1, 0):
        repository.create_session(clock=FrozenClock(today - timedelta(days=days_ago)))

    assert repository.session_day_streak(clock=FrozenClock(today)) == {
        "current": 3,
        "active_today": True,
        "longest": 3,
    }

    tomorrow = today + timedelta(days=1)
    assert repository.session_day_streak(clock=FrozenClock(tomorrow)) == {
        "current": 3,
        "active_today": False,
        "longest": 3,
    }

    day_after_tomorrow = today + timedelta(days=2)
    assert repository.session_day_streak(clock=FrozenClock(day_after_tomorrow)) == {
        "current": 0,
        "active_today": False,
        "longest": 3,
    }


def test_misconception_registry_round_trip_and_status_transitions(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    repository = Repository(paths.sqlite_path)
    clock = FrozenClock(NOW)

    mc_id = repository.insert_misconception(
        learning_object_id="lo_svd",
        concept_id="c_svd",
        statement="believes Q maps standard vectors to eigenbasis coefficients",
        signature="applies Q where Q^T is required",
        facet_ids=["coord_change", "coord_change"],
        severity=0.6,
        source_error_event_ids=["ee_1"],
        clock=clock,
    )
    record = repository.misconception(mc_id)
    assert record is not None
    assert record.status == "active"
    assert record.facet_ids == ["coord_change"]
    assert record.source_error_event_ids == ["ee_1"]
    assert record.resolved_at is None

    # Fetch by LO and by concept honors the status filter.
    assert [m.id for m in repository.misconceptions_for_learning_object("lo_svd")] == [mc_id]
    assert [m.id for m in repository.misconceptions_for_concepts(["c_svd"])] == [mc_id]

    # Append provenance + bump severity, flip to resolving then resolved.
    later = FrozenClock(NOW + timedelta(minutes=5))
    repository.update_misconception(
        mc_id,
        severity=0.8,
        status="resolving",
        append_source_error_event_ids=["ee_1", "ee_2"],
        clock=later,
    )
    resolving = repository.misconception(mc_id)
    assert resolving.status == "resolving"
    assert resolving.severity == 0.8
    assert resolving.source_error_event_ids == ["ee_1", "ee_2"]
    assert resolving.resolved_at is None

    resolved_clock = FrozenClock(NOW + timedelta(minutes=10))
    repository.update_misconception(mc_id, status="resolved", clock=resolved_clock)
    resolved = repository.misconception(mc_id)
    assert resolved.status == "resolved"
    assert resolved.resolved_at is not None
    # Resolved rows drop out of the default active/resolving views.
    assert repository.misconceptions_for_learning_object("lo_svd") == []
    assert repository.misconceptions_for_learning_object("lo_svd", statuses=("resolved",))

    # Reactivation clears resolved_at.
    repository.update_misconception(mc_id, status="active", clock=FrozenClock(NOW + timedelta(minutes=15)))
    reactivated = repository.misconception(mc_id)
    assert reactivated.status == "active"
    assert reactivated.resolved_at is None


def test_error_event_misconception_backfill(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    repository = Repository(paths.sqlite_path)

    repository.insert_error_event(
        {
            "id": "ee_1",
            "attempt_id": "attempt_1",
            "learning_object_id": "lo_svd",
            "error_type": "conceptual_slip",
            "severity": 0.6,
            "is_misconception": True,
            "misconception_statement": "reverses Q / Q^T roles",
            "misconception_consistent_answer": "Qx is the coordinate vector",
            "status": "active",
            "created_at": NOW_ISO,
            "updated_at": NOW_ISO,
        }
    )
    events = repository.error_events_for_attempt("attempt_1")
    assert events[0]["misconception_id"] is None
    assert events[0]["misconception_statement"] == "reverses Q / Q^T roles"
    assert events[0]["misconception_consistent_answer"] == "Qx is the coordinate vector"

    assert repository.set_error_event_misconception("ee_1", "mc_01", clock=FrozenClock(NOW)) is True
    assert repository.error_events_for_attempt("attempt_1")[0]["misconception_id"] == "mc_01"
    # ActiveErrorEvent carries the new fields too.
    active = repository.active_errors_by_learning_object("lo_svd")
    assert active[0].misconception_id == "mc_01"
    assert active[0].misconception_statement == "reverses Q / Q^T roles"


def test_item_misconception_discrimination_upsert_and_math(tmp_path):
    from learnloop.db.repositories import ItemMisconceptionDiscrimination

    paths = create_basic_vault(tmp_path / "vault")
    repository = Repository(paths.sqlite_path)

    # Flat Beta(1,1) prior: mean 0.5, 25th-percentile lower bound 0.25, J = 0.
    flat = ItemMisconceptionDiscrimination(
        practice_item_id="pi_1",
        misconception_id="mc_1",
        sensitivity_alpha=1.0,
        sensitivity_beta=1.0,
        specificity_alpha=1.0,
        specificity_beta=1.0,
        n_planted_trials=0,
        n_clean_trials=0,
        source="sim",
        updated_at=NOW_ISO,
    )
    repository.upsert_item_misconception_discrimination(flat)
    stored = repository.discrimination_row("pi_1", "mc_1")
    assert stored.sensitivity_mean == 0.5
    assert stored.sensitivity_lb(0.25) == pytest.approx(0.25, abs=1e-6)
    assert stored.youden_j == pytest.approx(0.0)

    # High-evidence discriminator: sens 0.9, spec 0.95; lb close to mean, J high.
    strong = ItemMisconceptionDiscrimination(
        practice_item_id="pi_1",
        misconception_id="mc_1",
        sensitivity_alpha=45.0,
        sensitivity_beta=5.0,
        specificity_alpha=95.0,
        specificity_beta=5.0,
        n_planted_trials=50,
        n_clean_trials=100,
        source="empirical",
        updated_at=NOW_ISO,
    )
    repository.upsert_item_misconception_discrimination(strong)  # upsert overwrites
    updated = repository.discrimination_row("pi_1", "mc_1")
    assert updated.n_planted_trials == 50
    assert updated.sensitivity_mean == pytest.approx(0.9, abs=1e-9)
    assert updated.sensitivity_lb(0.25) < updated.sensitivity_mean
    assert updated.sensitivity_lb(0.25) > 0.85
    assert updated.youden_j == pytest.approx(0.85, abs=1e-6)
    assert updated.youden_j_lb(0.25) < updated.youden_j

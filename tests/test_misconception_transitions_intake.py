"""B2: misconception transition events make relapse durable, and the three-way
remediation intake never mints a repair case from a one-off mechanism event."""

from __future__ import annotations

from learnloop.clock import FrozenClock
from learnloop.db.repositories import MisconceptionRecord, Repository
from learnloop.services.remediation import misconception_status_history
from learnloop.services.remediation_intake import classify_intake

from tests.helpers import NOW, create_basic_vault

LO_ID = "lo_svd_definition"


def _repository(tmp_path) -> Repository:
    paths = create_basic_vault(tmp_path / "vault")
    return Repository(paths.sqlite_path)


def _insert(repository, status="active"):
    return repository.insert_misconception(
        learning_object_id=LO_ID,
        statement="Confuses SVD with eigendecomposition.",
        facet_ids=["recall"],
        target_facet="recall",
        confused_with_facet="application",
        severity=0.8,
        status=status,
        clock=FrozenClock(NOW),
    )


# -- Transition events / reactivation ----------------------------------------


def test_reactivation_wipes_resolved_at_but_returned_stays_derivable(tmp_path):
    repository = _repository(tmp_path)
    misconception_id = _insert(repository)

    repository.update_misconception(misconception_id, status="resolved", clock=FrozenClock(NOW))
    resolved = repository.misconception(misconception_id)
    assert resolved.status == "resolved"
    assert resolved.resolved_at is not None

    # Reactivation: the current-state timestamp is wiped (fact 5)...
    repository.update_misconception(misconception_id, status="active", clock=FrozenClock(NOW))
    returned = repository.misconception(misconception_id)
    assert returned.status == "active"
    assert returned.resolved_at is None

    # ...but the transition event log preserves the full lifecycle, so
    # 'returned' is derivable forever.
    events = repository.misconception_transition_events(misconception_id)
    assert [(event["from_status"], event["to_status"]) for event in events] == [
        (None, "active"),
        ("active", "resolved"),
        ("resolved", "active"),
    ]
    history = misconception_status_history(repository, misconception_id)
    assert [entry["label"] for entry in history] == ["active", "resolved", "returned"]


def test_status_noop_update_emits_no_transition_event(tmp_path):
    repository = _repository(tmp_path)
    misconception_id = _insert(repository)
    repository.update_misconception(misconception_id, severity=0.9, clock=FrozenClock(NOW))
    events = repository.misconception_transition_events(misconception_id)
    assert [event["to_status"] for event in events] == ["active"]


# -- Three-way intake (spec §3) -----------------------------------------------


def _record(status: str) -> MisconceptionRecord:
    return MisconceptionRecord(
        id="m1",
        learning_object_id=LO_ID,
        concept_id=None,
        statement="Confuses SVD with eigendecomposition.",
        signature=None,
        facet_ids=["recall"],
        severity=0.8,
        status=status,
        source_error_event_ids=[],
        created_at="2026-05-19T12:00:00Z",
        updated_at="2026-05-19T12:00:00Z",
        resolved_at=None,
    )


def test_repair_requires_a_durable_active_or_resolving_registry_row():
    assert classify_intake(misconception=_record("active")) == "repair"
    assert classify_intake(misconception=_record("resolving")) == "repair"
    # A resolved row is not an open case.
    assert classify_intake(misconception=_record("resolved")) != "repair"


def test_lone_misconception_mechanism_event_is_not_a_repair_case():
    # is_misconception=true on one graded error is promotion evidence, not a
    # committed statement-pair case (spec §3 rule 1).
    route = classify_intake(misconception=None, mechanism_is_misconception=True)
    assert route == "diagnose"


def test_unexamined_facet_with_no_exposure_routes_to_read_first():
    route = classify_intake(
        facet_state_label="unexamined",
        has_source_exposure=False,
        mechanism_is_misconception=True,
    )
    assert route == "read_first"
    # Exposure exists: reading again is not the treatment.
    assert (
        classify_intake(facet_state_label="unexamined", has_source_exposure=True)
        == "diagnose"
    )


def test_unresolved_cause_and_repeated_failure_route_to_diagnose():
    assert classify_intake(unresolved_cause=True) == "diagnose"
    assert classify_intake(repeated_failure_despite_coverage=True) == "diagnose"


def test_durable_row_wins_over_every_other_signal():
    route = classify_intake(
        misconception=_record("active"),
        facet_state_label="unexamined",
        has_source_exposure=False,
        unresolved_cause=True,
        repeated_failure_despite_coverage=True,
    )
    assert route == "repair"

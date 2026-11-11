"""B2: misconception transition events make relapse durable."""

from __future__ import annotations

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.diagnosis.remediation import misconception_status_history

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

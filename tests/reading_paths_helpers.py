"""What other test files use from ``tests/test_reading_paths.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from learnloop.db.repositories import MasteryState
from learnloop.db.stores import placement as placement_store


def _demonstrate(monkeypatch, *lo_ids):
    import learnloop.goals.goal_certification as GC

    real = GC.lo_certification

    def fake(vault, repository, learning_object, **kwargs):
        found = real(vault, repository, learning_object, **kwargs)
        if learning_object.id in lo_ids:
            return type(found)(learning_object_id=learning_object.id, demonstrated=True, component_gaps=(),
                               integration_gaps=())
        return found

    monkeypatch.setattr(GC, "lo_certification", fake)


def _assume(repository, lo_id, assumption_id="as_1"):
    with repository.atomic():
        placement_store.insert_assumption_decision(repository.connection(), {
            "id": assumption_id, "learning_object_id": lo_id, "source": "self_report", "trigger_kind": "i_know_this",
            "trigger_ref": None, "p": None, "interval_json": None, "q_used": None, "theta_known": None,
            "predictor": "self_report", "predictor_version": "v1", "first_review_due": "2026-12-01T00:00:00Z",
            "quick_check_session_id": None, "algorithm_version": "mvp-0.29", "config_json": "{}",
            "inputs_json": "{}", "created_at": "2026-10-01T00:00:00Z"})


def _practised(repository, lo_id):
    repository.upsert_mastery_state(MasteryState(
        learning_object_id=lo_id, logit_mean=0.0, logit_variance=1.0, evidence_count=1,
        last_evidence_at="2026-10-11T00:00:00Z", algorithm_version="mvp-0.29", updated_at="2026-10-11T00:00:00Z"))

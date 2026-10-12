"""Daily-loop follow-up: a stale open session hid the welcome-back panel.

``start_session`` ends any session left open (the app was closed mid-session) and
stamped it ``ended_at = now``. The welcome-back gap is measured from the latest
session end, so that stamp reset the break to zero and the panel never showed
after a break that began with the app closed mid-session. It also stretched the
stale session's duration over the whole break.

The break is now measured from the learner's last real activity: the stale
session is ended at its own last activity (its last attempt or checkpoint, else
its start), and an attempt made outside any session counts as activity too.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from learnloop.attempts.attempts import ApplyAttemptInput, AttemptDraft, ResolvedGrade, apply_attempt
from learnloop.clock import FrozenClock
from learnloop.ids import new_ulid
from learnloop.vault.loader import load_vault

from tests.helpers import create_basic_vault, seed_due_item

ITEM_ID = "pi_svd_define_001"


def _iso(moment: datetime) -> str:
    return moment.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _backdated_session(repository, *, started: datetime, ended: datetime | None) -> str:
    session_id = repository.create_session(available_minutes=20)
    with repository.connection() as connection:
        connection.execute(
            "UPDATE sessions SET started_at = ?, ended_at = ?, updated_at = ? WHERE id = ?",
            (_iso(started), _iso(ended) if ended else None, _iso(started), session_id),
        )
        connection.commit()
    return session_id


def _attempt(vault_root, repository, *, at: datetime, session_id: str | None) -> None:
    apply_attempt(
        load_vault(vault_root),
        repository,
        ApplyAttemptInput(
            draft=AttemptDraft(practice_item_id=ITEM_ID, learner_answer_md="U Sigma V^T",
                               attempt_type="independent_attempt", session_id=session_id),
            attempt_id=new_ulid(),
            grade=ResolvedGrade(rubric_score=4, criterion_points={"correctness": 4.0}, evidence_rows=[],
                                error_attributions=[], grader_confidence=1.0, confidence=4,
                                manual_review_reason=None),
            grading_source="ai",
        ),
        clock=FrozenClock(at),
    )


def _ctx(root):
    import learnloop_sidecar.handlers  # noqa: F401
    from learnloop_sidecar.context import SidecarContext

    context = SidecarContext()
    context.load(root)
    context.grading_provider_override = "manual"
    return context


def _call(ctx, name: str, params: dict):
    from learnloop_sidecar.registry import METHOD_REGISTRY

    spec = METHOD_REGISTRY[name]
    return spec.handler(ctx, spec.params_model.model_validate(params))


def test_a_stale_open_session_does_not_hide_the_welcome_back(tmp_path):
    now = datetime.now(UTC)
    paths = create_basic_vault(tmp_path / "vault")
    repository = seed_due_item(paths)
    _backdated_session(repository, started=now - timedelta(days=30, minutes=40), ended=now - timedelta(days=30))
    # The app was closed mid-session 20 days ago: the session is still open.
    last_activity = now - timedelta(days=20)
    stale = _backdated_session(repository, started=last_activity - timedelta(minutes=10), ended=None)
    _attempt(paths.root, repository, at=last_activity, session_id=stale)

    ctx = _ctx(paths.root)
    _call(ctx, "start_session", {"availableMinutes": 20})

    # The stale session ends where the learner stopped, not when the app noticed.
    assert repository.fetch_session(stale)["ended_at"] == _iso(last_activity)
    summary = _call(ctx, "get_reentry_summary", {})["summary"]
    assert summary["show"] is True
    assert summary["gapDays"] == 20


def test_an_attempt_outside_any_session_is_real_activity(tmp_path):
    """The last attempt counts even when it belongs to no session, so a learner who
    practised two days ago is not welcomed back from a month-old session end."""

    now = datetime.now(UTC)
    paths = create_basic_vault(tmp_path / "vault")
    repository = seed_due_item(paths)
    _backdated_session(repository, started=now - timedelta(days=30, minutes=40), ended=now - timedelta(days=30))
    _attempt(paths.root, repository, at=now - timedelta(days=2), session_id=None)

    summary = _call(_ctx(paths.root), "get_reentry_summary", {})["summary"]
    assert summary["show"] is False
    assert summary["gapDays"] == 2


def test_the_current_sessions_own_attempts_do_not_end_the_re_entry(tmp_path):
    """Practising inside the re-entry session must not reset the break mid-session."""

    now = datetime.now(UTC)
    paths = create_basic_vault(tmp_path / "vault")
    repository = seed_due_item(paths)
    _backdated_session(repository, started=now - timedelta(days=30, minutes=40), ended=now - timedelta(days=30))
    ctx = _ctx(paths.root)
    session = _call(ctx, "start_session", {"availableMinutes": 20})
    _attempt(paths.root, repository, at=now, session_id=session["sessionId"])

    summary = _call(ctx, "get_reentry_summary", {})["summary"]
    assert summary["show"] is True
    assert summary["gapDays"] == 30

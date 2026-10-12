"""Daily-loop audit 2026-10-11: the welcome-back "N refreshers" did not limit the queue.

After a break the Today screen's welcome-back panel says "Your best next session:
N refreshers" (``reentry_summary.refresher_count``), but ``get_today_queue`` built
the full, unlimited queue, so the session served far more. Owner decision P6:
re-entry is a small automatic session of the most useful checks and reviews. While
re-entry shows, the queue is now limited to that number (the scheduler's own top
picks), and it reports the cap it applied so the panel can show the served count.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

from learnloop.scheduling import reentry_summary as re_mod

from tests.helpers import add_followup_item, create_basic_vault, seed_due_item

LO_ID = "lo_svd_definition"
SECOND_ITEM = "pi_svd_define_002"


def _iso(moment: datetime) -> str:
    return moment.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _vault_after_a_break(tmp_path, monkeypatch, *, days_away: int):
    """Two due items, and a last session that ended ``days_away`` days ago. FSRS
    decay is faked so exactly one facet slipped below target while away."""

    import learnloop_sidecar.handlers  # noqa: F401
    from learnloop_sidecar.context import SidecarContext

    paths = create_basic_vault(tmp_path / "vault")
    repository = seed_due_item(paths)
    add_followup_item(paths.root, SECOND_ITEM)
    repository.upsert_practice_item_state(
        SECOND_ITEM, difficulty=5.0, stability=2.0, due_at="2026-05-18T12:00:00Z",
        last_attempt_at="2026-05-16T12:00:00Z", active=True,
    )
    ended = datetime.now(UTC) - timedelta(days=days_away)
    old = repository.create_session(energy=None, sleep_quality=None, available_minutes=20, notes_md_path=None)
    repository.end_session(old)
    with repository.connection() as connection:
        connection.execute(
            "UPDATE sessions SET started_at = ?, ended_at = ? WHERE id = ?",
            (_iso(ended - timedelta(minutes=30)), _iso(ended), old),
        )
        connection.commit()

    def projections(vault, repository, goal, at, *, clock=None):
        at_last_end = abs((at.astimezone(UTC) - ended).total_seconds()) < 3600
        return [
            SimpleNamespace(learning_object_id=LO_ID, facet_id="recall", decay_estimated=True,
                            ready=0.9 if at_last_end else 0.5),       # slipped while away
            SimpleNamespace(learning_object_id=LO_ID, facet_id="definition", decay_estimated=True,
                            ready=0.95 if at_last_end else 0.9),      # still solid
        ]

    monkeypatch.setattr(re_mod, "facet_projections_at", projections)
    context = SidecarContext()
    context.load(paths.root)
    context.grading_provider_override = "manual"
    return context


def _call(ctx, name: str, params: dict):
    from learnloop_sidecar.registry import METHOD_REGISTRY

    spec = METHOD_REGISTRY[name]
    return spec.handler(ctx, spec.params_model.model_validate(params))


def _served(queue) -> list[str]:
    return [item["practiceItemId"] for section in queue["sections"] for item in section["items"]]


def test_reentry_session_serves_exactly_the_refreshers_the_panel_shows(tmp_path, monkeypatch):
    ctx = _vault_after_a_break(tmp_path, monkeypatch, days_away=30)
    session = _call(ctx, "start_session", {"availableMinutes": 30})

    summary = _call(ctx, "get_reentry_summary", {})["summary"]
    assert summary["show"] is True and summary["refresherCount"] == 1

    queue = _call(ctx, "get_today_queue", {"sessionId": session["sessionId"]})
    assert queue["totalItems"] == len(_served(queue)) == summary["refresherCount"]
    assert queue["reentryRefresherCap"] == 1


def test_reentry_cap_never_widens_a_smaller_requested_limit(tmp_path, monkeypatch):
    ctx = _vault_after_a_break(tmp_path, monkeypatch, days_away=30)
    queue = _call(ctx, "get_today_queue", {"limit": 0})
    assert queue["totalItems"] == 0


def test_without_a_break_the_queue_is_not_capped(tmp_path, monkeypatch):
    ctx = _vault_after_a_break(tmp_path, monkeypatch, days_away=1)
    session = _call(ctx, "start_session", {"availableMinutes": 30})
    assert _call(ctx, "get_reentry_summary", {})["summary"]["show"] is False

    queue = _call(ctx, "get_today_queue", {"sessionId": session["sessionId"]})
    assert queue["reentryRefresherCap"] is None
    assert {"pi_svd_define_001", SECOND_ITEM} <= set(_served(queue))

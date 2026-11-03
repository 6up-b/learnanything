"""Follow-ups batch 7 verify V1: a decision is linked to the request that was served.

A rich-only prebuild has no figure until its job stores one. So when an enqueue failure left an
orphan request (no figure, no job), a successful retry's request had no figure yet either, and
``_link`` took the older orphan, once and for good. The figure the retry's job stored later belonged
to a request the decision did not name: opening it closed the decision ``neither``, and the opening
model learned the opposite of what happened.

``_link`` and ``link_stored_requests`` now share one predicate: a request is served when it names a
figure or its rich job exists. Through the pass's own functions and the durable job queue; fakes for
the judge and the authors.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest

from learnloop.attempts.salience_firewall import salience_payload
from learnloop.clock import FrozenClock
from learnloop.figures import power as P
from learnloop.figures import prefetch as PF
from learnloop.figures import prefetch_ledger as PL
from learnloop.figures import rich as RICH
from learnloop.substrate.activities import log_interaction_event
from learnloop_sidecar import prefetch_runtime as RT
from tests import rich_fixtures as RF
from tests.figure_fixtures import EXTRACTION, build, rows
from tests.test_figures_prefetch import decisions
from tests.test_followups_batch6_prefetch_plan_wait import RICH_ONLY, _prebuild_jobs, _rig

DAY = datetime(2099, 3, 1, 12, tzinfo=UTC)
TRIGGER = PF.Trigger("offer", "tutor:q1", blocks=((EXTRACTION, "p3"),))
#: The same passage, so the decision's open row keeps it out: only the queue runs.
AGAIN = PF.Trigger("offer", "tutor:q2", blocks=((EXTRACTION, "p3"),))


@pytest.fixture(autouse=True)
def mains(monkeypatch):
    P.set_power_reader(lambda: P.PowerState(True, P.MAINS, "test"))
    monkeypatch.setattr(RICH, "_LAST_REQUEUE", {})
    yield
    P.set_power_reader(None)


def _queued_rig(tmp_path: Any, monkeypatch: Any) -> tuple[Any, Any, Any]:
    """A rich-only prebuild on the menu whose job waits in the queue until :func:`_drain`."""

    _paths, repository, ctx, rich_author = _rig(tmp_path, monkeypatch, [RF.scene_output()],
                                                author_answers=(RICH_ONLY, RICH_ONLY, RICH_ONLY))
    monkeypatch.setattr(ctx.ingest_jobs, "_ensure_worker", lambda: None)
    return repository, ctx, rich_author


def _drain(ctx: Any) -> None:
    ctx.ingest_jobs.drain_foreground()


def _env(ctx: Any, when: datetime, **changes: Any) -> PF.PrefetchEnv:
    return replace(RT.environment(ctx, None), clock=FrozenClock(when), **changes)


def _no_enqueue(payload: dict[str, Any]) -> None:
    """The durable queue refused the job: ``_RichSpawn.only`` refuses the build, its request stored."""

    return None


def _requests(repository: Any, decision_id: str) -> list[dict[str, Any]]:
    return [row for row in rows(repository, "figure_requests") if row["prefetch_decision_id"] == decision_id]


def _with_an_orphan(repository: Any, ctx: Any) -> tuple[dict[str, Any], str]:
    """A rich-only build whose enqueue failed: an open decision and a request with neither."""

    result = PF.run_trigger(_env(ctx, DAY, spawn_rich=_no_enqueue), TRIGGER)
    (decision,) = decisions(repository)
    assert result.built == [] and decision["request_id"] is None and decision["outcome"] is None
    (orphan,) = _requests(repository, decision["id"])
    assert orphan["figure_id"] is None and RICH.rich_job_for_request(repository, orphan["id"]) is None
    assert _prebuild_jobs(repository) == []
    return decision, orphan["id"]


def _opened_at(repository: Any, figure_id: str, when: datetime) -> None:
    log_interaction_event(repository, kind="reader_action_invoked", origin="learner", subject_type="reader_extraction",
                          subject_id=EXTRACTION, payload=salience_payload({"event": "figure_opened", "figure_id": figure_id}),
                          clock=FrozenClock(when))


def _observation(repository: Any) -> Any:
    (observed,) = PL.observations(decisions(repository))
    return observed


def test_a_rich_only_retry_after_an_orphan_is_linked_and_opening_its_eventual_figure_closes_opened(tmp_path, monkeypatch):
    repository, ctx, _rich_author = _queued_rig(tmp_path, monkeypatch)
    decision, orphan = _with_an_orphan(repository, ctx)

    retried = PF.run_trigger(_env(ctx, DAY + timedelta(minutes=1)), AGAIN)
    assert retried.built == [decision["id"]]
    (job,) = _prebuild_jobs(repository)
    served = str(job["payload"]["request_id"])
    assert served != orphan
    # No figure yet: the retry's request is the one its job will name.
    (row,) = decisions(repository)
    assert row["request_id"] == served
    assert {found["figure_id"] for found in _requests(repository, decision["id"])} == {None}

    _drain(ctx)
    figure_id = next(found["figure_id"] for found in _requests(repository, decision["id"]) if found["id"] == served)
    assert figure_id
    _opened_at(repository, figure_id, DAY + timedelta(minutes=30))
    assert PF.close_horizons(_env(ctx, DAY + timedelta(days=1))) == 1
    (row,) = decisions(repository)
    assert row["request_id"] == served and row["outcome"] == "opened"
    assert _observation(repository).opened is True


def test_the_same_retry_whose_pass_died_before_it_linked_is_linked_the_same_way(tmp_path, monkeypatch):
    """The other caller of the one predicate: ``link_stored_requests``, on the next pass."""

    repository, ctx, _rich_author = _queued_rig(tmp_path, monkeypatch)
    decision, orphan = _with_an_orphan(repository, ctx)
    with monkeypatch.context() as patch:
        patch.setattr(PF, "_link", lambda env, decision_id: True)
        PF.run_trigger(_env(ctx, DAY + timedelta(minutes=1)), AGAIN)
    (row,) = decisions(repository)
    assert row["request_id"] is None

    assert PF.link_stored_requests(_env(ctx, DAY + timedelta(minutes=2))) == 1
    (job,) = _prebuild_jobs(repository)
    (row,) = decisions(repository)
    assert row["request_id"] == job["payload"]["request_id"] != orphan


def test_a_retry_whose_enqueue_fails_again_links_nothing_and_stays_in_the_queue(tmp_path, monkeypatch):
    repository, ctx, _rich_author = _queued_rig(tmp_path, monkeypatch)
    decision, _orphan = _with_an_orphan(repository, ctx)
    result = PF.run_trigger(_env(ctx, DAY + timedelta(minutes=1), spawn_rich=_no_enqueue), AGAIN)
    assert result.built == []
    (row,) = decisions(repository)
    assert row["request_id"] is None and row["outcome"] is None
    assert [found[0]["id"] for found in PF.pending_builds(_env(ctx, DAY + timedelta(minutes=2)))] == [decision["id"]]


def test_waiting_on_someone_elses_rich_job_builds_nothing_and_its_figure_is_taken_once_stored(tmp_path, monkeypatch):
    """A request recorded against another request's pending job is served by neither predicate arm:
    that job's figure will name the other request, so linking here would lose the opening too. The
    row waits, no model is called, and the next pass reuses the stored figure on a request naming it."""

    repository, ctx, rich_author = _queued_rig(tmp_path, monkeypatch)
    pressed = build(ctx)
    assert pressed["rich"]["state"] == "pending" and rich_author.calls == 0
    authored = ctx.figure_author_client.calls

    result = PF.run_trigger(_env(ctx, DAY), TRIGGER)
    (decision,) = decisions(repository)
    assert result.built == [] and decision["request_id"] is None and decision["outcome"] is None
    assert ctx.figure_author_client.calls == authored and rich_author.calls == 0
    (waiting,) = _requests(repository, decision["id"])
    assert waiting["figure_id"] is None

    _drain(ctx)
    assert rich_author.calls == 1
    later = PF.run_trigger(_env(ctx, DAY + timedelta(minutes=1)), AGAIN)
    assert later.built == [decision["id"]] and ctx.figure_author_client.calls == authored and rich_author.calls == 1
    (row,) = decisions(repository)
    named = next(found for found in _requests(repository, decision["id"]) if found["id"] == row["request_id"])
    assert named["figure_id"]
    _opened_at(repository, named["figure_id"], DAY + timedelta(minutes=30))
    assert PF.close_horizons(_env(ctx, DAY + timedelta(days=1))) == 1
    (row,) = decisions(repository)
    assert row["outcome"] == "opened" and _observation(repository).opened is True

"""R12: Next never leaves a ready probe unserved with the answer held. Every surface, plan state and
workflow state, through the real handlers, with the fetch of the next step the screen makes while
feedback shows (``dailyPlan.ts``). Each cell asserts one thing: the next thing served is the probe,
or the feedback is released and Next goes on.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import timedelta
from types import SimpleNamespace

import pytest

from learnloop.clock import FrozenClock, SystemClock
from learnloop.diagnosis.split.jobs import drain
from learnloop.followup_run import jobs, router
from learnloop.followup_serve import identity, workflow as wf
from learnloop_sidecar import handlers  # noqa: F401 - registers the methods
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.registry import METHOD_REGISTRY

from tests.followup_serve_helpers import (
    LIVE_ITEM,
    AuthorFake,
    BlindRivalClient,
    author_clients,
    live_shape_vault,
)

PLAN_OFF = "\n[plan]\nenabled = false\n"
ARMS = {"preparing": router.ASK_NOW, "ready": router.ASK_NOW, "waiting": router.WAIT, "pending_wait": router.WAIT,
        "failed": router.ASK_NOW, "settled": router.NO_INTERVENTION}
#: (surface, plan state, when it closes): a plan can close before generation or after it.
PLAN_CELLS = [
    ("plan", "open", None), ("plan", "complete", "before"), ("plan", "stopped", "before"), ("plan", "stopped", "after"),
    ("queue", "open", None), ("queue", "complete", "before"), ("queue", "stopped", "before"),
    ("queue", "stopped", "after"), ("queue", "none", None),
    ("no_plan", "none", None),
]
CELLS = [(*cell, state) for cell in PLAN_CELLS for state in ARMS]


class _Ready:
    ready = True
    status = "ready"
    active_provider = "fake"
    provider_type = "codex_sdk"
    model = "fake-model"
    provider_revision = None
    message = None


class _Desk(SimpleNamespace):
    def call(self, name, params):
        spec = METHOD_REGISTRY[name]
        return spec.handler(self.ctx, spec.params_model.model_validate(params))

    @property
    def repository(self):
        return self.ctx.require_vault()[1]

    def step(self, *, serve):
        """What the screen reads for the plan's next step; ``serve=False`` is its fetch while feedback shows."""

        result = self.call("next_plan_item", {"sessionId": self.session, "serve": serve})
        step = result.get("step") or {}
        return {**step, "item": step.get("practiceItemId") or step.get("practice_item_id")}

    def jobs(self, fake=None, *, hours=0):
        vault, repository = self.ctx.require_vault()
        clock = FrozenClock(SystemClock().now() + timedelta(hours=hours)) if hours else None
        clients = author_clients(fake or AuthorFake())
        while jobs.process_next_job(vault, repository, owner="test", clients=clients, clock=clock) is not None:
            pass


def _desk(tmp_path, monkeypatch, *, config="", arm=None):
    paths, _vault, _repository = live_shape_vault(tmp_path, config=config)
    ctx = SidecarContext()
    ctx.load(paths.root)
    ctx.post_attempt_worker.autostart = False
    client = BlindRivalClient()
    monkeypatch.setattr("learnloop_sidecar.handlers.practice.ready_grading_provider",
                        lambda *_a, **_k: ("fake", _Ready(), client))
    if arm is not None:
        real = router.decide
        monkeypatch.setattr(router, "decide", lambda *a, **k: replace(real(*a, **k), chosen_ref=arm, reason=arm))
    desk = _Desk(ctx=ctx, client=client, paths=paths, session=None)
    started = desk.call("start_session", {"available_minutes": 45})
    desk.session = started.get("sessionId") or started["session_id"]
    return desk


def _miss(desk, surface):
    """A miss, with its diagnosis drained: the workflow's job is queued and not yet run."""

    params = {"sessionId": desk.session, "answerMd": "A = U Sigma V wrong", "attemptType": "independent_attempt",
              "latencySeconds": 60}
    if surface == "plan":
        step = desk.step(serve=True)
        assert step["kind"] == "item"
        params.update(practiceItemId=step["item"], planPresentationId=step.get("presentationId") or step.get("planPresentationId"))
        desk.call("get_practice_item", {"practiceItemId": step["item"], "sessionId": desk.session})
    else:
        params["practiceItemId"] = LIVE_ITEM
    result = desk.call("submit_attempt", params)
    attempt_id = result.get("attemptId") or result["attempt_id"]
    vault, repository = desk.ctx.require_vault()
    drain(vault, repository, client_factory=lambda: desk.client, embedding_factory=lambda: None)
    return attempt_id


def _finish_the_plan(desk):
    """Every other step of the plan answered or passed, with the screen's fetch after each."""

    for _ in range(40):
        step = desk.step(serve=False)
        if step.get("kind") != "item":
            return
        desk.call("next_plan_item", {"sessionId": desk.session, "skipPracticeItemId": step["item"]})
    raise AssertionError("the plan didn't end")


def _close(desk, state):
    if state == "stopped":
        desk.call("plan_keep_going", {"sessionId": desk.session, "stop": True})
    else:
        _finish_the_plan(desk)
    assert desk.call("get_daily_plan", {"sessionId": desk.session})["plan"]["status"] in {"stopped", "complete"}


def _held(desk, attempt_id):
    return (desk.call("get_feedback", {"attemptId": attempt_id}).get("followup") or {}).get("held")


def _answer_the_probe(desk, probe, attempt_id):
    desk.ctx.reload(maintenance=False)
    desk.call("open_queue_item", {"practiceItemId": probe})
    contract = desk.call("get_probe_contract", {"practiceItemId": probe})
    assert contract["active"] is True
    desk.call("submit_attempt", {
        "sessionId": desk.session, "practiceItemId": probe, "answerMd": "An answer.", "attemptType": "diagnostic_probe",
        "latencySeconds": 40, "probePresentationId": contract["presentationId"],
    })
    assert _held(desk, attempt_id) is False
    assert desk.call("followup_next", {"attemptId": attempt_id})["action"] == "continue"


def _the_one_thing(desk, attempt_id, *, plan_open):
    """The next thing served is the probe, or the feedback is released and Next goes on."""

    repository = desk.repository
    row = wf.attempt_workflow(repository, attempt_id)
    action = desk.call("followup_next", {"attemptId": attempt_id})
    assert action["action"] != "wait", row
    probe = row.get("practice_item_id")
    if action["action"] == "open":
        assert action["practiceItemId"] == probe
        _answer_the_probe(desk, probe, attempt_id)
        return "served"
    if plan_open and row["state"] == wf.READY:
        step = desk.step(serve=True)
        assert step.get("item") == probe, (step, row)
        _answer_the_probe(desk, probe, attempt_id)
        return "served"
    assert _held(desk, attempt_id) is False, row
    return "released"


@pytest.mark.parametrize("surface, plan, closes, state", CELLS)
def test_the_matrix(tmp_path, monkeypatch, surface, plan, closes, state):
    desk = _desk(tmp_path, monkeypatch, config=PLAN_OFF if surface == "no_plan" else "", arm=ARMS[state])
    if plan != "none":
        desk.call("get_daily_plan", {"sessionId": desk.session})
    attempt_id = _miss(desk, surface)
    repository = desk.repository
    assert wf.attempt_workflow(repository, attempt_id)["state"] == wf.PENDING
    if closes == "before":
        _close(desk, plan)
    fake = AuthorFake(same_predictions=state == "failed")
    if state == "preparing":
        action = desk.call("followup_next", {"attemptId": attempt_id})
        assert action["action"] == "wait" and action["line"].startswith("Preparing")
        desk.jobs(fake)
    elif state == "pending_wait":
        desk.jobs(AuthorFake(error=RuntimeError("provider down")))
        row = wf.attempt_workflow(repository, attempt_id)
        assert row["state"] == wf.PENDING and row["chosen_ref"] == router.WAIT
        assert row["feedback_released_at"] and row["exposed_at"]  # §6.0: released now, the later probe labelled
        assert desk.call("followup_next", {"attemptId": attempt_id})["action"] == "continue"
    else:
        desk.jobs(fake)
    desk.step(serve=False)  # the screen's fetch while feedback shows
    if closes == "after":
        _close(desk, plan)
    row = wf.attempt_workflow(repository, attempt_id)
    if state == "failed":
        assert row["state"] == wf.FAILED
    if state == "settled":
        assert row["state"] == wf.SETTLED
    if state == "waiting":
        assert row["state"] == wf.WAITING and row["exposed_at"] and row["feedback_released_at"]
    result = _the_one_thing(desk, attempt_id, plan_open=plan == "open" and surface == "plan")
    if state in {"preparing", "ready"}:
        assert result == "served"
    else:
        assert result == "released"
    if state == "pending_wait":
        desk.jobs(hours=1)  # the retry finishes it, whatever became of the plan
        after = wf.attempt_workflow(repository, attempt_id)
        assert after["state"] in {wf.WAITING, wf.FAILED, wf.READY} and after["exposed_at"]
        assert _held(desk, attempt_id) is False


def test_a_queue_miss_with_a_plan_open_opens_the_probe_and_the_plan_doesnt_serve_it_again(tmp_path, monkeypatch):
    desk = _desk(tmp_path, monkeypatch, arm=router.ASK_NOW)
    desk.call("get_daily_plan", {"sessionId": desk.session})
    attempt_id = _miss(desk, "queue")
    desk.jobs()
    probe = wf.attempt_workflow(desk.repository, attempt_id)["practice_item_id"]
    assert desk.call("followup_next", {"attemptId": attempt_id})["action"] == "open"
    _answer_the_probe(desk, probe, attempt_id)
    assert desk.step(serve=False).get("item") != probe
    assert probe in identity.closed_probe_ids(desk.repository)


def test_a_wait_outlasting_its_plan_comes_first_in_a_later_plan_and_its_answer_is_labelled(tmp_path, monkeypatch):
    desk = _desk(tmp_path, monkeypatch, arm=router.WAIT)
    desk.call("get_daily_plan", {"sessionId": desk.session})
    attempt_id = _miss(desk, "plan")
    desk.jobs()
    desk.call("plan_keep_going", {"sessionId": desk.session, "stop": True})
    row = wf.attempt_workflow(desk.repository, attempt_id)
    assert row["state"] == wf.WAITING and row["exposed_at"] and row["feedback_released_at"]
    assert wf.probe_answer_exposed(desk.repository, row["presentation_id"]) == "followup_feedback_released_before_probe"
    assert desk.call("followup_next", {"attemptId": attempt_id})["action"] == "continue"

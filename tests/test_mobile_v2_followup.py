"""Mobile v2 stage V2, J3 partial (spec §8's V2 row; Codex review of V2, F3): the follow-up panel through
the real phone handlers, without probes.

* A held workflow is held on the phone too, whichever device's miss opened it: the bundle, the diagnosis
  poll and the answer's display refuse what the desktop refuses (before this, a phone reopening a held
  desktop miss saw the repairs and causes before the pending question).
* The phone's bundle carries the workflow's read and the marks panel, exactly as the desktop's.
* *Show anyway* from the phone releases it, and the bundle the phone then reads is the desktop's.
* A phone miss opens its own workflow (surface ``phone``), held; its question is still served on the
  desktop only (the phone's plan holds a generated probe, ``tests/test_mobile_v2_plan.py``).

FG1's own fixtures (a synthetic vault, the faked author); no model and no network.
"""

from __future__ import annotations

import pytest

from learnloop.followup_serve import workflow as wf
from learnloop.followup_serve.gates import PHONE_SURFACE
from learnloop_sidecar import handlers  # noqa: F401 - registers the methods
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.errors import SidecarError
from learnloop_sidecar.registry import METHOD_REGISTRY
from learnloop_sidecar.request_origin import RequestOrigin

from tests.followup_serve_helpers import miss_with_rivals, rival_causes_vault

PHONE = RequestOrigin(device_id="dev_phone")


class _Runtime:
    ready = True
    status = "ready"
    message = None


def _call(ctx, name, params, origin=None):
    spec = METHOD_REGISTRY[name]
    with ctx.acting_as(origin):
        return spec.handler(ctx, spec.params_model.model_validate(params))


@pytest.fixture
def held(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "learnloop_sidecar.handlers.practice.ready_grading_provider",
        lambda *_args, **_kw: ("fake", _Runtime(), object()),
    )
    _vault, _repository, paths = rival_causes_vault(tmp_path)
    ctx = SidecarContext()
    ctx.load(paths.root)
    ctx.post_attempt_worker.autostart = False
    vault, repository = ctx.require_vault()
    result, outcome = miss_with_rivals(vault, repository)
    assert outcome.workflow_id is not None and wf.get(repository, outcome.workflow_id)["feedback_held"] == 1
    return ctx, repository, result, outcome


def test_f3_a_held_desktop_miss_reopened_on_the_phone_stays_held(held):
    ctx, _repository, result, outcome = held
    bundle = _call(ctx, "get_feedback", {"attemptId": result.attempt_id, "recordOpen": False}, PHONE)
    assert bundle["followup"]["held"] is True and bundle["followup"]["workflowId"] == outcome.workflow_id
    assert bundle["feedbackMd"] is None and bundle["repairSuggestions"] == [] and bundle["errorAttributions"] == []
    assert bundle["causalFeedback"] is None
    # The diagnosis poll shows nothing it holds, and the full answer can't be recorded as shown.
    assert _call(ctx, "diagnosis_status", {"attemptId": result.attempt_id}, PHONE)["status"] == "pending"
    with pytest.raises(SidecarError) as refused:
        _call(ctx, "record_answer_display", {"attemptId": result.attempt_id, "displayId": "disp_phone"}, PHONE)
    assert refused.value.code == "followup_feedback_held"


def test_f3_the_phones_bundle_is_the_desktops_held_and_released(held):
    ctx, _repository, result, _outcome = held
    params = {"attemptId": result.attempt_id, "recordOpen": False}
    assert _call(ctx, "get_feedback", params, PHONE) == _call(ctx, "get_feedback", params)
    assert _call(ctx, "followup_show_anyway", {"attemptId": result.attempt_id}, PHONE)["released"] is True
    phone = _call(ctx, "get_feedback", params, PHONE)
    assert phone == _call(ctx, "get_feedback", params)
    assert phone["followup"]["held"] is False and phone["followup"]["shownAnyway"] is True
    assert phone["feedbackMd"] == "Review the factorization."
    # The marks panel rides on the phone's released bundle as on the desktop's.
    assert "hypothesisMarks" in phone


def test_f3_a_door_bundle_on_the_phone_keeps_the_hold(held):
    from learnloop_sidecar.handlers.feedback import _door_bundle

    ctx, repository, result, _outcome = held
    vault, _ = ctx.require_vault()
    with ctx.acting_as(PHONE):
        bundle = _door_bundle(ctx, vault, repository, result.attempt_id)
    assert bundle["followup"]["held"] is True and bundle["feedbackMd"] is None


def test_f3_a_phone_miss_opens_its_workflow_held_under_the_phones_surface(tmp_path):
    from learnloop_sidecar.handlers.practice import followup_surface

    vault, repository, paths = rival_causes_vault(tmp_path)
    ctx = SidecarContext()
    ctx.load(paths.root)
    with ctx.acting_as(PHONE):
        surface = followup_surface(ctx)
    assert surface == PHONE_SURFACE and followup_surface(ctx) == "desktop"
    result, outcome = miss_with_rivals(vault, repository, surface=surface)
    row = wf.get(repository, outcome.workflow_id)
    assert row["surface"] == PHONE_SURFACE and row["feedback_held"] == 1 and row["state"] == wf.PENDING
    assert row["source_attempt_id"] == result.attempt_id


def test_f3_a_ready_question_says_on_the_phone_that_it_waits_for_the_desktop_and_no_phone_door_opens_it(held):
    from learnloop.followup_run.serving import PHONE_HANDOFF_LINE
    from learnloop.followup_serve import identity

    from tests.followup_serve_helpers import AuthorFake, author_clients, run_jobs

    ctx, repository, result, outcome = held
    vault, _ = ctx.require_vault()
    run_jobs(vault, repository, clients=author_clients(AuthorFake()))
    row = wf.get(repository, outcome.workflow_id)
    assert row["state"] == wf.READY and row["practice_item_id"]
    desktop = _call(ctx, "followup_status", {"attemptId": result.attempt_id})
    phone = _call(ctx, "followup_status", {"attemptId": result.attempt_id}, PHONE)
    assert desktop["line"] != PHONE_HANDOFF_LINE and phone["line"] == PHONE_HANDOFF_LINE
    assert {key: value for key, value in phone.items() if key != "line"} == \
        {key: value for key, value in desktop.items() if key != "line"}
    # Still held, and no phone door serves the question (V3).
    assert phone["held"] is True
    session_id = _call(ctx, "start_session", {"availableMinutes": 25})["sessionId"]
    with pytest.raises(SidecarError) as refused:
        _call(ctx, "get_practice_item", {"practiceItemId": row["practice_item_id"], "sessionId": session_id}, PHONE)
    assert refused.value.code == identity.GENERATED_PROBE_RESERVED


def test_f3_the_tui_stays_on_the_predecessors_path(tmp_path):
    vault, repository, _paths = rival_causes_vault(tmp_path)
    _result, outcome = miss_with_rivals(vault, repository, surface=None)
    assert outcome.workflow_id is None

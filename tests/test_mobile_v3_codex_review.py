"""Mobile v2 stage V3, the Codex review's findings (``docs/reviews/phone-v3-codex-review.md``), reproduced first.

* **F1** a phone that does not own the session can't burn a generated probe: every phone door that claims one (the
  session serve, the probe contract, the sessionless queue open) checks the session's owner in the transaction that
  claims it, so the desktop's ready probe stays the desktop's to open;
* **F2** the desktop's serving Next leaves alone a probe the phone served whose answer the host has accepted and is
  still grading: the presentation stays open and the held feedback stays held, so the phone's answer, when it
  commits, is the probe's observation and releases them;
* **F3** a cached V2 app (one that doesn't say it answers probes) gets V2's serving from a V3 host: the plan's step
  holds a generated probe for the desktop and no door burns one; the V3 app says so on every request.

Every model is a fake; no network.
"""

from __future__ import annotations

import pytest

from learnloop import capture
from learnloop.followup_run.serving import is_holding
from learnloop.followup_serve import identity, workflow as wf
from learnloop.followup_serve.gates import PHONE_SURFACE, SERVING_SURFACE
from learnloop_sidecar.request_origin import RequestOrigin

from tests.test_mobile_v3_probes import PHONE, TAG, _adopt, _call, _ready, _refused, _world, world  # noqa: F401


@pytest.fixture
def plan_world(tmp_path, monkeypatch):
    """V2's host plan world (``tests/test_mobile_v2_plan.py``), its vault at V3's successor tag."""

    pytest.importorskip("starlette")
    from starlette.testclient import TestClient

    import learnloop.clock as clock_module
    from learnloop.db.repositories import Repository
    from learnloop_mobile.host import create_app

    from tests.helpers import create_daily_plan_vault, set_algorithm_version
    from tests.mobile_host_helpers import HOSTNAME, CountingGrader, Phone, config_for, install_grader, pair
    from tests.test_mobile_v2_plan import DAY, ITEMS, _held_prompt

    monkeypatch.setattr(clock_module.SystemClock, "now", lambda _self: DAY)
    paths = create_daily_plan_vault(tmp_path / "vault", learning_objects=ITEMS)
    set_algorithm_version(paths, TAG)
    _held_prompt(paths.root)
    repository = Repository(paths.sqlite_path)
    install_grader(monkeypatch, CountingGrader())
    device = pair(repository)
    app = create_app(config_for(paths.root))
    with TestClient(app, base_url=f"https://{HOSTNAME}") as client:
        yield Phone(client, device), app.state.host, repository, paths


# -- F1: a non-owner phone can't burn the desktop's probe ------------------------------------------------------------


@pytest.mark.parametrize("door", ["get_practice_item", "get_probe_contract", "open_queue_item"])
def test_f1_a_phone_that_doesnt_own_the_session_never_burns_the_desktops_ready_probe(world, door):
    _attempt_id, row, repository = _ready(world, PHONE)
    item_id = row["practice_item_id"]
    # The learner takes the session to the desktop before the phone's request arrives.
    _adopt(world, None)
    params = {"practiceItemId": item_id} if door == "open_queue_item" else {
        "practiceItemId": item_id, "sessionId": world.session}
    _refused(world.ctx, door, params, PHONE, "session_moved")
    # Nothing was claimed: the probe is still unserved, and the desktop opens it as its own.
    assert identity.served_surface(repository, item_id) is None
    assert item_id not in identity.closed_probe_ids(repository)
    _call(world.ctx, "get_practice_item", {"practiceItemId": item_id, "sessionId": world.session})
    assert identity.served_surface(repository, item_id) == SERVING_SURFACE
    contract = _call(world.ctx, "get_probe_contract", {"practiceItemId": item_id, "sessionId": world.session})
    assert contract["active"] is True


def test_f1_the_owning_phone_still_burns_it_as_its_own(world):
    _attempt_id, row, repository = _ready(world, PHONE)
    item_id = row["practice_item_id"]
    _call(world.ctx, "get_practice_item", {"practiceItemId": item_id, "sessionId": world.session}, PHONE)
    assert identity.served_surface(repository, item_id) == PHONE_SURFACE


def _unserved_then_the_desktops(world, repository, item_id):
    """Nothing was claimed, and the desktop's next session opens the probe as its own."""

    assert identity.served_surface(repository, item_id) is None
    assert item_id not in identity.closed_probe_ids(repository)
    desktop_session = _call(world.ctx, "start_session", {"availableMinutes": 30})["sessionId"]
    _call(world.ctx, "get_practice_item", {"practiceItemId": item_id, "sessionId": desktop_session})
    assert identity.served_surface(repository, item_id) == SERVING_SURFACE


@pytest.mark.parametrize("door", ["get_practice_item", "get_probe_contract"])
def test_f1_reopened_a_stale_phone_serve_naming_a_session_the_desktop_ended_burns_nothing(world, door):
    """Codex re-review of V3, F1: the desktop adopts the phone's session and ends it, so no session is open; a stale
    phone serve naming the ended session is refused (a named serving session must still be open), not let through as
    a sessionless phone write would be."""

    _attempt_id, row, repository = _ready(world, PHONE)
    item_id = row["practice_item_id"]
    _adopt(world, None)
    _call(world.ctx, "end_session", {"sessionId": world.session})
    assert repository.most_recent_open_session() is None
    _refused(world.ctx, door, {"practiceItemId": item_id, "sessionId": world.session}, PHONE, "session_moved")
    _unserved_then_the_desktops(world, repository, item_id)


def test_f1_reopened_a_session_the_phone_ended_itself_is_refused_too(world):
    _attempt_id, row, repository = _ready(world, PHONE)
    item_id = row["practice_item_id"]
    _call(world.ctx, "end_session", {"sessionId": world.session}, PHONE)
    _refused(world.ctx, "get_practice_item", {"practiceItemId": item_id, "sessionId": world.session}, PHONE,
             "validation_error")
    _unserved_then_the_desktops(world, repository, item_id)


def _between_check_and_claim(monkeypatch, move):
    """Runs ``move`` once, after the door built its ownership check and before the claim's transaction runs it."""

    from learnloop_sidecar import serving

    real = serving._claim_refusal
    pending = [move]

    def claim(*args, **kwargs):
        while pending:
            pending.pop()()
        return real(*args, **kwargs)

    monkeypatch.setattr(serving, "_claim_refusal", claim)


def test_f1_reopened_a_handoff_and_back_between_the_check_and_the_claim_refuses_the_named_burn(world, monkeypatch):
    """The generation the door pinned is revalidated in the claim's transaction: the session went to the desktop and
    came back to the phone in between, so the phone's request was accepted against an owner that no longer stands."""

    _attempt_id, row, repository = _ready(world, PHONE)
    item_id = row["practice_item_id"]

    def there_and_back():
        _adopt(world, None)
        _adopt(world, PHONE)

    _between_check_and_claim(monkeypatch, there_and_back)
    _refused(world.ctx, "get_practice_item", {"practiceItemId": item_id, "sessionId": world.session}, PHONE,
             "session_moved")
    assert identity.served_surface(repository, item_id) is None
    assert item_id not in identity.closed_probe_ids(repository)


def test_f1_reopened_an_end_between_the_check_and_the_claim_refuses_the_named_burn(world, monkeypatch):
    _attempt_id, row, repository = _ready(world, PHONE)
    item_id = row["practice_item_id"]

    def adopt_and_end():
        _adopt(world, None)
        _call(world.ctx, "end_session", {"sessionId": world.session})

    _between_check_and_claim(monkeypatch, adopt_and_end)
    _refused(world.ctx, "get_practice_item", {"practiceItemId": item_id, "sessionId": world.session}, PHONE,
             "session_moved")
    _unserved_then_the_desktops(world, repository, item_id)


def test_f1_reopened_a_sessionless_phone_door_keeps_the_session_it_started_against(world, monkeypatch):
    """The queue's sessionless door pins the open session at its start: a handoff and back before the claim refuses it,
    where a fresh lookup at the claim would have found the phone's own session and burned."""

    _attempt_id, row, repository = _ready(world, PHONE)
    item_id = row["practice_item_id"]

    def there_and_back():
        _adopt(world, None)
        _adopt(world, PHONE)

    _between_check_and_claim(monkeypatch, there_and_back)
    _refused(world.ctx, "open_queue_item", {"practiceItemId": item_id}, PHONE, "session_moved")
    assert identity.served_surface(repository, item_id) is None


# -- F2: the desktop's Next and a phone answer still being graded ----------------------------------------------------


def _phone_plan_probe(world, monkeypatch):
    """A miss at the phone's plan step, its question generated (the router's arm pinned to asking now, as FG1's Next
    matrix pins it), and the plan's next step serving it on the phone."""

    from dataclasses import replace

    from learnloop.diagnosis.split.jobs import drain
    from learnloop.followup_run import router

    from tests.test_followup_rival_factor import _generate

    real = router.decide
    monkeypatch.setattr(router, "decide", lambda *a, **k: replace(real(*a, **k), chosen_ref=router.ASK_NOW,
                                                                   reason=router.ASK_NOW))
    _call(world.ctx, "get_daily_plan", {"sessionId": world.session}, PHONE)
    step = _call(world.ctx, "next_plan_item", {"sessionId": world.session, "serve": True}, PHONE)["step"]
    assert step["kind"] == "item", step
    _call(world.ctx, "get_practice_item", {"practiceItemId": step["practiceItemId"], "sessionId": world.session}, PHONE)
    missed = _call(world.ctx, "submit_attempt", {
        "sessionId": world.session, "practiceItemId": step["practiceItemId"], "answerMd": "A = U Sigma V wrong",
        "attemptType": "independent_attempt", "latencySeconds": 60,
        "planPresentationId": step.get("presentationId"),
    }, PHONE)
    vault, repository = world.ctx.require_vault()
    drain(vault, repository, client_factory=lambda: world.client, embedding_factory=lambda: None)
    _generate(world)
    world.ctx.reload(maintenance=False)
    _vault, repository = world.ctx.require_vault()
    row = wf.attempt_workflow(repository, missed["attemptId"])
    assert row["state"] == wf.READY and row["practice_item_id"], row
    probe = row["practice_item_id"]
    action = _call(world.ctx, "followup_next", {"attemptId": missed["attemptId"]}, PHONE)
    if action["action"] != "open":
        step = _call(world.ctx, "next_plan_item", {"sessionId": world.session, "serve": True}, PHONE)["step"]
        assert step["practiceItemId"] == probe, (action, step)
    _call(world.ctx, "get_practice_item", {"practiceItemId": probe, "sessionId": world.session}, PHONE)
    contract = _call(world.ctx, "get_probe_contract", {"practiceItemId": probe, "sessionId": world.session}, PHONE)
    assert contract["active"] is True and contract.get("phoneAnswers") is True
    assert identity.served_surface(repository, probe) == PHONE_SURFACE
    return missed["attemptId"], row, probe, contract["presentationId"], repository


def _plan_item(world, repository, probe):
    from learnloop.daily_plan.engine import PlanEnv, latest_today

    vault, _ = world.ctx.require_vault()
    record = latest_today(PlanEnv(vault=vault, repository=repository))
    return next((item for item in record.items() if item.practice_item_id == probe), None)


def test_f2_the_desktops_next_keeps_a_phone_probe_whose_answer_is_being_graded(tmp_path, monkeypatch):
    world = _world(tmp_path, monkeypatch)
    attempt_id, row, probe, presentation_id, repository = _phone_plan_probe(world, monkeypatch)
    planned = _plan_item(world, repository, probe)
    assert planned is not None and planned.served_at is not None, "the plan served the probe on the phone"
    # The phone's answer: the host accepted the job (its acceptance checked the owner) and the grader is still running.
    params = {"sessionId": world.session, "practiceItemId": probe, "answerMd": "An answer.",
              "attemptType": "diagnostic_probe", "latencySeconds": 40, "probePresentationId": presentation_id,
              "submissionId": "sub_phone_probe"}
    job, _enqueue = capture.accept_job(repository, device_id=PHONE.device_id, request_id="sub_phone_probe",
                                       method="submit_attempt", params=params, params_sha256="h", boot_id="boot")
    capture.start_job(repository, job["id"])
    # The learner takes the session to the desktop and presses Next before the grade comes back.
    _adopt(world, None)
    _call(world.ctx, "next_plan_item", {"sessionId": world.session, "serve": True})
    # The answer's presentation is still open and the miss's feedback is still held: nothing was abandoned.
    assert repository.active_probe_presentation_for_item(probe) is not None
    held = wf.get(repository, row["id"])
    assert held["state"] == wf.READY and is_holding(held)
    assert probe not in identity.retired_probe_ids(repository)
    # The job finishes on the host's job worker (its origin carries the accepted session): the probe's observation.
    accepted = RequestOrigin(device_id=PHONE.device_id, accepted_session_id=world.session, phone_probes=True)
    answer = _call(world.ctx, "submit_attempt", params, accepted)
    capture.finish_job(repository, job["id"], result=answer)
    attempt = repository.fetch_practice_attempt(answer["attemptId"])
    assert attempt["probe_presentation_id"] == presentation_id and attempt["attempt_type"] == "diagnostic_probe"
    settled = wf.get(repository, row["id"])
    assert settled["state"] == wf.SETTLED and settled["release_reason"] == wf.RELEASE_PROBE_ANSWERED
    assert _call(world.ctx, "get_feedback", {"attemptId": attempt_id, "recordOpen": False})["followup"]["held"] is False
    # The desktop's next Next moves on past the answered probe.
    step = _call(world.ctx, "next_plan_item", {"sessionId": world.session, "serve": True})["step"]
    assert step is None or step.get("practiceItemId") != probe


def test_f2_with_no_answer_on_its_way_the_desktops_next_still_moves_past_the_phones_probe(tmp_path, monkeypatch):
    world = _world(tmp_path, monkeypatch)
    _attempt_id, row, probe, _presentation_id, repository = _phone_plan_probe(world, monkeypatch)
    _adopt(world, None)
    step = _call(world.ctx, "next_plan_item", {"sessionId": world.session, "serve": True})["step"]
    assert step is None or step.get("practiceItemId") != probe
    assert probe in identity.retired_probe_ids(repository)
    assert wf.get(repository, row["id"])["state"] == wf.SKIPPED


# -- F3: a cached V2 app against a V3 host ---------------------------------------------------------------------------


def _make_probe(repository, item_id: str) -> None:
    """``item_id`` becomes an admitted, unserved generated probe with no workflow: the door's claim path."""

    identity.register(repository, practice_item_id=item_id, revision="rev", source="workflow")
    repository.set_practice_item_active(item_id, active=True)


def _phone_step_probe(plan_world):
    """The phone's first plan step (served to the current app), made a generated probe before its door opens."""

    from tests.test_mobile_v2_plan import _next

    phone, _host, repository, _paths = plan_world
    session_id = phone.start()["sessionId"]
    first = _next(phone, session_id, "v3_f3_peek", serve=True)["step"]
    assert first["kind"] == "item"
    _make_probe(repository, first["practiceItemId"])
    return phone, repository, session_id, first["practiceItemId"]


def test_f3_a_v2_app_gets_v2s_doors_from_a_v3_host_and_burns_nothing(plan_world):
    phone, repository, session_id, item_id = _phone_step_probe(plan_world)
    v2 = phone.without_capabilities()
    for name, params in (("get_practice_item", {"practiceItemId": item_id, "sessionId": session_id}),
                         ("get_probe_contract", {"practiceItemId": item_id, "sessionId": session_id}),
                         ("open_queue_item", {"practiceItemId": item_id})):
        _status, error = v2.error(name, params)
        assert error["code"] == identity.GENERATED_PROBE_RESERVED, (name, error)
    assert identity.served_surface(repository, item_id) is None
    # V2's own refusals: Next on a miss and a probe answer are the V3 app's.
    status, error = v2.error("followup_next", {"attemptId": "a"})
    assert (status, error["code"]) == (409, "phone_probes_off")
    status, error = v2.error("submit_attempt", {
        "sessionId": session_id, "practiceItemId": item_id, "answerMd": "x", "attemptType": "diagnostic_probe",
        "submissionId": "s_v2", "probePresentationId": "p"}, request_id="s_v2")
    assert (status, error["code"]) == (422, "validation_error")


def test_f3_a_v2_apps_plan_step_holds_a_generated_probe_for_the_desktop(plan_world):
    from tests.test_mobile_v2_plan import _next

    phone, _host, repository, _paths = plan_world
    session_id = phone.start()["sessionId"]
    v2 = phone.without_capabilities()
    first = _next(v2, session_id, "v3_f3_first", serve=False)["step"]
    assert first["kind"] == "item"
    _make_probe(repository, first["practiceItemId"])
    step = _next(v2, session_id, "v3_f3_serve", serve=True)["step"]
    assert step is None or step.get("practiceItemId") != first["practiceItemId"]
    assert identity.served_surface(repository, first["practiceItemId"]) is None


def test_f3_the_v3_app_says_it_answers_probes_and_gets_v3s_door(plan_world):
    phone, repository, session_id, item_id = _phone_step_probe(plan_world)
    phone.rpc("get_practice_item", {"practiceItemId": item_id, "sessionId": session_id})
    assert identity.served_surface(repository, item_id) == PHONE_SURFACE


def test_f3_the_app_and_the_host_name_the_same_capability_header():
    from pathlib import Path

    from learnloop_mobile.host import CLIENT_CAPABILITIES_HEADER, PHONE_PROBES_CAPABILITY

    source = (Path(__file__).resolve().parents[1] / "apps/learnloop-mobile/src/api/http.ts").read_text(encoding="utf-8")
    assert f'CLIENT_CAPABILITIES_HEADER = "{CLIENT_CAPABILITIES_HEADER}"'.lower() in source.lower()
    assert f'CLIENT_CAPABILITIES = "{PHONE_PROBES_CAPABILITY}"' in source

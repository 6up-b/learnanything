"""Mobile M2a: the ``/rpc`` adapter and the secondary workers (spec §3.1, §4.5, §6.2).

G2's new endpoints, G3 (the allowlist by enumerating the registry, each constraint),
G11 (provenance through the real host) and the part of G12 the host owns.
"""

from __future__ import annotations

import json
import threading

import pytest

pytest.importorskip("starlette")
from starlette.testclient import TestClient

import learnloop_sidecar.handlers  # noqa: F401 -- populate METHOD_REGISTRY
from learnloop_mobile.adapter import canonical_hash, status_for, translate
from learnloop_mobile.allowlist import ALLOWLIST, ParamRejected, check_parameters
from learnloop_mobile.host import create_app
from learnloop_sidecar.registry import METHOD_REGISTRY

from tests.mobile_host_helpers import (
    HOSTNAME, ITEM, SECOND_ITEM, CountingGrader, Phone, bearer, config_for, identity, install_grader, pair, rows,
    seeded_vault,
)

M2_ROW = {
    "start_session", "adopt_session", "get_session", "end_session", "update_session_checkpoint",
    "clear_session_checkpoint", "get_today_queue", "open_queue_item", "get_practice_item", "get_probe_contract",
    "save_practice_draft", "submit_attempt", "submit_dont_know", "skip_practice_item",
    "acknowledge_practice_submission", "get_feedback", "get_attempt", "get_grading_clarification",
    "answer_grading_clarification", "diagnosis_status", "submit_eliciting_response",
}


@pytest.fixture
def world(tmp_path, monkeypatch):
    paths, repository = seeded_vault(tmp_path / "vault")
    grader = CountingGrader()
    install_grader(monkeypatch, grader)
    device = pair(repository)
    app = create_app(config_for(paths.root))
    with TestClient(app, base_url=f"https://{HOSTNAME}") as client:
        yield Phone(client, device), app.state.host, repository, paths, grader


# -- G3: the allowlist ---------------------------------------------------------


def test_the_allowlist_is_the_m2_row_and_every_name_is_a_registered_method():
    assert set(ALLOWLIST) == M2_ROW
    assert M2_ROW <= set(METHOD_REGISTRY)
    assert {entry.name for entry in ALLOWLIST.values() if entry.kind == "long"} == {
        "submit_attempt", "submit_dont_know", "answer_grading_clarification",
    }
    assert all(entry.milestone == "M2" for entry in ALLOWLIST.values())
    with pytest.raises(TypeError):
        ALLOWLIST["run_cli_command"] = object()  # type: ignore[index]


def test_the_retry_policy_is_section_6_2s():
    never = {"start_session", "adopt_session", "end_session", "skip_practice_item", "submit_eliciting_response"}
    assert {name for name, entry in ALLOWLIST.items() if not entry.retry_safe} == never


def test_every_other_registered_method_answers_403(world):
    phone, *_ = world
    denied = sorted(set(METHOD_REGISTRY) - M2_ROW)
    assert len(denied) > 300
    assert {"get_queue_revision", "recover_practice_submission", "run_cli_command", "get_daily_plan",
            "stop_probe_diagnosing", "get_next_probe_item", "start_overconfidence_probe"} <= set(denied)
    for name in denied:
        status, error = phone.error(name)
        assert (status, error["code"]) == (403, "method_not_allowed"), name


@pytest.mark.parametrize("body", [
    [], [{"method": "get_session"}], {"method": 1}, {"method": ""}, {"method": "get_session", "params": []},
    {"method": "get_session", "jsonrpc": "2.0"}, {"method": "get_session", "id": 1},
    {"method": "get_session", "request_id": ""},
])
def test_a_malformed_envelope_is_400(world, body):
    phone, *_ = world
    response = phone.client.post("/rpc", json=body, headers=phone.headers)
    assert response.status_code == 400


# -- G3: each constraint, through the adapter ---------------------------------


@pytest.mark.parametrize("method,params,field", [
    ("start_session", {"notes_md_path": "/etc/passwd"}, "notes_md_path"),
    ("start_session", {"notesMdPath": "notes.md"}, "notes_md_path"),
    ("get_practice_item", {"practiceItemId": ITEM, "proposalId": "p"}, "proposal_id"),
    ("get_practice_item", {"practiceItemId": ITEM, "sourceExerciseImportId": "i"}, "source_exercise_import_id"),
    ("submit_attempt", {"selfGrade": {"criterionPoints": {}, "confidence": 3}, "submissionId": "s"}, "self_grade"),
    ("submit_attempt", {"self_grade": {"criterion_points": {}, "confidence": 3}, "submission_id": "s"}, "self_grade"),
    ("submit_attempt", {"submissionId": ""}, "submission_id"),
    ("submit_attempt", {"submissionId": "   "}, "submission_id"),
    ("submit_attempt", {}, "submission_id"),
    ("submit_dont_know", {}, "submission_id"),
    ("submit_attempt", {"submissionId": "s", "probePresentationId": "p"}, "probe_presentation_id"),
    ("submit_dont_know", {"submissionId": "s", "probePresentationId": "p"}, "probe_presentation_id"),
    ("submit_dont_know", {"submissionId": "s", "selfGrade": {"criterionPoints": {}, "confidence": 3}}, "self_grade"),
])
def test_each_constraint_is_a_422_before_dispatch(world, method, params, field):
    phone, *_ = world
    status, error = phone.error(method, params, request_id="r1")
    assert (status, error["code"]) == (422, "validation_error")
    assert error["details"] == {"field": field}


@pytest.mark.parametrize("name", ["vault_path", "filePath", "file", "directory", "dir", "root"])
def test_a_parameter_naming_a_path_is_rejected_for_every_method(name):
    for method in ALLOWLIST.values():
        with pytest.raises(ParamRejected):
            check_parameters(method, {name: "x"})


def test_no_allowlisted_model_declares_a_path_the_rule_misses():
    for name in ALLOWLIST:
        fields = METHOD_REGISTRY[name].params_model.model_fields
        for field in fields:
            words = set(field.split("_"))
            if words & {"path", "file", "dir", "directory", "folder", "vault", "root"}:
                with pytest.raises(ParamRejected):
                    check_parameters(ALLOWLIST[name], {field: "x"})


@pytest.mark.parametrize("params", [
    {"entrySurface": "desktop_practice"}, {"entry_surface": "desktop_practice"}, {"deviceClass": "desktop"},
    {"deviceId": "other"}, {"answerTranscriptionId": "t"},
])
def test_no_parameter_can_set_the_origin(world, params):
    phone, *_ = world
    session = phone.start()
    status, error = phone.error(
        "submit_attempt",
        {"sessionId": session["sessionId"], "practiceItemId": ITEM, "answerMd": "x", "attemptType": "independent_attempt",
         "submissionId": "s1", **params},
        request_id="s1",
    )
    assert (status, error["code"]) == (422, "validation_error")


def test_validation_errors_never_echo_the_learners_text(world):
    phone, *_ = world
    status, error = phone.error("save_practice_draft", {"answerMd": "my private answer"})
    assert status == 422
    assert "my private answer" not in json.dumps(error)


# -- §6.2: translation ---------------------------------------------------------


@pytest.mark.parametrize("code,status,retryable", [
    ("validation_error", 422, False), ("invalid_request", 422, False), ("not_found", 404, False),
    ("method_not_allowed", 403, False), ("session_open_elsewhere", 409, False), ("session_moved", 409, False),
    ("current_item_desktop_only", 409, False), ("submission_conflict", 409, False), ("capture_conflict", 409, False),
    ("desktop_only", 409, False), ("database_busy", 503, True), ("completion_busy", 503, True),
    ("host_busy", 503, True), ("grading_fallback_required", 409, True), ("internal", 500, False),
    ("item_retired", 409, False),
])
def test_the_status_table(code, status, retryable):
    assert status_for(code) == status
    got, body = translate({"error": {"code": -32001, "message": "m", "data": {"code": code, "details": {"a": 1}}}})
    assert got == status
    assert body == {"ok": False, "error": {"code": code, "message": "m", "retryable": retryable, "details": {"a": 1}}}


def test_a_result_is_ok_and_a_hash_ignores_key_order():
    assert translate({"result": {"a": 1}}) == (200, {"ok": True, "result": {"a": 1}})
    assert canonical_hash({"a": 1, "b": 2}) == canonical_hash({"b": 2, "a": 1})
    assert canonical_hash({"a": 1}) != canonical_hash({"a": 2})


def test_an_unknown_id_is_404_and_a_handler_crash_is_500_with_no_detail(world, monkeypatch):
    phone, *_ = world
    assert phone.error("get_session", {"sessionId": "nope"})[0] == 404
    spec = METHOD_REGISTRY["get_attempt"]

    def boom(_ctx, _params):
        raise RuntimeError("secret detail")

    monkeypatch.setitem(METHOD_REGISTRY, "get_attempt", type(spec)(spec.name, spec.params_model, boom))
    status, error = phone.error("get_attempt", {"attemptId": "a"})
    assert (status, error["code"]) == (500, "internal")
    assert "secret detail" not in json.dumps(error)


def test_a_locked_database_is_503_retryable(world, monkeypatch):
    phone, *_ = world
    import sqlite3

    spec = METHOD_REGISTRY["get_session"]

    def locked(_ctx, _params):
        raise sqlite3.OperationalError("database is locked")

    monkeypatch.setitem(METHOD_REGISTRY, "get_session", type(spec)(spec.name, spec.params_model, locked))
    status, error = phone.error("get_session", {"sessionId": "s"})
    assert (status, error["code"], error["retryable"]) == (503, "database_busy", True)


def test_a_full_rpc_queue_answers_host_busy_and_recovers(world, monkeypatch):
    phone, host, *_ = world
    import learnloop_mobile.runtime as runtime

    phone.start()  # the workers are up
    release = threading.Event()
    entered = threading.Event()

    def hold(_worker):
        entered.set()
        release.wait(30)

    host.runtime.rpc_worker.submit(hold)
    assert entered.wait(10)
    for _ in range(runtime.RPC_QUEUE_LIMIT):
        host.runtime.rpc_worker.submit(lambda _worker: None)
    try:
        status, error = phone.error("get_session", {"sessionId": "s"})
        assert (status, error["code"], error["retryable"]) == (503, "host_busy", True)
    finally:
        release.set()
    assert phone.error("get_session", {"sessionId": "s"})[0] == 404


# -- §6.1: authentication on the new endpoints ----------------------------------


@pytest.mark.parametrize("path", ["/api/v1/queue-revision", "/api/v1/jobs/j1", "/api/v1/submissions/s1"])
def test_status_endpoints_need_an_app_token(world, path):
    phone, _host, repository, *_ = world
    client = phone.client
    assert client.get(path).status_code == 403
    assert client.get(path, headers=identity()).status_code == 401
    narrow = pair(repository, scope="capture")
    assert client.get(path, headers=bearer(narrow)).status_code == 403
    assert client.get(path, headers=phone.headers).status_code in (200, 404)


def test_rpc_needs_an_app_token_before_any_body_is_read(world):
    phone, _host, repository, *_ = world
    client = phone.client
    body = {"method": "get_session", "params": {"sessionId": "s"}}
    assert client.post("/rpc", json=body).status_code == 403
    assert client.post("/rpc", json=body, headers=identity()).status_code == 401
    assert client.post("/rpc", json=body, headers=bearer(pair(repository, scope="capture"))).status_code == 403


def test_a_foreign_origin_is_refused_on_rpc(world):
    phone, *_ = world
    response = phone.client.post(
        "/rpc", json={"method": "get_session", "params": {"sessionId": "s"}},
        headers={**phone.headers, "Origin": "https://evil.invalid"},
    )
    assert response.status_code == 403
    assert not any(key.startswith("access-control") for key in response.headers)


# -- /api/v1/queue-revision ------------------------------------------------------


def test_the_host_bumps_once_at_start_so_a_lost_debt_still_moves_the_token(tmp_path):
    """Open item 1: a bump owed by a host that died is lost with it; a start moves the token."""

    paths, repository = seeded_vault(tmp_path / "vault")
    before = repository.queue_revision()["revision"]
    app = create_app(config_for(paths.root))
    assert repository.queue_revision()["revision"] == before  # nothing until it serves
    with TestClient(app, base_url=f"https://{HOSTNAME}"):
        assert repository.queue_revision()["revision"] == before + 1
    assert repository.queue_revision()["revision"] == before + 1


def test_the_token_read_is_read_only_and_answers_only_the_revision(world):
    phone, _host, repository, *_ = world
    before = repository.queue_revision()["revision"]
    response = phone.get("/api/v1/queue-revision")
    assert response.status_code == 200
    assert response.json() == {"revision": before}
    assert response.headers["cache-control"] == "no-store"
    assert repository.queue_revision()["revision"] == before
    phone.start()
    assert phone.get("/api/v1/queue-revision").json() == {"revision": before + 1}


def test_a_status_poll_is_not_logged_and_a_request_log_names_the_allowlisted_method(world):
    phone, _host, repository, *_ = world
    session = phone.start()
    phone.get("/api/v1/queue-revision")
    phone.post("not_a_method")
    phone.rpc("get_session", {"sessionId": session["sessionId"]})
    logged = [row["endpoint"] for row in rows(repository, "SELECT endpoint FROM mobile_request_log ORDER BY rowid")]
    assert logged == ["rpc:start_session", "/rpc", "rpc:get_session"]


# -- serving through the host: §6.4, §6.8, G9, G11 --------------------------------


def test_the_phone_is_served_from_the_real_handlers_as_a_secondary(world):
    phone, host, repository, _paths, _grader = world
    session = phone.start()
    assert session["ownerDeviceId"] == phone.device["device_id"]
    assert session["ownerLabel"] == "Phone"
    items = phone.queue_items(session["sessionId"])
    assert {item["practiceItemId"] for item in items} == {ITEM, SECOND_ITEM}
    item = phone.rpc("get_practice_item", {"practiceItemId": items[0]["practiceItemId"], "sessionId": session["sessionId"]})
    assert item["prompt"]
    assert host.runtime.rpc_worker.context.secondary is True
    assert host.runtime.job_worker.context.secondary is True
    assert host.runtime.rpc_worker.context is not host.runtime.job_worker.context
    offers = rows(repository, "SELECT entry_surface FROM scheduler_offer_receipts")
    assert offers and {row["entry_surface"] for row in offers} == {"phone_queue"}


def test_a_phone_attempt_is_phone_practice_and_its_offer_phone_queue(world):
    phone, _host, repository, _paths, _grader = world
    session = phone.start()
    head = phone.queue_items(session["sessionId"])[0]
    response = phone.submit(session["sessionId"], "sub1", item=head["practiceItemId"],
                            schedulerCandidateId=head.get("schedulerCandidateId"))
    assert response.status_code == 200, response.text
    attempt = rows(repository, "SELECT entry_surface FROM practice_attempts WHERE submission_id='sub1'")
    assert attempt == [{"entry_surface": "phone_practice"}]
    intent = rows(repository, "SELECT entry_surface FROM submission_intents WHERE submission_id='sub1'")
    assert intent == [{"entry_surface": "phone_practice"}]


def _reload_next_request(host) -> None:
    """The fingerprint window is 2 s; open it so a test does not sleep."""

    for worker in (host.runtime.rpc_worker, host.runtime.job_worker):
        if worker.context is not None:
            worker.context._fingerprint_checked_at = float("-inf")


def _add_item(paths, repository, item_id: str, prompt: str) -> None:
    from learnloop.vault.writer import upsert_practice_item

    upsert_practice_item(paths.root, {
        "id": item_id, "learning_object_id": "lo_svd_definition", "subjects": None, "practice_mode": "short_answer",
        "attempt_types_allowed": ["independent_attempt"], "evidence_facets": ["recall"],
        "evidence_weights": {"recall": 1.0}, "prompt": prompt, "expected_answer": "An answer.",
        "grading_rubric": {"max_points": 4, "fatal_errors": [],
                           "criteria": [{"id": "correctness", "points": 4, "description": "Correct."}]},
        "created_at": "2026-05-16T12:00:00Z", "updated_at": "2026-05-16T12:00:00Z",
    })
    repository.upsert_practice_item_state(
        item_id, difficulty=5.0, stability=2.0, due_at="2026-05-18T12:00:00Z", last_attempt_at="2026-05-16T12:00:00Z",
        active=True,
    )


def test_a_desktop_only_item_is_refused_at_each_door_and_counted(world):
    phone, host, repository, paths, _grader = world
    held = "pi_held_for_desktop"
    session = phone.start()
    _add_item(paths, repository, held, "See ![the figure](figures/a.png).")
    _reload_next_request(host)
    queue = phone.rpc("get_today_queue", {"sessionId": session["sessionId"]})
    listed = [item["practiceItemId"] for section in queue["sections"] for item in section["items"]]
    assert held not in listed and listed
    assert queue["deviceDeferredCount"] == 1
    for method, params in (
        ("open_queue_item", {"practiceItemId": held}),
        ("get_practice_item", {"practiceItemId": held, "sessionId": session["sessionId"]}),
        ("get_probe_contract", {"practiceItemId": held, "sessionId": session["sessionId"]}),
    ):
        status, error = phone.error(method, params)
        assert (status, error["code"]) == (409, "desktop_only"), method
        assert error["details"]["reason"] == "embeds_image"
    skipped = phone.rpc("skip_practice_item", {"sessionId": session["sessionId"], "practiceItemId": listed[0]})
    assert skipped["deviceDeferredCount"] == 1


def test_a_yaml_change_reaches_the_next_request_after_the_window(world):
    """G12: at most 2 s; the window is opened by hand so the test does not sleep."""

    phone, host, repository, paths, _grader = world
    session = phone.start()
    assert phone.error("get_practice_item", {"practiceItemId": "pi_new", "sessionId": session["sessionId"]})[0] == 404
    _add_item(paths, repository, "pi_new", "Written on the desktop just now.")
    _reload_next_request(host)
    after = phone.rpc("get_practice_item", {"practiceItemId": "pi_new", "sessionId": session["sessionId"]})
    assert after["prompt"] == "Written on the desktop just now."


def test_the_router_inputs_name_the_phones_device_policy(world):
    phone, _host, repository, *_ = world
    session = phone.start()
    phone.queue_items(session["sessionId"])
    decisions = rows(repository, "SELECT detail_json, surface FROM router_decisions WHERE decision_kind='today_offer'")
    assert decisions
    for row in decisions:
        assert json.loads(row["detail_json"])["inputs"]["device_policy"] == "device_eligibility_v1"


# -- open item 3: a phone offer logs what the phone showed ---------------------------


@pytest.fixture
def plan_serves(monkeypatch):
    """The finite plan serves Today (the basic vault is below its version)."""

    import learnloop_sidecar.handlers.queue as queue

    monkeypatch.setattr(queue, "plan_active", lambda _vault: True)


def test_under_a_serving_plan_the_phones_head_is_served_and_its_surface_is_phone_queue(world, plan_serves):
    phone, _host, repository, _paths, _grader = world
    session = phone.start()
    head = phone.queue_items(session["sessionId"])[0]
    offer = rows(repository, "SELECT surface, chosen_scheduler_candidate_id, propensity_kind FROM router_decisions "
                             "WHERE decision_kind='today_offer' ORDER BY rowid DESC LIMIT 1")[0]
    assert offer["surface"] == "phone_queue"
    assert offer["chosen_scheduler_candidate_id"] == head["schedulerCandidateId"]
    assert offer["propensity_kind"] != "not_served"


def test_the_kill_switch_takes_the_filter_off_and_the_log_still_says_what_the_phone_showed(world, plan_serves):
    """Codex review F8, rejected. ``head_served`` orders nothing: it is the decision log's account of
    a list the phone shows head first, and that stays true with the filter off. Logging the phone's
    head as a list it never showed would be the wrong row in the data this log exists for."""

    from tests.source_service_fakes import set_config

    phone, _host, repository, paths, _grader = world
    set_config(paths, "practice", device_eligibility_enabled=False)
    session = phone.start()
    head = phone.queue_items(session["sessionId"])[0]
    offer = rows(repository, "SELECT surface, chosen_scheduler_candidate_id, detail_json FROM router_decisions "
                             "WHERE decision_kind='today_offer' ORDER BY rowid DESC LIMIT 1")[0]
    assert json.loads(offer["detail_json"])["inputs"]["device_policy"] == "off"
    assert (offer["surface"], offer["chosen_scheduler_candidate_id"]) == ("phone_queue", head["schedulerCandidateId"])


def test_taking_the_head_is_no_pick(world, plan_serves):
    phone, *_rest = world
    repository = world[2]
    session = phone.start()
    head = phone.queue_items(session["sessionId"])[0]
    assert phone.submit(session["sessionId"], "sub_head", item=head["practiceItemId"],
                        schedulerCandidateId=head["schedulerCandidateId"]).status_code == 200
    assert rows(repository, "SELECT * FROM router_decisions WHERE decision_kind='learner_pick'") == []


def test_a_row_below_the_head_is_a_learner_pick_on_the_phones_surface(world, plan_serves):
    phone, *_rest = world
    repository = world[2]
    session = phone.start()
    _head, other = phone.queue_items(session["sessionId"])[:2]
    assert phone.submit(session["sessionId"], "sub_pick", item=other["practiceItemId"],
                        schedulerCandidateId=other["schedulerCandidateId"]).status_code == 200
    picks = rows(repository, "SELECT surface FROM router_decisions WHERE decision_kind='learner_pick'")
    assert picks == [{"surface": "phone_practice"}]


def test_the_desktops_offer_under_a_plan_is_still_full_list(tmp_path, plan_serves):
    """G9: the same change takes no branch for a None origin."""

    from learnloop_sidecar.context import SidecarContext

    paths, repository = seeded_vault(tmp_path / "vault")
    ctx = SidecarContext()
    ctx.load_secondary(paths.root)
    spec = METHOD_REGISTRY["start_session"]
    session = spec.handler(ctx, spec.params_model.model_validate({"availableMinutes": 25}))
    spec = METHOD_REGISTRY["get_today_queue"]
    reply = spec.handler(ctx, spec.params_model.model_validate({"sessionId": session["sessionId"]}))
    assert "deviceDeferredCount" not in reply
    offer = rows(repository, "SELECT surface, propensity_kind FROM router_decisions WHERE decision_kind='today_offer'")[0]
    assert offer == {"surface": "full_list", "propensity_kind": "not_served"}
    ctx.close()


# -- the app shell: §4.6, G2 -----------------------------------------------------


def test_the_shell_is_identity_gated_needs_no_bearer_and_holds_no_vault_data(world, tmp_path):
    phone, host, *_ = world
    client = phone.client
    host.app_dir = tmp_path / "never_built"
    assert client.get("/app/", headers=identity()).status_code == 404
    built = tmp_path / "built"
    (built / "assets").mkdir(parents=True)
    (built / "index.html").write_text("<!doctype html><title>LearnLoop</title>", encoding="utf-8")
    (built / "assets" / "a.js").write_text("console.log(1)", encoding="utf-8")
    secret = tmp_path / "outside.txt"
    secret.write_text("outside", encoding="utf-8")
    (built / "link.txt").symlink_to(secret)
    host.app_dir = built
    assert client.get("/app/").status_code == 403
    page = client.get("/app/", headers=identity())
    assert page.status_code == 200 and "LearnLoop" in page.text
    assert page.headers["content-security-policy"].startswith("default-src 'self'")
    assert page.headers["cache-control"] == "no-cache"
    assert client.get("/app/assets/a.js", headers=identity()).status_code == 200
    assert client.get("/app", headers=identity(), follow_redirects=False).status_code == 307
    assert client.get("/app/assets/", headers=identity()).status_code == 404  # no listing
    assert client.get("/app/link.txt", headers=identity()).status_code == 404  # no symlink out
    assert client.get("/app/%2e%2e/state.sqlite", headers=identity()).status_code == 404
    assert client.post("/app/", headers=identity()).status_code == 401  # the shell is GET only

"""Mobile M2a: accepted jobs and the status endpoints (spec §6.3, §6.1, G7).

The grader is a fake that can hold a grade open, so a "dropped connection" here is a
client that got its 202 and went away, and a "restart" is a second host on the same
vault, with the old run's rows left as a dead process leaves them.
"""

from __future__ import annotations

import json
import threading

import pytest

pytest.importorskip("starlette")
from starlette.testclient import TestClient

from learnloop import capture
from learnloop.ids import new_ulid
from learnloop_mobile import host as host_module
from learnloop_mobile.host import create_app

from tests.mobile_host_helpers import (
    HOSTNAME, ITEM, CountingGrader, Phone, config_for, install_grader, install_grading_outage, pair, poll_job, rows,
    seeded_vault,
)


@pytest.fixture
def world(tmp_path, monkeypatch):
    paths, repository = seeded_vault(tmp_path / "vault")
    grader = CountingGrader()
    install_grader(monkeypatch, grader)
    device = pair(repository)
    app = create_app(config_for(paths.root))
    with TestClient(app, base_url=f"https://{HOSTNAME}") as client:
        yield Phone(client, device), app.state.host, repository, paths, grader


def _attempts(repository, submission_id: str) -> list[dict]:
    return rows(repository, "SELECT id, entry_surface FROM practice_attempts WHERE submission_id=?", submission_id)


def test_a_fast_grade_is_a_plain_200_with_the_same_payload_as_the_receipt(world):
    phone, _host, repository, *_ = world
    session = phone.start()
    response = phone.submit(session["sessionId"], "sub1")
    assert response.status_code == 200, response.text
    result = response.json()["result"]
    assert result["attemptId"] and result["practiceItemId"] == ITEM
    receipt = repository.attempt_submission_receipt("sub1")
    assert receipt["result"] == result
    job = rows(repository, "SELECT state, device_id, method, host_boot_id, boot_attempts, started_at, finished_at FROM mobile_jobs WHERE request_id='sub1'")[0]
    assert job["state"] == "completed" and job["device_id"] == phone.device["device_id"]
    assert job["method"] == "submit_attempt" and job["boot_attempts"] == 0
    assert job["started_at"] and job["finished_at"]


def test_a_dropped_connection_yields_one_attempt_and_a_completed_job(world, monkeypatch):
    """G7: the 202 is the phone's last word; the job runs on and polling reads its end."""

    phone, _host, repository, _paths, grader = world
    monkeypatch.setattr(host_module, "JOB_WAIT_SECONDS", 0.05)
    grader.gate = threading.Event()
    session = phone.start()
    response = phone.submit(session["sessionId"], "sub1")
    assert response.status_code == 202
    accepted = response.json()["accepted"]
    assert accepted["request_id"] == "sub1" and accepted["state"] in ("accepted", "running")
    job_id = accepted["job_id"]
    assert grader.started.wait(30)
    assert phone.get(f"/api/v1/jobs/{job_id}").json()["state"] == "running"
    assert phone.get("/api/v1/submissions/sub1").json()["state"] == "running"
    grader.gate.set()
    done = poll_job(phone, job_id)
    assert done["state"] == "completed" and done["result"]["attemptId"]
    assert len(_attempts(repository, "sub1")) == 1
    assert grader.grades == 1
    assert phone.get("/api/v1/submissions/sub1").json()["result"] == done["result"]


def test_identical_retries_coalesce_with_one_provider_call(world, monkeypatch):
    """G7: a retry while it runs and a retry after it finished each find the same job."""

    phone, _host, repository, _paths, grader = world
    monkeypatch.setattr(host_module, "JOB_WAIT_SECONDS", 0.05)
    grader.gate = threading.Event()
    session = phone.start()
    first = phone.submit(session["sessionId"], "sub1").json()["accepted"]["job_id"]
    assert grader.started.wait(30)
    again = phone.submit(session["sessionId"], "sub1")
    assert again.status_code == 202 and again.json()["accepted"]["job_id"] == first
    grader.gate.set()
    poll_job(phone, first)
    last = phone.submit(session["sessionId"], "sub1")
    assert last.status_code == 200 and last.json()["result"]["attemptId"]
    assert grader.grades == 1
    assert len(rows(repository, "SELECT id FROM mobile_jobs WHERE request_id='sub1'")) == 1


def test_a_retry_spelled_differently_is_the_same_request(world):
    phone, *_ = world
    session = phone.start()
    first = phone.submit(session["sessionId"], "sub1")
    assert first.status_code == 200
    retry = phone.post("submit_attempt", {
        "session_id": session["sessionId"], "practice_item_id": ITEM, "answer_md": "an answer",
        "attempt_type": "independent_attempt", "submission_id": "sub1",
    }, request_id="sub1")
    assert retry.status_code == 200
    assert retry.json()["result"] == first.json()["result"]


def test_the_same_id_with_different_params_is_409(world):
    """G7: nothing is overwritten, and no second attempt."""

    phone, _host, repository, *_ = world
    session = phone.start()
    assert phone.submit(session["sessionId"], "sub1").status_code == 200
    response = phone.submit(session["sessionId"], "sub1", answerMd="another answer")
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "submission_conflict"
    assert len(_attempts(repository, "sub1")) == 1


@pytest.mark.parametrize("request_id", [None, "not-the-submission"])
def test_a_submit_needs_its_submission_id_as_request_id(world, request_id):
    phone, *_ = world
    session = phone.start()
    status, error = phone.error("submit_attempt", {
        "sessionId": session["sessionId"], "practiceItemId": ITEM, "answerMd": "x",
        "attemptType": "independent_attempt", "submissionId": "sub1",
    }, request_id=request_id)
    assert (status, error["code"]) == (422, "validation_error")


def test_invalid_params_are_refused_before_a_job_exists(world):
    phone, _host, repository, *_ = world
    status, error = phone.error("submit_attempt", {"submissionId": "sub1"}, request_id="sub1")
    assert (status, error["code"]) == (422, "validation_error")
    assert rows(repository, "SELECT id FROM mobile_jobs") == []


def test_grading_down_is_a_typed_failure_the_draft_survives_and_the_same_request_retries(world, monkeypatch):
    """§6.3: 'Phone without self-grade'. The checkpoint keeps the draft; 'retry later' is the same id."""

    phone, _host, repository, _paths, grader = world
    session = phone.start()
    phone.rpc("save_practice_draft", {
        "sessionId": session["sessionId"], "practiceItemId": ITEM, "answerMd": "an answer", "submissionId": "sub1",
    })
    install_grading_outage(monkeypatch)
    response = phone.submit(session["sessionId"], "sub1")
    assert response.status_code == 409
    error = response.json()["error"]
    assert error["code"] == "grading_fallback_required" and error["retryable"] is True
    assert _attempts(repository, "sub1") == []
    assert repository.fetch_session_checkpoint(session["sessionId"])["current_answer"] == "an answer"
    assert phone.get("/api/v1/submissions/sub1").json()["state"] == "failed"
    install_grader(monkeypatch, grader)
    retried = phone.submit(session["sessionId"], "sub1")
    assert retried.status_code == 200, retried.text
    assert len(_attempts(repository, "sub1")) == 1
    assert len(rows(repository, "SELECT id FROM mobile_jobs WHERE request_id='sub1'")) == 1


def test_a_refused_item_is_a_terminal_failure_and_a_retry_answers_the_same(world):
    phone, _host, repository, *_ = world
    session = phone.start()
    response = phone.submit(session["sessionId"], "sub1", item="pi_does_not_exist")
    assert response.status_code == 404
    again = phone.submit(session["sessionId"], "sub1", item="pi_does_not_exist")
    assert again.status_code == 404 and again.json() == response.json()
    assert rows(repository, "SELECT state FROM mobile_jobs WHERE request_id='sub1'") == [{"state": "failed"}]


def test_submit_dont_know_and_a_clarification_are_jobs_too(world):
    phone, _host, repository, *_ = world
    session = phone.start()
    response = phone.post("submit_dont_know", {
        "sessionId": session["sessionId"], "practiceItemId": ITEM, "submissionId": "sub1",
    }, request_id="sub1")
    assert response.status_code in (200, 409), response.text
    assert rows(repository, "SELECT method FROM mobile_jobs WHERE request_id='sub1'") == [{"method": "submit_dont_know"}]
    status, error = phone.error("answer_grading_clarification", {"attemptId": "nope", "answerMd": "x"}, request_id="c1")
    assert (status, error["code"]) == (404, "not_found")
    status, error = phone.error("answer_grading_clarification", {"attemptId": "nope", "answerMd": "x"})
    assert (status, error["code"]) == (422, "validation_error")


# -- ownership at acceptance (§6.5) -----------------------------------------------


def test_a_session_another_device_owns_is_refused_at_acceptance_with_no_job(world):
    phone, _host, repository, *_ = world
    session = phone.start()
    repository.adopt_session(session["sessionId"], None, session["ownerGeneration"])
    response = phone.submit(session["sessionId"], "sub1")
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "session_moved"
    assert rows(repository, "SELECT id FROM mobile_jobs") == []


def test_a_job_accepted_before_a_handoff_completes_on_the_phones_surface(world, monkeypatch):
    """§6.5: queued or running when the desktop takes the session back, it finishes."""

    phone, host, repository, _paths, grader = world
    monkeypatch.setattr(host_module, "JOB_WAIT_SECONDS", 0.05)
    session = phone.start()
    # Hold the job worker so the job is accepted and has not started when the handoff lands.
    release = threading.Event()
    entered = threading.Event()

    def hold(_worker):
        entered.set()
        release.wait(30)

    host.runtime.job_worker.submit(hold)
    assert entered.wait(30)
    response = phone.submit(session["sessionId"], "sub1")
    assert response.status_code == 202
    repository.adopt_session(session["sessionId"], None, session["ownerGeneration"])
    release.set()
    done = poll_job(phone, response.json()["accepted"]["job_id"])
    assert done["state"] == "completed", done
    assert _attempts(repository, "sub1")[0]["entry_surface"] == "phone_practice"
    assert grader.grades == 1


def test_a_full_job_queue_answers_host_busy_and_writes_nothing(world):
    phone, host, repository, *_ = world
    import learnloop_mobile.runtime as runtime

    session = phone.start()
    release = threading.Event()
    entered = threading.Event()

    def hold(_worker):
        entered.set()
        release.wait(30)

    host.runtime.job_worker.submit(hold)
    assert entered.wait(30)
    for _ in range(runtime.JOB_QUEUE_LIMIT):
        host.runtime.job_worker.submit(lambda _worker: None)
    try:
        response = phone.submit(session["sessionId"], "sub1")
        assert response.status_code == 503
        assert response.json()["error"]["code"] == "host_busy"
        assert rows(repository, "SELECT id FROM mobile_jobs") == []
    finally:
        release.set()


# -- status reads (§3.1, §6.1) ----------------------------------------------------


def test_an_unknown_job_is_404_and_an_unknown_submission_is_unknown(world):
    phone, *_ = world
    assert phone.get("/api/v1/jobs/nope").status_code == 404
    assert phone.get("/api/v1/submissions/nope").json() == {"state": "unknown"}


def test_the_submission_endpoint_covers_a_desktops_submissions(world):
    """§6.1: through ``attempt_submission_receipts``, and an attempt with no receipt is running."""

    from learnloop_sidecar.context import SidecarContext
    from learnloop_sidecar.registry import METHOD_REGISTRY

    phone, _host, repository, paths, _grader = world
    desktop = SidecarContext()
    desktop.load_secondary(paths.root)

    def call(name, params):
        spec = METHOD_REGISTRY[name]
        return spec.handler(desktop, spec.params_model.model_validate(params))

    session = call("start_session", {"availableMinutes": 25})
    result = call("submit_attempt", {
        "sessionId": session["sessionId"], "practiceItemId": ITEM, "answerMd": "an answer",
        "attemptType": "independent_attempt", "submissionId": "desktop_sub",
    })
    assert phone.get("/api/v1/submissions/desktop_sub").json() == {"state": "completed", "result": result}
    with repository.connection() as connection:
        connection.execute("DELETE FROM attempt_submission_receipts WHERE submission_id='desktop_sub'")
        connection.commit()
    assert phone.get("/api/v1/submissions/desktop_sub").json() == {"state": "running"}
    desktop.close()


def test_a_status_read_runs_no_handler_and_never_waits_for_a_grade(world, monkeypatch):
    phone, host, *_ = world
    monkeypatch.setattr(host_module, "JOB_WAIT_SECONDS", 0.05)
    grader = world[4]
    grader.gate = threading.Event()
    session = phone.start()
    job_id = phone.submit(session["sessionId"], "sub1").json()["accepted"]["job_id"]
    assert grader.started.wait(30)

    def must_not_run(*_args, **_kwargs):
        raise AssertionError("a status read reached a worker")

    monkeypatch.setattr(host.runtime.rpc_worker, "submit", must_not_run)
    assert phone.get(f"/api/v1/jobs/{job_id}").json()["state"] == "running"
    assert phone.get("/api/v1/submissions/sub1").json()["state"] == "running"
    assert phone.get("/api/v1/queue-revision").status_code == 200
    monkeypatch.undo()
    grader.gate.set()


def test_a_grade_never_blocks_a_short_rpc(world, monkeypatch):
    """§3.1: two workers. The queue answers while a grade is held open."""

    phone, _host, _repository, _paths, grader = world
    monkeypatch.setattr(host_module, "JOB_WAIT_SECONDS", 0.05)
    grader.gate = threading.Event()
    session = phone.start()
    job_id = phone.submit(session["sessionId"], "sub1").json()["accepted"]["job_id"]
    assert grader.started.wait(30)
    assert phone.rpc("get_session", {"sessionId": session["sessionId"]})["sessionId"] == session["sessionId"]
    assert phone.queue_items(session["sessionId"])
    grader.gate.set()
    assert poll_job(phone, job_id)["state"] == "completed"


def test_a_committed_job_bumps_the_token_once_and_a_failed_one_does_not(world, monkeypatch):
    phone, _host, repository, *_ = world
    session = phone.start()
    before = repository.queue_revision()["revision"]
    assert phone.submit(session["sessionId"], "sub1").status_code == 200
    assert repository.queue_revision()["revision"] == before + 1
    install_grading_outage(monkeypatch)
    assert phone.submit(session["sessionId"], "sub2", item="pi_svd_define_002").status_code == 409
    assert repository.queue_revision()["revision"] == before + 1


def test_the_request_log_carries_a_submits_status_and_no_payload(world, monkeypatch):
    phone, _host, repository, _paths, grader = world
    monkeypatch.setattr(host_module, "JOB_WAIT_SECONDS", 0.05)
    grader.gate = threading.Event()
    session = phone.start()
    job_id = phone.submit(session["sessionId"], "sub1", answerMd="my secret answer").json()["accepted"]["job_id"]
    assert grader.started.wait(30)
    grader.gate.set()
    poll_job(phone, job_id)
    log = rows(repository, "SELECT * FROM mobile_request_log WHERE endpoint='rpc:submit_attempt'")
    assert [row["status"] for row in log] == [202]
    assert "my secret answer" not in json.dumps(log)


# -- restart recovery (§6.3, G7) ---------------------------------------------------


def _left_open(repository, device, *, session_id, submission_id, state="running", boots=0, item=ITEM):
    """A row as a dead host leaves it."""

    params = {"sessionId": session_id, "practiceItemId": item, "answerMd": "an answer",
              "attemptType": "independent_attempt", "submissionId": submission_id}
    job, _enqueue = capture.accept_job(
        repository, device_id=device["device_id"], request_id=submission_id, method="submit_attempt", params=params,
        params_sha256="old-run", boot_id="dead-boot",
    )
    with repository.connection() as connection:
        connection.execute("UPDATE mobile_jobs SET state=?,boot_attempts=? WHERE id=?", (state, boots, job["id"]))
        connection.commit()
    return job["id"]


def _restart(paths):
    return TestClient(create_app(config_for(paths.root)), base_url=f"https://{HOSTNAME}")


def _started_session(repository, device) -> str:
    return repository.start_session_exclusive({"available_minutes": 25}, device["device_id"])


@pytest.mark.parametrize("state", ["accepted", "running"])
def test_a_restart_with_no_attempt_grades_again_and_ends_completed(tmp_path, monkeypatch, state):
    paths, repository = seeded_vault(tmp_path / "vault")
    grader = CountingGrader()
    install_grader(monkeypatch, grader)
    device = pair(repository)
    session = _started_session(repository, device)
    job_id = _left_open(repository, device, session_id=session, submission_id="sub1", state=state)
    with _restart(paths) as client:
        done = poll_job(Phone(client, device), job_id)
    assert done["state"] == "completed", done
    assert grader.grades == 1
    assert len(_attempts(repository, "sub1")) == 1
    assert rows(repository, "SELECT boot_attempts FROM mobile_jobs WHERE id=?", job_id) == [{"boot_attempts": 1}]


def test_a_restart_with_a_receipt_marks_it_completed_with_no_handler(tmp_path, monkeypatch):
    paths, repository = seeded_vault(tmp_path / "vault")
    grader = CountingGrader()
    install_grader(monkeypatch, grader)
    device = pair(repository)
    with _restart(paths) as client:
        phone = Phone(client, device)
        session = phone.start()["sessionId"]
        result = phone.submit(session, "sub1").json()["result"]
    with repository.connection() as connection:
        connection.execute("UPDATE mobile_jobs SET state='running',result_json=NULL,finished_at=NULL,host_boot_id='dead-boot'")
        connection.commit()
    grades = grader.grades
    with _restart(paths) as client:
        phone = Phone(client, device)
        body = phone.get("/api/v1/submissions/sub1").json()
    assert body["state"] == "completed" and body["result"] == result
    assert grader.grades == grades


def test_a_restart_with_an_attempt_and_no_receipt_resumes_without_grading_again(tmp_path, monkeypatch):
    """G7: the handler's ``_cached_submission`` resumes the saved completion."""

    paths, repository = seeded_vault(tmp_path / "vault")
    grader = CountingGrader()
    install_grader(monkeypatch, grader)
    device = pair(repository)
    with _restart(paths) as client:
        phone = Phone(client, device)
        session = phone.start()["sessionId"]
        result = phone.submit(session, "sub1").json()["result"]
    with repository.connection() as connection:
        connection.execute("DELETE FROM attempt_submission_receipts WHERE submission_id='sub1'")
        connection.execute("UPDATE mobile_jobs SET state='running',result_json=NULL,finished_at=NULL,host_boot_id='dead-boot'")
        connection.commit()
    grades = grader.grades
    job_id = rows(repository, "SELECT id FROM mobile_jobs")[0]["id"]
    with _restart(paths) as client:
        done = poll_job(Phone(client, device), job_id)
    assert grader.grades == grades
    assert len(_attempts(repository, "sub1")) == 1
    assert done["state"] in ("completed", "failed")
    if done["state"] == "completed":
        assert done["result"]["attemptId"] == result["attemptId"]
    else:
        # No saved completion for this path: the typed "committed" refusal, never a hang.
        assert done["error"]["code"] == "submission_committed"


def test_three_boots_is_a_typed_failure_and_the_draft_stays(tmp_path, monkeypatch):
    """G7: never indefinite ``accepted`` or ``running``."""

    paths, repository = seeded_vault(tmp_path / "vault")
    grader = CountingGrader()
    install_grader(monkeypatch, grader)
    device = pair(repository)
    session = _started_session(repository, device)
    job_id = _left_open(repository, device, session_id=session, submission_id="sub1", boots=2)
    with _restart(paths) as client:
        body = Phone(client, device).get(f"/api/v1/jobs/{job_id}").json()
    assert body["state"] == "failed"
    assert body["error"]["code"] == "host_restart_exhausted"
    assert grader.grades == 0


def test_a_job_of_this_run_is_never_recovered_by_itself(world):
    phone, host, repository, *_ = world
    session = phone.start()
    assert phone.submit(session["sessionId"], "sub1").status_code == 200
    assert host.runtime.recover() == 0
    new_run = capture.recover_jobs(repository, new_ulid())
    assert new_run == []  # terminal rows are nobody's debt

"""Mobile M2a: accepted jobs and the status endpoints (spec §6.3, §6.1, G7).

The grader is a fake that can hold a grade open, so a "dropped connection" here is a
client that got its 202 and went away, and a "restart" is a second host on the same
vault, with the old run's rows left as a dead process leaves them.
"""

from __future__ import annotations

import json
import threading
import time

import pytest

pytest.importorskip("starlette")
from starlette.testclient import TestClient

from learnloop import capture
from learnloop.ids import new_ulid
from learnloop_mobile import host as host_module
from learnloop_mobile.host import create_app

from tests.mobile_host_helpers import (
    HOSTNAME, ITEM, SECOND_ITEM, CountingGrader, Phone, config_for, install_grader, install_grading_outage, pair, poll_job,
    rows,
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
    assert done["state"] in ("completed", "recorded")
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


def test_a_terminal_write_that_keeps_failing_is_paid_without_a_restart(world, monkeypatch):
    """Codex review F7. The attempt is in and every retry of its row failed: the status reads answer
    from what this run owes, and the row is written once the database takes it, with no restart."""

    import sqlite3

    from learnloop_mobile import runtime as runtime_module

    phone, host, repository, *_ = world
    monkeypatch.setattr(runtime_module, "_FINISH_RETRIES", 0)
    monkeypatch.setattr(runtime_module, "_FINISH_DEBT_RETRY_SECONDS", 0.02)
    real_finish = capture.finish_job
    healed = threading.Event()

    def stuck_until_healed(*args, **kwargs):
        if not healed.is_set():
            raise sqlite3.OperationalError("database or disk is full")
        return real_finish(*args, **kwargs)

    monkeypatch.setattr(capture, "finish_job", stuck_until_healed)
    session = phone.start()
    response = phone.submit(session["sessionId"], "owed")
    assert response.status_code == 200, response.text
    job = rows(repository, "SELECT id, state FROM mobile_jobs WHERE request_id='owed'")[0]
    assert job["state"] == "running"
    # The row is behind; what the phone reads is not.
    assert phone.get(f"/api/v1/jobs/{job['id']}").json()["state"] == "completed"
    status = phone.get("/api/v1/submissions/owed").json()
    assert status["state"] == "completed" and status["result"]["attemptId"]
    # A retry of the same request reads the same answer, and no second grade or attempt.
    again = phone.submit(session["sessionId"], "owed")
    assert again.status_code == 200 and again.json()["result"]["attemptId"] == status["result"]["attemptId"]
    assert len(_attempts(repository, "owed")) == 1
    healed.set()
    deadline = time.monotonic() + 10
    while rows(repository, "SELECT state FROM mobile_jobs WHERE request_id='owed'")[0]["state"] != "completed":
        assert time.monotonic() < deadline, "the terminal write was never paid"
        time.sleep(0.01)
    assert phone.get(f"/api/v1/jobs/{job['id']}").json()["state"] == "completed"
    assert host.runtime.owed_finishes() == 0


def test_a_terminal_failure_that_cannot_be_written_is_read_as_failed(world, monkeypatch):
    import sqlite3

    from learnloop_mobile import runtime as runtime_module

    phone, _host, repository, *_ = world
    monkeypatch.setattr(runtime_module, "_FINISH_RETRIES", 0)
    monkeypatch.setattr(runtime_module, "_FINISH_DEBT_RETRY_SECONDS", 3600.0)
    install_grading_outage(monkeypatch)

    def always_full(*args, **kwargs):
        raise sqlite3.OperationalError("database or disk is full")

    monkeypatch.setattr(capture, "finish_job", always_full)
    session = phone.start()
    response = phone.submit(session["sessionId"], "owed2")
    assert response.status_code >= 400
    assert rows(repository, "SELECT state FROM mobile_jobs WHERE request_id='owed2'")[0]["state"] == "running"
    status = phone.get("/api/v1/submissions/owed2").json()
    assert status["state"] == "failed" and status["error"]["code"] == "grading_fallback_required"


# -- orchestrator ruling R2: "failed" means no attempt committed ----------------


def _break_completion(monkeypatch, *, times=None, gate=None):
    """The attempt commits, then its completion raises, as a process dying between the two would.

    ``times=None`` is a completion that can't ever finish. ``gate`` holds a call open.
    """

    import learnloop_sidecar.handlers.practice as practice

    real = practice.run_post_attempt_pipeline
    calls = []

    def broken(*args, **kwargs):
        calls.append(1)
        if gate is not None:
            assert gate.wait(30), "the test never released the completion"
        if times is None or len(calls) <= times:
            raise RuntimeError("the completion stopped after the attempt committed")
        return real(*args, **kwargs)

    monkeypatch.setattr(practice, "run_post_attempt_pipeline", broken)
    return calls


def _heal_completion(monkeypatch, real):
    import learnloop_sidecar.handlers.practice as practice

    monkeypatch.setattr(practice, "run_post_attempt_pipeline", real)


def _status(phone, key):
    return phone.get(f"/api/v1/submissions/{key}").json()


def _poll_until(phone, key, *states, timeout=20.0):
    """Poll as the phone does; what each poll read, the last one in ``states``."""

    seen = []
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        seen.append(_status(phone, key))
        if seen[-1]["state"] in states:
            return seen
        time.sleep(0.02)
    pytest.fail(f"{key} stayed at {seen[-1]}")


def test_a_completion_that_stops_after_the_attempt_finishes_under_the_same_key(world, monkeypatch):
    """Sol's F2 reproduction: never `failed`, one grade, one attempt, and the host re-drives it."""

    phone, _host, repository, _paths, grader = world
    calls = _break_completion(monkeypatch, times=1)
    session = phone.start()
    response = phone.submit(session["sessionId"], "k1")
    # The handler's error is not this job's end: the attempt is in, so the phone keeps polling.
    assert response.status_code == 202, response.text
    assert rows(repository, "SELECT state FROM mobile_jobs WHERE request_id='k1'")[0]["state"] == "running"
    seen = _poll_until(phone, "k1", "completed")
    assert {body["state"] for body in seen} <= {"running", "completed"}
    attempt = _attempts(repository, "k1")
    assert len(attempt) == 1 and grader.grades == 1 and len(calls) == 2
    assert seen[-1]["result"]["attemptId"] == attempt[0]["id"]
    assert repository.attempt_submission_receipt("k1") is not None
    # The row catches up, and a retry of the request reads the same answer.
    deadline = time.monotonic() + 10
    while rows(repository, "SELECT state FROM mobile_jobs WHERE request_id='k1'")[0]["state"] != "completed":
        assert time.monotonic() < deadline
        time.sleep(0.01)
    again = phone.submit(session["sessionId"], "k1")
    assert again.status_code == 200 and again.json()["result"]["attemptId"] == attempt[0]["id"]
    assert grader.grades == 1 and len(_attempts(repository, "k1")) == 1


def test_the_job_endpoint_says_the_same_as_the_submission_endpoint(world, monkeypatch):
    phone, _host, repository, _paths, grader = world
    _break_completion(monkeypatch, times=1)
    session = phone.start()
    accepted = phone.submit(session["sessionId"], "k1").json()["accepted"]
    deadline = time.monotonic() + 20
    while True:
        body = phone.get(f"/api/v1/jobs/{accepted['job_id']}").json()
        assert body["state"] != "failed", body
        if body["state"] == "completed":
            break
        assert time.monotonic() < deadline
        time.sleep(0.02)
    assert body["result"]["attemptId"] == _attempts(repository, "k1")[0]["id"] and grader.grades == 1


def test_the_recovery_runs_once_per_poll_at_most_and_never_on_its_own(world, monkeypatch):
    from learnloop_mobile import runtime as runtime_module

    phone, _host, _repository, _paths, _grader = world
    monkeypatch.setattr(runtime_module, "_REDRIVES_BEFORE_DELAYED", 10_000)
    calls = _break_completion(monkeypatch)
    session = phone.start()
    assert phone.submit(session["sessionId"], "k1").status_code == 202
    assert len(calls) == 1
    # Nobody polling: nothing runs, whatever the time.
    time.sleep(0.2)
    assert len(calls) == 1
    # One poll, one recovery.
    assert _status(phone, "k1")["state"] == "running"
    deadline = time.monotonic() + 10
    while len(calls) < 2:
        assert time.monotonic() < deadline
        time.sleep(0.005)
    time.sleep(0.1)
    assert len(calls) == 2


def test_polls_during_a_recovery_do_not_stack_another(world, monkeypatch):
    phone, _host, _repository, _paths, grader = world
    release = threading.Event()
    release.set()
    calls = _break_completion(monkeypatch, gate=release)
    session = phone.start()
    assert phone.submit(session["sessionId"], "k1").status_code == 202
    assert len(calls) == 1
    release.clear()
    for _ in range(5):
        assert _status(phone, "k1")["state"] == "running"
        time.sleep(0.02)
    deadline = time.monotonic() + 10
    while len(calls) < 2:
        assert time.monotonic() < deadline
        time.sleep(0.005)
    time.sleep(0.1)
    assert len(calls) == 2  # the first of the five, and the other four found it under way
    release.set()
    assert grader.grades == 1


def test_a_job_still_running_is_not_recovered_beside_itself(world, monkeypatch):
    """The attempt can commit while its own job is completing it: that job is the completion."""

    phone, _host, repository, _paths, grader = world
    monkeypatch.setattr(host_module, "JOB_WAIT_SECONDS", 0.05)
    release = threading.Event()
    calls = _break_completion(monkeypatch, times=0, gate=release)
    session = phone.start()
    assert phone.submit(session["sessionId"], "k1").status_code == 202
    deadline = time.monotonic() + 10
    while not calls:
        assert time.monotonic() < deadline
        time.sleep(0.005)
    for _ in range(5):
        assert _status(phone, "k1")["state"] == "running"
    release.set()
    assert _poll_until(phone, "k1", "completed")[-1]["result"]["attemptId"]
    assert len(calls) == 1 and grader.grades == 1 and len(_attempts(repository, "k1")) == 1


def test_a_completion_that_can_never_finish_says_recorded_and_never_failed(world, monkeypatch):
    """The phone opens the feedback; it never takes a new key. A later read can still finish it."""

    import learnloop_sidecar.handlers.practice as practice

    phone, _host, repository, _paths, grader = world
    real = practice.run_post_attempt_pipeline
    _break_completion(monkeypatch)
    session = phone.start()
    assert phone.submit(session["sessionId"], "k1").status_code == 202
    seen = _poll_until(phone, "k1", "recorded")
    assert {body["state"] for body in seen} <= {"running", "recorded"}
    attempt = _attempts(repository, "k1")[0]["id"]
    assert seen[-1]["attempt_id"] == attempt
    assert seen[-1]["error"]["code"] == "submission_committed"
    deadline = time.monotonic() + 10
    while rows(repository, "SELECT state FROM mobile_jobs WHERE request_id='k1'")[0]["state"] != "recorded":
        assert time.monotonic() < deadline
        time.sleep(0.01)
    job_id = rows(repository, "SELECT id FROM mobile_jobs WHERE request_id='k1'")[0]["id"]
    job = phone.get(f"/api/v1/jobs/{job_id}").json()
    assert job["state"] == "recorded" and job["attempt_id"] == attempt
    # A retry says the same in the /rpc shape the phone already reads, and grades nothing.
    again = phone.submit(session["sessionId"], "k1")
    assert again.status_code == 409 and again.json()["error"]["code"] == "submission_committed"
    assert again.json()["error"]["details"]["attempt_id"] == attempt
    assert grader.grades == 1 and len(_attempts(repository, "k1")) == 1
    # Its feedback opens without the completion.
    assert phone.rpc("get_feedback", {"attemptId": attempt})["attemptId"] == attempt
    # And it isn't over: healed, the next read finishes it under the same key.
    _heal_completion(monkeypatch, real)
    done = _poll_until(phone, "k1", "completed")[-1]
    assert done["result"]["attemptId"] == attempt and grader.grades == 1


def test_a_committed_attempt_with_no_saved_completion_is_recorded_at_once(world, monkeypatch):
    """`submission_committed`, the typed refusal for this, is not a job's failure either."""

    phone, _host, repository, _paths, grader = world
    calls = _break_completion(monkeypatch)
    session = phone.start()
    assert phone.submit(session["sessionId"], "k1").status_code == 202
    assert len(calls) == 1
    with repository.connection() as connection:
        connection.execute("DELETE FROM attempt_completion_work")
        connection.commit()
    seen = _poll_until(phone, "k1", "recorded")
    assert len(calls) == 1  # refused before any completion ran
    assert seen[-1]["attempt_id"] == _attempts(repository, "k1")[0]["id"]
    assert grader.grades == 1


def test_a_refusal_that_committed_nothing_is_still_failed(world, monkeypatch):
    phone, _host, repository, *_ = world
    install_grading_outage(monkeypatch)
    session = phone.start()
    assert phone.submit(session["sessionId"], "k1").status_code == 409
    assert _attempts(repository, "k1") == []
    assert _status(phone, "k1")["state"] == "failed"


def test_another_items_attempt_under_the_key_does_not_rewrite_this_requests_refusal(world):
    """A second device reusing a key for another item is refused; that refusal is its own."""

    phone, host, repository, _paths, _grader = world
    session = phone.start()
    assert phone.submit(session["sessionId"], "k1").status_code == 200
    other = Phone(phone.client, pair(repository, label="Other"))
    adopted = other.post("adopt_session", {"sessionId": session["sessionId"], "expectedGeneration": 0})
    assert adopted.status_code == 200, adopted.text
    refused = other.submit(session["sessionId"], "k1", item=SECOND_ITEM)
    assert refused.status_code == 422 and refused.json()["error"]["code"] == "validation_error"
    job = rows(repository, "SELECT id, state FROM mobile_jobs WHERE request_id='k1' AND device_id=?",
               other.device["device_id"])[0]
    assert job["state"] == "failed"
    assert other.get(f"/api/v1/jobs/{job['id']}").json()["state"] == "failed"


def test_the_attempt_of_a_successor_key_counts_for_its_job(world, monkeypatch):
    """§B4's answering key: the attempt is under a successor of the request's key."""

    import learnloop_sidecar.handlers.practice as practice

    phone, _host, repository, _paths, grader = world
    monkeypatch.setattr(practice, "answering_key",
                        lambda _repo, key, _session, _item: (f"{key}~after~a0", True) if key else (None, False))
    _break_completion(monkeypatch, times=1)
    session = phone.start()
    assert phone.submit(session["sessionId"], "k1").status_code == 202
    done = _poll_until(phone, "k1", "completed")[-1]
    assert done["result"]["attemptId"] == _attempts(repository, "k1~after~a0")[0]["id"]
    assert grader.grades == 1


def test_a_desktops_attempt_with_no_receipt_is_finished_by_the_status_read(world, monkeypatch):
    """No job: the desktop died after its attempt, and the phone adopted the session."""

    phone, _host, repository, _paths, grader = world
    _break_completion(monkeypatch, times=1)
    session = phone.start()
    assert phone.submit(session["sessionId"], "k1").status_code == 202
    with repository.connection() as connection:
        connection.execute("DELETE FROM mobile_jobs WHERE request_id='k1'")
        connection.commit()
    seen = _poll_until(phone, "k1", "completed")
    assert seen[0]["state"] == "running"
    assert seen[-1]["result"]["attemptId"] == _attempts(repository, "k1")[0]["id"]
    assert "job_id" not in seen[-1] and grader.grades == 1


def test_finishing_it_moves_the_queue_token_for_the_desktop(world, monkeypatch):
    phone, _host, repository, _paths, _grader = world
    _break_completion(monkeypatch, times=1)
    session = phone.start()
    assert phone.submit(session["sessionId"], "k1").status_code == 202
    before = repository.queue_revision()["revision"]
    _poll_until(phone, "k1", "completed")
    deadline = time.monotonic() + 10
    while repository.queue_revision()["revision"] == before:
        assert time.monotonic() < deadline, "the desktop would never see the completion"
        time.sleep(0.01)


def test_a_terminal_write_a_recovery_owes_is_paid_like_any_other(world, monkeypatch):
    """F7's debt: the row is behind, and what the phone reads is not."""

    import sqlite3

    from learnloop_mobile import runtime as runtime_module

    phone, host, repository, _paths, grader = world
    monkeypatch.setattr(runtime_module, "_FINISH_RETRIES", 0)
    monkeypatch.setattr(runtime_module, "_FINISH_DEBT_RETRY_SECONDS", 0.02)
    real_finish = capture.finish_job
    healed = threading.Event()

    def stuck_until_healed(*args, **kwargs):
        if not healed.is_set():
            raise sqlite3.OperationalError("database or disk is full")
        return real_finish(*args, **kwargs)

    _break_completion(monkeypatch, times=1)
    monkeypatch.setattr(capture, "finish_job", stuck_until_healed)
    session = phone.start()
    assert phone.submit(session["sessionId"], "k1").status_code == 202
    assert _poll_until(phone, "k1", "completed")[-1]["result"]["attemptId"]
    assert rows(repository, "SELECT state FROM mobile_jobs WHERE request_id='k1'")[0]["state"] == "running"
    deadline = time.monotonic() + 10
    while host.runtime.owed_finishes() == 0:
        assert time.monotonic() < deadline
        time.sleep(0.005)
    healed.set()
    deadline = time.monotonic() + 10
    while rows(repository, "SELECT state FROM mobile_jobs WHERE request_id='k1'")[0]["state"] != "completed":
        assert time.monotonic() < deadline, "the terminal write was never paid"
        time.sleep(0.01)
    assert grader.grades == 1


def test_a_failure_the_runtime_can_not_check_is_not_reported_failed(world, monkeypatch):
    """The read that would say whether the attempt committed fails too: the job stays open."""

    import sqlite3

    from learnloop_mobile import runtime as runtime_module

    phone, _host, repository, _paths, grader = world
    monkeypatch.setattr(runtime_module, "_FINISH_RETRIES", 0)
    monkeypatch.setattr(runtime_module, "_FINISH_DEBT_RETRY_SECONDS", 0.02)
    healed = threading.Event()
    real_attempt = type(repository).practice_attempt_by_submission_id

    def unreadable(self, key):
        if threading.current_thread().name == "mobile-job" and not healed.is_set() and failing.is_set():
            raise sqlite3.OperationalError("disk I/O error")
        return real_attempt(self, key)

    failing = threading.Event()
    import learnloop_sidecar.handlers.practice as practice

    real_pipeline = practice.run_post_attempt_pipeline

    def broken(*args, **kwargs):
        failing.set()
        raise RuntimeError("the completion stopped after the attempt committed")

    monkeypatch.setattr(practice, "run_post_attempt_pipeline", broken)
    monkeypatch.setattr(type(repository), "practice_attempt_by_submission_id", unreadable)
    session = phone.start()
    assert phone.submit(session["sessionId"], "k1").status_code == 202
    assert rows(repository, "SELECT state FROM mobile_jobs WHERE request_id='k1'")[0]["state"] != "failed"
    monkeypatch.setattr(practice, "run_post_attempt_pipeline", real_pipeline)
    healed.set()
    assert _poll_until(phone, "k1", "completed")[-1]["result"]["attemptId"]
    assert grader.grades == 1


def test_three_boots_of_a_committed_attempt_say_recorded_not_failed(tmp_path, monkeypatch):
    paths, repository = seeded_vault(tmp_path / "vault")
    grader = CountingGrader()
    install_grader(monkeypatch, grader)
    device = pair(repository)
    with _restart(paths) as client:
        phone = Phone(client, device)
        session = phone.start()["sessionId"]
        attempt = phone.submit(session, "k1").json()["result"]["attemptId"]
    with repository.connection() as connection:
        connection.execute("DELETE FROM attempt_submission_receipts WHERE submission_id='k1'")
        connection.execute(
            "UPDATE mobile_jobs SET state='running',result_json=NULL,finished_at=NULL,host_boot_id='dead-boot',boot_attempts=2"
        )
        connection.commit()
    _break_completion(monkeypatch)
    grades = grader.grades
    with _restart(paths) as client:
        phone = Phone(client, device)
        job_id = rows(repository, "SELECT id FROM mobile_jobs")[0]["id"]
        body = phone.get(f"/api/v1/jobs/{job_id}").json()
        assert body["state"] in ("running", "recorded") and body["state"] != "failed"
        assert rows(repository, "SELECT state FROM mobile_jobs")[0]["state"] == "recorded"
        assert _poll_until(phone, "k1", "recorded")[-1]["attempt_id"] == attempt
    assert grader.grades == grades


def test_a_recorded_job_is_tried_again_by_a_later_host_and_only_so_many_times(tmp_path, monkeypatch):
    """A recorded completion that nobody reads again still gets a try on a restart, boundedly."""

    paths, repository = seeded_vault(tmp_path / "vault")
    grader = CountingGrader()
    install_grader(monkeypatch, grader)
    device = pair(repository)
    with _restart(paths) as client:
        phone = Phone(client, device)
        session = phone.start()["sessionId"]
        attempt = phone.submit(session, "k1").json()["result"]["attemptId"]
    with repository.connection() as connection:
        connection.execute("DELETE FROM attempt_submission_receipts WHERE submission_id='k1'")
        connection.execute(
            "UPDATE mobile_jobs SET state='recorded',result_json=NULL,error_json='{}',host_boot_id='dead-boot',boot_attempts=0"
        )
        connection.commit()
    assert capture.recover_jobs(repository, "boot-1") != []
    job = rows(repository, "SELECT state, boot_attempts FROM mobile_jobs")[0]
    assert job == {"state": "accepted", "boot_attempts": 1}
    with repository.connection() as connection:
        connection.execute(
            "UPDATE mobile_jobs SET state='recorded',host_boot_id='dead-boot',boot_attempts=?", (capture.MAX_BOOTS,)
        )
        connection.commit()
    assert capture.recover_jobs(repository, "boot-2") == []
    assert rows(repository, "SELECT state FROM mobile_jobs")[0]["state"] == "recorded"
    assert attempt


def test_the_recorded_state_is_in_the_jobs_schema(world):
    _phone, _host, repository, *_ = world
    with repository.connection() as connection:
        ddl = connection.execute("SELECT sql FROM sqlite_master WHERE name='mobile_jobs'").fetchone()[0]
    assert "'recorded'" in ddl


def test_a_recovery_that_answers_pending_finishes_nothing(world, monkeypatch):
    """Recovery's other word: no failure of its own, and never a completed job with no result."""

    import learnloop_sidecar.handlers.practice as practice

    phone, _host, repository, _paths, _grader = world
    real_pipeline = practice.run_post_attempt_pipeline
    real_cached = practice._cached_submission
    _break_completion(monkeypatch)
    monkeypatch.setattr(practice, "_cached_submission", lambda *args: None)
    session = phone.start()
    assert phone.submit(session["sessionId"], "k1").status_code == 202
    _poll_until(phone, "k1", "recorded")
    assert rows(repository, "SELECT result_json FROM mobile_jobs WHERE request_id='k1'")[0]["result_json"] is None
    monkeypatch.setattr(practice, "_cached_submission", real_cached)
    monkeypatch.setattr(practice, "run_post_attempt_pipeline", real_pipeline)
    assert _poll_until(phone, "k1", "completed")[-1]["result"]["attemptId"]

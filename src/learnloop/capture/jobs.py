"""Accepted jobs for the phone's long mutations (mobile spec §6.3).

The host accepts a long request here, in one transaction, and only then answers;
its job worker runs the accepted copy through the ordinary sidecar handler, whether
or not the phone is still connected. Everything here is the ``mobile_jobs`` ledger:
no handler, no provider, no evidence. Reads work on a read-only repository, so the
status endpoints can never resume a completion or wait on a lock (§3.1).
"""

from __future__ import annotations

from datetime import datetime
import json
from typing import Any, Callable

from learnloop.db.repositories import Repository
from learnloop.ids import new_ulid

from .devices import _now
from .errors import CaptureError

ACCEPTED, RUNNING, COMPLETED, FAILED = "accepted", "running", "completed", "failed"
#: A submit whose attempt committed and whose completion has not finished (orchestrator ruling
#: R2). Not a failure: the attempt stands, its key is spent, and only its feedback is delayed.
RECORDED = "recorded"
OPEN_STATES = (ACCEPTED, RUNNING)
SUBMIT_METHODS = ("submit_attempt", "submit_dont_know")
#: The error a recorded submit answers /rpc with, the sidecar's own refusal for this.
SUBMISSION_COMMITTED = "submission_committed"
#: A job a restarted host has picked up this many times has failed for good (§6.3).
MAX_BOOTS = 3
HOST_RESTART_EXHAUSTED = "host_restart_exhausted"


def _row(row: Any) -> dict[str, Any]:
    job = dict(row)
    job["params"] = json.loads(job.pop("params_json"))
    result, error = job.pop("result_json"), job.pop("error_json")
    job["result"] = json.loads(result) if result is not None else None
    job["error"] = json.loads(error) if error is not None else None
    return job


def recorded_error(attempt: dict[str, Any]) -> dict[str, Any]:
    """What a recorded submit says, in ``CommandError``'s four fields."""

    return {
        "code": SUBMISSION_COMMITTED, "retryable": False,
        "message": "Your answer is recorded. Its feedback is delayed.",
        "details": {"attempt_id": attempt["id"], "attempt_type": attempt.get("attempt_type"), "route_status": "unknown"},
    }


def get_job(repo: Repository, job_id: str) -> dict[str, Any] | None:
    with repo.connection() as conn:
        row = conn.execute("SELECT * FROM mobile_jobs WHERE id=?", (job_id,)).fetchone()
    return _row(row) if row is not None else None


def job_for_request(repo: Repository, request_id: str) -> dict[str, Any] | None:
    """The newest job for a request id, whichever device made it (reads are unrestricted, §6.5)."""

    with repo.connection() as conn:
        row = conn.execute(
            "SELECT * FROM mobile_jobs WHERE request_id=? ORDER BY accepted_at DESC, id DESC LIMIT 1",
            (request_id,),
        ).fetchone()
    return _row(row) if row is not None else None


def accept_job(
    repo: Repository,
    *,
    device_id: str,
    request_id: str,
    method: str,
    params: dict[str, Any],
    params_sha256: str,
    boot_id: str,
    check_new: Callable[[], None] | None = None,
    now: datetime | None = None,
) -> tuple[dict[str, Any], bool]:
    """``(job, enqueue)``, committed before the host answers (§6.3).

    The same id with the same hash returns the existing job: identical retries are
    coalesced, with no second provider call. The same id with another hash is
    ``409 submission_conflict``. A job that failed with a retryable error (grading
    down, a busy database) wrote nothing a retry could repeat: the same request runs
    it again, under the same row, which is how "retry later" works on one
    submission id. ``check_new`` runs in this transaction, only when a new row or
    a retry is about to be accepted: admission and session ownership (§6.5), so no
    adopt commits between the check and the job.
    """

    at = _now(now).isoformat()
    with repo.atomic(), repo.connection() as conn:
        row = conn.execute(
            "SELECT * FROM mobile_jobs WHERE device_id=? AND request_id=?", (device_id, request_id)
        ).fetchone()
        if row is not None:
            job = _row(row)
            if job["params_sha256"] != params_sha256 or job["method"] != method:
                raise CaptureError("submission_conflict", 409, "This request id was used for a different request.")
            if job["state"] != FAILED or not (job["error"] or {}).get("retryable"):
                return job, False
            if check_new is not None:
                check_new()
            conn.execute(
                """UPDATE mobile_jobs SET state=?,error_json=NULL,result_json=NULL,host_boot_id=?,
                   boot_attempts=0,started_at=NULL,finished_at=NULL WHERE id=?""",
                (ACCEPTED, boot_id, job["id"]),
            )
            job_id = job["id"]
        else:
            if check_new is not None:
                check_new()
            job_id = new_ulid()
            conn.execute(
                """INSERT INTO mobile_jobs(id,device_id,request_id,method,params_json,params_sha256,state,
                   host_boot_id,boot_attempts,accepted_at) VALUES (?,?,?,?,?,?,?,?,0,?)""",
                (job_id, device_id, request_id, method, json.dumps(params, sort_keys=True), params_sha256,
                 ACCEPTED, boot_id, at),
            )
        row = conn.execute("SELECT * FROM mobile_jobs WHERE id=?", (job_id,)).fetchone()
    return _row(row), True


def submission_in_flight(repo: Repository, practice_item_id: str) -> bool:
    """A phone's answer to ``practice_item_id`` accepted and not yet finished (mobile v2 V3; Codex review of V3, F2).

    Its acceptance checked the session's owner, and it completes after a handoff (§6.5): until then, whatever its
    answer consumes (a probe's presentation, the feedback it releases) is still the answer's. Reads only."""

    with repo.connection() as conn:
        rows = conn.execute(
            f"SELECT params_json FROM mobile_jobs WHERE state IN ({','.join('?' for _ in OPEN_STATES)}) "
            f"AND method IN ({','.join('?' for _ in SUBMIT_METHODS)})",
            (*OPEN_STATES, *SUBMIT_METHODS),
        ).fetchall()
    for row in rows:
        params = json.loads(row["params_json"])
        if (params.get("practice_item_id") or params.get("practiceItemId")) == practice_item_id:
            return True
    return False


def start_job(repo: Repository, job_id: str, *, now: datetime | None = None) -> None:
    with repo.atomic(), repo.connection() as conn:
        conn.execute(
            "UPDATE mobile_jobs SET state=?,started_at=? WHERE id=? AND state IN ('accepted','running')",
            (RUNNING, _now(now).isoformat(), job_id),
        )


def finish_job(
    repo: Repository, job_id: str, *, result: Any = None, error: dict[str, Any] | None = None,
    state: str | None = None, now: datetime | None = None,
) -> None:
    """``state`` is only for :data:`RECORDED`, which carries an error and is no failure."""

    state = state or (FAILED if error is not None else COMPLETED)
    with repo.atomic(), repo.connection() as conn:
        conn.execute(
            "UPDATE mobile_jobs SET state=?,result_json=?,error_json=?,finished_at=? WHERE id=?",
            (
                state,
                None if error is not None else json.dumps(result, sort_keys=True),
                json.dumps(error, sort_keys=True) if error is not None else None,
                _now(now).isoformat(),
                job_id,
            ),
        )


def job_receipt(connection: Any, job_id: str) -> Any:
    """Mobile v2 V4 (Codex review F5): the result an open job's handler already committed, or None.

    An outbox intent's handler writes its rows and this receipt in one transaction (``write_job_receipt``), so a
    job a restart re-runs (``recover_jobs`` keeps ``result_json``) answers from the receipt and writes nothing
    again. Read in the handler's own transaction."""

    row = connection.execute(
        f"SELECT result_json FROM mobile_jobs WHERE id=? AND state IN ({','.join('?' for _ in OPEN_STATES)})",
        (job_id, *OPEN_STATES),
    ).fetchone()
    return json.loads(row[0]) if row is not None and row[0] is not None else None


def write_job_receipt(connection: Any, job_id: str, result: Any) -> None:
    """The handler's result on its open job's row, in the handler's transaction (see :func:`job_receipt`). The job
    stays open: the runtime still writes its end, with the same result."""

    connection.execute(
        f"UPDATE mobile_jobs SET result_json=? WHERE id=? AND state IN ({','.join('?' for _ in OPEN_STATES)})",
        (json.dumps(result, sort_keys=True), job_id, *OPEN_STATES),
    )


def recover_jobs(repo: Repository, boot_id: str, *, now: datetime | None = None) -> list[dict[str, Any]]:
    """What a starting host owes (§6.3): the jobs another run left open, to run again.

    A receipt means the handler finished and only its job row did not: mark it
    completed. Otherwise the job is requeued, and the handler decides what that
    means: ``_cached_submission`` resumes a committed attempt's saved completion
    without grading again, and no attempt means no evidence was written, so it grades
    again. After :data:`MAX_BOOTS` runs it fails with ``host_restart_exhausted``, and
    the draft is still in the checkpoint; unless the attempt committed, which makes it
    :data:`RECORDED` (R2). A recorded job is one more completion owed, so it gets the
    same bounded tries.
    """

    at = _now(now).isoformat()
    requeued: list[dict[str, Any]] = []
    with repo.atomic(), repo.connection() as conn:
        rows = conn.execute(
            """SELECT * FROM mobile_jobs WHERE host_boot_id<>? AND
               (state IN ('accepted','running') OR (state=? AND boot_attempts<?)) ORDER BY accepted_at, id""",
            (boot_id, RECORDED, MAX_BOOTS),
        ).fetchall()
        for row in rows:
            job = _row(row)
            submit = job["method"] in SUBMIT_METHODS
            receipt = repo.attempt_submission_receipt(job["request_id"]) if submit else None
            if receipt is not None:
                conn.execute(
                    "UPDATE mobile_jobs SET state=?,result_json=?,error_json=NULL,finished_at=? WHERE id=?",
                    (COMPLETED, json.dumps(receipt["result"], sort_keys=True), at, job["id"]),
                )
                continue
            attempts = int(job["boot_attempts"]) + 1
            if attempts >= MAX_BOOTS:
                attempt = repo.practice_attempt_by_submission_id(job["request_id"]) if submit else None
                if attempt is not None:
                    conn.execute(
                        "UPDATE mobile_jobs SET state=?,error_json=?,boot_attempts=?,finished_at=? WHERE id=?",
                        (RECORDED, json.dumps(recorded_error(attempt), sort_keys=True), attempts, at, job["id"]),
                    )
                    continue
                error = {"code": HOST_RESTART_EXHAUSTED, "retryable": False, "details": {},
                         "message": "The desktop restarted too many times during this request; your draft is saved."}
                conn.execute(
                    "UPDATE mobile_jobs SET state=?,error_json=?,boot_attempts=?,finished_at=? WHERE id=?",
                    (FAILED, json.dumps(error, sort_keys=True), attempts, at, job["id"]),
                )
                continue
            conn.execute(
                "UPDATE mobile_jobs SET state=?,host_boot_id=?,boot_attempts=?,error_json=NULL,started_at=NULL,finished_at=NULL WHERE id=?",
                (ACCEPTED, boot_id, attempts, job["id"]),
            )
            requeued.append({**job, "state": ACCEPTED, "host_boot_id": boot_id, "boot_attempts": attempts})
    return requeued

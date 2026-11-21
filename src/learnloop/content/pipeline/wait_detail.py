"""What a learner waiting on a book can be told, in facts the code recorded when they happened.

Two waits: a book being got ready for questions (its build: the inventory's windows, then the study map's
synthesis), and a section's questions being written (one topic at a time). For each, the status line carries a
typed detail beside its words (``build_detail`` on a build's own working line, ``writing_detail`` on the reading's
questions fact), which Today and the Library turn into a few short lines.

Every field is a recorded fact, named with its source:

- times a request was sent and a reply received: ``model_call_receipts`` (a receipt is written before its request
  is sent and finished when it ends);
- streamed output: ``ingest_job_progress.output_*`` (``runner.job_output_recorder``, fed by a streaming transport);
  a transport that does not stream records none, and the detail then says nothing about output;
- the build's step, its drafted-topic count and the units it reused: ``ingest_job_progress`` (the synthesis's own
  progress callback and the inventory handler);
- windows read and parts planned: the job's ``current_window``/``total_windows`` (the inventory counts a window once
  its answer is checked and kept; the synthesis names the part it is working on);
- which topic is being written, since when, and how long topics took here: the job's ``question_parts``
  (``started_at`` when a topic's writing is asked for, ``written_at`` once its questions applied);
- how long builds took here: the library's finished automatic builds (``add_source.build_minutes_measured``).

Nothing is estimated, extrapolated or read from a model's unfinished answer, and a lease heartbeat is never taken
for output. A measured time comes with the number of samples it rests on, and is absent with none.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Mapping

from learnloop.clock import parse_utc

#: The jobs a book's build is made of (``add_source.build_progress`` counts the same steps).
BUILD_STEP_JOBS = frozenset({"inventory", "bootstrap_synthesis", "append_synthesis"})

#: The synthesis's own steps (``source_set_synthesis._notify``), by what the learner is told is happening.
_SYNTHESIS_STAGE = {
    None: "planning",
    "plan": "planning",
    "plan_reused": "planning",
    "evidence": "planning",
    "identity": "checking",
    "validate": "checking",
    "structure": "organizing",
    "persist": "saving",
    "apply": "saving",
}


def _iso(value: Any) -> str | None:
    """One time format for the screens ("…Z", whole seconds), whatever wrote it."""

    if not value:
        return None
    try:
        parsed = parse_utc(str(value))
    except ValueError:
        return None
    return parsed.replace(microsecond=0).isoformat().replace("+00:00", "Z") if parsed else None


def _when(value: Any) -> datetime | None:
    try:
        return parse_utc(str(value)) if value else None
    except ValueError:
        return None


def _int(value: Any) -> int | None:
    return value if isinstance(value, int) and not isinstance(value, bool) and value >= 0 else None


def _progress(repo, job: Mapping[str, Any]) -> dict[str, Any] | None:
    """The job's progress row, only when it is this attempt's."""

    row = repo.ingest_job_progress(str(job["id"]))
    if row is None or row.get("attempt_count") != job.get("attempt_count"):
        return None
    return row


def _retry(job: Mapping[str, Any], progress: Mapping[str, Any] | None) -> bool:
    """Whether this is a try after an earlier one stopped: the runner's own second try, or a later attempt (Try
    again, or work taken over after its worker stopped)."""

    return bool(progress and (progress.get("try_number") or 1) > 1) or int(job.get("attempt_count") or 0) > 1


def delivery(repo, job: Mapping[str, Any], progress: Mapping[str, Any] | None) -> dict[str, Any]:
    """What the job's model requests have done, this try: when the newest request still in flight was sent, when
    the newest reply was received, and the in-flight request's streamed output so far (its count of pieces and when
    the last arrived; 0 and None with none, or on a transport that does not stream)."""

    receipts = repo.model_call_times(owner_kind="ingest_job", owner_id=str(job["id"]))
    since = _when((progress or {}).get("try_started_at"))

    def this_try(row: Mapping[str, Any]) -> bool:
        started = _when(row.get("started_at"))
        return since is None or (started is not None and started >= since)

    in_flight = [row for row in receipts if row.get("status") == "started" and not row.get("finished_at") and this_try(row)]
    replies = [row for row in receipts if row.get("status") == "completed" and row.get("finished_at")]
    sent = max((_when(row["started_at"]) for row in in_flight if _when(row["started_at"])), default=None)
    received = max((_when(row["finished_at"]) for row in replies if _when(row["finished_at"])), default=None)
    out: dict[str, Any] = {
        "request_sent_at": _iso(sent.isoformat()) if sent else None,
        "reply_received_at": _iso(received.isoformat()) if received else None,
        "output_pieces": 0,
        "last_output_at": None,
    }
    if progress and progress.get("output_events") and progress.get("output_call_id") in {row["id"] for row in in_flight}:
        out["output_pieces"] = int(progress["output_events"])
        out["last_output_at"] = _iso(progress.get("last_output_at"))
    return out


def _measured(measured: tuple[float, int] | None) -> dict[str, Any] | None:
    if measured is None:
        return None
    minutes, samples = measured
    return {"minutes": round(minutes, 1), "samples": samples}


def build_detail(repo, batch: Mapping[str, Any], *, measured: tuple[float, int] | None, now: datetime) -> dict[str, Any]:
    """A build under way, in facts. ``stage``: ``queued`` (no step running yet), ``reading`` (the inventory;
    ``inventory`` holds its windows done and known, and the units it reused), ``planning`` (the synthesis's model
    passes; ``synthesis`` holds the part it is on, of how many, and the pass: ``plan``, ``plan_reused`` or
    ``evidence``, a further pass with the passages the plan asked for), ``organizing`` (the topics' structure),
    ``checking`` (the plan's checks; ``drafted_topics`` once a complete parsed candidate exists), ``saving``.
    ``measured``: this library's build time, scaled to this build's scope, with its sample count, or None."""

    jobs = [job for job in repo.ingest_jobs_for_batch(str(batch["id"])) if job.get("job_type") in BUILD_STEP_JOBS]
    running = next((job for job in jobs if job.get("status") == "running"), None)
    detail: dict[str, Any] = {
        "as_of": _iso(now.astimezone(UTC).isoformat()),
        "started_at": _iso(batch.get("started_at")),
        "stage": "queued",
        "retry": False,
        "delivery": None,
        "measured": _measured(measured),
    }
    if running is None:
        return detail
    progress = _progress(repo, running)
    detail["retry"] = _retry(running, progress)
    detail["delivery"] = delivery(repo, running, progress)
    current, total = _int(running.get("current_window")), _int(running.get("total_windows"))
    if running["job_type"] == "inventory":
        detail["stage"] = "reading"
        detail["inventory"] = {"done": min(current or 0, total) if total is not None else (current or 0), "total": total,
                               "reused": _int((progress or {}).get("reused"))}
        return detail
    step = (progress or {}).get("step")
    detail["stage"] = _SYNTHESIS_STAGE.get(step, "planning")
    if detail["stage"] == "planning":
        detail["synthesis"] = {"part": current, "parts": total, "pass": step}
    if step == "validate" and _int((progress or {}).get("drafted_topics")) is not None:
        detail["drafted_topics"] = int(progress["drafted_topics"])  # type: ignore[index]
    return detail


def topic_minutes(repo, *, sample: int = 5) -> tuple[float, int] | None:
    """How long one topic's questions take to write in this library: the middle of the newest ``sample`` topics
    written (from the request for them to their questions applied), with how many it rests on; None before any
    topic was timed. The same rule as a build's measured time (``add_source.build_minutes_measured``)."""

    seconds: list[float] = []
    for job in repo.ingest_jobs_by_types(("practice_expansion",), limit=sample * 8):
        for part in reversed((job.get("payload") or {}).get("question_parts") or []):
            if len(seconds) >= sample:
                break
            started, written = _when(part.get("started_at")), _when(part.get("written_at"))
            if started is None or written is None or part.get("error"):
                continue
            seconds.append(max(0.0, (written - started).total_seconds()))
        if len(seconds) >= sample:
            break
    if not seconds:
        return None
    ordered = sorted(seconds)
    return ordered[len(ordered) // 2] / 60.0, len(seconds)


def writing_detail(repo, vault, job: Mapping[str, Any], *, measured: tuple[float, int] | None, now: datetime) -> dict[str, Any]:
    """A section's questions being written, in facts: ``queued`` while its job waits its turn; the topic being
    written now (``topic``: its title, which of the job's topics and of how many; ``reading_questions`` drops the
    place where other jobs write too) and when its writing was asked for; the job's model
    requests (``delivery``); whether this is a retry; and ``measured``, this library's time per topic with its
    sample count, or None before a topic was timed."""

    detail: dict[str, Any] = {
        "as_of": _iso(now.astimezone(UTC).isoformat()),
        "started_at": _iso(job.get("started_at")),
        "queued": job.get("status") == "queued",
        "retry": False,
        "topic": None,
        "topic_started_at": None,
        "delivery": None,
        "measured": _measured(measured),
    }
    if job.get("status") != "running":
        return detail
    parts = (job.get("payload") or {}).get("question_parts") or []
    for index, part in enumerate(parts):
        if part.get("started_at") and not part.get("patch_id") and not part.get("error"):
            topic_id = str(part.get("topic_id") or "")
            topic = (getattr(vault, "learning_objects", None) or {}).get(topic_id)
            detail["topic"] = {"title": str(getattr(topic, "title", "") or "").strip() or None,
                               "index": index + 1, "total": len(parts)}
            detail["topic_started_at"] = _iso(part["started_at"])
            break
    progress = _progress(repo, job)
    detail["retry"] = _retry(job, progress)
    detail["delivery"] = delivery(repo, job, progress)
    return detail


__all__ = ["BUILD_STEP_JOBS", "build_detail", "delivery", "topic_minutes", "writing_detail"]

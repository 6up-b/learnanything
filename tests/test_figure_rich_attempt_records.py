"""Every attempt of a rich (video) job recorded, and why it stopped (ADR-017's open item for the rich jobs).

A rich job notes each attempt in a ``figure_rich_author`` record (the ``figure_author`` record's shape, from the same
``AuthorAttempts``) with its code, and a job that ends with no row writes a ``figure_rich_stop`` record with its stop
code, so a requeue that rewrites the job's error leaves the reason it stopped for. Each code is staged here with the
fake rich author, renderer and function runner; the codes are the constants', so a new one fails
:func:`test_every_attempt_code_is_staged` until a case stages it.
"""

from __future__ import annotations

import json
from typing import Any

import pytest

from learnloop.ai.spend import SpendLimitExceeded
from learnloop.content.authoring.concept_animation import RenderResult
from learnloop.figures import records as FR
from learnloop.figures import rich as RICH
from tests import rich_fixtures as RF
from tests.figure_fixtures import rows
from tests.figure_rich_job_helpers import WHY, _Rig

QUICK = [("rich", "manim", RF.brief(), WHY)]
WRONG_CLAIM = RF.scene_output(declared={**RF.DECLARED, "claims": [
    {"kind": "equals", "function": "x", "expr": "exp(a*t)*sin(b*t)"}]})


def _run(tmp_path, monkeypatch, rich_answers=None, **rig: Any) -> _Rig:
    found = _Rig(tmp_path, monkeypatch, list(QUICK), rich_answers, **rig)
    found.build()
    found.ingest.drain()
    return found


def _records(rig: _Rig, kind: str) -> list[dict[str, Any]]:
    found = []
    for row in rows(rig.repository, "decision_records"):
        if row["kind"] == kind:
            row = dict(row)
            row["facts"] = json.loads(row["facts_json"])
            found.append(row)
    return sorted(found, key=lambda record: record["facts"].get("attempt", 0))


def _attempts(rig: _Rig) -> list[tuple[str, str]]:
    return [(record["rule"], record["status"]) for record in _records(rig, FR.KIND_RICH_AUTHOR)]


def test_a_video_that_lands_records_its_one_attempt_on_the_figure(tmp_path, monkeypatch):
    rig = _run(tmp_path, monkeypatch)
    (record,) = _records(rig, FR.KIND_RICH_AUTHOR)
    stored = [row for row in rows(rig.repository, "interactive_figures") if row["tier"] == "manim"]
    assert (record["rule"], record["status"], record["subject_kind"]) == (FR.ACCEPTED, "chosen", "figure")
    assert record["subject_id"] == stored[0]["id"] and record["facts"]["outcome"] == "illustrative"
    assert json.loads(record["versions_json"])["prompt_version"] == RICH.RICH_PROMPT_VERSION
    assert _records(rig, FR.KIND_RICH_STOP) == []


@pytest.mark.parametrize(("answers", "first"), [
    ([WRONG_CLAIM, RF.scene_output()], FR.CLAIM_FAILED),
    ([RF.scene_output(scene=""), RF.scene_output()], FR.RICH_BRIEF_INVALID),
    ([RF.scene_output(scene="import os\n" + RF.SCENE), RF.scene_output()], FR.SCENE_INVALID),
    ([RuntimeError("the animation model fell over"), RF.scene_output()], FR.MODEL_FAILED),
])
def test_attempt_ones_problem_survives_attempt_two(tmp_path, monkeypatch, answers, first):
    rig = _run(tmp_path, monkeypatch, answers)
    assert _attempts(rig) == [(first, "discarded"), (FR.ACCEPTED, "chosen")]


def test_a_scene_out_of_pacing_is_repaired_by_the_second_attempt(tmp_path, monkeypatch):
    import learnloop.content.authoring.concept_animation as CA

    paced = iter([["the scene is too fast"]])
    monkeypatch.setattr(CA, "lint_scene_pacing", lambda *_args, **_kwargs: next(paced, []))
    rig = _run(tmp_path, monkeypatch)
    assert _attempts(rig) == [(FR.PACING_FAILED, "discarded"), (FR.ACCEPTED, "chosen")]


@pytest.mark.parametrize(("render", "first"), [
    (RF.failed_render(), FR.RENDER_FAILED),
    (RenderResult(False, None, "render timed out after 600s", None), FR.RENDER_TIMEOUT),
])
def test_a_failed_render_and_its_repair_are_two_attempts(tmp_path, monkeypatch, render, first):
    rig = _run(tmp_path, monkeypatch, renders=RF.Renders([render]))
    assert _attempts(rig) == [(first, "discarded"), (FR.RENDER_REPAIRED, "chosen")]
    repair = _records(rig, FR.KIND_RICH_AUTHOR)[1]
    assert repair["facts"]["repair"] == "render"


def test_a_second_request_refused_by_the_budget_is_its_own_attempt(tmp_path, monkeypatch):
    rig = _run(tmp_path, monkeypatch, [WRONG_CLAIM, SpendLimitExceeded("today's figures", rule="envelope_cap")])
    assert _attempts(rig) == [(FR.CLAIM_FAILED, "discarded"), (FR.REQUEST_REFUSED, "refused")]
    assert _records(rig, FR.KIND_RICH_AUTHOR)[-1]["facts"]["outcome"] == "failed"


def test_a_stop_is_recorded_and_survives_the_requeue(tmp_path, monkeypatch):
    rig = _Rig(tmp_path, monkeypatch, list(QUICK))
    rig.build()
    RF.configure(rig.paths, manim_opt_in="declined")
    rig.ingest.drain()
    job = rig.job()
    (stop,) = _records(rig, FR.KIND_RICH_STOP)
    assert (stop["status"], stop["rule"], stop["subject_kind"], stop["subject_id"]) == (
        "refused", "rich_disabled", "job", job["id"])
    assert stop["facts"] == {"attempts": 0, "request_id": stop["facts"]["request_id"], "retryable": False}
    assert _records(rig, FR.KIND_RICH_AUTHOR) == []
    assert rig.ingest.requeue_failed_unless_cancelled(job["batch_id"], error_code="rich_disabled")
    assert rig.job()["status"] == "queued"  # the requeue rewrote the job; the record still says why it stopped
    assert [record["rule"] for record in _records(rig, FR.KIND_RICH_STOP)] == ["rich_disabled"]


def test_a_stop_waiting_for_the_plan_is_deferred_with_its_attempt(tmp_path, monkeypatch):
    from learnloop.figures import routes as R

    rig = _run(tmp_path, monkeypatch, [R.FigureUnavailable("unavailable", "the plan is down")])
    (stop,) = _records(rig, FR.KIND_RICH_STOP)
    assert (stop["status"], stop["rule"], stop["facts"]["retryable"]) == ("deferred", RICH.WAITING_FOR_PLAN, True)
    assert stop["facts"]["attempts"] == 1
    assert _attempts(rig) == [(FR.REQUEST_REFUSED, "refused")]


#: The attempt codes staged above.
STAGED = {FR.ACCEPTED, FR.CLAIM_FAILED, FR.RICH_BRIEF_INVALID, FR.SCENE_INVALID, FR.MODEL_FAILED, FR.PACING_FAILED,
          FR.RENDER_FAILED, FR.RENDER_TIMEOUT, FR.RENDER_REPAIRED, FR.REQUEST_REFUSED}


def test_every_attempt_code_is_staged():
    assert STAGED == set(FR.RICH_ATTEMPT_CODES)


def test_finished_verdict_is_durable_before_next_author_call(tmp_path, monkeypatch):
    rig = _Rig(tmp_path, monkeypatch, list(QUICK), [WRONG_CLAIM, RF.scene_output()])
    rig.build()
    complete = rig.rich_author.complete
    snapshots = []

    def inspect(request):
        snapshots.append(_attempts(rig))
        return complete(request)

    monkeypatch.setattr(rig.rich_author, "complete", inspect)
    rig.ingest.drain()
    assert snapshots == [[], [(FR.CLAIM_FAILED, "discarded")]]
    assert _attempts(rig) == [(FR.CLAIM_FAILED, "discarded"), (FR.ACCEPTED, "chosen")]


def test_final_attempt_commits_with_figure(tmp_path, monkeypatch):
    rig = _Rig(tmp_path, monkeypatch, list(QUICK))
    rig.build()
    from contextlib import contextmanager
    from learnloop.db.repositories import Repository

    observer = Repository(rig.repository.sqlite_path)
    atomic = Repository.atomic
    snapshots = []

    @contextmanager
    def observe_commit(repository):
        with atomic(repository):
            yield
        if not snapshots and any(row["tier"] == "manim" for row in rows(observer, "interactive_figures")):
            snapshots.append(_attempts(rig))

    monkeypatch.setattr(Repository, "atomic", observe_commit)
    rig.ingest.drain()
    assert snapshots == [[(FR.ACCEPTED, "chosen")]]
    assert _attempts(rig) == snapshots[0]


def test_rich_job_cancelled_at_its_initial_report_records_stop(tmp_path, monkeypatch):
    from learnloop.content.pipeline.runner import JobCancelled, JobContext

    rig = _Rig(tmp_path, monkeypatch, list(QUICK))
    rig.build()

    def cancel(*args, **kwargs):
        raise JobCancelled("cancel pressed")

    monkeypatch.setattr(JobContext, "report", cancel)
    rig.ingest.drain()
    assert rig.job()["status"] == "cancelled"
    (stop,) = _records(rig, FR.KIND_RICH_STOP)
    assert (stop["rule"], stop["subject_id"], stop["facts"]["attempts"]) == ("cancelled", rig.job()["id"], 0)


def test_rich_repair_refused_by_budget_records_the_refusal(tmp_path, monkeypatch):
    rig = _run(tmp_path, monkeypatch, [RF.scene_output(), SpendLimitExceeded("cap", rule="envelope_cap")],
               renders=RF.Renders([RF.failed_render()]))
    assert _attempts(rig) == [(FR.RENDER_FAILED, "discarded"), (FR.REQUEST_REFUSED, "refused")]


def test_cancel_before_fallback_render_records_no_render(tmp_path, monkeypatch):
    import learnloop.content.authoring.concept_animation as CA
    from learnloop.content.pipeline.runner import JobCancelled

    rig = _Rig(tmp_path, monkeypatch, list(QUICK), [RF.scene_output(), WRONG_CLAIM])
    rig.build()
    monkeypatch.setattr(CA, "lint_scene_pacing", lambda *_args, **_kwargs: ["too fast"])
    check = RICH.FiguresGate.check

    def cancel_at_render(self, purpose="request"):
        if purpose == "render":
            raise JobCancelled("cancel before render")
        return check(self, purpose)

    monkeypatch.setattr(RICH.FiguresGate, "check", cancel_at_render)
    rig.ingest.drain()
    assert rig.job()["status"] == "cancelled" and rig.renders.calls == []
    records = _records(rig, FR.KIND_RICH_AUTHOR)
    assert len(records) == 2
    assert all(not r["facts"].get("fallback_rendered") for r in records)


def test_attempts_record_the_model_each_receipt_resolved(tmp_path, monkeypatch):
    from learnloop.ai.execution import report_call_usage

    rig = _Rig(tmp_path, monkeypatch, list(QUICK), [WRONG_CLAIM, RF.scene_output()])
    rig.build()
    complete = rig.rich_author.complete

    def resolved(request):
        result = complete(request)
        report_call_usage({"resolved_model": f"resolved-{rig.rich_author.calls}"})
        return result

    monkeypatch.setattr(rig.rich_author, "complete", resolved)
    rig.ingest.drain()
    records = _records(rig, FR.KIND_RICH_AUTHOR)
    assert [json.loads(r["versions_json"])["model"] for r in records] == ["resolved-1", "resolved-2"]


def test_lease_recovery_preserves_the_interrupted_author_attempt(tmp_path, monkeypatch):
    from types import SimpleNamespace
    from learnloop.figures.rich_attempts import RichAttempts

    rig = _Rig(tmp_path, monkeypatch, list(QUICK))
    rig.build()
    job = rig.repository.claim_next_ingest_job(worker_id="gone", now_iso="2020-01-01T00:00:00Z",
                                              lease_cutoff_iso="2019-12-31T00:00:00Z")
    attempts = RichAttempts(rig.repository, job["id"], SimpleNamespace(origin="selection"),
                            RICH.content_key_for(job["payload"]), RICH.RICH_PROMPT_VERSION)
    attempts.start(1)
    attempts.end(FR.CLAIM_FAILED, problems=1)
    attempts.start(2)
    assert rig.ingest.recover_stale_leases() == [job["id"]]
    assert rig.ingest.recover_stale_leases() == []
    assert _attempts(rig) == [(FR.CLAIM_FAILED, "discarded"), (FR.INTERRUPTED, "failed")]

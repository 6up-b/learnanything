"""Follow-ups batch 6 (D): the prefetch pass retries prebuilds' plan waits itself (RW5d P5 F17).

A hidden rich-only prebuild that met the ChatGPT plan's limit was asked again only by the
Reader's figure reads of its source. After a quick re-failure the per-job pacing
(``rich.PLAN_WAIT_RETRY_SECONDS``) refused the next retry, the Reader stopped reading, and the
background retry was lost (landing ruling R2, recorded open). Each prefetch pass now asks the
plan again for every such job, bounded, paced the same way, under the background guards.

Fakes only: the judge, the authors, the renderer and the power reader are injected.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime

import numpy as np
import pytest

from learnloop.ai.errors import AIProviderUnavailable
from learnloop.figures import power as P
from learnloop.figures import prefetch as PF
from learnloop.figures import rich as RICH
from learnloop.figures import service as FS
from learnloop.vault.loader import load_vault
from tests import rich_fixtures as RF
from tests.figure_fixtures import EXTRACTION, call, set_config
from tests.test_figure_rich_job import WHY
from tests.test_figure_rich_rpc import _ctx
from tests.test_figures_prefetch import JudgeFake, decisions, env_for, seed_wait


@pytest.fixture(autouse=True)
def mains(monkeypatch):
    P.set_power_reader(lambda: P.PowerState(True, P.MAINS, "test"))
    monkeypatch.setattr(RICH, "_LAST_REQUEUE", {})
    yield
    P.set_power_reader(None)


RICH_ONLY = ("rich", "manim", RF.brief(), WHY)


def _rig(tmp_path, monkeypatch, rich_answers, *, author_answers=(RICH_ONLY,)):
    """A desktop context running its prefetch passes inline, a rich-only prebuild on the menu."""

    paths, repository, ctx, author, rich_author = _ctx(tmp_path, monkeypatch, list(author_answers), rich_answers)
    set_config(paths, "figures", price_per_million=2.0)
    seed_wait(repository)
    ctx.figure_prefetch_inline = True
    ctx.figure_prefetch_judge_client = JudgeFake()
    ctx.figure_prefetch_pause_reader = lambda: None
    ctx.figure_prefetch_rng = np.random.default_rng(0)
    return paths, repository, ctx, rich_author


def _pass(ctx, ref: str, span: str = "p3"):
    from learnloop_sidecar import prefetch_runtime as RT

    assert RT.notify(ctx, "offer", ref, blocks=[(EXTRACTION, span)])
    return ctx.figure_prefetch.results[-1]


def _prebuild_jobs(repository):
    return [job for job in repository.ingest_jobs_by_types(["figure_rich"])
            if (job.get("payload") or {}).get("build_mode") == "prefetch"]


def _waiting(job) -> bool:
    return job["status"] == "failed" and (job.get("error") or {}).get("code") == RICH.WAITING_FOR_PLAN


def _due_now(job_id: str) -> None:
    """The per-job interval has passed since the last retry (no sleep)."""

    RICH._LAST_REQUEUE[job_id] -= RICH.PLAN_WAIT_RETRY_SECONDS + 1


def test_a_plan_wait_the_reader_stopped_retrying_is_retried_by_the_next_pass(tmp_path, monkeypatch):
    unavailable = AIProviderUnavailable("usage limit reached")
    _paths, repository, ctx, rich_author = _rig(tmp_path, monkeypatch,
                                                [unavailable, unavailable, RF.scene_output()])
    first = _pass(ctx, "tutor:q1")
    (job,) = _prebuild_jobs(repository)
    assert _waiting(job) and rich_author.calls == 1
    assert first.plan_wait_retries == []  # a build of this pass is not asked again at once
    # The Reader reads its source: one retry, which meets the limit again (a quick re-failure).
    call(ctx, "reader.figures", {"extractionId": EXTRACTION})
    assert rich_author.calls == 2 and _waiting(_prebuild_jobs(repository)[0])
    # Its next read is inside the interval: nothing. Then the Reader stops reading.
    call(ctx, "reader.figures", {"extractionId": EXTRACTION})
    assert rich_author.calls == 2
    # Later, with no Reader line visible or polled, any prefetch pass asks the plan again.
    _due_now(job["id"])
    later = _pass(ctx, "tutor:q2")  # the same passage: no new decision, only the retry
    assert later.plan_wait_retries == [job["id"]] and later.decisions == []
    (done,) = _prebuild_jobs(repository)
    assert done["status"] == "completed" and rich_author.calls == 3
    # Nothing is left waiting: the next pass asks nothing.
    assert _pass(ctx, "tutor:q3").plan_wait_retries == [] and rich_author.calls == 3


def test_the_pass_and_the_reader_share_one_pacing(tmp_path, monkeypatch):
    unavailable = AIProviderUnavailable("usage limit reached")
    _paths, repository, ctx, rich_author = _rig(tmp_path, monkeypatch, [unavailable] * 3 + [RF.scene_output()])
    _pass(ctx, "tutor:q1")
    (job,) = _prebuild_jobs(repository)
    assert _pass(ctx, "tutor:q2").plan_wait_retries == [job["id"]] and rich_author.calls == 2
    # Inside the interval neither another pass nor a Reader read asks again.
    assert _pass(ctx, "tutor:q3").plan_wait_retries == []
    call(ctx, "reader.figures", {"extractionId": EXTRACTION})
    assert rich_author.calls == 2
    _due_now(job["id"])
    call(ctx, "reader.figures", {"extractionId": EXTRACTION})  # the read's retry now
    assert rich_author.calls == 3
    assert _pass(ctx, "tutor:q4").plan_wait_retries == []  # and the pass waits its interval again


# ---------------------------------------------------------------------------
# The guards, through the pass's own function (a recording requeue)
# ---------------------------------------------------------------------------

def _waiting_prebuild(tmp_path, monkeypatch):
    unavailable = AIProviderUnavailable("usage limit reached")
    paths, repository, ctx, rich_author = _rig(tmp_path, monkeypatch, [unavailable, RF.scene_output()])
    _pass(ctx, "tutor:q1")
    (job,) = _prebuild_jobs(repository)
    assert _waiting(job)
    return paths, repository, ctx, job


def _env(paths, repository, retried, **kwargs):
    return env_for(load_vault(paths.root), repository, retry_plan_wait=lambda job_id: retried.append(job_id) or True,
                   **kwargs)


def test_the_pass_retries_only_on_mains_with_the_switch_on_and_the_plan_not_paused(tmp_path, monkeypatch):
    paths, repository, _ctx_, job = _waiting_prebuild(tmp_path, monkeypatch)
    retried: list[str] = []
    P.set_power_reader(lambda: P.PowerState(False, P.BATTERY, "test"))
    PF.run_trigger(_env(paths, repository, retried), PF.Trigger("offer", "tutor:q5", blocks=((EXTRACTION, "p3"),)))
    assert retried == []
    P.set_power_reader(lambda: P.PowerState(True, P.MAINS, "test"))
    paused = {"at": datetime.now(UTC).isoformat()}
    PF.run_trigger(_env(paths, repository, retried, pause_reader=lambda: paused),
                   PF.Trigger("offer", "tutor:q6", blocks=((EXTRACTION, "p3"),)))
    assert retried == []
    PF.run_trigger(_env(paths, repository, retried), PF.Trigger("offer", "tutor:q7", blocks=((EXTRACTION, "p3"),)))
    assert retried == [job["id"]]
    # Switched off as configured now (the pass's snapshot still says on): nothing.
    retried.clear()
    env = _env(paths, repository, retried)
    RF.configure(paths, prefetch_enabled=False)
    result = PF.PassResult("ok", "offer")
    PF.retry_plan_waits(replace(env, live_vault=lambda: load_vault(paths.root)), result)
    assert retried == [] and result.plan_wait_retries == []


def test_a_held_out_passage_or_a_closed_decision_is_not_retried(tmp_path, monkeypatch):
    paths, repository, _ctx_, job = _waiting_prebuild(tmp_path, monkeypatch)
    retried: list[str] = []
    real = FS.withheld_message
    monkeypatch.setattr(FS, "withheld_message",
                        lambda v, r, e, found: "held out" if "p3" in set(found) else real(v, r, e, found))
    PF.retry_plan_waits(_env(paths, repository, retried), PF.PassResult("ok", "offer"))
    assert retried == []
    monkeypatch.setattr(FS, "withheld_message", real)
    (row,) = [row for row in decisions(repository) if row["request_id"]]
    with repository.connection() as connection:
        connection.execute("UPDATE figure_prefetch_decisions SET outcome = 'neither', outcome_at = ? WHERE id = ?",
                           ("2026-11-02T00:00:00+00:00", row["id"]))
        connection.commit()
    PF.retry_plan_waits(_env(paths, repository, retried), PF.PassResult("ok", "offer"))
    assert retried == []  # its horizon closed: no longer ahead of need


def test_a_pass_retries_at_most_the_daily_build_cap(tmp_path, monkeypatch):
    paths, repository, _ctx_, job = _waiting_prebuild(tmp_path, monkeypatch)
    set_config(paths, "figures.prefetch", max_daily_builds=1)
    monkeypatch.setattr(FS, "prefetch_plan_waits", lambda vault, repo, extraction_id, request_ids=None:
                        [job["id"], "job_two", "job_three"] if extraction_id is None else [])
    retried: list[str] = []
    PF.retry_plan_waits(_env(paths, repository, retried), PF.PassResult("ok", "offer"))
    assert retried == [job["id"]]


def test_with_no_requeue_seam_the_pass_retries_nothing(tmp_path, monkeypatch):
    paths, repository, _ctx_, _job = _waiting_prebuild(tmp_path, monkeypatch)
    result = PF.PassResult("ok", "offer")
    PF.retry_plan_waits(env_for(load_vault(paths.root), repository), result)
    assert result.plan_wait_retries == []


def test_the_runtime_wires_the_paced_requeue(tmp_path, monkeypatch):
    from learnloop_sidecar import prefetch_runtime as RT

    paths, repository, ctx, job = _waiting_prebuild(tmp_path, monkeypatch)
    requeued: list[str] = []
    monkeypatch.setattr(ctx.ingest_jobs, "retry_figure_rich",
                        lambda job_id, **kwargs: requeued.append(job_id) or True)
    env = RT.environment(ctx, None)
    assert env.retry_plan_wait(job["id"]) is True and requeued == [job["id"]]
    assert env.retry_plan_wait(job["id"]) is False and requeued == [job["id"]]  # paced
    assert FS.prefetch_plan_waits(load_vault(paths.root), repository, None) == [job["id"]]

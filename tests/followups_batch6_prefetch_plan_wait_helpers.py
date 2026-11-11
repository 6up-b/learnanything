"""What other test files use from ``tests/test_followups_batch6_prefetch_plan_wait.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

import numpy as np

from learnloop.figures import rich as RICH
from learnloop.vault.loader import load_vault

from tests import rich_fixtures as RF
from tests.figure_fixtures import EXTRACTION, set_config
from tests.figure_rich_job_helpers import WHY
from tests.figure_rich_rpc_helpers import _ctx
from tests.figures_prefetch_helpers import JudgeFake, env_for, seed_wait


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

    assert RT.notify(ctx, "offer", ref, blocks=[(EXTRACTION, span)], learner_activity=True)
    return ctx.figure_prefetch.results[-1]


def _prebuild_jobs(repository):
    return [job for job in repository.ingest_jobs_by_types(["figure_rich"])
            if (job.get("payload") or {}).get("build_mode") == "prefetch"]


def _waiting(job) -> bool:
    return job["status"] == "failed" and (job.get("error") or {}).get("code") == RICH.WAITING_FOR_PLAN


def _due_now(job_id: str) -> None:
    """The per-job interval has passed since the last retry (no sleep)."""

    RICH._LAST_REQUEUE[job_id] -= RICH.PLAN_WAIT_RETRY_SECONDS + 1


def _env(paths, repository, retried, **kwargs):
    return env_for(load_vault(paths.root), repository, retry_plan_wait=lambda job_id: retried.append(job_id) or True,
                   **kwargs)

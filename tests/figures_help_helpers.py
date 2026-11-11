"""What other test files use from ``tests/test_figures_help.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

import sqlite3
from contextlib import closing
from typing import Any

from learnloop.source_retrieval.find_sources import SourceHits
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.registry import METHOD_REGISTRY

from tests.figure_fixtures import AuthorFake
from tests.hint_fakes import ITEM, WORK, assists, hint_vault


CONFIG = '[hints]\nchoice_policy = "argmax"\n[figures]\nsketch_enabled = false\nrich_tiers_enabled = false\n'
SELF_GRADE = {"criterionPoints": {"cdf": 2, "value": 0}, "confidence": 3}
GOAL = "show how the area under 2x grows as the cut point moves"


def neutral_spec() -> dict[str, Any]:
    """A figure whose words share nothing with the CDF item's key (the
    existing overlap check reads them; a shared token writes a reveal)."""

    from learnloop.figures.help import _TEXT_KEYS
    from tests import figure_corpus as FC

    def words(value: Any, keyed: bool = False) -> Any:
        if isinstance(value, str):
            return "zebra stripes" if keyed else value
        if isinstance(value, dict):
            return {key: item if key == "choices" else words(item, keyed or key in _TEXT_KEYS)
                    for key, item in value.items()}
        if isinstance(value, list):
            return [words(item, keyed) for item in value]
        return value

    return words(FC.linear_map_spec())


class FindFake:
    """The grounding retrieval: nothing verified (an illustration, not from the books)."""

    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def __call__(self, vault: Any, repository: Any, query: str, **kwargs: Any) -> SourceHits:
        self.calls.append({"query": query, **kwargs})
        return SourceHits(intent="explain", policy="assisted_practice", status="ok", manifest={}, hits=[])


def _call(ctx: Any, name: str, params: dict[str, Any]) -> dict[str, Any]:
    spec = METHOD_REGISTRY[name]
    return spec.handler(ctx, spec.params_model.model_validate(params))


def _sidecar(tmp_path, *, author: AuthorFake | None = None, help_on: bool = True):
    paths = hint_vault(tmp_path, config=CONFIG + ("" if help_on else "help_kind_enabled = false\n"))
    ctx = SidecarContext()
    ctx.load(paths.root)
    ctx.grading_provider_override = "manual"
    ctx.hints_inline = True
    ctx.hint_seed = "e"
    ctx.library_ask_inline = True
    ctx.post_attempt_worker.autostart = False
    ctx.figure_author_client = author or AuthorFake([neutral_spec() for _ in range(8)])
    ctx.figure_find_sources = FindFake()
    session = _call(ctx, "start_session", {"energy": "medium"})["sessionId"]
    return paths, ctx, session


def _host(session: str, key: str = "k1") -> dict[str, Any]:
    return {"itemId": ITEM, "submissionId": key, "sessionId": session}


def _show_me(ctx: Any, host: dict[str, Any], goal: str = GOAL, **params: Any) -> dict[str, Any]:
    job = _call(ctx, "figure.request", {"goalText": goal, "origin": "ask", "hostRef": host, **params})
    if job["state"] == "pending":
        kept = ctx.figure_jobs.get(job["jobId"])
        assert kept is not None and kept.done.wait(60)
        job = _call(ctx, "reader.figure_job", {"jobId": job["jobId"]})
    assert job["state"] == "done", job
    return job


def _submit(ctx: Any, session: str, *, key: str = "k1", hints: int = 0) -> dict[str, Any]:
    return _call(ctx, "submit_attempt", {
        "sessionId": session, "practiceItemId": ITEM, "answerMd": WORK, "attemptType": "independent_attempt",
        "hintsUsed": hints, "selfGrade": SELF_GRADE, "submissionId": key})


def _attempt(paths: Any, attempt_id: str) -> dict[str, Any]:
    with closing(sqlite3.connect(paths.sqlite_path)) as connection:
        connection.row_factory = sqlite3.Row
        return dict(connection.execute("SELECT * FROM practice_attempts WHERE id = ?", (attempt_id,)).fetchone())


def _figure_rows(paths: Any) -> list[dict[str, Any]]:
    return [row for row in assists(paths.sqlite_path) if row["assist_kind"] == "figure"]


def _requests(paths: Any) -> list[dict[str, Any]]:
    with closing(sqlite3.connect(paths.sqlite_path)) as connection:
        connection.row_factory = sqlite3.Row
        return [dict(row) for row in connection.execute("SELECT * FROM figure_requests ORDER BY created_at, id")]


def _offer(figure_id: str = "fig_offered") -> dict[str, Any]:
    return {"figure_id": figure_id, "label": "a figure to explore", "goal_text": "vary the cut point",
            "kind": "illustrative", "tier": "grammar"}

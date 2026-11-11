"""What other test files use from ``tests/test_figures_show_me.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from typing import Any

from learnloop.source_retrieval.find_sources import SourceHits

from tests.figure_fixtures import (
    EXTRACTION,
    AuthorFake,
    build,
    build_figure_vault,
    call,
    context,
    flagship,
    rows,
    set_config,
)


READING_AT = {"extractionId": EXTRACTION, "spanId": "p2"}
GOAL = "show how the mass left of zero moves as p changes"


class FindFake:
    """The grounding retrieval: records every call, answers with ``hits`` (keys) and ``status``."""

    def __init__(self, hits: list[tuple[str, str]] | None = None, *, status: str = "ok",
                 fail: BaseException | None = None) -> None:
        self.hits = list(hits or [])
        self.status = status
        self.fail = fail
        self.calls: list[dict[str, Any]] = []

    def __call__(self, vault: Any, repository: Any, query: str, **kwargs: Any) -> SourceHits:
        self.calls.append({"query": query, **kwargs})
        if self.fail is not None:
            raise self.fail
        return SourceHits(intent="explain", policy="reading", status=self.status, manifest={"query_hash": "q"},
                          hits=[{"extraction_id": e, "span_id": s, "source_title": f"Book {e}", "section": "§1",
                                 "page": 1, "text": "..."} for e, s in self.hits])


def _vault(tmp_path):
    return build_figure_vault(tmp_path / "vault")


def _ctx(paths, *, author=None, find=None):
    ctx = context(paths.root, author=author or AuthorFake())
    if find is not None:
        ctx.figure_find_sources = find
    return ctx


def show_me(ctx, goal: str = GOAL, **params: Any) -> dict[str, Any]:
    return build(ctx, {"goalText": goal, "readingAt": READING_AT, "origin": "show_me", **params},
                 rpc="figure.request")


def _requests(repository) -> list[dict[str, Any]]:
    return rows(repository, "figure_requests")


def _tutor_ask(tmp_path, monkeypatch, *, figure_goal: str | None, show_me: bool = True):
    import learnloop_sidecar.handlers.reader as reader_handler
    from tests.reader_tutor_fakes import KeepContaining, LookupTutor, Ready

    paths, repository = _vault(tmp_path)
    if not show_me:
        set_config(paths, "figures", show_me_enabled=False)
    tutor = LookupTutor(answer_md="P(X <= 0) = p, whatever lambda is.", cite=lambda _c: [(EXTRACTION, "p6")])
    tutor.figure_goal = figure_goal
    author = AuthorFake([flagship(kind="illustrative")])
    find = FindFake([("ext_book", "s2")])
    ctx = _ctx(paths, author=author, find=find)
    ctx.reader_tutor_rerank_client = KeepContaining("whatever")
    monkeypatch.setattr(reader_handler, "ready_tutor_qa_provider", lambda vault: ("fake", Ready(), tutor))
    answer = call(ctx, "reader.ask", {"extractionId": EXTRACTION, "spanId": "p6", "question": "why is it p?",
                                      "selectionSpanIds": ["p6"], "selectionQuote": "P(X <= 0) = p"})
    return paths, repository, ctx, tutor, author, find, answer

"""What other test files use from ``tests/test_figure_rich_rpc.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from learnloop.content.pipeline.runner import RunnerServices

from tests import rich_fixtures as RF
from tests.figure_fixtures import AuthorFake, build_figure_vault, context
from tests.figure_fixtures import set_config


def _ctx(tmp_path, monkeypatch, author_answers=(), rich_answers=None, *, opt_in="standing", rich=True,
         foreground=True):
    paths, repository = build_figure_vault(tmp_path / "vault", rich=rich)
    if opt_in is not None:
        set_config(paths, "figures", manim_opt_in=opt_in)
    RF.ready_manim(monkeypatch)
    author = AuthorFake(list(author_answers))
    ctx = context(paths.root, author=author)
    rich_author = RF.RichAuthorFake(rich_answers)
    services = RunnerServices(figure_rich_client_factory=lambda job: rich_author, figure_rich_renderer=RF.Renders(),
                              figure_function_runner=RF.InProcessRunner())
    ctx.ingest_jobs.bind(ctx.repository, ctx.vault_root, services=services, background=False)
    if not foreground:
        monkeypatch.setattr(ctx.ingest_jobs, "_ensure_worker", lambda: None)
    return paths, repository, ctx, author, rich_author

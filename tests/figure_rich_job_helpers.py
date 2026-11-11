"""What other test files use from ``tests/test_figure_rich_job.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from learnloop.content.pipeline.runner import IngestRunner, JobSpec, RunnerServices
from learnloop.figures import service as FS
from learnloop.vault.loader import load_vault

from tests import rich_fixtures as RF
from tests.figure_fixtures import EXTRACTION, AuthorFake, build_figure_vault, rows, set_config


WHY = "a narrated video shows the spiral tighten as b grows"


class _Rig:
    def __init__(self, tmp_path, monkeypatch, author_answers, rich_answers=None, *, renders=None,
                 opt_in="standing", sketch=False):
        self.paths, self.repository = build_figure_vault(tmp_path / "vault", sketch=sketch, rich=True)
        set_config(self.paths, "figures", manim_opt_in=opt_in)
        RF.ready_manim(monkeypatch)
        self.author = AuthorFake(author_answers)
        self.rich_author = RF.RichAuthorFake(rich_answers)
        self.renders = renders or RF.Renders()
        self.functions = RF.InProcessRunner()
        self.ingest = IngestRunner(self.repository, vault_root=self.paths.root, worker_id="w1", services=RunnerServices(
            figure_rich_client_factory=lambda ctx: self.rich_author, figure_rich_renderer=self.renders,
            figure_function_runner=self.functions))
        self.batches: list[str] = []

    @property
    def vault(self):
        return load_vault(self.paths.root)

    def spawn(self, payload):
        batch = self.ingest.enqueue_batch("figure_rich", [JobSpec("figure_rich", payload)])
        self.batches.append(batch)
        return self.ingest.repo.ingest_jobs_for_batch(batch)[0]["id"]

    def build(self, request=None):
        request = request or FS.FigureRequest(extraction_id=EXTRACTION, span_ids=["p3"])
        return FS.build_figure(self.vault, self.repository, request, author_client=self.author, spawn_rich=self.spawn)

    def listed(self):
        return FS.list_figures(self.vault, self.repository, EXTRACTION)

    def job(self):
        return self.ingest.repo.ingest_jobs_for_batch(self.batches[-1])[0]


def _ledger(repository, task):
    return [row for row in rows(repository, "judgment_ledger") if row["task"] == task]

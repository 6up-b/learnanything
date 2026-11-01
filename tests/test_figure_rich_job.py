"""RW5d P2b: the rich job and progressive delivery, through the figure service and the durable queue
(spec_reader_show_me_figures_v1 §6.8, §8.6, §9b.3; G-SM21, G-SM22, G-SM26).

* A rich status with a quick figure: the quick one is shown at once with
  its fuller line pending; the rich job (on the ingest queue) writes, checks,
  renders and stores the Manim figure under it: one figure line, two
  versions. A failed or cancelled rich job leaves the quick one.
* With no quick figure: the pending line, the same input never asks again
  while it builds, and the rich figure lists on its own once stored.
* The job calls the concept pipeline as a library (validator, pacing lint,
  render_scene with the capped scope, the media store); its second attempt
  carries code's words (a failed claim, the pacing lint, render stderr).
* A restart never wedges a row; without a grant the job waits for the plan
  and makes no offer; a withdrawn opt-in or switch stops it with nothing
  stored; held-out material is refused before the rich call.

Fakes only: the authors, the renderer and the function runner are injected;
no model, Manim or bubblewrap runs.
"""

from __future__ import annotations

import pytest

from learnloop.ai.errors import AIProviderUnavailable
from learnloop.content.pipeline.runner import IngestRunner, JobSpec, RunnerServices
from learnloop.figures import rich as RICH
from learnloop.figures import service as FS
from learnloop.vault.loader import load_vault
from learnloop.vault.paths import animation_video_path
from tests import rich_fixtures as RF
from tests.figure_fixtures import EXTRACTION, AuthorFake, build_figure_vault, flagship, rows, set_config

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


def test_the_quick_figure_shows_first_and_the_fuller_one_lands_under_it(tmp_path, monkeypatch):
    """G-SM21: the quick figure before the rich job runs; then one line, two versions."""

    rig = _Rig(tmp_path, monkeypatch, [("rich", "manim", RF.brief(), WHY, flagship(kind="illustrative"))])
    outcome = rig.build()
    quick = outcome.view
    assert quick["verification"] == "illustrative" and quick["tier"] == "grammar"
    assert quick["fuller"]["state"] == "pending" and quick["fuller"]["phase"] == "writing"
    assert quick["fuller"]["richJobId" if "richJobId" in quick["fuller"] else "rich_job_id"]
    assert rig.rich_author.calls == 0  # the quick figure never waits for the rich one
    assert rig.author.calls == 1

    rig.ingest.drain()
    assert rig.job()["status"] == "completed", rig.job()
    (line,) = rig.listed()  # one figure line
    assert line["figure_id"] == quick["figure_id"] and line["fuller"]["state"] == "ready"
    rich = line["fuller"]["figure"]
    assert rich["tier"] == "manim" and rich["verification"] == "illustrative"
    assert rich["label"] == RICH.MANIM_LABEL == "AI-made video · not checked against the book"
    assert rich["spec_json"] is None or "scene_code" not in (rich["spec_json"] or "")
    manim = rich["manim"]
    assert manim["title"] == "Why the trajectory spirals" and "complex" in manim["narration_md"]
    assert [check["kind"] for check in manim["checks"]] == ["equals", "invariant"]
    assert manim["checks"][0]["plotted"] is True and manim["not_covered"] == [RICH.MANIM_NOT_COVERED]
    assert manim["not_checkable"][0]["function"] == "helper_uses_manim"
    assert animation_video_path(rig.paths.root, "sha256:" + manim["media_file_name"][len("sha256-"):-4]).is_file()
    stored = rows(rig.repository, "interactive_figures")
    assert len(stored) == 2 and stored[1]["fuller_of_id"] == stored[0]["id"] and stored[1]["tier"] == "manim"
    assert stored[1]["spec_version"] == "manim-fig-v1" and "manim" in stored[1]["runtime_digest"]
    assert stored[1]["input_hash"] == stored[0]["input_hash"]
    (tier,) = _ledger(rig.repository, "figure_tier")
    assert tier["verdict"] == "manim" and tier["rationale"] == WHY and tier["left_id"] == stored[0]["id"]
    assert len(_ledger(rig.repository, "figure_verified")) == 2

    # The rich author got what the figure author saw, plus the brief.
    context = rig.rich_author.contexts[0]
    assert context["brief"]["brief"].startswith("Animate x(t)") and context["passage"][0]["span_id"] == "p3"
    assert "scene_scaffold" in context and "problems_with_the_last_attempt" not in context
    # The concept pipeline's renderer, with the capped scope and its settings.
    (render,) = rig.renders.calls
    assert render["scene_class"] == "SpiralExplainer" and render["wrapper"]
    assert render["wrapper"][0].endswith("prlimit") and render["quality"] == "qm"
    # The declared functions ran without manim (the stand-in asserts it).
    assert len(rig.functions.sources) == 1 and "def x(t, a, b)" in rig.functions.sources[0]


def test_a_failed_rich_job_leaves_the_quick_figure_and_says_why(tmp_path, monkeypatch):
    wrong = RF.scene_output(declared={**RF.DECLARED, "claims": [
        {"kind": "equals", "function": "x", "expr": "exp(a*t)*sin(b*t)"}]})
    rig = _Rig(tmp_path, monkeypatch, [("rich", "manim", RF.brief(), WHY, flagship(kind="illustrative"))],
               [wrong, wrong])
    quick = rig.build().view
    rig.ingest.drain()
    (line,) = rig.listed()
    assert line["figure_id"] == quick["figure_id"] and line["verification"] == "illustrative"
    assert line["fuller"]["state"] == "failed" and "sin(b*t)" in line["fuller"]["reason"]
    assert rig.rich_author.calls == 2 and rig.renders.calls == []
    problems = rig.rich_author.contexts[1]["problems_with_the_last_attempt"]
    assert any("but exp(a*t)*sin(b*t)" in problem for problem in problems)
    rich = rows(rig.repository, "interactive_figures")[1]
    assert rich["verification"] == "failed" and rich["spec_json"] is None


def test_a_cancelled_rich_job_leaves_the_quick_figure(tmp_path, monkeypatch):
    rig = _Rig(tmp_path, monkeypatch, [("rich", "manim", RF.brief(), WHY, flagship(kind="illustrative"))])
    quick = rig.build().view
    rig.ingest.cancel_batch(rig.batches[-1])
    rig.ingest.drain()
    (line,) = rig.listed()
    assert line["figure_id"] == quick["figure_id"] and line["fuller"]["state"] == "cancelled"
    assert rig.rich_author.calls == 0 and len(rows(rig.repository, "interactive_figures")) == 1


def test_rich_only_shows_the_pending_line_and_never_asks_twice(tmp_path, monkeypatch):
    rig = _Rig(tmp_path, monkeypatch, [("rich", "manim", RF.brief(), WHY)])
    outcome = rig.build()
    assert outcome.view is None and outcome.rich["state"] == "pending"
    assert outcome.rich["anchor_span_id"] == "p3" and outcome.rich["tier"] == "manim"
    (pending,) = FS.rich_pending(rig.vault, rig.repository, EXTRACTION)
    assert pending["request_id"] == outcome.rich["request_id"] and pending["phase"] == "writing"
    assert rig.listed() == []
    again = rig.build()
    assert again.view is None and again.rich["rich_job_id"] == outcome.rich["rich_job_id"]
    assert rig.author.calls == 1  # the same input: its pending line, no second call

    rig.ingest.drain()
    assert FS.rich_pending(rig.vault, rig.repository, EXTRACTION) == []
    (line,) = rig.listed()
    assert line["tier"] == "manim" and line["verification"] == "illustrative" and line["fuller"] is None
    assert line["anchor_span_id"] == "p3"
    (asked, second) = rows(rig.repository, "figure_requests")
    assert asked["figure_id"] == line["figure_id"]
    # The tier receipt is the request's (Codex review F10), which names the figure.
    (tier,) = _ledger(rig.repository, "figure_tier")
    assert tier["left_kind"] == "figure_request" and tier["left_id"] == asked["id"] and tier["verdict"] == "manim"
    # A later request reuses the stored animation with no call.
    reused = rig.build()
    assert reused.reused and reused.view["figure_id"] == line["figure_id"] and rig.author.calls == 1


def test_the_pacing_repair_is_the_second_attempt_and_a_worse_repair_renders_the_first(tmp_path, monkeypatch):
    short = RF.scene_output(scene=RF.SCENE.replace("        for _ in range(8):\n            self.wait(4)\n", ""))
    invalid = RF.scene_output(scene="import os\n" + RF.SCENE)
    rig = _Rig(tmp_path, monkeypatch, [("rich", "manim", RF.brief(), WHY, flagship(kind="illustrative"))],
               [short, invalid])
    rig.build()
    rig.ingest.drain()
    assert rig.rich_author.calls == 2
    assert any("below the" in problem for problem in rig.rich_author.contexts[1]["problems_with_the_last_attempt"])
    (render,) = rig.renders.calls
    assert "self.wait(4)" not in render["scene_code"]  # the valid, short first scene
    assert rig.listed()[0]["fuller"]["state"] == "ready"


def test_a_render_failure_gets_one_repair_with_the_stderr(tmp_path, monkeypatch):
    renders = RF.Renders([RF.failed_render()])
    rig = _Rig(tmp_path, monkeypatch, [("rich", "manim", RF.brief(), WHY, flagship(kind="illustrative"))],
               renders=renders)
    rig.build()
    rig.ingest.drain()
    assert rig.rich_author.calls == 2 and len(renders.calls) == 2
    assert any("Cirle" in problem for problem in rig.rich_author.contexts[1]["problems_with_the_last_attempt"])
    assert rig.listed()[0]["fuller"]["state"] == "ready"


def test_a_restart_never_wedges_a_row(tmp_path, monkeypatch):
    """G-SM22: a rich job running when LearnLoop stopped is recovered as
    interrupted; no rich row exists in any unfinished state, and the line says so."""

    rig = _Rig(tmp_path, monkeypatch, [("rich", "manim", RF.brief(), WHY, flagship(kind="illustrative"))])
    quick = rig.build().view
    job = rig.job()
    with rig.repository.connection() as connection:
        connection.execute("UPDATE ingest_jobs SET status = 'running', worker_id = 'dead', attempt_count = 1, "
                           "heartbeat_at = '2000-01-01T00:00:00Z', started_at = '2000-01-01T00:00:00Z' WHERE id = ?",
                           (job["id"],))
        connection.commit()
    restarted = IngestRunner(rig.repository, vault_root=rig.paths.root, worker_id="w2")
    restarted.recover_stale_leases()
    assert rig.ingest.repo.get_ingest_job(job["id"])["status"] == "failed"
    (line,) = rig.listed()
    assert line["figure_id"] == quick["figure_id"]
    assert line["fuller"]["state"] == "failed" and "interrupted" in line["fuller"]["reason"]
    assert len(rows(rig.repository, "interactive_figures")) == 1 and rig.rich_author.calls == 0


def test_without_a_grant_a_plan_down_job_waits_and_asks_nothing(tmp_path, monkeypatch):
    from learnloop.ai import plan_fallback

    rig = _Rig(tmp_path, monkeypatch, [("rich", "manim", RF.brief(), WHY, flagship(kind="illustrative"))],
               [AIProviderUnavailable("usage limit reached"), RF.scene_output()])
    rig.build()
    batch = rig.batches[-1]
    assert plan_fallback.batch_origin(batch) is None and plan_fallback.batch_grant(batch) is None
    rig.ingest.drain()
    job = rig.job()
    assert job["status"] == "failed" and job["error"]["code"] == RICH.WAITING_FOR_PLAN
    assert job["error"]["retryable"] is True
    assert rig.listed()[0]["fuller"]["state"] == "waiting_for_plan"
    with plan_fallback._GRANTS_LOCK:
        assert batch not in plan_fallback._BATCH_OFFERS  # no offer kept for any read to show
    assert len(rows(rig.repository, "interactive_figures")) == 1
    # The plan back: the read's retry requeues it and it lands.
    assert rig.ingest.requeue_failed_unless_cancelled(batch, error_code=RICH.WAITING_FOR_PLAN)
    rig.ingest.drain()
    assert rig.listed()[0]["fuller"]["state"] == "ready"


@pytest.mark.parametrize("change", [{"manim_opt_in": "declined"}, {"rich_tiers_enabled": False}])
def test_a_withdrawn_opt_in_or_switch_stops_the_job_with_nothing_stored(tmp_path, monkeypatch, change):
    rig = _Rig(tmp_path, monkeypatch, [("rich", "manim", RF.brief(), WHY, flagship(kind="illustrative"))])
    rig.build()
    RF.configure(rig.paths, **change)
    rig.ingest.drain()
    assert rig.job()["status"] == "failed" and rig.job()["error"]["code"] == "rich_disabled"
    assert rig.rich_author.calls == 0 and len(rows(rig.repository, "interactive_figures")) == 1


def test_held_out_material_is_refused_before_the_rich_call(tmp_path, monkeypatch):
    from tests.test_figures_codex_review import _hold_out

    rig = _Rig(tmp_path, monkeypatch, [("rich", "manim", RF.brief(), WHY, flagship(kind="illustrative"))])
    rig.build()
    _hold_out(monkeypatch, "p2")  # a neighbour the author was sent
    rig.ingest.drain()
    assert rig.job()["error"]["code"] == "exam_material" and rig.rich_author.calls == 0


def test_a_provider_that_cannot_isolate_the_turn_is_refused_before_any_request(tmp_path, monkeypatch):
    class Leaky(RF.RichAuthorFake):
        def supports(self, capability):
            from learnloop.ai.transport import ISOLATED_TURN

            return capability != ISOLATED_TURN and super().supports(capability)

    rig = _Rig(tmp_path, monkeypatch, [("rich", "manim", RF.brief(), WHY, flagship(kind="illustrative"))])
    rig.rich_author = Leaky()
    rig.build()
    rig.ingest.drain()
    assert rig.job()["error"]["code"] == "not_isolated" and rig.rich_author.calls == 0


def test_rich_off_a_stored_animation_lists_as_cant_show_this_kind_here(tmp_path, monkeypatch):
    rig = _Rig(tmp_path, monkeypatch, [("rich", "manim", RF.brief(), WHY)])
    rig.build()
    rig.ingest.drain()
    RF.configure(rig.paths, rich_tiers_enabled=False)
    (line,) = rig.listed()
    assert line["verification"] == "unsupported" and line["label"] == "can't show this kind here"
    assert line["spec_json"] is None and "manim" not in line and "fuller" not in line and "tier" not in line


def test_rich_off_a_quick_figure_shows_without_its_fuller_line(tmp_path, monkeypatch):
    rig = _Rig(tmp_path, monkeypatch, [("rich", "manim", RF.brief(), WHY, flagship(kind="illustrative"))])
    quick = rig.build().view
    rig.ingest.drain()
    RF.configure(rig.paths, rich_tiers_enabled=False)
    (line,) = rig.listed()
    assert line["figure_id"] == quick["figure_id"] and line["verification"] == "illustrative"
    assert "fuller" not in line and "manim" not in line


def test_a_bad_brief_gets_the_second_attempt(tmp_path, monkeypatch):
    rig = _Rig(tmp_path, monkeypatch, [("rich", "manim", {"tier": "manim", "brief": ""}, WHY),
                                       flagship(kind="illustrative")])
    outcome = rig.build()
    assert rig.author.calls == 2 and outcome.view["tier"] == "grammar"
    assert any("rich.brief is empty" in problem
               for problem in rig.author.contexts[1]["problems_with_the_last_attempt"])


def test_a_failing_quick_figure_is_dropped_and_the_rich_half_carries_on(tmp_path, monkeypatch):
    rig = _Rig(tmp_path, monkeypatch, [("rich", "manim", RF.brief(), WHY, {"spec_version": "nope"})])
    outcome = rig.build()
    assert outcome.view is None and outcome.rich["state"] == "pending"
    assert rig.job()["payload"]["quick_dropped"]


def test_the_report_shows_the_rich_tier_rows(tmp_path, monkeypatch):
    from learnloop.reader.reader_report import build_reader_report

    rig = _Rig(tmp_path, monkeypatch, [("rich", "manim", RF.brief(), WHY, flagship(kind="illustrative"))])
    rig.build()
    rig.ingest.drain()
    report = build_reader_report(rig.repository.sqlite_path, figures_enabled=True, figure_rich_enabled=True)
    rich = report["figures"]["tiers"]["rich"]
    assert rich["built"] == {"manim": {"illustrative": 1}} and rich["followed_a_quick_figure"] == 1
    assert rich["build_seconds_p50"]["manim"] is not None
    assert rich["why_this_tier"] == {"manim": [{"reason": WHY, "n": 1}]}
    assert report["figures"]["tiers"]["verdicts"] == {"manim": 1}
    assert {"fuller_opened", "quick_opened", "cancelled"} <= set(rich)
    off = build_reader_report(rig.repository.sqlite_path, figures_enabled=True)
    assert "tiers" not in off["figures"]

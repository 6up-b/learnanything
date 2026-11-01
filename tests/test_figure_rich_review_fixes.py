"""RW5d P2b, the Manim half: the Codex review's job and service findings, each reproduced first.

* F6: a cancel pressed while the render runs is noticed before anything is
  stored or asked again, and a cancel raised inside the render repair is
  never stored as an honest failure.
* F7: "try again" after a stored rich-only failure starts a new generation:
  the author and then the rich author are asked afresh (their prompts, and so
  their paid checkpoints, differ), while a crash rerun keeps the generation.
* F8: the rich job's intent commits with the quick figure; a stop (or a
  failed enqueue) between the two is recovered by the next read, never
  twice, and never for a build that was cancelled.
* F9: a rich-only build that ended with no row (interrupted) stays as a
  failed line with its reason, and can be tried again (the same job).
* F10: a rich-only build's ``figure_tier`` receipt is appended against its
  request when the author's choice is accepted (once), whatever the job does.
* F11: "not right?" on an animation goes to the rich author with the note
  and the earlier program; the new version supersedes the old (kept); "try a
  different kind of figure" re-runs the tier choice instead.

Fakes only: the authors, the renderer and the function runner are injected;
no model, Manim or bubblewrap runs.
"""

from __future__ import annotations

import pytest

from learnloop.content.pipeline.runner import IngestRunner
from learnloop.db.stores import figures as store
from learnloop.figures import rich as RICH
from learnloop.figures import service as FS
from tests import rich_fixtures as RF
from tests.figure_fixtures import EXTRACTION, flagship, rows
from tests.test_figure_rich_job import WHY, _ledger, _Rig


def _quick_answer():
    return ("rich", "manim", RF.brief(), WHY, flagship(kind="illustrative"))


def _base(rig, figure_id):
    with rig.repository.connection() as connection:
        return store.figure(connection, figure_id)


def _interrupt(rig, job_id):
    with rig.repository.connection() as connection:
        connection.execute("UPDATE ingest_jobs SET status = 'running', worker_id = 'dead', attempt_count = 1, "
                           "heartbeat_at = '2000-01-01T00:00:00Z', started_at = '2000-01-01T00:00:00Z' WHERE id = ?",
                           (job_id,))
        connection.commit()
    IngestRunner(rig.repository, vault_root=rig.paths.root, worker_id="w2").recover_stale_leases()


# --- F6 -----------------------------------------------------------------------


def test_a_cancel_during_the_render_stores_nothing(tmp_path, monkeypatch):
    """F6: before the fix the rendered figure was stored after the cancel (its job ended cancelled)."""

    class CancellingRenders(RF.Renders):
        def __call__(self, scene_code, scene_class, **kwargs):
            rig.ingest.cancel_batch(rig.batches[-1])  # the learner presses cancel while it renders
            return super().__call__(scene_code, scene_class, **kwargs)

    rig = _Rig(tmp_path, monkeypatch, [_quick_answer()], renders=None)
    rig.renders = CancellingRenders()
    rig.ingest.services.figure_rich_renderer = rig.renders
    quick = rig.build().view
    rig.ingest.drain()
    assert len(rig.renders.calls) == 1
    assert rig.job()["status"] == "cancelled"
    assert len(rows(rig.repository, "interactive_figures")) == 1  # only the quick figure
    (line,) = rig.listed()
    assert line["figure_id"] == quick["figure_id"] and line["fuller"]["state"] == "cancelled"


def test_a_cancel_during_a_failed_render_never_asks_for_the_repair(tmp_path, monkeypatch):
    class CancellingRenders(RF.Renders):
        def __call__(self, scene_code, scene_class, **kwargs):
            rig.ingest.cancel_batch(rig.batches[-1])
            return super().__call__(scene_code, scene_class, **kwargs)

    rig = _Rig(tmp_path, monkeypatch, [_quick_answer()])
    rig.renders = CancellingRenders([RF.failed_render()])
    rig.ingest.services.figure_rich_renderer = rig.renders
    rig.build()
    rig.ingest.drain()
    assert rig.rich_author.calls == 1 and rig.job()["status"] == "cancelled"
    assert len(rows(rig.repository, "interactive_figures")) == 1


def test_a_cancel_raised_inside_the_render_repair_propagates(tmp_path, monkeypatch):
    """F6: _repair_render's broad handler used to store a JobCancelled as an honest failure."""

    class Cancelled(Exception):
        pass

    rig = _Rig(tmp_path, monkeypatch, [_quick_answer()], [RF.scene_output(), Cancelled("cancelled")],
               renders=RF.Renders([RF.failed_render()]))
    rig.build()
    payload = rig.job()["payload"]
    with pytest.raises(Cancelled):
        RICH.run_rich_job(rig.vault, rig.repository, payload, client=rig.rich_author, renderer=rig.renders,
                          function_runner=rig.functions, cancellation=(Cancelled,))
    assert len(rows(rig.repository, "interactive_figures")) == 1


# --- F7 -----------------------------------------------------------------------


def test_try_again_after_a_stored_rich_failure_asks_afresh(tmp_path, monkeypatch):
    """F7: the retry generation counted only grammar/sketch rows, and the rich
    prompt dropped the request identity, so "try again" recovered the failed answer."""

    wrong = RF.scene_output(declared={**RF.DECLARED, "claims": [
        {"kind": "equals", "function": "x", "expr": "exp(a*t)*sin(b*t)"}]})
    rig = _Rig(tmp_path, monkeypatch, [("rich", "manim", RF.brief(), WHY), ("rich", "manim", RF.brief(), WHY)],
               [wrong, wrong, RF.scene_output()])
    rig.build()
    rig.ingest.drain()
    (failed,) = rig.listed()
    assert failed["verification"] == "failed" and failed["tier"] == "manim"
    first_context = rig.rich_author.contexts[0]

    again = rig.build()  # "try again"
    assert again.view is None and again.rich["state"] == "pending"
    assert rig.author.calls == 2  # the author is asked afresh (generation 1)
    assert rig.job()["payload"]["generation"] == 1
    rig.ingest.drain()
    second_context = rig.rich_author.contexts[2]
    assert first_context["request_id"] != second_context["request_id"]
    assert rig.rich_author.prompts[0] != rig.rich_author.prompts[2]
    shown = [line for line in rig.listed() if line["verification"] == "illustrative"]
    assert shown and shown[0]["tier"] == "manim"


def test_a_crash_rerun_keeps_the_generation_and_the_rich_prompt(tmp_path, monkeypatch):
    rig = _Rig(tmp_path, monkeypatch, [_quick_answer()])
    rig.build()
    payload = rig.job()["payload"]
    assert payload["author_context"]["request_id"]
    first = RICH.rich_prompt(RICH.rich_context(rig.vault, payload["author_context"], payload["brief"], ()))
    again = RICH.rich_prompt(RICH.rich_context(rig.vault, payload["author_context"], payload["brief"], ()))
    assert first == again  # the requeued job's rich prompt (and checkpoint) are the same


# --- F8 -----------------------------------------------------------------------


def test_a_stop_between_the_quick_figure_and_the_enqueue_is_recovered_once(tmp_path, monkeypatch):
    """F8: the quick figure committed and the process stopped before the
    enqueue: before the fix the animation was lost with no line."""

    monkeypatch.setattr(FS._RichSpawn, "after_quick", lambda self, *args, **kwargs: None)  # the stop
    rig = _Rig(tmp_path, monkeypatch, [_quick_answer()])
    quick = rig.build().view
    assert rig.batches == []
    intent = rows(rig.repository, "interactive_figures")[0]
    assert '"rich_intent"' in intent["verification_report_json"]
    (line,) = rig.listed()
    assert line["fuller"]["state"] == "pending" and line["fuller"]["rich_job_id"] is None

    assert FS.resume_rich_intents(rig.vault, rig.repository, EXTRACTION, rig.spawn) == 1
    assert FS.resume_rich_intents(rig.vault, rig.repository, EXTRACTION, rig.spawn) == 0  # never twice
    assert len(rig.batches) == 1 and rig.job()["payload"]["fast_figure_id"] == quick["figure_id"]
    rig.ingest.drain()
    (line,) = rig.listed()
    assert line["fuller"]["state"] == "ready"
    assert FS.resume_rich_intents(rig.vault, rig.repository, EXTRACTION, rig.spawn) == 0


def test_a_failed_enqueue_is_not_swallowed_and_is_recovered(tmp_path, monkeypatch, caplog):
    rig = _Rig(tmp_path, monkeypatch, [_quick_answer()])

    def broken(payload):
        raise RuntimeError("queue busy")

    vault = rig.vault
    outcome = FS.build_figure(vault, rig.repository, FS.FigureRequest(extraction_id=EXTRACTION, span_ids=["p3"]),
                              author_client=rig.author, spawn_rich=broken)
    assert outcome.view["verification"] == "illustrative"
    assert any("could not start the rich job" in record.getMessage() for record in caplog.records)
    assert outcome.view["fuller"]["state"] == "pending"
    assert FS.resume_rich_intents(rig.vault, rig.repository, EXTRACTION, rig.spawn) == 1


def test_a_normal_build_or_a_cancelled_one_is_never_restarted_by_recovery(tmp_path, monkeypatch):
    rig = _Rig(tmp_path, monkeypatch, [_quick_answer()])
    rig.build()
    assert FS.resume_rich_intents(rig.vault, rig.repository, EXTRACTION, rig.spawn) == 0
    rig.ingest.cancel_batch(rig.batches[-1])
    rig.ingest.drain()
    assert FS.resume_rich_intents(rig.vault, rig.repository, EXTRACTION, rig.spawn) == 0
    assert len(rig.batches) == 1 and rig.listed()[0]["fuller"]["state"] == "cancelled"


# --- F9 -----------------------------------------------------------------------


def test_an_interrupted_rich_only_build_stays_as_a_failed_line_and_can_be_tried_again(tmp_path, monkeypatch):
    """F9: before the fix the pending line vanished with no explanation."""

    rig = _Rig(tmp_path, monkeypatch, [("rich", "manim", RF.brief(), WHY)])
    outcome = rig.build()
    job_id = outcome.rich["rich_job_id"]
    _interrupt(rig, job_id)
    assert rig.listed() == []
    (line,) = FS.rich_pending(rig.vault, rig.repository, EXTRACTION)
    assert line["state"] == "failed" and line["rich_job_id"] == job_id
    assert line["reason"] == "interrupted when LearnLoop stopped" and line["anchor_span_id"] == "p3"

    assert FS.retry_rich_job(rig.vault, rig.repository, job_id) == "interrupted"
    assert rig.ingest.requeue_failed_unless_cancelled(rig.job()["batch_id"], error_code="interrupted")
    (line,) = FS.rich_pending(rig.vault, rig.repository, EXTRACTION)
    assert line["state"] == "pending"
    rig.ingest.drain()
    assert FS.rich_pending(rig.vault, rig.repository, EXTRACTION) == []
    (figure,) = rig.listed()
    assert figure["tier"] == "manim" and figure["verification"] == "illustrative"
    assert rig.author.calls == 1  # the same build, never a second author call


def test_a_cancelled_rich_only_build_leaves_no_line_and_cannot_be_retried(tmp_path, monkeypatch):
    rig = _Rig(tmp_path, monkeypatch, [("rich", "manim", RF.brief(), WHY)])
    outcome = rig.build()
    rig.ingest.cancel_batch(rig.batches[-1])
    rig.ingest.drain()
    assert FS.rich_pending(rig.vault, rig.repository, EXTRACTION) == []
    with pytest.raises(FS.FigureRefused) as refused:
        FS.retry_rich_job(rig.vault, rig.repository, outcome.rich["rich_job_id"])
    assert refused.value.code == "not_failed"


def test_a_stored_rich_only_failure_lists_once(tmp_path, monkeypatch):
    wrong = RF.scene_output(declared={**RF.DECLARED, "claims": [
        {"kind": "equals", "function": "x", "expr": "exp(a*t)*sin(b*t)"}]})
    rig = _Rig(tmp_path, monkeypatch, [("rich", "manim", RF.brief(), WHY)], [wrong, wrong])
    rig.build()
    rig.ingest.drain()
    assert [line["verification"] for line in rig.listed()] == ["failed"]
    assert FS.rich_pending(rig.vault, rig.repository, EXTRACTION) == []  # its row lists it, not a second line


# --- F10 ----------------------------------------------------------------------


@pytest.mark.parametrize("ending", ["completed", "cancelled", "interrupted", "waiting"])
def test_a_rich_only_tier_judgment_is_receipted_once_against_its_request(tmp_path, monkeypatch, ending):
    """F10: before the fix only _store appended it, which waiting, cancelled
    and interrupted builds never reach."""

    from learnloop.ai.errors import AIProviderUnavailable

    rich = [AIProviderUnavailable("usage limit reached")] if ending == "waiting" else None
    rig = _Rig(tmp_path, monkeypatch, [("rich", "manim", RF.brief(), WHY)], rich)
    outcome = rig.build()
    (tier,) = _ledger(rig.repository, "figure_tier")
    assert tier["left_kind"] == "figure_request" and tier["left_id"] == outcome.rich["request_id"]
    assert tier["verdict"] == "manim" and tier["rationale"] == WHY and tier["judge"] == "llm"
    if ending == "cancelled":
        rig.ingest.cancel_batch(rig.batches[-1])
    if ending == "interrupted":
        _interrupt(rig, outcome.rich["rich_job_id"])
    else:
        rig.ingest.drain()
    assert len(_ledger(rig.repository, "figure_tier")) == 1
    if ending == "completed":
        (figure,) = rig.listed()
        (asked, *_rest) = rows(rig.repository, "figure_requests")
        assert asked["id"] == tier["left_id"] and asked["figure_id"] == figure["figure_id"]


# --- F11 ----------------------------------------------------------------------


def test_not_right_on_an_animation_goes_to_the_rich_author_with_the_note_and_program(tmp_path, monkeypatch):
    """F11: before the fix the revision was refused (rich_revision_later)."""

    better = RF.scene_output(scene=RF.SCENE.replace("color=BLUE", "color=RED"))
    rig = _Rig(tmp_path, monkeypatch, [("rich", "manim", RF.brief(), WHY)], [RF.scene_output(), better])
    rig.build()
    rig.ingest.drain()
    (first,) = rig.listed()
    revision = FS.revision_request(rig.repository, _base(rig, first["figure_id"]), "the spiral should be red")
    outcome = rig.build(revision)
    assert outcome.view is None and outcome.rich["state"] == "pending" and outcome.rich["anchor_span_id"] == "p3"
    assert rig.author.calls == 1  # never back to the tier choice
    rig.ingest.drain()
    context = rig.rich_author.contexts[1]
    assert context["learner_note"] == "the spiral should be red"
    assert "color=BLUE" in context["earlier_version"]["scene_code"]
    assert context["earlier_version"]["declared_json"] and context["brief"]["brief"].startswith("Animate x(t)")
    (line,) = rig.listed()
    assert line["figure_id"] != first["figure_id"] and line["versions"] == 2
    assert line["supersedes_id"] == first["figure_id"] and line["revision_note"] == "the spiral should be red"
    assert line["tier"] == "manim" and line["verification"] == "illustrative"
    stored = {row["id"]: row for row in rows(rig.repository, "interactive_figures")}
    assert first["figure_id"] in stored  # the earlier version is kept
    assert len(_ledger(rig.repository, "figure_tier")) == 1  # a revision makes no tier choice


def test_not_right_on_a_fuller_version_stays_that_quick_figures_fuller_version(tmp_path, monkeypatch):
    rig = _Rig(tmp_path, monkeypatch, [_quick_answer()], [RF.scene_output(), RF.scene_output(
        scene=RF.SCENE.replace("color=BLUE", "color=RED"))])
    quick = rig.build().view
    rig.ingest.drain()
    (line,) = rig.listed()
    old_rich = line["fuller"]["figure"]["figure_id"]
    rig.build(FS.revision_request(rig.repository, _base(rig, old_rich), "red please"))
    rig.ingest.drain()
    (line,) = rig.listed()  # still one figure line
    assert line["figure_id"] == quick["figure_id"] and line["fuller"]["state"] == "ready"
    new_rich = line["fuller"]["figure"]["figure_id"]
    assert new_rich != old_rich
    stored = _base(rig, new_rich)
    assert stored["fuller_of_id"] == quick["figure_id"] and stored["supersedes_id"] == old_rich


def test_try_a_different_kind_of_figure_reruns_the_tier_choice_with_the_note(tmp_path, monkeypatch):
    rig = _Rig(tmp_path, monkeypatch, [("rich", "manim", RF.brief(), WHY), flagship(kind="illustrative")])
    rig.build()
    rig.ingest.drain()
    (first,) = rig.listed()
    revision = FS.revision_request(rig.repository, _base(rig, first["figure_id"]), "a static picture is enough")
    revision.different_kind = True
    outcome = rig.build(revision)
    assert rig.author.calls == 2 and rig.rich_author.calls == 1
    context = rig.author.contexts[1]
    assert context["learner_note"] == "a static picture is enough"
    earlier = context["earlier_version"]
    assert earlier["animation"]["demonstrates"] and "scene_code" not in str(earlier)
    assert outcome.view["tier"] == "grammar" and outcome.view["supersedes_id"] == first["figure_id"]


def test_a_revision_needs_the_manim_tier_on_this_computer(tmp_path, monkeypatch):
    rig = _Rig(tmp_path, monkeypatch, [("rich", "manim", RF.brief(), WHY)])
    rig.build()
    rig.ingest.drain()
    (first,) = rig.listed()
    RF.configure(rig.paths, manim_opt_in="declined")
    with pytest.raises(FS.FigureRefused) as refused:
        rig.build(FS.revision_request(rig.repository, _base(rig, first["figure_id"]), "red"))
    assert refused.value.code == "manim_unavailable"
    RF.configure(rig.paths, rich_tiers_enabled=False)
    with pytest.raises(FS.FigureRefused) as refused:
        FS.check_request(rig.vault, rig.repository,
                         FS.revision_request(rig.repository, _base(rig, first["figure_id"]), "red"))
    assert refused.value.code == "rich_disabled"

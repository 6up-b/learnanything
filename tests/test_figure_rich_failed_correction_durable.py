"""Reader follow-ups Nov 1b, item 2: RW5d P2b ruling R1 (Codex re-review F14 remainder).

A correction of an animation whose rich job stored a failure lists a failed
line under its passage (the reason, and "try again"). Before this follow-up
:func:`learnloop.figures.service.rich_pending` found such corrections only
among the rich jobs the queue's newest-500 window still returned, so once 500
newer rich jobs ran, the line vanished with no reason and no retry. Now the
failed correction is discovered from the durable figure and request rows (the
stored failure names its request; its job is found by that request over the
whole queue), whatever the window holds.

Fakes only (as ``test_figure_rich_rereview_fixes.py``): no model, Manim or
bubblewrap runs. The window is aged out by filtering the correction's job out
of :func:`learnloop.figures.rich.rich_jobs` (what 500 newer rich jobs do).
"""

from __future__ import annotations

from learnloop.figures import rich as RICH
from learnloop.figures import service as FS
from tests import rich_fixtures as RF
from tests.figure_fixtures import EXTRACTION, flagship
from tests.test_figure_rich_job import WHY, _Rig
from tests.test_figure_rich_rereview_fixes import WRONG, _first_animation, _revision


def _age_out(monkeypatch, *job_ids):
    real = RICH.rich_jobs
    gone = set(job_ids)
    monkeypatch.setattr(RICH, "rich_jobs", lambda repository: [job for job in real(repository)
                                                               if job["id"] not in gone])


def test_r1_a_failed_correction_outside_the_job_window_still_says_so(tmp_path, monkeypatch):
    rig = _Rig(tmp_path, monkeypatch, [("rich", "manim", RF.brief(), WHY)], [RF.scene_output(), WRONG, WRONG])
    first = _first_animation(rig)
    job_id = rig.build(_revision(rig, first["figure_id"], "red please")).rich["rich_job_id"]
    rig.ingest.drain()
    (before,) = FS.rich_pending(rig.vault, rig.repository, EXTRACTION)
    _age_out(monkeypatch, job_id)
    (line,) = FS.rich_pending(rig.vault, rig.repository, EXTRACTION)
    assert line == before
    assert line["state"] == "failed" and line["rich_job_id"] == job_id and line["reason"]
    # "Try again" still works from the line (the job is read by id over the whole queue).
    retry = FS.rich_revision_retry(rig.vault, rig.repository, job_id)
    assert retry is not None and retry.supersedes_id == first["figure_id"]


def test_r1_a_newer_correction_in_the_window_still_speaks_for_the_figure(tmp_path, monkeypatch):
    rig = _Rig(tmp_path, monkeypatch, [("rich", "manim", RF.brief(), WHY)], [RF.scene_output(), WRONG, WRONG])
    first = _first_animation(rig)
    failed_job = rig.build(_revision(rig, first["figure_id"], "red please")).rich["rich_job_id"]
    rig.ingest.drain()
    newer = rig.build(_revision(rig, first["figure_id"], "blue please"))
    _age_out(monkeypatch, failed_job)
    (line,) = FS.rich_pending(rig.vault, rig.repository, EXTRACTION)
    assert line["state"] == "pending" and line["rich_job_id"] == newer.rich["rich_job_id"]


def test_r1_a_failed_correction_of_a_fuller_version_outside_the_window_says_so_too(tmp_path, monkeypatch):
    rig = _Rig(tmp_path, monkeypatch, [("rich", "manim", RF.brief(), WHY, flagship(kind="illustrative"))],
               [RF.scene_output(), WRONG, WRONG])
    quick = rig.build().view
    rig.ingest.drain()
    (line,) = rig.listed()
    old_rich = line["fuller"]["figure"]["figure_id"]
    job_id = rig.build(_revision(rig, old_rich, "red please")).rich["rich_job_id"]
    rig.ingest.drain()
    _age_out(monkeypatch, job_id)
    (line,) = rig.listed()
    assert line["figure_id"] == quick["figure_id"] and line["fuller"]["figure"]["figure_id"] == old_rich
    (failed,) = FS.rich_pending(rig.vault, rig.repository, EXTRACTION)
    assert failed["state"] == "failed" and failed["rich_job_id"] == job_id and failed["reason"]


def test_r1_a_replaced_failed_correction_lists_nothing_outside_the_window(tmp_path, monkeypatch):
    """A failed correction replaced by a later stored version lists no line,
    from the durable rows as from the window."""

    rig = _Rig(tmp_path, monkeypatch, [("rich", "manim", RF.brief(), WHY)],
               [RF.scene_output(), WRONG, WRONG, RF.scene_output(scene=RF.SCENE.replace("color=BLUE", "color=RED"))])
    first = _first_animation(rig)
    failed_job = rig.build(_revision(rig, first["figure_id"], "red please")).rich["rich_job_id"]
    rig.ingest.drain()
    again = rig.build(_revision(rig, first["figure_id"], "blue please"))
    rig.ingest.drain()
    _age_out(monkeypatch, failed_job, again.rich["rich_job_id"])
    assert FS.rich_pending(rig.vault, rig.repository, EXTRACTION) == []


def test_codex_f4_a_newer_cancelled_correction_still_speaks_for_the_figure_after_500_newer_rich_jobs(
        tmp_path, monkeypatch):
    """Codex review F4 (reader-followups-nov1b): correction A stores a
    failure; a later correction B of the same figure is cancelled (no row).
    B speaks for the figure, so A's failure lists no line, and it still
    doesn't once 500 newer rich jobs push both out of the queue's window (a
    real 500-job queue, not a filtered window)."""

    from learnloop.content.pipeline.runner import JobSpec

    rig = _Rig(tmp_path, monkeypatch, [("rich", "manim", RF.brief(), WHY)], [RF.scene_output(), WRONG, WRONG])
    first = _first_animation(rig)
    failed_job = rig.build(_revision(rig, first["figure_id"], "red please")).rich["rich_job_id"]
    rig.ingest.drain()
    (line,) = FS.rich_pending(rig.vault, rig.repository, EXTRACTION)
    assert line["state"] == "failed" and line["rich_job_id"] == failed_job
    cancelled_job = rig.build(_revision(rig, first["figure_id"], "blue please")).rich["rich_job_id"]
    rig.ingest.cancel_batch(rig.batches[-1])
    assert rig.repository.get_ingest_job(cancelled_job)["status"] == "cancelled"
    assert FS.rich_pending(rig.vault, rig.repository, EXTRACTION) == []

    batch = rig.ingest.enqueue_batch("figure_rich", [
        JobSpec("figure_rich", {"base": {"extraction_id": "ext_elsewhere"}, "input_hash": f"elsewhere-{index}"})
        for index in range(500)])
    with rig.repository.connection() as connection:
        connection.execute("UPDATE ingest_jobs SET created_at = '2999-01-01T00:00:00Z' WHERE batch_id = ?", (batch,))
        connection.commit()
    window = {job["id"] for job in RICH.rich_jobs(rig.repository)}
    assert len(window) == 500 and failed_job not in window and cancelled_job not in window
    assert FS.rich_pending(rig.vault, rig.repository, EXTRACTION) == []

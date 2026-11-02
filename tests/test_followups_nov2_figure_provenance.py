"""Follow-ups Nov 2 (a): figure learner-state provenance on every row.

Closes learner data-relax 2's ruling R1 remainder ("cached fuller delivery,
pre-branch rich rows, revision inheritance ... Queued follow-up: record inputs
on quick rows and reconstruct fuller views from current rows at delivery").
Exam-material protection, not privacy: a figure whose author was told about the
learner's work goes out only while nothing that state was read from is
protected now.

* A quick (grammar or sketch) figure keeps ``learner_state_inputs`` in its
  report, as rich figures do since data-relax 2; no state sent, its report is
  exactly as before.
* **Presentation-time recheck** (``row_withheld``, behind every listing and
  delivery): the figure and every figure it was made from (its earlier versions,
  a fuller version's quick figure and that figure's rich intent), read from the
  current rows (``FS.learner_state_withheld``). So a revision inherits its
  base's protection, and a fuller version stored with no record of its own is
  checked by what its job carried.
* **A kept build result is rebuilt from the current rows as it goes out**
  (``deliver_figure``): its fuller line is read again, never the one kept when
  the build finished.

Fakes only: the authors are injected; no model is reached.
"""

from __future__ import annotations

import copy
from types import SimpleNamespace

from learnloop.db.stores import figures as store
from learnloop.figures import rich as RICH
from learnloop.figures import service as FS
from learnloop.vault.loader import load_vault
from tests.figure_fixtures import EXTRACTION, AuthorFake, build, context, flagship, rows
from tests.reading_path_fixtures import call
from tests.test_learner_data_relax_2 import _history_world, _make_exam_material, _plain_vault, _rich_history_rig, \
    _rich_row, _switch_off


def _quick_row(repository) -> dict:
    (row,) = [found for found in rows(repository, "interactive_figures") if found["tier"] != "manim"]
    with repository.connection() as connection:
        return store.figure(connection, row["id"])


def _quick_world(tmp_path, monkeypatch):
    from tests.mcp_world import no_model_calls

    no_model_calls(monkeypatch)
    world = _history_world(tmp_path)
    author = AuthorFake([flagship(kind="illustrative"), flagship(kind="illustrative")])
    ctx = context(world.root, author=author)
    job = call(ctx, "reader.figure_request", {"extractionId": EXTRACTION, "spanIds": ["p3"]})
    assert job["state"] == "done", job  # inline
    return world, ctx, author, job


# ---------------------------------------------------------------------------
# Quick rows keep the record
# ---------------------------------------------------------------------------

def test_a_quick_figure_keeps_the_inputs_of_the_learner_state_it_was_written_from(tmp_path, monkeypatch):
    world, ctx, author, _job = _quick_world(tmp_path, monkeypatch)
    assert author.contexts[0]["learner_state"]["recent_answers"]
    report = _quick_row(world.repository)["verification_report"]
    inputs = report[RICH.LEARNER_STATE_INPUTS_KEY]
    assert "att_unpinned" in inputs["answers"]


def test_a_quick_figure_with_no_learner_state_keeps_its_report_as_before(tmp_path):
    paths, repository = _plain_vault(tmp_path, switch=False)
    ctx = context(paths.root, author=AuthorFake([flagship(kind="illustrative")]))
    build(ctx)
    report = _quick_row(repository)["verification_report"]
    assert RICH.LEARNER_STATE_INPUTS_KEY not in report
    assert FS.learner_state_withheld(load_vault(paths.root), repository, _quick_row(repository)) is None


# ---------------------------------------------------------------------------
# Presentation-time recheck
# ---------------------------------------------------------------------------

def test_a_quick_figure_whose_learner_inputs_became_protected_is_not_presented(tmp_path, monkeypatch):
    """R1: "Stored quick figures were never rechecked": before the fix the
    quick figure was still listed and delivered."""

    world, ctx, _author, job = _quick_world(tmp_path, monkeypatch)
    figure_id = job["result"]["figure"]["figureId"]
    vault = load_vault(world.root)
    assert not FS.figure_withheld(vault, world.repository, figure_id)
    assert [view["figure_id"] for view in FS.list_figures(vault, world.repository, EXTRACTION)] == [figure_id]
    _make_exam_material(SimpleNamespace(paths=world.paths))
    vault = load_vault(world.root)
    assert FS.figure_withheld(vault, world.repository, figure_id)
    assert FS.list_figures(vault, world.repository, EXTRACTION) == []
    # The kept build result is not delivered either.
    ctx.load(world.root)
    delivered = call(ctx, "reader.figure_job", {"jobId": job["jobId"]})["result"]
    assert delivered["figure"] is None and delivered["withheld"] is True


def test_a_revision_inherits_its_bases_learner_state_protection(tmp_path, monkeypatch):
    """R1's revision inheritance: a "not right?" version built with the switch
    off (no state of its own) is still made from its base's spec, which was
    written from the learner's state; before the fix it was presented after
    that state's inputs became protected."""

    world, ctx, author, job = _quick_world(tmp_path, monkeypatch)
    base = _quick_row(world.repository)
    _switch_off(world.paths)
    vault = load_vault(world.root)
    revision = FS.build_figure(vault, world.repository, FS.revision_request(world.repository, base, "bigger axes"),
                               author_client=AuthorFake([flagship(kind="illustrative", title="Bigger")]))
    revised_id = revision.view["figure_id"]
    with world.repository.connection() as connection:
        revised = store.figure(connection, revised_id)
    assert revised["supersedes_id"] == base["id"]
    assert RICH.LEARNER_STATE_INPUTS_KEY not in revised["verification_report"]  # no state of its own
    assert not FS.figure_withheld(vault, world.repository, revised_id)
    _make_exam_material(SimpleNamespace(paths=world.paths))
    vault = load_vault(world.root)
    assert FS.row_withheld(vault, world.repository, revised) is not None
    assert FS.figure_withheld(vault, world.repository, revised_id)


def test_a_fuller_version_with_no_record_of_its_own_is_checked_by_its_jobs_payload(tmp_path, monkeypatch):
    """R1's pre-branch rich rows: a fuller version stored with no inputs record
    (before rich rows kept one) is checked through its quick figure's rich
    intent (the job's payload). Before the fix it went out unchecked."""

    rig = _rich_history_rig(tmp_path, monkeypatch)
    rig.build()
    rig.ingest.drain()
    rich = _rich_row(rig.repository)
    report = dict(rich["verification_report"])
    report.pop(RICH.LEARNER_STATE_INPUTS_KEY)
    unrecorded = {**rich, "verification_report": report}
    assert FS.row_withheld(rig.vault, rig.repository, unrecorded) is None
    _make_exam_material(rig)
    assert FS.row_withheld(rig.vault, rig.repository, unrecorded) is not None


# ---------------------------------------------------------------------------
# A kept result goes out as the current rows say
# ---------------------------------------------------------------------------

def test_a_kept_build_results_fuller_line_is_read_again_from_the_current_rows(tmp_path, monkeypatch):
    """R1's cached fuller delivery: the job result kept since the build named
    the fuller version as it was then (pending); delivered later it is read
    again (ready now)."""

    from learnloop_sidecar.handlers import figures as handlers

    rig = _rich_history_rig(tmp_path, monkeypatch)
    outcome = rig.build()
    kept = {"figure": outcome.view, "reused": outcome.reused}
    assert kept["figure"]["fuller"]["state"] == "pending"
    rig.ingest.drain()
    ctx = context(rig.paths.root)
    delivered = handlers.deliver_figure(ctx, copy.deepcopy(kept))
    assert delivered["figure"]["fuller"]["state"] == "ready"
    assert delivered["figure"]["fuller"]["figure"]["figure_id"] == _rich_row(rig.repository)["id"]
    # Everything else in the view is the kept one.
    assert {key: value for key, value in delivered["figure"].items() if key != "fuller"} == {
        key: value for key, value in kept["figure"].items() if key != "fuller"}


def test_a_kept_result_naming_a_ready_fuller_version_is_not_delivered_once_its_inputs_are_protected(
        tmp_path, monkeypatch):
    from learnloop_sidecar.handlers import figures as handlers

    rig = _rich_history_rig(tmp_path, monkeypatch)
    rig.build()
    rig.ingest.drain()
    (view,) = rig.listed()
    kept = {"figure": view, "reused": True}
    assert kept["figure"]["fuller"]["state"] == "ready"
    _make_exam_material(rig)
    delivered = handlers.deliver_figure(context(rig.paths.root), copy.deepcopy(kept))
    assert delivered["figure"] is None and delivered["withheld"] is True


def test_with_the_rich_tiers_off_a_kept_view_goes_out_exactly_as_kept(tmp_path, monkeypatch):
    world, ctx, _author, job = _quick_world(tmp_path, monkeypatch)
    assert "fuller" not in job["result"]["figure"]
    assert call(ctx, "reader.figure_job", {"jobId": job["jobId"]})["result"] == job["result"]

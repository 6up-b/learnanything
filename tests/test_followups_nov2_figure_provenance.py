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


# ---------------------------------------------------------------------------
# Codex review F3: a marked row with no record fails closed
# ---------------------------------------------------------------------------

def _strip_record(repository, figure_id: str) -> None:
    """The row as a quick figure built before quick rows kept the record."""

    with repository.connection() as connection:
        connection.execute("UPDATE interactive_figures SET verification_report_json = "
                           "json_remove(verification_report_json, '$.learner_state_inputs') WHERE id = ?",
                           (figure_id,))
        connection.commit()


def test_a_marked_quick_figure_with_no_record_is_withheld(tmp_path, monkeypatch):
    """F3: before the fix a ``+learner-v1`` quick row with no record and no rich
    intent was listed and delivered whatever its inputs had become."""

    world, ctx, _author, job = _quick_world(tmp_path, monkeypatch)
    figure_id = job["result"]["figure"]["figureId"]
    _strip_record(world.repository, figure_id)
    row = _quick_row(world.repository)
    assert "+learner-v1" in row["prompt_version"] and RICH.LEARNER_STATE_INPUTS_KEY not in row["verification_report"]
    vault = load_vault(world.root)
    assert FS.learner_state_withheld(vault, world.repository, row) == FS.LEARNER_STATE_UNRECORDED
    assert FS.figure_withheld(vault, world.repository, figure_id)
    assert FS.list_figures(vault, world.repository, EXTRACTION) == []


def test_an_unmarked_quick_figure_with_no_record_keeps_the_no_learner_state_reading(tmp_path):
    """F3: a row whose prompt version carries no ``+learner-v1`` was sent no
    learner state; with no record it has nothing to check, as before."""

    paths, repository = _plain_vault(tmp_path, switch=False)
    ctx = context(paths.root, author=AuthorFake([flagship(kind="illustrative")]))
    build(ctx)
    row = _quick_row(repository)
    assert "+learner-v1" not in row["prompt_version"]
    vault = load_vault(paths.root)
    assert FS.learner_state_withheld(vault, repository, row) is None
    assert not FS.figure_withheld(vault, repository, row["id"])


def test_a_press_of_the_same_input_records_the_marked_rows_dependencies(tmp_path, monkeypatch):
    """F3, "unless dependencies can be established": the press's own read of
    the learner state matches the row's (the input hash names the state's
    hash), so it records what that read came from on the row; the figure goes
    out again, with no author call, and is withheld once those are protected."""

    world, ctx, author, job = _quick_world(tmp_path, monkeypatch)
    figure_id = job["result"]["figure"]["figureId"]
    recorded = _quick_row(world.repository)["verification_report"][RICH.LEARNER_STATE_INPUTS_KEY]
    _strip_record(world.repository, figure_id)
    calls = author.calls
    again = call(ctx, "reader.figure_request", {"extractionId": EXTRACTION, "spanIds": ["p3"]})
    assert again["state"] == "done" and again["result"]["figure"]["figureId"] == figure_id, again
    assert author.calls == calls  # reused, never rebuilt
    assert _quick_row(world.repository)["verification_report"][RICH.LEARNER_STATE_INPUTS_KEY] == recorded
    vault = load_vault(world.root)
    assert not FS.figure_withheld(vault, world.repository, figure_id)
    _make_exam_material(SimpleNamespace(paths=world.paths))
    assert FS.figure_withheld(load_vault(world.root), world.repository, figure_id)


# ---------------------------------------------------------------------------
# Codex review F4: a queued rich revision checks what it inherits
# ---------------------------------------------------------------------------

def _rich_revision_queued(tmp_path, monkeypatch):
    """A rich figure written from the learner's state, then "not right?" on it
    queued with the switch off (the revision sends no state of its own)."""

    from tests import rich_fixtures as RF

    rig = _rich_history_rig(tmp_path, monkeypatch)
    rig.rich_author = RF.RichAuthorFake([RF.scene_output(), RF.scene_output(
        scene=RF.SCENE.replace("color=BLUE", "color=RED"))])
    rig.build()
    rig.ingest.drain()
    rich = _rich_row(rig.repository)
    assert rich["verification_report"][RICH.LEARNER_STATE_INPUTS_KEY]
    _switch_off(rig.paths)
    outcome = rig.build(FS.revision_request(rig.repository, rich, "red please"))
    assert outcome.rich["state"] == "pending"
    payload = rig.job()["payload"]
    assert "learner_state" not in payload["author_context"]  # nothing of its own
    assert payload[RICH.INHERITED_LEARNER_INPUTS_KEY]
    return rig


def test_a_queued_rich_revision_never_sends_a_program_whose_learner_inputs_became_protected(tmp_path, monkeypatch):
    """F4: before the fix the queued revision checked only its own (absent)
    learner state and sent the earlier program to the rich author."""

    rig = _rich_revision_queued(tmp_path, monkeypatch)
    _make_exam_material(rig)
    rig.ingest.drain()
    job = rig.job()
    assert rig.rich_author.calls == 1  # only the first version's
    assert job["status"] == "failed" and job["error"]["code"] == "exam_material", job
    assert len([row for row in rows(rig.repository, "interactive_figures") if row["tier"] == "manim"]) == 1


def test_a_queued_rich_revision_stops_when_an_inherited_input_becomes_protected_while_it_runs(tmp_path, monkeypatch):
    """F4: the inherited inputs are the gate's hold too (before the store)."""

    from tests import rich_fixtures as RF

    rig = _rich_revision_queued(tmp_path, monkeypatch)

    class ProtectingRenders(RF.Renders):
        def __call__(self, scene_code, scene_class, **kwargs):
            _make_exam_material(rig)
            return super().__call__(scene_code, scene_class, **kwargs)

    from learnloop.content.pipeline.runner import IngestRunner, RunnerServices

    rig.renders = ProtectingRenders()
    rig.ingest = IngestRunner(rig.repository, vault_root=rig.paths.root, worker_id="w2", services=RunnerServices(
        figure_rich_client_factory=lambda ctx: rig.rich_author, figure_rich_renderer=rig.renders,
        figure_function_runner=rig.functions))
    rig.ingest.drain()
    job = rig.job()
    assert job["status"] == "failed" and job["error"]["code"] == "exam_material", job
    assert len([row for row in rows(rig.repository, "interactive_figures") if row["tier"] == "manim"]) == 1


def test_a_rich_revision_with_nothing_inherited_carries_no_record(tmp_path, monkeypatch):
    """F4's switch-off pin: no earlier version was written from a learner state,
    so the revision's payload is exactly as before (no key)."""

    from tests import rich_fixtures as RF
    from tests.test_figure_rich_job import WHY, _Rig

    rig = _Rig(tmp_path, monkeypatch, [("rich", "manim", RF.brief(), WHY)], [RF.scene_output(), RF.scene_output()])
    rig.build()
    rig.ingest.drain()
    (first,) = rig.listed()
    with rig.repository.connection() as connection:
        base = store.figure(connection, first["figure_id"])
    rig.build(FS.revision_request(rig.repository, base, "red"))
    assert RICH.INHERITED_LEARNER_INPUTS_KEY not in rig.job()["payload"]

"""Follow-ups Nov 2 (c): curriculum C5's retraction kind ``unlinked``.

Closes C5's ruling R2 ("Hiding a link after its note was read leaves existing
tier-2 gap rows (append-only); a retraction kind needs another FK-safe rebuild
and is queued as a follow-up"). Migration 235 widens
``learner_text_gap_reversals.reversal`` with ``unlinked``; when a note's
snapshot is no longer linked (the learner hid the link, or it is unlinked
otherwise), each gap read from it gets one ``unlinked`` reversal, written by
the gap pipeline (``jobs.retract_unlinked_notes``), and every reader that
leaves out a reversed gap leaves it out. The gap row stays (append-only).
Switched off (the opt-in, the notes, tend), nothing is read and nothing is
written. Fakes only: C2's fake ``tend`` over synthetic notes; no model.
"""

from __future__ import annotations

import json

from learnloop.diagnosis.text_gaps import jobs as J
from learnloop.learner_context import learning_context
from learnloop.tutor.ai_contracts import LearnerGap
from learnloop.vault.loader import load_vault
from tests.reading_path_fixtures import call
from tests.test_notes_as_learner_text import CLOCK, PlanGapFake, _clients, _gaps, _linked, _run, _snapshots
from tests.text_gap_fakes import word_match


def _reversals(repository) -> list[dict]:
    with repository.connection() as connection:
        return [dict(row) for row in connection.execute(
            "SELECT * FROM learner_text_gap_reversals ORDER BY created_at, id")]


def _read_both(paths, repository) -> dict[str, dict]:
    """Both linked notes read: a matched prerequisite (lo_det) from each."""

    snapshots = _snapshots(repository)
    llm = PlanGapFake(reading=LearnerGap(kind="prerequisite", prerequisite_name="the determinant of a matrix",
                                         prerequisite_line="Uses det(A - lI) without knowing determinants."),
                      decide=word_match("determinant"))
    for heading in ("Eigen stuff", "Eigen page"):
        outcome = _run(paths, repository, _clients(llm), source=("learner_note", snapshots[heading]))
        assert outcome.state == "done" and outcome.action == "matched_prerequisite", outcome
    return {heading: next(gap for gap in _gaps(repository) if gap["source_id"] == snapshots[heading])
            for heading in ("Eigen stuff", "Eigen page")}


def _open_gap_ids(paths, repository) -> set[str]:
    context = learning_context(load_vault(paths.root), repository, learning_object_ids=["lo_det", "lo_eigen"])
    return {gap["gap_id"] for gap in context["open_learner_text_gaps"]}


def test_hiding_a_read_notes_link_sets_its_gaps_aside_and_only_its_own(tmp_path, monkeypatch):
    """C5 R2: before the fix the hidden note's gap stayed open in every reader."""

    paths, repository, ctx, goal_id, fake_tend, lines = _linked(tmp_path, monkeypatch)
    gaps = _read_both(paths, repository)
    typed, page = gaps["Eigen stuff"], gaps["Eigen page"]
    assert _open_gap_ids(paths, repository) >= {typed["id"], page["id"]}
    line = next(line for line in lines if line["note"]["heading"] == "Eigen stuff")
    call(ctx, "notes.decide", {"link_id": line["linkId"], "choice": "hide"})
    [reversal] = _reversals(repository)
    assert (reversal["gap_id"], reversal["reversal"], reversal["actor"]) == (typed["id"], "unlinked", "learner")
    assert json.loads(reversal["detail_json"])["note_id"] == typed["source_id"]
    open_now = _open_gap_ids(paths, repository)
    assert typed["id"] not in open_now and page["id"] in open_now
    # The gap row itself is kept (append-only), unchanged.
    assert next(gap for gap in _gaps(repository) if gap["id"] == typed["id"]) == typed
    # The learner's reading of it says so; nothing is offered to undo there.
    from learnloop_sidecar.handlers.learner_gaps import gap_view

    view = gap_view(load_vault(paths.root), {**typed, "named": {}, "detail": {}}, ["unlinked"])
    assert view["label"] == "Set aside: the note it came from is no longer linked"


def test_the_retraction_is_idempotent_and_keep_does_not_reopen_the_gap(tmp_path, monkeypatch):
    paths, repository, ctx, goal_id, fake_tend, lines = _linked(tmp_path, monkeypatch)
    typed = _read_both(paths, repository)["Eigen stuff"]
    line = next(line for line in lines if line["note"]["heading"] == "Eigen stuff")
    hidden = call(ctx, "notes.decide", {"link_id": line["linkId"], "choice": "hide"})
    vault = load_vault(paths.root)
    assert J.retract_unlinked_notes(vault, repository, clock=CLOCK) == 0  # once per gap
    call(ctx, "notes.decide", {"link_id": hidden["linkId"], "choice": "keep"})
    assert [row["gap_id"] for row in _reversals(repository)] == [typed["id"]]
    assert typed["id"] not in _open_gap_ids(paths, repository)


def test_a_note_changed_into_a_new_snapshot_sets_the_old_snapshots_gap_aside(tmp_path, monkeypatch):
    from pathlib import Path

    paths, repository, ctx, goal_id, fake_tend, lines = _linked(tmp_path, monkeypatch)
    typed = _read_both(paths, repository)["Eigen stuff"]
    entry = next(e for e in fake_tend.entries if e["hit"]["heading"] == "Eigen stuff")
    Path(entry["hit"]["path"]).write_text("* Eigen stuff\nEigenvalues again: Av = lv, now with a picture.\n",
                                          encoding="utf-8")
    entry["hit"].update(hash="h-new", line=1)
    fake_tend.save()
    call(ctx, "notes.path", {"goal_id": goal_id, "retry": True})
    J.enqueue_learner_notes(load_vault(paths.root), repository, clock=CLOCK)
    assert [(row["gap_id"], row["reversal"]) for row in _reversals(repository)] == [(typed["id"], "unlinked")]


def test_switched_off_nothing_is_read_and_nothing_is_set_aside(tmp_path, monkeypatch):
    """The opt-in off (or tend gone): no note row is read, so a note gap is never
    set aside because the notes cannot be seen."""

    from learnloop.diagnosis.text_gaps import sources

    paths, repository, ctx, goal_id, fake_tend, lines = _linked(tmp_path, monkeypatch)
    _read_both(paths, repository)
    vault = load_vault(paths.root)
    monkeypatch.setattr(sources, "learner_notes_enabled", lambda _vault: False)
    monkeypatch.setattr(J, "learner_notes_enabled", lambda _vault: False)

    def no_read(*_args, **_kwargs):
        raise AssertionError("a note row was read while switched off")

    monkeypatch.setattr(J, "learner_note_ids", no_read)
    assert J.retract_unlinked_notes(vault, repository, clock=CLOCK) == 0
    assert J.enqueue_learner_notes(vault, repository, clock=CLOCK) == 0
    assert _reversals(repository) == []


def test_unlinked_is_never_a_learners_manual_reversal(tmp_path, monkeypatch):
    """It is the pipeline's, not a tap: ``reverse_gap`` refuses it."""

    import pytest

    from learnloop.diagnosis.text_gaps.actions import REVERSALS, UndoError, reverse_gap

    paths, repository, ctx, goal_id, fake_tend, lines = _linked(tmp_path, monkeypatch)
    typed = _read_both(paths, repository)["Eigen stuff"]
    assert "unlinked" not in REVERSALS
    with pytest.raises(UndoError):
        reverse_gap(paths.root, repository, typed["id"], "unlinked")

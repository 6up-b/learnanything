"""Follow-ups Nov 2 (c): curriculum C5's retraction kind ``unlinked``.

Closes C5's ruling R2 ("Hiding a link after its note was read leaves existing
tier-2 gap rows (append-only); a retraction kind needs another FK-safe rebuild
and is queued as a follow-up"). Migration 235 widens
``learner_text_gap_reversals.reversal`` with ``unlinked``; when a note's
snapshot is no longer linked (the learner hid the link, or it is unlinked
otherwise), each gap read from it gets one ``unlinked`` reversal, written by
the gap pipeline (``jobs.retract_unlinked_notes``), and every reader that
leaves out a reversed gap leaves it out. The gap row stays (append-only).
Switched off (the opt-in, the notes or the pipeline), nothing is read and
nothing is written. Fakes only: C2b's vault notes (a typed Reader note and a
capture) in the deliverable vault; no model.
"""

from __future__ import annotations

import json

from learnloop.diagnosis.text_gaps import jobs as J
from learnloop.learner_context import learning_context
from learnloop.tutor.ai_contracts import LearnerGap
from learnloop.vault.loader import load_vault
from tests.reading_path_fixtures import call
from tests.notes_fixtures import edit_annotation
from tests.test_notes_as_learner_text import CAPTURED, CLOCK, TYPED, PlanGapFake, _clients, _gaps, _linked, _run, \
    _snapshots, _typed_line
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
    for heading in (TYPED, CAPTURED):
        outcome = _run(paths, repository, _clients(llm), source=("learner_note", snapshots[heading]))
        assert outcome.state == "done" and outcome.action == "matched_prerequisite", outcome
    return {heading: next(gap for gap in _gaps(repository) if gap["source_id"] == snapshots[heading])
            for heading in (TYPED, CAPTURED)}


def _open_gap_ids(paths, repository) -> set[str]:
    context = learning_context(load_vault(paths.root), repository, learning_object_ids=["lo_det", "lo_eigen"])
    return {gap["gap_id"] for gap in context["open_learner_text_gaps"]}


def test_hiding_a_read_notes_link_sets_its_gaps_aside_and_only_its_own(tmp_path, monkeypatch):
    """C5 R2: before the fix the hidden note's gap stayed open in every reader."""

    paths, repository, ctx, goal_id, corpus, lines = _linked(tmp_path, monkeypatch)
    gaps = _read_both(paths, repository)
    typed, page = gaps[TYPED], gaps[CAPTURED]
    assert _open_gap_ids(paths, repository) >= {typed["id"], page["id"]}
    line = _typed_line(lines)
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
    paths, repository, ctx, goal_id, corpus, lines = _linked(tmp_path, monkeypatch)
    typed = _read_both(paths, repository)[TYPED]
    line = _typed_line(lines)
    hidden = call(ctx, "notes.decide", {"link_id": line["linkId"], "choice": "hide"})
    vault = load_vault(paths.root)
    assert J.retract_unlinked_notes(vault, repository, clock=CLOCK) == 0  # once per gap
    call(ctx, "notes.decide", {"link_id": hidden["linkId"], "choice": "keep"})
    assert [row["gap_id"] for row in _reversals(repository)] == [typed["id"]]
    assert typed["id"] not in _open_gap_ids(paths, repository)


def test_a_note_changed_into_a_new_snapshot_sets_the_old_snapshots_gap_aside(tmp_path, monkeypatch):
    paths, repository, ctx, goal_id, corpus, lines = _linked(tmp_path, monkeypatch)
    typed = _read_both(paths, repository)[TYPED]
    edit_annotation(repository, corpus[TYPED].split(":", 1)[1], "Eigenvalues again: Av = lv, now with a picture.")
    call(ctx, "notes.path", {"goal_id": goal_id, "retry": True})
    J.enqueue_learner_notes(load_vault(paths.root), repository, clock=CLOCK)
    assert [(row["gap_id"], row["reversal"]) for row in _reversals(repository)] == [(typed["id"], "unlinked")]


def test_switched_off_nothing_is_read_and_nothing_is_set_aside(tmp_path, monkeypatch):
    """The opt-in off (or the notes switched off): no note row is read, so a note gap is never
    set aside because the notes cannot be seen."""

    from learnloop.diagnosis.text_gaps import sources

    paths, repository, ctx, goal_id, corpus, lines = _linked(tmp_path, monkeypatch)
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

    paths, repository, ctx, goal_id, corpus, lines = _linked(tmp_path, monkeypatch)
    typed = _read_both(paths, repository)[TYPED]
    assert "unlinked" not in REVERSALS
    with pytest.raises(UndoError):
        reverse_gap(paths.root, repository, typed["id"], "unlinked")


def test_a_note_linked_while_the_retraction_runs_keeps_its_gap(tmp_path, monkeypatch):
    """Codex review F2: the retraction read the linked notes, then (on another
    connection) the gap rows, then wrote. A second sidecar that linked a note and
    wrote its gap between those reads had that gap set aside for good, though its
    note was never unlinked. Now the links, the gaps, the reversals and the
    writes are one ``BEGIN IMMEDIATE`` transaction: the second sidecar's write
    waits for it, and the next sweep sees the note linked."""

    import sqlite3
    from contextlib import closing

    paths, repository, ctx, goal_id, corpus, lines = _linked(tmp_path, monkeypatch)
    page = _snapshots(repository)[CAPTURED]
    real = J.learner_note_ids
    seen: dict[str, bool] = {}

    def second_sidecar_writes_the_gap() -> bool:
        try:
            with closing(sqlite3.connect(repository.sqlite_path, timeout=0.2)) as other:
                other.execute(
                    "INSERT INTO learner_text_gaps (id, source_kind, source_id, learner_text, chooser, "
                    "context_judge, kind, named_json, action, detail_json, algorithm_version, pipeline_version, "
                    "created_at) VALUES ('ltg_b', 'learner_note', ?, '', 'context_model', 'gap_reader', "
                    "'prerequisite', '{}', 'matched_prerequisite', '{}', 'mvp-0.40', 'learner-text-gaps-v1', "
                    "'2026-10-20T09:00:00Z')", (page,))
                other.commit()
            return True
        except sqlite3.OperationalError as exc:
            assert "locked" in str(exc)
            return False

    def interleaved(vault, repo):
        ids = real(vault, repo)
        if "first" not in seen:
            # The links as they were before the second sidecar linked the page ...
            seen["first"] = True
            ids = [note_id for note_id in ids if note_id != page]
            # ... which then links it and completes its gap job.
            seen["wrote_during"] = second_sidecar_writes_the_gap()
        return ids

    monkeypatch.setattr(J, "learner_note_ids", interleaved)
    J.retract_unlinked_notes(load_vault(paths.root), repository, clock=CLOCK)
    if not seen["wrote_during"]:
        # It waited for the retraction's transaction; it writes now.
        assert second_sidecar_writes_the_gap()
    J.retract_unlinked_notes(load_vault(paths.root), repository, clock=CLOCK)
    assert [row for row in _reversals(repository) if row["gap_id"] == "ltg_b"] == []

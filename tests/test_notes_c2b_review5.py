"""Curriculum C2b, Codex review round 5 (job 20261102-004112-IbYkNL).

* F1: a note linked before its own anchor became protected material is withheld at every
  delivery boundary (the path's lines, a reading's marks, Compare's band and its take text),
  while the ledger keeps its rows.
* F2: a note's gap reading records everything it was prepared from (the annotation's own
  anchor and section header, and every block of each linked passage's section), so the
  chat's text guard withholds a text written from it once any of those becomes protected.

Every note is synthetic vault data (tests/notes_fixtures.py); every model is a fake.
"""
from __future__ import annotations

import json

from learnloop.source_retrieval import note_links as NL
from learnloop.vault.loader import load_vault
from tests.notes_fixtures import add_annotation
from tests.reading_path_fixtures import call
from tests.section_coverage_fixtures import hold_out
from tests.notes_linked_helpers import _deliverable, _lines

#: A synthetic sentinel in the note written beside Lay's eigenvector section.
LAY_SENTINEL = "LAYNOTESENTINEL-91c2"
#: Lay's eigenvector section's header (its text is the note's heading).
LAY_HEADER = "5.1 Eigenvectors and eigenvalues"


def _lay_note(repository) -> str:
    """A Reader note beside Lay's eigenvector section (ext_lay s2: unprotected until held out)."""

    return "annotation:" + add_annotation(repository, f"My own words on this. {LAY_SENTINEL}", extraction_id="ext_lay",
                                          span_id="s2", source_id="src_lay", revision_id="rev_lay")


def _shown(ctx, goal_id) -> str:
    """Everything the notes RPCs deliver for ext_book's eigenvalue passage, as one string."""

    path = call(ctx, "notes.path", {"goal_id": goal_id, "link": False})
    marks = call(ctx, "notes.marks", {"extraction_id": "ext_book"})
    band = call(ctx, "notes.passages", {"passages": [{"extraction_id": "ext_book", "span_id": "s2"}]})
    return json.dumps([_lines(path), marks["marks"], band["notes"]])


def _rows(repository) -> tuple[int, int]:
    with repository.connection() as connection:
        return (int(connection.execute("SELECT COUNT(*) FROM learner_notes").fetchone()[0]),
                int(connection.execute("SELECT COUNT(*) FROM learner_note_links").fetchone()[0]))


def test_c2b_r5_f1_a_linked_note_whose_anchor_became_protected_is_withheld_everywhere(tmp_path):
    paths, repository, ctx, goal_id, corpus, notes = _deliverable(tmp_path)
    key = _lay_note(repository)
    call(ctx, "notes.link", {"note": {"note_key": key}, "extraction_id": "ext_book", "span_id": "s2"})
    call(ctx, "notes.path", {"goal_id": goal_id})  # the model's proposals too (inline)
    before = _shown(ctx, goal_id)
    # Shown on all three surfaces, with its source-derived heading.
    assert before.count(LAY_SENTINEL) >= 3 and LAY_HEADER in before
    rows = _rows(repository)
    # The note's own section becomes protected (held out) after it was linked.
    hold_out(repository, "lay_eigen")
    after = _shown(ctx, goal_id)
    assert LAY_SENTINEL not in after and LAY_HEADER not in after and key not in after
    # The ledger keeps its history (nothing deleted; delivery withholds it).
    assert _rows(repository) == rows
    # Other notes linked beside the same passage still show.
    assert "Av = lv" in after
    vault = load_vault(paths.root)
    assert all(view["note_key"] != key for view in NL.marks(vault, repository, "ext_book")[0]["notes"])


def _lay_reading(tmp_path, monkeypatch):
    """C2's deliverable vault with the gap opt-in on, a Lay note linked by hand beside
    ext_book's eigenvalue passage, and its snapshot read for gaps (a belief named)."""

    from learnloop.tutor.ai_contracts import LearnerGap
    from tests.notes_as_learner_text_helpers import GAPS_ON, PlanGapFake, _clients, _gaps, _run

    paths, repository, ctx, goal_id, corpus, notes = _deliverable(tmp_path, config=GAPS_ON)
    ctx.post_attempt_worker.autostart = False
    key = _lay_note(repository)
    call(ctx, "notes.link", {"note": {"note_key": key}, "extraction_id": "ext_book", "span_id": "s2"})
    with repository.connection() as connection:
        (snapshot,) = [str(row[0]) for row in connection.execute(
            "SELECT id FROM learner_notes WHERE note_key = ?", (key,))]
    plan = PlanGapFake(reading=LearnerGap(kind="misconception", belief_statement="Eigenvectors can be zero"))
    outcome = _run(paths, repository, _clients(plan), source=("learner_note", snapshot))
    assert outcome.state == "done"
    (gap,) = [row for row in _gaps(repository) if row["source_id"] == snapshot]
    return paths, repository, key, snapshot, gap


def _recorded(repository, kind: str, record_id: str):
    from learnloop.learner_context import recorded_write_provenance

    with repository.connection() as connection:
        return recorded_write_provenance(connection, kind, record_id)


def _source_reason(paths, repository, record):
    from learnloop.learner_context import TextGuard

    with repository.connection() as connection:
        return TextGuard(connection, load_vault(paths.root), repository).past.source_reason(record.sources)


def test_c2b_r5_f2_a_notes_reading_records_its_anchor_heading_and_every_section_span(tmp_path, monkeypatch):
    paths, repository, key, snapshot, gap = _lay_reading(tmp_path, monkeypatch)
    vault = load_vault(paths.root)
    from learnloop.diagnosis.text_gaps.sources import learner_text
    from learnloop.source_retrieval import section_coverage as SC

    text = learner_text(vault, repository, "learner_note", snapshot)
    bound = dict(text.bound_sources)
    # The note's own anchor (Lay s2) and its heading's header block (Lay s1).
    assert {"s1", "s2"} <= set(bound["ext_lay"])
    # Every span of the linked section (ch_eigen), not only the linked span.
    reading = SC.Library(vault, repository).reading("ext_book")
    section = {span for span, owner in reading.all_spans.items() if owner == "ch_eigen"}
    assert len(section) > 1 and section <= set(bound["ext_book"])
    record = _recorded(repository, "learner_text_gap", gap["id"])
    recorded = {(ref["extraction_id"], span) for ref in record.sources for span in ref.get("span_ids") or ()}
    assert {("ext_lay", "s1"), ("ext_lay", "s2")} <= recorded
    assert {("ext_book", span) for span in section} <= recorded


def test_c2b_r5_f2_protecting_an_input_the_old_record_omitted_withholds_the_text(tmp_path, monkeypatch):
    """The negative test: the note's own section (an input the reading saw, through the note's
    heading and anchor, but the pre-fix record omitted) becomes protected after the gap and
    the belief were written; the chat's text guard now withholds both."""

    paths, repository, key, snapshot, gap = _lay_reading(tmp_path, monkeypatch)
    records = [_recorded(repository, "learner_text_gap", gap["id"])]
    with repository.connection() as connection:
        candidates = [str(row[0]) for row in connection.execute(
            "SELECT record_id FROM text_write_provenance WHERE kind = 'candidate'")]
    records += [_recorded(repository, "candidate", candidate) for candidate in candidates]
    assert candidates and all(record is not None for record in records)  # a belief candidate was named
    assert all(_source_reason(paths, repository, record) is None for record in records)  # releasable now
    hold_out(repository, "lay_eigen")
    assert all(_source_reason(paths, repository, record) is not None for record in records)


def test_c2b_r5_f2_the_note_gate_refuses_once_a_bound_source_is_protected(tmp_path, monkeypatch):
    """The request gate revalidates the prepared text's frozen sources (protection read now)."""

    from learnloop.diagnosis.text_gaps.sources import learner_note_refusal, learner_text
    from learnloop.source_retrieval import note_gaps

    paths, repository, key, snapshot, gap = _lay_reading(tmp_path, monkeypatch)
    vault = load_vault(paths.root)
    prepared = learner_text(vault, repository, "learner_note", snapshot)
    assert learner_note_refusal(vault, repository, snapshot, prepared=prepared) is None
    # Only the frozen source is protected now (the note's anchor check is bypassed).
    monkeypatch.setattr(note_gaps.VN, "beside_protected", lambda *_a, **_k: False)
    hold_out(repository, "lay_eigen")
    assert learner_note_refusal(load_vault(paths.root), repository, snapshot, prepared=prepared) == note_gaps.PROTECTED


def _reanchor(repository, key: str, *, extraction_id: str, span_id: str, source_id: str, revision_id: str) -> None:
    """The Reader note moved by hand onto another passage (a successor anchor; the old one kept)."""

    from learnloop.reader import annotations as ANN

    with repository.connection() as connection:
        block = connection.execute("SELECT text FROM source_document_blocks WHERE extraction_id = ? AND span_id = ?",
                                   (extraction_id, span_id)).fetchone()
    translation = ANN.translate_selection(repository, extraction_id=extraction_id, raw_selection={
        "nodes": [{"span_id": span_id, "quote": " ".join(str(block[0]).split()[:4])}]})
    assert translation["status"] == "exact", translation
    ANN.manual_anchor(repository, annotation_id=key.split(":", 1)[1], source_id=source_id, revision_id=revision_id,
                      extraction_id=extraction_id, segments=translation["segments"])


def test_c2b_r5_rereview_f1_a_snapshot_from_an_older_anchor_is_withheld_once_that_anchor_is_protected(tmp_path):
    """Codex re-review F1 (job 20261102-012346-6YalUi): the snapshot a note shows may carry
    text and a heading from an anchor older than its newest one. A note linked beside Lay's
    eigenvector section, then moved onto an unprotected passage, then Lay's section held
    out: the stored snapshot (Lay's heading, written there) is withheld everywhere."""

    from learnloop.source_retrieval import vault_notes as VN

    paths, repository, ctx, goal_id, corpus, notes = _deliverable(tmp_path)
    key = _lay_note(repository)
    call(ctx, "notes.link", {"note": {"note_key": key}, "extraction_id": "ext_book", "span_id": "s2"})
    call(ctx, "notes.path", {"goal_id": goal_id})  # the model's proposals too (inline)
    _reanchor(repository, key, extraction_id="ext_book", span_id="s3", source_id="src_book", revision_id="rev_book")
    before = _shown(ctx, goal_id)
    # The snapshot taken beside Lay still shows, with Lay's header as its heading (control).
    assert LAY_SENTINEL in before and LAY_HEADER in before and "Av = lv" in before
    rows = _rows(repository)
    hold_out(repository, "lay_eigen")
    vault = load_vault(paths.root)
    # The newest anchor alone is unprotected: the old check passes the note...
    assert VN.protected_keys(vault, repository, [key]) == set()
    # ...but the snapshot's own (older) anchor is protected now: withheld on every surface.
    after = _shown(ctx, goal_id)
    assert LAY_SENTINEL not in after and LAY_HEADER not in after and key not in after
    assert _rows(repository) == rows
    assert "Av = lv" in after
    assert all(view["note_key"] != key for view in NL.marks(vault, repository, "ext_book")[0]["notes"])


def test_c2b_r5_rereview_f1_a_notes_reading_refuses_a_snapshot_from_a_now_protected_older_anchor(tmp_path, monkeypatch):
    """The gap reading's own refusal reads the same history (the note's every anchor)."""

    import pytest

    from learnloop.source_retrieval import note_gaps

    paths, repository, key, snapshot, gap = _lay_reading(tmp_path, monkeypatch)
    _reanchor(repository, key, extraction_id="ext_book", span_id="s3", source_id="src_book", revision_id="rev_book")
    vault = load_vault(paths.root)
    assert note_gaps.note_text(vault, repository, snapshot) is not None  # control: nothing protected yet
    hold_out(repository, "lay_eigen")
    with pytest.raises(note_gaps.NoteWithheld):
        note_gaps.note_text(load_vault(paths.root), repository, snapshot)


def test_c2b_final_verify_f1_the_notes_guard_judges_a_candidate_by_every_anchor_it_ever_had(tmp_path):
    """Final verify F1 (job 20261102-014150-SGh5IK), landing ruling R2: a candidate prepared
    while anchored beside Lay's section (its heading Lay's header), moved onto an unprotected
    passage, then Lay's section held out before the request's admission: the composed
    guard refuses (it reads every anchor the annotation ever had, not only the newest)."""

    import pytest

    from learnloop.source_retrieval import section_coverage as SC
    from learnloop.source_retrieval import vault_notes as VN
    from tests.notes_linked_helpers import _Published, _target

    paths, repository, ctx, goal_id, corpus, notes = _deliverable(tmp_path)
    key = _lay_note(repository)
    _reanchor(repository, key, extraction_id="ext_book", span_id="s3", source_id="src_book", revision_id="rev_book")
    vault, target = _target(paths, repository, goal_id)
    keys = [(target.extraction_id, target.section_id)]

    def guard(on):
        return NL.NotesGuard(on, live_vault=_Published(on)).with_coverage(SC.Library(on, repository), keys,
                                                                          notes=[key])

    control = guard(vault)  # nothing protected yet: admitted
    control.settle(control.admit(notes, purpose="note_link_judge", prompt="p", budget=None), {})
    hold_out(repository, "lay_eigen")
    held = load_vault(paths.root)
    assert VN.protected_keys(held, repository, [key]) == set()  # the newest anchor alone passes
    with pytest.raises(NL.NotesSwitchedOff):
        guard(held).admit(notes, purpose="note_link_judge", prompt="p", budget=None)


def test_c2b_final_verify_f1_an_embedding_batch_drops_a_note_from_a_now_protected_older_anchor(tmp_path):
    """Final verify F1, landing ruling R2: the corpus read while the note sat beside Lay's
    section (Lay's header its heading), the note then moved onto an unprotected passage and
    Lay's section held out before the embedding batch: the batch drops it (nothing sent)."""

    from learnloop.source_retrieval import vault_notes as VN
    from tests.deliverable_fixtures import build_deliverable_vault
    from tests.notes_fixtures import NoteEmbeddingFake, turn_on_embeddings

    paths, repository = build_deliverable_vault(tmp_path / "vault")
    turn_on_embeddings(paths)
    key = _lay_note(repository)
    vault = load_vault(paths.root)
    corpus = VN.notes(vault, repository)
    (prepared,) = [note for note in corpus if note.note_key == key]
    assert LAY_HEADER in prepared.heading and LAY_SENTINEL in prepared.text  # control
    _reanchor(repository, key, extraction_id="ext_book", span_id="s3", source_id="src_book", revision_id="rev_book")
    hold_out(repository, "lay_eigen")
    assert VN.protected_keys(load_vault(paths.root), repository, [key]) == set()  # newest anchor alone passes
    embedder = NoteEmbeddingFake()
    report = VN.ensure_vectors(vault, corpus, client_factory=lambda: embedder, repository=repository)
    assert report["dropped"] == 1, report
    assert all(LAY_SENTINEL not in text and LAY_HEADER not in text for text in embedder.inputs)

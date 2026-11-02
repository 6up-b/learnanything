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
from tests.test_notes_linked import _deliverable, _lines

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

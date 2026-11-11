"""Follow-ups batch 7 (B): a Reader note is named by its source's title, never its ``file://`` URI.

A source with no display title is titled by its URI in ``corpus.current_extractions`` (the title
retrieval keys hash), and a Reader note took that as its title: stored in its snapshot, and shown in
Settings' hidden notes, the Reader's marks, Compare's quoted take and the note search.

Now new snapshots store the readable name, every view shows it, and a row stored with the URI is shown
the same way and not rewritten. The note's content hash still reads the source's title as before, so no
note reads as changed: no new snapshot, no new judgment, no new embedding. Synthetic vault, fakes only.
"""

from __future__ import annotations

import json
from typing import Any

import pytest

from learnloop.content.pipeline.add_source import learner_title
from learnloop.content.sources.source_outline import title_from_local_uri
from learnloop.source_retrieval import note_links as NL
from learnloop.source_retrieval import vault_notes as VN
from learnloop.vault.loader import load_vault
from tests.reading_path_fixtures import call
from tests.notes_linked_helpers import _deliverable, _link_typed_by_hand

URI = "file:///home/someone/books/linear_algebra%20done_right.pdf"
READABLE = "Linear Algebra Done Right"


def _untitle(repository: Any, *, extraction_id: str = "ext_book") -> str:
    """The book of ``extraction_id`` as an old import left it: no display title, its URI only."""

    with repository.connection() as connection:
        source_id, revision_id = connection.execute(
            "SELECT v.source_id, r.revision_id FROM source_extraction_runs r JOIN source_revisions v "
            "ON v.id = r.revision_id WHERE r.id = ?", (extraction_id,)).fetchone()
        connection.execute("UPDATE source_artifacts SET display_title = NULL WHERE id = ?", (source_id,))
        connection.execute("UPDATE source_revisions SET original_uri = ? WHERE id = ?", (URI, revision_id))
        connection.commit()
    return str(source_id)


def _hidden_note(ctx: Any, corpus: Any) -> dict[str, Any]:
    hand = _link_typed_by_hand(ctx, corpus)
    call(ctx, "notes.decide", {"link_id": hand["linkId"], "choice": "hide"})
    (entry,) = call(ctx, "notes.hidden", {})["hidden"]
    return entry


def _stored_titles(repository: Any, note_key: str) -> list[str]:
    with repository.connection() as connection:
        return [str(row[0]) for row in connection.execute(
            "SELECT title FROM learner_notes WHERE note_key = ? ORDER BY rowid", (note_key,))]


@pytest.mark.parametrize(("value", "readable"), [
    (URI, READABLE),
    ("file:///home/x/Probability.Theory.pdf", "Probability Theory"),
    ("file:///home/x/My%20Book%20(2nd%20ed).pdf", "My Book (2nd ed)"),
    ("https://example.com/paper.pdf", None),  # the web address the Library shows
    ("Linear Algebra Done Right", None),
    ("your reading", None),
    ("file:///", None),
    ("", None),
])
def test_a_local_uri_reads_as_its_file_name_in_words(value, readable):
    assert title_from_local_uri(value) == readable


def test_the_library_card_names_a_percent_encoded_file_the_same_way():
    assert learner_title({"id": "src_a"}, {"original_uri": URI}) == READABLE
    assert learner_title({"id": "src_a", "display_title": "Axler"}, {"original_uri": URI}) == "Axler"
    assert learner_title({"id": "src_a", "canonical_uri": "https://a.example/x"}, None) == "https://a.example/x"


def test_settings_hidden_notes_name_the_note_and_where_with_no_uri(tmp_path):
    _paths, repository, ctx, _goal_id, corpus, _notes = _deliverable(tmp_path)
    _untitle(repository)
    entry = _hidden_note(ctx, corpus)
    assert entry["note"]["title"] == READABLE
    assert entry["where"].startswith(READABLE)
    assert "file:" not in json.dumps(entry) and "%20" not in json.dumps(entry)


def test_every_view_of_a_new_note_names_it_and_its_snapshot_stores_the_readable_name(tmp_path):
    _paths, repository, ctx, _goal_id, corpus, _notes = _deliverable(tmp_path)
    _untitle(repository)
    typed = corpus["typed"]
    found = call(ctx, "notes.search", {"query": "eigenvalues"})
    hit = next(hit for hit in found["hits"] if hit["noteKey"] == typed)
    assert hit["title"] == READABLE
    assert "file:" not in json.dumps(found)
    # The title a learner reads finds it (its words, not the path's).
    assert typed in {one["noteKey"] for one in call(ctx, "notes.search", {"query": "done right"})["hits"]}
    out = call(ctx, "notes.link", {"note": {"note_key": typed}, "extraction_id": "ext_book", "span_id": "s2"})
    assert "file:" not in json.dumps(out)
    band = call(ctx, "notes.passages", {"passages": [{"extraction_id": "ext_book", "span_id": "s2"}]})
    assert band["notes"] and all("file:" not in note["takeText"] for note in band["notes"])
    assert _stored_titles(repository, typed) == [READABLE]


def test_a_row_stored_with_the_uri_is_shown_readable_and_stays_as_it_was(tmp_path, monkeypatch):
    paths, repository, ctx, _goal_id, corpus, _notes = _deliverable(tmp_path)
    source_id = _untitle(repository)
    typed = corpus["typed"]
    with monkeypatch.context() as earlier:  # as an earlier version wrote it (the table is append-only)
        earlier.setattr(VN.VaultNote, "display_title", property(lambda note: note.title))
        call(ctx, "notes.link", {"note": {"note_key": typed}, "extraction_id": "ext_book", "span_id": "s2"})
    assert _stored_titles(repository, typed) == [URI]
    vault = load_vault(paths.root)
    with repository.connection() as connection:
        rows = [row for row in NL.store.links(connection) if row["note_key"] == typed]
    views = NL.effective(repository, rows, vault=vault)
    assert views and {view["note"]["title"] for view in views} == {READABLE}
    assert _stored_titles(repository, typed) == [URI]  # never rewritten
    # The source's display title, once it has one, is what it is called now.
    with repository.connection() as connection:
        connection.execute("UPDATE source_artifacts SET display_title = 'Axler' WHERE id = ?", (source_id,))
        connection.commit()
    assert {view["note"]["title"] for view in NL.effective(repository, rows, vault=vault)} == {"Axler"}
    assert _stored_titles(repository, typed) == [URI]


def test_the_notes_content_hash_is_unchanged_so_nothing_reads_as_changed(tmp_path):
    paths, repository, ctx, goal_id, corpus, notes = _deliverable(tmp_path)
    _untitle(repository)
    vault = load_vault(paths.root)
    note = next(note for note in VN.notes(vault, repository) if note.note_key == corpus["typed"])
    assert note.title == URI and note.display_title == READABLE
    # The hash and the embedded text read the source's title as they always did.
    assert note.content_hash == VN.VaultNote(
        ref_kind=note.ref_kind, ref_id=note.ref_id, title=URI, heading=note.heading, text=note.text,
        truncated=note.truncated, captured_on=note.captured_on, full_text=note.full_text).content_hash
    assert VN.recipe_text(note).startswith(URI)
    call(ctx, "notes.link", {"note": {"note_key": corpus["typed"]}, "extraction_id": "ext_book", "span_id": "s2"})
    with repository.connection() as connection:
        before = connection.execute("SELECT COUNT(*), MAX(content_hash) FROM learner_notes WHERE note_key = ?",
                                    (corpus["typed"],)).fetchone()
    assert tuple(before) == (1, note.content_hash)
    # A refresh of what was linked by hand stores nothing new, and the model is not asked again.
    calls = notes.calls
    assert NL.refresh_learner_links(vault, repository) == 0
    with repository.connection() as connection:
        assert connection.execute("SELECT COUNT(*) FROM learner_notes WHERE note_key = ?",
                                  (corpus["typed"],)).fetchone()[0] == 1
    assert notes.calls == calls


def test_a_titled_source_and_a_capture_keep_their_names(tmp_path):
    _paths, repository, ctx, _goal_id, corpus, _notes = _deliverable(tmp_path)
    entry = _hidden_note(ctx, corpus)
    assert "file:" not in entry["note"]["title"] and entry["note"]["title"] != READABLE
    assert entry["note"]["title"]  # the fixture's own title, unchanged by any of this
    found = call(ctx, "notes.search", {"query": "2x2 example"})
    assert [hit["title"] for hit in found["hits"]] == [VN.CAPTURE_TITLE]

"""The same file added from another place is the book already in the library.

``add_source`` answered ``existing`` ("Already in your library — opened where
you left off.") only for the same path; the same bytes from another folder
became a second library copy with no word (retainer-3 #6, #48). The sources
already carry their bytes' hash (``source_revisions.asset_hash``): Add now
recognises it. Nothing is merged or deleted where two copies already exist.
"""

from __future__ import annotations

import learnloop_sidecar.handlers  # noqa: F401 -- populate METHOD_REGISTRY
from learnloop.content.sources.source_library import register_source_revision

from tests.ux_phase1_support import CLOCK, fresh_library, write_book, write_pdf
from tests.ux_phase1_add_source_helpers import _held_ctx, call

EXISTING = "Already in your library — opened where you left off."


def _copy(path, folder):
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / path.name
    target.write_bytes(path.read_bytes())
    return target


def test_the_same_file_from_another_folder_opens_the_book_already_there(tmp_path):
    root = fresh_library(tmp_path)
    ctx = _held_ctx(root)
    (tmp_path / "downloads").mkdir()
    pdf = write_pdf(tmp_path / "downloads")
    first = call(ctx, "add_source", {"sources": [str(pdf)]})["items"][0]
    batches = len(ctx.repository.list_ingest_batches())

    elsewhere = _copy(pdf, tmp_path / "desktop" / "papers")
    again = call(ctx, "add_source", {"sources": [str(elsewhere)]})["items"][0]

    assert again["status"] == "existing"
    assert again["sourceId"] == first["sourceId"]
    assert again["revisionId"] == first["revisionId"]
    assert again["title"] == first["title"]
    assert again["message"] == EXISTING
    assert len(ctx.repository.all_source_artifacts()) == 1
    assert len(ctx.repository.list_ingest_batches()) == batches


def test_the_same_file_under_another_name_is_recognised_too(tmp_path):
    root = fresh_library(tmp_path)
    ctx = _held_ctx(root)
    book = write_book(tmp_path, "probability_book.md")
    first = call(ctx, "add_source", {"sources": [str(book)]})["items"][0]
    renamed = tmp_path / "other" / "my copy.md"
    renamed.parent.mkdir()
    renamed.write_bytes(book.read_bytes())

    again = call(ctx, "add_source", {"sources": [str(renamed)]})["items"][0]

    assert (again["status"], again["sourceId"], again["message"]) == ("existing", first["sourceId"], EXISTING)
    assert len(ctx.repository.all_source_artifacts()) == 1


def test_a_different_file_is_still_a_new_book(tmp_path):
    root = fresh_library(tmp_path)
    ctx = _held_ctx(root)
    one = write_book(tmp_path, "one.md")
    (tmp_path / "x").mkdir()
    two = write_book(tmp_path / "x", "one.md", text="# Another book\n\nDifferent words entirely.\n")
    first = call(ctx, "add_source", {"sources": [str(one)]})["items"][0]
    second = call(ctx, "add_source", {"sources": [str(two)]})["items"][0]
    assert first["status"] == second["status"] == "added"
    assert first["sourceId"] != second["sourceId"]
    assert len(ctx.repository.all_source_artifacts()) == 2


def test_two_copies_already_in_the_library_stay_and_a_third_add_opens_the_first(tmp_path):
    """A library that already holds two sources with one hash (added before this
    was recognised): nothing is merged or deleted; Add opens the first one."""

    root = fresh_library(tmp_path)
    ctx = _held_ctx(root)
    (tmp_path / "a").mkdir()
    pdf = write_pdf(tmp_path / "a")
    copy = _copy(pdf, tmp_path / "b")
    made = []
    for path in (pdf, copy):
        registered = register_source_revision(
            ctx.repository, acquisition_kind="pdf", canonical_uri=str(path), raw_bytes=path.read_bytes(),
            original_uri=path.resolve().as_uri(), display_title="Probability", vault_root=root, clock=CLOCK,
        )
        ctx.ingest_jobs.enqueue_add_source(str(path), source_id=registered.source_id)
        made.append(registered.source_id)
    assert len(set(made)) == 2

    third = _copy(pdf, tmp_path / "c")
    again = call(ctx, "add_source", {"sources": [str(third)]})["items"][0]

    assert (again["status"], again["sourceId"], again["message"]) == ("existing", made[0], EXISTING)
    assert sorted(artifact["id"] for artifact in ctx.repository.all_source_artifacts()) == sorted(made)
    cards = [card for card in call(ctx, "get_source_library", {})["sources"] if card["sourceId"] in made]
    assert len(cards) == 2

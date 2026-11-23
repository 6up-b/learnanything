"""Carried questions and the desk drain (spec §10.12), and LearnLoop's proposals with their labels (spec §10.6),
through their RPCs: workflow data and labels, never evidence; every write idempotent by a client-minted id."""

from __future__ import annotations

from contextlib import closing
import sqlite3

import pytest

from learnloop.pads.drain import local_day
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.errors import SidecarError
from tests.desk_helpers import _ledger, seed_reading
from tests.helpers import create_basic_vault
from tests.workbench_help_fakes import call

BOOK = "ext_book"
EVIDENCE = ("practice_attempts", "learner_text_gaps", "learning_object_mastery", "facet_recall_state",
            "router_learner_preferences", "router_decisions")


@pytest.fixture
def ctx(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    context = SidecarContext()
    context.load(paths.root)
    context.post_attempt_worker.autostart = False
    context.paths = paths
    return context


def _counts(ctx):
    with closing(sqlite3.connect(ctx.paths.sqlite_path)) as connection:
        return {table: connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] for table in EVIDENCE}


def _carry(ctx, carried_id="cq_1", text="Why is the kernel a subspace?", **extra):
    return call(ctx, "carried.carry", {"carriedId": carried_id, "text": text, "originKind": "block",
                                       "originRef": "b1", **extra})


def test_carrying_is_idempotent_and_writes_one_event_and_no_evidence(ctx):
    before = _counts(ctx)
    first = _carry(ctx)
    assert first["version"] == 1 and first["created"] is True
    assert (first["carried"]["state"], first["carried"]["carried"], first["carried"]["version"]) == ("carried", True, 1)
    assert _carry(ctx)["created"] is False
    with pytest.raises(SidecarError) as refused:
        _carry(ctx, text="another question")
    assert refused.value.code == "carried_id_reused"
    with closing(sqlite3.connect(ctx.paths.sqlite_path)) as connection:
        assert connection.execute("SELECT event FROM carried_question_events").fetchall() == [("carried",)]
    assert _counts(ctx) == before


def test_three_labels_each_logged_and_a_stale_label_is_a_conflict(ctx):
    _carry(ctx)
    marked = call(ctx, "carried.mark", {"eventId": "e1", "carriedId": "cq_1", "event": "not_now", "expectedVersion": 1})
    assert (marked["applied"], marked["conflict"], marked["carried"]["state"], marked["carried"]["carried"]) == (
        True, False, "not_now", True)
    stale = call(ctx, "carried.mark", {"eventId": "e2", "carriedId": "cq_1", "event": "let_go", "expectedVersion": 1})
    assert (stale["applied"], stale["conflict"], stale["carried"]["state"]) == (False, True, "not_now")
    done = call(ctx, "carried.mark", {"eventId": "e3", "carriedId": "cq_1", "event": "fruitful", "expectedVersion": 2})
    assert (done["carried"]["state"], done["carried"]["carried"], done["carried"]["version"]) == ("fruitful", False, 3)
    # A retried label writes nothing; a notice changes nothing but is logged.
    assert call(ctx, "carried.mark", {"eventId": "e3", "carriedId": "cq_1", "event": "fruitful",
                                      "expectedVersion": 2})["applied"] is False
    seen = call(ctx, "carried.mark", {"eventId": "e4", "carriedId": "cq_1", "event": "surfaced", "ref": "ext:s1"})
    assert seen["applied"] is True and seen["carried"]["version"] == 3
    with pytest.raises(SidecarError) as refused:
        call(ctx, "carried.mark", {"eventId": "e5", "carriedId": "cq_1", "event": "let_go"})
    assert refused.value.code == "expected_version_required"
    with closing(sqlite3.connect(ctx.paths.sqlite_path)) as connection:
        assert [row[0] for row in connection.execute("SELECT event FROM carried_question_events ORDER BY rowid")] == [
            "carried", "not_now", "fruitful", "surfaced"]


def test_the_list_pages_open_and_closed_questions_with_the_shelf_limit(ctx):
    for index in range(4):
        _carry(ctx, carried_id=f"cq_{index}", text=f"question {index}?")
    call(ctx, "carried.mark", {"eventId": "x", "carriedId": "cq_2", "event": "let_go", "expectedVersion": 1})
    listed = call(ctx, "carried.list", {})
    assert listed["shelfLimit"] == 3 and listed["cursor"] is None
    assert [row["carriedId"] for row in listed["carried"]] == ["cq_0", "cq_1", "cq_3"]
    assert [row["carriedId"] for row in call(ctx, "carried.list", {"which": "closed"})["carried"]] == ["cq_2"]


def test_a_carried_question_comes_back_beside_its_passage_in_the_union_read(ctx):
    from learnloop.db.repositories import Repository

    seed_reading(Repository(ctx.paths.sqlite_path), source_id="src_book", revision_id="rev_book",
                 extraction_id=BOOK, spans=["s1", "s2"])
    _carry(ctx, anchor={"extractionId": BOOK, "spanId": "s2", "anchor": {"quote": "The passage s2."}},
           originKind="selection")
    _carry(ctx, carried_id="cq_gone", text="gone?", anchor={"extractionId": BOOK, "spanId": "s2"})
    call(ctx, "carried.mark", {"eventId": "g", "carriedId": "cq_gone", "event": "let_go", "expectedVersion": 1})
    union = call(ctx, "passage.union_range", {"extractionId": BOOK, "fromSpanId": "s1", "toSpanId": "s2"})
    by_span = {span["spanId"]: span for span in union["spans"]}
    assert by_span["s1"]["carried"] == []
    assert [(row["carriedId"], row["alias"]) for row in by_span["s2"]["carried"]] == [("cq_1", "exact")]


def test_the_drain_lists_todays_pads_and_offers_to_carry_a_closing_question(ctx):
    call(ctx, "desk.apply", {"clientId": "c", "seq": 1, "ops": [
        {"op": "create_desk", "deskId": "d1", "title": "maps", "position": "a0"}]})
    call(ctx, "pad.apply", {"clientId": "c", "seq": 2, "padId": "pad_1", "ops": [
        {"op": "create_pad", "kind": "running", "title": "today", "homeDeskId": "d1"},
        {"op": "insert_block", "blockId": "b1", "kind": "text", "provenance": "learner", "positionKey": "a0",
         "bodyMd": "kernels first"},
        {"op": "insert_block", "blockId": "b2", "kind": "text", "provenance": "learner", "positionKey": "a1",
         "bodyMd": "but why is it a subspace?"}]})
    drain = call(ctx, "pad.drain", {"deskId": "d1"})
    assert drain["day"] == local_day()
    assert [(pad["padId"], pad["firstLine"], pad["lastLine"], pad["carryCandidate"], pad["kept"])
            for pad in drain["pads"]] == [("pad_1", "kernels first", "but why is it a subspace?",
                                           "but why is it a subspace?", False)]
    assert call(ctx, "pad.drain", {"deskId": "d1", "day": "2000-01-01"})["pads"] == []


# -- proposals -----------------------------------------------------------------------------------------------------


def _linked_problem(ctx):
    """A reading whose passage s1 the cue judge tied to one of the learner's misconceptions, and passage s3 tied to
    the same one; a pad whose note sits under a quote linked to s1."""

    from learnloop.db.repositories import Repository

    repository = Repository(ctx.paths.sqlite_path)
    seed_reading(repository, source_id="src_book", revision_id="rev_book", extraction_id=BOOK,
                 spans=["s1", "s2", "s3"])
    with closing(sqlite3.connect(ctx.paths.sqlite_path)) as connection:
        for link_id, span, rank, relation, quote in (("pl_here", "s1", 1, "clarifies_distinction", "Here."),
                                                     ("pl_far", "s3", 2, "new_application", "There, applied."),
                                                     ("pl_worse", "s2", 3, "try_first", "Elsewhere.")):
            connection.execute(
                "INSERT INTO passage_links (id, extraction_id, span_id, target_kind, target_id, relation, quote, "
                "pick_rank, ledger_id, state_key, model, prompt_version, created_at) VALUES (?, ?, ?, "
                "'misconception', 'm_1', ?, ?, ?, ?, 'k', 'm', 'p', '2026-05-19T09:00:00Z')",
                (link_id, BOOK, span, relation, quote, rank, _ledger(connection, f"jl_{link_id}")))
        connection.commit()
    call(ctx, "pad.apply", {"clientId": "c", "seq": 1, "padId": "pad_1", "ops": [
        {"op": "create_pad", "kind": "running"},
        {"op": "insert_block", "blockId": "q1", "kind": "source_quote", "provenance": "source", "positionKey": "a0",
         "bodyMd": "The passage s1."},
        {"op": "link_anchor", "blockId": "q1", "extractionId": BOOK, "spanId": "s1", "expectedAnchorHead": None},
        {"op": "insert_block", "blockId": "n1", "versionId": "v1", "kind": "note", "provenance": "learner",
         "positionKey": "a1", "bodyMd": "so this is where I mix them up", "payload": {"parent_block_id": "q1"}}]})


def test_a_committed_note_under_a_linked_quote_gets_one_proposal_from_the_passage_links(ctx):
    _linked_problem(ctx)
    proposals = call(ctx, "pad.proposals", {"padId": "pad_1"})["proposals"]
    assert len(proposals) == 1
    proposal = proposals[0]
    # The best other passage tied to the same problem (its pick rank), never the passage the block is on.
    assert (proposal["blockId"], proposal["blockVersionId"], proposal["foundBy"], proposal["quote"],
            proposal["judgmentRef"], proposal["shown"]) == ("n1", "v1", "passage_link", "There, applied.",
                                                            "jl_pl_far", True)
    assert proposal["target"] == {"content": {"kind": "source", "source_id": "src_book", "extraction_id": BOOK,
                                              "view": "render"}, "target": {"span_id": "s3"}}
    # Never for a quote block, and once per words version: settling again writes nothing more.
    from learnloop.db.repositories import Repository
    from learnloop.pads.proposals import propose_for_blocks

    assert propose_for_blocks(Repository(ctx.paths.sqlite_path), ["n1", "q1"]) == []


def test_labels_are_logged_once_and_dismiss_or_not_this_hides_the_marker(ctx):
    _linked_problem(ctx)
    before = _counts(ctx)
    proposal_id = call(ctx, "pad.proposals", {"padId": "pad_1"})["proposals"][0]["proposalId"]
    opened = call(ctx, "proposal.label", {"labelId": "l1", "proposalId": proposal_id, "label": "opened"})
    assert opened["applied"] is True
    assert call(ctx, "proposal.label", {"labelId": "l1", "proposalId": proposal_id, "label": "opened"})[
        "applied"] is False
    assert call(ctx, "pad.proposals", {"padId": "pad_1"})["proposals"][0]["shown"] is True
    call(ctx, "proposal.label", {"labelId": "l2", "proposalId": proposal_id, "label": "not_this"})
    shown = call(ctx, "pad.proposals", {"padId": "pad_1"})["proposals"][0]
    assert shown["shown"] is False and [label["label"] for label in shown["labels"]] == ["opened", "not_this"]
    with pytest.raises(SidecarError) as refused:
        call(ctx, "proposal.label", {"labelId": "l1", "proposalId": proposal_id, "label": "dismiss"})
    assert refused.value.code == "label_id_reused"
    with pytest.raises(SidecarError) as refused:
        call(ctx, "proposal.label", {"labelId": "l3", "proposalId": "nope", "label": "dismiss"})
    assert refused.value.code == "proposal_not_found"
    # A promoted row's id is the menus' own: its label is kept without a lookup.
    assert call(ctx, "proposal.label", {"labelId": "l4", "proposalKind": "promoted_row", "proposalId": "row_x",
                                        "label": "ignored"})["applied"] is True
    assert _counts(ctx) == before


def test_an_edit_needs_its_own_proposal_and_a_block_with_no_linked_passage_gets_none(ctx):
    _linked_problem(ctx)
    call(ctx, "pad.apply", {"clientId": "c", "seq": 2, "padId": "pad_1", "ops": [
        {"op": "edit_block", "blockId": "n1", "expectedHead": "v1", "bodyMd": "this is where I mix them up",
         "versionId": "v2"},
        {"op": "insert_block", "blockId": "b9", "kind": "text", "provenance": "learner", "positionKey": "a2",
         "bodyMd": "unrelated thought"}]})
    proposals = call(ctx, "pad.proposals", {"padId": "pad_1"})["proposals"]
    assert [(row["blockId"], row["blockVersionId"]) for row in proposals] == [("n1", "v2")]

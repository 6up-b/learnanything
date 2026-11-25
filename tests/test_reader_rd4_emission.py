"""mvp-0.68: a scratchpad's committed words are learner text (spec §10.11, the contract per review F4; §16's RD4
row: quote-only pads emit nothing, corrections supersede, tombstones retract).

Through ``learnloop.pads.emission`` alone: a committed block version of the learner's own words is queued once as a
``pad_text`` learner text with its frozen snapshot, read by the gap pipeline like any learner text (tier 2), and
superseded or retracted when the block's words change or the block goes. Every model is a fake.
"""

from __future__ import annotations

import pytest

from learnloop.algorithm_versions import PAD_TEXT_ALGORITHM_VERSION, SUCCESSOR_CHAIN, pad_text_on
from learnloop.db.stores import learner_gaps as gap_store
from learnloop.diagnosis.text_gaps.contract import NON_SERVING_SOURCE_KINDS, READABLE_SOURCE_KINDS, SOURCE_KINDS
from learnloop.diagnosis.text_gaps.judges import READER_NOTE_PROMPT_VERSION, reader_version
from learnloop.diagnosis.text_gaps.sources import learner_text
from learnloop.pads import emission
from learnloop.pads.blocks import pad_view
from learnloop.pads.quoting import includes_quote
from learnloop.substrate.passage_spans import rebuild_learner_text_gap_spans
from learnloop.tutor.ai_contracts import LearnerGap
from tests.desk_helpers import seed_reading
from tests.helpers import set_algorithm_version
from tests.reader_rd4_helpers import (
    PAD,
    apply_and_settle,
    create_pad,
    edit,
    gap_clients,
    head_of,
    insert,
    pad_gaps,
    pad_jobs,
    pad_reversals,
    pad_vault,
    read_queued,
    rows,
    settle,
    vault,
)

BELIEF = LearnerGap(kind="misconception", prerequisite_name=None, prerequisite_line=None,
                    belief_statement="A matrix with a zero eigenvalue is the zero matrix.")


def test_the_tag_and_the_kind():
    assert PAD_TEXT_ALGORITHM_VERSION == "mvp-0.68" == SUCCESSOR_CHAIN[-10]
    for version, on in ((SUCCESSOR_CHAIN[SUCCESSOR_CHAIN.index(PAD_TEXT_ALGORITHM_VERSION) - 1], False), (PAD_TEXT_ALGORITHM_VERSION, True)):
        config = type("C", (), {"algorithms": type("A", (), {"algorithm_version": version})()})()
        assert pad_text_on(config) is on
    assert "pad_text" in SOURCE_KINDS and "pad_text" in READABLE_SOURCE_KINDS
    # Never a check brought forward, never a placement observation (spec §10.11 "Effects").
    assert "pad_text" in NON_SERVING_SOURCE_KINDS
    assert emission.SNAPSHOT_KEY == gap_store.PAD_TEXT_SNAPSHOT


def test_a_committed_text_block_is_queued_once_with_its_snapshot(tmp_path):
    paths, repository, batches = pad_vault(tmp_path)
    create_pad(batches)
    reply = batches.pad(PAD, insert("b1", "I think the kernel is always trivial?", version_id="v1"))
    first = settle(paths, repository, reply)
    assert first.queued == ["v1"] and pad_jobs(repository) == {"v1": "queued"}
    # Idempotent: the same batch settled again, and a full reconcile, queue nothing more.
    assert settle(paths, repository, reply).queued == []
    assert emission.reconcile(vault(paths), repository).queued == []
    with repository.connection() as connection:
        job = gap_store.job_for_source(connection, "pad_text", "v1")
    snapshot = job["payload"][gap_store.PAD_TEXT_SNAPSHOT]
    assert (snapshot["text"], snapshot["block_id"], snapshot["pad_id"], snapshot["transcribed"],
            snapshot["quoted_by_learner"], snapshot["passages"]) == (
        "I think the kernel is always trivial?", "b1", PAD, False, False, [])


def test_quotes_sketches_cells_and_stubs_emit_nothing(tmp_path):
    paths, repository, batches = pad_vault(tmp_path)
    create_pad(batches)
    apply_and_settle(paths, repository, batches, PAD,
                     insert("q1", "A linear map is injective exactly when its kernel is trivial.",
                            kind="source_quote", provenance="source"),
                     insert("q2", "The kernel is a subspace.", kind="source_piece", provenance="source",
                            position="a1"),
                     insert("t1", "Look at the null space first.", kind="tutor_quote", provenance="tutor",
                            position="a2"),
                     insert("s1", "", kind="sketch", payload={"paths": ["M0 0 L1 1"]}, position="a3"),
                     insert("c1", "print(1)", kind="cell", position="a4"),
                     insert("f1", "Figure 2", kind="figure", provenance="learnloop", position="a5"),
                     insert("k1", "Is it injective?", kind="check_cell", provenance="tutor", position="a6"),
                     insert("e1", "   ", position="a7"))
    assert pad_jobs(repository) == {}


def test_a_quote_pasted_into_the_learners_block_is_kept_but_never_read_for_a_gap(tmp_path):
    paths, repository, batches = pad_vault(tmp_path)
    create_pad(batches)
    quote = "A linear map is injective exactly when its kernel is trivial. The rest follows."
    apply_and_settle(paths, repository, batches, PAD,
                     insert("q1", quote, kind="source_quote", provenance="source"),
                     insert("b1", "copying: a linear map is injective exactly when its kernel is trivial",
                            version_id="v1", position="a1"))
    with repository.connection() as connection:
        snapshot = gap_store.job_for_source(connection, "pad_text", "v1")["payload"][gap_store.PAD_TEXT_SNAPSHOT]
    assert snapshot["quoted_by_learner"] is True
    clients, llm = gap_clients(BELIEF)
    outcomes = read_queued(paths, repository, clients)
    assert [outcome.state for outcome in outcomes] == ["done"]
    # Recorded as the learner's text, read as nothing, no model call: a belief named from a pasted passage would be
    # the passage's.
    assert pad_gaps(repository) == {"v1": ("none", "none")}
    assert llm.calls == []


def test_the_pipeline_reads_it_as_the_learners_own_words_and_writes_a_pad_text_gap(tmp_path):
    paths, repository, batches = pad_vault(tmp_path)
    create_pad(batches)
    apply_and_settle(paths, repository, batches, PAD, insert("b1", "So a zero eigenvalue means A = 0.",
                                                             version_id="v1"))
    text = learner_text(vault(paths), repository, "pad_text", "v1")
    assert (text.source_kind, text.source_id, text.text, text.context_judge, text.context["surface"]) == (
        "pad_text", "v1", "So a zero eigenvalue means A = 0.", "gap_reader", "scratchpad")
    # Read as free writing beside what the learner studies (the note reader's task), not as a stuck answer.
    assert reader_version(text) == READER_NOTE_PROMPT_VERSION
    clients, _llm = gap_clients(BELIEF)
    outcomes = read_queued(paths, repository, clients)
    assert [(outcome.source_kind, outcome.source_id, outcome.state) for outcome in outcomes] == [
        ("pad_text", "v1", "done")]
    kind, _action = pad_gaps(repository)["v1"]
    assert kind == "misconception"
    assert pad_jobs(repository) == {"v1": "done"}


def test_a_correction_supersedes_the_gap_read_from_the_old_words(tmp_path):
    paths, repository, batches = pad_vault(tmp_path)
    create_pad(batches)
    reply = apply_and_settle(paths, repository, batches, PAD, insert("b1", "A zero eigenvalue means A = 0.",
                                                                     version_id="v1"))
    clients, _llm = gap_clients(BELIEF)
    read_queued(paths, repository, clients)
    apply_and_settle(paths, repository, batches, PAD, edit("b1", head_of(reply, "b1"),
                                                           "A zero eigenvalue means A is singular.", "v2"))
    assert pad_jobs(repository) == {"v1": "done", "v2": "queued"}
    assert pad_reversals(repository) == {"v1": "superseded"}
    read_queued(paths, repository, clients)
    assert set(pad_gaps(repository)) == {"v1", "v2"}
    # The old gap stays, set aside; only the new words' gap stands.
    assert pad_reversals(repository) == {"v1": "superseded"}


def test_words_superseded_before_they_were_read_are_set_aside_unread(tmp_path):
    paths, repository, batches = pad_vault(tmp_path)
    create_pad(batches)
    reply = apply_and_settle(paths, repository, batches, PAD, insert("b1", "first try", version_id="v1"))
    apply_and_settle(paths, repository, batches, PAD, edit("b1", head_of(reply, "b1"), "second try", "v2"))
    assert pad_jobs(repository) == {"v1": "skipped", "v2": "queued"}
    clients, llm = gap_clients()
    read_queued(paths, repository, clients)
    assert set(pad_gaps(repository)) == {"v2"}


def test_a_removed_block_retracts_its_gaps(tmp_path):
    paths, repository, batches = pad_vault(tmp_path)
    create_pad(batches)
    reply = apply_and_settle(paths, repository, batches, PAD, insert("b1", "A zero eigenvalue means A = 0.",
                                                                     version_id="v1"))
    read_queued(paths, repository, gap_clients(BELIEF)[0])
    apply_and_settle(paths, repository, batches, PAD, {"op": "remove_block", "block_id": "b1",
                                                       "expected_head": head_of(reply, "b1")})
    assert pad_reversals(repository) == {"v1": "retracted"}
    assert set(pad_gaps(repository)) == {"v1"}  # the row stays; every reader leaves a reversed gap out
    assert len(pad_jobs(repository)) == 1


def test_a_reading_that_finished_after_its_words_were_replaced_is_set_aside_by_the_reconcile(tmp_path):
    paths, repository, batches = pad_vault(tmp_path)
    create_pad(batches)
    reply = apply_and_settle(paths, repository, batches, PAD, insert("b1", "old words", version_id="v1"))
    # The edit lands while v1's reading is under way (its job leased): the batch's settle cannot skip it.
    with repository.atomic():
        gap_store.lease_next_job(repository.connection(), owner="other", now="2026-11-23T00:00:00Z",
                                 lease_seconds=600)
    apply_and_settle(paths, repository, batches, PAD, edit("b1", head_of(reply, "b1"), "new words", "v2"))
    assert pad_jobs(repository)["v1"] == "leased"
    from learnloop.diagnosis.text_gaps.pipeline import process_learner_text

    process_learner_text(paths.root, repository, learner_text(vault(paths), repository, "pad_text", "v1"),
                         clients=gap_clients(BELIEF)[0])
    assert "v1" in pad_gaps(repository) and pad_reversals(repository) == {}
    assert emission.reconcile(vault(paths), repository).reversed
    assert pad_reversals(repository) == {"v1": "superseded"}


def test_a_move_keeps_the_words_and_their_reading(tmp_path):
    paths, repository, batches = pad_vault(tmp_path)
    create_pad(batches)
    reply = apply_and_settle(paths, repository, batches, PAD, insert("b1", "some words", version_id="v1"))
    apply_and_settle(paths, repository, batches, PAD, {"op": "move_block", "block_id": "b1",
                                                       "expected_head": head_of(reply, "b1"), "position_key": "b0"})
    assert pad_jobs(repository) == {"v1": "queued"} and pad_reversals(repository) == {}


def test_a_lifted_block_carries_its_words_and_their_reading_to_its_own_pad(tmp_path):
    paths, repository, batches = pad_vault(tmp_path)
    create_pad(batches)
    reply = apply_and_settle(paths, repository, batches, PAD, insert("b1", "worth its own pad", version_id="v1"))
    read_queued(paths, repository, gap_clients()[0])
    lifted = apply_and_settle(paths, repository, batches, PAD, {
        "op": "lift_out", "block_id": "b1", "expected_head": head_of(reply, "b1"), "new_pad_id": "pad_2",
        "new_block_id": "b2", "new_version_id": "v2"})
    # Nothing queued again and nothing set aside: the same words, now in the lifted block.
    assert pad_jobs(repository) == {"v1": "done"} and pad_reversals(repository) == {}
    # The lifted block's later edit supersedes the reading of the words it carried.
    apply_and_settle(paths, repository, batches, "pad_2", edit("b2", head_of(lifted, "b2"), "reworded", "v3"))
    assert pad_jobs(repository) == {"v1": "done", "v3": "queued"}
    assert pad_reversals(repository) == {"v1": "superseded"}


def test_ink_transcriptions_and_corrections_are_emitted_as_transcribed(tmp_path):
    paths, repository, batches = pad_vault(tmp_path)
    create_pad(batches, kind="ink")
    reply = apply_and_settle(paths, repository, batches, PAD, insert("i1", "det(A) = 0 so A^{-1} exists",
                                                                     kind="ink", provenance="ink_transcription",
                                                                     version_id="v1"))
    apply_and_settle(paths, repository, batches, PAD, edit("i1", head_of(reply, "i1"),
                                                           "det(A) = 0 so A^{-1} does not exist", "v2"))
    assert pad_jobs(repository) == {"v1": "skipped", "v2": "queued"}
    text = learner_text(vault(paths), repository, "pad_text", "v2")
    assert text.context["transcribed_from_handwriting"] is True and text.markers["transcribed"] is True


def test_below_the_tag_a_pad_emits_nothing_and_the_upgrade_queues_its_standing_words(tmp_path):
    paths, repository, batches = pad_vault(tmp_path)
    set_algorithm_version(paths, SUCCESSOR_CHAIN[SUCCESSOR_CHAIN.index(PAD_TEXT_ALGORITHM_VERSION) - 1])
    create_pad(batches)
    reply = apply_and_settle(paths, repository, batches, PAD, insert("b1", "old words", version_id="v1"))
    apply_and_settle(paths, repository, batches, PAD, edit("b1", head_of(reply, "b1"), "standing words", "v2"))
    assert pad_jobs(repository) == {}
    set_algorithm_version(paths, PAD_TEXT_ALGORITHM_VERSION)
    assert emission.reconcile(vault(paths), repository).queued == ["v2"]


def test_switched_off_nothing_is_queued_and_switched_on_the_reconcile_queues_it(tmp_path):
    paths, repository, batches = pad_vault(tmp_path, "[learner_text_gaps]\nenabled = false\n")
    create_pad(batches)
    apply_and_settle(paths, repository, batches, PAD, insert("b1", "words", version_id="v1"))
    assert pad_jobs(repository) == {}
    toml = paths.root / "learnloop.toml"
    toml.write_text(toml.read_text().replace("[learner_text_gaps]\nenabled = false\n", ""))
    assert emission.reconcile(vault(paths), repository).queued == ["v1"]


def test_the_passages_a_block_is_linked_to_place_its_gap_and_live_equals_rebuild(tmp_path):
    paths, repository, batches = pad_vault(tmp_path)
    seed_reading(repository, source_id="src_book", revision_id="rev_book", extraction_id="ext_book",
                 spans=["s1", "s2"], texts={"s1": "Kernels.", "s2": "Images."})
    create_pad(batches)
    apply_and_settle(paths, repository, batches, PAD,
                     insert("q1", "Kernels.", kind="source_quote", provenance="source"),
                     {"op": "link_anchor", "block_id": "q1", "extraction_id": "ext_book", "span_id": "s1",
                      "expected_anchor_head": None},
                     insert("n1", "why would the kernel matter for injectivity", kind="note", version_id="v1",
                            position="a1", payload={"parent_block_id": "q1"}))
    with repository.connection() as connection:
        snapshot = gap_store.job_for_source(connection, "pad_text", "v1")["payload"][gap_store.PAD_TEXT_SNAPSHOT]
    assert snapshot["passages"] == [["ext_book", "s1"]]
    read_queued(paths, repository, gap_clients()[0])
    live = rows(repository, "SELECT gap_id, extraction_id, span_id, role, quality FROM learner_text_gap_spans "
                            "ORDER BY 1, 2, 3")
    assert [row[1:] for row in live] == [("ext_book", "s1", "selection", "exact_selection")]
    rebuild_learner_text_gap_spans(vault(paths), repository)
    assert rows(repository, "SELECT gap_id, extraction_id, span_id, role, quality FROM learner_text_gap_spans "
                            "ORDER BY 1, 2, 3") == live


def _snapshot(repository, version_id):
    with repository.connection() as connection:
        return gap_store.job_for_source(connection, "pad_text", version_id)["payload"][gap_store.PAD_TEXT_SNAPSHOT]


QUOTE = "A linear map is injective exactly when its kernel is trivial."


def _linked_block_lifted(paths, repository, batches):
    """A pad with a quote and a learner's block linked to passage s1, the block lifted into a pad of its own."""

    seed_reading(repository, source_id="src_book", revision_id="rev_book", extraction_id="ext_book",
                 spans=["s1", "s2"], texts={"s1": "The kernel is the null space of the map.", "s2": "Images."})
    create_pad(batches)
    reply = apply_and_settle(paths, repository, batches, PAD,
                             insert("q1", QUOTE, kind="source_quote", provenance="source"),
                             insert("b1", "so the kernel decides injectivity", version_id="v1", position="a1"),
                             {"op": "link_anchor", "block_id": "b1", "extraction_id": "ext_book", "span_id": "s1",
                              "expected_anchor_head": None})
    return apply_and_settle(paths, repository, batches, PAD, {
        "op": "lift_out", "block_id": "b1", "expected_head": head_of(reply, "b1"), "new_pad_id": "pad_2",
        "new_block_id": "b2", "new_version_id": "v2"})


def test_a_lift_out_takes_the_blocks_links_and_its_quotes_with_its_words(tmp_path):
    """The lifted block's later wording is emitted with the passage its words were linked to, and a quote of the pad
    its words came from is still a quote (review finding 6)."""

    paths, repository, batches = pad_vault(tmp_path)
    lifted = _linked_block_lifted(paths, repository, batches)
    view = pad_view(repository, "pad_2")
    assert [(a["block_id"], a["span_id"], a["inherited_from_block_id"]) for a in view["anchors"]] == [
        ("b2", "s1", None)]
    assert pad_view(repository, PAD)["anchors"] == []  # the stub gave the link up
    apply_and_settle(paths, repository, batches, "pad_2", edit("b2", head_of(lifted, "b2"),
                                                               "so the kernel decides injectivity, I think", "v3"))
    assert _snapshot(repository, "v3")["passages"] == [["ext_book", "s1"]]
    apply_and_settle(paths, repository, batches, "pad_2", edit("b2", "v3", "copying: " + QUOTE, "v4"))
    assert _snapshot(repository, "v4")["quoted_by_learner"] is True


def test_a_lift_made_before_links_moved_still_carries_them(tmp_path):
    """A lift made before this fix left the block's links on the stub: the pad's read shows them on the lifted
    block (read only), the passage's union marks the lifted block, and the lifted block's emission carries them."""

    paths, repository, batches = pad_vault(tmp_path)
    lifted = _linked_block_lifted(paths, repository, batches)
    # Put the link back on the stub, as the earlier lift left it.
    batches.pad(PAD, {"op": "link_anchor", "block_id": "b1", "extraction_id": "ext_book", "span_id": "s1",
                      "expected_anchor_head": rows(repository, "SELECT event_id FROM pad_block_anchors WHERE block_id "
                                                               "= 'b1' ORDER BY rowid DESC LIMIT 1")[0][0]})
    batches.pad("pad_2", {"op": "unlink_anchor", "block_id": "b2", "extraction_id": "ext_book", "span_id": "s1",
                          "expected_anchor_head": rows(repository, "SELECT event_id FROM pad_block_anchors WHERE "
                                                                   "block_id = 'b2'")[0][0]})
    view = pad_view(repository, "pad_2")
    assert [(a["block_id"], a["span_id"], a["inherited_from_block_id"]) for a in view["anchors"]] == [
        ("b2", "s1", "b1")]
    from learnloop.passage_union.union import union_range

    union = union_range(vault(paths), repository, extraction_id="ext_book", from_span_id="s1", to_span_id="s1")
    assert [(row["block_id"], row["pad_id"], row["lifted_from_block_id"]) for row in union["spans"][0]["pad_blocks"]
            ] == [("b2", "pad_2", "b1")]
    apply_and_settle(paths, repository, batches, "pad_2", edit("b2", head_of(lifted, "b2"), "reworded words", "v3"))
    assert _snapshot(repository, "v3")["passages"] == [["ext_book", "s1"]]


@pytest.mark.parametrize(("block", "quotes", "expected"), [
    ("a linear map is injective exactly when its kernel is trivial", ["A linear map is injective exactly when its "
                                                                     "kernel is trivial. Then more."], True),
    ("I am not sure the kernel matters", ["A linear map is injective exactly when its kernel is trivial."], False),
    ("yes", ["Yes."], False),
    ("", ["Anything at all here."], False),
])
def test_a_quote_is_a_whole_sentence_of_it_word_for_word(block, quotes, expected):
    assert includes_quote(block, quotes) is expected

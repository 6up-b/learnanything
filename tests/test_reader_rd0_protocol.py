"""The workbench's write protocol and its desk and pad ops (spec §3.4, §3.5, §5.1, §5.2, §10):
batches in seq order, conflicts that return heads, retries that return the stored receipt."""

from __future__ import annotations

import pytest

from learnloop.db.repositories import Repository
from learnloop.desks.protocol import ProtocolError
from learnloop.desks.workspace import desk_state
from learnloop.pads.blocks import pad_list, pad_view
from tests.desk_helpers import Batches, source_ref
from tests.helpers import create_basic_vault


@pytest.fixture
def repository(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    return Repository(paths.sqlite_path)


def _desk(batches: Batches, desk_id: str = "d1") -> dict:
    return batches.desk({"op": "create_desk", "desk_id": desk_id, "title": "linear maps", "position": "a0"})


def _counts(repository):
    with repository.connection() as connection:
        return {table: connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                for table in ("desks", "desk_windows", "desk_op_receipts", "pads", "pad_block_versions",
                              "pad_block_anchors", "pad_op_receipts")}


def _slots(repository, desk_id="d1"):
    desk = next(d for d in desk_state(repository)["desks"] if d["desk_id"] == desk_id)
    return [[window["window_id"] for window in slot["windows"]] for slot in desk["slots"]]


def _version(repository, desk_id="d1"):
    return next(d for d in desk_state(repository)["desks"] if d["desk_id"] == desk_id)["version"]


def _open(window_id: str, version: int, **extra) -> dict:
    return {"op": "open_window", "desk_id": "d1", "window_id": window_id, "expected_version": version,
            "content": source_ref(), **extra}


# -- the protocol ------------------------------------------------------------------------------------


def test_a_batch_out_of_seq_order_is_refused_and_applies_nothing(repository):
    batches = Batches(repository)
    batches.seq = 1  # the client skips batch 1
    before = _counts(repository)
    with pytest.raises(ProtocolError) as refused:
        _desk(batches)
    assert refused.value.code == "seq_gap" and refused.value.details == {"seq": 2, "expected_seq": 1}
    assert _counts(repository) == before


def test_a_retried_batch_returns_its_stored_receipt_and_applies_nothing_again(repository):
    batches = Batches(repository)
    first = _desk(batches)
    assert first == {"applied_seq": 1, "results": [{"status": "ok"}], "versions": [{"desk_id": "d1", "version": 1}]}
    after_first = _counts(repository)
    batches.seq = 0  # the reply was lost: the outbox replays batch 1
    assert _desk(batches) == first
    assert _counts(repository) == after_first


def test_a_batch_number_used_with_other_ops_is_refused(repository):
    batches = Batches(repository)
    _desk(batches)
    batches.seq = 0
    with pytest.raises(ProtocolError) as refused:
        _desk(batches, "d2")
    assert refused.value.code == "seq_reused"
    assert [d["desk_id"] for d in desk_state(repository)["desks"]] == ["d1"]


def test_desk_and_pad_batches_share_one_sequence_per_client(repository):
    batches = Batches(repository)
    _desk(batches)
    batches.pad("p1", {"op": "create_pad", "kind": "running", "home_desk_id": "d1"})
    batches.seq = 0  # a pad batch numbered as the desk batch already applied
    with pytest.raises(ProtocolError) as refused:
        batches.pad("p1", {"op": "create_pad", "kind": "running", "home_desk_id": "d1"})
    assert refused.value.code == "seq_reused"
    assert desk_state(repository)["server_seq"] == [{"client_id": "client_a", "seq": 2}]
    other = Batches(repository, "client_b")
    assert other.desk({"op": "set_dock", "desk_id": "d1", "dock": "right", "expected_version": 1})["applied_seq"] == 1
    assert desk_state(repository)["server_seq"] == [{"client_id": "client_a", "seq": 2}, {"client_id": "client_b", "seq": 1}]


def test_a_stale_head_is_a_conflict_with_the_current_head_and_is_not_applied(repository):
    batches = Batches(repository)
    _desk(batches)
    batches.desk({"op": "rename_desk", "desk_id": "d1", "title": "maps", "expected_version": 1})
    reply = batches.desk({"op": "rename_desk", "desk_id": "d1", "title": "stale", "expected_version": 1},
                         {"op": "set_dock", "desk_id": "d1", "dock": "bl", "expected_version": 2})
    assert reply["results"] == [{"status": "conflict", "current": {"desk_id": "d1", "version": 2}}, {"status": "ok"}]
    desk = desk_state(repository)["desks"][0]
    assert desk["title"] == "maps" and desk["companion"]["dock"] == "bl" and desk["version"] == 3


def test_a_refused_op_leaves_no_partial_write_and_the_batch_still_lands(repository):
    batches = Batches(repository)
    _desk(batches)
    batches.desk(_open("w1", 1))
    # pair with nothing to the right: refused; the rename after it lands.
    reply = batches.desk({"op": "pair", "window_id": "w1", "expected_version": 2},
                         {"op": "rename_desk", "desk_id": "d1", "title": "after", "expected_version": 2})
    assert reply["results"][0] == {"status": "refused", "code": "nothing_to_the_right",
                                   "message": "Nothing to the right to share this slot with."}
    assert reply["results"][1] == {"status": "ok"} and reply["applied_seq"] == 3
    assert _slots(repository) == [["w1"]]


def test_batches_replayed_out_of_order_converge_to_the_in_order_state(tmp_path):
    def run(order):
        paths = create_basic_vault(tmp_path / f"vault_{'_'.join(map(str, order))}")
        repository = Repository(paths.sqlite_path)
        from pydantic import TypeAdapter

        from learnloop.desks.workspace import DeskOp, apply_desk_ops

        plan = {
            1: [{"op": "create_desk", "desk_id": "d1", "title": "t", "position": "a0"}],
            2: [_open("w1", 1)],
            3: [_open("w2", 2), {"op": "pair", "window_id": "w1", "expected_version": 3}],
        }
        for seq in order:
            try:
                apply_desk_ops(repository, client_id="c", seq=seq,
                               ops=[TypeAdapter(DeskOp).validate_python(op) for op in plan[seq]])
            except ProtocolError:
                continue
        return desk_state(repository)["desks"]

    in_order = run([1, 2, 3])
    # The outbox sends 1, 3, 2, then replays every unacknowledged batch in order (2 was applied, 3 refused).
    assert run([1, 3, 2, 2, 3]) == in_order
    assert [[w["window_id"] for w in slot["windows"]] for slot in in_order[0]["slots"]] == [["w1", "w2"]]


# -- desks and windows ---------------------------------------------------------------------------------


def test_windows_open_beside_pair_at_most_two_and_unpair(repository):
    batches = Batches(repository)
    _desk(batches)
    batches.desk(_open("w1", 1), _open("w3", 2), _open("w2", 3, after_window_id="w1"))
    assert _slots(repository) == [["w1"], ["w2"], ["w3"]]
    batches.desk({"op": "pair", "window_id": "w1", "expected_version": 4})
    assert _slots(repository) == [["w1", "w2"], ["w3"]]
    third = batches.desk({"op": "pair", "window_id": "w1", "expected_version": 5})
    assert third["results"][0]["code"] == "slot_full"
    state = desk_state(repository)["desks"][0]
    pair = state["slots"][0]["windows"]
    assert [(w["pane"], w["active"]) for w in pair] == [(0, True), (1, False)]
    batches.desk({"op": "set_active_pane", "window_id": "w2", "expected_version": 5})
    pair = desk_state(repository)["desks"][0]["slots"][0]["windows"]
    assert [w["active"] for w in pair] == [False, True]
    batches.desk({"op": "unpair", "window_id": "w2", "expected_version": 6})
    assert _slots(repository) == [["w1"], ["w2"], ["w3"]]


def test_close_and_reopen_move_and_move_to_another_desk(repository):
    batches = Batches(repository)
    _desk(batches)
    batches.desk(_open("w1", 1), _open("w2", 2), _open("w3", 3),
                 {"op": "set_focus", "desk_id": "d1", "window_id": "w2", "expected_version": 4})
    batches.desk({"op": "close_window", "window_id": "w2", "expected_version": 5})
    state = desk_state(repository)["desks"][0]
    assert _slots(repository) == [["w1"], ["w3"]] and state["focus_window_id"] is None
    batches.desk({"op": "reopen_window", "window_id": "w2", "slot": 1, "expected_version": 6})
    assert _slots(repository) == [["w1"], ["w2"], ["w3"]]
    batches.desk({"op": "move_window", "window_id": "w3", "to_slot": 0, "expected_version": 7})
    assert _slots(repository) == [["w3"], ["w1"], ["w2"]]
    _desk(batches, "d2")
    reply = batches.desk({"op": "move_to_desk", "window_id": "w1", "to_desk_id": "d2", "expected_version": 8})
    assert reply["versions"] == [{"desk_id": "d1", "version": 9}, {"desk_id": "d2", "version": 2}]
    assert _slots(repository) == [["w3"], ["w2"]] and _slots(repository, "d2") == [["w1"]]


def test_a_desk_carries_its_view_dock_shown_goal_and_order_and_archives(repository):
    batches = Batches(repository)
    _desk(batches)
    _desk(batches, "d0")
    batches.desk(_open("w1", 1, view={"spanId": "s4", "offsetFrac": 0.25}),
                 {"op": "set_view", "window_id": "w1", "view": {"spanId": "s9", "offsetFrac": 0.5}, "expected_version": 2},
                 {"op": "set_companion_shown", "desk_id": "d1", "shown": True, "expected_version": 3},
                 {"op": "set_goal", "desk_id": "d1", "goal_id": "goal_linear_algebra_ml", "expected_version": 4},
                 {"op": "move_desk", "desk_id": "d0", "position": "b0", "expected_version": 1})
    state = desk_state(repository)["desks"]
    assert [d["desk_id"] for d in state] == ["d1", "d0"]
    d1 = state[0]
    assert d1["companion"] == {"dock": "br", "shown": True} and d1["goal_id"] == "goal_linear_algebra_ml"
    assert d1["slots"][0]["windows"][0]["view"] == {"spanId": "s9", "offsetFrac": 0.5}
    assert d1["slots"][0]["windows"][0]["content"] == source_ref()
    batches.desk({"op": "archive_desk", "desk_id": "d0", "expected_version": 2})
    assert [d["desk_id"] for d in desk_state(repository)["desks"]] == ["d1"]


def test_a_pad_stack_window_holds_pads_and_lessons(repository):
    batches = Batches(repository)
    _desk(batches)
    batches.desk({"op": "open_window", "desk_id": "d1", "window_id": "stack", "expected_version": 1,
                  "stack": [{"kind": "pad", "padId": "p1"}, {"kind": "lesson", "lessonId": "les_1"}]})
    window = desk_state(repository)["desks"][0]["slots"][0]["windows"][0]
    assert window["kind"] == "pad_stack" and window["stack"] == [{"kind": "pad", "pad_id": "p1"},
                                                                {"kind": "lesson", "lesson_id": "les_1"}]


# -- pads --------------------------------------------------------------------------------------------


def _pad(batches: Batches, pad_id="p1", **extra) -> dict:
    return batches.pad(pad_id, {"op": "create_pad", "kind": "named", "title": "kernels", **extra})


def test_blocks_chain_and_a_stale_edit_returns_the_current_head(repository):
    batches = Batches(repository)
    _pad(batches)
    inserted = batches.pad("p1", {"op": "insert_block", "block_id": "b1", "version_id": "v1", "kind": "text",
                                  "provenance": "learner", "position_key": "a0", "body_md": "first"})
    assert inserted["heads"] == [{"block_id": "b1", "head_version_id": "v1"}]
    batches.pad("p1", {"op": "edit_block", "block_id": "b1", "expected_head": "v1", "version_id": "v2",
                       "body_md": "second"},
                {"op": "edit_block", "block_id": "b1", "expected_head": "v2", "version_id": "v3", "body_md": "third"})
    before = _counts(repository)
    stale = batches.pad("p1", {"op": "edit_block", "block_id": "b1", "expected_head": "v1", "body_md": "other device"})
    assert stale["results"] == [{"status": "conflict", "current": {"block_id": "b1", "head_version_id": "v3"}}]
    assert _counts(repository)["pad_block_versions"] == before["pad_block_versions"]
    view = pad_view(repository, "p1")
    assert [(b["block_id"], b["head_version_id"], b["body_md"]) for b in view["blocks"]] == [("b1", "v3", "third")]


def test_remove_move_lift_out_and_links(repository):
    batches = Batches(repository)
    _pad(batches, home_desk_id="d1")
    batches.pad("p1", *[{"op": "insert_block", "block_id": f"b{n}", "version_id": f"b{n}v1", "kind": "text",
                         "provenance": "learner", "position_key": f"a{n}", "body_md": f"line {n}"} for n in (1, 2, 3)])
    batches.pad("p1", {"op": "remove_block", "block_id": "b1", "expected_head": "b1v1"},
                {"op": "move_block", "block_id": "b3", "expected_head": "b3v1", "position_key": "a0"},
                {"op": "link_anchor", "block_id": "b2", "extraction_id": "ext_book", "span_id": "s4",
                 "annotation_id": "ann_1", "event_id": "e1"},
                {"op": "link_anchor", "block_id": "b3", "extraction_id": "ext_book", "span_id": "s5", "event_id": "e2"},
                {"op": "unlink_anchor", "block_id": "b3", "extraction_id": "ext_book", "span_id": "s5", "event_id": "e3"})
    view = pad_view(repository, "p1")
    assert [b["block_id"] for b in view["blocks"]] == ["b3", "b2"]  # b1 removed, b3 moved first
    assert [(a["block_id"], a["span_id"], a["annotation_id"]) for a in view["anchors"]] == [("b2", "s4", "ann_1")]
    head = view["blocks"][1]["head_version_id"]
    lifted = batches.pad("p1", {"op": "lift_out", "block_id": "b2", "expected_head": head, "new_pad_id": "p2",
                                "new_block_id": "b2x", "title": "its own pad", "stub_version_id": "stub",
                                "new_version_id": "b2xv1"})
    assert lifted["pads"] == [{"pad_id": "p2", "version": 1}]
    stub = next(b for b in pad_view(repository, "p1")["blocks"] if b["block_id"] == "b2")
    assert stub["kind"] == "lifted" and stub["payload"] == {"lifted_to_pad_id": "p2", "lifted_block_id": "b2x"}
    moved = pad_view(repository, "p2")
    assert moved["pad"]["home_desk_id"] == "d1"
    assert [(b["body_md"], b["provenance"]) for b in moved["blocks"]] == [("line 2", "learner")]


def test_provenance_is_never_laundered(repository):
    batches = Batches(repository)
    _pad(batches)
    batches.pad("p1", {"op": "insert_block", "block_id": "q", "version_id": "q1", "kind": "source_quote",
                       "provenance": "source", "position_key": "a0", "body_md": "A quote."},
                {"op": "insert_block", "block_id": "i", "version_id": "i1", "kind": "ink",
                 "provenance": "ink_transcription", "position_key": "a1", "body_md": "teh kernal"})
    reply = batches.pad("p1", {"op": "edit_block", "block_id": "q", "expected_head": "q1", "body_md": "Mine now."},
                        {"op": "edit_block", "block_id": "i", "expected_head": "i1", "body_md": "the kernel"})
    assert reply["results"][0]["status"] == "refused" and reply["results"][0]["code"] == "not_editable"
    blocks = {b["block_id"]: b for b in pad_view(repository, "p1")["blocks"]}
    assert blocks["q"]["body_md"] == "A quote." and blocks["q"]["provenance"] == "source"
    assert blocks["i"]["body_md"] == "the kernel" and blocks["i"]["provenance"] == "learner_correction"


def test_pad_metadata_versions_and_keep(repository):
    batches = Batches(repository)
    _pad(batches)
    reply = batches.pad("p1", {"op": "keep", "expected_version": 1},
                        {"op": "set_title", "title": "stale", "expected_version": 1},
                        {"op": "set_title", "title": "kept kernels", "expected_version": 2})
    assert [r["status"] for r in reply["results"]] == ["ok", "conflict", "ok"]
    assert reply["results"][1]["current"] == {"pad_id": "p1", "version": 2}
    pad = pad_view(repository, "p1")["pad"]
    assert pad["kept"] is True and pad["title"] == "kept kernels" and pad["version"] == 3


def test_a_create_for_an_existing_pad_or_block_conflicts(repository):
    batches = Batches(repository)
    _pad(batches)
    batches.pad("p1", {"op": "insert_block", "block_id": "b1", "version_id": "v1", "kind": "text",
                       "provenance": "learner", "position_key": "a0"})
    again = batches.pad("p1", {"op": "create_pad", "kind": "named"},
                        {"op": "insert_block", "block_id": "b1", "kind": "text", "provenance": "learner",
                         "position_key": "a1"})
    assert again["results"] == [{"status": "conflict", "current": {"pad_id": "p1", "version": 1}},
                                {"status": "conflict", "current": {"block_id": "b1", "head_version_id": "v1"}}]


def test_running_pads_show_on_their_desk_and_the_library_lists_pads(repository):
    batches = Batches(repository)
    _desk(batches)
    batches.pad("run", {"op": "create_pad", "kind": "running", "home_desk_id": "d1"},
                {"op": "insert_block", "block_id": "r1", "kind": "text", "provenance": "learner", "position_key": "a0",
                 "body_md": "orthogonal projections\nmore", "day": "2026-11-22"})
    _pad(batches, "p2")
    assert desk_state(repository)["running_pad_ids"] == ["run"]
    listed = pad_list(repository, query="orthogonal")
    assert [p["pad_id"] for p in listed["pads"]] == ["run"] and listed["pads"][0]["first_line"] == "orthogonal projections"
    assert {p["pad_id"] for p in pad_list(repository)["pads"]} == {"run", "p2"}
    assert [p["pad_id"] for p in pad_list(repository, desk_id="d1")["pads"]] == ["run"]


def test_an_op_refused_after_its_first_write_leaves_none_of_its_writes(repository):
    batches = Batches(repository)
    _desk(batches)
    _desk(batches, "d2")
    batches.desk(_open("w1", 1), _open("w2", 2), _open("w3", 3))
    # The move takes w1 off d1 (renumbering d1's slots) before it finds no such window on d2 to open after.
    reply = batches.desk({"op": "move_to_desk", "window_id": "w1", "to_desk_id": "d2", "after_window_id": "nope",
                          "expected_version": 4})
    assert reply["results"][0]["status"] == "refused" and reply["results"][0]["code"] == "window_not_open"
    assert _slots(repository) == [["w1"], ["w2"], ["w3"]] and _slots(repository, "d2") == []
    assert _version(repository) == 4

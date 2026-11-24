"""The Reader workbench v2 RD4 fix round, server side (the Codex review of RD4, 2026-11-23): what a stale edit leaves
(finding 3), stack membership as its own op (7), the running pad ensured in one place (8), and the reads the
frontend needs for a passage's canonical content (12) and for reopening a closed source at a stored place (13)."""

from __future__ import annotations

import pytest

from learnloop.desks.workspace import desk_state
from learnloop.pads.blocks import pad_list, pad_view
from tests.desk_helpers import Batches, seed_reading
from tests.reader_rd4_helpers import PAD, create_pad, edit, insert, pad_jobs, pad_vault, settle


# -- finding 3: a stale edit keeps both ------------------------------------------------------------------------


def _two_devices(tmp_path):
    paths, repository, device_a = pad_vault(tmp_path)
    device_b = Batches(repository, client_id="client_b")
    create_pad(device_a)
    reply = device_a.pad(PAD, insert("b1", "first words", version_id="v1"),
                         insert("b9", "the next block", version_id="v9", position="a5"))
    settle(paths, repository, reply)
    return paths, repository, device_a, device_b


def test_a_stale_edit_with_keep_both_keeps_the_server_head_and_lands_as_its_own_block(tmp_path):
    paths, repository, device_a, device_b = _two_devices(tmp_path)
    settle(paths, repository, device_a.pad(PAD, edit("b1", "v1", "device A's words", "v2")))
    reply = device_b.pad(PAD, {**edit("b1", "v1", "device B's words", "vB"),
                               "keep_both": {"block_id": "b1_b", "version_id": "vB2",
                                             "label": "from your other device · 10:02"}})
    [result] = reply["results"]
    assert result == {"status": "ok", "head_version_id": "v2",
                      "kept_both": {"block_id": "b1_b", "head_version_id": "vB2"}}
    settle(paths, repository, reply)
    blocks = {block["block_id"]: block for block in pad_view(repository, PAD)["blocks"]}
    # The other device's words stand; this device's words are a block of their own, right after them.
    assert blocks["b1"]["body_md"] == "device A's words" and blocks["b1"]["head_version_id"] == "v2"
    assert blocks["b1_b"]["body_md"] == "device B's words"
    assert blocks["b1_b"]["payload"]["conflict"] == {
        "of_block_id": "b1", "expected_head": "v1", "server_head_version_id": "v2",
        "label": "from your other device · 10:02", "at": blocks["b1_b"]["payload"]["conflict"]["at"]}
    order = [block["block_id"] for block in pad_view(repository, PAD)["blocks"]]
    assert order == ["b1", "b1_b", "b9"]
    # Both wordings are learner text; neither supersedes the other.
    assert pad_jobs(repository) == {"v1": "skipped", "v2": "queued", "v9": "queued", "vB2": "queued"}


def test_keep_both_on_a_current_head_is_an_ordinary_edit_and_a_removed_block_still_keeps_the_words(tmp_path):
    paths, repository, device_a, device_b = _two_devices(tmp_path)
    reply = device_a.pad(PAD, {**edit("b1", "v1", "an ordinary edit", "v2"), "keep_both": {"block_id": "unused"}})
    assert reply["results"] == [{"status": "ok", "head_version_id": "v2"}]
    device_a.pad(PAD, {"op": "remove_block", "block_id": "b1", "expected_head": "v2"})
    late = device_b.pad(PAD, {**edit("b1", "v1", "typed before I saw it go", "vB"), "keep_both": {"block_id": "bk"}})
    assert late["results"][0]["kept_both"]["block_id"] == "bk"
    blocks = {block["block_id"]: block for block in pad_view(repository, PAD)["blocks"]}
    assert "b1" not in blocks and blocks["bk"]["body_md"] == "typed before I saw it go"


def test_without_keep_both_a_stale_edit_remove_move_or_lift_is_a_conflict_naming_the_head_and_writes_nothing(
        tmp_path):
    paths, repository, device_a, device_b = _two_devices(tmp_path)
    device_a.pad(PAD, edit("b1", "v1", "device A's words", "v2"))
    before = pad_view(repository, PAD)
    stale = device_b.pad(PAD, edit("b1", "v1", "lost?", "vB"),
                         {"op": "remove_block", "block_id": "b1", "expected_head": "v1"},
                         {"op": "move_block", "block_id": "b1", "expected_head": "v1", "position_key": "z"},
                         {"op": "lift_out", "block_id": "b1", "expected_head": "v1", "new_pad_id": "pad_x",
                          "new_block_id": "bx"})
    assert stale["results"] == [{"status": "conflict", "current": {"block_id": "b1", "head_version_id": "v2"}}] * 4
    assert pad_view(repository, PAD) == before


@pytest.mark.parametrize(("a", "b"), [(None, None), (None, "a0"), ("a0", None), ("a0", "a1"), ("a0", "a01"),
                                      ("0V", "0W"), ("az", "b"), ("a", "a0V")])
def test_the_server_places_a_block_between_two_keys_as_the_client_does(a, b):
    from learnloop.pads.blocks import key_between

    key = key_between(a, b)
    assert (a is None or a < key) and (b is None or key < b) and not key.endswith("0")


# -- findings 7 and 8: stack membership as its own op; the running pad ensured in one place ----------------------


def _desk_with_stack(tmp_path):
    paths, repository, device_a = pad_vault(tmp_path)
    device_b = Batches(repository, client_id="client_b")
    create_pad(device_a)
    device_a.desk({"op": "create_desk", "desk_id": "d1", "title": "maps", "position": "a0"},
                  {"op": "open_window", "desk_id": "d1", "window_id": "w_stack", "expected_version": 1,
                   "stack": [{"kind": "pad", "pad_id": PAD}], "view": {"active_pad": PAD}})
    return paths, repository, device_a, device_b


def _stack(repository, window_id="w_stack", desk_id="d1"):
    desk = next(d for d in desk_state(repository)["desks"] if d["desk_id"] == desk_id)
    window = next(w for slot in desk["slots"] for w in slot["windows"] if w["window_id"] == window_id)
    return [entry["pad_id"] for entry in window["stack"]], window["view"]


def test_a_pad_added_to_a_stack_survives_another_devices_desk_change_and_its_view_write(tmp_path):
    """Device B changes the desk (a whole-view write) while device A creates a pad and adds it to the stack against
    an older desk version: the addition still lands, and B's view stays (review finding 7)."""

    paths, repository, device_a, device_b = _desk_with_stack(tmp_path)
    device_b.desk({"op": "set_view", "desk_id": "d1", "window_id": "w_stack", "expected_version": 2,
                   "view": {"active_pad": PAD, "split": [0.5, 0.5]}})
    create_pad(device_a, "pad_2", kind="named")
    reply = device_a.desk({"op": "add_to_stack", "desk_id": "d1", "window_id": "w_stack", "expected_version": 2,
                           "entry": {"kind": "pad", "pad_id": "pad_2"}})
    assert reply["results"][0]["status"] == "ok" and reply["results"][0]["changed"] is True
    again = device_b.desk({"op": "add_to_stack", "desk_id": "d1", "window_id": "w_stack",
                           "entry": {"kind": "pad", "pad_id": "pad_2"}})
    assert again["results"][0]["changed"] is False  # a union: never a duplicate tab
    stack, view = _stack(repository)
    assert stack == [PAD, "pad_2"] and view == {"active_pad": PAD, "split": [0.5, 0.5]}
    # A whole-view write never drops a tab: membership lives apart from the view.
    device_b.desk({"op": "set_view", "desk_id": "d1", "window_id": "w_stack", "expected_version": 5, "view": {}})
    assert _stack(repository)[0] == [PAD, "pad_2"]
    removed = device_a.desk({"op": "remove_from_stack", "desk_id": "d1", "window_id": "w_stack",
                             "entry": {"kind": "pad", "pad_id": "pad_2"}})
    assert removed["results"][0]["changed"] is True and _stack(repository)[0] == [PAD]
    last = device_a.desk({"op": "remove_from_stack", "desk_id": "d1", "window_id": "w_stack",
                          "entry": {"kind": "pad", "pad_id": PAD}})
    assert last["results"][0] == {"status": "refused", "code": "last_in_stack",
                                  "message": "This is the last pad in the stack. Close the window to close it."}
    missing = device_a.desk({"op": "add_to_stack", "desk_id": "d1", "window_id": "w_stack",
                             "entry": {"kind": "pad", "pad_id": "pad_nope"}})
    assert missing["results"][0]["code"] == "pad_not_found"


def test_the_running_pad_is_ensured_once_with_its_stack_on_a_new_desk_and_an_old_one(tmp_path):
    paths, repository, device_a, device_b = _desk_with_stack(tmp_path)
    device_a.desk({"op": "create_desk", "desk_id": "d2", "title": "fresh", "position": "a1"})
    fresh = device_a.desk({"op": "ensure_running_pad", "desk_id": "d2", "pad_id": "run_d2", "window_id": "w_run",
                           "title": "Running"})
    assert fresh["results"][0] == {"status": "ok", "pad_id": "run_d2", "window_id": "w_run", "created_pad": True,
                                   "created_window": True, "added_to_stack": False}
    assert _stack(repository, "w_run", "d2")[0] == ["run_d2"]
    assert "run_d2" in desk_state(repository)["running_pad_ids"]
    # Again, from the other device with its own ids: the same pad and window, nothing created.
    again = device_b.desk({"op": "ensure_running_pad", "desk_id": "d2", "pad_id": "run_other", "window_id": "w_other"})
    assert again["results"][0] == {"status": "ok", "pad_id": "run_d2", "window_id": "w_run", "created_pad": False,
                                   "created_window": False, "added_to_stack": False}
    # An existing desk with a stack but no running pad: the running pad joins that stack.
    old = device_a.desk({"op": "ensure_running_pad", "desk_id": "d1", "pad_id": "run_d1", "window_id": "w_unused"})
    assert old["results"][0]["added_to_stack"] is True and old["results"][0]["window_id"] == "w_stack"
    assert _stack(repository)[0] == [PAD, "run_d1"]
    assert "run_d1" in {pad["pad_id"] for pad in pad_list(repository, desk_id="d1")["pads"]}


# -- findings 12 and 13: a passage's canonical content; reopening a closed source at a stored link ---------------


def test_a_passages_canonical_content_comes_with_its_title_location_and_time_apart(tmp_path, monkeypatch):
    from learnloop.passage_union import content as content_module
    from learnloop.passage_union.content import passage_content
    from tests.reader_rd4_helpers import vault

    paths, repository, _batches = pad_vault(tmp_path)
    long_text = "The kernel of a linear map is every vector it sends to zero. " * 4
    seed_reading(repository, source_id="src_book", revision_id="rev_book", extraction_id="ext_book",
                 spans=["s1", "s2", "s3"], texts={"s1": long_text, "s2": "Images.", "s3": "Ranks."})
    seed_reading(repository, source_id="src_talk", revision_id="rev_talk", extraction_id="ext_talk",
                 spans=["c1", "c2"], texts={"c1": "Say the kernel is trivial.", "c2": "Then it is injective."},
                 timed=True)
    got = passage_content(vault(paths), repository, extraction_id="ext_book", from_span_id="s1", to_span_id="s2")
    assert (got["source_id"], got["title"], got["withheld"]) == ("src_book", "file:///src_book.pdf", False)
    # The source's own words, unclipped, never a search row's label; location and time apart from them.
    assert [(row["span_id"], row["text"], row["t0"]) for row in got["spans"]] == [
        ("s1", long_text, None), ("s2", "Images.", None)]
    assert got["spans"][0]["section_label"] == "Section ext_book_u1"
    timed = passage_content(vault(paths), repository, extraction_id="ext_talk", t0=12, t1=15)
    assert [(row["span_id"], row["text"], row["t0"], row["t1"]) for row in timed["spans"]] == [
        ("c2", "Then it is injective.", 10.0, 20.0)]
    # Exam or held-out material is withheld: nothing protected is copied into a pad.
    monkeypatch.setattr(content_module, "exam_withheld", lambda _vault, _repository, keys: {keys[0]})
    held = passage_content(vault(paths), repository, extraction_id="ext_book", from_span_id="s1", to_span_id="s2")
    assert held["withheld"] is True and [row["text"] for row in held["spans"]] == [None, "Images."]


def test_a_pads_links_name_their_source_and_time_so_a_closed_source_can_be_reopened(tmp_path):
    paths, repository, batches = pad_vault(tmp_path)
    seed_reading(repository, source_id="src_book", revision_id="rev_book", extraction_id="ext_book",
                 spans=["s1"], texts={"s1": "Kernels."})
    seed_reading(repository, source_id="src_talk", revision_id="rev_talk", extraction_id="ext_talk",
                 spans=["c1", "c2"], timed=True)
    create_pad(batches)
    batches.pad(PAD, insert("q1", "Kernels.", kind="source_quote", provenance="source"),
                insert("q2", "the cue", kind="source_quote", provenance="source", position="a1"),
                {"op": "link_anchor", "block_id": "q1", "extraction_id": "ext_book", "span_id": "s1",
                 "expected_anchor_head": None},
                {"op": "link_anchor", "block_id": "q2", "extraction_id": "ext_talk", "span_id": "c2",
                 "expected_anchor_head": None})
    anchors = {a["block_id"]: a for a in pad_view(repository, PAD)["anchors"]}
    assert (anchors["q1"]["source_id"], anchors["q1"]["t"]) == ("src_book", None)
    assert (anchors["q2"]["source_id"], anchors["q2"]["t"]) == ("src_talk", 10.0)
    # Which is all a source (or video) window needs to open with no window of that source on the desk.
    batches.desk({"op": "create_desk", "desk_id": "d1", "title": "t", "position": "a0"},
                 {"op": "open_window", "desk_id": "d1", "window_id": "w_talk", "expected_version": 1,
                  "content": {"kind": "video", "source_id": anchors["q2"]["source_id"], "extraction_id": "ext_talk",
                              "t": anchors["q2"]["t"]}, "view": {"t": anchors["q2"]["t"]}})
    assert [w["content"]["kind"] for d in desk_state(repository)["desks"] for slot in d["slots"]
            for w in slot["windows"]] == ["video"]


# -- finding 14 (server side already fine): every carried question is reachable, page by page ---------------------


def test_the_carried_list_pages_past_the_first_fifty_and_each_question_takes_its_labels(tmp_path):
    from learnloop.pads import carried

    _paths, repository, _batches = pad_vault(tmp_path)
    for index in range(carried.PAGE_SIZE + 1):
        carried.carry(repository, carried_id=f"cq_{index:03d}", text=f"question {index}?", origin_kind="typed",
                      origin_ref=None, anchor=None, desk_id=None)
    first = carried.listing(repository, which="open", desk_id=None, cursor=None)
    assert len(first["carried"]) == carried.PAGE_SIZE and first["cursor"] and first["shelf_limit"] == 3
    rest = carried.listing(repository, which="open", desk_id=None, cursor=first["cursor"])
    seen = [row["carried_id"] for row in first["carried"] + rest["carried"]]
    assert sorted(seen) == [f"cq_{index:03d}" for index in range(carried.PAGE_SIZE + 1)] and rest["cursor"] is None
    last = rest["carried"][0]
    marked = carried.mark(repository, event_id="e1", carried_id=last["carried_id"], event="let_go",
                          expected_version=last["version"], ref=None)
    assert marked["state"] == "let_go" and marked["carried"] is False


# -- finding 15 (server side already fine): passage marks come from the union read, aliases included ----------


def test_a_pads_link_on_an_older_reading_marks_the_newer_one_from_the_union_alone(tmp_path):
    """passage.union_range places a pad block's link made on another reading of the book through its aliases, with
    the alias status (an exact one, or needs_reanchor for the same place only), with no pad loaded by the client."""

    from learnloop.passage_union.union import union_range
    from tests.desk_helpers import record_alias
    from tests.reader_rd4_helpers import vault

    paths, repository, batches = pad_vault(tmp_path)
    seed_reading(repository, source_id="src_book", revision_id="rev_book", extraction_id="ext_old", spans=["o1", "o2"])
    seed_reading(repository, source_id="src_book", revision_id="rev_book", extraction_id="ext_new",
                 spans=["n1", "n2"])
    record_alias(repository, from_extraction_id="ext_old", from_span_id="o1", to_extraction_id="ext_new",
                 to_span_id="n1")
    record_alias(repository, from_extraction_id="ext_old", from_span_id="o2", to_extraction_id="ext_new",
                 to_span_id="n2", match_kind="geometry_section")
    create_pad(batches)
    batches.pad(PAD, insert("q1", "one", kind="source_quote", provenance="source"),
                insert("q2", "two", kind="source_quote", provenance="source", position="a1"),
                {"op": "link_anchor", "block_id": "q1", "extraction_id": "ext_old", "span_id": "o1",
                 "expected_anchor_head": None},
                {"op": "link_anchor", "block_id": "q2", "extraction_id": "ext_old", "span_id": "o2",
                 "expected_anchor_head": None})
    union = union_range(vault(paths), repository, extraction_id="ext_new", from_span_id="n1", to_span_id="n2")
    assert [[(row["block_id"], row["pad_id"], row["alias"]) for row in span["pad_blocks"]] for span in union["spans"]
            ] == [[("q1", PAD, "exact")], [("q2", PAD, "needs_reanchor")]]

"""The workbench's RPCs (spec §3.4, §18.1): registered, desktop only, params refusing extra fields, replies
versioned and camelCase, and the protocol's refusals as sidecar errors."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from learnloop.db.repositories import Repository
from learnloop_sidecar.errors import SidecarError
from tests.desk_helpers import BOOK, seed_reading
from tests.helpers import create_basic_vault
from tests.reading_path_fixtures import call, context

RD0_RPCS = ("desk.state", "desk.apply", "pad.get", "pad.list", "pad.apply", "passage.union_range",
            "companion.history", "checks.due_for")
MINIMAL = {
    "desk.state": {}, "desk.apply": {"clientId": "c", "seq": 1, "ops": []}, "pad.get": {"padId": "p"},
    "pad.list": {}, "pad.apply": {"clientId": "c", "seq": 1, "padId": "p", "ops": []},
    "passage.union_range": {"extractionId": BOOK, "fromSpanId": "s1", "toSpanId": "s2"},
    "companion.history": {}, "checks.due_for": {},
}


@pytest.fixture
def ctx(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    seed_reading(Repository(paths.sqlite_path), source_id="src_book", revision_id="rev_book", extraction_id=BOOK,
                 spans=["s1", "s2"])
    return context(paths.root)


def test_the_rpcs_are_registered_and_desktop_only():
    from learnloop_mobile.allowlist import ALLOWLIST
    from learnloop_sidecar.handlers.companion import COMPANION_RPCS
    from learnloop_sidecar.handlers.desks import DESK_RPCS
    from learnloop_sidecar.handlers.inline_checks import INLINE_CHECK_RPCS
    from learnloop_sidecar.handlers.pads import PAD_RPCS
    from learnloop_sidecar.handlers.passage_union import PASSAGE_UNION_RPCS
    from learnloop_sidecar.registry import METHOD_REGISTRY

    # RD0's own inline check RPC is ``checks.due_for``; RD7 added the administration protocol's beside it.
    assert DESK_RPCS + PAD_RPCS + PASSAGE_UNION_RPCS + COMPANION_RPCS + INLINE_CHECK_RPCS[:1] == RD0_RPCS
    assert INLINE_CHECK_RPCS[0] == "checks.due_for"
    assert all(name in METHOD_REGISTRY and name not in ALLOWLIST for name in RD0_RPCS)


@pytest.mark.parametrize("name", RD0_RPCS)
def test_params_refuse_an_extra_field(name):
    from learnloop_sidecar.registry import METHOD_REGISTRY

    model = METHOD_REGISTRY[name].params_model
    model.model_validate(MINIMAL[name])
    with pytest.raises(ValidationError):
        model.model_validate({**MINIMAL[name], "unexpected": True})


@pytest.mark.parametrize("name", RD0_RPCS)
def test_every_reply_is_versioned(ctx, name):
    params = MINIMAL[name]
    if name == "pad.get":
        call(ctx, "pad.apply", {"clientId": "c", "seq": 1, "padId": "p", "ops": [{"op": "create_pad", "kind": "named"}]})
    reply = call(ctx, name, params)
    assert reply["version"] == 1


def test_an_op_refuses_an_extra_field_and_an_unknown_op():
    from learnloop_sidecar.registry import METHOD_REGISTRY

    model = METHOD_REGISTRY["desk.apply"].params_model
    with pytest.raises(ValidationError):
        model.model_validate({"clientId": "c", "seq": 1, "ops": [
            {"op": "rename_desk", "deskId": "d", "title": "t", "expectedVersion": 1, "colour": "red"}]})
    with pytest.raises(ValidationError):
        model.model_validate({"clientId": "c", "seq": 1, "ops": [{"op": "erase_ink", "strokeIds": []}]})


def test_desk_apply_speaks_camel_case_and_maps_the_protocols_refusals(ctx):
    reply = call(ctx, "desk.apply", {"clientId": "c", "seq": 1, "ops": [
        {"op": "create_desk", "deskId": "d1", "title": "maps", "position": "a0"},
        {"op": "open_window", "deskId": "d1", "windowId": "w1", "expectedVersion": 1,
         "content": {"kind": "source", "sourceId": "src_book", "extractionId": BOOK, "view": "pdf"}}]})
    assert reply == {"version": 1, "appliedSeq": 1, "results": [{"status": "ok"}, {"status": "ok"}],
                     "versions": [{"deskId": "d1", "version": 2}]}
    state = call(ctx, "desk.state", {})
    window = state["desks"][0]["slots"][0]["windows"][0]
    assert window["content"] == {"kind": "source", "sourceId": "src_book", "extractionId": BOOK, "view": "pdf"}
    assert state["serverSeq"] == [{"clientId": "c", "seq": 1}]
    with pytest.raises(SidecarError) as gap:
        call(ctx, "desk.apply", {"clientId": "c", "seq": 3, "ops": []})
    assert gap.value.code == "seq_gap" and gap.value.details == {"seq": 3, "expected_seq": 2}
    with pytest.raises(SidecarError) as reused:
        call(ctx, "desk.apply", {"clientId": "c", "seq": 1, "ops": []})
    assert reused.value.code == "seq_reused"


def test_pad_get_of_an_unknown_pad_and_a_union_range_of_two_kinds_are_refused(ctx):
    from learnloop_sidecar.registry import METHOD_REGISTRY

    with pytest.raises(SidecarError) as missing:
        call(ctx, "pad.get", {"padId": "nope"})
    assert missing.value.code == "pad_not_found"
    model = METHOD_REGISTRY["passage.union_range"].params_model
    for params in ({"extractionId": BOOK}, {"extractionId": BOOK, "fromSpanId": "s1"},
                   {"extractionId": BOOK, "fromSpanId": "s1", "toSpanId": "s2", "t0": 1, "t1": 2}):
        with pytest.raises(ValidationError):
            model.model_validate(params)
    with pytest.raises(SidecarError) as unknown:
        call(ctx, "passage.union_range", {"extractionId": BOOK, "fromSpanId": "s1", "toSpanId": "zz"})
    assert unknown.value.code == "span_not_found"


def test_companion_history_takes_the_specs_from_and_to(ctx):
    reply = call(ctx, "companion.history", {"from": "2026-05-01", "to": "2026-05-31"})
    assert reply == {"version": 1, "days": [], "cursor": None}


def test_opaque_json_round_trips_with_its_keys_as_stored(ctx):
    """A block's payload, a window's view and an anchor's JSON are the client's: their keys come back as
    stored, never camelCased (``a_b`` and ``aB`` would merge into one key)."""

    opaque = {"a_b": 1, "aB": 2, "nested": {"c_d": [{"e_f": True}]}}
    call(ctx, "pad.apply", {"clientId": "c", "seq": 1, "padId": "p1", "ops": [
        {"op": "create_pad", "kind": "named"},
        {"op": "insert_block", "blockId": "b", "kind": "sketch", "provenance": "learner", "positionKey": "a0",
         "payload": opaque},
        {"op": "link_anchor", "blockId": "b", "extractionId": BOOK, "spanId": "s1", "anchor": opaque,
         "expectedAnchorHead": None}]})
    pad = call(ctx, "pad.get", {"padId": "p1"})
    assert pad["blocks"][0]["payload"] == opaque and pad["anchors"][0]["anchor"] == opaque
    assert "headVersionId" in pad["blocks"][0]  # declared fields stay camelCase
    call(ctx, "desk.apply", {"clientId": "c", "seq": 2, "ops": [
        {"op": "create_desk", "deskId": "d1", "title": "t", "position": "a0"},
        {"op": "open_window", "deskId": "d1", "windowId": "w1", "expectedVersion": 1, "view": opaque,
         "content": {"kind": "pad", "padId": "p1"}}]})
    window = call(ctx, "desk.state", {})["desks"][0]["slots"][0]["windows"][0]
    assert window["view"] == opaque and window["windowId"] == "w1"

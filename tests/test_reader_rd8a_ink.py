"""The learner's ink (spec §10.10, §15.1): ``ink.save`` through the write protocol, the ``erase_ink`` pad op, and the
reads that return an owner's strokes as they stand. Lossless storage, client-minted ids, idempotent retries."""

from __future__ import annotations

import json
import zlib

import pytest
from pydantic import ValidationError

from learnloop.desks.protocol import ProtocolError
from learnloop.pads import ink
from tests.ink_helpers import PEN, STROKES, ink_pad, stroke
from tests.reader_rd4_helpers import PAD, insert, rows


def test_a_save_keeps_every_point_as_sent_compressed_with_its_hash(tmp_path):
    _paths, repository, _batches, client = ink_pad(tmp_path)
    precise = [stroke("p1", (10.123456789, 20.000001), (11.5, 21.25), pressure=0.3333333)]
    reply = client.save("ink_1", precise, block_id="b1", pointer={"pointer_type": "pen", "device_pixel_ratio": 2.0})
    assert reply["ink_id"] == "ink_1" and reply["results"] == [{"status": "ok", "duplicate": False}]
    [(owner_kind, owner_id, kind, encoding, blob, digest, count, meta)] = rows(
        repository, "SELECT owner_kind, owner_id, kind, encoding, strokes_blob, content_hash, stroke_count, "
                    "pointer_meta FROM ink_strokes")
    assert (owner_kind, owner_id, kind, encoding, count) == ("block", "b1", "strokes", "zlib-json-v1", 1)
    assert json.loads(zlib.decompress(blob)) == precise  # lossless: nothing rounded or thinned
    assert digest == ink.content_hash(precise)
    assert json.loads(meta) == {"device_pixel_ratio": 2.0, "pointer_type": "pen"}


def test_a_retried_batch_returns_its_receipt_and_a_resent_ink_id_is_a_no_op(tmp_path):
    _paths, repository, batches, client = ink_pad(tmp_path)
    first = client.save("ink_1", STROKES, block_id="b1")
    # The same batch number again (the receipt was lost): the stored reply, nothing applied.
    again = ink.save_ink(repository, client_id=batches.client_id, seq=batches.seq, owner=ink.InkOwner(block_id="b1"),
                         ink_id="ink_1", strokes=[ink.InkStroke.model_validate(s) for s in STROKES],
                         pointer_meta=ink.PointerMeta.model_validate(PEN))
    assert again == first
    # The same ink in a later batch (the outbox replayed it): a no-op.
    assert client.save("ink_1", STROKES, block_id="b1")["results"] == [{"status": "ok", "duplicate": True}]
    assert rows(repository, "SELECT COUNT(*) FROM ink_strokes") == [(1,)]
    # The same batch number with other strokes is refused whole.
    with pytest.raises(ProtocolError) as refused:
        ink.save_ink(repository, client_id=batches.client_id, seq=batches.seq, owner=ink.InkOwner(block_id="b1"),
                     ink_id="ink_9", strokes=[ink.InkStroke.model_validate(STROKES[0])],
                     pointer_meta=ink.PointerMeta.model_validate(PEN))
    assert refused.value.code == "seq_reused"


def test_ink_shares_the_clients_one_sequence_with_pad_batches(tmp_path):
    _paths, repository, batches, client = ink_pad(tmp_path)
    with pytest.raises(ProtocolError) as gap:
        ink.save_ink(repository, client_id=batches.client_id, seq=batches.seq + 2, owner=ink.InkOwner(block_id="b1"),
                     ink_id="ink_1", strokes=[ink.InkStroke.model_validate(STROKES[0])],
                     pointer_meta=ink.PointerMeta.model_validate(PEN))
    assert gap.value.code == "seq_gap"
    client.save("ink_1", STROKES, block_id="b1")
    reply = batches.pad(PAD, insert("t1", "words", position="a1"))
    assert reply["applied_seq"] == batches.seq == 4  # create, insert, the ink, this batch
    assert rows(repository, "SELECT seq, pad_id FROM pad_op_receipts WHERE seq = 3") == [(3, PAD)]


@pytest.mark.parametrize(("owner", "code"), [
    ({"block_id": "nope"}, "block_not_found"),
    ({"block_id": "t1"}, "not_an_ink_block"),
    ({"annotation_id": "nope"}, "annotation_not_found"),
])
def test_ink_goes_only_to_an_ink_block_or_an_annotation_that_exists(tmp_path, owner, code):
    _paths, repository, batches, client = ink_pad(tmp_path)
    batches.pad(PAD, insert("t1", "words", position="a1"))
    reply = client.save("ink_1", STROKES, **owner)
    assert reply["results"][0]["status"] == "refused" and reply["results"][0]["code"] == code
    assert rows(repository, "SELECT COUNT(*) FROM ink_strokes") == [(0,)]


def test_a_reused_ink_id_or_stroke_id_is_refused(tmp_path):
    _paths, _repository, _batches, client = ink_pad(tmp_path)
    client.save("ink_1", STROKES[:1], block_id="b1")
    assert client.save("ink_1", STROKES[1:2], block_id="b1")["results"][0]["code"] == "ink_id_reused"
    assert client.save("ink_2", STROKES[:1], block_id="b1")["results"][0]["code"] == "stroke_exists"


def test_a_removed_block_takes_no_more_ink(tmp_path):
    _paths, repository, batches, client = ink_pad(tmp_path)
    batches.pad(PAD, {"op": "remove_block", "block_id": "b1", "expected_head": "v0"})
    assert client.save("ink_1", STROKES, block_id="b1")["results"][0]["code"] == "block_removed"


@pytest.mark.parametrize("bad", [
    {"stroke_id": "x", "points": []},
    {"stroke_id": "x", "points": [[1, 2, 0, 1.5, 0, 0]]},
    {"stroke_id": "x", "points": [[1, 2, 0, 0.5, 91, 0]]},
    {"stroke_id": "x", "points": [[1, 2, 0, 0.5]]},
    {"stroke_id": "x", "points": [[float("nan"), 2, 0, 0.5, 0, 0]]},
    {"stroke_id": "", "points": [[1, 2, 0, 0.5, 0, 0]]},
])
def test_a_malformed_stroke_is_refused(bad):
    with pytest.raises(ValidationError):
        ink.InkStroke.model_validate(bad)


def test_touch_never_draws_and_an_owner_is_one_thing():
    with pytest.raises(ValidationError):
        ink.PointerMeta.model_validate({"pointer_type": "touch"})
    with pytest.raises(ValidationError):
        ink.InkOwner.model_validate({"block_id": "b", "annotation_id": "a"})
    with pytest.raises(ValidationError):
        ink.InkOwner.model_validate({})


def test_erasing_tombstones_strokes_and_the_standing_ink_and_its_hash_follow(tmp_path):
    _paths, repository, batches, client = ink_pad(tmp_path)
    client.save("ink_1", STROKES[:2], block_id="b1")
    client.save("ink_2", STROKES[2:], block_id="b1", pointer={"pointer_type": "pen", "device_pixel_ratio": 1.5})
    [before] = ink.ink_for_pad(repository, PAD)
    assert [s["stroke_id"] for s in before["strokes"]] == ["s1", "s2", "s3"]
    assert [s["ink_id"] for s in before["strokes"]] == ["ink_1", "ink_1", "ink_2"]
    assert before["device_pixel_ratio"] == 1.5 and before["transcription"] is None
    reply = batches.pad(PAD, {"op": "erase_ink", "block_id": "b1", "stroke_ids": ["s2"], "erase_id": "er_1"})
    assert reply["results"] == [{"status": "ok", "erase_id": "er_1"}]
    [after] = ink.ink_for_pad(repository, PAD)
    assert [s["stroke_id"] for s in after["strokes"]] == ["s1", "s3"]
    assert after["content_hash"] != before["content_hash"]
    validated = [ink.InkStroke.model_validate(STROKES[index]) for index in (0, 2)]
    assert after["content_hash"] == ink.strokes_hash(
        [{"stroke_id": s.stroke_id, "points": [list(point) for point in s.points]} for s in validated])
    # The rows stay (append-only): the erase is a row of its own.
    assert rows(repository, "SELECT ink_id, kind, stroke_count FROM ink_strokes ORDER BY rowid") == [
        ("ink_1", "strokes", 2), ("ink_2", "strokes", 1), ("er_1", "erase", 1)]


def test_an_erase_names_standing_strokes_of_an_ink_block_in_this_pad(tmp_path):
    _paths, _repository, batches, client = ink_pad(tmp_path)
    client.save("ink_1", STROKES, block_id="b1")
    batches.pad(PAD, {"op": "erase_ink", "block_id": "b1", "stroke_ids": ["s1"]})
    reply = batches.pad(PAD, {"op": "erase_ink", "block_id": "b1", "stroke_ids": ["s1"]},
                        {"op": "erase_ink", "block_id": "b1", "stroke_ids": ["zz"]},
                        insert("t1", "words", position="a1"),
                        {"op": "erase_ink", "block_id": "t1", "stroke_ids": ["s2"]})
    assert [(r["status"], r.get("code")) for r in reply["results"]] == [
        ("refused", "stroke_not_found"), ("refused", "stroke_not_found"), ("ok", None),
        ("refused", "not_an_ink_block")]
    batches.pad("pad_2", {"op": "create_pad", "kind": "ink"})
    other = batches.pad("pad_2", {"op": "erase_ink", "block_id": "b1", "stroke_ids": ["s2"]})
    assert other["results"][0]["code"] == "block_not_in_pad"


def test_a_margin_notes_ink_is_listed_with_its_source(tmp_path):
    _paths, repository, batches, client = ink_pad(tmp_path)
    kept = repository.create_annotation(source_id="src_book")
    other = repository.create_annotation(source_id="src_other")
    client.save("ink_a", STROKES[:1], annotation_id=kept)
    client.save("ink_b", STROKES[1:2], annotation_id=other)
    [owner] = ink.ink_for_source(repository, "src_book")
    assert (owner["owner_kind"], owner["owner_id"], [s["stroke_id"] for s in owner["strokes"]]) == (
        "annotation", kept, ["s1"])
    # Its receipt is filed under no pad.
    assert rows(repository, "SELECT pad_id FROM pad_op_receipts WHERE seq = ?", (batches.seq - 1,)) == [("",)]
    assert ink.ink_for_source(repository, "src_none") == []
    with pytest.raises(ink.InkError):
        ink.ink_for_pad(repository, "pad_none")


def test_a_pad_lists_only_its_standing_ink_blocks_with_ink(tmp_path):
    _paths, repository, batches, client = ink_pad(tmp_path)
    batches.pad(PAD, insert("b2", "", kind="ink", provenance="ink_transcription", position="a1"),
                insert("b3", "", kind="ink", provenance="ink_transcription", position="a2", version_id="v3"))
    client.save("ink_1", STROKES[:1], block_id="b1")
    client.save("ink_3", STROKES[1:2], block_id="b3")
    batches.pad(PAD, {"op": "remove_block", "block_id": "b3", "expected_head": "v3"})
    assert [owner["owner_id"] for owner in ink.ink_for_pad(repository, PAD)] == ["b1"]

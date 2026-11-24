"""RD8a's fix round, the backend half: a stale reading never replaces a newer one, erased handwriting takes its
automatic transcription with it, lifting an ink line out keeps its handwriting, and a cached reading keeps its
reason. Every model is a fake."""

from __future__ import annotations

from learnloop.db.stores import pad_reads
from learnloop.pads import emission, ink
from learnloop.pads import ink_transcribe as reading
from learnloop.tutor.ai_contracts import LearnerGap
from tests.ink_helpers import STROKES, ImageReader, ink_pad, reads_as
from tests.reader_rd4_helpers import PAD, edit, gap_clients, pad_reversals, read_queued, vault

BELIEF = LearnerGap(kind="misconception", prerequisite_name=None, prerequisite_line=None,
                    belief_statement="The square root of a sum is the sum of the square roots.")


def _head(repository, block_id="b1"):
    with repository.connection() as connection:
        return pad_reads.head(connection, block_id)


def _read(paths, repository, prepared, text):
    result = reading.transcribe(vault(paths), repository, prepared, client=ImageReader(reads_as(text)))
    emission.settle_blocks(vault(paths), repository, [prepared.owner_id])
    return result


def test_a_reading_of_strokes_that_changed_meanwhile_is_kept_but_never_replaces_the_newer_one(tmp_path):
    paths, repository, _batches, client = ink_pad(tmp_path)
    client.save("ink_1", STROKES[:2], block_id="b1")
    older = reading.prepare(repository, "ink_1")
    client.save("ink_2", STROKES[2:], block_id="b1")
    newer = reading.prepare(repository, "ink_2")
    second = _read(paths, repository, newer, "the whole line")
    first = _read(paths, repository, older, "half a line")
    assert (second["applied"], first["applied"], first["reason"]) == (True, False, "strokes_changed")
    assert _head(repository)["body_md"] == "the whole line"
    # Kept (the same strokes are never read twice), and a retry still says why it stands aside.
    again = reading.transcribe(vault(paths), repository, older, client=ImageReader(reads_as("x")))
    assert (again["applied"], again["reason"]) == (False, "strokes_changed")


def test_a_cached_reading_beside_the_learners_correction_keeps_its_reason(tmp_path):
    paths, repository, batches, client = ink_pad(tmp_path)
    client.save("ink_1", STROKES[:2], block_id="b1")
    first = _read(paths, repository, reading.prepare(repository, "ink_1"), "a")
    batches.pad(PAD, edit("b1", first["head_version_id"], "mine", "v_fix"))
    client.save("ink_2", STROKES[2:], block_id="b1")
    prepared = reading.prepare(repository, "ink_2")
    kept = _read(paths, repository, prepared, "b")
    assert (kept["applied"], kept["reason"]) == (False, "kept_your_correction")
    again = reading.transcribe(vault(paths), repository, prepared, client=ImageReader(reads_as("c")))
    assert (again["applied"], again["reason"]) == (False, "kept_your_correction")


def test_erasing_handwriting_takes_its_automatic_transcription_and_what_was_read_from_it(tmp_path):
    paths, repository, batches, client = ink_pad(tmp_path)
    client.save("ink_1", STROKES, block_id="b1")
    first = _read(paths, repository, reading.prepare(repository, "ink_1"), "$\\sqrt{a+b} = \\sqrt{a} + \\sqrt{b}$")
    read_queued(paths, repository, gap_clients(BELIEF)[0])
    reply = batches.pad(PAD, {"op": "erase_ink", "block_id": "b1", "stroke_ids": ["s1", "s2", "s3"], "version_id": "v_erased"})
    assert reply["results"][0]["status"] == "ok" and reply["heads"] == [{"block_id": "b1", "head_version_id": "v_erased"}]
    head = _head(repository)
    assert (head["body_md"], head["provenance"], "ink_transcription" in head["payload"]) == ("", "ink_transcription", False)
    emission.settle_blocks(vault(paths), repository, ["b1"])
    assert pad_reversals(repository) == {first["head_version_id"]: "superseded"}


def test_a_partial_erase_leaves_the_words_until_the_line_is_read_again(tmp_path):
    paths, repository, batches, client = ink_pad(tmp_path)
    client.save("ink_1", STROKES, block_id="b1")
    first = _read(paths, repository, reading.prepare(repository, "ink_1"), "a + b")
    reply = batches.pad(PAD, {"op": "erase_ink", "block_id": "b1", "stroke_ids": ["s3"]})
    assert reply["heads"] == [] and "standing" not in reply["results"][0]
    assert _head(repository)["version_id"] == first["head_version_id"]
    [listed] = ink.ink_for_pad(repository, PAD)
    assert listed["transcription"]["current"] is False


def test_erasing_handwriting_keeps_the_learners_own_words(tmp_path):
    paths, repository, batches, client = ink_pad(tmp_path)
    client.save("ink_1", STROKES, block_id="b1")
    first = _read(paths, repository, reading.prepare(repository, "ink_1"), "a")
    batches.pad(PAD, edit("b1", first["head_version_id"], "my words", "v_fix"))
    reply = batches.pad(PAD, {"op": "erase_ink", "block_id": "b1", "stroke_ids": ["s1", "s2", "s3"]})
    assert reply["heads"] == []
    assert (_head(repository)["body_md"], _head(repository)["version_id"]) == ("my words", "v_fix")


def test_lifting_an_ink_line_out_keeps_its_handwriting_and_its_reading(tmp_path):
    paths, repository, batches, client = ink_pad(tmp_path, kind="running")
    client.save("ink_1", STROKES, block_id="b1")
    first = _read(paths, repository, reading.prepare(repository, "ink_1"), "a + b")
    batches.pad(PAD, {"op": "lift_out", "block_id": "b1", "expected_head": first["head_version_id"], "new_pad_id": "pad_2",
                      "new_block_id": "b9", "title": "lifted"})
    [moved] = ink.ink_for_pad(repository, "pad_2")
    assert moved["owner_id"] == "b9" and [s["stroke_id"] for s in moved["strokes"]] == ["s1", "s2", "s3"]
    assert ink.ink_for_pad(repository, PAD) == []
    reader = ImageReader(reads_as("paid again"))
    again = reading.transcribe(vault(paths), repository, reading.prepare(repository, moved["strokes"][0]["ink_id"]), client=reader)
    assert reader.requests == [] and again["latex_md"] == "a + b"
    assert (again["applied"], again["reason"]) == (True, None)

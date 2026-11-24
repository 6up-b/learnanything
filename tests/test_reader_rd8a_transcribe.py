"""Reading the learner's ink (spec §10.10 "Transcription", §10.11): one image of an owner's standing strokes read by
GLM-OCR, the reading kept once per owner and strokes (a retry spends nothing), written into an ink block as its next
version (provenance ``ink_transcription``) unless the learner's words stand, and emitted as learner text marked as
transcribed: corrections supersede it, a removal retracts it. GLM-OCR is faked at its transport seam (the local
backend here; the hosted one in ``tests/test_reader_ink_glm_ocr.py``); no live call."""

from __future__ import annotations

import base64

import pytest

from learnloop.db.stores import learner_gaps as gap_store
from learnloop.ingest.extractors.glm_ocr import LAYOUT_MODEL, RECOGNITION_MODEL
from learnloop.pads import emission
from learnloop.pads import ink_transcribe as reading
from learnloop.substrate.passage_spans import rebuild_learner_text_gap_spans
from learnloop.tutor.ai_contracts import LearnerGap
from tests.desk_helpers import seed_reading
from tests.ink_helpers import STROKES, glm_local, ink_pad
from tests.reader_rd4_helpers import (
    PAD,
    apply_and_settle,
    edit,
    gap_clients,
    pad_gaps,
    pad_jobs,
    pad_reversals,
    read_queued,
    rows,
    vault,
)

BELIEF = LearnerGap(kind="misconception", prerequisite_name=None, prerequisite_line=None,
                    belief_statement="The square root of a sum is the sum of the square roots.")


def _read(paths, repository, ink_id="ink_1"):
    prepared = reading.prepare(repository, ink_id)
    result = reading.transcribe(vault(paths), repository, prepared)
    emission.settle_blocks(vault(paths), repository, [prepared.owner_id] if prepared.owner_kind == "block" else [])
    return result


def _head(repository, block_id="b1"):
    from learnloop.db.stores import pad_reads

    with repository.connection() as connection:
        return pad_reads.head(connection, block_id)


def test_one_image_of_the_standing_strokes_is_sent_alone(tmp_path, monkeypatch):
    paths, repository, _batches, client = ink_pad(tmp_path)
    ocr = glm_local(monkeypatch, paths.root, r"$\sqrt{x}$")
    client.save("ink_1", STROKES[:2], block_id="b1")
    client.save("ink_2", STROKES[2:], block_id="b1")
    _read(paths, repository, "ink_2")  # any of the owner's inks reads all of its standing strokes
    [request] = ocr.requests
    assert set(request.body) == {"images"}  # the image, nothing else
    [image] = request.body["images"]
    prepared = reading.prepare(repository, "ink_1")
    assert image == "data:image/png;base64," + base64.b64encode(reading.render(prepared)).decode()


def test_the_reading_becomes_the_blocks_next_version_and_is_kept_with_its_provenance(tmp_path, monkeypatch):
    paths, repository, _batches, client = ink_pad(tmp_path)
    glm_local(monkeypatch, paths.root, r"$\sqrt{a+b}$")
    client.save("ink_1", STROKES, block_id="b1")
    result = _read(paths, repository)
    assert (result["latex_md"], result["confidence_label"], result["applied"]) == (r"$\sqrt{a+b}$", "may_be_wrong",
                                                                                     True)
    head = _head(repository)
    assert (head["body_md"], head["provenance"], head["supersedes_id"]) == (r"$\sqrt{a+b}$", "ink_transcription", "v0")
    assert head["version_id"] == result["head_version_id"]
    assert head["payload"]["ink_transcription"] == {
        "transcription_id": result["transcription_id"], "content_hash": result["content_hash"],
        "confidence_label": "may_be_wrong"}
    assert rows(repository, "SELECT owner_kind, owner_id, content_hash, task, provider, model, prompt_version "
                            "FROM ink_transcriptions") == [
        ("block", "b1", result["content_hash"], "ink_transcription", "glm-ocr-local", RECOGNITION_MODEL,
         f"glm_ocr:{RECOGNITION_MODEL}+{LAYOUT_MODEL}+local")]


def test_the_same_strokes_are_read_once_and_a_retry_spends_nothing(tmp_path, monkeypatch):
    paths, repository, batches, client = ink_pad(tmp_path)
    ocr = glm_local(monkeypatch, paths.root, "x")
    client.save("ink_1", STROKES, block_id="b1")
    first = _read(paths, repository)
    again = _read(paths, repository)
    assert again == first and ocr.reached == 1
    # Kept by the strokes, not by the request: a reader that would answer otherwise is never asked.
    ocr.text = "y"
    assert _read(paths, repository) == first and ocr.reached == 1
    # Other strokes are another reading.
    batches.pad(PAD, {"op": "erase_ink", "block_id": "b1", "stroke_ids": ["s3"]})
    other = _read(paths, repository)
    assert other["content_hash"] != first["content_hash"] and ocr.reached == 2


def test_no_writing_read_is_said_so(tmp_path, monkeypatch):
    paths, repository, _batches, client = ink_pad(tmp_path)
    glm_local(monkeypatch, paths.root, "   ")
    client.save("ink_1", STROKES, block_id="b1")
    result = _read(paths, repository)
    assert (result["latex_md"], result["confidence_label"]) == ("", "nothing_read")


def test_the_learners_correction_is_never_overwritten(tmp_path, monkeypatch):
    paths, repository, batches, client = ink_pad(tmp_path)
    ocr = glm_local(monkeypatch, paths.root, "$\\sqrt{x}$")
    client.save("ink_1", STROKES[:2], block_id="b1")
    first = _read(paths, repository)
    batches.pad(PAD, edit("b1", first["head_version_id"], "$\\sqrt{y}$", "v_fix"))
    assert _head(repository)["provenance"] == "learner_correction"
    # More strokes, a new reading: kept and returned, the learner's words stand.
    client.save("ink_2", STROKES[2:], block_id="b1")
    ocr.text = "$\\sqrt{x}.$"
    second = _read(paths, repository)
    assert (second["applied"], second["reason"], second["head_version_id"]) == (False, "kept_your_correction",
                                                                                "v_fix")
    assert _head(repository)["body_md"] == "$\\sqrt{y}$"


def test_a_removed_blocks_ink_is_not_read(tmp_path):
    paths, repository, batches, client = ink_pad(tmp_path)
    client.save("ink_1", STROKES, block_id="b1")
    batches.pad(PAD, {"op": "remove_block", "block_id": "b1", "expected_head": "v0"})
    with pytest.raises(reading.ink_core.InkError) as gone:
        reading.prepare(repository, "ink_1")
    assert gone.value.code == "block_removed"
    batches.pad("pad_2", {"op": "create_pad", "kind": "ink"},
                {"op": "insert_block", "block_id": "b9", "kind": "ink", "provenance": "ink_transcription",
                 "position_key": "a0"})
    client.save("ink_9", STROKES[:1], block_id="b9")
    batches.pad("pad_2", {"op": "erase_ink", "block_id": "b9", "stroke_ids": ["s1"]})
    with pytest.raises(reading.ink_core.InkError) as empty:
        reading.prepare(repository, "ink_9")
    assert empty.value.code == "nothing_to_read"
    with pytest.raises(reading.ink_core.InkError):
        reading.prepare(repository, "ink_none")


def test_a_margin_notes_reading_is_kept_and_returned_never_written_into_the_note(tmp_path, monkeypatch):
    paths, repository, _batches, client = ink_pad(tmp_path)
    glm_local(monkeypatch, paths.root, "why $n^2$?")
    note = repository.create_annotation(source_id="src_book")
    client.save("ink_a", STROKES, annotation_id=note)
    result = _read(paths, repository, "ink_a")
    assert (result["owner_kind"], result["latex_md"], result["applied"], result["head_version_id"]) == (
        "annotation", "why $n^2$?", False, None)
    from learnloop.pads import ink

    [owner] = ink.ink_for_source(repository, "src_book")
    assert owner["transcription"]["latex_md"] == "why $n^2$?" and owner["transcription"]["current"] is True


def test_a_transcription_is_learner_text_marked_transcribed_and_a_correction_supersedes_it(tmp_path, monkeypatch):
    paths, repository, batches, client = ink_pad(tmp_path)
    glm_local(monkeypatch, paths.root, "$\\sqrt{a+b} = \\sqrt{a} + \\sqrt{b}$")
    client.save("ink_1", STROKES, block_id="b1")
    first = _read(paths, repository)
    version = first["head_version_id"]
    assert pad_jobs(repository) == {version: "queued"}
    with repository.connection() as connection:
        snapshot = gap_store.job_for_source(connection, "pad_text", version)["payload"][gap_store.PAD_TEXT_SNAPSHOT]
    assert (snapshot["text"], snapshot["transcribed"]) == ("$\\sqrt{a+b} = \\sqrt{a} + \\sqrt{b}$", True)
    clients, _llm = gap_clients(BELIEF)
    read_queued(paths, repository, clients)
    assert version in pad_gaps(repository)
    apply_and_settle(paths, repository, batches, PAD, edit("b1", version, "$\\sqrt{a+b} \\ne \\sqrt{a}+\\sqrt{b}$",
                                                           "v_fix"))
    assert pad_reversals(repository) == {version: "superseded"}
    assert pad_jobs(repository)["v_fix"] == "queued"
    with repository.connection() as connection:
        fixed = gap_store.job_for_source(connection, "pad_text", "v_fix")["payload"][gap_store.PAD_TEXT_SNAPSHOT]
    assert fixed["transcribed"] is True  # still the learner's handwriting, corrected by them


def test_a_removed_ink_block_retracts_its_transcriptions_gaps(tmp_path, monkeypatch):
    paths, repository, batches, client = ink_pad(tmp_path)
    glm_local(monkeypatch, paths.root, "$\\sqrt{a+b} = \\sqrt{a} + \\sqrt{b}$")
    client.save("ink_1", STROKES, block_id="b1")
    first = _read(paths, repository)
    read_queued(paths, repository, gap_clients(BELIEF)[0])
    apply_and_settle(paths, repository, batches, PAD, {"op": "remove_block", "block_id": "b1",
                                                       "expected_head": first["head_version_id"]})
    assert pad_reversals(repository) == {first["head_version_id"]: "retracted"}


def test_a_linked_ink_lines_gap_is_placed_by_its_passage_and_live_equals_rebuild(tmp_path, monkeypatch):
    paths, repository, batches, client = ink_pad(tmp_path)
    glm_local(monkeypatch, paths.root, "$\\sqrt{a+b}$ splits?")
    seed_reading(repository, source_id="src_book", revision_id="rev_book", extraction_id="ext_book",
                 spans=["s1", "s2"], texts={"s1": "Roots.", "s2": "Sums."})
    batches.pad(PAD, {"op": "link_anchor", "block_id": "b1", "extraction_id": "ext_book", "span_id": "s1",
                      "expected_anchor_head": None})
    client.save("ink_1", STROKES, block_id="b1")
    first = _read(paths, repository)
    with repository.connection() as connection:
        snapshot = gap_store.job_for_source(connection, "pad_text", first["head_version_id"])["payload"][
            gap_store.PAD_TEXT_SNAPSHOT]
    assert snapshot["passages"] == [["ext_book", "s1"]]
    read_queued(paths, repository, gap_clients()[0])
    query = "SELECT gap_id, extraction_id, span_id, role, quality FROM learner_text_gap_spans ORDER BY 1, 2, 3"
    live = rows(repository, query)
    assert [row[1:3] for row in live] == [("ext_book", "s1")]
    rebuild_learner_text_gap_spans(vault(paths), repository)
    assert rows(repository, query) == live


def test_ink_on_a_page_is_never_read_nor_learner_text(tmp_path):
    from tests.desk_helpers import seed_reading

    paths, repository, _batches, client = ink_pad(tmp_path)
    seed_reading(repository, source_id="src_book", revision_id="rev_book", extraction_id="ext_book", spans=["s1"],
                 texts={"s1": "Kernels."})
    client.save("ink_p", STROKES, extraction_id="ext_book")
    with pytest.raises(reading.ink_core.InkError) as refused:
        reading.prepare(repository, "ink_p")
    assert refused.value.code == "not_read"
    # Nothing turns it into learner text: no gap job, and a full reconcile of the pads emits nothing.
    assert emission.reconcile(vault(paths), repository).queued == []
    assert rows(repository, "SELECT COUNT(*) FROM learner_text_gap_jobs") == [(0,)]
    assert rows(repository, "SELECT COUNT(*) FROM ink_transcriptions") == [(0,)]

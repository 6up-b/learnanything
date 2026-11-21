"""A first set of questions from the part of a section read: a topic qualifies once every passage it cites has been
seen by the learner's own reading, before the section is finished (owner's decision, 2026-11-20).

The book (``tests/part_read_helpers.py``) is added and built through Add with the house fakes; its first chapter has
six paragraphs, P1..P6, and its build applies topics citing known paragraphs: the house topic and ``lo_early`` lie
wholly before a stop after P4, ``lo_straddle`` (P3, P5) straddles it, ``lo_late`` (P6) lies after it, ``lo_cross``
cites P2 and the second chapter's Q1. The learner reads through the real progress report; the questions' writer is
a fake that counts its calls and keeps the prompts it was sent.
"""

from __future__ import annotations

import json

import pytest

from learnloop.ai.execution import ModelCheckpoint
from learnloop.reader.part_read import topic_coverage
from learnloop.vault.loader import load_vault
from learnloop.vault.paths import VaultPaths
from learnloop.vault.yaml_io import read_yaml, write_yaml
from learnloop_sidecar.context import SidecarContext

from tests.part_read_helpers import (
    PARAGRAPH_WORD, SeenWriter, book_ctx, build, build_until_synthesis, drain,
)
from tests.ux_phase1_add_source_helpers import call

BEFORE_THE_STOP = {"lo_diagonalize_symmetric", "lo_early"}
STOP = ("P1", "P2", "P3", "P4")


@pytest.fixture(autouse=True)
def isolated_config(tmp_path, monkeypatch):
    monkeypatch.setenv("LEARNLOOP_CONFIG_DIR", str(tmp_path / "config"))
    monkeypatch.delenv("LEARNLOOP_AI_PROVIDER", raising=False)


@pytest.fixture
def writer():
    return SeenWriter()


@pytest.fixture
def book(tmp_path, writer):
    built = book_ctx(tmp_path, writer=writer)
    build(built)
    return built


def _section_row(book, name):
    section, _span = book.spans()[name]
    return book.repo.reader_section_progress_row(book.extraction_id, section)


def _asked(writer) -> list[str]:
    return [topic for call_topics in writer.calls for topic in call_topics]


def _frozen_requests(book) -> dict[str, dict]:
    """Each claimed topic's frozen request (``<its key>:requests``), as saved before its first call."""

    return {row["learning_object_id"]: ModelCheckpoint(book.repo, f"{row['work_key']}:requests", "authoring_requests",
                                                       dict).load()
            for row in book.claims()}


def _unseen_words(*seen: str) -> set[str]:
    return {word for name, word in PARAGRAPH_WORD.items() if name not in seen}


# -- the stopping point ---------------------------------------------------------------------------------------


def test_before_the_finish_only_the_topics_read_whole_get_their_first_set(book, writer):
    reply = book.read(*STOP)

    assert book.claimed() == {topic: "part_read" for topic in BEFORE_THE_STOP}
    assert sorted(_asked(writer)) == sorted(BEFORE_THE_STOP)
    # The section is not finished and the reply is a progress report's: the Reader's finish is unchanged.
    assert _section_row(book, "P1")["completed_at"] is None
    assert (reply["enqueuedGeneration"], reply["batchId"], reply["waitingForBuild"]) == (False, None, False)
    assert reply["progress"]["generationBatchId"] == "topic_managed"
    questions = book.questions()
    assert questions["count"] == 2
    assert set(questions["itemIds"]) == {f"pi_{topic}" for topic in BEFORE_THE_STOP}
    assert questions["partRead"] == questions["sections"] == ["1-eigenvalues"]
    assert "readFurther" not in questions and "owed" not in questions and "beforeBuild" not in questions


def test_the_grounding_quotes_no_passage_the_learner_has_not_seen(book, writer):
    book.read(*STOP)

    spans = book.spans()
    seen = {spans[name][1] for name in STOP}
    unseen_words = _unseen_words(*STOP)
    frozen = _frozen_requests(book)
    assert set(frozen) == BEFORE_THE_STOP
    for topic, request in frozen.items():
        bundles = [ref for ref in request["context"]["source_refs"] if topic in ref.get("learning_object_ids", [])]
        assert bundles, topic
        assert {span for ref in bundles for span in ref["span_ids"]} <= seen
        text = repr(request)
        assert not [word for word in unseen_words if word in text], topic
    for row in book.claims():
        assert set(json.loads(row["passage_ids_json"])) <= seen
    # What the model was sent: no word of a paragraph the learner has not seen, in any request.
    assert len(writer.prompts) == 2
    for prompt in writer.prompts:
        assert not [word for word in unseen_words if word in prompt]
    # lo_early cites P1 and P2; its neighbours P3 and P4 are seen, so they are its context; P5 is not.
    early = next(ref for ref in frozen["lo_early"]["context"]["source_refs"] if "lo_early" in ref["learning_object_ids"])
    assert early["span_ids"] == [spans[name][1] for name in STOP]


def test_repeated_progress_reports_claim_nothing_twice_and_send_nothing_twice(book, writer):
    book.read(*STOP)
    batches = {row["batch_id"] for row in book.claims()}

    for _ in range(3):
        book.read(*STOP)
        book.read("P3")
        book.questions()
        call(book.ctx, "reader.get_progress", {"extractionId": book.extraction_id})

    assert len(book.claims()) == 2
    assert {row["batch_id"] for row in book.claims()} == batches
    assert sorted(_asked(writer)) == sorted(BEFORE_THE_STOP)


def test_the_later_finish_writes_only_the_remaining_topics(book, writer):
    book.read(*STOP)
    first = sorted(_asked(writer))

    done = book.finish("P1")

    assert done["enqueuedGeneration"] is True
    assert book.claimed() == {**{topic: "part_read" for topic in BEFORE_THE_STOP},
                              "lo_straddle": "section_finished", "lo_late": "section_finished",
                              "lo_cross": "section_finished"}
    asked = _asked(writer)
    assert sorted(asked[:2]) == first
    assert sorted(asked[2:]) == ["lo_cross", "lo_late", "lo_straddle"]
    assert len(asked) == len(set(asked))
    questions = book.questions()
    assert questions["count"] == 5
    assert questions["sections"] == ["1-eigenvalues"]
    assert "partRead" not in questions  # finished now: its questions are a finished section's
    # Finishing again, and reading again, claims and sends nothing more.
    book.finish("P1")
    book.read(*STOP)
    assert len(_asked(writer)) == 5


def test_reading_on_and_finishing_during_a_blocked_call_adds_claims_and_leaves_the_frozen_work_alone(book, writer):
    events = []

    def during_the_first_call():
        if len(writer.calls) == 1:
            book.read("P5")  # lo_straddle's passages are all seen now
            events.append(dict(book.claimed()))
            book.finish("P1")  # the rest of the section
            events.append(dict(book.claimed()))

    writer.before = during_the_first_call
    book.read(*STOP)
    build(book)

    assert events[0] == {**{topic: "part_read" for topic in BEFORE_THE_STOP}, "lo_straddle": "part_read"}
    assert events[1] == {**events[0], "lo_late": "section_finished", "lo_cross": "section_finished"}
    asked = _asked(writer)
    assert sorted(asked) == sorted(["lo_diagonalize_symmetric", "lo_early", "lo_straddle", "lo_late", "lo_cross"])
    # The first wave's requests were frozen before its first call: P5, seen during it, is in none of them.
    frozen = _frozen_requests(book)
    for topic in BEFORE_THE_STOP:
        assert PARAGRAPH_WORD["P5"] not in repr(frozen[topic])
    assert PARAGRAPH_WORD["P5"] in repr(frozen["lo_straddle"])
    assert PARAGRAPH_WORD["P6"] not in repr(frozen["lo_straddle"])
    assert book.questions()["count"] == 5


def test_a_topic_citing_another_section_waits_for_that_sections_passage_too(book, writer):
    book.read("P1", "P2")
    assert "lo_cross" not in book.claimed()

    book.read("Q1")

    assert book.claimed()["lo_cross"] == "part_read"
    assert _asked(writer).count("lo_cross") == 1
    spans = book.spans()
    request = _frozen_requests(book)["lo_cross"]
    bundles = [ref for ref in request["context"]["source_refs"] if "lo_cross" in ref["learning_object_ids"]]
    assert {span for ref in bundles for span in ref["span_ids"]} == {spans[name][1] for name in ("P1", "P2", "Q1")}
    assert not [word for word in _unseen_words("P1", "P2", "Q1") if word in repr(request)]


# -- the build finishing after the learner left; the phone ----------------------------------------------------


def test_a_learner_who_left_while_the_build_ran_gets_the_first_set_when_it_finishes(tmp_path, writer):
    book = book_ctx(tmp_path, writer=writer)
    build_until_synthesis(book)

    book.read(*STOP, run=False)

    assert book.claims() == []  # no topic is in yet
    from learnloop.content.pipeline.add_source import reading_questions

    assert reading_questions(book.repo, load_vault(book.ctx.vault_root), book.source_id)["before_build"] == [
        "1-eigenvalues"]
    assert writer.calls == []

    assert drain(book.ctx, 1) == 1  # the build's synthesis applies its topics; nothing else is read or reported
    assert book.claimed() == {topic: "part_read" for topic in BEFORE_THE_STOP}
    build(book)
    assert sorted(_asked(writer)) == sorted(BEFORE_THE_STOP)
    questions = book.questions()
    assert questions["count"] == 2 and "beforeBuild" not in questions


def test_reading_on_the_phone_is_saved_there_and_its_first_set_is_written_by_the_desktop(book, writer):
    phone = SidecarContext()
    phone.load_secondary(book.ctx.vault_root)
    spans = book.spans()

    call(phone, "reader.mark_section_progress",
         {"extractionId": book.extraction_id, "sectionId": spans["P1"][0], "spansSeen": 4, "spanCount": 6,
          "seenSpanIds": [spans[name][1] for name in STOP]})

    assert book.claims() == [] and writer.calls == []
    on_phone = next(card for card in call(phone, "get_source_library", {})["sources"]
                    if card["sourceId"] == book.source_id)["statusLine"]["questions"]
    assert on_phone["owed"] == ["1-eigenvalues"]
    assert book.claims() == []

    book.questions()  # the desktop's next read of the books (or its start, or the Reader opening the book)

    assert book.claimed() == {topic: "part_read" for topic in BEFORE_THE_STOP}
    assert sorted(_asked(writer)) == sorted(BEFORE_THE_STOP)


def test_the_desktop_claims_the_phones_reading_when_it_starts(book, writer):
    phone = SidecarContext()
    phone.load_secondary(book.ctx.vault_root)
    spans = book.spans()
    call(phone, "reader.mark_section_progress",
         {"extractionId": book.extraction_id, "sectionId": spans["P1"][0], "spansSeen": 4, "spanCount": 6,
          "seenSpanIds": [spans[name][1] for name in STOP]})

    from learnloop_sidecar.section_questions import drain_owed_section_questions

    book.ctx.reload(maintenance=False)  # the desktop starts: its vault is read anew
    assert drain_owed_section_questions(book.ctx, book.ctx.vault, book.ctx.repository) == 1  # what its start runs
    assert book.claimed() == {topic: "part_read" for topic in BEFORE_THE_STOP}


def test_a_section_finished_on_the_phone_after_its_part_read_claims_only_the_rest_on_the_desktop(book, writer):
    book.read(*STOP)
    phone = SidecarContext()
    phone.load_secondary(book.ctx.vault_root)
    section = book.spans()["P1"][0]

    call(phone, "reader.mark_section_progress", {"extractionId": book.extraction_id, "sectionId": section,
                                                  "spansSeen": 6, "spanCount": 6, "completed": True})

    assert _section_row(book, "P1")["generation_batch_id"] == "deferred_to_primary"
    book.questions()
    assert book.claimed() == {**{topic: "part_read" for topic in BEFORE_THE_STOP},
                              "lo_straddle": "section_finished", "lo_late": "section_finished",
                              "lo_cross": "section_finished"}
    assert _section_row(book, "P1")["generation_batch_id"] == "topic_managed"
    assert len(_asked(writer)) == len(set(_asked(writer))) == 5


# -- what Today says -------------------------------------------------------------------------------------------


def test_reading_that_completes_no_topic_says_read_further(book, writer):
    book.read("P3", "P4")

    assert book.claims() == []
    questions = book.questions()
    assert questions["readFurther"] == ["1-eigenvalues"]
    assert questions["count"] == 0 and "partRead" not in questions


# -- what qualifies, and what does not -------------------------------------------------------------------------


def _cite_more(book, topic, *refs):
    """Add references to a topic's own provenance, as a build or an edit would leave them."""

    vault = load_vault(book.ctx.vault_root)
    learning_object = vault.learning_objects[topic]
    path = VaultPaths(vault.root, vault.config).learning_object_path(learning_object.subjects[0], topic)
    data = read_yaml(path)
    data["provenance"]["source_refs"].extend(refs)
    write_yaml(path, data)
    book.ctx.reload(maintenance=False)


def _ref(book, locator=None, **fields):
    return {"ref_type": "canonical_source", "ref_id": book.source_id, "source_id": book.source_id,
            "locator": locator, **fields}


def _coverage(book, topic):
    return topic_coverage(load_vault(book.ctx.vault_root), book.repo, book.extraction_id, [topic])[topic]


def test_a_reference_that_cannot_be_resolved_exactly_is_never_read(book, writer):
    _cite_more(book, "lo_early", _ref(book, f"span:{book.extraction_id}/no_such_passage"))

    book.read("P1", "P2", "P3", "P4", "P5", "P6")

    assert "lo_early" not in book.claimed()
    assert _coverage(book, "lo_early").reason == "unresolved"
    # An ambiguous quote (every paragraph says it) resolves to no one passage either.
    _cite_more(book, "lo_late", _ref(book, None, quote="the characteristic polynomial of a square matrix"))
    assert _coverage(book, "lo_late").reason == "unresolved"


def test_a_held_out_passage_keeps_its_topic_for_the_finish(book, writer):
    from tests.reread_safety_helpers import _made_on

    run = book.repo.get_extraction_run(book.extraction_id)
    book.repo.upsert_unit_selection(extraction_id=book.extraction_id, source_id=book.source_id,
                                    revision_id=run["revision_id"], selected_unit_ids=["u1", "u2"],
                                    exam_use_modes={"u2": "held_out_evaluation"},
                                    exam_paper_metadata=_made_on(book.extraction_id, run["revision_id"]))

    book.read("P1", "P2", "Q1")

    assert "lo_cross" not in book.claimed()
    assert _coverage(book, "lo_cross").reason == "held_out"
    assert book.claimed() == {topic: "part_read" for topic in BEFORE_THE_STOP}


def test_a_topic_citing_another_book_needs_that_books_passages_seen_too(book, writer, tmp_path):
    from tests.mobile_v4_reader_helpers import add_book

    add_book(book.ctx.vault_root, book.repo, source_id="src_other", revision_id="rev_other",
             extraction_id="ext_other", held_out=False)
    _cite_more(book, "lo_early", {"ref_type": "canonical_source", "ref_id": "src_other", "source_id": "src_other",
                                  "locator": "span:ext_other/b2"})

    book.read(*STOP)

    assert "lo_early" not in book.claimed()
    assert _coverage(book, "lo_early").reason == "unseen"
    assert _coverage(book, "lo_early").unseen == (("ext_other", "b2"),)

    call(book.ctx, "reader.mark_section_progress",
         {"extractionId": "ext_other", "sectionId": "u1", "spansSeen": 1, "spanCount": 3, "seenSpanIds": ["b2"]})
    book.questions()  # a report claims for its own book; the next read of the books for every book read

    assert book.claimed()["lo_early"] == "part_read"
    request = _frozen_requests(book)["lo_early"]
    bundles = [ref for ref in request["context"]["source_refs"] if "lo_early" in ref["learning_object_ids"]]
    assert {(ref["extraction_id"], span) for ref in bundles for span in ref["span_ids"]} == {
        *((book.extraction_id, book.spans()[name][1]) for name in STOP), ("ext_other", "b2")}
    # b2 is quoted; b1 beside it, never seen, is not.
    assert "has a zero vector" in repr(request) and "addition and scalar" not in repr(request)


def test_a_topic_with_no_citation_never_qualifies(book, writer):
    book.read("P1", "P2", "P3", "P4", "P5", "P6", run=False)
    vault = load_vault(book.ctx.vault_root)
    vault.learning_objects["lo_late"].provenance.source_refs = []
    vault.evidence_facets["facet_lo_late"].provenance.source_refs = []

    coverage = topic_coverage(vault, book.repo, book.extraction_id, ["lo_late"])["lo_late"]

    assert (coverage.reason, coverage.qualifies) == ("no_citation", False)


# -- the request a part read sends -----------------------------------------------------------------------------

#: The words of a part-read request's own instruction line, and of the finish's.
PART_READ_LINE = "the part of a section the learner has read so far"
FINISH_LINE = "material the learner just finished reading"


def _subject(book) -> str:
    return load_vault(book.ctx.vault_root).learning_objects["lo_early"].subjects[0]


def _with_notes(book) -> dict[str, str]:
    """Two notes in the book's subject, as a book ingested the older way leaves one: one whose body is a paragraph
    the learner will have read (P1), one whose body holds a paragraph they will not have (P5). Their note ids."""

    from learnloop.vault.loader import add_note

    subject = _subject(book)
    seen = f"Paragraph P1 about the {PARAGRAPH_WORD['P1']} is part of the account of eigenvalues and the characteristic polynomial of a square matrix."
    unseen = f"Paragraph P5 about the {PARAGRAPH_WORD['P5']} is part of the account of eigenvalues and the characteristic polynomial of a square matrix."
    for note_id, body in (("read_part", seen), ("unread_part", unseen)):
        path = add_note(book.ctx.vault_root, subject, note_id, note_id, body)
        # The body alone, as a note that stands for a book's text holds it (add_note heads it with its title).
        path.write_text(path.read_text(encoding="utf-8").replace(f"# {note_id}\n\n", ""), encoding="utf-8")
    book.ctx.reload(maintenance=False)
    return {"seen": "note_read_part", "unseen": "note_unread_part"}


def test_a_part_read_request_says_the_learner_read_part_of_the_section(book, writer):
    book.read(*STOP)

    assert len(writer.prompts) == 2
    for prompt in writer.prompts:
        assert PART_READ_LINE in prompt
        assert FINISH_LINE not in prompt


def test_a_finish_request_keeps_the_finish_line(book, writer):
    book.read(*STOP)
    book.finish("P1")

    finish = writer.prompts[2:]
    assert len(finish) == 3  # lo_straddle, lo_late, lo_cross: the rest of the section, one topic a call
    for prompt in finish:
        assert FINISH_LINE in prompt and PART_READ_LINE not in prompt


def test_a_part_read_request_on_a_note_backed_book_sends_no_unread_note_text(book, writer):
    notes = _with_notes(book)

    book.read(*STOP)

    assert len(writer.prompts) == 2
    for prompt in writer.prompts:
        # The note wholly within passages read stays; the one holding an unread paragraph is left out.
        assert notes["seen"] in prompt
        assert notes["unseen"] not in prompt
        assert not [word for word in _unseen_words(*STOP) if word in prompt]
    for request in _frozen_requests(book).values():
        assert notes["unseen"] not in repr(request)
        assert not [word for word in _unseen_words(*STOP) if word in repr(request)]
    # The section's finish sends what it sent before: both notes, read or not.
    book.finish("P1")
    for prompt in writer.prompts[2:]:
        assert notes["seen"] in prompt and notes["unseen"] in prompt

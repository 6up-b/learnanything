"""The request a first set from the part read sends, beside the one a finished section sends: a part-read request has
an instruction line of its own (the learner has read part of the section, the passages given), and its context
leaves out every vault note whose excerpt is not wholly within passages the learner has seen. A finish request is
byte-identical to the one sent before part-read requests had either.

The bytes are pinned on the synthetic section of the section-writer tests (``tests/section_question_parts_helpers``):
one topic claimed as a finish claims it, or as a part read does, through the same per-topic claim. Its library holds
one note ("The topic definitions.") and no reading, so no passage of it has been seen.
"""

from __future__ import annotations

from learnloop.reader.section_generation import claim_section_topics

from tests.section_question_parts_helpers import (
    EXTRACTION, SOURCE, TOPICS, Writer, jobs_for, queue, request_digest, section,
)

#: The words of a part-read request's own instruction line, and of the finish's.
PART_READ_LINE = "the part of a section the learner has read so far"
FINISH_LINE = "material the learner just finished reading"

#: The finish request's digest, computed on the code before part-read requests had a line of their own.
FINISH_DIGEST = "7d64213113f46133ea1d7749ff9f1e35ad5ee4927e118831474d209b76cfbeb1"
#: The part-read request's digest: its own line, and no note.
PART_READ_DIGEST = "0df739ef507d2de295c1ebfd5bb0bf03c19dadba58766413a93321c3918756ed"


def _digest(request, root) -> str:
    """The request's digest with the library's own path (a temporary directory, different every run) named
    ``<library>``: everything else of it is the same bytes every run."""

    return request_digest({**request, "prompt": request["prompt"].replace(str(root), "<library>")})


def _claimed(tmp_path, trigger):
    paths, repo = section(tmp_path, 1)
    writer = Writer()
    jobs = jobs_for(paths, repo, writer)
    # A finish claims a finished section's topics; a part read claims an unfinished one's.
    repo.upsert_reader_section_progress(extraction_id=EXTRACTION, section_id="section_one", spans_seen=1,
                                        span_count=1, completed=trigger == "section_finished")
    batch = claim_section_topics(repo, extraction_id=EXTRACTION, section_id="section_one", source_id=SOURCE,
                                 lo_ids=TOPICS[:1], refs=[], from_stamp=None, enqueue=queue(jobs), trigger=trigger)
    assert batch
    jobs.run_queued_work()
    assert len(writer.requests) == 1
    return writer, paths.root


def test_a_finish_request_is_the_bytes_it_was(tmp_path):
    writer, root = _claimed(tmp_path, "section_finished")

    prompt = writer.requests[0]["prompt"]
    assert FINISH_LINE in prompt and PART_READ_LINE not in prompt
    assert "note_section" in prompt
    assert _digest(writer.requests[0], root) == FINISH_DIGEST


def test_a_part_read_request_has_its_own_line_and_no_unseen_note(tmp_path):
    writer, root = _claimed(tmp_path, "part_read")

    prompt = writer.requests[0]["prompt"]
    assert PART_READ_LINE in prompt and FINISH_LINE not in prompt
    # No passage of this library was seen, so no note's excerpt is wholly within one.
    assert "note_section" not in prompt and "The topic definitions." not in prompt
    assert _digest(writer.requests[0], root) == PART_READ_DIGEST

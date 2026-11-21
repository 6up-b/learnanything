"""The Reader records WHICH passages the learner saw, not only how many.

``reader.mark_section_progress`` takes an optional ``seenSpanIds`` (the passages the desktop or the phone observed
during the learner's own reading) and ``reachedEnd`` (the section's last readable passage was among them). Through the
real handler, on a synthetic book of three sections (``tests/mobile_v4_reader_helpers.py``: ``u1`` is b0-b2, ``u2``
b3-b4, ``u3`` b5-b6), and through the phone host for the phone's origin:

* only ids that are readable passages of the section on the reading are kept; any other is left out (logged with
  counts only), and the report's count, reveal and completion land exactly as without passages, never refused;
* reports union: a repeated, a smaller or a replayed report removes nothing and keeps each passage's first time and
  origin, across a restart;
* a count, or a completion, never becomes a passage (the phone's count cannot say which were seen);
* the end of a section is recorded with its origin; below algorithm tag mvp-0.63 it is acted on by nothing (from the tag
  it finishes the section: ``tests/test_section_end.py``);
* on a book read again, an exact alias carries a seen passage to the unchanged one; a changed or missing one does not
  (``content.sources.span_aliases``, the one alias authority);
* nothing in ``src`` reads the rows but their store and the reading this module tests.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

import learnloop_sidecar.handlers  # noqa: F401 -- populate METHOD_REGISTRY
from learnloop.reader.seen_passages import section_ends_on, seen_on
from learnloop_sidecar.context import SidecarContext
from tests.mobile_host_helpers import rows
from tests.mobile_v4_reader_helpers import EXTRACTION, call, desktop, job
from tests.mobile_v4_reader_helpers import world  # noqa: F401 - a fixture, used by parameter name
from tests.reread_safety_helpers import EXACT, GONE, MOVED, _reread
from tests.reread_safety_helpers import studied  # noqa: F401 - a fixture, used by parameter name

pytest.importorskip("starlette")

SRC = Path(__file__).resolve().parents[1] / "src"


def _report(ctx, section: str, *, ids=None, end: bool = False, extraction: str = EXTRACTION, **counts):
    params = {"extractionId": extraction, "sectionId": section, **counts}
    if ids is not None:
        params["seenSpanIds"] = ids
    if end:
        params["reachedEnd"] = True
    return call(ctx, "reader.mark_section_progress", params)


def _seen(repository, extraction: str = EXTRACTION) -> dict[str, dict]:
    return {row["span_id"]: row for row in rows(
        repository, "SELECT * FROM reader_seen_spans WHERE extraction_id = ? ORDER BY span_id", extraction)}


def _ends(repository, extraction: str = EXTRACTION) -> dict[str, dict]:
    return {row["section_id"]: row for row in rows(
        repository, "SELECT * FROM reader_section_ends WHERE extraction_id = ? ORDER BY section_id", extraction)}


# -- recording and leaving out ------------------------------------------------------------------------------------------


def test_a_report_records_each_observed_passage_once_with_its_section_time_and_origin(world):
    ctx = desktop(world["root"])
    _report(ctx, "u1", ids=["b1", "b0", "b1"], spansSeen=2, spanCount=3)
    seen = _seen(world["repo"])
    assert sorted(seen) == ["b0", "b1"]
    assert {(row["section_id"], row["origin"]) for row in seen.values()} == {("u1", "desktop")}
    assert all(row["first_seen_at"] for row in seen.values())
    # The count is recorded as before, beside them.
    assert world["repo"].reader_section_progress_row(EXTRACTION, "u1")["spans_seen"] == 2


def _without_times(row: dict | None) -> dict | None:
    return None if row is None else {key: value for key, value in row.items() if key != "updated_at"}


@pytest.mark.parametrize("ids", [
    ["zz"],          # no such passage in the reading
    ["b1", "b3"],    # b3 is u2's
], ids=["unknown_passage", "another_sections_passage"])
def test_an_id_that_is_not_a_passage_of_the_section_is_left_out_and_the_rest_of_the_report_lands(world, ids, caplog):
    ctx = desktop(world["root"])
    with caplog.at_level("WARNING", logger="learnloop.reader.seen_passages"):
        reply = _report(ctx, "u1", ids=ids, spansSeen=2, spanCount=3, completed=True)
    # The section's own passages are kept, the stranger is never recorded, and the count and the completion land.
    assert sorted(_seen(world["repo"])) == [span for span in ids if span == "b1"]
    row = world["repo"].reader_section_progress_row(EXTRACTION, "u1")
    assert row["spans_seen"] == 2 and row["completed_at"] is not None
    assert reply["progress"]["completedAt"] is not None
    # One warning, with counts only: a client mismatch shows, never an id.
    warnings = [record.getMessage() for record in caplog.records if record.name == "learnloop.reader.seen_passages"]
    assert len(warnings) == 1 and "1 of" in warnings[0]
    assert not any(span in warnings[0] for span in ("zz", "b3", "b1"))


@pytest.mark.parametrize("extraction, section", [
    (EXTRACTION, "u9"),          # no such section
    ("ext_nowhere", "u1"),       # no such reading
], ids=["unknown_section", "unknown_reading"])
def test_on_an_unknown_section_or_reading_no_passage_is_recorded_and_the_report_is_mains(world, extraction, section):
    """Main records the count of any section id on any reading id it is sent (no check: the row is written as
    named) and answers with it. The same report with passages does exactly that and records no passage."""

    with_ids = desktop(world["root"])
    reply = _report(with_ids, section, ids=["b1"], end=True, extraction=extraction, spansSeen=2, spanCount=3)
    without = _report(with_ids, section + "_plain", extraction=extraction, spansSeen=2, spanCount=3)
    row = _without_times(world["repo"].reader_section_progress_row(extraction, section))
    plain = _without_times(world["repo"].reader_section_progress_row(extraction, section + "_plain"))
    assert row is not None and {**row, "section_id": None} == {**plain, "section_id": None}
    assert row["spans_seen"] == 2 and row["span_count"] == 3
    assert {key: value for key, value in reply.items() if key != "progress"} == {
        key: value for key, value in without.items() if key != "progress"}
    assert rows(world["repo"], "SELECT * FROM reader_seen_spans") == []
    assert rows(world["repo"], "SELECT * FROM reader_section_ends") == []


def test_a_phone_completion_coalesced_with_passages_and_a_stranger_lands_whole(world):
    """The phone's outbox merges a section's queued reports, so a completion ("Next section") can arrive with the
    passages of an earlier report. One id the host does not count as the section's passage must not keep the
    completion from landing: the completion and the good ids are recorded, the stranger is not."""

    done = job(world["phone"], "reader.mark_section_progress",
               {"extractionId": EXTRACTION, "sectionId": "u1", "spansSeen": 3, "spanCount": 3, "completed": True,
                "seenSpanIds": ["b0", "b1", "node-footnote-7"], "reachedEnd": True}, "merged_1")
    row = world["repo"].reader_section_progress_row(EXTRACTION, "u1")
    assert row["completed_at"] is not None and row["spans_seen"] == 3
    assert row["generation_batch_id"] == "deferred_to_primary" and done["enqueuedGeneration"] is False
    seen = _seen(world["repo"])
    assert sorted(seen) == ["b0", "b1"] and {r["origin"] for r in seen.values()} == {"phone"}
    # Its end named b2, which it did not keep: no end is recorded, and nothing was refused.
    assert _ends(world["repo"]) == {}


# -- union ----------------------------------------------------------------------------------------------------------


def test_reports_union_and_a_smaller_report_removes_nothing_or_changes_a_first_observation(world):
    ctx = desktop(world["root"])
    _report(ctx, "u1", ids=["b0", "b1"], spansSeen=2, spanCount=3)
    first = _seen(world["repo"])
    # The phone saw b1 again (a smaller report), then b2.
    job(world["phone"], "reader.mark_section_progress",
        {"extractionId": EXTRACTION, "sectionId": "u1", "seenSpanIds": ["b1"], "spansSeen": 1, "spanCount": 3}, "p1")
    job(world["phone"], "reader.mark_section_progress",
        {"extractionId": EXTRACTION, "sectionId": "u1", "seenSpanIds": ["b2"], "spansSeen": 3, "spanCount": 3}, "p2")
    seen = _seen(world["repo"])
    assert sorted(seen) == ["b0", "b1", "b2"]
    assert seen["b0"] == first["b0"] and seen["b1"] == first["b1"]  # b1 keeps the desktop's time and origin
    assert seen["b2"]["origin"] == "phone"
    # An empty list and a report with no ids remove nothing either.
    _report(ctx, "u1", ids=[], spansSeen=1, spanCount=3)
    _report(ctx, "u1", spansSeen=1, spanCount=3)
    assert _seen(world["repo"]) == seen


def test_a_duplicate_report_and_an_outbox_replay_write_nothing_new(world):
    ctx = desktop(world["root"])
    _report(ctx, "u2", ids=["b3"], spansSeen=1, spanCount=2)
    once = _seen(world["repo"])
    _report(ctx, "u2", ids=["b3"], spansSeen=1, spanCount=2)
    assert _seen(world["repo"]) == once
    phone = {"extractionId": EXTRACTION, "sectionId": "u2", "seenSpanIds": ["b4"], "spansSeen": 2, "spanCount": 2}
    job(world["phone"], "reader.mark_section_progress", phone, "replayed")
    after_phone = _seen(world["repo"])
    job(world["phone"], "reader.mark_section_progress", phone, "replayed")
    assert _seen(world["repo"]) == after_phone and sorted(after_phone) == ["b3", "b4"]


def test_the_passages_survive_a_restart_and_later_reports_union_with_them(world):
    _report(desktop(world["root"]), "u1", ids=["b0"], spansSeen=1, spanCount=3)
    before = _seen(world["repo"])
    restarted = SidecarContext()
    restarted.load(world["root"])
    _report(restarted, "u1", ids=["b0", "b1"], spansSeen=2, spanCount=3)
    after = _seen(world["repo"])
    assert sorted(after) == ["b0", "b1"] and after["b0"] == before["b0"]
    # What the Reader reads back is the counts, as before: no reader is given the passages.
    progress = call(restarted, "reader.get_progress", {"extractionId": EXTRACTION})["sections"][0]
    assert set(progress) == {"extractionId", "sectionId", "spansSeen", "spanCount", "revealedAt", "completedAt",
                             "generationBatchId"}


def test_a_count_or_a_completion_is_never_turned_into_passages(world):
    ctx = desktop(world["root"])
    _report(ctx, "u1", spansSeen=3, spanCount=3)
    job(world["phone"], "reader.mark_section_progress",
        {"extractionId": EXTRACTION, "sectionId": "u2", "spansSeen": 2, "spanCount": 2, "completed": True}, "done")
    _report(ctx, "u1", completed=True)
    assert _seen(world["repo"]) == {} and _ends(world["repo"]) == {}


# -- the end of a section: recorded; below the tag acted on by nothing --------------------------------------------


def test_below_the_tag_reaching_the_end_is_recorded_with_its_origin_and_acted_on_by_nothing(world, monkeypatch):
    """At mvp-0.62. From mvp-0.63 the end finishes the section (``tests/test_section_end.py``)."""

    import learnloop.daily_plan.engine as engine
    import learnloop_sidecar.section_questions as section_questions
    from tests.helpers import _set_algorithm_version_at

    _set_algorithm_version_at(world["root"], "mvp-0.62")

    started: list[tuple] = []
    told: list[dict] = []
    monkeypatch.setattr(section_questions, "start_section_questions", lambda *args, **kwargs: started.append(args))
    real_note = engine.note_reading_progress
    monkeypatch.setattr(engine, "note_reading_progress", lambda env, **kwargs: told.append(kwargs) or real_note(env, **kwargs))
    ctx = desktop(world["root"])
    plain = _report(ctx, "u1", ids=["b1"], spansSeen=2, spanCount=3)
    ended = _report(ctx, "u1", ids=["b2"], end=True, spansSeen=3, spanCount=3)
    ends = _ends(world["repo"])
    assert list(ends) == ["u1"]
    assert (ends["u1"]["span_id"], ends["u1"]["origin"]) == ("b2", "desktop") and ends["u1"]["first_seen_at"]
    # The section is finished exactly as before: not by its end.
    row = world["repo"].reader_section_progress_row(EXTRACTION, "u1")
    assert row["completed_at"] is None and row["generation_batch_id"] is None
    assert started == [] and [note["completed"] for note in told] == [False, False]
    assert set(ended) == set(plain) and ended["enqueuedGeneration"] is False and ended["waitingForBuild"] is False
    assert ended["progress"]["completedAt"] is None
    # The phone's end is the phone's; a second end of a section keeps the first.
    job(world["phone"], "reader.mark_section_progress",
        {"extractionId": EXTRACTION, "sectionId": "u2", "seenSpanIds": ["b3", "b4"], "reachedEnd": True,
         "spansSeen": 2, "spanCount": 2}, "end_u2")
    _report(ctx, "u1", ids=["b2"], end=True, spansSeen=3, spanCount=3)
    again = _ends(world["repo"])
    assert again["u1"] == ends["u1"] and again["u2"]["origin"] == "phone" and again["u2"]["span_id"] == "b4"
    assert world["repo"].reader_section_progress_row(EXTRACTION, "u2")["completed_at"] is None


def test_an_end_is_recorded_only_when_its_last_passage_is_seen(world):
    ctx = desktop(world["root"])
    # Its last passage not seen: the end is left out, not refused; the passage and the count land.
    _report(ctx, "u1", ids=["b1"], end=True, spansSeen=2, spanCount=3)
    assert _ends(world["repo"]) == {} and sorted(_seen(world["repo"])) == ["b1"]
    assert world["repo"].reader_section_progress_row(EXTRACTION, "u1")["spans_seen"] == 2
    # Seen in an earlier report, the last passage makes a later end good on its own.
    _report(ctx, "u1", ids=["b2"], spansSeen=3, spanCount=3)
    _report(ctx, "u1", end=True)
    assert _ends(world["repo"])["u1"]["span_id"] == "b2"


# -- a book read again: exact aliases carry, changed ones do not ----------------------------------------------------


@pytest.mark.parametrize("carry", [True, False], ids=["aliases_recorded", "aliases_computed"])
def test_an_exact_alias_carries_a_seen_passage_to_a_reread_and_a_changed_one_does_not(studied, carry):
    repo = studied["repo"]
    ctx = SidecarContext()
    ctx.load(studied["root"])
    _report(ctx, "u1", ids=["a0", EXACT], spansSeen=2, spanCount=4, extraction="extA")
    _reread(studied, carry=carry)
    # A late report on the old reading (a phone that was away while the book was read again) counts too.
    _report(ctx, "u1", ids=[MOVED], spansSeen=3, spanCount=4, extraction="extA")
    _report(ctx, "u2", ids=[GONE], spansSeen=2, spanCount=2, extraction="extA")
    assert set(seen_on(repo, "extA")) == {"a0", EXACT, MOVED, GONE}
    on_b = seen_on(repo, "extB")
    # a0 and a1 are the same text in reading B (b0, b1); a2's words changed (b2) and a5's are gone.
    assert set(on_b) == {"b0", "b1"}
    assert on_b["b1"].observed_on == ("extA", EXACT) and on_b["b1"].origin == "desktop"
    assert on_b["b1"].first_seen_at == _seen(repo, "extA")[EXACT]["first_seen_at"]
    # Nothing is written onto the new reading: the carry is a read through the aliases.
    assert _seen(repo, "extB") == {}
    # A passage seen on the new reading is its own.
    _report(ctx, "h1", ids=["b2"], spansSeen=3, spanCount=4, extraction="extB")
    on_b = seen_on(repo, "extB")
    assert set(on_b) == {"b0", "b1", "b2"} and on_b["b2"].observed_on == ("extB", "b2")


def test_section_ends_are_read_on_their_own_reading_only(world):
    ctx = desktop(world["root"])
    _report(ctx, "u2", ids=["b3", "b4"], end=True, spansSeen=2, spanCount=2)
    assert {end.section_id: (end.span_id, end.origin) for end in section_ends_on(world["repo"], EXTRACTION)} == {
        "u2": ("b4", "desktop")}
    assert section_ends_on(world["repo"], "ext_other") == []


# -- readers: none but tests ----------------------------------------------------------------------------------------


def _mentions(pattern: str) -> set[str]:
    found = set()
    for path in SRC.rglob("*.py"):
        if re.search(pattern, path.read_text(encoding="utf-8")):
            found.add(path.relative_to(SRC).as_posix())
    return found


def test_nothing_in_src_reads_the_passages_but_their_store_and_the_one_reading():
    """These rows are generation evidence, not evidence of understanding: no mastery, exposure, scheduling or
    reading-credit reader may read them. The tables are named only by their store and the registries that classify
    them; the store's reads are called only by ``reader.seen_passages``; and of the reads it offers, only the first
    set from the part read (``reader.part_read``) calls ``seen_on``, ``seen_marker`` and ``seen_readings``, and
    nothing calls ``section_ends_on``. A new reader fails here on purpose."""

    assert _mentions(r"reader_seen_spans|reader_section_ends|reader_seen_readings") == {
        "learnloop/db/stores/reader.py",
        "learnloop/db/table_roles.py",
        "learnloop/adaptive_difficulty/protected_tables.py",
        "learnloop/adaptive_difficulty/column_classes.py",
        "learnloop/reader/seen_passages.py",
    }
    assert _mentions(r"\.reader_seen_spans_for\(|\.reader_section_ends_for\(|\.reader_seen_spans_marker\(|"
                     r"\.reader_seen_readings\(") == {"learnloop/reader/seen_passages.py"}
    assert _mentions(r"\bseen_on\b|\bseen_marker\b|\bseen_readings\b") == {
        "learnloop/reader/seen_passages.py", "learnloop/reader/part_read.py"}
    assert _mentions(r"\bsection_ends_on\b") == {"learnloop/reader/seen_passages.py"}

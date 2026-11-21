"""The Reader records WHICH passages the learner saw (UX "the first evening, finished", step 2).

``reader.mark_section_progress`` takes an optional ``seenSpanIds`` (the passages the desktop or the phone observed
during the learner's own reading) and ``reachedEnd`` (the section's last readable passage was among them). Through the
real handler, on a synthetic book of three sections (``tests/mobile_v4_reader_helpers.py``: ``u1`` is b0-b2, ``u2``
b3-b4, ``u3`` b5-b6), and through the phone host for the phone's origin:

* ids are checked against the reading and the section, and a report naming one that is not there writes nothing;
* reports union: a repeated, a smaller or a replayed report removes nothing and keeps each passage's first time and
  origin, across a restart;
* a count, or a completion, never becomes a passage (the phone's count cannot say which were seen);
* the end of a section is recorded with its origin and acted on by nothing: the section is finished exactly as before;
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
from learnloop_sidecar.errors import SidecarError
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


# -- recording and checking ------------------------------------------------------------------------------------------


def test_a_report_records_each_observed_passage_once_with_its_section_time_and_origin(world):
    ctx = desktop(world["root"])
    _report(ctx, "u1", ids=["b1", "b0", "b1"], spansSeen=2, spanCount=3)
    seen = _seen(world["repo"])
    assert sorted(seen) == ["b0", "b1"]
    assert {(row["section_id"], row["origin"]) for row in seen.values()} == {("u1", "desktop")}
    assert all(row["first_seen_at"] for row in seen.values())
    # The count is recorded as before, beside them.
    assert world["repo"].reader_section_progress_row(EXTRACTION, "u1")["spans_seen"] == 2


@pytest.mark.parametrize("section, ids", [
    ("u1", ["zz"]),          # no such passage in the reading
    ("u1", ["b1", "b3"]),    # b3 is u2's
    ("u9", ["b1"]),          # no such section
])
def test_a_report_naming_a_passage_not_in_its_reading_and_section_is_refused_whole(world, section, ids):
    ctx = desktop(world["root"])
    with pytest.raises(SidecarError) as refused:
        _report(ctx, section, ids=ids, spansSeen=2, spanCount=3)
    assert refused.value.code == "validation_error"
    assert _seen(world["repo"]) == {}
    assert world["repo"].reader_section_progress_row(EXTRACTION, section) is None


def test_a_report_on_a_reading_that_does_not_exist_is_refused(world):
    with pytest.raises(SidecarError) as refused:
        _report(desktop(world["root"]), "u1", ids=["b1"], extraction="ext_nowhere")
    assert refused.value.code == "validation_error"
    assert rows(world["repo"], "SELECT * FROM reader_seen_spans") == []


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


# -- the end of a section: recorded, acted on by nothing -------------------------------------------------------------


def test_reaching_the_end_is_recorded_with_its_origin_and_acted_on_by_nothing(world, monkeypatch):
    import learnloop.daily_plan.engine as engine
    import learnloop_sidecar.section_questions as section_questions

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
    with pytest.raises(SidecarError) as refused:
        _report(ctx, "u1", ids=["b1"], end=True, spansSeen=2, spanCount=3)
    assert refused.value.code == "validation_error"
    assert _ends(world["repo"]) == {} and _seen(world["repo"]) == {}
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
    """These rows are generation evidence for a later step, not evidence of understanding: no mastery, exposure,
    scheduling, reading-credit or generation reader may read them yet. The tables are named only by their store and
    the registries that classify them; the store's reads are called only by ``reader.seen_passages``; and the reads it
    offers (``seen_on``, ``section_ends_on``) are called by nothing in ``src``. A new reader fails here on purpose:
    it belongs to the step that makes the rows mean something."""

    assert _mentions(r"reader_seen_spans|reader_section_ends") == {
        "learnloop/db/stores/reader.py",
        "learnloop/db/table_roles.py",
        "learnloop/adaptive_difficulty/protected_tables.py",
        "learnloop/adaptive_difficulty/column_classes.py",
        "learnloop/reader/seen_passages.py",
    }
    assert _mentions(r"\.reader_seen_spans_for\(|\.reader_section_ends_for\(") == {"learnloop/reader/seen_passages.py"}
    assert _mentions(r"\bseen_on\b|\bsection_ends_on\b") == {"learnloop/reader/seen_passages.py"}

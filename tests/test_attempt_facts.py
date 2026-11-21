"""Attempt facts (``learnloop.attempts.facts``): collected as stored, with their coverage, never inferred backwards.

On a basic vault with rows written straight into its database: an old attempt with only its counts, partial modern
capture, a hint requested and never shown, a hint attached after the fact, a count that disagrees with its rows,
reveals of every source kind on both sides of the serve and under the auto-prime threshold, questions, the cutoff's
admission and its historical help visibility, the draft form, a withheld item read through adaptive difficulty's
material view against the same vault with that item removed, one answer through two surfaces, and the reads the
collector makes. Adaptive difficulty's outcome categories over facts mapped onto its own type are compared with its
category over the values its replay reads, on the full assistance x timing x category matrix.
"""

from __future__ import annotations

from contextlib import closing
import dataclasses
import itertools

import pytest

from learnloop.adaptive_difficulty import outcomes as O
from learnloop.adaptive_difficulty.material_view import detached_view
from learnloop.attempts import facts as F
from learnloop.attempts.attempts import AttemptDraft
from learnloop.db.evidence_cutoff import Cutoff
from learnloop.db.repositories import Repository
from learnloop.vault.loader import load_vault

from tests.attempt_facts_helpers import ITEM, ad_facts, assist, attempt, presentation, question, raw, reveal
from tests.helpers import create_basic_vault

T0 = "2026-06-01T10:00:00Z"


@pytest.fixture()
def paths(tmp_path):
    return create_basic_vault(tmp_path / "vault")


def _collect(paths, ids, cutoff=None):
    with closing(raw(paths.sqlite_path)) as connection:
        return F.collect_facts(F.ConnectionReader(connection), ids, cutoff or Cutoff.current())


def _coverage(facts, field):
    entry = facts.coverage_of(field)
    assert entry is not None, field
    return entry


def test_an_old_attempt_keeps_its_counts_and_says_it_has_nothing_more(paths):
    attempt(paths.sqlite_path, "att_old", T0, hints_used=2, primed=1)
    facts = _collect(paths, ["att_old"])["att_old"]
    assert (facts.hints_used, facts.primed, facts.first_hint_progress) == (2, 1, None)
    assert facts.hints == () and facts.detail == F.DETAIL_COUNTS_ONLY
    assert _coverage(facts, "hints").coverage == F.COUNT_ONLY
    assert _coverage(facts, "first_hint_progress").coverage == F.ABSENT
    assert _coverage(facts, "pre_exposed").coverage == F.ABSENT
    assert _coverage(facts, "hints_used").source == "practice_attempts.hints_used"


def test_without_the_help_table_the_source_is_absent_not_no_help():
    connection = __import__("sqlite3").connect(":memory:")
    connection.row_factory = __import__("sqlite3").Row
    connection.execute("CREATE TABLE practice_attempts (id TEXT, practice_item_id TEXT, learning_object_id TEXT, "
                       "attempt_type TEXT, hints_used INTEGER, primed INTEGER, created_at TEXT)")
    connection.execute("INSERT INTO practice_attempts VALUES ('a1', 'pi', 'lo', 'independent_attempt', 0, 0, ?)",
                       (T0,))
    facts = F.collect_facts(F.ConnectionReader(connection), ["a1"], Cutoff.current())["a1"]
    assert [_coverage(facts, name).coverage for name in ("hints", "questions", "reveals")] == [F.ABSENT] * 3
    assert facts.detail == F.DETAIL_COUNTS_ONLY and facts.hints_used == 0


def test_partial_modern_capture_keeps_the_count_and_the_rows_apart(paths):
    attempt(paths.sqlite_path, "att_p", "2026-06-01T10:05:00Z", hints_used=2, submission_id="sub_p",
            first_hint_progress="draft_started")
    assist(paths.sqlite_path, "ha_1", "2026-06-01T10:01:00Z", level=2, counted_by="server", attempt_id="att_p",
           submission_id="sub_p", shown_at="2026-06-01T10:01:01Z", work_chars=12)
    facts = _collect(paths, ["att_p"])["att_p"]
    assert facts.hints_used == 2 and len(facts.hints) == 1
    entry = _coverage(facts, "hints")
    assert entry.coverage == F.PARTIAL and entry.source_ids == ("ha_1",)
    assert "1 of the submitted 2" in entry.note
    assert facts.detail == F.DETAIL_FULL
    (hint,) = facts.hints
    assert (hint.level, hint.shown, hint.attached, hint.work_chars) == (2, True, True, 12)


def test_a_count_that_disagrees_with_its_rows_keeps_both(paths):
    attempt(paths.sqlite_path, "att_c", "2026-06-01T10:05:00Z", hints_used=0, submission_id="sub_c")
    assist(paths.sqlite_path, "ha_c", "2026-06-01T10:01:00Z", level=1, counted_by="server", attempt_id="att_c",
           submission_id="sub_c", shown_at="2026-06-01T10:01:01Z")
    facts = _collect(paths, ["att_c"])["att_c"]
    assert facts.hints_used == 0 and [hint.assist_id for hint in facts.hints] == ["ha_c"]
    assert _coverage(facts, "hints").coverage == F.PARTIAL


def test_a_hint_requested_and_never_shown_is_kept_as_not_shown(paths):
    attempt(paths.sqlite_path, "att_u", "2026-06-01T10:05:00Z", hints_used=1, submission_id="sub_u")
    assist(paths.sqlite_path, "ha_shown", "2026-06-01T10:01:00Z", level=2, counted_by="server",
           attempt_id="att_u", submission_id="sub_u", shown_at="2026-06-01T10:01:01Z")
    assist(paths.sqlite_path, "ha_unshown", "2026-06-01T10:02:00Z", level=3, counted_by="server", shown=0,
           attempt_id="att_u", submission_id="sub_u")
    facts = _collect(paths, ["att_u"])["att_u"]
    shown = {hint.assist_id: hint.shown for hint in facts.hints}
    assert shown == {"ha_shown": True, "ha_unshown": False}
    # The unshown row is not counted, so the one shown row accounts for the submitted count.
    assert _coverage(facts, "hints").coverage == F.PRESENT
    assert [hint.assist_id for hint in facts.assists("hint", shown=True)] == ["ha_shown"]


def test_a_hint_under_the_submission_key_is_found_before_and_after_its_late_attachment(paths):
    attempt(paths.sqlite_path, "att_l", "2026-06-01T10:05:00Z", hints_used=1, submission_id="sub_l")
    assist(paths.sqlite_path, "ha_late", "2026-06-01T10:01:00Z", level=2, counted_by="server",
           submission_id="sub_l", shown_at="2026-06-01T10:01:01Z")
    before = _collect(paths, ["att_l"])["att_l"]
    assert [(hint.assist_id, hint.attached) for hint in before.hints] == [("ha_late", False)]
    assert _coverage(before, "hints").coverage == F.PARTIAL
    with closing(raw(paths.sqlite_path)) as connection:
        connection.execute("UPDATE help_assists SET attempt_id = 'att_l' WHERE id = 'ha_late'")
        connection.commit()
    after = _collect(paths, ["att_l"])["att_l"]
    assert [(hint.assist_id, hint.attached) for hint in after.hints] == [("ha_late", True)]
    assert _coverage(after, "hints").coverage == F.PRESENT


def test_as_known_at_a_cutoff_a_later_showing_reads_not_shown_and_the_attachment_partial(paths):
    attempt(paths.sqlite_path, "att_k", "2026-06-01T10:05:00Z", hints_used=1, submission_id="sub_k")
    # Requested and shown before the cutoff, attached at some time the row does not record.
    assist(paths.sqlite_path, "ha_k", "2026-06-01T10:01:00Z", level=2, counted_by="server", attempt_id="att_k",
           submission_id="sub_k", shown_at="2026-06-01T10:03:00Z")
    # Requested before the cutoff, shown after it.
    assist(paths.sqlite_path, "ha_late_shown", "2026-06-01T10:04:00Z", level=2, counted_by="server",
           attempt_id="att_k", submission_id="sub_k", shown_at="2026-06-01T10:07:00Z")
    # Requested after the cutoff.
    assist(paths.sqlite_path, "ha_after", "2026-06-01T10:08:00Z", level=2, counted_by="server",
           attempt_id="att_k", submission_id="sub_k", shown_at="2026-06-01T10:08:01Z")
    cutoff = Cutoff.as_known_at("2026-06-01T10:06:00Z")
    facts = _collect(paths, ["att_k"], cutoff)["att_k"]
    assert [(hint.assist_id, hint.shown, hint.shown_at) for hint in facts.hints] == [
        ("ha_k", True, "2026-06-01T10:03:00Z"), ("ha_late_shown", False, None)]
    entry = _coverage(facts, "hints")
    assert entry.coverage == F.PARTIAL and "no time of their own" in entry.note
    now = _collect(paths, ["att_k"])["att_k"]
    assert [(hint.assist_id, hint.shown) for hint in now.hints] == [
        ("ha_k", True), ("ha_late_shown", True), ("ha_after", True)]
    # Known only after the attempt itself: not admitted at all.
    assert _collect(paths, ["att_k"], Cutoff.as_known_at("2026-06-01T10:02:00Z")) == {}


def test_the_cutoff_admits_attempts_by_its_own_rule(paths):
    attempt(paths.sqlite_path, "att_a", "2026-06-01T10:00:00Z")
    attempt(paths.sqlite_path, "att_b", "2026-06-02T10:00:00Z")
    assert list(_collect(paths, ["att_b", "att_a"])) == ["att_b", "att_a"]
    assert list(_collect(paths, ["att_a", "att_b"], Cutoff.completed_by("2026-06-01T12:00:00Z"))) == ["att_a"]
    assert list(_collect(paths, ["att_a", "att_b"], Cutoff.ad_replay("2026-06-01T12:00:00Z"))) == ["att_a"]
    assert _collect(paths, []) == {}
    assert _collect(paths, ["missing"]) == {}


@pytest.mark.parametrize("source_kind", ["tutor_answer", "repair_display", "guided_redo", "source_review",
                                         "answer_display"])
def test_each_reveal_kind_is_kept_with_its_amount_and_its_side_of_the_serve(paths, source_kind):
    attempt(paths.sqlite_path, "att_prev", "2026-06-01T09:00:00Z")
    reveal(paths.sqlite_path, "rv_old", "2026-06-01T08:00:00Z", source_kind=source_kind)
    presentation(paths.sqlite_path, "pp_1", "2026-06-01T10:02:00Z")
    attempt(paths.sqlite_path, "att_r", "2026-06-01T10:05:00Z", plan_presentation_id="pp_1")
    reveal(paths.sqlite_path, "rv_before", "2026-06-01T10:01:00Z", source_kind=source_kind, amount=0.2)
    reveal(paths.sqlite_path, "rv_during", "2026-06-01T10:03:00Z", source_kind=source_kind, amount=0.5,
           basis="b1")
    reveal(paths.sqlite_path, "rv_after", "2026-06-01T10:06:00Z", source_kind=source_kind)
    facts = _collect(paths, ["att_r"])["att_r"]
    assert facts.presented_at == "2026-06-01T10:02:00Z" and facts.bound_presentation
    assert [(row.reveal_id, row.source_kind, row.amount, row.position) for row in facts.reveals] == [
        ("rv_before", source_kind, 0.2, F.BEFORE_SERVE), ("rv_during", source_kind, 0.5, F.DURING)]
    assert [row.reveal_id for row in facts.shown_before()] == ["rv_before"]
    assert [row.reveal_id for row in facts.shown_during()] == ["rv_during"]
    assert _coverage(facts, "reveals").source_ids == ("rv_before", "rv_during")


def test_a_reveal_under_the_priming_threshold_leaves_primed_as_submitted(paths):
    attempt(paths.sqlite_path, "att_t", "2026-06-01T10:05:00Z", primed=0)
    reveal(paths.sqlite_path, "rv_small", "2026-06-01T10:01:00Z", amount=0.2)
    facts = _collect(paths, ["att_t"])["att_t"]
    assert facts.primed == 0
    assert [(row.amount, row.position) for row in facts.reveals] == [(0.2, F.POSITION_UNKNOWN)]
    assert _coverage(facts, "presented_at").coverage == F.ABSENT


def test_questions_are_kept_with_their_progress_markers(paths):
    attempt(paths.sqlite_path, "att_q", "2026-06-01T10:05:00Z")
    question(paths.sqlite_path, "qe_1", "2026-06-01T10:01:00Z", "att_q", hint_equivalent=1,
             attempt_progress="no_draft", seconds_into_attempt=0)
    question(paths.sqlite_path, "qe_2", "2026-06-01T10:02:00Z", "att_q", context="feedback")
    facts = _collect(paths, ["att_q"])["att_q"]
    assert [(q.question_id, q.context, q.hint_equivalent, q.attempt_progress) for q in facts.questions] == [
        ("qe_1", "practice", True, "no_draft"), ("qe_2", "feedback", False, None)]
    assert _coverage(facts, "questions").source_ids == ("qe_1", "qe_2")


def test_draft_facts_need_no_attempt_id_and_no_database():
    draft = AttemptDraft(practice_item_id=ITEM, learner_answer_md="  ", attempt_type="hinted_attempt",
                         hints_used=2, primed=True, declared_stuck=True, submission_id="sub_d", latency_seconds=40)
    facts = F.facts_from_draft(draft)
    assert facts.attempt_id is None and facts.created_at is None
    assert (facts.produced_as, facts.hints_used, facts.primed, facts.declared_stuck) == ("hinted_attempt", 2, True,
                                                                                        True)
    assert facts.answer_empty is True and facts.submission_id == "sub_d" and facts.latency_seconds == 40
    assert {entry.field: entry.coverage for entry in facts.coverage if entry.coverage == F.NOT_READ} == {
        "hints": F.NOT_READ, "questions": F.NOT_READ, "reveals": F.NOT_READ, "presented_at": F.NOT_READ}


def test_one_answer_through_two_surfaces_is_one_set_of_facts(paths):
    attempt(paths.sqlite_path, "att_desk", "2026-06-01T10:05:00Z", entry_surface="desktop", hints_used=1)
    attempt(paths.sqlite_path, "att_phone", "2026-06-02T10:05:00Z", entry_surface="phone", hints_used=1)
    out = _collect(paths, ["att_desk", "att_desk", "att_phone"])
    assert list(out) == ["att_desk", "att_phone"]
    desk, phone = out["att_desk"], out["att_phone"]
    assert (desk.entry_surface, phone.entry_surface) == ("desktop", "phone")
    ignore = {"attempt_id", "created_at", "entry_surface", "coverage"}
    assert {k: v for k, v in dataclasses.asdict(desk).items() if k not in ignore} == {
        k: v for k, v in dataclasses.asdict(phone).items() if k not in ignore}


def _withheld_fixture(paths, *, with_withheld: bool):
    attempt(paths.sqlite_path, "att_v1", "2026-06-01T09:00:00Z", submission_id="sub_v1")
    attempt(paths.sqlite_path, "att_v2", "2026-06-01T10:05:00Z", hints_used=1, submission_id="sub_v2")
    assist(paths.sqlite_path, "ha_v", "2026-06-01T10:01:00Z", level=2, counted_by="server", attempt_id="att_v2",
           submission_id="sub_v2", shown_at="2026-06-01T10:01:01Z")
    reveal(paths.sqlite_path, "rv_v", "2026-06-01T10:02:00Z")
    question(paths.sqlite_path, "qe_v", "2026-06-01T10:03:00Z", "att_v2")
    if with_withheld:
        attempt(paths.sqlite_path, "att_w", "2026-06-01T10:00:00Z", item="pi_withheld", submission_id="sub_w",
                hints_used=1)
        assist(paths.sqlite_path, "ha_w", "2026-06-01T09:59:00Z", item="pi_withheld", level=2,
               counted_by="server", attempt_id="att_w", submission_id="sub_w", shown_at="2026-06-01T09:59:01Z")
        reveal(paths.sqlite_path, "rv_w", "2026-06-01T09:58:00Z", item="pi_withheld")
        question(paths.sqlite_path, "qe_w", "2026-06-01T09:59:30Z", "att_w", practice_item_id="pi_withheld")
        # Rows on the visible attempt that name withheld material: a question about the withheld item, and a
        # reveal on the visible item made by the withheld item's tutor question.
        question(paths.sqlite_path, "qe_cross", "2026-06-01T10:03:30Z", "att_v2", practice_item_id="pi_withheld")
        reveal(paths.sqlite_path, "rv_cross", "2026-06-01T10:04:00Z", question_event_id="qe_w")


def test_a_withheld_item_behind_the_material_view_reads_as_if_it_were_never_stored(tmp_path):
    present = create_basic_vault(tmp_path / "present")
    removed = create_basic_vault(tmp_path / "removed")
    _withheld_fixture(present, with_withheld=True)
    _withheld_fixture(removed, with_withheld=False)
    ids = ["att_v1", "att_v2", "att_w"]
    vault = load_vault(present.root)
    view = detached_view(vault, Repository(present.sqlite_path), {"pi_withheld"})
    with closing(raw(present.sqlite_path)) as connection:
        through_view = F.collect_facts(F.FilteredReader(connection, view), ids, Cutoff.current())
        unfiltered = F.collect_facts(F.ConnectionReader(connection), ids, Cutoff.current())
    assert [hint.assist_id for hint in unfiltered["att_w"].hints] == ["ha_w"]
    assert [row.reveal_id for row in unfiltered["att_w"].reveals] == ["rv_w"]
    assert [q.question_id for q in unfiltered["att_v2"].questions] == ["qe_v", "qe_cross"]
    assert [row.reveal_id for row in unfiltered["att_v2"].reveals] == ["rv_v", "rv_cross"]
    assert [q.question_id for q in through_view["att_v2"].questions] == ["qe_v"]
    assert [row.reveal_id for row in through_view["att_v2"].reveals] == ["rv_v"]
    assert through_view == _collect(removed, ids)
    assert list(through_view) == ["att_v1", "att_v2"]


def test_the_collector_reads_a_fixed_handful_whatever_the_number_of_attempts(paths):
    ids = []
    for index in range(30):
        attempt_id = f"att_n{index:02d}"
        ids.append(attempt_id)
        attempt(paths.sqlite_path, attempt_id, f"2026-06-01T10:{index:02d}:00Z", submission_id=f"sub_{index}",
                hints_used=1, plan_presentation_id=f"pp_{index}")
        assist(paths.sqlite_path, f"ha_n{index}", f"2026-06-01T10:{index:02d}:00Z", level=2, counted_by="server",
               attempt_id=attempt_id, submission_id=f"sub_{index}")
        presentation(paths.sqlite_path, f"pp_{index}", f"2026-06-01T10:{index:02d}:00Z")

    def reads(wanted):
        statements = []
        with closing(raw(paths.sqlite_path)) as connection:
            connection.set_trace_callback(statements.append)
            F.collect_facts(F.ConnectionReader(connection), wanted, Cutoff.current())
        return [statement for statement in statements if statement.lstrip().upper().startswith("SELECT")]

    one, thirty = reads(ids[:1]), reads(ids)
    assert len(one) == len(thirty) == 8, thirty


# -- adaptive difficulty's categories over the facts ------------------------------------------------------------

HINTS = (0, 1, 2)
PROGRESS = (None, O.NO_DRAFT, O.DRAFT_STARTED, "unexpected")
QUESTIONS = ((), (("practice", 1, None, O.NO_DRAFT, None),), (("practice", 1, None, O.DRAFT_STARTED, 30.0),),
             (("practice", 0, "mechanism", None, 0.0),), (("feedback", 1, None, O.NO_DRAFT, None),),
             (("practice", 0, "other", O.NO_DRAFT, None),))
CORRECTNESS = (None, 0.0, 0.3, 0.5, 0.8, 1.0)


def test_adaptive_difficultys_categories_over_the_facts_match_its_own_on_the_full_matrix():
    cases = 0
    for hints, progress, rows, primed, correctness, bound, stuck, pre in itertools.product(
            HINTS, PROGRESS, QUESTIONS, (False, True), CORRECTNESS, (False, True), (False, True), (False, True)):
        questions = tuple(F.QuestionFact(f"q{i}", context, question_type, bool(flag), attempt_progress, seconds,
                                         T0)
                          for i, (context, flag, question_type, attempt_progress, seconds) in enumerate(rows))
        facts = dataclasses.replace(
            F.submitted_facts(attempt_type="independent_attempt", hints_used=hints, primed=primed,
                              correctness=correctness, first_hint_progress=progress),
            questions=questions, plan_presentation_id="pp" if bound else None)
        replay_rows = [{"context": context, "hint_equivalent": flag, "question_type": question_type,
                        "attempt_progress": attempt_progress, "seconds_into_attempt": seconds}
                       for context, flag, question_type, attempt_progress, seconds in rows]
        own = O.AttemptFacts(correctness=correctness, hints_used=hints, first_hint_progress=progress,
                             help_questions=O.help_questions_from_rows(replay_rows), primed=primed,
                             pre_exposed=pre, bound_presentation=bound, stuck=stuck)
        mapped = ad_facts(facts, stuck=stuck, pre_exposed=pre)
        assert mapped == own
        assert (O.help_timing(mapped), O.category(mapped)) == (O.help_timing(own), O.category(own))
        cases += 1
    assert cases == len(HINTS) * len(PROGRESS) * len(QUESTIONS) * 2 * len(CORRECTNESS) * 2 * 2 * 2

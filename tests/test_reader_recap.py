"""Reader workbench RW6a: "Last time here" (spec_reader_workbench_v1 §9.1;
gates G25 (the summary part) and G31; docs/reviews/reader-workbench-RW6a.md).

* A reader session is one visit on the reader envelope, or several visits on
  the same source less than 30 minutes apart.
* The typed per-session summary is deterministic from the ledgers: computed
  twice, it is identical (G25).
* The card is a pure read over the ledgers: Still open (question_events),
  Unfinished (workbench_sessions), Worth a second look (RW1a's still unclear),
  Since last time (lo_certification, dated by the certifying attempt after the
  previous session ended). Headings carry no counts.
* Opening a source with the recap on or off writes nothing but the
  ``recap_shown`` event (G31); dismiss hides the card until the next session.

Fakes only; no model call anywhere.
"""

from __future__ import annotations

import json
from datetime import timedelta

import pytest

from learnloop.reader import reader_sessions as RS
from learnloop.reader import recap as RC
from learnloop.vault.loader import load_vault
from tests.helpers import append_config_toml
from tests.recap_fixtures import (
    EXT, T0, ask, call, close_visit, context, interaction_rows, iso, open_visit, problem, resolve,
    still_unclear, table_counts, visit,
)
from tests.test_reader_dialogue import _setup


def _now(minutes: float):
    return T0 + timedelta(minutes=minutes)


# -- the reader session ---------------------------------------------------------------------------


def _events(*visits: tuple[str, float, float | None, str]) -> list[dict]:
    rows: list[dict] = []
    for visit_id, start, end, extraction in visits:
        rows.append({"kind": "reader_view_opened", "created_at": iso(start),
                     "payload": {"visit_id": visit_id, "extraction_id": extraction}})
        if end is not None:
            rows.append({"kind": "reader_view_closed", "created_at": iso(end),
                         "payload": {"visit_id": visit_id, "extraction_id": extraction}})
    return rows


def test_visits_less_than_30_minutes_apart_are_one_session():
    visits = RS.visits_from_events(_events(
        ("v1", 0, 10, EXT),
        ("v2", 39.9, 45, EXT),    # 29.9 minutes after v1 ended: the same session
        ("v3", 75, 80, EXT),      # exactly 30 minutes after v2: a new session
        ("v4", 140, 150, EXT),
    ))
    sessions = RS.group_sessions(visits)
    assert [s.visit_ids for s in sessions] == [("v1", "v2"), ("v3",), ("v4",)]
    assert sessions[0].started_at == iso(0) and sessions[0].ended_at == iso(45)
    assert sessions[0].session_id == "v1"


def test_sessions_are_per_source_and_a_visit_without_a_close_ends_at_its_last_event():
    rows = _events(("v1", 0, None, EXT), ("w1", 5, 6, "ext_other"))
    rows.append({"kind": "reader_action_invoked", "created_at": iso(12),
                 "payload": {"event": "detour_opened", "visit_id": "v1", "extraction_id": EXT}})
    visits = RS.visits_from_events(rows)
    by_source = {v.visit_id: v for v in visits}
    assert by_source["v1"].ended_at == iso(12)
    sessions = RS.group_sessions(visits)
    assert sorted((s.extraction_id, s.visit_ids) for s in sessions) == [(EXT, ("v1",)), ("ext_other", ("w1",))]


def test_the_card_is_about_the_session_before_the_current_one():
    sessions = RS.group_sessions(RS.visits_from_events(_events(("v1", 0, 10, EXT), ("v2", 100, 110, EXT))))
    # A new visit two hours later: the previous session is v2's.
    previous, current = RS.split_sessions(sessions, current_visit_id="v3", now=_now(230))
    assert previous.visit_ids == ("v2",) and current.visit_ids == ("v3",)
    # Reopened twenty minutes after v2 closed: the visit joins v2's session, so
    # the card is about v1's.
    previous, current = RS.split_sessions(sessions, current_visit_id="v3", now=_now(130))
    assert previous.visit_ids == ("v1",) and current.visit_ids == ("v2", "v3")
    # The current visit already on the envelope.
    previous, current = RS.split_sessions(sessions, current_visit_id="v2", now=_now(111))
    assert previous.visit_ids == ("v1",) and current.visit_ids == ("v2",)
    # First visit ever: nothing before it.
    previous, _current = RS.split_sessions([], current_visit_id="v1", now=_now(0))
    assert previous is None


def test_sessions_are_read_from_the_reader_envelope(tmp_path):
    _vault, repo = _setup(tmp_path)
    visit(repo, "v1", 0, 10)
    visit(repo, "v2", 20, 25)
    visit(repo, "v3", 100, 110)
    visit(repo, "x1", 0, 5, extraction_id="ext_other")
    sessions = RS.sessions_for_source(repo, EXT)
    assert [s.visit_ids for s in sessions] == [("v1", "v2"), ("v3",)]


# -- the typed summary (G25) ----------------------------------------------------------------------


def _seed_session(vault, repo):
    """One earlier session (0-40 min) with an inquiry, a resolved one, a
    still-unclear answer, a problem worked with the book, and a cue tap."""

    visit(repo, "v1", 0, 40)
    first = ask(vault, repo, "Why are the densities weighted by p?", 2)
    second = ask(vault, repo, "What is a mixture?", 4, span_id="s2")
    resolve(repo, second["reader_answer_event_id"], 6)
    still_unclear(repo, first["reader_answer_event_id"], 8)
    ask(vault, repo, "ok but why does differentiating keep the weights?", 9,
        parent=first["reader_answer_event_id"])
    problem(repo, 10, steps=3, book=True)
    return first, second


def test_the_typed_summary_is_deterministic_from_the_ledgers(tmp_path):
    vault, repo = _setup(tmp_path)
    _seed_session(vault, repo)
    session = RS.sessions_for_source(repo, EXT)[0]

    first = RC.session_summary(vault, repo, extraction_id=EXT, session=session, now=_now(300))
    # Computed twice, from freshly loaded state: identical (G25).
    again = RC.session_summary(load_vault(vault.root), type(repo)(repo.sqlite_path), extraction_id=EXT,
                               session=RS.sessions_for_source(repo, EXT)[0], now=_now(300))
    assert json.dumps(first, sort_keys=True) == json.dumps(again, sort_keys=True)

    # §9.1's list, typed.
    assert first["summary_version"] == RC.SUMMARY_VERSION
    for key in ("session", "sections_read", "inquiries", "workbench", "cues", "predictions_missed",
                "gaps_named", "facets_touched", "claims_needing_independent_check", "observations"):
        assert key in first, key
    assert set(first["inquiries"]) == {"opened", "resolved", "still_open"}
    assert len(first["inquiries"]["opened"]) == 2  # two roots (the follow-up is a branch)
    assert [r["resolution"] for r in first["inquiries"]["resolved"]] == ["resolved"]
    assert len(first["inquiries"]["still_open"]) == 1
    [worked] = first["workbench"]
    assert worked["status"] == "open" and worked["book_counted"] is True
    assert worked["highest_help_level"] is None  # no ladder before RW2b
    assert first["predictions_missed"] == []     # RW5a has not landed
    # Typed, not prose: no learner words in the summary.
    flat = json.dumps(first)
    assert "weighted by p" not in flat and "differentiating" not in flat


def test_the_summary_keeps_to_its_session(tmp_path):
    vault, repo = _setup(tmp_path)
    _seed_session(vault, repo)
    visit(repo, "v2", 200, 230)
    ask(vault, repo, "A later question", 205)
    early, late = RS.sessions_for_source(repo, EXT)
    late_summary = RC.session_summary(vault, repo, extraction_id=EXT, session=late, now=_now(300))
    assert len(late_summary["inquiries"]["opened"]) == 1
    assert late_summary["workbench"] == []
    early_summary = RC.session_summary(vault, repo, extraction_id=EXT, session=early, now=_now(300))
    assert len(early_summary["inquiries"]["opened"]) == 2


def test_claims_needing_an_independent_check_are_assisted_only_facets(tmp_path):
    vault, repo = _setup(tmp_path)
    visit(repo, "v1", 0, 40)
    row = problem(repo, 2, steps=1, book=True)
    _attempt(repo, "att_book", minutes=20, hints=1)
    _link(repo, row["id"], "att_book", minutes=20)
    session = RS.sessions_for_source(repo, EXT)[0]
    summary = RC.session_summary(vault, repo, extraction_id=EXT, session=session, now=_now(300))
    [claim] = summary["claims_needing_independent_check"]
    assert claim["facet_id"] == vault.canonical_facet_id("recall")
    assert claim["attempt_ids"] == ["att_book"]
    assert claim["basis"] == "source_visible"

    # An unassisted success on the facet afterwards (credit it banks on its
    # Demonstrated curve, the evidence system's own reading) answers it; an
    # assisted one, or one before the session, does not. Real attempts, the
    # production timeline (review round 2 F3: no synthetic curve).
    from learnloop.attempts.attempts import AttemptDraft, SelfGradeInput, complete_self_graded_attempt
    from learnloop.clock import FrozenClock

    def graded(minutes, *, hints=0):
        complete_self_graded_attempt(
            vault, repo,
            AttemptDraft(practice_item_id="pi_svd_define_001", learner_answer_md="U Sigma V^T",
                         attempt_type="hinted_attempt" if hints else "independent_attempt", hints_used=hints),
            SelfGradeInput(criterion_points={"correctness": 4}, fatal_errors=[], confidence=4),
            clock=FrozenClock(T0 + timedelta(minutes=minutes)),
        )

    for minutes, hints, answered in ((200, 1, False), (-10, 0, False), (210, 0, True)):
        graded(minutes, hints=hints)
        summary = RC.session_summary(vault, repo, extraction_id=EXT, session=session, now=_now(300))
        assert (summary["claims_needing_independent_check"] == []) is answered, (minutes, hints)


def _attempt(repo, attempt_id: str, *, minutes: float, hints: int) -> None:
    repo.insert_practice_attempt({
        "id": attempt_id, "practice_item_id": "pi_svd_define_001", "learning_object_id": "lo_svd_definition",
        "subject": "linear-algebra", "concept": "singular_value_decomposition", "practice_mode": "short_answer",
        "attempt_type": "hinted_attempt" if hints else "independent_attempt",
        "learner_answer_md": "U Sigma V^T", "evidence_facets": ["recall"], "evidence_weights": {"recall": 1.0},
        "rubric_score": 4, "correctness": 1.0, "confidence": 3, "latency_seconds": 30, "hints_used": hints,
        "error_type": None, "grader_confidence": 1.0, "created_at": iso(minutes), "updated_at": iso(minutes),
        "entry_surface": "desktop_reader_workbench",
    })


def _link(repo, session_id: str, attempt_id: str, *, minutes: float) -> None:
    from learnloop.reader import workbench as WB
    from tests.recap_fixtures import at

    WB.mark_submitted(repo, session_id, attempt_id=attempt_id, practice_session_id="ps_1", clock=at(minutes))


# -- the card's sections and their sources ------------------------------------------------------


def test_the_card_reads_still_open_unfinished_and_worth_a_second_look(tmp_path):
    vault, repo = _setup(tmp_path)
    first, second = _seed_session(vault, repo)
    open_root = ask(vault, repo, "Why is the density of a sum a convolution?", 12)
    result = RC.build_recap(vault, repo, extraction_id=EXT, current_visit_id="v_now", now=_now(600))
    card = result["recap"]
    assert card is not None and result["dismissed"] is False
    assert card["session"]["started_at"] == iso(0) and card["session"]["ended_at"] == iso(40)

    # Still open: the open root, in the learner's own words, with its anchor.
    still_open = {line["root_exchange_id"]: line for line in card["still_open"]}
    assert open_root["reader_answer_event_id"] in still_open
    assert still_open[open_root["reader_answer_event_id"]]["question_md"].startswith("Why is the density")
    # The resolved root is not open; the still-unclear root moved to Worth a second look.
    assert second["reader_answer_event_id"] not in still_open
    assert first["reader_answer_event_id"] not in still_open
    [second_look] = card["worth_a_second_look"]
    assert second_look["kind"] == "still_unclear"
    assert second_look["root_exchange_id"] == first["reader_answer_event_id"]
    assert second_look["question_md"].startswith("Why are the densities")

    # Unfinished: the open problem, its steps and the help so far.
    [unfinished] = card["unfinished"]
    assert unfinished["step_count"] == 3
    assert unfinished["help"] == {"book_counted": True, "hints": 0}
    assert unfinished["help_line"] == "help so far: the book"
    assert unfinished["title"].startswith("Exercise 5.14")

    # No counts, no "overdue", no percentage anywhere in what the card says.
    flat = json.dumps(card).lower()
    assert "overdue" not in flat and "%" not in flat


def test_no_card_on_a_first_visit_or_within_the_same_session(tmp_path):
    vault, repo = _setup(tmp_path)
    assert RC.build_recap(vault, repo, extraction_id=EXT, current_visit_id="v1", now=_now(0))["recap"] is None
    visit(repo, "v1", 0, 10)
    ask(vault, repo, "A question", 2)
    # Back twenty minutes later: the same session, and nothing before it.
    assert RC.build_recap(vault, repo, extraction_id=EXT, current_visit_id="v2", now=_now(30))["recap"] is None
    # The next day: the card.
    assert RC.build_recap(vault, repo, extraction_id=EXT, current_visit_id="v3", now=_now(1440))["recap"] is not None


# The dating of "Since last time" runs on the real ledger and the recipe
# predicate: tests/test_reader_recap_review.py (review F1).


def test_since_last_time_reads_the_real_ledger_without_inventing_a_gain(tmp_path):
    vault, repo = _setup(tmp_path)
    _seed_session(vault, repo)
    card = RC.build_recap(vault, repo, extraction_id=EXT, current_visit_id="v_now", now=_now(600))["recap"]
    # Nothing on this vault is demonstrated, so nothing is claimed.
    assert card["since_last_time"] == {"demonstrated": [], "checks_retired": []}


# -- G31: opening a source writes nothing but recap_shown ----------------------------------------


def test_opening_a_source_writes_nothing_but_the_recap_shown_event(tmp_path):
    vault, repo = _setup(tmp_path)
    _seed_session(vault, repo)
    ctx = context(vault.root)
    before_counts, before_rows = table_counts(repo), interaction_rows(repo)
    read = call(ctx, "reader.recap", {"extractionId": EXT, "visitId": "v_now"})
    assert read["recap"] is not None
    assert table_counts(repo) == before_counts and interaction_rows(repo) == before_rows

    call(ctx, "reader.recap_event", {"extractionId": EXT, "visitId": "v_now", "event": "recap_shown"})
    after = interaction_rows(repo)
    new = [row for row in after if row not in before_rows]
    assert len(new) == 1
    _id, kind, subject_type, subject_id, payload_json, _at = new[0]
    payload = json.loads(payload_json)
    assert (kind, subject_type, subject_id) == ("reader_action_invoked", "reader_extraction", EXT)
    assert payload["event"] == "recap_shown" and payload["authority_class"] == "salience_only"
    assert payload["visit_id"] == "v_now"
    changed = {name for name, count in table_counts(repo).items() if before_counts.get(name) != count}
    assert changed == {"interaction_events"}


def test_switched_off_opening_writes_nothing_and_the_recap_rpcs_refuse(tmp_path):
    from learnloop_sidecar.context import config_dto
    from learnloop_sidecar.errors import SidecarError

    vault, repo = _setup(tmp_path)
    _seed_session(vault, repo)
    append_config_toml(vault.root, """
    [recap]
    enabled = false
    wrap_up_enabled = false
    """)
    ctx = context(vault.root)
    before_counts, before_rows = table_counts(repo), interaction_rows(repo)
    for name, params in (
        ("reader.recap", {"extractionId": EXT, "visitId": "v_now"}),
        ("reader.recap_event", {"extractionId": EXT, "visitId": "v_now", "event": "recap_shown"}),
        ("reader.recap_event", {"extractionId": EXT, "visitId": "v_now", "event": "recap_dismissed"}),
    ):
        with pytest.raises(SidecarError) as refused:
            call(ctx, name, params)
        assert refused.value.code == "recap_disabled"
    assert table_counts(repo) == before_counts and interaction_rows(repo) == before_rows
    assert "recap" not in config_dto(load_vault(vault.root))


def test_the_kill_switches_default_on_and_the_config_dto_names_them(tmp_path):
    from learnloop_sidecar.context import config_dto

    vault, _repo = _setup(tmp_path)
    assert RC.recap_enabled(vault) is True and RC.wrap_up_enabled(vault) is True
    assert config_dto(vault)["recap"] == {"enabled": True, "wrapUpEnabled": True}


def test_unknown_recap_events_are_refused_before_any_write(tmp_path):
    from learnloop_sidecar.errors import SidecarError

    vault, repo = _setup(tmp_path)
    ctx = context(vault.root)
    before = interaction_rows(repo)
    with pytest.raises(SidecarError) as refused:
        call(ctx, "reader.recap_event", {"extractionId": EXT, "event": "recap_clicked"})
    assert refused.value.code == "validation_error"
    assert interaction_rows(repo) == before


# -- dismiss: hidden for this source until the next session --------------------------------------


def test_dismiss_hides_the_card_until_the_next_session(tmp_path):
    vault, repo = _setup(tmp_path)
    _seed_session(vault, repo)
    open_visit(repo, "v2", 600)
    RC.record_recap_event(repo, extraction_id=EXT, event="recap_dismissed", visit_id="v2",
                          clock=_frozen(601))
    hidden = RC.build_recap(vault, repo, extraction_id=EXT, current_visit_id="v2", now=_now(602))
    assert hidden == {"recap": None, "dismissed": True}
    close_visit(repo, "v2", 610)
    # Back within 30 minutes: the same session, still hidden.
    assert RC.build_recap(vault, repo, extraction_id=EXT, current_visit_id="v3", now=_now(630))["dismissed"] is True
    # The next session: the card returns (now about the dismissed session).
    back = RC.build_recap(vault, repo, extraction_id=EXT, current_visit_id="v4", now=_now(2000))
    assert back["dismissed"] is False and back["recap"]["session"]["started_at"] == iso(600)


def _frozen(minutes: float):
    from tests.recap_fixtures import at

    return at(minutes)

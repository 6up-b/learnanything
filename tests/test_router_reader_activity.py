"""Reader workbench RW6b part 2: reader activity for the router's learner-state
card (spec_reader_workbench_v1 §9.2; router spec §4; G25;
docs/reviews/reader-rw6b-p2-digest-card.md).

* ``reader_activity_for_card(lo_ids, as_of)`` is a pure read: computed twice
  it is identical, it writes nothing, and it reads strictly before ``as_of``.
* Its contents: open inquiries (excerpt, age, depth), assisted-only work,
  pending reader follow-ups with their valuation, formative records, open
  hypotheses, candidate actions with where each came from, the latest
  narrative labelled model-written with its cited ids; exam-anchored
  inquiries keep their entry and never their words.
* It is the card's "Reader activity" section (Codex review F1): typed in
  ``evidence_sections.reader_activity``, rendered in the card's text, hashed
  and stored, so the router models read it. With nothing on the candidates'
  LOs, or with ``digest.enabled`` off, the card is the predecessor's byte for
  byte. Unreadable: named in the card's unknowns.
* Absent with ``digest.enabled`` or ``reader_inquiry.enabled`` off; the
  narrative also with ``digest.narrative_enabled`` off (F4).
* Bounded by ``as_of`` (F5): the same historical cutoff reads the same before
  and after later writes (a resolution, an undo, a later narrative).
* Missed figure predictions are scoped through their figure's passages (F6);
  open hypotheses leave out reversed gaps and closed episodes, once each (F8).

Fakes only; no model call anywhere.
"""

from __future__ import annotations

import dataclasses
import json

import pytest

from learnloop.daily_plan import router_reader as RR
from learnloop.instructional import reader_digest as RN
from learnloop.reader import reader_sessions as RS
from learnloop.router.card import build_card
from learnloop.vault.loader import load_vault
from tests.recap_fixtures import EXT, ask, at, iso
from tests.test_reader_digest_narrative import NarrativeFake
from tests.test_reader_followups import FakeSearch, _candidate, _now, _plan, _seeded

LO = "lo_svd_definition"
QUESTION = "Why three factors and not two?"


@pytest.fixture
def reader_world(tmp_path, monkeypatch):
    """One ended session (0-40 min) with a question on s1, a follow-up up
    (the book-and-hint problem's claim) and a kept narrative."""

    import learnloop.reader.reader_progression as progression
    import learnloop.reader.recap as recap

    # The synthetic extraction's spans teach the LO (the recap's and the card's mapping).
    monkeypatch.setattr(recap, "learning_objects_for_span", lambda *_a, **_k: [LO])
    monkeypatch.setattr(progression, "learning_objects_for_span", lambda *_a, **_k: [LO])
    vault, repo, _session = _seeded(tmp_path)
    exchange = ask(vault, repo, QUESTION, 5)
    follow = ask(vault, repo, "And the middle one?", 6, parent=exchange["reader_answer_event_id"])
    session = RS.sessions_for_source(repo, EXT)[0]
    row = _plan(vault, repo, session, FakeSearch([_candidate("pi_svd_define_002", 0.99, 0.01, 1.0)]))
    assert RN.narrate_digest(vault, repo, row["id"], client=NarrativeFake(), now=_now(),
                             clock=at(300)).status == "narrated"
    return vault, repo, row, exchange, follow


def _table_counts(repo) -> dict[str, int]:
    with repo.connection() as connection:
        names = [r[0] for r in connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'")]
        return {name: connection.execute(f'SELECT COUNT(*) FROM "{name}"').fetchone()[0] for name in names}


def test_the_reader_activity_carries_what_the_spec_lists(reader_world):
    vault, repo, row, exchange, follow = reader_world
    activity = RR.reader_activity_for_card(vault, repo, [LO], iso(400))
    assert activity["activity_version"] == RR.ACTIVITY_VERSION and activity["authority"] == "routing_only"
    assert set(RR.SECTIONS) <= set(activity)
    [inquiry] = activity["open_inquiries"]
    assert inquiry["root_exchange_id"] == exchange["reader_answer_event_id"]
    assert inquiry["question_excerpt"] == QUESTION and inquiry["depth"] == 1 and inquiry["exchanges"] == 2
    assert inquiry["age_days"] == 0 and inquiry["learning_object_ids"] == [LO]
    [pending] = activity["pending_followups"]
    assert pending["commitment_id"] == row["followup_commitment_ids"][0] and pending["purpose"] == "retention"
    assert pending["due_hint"] and pending["valuation"]["scale"] == row["valuation"]["scale"]
    assert pending["valuation"]["value_minutes_lcb"] is not None
    assert [entry["facet_id"] for entry in activity["assisted_only"]] == [
        claim["facet_id"] for claim in row["summary"]["claims_needing_independent_check"]]
    kinds = [action["kind"] for action in activity["candidate_actions"]]
    assert kinds[0] == "pending_followup" and activity["candidate_actions"][0]["from"] == "reader_followup"
    narrative = activity["narrative"]
    assert narrative["label"] == "summary written by LearnLoop's model" and narrative["authority"] == "salience_only"
    assert narrative["text"] == NarrativeFake().text and narrative["cited_event_ids"]


def test_it_is_a_pure_read(reader_world):
    vault, repo, *_rest = reader_world
    before = _table_counts(repo)
    with repo.connection() as connection:
        changes = connection.total_changes
    first = RR.reader_activity_for_card(vault, repo, [LO], iso(400))
    second = RR.reader_activity_for_card(vault, repo, [LO], iso(400))
    assert json.dumps(first, sort_keys=True, default=str) == json.dumps(second, sort_keys=True, default=str)
    assert _table_counts(repo) == before
    with repo.connection() as connection:
        assert connection.total_changes == changes


def test_it_reads_strictly_before_as_of_and_only_these_los(reader_world):
    vault, repo, *_rest = reader_world
    early = RR.reader_activity_for_card(vault, repo, [LO], iso(30))  # before the session ended
    assert early["open_inquiries"] == [] and early["pending_followups"] == [] and early["narrative"] is None
    other = RR.reader_activity_for_card(vault, repo, ["lo_unrelated"], iso(400))
    assert other["open_inquiries"] == [] and other["pending_followups"] == [] and other["narrative"] is None


def test_a_resolved_inquiry_is_no_longer_open(reader_world):
    from tests.recap_fixtures import resolve

    vault, repo, _row, exchange, _follow = reader_world
    resolve(repo, exchange["reader_answer_event_id"], 320)
    assert RR.reader_activity_for_card(vault, repo, [LO], iso(400))["open_inquiries"] == []


def test_an_exam_anchored_inquiry_keeps_its_entry_and_never_its_words(reader_world, monkeypatch):
    from learnloop.content.sources import exam_material as EM

    vault, repo, *_rest = reader_world
    monkeypatch.setattr(EM, "exam_withheld", lambda _v, _r, keys: frozenset(tuple(k) for k in keys))
    [inquiry] = RR.reader_activity_for_card(vault, repo, [LO], iso(400))["open_inquiries"]
    assert inquiry["question_excerpt"] is None and inquiry["withheld"] == "exam_material"

    def unreadable(*_a, **_k):
        raise RuntimeError("predicate down")

    monkeypatch.setattr(EM, "exam_withheld", unreadable)
    [inquiry] = RR.reader_activity_for_card(vault, repo, [LO], iso(400))["open_inquiries"]
    assert inquiry["question_excerpt"] is None  # fail closed


@pytest.mark.parametrize("config", ["[digest]\nenabled = false\n", "[reader_inquiry]\nenabled = false\n"])
def test_the_section_is_absent_with_its_switches_off(reader_world, config):
    from tests.helpers import append_config_toml

    vault, repo, *_rest = reader_world
    append_config_toml(vault.root, config)
    vault = load_vault(vault.root)
    assert RR.reader_activity_for_card(vault, repo, [LO], iso(400)) is None


# -- the card's "Reader activity" section (Codex review F1) ------------------------------------


PLANTED = "PLANTED_7781"
ACTIVITY = {"activity_version": RR.ACTIVITY_VERSION, "authority": RR.AUTHORITY, "as_of": "2026-10-12T09:00:00Z",
            "learning_object_ids": ["lo_m1"],
            "open_inquiries": [{"question_excerpt": PLANTED, "age_days": 2, "depth": 1, "exchanges": 2,
                                "learning_object_ids": ["lo_m1"]}],
            "assisted_only": [], "pending_followups": [], "missed_predictions": [], "open_hypotheses": [],
            "formative_records": [], "kept_comparisons": [],
            "candidate_actions": [{"kind": "continue_reading", "from": "reader_section_progress",
                                   "label": "2.3 The SVD"}],
            "narrative": {"text": "You read 2.3.", "label": "summary written by LearnLoop's model",
                          "cited_event_ids": ["e1"], "authority": "salience_only", "ended_at": "2026-10-11"}}


def _with_section(inputs, activity):
    return dataclasses.replace(inputs, evidence_sections={**inputs.evidence_sections,
                                                          RR.CARD_SECTION: RR.for_card(activity)})


def test_the_section_is_in_the_typed_card_its_text_and_its_hash():
    from tests.test_router_card import _inputs

    inputs = _inputs(3)
    without = build_card(inputs)
    card = build_card(_with_section(inputs, ACTIVITY))
    assert card.card_hash != without.card_hash
    section = card.json["evidence_sections"]["reader_activity"]
    assert section["open_inquiries"][0]["question_excerpt"] == PLANTED and "as_of" not in section
    assert "# Reader activity (from the Reader; routing only, never evidence)" in card.text
    assert PLANTED in card.text and "continue_reading, 2.3 The SVD" in card.text
    assert "summary written by LearnLoop's model (2026-10-11; cites 1 events): You read 2.3." in card.text
    assert PLANTED in json.dumps(card.payload())
    # Never evidence: the router never cites a reader entry as evidence.
    from learnloop.router.requests import evidence_from_card

    assert evidence_from_card(card.json) == evidence_from_card(without.json)


def test_nothing_to_say_leaves_the_predecessor_card_byte_for_byte():
    from tests.test_router_card import _inputs

    empty = {**ACTIVITY, "open_inquiries": [], "candidate_actions": [], "narrative": None}
    assert RR.for_card(empty) is None and RR.for_card(None) is None
    inputs = _inputs(3)
    assert build_card(inputs).payload() == build_card(inputs).payload()
    assert "Reader activity" not in build_card(inputs).text


def test_the_card_copy_is_bounded_and_says_what_it_left_out():
    many = {**ACTIVITY, "open_inquiries": [{"question_excerpt": f"q{i}", "learning_object_ids": ["lo_m1"]}
                                           for i in range(RR.CARD_LIST_LIMIT + 3)]}
    section = RR.for_card(many)
    assert [e["question_excerpt"] for e in section["open_inquiries"]] == [
        f"q{i}" for i in range(3, RR.CARD_LIST_LIMIT + 3)]  # the newest
    assert section["omitted"] == {"open_inquiries": 3}
    from tests.test_router_card import _inputs

    assert "(3 older reader entries left out)" in build_card(_with_section(_inputs(1), many)).text


# -- re-review F9: the reader section is inside the card's token budget ---------------------------


def _busy(inquiries: int = RR.CARD_LIST_LIMIT) -> dict:
    words = "w" * (RR.EXCERPT_CHARS - 1)
    return {**ACTIVITY,
            "open_inquiries": [{"question_excerpt": f"{i}{words}", "age_days": i, "depth": 3, "exchanges": 9,
                                "learning_object_ids": ["lo"]} for i in range(inquiries)],
            "candidate_actions": [{"kind": "continue_reading", "from": "reader_section_progress",
                                   "label": "2.3 The SVD"}],
            "narrative": {**ACTIVITY["narrative"], "text": "word " * 120}}


@pytest.mark.parametrize("budget", [1_000, 1_500, 2_000])
def test_the_reader_section_fits_wherever_the_predecessor_card_fits(budget):
    from tests.test_router_card import _inputs

    inputs = _inputs(3)
    predecessor = build_card(inputs, token_budget=budget)
    assert predecessor.tokens <= budget
    card = build_card(_with_section(inputs, _busy()), token_budget=budget)
    assert card.tokens <= budget
    # The predecessor's content is never traded for reader entries.
    assert card.json["recent_work"] == predecessor.json["recent_work"]
    assert {key: card.truncation[key] for key in predecessor.truncation} == predecessor.truncation


def test_the_budget_trims_reader_entries_deterministically_and_says_so():
    from tests.test_router_card import _inputs

    inputs = _with_section(_inputs(3), _busy())
    full = build_card(inputs, token_budget=10**6)
    assert len(full.json["evidence_sections"]["reader_activity"]["open_inquiries"]) == RR.CARD_LIST_LIMIT
    budget = full.tokens - 200
    card = build_card(inputs, token_budget=budget)
    assert card.tokens <= budget and card == build_card(inputs, token_budget=budget)
    section = card.json["evidence_sections"]["reader_activity"]
    kept = section["open_inquiries"]
    left = section["omitted"]
    assert sum(left.values()) == card.truncation["dropped_reader_entries"] > 0
    # The newest inquiries stay (oldest first in the list); the typed card's own record is the section's.
    assert kept == full.json["evidence_sections"]["reader_activity"]["open_inquiries"][-len(kept):]
    assert "dropped_reader_entries" not in card.json["truncation"]
    assert f"({sum(left.values())} older reader entr" in card.text
    # With no room for any of it, the section goes whole and the card is the predecessor's.
    bare = build_card(_inputs(3), token_budget=10**6)
    gone = build_card(inputs, token_budget=bare.tokens)
    assert gone.json == bare.json and gone.text == bare.text and gone.card_hash == bare.card_hash
    assert gone.truncation["dropped_reader_section"] == 1


def test_the_router_reads_the_section_and_the_kill_switch_restores_the_predecessor(tmp_path, monkeypatch):
    from learnloop.daily_plan.engine import _live_context, decide, get_or_create_today
    from tests.test_router_card import _card_world

    env = _card_world(tmp_path, monkeypatch)
    gatherer = env.policy.chooser.card_builder
    record = get_or_create_today(env)
    context, _built = _live_context(env, record)
    decision = decide(record, context, env.policy.projection())

    monkeypatch.setattr(RR, "reader_activity_for_card", lambda *_a, **_k: dict(ACTIVITY))
    card_on = gatherer(decision.state, decision.feasible)
    assert PLANTED in card_on.text and card_on.json["evidence_sections"]["reader_activity"]

    # digest.enabled off: no read at all, the predecessor's card.
    monkeypatch.setattr(RR, "reader_activity_enabled", lambda _vault: False)
    card_off = gatherer(decision.state, decision.feasible)
    # Nothing on these LOs: the same card as off, byte for byte.
    monkeypatch.setattr(RR, "reader_activity_enabled", lambda _vault: True)
    monkeypatch.setattr(RR, "reader_activity_for_card", lambda *_a, **_k: {
        **ACTIVITY, "open_inquiries": [], "candidate_actions": [], "narrative": None})
    card_empty = gatherer(decision.state, decision.feasible)
    assert card_off.payload() == card_empty.payload() and card_off.card_hash == card_empty.card_hash
    assert "reader_activity" not in card_off.json["evidence_sections"] and PLANTED not in card_off.text
    assert card_on.card_hash != card_off.card_hash



def test_the_plan_stores_the_card_with_its_reader_section(tmp_path, monkeypatch):
    from learnloop.daily_plan.engine import build_plan
    from tests.test_router_card import _card_world, _stored_card

    env = _card_world(tmp_path, monkeypatch)
    monkeypatch.setattr(RR, "reader_activity_for_card", lambda *_a, **_k: dict(ACTIVITY))
    build_plan(env, kind="normal", budget=25.0, remembered=25, minutes_source="chip")
    row, payload = _stored_card(env)
    assert PLANTED in payload["content_text"] and PLANTED in payload["content_json"]
    assert row["card_hash"] == payload["content_hash"]


def test_an_unreadable_section_is_named_in_the_unknowns(tmp_path, monkeypatch):
    from learnloop.daily_plan.engine import _live_context, decide, get_or_create_today
    from tests.test_router_card import _card_world

    env = _card_world(tmp_path, monkeypatch)
    gatherer = env.policy.chooser.card_builder
    record = get_or_create_today(env)
    context, _built = _live_context(env, record)
    decision = decide(record, context, env.policy.projection())

    def broken(*_a, **_k):
        raise RuntimeError("digest table unreadable")

    monkeypatch.setattr(RR, "reader_activity_for_card", broken)
    card = gatherer(decision.state, decision.feasible)
    assert "reader activity could not be read" in card.json["unknowns"]
    assert "reader_activity" not in card.json["evidence_sections"]


# -- F4: the narrative switch reaches every surface ---------------------------------------------


def test_narration_switched_off_after_a_narrative_was_saved_shows_it_nowhere(reader_world):
    from tests.helpers import append_config_toml
    from tests.test_router_card import _inputs

    vault, repo, row, *_rest = reader_world
    assert RR.reader_activity_for_card(vault, repo, [LO], iso(400))["narrative"] is not None
    append_config_toml(vault.root, "[digest]\nnarrative_enabled = false\n")
    vault = load_vault(vault.root)
    activity = RR.reader_activity_for_card(vault, repo, [LO], iso(400))
    assert activity is not None and activity["narrative"] is None
    assert activity["open_inquiries"] and activity["pending_followups"]  # the rest stays
    section = RR.for_card(activity)
    assert "narrative" not in section and NarrativeFake().text not in json.dumps(section)
    card = build_card(_with_section(_inputs(1), activity))
    assert NarrativeFake().text not in card.text and NarrativeFake().text not in json.dumps(card.payload())
    # The recap and Wrap up views (the card's and Wrap up's narrative) are absent too.
    assert RN.narrative_view(vault, repo, extraction_id=EXT, session_key=row["session_key"], now=_now()) is None


# -- F5: as_of bounds every mutable read ---------------------------------------------------------


def _same(first, second):
    return json.dumps(first, sort_keys=True, default=str) == json.dumps(second, sort_keys=True, default=str)


def test_a_historical_cutoff_reads_the_same_after_a_later_resolution(reader_world):
    from tests.recap_fixtures import resolve

    vault, repo, _row, exchange, _follow = reader_world
    before = RR.reader_activity_for_card(vault, repo, [LO], iso(400))
    assert before["open_inquiries"]
    resolve(repo, exchange["reader_answer_event_id"], 500)
    assert _same(RR.reader_activity_for_card(vault, repo, [LO], iso(400)), before)
    assert RR.reader_activity_for_card(vault, repo, [LO], iso(600))["open_inquiries"] == []


def test_a_historical_cutoff_reads_the_same_after_a_later_undo(reader_world):
    from learnloop.instructional import reader_followups as RF

    vault, repo, row, *_rest = reader_world
    before = RR.reader_activity_for_card(vault, repo, [LO], iso(400))
    assert before["pending_followups"]
    RF.undo_followup(repo, commitment_id=row["followup_commitment_ids"][0], clock=at(500))
    assert _same(RR.reader_activity_for_card(vault, repo, [LO], iso(400)), before)
    assert RR.reader_activity_for_card(vault, repo, [LO], iso(600))["pending_followups"] == []


def test_a_historical_cutoff_ignores_a_later_unaided_success(reader_world, monkeypatch):
    from types import SimpleNamespace

    import learnloop.learner.facet_evidence_timeline as timeline

    vault, repo, *_rest = reader_world
    before = RR.reader_activity_for_card(vault, repo, [LO], iso(400))
    [claim] = before["assisted_only"]
    later = SimpleNamespace(attempt_id="att_later", t=iso(500), attempt_banked_credit=1.0, assisted=False,
                            primed=False)
    monkeypatch.setattr(timeline, "facet_evidence_timelines",
                        lambda _v, _r, facets: {facet: [later] for facet in facets})
    assert _same(RR.reader_activity_for_card(vault, repo, [LO], iso(400)), before)
    assert RR.reader_activity_for_card(vault, repo, [LO], iso(600))["assisted_only"] == []
    assert claim["facet_id"]


def test_a_narrative_written_after_the_cutoff_is_not_shown_at_it(tmp_path, monkeypatch):
    import learnloop.reader.reader_progression as progression
    import learnloop.reader.recap as recap

    monkeypatch.setattr(recap, "learning_objects_for_span", lambda *_a, **_k: [LO])
    monkeypatch.setattr(progression, "learning_objects_for_span", lambda *_a, **_k: [LO])
    vault, repo, _session = _seeded(tmp_path)
    ask(vault, repo, QUESTION, 5)
    session = RS.sessions_for_source(repo, EXT)[0]
    row = _plan(vault, repo, session, FakeSearch([_candidate("pi_svd_define_002", 0.99, 0.01, 1.0)]))
    before = RR.reader_activity_for_card(vault, repo, [LO], iso(400))
    assert before["narrative"] is None
    assert RN.narrate_digest(vault, repo, row["id"], client=NarrativeFake(), now=_now(500),
                             clock=at(500)).status == "narrated"
    assert _same(RR.reader_activity_for_card(vault, repo, [LO], iso(400)), before)
    assert RR.reader_activity_for_card(vault, repo, [LO], iso(600))["narrative"]["text"] == NarrativeFake().text


# -- F6: a missed figure prediction is scoped through its figure ---------------------------------


def _missed_prediction(repo, minutes: float) -> str:
    with repo.connection() as connection:
        connection.execute(
            "INSERT INTO interactive_figures (id, extraction_id, span_ids_json, input_span_ids_json, origin, "
            "spec_version, verification, prompt_version, input_hash, created_at) "
            "VALUES ('fig_1', ?, '[\"s1\"]', '[\"s1\"]', 'selection', 'v1', 'failed', 'p1', 'h1', ?)",
            (EXT, iso(minutes)))
        connection.execute(
            "INSERT INTO figure_predictions (id, figure_id, extraction_id, prediction_index, learner_answer, "
            "observed_json, matched, created_at) VALUES ('pred_1', 'fig_1', ?, 0, 'rises', '{}', 0, ?)",
            (EXT, iso(minutes)))
        connection.commit()
    return "pred_1"


def test_a_real_missed_prediction_reaches_the_section_through_its_figure(tmp_path, monkeypatch):
    import learnloop.reader.reader_progression as progression
    import learnloop.reader.recap as recap

    spans_asked = []
    monkeypatch.setattr(recap, "learning_objects_for_span", lambda *_a, **_k: [LO])
    def spans_to_los(*_a, span_id=None, **_k):
        spans_asked.append(span_id)
        return [LO] if span_id == "s1" else []

    monkeypatch.setattr(progression, "learning_objects_for_span", spans_to_los)
    vault, repo, _session = _seeded(tmp_path)
    prediction_id = _missed_prediction(repo, 10)
    session = RS.sessions_for_source(repo, EXT)[0]
    row = _plan(vault, repo, session, FakeSearch([_candidate("pi_svd_define_002", 0.99, 0.01, 1.0)]))
    [record] = row["summary"]["predictions_missed"]
    assert record["facet_candidates"] == [] and record["span_ids"] == []  # the production shape
    activity = RR.reader_activity_for_card(vault, repo, [LO], iso(400))
    assert [r["source_event_ids"] for r in activity["missed_predictions"]] == [[prediction_id]]
    assert "s1" in spans_asked
    # The session's formative records carry the same prediction, scoped the same way (re-review F6).
    observed = [r for r in row["summary"]["observations"] if r.get("kind") == "prediction_missed"]
    assert [r["source_event_ids"] for r in observed] == [[prediction_id]]
    assert [r["source_event_ids"] for r in activity["formative_records"]
            if r.get("kind") == "prediction_missed"] == [[prediction_id]]
    other = RR.reader_activity_for_card(vault, repo, ["lo_unrelated"], iso(400))
    assert other["missed_predictions"] == [] and other["formative_records"] == []


def test_a_session_that_touched_the_lo_only_through_a_figure_is_kept_for_its_prediction(tmp_path, monkeypatch):
    """Final verify F6, its reproduction: the session's summary names LO A (its
    other work), its missed prediction's figure is on a distinct LO B, and the
    prediction names no facet or span. Asking for B keeps the session for the
    prediction (figure, then passage, then LO) instead of discarding it before
    the provenance is read."""

    import learnloop.reader.reader_progression as progression
    import learnloop.reader.recap as recap

    lo_b = "lo_figure_only_b"
    spans = {"s1": [lo_b], "s2": [LO]}  # the figure's passage is on B; the inquiry's on A
    monkeypatch.setattr(recap, "learning_objects_for_span", lambda *_a, span_id=None, **_k: spans.get(span_id, []))
    monkeypatch.setattr(progression, "learning_objects_for_span",
                        lambda *_a, span_id=None, **_k: spans.get(span_id, []))
    vault, repo, _session = _seeded(tmp_path)
    ask(vault, repo, "WHY_A_7731", 5, span_id="s2")
    prediction_id = _missed_prediction(repo, 10)
    session = RS.sessions_for_source(repo, EXT)[0]
    row = _plan(vault, repo, session, FakeSearch([_candidate("pi_svd_define_002", 0.99, 0.01, 1.0)]))
    summary = row["summary"]
    assert summary["learning_objects_touched"] == [LO]
    [record] = summary["predictions_missed"]
    assert record["facet_candidates"] == [] and record["span_ids"] == []
    activity = RR.reader_activity_for_card(vault, repo, [lo_b], iso(400))
    assert [r["source_event_ids"] for r in activity["missed_predictions"]] == [[prediction_id]]
    assert [r["source_event_ids"] for r in activity["formative_records"]] == [[prediction_id]]
    # The session's other work stays scoped to its own LO: nothing of A's leaks into B's lists.
    assert activity["open_inquiries"] == [] and activity["assisted_only"] == []
    assert activity["pending_followups"] == []
    # A keeps its inquiry and does not take B's prediction; an unrelated LO still sees nothing.
    for_a = RR.reader_activity_for_card(vault, repo, [LO], iso(400))
    assert len(for_a["open_inquiries"]) == 1 and for_a["missed_predictions"] == []
    other = RR.reader_activity_for_card(vault, repo, ["lo_unrelated"], iso(400))
    assert other["missed_predictions"] == [] and other["formative_records"] == []


# -- F8: open hypotheses as they stood, once each -------------------------------------------------


def _row(digest_id, ended, *, gaps=(), questions=()):
    return {"id": digest_id, "ended_at": ended, "summary": {"gaps_named": list(gaps)},
            "valuation": {"questions": list(questions)}}


def _rival(key, targets):
    return {"key": key, "outcome": "checks", "question": {"purpose": "discriminating", "learning_object_ids": [LO],
                                                          "target_hypotheses": targets, "raised_by": []}}


def test_a_reversed_gap_and_a_closed_episode_are_not_open_hypotheses(reader_world, monkeypatch):
    from types import SimpleNamespace

    vault, repo, *_rest = reader_world
    with repo.connection() as connection:
        connection.execute("PRAGMA foreign_keys = OFF")
        connection.execute(
            "INSERT INTO learner_text_gap_reversals (id, gap_id, reversal, actor, detail_json, created_at) "
            "VALUES ('rev_1', 'gap_rev', 'undo_edge', 'learner', '{}', ?)", (iso(350),))
        connection.commit()
    episodes = {"ep_closed": SimpleNamespace(status="complete", created_at=iso(1), completed_at=iso(350),
                                             updated_at=iso(350)),
                "ep_open": SimpleNamespace(status="in_progress", created_at=iso(1), completed_at=None,
                                           updated_at=iso(1))}
    monkeypatch.setattr(repo, "probe_episode", lambda episode_id: episodes.get(episode_id))
    rows = [
        _row("d1", iso(40), gaps=[{"gap_id": "gap_keep", "kind": "prerequisite", "target_kind": "learning_object",
                                   "target_id": LO, "source_id": "q1"},
                                  {"gap_id": "gap_rev", "kind": "misconception", "source_id": "q2"}],
             questions=[_rival(f"discriminate:{LO}", [{"kind": "episode_label", "id": "ep_closed"},
                                                      {"kind": "named_gap", "id": "gap_rev"}])]),
        _row("d2", iso(140), gaps=[{"gap_id": "gap_keep", "kind": "prerequisite", "target_kind": "learning_object",
                                    "target_id": LO, "source_id": "q1"}],
             questions=[_rival(f"discriminate:{LO}", [{"kind": "episode_label", "id": "ep_open"},
                                                      {"kind": "episode_label", "id": "ep_closed"}])]),
    ]
    now = RR._open_hypotheses(repo, rows, {LO}, RR.parse_utc(iso(400)))
    assert [(h["kind"], h.get("gap_id") or h.get("question")) for h in now] == [
        ("named_gap", "gap_keep"), ("rival_explanations", f"discriminate:{LO}")]
    assert now[0]["source"]["digest_id"] == "d2"  # the latest session that named it, once
    assert now[1]["target_hypotheses"] == [{"kind": "episode_label", "id": "ep_open"}]
    # Before the reversal and the close (minute 300) both were still open.
    then = RR._open_hypotheses(repo, rows, {LO}, RR.parse_utc(iso(300)))
    assert {h.get("gap_id") for h in then if h["kind"] == "named_gap"} == {"gap_keep", "gap_rev"}
    [rival] = [h for h in then if h["kind"] == "rival_explanations"]
    assert rival["target_hypotheses"] == [{"kind": "episode_label", "id": "ep_open"},
                                          {"kind": "episode_label", "id": "ep_closed"}]
    # Every target settled: the rival goes.
    gone = RR._open_hypotheses(repo, [rows[0]], {LO}, RR.parse_utc(iso(400)))
    assert [h for h in gone if h["kind"] == "rival_explanations"] == []

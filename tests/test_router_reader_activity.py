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
* It is data beside the card: the card's hash, text, JSON, tokens and stored
  payload are the same with and without it, and so is every router decision.
* Absent with ``digest.enabled`` or ``reader_inquiry.enabled`` off.

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


# -- data beside the card: no hash, text, payload or decision changes ----------------------------


def test_the_card_is_byte_identical_with_the_section_present():
    from tests.test_router_card import _inputs

    inputs = _inputs(3)
    activity = {"activity_version": RR.ACTIVITY_VERSION, "open_inquiries": [{"question_excerpt": "why?"}],
                "narrative": {"text": "You read.", "label": "summary written by LearnLoop's model"}}
    without = build_card(inputs)
    with_section = build_card(dataclasses.replace(inputs, reader_activity=activity))
    assert with_section.card_hash == without.card_hash
    assert with_section.text == without.text and with_section.json == without.json
    assert with_section.tokens == without.tokens and with_section.payload() == without.payload()
    assert with_section == without  # equality ignores the section
    assert with_section.reader_activity == activity and without.reader_activity is None
    assert "why?" not in with_section.text and "reader_activity" not in with_section.json


def test_router_decisions_and_stored_cards_are_unchanged_with_the_section_present(tmp_path, monkeypatch):
    from learnloop.daily_plan.engine import _live_context, build_plan, decide, get_or_create_today
    from tests.test_router_card import _card_world, _stored_card

    env = _card_world(tmp_path, monkeypatch)
    activity = {"activity_version": RR.ACTIVITY_VERSION, "open_inquiries": [{"question_excerpt": "PLANTED_7781"}],
                "candidate_actions": [{"kind": "continue_reading", "from": "reader_section_progress"}]}
    gatherer = env.policy.chooser.card_builder
    record = get_or_create_today(env)
    context, _built = _live_context(env, record)

    monkeypatch.setattr(RR, "reader_activity_enabled", lambda _vault: False)
    decision_off = decide(record, context, env.policy.projection())
    card_off = gatherer(decision_off.state, decision_off.feasible)
    monkeypatch.setattr(RR, "reader_activity_enabled", lambda _vault: True)
    monkeypatch.setattr(RR, "reader_activity_for_card", lambda *_a, **_k: activity)
    decision_on = decide(record, context, env.policy.projection())
    card_on = gatherer(decision_on.state, decision_on.feasible)

    assert card_on.reader_activity == activity and card_off.reader_activity is None
    assert card_on.card_hash == card_off.card_hash and card_on.text == card_off.text
    assert card_on.json == card_off.json and card_on.payload() == card_off.payload()
    assert decision_on.choice.candidate_id == decision_off.choice.candidate_id
    assert decision_on.choice.why == decision_off.choice.why
    assert [c.candidate_id for c in decision_on.feasible] == [c.candidate_id for c in decision_off.feasible]

    # The plan built with the section present stores the card a section-less builder gives.
    build_plan(env, kind="normal", budget=25.0, remembered=25, minutes_source="chip")
    row, payload = _stored_card(env)
    assert "PLANTED_7781" not in payload["content_text"] and "PLANTED_7781" not in payload["content_json"]
    assert row["card_hash"] == payload["content_hash"]


def test_an_unreadable_section_never_names_itself_in_the_hashed_unknowns(tmp_path, monkeypatch):
    from learnloop.daily_plan.engine import _live_context, decide, get_or_create_today
    from tests.test_router_card import _card_world

    env = _card_world(tmp_path, monkeypatch)
    gatherer = env.policy.chooser.card_builder
    record = get_or_create_today(env)
    context, _built = _live_context(env, record)
    decision = decide(record, context, env.policy.projection())
    clean = gatherer(decision.state, decision.feasible)

    def broken(*_a, **_k):
        raise RuntimeError("digest table unreadable")

    monkeypatch.setattr(RR, "reader_activity_for_card", broken)
    card = gatherer(decision.state, decision.feasible)
    assert card.reader_activity is None and card.card_hash == clean.card_hash

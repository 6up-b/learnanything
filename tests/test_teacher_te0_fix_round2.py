"""Teacher TE0, fix round 2 (docs/reviews/teacher-te0-codex-review.md, the
scoped verify's two Mediums).

* R2-1: an offline review's history takes an attempt's hold from the same
  source as its score: a review grade that holds a previously scored attempt
  renders "held for review" (no score) in a later target's history, never
  "wrong";
* R2-2: the card's confidence metadata (the stated limit and the omission
  notice) counts in the token budget and drops when it does not fit, so the
  card never exceeds the budget whenever the predecessor's card would fit.

Fakes only; no model is called.
"""

from __future__ import annotations

from contextlib import closing
from dataclasses import replace

from learnloop import confidence_events as CE
from learnloop.db.connection import connect
from learnloop.router.card import build_card

from tests.test_teacher_te0_confidence_events import _card_inputs
from tests.test_teacher_te0_review_fixes import HELD_SUPPORT

HELD_EVENT = "marked 5/5 sure; held for review (no score yet)"


# -- R2-1: held offline grades in the history ------------------------------------------------


class _HeldRecord:
    """A validated blind grade whose record the route rule held."""

    def __init__(self, validated):
        self._validated = validated

    def as_record(self):
        return {**self._validated.as_record(), "grading_support": dict(HELD_SUPPORT)}


def test_a_held_review_grade_reads_held_for_review_in_a_later_targets_history(tmp_path, monkeypatch):
    from learnloop.diagnosis.offline_review import runner as runner_module
    from learnloop.learner_protection import held_attempts
    from tests.diagnosis_split_helpers import build_diagnosis_vault, seed_history
    from tests.test_diagnose_review import OPTIONS, _run

    real_validate = runner_module.validate_blind_grading_proposal

    def validate(proposal, *, attempt_id, **kwargs):
        validated = real_validate(proposal, attempt_id=attempt_id, **kwargs)
        # The review's grader holds every real target (the vault scored them).
        return validated if str(attempt_id).startswith("planted") else _HeldRecord(validated)

    monkeypatch.setattr(runner_module, "validate_blind_grading_proposal", validate)
    seen: list = []
    real_diagnosis = runner_module.run_diagnosis

    def spy(client, **kwargs):
        seen.append((kwargs["current"], kwargs["store"]))
        return real_diagnosis(client, **kwargs)

    monkeypatch.setattr(runner_module, "run_diagnosis", spy)
    paths = build_diagnosis_vault(tmp_path / "vault")
    vault, repository = seed_history(paths)
    with closing(connect(paths.sqlite_path)) as connection:
        connection.execute("UPDATE practice_attempts SET answer_confidence = 5")
        connection.commit()
        scored = {str(row[0]) for row in connection.execute(
            "SELECT id FROM practice_attempts WHERE rubric_score IS NOT NULL")}
    with repository.connection() as connection:
        assert not held_attempts(connection, sorted(scored))  # the vault's ledger holds none of them

    _run(paths, vault, tmp_path / "run", options=replace(OPTIONS, generate_planted=False, sweep=False))

    real = [(current, store) for current, store in seen if not str(current.attempt_id).startswith("planted")]
    assert real, "no real target was diagnosed"
    targets = {str(current.attempt_id) for current, _store in real}
    checked = 0
    for current, store in real:
        ref = store.ref(str(current.attempt_id))
        for attempt in store.attempts_before(ref):
            if attempt.attempt_id not in targets:
                continue  # no review grade: the vault's own grading, unchanged
            checked += 1
            assert attempt.score is None, attempt
            assert attempt.confidence_event == HELD_EVENT, attempt.confidence_event
    assert checked, "no held review grade was in a later target's history"


def test_the_live_history_keeps_the_ledgers_hold(tmp_path):
    """The live overlay is the vault's own grading (read with its identity):
    its hold stays THE ledger predicate's, so a contract-unrecorded hold the
    record does not carry still reads held."""

    from learnloop.diagnosis.split.live import live_history_store
    from learnloop.outcome_contract import GRADE_CONTRACT_UNRECORDED
    from tests.approach_map_fakes import ITEM
    from tests.test_teacher_te0_confidence_events import _attempt, _vault

    paths, vault, repository = _vault(tmp_path)
    _attempt(paths.sqlite_path, "att_live", at="2026-10-13T09:00:00Z", correctness=0.0, tap=5)
    record = {"practice_item_id": ITEM, "rubric_score": 0, "max_points": 4.0,
              "criteria": [{"criterion_id": "correctness", "points_awarded": 0}]}
    repository.insert_blind_grade_record(
        attempt_id="att_live", agent_run_id=None, grading_prompt_version="blind-test",
        output_schema_version="BlindGradingProposal", context_hash="ctx", record=record)
    shown = {attempt.attempt_id: attempt for attempt in live_history_store(vault, repository).all_attempts()}["att_live"]
    assert shown.confidence_event == "marked 5/5 sure; wrong"
    with closing(connect(paths.sqlite_path)) as connection:
        connection.execute("UPDATE practice_attempts SET manual_review_reason = ? WHERE id = 'att_live'",
                           (GRADE_CONTRACT_UNRECORDED,))
        connection.commit()
    shown = {attempt.attempt_id: attempt for attempt in live_history_store(vault, repository).all_attempts()}["att_live"]
    assert shown.score is None and shown.confidence_event == HELD_EVENT


# -- R2-2: the confidence metadata counts in the card budget ---------------------------------


def _topics(pad: int) -> dict:
    return {f"lo_{i}": {"title": f"Topic number {i} " + "x" * pad, "status": "demonstrated",
                        "evidence": {"graded": 3, "passed": 2, "failed": 1}, "due": "2026-10-14"} for i in range(8)}


def _events() -> dict:
    return {f"lo_{topic}": [{"attempt_id": f"w{topic}{i}", "at": f"2026-10-{10 - i:02d}T09:00:00Z",
                             "event": "marked 4/5 sure; the grader read parts of the answer as hedged; partly right"}
                            for i in range(4)] for topic in range(3)}


def _pair(pad: int):
    """TE0's inputs (12 events, the limit, a tap on each work line) and the
    predecessor's (the same card with the kill switch off and no confidence)."""

    te0 = replace(_card_inputs(work=["marked 5/5 sure; right"] * 4, confidence_7d=_events(),
                               confidence_limit="your taps so far are all 4–5 (30 taps)"),
                  learning_objects=_topics(pad))
    predecessor = replace(_card_inputs(), learning_objects=_topics(pad), confidence_enabled=False)
    return te0, predecessor


def test_the_card_never_exceeds_a_budget_the_predecessor_fits_eight_topics_at_1000():
    te0, predecessor = _pair(48)
    before = build_card(predecessor, token_budget=1000)
    assert before.tokens == 953  # the predecessor fits
    card = build_card(te0, token_budget=1000)
    # Before the fix: 1,021 tokens with all 12 events and all recent work dropped.
    assert card.tokens <= 1000, card.tokens
    assert card.truncation["dropped_confidence_events"] == 12
    assert card.truncation["dropped_confidence_limit"] == 1 and card.truncation["dropped_confidence_notice"] == 1
    body = card.json
    assert "confidence_limit" not in body and "confidence_omitted" not in body and "confidence_7d" not in body
    # The typed card spends no tokens on what it had no room for.
    assert not any(key.startswith("dropped_confidence") for key in body["truncation"])
    assert "Confidence" not in card.text and "older confidence event" not in card.text


def test_the_card_fits_whenever_the_predecessor_fits_across_budgets_and_topic_sizes():
    for pad in range(0, 120, 8):
        te0, predecessor = _pair(pad)
        for budget in range(700, 1_600, 25):
            if build_card(predecessor, token_budget=budget).tokens <= budget:
                card = build_card(te0, token_budget=budget)
                assert card.tokens <= budget, (pad, budget, card.tokens, dict(card.truncation))


def test_the_metadata_goes_only_after_every_event_and_the_limit_before_the_notice():
    te0, _predecessor = _pair(0)
    full = build_card(te0, token_budget=16_000)
    assert full.json["confidence_limit"] and "dropped_confidence_events" not in full.truncation
    without_events = replace(te0, confidence_7d={}, confidence_omitted=12)
    tight = build_card(without_events, token_budget=build_card(without_events).tokens - 1)
    # Just over: the limit goes, the omission notice stays (and is stated).
    assert "confidence_limit" not in tight.json and tight.json["confidence_omitted"] == 12
    assert "(12 older confidence events left out)" in tight.text
    assert tight.truncation["dropped_confidence_limit"] == 1 and "dropped_confidence_notice" not in tight.truncation
    # A budget the events alone overrun keeps the metadata while an event remains.
    some = build_card(te0, token_budget=full.tokens - 30)
    assert some.json.get("confidence_7d") and some.json["confidence_limit"]
    assert CE.CONTEXT_EVENT_LIMIT >= 12

"""Teacher TE0, Codex review fixes (docs/reviews/teacher-te0-codex-review.md).

* F1: the diagnosed attempt's confidence event reads THE held predicate: a
  held grade is "held for review", never "wrong";
* F2: an attempt's outcome, hedge read, held status and the taps are read in
  one read snapshot, so a regrade committed between the reads never yields
  an event from neither revision (hint writer, tutor, router card, diagnoser);
* F3: the card's confidence section is bounded and trimmed under the token
  budget (both renderings), and the omission is stated;
* F4: offline diagnosis gives each arm the same confidence block live
  diagnosis gives, from the arm's own blind record;
* F5: ``teacher.confidence_events_enabled`` (default on) is the shared kill
  switch: off, every reader's context is its predecessor's.

Fakes only; no model is called.
"""

from __future__ import annotations

import json
from contextlib import closing

import pytest

from learnloop import confidence_events as CE
from learnloop.db.connection import connect
from learnloop.router.card import CARD_VERSION, PREDECESSOR_CARD_VERSION, build_card

from tests.approach_map_fakes import ITEM, LO
from tests.test_teacher_te0_confidence_events import (
    _attempt,
    _card_inputs,
    _gathered_card,
    _tutor_context,
    _vault,
)

HELD_SUPPORT = {
    "proof_route_check": {"status": "checked", "held_for_review": True, "version": "proof-route-check-v3"},
    "valid_alternative_gate_applied": True,
    "assessed_shortfall": False,
}


def _switch_off(vault):
    from dataclasses import replace as dc_replace

    config = vault.config.model_copy(update={
        "teacher": vault.config.teacher.model_copy(update={"confidence_events_enabled": False})})
    try:
        return dc_replace(vault, config=config)
    except TypeError:
        object.__setattr__(vault, "config", config)
        return vault


# -- F1: the held predicate on the diagnosed attempt ---------------------------------------


def test_a_held_current_attempt_reads_held_for_review_never_wrong(tmp_path):
    from learnloop.diagnosis.split.live import current_attempt_for, current_confidence

    paths, vault, repository = _vault(tmp_path)
    _attempt(paths.sqlite_path, "att_held", at="2026-10-13T09:00:00Z", correctness=0.0, tap=5)
    record = {"practice_item_id": ITEM, "rubric_score": 0, "max_points": 4.0, "grading_support": dict(HELD_SUPPORT),
              "criteria": [{"criterion_id": "correctness", "points_awarded": 0}]}
    repository.insert_blind_grade_record(
        attempt_id="att_held", agent_run_id=None, grading_prompt_version="blind-test",
        output_schema_version="BlindGradingProposal", context_hash="ctx", record=record)
    with repository.connection() as connection:
        from learnloop.learner_protection import held_attempts

        assert held_attempts(connection, ["att_held"]) == frozenset({"att_held"})  # THE predicate holds it
    attempt = {"id": "att_held", "practice_item_id": ITEM, "created_at": "2026-10-13T09:00:00Z",
               "learner_answer_md": "x", "answer_confidence": 5}
    block = current_confidence(repository, attempt, record)
    assert block["event"] == "marked 5/5 sure; held for review (no score yet)"
    assert "wrong" not in json.dumps(block)
    # The ledger's predicate holds it even when the record handed in carries no support.
    bare = {key: value for key, value in record.items() if key != "grading_support"}
    assert current_confidence(repository, attempt, bare)["event"] == "marked 5/5 sure; held for review (no score yet)"
    assert current_attempt_for(vault, attempt, record, repository).render()["confidence"]["event"] == block["event"]


# -- F2: one read snapshot -----------------------------------------------------------------


def _regrade(sqlite_path, attempt_id: str) -> None:
    """hedged/wrong -> confident/right, committed on another connection."""

    with closing(connect(sqlite_path)) as connection:
        connection.execute("UPDATE practice_attempts SET correctness = 1.0, rubric_score = 4 WHERE id = ?",
                           (attempt_id,))
        connection.execute("UPDATE grading_evidence SET superseded_at = '2026-10-12T00:00:00Z' WHERE attempt_id = ?",
                           (attempt_id,))
        connection.execute(
            "INSERT INTO grading_evidence (id, attempt_id, criterion_id, points_awarded, grader_tier, created_at, "
            "learner_confidence) VALUES (?, ?, 'correctness', 4, 3, '2026-10-12T00:00:00Z', 'confident')",
            (f"ge2_{attempt_id}", attempt_id))
        connection.commit()


def _interleave(monkeypatch, sqlite_path, attempt_id: str) -> None:
    """Commit the regrade the first time the hedge reads run (after the outcome was read)."""

    real = CE.read_hedges
    fired = []

    def read_hedges(connection, attempt_ids=None):
        if not fired:
            fired.append(True)
            _regrade(sqlite_path, attempt_id)
        return real(connection, attempt_ids)

    monkeypatch.setattr(CE, "read_hedges", read_hedges)


@pytest.mark.durability
def test_a_regrade_between_the_reads_never_mixes_revisions_in_the_tutor_and_hint_block(tmp_path, monkeypatch):
    paths, vault, repository = _vault(tmp_path)
    _attempt(paths.sqlite_path, "att_rg", at="2026-10-10T09:00:00Z", correctness=0.0, hedge="hedged")
    _interleave(monkeypatch, paths.sqlite_path, "att_rg")
    block = CE.learner_events(vault, repository, learning_object_ids=[LO], before_iso="2027-01-01T00:00:00Z")
    event = block["topics"][0]["events"][0]
    # One committed revision or the other, never "confident; wrong".
    assert event in {"2026-10-10: no tap; the grader read the answer as hedged; wrong",
                     "2026-10-10: no tap; the grader read the answer as confident; right"}, event


@pytest.mark.durability
def test_a_regrade_between_the_reads_never_mixes_revisions_on_the_card(tmp_path, monkeypatch):
    from tests.test_router_card import _card, _card_world

    env = _card_world(tmp_path, monkeypatch)
    _attempt(env.repository.sqlite_path, "att_rg", at="2026-10-10T09:00:00Z", correctness=0.0, hedge="hedged",
             item_id="pi_a", lo_id="lo_m1")
    _interleave(monkeypatch, env.repository.sqlite_path, "att_rg")
    body = _card(env)["json"]
    work = {entry["attempt_id"]: entry for entry in body["recent_work"]}
    shown = (work["att_rg"]["result"], work["att_rg"]["confidence"])
    assert shown in {("incorrect", "no tap; the grader read the answer as hedged; wrong"),
                     ("correct", "no tap; the grader read the answer as confident; right")}, shown
    assert body["confidence_7d"]["lo_m1"][0]["event"] == work["att_rg"]["confidence"]


# -- F3: the card's budget ------------------------------------------------------------------


def _heavy_inputs(events: int = 300, **extra):
    window = {"lo": [{"attempt_id": f"w{i}", "at": f"2026-10-{1 + i % 9:02d}T09:{i % 60:02d}:00Z",
                      "event": "marked 4/5 sure; the grader read parts of the answer as hedged; partly right"}
                     for i in range(events)]}
    return _card_inputs(confidence_7d=window, confidence_limit="your taps so far are all 4–5 (300 taps)", **extra)


def test_a_heavy_confidence_week_stays_within_the_card_budget_and_keeps_recent_work():
    budget = 16_000
    card = build_card(_heavy_inputs(), token_budget=budget)
    assert card.tokens <= budget
    # Recent work survives whole: the section's events go first (each shown
    # attempt's line keeps its own event).
    assert len(card.json["recent_work"]) == 4
    assert all(entry["stem"] for entry in card.json["recent_work"])
    dropped = card.truncation["dropped_confidence_events"]
    assert dropped > 0 and len(card.json["confidence_7d"]["lo"]) == 300 - dropped
    assert card.json["confidence_omitted"] == dropped
    assert f"({dropped} older confidence events left out)" in card.text
    # The newest events are the ones kept (newest first in the section).
    assert card.json["confidence_7d"]["lo"][0]["attempt_id"] == "w0"


def test_the_gatherer_bounds_each_topics_events_and_states_the_omission(tmp_path, monkeypatch):
    rows = [dict(attempt_id=f"att_{i:02d}", at=f"2026-10-11T{i % 24:02d}:{i:02d}:00Z", correctness=1.0, tap=4,
                 item_id="pi_a", lo_id="lo_m1") for i in range(CE.CONTEXT_EVENT_LIMIT + 5)]
    body = _gathered_card(tmp_path, monkeypatch, rows)["json"]
    assert len(body["confidence_7d"]["lo_m1"]) == CE.CONTEXT_EVENT_LIMIT
    assert body["confidence_omitted"] == 5


def test_a_card_within_budget_states_no_omission():
    card = build_card(_heavy_inputs(events=3))
    assert "confidence_omitted" not in card.json and "dropped_confidence_events" not in card.truncation
    assert "left out" not in card.text


# -- F4: offline diagnosis ------------------------------------------------------------------


def test_offline_and_live_diagnosis_share_the_confidence_block(tmp_path):
    from learnloop.diagnosis.split.live import confidence_for_offline_target, current_confidence

    paths, vault, repository = _vault(tmp_path)
    _attempt(paths.sqlite_path, "att_prior", at="2026-10-10T09:00:00Z", correctness=1.0, tap=4)
    _attempt(paths.sqlite_path, "att_t", at="2026-10-13T09:00:00Z", correctness=0.0, tap=5, hedge="confident")
    record = {"rubric_score": 0, "max_points": 4.0,
              "criteria": [{"criterion_id": "correctness", "points_awarded": 0, "learner_confidence": "hedged"}]}
    attempt = {"id": "att_t", "practice_item_id": ITEM, "created_at": "2026-10-13T09:00:00Z"}
    live = current_confidence(repository, attempt, record, vault=vault)
    offline = confidence_for_offline_target(vault, repository, attempt_id="att_t", completed_at="2026-10-13T09:00:00Z",
                                            record=record, planted=False)
    assert offline == live
    assert offline["event"] == "marked 5/5 sure; the grader read the answer as hedged; wrong"
    assert offline["taps_so_far"] == "your taps so far are all 4–5 (2 taps)"
    # The arm's own record decides: with no hedge read in it, the vault's grading is not mixed in.
    plain = {"rubric_score": 0, "max_points": 4.0, "criteria": [{"criterion_id": "correctness", "points_awarded": 0}]}
    assert confidence_for_offline_target(vault, repository, attempt_id="att_t", completed_at="2026-10-13T09:00:00Z",
                                         record=plain, planted=False)["event"] == "marked 5/5 sure; wrong"
    # A held arm record reads held for review.
    held = {**plain, "grading_support": dict(HELD_SUPPORT)}
    assert confidence_for_offline_target(vault, repository, attempt_id="att_t", completed_at="2026-10-13T09:00:00Z",
                                         record=held, planted=False)["event"] == \
        "marked 5/5 sure; held for review (no score yet)"
    # A planted target: its record's hedge read only, no tap and no vault taps.
    planted = confidence_for_offline_target(vault, repository, attempt_id="planted_1",
                                            completed_at="2026-10-13T09:00:00Z", record=record, planted=True)
    assert planted == {"version": CE.VERSION, "note": CE.NOTE,
                       "event": "no tap; the grader read the answer as hedged; wrong"}
    assert confidence_for_offline_target(vault, repository, attempt_id="planted_1",
                                         completed_at="2026-10-13T09:00:00Z", record=plain, planted=True) is None


def test_the_offline_runner_renders_the_confidence_block_into_each_arms_prompt(tmp_path, monkeypatch):
    from learnloop.diagnosis.offline_review import runner as runner_module

    seen: list = []
    real = runner_module.run_diagnosis

    def spy(client, **kwargs):
        seen.append(kwargs["current"])
        return real(client, **kwargs)

    monkeypatch.setattr(runner_module, "run_diagnosis", spy)
    from tests.diagnosis_split_helpers import build_diagnosis_vault, seed_history
    from tests.test_diagnose_review import OPTIONS, _run
    from learnloop.diagnosis.offline_review.runner import ReviewOptions

    paths = build_diagnosis_vault(tmp_path / "vault")
    vault, _repository = seed_history(paths)
    with closing(connect(paths.sqlite_path)) as connection:
        connection.execute("UPDATE practice_attempts SET answer_confidence = 5")
        connection.commit()
    from dataclasses import replace

    _run(paths, vault, tmp_path / "run", options=replace(OPTIONS, generate_planted=False, sweep=False))
    real_targets = [current for current in seen if not str(current.attempt_id).startswith("planted")]
    assert real_targets, "no real target was diagnosed"
    for current in real_targets:
        assert current.confidence is not None and current.confidence["event"].startswith("marked 5/5 sure")
        assert current.render()["confidence"]["version"] == CE.VERSION
    assert ReviewOptions  # imported for the options' shape


# -- F5: the kill switch ----------------------------------------------------------------------


def test_the_switch_is_on_by_default_and_registered():
    from learnloop.config.schema import LearnLoopConfig
    from learnloop.params.parameter_registry import classify_config_path

    assert LearnLoopConfig().teacher.confidence_events_enabled is True
    assert classify_config_path("teacher.confidence_events_enabled") is not None


def test_switched_off_every_reader_gets_its_predecessor_context(tmp_path, monkeypatch):
    from learnloop.diagnosis.split.history import VaultHistoryStore
    from learnloop.diagnosis.split.live import current_attempt_for

    paths, vault, repository = _vault(tmp_path)
    _attempt(paths.sqlite_path, "att_1", at="2026-10-10T09:00:00Z", correctness=0.0, tap=5, hedge="hedged")
    off = _switch_off(vault)
    assert CE.enabled(vault) and not CE.enabled(off)
    # Hint writer and tutor block.
    assert CE.learner_events(off, repository, learning_object_ids=[LO], before_iso="2027-01-01T00:00:00Z") is None
    assert _tutor_context(off, repository, "practice").learner_confidence is None
    # History-aware diagnoser: history rows and the diagnosed attempt.
    by_id = {attempt.attempt_id: attempt for attempt in VaultHistoryStore(off, repository).all_attempts()}
    assert by_id["att_1"].confidence_event is None and by_id["att_1"].answer_confidence is None
    record = {"rubric_score": 0, "max_points": 4.0,
              "criteria": [{"criterion_id": "correctness", "points_awarded": 0, "learner_confidence": "hedged"}]}
    attempt = {"id": "att_1", "practice_item_id": ITEM, "created_at": "2026-10-10T09:00:00Z",
               "learner_answer_md": "x", "answer_confidence": 5}
    assert "confidence" not in current_attempt_for(off, attempt, record, repository).render()


def test_switched_off_the_card_is_the_predecessors_card(tmp_path, monkeypatch):
    import learnloop.confidence_events as module

    on = _gathered_card(tmp_path / "on", monkeypatch, [
        dict(attempt_id="att_1", at="2026-10-10T09:00:00Z", correctness=0.0, tap=5, item_id="pi_a", lo_id="lo_m1")])
    assert on["json"]["card_version"] == CARD_VERSION and "confidence_7d" in on["json"]
    monkeypatch.setattr(module, "enabled", lambda _vault: False)
    off = _gathered_card(tmp_path / "off", monkeypatch, [
        dict(attempt_id="att_1", at="2026-10-10T09:00:00Z", correctness=0.0, tap=5, item_id="pi_a", lo_id="lo_m1")])
    body = off["json"]
    assert body["card_version"] == PREDECESSOR_CARD_VERSION
    assert "confidence_7d" not in body and "confidence_limit" not in body
    assert all("confidence" not in entry for entry in body["recent_work"])
    assert "Confidence" not in off["text"]

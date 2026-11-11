"""RO0 rows 1, 2 and 3 at an ask (spec_router_objective_v1 §4): the state a question was asked in."""

from __future__ import annotations

import json

import pytest

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.db.stores.help_assists import insert_assist
from learnloop.field.probability_states import STATE_VERSION
from learnloop.router_objective import question_state as QS
from learnloop.tutor.tutor_qa import ask_question
from learnloop.vault.loader import load_vault
from tests.daily_plan_fakes import record_attempt
from tests.helpers import NOW, append_config_toml, create_basic_vault
from tests.question_context_helpers import FakeTutorClient

CLOCK = FrozenClock(NOW)
ITEM = "pi_svd_define_001"
OFF = "[router_objective]\nreceipts = false\n"


def _setup(tmp_path, *, off: bool = False):
    paths = create_basic_vault(tmp_path / "vault")
    if off:
        append_config_toml(paths.root, OFF)
    return load_vault(paths.root), Repository(paths.sqlite_path)


def _ask(vault, repository, *, context="practice", **kwargs):
    arguments = {"practice_item_id": ITEM, "session_id": "s1", "clock": CLOCK, **kwargs}
    result = ask_question(vault, repository, FakeTutorClient(), context=context, question_md="Why?", **arguments)
    return repository.question_event(result["event_id"])


def _assist(repository, *, assist_id, level, session="s1", kind="hint", hint_kind="next_step", attempt=None, index=None):
    with repository.atomic(), repository.connection() as connection:
        insert_assist(connection, {
            "id": assist_id, "surface": "practice", "assist_kind": kind, "practice_item_id": ITEM,
            "practice_session_id": session, "hint_kind": hint_kind, "level": level, "shown": 1, "attempt_id": attempt, "chooser": "none",
            "authored_index": index, "requested_at": f"2026-01-01T00:00:0{level}Z",
            "shown_at": f"2026-01-01T00:00:0{level}Z",
        })


def _reveal(repository, *, kind, amount):
    repository.insert_reveal_event({"practice_item_id": ITEM, "source_kind": kind, "amount": amount, "basis": "test"})


def _state(event) -> dict:
    return json.loads(event["reveal_state_json"])


def test_a_first_question_says_nothing_was_disclosed_and_visible_now_is_unknown(tmp_path):
    vault, repository = _setup(tmp_path)
    event = _ask(vault, repository, question_context={"attempt_progress": "no_draft"})
    state = _state(event)
    assert state["reveal_sum"] == 0 and state["answer_disclosed_ever"] is False
    assert state["worked_solution_disclosed_ever"] is False and state["hint_level_reached"] is None
    assert state["attempt_state"] == "no_draft"
    assert state["visible_now"] == QS.UNKNOWN
    assert event["hints_used_before"] == 0 and event["scaffold_level"] == "none" and event["preceding_tutor_move"] == "none"


def test_ever_disclosed_and_visible_now_are_separate_fields(tmp_path):
    vault, repository = _setup(tmp_path)
    _reveal(repository, kind="answer_display", amount=1.0)
    # The server knows it was disclosed; only the screen knows it is on screen now, and it says it is not.
    state = _state(_ask(vault, repository, question_context={"answer_visible_now": False}))
    assert state["answer_disclosed_ever"] is True and state["reveal_sum"] == 1.0
    assert state["visible_now"] == QS.NOT_VISIBLE
    assert _state(_ask(vault, repository, question_context={"answer_visible_now": True}))["visible_now"] == QS.VISIBLE
    # Silence is unknown, never inferred from ever disclosed.
    assert _state(_ask(vault, repository))["visible_now"] == QS.UNKNOWN


def test_the_server_computes_the_generating_process_from_help_assists(tmp_path):
    vault, repository = _setup(tmp_path)
    _assist(repository, assist_id="a1", level=1)
    _assist(repository, assist_id="a2", level=2)
    # An authored hint is one per index, however often it was re-shown.
    _assist(repository, assist_id="a3", level=3, hint_kind="authored", index=0)
    _assist(repository, assist_id="a4", level=3, hint_kind="authored", index=0)
    # Another session's hint and one an attempt already took are not this attempt's.
    _assist(repository, assist_id="a5", level=1, session="other")
    taken = record_attempt(repository, ITEM, vault.practice_items[ITEM].learning_object_id, NOW, session_id="s1")
    _assist(repository, assist_id="a6", level=1, attempt=taken)
    event = _ask(vault, repository)
    assert event["hints_used_before"] == 3
    assert event["scaffold_level"] == "3"
    assert event["preceding_tutor_move"].startswith("hint:")
    assert _state(event)["hint_level_reached"] == 3
    # The answer it gets is the next question's preceding move.
    assert _ask(vault, repository)["preceding_tutor_move"] == "tutor_answer"


def test_worked_help_counts_as_a_disclosed_solution(tmp_path):
    vault, repository = _setup(tmp_path)
    _assist(repository, assist_id="a1", level=4)
    assert _state(_ask(vault, repository))["worked_solution_disclosed_ever"] is True


def test_a_clients_value_stands_where_only_it_knows(tmp_path):
    vault, repository = _setup(tmp_path)
    _assist(repository, assist_id="a1", level=1)
    event = _ask(vault, repository, question_context={
        "learner_mode": "plan", "scaffold_level": "minimal", "preceding_tutor_move": "elicit", "hints_used_before": 7,
        "question_opportunity": "mid_attempt"})
    assert (event["learner_mode"], event["scaffold_level"], event["preceding_tutor_move"], event["hints_used_before"],
            event["question_opportunity"]) == ("plan", "minimal", "elicit", 7, "mid_attempt")


def test_a_practice_question_names_the_presentation_it_was_asked_from(tmp_path):
    vault, repository = _setup(tmp_path)
    assert _ask(vault, repository)["question_opportunity"] == "practice"
    with repository.atomic(), repository.connection() as connection:
        connection.execute("PRAGMA foreign_keys = OFF")
        connection.execute(
            "INSERT INTO attention_blocks(id, action, budget_minutes, content_hash, created_at) VALUES ('b1', 'a', 1, 'h', 't')")
        connection.execute(
            "INSERT INTO plan_presentations(id, block_id, practice_item_id, origin, session_id, served_at) "
            "VALUES ('p1', 'b1', ?, 'chooser', 's1', 't')", (ITEM,))
    event = _ask(vault, repository)
    assert event["question_opportunity"] == "plan_presentation"
    assert _state(event)["presentation_id"] == "p1"


def test_receipts_hold_no_learner_text(tmp_path):
    vault, repository = _setup(tmp_path)
    event = _ask(vault, repository)
    assert "Why?" not in event["reveal_state_json"]
    assert set(_state(event)) <= {"version", "reveal_sum", "reveal_kinds", "answer_disclosed_ever",
                                  "worked_solution_disclosed_ever", "hint_level_reached", "attempt_state", "visible_now",
                                  "presentation_id"}


def test_with_the_switch_off_nothing_is_written_whoever_sent_it(tmp_path):
    vault, repository = _setup(tmp_path, off=True)
    _assist(repository, assist_id="a1", level=1)
    event = _ask(vault, repository, question_context={"learner_mode": "plan", "hints_used_before": 2,
                                                      "attempt_progress": "no_draft"})
    assert event["reveal_state_json"] is None
    for field_name in QS.PROCESS_FIELDS:
        assert event[field_name] is None, field_name
    # What is not RO0's is kept.
    assert event["attempt_progress"] == "no_draft"


def test_a_state_that_cannot_be_read_never_fails_the_question(tmp_path, monkeypatch):
    vault, repository = _setup(tmp_path)

    def broken(*_args, **_kwargs):
        raise RuntimeError("no")

    monkeypatch.setattr(QS, "_assists", broken)
    event = _ask(vault, repository)
    assert event["answer_status"] == "answered" and event["reveal_state_json"] is None


def test_the_probability_card_version_records_hints_used_before():
    # The arms' card reads hints_used_before, which RO0 now populates: an input change (§4 "Readers").
    assert STATE_VERSION == "llm-probability-state-v4"


@pytest.mark.parametrize("context", ["feedback"])
def test_a_feedback_question_is_after_the_attempt(tmp_path, context):
    vault, repository = _setup(tmp_path)
    attempt_id = record_attempt(repository, ITEM, vault.practice_items[ITEM].learning_object_id, NOW, session_id="s1")
    event = _ask(vault, repository, context=context, attempt_id=attempt_id, question_context={"answer_visible_now": True})
    state = _state(event)
    assert state["attempt_state"] == "submitted" and state["visible_now"] == QS.VISIBLE

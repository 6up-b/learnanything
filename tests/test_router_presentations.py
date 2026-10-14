"""Router R2a: the exact decision -> presentation -> attempt receipt (plan §5.2).

A served plan item writes one append-only ``plan_presentations`` row in the
same transaction as its ``item_served`` event, and the plan step names it
(``presentation_id``). An attempt that sends the id is bound to it
(``practice_attempts.plan_presentation_id``); a wrong, foreign or consumed id
never fails the submit, it only leaves the attempt unbound. ``router_outcomes``
v2 joins a ``plan_block`` decision through its block's first bound
presentation, so the action is what the learner was actually served and
answered, not the block's first planned item; R1's session rule stays only as
the labelled fallback for rows and clients without a receipt.

Fail-first (plan §9 R2a, item 2): under R1's session rule an attempt on the
second planned item after a skip is mis-bound. The block's decision names its
first planned item, so when that item is answered later in the session (here
picked from the full list) the decision's "action" becomes that later pick.
"""

from __future__ import annotations

import sqlite3
from datetime import UTC, datetime, timedelta

import pytest

from learnloop.daily_plan.engine import advance, build_plan, learner_pick
from learnloop.db.connection import connect
from learnloop.router.outcomes import derive_router_outcomes

from tests.daily_plan_fakes import MovableClock, iso, make_env, scheduled, seed_due
from tests.helpers import create_daily_plan_vault

PAST = datetime(2026, 10, 1, 9, 0, tzinfo=UTC)
LAST = datetime(2026, 9, 20, 9, 0, tzinfo=UTC)


def _vault(tmp_path, *, version: str = "mvp-0.22"):
    los = {"lo_m1": [("pi_m1a", 2.0), ("pi_m1b", 2.0), ("pi_m1c", 2.0)]}
    return create_daily_plan_vault(tmp_path / "vault", learning_objects=los, version=version)


def _items():
    return [
        scheduled("pi_m1a", "lo_m1", forgetting_risk=0.6),
        scheduled("pi_m1b", "lo_m1", forgetting_risk=0.6),
        scheduled("pi_m1c", "lo_m1", forgetting_risk=0.6),
    ]


def _env(tmp_path, **kwargs):
    paths = _vault(tmp_path, **kwargs)
    clock = MovableClock()
    env = make_env(paths.root, _items(), clock=clock, session_id="s1")
    for item in ("pi_m1a", "pi_m1b", "pi_m1c"):
        seed_due(env.repository, item, due=PAST, last=LAST)
    with env.repository.connection() as connection:
        connection.execute(
            "INSERT INTO sessions(id, started_at, available_minutes) VALUES ('s1', ?, 30)", (iso(clock.now()),)
        )
        connection.commit()
    return env, clock


def _has_column(connection, table: str, column: str) -> bool:
    return any(row[1] == column for row in connection.execute(f"PRAGMA table_info({table})"))


def _answer(env, item_id: str, at: datetime, *, presentation_id: str | None, correctness: float = 1.0) -> str:
    """An answered attempt; bound to its presentation when the schema has the column."""

    attempt_id = f"att_{item_id}_{int(at.timestamp())}"
    with env.repository.connection() as connection:
        columns = ["id", "practice_item_id", "learning_object_id", "practice_mode", "attempt_type",
                   "latency_seconds", "created_at", "session_id", "correctness", "evidence_origin"]
        values = [attempt_id, item_id, "lo_m1", "short_answer", "independent_attempt", 60, iso(at), "s1",
                  correctness, "human"]
        if presentation_id is not None and _has_column(connection, "practice_attempts", "plan_presentation_id"):
            columns.append("plan_presentation_id")
            values.append(presentation_id)
        connection.execute(
            f"INSERT INTO practice_attempts({', '.join(columns)}) VALUES ({', '.join('?' for _ in columns)})",
            values,
        )
        connection.commit()
    return attempt_id


def _outcome_for_block(env, block_id: str) -> dict:
    with connect(env.repository.sqlite_path, read_only=True) as connection:
        decision = connection.execute(
            "SELECT id FROM router_decisions WHERE receipt_key = ?", (f"plan_block:{block_id}",)
        ).fetchone()
        assert decision is not None, "R1 logs every plan block decision"
        outcomes = {row["decision_id"]: row for row in derive_router_outcomes(connection)}
    return outcomes[decision["id"]]


def test_an_attempt_after_a_skip_binds_by_presentation_not_the_session_rule(tmp_path):
    env, clock = _env(tmp_path)
    build_plan(env, kind="normal", budget=10.0, remembered=10, minutes_source="chip")
    record, first = advance(env, serve=True)
    assert first["kind"] == "item" and first["practice_item_id"] == "pi_m1a"
    block_id = first["block_id"]
    # The learner skips the first planned item and is served the second.
    clock.advance(1)
    record, second = advance(env, serve=True, skip_practice_item_id="pi_m1a")
    assert second["practice_item_id"] == "pi_m1b" and second["block_id"] == block_id
    clock.advance(2)
    answered = _answer(env, "pi_m1b", clock.now(), presentation_id=second.get("presentation_id"))
    # Later in the same session the skipped item is picked from the full list
    # and answered: R1's session rule takes this as the block decision's action.
    clock.advance(3)
    _record, pick = learner_pick(env, "pi_m1a")
    clock.advance(2)
    _answer(env, "pi_m1a", clock.now(), presentation_id=pick.get("presentation_id"), correctness=0.0)

    outcome = _outcome_for_block(env, block_id)
    assert outcome["action_status"] == "taken"
    assert outcome["action_attempt_id"] == answered, "the block's action is the answer to what it served"
    assert outcome["target_practice_item_id"] == "pi_m1b"
    assert outcome["action_binding"] == "presentation"


def test_a_served_item_writes_one_presentation_with_its_block_and_decision(tmp_path):
    env, clock = _env(tmp_path)
    build_plan(env, kind="normal", budget=10.0, remembered=10, minutes_source="chip")
    _record, step = advance(env, serve=True)
    presentation_id = step["presentation_id"]
    assert presentation_id
    # Serving the same step again (a reopen) names the same presentation.
    _record, again = advance(env, serve=True)
    assert again["presentation_id"] == presentation_id
    with env.repository.connection() as connection:
        rows = [dict(row) for row in connection.execute("SELECT * FROM plan_presentations")]
        block = connection.execute("SELECT decision_ref FROM attention_blocks WHERE id = ?", (step["block_id"],)).fetchone()
    assert len(rows) == 1
    row = rows[0]
    assert (row["id"], row["block_id"], row["practice_item_id"], row["session_id"]) == (
        presentation_id, step["block_id"], "pi_m1a", "s1",
    )
    assert row["router_decision_id"] == block["decision_ref"] and row["router_decision_id"]
    assert row["position"] == 1 and row["origin"] == "chooser"
    # The prefetch (no serve) names no presentation: nothing was shown yet.
    clock.advance(2)
    _answer(env, "pi_m1a", clock.now(), presentation_id=presentation_id)
    _record, prefetch = advance(env, serve=False)
    assert prefetch["kind"] == "item" and prefetch.get("presentation_id") is None


def test_presentations_are_append_only(tmp_path):
    env, _clock = _env(tmp_path)
    build_plan(env, kind="normal", budget=10.0, remembered=10, minutes_source="chip")
    _record, step = advance(env, serve=True)
    with env.repository.connection() as connection:
        with pytest.raises(sqlite3.DatabaseError, match="append-only"):
            connection.execute("UPDATE plan_presentations SET session_id = 'other' WHERE id = ?", (step["presentation_id"],))
        with pytest.raises(sqlite3.DatabaseError, match="append-only"):
            connection.execute("DELETE FROM plan_presentations WHERE id = ?", (step["presentation_id"],))


def test_a_learner_pick_and_an_open_list_pick_get_their_own_presentations(tmp_path):
    env, clock = _env(tmp_path)
    build_plan(env, kind="normal", budget=4.0, remembered=4, minutes_source="chip")
    _record, pick = learner_pick(env, "pi_m1c")
    assert pick["presentation_id"]
    with env.repository.connection() as connection:
        row = connection.execute("SELECT * FROM plan_presentations WHERE id = ?", (pick["presentation_id"],)).fetchone()
    assert row["origin"] == "learner_pick" and row["practice_item_id"] == "pi_m1c"
    # A pick is the learner's own choice, logged as such (no propensity) and
    # named by its presentation (G9; Codex review F4).
    with env.repository.connection() as connection:
        decision = connection.execute("SELECT * FROM router_decisions WHERE id = ?",
                                      (row["router_decision_id"],)).fetchone()
    assert decision is not None
    assert (decision["learner_pick"], decision["propensity"], decision["chosen_practice_item_id"]) == (1, None, "pi_m1c")


def test_the_session_rule_stays_the_labelled_fallback_for_an_unbound_attempt(tmp_path):
    """A client that sends no presentation id (an older client, the TUI) is
    still joined, by R1's session rule, and labelled so R3 can exclude it."""

    env, clock = _env(tmp_path)
    build_plan(env, kind="normal", budget=10.0, remembered=10, minutes_source="chip")
    _record, step = advance(env, serve=True)
    clock.advance(2)
    attempt_id = _answer(env, "pi_m1a", clock.now(), presentation_id=None)
    outcome = _outcome_for_block(env, step["block_id"])
    assert (outcome["action_status"], outcome["action_attempt_id"], outcome["action_binding"]) == (
        "taken", attempt_id, "session_rule",
    )


def test_the_session_rule_never_takes_an_attempt_bound_to_another_presentation(tmp_path):
    """Codex review F3, the negative counterpart of the skip test: block A's
    served items are never answered; its skipped first item is answered later
    through block B's own presentation (a pick). That attempt has an exact
    receipt elsewhere, so A's session-rule fallback must not take it: A is
    not ``taken``, and B's outcome keeps it."""

    env, clock = _env(tmp_path)
    build_plan(env, kind="normal", budget=10.0, remembered=10, minutes_source="chip")
    record, first = advance(env, serve=True)
    assert first["practice_item_id"] == "pi_m1a"
    block_a = first["block_id"]
    clock.advance(1)
    record, second = advance(env, serve=True, skip_practice_item_id="pi_m1a")
    assert second["practice_item_id"] == "pi_m1b" and second["block_id"] == block_a
    # Nothing A served is answered. The skipped item is picked and answered
    # through the pick's own presentation.
    clock.advance(3)
    _record, pick = learner_pick(env, "pi_m1a")
    assert pick["presentation_id"] and pick["block_id"] != block_a
    clock.advance(2)
    picked = _answer(env, "pi_m1a", clock.now(), presentation_id=pick["presentation_id"])

    outcome_a = _outcome_for_block(env, block_a)
    assert outcome_a["action_attempt_id"] is None, "A never served what this attempt answered"
    assert outcome_a["action_status"] != "taken"
    # The pick block's own decision (G9) takes it, exactly.
    outcome_b = _outcome_for_block(env, pick["block_id"])
    assert (outcome_b["action_attempt_id"], outcome_b["action_binding"]) == (picked, "presentation")

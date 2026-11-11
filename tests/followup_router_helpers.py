"""What other test files use from ``tests/test_followup_router.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from learnloop.daily_plan.engine import advance, build_plan
from learnloop.daily_plan.router_chooser import FollowupGate
from learnloop.db.stores import followup_serve as store
from learnloop.followup_run import router
from learnloop.followup_serve import identity, workflow as wf

from tests.daily_plan_fakes import record_attempt
from tests.followup_serve_helpers import TAG
from tests.router_mixture_helpers import mixture_env
from tests.daily_plan_build_helpers import _wide_items


ITEM = "pi_diag_mid"


def _env(tmp_path, runtime, *, toml=None):
    env = mixture_env(tmp_path, runtime, version=TAG, toml=toml, items=lambda: list(_wide_items()))
    build_plan(env, kind="normal", budget=25.0, remembered=25, minutes_source="chip")
    record, step = advance(env, serve=True)
    assert step["kind"] == "item"
    env.clock.advance(1)
    record_attempt(env.repository, step["practice_item_id"], step["learning_object_id"], env.clock.now(),
                   session_id=env.session_id)
    env.clock.advance(1)
    return env, record


def _workflow(env, *, state=wf.PENDING, item=None, decision=None, held=1):
    record_attempt(env.repository, "pi_m1a", "lo_m1", env.clock.now(), session_id=env.session_id)
    with env.repository.connection() as connection:
        attempt_id = connection.execute("SELECT id FROM practice_attempts ORDER BY created_at DESC, id DESC").fetchone()[0]
    with env.repository.atomic(), env.repository.connection() as connection:
        store.insert_workflow(connection, {
            "id": "fw_test", "source_attempt_id": attempt_id, "revision_key": "joint",
            "learning_object_id": "lo_r1", "session_id": env.session_id, "surface": "desktop", "origin": "practice",
            "feedback_held": held, "created_at": env.now_iso(),
        })
    if item or state != wf.PENDING:
        wf.move(env.repository, "fw_test", to_state=state, reason="test", practice_item_id=item, decision_id=decision,
                factor_id="f", clock=env.clock)
    return wf.get(env.repository, "fw_test")


def _gate(env):
    restraint = env.policy.restraint
    return FollowupGate(env.vault, env.repository, restraint.runtime, frame=restraint.frame,
                        card_builder=restraint.card_builder, session_id=env.session_id, clock=env.clock,
                        may_defer=False)


def _row():
    return {"id": "fw_test", "learning_object_id": "lo_r1", "source_attempt_id": "att_x", "session_id": "s1",
            "factor_id": "f"}


def _decide(env, record, chosen):
    outcome = _gate(env).decide_followup(record, record.current_block(), _row(), wait_feasible=True)
    return router.FollowupDecision(
        chosen, chosen, "mixture", propensity=outcome.record["mixture"]["pi"][chosen], record=dict(outcome.record),
        block_id=record.current_block().id, plan_id=record.id, plan_kind=record.kind, local_date="2026-11-03",
    )


def _ready(env, *, state=wf.READY, decision=None):
    row = _workflow(env, state=state, item=ITEM, decision=decision)
    identity.register(env.repository, practice_item_id=ITEM, revision="r", source="workflow", workflow_id="fw_test",
                      clock=env.clock)
    return row

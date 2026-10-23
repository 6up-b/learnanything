"""DL2 x RW4b (landing): a keyed learner pick of an item that has a "Check once".

RW4b's keyed ``learner_pick`` (``idempotency_key``, ``within``, the strict
presentation write and the ``pick_keyed`` receipt) and DL2's "Check once"
(planned in the maintain lane as DL1's ``check_once``, settled by an attempt
the one eligibility decision would have served cold) were built on different
bases. On the merged tree both must hold together:

* a keyed pick of a planned due check serves the check's own planned item (no
  second block), writes one keyed receipt, runs ``within`` once, and the
  served view is still the check on your own; a retry returns the same pick;
  an answer on your own then satisfies the check;
* a keyed pick of an item whose due check the plan does not hold (the check
  became due after the plan was built) is the learner's one-item block, and
  its answer satisfies the check too;
* a keyed pick of an item a waiting check holds is still the learner's own
  pick (L3), and its attempt before the date answers nothing.
"""

from __future__ import annotations

from contextlib import closing
from datetime import timedelta

from learnloop.clock import FrozenClock
from learnloop.curriculum import commitments as C
from learnloop.daily_plan import engine as E
from learnloop.daily_plan.engine import PlanEnv, build_plan, learner_pick
from learnloop.db.connection import connect
from learnloop.intent.checks import served_check, settle_answered_checks
from tests.daily_plan_fakes import MovableClock
from tests.intent_fakes import NOW, make_intent_vault

KEY = "workbench_admission:wbs_dl2"


def _keyed(repository, key: str) -> int:
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        return connection.execute(
            "SELECT COUNT(*) FROM attention_block_events WHERE kind = ? "
            "AND json_extract(detail_json, '$.idempotency_key') = ?", (E.PICK_KEYED, key)).fetchone()[0]


def _learner_pick_blocks(repository) -> int:
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        return connection.execute(
            "SELECT COUNT(*) FROM router_decisions WHERE json_extract(detail_json, '$.chosen_by') = 'learner_pick'"
        ).fetchone()[0]


def _check_id(iv, item_id: str) -> str:
    serving = iv.serving(NOW + timedelta(days=8))
    return next(state.commitment_id for state in serving.due_checks() if item_id in state.candidates)


def test_a_keyed_pick_of_a_planned_due_check_serves_the_check_once_and_its_answer_satisfies_it(tmp_path):
    iv = make_intent_vault(tmp_path / "vault")
    iv.choose("practice_item", "pi_b1", "check_once", NOW)
    commitment = _check_id(iv, "pi_b1")
    at = NOW + timedelta(days=8)
    clock = MovableClock(at)
    env = PlanEnv(vault=iv.vault, repository=iv.repository, clock=clock)
    plan = build_plan(env, kind="normal", budget=25.0, remembered=25, minutes_source="chip")
    planned = next(item for item in plan.items() if item.practice_item_id == "pi_b1")
    assert planned.check_kind == "check_once"
    blocks_before = _learner_pick_blocks(iv.repository)

    calls: list[str] = []
    _record, step = learner_pick(env, "pi_b1", idempotency_key=KEY,
                                 within=lambda record, step: calls.append(step["practice_item_id"]))
    # The planned check's own block, not a new one-item learner-pick block.
    assert step["block_id"] == planned.block_id and step["presentation_id"]
    assert _learner_pick_blocks(iv.repository) == blocks_before
    assert (calls, _keyed(iv.repository, KEY)) == (["pi_b1"], 1)
    # The served view is still the check on your own.
    view = served_check(iv.vault, iv.repository, "pi_b1", now=clock.now())
    assert view is not None and view["cold"] is True

    # A retry under the key returns the same pick and writes nothing.
    _record, again = learner_pick(env, "pi_b1", idempotency_key=KEY,
                                  within=lambda record, step: calls.append("again"))
    assert again["presentation_id"] == step["presentation_id"]
    assert (calls, _keyed(iv.repository, KEY)) == (["pi_b1"], 1)

    # Answered on your own: the check is satisfied, once.
    iv.answer("pi_b1", at + timedelta(minutes=2))
    settle = FrozenClock(at + timedelta(minutes=3))
    assert settle_answered_checks(iv.vault, iv.repository, clock=settle) == [commitment]
    assert C.resolve_disposition(iv.repository, commitment) == "satisfied"


def test_a_keyed_pick_of_a_due_check_the_plan_does_not_hold_is_a_one_item_block_and_answers_it(tmp_path):
    iv = make_intent_vault(tmp_path / "vault")
    at = NOW + timedelta(days=8)
    clock = MovableClock(at)
    env = PlanEnv(vault=iv.vault, repository=iv.repository, clock=clock)
    plan = build_plan(env, kind="normal", budget=4.0, remembered=4, minutes_source="chip")
    assert "pi_c2" not in [item.practice_item_id for item in plan.items()]
    # A Reader-made check, dated today, created after the plan was built.
    commitment = C.create_commitment(
        iv.repository, action="test_me_later", intent_text="rebuild without the book",
        targets=[{"target_kind": "legacy_practice_item", "target_ref": "pi_c2", "role": "required"}],
        depth_preset="keep_in_touch", client_idempotency_key="reader_reconstruct:pi_c2",
        due_hint=(at - timedelta(hours=1)).date().isoformat(), clock=FrozenClock(at - timedelta(minutes=5)),
    ).id
    assert served_check(iv.vault, iv.repository, "pi_c2", now=at) is not None
    blocks_before = _learner_pick_blocks(iv.repository)

    _record, step = learner_pick(env, "pi_c2", idempotency_key=KEY, within=lambda record, step: None)
    assert step["practice_item_id"] == "pi_c2" and step["presentation_id"]
    assert _learner_pick_blocks(iv.repository) == blocks_before + 1
    assert _keyed(iv.repository, KEY) == 1

    iv.answer("pi_c2", at + timedelta(minutes=2))
    assert settle_answered_checks(iv.vault, iv.repository, clock=FrozenClock(at + timedelta(minutes=3))) == [
        commitment]
    assert C.resolve_disposition(iv.repository, commitment) == "satisfied"


def test_a_keyed_pick_of_an_item_a_waiting_check_holds_is_served_and_answers_nothing(tmp_path):
    iv = make_intent_vault(tmp_path / "vault")
    iv.choose("practice_item", "pi_b1", "check_once", NOW)
    at = NOW + timedelta(days=1)
    env = PlanEnv(vault=iv.vault, repository=iv.repository, clock=MovableClock(at))
    plan = build_plan(env, kind="normal", budget=25.0, remembered=25, minutes_source="chip")
    assert "pi_b1" not in set(plan.split["universe"])  # the waiting check holds it back from serving
    _record, step = learner_pick(env, "pi_b1", idempotency_key=KEY, within=lambda record, step: None)
    assert step["practice_item_id"] == "pi_b1" and step["presentation_id"]
    assert served_check(iv.vault, iv.repository, "pi_b1", now=at) is None  # not due: an ordinary item
    iv.answer("pi_b1", at + timedelta(minutes=2))
    assert settle_answered_checks(iv.vault, iv.repository, clock=FrozenClock(at + timedelta(minutes=3))) == []
    commitment = next(state.commitment_id for state in iv.serving(at + timedelta(days=8)).checks.values()
                      if "pi_b1" in state.candidates)
    assert C.resolve_disposition(iv.repository, commitment) == "one_check_pending"

"""Router R2c, G4: the restraint on mid-block follow-ups (``plan_interrupt``).

Fail-first (plan §9 R2c): today a follow-up always joins the current block;
with a fake Decider whose P(intervene now) is near 0, it waits for the
boundary, with an exact propensity on its ``plan_interrupt`` row, and opens
the next block.
"""

from __future__ import annotations

import pytest

from learnloop.algorithm_versions import ROUTER_STAGED_FRAME_ALGORITHM_VERSION
from learnloop.daily_plan.engine import advance, build_plan

from tests.daily_plan_fakes import iso, record_attempt, scheduled
from tests.router_mixture_helpers import mixture_env, rows
from tests.router_model_fakes import FakeDecider, fake_runtime, first_option, seed_with_first_uniform
from tests.test_daily_plan_build import _wide_items

DECIDER_ONLY = "[router.weights]\nstaged = 0.0\ndecider = 1.0\nllm = 0.0\n"
#: A first stage outside every floor (k * eps <= 7 * 0.02): the draw follows
#: the Decider, whose block choice is the rule's pick (``first_option``).
PAST_THE_FLOOR = 0.2


def _followup_env(tmp_path, runtime, *, version=None, toml=None):
    live = list(_wide_items())
    kwargs = {"version": version} if version else {}
    env = mixture_env(tmp_path, runtime, toml=toml, items=lambda: live, **kwargs)
    build_plan(env, kind="normal", budget=25.0, remembered=25, minutes_source="chip")
    record, step = advance(env, serve=True)
    assert step["kind"] == "item"
    assert len(record.current_block().items) >= 2
    # The learner answers it, and the answer produced a follow-up that was
    # not in the plan at build.
    env.clock.advance(1)
    record_attempt(env.repository, step["practice_item_id"], step["learning_object_id"], env.clock.now(),
                   session_id=env.session_id)
    live.insert(0, scheduled("pi_diag_mid", "lo_diag", followup_kind="negative_surprise_followup"))
    env.clock.advance(1)
    return env


def test_a_follow_up_joins_the_current_block_today_and_waits_with_a_decider_near_zero(tmp_path):
    # Today (R2a, mvp-0.23): the follow-up joins the current block.
    today = _followup_env(tmp_path / "today", fake_runtime(), version=ROUTER_STAGED_FRAME_ALGORITHM_VERSION)
    record, step = advance(today, serve=False)
    current = record.current_block()
    assert "pi_diag_mid" in [item.practice_item_id for item in current.items]
    assert step["practice_item_id"] == "pi_diag_mid"

    # R2c: the Decider says "don't interrupt" (P(yes) = 0); the draw lands
    # outside the floor, so the follow-up waits for the next block.
    runtime = fake_runtime(decider=FakeDecider(choice=first_option, p_yes=0.0),
                           seed=seed_with_first_uniform(at_least=PAST_THE_FLOOR))
    env = _followup_env(tmp_path / "r2c", runtime, toml=DECIDER_ONLY)
    record, step = advance(env, serve=True)
    current = record.current_block()
    assert "pi_diag_mid" not in [item.practice_item_id for item in current.items]
    assert current.deferred_followups() == {"pi_diag_mid"}
    (row,) = rows(env, "plan_interrupt")
    assert row["chosen_ref"] == "continue_current"
    assert row["propensity_kind"] == "exact"
    # pi(insert) = (1 - 2 eps) * (w_d * 0) + eps; pi(continue) = 1 - pi(insert).
    assert row["propensity"] == pytest.approx(1 - 0.02)
    assert row["design"] == "model_mixture" and row["seed"]
    assert row["chosen_practice_item_id"] is None
    by_ref = {entry["ref"]: entry for entry in row["candidates_json"]}
    assert by_ref["insert_now"]["propensity"] == pytest.approx(0.02)
    assert by_ref["insert_now"]["feasible"] and by_ref["continue_current"]["feasible"]

    # It opens the next block, at the boundary.
    for _ in range(20):
        env.clock.advance(2)
        if step is None or step["kind"] != "item":
            break
        record_attempt(env.repository, step["practice_item_id"], step["learning_object_id"], env.clock.now(),
                       session_id=env.session_id)
        record, step = advance(env, serve=True)
        if step and step.get("practice_item_id") == "pi_diag_mid":
            break
    assert step["practice_item_id"] == "pi_diag_mid"
    block = next(block for block in record.blocks if block.id == step["block_id"])
    assert block.ordinal > current.ordinal
    assert next(item for item in block.items if item.practice_item_id == "pi_diag_mid").origin == "followup"


def test_with_the_restraint_off_a_follow_up_joins_as_in_r2b(tmp_path):
    from tests.router_model_fakes import FakeLLM

    runtime = fake_runtime(decider=FakeDecider(choice=first_option, p_yes=0.0), llm=FakeLLM(),
                           seed=seed_with_first_uniform(at_least=PAST_THE_FLOOR))
    env = _followup_env(tmp_path, runtime, toml="[router]\nrestraint = false\n[router.weights]\nstaged = 1.0\n"
                        "decider = 0.0\nllm = 0.0\n")
    assert env.policy.restraint is None
    record, step = advance(env, serve=True)
    assert "pi_diag_mid" in [item.practice_item_id for item in record.current_block().items]
    assert step["practice_item_id"] == "pi_diag_mid"
    assert rows(env, "plan_interrupt") == []
    # The block decisions are still the mixture's (R2b).
    assert {row["policy"] for row in rows(env)} >= {"router_mixture_v1"}


def test_when_the_models_agree_to_interrupt_the_follow_up_joins_with_its_decision(tmp_path):
    runtime = fake_runtime(decider=FakeDecider(choice=first_option, p_yes=1.0),
                           seed=seed_with_first_uniform(at_least=PAST_THE_FLOOR))
    env = _followup_env(tmp_path, runtime, toml=DECIDER_ONLY)
    record, step = advance(env, serve=True)
    (row,) = rows(env, "plan_interrupt")
    assert row["chosen_ref"] == "insert_now" and row["propensity"] == pytest.approx(1 - 0.02)
    assert row["chosen_practice_item_id"] == "pi_diag_mid"
    joined = next(item for item in record.current_block().items if item.practice_item_id == "pi_diag_mid")
    assert joined.origin == "followup"
    with env.repository.connection() as connection:
        detail = connection.execute(
            "SELECT detail_json FROM attention_block_events WHERE kind = 'item_planned' AND detail_json LIKE ?",
            ("%pi_diag_mid%",),
        ).fetchone()["detail_json"]
    assert row["id"] in detail


def test_the_models_never_force_a_follow_up_the_rules_would_not_place(tmp_path, monkeypatch):
    from learnloop.daily_plan import engine

    runtime = fake_runtime(decider=FakeDecider(choice=first_option, p_yes=1.0),
                           seed=seed_with_first_uniform(at_least=PAST_THE_FLOOR))
    env = _followup_env(tmp_path, runtime, toml=DECIDER_ONLY)
    called = []
    monkeypatch.setattr(type(env.policy.restraint), "decide", lambda *args, **kwargs: called.append(args))
    monkeypatch.setattr(engine, "_displacement_plan", lambda *args, **kwargs: None)
    record, _step = advance(env, serve=True)
    assert called == [] and rows(env, "plan_interrupt") == []
    assert "pi_diag_mid" not in [item.practice_item_id for item in record.current_block().items]


def test_a_follow_up_a_hard_constraint_refuses_is_declined_by_name(tmp_path):
    from learnloop.substrate.activities import reserve_surface
    from learnloop.substrate.activities import resolve_legacy_item
    from learnloop.vault.loader import load_vault

    runtime = fake_runtime(decider=FakeDecider(choice=first_option, p_yes=1.0),
                           seed=seed_with_first_uniform(at_least=PAST_THE_FLOOR))
    env = _followup_env(tmp_path, runtime, toml=DECIDER_ONLY)
    vault = load_vault(env.vault.root)
    resolved = resolve_legacy_item(vault, env.repository, vault.practice_items["pi_diag_mid"], purpose="assessment")
    reserve_surface(env.repository, surface_id=resolved.surface_id, purpose="assessment")
    record, _step = advance(env, serve=True)
    (row,) = rows(env, "plan_interrupt")
    assert row["chosen_ref"] == "decline" and row["propensity_kind"] == "deterministic"
    assert row["exclusions_json"]["named"]["assessment_reservation"] == ["pi_diag_mid"]
    assert "pi_diag_mid" in record.refused_followups()
    assert "pi_diag_mid" not in {item.practice_item_id for item in record.items()}
    # Nothing was asked of a model for a refused follow-up.
    assert row["model_distributions_json"] is None


def _finish_first_block_then_follow_up(tmp_path, *, reserve: bool):
    """Answer every item of the first block; the last answer produces a follow-up
    (so no block is current when it appears); optionally reserve its surface."""

    from learnloop.substrate.activities import reserve_surface, resolve_legacy_item
    from learnloop.vault.loader import load_vault

    live = list(_wide_items())
    env = mixture_env(tmp_path, fake_runtime(), items=lambda: live)
    build_plan(env, kind="normal", budget=25.0, remembered=25, minutes_source="chip")
    first = None
    for _ in range(20):
        record, step = advance(env, serve=True)
        block = record.current_block()
        first = first or block.id
        assert block.id == first and step["kind"] == "item"
        env.clock.advance(1)
        record_attempt(env.repository, step["practice_item_id"], step["learning_object_id"], env.clock.now(),
                       session_id=env.session_id)
        if not [item for item in block.items if not item.resolved and not item.displaced
                and item.practice_item_id != step["practice_item_id"]]:
            break
    live.insert(0, scheduled("pi_diag_mid", "lo_diag", followup_kind="negative_surprise_followup"))
    if reserve:
        vault = load_vault(env.vault.root)
        resolved = resolve_legacy_item(vault, env.repository, vault.practice_items["pi_diag_mid"], purpose="assessment")
        reserve_surface(env.repository, surface_id=resolved.surface_id, purpose="assessment")
    env.clock.advance(1)
    record, step = advance(env, serve=True)
    assert record.current_block().id != first
    return env, record, step


def test_a_follow_up_after_a_blocks_last_answer_is_forced_into_the_next_block(tmp_path):
    env, record, step = _finish_first_block_then_follow_up(tmp_path, reserve=False)
    assert step["practice_item_id"] == "pi_diag_mid"
    assert next(item for item in record.current_block().items if item.practice_item_id == "pi_diag_mid").origin == "followup"


def test_a_refused_follow_up_is_never_forced_into_the_next_block(tmp_path):
    # R2a open question 2, the end-of-block path: with the restraint on, the
    # constraint engine runs on a follow-up before it is forced into the next
    # block; a refused one is declined by name, once, on the block whose answer
    # produced it, and never placed or rechecked in this plan.
    env, record, step = _finish_first_block_then_follow_up(tmp_path, reserve=True)
    assert step["practice_item_id"] != "pi_diag_mid"
    assert "pi_diag_mid" not in {item.practice_item_id for item in record.items()}
    assert "pi_diag_mid" in record.refused_followups()
    (row,) = rows(env, "plan_interrupt")
    first_block = record.blocks[0]
    assert (row["chosen_ref"], row["propensity_kind"], row["policy"]) == ("decline", "deterministic", "staged_v1")
    assert row["receipt_key"] == f"plan_interrupt:{first_block.id}:pi_diag_mid"
    assert row["exclusions_json"]["named"]["assessment_reservation"] == ["pi_diag_mid"]
    assert row["model_distributions_json"] is None
    env.clock.advance(1)
    advance(env, serve=False)
    assert len(rows(env, "plan_interrupt")) == 1


def test_with_no_model_set_up_a_placeable_follow_up_joins_deterministically(tmp_path):
    env = _followup_env(tmp_path, fake_runtime())
    record, step = advance(env, serve=True)
    assert step["practice_item_id"] == "pi_diag_mid"
    (row,) = rows(env, "plan_interrupt")
    assert (row["chosen_ref"], row["propensity_kind"], row["policy"]) == ("insert_now", "deterministic", "staged_v1")


# -- Codex review F1, F6, F8 -------------------------------------------------------------------


def _bound_answer(env, step, *, correctness: float = 1.0) -> str:
    """The learner's answer to a served step, bound to the presentation serving returned."""

    at = env.clock.now()
    attempt_id = f"att_{step['practice_item_id']}_{int(at.timestamp())}"
    with env.repository.connection() as connection:
        connection.execute(
            "INSERT INTO practice_attempts(id, practice_item_id, learning_object_id, practice_mode, attempt_type, "
            "correctness, hints_used, primed, latency_seconds, created_at, session_id, evidence_origin, "
            "plan_presentation_id) VALUES (?, ?, ?, 'short_answer', 'independent_attempt', ?, 0, 0, 60, ?, ?, "
            "'human', ?)",
            (attempt_id, step["practice_item_id"], step["learning_object_id"], correctness, iso(at),
             env.session_id, step["presentation_id"]),
        )
        connection.commit()
    return attempt_id


def test_an_inserted_follow_up_is_bound_to_its_own_decision_by_its_presentation(tmp_path):
    # Codex review F1: the follow-up a plan_interrupt decision inserted is
    # answered through Today with the presentation id serving returned; the
    # outcome replayer binds that answer to the interrupt decision exactly.
    from learnloop.db.connection import connect
    from learnloop.router.outcomes import derive_router_outcomes

    runtime = fake_runtime(decider=FakeDecider(choice=first_option, p_yes=1.0),
                           seed=seed_with_first_uniform(at_least=PAST_THE_FLOOR))
    env = _followup_env(tmp_path, runtime, toml=DECIDER_ONLY)
    record, step = advance(env, serve=True)
    assert step["practice_item_id"] == "pi_diag_mid" and step["presentation_id"]
    (interrupt,) = rows(env, "plan_interrupt")
    assert interrupt["chosen_ref"] == "insert_now" and interrupt["propensity_kind"] == "exact"
    env.clock.advance(2)
    answered = _bound_answer(env, step)
    with connect(env.repository.sqlite_path, read_only=True) as connection:
        owner = connection.execute(
            "SELECT router_decision_id FROM plan_presentations WHERE id = ?", (step["presentation_id"],)
        ).fetchone()[0]
        outcomes = {row["decision_id"]: row for row in derive_router_outcomes(connection)}
    outcome = outcomes[interrupt["id"]]
    assert (outcome["action_status"], outcome["action_attempt_id"], outcome["action_binding"]) == (
        "taken", answered, "presentation",
    )
    assert outcome["target_practice_item_id"] == "pi_diag_mid"
    # The presentation names the decision that placed the follow-up.
    assert owner == interrupt["id"]
    # The block's own decision never takes the follow-up's answer as its action.
    block_decision = next(row for row in rows(env) if row["receipt_key"] == f"plan_block:{step['block_id']}")
    assert outcomes[block_decision["id"]]["action_attempt_id"] != answered


def _tight_env(tmp_path, runtime, *, budget: float, followup_los: dict[str, list[tuple[str, float]]]):
    """A plan whose first block (two 1.5-minute items) fills nearly all of
    ``budget``; ``followup_los`` adds learning objects for follow-ups. The
    first item is served and answered."""

    from learnloop.algorithm_versions import ROUTER_MIXTURE_ALGORITHM_VERSION
    from learnloop.daily_plan.policy import policy_for

    from tests.daily_plan_fakes import MovableClock, make_env
    from tests.helpers import append_config_toml, create_daily_plan_vault
    from tests.test_daily_plan_build import _seed_wide

    los = {"lo_m1": [("pi_m1a", 1.0), ("pi_m1b", 1.0)], "lo_m2": [("pi_m2a", 2.0)],
           "lo_r1": [("pi_r1a", 2.0), ("pi_r1b", 2.0)], "lo_p1": [("pi_p1a", 3.0), ("pi_p1b", 3.0)],
           **followup_los}
    paths = create_daily_plan_vault(tmp_path / "vault", learning_objects=los,
                                    version=ROUTER_MIXTURE_ALGORITHM_VERSION)
    append_config_toml(paths.root, DECIDER_ONLY)
    live = list(_wide_items())
    env = make_env(paths.root, lambda: live, clock=MovableClock(), session_id="s1")
    _seed_wide(env.repository)
    env.policy = policy_for(env.vault, env.repository, session_id="s1", clock=env.clock, runtime=runtime, serve=True)
    build_plan(env, kind="normal", budget=budget, remembered=int(budget), minutes_source="chip")
    record, step = advance(env, serve=True)
    assert [item.practice_item_id for item in record.current_block().items] == ["pi_m1a", "pi_m1b"]
    env.clock.advance(1)
    record_attempt(env.repository, step["practice_item_id"], step["learning_object_id"], env.clock.now(),
                   session_id=env.session_id)
    return env, live


def _play_out(env, step, record):
    served = []
    for _ in range(12):
        if step is None or step["kind"] != "item":
            break
        served.append((step["practice_item_id"], step["block_ordinal"]))
        env.clock.advance(2)
        record_attempt(env.repository, step["practice_item_id"], step["learning_object_id"], env.clock.now(),
                       session_id=env.session_id)
        record, step = advance(env, serve=True)
    return record, served


def test_competing_follow_ups_log_only_the_insertions_that_happen(tmp_path):
    # Codex review F6: two follow-ups each fit only by displacing the same
    # remaining tail item. They are decided one at a time against the plan
    # the earlier one left: the second no longer fits, so no insertion is
    # logged for it, and every logged insert_now is placed.
    runtime = fake_runtime(decider=FakeDecider(choice=first_option, p_yes=1.0),
                           seed=seed_with_first_uniform(at_least=PAST_THE_FLOOR))
    env, live = _tight_env(tmp_path, runtime, budget=3.05,
                           followup_los={"lo_f1": [("pi_f1a", 0.7), ("pi_f1b", 0.7)]})
    for item in ("pi_f1a", "pi_f1b"):
        live.insert(0, scheduled(item, "lo_f1", followup_kind="negative_surprise_followup"))
    env.clock.advance(1)
    record, step = advance(env, serve=True)
    planned = {item.practice_item_id for item in record.items() if item.origin == "followup" and not item.displaced}
    inserted = [row for row in rows(env, "plan_interrupt") if row["chosen_ref"] == "insert_now"]
    assert len(planned) == 1 and step["practice_item_id"] in planned
    assert {row["chosen_practice_item_id"] for row in inserted} == planned
    assert record.minutes_planned() <= record.budget + 1e-6


def test_a_follow_up_that_waiting_would_drop_joins_now(tmp_path):
    # Codex review F8: the follow-up fits now only by displacing the block's
    # unserved tail, so after the block there is no room for it today.
    # Waiting would drop it, so waiting is not offered: it joins now, with no
    # model asked, and the row names waiting infeasible.
    decider = FakeDecider(choice=first_option, p_yes=0.0)
    runtime = fake_runtime(decider=decider, seed=seed_with_first_uniform(at_least=PAST_THE_FLOOR))
    env, live = _tight_env(tmp_path, runtime, budget=3.05, followup_los={"lo_f1": [("pi_f1a", 0.7)]})
    asked_before = len(decider.calls)
    live.insert(0, scheduled("pi_f1a", "lo_f1", followup_kind="negative_surprise_followup"))
    env.clock.advance(1)
    record, step = advance(env, serve=True)
    assert step["practice_item_id"] == "pi_f1a"
    (row,) = rows(env, "plan_interrupt")
    assert (row["chosen_ref"], row["propensity_kind"], row["policy"]) == ("insert_now", "deterministic", "staged_v1")
    by_ref = {entry["ref"]: entry for entry in row["candidates_json"]}
    assert by_ref["insert_now"]["feasible"] and not by_ref["continue_current"]["feasible"]
    assert row["detail_json"]["wait"] == {"feasible": False, "reason": "no_room_after_block"}
    assert len(decider.calls) == asked_before
    _record, served = _play_out(env, step, record)
    assert ("pi_f1a", 1) in served


class _WaitsOnF1(FakeDecider):
    """P(intervene now) = 0 for the follow-up on F1, 1 for any other."""

    def _decide(self, state, questions, **kwargs):
        self.p_yes = 0.0 if "question on F1" in str(state) else 1.0
        return super()._decide(state, questions, **kwargs)


def test_a_waiting_follow_up_keeps_its_room_until_the_boundary(tmp_path):
    # Codex review F8: a follow-up that waits keeps its room. A later
    # follow-up cannot take it (it must displace the tail instead), and at
    # the boundary the waiting one opens the next block in its kept room,
    # although its estimate has grown since with the session's answers.
    runtime = fake_runtime(decider=_WaitsOnF1(choice=first_option),
                           seed=seed_with_first_uniform(at_least=PAST_THE_FLOOR))
    env, live = _tight_env(tmp_path, runtime, budget=4.6,
                           followup_los={"lo_f1": [("pi_f1a", 0.7)], "lo_g1": [("pi_g1a", 0.7)]})
    live.insert(0, scheduled("pi_g1a", "lo_g1", followup_kind="negative_surprise_followup", priority=0.4))
    live.insert(0, scheduled("pi_f1a", "lo_f1", followup_kind="negative_surprise_followup", priority=0.9))
    env.clock.advance(1)
    record, step = advance(env, serve=True)
    decisions = {row["detail_json"]["followup"]["practice_item_id"]: row for row in rows(env, "plan_interrupt")}
    assert decisions["pi_f1a"]["chosen_ref"] == "continue_current"
    assert decisions["pi_f1a"]["propensity_kind"] == "exact"
    assert decisions["pi_g1a"]["chosen_ref"] == "insert_now"
    assert record.current_block().deferred_followups() == {"pi_f1a"}
    # The later follow-up displaced the tail rather than taking the kept room.
    assert {item.practice_item_id for item in record.items() if item.displaced} == {"pi_m1b"}
    record, served = _play_out(env, step, record)
    assert ("pi_g1a", 1) in served and ("pi_f1a", 2) in served
    assert record.minutes_planned() <= record.budget + 1e-6

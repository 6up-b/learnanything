"""What other test files use from ``tests/test_data_capture_a2_measurement.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from datetime import timedelta

from learnloop.algorithm_versions import DATA_CAPTURE_ALGORITHM_VERSION
from learnloop.daily_plan import engine
from learnloop.daily_plan import measurement as M
from learnloop.data_capture import reading_exposures as RE
from learnloop.daily_plan.engine import advance, build_plan
from learnloop.daily_plan.lanes import ReadingTarget
from learnloop.db.stores import data_capture as store
from learnloop.router import outcomes as RO

from tests.daily_plan_fakes import record_attempt
from tests.router_mixture_helpers import mixture_env, rows
from tests.router_model_fakes import FakeDecider, fake_runtime, first_option, seed_with_first_uniform
from tests.router_g4_restraint_helpers import DECIDER_ONLY, PAST_THE_FLOOR, _followup_env


TAG = DATA_CAPTURE_ALGORITHM_VERSION
READING = ReadingTarget(source_id="s", extraction_id="e", section_id="sec", section_title="A section", words_left=800)


def _objectives(env):
    with env.repository.connection() as connection:
        return store.objectives(connection)


def _events(env):
    with env.repository.connection() as connection:
        return store.measurement_events(connection)


def _outcomes(env, version=RO.OUTCOME_VERSION_V3):
    with env.repository.connection() as connection:
        return {row["decision_id"]: row for row in RO.derive_router_outcomes(
            connection, outcome_version=version,
            reader_exposures=RE.for_version(connection, env.vault, env.repository, version))}


def _answer(env, item, lo, *, correctness=1.0, hints=0):
    with env.repository.connection() as connection:
        connection.execute(
            "INSERT INTO practice_attempts(id, practice_item_id, learning_object_id, practice_mode, attempt_type,"
            " hints_used, correctness, manual_review, created_at, session_id, primed, evidence_origin)"
            " VALUES (?,?,?,?,?,?,?,0,?,?,0,'human')",
            (f"att_{item}_{env.now_iso()}", item, lo, "short_answer", "independent_attempt", hints, correctness,
             env.now_iso(), "s_later"),
        )
        connection.commit()


def _picker(*wanted):
    def choice(refs):
        for ref in refs:
            if any(token in ref for token in wanted):
                return {other: (1.0 if other == ref else 0.0) for other in refs}
        return first_option(refs)

    return choice


def _reading_env(tmp_path, monkeypatch, *, choice, toml=DECIDER_ONLY, version=TAG, los=("lo_diag",)):
    monkeypatch.setattr(engine, "_fresh_reading", lambda _env, _intent: (READING, None))
    monkeypatch.setattr(engine, "deliverable_plan_active", lambda _vault: False)
    monkeypatch.setattr(M, "reading_learning_objects", lambda _vault, _repo, _target: list(los))
    runtime = fake_runtime(decider=FakeDecider(choice=choice), seed=seed_with_first_uniform(at_least=PAST_THE_FLOOR))
    from learnloop.algorithm_versions import ROUTER_OBJECTIVE_VERSIONS

    if version in ROUTER_OBJECTIVE_VERSIONS:
        # These steer R2b's mixture with a Decider; at router objective RO4's tag the Decider is advice only, so the
        # frame they exercise is the objective switched off (RO4's own arms: tests/test_ro4_objective_serving.py).
        toml = f"{toml or ''}\n[router_objective]\nenabled = false\n"
    return mixture_env(tmp_path, runtime, version=version, toml=toml)


def _reading_decision(env):
    build_plan(env, kind="normal", budget=40.0, remembered=40, minutes_source="chip")
    for _ in range(12):
        record, step = advance(env, serve=True)
        if step is None or step["kind"] == "reading":
            return record, step
        env.clock.advance(1)
        record_attempt(env.repository, step["practice_item_id"], step["learning_object_id"], env.clock.now(),
                       session_id=env.session_id)
    return record, step


def _arranged_wait(tmp_path, *, toml=DECIDER_ONLY):
    runtime = fake_runtime(decider=FakeDecider(choice=first_option, p_yes=0.0),
                           seed=seed_with_first_uniform(at_least=PAST_THE_FLOOR))
    env = _followup_env(tmp_path, runtime, version=TAG, toml=toml)
    advance(env, serve=True)
    (row,) = rows(env, "plan_interrupt")
    return env, row["id"], _objectives(env)[row["id"]]


def _due_measurement(tmp_path):
    env, decision_id, objective = _arranged_wait(tmp_path)
    env.clock.instant = env.clock.instant + timedelta(days=30)
    return env, decision_id, objective

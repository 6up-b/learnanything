"""Data capture A5: the router's ``not_ready`` branch keeps the existing fallback distribution.

With neither model set up the staged rule's pick used to be deterministic, though a full model failure
later keeps the floor (owner Q7). From mvp-0.44, with ``data_capture.serving`` on, ``not_ready`` draws
from the same distribution with the same ``router.epsilon_min``: no new constant and zero model calls.
Below the tag, or with the switch off, the plan and the row are the predecessor's byte for byte.
"""

from __future__ import annotations


from learnloop.algorithm_versions import DATA_CAPTURE_ALGORITHM_VERSION, LESSON_SUGGESTIONS_ALGORITHM_VERSION
from learnloop.daily_plan import router_chooser as RC
from learnloop.daily_plan.engine import advance, build_plan
from learnloop.router import mixture as mx

from tests.router_mixture_helpers import mixture_env, rows, run
from tests.router_model_fakes import FakeDecider, FakeLLM, fake_runtime, seed_with_first_uniform

TAG = DATA_CAPTURE_ALGORITHM_VERSION
OLD = LESSON_SUGGESTIONS_ALGORITHM_VERSION
OFF = "[data_capture]\nserving = false\n"


def _blocks(record):
    return [(block.lane, tuple(item.practice_item_id for item in block.items)) for block in record.blocks]


def _floor_row(env):
    found = [row for row in rows(env) if (row["detail_json"].get("router") or {}).get("decided_by") == "not_ready"]
    assert found
    return found


def test_not_ready_draws_from_the_fallback_distribution_with_its_floor_and_exact_propensity(tmp_path):
    env = mixture_env(tmp_path, fake_runtime(), version=TAG)
    run(env)
    drawn = [row for row in _floor_row(env) if row["propensity_kind"] == "exact"]
    assert drawn, "a not_ready decision with more than one reversible option is a logged draw"
    for row in drawn:
        mixture = row["detail_json"]["mixture"]
        epsilon = env.vault.config.router.epsilon_min
        assert mixture["epsilon"] == epsilon and row["design"] == mx.DESIGN and row["seed"]
        assert mixture["effective_weights"] == {"staged": 1.0, "decider": 0.0, "llm": 0.0}
        assert row["fallback"] == "both"
        # The rule's pick keeps the rest of the mass: every option of the support keeps the floor.
        by_ref = {entry["ref"]: entry["propensity"] for entry in row["candidates_json"]}
        k = len(mixture["support"])
        for ref in mixture["support"]:
            expected = (1 - k * epsilon) * (1.0 if ref == mixture["staged_ref"] else 0.0) + epsilon
            assert abs(by_ref[ref] - expected) < 1e-12
        assert abs(row["propensity"] - by_ref[row["chosen_ref"]]) < 1e-12
        assert row["cost_usd"] == 0.0 and row["latency_ms"] is None


def test_not_ready_asks_no_model(tmp_path):
    """Zero model calls: the runtime starts no job, and the row holds no request or response."""

    runtime = fake_runtime()
    started: list[str] = []
    original = runtime.start

    def spy(*args, **kwargs):
        started.append(args[1])
        return original(*args, **kwargs)

    runtime.start = spy  # type: ignore[method-assign]
    env = mixture_env(tmp_path, runtime, version=TAG)
    run(env)
    assert started == []
    with env.repository.connection() as connection:
        kinds = {row[0] for row in connection.execute("SELECT kind FROM router_decision_payloads")}
    assert kinds <= {"card"}


def test_the_floor_can_draw_another_option_than_the_rules(tmp_path):
    """Below the floor's share the first uniform picks the uniform component: a comparison is made."""

    env = mixture_env(tmp_path, fake_runtime(seed=seed_with_first_uniform(below=0.01)), version=TAG)
    run(env)
    drawn = [row for row in _floor_row(env) if row["propensity_kind"] == "exact"]
    assert {row["detail_json"]["mixture"]["drawn_component"] for row in drawn} == {mx.UNIFORM}
    assert any(row["chosen_ref"] != row["detail_json"]["mixture"]["staged_ref"] for row in drawn)


def test_the_draw_reproduces_from_its_logged_seed(tmp_path):
    env = mixture_env(tmp_path, fake_runtime(), version=TAG)
    run(env)
    for row in _floor_row(env):
        if row["propensity_kind"] != "exact":
            continue
        mixture = row["detail_json"]["mixture"]
        support = mixture["support"]
        components = mx.component_distributions(support, mixture["staged_ref"], {})
        again = mx.draw(support, components, mixture["effective_weights"], mixture["epsilon"], row["seed"])
        assert again.chosen == row["chosen_ref"] and abs(again.propensity - row["propensity"]) < 1e-12


def test_a_single_option_stays_the_rules_deterministic_pick(tmp_path):
    env = mixture_env(tmp_path, fake_runtime(), version=TAG, toml="[router]\nk = 2\nties_only = true\n")
    run(env)
    for row in rows(env):
        decided_by = (row["detail_json"].get("router") or {}).get("decided_by")
        if decided_by == "single_option":
            assert row["propensity_kind"] in {"deterministic", "none"} and row["design"] is None


def test_the_restraint_keeps_the_floor_on_not_ready_too(tmp_path):
    """The follow-up's now-or-wait decision has the same not_ready branch; waiting gets its floor."""

    from learnloop.daily_plan.router_chooser import RestraintGate
    from learnloop.router.plan_log import INSERT_REF

    class Item:
        practice_item_id = "pi_m1a"
        learning_object_id = "lo_m1"
        lane = "repair"
        est_minutes = 2.0

    env = mixture_env(tmp_path, fake_runtime(), version=TAG)
    record = run_first_block(env)
    current = record.current_block() or record.blocks[0]
    gate = env.policy.restraint
    assert isinstance(gate, RestraintGate)
    outcome = gate.decide(record, current, Item())
    assert outcome.record["decided_by"] == "not_ready"
    assert outcome.record["design"] == mx.DESIGN and outcome.record["seed"]
    pi = outcome.record["mixture"]["pi"]
    epsilon = env.vault.config.router.epsilon_min
    assert abs(pi[RC.CONTINUE_CURRENT] - epsilon) < 1e-12 and abs(pi[INSERT_REF] - (1 - epsilon)) < 1e-12
    assert 0 < outcome.propensity <= 1


def run_first_block(env):
    build_plan(env, kind="normal", budget=25.0, remembered=25, minutes_source="chip")
    record, step = advance(env, serve=True)
    assert step["kind"] == "item"
    return record


def test_below_the_tag_or_switched_off_it_is_the_predecessors(tmp_path):
    old = mixture_env(tmp_path / "old", fake_runtime(), version=OLD)
    off = mixture_env(tmp_path / "off", fake_runtime(), version=TAG, toml=OFF)
    assert _blocks(run(old)) == _blocks(run(off))
    for env in (old, off):
        for row in rows(env):
            assert row["propensity_kind"] in {"deterministic", "none"} and row["design"] is None
        assert all(not (row["detail_json"].get("mixture")) for row in rows(env))
    for env in (old, off):
        record = advance(env, serve=False)[0]
        assert record is not None


def test_a_model_that_answers_is_untouched(tmp_path):
    """Only the branch with no ready model changes: with models set up it is the ordinary mixture."""

    env = mixture_env(tmp_path, fake_runtime(decider=FakeDecider(), llm=FakeLLM()), version=TAG)
    run(env)
    assert {(row["detail_json"].get("router") or {}).get("decided_by") for row in rows(env)} & {"not_ready"} == set()
    assert any(row["policy"] == mx.POLICY for row in rows(env))



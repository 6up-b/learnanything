"""Router objective RO6 §10, the data: logged decisions, trajectories, fits by version, availability, the report.

* **Frozen-logger invariance**: refitting after a later generator version exists does not change version ``k``'s
  evaluation; the transition across the change point is censored ``change_point``;
* **availability**: a trace, an RO0 receipt or an imported result received after the moment never enters a feature
  or a reward (THE availability predicate, ``router_objective_switches.known_at`` / ``attempt_time_sql``);
* the transitions carry this objective's reward (the attention cost, the randomized checks at ``c/r``), never
  ``S``, each censored by a named reason;
* the report states the narrow claim and no guarantee, and lists the versions, change points and ŵ's history;
* **a few simulated weeks** on the copy-shaped synthetic vault: the fit's size and time, ŵ's path, the residual's
  share of ``Ṽ`` and the serving time, printed for the stage record.

Fakes only; no model request.
"""

from __future__ import annotations

import json
import os

import pytest

from learnloop.algorithm_versions import ROUTER_LEARNED_TAIL_ALGORITHM_VERSION
from learnloop.db.stores import router_objective as store
from learnloop.router_objective import tail_data as TD
from learnloop.router_objective import tail_report as TR
from learnloop.vault.loader import load_vault

from tests.helpers import append_config_toml
from tests.router_model_fakes import FakeLLM, fake_runtime
from tests.test_ro4_objective_serving import policy_answer
from tests.test_ro5_calibration import _end_session, _grade_answers, _new_session, _week_env
from tests.router_mixture_helpers import run

TAG = ROUTER_LEARNED_TAIL_ALGORITHM_VERSION
REASONS = {TD.NO_LATER_DECISION, TD.CHANGE_POINT, TD.VALUE_MISSING, TD.PAST_CUTOFF, TD.REWARD_OPEN, TD.NO_RESULT,
           TD.CUTOFF_UNMATCHED}


def _days(env, runtime, days: range, *, skip: frozenset[int] = frozenset(), steps: int = 60) -> None:
    for day in days:
        if day not in skip:
            session_id = _new_session(env, runtime, day)
            run(env, steps=steps)
            _grade_answers(env, day)
            _end_session(env, session_id)
        env.clock.advance(24 * 60)


def _tag_env(tmp_path, runtime, toml: str | None = None):
    env = _week_env(tmp_path, runtime)
    from learnloop.vault.paths import VaultPaths
    from tests.helpers import set_algorithm_version

    set_algorithm_version(VaultPaths(env.vault.root, env.vault.config), TAG)
    if toml:
        append_config_toml(env.vault.root, toml)
    env.vault = load_vault(env.vault.root)
    return env


def test_refitting_on_a_later_version_does_not_change_version_ks_evaluation(tmp_path):
    runtime = fake_runtime(llm=FakeLLM(answer=policy_answer))
    env = _tag_env(tmp_path, runtime)
    _days(env, runtime, range(3))
    from learnloop.daily_plan.objective_chooser import generator_now

    first = generator_now(env.vault.config)
    with env.repository.connection() as connection:
        before = TD.fits(connection, env.vault.config, at=env.now_iso())
    assert first in before.by_generator and before.by_generator[first].n > 0
    # A new generator version: the mix's prior weight changes (the logger changes).
    append_config_toml(env.vault.root, "[router_objective]\nllm_weight_prior = 0.7\n")
    env.vault = load_vault(env.vault.root)
    second = generator_now(env.vault.config)
    assert second != first
    _days(env, runtime, range(3, 5))
    with env.repository.connection() as connection:
        after = TD.fits(connection, env.vault.config, at=env.now_iso())
    assert after.order[:1] == (first,) and second in after.order
    assert after.by_generator[first] == before.by_generator[first]
    assert after.steps.censored.get(TD.CHANGE_POINT) == 1
    assert [(point["from"], point["to"]) for point in after.steps.change_points] == [(first, second)]
    # Serving under the new version uses its own fit once it has transitions; with none, version k's.
    model, basis = after.for_serving(second)
    assert basis == ("own_version" if second in after.by_generator else "previous_version")
    assert model is not None


def test_the_transitions_carry_the_objectives_reward_with_named_censoring(tmp_path):
    runtime = fake_runtime(llm=FakeLLM(answer=policy_answer))
    env = _tag_env(tmp_path, runtime)
    _days(env, runtime, range(3))
    with env.repository.connection() as connection:
        rows = TD.logged(connection, env.vault.config, at=env.now_iso())
        steps = TD.transitions(connection, env.vault.config, rows, at=env.now_iso())
    assert rows and steps.transitions
    assert set(steps.censored) <= REASONS and steps.censored.get(TD.NO_LATER_DECISION) == 1
    # Every next decision valued its state at the earlier decision's cutoff too (Codex review F3): none unmatched.
    assert steps.censored.get(TD.CUTOFF_UNMATCHED, 0) == 0
    assert {step.detail["cutoff"] for step in steps.transitions} <= {"same_cutoff", "previous_cutoff"}
    assert {row.features_source for row in rows} == {"frozen"}
    for step in steps.transitions:
        assert len(step.phi) == len(step.next_phi)
        # Within a session the reward is minus the attention cost of the interval: never S's labels.
        if step.detail["checks"] == 0:
            assert step.reward <= 0.0
    # Across a day boundary the day's randomized check enters at c / r.
    assert any(step.detail["checks"] > 0 and step.reward > 0 for step in steps.transitions) or not any(
        step.detail["checks"] for step in steps.transitions)


def test_a_row_received_after_the_moment_never_enters_a_feature(tmp_path):
    runtime = fake_runtime(llm=FakeLLM(answer=policy_answer))
    env = _tag_env(tmp_path, runtime)
    _days(env, runtime, range(1))
    with env.repository.connection() as connection:
        traces = store.traces(connection)
        first, last = traces[0], traces[-1]
        before = TD.logged(connection, env.vault.config, at="2000-01-01T00:00:00Z")
        middle = TD.logged(connection, env.vault.config, at=first["created_at"])
        # RO0's receipt of the first decision, asked as of a moment before it was written: not known.
        early = TD._receipt(connection, first["decision_id"], env.vault.config, "2000-01-01T00:00:00Z")
        known = TD._receipt(connection, first["decision_id"], env.vault.config, last["created_at"])
    assert before == []
    assert [row.decision_id for row in middle] == [row["decision_id"] for row in traces
                                                   if row["created_at"] <= first["created_at"]]
    assert early is None and known is not None and "state" in known


@pytest.mark.parametrize("toml, sees_exam", [(None, False), ("[router_objective]\navailable_at_reads = false\n", True)],
                         ids=["tag", "switched_off"])
def test_an_exam_imported_after_the_moment_is_no_reward_yet(tmp_path, toml, sees_exam):
    from tests.test_ro1_availability_reads import AFTER, CUTOFF, LO, _seeded

    vault, repository = _seeded(tmp_path, TAG, toml)
    with repository.connection() as connection:
        at_cutoff = TD._exam_result_known(connection, vault.config, LO, "2026-05-01", CUTOFF)
        after = TD._exam_result_known(connection, vault.config, LO, "2026-05-01", AFTER)
    assert (at_cutoff is not None) is sees_exam
    assert after is not None


def test_the_report_states_the_claim_and_lists_versions_and_w_hats_history(tmp_path):
    runtime = fake_runtime(llm=FakeLLM(answer=policy_answer))
    env = _tag_env(tmp_path, runtime)
    _days(env, runtime, range(2))
    with env.repository.connection() as connection:
        report = TR.build(connection, env.vault, now=env.now_iso())
    assert report["claim"].startswith("the logger's value plus one small improvement step")
    assert "no improvement guarantee" in report["no_guarantee"]
    assert report["kept_evaluations"] == ["forecast", "action_value", "recommendation_value", "whole_policy"]
    assert report["versions"] and report["versions"][0]["fit"]["n"] >= 0
    assert [day["local_date"] for day in report["w_hat_history"]] and report["w_hat"]["w_hat"] == 0.0
    assert all(isinstance(line, str) and line for line in TR.lines(report))
    from typer.testing import CliRunner

    from learnloop.cli.app import app

    result = CliRunner().invoke(app, ["router", "objective-report", "--vault", str(env.vault.root), "--json"])
    assert result.exit_code == 0, result.output
    assert "learned_tail" in json.loads(result.output)["router_objective"]


def test_a_few_weeks_on_a_copy_shaped_synthetic_vault(tmp_path):
    """Two weeks and a day by default (``LEARNLOOP_RO6_DAYS`` for more), one day a week without a session, the default
    arms (the coin 0.05 each way, one embedded check a day), both policies answering. Printed for the stage record:
    the fit's size and time, ŵ's path, the residual's share of ``Ṽ`` and the serving time per decision."""

    days = int(os.environ.get("LEARNLOOP_RO6_DAYS", "15"))
    runtime = fake_runtime(llm=FakeLLM(answer=policy_answer))
    env = _tag_env(tmp_path, runtime)
    _days(env, runtime, range(days), skip=frozenset(day for day in range(days) if day % 7 == 3))
    with env.repository.connection() as connection:
        report = TR.build(connection, env.vault, now=env.now_iso())
    summary = {
        "days": days, "transitions": report["transitions"], "versions": [
            {key: entry.get(key) for key in ("generator", "decisions", "features")} | {
                "fit_n": entry["fit"].get("n"), "sigma2": entry["fit"].get("sigma2"),
                "condition": entry["fit"].get("condition")} for entry in report["versions"]],
        "w_hat": {key: report["w_hat"][key] for key in ("w_hat", "slope_mean", "slope_sd", "n", "forced", "rank",
                                                         "p_rank", "source")},
        "w_hat_path": [(day["local_date"], day["w_hat_last"], day["contrasts"]) for day in report["w_hat_history"]],
        "serving": report["serving"], "cross_check": report["cross_check"]["partial_history"].get("one_step"),
        "fit_projection": report["cross_check"]["fit_projection"],
    }
    print("RO6_WEEKS_REPORT", json.dumps(summary, sort_keys=True, default=str))
    assert report["transitions"]["n"] > 0
    assert 0.0 <= report["w_hat"]["w_hat"] <= 1.0
    assert report["serving"]["decisions_with_residual"] > 0

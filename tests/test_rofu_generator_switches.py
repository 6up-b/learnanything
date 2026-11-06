"""The follow-up batch's landing ruling R8: its serving switches are part of RO6's generator payload.

Each switch that changes a logged decision's value or mixture (``combiner_trace_outcomes``, ``merged_sessions``,
``consistent_review_draw``, ``scope_extension``) is in the generator version, so flipping one is a change point and
never changes ``Q`` under the same generator version. ``carried_in_prefetch`` changes only which transitions are
valued, not the logger, so it is not. Below the batch's tag the trace and the payload are RO6's. Fakes only.
"""

from __future__ import annotations

import pytest

from learnloop.algorithm_versions import ROUTER_FOLLOWUPS_ALGORITHM_VERSION, ROUTER_LEARNED_TAIL_ALGORITHM_VERSION
from learnloop.router_objective import tail_data as TD
from learnloop.router_objective_switches import FOLLOWUP_GENERATOR_SWITCHES

TAG = ROUTER_FOLLOWUPS_ALGORITHM_VERSION
OLD = ROUTER_LEARNED_TAIL_ALGORITHM_VERSION


def _served(tmp_path, *, version: str = TAG, toml: str | None = None) -> list[dict]:
    from learnloop.db.stores import router_objective as store

    from tests.router_mixture_helpers import mixture_env, run
    from tests.router_model_fakes import block_drawing_seed, fake_runtime

    env = mixture_env(tmp_path, fake_runtime(seed=block_drawing_seed()), version=version, toml=toml)
    run(env, steps=4)
    with env.repository.connection() as connection:
        rows = [store.trace(connection, row["decision_id"]) for row in store.traces(connection)]
    return [row["trace"] for row in rows if row["decision_kind"] == "plan_block"]


def _generators(traces: list[dict], version: str, *, scope_extension: bool) -> set[str]:
    return {TD.generator(trace, version, scope_extension=scope_extension) for trace in traces}


def test_at_the_defaults_the_payload_is_stable_across_decisions_and_is_the_one_served(tmp_path):
    traces = _served(tmp_path)
    assert len(traces) >= 2
    assert {tuple(sorted(trace["versions"]["serving_switches"].items())) for trace in traces} == {
        tuple(sorted((key, True) for key in FOLLOWUP_GENERATOR_SWITCHES))}
    generators = _generators(traces, TAG, scope_extension=True)
    assert len(generators) == 1
    # the serve logged each decision under the generator its trace recomputes (``generator_now``)
    assert {trace["residual"]["generator"] for trace in traces} == generators


@pytest.mark.parametrize("switch", FOLLOWUP_GENERATOR_SWITCHES)
def test_flipping_a_serving_switch_is_a_new_generator_version(tmp_path, switch):
    default = _generators(_served(tmp_path / "default"), TAG, scope_extension=True)
    flipped_traces = _served(tmp_path / "flipped", toml=f"[router_objective]\n{switch} = false\n")
    flipped = _generators(flipped_traces, TAG, scope_extension=switch != "scope_extension")
    assert len(flipped) == 1 and flipped != default
    assert {trace["residual"]["generator"] for trace in flipped_traces} == flipped
    assert all(trace["versions"]["serving_switches"][switch] is False for trace in flipped_traces)


def test_carried_in_prefetch_is_not_part_of_the_generator(tmp_path):
    default = _generators(_served(tmp_path / "default"), TAG, scope_extension=True)
    flipped = _generators(_served(tmp_path / "flipped", toml="[router_objective]\ncarried_in_prefetch = false\n"),
                          TAG, scope_extension=True)
    assert flipped == default


def test_below_the_tag_the_trace_and_the_payload_are_ro6s(tmp_path):
    traces = _served(tmp_path, version=OLD)
    assert traces and all("serving_switches" not in trace["versions"] for trace in traces)
    payload = TD.generator_payload(algorithm_version=OLD, objective="o", tail="t", terminal="c", horizon_days=90.0,
                                   llm_schema="s", seeds={}, epsilon=0.05)
    assert "switches" not in payload
    assert {trace["residual"]["generator"] for trace in traces} == _generators(traces, OLD, scope_extension=False)

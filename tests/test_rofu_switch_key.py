"""The follow-up batch's landing ruling R12: the switches are part of the prefetch boundary key, and an answer's trace
names the switches it was computed under.

Codex's N3: with a warm prefetch at mvp-0.50, reloading the config with a switch flipped and serving the same
boundary reused the cached answer (``objective_settings`` named none of the batch's switches), while the trace
recorded the serving config's switches, so old ``Q`` values were logged under the new generator. Now the key names
the tag-gated switch snapshot (a flip starts a new job), and every numeric answer freezes the generator switches it
was computed under, which its trace records. Codex's reproduction: the real ``ObjectiveChooser.choose`` at one
boundary (the model branch, a shared runtime cache), served again at once with the config reloaded. Fakes only.
"""

from __future__ import annotations

from dataclasses import replace
from typing import Any, Callable

import pytest

from learnloop.algorithm_versions import ROUTER_FOLLOWUPS_ALGORITHM_VERSION, ROUTER_LEARNED_TAIL_ALGORITHM_VERSION
from learnloop.daily_plan import objective_chooser as OC
from learnloop.daily_plan.router_runtime import RouterRuntime
from learnloop.router_objective import tail_data as TD
from learnloop.router_objective_switches import FOLLOWUP_GENERATOR_SWITCHES

TAG = ROUTER_FOLLOWUPS_ALGORITHM_VERSION


def _flipped(config, switch: str):
    section = config.router_objective.model_copy(update={switch: not getattr(config.router_objective, switch)})
    return config.model_copy(update={"router_objective": section})


def _at_first_boundary(tmp_path, monkeypatch, then: Callable[..., Any]) -> Any:
    """Run the journey; at the first boundary the chooser decides (its job starts and finishes), and right after it,
    with nothing recorded in between, ``then(serve, starts, base)`` serves the same boundary again under a given
    config (``serve(config)`` returns the choice; ``base``: the chooser's own config; ``starts``: the keys a new job
    started for)."""

    from tests.router_mixture_helpers import mixture_env, run
    from tests.router_model_fakes import FakeLLM, block_drawing_seed, fake_runtime
    from tests.ro4_objective_serving_helpers import policy_answer

    real_choose = OC.ObjectiveChooser.choose
    outcome: list[Any] = []

    def capture(self, state, feasible):
        choice = real_choose(self, state, feasible)
        if not outcome:
            original = self.vault

            def serve(config):
                self.vault = replace(original, config=config)
                try:
                    return real_choose(self, state, feasible)
                finally:
                    self.vault = original

            outcome.append(then(serve, starts, original.config))
        return choice

    starts: list[str] = []
    real_start = RouterRuntime.start

    def counted(self, scope, key, **kwargs):
        if self.lookup(scope, key) is None:
            starts.append(key)
        return real_start(self, scope, key, **kwargs)

    monkeypatch.setattr(OC.ObjectiveChooser, "choose", capture)
    monkeypatch.setattr(RouterRuntime, "start", counted)
    # The model branch (an LLM policy is ready), so the boundary is a prefetch job keyed by the boundary key.
    env = mixture_env(tmp_path, fake_runtime(llm=FakeLLM(answer=policy_answer), seed=block_drawing_seed()),
                      version=TAG)
    run(env, steps=4)
    assert outcome, "no boundary decision was made"
    return outcome[0]


@pytest.mark.parametrize("switch", [*FOLLOWUP_GENERATOR_SWITCHES, "carried_in_prefetch"])
def test_flipping_a_switch_between_prefetch_and_serve_starts_a_new_job(tmp_path, monkeypatch, switch):
    def then(serve, starts, base):
        before = len(starts)
        assert before >= 1
        serve(base)
        reused = len(starts) == before
        flipped_choice = serve(_flipped(base, switch))
        return reused, len(starts) - before, flipped_choice

    reused, new_jobs, flipped_choice = _at_first_boundary(tmp_path, monkeypatch, then)
    assert reused  # the same settings: the warm entry is served
    assert new_jobs == 1, switch
    if switch != "carried_in_prefetch":
        trace = (flipped_choice.router_record or {}).get("objective_trace")
        assert trace is not None
        assert trace["versions"]["serving_switches"][switch] is False
        assert trace["residual"]["generator"] == TD.generator(trace, TAG, scope_extension=switch != "scope_extension")


def test_below_the_tag_the_key_names_no_switch():
    from learnloop.config.schema import LearnLoopConfig

    config = LearnLoopConfig()
    below = config.model_copy(update={"algorithms": config.algorithms.model_copy(
        update={"algorithm_version": ROUTER_LEARNED_TAIL_ALGORITHM_VERSION})})
    assert "followup_switches" not in OC.objective_settings(below)
    at_tag = config.model_copy(update={"algorithms": config.algorithms.model_copy(update={"algorithm_version": TAG})})
    assert set(OC.objective_settings(at_tag)) == set(OC.objective_settings(below)) | {"followup_switches"}


@pytest.mark.parametrize("switch", ["consistent_review_draw", "monotone_combiner"])
def test_a_served_cached_answer_names_the_generator_that_produced_it(tmp_path, monkeypatch, switch):
    """With the key forced to ignore the switches (Codex's warm entry: the predecessor's key), the cached answer is
    served under a flipped config: its trace still records the switches it was computed under, and the generator the
    trace recomputes is the one its residual was logged under."""

    real_settings = OC.objective_settings
    monkeypatch.setattr(OC, "objective_settings",
                        lambda config: {k: v for k, v in real_settings(config).items() if k != "followup_switches"})

    def then(serve, starts, base):
        before = len(starts)
        choice = serve(_flipped(base, switch))
        return len(starts) - before, choice

    new_jobs, choice = _at_first_boundary(tmp_path, monkeypatch, then)
    assert new_jobs == 0  # the warm entry was reused
    trace = (choice.router_record or {}).get("objective_trace")
    assert trace is not None
    assert trace["versions"]["serving_switches"][switch] is True  # computed with it on; served with it off
    assert trace["residual"]["generator"] == TD.generator(trace, TAG, scope_extension=True)

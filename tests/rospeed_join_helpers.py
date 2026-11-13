"""What other test files use from ``tests/test_rospeed_join.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from learnloop.algorithm_versions import LATEST_ALGORITHM_VERSION


TAG = LATEST_ALGORITHM_VERSION


def _journey(tmp_path, steps: int = 3, *, version: str = TAG):
    """A journey at the tag, both policies answering through fakes. Three steps: the first decisions' blocks, so
    their untouched topics are still untouched (a later answer on one is a cold outcome with no exposure between)."""

    from tests.router_mixture_helpers import mixture_env, run
    from tests.router_model_fakes import FakeLLM, block_drawing_seed, fake_runtime
    from tests.ro4_objective_serving_helpers import policy_answer

    env = mixture_env(tmp_path, fake_runtime(llm=FakeLLM(answer=policy_answer), seed=block_drawing_seed()),
                      version=version)
    run(env, steps=steps)
    return env

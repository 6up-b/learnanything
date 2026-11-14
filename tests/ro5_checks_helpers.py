"""What other test files use from ``tests/test_ro5_checks.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from learnloop.algorithm_versions import LATEST_ALGORITHM_VERSION
from learnloop.router_objective import checks as C

from tests.router_mixture_helpers import mixture_env
from tests.router_model_fakes import fake_runtime


TAG = LATEST_ALGORITHM_VERSION
CHECKS_ONLY = "[router_objective]\nstop_coin = 0.0\npick_open_share = 0.0\n"


def _env(tmp_path, *, toml: str = CHECKS_ONLY, llm=None):
    return mixture_env(tmp_path, fake_runtime(llm=llm), version=TAG, toml=toml)


def grade_checks(env, correctness: float) -> None:
    """Grade every answered check (the fake run records ungraded answers)."""

    with env.repository.atomic(), env.repository.connection() as connection:
        for entry in C.resolve(connection, through="9999-12-31"):
            if entry.attempt_id:
                connection.execute("UPDATE practice_attempts SET correctness = ? WHERE id = ?",
                                   (correctness, entry.attempt_id))


def _trace(*, decision_mu=None, llm=None, numeric="a", coin=None):
    return {
        "mixing": {"mu": decision_mu or {"a": 0.5, "b": 0.5}, "chosen": "a"},
        "policies": {"llm": {"distribution": llm or {"a": 0.2, "b": 0.8}}, "numeric": {"choice": numeric}},
        "evaluation": {"window_days": 2, "c0": 0.0, "uses": {"topics": [{"lo": "L", "c": 0.5, "m0": [0.4, 0.4]}],
                                                              "dated": []}},
        **({"stop_coin": coin} if coin else {}),
    }


def _row():
    return {"decision_id": "d1", "created_at": "2026-01-01T10:00:00Z", "window_closes_at": "2026-01-03T10:00:00Z",
            "local_date": "2026-01-01", "llm_status": "answered", "numeric_status": "answered", "kappa0": 0.0,
            "remembered_minutes": 10.0}

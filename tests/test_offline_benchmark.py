"""Offline DAS3H-style forgetting benchmark (Checkpoint 5.6): report-only."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from learnloop.sim.offline_benchmarks import build_examples, run_forgetting_benchmark

START = datetime(2026, 5, 1, 12, 0, tzinfo=UTC)


class StubRepository:
    """Duck-typed stand-in: the benchmark reads only attempt history."""

    def __init__(self, attempts_by_lo):
        self._attempts_by_lo = attempts_by_lo

    def learning_object_ids_with_attempts(self):
        return list(self._attempts_by_lo)

    def list_attempts_by_learning_object(self, learning_object_id):
        return list(self._attempts_by_lo.get(learning_object_id, []))


def _attempt(index: int, *, correct: bool, lo: str = "lo_a") -> dict:
    created = START + timedelta(hours=6 * index)
    return {
        "id": f"att_{lo}_{index}",
        "practice_item_id": "pi_x",
        "created_at": created.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "attempt_type": "independent_attempt",
        "correctness": 1.0 if correct else 0.0,
        "error_type": None,
    }


def _forgetting_student(n: int, lo: str) -> list[dict]:
    """Success depends on recent practice density: correct iff the previous
    attempt was within the last 24h — a signal time-window features can learn
    and a static frequency baseline cannot."""

    attempts = []
    for index in range(n):
        # Alternate dense (6h apart) and sparse (60h gap) stretches.
        dense = (index // 5) % 2 == 0
        attempts.append(_attempt(index if dense else index * 10, correct=dense, lo=lo))
    return attempts


def test_examples_use_only_prior_history():
    repository = StubRepository({"lo_a": [_attempt(i, correct=True) for i in range(3)]})
    examples = build_examples(repository)
    assert len(examples) == 3
    # First attempt has an empty history: bias plus all-zero counts.
    assert examples[0].features[0] == 1.0
    assert all(value == 0.0 for value in examples[0].features[1:])
    # Later attempts see growing lifetime counts.
    assert examples[2].features[-2] > examples[1].features[-2]


def test_insufficient_data_is_reported_not_fitted():
    report = run_forgetting_benchmark(StubRepository({"lo_a": [_attempt(0, correct=True)]}))
    assert report["status"] == "insufficient_data"


def test_benchmark_is_deterministic_and_report_only():
    repository = StubRepository({"lo_a": _forgetting_student(60, "lo_a")})
    first = run_forgetting_benchmark(repository)
    second = run_forgetting_benchmark(repository)
    assert first == second  # no RNG anywhere in the fit
    assert first["status"] == "ok"
    assert set(first["results"]) == {
        "das3h_time_windows",
        "baseline_global_rate",
        "baseline_per_lo_rate",
    }
    assert "never replaced automatically" in first["note"]


def test_time_window_model_beats_static_baseline_on_forgetting_data():
    repository = StubRepository(
        {
            "lo_a": _forgetting_student(80, "lo_a"),
        }
    )
    report = run_forgetting_benchmark(repository)
    assert report["status"] == "ok"
    das3h = report["results"]["das3h_time_windows"]["log_loss"]
    static = report["results"]["baseline_per_lo_rate"]["log_loss"]
    assert das3h < static

"""P0.3 micro-benchmark (design §3.3, spec §9.3): a realistic selection decision
(12 candidates x 4 hypotheses x 3 classes x 4 conf buckets, 128 draws) completes
well under the interactive budget. Bound: <100ms; justified fallback <250ms."""

from __future__ import annotations

import time

from learnloop.services import robust_composition as rc


def _alpha() -> dict[str, dict[str, float]]:
    zs = ["s", "p", "o"]
    buckets = {"unknown": 0.05, "low": 0.15, "medium": 0.40, "high": 0.40}
    a: dict[str, dict[str, float]] = {}
    for z in zs:
        row: dict[str, float] = {}
        for g in zs:
            base = 0.8 if g == z else 0.1
            for b, share in buckets.items():
                row[f"{g}|{b}"] = base * share * 40.0
        a[z] = row
    return a


_ROWS = {
    "h1": {"s": 0.7, "p": 0.2, "o": 0.1},
    "h2": {"s": 0.2, "p": 0.6, "o": 0.2},
    "h3": {"s": 0.1, "p": 0.3, "o": 0.6},
    "h4": {"s": 0.34, "p": 0.33, "o": 0.33},
}
_POSTERIOR = {"h1": 0.25, "h2": 0.25, "h3": 0.25, "h4": 0.25}


def _one_selection() -> float:
    alpha = _alpha()
    t0 = time.perf_counter()
    candidates = []
    for i in range(12):
        ctx = rc.decision_context_hash(
            episode_id="e",
            candidate_card_version=f"c{i}",
            resolved_slot_map=None,
            posterior_at_selection=_POSTERIOR,
            projection_algorithm_version="mvp-0.8",
        )
        ens = rc.build_ensemble(
            joint_alpha=alpha,
            instrument_rows=_ROWS,
            calibration_model_hash="mh",
            decision_context_hash=ctx,
        )
        candidates.append((f"c{i}", ens, 45.0))
    rc.evaluate_selection(candidates=candidates, posterior=_POSTERIOR)
    return (time.perf_counter() - t0) * 1000.0


def test_selection_decision_under_budget():
    # Warm up (import/JIT-free but caches allocator), then take the median of runs.
    _one_selection()
    runs = sorted(_one_selection() for _ in range(5))
    median_ms = runs[len(runs) // 2]
    assert median_ms < 250.0, f"selection decision too slow: {median_ms:.1f}ms"

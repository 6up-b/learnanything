"""Store-free, predict-before-observe seam shared by offline evaluation arms.

Prediction inputs deliberately have no outcome. This research protocol is not
the live LearnerPredictor activation contract; Phase 2 can adapt its outcome view
here without importing a repository into an arm.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import asdict
import math
import random
from typing import Iterable, Protocol

from learnloop.offline_outcomes import OutcomeRow, PredictionRow, digest


class LearnerPredictor(Protocol):
    name: str
    version_hash: str
    granularity: str

    def predict(self, row: PredictionRow) -> float: ...
    def observe(self, row: OutcomeRow) -> None: ...


def _metrics(samples: list[tuple[str, float, float]], seed: int = 0) -> dict:
    if not samples:
        return {"count": 0, "log_loss": None, "brier": None, "auc": None,
                "intervals": None, "reliability": []}
    losses = [-y * math.log(p) - (1-y) * math.log1p(-p) for _, p, y in samples]
    briers = [(p-y)**2 for _, p, y in samples]
    clusters: dict[str, list[int]] = defaultdict(list)
    for i, (attempt, _, _) in enumerate(samples):
        clusters[attempt].append(i)
    groups = list(clusters.values())
    rng = random.Random(seed)
    estimates = []
    for _ in range(300):
        indices = [i for _ in groups for i in rng.choice(groups)]
        estimates.append((sum(losses[i] for i in indices)/len(indices),
                          sum(briers[i] for i in indices)/len(indices)))
    intervals = {}
    for column, label in enumerate(("log_loss", "brier")):
        ordered = sorted(pair[column] for pair in estimates)
        intervals[label] = [ordered[7], ordered[292]]
    positives = [p for _, p, y in samples if y == 1]
    negatives = [p for _, p, y in samples if y == 0]
    auc = None
    if positives and negatives and len(positives) + len(negatives) == len(samples):
        auc = sum((p > n) + 0.5 * (p == n) for p in positives for n in negatives) / (
            len(positives) * len(negatives))
    reliability = []
    for bucket in range(10):
        subset = [(p, y) for _, p, y in samples if min(int(p*10), 9) == bucket]
        if subset:
            reliability.append({"bin": bucket, "count": len(subset),
                                "prediction": sum(p for p, _ in subset)/len(subset),
                                "outcome": sum(y for _, y in subset)/len(subset)})
    return {"count": len(samples), "attempt_clusters": len(groups),
            "log_loss": sum(losses)/len(losses), "brier": sum(briers)/len(briers),
            "auc": auc, "intervals": intervals, "reliability": reliability}


def replay(rows: Iterable[OutcomeRow], arms: Iterable[LearnerPredictor], *,
           manifest: dict | None = None) -> dict:
    """Evaluate a frozen snapshot in deterministic time/id order, aggregates only."""
    ordered = sorted(rows, key=lambda r: (r.features.observed_at, r.features.attempt_id))
    predictors = list(arms)
    if len({a.name for a in predictors}) != len(predictors):
        raise ValueError("arm names must be unique")
    ids = [r.features.attempt_id for r in ordered]
    if len(set(ids)) != len(ids):
        raise ValueError("one effective grading epoch per attempt is required")
    samples: dict[str, dict[str, list]] = {a.name: defaultdict(list) for a in predictors}
    excluded: Counter = Counter()
    seen_los: set[str] = set()
    distance_missing = 0
    for row in ordered:
        f = row.features
        reason = row.exclusion
        if reason:
            excluded[reason] += 1
            continue
        if not 0 <= row.outcome <= 1:
            raise ValueError("outcome must be in [0, 1]")
        distance_missing += f.family_id is not None and f.variant_distance is None
        splits = ["overall",
                  "lo_history:" + ("later" if f.lo_id in seen_los else "first"),
                  "origin:" + f.serving_origin, "revision:" + f.revision_status,
                  "topic:" + f.topic, "grader_model:" + f.grader_model,
                  "status:" + f.observation_status,
                  "relation:" + (f.variant_relation or "unfamilied"),
                  "cold:" + str(row.cold).lower()]
        splits += ["family_judge_model:" + model for model in (
            f.family_judge_models or (("authored" if f.family_id else "unfamilied"),)
        )]
        # Predict EVERY arm before ANY arm gets the outcome.
        # Ability reliability is not retrieval eligibility. An uncalibrated
        # grade can train FSRS without becoming invented ability evidence.
        predictions = [(arm, arm.predict(f)) for arm in predictors
                       if f.effective_mass > 0 or getattr(arm, "uses_graded_memory", False)]
        for arm, p in predictions:
            if not math.isfinite(p) or not 0 < p < 1:
                raise ValueError(f"{arm.name}: prediction must be finite and in (0, 1)")
            if hasattr(arm, "scores") and not arm.scores(row):
                continue
            for split in splits:
                samples[arm.name][split].append((f.attempt_id, p, row.outcome))
        for arm, _ in predictions:
            arm.observe(row)
        seen_los.add(f.lo_id)
    return {
        "status": "research_only", "activatable": False,
        "counts": {"input": len(ordered), "excluded": dict(sorted(excluded.items())),
                   "missing_skeleton_distance": distance_missing,
                   "revision": dict(Counter(r.features.revision_status for r in ordered)),
                   "observation_status": dict(Counter(r.features.observation_status for r in ordered)),
                   "zero_ability_mass": sum(r.features.effective_mass <= 0 for r in ordered),
                   "cold": sum(r.cold for r in ordered),
                   "memory_eligible": sum(r.memory_eligible for r in ordered)},
        "manifest": {
            **(manifest or {}), "harness": "pf-a-prequential-v2",
            "data_snapshot": digest([asdict(r) for r in ordered]),
            "arms": {a.name: a.version_hash for a in predictors},
            "ordering": ["observed_at", "attempt_id"],
            "uncertainty": "300 deterministic percentile bootstrap resamples clustered by attempt",
        },
        "arms": {a.name: {k: _metrics(v) for k, v in sorted(samples[a.name].items())}
                 or {"overall": _metrics([])} for a in predictors},
        "limitations": [
            "Research only: no activation, scheduling changes or promotion conclusion.",
            "Historical serving is observational; bootstrap intervals do not remove selection bias.",
            "Memory arms admit uncalibrated graded cold retrievals; ability arms require positive effective mass. Their sample counts can differ.",
            "Current fitted weights may include evaluation outcomes; default arms are the strictly fixed-weight comparison.",
            "Current authored family assignments are a retrospective grouping, not historical family knowledge.",
            "Missing skeleton distances receive no invented discount; compare distance coverage before interpreting this arm.",
        ],
    }

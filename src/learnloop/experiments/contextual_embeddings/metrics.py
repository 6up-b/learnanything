"""E0 metrics (spec §5.2): evidence sets, rankings, agreement, paired intervals.

* **Complete Evidence@k** (primary): 1 when the top-k units, deduplicated by
  original span and offset, cover every required span of at least one
  accepted evidence set; else 0. N/A (None) for an unanswerable question or
  one without an accepted set.
* **Support Recall@k**: the best-covered set's covered share; ties go to the
  lowest set id (fixed rule).
* **Answer Recall@k**: the covered share of the answer spans.
* **nDCG@k**, **MRR** over the final labels (graded gain: required 2,
  helpful 1); **unknown share**: top-k units nobody labelled.
* Coverage of a required span by delivered or ranked text uses offsets: a
  unit covers ``(extraction, span, start, end)`` when it overlaps it fully;
  a delivered cut covers only what it delivered.
* **Cohen's κ** (unweighted, plus linear weights) with the confusion table.
* **Paired bootstrap** clustered by source family (10,000 resamples, fixed
  seed), source-macro and query-weighted estimates, 95% percentile intervals.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
import math
import random
from typing import Any

from learnloop.experiments.contextual_embeddings import pins

SpanRef = tuple[str, str, int, int]


def _covered(required: SpanRef, pieces: Sequence[SpanRef]) -> bool:
    extraction, span, start, end = required
    reached = start
    for piece in sorted(piece for piece in pieces if piece[0] == extraction and piece[1] == span):
        if piece[2] <= reached < piece[3]:
            reached = max(reached, piece[3])
        if reached >= end:
            return True
    return reached >= end


def dedupe(pieces: Sequence[SpanRef]) -> list[SpanRef]:
    """Original spans and offsets once each (merged units never count twice)."""

    return sorted(set(pieces))


def complete_evidence(pieces: Sequence[SpanRef], evidence_sets: Sequence[Sequence[SpanRef]]) -> float | None:
    if not evidence_sets:
        return None
    pieces = dedupe(pieces)
    return 1.0 if any(all(_covered(ref, pieces) for ref in required) for required in evidence_sets) else 0.0


def support_recall(pieces: Sequence[SpanRef], evidence_sets: Sequence[Sequence[SpanRef]]) -> float | None:
    if not evidence_sets:
        return None
    pieces = dedupe(pieces)
    best = None
    for required in evidence_sets:  # in set-id order: the first best wins ties
        if not required:
            continue
        share = sum(1 for ref in required if _covered(ref, pieces)) / len(required)
        if best is None or share > best:
            best = share
    return best


def answer_recall(pieces: Sequence[SpanRef], answer_spans: Sequence[SpanRef]) -> float | None:
    if not answer_spans:
        return None
    pieces = dedupe(pieces)
    return sum(1 for ref in answer_spans if _covered(ref, pieces)) / len(answer_spans)


def ndcg(ranked: Sequence[str], labels: Mapping[str, str], *, k: int = pins.TOP_K) -> float | None:
    gain = {"required": 2.0, "helpful": 1.0}
    gains = [gain.get(labels.get(unit, ""), 0.0) for unit in ranked[:k]]
    ideal = sorted((gain.get(value, 0.0) for value in labels.values()), reverse=True)[:k]
    if not any(ideal):
        return None
    dcg = sum(value / math.log2(index + 2) for index, value in enumerate(gains))
    best = sum(value / math.log2(index + 2) for index, value in enumerate(ideal))
    return dcg / best


def mrr(ranked: Sequence[str], labels: Mapping[str, str], *, k: int = pins.TOP_K) -> float | None:
    relevant = {unit for unit, value in labels.items() if value in ("required", "helpful")}
    if not relevant:
        return None
    for position, unit in enumerate(ranked[:k], start=1):
        if unit in relevant:
            return 1.0 / position
    return 0.0


def unknown_share(ranked: Sequence[str], labels: Mapping[str, str], *, k: int = pins.TOP_K) -> float:
    top = list(ranked[:k])
    return sum(1 for unit in top if unit not in labels) / len(top) if top else 0.0


def cohen_kappa(pairs: Sequence[tuple[str, str]], categories: Sequence[str]) -> dict[str, Any]:
    """Unweighted and linear-weighted κ with the confusion table."""

    index = {category: position for position, category in enumerate(categories)}
    size = len(categories)
    table = [[0] * size for _ in range(size)]
    for first, second in pairs:
        table[index[first]][index[second]] += 1
    total = sum(map(sum, table))
    if not total:
        return {"n": 0, "kappa": None, "weighted_kappa": None, "confusion": table, "categories": list(categories)}
    rows = [sum(row) / total for row in table]
    cols = [sum(table[r][c] for r in range(size)) / total for c in range(size)]
    observed = sum(table[i][i] for i in range(size)) / total
    expected = sum(rows[i] * cols[i] for i in range(size))
    kappa = None if expected >= 1 else (observed - expected) / (1 - expected)
    if size > 1:
        weight = [[1 - abs(i - j) / (size - 1) for j in range(size)] for i in range(size)]
        observed_w = sum(weight[i][j] * table[i][j] / total for i in range(size) for j in range(size))
        expected_w = sum(weight[i][j] * rows[i] * cols[j] for i in range(size) for j in range(size))
        weighted = None if expected_w >= 1 else (observed_w - expected_w) / (1 - expected_w)
    else:
        weighted = None
    return {"n": total, "kappa": None if kappa is None else round(kappa, 4),
            "weighted_kappa": None if weighted is None else round(weighted, 4),
            "observed_agreement": round(observed, 4), "confusion": table, "categories": list(categories)}


def _mean(values: Sequence[float]) -> float | None:
    return sum(values) / len(values) if values else None


def paired_bootstrap(rows: Sequence[Mapping[str, Any]], *, a: str, b: str, cluster: str = "family",
                     resamples: int = pins.BOOTSTRAP_RESAMPLES, seed: int = pins.SEED) -> dict[str, Any]:
    """Paired difference ``b - a`` on rows ``{cluster, a, b}`` with both scored;
    clusters (source families) are resampled with replacement.

    Returns the query-weighted and cluster-macro point estimates and a 95%
    percentile interval of the query-weighted difference."""

    scored = [row for row in rows if row.get(a) is not None and row.get(b) is not None]
    clusters: dict[str, list[float]] = {}
    for row in scored:
        clusters.setdefault(str(row.get(cluster) or "none"), []).append(float(row[b]) - float(row[a]))
    keys = sorted(clusters)
    if not keys:
        return {"n": 0, "clusters": 0, "families": 0, "difference": None, "macro_difference": None, "ci95": None,
                "exploratory": True}
    differences = [value for key in keys for value in clusters[key]]
    point = _mean(differences)
    macro = _mean([_mean(clusters[key]) for key in keys])
    generator = random.Random(seed)
    estimates: list[float] = []
    for _ in range(resamples):
        sample: list[float] = []
        for _cluster in range(len(keys)):
            sample.extend(clusters[keys[generator.randrange(len(keys))]])
        estimates.append(sum(sample) / len(sample))
    estimates.sort()
    low = estimates[int(0.025 * (resamples - 1))]
    high = estimates[int(math.ceil(0.975 * (resamples - 1)))]
    # Independent families: the real clusters of the paired evidence ("none"
    # pools questions without a family and is no independent family).
    families = sum(1 for key in keys if key != "none")
    return {"n": len(differences), "clusters": len(keys), "families": families, "difference": round(point, 6),
            "macro_difference": round(macro, 6), "ci95": [round(low, 6), round(high, 6)],
            "exploratory": families < pins.MIN_INDEPENDENT_FAMILIES}


def latency_summary(values: Sequence[float]) -> dict[str, float | None]:
    ordered = sorted(values)
    if not ordered:
        return {"n": 0, "p50": None, "p95": None}

    def quantile(share: float) -> float:
        position = share * (len(ordered) - 1)
        low, high = math.floor(position), math.ceil(position)
        return ordered[low] + (ordered[high] - ordered[low]) * (position - low)

    return {"n": len(ordered), "p50": round(quantile(0.5), 4), "p95": round(quantile(0.95), 4)}

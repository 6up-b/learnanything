"""Learned rank fusion across embedding spaces (spec_local_contextual_retrieval_v1 §5.2, §9.2).

Functional core: no I/O. The resolver (``source_retrieval.spaces``) and the
replayer (``retrieval_fusion_posteriors``) call it.

**The model.** For consumer ``c`` and query kind ``k``, a signal ``t``
(a validated citation, a result open, a teacher anchor) on a delivered span
``d`` follows a logistic examination-and-relevance model,
``P(t on d) = examined(pos_d) * sigma(sum_s beta_s / (rrf_k + rank_s(d)) + gamma_t)``,
fitted by inverse-propensity weighting (Joachims, Swaminathan and Schnabel
2017): each delivered span's observation is weighted by ``1 / (examined(pos)
* propensity)``. The fusion weights are ``w = max(beta, 0)`` renormalized over
the available lists.

**Priors, each with its basis (no made-up constants, owner 2026-10-24).**

* ``beta`` (global): mean at the CURRENT DEFAULT space (basis ``legacy``:
  full weight on today's default, zero on the others), its scale the
  default-only maximum-likelihood coefficient (``empirical``); covariance the
  unit-information prior (``published``: Kass and Wasserman 1995, a prior
  worth one observation, computed from the data's own Fisher information).
* ``beta`` per context: partial pooling, mean at the global posterior
  (``empirical``), the same unit-information covariance on the context's data.
* ``gamma_t``: mean at the logit of the signal's pooled empirical rate
  (``empirical``), unit-information covariance.
* ``examined(pos)``: seeded at the ``1/pos`` shape (``published``, Joachims et
  al. 2017) and learned only from randomized deliveries (exploration rows),
  each position a Beta posterior worth one pseudo-observation of the seed.
* ``rrf_k``: seeded at ``source_retrieval.rrf_k`` (``legacy``), chosen by the
  Laplace marginal likelihood over an octave grid around the seed.

**Serving (orchestrator scoping 2026-10-24).** With
``embedding.source_space.learned_fusion`` off the served weights are the seed;
the learned ones are only logged. :func:`explore` (its own switch, off by
default) may reorder only spans whose posterior score gap is smaller than its
own posterior standard deviation (the posterior cannot order the pair: a
structural band, unit signal-to-noise), and records each span's propensity.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
import hashlib
import json
import math
from typing import Any

import numpy as np

FIT_VERSION = "fusion-ips-laplace-v1"
SPACE_LISTS = ("qwen", "local:grouped", "local:singleton", "voyage")
SIGNAL_TYPES = ("cited", "opened", "anchored")
GLOBAL = "global"
#: keep (numerical): Newton iterations and the convergence tolerance of the MAP fit.
NEWTON_STEPS = 50
NEWTON_TOLERANCE = 1e-8
#: keep (computation budget): Monte Carlo draws behind an explored delivery's propensities.
PROPENSITY_DRAWS = 256
#: keep (structural): the octave grid of rrf_k multipliers around its seed.
RRF_K_GRID = (0.25, 0.5, 1.0, 2.0, 4.0)

PRIOR_BASIS = {
    "beta_mean": "legacy: full weight on the current default space (embedding.source_space.default), zero on "
                 "the others; its scale the default-only maximum-likelihood coefficient (empirical)",
    "beta_context_mean": "empirical: the global posterior mean (partial pooling)",
    "covariance": "published: unit-information prior (Kass and Wasserman 1995) from the data's own Fisher "
                  "information",
    "gamma_mean": "empirical: logit of each signal's pooled rate",
    "examination": "published: 1/position seed (Joachims, Swaminathan and Schnabel 2017), learned from "
                   "randomized deliveries only, one pseudo-observation of the seed per position",
    "rrf_k": "legacy: source_retrieval.rrf_k, chosen by Laplace marginal likelihood over an octave grid",
}


def seed_weights(default: str, lists: Sequence[str]) -> dict[str, float]:
    return {name: (1.0 if name == default else 0.0) for name in lists}


def feature_row(ranks: Mapping[str, int], lists: Sequence[str], rrf_k: float) -> np.ndarray:
    return np.array([1.0 / (rrf_k + int(ranks[name])) if name in ranks else 0.0 for name in lists])


def examination_seed(position: int) -> float:
    return 1.0 / max(1, int(position))


def _sigmoid(z: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-np.clip(z, -60.0, 60.0)))


def _newton(design: np.ndarray, y: np.ndarray, weights: np.ndarray, mean0: np.ndarray,
            precision0: np.ndarray) -> tuple[np.ndarray, np.ndarray, float]:
    """MAP of a weighted logistic regression under N(mean0, precision0^-1).
    Returns ``(mode, Hessian at the mode, log marginal likelihood by Laplace)``."""

    theta = mean0.copy()
    for _step in range(NEWTON_STEPS):
        p = _sigmoid(design @ theta)
        gradient = design.T @ (weights * (y - p)) - precision0 @ (theta - mean0)
        hessian = design.T @ (design * (weights * p * (1 - p))[:, None]) + precision0
        try:
            step = np.linalg.solve(hessian, gradient)
        except np.linalg.LinAlgError:
            step = np.linalg.lstsq(hessian, gradient, rcond=None)[0]
        theta = theta + step
        if float(np.max(np.abs(step))) < NEWTON_TOLERANCE:
            break
    p = np.clip(_sigmoid(design @ theta), 1e-12, 1 - 1e-12)
    hessian = design.T @ (design * (weights * p * (1 - p))[:, None]) + precision0
    loglik = float(np.sum(weights * (y * np.log(p) + (1 - y) * np.log(1 - p))))
    delta = theta - mean0
    _sign0, logdet0 = np.linalg.slogdet(precision0)
    _sign, logdet = np.linalg.slogdet(hessian)
    evidence = loglik - 0.5 * float(delta @ precision0 @ delta) + 0.5 * (logdet0 - logdet)
    return theta, hessian, evidence


def _unit_information(design: np.ndarray, weights: np.ndarray, at: np.ndarray) -> np.ndarray:
    """The prior precision worth one observation: the average weighted Fisher information at ``at``."""

    p = _sigmoid(design @ at)
    total = float(np.sum(weights)) or 1.0
    information = design.T @ (design * (weights * p * (1 - p))[:, None])
    precision = information / total
    # A list never observed has no information: give it the smallest observed
    # direction's information so the precision stays proper (still one observation).
    diagonal = np.diag(precision)
    floor = float(np.min(diagonal[diagonal > 0])) if np.any(diagonal > 0) else 1.0
    return precision + np.diag(np.where(diagonal > 0, 0.0, floor))


def _logit(rate: float) -> float:
    rate = min(max(rate, 1e-6), 1 - 1e-6)
    return math.log(rate / (1 - rate))


def parse_feedback(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Group feedback rows into queries with their delivered spans and signals."""

    queries: dict[str, dict[str, Any]] = {}
    for row in rows:
        receipt = str(row["receipt_id"])
        entry = queries.setdefault(receipt, {"receipt_id": receipt, "consumer": row["consumer"],
                                             "query_kind": row["query_kind"], "payload": {}, "delivered": {},
                                             "signals": {}})
        if row["event"] == "query":
            entry["payload"] = dict(row.get("payload") or {})
        elif row["event"] == "delivered":
            entry["delivered"][(row["extraction_id"], row["span_id"])] = {
                "position": int(row.get("position") or 1), **dict(row.get("payload") or {})}
        else:
            entry["signals"].setdefault((row["extraction_id"], row["span_id"]), set()).add(str(row["event"]))
    return queries


def _observations(queries: Sequence[Mapping[str, Any]], lists: Sequence[str], rrf_k: float,
                  examination: Mapping[int, float], types: Sequence[str]):
    """Design rows ``[features, one-hot signal type]``, outcomes and IPS weights."""

    rows, ys, ws = [], [], []
    for query in queries:
        for key, delivered in sorted(query["delivered"].items()):
            ranks = {name: rank for name, rank in (delivered.get("space_ranks") or {}).items() if name in lists}
            x = feature_row(ranks, lists, rrf_k)
            position = int(delivered.get("position") or 1)
            examined = examination.get(position, examination_seed(position))
            propensity = float(delivered.get("propensity") or 1.0)
            weight = 1.0 / max(examined * propensity, 1e-6)
            for index, signal in enumerate(types):
                onehot = np.zeros(len(types))
                onehot[index] = 1.0
                rows.append(np.concatenate([x, onehot]))
                ys.append(1.0 if signal in query["signals"].get(key, ()) else 0.0)
                ws.append(weight)
    if not rows:
        return None
    return np.array(rows), np.array(ys), np.array(ws)


def fit_examination(queries: Sequence[Mapping[str, Any]]) -> dict[int, float]:
    """Relative examination by position from randomized (explored) deliveries:
    a Beta posterior per position seeded at ``1/pos`` with one pseudo-observation,
    normalized to position 1."""

    counts: dict[int, list[float]] = {}
    for query in queries:
        if not (query.get("payload") or {}).get("explored"):
            continue
        for key, delivered in query["delivered"].items():
            position = int(delivered.get("position") or 1)
            cell = counts.setdefault(position, [0.0, 0.0])
            cell[0] += 1.0 if query["signals"].get(key) else 0.0
            cell[1] += 1.0
    if not counts:
        return {}
    rates = {position: (hits + examination_seed(position)) / (seen + 1.0) for position, (hits, seen) in counts.items()}
    top = rates.get(1, examination_seed(1))
    return {position: min(1.0, rate / top) if top else examination_seed(position)
            for position, rate in sorted(rates.items())}


def _fit(queries, lists, rrf_k, examination, types, mean0_beta: np.ndarray | None):
    data = _observations(queries, lists, rrf_k, examination, types)
    if data is None:
        return None
    design, y, w = data
    signals = int(np.sum(y))
    rates = [float(np.sum(y[design[:, len(lists) + index] == 1] * w[design[:, len(lists) + index] == 1])
                   / max(np.sum(w[design[:, len(lists) + index] == 1]), 1e-12)) for index in range(len(types))]
    gamma0 = np.array([_logit(rate) for rate in rates])
    beta0 = np.zeros(len(lists)) if mean0_beta is None else np.asarray(mean0_beta, dtype=float)
    mean0 = np.concatenate([beta0, gamma0])
    precision0 = _unit_information(design, w, mean0)
    mode, hessian, evidence = _newton(design, y, w, mean0, precision0)
    covariance = np.linalg.pinv(hessian)
    return {"mode": mode, "covariance": covariance, "evidence": evidence, "observations": int(len(y) // len(types)),
            "signals": signals}


def _default_scale(queries, lists, default, rrf_k, examination, types) -> float:
    """The default-only maximum-likelihood coefficient: the seed's scale (empirical)."""

    if default not in lists:
        return 0.0
    data = _observations(queries, [default], rrf_k, examination, types)
    if data is None:
        return 0.0
    design, y, w = data
    mean0 = np.zeros(design.shape[1])
    mode, _h, _e = _newton(design, y, w, mean0, _unit_information(design, w, mean0))
    return max(0.0, float(mode[0]))


def refit(rows: Sequence[Mapping[str, Any]], *, default: str, rrf_k_seed: float) -> list[dict[str, Any]]:
    """Every context's posterior from the feedback rows (deterministic; replay-safe)."""

    queries = list(parse_feedback(rows).values())
    queries = [query for query in queries if query["delivered"]]
    if not queries:
        return []
    lists = [name for name in SPACE_LISTS
             if any(name in (d.get("space_ranks") or {}) for q in queries for d in q["delivered"].values())]
    if default not in lists:
        lists = [default, *lists] if default in SPACE_LISTS else lists
    types = [signal for signal in SIGNAL_TYPES
             if any(signal in s for q in queries for s in q["signals"].values())] or ["cited"]
    examination = fit_examination(queries)
    fitted_at = max(str(row.get("created_at") or "") for row in rows)
    digest = hashlib.sha256(json.dumps([[row["id"], row["event"]] for row in rows]).encode()).hexdigest()
    best_k, best = rrf_k_seed, None
    for multiplier in RRF_K_GRID:
        k = rrf_k_seed * multiplier
        scale = _default_scale(queries, lists, default, k, examination, types)
        beta0 = np.array([scale if name == default else 0.0 for name in lists])
        fit = _fit(queries, lists, k, examination, types, beta0)
        if fit is not None and (best is None or fit["evidence"] > best[1]["evidence"] + 1e-12):
            best_k, best = k, (beta0, fit)
    if best is None:
        return []
    beta0, global_fit = best
    out = [_row(GLOBAL, GLOBAL, GLOBAL, lists, types, global_fit, examination, best_k, digest, fitted_at)]
    contexts = sorted({(query["consumer"], query["query_kind"]) for query in queries})
    for consumer, kind in contexts:
        subset = [query for query in queries if (query["consumer"], query["query_kind"]) == (consumer, kind)]
        fit = _fit(subset, lists, best_k, examination, types, global_fit["mode"][:len(lists)])
        if fit is not None:
            out.append(_row(f"{consumer}|{kind}", consumer, kind, lists, types, fit, examination, best_k, digest,
                            fitted_at))
    return out


def _row(key, consumer, kind, lists, types, fit, examination, rrf_k, digest, fitted_at) -> dict[str, Any]:
    n = len(lists)
    return {"context_key": key, "consumer": consumer, "query_kind": kind, "lists": list(lists),
            "mean": [round(float(value), 12) for value in fit["mode"][:n]],
            "covariance": [[round(float(value), 12) for value in row[:n]] for row in fit["covariance"][:n]],
            "intercepts": {signal: round(float(fit["mode"][n + index]), 12) for index, signal in enumerate(types)},
            "examination": {str(position): round(value, 12) for position, value in examination.items()},
            "rrf_k": float(rrf_k), "observations": fit["observations"], "signals": fit["signals"],
            "prior_basis": dict(PRIOR_BASIS), "fit_version": FIT_VERSION, "input_digest": digest,
            "fitted_at": fitted_at}


def posterior_for(posteriors: Mapping[str, Mapping[str, Any]], consumer: str, query_kind: str
                  ) -> Mapping[str, Any] | None:
    """The context's posterior, else the consumer-agnostic global one (partial pooling's fallback)."""

    return posteriors.get(f"{consumer}|{query_kind}") or posteriors.get(GLOBAL)


def learned_weights(posterior: Mapping[str, Any] | None, available: Sequence[str]) -> dict[str, float] | None:
    """``max(beta, 0)`` renormalized over ``available`` (None: no posterior, or no positive weight)."""

    if not posterior or not posterior.get("signals"):
        return None
    mean = dict(zip(posterior["lists"], posterior["mean"], strict=True))
    raw = {name: max(0.0, float(mean.get(name, 0.0))) for name in available}
    total = sum(raw.values())
    if total <= 0:
        return None
    return {name: value / total for name, value in raw.items()}


def explore(order: Sequence[str], features: Mapping[str, np.ndarray], posterior: Mapping[str, Any] | None,
            lists: Sequence[str], *, seed: int) -> tuple[list[str], dict[str, Any]]:
    """Reorder only the spans the posterior cannot order (Thompson draw within
    tie bands); returns the new order and each moved span's propensity.

    Two neighbours ``i, j`` of the served order share a band when the posterior
    mean of their score gap is smaller than its posterior standard deviation.
    Without a posterior (no signals yet) nothing moves."""

    info: dict[str, Any] = {"explored": False, "bands": [], "propensities": {}, "seed": seed}
    if not posterior or not posterior.get("signals") or len(order) < 2:
        return list(order), info
    index = [posterior["lists"].index(name) if name in posterior["lists"] else None for name in lists]
    mean_all = np.asarray(posterior["mean"], dtype=float)
    cov_all = np.asarray(posterior["covariance"], dtype=float)
    keep = [position for position, value in enumerate(index) if value is not None]
    picks = [index[position] for position in keep]
    mean = mean_all[picks]
    cov = cov_all[np.ix_(picks, picks)]

    def x(key: str) -> np.ndarray:
        return np.asarray(features[key], dtype=float)[keep]

    bands: list[list[int]] = [[0]]
    for position in range(1, len(order)):
        gap = x(order[position - 1]) - x(order[position])
        spread = math.sqrt(max(float(gap @ cov @ gap), 0.0))
        if spread > 0 and abs(float(gap @ mean)) < spread:
            bands[-1].append(position)
        else:
            bands.append([position])
    bands = [band for band in bands if len(band) > 1]
    if not bands:
        return list(order), info
    rng = np.random.default_rng(seed)

    def reorder(draw: np.ndarray) -> list[str]:
        result = list(order)
        for band in bands:
            members = [order[position] for position in band]
            ranked = sorted(members, key=lambda key: (-float(x(key) @ draw), members.index(key)))
            for position, key in zip(band, ranked, strict=True):
                result[position] = key
        return result

    served = reorder(rng.multivariate_normal(mean, cov, method="svd"))
    hits = {key: 0 for band in bands for key in (order[position] for position in band)}
    for _draw in range(PROPENSITY_DRAWS):
        candidate = reorder(rng.multivariate_normal(mean, cov, method="svd"))
        for key in hits:
            if candidate.index(key) == served.index(key):
                hits[key] += 1
    info.update(explored=True, bands=[[order[position] for position in band] for band in bands],
                propensities={key: round(max(count, 1) / PROPENSITY_DRAWS, 6) for key, count in hits.items()})
    return served, info


def rng_seed(receipt_id: str) -> int:
    """The draw's seed, keyed by the query receipt (a replay is reproducible)."""

    return int(hashlib.sha256(receipt_id.encode("utf-8")).hexdigest()[:8], 16)


__all__ = ["FIT_VERSION", "GLOBAL", "PRIOR_BASIS", "SIGNAL_TYPES", "SPACE_LISTS", "examination_seed", "explore",
           "feature_row", "fit_examination", "learned_weights", "parse_feedback", "posterior_for", "refit",
           "rng_seed", "seed_weights"]

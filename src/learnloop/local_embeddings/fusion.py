"""Learned rank fusion across embedding spaces (spec_local_contextual_retrieval_v1 §5.2, §9.2).

Functional core: no I/O. The resolver (``source_retrieval.spaces``), the
delivery recorder (``source_retrieval.feedback``) and the replayer
(``retrieval_fusion_posteriors``) call it.

**Lists are identities, not names (Codex review F12).** A list is
``<name>@<space id>`` (plus ``#<query encoder id>`` for a local space), so a
re-indexed local space under a new software epoch, a new hosted model or a
new query encoder is a NEW list: it never inherits the coefficients learned
for another geometry, and starts from its own declared prior (§10).

**The model (Codex review F8).** For consumer ``c`` and query kind ``k``, a
signal ``t`` (a validated citation, a result open, a teacher anchor) on a
delivered span ``d`` follows the examination-and-relevance likelihood

``P(t on d) = examined(pos_d) * sigma(sum_s beta_s / (rrf_k + rank_s(d)) + gamma_t)``

fitted as written (Fisher scoring on that likelihood: a low-examination
position gives fewer signals for equally relevant spans, and the fit
expects exactly that instead of learning position as relevance). The
randomized-delivery correction is inverse-propensity weighting by the
logged propensities only (Joachims, Swaminathan and Schnabel 2017): the
joint probability that the resolver's policy, applied to the Thompson draw,
selected exactly the lists it queried (:func:`selection_propensity`, under
the posterior's covariance, forced stand-ins included; Codex re-review F18),
times the exploration propensity of the span's final position.

**Serving (§5.2, Codex review F7, F14).** With
``embedding.source_space.learned_fusion`` on, the served weights are a
Thompson draw from the posterior (seeded by the query receipt), and the
probability of the selection it led to (and each list's) is logged. A list
that was available but never queried keeps its prior, so a challenger at
zero mean is still drawn positive sometimes, queried, observed, and can
learn its way up. The posterior's own ``rrf_k`` serves with its
coefficients. Off (the default) the seed serves at the configured ``rrf_k``;
the learned weights are only logged.

**Priors, each with its basis (no made-up constants, owner 2026-10-24).**

* ``beta`` (global): mean at the CURRENT DEFAULT space (basis ``legacy``:
  full weight on today's default, zero on the others), its scale the
  default-only maximum-likelihood coefficient (``empirical``); covariance the
  unit-information prior (``published``: Kass and Wasserman 1995, a prior
  worth one observation, computed from the data's own Fisher information).
* ``beta`` per context: partial pooling, mean at the global posterior
  (``empirical``), the same unit-information covariance on the context's data.
* ``gamma_t``: mean at the logit of the signal's pooled rate over the mean
  examination (``empirical``), unit-information covariance.
* ``examined(pos)``: seeded at the ``1/pos`` shape (``published``, Joachims et
  al. 2017) and learned only from randomized deliveries (exploration rows),
  each position a Beta posterior worth one pseudo-observation of the seed.
* ``rrf_k``: seeded at ``source_retrieval.rrf_k`` (``legacy``), chosen by the
  Laplace marginal likelihood over an octave grid around the seed.
* A list the posterior has never had available: mean 0, the widest marginal
  variance the posterior holds (``structural``: never surer of a list than
  of any list it has seen).

:func:`explore` (its own switch, off by default) may reorder only spans whose
posterior score gap is smaller than its own posterior standard deviation (the
posterior cannot order the pair: a structural band, unit signal-to-noise),
and records each span's propensity; it runs at each consumer's delivery
boundary, so the propensity describes the delivered position (Codex review F9).
"""
from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
import hashlib
import json
import math
from typing import Any

import numpy as np

FIT_VERSION = "fusion-examination-ips-laplace-v2"
SPACE_LISTS = ("qwen", "local:grouped", "local:singleton", "voyage")
SIGNAL_TYPES = ("cited", "opened", "anchored")
GLOBAL = "global"
#: keep (numerical): Fisher-scoring iterations and the convergence tolerance of the MAP fit.
NEWTON_STEPS = 50
NEWTON_TOLERANCE = 1e-8
#: keep (computation budget): Monte Carlo draws behind an explored delivery's propensities.
PROPENSITY_DRAWS = 256
#: keep (structural): the octave grid of rrf_k multipliers around its seed.
RRF_K_GRID = (0.25, 0.5, 1.0, 2.0, 4.0)
#: keep (numerical): the smallest propensity an inverse-propensity weight divides by.
MIN_PROPENSITY = 1e-6
#: keep (computation budget): Monte Carlo draws behind a query's selection probability
#: (standard error at most 0.5 / sqrt(draws), under 0.008).
SELECTION_DRAWS = 4096

PRIOR_BASIS = {
    "beta_mean": "legacy: full weight on the current default space (embedding.source_space.default), zero on "
                 "the others; its scale the default-only maximum-likelihood coefficient (empirical)",
    "beta_context_mean": "empirical: the global posterior mean (partial pooling)",
    "covariance": "published: unit-information prior (Kass and Wasserman 1995) from the data's own Fisher "
                  "information",
    "gamma_mean": "empirical: logit of each signal's pooled rate over the mean examination",
    "examination": "published: 1/position seed (Joachims, Swaminathan and Schnabel 2017), learned from "
                   "randomized deliveries only, one pseudo-observation of the seed per position",
    "rrf_k": "legacy: source_retrieval.rrf_k, chosen by Laplace marginal likelihood over an octave grid",
    "unseen_list": "structural: a list never available to the fit is drawn at mean 0 with the widest marginal "
                   "variance the posterior holds",
    "lists": "identity: <name>@<space id>[#<query encoder id>]; a new space or encoder is a new list that "
             "starts from its own prior (spec §10)",
}


def list_key(name: str, space_id: str | None = None, encoder_id: str | None = None) -> str:
    """A list's immutable identity: its name, its space id, and (for a local
    space) its query encoder id (Codex review F12)."""

    key = f"{name}@{space_id}" if space_id else name
    return f"{key}#{encoder_id}" if encoder_id else key


def list_name(key: str) -> str:
    return str(key).split("@", 1)[0].split("#", 1)[0]


def _order(keys: Sequence[str]) -> list[str]:
    rank = {name: index for index, name in enumerate(SPACE_LISTS)}
    return sorted(set(keys), key=lambda key: (rank.get(list_name(key), len(rank)), key))


def seed_weights(default: str, lists: Sequence[str]) -> dict[str, float]:
    return {name: (1.0 if list_name(name) == default else 0.0) for name in lists}


def feature_row(ranks: Mapping[str, int], lists: Sequence[str], rrf_k: float) -> np.ndarray:
    return np.array([1.0 / (rrf_k + int(ranks[name])) if name in ranks else 0.0 for name in lists])


def examination_seed(position: int) -> float:
    return 1.0 / max(1, int(position))


def _sigmoid(z: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-np.clip(z, -60.0, 60.0)))


def _probabilities(design: np.ndarray, theta: np.ndarray, examined: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """``(p, dp/dz)`` of the examination-and-relevance likelihood ``p = e * sigma(z)``."""

    sigma = _sigmoid(design @ theta)
    p = np.clip(examined * sigma, 1e-12, 1 - 1e-12)
    return p, examined * sigma * (1 - sigma)


def _information(design: np.ndarray, weights: np.ndarray, p: np.ndarray, dp: np.ndarray) -> np.ndarray:
    return design.T @ (design * (weights * dp * dp / (p * (1 - p)))[:, None])


def _map_fit(design: np.ndarray, y: np.ndarray, weights: np.ndarray, examined: np.ndarray, mean0: np.ndarray,
             precision0: np.ndarray) -> tuple[np.ndarray, np.ndarray, float]:
    """MAP of ``P(y = 1) = e * sigma(x . theta)`` under N(mean0, precision0^-1),
    by Fisher scoring (IRLS for a non-canonical link). Returns ``(mode,
    information at the mode, log marginal likelihood by Laplace)``."""

    def objective(value: np.ndarray) -> float:
        p, _dp = _probabilities(design, value, examined)
        delta = value - mean0
        return float(np.sum(weights * (y * np.log(p) + (1 - y) * np.log(1 - p)))) - 0.5 * float(
            delta @ precision0 @ delta)

    theta = mean0.copy()
    current = objective(theta)
    for _step in range(NEWTON_STEPS):
        p, dp = _probabilities(design, theta, examined)
        gradient = design.T @ (weights * (y - p) * dp / (p * (1 - p))) - precision0 @ (theta - mean0)
        information = _information(design, weights, p, dp) + precision0
        try:
            step = np.linalg.solve(information, gradient)
        except np.linalg.LinAlgError:
            step = np.linalg.lstsq(information, gradient, rcond=None)[0]
        # Step halving keeps every iterate an ascent of the log posterior (the
        # non-canonical link's scoring step can overshoot near saturation).
        for _halving in range(NEWTON_STEPS):
            candidate = theta + step
            value = objective(candidate)
            if value >= current - 1e-12 or float(np.max(np.abs(step))) < NEWTON_TOLERANCE:
                break
            step = step / 2.0
        theta, current = candidate, max(value, current)
        if float(np.max(np.abs(step))) < NEWTON_TOLERANCE:
            break
    p, dp = _probabilities(design, theta, examined)
    information = _information(design, weights, p, dp) + precision0
    loglik = float(np.sum(weights * (y * np.log(p) + (1 - y) * np.log(1 - p))))
    delta = theta - mean0
    _sign0, logdet0 = np.linalg.slogdet(precision0)
    _sign, logdet = np.linalg.slogdet(information)
    # A degenerate (signal-free) context has a singular information; its
    # Occam term is then undefined and left out rather than made NaN.
    occam = logdet0 - logdet if np.isfinite(logdet0) and np.isfinite(logdet) else 0.0
    evidence = loglik - 0.5 * float(delta @ precision0 @ delta) + 0.5 * occam
    return theta, information, evidence


def _unit_information(design: np.ndarray, weights: np.ndarray, examined: np.ndarray, at: np.ndarray) -> np.ndarray:
    """The prior precision worth one observation: the average weighted Fisher information at ``at``."""

    p, dp = _probabilities(design, at, examined)
    total = float(np.sum(weights)) or 1.0
    precision = _information(design, weights, p, dp) / total
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


def _set_propensity(payload: Mapping[str, Any], lists: Sequence[str], ranked: set[str]) -> float:
    """The logged probability that the resolver's policy selected the set of
    lists this search queried (:func:`selection_propensity`, recorded at
    serve time; Codex re-review F18), consumed as recorded; 1 under the seed,
    whose selection is not random."""

    del lists, ranked  # the joint probability is recorded whole, never rebuilt from marginals
    value = payload.get("query_set_propensity")
    return 1.0 if value is None else float(value)


def _observations(queries: Sequence[Mapping[str, Any]], lists: Sequence[str], rrf_k: float,
                  examination: Mapping[int, float], types: Sequence[str]):
    """Design rows ``[features, one-hot signal type]``, outcomes, IPS weights and examination."""

    rows, ys, ws, es = [], [], [], []
    for query in queries:
        payload = query.get("payload") or {}
        ranked = {name for delivered in query["delivered"].values() for name in (delivered.get("space_ranks") or {})}
        set_propensity = _set_propensity(payload, lists, ranked)
        for key, delivered in sorted(query["delivered"].items()):
            ranks = {name: rank for name, rank in (delivered.get("space_ranks") or {}).items() if name in lists}
            x = feature_row(ranks, lists, rrf_k)
            position = int(delivered.get("position") or 1)
            examined = examination.get(position, examination_seed(position))
            propensity = float(delivered.get("propensity") or 1.0)
            weight = 1.0 / max(set_propensity * propensity, MIN_PROPENSITY)
            for index, signal in enumerate(types):
                onehot = np.zeros(len(types))
                onehot[index] = 1.0
                rows.append(np.concatenate([x, onehot]))
                ys.append(1.0 if signal in query["signals"].get(key, ()) else 0.0)
                ws.append(weight)
                es.append(examined)
    if not rows:
        return None
    return np.array(rows), np.array(ys), np.array(ws), np.array(es)


def _explored(query: Mapping[str, Any], delivered: Mapping[str, Any]) -> bool:
    return bool(delivered.get("explored") or (query.get("payload") or {}).get("explored"))


def fit_examination(queries: Sequence[Mapping[str, Any]]) -> dict[int, float]:
    """Relative examination by position from randomized (explored) deliveries:
    a Beta posterior per position seeded at ``1/pos`` with one pseudo-observation,
    normalized to position 1."""

    counts: dict[int, list[float]] = {}
    for query in queries:
        for key, delivered in query["delivered"].items():
            if not _explored(query, delivered):
                continue
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


def fit_context(queries, lists, rrf_k, examination, types, mean0_beta: np.ndarray | None):
    """One context's MAP fit under the examination-and-relevance likelihood (or None without data)."""

    data = _observations(queries, lists, rrf_k, examination, types)
    if data is None:
        return None
    design, y, w, e = data
    signals = int(np.sum(y))
    mean_examined = float(np.sum(w * e) / max(float(np.sum(w)), 1e-12))
    rates = [float(np.sum(y[design[:, len(lists) + index] == 1] * w[design[:, len(lists) + index] == 1])
                   / max(np.sum(w[design[:, len(lists) + index] == 1]), 1e-12)) for index in range(len(types))]
    gamma0 = np.array([_logit(rate / max(mean_examined, 1e-12)) for rate in rates])
    beta0 = np.zeros(len(lists)) if mean0_beta is None else np.asarray(mean0_beta, dtype=float)
    mean0 = np.concatenate([beta0, gamma0])
    precision0 = _unit_information(design, w, e, mean0)
    mode, information, evidence = _map_fit(design, y, w, e, mean0, precision0)
    covariance = np.linalg.pinv(information)
    return {"mode": mode, "covariance": covariance, "evidence": evidence, "observations": int(len(y) // len(types)),
            "signals": signals}


def _default_scale(queries, default_key, rrf_k, examination, types) -> float:
    """The default-only maximum-likelihood coefficient: the seed's scale (empirical)."""

    data = _observations(queries, [default_key], rrf_k, examination, types)
    if data is None:
        return 0.0
    design, y, w, e = data
    mean0 = np.zeros(design.shape[1])
    mode, _i, _e = _map_fit(design, y, w, e, mean0, _unit_information(design, w, e, mean0))
    return max(0.0, float(mode[0]))


def refit(rows: Sequence[Mapping[str, Any]], *, default: str, rrf_k_seed: float) -> list[dict[str, Any]]:
    """Every context's posterior from the feedback rows (deterministic; replay-safe)."""

    queries = list(parse_feedback(rows).values())
    queries = [query for query in queries if query["delivered"]]
    if not queries:
        return []
    seen = [name for q in queries for d in q["delivered"].values() for name in (d.get("space_ranks") or {})]
    seen += [name for q in queries for name in ((q.get("payload") or {}).get("lists_available") or ())]
    lists = _order(seen)
    if not any(list_name(name) == default for name in lists) and default in SPACE_LISTS:
        lists = _order([default, *lists])
    types = [signal for signal in SIGNAL_TYPES
             if any(signal in s for q in queries for s in q["signals"].values())] or ["cited"]
    examination = fit_examination(queries)
    fitted_at = max(str(row.get("created_at") or "") for row in rows)
    digest = hashlib.sha256(json.dumps([[row["id"], row["event"]] for row in rows]).encode()).hexdigest()
    best_k, best = rrf_k_seed, None
    for multiplier in RRF_K_GRID:
        k = rrf_k_seed * multiplier
        beta0 = np.array([_default_scale(queries, name, k, examination, types) if list_name(name) == default else 0.0
                          for name in lists])
        fit = fit_context(queries, lists, k, examination, types, beta0)
        if fit is not None and (best is None or fit["evidence"] > best[1]["evidence"] + 1e-12):
            best_k, best = k, (beta0, fit)
    if best is None:
        return []
    beta0, global_fit = best
    out = [_row(GLOBAL, GLOBAL, GLOBAL, lists, types, global_fit, examination, best_k, digest, fitted_at)]
    contexts = sorted({(query["consumer"], query["query_kind"]) for query in queries})
    for consumer, kind in contexts:
        subset = [query for query in queries if (query["consumer"], query["query_kind"]) == (consumer, kind)]
        fit = fit_context(subset, lists, best_k, examination, types, global_fit["mode"][:len(lists)])
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


def _marginals(posterior: Mapping[str, Any], keys: Sequence[str]) -> tuple[np.ndarray, np.ndarray]:
    """Mean and covariance over ``keys``; a key the posterior lacks gets mean 0
    and the widest marginal variance it holds (``unseen_list``)."""

    lists = list(posterior.get("lists") or ())
    mean_all = np.asarray(posterior.get("mean") or [], dtype=float)
    cov_all = np.asarray(posterior.get("covariance") or [], dtype=float).reshape(len(lists), len(lists))
    widest = float(np.max(np.diag(cov_all))) if len(lists) else 1.0
    mean = np.zeros(len(keys))
    cov = np.zeros((len(keys), len(keys)))
    for i, a in enumerate(keys):
        if a in lists:
            mean[i] = mean_all[lists.index(a)]
        for j, b in enumerate(keys):
            if a in lists and b in lists:
                cov[i, j] = cov_all[lists.index(a), lists.index(b)]
            elif i == j:
                cov[i, j] = widest
    return mean, cov


def learned_weights(posterior: Mapping[str, Any] | None, available: Sequence[str]) -> dict[str, float] | None:
    """The posterior mean's ``max(beta, 0)`` renormalized over ``available`` (logged; None: no posterior or no
    positive weight)."""

    if not posterior or not posterior.get("signals"):
        return None
    mean, _cov = _marginals(posterior, list(available))
    raw = {name: max(0.0, float(value)) for name, value in zip(available, mean, strict=True)}
    total = sum(raw.values())
    if total <= 0:
        return None
    return {name: value / total for name, value in raw.items()}


def thompson_weights(posterior: Mapping[str, Any] | None, available: Sequence[str], *, seed: int
                     ) -> dict[str, float] | None:
    """A Thompson draw of the weights (§5.2): ``max(beta, 0)`` of one posterior
    draw, renormalized over ``available``. None without a posterior (the seed
    serves). The probability of what the draw selects is
    :func:`selection_propensity`'s: it depends on the resolver's policy, not
    on the draw alone."""

    if not posterior or not posterior.get("signals") or not available:
        return None
    keys = list(available)
    mean, cov = _marginals(posterior, keys)
    draw = np.random.default_rng(seed).multivariate_normal(mean, cov, method="svd")
    raw = {name: max(0.0, float(value)) for name, value in zip(keys, draw, strict=True)}
    total = sum(raw.values())
    return {name: (value / total if total > 0 else 0.0) for name, value in raw.items()}


def selection_propensity(posterior: Mapping[str, Any] | None, available: Sequence[str],
                         policy: Callable[[frozenset[str]], frozenset[str]], chosen: frozenset[str], *,
                         seed: int) -> tuple[float, dict[str, float]]:
    """The probability that the resolver's selection ``policy``, applied to a
    Thompson draw from ``posterior`` over ``available``, selects exactly
    ``chosen``, and each list's probability of being selected (Codex
    re-review F18).

    ``policy`` maps the set of lists drawn positive to the set the resolver
    queries (its coverage assignment, the forced cheapest stand-in included);
    a draw's selection depends only on which coefficients are positive. The
    probability is joint, under the posterior's own covariance, estimated by
    ``SELECTION_DRAWS`` draws (seeded, so a replay logs the same number) with
    the served draw counted as one of them, so a selection that happened is
    never given probability 0. ``(1.0, {})`` without a posterior: the seed's
    selection is not random."""

    if not posterior or not posterior.get("signals") or not available:
        return 1.0, {}
    keys = list(available)
    mean, cov = _marginals(posterior, keys)
    draws = np.random.default_rng(seed).multivariate_normal(mean, cov, size=SELECTION_DRAWS, method="svd")
    patterns, counts = np.unique(draws > 0, axis=0, return_counts=True)
    hits = 1
    selected = {name: (1 if name in chosen else 0) for name in keys}
    for pattern, count in zip(patterns, counts, strict=True):
        picked = policy(frozenset(name for name, positive in zip(keys, pattern, strict=True) if positive))
        if picked == chosen:
            hits += int(count)
        for name in picked:
            if name in selected:
                selected[name] += int(count)
    total = SELECTION_DRAWS + 1
    return round(hits / total, 9), {name: round(value / total, 9) for name, value in selected.items()}


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
    mean, cov = _marginals(posterior, list(lists))

    def x(key: str) -> np.ndarray:
        return np.asarray(features[key], dtype=float)

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


def refit_posteriors(vault: Any, repository: Any) -> dict[str, Any]:
    """Recompute ``retrieval_fusion_posteriors`` from every feedback row, in
    order (the replayer's body, ``learnloop embeddings fusion refit`` and the
    ingest host's background refresh)."""

    from learnloop.db.stores.retrieval_spaces import feedback_rows, has_tables, replace_fusion_posteriors

    with repository.connection() as connection:
        if not has_tables(connection):
            return {"written": 0, "rows": 0}
        rows = feedback_rows(connection)
        fitted = refit(rows, default=vault.config.embedding.source_space.default,
                       rrf_k_seed=float(vault.config.source_retrieval.rrf_k))
        written = replace_fusion_posteriors(connection, fitted)
    return {"written": written, "rows": len(rows), "contexts": [row["context_key"] for row in fitted],
            "signals": sum(int(row["signals"]) for row in fitted if row["context_key"] == GLOBAL)}


def rng_seed(receipt_id: str) -> int:
    """The draw's seed, keyed by the query receipt (a replay is reproducible)."""

    return int(hashlib.sha256(receipt_id.encode("utf-8")).hexdigest()[:8], 16)


__all__ = ["FIT_VERSION", "GLOBAL", "PRIOR_BASIS", "SIGNAL_TYPES", "SPACE_LISTS", "examination_seed", "explore",
           "feature_row", "fit_context", "fit_examination", "learned_weights", "list_key", "list_name",
           "parse_feedback", "posterior_for", "refit", "refit_posteriors", "rng_seed", "seed_weights",
           "selection_propensity", "thompson_weights"]

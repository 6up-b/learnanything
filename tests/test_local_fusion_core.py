"""Local contextual retrieval P1: the fusion core (learned weights, seeded priors, exploration band)."""
from __future__ import annotations

import numpy as np

from learnloop.local_embeddings import fusion


def _feedback(receipts: int, *, cited_list: str, rng: np.random.Generator, explored: bool = False) -> list[dict]:
    """Synthetic searches over two lists; the citation falls on ``cited_list``'s top span."""

    rows = []
    for index in range(receipts):
        receipt = f"rq_{index:04d}"
        rows.append({"id": f"{receipt}_q", "receipt_id": receipt, "event": "query", "consumer": "tutor",
                     "query_kind": "lookup", "extraction_id": None, "span_id": None, "position": None,
                     "payload": {"explored": explored}, "created_at": f"2026-10-24T00:{index // 60:02d}:{index % 60:02d}"})
        spans = [("e", f"a{index}"), ("e", f"b{index}"), ("e", f"c{index}")]
        ranks = {spans[0]: {"qwen": 1, "voyage": 3}, spans[1]: {"qwen": 3, "voyage": 1}, spans[2]: {"qwen": 2, "voyage": 2}}
        for position, key in enumerate(spans, start=1):
            rows.append({"id": f"{receipt}_d{position}", "receipt_id": receipt, "event": "delivered", "consumer": "tutor",
                         "query_kind": "lookup", "extraction_id": key[0], "span_id": key[1], "position": position,
                         "payload": {"space_ranks": ranks[key]}, "created_at": rows[0]["created_at"]})
        best = spans[0] if cited_list == "qwen" else spans[1]
        if rng.random() < 0.8:
            rows.append({"id": f"{receipt}_c", "receipt_id": receipt, "event": "cited", "consumer": "tutor",
                         "query_kind": "lookup", "extraction_id": best[0], "span_id": best[1], "position": None,
                         "payload": {}, "created_at": rows[0]["created_at"]})
    return rows


def test_no_feedback_means_the_seed():
    assert fusion.refit([], default="qwen", rrf_k_seed=60.0) == []
    assert fusion.seed_weights("qwen", fusion.SPACE_LISTS) == {"qwen": 1.0, "local:grouped": 0.0,
                                                                "local:singleton": 0.0, "voyage": 0.0}
    assert fusion.learned_weights(None, ["qwen", "voyage"]) is None


def test_signals_move_the_learned_weights_toward_the_list_that_finds_what_is_cited():
    rows = _feedback(120, cited_list="voyage", rng=np.random.default_rng(1))
    fitted = {row["context_key"]: row for row in fusion.refit(rows, default="qwen", rrf_k_seed=60.0)}
    assert set(fitted) == {"global", "tutor|lookup"}
    weights = fusion.learned_weights(fitted["tutor|lookup"], ["qwen", "voyage"])
    assert weights is not None and weights["voyage"] > weights["qwen"]
    # Every prior names its basis (owner, 2026-10-24: no made-up constants).
    assert set(fitted["global"]["prior_basis"]) >= {"beta_mean", "covariance", "gamma_mean", "examination", "rrf_k"}
    assert fitted["global"]["rrf_k"] in {60.0 * m for m in fusion.RRF_K_GRID}


def test_the_refit_is_deterministic_and_replay_safe():
    rows = _feedback(40, cited_list="qwen", rng=np.random.default_rng(7))
    first = fusion.refit(rows, default="qwen", rrf_k_seed=60.0)
    second = fusion.refit(list(rows), default="qwen", rrf_k_seed=60.0)
    assert first == second
    assert first[0]["fitted_at"] == max(row["created_at"] for row in rows)


def test_examination_is_learned_only_from_randomized_deliveries():
    plain = fusion.parse_feedback(_feedback(20, cited_list="qwen", rng=np.random.default_rng(3)))
    assert fusion.fit_examination(list(plain.values())) == {}
    explored = fusion.parse_feedback(_feedback(20, cited_list="qwen", rng=np.random.default_rng(3), explored=True))
    curve = fusion.fit_examination(list(explored.values()))
    assert curve[1] == 1.0 and all(0 < value <= 1.0 for value in curve.values())


def test_exploration_moves_nothing_without_a_posterior_and_only_inside_the_tie_band():
    order = ["e/a", "e/b", "e/c"]
    features = {"e/a": np.array([1 / 61, 0, 0, 1 / 63]), "e/b": np.array([1 / 62, 0, 0, 1 / 62]),
                "e/c": np.array([1 / 63, 0, 0, 1 / 61])}
    same, info = fusion.explore(order, features, None, list(fusion.SPACE_LISTS), seed=1)
    assert same == order and not info["explored"]
    # A posterior sure of the order: no band.
    certain = {"lists": list(fusion.SPACE_LISTS), "mean": [100.0, 0.0, 0.0, 0.0], "signals": 5,
               "covariance": np.diag([1e-6, 1e-6, 1e-6, 1e-6]).tolist()}
    kept, info = fusion.explore(order, features, certain, list(fusion.SPACE_LISTS), seed=1)
    assert kept == order and not info["explored"]
    # A posterior that cannot order them: the band holds all three, propensities logged.
    unsure = {"lists": list(fusion.SPACE_LISTS), "mean": [1.0, 0.0, 0.0, 1.0], "signals": 5,
              "covariance": np.diag([4e4, 1e-6, 1e-6, 4e4]).tolist()}
    moved, info = fusion.explore(order, features, unsure, list(fusion.SPACE_LISTS), seed=1)
    assert info["explored"] and sorted(moved) == sorted(order)
    assert set(info["propensities"]) == set(order) and all(0 < p <= 1 for p in info["propensities"].values())
    again, _ = fusion.explore(order, features, unsure, list(fusion.SPACE_LISTS), seed=1)
    assert again == moved  # seeded by the receipt: reproducible


def _position_biased(queries: int, *, beta, gamma, rng) -> list[dict]:
    """Searches whose deliveries follow ``examined(pos) = 1/pos`` times
    ``sigma(beta . x + gamma)``, with relevance that does NOT depend on position
    (each span's list ranks are drawn independently of where it is shown)."""

    rows = []
    for index in range(queries):
        receipt = f"rq_{index:05d}"
        stamp = f"2026-10-24T{index // 3600 % 24:02d}:{index // 60 % 60:02d}:{index % 60:02d}"
        rows.append({"id": f"{receipt}_q", "receipt_id": receipt, "event": "query", "consumer": "library",
                     "query_kind": "lookup", "extraction_id": None, "span_id": None, "position": None,
                     "payload": {}, "created_at": stamp})
        for position in range(1, 7):
            ranks = {"qwen": int(rng.integers(1, 7)), "voyage": int(rng.integers(1, 7))}
            x = np.array([1.0 / (1.0 + ranks["qwen"]), 1.0 / (1.0 + ranks["voyage"])])
            relevant = 1.0 / (1.0 + np.exp(-(x @ beta + gamma)))
            key = ("e", f"{receipt}_{position}")
            rows.append({"id": f"{receipt}_d{position}", "receipt_id": receipt, "event": "delivered",
                         "consumer": "library", "query_kind": "lookup", "extraction_id": key[0], "span_id": key[1],
                         "position": position, "payload": {"space_ranks": ranks}, "created_at": stamp})
            if rng.random() < (1.0 / position) * relevant:
                rows.append({"id": f"{receipt}_o{position}", "receipt_id": receipt, "event": "opened",
                             "consumer": "library", "query_kind": "lookup", "extraction_id": key[0],
                             "span_id": key[1], "position": position, "payload": {}, "created_at": stamp})
    return rows


def test_the_fit_recovers_relevance_under_a_known_position_bias():
    """Codex review F8: with examination 1/pos, the declared likelihood
    ``e * sigma(x . beta + gamma)`` recovers beta and gamma; the old
    1/e-weighted logistic fit, which learns position bias as relevance, does not."""

    beta, gamma = np.array([6.0, 2.0]), -1.0
    rows = _position_biased(6000, beta=beta, gamma=gamma, rng=np.random.default_rng(2))
    queries = list(fusion.parse_feedback(rows).values())
    fit = fusion.fit_context(queries, ["qwen", "voyage"], 1.0, {}, ["opened"], np.zeros(2))
    estimate = fit["mode"]
    errors = np.sqrt(np.diag(fit["covariance"]))
    assert abs(estimate[0] - beta[0]) < 3 * errors[0] and abs(estimate[1] - beta[1]) < 3 * errors[1], (estimate, errors)
    assert abs(estimate[2] - gamma) < 3 * errors[2]
    # The old weighting (both outcomes times 1/examined under sigma alone) is biased here.
    x = np.array([[1.0 / (1.0 + d["space_ranks"]["qwen"]), 1.0 / (1.0 + d["space_ranks"]["voyage"]), 1.0]
                  for q in queries for d in q["delivered"].values()])
    y = np.array([1.0 if q["signals"].get(k) else 0.0 for q in queries for k in q["delivered"]])
    w = np.array([float(d["position"]) for q in queries for d in q["delivered"].values()])
    theta = np.zeros(3)
    for _ in range(50):
        p = 1.0 / (1.0 + np.exp(-(x @ theta)))
        theta += np.linalg.solve(x.T @ (x * (w * p * (1 - p))[:, None]), x.T @ (w * (y - p)))
    assert abs(theta[2] - gamma) > 3 * errors[2]

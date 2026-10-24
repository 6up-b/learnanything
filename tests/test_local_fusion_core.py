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

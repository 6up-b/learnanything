"""Diversity scores for PF-b selection (Slice 2 §5.4 "Selection"); pure functions.

Survivors are ordered by maximal marginal relevance against administered history
and each other, weighted by verifier strength, and the set's Vendi score is
reported. The kernel here is lexical (word and bigram Jaccard with numbers
masked, so a number swap counts as near-identical surface). It is the basis
until B2 sets embedding blocking cutoffs; the report names the basis used. For
ensemble families these scores are input to the selection judge, which picks;
for generator families MMR order selects directly. Nothing here decides
correctness or identity.
"""
from __future__ import annotations

import math
import re
import unicodedata
from typing import Sequence

import numpy as np

DIVERSITY_BASIS = "lexical_jaccard_v1"
MMR_LAMBDA = 0.7
_WORD = re.compile(r"[a-z]+|\d+(?:\.\d+)?|[^\sa-z\d]")


def tokens(text: str) -> frozenset[str]:
    words = ["#" if word[0].isdigit() else word
             for word in _WORD.findall(unicodedata.normalize("NFKC", text).casefold())]
    return frozenset(words) | frozenset(f"{a} {b}" for a, b in zip(words, words[1:]))


def similarity(left: str, right: str) -> float:
    a, b = tokens(left), tokens(right)
    if not a and not b:
        return 1.0
    return len(a & b) / len(a | b)


def kernel(texts: Sequence[str]) -> np.ndarray:
    size = len(texts)
    matrix = np.eye(size)
    for i in range(size):
        for j in range(i + 1, size):
            matrix[i, j] = matrix[j, i] = similarity(texts[i], texts[j])
    return matrix


def vendi_score(texts: Sequence[str]) -> float:
    """exp(Shannon entropy of the eigenvalues of K/n): the effective number of distinct items."""
    if not texts:
        return 0.0
    eigenvalues = np.linalg.eigvalsh(kernel(texts) / len(texts))
    positive = [value for value in eigenvalues if value > 1e-12]
    return float(math.exp(-sum(value * math.log(value) for value in positive)))


def vendi_contributions(texts: Sequence[str]) -> list[float]:
    """Leave-one-out drop in the set's Vendi score for each member."""
    total = vendi_score(texts)
    return [round(total - vendi_score([t for j, t in enumerate(texts) if j != i]), 6)
            for i in range(len(texts))]


def mmr_order(candidates: Sequence[tuple[str, float, str]], history: Sequence[str],
              *, lambda_: float = MMR_LAMBDA) -> list[dict[str, float | str]]:
    """Greedy MMR over ``(ref, relevance, text)`` against history and picks so far."""
    remaining = list(candidates)
    picked: list[tuple[str, float, str]] = []
    order: list[dict[str, float | str]] = []
    while remaining:
        best = None
        for ref, relevance, text in remaining:
            others = [other for other in history] + [item[2] for item in picked]
            redundancy = max((similarity(text, other) for other in others), default=0.0)
            score = lambda_ * relevance - (1.0 - lambda_) * redundancy
            key = (score, relevance, ref)
            if best is None or key > best[0]:
                best = (key, ref, relevance, text, redundancy, score)
        _, ref, relevance, text, redundancy, score = best
        remaining = [item for item in remaining if item[0] != ref]
        picked.append((ref, relevance, text))
        order.append({"ref": ref, "mmr_score": round(score, 6),
                      "max_similarity": round(redundancy, 6), "relevance": round(relevance, 6)})
    return order


__all__ = ["DIVERSITY_BASIS", "MMR_LAMBDA", "kernel", "mmr_order", "similarity", "tokens",
           "vendi_contributions", "vendi_score"]

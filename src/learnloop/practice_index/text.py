"""Keyword search and rank fusion for the practice index (no model calls).

Okapi BM25 with the standard k1 = 1.2, b = 0.75, and reciprocal-rank fusion
(Cormack, Clarke and Buettcher, SIGIR 2009). Fusion uses ranks only, so no
cosine or BM25 score threshold is ever hand-set (Slice 2 R4).
"""
from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
import math
import re
import unicodedata


_TOKEN = re.compile(r"[a-z0-9]+")
_STOPWORDS = frozenset("""
a an and are as at be by can do does for from give how i in into is it its me
my of on or practice question questions some that the this to want what when
where which with you your
""".split())


def tokenize(text: str) -> list[str]:
    """Lowercased alphanumeric tokens, stopwords removed, plural 's' folded."""
    normalized = unicodedata.normalize("NFKC", text or "").lower()
    tokens = []
    for token in _TOKEN.findall(normalized):
        if token in _STOPWORDS:
            continue
        if len(token) > 3 and token.endswith("s") and not token.endswith("ss"):
            token = token[:-1]
        tokens.append(token)
    return tokens


class BM25:
    """Okapi BM25 over a fixed document collection."""

    def __init__(self, documents: Mapping[str, str], *, k1: float = 1.2, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self._terms = {doc_id: Counter(tokenize(text)) for doc_id, text in documents.items()}
        self._lengths = {doc_id: sum(terms.values()) for doc_id, terms in self._terms.items()}
        count = len(self._terms)
        self._average = (sum(self._lengths.values()) / count) if count else 0.0
        frequency: Counter[str] = Counter()
        for terms in self._terms.values():
            frequency.update(terms.keys())
        # BM25+-style non-negative IDF (Lucene's form): log(1 + (N - n + 0.5)/(n + 0.5)).
        self._idf = {
            term: math.log(1.0 + (count - n + 0.5) / (n + 0.5)) for term, n in frequency.items()
        }

    def scores(self, query: str, candidates: Iterable[str] | None = None) -> dict[str, float]:
        """Positive scores only; documents sharing no query term are omitted."""
        query_terms = Counter(tokenize(query))
        ids = self._terms.keys() if candidates is None else [
            doc_id for doc_id in candidates if doc_id in self._terms
        ]
        result: dict[str, float] = {}
        for doc_id in ids:
            terms = self._terms[doc_id]
            length = self._lengths[doc_id]
            norm = self.k1 * (1 - self.b + self.b * (length / self._average if self._average else 0.0))
            score = 0.0
            for term, query_count in query_terms.items():
                tf = terms.get(term, 0)
                if tf:
                    score += query_count * self._idf.get(term, 0.0) * tf * (self.k1 + 1) / (tf + norm)
            if score > 0:
                result[doc_id] = score
        return result

    def ranking(self, query: str, candidates: Iterable[str] | None = None) -> list[str]:
        scores = self.scores(query, candidates)
        return sorted(scores, key=lambda doc_id: (-scores[doc_id], doc_id))


def reciprocal_rank_fusion(rankings: Mapping[str, Sequence[str]], *,
                           k: int = 60) -> tuple[list[str], dict[str, dict[str, int]]]:
    """Fuse ranked lists; returns the fused order and each id's per-list rank.

    An id absent from a list contributes nothing for it. Ties break by id.
    """
    scores: dict[str, float] = {}
    ranks: dict[str, dict[str, int]] = {}
    for name, ranking in sorted(rankings.items()):
        for position, doc_id in enumerate(ranking, start=1):
            scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (k + position)
            ranks.setdefault(doc_id, {})[name] = position
    order = sorted(scores, key=lambda doc_id: (-scores[doc_id], doc_id))
    return order, ranks


__all__ = ["BM25", "reciprocal_rank_fusion", "tokenize"]

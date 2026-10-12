"""Embeddings shortlist candidate pairs; they never decide (Slice 2 R1, R4).

For each query subject, rank the pool subjects that pass the kind's structured
filter (applied BEFORE ranking, as Slice 1 §9.4 requires) by mean-centred
cosine over the vectors already stored for the kind's embedding identity, keep
the top ``k`` and, when a benchmark has set one for this model, drop those
below the blocking cutoff. Pairs the caller says are already settled are
skipped before ranking, so the judge's budget goes to undecided pairs.

The score only chooses which pairs a judge sees. Nothing here merges,
rejects or skips a judge by score, and a model without a benchmark-set
cutoff is blocked by top-k alone (cutoffs are never hand-set in code). A
cutoff applies only to vectors of the identity it was measured on (model,
width, text recipe, task prefix); any other is refused and top-k alone blocks.

**Which model ranks** (Slice 1 §9.6: retrieval switches only once the new
model's backfill is complete). The configured model ranks once its current
vectors cover every subject that any other stored model covers. Until then a
replacement is pending: the previous model with the most current vectors
keeps ranking (subjects it never embedded, such as new ones, can then be
neither query nor candidate, so they link by exact statement and validated
citation only), and the replacement's partial index is never ranked. Partial
coverage of the ranking model is allowed and reported.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
import sqlite3
from typing import Any

import numpy as np

from learnloop.matching.kinds import MatchKind, Subject


@dataclass(frozen=True)
class CandidatePair:
    left: Subject
    right: Subject
    score: float
    rank: int
    model_id: str
    basis: str = "knn"


@dataclass
class Shortlist:
    pairs: list[CandidatePair] = field(default_factory=list)
    model_id: str | None = None
    top_k: int = 0
    cutoff: float | None = None
    queries: int = 0
    queries_without_vector: int = 0
    pool_with_vector: int = 0
    below_cutoff: int = 0
    skipped_settled: int = 0
    #: Why the cutoff is or is not applied (``benchmark`` | ``top_k_only`` |
    #: ``refused_incompatible``) and which model ranks and why.
    cutoff_basis: str | None = None
    cutoff_refusal: str | None = None
    activation: dict[str, Any] | None = None

    def summary(self) -> dict[str, Any]:
        return {
            "model_id": self.model_id,
            "top_k": self.top_k,
            "cutoff": self.cutoff,
            "cutoff_basis": self.cutoff_basis or ("benchmark" if self.cutoff is not None else "top_k_only"),
            "cutoff_refusal": self.cutoff_refusal,
            "model_activation": self.activation,
            "queries": self.queries,
            "queries_without_vector": self.queries_without_vector,
            "pool_with_vector": self.pool_with_vector,
            "pairs": len(self.pairs),
            "below_cutoff": self.below_cutoff,
            "skipped_settled": self.skipped_settled,
        }


@dataclass(frozen=True)
class ModelActivation:
    """Which stored model ranks a kind's subjects, and why (Slice 1 §9.6)."""

    configured: str
    ranking: str | None
    status: str  # active | replacement_pending | no_vectors
    population: int
    coverage: Mapping[str, int]

    def summary(self) -> dict[str, Any]:
        return {
            "configured_model": self.configured,
            "ranking_model": self.ranking,
            "status": self.status,
            "subjects": self.population,
            "current_vectors_by_model": dict(self.coverage),
        }


def active_model(
    connection: sqlite3.Connection, kind: MatchKind, subjects: Sequence[Subject], *, configured: str
) -> ModelActivation:
    """The configured model once its backfill covers what the others cover, else the previous one."""

    # Imported here: CLI start-up must not load the numpy-backed vector store.
    from learnloop.db.stores.embedding_vectors import current_records_by_model

    expected = {subject.id: subject.content_hash for subject in subjects}
    coverage = current_records_by_model(
        connection, record_kind=kind.record_kind, field=kind.field, task_prefix=kind.task_prefix,
        expected_records=expected,
    ) if expected else {}
    own = coverage.get(configured, frozenset())
    others = {model: ids for model, ids in coverage.items() if model != configured and ids}
    counts = {model: len(ids) for model, ids in coverage.items()}
    if all(ids <= own for ids in others.values()):
        if not own:
            return ModelActivation(configured, None, "no_vectors", len(expected), counts)
        return ModelActivation(configured, configured, "active", len(expected), counts)
    previous = min(others, key=lambda model: (-len(others[model]), model))
    return ModelActivation(configured, previous, "replacement_pending", len(expected), counts)


def stored_width(connection: sqlite3.Connection, kind: MatchKind, *, model_id: str) -> int | None:
    """The width of a model's stored vectors for this kind (one per model)."""

    rows = connection.execute(
        "SELECT DISTINCT dims FROM embedding_vectors WHERE record_kind = ? AND field = ? AND model_id = ? "
        "AND task_prefix = ?",
        (kind.record_kind, kind.field, model_id, kind.task_prefix),
    ).fetchall()
    widths = {int(row[0]) for row in rows}
    return widths.pop() if len(widths) == 1 else None


def compatible_cutoff(
    entry: Any, kind: MatchKind, *, model_id: str, dims: int | None
) -> tuple[float | None, str, str | None]:
    """(cutoff, basis, refusal) for a configured benchmark cutoff entry.

    ``entry`` carries ``cutoff``, ``dims``, ``recipe`` and ``task_prefix``: the
    identity of the vectors the benchmark measured. A cutoff measured on
    another width, recipe or prefix describes another cosine distribution, so
    it is refused (and top-k alone blocks) instead of silently applied.
    """

    if entry is None:
        return None, "top_k_only", None
    problems = []
    if dims is None or int(getattr(entry, "dims", 0) or 0) != int(dims):
        problems.append(f"measured at {getattr(entry, 'dims', None)} dimensions, stored vectors are {dims}")
    if str(getattr(entry, "recipe", "") or "") != kind.recipe:
        problems.append(f"measured on recipe {getattr(entry, 'recipe', None)!r}, this kind embeds {kind.recipe!r}")
    if str(getattr(entry, "task_prefix", "") or "") != kind.task_prefix:
        problems.append(f"measured with prefix {getattr(entry, 'task_prefix', None)!r}, vectors use {kind.task_prefix!r}")
    if problems:
        return None, "refused_incompatible", f"{model_id}: " + "; ".join(problems)
    return float(entry.cutoff), "benchmark", None


def stored_vectors(
    connection: sqlite3.Connection,
    kind: MatchKind,
    subjects: Sequence[Subject],
    *,
    model_id: str,
) -> dict[str, np.ndarray]:
    """Current vectors (content hash matches) for these subjects, by subject id."""

    wanted = {subject.id: subject.content_hash for subject in subjects}
    if not wanted:
        return {}
    rows = connection.execute(
        "SELECT record_id, content_hash, vector FROM embedding_vectors "
        "WHERE record_kind = ? AND field = ? AND model_id = ? AND task_prefix = ?",
        (kind.record_kind, kind.field, model_id, kind.task_prefix),
    ).fetchall()
    vectors: dict[str, np.ndarray] = {}
    for record_id, content_hash, blob in rows:
        if wanted.get(str(record_id)) == content_hash:
            vectors[str(record_id)] = np.frombuffer(blob, dtype="<f2").astype(np.float64)
    return vectors


def centred_unit(vectors: Mapping[str, np.ndarray]) -> dict[str, np.ndarray]:
    """Mean-centred, unit-length rows over the given set (Slice 1 §9.2)."""

    if not vectors:
        return {}
    ids = sorted(vectors)
    widths = {vectors[key].size for key in ids}
    if len(widths) != 1:
        raise ValueError("stored vectors of one model have different widths")
    matrix = np.stack([vectors[key] for key in ids])
    centred = matrix - matrix.mean(axis=0)
    norms = np.linalg.norm(centred, axis=1, keepdims=True)
    unit = np.divide(centred, norms, out=np.zeros_like(centred), where=norms != 0)
    return {key: unit[index] for index, key in enumerate(ids)}


def shortlist_pairs(
    connection: sqlite3.Connection,
    kind: MatchKind,
    *,
    queries: Sequence[Subject],
    pool: Sequence[Subject],
    model_id: str,
    top_k: int,
    cutoff: float | None,
    compatible: Callable[[Subject, Subject], bool],
    settled: Callable[[Subject, Subject], bool] | None = None,
    centre_over: Sequence[Subject] | None = None,
) -> Shortlist:
    """Top-k compatible, unsettled pool neighbours of each query.

    ``centre_over`` names the population whose mean is removed (default:
    queries plus pool); it should be every current subject of the kind, so a
    small query batch is centred like the whole vault.
    """

    if top_k < 1:
        raise ValueError("top_k must be at least 1")
    population = {subject.id: subject for subject in (centre_over or [*queries, *pool])}
    for subject in (*queries, *pool):
        population.setdefault(subject.id, subject)
    unit = centred_unit(stored_vectors(connection, kind, list(population.values()), model_id=model_id))
    result = Shortlist(model_id=model_id, top_k=top_k, cutoff=cutoff, queries=len(queries))
    pool_with_vector = [subject for subject in pool if subject.id in unit]
    result.pool_with_vector = len(pool_with_vector)
    for query in queries:
        vector = unit.get(query.id)
        if vector is None:
            result.queries_without_vector += 1
            continue
        scored: list[tuple[float, str, Subject]] = []
        for candidate in pool_with_vector:
            if candidate.id == query.id or not compatible(query, candidate):
                continue
            if settled is not None and settled(query, candidate):
                result.skipped_settled += 1
                continue
            scored.append((float(vector @ unit[candidate.id]), candidate.id, candidate))
        scored.sort(key=lambda row: (-row[0], row[1]))
        for rank, (score, _id, candidate) in enumerate(scored[:top_k], start=1):
            if cutoff is not None and score < cutoff:
                result.below_cutoff += 1
                continue
            result.pairs.append(
                CandidatePair(left=query, right=candidate, score=round(score, 6), rank=rank, model_id=model_id)
            )
    return result


__all__ = [
    "CandidatePair",
    "ModelActivation",
    "Shortlist",
    "active_model",
    "centred_unit",
    "compatible_cutoff",
    "shortlist_pairs",
    "stored_vectors",
    "stored_width",
]

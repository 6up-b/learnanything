"""Vault-local paid vectors and exact retrieval; callers supply current identity.

Vectors are sensitive persisted inputs, not projections. No provider is called
here. Retrieval requires the complete current manifest for this record kind and
field, so a changed model cannot silently serve a partially backfilled index.
"""
from __future__ import annotations

from collections.abc import Collection, Mapping, Sequence
from contextlib import closing
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import sqlite3
from uuid import uuid4

import numpy as np

from learnloop.db.connection import connect


class IncompleteEmbeddingIndex(ValueError):
    """The requested model has not embedded the complete current manifest."""


@dataclass(frozen=True)
class EmbeddingMatch:
    record_id: str
    content_hash: str
    score: float


def _vector(value: Sequence[float] | np.ndarray) -> np.ndarray:
    array = np.asarray(value, dtype=np.float64)
    if array.ndim != 1 or not array.size or not np.isfinite(array).all():
        raise ValueError("vector must be a nonempty finite one-dimensional array")
    if np.any(np.abs(array) > np.finfo(np.float16).max):
        raise ValueError("vector exceeds float16 range")
    return array


def _unit_rows(matrix: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    return np.divide(matrix, norms, out=np.zeros_like(matrix), where=norms != 0)


def get_vector(connection: sqlite3.Connection, *, record_kind: str, record_id: str,
               field: str, content_hash: str, model_id: str, task_prefix: str) -> np.ndarray | None:
    row = connection.execute(
        "SELECT vector FROM embedding_vectors WHERE record_kind=? AND record_id=? "
        "AND field=? AND content_hash=? AND model_id=? AND task_prefix=?",
        (record_kind, record_id, field, content_hash, model_id, task_prefix),
    ).fetchone()
    return None if row is None else np.frombuffer(row[0], dtype="<f2").astype(np.float64)


def put_vector(connection: sqlite3.Connection, *, record_kind: str, record_id: str,
               field: str, content_hash: str, model_id: str, task_prefix: str,
               vector: Sequence[float] | np.ndarray, created_at: str | None = None) -> str:
    """Insert once by full identity, preserving the first paid result."""
    array = _vector(vector).astype("<f2")
    identity = (record_kind, record_id, field, content_hash, model_id, task_prefix)
    connection.execute(
        "INSERT INTO embedding_vectors "
        "(id,record_kind,record_id,field,content_hash,model_id,task_prefix,dims,vector,created_at) "
        "VALUES (?,?,?,?,?,?,?,?,?,?) "
        "ON CONFLICT(record_kind,record_id,field,model_id,task_prefix,content_hash) DO NOTHING",
        (str(uuid4()), *identity, array.size, array.tobytes(),
         created_at or datetime.now(timezone.utc).isoformat()),
    )
    row = connection.execute(
        "SELECT id FROM embedding_vectors WHERE record_kind=? AND record_id=? "
        "AND field=? AND content_hash=? AND model_id=? AND task_prefix=?", identity,
    ).fetchone()
    assert row is not None
    return str(row[0])


def retrieve(connection: sqlite3.Connection, *, record_kind: str, field: str,
             model_id: str, task_prefix: str, query: Sequence[float] | np.ndarray,
             expected_records: Mapping[str, str], limit: int = 10,
             candidate_ids: Collection[str] | None = None,
             dimensions: int | None = None) -> list[EmbeddingMatch]:
    """Mean-centered cosine over current vectors; exact filters precede ranking.

    The caller supplies ALL current records for this scope, not just candidates.
    Old revisions and other models/prefixes/fields never enter its centroid.
    Zero centered vectors score zero; ties are deterministic by record ID.
    Without dimensions, query and stored dimensions must match. With dimensions,
    both are truncated to that positive prefix length BEFORE centering/ranking;
    a view narrower than storage then L2-normalizes rows and query, as MRL
    requires and as the client does when it truncates at write time, so a view
    ranks like vectors embedded at that width. Callers may pass a full or
    already-truncated query; each vector must have at least dimensions
    elements. Storage retains one full dimension per model.
    """
    if limit < 0:
        raise ValueError("limit must be nonnegative")
    q = _vector(query)
    if dimensions is not None:
        if isinstance(dimensions, bool) or not isinstance(dimensions, int) or dimensions <= 0:
            raise ValueError("dimensions must be a positive integer")
        if dimensions > q.size:
            raise ValueError("requested dimensions exceed query dimension")
    rows = connection.execute(
        "SELECT record_id,content_hash,dims,vector FROM embedding_vectors "
        "WHERE record_kind=? AND field=? AND model_id=? AND task_prefix=?",
        (record_kind, field, model_id, task_prefix),
    ).fetchall()
    current = {str(row[0]): row for row in rows
               if expected_records.get(str(row[0])) == row[1]}
    missing = set(expected_records) - current.keys()
    if missing:
        raise IncompleteEmbeddingIndex(f"{len(missing)} current records missing for {model_id}")
    if not current:
        return []
    ids = sorted(current)
    if dimensions is None:
        if any(current[key][2] != q.size for key in ids):
            raise ValueError("query dimension does not match model")
    elif any(current[key][2] < dimensions for key in ids):
        raise ValueError("requested dimensions exceed stored model dimension")
    matrix = np.stack([np.frombuffer(current[key][3], dtype="<f2").astype(np.float64)
                       for key in ids])
    if dimensions is not None:
        q = q[:dimensions]
        if matrix.shape[1] > dimensions:
            matrix = _unit_rows(matrix[:, :dimensions])
            q = _unit_rows(q[np.newaxis, :])[0]
    mean = matrix.mean(axis=0)
    centered = matrix - mean
    centered_query = q - mean
    denominator = np.linalg.norm(centered, axis=1) * np.linalg.norm(centered_query)
    scores = np.divide(centered @ centered_query, denominator,
                       out=np.zeros(len(ids)), where=denominator != 0)
    candidates = None if candidate_ids is None else set(candidate_ids)
    matches = [EmbeddingMatch(key, expected_records[key], float(scores[index]))
               for index, key in enumerate(ids) if candidates is None or key in candidates]
    return sorted(matches, key=lambda match: (-match.score, match.record_id))[:limit]


class EmbeddingVectorStore:
    """Short transactions for jobs; use module functions for atomic batches."""

    def __init__(self, sqlite_path: Path):
        self.sqlite_path = sqlite_path

    def get(self, **identity) -> np.ndarray | None:
        with closing(connect(self.sqlite_path, read_only=True)) as connection:
            return get_vector(connection, **identity)

    get_vector = get

    def contains(self, **identity) -> bool:
        return self.get(**identity) is not None

    def put(self, **values) -> str:
        with closing(connect(self.sqlite_path)) as connection, connection:
            return put_vector(connection, **values)

    def retrieve(self, **query) -> list[EmbeddingMatch]:
        with closing(connect(self.sqlite_path, read_only=True)) as connection:
            return retrieve(connection, **query)


def nearest_among_current(connection: sqlite3.Connection, *, record_kind: str, field: str,
                          model_id: str, task_prefix: str,
                          expected_records: Mapping[str, str],
                          limit: int) -> dict[str, list[EmbeddingMatch]]:
    """Each current record's top ``limit`` neighbours among the other current ones.

    The same mean-centred cosine as ``retrieve``, for every pair at once. Unlike
    ``retrieve``, partial coverage is allowed: only records of
    ``expected_records`` whose stored vector has the current content hash take
    part, as sources and as candidates, and only they appear as keys. The
    centroid is theirs alone. Callers must label that coverage. This ranks for
    display or context and never decides anything (Slice 2 R1). Ties go to the
    smaller record ID; a zero centred vector scores zero against everything.
    """
    if limit < 0:
        raise ValueError("limit must be nonnegative")
    rows = connection.execute(
        "SELECT record_id,content_hash,vector FROM embedding_vectors "
        "WHERE record_kind=? AND field=? AND model_id=? AND task_prefix=?",
        (record_kind, field, model_id, task_prefix),
    ).fetchall()
    current = {str(row[0]): row[2] for row in rows
               if expected_records.get(str(row[0])) == row[1]}
    ids = sorted(current)
    if len(ids) < 2 or limit == 0:
        return {key: [] for key in ids}
    matrix = np.stack([np.frombuffer(current[key], dtype="<f2").astype(np.float64)
                       for key in ids])
    unit = _unit_rows(matrix - matrix.mean(axis=0))
    neighbours: dict[str, list[EmbeddingMatch]] = {}
    block = 256  # bounds the score matrix held at once
    for start in range(0, len(ids), block):
        scores = unit[start:start + block] @ unit.T
        for offset, row in enumerate(scores):
            index = start + offset
            ranked = row.copy()
            ranked[index] = -np.inf  # never its own neighbour
            # Stable sort keeps sorted-ID order among equal scores.
            order = np.argsort(-ranked, kind="stable")[:min(limit, len(ids) - 1)]
            neighbours[ids[index]] = [
                EmbeddingMatch(ids[j], expected_records[ids[j]], float(row[j])) for j in order
            ]
    return neighbours

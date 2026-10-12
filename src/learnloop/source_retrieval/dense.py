"""Dense retrieval over stored ``source_block/text`` vectors (no provider call).

The Phase 1 rules hold: a scope is searched densely only when every embeddable
block in it has a vector for ``embedding.model`` (by its own identity or by an
identical recipe text stored under another record), so a partially backfilled
or half-switched index never ranks silently. Scores are the Phase 1
mean-centred cosine (``db.stores.embedding_vectors.retrieve``): the centroid is
the whole scope's, exclusions are applied after centring like
``candidate_ids``, ties go to the smaller record id. A test pins the ranking and
scores to ``retrieve()``.

The centred, row-normalized matrix of a scope is cached per process (keyed by
database, model and the scope's manifest digest), so a long-lived sidecar
reads the vectors once per index state rather than per query.
"""
from __future__ import annotations

from collections import OrderedDict
from collections.abc import Callable, Mapping
from contextlib import closing
from dataclasses import dataclass, field
from pathlib import Path
from threading import Lock
from typing import Any

import numpy as np

from learnloop.ai.execution import content_key
from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.source_retrieval.corpus import Scope
from learnloop.source_retrieval.recipes import (
    DOC_TASK_PREFIX,
    SOURCE_BLOCK_FIELD,
    SOURCE_BLOCK_KIND,
    scope_manifest,
    split_record_id,
)
from learnloop.vault.models import LoadedVault


@dataclass
class DenseIndex:
    status: str
    reason: str | None = None
    model_id: str | None = None
    expected: int = 0
    covered: int = 0
    ids: list[str] = field(default_factory=list)
    mean: np.ndarray | None = None
    unit: np.ndarray | None = None

    @property
    def ready(self) -> bool:
        return self.status == "ready"

    def describe(self) -> dict[str, Any]:
        return {"status": self.status, "reason": self.reason, "model_id": self.model_id,
                "expected": self.expected, "covered": self.covered}

    def rank(self, query: np.ndarray, *, limit: int,
             allow: Callable[[str], bool] | None = None) -> list[tuple[str, float]]:
        """``(record_id, score)`` best first; ``allow`` filters after centring."""

        if not self.ready or self.unit is None or self.mean is None or limit <= 0:
            return []
        q = np.asarray(query, dtype=np.float64)
        if q.ndim != 1 or q.size != self.mean.size:
            raise ValueError("query dimension does not match the index")
        centered = q - self.mean
        norm = np.linalg.norm(centered)
        if norm == 0 or not np.isfinite(norm):
            scores = np.zeros(len(self.ids))
        else:
            scores = self.unit.astype(np.float64) @ (centered / norm)
        order = sorted(range(len(self.ids)), key=lambda index: (-scores[index], self.ids[index]))
        ranked: list[tuple[str, float]] = []
        for index in order:
            record_id = self.ids[index]
            if allow is not None and not allow(record_id):
                continue
            ranked.append((record_id, float(scores[index])))
            if len(ranked) >= limit:
                break
        return ranked


_CACHE: OrderedDict[tuple[str, str, str], DenseIndex] = OrderedDict()
_CACHE_LOCK = Lock()
_CACHE_SIZE = 4


def clear_cache() -> None:
    with _CACHE_LOCK:
        _CACHE.clear()


def _stored(connection, *, model_id: str, extraction_ids: list[str],
            manifest: Mapping[str, str]) -> dict[str, bytes]:
    """The current vector blob per manifest record: by identity, else by content."""

    found: dict[str, bytes] = {}
    if not connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'embedding_vectors'"
    ).fetchone():
        return found
    for extraction_id in extraction_ids:
        for record_id, content_hash, blob in connection.execute(
            "SELECT record_id, content_hash, vector FROM embedding_vectors "
            "WHERE record_kind = ? AND field = ? AND model_id = ? AND task_prefix = ? "
            "AND record_id >= ? AND record_id < ? ORDER BY created_at, id",
            (SOURCE_BLOCK_KIND, SOURCE_BLOCK_FIELD, model_id, DOC_TASK_PREFIX,
             f"{extraction_id}/", f"{extraction_id}0"),
        ):
            key = str(record_id)
            if manifest.get(key) == content_hash and key not in found:
                found[key] = blob
    missing: dict[str, list[str]] = {}
    for key, content_hash in manifest.items():
        if key not in found:
            missing.setdefault(content_hash, []).append(key)
    hashes = sorted(missing)
    for start in range(0, len(hashes), 500):
        chunk = hashes[start:start + 500]
        for content_hash, blob in connection.execute(
            "SELECT content_hash, vector FROM embedding_vectors WHERE record_kind = ? AND field = ? "
            "AND model_id = ? AND task_prefix = ? AND content_hash IN "
            f"({', '.join('?' for _ in chunk)}) ORDER BY created_at, id",
            (SOURCE_BLOCK_KIND, SOURCE_BLOCK_FIELD, model_id, DOC_TASK_PREFIX, *chunk),
        ):
            for key in missing.get(str(content_hash), ()):
                found.setdefault(key, blob)
    return found


def load_dense_index(vault: LoadedVault, repository: Repository, scope: Scope) -> DenseIndex:
    """The scope's dense index, or a labelled reason it cannot be used."""

    config = vault.config
    if not config.source_retrieval.dense:
        return DenseIndex("disabled", "source_retrieval.dense is false")
    model_id = config.embedding.model
    sqlite_path = Path(repository.sqlite_path)
    extraction_ids = sorted(scope.extractions)
    with closing(connect(sqlite_path, read_only=True)) as connection:
        manifest = scope_manifest(connection, sqlite_path, extraction_ids)
        if not manifest:
            return DenseIndex("empty", "no embeddable block in scope", model_id)
        key = (str(sqlite_path), model_id, content_key(sorted(manifest.items())))
        with _CACHE_LOCK:
            cached = _CACHE.get(key)
            if cached is not None:
                _CACHE.move_to_end(key)
                return cached
        found = _stored(connection, model_id=model_id, extraction_ids=extraction_ids, manifest=manifest)
    if len(found) < len(manifest):
        return DenseIndex(
            "incomplete",
            f"{len(manifest) - len(found)} of {len(manifest)} blocks in scope have no "
            f"{model_id} vector; run `learnloop embeddings backfill --record-kind source_block`",
            model_id, expected=len(manifest), covered=len(found))
    ids = sorted(manifest)
    widths = {len(found[key]) for key in ids}
    if len(widths) != 1:
        return DenseIndex("unavailable", "stored vectors have mixed widths", model_id,
                          expected=len(manifest), covered=len(found))
    matrix = np.stack([np.frombuffer(found[key], dtype="<f2").astype(np.float64) for key in ids])
    mean = matrix.mean(axis=0)
    centered = matrix - mean
    norms = np.linalg.norm(centered, axis=1, keepdims=True)
    unit = np.divide(centered, norms, out=np.zeros_like(centered), where=norms != 0).astype(np.float32)
    index = DenseIndex("ready", None, model_id, expected=len(manifest), covered=len(found),
                       ids=ids, mean=mean, unit=unit)
    with _CACHE_LOCK:
        _CACHE[key] = index
        while len(_CACHE) > _CACHE_SIZE:
            _CACHE.popitem(last=False)
    return index


def record_keys(record_id: str) -> tuple[str, str]:
    return split_record_id(record_id)


__all__ = ["DenseIndex", "clear_cache", "load_dense_index", "record_keys"]

"""Dense retrieval over stored ``source_block/text`` vectors (no provider call).

Coverage is decided per extraction. An extraction is searched densely only when
every embeddable block in it has a vector for ``embedding.model`` (by its own
identity or by an identical recipe text stored under another record): a
half-embedded source never ranks by meaning. The index covers the complete
extractions of the scope:

* ``ready``: every extraction in scope is complete;
* ``partial``: some are; the others are left to keyword search, and the status
  says how many blocks and sources are not covered (a new import or a
  re-extraction never switches meaning search off for the whole library);
* ``incomplete``: none is (run the source-block backfill);
* ``disabled`` / ``empty`` / ``unavailable``: switched off, nothing to embed,
  or mixed vector widths.

Scores are the Phase 1 mean-centred cosine (``db.stores.embedding_vectors.
retrieve``) over the covered blocks: the centroid is theirs, exclusions are
applied after centring like ``candidate_ids``, ties go to the smaller record
id. A test pins a complete scope's ranking and scores to ``retrieve()``.

Coverage (no vector bytes read) and the centred, row-normalized matrix are
cached per process, keyed by database, model, the scope's manifest digest and a
fingerprint of the stored vectors, so a long-lived sidecar reads the vectors
once per index state. Coverage is also cached by a cheap fingerprint of the
scope (each extraction's block count and largest rowid, one grouped query), so
a typing search on an unchanged library says whether a meaning search is
available without re-reading or re-hashing any block, however many sources
the library holds.
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
from learnloop.db.stores.source_block_fts import extraction_fingerprints
from learnloop.source_retrieval.corpus import Scope
from learnloop.source_retrieval.recipes import (
    DOC_TASK_PREFIX,
    SOURCE_BLOCK_FIELD,
    SOURCE_BLOCK_KIND,
    extraction_manifest,
    split_record_id,
)
from learnloop.vault.models import LoadedVault

#: Statuses under which the index ranks (``partial`` ranks its complete extractions).
USABLE = frozenset({"ready", "partial"})
BACKFILL_HINT = "run `learnloop embeddings backfill --record-kind source_block`"


@dataclass
class DenseIndex:
    status: str
    reason: str | None = None
    model_id: str | None = None
    expected: int = 0
    covered: int = 0
    sources: int = 0
    sources_covered: int = 0
    ids: list[str] = field(default_factory=list)
    mean: np.ndarray | None = None
    unit: np.ndarray | None = None

    @property
    def ready(self) -> bool:
        """Every block in scope has a vector (the Phase 1 complete-index rule)."""

        return self.status == "ready"

    @property
    def usable(self) -> bool:
        return self.status in USABLE

    def describe(self) -> dict[str, Any]:
        return {"status": self.status, "reason": self.reason, "model_id": self.model_id,
                "expected": self.expected, "covered": self.covered,
                "sources": self.sources, "sources_covered": self.sources_covered}

    def rank(self, query: np.ndarray, *, limit: int,
             allow: Callable[[str], bool] | None = None) -> list[tuple[str, float]]:
        """``(record_id, score)`` best first; ``allow`` filters after centring."""

        if not self.usable or self.unit is None or self.mean is None or limit <= 0:
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


@dataclass(frozen=True)
class _Coverage:
    model_id: str
    expected: int
    sources: int
    #: record id -> ``embedding_vectors.id`` of its current vector, complete extractions only.
    rows: Mapping[str, str]
    complete: tuple[str, ...]
    uncovered_blocks: int


_CACHE: OrderedDict[tuple[Any, ...], DenseIndex] = OrderedDict()
_COVERAGE: OrderedDict[tuple[Any, ...], _Coverage] = OrderedDict()
#: Cheap scope fingerprint -> (coverage, its manifest-digest key).
_BY_FINGERPRINT: OrderedDict[tuple[Any, ...], tuple[_Coverage | None, tuple[Any, ...]]] = OrderedDict()
_CACHE_LOCK = Lock()
_CACHE_SIZE = 4
_COVERAGE_SIZE = 16


def clear_cache() -> None:
    with _CACHE_LOCK:
        _CACHE.clear()
        _COVERAGE.clear()
        _BY_FINGERPRINT.clear()


def _vectors_fingerprint(connection, model_id: str) -> tuple[int, int]:
    """Changes whenever a source-block vector for the model is added or removed."""

    if not connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'embedding_vectors'"
    ).fetchone():
        return (0, 0)
    row = connection.execute(
        "SELECT COUNT(*), COALESCE(MAX(rowid), 0) FROM embedding_vectors "
        "WHERE model_id = ? AND record_kind = ?", (model_id, SOURCE_BLOCK_KIND),
    ).fetchone()
    return int(row[0]), int(row[1])


def _covering_rows(connection, *, model_id: str, extraction_id: str,
                   manifest: Mapping[str, str]) -> dict[str, str]:
    """The current vector row per manifest record: by identity, else by content."""

    found: dict[str, str] = {}
    for row_id, record_id, content_hash in connection.execute(
        "SELECT id, record_id, content_hash FROM embedding_vectors "
        "WHERE record_kind = ? AND field = ? AND model_id = ? AND task_prefix = ? "
        "AND record_id >= ? AND record_id < ? ORDER BY created_at, id",
        (SOURCE_BLOCK_KIND, SOURCE_BLOCK_FIELD, model_id, DOC_TASK_PREFIX,
         f"{extraction_id}/", f"{extraction_id}0"),
    ):
        key = str(record_id)
        if manifest.get(key) == content_hash and key not in found:
            found[key] = str(row_id)
    missing: dict[str, list[str]] = {}
    for key, content_hash in manifest.items():
        if key not in found:
            missing.setdefault(content_hash, []).append(key)
    hashes = sorted(missing)
    for start in range(0, len(hashes), 500):
        chunk = hashes[start:start + 500]
        for row_id, content_hash in connection.execute(
            "SELECT id, content_hash FROM embedding_vectors WHERE record_kind = ? AND field = ? "
            "AND model_id = ? AND task_prefix = ? AND content_hash IN "
            f"({', '.join('?' for _ in chunk)}) ORDER BY created_at, id",
            (SOURCE_BLOCK_KIND, SOURCE_BLOCK_FIELD, model_id, DOC_TASK_PREFIX, *chunk),
        ):
            for key in missing.get(str(content_hash), ()):
                found.setdefault(key, str(row_id))
    return found


def extraction_coverage(connection, sqlite_path: Path, model_id: str, extraction_id: str) -> tuple[int, int]:
    """``(covered, embeddable)`` blocks of one extraction for ``model_id`` (no vector bytes read)."""

    manifest = extraction_manifest(connection, sqlite_path, extraction_id)
    if not manifest:
        return 0, 0
    if not connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'embedding_vectors'"
    ).fetchone():
        return 0, len(manifest)  # a database before the vector store: nothing embedded
    return len(_covering_rows(connection, model_id=model_id, extraction_id=extraction_id,
                              manifest=manifest)), len(manifest)


def _remember(cheap: tuple[Any, ...], coverage: _Coverage | None,
              key: tuple[Any, ...]) -> tuple[_Coverage | None, tuple[Any, ...]]:
    with _CACHE_LOCK:
        _BY_FINGERPRINT[cheap] = (coverage, key)
        while len(_BY_FINGERPRINT) > _COVERAGE_SIZE:
            _BY_FINGERPRINT.popitem(last=False)
    return coverage, key


def _coverage(connection, sqlite_path: Path, model_id: str, extraction_ids: list[str],
              ) -> tuple[_Coverage | None, tuple[Any, ...]]:
    fingerprints = extraction_fingerprints(connection, extraction_ids)
    vectors = _vectors_fingerprint(connection, model_id)
    cheap = (str(sqlite_path), model_id, tuple(sorted(fingerprints.items())), vectors)
    with _CACHE_LOCK:
        seen = _BY_FINGERPRINT.get(cheap)
        if seen is not None:
            _BY_FINGERPRINT.move_to_end(cheap)
            return seen
    manifests = {extraction_id: extraction_manifest(connection, sqlite_path, extraction_id,
                                                    fingerprints.get(extraction_id))
                 for extraction_id in extraction_ids}
    manifests = {key: value for key, value in manifests.items() if value}
    if not manifests:
        return _remember(cheap, None, ())
    digest = content_key(sorted((key, sorted(value.items())) for key, value in manifests.items()))
    key = (str(sqlite_path), model_id, digest, vectors)
    with _CACHE_LOCK:
        cached = _COVERAGE.get(key)
        if cached is not None:
            _COVERAGE.move_to_end(key)
    if cached is not None:
        return _remember(cheap, cached, key)
    rows: dict[str, str] = {}
    complete: list[str] = []
    uncovered = 0
    for extraction_id, manifest in sorted(manifests.items()):
        found = _covering_rows(connection, model_id=model_id, extraction_id=extraction_id, manifest=manifest)
        if len(found) == len(manifest):
            complete.append(extraction_id)
            rows.update(found)
        else:
            uncovered += len(manifest) - len(found)
    coverage = _Coverage(model_id, sum(len(manifest) for manifest in manifests.values()), len(manifests),
                         rows, tuple(complete), uncovered)
    with _CACHE_LOCK:
        _COVERAGE[key] = coverage
        while len(_COVERAGE) > _COVERAGE_SIZE:
            _COVERAGE.popitem(last=False)
    return _remember(cheap, coverage, key)


def _label(coverage: _Coverage) -> tuple[str, str | None]:
    if len(coverage.complete) == coverage.sources:
        return "ready", None
    missing_sources = coverage.sources - len(coverage.complete)
    detail = (f"{coverage.uncovered_blocks} of {coverage.expected} blocks in scope "
              f"({missing_sources} of {coverage.sources} sources) have no {coverage.model_id} vector")
    if not coverage.complete:
        return "incomplete", f"{detail}; {BACKFILL_HINT}"
    return "partial", f"meaning search covers {len(coverage.complete)} of {coverage.sources} sources: {detail}; {BACKFILL_HINT}"


def dense_coverage(vault: LoadedVault, repository: Repository, scope: Scope) -> DenseIndex:
    """The scope's dense status and counts without reading any vector bytes."""

    if not vault.config.source_retrieval.dense:
        return DenseIndex("disabled", "source_retrieval.dense is false")
    model_id = vault.config.embedding.model
    sqlite_path = Path(repository.sqlite_path)
    with closing(connect(sqlite_path, read_only=True)) as connection:
        coverage, _key = _coverage(connection, sqlite_path, model_id, sorted(scope.extractions))
    if coverage is None:
        return DenseIndex("empty", "no embeddable block in scope", model_id)
    status, reason = _label(coverage)
    return DenseIndex(status, reason, model_id, expected=coverage.expected, covered=len(coverage.rows),
                      sources=coverage.sources, sources_covered=len(coverage.complete))


def load_dense_index(vault: LoadedVault, repository: Repository, scope: Scope) -> DenseIndex:
    """The scope's dense index over its complete extractions, or a labelled reason."""

    if not vault.config.source_retrieval.dense:
        return DenseIndex("disabled", "source_retrieval.dense is false")
    model_id = vault.config.embedding.model
    sqlite_path = Path(repository.sqlite_path)
    with closing(connect(sqlite_path, read_only=True)) as connection:
        coverage, key = _coverage(connection, sqlite_path, model_id, sorted(scope.extractions))
        if coverage is None:
            return DenseIndex("empty", "no embeddable block in scope", model_id)
        status, reason = _label(coverage)
        counts = {"expected": coverage.expected, "covered": len(coverage.rows),
                  "sources": coverage.sources, "sources_covered": len(coverage.complete)}
        if status not in USABLE:
            return DenseIndex(status, reason, model_id, **counts)
        with _CACHE_LOCK:
            cached = _CACHE.get(key)
            if cached is not None:
                _CACHE.move_to_end(key)
                return cached
        ids = sorted(coverage.rows)
        blobs: dict[str, bytes] = {}
        row_ids = sorted(set(coverage.rows.values()))
        for start in range(0, len(row_ids), 500):
            chunk = row_ids[start:start + 500]
            for row_id, blob in connection.execute(
                f"SELECT id, vector FROM embedding_vectors WHERE id IN ({', '.join('?' for _ in chunk)})",
                chunk,
            ):
                blobs[str(row_id)] = blob
    if any(coverage.rows[record_id] not in blobs for record_id in ids):
        return DenseIndex("unavailable", "stored vectors changed while reading; retry", model_id, **counts)
    widths = {len(blobs[coverage.rows[record_id]]) for record_id in ids}
    if len(widths) != 1:
        return DenseIndex("unavailable", "stored vectors have mixed widths", model_id, **counts)
    matrix = np.stack([np.frombuffer(blobs[coverage.rows[record_id]], dtype="<f2").astype(np.float64)
                       for record_id in ids])
    mean = matrix.mean(axis=0)
    centered = matrix - mean
    norms = np.linalg.norm(centered, axis=1, keepdims=True)
    unit = np.divide(centered, norms, out=np.zeros_like(centered), where=norms != 0).astype(np.float32)
    index = DenseIndex(status, reason, model_id, ids=ids, mean=mean, unit=unit, **counts)
    with _CACHE_LOCK:
        _CACHE[key] = index
        while len(_CACHE) > _CACHE_SIZE:
            _CACHE.popitem(last=False)
    return index


def record_keys(record_id: str) -> tuple[str, str]:
    return split_record_id(record_id)


__all__ = ["BACKFILL_HINT", "USABLE", "DenseIndex", "clear_cache", "dense_coverage", "extraction_coverage",
           "load_dense_index", "record_keys"]

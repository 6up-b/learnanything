"""Hybrid kNN retrieval for the diagnosis context (Slice 1 §9.3–9.4; M1 arm (c)).

The embedded text is always grader-written or canonical, never a raw answer
alone (§9.3): the item stem, the first-divergence quote(s), the error types and
an excerpt of the blind grader's local analysis. Problem content dominates
raw-response embeddings, so the divergence recipe is what makes "the same
mistake on a different problem" land nearby.

Vectors are paid inputs stored through the Phase 1 store
(:mod:`learnloop.db.stores.embedding_vectors`), keyed by content hash, so a
rerun never re-embeds; replay never calls this module. Retrieval is exact
mean-centred cosine over every prepared record of one model; structured
constraints (LO neighbourhood, facet overlap, valid measurement, as-of) are
applied BEFORE ranking by the caller choosing ``candidates`` (§9.4). Any
failure degrades to ``exact_fallback`` (S6): embeddings never decide
correctness.
"""

from __future__ import annotations

import hashlib
from contextlib import AbstractContextManager, closing, nullcontext
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable, Sequence

from learnloop.ai.embedding import EmbeddingClient
from learnloop.db.connection import connect
from learnloop.db.stores.embedding_vectors import get_vector, put_vector, retrieve
from learnloop.diagnosis.split.context import (
    CurrentAttempt,
    RegistryNeighbor,
    RegistryShortlist,
    RetrievalMatch,
    RetrievalResult,
    registry_key,
)
from learnloop.diagnosis.split.history import HistoryAttempt, RegistryRecord

RECORD_KIND = "attempt"
FIELD = "divergence"
DOCUMENT_PREFIX = "retrieval-document"
QUERY_PREFIX = "retrieval-query"
RECIPE_VERSION = "attempt-divergence-v1"
_EXCERPT_CHARS = 600

#: (purpose, estimated input tokens) -> context manager admitting one paid
#: embedding request; the runner supplies its spend admission here.
RequestGuard = Callable[[str, int], AbstractContextManager]


def divergence_text(
    *,
    item_prompt: str,
    first_divergence_quotes: Iterable[str],
    error_types: Iterable[str],
    local_analysis_md: str | None,
) -> str:
    quotes = [quote.strip() for quote in first_divergence_quotes if quote and quote.strip()]
    parts = [
        f"Problem: {item_prompt.strip()}",
        "Where the work went wrong: " + (" | ".join(quotes) if quotes else "(no quote)"),
        "Error type: " + (", ".join(sorted(set(error_types))) or "(none)"),
    ]
    if local_analysis_md:
        parts.append("Grader's local reading: " + local_analysis_md.strip()[:_EXCERPT_CHARS])
    return "\n".join(parts)


def attempt_divergence_text(attempt: HistoryAttempt) -> str:
    return divergence_text(
        item_prompt=attempt.item_prompt,
        first_divergence_quotes=attempt.first_divergence_quotes,
        error_types=attempt.error_types,
        local_analysis_md=attempt.local_analysis_md,
    )


def current_divergence_text(current: CurrentAttempt) -> str:
    rows = list(current.blind_grade.get("error_attributions") or [])
    quotes = [
        str((row.get("first_divergence") or {}).get("quote") or "")
        for row in rows
        if isinstance(row.get("first_divergence"), dict)
    ]
    return divergence_text(
        item_prompt=current.item_prompt,
        first_divergence_quotes=quotes,
        error_types=[str(row.get("error_type") or "") for row in rows if row.get("error_type")],
        local_analysis_md=str(current.blind_grade.get("local_analysis_md") or "") or None,
    )


def content_hash(text: str) -> str:
    return hashlib.sha256(f"{RECIPE_VERSION}\n{text}".encode("utf-8")).hexdigest()


def estimated_embedding_tokens(text: str) -> int:
    """Same conservative bound the Phase 1 backfill uses."""

    return len(text.encode("utf-8")) + 128


@dataclass
class EmbeddingHistoryRetriever:
    """kNN over ``attempt/divergence`` vectors in one (scratch) database.

    ``prepare`` embeds every record the centroid should cover, in batches
    admitted by ``guard``. ``knn`` embeds the query (also admitted) and ranks
    only the supplied candidates, centred over all prepared records.
    """

    client: EmbeddingClient
    sqlite_path: Path
    guard: RequestGuard | None = None
    batch_size: int = 32

    def __post_init__(self) -> None:
        self._prepared: dict[str, str] = {}
        self._texts: dict[str, str] = {}

    @property
    def model_id(self) -> str:
        return self.client.model_id

    def _admit(self, purpose: str, tokens: int) -> AbstractContextManager:
        return self.guard(purpose, tokens) if self.guard is not None else nullcontext()

    def _embed(self, texts: list[str], prefix: str, purpose: str) -> list[list[float]]:
        tokens = sum(estimated_embedding_tokens(text) for text in texts)
        with self._admit(purpose, tokens):
            vectors = self.client.embed(texts, prefix)
        if len(vectors) != len(texts) or any(len(vector) != self.client.dims for vector in vectors):
            raise ValueError("embedding provider returned the wrong vector count or width")
        return vectors

    def prepare(self, attempts: Sequence[HistoryAttempt]) -> int:
        """Embed missing divergences; returns how many were newly embedded."""

        pending: list[tuple[str, str, str]] = []
        with closing(connect(self.sqlite_path, read_only=True)) as connection:
            for attempt in attempts:
                if not attempt.non_pass:
                    continue
                text = attempt_divergence_text(attempt)
                digest = content_hash(text)
                self._prepared[attempt.attempt_id] = digest
                self._texts[attempt.attempt_id] = text
                if get_vector(
                    connection,
                    record_kind=RECORD_KIND,
                    record_id=attempt.attempt_id,
                    field=FIELD,
                    content_hash=digest,
                    model_id=self.client.model_id,
                    task_prefix=DOCUMENT_PREFIX,
                ) is None:
                    pending.append((attempt.attempt_id, digest, text))
        embedded = 0
        for offset in range(0, len(pending), self.batch_size):
            batch = pending[offset:offset + self.batch_size]
            vectors = self._embed([text for _id, _hash, text in batch], DOCUMENT_PREFIX, "embedding:attempt_divergence")
            with closing(connect(self.sqlite_path)) as connection, connection:
                for (record_id, digest, _text), vector in zip(batch, vectors, strict=True):
                    put_vector(
                        connection,
                        record_kind=RECORD_KIND,
                        record_id=record_id,
                        field=FIELD,
                        content_hash=digest,
                        model_id=self.client.model_id,
                        task_prefix=DOCUMENT_PREFIX,
                        vector=vector,
                    )
            embedded += len(batch)
        return embedded

    def knn(
        self,
        current: CurrentAttempt,
        candidates: Sequence[HistoryAttempt],
        *,
        limit: int,
    ) -> RetrievalResult:
        try:
            missing = [attempt for attempt in candidates if attempt.attempt_id not in self._prepared]
            if missing:
                self.prepare(missing)
            query_text = current_divergence_text(current)
            query = self._embed([query_text], QUERY_PREFIX, "embedding:attempt_divergence_query")[0]
            candidate_ids = [attempt.attempt_id for attempt in candidates if attempt.attempt_id in self._prepared]
            with closing(connect(self.sqlite_path, read_only=True)) as connection:
                matches = retrieve(
                    connection,
                    record_kind=RECORD_KIND,
                    field=FIELD,
                    model_id=self.client.model_id,
                    task_prefix=DOCUMENT_PREFIX,
                    query=query,
                    expected_records=dict(self._prepared),
                    limit=limit,
                    candidate_ids=candidate_ids,
                )
        except Exception as exc:  # noqa: BLE001 - S6: never fail the diagnosis on retrieval
            return RetrievalResult(method="exact_fallback", model_id=self.client.model_id, error=type(exc).__name__)
        return RetrievalResult(
            method="knn",
            model_id=self.client.model_id,
            matches=tuple(
                RetrievalMatch(attempt_id=match.record_id, score=match.score, rank=rank)
                for rank, match in enumerate(matches, start=1)
            ),
        )

    def registry_knn(
        self,
        current: CurrentAttempt,
        records: Sequence[RegistryRecord],
        *,
        limit: int,
    ) -> RegistryShortlist:
        """Rank the as-of registry by the current failure (S1.4a shortlist).

        Model completeness: every record in ``records`` must have a current
        ``misconception/statement`` vector under this model before anything
        is ranked (the index is centred over exactly these records). Missing
        or stale ones are embedded first, admitted by ``guard``; any failure,
        refusal or incomplete index is ``exact_fallback`` (S6), never a
        partial ranking.
        """

        from learnloop.diagnosis.split.embeddings import (
            MISCONCEPTION_FIELD,
            MISCONCEPTION_KIND,
            TASK_PREFIX,
            misconception_record,
        )

        try:
            expected: dict[str, str] = {}
            pending = []
            with closing(connect(self.sqlite_path, read_only=True)) as connection:
                for record in records:
                    embedded = misconception_record(registry_key(record), record.statement)
                    if embedded is None:
                        continue
                    expected[embedded.record_id] = embedded.content_hash
                    if get_vector(
                        connection,
                        record_kind=MISCONCEPTION_KIND,
                        record_id=embedded.record_id,
                        field=MISCONCEPTION_FIELD,
                        content_hash=embedded.content_hash,
                        model_id=self.client.model_id,
                        task_prefix=TASK_PREFIX,
                    ) is None:
                        pending.append(embedded)
            for offset in range(0, len(pending), self.batch_size):
                batch = pending[offset:offset + self.batch_size]
                vectors = self._embed([record.text for record in batch], TASK_PREFIX, "embedding:misconception_statement")
                with closing(connect(self.sqlite_path)) as connection, connection:
                    for record, vector in zip(batch, vectors, strict=True):
                        put_vector(
                            connection,
                            record_kind=MISCONCEPTION_KIND,
                            record_id=record.record_id,
                            field=MISCONCEPTION_FIELD,
                            content_hash=record.content_hash,
                            model_id=self.client.model_id,
                            task_prefix=TASK_PREFIX,
                            vector=vector,
                        )
            if not expected:
                return RegistryShortlist(method="knn", model_id=self.client.model_id)
            query = self._embed([current_divergence_text(current)], QUERY_PREFIX, "embedding:misconception_query")[0]
            with closing(connect(self.sqlite_path, read_only=True)) as connection:
                matches = retrieve(
                    connection,
                    record_kind=MISCONCEPTION_KIND,
                    field=MISCONCEPTION_FIELD,
                    model_id=self.client.model_id,
                    task_prefix=TASK_PREFIX,
                    query=query,
                    expected_records=expected,
                    limit=limit,
                )
        except Exception as exc:  # noqa: BLE001 - S6: retrieval never fails a diagnosis
            return RegistryShortlist(method="exact_fallback", model_id=self.client.model_id, error=type(exc).__name__)
        return RegistryShortlist(
            method="knn",
            model_id=self.client.model_id,
            matches=tuple(
                RegistryNeighbor(key=match.record_id, score=match.score, rank=rank)
                for rank, match in enumerate(matches, start=1)
            ),
        )



def planned_retrieval_requests(
    sqlite_path: Path,
    model_id: str,
    current: CurrentAttempt,
    *,
    registry: Sequence[RegistryRecord] = (),
    failures: Sequence[HistoryAttempt] = (),
    seen: set[tuple[str, str, str]] | None = None,
    batch_size: int = 32,
) -> tuple[int, int]:
    """Upper bound on one diagnosis's embedding requests: (requests, input tokens).

    Mirrors :class:`EmbeddingHistoryRetriever` without calling it (a dry
    run): the registry shortlist embeds every visible record still missing a
    vector, in batches, then one query; the hybrid index embeds every prior
    failure still missing one, then one query. ``seen`` carries what earlier
    planned diagnoses of the same command will already have embedded.
    """

    from learnloop.diagnosis.split.embeddings import (
        MISCONCEPTION_FIELD,
        MISCONCEPTION_KIND,
        TASK_PREFIX,
        misconception_record,
    )

    seen = seen if seen is not None else set()
    requests = 0
    tokens = 0
    query_tokens = estimated_embedding_tokens(current_divergence_text(current))

    def batches(texts: list[str]) -> None:
        nonlocal requests, tokens
        requests += -(-len(texts) // batch_size)
        tokens += sum(estimated_embedding_tokens(text) for text in texts)

    with closing(connect(sqlite_path, read_only=True)) as connection:
        expected = 0
        pending: list[str] = []
        for record in registry:
            embedded = misconception_record(registry_key(record), record.statement)
            if embedded is None:
                continue
            expected += 1
            key = (MISCONCEPTION_KIND, embedded.record_id, embedded.content_hash)
            if key in seen:
                continue
            if get_vector(
                connection,
                record_kind=MISCONCEPTION_KIND,
                record_id=embedded.record_id,
                field=MISCONCEPTION_FIELD,
                content_hash=embedded.content_hash,
                model_id=model_id,
                task_prefix=TASK_PREFIX,
            ) is None:
                seen.add(key)
                pending.append(embedded.text)
        if expected:
            batches(pending)
            requests += 1
            tokens += query_tokens
        pending = []
        prior = [attempt for attempt in failures if attempt.non_pass]
        for attempt in prior:
            text = attempt_divergence_text(attempt)
            digest = content_hash(text)
            key = (RECORD_KIND, attempt.attempt_id, digest)
            if key in seen:
                continue
            if get_vector(
                connection,
                record_kind=RECORD_KIND,
                record_id=attempt.attempt_id,
                field=FIELD,
                content_hash=digest,
                model_id=model_id,
                task_prefix=DOCUMENT_PREFIX,
            ) is None:
                seen.add(key)
                pending.append(text)
        if prior:
            batches(pending)
            requests += 1
            tokens += query_tokens
    return requests, tokens

__all__ = [
    "DOCUMENT_PREFIX",
    "EmbeddingHistoryRetriever",
    "FIELD",
    "QUERY_PREFIX",
    "RECIPE_VERSION",
    "RECORD_KIND",
    "attempt_divergence_text",
    "content_hash",
    "current_divergence_text",
    "divergence_text",
    "estimated_embedding_tokens",
    "planned_retrieval_requests",
]

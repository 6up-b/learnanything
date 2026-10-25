"""Retrieval feedback: deliveries, signals and the fusion posterior's refit (spec §9.2).

While a new space is switched on and ``embedding.source_space.log_feedback``
is true:

* every deep search writes ONE ``query`` receipt (spaces, reasons, served and
  would-be learned weights, the lists available and queried and each list's
  probability of being queried, and the candidates' ranks in every list);
* each consumer writes the ``delivered`` rows at ITS delivery boundary
  (:func:`deliver`; Codex review F9): what the learner or the model was
  actually given, in its final order, after answer-overlap filtering,
  verification and truncation. A candidate the consumer dropped is never a
  delivery, so it never becomes a negative observation. Exploration (its own
  switch) reorders the final list there, so the logged propensity is the
  delivered position's.

Signals name the delivery they answer:

* **cited**: the tutor's validated citations (``tutor_qa``) join the newest
  delivery of the same span for the same question (``owner_id``); a library
  ask's pinned tutor answer cites the ask's own retrieval;
* **opened**: :func:`record_open` names the result's receipt (the Reader's
  library search result click sends it);
* **anchored**: the teacher's grounded anchors, when the teacher lands.

A logging failure never fails the search or the answer it rides on.
``local_embeddings.fusion.refit_posteriors`` (re-exported here) is the
replayer's body, the refit command's and the ingest host's background
refresh (:func:`refresh_due`).
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from contextlib import closing
import logging
from typing import Any

from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.db.stores.retrieval_spaces import (
    append_feedback,
    delivery_for_receipt,
    feedback_rows,
    has_tables,
    record_citation_signals,
)
from learnloop.ids import new_ulid
from learnloop.local_embeddings.fusion import refit_posteriors

logger = logging.getLogger(__name__)


def new_receipt_id() -> str:
    return "rq_" + new_ulid()


def log_search(repository: Repository, *, receipt_id: str, consumer: str, query_kind: str, owner_id: str,
               resolution: Mapping[str, Any], hits: Sequence[Any], space_ranks: Mapping[str, Mapping[str, int]],
               lists_available: Sequence[str] = (), queried: Sequence[str] = (),
               query_propensity: Mapping[str, float] | None = None) -> int:
    """The one ``query`` row of a search, its candidates' ranks included; returns rows written (0 on failure)."""

    candidates = {hit.record_id: dict(space_ranks.get(hit.record_id) or {}) for hit in hits}
    rows: list[dict[str, Any]] = [{"receipt_id": receipt_id, "event": "query", "consumer": consumer,
                                   "query_kind": query_kind, "owner_id": owner_id,
                                   "payload": {**dict(resolution), "lists_available": list(lists_available),
                                               "queried": list(queried),
                                               "query_propensity": dict(query_propensity or {}),
                                               "candidates": candidates}}]
    try:
        with repository.connection() as connection:
            if not has_tables(connection):
                return 0
            return append_feedback(connection, rows)
    except Exception:  # noqa: BLE001 - logging never fails the search
        logger.warning("retrieval feedback could not be logged", exc_info=True)
        return 0


def deliver(vault: Any, repository: Repository, search: Any, keys: Sequence[tuple[str, str]]) -> list[int]:
    """Record what a consumer finally delivers from ``search`` (Codex review F9).

    ``keys`` are the delivered spans in the order the consumer would give
    them. With ``embedding.source_space.exploration`` on, spans the posterior
    cannot order are reordered inside their tie band (a seeded Thompson draw)
    and each span's propensity is that of its DELIVERED position. Returns the
    delivery order as indices into ``keys`` (the identity when nothing is
    logged or explored). Never fails the consumer."""

    from learnloop.local_embeddings import fusion
    from learnloop.source_retrieval.recipes import block_record_id

    order = list(range(len(keys)))
    resolution = getattr(search, "resolution", None)
    if resolution is None or not getattr(resolution, "receipt_id", "") or not keys:
        return order
    settings = vault.config.embedding.source_space
    if not settings.log_feedback:
        return order
    try:
        record_ids = [block_record_id(str(extraction_id), str(span_id)) for extraction_id, span_id in keys]
        info: dict[str, Any] = {}
        posterior = resolution.posterior
        if settings.exploration and posterior:
            lists = list(posterior.get("lists") or ())
            rrf_k = float(posterior.get("rrf_k") or resolution.rrf_k)
            features = {record_id: fusion.feature_row(resolution.space_ranks.get(record_id, {}), lists, rrf_k)
                        for record_id in record_ids}
            explored, info = fusion.explore(record_ids, features, posterior, lists,
                                            seed=fusion.rng_seed(resolution.receipt_id + ":delivered"))
            order = [record_ids.index(record_id) for record_id in explored]
            resolution.exploration = info
        propensities = info.get("propensities") or {}
        rows = [{"receipt_id": resolution.receipt_id, "event": "delivered", "consumer": resolution.consumer,
                 "query_kind": resolution.query_kind, "owner_id": resolution.owner_id,
                 "extraction_id": str(keys[index][0]), "span_id": str(keys[index][1]), "position": position,
                 "payload": {"space_ranks": dict(resolution.space_ranks.get(record_ids[index]) or {}),
                             "propensity": float(propensities.get(record_ids[index], 1.0)),
                             "explored": bool(info.get("explored")), "seed": info.get("seed")}}
                for position, index in enumerate(order, start=1)]
        with repository.connection() as connection:
            if has_tables(connection):
                append_feedback(connection, rows)
    except Exception:  # noqa: BLE001 - logging never fails the consumer
        logger.warning("retrieval deliveries could not be logged", exc_info=True)
        return list(range(len(keys)))
    return order


def record_citations(repository: Repository, *, consumer: str, owner_id: str,
                     citations: Sequence[Mapping[str, Any]]) -> int:
    """``cited`` rows for validated citations of spans this owner's search delivered."""

    if not owner_id or not citations:
        return 0
    try:
        with repository.connection() as connection:
            return record_citation_signals(connection, consumer=consumer, owner_id=owner_id, citations=citations)
    except Exception:  # noqa: BLE001 - a signal never fails the answer
        logger.warning("retrieval citations could not be logged", exc_info=True)
        return 0


def record_receipt_citations(repository: Repository, *, receipt_ids: Sequence[str],
                             citations: Sequence[Mapping[str, Any]]) -> int:
    """``cited`` rows for validated citations of spans one of ``receipt_ids``
    delivered (a library ask's tutor answer cites the ask's own retrieval);
    returns rows written, 0 when none was delivered or on failure."""

    receipts = [str(receipt) for receipt in dict.fromkeys(receipt_ids) if receipt]
    if not receipts or not citations:
        return 0
    try:
        with repository.connection() as connection:
            if not has_tables(connection):
                return 0
            rows: list[dict[str, Any]] = []
            for key in dict.fromkeys((str(item.get("extraction_id")), str(item.get("span_id"))) for item in citations):
                for receipt in receipts:
                    found = delivery_for_receipt(connection, receipt, key)
                    if found is not None:
                        rows.append({"receipt_id": receipt, "event": "cited", "consumer": found["consumer"],
                                     "query_kind": found["query_kind"], "owner_id": found["owner_id"],
                                     "extraction_id": key[0], "span_id": key[1], "position": found["position"],
                                     "payload": {"signal": "validated_citation"}})
                        break
            return append_feedback(connection, rows) if rows else 0
    except Exception:  # noqa: BLE001 - a signal never fails the answer
        logger.warning("retrieval citations could not be logged", exc_info=True)
        return 0


#: keep (operational, spec §9.2 "a nightly job, or one at sidecar start"): the
#: ingest host refits the fusion posterior at its start and then at most once
#: in this many hours, and only when receipts arrived since the last fit.
REFIT_EVERY_HOURS = 24.0


def refresh_due(repository: Repository, *, last_refit: Any | None, now: Any) -> bool:
    """Whether the background refit should run: receipts newer than the stored
    posterior, and this host has not refitted within ``REFIT_EVERY_HOURS``."""

    from datetime import timedelta

    if last_refit is not None and now - last_refit < timedelta(hours=REFIT_EVERY_HOURS):
        return False
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        if not has_tables(connection):
            return False
        newest = connection.execute("SELECT MAX(created_at) FROM retrieval_feedback").fetchone()[0]
        fitted = connection.execute(
            "SELECT fitted_at FROM retrieval_fusion_posteriors WHERE context_key = 'global'").fetchone()
    return newest is not None and (fitted is None or str(newest) > str(fitted[0]))


def record_open(repository: Repository, *, receipt_id: str, extraction_id: str, span_id: str) -> bool:
    """An ``opened`` row when the learner opens a span that ``receipt_id`` delivered."""

    try:
        with repository.connection() as connection:
            found = delivery_for_receipt(connection, receipt_id, (extraction_id, span_id))
            if found is None:
                return False
            append_feedback(connection, [{"receipt_id": receipt_id, "event": "opened", "consumer": found["consumer"],
                                          "query_kind": found["query_kind"], "owner_id": found["owner_id"],
                                          "extraction_id": extraction_id, "span_id": span_id,
                                          "position": found["position"], "payload": {"signal": "result_open"}}])
            return True
    except Exception:  # noqa: BLE001
        logger.warning("a result open could not be logged", exc_info=True)
        return False


def feedback_summary(repository: Repository) -> dict[str, Any]:
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        if not has_tables(connection):
            return {"available": False}
        counts = dict(connection.execute(
            "SELECT event, COUNT(*) FROM retrieval_feedback GROUP BY event").fetchall())
        posteriors = connection.execute("SELECT COUNT(*) FROM retrieval_fusion_posteriors").fetchone()[0]
    return {"available": True, "events": {key: int(value) for key, value in sorted(counts.items())},
            "posterior_contexts": int(posteriors)}


__all__ = ["REFIT_EVERY_HOURS", "deliver", "feedback_summary", "log_search", "new_receipt_id", "record_citations", "record_open", "record_receipt_citations", "refit_posteriors", "refresh_due"]

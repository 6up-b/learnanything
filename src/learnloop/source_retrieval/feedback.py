"""Retrieval feedback: deliveries, signals and the fusion posterior's refit (spec §9.2).

P1 ships the LOGGING (orchestrator scoping 2026-10-24): while a new space is
switched on and ``embedding.source_space.log_feedback`` is true, every deep
search writes one ``query`` receipt (spaces, reasons, served and would-be
learned weights, the exploration draw) and one ``delivered`` row per
delivered span (its rank in every contributing space's list and its
position). Signals name the delivery they answer:

* **cited**: the tutor's validated citations (``tutor_qa``) join the newest
  delivery of the same span for the same question (``owner_id``);
* **opened**: :func:`record_open` names the result's receipt (the desktop
  wiring is a follow-up; the recorder and its tests land here);
* **anchored**: the teacher's grounded anchors, when the teacher lands.

A logging failure never fails the search or the answer it rides on.
``refit_posteriors`` is the replayer's body and the refit command's: it
recomputes the whole DERIVED table from the receipts in order.
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
    deliveries_for_owner,
    delivery_for_receipt,
    feedback_rows,
    has_tables,
    replace_fusion_posteriors,
)
from learnloop.ids import new_ulid
from learnloop.source_retrieval import fusion
from learnloop.vault.models import LoadedVault

logger = logging.getLogger(__name__)


def new_receipt_id() -> str:
    return "rq_" + new_ulid()


def log_search(repository: Repository, *, receipt_id: str, consumer: str, query_kind: str, owner_id: str,
               resolution: Mapping[str, Any], hits: Sequence[Any], space_ranks: Mapping[str, Mapping[str, int]],
               propensities: Mapping[str, float] | None = None, explored: bool = False) -> int:
    """One ``query`` row and one ``delivered`` row per hit; returns rows written (0 on failure)."""

    rows: list[dict[str, Any]] = [{"receipt_id": receipt_id, "event": "query", "consumer": consumer,
                                   "query_kind": query_kind, "owner_id": owner_id,
                                   "payload": {**dict(resolution), "explored": bool(explored)}}]
    for position, hit in enumerate(hits, start=1):
        record_id = hit.record_id
        rows.append({"receipt_id": receipt_id, "event": "delivered", "consumer": consumer, "query_kind": query_kind,
                     "owner_id": owner_id, "extraction_id": hit.extraction_id, "span_id": hit.span_id,
                     "position": position,
                     "payload": {"space_ranks": dict(space_ranks.get(record_id) or {}),
                                 "pool_role": hit.pool_role,
                                 "propensity": float((propensities or {}).get(record_id, 1.0))}})
    try:
        with repository.connection() as connection:
            if not has_tables(connection):
                return 0
            return append_feedback(connection, rows)
    except Exception:  # noqa: BLE001 - logging never fails the search
        logger.warning("retrieval feedback could not be logged", exc_info=True)
        return 0


def record_citations(repository: Repository, *, consumer: str, owner_id: str,
                     citations: Sequence[Mapping[str, Any]]) -> int:
    """``cited`` rows for validated citations of spans this owner's search delivered."""

    keys = [(str(item.get("extraction_id")), str(item.get("span_id"))) for item in citations]
    if not owner_id or not keys:
        return 0
    try:
        with repository.connection() as connection:
            delivered = deliveries_for_owner(connection, consumer=consumer, owner_id=owner_id, keys=keys)
            rows = [{"receipt_id": found["receipt_id"], "event": "cited", "consumer": consumer,
                     "query_kind": found["query_kind"], "owner_id": owner_id, "extraction_id": key[0],
                     "span_id": key[1], "position": found["position"], "payload": {"signal": "validated_citation"}}
                    for key, found in sorted(delivered.items())]
            return append_feedback(connection, rows) if rows else 0
    except Exception:  # noqa: BLE001 - a signal never fails the answer
        logger.warning("retrieval citations could not be logged", exc_info=True)
        return 0


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


def refit_posteriors(vault: LoadedVault, repository: Repository) -> dict[str, Any]:
    """Recompute ``retrieval_fusion_posteriors`` from every feedback row, in order."""

    with repository.connection() as connection:
        if not has_tables(connection):
            return {"written": 0, "rows": 0}
        rows = feedback_rows(connection)
        fitted = fusion.refit(rows, default=vault.config.embedding.source_space.default,
                              rrf_k_seed=float(vault.config.source_retrieval.rrf_k))
        written = replace_fusion_posteriors(connection, fitted)
    return {"written": written, "rows": len(rows),
            "contexts": [row["context_key"] for row in fitted],
            "signals": sum(int(row["signals"]) for row in fitted if row["context_key"] == fusion.GLOBAL)}


def feedback_summary(repository: Repository) -> dict[str, Any]:
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        if not has_tables(connection):
            return {"available": False}
        counts = dict(connection.execute(
            "SELECT event, COUNT(*) FROM retrieval_feedback GROUP BY event").fetchall())
        posteriors = connection.execute("SELECT COUNT(*) FROM retrieval_fusion_posteriors").fetchone()[0]
    return {"available": True, "events": {key: int(value) for key, value in sorted(counts.items())},
            "posterior_contexts": int(posteriors)}


__all__ = ["feedback_summary", "log_search", "new_receipt_id", "record_citations", "record_open", "refit_posteriors"]

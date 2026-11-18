"""Availability and evidence admission for attempt-ledger readers.

An attempt becomes known at received_at when present, otherwise at created_at.
With available_at_reads enabled, decision cutoffs use this time in SQL and
over loaded rows. SQL falls back on NULL, and the loaded-row reader also falls
back on an empty receipt. With the switch disabled, cutoffs use created_at.
Lower bounds and display order remain on occurrence time. With
self_report_not_validated enabled, learner reports are excluded from validated
resolution evidence.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any


#: The resolution-id prefix a learner's own report carries (``record_unresolved_cause_self_report``).
LEARNER_REPORT_PREFIX = "learner_report:"

#: The SQL form of :func:`available_at`, for a ``practice_attempts`` row (optionally aliased).
AVAILABLE_AT_SQL = "COALESCE(received_at, created_at)"

#: ``practice_attempts.received_at_source``: written at the time of the write, or inferred by the
#: migration from the attempt id's ULID time (imported exam rows).
RECEIVED_AT_RECORDED = "recorded"
RECEIVED_AT_INFERRED = "inferred"


def available_at_reads_on(config: Any) -> bool:
    """§5.3: True when decision-time attempt reads use the availability time."""

    section = getattr(config, "router_objective", None)
    return bool(getattr(section, "available_at_reads", False))


def self_report_not_validated_on(config: Any) -> bool:
    """§5.4: True when a learner's pick is not counted as validated evidence."""

    section = getattr(config, "router_objective", None)
    return bool(getattr(section, "self_report_not_validated", False))


def available_at(row: Mapping[str, Any]) -> str | None:
    """``coalesce(received_at, created_at)``: when the attempt became known to the system.

    ``created_at`` is when it happened (an exam sat on its date); ``received_at`` is set only where the
    two differ (exam seeding writes a past ``created_at``)."""

    received = row.get("received_at")
    if received:
        return str(received)
    created = row.get("created_at")
    return str(created) if created else None


def attempt_time_sql(config: Any, *, alias: str | None = None) -> str:
    """THE availability predicate's SQL form: the expression a decision-time read of
    ``practice_attempts`` compares its time cutoff with (``<expr> < ?``, ``<expr> <= ?``).

    With ``[router_objective] available_at_reads`` on, ``COALESCE(received_at, created_at)``:
    an attempt counts at a cutoff only once it was known (an exam sat May 1 and imported May 19 is not
    there on May 5). Otherwise ``created_at``: the predecessor's column, so the read's SQL is
    the predecessor's text byte for byte. ``alias`` prefixes the columns (``a.created_at``).

    A window's lower bound (``created_at >= since``) and the order rows are shown in stay by when the
    work happened; only the cutoff asks this."""

    prefix = f"{alias}." if alias else ""
    occurrence = f"{prefix}created_at"
    if not available_at_reads_on(config):
        return occurrence
    return f"COALESCE({prefix}received_at, {occurrence})"


def known_at(row: Mapping[str, Any], config: Any) -> str | None:
    """THE availability predicate over a loaded ``practice_attempts`` row: the time a decision-time
    cutoff compares with. :func:`available_at` with the switch on (a row read without
    ``received_at`` falls back to ``created_at``), otherwise ``created_at``, as the predecessor."""

    if available_at_reads_on(config):
        return available_at(row)
    created = row.get("created_at")
    return str(created) if created else None


def validated_resolution_ids(ids: Iterable[Any], config: Any) -> list[Any]:
    """The resolution ids that count as validated evidence: all of them with the switch off; otherwise all but a learner's own reports (§5.4)."""

    values = list(ids or [])
    if not self_report_not_validated_on(config):
        return values
    return [value for value in values if not str(value).startswith(LEARNER_REPORT_PREFIX)]

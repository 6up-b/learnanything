"""Router objective RO1's switches and the availability time (spec_router_objective_v1 §5). A leaf.

Each gate is the successor's tag (``INTERVAL_FACTOR_VERSIONS``, mvp-0.46) AND its own kill switch, default
true; off, or below the tag, the predecessor's behaviour:

* :func:`interval_factor_removed`: the surprise factor is not applied to the FSRS interval (§5.1). The
  attempt path asks it once per review, live and in replay alike, so a rebuild re-derives due dates under
  the vault's config;
* :func:`available_at_reads_on`: decision-time reads of attempts use :func:`available_at` (§5.3);
* :func:`self_report_not_validated_on`: a ``learner_report:*`` resolution id is no validated evidence (§5.4).

:func:`projection_switches` is what a whole-vault rebuild's receipt records (the projection's defaults
snapshot, §5.5), so ``doctor`` can say when persisted due dates were derived under another setting.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from learnloop.algorithm_versions import INTERVAL_FACTOR_VERSIONS

#: The resolution-id prefix a learner's own report carries (``record_unresolved_cause_self_report``).
LEARNER_REPORT_PREFIX = "learner_report:"

#: The SQL form of :func:`available_at`, for a ``practice_attempts`` row (optionally aliased).
AVAILABLE_AT_SQL = "COALESCE(received_at, created_at)"

#: ``practice_attempts.received_at_source``: written at the time of the write, or inferred by the
#: migration from the attempt id's ULID time (imported exam rows).
RECEIVED_AT_RECORDED = "recorded"
RECEIVED_AT_INFERRED = "inferred"

#: The key a rebuild receipt's ``projection_switches_json`` records the factor's gate under.
INTERVAL_FACTOR_SNAPSHOT_KEY = "scheduler.surprise.remove_interval_factor"


def _at_tag(config: Any) -> bool:
    algorithms = getattr(config, "algorithms", None)
    return getattr(algorithms, "algorithm_version", None) in INTERVAL_FACTOR_VERSIONS


def interval_factor_removed(config: Any) -> bool:
    """§5.1: True when the FSRS interval carries no surprise factor (the tag and the switch)."""

    scheduler = getattr(config, "scheduler", None)
    surprise = getattr(scheduler, "surprise", None)
    return _at_tag(config) and bool(getattr(surprise, "remove_interval_factor", False))


def available_at_reads_on(config: Any) -> bool:
    """§5.3: True when decision-time attempt reads use the availability time."""

    section = getattr(config, "router_objective", None)
    return _at_tag(config) and bool(getattr(section, "available_at_reads", False))


def self_report_not_validated_on(config: Any) -> bool:
    """§5.4: True when a learner's pick is not counted as validated evidence."""

    section = getattr(config, "router_objective", None)
    return _at_tag(config) and bool(getattr(section, "self_report_not_validated", False))


def available_at(row: Mapping[str, Any]) -> str | None:
    """``coalesce(received_at, created_at)``: when the attempt became known to the system.

    ``created_at`` is when it happened (an exam sat on its date); ``received_at`` is set only where the
    two differ (exam seeding writes a past ``created_at``)."""

    received = row.get("received_at")
    if received:
        return str(received)
    created = row.get("created_at")
    return str(created) if created else None


def attempt_time_column(config: Any) -> str:
    """The SQL expression a decision-time read filters and orders attempts by: the availability time at
    the tag with the switch on, otherwise ``created_at`` (the predecessor's SQL, byte for byte)."""

    return AVAILABLE_AT_SQL if available_at_reads_on(config) else "created_at"


def validated_resolution_ids(ids: Iterable[Any], config: Any) -> list[Any]:
    """The resolution ids that count as validated evidence: all of them below the tag or with the switch
    off; otherwise all but a learner's own reports (§5.4)."""

    values = list(ids or [])
    if not self_report_not_validated_on(config):
        return values
    return [value for value in values if not str(value).startswith(LEARNER_REPORT_PREFIX)]


def projection_switches(config: Any) -> dict[str, bool]:
    """What a whole-vault rebuild derived persisted due dates under (§5.5): whether the factor was removed."""

    return {INTERVAL_FACTOR_SNAPSHOT_KEY: interval_factor_removed(config)}


__all__ = [
    "AVAILABLE_AT_SQL",
    "INTERVAL_FACTOR_SNAPSHOT_KEY",
    "LEARNER_REPORT_PREFIX",
    "RECEIVED_AT_INFERRED",
    "RECEIVED_AT_RECORDED",
    "attempt_time_column",
    "available_at",
    "available_at_reads_on",
    "interval_factor_removed",
    "projection_switches",
    "self_report_not_validated_on",
    "validated_resolution_ids",
]

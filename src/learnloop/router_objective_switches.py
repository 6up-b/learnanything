"""Router objective RO1's switches and the availability time (spec_router_objective_v1 §5). A leaf.

Each gate is the successor's tag (``INTERVAL_FACTOR_VERSIONS``, mvp-0.46) AND its own kill switch, default
true; off, or below the tag, the predecessor's behaviour:

* :func:`interval_factor_removed`: the surprise factor is not applied to the FSRS interval (§5.1). The
  attempt path asks it once per review, live and in replay alike, so a rebuild re-derives due dates under
  the vault's config;
* :func:`available_at_reads_on`: decision-time reads of attempts use :func:`available_at` (§5.3),
  through the one predicate, :func:`attempt_time_sql` in SQL and :func:`known_at` over a loaded row
  (landing ruling R1: every decision-time read of ``practice_attempts`` with a time cutoff asks it;
  outcomes, FSRS, mastery, write paths and reports keep occurrence time, named with their reasons in
  ``tests/test_ro1_availability_reads.py``);
* :func:`self_report_not_validated_on`: a ``learner_report:*`` resolution id is no validated evidence (§5.4).

Router objective RO4's (§8; ``ROUTER_OBJECTIVE_VERSIONS``, mvp-0.47): :func:`objective_on` (the tag and
``[router_objective] enabled``), :func:`objective_scores_on` (and RO0's receipts: a comparison score needs
them) and :func:`sensors_in_value_on`.

:func:`projection_switches` is what a whole-vault rebuild's receipt records (the projection's defaults
snapshot, §5.5), so ``doctor`` can say when persisted due dates were derived under another setting.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from learnloop.algorithm_versions import INTERVAL_FACTOR_VERSIONS, ROUTER_OBJECTIVE_VERSIONS

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


def attempt_time_sql(config: Any, connection: Any = None, *, alias: str | None = None) -> str:
    """THE availability predicate's SQL form: the expression a decision-time read of
    ``practice_attempts`` compares its time cutoff with (``<expr> < ?``, ``<expr> <= ?``).

    At the tag with ``[router_objective] available_at_reads`` on, ``COALESCE(received_at, created_at)``:
    an attempt counts at a cutoff only once it was known (an exam sat May 1 and imported May 19 is not
    there on May 5). Otherwise, and when ``connection``'s ``practice_attempts`` has no ``received_at``
    (a database below migration 244), ``created_at``: the predecessor's column, so the read's SQL is
    the predecessor's text byte for byte. ``alias`` prefixes the columns (``a.created_at``).

    A window's lower bound (``created_at >= since``) and the order rows are shown in stay by when the
    work happened; only the cutoff asks this."""

    prefix = f"{alias}." if alias else ""
    occurrence = f"{prefix}created_at"
    if not available_at_reads_on(config):
        return occurrence
    if connection is not None and not _has_received_at(connection):
        return occurrence
    return f"COALESCE({prefix}received_at, {occurrence})"


def known_at(row: Mapping[str, Any], config: Any) -> str | None:
    """THE availability predicate over a loaded ``practice_attempts`` row: the time a decision-time
    cutoff compares with. :func:`available_at` at the tag with the switch on (a row read without
    ``received_at`` falls back to ``created_at``), otherwise ``created_at``, as the predecessor."""

    if available_at_reads_on(config):
        return available_at(row)
    created = row.get("created_at")
    return str(created) if created else None


def _has_received_at(connection: Any) -> bool:
    return any(row[1] == "received_at" for row in connection.execute("PRAGMA table_info(practice_attempts)"))


def validated_resolution_ids(ids: Iterable[Any], config: Any) -> list[Any]:
    """The resolution ids that count as validated evidence: all of them below the tag or with the switch
    off; otherwise all but a learner's own reports (§5.4)."""

    values = list(ids or [])
    if not self_report_not_validated_on(config):
        return values
    return [value for value in values if not str(value).startswith(LEARNER_REPORT_PREFIX)]


def objective_tag(config: Any) -> bool:
    """RO4 (§8): the vault is at the router objective's successor (mvp-0.47) or later."""

    algorithms = getattr(config, "algorithms", None)
    return getattr(algorithms, "algorithm_version", None) in ROUTER_OBJECTIVE_VERSIONS


def objective_on(config: Any) -> bool:
    """RO4 (§8.3): the objective serves: the tag and ``[router_objective] enabled``. Off, or below the tag,
    the predecessor's mixture and frame exactly (below the tag nothing is computed)."""

    section = getattr(config, "router_objective", None)
    return objective_tag(config) and bool(getattr(section, "enabled", False))


def objective_scores_on(config: Any) -> bool:
    """RO4 (§8.3, §8.7): a comparison score can be formed: the objective serves AND RO0's receipts are on
    (with receipts off the objective serves and no score forms)."""

    section = getattr(config, "router_objective", None)
    return objective_on(config) and bool(getattr(section, "receipts", False))


def sensors_in_value_on(config: Any) -> bool:
    """RO4 (§8.4): the LLM's effect-slope correction enters the value (by hand off)."""

    section = getattr(config, "router_objective", None)
    return objective_on(config) and bool(getattr(section, "sensors_in_value", False))


def projection_switches(config: Any) -> dict[str, bool]:
    """What a whole-vault rebuild derived persisted due dates under (§5.5): whether the factor was removed."""

    return {INTERVAL_FACTOR_SNAPSHOT_KEY: interval_factor_removed(config)}


__all__ = [
    "AVAILABLE_AT_SQL",
    "INTERVAL_FACTOR_SNAPSHOT_KEY",
    "LEARNER_REPORT_PREFIX",
    "RECEIVED_AT_INFERRED",
    "RECEIVED_AT_RECORDED",
    "attempt_time_sql",
    "available_at",
    "available_at_reads_on",
    "interval_factor_removed",
    "known_at",
    "objective_on",
    "objective_scores_on",
    "objective_tag",
    "projection_switches",
    "sensors_in_value_on",
    "self_report_not_validated_on",
    "validated_resolution_ids",
]

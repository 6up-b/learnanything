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

Router objective RO5's (§9; ``ROUTER_CALIBRATION_VERSIONS``, mvp-0.48): each arm is the tag, the objective
serving (the coin and the checks live in its frame; the open picks only need the tag) and its own rate:
:func:`stop_coin_rate` (0: no coin), :func:`check_mode` (``"embedded"``, ``"rate"`` or ``"off"``),
:func:`pick_open_share`; :func:`fitted_models_on` for RO4's follow-ups (§9 item 7).

Router objective RO6's (§10; ``ROUTER_LEARNED_TAIL_VERSIONS``, mvp-0.49): :func:`learned_tail_on` (the tag, the
objective serving and ``[router_objective] learned_tail``).

The follow-up batch's (``ROUTER_FOLLOWUPS_VERSIONS``, mvp-0.50): :func:`followup_on` (the tag, the objective serving
and the part's own ``[router_objective]`` switch).

:func:`projection_switches` is what a whole-vault rebuild's receipt records (the projection's defaults
snapshot, §5.5), so ``doctor`` can say when persisted due dates were derived under another setting.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from learnloop.algorithm_versions import (
    INTERVAL_FACTOR_VERSIONS,
    LESSON_OFFERS_VERSIONS,
    FAILURE_SHARE_VERSIONS,
    ROUTER_CALIBRATION_VERSIONS,
    ROUTER_FOLLOWUPS_VERSIONS,
    ROUTER_LEARNED_TAIL_VERSIONS,
    ROUTER_OBJECTIVE_VERSIONS,
)

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


def calibration_tag(config: Any) -> bool:
    """RO5 (§9): the vault is at the calibration successor (mvp-0.48) or later."""

    algorithms = getattr(config, "algorithms", None)
    return getattr(algorithms, "algorithm_version", None) in ROUTER_CALIBRATION_VERSIONS


def stop_coin_rate(config: Any) -> float:
    """RO5 §9 item 1: the stop coin's probability each way at a reversible boundary (0: no coin drawn)."""

    if not (calibration_tag(config) and objective_on(config)):
        return 0.0
    return float(getattr(getattr(config, "router_objective", None), "stop_coin", 0.0) or 0.0)


CHECKS_EMBEDDED = "embedded"
CHECKS_RATE = "rate"
CHECKS_OFF = "off"


def check_mode(config: Any) -> tuple[str, float]:
    """RO5 §9 item 2: ``(mode, value)``: ``("embedded", checks per day)``, ``("rate", per topic per day)`` or
    ``("off", 0)``. Below the tag or with the objective off, off."""

    section = getattr(config, "router_objective", None)
    if not (calibration_tag(config) and objective_on(config)):
        return CHECKS_OFF, 0.0
    rate = getattr(section, "check_rate", CHECKS_OFF)
    if rate == CHECKS_EMBEDDED:
        per_day = int(getattr(section, "embedded_checks_per_day", 0) or 0)
        return (CHECKS_EMBEDDED, float(per_day)) if per_day > 0 else (CHECKS_OFF, 0.0)
    if isinstance(rate, str) or float(rate) <= 0.0:
        return CHECKS_OFF, 0.0
    return CHECKS_RATE, float(rate)


def calibrated_weight_on(config: Any) -> bool:
    """RO5 §9 item 2 into §8.7: the randomized checks' comparison scores move ``w``. The check arm's own switch
    (Codex review F5): with ``check_rate = "off"`` the weight is RO4's calculation exactly, even after checks and
    scores accumulated."""

    return check_mode(config)[0] != CHECKS_OFF


def pick_open_share(config: Any) -> float:
    """RO5 §9 item 6: the seeded share of misconception picks left open (0 below the tag)."""

    if not calibration_tag(config):
        return 0.0
    return float(getattr(getattr(config, "router_objective", None), "pick_open_share", 0.0) or 0.0)


def fitted_models_on(config: Any) -> bool:
    """RO5 §9 item 7: the rollouts read AD's fitted learning posterior and the combiner fed resolved checks."""

    section = getattr(config, "router_objective", None)
    return calibration_tag(config) and objective_on(config) and bool(getattr(section, "fitted_models", False))


def learned_tail_tag(config: Any) -> bool:
    """RO6 (§10): the vault is at the learned tail's successor (mvp-0.49) or later."""

    algorithms = getattr(config, "algorithms", None)
    return getattr(algorithms, "algorithm_version", None) in ROUTER_LEARNED_TAIL_VERSIONS


def learned_tail_on(config: Any) -> bool:
    """RO6 (§10): the numeric policy values its candidates with the learned tail's residual (the tag, the
    objective serving and ``[router_objective] learned_tail``). Off, or below the tag, mvp-0.48 exactly: nothing
    is fitted, read or traced."""

    section = getattr(config, "router_objective", None)
    return learned_tail_tag(config) and objective_on(config) and bool(getattr(section, "learned_tail", False))


def followups_tag(config: Any) -> bool:
    """The router objective's follow-up batch: the vault is at its successor (mvp-0.50) or later."""

    algorithms = getattr(config, "algorithms", None)
    return getattr(algorithms, "algorithm_version", None) in ROUTER_FOLLOWUPS_VERSIONS


def followup_on(config: Any, key: str) -> bool:
    """One part of the follow-up batch serves: the tag, the objective serving and its own ``[router_objective]``
    switch ``key`` (default true). Off, or below the tag, that part is mvp-0.49's exactly."""

    section = getattr(config, "router_objective", None)
    return followups_tag(config) and objective_on(config) and bool(getattr(section, key, False))


def monotone_combiner_on(config: Any) -> bool:
    """The follow-up batch's landing ruling R6: the memory model's combiner is monotone in ability by construction
    (``memory.FORM_MONOTONE``), in its prior and its fit: the tag, the objective serving and ``[router_objective]
    monotone_combiner`` (a structural kill switch, default true); off, or below the tag, mvp-0.49's linear combiner."""

    return followup_on(config, "monotone_combiner")


#: The follow-up batch's landing ruling R8: its switches that change a logged decision's value or mixture, so each
#: is part of RO6's generator payload and flipping one is a change point, never a change of ``Q`` under the same
#: generator version. ``carried_in_prefetch`` is not here: it changes which transitions are valued, not the logger.
#: ``held_ad_link`` (router speed, item 1; Codex review F1 on it): like ``merged_sessions``, the same values per draw
#: but more draws within a deadline, so it changes the logger's values and is here too.
FOLLOWUP_GENERATOR_SWITCHES: tuple[str, ...] = (
    "combiner_trace_outcomes", "merged_sessions", "consistent_review_draw", "monotone_combiner", "ad_predictive_link",
    "scope_extension", "held_ad_link")


def followup_generator_switches(config: Any) -> dict[str, bool] | None:
    """R8: each of :data:`FOLLOWUP_GENERATOR_SWITCHES` as it serves (:func:`followup_on`) at the batch's tag; None
    below it, so a predecessor's generator payload (and its trace) keeps its bytes."""

    if not followups_tag(config):
        return None
    return {key: followup_on(config, key) for key in FOLLOWUP_GENERATOR_SWITCHES}


#: The follow-up batch's landing ruling R12: every switch of the batch, as part of the prefetch boundary key, so a
#: flip between a prefetch and its serve starts a new job (``carried_in_prefetch`` too: it changes what the job does
#: with its carried valuation, though not the logger's values).
FOLLOWUP_SWITCHES: tuple[str, ...] = (*FOLLOWUP_GENERATOR_SWITCHES, "carried_in_prefetch")


def followup_switch_snapshot(config: Any) -> dict[str, bool] | None:
    """R12: each of :data:`FOLLOWUP_SWITCHES` as it serves, at the batch's tag; None below it (the boundary key
    keeps its predecessor's bytes)."""

    if not followups_tag(config):
        return None
    return {key: followup_on(config, key) for key in FOLLOWUP_SWITCHES}


def lesson_offers_tag(config: Any) -> bool:
    """Teacher TE3b (spec_teacher_v1 rev 5 §15.1a): the vault is at the lesson offers' successor (mvp-0.53) or
    later."""

    algorithms = getattr(config, "algorithms", None)
    return getattr(algorithms, "algorithm_version", None) in LESSON_OFFERS_VERSIONS


def lesson_offers_on(config: Any) -> bool:
    """Teacher TE3b: lesson offers are candidates of the router objective, lesson minutes count on its clock and
    LOs with a pending lesson check join its population: the tag, the objective serving, TE1b's suggestions on
    (``router.lesson_suggestions.enabled`` with the router and its decision log, lessons able to open) and
    ``router.lesson_suggestions.in_objective``. Off, or below the tag, mvp-0.52 exactly."""

    if not (lesson_offers_tag(config) and objective_on(config)):
        return False
    router = getattr(config, "router", None)
    suggestions = getattr(router, "lesson_suggestions", None)
    teacher = getattr(config, "teacher", None)
    return bool(getattr(suggestions, "enabled", False) and getattr(suggestions, "in_objective", False)
                and getattr(router, "enabled", False) and getattr(router, "log_decisions", False)
                and getattr(teacher, "enabled", False))


def failure_share_tag(config: Any) -> bool:
    """Instruct hand-off IH5 (spec_instruct_handoff_v1 §7a): the vault is at the failure-share successor (mvp-0.55)
    or later."""

    algorithms = getattr(config, "algorithms", None)
    return getattr(algorithms, "algorithm_version", None) in FAILURE_SHARE_VERSIONS


def failure_share_to_other_policy_on(config: Any) -> bool:
    """IH5: a failed policy's share of the objective's mix goes to the other policy, not staged: the tag, the
    objective serving and ``[router_objective] failure_share_to_other_policy`` (default true). Off, or below the tag,
    mvp-0.54's mix exactly."""

    section = getattr(config, "router_objective", None)
    return failure_share_tag(config) and objective_on(config) and bool(
        getattr(section, "failure_share_to_other_policy", False))


def lessons_compete_with_followups_on(config: Any) -> bool:
    """IH2 (spec_instruct_handoff_v1 §5, the same unreleased tag as IH5): a lesson offer and a follow-up compete in one
    logged decision wherever a lesson is available: the tag, lesson offers on (:func:`lesson_offers_on`: the objective
    serving and TE1b's suggestions) and ``[router_objective] lessons_compete_with_followups`` (default true). Off, or
    below the tag, mvp-0.54's boundary exactly: forced items keep offers out and take a drawn one back."""

    section = getattr(config, "router_objective", None)
    return failure_share_tag(config) and lesson_offers_on(config) and bool(
        getattr(section, "lessons_compete_with_followups", False))


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
    "CHECKS_EMBEDDED",
    "CHECKS_OFF",
    "CHECKS_RATE",
    "available_at_reads_on",
    "calibrated_weight_on",
    "calibration_tag",
    "check_mode",
    "fitted_models_on",
    "FOLLOWUP_GENERATOR_SWITCHES",
    "FOLLOWUP_SWITCHES",
    "followup_generator_switches",
    "followup_switch_snapshot",
    "failure_share_tag",
    "failure_share_to_other_policy_on",
    "followup_on",
    "lessons_compete_with_followups_on",
    "lesson_offers_on",
    "lesson_offers_tag",
    "monotone_combiner_on",
    "followups_tag",
    "interval_factor_removed",
    "learned_tail_on",
    "learned_tail_tag",
    "pick_open_share",
    "stop_coin_rate",
    "known_at",
    "objective_on",
    "objective_scores_on",
    "objective_tag",
    "projection_switches",
    "sensors_in_value_on",
    "self_report_not_validated_on",
    "validated_resolution_ids",
]

"""Refusals and the follow-up gate's decision as decision records (ADR-017; refactor strategy §2.4, B5).

A refused request leaves no model call row (nothing was sent), and a Decider that was never asked leaves no ledger
row, so before these records "why did the hint not read my style?" or "why did the router fall back?" had no stored
answer. Each record names the rule that refused and the limit it refused at, as ids, numbers and codes:

* **decider_judgment**: a Decider judgment that gave no answer (``decider_judgments.decide`` and ``decide_many``,
  the hint chooser): ``excluded`` (its switch is off, the version is below it, no Decider is routed, the route is
  not ready, models are off), ``refused`` (a spend cap, named with its limit), ``timeout`` (a caller's time box) or
  ``failed`` (the request raised: the exception's class and ``module:function:line``, never its message). An
  answered judgment writes none: ``judgment_ledger`` holds it.
* **spend_admission**: the router's daily guard refused a metered request before it was sent: the cap, what the
  day had spent and what the request would add. The same kind for a shared daily envelope's refusal
  (``SharedDailyEnvelope``: the source service's, the hints', the figures', the Reader's caps; B8) and for the lesson
  envelope's refusal that closes a lesson with ``budget`` (B8).
* **figure_admission**: the figure gate refused a figure-derived request (figures switched off, the route, cap or
  price changed, the vault closed, a hold).
* **router_decision_row**: the router's ledger refused a decision row while the behaviour it describes still applied,
  or (B8) a plan decision's logger raised before its row reached the ledger (``failed``/``logger_error``).
* **followup_gate**: the follow-up gate's decision (``followup_run.router``): the arm, the rule (a hard refusal's
  reason, ``no_plan``, ``router_off``, or the component the mixture drew from), the arms' probabilities, and the
  components' answers by reference (their statuses here, their payloads on the ``router_decisions`` row).

Builders are pure; :func:`write` and :func:`write_on` never raise: a builder that fails or a record that cannot be
written logs a warning with the trace and the decision stands. Callers write after their decision is made, in the
transaction they already hold where there is one, so a router path never waits on the write lock for a record.
Nothing replays these records: the replay closure reaches this module (through ``decider_judgments``,
``db.stores.router`` and ``figure_admission``) only as a declared writer, and ``tests/test_provenance.py`` shows a
rebuild never calls it. It imports nothing of LearnLoop but the leaf, so the store layer can write through it.
"""

from __future__ import annotations

import hashlib
import logging
import math
from collections.abc import Callable, Mapping
from typing import Any

from learnloop import provenance
from learnloop.provenance import DecisionRecord

LOG = logging.getLogger(__name__)

DECIDER_JUDGMENT = "decider_judgment"
SPEND_ADMISSION = "spend_admission"
FIGURE_ADMISSION = "figure_admission"
ROUTER_DECISION_ROW = "router_decision_row"
FOLLOWUP_GATE = "followup_gate"

# -- rules ------------------------------------------------------------------------------------------------------
#: The judgment's ``[decider_routes]`` switch is off.
SWITCH_OFF = "switch_off"
#: The vault's algorithm version is below the one the judgment is live at.
BELOW_VERSION = "below_version"
#: The task is no Tier-1 judgment (the router's own Decider, a typo).
NOT_A_DECIDER_TASK = "not_a_decider_task"
#: The route names no Decider profile (manual, empty, or a profile the config does not have).
NO_DECIDER_ROUTED = "no_decider_routed"
#: The route names a Decider profile that is not ready (no key, unreachable at setup).
DECIDER_NOT_READY = "decider_not_ready"
#: The models-off switch of the environment.
MODELS_OFF = "models_off"
#: The provider said it is unavailable during the request.
PROVIDER_UNAVAILABLE = "provider_unavailable"
#: The request raised anything else.
REQUEST_FAILED = "request_failed"
#: The caller's time box ran out.
TIME_BOX = "time_box"
#: A spend refusal that named no rule of its own.
SPEND_REFUSED = "spend_refused"
#: The router's daily guard (``router.max_daily_cost_usd``).
ROUTER_DAILY_CAP = "router_daily_cap"
#: A plan decision's logger raised before its row reached the ledger (the block stands, unlogged).
LOGGER_ERROR = "logger_error"
#: A shared daily envelope's cap (``SpendEnvelope``'s own rule name, kept for the shared one).
ENVELOPE_CAP = "envelope_cap"


def _ref(value: Any) -> str | None:
    """An id as a record keeps it: itself, or a short hash of one that is not a code (vault ids are free-form, and
    one odd id must not drop the whole record)."""

    if value is None or value == "":
        return None
    text = str(value)
    if provenance.is_code(text):
        return text
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def _code(value: Any) -> str | None:
    return value if provenance.is_code(value) else None


def _number(value: Any) -> float | int | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return value if math.isfinite(float(value)) else None


def _compact(values: Mapping[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in values.items() if value is not None and value != {}}


def _clean(value: Any) -> Any:
    """A caller's fact as a record keeps it: numbers and flags as they are, strings as ids (hashed when not a code),
    lists and maps element by element; anything else dropped."""

    if value is None or isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return _number(value)
    if isinstance(value, str):
        return _ref(value)
    if isinstance(value, Mapping):
        return {str(key): _clean(item) for key, item in value.items() if provenance.is_code(str(key))}
    if isinstance(value, (list, tuple)):
        return [_clean(item) for item in value]
    return None


def _error(exc: BaseException | None) -> tuple[str | None, str | None]:
    if exc is None:
        return None, None
    where = provenance.where(exc)
    # ``<lambda>`` or ``<listcomp>`` would fail the record's code check; the frame stays findable without brackets.
    if where is not None:
        where = "".join(char if char.isalnum() or char in "_.:/-" else "_" for char in where)[:160]
    return _code(type(exc).__name__), where


# -- what refused -------------------------------------------------------------------------------------------------


def spend_rule(exc: BaseException) -> tuple[str, dict[str, Any]]:
    """The rule a spend refusal names (``SpendLimitExceeded.rule``) and its numbers, as a record's facts."""

    rule = _code(getattr(exc, "rule", None)) or SPEND_REFUSED
    return rule, _compact({
        "limit": _number(getattr(exc, "limit", None)), "used": _number(getattr(exc, "used", None)),
        "requested": _number(getattr(exc, "requested", None)), "scope": _ref(getattr(exc, "scope", None)),
    })


def route_rule(provider_name: str | None, providers: Mapping[str, Any] | None) -> tuple[str, str | None]:
    """Why a route gave no ready Decider, from what it names (no client is built): no profile routed (manual, empty, or
    a profile the config does not have), or one routed that is not ready; and the profile's name."""

    if not provider_name or provider_name == "manual" or provider_name not in (providers or {}):
        return NO_DECIDER_ROUTED, _ref(provider_name)
    return DECIDER_NOT_READY, _ref(provider_name)


def disabled_rule(config: Any, task: str, *, serving_tasks: tuple[str, ...], content_tasks: tuple[str, ...]) -> str:
    """Why ``decider_judgments.enabled`` said no, in its own order: not a judgment, its switch, its version."""

    if task not in serving_tasks and task not in content_tasks:
        return NOT_A_DECIDER_TASK
    if not bool(getattr(getattr(config, "decider_routes", None), task, False)):
        return SWITCH_OFF
    return BELOW_VERSION


# -- builders (pure) ----------------------------------------------------------------------------------------------


def decider_record(*, status: str, rule: str, route: str, task: str, ledger_task: str | None = None,
                   left_kind: str | None = None, left_id: Any = None, input_hash: Any = None, model: Any = None,
                   judgment_id: str | None = None, detail_table: str = "judgment_ledger",
                   facts: Mapping[str, Any] | None = None, versions: Mapping[str, Any] | None = None,
                   error: BaseException | None = None, subject_kind: str | None = None,
                   subject_id: Any = None) -> DecisionRecord:
    """A Decider judgment with no answer: ``status`` and ``rule`` say why, ``facts`` the limit that refused."""

    error_type, error_where = _error(error)
    kind_of_left = _code(left_kind)
    if subject_kind is None and kind_of_left in provenance.SUBJECT_KINDS:
        subject_kind, subject_id = kind_of_left, left_id
    return DecisionRecord(
        kind=DECIDER_JUDGMENT,
        status=status,
        subject_kind=_code(subject_kind) if subject_id is not None else None,
        subject_id=_ref(subject_id),
        decided_by=_code(route) or "decider",
        rule=_code(rule) or REQUEST_FAILED,
        facts=_compact({
            "task": _code(task), "ledger_task": _code(ledger_task) if ledger_task != task else None,
            "route": _code(route), "left_kind": kind_of_left, "left_id": _ref(left_id),
            "input_hash": _ref(input_hash), "model": _ref(model) if model not in (None, "unavailable") else None,
            **{str(key): _clean(value) for key, value in dict(facts or {}).items()},
        }),
        versions=_compact({str(key): _clean(value) for key, value in dict(versions or {}).items()}),
        detail_table=detail_table if judgment_id else None,
        detail_id=_ref(judgment_id),
        error_type=error_type,
        error_where=error_where,
    )


def router_spend_record(*, cap_usd: Any, spent_usd: Any, request_usd: Any, owner_kind: Any, owner_id: Any,
                        event: Mapping[str, Any]) -> DecisionRecord:
    """The router's daily guard refused a metered request: no receipt is written, so this is the only row."""

    return DecisionRecord(
        kind=SPEND_ADMISSION,
        status="refused",
        decided_by="router_daily_guard",
        rule=ROUTER_DAILY_CAP,
        facts=_compact({
            "limit_usd": _number(cap_usd), "spent_usd": _number(spent_usd), "request_usd": _number(request_usd),
            "owner_kind": _code(owner_kind), "boundary_key": _ref(owner_id), "purpose": _code(event.get("purpose")),
            "provider": _ref(event.get("provider")), "model": _ref(event.get("model")),
        }),
    )


def envelope_record(*, envelope: Any, cap_usd: Any, spent_usd: Any, request_usd: Any,
                    owner_kinds: Any = None) -> DecisionRecord:
    """A shared daily cap (``source_service.max_daily_cost_usd``, ``hints.max_daily_cost_usd``, the figures', the
    Reader's, ...) refused a metered request before it was sent: no call row exists, and each caller turns the
    refusal into its own status (``over_budget``, ``capped``, an empty result), so this is the row that names the
    cap, the day's total and the request's estimate."""

    kinds = [kind for kind in (owner_kinds or ()) if provenance.is_code(kind)]
    return DecisionRecord(
        kind=SPEND_ADMISSION,
        status="refused",
        decided_by=_code(envelope) or "shared_daily_envelope",
        rule=ENVELOPE_CAP,
        facts=_compact({
            "limit_usd": _number(cap_usd), "spent_usd": _number(spent_usd), "request_usd": _number(request_usd),
            "scope": _code(envelope), "owner_kinds": kinds or None,
        }),
    )


def lesson_budget_record(*, lesson_id: Any, exc: BaseException | None, refusal: Mapping[str, Any] | None
                         ) -> DecisionRecord:
    """A lesson's own envelope (or a cap below it) refused its next request, so the lesson closed with ``budget``:
    the close receipt says ``budget``, and this names which request (its purpose), the rule and the numbers."""

    seen, spend = exc, None
    while seen is not None and spend is None:
        if getattr(seen, "rule", None) is not None or type(seen).__name__ == "SpendLimitExceeded":
            spend = seen
        seen = seen.__cause__ or seen.__context__
    rule, facts = spend_rule(spend) if spend is not None else (SPEND_REFUSED, {})
    gate = dict(refusal or {})
    if spend is None and gate.get("reason") == "unknown_price":
        rule = "unknown_price"
    lesson = _ref(lesson_id)
    return DecisionRecord(
        kind=SPEND_ADMISSION,
        status="refused",
        # ``why lesson:<id>`` finds records by subject only.
        subject_kind="lesson" if lesson else None,
        subject_id=lesson,
        decided_by="lesson_envelope",
        rule=rule,
        facts=_compact({
            **facts, "lesson_id": _ref(lesson_id), "purpose": _code(gate.get("purpose")),
            "provider": _ref(gate.get("provider")), "request_usd": _number(gate.get("request_estimate_usd")),
            "committed_usd": _number(gate.get("committed_usd")), "limit_usd": _number(gate.get("limit_usd")),
        }),
    )


def figure_gate_record(*, rule: str, purpose: Any) -> DecisionRecord:
    """The figure gate refused a figure-derived request; every later request of the unit is refused with it."""

    return DecisionRecord(
        kind=FIGURE_ADMISSION, status="refused", decided_by="figures_gate", rule=_code(rule) or "refused",
        facts=_compact({"purpose": _code(purpose)}),
    )


def router_row_record(row: Mapping[str, Any], exc: BaseException) -> DecisionRecord:
    """The ledger refused a router decision row; the caller's behaviour applies all the same (``applied``)."""

    error_type, error_where = _error(exc)
    rule = "unregistered_design" if isinstance(exc, ValueError) else (
        "constraint_failed" if type(exc).__name__ == "IntegrityError" else "storage_error")
    return DecisionRecord(
        kind=ROUTER_DECISION_ROW,
        status="refused",
        subject_kind="decision",
        subject_id=_ref(row.get("id")),
        decided_by="router_ledger",
        rule=rule,
        facts=_compact({
            "decision_kind": _code(row.get("decision_kind")), "receipt_key": _ref(row.get("receipt_key")),
            "design": _ref(row.get("design")), "policy": _code(row.get("policy")), "applied": True,
        }),
        versions=_compact({"algorithm_version": _code(row.get("algorithm_version")),
                           "log_version": _code(row.get("log_version"))}),
        detail_table="router_decisions",
        error_type=error_type,
        error_where=error_where,
    )


def plan_logger_record(*, decision_kind: str, block_id: Any, plan_id: Any, logger: Any, exc: BaseException,
                       logged_ref: Any = None) -> DecisionRecord:
    """A plan decision's logger raised: the block it describes is served all the same, with no ledger row (or, for a
    follow-up's interrupt, with a row whose linked rows stopped at ``logged_ref``). Before this the warning line was
    the only trace that the block's ``router_decisions`` row was missing, and why."""

    error_type, error_where = _error(exc)
    return DecisionRecord(
        kind=ROUTER_DECISION_ROW,
        status="failed",
        subject_kind="block" if block_id else None,
        subject_id=_ref(block_id),
        decided_by="plan_decision_logger",
        rule=LOGGER_ERROR,
        facts=_compact({
            "decision_kind": _code(decision_kind), "plan_id": _ref(plan_id),
            "logger": _code(getattr(logger, "__name__", logger)), "logged_ref": _ref(logged_ref), "applied": True,
        }),
        detail_table="router_decisions",
        detail_id=_ref(logged_ref),
        error_type=error_type,
        error_where=error_where,
    )


def followup_gate_record(row: Mapping[str, Any], decision: Any, *, logged: bool, retry: bool = False,
                         value_check_error: BaseException | None = None) -> DecisionRecord:
    """The follow-up gate's decision for one workflow: what it chose, the rule, the arms, the components' answers."""

    record = dict(getattr(decision, "record", None) or {})
    mixture = record.get("mixture") if isinstance(record.get("mixture"), Mapping) else {}
    chosen = str(getattr(decision, "chosen_ref", "") or "")
    decided_by = str(getattr(decision, "decided_by", "") or "")
    refused = bool(getattr(decision, "refused", False))
    reason = str(getattr(decision, "reason", "") or "")
    drawn = mixture.get("drawn_component") or record.get("drawn_component")
    if refused or decided_by in {"no_plan", "staged", "recorded"}:
        rule = reason
    elif drawn:
        rule = f"drawn_{drawn}"
    else:
        rule = decided_by or reason
    pi = mixture.get("pi") if isinstance(mixture.get("pi"), Mapping) else {}
    alternatives = tuple(
        _compact({"ref": _ref(option), "p": _number(p), "lost_by": "not_drawn"})
        for option, p in pi.items() if str(option) != chosen
    )
    models = mixture.get("models") if isinstance(mixture.get("models"), Mapping) else {}
    components = {str(name): _code((summary or {}).get("status")) or "unknown"
                  for name, summary in models.items() if _code(str(name))}
    observational = getattr(decision, "observational", None) or {}
    error_type, error_where = _error(value_check_error)
    decision_id = getattr(decision, "decision_id", None)
    refusal_reasons = [_code(str(item.get("reason"))) for item in getattr(decision, "refusals", ()) or ()
                       if isinstance(item, Mapping)]
    return DecisionRecord(
        kind=FOLLOWUP_GATE,
        status="refused" if refused else "chosen",
        subject_kind="attempt" if row.get("source_attempt_id") else None,
        subject_id=_ref(row.get("source_attempt_id")),
        chosen_ref=_ref(chosen),
        decided_by=_code(decided_by) or "unknown",
        rule=_code(rule) or _ref(rule) or "unknown",
        alternatives=alternatives,
        facts=_compact({
            "workflow_id": _ref(row.get("id")), "learning_object_id": _ref(row.get("learning_object_id")),
            "factor_id": _ref(row.get("factor_id")), "plan_id": _ref(getattr(decision, "plan_id", None)),
            "block_id": _ref(getattr(decision, "block_id", None)),
            "propensity": _number(getattr(decision, "propensity", None)),
            "wait_feasible": bool(getattr(decision, "wait_feasible", True)),
            "logged": bool(logged), "retry": True if retry else None,
            "boundary_key": _ref(mixture.get("boundary_key")),
            "components": components or None,
            "fallback": _code(record.get("fallback")),
            "refusals": [reason for reason in refusal_reasons if reason] or None,
            "lesson_offer": True if getattr(decision, "lesson_offer", False) else None,
            # The value checks that log and do not decide (§5 item 5): their answer, or that they failed (S14).
            "value_check": "failed" if value_check_error is not None else _code(observational.get("decide_probe")),
            "value_check_error_type": error_type, "value_check_error_where": error_where,
        }),
        versions=_compact({
            "policy": _code(record.get("policy")), "design": _code(record.get("design")),
            "seed": _ref(record.get("seed")), "why_version": _code(record.get("why_version")),
            "question_set_version": _code(record.get("question_set_version")),
        }),
        detail_table="router_decisions" if decision_id else None,
        detail_id=_ref(decision_id),
    )


# -- writing (never raises) ---------------------------------------------------------------------------------------


def built(kind: str, build: Callable[[], DecisionRecord]) -> DecisionRecord | None:
    try:
        return build()
    except Exception as exc:  # noqa: BLE001 - a record never changes the decision it describes
        LOG.warning("decision record %r not built (trace %s): %s", kind, provenance.current_trace(),
                    type(exc).__name__)
        LOG.debug("decision record %r not built", kind, exc_info=True)
        return None


def write(repository: Any, kind: str, build: Callable[[], DecisionRecord]) -> str | None:
    """Build and write one record through ``repository`` (joining its open transaction without committing it, else a
    short one of its own); its id, or None. Never raises.

    The same write as ``db.stores.provenance.write_decision`` (both are the leaf's :func:`provenance.write_through`):
    ``db.stores.router`` writes through this module, so importing the store back would close a package cycle.
    """

    record = built(kind, build)
    if record is None:
        return None
    return provenance.write_through(repository, record)


def write_on(connection: Any, kind: str, build: Callable[[], DecisionRecord]) -> str | None:
    """Build and write one record on ``connection``, inside the transaction the caller holds; never raises."""

    record = built(kind, build)
    if record is None:
        return None
    return provenance.write(connection, record)


__all__ = [
    "BELOW_VERSION", "DECIDER_JUDGMENT", "DECIDER_NOT_READY", "ENVELOPE_CAP", "FIGURE_ADMISSION", "FOLLOWUP_GATE",
    "LOGGER_ERROR", "MODELS_OFF", "NOT_A_DECIDER_TASK", "NO_DECIDER_ROUTED", "PROVIDER_UNAVAILABLE", "REQUEST_FAILED",
    "ROUTER_DAILY_CAP", "ROUTER_DECISION_ROW", "SPEND_ADMISSION", "SPEND_REFUSED", "SWITCH_OFF", "TIME_BOX",
    "decider_record", "disabled_rule", "envelope_record", "figure_gate_record", "followup_gate_record",
    "lesson_budget_record", "plan_logger_record", "route_rule", "router_row_record", "router_spend_record",
    "spend_rule", "built", "write", "write_on",
]

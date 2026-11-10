"""A plan boundary's decision records (ADR-017; refactor strategy §3.6, case 1): what was chosen, what each model said.

Built by a pure function from what the boundary already holds (the decision, the chooser's record, what the router
saw), and written by the container in the block's own transaction (``engine._boundary``, ``engine._close``), after
the decision is made. So a record never changes what is served, and never waits on the write lock by itself: a router
path with a deadline has already decided when it writes.

* **plan_block**, one per boundary decision the container persists: ``chosen``, or ``fallback`` with the rule that
  made it (``chooser_error``, ``not_offered``, ``continue_current_at_boundary``, a malformed choice). It names the
  support with each option's probability and why it lost, the configured waits and how long the decision waited,
  the boundary key, the trace that started the prefetch, and the versions and seed. A chooser's exception adds its
  type and ``module:function:line``, never its message.
* **model_answer**, one per component of the decision (the Decider, the LLM, the numeric policy, the staged rule),
  a child of the plan_block: ``chosen`` when it answered in time (its answer entered the decision, or was logged as
  advice), ``timeout`` when it was still out at the decision, ``failed``, ``refused`` (the spend guard), ``excluded``
  (not set up), or ``discarded`` when a chooser's exception threw its answer away.

A late answer needs no write of its own: a plan_block's ``created_at`` is the wall time the answers were taken, and
``why`` lists the receipts of its traces that finished after it.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import replace
from datetime import datetime, timezone
import hashlib
import math
import re
from typing import Any

from learnloop import provenance
from learnloop.provenance import DecisionRecord

PLAN_BLOCK = "plan_block"
MODEL_ANSWER = "model_answer"
#: The attribute a chooser's exception carries the router's view on (``router_runtime.note_failure``): the chooser's
#: own record dies with the exception, and the container's fallback record is the only place its models can go.
FAILURE_NOTE = "learnloop_router_seen"

#: A component's status (``router_runtime``) as a record's.
_STATUS = {"answered": "chosen", "timeout": "timeout", "failed": "failed", "invalid": "failed",
           "unreachable": "failed", "spend": "refused", "not_ready": "excluded"}
#: Who answered, as ``decided_by``: the AI route for a model, the policy otherwise.
_DECIDED_BY = {"llm": "router_llm", "decider": "router_decider", "numeric": "numeric_policy", "staged": "staged_rule"}
#: The exception class at the head of a component's error ("TimeoutError: ..."), never what follows it.
_ERROR_TYPE = re.compile(r"(?:^|: )([A-Z][A-Za-z0-9_]{0,79})(?::|$)")
_NOT_CODE = re.compile(r"[^A-Za-z0-9_.:/@+#=\-]")


def wall_now() -> str:
    """The wall clock in the receipts' format (``ai.execution``): a record's time is compared with theirs."""

    return datetime.now(timezone.utc).isoformat()


def ref(value: Any) -> str | None:
    """An option's id as a record keeps it: the id itself, or a short hash of one that isn't a code (a space in a
    vault's id would otherwise drop the whole record)."""

    if value is None:
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


def _where(value: Any) -> str | None:
    # ``<lambda>`` or ``<listcomp>`` would fail the record's code check; the frame stays findable without the brackets.
    return _NOT_CODE.sub("_", value)[:160] if isinstance(value, str) and value else None


def _error_type(error: Any) -> str | None:
    match = _ERROR_TYPE.search(error) if isinstance(error, str) else None
    return match.group(1) if match else None


def _compact(values: Mapping[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in values.items() if value is not None}


def _favoured(distribution: Mapping[str, Any]) -> str | None:
    numbers = {key: float(value) for key, value in distribution.items() if _number(value) is not None}
    if not numbers:
        return None
    top = max(numbers.values())
    leaders = [key for key, value in numbers.items() if value >= top - 1e-12]
    return leaders[0] if len(leaders) == 1 else None


#: Ids kept in a list fact; the rest are only counted.
IDS_KEPT = 10


def forced_entry(item_id: Any, *, origin: Any, workflow: Mapping[str, Any] | None) -> dict[str, Any]:
    """One forced item as a record names it: its id and origin, and its follow-up workflow, source attempt and state
    when a workflow holds it (a follow-up from a recorded need has none)."""

    workflow = workflow or {}
    return _compact({
        "ref": ref(item_id),
        "origin": _code(origin),
        "workflow": ref(workflow.get("id")),
        "source_attempt": ref(workflow.get("source_attempt_id")),
        "workflow_state": _code(workflow.get("state")),
        "workflow_decision": ref(workflow.get("decision_id")),
    })


def forced_facts(entries: Any) -> dict[str, Any]:
    """The forced items' ids, workflows and source attempts as lists (capped), and how many there were."""

    entries = [dict(entry) for entry in entries or ()]
    if not entries:
        return {}
    attempts = sorted({entry["source_attempt"] for entry in entries if entry.get("source_attempt")})
    return _compact({
        "forced_n": len(entries),
        "forced": [entry["ref"] for entry in entries[:IDS_KEPT] if entry.get("ref")] or None,
        "workflows": [entry["workflow"] for entry in entries[:IDS_KEPT] if entry.get("workflow")] or None,
        "source_attempts": attempts[:IDS_KEPT] or None,
        "forced_origin": next((entry["origin"] for entry in entries if entry.get("origin")), None),
    })


_forced = forced_facts


def _superseding(value: Any) -> dict[str, Any]:
    """IH2's contest: the open offer this decision replaces (its block and its decision)."""

    if not isinstance(value, Mapping):
        return {}
    return _compact({"superseding_offer_block": ref(value.get("block_id")),
                     "superseding_offer_decision": ref(value.get("decision_id"))})


def plan_block_records(decision: Any, *, block_id: str, detail_id: str | None, config: Any, stop: bool,
                       trace_id: str | None = None, parent_id: str | None = None,
                       trigger_attempt: str | None = None) -> list[DecisionRecord]:
    """A boundary decision's plan_block record, its components' model_answer records and any failed step's record,
    oldest first.

    ``decision`` is ``engine.Decision``; ``block_id`` the block (or a stop's receipt) it placed; ``detail_id`` the
    router's ``plan_block`` row, when one was logged. All records share one trace, the serving request's.
    ``parent_id``: the record that caused this boundary (an offer taken back for forced items, or the triggering
    attempt's record); ``trigger_attempt``: the newest attempt as of the decision, the one its boundary key names.
    ``decision.seen`` may add the forced items (``forced``), an offer this decision replaces (``superseding``) and the
    steps that failed before it (``failures``).
    """

    router = dict(decision.router_record or {})
    mixture = dict(router.get("mixture") or {})
    seen = dict(decision.seen or {})
    choice = decision.choice
    trace = trace_id or provenance.current_trace() or provenance.new_trace_id()
    decided_at = seen.get("decided_wall") or wall_now()
    crashed = decision.fallback_reason == "chooser_error"
    chosen = choice.candidate_id
    pi = dict(mixture.get("pi") or {})
    support = [str(option) for option in mixture.get("support") or ()]
    fallback_from = decision.fallback_from if decision.fallback and not crashed else None

    alternatives: list[dict[str, Any]] = []
    if fallback_from is not None and fallback_from != chosen:
        alternatives.append({"ref": ref(fallback_from), "lost_by": _code(decision.fallback_reason)})
    taken = {chosen, *(item["ref"] for item in alternatives)}
    for option in support:
        if option not in taken:
            alternatives.append(_compact({"ref": ref(option), "p": _number(pi.get(option)), "lost_by": "not_drawn"}))
            taken.add(option)
    feasible_ids = [candidate.candidate_id for candidate in decision.feasible]
    for option in feasible_ids:
        if option not in taken:
            alternatives.append({"ref": ref(option), "lost_by": "outside_support" if support else "not_chosen"})
            taken.add(option)
    for candidate in decision.candidates:
        if candidate.candidate_id not in taken:
            alternatives.append({"ref": ref(candidate.candidate_id), "lost_by": "infeasible"})
            taken.add(candidate.candidate_id)

    timeouts = {"timeout_s": _number(config.router.timeout_seconds),
                "prefetch_timeout_s": _number(config.router.prefetch_timeout_seconds)}
    waited_ms = _number(mixture.get("waited_ms")) if "waited_ms" in mixture else _number(seen.get("waited_ms"))
    model_ids = dict(router.get("model_ids") or {})
    block = DecisionRecord(
        kind=PLAN_BLOCK,
        status="fallback" if decision.fallback else "chosen",
        subject_kind="block",
        subject_id=block_id,
        chosen_ref=ref(chosen),
        decided_by="lane_quota" if decision.fallback else _code(router.get("decided_by") or choice.chosen_by),
        rule=_code(decision.fallback_reason) if decision.fallback else _code(router.get("why_code")),
        alternatives=tuple(alternatives),
        facts=_compact({
            "stop": bool(stop),
            "stop_offered": bool(decision.stop_offered),
            "propensity": _number(choice.propensity),
            "feasible_n": len(feasible_ids),
            "candidates_n": len(decision.candidates),
            **timeouts,
            "waited_ms": waited_ms,
            "may_defer": seen.get("may_defer"),
            "boundary_key": _code(mixture.get("boundary_key") or seen.get("boundary_key")),
            "prefetch_trace": _code(seen.get("prefetch_trace")),
            "chooser_decided_by": _code(router.get("decided_by")) if decision.fallback else None,
            "drawn_component": _code(mixture.get("drawn_component") or router.get("drawn_component")),
            "mix_fallback": _code(router.get("fallback")),
            "option_count": _number(router.get("option_count")),
            "card_error": _code(router.get("card_error")),
            "trigger_attempt": ref(trigger_attempt),
            **_forced(seen.get("forced") or ()),
            **_superseding(seen.get("superseding")),
        }),
        versions=_compact({
            "algorithm_version": _code(getattr(config.algorithms, "algorithm_version", None)),
            "policy": _code(router.get("policy")),
            "design": _code(router.get("design")),
            "seed": _code(router.get("seed")),
            "why_version": _code(router.get("why_version")),
            "question_set_version": _code(router.get("question_set_version")),
            "llm_schema_version": _code(model_ids.get("llm_schema_version")),
        }),
        detail_table="router_decisions" if detail_id else None,
        detail_id=detail_id,
        error_type=_code(seen.get("error_type")) if crashed else None,
        error_where=_where(seen.get("error_where")) if crashed else None,
        parent_id=parent_id,
        trace_id=trace,
        id=provenance.new_record_id(),
        created_at=decided_at,
    )
    records = [block]
    records += component_records(block, router, mixture, timeouts=timeouts, waited_ms=waited_ms, crashed=crashed,
                                 models=seen.get("models"))
    # Refactor B3: the boundary's steps that failed before its decision (the day's check, the lesson offer's builder),
    # as its children.
    for failure in seen.get("failures") or ():
        records.append(replace(failure, parent_id=block.id, trace_id=block.trace_id, subject_kind=block.subject_kind,
                               subject_id=block.subject_id, created_at=block.created_at, id=failure.id or provenance.new_record_id()))
    return records


def component_records(block: DecisionRecord, router: Mapping[str, Any], mixture: Mapping[str, Any], *,
                      timeouts: Mapping[str, Any], waited_ms: Any, crashed: bool,
                      models: Mapping[str, Any] | None = None) -> list[DecisionRecord]:
    """One ``model_answer`` per component of ``block``'s decision (the Decider, the LLM, the numeric policy, the staged
    rule), from the router's record of it: a plan block's (B2) or a follow-up's ``plan_interrupt`` (B3)."""

    records: list[DecisionRecord] = []
    models = mixture.get("models") or router.get("models") or models or {}
    distributions = dict(router.get("model_distributions") or {})
    # A component that failed or timed out reports no model of its own; the route as the decision logged it does.
    route_models = dict(router.get("model_ids") or {})
    drawn = mixture.get("drawn_component") or router.get("drawn_component")
    for name, summary in sorted(models.items()):
        summary = dict(summary or {})
        raw = str(summary.get("status") or "")
        status = "discarded" if crashed and raw == "answered" else _STATUS.get(raw, "failed")
        distribution = dict(distributions.get(name) or {})
        favoured = mixture.get("numeric_choice") if name == "numeric" else _favoured(distribution)
        model, provider = _code(summary.get("model")), _code(summary.get("provider"))
        model_basis = "answer" if model else None
        if model is None and _code(route_models.get(name)):
            model, model_basis = _code(route_models.get(name)), "route_at_decision"
        asked = name in {"llm", "decider"}
        records.append(_answer(
            name, status=status, raw=raw, chosen_ref=favoured, block=block, distribution=distribution,
            facts={"latency_ms": _number(summary.get("latency_ms")), "cost_usd": _number(summary.get("cost_usd")),
                   "subscription": summary.get("subscription") if isinstance(summary.get("subscription"), bool)
                   else None, "drew": drawn == name if drawn else None, **timeouts, "waited_ms": waited_ms,
                   "reason": _code(summary.get("error")) if raw == "not_ready" else None,
                   "discarded_by": "chooser_error" if status == "discarded" else None,
                   "model_basis": (model_basis or "not_stored") if asked else None,
                   "provider_basis": ("answer" if provider else "not_stored") if asked else None},
            versions={"model": model, "provider": provider},
            error_type=_error_type(summary.get("error")) if status in {"failed", "timeout"} else None,
        ))
    if mixture.get("staged_ref") is not None:
        records.append(_answer(
            "staged", status="chosen", raw="answered", chosen_ref=mixture.get("staged_ref"), block=block,
            distribution={}, facts={"drew": drawn == "staged" if drawn else None}, versions={}, error_type=None,
        ))
    return records


def _answer(name: str, *, status: str, raw: str, chosen_ref: Any, block: DecisionRecord,
            distribution: Mapping[str, Any], facts: Mapping[str, Any], versions: Mapping[str, Any],
            error_type: str | None) -> DecisionRecord:
    return DecisionRecord(
        kind=MODEL_ANSWER,
        status=status,
        subject_kind=block.subject_kind,
        subject_id=block.subject_id,
        chosen_ref=ref(chosen_ref),
        decided_by=_DECIDED_BY.get(name, _code(name)),
        rule=_code(raw) or "unknown",
        alternatives=tuple(_compact({"ref": ref(option), "p": _number(p)}) for option, p in distribution.items()),
        facts=_compact({"component": _code(name), **facts}),
        versions=_compact(versions),
        detail_table=block.detail_table,
        detail_id=block.detail_id,
        error_type=error_type,
        parent_id=block.id,
        trace_id=block.trace_id,
        created_at=block.created_at,
    )


__all__ = ["FAILURE_NOTE", "IDS_KEPT", "MODEL_ANSWER", "PLAN_BLOCK", "component_records", "forced_entry",
           "forced_facts", "plan_block_records", "ref", "wall_now"]

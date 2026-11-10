"""The plan's decision records besides its blocks (ADR-017; refactor strategy §3.6, case 2): an offer taken back, a
follow-up held or let in, and a boundary step that failed and left the rest of the boundary to decide.

Each builder is pure: it returns :class:`~learnloop.provenance.DecisionRecord` values from what its caller already
holds, and never writes. The callers write them in the transaction of the act they describe, after it is decided, so a
record never changes what is served:

* **offer_withdrawn** (``withdrawn``): an unanswered lesson offer the plan took back (``forced_items``, ``offers_off``,
  ``never_shown``) or a newer decision replaced (``superseded_by_decision``, IH2's contest). It names the forced items,
  their follow-up workflows and source attempts, and its parent is the offer's own ``plan_block``. The next boundary's
  ``plan_block`` names it as its parent, so "what took the offer's place" is one hop.
* **plan_interrupt** (``chosen``, ``deferred``, ``refused``): the restraint gate's decision on one mid-block follow-up:
  what was let in, made to wait or refused, by which rule, with the gate's support and its components' answers.
* **randomized_check** and **lesson_offer_build** (``failed``): a boundary step that raised (the day's check draw or
  placement, the lesson offer's builder). The boundary decides without it; the record is the boundary's child.
* **ad_slot** (``fallback``): adaptive difficulty was unavailable for a slot or the day's deferrals, so the incumbent
  decided, with AD's failure code and, when its guard refused something, what it refused (verb, table, reader).
* **serve_eligibility** (``excluded``, ``fallback``): a planned cold check the serve could not take cold: displaced,
  or served as ordinary practice. A plain serve has no record: the presentation row is its record.

Ids that aren't codes are hashed (``boundary_records.ref``); a refusal's prose is never kept, only its codes.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import replace
from typing import Any

from learnloop import provenance
from learnloop.daily_plan.boundary_records import (
    IDS_KEPT, MODEL_ANSWER, component_records, forced_entry, forced_facts, ref, wall_now,
)
from learnloop.provenance import DecisionRecord

OFFER_WITHDRAWN = "offer_withdrawn"
PLAN_INTERRUPT = "plan_interrupt"
RANDOMIZED_CHECK = "randomized_check"
LESSON_OFFER_BUILD = "lesson_offer_build"
AD_SLOT = "ad_slot"
SERVE_ELIGIBILITY = "serve_eligibility"

#: A boundary step's failure rules.
CHECK_DRAW_ERROR = "draw_error"
CHECK_PLACE_ERROR = "place_error"
BUILDER_ERROR = "builder_error"
#: The rule of the day's check block (placed by the rules before the boundary's decision).
CHECK_BLOCK_RULE = "ro5_randomized_check"
#: Who decides when AD is unavailable, and who takes an offer back.
INCUMBENT = "incumbent"
PLAN = "plan"

_NUMBER = (int, float)


def _code(value: Any) -> str | None:
    return value if provenance.is_code(value) else None


def _number(value: Any) -> float | int | None:
    if isinstance(value, bool) or not isinstance(value, _NUMBER):
        return None
    return value if float(value) == float(value) and abs(float(value)) != float("inf") else None


def _compact(values: Mapping[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in values.items() if value is not None and value != [] and value != {}}


def _refs(values: Iterable[Any], *, limit: int = IDS_KEPT) -> list[str]:
    out = [ref(value) for value in values if value is not None]
    return [value for value in out[:limit] if value is not None]


def offer_withdrawn(*, why: str, block_id: Any, offer_decision_id: Any, forced: Sequence[Mapping[str, Any]] = (),
                    superseded_by: Any = None, shown_on: Any = None, expired_row: bool | None = None,
                    parent_id: str | None = None, record_id: str | None = None) -> DecisionRecord:
    """An unanswered offer taken back by the plan, or replaced by a newer decision (``superseded_by``)."""

    offer = ref(offer_decision_id)
    return DecisionRecord(
        kind=OFFER_WITHDRAWN,
        status="withdrawn",
        subject_kind="offer" if offer else "block",
        subject_id=offer or ref(block_id),
        chosen_ref=ref(superseded_by),
        decided_by=PLAN,
        rule=_code(why) or "unspecified",
        alternatives=tuple(dict(entry) for entry in forced),
        facts=_compact({
            "offer_block": ref(block_id),
            "offer_decision": offer,
            "superseded_by": ref(superseded_by),
            "shown_on": _code(shown_on),
            "expired_row": expired_row,
            **forced_facts(forced),
        }),
        detail_table="router_decisions" if offer else None,
        detail_id=offer,
        parent_id=parent_id,
        id=record_id,
    )


def step_failure(kind: str, rule: str, exc: BaseException, *, facts: Mapping[str, Any] | None = None) -> DecisionRecord:
    """A boundary step that raised: its type and ``module:function:line``, never its message. The boundary's writer
    gives it its parent, trace and subject."""

    return DecisionRecord(
        kind=kind, status="failed", decided_by=PLAN, rule=rule, facts=_compact(dict(facts or {})),
        error_type=_code(type(exc).__name__), error_where=_where(provenance.where(exc)),
    )


def _where(value: Any) -> str | None:
    if not isinstance(value, str) or not value:
        return None
    return "".join(ch if (ch.isalnum() or ch in "_.:/@+#=-") else "_" for ch in value)[:160]


def children(records: Iterable[DecisionRecord], parent: DecisionRecord) -> list[DecisionRecord]:
    """``records`` as children of ``parent``: its trace, subject and time, and their own ids."""

    return [replace(record, parent_id=parent.id, trace_id=parent.trace_id, subject_kind=parent.subject_kind,
                    subject_id=parent.subject_id, created_at=record.created_at or parent.created_at,
                    id=record.id or provenance.new_record_id()) for record in records]


def check_block(*, block_id: str, detail_id: str | None, forced: Sequence[Mapping[str, Any]], assignments: Sequence[Any],
                checks: Sequence[Any], trigger_attempt: str | None, parent_id: str | None,
                algorithm_version: Any) -> DecisionRecord:
    """The day's randomized check block, placed by the rules before the boundary's decision (RO5 §9 item 2): no draw,
    no alternatives; it names the checks and the forced items it holds first."""

    return DecisionRecord(
        kind="plan_block",
        status="chosen",
        subject_kind="block",
        subject_id=block_id,
        decided_by="rules",
        rule=CHECK_BLOCK_RULE,
        facts=_compact({
            "checks": _refs(checks),
            "assignments": _refs(assignments),
            "propensity": 1.0,
            "trigger_attempt": ref(trigger_attempt),
            **forced_facts(forced),
        }),
        versions=_compact({"algorithm_version": _code(algorithm_version)}),
        detail_table="router_decisions" if detail_id else None,
        detail_id=detail_id,
        parent_id=parent_id,
        id=provenance.new_record_id(),
        created_at=wall_now(),
    )


#: The restraint's outcome as a record's status: let in now, made to wait, refused by a hard constraint.
_INTERRUPT_STATUS = {"insert_now": "chosen", "continue_current": "deferred", "decline": "refused"}


def plan_interrupt(*, outcome: Any, item_id: Any, block_id: Any, plan_id: Any, detail_id: str | None,
                   displaced: Sequence[Any] = (), est_minutes: Any = None, trigger_attempt: str | None = None,
                   config: Any = None) -> list[DecisionRecord]:
    """The restraint gate's decision on one follow-up and its components' answers (``model_answer`` children).

    ``outcome`` is ``router_chooser.RestraintOutcome``: ``chosen_ref`` (``insert_now``, ``continue_current``,
    ``decline`` or a lesson offer's ref), its propensity, the router's record and any hard-constraint refusals."""

    router = dict(getattr(outcome, "record", None) or {})
    mixture = dict(router.get("mixture") or {})
    chosen = str(getattr(outcome, "chosen_ref", "") or "")
    refusals = list((getattr(outcome, "refused", None) or {}).get("reasons") or ())
    refusal_codes = [code for code in (_code(dict(reason).get("constraint_key")) for reason in refusals) if code]
    status = _INTERRUPT_STATUS.get(chosen, "chosen")
    decided_by = _code(router.get("decided_by")) or _code(router.get("policy"))
    rule = (refusal_codes[0] if refusal_codes else None) if status == "refused" else None
    rule = rule or _code(router.get("why_code")) or decided_by or "unspecified"
    pi = dict(mixture.get("pi") or {})
    alternatives = [_compact({"ref": ref(option), "p": _number(pi.get(option)), "lost_by": "not_drawn"})
                    for option in (mixture.get("support") or ()) if str(option) != chosen]
    timeouts = {"timeout_s": _number(getattr(getattr(config, "router", None), "timeout_seconds", None)),
                "prefetch_timeout_s": _number(getattr(getattr(config, "router", None), "prefetch_timeout_seconds",
                                                      None))}
    waited_ms = _number(mixture.get("waited_ms"))
    record = DecisionRecord(
        kind=PLAN_INTERRUPT,
        status=status,
        subject_kind="item",
        subject_id=ref(item_id),
        chosen_ref=ref(chosen),
        decided_by=decided_by,
        rule=rule,
        alternatives=tuple(alternatives),
        facts=_compact({
            "block": ref(block_id),
            "plan": ref(plan_id),
            "propensity": _number(getattr(outcome, "propensity", None)),
            "wait_feasible": bool(getattr(outcome, "wait_feasible", True)),
            "est_minutes": _number(est_minutes),
            "displaced": _refs(displaced),
            "refusals": refusal_codes[:IDS_KEPT],
            "boundary_key": _code(mixture.get("boundary_key")),
            "trigger_attempt": ref(trigger_attempt),
            **timeouts,
            "waited_ms": waited_ms,
        }),
        versions=_compact({
            "algorithm_version": _code(getattr(getattr(config, "algorithms", None), "algorithm_version", None)),
            "policy": _code(router.get("policy")),
            "seed": _code(router.get("seed")),
            "why_version": _code(router.get("why_version")),
        }),
        detail_table="router_decisions" if detail_id else None,
        detail_id=detail_id,
        id=provenance.new_record_id(),
        created_at=wall_now(),
    )
    answers = component_records(record, router, mixture, timeouts=timeouts, waited_ms=waited_ms, crashed=False)
    return [record, *answers]


def ad_unavailable(*, phase: str, code: Any, subject_kind: str, subject_id: Any, facts: Mapping[str, Any] | None = None,
                   denials: Sequence[Mapping[str, Any]] = (), error_type: Any = None) -> DecisionRecord:
    """Adaptive difficulty could not decide (its view, the plan's facts, its decision, or the plan's re-check of it),
    so the incumbent did. ``denials``: what AD's guard refused in that operation, as codes."""

    refused = [_compact({"verb": _code(d.get("verb")), "table": _code(d.get("table")),
                         "reader": _code(d.get("reader"))}) for d in denials][:IDS_KEPT]
    entries = sorted({str(d.get("entry")) for d in denials if _code(d.get("entry"))})
    return DecisionRecord(
        kind=AD_SLOT,
        status="fallback",
        subject_kind=subject_kind,
        subject_id=ref(subject_id),
        decided_by=INCUMBENT,
        rule=_code(code) or "unavailable",
        facts=_compact({"phase": _code(phase), **dict(facts or {}), "denials": refused,
                        "denials_n": len(denials) or None, "entries": entries[:IDS_KEPT]}),
        error_type=_code(error_type),
    )


def serve_eligibility(decision: Any, *, block_id: Any, displaced: bool) -> DecisionRecord:
    """A planned cold check the serve could not take cold (``serve_eligibility.EligibilityDecision``): displaced from
    its block, or served as ordinary practice with its task re-timed."""

    retimes = dict(getattr(decision, "retimes", ()) or ())
    withdrawals = dict(getattr(decision, "withdrawals", ()) or ())
    item = ref(getattr(decision, "practice_item_id", None))
    return DecisionRecord(
        kind=SERVE_ELIGIBILITY,
        status="excluded" if displaced else "fallback",
        subject_kind="item",
        subject_id=item,
        chosen_ref=None if displaced else item,
        decided_by="serve_eligibility",
        rule=_code(getattr(decision, "reason", None)) or "unspecified",
        facts=_compact({
            "verdict": _code(getattr(decision, "verdict", None)),
            "request": _code(getattr(decision, "request", None)),
            "block": ref(block_id),
            "until": _code(getattr(decision, "until", None)),
            "window_until": _code(getattr(decision, "window_until", None)),
            "reveal_total": _number(getattr(decision, "reveal_total", None)),
            "primed": bool(getattr(decision, "primed", False)),
            "reveal_events": _refs(getattr(decision, "reveal_event_ids", ()) or ()),
            "tasks": _refs(getattr(decision, "task_ids", ()) or ()),
            "retimed": _refs(retimes),
            "task_withdrawals": sorted({code for code in (_code(v) for v in withdrawals.values()) if code}),
        }),
    )


__all__ = [
    "AD_SLOT", "BUILDER_ERROR", "CHECK_BLOCK_RULE", "CHECK_DRAW_ERROR", "CHECK_PLACE_ERROR", "INCUMBENT",
    "LESSON_OFFER_BUILD", "MODEL_ANSWER", "OFFER_WITHDRAWN", "PLAN", "PLAN_INTERRUPT", "RANDOMIZED_CHECK",
    "SERVE_ELIGIBILITY", "ad_unavailable", "check_block", "children", "forced_entry", "forced_facts", "offer_withdrawn",
    "plan_interrupt", "serve_eligibility", "step_failure",
]

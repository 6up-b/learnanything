"""Why x and not y for rows older than their decision records: what the old rows themselves can still say.

Decisions made before migration 253 (and boundaries B2-B8 had not reached yet) have no ``decision_records`` row,
and none is backfilled (ADR-017: a record written now would claim to know inputs nobody stored). This reader
answers from the rows they did leave, in the same shape as a record's answer, and labels every answer
``reconstructed``. A field that comes from an exact key (a decision's ``detail_json``, a receipt's ``owner_id``, a
response's ``decision_id``) is reconstructed; a field that comes only from ordering rows in time (the decision after
a withdrawal, the forced item that took the offer's place, a call that finished after its decision's row was
written) is also named in the answer's ``inferred`` list, because a row written in between would change it.

Like a record, an answer holds ids, numbers and code constants only: free-form ids are hashed (``sha256:``), an
error or a verification reason is reduced to its code, and no prompt, output, goal or learner text is read into it
(``model_call_receipts``' payloads stay behind ``learnloop why --payload``).

Every read tolerates a vault without the table or column it reads (an older schema answers with less).
"""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from collections.abc import Callable, Iterable, Mapping, Sequence
from datetime import datetime, timezone
from typing import Any

from learnloop import provenance

LABEL = "reconstructed"

#: ``daily_plan.router_runtime.RECEIPT_OWNER``: a router call's owner kind; its ``owner_id`` is the boundary key.
ROUTER_OWNER = "router_decision"
#: ``figures.service``: an author call's owner is ``figure:<content_key(input_hash, generation)>``.
FIGURE_OWNER_PREFIX = "figure:"
FIGURE_AUTHOR_OWNER = "figure_author"
#: ``daily_plan.lesson_offer``: the ``expired`` row's key naming why an offer was taken back, or the newer decision.
WITHDRAWN_KEY = "withdrawn"
SUPERSEDED_KEY = "superseded_by_decision"
#: ``daily_plan.lesson_offer.offer_ref``'s prefix: a lesson offer's candidate ref.
OFFER_PREFIX = "lesson_offer:"

#: A figure verification problem's code, from the text an old report stored (``figures.records`` gives new rows these
#: codes at the source). A schema path (``predictions.0.change.param``) or ``prediction N:`` is the prediction's own
#: problem; ``invariant N`` is a failed check; anything else is the spec's.
PREDICTION_INVALID = "prediction_invalid"
VERIFICATION_FAILED = "verification_failed"
SPEC_INVALID = "spec_invalid"
_PREDICTION_PROBLEM = re.compile(r"^predictions?[ .]\d+")
_INVARIANT_PROBLEM = re.compile(r"^invariants?[ .]\d+")
_PATH = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z0-9_]+)+):")


# -- small, safe reads ---------------------------------------------------------------------------------------------


def code(value: Any) -> Any:
    """``value`` when it is a number, a bool or a code (:func:`provenance.is_code`); a free-form string as
    ``sha256:<16 hex>``, so an answer never carries text and never loses the id."""

    if value is None or isinstance(value, (bool, int, float)):
        return value
    text = str(value)
    if provenance.is_code(text):
        return text
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def digest(value: Any) -> str | None:
    """A stored free-text value (model or learner words) as ``sha256:<16 hex>`` whatever its spelling, or None."""

    if value is None or value == "":
        return None
    return "sha256:" + hashlib.sha256(str(value).encode("utf-8")).hexdigest()[:16]


def _number(value: Any) -> float | int | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return value


def select_rows(connection: Any, sql: str, args: Sequence[Any] = ()) -> list[dict[str, Any]]:
    try:
        cursor = connection.execute(sql, tuple(args))
        names = [column[0] for column in cursor.description or ()]
        return [dict(zip(names, tuple(row), strict=True)) for row in cursor.fetchall()]
    except sqlite3.OperationalError as exc:  # an older schema: no such table or column
        if "no such" in str(exc):
            return []
        raise


def select_one(connection: Any, sql: str, args: Sequence[Any] = ()) -> dict[str, Any] | None:
    found = select_rows(connection, sql, args)
    return found[0] if found else None


def _json(text: Any, default: Any) -> Any:
    if not isinstance(text, str) or not text:
        return default
    try:
        value = json.loads(text)
    except ValueError:
        return default
    return value if isinstance(value, type(default)) else default


def moment(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=timezone.utc)


def _ms_between(start: Any, end: Any) -> int | None:
    first, second = moment(start), moment(end)
    if first is None or second is None:
        return None
    return int(round((second - first).total_seconds() * 1000))


def _error_type(text: Any) -> str | None:
    """The class at the head of a stored error (``TimeoutError: ...``), never the rest."""

    if not isinstance(text, str) or ":" not in text:
        return None
    head = text.split(":", 1)[0].strip()
    return head if provenance.is_code(head) else None


# -- model calls: metadata, and whether the output is still there --------------------------------------------------


_CALL_COLUMNS = ("id", "owner_kind", "owner_id", "purpose", "provider", "model", "status", "error_type",
                 "started_at", "finished_at", "input_tokens", "output_tokens", "cost")


def calls_for_owner(connection: Any, owner_ids: Iterable[str], *, owner_kind: str | None = None) -> list[dict[str, Any]]:
    """Calls whose ``owner_id`` is one of ``owner_ids`` (the old join), metadata only, with whether the output is
    present and, when absent, why (``failed``, ``interrupted``, ``never_finished``, ``pruned``)."""

    owners = sorted({str(owner) for owner in owner_ids if owner})
    if not owners:
        return []
    kind_clause = " AND owner_kind = ?" if owner_kind else ""
    rows = select_rows(connection,
                 f"SELECT {', '.join(_CALL_COLUMNS)}, output_text IS NOT NULL AND output_text != '' AS has_output "
                 f"FROM model_call_receipts WHERE owner_id IN ({', '.join('?' for _ in owners)}){kind_clause} "
                 "ORDER BY started_at, id", [*owners, *([owner_kind] if owner_kind else [])])
    out = []
    for row in rows:
        present = bool(row.pop("has_output"))
        status = str(row.get("status") or "")
        if present:
            absent = None
        elif status in {"failed", "interrupted", "truncated"}:
            absent = status
        elif status == "started" or not row.get("finished_at"):
            absent = "never_finished"
        else:
            absent = "pruned"  # completed, its payload cleared by router.payload_retention_days
        out.append({
            "call_id": code(row["id"]), "owner_kind": code(row["owner_kind"]), "purpose": code(row["purpose"]),
            "provider": code(row["provider"]), "model": code(row["model"]), "status": code(status),
            "error_type": code(row["error_type"]), "started_at": row["started_at"], "finished_at": row["finished_at"],
            "input_tokens": _number(row["input_tokens"]), "output_tokens": _number(row["output_tokens"]),
            "cost": _number(row["cost"]), "output": "present" if present else "absent", "output_absent_reason": absent,
        })
    return out


def late_calls(calls: Iterable[Mapping[str, Any]], decided_at: Any) -> list[dict[str, Any]]:
    """Calls that started before ``decided_at`` and finished after it (``late_ms``) or never (``late_ms`` None)."""

    decided = moment(decided_at)
    if decided is None:
        return []
    out = []
    for call in calls:
        started, finished = moment(call.get("started_at")), moment(call.get("finished_at"))
        if started is None or started > decided or (finished is not None and finished <= decided):
            continue
        out.append({"call_id": call.get("call_id"), "purpose": call.get("purpose"), "model": call.get("model"),
                    "status": call.get("status"), "finished_at": call.get("finished_at"),
                    "late_ms": None if finished is None else _ms_between(decided_at, call.get("finished_at")),
                    "output": call.get("output")})
    return out


# -- a router decision (case 1) ----------------------------------------------------------------------------------


_DECISION_COLUMNS = ("id", "decision_kind", "surface", "mode", "policy", "algorithm_version", "log_version",
                     "session_id", "parent_decision_id", "design", "seed", "chosen_ref", "propensity",
                     "propensity_kind", "fallback", "question_set_version", "latency_ms", "cost_usd", "detail_json",
                     "created_at")


def _decision_row(connection: Any, decision_id: str) -> dict[str, Any] | None:
    return select_one(connection, f"SELECT {', '.join(_DECISION_COLUMNS)} FROM router_decisions WHERE id = ?",
                (decision_id,))


def _components(mixture: Mapping[str, Any]) -> list[dict[str, Any]]:
    models = mixture.get("models") if isinstance(mixture.get("models"), Mapping) else {}
    out = []
    for name, summary in sorted(models.items()):
        summary = summary if isinstance(summary, Mapping) else {}
        out.append({
            "component": code(name), "status": code(summary.get("status")),
            "decided_by": {"llm": "router_llm", "decider": "router_decider", "numeric": "numeric_policy"}.get(
                str(name), code(name)),
            "latency_ms": _number(summary.get("latency_ms")), "cost_usd": _number(summary.get("cost_usd")),
            "model": code(summary.get("model")), "provider": code(summary.get("provider")),
            "error_type": _error_type(summary.get("error")),
        })
    return out


def _alternatives(row: Mapping[str, Any], mixture: Mapping[str, Any]) -> list[dict[str, Any]]:
    chosen = row.get("chosen_ref")
    pi = mixture.get("mix_pi") if isinstance(mixture.get("mix_pi"), Mapping) else None
    if pi:
        options = [(ref, _number(p)) for ref, p in pi.items()]
    else:
        options = [(ref, None) for ref in mixture.get("support") or () if isinstance(ref, str)]
    kept, overflow = provenance.cap_alternatives(
        [{"ref": code(ref), "p": p, "lost_by": "not_drawn"} for ref, p in options if ref != chosen])
    if overflow:
        kept.append({"ref": None, "lost_by": "overflow", "count": sum(overflow.values())})
    return kept


#: Answers a router decision's outcome as of now (``why.reader``'s read-time derivation), or None.
OutcomeReader = Callable[[Any, str], "dict[str, Any] | None"]


def _decision_next(connection: Any, row: Mapping[str, Any], detail: Mapping[str, Any],
                   outcome_now: OutcomeReader | None = None) -> tuple[dict[str, Any], list[str]]:
    """What came after a decision: its outcome (derived now) and responses (exact keys), and the plan's next decision
    (by time)."""

    out: dict[str, Any] = {}
    outcome = outcome_now(connection, str(row["id"])) if outcome_now is not None else None
    if outcome is not None:
        out["outcome"] = outcome
    responses = select_rows(connection, "SELECT id, response, responded_at, detail_json FROM router_suggestion_responses "
                                  "WHERE decision_id = ? ORDER BY responded_at, id", (row["id"],))
    if responses:
        out["responses"] = [{
            "response_id": code(item["id"]), "response": code(item["response"]), "responded_at": item["responded_at"],
            "withdrawn": code(_json(item["detail_json"], {}).get(WITHDRAWN_KEY)),
            "superseded_by": code(_json(item["detail_json"], {}).get(SUPERSEDED_KEY)),
        } for item in responses]
    plan = detail.get("plan_id")
    nxt = select_one(connection,
               "SELECT id, decision_kind, created_at, chosen_ref FROM router_decisions WHERE created_at >= ? AND id != ? "
               + ("AND json_extract(detail_json, '$.plan_id') = ? " if plan else "")
               + "ORDER BY created_at, id LIMIT 1",
               (row["created_at"], row["id"], *((plan,) if plan else ())))
    inferred = []
    if nxt is not None:
        out["next_decision"] = {"decision_id": code(nxt["id"]), "kind": code(nxt["decision_kind"]),
                                "created_at": nxt["created_at"], "chosen": code(nxt["chosen_ref"])}
        inferred.append("next.next_decision")
    return out, inferred


def router_decision(connection: Any, decision_id: str, *, timeout_now: float | None = None,
                    outcome_now: OutcomeReader | None = None) -> dict[str, Any] | None:
    """A ``router_decisions`` row as an answer: what won, the mix's alternatives, each model's answer, the inputs the
    row kept, versions and seed, its calls joined by the boundary key, the calls that answered after it, and next."""

    row = _decision_row(connection, decision_id)
    if row is None:
        return None
    detail = _json(row["detail_json"], {})
    mixture = detail.get("mixture") if isinstance(detail.get("mixture"), Mapping) else {}
    router = detail.get("router") if isinstance(detail.get("router"), Mapping) else {}
    state = detail.get("state") if isinstance(detail.get("state"), Mapping) else {}
    key = mixture.get("boundary_key")
    calls = calls_for_owner(connection, [key], owner_kind=ROUTER_OWNER) if key else []
    discarded = late_calls(calls, row["created_at"])
    # The row's own ``fallback`` column names a component that fell back (``llm``); the plan fell back only when its
    # detail says so.
    fallback = bool(detail.get("fallback"))
    forced = [item for item in detail.get("forced") or () if isinstance(item, Mapping)]
    nxt, inferred = _decision_next(connection, row, detail, outcome_now)
    answer = {
        "label": LABEL,
        "kind": code(row["decision_kind"]),
        "row": {"table": "router_decisions", "id": code(row["id"])},
        "created_at": row["created_at"],
        "subject": f"block:{code(detail['block_id'])}" if detail.get("block_id") else None,
        "status": "fallback" if fallback else "chosen",
        "chosen": code(row["chosen_ref"]),
        "decided_by": code(detail.get("chosen_by") or router.get("decided_by") or row["policy"]),
        "rule": code(router.get("why_code") or detail.get("fallback_reason") or detail.get("why_kind")),
        "alternatives": _alternatives(row, mixture),
        "components": _components(mixture),
        "inputs": {
            "boundary_key": code(key), "waited_ms": _number(mixture.get("waited_ms")),
            "prefetched_at": code(mixture.get("prefetched_at")),
            # The configured wait was not stored before migration 253; the vault's setting now may differ.
            "timeout_s": None, "timeout_s_basis": "not_stored", "timeout_s_now": _number(timeout_now),
            "drawn_component": code(mixture.get("drawn_component")),
            "effective_weights": {code(name): _number(weight) for name, weight in
                                  (mixture.get("effective_weights") or {}).items()} or None,
            "failed_components": [code(name) for name in mixture.get("failed") or ()],
            "fallback_reasons": {code(name): code(reason) for name, reason in
                                 (router.get("fallback_reasons") or {}).items()} or None,
            "option_count": _number(router.get("option_count")), "propensity": _number(row["propensity"]),
            "propensity_kind": code(row["propensity_kind"]), "minutes_left": _number(state.get("minutes_left")),
            "forced": [code(item.get("practice_item_id")) for item in forced],
            "forced_origins": [code(item.get("origin")) for item in forced],
            "stop": detail.get("stop") if isinstance(detail.get("stop"), bool) else None,
            "plan_id": code(detail.get("plan_id")),
        },
        "versions": {
            "algorithm_version": code(row["algorithm_version"]), "policy": code(row["policy"]),
            "design": code(row["design"]), "seed": code(row["seed"]), "log_version": code(row["log_version"]),
            "question_set_version": code(row["question_set_version"]), "chooser": code(detail.get("chooser")),
            "mode": code(router.get("mode") or row["mode"]), "card_version": code(router.get("card_version")),
        },
        "calls": calls,
        "discarded": discarded,
        "next": nxt,
        # The decision's row is written when it is decided, so "finished after it" is "answered too late".
        "inferred": (["discarded"] if discarded else []) + inferred,
    }
    return answer


def decisions_for_block(connection: Any, block_id: str) -> list[str]:
    return [str(row["id"]) for row in select_rows(
        connection, "SELECT id FROM router_decisions WHERE json_extract(detail_json, '$.block_id') = ? "
                    "ORDER BY created_at, id", (block_id,))]


def latest_decision(connection: Any) -> str | None:
    row = select_one(connection, "SELECT id FROM router_decisions ORDER BY created_at DESC, id DESC LIMIT 1")
    return str(row["id"]) if row else None


# -- an offer taken back (case 2) ----------------------------------------------------------------------------------


def _workflow_for(connection: Any, item_id: str, before: Any) -> dict[str, Any] | None:
    found = select_one(connection, "SELECT w.id, w.source_attempt_id, w.state, w.decision_id FROM generated_probe_items g "
                             "JOIN followup_workflows w ON w.id = g.workflow_id WHERE g.practice_item_id = ?", (item_id,))
    if found is None:
        found = select_one(connection, "SELECT id, source_attempt_id, state, decision_id FROM followup_workflows "
                                 "WHERE practice_item_id = ? AND created_at <= ? ORDER BY created_at DESC, id DESC "
                                 "LIMIT 1", (item_id, before or "9999"))
    return found


def offer_withdrawals(connection: Any, decision_id: str) -> list[dict[str, Any]]:
    """Each ``expired`` row that took ``decision_id``'s offer back, as an ``offer_withdrawn`` answer.

    The row names why (``forced_items``) but not which items forced it. They are read from the plan's next decision
    (its ``forced`` list, with each item's follow-up workflow and source attempt), and the workflows that became
    ready between the offer and its withdrawal: both by time, so both are ``inferred``."""

    offer = _decision_row(connection, decision_id)
    out = []
    for response in select_rows(connection, "SELECT id, response, responded_at, detail_json FROM router_suggestion_responses "
                                      "WHERE decision_id = ? AND response = 'expired' ORDER BY responded_at, id",
                          (decision_id,)):
        detail = _json(response["detail_json"], {})
        why = detail.get(WITHDRAWN_KEY) or (SUPERSEDED_KEY if detail.get(SUPERSEDED_KEY) else None)
        if why is None:
            continue
        offer_detail = _json(offer["detail_json"], {}) if offer else {}
        nxt = select_one(connection, "SELECT id, decision_kind, created_at, chosen_ref, detail_json FROM router_decisions "
                               "WHERE created_at >= ? AND id != ? ORDER BY created_at, id LIMIT 1",
                   (response["responded_at"], decision_id))
        forced = [item for item in (_json(nxt["detail_json"], {}).get("forced") if nxt else None) or ()
                  if isinstance(item, Mapping) and item.get("practice_item_id")]
        alternatives = []
        for item in forced:
            workflow = _workflow_for(connection, str(item["practice_item_id"]), nxt["created_at"] if nxt else None) or {}
            alternatives.append({key: value for key, value in {
                "ref": code(item["practice_item_id"]), "origin": code(item.get("origin")),
                "workflow": code(workflow.get("id")), "source_attempt": code(workflow.get("source_attempt_id")),
                "workflow_state": code(workflow.get("state")), "lost_by": None,
            }.items() if value is not None})
        since = offer["created_at"] if offer else response["responded_at"]
        ready = select_rows(connection,
                      "SELECT w.id, w.practice_item_id, w.source_attempt_id, e.created_at FROM followup_workflow_events e "
                      "JOIN followup_workflows w ON w.id = e.workflow_id WHERE e.to_state = 'ready' "
                      "AND e.created_at >= ? AND e.created_at <= ? ORDER BY e.created_at, e.id",
                      (since, response["responded_at"]))
        # A probe generated from a recorded need has no workflow of its own: the follow-up workflows opened while the
        # offer waited, and the generation jobs that finished then, are where it came from.
        opened = select_rows(connection, "SELECT id, source_attempt_id, state, settled_reason, created_at FROM "
                                   "followup_workflows WHERE created_at >= ? AND created_at <= ? ORDER BY created_at, id",
                       (since, response["responded_at"]))
        generated = select_rows(connection, "SELECT id, kind, workflow_id, need_id, probe_episode_id, state, updated_at FROM "
                                      "followup_generation_jobs WHERE state = 'done' AND updated_at >= ? AND "
                                      "updated_at <= ? ORDER BY updated_at, id", (since, response["responded_at"]))
        needs = [job for job in generated if job.get("need_id")]
        for entry in alternatives:
            if "workflow" not in entry and len(needs) == 1:
                entry["generated_by_job"] = code(needs[0]["id"])
                entry["need"] = code(needs[0]["need_id"])
        inferred = ["alternatives", "inputs.forced", "inputs.workflows", "inputs.source_attempts", "next.next_decision",
                    "inputs.ready_between", "inputs.opened_between", "inputs.generated_between"]
        out.append({
            "label": LABEL,
            "kind": "offer_withdrawn",
            "row": {"table": "router_suggestion_responses", "id": code(response["id"])},
            "created_at": response["responded_at"],
            "subject": f"offer:{code(decision_id)}",
            "status": "withdrawn",
            "chosen": code(detail.get(SUPERSEDED_KEY)),
            "decided_by": "plan",
            "rule": code(why),
            "parent": {"table": "router_decisions", "id": code(decision_id)},
            "alternatives": alternatives,
            "inputs": {
                "offer_block": code(detail.get("block_id") or offer_detail.get("block_id")),
                "offer_decision": code(decision_id), "offer_chosen": code(offer["chosen_ref"]) if offer else None,
                "offer_decided_at": offer["created_at"] if offer else None, "shown_on": code(detail.get("shown_on")),
                "responded_at": response["responded_at"],
                "forced": [entry["ref"] for entry in alternatives],
                "workflows": [entry.get("workflow") for entry in alternatives if entry.get("workflow")],
                "source_attempts": [entry.get("source_attempt") for entry in alternatives if entry.get("source_attempt")],
                "ready_between": [{"workflow": code(row["id"]), "item": code(row["practice_item_id"]),
                                   "source_attempt": code(row["source_attempt_id"]), "ready_at": row["created_at"]}
                                  for row in ready],
                "opened_between": [{"workflow": code(row["id"]), "source_attempt": code(row["source_attempt_id"]),
                                    "state": code(row["state"]), "settled_reason": code(row["settled_reason"]),
                                    "opened_at": row["created_at"]} for row in opened],
                "generated_between": [{"job": code(row["id"]), "kind": code(row["kind"]),
                                       "workflow": code(row["workflow_id"]), "need": code(row["need_id"]),
                                       "probe_episode": code(row["probe_episode_id"]), "done_at": row["updated_at"]}
                                      for row in generated],
            },
            "versions": {},
            "next": {"next_decision": {"decision_id": code(nxt["id"]), "kind": code(nxt["decision_kind"]),
                                       "created_at": nxt["created_at"], "chosen": code(nxt["chosen_ref"])}}
                    if nxt else {},
            "inferred": inferred,
        })
    return out


def withdrawals_for_response(connection: Any, response_id: str) -> list[dict[str, Any]]:
    row = select_one(connection, "SELECT decision_id FROM router_suggestion_responses WHERE id = ?", (response_id,))
    return offer_withdrawals(connection, str(row["decision_id"])) if row else []


# -- a figure stored failed (case 3) -------------------------------------------------------------------------------


def problem_code(text: Any) -> str:
    value = str(text or "").strip()
    if _PREDICTION_PROBLEM.match(value):
        return PREDICTION_INVALID
    if _INVARIANT_PROBLEM.match(value):
        return VERIFICATION_FAILED
    return SPEC_INVALID


def problem_path(text: Any) -> str | None:
    """A schema path at the head of a problem (``predictions.0.change.param``), when it is one; never the message."""

    found = _PATH.match(str(text or "").strip())
    return found.group(1) if found and provenance.is_code(found.group(1)) else None


def _figure_calls(connection: Any, figure: Mapping[str, Any]) -> tuple[list[dict[str, Any]], int | None]:
    """The author calls of a figure's build: owner ``figure:<content_key(input_hash, generation)>``, where the
    generation is how many builds of the same input came before it (a recount, so ``inferred``)."""

    from learnloop.ai.execution import content_key

    input_hash = figure.get("input_hash")
    if not input_hash:
        return [], None
    before = select_rows(connection, "SELECT id, created_at FROM interactive_figures WHERE input_hash = ? "
                               "ORDER BY created_at, id", (input_hash,))
    generation = sum(1 for row in before if (row["created_at"], row["id"]) < (figure["created_at"], figure["id"]))
    tried = [generation, *[g for g in range(len(before) + 1) if g != generation]]
    for candidate in tried:
        owner = FIGURE_OWNER_PREFIX + content_key({"input_hash": input_hash, "generation": candidate})
        calls = calls_for_owner(connection, [owner])
        if calls and (candidate == generation or all(
                (moment(call["started_at"]) or moment(figure["created_at"])) <= moment(figure["created_at"])
                for call in calls)):
            return calls, candidate
    return [], None


def figure(connection: Any, figure_id: str) -> dict[str, Any] | None:
    """An ``interactive_figures`` row as a ``figure_author`` answer: its verification, the typed problem codes its
    report's text reduces to, the prompt version and model, its request, and its author calls."""

    row = select_one(connection, "SELECT id, origin, verification, unsupported_kind, model, prompt_version, input_hash, "
                           "created_at, request_id, verification_report_json, tier, supersedes_id FROM interactive_figures "
                           "WHERE id = ?", (figure_id,))
    if row is None:
        return None
    report = _json(row["verification_report_json"], {})
    texts = [report.get("reason"), *list(report.get("structural") or ()), *list(report.get("problems") or ()),
             *list(report.get("invariant_problems") or ())]
    texts = [text for text in texts if isinstance(text, str) and text]
    problems = [problem_code(text) for text in texts]
    failed = row["verification"] == "failed"
    rule = None
    if failed:
        rule = PREDICTION_INVALID if PREDICTION_INVALID in problems else (problems[0] if problems else VERIFICATION_FAILED)
    request = select_one(connection, "SELECT id, origin, build_mode, prefetch_decision_id, created_at FROM figure_requests "
                               "WHERE id = ?", (row["request_id"],)) if row["request_id"] else None
    calls, generation = _figure_calls(connection, row)
    authors = [call for call in calls if call["purpose"] == FIGURE_AUTHOR_OWNER or call["owner_kind"] == FIGURE_AUTHOR_OWNER]
    return {
        "label": LABEL,
        "kind": "figure_author",
        "row": {"table": "interactive_figures", "id": code(row["id"])},
        "created_at": row["created_at"],
        "subject": f"figure:{code(row['id'])}",
        "status": "failed" if failed else "chosen",
        "chosen": None if failed else code(row["id"]),
        "decided_by": code(row["model"]),
        "rule": rule if failed else code(row["verification"]),
        "alternatives": [],
        "inputs": {
            "verification": code(row["verification"]), "outcome": code(report.get("outcome")),
            "problems": problems, "problems_n": len(problems),
            "problem_paths": sorted({path for path in (problem_path(text) for text in texts) if path}),
            "dropped_predictions_n": len(report.get("dropped_predictions") or ()),
            # The author's own words for what it couldn't draw: hashed even when it is one word.
            "unsupported_kind": digest(row["unsupported_kind"]), "tier": code(row["tier"]),
            "origin": code(row["origin"]), "request_id": code(row["request_id"]),
            "build_mode": code(request["build_mode"]) if request else None,
            "prefetch_decision_id": code(request["prefetch_decision_id"]) if request else None,
            "supersedes_id": code(row["supersedes_id"]), "generation": generation,
            "author_calls_n": len(authors), "calls_failed_n": sum(1 for call in calls if call["status"] == "failed"),
        },
        "versions": {"prompt_version": code(row["prompt_version"]), "model": code(row["model"])},
        "calls": calls,
        "discarded": [],
        "next": {},
        "inferred": ["inputs.generation", "calls"] if calls else [],
    }


# -- pre-builds before and after the first measured latency (case 4) ----------------------------------------------


_PREFETCH_COLUMNS = ("id", "trigger_kind", "trigger_ref", "request_key", "decision", "sampled_eu", "w_minutes",
                     "cost_minutes", "p_open_content", "propensity", "model_version", "posterior_digest", "request_id",
                     "created_at")
#: The measurements behind a pre-build decision that can change between two of them.
_PREFETCH_MEASURES = ("sampled_eu", "w_minutes", "cost_minutes", "p_open_content", "propensity", "posterior_digest",
                      "model_version")


def _prefetch(row: Mapping[str, Any]) -> dict[str, Any]:
    return {"decision_id": code(row["id"]), "trigger_kind": code(row["trigger_kind"]),
            "verdict": code(row["decision"]), "created_at": row["created_at"],
            **{name: code(row[name]) for name in _PREFETCH_MEASURES}}


def prefetch_decision(connection: Any, decision_id: str) -> dict[str, Any] | None:
    row = select_one(connection, f"SELECT {', '.join(_PREFETCH_COLUMNS)} FROM figure_prefetch_decisions WHERE id = ?",
               (decision_id,))
    if row is None:
        return None
    verdict = str(row["decision"])
    return {
        "label": LABEL, "kind": "figure_prebuild",
        "row": {"table": "figure_prefetch_decisions", "id": code(row["id"])},
        "created_at": row["created_at"], "subject": f"decision:{code(row['id'])}",
        "status": {"build": "chosen", "skip": "excluded"}.get(verdict, "deferred"),
        "chosen": code(row["request_key"]) if verdict == "build" else None,
        "decided_by": code(row["model_version"]),
        # The rule was never stored; a skip with no EU is the one taken before any measured latency.
        "rule": ("no_measured_latency" if verdict == "skip" and row["sampled_eu"] is None else code(verdict)),
        "alternatives": [],
        "inputs": {**_prefetch(row), "trigger_ref": code(row["trigger_ref"]), "request_id": code(row["request_id"])},
        "versions": {"model_version": code(row["model_version"]), "posterior_digest": code(row["posterior_digest"]),
                     "seed": None, "seed_basis": "not_stored"},
        "calls": [], "discarded": [], "next": {}, "inferred": ["rule"] if verdict == "skip" else [],
    }


def first_measurement(connection: Any) -> dict[str, Any] | None:
    """The first measured build latency: the first completed figure author call (the calls the quick tiers' wait W is
    measured from, ``figures.prefetch_ledger``), or the first pressed request."""

    call = select_one(connection, "SELECT id, finished_at FROM model_call_receipts WHERE purpose = ? AND status = "
                            "'completed' AND finished_at IS NOT NULL ORDER BY finished_at, id LIMIT 1",
                (FIGURE_AUTHOR_OWNER,))
    press = select_one(connection, "SELECT id, created_at FROM figure_requests WHERE build_mode = 'pressed' "
                             "ORDER BY created_at, id LIMIT 1")
    found = []
    if call is not None:
        found.append((moment(call["finished_at"]), {"kind": "author_call_completed", "at": call["finished_at"],
                                                    "row": {"table": "model_call_receipts", "id": code(call["id"])}}))
    if press is not None:
        found.append((moment(press["created_at"]), {"kind": "pressed_request", "at": press["created_at"],
                                                    "row": {"table": "figure_requests", "id": code(press["id"])}}))
    found = [item for item in found if item[0] is not None]
    if not found:
        return None
    first = min(found, key=lambda item: item[0])[1]
    return {**first, "all": [item[1] for item in sorted(found, key=lambda item: item[0])]}


def _changed(before: Mapping[str, Any], after: Mapping[str, Any], names: Iterable[str]) -> dict[str, list[Any]]:
    return {name: [before.get(name), after.get(name)] for name in names if before.get(name) != after.get(name)}


def first_build(connection: Any) -> dict[str, Any] | None:
    """The last skip, the first build and what changed between them, from ``figure_prefetch_decisions``: how many
    skips came before the first non-skip (overall and per trigger kind), and whether the first measured latency
    falls between the last skip and the first build."""

    rows = select_rows(connection, f"SELECT {', '.join(_PREFETCH_COLUMNS)} FROM figure_prefetch_decisions "
                             "ORDER BY created_at, id")
    if not rows:
        return None
    first_non_skip = next((index for index, row in enumerate(rows) if row["decision"] != "skip"), None)
    first_build_at = next((index for index, row in enumerate(rows) if row["decision"] == "build"), None)
    end = first_build_at if first_build_at is not None else len(rows)
    skips = [row for row in rows[:end] if row["decision"] == "skip"]
    last_skip = skips[-1] if skips else None
    built = rows[first_build_at] if first_build_at is not None else None
    by_kind: dict[str, dict[str, Any]] = {}
    for kind in dict.fromkeys(str(row["trigger_kind"]) for row in rows):
        mine = [row for row in rows if str(row["trigger_kind"]) == kind]
        first = next((index for index, row in enumerate(mine) if row["decision"] != "skip"), None)
        by_kind[code(kind)] = {
            "skips_before_first_non_skip": sum(1 for row in mine[:first if first is not None else len(mine)]
                                               if row["decision"] == "skip"),
            "first_non_skip": _prefetch(mine[first]) if first is not None else None,
        }
    measured = first_measurement(connection)
    between = None
    if measured is not None and last_skip is not None and built is not None:
        at = moment(measured["at"])
        between = bool(at is not None and moment(last_skip["created_at"]) < at <= moment(built["created_at"]))
    return {
        "label": LABEL,
        "kind": "figure_prebuild_first_build",
        "row": {"table": "figure_prefetch_decisions", "id": code(built["id"]) if built else None},
        "decisions_n": len(rows),
        "skips_before_first_build": len(skips),
        "skips_before_first_non_skip": sum(1 for row in rows[:first_non_skip if first_non_skip is not None
                                                             else len(rows)] if row["decision"] == "skip"),
        "first_non_skip": _prefetch(rows[first_non_skip]) if first_non_skip is not None else None,
        "last_skip": _prefetch(last_skip) if last_skip else None,
        "first_build": _prefetch(built) if built else None,
        "by_trigger_kind": by_kind,
        "first_measurement": measured,
        "measurement_between": between,
        "changed": _changed(_prefetch(last_skip), _prefetch(built), _PREFETCH_MEASURES) if last_skip and built else {},
        # The skip's rule was never stored; the measurement is matched by time.
        "inferred": ["first_measurement", "measurement_between"],
    }


# -- dispatch ------------------------------------------------------------------------------------------------------


def resolve(connection: Any, target: str, *, timeout_now: float | None = None,
            outcome_now: OutcomeReader | None = None) -> list[dict[str, Any]]:
    """The reconstructed answers ``target`` names (empty when none): ``latest`` (the newest router decision),
    ``block:``, ``offer:``, ``decision:``, ``figure:``, or a bare router decision, figure, pre-build decision or
    offer response id."""

    prefix, _, rest = target.partition(":")
    out: list[dict[str, Any]] = []

    def decision(decision_id: str) -> None:
        answer = router_decision(connection, decision_id, timeout_now=timeout_now, outcome_now=outcome_now)
        if answer is not None:
            out.append(answer)
            out.extend(offer_withdrawals(connection, decision_id))

    if target == "latest":
        latest = latest_decision(connection)
        if latest:
            decision(latest)
    elif prefix == "block" and rest:
        for decision_id in decisions_for_block(connection, rest):
            decision(decision_id)
    elif prefix == "offer" and rest:
        decision(rest)
    elif prefix == "figure" and rest:
        answer = figure(connection, rest)
        if answer is not None:
            out.append(answer)
    elif prefix == "decision" and rest:
        decision(rest)
        if not out:
            answer = prefetch_decision(connection, rest)
            if answer is not None:
                out.append(answer)
    elif not rest or prefix not in provenance.SUBJECT_KINDS:
        decision(target)
        if not out:
            for answer in (figure(connection, target), prefetch_decision(connection, target)):
                if answer is not None:
                    out.append(answer)
        if not out:
            out.extend(withdrawals_for_response(connection, target))
    return out

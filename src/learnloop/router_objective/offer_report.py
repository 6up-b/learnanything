"""Teacher TE3b (spec_teacher_v1 rev 5 §15.1a, "Evaluation" and "What the trace records"): the lesson offers' rows of
``learnloop router objective-report`` and a drawn offer's binding for ``learnloop router trace``. Read-only reads over
existing ids (the traces, the router's decisions, the learner's responses, the lessons and their receipts and the
attempts); nothing here gates anything, and no count does.

The report: offers in the support and drawn, their ``μ`` and ``P(accept)``, the responses, the lessons they opened, and
the lesson curve's posterior as the latest trace read it. The binding: decision → response → lesson → receipt →
delayed checks and their outcomes (RO0 row 12's kind of read).
"""

from __future__ import annotations

import json
from collections import Counter
from collections.abc import Mapping
from typing import Any

VERSION = "te3b_lesson_offer_report_v1"
PREFIX = "lesson_offer:"


def _has(connection: Any, table: str) -> bool:
    return connection.execute("SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?", (table,)).fetchone() \
        is not None


def binding(connection: Any, decision_id: str) -> dict[str, Any] | None:
    """A drawn offer's chain of ids and outcomes, or None when the decision drew no offer."""

    if not _has(connection, "router_decisions"):
        return None
    row = connection.execute("SELECT chosen_ref FROM router_decisions WHERE id = ?", (decision_id,)).fetchone()
    if row is None or not str(row[0] or "").startswith(PREFIX):
        return None
    out: dict[str, Any] = {"decision_id": decision_id, "offer": str(row[0]), "response": None, "lesson": None,
                           "delayed_checks": []}
    if not _has(connection, "router_suggestion_responses"):
        return out
    response = connection.execute(
        "SELECT response, candidate_ref, lesson_id, responded_at FROM router_suggestion_responses WHERE decision_id = ? "
        "AND response IN ('accepted', 'chose_alternative', 'declined', 'ignored')", (decision_id,)).fetchone()
    if response is None:
        # IH2: taken back by the plan: a newer decision replaced it, or a withdrawal. Never the learner's answer.
        taken_back = connection.execute(
            "SELECT detail_json, responded_at FROM router_suggestion_responses WHERE decision_id = ? AND response = 'expired'",
            (decision_id,)).fetchone()
        detail = json.loads(taken_back[0] or "{}") if taken_back is not None else {}
        if detail.get("superseded_by_decision"):
            out["response"] = {"response": "superseded", "by": detail["superseded_by_decision"], "at": taken_back[1]}
        return out
    out["response"] = {"response": response[0], "candidate_ref": response[1], "at": response[3]}
    if not response[2] or not _has(connection, "lessons"):
        return out
    lesson = connection.execute("SELECT id, opened_at, closed_at, close_reason FROM lessons WHERE id = ?",
                                (response[2],)).fetchone()
    if lesson is None:
        out["lesson"] = {"lesson_id": response[2], "status": "not_opened"}
        return out
    out["lesson"] = {"lesson_id": lesson[0], "opened_at": lesson[1], "closed_at": lesson[2], "close_reason": lesson[3]}
    receipt = connection.execute("SELECT receipt_json FROM lesson_receipts WHERE lesson_id = ?", (lesson[0],)).fetchone() \
        if _has(connection, "lesson_receipts") else None
    for entry in (json.loads(receipt[0]).get("delayed_checks") or ()) if receipt is not None else ():
        item = entry.get("item_id")
        answer = connection.execute(
            "SELECT id, correctness, created_at FROM practice_attempts WHERE practice_item_id = ? AND created_at > ? "
            "ORDER BY created_at, id LIMIT 1", (item, lesson[2])).fetchone() if item and lesson[2] else None
        out["delayed_checks"].append({"purpose": entry.get("purpose"), "learning_object_id": entry.get("learning_object_id"),
                                      "item_id": item, "due": entry.get("due"),
                                      "outcome": ({"attempt_id": answer[0], "correctness": answer[1], "at": answer[2]}
                                                  if answer is not None else None)})
    return out


def build(connection: Any) -> dict[str, Any]:
    """The lesson-offer rows (module docstring)."""

    if not _has(connection, "router_objective_traces"):
        return {"version": VERSION, "status": "no_traces_table"}
    in_support = drawn = 0
    mu: list[float] = []
    p_accept: list[float] = []
    curve: Any = "placeholder"
    drawn_ids: list[str] = []
    for decision_id, chosen, raw in connection.execute(
            "SELECT decision_id, chosen_ref, trace_json FROM router_objective_traces "
            "WHERE decision_kind IN ('plan_block', 'plan_interrupt') ORDER BY created_at, id"):
        trace = json.loads(raw)
        offers = {ref: entry for ref, entry in (trace.get("candidates") or {}).items() if str(ref).startswith(PREFIX)}
        if not offers:
            continue
        in_support += 1
        for ref, entry in offers.items():
            value = ((trace.get("mixing") or {}).get("mu") or {}).get(ref)
            if isinstance(value, (int, float)):
                mu.append(float(value))
            sensors = ((entry.get("offer") or {}).get("sensors") or {})
            accept = (sensors.get("p_accept") or {}).get("mean")
            if isinstance(accept, (int, float)):
                p_accept.append(float(accept))
            if sensors.get("lesson_curve") is not None:
                curve = sensors["lesson_curve"]
        if str(chosen).startswith(PREFIX):
            drawn += 1
            drawn_ids.append(str(decision_id))
    responses: Counter[str] = Counter()
    opened = closed = 0
    for decision_id in drawn_ids:
        found = binding(connection, decision_id) or {}
        responses[str((found.get("response") or {}).get("response") or "unanswered")] += 1
        lesson = found.get("lesson") or {}
        if lesson.get("opened_at"):
            opened += 1
        if lesson.get("closed_at"):
            closed += 1
    return {"version": VERSION, "decisions_with_an_offer": in_support, "offers_drawn": drawn,
            "mu_mean": round(sum(mu) / len(mu), 6) if mu else None,
            "p_accept_mean": round(sum(p_accept) / len(p_accept), 6) if p_accept else None,
            "responses": dict(responses), "lessons_opened": opened, "lessons_closed": closed,
            "lesson_curve": curve,
            "evaluation": "as any action: RO §8.7's common return under the live continuation, the offer's acceptance "
                          "inside the outcome; the effect among those who accepted is self-selected and never claimed"}


def lines(report: Mapping[str, Any]) -> list[str]:
    if report.get("status") == "no_traces_table":
        return []
    return [f"lesson offers ({report['version']}): in the support at {report['decisions_with_an_offer']} decisions, "
            f"drawn {report['offers_drawn']} (mean mu {report['mu_mean']}, mean P(accept) {report['p_accept_mean']}); "
            f"responses {report['responses']}; lessons opened {report['lessons_opened']}, closed "
            f"{report['lessons_closed']}; lesson curve {report['lesson_curve']}"]


__all__ = ["VERSION", "binding", "build", "lines"]

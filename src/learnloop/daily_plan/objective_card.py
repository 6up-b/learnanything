"""Router objective RO4 (spec §8.3): the LLM policy's card, a decision-level variant of RO2's H3 card.

RO2's ``ad-forecast-state-v3`` H3 rung reads one served item's whole history (``adaptive_difficulty.history_card``).
Here it is read for every candidate topic (one representative item per LO: the candidate's own first item on it,
else the LO's first item AD's material view shows) and the sections are merged by evidence id, so the union of the
candidates' LOs shares **one** token budget (``[router_objective] llm_card_token_budget``, ``keep``), trimmed oldest
first within each section, with what it left out stated. It is built in the prefetch job, never in a serve
transaction, and frozen with the decision's boundary key. Every read goes through AD's material view and
``learner_protection`` exactly as RO2's card (no reference solution, key or rubric; no stem of an unattempted item;
exam work keeps its result only; a probe shows no question or answer), so the card's rules hold on it as on v3.

Beside the history: the goals, their dates, their use weights and the topics each covers (with each topic's effective
weight), the session, and the declared objective.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from contextlib import closing
import json
from typing import Any

#: v2 (Codex review F10): each goal lists its topics and their effective weights.
CARD_VERSION = "router-policy-card-v2 (ad-forecast-state-v3 H3, decision level)"
#: H3's sections, every rung's (RO2's ladder), in its order.
_SECTION_ORDER: tuple[str, ...] = (
    "recent_attempts", "whole_answers", "help", "questions", "reveals", "reading", "inquiries", "self_checks",
    "digests", "other_topics", "teach_backs", "gaps", "exams", "goals",
)


def _size(state: Mapping[str, Any]) -> int:
    return len(json.dumps(state, sort_keys=True, ensure_ascii=False, default=str).encode("utf-8"))


def _merged(built: Sequence[Mapping[str, Any]]) -> tuple[dict[str, list[dict[str, Any]]], list[str], list[str]]:
    history: dict[str, list[dict[str, Any]]] = {}
    seen: dict[str, set[str]] = {}
    limits: set[str] = set()
    scope: list[str] = []
    for one in built:
        limits.update(one.get("row_limits_reached") or ())
        scope.extend(lo for lo in one.get("scope") or () if lo not in scope)
        for name, entries in (one.get("sections") or {}).items():
            bucket = history.setdefault(name, [])
            ids = seen.setdefault(name, set())
            for entry in entries:
                key = str(entry.get("evidence_id") or json.dumps(entry, sort_keys=True, default=str))
                if key not in ids:
                    ids.add(key)
                    bucket.append(dict(entry))
    for entries in history.values():
        entries.sort(key=lambda entry: -(entry.get("days_before") or 0.0))
    return history, sorted(limits), scope


def _trim(state: dict[str, Any], budget: int) -> dict[str, dict[str, int]]:
    """Oldest first within each section, one entry per non-empty section per round, until it fits."""

    history: dict[str, list[dict[str, Any]]] = state["history"]
    left_out: dict[str, dict[str, int]] = {}
    while _size({**state, "left_out": left_out}) > int(budget):
        trimmed = False
        for name in reversed(_SECTION_ORDER):
            entries = history.get(name) or []
            if not entries:
                continue
            entries.pop(0)
            record = left_out.setdefault(name, {"entries": 0})
            record["entries"] += 1
            trimmed = True
            if _size({**state, "left_out": left_out}) <= int(budget):
                break
        if not trimmed:
            break
    return left_out


def _goal_entry(goal: Mapping[str, Any], titles: Mapping[str, str]) -> dict[str, Any]:
    """One goal as the policy sees it (Codex review F10): its date, its use weights and which topics it covers, with
    each topic's effective weight at the date (``dated``, unless ``topic_weights`` names the topic), the same weights
    the numeric policy's scoring reads."""

    entry = {key: value for key, value in goal.items() if key in (
        "due_at", "days_to_date", "dated", "undated_density", "source", "scope")}
    los = [str(lo) for lo in goal.get("los") or ()]
    per_lo = goal.get("per_lo") or {}
    entry["topics"] = [titles.get(lo, lo) for lo in los]
    entry["topic_weights"] = {titles.get(lo, lo): float(per_lo[lo]) for lo in los if lo in per_lo}
    return entry


def decision_card(vault: Any, repository: Any, candidates: Sequence[Any], *, served_at: str,
                  goals: Mapping[str, Any], session: Mapping[str, Any], budget: int) -> dict[str, Any]:
    """The frozen card (the state), its evidence ids and what the budget left out."""

    from learnloop.adaptive_difficulty import history_card as HC
    from learnloop.db.connection import connect

    asked = [(tuple(getattr(candidate, "item_ids", ()) or ()), tuple(getattr(candidate, "learning_object_ids", ()) or ()))
             for candidate in candidates]
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        built = HC.decision_sections_entry(vault, repository, connection, asked, served_at=served_at)
    picked = {one["lo"]: one["item"] for one in built}
    history, limits, scope = _merged(built)
    titles = {lo_id: lo.title for lo_id, lo in vault.learning_objects.items()}
    state: dict[str, Any] = {
        "card": CARD_VERSION,
        "topics": [titles.get(lo, lo) for lo in scope],
        "history": history,
        "row_limits_reached": limits,
        "goals": {goal_id: _goal_entry(goal, titles) for goal_id, goal in goals.items()},
        "session": dict(session),
        "not_recorded": ("Hedges (the grader's reading of an answer's tone) are not on this card; a tutor's answers "
                         "are summarized by the learner's questions only."),
    }
    left_out = _trim(state, budget)
    state["left_out"] = left_out
    evidence = sorted({str(entry["evidence_id"]) for entries in history.values() for entry in entries
                       if entry.get("evidence_id")})
    return {"state": state, "evidence_ids": evidence, "left_out": left_out, "bytes": _size(state),
            "items": dict(picked)}


__all__ = ["CARD_VERSION", "decision_card"]

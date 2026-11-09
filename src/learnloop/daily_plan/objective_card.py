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

**The learner's own statements** (instruct hand-off IH4, spec_instruct_handoff_v1 §7 item 6, ``CARD_VERSION_STATEMENTS``):
with ``[router_objective] preferences_inform_router`` and any on record, what the learner said would help and their notes
are one more section of the history, under the same limits as their questions (:data:`learnloop.adaptive_difficulty.
history_card.ROW_LIMITS`, then the shared budget, oldest first), each marked as their own statement. A note follows the
rule the card's questions follow: on an attempt whose question and answer are protected it shows nothing and says why
(``learner_protection.PastWork``). With none on record the card is v2, byte for byte.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from contextlib import closing
import json
from typing import Any

#: v2 (Codex review F10): each goal lists its topics and their effective weights.
CARD_VERSION = "router-policy-card-v2 (ad-forecast-state-v3 H3, decision level)"
#: v3 (IH4): v2 with the learner's own statements. Named only on a card that holds some.
CARD_VERSION_STATEMENTS = "router-policy-card-v3 (ad-forecast-state-v3 H3, decision level, the learner's own statements)"
#: Slip or gap SG1 (spec_slip_vs_gap_v1 §3 item 3): v2 or v3 with the miss-cause section. Named only on a card that holds
#: an entry, so a card with none keeps its predecessor's version and bytes.
CARD_VERSION_MISS_CAUSES = ("router-policy-card-v4 (ad-forecast-state-v3 H3, decision level, the learner's own statements, "
                            "miss causes)")
MISS_CAUSES = "miss_causes"
STATEMENTS = "learner_statements"
STATEMENTS_NOTE = ("Each entry of history.learner_statements is the learner's own statement of what they thought would "
                   "help, in their words where there is a note. It is context to read, not evidence of what they know "
                   "or of what works: nobody has checked it against outcomes. A decision with no entry says nothing "
                   "about what they wanted.")
#: H3's sections, every rung's (RO2's ladder), in its order.
_SECTION_ORDER: tuple[str, ...] = (
    "miss_causes", "learner_statements", "recent_attempts", "whole_answers", "help", "questions", "reveals", "reading", "inquiries", "self_checks",
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


def learner_statements(vault: Any, repository: Any, connection: Any, *, served_at: str) -> tuple[list[dict[str, Any]], bool]:
    """The learner's statements known at ``served_at``, oldest first, and whether the read reached its limit. The row
    limit is the learner's questions' (no window of its own). Numbers and topics always; a note only as the card's rule
    for the learner's own text lets it out."""

    from learnloop.adaptive_difficulty import history_card as HC
    from learnloop.db.stores import router as router_store
    from learnloop.learner_protection import WITHHELD_UNREADABLE, PastWork
    from learnloop.router_objective.preferences import WORDS
    from learnloop.router_objective_switches import preferences_inform_router_on

    if not preferences_inform_router_on(vault.config):
        return [], False
    limit = int(HC.ROW_LIMITS["questions"])
    rows = router_store.recent_learner_preferences(connection, at=served_at, limit=limit)
    days = HC._Days(served_at)
    past = PastWork(connection, vault, repository)
    out: list[dict[str, Any]] = []
    for row in rows:
        offered = json.loads(row.get("offered_json") or "{}")
        kind = str(row["chosen_kind"])
        picked = offered.get("router_pick") or {}
        served = connection.execute("SELECT chosen_learning_object_id FROM router_decisions WHERE id = ?",
                                    (row.get("served_decision_id"),)).fetchone() if row.get("served_decision_id") else None
        lo = served[0] if served is not None else None
        entry: dict[str, Any] = {
            "evidence_id": f"preference:{row['id']}", "days_before": days(row["created_at"]),
            "source": "the learner's own statement", "said_would_help": WORDS.get(kind, kind),
            "where": row.get("surface"), "plan_had_chosen": WORDS.get(str(picked.get("kind"))) if picked else None}
        if lo:
            entry["topic"] = HC._topic(vault, lo)
        note = str(row.get("note_md") or "").strip()
        if note:
            attempt = row.get("attempt_id")
            reason = past.evidence_reason([attempt] if attempt else ())
            if reason is None and not past.withheld.available:
                reason = WITHHELD_UNREADABLE
            if reason:
                entry["note_withheld"] = reason
            else:
                entry["note"] = HC._excerpt(note, HC.TEXT_LIMIT)
        out.append(entry)
    return out, len(rows) >= limit


def _card_topics(candidates: Sequence[Any]) -> list[str]:
    """SG1: the topics the card shows a miss's cause for: a lesson offer's and each repair candidate's."""

    from learnloop.daily_plan.types import LESSON_OFFER_SUBTYPE

    out: list[str] = []
    for candidate in candidates:
        if getattr(candidate, "subtype", None) == LESSON_OFFER_SUBTYPE or getattr(candidate, "lane", None) == "repair":
            out.extend(str(lo) for lo in getattr(candidate, "learning_object_ids", ()) or () if str(lo) not in out)
    return out


def miss_cause_entries(vault: Any, connection: Any, candidates: Sequence[Any], *, served_at: str) -> list[dict[str, Any]]:
    """SG1 (spec_slip_vs_gap_v1 §3 item 3): for the offer's topic and each repair candidate's, the latest miss's cause
    class probabilities, its surprise in words and its status (:func:`learnloop.router_objective.miss_cause.card_entry`),
    probe attempts included. Never a hypothesis's statement or the answer. Empty off, below the tag, or with none."""

    from learnloop.adaptive_difficulty import history_card as HC
    from learnloop.router_objective import miss_cause as MC
    from learnloop.router_objective_switches import miss_cause_sensor_on

    if not miss_cause_sensor_on(vault.config):
        return []
    topics = _card_topics(candidates)
    if not topics:
        return []
    records = MC.sensor(connection, vault.config, topics, served_at)
    if not records:
        return []
    reference = MC.surprise_reference(connection, vault.config, served_at)
    days = HC._Days(served_at)
    return [MC.card_entry(records[lo], topic=HC._topic(vault, lo), days_before=days(records[lo]["attempt_at"]),
                          reference=reference) for lo in topics if lo in records]


def miss_cause_lines(vault: Any, repository: Any, candidates: Sequence[Any], *, served_at: str, budget: int) -> list[str]:
    """The same entries for the mid-block ``plan_interrupt`` request, whose state is text (the LLM's request only, never
    the Decider's), oldest dropped first to fit ``budget``. None: no line, so the request is the predecessor's."""

    from learnloop.db.connection import connect

    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        entries = miss_cause_entries(vault, connection, candidates, served_at=served_at)
    entries.sort(key=lambda entry: -(entry.get("days_before") or 0.0))
    from learnloop.router_objective.miss_cause import CARD_NOTE

    head = ["# What the last miss on each topic was",
            CARD_NOTE.replace("Each entry of history.miss_causes", "Each line below")]

    def lines() -> list[str]:
        return [*head, *(json.dumps(entry, sort_keys=True, ensure_ascii=False, default=str) for entry in entries)]

    # The heading and the note count against the budget too (Codex F9).
    while entries and len("\n".join(lines()).encode("utf-8")) > int(budget):
        entries.pop(0)
    return lines() if entries else []


def statement_lines(vault: Any, repository: Any, *, served_at: str, budget: int) -> list[str]:
    """The same statements for the mid-block ``plan_interrupt`` request, whose state is text: lines for the LLM's request
    only (never the Decider's), oldest dropped first to fit ``budget``. Nothing on record or switched off: no line, so the
    request is the predecessor's."""

    from learnloop.db.connection import connect

    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        entries, _limited = learner_statements(vault, repository, connection, served_at=served_at)
    while entries and _size({"entries": entries}) > int(budget):
        entries.pop(0)
    if not entries:
        return []
    return ["# The learner's own statements", STATEMENTS_NOTE.replace("Each entry of history.learner_statements",
                                                                      "Each line below"),
            *(json.dumps(entry, sort_keys=True, ensure_ascii=False, default=str) for entry in entries)]


def decision_card(vault: Any, repository: Any, candidates: Sequence[Any], *, served_at: str,
                  goals: Mapping[str, Any], session: Mapping[str, Any], budget: int) -> dict[str, Any]:
    """The frozen card (the state), its evidence ids and what the budget left out."""

    from learnloop.adaptive_difficulty import history_card as HC
    from learnloop.db.connection import connect

    asked = [(tuple(getattr(candidate, "item_ids", ()) or ()), tuple(getattr(candidate, "learning_object_ids", ()) or ()))
             for candidate in candidates]
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        built = HC.decision_sections_entry(vault, repository, connection, asked, served_at=served_at)
        statements, statements_limited = learner_statements(vault, repository, connection, served_at=served_at)
        causes = miss_cause_entries(vault, connection, candidates, served_at=served_at)
    picked = {one["lo"]: one["item"] for one in built}
    history, limits, scope = _merged(built)
    if statements:
        history[STATEMENTS] = statements
    if statements_limited:
        limits = sorted({*limits, STATEMENTS})
    if causes:
        # SG1: oldest first, as every section (the budget trims the oldest of a section first).
        history[MISS_CAUSES] = sorted(causes, key=lambda entry: -(entry.get("days_before") or 0.0))
    titles = {lo_id: lo.title for lo_id, lo in vault.learning_objects.items()}
    from learnloop.router_objective.miss_cause import CARD_NOTE

    state: dict[str, Any] = {
        "card": (CARD_VERSION_MISS_CAUSES if causes else CARD_VERSION_STATEMENTS if statements else CARD_VERSION),
        **({"learner_statements_are": STATEMENTS_NOTE} if statements else {}),
        **({"miss_causes_are": CARD_NOTE} if causes else {}),
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
    out = {"state": state, "evidence_ids": evidence, "left_out": left_out, "bytes": _size(state),
           "items": dict(picked), "statements": len(history.get(STATEMENTS) or ())}
    if causes:
        out["miss_causes"] = len(history.get(MISS_CAUSES) or ())
    return out


__all__ = ["CARD_VERSION", "CARD_VERSION_MISS_CAUSES", "CARD_VERSION_STATEMENTS", "MISS_CAUSES", "STATEMENTS",
           "STATEMENTS_NOTE", "decision_card", "learner_statements", "miss_cause_entries", "miss_cause_lines",
           "statement_lines"]

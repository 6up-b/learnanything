"""``learnloop data-capture report``'s section on what the learner said would help (instruct hand-off IH4,
spec_instruct_handoff_v1 §7 items 4-5). Read-only, and nothing reads it back.

Everything here is **self-selected** (:data:`picks.DELAYED_LABEL`): the learner chose when to use the link and what to
choose, and nothing after it is randomized, so no line estimates what following the learner does. A comparison of an
override with a router draw of the same kind is a description of two differently selected groups, and says so.

* **Agreement**: among preferences with a draw waiting, what the plan had drawn against what the learner chose, by kind. A
  preference with no draw has nothing to agree with and is counted apart.
* **Override rate**: overrides (``learner_pick`` decisions from the link) over preferences with a draw, and beside it over
  the plan's decisions since the first preference. The rest of those decisions said nothing: never agreement.
* **Follow-through**: whether what the choice asked for happened (a question answered, a lesson opened on the topic, a
  reading read, the session stopped).
* **Later cold results**: the first later unassisted, unprimed graded answer on the chosen topic (as RO5's picks read it),
  per kind for overrides, agreements and no-draw preferences, and for the router's own draws of that kind.

The same section reports where ``w_pref`` stands, from the latest trace, and what would move it.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping
import json
from typing import Any

from learnloop.db.stores import router as router_store
from learnloop.router_objective.picks import DELAYED_LABEL
from learnloop.router_objective.preferences import KINDS, STOP, kind_of

VERSION = "ih4_preference_report_v1"
SELF_SELECTED = DELAYED_LABEL
COMPARISON_LABEL = (f"{DELAYED_LABEL}; the router's draw of the same kind is randomized only in what it drew, and the "
                    "groups differ in who chose and when, so neither column says which works better")
NOT_USING = "a decision where the link wasn't used said nothing: it is never counted as agreeing with what was served"
OFFER_PREFIX = "lesson_offer:"
WHAT_MOVES_W_PREF = (
    "w_pref is fitted only on the mix's randomized draws, never on a pick. It moves once a decision with a frozen sensor "
    "(any preference with frozen features before it) has some spread under its served distribution, its window has "
    "closed, and the randomized checks' returns, with their missing terms at the least favourable fill, give a positive "
    "slope; with fewer than three draws the rank's chance stays one half.")


def _later_cold(connection: Any, lo: str | None, after: str) -> float | None:
    if not lo:
        return None
    row = connection.execute(
        "SELECT correctness FROM practice_attempts WHERE learning_object_id = ? AND created_at > ? AND correctness IS NOT "
        "NULL AND COALESCE(hints_used, 0) = 0 AND COALESCE(primed, 0) = 0 ORDER BY created_at, id LIMIT 1",
        (lo, after)).fetchone()
    return float(row[0]) if row is not None else None


def _block(connection: Any, decision_id: str | None) -> Mapping[str, Any] | None:
    if not decision_id:
        return None
    row = connection.execute("SELECT id, lane, subtype, reading_json FROM attention_blocks WHERE decision_ref = ? "
                             "ORDER BY created_at, id LIMIT 1", (decision_id,)).fetchone()
    return dict(row) if row is not None else None


def _topic_of(connection: Any, ref: Any, decision_id: str | None) -> str | None:
    """The topic a choice or a draw names: a lesson's from its ref, else the decision's, else its block's first."""

    if str(ref or "").startswith(OFFER_PREFIX):
        return str(ref)[len(OFFER_PREFIX):]
    if not decision_id:
        return None
    row = connection.execute("SELECT chosen_learning_object_id FROM router_decisions WHERE id = ?", (decision_id,)).fetchone()
    if row is not None and row[0]:
        return str(row[0])
    found = connection.execute("SELECT neighborhood_json FROM attention_blocks WHERE decision_ref = ? ORDER BY created_at, id "
                               "LIMIT 1", (decision_id,)).fetchone()
    los = (json.loads(found[0] or "{}").get("learning_object_ids") or ()) if found is not None else ()
    return str(los[0]) if los else None


def _lesson_opened(connection: Any, lo: str | None, after: str) -> bool:
    if not lo or connection.execute("SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'lessons'").fetchone() is None:
        return False
    return connection.execute(
        "SELECT 1 FROM lessons, json_each(lessons.learning_object_ids_json) WHERE json_each.value = ? AND opened_at >= ? "
        "LIMIT 1", (lo, after)).fetchone() is not None


def _followed(connection: Any, row: Mapping[str, Any], lo: str | None) -> bool | None:
    """Whether what the choice asked for happened; None where nothing could say (no decision logged, no block placed)."""

    kind, served, at = str(row["chosen_kind"]), row.get("served_decision_id"), str(row["created_at"])
    if kind == "lesson":
        return _lesson_opened(connection, lo, at)
    if kind == STOP:
        return True if served else None
    block = _block(connection, served)
    if block is None:
        return None
    if block.get("reading_json"):
        return connection.execute("SELECT 1 FROM attention_block_events WHERE block_id = ? AND kind = 'block_ended' AND "
                                  "COALESCE(json_extract(detail_json, '$.minutes_counted'), 0) > 0 LIMIT 1",
                                  (block["id"],)).fetchone() is not None
    return connection.execute("SELECT 1 FROM plan_presentations p JOIN practice_attempts a ON a.plan_presentation_id = p.id "
                              "WHERE p.block_id = ? AND a.created_at >= ? LIMIT 1", (block["id"], at)).fetchone() is not None


def _mean(values: list[float]) -> dict[str, Any]:
    return {"n": len(values), "mean": round(sum(values) / len(values), 4) if values else None}


def _standing(connection: Any) -> dict[str, Any]:
    """``w_pref`` as the latest ``plan_block`` trace froze it, and how many decisions carry the sensor."""

    if connection.execute("SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'router_objective_traces'"
                          ).fetchone() is None:
        return {"w_pref": 0.0, "decisions_with_the_sensor": 0, "status": "no_traces_table",
                "what_moves_it": WHAT_MOVES_W_PREF}
    rows = connection.execute(
        "SELECT json_extract(trace_json, '$.preference.w_pref'), json_extract(trace_json, '$.preference.weight.n'), "
        "json_extract(trace_json, '$.preference.status') FROM router_objective_traces WHERE decision_kind = 'plan_block' "
        "AND json_extract(trace_json, '$.preference') IS NOT NULL ORDER BY created_at, id").fetchall()
    latest = rows[-1] if rows else None
    return {"w_pref": float(latest[0] or 0.0) if latest is not None else 0.0, "draws_it_read": latest[1] if latest else 0,
            "decisions_with_the_sensor": len(rows),
            "status": str(latest[2]) if latest is not None else "no decision has read a preference yet",
            "what_moves_it": WHAT_MOVES_W_PREF}


def section(connection: Any) -> dict[str, Any]:
    """The section (module docstring), read-only."""

    if not router_store.preferences_present(connection):
        return {"available": False, "reason": "this database predates the preference ledger", "label": SELF_SELECTED}
    rows = router_store.learner_preference_rows(connection)
    agreement: dict[str, Counter[str]] = {}
    by_kind: dict[str, Counter[str]] = {kind: Counter() for kind in KINDS}
    follow: dict[str, Counter[str]] = {kind: Counter() for kind in KINDS}
    cold: dict[str, dict[str, list[float]]] = {kind: {"override": [], "agreed": [], "no_draw": []} for kind in KINDS}
    overrides = with_a_draw = agreed = no_draw = with_notes = 0
    no_draw_reasons: Counter[str] = Counter()
    overridden: set[str] = set()
    for row in rows:
        kind = str(row["chosen_kind"])
        offered = json.loads(row.get("offered_json") or "{}")
        parent, served = row.get("decision_id"), row.get("served_decision_id")
        by_kind.setdefault(kind, Counter())["preferences"] += 1
        with_notes += 1 if str(row.get("note_md") or "").strip() else 0
        if parent is None:
            no_draw += 1
            no_draw_reasons[str(offered.get("no_draw") or "unstated")] += 1
            route = "no_draw"
        else:
            with_a_draw += 1
            pick = str((offered.get("router_pick") or {}).get("kind") or "unstated")
            agreement.setdefault(pick, Counter())[kind] += 1
            if served == parent:
                agreed += 1
                route = "agreed"
            else:
                overrides += 1
                overridden.add(str(parent))
                route = "override"
        by_kind[kind][route] += 1
        lo = _topic_of(connection, row.get("chosen_ref"), str(served) if served else None)
        result = _followed(connection, row, lo)
        follow.setdefault(kind, Counter())["unknown" if result is None else "followed" if result else "not_followed"] += 1
        later = _later_cold(connection, lo, str(row["created_at"]))
        if later is not None and kind in cold:
            cold[kind][route].append(later)
    first = str(rows[0]["created_at"]) if rows else None
    decisions = int(connection.execute(
        "SELECT COUNT(*) FROM router_decisions WHERE decision_kind = 'plan_block' AND created_at >= ?", (first,)
    ).fetchone()[0]) if first else 0
    draws: dict[str, list[float]] = {kind: [] for kind in KINDS}
    if first:
        for decision_id, chosen, created in connection.execute(
                "SELECT id, chosen_ref, created_at FROM router_decisions WHERE decision_kind = 'plan_block' AND created_at "
                ">= ? ORDER BY created_at, id", (first,)).fetchall():
            if str(decision_id) in overridden or chosen == "stop_for_today":
                continue
            block = _block(connection, str(decision_id))
            if block is None:
                continue
            kind = kind_of(reading=block.get("reading_json") or None, subtype=block.get("subtype"), lane=block.get("lane"))
            later = _later_cold(connection, _topic_of(connection, chosen, str(decision_id)), str(created))
            if later is not None:
                draws[kind].append(later)
    return {
        "available": True, "version": VERSION, "label": SELF_SELECTED,
        "preferences": len(rows), "with_a_note": with_notes,
        "with_a_draw": with_a_draw, "no_draw": no_draw, "no_draw_reasons": dict(no_draw_reasons),
        "agreement_by_kind": {"label": f"{SELF_SELECTED}; {NOT_USING}",
                              "agreed": agreed,
                              "router_drew_learner_chose": {pick: dict(found) for pick, found in sorted(agreement.items())},
                              "by_learner_kind": {kind: dict(found) for kind, found in by_kind.items() if found}},
        "override_rate": {"label": f"{SELF_SELECTED}; {NOT_USING}", "overrides": overrides,
                          "of_preferences_with_a_draw": round(overrides / with_a_draw, 4) if with_a_draw else None,
                          "plan_decisions_since_the_first": decisions,
                          "of_plan_decisions_since_the_first": round(overrides / decisions, 4) if decisions else None},
        "follow_through": {"label": SELF_SELECTED, "by_kind": {kind: dict(found) for kind, found in follow.items() if found}},
        "later_cold_results": {
            "label": COMPARISON_LABEL,
            "by_kind": {kind: {**{route: _mean(values) for route, values in cold[kind].items()},
                               "router_draw": _mean(draws[kind])}
                        for kind in KINDS if any(cold[kind].values()) or draws[kind]}},
        "w_pref": _standing(connection),
    }


def lines(report: Mapping[str, Any]) -> list[str]:
    if not report.get("available"):
        return [f"Learner preferences: unavailable ({report.get('reason')})"]
    rate = report["override_rate"]
    standing = report["w_pref"]
    return [
        f"Learner preferences ({report['version']}; self-selected: {report['label']}): {report['preferences']} "
        f"({report['with_a_draw']} with a draw, {report['no_draw']} with none, {report['with_a_note']} with a note)",
        f"  router drew / learner chose (self-selected): {report['agreement_by_kind']['router_drew_learner_chose']}; "
        f"agreed {report['agreement_by_kind']['agreed']}",
        f"  override rate (self-selected): {rate['overrides']} overrides, {rate['of_preferences_with_a_draw']} of "
        f"preferences with a draw, {rate['of_plan_decisions_since_the_first']} of "
        f"{rate['plan_decisions_since_the_first']} plan decisions; {NOT_USING}",
        f"  follow-through (self-selected): {report['follow_through']['by_kind']}",
        f"  later cold results (self-selected): {report['later_cold_results']['by_kind']}",
        f"  w_pref {standing['w_pref']} ({standing['status']}; {standing['decisions_with_the_sensor']} decisions with the "
        f"sensor); {standing['what_moves_it']}",
    ]


__all__ = ["COMPARISON_LABEL", "NOT_USING", "SELF_SELECTED", "VERSION", "WHAT_MOVES_W_PREF", "lines", "section"]

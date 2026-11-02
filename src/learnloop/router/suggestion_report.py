"""Teacher TE1b's lesson suggestions: the intention-to-treat split (``learnloop router report``).

Follow-ups batch 6 (G2; TE1b open item): every ``lesson_suggestion`` decision, shown or not, by its
randomized arm (``card``: the card was shown; ``no_card``: it was drawn and not shown), with the
funnel the card arm went through (offered, accepted, opened, completed) and the predeclared ITT
outcome (the drawn LO's first eligible cold retrieval, ``router.outcomes``' ``S = R_cold``).

Pure: the caller reads the logged ledgers (the decisions, the response ledger, the lessons and the
outcomes derived from them) and passes them in; nothing here reads a database, calls a model or
writes. Rates are Hájek estimates weighted by ``1 / P(arm | drawn target)`` (the decision's
``arm_propensity``, logged at the draw; 1 when the ceiling bound it), so each arm stands for every
drawn target; raw counts are printed beside them. A decision whose arm propensity is missing or
not positive is counted but left out of the weighted figures (named in ``unweighted``). A report,
never a switch: nothing here changes what the router or the card does.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

#: The arms, in the order the report prints them.
ARMS: tuple[str, ...] = ("card", "no_card")
#: A lesson opened from a suggestion that closed with its goal reached is "completed".
COMPLETED_REASON = "goal_reached"
TAKEN = ("accepted", "chose_alternative")


def _weight(detail: Mapping[str, Any]) -> float | None:
    try:
        propensity = float(detail.get("arm_propensity"))
    except (TypeError, ValueError):
        return None
    return 1.0 / propensity if propensity > 0.0 else None


def _hajek(pairs: Iterable[tuple[float, float]]) -> float | None:
    total = value = 0.0
    for weight, outcome in pairs:
        total += weight
        value += weight * outcome
    return round(value / total, 6) if total > 0.0 else None


def itt_split(decisions: Iterable[Mapping[str, Any]], responses: Iterable[Mapping[str, Any]],
              releases: Iterable[Mapping[str, Any]], lessons: Mapping[str, Mapping[str, Any]],
              outcomes: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    """The split (module docstring). ``decisions``: ``router_suggestions.decisions`` (with
    ``detail``); ``responses``: the learner responses; ``releases``: released and expired rows;
    ``lessons``: lesson id -> its row (``origin_ref``, ``close_reason``); ``outcomes``: decision id
    -> its derived outcome."""

    answer = {str(row["decision_id"]): row for row in responses}
    let_go = {str(row["decision_id"]): str(row["response"]) for row in releases}
    rows: dict[str, list[dict[str, Any]]] = {arm: [] for arm in ARMS}
    for decision in decisions:
        detail = decision.get("detail") or {}
        decision_id = str(decision["id"])
        arm = "card" if detail.get("shown") else "no_card"
        response_row = answer.get(decision_id)
        response = str(response_row["response"]) if response_row else None
        lesson = lessons.get(str((response_row or {}).get("lesson_id") or "")) if response in TAKEN else None
        opened = bool(lesson) and str(lesson.get("origin_ref") or "") == decision_id
        outcome = outcomes.get(decision_id) or {}
        observed = outcome.get("s_status") == "final" and outcome.get("s_value") is not None
        rows[arm].append({
            "weight": _weight(detail), "arm_propensity": detail.get("arm_propensity"), "response": response,
            "taken": response in TAKEN, "opened": opened,
            "completed": opened and str((lesson or {}).get("close_reason") or "") == COMPLETED_REASON,
            "released": let_go.get(decision_id) == "released", "expired": let_go.get(decision_id) == "expired",
            "observed": observed, "s": float(outcome["s_value"]) if observed else None,
        })
    arms: dict[str, Any] = {}
    for arm in ARMS:
        entries = rows[arm]
        weighted = [entry for entry in entries if entry["weight"] is not None]
        responses_count = {kind: sum(entry["response"] == kind for entry in entries)
                           for kind in ("accepted", "chose_alternative", "declined", "ignored")}
        propensities = [float(entry["arm_propensity"]) for entry in weighted]
        arms[arm] = {
            "decisions": len(entries),
            "unweighted": len(entries) - len(weighted),
            "weight": round(sum(entry["weight"] for entry in weighted), 6),
            "mean_arm_propensity": round(sum(propensities) / len(propensities), 6) if propensities else None,
            "funnel": {
                "offered": len(entries) if arm == "card" else 0,
                "accepted": sum(entry["taken"] for entry in entries),
                "opened": sum(entry["opened"] for entry in entries),
                "completed": sum(entry["completed"] for entry in entries),
            },
            "responses": {**responses_count,
                          "unanswered": sum(entry["response"] is None for entry in entries) if arm == "card" else 0,
                          "released": sum(entry["released"] for entry in entries),
                          "expired": sum(entry["expired"] for entry in entries)},
            "weighted_rates": {key: _hajek((entry["weight"], float(entry[key])) for entry in weighted)
                               for key in ("taken", "opened", "completed")},
            "outcome": {
                "observed": sum(entry["observed"] for entry in entries),
                "pending": sum(not entry["observed"] for entry in entries),
                "weighted_mean_r_cold": _hajek((entry["weight"], entry["s"]) for entry in weighted
                                               if entry["observed"]),
            },
        }
    card, none = arms["card"]["outcome"]["weighted_mean_r_cold"], arms["no_card"]["outcome"]["weighted_mean_r_cold"]
    return {
        "decisions": sum(arms[arm]["decisions"] for arm in ARMS),
        "weights": "1 / P(arm | drawn target), Hajek",
        "arms": arms,
        "itt_difference_r_cold": round(card - none, 6) if card is not None and none is not None else None,
    }


def lines(split: Mapping[str, Any]) -> list[str]:
    """The split in plain words (the text report)."""

    out = [f"Lesson suggestions (teacher TE1b): {split['decisions']} decisions, intention to treat by arm "
           f"(rates weighted by {split['weights']}; raw counts beside them)."]
    for arm in ARMS:
        row = split["arms"][arm]
        funnel, rates, outcome, said = row["funnel"], row["weighted_rates"], row["outcome"], row["responses"]

        def rate(key: str) -> str:
            value = rates[key]
            return "-" if value is None else f"{value:.2f}"

        mean = outcome["weighted_mean_r_cold"]
        if arm == "card":
            out.append(
                f"- card shown: {row['decisions']} (mean P(arm) {row['mean_arm_propensity'] or '-'}); offered "
                f"{funnel['offered']}, accepted {funnel['accepted']} ({rate('taken')}; {said['chose_alternative']} "
                f"chose an alternative), opened {funnel['opened']} ({rate('opened')}), completed "
                f"{funnel['completed']} ({rate('completed')}); not now {said['declined']}, no answer "
                f"{said['ignored']}, unanswered {said['unanswered']}, let go before opening {said['released']}, "
                f"set aside {said['expired']}.")
        else:
            out.append(f"- no card: {row['decisions']} (mean P(arm) {row['mean_arm_propensity'] or '-'}).")
        out.append(f"  R_cold on the drawn topic: observed {outcome['observed']}, pending {outcome['pending']}, "
                   f"weighted mean {'-' if mean is None else f'{mean:.2f}'}."
                   + (f" ({row['unweighted']} without a logged arm propensity, unweighted)" if row["unweighted"] else ""))
    difference = split["itt_difference_r_cold"]
    out.append("ITT difference in R_cold (card - no card): "
               + ("- (an arm has no observed outcome yet)" if difference is None else f"{difference:+.2f}")
               + ". A report only: no switch is claimed.")
    return out


__all__ = ["ARMS", "COMPLETED_REASON", "itt_split", "lines"]

"""The router's decision, in one plain line (spec §6.4). Display only: nothing reads it back.

> Router: ask now · drawn by LLM · ask now 62%, wait 38% · floor 5%

For debugging and calibration; ``ui.show_router_decisions`` turns it off. It covers
follow-up decisions and ordinary block choices alike.
"""

from __future__ import annotations

from collections.abc import Mapping
import json
from typing import Any

from learnloop.db.repositories import Repository

_ARMS: Mapping[str, str] = {
    "insert_now": "ask now", "continue_current": "wait", "no_intervention": "no question", "decline": "can't ask",
}
_DRAWS: Mapping[str, str] = {
    "llm": "drawn by LLM", "decider": "drawn by Decider", "staged": "drawn by the rules", "uniform": "drawn by the floor",
}
_MODELS: Mapping[str, str] = {"decider": "Decider", "llm": "LLM"}


def show_router_decisions(vault: Any) -> bool:
    return bool(getattr(getattr(vault.config, "ui", None), "show_router_decisions", False))


def _parsed(value: Any) -> Any:
    if isinstance(value, str):
        try:
            return json.loads(value)
        except ValueError:
            return None
    return value


def _label(ref: str) -> str:
    return _ARMS.get(ref, ref.replace("_", " "))


def _percent(value: float) -> str:
    return f"{round(value * 100)}%"


def decision_view(repository: Repository, decision_id: str | None) -> dict[str, Any] | None:
    """The line and its *details*, or None for a decision the ledger doesn't hold."""

    if not decision_id:
        return None
    with repository.connection() as connection:
        row = connection.execute("SELECT * FROM router_decisions WHERE id = ?", (decision_id,)).fetchone()
        card_row = connection.execute(
            "SELECT content_text FROM router_decision_payloads WHERE decision_id = ? AND kind = 'card'", (decision_id,)
        ).fetchone()
    if row is None:
        return None
    candidates = _parsed(row["candidates_json"]) or []
    detail = _parsed(row["detail_json"]) or {}
    mixture = detail.get("mixture") if isinstance(detail, Mapping) else None
    mixture = mixture if isinstance(mixture, Mapping) else {}
    shares = [
        (str(entry.get("ref")), float(entry.get("propensity") or 0.0)) for entry in candidates
        if isinstance(entry, Mapping) and float(entry.get("propensity") or 0.0) > 0.0
    ]
    shares.sort(key=lambda pair: -pair[1])
    drawn = str(mixture.get("drawn_component") or "")
    parts = [f"Router: {_label(str(row['chosen_ref']))}"]
    parts.append(_DRAWS.get(drawn, "by the rules"))
    if shares:
        parts.append(", ".join(f"{_label(ref)} {_percent(value)}" for ref, value in shares))
    if mixture.get("epsilon") is not None:
        parts.append(f"floor {_percent(float(mixture['epsilon']))}")
    models: list[dict[str, Any]] = []
    for name, summary in sorted((mixture.get("models") or {}).items()):
        if not isinstance(summary, Mapping):
            continue
        models.append({"name": _MODELS.get(str(name), str(name)), "status": summary.get("status"),
                       "answer": summary.get("distribution") or summary.get("p_yes")})
    rationale = mixture.get("rationale")
    return {
        "decision_id": str(row["id"]),
        "line": " · ".join(parts),
        "details": {
            "card_summary": str(card_row[0]) if card_row is not None and card_row[0] else None,
            "models": models,
            "rationale": rationale.get("text") if isinstance(rationale, Mapping) else None,
            "fallback": row["fallback"],
            "observational": detail.get("observational") if isinstance(detail, Mapping) else None,
        },
    }


__all__ = ["decision_view", "show_router_decisions"]

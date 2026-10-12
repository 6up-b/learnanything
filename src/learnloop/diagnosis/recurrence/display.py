"""The escalated repair as one of the attempt's repair suggestions (Slice 2 §3.7).

When a recurrence group reaches K and the diagnosis offered no repair with a
new operator, the escalation writes one (``repair_source = generated``). That
repair is a repair suggestion like any other (second review F4): it carries
its eliciting question, representation and practice mode, it was validated
when it was written, and every surface that shows the attempt's repairs shows
it FIRST, so the feedback screen's lead repair and its "one question,
unaided" response box are the escalated repair's. Its id is
``escalation:<diagnosis id>``; showing it is charged to the reveal ledger
once (basis ``repair_display:escalation:<diagnosis id>``), independently of
the diagnosis's own repairs, which may have been charged before it existed.

This is a DISPLAY overlay: ``Repository.fetch_attempt_feedback_metadata``
(what materialization and repair selection read) is unchanged, so showing the
escalated repair never rewrites a hypothesis or its repair class. It follows
the escalation card's switch (``recurrence.escalation_card_enabled``).
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

ESCALATION_SUGGESTION_PREFIX = "escalation:"


def escalation_suggestion_id(diagnosis_id: str) -> str:
    return f"{ESCALATION_SUGGESTION_PREFIX}{diagnosis_id}"


def is_escalation_suggestion(suggestion: Mapping[str, Any]) -> bool:
    return str(suggestion.get("id") or "").startswith(ESCALATION_SUGGESTION_PREFIX)


def generated_repair(escalation: Mapping[str, Any] | None) -> dict[str, Any] | None:
    """The escalation receipt's generated repair, with its suggestion id."""

    if escalation is None or escalation.get("repair_source") != "generated":
        return None
    repair = escalation.get("repair")
    if not isinstance(repair, Mapping):
        return None
    out = dict(repair)
    out.setdefault("id", escalation_suggestion_id(str(escalation["diagnosis_id"])))
    return out


def escalated_repair(repository: Any, attempt_id: str) -> dict[str, Any] | None:
    """The generated escalated repair of the diagnosis in force, if any."""

    diagnosis = repository.current_live_diagnosis(attempt_id)
    if diagnosis is None:
        return None
    return generated_repair(repository.recurrence_escalation(str(diagnosis["id"])))


def displayed_repair_suggestions(
    vault: Any, repository: Any, attempt_id: str, suggestions: Iterable[Any] | None
) -> list[dict[str, Any]]:
    """The attempt's repair suggestions as shown: the escalated repair first."""

    rows = [dict(row) for row in suggestions or [] if isinstance(row, Mapping)]
    config = getattr(getattr(vault, "config", None), "recurrence", None)
    if config is not None and not bool(getattr(config, "escalation_card_enabled", True)):
        return rows
    try:
        repair = escalated_repair(repository, attempt_id)
    except Exception:  # noqa: BLE001 - a schema without the receipts shows what it has
        return rows
    if repair is None or any(str(row.get("id") or "") == repair["id"] for row in rows):
        return rows
    return [repair, *rows]


__all__ = [
    "ESCALATION_SUGGESTION_PREFIX",
    "displayed_repair_suggestions",
    "escalated_repair",
    "escalation_suggestion_id",
    "generated_repair",
    "is_escalation_suggestion",
]

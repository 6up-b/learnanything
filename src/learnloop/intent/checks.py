"""Serving "Check once" (spec §5.2) and how a served check looks (Reader §9.3).

* :func:`settle_answered_checks` writes ``satisfy_single_check`` for every
  pending check an attempt has answered (an attempt on an item it decides at
  or after its date). Resolution already reads such a check as ``satisfied``
  (``serving.build_checks``), so this only makes the commitment's own
  disposition say so; it runs where a Today build prepares (never in replay).
* :func:`served_check` is the practice view of a due check (DL2's surface,
  Reader §9.3 item 10, D42, D46): the cold banner; help is never blocked, and
  the help ladder's header states the consequence (no confirmation dialog);
  the header locates nothing (no exercise number, page, section, link or
  *why*) until feedback. Only when the one eligibility decision lets the
  item be taken cold now (DL2 Codex review F3): an item whose answer was
  shown is labelled practice instead, with no cold banner or ladder header,
  and the check comes back after its delay.
* :func:`restoration_link` (Reader §9.3 item 9): after the measurement, "Back
  to where you studied this" when the commitment's provenance carries inquiry
  roots or anchor spans (RW6b supplies them; rendered only when present).
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from typing import Any

from learnloop.clock import Clock, SystemClock
from learnloop.curriculum import commitments as C
from learnloop.scheduling.intent.serving import CheckState, intent_serving

#: The cold banner (Reader §9.3 item 10, verbatim).
COLD_BANNER = "A check on your own. Help is still here — using it makes this practice with help."
#: The help ladder's header during a check on your own (D42): stated before a
#: rung is taken; Enter on a rung takes it (the ladder's choose-then-take).
HELP_LADDER_HEADER = "Taking any help makes this attempt practice with help, not a check on your own."
#: The plan line's purpose before the check (kept; the check itself says none).
PLAN_LINE = "check · on your own"
#: F3: a check's item that cannot be taken cold now (its answer was shown):
#: honest about what this attempt is, and that the check is not lost.
PRACTICE_BANNER = (
    "Practice: you've seen this answer, so this one is practice, not your check on your own. "
    "Your check comes back later."
)


def settle_answered_checks(vault: Any, repository: Any, *, clock: Clock | None = None) -> list[str]:
    """Satisfy every pending check an attempt has answered. Returns their ids."""

    now = (clock or SystemClock()).now()
    serving = intent_serving(vault, repository, now=now)
    if serving is None:
        return []
    settled: list[str] = []
    for check in serving.checks.values():
        if check.answered_by is None:
            continue
        if C.resolve_disposition(repository, check.commitment_id) != "one_check_pending":
            continue
        C.satisfy_single_check(
            repository, commitment_id=check.commitment_id, administration_id=check.answered_by, clock=clock
        )
        settled.append(check.commitment_id)
    if settled:
        repository.bump_queue_revision(clock=clock)
    return settled


def restoration_link(provenance: Mapping[str, Any]) -> dict[str, Any] | None:
    """The way back to where it was studied, or None (rendered only when present)."""

    roots = [str(value) for value in (provenance.get("inquiry_root_event_ids") or []) if value]
    spans = [str(value) for value in (provenance.get("anchor_span_ids") or []) if value]
    if not roots and not spans:
        return None
    return {
        "label": "Back to where you studied this",
        "detail": str(provenance.get("restoration_label") or "") or None,
        "inquiry_root_event_ids": roots,
        "anchor_span_ids": spans,
        "extraction_id": provenance.get("extraction_id"),
        "source_id": provenance.get("source_id"),
    }


def _view(check: CheckState, *, cold: bool) -> dict[str, Any]:
    if not cold:
        # F3: practice, honestly labelled; nothing to protect, so the item
        # shows as any practice does (no ladder header, locators shown).
        return {
            "kind": "check_once",
            "commitment_id": check.commitment_id,
            "due_since": check.date.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "date_source": check.date_source,
            "cold": False,
            "banner": PRACTICE_BANNER,
            "locators_hidden": False,
            "restoration": None,
        }
    return {
        "kind": "check_once",
        "commitment_id": check.commitment_id,
        "due_since": check.date.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "date_source": check.date_source,
        "cold": True,
        "banner": COLD_BANNER,
        "help_header": HELP_LADDER_HEADER,
        # D46: the header names nothing that locates the exercise until feedback.
        "locators_hidden": True,
        "restoration": restoration_link(check.provenance),
    }


def served_check(vault: Any, repository: Any, practice_item_id: str, *, now: datetime) -> dict[str, Any] | None:
    """The practice view of ``practice_item_id`` when it is a due check now:
    cold only when the one eligibility decision says so at this serve (F3:
    an exposure after the check was planned is read here)."""

    serving = intent_serving(vault, repository, now=now)
    if serving is None:
        return None
    check = serving.check_for(practice_item_id)
    if check is None or not check.due or check.answered_by is not None or practice_item_id not in check.candidates:
        return None
    return _view(check, cold=check.cold(practice_item_id))


def answered_check(vault: Any, repository: Any, attempt_id: str) -> dict[str, Any] | None:
    """The check an attempt answered (its feedback shows the restoration
    link), or None. Reads the satisfying event if written, else derives it."""

    with repository.connection() as connection:
        rows = connection.execute(
            "SELECT commitment_id FROM commitment_events WHERE kind = 'disposition_changed' "
            "AND json_extract(detail_json, '$.disposition') = 'satisfied' "
            "AND json_extract(detail_json, '$.administration_id') = ? ORDER BY created_at, id",
            (attempt_id,),
        ).fetchall()
    commitment_ids = [str(row[0]) for row in rows]
    if not commitment_ids:
        serving = intent_serving(vault, repository, now=SystemClock().now())
        if serving is None:
            return None
        commitment_ids = [check.commitment_id for check in serving.checks.values() if check.answered_by == attempt_id]
    for commitment_id in commitment_ids:
        try:
            versions = repository.commitment_versions_for(commitment_id)
        except Exception:  # noqa: BLE001 - display only
            continue
        provenance: dict[str, Any] = {}
        if versions:
            import json

            first = min(versions, key=lambda row: int(row["version"]))
            try:
                provenance = json.loads(first.get("provenance_json") or "{}") or {}
            except ValueError:
                provenance = {}
        return {"kind": "check_once", "commitment_id": commitment_id, "restoration": restoration_link(provenance)}
    return None


__all__ = [
    "COLD_BANNER",
    "HELP_LADDER_HEADER",
    "PLAN_LINE",
    "PRACTICE_BANNER",
    "answered_check",
    "restoration_link",
    "served_check",
    "settle_answered_checks",
]

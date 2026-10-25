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
* **A stricter measurement duty** (DL2 verify F15, orchestrator ruling R3 of
  fix round 4): when the check's item is also a due cold follow-up
  (``cold_retry``, ``certification_cold_probe``) or an active diagnostic
  presentation, it is served under that duty, whose safeguards stay as they
  are (no hints on a cold check; hints disabled in a diagnostic block). The
  view says so honestly (:data:`MEASURED_BANNER`, no help ladder header),
  chosen here, server-side: the practice item's serve reads the cold
  follow-up, the probe contract passes ``duty="diagnostic"``. An answer on
  your own completes the duty and answers the check (a pure diagnostic is on
  your own by the activity policy).
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
#: F15 (R3): the check's item is also measured under a stricter duty (a cold
#: follow-up, a diagnostic): no help is promised, because none is offered.
MEASURED_BANNER = "A check on your own: this one is measured on your own, so no help is offered."
#: The stricter duties a check's item can carry.
DUTY_COLD_FOLLOWUP = "cold_followup"
DUTY_DIAGNOSTIC = "diagnostic"
#: The follow-up lanes whose claim is an unassisted attempt
#: (``serve_eligibility.COLD_FOLLOWUP_TASK_KINDS``).
_COLD_FOLLOWUP_KINDS = ("cold_retry", "certification_cold_probe")


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


def _measured_view(check: CheckState, *, duty: str) -> dict[str, Any]:
    """F15 (R3): a cold check served under the item's stricter duty, whose
    safeguards refuse help; the view promises none and offers no ladder
    header. (A check that is not cold is practice: :func:`_view`.)"""

    return {
        "kind": "check_once",
        "commitment_id": check.commitment_id,
        "due_since": check.date.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "date_source": check.date_source,
        "cold": True,
        "duty": duty,
        "banner": MEASURED_BANNER,
        "locators_hidden": True,
        "restoration": restoration_link(check.provenance),
    }


def cold_followup_duty(repository: Any, practice_item_id: str, *, now: datetime) -> str | None:
    """``"cold_followup"`` when a due cold follow-up selects the item (the
    task submit answers and refuses help for), else None."""

    at = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    for kind in _COLD_FOLLOWUP_KINDS:
        if repository.active_followup_task_for_item(practice_item_id, kind=kind, at=at) is not None:
            return DUTY_COLD_FOLLOWUP
    return None


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


def served_check(
    vault: Any, repository: Any, practice_item_id: str, *, now: datetime, duty: str | None = None
) -> dict[str, Any] | None:
    """The practice view of ``practice_item_id`` when it is a due check now:
    cold only when the one eligibility decision says so at this serve (F3:
    an exposure after the check was planned is read here).

    ``duty``: a stricter measurement the caller is serving the item under
    (``"diagnostic"``: the probe contract); with none given, a due cold
    follow-up on the item is read here. Either gives the measured view (F15)."""

    serving = intent_serving(vault, repository, now=now)
    if serving is None:
        return None
    check = serving.check_for(practice_item_id)
    if check is None or not check.due or check.answered_by is not None or practice_item_id not in check.candidates:
        return None
    cold = check.cold(practice_item_id)
    if not cold:
        # F3: practice whatever else the item carries; the measured banner
        # would claim a check this attempt cannot answer.
        return _view(check, cold=False)
    if duty is None:
        duty = cold_followup_duty(repository, practice_item_id, now=now)
    if duty == DUTY_COLD_FOLLOWUP and _help_converts(vault):
        # Reader CA2 (mvp-0.34, §15 Q4): help is never withheld on a cold
        # follow-up either; taking it makes the attempt practice with help,
        # so the check is served with the ladder's take step like any other.
        duty = None
    if duty is not None:
        return _measured_view(check, duty=duty)
    return _view(check, cold=True)


def _help_converts(vault: Any) -> bool:
    from learnloop.serve_eligibility import help_converts_active

    return help_converts_active(vault)


def cold_followup_view(vault: Any, repository: Any, practice_item_id: str, *, now: datetime) -> dict[str, Any] | None:
    """Reader CA2 (mvp-0.34, §15 Q4, ``ask.cold_help_converts``): the practice
    view of a due cold follow-up served without a "Check once": the cold
    banner, the help ladder's header (choose, then take) and no locators
    until feedback, exactly as a check's cold view. None below the
    successor, switched off, or when no cold follow-up selects the item (the
    predecessor's "no hints on this one" then applies)."""

    if not _help_converts(vault):
        return None
    if cold_followup_duty(repository, practice_item_id, now=now) is None:
        return None
    return {
        "kind": "cold_followup",
        "cold": True,
        "banner": COLD_BANNER,
        "help_header": HELP_LADDER_HEADER,
        "locators_hidden": True,
        "restoration": None,
    }


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
    "DUTY_COLD_FOLLOWUP",
    "DUTY_DIAGNOSTIC",
    "HELP_LADDER_HEADER",
    "MEASURED_BANNER",
    "PLAN_LINE",
    "PRACTICE_BANNER",
    "answered_check",
    "cold_followup_duty",
    "cold_followup_view",
    "restoration_link",
    "served_check",
    "settle_answered_checks",
]

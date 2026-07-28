"""Explicit coldness administration receipts for the repair lane (migration 149).

"Cold" used to be an inference: the §6.2 preconditions (chronology, surface
group difference, unprimed + ``hints_used == 0``, the +1-day ``not_before``)
enforced coldness but never RECORDED it, so a cold verification's claim to be
cold rested on the absence of counter-evidence nobody had scanned for. This
module turns coldness into positive recorded evidence:

* eight dimensions, each ``pass | fail | unknown`` with evidence —
  ``retrieval_delay``, ``exposure_isolation``, ``surface_novelty``,
  ``selection_basis``, ``answer_leakage``, ``window_integrity``,
  ``verification_blinding``, ``unassisted``;
* scoped absence claims — every exposure-scan dimension names the ledgers it
  scanned, the interval boundaries, and the channels KNOWN to be unobserved.
  A scan proves "no exposure recorded in these ledgers", never "unseen
  universally", and a channel without telemetry (passages prepared vs actually
  rendered) yields ``unknown``, never a silent pass;
* derived qualifications as distinct claims — ``qualifies_as_cold_retrieval``
  (delay + unassisted + no hard exposure),
  ``qualifies_as_repair_effect_verification`` (additionally no retrieval-type
  co-intervention and window integrity) and
  ``qualifies_as_held_out_validation`` (additionally surface novelty). An
  attempt can be genuinely cold retrieval yet fail repair attribution because
  an intervening retrieval on overlapping facets is a co-intervention.

Two stages per follow-up task: an ``administration`` snapshot when the cold
item's detail is served while its task is active (window state, surface
eligibility, selection basis, render-time exposure scan — idempotent per
task), and a ``final`` receipt when the terminal disposition lands. Refusal
dispositions (§4.3) get a final receipt with partial evidence too. Failure to
CONSTRUCT a receipt records one with ``unknown`` dimensions rather than
silently falling back to the pre-receipt behavior.

Semantics are prospective-only: verifications recorded before this module keep
their meaning, and consumers distinguish eras by receipt presence and
``receipt_version``. The existing enforcement (the §6.2 guards) stays; this is
the recorded line-item layer above it, plus exactly two NEW hard-fail causes
(applied by ``causal_orchestrator.record_cold_verification_from_task``): the
cold item's own answer revealed post-primed, and a hard same-surface exposure
post-primed. Everything else records without blocking, so the lane is never
starved by its own receipts.

Replay-safe: every quantity derives from stored events plus the injected
clock; writes are INSERT OR IGNORE over content ids with a unique
(task, stage) slot.
"""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Mapping

from learnloop.clock import Clock, SystemClock, parse_utc
from learnloop.db.repositories import Repository
from learnloop.vault.models import LoadedVault

logger = logging.getLogger(__name__)

COLDNESS_RECEIPT_VERSION = "coldness_receipt_v1"
TELEMETRY_COVERAGE_VERSION = "coldness_telemetry_v1"

#: The only lane with a producer today. The schema is lane-agnostic on purpose
#: (certification §5.7 and teach-back are expected adopters).
LANE_REPAIR_COLD_RETRY = "repair_cold_retry"

#: Mirrors the lane's own scheduling rule (`remediation.record_remediation_attempt`
#: schedules `not_before` at +1 day): a retrieval closer than this to its anchor
#: is warm recall of the session, not delayed retrieval.
MIN_COLD_DELAY = timedelta(days=1)

#: Window rule: eligibility keys on the administration OPEN time. Opening just
#: before expiry and submitting shortly after stays valid within this grace.
WINDOW_SUBMIT_GRACE = timedelta(hours=24)
WINDOW_RULE = "eligibility_keyed_on_open_time_v1"

DIMENSION_NAMES = (
    "retrieval_delay",
    "exposure_isolation",
    "surface_novelty",
    "selection_basis",
    "answer_leakage",
    "window_integrity",
    "verification_blinding",
    "unassisted",
)

#: Scoped enumeration of the exposure ledgers that ACTUALLY have writers today.
#: This is the "in these ledgers" of every absence claim below.
SCANNED_LEDGERS = (
    {
        "ledger": "practice_attempts",
        "observes": (
            "every recorded attempt: item, learning object, facets, hints, "
            "primed flag; post-attempt feedback reveals the item's expected "
            "answer, so an attempt row doubles as an answer-reveal record for "
            "its own item"
        ),
    },
    {
        "ledger": "question_events",
        "observes": (
            "tutor Q&A in library/practice/feedback contexts, with "
            "hint_equivalent and leak_suspected flags and the practice item "
            "the question was asked on"
        ),
    },
    {
        "ledger": "source_exposure_events",
        "observes": (
            "span views (Open-in-source), including remediation-context "
            "passage opens, keyed by entity and source span"
        ),
    },
    {
        "ledger": "remediation_episodes.passages_shown_json",
        "observes": (
            "passages PREPARED at prescription time only; rendering is not "
            "confirmed by any event, so in-interval preparations classify as "
            "indeterminate, never as clear or contaminated"
        ),
    },
)

#: Channels a scan cannot see. Their existence is why every clear result is
#: `clear_in_observed_channels`, not "unseen universally".
KNOWN_UNOBSERVED_CHANNELS = (
    # passages_shown_json records prescription, not rendering.
    "remediation_passages_render",
    # Re-opening the feedback screen on an old attempt re-reveals its answer
    # without a new event; only the original attempt row is recorded.
    "feedback_screen_reopens",
    # Read-only practice-item detail opens (inspector, retire dialogs) serve
    # expected_answer without an event — except the cold item itself, whose
    # serve now writes the administration snapshot.
    "practice_item_detail_reads",
    # Reader browsing outside span-view telemetry (free navigation, search).
    "reader_free_navigation",
    # Anything outside the app entirely.
    "off_app_exposure",
)

ABSENCE_CLEAR = "clear_in_observed_channels"
ABSENCE_CONTAMINATED = "contaminated"
ABSENCE_INDETERMINATE = "indeterminate"

SELECTION_POLICY = "remediation_checkpoint_targeted_rank_v1"
SELECTION_POLICY_NOTE = (
    "remediation._rank_items ordering: not attempted within the recency "
    "window, then covers a targeted repair checkpoint (diagnosis-informed), "
    "then facet overlap with the confused pair, then least recently "
    "practiced, then item id; the cold item is the best-ranked item in a "
    "surface group different from the primed item's"
)


def _content_id(prefix: str, value: Any) -> str:
    encoded = json.dumps(
        value, sort_keys=True, separators=(",", ":"), default=str
    ).encode("utf-8")
    return f"{prefix}_{hashlib.sha256(encoded).hexdigest()[:26]}"


def _iso(value: datetime) -> str:
    return value.isoformat().replace("+00:00", "Z")


def _dimension(status: str, evidence: Mapping[str, Any]) -> dict[str, Any]:
    return {"status": status, "evidence": dict(evidence)}


def _canonical_facets(vault: LoadedVault, facets: Any) -> set[str]:
    return {vault.canonical_facet_id(str(facet)) for facet in facets or [] if facet}


def _telemetry_coverage(interval: Mapping[str, Any] | None) -> dict[str, Any]:
    return {
        "telemetry_coverage_version": TELEMETRY_COVERAGE_VERSION,
        "scanned_ledgers": [dict(entry) for entry in SCANNED_LEDGERS],
        "known_unobserved_channels": list(KNOWN_UNOBSERVED_CHANNELS),
        "interval": dict(interval) if interval else None,
    }


def _indeterminate_dimensions(reason: str) -> dict[str, Any]:
    return {
        name: _dimension("unknown", {"reason": reason})
        for name in DIMENSION_NAMES
    }


# --- exposure scan -----------------------------------------------------------


def _scan_exposures(
    vault: LoadedVault,
    repository: Repository,
    *,
    interval_start: str,
    interval_end: str,
    source_attempt: Mapping[str, Any] | None,
    cold_item_id: str | None,
    case_ref: str | None,
    exclude_attempt_ids: set[str],
) -> dict[str, Any]:
    """Typed intervening-exposure scan over the enumerated ledgers.

    Event types: ``hard`` (the cold item's own answer reveal or a same
    surface-group administration), ``retrieval`` (an attempt on overlapping
    facets/LO — a co-intervention for attribution), ``soft`` (related passage
    read, non-revealing tutor question), ``irrelevant`` (counted, not listed).
    """

    from learnloop.services.canonical_projection import surface_group_id

    cold_item = vault.practice_items.get(cold_item_id) if cold_item_id else None
    source_item = (
        vault.practice_items.get(str(source_attempt.get("practice_item_id") or ""))
        if source_attempt is not None
        else None
    )
    cold_group = surface_group_id(cold_item) if cold_item is not None else None
    relevant_los = {
        value
        for value in (
            getattr(cold_item, "learning_object_id", None),
            getattr(source_item, "learning_object_id", None),
            (source_attempt or {}).get("learning_object_id"),
        )
        if value
    }
    relevant_facets: set[str] = set()
    for item in (cold_item, source_item):
        if item is not None:
            relevant_facets |= _canonical_facets(vault, item.evidence_facets)

    events: list[dict[str, Any]] = []
    irrelevant = 0

    for attempt in repository.practice_attempts_between(
        after=interval_start, before=interval_end
    ):
        attempt_id = str(attempt["id"])
        if attempt_id in exclude_attempt_ids:
            continue
        item_id = str(attempt.get("practice_item_id") or "")
        item = vault.practice_items.get(item_id)
        group = surface_group_id(item) if item is not None else None
        facets = _canonical_facets(vault, attempt.get("evidence_facets"))
        if cold_item_id and item_id == cold_item_id:
            kind, why = "hard", "cold_item_answer_reveal"
        elif cold_group is not None and group == cold_group:
            kind, why = "hard", "same_surface_group_administration"
        elif (facets & relevant_facets) or (
            str(attempt.get("learning_object_id") or "") in relevant_los
        ):
            kind, why = "retrieval", "attempt_on_overlapping_facets"
        else:
            irrelevant += 1
            continue
        events.append(
            {
                "type": kind,
                "ledger": "practice_attempts",
                "event_id": attempt_id,
                "at": str(attempt.get("created_at") or ""),
                "practice_item_id": item_id,
                "why": why,
            }
        )

    for event in repository.question_events(since=interval_start):
        at = str(event.get("created_at") or "")
        if not at or at >= interval_end or at <= interval_start:
            continue
        item_id = str(event.get("practice_item_id") or "")
        if cold_item_id and item_id == cold_item_id:
            kind = "hard" if event.get("leak_suspected") else "soft"
            why = (
                "tutor_answer_leak_suspected_on_cold_item"
                if kind == "hard"
                else "tutor_question_on_cold_item"
            )
        else:
            item = vault.practice_items.get(item_id) if item_id else None
            if item is not None and item.learning_object_id in relevant_los:
                kind, why = "soft", "tutor_question_on_related_item"
            else:
                irrelevant += 1
                continue
        events.append(
            {
                "type": kind,
                "ledger": "question_events",
                "event_id": str(event.get("id") or ""),
                "at": at,
                "practice_item_id": item_id or None,
                "why": why,
            }
        )

    for event in repository.source_exposure_events():
        at = str(event.get("created_at") or "")
        if not at or at >= interval_end or at <= interval_start:
            continue
        entity_id = str(event.get("entity_id") or "")
        related = entity_id and (
            entity_id == (case_ref or "") or entity_id in relevant_los
        )
        if related or str(event.get("context") or "") == "remediation":
            events.append(
                {
                    "type": "soft",
                    "ledger": "source_exposure_events",
                    "event_id": str(event.get("id") or ""),
                    "at": at,
                    "why": "related_source_passage_viewed",
                }
            )
        else:
            irrelevant += 1

    prepared_unconfirmed: list[dict[str, Any]] = []
    for episode in repository.remediation_episodes_created_between(
        after=interval_start, before=interval_end
    ):
        passages = episode.get("passages_shown") or []
        if not passages:
            continue
        prepared_unconfirmed.append(
            {
                "ledger": "remediation_episodes.passages_shown_json",
                "remediation_episode_id": str(episode["id"]),
                "at": str(episode.get("created_at") or ""),
                "passage_count": len(passages),
                "why": "passages_prepared_in_interval_render_unconfirmed",
            }
        )

    hard = [event for event in events if event["type"] == "hard"]
    if hard:
        absence_status = ABSENCE_CONTAMINATED
    elif prepared_unconfirmed:
        absence_status = ABSENCE_INDETERMINATE
    else:
        absence_status = ABSENCE_CLEAR
    return {
        "events": events,
        "prepared_unconfirmed": prepared_unconfirmed,
        "irrelevant_count": irrelevant,
        "absence_status": absence_status,
        "interval": {"from": interval_start, "to": interval_end},
    }


# --- dimension builders ------------------------------------------------------


def _retrieval_delay(
    *,
    source_at: str | None,
    measured_to: str | None,
    scan: Mapping[str, Any],
) -> dict[str, Any]:
    source_dt = parse_utc(source_at) if source_at else None
    to_dt = parse_utc(measured_to) if measured_to else None
    if source_dt is None or to_dt is None:
        return _dimension(
            "unknown",
            {
                "reason": "missing_timestamps",
                "primed_attempt_at": source_at,
                "measured_to": measured_to,
            },
        )
    refresh = [
        event
        for event in scan.get("events") or []
        if event.get("type") in ("hard", "soft") and event.get("at")
    ]
    anchor_at, anchor_event = source_at, None
    for event in refresh:
        if str(event["at"]) > str(anchor_at):
            anchor_at, anchor_event = str(event["at"]), event
    anchor_dt = parse_utc(anchor_at) or source_dt
    delay_from_primed = (to_dt - source_dt).total_seconds()
    delay_from_anchor = (to_dt - anchor_dt).total_seconds()
    status = "pass" if delay_from_anchor >= MIN_COLD_DELAY.total_seconds() else "fail"
    return _dimension(
        status,
        {
            "primed_attempt_at": source_at,
            "measured_to": measured_to,
            "delay_seconds_from_primed": delay_from_primed,
            "anchor_at": anchor_at,
            "anchor_reset_by": (
                {
                    "ledger": anchor_event["ledger"],
                    "event_id": anchor_event["event_id"],
                    "type": anchor_event["type"],
                }
                if anchor_event is not None
                else None
            ),
            "delay_seconds_from_anchor": delay_from_anchor,
            "minimum_delay_seconds": MIN_COLD_DELAY.total_seconds(),
        },
    )


def _exposure_isolation(scan: Mapping[str, Any]) -> dict[str, Any]:
    status_map = {
        ABSENCE_CONTAMINATED: "fail",
        ABSENCE_INDETERMINATE: "unknown",
        ABSENCE_CLEAR: "pass",
    }
    return _dimension(
        status_map[str(scan["absence_status"])],
        {
            "absence_status": scan["absence_status"],
            "events": scan.get("events") or [],
            "prepared_unconfirmed": scan.get("prepared_unconfirmed") or [],
            "irrelevant_count": scan.get("irrelevant_count", 0),
            "interval": scan.get("interval"),
        },
    )


def _surface_novelty(
    vault: LoadedVault,
    repository: Repository,
    *,
    cold_item_id: str | None,
    source_attempt: Mapping[str, Any] | None,
    interval_end: str,
    exclude_attempt_ids: set[str],
) -> dict[str, Any]:
    """Positive administered-exclusion evidence, time-bounded.

    Same query `probe_episodes.administered_surface_exclusions` runs
    (attempted item ids -> attempted surface groups), reimplemented through the
    repository because the receipt needs it BOUNDED at the administration
    boundary — the global read would count the cold attempt itself as a prior
    administration of its own surface. Remint lineage needs no special case:
    `surface_group_id` resolves a probe_remint to its ancestor's group through
    `evidence_fingerprint.source_family`.
    """

    from learnloop.services.canonical_projection import surface_group_id

    cold_item = vault.practice_items.get(cold_item_id) if cold_item_id else None
    if cold_item is None:
        return _dimension(
            "unknown",
            {"reason": "cold_item_unresolvable", "cold_item_id": cold_item_id},
        )
    cold_group = surface_group_id(cold_item)
    source_item = (
        vault.practice_items.get(str(source_attempt.get("practice_item_id") or ""))
        if source_attempt is not None
        else None
    )
    source_group = surface_group_id(source_item) if source_item is not None else None
    prior_ids: list[str] = []
    item_seen = False
    group_seen = False
    for attempt in repository.practice_attempts_between(
        after=None, before=interval_end
    ):
        attempt_id = str(attempt["id"])
        if attempt_id in exclude_attempt_ids:
            continue
        item_id = str(attempt.get("practice_item_id") or "")
        if item_id == cold_item_id:
            item_seen = True
            prior_ids.append(attempt_id)
            continue
        item = vault.practice_items.get(item_id)
        if item is not None and surface_group_id(item) == cold_group:
            group_seen = True
            prior_ids.append(attempt_id)
    distinct = source_group is None or cold_group != source_group
    administered = item_seen or group_seen
    status = "fail" if (administered or not distinct) else "pass"
    return _dimension(
        status,
        {
            "cold_item_id": cold_item_id,
            "surface_group_id": cold_group,
            "source_surface_group_id": source_group,
            "distinct_from_source_group": distinct,
            "cold_item_previously_attempted": item_seen,
            "surface_group_previously_administered": group_seen,
            "prior_administration_attempt_ids": prior_ids,
            "checked_until": interval_end,
            "group_basis": (
                "canonical_projection.surface_group_id: shared_stimulus_id, "
                "source_family, solution_recipe_family, surface_family, item "
                "id — a probe_remint pins its ancestor's group via "
                "fingerprint.source_family"
            ),
        },
    )


def _selection_basis(task: Mapping[str, Any]) -> dict[str, Any]:
    context = task.get("context")
    context = context if isinstance(context, Mapping) else {}
    carried = context.get("kind") == "causal_cold_verification" and bool(
        context.get("source_attempt_id")
    )
    evidence = {
        "selection_policy": SELECTION_POLICY,
        "policy_note": SELECTION_POLICY_NOTE,
        "case_kind": str(task.get("case_kind") or "") or None,
        "case_ref": str(task.get("case_ref") or "") or None,
        "repair_class_id": context.get("repair_class_id"),
        "hypothesis_ids": [str(v) for v in context.get("hypothesis_ids") or []],
        "avoided_affordances": [
            str(v) for v in context.get("avoided_affordances") or []
        ],
        "selected_item_id": str(task.get("selected_item_id") or "") or None,
        "learner_visible_personalization": False,
        # Hidden personalization narrows WHAT the measurement estimates (the
        # diagnosed subpopulation/checkpoints), it does not contaminate it —
        # recorded as an estimand-narrowing declaration by design.
        "estimand_narrowing": (
            "cold surface selected conditional on the diagnosed repair "
            "class/checkpoint targets without learner-visible disclosure; "
            "narrows the verified claim to the diagnosed mechanism"
        ),
    }
    return _dimension("pass" if carried else "unknown", evidence)


def _answer_leakage(scan: Mapping[str, Any]) -> dict[str, Any]:
    reveals = [
        event
        for event in scan.get("events") or []
        if event.get("why")
        in ("cold_item_answer_reveal", "tutor_answer_leak_suspected_on_cold_item")
    ]
    status = "fail" if reveals else "pass"
    return _dimension(
        status,
        {
            "absence_status": ABSENCE_CONTAMINATED if reveals else ABSENCE_CLEAR,
            "reveal_events": reveals,
            "interval": scan.get("interval"),
            "note": (
                "covers the cold item's own expected answer / repaired trace "
                "only; general-material exposure is exposure_isolation's claim"
            ),
        },
    )


def _window_integrity(
    *,
    task: Mapping[str, Any],
    open_at: str | None,
    submit_at: str | None,
) -> dict[str, Any]:
    not_before = str(task.get("not_before") or "") or None
    expires_at = str(task.get("expires_at") or "") or None
    evidence = {
        "rule": WINDOW_RULE,
        "submit_grace_seconds": WINDOW_SUBMIT_GRACE.total_seconds(),
        "not_before": not_before,
        "expires_at": expires_at,
        "opened_at": open_at,
        "submitted_at": submit_at,
    }
    open_dt = parse_utc(open_at) if open_at else None
    if open_dt is None:
        evidence["reason"] = "no_administration_open_recorded"
        return _dimension("unknown", evidence)
    not_before_dt = parse_utc(not_before) if not_before else None
    expires_dt = parse_utc(expires_at) if expires_at else None
    submit_dt = parse_utc(submit_at) if submit_at else None
    ok = True
    if not_before_dt is not None and open_dt < not_before_dt:
        ok = False
        evidence["violation"] = "opened_before_not_before"
    if expires_dt is not None and open_dt > expires_dt:
        ok = False
        evidence["violation"] = "opened_after_expiry"
    if submit_dt is not None:
        if submit_dt < open_dt:
            ok = False
            evidence["violation"] = "submitted_before_open"
        elif expires_dt is not None and submit_dt > expires_dt + WINDOW_SUBMIT_GRACE:
            ok = False
            evidence["violation"] = "submitted_beyond_grace"
    return _dimension("pass" if ok else "fail", evidence)


def _verification_blinding(
    repository: Repository,
    *,
    source_attempt_id: str | None,
    cold_attempt: Mapping[str, Any] | None,
) -> dict[str, Any]:
    diagnosis_receipt_present = False
    if source_attempt_id:
        try:
            debug = repository.attempt_debug_payload(source_attempt_id) or {}
            attribution = debug.get("causal_attribution")
            diagnosis_receipt_present = isinstance(attribution, dict) and isinstance(
                attribution.get("diagnosis_receipt"), dict
            )
        except Exception:  # pragma: no cover - evidence-only lookup
            diagnosis_receipt_present = False
    evidence = {
        "cold_grading": (
            {
                "attempt_type": str(cold_attempt.get("attempt_type") or "") or None,
                "manual_review": bool(cold_attempt.get("manual_review")),
                "grader_confidence_recorded": cold_attempt.get("grader_confidence")
                is not None,
            }
            if cold_attempt is not None
            else None
        ),
        "repair_generation": {
            "diagnosis_receipt_present": diagnosis_receipt_present,
            "model_profile_agent_run_ids": "unrecorded",
        },
        "cold_grading_saw_repair_context": "unrecorded",
        "note": (
            "current telemetry does not capture per-call model/profile/"
            "agent_run identities for repair generation vs cold grading, so "
            "separation cannot be positively established; recorded as "
            "unknown, never assumed. A shared calibration model would be "
            "recorded here, not failed."
        ),
    }
    return _dimension("unknown", evidence)


def _unassisted(cold_attempt: Mapping[str, Any] | None) -> dict[str, Any]:
    if cold_attempt is None:
        return _dimension("unknown", {"reason": "no_attempt_yet"})
    hints = int(cold_attempt.get("hints_used") or 0)
    primed = bool(cold_attempt.get("primed"))
    return _dimension(
        "pass" if (hints == 0 and not primed) else "fail",
        {
            "hints_used": hints,
            "primed": primed,
            "attempt_type": str(cold_attempt.get("attempt_type") or "") or None,
        },
    )


# --- assembly ----------------------------------------------------------------


@dataclass
class ColdnessEvaluation:
    """One computed set of dimensions, ready to store or to gate on."""

    dimensions: dict[str, Any]
    derived: dict[str, Any]
    telemetry_coverage: dict[str, Any]
    #: Non-None exactly when a HARD exposure was found — the only two causes
    #: allowed to block a verification (answer reveal / same-surface exposure
    #: post-primed).
    hard_contamination: dict[str, Any] | None
    construction_error: str | None = None


def _derive(
    dimensions: Mapping[str, Any],
    scan: Mapping[str, Any] | None,
    *,
    stage: str,
) -> dict[str, Any]:
    if stage == "administration" or scan is None:
        return {
            "qualifies_as_cold_retrieval": None,
            "qualifies_as_repair_effect_verification": None,
            "qualifies_as_held_out_validation": None,
            "note": "qualifications are final-stage claims",
        }
    events = scan.get("events") or []
    hard_ids = [e["event_id"] for e in events if e.get("type") == "hard"]
    retrieval_ids = [e["event_id"] for e in events if e.get("type") == "retrieval"]

    def _status(name: str) -> str:
        return str((dimensions.get(name) or {}).get("status") or "unknown")

    cold = (
        _status("retrieval_delay") == "pass"
        and _status("unassisted") == "pass"
        and not hard_ids
    )
    repair = (
        cold and not retrieval_ids and _status("window_integrity") == "pass"
    )
    held_out = repair and _status("surface_novelty") == "pass"
    return {
        "qualifies_as_cold_retrieval": cold,
        "qualifies_as_repair_effect_verification": repair,
        "qualifies_as_held_out_validation": held_out,
        "hard_exposure_event_ids": hard_ids,
        "retrieval_cointervention_event_ids": retrieval_ids,
        "basis": (
            "cold_retrieval = delay + unassisted + no hard exposure; "
            "repair_effect adds no retrieval co-intervention + window "
            "integrity; held_out adds surface novelty"
        ),
    }


def _hard_contamination(scan: Mapping[str, Any]) -> dict[str, Any] | None:
    hard = [e for e in (scan.get("events") or []) if e.get("type") == "hard"]
    if not hard:
        return None
    reveal = [e for e in hard if e.get("why") != "same_surface_group_administration"]
    return {
        "reason": (
            "cold_item_answer_revealed_post_primed"
            if reveal
            else "hard_same_surface_exposure_post_primed"
        ),
        "event_ids": [e["event_id"] for e in hard],
        "events": hard,
    }


def _evaluate(
    vault: LoadedVault,
    repository: Repository,
    *,
    task: Mapping[str, Any],
    stage: str,
    cold_attempt_id: str | None,
    open_at: str | None,
    now_iso: str,
) -> ColdnessEvaluation:
    context = task.get("context")
    context = context if isinstance(context, Mapping) else {}
    source_attempt_id = (
        str(context.get("source_attempt_id") or "")
        or str(task.get("source_attempt_id") or "")
    ) or None
    source_attempt = (
        repository.fetch_practice_attempt(source_attempt_id)
        if source_attempt_id
        else None
    )
    cold_attempt = (
        repository.fetch_practice_attempt(cold_attempt_id)
        if cold_attempt_id
        else None
    )
    if cold_attempt is not None:
        cold_item_id = str(cold_attempt.get("practice_item_id") or "") or None
        submit_at = str(cold_attempt.get("created_at") or "") or None
    else:
        cold_item_id = str(task.get("selected_item_id") or "") or None
        submit_at = None
    interval_start = (
        str(source_attempt.get("created_at") or "")
        if source_attempt is not None
        else None
    )
    interval_end = submit_at or open_at or now_iso
    exclude = {
        value
        for value in (source_attempt_id, cold_attempt_id)
        if value
    }

    scan: dict[str, Any] | None = None
    if interval_start and interval_end and interval_start < interval_end:
        scan = _scan_exposures(
            vault,
            repository,
            interval_start=interval_start,
            interval_end=interval_end,
            source_attempt=source_attempt,
            cold_item_id=cold_item_id,
            case_ref=str(task.get("case_ref") or "") or None,
            exclude_attempt_ids=exclude,
        )

    dimensions: dict[str, Any] = {}
    if scan is not None:
        dimensions["retrieval_delay"] = _retrieval_delay(
            source_at=interval_start,
            measured_to=submit_at or open_at,
            scan=scan,
        )
        dimensions["exposure_isolation"] = _exposure_isolation(scan)
        dimensions["answer_leakage"] = _answer_leakage(scan)
    else:
        reason = (
            "no_source_attempt"
            if not interval_start
            else "non_monotone_interval"
        )
        for name in ("retrieval_delay", "exposure_isolation", "answer_leakage"):
            dimensions[name] = _dimension("unknown", {"reason": reason})
    dimensions["surface_novelty"] = _surface_novelty(
        vault,
        repository,
        cold_item_id=cold_item_id,
        source_attempt=source_attempt,
        interval_end=interval_end,
        exclude_attempt_ids=exclude,
    )
    dimensions["selection_basis"] = _selection_basis(task)
    dimensions["window_integrity"] = _window_integrity(
        task=task, open_at=open_at, submit_at=submit_at
    )
    dimensions["verification_blinding"] = _verification_blinding(
        repository,
        source_attempt_id=source_attempt_id,
        cold_attempt=cold_attempt,
    )
    dimensions["unassisted"] = _unassisted(cold_attempt)

    interval = scan.get("interval") if scan is not None else None
    return ColdnessEvaluation(
        dimensions=dimensions,
        derived=_derive(dimensions, scan, stage=stage),
        telemetry_coverage=_telemetry_coverage(interval),
        hard_contamination=_hard_contamination(scan) if scan is not None else None,
    )


def evaluate_final_coldness(
    vault: LoadedVault,
    repository: Repository,
    *,
    task: Mapping[str, Any],
    cold_attempt_id: str | None,
    clock: Clock | None = None,
) -> ColdnessEvaluation:
    """Compute the final-stage dimensions. Never raises.

    A construction failure yields an all-``unknown`` evaluation carrying the
    error — the receipt still gets recorded (with indeterminate dimensions)
    rather than silently reverting to the inference era.
    """

    now_iso = _iso((clock or SystemClock()).now())
    task_id = str(task.get("id") or "") or None
    snapshot = (
        repository.coldness_receipt_for_task_stage(task_id, "administration")
        if task_id
        else None
    )
    open_at = str(snapshot.get("created_at") or "") or None if snapshot else None
    try:
        evaluation = _evaluate(
            vault,
            repository,
            task=task,
            stage="final",
            cold_attempt_id=cold_attempt_id,
            open_at=open_at,
            now_iso=now_iso,
        )
    except Exception as exc:
        logger.warning(
            "coldness evaluation failed for task %s", task_id, exc_info=True
        )
        return ColdnessEvaluation(
            dimensions=_indeterminate_dimensions("receipt_construction_failed"),
            derived=_derive({}, None, stage="administration"),
            telemetry_coverage=_telemetry_coverage(None),
            hard_contamination=None,
            construction_error=str(exc),
        )
    if snapshot is not None:
        evaluation.derived["administration_receipt_id"] = str(snapshot["id"])
    return evaluation


# --- stage writes ------------------------------------------------------------


def record_administration_snapshot(
    vault: LoadedVault,
    repository: Repository,
    *,
    task: Mapping[str, Any],
    clock: Clock | None = None,
) -> dict[str, Any] | None:
    """Stage 1: the serving-time snapshot, idempotent per follow-up task.

    Called when the practice-item detail is served for an item carrying an
    active ``cold_retry`` task. The snapshot's ``created_at`` is the
    administration OPEN time that ``window_integrity`` keys on.
    """

    task_id = str(task.get("id") or "") or None
    if task_id is None or str(task.get("kind") or "") != "cold_retry":
        return None
    existing = repository.coldness_receipt_for_task_stage(task_id, "administration")
    if existing is not None:
        return existing
    now_iso = _iso((clock or SystemClock()).now())
    try:
        evaluation = _evaluate(
            vault,
            repository,
            task=task,
            stage="administration",
            cold_attempt_id=None,
            open_at=now_iso,
            now_iso=now_iso,
        )
    except Exception as exc:
        logger.warning(
            "coldness snapshot construction failed for task %s",
            task_id,
            exc_info=True,
        )
        evaluation = ColdnessEvaluation(
            dimensions=_indeterminate_dimensions("receipt_construction_failed"),
            derived=_derive({}, None, stage="administration"),
            telemetry_coverage=_telemetry_coverage(None),
            hard_contamination=None,
            construction_error=str(exc),
        )
    derived = dict(evaluation.derived)
    if evaluation.construction_error:
        derived["construction_error"] = evaluation.construction_error
    return repository.insert_coldness_receipt(
        receipt_id=_content_id(
            "cra", {"task": task_id, "stage": "administration"}
        ),
        lane=LANE_REPAIR_COLD_RETRY,
        stage="administration",
        followup_task_id=task_id,
        remediation_episode_id=(
            str(task.get("remediation_episode_id") or "") or None
        ),
        source_attempt_id=(
            str(task.get("source_attempt_id") or "") or None
        ),
        cold_attempt_id=None,
        cold_verification_id=None,
        dimensions=evaluation.dimensions,
        derived=derived,
        telemetry_coverage=evaluation.telemetry_coverage,
        receipt_version=COLDNESS_RECEIPT_VERSION,
        clock=clock,
    )


def record_final_receipt(
    repository: Repository,
    *,
    task: Mapping[str, Any],
    evaluation: ColdnessEvaluation,
    outcome: str,
    cold_attempt_id: str | None = None,
    cold_verification_id: str | None = None,
    clock: Clock | None = None,
) -> dict[str, Any] | None:
    """Stage 2: the terminal receipt — measured verifications AND refusals.

    Idempotent per (task, stage) through the migration-149 unique slot;
    replaying the same terminal event returns the row that holds it.
    """

    task_id = str(task.get("id") or "") or None
    derived = dict(evaluation.derived)
    derived["outcome"] = outcome
    if evaluation.construction_error:
        derived["construction_error"] = evaluation.construction_error
    if evaluation.hard_contamination is not None:
        derived["hard_contamination"] = evaluation.hard_contamination
    context = task.get("context")
    context = context if isinstance(context, Mapping) else {}
    return repository.insert_coldness_receipt(
        receipt_id=_content_id(
            "crf",
            {
                "task": task_id,
                "stage": "final",
                "cold_attempt_id": cold_attempt_id,
                "cold_verification_id": cold_verification_id,
                "outcome": outcome,
            },
        ),
        lane=LANE_REPAIR_COLD_RETRY,
        stage="final",
        followup_task_id=task_id,
        remediation_episode_id=(
            str(task.get("remediation_episode_id") or "") or None
        ),
        source_attempt_id=(
            str(context.get("source_attempt_id") or "")
            or str(task.get("source_attempt_id") or "")
        )
        or None,
        cold_attempt_id=cold_attempt_id,
        cold_verification_id=cold_verification_id,
        dimensions=evaluation.dimensions,
        derived=derived,
        telemetry_coverage=evaluation.telemetry_coverage,
        receipt_version=COLDNESS_RECEIPT_VERSION,
        clock=clock,
    )


__all__ = [
    "COLDNESS_RECEIPT_VERSION",
    "TELEMETRY_COVERAGE_VERSION",
    "LANE_REPAIR_COLD_RETRY",
    "KNOWN_UNOBSERVED_CHANNELS",
    "MIN_COLD_DELAY",
    "SCANNED_LEDGERS",
    "WINDOW_SUBMIT_GRACE",
    "ColdnessEvaluation",
    "evaluate_final_coldness",
    "record_administration_snapshot",
    "record_final_receipt",
]

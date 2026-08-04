"""Explicit coldness administration receipts for delayed retrieval lanes.

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

v2 (telemetry adoption) closes the two channels that had writers nobody was
reading and splits the blinding claim:

* ``remediation_passages_render`` -> the prescribe RPC now records passage
  DELIVERY (``source_exposure_events.context = 'remediation_delivery'``,
  migration 150). A prescription DELIVERED inside the interval is a typed
  exposure (``soft``, or ``hard`` when the delivered span is one the cold item
  was authored from); a prescription with no delivery event anywhere stays
  ``indeterminate``, because prepared-and-never-delivered and
  prescribed-through-an-uninstrumented-path are the same silence. On-screen
  dwell remains unobserved and remains declared.
* ``feedback_screen_reopens`` -> ``attempt_feedback_metadata`` has counted
  every ``get_feedback`` since migration 010; the scan now consumes it. A
  reopen re-reveals that attempt's graded answer, feedback and repair
  suggestions, so a reopen on the cold surface is ``hard`` and one on the
  source/related attempts is ``soft``. Only the LAST reopen is timestamped, so
  intermediate reopens stay declared unobserved.
* ``verification_blinding`` -> the two halves are recorded separately.
  ``run_separation`` compares the source attempt's grading ``agent_run`` (the
  run that also authored the repair suggestions) with the cold attempt's;
  ``context_blinding`` reads the cold grading call's Phase-C receipt
  (migration 144) for the prior-attempt traces it was given. The dimension
  passes only when BOTH halves pass, so a self-graded pair — where no model
  identity exists at all — stays ``unknown`` exactly as before.

v3 (migration 151) makes the denominator and freshness claim auditable too:

* a durable measurement opportunity exists before surface selection and is
  settled as scheduled or with a typed refusal;
* retrieval practice is a memory-refreshing exposure and therefore resets the
  delay anchor as well as remaining a repair-attribution co-intervention;
* remediation deliveries, passage preparations, and source views affect a
  receipt only after resolving to the target case, LO, facets, or source spans;
* every large-vault ledger scan is time-bounded and indexed, while surface
  novelty queries only the candidate's finite canonical surface group;
* certification cold probes share the opportunity, administration, and final
  receipt schema instead of publishing only their outcome label.

Semantics are prospective-only: verifications recorded before this module keep
their meaning, and consumers distinguish eras by receipt presence and
``receipt_version``. Earlier receipts are not reinterpreted under v3 coverage
— the ``telemetry_coverage_version`` on the row says which channels were
observable when it was written. The existing enforcement (the §6.2 guards)
stays; this is the recorded line-item layer above it, plus exactly two NEW
hard-fail causes
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

COLDNESS_RECEIPT_VERSION = "coldness_receipt_v3"
TELEMETRY_COVERAGE_VERSION = "coldness_telemetry_v3"

#: The repair and certification producers share one schema; lane remains open
#: TEXT so later delayed-retrieval instruments can adopt it without a rebuild.
LANE_REPAIR_COLD_RETRY = "repair_cold_retry"
LANE_CERTIFICATION_COLD_PROBE = "certification_cold_probe"

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
            "passage opens, keyed by entity and source span; plus (v2, "
            "migration 150) prescribed remediation passages DELIVERED for "
            "render, under context 'remediation_delivery' and keyed by "
            "remediation episode"
        ),
    },
    {
        "ledger": "remediation_episodes.passages_shown_json",
        "observes": (
            "passages PREPARED at prescription time. v2 pairs each prepared "
            "episode with its delivery events: delivered in-interval is a "
            "typed exposure, delivered only outside is clear, and an episode "
            "with no delivery event at all stays indeterminate — prepared-but-"
            "never-shown and prescribed-through-an-uninstrumented-path are "
            "indistinguishable"
        ),
    },
    {
        "ledger": "attempt_feedback_metadata",
        "observes": (
            "feedback-screen opens per attempt (shown_count, first/last "
            "shown_at), written by every get_feedback since migration 010; a "
            "reopen re-reveals that attempt's graded answer, feedback and "
            "repair suggestions. Only the LAST reopen carries a timestamp"
        ),
    },
)

#: Channels a scan cannot see. Their existence is why every clear result is
#: `clear_in_observed_channels`, not "unseen universally".
KNOWN_UNOBSERVED_CHANNELS = (
    # v2 observes DELIVERY of prescribed passages, not what happened on screen:
    # nothing records how long the text stayed visible or whether it was read.
    "remediation_passage_on_screen_dwell",
    # A prescription with no delivery event could be one that was never shown
    # or one prescribed outside the instrumented RPC (CLI, replay).
    "remediation_prescription_without_delivery_record",
    # `record_feedback_shown` keeps a counter plus first/last timestamps, so a
    # reopen between the first and the last one has no visible time.
    "feedback_reopen_intermediate_timestamps",
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


def _case_scope(
    vault: LoadedVault,
    repository: Repository,
    *,
    case_kind: str | None,
    case_ref: str | None,
) -> tuple[set[str], set[str]]:
    """Resolve a case to the LO/facets whose study can refresh this target."""

    if not case_kind or not case_ref:
        return set(), set()
    learning_objects: set[str] = set()
    facets: set[str] = set()
    try:
        if case_kind == "misconception":
            misconception = repository.misconception(case_ref)
            if misconception is not None:
                if misconception.learning_object_id:
                    learning_objects.add(str(misconception.learning_object_id))
                facets |= _canonical_facets(
                    vault,
                    [
                        *misconception.facet_ids,
                        misconception.target_facet,
                        misconception.confused_with_facet,
                    ],
                )
        elif case_kind == "diagnosis":
            hypothesis = repository.causal_hypothesis(case_ref)
            if hypothesis is not None:
                learning_object_id = str(
                    hypothesis.get("learning_object_id") or ""
                )
                if learning_object_id:
                    learning_objects.add(learning_object_id)
                target = hypothesis.get("target_ref")
                if isinstance(target, Mapping):
                    facets |= _canonical_facets(
                        vault,
                        [
                            target.get("facet_id"),
                            target.get("target_facet"),
                            target.get("confused_with_facet"),
                        ],
                    )
        elif case_kind == "certification":
            # Certification events normally carry their indexed LO directly.
            # A case ref is a certificate hash, not an LO, so it contributes no
            # extra scope here.
            pass
    except Exception:  # pragma: no cover - relevance lookup is evidence-only
        logger.warning(
            "failed to resolve receipt relevance for %s/%s",
            case_kind,
            case_ref,
            exc_info=True,
        )
    return learning_objects, facets


def _episode_is_relevant(
    vault: LoadedVault,
    repository: Repository,
    episode: Mapping[str, Any] | None,
    *,
    relevant_los: set[str],
    relevant_facets: set[str],
    relevant_case_refs: set[str],
) -> bool:
    if episode is None:
        return False
    case_ref = str(episode.get("case_ref") or "")
    if case_ref and case_ref in relevant_case_refs:
        return True
    episode_los, episode_facets = _case_scope(
        vault,
        repository,
        case_kind=str(episode.get("case_kind") or "") or None,
        case_ref=case_ref or None,
    )
    if episode_los and relevant_los:
        return bool(episode_los & relevant_los)
    return bool(episode_facets & relevant_facets)


def _scan_exposures(
    vault: LoadedVault,
    repository: Repository,
    *,
    interval_start: str,
    interval_end: str,
    source_attempt: Mapping[str, Any] | None,
    cold_item_id: str | None,
    cold_attempt_id: str | None = None,
    case_ref: str | None,
    exclude_attempt_ids: set[str],
    additional_relevant_los: set[str] | None = None,
    additional_relevant_facets: set[str] | None = None,
    additional_relevant_case_refs: set[str] | None = None,
) -> dict[str, Any]:
    """Typed intervening-exposure scan over the enumerated ledgers.

    Event types: ``hard`` (the cold item's own answer reveal or a same
    surface-group administration), ``retrieval`` (an attempt on overlapping
    facets/LO — a co-intervention for attribution), ``soft`` (related passage
    read or delivered, non-revealing tutor question, feedback reopen on a
    related attempt), ``irrelevant`` (counted, not listed).
    """

    from learnloop.services.canonical_projection import surface_group_id
    from learnloop.services.remediation import (
        REMEDIATION_DELIVERY_CONTEXT,
        REMEDIATION_DELIVERY_ENTITY_TYPE,
    )

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
    relevant_los |= {
        str(value) for value in (additional_relevant_los or set()) if value
    }
    relevant_facets: set[str] = set()
    for item in (cold_item, source_item):
        if item is not None:
            relevant_facets |= _canonical_facets(vault, item.evidence_facets)
    relevant_facets |= _canonical_facets(
        vault, additional_relevant_facets or set()
    )
    relevant_case_refs = {
        str(value)
        for value in ({case_ref} | (additional_relevant_case_refs or set()))
        if value
    }
    source_item_spans = _item_source_spans(source_item)
    cold_item_spans = _item_source_spans(cold_item)
    related_item_spans = source_item_spans | cold_item_spans

    events: list[dict[str, Any]] = []
    irrelevant = 0
    irrelevant_by_ledger: dict[str, int] = {}

    def mark_irrelevant(ledger: str) -> None:
        nonlocal irrelevant
        irrelevant += 1
        irrelevant_by_ledger[ledger] = irrelevant_by_ledger.get(ledger, 0) + 1

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
        elif (
            str(attempt.get("learning_object_id") or "") in relevant_los
            if attempt.get("learning_object_id") and relevant_los
            else bool(facets & relevant_facets)
        ):
            kind, why = "retrieval", "attempt_on_overlapping_facets"
        else:
            mark_irrelevant("practice_attempts")
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

    for event in repository.question_events(
        since=interval_start, until=interval_end
    ):
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
            if item is not None and (
                item.learning_object_id in relevant_los
                if item.learning_object_id and relevant_los
                else bool(
                    _canonical_facets(vault, item.evidence_facets)
                    & relevant_facets
                )
            ):
                kind, why = "soft", "tutor_question_on_related_item"
            else:
                mark_irrelevant("question_events")
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

    delivered_in_interval: set[str] = set()
    episode_cache: dict[str, Mapping[str, Any] | None] = {}
    for event in repository.source_exposure_events(
        after=interval_start, before=interval_end
    ):
        at = str(event.get("created_at") or "")
        context = str(event.get("context") or "")
        entity_id = str(event.get("entity_id") or "")
        entity_type = str(event.get("entity_type") or "")
        span_key = (
            str(event.get("extraction_id") or ""),
            str(event.get("span_id") or ""),
        )
        if context == REMEDIATION_DELIVERY_CONTEXT:
            episode_id = (
                entity_id
                if entity_type == REMEDIATION_DELIVERY_ENTITY_TYPE
                else ""
            )
            episode = None
            if episode_id:
                if episode_id not in episode_cache:
                    episode_cache[episode_id] = repository.remediation_episode(
                        episode_id
                    )
                episode = episode_cache[episode_id]
            relevant_delivery = (
                span_key in related_item_spans
                or _episode_is_relevant(
                    vault,
                    repository,
                    episode,
                    relevant_los=relevant_los,
                    relevant_facets=relevant_facets,
                    relevant_case_refs=relevant_case_refs,
                )
            )
            if not relevant_delivery:
                mark_irrelevant("source_exposure_events")
                continue
            if episode_id:
                delivered_in_interval.add(episode_id)
            if cold_item_spans and span_key in cold_item_spans:
                kind, why = "hard", "remediation_passage_revealed_cold_item_source_span"
            else:
                kind, why = "soft", "remediation_passage_delivered_for_render"
            events.append(
                {
                    "type": kind,
                    "ledger": "source_exposure_events",
                    "event_id": str(event.get("id") or ""),
                    "at": at,
                    "remediation_episode_id": episode_id or None,
                    "why": why,
                    "cold_item_source_spans_resolvable": bool(cold_item_spans),
                }
            )
            continue
        related = bool(
            entity_id
            and (entity_id in relevant_case_refs or entity_id in relevant_los)
        )
        if not related and entity_type == REMEDIATION_DELIVERY_ENTITY_TYPE:
            if entity_id not in episode_cache:
                episode_cache[entity_id] = repository.remediation_episode(entity_id)
            related = _episode_is_relevant(
                vault,
                repository,
                episode_cache[entity_id],
                relevant_los=relevant_los,
                relevant_facets=relevant_facets,
                relevant_case_refs=relevant_case_refs,
            )
        elif not related and entity_type in {"misconception", "diagnosis"}:
            entity_los, entity_facets = _case_scope(
                vault,
                repository,
                case_kind=entity_type,
                case_ref=entity_id or None,
            )
            related = (
                bool(entity_los & relevant_los)
                if entity_los and relevant_los
                else bool(entity_facets & relevant_facets)
            )
        related = related or span_key in related_item_spans
        if related:
            kind = "hard" if span_key in cold_item_spans else "soft"
            events.append(
                {
                    "type": kind,
                    "ledger": "source_exposure_events",
                    "event_id": str(event.get("id") or ""),
                    "at": at,
                    "why": (
                        "cold_item_source_span_viewed"
                        if kind == "hard"
                        else "related_source_passage_viewed"
                    ),
                }
            )
        else:
            mark_irrelevant("source_exposure_events")

    for row in repository.attempts_with_feedback_shown_between(
        after=interval_start, before=interval_end
    ):
        attempt_id = str(row.get("attempt_id") or "")
        if not attempt_id or attempt_id == (cold_attempt_id or ""):
            continue
        item_id = str(row.get("practice_item_id") or "")
        item = vault.practice_items.get(item_id)
        group = surface_group_id(item) if item is not None else None
        facets = _canonical_facets(vault, getattr(item, "evidence_facets", None))
        if cold_item_id and item_id == cold_item_id:
            kind, why = "hard", "cold_item_feedback_reopened"
        elif cold_group is not None and group == cold_group:
            kind, why = "hard", "same_surface_group_feedback_reopened"
        elif attempt_id == str((source_attempt or {}).get("id") or ""):
            # The learner re-read their own graded repair attempt: its feedback
            # carries the grader's repair suggestions for the diagnosed case.
            kind, why = "soft", "source_attempt_feedback_reopened"
        elif (
            str(row.get("learning_object_id") or "") in relevant_los
            if row.get("learning_object_id") and relevant_los
            else bool(facets & relevant_facets)
        ):
            kind, why = "soft", "related_attempt_feedback_reopened"
        else:
            mark_irrelevant("attempt_feedback_metadata")
            continue
        events.append(
            {
                "type": kind,
                "ledger": "attempt_feedback_metadata",
                "event_id": f"feedback_shown:{attempt_id}",
                "at": str(row.get("last_shown_at") or ""),
                "practice_item_id": item_id or None,
                "attempt_id": attempt_id,
                "shown_count": int(row.get("shown_count") or 0),
                "why": why,
            }
        )

    prepared_unconfirmed: list[dict[str, Any]] = []
    delivered_outside_interval: list[dict[str, Any]] = []
    for episode in repository.remediation_episodes_created_between(
        after=interval_start, before=interval_end
    ):
        passages = episode.get("passages_shown") or []
        episode_id = str(episode["id"])
        if not _episode_is_relevant(
            vault,
            repository,
            episode,
            relevant_los=relevant_los,
            relevant_facets=relevant_facets,
            relevant_case_refs=relevant_case_refs,
        ):
            if passages:
                mark_irrelevant("remediation_episodes.passages_shown_json")
            continue
        if not passages or episode_id in delivered_in_interval:
            # Delivered in-interval: already recorded above as typed events.
            continue
        deliveries = repository.source_exposure_events(
            entity_type=REMEDIATION_DELIVERY_ENTITY_TYPE, entity_id=episode_id
        )
        entry = {
            "ledger": "remediation_episodes.passages_shown_json",
            "remediation_episode_id": episode_id,
            "at": str(episode.get("created_at") or ""),
            "passage_count": len(passages),
        }
        if deliveries:
            # Its passages have a delivery record, and none of it lands inside
            # the interval: the silence here is observed, not missing.
            entry["why"] = "passages_delivered_outside_interval"
            entry["delivery_event_ids"] = [
                str(delivery.get("id") or "") for delivery in deliveries
            ]
            delivered_outside_interval.append(entry)
        else:
            entry["why"] = "passages_prepared_in_interval_no_delivery_record"
            prepared_unconfirmed.append(entry)

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
        "delivered_outside_interval": delivered_outside_interval,
        "irrelevant_count": irrelevant,
        "irrelevant_by_ledger": irrelevant_by_ledger,
        "absence_status": absence_status,
        "interval": {"from": interval_start, "to": interval_end},
    }


def _item_source_spans(item: Any) -> set[tuple[str, str]]:
    """The (extraction, span) pairs an item was authored from, if any.

    The strongest reveal test the stored provenance supports: a remediation
    passage delivered on one of these spans is the source text the item's
    expected answer was written from. Empty for hand-authored items, and the
    emptiness travels on the event (`cold_item_source_spans_resolvable`) so a
    reader can see the test could not bind rather than assuming it passed.
    """

    spans: set[tuple[str, str]] = set()
    provenance = getattr(item, "provenance", None)
    for ref in getattr(provenance, "source_refs", None) or []:
        extraction_id = str(getattr(ref, "extraction_id", "") or "")
        if not extraction_id:
            continue
        for span_id in getattr(ref, "span_ids", None) or []:
            if span_id:
                spans.add((extraction_id, str(span_id)))
    return spans


# --- dimension builders ------------------------------------------------------


def _retrieval_delay(
    *,
    source_at: str | None,
    measured_to: str | None,
    scan: Mapping[str, Any],
    minimum_delay: timedelta = MIN_COLD_DELAY,
    anchor_kind: str = "primed_attempt",
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
        if event.get("type") in ("hard", "soft", "retrieval") and event.get("at")
    ]
    anchor_at, anchor_event = source_at, None
    for event in refresh:
        if str(event["at"]) > str(anchor_at):
            anchor_at, anchor_event = str(event["at"]), event
    anchor_dt = parse_utc(anchor_at) or source_dt
    delay_from_primed = (to_dt - source_dt).total_seconds()
    delay_from_anchor = (to_dt - anchor_dt).total_seconds()
    status = "pass" if delay_from_anchor >= minimum_delay.total_seconds() else "fail"
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
            "minimum_delay_seconds": minimum_delay.total_seconds(),
            "anchor_kind": anchor_kind,
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
            "delivered_outside_interval": scan.get("delivered_outside_interval") or [],
            "irrelevant_count": scan.get("irrelevant_count", 0),
            "irrelevant_by_ledger": scan.get("irrelevant_by_ledger") or {},
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
    group_item_ids = [
        item_id
        for item_id, item in vault.practice_items.items()
        if surface_group_id(item) == cold_group
    ]
    prior_ids: list[str] = []
    item_seen = False
    group_seen = False
    for attempt in repository.practice_attempts_for_items_before(
        group_item_ids, before=interval_end
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
    if str(task.get("kind") or "") == "certification_cold_probe":
        selected = str(task.get("selected_item_id") or "") or None
        excluded = [
            str(value)
            for value in context.get("excluded_surface_groups") or []
        ]
        basis = str(context.get("held_out_basis") or "") or None
        carried = (
            context.get("kind") == "certification_cold_probe"
            and bool(context.get("certificate_id"))
            and bool(selected)
        )
        return _dimension(
            "pass" if carried and basis == "distinct_surface_group" else "unknown",
            {
                "selection_policy": context.get("policy_version"),
                "certificate_id": context.get("certificate_id"),
                "selected_item_id": selected,
                "probe_surface_group": context.get("probe_surface_group"),
                "excluded_certifying_surface_groups": excluded,
                "held_out_basis": basis,
                "personalization_basis": (
                    "selected for certificate-cell and integration coverage "
                    "after excluding certifying, unservable, and already "
                    "administered diagnostic surfaces"
                ),
                "estimand_narrowing": (
                    "validates the certified LO/recipe represented by this "
                    "certificate, not undifferentiated recall"
                ),
            },
        )
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


#: Findings that reveal the COLD item's own answer (answer_leakage's claim),
#: as opposed to a same-surface administration (exposure_isolation's).
COLD_ITEM_REVEAL_REASONS = (
    "cold_item_answer_reveal",
    "tutor_answer_leak_suspected_on_cold_item",
    # v2: the feedback screen for a prior attempt on the cold item was reopened
    # inside the interval — the same reveal as the attempt row, at a later time.
    "cold_item_feedback_reopened",
    # v2: a delivered remediation passage sat on a span the cold item was
    # authored from.
    "remediation_passage_revealed_cold_item_source_span",
    "cold_item_source_span_viewed",
)

#: Hard findings that are same-surface EXPOSURE rather than an answer reveal.
SAME_SURFACE_REASONS = (
    "same_surface_group_administration",
    "same_surface_group_feedback_reopened",
)


def _answer_leakage(scan: Mapping[str, Any]) -> dict[str, Any]:
    reveals = [
        event
        for event in scan.get("events") or []
        if event.get("why") in COLD_ITEM_REVEAL_REASONS
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


def _grading_identity(
    repository: Repository, attempt_id: str | None
) -> dict[str, Any] | None:
    """Who graded one attempt: channel, tiers, and the agent run behind it.

    Repair generation has no run of its own — the repair suggestions the lane
    acts on are produced by the grading call on the SOURCE attempt — so this
    same read serves as the repair-generation identity for that attempt.
    """

    if not attempt_id:
        return None
    try:
        rows = repository.fetch_grading_evidence(attempt_id)
    except Exception:  # pragma: no cover - evidence-only lookup
        rows = []
    try:
        metadata = repository.fetch_attempt_feedback_metadata(attempt_id) or {}
    except Exception:  # pragma: no cover - evidence-only lookup
        metadata = {}
    tiers = sorted({int(row.grader_tier) for row in rows})
    run_ids = sorted({str(row.agent_run_id) for row in rows if row.agent_run_id})
    metadata_run_id = str(metadata.get("agent_run_id") or "") or None
    if metadata_run_id and metadata_run_id not in run_ids:
        run_ids.append(metadata_run_id)
    run = None
    if run_ids:
        try:
            run = repository.agent_run(run_ids[0])
        except Exception:  # pragma: no cover - evidence-only lookup
            run = None
    return {
        "attempt_id": attempt_id,
        "grading_source": str(metadata.get("grading_source") or "") or None,
        "grader_tiers": tiers,
        # Tier >= 2 is the model-graded band; tier 1 is the learner grading
        # their own work, where "blinding" has no subject.
        "model_graded": any(tier >= 2 for tier in tiers),
        "agent_run_ids": run_ids,
        "agent_run": (
            {
                "id": str(run.get("id") or ""),
                "purpose": run.get("purpose"),
                "provider": run.get("provider"),
                "provider_type": run.get("provider_type"),
                "model": run.get("model"),
                "prompt_template": run.get("prompt_template"),
                "prompt_version": run.get("prompt_version"),
                "started_at": run.get("started_at"),
            }
            if isinstance(run, dict)
            else None
        ),
    }


def _run_separation(
    source: Mapping[str, Any] | None, cold: Mapping[str, Any] | None
) -> dict[str, Any]:
    """Half one: did a DIFFERENT run grade the cold attempt?"""

    source_runs = set((source or {}).get("agent_run_ids") or [])
    cold_runs = set((cold or {}).get("agent_run_ids") or [])
    shared = sorted(source_runs & cold_runs)
    if shared:
        status, reason = "fail", "shared_agent_run"
    elif source_runs and cold_runs:
        status, reason = "pass", "disjoint_agent_runs"
    else:
        status = "unknown"
        reason = (
            "no_model_grading_run_recorded"
            if not cold_runs
            else "no_source_grading_run_recorded"
        )
    return {
        "status": status,
        "reason": reason,
        "source_agent_run_ids": sorted(source_runs),
        "cold_agent_run_ids": sorted(cold_runs),
        "shared_agent_run_ids": shared,
        "note": (
            "a shared model between two distinct runs is recorded (see each "
            "identity's model/provider), never failed — only a shared RUN is a "
            "failure of separation"
        ),
    }


def _context_blinding(
    repository: Repository,
    *,
    source_attempt_id: str | None,
    cold_attempt_id: str | None,
) -> dict[str, Any]:
    """Half two: was the cold grading call given repair/diagnosis context?

    Answered from the Phase-C receipt (migration 144), which records what the
    grading call was actually handed: the grader provider/model, the prompt
    version, and the prior-attempt ids whose raw traces were attached as C4
    history. ``augment_grading_context`` attaches those traces WITHOUT their
    diagnoses by contract, so a receipt naming no prior attempt from this repair
    chain is positive evidence of blinding. No receipt (self-graded, manual, or
    a pre-Stage-7 attempt) is ``unknown``, never a pass.
    """

    evidence: dict[str, Any] = {
        "ledger": "diagnostic_augmentation_receipts",
        "basis": (
            "the grading context is a closed structure; the only field that can "
            "carry another attempt's material is the C4 diagnostic history, "
            "whose attempt ids the receipt records. Prior DIAGNOSES are omitted "
            "from that history by the augmentation contract — the grader is "
            "given evidence of recurrence, not the system's earlier answer"
        ),
    }
    if not cold_attempt_id:
        evidence["reason"] = "no_cold_attempt"
        evidence["status"] = "unknown"
        return evidence
    try:
        receipt = repository.diagnostic_augmentation_receipt_for_attempt(
            cold_attempt_id
        )
    except Exception:  # pragma: no cover - evidence-only lookup
        receipt = None
    if receipt is None:
        evidence["status"] = "unknown"
        evidence["reason"] = "no_grading_context_receipt"
        evidence["note"] = (
            "the cold attempt has no recorded model-grading context (self- or "
            "deterministically graded, or graded before the Phase-C receipt "
            "existed), so what its grader saw is not introspectable"
        )
        return evidence
    history_ids = [str(value) for value in receipt.get("c4_history_attempt_ids") or []]
    saw_source = bool(source_attempt_id) and source_attempt_id in history_ids
    evidence.update(
        {
            "status": "fail" if saw_source else "pass",
            "grading_prompt_version": receipt.get("grading_prompt_version"),
            "grader_provider": receipt.get("grader_provider"),
            "grader_model": receipt.get("grader_model"),
            "diagnostic_history_attempt_ids": history_ids,
            "source_attempt_in_grading_history": saw_source,
            "prior_diagnoses_in_context": False,
        }
    )
    if saw_source:
        evidence["reason"] = "source_attempt_trace_in_cold_grading_history"
    return evidence


def _verification_blinding(
    repository: Repository,
    *,
    source_attempt_id: str | None,
    cold_attempt_id: str | None,
    cold_attempt: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Two independent halves, recorded separately and reported separately.

    v1 recorded a single ``unknown`` with a note. The halves fail and pass for
    different reasons, and a consumer that cannot see WHICH half is established
    has no way to tell "nothing is known" from "the runs are provably distinct
    and only the prompt contents are unverified" — so both statuses travel, and
    the dimension passes only when both do.
    """

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
    source_identity = _grading_identity(repository, source_attempt_id)
    cold_identity = _grading_identity(repository, cold_attempt_id)
    separation = _run_separation(source_identity, cold_identity)
    context = _context_blinding(
        repository,
        source_attempt_id=source_attempt_id,
        cold_attempt_id=cold_attempt_id,
    )
    statuses = {str(separation["status"]), str(context["status"])}
    if "fail" in statuses:
        status = "fail"
    elif statuses == {"pass"}:
        status = "pass"
    else:
        status = "unknown"
    evidence = {
        "run_separation": separation,
        "context_blinding": context,
        "repair_generation": {
            # Repair suggestions are authored by the grading call on the source
            # attempt, so that call's identity IS the repair-generation identity.
            "identity_is": "source_attempt_grading_run",
            "diagnosis_receipt_present": diagnosis_receipt_present,
            "grading_identity": source_identity,
        },
        "cold_grading": {
            "grading_identity": cold_identity,
            "attempt_type": (
                str(cold_attempt.get("attempt_type") or "") or None
                if cold_attempt is not None
                else None
            ),
            "manual_review": (
                bool(cold_attempt.get("manual_review"))
                if cold_attempt is not None
                else None
            ),
            "grader_confidence_recorded": (
                cold_attempt.get("grader_confidence") is not None
                if cold_attempt is not None
                else None
            ),
        },
        "rule": (
            "pass requires BOTH halves to pass: a cold grading run distinct "
            "from the run that produced the repair, and a recorded cold "
            "grading context free of this repair chain's material. Either half "
            "unestablished leaves the dimension unknown"
        ),
    }
    return _dimension(status, evidence)


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
    lane: str = LANE_REPAIR_COLD_RETRY,
) -> dict[str, Any]:
    if stage == "administration" or scan is None:
        return {
            "qualifies_as_cold_retrieval": None,
            "qualifies_as_repair_effect_verification": None,
            "qualifies_as_held_out_validation": None,
            "qualifies_as_certificate_validation": None,
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
    certificate = (
        cold
        and not retrieval_ids
        and _status("window_integrity") == "pass"
        and _status("surface_novelty") == "pass"
    )
    return {
        "qualifies_as_cold_retrieval": cold,
        "qualifies_as_repair_effect_verification": (
            repair if lane == LANE_REPAIR_COLD_RETRY else None
        ),
        "qualifies_as_held_out_validation": held_out,
        "qualifies_as_certificate_validation": (
            certificate if lane == LANE_CERTIFICATION_COLD_PROBE else None
        ),
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
    reveal = [e for e in hard if e.get("why") not in SAME_SURFACE_REASONS]
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
    lane = (
        LANE_CERTIFICATION_COLD_PROBE
        if str(task.get("kind") or "") == "certification_cold_probe"
        else LANE_REPAIR_COLD_RETRY
    )
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
    if lane == LANE_CERTIFICATION_COLD_PROBE:
        interval_start = (
            str(context.get("certified_at") or "")
            or str(context.get("measurement_anchor_at") or "")
        ) or None
    else:
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
            cold_attempt_id=cold_attempt_id,
            case_ref=str(task.get("case_ref") or "") or None,
            exclude_attempt_ids=exclude,
            additional_relevant_los={
                str(
                    context.get("learning_object_id")
                    or task.get("learning_object_id")
                    or ""
                )
            }
            if lane == LANE_CERTIFICATION_COLD_PROBE
            else None,
            additional_relevant_facets={
                str(cell.get("facet_id"))
                for cell in (
                    (context.get("certificate_receipt") or {}).get("cells") or []
                )
                if isinstance(cell, Mapping) and cell.get("facet_id")
            }
            if lane == LANE_CERTIFICATION_COLD_PROBE
            and isinstance(context.get("certificate_receipt"), Mapping)
            else None,
            additional_relevant_case_refs={
                str(context.get("certificate_id") or "")
            }
            if lane == LANE_CERTIFICATION_COLD_PROBE
            else None,
        )

    dimensions: dict[str, Any] = {}
    if scan is not None:
        dimensions["retrieval_delay"] = _retrieval_delay(
            source_at=interval_start,
            measured_to=submit_at or open_at,
            scan=scan,
            minimum_delay=(
                timedelta(days=float(context.get("horizon_days") or 0.0))
                if lane == LANE_CERTIFICATION_COLD_PROBE
                else MIN_COLD_DELAY
            ),
            anchor_kind=(
                "certificate"
                if lane == LANE_CERTIFICATION_COLD_PROBE
                else "primed_attempt"
            ),
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
    if lane == LANE_CERTIFICATION_COLD_PROBE:
        novelty = dimensions["surface_novelty"]
        evidence = dict(novelty.get("evidence") or {})
        excluded_groups = {
            str(value)
            for value in context.get("excluded_surface_groups") or []
        }
        probe_group = str(evidence.get("surface_group_id") or "")
        distinct_from_certificate = bool(probe_group) and (
            probe_group not in excluded_groups
        )
        evidence.update(
            {
                "excluded_certifying_surface_groups": sorted(excluded_groups),
                "distinct_from_certifying_surface_groups": distinct_from_certificate,
            }
        )
        dimensions["surface_novelty"] = _dimension(
            (
                "fail"
                if not distinct_from_certificate
                else str(novelty.get("status") or "unknown")
            ),
            evidence,
        )
    dimensions["selection_basis"] = _selection_basis(task)
    dimensions["window_integrity"] = _window_integrity(
        task=task, open_at=open_at, submit_at=submit_at
    )
    dimensions["verification_blinding"] = _verification_blinding(
        repository,
        source_attempt_id=source_attempt_id,
        cold_attempt_id=cold_attempt_id,
        cold_attempt=cold_attempt,
    )
    dimensions["unassisted"] = _unassisted(cold_attempt)

    interval = scan.get("interval") if scan is not None else None
    return ColdnessEvaluation(
        dimensions=dimensions,
        derived=_derive(dimensions, scan, stage=stage, lane=lane),
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
    active repair or certification cold task. The snapshot's ``created_at`` is the
    administration OPEN time that ``window_integrity`` keys on.
    """

    task_id = str(task.get("id") or "") or None
    lane_by_kind = {
        "cold_retry": LANE_REPAIR_COLD_RETRY,
        "certification_cold_probe": LANE_CERTIFICATION_COLD_PROBE,
    }
    lane = lane_by_kind.get(str(task.get("kind") or ""))
    if task_id is None or lane is None:
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
        lane=lane,
        stage="administration",
        measurement_opportunity_id=(
            str(task.get("measurement_opportunity_id") or "") or None
        ),
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


def record_certification_administration_snapshot(
    vault: LoadedVault,
    repository: Repository,
    *,
    task: Mapping[str, Any],
    clock: Clock | None = None,
) -> dict[str, Any] | None:
    """Named certification-lane adapter for callers that require lane clarity."""

    if str(task.get("kind") or "") != "certification_cold_probe":
        return None
    return record_administration_snapshot(
        vault, repository, task=task, clock=clock
    )


def record_final_receipt(
    repository: Repository,
    *,
    task: Mapping[str, Any],
    evaluation: ColdnessEvaluation,
    outcome: str,
    cold_attempt_id: str | None = None,
    cold_verification_id: str | None = None,
    lane: str = LANE_REPAIR_COLD_RETRY,
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
        lane=lane,
        stage="final",
        measurement_opportunity_id=(
            str(task.get("measurement_opportunity_id") or "") or None
        ),
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


def record_schedule_refusal_receipt(
    repository: Repository,
    *,
    opportunity: Mapping[str, Any],
    decision: str,
    reason: str,
    candidate_summary: Mapping[str, Any] | None = None,
    clock: Clock | None = None,
) -> dict[str, Any] | None:
    """Record a terminal receipt when no task could be scheduled.

    There is deliberately no task-shaped input: the measurement opportunity is
    the parent. Dimensions that require administration remain unknown, while
    the selection/refusal evidence is explicit and auditable.
    """

    opportunity_id = str(opportunity.get("id") or "") or None
    if opportunity_id is None:
        return None
    existing = repository.coldness_receipt_for_opportunity_stage(
        opportunity_id, "final"
    )
    if existing is not None:
        return existing
    dimensions = _indeterminate_dimensions("not_administered_schedule_refusal")
    dimensions["selection_basis"] = _dimension(
        "fail",
        {
            "decision": decision,
            "reason": reason,
            "candidate_summary": dict(candidate_summary or {}),
            "policy_version": opportunity.get("policy_version"),
            "selected_item_id": None,
        },
    )
    derived = {
        "qualifies_as_cold_retrieval": None,
        "qualifies_as_repair_effect_verification": None,
        "qualifies_as_held_out_validation": None,
        "qualifies_as_certificate_validation": None,
        "outcome": "schedule_refused",
        "schedule_decision": decision,
        "schedule_reason": reason,
        "measurement_opportunity_id": opportunity_id,
        "note": "no administration occurred; final receipt settles the opportunity",
    }
    return repository.insert_coldness_receipt(
        receipt_id=_content_id(
            "crf",
            {
                "measurement_opportunity_id": opportunity_id,
                "stage": "final",
                "decision": decision,
                "reason": reason,
            },
        ),
        lane=str(opportunity.get("lane") or ""),
        stage="final",
        measurement_opportunity_id=opportunity_id,
        followup_task_id=None,
        remediation_episode_id=(
            str(opportunity.get("remediation_episode_id") or "") or None
        ),
        source_attempt_id=(
            str(opportunity.get("source_attempt_id") or "") or None
        ),
        cold_attempt_id=None,
        cold_verification_id=None,
        dimensions=dimensions,
        derived=derived,
        telemetry_coverage=_telemetry_coverage(None),
        receipt_version=COLDNESS_RECEIPT_VERSION,
        clock=clock,
    )


__all__ = [
    "COLDNESS_RECEIPT_VERSION",
    "TELEMETRY_COVERAGE_VERSION",
    "LANE_REPAIR_COLD_RETRY",
    "LANE_CERTIFICATION_COLD_PROBE",
    "KNOWN_UNOBSERVED_CHANNELS",
    "MIN_COLD_DELAY",
    "SCANNED_LEDGERS",
    "WINDOW_SUBMIT_GRACE",
    "ColdnessEvaluation",
    "evaluate_final_coldness",
    "record_administration_snapshot",
    "record_certification_administration_snapshot",
    "record_final_receipt",
    "record_schedule_refusal_receipt",
]

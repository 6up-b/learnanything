"""Reading-signal / salience firewall (spec_p3_reader_integration §8.2, §15.4;
design §C).

Standing rule (mirrors ``familiarity.py`` rule 5): **reading signals are never
learner evidence.** Dwell, skip, highlight, revisit, "already know", and salience
projections carry authority class ``salience_only`` and NEVER enter mastery,
posterior, readiness, certification, or scheduling. There is no numeric conversion
path from a reading signal to correctness/mastery/diagnosis/certification.

**The one confirmed exception** (owner 2026-10-15, D20, amended 2026-10-17 by
D22; spec_adaptive_difficulty_v1 A12 and §5.11; the P3 reader spec's Q8 is
resolved by it): adaptive difficulty's *predicted* level may read discrete
reading opportunities as learning opportunities, under four limits:

1. **Only discrete events**: the listed kinds and sources of
   :data:`LEARNING_OPPORTUNITY_SOURCES` (a section read and a passage viewed,
   collated as ``reading``; a tutor exchange while reading; a worked example
   studied; an in-passage question answered), each the fact that it happened,
   with a dose. No magnitude ever passes: no dwell, scroll, highlight, skip,
   visibility segment, active time, answer text or salience projection. The one
   typed value admitted is the learner's self-check verdict class on an answered
   in-passage question (``self_check:matched`` / ``self_check:missed``, read from
   ``judgment_ledger``), as its own learned term (D22).
2. **Prediction and selection only**, never evidence or certification: AD's
   subject view, its draws, forecasts and readiness numbers. Nothing here passes
   the evidence chokepoint (``reject_salience`` in ``attempts.apply_attempt``):
   every record :func:`learning_opportunity_events` returns stays stamped
   ``salience_only``, so the chokepoint still refuses it.
3. **Learned weights**: each kind's dose curve is latent state with a-priori,
   versioned priors, learned per vault; nothing is hand-set.
4. **Its own kill switch and auto-flag**: ``adaptive_difficulty.
   reading_opportunities`` (and ``reading_self_check`` for the verdict term),
   with the AD report's reading and verdict auto-flags.

The carve-out is :func:`learning_opportunity_events`, beside
:func:`proposal_priority_signal`: the only path from reading records (AD1's
``ad_reading_opportunities`` receipt) to AD's state. It admits exactly the
allowlist and nothing else; AD1's sweep records only these sources and reads
the same list from here.

Enforcement has three parts (design §C):

1. **Typed authority class at the source.** Every reader/reading event payload and
   every salience-projector output stamps ``authority_class='salience_only'``.
2. **A hard reject guard at the evidence-ingestion chokepoint.** ``reject_salience``
   raises :class:`SalienceEvidenceRejected` for any input whose authority class is
   ``salience_only``. It is wired into ``attempts.apply_attempt`` -- the single
   ingest step used by live recording and deterministic replay -- so no reading
   signal can reach the belief pipeline even by mistake.
3. **A parametrized static + behavioral test** (``tests/test_salience_firewall.py``)
   over the full reader ``kind`` vocabulary asserting each is rejected by the
   evidence APIs and that the belief modules never import this module.

The allowed downstreams are proposal PRIORITY (§8.2): highlights/dwell may only
reorder proposals (``proposal_priority_signal``), and the confirmed exception
above (``learning_opportunity_events``).
"""

from __future__ import annotations

from typing import Any, Mapping

SALIENCE_ONLY = "salience_only"

# Bounded visibility-segment cap per aggregation window (§8.2): clients emit
# bounded segments, never high-frequency timer ticks. Decision parameter.
DWELL_SEGMENT_MAX = 12

# The launch reader/reading event kinds on the interaction_events envelope. Every
# one is salience-only; a newly-added kind that forgets its authority class fails
# the parametrized firewall test.
READING_EVENT_KINDS: tuple[str, ...] = (
    "reader_view_opened",
    "reader_view_closed",
    "reader_mode_changed",
    "reader_span_visible",
    "reader_scroll",
    "reader_dwell",
    "reader_selection",
    "reader_highlight",
    "reader_annotation_edited",
    "reader_action_invoked",
    "reader_capture_acknowledged",
    "reader_question_control",
    # F1: the full P3 reader/reading vocabulary written through the interaction
    # envelope. Membership here is the single source of truth for the firewall
    # auto-stamp in ``log_interaction_event`` -- every kind below is salience-only.
    "reader_question_presented",
    "reader_question_skipped",
    "reader_answer_submitted",
    "reader_answer_mode_set",
    "reader_disposition_chosen",
    "reader_source_restored",
    # Reader workbench RW1a: model-backed actions' queue and completion rows
    # (status, latency, model wait, the learner's activity while waiting) for
    # the reader report's funnel. Kinds already in the envelope's CHECK since
    # migration 091; first written by RW1a.
    "reader_job_queued",
    "reader_job_completed",
)

# Salience projections a versioned projector may emit (§8.2). All salience-only.
SALIENCE_PROJECTIONS: tuple[str, ...] = (
    "highlight_count",
    "question_count",
    "revisit_count",
    "bounded_dwell",
    "skip_skim",
    "explicit_interest",
    "proposal_priority",
    "depth_suggestion",
)


class SalienceEvidenceRejected(ValueError):
    """Raised when a salience-only signal is fed into an evidence/belief API."""


def salience_payload(payload: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Stamp ``authority_class='salience_only'`` onto a reader/reading event payload."""

    out = dict(payload or {})
    out["authority_class"] = SALIENCE_ONLY
    return out


def _extract_authority_class(obj: Any) -> str | None:
    """Best-effort recovery of an authority class from a dict, an event row, or an
    object carrying a payload/metadata/draft. Deliberately conservative: it only
    reports ``salience_only`` when it can positively see it."""

    if obj is None:
        return None
    if isinstance(obj, str):
        return obj if obj == SALIENCE_ONLY else None
    if isinstance(obj, Mapping):
        if obj.get("authority_class") == SALIENCE_ONLY:
            return SALIENCE_ONLY
        for nested_key in ("payload", "payload_json", "metadata", "draft"):
            nested = obj.get(nested_key)
            if _extract_authority_class(nested) == SALIENCE_ONLY:
                return SALIENCE_ONLY
        return None
    direct = getattr(obj, "authority_class", None)
    if direct == SALIENCE_ONLY:
        return SALIENCE_ONLY
    for nested_key in ("payload", "metadata", "draft"):
        if _extract_authority_class(getattr(obj, nested_key, None)) == SALIENCE_ONLY:
            return SALIENCE_ONLY
    return None


def is_salience_only(obj: Any) -> bool:
    return _extract_authority_class(obj) == SALIENCE_ONLY


def reject_salience(obj: Any, *, context: str = "evidence_ingestion") -> None:
    """Hard reject: raise if ``obj`` carries salience-only authority. The guard at
    the evidence-ingestion chokepoint (design §C.2). Never coerces to zero -- for a
    single event it refuses outright."""

    if is_salience_only(obj):
        raise SalienceEvidenceRejected(
            f"reading/salience signal (authority_class={SALIENCE_ONLY!r}) cannot enter "
            f"{context}; reading is never learner evidence (§8.2, invariant 1.1.6)."
        )


def proposal_priority_signal(events: list[Mapping[str, Any]]) -> dict[str, float]:
    """The ONE allowed downstream of salience (§8.2): reorder PROPOSAL priority only.
    Highlights/dwell/revisits raise a target's proposal priority; nothing here
    touches evidence, posteriors, or scheduling."""

    priority: dict[str, float] = {}
    for event in events:
        subject = event.get("subject_id")
        if subject is None:
            continue
        weight = 1.0 if event.get("kind") == "reader_highlight" else 0.25
        priority[subject] = priority.get(subject, 0.0) + weight
    return priority


SALIENCE_PROJECTOR_VERSION = "salience_projection_v1"

# Weight of one dwell/visibility segment when suggesting depth (§8.2). Bounded and
# never a numeric conversion to evidence -- only a proposal-priority / depth-suggestion
# reorder signal.
_DEPTH_SUGGEST_HIGHLIGHT_WEIGHT = 1.0
_DEPTH_SUGGEST_QUESTION_WEIGHT = 0.75
_DEPTH_SUGGEST_REVISIT_WEIGHT = 0.5


def salience_projection_v1(events: list[Mapping[str, Any]]) -> dict[str, Any]:
    """Versioned salience projector v1 (§8.2, design B step 9). Derives per-subject
    highlight/question/revisit counts, BOUNDED dwell (capped at ``DWELL_SEGMENT_MAX``
    per subject -- no high-frequency timer ticks), skip/skim, explicit interest, and a
    ``proposal_priority`` + ``depth_suggestion`` from those bounded segments.

    EVERY output is stamped ``authority_class='salience_only'`` and the projector is
    the firewall's single allowed downstream: its outputs may reorder proposals and
    SUGGEST depth only. There is no path from any of these numbers to mastery,
    posterior, readiness, certification, or scheduling (invariant 1.1.6)."""

    highlight: dict[str, int] = {}
    question: dict[str, int] = {}
    revisit: dict[str, int] = {}
    dwell: dict[str, int] = {}
    skip_skim: dict[str, int] = {}
    interest: dict[str, int] = {}

    for event in events:
        subject = event.get("subject_id")
        if subject is None:
            continue
        kind = event.get("kind")
        if kind == "reader_highlight":
            highlight[subject] = highlight.get(subject, 0) + 1
        elif kind in ("reader_action_invoked", "reader_capture_acknowledged"):
            payload = event.get("payload") or {}
            action = payload.get("action") if isinstance(payload, Mapping) else None
            if action in ("ask", "mark_confusing", "question", "confusion"):
                question[subject] = question.get(subject, 0) + 1
            elif action in ("not_worth_remembering",):
                skip_skim[subject] = skip_skim.get(subject, 0) + 1
            elif action in ("help_me_remember", "test_me_later", "connect_it", "why_matters"):
                interest[subject] = interest.get(subject, 0) + 1
        elif kind == "reader_view_opened":
            revisit[subject] = revisit.get(subject, 0) + 1
        elif kind in ("reader_dwell", "reader_span_visible"):
            # Bounded: never exceed the per-window segment cap (§8.2).
            dwell[subject] = min(DWELL_SEGMENT_MAX, dwell.get(subject, 0) + 1)
        elif kind == "reader_scroll":
            skip_skim[subject] = skip_skim.get(subject, 0) + 1
        elif kind == "reader_mode_changed":
            payload = event.get("payload") or {}
            if isinstance(payload, Mapping) and payload.get("mode") == "skim":
                skip_skim[subject] = skip_skim.get(subject, 0) + 1

    priority = proposal_priority_signal(events)
    depth_suggestion: dict[str, float] = {}
    subjects = set(highlight) | set(question) | set(revisit)
    for subject in subjects:
        score = (
            _DEPTH_SUGGEST_HIGHLIGHT_WEIGHT * highlight.get(subject, 0)
            + _DEPTH_SUGGEST_QUESTION_WEIGHT * question.get(subject, 0)
            + _DEPTH_SUGGEST_REVISIT_WEIGHT * min(DWELL_SEGMENT_MAX, revisit.get(subject, 0))
        )
        if score > 0:
            depth_suggestion[subject] = score

    return salience_payload({
        "projector_version": SALIENCE_PROJECTOR_VERSION,
        "highlight_count": highlight,
        "question_count": question,
        "revisit_count": revisit,
        "bounded_dwell": dwell,
        "skip_skim": skip_skim,
        "explicit_interest": interest,
        # F2: the "I already know this" cold-check claim (spec §8.2 last paragraph)
        # is DEFERRED -- there is no already_know event kind or projector branch yet,
        # so the field was dead (always {}). Dropped until the cold-check proposal
        # path is built. See spec_p3_reader_integration.md change log 2026-07-20.
        "proposal_priority": priority,
        "depth_suggestion": depth_suggestion,
    })


# -- the confirmed exception: learning opportunities (spec_adaptive_difficulty_v1 A12, §5.11) ----

#: A reader tutor question's answer modes, each a tutor exchange's subkind;
#: ``unknown`` where none was stored (before migration 213, or outside the Reader).
TUTOR_ANSWER_MODES: tuple[str, ...] = ("answer_directly", "help_me_reason", "ask_me_first")
UNKNOWN_ANSWER_MODE = "unknown"
#: The in-passage question styles that are learning opportunities (``reconstruct``
#: questions are escalated to practice items, which AD reads as attempts).
IN_PASSAGE_STYLES: tuple[str, ...] = ("recall", "next_step", "why_step", "assumptions")
#: D22's verdict classes: the one typed value the carve-out admits.
SELF_CHECK_SUBKINDS: tuple[str, ...] = ("self_check:matched", "self_check:missed")

#: The carve-out's allowlist, ``(kind, subkind, source table)``: the only sources
#: whose records may reach AD's state (§5.11's table). One list: AD1's sweep
#: records only these.
LEARNING_OPPORTUNITY_SOURCES: tuple[tuple[str, str, str], ...] = (
    ("reading", "section_read", "reader_section_progress"),
    ("reading", "passage_viewed", "source_exposure_events"),
    *(("reader_tutor_exchange", mode, "question_events") for mode in TUTOR_ANSWER_MODES),
    ("reader_tutor_exchange", UNKNOWN_ANSWER_MODE, "question_events"),
    ("worked_example", "shown", "source_exposure_events"),
    ("worked_example", "in_completed_section", "reader_section_progress"),
    *(("in_passage_question", style, "reader_authored_questions") for style in IN_PASSAGE_STYLES),
    ("in_passage_question", "owner_placed", "interaction_events"),
    *(("in_passage_question", subkind, "judgment_ledger") for subkind in SELF_CHECK_SUBKINDS),
)
LEARNING_OPPORTUNITY_KINDS: tuple[str, ...] = ("reading", "reader_tutor_exchange", "worked_example",
                                               "in_passage_question")
#: The only fields a learning-opportunity record carries: ids, times, the LO,
#: the facets and their doses. No magnitude field exists.
LEARNING_OPPORTUNITY_FIELDS: tuple[str, ...] = (
    "opportunity_id", "kind", "subkind", "source_table", "source_id", "source_written_at",
    "learning_object_id", "facet_doses", "dose_offer_id", "authority_class",
)
_ALLOWED = frozenset(LEARNING_OPPORTUNITY_SOURCES)


def _doses(value: Any) -> dict[str, float]:
    import json

    if isinstance(value, str):
        try:
            value = json.loads(value)
        except ValueError:
            return {}
    if not isinstance(value, Mapping):
        return {}
    doses: dict[str, float] = {}
    for facet, dose in value.items():
        try:
            number = float(dose)
        except (TypeError, ValueError):
            continue
        if 0.0 < number <= 1.0:
            doses[str(facet)] = number
    return doses


def learning_opportunity_events(rows: Any) -> list[dict[str, Any]]:
    """The confirmed exception's only path (A12, §5.11): learning opportunities, never evidence.

    ``rows`` are ``ad_reading_opportunities`` rows (mappings). Exactly the
    sources of :data:`LEARNING_OPPORTUNITY_SOURCES` pass; any other reading
    kind, salience projection or source table returns nothing. Each record
    carries only :data:`LEARNING_OPPORTUNITY_FIELDS` (no dwell, active or idle
    seconds, scroll, highlight or revisit count, outcome class or answer text;
    the only typed value is the verdict class in the subkind), and stays
    stamped ``salience_only``, so :func:`reject_salience` and
    ``attempts.apply_attempt`` still refuse it."""

    out: list[dict[str, Any]] = []
    for row in rows or ():
        if not isinstance(row, Mapping):
            continue
        key = (row.get("kind"), row.get("subkind"), row.get("source_table"))
        if key not in _ALLOWED:
            continue
        if row.get("authority_class", SALIENCE_ONLY) != SALIENCE_ONLY:
            continue
        doses = _doses(row.get("facet_doses", row.get("facet_doses_json")))
        if not doses or not row.get("learning_object_id") or not row.get("source_written_at"):
            continue
        out.append({
            "opportunity_id": str(row.get("id") or row.get("opportunity_id") or ""),
            "kind": str(key[0]),
            "subkind": str(key[1]),
            "source_table": str(key[2]),
            "source_id": str(row.get("source_id") or ""),
            "source_written_at": str(row["source_written_at"]),
            "learning_object_id": str(row["learning_object_id"]),
            "facet_doses": doses,
            "dose_offer_id": row.get("dose_offer_id"),
            "authority_class": SALIENCE_ONLY,
        })
    return out

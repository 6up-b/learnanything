"""Reading-signal / salience firewall (spec_p3_reader_integration §8.2, §15.4;
design §C).

Standing rule (mirrors ``familiarity.py`` rule 5): **reading signals are never
learner evidence.** Dwell, skip, highlight, revisit, "already know", and salience
projections carry authority class ``salience_only`` and NEVER enter mastery,
posterior, readiness, certification, or scheduling. There is no numeric conversion
path from a reading signal to correctness/mastery/diagnosis/certification.

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

The ONE allowed downstream is proposal PRIORITY (§8.2): highlights/dwell may only
reorder proposals. ``proposal_priority_signal`` is that single accepting path.
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

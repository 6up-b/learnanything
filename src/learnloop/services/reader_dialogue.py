"""P2 step B.11 -- minimal bidirectional reader dialogue (U-033, spec §7.6).

Reading the chapter is part of the golden path, not a prelude to it. This slice
runs on block-level ``span_view`` + the existing tutor Q&A persistence -- it does
NOT require the P3 annotation layer, and the golden path must complete with it
DISABLED (``tutor_qa.reader_enabled=False`` default, spec §12.3.2).

Two directions (§7.6):

* **Learner -> AI (Ask).** :func:`ask` answers a span-grounded question in the new
  ``reader`` tutor context (added to ``tutor_qa``). Per-ask answer mode
  (``answer_directly`` / ``help_me_reason`` / ``ask_me_first``, default direct).
  A learner question is NEVER ability evidence (P0 invariant 10) -- the reader
  context attaches no facets. On answer commit the revealed cues warm related
  surfaces via ``familiarity.propagate_tutor_exposure``; a cue that reveals a
  reserved surface invalidates that reserve exactly as any other exposure.
* **AI -> learner (owner-placed).** :func:`administer_reading_question` renders an
  owner-placed question at a section boundary as an ordinary
  **instructional-purpose** administration with ``source_visible=true`` +
  ``reading_phase`` (migration 076 columns) -- categorically ineligible for
  certification (the ``InstructionalAdapter`` mints no unassisted certification).
  Always skippable; a skip is an interaction-policy signal, never low ability.

Every reader signal lands as a NEW KIND on the P0 ``interaction_events`` envelope
(migration 086) -- there is no reader_exchanges table: the exact per-exchange
record (question, manifest, answer + validated citations, provider/model
provenance, chosen mode) rides the ``reader_answer_submitted`` payload.

**Evidence semantics (invariant 10).** A formative reading answer mints AT MOST a
replay-derived routing prior (:func:`routing_prior_projection_v1`) -- a projection,
no stored table -- that may only reorder tier-two triage candidates inside the
U-027 decision-aid channel (registered ``heuristic``) and is superseded
structurally by the first cold observation on the same target. It NEVER touches a
posterior, FSRS state, or certification.
"""

from __future__ import annotations

import re
from typing import Any, Mapping, Sequence

from learnloop.clock import Clock, parse_utc, utc_now_iso
from learnloop.db.repositories import Repository
from learnloop.services import administration_adapters
from learnloop.services import commitments
from learnloop.services import familiarity
from learnloop.services import tutor_qa
from learnloop.services.activities import (
    append_exposure,
    log_interaction_event,
    open_administration,
    reserve_surface,
    resolve_legacy_item,
)
from learnloop.services.salience_firewall import salience_payload
from learnloop.services.span_view import SpanViewError, build_span_view
from learnloop.vault.models import LoadedVault

# P3 slice 2 reading modes (§5.1). Modes gate owner-placed questions + influence
# proposal priority only; they NEVER alter evidence eligibility (salience-only).
READER_MODES = ("skim", "anchor", "incremental")

# P3 slice 2 per-question controls (§5.1) beyond the P2 skip. All interaction-policy
# signals, never ability evidence. ``i_dont_understand`` routes to source
# restoration/instruction, never to a lapse.
READER_QUESTION_CONTROLS = (
    "skip", "too_easy", "too_intrusive", "ask_me_differently",
    "dont_bring_this_back", "i_dont_understand",
)

# --- registered decision knobs (parameter_registry: reader_dialogue:*) ---------
# The routing prior ships DARK with the reader (reader_enabled=False default), so
# both are dormant (bind-log, no coverage certificate) -- see parameter_registry.
ROUTING_PRIOR_HALFLIFE_DAYS = 7.0
ROUTING_PRIOR_MAX_WEIGHT = 0.25
# Owner-tuning guideline, never auto-inserted (no ask_now planner / density policy
# in this cut, U-017@v3): ~1 owner-placed reading question per major section.
READER_QUESTION_DENSITY_TARGET = 1
# Verbatim-overlap threshold (L3): the minimum share of a reserved surface's statement
# word-bigrams an answer must reproduce for server-side reveal detection to treat the
# answer as quoting that reserved surface (and burn its reserve). Cheap, no LLM. Ships
# dormant with the dark reader; a heuristic decision knob (parameter_registry).
READER_REVEAL_OVERLAP_THRESHOLD = 0.5

READER_ANSWER_MODES = tutor_qa.READER_ANSWER_MODES
READER_ANSWER_MODE_DEFAULT = tutor_qa.READER_ANSWER_MODE_DEFAULT

# The four reading dispositions (§7.6 umbrella U-033). Each maps to exactly one
# mechanism; walking past the picker is comprehension_only, never an obligation.
READER_DISPOSITIONS = (
    "comprehension_only",
    "check_once_later",
    "keep_developing",
    "reference_only",
)

# Reader event kinds on the P0 interaction_events envelope (§7.6, migration 086).
READER_EVENT_KINDS = (
    "reader_question_presented",
    "reader_question_skipped",
    "reader_answer_submitted",
    "learner_question_asked",
    "reader_answer_mode_set",
    "reader_disposition_chosen",
    "reader_source_restored",
)

# The valid reading phases for an owner-placed question (migration 076 doc).
READING_PHASES = ("before_section", "during_section", "after_section")

READER_PROMPT_CONTRACT_VERSION = "p2-reader-v1"

# Coarse reading-answer outcome class -> triage-reason weight seed (design A.1).
# Lowercase so the parameter-registry AST scan (UPPERCASE only) does not require
# per-entry registration; the single registered magnitude knob is
# ROUTING_PRIOR_MAX_WEIGHT and the single decay knob ROUTING_PRIOR_HALFLIFE_DAYS.
_reason_weight_seed: dict[str, tuple[str, float]] = {
    # outcome_class : (triage_reason, base_weight in [0, 1])
    "confused": ("false_belief_or_confusion", 1.0),
    "partial": ("unknown_or_ambiguous", 0.6),
    "clear": ("unfamiliar_content", 0.3),
    "unknown": ("unknown_or_ambiguous", 0.5),
}


class ReaderDialogueError(ValueError):
    pass


def reader_enabled(vault: LoadedVault) -> bool:
    """Launch default OFF (§12.3.2): the golden path completes without the reader.

    The reader module is never imported on the canonical golden-path walk; this
    flag is the owner opt-in for the reader surfaces themselves."""

    return bool(getattr(vault.config.tutor_qa, "reader_enabled", False))


# ---------------------------------------------------------------------------
# Owner-reviewable prompt contract (U-034 artifact; deterministic).
# ---------------------------------------------------------------------------

def reader_prompt_contract() -> dict[str, Any]:
    """The owner-reviewable ``reader`` prompt/manifest contract (design A.2).

    Deterministic (no live AI) so it can be diffed + reviewed like any other
    U-034 artifact and asserted in tests. Declares exactly what the reader answer
    MAY reveal, what the context manifest carries, and -- load-bearing for
    invariant 10 -- what it must NEVER receive."""

    return {
        "version": READER_PROMPT_CONTRACT_VERSION,
        "context": "reader",
        "not_socratic_by_default": True,
        "answer_modes": list(READER_ANSWER_MODES),
        "default_answer_mode": READER_ANSWER_MODE_DEFAULT,
        "may_reveal": [
            "state facts",
            "complete a derivation",
            "give a worked example",
            "confirm or deny an interpretation",
        ],
        "manifest_includes": [
            "the exact source span(s) in view (block-level span_view text + citation ids)",
            "the learner question text",
            "the goal-contract task invariants + required capabilities (read-only head)",
            "prior reader exchanges on the same span only",
            "the chosen answer mode for this ask",
        ],
        "manifest_never_includes": [
            "the learner ability / posterior estimate",
            "any assessment-reserved surface statement or rubric",
            "any cold administration's in-flight response",
        ],
        "citations": "reuse tutor_qa validated citations; uncited claims are stripped",
        "exposure_on_commit": "familiarity.propagate_tutor_exposure (warms revealed cues)",
    }


# ---------------------------------------------------------------------------
# Context manifest (reader_context_manifest_v1, design A.2).
# ---------------------------------------------------------------------------

def build_reader_manifest(
    repository: Repository,
    *,
    extraction_id: str,
    span_id: str,
    question_md: str,
    answer_mode: str,
    goal_invariants: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """The exact bounded context handed to the reader tutor (design A.2).

    Carries the in-view span + surrounding blocks, the question, the chosen mode,
    the read-only goal-contract invariants, and the prior same-span exchanges. It
    deliberately carries NO ability estimate and NO assessment-reserved content."""

    span_key = tutor_qa.reader_span_key(extraction_id, span_id)
    source_spans = tutor_qa._reader_source_spans(repository, extraction_id, span_id)
    prior = repository.question_events(
        context="reader", note_id=span_key, answer_status="answered"
    )
    return {
        "version": READER_PROMPT_CONTRACT_VERSION,
        "span": {"extraction_id": extraction_id, "span_id": span_id, "key": span_key},
        "source_spans": source_spans,
        "question_md": question_md,
        "answer_mode": answer_mode,
        # Read-only current goal head (invariants + required capabilities). Bounded
        # to the connection fields only; never the learner posterior.
        "goal_invariants": dict(goal_invariants) if goal_invariants is not None else None,
        "prior_exchanges": [
            {"question_md": e["question_md"], "answer_md": e["answer_md"]}
            for e in prior
        ],
        # Explicit negative space -- asserted by tests; the ability estimate and any
        # reserved surface content are structurally absent.
        "excluded": ["ability_estimate", "assessment_reserved_surface", "cold_in_flight_response"],
    }


# ---------------------------------------------------------------------------
# Learner -> AI (Ask).
# ---------------------------------------------------------------------------

def set_answer_mode(
    repository: Repository,
    *,
    extraction_id: str,
    span_id: str,
    answer_mode: str,
    clock: Clock | None = None,
) -> str:
    """Log the per-ask answer-mode toggle (``reader_answer_mode_set``)."""

    if answer_mode not in READER_ANSWER_MODES:
        raise ReaderDialogueError(f"unknown reader answer mode: {answer_mode!r}")
    return log_interaction_event(
        repository,
        kind="reader_answer_mode_set",
        origin="learner",
        subject_type="reader_span",
        subject_id=tutor_qa.reader_span_key(extraction_id, span_id),
        payload={"answer_mode": answer_mode, "extraction_id": extraction_id, "span_id": span_id},
        clock=clock,
    )


def set_mode(
    repository: Repository,
    *,
    mode: str,
    extraction_id: str | None = None,
    session_id: str | None = None,
    clock: Clock | None = None,
) -> dict[str, Any]:
    """Set the reading mode (skim/anchor/incremental, §5.1). Appends a salience-only
    ``reader_mode_changed`` event: it gates owner-placed questions and reorders
    proposal priority only -- it never alters evidence eligibility (§5.1, §C)."""

    if mode not in READER_MODES:
        raise ReaderDialogueError(f"unknown reader mode: {mode!r}")
    event_id = log_interaction_event(
        repository,
        kind="reader_mode_changed",
        origin="learner",
        subject_type="reader_extraction",
        subject_id=extraction_id,
        payload=salience_payload({"mode": mode, "extraction_id": extraction_id, "session_id": session_id}),
        clock=clock,
    )
    # §5.1: skim never presents owner-placed questions; anchor presents at placed
    # boundaries; incremental presents at most the pretest prime on revisit.
    presents_questions = {"skim": "never", "anchor": "at_boundaries", "incremental": "pretest_prime_only"}[mode]
    return {"event_id": event_id, "mode": mode, "presents_owner_questions": presents_questions}


def question_control(
    repository: Repository,
    *,
    control: str,
    administration_id: str | None = None,
    subject_id: str | None = None,
    subject_type: str = "reader_span",
    clock: Clock | None = None,
) -> dict[str, Any]:
    """Record a per-question control (§5.1). All are interaction-policy signals on the
    envelope, never ability evidence (salience-only, §C). ``i_dont_understand`` routes
    to source restoration/instruction, never to a lapse."""

    if control not in READER_QUESTION_CONTROLS:
        raise ReaderDialogueError(f"unknown question control: {control!r}")
    routes_to = "source_restoration" if control == "i_dont_understand" else None
    event_id = log_interaction_event(
        repository,
        kind="reader_question_control",
        origin="learner",
        subject_type=subject_type,
        subject_id=subject_id,
        administration_id=administration_id,
        payload=salience_payload({"control": control, "routes_to": routes_to}),
        clock=clock,
    )
    return {"event_id": event_id, "control": control, "routes_to": routes_to, "signal": "interaction_policy"}


def _normalize_tokens(text: str) -> list[str]:
    return [t for t in re.sub(r"[^a-z0-9 ]+", " ", text.lower()).split() if t]


def _bigrams(tokens: Sequence[str]) -> set[tuple[str, str]]:
    return {(tokens[i], tokens[i + 1]) for i in range(len(tokens) - 1)}


def _verbatim_overlap(answer_md: str, statement: str) -> float:
    """Cheap word-bigram overlap: the share of a reserved statement's bigrams that
    appear in the answer (no LLM, L3). ~1.0 when the answer quotes the statement."""

    statement_bigrams = _bigrams(_normalize_tokens(statement))
    if not statement_bigrams:
        return 0.0
    answer_bigrams = _bigrams(_normalize_tokens(answer_md))
    return len(answer_bigrams & statement_bigrams) / len(statement_bigrams)


def _surface_statement_text(surface_row: Mapping[str, Any]) -> str:
    surf = surface_row.get("surface") or {}
    parts = [
        str(surf[key])
        for key in ("prompt", "statement", "statement_md", "question", "expected_answer")
        if isinstance(surf.get(key), str)
    ]
    return " ".join(parts)


def _detect_revealed_reserves(
    repository: Repository,
    *,
    answer_md: str,
    citations: Sequence[Mapping[str, Any]],
    caller_supplied: Sequence[str],
) -> list[str]:
    """Server-side reveal detection (L3): map the answer's text + validated citations
    against every LIVE assessment reserve by surface_hash / fingerprint / verbatim
    overlap (>= ``READER_REVEAL_OVERLAP_THRESHOLD``). Returns the reserved surface ids
    the answer leaked that the caller did NOT already declare -- so the caller-supplied
    ids are UNIONed with these before burning."""

    reserves = repository.reserved_assessment_surfaces()
    if not reserves:
        return []
    caller_set = set(caller_supplied)
    # Hash/fingerprint tokens the answer text or a citation label may echo verbatim.
    haystack = " ".join(
        [answer_md, *[str(c.get("label") or "") for c in citations]]
    )
    detected: list[str] = []
    for surface in reserves:
        sid = surface["id"]
        if sid in caller_set or sid in detected:
            continue
        surface_hash = surface.get("surface_hash")
        fingerprint = surface.get("fingerprint")
        hash_hit = bool(surface_hash) and str(surface_hash) in haystack
        fp_hit = bool(fingerprint) and str(fingerprint) in haystack
        statement = _surface_statement_text(surface)
        overlap_hit = bool(statement) and _verbatim_overlap(answer_md, statement) >= READER_REVEAL_OVERLAP_THRESHOLD
        if hash_hit or fp_hit or overlap_hit:
            detected.append(sid)
    return detected


def ask(
    vault: LoadedVault,
    repository: Repository,
    client: Any,
    *,
    extraction_id: str,
    span_id: str,
    question_md: str,
    answer_mode: str = READER_ANSWER_MODE_DEFAULT,
    target_key: str | None = None,
    goal_invariants: Mapping[str, Any] | None = None,
    revealed_surface_ids: Sequence[str] = (),
    cold_active: bool = False,
    cold_attempt_id: str | None = None,
    clock: Clock | None = None,
) -> dict[str, Any]:
    """Answer a span-grounded reader question (§7.6).

    The learner question is elicitation about the source, never ability evidence
    (the reader context attaches no facets). On answer commit the revealed cues
    warm related surfaces (familiarity) and any explicitly-revealed reserved
    surface is burned on the exposure ledger so its reserve is invalidated exactly
    as any other exposure. Persists the full exchange on the
    ``reader_answer_submitted`` event.

    ``cold_active`` marks that a cold administration is open: the answer is then
    hint-equivalent and the touched surfaces lose cold eligibility (§7.4). Callers
    surface this rather than concealing it. When ``cold_attempt_id`` is supplied
    (L6), the exchange is ALSO linked into the practice hint accounting: a
    hint-equivalent practice ``question_event`` is recorded for that attempt's
    (item, session) so the landed practice evidence path dampens the cold attempt
    exactly as an in-attempt tutor hint would -- not just telemetry."""

    if answer_mode not in READER_ANSWER_MODES:
        raise ReaderDialogueError(f"unknown reader answer mode: {answer_mode!r}")

    span_key = tutor_qa.reader_span_key(extraction_id, span_id)
    manifest = build_reader_manifest(
        repository,
        extraction_id=extraction_id,
        span_id=span_id,
        question_md=question_md,
        answer_mode=answer_mode,
        goal_invariants=goal_invariants,
    )

    # Signal ordering: mode + asked land before the (possibly failing) provider call.
    set_answer_mode(repository, extraction_id=extraction_id, span_id=span_id,
                    answer_mode=answer_mode, clock=clock)
    log_interaction_event(
        repository,
        kind="learner_question_asked",
        origin="learner",
        subject_type="reader_span",
        subject_id=span_key,
        payload={"question_md": question_md, "extraction_id": extraction_id, "span_id": span_id},
        clock=clock,
    )

    result = tutor_qa.ask_question(
        vault,
        repository,
        client,
        context="reader",
        question_md=question_md,
        extraction_id=extraction_id,
        span_id=span_id,
        answer_mode=answer_mode,
        clock=clock,
    )

    # L3 server-side reveal detection: an answer can leak a reserved surface even when
    # the caller forgets to declare it. Derive candidate revealed reserves from the
    # answer text + validated citations (surface_hash / fingerprint / verbatim overlap),
    # and UNION them with the caller-supplied ids BEFORE burning -- so a quoted reserve
    # is always invalidated, never silently left eligible.
    detected = _detect_revealed_reserves(
        repository,
        answer_md=result.get("answer_md") or "",
        citations=result.get("citations") or [],
        caller_supplied=revealed_surface_ids,
    )
    all_revealed: list[str] = list(dict.fromkeys([*revealed_surface_ids, *detected]))

    # Exposure (§7.6 / P1 §4.1): revealed cues warm related surfaces. An explicitly
    # revealed reserved surface is ALSO burned on the ledger so eligibility flips.
    warmed: list[str] = []
    burned: list[str] = []
    for surface_id in all_revealed:
        surface = repository.fetch_surface(surface_id)
        if surface is None:
            continue
        familiarity.propagate_tutor_exposure(
            repository,
            explanation_fingerprints=[
                {
                    "surface_id": surface_id,
                    "namespace": "source_example",
                    "value_hash": tutor_qa.reader_span_key(extraction_id, span_id),
                }
            ],
            clock=clock,
        )
        warmed.append(surface_id)
        append_exposure(
            repository,
            surface=surface,
            administration_id=None,
            kind="externally_reported",
            purpose="instructional",
            consumes_unseen=False,
            detail={"reader_span": span_key, "reason": "reader_answer_revealed_cue"},
            clock=clock,
        )
        burned.append(surface_id)

    submitted_event_id = log_interaction_event(
        repository,
        kind="reader_answer_submitted",
        origin="system",
        subject_type="reader_span",
        subject_id=span_key,
        payload={
            "question_event_id": result["event_id"],
            "extraction_id": extraction_id,
            "span_id": span_id,
            "answer_mode": answer_mode,
            "answer_md": result["answer_md"],
            "citations": result["citations"],
            "manifest": manifest,
            "provider": getattr(client, "provider_name", None),
            "provider_type": getattr(client, "provider_type", None),
            "model": getattr(client, "model", None),
            # invariant 10: never ability evidence; routing-prior target only.
            "target_key": target_key,
            "outcome_class": "unknown",
            "hint_equivalent": bool(cold_active),
            "source_visible": True,
        },
        clock=clock,
    )

    # L6: a cold-active Ask is hint-equivalent under the existing practice rules -- link
    # it into the ATTEMPT's hint accounting, not just telemetry. Record a practice-context
    # hint-equivalent question_event for the cold attempt's (item, session) so the landed
    # practice evidence path (tutor_qa.hint_equivalents_for_submission /_for_attempt)
    # dampens the cold attempt exactly as an in-attempt tutor hint.
    cold_hint_event_id: str | None = None
    if cold_active and cold_attempt_id is not None:
        cold_hint_event_id = _record_cold_hint_equivalent(
            repository,
            cold_attempt_id=cold_attempt_id,
            question_md=question_md,
            answer_md=result["answer_md"],
            span_key=span_key,
            clock=clock,
        )

    return {
        "event_id": result["event_id"],
        "reader_answer_event_id": submitted_event_id,
        "answer_md": result["answer_md"],
        "answer_mode": answer_mode,
        "citations": result["citations"],
        "manifest": manifest,
        "warmed_surface_ids": warmed,
        "burned_surface_ids": burned,
        "hint_equivalent": bool(cold_active),
        "cold_hint_event_id": cold_hint_event_id,
        "remaining": result["remaining"],
    }


def _record_cold_hint_equivalent(
    repository: Repository,
    *,
    cold_attempt_id: str,
    question_md: str,
    answer_md: str | None,
    span_key: str,
    clock: Clock | None,
) -> str | None:
    """Record the cold reader Ask as a hint-equivalent PRACTICE question_event tied to
    the cold attempt's (item, session), so the practice evidence path counts it (L6).
    No-op when the attempt cannot be resolved."""

    attempt = repository.fetch_practice_attempt(cold_attempt_id)
    if attempt is None:
        return None
    return repository.insert_question_event(
        {
            "context": "practice",
            "practice_item_id": attempt.get("practice_item_id"),
            "attempt_id": cold_attempt_id,
            "session_id": attempt.get("session_id"),
            "question_md": question_md,
            "answer_md": answer_md,
            "question_type": "other",
            "hint_equivalent": True,
            "answer_status": "answered",
            "signal_channel": "interaction_preference",
            "provider": "reader",
        },
        clock=clock,
    )


# ---------------------------------------------------------------------------
# AI -> learner (owner-placed reading questions).
# ---------------------------------------------------------------------------

def administer_reading_question(
    vault: LoadedVault,
    repository: Repository,
    item: Any,
    *,
    reading_phase: str,
    goal_id: str | None = None,
    target_contract_version_id: str | None = None,
    clock: Clock | None = None,
) -> dict[str, Any]:
    """Render an owner-placed reading question as an instructional administration
    (§7.6): ``source_visible=true`` + a ``reading_phase``, no new activity kind.

    Instructional purpose is categorically ineligible for certification -- the
    ``InstructionalAdapter`` mints no unassisted certification (invariant 9). This
    primes/scaffolds; it is never cold evidence."""

    if reading_phase not in READING_PHASES:
        raise ReaderDialogueError(f"unknown reading phase: {reading_phase!r}")

    resolved = resolve_legacy_item(vault, repository, item, purpose="instructional", clock=clock)
    reservation = reserve_surface(
        repository,
        surface_id=resolved.surface_id,
        purpose="instructional",
        goal_id=goal_id,
        clock=clock,
    )
    admin = open_administration(
        repository,
        resolved=resolved,
        reservation=reservation,
        goal_id=goal_id,
        target_contract_version_id=target_contract_version_id,
        assistance={"source_visible": True, "reading_phase": reading_phase},
        feedback_condition="after_response",
        clock=clock,
    )
    # Stamp the migration-076 context columns (reading_phase + source_visible).
    repository.set_administration_context(
        administration_id=admin.administration_id,
        reading_phase=reading_phase,
        admin_context={"source_visible": True, "reading_phase": reading_phase, "cold": False},
    )
    effects = administration_adapters.resolve_adapter("instructional").effects(
        eligible=True, failed=False
    )
    assert effects.mints_unassisted_certification is False, "instructional never certifies"

    log_interaction_event(
        repository,
        kind="reader_question_presented",
        origin="owner_tooling",
        subject_type="administration",
        subject_id=admin.administration_id,
        administration_id=admin.administration_id,
        surface_id=resolved.surface_id,
        payload={"reading_phase": reading_phase, "source_visible": True},
        clock=clock,
    )
    return {
        "administration_id": admin.administration_id,
        "surface_id": resolved.surface_id,
        "purpose": "instructional",
        "reading_phase": reading_phase,
        "source_visible": True,
        "certification_eligible": False,
    }


def skip_reading_question(
    repository: Repository,
    *,
    administration_id: str,
    clock: Clock | None = None,
) -> str:
    """A skip is an interaction-policy signal, NEVER low-ability evidence (§7.6)."""

    return log_interaction_event(
        repository,
        kind="reader_question_skipped",
        origin="learner",
        subject_type="administration",
        subject_id=administration_id,
        administration_id=administration_id,
        payload={"signal": "interaction_policy", "ability_evidence": False},
        clock=clock,
    )


def submit_reading_question(
    repository: Repository,
    *,
    administration_id: str,
    response_md: str | None = None,
    target_key: str | None = None,
    outcome_class: str = "unknown",
    clock: Clock | None = None,
) -> str:
    """Record an answer to an owner-placed reading question (source_visible
    instructional; primes/scaffolds, never cold evidence)."""

    return log_interaction_event(
        repository,
        kind="reader_answer_submitted",
        origin="learner",
        subject_type="administration",
        subject_id=administration_id,
        administration_id=administration_id,
        payload={
            "response_md": response_md,
            "source_visible": True,
            "target_key": target_key,
            "outcome_class": outcome_class,
            "hint_equivalent": True,
        },
        clock=clock,
    )


# ---------------------------------------------------------------------------
# Disposition picker (four dispositions, §7.6).
# ---------------------------------------------------------------------------

def choose_disposition(
    vault: LoadedVault,
    repository: Repository,
    *,
    disposition: str,
    subject_id: str,
    subject_type: str = "reader_span",
    commitment_target: Mapping[str, Any] | None = None,
    goal_id: str | None = None,
    client_idempotency_key: str | None = None,
    clock: Clock | None = None,
) -> dict[str, Any]:
    """Apply one of the four reading dispositions -- and nothing else (§7.6).

    ``keep_developing`` is the ONLY commit-class path (creates/extends the
    commitment). ``comprehension_only`` / ``reference_only`` log the exchange
    only. ``check_once_later`` reserves exactly one single-use diagnostic cold
    check. No reading interaction creates a commitment silently."""

    if disposition not in READER_DISPOSITIONS:
        raise ReaderDialogueError(f"unknown disposition: {disposition!r}")

    outcome: dict[str, Any] = {"disposition": disposition}

    if disposition == "keep_developing":
        # The single commit-class action (§3.1 commit-class; invariant 4).
        target = dict(commitment_target) if commitment_target is not None else {
            "target_kind": "source_locator",
            "target_ref": subject_id,
            "role": "required",
        }
        commitment = commitments.create_commitment(
            repository,
            action="help_me_remember",
            intent_text="keep developing this reading",
            targets=[target],
            depth_preset="remember_key_ideas",
            goal_id=goal_id,
            client_idempotency_key=client_idempotency_key,
            reason="reader_keep_developing",
            clock=clock,
        )
        outcome["commitment_id"] = commitment.id
        outcome["mechanism"] = "commitment"
    elif disposition == "check_once_later":
        outcome["mechanism"] = "single_use_diagnostic_check"
        outcome["single_use"] = True
    elif disposition == "reference_only":
        outcome["mechanism"] = "citation_preserved"
    else:  # comprehension_only
        outcome["mechanism"] = "logged_only"

    event_id = log_interaction_event(
        repository,
        kind="reader_disposition_chosen",
        origin="learner",
        subject_type=subject_type,
        subject_id=subject_id,
        payload=outcome,
        clock=clock,
    )
    outcome["event_id"] = event_id
    return outcome


# ---------------------------------------------------------------------------
# Source restoration during reading (§7.4 / §7.6).
# ---------------------------------------------------------------------------

def restore_source(
    repository: Repository,
    *,
    extraction_id: str,
    span_id: str,
    cold_surface_id: str | None = None,
    cold_administration_id: str | None = None,
    clock: Clock | None = None,
) -> dict[str, Any]:
    """Restore a source span during reading. If a cold administration is open, the
    restore is a contamination event: it burns cold eligibility (never conceals)."""

    span_key = tutor_qa.reader_span_key(extraction_id, span_id)
    try:
        view = build_span_view(repository, extraction_id, span_id, context="other",
                               record=True, clock=clock)
    except SpanViewError as exc:
        raise ReaderDialogueError(str(exc)) from exc

    burned = False
    if cold_surface_id is not None:
        surface = repository.fetch_surface(cold_surface_id)
        if surface is not None:
            append_exposure(
                repository,
                surface=surface,
                administration_id=cold_administration_id,
                kind="externally_reported",
                purpose="instructional",
                consumes_unseen=False,
                detail={"reader_span": span_key, "reason": "source_restored_during_cold"},
                clock=clock,
            )
            burned = True

    event_id = log_interaction_event(
        repository,
        kind="reader_source_restored",
        origin="learner",
        subject_type="reader_span",
        subject_id=span_key,
        surface_id=cold_surface_id,
        administration_id=cold_administration_id,
        payload={
            "extraction_id": extraction_id,
            "span_id": span_id,
            "cold_eligibility_burned": burned,
        },
        clock=clock,
    )
    return {"event_id": event_id, "text": view.get("text"), "cold_eligibility_burned": burned}


# ---------------------------------------------------------------------------
# Routing prior (design A.1) -- replay-derived, no stored table.
# ---------------------------------------------------------------------------

def routing_prior_projection_v1(
    repository: Repository,
    *,
    target_key: str,
    as_of: str | None = None,
    cold_observation_at: str | None = None,
    halflife_days: float | None = None,
    max_weight: float | None = None,
    clock: Clock | None = None,
) -> dict[str, Any]:
    """Fold ``reader_answer_submitted`` events for ``target_key`` into a bounded,
    replay-derived routing prior (design A.1 / spec §7.6 evidence semantics).

    Pure projection -- NO stored prior table. It contributes only to tier-two
    triage inside the U-027 decision-aid channel (labeled ``heuristic``) and is
    superseded structurally by the first cold observation on the same target: once
    a cold observation exists at/after the first reading answer, every reading
    answer contributes ZERO and only survives in the trace as a labeled,
    superseded input. It never touches a posterior/FSRS/certification.

    ``cold_observation_at`` may be supplied by the caller; otherwise it is read
    from the ledger (``first_cold_observation_for_target``)."""

    halflife = ROUTING_PRIOR_HALFLIFE_DAYS if halflife_days is None else halflife_days
    cap = ROUTING_PRIOR_MAX_WEIGHT if max_weight is None else max_weight
    now = as_of or utc_now_iso(clock)

    reading_answers = [
        event
        for event in repository.reader_interaction_events(kind="reader_answer_submitted")
        if isinstance(event.get("payload"), Mapping)
        and event["payload"].get("target_key") == target_key
    ]
    reading_answers.sort(key=lambda e: (e["created_at"], e["id"]))

    trace: list[dict[str, Any]] = []
    if not reading_answers:
        return {
            "target_key": target_key,
            "channel": "u027_decision_aid",
            "label": "heuristic",
            "superseded": False,
            "reasons": {},
            "hypothesis_seed_ids": [],
            "trace": trace,
        }

    if cold_observation_at is None:
        cold_observation_at = repository.first_cold_observation_for_target(target_key)
    # L9: ANY cold observation on the target supersedes the formative routing prior --
    # regardless of ordering. A cold observation is real ability evidence; once one
    # exists the reading-answer prior contributes zero (even a cold observation recorded
    # BEFORE the reading answer supersedes it -- the prior never revives).
    superseded = cold_observation_at is not None

    reasons: dict[str, float] = {}
    seeds: list[str] = []
    for event in reading_answers:
        payload = event["payload"]
        outcome_class = str(payload.get("outcome_class") or "unknown")
        reason, base = _reason_weight_seed.get(outcome_class, _reason_weight_seed["unknown"])
        elapsed_days = max(0.0, _days_between(event["created_at"], now))
        decay = 0.5 ** (elapsed_days / halflife) if halflife > 0 else 1.0
        weight = min(cap, base * cap * decay)
        seed_id = payload.get("question_event_id") or event["id"]
        contribution = 0.0 if superseded else weight
        if not superseded:
            reasons[reason] = reasons.get(reason, 0.0) + weight
            seeds.append(seed_id)
        trace.append(
            {
                "reading_answer_event_id": event["id"],
                "reason": reason,
                "weight": weight,
                "contribution": contribution,
                "superseded": superseded,
                "label": "heuristic",
            }
        )

    return {
        "target_key": target_key,
        "channel": "u027_decision_aid",
        "label": "heuristic",
        "superseded": superseded,
        "superseded_by_at": cold_observation_at if superseded else None,
        "reasons": reasons,
        "hypothesis_seed_ids": seeds,
        "trace": trace,
    }


def _days_between(start_iso: str, end_iso: str) -> float:
    start = parse_utc(start_iso)
    end = parse_utc(end_iso)
    return (end - start).total_seconds() / 86400.0


# ---------------------------------------------------------------------------
# Deterministic stub client (offline fixture render + tests; no live AI).
# ---------------------------------------------------------------------------

class StubReaderClient:
    """A deterministic ``reader`` tutor client (U-034 stub). Echoes a bounded,
    citation-carrying answer so offline fixtures + tests render without live AI."""

    provider_name = "stub_reader"
    provider_type = "stub"
    model = "stub-reader-1"

    def __init__(self, *, answer_md: str = "Grounded in the span in view.") -> None:
        self.answer_md = answer_md
        self.contexts: list[Any] = []

    def run_tutor_qa(self, context: Any) -> Any:
        from learnloop.codex.schemas import TutorAnswer, TutorCitation

        self.contexts.append(context)
        citations = [
            TutorCitation(
                extraction_id=str(span.get("extraction_id")),
                span_id=str(span.get("span_id")),
                label=str(span.get("label") or ""),
            )
            for span in (context.source_spans or [])[:1]
        ]
        return TutorAnswer(
            answer_md=self.answer_md,
            question_type="other",
            facets=[],
            citations=citations,
        )

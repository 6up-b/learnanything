"""Misconception registry normalization and evidence-based resolution.

Implements spec_misconception_diagnostics.md §2.2 (normalize per-attempt error
events into content-bearing registry rows) and §7 (posterior-driven resolution
rekeyed to ``misconception_id``). Both run *after* error-event persistence and
*before* follow-up evaluation (§4.3), never inside ``apply_attempt`` — replay
must reproduce links/status from persisted attempts + error events, not from a
fresh LLM call.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from learnloop.clock import Clock, parse_utc
from learnloop.db.repositories import MisconceptionRecord, Repository
from learnloop.services.error_taxonomy_map import map_legacy_error_type
from learnloop.services.facet_state_reader import is_canonical_state_vault
from learnloop.vault.models import LoadedVault

# §10.3 promotion is high-confidence-gated when a single first-error trace is the
# only evidence; below this a lone attribution stays a candidate.
_FIRST_ERROR_TRACE_CONFIDENCE = 0.9

_PUNCT_RE = re.compile(r"[^\w\s]")
_WS_RE = re.compile(r"\s+")


def _normalize_text(text: str) -> str:
    """Case/whitespace/punctuation-normalized statement for deterministic match."""

    lowered = _PUNCT_RE.sub(" ", text.lower())
    return _WS_RE.sub(" ", lowered).strip()


def _confusable_neighbor_concepts(vault: LoadedVault, concept_id: str | None) -> list[str]:
    """Concepts reachable from ``concept_id`` over ``confusable_with`` edges (§2.2.1)."""

    if concept_id is None:
        return []
    neighbors: list[str] = []
    for edge in vault.edges:
        if edge.relation_type != "confusable_with":
            continue
        if edge.source == concept_id:
            neighbors.append(edge.target)
        elif edge.target == concept_id:
            neighbors.append(edge.source)
    return neighbors


def _candidate_misconceptions(
    vault: LoadedVault,
    repository: Repository,
    learning_object_id: str,
) -> list[MisconceptionRecord]:
    """Registry rows a new attribution on this LO could merge into (spec §2.2.1).

    The LO's own rows (including ``resolved``, so a returning belief reactivates
    rather than duplicating) plus ``active``/``resolving`` rows on the LO's
    concept and its ``confusable_with`` neighbors.
    """

    learning_object = vault.learning_objects.get(learning_object_id)
    concept_id = learning_object.concept if learning_object is not None else None
    candidates: dict[str, MisconceptionRecord] = {
        row.id: row
        for row in repository.misconceptions_for_learning_object(
            learning_object_id, statuses=("active", "resolving", "resolved")
        )
    }
    concept_scope = [concept_id, *_confusable_neighbor_concepts(vault, concept_id)]
    concept_scope = [c for c in concept_scope if c]
    for row in repository.misconceptions_for_concepts(concept_scope, statuses=("active", "resolving")):
        candidates.setdefault(row.id, row)
    return list(candidates.values())


@dataclass(frozen=True)
class MisconceptionMatchContext:
    """Bounded input for the optional LLM belief-match call (spec §2.2.2)."""

    statement: str
    learning_object_id: str
    candidates: list[dict[str, str]]


def _match_misconception(
    statement: str,
    candidates: list[MisconceptionRecord],
    ai_client: object | None,
    *,
    learning_object_id: str,
) -> str | None:
    """Return the id of the registry row ``statement`` belongs to, or ``None`` (new).

    Prefers the provider's ``run_misconception_match`` when available; otherwise
    falls back to a deterministic normalized-text match. Never dedupes by error
    type (spec §2.2.2).
    """

    if not candidates:
        return None
    runner = getattr(ai_client, "run_misconception_match", None)
    if callable(runner):
        context = MisconceptionMatchContext(
            statement=statement,
            learning_object_id=learning_object_id,
            candidates=[{"id": row.id, "statement": row.statement} for row in candidates],
        )
        try:
            result = runner(context)
        except Exception:
            result = None
        if result is not None:
            decision = getattr(result, "decision", None)
            matched_id = getattr(result, "misconception_id", None)
            if decision == "same" and matched_id in {row.id for row in candidates}:
                return matched_id
            if decision in {"same", "new"}:
                # A well-formed "new" (or a "same" with an unknown id) is trusted;
                # only a malformed response falls through to the text heuristic.
                return matched_id if decision == "same" else None
    target = _normalize_text(statement)
    for row in candidates:
        if _normalize_text(row.statement) == target:
            return row.id
    return None


def _event_facet_ids(vault: LoadedVault, event: dict, attempt: dict | None) -> list[str]:
    """Coarse facets a new registry row targets (spec §1.1 / §2.2.4).

    The event's repair-plan ``target_evidence_families`` (canonicalized), falling
    back to the attempt's evidence facets when the grader named none.
    """

    repair_plan = event.get("repair_plan")
    families = repair_plan.get("target_evidence_families") if isinstance(repair_plan, dict) else None
    if isinstance(families, list) and families:
        return list(dict.fromkeys(vault.canonical_facet_id(str(f)) for f in families))
    if attempt is not None:
        evidence = attempt.get("evidence_facets")
        if isinstance(evidence, list) and evidence:
            return list(dict.fromkeys(vault.canonical_facet_id(str(f)) for f in evidence))
    return []


def normalize_attempt_misconceptions(
    vault: LoadedVault,
    repository: Repository,
    *,
    attempt_id: str,
    learning_object_id: str,
    ai_client: object | None = None,
    clock: Clock | None = None,
) -> list[str]:
    """Normalize an attempt's misconception error events into the registry (spec §2.2).

    For each error event that is a misconception AND carries a non-empty
    ``misconception_statement`` (statementless self-grade/legacy events keep the
    legacy behavior and never create registry rows), match against candidate
    registry rows and either merge (``same``) or insert (``new``), then write the
    ``misconception_id`` back onto the event. Idempotent: events already linked
    are skipped, so replay/re-normalization is a no-op. Returns the touched ids.
    """

    learning_object = vault.learning_objects.get(learning_object_id)
    if learning_object is None:
        return []
    if is_canonical_state_vault(vault):
        return _normalize_compositional(
            vault,
            repository,
            attempt_id=attempt_id,
            learning_object_id=learning_object_id,
            ai_client=ai_client,
            clock=clock,
        )
    events = repository.error_events_for_attempt(attempt_id)
    attempt = repository.fetch_practice_attempt(attempt_id)
    candidates = _candidate_misconceptions(vault, repository, learning_object_id)
    touched: list[str] = []
    for event in events:
        if not event.get("is_misconception"):
            continue
        statement = (event.get("misconception_statement") or "").strip()
        if not statement:
            continue
        if event.get("misconception_id"):
            continue  # already normalized (idempotent / replay-safe)
        severity = float(event.get("severity") or 0.0)
        match_id = _match_misconception(
            statement, candidates, ai_client, learning_object_id=learning_object_id
        )
        if match_id is not None:
            existing = repository.misconception(match_id)
            if existing is not None:
                new_status = "active" if existing.status in ("resolving", "resolved") else existing.status
                repository.update_misconception(
                    match_id,
                    severity=max(existing.severity, severity),
                    status=new_status,
                    append_source_error_event_ids=[event["id"]],
                    clock=clock,
                )
                misconception_id = match_id
            else:
                misconception_id = None
        else:
            misconception_id = None
        if misconception_id is None:
            misconception_id = repository.insert_misconception(
                learning_object_id=learning_object_id,
                statement=statement,
                concept_id=learning_object.concept,
                signature=event.get("misconception_consistent_answer"),
                facet_ids=_event_facet_ids(vault, event, attempt),
                severity=severity,
                source_error_event_ids=[event["id"]],
                clock=clock,
            )
            inserted = repository.misconception(misconception_id)
            if inserted is not None:
                candidates.append(inserted)  # dedupe repeats within the same attempt
            # Probe redesign §6.5: a newly registered high-severity misconception
            # is a re-probe trigger — a NEW episode with a fresh locked set that
            # includes the belief, replacing the stale diagnosis.
            from learnloop.services.probe_episodes import maybe_reprobe_for_misconception

            maybe_reprobe_for_misconception(
                vault, repository, learning_object_id, severity=severity, clock=clock
            )
        repository.set_error_event_misconception(event["id"], misconception_id, clock=clock)
        touched.append(misconception_id)
    return touched


# -- §10.2/§10.3 compositional records + promotion discipline (mvp-0.7) ------


def _surface_family_for_attempt(vault: LoadedVault, attempt: dict | None) -> str | None:
    if attempt is None:
        return None
    item = vault.practice_items.get(str(attempt.get("practice_item_id") or ""))
    return getattr(item, "surface_family", None) if item is not None else None


def _promotion_reason(candidate: dict, attempt: dict | None) -> str | None:
    """Which §10.3 condition (if any) promotes ``candidate`` to a durable belief.

    A one-off ambiguous failure stays a candidate distribution. Promotion needs
    an independent surface repeat, a targeted probe reproduction, or a
    high-confidence first-error trace. (The fourth condition — maps to a
    validated registry belief — is handled up-front by the durable-row match.)
    """

    if len(set(candidate.get("surface_families") or [])) >= 2:
        return "independent_surface"
    if len(set(candidate.get("item_ids") or [])) >= 2:
        return "independent_surface"
    attempt_type = str((attempt or {}).get("attempt_type") or "")
    if attempt_type == "diagnostic_probe":
        return "probe_reproduction"
    confidence = (attempt or {}).get("grader_confidence")
    if (
        confidence is not None
        and float(confidence) >= _FIRST_ERROR_TRACE_CONFIDENCE
        and candidate.get("target_facet")
    ):
        return "first_error_trace"
    return None


def _promote_candidate(
    vault: LoadedVault,
    repository: Repository,
    candidate: dict,
    *,
    learning_object,
    reason: str,
    clock: Clock | None,
) -> str:
    """Mint a durable compositional misconception from a promoted candidate (§10.2)."""

    signature = candidate.get("signature")
    correction_statement, correction_spans = _authored_correction(
        vault,
        candidate.get("target_facet"),
        candidate.get("confused_with_facet"),
    )
    misconception_id = repository.insert_misconception(
        learning_object_id=candidate["learning_object_id"],
        statement=candidate["statement"],
        concept_id=candidate.get("concept_id") or learning_object.concept,
        signature=signature,
        facet_ids=candidate.get("facet_ids") or [],
        severity=float(candidate.get("severity") or 0.0),
        source_error_event_ids=candidate.get("source_error_event_ids") or [],
        mechanism=candidate.get("mechanism"),
        operation=candidate.get("operation"),
        target_facet=candidate.get("target_facet"),
        confused_with_facet=candidate.get("confused_with_facet"),
        expected_signatures=[signature] if signature else [],
        promotion_reason=reason,
        correction_statement=correction_statement,
        correction_source_span_ids=correction_spans,
        clock=clock,
    )
    repository.update_misconception_candidate(
        candidate["id"],
        status="promoted",
        promoted_misconception_id=misconception_id,
        promotion_reason=reason,
        clock=clock,
    )
    from learnloop.services.probe_episodes import maybe_reprobe_for_misconception

    maybe_reprobe_for_misconception(
        vault,
        repository,
        candidate["learning_object_id"],
        severity=float(candidate.get("severity") or 0.0),
        clock=clock,
    )
    return misconception_id


def _authored_correction(
    vault: LoadedVault,
    target_facet_id: str | None,
    confused_with_facet_id: str | None,
) -> tuple[str | None, list[str]]:
    """Freeze correction copy from reviewed canonical facet contracts.

    This runs only at promotion time. Rendering later reads the stored sentence;
    it never synthesizes a distinction from live content.
    """

    if not target_facet_id:
        return None, []
    target = vault.evidence_facets.get(vault.canonical_facet_id(target_facet_id))
    confused = (
        vault.evidence_facets.get(vault.canonical_facet_id(confused_with_facet_id))
        if confused_with_facet_id
        else None
    )
    if target is None or not target.claim:
        return None, []
    if confused is not None and confused.claim:
        correction = f"Use this distinction: {target.claim} By contrast, {confused.claim}"
    else:
        correction = target.claim
    refs = [
        ref.ref_id
        for facet in (target, confused)
        if facet is not None
        for ref in facet.provenance.source_refs
    ]
    return correction, list(dict.fromkeys(refs))


def _normalize_compositional(
    vault: LoadedVault,
    repository: Repository,
    *,
    attempt_id: str,
    learning_object_id: str,
    ai_client: object | None,
    clock: Clock | None,
) -> list[str]:
    """mvp-0.7 normalization with promotion discipline (§10.3) and compositional
    records (§10.2).

    A misconception error event does NOT immediately mint a durable belief:

    * If it maps to an already-validated (active) registry belief, merge into it
      (promotion by validated belief).
    * If the attempt's failure is an open unresolved cause set, it stays a
      distribution over causes — no candidate, no mint.
    * Otherwise it accumulates in the candidate holding pen; it promotes to a
      durable compositional misconception only when a §10.3 condition fires.

    Events left as candidates keep ``misconception_id`` NULL, so replay/
    re-normalization reproduces the same durable rows statelessly.
    """

    learning_object = vault.learning_objects.get(learning_object_id)
    if learning_object is None:
        return []
    events = repository.error_events_for_attempt(attempt_id)
    attempt = repository.fetch_practice_attempt(attempt_id)
    open_unresolved = bool(
        repository.unresolved_cause_factors_for_attempt(attempt_id, status="open")
    )
    surface_family = _surface_family_for_attempt(vault, attempt)
    item_id = str(attempt.get("practice_item_id")) if attempt else None
    durable_candidates = _candidate_misconceptions(vault, repository, learning_object_id)
    touched: list[str] = []
    for event in events:
        if not event.get("is_misconception"):
            continue
        statement = (event.get("misconception_statement") or "").strip()
        if not statement:
            continue
        if event.get("misconception_id"):
            continue  # already normalized (idempotent / replay-safe)
        severity = float(event.get("severity") or 0.0)

        # (a) maps to a validated registry belief -> merge (promotion).
        match_id = _match_misconception(
            statement, durable_candidates, ai_client, learning_object_id=learning_object_id
        )
        if match_id is not None:
            existing = repository.misconception(match_id)
            if existing is not None:
                new_status = "active" if existing.status in ("resolving", "resolved") else existing.status
                repository.update_misconception(
                    match_id,
                    severity=max(existing.severity, severity),
                    status=new_status,
                    append_source_error_event_ids=[event["id"]],
                    clock=clock,
                )
                repository.set_error_event_misconception(event["id"], match_id, clock=clock)
                touched.append(match_id)
                continue

        # (b) an unresolved cause set stays a distribution — never mints.
        if open_unresolved:
            continue

        # (c) accumulate in the candidate holding pen, then check promotion.
        normalized = _normalize_text(statement)
        facets = _event_facet_ids(vault, event, attempt)
        target_facet = facets[0] if facets else None
        confused_with_facet = facets[1] if len(facets) > 1 else None
        mechanism = map_legacy_error_type(str(event.get("error_type") or "")) or None
        signature = event.get("misconception_consistent_answer")
        candidate = repository.misconception_candidate_by_normalized(
            learning_object_id, normalized
        )
        if candidate is None:
            candidate_id = repository.insert_misconception_candidate(
                learning_object_id=learning_object_id,
                statement=statement,
                statement_normalized=normalized,
                concept_id=learning_object.concept,
                signature=signature,
                mechanism=mechanism,
                target_facet=target_facet,
                confused_with_facet=confused_with_facet,
                facet_ids=facets,
                source_error_event_ids=[event["id"]],
                surface_families=[surface_family] if surface_family else [],
                item_ids=[item_id] if item_id else [],
                occurrence_count=1,
                severity=severity,
                clock=clock,
            )
        else:
            candidate_id = candidate["id"]
            repository.update_misconception_candidate(
                candidate_id,
                severity=max(float(candidate.get("severity") or 0.0), severity),
                occurrence_count=int(candidate.get("occurrence_count") or 0) + 1,
                append_source_error_event_ids=[event["id"]],
                add_surface_families=[surface_family] if surface_family else [],
                add_item_ids=[item_id] if item_id else [],
                signature=signature or candidate.get("signature"),
                mechanism=mechanism or candidate.get("mechanism"),
                target_facet=target_facet or candidate.get("target_facet"),
                confused_with_facet=confused_with_facet or candidate.get("confused_with_facet"),
                clock=clock,
            )
        candidate = repository.misconception_candidate_by_id(candidate_id)
        if candidate is None:
            continue
        reason = _promotion_reason(candidate, attempt)
        if reason is None:
            continue
        misconception_id = _promote_candidate(
            vault,
            repository,
            candidate,
            learning_object=learning_object,
            reason=reason,
            clock=clock,
        )
        # Refresh durable candidates so a repeat within this attempt merges.
        promoted = repository.misconception(misconception_id)
        if promoted is not None:
            durable_candidates.append(promoted)
        repository.set_error_event_misconception(event["id"], misconception_id, clock=clock)
        touched.append(misconception_id)
    return touched


# -- §7 posterior update & resolution ---------------------------------------

_PRIOR_FLOOR = 0.05
_PRIOR_CEIL = 0.95
_PROB_EPS = 1e-6


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def misconception_posterior(
    vault: LoadedVault,
    repository: Repository,
    record: MisconceptionRecord,
) -> float:
    """P(learner still holds ``record``) from persisted evidence (spec §7).

    Prior is the row's severity clamped to ``[0.05, 0.95]`` (simple, deterministic,
    documented). Each attempt on the LO at/after the row's ``created_at`` updates
    the odds by the §1.3 likelihood ratio: a keyed fatal fire → ``sens/(1-spec)``;
    a discriminating item with no fire → ``(1-sens)/spec``; an item with no
    discrimination row for this belief leaves the odds untouched (LR 1).
    """

    prior = _clamp(record.severity, _PRIOR_FLOOR, _PRIOR_CEIL)
    odds = prior / (1.0 - prior)
    entered = parse_utc(record.created_at)
    attempts = sorted(
        repository.list_attempts_by_learning_object(record.learning_object_id),
        key=lambda row: (str(row.get("created_at") or ""), str(row.get("id") or "")),
    )
    for attempt in attempts:
        created = parse_utc(attempt.get("created_at"))
        if entered is not None and created is not None and created < entered:
            continue
        item_id = attempt.get("practice_item_id")
        if not item_id:
            continue
        discrimination = repository.discrimination_row(str(item_id), record.id)
        if discrimination is None:
            continue  # unlinked item: no fire-mass separation (§7)
        sens = _clamp(discrimination.sensitivity_mean, _PROB_EPS, 1.0 - _PROB_EPS)
        spec = _clamp(discrimination.specificity_mean, _PROB_EPS, 1.0 - _PROB_EPS)
        fired = any(
            evt.get("misconception_id") == record.id
            for evt in repository.error_events_for_attempt(str(attempt.get("id")))
        )
        if fired:
            odds *= sens / (1.0 - spec)
        else:
            odds *= (1.0 - sens) / spec
    return odds / (1.0 + odds)


def update_misconception_posteriors_and_resolve(
    vault: LoadedVault,
    repository: Repository,
    *,
    learning_object_id: str,
    clock: Clock | None = None,
) -> list[str]:
    """Resolve (or reactivate) registry rows on ``learning_object_id`` by posterior (§7).

    Stateless recompute from persisted attempts + error events, so replay
    reproduces the same status. A row whose posterior falls below
    ``tau_misconception_resolved`` flips to ``resolved`` (its source events are
    resolved too, keeping the legacy views coherent); a resolved row whose
    posterior climbs back above the threshold reactivates. Legacy statementless
    events are untouched — they have no registry row. Returns resolved ids.
    """

    tau = vault.config.misconceptions.tau_misconception_resolved
    resolved_ids: list[str] = []
    rows = repository.misconceptions_for_learning_object(
        learning_object_id, statuses=("active", "resolving", "resolved")
    )
    for record in rows:
        posterior = misconception_posterior(vault, repository, record)
        should_resolve = posterior < tau
        if should_resolve and record.status != "resolved":
            repository.update_misconception(
                record.id,
                status="resolved",
                transition_source="posterior",
                clock=clock,
            )
            for event_id in record.source_error_event_ids:
                repository.resolve_error_event(event_id, clock=clock)
            resolved_ids.append(record.id)
        elif not should_resolve and record.status == "resolved":
            repository.update_misconception(
                record.id,
                status="active",
                transition_source="posterior",
                clock=clock,
            )
    return resolved_ids


def normalize_and_resolve_attempt(
    vault: LoadedVault,
    repository: Repository,
    *,
    attempt_id: str,
    learning_object_id: str,
    ai_client: object | None = None,
    clock: Clock | None = None,
) -> list[str]:
    """Run normalization then posterior resolution for one attempt (spec §2.2 + §7).

    The single entrypoint wired in front of follow-up evaluation so the just-
    diagnosed belief is visible to the hypothesis prior and routing (§4.3).
    """

    touched = normalize_attempt_misconceptions(
        vault,
        repository,
        attempt_id=attempt_id,
        learning_object_id=learning_object_id,
        ai_client=ai_client,
        clock=clock,
    )
    update_misconception_posteriors_and_resolve(
        vault, repository, learning_object_id=learning_object_id, clock=clock
    )
    return touched

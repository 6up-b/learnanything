"""Durable misconception-repair episode lifecycle and cold retries."""

from __future__ import annotations

import logging
from collections.abc import Mapping
from datetime import UTC, timedelta
from typing import Any

from learnloop.clock import Clock, SystemClock, parse_utc
from learnloop.db.repositories import Repository
from learnloop.ingest.locators import parse_block_span
from learnloop.content.sources.exam_material import exam_material, exposed_items
from learnloop.content.sources.provenance import get_entity_provenance
from learnloop.reader.span_view import SpanViewError, build_span_view
from learnloop.vault.models import LoadedVault

logger = logging.getLogger(__name__)

REPAIR_COLD_OPPORTUNITY_POLICY_VERSION = "repair_cold_opportunity_v1"

#: The delay between the priming attempt and the earliest honest cold retry.
#: One authority for the lane's "later session, not this one" rule: scheduling
#: (`record_remediation_attempt`) sets `not_before` at +this, the scheduler
#: re-applies it when a reveal contaminates a task that was already due
#: (`scheduler._defer_revealed_cold_followups`), and `coldness_receipt
#: .MIN_COLD_DELAY` mirrors it as the receipt's `retrieval_delay` floor. A
#: module constant rather than vault config: it is the definition of the
#: instrument, not a tuning knob — a vault that shortened it would still call
#: the result a cold retrieval.
COLD_RETRIEVAL_DELAY = timedelta(days=1)

#: How long a scheduled cold retry stays takeable after it falls due (its
#: ``expires_at`` is ``not_before`` + this). Named for the cold-retry
#: reschedule (``mvp-0.38``), which gives a fresh retry the lane's own window;
#: the value is the one ``record_remediation_attempt`` always used inline.
COLD_RETRY_WINDOW = timedelta(days=30)

#: How much of a repair episode's answer may be handed over before the cold
#: measurement at the end of it is worth less than it claims. Expressed on the
#: reveal ledger's 0..1 fraction-of-answer scale and summed over the episode's
#: own rows (`episode_reveal_spend`).
#:
#: A module constant, not vault config — same reasoning as
#: `causal_factor_deferral.ESCALATION_RECURRENCE_K` and `FACTOR_DEFERRAL_TTL`:
#: the budget is a property of what a repair episode IS (a bounded amount of
#: telling, followed by an unassisted check), not a per-vault preference. 0.85
#: leaves room for a full worked example plus a partial restatement while still
#: falling short of "the answer was simply given"; a vault free to raise it to
#: 1.0 could call an outright answer transfer a repair.
#:
#: Measured, not enforced, in this slice: nothing refuses a repair or a
#: verification on budget. The spend travels on the repair status and on the
#: cold-scheduling context so the eventual verification can say the episode was
#: over-budget rather than pretending it was not.
EPISODE_REVEAL_BUDGET = 0.85


class RemediationError(ValueError):
    pass


class RemediationBlocked(RemediationError):
    """A repair that the causal state holds back, with its typed status.

    Carries the full :class:`~learnloop.diagnosis.causal_orchestrator.RepairStatus`
    so a caller can render the §6 learner copy and actions instead of a bare
    string. ``str(exc)`` is the learner-facing message.
    """

    def __init__(self, status: Any) -> None:
        super().__init__(status.message)
        self.repair_status = status

    @property
    def status(self) -> str:
        return str(self.repair_status.status)


def open_episode_for_practice_item(
    repository: Repository, practice_item_id: str | None
) -> dict[str, Any] | None:
    """The live repair episode a reveal on ``practice_item_id`` belongs to.

    Attribution only — this never creates or advances an episode. Preference
    order:

    1. the episode still waiting for its primed attempt on this exact item
       (``open_remediation_episode_for_primed_item``), the binding
       ``record_remediation_attempt`` itself uses, so a reveal and the attempt
       it contaminates land on the same episode;
    2. otherwise the newest live episode holding the item as its primed *or*
       cold surface — a reveal on a scheduled cold item is the contamination
       the ledger exists to catch, and that item has no primed binding.

    Returns ``None`` when the item is not part of any live repair, which is the
    ordinary case: a reveal outside a repair is still a reveal, just an
    unattributed one."""

    if not practice_item_id:
        return None
    episode = repository.open_remediation_episode_for_primed_item(practice_item_id)
    if episode is not None:
        return episode
    episodes = repository.open_remediation_episodes_for_item(practice_item_id)
    return episodes[0] if episodes else None


def episode_reveal_spend(repository: Repository, episode_id: str | None) -> float:
    """How much answer this repair episode has already handed over (0..1+).

    Sums the ledger rows STAMPED with the episode — an unattributed reveal on
    the same item is still a reveal, but it is not this episode's spend, and
    inferring attribution here would double-count exposures the ledger
    deliberately left unattributed. Read-only and best-effort: a ledger failure
    reports 0.0 spend and logs rather than breaking a repair screen.
    """

    if not episode_id:
        return 0.0
    try:
        rows = repository.reveal_events(remediation_episode_id=episode_id)
    except Exception:  # pragma: no cover - defensive, evidence-only read
        logger.warning(
            "episode reveal spend read failed for %s", episode_id, exc_info=True
        )
        return 0.0
    return float(sum(float(row.get("amount") or 0.0) for row in rows))


def start_remediation_episode(
    repository: Repository,
    misconception_id: str,
    *,
    vault: LoadedVault | None = None,
    session_id: str | None = None,
    clock: Clock | None = None,
) -> dict[str, Any]:
    """Start the repair episode, or raise the typed causal hold.

    Thin adapter over ``causal_orchestrator.causal_repair_status`` (§6): the
    orchestrator owns the decision, records the probe-decision receipt, and
    creates the episode when the causal state permits it. Callers that want the
    learner offer (message + "Take the quick check" / "Teach me now" /
    "Not now") should call ``causal_repair_status`` directly.
    """

    from learnloop.diagnosis.causal_orchestrator import (
        CausalRepairError,
        causal_repair_status,
    )

    try:
        status = causal_repair_status(
            vault,
            repository,
            misconception_id=misconception_id,
            session_id=session_id,
            clock=clock,
        )
    except CausalRepairError as exc:
        raise RemediationError(str(exc)) from exc
    if status.episode is None:
        raise RemediationBlocked(status)
    return status.episode


def episode_case(repository: Repository, episode: dict[str, Any]) -> Any | None:
    if episode.get("case_kind") == "misconception":
        return repository.misconception(str(episode["case_ref"]))
    return repository.misconception_candidate_by_id(str(episode["case_ref"]))


def case_value(case: Any, key: str, default: Any = None) -> Any:
    if isinstance(case, dict):
        return case.get(key, default)
    return getattr(case, key, default)


def prescribe_remediation(
    vault: LoadedVault,
    repository: Repository,
    episode_id: str,
    *,
    clock: Clock | None = None,
    passage_provider: Any | None = None,
) -> dict[str, Any]:
    """Prescribe the passages a repair overlay shows.

    ``passage_provider`` (canonical sources S3, injected by the adapter: this
    package never imports the service) ranks and verifies passages for the
    misconception, at most one per role. When it is absent, returns nothing,
    or fails, today's first linked span per facet is used, so the prescription
    is byte-identical (G11), except that a link into exam or held-out material
    (the one exam predicate, ``content.sources.exam_material``) is never the
    passage a repair teaches from (exam protection, 2026-10-13).
    """
    episode = repository.remediation_episode(episode_id)
    if episode is None:
        raise RemediationError("remediation episode does not exist")
    misconception = episode_case(repository, episode)
    if misconception is None:
        raise RemediationError("remediation case no longer exists")

    passages: list[dict[str, Any]] = []
    if passage_provider is not None:
        try:
            ranked = list(passage_provider(vault, repository, misconception=misconception, episode=episode) or [])
        except Exception:  # noqa: BLE001 - the fallback below is today's prescription
            logger.warning("ranked remediation passages failed for %s", episode_id, exc_info=True)
            ranked = []
        for entry in ranked:
            try:
                view = build_span_view(
                    repository,
                    str(entry["extraction_id"]),
                    str(entry["span_id"]),
                    context="remediation",
                    entity_type="misconception",
                    entity_id=str(case_value(misconception, "id", episode["case_ref"])),
                    record=False,
                    clock=clock,
                )
            except SpanViewError:
                continue
            passages.append({"role": entry["role"], "facet_id": entry.get("facet_id"), "span_view": view,
                             "basis": entry.get("basis", "ranked_verified")})
        if passages:
            return repository.update_remediation_episode(
                episode_id, state="prescribed", passages_shown=passages, clock=clock
            ) or episode
    exam = None
    for role, facet_id in (
        ("target", case_value(misconception, "target_facet")),
        ("confused_with", case_value(misconception, "confused_with_facet")),
    ):
        if not facet_id:
            continue
        provenance = get_entity_provenance(repository, "facet", facet_id)
        links = provenance.get("semantic_sources") or []
        for link in links:
            parsed = parse_block_span(str(link.get("locator") or ""))
            if parsed is None:
                continue
            extraction_id, span_id = parsed
            if exam is None:
                exam = exam_material(vault, repository)
            if exam.covers(extraction_id, span_id):
                continue
            try:
                view = build_span_view(
                    repository,
                    extraction_id,
                    span_id,
                    context="remediation",
                    entity_type="misconception",
                    entity_id=str(case_value(misconception, "id", episode["case_ref"])),
                    record=False,
                    clock=clock,
                )
            except SpanViewError:
                continue
            passages.append({"role": role, "facet_id": facet_id, "span_view": view})
            break
    return repository.update_remediation_episode(
        episode_id, state="prescribed", passages_shown=passages, clock=clock
    ) or episode


#: Exposure discriminator for the delivery write (migration 150). Deliberately
#: NOT `remediation`, which means the learner clicked Open-in-source on a span:
#: this one claims only that the prescribed passage text was handed to the
#: surface that renders it inline.
REMEDIATION_DELIVERY_CONTEXT = "remediation_delivery"

#: The entity a delivery event is keyed by, so a coldness scan can correlate
#: deliveries with the episode whose prescription produced them (the case id is
#: not enough — one case can have several episodes).
REMEDIATION_DELIVERY_ENTITY_TYPE = "remediation_episode"


def record_prescription_delivery(
    repository: Repository,
    episode: Mapping[str, Any],
    *,
    clock: Clock | None = None,
) -> list[str]:
    """Record that this episode's prescribed passages were delivered for render.

    ``passages_shown_json`` records a PRESCRIPTION; this records the one thing
    about rendering that is actually observable server-side — that the passage
    text left the sidecar for the surface that displays it. The repair overlay
    renders the returned text inline with no further learner action, so delivery
    is the closest honest proxy for exposure; time on screen is not observed and
    stays declared as unobserved in the coldness receipt's coverage block.

    Returns the ids of the events written (empty when the prescription carried
    no resolvable spans). Never raises: a telemetry write must not be able to
    fail a serve.
    """

    episode_id = str(episode.get("id") or "")
    if not episode_id:
        return []
    written: list[str] = []
    for passage in episode.get("passages_shown") or []:
        if not isinstance(passage, Mapping):
            continue
        view = passage.get("span_view")
        if not isinstance(view, Mapping):
            continue
        extraction_id = str(view.get("extraction_id") or "")
        span_id = str(view.get("span_id") or "")
        if not extraction_id or not span_id:
            continue
        try:
            written.append(
                repository.insert_source_exposure_event(
                    {
                        "context": REMEDIATION_DELIVERY_CONTEXT,
                        "extraction_id": extraction_id,
                        "span_id": span_id,
                        "revision_id": view.get("revision_id"),
                        "source_id": view.get("source_id"),
                        "entity_type": REMEDIATION_DELIVERY_ENTITY_TYPE,
                        "entity_id": episode_id,
                        "page": view.get("page"),
                        "locator": view.get("locator"),
                        "section_path": list(view.get("section_path") or []),
                    },
                    clock=clock,
                )
            )
        except Exception:  # pragma: no cover - telemetry never fails a serve
            logger.warning(
                "remediation delivery exposure write failed for episode %s",
                episode_id,
                exc_info=True,
            )
    return written


#: An item attempted within this window is still "hot" — serving it again as the
#: primed half of a repair pair measures short-term memory of the question, not
#: the repair. Mirrors the lane's own §6.2 day boundary: the cold retry is not
#: schedulable before +1 day for exactly the same reason.
RECENT_ATTEMPT_WINDOW = timedelta(days=1)


def item_step_checkpoint_ids(target_refs) -> tuple[str, ...]:
    return tuple(
        dict.fromkeys(
            str(ref["checkpoint_id"])
            for ref in target_refs or []
            if isinstance(ref, dict)
            and ref.get("kind") == "item_step"
            and ref.get("checkpoint_id")
        )
    )


def _case_target_checkpoint_ids(
    repository: Repository,
    misconception,
    *,
    case_kind: str = "misconception",
    case_ref: str | None = None,
) -> tuple[str, ...]:
    """The checkpoint ids the case's selected repair class targets, if known.

    Misconception/candidate cases read the newest diagnosing attempt's receipt
    (`repair_selection` / `common_repair_cover` live there): the repair class's
    `item_step` target_refs carry `checkpoint_id`s, which is the
    checkpoint-precise targeting signal the facet-overlap ranking used to
    ignore. A diagnosis-kind case has no misconception-linked receipt path —
    its case_ref IS the causal hypothesis id, so the hypothesis's own
    `repair_class_id` resolves through the durable
    `causal_repair_class_definitions` store (migration 133) instead. Empty for
    legacy receipts — callers fall back to facet overlap alone."""

    if case_kind == "diagnosis" and case_ref:
        hypothesis = repository.causal_hypothesis(str(case_ref))
        repair_class_id = str((hypothesis or {}).get("repair_class_id") or "")
        if not repair_class_id:
            return ()
        definition = repository.causal_repair_class_definitions(
            [repair_class_id]
        ).get(repair_class_id)
        return item_step_checkpoint_ids((definition or {}).get("target_refs"))

    case_id = str(case_value(misconception, "id", "") or "")
    if not case_id:
        return ()
    source_event_ids = list(
        case_value(misconception, "source_error_event_ids", None) or []
    )
    try:
        attempt_ids = repository.attempt_ids_for_misconception(
            case_id, event_ids=source_event_ids
        )
    except Exception:  # pragma: no cover - candidate cases have no events table row
        return ()
    for attempt_id in attempt_ids:
        debug = repository.attempt_debug_payload(attempt_id) or {}
        attribution = debug.get("causal_attribution")
        if not isinstance(attribution, dict):
            continue
        receipt = attribution.get("diagnosis_receipt")
        if not isinstance(receipt, dict):
            continue
        selection = receipt.get("repair_selection")
        selected = selection.get("selected") if isinstance(selection, dict) else None
        repair_class = (
            selected.get("repair_class") if isinstance(selected, dict) else None
        )
        checkpoint_ids = item_step_checkpoint_ids(
            (repair_class or {}).get("target_refs")
        )
        if checkpoint_ids:
            return checkpoint_ids
    return ()


def item_checkpoints(item: Any) -> set[str]:
    contract = getattr(item, "trace_contract", None)
    if contract is None or getattr(contract, "status", None) != "available":
        return set()
    return {
        str(checkpoint)
        for recipe in contract.recipes
        for checkpoint in recipe.checkpoints
    }


def _rank_items(
    vault: LoadedVault,
    repository: Repository,
    misconception,
    *,
    target_checkpoint_ids: tuple[str, ...] = (),
    clock: Clock | None = None,
) -> tuple[list[Any], list[dict[str, Any]]]:
    """The repair's candidate items best-first, plus the servability skips.

    Ordering (deterministic, lowest key first):

    1. not attempted within :data:`RECENT_ATTEMPT_WINDOW` — an item the learner
       answered minutes ago is a memory probe, not a repair measurement;
    2. covers a targeted repair checkpoint — when the case's repair class names
       `item_step` targets, an item whose trace-contract recipes exercise those
       checkpoints measures the repaired step itself;
    3. facet overlap with the confused pair;
    4. least recently practiced;
    5. item id (stable tie-break).

    Meas §3.A2/§3.A3: an item whose stimulus the practice surface cannot render
    is not schedulable, and a repair episode is the worst place to break that
    rule. The primed/cold pair is the *measurement* of whether the repair took;
    serving an error hunt whose worked solution never reaches the surface means
    the learner cannot answer, the grader (which does receive the solution) marks
    every plant missed, and the episode records a failed repair the learner was
    never shown the material to make — a harmful write manufactured by the
    serving path, on the one attempt pair the repair is judged by.

    Skips are returned rather than dropped because this is a selection path: the
    ranking simply picks another item, and an invisible skip leaves
    "no practice item is available for this repair" as the only trace of a
    learning object that demonstrably has items.
    """

    from learnloop.substrate.instrument_serving import unservable_refusal

    target_facets = {
        vault.canonical_facet_id(facet)
        for facet in (
            case_value(misconception, "target_facet"),
            case_value(misconception, "confused_with_facet"),
        )
        if facet
    }
    targeted = {str(value) for value in target_checkpoint_ids if value}
    now = (clock or SystemClock()).now()
    ranked = []
    skipped: list[dict[str, Any]] = []
    for item in vault.practice_items.values():
        if item.learning_object_id != case_value(misconception, "learning_object_id"):
            continue
        state = repository.practice_item_state(item.id)
        if state is not None and not state.active:
            continue
        refusal = unservable_refusal(item)
        if refusal is not None:
            skipped.append(refusal)
            continue
        overlap = len(
            target_facets
            & {vault.canonical_facet_id(str(facet)) for facet in item.evidence_facets}
        )
        covers_checkpoint = bool(targeted & item_checkpoints(item)) if targeted else False
        # A seeded-but-never-attempted item has a state row whose
        # `last_attempt_at` is NULL; comparing that against another item's
        # timestamp raised TypeError and crashed the whole prescription. Treat
        # "never attempted" as the earliest possible time, which is also the
        # ordering this rank wants (least recently practiced first).
        last_attempt_at = (state.last_attempt_at or "") if state else ""
        attempted_recently = False
        if last_attempt_at:
            parsed = parse_utc(last_attempt_at)
            if parsed is not None:
                attempted_recently = now - parsed < RECENT_ATTEMPT_WINDOW
        ranked.append(
            (
                1 if attempted_recently else 0,
                0 if covers_checkpoint else 1,
                -overlap,
                last_attempt_at,
                item.id,
                item,
            )
        )
    return [entry[-1] for entry in sorted(ranked, key=lambda entry: entry[:-1])], skipped


def start_remediation_treatment(
    vault: LoadedVault,
    repository: Repository,
    episode_id: str,
    *,
    clock: Clock | None = None,
) -> dict[str, Any]:
    episode = repository.remediation_episode(episode_id)
    if episode is None:
        raise RemediationError("remediation episode does not exist")
    misconception = episode_case(repository, episode)
    if misconception is None:
        raise RemediationError("remediation case no longer exists")
    from learnloop.attempts.coldness_receipt import (
        LANE_REPAIR_COLD_RETRY,
        record_schedule_refusal_receipt,
    )

    opportunity = repository.get_or_create_cold_measurement_opportunity(
        lane=LANE_REPAIR_COLD_RETRY,
        trigger_kind="remediation_episode_selection",
        trigger_ref=episode_id,
        learning_object_id=(
            str(case_value(misconception, "learning_object_id") or "") or None
        ),
        case_kind=str(episode.get("case_kind") or "") or None,
        case_ref=str(episode.get("case_ref") or "") or None,
        remediation_episode_id=episode_id,
        policy_version=REPAIR_COLD_OPPORTUNITY_POLICY_VERSION,
        clock=clock,
    )
    episode = (
        repository.update_remediation_episode(
            episode_id,
            cold_measurement_opportunity_id=str(opportunity["id"]),
            clock=clock,
        )
        or episode
    )
    ranked, unservable_skips = _rank_items(
        vault,
        repository,
        misconception,
        target_checkpoint_ids=_case_target_checkpoint_ids(
            repository,
            misconception,
            case_kind=str(episode.get("case_kind") or "misconception"),
            case_ref=str(episode.get("case_ref") or "") or None,
        ),
        clock=clock,
    )
    if not ranked:
        decision = (
            "operationally_unavailable"
            if unservable_skips
            else "structurally_refused"
        )
        reason = "no_servable_item" if unservable_skips else "no_candidate_item"
        candidate_summary = {
            "candidate_count": 0,
            "unservable_skips": unservable_skips,
        }
        repository.record_cold_measurement_opportunity_decision(
            measurement_opportunity_id=str(opportunity["id"]),
            decision=decision,
            reason=reason,
            candidate_summary=candidate_summary,
            clock=clock,
        )
        record_schedule_refusal_receipt(
            repository,
            opportunity=opportunity,
            decision=decision,
            reason=reason,
            candidate_summary=candidate_summary,
            clock=clock,
        )
        if unservable_skips:
            # Name the rule that emptied the ranking. The bare message sends a
            # reader looking for an authoring failure when the items exist, are
            # active, and were refused by a known serving limit with a known
            # remedy.
            raise RemediationError(
                "no practice item is available for this repair: "
                f"{len(unservable_skips)} item(s) are not servable — "
                f"{unservable_skips[0]['remedy']}"
            )
        raise RemediationError("no practice item is available for this repair")
    primed = ranked[0]
    # §4.3 / spec §6.2: the cold retry is only a verification if it lands on an
    # independent surface. Prefer the best-ranked item in a DIFFERENT surface
    # group; when none exists, record that fact now (cold_item_id stays unset)
    # instead of scheduling a retry the consume-time guard is bound to reject.
    from learnloop.substrate.canonical_projection import surface_group_id

    primed_surface = surface_group_id(primed)
    # Exam protection (owner default 2026-10-13): an item whose own material
    # the learner was already shown (a reveal of its answer outside its own
    # attempt's feedback, its exercise or book solution read in a source, its
    # prompt rendered in a proposal), or one made from held-out material, is
    # never the cold check (off with ``goals.held_out_selection``).
    cold = _independent_cold_item(vault, repository, ranked[1:], excluded_surfaces={primed_surface})
    updates: dict[str, Any] = {
        "state": "treatment",
        "primed_item_id": primed.id,
    }
    if cold is not None:
        updates["cold_item_id"] = cold.id
    else:
        candidate_summary = {
            "primed_item_id": primed.id,
            "cold_item_id": None,
            "ranked_item_ids": [item.id for item in ranked],
        }
        repository.record_cold_measurement_opportunity_decision(
            measurement_opportunity_id=str(opportunity["id"]),
            decision="structurally_refused",
            reason="no_independent_surface",
            candidate_summary=candidate_summary,
            clock=clock,
        )
        record_schedule_refusal_receipt(
            repository,
            opportunity=opportunity,
            decision="structurally_refused",
            reason="no_independent_surface",
            candidate_summary=candidate_summary,
            clock=clock,
        )
    updated = repository.update_remediation_episode(episode_id, clock=clock, **updates)
    assert updated is not None
    return {
        "episode": updated,
        "primed_item_id": primed.id,
        "cold_item_id": cold.id if cold is not None else None,
        "cold_unmeasurable_reason": (
            None if cold is not None else "no_independent_surface"
        ),
        # Travels on the success result too, and the handler spreads it onto the
        # wire: the pair the learner gets is not the pair the ranking would have
        # chosen, and this is the only record of why.
        "unservable_skips": unservable_skips,
    }


def _independent_cold_item(
    vault: LoadedVault,
    repository: Repository,
    candidates: list[Any],
    *,
    excluded_surfaces: set[str | None],
) -> Any | None:
    """The best-ranked candidate on a surface group outside
    ``excluded_surfaces`` whose own material the learner was not shown (exam
    protection: ``exposed_items`` with held-out material), or None.

    THE cold-surface rule of the repair lane: treatment picks the episode's
    first cold item with it (excluding the primed surface), and the cold-retry
    reschedule (``mvp-0.38``) picks a fresh retry's with it (excluding every
    surface the episode already used, then skipping any surface already
    hard-contaminated since the primed attempt: Codex review F1)."""

    return next(iter(_independent_cold_candidates(vault, repository, candidates,
                                                  excluded_surfaces=excluded_surfaces)), None)


def _independent_cold_candidates(
    vault: LoadedVault,
    repository: Repository,
    candidates: list[Any],
    *,
    excluded_surfaces: set[str | None],
) -> list[Any]:
    """Every candidate :func:`_independent_cold_item` accepts, in rank order."""

    from learnloop.substrate.canonical_projection import surface_group_id

    shown = set(exposed_items(vault, repository, candidates, with_held_out=True))
    return [item for item in candidates
            if surface_group_id(item) not in excluded_surfaces and item.id not in shown]


def _record_unbound_primed_disposition(
    repository: Repository,
    attempt: dict[str, Any],
    *,
    vault: LoadedVault | None = None,
    clock: Clock | None = None,
) -> None:
    """Typed §4.3 disposition for a primed repair attempt with NO episode.

    Only fires when the attempt's own diagnosis receipt selected a repair
    class: that is the mark of primed *repair activity* (a guided redo or a
    diagnosed retry), as opposed to an ordinary primed attempt with nothing to
    measure. Mirrors the schedule-time ``unmeasurable_no_held_out_surface``
    pattern above — with no episode, no held-out cold surface was ever picked,
    so the repair structurally cannot convert to a cold verification — and the
    ``no_episode`` detail keeps the two schedule-time facts distinguishable.
    """

    from learnloop.diagnosis.causal_probe_coherence import record_causal_cold_outcome
    from learnloop.diagnosis.guided_redo import diagnosis_receipt, selected_repair

    selected = selected_repair(diagnosis_receipt(repository, str(attempt["id"])))
    repair_class = (selected or {}).get("repair_class")
    repair_class = repair_class if isinstance(repair_class, dict) else {}
    repair_class_id = str(repair_class.get("id") or "") or None
    if repair_class_id is None:
        return
    from learnloop.attempts.coldness_receipt import (
        LANE_REPAIR_COLD_RETRY,
        record_schedule_refusal_receipt,
    )

    opportunity = repository.get_or_create_cold_measurement_opportunity(
        lane=LANE_REPAIR_COLD_RETRY,
        trigger_kind="repair_primed_attempt",
        trigger_ref=str(attempt["id"]),
        learning_object_id=(
            str(attempt.get("learning_object_id") or "") or None
        ),
        source_attempt_id=str(attempt["id"]),
        policy_version=REPAIR_COLD_OPPORTUNITY_POLICY_VERSION,
        clock=clock,
    )
    candidate_summary = {
        "primed_item_id": str(attempt.get("practice_item_id") or "") or None,
        "cold_item_id": None,
        "repair_class_id": repair_class_id,
    }
    repository.record_cold_measurement_opportunity_decision(
        measurement_opportunity_id=str(opportunity["id"]),
        decision="structurally_refused",
        reason="no_episode",
        candidate_summary=candidate_summary,
        clock=clock,
    )
    record_schedule_refusal_receipt(
        repository,
        opportunity=opportunity,
        decision="structurally_refused",
        reason="no_episode",
        candidate_summary=candidate_summary,
        clock=clock,
    )
    hypothesis_ids = [
        str(row["id"])
        for row in repository.causal_hypotheses_for_attempt(str(attempt["id"]))
        if row.get("id")
    ]
    _repair_forecast(
        vault, repository, attempt, repair_class_id=repair_class_id, hypothesis_ids=hypothesis_ids,
        censor_reason="no_episode", clock=clock,
    )
    record_causal_cold_outcome(
        repository,
        outcome="unmeasurable_no_held_out_surface",
        source_attempt_id=str(attempt["id"]),
        repair_class_id=repair_class_id,
        hypothesis_ids=hypothesis_ids,
        servable_opportunity=False,
        detail={"stage": "schedule", "reason": "no_episode"},
        clock=clock,
    )


def _repair_forecast(
    vault: LoadedVault | None,
    repository: Repository,
    attempt: Mapping[str, Any],
    *,
    repair_class_id: str | None,
    hypothesis_ids: list[str] | tuple[str, ...] = (),
    episode: Mapping[str, Any] | None = None,
    task: Mapping[str, Any] | None = None,
    censor_reason: str | None = None,
    clock: Clock | None = None,
) -> None:
    """Saved diagnosis forecasts: the repair's predicted cold outcome, in the
    primed attempt's transaction (bound to its cold task, or censored at birth
    with the reason none was scheduled). ``vault`` None (replay, a regrade)
    writes nothing; it never raises."""

    if vault is None:
        return
    from learnloop.diagnosis.forecast_receipts import record_repair_expectation

    record_repair_expectation(
        vault, repository, attempt=attempt, repair_class_id=repair_class_id, hypothesis_ids=hypothesis_ids,
        episode=episode, task=task, censor_reason=censor_reason, clock=clock,
    )


def record_remediation_attempt(
    repository: Repository,
    attempt: dict[str, Any],
    *,
    clock: Clock | None = None,
    vault: LoadedVault | None = None,
) -> None:
    """Link treatment attempts and consume delayed tasks exactly once.

    ``vault`` (the live attempt step only; replay and a regrade pass none)
    lets a scheduled cold check record its repair forecast, and (from
    ``mvp-0.38``) an assisted due cold retry schedule its fresh retry.
    """

    # The cold-retry reschedule (mvp-0.38, owner decision 2026-10-25): help
    # taken on a due repair cold retry ends it now and schedules one fresh
    # retry. Live only (``vault``): replay and a regrade pass none, so they
    # schedule nothing. Off, below the tag, or for any other attempt it does
    # nothing and the predecessor's branches below run exactly as before.
    if vault is not None:
        try:
            # A savepoint of the attempt's transaction: a failure here rolls
            # the whole reschedule back (the retry stays open for the next
            # serve to withdraw, as the predecessor leaves it) and never fails
            # the attempt.
            with repository.atomic():
                reschedule_assisted_cold_retry(vault, repository, attempt, clock=clock)
        except Exception:  # pragma: no cover - bookkeeping must not fail an attempt
            logger.warning("cold-retry reschedule failed for attempt %s", attempt.get("id"), exc_info=True)

    if attempt.get("primed"):
        episode = repository.open_remediation_episode_for_primed_item(
            str(attempt["practice_item_id"])
        )
        if episode is None:
            # G6: a primed attempt that carries a diagnosed repair class but
            # found no episode (the guided redo's held/blocked arm, or any
            # primed retry taken with the repair lane closed) must not vanish —
            # nothing downstream would ever say why no cold retry exists.
            _record_unbound_primed_disposition(repository, attempt, vault=vault, clock=clock)
            return
        from learnloop.attempts.coldness_receipt import (
            LANE_REPAIR_COLD_RETRY,
            record_schedule_refusal_receipt,
        )

        opportunity_id = (
            str(episode.get("cold_measurement_opportunity_id") or "") or None
        )
        opportunity = (
            repository.cold_measurement_opportunity(opportunity_id)
            if opportunity_id
            else None
        )
        if opportunity is None:
            # Legacy/open episodes created before migration 151 first acquire
            # lineage here. New episodes already created it before selection.
            opportunity = repository.get_or_create_cold_measurement_opportunity(
                lane=LANE_REPAIR_COLD_RETRY,
                trigger_kind="repair_primed_attempt_legacy",
                trigger_ref=str(attempt["id"]),
                learning_object_id=(
                    str(attempt.get("learning_object_id") or "") or None
                ),
                case_kind=str(episode.get("case_kind") or "") or None,
                case_ref=str(episode.get("case_ref") or "") or None,
                remediation_episode_id=str(episode["id"]),
                source_attempt_id=str(attempt["id"]),
                policy_version=REPAIR_COLD_OPPORTUNITY_POLICY_VERSION,
                clock=clock,
            )
            repository.update_remediation_episode(
                str(episode["id"]),
                cold_measurement_opportunity_id=str(opportunity["id"]),
                clock=clock,
            )
        cold_item_id = str(episode.get("cold_item_id") or "")
        if not cold_item_id or cold_item_id == str(attempt["practice_item_id"]):
            # No independent surface existed when treatment picked the pair
            # (or a legacy episode reused the primed item). Scheduling would
            # only manufacture a verification the §6.2 guard rejects on
            # consume days later — record the typed §4.3 disposition now.
            from learnloop.diagnosis.causal_probe_coherence import (
                record_causal_cold_outcome,
            )

            repository.update_remediation_episode(
                episode["id"], primed_attempt_id=attempt["id"], clock=clock
            )
            record_causal_cold_outcome(
                repository,
                outcome="unmeasurable_no_held_out_surface",
                remediation_episode_id=str(episode["id"]),
                case_kind=str(episode.get("case_kind") or "") or None,
                case_ref=str(episode.get("case_ref") or "") or None,
                source_attempt_id=str(attempt["id"]),
                servable_opportunity=False,
                detail={
                    "stage": "schedule",
                    "reason": "same_surface_only"
                    if cold_item_id
                    else "no_independent_surface",
                },
                clock=clock,
            )
            reason = (
                "same_surface_only"
                if cold_item_id
                else "no_independent_surface"
            )
            _repair_forecast(
                vault, repository, attempt, repair_class_id=None,
                hypothesis_ids=[str(episode.get("case_ref") or "")] if episode.get("case_ref") else [],
                episode=episode, censor_reason=reason, clock=clock,
            )
            candidate_summary = {
                "primed_item_id": str(attempt["practice_item_id"]),
                "cold_item_id": cold_item_id or None,
            }
            repository.record_cold_measurement_opportunity_decision(
                measurement_opportunity_id=str(opportunity["id"]),
                decision="structurally_refused",
                reason=reason,
                candidate_summary=candidate_summary,
                clock=clock,
            )
            record_schedule_refusal_receipt(
                repository,
                opportunity=opportunity,
                decision="structurally_refused",
                reason=reason,
                candidate_summary=candidate_summary,
                clock=clock,
            )
            return
        created = parse_utc(attempt.get("created_at")) or (clock or SystemClock()).now()
        not_before = (created.astimezone(UTC) + COLD_RETRIEVAL_DELAY).replace(microsecond=0)
        expires = not_before + COLD_RETRY_WINDOW
        repository.update_remediation_episode(
            episode["id"], state="cold_scheduled", primed_attempt_id=attempt["id"], clock=clock
        )
        # §6.2: resolve the cold-verification inputs NOW and carry them on the
        # task. When the retry lands days later, the factor may have closed and
        # the receipt may be stale; reconstructing them then is exactly the
        # "future caller" assumption that left this channel unwired.
        from learnloop.diagnosis.causal_orchestrator import cold_verification_context

        context = cold_verification_context(
            None, repository, episode=episode, source_attempt=attempt
        )
        # What this episode spent from the reveal budget, resolved at schedule
        # time like the rest of the §6.2 context. The verification lands days
        # later, by which point more reveals may have accumulated against the
        # episode; the number carried here is the spend the SCHEDULING decision
        # saw, and `reveal_over_budget` is the fact a later reader would
        # otherwise have to re-derive from a constant it cannot see. Nothing is
        # blocked on it in this slice — an over-budget episode still schedules
        # its cold retry, it just cannot later claim nobody noticed.
        spend = episode_reveal_spend(repository, str(episode["id"]))
        context = dict(context) | {
            "reveal_spend": spend,
            "reveal_budget": EPISODE_REVEAL_BUDGET,
            "reveal_over_budget": spend > EPISODE_REVEAL_BUDGET,
        }
        # A diagnosis-kind episode whose context resolves no repair class would
        # schedule a 30-day retry doomed to land `missing_chain` at verification
        # (§4.3). New episodes can no longer be minted unmapped, but episodes
        # created before that gate — or through other entry points — still reach
        # here; record the refusal now instead of wasting the measurement.
        if str(episode.get("case_kind") or "") == "diagnosis" and not context.get(
            "repair_class_id"
        ):
            from learnloop.diagnosis.causal_probe_coherence import (
                record_causal_cold_outcome,
            )

            record_causal_cold_outcome(
                repository,
                outcome="missing_chain",
                remediation_episode_id=str(episode["id"]),
                case_kind=str(episode["case_kind"]),
                case_ref=str(episode["case_ref"]),
                source_attempt_id=str(attempt["id"]),
                repair_class_id=None,
                hypothesis_ids=[str(episode["case_ref"])],
                servable_opportunity=False,
                detail={"stage": "schedule", "reason": "no_repair_class"},
                clock=clock,
            )
            _repair_forecast(
                vault, repository, attempt, repair_class_id=None, hypothesis_ids=[str(episode["case_ref"])],
                episode=episode, censor_reason="no_repair_class", clock=clock,
            )
            candidate_summary = {
                "primed_item_id": str(attempt["practice_item_id"]),
                "cold_item_id": cold_item_id,
                "hypothesis_id": str(episode["case_ref"]),
            }
            repository.record_cold_measurement_opportunity_decision(
                measurement_opportunity_id=str(opportunity["id"]),
                decision="policy_refused",
                reason="no_repair_class",
                candidate_summary=candidate_summary,
                clock=clock,
            )
            record_schedule_refusal_receipt(
                repository,
                opportunity=opportunity,
                decision="policy_refused",
                reason="no_repair_class",
                candidate_summary=candidate_summary,
                clock=clock,
            )
            return
        candidate_summary = {
            "primed_item_id": str(attempt["practice_item_id"]),
            "cold_item_id": cold_item_id,
        }
        task = repository.create_followup_task(
            kind="cold_retry",
            case_kind=episode["case_kind"],
            case_ref=episode["case_ref"],
            source_attempt_id=attempt["id"],
            remediation_episode_id=episode["id"],
            not_before=not_before.isoformat().replace("+00:00", "Z"),
            expires_at=expires.isoformat().replace("+00:00", "Z"),
            selected_item_id=episode.get("cold_item_id"),
            context=context,
            measurement_opportunity_id=str(opportunity["id"]),
            measurement_decision_reason="independent_surface_selected",
            measurement_candidate_summary=candidate_summary,
            clock=clock,
        )
        _repair_forecast(
            vault, repository, attempt,
            repair_class_id=str(context.get("repair_class_id") or "") or None,
            hypothesis_ids=[str(value) for value in context.get("hypothesis_ids") or [] if value],
            episode=episode, task=task, clock=clock,
        )
        return

    # An exam sitting that happens to serve the cold item must not silently
    # consume the one cold measurement: the sitting is proctored, time-pressured
    # context — not the unassisted later-session retrieval the §6.2 receipt
    # claims — and burning the task on it leaves the episode "completed" on
    # contaminated evidence. Same taxonomy split the dual-write chokepoint uses
    # (`exam_evidence` / `exam_attempt`, migrations 018/022).
    if "exam" in str(attempt.get("attempt_type") or ""):
        return
    # Reader CA2 (mvp-0.34, §15 Q4): an attempt that took help is practice with
    # help, never the unassisted cold measurement, so it leaves the task open
    # (the next serve withdraws it as practised since scheduled). Before the
    # successor submit refused such an attempt on a cold task, so no recorded
    # attempt reaches here assisted: this changes nothing for them.
    if assisted_attempt(attempt):
        return

    # Ask for the repair lane by name (migration 139 added a second `kind` to the
    # same table). An unfiltered read returns whichever row sorts first, so a
    # queued §5.7 certification probe on the same item could shadow the cold
    # retry this function exists to consume.
    task = repository.active_followup_task_for_item(
        str(attempt["practice_item_id"]),
        kind="cold_retry",
        at=str(attempt.get("created_at") or ""),
    )
    if task is None:
        return
    consumed = repository.consume_followup_task(task["id"], attempt["id"], clock=clock)
    if consumed is None or consumed.get("status") != "consumed":
        return
    episode_id = task.get("remediation_episode_id")
    if episode_id:
        completed_at = str(attempt.get("created_at") or "")
        repository.update_remediation_episode(
            episode_id,
            state="completed",
            cold_attempt_id=attempt["id"],
            completed_at=completed_at,
            clock=clock,
        )


#: The ``context`` key a fresh cold retry carries (the cold-retry reschedule,
#: ``mvp-0.38``): where it came from. Its presence is the chain's bound: a
#: retry that carries it is never rescheduled again.
ASSISTED_RESCHEDULE_CONTEXT_KEY = "assisted_reschedule"

#: The trigger of a fresh retry's cold-measurement opportunity (one per
#: withdrawn retry: the opportunity's unique ``(lane, trigger_kind,
#: trigger_ref)`` key, ``trigger_ref`` = the withdrawn task).
ASSISTED_RESCHEDULE_TRIGGER = "assisted_cold_retry"


def reschedule_cold_after_assist_active(vault: Any) -> bool:
    """The cold-retry reschedule (``COLD_RETRY_RESCHEDULE_ALGORITHM_VERSION``,
    ``mvp-0.38``): at that tag or later with
    ``practice.reschedule_cold_after_assist`` on, and with Reader CA2's rule on
    (``serve_eligibility.help_converts_active``: without it submit refuses an
    assisted attempt on a due cold retry, so there is nothing to reschedule).
    Below the tag, switched off, or no vault (replay, a regrade): the
    predecessor."""

    from learnloop import serve_eligibility
    from learnloop.algorithm_versions import COLD_RETRY_RESCHEDULE_VERSIONS

    config = getattr(vault, "config", None)
    if config is None:
        return False
    version = getattr(getattr(config, "algorithms", None), "algorithm_version", None)
    switch = getattr(config, "practice", None)
    return (
        version in COLD_RETRY_RESCHEDULE_VERSIONS
        and bool(getattr(switch, "reschedule_cold_after_assist", False))
        and serve_eligibility.help_converts_active(vault)
    )


def reschedule_assisted_cold_retry(
    vault: LoadedVault | None,
    repository: Repository,
    attempt: Mapping[str, Any],
    *,
    clock: Clock | None = None,
) -> dict[str, Any] | None:
    """Help taken on a due repair cold retry: end it and schedule ONE fresh
    cold retry for the same repair (owner decision 2026-10-25, Reader CA2
    follow-up Q4; ``mvp-0.38``). Returns the fresh task, or None.

    Acts only when the rule is live (:func:`reschedule_cold_after_assist_active`)
    and ``attempt`` is assisted (:func:`assisted_attempt`: hints, a hinted
    type, or primed) on the item of a due, open ``cold_retry`` (the task an
    unassisted attempt would have consumed: the consumer's own lookup), and
    is not an exam attempt (which never touches the lane). Then, in the
    attempt's transaction:

    * the assisted retry is withdrawn now with the existing typed disposition
      (``withdraw_cold_measurement``: ``unmeasurable_no_held_out_surface``,
      reason ``cold_check_help_taken``, ``detail.stage = "submit"``) instead of
      at the next serve, where the predecessor withdraws it as practised;
    * unless that retry was itself a fresh one (its context carries
      :data:`ASSISTED_RESCHEDULE_CONTEXT_KEY`): one fresh retry per chain, a
      structural bound (keep), so help taken on every retry never schedules
      retries forever;
    * the fresh retry's surface is chosen by the lane's one rule
      (:func:`_independent_cold_item`) among the repair's ranked items,
      excluding the primed surface and the assisted retry's (the receipt's
      surface novelty fails on any surface already attempted), skipping any
      surface already hard-contaminated since the primed attempt (its answer
      seen or its group administered: the final receipt's own scan, Codex
      review F1); none left is recorded as a refused opportunity
      (``no_independent_surface``, or ``no_uncontaminated_surface`` when the
      exposure history ruled them all out) and the repair stays unmeasurable,
      as below the tag;
    * its timing is the lane's existing rule, read from the attempt that took
      the help (the latest exposure): due ``COLD_RETRIEVAL_DELAY`` after it,
      open for ``COLD_RETRY_WINDOW`` (no new delay);
    * it carries the withdrawn retry's scheduling-time context unchanged (the
      repair's primed source attempt, repair class, hypotheses: §6.2), plus
      where it came from, so the coldness receipt scans from the primed
      attempt and records the assisted attempt as the co-intervention it is.
      The episode's cold item moves to the fresh surface (reveal attribution
      follows it); the episode stays ``cold_scheduled``;
    * the fresh retry records its own repair forecast (bound to it, in the
      same transaction; Codex review F2), so a measured replacement resolves
      in ``learnloop diagnosis calibration`` while the withdrawn retry's
      forecast censors.

    A certification cold probe is never rescheduled: one probe per
    certificate, ever (``certification_cold_probe``, migration 139's unique
    index); an assisted probe stays practice and its next serve withdraws it.
    """

    if vault is None or not reschedule_cold_after_assist_active(vault):
        return None
    if not assisted_attempt(attempt) or "exam" in str(attempt.get("attempt_type") or ""):
        return None
    practice_item_id = str(attempt.get("practice_item_id") or "")
    attempted_at = str(attempt.get("created_at") or "")
    if not practice_item_id or not attempted_at:
        return None
    task = repository.active_followup_task_for_item(practice_item_id, kind="cold_retry", at=attempted_at)
    if task is None:
        return None
    from learnloop.serve_eligibility import COLD_CHECK_HELP_TAKEN

    withdrawn = withdraw_cold_measurement(
        vault, repository, str(task["id"]), reason=COLD_CHECK_HELP_TAKEN, stage="submit",
        decision={"assisted_attempt_id": str(attempt.get("id") or "")}, clock=clock,
    )
    if withdrawn is None or str(withdrawn.get("status") or "") != "expired":
        return None
    context = task.get("context")
    context = dict(context) if isinstance(context, Mapping) else {}
    if context.get(ASSISTED_RESCHEDULE_CONTEXT_KEY):
        # The bound: this retry was the chain's fresh one.
        logger.info("cold retry %s was itself a fresh retry; not rescheduled again", task["id"])
        return None
    episode_id = str(task.get("remediation_episode_id") or "")
    episode = repository.remediation_episode(episode_id) if episode_id else None
    if episode is None or str(episode.get("state") or "") != "cold_scheduled":
        return None
    case = episode_case(repository, episode)
    if case is None:
        return None
    from learnloop.attempts.coldness_receipt import (
        LANE_REPAIR_COLD_RETRY,
        record_schedule_refusal_receipt,
        repair_surface_hard_contamination,
    )
    from learnloop.substrate.canonical_projection import surface_group_id

    opportunity = repository.get_or_create_cold_measurement_opportunity(
        lane=LANE_REPAIR_COLD_RETRY,
        trigger_kind=ASSISTED_RESCHEDULE_TRIGGER,
        trigger_ref=str(task["id"]),
        learning_object_id=str(case_value(case, "learning_object_id") or "") or None,
        case_kind=str(episode.get("case_kind") or "") or None,
        case_ref=str(episode.get("case_ref") or "") or None,
        remediation_episode_id=episode_id,
        source_attempt_id=str(attempt.get("id") or "") or None,
        policy_version=REPAIR_COLD_OPPORTUNITY_POLICY_VERSION,
        clock=clock,
    )
    ranked, _unservable = _rank_items(
        vault, repository, case,
        target_checkpoint_ids=_case_target_checkpoint_ids(
            repository, case,
            case_kind=str(episode.get("case_kind") or "misconception"),
            case_ref=str(episode.get("case_ref") or "") or None,
        ),
        clock=clock,
    )
    used_items = [
        vault.practice_items.get(item_id)
        for item_id in (str(episode.get("primed_item_id") or ""), str(task.get("selected_item_id") or ""))
        if item_id
    ]
    excluded = {surface_group_id(item) for item in used_items if item is not None}
    excluded_ids = {item.id for item in used_items if item is not None}
    independent = _independent_cold_candidates(
        vault, repository, [item for item in ranked if item.id not in excluded_ids], excluded_surfaces=excluded,
    )
    # Codex review F1: the fresh retry keeps the primed source attempt, so its
    # final receipt scans from it. A surface whose answer the learner saw, or
    # whose group they were administered, since then is already a hard
    # contamination there: skip it (first clean one in rank order) rather than
    # spend an answer on a measurement unusable when scheduled.
    source_attempt_id = (
        str(context.get("source_attempt_id") or "") or str(task.get("source_attempt_id") or "")
    ) or None
    source_attempt = repository.fetch_practice_attempt(source_attempt_id) if source_attempt_id else None
    contaminated: dict[str, dict[str, Any]] = {}
    fresh_item = None
    for candidate in independent:
        hard = repair_surface_hard_contamination(
            vault, repository, source_attempt=source_attempt, cold_item_id=candidate.id,
            case_ref=str(task.get("case_ref") or "") or None, until=attempted_at,
        )
        if hard is None:
            fresh_item = candidate
            break
        contaminated[candidate.id] = {"reason": hard["reason"], "event_ids": list(hard["event_ids"])}
    candidate_summary = {
        "withdrawn_task_id": str(task["id"]),
        "assisted_attempt_id": str(attempt.get("id") or "") or None,
        "primed_item_id": str(episode.get("primed_item_id") or "") or None,
        "withdrawn_cold_item_id": str(task.get("selected_item_id") or "") or None,
        "cold_item_id": fresh_item.id if fresh_item is not None else None,
    }
    if contaminated:
        candidate_summary["contaminated"] = contaminated
    if fresh_item is None:
        candidate_summary["ranked_item_ids"] = [item.id for item in ranked]
        # Every independent surface already contaminated is its own structural
        # fact (the exposure history ruled them out), distinct from none at all.
        reason = "no_uncontaminated_surface" if contaminated else "no_independent_surface"
        repository.record_cold_measurement_opportunity_decision(
            measurement_opportunity_id=str(opportunity["id"]), decision="structurally_refused",
            reason=reason, candidate_summary=candidate_summary, clock=clock,
        )
        record_schedule_refusal_receipt(
            repository, opportunity=opportunity, decision="structurally_refused",
            reason=reason, candidate_summary=candidate_summary, clock=clock,
        )
        return None
    created = parse_utc(attempted_at) or (clock or SystemClock()).now()
    not_before = (created.astimezone(UTC) + COLD_RETRIEVAL_DELAY).replace(microsecond=0)
    expires = not_before + COLD_RETRY_WINDOW
    context[ASSISTED_RESCHEDULE_CONTEXT_KEY] = {
        "from_task_id": str(task["id"]),
        "assisted_attempt_id": str(attempt.get("id") or "") or None,
        "withdrawn_cold_item_id": str(task.get("selected_item_id") or "") or None,
        "reason": COLD_CHECK_HELP_TAKEN,
    }
    fresh = repository.create_followup_task(
        kind="cold_retry",
        case_kind=str(task.get("case_kind") or episode["case_kind"]),
        case_ref=str(task.get("case_ref") or episode["case_ref"]),
        source_attempt_id=str(task.get("source_attempt_id") or "") or None,
        remediation_episode_id=episode_id,
        not_before=not_before.isoformat().replace("+00:00", "Z"),
        expires_at=expires.isoformat().replace("+00:00", "Z"),
        selected_item_id=fresh_item.id,
        context=context,
        measurement_opportunity_id=str(opportunity["id"]),
        measurement_decision_reason="independent_surface_selected",
        measurement_candidate_summary=candidate_summary,
        clock=clock,
    )
    repository.update_remediation_episode(episode_id, cold_item_id=fresh_item.id, clock=clock)
    # Codex review F2: the replacement gets its own repair forecast, bound to
    # its own task in this scheduling transaction (the receipt key carries the
    # task, so the withdrawn retry's forecast stays as written and censors on
    # its disposition). It is the primed attempt's forecast, as the original
    # was: the repair class and hypotheses are the carried §6.2 context.
    if source_attempt is not None:
        _repair_forecast(
            vault, repository, source_attempt,
            repair_class_id=str(context.get("repair_class_id") or "") or None,
            hypothesis_ids=[str(value) for value in context.get("hypothesis_ids") or [] if value],
            episode=repository.remediation_episode(episode_id) or episode, task=fresh, clock=clock,
        )
    logger.info(
        "cold retry %s withdrawn after help was taken (attempt %s); fresh retry %s on %s",
        task["id"], attempt.get("id"), fresh["id"], fresh_item.id,
    )
    return fresh


def assisted_attempt(attempt: Mapping[str, Any]) -> bool:
    """Did the attempt take help (hints, a hinted type) or see its answer
    (primed)? Such an attempt never answers a cold measurement (Reader CA2)."""

    return (
        int(attempt.get("hints_used") or 0) > 0
        or str(attempt.get("attempt_type") or "") == "hinted_attempt"
        or bool(attempt.get("primed"))
    )


#: The terminal disposition of a repair cold retry withdrawn because its
#: surface can no longer be taken cold (``withdraw_cold_measurement``): its
#: selected surface is no longer held out, so the retry is unmeasurable there.
#: Not ``contaminated_or_assisted``, which (like every consume-time
#: disposition) is about a concrete cold attempt (migration 145's CHECK); and
#: not ``right_censored_expired``, which claims a genuine opportunity the
#: learner never took.
WITHDRAWN_COLD_RETRY_OUTCOME = "unmeasurable_no_held_out_surface"


def withdraw_cold_measurement(
    vault: LoadedVault | None,
    repository: Repository,
    task_id: str,
    *,
    reason: str,
    reveal_event_ids: tuple[str, ...] | list[str] = (),
    decision: Mapping[str, Any] | None = None,
    stage: str = "serve",
    clock: Clock | None = None,
) -> dict[str, Any] | None:
    """Withdraw an open cold measurement its selected surface can no longer
    give a cold reading (the one eligibility decision, ``mvp-0.27``; Codex
    review F2): the item's answer was shown with no lapse (submit primes it
    until an attempt, and an attempt on it is a hard exposure of the cold item
    in the receipt's scan), or the item was attempted since the check was set.

    Re-timing such a check only promised a measurement that could not be
    cold, and spent the learner's answer on it. So it ends now, honestly:

    * a repair ``cold_retry`` records its typed §4.3 disposition
      (:data:`WITHDRAWN_COLD_RETRY_OUTCOME`, no servable independent
      opportunity, ``detail.stage = stage`` (``"serve"``; ``"submit"`` when the
      cold-retry reschedule ends an assisted retry in its attempt's step) with
      the reason and the reveal rows) and its final coldness receipt, as the expiry sweep does for an
      expiry, then expires (the sweep sees the outcome and writes nothing
      more). If the disposition cannot be written the task is left open, so
      nothing ends unlabelled;
    * a ``certification_cold_probe`` expires, the existing door for a probe
      whose claim no longer stands (``_cancel_stale_probes``); its rate reads
      it as unmeasured.

    One transaction; idempotent (the outcome's content id, the expiry's
    status guard). Returns the task as it now stands, or None when it was not
    open.

    The task is read and checked inside that transaction (Codex re-review
    F5): a submit may consume it between a caller's look and the lock, with
    its consume-time disposition still to be written, and the one-row-per-task
    outcome index would then keep this withdrawal's label on a consumed task
    for good. Under ``BEGIN IMMEDIATE`` a consume either committed first (so
    the task is not open and nothing is written) or waits for this one (and
    its status guard leaves the expired task alone)."""

    with repository.atomic():
        task = repository.followup_task(task_id)
        if task is None or str(task.get("status") or "") not in ("pending", "served"):
            return None
        if str(task.get("kind") or "") == "cold_retry":
            from learnloop.attempts.coldness_receipt import evaluate_final_coldness, record_final_receipt
            from learnloop.diagnosis.causal_probe_coherence import record_causal_cold_outcome

            context = task.get("context")
            context = context if isinstance(context, Mapping) else {}
            recorded = record_causal_cold_outcome(
                repository,
                outcome=WITHDRAWN_COLD_RETRY_OUTCOME,
                followup_task_id=str(task["id"]),
                remediation_episode_id=str(task.get("remediation_episode_id") or "") or None,
                case_kind=str(task.get("case_kind") or "") or None,
                case_ref=str(task.get("case_ref") or "") or None,
                source_attempt_id=(
                    str(context.get("source_attempt_id") or "") or (str(task.get("source_attempt_id") or "") or None)
                ),
                repair_class_id=str(context.get("repair_class_id") or "") or None,
                hypothesis_ids=[str(value) for value in context.get("hypothesis_ids") or []],
                # The surface stopped being an independent opportunity before
                # it was administered (spec §4.3: only a genuine one
                # right-censors).
                servable_opportunity=False,
                detail={
                    "stage": stage,
                    "reason": reason,
                    "reveal_event_ids": [str(value) for value in reveal_event_ids],
                    "eligibility": dict(decision or {}),
                },
                scheduled_not_before=str(task.get("not_before") or "") or None,
                scheduled_expires_at=str(task.get("expires_at") or "") or None,
                clock=clock,
            )
            if recorded is None and repository.causal_cold_outcome_for_task(str(task["id"])) is None:
                logging.getLogger(__name__).warning(
                    "cold retry %s not withdrawn: its disposition could not be recorded", task_id,
                )
                return None
            if vault is not None:
                try:
                    record_final_receipt(
                        repository,
                        task=task,
                        evaluation=evaluate_final_coldness(
                            vault, repository, task=task, cold_attempt_id=None, clock=clock
                        ),
                        outcome=WITHDRAWN_COLD_RETRY_OUTCOME,
                        clock=clock,
                    )
                except Exception:  # pragma: no cover - receipts must not fail a serve
                    logging.getLogger(__name__).warning(
                        "coldness final receipt failed for withdrawn task %s", task_id, exc_info=True,
                    )
        repository.expire_followup_task(str(task["id"]), clock=clock)
    logging.getLogger(__name__).info(
        "cold %s task %s withdrawn: %s (%d reveal(s))", task.get("kind"), task_id, reason, len(reveal_event_ids),
    )
    return repository.followup_task(str(task["id"]))


def misconception_status_history(repository: Repository, misconception_id: str) -> list[dict[str, Any]]:
    history = []
    for event in repository.misconception_transition_events(misconception_id):
        label = event["to_status"]
        if event.get("from_status") == "resolved" and event["to_status"] in {"active", "resolving"}:
            label = "returned"
        history.append(dict(event) | {"label": label})
    return history

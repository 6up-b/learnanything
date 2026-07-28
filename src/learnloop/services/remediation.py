"""Durable misconception-repair episode lifecycle and cold retries."""

from __future__ import annotations

from datetime import UTC, timedelta
from typing import Any

from learnloop.clock import Clock, SystemClock, parse_utc
from learnloop.db.repositories import Repository
from learnloop.ingest.locators import parse_block_span
from learnloop.services.provenance import get_entity_provenance
from learnloop.services.span_view import SpanViewError, build_span_view
from learnloop.vault.models import LoadedVault


class RemediationError(ValueError):
    pass


class RemediationBlocked(RemediationError):
    """A repair that the causal state holds back, with its typed status.

    Carries the full :class:`~learnloop.services.causal_orchestrator.RepairStatus`
    so a caller can render the §6 learner copy and actions instead of a bare
    string. ``str(exc)`` is the learner-facing message.
    """

    def __init__(self, status: Any) -> None:
        super().__init__(status.message)
        self.repair_status = status

    @property
    def status(self) -> str:
        return str(self.repair_status.status)


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

    from learnloop.services.causal_orchestrator import (
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


def _episode_case(repository: Repository, episode: dict[str, Any]) -> Any | None:
    if episode.get("case_kind") == "misconception":
        return repository.misconception(str(episode["case_ref"]))
    return repository.misconception_candidate_by_id(str(episode["case_ref"]))


def _case_value(case: Any, key: str, default: Any = None) -> Any:
    if isinstance(case, dict):
        return case.get(key, default)
    return getattr(case, key, default)


def prescribe_remediation(
    vault: LoadedVault,
    repository: Repository,
    episode_id: str,
    *,
    clock: Clock | None = None,
) -> dict[str, Any]:
    episode = repository.remediation_episode(episode_id)
    if episode is None:
        raise RemediationError("remediation episode does not exist")
    misconception = _episode_case(repository, episode)
    if misconception is None:
        raise RemediationError("remediation case no longer exists")

    passages: list[dict[str, Any]] = []
    for role, facet_id in (
        ("target", _case_value(misconception, "target_facet")),
        ("confused_with", _case_value(misconception, "confused_with_facet")),
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
            try:
                view = build_span_view(
                    repository,
                    extraction_id,
                    span_id,
                    context="remediation",
                    entity_type="misconception",
                    entity_id=str(_case_value(misconception, "id", episode["case_ref"])),
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


#: An item attempted within this window is still "hot" — serving it again as the
#: primed half of a repair pair measures short-term memory of the question, not
#: the repair. Mirrors the lane's own §6.2 day boundary: the cold retry is not
#: schedulable before +1 day for exactly the same reason.
RECENT_ATTEMPT_WINDOW = timedelta(days=1)


def _item_step_checkpoint_ids(target_refs) -> tuple[str, ...]:
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
        return _item_step_checkpoint_ids((definition or {}).get("target_refs"))

    case_id = str(_case_value(misconception, "id", "") or "")
    if not case_id:
        return ()
    source_event_ids = list(
        _case_value(misconception, "source_error_event_ids", None) or []
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
        checkpoint_ids = _item_step_checkpoint_ids(
            (repair_class or {}).get("target_refs")
        )
        if checkpoint_ids:
            return checkpoint_ids
    return ()


def _item_checkpoints(item: Any) -> set[str]:
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

    from learnloop.services.instrument_serving import unservable_refusal

    target_facets = {
        vault.canonical_facet_id(facet)
        for facet in (
            _case_value(misconception, "target_facet"),
            _case_value(misconception, "confused_with_facet"),
        )
        if facet
    }
    targeted = {str(value) for value in target_checkpoint_ids if value}
    now = (clock or SystemClock()).now()
    ranked = []
    skipped: list[dict[str, Any]] = []
    for item in vault.practice_items.values():
        if item.learning_object_id != _case_value(misconception, "learning_object_id"):
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
        covers_checkpoint = bool(targeted & _item_checkpoints(item)) if targeted else False
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
    misconception = _episode_case(repository, episode)
    if misconception is None:
        raise RemediationError("remediation case no longer exists")
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
    from learnloop.services.canonical_projection import surface_group_id

    primed_surface = surface_group_id(primed)
    cold = next(
        (item for item in ranked[1:] if surface_group_id(item) != primed_surface),
        None,
    )
    updates: dict[str, Any] = {
        "state": "treatment",
        "primed_item_id": primed.id,
    }
    if cold is not None:
        updates["cold_item_id"] = cold.id
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


def _record_unbound_primed_disposition(
    repository: Repository,
    attempt: dict[str, Any],
    *,
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

    from learnloop.services.causal_probe_coherence import record_causal_cold_outcome
    from learnloop.services.guided_redo import _diagnosis_receipt, _selected_repair

    selected = _selected_repair(_diagnosis_receipt(repository, str(attempt["id"])))
    repair_class = (selected or {}).get("repair_class")
    repair_class = repair_class if isinstance(repair_class, dict) else {}
    repair_class_id = str(repair_class.get("id") or "") or None
    if repair_class_id is None:
        return
    record_causal_cold_outcome(
        repository,
        outcome="unmeasurable_no_held_out_surface",
        source_attempt_id=str(attempt["id"]),
        repair_class_id=repair_class_id,
        hypothesis_ids=[
            str(row["id"])
            for row in repository.causal_hypotheses_for_attempt(str(attempt["id"]))
            if row.get("id")
        ],
        servable_opportunity=False,
        detail={"stage": "schedule", "reason": "no_episode"},
        clock=clock,
    )


def record_remediation_attempt(
    repository: Repository,
    attempt: dict[str, Any],
    *,
    clock: Clock | None = None,
) -> None:
    """Link treatment attempts and consume delayed tasks exactly once."""

    if attempt.get("primed"):
        episode = repository.open_remediation_episode_for_primed_item(
            str(attempt["practice_item_id"])
        )
        if episode is None:
            # G6: a primed attempt that carries a diagnosed repair class but
            # found no episode (the guided redo's held/blocked arm, or any
            # primed retry taken with the repair lane closed) must not vanish —
            # nothing downstream would ever say why no cold retry exists.
            _record_unbound_primed_disposition(repository, attempt, clock=clock)
            return
        cold_item_id = str(episode.get("cold_item_id") or "")
        if not cold_item_id or cold_item_id == str(attempt["practice_item_id"]):
            # No independent surface existed when treatment picked the pair
            # (or a legacy episode reused the primed item). Scheduling would
            # only manufacture a verification the §6.2 guard rejects on
            # consume days later — record the typed §4.3 disposition now.
            from learnloop.services.causal_probe_coherence import (
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
            return
        created = parse_utc(attempt.get("created_at")) or (clock or SystemClock()).now()
        not_before = (created.astimezone(UTC) + timedelta(days=1)).replace(microsecond=0)
        expires = not_before + timedelta(days=30)
        repository.update_remediation_episode(
            episode["id"], state="cold_scheduled", primed_attempt_id=attempt["id"], clock=clock
        )
        # §6.2: resolve the cold-verification inputs NOW and carry them on the
        # task. When the retry lands days later, the factor may have closed and
        # the receipt may be stale; reconstructing them then is exactly the
        # "future caller" assumption that left this channel unwired.
        from learnloop.services.causal_orchestrator import cold_verification_context

        context = cold_verification_context(
            None, repository, episode=episode, source_attempt=attempt
        )
        # A diagnosis-kind episode whose context resolves no repair class would
        # schedule a 30-day retry doomed to land `missing_chain` at verification
        # (§4.3). New episodes can no longer be minted unmapped, but episodes
        # created before that gate — or through other entry points — still reach
        # here; record the refusal now instead of wasting the measurement.
        if str(episode.get("case_kind") or "") == "diagnosis" and not context.get(
            "repair_class_id"
        ):
            from learnloop.services.causal_probe_coherence import (
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
            return
        repository.create_followup_task(
            kind="cold_retry",
            case_kind=episode["case_kind"],
            case_ref=episode["case_ref"],
            source_attempt_id=attempt["id"],
            remediation_episode_id=episode["id"],
            not_before=not_before.isoformat().replace("+00:00", "Z"),
            expires_at=expires.isoformat().replace("+00:00", "Z"),
            selected_item_id=episode.get("cold_item_id"),
            context=context,
            clock=clock,
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


def misconception_status_history(repository: Repository, misconception_id: str) -> list[dict[str, Any]]:
    history = []
    for event in repository.misconception_transition_events(misconception_id):
        label = event["to_status"]
        if event.get("from_status") == "resolved" and event["to_status"] in {"active", "resolving"}:
            label = "returned"
        history.append(dict(event) | {"label": label})
    return history

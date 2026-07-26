"""Commission a discriminating probe instrument for a divergent factor.

This is the producer the P2 probe-administration lane never had.  Every piece
below already existed — ``lock_causal_hypothesis_set``,
``generate_blind_prediction_bundle``, ``blind_bundle_discrimination``,
``audit_manipulation_contract``, ``validate_independent_measurement_contract``,
``create_probe_candidate``, ``transition_probe_candidate`` — and **none of them
had a production caller**.  The consequence was a lane that looked complete and
was inert: ``causal_probe_candidates`` stayed empty, so
``causal_orchestrator``'s ``instrument_available`` was permanently False,
``probe_now`` always degraded to ``no_discriminating_instrument``, and
``causal_discriminating_observations`` (migration 130) could never be written.
One producer lights the whole chain.

**The blind generator runs no model by default.**  It maps each hypothesis's
typed ``target_ref`` onto the candidate item's independently authored criterion
targets.  This is intentionally *not* based on ``postdictive_claims``: causal
§5.1 says those claims are observation-conditioned and may never feed probe
discrimination.  The signature is therefore a fresh-item structural commitment
over exactly the input §7 permits (hypothesis + item + rubric + trace contract).
A model generator remains injectable for hypotheses whose typed targets cannot
be expressed in the deterministic vocabulary.

**Two failure modes are the point, not defects.**  Hypotheses that commit to the
same observables produce identical bundles and the commissioning returns
``bundles_do_not_discriminate``; hypotheses whose targets map to no criterion on
the candidate item return ``no_derivable_predictions``.  Both say
"this item cannot separate these causes" — which is the instrument-pool
bottleneck the measurement spec's Step 0 measured, stated per factor instead of
in aggregate.

**Nothing here can serve a probe.**  Commissioning ends at ``registered``; the
``registered → reviewed → active`` half of the ladder needs a reviewer, and only
an ACTIVE candidate is servable (``causal_orchestrator`` line ~1276).  A
producer that auto-activated its own instruments would defeat the register →
review → activate discipline it exists to feed.
"""

from __future__ import annotations

from typing import Any, Callable, Mapping, Sequence

from learnloop.clock import Clock
from learnloop.db.repositories import Repository
from learnloop.services.causal_probe_coherence import (
    audit_manipulation_contract,
    blind_bundle_discrimination,
    build_causal_hypothesis_set,
    candidate_has_current_blind_input_contract,
    create_probe_candidate,
    generate_blind_prediction_bundle,
    lock_causal_hypothesis_set,
    transition_probe_candidate,
)
from learnloop.vault.models import LoadedVault, PracticeItem

#: Stamped on every commissioning receipt so a stored outcome can be replayed
#: against the policy that produced it.
COMMISSIONING_POLICY_VERSION = "causal_probe_commissioning_v2"

#: How the pre-registered predictions were produced.  ``hypothesis_target_frame_v1``
#: runs no model; ``injected_generator`` means a caller supplied one, and the
#: bundle records the model revision it came from.
PREDICTION_BASES = ("hypothesis_target_frame_v1", "injected_generator")

#: Every terminal state of one commissioning attempt.  A typed outcome per
#: reason, because "no instrument" has at least six different remedies and an
#: undifferentiated failure is not a queue entry.
COMMISSIONING_OUTCOMES = (
    # A candidate now exists at `registered`, awaiting review.
    "commissioned",
    # An active candidate already serves this factor; nothing to do.
    "already_available",
    # A candidate exists and is somewhere in the review ladder.
    "already_pending_review",
    # The factor's plausible causes imply one repair class, so there is nothing
    # to discriminate. Not a failure — the probe would buy nothing.
    "not_divergent",
    # The factor is not in a state that can carry a probe at all (closed, no
    # concrete hypotheses, or no open-set arm).
    "factor_not_probeable",
    # No item exists that could serve as the instrument. Remedy: authoring.
    "no_candidate_item",
    # The hypotheses' typed targets map to no criterion the candidate item
    # measures. Remedy: author an item with a matching measurement contract.
    "no_derivable_predictions",
    # Bundles were generated but do not separate the cause set. Remedy: author a
    # manipulation that changes what the rival causes predict.
    "bundles_do_not_discriminate",
    # The structural diff or the independent review rejected the manipulation.
    "manipulation_audit_rejected",
    # Structural audit passed; the adversarial half has not run yet (§5.8 rule 2
    # / §7). The audit id is returned so a reviewer can discharge it.
    "pending_adversarial_review",
    # The candidate item's measurement targets are not independently compiled.
    "measurement_contract_rejected",
)

_ALGORITHM_VERSION = COMMISSIONING_POLICY_VERSION

BlindGenerator = Callable[[Mapping[str, Any]], Mapping[str, Any]]


# ---------------------------------------------------------------------------
# The model-free blind generator
# ---------------------------------------------------------------------------


def _criterion_ids(payload: Mapping[str, Any]) -> list[str]:
    rubric = payload.get("rubric")
    criteria = rubric.get("criteria") if isinstance(rubric, Mapping) else None
    ids: list[str] = []
    for criterion in criteria or []:
        if not isinstance(criterion, Mapping):
            continue
        criterion_id = str(
            criterion.get("id") or criterion.get("criterion_id") or ""
        ).strip()
        if criterion_id:
            ids.append(criterion_id)
    return ids


def targeted_criteria(
    hypothesis: Mapping[str, Any], rubric: Mapping[str, Any]
) -> list[str]:
    """Candidate-item criterion ids that structurally exercise a hypothesis.

    A criterion target maps directly. A facet-capability target maps only
    through authored targets on the fresh item's rubric. Item-step and
    answer-span targets are local to the old response and therefore abstain.
    There is deliberately no lexical or postdictive fallback.
    """

    target_ref = hypothesis.get("target_ref")
    target_ref = target_ref if isinstance(target_ref, Mapping) else {}
    kind = str(target_ref.get("kind") or "")
    criteria = rubric.get("criteria")
    criteria = criteria if isinstance(criteria, Sequence) else []
    observable = {
        str(criterion.get("id") or criterion.get("criterion_id") or "").strip()
        for criterion in criteria
        if isinstance(criterion, Mapping)
    }
    observable.discard("")
    if kind == "criterion":
        criterion_id = str(target_ref.get("criterion_id") or "").strip()
        return [criterion_id] if criterion_id in observable else []
    if kind != "facet_capability":
        return []
    facet_id = str(
        target_ref.get("facet_id") or target_ref.get("facet") or ""
    ).strip()
    capability = str(target_ref.get("capability") or "").strip()
    if not facet_id:
        return []
    matched: list[str] = []
    for criterion in criteria:
        if not isinstance(criterion, Mapping):
            continue
        criterion_id = str(
            criterion.get("id") or criterion.get("criterion_id") or ""
        ).strip()
        if not criterion_id:
            continue
        for target in criterion.get("targets") or []:
            if not isinstance(target, Mapping):
                continue
            target_facet = str(
                target.get("facet") or target.get("facet_id") or ""
            ).strip()
            target_capability = str(target.get("capability") or "").strip()
            if target_facet == facet_id and (
                not capability
                or not target_capability
                or target_capability == capability
            ):
                matched.append(criterion_id)
                break
    return sorted(set(matched))


def make_target_generator(
    frame_criterion_ids: Sequence[str],
) -> BlindGenerator:
    """Blind structural predictions over the rivals' fresh-item target frame.

    A hypothesis predicts failure on criteria that exercise its typed target and
    full credit on the other in-frame criteria. The latter is an added,
    reviewer-visible complement commitment; if wrong, classification falls into
    the no-match/open-set arm and never promotes a hypothesis.
    """

    frame = sorted({str(value).strip() for value in frame_criterion_ids if str(value).strip()})

    def generate(payload: Mapping[str, Any]) -> dict[str, Any]:
        hypothesis = payload.get("hypothesis")
        hypothesis = hypothesis if isinstance(hypothesis, Mapping) else {}
        rubric = payload.get("rubric")
        rubric = rubric if isinstance(rubric, Mapping) else {}
        observable = set(_criterion_ids(payload))
        targets = set(targeted_criteria(hypothesis, rubric))
        in_frame = [value for value in frame if value in observable]
        dropped = sorted(
            {value for value in targets if value not in observable}
            | {value for value in frame if value not in observable}
        )
        if not in_frame or not any(value in targets for value in in_frame):
            return {}
        values: dict[str, Any] = {}
        complement: list[str] = []
        for criterion_id in in_frame:
            if criterion_id in targets:
                values[f"criterion:{criterion_id}:passed"] = False
                values[f"criterion:{criterion_id}:full_credit"] = False
            else:
                values[f"criterion:{criterion_id}:full_credit"] = True
                complement.append(criterion_id)
        keys = sorted(values)
        return {
            "feature_rows": [
                {"keys": keys, "values": {key: values[key] for key in keys}}
            ],
            "prediction_basis": "hypothesis_target_frame_v1",
            "frame_criterion_ids": in_frame,
            "targeted_criteria": sorted(targets & observable),
            "complement_criteria": complement,
            "unobservable_criteria": dropped,
        }

    return generate


# ---------------------------------------------------------------------------
# Candidate-item resolution and the measurement contract
# ---------------------------------------------------------------------------


def _is_diagnostic_item(item: PracticeItem) -> bool:
    if str(getattr(item, "practice_mode", "") or "") == "diagnostic_probe":
        return True
    allowed = getattr(item, "attempt_types_allowed", None) or []
    return "diagnostic_probe" in {str(value) for value in allowed}


def candidate_probe_items(
    vault: LoadedVault,
    *,
    learning_object_id: str,
    exclude_item_ids: Sequence[str] = (),
) -> list[PracticeItem]:
    """Items that could serve as this factor's instrument, best first.

    Deliberately narrow: a diagnostic item for the same learning object that is
    not the item the learner just attempted.  Reusing the attempted item would
    measure the same surface again, which is the near-clone contamination class
    the P2 lane already refuses at serving time.
    """

    excluded = {str(value) for value in exclude_item_ids if value}
    items = [
        item
        for item in vault.practice_items.values()
        if str(getattr(item, "learning_object_id", "") or "") == learning_object_id
        and str(item.id) not in excluded
        and _is_diagnostic_item(item)
    ]
    return sorted(items, key=lambda item: str(item.id))


def measurement_contract_for_item(
    vault: LoadedVault, item: PracticeItem
) -> dict[str, Any]:
    """The item's OWN measurement targets, never the parent's.

    ``independently_compiled`` is a claim about provenance, and it is true by
    construction here: the contract is read off the candidate item's authored
    rubric, and no facet weight is copied from the factor's source item.  An item
    with no criteria yields a typed abstention rather than an empty contract that
    would read as "measures nothing in particular".
    """

    rubric = vault.rubric_for_item(item)
    criteria: list[dict[str, Any]] = []
    for criterion in getattr(rubric, "criteria", None) or []:
        criteria.append(
            {
                "criterion_id": str(criterion.id),
                "measurement_status": str(
                    getattr(criterion, "measurement_status", "") or "item_local"
                ),
            }
        )
    statuses = {value["measurement_status"] for value in criteria}
    return {
        "independently_compiled": True,
        "inherited_parent_facet_weights": False,
        "practice_item_id": str(item.id),
        "criteria": criteria,
        "measurement_status": (
            "abstained"
            if not criteria
            else (
                statuses.pop()
                if len(statuses) == 1
                else "composite"
            )
        ),
    }


# ---------------------------------------------------------------------------
# The commissioning pipeline
# ---------------------------------------------------------------------------


def _result(outcome: str, **extra: Any) -> dict[str, Any]:
    assert outcome in COMMISSIONING_OUTCOMES, outcome
    return {
        "outcome": outcome,
        "policy_version": COMMISSIONING_POLICY_VERSION,
        **extra,
    }


def commission_probe_instrument(
    vault: LoadedVault,
    repository: Repository,
    *,
    factor_id: str,
    candidate_practice_item_id: str | None = None,
    blind_generator: BlindGenerator | None = None,
    model_revision: str | None = None,
    outcome_schema_version: str = "deterministic_criterion_features_v1",
    adversarial_review: Mapping[str, Any] | None = None,
    generation_agent_run_id: str | None = None,
    reviewer_agent_run_id: str | None = None,
    require_adversarial: bool = True,
    clock: Clock | None = None,
) -> dict[str, Any]:
    """Commission one discriminating instrument for ``factor_id``.

    Returns a typed result; expected states are outcomes, not exceptions, because
    the caller is a sweep and "this factor cannot be instrumented yet" is the
    common case.  ``ValueError`` is reserved for a caller error (unknown factor,
    unknown item).
    """

    from learnloop.services.causal_probe_coherence import (
        repair_class_need_for_factor,
    )

    factor = repository.unresolved_cause_factor(factor_id)
    if factor is None:
        raise ValueError("unresolved-cause factor does not exist")

    existing = repository.causal_probe_candidates_for_factor(factor_id)
    # v1's nominally blind input exposed postdictive claims. Retire every
    # nonterminal candidate minted under it before considering availability;
    # the append-only candidate event records the safety withdrawal.
    for value in existing:
        if (
            value.get("status") != "rejected"
            and not candidate_has_current_blind_input_contract(value)
        ):
            transition_probe_candidate(
                repository,
                str(value["id"]),
                to_status="rejected",
                reviewer="system:blind_input_contract_v2",
                reason=(
                    "withdrawn: generated under the observation-exposed v1 "
                    "blind input contract"
                ),
                clock=clock,
            )
    existing = [
        value
        for value in repository.causal_probe_candidates_for_factor(factor_id)
        if candidate_has_current_blind_input_contract(value)
    ]
    if any(value.get("status") == "active" for value in existing):
        return _result(
            "already_available",
            candidate_ids=[
                str(value["id"]) for value in existing if value.get("status") == "active"
            ],
        )
    pending = [
        value
        for value in existing
        if value.get("status") in {"candidate", "registered", "reviewed"}
    ]
    if pending:
        return _result(
            "already_pending_review",
            candidate_ids=[str(value["id"]) for value in pending],
            statuses=sorted(str(value["status"]) for value in pending),
        )

    if str(factor.get("status") or "") != "open":
        return _result("factor_not_probeable", reason="factor_is_not_open")

    # Divergence is the whole warrant for spending anything on discrimination.
    need = repair_class_need_for_factor(repository, factor_id)
    if not need.get("repair_class_divergence"):
        return _result(
            "not_divergent",
            repair_class_ids=list(need.get("repair_class_ids") or []),
            common_repair_covers=bool(need.get("common_repair_covers")),
        )

    receipt_scores = _support_scores(repository, factor)
    try:
        plan = build_causal_hypothesis_set(
            repository, factor_id, support_scores=receipt_scores
        )
    except ValueError as error:
        # "no concrete hypotheses" / "no open-set arm" are states, not bugs.
        return _result("factor_not_probeable", reason=str(error))

    learning_object_id = plan.learning_object_id
    # The factor row (migration 034) carries only the attempt, so the source item
    # — the surface the learner just failed on, which the instrument must not
    # re-measure — comes from the attempt.
    source_attempt = (
        repository.fetch_practice_attempt(str(factor.get("attempt_id") or "")) or {}
    )
    source_item_id = str(source_attempt.get("practice_item_id") or "")

    if candidate_practice_item_id is None:
        available = candidate_probe_items(
            vault,
            learning_object_id=learning_object_id,
            exclude_item_ids=[source_item_id],
        )
        if not available:
            return _result(
                "no_candidate_item",
                learning_object_id=learning_object_id,
                excluded_item_id=source_item_id or None,
            )
        candidate_item = available[0]
    else:
        candidate_item = vault.practice_items.get(str(candidate_practice_item_id))
        if candidate_item is None:
            raise ValueError("candidate practice item does not exist")
    candidate_item_id = str(candidate_item.id)
    rubric = vault.rubric_for_item(candidate_item)
    trace_contract = getattr(candidate_item, "trace_contract", None)

    rubric_payload = (
        rubric.model_dump(mode="json", exclude_none=False)
        if hasattr(rubric, "model_dump")
        else rubric
    )
    rubric_payload = (
        rubric_payload if isinstance(rubric_payload, Mapping) else {}
    )
    # The frame is the union of fresh-item criteria structurally targeted by the
    # rivals. Observation-conditioned postdictive claims are intentionally absent.
    frame = sorted(
        {
            criterion_id
            for label in plan.hypothesis_versions
            for criterion_id in targeted_criteria(
                repository.causal_hypothesis(label) or {}, rubric_payload
            )
        }
    )
    generator = blind_generator or make_target_generator(frame)
    prediction_basis = (
        "injected_generator"
        if blind_generator is not None
        else "hypothesis_target_frame_v1"
    )
    revision = model_revision or (
        "deterministic_hypothesis_target_v1"
        if blind_generator is None
        else "unspecified"
    )
    bundle_ids: list[str] = []
    undeclarable: list[dict[str, Any]] = []
    for label in plan.hypothesis_versions:
        try:
            bundle = generate_blind_prediction_bundle(
                repository,
                hypothesis_id=label,
                item=candidate_item,
                rubric=rubric,
                trace_contract=trace_contract,
                generator=generator,
                model_revision=revision,
                outcome_schema_version=outcome_schema_version,
                generation_agent_run_id=generation_agent_run_id,
                clock=clock,
            )
        except ValueError as error:
            # A hypothesis whose typed target this item cannot observe is not a bug;
            # it is the instrument-pool gap, per hypothesis.
            undeclarable.append({"hypothesis_id": label, "reason": str(error)})
            continue
        bundle_ids.append(str(bundle["id"]))
    if len(bundle_ids) < 2:
        return _result(
            "no_derivable_predictions",
            practice_item_id=candidate_item_id,
            prediction_basis=prediction_basis,
            bundle_ids=bundle_ids,
            undeclarable=undeclarable,
        )

    discrimination = blind_bundle_discrimination(
        repository,
        hypothesis_ids=list(plan.hypothesis_versions),
        practice_item_id=candidate_item_id,
    )
    if not discrimination["distinguishable"]:
        return _result(
            "bundles_do_not_discriminate",
            practice_item_id=candidate_item_id,
            prediction_basis=prediction_basis,
            bundle_ids=bundle_ids,
            undeclarable=undeclarable,
            discrimination=discrimination,
        )

    source_item = (
        vault.practice_items.get(source_item_id) if source_item_id else None
    )
    audit = audit_manipulation_contract(
        repository,
        # With no source item to diff against, the candidate is diffed against
        # itself: every axis is unchanged, so the structural half is vacuously
        # satisfied and the adversarial half carries the whole audit. Recorded
        # explicitly rather than skipped, so the receipt says which it was.
        source_item=source_item if source_item is not None else candidate_item,
        candidate_item=candidate_item,
        source_kind="causal_probe",
        adversarial_review=adversarial_review,
        generation_agent_run_id=generation_agent_run_id,
        reviewer_agent_run_id=reviewer_agent_run_id,
        require_adversarial=require_adversarial,
        clock=clock,
    )
    audit_id = str(audit["id"])
    if str(audit["status"]) == "pending_adversarial_review":
        return _result(
            "pending_adversarial_review",
            manipulation_audit_id=audit_id,
            practice_item_id=candidate_item_id,
            bundle_ids=bundle_ids,
            structural_diff=audit.get("structural_diff"),
        )
    if str(audit["status"]) != "passed":
        return _result(
            "manipulation_audit_rejected",
            manipulation_audit_id=audit_id,
            practice_item_id=candidate_item_id,
            structural_diff=audit.get("structural_diff"),
            adversarial_review=audit.get("adversarial_review"),
        )

    hypothesis_set = lock_causal_hypothesis_set(
        repository,
        factor_id,
        probe_phase_id=None,
        algorithm_version=_ALGORITHM_VERSION,
        support_scores=receipt_scores,
        clock=clock,
    )
    contract = measurement_contract_for_item(vault, candidate_item)
    try:
        candidate = create_probe_candidate(
            repository,
            factor_id=factor_id,
            practice_item_id=candidate_item_id,
            hypothesis_set_id=str(hypothesis_set.id),
            manipulation_audit_id=audit_id,
            measurement_contract=contract,
            clock=clock,
        )
    except ValueError as error:
        message = str(error)
        if "measurement" in message:
            return _result(
                "measurement_contract_rejected",
                practice_item_id=candidate_item_id,
                reason=message,
            )
        return _result(
            "bundles_do_not_discriminate",
            practice_item_id=candidate_item_id,
            reason=message,
            bundle_ids=bundle_ids,
        )

    # Register it. Review and activation stay human (or at least separate):
    # `registered → reviewed` requires a reviewer by construction.
    registered = transition_probe_candidate(
        repository,
        str(candidate["id"]),
        to_status="registered",
        reason="commissioned by causal_probe_commissioning",
        clock=clock,
    )
    return _result(
        "commissioned",
        candidate_id=str(registered["id"]),
        status=str(registered["status"]),
        practice_item_id=candidate_item_id,
        hypothesis_set_id=str(hypothesis_set.id),
        manipulation_audit_id=audit_id,
        bundle_ids=bundle_ids,
        prediction_basis=prediction_basis,
        undeclarable=undeclarable,
        discrimination=discrimination,
        measurement_contract=contract,
    )


def _support_scores(
    repository: Repository, factor: Mapping[str, Any]
) -> dict[str, float | None]:
    """Support scores from the factor's diagnosis receipt, when it owns any.

    A single-attempt receipt owns none (``unavailable_single_attempt``), which is
    why ``build_causal_hypothesis_set`` stamps ``uniform_fallback`` — the prior
    is then an authored choice and says so.
    """

    attempt_id = str(factor.get("attempt_id") or "")
    if not attempt_id:
        return {}
    debug = repository.attempt_debug_payload(attempt_id) or {}
    attribution = debug.get("causal_attribution")
    receipt = (
        attribution.get("diagnosis_receipt")
        if isinstance(attribution, Mapping)
        else None
    )
    scores = receipt.get("support_scores") if isinstance(receipt, Mapping) else None
    if not isinstance(scores, Mapping):
        return {}
    return {
        str(key): (float(value) if isinstance(value, (int, float)) else None)
        for key, value in scores.items()
    }


def sweep_probe_commissioning(
    vault: LoadedVault,
    repository: Repository,
    *,
    learning_object_id: str,
    limit: int = 4,
    clock: Clock | None = None,
    **kwargs: Any,
) -> list[dict[str, Any]]:
    """Commission instruments for this learning object's divergent factors.

    Bounded by ``limit`` because commissioning is not free even model-free (it
    writes bundles and locks a hypothesis set per factor), and an unbounded sweep
    on a busy learning object would do that work for factors nobody will probe.
    The bound is reported by the caller rather than hidden: a factor left
    uncommissioned this pass is picked up on the next.
    """

    results: list[dict[str, Any]] = []
    for factor in repository.open_unresolved_cause_factors(
        learning_object_id=learning_object_id
    ):
        if len(results) >= max(0, limit):
            break
        result = commission_probe_instrument(
            vault,
            repository,
            factor_id=str(factor["id"]),
            clock=clock,
            **kwargs,
        )
        results.append({"factor_id": str(factor["id"]), **result})
    return results

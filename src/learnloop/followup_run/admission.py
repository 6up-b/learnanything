"""From an authored question to a pinned offer, with no human in the loop (spec §4.1, §5.1).

The review lifecycle stays and automation drives it: serving accepts only ``active``
candidates, so a machine admission receipt moves the candidate and updates its family link
and item state. These checks stay, and a failure means the question isn't served: the
structural instance gate and the never-before-seen check, the manipulation audit, the
blind prediction bundles, and exam-material protection.

**What the orchestrator keeps** (§5.1): it locks the hypothesis set, pins the prediction
bundles, classifies the answer against them, writes the discriminating-observation receipt
and starts the repair. Only ``accept_probe_offer``'s click is replaced, by the router's
decision.

**A defined presentation binding** (§4.1): generic family rows are not the causal
measurement. Bundles predict over the criterion features the deterministic sensor reads
(``deterministic_probe_features``), so a graded answer classifies with no model and no click.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
import json
from typing import Any

from learnloop.clock import Clock, utc_now_iso
from learnloop.db.repositories import Repository
from learnloop.followup_run.authoring import (
    QUESTION_MATCHES_RESERVED,
    causes_coverage,
    AuthoredProbe,
    AuthoringRejected,
    build_context,
    check_output,
    request_authored_probe,
)
from learnloop.followup_serve import identity
from learnloop.content.authoring.practice_leakage import (
    learner_visible_text,
    matching_phrases,
    reserved_payload_findings,
)

#: Who the machine admission receipt says moved the candidate.
MACHINE_REVIEWER = identity.MACHINE_REVIEWER
#: The axes only the system writes on a generated item, always incidental to the question.
SYSTEM_AXES: tuple[str, ...] = ("practice_mode", "surface_family", "measurement_targets", "trace_contract", "difficulty")
OUTCOME_SCHEMA = "deterministic_criterion_features_v1"


class AdmissionFailed(RuntimeError):
    """No question passed the checks (§6.2). ``reason`` is the typed outcome."""

    def __init__(self, reason: str, *, detail: Mapping[str, Any] | None = None) -> None:
        super().__init__(reason)
        self.reason = reason
        self.detail = dict(detail or {})


class OfferRefused(RuntimeError):
    """A hard refusal arrived at the pin (an episode conflict): nothing is served."""

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


@dataclass(frozen=True)
class AdmittedProbe:
    practice_item_id: str
    candidate_id: str
    hypothesis_set_id: str
    presentation_id: str
    episode_id: str
    bundle_ids: tuple[str, ...] = field(default_factory=tuple)
    model: str | None = None


def blind_generator(probe: AuthoredProbe) -> Any:
    """Bundles over the deterministic sensor's vocabulary, uniform across hypotheses.

    Written before the question is ever served, from the author's observation-free
    predictions: a hypothesis predicts failure on its criteria and full credit on the
    rest of the frame.
    """

    frame = sorted(criterion.id.strip() for criterion in probe.authored.criteria)

    def generate(payload: Mapping[str, Any]) -> dict[str, Any]:
        hypothesis = payload.get("hypothesis")
        hypothesis_id = str(hypothesis.get("id")) if isinstance(hypothesis, Mapping) else ""
        failing = set(probe.failing.get(hypothesis_id) or ())
        if not failing:
            return {}
        values: dict[str, Any] = {}
        for criterion_id in frame:
            passed = criterion_id not in failing
            values[f"criterion:{criterion_id}:passed"] = passed
            values[f"criterion:{criterion_id}:full_credit"] = passed
        keys = sorted(values)
        return {
            "feature_rows": [{"keys": keys, "values": {key: values[key] for key in keys}}],
            "prediction_basis": "injected_generator",
            "frame_criterion_ids": frame,
            "targeted_criteria": sorted(failing),
            "open_set_disposition": {
                "label": "other_or_unknown",
                "disposition": "excluded_no_declared_emission",
                "note": "H_OTHER predicts nothing; classification falls to the no-match arm and never promotes.",
            },
        }

    return generate


def _task_feature_axes(vault: Any, repository: Repository, factor_id: str, practice_item_id: str) -> set[str]:
    """Each task feature of the missed item or the new one is an axis of the audit's diff, and
    none is the author's to declare (``AUTHOR_AXES``). The system writes these: a new question
    doesn't inherit the missed one's task features."""

    factor = repository.unresolved_cause_factor(factor_id) or {}
    attempt = repository.fetch_practice_attempt(str(factor.get("attempt_id") or "")) or {}
    axes: set[str] = set()
    for item_id in (str(attempt.get("practice_item_id") or ""), practice_item_id):
        features = getattr(vault.practice_items.get(item_id), "task_features", None)
        if isinstance(features, Mapping):
            axes |= {str(axis) for axis in features}
    return axes


def manipulation_contract(probe: AuthoredProbe, *, system_axes: Iterable[str] = ()) -> dict[str, Any]:
    authored = probe.authored
    return {
        "intended_manipulations": [
            {"axis": entry.axis, "rationale": entry.rationale} for entry in authored.intended_manipulations
        ],
        "incidental_changes": sorted({*authored.incidental_changes, *SYSTEM_AXES, *system_axes}),
        "held_constant": sorted(set(authored.held_constant)),
    }


def _template_and_card(vault: Any, repository: Repository, learning_object_id: str, clock: Clock | None) -> tuple[Any, Any]:
    from learnloop.diagnosis.probe_families import DIALOGUE_MICROPROBE_V1
    from learnloop.diagnosis.probe_instance_generation import applicable_families, ensure_instrument_card

    learning_object = vault.learning_objects[learning_object_id]
    for template in applicable_families(vault, learning_object, repository):
        if template.id == DIALOGUE_MICROPROBE_V1.id:
            continue
        resolved = ensure_instrument_card(vault, repository, learning_object_id, template, clock=clock)
        if resolved is not None:
            return resolved[1], resolved[0]
    raise AdmissionFailed("no_family_binding")


def _restore_open_set_arm(repository: Repository, factor: Mapping[str, Any]) -> None:
    """A factor written before the tag lost its ``H_OTHER`` arm when its episode was materialized
    a second time; every open factor on the owner's copies has. It gets the arm back here."""

    from learnloop.diagnosis.causal_attribution import with_open_set_arm

    causes = [value for value in factor.get("candidate_causes") or [] if isinstance(value, Mapping)]
    refs = [
        {"hypothesis_id": value["hypothesis_id"], "version": value.get("version"),
         **({"open_set": True} if value.get("open_set") else {})}
        for value in causes if value.get("hypothesis_id")
    ]
    restored = with_open_set_arm(refs)
    if restored != refs:
        repository.set_unresolved_cause_hypothesis_refs(str(factor["id"]), restored)


def author_probe(
    vault: Any,
    repository: Repository,
    *,
    workflow: Mapping[str, Any],
    factor_id: str,
    decision: Mapping[str, Any],
    client: Any,
    avoid_phrases: Sequence[str] = (),
) -> tuple[AuthoredProbe, Any, Any]:
    """The one authoring call for this workflow, and its output checks."""

    from learnloop.diagnosis.causal_probe_coherence import build_causal_hypothesis_set
    from learnloop.diagnosis.causal_probe_commissioning import support_scores
    from learnloop.diagnosis.probe_instance_generation import family_measurement_intent

    factor = repository.unresolved_cause_factor(factor_id)
    if factor is None or factor.get("status") != "open":
        raise AdmissionFailed("factor_not_open")
    _restore_open_set_arm(repository, factor)
    try:
        plan = build_causal_hypothesis_set(repository, factor_id, support_scores=support_scores(repository, factor))
    except ValueError as error:
        raise AdmissionFailed("factor_not_probeable", detail={"reason": str(error)}) from error
    learning_object_id = str(workflow["learning_object_id"])
    template, card = _template_and_card(vault, repository, learning_object_id, None)
    attempt = repository.fetch_practice_attempt(str(workflow["source_attempt_id"])) or {}
    hypotheses = [
        hypothesis for label in plan.hypothesis_versions
        if (hypothesis := repository.causal_hypothesis(str(label))) is not None
    ]
    try:
        context, refs = build_context(
            vault, repository, learning_object_id=learning_object_id, hypotheses=hypotheses,
            router_decision=decision, target_facets=[str(value) for value in card.target_facets],
            source_item_id=str(attempt.get("practice_item_id") or "") or None,
            measurement_pattern=family_measurement_intent(template.id), avoid_phrases=avoid_phrases,
        )
        authored = request_authored_probe(client, context)
        probe = check_output(vault, repository, authored, refs=refs, learning_object_id=learning_object_id)
    except AuthoringRejected as rejected:
        raise AdmissionFailed(str(rejected)) from rejected
    return probe, template, card


def _reserved(vault: Any, repository: Repository) -> Any:
    from learnloop.followup_run.authoring import AuthoringRejected, reserved_view

    try:
        return reserved_view(vault, repository)
    except AuthoringRejected as rejected:
        raise AdmissionFailed(str(rejected)) from rejected


def persist_item(
    vault: Any,
    repository: Repository,
    probe: AuthoredProbe,
    *,
    template: Any,
    card: Any,
    workflow_id: str | None,
    episode_id: str | None = None,
    source: str = "workflow",
    client: Any = None,
    clock: Clock | None = None,
) -> str:
    """The mint's persistence and single-use handling, reused (§4.1). Inactive until admitted."""

    from learnloop.diagnosis.probe_episodes import administered_surface_exclusions
    from learnloop.diagnosis.probe_instance_generation import (
        LLM_GENERATOR_ID,
        LLM_GENERATOR_VERSION,
        generated_instance_payload,
        instance_gate_errors,
    )
    from learnloop.diagnosis.ai_contracts import FOLLOWUP_PROBE_PROMPT_VERSION
    from learnloop.vault.writer import upsert_practice_item

    learning_object = vault.learning_objects[str(card.learning_object_id)]
    authored = probe.authored
    now = utc_now_iso(clock)
    payload = generated_instance_payload(
        learning_object, card, template, prompt=authored.prompt_md.strip(),
        expected_answer=authored.expected_answer_md.strip(), surface_suffix=authored.surface_suffix,
        surface_prefix="followup", now=now,
    )
    total = sum(criterion.points for criterion in authored.criteria)
    payload = {
        **payload,
        # The mode is what carries the freshness rules downstream; the identity below is
        # what makes it single use at every door.
        "practice_mode": "diagnostic_probe",
        "attempt_types_allowed": ["diagnostic_probe", "dont_know"],
        "grading_rubric": {
            **payload["grading_rubric"],
            "max_points": total,
            "criteria": [
                {"id": criterion.id.strip(), "points": criterion.points, "description": criterion.description.strip()}
                for criterion in authored.criteria
            ],
        },
    }
    # First, since the structural gate would also call an exact echo a duplicate: a reserved
    # question's echo is §8's to refuse, nothing has been written, and the miss takes the practice lane.
    findings = reserved_payload_findings(payload, _reserved(vault, repository))
    if findings:
        raise AdmissionFailed(QUESTION_MATCHES_RESERVED,
                              detail={"phrases": matching_phrases(learner_visible_text(payload), findings)})
    errors = instance_gate_errors(vault, payload, card, template)
    if errors:
        raise AdmissionFailed("instance_gate", detail={"errors": errors})
    attempted_ids, attempted_surfaces = administered_surface_exclusions(vault, repository)
    if payload["id"] in attempted_ids or payload["surface_family"] in attempted_surfaces:
        raise AdmissionFailed("seen_before")
    # The identity, and the family link whose pending review parks the item from state sync,
    # commit before the file exists. A crash after it leaves a question no door serves: the
    # retry withdraws it (``identity.retire_unbound``), or it stays parked. Never the reverse:
    # a file with neither would sync as an active ordinary item.
    with repository.atomic():
        repository.link_probe_item_family(
            practice_item_id=payload["id"],
            instrument_card_id=card.id,
            instrument_card_version=card.version,
            generator_id=LLM_GENERATOR_ID,
            generator_version=LLM_GENERATOR_VERSION,
            generation_seed=workflow_id or episode_id or payload["id"],
            instance_metadata={
                "review_status": "pending_review",
                "surface_family": payload["surface_family"],
                "single_use_probe_mint": True,
                "generated_by": "followup_probe_authoring",
                "generator_model": getattr(client, "model", None),
                "prompt_version": FOLLOWUP_PROBE_PROMPT_VERSION,
                **({"followup_workflow_id": workflow_id} if workflow_id else {}),
            },
            clock=clock,
        )
        identity.register(
            repository, practice_item_id=payload["id"], revision=identity.item_revision(payload), source=source,
            workflow_id=workflow_id, probe_episode_id=episode_id, clock=clock,
        )
    upsert_practice_item(vault.root, payload, clock=clock)
    repository.upsert_practice_item_state(payload["id"], active=False, clock=clock)
    return str(payload["id"])


def admit(repository: Repository, *, candidate_id: str, receipt: Mapping[str, Any], clock: Clock | None = None) -> None:
    """The machine admission receipt: the ladder, walked by what actually checked it."""

    from learnloop.diagnosis.causal_probe_coherence import transition_probe_candidate

    reason = json.dumps(dict(receipt), sort_keys=True)
    transition_probe_candidate(repository, candidate_id, to_status="reviewed", reviewer=MACHINE_REVIEWER, reason=reason,
                               clock=clock)
    transition_probe_candidate(repository, candidate_id, to_status="active", reviewer=MACHINE_REVIEWER, reason=reason,
                               clock=clock)


def commission_only(
    vault: Any,
    repository: Repository,
    probe: AuthoredProbe,
    *,
    factor_id: str,
    practice_item_id: str,
    client: Any = None,
    clock: Clock | None = None,
) -> str:
    """An entry or a failed lane's later generation: an active candidate, pinned by no
    one yet. The offer's *Take the quick check* or a later block serves it (§5.1)."""

    from learnloop.diagnosis.causal_probe_commissioning import commission_probe_instrument

    result = commission_probe_instrument(
        vault, repository, factor_id=factor_id, candidate_practice_item_id=practice_item_id,
        blind_generator=blind_generator(probe), model_revision=str(getattr(client, "model", None) or "followup_probe_author"),
        outcome_schema_version=OUTCOME_SCHEMA, require_adversarial=False, require_divergence=False,
        manipulation_contract=manipulation_contract(
            probe, system_axes=_task_feature_axes(vault, repository, factor_id, practice_item_id),
        ),
        clock=clock,
    )
    if result["outcome"] != "commissioned":
        raise AdmissionFailed(str(result["outcome"]))
    admit(
        repository, candidate_id=str(result["candidate_id"]),
        receipt={"instance_gate": "passed", "never_before_seen": "passed", "reserved_check": "passed",
                 "causes_record": causes_coverage(vault, repository, tuple(probe.refs.values())),
                 "manipulation_audit_id": result.get("manipulation_audit_id"), "bundle_ids": result.get("bundle_ids"),
                 "adversarial_review": "not_run"},
        clock=clock,
    )
    return str(result["candidate_id"])


def commission_and_pin(
    vault: Any,
    repository: Repository,
    probe: AuthoredProbe,
    *,
    workflow: Mapping[str, Any],
    factor_id: str,
    decision_id: str | None,
    practice_item_id: str,
    client: Any = None,
    clock: Clock | None = None,
) -> AdmittedProbe:
    """Commissioning of the explicit item, machine admission, and the pinned offer."""

    from learnloop.diagnosis.causal_orchestrator import accept_probe_offer
    from learnloop.diagnosis.causal_probe_commissioning import commission_probe_instrument

    model = getattr(client, "model", None)
    result = commission_probe_instrument(
        vault, repository, factor_id=factor_id, candidate_practice_item_id=practice_item_id,
        blind_generator=blind_generator(probe), model_revision=str(model or "followup_probe_author"),
        outcome_schema_version=OUTCOME_SCHEMA, require_adversarial=False, require_divergence=False,
        manipulation_contract=manipulation_contract(
            probe, system_axes=_task_feature_axes(vault, repository, factor_id, practice_item_id),
        ),
        clock=clock,
    )
    if result["outcome"] != "commissioned":
        raise AdmissionFailed(str(result["outcome"]), detail={"commissioning": result["outcome"]})
    candidate_id = str(result["candidate_id"])
    admit(
        repository, candidate_id=candidate_id,
        receipt={
            "instance_gate": "passed", "never_before_seen": "passed", "reserved_check": "passed",
            "causes_record": causes_coverage(vault, repository, tuple(probe.refs.values())),
            "manipulation_audit_id": result.get("manipulation_audit_id"),
            "bundle_ids": result.get("bundle_ids"), "discrimination": result.get("discrimination"),
            "adversarial_review": "not_run",
        },
        clock=clock,
    )
    offer = accept_probe_offer(
        vault, repository, factor_id=factor_id, decision_receipt_id=decision_id,
        session_id=workflow.get("session_id"), clock=clock, candidate_id=candidate_id,
        followup_workflow_id=str(workflow["id"]),
    )
    if not offer.accepted:
        raise OfferRefused(str(offer.reason))
    return AdmittedProbe(
        practice_item_id=practice_item_id, candidate_id=candidate_id,
        hypothesis_set_id=str(offer.hypothesis_set_id), presentation_id=str(offer.presentation_id),
        episode_id=str(offer.episode_id), bundle_ids=tuple(offer.blind_bundle_ids), model=model,
    )


__all__ = [
    "AdmissionFailed", "AdmittedProbe", "MACHINE_REVIEWER", "OfferRefused", "admit", "author_probe",
    "blind_generator", "commission_and_pin", "commission_only", "manipulation_contract", "persist_item",
]

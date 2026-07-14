"""Parameterized instance generation from admitted family/card bindings (§10).

The durable unit of probe quality is the versioned family/card binding, not
the generated instance (§9.1): this module resolves an admitted binding for a
pending episode target, mints one to three surface-varied Item Instances from
the family's parametric surface templates, runs the instance-level structural
gates, and persists full generator provenance through
``probe_item_family_links``.

Trust policy (§10): instances from a ``trusted`` family version are
auto-admitted provisionally after the structural gates (active immediately,
`review_status="auto_admitted_provisional"`); instances from a ``provisional``
family are written but parked behind review (`review_status="pending_review"`,
item state inactive) — review throughput never blocks ordinary practice, only
episode advancement waits.
"""

from __future__ import annotations

import hashlib
import random
import re
from dataclasses import dataclass, field
from typing import Any, Mapping

from learnloop.clock import Clock, utc_now_iso
from learnloop.db.repositories import ProbeGenerationNeedRecord, Repository
from learnloop.services.facet_state_reader import is_canonical_state_vault
from learnloop.services.probe_families import (
    CONTRAST_CONFUSABLE_V1,
    DEFAULT_INSTRUCTIONAL_ACTIONS,
    DERIVATION_V1,
    DIALOGUE_MICROPROBE_V1,
    EXTENDED_CASE_V1,
    FAMILY_DEFAULT_ROWS,
    LONGFORM_FAMILY_IDS,
    LONGFORM_OBLIGATIONS,
    MINIMAL_COUNTEREXAMPLE_V1,
    MINIMAL_RECALL_V1,
    PERTURBATION_V1,
    PREDICTION_V1,
    PROOF_SKELETON_V1,
    InstrumentCard,
    ProbeFamilyTemplate,
    ensure_builtin_families,
    knowledge_type_tokens,
    validate_and_compile_card,
)
from learnloop.vault.loader import load_vault
from learnloop.vault.models import LearningObject, LoadedVault
from learnloop.vault.writer import upsert_practice_item

GENERATOR_ID = "probe_family_parametric"
GENERATOR_VERSION = "1"

# LLM-backed surface generator (§9.2/§9.4): the family/card still owns the
# measurement pattern, rubric, and signature fatal errors; the LLM supplies
# only surface wording, validated by the same structural instance gate.
# Calibration pools per (family version, generator version), so LLM instances
# never contaminate the parametric generator's posterior (§9.7).
LLM_GENERATOR_ID = "probe_family_llm"
LLM_GENERATOR_VERSION = "1"

# Signature outcome class -> the rubric fatal-error / error-type ids whose
# firing identifies it. The generated rubric declares fatal errors with these
# ids, so grader attributions and the deterministic matcher agree by
# construction.
SIGNATURE_FATAL_ERRORS: dict[str, dict[str, str]] = {
    "confusable_signature": {
        "id": "confusable_signature",
        "description": "Answer is consistent with the confusable neighbor concept, not the target.",
    },
    "surface_bound_error": {
        "id": "surface_bound_error",
        "description": "Answer reproduces the familiar surface and breaks on the shifted surface.",
    },
    "overgeneralization_signature": {
        "id": "overgeneralization_signature",
        "description": "Answer applies the schema beyond its boundary instead of locating the failure case.",
    },
    "incorrect_prediction": {
        "id": "incorrect_prediction",
        "description": "Committed prediction contradicts what the mechanism actually implies.",
    },
    "wrong_strategy_selected": {
        "id": "wrong_strategy_selected",
        "description": "A viable derivation is executed under a strategy that cannot reach the target result.",
    },
    "surface_match_error": {
        "id": "surface_match_error",
        "description": "The response pattern-matches a familiar surface instead of integrating the case's actual constraints.",
    },
}


class InstanceGateRejection(ValueError):
    """A generated instance failed the structural/grounding/conformance gate."""


@dataclass(frozen=True)
class GeneratedInstance:
    practice_item_id: str
    instrument_card_id: str
    instrument_card_version: int
    family_template_id: str
    family_template_version: int
    surface_family: str
    review_status: str  # auto_admitted_provisional | pending_review
    generation_seed: str
    generator_id: str = GENERATOR_ID


@dataclass
class GenerationSummary:
    episode_id: str
    learning_object_id: str
    generated: list[GeneratedInstance] = field(default_factory=list)
    resolved_need_ids: list[str] = field(default_factory=list)
    episode_unparked: bool = False
    family_authoring_needed: bool = False

    def as_dict(self) -> dict[str, Any]:
        return {
            "episode_id": self.episode_id,
            "learning_object_id": self.learning_object_id,
            "generated": [
                {
                    "practice_item_id": instance.practice_item_id,
                    "instrument_card_id": instance.instrument_card_id,
                    "instrument_card_version": instance.instrument_card_version,
                    "family_template_id": instance.family_template_id,
                    "family_template_version": instance.family_template_version,
                    "surface_family": instance.surface_family,
                    "review_status": instance.review_status,
                    "generator_id": instance.generator_id,
                }
                for instance in self.generated
            ],
            "resolved_need_ids": list(self.resolved_need_ids),
            "episode_unparked": self.episode_unparked,
            "family_authoring_needed": self.family_authoring_needed,
        }


# --- Family/card resolution (§10 step 3) -------------------------------------------


def applicable_families(
    vault: LoadedVault,
    learning_object: LearningObject,
    repository: Repository | None = None,
) -> list[ProbeFamilyTemplate]:
    """Families whose bindings this LO can fill, best-first (§9.5 coverage:
    one direct/minimal instrument plus one contrast/perturbation instrument).

    KM4 §10.2: a compositional misconception record (target/confused facet pair)
    is an additional source of a contrast binding, so the contrast family is
    applicable even when the LO has no confusable-concept metadata.
    """

    knowledge_type = (learning_object.knowledge_type or "").lower()
    tokens = knowledge_type_tokens(knowledge_type)
    has_confusable = bool(_confusable_for(vault, learning_object)) or (
        repository is not None
        and compositional_contrast_binding(vault, repository, learning_object.id) is not None
    )
    ordered: list[ProbeFamilyTemplate] = [MINIMAL_RECALL_V1]
    if has_confusable:
        ordered.append(CONTRAST_CONFUSABLE_V1)
    ordered.append(PERTURBATION_V1)
    if tokens & {"concept", "conceptual", "principle", "procedure", "procedural"}:
        ordered.append(PREDICTION_V1)
        ordered.append(MINIMAL_COUNTEREXAMPLE_V1)
    # §9.5/§7.5: an integrative long-form family MUST be available when the
    # knowledge type requires planning, dependency management, proof standards,
    # or procedure selection — microprobes cannot observe those targets.
    if tokens & {"procedure", "procedural", "skill"}:
        ordered.append(DERIVATION_V1)
    if tokens & {"proof", "derivation", "theorem"}:
        ordered.append(PROOF_SKELETON_V1)
        ordered.append(DERIVATION_V1)
    if tokens & {"case", "application"}:
        ordered.append(EXTENDED_CASE_V1)
    seen: set[str] = set()
    ordered = [t for t in ordered if not (t.id in seen or seen.add(t.id))]
    return [
        template
        for template in ordered
        if not template.applicable_knowledge_types
        or tokens & set(template.applicable_knowledge_types)
        or not knowledge_type
    ]


def compositional_contrast_binding(
    vault: LoadedVault,
    repository: Repository,
    learning_object_id: str,
) -> tuple[str, str] | None:
    """The (target_facet, confused_with_facet) pair of an active compositional
    misconception on this LO, if any (knowledge-model §10.2).

    KM4 lets contrast/dialogue probe generation bind the two facets directly from
    a compositional record, rather than only from LO confusable metadata. Only
    canonical (mvp-0.7) vaults carry compositional records; mvp-0.6 returns None
    so the legacy confusable-concept binding path is unchanged.
    """

    if not is_canonical_state_vault(vault):
        return None
    for row in repository.misconceptions_for_learning_object(
        learning_object_id, statuses=("active", "resolving")
    ):
        target = getattr(row, "target_facet", None)
        confused = getattr(row, "confused_with_facet", None)
        if target and confused:
            return (
                vault.canonical_facet_id(target),
                vault.canonical_facet_id(confused),
            )
    return None


def _confusable_for(vault: LoadedVault, learning_object: LearningObject) -> str | None:
    if learning_object.confusables:
        return sorted(learning_object.confusables)[0]
    for edge in sorted(vault.edges, key=lambda entry: (entry.source, entry.target)):
        if edge.relation_type != "confusable_with":
            continue
        if edge.source == learning_object.concept:
            return edge.target
        if edge.target == learning_object.concept:
            return edge.source
    return None


def _target_facet_for(vault: LoadedVault, learning_object: LearningObject) -> str:
    """The LO's most evidence-weighted facet across its items (deterministic)."""

    totals: dict[str, float] = {}
    for item in vault.practice_items.values():
        if item.learning_object_id != learning_object.id:
            continue
        if item.evidence_weights:
            for facet, weight in item.evidence_weights.items():
                totals[str(facet)] = totals.get(str(facet), 0.0) + float(weight)
        else:
            for facet in item.evidence_facets:
                totals[str(facet)] = totals.get(str(facet), 0.0) + 1.0
    if totals:
        return max(sorted(totals), key=lambda facet: totals[facet])
    return "recall"


def _misconception_error_types(vault: LoadedVault) -> list[str]:
    """Error-type ids whose firing marks a confusable/misconception signature.

    KM4 §10.1: under mvp-0.7 the grader emits the mechanism taxonomy, so the
    confusable-signature fatal set must include the misconception mechanisms
    (e.g. ``conceptual_schema_error``) for the deterministic matcher to keep
    firing that signature. The rubric fatal id / signature-name invariant is
    unaffected: the signature outcome's own fatal id (``confusable_signature``)
    is still declared and is what identifies it; the mechanisms are additional
    fired ids. mvp-0.6 is unchanged.
    """

    ids = {
        error_type_id
        for error_type_id, taxonomy in vault.error_types.items()
        if getattr(taxonomy, "is_misconception", False)
    }
    if is_canonical_state_vault(vault):
        from learnloop.services.error_taxonomy_map import MECHANISM_IS_MISCONCEPTION

        ids.update(
            mechanism
            for mechanism, is_misconception in MECHANISM_IS_MISCONCEPTION.items()
            if is_misconception
        )
    return sorted(ids)


def ensure_instrument_card(
    vault: LoadedVault,
    repository: Repository,
    learning_object_id: str,
    template: ProbeFamilyTemplate,
    *,
    clock: Clock | None = None,
) -> tuple[InstrumentCard, ProbeFamilyTemplate] | None:
    """Resolve or mint the LO-bound card for one family template (§9.3).

    Returns None when the LO cannot fill the family's bindings (for example a
    contrast family with no confusable neighbor) — the caller must fall back to
    another family or file a family-authoring need instead of fabricating an
    unmodeled instrument (§10).
    """

    ensure_builtin_families(repository, clock=clock)
    learning_object = vault.learning_objects.get(learning_object_id)
    if learning_object is None:
        return None

    for record in repository.probe_instrument_cards_for_learning_object(learning_object_id):
        if record.probe_family_template_id != template.id:
            continue
        family_record = repository.probe_family_template(
            record.probe_family_template_id, record.probe_family_template_version
        )
        if family_record is None or family_record.status not in ("provisional", "trusted"):
            continue
        return (
            InstrumentCard.from_dict(record.card),
            ProbeFamilyTemplate.from_dict(family_record.template),
        )

    confusable = _confusable_for(vault, learning_object)
    # KM4 §10.2: a compositional misconception record binds the (target, confused)
    # facet pair directly, so a contrast/dialogue instrument can be minted from it
    # even when the LO has no confusable-concept metadata.
    compositional = compositional_contrast_binding(vault, repository, learning_object_id)
    hypotheses = list(template.hypothesis_slots)
    if confusable is None and compositional is None:
        if template.instrument_kind == "contrast":
            # A contrast instrument without a confusable neighbor or a
            # compositional facet pair has no measurement target — the caller
            # must pick another family.
            return None
        # Families with an optional neighbor slot (dialogue) bind without it.
        hypotheses = [slot for slot in hypotheses if slot != "confuses_with_neighbor"]
    if compositional is not None:
        target_facet, confused_with_facet = compositional
    else:
        target_facet = _target_facet_for(vault, learning_object)
        confused_with_facet = None
    rows = FAMILY_DEFAULT_ROWS.get(template.id)
    if rows is None:
        return None

    signature_error_types: dict[str, list[str]] = {}
    for outcome in template.observation_alphabet:
        if outcome not in SIGNATURE_FATAL_ERRORS:
            continue
        fired: list[str] = [outcome]
        if outcome == "confusable_signature":
            fired.extend(_misconception_error_types(vault))
        signature_error_types[outcome] = fired

    bindings: dict[str, Any] = {"target_facet": target_facet}
    if confused_with_facet is not None:
        bindings["confused_with_facet"] = confused_with_facet
    # Surface templates render {confusable}: prefer LO confusable-concept
    # metadata, else the compositional record's confused facet is the contrast.
    contrast_confusable = confusable if confusable is not None else confused_with_facet
    if template.contrast_slots and contrast_confusable is not None:
        bindings["confusable_concept"] = contrast_confusable
    if template.id in LONGFORM_OBLIGATIONS:
        # §8.2: the card declares the ordered obligations the structured trace
        # assesses; each maps onto one rubric criterion of generated instances.
        bindings["obligations"] = [dict(entry) for entry in LONGFORM_OBLIGATIONS[template.id]]

    card = InstrumentCard(
        id=f"card_{template.id}_{learning_object_id}",
        version=1,
        family_template_id=template.id,
        family_template_version=template.version,
        learning_object_id=learning_object_id,
        target_decision=f"select_next_intervention_for_{learning_object_id}",
        bindings=bindings,
        hypotheses=tuple(hypotheses),
        conditional_observations={
            slot: dict(row) for slot, row in rows.items() if slot in hypotheses
        },
        expected_seconds=template.expected_seconds_median,
        instructional_actions={
            slot: DEFAULT_INSTRUCTIONAL_ACTIONS.get(slot, "diagnostic_followup")
            for slot in hypotheses
        },
        target_facets=(
            (target_facet, confused_with_facet)
            if confused_with_facet is not None
            else (target_facet,)
        ),
        signature_error_types=signature_error_types,
    )
    instrument = validate_and_compile_card(card, template)
    repository.insert_probe_instrument_card(
        card_id=card.id,
        version=card.version,
        probe_family_template_id=template.id,
        probe_family_template_version=template.version,
        learning_object_id=learning_object_id,
        hypothesis_scope=list(card.hypotheses),
        card=card.as_dict(),
        compiled_likelihood_hash=instrument.compiled_likelihood_hash(),
        clock=clock,
    )
    return card, template


# --- Parametric surfaces (§9.2 generator, Checkpoint 3.4) ----------------------------

_SURFACE_TEMPLATES: dict[str, list[tuple[str, str]]] = {
    # (surface_family_suffix, prompt template). Slots: {title}, {concept},
    # {facet}, {confusable}, {summary}.
    "minimal_recall": [
        (
            "direct_definition",
            "In one or two sentences and without looking anything up: state the key idea of "
            "{title}. What exactly is {facet} here?",
        ),
        (
            "own_words_recall",
            "Explain {title} in your own words, as if reminding yourself before an exam. "
            "Focus on {facet}.",
        ),
        (
            "core_claim",
            "What is the single core claim of {title}? State it precisely.",
        ),
    ],
    "prediction_before_computation": [
        (
            "predict_outcome",
            "Before doing any computation: predict what happens when {title} is applied in a "
            "typical case, and state the decisive reason for your prediction.",
        ),
        (
            "predict_change",
            "Suppose one input or assumption of {title} is made larger or stronger. Predict how "
            "the outcome changes and give the decisive reason — no computation.",
        ),
        (
            "predict_failure",
            "Predict, before checking: in which direction would the result of {title} move if "
            "{facet} were violated? State your reason.",
        ),
    ],
    "perturbation": [
        (
            "shifted_surface",
            "Here is a shifted version of the usual setting for {title}: the familiar framing is "
            "changed, but the underlying idea may still apply. Does {facet} still hold in the "
            "shifted setting? Answer and explain the decisive reason.",
        ),
        (
            "new_notation",
            "Restate and apply the key idea of {title} using different notation or a different "
            "representation than the one you practiced with. Does the conclusion survive the "
            "change of surface? Why?",
        ),
        (
            "reversed_direction",
            "Take the usual statement of {title} and approach it from the opposite direction "
            "(conclusion first). Does {facet} still justify the step? Explain.",
        ),
    ],
    "minimal_counterexample": [
        (
            "boundary_case",
            "Give a minimal counterexample or boundary condition where {title} fails or no longer "
            "applies, and say precisely why it fails there.",
        ),
        (
            "necessary_assumption",
            "Which assumption of {title} is doing the real work? Give the smallest change that "
            "breaks the conclusion and explain why.",
        ),
        (
            "does_not_apply",
            "Describe a nearby-looking situation where {title} does NOT apply. What is the "
            "decisive difference?",
        ),
    ],
    "contrast_confusable": [
        (
            "target_vs_confusable",
            "Contrast {concept} with {confusable}: for {facet}, which of the two applies, and "
            "what is the decisive difference between them?",
        ),
        (
            "spot_the_swap",
            "A classmate's answer quietly uses {confusable} where {concept} is required. For "
            "{facet}, explain what gives the swap away.",
        ),
        (
            "choose_and_justify",
            "You must pick exactly one of {concept} or {confusable} to explain {facet}. Which one, "
            "and what is the single decisive reason?",
        ),
    ],
    "proof_skeleton": [
        (
            "skeleton_outline",
            "Without filling in every detail, write the skeleton of a proof for the central claim "
            "of {title}: (1) state precisely what is to be shown, (2) list the key steps in order, "
            "(3) for each step name the fact or rule that justifies it, and (4) state how the "
            "conclusion follows.",
        ),
        (
            "skeleton_from_assumptions",
            "Starting only from the assumptions of {title}, outline a complete argument for its "
            "conclusion: state the claim, choose a proof structure, order the intermediate claims, "
            "and justify each dependency explicitly.",
        ),
    ],
    "derivation": [
        (
            "derive_with_strategy",
            "Derive the main result of {title} end to end. First name the strategy you are "
            "choosing and why it can reach the result, then set up from the givens, carry out the "
            "intermediate steps, and state the final result.",
        ),
        (
            "derive_alternative_route",
            "Work out the result of {title} from first principles. Before computing anything, "
            "commit to the method you will use; then execute it step by step, keeping each "
            "inference explicit, and finish with the result.",
        ),
    ],
    "extended_case": [
        (
            "rich_case",
            "Here is an extended case for {title}: a realistic scenario where {facet} interacts "
            "with several competing constraints. Identify which principle actually governs the "
            "case, apply it to the specific facts (not a remembered template), and integrate the "
            "constraints and edge conditions into a defensible conclusion.",
        ),
        (
            "case_with_distractor",
            "Consider a case that superficially resembles the textbook setting of {title} but "
            "differs in a load-bearing detail. Determine whether {facet} still applies, work the "
            "case through end to end, and justify how the differing detail changes (or does not "
            "change) the outcome.",
        ),
    ],
    "dialogue_microprobe": [
        (
            "dialogue_commit",
            "Commit to an answer: for {title}, what does {facet} say happens? One sentence, no "
            "hedging.",
        ),
        (
            "dialogue_reason",
            "State the decisive reason behind your last answer about {title}. What fact makes it "
            "true?",
        ),
        (
            "dialogue_counterfactual",
            "Minimally change the situation: if {facet} were altered slightly, would your answer "
            "about {title} still hold? Answer and say why.",
        ),
        (
            "dialogue_counterexample",
            "Give one boundary condition or failure case for your answer about {title}.",
        ),
    ],
}


# §8.2: one rubric criterion per declared obligation, so criterion-level
# grading evidence localizes the first invalid step deterministically.
_LONGFORM_CRITERIA: dict[str, list[tuple[str, int, str]]] = {
    PROOF_SKELETON_V1.id: [
        ("claim_statement", 1, "States precisely what is to be shown."),
        ("skeleton_structure", 1, "Chooses a viable proof structure with the key steps in a workable order."),
        ("step_justification", 1, "Each step names the fact or rule that justifies it."),
        ("conclusion", 1, "The conclusion follows from the assembled steps."),
    ],
    DERIVATION_V1.id: [
        ("strategy_selection", 1, "Selects and names a strategy that can reach the target result."),
        ("setup", 1, "Sets the derivation up correctly from the givens."),
        ("execution", 1, "Executes the intermediate steps without invalid inferences."),
        ("result", 1, "Arrives at the correct result and states it clearly."),
    ],
    EXTENDED_CASE_V1.id: [
        ("identify_principle", 2, "Identifies which principle or procedure the case actually calls for."),
        ("apply_to_case", 1, "Applies it to the case's specific facts rather than a remembered template."),
        ("integrate_constraints", 1, "Integrates the case's constraints and edge conditions into the conclusion."),
    ],
}


def parametric_instance_payloads(
    vault: LoadedVault,
    card: InstrumentCard,
    template: ProbeFamilyTemplate,
    *,
    count: int,
    seed: int,
    clock: Clock | None = None,
    surface_offset: int = 0,
) -> list[dict[str, Any]]:
    """Deterministic surface-varied Item Instance payloads for one binding.

    Surfaces are drawn without replacement from the family's parametric
    templates in a seeded order, so the same (card, seed) always yields the
    same instances and re-generation cannot silently duplicate a surface.
    """

    learning_object = vault.learning_objects[card.learning_object_id]
    surfaces = list(_SURFACE_TEMPLATES.get(template.id, ()))
    if not surfaces:
        return []
    rng = random.Random(f"{GENERATOR_ID}:{GENERATOR_VERSION}:{card.id}:{seed}")
    rng.shuffle(surfaces)
    if surface_offset:
        surfaces = surfaces[surface_offset:] + surfaces[:surface_offset]
    now = utc_now_iso(clock)
    slots = {
        "title": learning_object.title,
        "concept": learning_object.concept,
        "facet": str(card.bindings.get("target_facet", "the key idea")),
        "confusable": str(card.bindings.get("confusable_concept", "a related concept")),
        "summary": learning_object.summary,
    }

    payloads: list[dict[str, Any]] = []
    for index, (surface_suffix, prompt_template) in enumerate(surfaces[: max(count, 0)]):
        prompt = prompt_template.format(**slots)
        payloads.append(
            _instance_payload(
                learning_object,
                card,
                template,
                prompt=prompt,
                expected_answer=(
                    f"Grounded in the Learning Object summary: {learning_object.summary}"
                ),
                surface_family=f"{template.id}_{surface_suffix}",
                now=now,
            )
        )
    return payloads


def _instance_payload(
    learning_object: LearningObject,
    card: InstrumentCard,
    template: ProbeFamilyTemplate,
    *,
    prompt: str,
    expected_answer: str,
    surface_family: str,
    now: str,
) -> dict[str, Any]:
    """One Item Instance payload: card/template own everything except the
    surface (prompt, expected answer, surface family)."""

    fatal_errors = [
        dict(SIGNATURE_FATAL_ERRORS[outcome], max_grade=1)
        for outcome in template.observation_alphabet
        if outcome in card.signature_error_types and outcome in SIGNATURE_FATAL_ERRORS
    ]
    digest = hashlib.sha256(f"{card.id}:{surface_family}:{prompt}".encode("utf-8")).hexdigest()[:8]
    return {
        "id": f"pi_gen_{template.id}_{learning_object.id.removeprefix('lo_')}_{digest}",
        "learning_object_id": learning_object.id,
        "subjects": None,
        "practice_mode": "diagnostic_microprobe" if template.id == DIALOGUE_MICROPROBE_V1.id else "short_answer",
        "attempt_types_allowed": ["diagnostic_probe", "dont_know"],
        "evidence_facets": list(card.target_facets),
        "evidence_weights": {facet: 1.0 for facet in card.target_facets},
        "prompt": prompt,
        "expected_answer": expected_answer,
        "surface_family": surface_family,
        "transfer_distance": (
            0.35
            if template.id in ("perturbation", "minimal_counterexample")
            else 0.5 if template.id in LONGFORM_FAMILY_IDS else 0.0
        ),
        "grading_rubric": {
            "max_points": 4,
            "criteria": (
                [
                    {"id": criterion_id, "points": points, "description": description}
                    for criterion_id, points, description in _LONGFORM_CRITERIA[template.id]
                ]
                if template.id in _LONGFORM_CRITERIA
                else [
                    {
                        "id": "correctness",
                        "points": 4,
                        "description": "Response demonstrates the target idea with a decisive reason.",
                    }
                ]
            ),
            "fatal_errors": fatal_errors,
        },
        "provenance": {"origin": "codex_proposal"},
        "created_at": now,
        "updated_at": now,
    }


# --- LLM surfaces (§9.2/§9.4) ---------------------------------------------------------

# The family's measurement pattern in prose, handed to the LLM so surface
# wording honors the instrument contract instead of drifting into generic quiz
# questions. Keyed by family template id.
_FAMILY_MEASUREMENT_INTENT: dict[str, str] = {
    "minimal_recall": (
        "Minimal recall: ask the learner to state the target idea itself, briefly and "
        "from memory — no application, no multi-step task."
    ),
    "prediction_before_computation": (
        "Prediction before computation: force a committed prediction about what happens "
        "in a concrete case, plus the decisive reason, explicitly BEFORE any computation "
        "or checking."
    ),
    "perturbation": (
        "Perturbation: shift the familiar surface (notation, framing, direction, or "
        "representation) while keeping the underlying idea applicable, and ask whether "
        "and why the idea still holds."
    ),
    "minimal_counterexample": (
        "Minimal counterexample: ask for a boundary condition, failure case, or the "
        "smallest change that breaks the idea, with the decisive reason it fails there."
    ),
    "contrast_confusable": (
        "Contrast with a confusable neighbor: force a choice between the target concept "
        "and the confusable concept on a case where exactly one applies, with the "
        "decisive difference."
    ),
    "proof_skeleton": (
        "Proof skeleton: ask for the ordered skeleton of a proof — the claim, the key "
        "steps in order, the justification for each step, and how the conclusion follows."
    ),
    "derivation": (
        "Derivation: ask for an end-to-end derivation that first commits to a named "
        "strategy, then sets up from the givens and executes explicit intermediate steps."
    ),
    "extended_case": (
        "Extended case: pose a realistic scenario where the target idea interacts with "
        "competing constraints; the learner must identify the governing principle, apply "
        "it to the specific facts, and integrate the constraints into a conclusion."
    ),
    "dialogue_microprobe": (
        "Dialogue microprobe turn: one short committed question — commit to an answer, "
        "state the decisive reason, respond to a minimal counterfactual, or give a "
        "boundary case — answerable in one or two sentences."
    ),
}


def _llm_prompt_version() -> str:
    from learnloop.codex.prompts import PROBE_INSTANCE_PROMPT_VERSION

    return PROBE_INSTANCE_PROMPT_VERSION


def _sanitized_surface_suffix(raw: str, index: int) -> str:
    cleaned = "".join(ch if ch.isalnum() else "_" for ch in raw.strip().lower()).strip("_")
    while "__" in cleaned:
        cleaned = cleaned.replace("__", "_")
    return cleaned[:40] or f"surface_{index}"


def llm_instance_payloads(
    vault: LoadedVault,
    card: InstrumentCard,
    template: ProbeFamilyTemplate,
    *,
    count: int,
    ai_client: object,
    clock: Clock | None = None,
) -> list[dict[str, Any]] | None:
    """LLM-generated surface payloads for one binding, or None when the
    provider lacks the capability or is unavailable (§9.2 fallback contract).

    The LLM supplies only prompt/expected-answer/surface wording; rubric,
    facets, and signature fatal errors stay card-derived, and every payload
    still passes ``instance_gate_errors`` at the caller.
    """

    from learnloop.codex.client import CodexUnavailable, ProbeInstanceContext

    run_surfaces = getattr(ai_client, "run_probe_instance_surfaces", None)
    if run_surfaces is None:
        return None
    learning_object = vault.learning_objects[card.learning_object_id]
    existing_items = [
        item
        for item in vault.practice_items.values()
        if item.learning_object_id == learning_object.id
    ]
    context = ProbeInstanceContext(
        family_template_id=template.id,
        family_template_version=template.version,
        instrument_kind=template.instrument_kind,
        measurement_intent=_FAMILY_MEASUREMENT_INTENT.get(
            template.id, f"Instrument kind: {template.instrument_kind}."
        ),
        learning_object_id=learning_object.id,
        learning_object_title=learning_object.title,
        learning_object_concept=learning_object.concept,
        learning_object_summary=learning_object.summary,
        target_facets=[str(facet) for facet in card.target_facets],
        confusable_concept=(
            str(card.bindings["confusable_concept"])
            if card.bindings.get("confusable_concept")
            else None
        ),
        observation_alphabet=list(template.observation_alphabet),
        count=max(count, 1),
        existing_prompts=sorted(item.prompt.strip() for item in existing_items),
        existing_surface_families=sorted(
            {item.surface_family for item in existing_items if item.surface_family}
        ),
    )
    try:
        result = run_surfaces(context)
    except CodexUnavailable:
        return None
    now = utc_now_iso(clock)
    payloads: list[dict[str, Any]] = []
    seen_suffixes: set[str] = set()
    for index, surface in enumerate(result.surfaces):
        prompt = surface.prompt_md.strip()
        expected = surface.expected_answer_md.strip()
        if not prompt or not expected:
            continue
        suffix = _sanitized_surface_suffix(surface.surface_suffix, index)
        if suffix in seen_suffixes:
            suffix = f"{suffix}_{index}"
        seen_suffixes.add(suffix)
        payloads.append(
            _instance_payload(
                learning_object,
                card,
                template,
                prompt=prompt,
                expected_answer=expected,
                surface_family=f"{template.id}_llm_{suffix}",
                now=now,
            )
        )
    return payloads


# --- Instance gate (§10 step 4) ------------------------------------------------------


def _grounding_tokens(text: str) -> set[str]:
    """Content tokens for the grounding check: >3 chars, naive plural fold."""

    return {
        token.rstrip("s")
        for token in re.split(r"[^a-z0-9]+", text.lower())
        if len(token) > 3
    }


def instance_gate_errors(
    vault: LoadedVault,
    payload: Mapping[str, Any],
    card: InstrumentCard,
    template: ProbeFamilyTemplate,
) -> list[str]:
    """Cheap structural, grounding, duplication, and card-conformance checks."""

    errors: list[str] = []
    prompt = str(payload.get("prompt") or "").strip()
    expected = payload.get("expected_answer")
    if not prompt:
        errors.append("empty prompt")
    if not expected:
        errors.append("empty expected answer")
    if prompt and expected and prompt == expected:
        errors.append("prompt equals expected answer (answer leakage)")
    learning_object = vault.learning_objects.get(card.learning_object_id)
    if learning_object is not None and prompt:
        prompt_lower = prompt.lower()
        title_lower = learning_object.title.lower()
        # Natural-language surfaces (LLM-generated) reference the target in
        # prose rather than echoing internal slugs, so grounding also accepts
        # most of the title's or concept's content tokens (stem-folded, so
        # "dot product" grounds a title saying "Dot Products") or a facet
        # phrase in natural form.
        prompt_tokens = _grounding_tokens(prompt_lower)
        title_tokens = _grounding_tokens(title_lower)
        concept_tokens = _grounding_tokens(learning_object.concept.lower())
        mentions_target = (
            title_lower in prompt_lower
            or learning_object.concept.lower() in prompt_lower
            or any(str(facet).lower() in prompt_lower for facet in card.target_facets)
            or any(
                str(facet).lower().replace("_", " ") in prompt_lower
                for facet in card.target_facets
            )
            or (title_tokens and len(title_tokens & prompt_tokens) / len(title_tokens) >= 0.6)
            or (concept_tokens and concept_tokens <= prompt_tokens)
        )
        if not mentions_target:
            errors.append("prompt does not mention the bound target (grounding failure)")
    item_facets = {str(facet) for facet in payload.get("evidence_facets") or []}
    if not set(card.target_facets) <= item_facets:
        errors.append("instance does not cover the card's target facets (card conformance)")
    rubric = payload.get("grading_rubric") or {}
    declared_fatals = {str(entry.get("id")) for entry in rubric.get("fatal_errors", [])}
    for outcome, fired in card.signature_error_types.items():
        if outcome not in SIGNATURE_FATAL_ERRORS:
            continue
        if not declared_fatals & set(fired):
            errors.append(f"rubric has no fatal error identifying signature outcome {outcome}")
    # Duplication: an existing item on the LO with the same prompt or the same
    # generated surface family is a disallowed repeat (§5.4 exposure control).
    # Ephemeral dialogue turn instances are exempt as comparison targets: they
    # are never schedulable (exposure control does not apply) and every block
    # legitimately re-mints the same turn surfaces — without the exemption a
    # second dialogue block on the same LO could never open.
    for item in vault.practice_items.values():
        if item.learning_object_id != card.learning_object_id:
            continue
        if item.id == payload.get("id"):
            continue
        if item.practice_mode == "diagnostic_microprobe":
            continue
        if item.prompt.strip() == prompt:
            errors.append(f"duplicate prompt of existing item {item.id}")
        if item.surface_family and item.surface_family == payload.get("surface_family"):
            errors.append(f"duplicate surface family of existing item {item.id}")
    return errors


# --- Need resolution (§10) -----------------------------------------------------------


def generate_instances_for_episode(
    repository: Repository,
    vault: LoadedVault,
    episode_id: str,
    *,
    clock: Clock | None = None,
    instances_per_family: int | None = None,
    seed: int = 0,
    ai_client: object | None = None,
) -> GenerationSummary:
    """Resolve a `pending_items` episode's generation needs through admitted
    family/card bindings (§10 steps 3–6).

    Writes instances as vault YAML (the same source of truth accepted
    proposals compile to), links provenance, applies the trust policy, and
    unparks the episode when a freshly reloaded vault yields at least one
    eligible instrument.

    When ``ai_client`` supports ``run_probe_instance_surfaces`` (and
    ``probe.generation.llm_surfaces`` is enabled), surfaces come from the LLM
    first — validated by the same structural gate — and the parametric
    templates top up any shortfall (§9.2 fallback contract).
    """

    from learnloop.services.probe_episodes import eligible_instruments

    episode = repository.probe_episode(episode_id)
    if episode is None:
        raise ValueError(f"unknown probe episode {episode_id}")
    summary = GenerationSummary(episode_id=episode.id, learning_object_id=episode.learning_object_id)
    if episode.status != "pending_items":
        return summary
    learning_object = vault.learning_objects.get(episode.learning_object_id)
    if learning_object is None:
        return summary

    count = instances_per_family or vault.config.probe.generation.instances_per_need
    families = [
        template
        for template in applicable_families(vault, learning_object, repository)
        if template.id != DIALOGUE_MICROPROBE_V1.id
    ]
    # §9.5 coverage: one direct/minimal family plus EVERY applicable shifted
    # family (contrast, perturbation, counterexample) — each locked hypothesis
    # needs at least one instrument that actually elicits it, or the episode
    # can never separate that state from robust performance.
    direct = [t for t in families if t.id in (MINIMAL_RECALL_V1.id, PREDICTION_V1.id)]
    shifted = [t for t in families if t.id not in (MINIMAL_RECALL_V1.id, PREDICTION_V1.id)]
    chosen = ([direct[0]] if direct else []) + shifted
    if not chosen:
        summary.family_authoring_needed = True
        return summary

    # Intra-batch dedup: the structural gate compares against the loaded vault,
    # which does not yet contain instances accepted earlier in this same run.
    batch_ids: set[str] = set()
    batch_prompts: set[str] = set()
    batch_surfaces: set[str] = set()

    for template in chosen:
        resolved = ensure_instrument_card(
            vault, repository, episode.learning_object_id, template, clock=clock
        )
        if resolved is None:
            continue
        card, resolved_template = resolved
        family_record = repository.probe_family_template(
            resolved_template.id, resolved_template.version
        )
        family_status = family_record.status if family_record is not None else "provisional"
        review_status = (
            "auto_admitted_provisional" if family_status == "trusted" else "pending_review"
        )
        # LLM surfaces first (when available), parametric templates as the
        # top-up fallback; both flow through the same structural gate.
        candidates: list[tuple[dict[str, Any], str, str]] = []
        if ai_client is not None and vault.config.probe.generation.llm_surfaces:
            llm_payloads = llm_instance_payloads(
                vault, card, resolved_template, count=count, ai_client=ai_client, clock=clock
            )
            for payload in llm_payloads or []:
                candidates.append((payload, LLM_GENERATOR_ID, LLM_GENERATOR_VERSION))
        for payload in parametric_instance_payloads(
            vault, card, resolved_template, count=count, seed=seed, clock=clock
        ):
            candidates.append((payload, GENERATOR_ID, GENERATOR_VERSION))

        accepted = 0
        for payload, generator_id, generator_version in candidates:
            if accepted >= count:
                break
            if payload["id"] in vault.practice_items or payload["id"] in batch_ids:
                continue  # idempotent re-run / intra-batch duplicate
            prompt_key = str(payload["prompt"]).strip()
            if prompt_key in batch_prompts or payload["surface_family"] in batch_surfaces:
                continue
            errors = instance_gate_errors(vault, payload, card, resolved_template)
            if errors:
                continue
            instance_metadata: dict[str, Any] = {
                "review_status": review_status,
                "surface_family": payload["surface_family"],
                "family_status_at_generation": family_status,
            }
            if generator_id == LLM_GENERATOR_ID:
                instance_metadata["generator_model"] = getattr(ai_client, "model", None)
                instance_metadata["prompt_version"] = _llm_prompt_version()
            upsert_practice_item(vault.root, payload, clock=clock)
            repository.link_probe_item_family(
                practice_item_id=payload["id"],
                instrument_card_id=card.id,
                instrument_card_version=card.version,
                generator_id=generator_id,
                generator_version=generator_version,
                generation_seed=str(seed),
                instance_metadata=instance_metadata,
                clock=clock,
            )
            repository.upsert_practice_item_state(
                payload["id"],
                active=review_status == "auto_admitted_provisional",
                clock=clock,
            )
            summary.generated.append(
                GeneratedInstance(
                    practice_item_id=payload["id"],
                    instrument_card_id=card.id,
                    instrument_card_version=card.version,
                    family_template_id=resolved_template.id,
                    family_template_version=resolved_template.version,
                    surface_family=payload["surface_family"],
                    review_status=review_status,
                    generation_seed=str(seed),
                    generator_id=generator_id,
                )
            )
            batch_ids.add(payload["id"])
            batch_prompts.add(prompt_key)
            batch_surfaces.add(str(payload["surface_family"]))
            accepted += 1

    if summary.generated:
        refreshed_vault = load_vault(vault.root)
        refreshed_vault.config = vault.config
        refreshed = repository.probe_episode(episode.id)
        if refreshed is not None and refreshed.status == "pending_items":
            if eligible_instruments(refreshed_vault, repository, refreshed):
                repository.update_probe_episode_status(episode.id, status="in_progress", clock=clock)
                summary.episode_unparked = True
        for need in repository.probe_generation_needs(
            probe_episode_id=episode.id, status="pending"
        ):
            repository.resolve_probe_generation_need(need.id, clock=clock)
            summary.resolved_need_ids.append(need.id)
    return summary


def approve_probe_instance(
    repository: Repository,
    vault: LoadedVault,
    practice_item_id: str,
    *,
    clock: Clock | None = None,
) -> bool:
    """Reviewer approval for a pending instance: activate it and unpark its
    LO's episode when it now yields an eligible instrument."""

    from learnloop.services.probe_episodes import eligible_instruments

    links = repository.probe_item_family_links(practice_item_id)
    if not links:
        return False
    link = links[0]
    metadata = dict(link.instance_metadata or {})
    metadata["review_status"] = "approved"
    repository.update_probe_item_family_metadata(
        practice_item_id=practice_item_id,
        instrument_card_id=link.instrument_card_id,
        instrument_card_version=link.instrument_card_version,
        instance_metadata=metadata,
    )
    repository.upsert_practice_item_state(practice_item_id, active=True, clock=clock)
    item = vault.practice_items.get(practice_item_id)
    if item is not None:
        episode = repository.open_probe_episode(item.learning_object_id)
        if episode is not None and episode.status == "pending_items":
            if eligible_instruments(vault, repository, episode):
                repository.update_probe_episode_status(episode.id, status="in_progress", clock=clock)
    return True


# --- LLM-backed family admission gate (§9.6) ------------------------------------------


def run_llm_family_gate(
    vault: LoadedVault,
    repository: Repository,
    learning_object_id: str,
    template: ProbeFamilyTemplate,
    ai_client: object,
    *,
    trials_per_hypothesis: int = 3,
    clock: Clock | None = None,
):
    """Run the §9.6 family admission gate with LLM planted-trial traces.

    The LLM simulates learner responses under each card-bound hypothesis and
    judges the outcome class each response lands in; the deterministic gate
    (structural compile, pair separation, reverse matching, non-applicable
    controls) then runs in ``run_family_admission_gate``, which stores the
    counts under ``evidence_source='synthetic_gate'`` only. Returns the
    ``FamilyGateResult``, or None when the LO cannot bind the family or the
    provider lacks ``run_probe_family_trials``.
    """

    from learnloop.codex.client import CodexUnavailable, ProbeFamilyTrialsContext
    from learnloop.services.probe_families import PlantedTrial, run_family_admission_gate

    run_trials = getattr(ai_client, "run_probe_family_trials", None)
    if run_trials is None:
        return None
    resolved = ensure_instrument_card(vault, repository, learning_object_id, template, clock=clock)
    if resolved is None:
        return None
    card, resolved_template = resolved

    # The surfaces under test are the ones generation would actually serve:
    # LLM surfaces when available, parametric otherwise.
    payloads = (
        llm_instance_payloads(
            vault, card, resolved_template, count=3, ai_client=ai_client, clock=clock
        )
        if vault.config.probe.generation.llm_surfaces
        else None
    ) or parametric_instance_payloads(vault, card, resolved_template, count=3, seed=0, clock=clock)
    if not payloads:
        return None

    learning_object = vault.learning_objects[learning_object_id]
    context = ProbeFamilyTrialsContext(
        family_template_id=resolved_template.id,
        family_template_version=resolved_template.version,
        instrument_kind=resolved_template.instrument_kind,
        measurement_intent=_FAMILY_MEASUREMENT_INTENT.get(
            resolved_template.id, f"Instrument kind: {resolved_template.instrument_kind}."
        ),
        learning_object_title=learning_object.title,
        learning_object_summary=learning_object.summary,
        target_facets=[str(facet) for facet in card.target_facets],
        confusable_concept=(
            str(card.bindings["confusable_concept"])
            if card.bindings.get("confusable_concept")
            else None
        ),
        hypothesis_slots=list(card.hypotheses),
        observation_alphabet=list(resolved_template.observation_alphabet),
        non_applicable_controls=list(resolved_template.non_applicable_controls),
        surfaces=[
            {
                "surface_suffix": payload["surface_family"],
                "prompt_md": payload["prompt"],
                "expected_answer_md": payload["expected_answer"],
            }
            for payload in payloads
        ],
        trials_per_hypothesis=trials_per_hypothesis,
    )
    try:
        result = run_trials(context)
    except CodexUnavailable:
        return None

    # Out-of-alphabet outcomes are elicitation noise, not family evidence:
    # drop them rather than letting them corrupt reverse matching.
    alphabet = set(resolved_template.observation_alphabet)
    trials = [
        PlantedTrial(
            planted_slot=trial.hypothesis_slot,
            matched_outcome=trial.matched_outcome,
            non_applicable_control=trial.non_applicable_control,
        )
        for trial in result.trials
        if trial.matched_outcome in alphabet
    ]
    if not trials:
        return None
    return run_family_admission_gate(
        card, resolved_template, trials, repository=repository, clock=clock
    )


def pending_review_instance_ids(repository: Repository) -> set[str]:
    """Item ids parked behind instance review (consumed by state sync so a
    vault sync cannot force-reactivate them)."""

    return repository.probe_instance_ids_with_review_status("pending_review")

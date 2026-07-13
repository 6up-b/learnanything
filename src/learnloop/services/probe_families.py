"""Probe Family Templates and Instrument Cards (spec_probe_eig_redesign.md §9).

The durable unit of probe authoring, admission, and primary calibration is a
versioned ``ProbeFamilyTemplate``; an LO-bound ``InstrumentCard`` binds its
slots to concrete facets/hypotheses; compiled conditionals drive BOTH candidate
EIG and posterior replay (§7.2 likelihood identity), composed with the grader
channel (§7.6).

Card conditionals are authored in the fixed ordinal vocabulary only. The
canonical table is a protocol constant — never tuned, never fit, never grown —
and free-form numeric conditionals are rejected at validation (§9.3). All
numeric drift happens in the per-family-version Dirichlet posterior updated by
observed outcome counts (§9.7).
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from math import log
from typing import Any, Mapping

from learnloop.clock import Clock
from learnloop.db.repositories import Repository

# §9.3 canonical ordinal table. Fixed protocol constant, like Likert anchors.
ORDINAL_VOCABULARY: dict[str, float] = {
    "dominant": 0.60,
    "likely": 0.25,
    "occasional": 0.10,
    "rare": 0.04,
    "negligible": 0.01,
}
DEFAULT_CONDITIONAL_PSEUDO_COUNT = 8.0

SIGNATURE_MATCHER_VERSION = 1


def knowledge_type_tokens(knowledge_type: str | None) -> set[str]:
    """Tokens of a possibly-compound knowledge type.

    Real vaults use compound types like ``conceptual_procedural`` or
    ``theorem_application``; exact-string matching silently dropped every
    knowledge-type-restricted family, hypothesis, and coverage check for
    those LOs.
    """

    return {token for token in re.split(r"[_\s/+-]+", (knowledge_type or "").lower()) if token}
# v2: predictive EIG per expected second is the default diagnostic objective
# (§7.4/§7.5); hypothesis EIG is the fallback when the held-out target set is
# inadequate. The presentation's selection_components record which one ranked.
SELECTION_POLICY_VERSION = "probe_episode_v2"

# §7.6 grader channels: symmetric confusion with a per-policy reliability. The
# identity share is the probability the observed outcome class equals the true
# one; the remainder spreads uniformly over the other classes.
GRADER_CHANNEL_RELIABILITY: dict[str, float] = {
    "diagnostic_microprobe_v1": 0.90,
    "diagnostic_longform_v1": 0.80,
}
# §5.8: self-grading is not an approved diagnostic grading provider.
# "deterministic" covers grades no judgment call can distort (dont_know → 0).
APPROVED_DIAGNOSTIC_GRADING_SOURCES = ("ai", "codex", "deterministic")


class CardValidationError(ValueError):
    """A family/card failed schema, vocabulary, or normalization validation."""


class FamilyGateRejection(ValueError):
    """A family/card version failed the admission gate (§9.6)."""


@dataclass(frozen=True)
class ProbeFamilyTemplate:
    """Versioned reusable measurement pattern (§9.2).

    ``slot_aliases`` maps episode hypothesis labels the instrument cannot
    separate onto the slot whose predicted observations they share — an honest
    zero-EIG identification (§2.2), not a diagnosis. A minimal-recall item
    predicts identical responses under ``surface_only`` and
    ``robust_initial_grasp``, so both alias to the same row.
    """

    id: str
    version: int
    instrument_kind: str
    observation_alphabet: tuple[str, ...]
    hypothesis_slots: tuple[str, ...]
    applicable_knowledge_types: tuple[str, ...] = ()
    target_slot: str | None = None
    contrast_slots: tuple[str, ...] = ()
    slot_aliases: tuple[tuple[str, str], ...] = ()
    applicability_conditions: tuple[str, ...] = ()
    non_applicable_controls: tuple[str, ...] = ()
    expected_seconds_median: float = 45.0
    total_task_evidence_mass: float = 1.0
    allowed_assistance: tuple[str, ...] = ("none",)
    generator_schema_version: int = 1
    signature_matcher_version: int = SIGNATURE_MATCHER_VERSION
    grader_policy: str = "diagnostic_microprobe_v1"

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "version": self.version,
            "instrument_kind": self.instrument_kind,
            "observation_alphabet": list(self.observation_alphabet),
            "hypothesis_slots": list(self.hypothesis_slots),
            "applicable_knowledge_types": list(self.applicable_knowledge_types),
            "target_slot": self.target_slot,
            "contrast_slots": list(self.contrast_slots),
            "slot_aliases": {label: slot for label, slot in self.slot_aliases},
            "applicability_conditions": list(self.applicability_conditions),
            "non_applicable_controls": list(self.non_applicable_controls),
            "expected_seconds_prior": {"median": self.expected_seconds_median},
            "total_task_evidence_mass": self.total_task_evidence_mass,
            "allowed_assistance": list(self.allowed_assistance),
            "generator_schema_version": self.generator_schema_version,
            "signature_matcher_version": self.signature_matcher_version,
            "grader_policy": self.grader_policy,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "ProbeFamilyTemplate":
        return cls(
            id=str(payload["id"]),
            version=int(payload["version"]),
            instrument_kind=str(payload["instrument_kind"]),
            observation_alphabet=tuple(payload["observation_alphabet"]),
            hypothesis_slots=tuple(payload["hypothesis_slots"]),
            applicable_knowledge_types=tuple(payload.get("applicable_knowledge_types", ())),
            target_slot=payload.get("target_slot"),
            contrast_slots=tuple(payload.get("contrast_slots", ())),
            slot_aliases=tuple(sorted(dict(payload.get("slot_aliases", {})).items())),
            applicability_conditions=tuple(payload.get("applicability_conditions", ())),
            non_applicable_controls=tuple(payload.get("non_applicable_controls", ())),
            expected_seconds_median=float((payload.get("expected_seconds_prior") or {}).get("median", 45.0)),
            total_task_evidence_mass=float(payload.get("total_task_evidence_mass", 1.0)),
            allowed_assistance=tuple(payload.get("allowed_assistance", ("none",))),
            generator_schema_version=int(payload.get("generator_schema_version", 1)),
            signature_matcher_version=int(payload.get("signature_matcher_version", SIGNATURE_MATCHER_VERSION)),
            grader_policy=str(payload.get("grader_policy", "diagnostic_microprobe_v1")),
        )

    def schema_hash(self) -> str:
        return hashlib.sha256(
            json.dumps(self.as_dict(), sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()


@dataclass(frozen=True)
class InstrumentCard:
    """LO-bound executable binding of a family template (§9.3).

    ``conditional_observations`` maps hypothesis slot -> outcome -> ordinal word.
    ``signature_error_types`` maps an outcome class to the vault error types /
    misconception ids whose firing identifies it (the deterministic matcher input).
    """

    id: str
    version: int
    family_template_id: str
    family_template_version: int
    learning_object_id: str
    target_decision: str
    bindings: dict[str, Any]
    hypotheses: tuple[str, ...]
    conditional_observations: dict[str, dict[str, Any]]
    conditional_pseudo_count: float = DEFAULT_CONDITIONAL_PSEUDO_COUNT
    nuisance_requirements: tuple[str, ...] = ()
    expected_seconds: float = 45.0
    instructional_actions: dict[str, str] = field(default_factory=dict)
    target_facets: tuple[str, ...] = ()
    signature_error_types: dict[str, list[str]] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "version": self.version,
            "family_template_id": self.family_template_id,
            "family_template_version": self.family_template_version,
            "learning_object_id": self.learning_object_id,
            "target_decision": self.target_decision,
            "bindings": dict(self.bindings),
            "hypotheses": list(self.hypotheses),
            "conditional_observations": {
                slot: dict(row) for slot, row in self.conditional_observations.items()
            },
            "conditional_pseudo_count": self.conditional_pseudo_count,
            "nuisance_requirements": list(self.nuisance_requirements),
            "expected_seconds": self.expected_seconds,
            "instructional_actions": dict(self.instructional_actions),
            "target_facets": list(self.target_facets),
            "signature_error_types": {key: list(value) for key, value in self.signature_error_types.items()},
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "InstrumentCard":
        return cls(
            id=str(payload["id"]),
            version=int(payload["version"]),
            family_template_id=str(payload["family_template_id"]),
            family_template_version=int(payload["family_template_version"]),
            learning_object_id=str(payload["learning_object_id"]),
            target_decision=str(payload.get("target_decision", "")),
            bindings=dict(payload.get("bindings", {})),
            hypotheses=tuple(payload["hypotheses"]),
            conditional_observations={
                slot: dict(row) for slot, row in dict(payload["conditional_observations"]).items()
            },
            conditional_pseudo_count=float(
                payload.get("conditional_pseudo_count", DEFAULT_CONDITIONAL_PSEUDO_COUNT)
            ),
            nuisance_requirements=tuple(payload.get("nuisance_requirements", ())),
            expected_seconds=float(payload.get("expected_seconds", 45.0)),
            instructional_actions=dict(payload.get("instructional_actions", {})),
            target_facets=tuple(payload.get("target_facets", ())),
            signature_error_types={
                key: list(value) for key, value in dict(payload.get("signature_error_types", {})).items()
            },
        )


@dataclass(frozen=True)
class CompiledInstrument:
    """Executable conditional model shared by selection and replay (§7.2).

    ``rows`` are normalized ``P(true_outcome | hypothesis_slot)``; the grader
    channel is composed at call time so selection and replay stay identical.
    ``provenance`` is ``instrument_card`` for admitted cards or
    ``legacy_fallback`` for the explicitly-logged registry/IRT fallback (§7.2).
    """

    outcome_alphabet: tuple[str, ...]
    rows: dict[str, dict[str, float]]
    pseudo_count: float
    grader_policy: str
    provenance: str
    family_template_id: str | None = None
    family_template_version: int | None = None
    card_id: str | None = None
    card_version: int | None = None
    target_facets: tuple[str, ...] = ()
    signature_error_types: dict[str, tuple[str, ...]] = field(default_factory=dict)
    expected_seconds: float = 45.0
    total_task_evidence_mass: float = 1.0
    instructional_actions: dict[str, str] = field(default_factory=dict)
    slot_aliases: dict[str, str] = field(default_factory=dict)

    def compiled_likelihood_hash(self) -> str:
        payload = {
            "alphabet": list(self.outcome_alphabet),
            "rows": {
                slot: {outcome: round(value, 10) for outcome, value in sorted(row.items())}
                for slot, row in sorted(self.rows.items())
            },
            "pseudo_count": self.pseudo_count,
            "grader_policy": self.grader_policy,
        }
        return hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()

    def snapshot(self) -> dict[str, Any]:
        """Persistable resolved snapshot for a committed presentation (§9.3)."""

        return {
            "outcome_alphabet": list(self.outcome_alphabet),
            "rows": {slot: dict(row) for slot, row in self.rows.items()},
            "pseudo_count": self.pseudo_count,
            "grader_policy": self.grader_policy,
            "provenance": self.provenance,
            "family_template_id": self.family_template_id,
            "family_template_version": self.family_template_version,
            "card_id": self.card_id,
            "card_version": self.card_version,
            "target_facets": list(self.target_facets),
            "signature_error_types": {
                key: list(value) for key, value in self.signature_error_types.items()
            },
            "expected_seconds": self.expected_seconds,
            "total_task_evidence_mass": self.total_task_evidence_mass,
            "instructional_actions": dict(self.instructional_actions),
            "slot_aliases": dict(self.slot_aliases),
            "compiled_likelihood_hash": self.compiled_likelihood_hash(),
        }

    @classmethod
    def from_snapshot(cls, payload: Mapping[str, Any]) -> "CompiledInstrument":
        return cls(
            outcome_alphabet=tuple(payload["outcome_alphabet"]),
            rows={slot: dict(row) for slot, row in dict(payload["rows"]).items()},
            pseudo_count=float(payload.get("pseudo_count", DEFAULT_CONDITIONAL_PSEUDO_COUNT)),
            grader_policy=str(payload.get("grader_policy", "diagnostic_microprobe_v1")),
            provenance=str(payload.get("provenance", "instrument_card")),
            family_template_id=payload.get("family_template_id"),
            family_template_version=payload.get("family_template_version"),
            card_id=payload.get("card_id"),
            card_version=payload.get("card_version"),
            target_facets=tuple(payload.get("target_facets", ())),
            signature_error_types={
                key: tuple(value) for key, value in dict(payload.get("signature_error_types", {})).items()
            },
            expected_seconds=float(payload.get("expected_seconds", 45.0)),
            total_task_evidence_mass=float(payload.get("total_task_evidence_mass", 1.0)),
            instructional_actions=dict(payload.get("instructional_actions", {})),
            slot_aliases=dict(payload.get("slot_aliases", {})),
        )


def validate_and_compile_card(
    card: InstrumentCard,
    template: ProbeFamilyTemplate,
    *,
    calibration_counts: Mapping[str, Mapping[str, float]] | None = None,
) -> CompiledInstrument:
    """Validate a card against its template and compile executable rows (§9.3).

    Rejects numeric conditionals, unknown ordinal words, unknown outcomes, and
    incomplete rows. Compiled rows are Dirichlet prior means; when
    ``calibration_counts`` (observed outcome counts per hypothesis, §9.7) are
    supplied, the posterior mean ``(pseudo·prior + counts) / (pseudo + n)``
    replaces the prior mean.
    """

    if card.family_template_id != template.id or card.family_template_version != template.version:
        raise CardValidationError(
            f"card {card.id} v{card.version} binds family "
            f"{card.family_template_id} v{card.family_template_version}, "
            f"not {template.id} v{template.version}"
        )
    if card.conditional_pseudo_count <= 0:
        raise CardValidationError("conditional_pseudo_count must be positive")
    unknown_slots = [slot for slot in card.hypotheses if slot not in template.hypothesis_slots]
    if unknown_slots:
        raise CardValidationError(
            f"card {card.id} binds hypotheses outside the family's slots: {unknown_slots}"
        )
    alphabet = template.observation_alphabet

    rows: dict[str, dict[str, float]] = {}
    for slot in card.hypotheses:
        authored = card.conditional_observations.get(slot)
        if authored is None:
            raise CardValidationError(f"card {card.id} is missing a conditional row for {slot}")
        missing = [outcome for outcome in alphabet if outcome not in authored]
        if missing:
            raise CardValidationError(
                f"card {card.id} row {slot} is incomplete; missing outcomes {missing}"
            )
        extra = [outcome for outcome in authored if outcome not in alphabet]
        if extra:
            raise CardValidationError(
                f"card {card.id} row {slot} names outcomes outside the family alphabet: {extra}"
            )
        compiled_row: dict[str, float] = {}
        for outcome, word in authored.items():
            if isinstance(word, (int, float)) and not isinstance(word, bool):
                raise CardValidationError(
                    f"card {card.id} row {slot} outcome {outcome}: free-form numeric "
                    "conditionals are rejected; author with the ordinal vocabulary "
                    f"{sorted(ORDINAL_VOCABULARY)} (§9.3)"
                )
            if word not in ORDINAL_VOCABULARY:
                raise CardValidationError(
                    f"card {card.id} row {slot} outcome {outcome}: unknown ordinal "
                    f"word {word!r}; allowed: {sorted(ORDINAL_VOCABULARY)}"
                )
            compiled_row[outcome] = ORDINAL_VOCABULARY[word]
        total = sum(compiled_row.values())
        prior_row = {outcome: value / total for outcome, value in compiled_row.items()}
        counts = dict((calibration_counts or {}).get(slot, {}))
        count_total = sum(max(float(value), 0.0) for value in counts.values())
        if count_total > 0:
            pseudo = card.conditional_pseudo_count
            prior_row = {
                outcome: (pseudo * prior + max(float(counts.get(outcome, 0.0)), 0.0))
                / (pseudo + count_total)
                for outcome, prior in prior_row.items()
            }
        rows[slot] = prior_row

    # Aliases whose target row the card does not bind fall through to the
    # open-set abstention path in map_episode_labels_to_slots.
    alias_map = {label: slot for label, slot in template.slot_aliases if slot in rows}
    return CompiledInstrument(
        outcome_alphabet=alphabet,
        rows=rows,
        pseudo_count=card.conditional_pseudo_count,
        grader_policy=template.grader_policy,
        provenance="instrument_card",
        family_template_id=template.id,
        family_template_version=template.version,
        card_id=card.id,
        card_version=card.version,
        target_facets=card.target_facets,
        signature_error_types={key: tuple(value) for key, value in card.signature_error_types.items()},
        expected_seconds=card.expected_seconds,
        total_task_evidence_mass=template.total_task_evidence_mass,
        instructional_actions=dict(card.instructional_actions),
        slot_aliases=alias_map,
    )


# --- Grader channel (§7.6) -----------------------------------------------------


def grader_channel_matrix(
    grader_policy: str,
    alphabet: tuple[str, ...],
    *,
    reliability: float | None = None,
) -> dict[str, dict[str, float]]:
    """``P(observed_grade | true_response)`` per outcome class.

    Symmetric confusion: the true class is observed with probability
    ``reliability``; the remainder spreads uniformly over the other classes.
    """

    r = reliability if reliability is not None else GRADER_CHANNEL_RELIABILITY.get(grader_policy, 0.9)
    r = min(max(r, 0.0), 1.0)
    size = len(alphabet)
    spread = (1.0 - r) / (size - 1) if size > 1 else 0.0
    return {
        true: {observed: (r if observed == true else spread) for observed in alphabet}
        for true in alphabet
    }


def compose_with_grader_channel(
    rows: Mapping[str, Mapping[str, float]],
    channel: Mapping[str, Mapping[str, float]],
) -> dict[str, dict[str, float]]:
    """``P(observed | h) = Σ_true P(observed | true) P(true | h)`` (§7.6)."""

    composed: dict[str, dict[str, float]] = {}
    for slot, row in rows.items():
        observed_row: dict[str, float] = {}
        for observed in next(iter(channel.values())).keys() if channel else row.keys():
            observed_row[observed] = sum(
                channel[true][observed] * probability for true, probability in row.items()
            )
        composed[slot] = observed_row
    return composed


def _entropy(distribution: Mapping[str, float]) -> float:
    return -sum(p * log(p) for p in distribution.values() if p > 0)


def instrument_conditionals(
    instrument: CompiledInstrument,
    *,
    grader_reliability: float | None = None,
) -> dict[str, dict[str, float]]:
    """The grader-composed observed-outcome conditionals used everywhere (§7.2)."""

    channel = grader_channel_matrix(
        instrument.grader_policy, instrument.outcome_alphabet, reliability=grader_reliability
    )
    return compose_with_grader_channel(instrument.rows, channel)


def instrument_expected_information_gain(
    posterior: Mapping[str, float],
    instrument: CompiledInstrument,
    slot_map: Mapping[str, str],
    *,
    grader_reliability: float | None = None,
) -> float:
    """Actual hypothesis EIG in nats over the grader-composed conditionals (§7.2).

    ``slot_map`` maps episode hypothesis labels to card hypothesis slots. An
    item with identical predicted outcomes across every hypothesis receives
    zero EIG regardless of its marginal difficulty (§2.2).
    """

    conditionals = instrument_conditionals(instrument, grader_reliability=grader_reliability)
    labels = [label for label in posterior if label in slot_map]
    if len(labels) <= 1:
        return 0.0
    weights = {label: max(float(posterior[label]), 0.0) for label in labels}
    total = sum(weights.values())
    if total <= 0:
        return 0.0
    weights = {label: weight / total for label, weight in weights.items()}
    mixture: dict[str, float] = {outcome: 0.0 for outcome in instrument.outcome_alphabet}
    for label, weight in weights.items():
        row = conditionals[slot_map[label]]
        for outcome, probability in row.items():
            mixture[outcome] += weight * probability
    eig = 0.0
    for label, weight in weights.items():
        if weight <= 0:
            continue
        row = conditionals[slot_map[label]]
        kl = 0.0
        for outcome, probability in row.items():
            mixture_probability = mixture[outcome]
            if probability > 0 and mixture_probability > 0:
                kl += probability * log(probability / mixture_probability)
        eig += weight * kl
    return max(eig, 0.0)


def instrument_observation_likelihoods(
    instrument: CompiledInstrument,
    slot_map: Mapping[str, str],
    observed_outcome: str,
    *,
    grader_reliability: float | None = None,
) -> dict[str, float]:
    """``P(observed_outcome | hypothesis)`` per episode label — the same
    grader-composed conditionals candidate EIG scores with (§7.2)."""

    conditionals = instrument_conditionals(instrument, grader_reliability=grader_reliability)
    likelihoods: dict[str, float] = {}
    for label, slot in slot_map.items():
        likelihoods[label] = conditionals.get(slot, {}).get(observed_outcome, 0.0)
    return likelihoods


@dataclass(frozen=True)
class PredictiveInstrumentEig:
    """Predictive EIG of one candidate over held-out target instruments (§7.4)."""

    eig_nats: float
    prior_predictive_entropy: float
    expected_posterior_entropy: float
    target_count: int


def instrument_predictive_information_gain(
    posterior: Mapping[str, float],
    candidate: CompiledInstrument,
    candidate_slot_map: Mapping[str, str],
    targets: list[tuple[CompiledInstrument, Mapping[str, str]]],
    *,
    grader_reliability: float | None = None,
) -> PredictiveInstrumentEig:
    """How much observing the candidate's response is expected to sharpen
    predictions of the learner's responses to the held-out target instruments
    (§7.4, Adaptive Elicitation view).

        EIG_pred = H_prior - Σ_o m(o) · H_post(o)

    where ``m`` is the candidate's grader-composed prior-predictive mixture,
    ``H_prior``/``H_post`` sum predictive outcome entropy over the targets, and
    the posterior update uses the same conditionals replay applies (§7.2).
    All distributions are discrete, so the expectation is exact enumeration.
    A candidate with hypothesis-independent conditionals never moves the
    posterior and scores exactly zero.
    """

    labels = [label for label in posterior if label in candidate_slot_map]
    weights = {label: max(float(posterior[label]), 0.0) for label in labels}
    total = sum(weights.values())
    # Held-out means held out: the candidate never predicts itself.
    usable_targets = [(instrument, slot_map) for instrument, slot_map in targets if instrument is not candidate]
    if total <= 0 or len(labels) <= 1 or not usable_targets:
        return PredictiveInstrumentEig(0.0, 0.0, 0.0, len(usable_targets))
    belief = {label: weight / total for label, weight in weights.items()}

    target_conditionals = [
        (instrument_conditionals(instrument, grader_reliability=grader_reliability), slot_map, instrument)
        for instrument, slot_map in usable_targets
    ]

    def predictive_entropy(distribution: Mapping[str, float]) -> float:
        entropy_total = 0.0
        for conditionals, slot_map, instrument in target_conditionals:
            predictive: dict[str, float] = {outcome: 0.0 for outcome in instrument.outcome_alphabet}
            mass = 0.0
            for label, weight in distribution.items():
                slot = slot_map.get(label)
                if slot is None:
                    continue
                mass += weight
                for outcome, probability in conditionals[slot].items():
                    predictive[outcome] += weight * probability
            if mass <= 0:
                continue
            entropy_total += _entropy({outcome: value / mass for outcome, value in predictive.items()})
        return entropy_total

    prior_entropy = predictive_entropy(belief)

    candidate_conditionals = instrument_conditionals(candidate, grader_reliability=grader_reliability)
    mixture: dict[str, float] = {outcome: 0.0 for outcome in candidate.outcome_alphabet}
    for label, weight in belief.items():
        row = candidate_conditionals[candidate_slot_map[label]]
        for outcome, probability in row.items():
            mixture[outcome] += weight * probability

    expected_posterior_entropy = 0.0
    for outcome, outcome_probability in mixture.items():
        if outcome_probability <= 0:
            continue
        updated = {
            label: weight * candidate_conditionals[candidate_slot_map[label]].get(outcome, 0.0)
            for label, weight in belief.items()
        }
        updated_total = sum(updated.values())
        if updated_total <= 0:
            expected_posterior_entropy += outcome_probability * prior_entropy
            continue
        posterior_o = {label: value / updated_total for label, value in updated.items()}
        expected_posterior_entropy += outcome_probability * predictive_entropy(posterior_o)

    return PredictiveInstrumentEig(
        eig_nats=max(prior_entropy - expected_posterior_entropy, 0.0),
        prior_predictive_entropy=prior_entropy,
        expected_posterior_entropy=expected_posterior_entropy,
        target_count=len(usable_targets),
    )


def information_rate(eig_nats: float, expected_seconds: float, *, overhead_seconds: float) -> float:
    """Information per expected second with a conservative fixed overhead (§7.5)."""

    return eig_nats / max(overhead_seconds + max(expected_seconds, 0.0), 1.0)


def map_episode_labels_to_slots(
    instrument: CompiledInstrument,
    episode_labels: list[str],
    *,
    bindings: Mapping[str, Any] | None = None,
) -> dict[str, str] | None:
    """Episode hypothesis label -> card slot, or None when the card cannot
    model the episode's locked set (the card must then abstain, §9.4)."""

    from learnloop.services.probe_hypotheses import CONFUSES_PREFIX, MISCONCEPTION_PREFIX

    bindings = bindings or {}
    slots = set(instrument.rows)
    slot_map: dict[str, str] = {}
    bound_confusable = str(bindings.get("confusable_concept", "")) or None
    bound_misconception = str(bindings.get("misconception_id", "")) or None
    for label in episode_labels:
        if label in slots:
            slot_map[label] = label
            continue
        alias = instrument.slot_aliases.get(label)
        if alias is not None and alias in slots:
            # §2.2 honest identification: the instrument predicts identical
            # observations under this label and its alias target, so the label
            # shares that row (zero EIG between the two) instead of falling to
            # the broad open-set row.
            slot_map[label] = alias
            continue
        if label.startswith(CONFUSES_PREFIX):
            concept = label[len(CONFUSES_PREFIX) :]
            if "confuses_with_neighbor" in slots:
                if bound_confusable is None or bound_confusable == concept:
                    slot_map[label] = "confuses_with_neighbor"
                    continue
                episode_confusables = {
                    entry[len(CONFUSES_PREFIX) :]
                    for entry in episode_labels
                    if entry.startswith(CONFUSES_PREFIX)
                }
                if bound_confusable in episode_confusables and "other_or_unknown" in slots:
                    # The card measures one of the episode's live contrasts;
                    # this OTHER neighbor's confusion is simply not separable
                    # by this instrument, so the label abstains onto the broad
                    # open-set row (§2.2 honest identification). Returning None
                    # here would make every instrument ineligible on any LO
                    # with two or more confusables — blocking dialogue and
                    # contrast blocks on real vaults entirely.
                    slot_map[label] = "other_or_unknown"
                    continue
                # A card bound to a confusable that matches NONE of the
                # episode's live contrasts is the wrong instrument — it must
                # abstain entirely (§9.4).
                return None
            neighbor_alias = instrument.slot_aliases.get("confuses_with_neighbor")
            if neighbor_alias is not None and neighbor_alias in slots:
                # Family-declared identification: this instrument predicts the
                # same observations for a neighbor-confused learner as for the
                # alias target (confusion only shows on contrast surfaces).
                slot_map[label] = neighbor_alias
                continue
            if "other_or_unknown" in slots:
                slot_map[label] = "other_or_unknown"
                continue
            return None
        if label.startswith(MISCONCEPTION_PREFIX):
            misconception_id = label[len(MISCONCEPTION_PREFIX) :]
            if "holds_misconception" in slots and (
                bound_misconception is None or bound_misconception == misconception_id
            ):
                slot_map[label] = "holds_misconception"
                continue
            if "other_or_unknown" in slots:
                slot_map[label] = "other_or_unknown"
                continue
            return None
        if "other_or_unknown" in slots:
            # Template hypotheses the card does not bind fall to the broad
            # open-set row: the instrument abstains from diagnosing them (§9.4)
            # rather than fabricating a signature.
            slot_map[label] = "other_or_unknown"
            continue
        return None
    return slot_map


# --- Deterministic signature matcher (v1) ---------------------------------------


def classify_outcome(
    instrument: CompiledInstrument,
    *,
    rubric_score: int | None,
    attempt_type: str,
    fired_error_types: list[str],
) -> str:
    """Map one graded attempt onto the instrument's outcome alphabet.

    Signature matcher v1 is deterministic: it reads only the persisted grade,
    attempt type, and fired error events, so replay classifies identically.
    Outcomes whose signature cannot be matched fall to the systematic-error /
    weak classes rather than fabricating a diagnosis (§9.4 abstention).
    """

    alphabet = instrument.outcome_alphabet
    if attempt_type == "dont_know" and "unanswered" in alphabet:
        return "unanswered"
    fired = set(fired_error_types)
    score = int(rubric_score or 0)
    # Signature classes fire on their declared error types regardless of the
    # (low/mid) grade band; a high grade with a fired fatal never happens by
    # rubric construction.
    if score <= 3:
        for outcome, error_types in instrument.signature_error_types.items():
            if outcome in alphabet and fired & set(error_types):
                return outcome
    if score >= 4:
        return _first_present(
            alphabet,
            (
                "correct_target_reason",
                "correct_recall",
                "correct_prediction_reason",
                "correct_on_shifted",
                "valid_counterexample",
                "correct_commit_reason",
                "complete_correct_structure",
                "correct_strategy_complete",
                "integrated_correct",
                "correct",
                "high",
            ),
        )
    if score >= 2:
        return _first_present(
            alphabet,
            (
                "correct_weak_reason",
                "partial_recall",
                "correct_prediction_weak_reason",
                "partial_boundary",
                "correct_commit_weak_reason",
                "valid_prefix_first_invalid",
                "correct_strategy_execution_slip",
                "partial_integration",
                "partial",
                "mid",
            ),
        )
    if attempt_type == "dont_know":
        return _first_present(alphabet, ("unanswered", "other_systematic_error", "low"))
    return _first_present(
        alphabet,
        ("other_systematic_error", "no_viable_structure", "no_strategy", "incorrect", "low"),
    )


def _first_present(alphabet: tuple[str, ...], preferences: tuple[str, ...]) -> str:
    for preference in preferences:
        if preference in alphabet:
            return preference
    return alphabet[-1]


# --- Built-in family templates (§17 slice item 2) --------------------------------

CONTRAST_CONFUSABLE_V1 = ProbeFamilyTemplate(
    id="contrast_confusable",
    version=1,
    instrument_kind="contrast",
    observation_alphabet=(
        "correct_target_reason",
        "correct_weak_reason",
        "confusable_signature",
        "other_systematic_error",
        "hedge",
        "unanswered",
    ),
    hypothesis_slots=(
        "robust_initial_grasp",
        "confuses_with_neighbor",
        "surface_only",
        "unfamiliar",
        "other_or_unknown",
    ),
    applicable_knowledge_types=("concept", "conceptual", "definition", "procedure", "procedural", "principle", "fact", "skill"),
    target_slot="concept_a",
    contrast_slots=("confusable_b",),
    non_applicable_controls=("unrelated_concept_control",),
    expected_seconds_median=45.0,
    grader_policy="diagnostic_microprobe_v1",
)

# Ordinal-word rows every contrast_confusable card starts from; cards may
# override rows but stay within the vocabulary.
CONTRAST_CONFUSABLE_DEFAULT_ROWS: dict[str, dict[str, str]] = {
    "robust_initial_grasp": {
        "correct_target_reason": "dominant",
        "correct_weak_reason": "occasional",
        "confusable_signature": "negligible",
        "other_systematic_error": "negligible",
        "hedge": "negligible",
        "unanswered": "negligible",
    },
    "confuses_with_neighbor": {
        "correct_target_reason": "rare",
        "correct_weak_reason": "rare",
        "confusable_signature": "dominant",
        "other_systematic_error": "rare",
        "hedge": "rare",
        "unanswered": "rare",
    },
    "surface_only": {
        "correct_target_reason": "occasional",
        "correct_weak_reason": "dominant",
        "confusable_signature": "occasional",
        "other_systematic_error": "occasional",
        "hedge": "occasional",
        "unanswered": "rare",
    },
    "unfamiliar": {
        "correct_target_reason": "negligible",
        "correct_weak_reason": "negligible",
        "confusable_signature": "negligible",
        "other_systematic_error": "occasional",
        "hedge": "occasional",
        "unanswered": "likely",
    },
    "other_or_unknown": {
        "correct_target_reason": "negligible",
        "correct_weak_reason": "rare",
        "confusable_signature": "negligible",
        "other_systematic_error": "likely",
        "hedge": "occasional",
        "unanswered": "occasional",
    },
}


# §9.5 family library. Each template pairs with default ordinal rows so a
# parametric generator can mint an LO-bound card without free-form numerics.
# Slot aliases record which template hypotheses the instrument genuinely cannot
# separate — an honest zero-EIG identification, not a diagnosis (§2.2).

MINIMAL_RECALL_V1 = ProbeFamilyTemplate(
    id="minimal_recall",
    version=1,
    instrument_kind="minimal_recall",
    observation_alphabet=(
        "correct_recall",
        "partial_recall",
        "other_systematic_error",
        "hedge",
        "unanswered",
    ),
    hypothesis_slots=("robust_initial_grasp", "unfamiliar", "other_or_unknown"),
    # Minimal recall is a universal measurement pattern: applicable to every
    # knowledge type (empty tuple = unrestricted).
    applicable_knowledge_types=(),
    target_slot="target_facet",
    slot_aliases=(
        ("confuses_with_neighbor", "robust_initial_grasp"),
        ("recall_without_mechanism", "robust_initial_grasp"),
        ("schema_without_transfer", "robust_initial_grasp"),
        ("surface_only", "robust_initial_grasp"),
    ),
    expected_seconds_median=25.0,
    grader_policy="diagnostic_microprobe_v1",
)

MINIMAL_RECALL_DEFAULT_ROWS: dict[str, dict[str, str]] = {
    "robust_initial_grasp": {
        "correct_recall": "dominant",
        "partial_recall": "occasional",
        "other_systematic_error": "negligible",
        "hedge": "negligible",
        "unanswered": "negligible",
    },
    "unfamiliar": {
        "correct_recall": "negligible",
        "partial_recall": "rare",
        "other_systematic_error": "occasional",
        "hedge": "occasional",
        "unanswered": "likely",
    },
    "other_or_unknown": {
        "correct_recall": "rare",
        "partial_recall": "occasional",
        "other_systematic_error": "likely",
        "hedge": "occasional",
        "unanswered": "occasional",
    },
}

PREDICTION_V1 = ProbeFamilyTemplate(
    id="prediction_before_computation",
    version=1,
    instrument_kind="prediction",
    observation_alphabet=(
        "correct_prediction_reason",
        "correct_prediction_weak_reason",
        "incorrect_prediction",
        "other_systematic_error",
        "hedge",
        "unanswered",
    ),
    hypothesis_slots=(
        "robust_initial_grasp",
        "recall_without_mechanism",
        "unfamiliar",
        "other_or_unknown",
    ),
    applicable_knowledge_types=("concept", "conceptual", "definition", "principle", "procedure", "procedural", "skill"),
    target_slot="target_facet",
    slot_aliases=(
        ("confuses_with_neighbor", "robust_initial_grasp"),
        ("schema_without_transfer", "robust_initial_grasp"),
        ("surface_only", "recall_without_mechanism"),
    ),
    expected_seconds_median=40.0,
    grader_policy="diagnostic_microprobe_v1",
)

PREDICTION_DEFAULT_ROWS: dict[str, dict[str, str]] = {
    "robust_initial_grasp": {
        "correct_prediction_reason": "dominant",
        "correct_prediction_weak_reason": "occasional",
        "incorrect_prediction": "rare",
        "other_systematic_error": "negligible",
        "hedge": "negligible",
        "unanswered": "negligible",
    },
    "recall_without_mechanism": {
        "correct_prediction_reason": "rare",
        "correct_prediction_weak_reason": "occasional",
        "incorrect_prediction": "dominant",
        "other_systematic_error": "rare",
        "hedge": "occasional",
        "unanswered": "rare",
    },
    "unfamiliar": {
        "correct_prediction_reason": "negligible",
        "correct_prediction_weak_reason": "negligible",
        "incorrect_prediction": "occasional",
        "other_systematic_error": "occasional",
        "hedge": "occasional",
        "unanswered": "likely",
    },
    "other_or_unknown": {
        "correct_prediction_reason": "negligible",
        "correct_prediction_weak_reason": "rare",
        "incorrect_prediction": "occasional",
        "other_systematic_error": "likely",
        "hedge": "occasional",
        "unanswered": "occasional",
    },
}

PERTURBATION_V1 = ProbeFamilyTemplate(
    id="perturbation",
    version=1,
    instrument_kind="perturbation",
    observation_alphabet=(
        "correct_on_shifted",
        "correct_weak_reason",
        "surface_bound_error",
        "other_systematic_error",
        "hedge",
        "unanswered",
    ),
    hypothesis_slots=("robust_initial_grasp", "surface_only", "unfamiliar", "other_or_unknown"),
    # A shifted surface can test any knowledge type (empty tuple = unrestricted).
    applicable_knowledge_types=(),
    target_slot="target_facet",
    slot_aliases=(
        ("confuses_with_neighbor", "robust_initial_grasp"),
        ("recall_without_mechanism", "surface_only"),
        ("schema_without_transfer", "robust_initial_grasp"),
    ),
    expected_seconds_median=50.0,
    grader_policy="diagnostic_microprobe_v1",
)

PERTURBATION_DEFAULT_ROWS: dict[str, dict[str, str]] = {
    "robust_initial_grasp": {
        "correct_on_shifted": "dominant",
        "correct_weak_reason": "occasional",
        "surface_bound_error": "negligible",
        "other_systematic_error": "negligible",
        "hedge": "negligible",
        "unanswered": "negligible",
    },
    "surface_only": {
        "correct_on_shifted": "rare",
        "correct_weak_reason": "occasional",
        "surface_bound_error": "dominant",
        "other_systematic_error": "rare",
        "hedge": "occasional",
        "unanswered": "rare",
    },
    "unfamiliar": {
        "correct_on_shifted": "negligible",
        "correct_weak_reason": "negligible",
        "surface_bound_error": "rare",
        "other_systematic_error": "occasional",
        "hedge": "occasional",
        "unanswered": "likely",
    },
    "other_or_unknown": {
        "correct_on_shifted": "negligible",
        "correct_weak_reason": "rare",
        "surface_bound_error": "rare",
        "other_systematic_error": "likely",
        "hedge": "occasional",
        "unanswered": "occasional",
    },
}

MINIMAL_COUNTEREXAMPLE_V1 = ProbeFamilyTemplate(
    id="minimal_counterexample",
    version=1,
    instrument_kind="counterexample",
    observation_alphabet=(
        "valid_counterexample",
        "partial_boundary",
        "overgeneralization_signature",
        "other_systematic_error",
        "hedge",
        "unanswered",
    ),
    hypothesis_slots=(
        "robust_initial_grasp",
        "schema_without_transfer",
        "unfamiliar",
        "other_or_unknown",
    ),
    applicable_knowledge_types=("concept", "conceptual", "definition", "principle", "procedure", "procedural", "skill"),
    target_slot="target_facet",
    slot_aliases=(
        ("confuses_with_neighbor", "robust_initial_grasp"),
        ("recall_without_mechanism", "schema_without_transfer"),
        ("surface_only", "schema_without_transfer"),
    ),
    expected_seconds_median=60.0,
    grader_policy="diagnostic_microprobe_v1",
)

MINIMAL_COUNTEREXAMPLE_DEFAULT_ROWS: dict[str, dict[str, str]] = {
    "robust_initial_grasp": {
        "valid_counterexample": "dominant",
        "partial_boundary": "occasional",
        "overgeneralization_signature": "negligible",
        "other_systematic_error": "negligible",
        "hedge": "negligible",
        "unanswered": "negligible",
    },
    "schema_without_transfer": {
        "valid_counterexample": "rare",
        "partial_boundary": "occasional",
        "overgeneralization_signature": "dominant",
        "other_systematic_error": "rare",
        "hedge": "occasional",
        "unanswered": "rare",
    },
    "unfamiliar": {
        "valid_counterexample": "negligible",
        "partial_boundary": "negligible",
        "overgeneralization_signature": "rare",
        "other_systematic_error": "occasional",
        "hedge": "occasional",
        "unanswered": "likely",
    },
    "other_or_unknown": {
        "valid_counterexample": "negligible",
        "partial_boundary": "rare",
        "overgeneralization_signature": "rare",
        "other_systematic_error": "likely",
        "hedge": "occasional",
        "unanswered": "occasional",
    },
}

DIALOGUE_MICROPROBE_V1 = ProbeFamilyTemplate(
    id="dialogue_microprobe",
    version=1,
    instrument_kind="dialogue",
    observation_alphabet=(
        "correct_commit_reason",
        "correct_commit_weak_reason",
        "confusable_signature",
        "other_systematic_error",
        "hedge",
        "unanswered",
    ),
    hypothesis_slots=(
        "robust_initial_grasp",
        "surface_only",
        "confuses_with_neighbor",
        "unfamiliar",
        "other_or_unknown",
    ),
    applicable_knowledge_types=("concept", "conceptual", "definition", "principle", "procedure", "procedural", "fact", "skill"),
    target_slot="target_facet",
    contrast_slots=("confusable_b",),
    slot_aliases=(
        ("recall_without_mechanism", "surface_only"),
        ("schema_without_transfer", "surface_only"),
    ),
    # One dialogue block is one task: turns share this mass (§7.7).
    expected_seconds_median=30.0,
    total_task_evidence_mass=1.0,
    grader_policy="diagnostic_microprobe_v1",
)

DIALOGUE_MICROPROBE_DEFAULT_ROWS: dict[str, dict[str, str]] = {
    "robust_initial_grasp": {
        "correct_commit_reason": "dominant",
        "correct_commit_weak_reason": "occasional",
        "confusable_signature": "negligible",
        "other_systematic_error": "negligible",
        "hedge": "negligible",
        "unanswered": "negligible",
    },
    "surface_only": {
        "correct_commit_reason": "occasional",
        "correct_commit_weak_reason": "dominant",
        "confusable_signature": "rare",
        "other_systematic_error": "occasional",
        "hedge": "occasional",
        "unanswered": "rare",
    },
    "confuses_with_neighbor": {
        "correct_commit_reason": "rare",
        "correct_commit_weak_reason": "rare",
        "confusable_signature": "dominant",
        "other_systematic_error": "rare",
        "hedge": "rare",
        "unanswered": "rare",
    },
    "unfamiliar": {
        "correct_commit_reason": "negligible",
        "correct_commit_weak_reason": "negligible",
        "confusable_signature": "negligible",
        "other_systematic_error": "occasional",
        "hedge": "occasional",
        "unanswered": "likely",
    },
    "other_or_unknown": {
        "correct_commit_reason": "negligible",
        "correct_commit_weak_reason": "rare",
        "confusable_signature": "negligible",
        "other_systematic_error": "likely",
        "hedge": "occasional",
        "unanswered": "occasional",
    },
}

# --- Long-form / integrative families (§8.2, §9.5) --------------------------------
#
# One long-form response is ONE structured multi-channel instrument with a
# bounded task evidence mass, graded through the diagnostic_longform_v1
# channel. Each family declares ordered proof/derivation obligations
# (services/longform_trace.py): the generated rubric carries one criterion per
# obligation, so criterion-level grading evidence localizes the first invalid
# step deterministically.

PROOF_SKELETON_V1 = ProbeFamilyTemplate(
    id="proof_skeleton",
    version=1,
    instrument_kind="proof_skeleton",
    observation_alphabet=(
        "complete_correct_structure",
        "valid_prefix_first_invalid",
        "structure_without_justification",
        "no_viable_structure",
        "hedge",
        "unanswered",
    ),
    hypothesis_slots=(
        "robust_initial_grasp",
        "schema_without_transfer",
        "recall_without_mechanism",
        "unfamiliar",
        "other_or_unknown",
    ),
    applicable_knowledge_types=("proof", "derivation", "theorem", "principle", "concept", "conceptual"),
    target_slot="target_claim",
    slot_aliases=(
        ("surface_only", "recall_without_mechanism"),
    ),
    expected_seconds_median=300.0,
    total_task_evidence_mass=1.0,
    grader_policy="diagnostic_longform_v1",
)

PROOF_SKELETON_DEFAULT_ROWS: dict[str, dict[str, str]] = {
    "robust_initial_grasp": {
        "complete_correct_structure": "dominant",
        "valid_prefix_first_invalid": "occasional",
        "structure_without_justification": "rare",
        "no_viable_structure": "negligible",
        "hedge": "negligible",
        "unanswered": "negligible",
    },
    "schema_without_transfer": {
        "complete_correct_structure": "rare",
        "valid_prefix_first_invalid": "dominant",
        "structure_without_justification": "occasional",
        "no_viable_structure": "rare",
        "hedge": "occasional",
        "unanswered": "rare",
    },
    "recall_without_mechanism": {
        "complete_correct_structure": "negligible",
        "valid_prefix_first_invalid": "occasional",
        "structure_without_justification": "dominant",
        "no_viable_structure": "occasional",
        "hedge": "occasional",
        "unanswered": "rare",
    },
    "unfamiliar": {
        "complete_correct_structure": "negligible",
        "valid_prefix_first_invalid": "negligible",
        "structure_without_justification": "rare",
        "no_viable_structure": "likely",
        "hedge": "occasional",
        "unanswered": "likely",
    },
    "other_or_unknown": {
        "complete_correct_structure": "negligible",
        "valid_prefix_first_invalid": "occasional",
        "structure_without_justification": "likely",
        "no_viable_structure": "likely",
        "hedge": "occasional",
        "unanswered": "rare",
    },
}

DERIVATION_V1 = ProbeFamilyTemplate(
    id="derivation",
    version=1,
    instrument_kind="derivation",
    observation_alphabet=(
        "correct_strategy_complete",
        "correct_strategy_execution_slip",
        "wrong_strategy_selected",
        "no_strategy",
        "hedge",
        "unanswered",
    ),
    hypothesis_slots=(
        "robust_initial_grasp",
        "procedure_without_selection",
        "recall_without_mechanism",
        "unfamiliar",
        "other_or_unknown",
    ),
    applicable_knowledge_types=("procedure", "procedural", "skill", "derivation", "proof"),
    target_slot="target_result",
    slot_aliases=(
        ("surface_only", "recall_without_mechanism"),
    ),
    expected_seconds_median=300.0,
    total_task_evidence_mass=1.0,
    grader_policy="diagnostic_longform_v1",
)

# The separating family for procedure_without_selection (§9.5): choosing the
# wrong strategy while executing competently is its dominant signature —
# distinct from execution slips (recall_without_mechanism) and from robust
# performance.
DERIVATION_DEFAULT_ROWS: dict[str, dict[str, str]] = {
    "robust_initial_grasp": {
        "correct_strategy_complete": "dominant",
        "correct_strategy_execution_slip": "occasional",
        "wrong_strategy_selected": "rare",
        "no_strategy": "negligible",
        "hedge": "negligible",
        "unanswered": "negligible",
    },
    "procedure_without_selection": {
        "correct_strategy_complete": "occasional",
        "correct_strategy_execution_slip": "occasional",
        "wrong_strategy_selected": "dominant",
        "no_strategy": "rare",
        "hedge": "rare",
        "unanswered": "negligible",
    },
    "recall_without_mechanism": {
        "correct_strategy_complete": "rare",
        "correct_strategy_execution_slip": "dominant",
        "wrong_strategy_selected": "occasional",
        "no_strategy": "occasional",
        "hedge": "occasional",
        "unanswered": "rare",
    },
    "unfamiliar": {
        "correct_strategy_complete": "negligible",
        "correct_strategy_execution_slip": "negligible",
        "wrong_strategy_selected": "rare",
        "no_strategy": "likely",
        "hedge": "occasional",
        "unanswered": "likely",
    },
    "other_or_unknown": {
        "correct_strategy_complete": "negligible",
        "correct_strategy_execution_slip": "occasional",
        "wrong_strategy_selected": "occasional",
        "no_strategy": "likely",
        "hedge": "likely",
        "unanswered": "rare",
    },
}

EXTENDED_CASE_V1 = ProbeFamilyTemplate(
    id="extended_case",
    version=1,
    instrument_kind="extended_case",
    observation_alphabet=(
        "integrated_correct",
        "partial_integration",
        "surface_match_error",
        "other_systematic_error",
        "hedge",
        "unanswered",
    ),
    hypothesis_slots=(
        "robust_initial_grasp",
        "schema_without_transfer",
        "surface_only",
        "unfamiliar",
        "other_or_unknown",
    ),
    applicable_knowledge_types=(
        "concept", "conceptual", "principle", "procedure", "procedural", "skill", "case", "application",
    ),
    target_slot="target_case",
    slot_aliases=(
        ("recall_without_mechanism", "surface_only"),
    ),
    expected_seconds_median=360.0,
    total_task_evidence_mass=1.0,
    grader_policy="diagnostic_longform_v1",
)

EXTENDED_CASE_DEFAULT_ROWS: dict[str, dict[str, str]] = {
    "robust_initial_grasp": {
        "integrated_correct": "dominant",
        "partial_integration": "occasional",
        "surface_match_error": "negligible",
        "other_systematic_error": "negligible",
        "hedge": "negligible",
        "unanswered": "negligible",
    },
    "schema_without_transfer": {
        "integrated_correct": "rare",
        "partial_integration": "dominant",
        "surface_match_error": "occasional",
        "other_systematic_error": "occasional",
        "hedge": "occasional",
        "unanswered": "rare",
    },
    "surface_only": {
        "integrated_correct": "rare",
        "partial_integration": "occasional",
        "surface_match_error": "dominant",
        "other_systematic_error": "occasional",
        "hedge": "rare",
        "unanswered": "rare",
    },
    "unfamiliar": {
        "integrated_correct": "negligible",
        "partial_integration": "negligible",
        "surface_match_error": "rare",
        "other_systematic_error": "occasional",
        "hedge": "occasional",
        "unanswered": "likely",
    },
    "other_or_unknown": {
        "integrated_correct": "negligible",
        "partial_integration": "occasional",
        "surface_match_error": "rare",
        "other_systematic_error": "likely",
        "hedge": "occasional",
        "unanswered": "occasional",
    },
}

LONGFORM_FAMILY_IDS = (PROOF_SKELETON_V1.id, DERIVATION_V1.id, EXTENDED_CASE_V1.id)

# Ordered obligations per long-form family (§8.2): the generated rubric carries
# one criterion per obligation; longform_trace derives first-invalid-step
# localization, correct-prefix preservation, and dependent-downstream
# unassessability from the persisted criterion-level grading evidence.
LONGFORM_OBLIGATIONS: dict[str, list[dict[str, Any]]] = {
    PROOF_SKELETON_V1.id: [
        {"id": "ob_claim", "criterion_id": "claim_statement", "kind": "step", "depends_on": []},
        {"id": "ob_structure", "criterion_id": "skeleton_structure", "kind": "selection", "depends_on": ["ob_claim"]},
        {"id": "ob_justification", "criterion_id": "step_justification", "kind": "step", "depends_on": ["ob_structure"]},
        {"id": "ob_conclusion", "criterion_id": "conclusion", "kind": "step", "depends_on": ["ob_justification"]},
    ],
    DERIVATION_V1.id: [
        {"id": "ob_strategy", "criterion_id": "strategy_selection", "kind": "selection", "depends_on": []},
        {"id": "ob_setup", "criterion_id": "setup", "kind": "step", "depends_on": ["ob_strategy"]},
        {"id": "ob_execution", "criterion_id": "execution", "kind": "step", "depends_on": ["ob_setup"]},
        {"id": "ob_result", "criterion_id": "result", "kind": "step", "depends_on": ["ob_execution"]},
    ],
    EXTENDED_CASE_V1.id: [
        {"id": "ob_identify", "criterion_id": "identify_principle", "kind": "selection", "depends_on": []},
        {"id": "ob_apply", "criterion_id": "apply_to_case", "kind": "step", "depends_on": ["ob_identify"]},
        {"id": "ob_integrate", "criterion_id": "integrate_constraints", "kind": "step", "depends_on": ["ob_apply"]},
    ],
}


# Default per-slot instructional actions used by generated cards (§9.3).
DEFAULT_INSTRUCTIONAL_ACTIONS: dict[str, str] = {
    "robust_initial_grasp": "shifted_surface_practice",
    "surface_only": "varied_surface_practice",
    "recall_without_mechanism": "mechanism_instruction",
    "procedure_without_selection": "procedure_selection_practice",
    "schema_without_transfer": "transfer_practice",
    "confuses_with_neighbor": "contrastive_repair",
    "holds_misconception": "misconception_repair",
    "unfamiliar": "foundational_instruction",
    "other_or_unknown": "diagnostic_followup",
}

FAMILY_DEFAULT_ROWS: dict[str, dict[str, dict[str, str]]] = {
    CONTRAST_CONFUSABLE_V1.id: CONTRAST_CONFUSABLE_DEFAULT_ROWS,
    MINIMAL_RECALL_V1.id: MINIMAL_RECALL_DEFAULT_ROWS,
    PREDICTION_V1.id: PREDICTION_DEFAULT_ROWS,
    PERTURBATION_V1.id: PERTURBATION_DEFAULT_ROWS,
    MINIMAL_COUNTEREXAMPLE_V1.id: MINIMAL_COUNTEREXAMPLE_DEFAULT_ROWS,
    DIALOGUE_MICROPROBE_V1.id: DIALOGUE_MICROPROBE_DEFAULT_ROWS,
    PROOF_SKELETON_V1.id: PROOF_SKELETON_DEFAULT_ROWS,
    DERIVATION_V1.id: DERIVATION_DEFAULT_ROWS,
    EXTENDED_CASE_V1.id: EXTENDED_CASE_DEFAULT_ROWS,
}


def builtin_family_templates() -> list[ProbeFamilyTemplate]:
    return [
        CONTRAST_CONFUSABLE_V1,
        MINIMAL_RECALL_V1,
        PREDICTION_V1,
        PERTURBATION_V1,
        MINIMAL_COUNTEREXAMPLE_V1,
        DIALOGUE_MICROPROBE_V1,
        PROOF_SKELETON_V1,
        DERIVATION_V1,
        EXTENDED_CASE_V1,
    ]


def ensure_builtin_families(repository: Repository, *, clock: Clock | None = None) -> None:
    """Persist built-in family template versions as provisional (idempotent)."""

    for template in builtin_family_templates():
        if repository.probe_family_template(template.id, template.version) is not None:
            continue
        repository.upsert_probe_family_template(
            family_id=template.id,
            version=template.version,
            status="provisional",
            template=template.as_dict(),
            schema_hash=template.schema_hash(),
            clock=clock,
        )


# --- Family admission gate (§9.6, structural + planted-trace stages) -------------


@dataclass(frozen=True)
class PlantedTrial:
    """One synthetic response trace: which hypothesis was planted, and the
    outcome the real signature matcher recovered from the generated response."""

    planted_slot: str
    matched_outcome: str
    non_applicable_control: bool = False


@dataclass(frozen=True)
class FamilyGateResult:
    accepted: bool
    reasons: list[str]
    reverse_match_accuracy: dict[str, float]
    outcome_counts: dict[str, dict[str, float]]


def run_family_admission_gate(
    card: InstrumentCard,
    template: ProbeFamilyTemplate,
    trials: list[PlantedTrial],
    *,
    minimum_reverse_match: float = 0.6,
    minimum_pair_separation: float = 0.25,
    repository: Repository | None = None,
    clock: Clock | None = None,
) -> FamilyGateResult:
    """Admission gate for one family/card version (§9.6).

    Structural stage: the card must validate and compile. Separation stage:
    every pair of bound hypotheses must predict materially different outcome
    distributions (total-variation distance ≥ ``minimum_pair_separation``) for
    at least one member of each pair — hypotheses that answer similarly reject
    the family. Reverse-matching stage: planted-hypothesis trials must recover
    their planted slot as the likelihood argmax at ≥ ``minimum_reverse_match``.
    Non-applicable controls must NOT match the misconception signature (a
    simulator expressing the belief as generalized incompetence is caught here).

    Synthetic outcome counts are stored under ``evidence_source='synthetic_gate'``
    only — never merged with real learner calibration (§9.6).
    """

    reasons: list[str] = []
    instrument = validate_and_compile_card(card, template)

    for index, left in enumerate(card.hypotheses):
        for right in card.hypotheses[index + 1 :]:
            distance = 0.5 * sum(
                abs(instrument.rows[left][outcome] - instrument.rows[right][outcome])
                for outcome in template.observation_alphabet
            )
            if distance < minimum_pair_separation:
                reasons.append(
                    f"hypotheses {left} and {right} answer similarly "
                    f"(TV distance {distance:.3f} < {minimum_pair_separation})"
                )

    accuracy: dict[str, float] = {}
    counts: dict[str, dict[str, float]] = {slot: {} for slot in card.hypotheses}
    planted_totals: dict[str, int] = {}
    planted_hits: dict[str, int] = {}
    for trial in trials:
        if trial.non_applicable_control:
            # §9.6: a control outside the family's applicability must not fire
            # the misconception signature.
            signature_outcomes = set(instrument.signature_error_types)
            if trial.matched_outcome in signature_outcomes:
                reasons.append(
                    "non-applicable control fired the misconception signature "
                    f"({trial.matched_outcome}); the simulated belief overapplies"
                )
            continue
        if trial.planted_slot not in instrument.rows:
            reasons.append(f"planted trial references unknown hypothesis slot {trial.planted_slot}")
            continue
        counts.setdefault(trial.planted_slot, {})
        counts[trial.planted_slot][trial.matched_outcome] = (
            counts[trial.planted_slot].get(trial.matched_outcome, 0.0) + 1.0
        )
        planted_totals[trial.planted_slot] = planted_totals.get(trial.planted_slot, 0) + 1
        recovered = max(
            instrument.rows,
            key=lambda slot: instrument.rows[slot].get(trial.matched_outcome, 0.0),
        )
        if recovered == trial.planted_slot:
            planted_hits[trial.planted_slot] = planted_hits.get(trial.planted_slot, 0) + 1

    for slot, total in planted_totals.items():
        accuracy[slot] = planted_hits.get(slot, 0) / total
        if accuracy[slot] < minimum_reverse_match:
            reasons.append(
                f"planted {slot} responses fail reverse matching "
                f"({accuracy[slot]:.2f} < {minimum_reverse_match}); declared "
                "signatures cannot be reproduced"
            )

    accepted = not reasons
    if repository is not None:
        repository.upsert_probe_family_calibration(
            probe_family_template_id=template.id,
            probe_family_template_version=template.version,
            evidence_source="synthetic_gate",
            parameter_posterior={
                "outcome_counts": counts,
                "reverse_match_accuracy": accuracy,
                "accepted": accepted,
                "reasons": reasons,
            },
            sample_size=len(trials),
            grader_version=template.grader_policy,
            clock=clock,
        )
    return FamilyGateResult(
        accepted=accepted,
        reasons=reasons,
        reverse_match_accuracy=accuracy,
        outcome_counts=counts,
    )


# --- Real-learner hierarchical calibration (§9.7) --------------------------------


def record_real_observation_counts(
    repository: Repository,
    *,
    family_template_id: str,
    family_template_version: int,
    posterior_after: Mapping[str, float],
    slot_map: Mapping[str, str],
    observed_outcome: str,
    grader_version: str | None = None,
    practice_item_id: str | None = None,
    clock: Clock | None = None,
) -> None:
    """Fold one real observation into the family-version Dirichlet posterior.

    The true hypothesis is latent, so counts are posterior-weighted per slot
    (EM-style fractional counts). Stored under ``evidence_source='real_learner'``,
    strictly separate from synthetic gate statistics. When ``practice_item_id``
    is given the same fractional counts also land in that item's residual layer
    (§9.7), which shrinks toward the family posterior at read time.
    """

    slot_weights: dict[str, float] = {}
    for label, probability in posterior_after.items():
        slot = slot_map.get(label)
        if slot is None:
            continue
        slot_weights[slot] = slot_weights.get(slot, 0.0) + max(float(probability), 0.0)

    existing = repository.probe_family_calibration(
        family_template_id,
        family_template_version,
        evidence_source="real_learner",
        grader_version=grader_version,
    )
    counts: dict[str, dict[str, float]] = {}
    sample_size = 0
    if existing is not None:
        counts = {
            slot: dict(row)
            for slot, row in dict(existing["parameter_posterior"].get("outcome_counts", {})).items()
        }
        sample_size = int(existing["sample_size"])
    for slot, weight in slot_weights.items():
        row = counts.setdefault(slot, {})
        row[observed_outcome] = row.get(observed_outcome, 0.0) + weight
    effective = sum(sum(row.values()) for row in counts.values())
    repository.upsert_probe_family_calibration(
        probe_family_template_id=family_template_id,
        probe_family_template_version=family_template_version,
        evidence_source="real_learner",
        parameter_posterior={"outcome_counts": counts},
        sample_size=sample_size + 1,
        effective_sample_size=effective,
        grader_version=grader_version,
        clock=clock,
    )

    if practice_item_id is None:
        return
    item_existing = repository.probe_item_calibration(
        practice_item_id,
        family_template_id,
        family_template_version,
        evidence_source="real_learner",
        grader_version=grader_version,
    )
    item_counts: dict[str, dict[str, float]] = {}
    item_sample = 0
    if item_existing is not None:
        item_counts = {
            slot: dict(row)
            for slot, row in dict(item_existing["parameter_posterior"].get("outcome_counts", {})).items()
        }
        item_sample = int(item_existing["sample_size"])
    for slot, weight in slot_weights.items():
        row = item_counts.setdefault(slot, {})
        row[observed_outcome] = row.get(observed_outcome, 0.0) + weight
    item_effective = sum(sum(row.values()) for row in item_counts.values())
    repository.upsert_probe_item_calibration(
        practice_item_id=practice_item_id,
        probe_family_template_id=family_template_id,
        probe_family_template_version=family_template_version,
        evidence_source="real_learner",
        parameter_posterior={"outcome_counts": item_counts},
        sample_size=item_sample + 1,
        effective_sample_size=item_effective,
        grader_version=grader_version,
        clock=clock,
    )


def real_calibration_counts(
    repository: Repository,
    family_template_id: str,
    family_template_version: int,
    *,
    grader_version: str | None = None,
) -> dict[str, dict[str, float]] | None:
    calibration = repository.probe_family_calibration(
        family_template_id,
        family_template_version,
        evidence_source="real_learner",
        grader_version=grader_version,
    )
    if calibration is None:
        return None
    counts = calibration["parameter_posterior"].get("outcome_counts")
    return {slot: dict(row) for slot, row in dict(counts or {}).items()} or None


def shrunk_item_calibration_counts(
    repository: Repository,
    family_template_id: str,
    family_template_version: int,
    *,
    practice_item_id: str,
    grader_version: str | None = None,
    item_shrinkage_pseudo_count: float = 25.0,
) -> dict[str, dict[str, float]] | None:
    """Item-level Dirichlet counts shrunk toward the family posterior (§9.7).

    The family row contributes at most ``item_shrinkage_pseudo_count``
    observations of mass per hypothesis slot (its direction, capped); the
    item's own real counts add on top. With sparse item evidence the blend is
    dominated by the family posterior; item-specific deviation emerges only
    once the item's own evidence rivals the shrinkage mass. Real-learner
    evidence only — synthetic gate counts never feed compilation (§9.6).
    """

    family_counts = (
        real_calibration_counts(
            repository, family_template_id, family_template_version, grader_version=grader_version
        )
        or {}
    )
    item_calibration = repository.probe_item_calibration(
        practice_item_id,
        family_template_id,
        family_template_version,
        evidence_source="real_learner",
        grader_version=grader_version,
    )
    item_counts: dict[str, dict[str, float]] = {}
    if item_calibration is not None:
        item_counts = {
            slot: {k: max(float(v), 0.0) for k, v in dict(row).items()}
            for slot, row in dict(
                item_calibration["parameter_posterior"].get("outcome_counts", {})
            ).items()
        }

    blended: dict[str, dict[str, float]] = {}
    for slot in sorted(set(family_counts) | set(item_counts)):
        family_row = {k: max(float(v), 0.0) for k, v in dict(family_counts.get(slot) or {}).items()}
        item_row = dict(item_counts.get(slot) or {})
        family_total = sum(family_row.values())
        scale = (
            min(family_total, item_shrinkage_pseudo_count) / family_total
            if family_total > 0
            else 0.0
        )
        row: dict[str, float] = {}
        for outcome in sorted(set(family_row) | set(item_row)):
            row[outcome] = family_row.get(outcome, 0.0) * scale + item_row.get(outcome, 0.0)
        if row:
            blended[slot] = row
    return blended or None

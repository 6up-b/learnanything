from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from math import exp, log

from learnloop.clock import Clock, SystemClock, parse_utc
from learnloop.db.repositories import ActiveErrorEvent, Repository
from learnloop.services.mastery import display_mastery, initial_mastery_state, sigmoid
from learnloop.vault.models import LoadedVault, PracticeItem, Rubric

SCORE_BUCKETS = ("low", "mid", "high")
Outcome = tuple[str, str | None]


@dataclass(frozen=True)
class Hypothesis:
    label: str
    error_type: str | None = None
    source_error_event_id: str | None = None
    source_concept_id: str | None = None
    severity_at_entry: float = 0.0

    def as_record(self) -> dict[str, object]:
        return {
            "label": self.label,
            "error_type": self.error_type,
            "source_error_event_id": self.source_error_event_id,
            "source_concept_id": self.source_concept_id,
            "severity_at_entry": self.severity_at_entry,
        }


@dataclass(frozen=True)
class HypothesisSet:
    learning_object_id: str
    hypotheses: list[Hypothesis]
    prior: dict[str, float]
    id: str | None = None

    @property
    def known_error_types(self) -> list[str]:
        seen: list[str] = []
        for hypothesis in self.hypotheses:
            if hypothesis.error_type is not None and hypothesis.error_type not in seen:
                seen.append(hypothesis.error_type)
        return sorted(seen)

    @classmethod
    def from_record(cls, record: dict) -> "HypothesisSet":
        hypotheses = [
            Hypothesis(
                label=entry["label"],
                error_type=entry.get("error_type"),
                source_error_event_id=entry.get("source_error_event_id"),
                source_concept_id=entry.get("source_concept_id"),
                severity_at_entry=float(entry.get("severity_at_entry", 0.0)),
            )
            for entry in record.get("hypotheses", [])
        ]
        prior = {key: float(value) for key, value in record.get("prior", {}).items()}
        return cls(
            learning_object_id=record.get("learning_object_id", ""),
            hypotheses=hypotheses,
            prior=prior,
            id=record.get("id"),
        )


def build_hypothesis_set(
    vault: LoadedVault,
    repository: Repository,
    learning_object_id: str,
    *,
    clock: Clock | None = None,
) -> HypothesisSet:
    learning_object = vault.learning_objects[learning_object_id]
    now = (clock or SystemClock()).now().astimezone(UTC)
    algorithm_version = vault.config.algorithms.algorithm_version
    mastery = repository.mastery_state(learning_object_id) or initial_mastery_state(
        learning_object_id, algorithm_version, ""
    )
    mastery_mean = sigmoid(mastery.logit_mean)

    hypotheses: list[Hypothesis] = [
        Hypothesis(label="mastered", severity_at_entry=mastery_mean),
        Hypothesis(label="unfamiliar", severity_at_entry=1.0 - mastery_mean),
    ]
    prior: dict[str, float] = {
        "mastered": max(mastery_mean, 1e-6),
        "unfamiliar": max(1.0 - mastery_mean, 1e-6),
    }

    misconceptions: list[tuple[float, Hypothesis, float]] = []  # (decayed_weight, hypothesis, severity)
    seen_error_types: set[str] = set()

    for error in repository.active_errors_by_learning_object(learning_object_id):
        if error.error_type in seen_error_types:
            continue
        seen_error_types.add(error.error_type)
        weight = error.severity * _decay(error.created_at, now)
        misconceptions.append(
            (
                weight,
                Hypothesis(
                    label=f"misconception:{error.error_type}",
                    error_type=error.error_type,
                    source_error_event_id=error.id,
                    severity_at_entry=error.severity,
                ),
                error.severity,
            )
        )

    for neighbor_concept, neighbor_error in _neighbor_misconceptions(vault, repository, learning_object.concept, now):
        if neighbor_error.error_type in seen_error_types:
            continue
        seen_error_types.add(neighbor_error.error_type)
        weight = neighbor_error.severity * _decay(neighbor_error.created_at, now)
        misconceptions.append(
            (
                weight,
                Hypothesis(
                    label=f"misconception:{neighbor_error.error_type}",
                    error_type=neighbor_error.error_type,
                    source_error_event_id=neighbor_error.id,
                    source_concept_id=neighbor_concept,
                    severity_at_entry=neighbor_error.severity,
                ),
                neighbor_error.severity,
            )
        )

    # Cap at hypothesis_set_max_size; drop lowest-severity misconceptions first.
    max_size = vault.config.probe.hypothesis_set_max_size
    misconceptions.sort(key=lambda entry: (-entry[2], entry[1].error_type or ""))
    misconceptions = misconceptions[: max(0, max_size - len(hypotheses))]

    for decayed_weight, hypothesis, _severity in misconceptions:
        hypotheses.append(hypothesis)
        prior[hypothesis.label] = max(decayed_weight, 1e-6)

    total = sum(prior.values())
    prior = {label: value / total for label, value in prior.items()}
    return HypothesisSet(learning_object_id=learning_object_id, hypotheses=hypotheses, prior=prior)


def enter_probe(
    vault: LoadedVault,
    repository: Repository,
    learning_object_id: str,
    *,
    claimed_level: float | None = None,
    clock: Clock | None = None,
) -> HypothesisSet:
    algorithm_version = vault.config.algorithms.algorithm_version
    hypothesis_set = build_hypothesis_set(vault, repository, learning_object_id, clock=clock)
    probe_phase_id = f"probe_{learning_object_id}"
    hypothesis_set_id = repository.insert_hypothesis_set(
        learning_object_id=learning_object_id,
        probe_phase_id=probe_phase_id,
        hypotheses=[hypothesis.as_record() for hypothesis in hypothesis_set.hypotheses],
        prior=hypothesis_set.prior,
        algorithm_version=algorithm_version,
        clock=clock,
    )
    target = vault.config.probe.attempts_target_default
    if claimed_level is not None and claimed_level >= vault.config.probe.claim_skip_threshold:
        target = vault.config.probe.attempts_target_with_strong_claim
    from learnloop.clock import utc_now_iso

    now = utc_now_iso(clock)
    repository.upsert_probe_state(
        learning_object_id=learning_object_id,
        status="in_progress",
        algorithm_version=algorithm_version,
        probe_phase_id=probe_phase_id,
        hypothesis_set_id=hypothesis_set_id,
        probe_attempts_completed=0,
        probe_attempts_target=target,
        entered_at=now,
        clock=clock,
    )
    return HypothesisSet(
        learning_object_id=hypothesis_set.learning_object_id,
        hypotheses=hypothesis_set.hypotheses,
        prior=hypothesis_set.prior,
        id=hypothesis_set_id,
    )


def conditional_distribution(
    hypothesis: Hypothesis,
    *,
    fatal_error_ids: set[str],
    known_error_types: list[str],
) -> dict[Outcome, float]:
    error_types: list[str | None] = [None, *known_error_types]
    distribution: dict[Outcome, float] = {
        (bucket, error_type): 0.0 for bucket in SCORE_BUCKETS for error_type in error_types
    }
    low_outcomes = [("low", error_type) for error_type in error_types]

    if hypothesis.label == "mastered":
        distribution[("high", None)] = 0.75
        distribution[("mid", None)] = 0.20
        _spread(distribution, low_outcomes, 0.05)
        return distribution

    if hypothesis.label == "unfamiliar" or (
        hypothesis.error_type is not None and hypothesis.error_type not in fatal_error_ids
    ):
        distribution[("low", None)] += 0.45
        distribution[("mid", None)] = 0.30
        distribution[("high", None)] = 0.05
        low_known = [("low", error_type) for error_type in known_error_types]
        if low_known:
            _spread(distribution, low_known, 0.20)
        else:
            distribution[("low", None)] += 0.20
        return distribution

    # misconception:E where E probes the item (E is a fatal error of the item).
    error_type = hypothesis.error_type
    distribution[("low", error_type)] += 0.55
    distribution[("mid", error_type)] += 0.25
    distribution[("high", None)] += 0.05
    _spread(distribution, low_outcomes, 0.15)
    return distribution


def expected_information_gain(
    hypothesis_set: HypothesisSet,
    item: PracticeItem,
    rubric: Rubric | None = None,
) -> float:
    fatal_error_ids = _fatal_error_ids(item, rubric)
    known_error_types = hypothesis_set.known_error_types
    conditionals = {
        hypothesis.label: conditional_distribution(
            hypothesis, fatal_error_ids=fatal_error_ids, known_error_types=known_error_types
        )
        for hypothesis in hypothesis_set.hypotheses
    }
    prior = hypothesis_set.prior
    outcomes = next(iter(conditionals.values())).keys()
    mixture: dict[Outcome, float] = {outcome: 0.0 for outcome in outcomes}
    for hypothesis in hypothesis_set.hypotheses:
        weight = prior.get(hypothesis.label, 0.0)
        for outcome, probability in conditionals[hypothesis.label].items():
            mixture[outcome] += weight * probability

    eig = 0.0
    for hypothesis in hypothesis_set.hypotheses:
        weight = prior.get(hypothesis.label, 0.0)
        if weight <= 0:
            continue
        conditional = conditionals[hypothesis.label]
        kl = 0.0
        for outcome, probability in conditional.items():
            mixture_probability = mixture[outcome]
            if probability > 0 and mixture_probability > 0:
                kl += probability * log(probability / mixture_probability)
        eig += weight * kl
    return max(eig, 0.0)


def probe_eig_component(
    hypothesis_set: HypothesisSet,
    item: PracticeItem,
    rubric: Rubric | None = None,
) -> float:
    size = len(hypothesis_set.hypotheses)
    if size <= 1:
        return 0.0
    return expected_information_gain(hypothesis_set, item, rubric) / log(size)


def record_probe_attempt(
    vault: LoadedVault,
    repository: Repository,
    learning_object_id: str,
    *,
    clock: Clock | None = None,
) -> None:
    """Advance an in-progress probe after an attempt on its Learning Object.

    No-op when the Learning Object is not currently in a probe phase. The
    hypothesis set stays locked; only progress and completion are updated.
    """

    probe_state = repository.probe_state(learning_object_id)
    if probe_state is None or probe_state.status != "in_progress":
        return
    from learnloop.clock import utc_now_iso

    completed = probe_state.probe_attempts_completed + 1
    mastery = repository.mastery_state(learning_object_id)
    converged = (
        mastery is not None
        and display_mastery(mastery).mastery_variance <= vault.config.probe.variance_convergence_threshold
    )
    status = "in_progress"
    completed_at = None
    if completed >= probe_state.probe_attempts_target or converged:
        status = "complete"
        completed_at = utc_now_iso(clock)
    repository.upsert_probe_state(
        learning_object_id=learning_object_id,
        status=status,
        algorithm_version=vault.config.algorithms.algorithm_version,
        probe_phase_id=probe_state.probe_phase_id,
        hypothesis_set_id=probe_state.hypothesis_set_id,
        probe_attempts_completed=completed,
        probe_attempts_target=probe_state.probe_attempts_target,
        families_converged=["mastery"] if converged else probe_state.families_converged,
        entered_at=probe_state.entered_at,
        completed_at=completed_at,
        clock=clock,
    )


def _spread(distribution: dict[Outcome, float], outcomes: list[Outcome], mass: float) -> None:
    if not outcomes:
        return
    share = mass / len(outcomes)
    for outcome in outcomes:
        distribution[outcome] += share


def _fatal_error_ids(item: PracticeItem, rubric: Rubric | None = None) -> set[str]:
    effective_rubric = rubric or item.grading_rubric
    if effective_rubric is None:
        return set()
    return {fatal_error.id for fatal_error in effective_rubric.fatal_errors}


def _decay(created_at: str | None, now: datetime) -> float:
    created = parse_utc(created_at)
    if created is None:
        return 1.0
    days_since = max(0.0, (now - created).total_seconds() / 86400)
    return exp(-days_since / 7)


def _neighbor_misconceptions(
    vault: LoadedVault,
    repository: Repository,
    concept_id: str,
    now: datetime,
) -> list[tuple[str, ActiveErrorEvent]]:
    neighbors: list[str] = []
    for edge in vault.edges:
        if edge.relation_type != "confusable_with":
            continue
        if edge.source == concept_id:
            neighbors.append(edge.target)
        elif edge.target == concept_id:
            neighbors.append(edge.source)
    if not neighbors:
        return []

    mastery_states = repository.mastery_states()
    active_errors = repository.active_error_events()
    concept_to_los: dict[str, list[str]] = {}
    for lo_id, learning_object in vault.learning_objects.items():
        concept_to_los.setdefault(learning_object.concept, []).append(lo_id)

    results: list[tuple[str, ActiveErrorEvent]] = []
    for neighbor in neighbors:
        neighbor_los = concept_to_los.get(neighbor, [])
        neighbor_mastery = 0.0
        for lo_id in neighbor_los:
            state = mastery_states.get(lo_id)
            if state is not None:
                neighbor_mastery = max(neighbor_mastery, sigmoid(state.logit_mean))
        if neighbor_mastery < 0.7:
            continue
        neighbor_lo_set = set(neighbor_los)
        candidate_errors = [error for error in active_errors if error.learning_object_id in neighbor_lo_set]
        if not candidate_errors:
            continue
        most_severe = max(candidate_errors, key=lambda error: error.severity)
        results.append((neighbor, most_severe))
    return results

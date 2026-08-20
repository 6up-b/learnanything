from __future__ import annotations

from dataclasses import dataclass

from learnloop.db.repositories import Repository
from learnloop.diagnosis.probe_episodes import episode_posterior
from learnloop.diagnosis.probe_hypotheses import confused_concept
from learnloop.vault.models import LoadedVault


OBSERVED_CONFUSION_MIN_EVIDENCE = 2
OBSERVED_CONFUSION_MIN_PROBABILITY = 0.5
OBSERVED_CONFUSION_MIN_PRIOR_LIFT = 0.05


@dataclass(frozen=True)
class ObservedConfusableConcept:
    concept_id: str
    probability: float
    prior_probability: float
    evidence_count: int
    last_observed_at: str | None


def learner_observed_confusable_concepts(
    vault: LoadedVault,
    repository: Repository,
    learning_object_id: str,
) -> list[ObservedConfusableConcept]:
    """Return stable learner-specific confusions inferred from probe episodes.

    Authored concept relations remain immutable curriculum data. This projection
    only promotes a candidate after at least two qualifying observations, a
    posterior majority, and meaningful lift over its locked entry prior.
    """

    learning_object = vault.learning_objects.get(learning_object_id)
    if learning_object is None:
        return []

    totals: dict[str, dict[str, float | int | str | None]] = {}
    for episode in repository.probe_episodes_for_learning_object(learning_object_id):
        posterior = episode_posterior(vault, repository, episode)
        if posterior is None or posterior.qualifying_observations <= 0:
            continue
        weight = posterior.qualifying_observations
        observed_at = episode.completed_at or episode.updated_at or episode.created_at
        for hypothesis in posterior.hypothesis_set.hypotheses:
            concept_id = hypothesis.source_concept_id or confused_concept(hypothesis.label)
            if concept_id is None or concept_id not in vault.concepts or concept_id == learning_object.concept:
                continue
            probability = float(posterior.posterior.get(hypothesis.label, 0.0))
            prior_probability = float(posterior.prior.get(hypothesis.label, 0.0))
            row = totals.setdefault(
                concept_id,
                {
                    "posterior_mass": 0.0,
                    "prior_mass": 0.0,
                    "evidence_count": 0,
                    "last_observed_at": None,
                },
            )
            row["posterior_mass"] = float(row["posterior_mass"]) + probability * weight
            row["prior_mass"] = float(row["prior_mass"]) + prior_probability * weight
            row["evidence_count"] = int(row["evidence_count"]) + weight
            previous = row["last_observed_at"]
            if observed_at and (previous is None or observed_at > str(previous)):
                row["last_observed_at"] = observed_at

    observed: list[ObservedConfusableConcept] = []
    for concept_id, row in totals.items():
        evidence_count = int(row["evidence_count"])
        if evidence_count < OBSERVED_CONFUSION_MIN_EVIDENCE:
            continue
        probability = float(row["posterior_mass"]) / evidence_count
        prior_probability = float(row["prior_mass"]) / evidence_count
        if probability < OBSERVED_CONFUSION_MIN_PROBABILITY:
            continue
        if probability - prior_probability < OBSERVED_CONFUSION_MIN_PRIOR_LIFT:
            continue
        observed.append(
            ObservedConfusableConcept(
                concept_id=concept_id,
                probability=probability,
                prior_probability=prior_probability,
                evidence_count=evidence_count,
                last_observed_at=(str(row["last_observed_at"]) if row["last_observed_at"] else None),
            )
        )
    return sorted(observed, key=lambda row: (-row.probability, -row.evidence_count, row.concept_id))

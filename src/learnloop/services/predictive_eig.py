"""Predictive facet EIG (Adaptive Elicitation, arXiv 2504.04204).

The existing facet EIG measures entropy over *hypothesis labels*. The paper's
predictive view measures epistemic uncertainty as entropy over *unobserved
future answers*: the value of asking candidate item x is how much its answer
is expected to sharpen predictions of the learner's answers to a held-out
target set (the other items probing the same open facets).

    EIG_pred(x, f) = H_prior - sum_o m_x(o) * H_post(o)

where m_x(o) is the candidate's prior-predictive outcome distribution,
H_prior = sum_t H(P_t(. | pi)) over target items t, and H_post(o) uses the
posterior pi_o after observing outcome o on x. The paper simulates answers
autoregressively; here the conditionals are discrete and analytic
(score-bucket x error-type), so the expectation is exact enumeration — no
Monte Carlo. Cost per (candidate, facet) ~ |O|^2 * K * |H| ~ 10^4 float ops.

Properties (asserted in tests): a candidate not supporting the facet has
EIG_pred exactly 0 (its conditional is hypothesis-independent, so the
posterior never moves); for a single target, EIG_pred = I(Y_x; Y_t) <=
I(Y_x; H) — the hypothesis-label EIG — by the data-processing inequality.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import log

from learnloop.config import ProbeIRTConfig
from learnloop.services.facet_diagnostics import candidate_facet_support
from learnloop.services.probes import apply_facet_observation, facet_conditional_distribution, resolve_item_irt
from learnloop.vault.models import LoadedVault


@dataclass(frozen=True)
class TargetItemModel:
    """Precomputed static per-item inputs, built once per slate and reused
    across all candidates."""

    item_id: str
    support: frozenset[str]
    fatal_error_ids: frozenset[str]
    item_a: float
    item_b: float


@dataclass(frozen=True)
class PredictiveEigResult:
    eig_nats: float
    prior_predictive_entropy: float
    expected_posterior_entropy: float
    target_item_ids: list[str]


def build_target_models(
    vault: LoadedVault,
    *,
    learning_object_id: str,
    exclude_item_ids: set[str],
    facet_ids: set[str],
    cap: int,
) -> dict[str, list[TargetItemModel]]:
    """Per open facet: the LO's items whose candidate support probes the facet,
    excluding the source attempt's item, capped at ``cap``.

    The cap is filled by round-robin over (surface_family, practice_mode)
    strata rather than first-N by item id: an id-ordered cap lets one authored
    sibling family crowd out the whole held-out pool, so EIG would measure
    prediction improvement against near-duplicates of a single surface.
    """

    models: dict[str, TargetItemModel] = {}
    strata: dict[str, tuple[str, str]] = {}
    by_facet_all: dict[str, list[TargetItemModel]] = {facet_id: [] for facet_id in facet_ids}
    for item in sorted(vault.practice_items.values(), key=lambda entry: entry.id):
        if item.learning_object_id != learning_object_id or item.id in exclude_item_ids:
            continue
        support = candidate_facet_support(item)
        relevant = facet_ids & set(support)
        if not relevant:
            continue
        if item.id not in models:
            item_a, item_b, _probe_irt = resolve_item_irt(vault, item)
            rubric = vault.rubric_for_item(item)
            fatal_error_ids = (
                frozenset(fatal_error.id for fatal_error in rubric.fatal_errors)
                if rubric is not None
                else frozenset()
            )
            models[item.id] = TargetItemModel(
                item_id=item.id,
                support=frozenset(support),
                fatal_error_ids=fatal_error_ids,
                item_a=item_a,
                item_b=item_b,
            )
            strata[item.id] = (
                str(getattr(item, "surface_family", None) or ""),
                str(getattr(item, "practice_mode", None) or ""),
            )
        for facet_id in sorted(relevant):
            by_facet_all[facet_id].append(models[item.id])
    return {
        facet_id: _stratified_cap(candidates, strata, cap)
        for facet_id, candidates in by_facet_all.items()
    }


def _stratified_cap(
    candidates: list[TargetItemModel],
    strata: dict[str, tuple[str, str]],
    cap: int,
) -> list[TargetItemModel]:
    """Round-robin the cap across strata (deterministic: strata and members id-sorted)."""

    if len(candidates) <= cap:
        return list(candidates)
    grouped: dict[tuple[str, str], list[TargetItemModel]] = {}
    for model in candidates:
        grouped.setdefault(strata[model.item_id], []).append(model)
    queues = [grouped[key] for key in sorted(grouped)]
    picked: list[TargetItemModel] = []
    while len(picked) < cap and any(queues):
        for queue in queues:
            if queue and len(picked) < cap:
                picked.append(queue.pop(0))
    return picked


def predictive_facet_eig(
    hypothesis_marginal: dict[str, float],
    *,
    facet_id: str,
    candidate_support: set[str],
    candidate_fatal_error_ids: set[str],
    candidate_a: float,
    candidate_b: float,
    targets: list[TargetItemModel],
    candidate_item_id: str | None = None,
    irt: ProbeIRTConfig | None = None,
) -> PredictiveEigResult:
    prior = _normalized(hypothesis_marginal)
    usable_targets = [target for target in targets if target.item_id != candidate_item_id]
    target_ids = [target.item_id for target in usable_targets]
    if len(prior) <= 1 or not usable_targets:
        return PredictiveEigResult(0.0, 0.0, 0.0, target_ids)

    known_error_types = sorted(
        label.split(":", 1)[1] for label in prior if label.startswith("misconception:")
    )

    def _target_entropy(posterior: dict[str, float]) -> float:
        total = 0.0
        for target in usable_targets:
            predictive: dict[tuple[str, str | None], float] = {}
            for label, weight in posterior.items():
                conditional = facet_conditional_distribution(
                    label,
                    facet_id=facet_id,
                    candidate_facet_support=set(target.support),
                    fatal_error_ids=set(target.fatal_error_ids),
                    known_error_types=known_error_types,
                    item_a=target.item_a,
                    item_b=target.item_b,
                    irt=irt,
                )
                for outcome, probability in conditional.items():
                    predictive[outcome] = predictive.get(outcome, 0.0) + weight * probability
            total += _entropy(predictive)
        return total

    prior_entropy = _target_entropy(prior)
    if facet_id not in candidate_support:
        # Hypothesis-independent conditional: the posterior never moves.
        return PredictiveEigResult(0.0, prior_entropy, prior_entropy, target_ids)

    # Candidate prior-predictive mixture over its own outcomes.
    mixture: dict[tuple[str, str | None], float] = {}
    for label, weight in prior.items():
        conditional = facet_conditional_distribution(
            label,
            facet_id=facet_id,
            candidate_facet_support=candidate_support,
            fatal_error_ids=candidate_fatal_error_ids,
            known_error_types=known_error_types,
            item_a=candidate_a,
            item_b=candidate_b,
            irt=irt,
        )
        for outcome, probability in conditional.items():
            mixture[outcome] = mixture.get(outcome, 0.0) + weight * probability

    expected_posterior_entropy = 0.0
    for (bucket, error_type), outcome_probability in mixture.items():
        if outcome_probability <= 0.0:
            continue
        posterior = apply_facet_observation(
            prior,
            facet_id=facet_id,
            candidate_facet_support=candidate_support,
            fatal_error_ids=candidate_fatal_error_ids,
            observed_bucket=bucket,
            observed_error_type=error_type,
            item_a=candidate_a,
            item_b=candidate_b,
            irt=irt,
        )
        expected_posterior_entropy += outcome_probability * _target_entropy(posterior)

    return PredictiveEigResult(
        eig_nats=max(prior_entropy - expected_posterior_entropy, 0.0),
        prior_predictive_entropy=prior_entropy,
        expected_posterior_entropy=expected_posterior_entropy,
        target_item_ids=target_ids,
    )


def _normalized(marginal: dict[str, float]) -> dict[str, float]:
    positive = {label: max(0.0, float(value)) for label, value in marginal.items()}
    total = sum(positive.values())
    if total <= 0:
        return {}
    return {label: value / total for label, value in positive.items() if value > 0}


def _entropy(distribution: dict) -> float:
    entropy = 0.0
    for probability in distribution.values():
        if probability > 0:
            entropy -= probability * log(probability)
    return entropy

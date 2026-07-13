"""Cold-start hypothesis templates for diagnostic episodes.

Implements spec_probe_eig_redesign.md §6: authored coarse hypothesis templates
keyed by LO knowledge type, claims, confusables, and active misconceptions,
with reserved executable ``other_or_unknown`` open-set mass. Only the most
plausible three to five hypotheses are instantiated per episode; the resulting
set is locked for the episode's lifetime.

The generic (non-card) observation model for these labels lives here too so
incidental belief updates and the legacy-fallback instrument compile against
one executable definition per hypothesis.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC

from learnloop.clock import Clock, SystemClock, parse_utc
from learnloop.config import ProbeIRTConfig
from learnloop.db.repositories import Repository
from learnloop.services.mastery import (
    covering_learner_claim,
    initial_mastery_state_for_learning_object,
    sigmoid,
)
from learnloop.services.probes import Hypothesis, HypothesisSet, _decay, _graded_marginals
from learnloop.vault.models import LoadedVault, PracticeItem

# Canonical template labels (§6.1).
H_UNFAMILIAR = "unfamiliar"
H_SURFACE_ONLY = "surface_only"
H_RECALL_WITHOUT_MECHANISM = "recall_without_mechanism"
H_PROCEDURE_WITHOUT_SELECTION = "procedure_without_selection"
H_SCHEMA_WITHOUT_TRANSFER = "schema_without_transfer"
H_ROBUST = "robust_initial_grasp"
H_OTHER = "other_or_unknown"

CONFUSES_PREFIX = "confuses_with:"
MISCONCEPTION_PREFIX = "misconception:"


def confused_concept(label: str) -> str | None:
    if not label.startswith(CONFUSES_PREFIX):
        return None
    return label[len(CONFUSES_PREFIX) :]


@dataclass(frozen=True)
class ItemObservationContext:
    """Item-side flags that decide which latent gaps a generic item elicits.

    These are static, replay-deterministic item properties — never attempt-time
    state — so the same attempt always replays through the same conditional.
    """

    fresh_surface: bool = False
    probes_mechanism: bool = False
    probes_selection: bool = False
    probes_transfer: bool = False


def item_observation_context(item: PracticeItem) -> ItemObservationContext:
    mode = (item.practice_mode or "").lower()
    return ItemObservationContext(
        fresh_surface=(item.transfer_distance or 0.0) > 0.0,
        probes_mechanism=mode in ("explain", "teach_back", "derivation", "proof"),
        probes_selection=mode in ("worked_problem", "procedure_selection"),
        probes_transfer=(item.transfer_distance or 0.0) > 0.0,
    )


def generic_bucket_marginals(
    label: str,
    context: ItemObservationContext,
    *,
    item_a: float = 1.0,
    item_b: float = 0.0,
    irt: ProbeIRTConfig | None = None,
) -> dict[str, float]:
    """``P(score_bucket | hypothesis)`` for a generic (card-less) item.

    Each template anchors at the mastered ability unless the item elicits the
    gap the template names, in which case it anchors at the unfamiliar ability.
    ``other_or_unknown`` is deliberately broad — an even mixture of both
    anchors — so it stays executable (§6.3) without claiming a signature.
    """

    irt = irt or ProbeIRTConfig()

    def marginals(theta: float) -> dict[str, float]:
        low, mid, high = _graded_marginals(item_a * (theta - item_b), irt.cut_mid, irt.cut_high)
        return {"low": low, "mid": mid, "high": high}

    mastered = marginals(irt.theta_mastered)
    unfamiliar = marginals(irt.theta_unfamiliar)

    if label == H_UNFAMILIAR:
        return unfamiliar
    if label == H_OTHER:
        return {bucket: 0.5 * mastered[bucket] + 0.5 * unfamiliar[bucket] for bucket in mastered}
    elicited = (
        (label == H_SURFACE_ONLY and context.fresh_surface)
        or (label == H_RECALL_WITHOUT_MECHANISM and context.probes_mechanism)
        or (label == H_PROCEDURE_WITHOUT_SELECTION and context.probes_selection)
        or (label == H_SCHEMA_WITHOUT_TRANSFER and context.probes_transfer)
    )
    # robust_initial_grasp, misconception:*, confuses_with:*, and any gap the
    # item does not elicit all perform capably on a generic item — a
    # non-eliciting item earns no separation and clean success on it is not
    # evidence the gap is gone (same principle as registry beliefs in §3).
    return unfamiliar if elicited else mastered


@dataclass(frozen=True)
class _Candidate:
    hypothesis: Hypothesis
    weight: float


def build_episode_hypothesis_set(
    vault: LoadedVault,
    repository: Repository,
    learning_object_id: str,
    *,
    clock: Clock | None = None,
) -> HypothesisSet:
    """Instantiate the locked cold-start set for one episode (§6.1/§6.2).

    Deterministic in the (vault, repository) snapshot: candidates are scored by
    plausibility, the top ``hypothesis_set_max_size`` are kept, and the
    reserved open-set mass is appended last.
    """

    from learnloop.clock import utc_now_iso

    learning_object = vault.learning_objects[learning_object_id]
    now = (clock or SystemClock()).now().astimezone(UTC)
    mastery = repository.mastery_state(learning_object_id) or initial_mastery_state_for_learning_object(
        vault,
        repository,
        learning_object_id,
        utc_now_iso(clock),
    )
    mastery_mean = sigmoid(mastery.logit_mean)
    claim = covering_learner_claim(vault, repository, learning_object_id)
    claimed_level = float(claim["claimed_level"]) if claim is not None else None
    knowledge_type = (learning_object.knowledge_type or "").lower()

    candidates: list[_Candidate] = [
        _Candidate(Hypothesis(label=H_UNFAMILIAR, severity_at_entry=1.0 - mastery_mean), max(1.0 - mastery_mean, 0.05)),
        _Candidate(Hypothesis(label=H_ROBUST, severity_at_entry=mastery_mean), max(mastery_mean, 0.05)),
    ]

    # Surface-only knowledge is plausible whenever there is any prior signal of
    # success (claim or observed evidence) that has not been transfer-tested.
    prior_signal = max(claimed_level or 0.0, mastery_mean if mastery.last_evidence_at is not None else 0.0)
    if prior_signal > 0.0:
        candidates.append(
            _Candidate(Hypothesis(label=H_SURFACE_ONLY, severity_at_entry=prior_signal), 0.6 * prior_signal + 0.1)
        )

    # Token matching handles compound knowledge types (conceptual_procedural,
    # theorem_application) that real vaults use.
    from learnloop.services.probe_families import knowledge_type_tokens

    tokens = knowledge_type_tokens(knowledge_type)
    if tokens & {"concept", "conceptual", "definition", "principle", "fact", "theorem"}:
        candidates.append(_Candidate(Hypothesis(label=H_RECALL_WITHOUT_MECHANISM), 0.3))
    if tokens & {"procedure", "procedural", "skill"}:
        candidates.append(_Candidate(Hypothesis(label=H_PROCEDURE_WITHOUT_SELECTION), 0.3))
    if mastery_mean >= 0.6 or (claimed_level or 0.0) >= 0.6:
        candidates.append(_Candidate(Hypothesis(label=H_SCHEMA_WITHOUT_TRANSFER), 0.25))

    for neighbor in _confusable_neighbors(vault, learning_object):
        candidates.append(
            _Candidate(
                Hypothesis(label=f"{CONFUSES_PREFIX}{neighbor}", source_concept_id=neighbor),
                0.35,
            )
        )

    seen_misconception_ids: set[str] = set()
    for record in repository.misconceptions_for_learning_object(
        learning_object_id, statuses=("active", "resolving")
    ):
        if record.id in seen_misconception_ids:
            continue
        seen_misconception_ids.add(record.id)
        weight = record.severity * _decay(record.updated_at or record.created_at, now)
        candidates.append(
            _Candidate(
                Hypothesis(
                    label=f"{MISCONCEPTION_PREFIX}{record.id}",
                    misconception_id=record.id,
                    severity_at_entry=record.severity,
                ),
                max(weight, 0.05),
            )
        )

    # Deduplicate by label keeping the strongest weight, then keep the most
    # plausible `hypothesis_set_max_size` (§6.1: three to five).
    by_label: dict[str, _Candidate] = {}
    for candidate in candidates:
        existing = by_label.get(candidate.hypothesis.label)
        if existing is None or candidate.weight > existing.weight:
            by_label[candidate.hypothesis.label] = candidate
    ranked = sorted(by_label.values(), key=lambda c: (-c.weight, c.hypothesis.label))
    max_size = vault.config.probe.hypothesis_set_max_size
    kept = ranked[:max_size]

    open_set_prior = vault.config.probe.episode.open_set_prior
    hypotheses = [candidate.hypothesis for candidate in kept]
    weights = {candidate.hypothesis.label: candidate.weight for candidate in kept}
    total = sum(weights.values())
    prior = {label: (1.0 - open_set_prior) * weight / total for label, weight in weights.items()}

    hypotheses.append(Hypothesis(label=H_OTHER))
    prior[H_OTHER] = open_set_prior

    return HypothesisSet(learning_object_id=learning_object_id, hypotheses=hypotheses, prior=prior)


def _confusable_neighbors(vault: LoadedVault, learning_object) -> list[str]:
    """Confusable concept ids from the LO's authored list plus concept edges."""

    neighbors: list[str] = list(learning_object.confusables)
    for edge in vault.edges:
        if edge.relation_type != "confusable_with":
            continue
        if edge.source == learning_object.concept and edge.target not in neighbors:
            neighbors.append(edge.target)
        elif edge.target == learning_object.concept and edge.source not in neighbors:
            neighbors.append(edge.source)
    return neighbors


def strong_prior_claim(
    vault: LoadedVault,
    repository: Repository,
    learning_object_id: str,
) -> bool:
    """Whether the learner made a strong covering claim (§11 fast-path input)."""

    episode_config = vault.config.probe.episode
    if not episode_config.fast_path_enabled:
        return False
    claim = covering_learner_claim(vault, repository, learning_object_id)
    if claim is None:
        return False
    return float(claim["claimed_level"]) >= episode_config.fast_path_claim_threshold

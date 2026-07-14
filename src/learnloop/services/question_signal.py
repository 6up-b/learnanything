"""Learner questions as observations on facet hypothesis marginals.

Adaptive-elicitation framing (arXiv:2504.04204): the per-facet hypothesis
marginal is the belief state over the latent learner; graded attempts are one
observation channel and learner-initiated tutor questions are another. A
substantive (prerequisite/mechanism/strategy) question about a facet is
evidence AGAINST ``facet_solid`` — learners rarely ask how something works
when they hold it solidly. Folding that into the marginal at decision time
lets the existing facet-EIG machinery aim follow-up probes at what the
learner actually asked about, with no separate targeting mechanism.

Design constraints:

- **Read-side only.** Nothing here writes derived state. ``question_events``
  persist, so every adjustment is a pure function of persisted rows; replay /
  rebuild (which folds only ``practice_attempts``) can never drift from a
  decision made through this module.
- **Resolution requires success.** A question stays live until the learner
  lands *successful* attempt evidence on that facet after asking. A failed
  attempt on the questioned facet confirms the confusion rather than
  resolving it, and the attempt that triggered the current decision is
  excluded so it cannot absorb its own mid-attempt questions.
- **Self-calibrating strength.** The likelihood ratio is resolved from the
  learner's own question->failure lift when enough questioned attempts exist,
  else the single config fallback applies (same absolute-fallback pattern as
  ``signal_quantiles``). No per-question-type coefficient table.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import timedelta
from typing import Any

from learnloop.clock import Clock, parse_utc, utc_now_iso
from learnloop.config import TutorPromotionConfig, TutorQAConfig
from learnloop.db.repositories import FacetUncertaintyState, Repository
from learnloop.services.facet_diagnostics import entropy, facet_state_label, normalize_distribution
from learnloop.services.facet_state_reader import (
    facet_recall_states_for_lo,
    facet_uncertainty_states_for_lo,
)
from learnloop.vault.models import LoadedVault

# Substantive question types (mirrors tutor_qa.HINT_EQUIVALENT_TYPES, which is
# practice-context-only as a *hint* marker; as *evidence* the same types count
# in the feedback context too).
SUBSTANTIVE_QUESTION_TYPES = frozenset({"prerequisite", "mechanism", "strategy"})

# Same bounds as the display bump in facet_diagnostics: at most this many
# recent unresolved questions per facet act as observations, within the window.
QUESTION_SIGNAL_WINDOW_DAYS = 7
MAX_QUESTION_OBSERVATIONS_PER_FACET = 3

# Frontier natures (spec §3 G2): a gap declared while probing a transfer / edge /
# what-if boundary must NOT degrade a facet the diagnostics already call solid —
# it marks the learner's frontier boundary, not core decay.
_FRONTIER_NATURES = frozenset({"transfer", "edge_case", "what_if"})

# Odds-ratio guards for the empirical calibration: failure rates are clamped
# away from 0/1 before forming odds, and the resolved ratio is kept in
# (0.05, 1.0] so question evidence can never certify absence outright nor
# raise P(facet_solid).
_RATE_CLAMP = (0.05, 0.95)
_RATIO_FLOOR = 0.05
_SMOOTHING_PSEUDO_COUNT = 2.0


@dataclass(frozen=True)
class ResolvedQuestionLikelihood:
    """L(ask | facet_solid) / L(ask | not solid), with provenance."""

    value: float
    source: str  # "empirical" | "absolute_fallback"
    sample_size: int  # questioned attempts backing the empirical estimate
    questioned_failure_rate: float | None
    base_failure_rate: float | None
    absolute_fallback: float

    def as_dict(self) -> dict[str, Any]:
        return {
            "value": self.value,
            "source": self.source,
            "sample_size": self.sample_size,
            "questioned_failure_rate": self.questioned_failure_rate,
            "base_failure_rate": self.base_failure_rate,
            "absolute_fallback": self.absolute_fallback,
        }


@dataclass(frozen=True)
class QuestionSignal:
    """Unresolved substantive questions for one LO, grouped for consumers."""

    events_by_facet: dict[str, list[dict[str, Any]]]
    unfaceted_events: list[dict[str, Any]]
    likelihood: ResolvedQuestionLikelihood
    # Second read-side channel (spec §3 G2 + §4b): gap-declared promotions
    # (``question_promotions`` intent='gap') act as unresolved-question
    # observations on their attributed facets, independent of question_type, with
    # their OWN empirically-fit likelihood slot. Kept separate from
    # ``events_by_facet`` so the ordinary substantive channel and its consumers
    # (followups diagnostic focus) are untouched.
    gap_events_by_facet: dict[str, list[dict[str, Any]]] = field(default_factory=dict)
    gap_likelihood: ResolvedQuestionLikelihood | None = None

    @property
    def facets(self) -> list[str]:
        return sorted(self.events_by_facet)

    def context_entries(self, *, max_entries: int = 6, excerpt_chars: int = 240) -> list[dict[str, Any]]:
        """Compact question context for diagnostic_focus / authoring prompts."""

        events = sorted(
            {event["id"]: event for facet_events in self.events_by_facet.values() for event in facet_events}.values(),
            key=lambda event: event["created_at"],
        )
        events = [*events, *self.unfaceted_events][:max_entries]
        return [
            {
                "question_event_id": event["id"],
                "question_type": event.get("question_type"),
                "context": event.get("context"),
                "facets": list(event.get("facets", [])),
                "question_excerpt": " ".join(str(event.get("question_md", "")).split())[:excerpt_chars],
                "asked_at": event.get("created_at"),
            }
            for event in events
        ]


def resolve_question_likelihood(repository: Repository, config: TutorQAConfig) -> ResolvedQuestionLikelihood:
    """Calibrate the solid-likelihood ratio from the learner's own history.

    Empirical form: among graded attempts that were preceded by a substantive
    question on the same practice item (the question's target attempt), how
    much more often does the attempt fail than the base rate? The failure
    odds ratio approximates L(ask | not solid) / L(ask | solid); its inverse
    is the ratio applied to ``facet_solid``. Below
    ``question_likelihood_min_samples`` questioned attempts the config
    constant applies unchanged (``source="absolute_fallback"``).
    """

    fallback = float(config.question_solid_likelihood_ratio)
    questioned: dict[str, bool] = {}
    for event in repository.question_events(context="practice", answer_status="answered"):
        if event.get("question_type") not in SUBSTANTIVE_QUESTION_TYPES:
            continue
        item_id = event.get("practice_item_id")
        if not item_id:
            continue
        target = _first_attempt_at_or_after(repository, item_id, event["created_at"])
        if target is not None:
            questioned.setdefault(str(target["id"]), _attempt_failed(target))
    return _empirical_solid_likelihood(
        questioned, repository, min_samples=int(config.question_likelihood_min_samples), fallback=fallback
    )


def resolve_gap_declaration_likelihood(
    repository: Repository, config: TutorPromotionConfig
) -> ResolvedQuestionLikelihood:
    """Calibrate the gap-declaration solid-likelihood ratio (spec §3 G2).

    Mirrors ``resolve_question_likelihood`` but conditions the questioned sample
    on **gap-declared** promotions (``question_promotions`` intent='gap') rather
    than substantive question_types: among graded attempts preceded by a gap
    declaration on the same practice item, how much more often does the attempt
    fail than the base rate. Below ``gap_declaration_likelihood_min_samples``
    gap-declared attempts the config ``gap_declaration_solid_likelihood_ratio``
    applies unchanged — a stronger prior bump than an ordinary ask because a
    declaration is explicit, not inferred from question type.
    """

    fallback = float(config.gap_declaration_solid_likelihood_ratio)
    questioned: dict[str, bool] = {}
    for promotion in repository.question_promotions():
        if promotion.get("intent") != "gap":
            continue
        event = repository.question_event(str(promotion["question_event_id"]))
        if event is None:
            continue
        item_id = event.get("practice_item_id")
        created_at = event.get("created_at")
        if not item_id or not created_at:
            continue
        target = _first_attempt_at_or_after(repository, item_id, created_at)
        if target is not None:
            questioned.setdefault(str(target["id"]), _attempt_failed(target))
    return _empirical_solid_likelihood(
        questioned,
        repository,
        min_samples=int(config.gap_declaration_likelihood_min_samples),
        fallback=fallback,
    )


def _empirical_solid_likelihood(
    questioned: dict[str, bool],
    repository: Repository,
    *,
    min_samples: int,
    fallback: float,
) -> ResolvedQuestionLikelihood:
    """Shared Laplace-smoothed failure-lift → solid-likelihood ratio.

    Both the ordinary substantive channel and the gap-declaration channel form
    the same statistic: the questioned-attempt failure odds relative to the base
    failure odds, inverted, clamped to ``(_RATIO_FLOOR, 1.0]``. Below
    ``min_samples`` the caller's config constant applies unchanged.
    """

    sample_size = len(questioned)
    if sample_size < min_samples:
        return ResolvedQuestionLikelihood(
            value=fallback,
            source="absolute_fallback",
            sample_size=sample_size,
            questioned_failure_rate=None,
            base_failure_rate=None,
            absolute_fallback=fallback,
        )
    base_rate = _base_failure_rate(repository)
    questioned_failures = sum(1 for failed in questioned.values() if failed)
    # Laplace-style shrinkage toward the base rate so a thin questioned sample
    # cannot swing the ratio to its clamps.
    questioned_rate = _clamped_rate(
        questioned_failures + _SMOOTHING_PSEUDO_COUNT * base_rate,
        sample_size + _SMOOTHING_PSEUDO_COUNT,
    )
    odds_ratio = (questioned_rate / (1.0 - questioned_rate)) / (base_rate / (1.0 - base_rate))
    value = min(1.0, max(_RATIO_FLOOR, 1.0 / odds_ratio)) if odds_ratio > 0 else fallback
    return ResolvedQuestionLikelihood(
        value=value,
        source="empirical",
        sample_size=sample_size,
        questioned_failure_rate=questioned_rate,
        base_failure_rate=base_rate,
        absolute_fallback=fallback,
    )


def _base_failure_rate(repository: Repository) -> float:
    base_n = 0
    base_failures = 0
    for learning_object_id in repository.learning_object_ids_with_attempts():
        for attempt in repository.list_attempts_by_learning_object(learning_object_id):
            base_n += 1
            if _attempt_failed(attempt):
                base_failures += 1
    return _clamped_rate(base_failures, base_n)


def apply_question_observation(
    hypothesis_marginal: dict[str, float],
    *,
    solid_likelihood_ratio: float,
) -> dict[str, float]:
    """One substantive-question observation on a facet's hypothesis marginal.

    Multiplies every ``facet_solid:*`` label by the likelihood ratio and
    renormalizes; relative mass among absent/misconception hypotheses is
    untouched (the question says "not solid", not which failure mode).
    """

    prior = normalize_distribution(hypothesis_marginal)
    if not prior:
        return prior
    updated = {
        label: probability * (solid_likelihood_ratio if label.startswith("facet_solid:") else 1.0)
        for label, probability in prior.items()
    }
    return normalize_distribution(updated)


def collect_question_signal(
    vault: LoadedVault,
    repository: Repository,
    learning_object_id: str,
    *,
    exclude_attempt_id: str | None = None,
    clock: Clock | None = None,
) -> QuestionSignal:
    """Unresolved substantive questions mapped to one LO's facets.

    A question is unresolved while no *successful* attempt evidence on that
    facet has landed after it (``exclude_attempt_id`` — the attempt whose
    decision we are making — never resolves). Questions whose classification
    matched no canonical facet are kept separately: they still carry text
    context even though they cannot adjust a marginal.
    """

    likelihood = resolve_question_likelihood(repository, vault.config.tutor_qa)
    gap_likelihood = resolve_gap_declaration_likelihood(repository, vault.config.tutor_promotion)
    now = parse_utc(utc_now_iso(clock))
    since = (now - timedelta(days=QUESTION_SIGNAL_WINDOW_DAYS)).strftime("%Y-%m-%dT%H:%M:%SZ")
    successes = _facet_success_times(
        vault, repository, learning_object_id, exclude_attempt_id=exclude_attempt_id
    )
    events_by_facet: dict[str, list[dict[str, Any]]] = {}
    unfaceted: list[dict[str, Any]] = []
    for event in repository.question_events(since=since, answer_status="answered"):
        if event.get("question_type") not in SUBSTANTIVE_QUESTION_TYPES:
            continue
        if not _event_maps_to_lo(vault, event, learning_object_id):
            continue
        facets = sorted({vault.canonical_facet_id(str(facet)) for facet in event.get("facets", [])})
        if not facets:
            unfaceted.append(event)
            continue
        for facet in facets:
            resolved_at = successes.get(facet)
            if resolved_at is not None and resolved_at > event["created_at"]:
                continue
            events_by_facet.setdefault(facet, []).append(event)
    gap_events_by_facet = _collect_gap_declarations(
        vault, repository, learning_object_id, since=since, successes=successes
    )
    return QuestionSignal(
        events_by_facet=events_by_facet,
        unfaceted_events=unfaceted,
        likelihood=likelihood,
        gap_events_by_facet=gap_events_by_facet,
        gap_likelihood=gap_likelihood,
    )


def _collect_gap_declarations(
    vault: LoadedVault,
    repository: Repository,
    learning_object_id: str,
    *,
    since: str,
    successes: dict[str, str],
) -> dict[str, list[dict[str, Any]]]:
    """Gap-declared promotions mapped to this LO's attributed facets.

    Mirrors the ordinary channel's window / LO-mapping / success-resolution, but
    the observation targets are the promotion's ``attributed_facets`` (not the
    event's classified facets) and the type filter is dropped — a declaration is
    explicit. Nature-based skip: a transfer/edge_case/what_if gap on a facet the
    diagnostics currently call ``solid`` is the learner's frontier boundary and
    must NOT degrade core state, so it is skipped for that facet.
    """

    promotions = [p for p in repository.question_promotions() if p.get("intent") == "gap"]
    if not promotions:
        return {}
    uncertainty_states = {
        state.facet_id: state
        for state in facet_uncertainty_states_for_lo(vault, repository, learning_object_id)
    }
    recall_states = {
        state.facet_id: state
        for state in facet_recall_states_for_lo(vault, repository, learning_object_id)
        if state.practice_item_id is None
    }
    min_mass = vault.config.recall_coverage.min_facet_evidence_mass
    gap_events_by_facet: dict[str, list[dict[str, Any]]] = {}
    for promotion in promotions:
        event = repository.question_event(str(promotion["question_event_id"]))
        if event is None or event.get("answer_status") != "answered":
            continue
        created_at = event.get("created_at")
        if not created_at or created_at < since:
            continue
        if not _event_maps_to_lo(vault, event, learning_object_id):
            continue
        skip_solid = promotion.get("question_nature") in _FRONTIER_NATURES
        facets = sorted(
            {vault.canonical_facet_id(str(facet)) for facet in promotion.get("attributed_facets", [])}
        )
        for facet in facets:
            resolved_at = successes.get(facet)
            if resolved_at is not None and resolved_at > created_at:
                continue
            if skip_solid and facet_state_label(
                facet, uncertainty_states.get(facet), recall_states.get(facet), min_mass
            ) == "solid":
                continue
            gap_events_by_facet.setdefault(facet, []).append(event)
    return gap_events_by_facet


def question_adjusted_uncertainty_states(
    vault: LoadedVault,
    repository: Repository,
    learning_object_id: str,
    *,
    states: list[FacetUncertaintyState] | None = None,
    signal: QuestionSignal | None = None,
    exclude_attempt_id: str | None = None,
    clock: Clock | None = None,
) -> tuple[list[FacetUncertaintyState], QuestionSignal]:
    """Facet uncertainty states with question observations folded in.

    Existing states get their marginal updated (one observation per
    unresolved question, capped); questioned facets with no persisted state
    get a virtual ``open`` state seeded from a neutral solid/absent prior so
    they can participate in EIG ranking and gate-facet selection. Purely
    decision-time: nothing is written back.
    """

    if states is None:
        states = facet_uncertainty_states_for_lo(vault, repository, learning_object_id)
    if not vault.config.tutor_qa.apply_question_evidence:
        # Config-off disables the whole channel (marginal adjustment AND the
        # focus enrichment downstream reads from the signal) without scanning.
        return list(states), _empty_signal(vault.config.tutor_qa)
    if signal is None:
        signal = collect_question_signal(
            vault,
            repository,
            learning_object_id,
            exclude_attempt_id=exclude_attempt_id,
            clock=clock,
        )
    if not signal.events_by_facet and not signal.gap_events_by_facet:
        return list(states), signal

    ratio = signal.likelihood.value
    gap_ratio = signal.gap_likelihood.value if signal.gap_likelihood is not None else 1.0
    preference_damping = float(vault.config.tutor_qa.preference_channel_damping)
    adjusted: list[FacetUncertaintyState] = []
    seen_facets: set[str] = set()
    for state in states:
        seen_facets.add(state.facet_id)
        events = signal.events_by_facet.get(state.facet_id, [])
        gap_events = signal.gap_events_by_facet.get(state.facet_id, [])
        if not events and not gap_events:
            adjusted.append(state)
            continue
        marginal = _apply_question_channels(
            dict(state.hypothesis_marginal),
            events,
            gap_events,
            ratio,
            gap_ratio,
            preference_damping=preference_damping,
        )
        adjusted.append(
            replace(state, hypothesis_marginal=marginal, uncertainty=entropy(marginal))
        )
    now_iso = utc_now_iso(clock)
    observed_facets = sorted(set(signal.events_by_facet) | set(signal.gap_events_by_facet))
    for facet in observed_facets:
        if facet in seen_facets:
            continue
        events = signal.events_by_facet.get(facet, [])
        gap_events = signal.gap_events_by_facet.get(facet, [])
        marginal = _apply_question_channels(
            {f"facet_solid:{facet}": 0.5, f"facet_absent:{facet}": 0.5},
            events,
            gap_events,
            ratio,
            gap_ratio,
            preference_damping=preference_damping,
        )
        ordered = sorted([*events, *gap_events], key=lambda event: str(event.get("created_at") or ""))
        adjusted.append(
            FacetUncertaintyState(
                id=f"virtual_question_{learning_object_id}_{facet}",
                learning_object_id=learning_object_id,
                facet_id=facet,
                hypothesis_marginal=marginal,
                uncertainty=entropy(marginal),
                status="open",
                opened_by_attempt_id=str(ordered[0].get("id", "")),
                opened_reason="tutor_question",
                last_evidence_at=ordered[-1].get("created_at"),
                algorithm_version=vault.config.algorithms.algorithm_version,
                created_at=str(ordered[0].get("created_at") or now_iso),
                updated_at=now_iso,
            )
        )
    return adjusted, signal


def _apply_question_channels(
    marginal: dict[str, float],
    ordinary_events: list[dict[str, Any]],
    gap_events: list[dict[str, Any]],
    ordinary_ratio: float,
    gap_ratio: float,
    *,
    preference_damping: float = 1.0,
) -> dict[str, float]:
    """Fold both question channels into one facet marginal under a shared cap.

    Gap declarations are applied first because they are the explicit, stronger
    signal; the ordinary substantive observations then consume whatever remains
    of ``MAX_QUESTION_OBSERVATIONS_PER_FACET`` so the two channels together never
    exceed the per-facet observation budget.

    §13.4: an event classified ``interaction_preference`` is a request about
    HOW to be tutored, not evidence of missing knowledge; its likelihood ratio
    is damped toward 1 by ``preference_damping`` (retained-strength factor —
    0 removes its mastery effect entirely) until contextual likelihoods are
    calibrated.
    """

    def event_ratio(event: dict[str, Any], base_ratio: float) -> float:
        if event.get("signal_channel") == "interaction_preference":
            return 1.0 - (1.0 - base_ratio) * preference_damping
        return base_ratio

    gap_count = min(len(gap_events), MAX_QUESTION_OBSERVATIONS_PER_FACET)
    ordinary_count = min(len(ordinary_events), MAX_QUESTION_OBSERVATIONS_PER_FACET - gap_count)
    for event in gap_events[:gap_count]:
        marginal = apply_question_observation(
            marginal, solid_likelihood_ratio=event_ratio(event, gap_ratio)
        )
    for event in ordinary_events[:ordinary_count]:
        marginal = apply_question_observation(
            marginal, solid_likelihood_ratio=event_ratio(event, ordinary_ratio)
        )
    return marginal


def _empty_signal(config: TutorQAConfig) -> QuestionSignal:
    fallback = float(config.question_solid_likelihood_ratio)
    return QuestionSignal(
        events_by_facet={},
        unfaceted_events=[],
        likelihood=ResolvedQuestionLikelihood(
            value=fallback,
            source="absolute_fallback",
            sample_size=0,
            questioned_failure_rate=None,
            base_failure_rate=None,
            absolute_fallback=fallback,
        ),
    )


def _clamped_rate(successes: float, total: float) -> float:
    low, high = _RATE_CLAMP
    if total <= 0:
        return low
    return min(high, max(low, successes / total))


def _first_attempt_at_or_after(
    repository: Repository, practice_item_id: str, created_at: str
) -> dict[str, Any] | None:
    candidates = [
        attempt
        for attempt in repository.list_recent_attempts_by_practice_item(practice_item_id, limit=50)
        if attempt.get("created_at") and attempt["created_at"] >= created_at
    ]
    return min(candidates, key=lambda attempt: (attempt["created_at"], attempt.get("id", "")), default=None)


def _attempt_failed(attempt: dict[str, Any]) -> bool:
    # Same failure predicate as followups' repeated-failure counters.
    return (
        attempt.get("attempt_type") == "dont_know"
        or float(attempt.get("correctness") or 0.0) <= 0.40
        or bool(attempt.get("error_type"))
    )


def _facet_success_times(
    vault: LoadedVault,
    repository: Repository,
    learning_object_id: str,
    *,
    exclude_attempt_id: str | None,
) -> dict[str, str]:
    """Latest *successful* attempt time per canonical facet (the resolution signal)."""

    latest: dict[str, str] = {}
    for attempt in repository.list_recent_attempts_by_learning_object(learning_object_id, limit=200):
        if exclude_attempt_id is not None and attempt.get("id") == exclude_attempt_id:
            continue
        if _attempt_failed(attempt):
            continue
        created_at = attempt.get("created_at")
        if not created_at:
            continue
        for facet in attempt.get("evidence_facets", []):
            facet_id = vault.canonical_facet_id(str(facet))
            if facet_id not in latest or created_at > latest[facet_id]:
                latest[facet_id] = created_at
    return latest


def _event_maps_to_lo(vault: LoadedVault, event: dict[str, Any], learning_object_id: str) -> bool:
    item_id = event.get("practice_item_id")
    if item_id is not None:
        item = vault.practice_items.get(item_id)
        return item is not None and item.learning_object_id == learning_object_id
    note_id = event.get("note_id")
    if note_id is not None:
        note = vault.notes.get(note_id)
        return note is not None and learning_object_id in note.related_los
    return False

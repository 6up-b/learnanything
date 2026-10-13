"""Valuing candidates by value of information (spec_source_practice_and_probes_v1 §8.2-§8.3).

The adapter computes no value of its own. It reads the learner's rival
hypotheses where they already live (:func:`open_hypotheses`), converts each
candidate into the representation the existing selectors take
(:class:`ValuationProblem`, :class:`CandidateInput`), calls them
(``robust_composition.evaluate_selection``, its credible-set form, or
``evsi.rank_feasible``) and records what they said.

* **One problem per hypothesis space.** Producers' hypotheses can coexist, and
  no producer states a joint distribution, so two spaces are two problems,
  each valued, stopped and verdicted on its own; nothing is summed across them.
* **Likelihood regimes say what a verdict may license** (§8.3.3): a
  ``pinned_channel`` verdict can license a system-initiated check; an
  ``item_point`` table or an ``arm_b_noiseless`` bound cannot (it can still
  license a skip); a ``structural`` candidate gets no value at all.
* **No count cap.** After the first pick, each later candidate is valued by
  its expected robust EIG over the predicted-outcome branches of the picks so
  far; adding stops at the first ``stop``. ``limit`` plays no part.
* **No fallback.** An abstention or exclusion never becomes an entropy order:
  learner-initiated results list such candidates in their groups and the
  learner decides; system-initiated ones get ``abstain`` with the reason.
* **No new constants.** λ, the burden and the nat-to-minutes scale are read
  from ``robust_composition`` so a calibration lands everywhere at once, and
  every valuation says the scale is not yet calibrated.

Its only write is the idempotent channel snapshot ``resolve_episode_channel``
persists (so replay can rehydrate the pinned channel).
"""
from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import asdict, dataclass, field
import json
import math
from typing import Any

from learnloop.ai.execution import content_key
from learnloop.db.repositories import Repository
from learnloop.diagnosis import robust_composition as RC
from learnloop.diagnosis.probe_hypotheses import H_OTHER
from learnloop.diagnosis.probes import (
    Hypothesis,
    HypothesisSet,
    build_hypothesis_set,
    conditional_distribution,
    facet_conditional_distribution,
    item_registry_discrimination,
    resolve_item_irt,
)
from learnloop.learner.mastery import sigmoid
from learnloop.scheduling import evsi as EV
from learnloop.vault.models import LoadedVault, PracticeItem

VALUATION_VERSION = "source_valuation.v1"
HYPOTHESIS_KINDS = ("misconception", "causal_hypothesis", "episode_label", "unresolved_cause", "facet_state",
                    "named_gap", "retention")
#: Regimes, and what each may license (§8.3.3).
LICENSES_SYSTEM_CHECK = frozenset({"pinned_channel"})
VALUED_REGIMES = frozenset({"pinned_channel", "item_point"})
SCALE_LABEL = "LearnLoop's estimate; its scale is not yet calibrated"
#: Branch mass below this is dropped (renormalized) when valuing later checks
#: conditionally: it bounds compute, never the number of checks.
BRANCH_MASS_FLOOR = 0.01
MAX_BRANCHES = 64


@dataclass(frozen=True)
class HypothesisRef:
    kind: str
    id: str

    @classmethod
    def parse(cls, value: Mapping[str, Any] | "HypothesisRef") -> "HypothesisRef":
        if isinstance(value, HypothesisRef):
            return value
        kind, ident = str(value.get("kind") or ""), str(value.get("id") or "")
        if kind not in HYPOTHESIS_KINDS or not ident:
            raise ValueError(f"a hypothesis ref needs kind in {', '.join(HYPOTHESIS_KINDS)} and an id")
        return cls(kind, ident)


@dataclass
class PendingDecision:
    decision_kind: str
    action_by_slot: dict[str, str | None]
    loss_table: Any | None = None
    meta: dict[str, Any] = field(default_factory=dict)


@dataclass
class ValuationProblem:
    """One hypothesis space: mutually exclusive slots under one prior."""

    key: str
    space_kind: str
    slots: tuple[str, ...]
    prior: dict[str, float]
    prior_basis: str
    state_hash: str
    refs: list[HypothesisRef] = field(default_factory=list)
    excluded_mass: dict[str, float] = field(default_factory=dict)
    decision: PendingDecision | None = None
    context: dict[str, Any] = field(default_factory=dict)

    def describe(self) -> dict[str, Any]:
        return {"key": self.key, "space_kind": self.space_kind, "slots": list(self.slots),
                "prior": {k: round(v, 6) for k, v in sorted(self.prior.items())}, "prior_basis": self.prior_basis,
                "state_hash": self.state_hash, "refs": [asdict(ref) for ref in self.refs],
                "excluded_mass": dict(self.excluded_mass),
                "decision": None if self.decision is None else {
                    "decision_kind": self.decision.decision_kind, "action_by_slot": self.decision.action_by_slot,
                    **self.decision.meta}}


@dataclass
class CandidateInput:
    ref: str
    kind: str
    members: tuple[dict[str, dict[str, float]], ...] = ()
    outcome_alphabet: tuple[str, ...] = ()
    regime: str = "structural"
    likelihood_basis: str | None = None
    expected_minutes: float = 3.0
    minutes_provenance: dict[str, Any] = field(default_factory=dict)
    burden_minutes: float = 0.0
    missing: list[str] = field(default_factory=list)
    ensemble_hash: str | None = None
    #: How the credible set was built; candidates pair members by index only
    #: when their constructions (and member counts) match (§8.3.4).
    construction: str = ""

    @property
    def evaluable(self) -> bool:
        return bool(self.members) and not self.missing and self.regime != "structural"


# -- reading the hypotheses (§8.2) --------------------------------------------------


def _hash(value: Any) -> str:
    return content_key(value)[:32]


def _normalized(prior: Mapping[str, float], slots: Sequence[str]) -> dict[str, float]:
    values = {slot: max(float(prior.get(slot, 0.0)), 0.0) for slot in slots}
    total = sum(values.values())
    if total <= 0:
        raise EV.EVSIInputError("prior_mass_zero", tuple(slots))
    return {slot: value / total for slot, value in values.items()}


def lo_problem(vault: LoadedVault, repository: Repository, lo_id: str,
               refs: Sequence[HypothesisRef] = ()) -> tuple[ValuationProblem | None, list[dict[str, Any]]]:
    """The LO's hypothesis set: mastered, unfamiliar and one slot per active belief
    on the LO and its confusable neighbours (``build_hypothesis_set``)."""

    if lo_id not in vault.learning_objects:
        return None, [{"refs": [asdict(ref) for ref in refs], "reason": "no_hypothesis_set"}]
    hypothesis_set = build_hypothesis_set(vault, repository, lo_id)
    labels = tuple(h.label for h in hypothesis_set.hypotheses)
    unavailable = []
    joined = []
    for ref in refs:
        label = f"misconception:{ref.id}"
        if ref.kind in ("misconception", "named_gap") and label not in labels:
            unavailable.append({"ref": asdict(ref), "reason": "not_in_hypothesis_set"})
        else:
            joined.append(ref)
    prior = _normalized(hypothesis_set.prior, labels)
    problem = ValuationProblem(
        key=f"lo:{lo_id}", space_kind="hypothesis_set", slots=labels, prior=prior, prior_basis="hypothesis_set",
        state_hash=_hash({"lo": lo_id, "prior": prior}), refs=joined,
        context={"learning_object_id": lo_id, "hypothesis_set": hypothesis_set})
    return problem, unavailable


def facet_problem(vault: LoadedVault, repository: Repository, lo_id: str, facet_id: str,
                  refs: Sequence[HypothesisRef] = ()) -> tuple[ValuationProblem | None, list[dict[str, Any]]]:
    state = repository.facet_uncertainty_state(lo_id, facet_id)
    if state is None or not state.hypothesis_marginal:
        return None, [{"ref": {"kind": "facet_state", "id": facet_id}, "reason": "no_prior"}]
    slots = tuple(sorted(state.hypothesis_marginal))
    prior = _normalized(state.hypothesis_marginal, slots)
    return ValuationProblem(
        key=f"facet:{lo_id}:{facet_id}", space_kind="facet_marginal", slots=slots, prior=prior,
        prior_basis="facet_marginal", state_hash=_hash({"facet": facet_id, "prior": prior}), refs=list(refs),
        context={"learning_object_id": lo_id, "facet_id": facet_id}), []


def episode_problem(vault: LoadedVault, repository: Repository, episode_id: str,
                    refs: Sequence[HypothesisRef] = ()) -> tuple[ValuationProblem | None, list[dict[str, Any]]]:
    from learnloop.diagnosis.probe_episodes import episode_hypothesis_set, episode_posterior

    episode = repository.probe_episode(episode_id)
    if episode is None:
        return None, [{"ref": {"kind": "episode_label", "id": episode_id}, "reason": "no_episode"}]
    hypothesis_set = episode_hypothesis_set(repository, episode)
    posterior = episode_posterior(vault, repository, episode, hypothesis_set=hypothesis_set) if hypothesis_set else None
    if hypothesis_set is None or posterior is None:
        return None, [{"ref": {"kind": "episode_label", "id": episode_id}, "reason": "no_prior"}]
    record = repository.fetch_hypothesis_set(str(episode.hypothesis_set_id)) or {}
    labels = tuple(h.label for h in hypothesis_set.hypotheses)
    concrete = tuple(label for label in labels if label != H_OTHER)
    excluded = {H_OTHER: round(float(posterior.posterior.get(H_OTHER, 0.0)), 6)} if H_OTHER in labels else {}
    prior = _normalized(posterior.posterior, concrete)
    return ValuationProblem(
        key=f"episode:{episode_id}", space_kind="episode", slots=concrete, prior=prior,
        prior_basis=str(record.get("prior_basis") or "episode_posterior"),
        state_hash=_hash({"episode": episode_id, "posterior": prior}), refs=list(refs), excluded_mass=excluded,
        context={"learning_object_id": episode.learning_object_id, "hypothesis_set": hypothesis_set,
                 "episode_id": episode_id}), []


def causal_problem(vault: LoadedVault, repository: Repository, hypothesis_set_id: str,
                   refs: Sequence[HypothesisRef] = (), *,
                   repair_class_by_hypothesis: Mapping[str, str | None] | None = None,
                   ) -> tuple[ValuationProblem | None, list[dict[str, Any]]]:
    """A causal factor's concrete hypotheses (``H_OTHER`` excluded explicitly, its mass recorded)."""

    record = repository.fetch_hypothesis_set(hypothesis_set_id)
    if record is None:
        return None, [{"ref": {"kind": "causal_hypothesis", "id": hypothesis_set_id}, "reason": "no_hypothesis_set"}]
    raw = {str(k): float(v) for k, v in (record.get("prior") or {}).items()}
    concrete = tuple(sorted(key for key in raw if key != H_OTHER))
    excluded = {H_OTHER: round(raw.get(H_OTHER, 0.0), 6)}
    try:
        prior = _normalized(raw, concrete)
    except EV.EVSIInputError:
        return None, [{"ref": {"kind": "causal_hypothesis", "id": hypothesis_set_id}, "reason": "no_prior"}]
    decision = None
    if repair_class_by_hypothesis is not None:
        from learnloop.diagnosis.causal_diagnostic_selector import build_causal_loss_table

        mapping = {slot: repair_class_by_hypothesis.get(slot) for slot in concrete}
        table, meta = build_causal_loss_table(repository, repair_class_by_hypothesis=mapping)
        decision = PendingDecision("repair_class", mapping, table, meta)
    return ValuationProblem(
        key=f"causal:{hypothesis_set_id}", space_kind="causal_factor", slots=concrete, prior=prior,
        prior_basis=str(record.get("prior_basis") or "uniform_fallback"),
        state_hash=_hash({"set": hypothesis_set_id, "prior": prior}), refs=list(refs), excluded_mass=excluded,
        decision=decision, context={"hypothesis_set_id": hypothesis_set_id}), []


def retention_problem(vault: LoadedVault, repository: Repository, lo_id: str, facet_id: str | None = None,
                      ) -> tuple[ValuationProblem | None, list[dict[str, Any]]]:
    """Does a recently assisted success hold unaided? Two slots; the prior is the
    active predictor's P(success) (the LO's mastery mean, ``mastery_ekf``)."""

    mastery = repository.mastery_state(lo_id)
    if mastery is None:
        return None, [{"ref": {"kind": "retention", "id": facet_id or lo_id}, "reason": "no_prior"}]
    p = min(max(sigmoid(mastery.logit_mean), 1e-6), 1 - 1e-6)
    prior = {"holds_unaided": p, "not_unaided": 1.0 - p}
    return ValuationProblem(
        key=f"retention:{lo_id}:{facet_id or '*'}", space_kind="retention", slots=("holds_unaided", "not_unaided"),
        prior=prior, prior_basis="predictor:mastery_ekf", state_hash=_hash({"retention": lo_id, "p": p}),
        refs=[HypothesisRef("retention", facet_id or lo_id)],
        context={"learning_object_id": lo_id, "facet_id": facet_id}), []


def named_gaps_available(repository: Repository) -> bool:
    """The learner-text gaps branch's table, feature-detected (§8.2)."""

    with repository.connection() as connection:
        return connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name IN ('named_gaps', 'learner_text_gaps')"
        ).fetchone() is not None


def _facet_los(vault: LoadedVault, facet_id: str) -> list[str]:
    from learnloop.practice_index.catalog import item_facets

    canonical = vault.canonical_facet_id(facet_id)
    return sorted({item.learning_object_id for item in vault.practice_items.values()
                   if canonical in item_facets(vault, item)})


def open_hypotheses(vault: LoadedVault, repository: Repository, *, facet_ids: Sequence[str] = (),
                    learning_object_ids: Sequence[str] = (),
                    refs: Sequence[Mapping[str, Any] | HypothesisRef] = (), intent: str = "discriminate",
                    repair_class_by_hypothesis: Mapping[str, str | None] | None = None,
                    ) -> tuple[list[ValuationProblem], list[dict[str, Any]]]:
    """The rival-hypothesis spaces a request bears on, one problem each. Reads, never writes."""

    parsed = [HypothesisRef.parse(ref) for ref in refs]
    problems: dict[str, ValuationProblem] = {}
    unavailable: list[dict[str, Any]] = []

    def add(result: tuple[ValuationProblem | None, list[dict[str, Any]]]) -> None:
        problem, missing = result
        unavailable.extend(missing)
        if problem is not None:
            if problem.key in problems:
                problems[problem.key].refs.extend(ref for ref in problem.refs if ref not in problems[problem.key].refs)
            else:
                problems[problem.key] = problem

    if intent == "retention":
        los = list(learning_object_ids) or sorted({lo for facet in facet_ids for lo in _facet_los(vault, facet)})
        for lo_id in los:
            add(retention_problem(vault, repository, lo_id, facet_ids[0] if facet_ids else None))
        return list(problems.values()), unavailable
    by_lo: dict[str, list[HypothesisRef]] = {}
    for ref in parsed:
        if ref.kind == "misconception":
            record = repository.misconception(ref.id)
            if record is None:
                unavailable.append({"ref": asdict(ref), "reason": "unknown_misconception"})
            else:
                by_lo.setdefault(record.learning_object_id, []).append(ref)
        elif ref.kind == "named_gap":
            if not named_gaps_available(repository):
                unavailable.append({"ref": asdict(ref), "reason": "unavailable: learner-text gaps not merged"})
            else:
                unavailable.append({"ref": asdict(ref), "reason": "unmapped_named_gap"})
        elif ref.kind == "facet_state":
            for lo_id in _facet_los(vault, ref.id) or list(learning_object_ids):
                add(facet_problem(vault, repository, lo_id, vault.canonical_facet_id(ref.id), [ref]))
        elif ref.kind in ("causal_hypothesis", "unresolved_cause"):
            add(causal_problem(vault, repository, ref.id, [ref], repair_class_by_hypothesis=repair_class_by_hypothesis))
        elif ref.kind == "episode_label":
            add(episode_problem(vault, repository, ref.id, [ref]))
        elif ref.kind == "retention":
            add(retention_problem(vault, repository, ref.id))
    for lo_id, lo_refs in by_lo.items():
        add(lo_problem(vault, repository, lo_id, lo_refs))
    if not parsed:
        los = list(learning_object_ids) or sorted({lo for facet in facet_ids for lo in _facet_los(vault, facet)})
        for lo_id in los:
            add(lo_problem(vault, repository, lo_id))
            for facet in facet_ids:
                state = repository.facet_uncertainty_state(lo_id, vault.canonical_facet_id(facet))
                if state is not None and state.hypothesis_marginal:
                    add(facet_problem(vault, repository, lo_id, vault.canonical_facet_id(facet)))
    return list(problems.values()), unavailable


# -- candidate tables (§8.3.2) --------------------------------------------------------


def _outcome_key(outcome: Any) -> str:
    if isinstance(outcome, tuple):
        return "|".join("none" if part is None else str(part) for part in outcome)
    return str(outcome)


def _normalize_rows(table: Mapping[str, Mapping[Any, float]]) -> dict[str, dict[str, float]]:
    out: dict[str, dict[str, float]] = {}
    for slot, row in table.items():
        keyed = {_outcome_key(key): max(float(value), 0.0) for key, value in row.items()}
        total = sum(keyed.values())
        if total <= 0:
            raise EV.EVSIInputError("incomplete_likelihoods", (slot,))
        out[slot] = {key: value / total for key, value in keyed.items()}
    return out


def check_tables(problem: ValuationProblem, members: Sequence[Mapping[str, Mapping[str, float]]]) -> None:
    """Each row sums to 1 over the alphabet and every prior slot has a row (§8.3.1)."""

    for member in members:
        missing = [slot for slot in problem.slots if slot not in member]
        if missing:
            raise EV.EVSIInputError("incomplete_likelihoods", missing)
        for slot in problem.slots:
            if abs(sum(member[slot].values()) - 1.0) > 1e-6:
                raise EV.EVSIInputError("row_not_normalized", (slot,))


def _item_point_members(point: dict[str, dict[str, float]]) -> tuple[dict[str, dict[str, float]], ...]:
    """Member 0 plus ``evsi.stress_matrices``' ±0.15 perturbations: a robustness check, not a calibration."""

    return (point, *EV.stress_matrices(point))


def _minutes(estimator: Callable[..., Any] | None, ref: str, mode: str | None,
             expected: float | None) -> tuple[float, dict[str, Any]]:
    if estimator is None:
        return 3.0, {"prior_source": "fallback", "note": "no estimator injected"}
    estimate = estimator(ref, mode, expected)
    minutes = float(getattr(estimate, "minutes", estimate))
    provenance = estimate.as_dict() if hasattr(estimate, "as_dict") else {"minutes": minutes}
    return minutes, provenance


def item_input(vault: LoadedVault, repository: Repository, problem: ValuationProblem, item: PracticeItem, *,
               estimator: Callable[..., Any] | None = None, channel: Any | None = None) -> CandidateInput:
    minutes, provenance = _minutes(estimator, item.id, item.practice_mode, item.expected_minutes)
    candidate = CandidateInput(ref=item.id, kind="item", expected_minutes=minutes, minutes_provenance=provenance)
    rubric = vault.rubric_for_item(item)
    try:
        if problem.space_kind in ("hypothesis_set", "episode"):
            hypothesis_set: HypothesisSet = problem.context["hypothesis_set"]
            discrimination, discriminated = item_registry_discrimination(repository, vault, item, rubric, hypothesis_set)
            item_a, item_b, irt = resolve_item_irt(vault, item)
            fatal = {error.id for error in (rubric.fatal_errors if rubric is not None else [])}
            hypotheses: dict[str, Hypothesis] = {h.label: h for h in hypothesis_set.hypotheses}
            point = _normalize_rows({
                label: conditional_distribution(
                    hypotheses[label], item_a=item_a, item_b=item_b, irt=irt, fatal_error_ids=fatal,
                    known_error_types=hypothesis_set.known_error_types, discrimination=discrimination,
                    discriminated_ids=discriminated)
                for label in problem.slots})
            if discrimination:
                basis = "estimated_row"
            elif discriminated:
                basis = "bridge_default"
            elif item.canonical_exercise is not None and item.discrimination_profiles:
                basis = "authored_profile_unchecked"
            else:
                basis = "estimated_row" if not any(h.misconception_id for h in hypothesis_set.hypotheses) else "no_profile"
            candidate.members = _item_point_members(point)
            candidate.regime, candidate.likelihood_basis = "item_point", basis
            candidate.construction = "item_point:stress"
        elif problem.space_kind == "facet_marginal":
            from learnloop.practice_index.catalog import item_facets

            facet_id = problem.context["facet_id"]
            item_a, item_b, irt = resolve_item_irt(vault, item)
            fatal = {error.id for error in (rubric.fatal_errors if rubric is not None else [])}
            point = _normalize_rows({
                label: facet_conditional_distribution(
                    label, facet_id=facet_id, candidate_facet_support=set(item_facets(vault, item)),
                    fatal_error_ids=fatal, known_error_types=[], item_a=item_a, item_b=item_b, irt=irt)
                for label in problem.slots})
            candidate.members = _item_point_members(point)
            candidate.regime, candidate.likelihood_basis = "item_point", "facet_conditional"
            candidate.construction = "item_point:stress"
        elif problem.space_kind == "causal_factor":
            from learnloop.diagnosis.causal_diagnostic_selector import likelihood_regime_for_candidate

            regime, detail, member = likelihood_regime_for_candidate(
                repository, {"practice_item_id": item.id}, concrete_hypothesis_ids=list(problem.slots))
            if regime == "arm_b_noiseless_partition" and member is not None:
                candidate.members = (member,)
                candidate.regime, candidate.likelihood_basis = "arm_b_noiseless", "blind_bundles"
                candidate.construction = "noiseless"
            else:
                candidate.regime = "structural"
                candidate.missing = ["incomplete_likelihoods:" + str(detail.get("reason") or regime)]
        elif problem.space_kind == "retention":
            if channel is None:
                candidate.missing = ["no_channel"]
            else:
                candidate.members, candidate.ensemble_hash = retention_members(channel, item.id)
                candidate.regime, candidate.likelihood_basis = "pinned_channel", "declared_retention_rows"
                candidate.construction = f"pinned:{channel.model_hash}:retention"
                if getattr(channel, "fallback_reason", None):
                    candidate.minutes_provenance["channel_fallback_reason"] = channel.fallback_reason
        if candidate.members:
            check_tables(problem, candidate.members)
            candidate.outcome_alphabet = tuple(sorted({e for row in candidate.members[0].values() for e in row}))
            candidate.ensemble_hash = candidate.ensemble_hash or _hash({"item": item.id, "space": problem.key,
                                                                        "basis": candidate.likelihood_basis})
    except EV.EVSIInputError as error:
        candidate.members = ()
        candidate.missing = [error.reason, *error.detail]
        candidate.regime = "structural"
    return candidate


def retention_members(channel: Any, ref: str) -> tuple[tuple[dict[str, dict[str, float]], ...], str]:
    """Declared retention rows composed with the pinned grader channel, as the
    robust probe path composes card rows: ``holds_unaided`` -> the correct class,
    ``not_unaided`` -> its incorrect classes. How mass splits among incorrect
    classes is unknown, so the credible set holds every extreme split."""

    classes = list(channel.true_classes)
    correct = next((cls for cls in classes if "correct" in cls and "incorrect" not in cls), classes[0])
    incorrect = [cls for cls in classes if cls != correct] or [correct]
    members: list[dict[str, dict[str, float]]] = []
    for target in incorrect:
        rows = {"holds_unaided": {correct: 1.0}, "not_unaided": {target: 1.0}}
        ensemble = RC.build_ensemble(joint_alpha=channel.joint_alpha, instrument_rows=rows,
                                     calibration_model_hash=channel.model_hash,
                                     decision_context_hash=_hash({"retention": ref, "split": target}))
        members.extend(ensemble.members)
    # Every member normalized over the full emission alphabet.
    emissions = sorted({e for member in members for row in member.values() for e in row})
    normalized = []
    for member in members:
        fixed = {}
        for slot, row in member.items():
            total = sum(row.values()) or 1.0
            fixed[slot] = {e: float(row.get(e, 0.0)) / total for e in emissions}
        normalized.append(fixed)
    return tuple(normalized), _hash({"channel": channel.model_hash, "ref": ref, "splits": incorrect})


def exercise_input(problem: ValuationProblem, exercise: Mapping[str, Any], screen: Mapping[str, Any] | None, *,
                   estimator: Callable[..., Any] | None = None) -> CandidateInput:
    """An unimported exercise: a complete screen is a noiseless partition (a bound);
    anything else is structural (§8.4)."""

    mode = (exercise.get("provisional") or {}).get("practice_mode")
    minutes, provenance = _minutes(estimator, str(exercise["key"]), mode, None)
    candidate = CandidateInput(ref=str(exercise["key"]), kind="source_exercise", expected_minutes=minutes,
                               minutes_provenance=provenance)
    if screen is None:
        candidate.missing = ["not_screened"]
        return candidate
    signatures = {str(row["slot"]): str(row["signature_key"]) for row in screen.get("signatures") or []}
    complete = (screen.get("complete") and set(problem.slots) <= set(signatures)
                and len({signatures[slot] for slot in problem.slots}) == len(problem.slots))
    if not complete:
        candidate.missing = ["structural_only"]
        candidate.likelihood_basis = "model_screen_unchecked"
        return candidate
    candidate.members = ({slot: {signatures[slot]: 1.0} for slot in problem.slots},)
    candidate.regime, candidate.likelihood_basis = "arm_b_noiseless", "model_screen_unchecked"
    candidate.construction = "noiseless"
    candidate.outcome_alphabet = tuple(sorted(set(signatures[slot] for slot in problem.slots)))
    candidate.ensemble_hash = _hash({"screen": screen.get("judgment_id"), "space": problem.key})
    return candidate


# -- valuing one problem (§8.3.4) ---------------------------------------------------------


def _ensemble(candidate: CandidateInput, problem: ValuationProblem) -> RC.Ensemble:
    return RC.Ensemble(members=candidate.members, slots=problem.slots, emissions=candidate.outcome_alphabet,
                       calibration_model_hash=candidate.ensemble_hash or "", decision_context_hash=problem.state_hash,
                       seed=0, draw_count=max(len(candidate.members) - 1, 0), quantile=RC.ROBUST_QUANTILE,
                       perturbation_concentration=0.0)


def entropy_nats(prior: Mapping[str, float]) -> float:
    return -sum(p * math.log(p) for p in prior.values() if p > 0)


def _branches(picks: Sequence[CandidateInput], prior: Mapping[str, float]) -> list[tuple[float, dict[str, float]]]:
    """The predicted-outcome branches of the picks so far, on each pick's member 0."""

    branches = [(1.0, dict(prior))]
    for pick in picks:
        table = pick.members[0]
        grown = []
        for weight, posterior in branches:
            for emission in pick.outcome_alphabet:
                p_e = sum(posterior[h] * table.get(h, {}).get(emission, 0.0) for h in posterior)
                if p_e * weight < BRANCH_MASS_FLOOR:
                    continue
                grown.append((weight * p_e, RC.observed_update(table, posterior, emission)))
        grown.sort(key=lambda entry: entry[0], reverse=True)
        grown = grown[:MAX_BRANCHES]
        total = sum(weight for weight, _ in grown) or 1.0
        branches = [(weight / total, posterior) for weight, posterior in grown]
    return branches


def _conditional_series(candidate: CandidateInput, branches: Sequence[tuple[float, Mapping[str, float]]]) -> list[float]:
    return [sum(weight * RC.expected_information_gain(member, posterior) for weight, posterior in branches)
            for member in candidate.members]


def value_problem(problem: ValuationProblem, inputs: Sequence[CandidateInput], *, caller_kind: str = "learner",
                  system_initiated: bool = False) -> dict[str, Any]:
    """Groups, verdicts and stops for one hypothesis space."""

    report: dict[str, Any] = {"problem": problem.describe(), "valuation_version": VALUATION_VERSION,
                              "scale": SCALE_LABEL, "constants": {
                                  "lambda_time": RC.LAMBDA_TIME, "burden_cost": RC.BURDEN_COST,
                                  "value_per_nat_minutes": RC.VALUE_PER_NAT_MINUTES,
                                  "quantile": RC.ROBUST_QUANTILE}}
    groups = {"valued": [], "bounded": [], "unvalued": []}
    for candidate in inputs:
        entry = {"ref": candidate.ref, "kind": candidate.kind, "regime": candidate.regime,
                 "likelihood_basis": candidate.likelihood_basis, "missing": list(candidate.missing),
                 "expected_minutes": round(candidate.expected_minutes, 4),
                 "minutes_provenance": candidate.minutes_provenance, "members": len(candidate.members)}
        if not candidate.evaluable:
            entry["label"] = "LearnLoop can't estimate how much this would tell you"
            groups["unvalued"].append(entry)
        elif candidate.regime == "arm_b_noiseless":
            groups["bounded"].append(entry)
        else:
            groups["valued"].append(entry)
    by_ref = {candidate.ref: candidate for candidate in inputs}
    # Each valued candidate's own robust value interval (its members' EIG at the
    # lower and upper ROBUST_QUANTILE), in minutes, and P(E) under the prior:
    # the valued group is listed in value order (per minute) with the stop marked.
    for entry in groups["valued"]:
        candidate = by_ref[entry["ref"]]
        series = [RC.expected_information_gain(member, problem.prior) for member in candidate.members]
        low, high = RC.robust_quantile(series), RC.robust_quantile(series, 1.0 - RC.ROBUST_QUANTILE)
        entry.update(point_eig_nats=round(series[0], 6), robust_eig_nats=round(low, 6),
                     value_minutes_lcb=round(RC.VALUE_PER_NAT_MINUTES * low, 4),
                     value_minutes_ucb=round(RC.VALUE_PER_NAT_MINUTES * high, 4),
                     predicted_outcomes=_predicted(candidate, problem.prior))
    groups["valued"].sort(key=lambda entry: (-entry["value_minutes_lcb"] / max(entry["expected_minutes"], 1e-6),
                                             entry["ref"]))
    report["groups"] = groups
    if problem.decision is not None:
        return _decision_mode(problem, inputs, report, by_ref, system_initiated=system_initiated)
    report["mode"] = "information"
    # Bounds (arm B) are compared only with the stop, to license a skip.
    for entry in groups["bounded"]:
        candidate = by_ref[entry["ref"]]
        bound_nats = RC.expected_information_gain(candidate.members[0], problem.prior)
        bound_minutes = RC.VALUE_PER_NAT_MINUTES * bound_nats
        entry["upper_bound_minutes"] = round(bound_minutes, 4)
        entry["label"] = f"LearnLoop's reading of the exercise, not yet checked: at most {bound_minutes:.1f} minutes"
        entry["skip_licensed"] = bound_minutes <= RC.LAMBDA_TIME * candidate.expected_minutes + RC.BURDEN_COST
    competing = [by_ref[entry["ref"]] for entry in groups["valued"]
                 if not system_initiated or by_ref[entry["ref"]].regime in LICENSES_SYSTEM_CHECK]
    if system_initiated:
        for entry in groups["valued"] + groups["bounded"]:
            if by_ref[entry["ref"]].regime not in LICENSES_SYSTEM_CHECK:
                entry["excluded"] = "regime_cannot_license"
    if not competing:
        reason = "regime_cannot_license" if system_initiated and (groups["valued"] or groups["bounded"]) \
            else "no_discriminating_instrument"
        report.update(verdict="abstain" if reason == "regime_cannot_license" else reason, reason=reason, checks=[],
                      selector=None)
        report["perfect_information_minutes"] = round(RC.VALUE_PER_NAT_MINUTES * entropy_nats(problem.prior), 4)
        return report
    checks: list[dict[str, Any]] = []
    picks: list[CandidateInput] = []
    remaining = list(competing)
    verdict, reason, selector = "stop", "no_candidate", None
    while remaining:
        if not picks:
            sizes = {len(candidate.members) for candidate in remaining}
            constructions = {candidate.construction for candidate in remaining}
            same_shape = len(sizes) == 1 and len(constructions) == 1
            triples = [(c.ref, _ensemble(c, problem), c.expected_minutes * 60.0) for c in remaining]
            if same_shape:
                selector = "evaluate_selection"
                decision = RC.evaluate_selection(candidates=triples, posterior=problem.prior)
            else:
                selector = "evaluate_selection_credible_sets"
                decision = RC.evaluate_selection_credible_sets(candidates=triples, posterior=problem.prior)
        else:
            branches = _branches(picks, problem.prior)
            series = [(c.ref, _conditional_series(c, branches), c.expected_minutes * 60.0) for c in remaining]
            winner_ref = max(series, key=lambda t: RC.robust_quantile([v / max(t[2], 1e-6) for v in t[1]]))[0]
            decision = RC.evaluate_series_selection(
                candidates=series, winner_eig_nats=dict((ref, s) for ref, s, _ in series)[winner_ref])
        if decision.verdict != "act":
            verdict = "stop" if decision.verdict == "stop" else "abstain"
            reason = ("lcb_value_below_minutes_cost" if decision.verdict == "stop"
                      else "couldnt_reliably_distinguish")
            if picks:
                verdict, reason = "act", f"stopped_after_{len(picks)}"
            report["stop_at"] = {"candidate": decision.chosen_slot, "verdict": decision.verdict,
                                 "robust_eig_per_second": round(decision.robust_eig_per_second, 8),
                                 "action_agreement": round(decision.action_agreement_fraction, 4)}
            break
        chosen = by_ref[str(decision.chosen_slot)]
        picks.append(chosen)
        remaining = [candidate for candidate in remaining if candidate.ref != chosen.ref]
        series = ([RC.expected_information_gain(member, problem.prior) for member in chosen.members] if len(picks) == 1
                  else _conditional_series(chosen, _branches(picks[:-1], problem.prior)))
        checks.append({
            "ref": chosen.ref, "order": len(picks), "regime": chosen.regime,
            "robust_eig_nats": round(RC.robust_quantile(series), 6), "point_eig_nats": round(series[0], 6),
            "value_minutes_lcb": round(RC.VALUE_PER_NAT_MINUTES * RC.robust_quantile(series), 4),
            "expected_minutes": round(chosen.expected_minutes, 4),
            "action_agreement": round(decision.action_agreement_fraction, 4),
            "licenses_system_check": chosen.regime in LICENSES_SYSTEM_CHECK,
            "predicted_outcomes": _predicted(chosen, problem.prior if len(picks) == 1 else None),
        })
        verdict, reason = "act", "positive_robust_net_value"
    report.update(verdict=verdict, reason=reason, checks=checks, selector=selector)
    report["perfect_information_minutes"] = round(RC.VALUE_PER_NAT_MINUTES * entropy_nats(problem.prior), 4)
    for entry in groups["valued"]:
        if entry["ref"] in {check["ref"] for check in checks}:
            entry["check_order"] = next(check["order"] for check in checks if check["ref"] == entry["ref"])
    return report


def _predicted(candidate: CandidateInput, prior: Mapping[str, float] | None) -> dict[str, float] | None:
    """P(E) = sum_H P(H) P(E|H) on member 0 (S5 logs it beside the observed bucket)."""

    if prior is None:
        return None
    table = candidate.members[0]
    return {e: round(sum(prior[h] * table.get(h, {}).get(e, 0.0) for h in prior), 6)
            for e in candidate.outcome_alphabet}


def _decision_mode(problem: ValuationProblem, inputs: Sequence[CandidateInput], report: dict[str, Any],
                   by_ref: Mapping[str, CandidateInput], *, system_initiated: bool) -> dict[str, Any]:
    report["mode"] = "decision"
    decision = problem.decision
    assert decision is not None
    if decision.loss_table is None:
        reason = str(decision.meta.get("reason") or "no_action_mapping")
        report.update(verdict="abstain", reason=reason, checks=[], selector="rank_feasible")
        return report
    pool = [c for c in inputs if c.evaluable and (not system_initiated or c.regime in LICENSES_SYSTEM_CHECK)]
    candidates = [EV.DiagnosticCandidate(ref=c.ref, members=tuple(c.members), prior=problem.prior,
                                         expected_minutes=c.expected_minutes, burden_minutes=c.burden_minutes,
                                         prior_basis=problem.prior_basis) for c in pool]
    if not candidates:
        report.update(verdict="no_discriminating_instrument" if not system_initiated else "abstain",
                      reason="no_evaluable_candidate" if not system_initiated else "regime_cannot_license",
                      checks=[], selector="rank_feasible")
        return report
    result = EV.rank_feasible(candidates, decision.loss_table)
    report["rank"] = result.as_dict()
    report["selector"] = "rank_feasible"
    common = EV.shared_optimal_action(decision.loss_table)
    best = next((r for r in result.ranked if r.ref == result.best_ref), None)
    if result.verdict == "measure":
        verdict = "measure"
        checks = [{"ref": result.best_ref, "order": 1, "evsi": best.evsi.as_dict() if best else None,
                   "regime": by_ref[result.best_ref].regime,
                   "licenses_system_check": by_ref[result.best_ref].regime in LICENSES_SYSTEM_CHECK}]
    else:
        verdict = result.verdict
        checks = []
    named_action = common if common is not None else (best.evsi.current_action if best else None)
    report.update(verdict=verdict, reason=result.reason, checks=checks,
                  named_action=named_action, action_kind="common_action" if common else "current_action",
                  perfect_information_minutes=round(_evpi(problem, decision.loss_table), 4))
    return report


def _evpi(problem: ValuationProblem, loss_table: Any) -> float:
    current = min(sum(problem.prior[h] * loss_table.loss(h, a) for h in problem.slots) for a in loss_table.actions)
    perfect = sum(problem.prior[h] * min(loss_table.loss(h, a) for a in loss_table.actions) for h in problem.slots)
    return max(current - perfect, 0.0)


def value_candidates(problems: Sequence[ValuationProblem], inputs_by_problem: Mapping[str, Sequence[CandidateInput]],
                     *, caller_kind: str = "learner", system_initiated: bool = False,
                     unavailable: Sequence[Mapping[str, Any]] = ()) -> dict[str, Any]:
    """The valuation receipt: one section per problem, nothing summed across them."""

    sections = [value_problem(problem, inputs_by_problem.get(problem.key, ()), caller_kind=caller_kind,
                              system_initiated=system_initiated) for problem in problems]
    listed: dict[str, list[dict[str, Any]]] = {}
    for section in sections:
        for group, entries in section["groups"].items():
            for entry in entries:
                listed.setdefault(entry["ref"], []).append({"problem": section["problem"]["key"], "group": group,
                                                            "check_order": entry.get("check_order"),
                                                            "regime": entry["regime"]})
    return {"valuation_version": VALUATION_VERSION, "caller_kind": caller_kind,
            "system_initiated": system_initiated, "problems": sections, "candidates": listed,
            "unavailable": [dict(entry) for entry in unavailable], "scale": SCALE_LABEL}


def refuse_mixed_decision(problems: Sequence[ValuationProblem], action_by_slot: Mapping[str, Any]) -> None:
    """A pending decision belongs to one space; one naming slots of several is refused."""

    owners = {problem.key for problem in problems for slot in action_by_slot if slot in problem.slots}
    if len(owners) > 1:
        raise ValueError("mixed_hypothesis_spaces")


__all__ = [
    "CandidateInput",
    "HYPOTHESIS_KINDS",
    "HypothesisRef",
    "LICENSES_SYSTEM_CHECK",
    "PendingDecision",
    "SCALE_LABEL",
    "VALUATION_VERSION",
    "ValuationProblem",
    "causal_problem",
    "check_tables",
    "entropy_nats",
    "episode_problem",
    "exercise_input",
    "facet_problem",
    "item_input",
    "lo_problem",
    "open_hypotheses",
    "refuse_mixed_decision",
    "retention_members",
    "retention_problem",
    "value_candidates",
    "value_problem",
]

"""The simulated diagnostic world: scenarios, the true learner, the system's model.

A **scenario** is one Eedi 2024 subject (for example "BIDMAS"): its questions
are the candidate checks, and its hypothesis space is

* ``knows`` (no misconception; route: continue),
* ``mis:<id>`` for each misconception the subject's questions diagnose on at
  least two questions (route: that misconception's repair),
* ``other`` (an unlabelled misconception or none: route: reteach).

The **true learner** answers with the response model fitted to Eedi 2020
(:mod:`.response_fit`): per-subject estimates where the subject has at least
two fitted triples, pooled estimates otherwise, and per-question consistency
drawn around the subject mean with the fitted between-item concentration (real
questions differ in how reliably they elicit a misconception).

The **system's model** is what the selectors believe ``P(option | h)`` is:

* ``hand_set``: today's live vocabulary, the contrast-card default rows
  (:data:`probe_families.CONTRAST_CONFUSABLE_DEFAULT_ROWS`) compiled through
  :data:`probe_families.ORDINAL_VOCABULARY`, mapped onto the four options;
* ``eedi_fitted``: the fitted subject means (what a calibrated card would say,
  without knowing the per-question variation).

The gap between the two models and the truth is exactly what the calibration
metrics measure.
"""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass, field
from typing import Mapping, Sequence

import numpy as np

from learnloop.diagnosis.probe_families import CONTRAST_CONFUSABLE_DEFAULT_ROWS, ORDINAL_VOCABULARY
from learnloop.evsi_calibration.eedi import OPTIONS, EediBank, EediQuestion
from learnloop.evsi_calibration.response_fit import ResponseFit

HYP_KNOWS = "knows"
HYP_OTHER = "other"
MIS_PREFIX = "mis:"
ACTION_CONTINUE = "continue"
ACTION_RETEACH = "reteach"
REPAIR_PREFIX = "repair:"

SYSTEM_MODELS = ("hand_set", "eedi_fitted")

#: Response-model parameters the truth needs (names match :data:`response_fit.PARAMETERS`).
TRUTH_PARAMETERS = (
    "consistency",
    "holder_correct",
    "unsure_designated",
    "unsure_correct",
    "knower_slip",
    "knower_designated",
    "prevalence_knows",
    "prevalence_holds",
    "prevalence_unsure",
)


def misconception_hypothesis(misconception_id: str) -> str:
    return f"{MIS_PREFIX}{misconception_id}"


def route_for(hypothesis: str) -> str:
    if hypothesis == HYP_KNOWS:
        return ACTION_CONTINUE
    if hypothesis == HYP_OTHER:
        return ACTION_RETEACH
    return f"{REPAIR_PREFIX}{hypothesis[len(MIS_PREFIX):]}"


@dataclass(frozen=True)
class TruthParams:
    values: Mapping[str, float]
    consistency_concentration: float | None
    source: str  # 'subject_fit' | 'pooled_fit'

    def __getitem__(self, name: str) -> float:
        return float(self.values[name])


@dataclass(frozen=True)
class Scenario:
    subject_id: int
    subject_name: str
    hypotheses: tuple[str, ...]
    questions: tuple[EediQuestion, ...]
    prior: Mapping[str, float]
    truth: TruthParams

    @property
    def misconceptions(self) -> tuple[str, ...]:
        return tuple(h[len(MIS_PREFIX):] for h in self.hypotheses if h.startswith(MIS_PREFIX))

    def question(self, question_id: str) -> EediQuestion:
        for question in self.questions:
            if question.question_id == question_id:
                return question
        raise KeyError(question_id)


def build_scenarios(
    bank: EediBank,
    fit: ResponseFit,
    *,
    min_questions: int = 6,
    min_misconception_questions: int = 2,
    max_misconceptions: int = 5,
) -> list[Scenario]:
    """One scenario per subject with enough questions and diagnosable misconceptions."""

    scenarios: list[Scenario] = []
    for subject_id, questions in sorted(bank.by_subject().items()):
        if len(questions) < min_questions:
            continue
        coverage: dict[str, int] = {}
        for question in questions:
            for misconception in set(question.misconception_by_option.values()):
                coverage[misconception] = coverage.get(misconception, 0) + 1
        diagnosable = sorted(
            (m for m, n in coverage.items() if n >= min_misconception_questions),
            key=lambda m: (-coverage[m], int(m) if m.isdigit() else m),
        )[:max_misconceptions]
        if len(diagnosable) < 2:
            continue
        subject_fit = fit.by_subject.get(subject_id)
        values = {name: fit.param(name, subject_id) for name in TRUTH_PARAMETERS}
        truth = TruthParams(
            values=values,
            consistency_concentration=fit.consistency_concentration,
            source="subject_fit" if subject_fit is not None else "pooled_fit",
        )
        hypotheses = (HYP_KNOWS, *(misconception_hypothesis(m) for m in diagnosable), HYP_OTHER)
        # Population prior: the fitted class prevalences; misconception mass is
        # the fitted per-misconception prevalence for each candidate, all
        # renormalized (the hypothesis space is single-cause).
        raw = {HYP_KNOWS: values["prevalence_knows"], HYP_OTHER: values["prevalence_unsure"]}
        for m in diagnosable:
            raw[misconception_hypothesis(m)] = values["prevalence_holds"]
        total = sum(raw.values())
        prior = {h: raw[h] / total for h in hypotheses}
        scenarios.append(
            Scenario(
                subject_id=subject_id,
                subject_name=questions[0].subject_name,
                hypotheses=hypotheses,
                questions=tuple(questions),
                prior=prior,
                truth=truth,
            )
        )
    return scenarios


# -- response rows --------------------------------------------------------------------------------


def _spread(weights: Mapping[str, float], mass: float) -> dict[str, float]:
    total = sum(weights.values())
    if total <= 0 or mass <= 0:
        return {k: 0.0 for k in weights}
    return {k: mass * v / total for k, v in weights.items()}


def _normalized(row: Mapping[str, float]) -> dict[str, float]:
    total = sum(max(v, 0.0) for v in row.values())
    return {k: max(v, 0.0) / total for k, v in row.items()}


def eedi_row(
    hypothesis: str,
    question: EediQuestion,
    params: Mapping[str, float],
    *,
    consistency: float | None = None,
) -> dict[str, float]:
    """``P(option | hypothesis, question)`` under the fitted response model.

    ``consistency`` overrides the subject mean for this question (the truth's
    per-question draw); the system's ``eedi_fitted`` model passes None.
    """

    labelled = set(question.misconception_by_option)
    distractors = question.distractors
    unlabelled = [d for d in distractors if d not in labelled]
    row = {option: 0.0 for option in OPTIONS}

    def non_holder(correct_rate: float, designated_rate: float) -> None:
        wrong = max(1.0 - correct_rate, 0.0)
        row[question.correct] = correct_rate
        other_each = max(1.0 - correct_rate - designated_rate, 0.0) / 2.0
        weights = {d: (designated_rate if d in labelled else other_each) for d in distractors}
        if not unlabelled:
            weights = {d: 1.0 for d in distractors}
        row.update(_spread(weights, wrong))

    if hypothesis == HYP_KNOWS:
        non_holder(1.0 - float(params["knower_slip"]), float(params["knower_designated"]))
        return _normalized(row)
    if hypothesis.startswith(MIS_PREFIX):
        signature = question.options_for(hypothesis[len(MIS_PREFIX):])
        if signature:
            mean_c = float(params["consistency"])
            c = mean_c if consistency is None else float(consistency)
            c = min(max(c, 0.0), 1.0 - 1e-6)
            # The holder's non-signature answers split between correct and the
            # other distractors in the fitted ratio, whatever this question's
            # own consistency (so no outcome the fit saw gets probability 0).
            share_correct = min(max(float(params["holder_correct"]) / max(1.0 - mean_c, 1e-9), 0.0), 1.0)
            rest = [d for d in distractors if d not in signature]
            if not rest:
                share_correct = 1.0
            row[question.correct] = (1.0 - c) * share_correct
            for option in signature:
                row[option] = c / len(signature)
            if rest:
                row.update(_spread({d: 1.0 for d in rest}, (1.0 - c) * (1.0 - share_correct)))
            return _normalized(row)
    # Off-target misconception, or `other`: the unsure class's behaviour.
    non_holder(float(params["unsure_correct"]), float(params["unsure_designated"]))
    return _normalized(row)


def hand_set_row(hypothesis: str, question: EediQuestion) -> dict[str, float]:
    """Today's ordinal-vocabulary contrast-card row mapped onto four options.

    Slots: ``knows`` reads ``robust_initial_grasp``; a misconception on a
    question that targets it reads ``confuses_with_neighbor``; an off-target
    misconception and ``other`` read ``other_or_unknown``. Outcomes:
    ``correct_target_reason`` + ``correct_weak_reason`` -> the correct option;
    ``confusable_signature`` -> the hypothesis's labelled distractor (for the
    other slots: the labelled distractors); ``other_systematic_error`` -> the
    remaining distractors. ``hedge``/``unanswered`` do not exist on a forced
    choice and are dropped (the row is renormalized).
    """

    if hypothesis == HYP_KNOWS:
        slot = "robust_initial_grasp"
        signature: tuple[str, ...] = tuple(sorted(question.misconception_by_option))
    elif hypothesis.startswith(MIS_PREFIX) and question.options_for(hypothesis[len(MIS_PREFIX):]):
        slot = "confuses_with_neighbor"
        signature = question.options_for(hypothesis[len(MIS_PREFIX):])
    else:
        slot = "other_or_unknown"
        signature = tuple(sorted(question.misconception_by_option))
    words = CONTRAST_CONFUSABLE_DEFAULT_ROWS[slot]
    weight = {outcome: ORDINAL_VOCABULARY[word] for outcome, word in words.items()}
    distractors = question.distractors
    if not signature:
        signature = distractors
    rest = [d for d in distractors if d not in signature] or list(distractors)
    row = {option: 0.0 for option in OPTIONS}
    row[question.correct] = weight["correct_target_reason"] + weight["correct_weak_reason"]
    for option in signature:
        row[option] += weight["confusable_signature"] / len(signature)
    for option in rest:
        row[option] += weight["other_systematic_error"] / len(rest)
    return _normalized(row)


def system_rows(
    model: str,
    scenario: Scenario,
    question: EediQuestion,
) -> dict[str, dict[str, float]]:
    """``{hypothesis: {option: p}}``: the instrument rows the selectors see."""

    if model == "hand_set":
        return {h: hand_set_row(h, question) for h in scenario.hypotheses}
    if model == "eedi_fitted":
        return {h: eedi_row(h, question, scenario.truth.values) for h in scenario.hypotheses}
    raise ValueError(f"unknown system model {model!r}")


@dataclass
class TrueLearner:
    """One simulated learner: a true hypothesis and per-question consistency draws."""

    scenario: Scenario
    hypothesis: str
    rng: np.random.Generator
    item_consistency: dict[str, float] = field(default_factory=dict)

    def consistency_for(self, question: EediQuestion) -> float:
        if question.question_id not in self.item_consistency:
            mean = float(self.scenario.truth["consistency"])
            kappa = self.scenario.truth.consistency_concentration
            if kappa is None or kappa <= 0:
                draw = mean
            else:
                # Seeded per question, not per learner: the question's own pull.
                seed = int(hashlib.sha256(f"{self.scenario.subject_id}:{question.question_id}".encode()).hexdigest()[:8], 16)
                draw = float(np.random.default_rng(seed).beta(mean * kappa, (1.0 - mean) * kappa))
            self.item_consistency[question.question_id] = draw
        return self.item_consistency[question.question_id]

    def row(self, question: EediQuestion) -> dict[str, float]:
        return eedi_row(
            self.hypothesis, question, self.scenario.truth.values, consistency=self.consistency_for(question)
        )

    def answer(self, question: EediQuestion) -> str:
        row = self.row(question)
        options = list(OPTIONS)
        return str(self.rng.choice(options, p=[row[o] for o in options]))


def with_truth(scenarios: Sequence[Scenario], **overrides: float) -> list[Scenario]:
    """The same scenarios with some response parameters replaced.

    Used to ask "what if the instrument were stronger than Eedi's multiple
    choice" (a free-text explanation graded by a model plausibly separates a
    misconception better than a distractor choice does). The replaced values
    apply to the truth and to the ``eedi_fitted`` system model alike.
    """

    out: list[Scenario] = []
    for scenario in scenarios:
        values = dict(scenario.truth.values)
        values.update({k: float(v) for k, v in overrides.items()})
        if "consistency" in overrides:
            # Keep the holder's correct : other-distractor split as fitted.
            old_c = float(scenario.truth.values["consistency"])
            values["holder_correct"] = (
                (1.0 - values["consistency"]) * float(scenario.truth.values["holder_correct"]) / max(1.0 - old_c, 1e-9)
            )
        truth = TruthParams(values, scenario.truth.consistency_concentration, scenario.truth.source + "+override")
        out.append(
            Scenario(scenario.subject_id, scenario.subject_name, scenario.hypotheses, scenario.questions,
                     scenario.prior, truth)
        )
    return out


def entropy(distribution: Mapping[str, float]) -> float:
    return -sum(p * math.log(p) for p in distribution.values() if p > 0)


def model_misfit(scenarios: Sequence[Scenario], model: str) -> dict[str, float]:
    """Per-row L-infinity distance between a system model and the per-question truth.

    This is the measured model error that the ±delta stress test is meant to
    cover (``evsi.PERTURBATION_DELTA``).
    """

    gaps: list[float] = []
    for scenario in scenarios:
        learner = TrueLearner(scenario, HYP_KNOWS, np.random.default_rng(0))
        for question in scenario.questions:
            rows = system_rows(model, scenario, question)
            for hypothesis in scenario.hypotheses:
                learner.hypothesis = hypothesis
                truth = learner.row(question)
                gaps.append(max(abs(rows[hypothesis][o] - truth[o]) for o in OPTIONS))
    array = np.asarray(gaps, dtype=float)
    if array.size == 0:
        return {}
    return {
        "rows": int(array.size),
        "median": round(float(np.median(array)), 4),
        "p75": round(float(np.quantile(array, 0.75)), 4),
        "p90": round(float(np.quantile(array, 0.90)), 4),
        "max": round(float(array.max()), 4),
    }

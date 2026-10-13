"""Fit a misconception response model to Eedi's real answer patterns.

What the simulator needs, and what the live system hand-sets today:

* **consistency** ``c`` = P(the learner picks the distractor that diagnoses
  their misconception | they hold it, the item targets it). Live: the ordinal
  word ``dominant`` (0.60 raw, about 0.83 once a contrast card's row is
  normalized), ``probe.irt.err_low_frac`` 0.80, the bridge sensitivity 0.60.
* **false alarm** ``f`` = P(that distractor | the learner does not hold it).
  Live: ``probe.irt.unfamiliar_error_leak`` 0.20 (shared across errors), the
  bridge specificity 0.90.
* **slip** ``s`` = P(wrong | the learner knows it). Live: implied by
  ``probe.irt.theta_mastered`` 2.0 (P(low) about 0.05 at b = 0).
* **holder / unsure success**: P(correct) for a misconception holder and for a
  learner with no systematic error. Live: ``theta_unfamiliar`` -2.0.

Eedi NeurIPS 2020 has the answers but no misconception labels, so the fit
finds them: within a level-3 subject, distractor pairs that the *same*
students pick together far more often than chance (co-selection lift) are
taken to diagnose one misconception; three questions whose designated
distractors are pairwise linked form a **misconception triple**. On each
triple a three-class latent class model (knows / holds the misconception /
unsure) over the three answers (correct, designated distractor, other
distractor) is identified (26 free cells, 20 parameters) and fitted by EM.

Selection and fit use disjoint students (even ``UserId`` select the triples,
odd ``UserId`` fit them), so picking high-lift triples does not inflate the
fitted consistency with the same noise that selected it. What the method
cannot rule out: a triple whose distractors target related-but-different
misconceptions (that biases ``c`` *down*), and a "holder" class that mixes
partial holders (also down). Read ``c`` as a population lower-ish estimate.

Persistence (for the Part C population prior): with answer times, the three
answers of a triple are ordered; after a designated error on the first
encounter, how many of the two later encounters repeat it, versus after a
correct first answer. The difference is the excess repeat-error rate an
unresolved misconception causes per later encounter, under Eedi's ordinary
teaching (so a lower bound on the cost of leaving it unresolved).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

import numpy as np

from learnloop.evsi_calibration.eedi import NeuripsResponses

RESPONSE_FIT_VERSION = "eedi_triple_lca_v1"

#: Answer categories on a triple item.
CORRECT, DESIGNATED, OTHER = 0, 1, 2
CLASSES = ("knows", "holds", "unsure")


@dataclass(frozen=True)
class FitSettings:
    min_pair_overlap: int = 150
    min_triple_overlap: int = 200
    min_lift: float = 2.0
    min_option_count: int = 10
    max_triples_per_subject: int = 6
    max_questions_per_subject: int = 400
    max_users_per_subject: int = 20000
    em_iterations: int = 600
    bootstrap: int = 500
    seed: int = 20261012

    def as_dict(self) -> dict[str, Any]:
        return dict(self.__dict__)


@dataclass(frozen=True)
class Estimate:
    """A pooled estimate across triples: median, mean and a bootstrap CI of the median."""

    median: float
    mean: float
    lower: float
    upper: float
    n: int

    def as_dict(self) -> dict[str, Any]:
        return {
            "median": round(self.median, 4),
            "mean": round(self.mean, 4),
            "ci95": [round(self.lower, 4), round(self.upper, 4)],
            "n": self.n,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "Estimate":
        lower, upper = payload.get("ci95") or [payload["median"], payload["median"]]
        return cls(float(payload["median"]), float(payload["mean"]), float(lower), float(upper), int(payload["n"]))


@dataclass(frozen=True)
class TripleFit:
    subject_id: int
    questions: tuple[int, int, int]
    designated: tuple[int, int, int]
    n: int
    min_lift: float
    prevalence: Mapping[str, float]
    #: class -> per item [P(correct), P(designated), P(other)].
    theta: Mapping[str, Sequence[Sequence[float]]]
    persistence: Mapping[str, float] | None = None

    def params(self) -> dict[str, float]:
        def mean(cls: str, category: int) -> float:
            return float(np.mean([row[category] for row in self.theta[cls]]))

        return {
            "consistency": mean("holds", DESIGNATED),
            "holder_correct": mean("holds", CORRECT),
            "unsure_designated": mean("unsure", DESIGNATED),
            "unsure_correct": mean("unsure", CORRECT),
            "knower_slip": 1.0 - mean("knows", CORRECT),
            "knower_designated": mean("knows", DESIGNATED),
            "prevalence_knows": float(self.prevalence["knows"]),
            "prevalence_holds": float(self.prevalence["holds"]),
            "prevalence_unsure": float(self.prevalence["unsure"]),
        }

    def as_dict(self) -> dict[str, Any]:
        return {
            "subject_id": self.subject_id,
            "questions": list(self.questions),
            "designated": list(self.designated),
            "n": self.n,
            "min_lift": round(self.min_lift, 4),
            "prevalence": {k: round(float(v), 6) for k, v in self.prevalence.items()},
            "theta": {k: [[round(float(x), 6) for x in row] for row in rows] for k, rows in self.theta.items()},
            "persistence": dict(self.persistence) if self.persistence is not None else None,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "TripleFit":
        return cls(
            subject_id=int(payload["subject_id"]),
            questions=tuple(int(v) for v in payload["questions"]),  # type: ignore[arg-type]
            designated=tuple(int(v) for v in payload["designated"]),  # type: ignore[arg-type]
            n=int(payload["n"]),
            min_lift=float(payload["min_lift"]),
            prevalence=dict(payload["prevalence"]),
            theta={k: [list(row) for row in rows] for k, rows in payload["theta"].items()},
            persistence=payload.get("persistence"),
        )


PARAMETERS = (
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


@dataclass(frozen=True)
class ResponseFit:
    """The fitted response model: pooled estimates, per-subject medians, dispersion."""

    source: Mapping[str, Any]
    triples: tuple[TripleFit, ...]
    pooled: Mapping[str, Estimate]
    by_subject: Mapping[int, Mapping[str, float]]
    #: Beta concentration of item-level consistency around its mean (method of
    #: moments, sampling noise removed): how much one question's consistency
    #: differs from another's.
    consistency_concentration: float | None
    persistence: Mapping[str, Estimate] = field(default_factory=dict)
    version: str = RESPONSE_FIT_VERSION

    def param(self, name: str, subject_id: int | None = None) -> float:
        if subject_id is not None:
            subject = self.by_subject.get(subject_id)
            if subject is not None and name in subject:
                return float(subject[name])
        return float(self.pooled[name].median)

    def as_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "source": dict(self.source),
            "pooled": {k: v.as_dict() for k, v in self.pooled.items()},
            "persistence": {k: v.as_dict() for k, v in self.persistence.items()},
            "consistency_concentration": (
                round(self.consistency_concentration, 3) if self.consistency_concentration is not None else None
            ),
            "by_subject": {
                str(subject): {k: round(float(v), 4) for k, v in params.items()}
                for subject, params in sorted(self.by_subject.items())
            },
            "triples": [triple.as_dict() for triple in self.triples],
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "ResponseFit":
        return cls(
            source=dict(payload.get("source") or {}),
            triples=tuple(TripleFit.from_dict(t) for t in payload.get("triples") or ()),
            pooled={k: Estimate.from_dict(v) for k, v in (payload.get("pooled") or {}).items()},
            by_subject={int(k): dict(v) for k, v in (payload.get("by_subject") or {}).items()},
            consistency_concentration=payload.get("consistency_concentration"),
            persistence={k: Estimate.from_dict(v) for k, v in (payload.get("persistence") or {}).items()},
            version=str(payload.get("version") or RESPONSE_FIT_VERSION),
        )


# -- triple search -----------------------------------------------------------------------------


def _pair_lifts(
    answers: np.ndarray,
    users: np.ndarray,
    q_index: np.ndarray,
    correct_by_q: np.ndarray,
    n_questions: int,
    settings: FitSettings,
) -> dict[tuple[int, int], tuple[float, int, int]]:
    """Best co-selection lift per question pair: (i, j) -> (lift, di, dj), i < j.

    ``di``/``dj`` are option indices 1..4 (never the correct option). Lift is
    computed among the students who answered both questions.
    """

    unique_users, user_rows = np.unique(users, return_inverse=True)
    n_users = unique_users.shape[0]
    cols = q_index * 4 + (answers.astype(np.int64) - 1)
    matrix = np.zeros((n_users, n_questions * 4), dtype=np.float32)
    matrix[user_rows, cols] = 1.0
    co = matrix.T @ matrix  # (4Q, 4Q)
    co4 = co.reshape(n_questions, 4, n_questions, 4)  # [i, di, j, dj]
    answered = co4.sum(axis=(1, 3))  # (Q, Q) overlap counts
    marg_i = co4.sum(axis=3)  # [i, di, j]: option di of i among those who answered j
    marg_j = co4.sum(axis=1)  # [i, j, dj]: option dj of j among those who answered i
    minimum = settings.min_option_count
    wrong = np.ones((n_questions, 4), dtype=bool)
    valid_correct = (correct_by_q >= 1) & (correct_by_q <= 4)
    wrong[np.flatnonzero(valid_correct), correct_by_q[valid_correct] - 1] = False
    upper = np.arange(n_questions)[:, None] < np.arange(n_questions)[None, :]
    mask = (
        (co4 >= minimum)
        & (marg_i[..., None] >= minimum)
        & (marg_j[:, None, :, :] >= minimum)
        & (answered[:, None, :, None] >= settings.min_pair_overlap)
        & wrong[:, :, None, None]
        & wrong[None, None, :, :]
        & upper[:, None, :, None]
    )
    with np.errstate(divide="ignore", invalid="ignore"):
        lift = co4 * answered[:, None, :, None] / (marg_i[..., None] * marg_j[:, None, :, :])
    lift = np.where(mask, lift, 0.0)
    flat = lift.transpose(0, 2, 1, 3).reshape(n_questions, n_questions, 16)
    best_index = flat.argmax(axis=2)
    best_value = flat.max(axis=2)
    best: dict[tuple[int, int], tuple[float, int, int]] = {}
    for i, j in zip(*np.nonzero(best_value > 0.0)):
        index = int(best_index[i, j])
        best[(int(i), int(j))] = (float(best_value[i, j]), index // 4 + 1, index % 4 + 1)
    return best


def _triples_from_pairs(
    best: Mapping[tuple[int, int], tuple[float, int, int]],
    settings: FitSettings,
) -> list[tuple[float, tuple[int, int, int], tuple[int, int, int]]]:
    """Triples whose three pairwise best distractor choices agree, best first."""

    def lookup(a: int, b: int) -> tuple[float, int, int] | None:
        if a < b:
            return best.get((a, b))
        hit = best.get((b, a))
        return (hit[0], hit[2], hit[1]) if hit else None

    partners: dict[int, list[int]] = {}
    for (i, j), (lift, _di, _dj) in best.items():
        if lift >= settings.min_lift:
            partners.setdefault(i, []).append(j)
            partners.setdefault(j, []).append(i)
    found: list[tuple[float, tuple[int, int, int], tuple[int, int, int]]] = []
    for i in sorted(partners):
        mates = sorted(m for m in partners[i] if m > i)
        for a_index, j in enumerate(mates):
            ij = lookup(i, j)
            if ij is None:
                continue
            for k in mates[a_index + 1:]:
                ik, jk = lookup(i, k), lookup(j, k)
                if ik is None or jk is None:
                    continue
                if ik[1] != ij[1] or jk[1] != ij[2] or jk[2] != ik[2]:
                    continue
                lift = min(ij[0], ik[0], jk[0])
                if lift < settings.min_lift:
                    continue
                found.append((lift, (i, j, k), (ij[1], ij[2], ik[2])))
    found.sort(key=lambda t: (-t[0], t[1]))
    return found


def _em_three_class(table: Mapping[tuple[int, int, int], int], iterations: int) -> tuple[np.ndarray, np.ndarray]:
    """Three-class latent class model on three 3-category items (deterministic init)."""

    cells = np.asarray(list(table.keys()), dtype=np.int64)
    counts = np.asarray(list(table.values()), dtype=float)
    weights = np.array([0.5, 0.2, 0.3])
    theta = np.array(
        [
            [[0.90, 0.05, 0.05]] * 3,  # knows
            [[0.15, 0.75, 0.10]] * 3,  # holds the misconception
            [[0.35, 0.30, 0.35]] * 3,  # unsure
        ]
    )
    for _ in range(iterations):
        likelihood = np.stack(
            [
                weights[c] * theta[c, 0, cells[:, 0]] * theta[c, 1, cells[:, 1]] * theta[c, 2, cells[:, 2]]
                for c in range(3)
            ],
            axis=1,
        )
        total = likelihood.sum(axis=1, keepdims=True)
        total[total <= 0] = 1.0
        resp = likelihood / total
        mass = counts[:, None] * resp
        weights = mass.sum(axis=0) / counts.sum()
        for c in range(3):
            for item in range(3):
                for category in range(3):
                    theta[c, item, category] = mass[cells[:, item] == category, c].sum()
                row = theta[c, item].sum()
                theta[c, item] = theta[c, item] / row if row > 0 else 1.0 / 3.0
        theta = np.clip(theta, 1e-6, 1.0)
    return weights, theta


def _label_classes(theta: np.ndarray) -> dict[str, int]:
    knows = int(np.argmax(theta[:, :, CORRECT].mean(axis=1)))
    rest = [c for c in range(3) if c != knows]
    holds = max(rest, key=lambda c: float(theta[c, :, DESIGNATED].mean()))
    unsure = next(c for c in rest if c != holds)
    return {"knows": knows, "holds": holds, "unsure": unsure}


def _persistence(categories: np.ndarray, minutes: np.ndarray) -> dict[str, float] | None:
    """Repeat-error rates after a designated vs a correct first encounter."""

    usable = (minutes >= 0).all(axis=1)
    if usable.sum() < 30:
        return None
    categories, minutes = categories[usable], minutes[usable]
    order = np.argsort(minutes, axis=1, kind="stable")
    ordered = np.take_along_axis(categories, order, axis=1)
    first = ordered[:, 0]
    later_designated = (ordered[:, 1:] == DESIGNATED).sum(axis=1)
    after_designated = later_designated[first == DESIGNATED]
    after_correct = later_designated[first == CORRECT]
    if after_designated.size < 10 or after_correct.size < 10:
        return None
    rate_d = float(after_designated.mean()) / 2.0
    rate_c = float(after_correct.mean()) / 2.0
    return {
        "first_designated_n": int(after_designated.size),
        "first_correct_n": int(after_correct.size),
        "repeat_rate_after_designated": round(rate_d, 6),
        "designated_rate_after_correct": round(rate_c, 6),
        "excess_repeat_rate": round(rate_d - rate_c, 6),
    }


def _bootstrap_median(values: np.ndarray, rng: np.random.Generator, draws: int) -> tuple[float, float]:
    if values.size == 0:
        return float("nan"), float("nan")
    picks = rng.integers(0, values.size, size=(draws, values.size))
    medians = np.median(values[picks], axis=1)
    return float(np.quantile(medians, 0.025)), float(np.quantile(medians, 0.975))


def _estimate(values: Sequence[float], rng: np.random.Generator, draws: int) -> Estimate:
    array = np.asarray([v for v in values if v is not None and not math.isnan(v)], dtype=float)
    if array.size == 0:
        return Estimate(float("nan"), float("nan"), float("nan"), float("nan"), 0)
    lower, upper = _bootstrap_median(array, rng, draws)
    return Estimate(float(np.median(array)), float(array.mean()), lower, upper, int(array.size))


def _consistency_concentration(triples: Sequence[TripleFit]) -> float | None:
    """Beta concentration of item-level consistency (between-item spread only)."""

    values: list[float] = []
    noise: list[float] = []
    for triple in triples:
        holders = max(triple.n * float(triple.prevalence["holds"]), 1.0)
        for row in triple.theta["holds"]:
            c = float(row[DESIGNATED])
            values.append(c)
            noise.append(c * (1.0 - c) / holders)
    if len(values) < 6:
        return None
    mean = float(np.mean(values))
    between = float(np.var(values, ddof=1)) - float(np.mean(noise))
    if between <= 1e-6:
        return None
    return max(mean * (1.0 - mean) / between - 1.0, 1.0)


def fit_response_model(
    responses: NeuripsResponses,
    *,
    settings: FitSettings | None = None,
    subjects: Sequence[int] | None = None,
) -> ResponseFit:
    """Find misconception triples per subject and fit the latent class model."""

    settings = settings or FitSettings()
    leaf = responses.leaf_subject
    question_subject = np.full(int(responses.question.max()) + 1, -1, dtype=np.int64)
    for question, subject in leaf.items():
        if question < question_subject.shape[0]:
            question_subject[question] = subject
    row_subject = question_subject[responses.question]
    wanted = set(int(s) for s in subjects) if subjects is not None else None
    triples: list[TripleFit] = []
    subject_ids = sorted(int(s) for s in np.unique(row_subject) if s >= 0)
    for subject in subject_ids:
        if wanted is not None and subject not in wanted:
            continue
        rows = np.flatnonzero(row_subject == subject)
        if rows.size < settings.min_triple_overlap * 3:
            continue
        triples.extend(_fit_subject(responses, subject, rows, settings))
    return assemble_response_fit(
        triples,
        settings=settings,
        source={
            "dataset": "Eedi NeurIPS 2020 Education Challenge (public archive)",
            "task": responses.task,
            "source_hash": responses.source_hash,
            "rows": responses.rows,
            "settings": settings.as_dict(),
            "notes": list(responses.notes),
        },
    )


def assemble_response_fit(
    triples: Sequence[TripleFit],
    *,
    settings: FitSettings,
    source: Mapping[str, Any],
) -> ResponseFit:
    """Pool fitted triples into a :class:`ResponseFit` (medians, subject medians,
    dispersion, persistence). Shared by the single-family fit and the
    multi-family stage's refit on its fit split (:mod:`.family_fit`)."""

    rng = np.random.default_rng(settings.seed)
    pooled = {
        name: _estimate([t.params()[name] for t in triples], rng, settings.bootstrap) for name in PARAMETERS
    }
    by_subject: dict[int, dict[str, float]] = {}
    grouped: dict[int, list[TripleFit]] = {}
    for triple in triples:
        grouped.setdefault(triple.subject_id, []).append(triple)
    for subject, members in grouped.items():
        if len(members) >= 2:
            by_subject[subject] = {
                name: float(np.median([m.params()[name] for m in members])) for name in PARAMETERS
            }
            by_subject[subject]["triples"] = float(len(members))
    persistence: dict[str, Estimate] = {}
    with_persistence = [t.persistence for t in triples if t.persistence]
    if with_persistence:
        for key in ("repeat_rate_after_designated", "designated_rate_after_correct", "excess_repeat_rate"):
            persistence[key] = _estimate([float(p[key]) for p in with_persistence], rng, settings.bootstrap)
    return ResponseFit(
        source={**dict(source), "subjects_with_triples": len(grouped)},
        triples=tuple(triples),
        pooled=pooled,
        by_subject=by_subject,
        consistency_concentration=_consistency_concentration(triples),
        persistence=persistence,
    )


def _fit_subject(
    responses: NeuripsResponses,
    subject: int,
    rows: np.ndarray,
    settings: FitSettings,
) -> list[TripleFit]:
    question = responses.question[rows]
    user = responses.user[rows]
    answer = responses.answer[rows]
    correct = responses.correct_option[rows]
    minutes = responses.answered_minute[rows] if responses.answered_minute is not None else None
    # Bound the matrix: the most-answered questions only.
    q_ids, q_counts = np.unique(question, return_counts=True)
    if q_ids.size < 3:
        return []
    if q_ids.size > settings.max_questions_per_subject:
        keep = q_ids[np.argsort(-q_counts, kind="stable")[: settings.max_questions_per_subject]]
        keep.sort()
        mask = np.isin(question, keep)
        question, user, answer, correct = question[mask], user[mask], answer[mask], correct[mask]
        minutes = minutes[mask] if minutes is not None else None
        q_ids = keep
    q_lookup = {int(q): i for i, q in enumerate(q_ids.tolist())}
    q_index = np.asarray([q_lookup[int(q)] for q in question.tolist()], dtype=np.int64)
    correct_by_q = np.zeros(q_ids.size, dtype=np.int64)
    correct_by_q[q_index] = correct
    select = user % 2 == 0
    fit = ~select
    sel_users = np.unique(user[select])
    if sel_users.size > settings.max_users_per_subject:
        chooser = np.random.default_rng(settings.seed + subject)
        sel_users = np.sort(chooser.choice(sel_users, settings.max_users_per_subject, replace=False))
        select = select & np.isin(user, sel_users)
    best = _pair_lifts(answer[select], user[select], q_index[select], correct_by_q, q_ids.size, settings)
    candidates = _triples_from_pairs(best, settings)
    if not candidates:
        return []
    # Fit-half lookup: (user, question index) -> (category-agnostic answer, minute).
    fit_rows = np.flatnonzero(fit)
    answer_of: dict[tuple[int, int], tuple[int, int]] = {}
    for r in fit_rows.tolist():
        answer_of[(int(user[r]), int(q_index[r]))] = (
            int(answer[r]),
            int(minutes[r]) if minutes is not None else -1,
        )
    users_by_q: dict[int, set[int]] = {}
    for (u, qi) in answer_of:
        users_by_q.setdefault(qi, set()).add(u)
    used: set[int] = set()
    fitted: list[TripleFit] = []
    for lift, items, designated in candidates:
        if len(fitted) >= settings.max_triples_per_subject:
            break
        if used & set(items):
            continue
        common = users_by_q.get(items[0], set()) & users_by_q.get(items[1], set()) & users_by_q.get(items[2], set())
        if len(common) < settings.min_triple_overlap:
            continue
        table: dict[tuple[int, int, int], int] = {}
        categories = np.zeros((len(common), 3), dtype=np.int64)
        stamps = np.zeros((len(common), 3), dtype=np.int64)
        for row_index, u in enumerate(sorted(common)):
            cats = []
            for position, (qi, d) in enumerate(zip(items, designated)):
                value, minute = answer_of[(u, qi)]
                category = CORRECT if value == correct_by_q[qi] else (DESIGNATED if value == d else OTHER)
                cats.append(category)
                categories[row_index, position] = category
                stamps[row_index, position] = minute
            key = (cats[0], cats[1], cats[2])
            table[key] = table.get(key, 0) + 1
        weights, theta = _em_three_class(table, settings.em_iterations)
        labels = _label_classes(theta)
        fitted.append(
            TripleFit(
                subject_id=subject,
                questions=tuple(int(q_ids[i]) for i in items),  # type: ignore[arg-type]
                designated=tuple(int(d) for d in designated),  # type: ignore[arg-type]
                n=len(common),
                min_lift=float(lift),
                prevalence={name: float(weights[idx]) for name, idx in labels.items()},
                theta={name: theta[idx].tolist() for name, idx in labels.items()},
                persistence=_persistence(categories, stamps) if minutes is not None else None,
            )
        )
        used |= set(items)
    return fitted

"""Fit structurally different simulator families to the same Eedi answers.

RankCert (arXiv 2609.26069): simulators that fit learner data equally well can
disagree about which policy is best, so a conclusion drawn under one family is
a statement about that family. This module fits four families to the same
students on the same misconception triples (:mod:`.family_data`), then scores
each on held-out students (``UserId % 8 == 7``):

``lca``
    The single-family study's three-class latent class model (knows / holds the
    triple's misconception / unsure), refitted per triple on the fit split.
``cdm``
    A multiple-choice cognitive diagnosis model (MC-DINA, de la Torre 2009,
    with a DINO-style misconception trigger), fitted per **subject**: a learner
    has a binary skill attribute shared by every item of the subject and binary
    misconception attributes (one per triple, at most two held at once). The
    Q-matrix is the misconception labelling: each item's designated distractor
    is coded with its triple's attribute. An item has four response groups
    (skill x triggered), each a free categorical over the four options. Unlike
    the latent class model, misconceptions can co-occur, a skilled learner can
    hold one, and one learner's skill links the subject's triples.
``nrm``
    An IRT family: continuous ability ``theta`` and a continuous misconception
    trait ``eta`` (independent standard normals), each item a Bock nominal
    response model over its four options in which only the designated
    distractor's logit depends on ``eta``
    (``z_d = a_d theta + lambda eta + b_d``). Fitted per triple by marginal
    maximum likelihood (EM on a Gauss-Hermite grid, MAP with a weak normal
    prior on the item parameters). Holding a misconception is a matter of
    degree here.
``lta``
    The learning family: a latent transition (hidden Markov) model with the
    latent class model's three states whose state can change between
    encounters, in time order. Two transition matrices shared across all
    triples: within one session (encounters at most an hour apart: a check
    plus whatever feedback Eedi showed) and later (days, with teaching in
    between). Per-triple emissions and starting mix. This is the family where a
    learner learns during probing.

Plus ``marginal``: each item's option frequencies (no latent structure), the
baseline every family must beat.

Validation task (common to every family): on a held-out student's triple,
predict each answer from the other two. Reported: log loss over the three
categories (correct / designated / other) and over the four options, the
calibration (ECE) of the category forecasts, the AUC of P(correct), and the
**distractor-choice calibration** (given a wrong answer, the forecast share of
the designated distractor against how often it was the one chosen). RankCert's
adequacy gate is applied: AUC >= 0.55, NLL gain over the marginal >= 0.002
nats, ECE <= 0.08.
"""

from __future__ import annotations

import math
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass, field
from itertools import combinations
from typing import Any, Mapping, Sequence

import numpy as np

from learnloop.evsi_calibration.family_data import (
    GAP_LATER,
    GAP_SAME_SESSION,
    SubjectData,
    TripleData,
    category_counts,
    item_roles,
)
from learnloop.evsi_calibration.response_fit import (
    CORRECT,
    DESIGNATED,
    OTHER,
    FitSettings,
    ResponseFit,
    TripleFit,
    _em_three_class,
    _label_classes,
    _persistence,
    assemble_response_fit,
)

FAMILY_FIT_VERSION = "evsi_multisim_family_fit_v1"
FAMILIES = ("lca", "cdm", "nrm", "lta")
STATES = ("knows", "holds", "unsure")
#: RankCert adequacy gate (arXiv 2609.26069 §3.2).
ADEQUACY_MIN_AUC = 0.55
ADEQUACY_MIN_NLL_GAIN = 0.002
ADEQUACY_MAX_ECE = 0.08
#: Most misconceptions a cognitive-diagnosis learner holds at once.
CDM_MAX_HELD = 2


@dataclass(frozen=True)
class FamilyFitSettings:
    lca_iterations: int = 600
    cdm_iterations: int = 400
    cdm_smoothing: float = 0.5
    nrm_iterations: int = 150
    nrm_nodes: int = 11
    nrm_prior_sd: float = 2.5
    lta_iterations: int = 300
    lta_smoothing: float = 0.5
    bootstrap: int = 300
    seed: int = 20261013
    workers: int = 8

    def as_dict(self) -> dict[str, Any]:
        return dict(self.__dict__)


# -- LCA (refit on the fit split) ---------------------------------------------------------------


def fit_lca(triples: Sequence[TripleData], settings: FamilyFitSettings) -> list[TripleFit]:
    fits: list[TripleFit] = []
    for triple in triples:
        categories = triple.categories()
        if categories.shape[0] < 30:
            continue
        weights, theta = _em_three_class(category_counts(categories), settings.lca_iterations)
        labels = _label_classes(theta)
        fits.append(
            TripleFit(
                subject_id=triple.subject_id,
                questions=triple.questions,
                designated=triple.designated,
                n=triple.n,
                min_lift=float("nan"),
                prevalence={name: float(weights[idx]) for name, idx in labels.items()},
                theta={name: theta[idx].tolist() for name, idx in labels.items()},
                persistence=_persistence(categories, triple.minutes),
            )
        )
    return fits


def lca_response_fit(fits: Sequence[TripleFit], *, seed: int, source: Mapping[str, Any]) -> ResponseFit:
    return assemble_response_fit(fits, settings=FitSettings(seed=seed), source=source)


def _lca_tables(fit: TripleFit) -> tuple[np.ndarray, np.ndarray]:
    prevalence = np.asarray([fit.prevalence[s] for s in STATES], dtype=float)
    theta = np.asarray([fit.theta[s] for s in STATES], dtype=float)  # (3 states, 3 items, 3 cats)
    return prevalence, theta


def _three_to_four(probabilities: np.ndarray) -> np.ndarray:
    """(..., 3) categories -> (..., 4) roles: 'other' split evenly (as the
    simulator's latent class rows split it)."""

    out = np.zeros(probabilities.shape[:-1] + (4,))
    out[..., 0] = probabilities[..., CORRECT]
    out[..., 1] = probabilities[..., DESIGNATED]
    out[..., 2] = probabilities[..., OTHER] / 2.0
    out[..., 3] = probabilities[..., OTHER] / 2.0
    return out


def predict_lca(fit: TripleFit, roles: np.ndarray) -> np.ndarray:
    """(n, 3 items, 4 roles) leave-one-out predictions on a triple."""

    prevalence, theta = _lca_tables(fit)
    categories = np.minimum(roles, OTHER)
    n = roles.shape[0]
    # per student per state: likelihood of each item's observed category
    like = np.stack([theta[:, i, categories[:, i]] for i in range(3)], axis=2)  # (3 states, n, 3 items)
    out = np.zeros((n, 3, 4))
    for i in range(3):
        others = [k for k in range(3) if k != i]
        weight = prevalence[:, None] * like[:, :, others[0]] * like[:, :, others[1]]  # (3, n)
        weight = weight / weight.sum(axis=0, keepdims=True)
        out[:, i, :] = _three_to_four(weight.T @ theta[:, i, :])
    return out


# -- marginal baseline ----------------------------------------------------------------------------


def fit_marginal(triples: Sequence[TripleData]) -> dict[int, np.ndarray]:
    out: dict[int, np.ndarray] = {}
    for triple in triples:
        roles = triple.role_options()
        table = np.zeros((3, 4))
        for i in range(3):
            table[i] = np.bincount(roles[:, i], minlength=4) + 0.5
        out[triple.index] = table / table.sum(axis=1, keepdims=True)
    return out


# -- CDM: MC-DINA with a DINO misconception trigger ------------------------------------------------


def cdm_profiles(attributes: int, max_held: int = CDM_MAX_HELD) -> list[tuple[int, tuple[int, ...]]]:
    held_sets: list[tuple[int, ...]] = [()]
    for size in range(1, min(max_held, attributes) + 1):
        held_sets.extend(combinations(range(attributes), size))
    return [(skill, held) for skill in (0, 1) for held in held_sets]


def _cdm_groups(profiles: Sequence[tuple[int, tuple[int, ...]]], attribute: np.ndarray) -> np.ndarray:
    """(P, J) response group: 2*triggered + skill."""

    groups = np.zeros((len(profiles), attribute.shape[0]), dtype=np.int64)
    for p, (skill, held) in enumerate(profiles):
        triggered = np.isin(attribute, held).astype(np.int64)
        groups[p] = 2 * triggered + skill
    return groups


#: Initial role-space rows per group: untriggered without / with the skill,
#: triggered without / with the skill (correct, designated, other, other).
_CDM_INIT = np.array([
    [0.35, 0.15, 0.25, 0.25],
    [0.85, 0.03, 0.06, 0.06],
    [0.15, 0.60, 0.125, 0.125],
    [0.40, 0.45, 0.075, 0.075],
])


@dataclass(frozen=True)
class CdmSubjectFit:
    subject_id: int
    attributes: int
    questions: tuple[int, ...]
    attribute: tuple[int, ...]
    #: (J, 4 groups, 4 roles) role-space option probabilities.
    phi: np.ndarray
    profiles: tuple[tuple[int, tuple[int, ...]], ...]
    prior: np.ndarray
    n: int
    loglik: float
    iterations: int

    def as_dict(self) -> dict[str, Any]:
        return {
            "subject_id": self.subject_id,
            "attributes": self.attributes,
            "questions": list(self.questions),
            "attribute": list(self.attribute),
            "phi": np.round(self.phi, 6).tolist(),
            "profiles": [[skill, list(held)] for skill, held in self.profiles],
            "prior": np.round(self.prior, 8).tolist(),
            "n": self.n,
            "loglik": round(self.loglik, 4),
            "iterations": self.iterations,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "CdmSubjectFit":
        return cls(
            subject_id=int(payload["subject_id"]),
            attributes=int(payload["attributes"]),
            questions=tuple(int(q) for q in payload["questions"]),
            attribute=tuple(int(a) for a in payload["attribute"]),
            phi=np.asarray(payload["phi"], dtype=float),
            profiles=tuple((int(s), tuple(int(h) for h in held)) for s, held in payload["profiles"]),
            prior=np.asarray(payload["prior"], dtype=float),
            n=int(payload["n"]),
            loglik=float(payload["loglik"]),
            iterations=int(payload["iterations"]),
        )

    def summary(self) -> dict[str, float]:
        """The common quantities (as the latent class model names them) plus the
        profile structure the simulator transfers."""

        prior = self.prior
        skill = np.asarray([s for s, _ in self.profiles])
        holds = np.zeros((len(self.profiles), self.attributes))
        for p, (_s, held) in enumerate(self.profiles):
            for k in held:
                holds[p, k] = 1.0
        p_skill = float(prior[skill == 1].sum())
        p_hold_s0 = float((prior[skill == 0, None] * holds[skill == 0]).sum(axis=0).mean() / max(1.0 - p_skill, 1e-9))
        p_hold_s1 = float((prior[skill == 1, None] * holds[skill == 1]).sum(axis=0).mean() / max(p_skill, 1e-9))
        marginal = (prior[:, None] * holds).sum(axis=0)
        lifts = []
        for a, b in combinations(range(self.attributes), 2):
            joint = float((prior * holds[:, a] * holds[:, b]).sum())
            if marginal[a] > 1e-6 and marginal[b] > 1e-6:
                lifts.append(joint / (marginal[a] * marginal[b]))
        # Holder mix among triggered learners, for the consistency average.
        held_any = holds.sum(axis=1) > 0
        triggered_skill = float(prior[held_any & (skill == 1)].sum() / max(prior[held_any].sum(), 1e-9))
        phi = self.phi
        triggered = (1.0 - triggered_skill) * phi[:, 2, :] + triggered_skill * phi[:, 3, :]
        untriggered_skill0 = phi[:, 0, :]
        return {
            "consistency": float(triggered[:, 1].mean()),
            "holder_correct": float(triggered[:, 0].mean()),
            "unsure_designated": float(untriggered_skill0[:, 1].mean()),
            "unsure_correct": float(untriggered_skill0[:, 0].mean()),
            "knower_slip": float(1.0 - phi[:, 1, 0].mean()),
            "knower_designated": float(phi[:, 1, 1].mean()),
            "p_skill": p_skill,
            "p_hold_given_no_skill": p_hold_s0,
            "p_hold_given_skill": p_hold_s1,
            "pair_lift": float(np.mean(lifts)) if lifts else float("nan"),
            "p_two_held": float(prior[holds.sum(axis=1) >= 2].sum()),
            "triggered_skill_share": triggered_skill,
        }


def fit_cdm_subject(subject: SubjectData, settings: FamilyFitSettings) -> CdmSubjectFit:
    profiles = cdm_profiles(subject.attributes)
    groups = _cdm_groups(profiles, subject.attribute)
    J = subject.items
    roles = np.full(subject.options.shape, -1, dtype=np.int64)
    for j in range(J):
        lookup = np.full(5, -1, dtype=np.int64)
        for option, role in item_roles(int(subject.correct[j]), int(subject.designated[j])).items():
            lookup[option] = role
        roles[:, j] = lookup[subject.options[:, j]]
    phi = np.repeat(_CDM_INIT[None, :, :], J, axis=0).copy()
    prior = np.asarray([(0.6 if s else 0.4) * (0.1 ** len(held)) for s, held in profiles], dtype=float)
    prior /= prior.sum()
    n = roles.shape[0]
    observed = [np.flatnonzero(roles[:, j] >= 0) for j in range(J)]
    previous = -math.inf
    loglik = -math.inf
    iteration = 0
    for iteration in range(1, settings.cdm_iterations + 1):
        log_phi = np.log(phi)
        ll = np.tile(np.log(prior), (n, 1))
        for j in range(J):
            rows = observed[j]
            if rows.size:
                ll[rows] += log_phi[j][groups[:, j]][:, roles[rows, j]].T
        top = ll.max(axis=1, keepdims=True)
        weights = np.exp(ll - top)
        total = weights.sum(axis=1, keepdims=True)
        loglik = float((np.log(total) + top).sum())
        resp = weights / total
        prior = resp.sum(axis=0) + 1.0
        prior /= prior.sum()
        counts = np.full((J, 4, 4), settings.cdm_smoothing)
        for j in range(J):
            rows = observed[j]
            if not rows.size:
                continue
            by_group = resp[rows] @ np.eye(4)[groups[:, j]]  # (rows, 4 groups)
            counts[j] += by_group.T @ np.eye(4)[roles[rows, j]]
        phi = counts / counts.sum(axis=2, keepdims=True)
        if abs(loglik - previous) < 1e-7 * max(abs(loglik), 1.0):
            break
        previous = loglik
    return CdmSubjectFit(
        subject_id=subject.subject_id,
        attributes=subject.attributes,
        questions=tuple(int(q) for q in subject.questions),
        attribute=tuple(int(a) for a in subject.attribute),
        phi=phi,
        profiles=tuple(profiles),
        prior=prior,
        n=n,
        loglik=loglik,
        iterations=iteration,
    )


def predict_cdm(fit: CdmSubjectFit, position: int, roles: np.ndarray) -> np.ndarray:
    """Leave-one-out predictions on one of the subject's triples (``position``),
    conditioning only on that triple's other two answers."""

    items = [3 * position + i for i in range(3)]
    groups = _cdm_groups(fit.profiles, np.asarray(fit.attribute))
    n = roles.shape[0]
    like = np.stack([fit.phi[j][groups[:, j]][:, roles[:, i]] for i, j in enumerate(items)], axis=2)  # (P, n, 3)
    out = np.zeros((n, 3, 4))
    for i, j in enumerate(items):
        others = [k for k in range(3) if k != i]
        weight = fit.prior[:, None] * like[:, :, others[0]] * like[:, :, others[1]]
        weight = weight / weight.sum(axis=0, keepdims=True)
        out[:, i, :] = weight.T @ fit.phi[j][groups[:, j]]
    return out


# -- NRM: nominal response with a misconception trait ----------------------------------------------


def gauss_hermite_grid(nodes: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """2-D standard-normal product grid: theta, eta, weights (sum 1)."""

    x, w = np.polynomial.hermite_e.hermegauss(nodes)
    w = w / w.sum()
    theta, eta = np.meshgrid(x, x, indexing="ij")
    weights = np.outer(w, w)
    return theta.ravel(), eta.ravel(), weights.ravel()


#: Item parameter layout: a_correct, b_correct, a_designated, b_designated,
#: lambda (the misconception slope), a_other, b_other; the last distractor is
#: the reference (logit 0).
NRM_PARAMS = ("a_c", "b_c", "a_d", "b_d", "lam", "a_o", "b_o")


def nrm_logits(params: np.ndarray, theta: np.ndarray, eta: np.ndarray) -> np.ndarray:
    """(..., 4) role logits for item parameters ``params`` (..., 7)."""

    a_c, b_c, a_d, b_d, lam, a_o, b_o = (params[..., k] for k in range(7))
    zeros = np.zeros(np.broadcast(theta, eta, a_c).shape)
    return np.stack(
        [a_c * theta + b_c + zeros, a_d * theta + lam * eta + b_d + zeros, a_o * theta + b_o + zeros, zeros],
        axis=-1,
    )


def _softmax(z: np.ndarray) -> np.ndarray:
    z = z - z.max(axis=-1, keepdims=True)
    e = np.exp(z)
    return e / e.sum(axis=-1, keepdims=True)


def _nrm_item_objective(params: np.ndarray, counts: np.ndarray, theta: np.ndarray, eta: np.ndarray,
                        prior_sd: float) -> tuple[float, np.ndarray]:
    z = nrm_logits(params, theta, eta)  # (Q, 4)
    p = _softmax(z)
    log_p = np.log(np.clip(p, 1e-300, None))
    value = -float((counts * log_p).sum()) + 0.5 * float((params ** 2).sum()) / prior_sd ** 2
    residual = counts - counts.sum(axis=1, keepdims=True) * p  # d/dz of the log likelihood
    grad = np.empty(7)
    grad[0] = -(residual[:, 0] * theta).sum()
    grad[1] = -residual[:, 0].sum()
    grad[2] = -(residual[:, 1] * theta).sum()
    grad[3] = -residual[:, 1].sum()
    grad[4] = -(residual[:, 1] * eta).sum()
    grad[5] = -(residual[:, 2] * theta).sum()
    grad[6] = -residual[:, 2].sum()
    grad += params / prior_sd ** 2
    return value, grad


@dataclass(frozen=True)
class NrmTripleFit:
    triple_index: int
    subject_id: int
    params: np.ndarray  # (3 items, 7)
    n: int
    loglik: float
    iterations: int

    def as_dict(self) -> dict[str, Any]:
        return {
            "triple_index": self.triple_index,
            "subject_id": self.subject_id,
            "params": np.round(self.params, 6).tolist(),
            "n": self.n,
            "loglik": round(self.loglik, 4),
            "iterations": self.iterations,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "NrmTripleFit":
        return cls(
            triple_index=int(payload["triple_index"]),
            subject_id=int(payload["subject_id"]),
            params=np.asarray(payload["params"], dtype=float),
            n=int(payload["n"]),
            loglik=float(payload["loglik"]),
            iterations=int(payload["iterations"]),
        )


def fit_nrm_triple(payload: tuple[TripleData, FamilyFitSettings]) -> NrmTripleFit:
    from scipy.optimize import minimize

    triple, settings = payload
    roles = triple.role_options()
    theta, eta, weights = gauss_hermite_grid(settings.nrm_nodes)
    params = np.tile(np.array([1.0, 1.0, -0.3, -0.5, 1.0, -0.3, 0.0]), (3, 1))
    previous = -math.inf
    loglik = -math.inf
    iteration = 0
    log_weights = np.log(weights)
    for iteration in range(1, settings.nrm_iterations + 1):
        p = _softmax(nrm_logits(params[:, None, :], theta[None, :], eta[None, :]))  # (3, Q, 4)
        log_p = np.log(np.clip(p, 1e-300, None))
        ll = log_weights[None, :] + sum(log_p[i][:, roles[:, i]].T for i in range(3))  # (n, Q)
        top = ll.max(axis=1, keepdims=True)
        post = np.exp(ll - top)
        total = post.sum(axis=1, keepdims=True)
        loglik = float((np.log(total) + top).sum())
        post /= total
        for i in range(3):
            counts = post.T @ np.eye(4)[roles[:, i]]  # (Q, 4)
            result = minimize(_nrm_item_objective, params[i], args=(counts, theta, eta, settings.nrm_prior_sd),
                              jac=True, method="L-BFGS-B", options={"maxiter": 50})
            params[i] = result.x
        if abs(loglik - previous) < 1e-7 * max(abs(loglik), 1.0):
            break
        previous = loglik
    # eta's sign is not identified: orient it so a higher trait means more of
    # the designated distractor.
    if params[:, 4].mean() < 0:
        params[:, 4] = -params[:, 4]
    return NrmTripleFit(triple.index, triple.subject_id, params.copy(), triple.n, loglik, iteration)


def predict_nrm(fit: NrmTripleFit, roles: np.ndarray, nodes: int) -> np.ndarray:
    theta, eta, weights = gauss_hermite_grid(nodes)
    p = _softmax(nrm_logits(fit.params[:, None, :], theta[None, :], eta[None, :]))  # (3, Q, 4)
    like = np.stack([p[i][:, roles[:, i]] for i in range(3)], axis=2)  # (Q, n, 3)
    n = roles.shape[0]
    out = np.zeros((n, 3, 4))
    for i in range(3):
        others = [k for k in range(3) if k != i]
        weight = weights[:, None] * like[:, :, others[0]] * like[:, :, others[1]]
        weight = weight / weight.sum(axis=0, keepdims=True)
        out[:, i, :] = weight.T @ p[i]
    return out


# -- LTA: the learning family -----------------------------------------------------------------------


@dataclass(frozen=True)
class LtaFit:
    """Latent transition model: per-triple start mix and emissions, shared transitions."""

    #: triple index -> (3,) start mix over knows / holds / unsure.
    start: Mapping[int, np.ndarray]
    #: triple index -> (3 items, 3 states, 3 categories).
    emission: Mapping[int, np.ndarray]
    subject_of: Mapping[int, int]
    #: (2 gap types, 3, 3) row-stochastic, rows = from-state.
    transitions: np.ndarray
    transition_counts: np.ndarray
    sequences: int
    loglik: float
    iterations: int

    def as_dict(self) -> dict[str, Any]:
        return {
            "start": {str(k): np.round(v, 6).tolist() for k, v in sorted(self.start.items())},
            "emission": {str(k): np.round(v, 6).tolist() for k, v in sorted(self.emission.items())},
            "subject_of": {str(k): int(v) for k, v in sorted(self.subject_of.items())},
            "transitions": np.round(self.transitions, 6).tolist(),
            "transition_counts": np.round(self.transition_counts, 2).tolist(),
            "sequences": self.sequences,
            "loglik": round(self.loglik, 4),
            "iterations": self.iterations,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "LtaFit":
        return cls(
            start={int(k): np.asarray(v, dtype=float) for k, v in payload["start"].items()},
            emission={int(k): np.asarray(v, dtype=float) for k, v in payload["emission"].items()},
            subject_of={int(k): int(v) for k, v in payload["subject_of"].items()},
            transitions=np.asarray(payload["transitions"], dtype=float),
            transition_counts=np.asarray(payload["transition_counts"], dtype=float),
            sequences=int(payload["sequences"]),
            loglik=float(payload["loglik"]),
            iterations=int(payload["iterations"]),
        )

    def triple_fit(self, index: int) -> TripleFit:
        """This triple's emissions and start mix as a latent class triple (the
        simulator's row machinery reads these)."""

        start, emission = self.start[index], self.emission[index]
        return TripleFit(
            subject_id=int(self.subject_of[index]),
            questions=(0, 0, 0),
            designated=(0, 0, 0),
            n=0,
            min_lift=float("nan"),
            prevalence={s: float(start[k]) for k, s in enumerate(STATES)},
            theta={s: emission[:, k, :].tolist() for k, s in enumerate(STATES)},
        )


def _lta_sequences(triples: Sequence[TripleData]) -> dict[str, np.ndarray]:
    blocks: dict[str, list[np.ndarray]] = {"triple": [], "item": [], "cat": [], "gap": []}
    for t, triple in enumerate(triples):
        order, gaps = triple.time_order()
        categories = np.take_along_axis(triple.categories(), order, axis=1)
        blocks["triple"].append(np.full(triple.n, t, dtype=np.int64))
        blocks["item"].append(order)
        blocks["cat"].append(categories)
        blocks["gap"].append(gaps)
    return {k: np.concatenate(v) for k, v in blocks.items()}


def _lta_forward_backward(start: np.ndarray, emission: np.ndarray, transitions: np.ndarray,
                          seq: Mapping[str, np.ndarray]) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Posterior state marginals (n, 3 steps, 3), pair posteriors (n, 2, 3, 3), log likelihoods (n,)."""

    t_index, items, cats, gaps = seq["triple"], seq["item"], seq["cat"], seq["gap"]
    n = t_index.shape[0]
    # e[n, k, s] = emission[t, item_k, s, cat_k]
    e = np.stack([emission[t_index, items[:, k], :, cats[:, k]] for k in range(3)], axis=1)
    trans = transitions[gaps]  # (n, 2, 3, 3)
    alpha = np.zeros((n, 3, 3))
    alpha[:, 0] = start[t_index] * e[:, 0]
    for k in (1, 2):
        alpha[:, k] = np.einsum("ns,nst->nt", alpha[:, k - 1], trans[:, k - 1]) * e[:, k]
    beta = np.ones((n, 3, 3))
    for k in (1, 0):
        beta[:, k] = np.einsum("nst,nt->ns", trans[:, k], e[:, k + 1] * beta[:, k + 1])
    likelihood = alpha[:, 2].sum(axis=1)
    gamma = alpha * beta / likelihood[:, None, None]
    xi = np.zeros((n, 2, 3, 3))
    for k in (0, 1):
        xi[:, k] = (alpha[:, k][:, :, None] * trans[:, k] * (e[:, k + 1] * beta[:, k + 1])[:, None, :]
                    / likelihood[:, None, None])
    return gamma, xi, np.log(likelihood)


def fit_lta(triples: Sequence[TripleData], lca: Mapping[int, TripleFit], settings: FamilyFitSettings) -> LtaFit:
    """Baum-Welch over every fit-split triple sequence in time order."""

    usable = [t for t in triples if t.index in lca]
    seq = _lta_sequences(usable)
    T = len(usable)
    start = np.zeros((T, 3))
    emission = np.zeros((T, 3, 3, 3))  # (triple, item, state, category)
    for t, triple in enumerate(usable):
        prevalence, theta = _lca_tables(lca[triple.index])
        start[t] = prevalence
        emission[t] = np.transpose(theta, (1, 0, 2))
    emission = np.clip(emission, 1e-4, 1.0)
    emission /= emission.sum(axis=3, keepdims=True)
    transitions = np.stack([0.9 * np.eye(3) + 0.1 / 3.0] * 2)
    smoothing = settings.lta_smoothing
    previous = -math.inf
    loglik = -math.inf
    iteration = 0
    pair_counts = np.zeros((2, 3, 3))
    for iteration in range(1, settings.lta_iterations + 1):
        gamma, xi, log_like = _lta_forward_backward(start, emission, transitions, seq)
        loglik = float(log_like.sum())
        start = np.zeros((T, 3)) + smoothing
        np.add.at(start, seq["triple"], gamma[:, 0])
        start /= start.sum(axis=1, keepdims=True)
        pair_counts = np.zeros((2, 3, 3))
        for k in (0, 1):
            for g in (GAP_SAME_SESSION, GAP_LATER):
                rows = seq["gap"][:, k] == g
                pair_counts[g] += xi[rows, k].sum(axis=0)
        transitions = (pair_counts + smoothing) / (pair_counts + smoothing).sum(axis=2, keepdims=True)
        counts = np.zeros((T, 3, 3, 3)) + smoothing
        for k in range(3):
            np.add.at(counts, (seq["triple"], seq["item"][:, k], slice(None), seq["cat"][:, k]), gamma[:, k])
        emission = counts / counts.sum(axis=3, keepdims=True)
        if abs(loglik - previous) < 1e-8 * max(abs(loglik), 1.0):
            break
        previous = loglik
    return LtaFit(
        start={triple.index: start[t] for t, triple in enumerate(usable)},
        emission={triple.index: emission[t] for t, triple in enumerate(usable)},
        subject_of={triple.index: triple.subject_id for triple in usable},
        transitions=transitions,
        transition_counts=pair_counts,
        sequences=int(seq["triple"].shape[0]),
        loglik=loglik,
        iterations=iteration,
    )


def predict_lta(fit: LtaFit, triple: TripleData) -> np.ndarray:
    """Leave-one-out predictions in time order (forward over each completion)."""

    start, emission = fit.start[triple.index], fit.emission[triple.index]
    order, gaps = triple.time_order()
    categories = triple.categories()
    n = triple.n
    trans = fit.transitions[gaps]  # (n, 2, 3, 3)
    out = np.zeros((n, 3, 4))
    for i in range(3):
        joint = np.zeros((n, 3))
        for c in range(3):
            cats = categories.copy()
            cats[:, i] = c
            ordered = np.take_along_axis(cats, order, axis=1)
            e = np.stack([emission[order[:, k], :, ordered[:, k]] for k in range(3)], axis=1)  # (n, 3, 3)
            alpha = start[None, :] * e[:, 0]
            for k in (1, 2):
                alpha = np.einsum("ns,nst->nt", alpha, trans[:, k - 1]) * e[:, k]
            joint[:, c] = alpha.sum(axis=1)
        out[:, i, :] = _three_to_four(joint / joint.sum(axis=1, keepdims=True))
    return out


# -- validation -------------------------------------------------------------------------------------


def _auc(scores: np.ndarray, labels: np.ndarray) -> float:
    positives = labels.sum()
    negatives = labels.size - positives
    if positives == 0 or negatives == 0:
        return float("nan")
    order = np.argsort(scores, kind="mergesort")
    ranks = np.empty(scores.size)
    sorted_scores = scores[order]
    # average ranks for ties
    i = 0
    rank_values = np.arange(1, scores.size + 1, dtype=float)
    while i < scores.size:
        j = i
        while j + 1 < scores.size and sorted_scores[j + 1] == sorted_scores[i]:
            j += 1
        rank_values[i:j + 1] = (i + j + 2) / 2.0
        i = j + 1
    ranks[order] = rank_values
    return float((ranks[labels == 1].sum() - positives * (positives + 1) / 2.0) / (positives * negatives))


def _ece(predicted: np.ndarray, outcome: np.ndarray, bins: int = 10) -> float:
    if predicted.size == 0:
        return float("nan")
    edges = np.linspace(0.0, 1.0, bins + 1)
    which = np.clip(np.digitize(predicted, edges[1:-1]), 0, bins - 1)
    ece = 0.0
    for b in range(bins):
        mask = which == b
        if mask.any():
            ece += mask.sum() / predicted.size * abs(predicted[mask].mean() - outcome[mask].mean())
    return float(ece)


@dataclass
class Predictions:
    """Stacked held-out predictions of one family: (N, 4) role forecasts, realized roles, users."""

    forecast: list[np.ndarray] = field(default_factory=list)
    realized: list[np.ndarray] = field(default_factory=list)
    users: list[np.ndarray] = field(default_factory=list)

    def add(self, forecast: np.ndarray, roles: np.ndarray, users: np.ndarray) -> None:
        self.forecast.append(forecast.reshape(-1, 4))
        self.realized.append(roles.reshape(-1))
        self.users.append(np.repeat(users, 3))

    def stacked(self) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        if not self.forecast:
            return np.zeros((0, 4)), np.zeros(0, dtype=np.int64), np.zeros(0, dtype=np.int64)
        return np.concatenate(self.forecast), np.concatenate(self.realized), np.concatenate(self.users)


def score_predictions(forecast: np.ndarray, realized: np.ndarray, users: np.ndarray, *,
                      baseline_three: np.ndarray | None, rng: np.random.Generator, draws: int) -> dict[str, Any]:
    forecast = np.clip(forecast, 1e-9, 1.0)
    forecast = forecast / forecast.sum(axis=1, keepdims=True)
    n = realized.size
    rows = np.arange(n)
    four = -np.log(forecast[rows, realized])
    three_p = np.stack([forecast[:, 0], forecast[:, 1], forecast[:, 2] + forecast[:, 3]], axis=1)
    category = np.minimum(realized, 2)
    three = -np.log(three_p[rows, category])
    one_hot = np.eye(3)[category]
    ece = _ece(three_p.ravel(), one_hot.ravel())
    auc = _auc(forecast[:, 0], (realized == 0).astype(int))
    wrong = realized != 0
    designated_share = forecast[wrong, 1] / np.clip(1.0 - forecast[wrong, 0], 1e-9, None)
    chose_designated = (realized[wrong] == 1).astype(float)
    distractor_ll = -np.log(forecast[wrong, realized[wrong]] / np.clip(1.0 - forecast[wrong, 0], 1e-9, None))
    unique, inverse = np.unique(users, return_inverse=True)
    sums = np.bincount(inverse, weights=three, minlength=unique.size)
    sums4 = np.bincount(inverse, weights=four, minlength=unique.size)
    counts = np.bincount(inverse, minlength=unique.size).astype(float)
    gain_sums = None
    if baseline_three is not None:
        gain_sums = np.bincount(inverse, weights=baseline_three - three, minlength=unique.size)
    boots3, boots4, boots_gain = [], [], []
    for _ in range(draws):
        pick = rng.integers(0, unique.size, unique.size)
        boots3.append(sums[pick].sum() / counts[pick].sum())
        boots4.append(sums4[pick].sum() / counts[pick].sum())
        if gain_sums is not None:
            boots_gain.append(gain_sums[pick].sum() / counts[pick].sum())

    def ci(values: list[float]) -> list[float] | None:
        if not values:
            return None
        return [round(float(np.quantile(values, 0.025)), 5), round(float(np.quantile(values, 0.975)), 5)]

    out: dict[str, Any] = {
        "predictions": int(n),
        "students": int(unique.size),
        "log_loss_three": round(float(three.mean()), 5),
        "log_loss_three_ci95": ci(boots3),
        "log_loss_four": round(float(four.mean()), 5),
        "log_loss_four_ci95": ci(boots4),
        "ece_three": round(ece, 5),
        "auc_correct": round(auc, 5),
        "distractor": {
            "wrong_answers": int(wrong.sum()),
            "mean_predicted_designated_share": round(float(designated_share.mean()), 5),
            "observed_designated_share": round(float(chose_designated.mean()), 5),
            "ece_designated_share": round(_ece(designated_share, chose_designated), 5),
            "log_loss_choice_given_wrong": round(float(distractor_ll.mean()), 5),
        },
    }
    if baseline_three is not None:
        gain = float((baseline_three - three).mean())
        out["nll_gain_vs_marginal"] = round(gain, 5)
        out["nll_gain_ci95"] = ci(boots_gain)
        out["adequate"] = bool(
            auc >= ADEQUACY_MIN_AUC and gain >= ADEQUACY_MIN_NLL_GAIN and ece <= ADEQUACY_MAX_ECE
        )
    return out


# -- the container ------------------------------------------------------------------------------------


@dataclass
class FamilyFits:
    """Every family fitted to the fit split, with the held-out validation."""

    lca: ResponseFit
    cdm: dict[int, CdmSubjectFit]
    nrm: dict[int, NrmTripleFit]
    lta: LtaFit
    validation: dict[str, Any]
    settings: FamilyFitSettings
    source: dict[str, Any]
    version: str = FAMILY_FIT_VERSION

    def as_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "source": self.source,
            "settings": self.settings.as_dict(),
            "lca": self.lca.as_dict(),
            "cdm": {str(k): v.as_dict() for k, v in sorted(self.cdm.items())},
            "nrm": {str(k): v.as_dict() for k, v in sorted(self.nrm.items())},
            "lta": self.lta.as_dict(),
            "validation": self.validation,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "FamilyFits":
        settings_payload = dict(payload.get("settings") or {})
        return cls(
            lca=ResponseFit.from_dict(payload["lca"]),
            cdm={int(k): CdmSubjectFit.from_dict(v) for k, v in payload["cdm"].items()},
            nrm={int(k): NrmTripleFit.from_dict(v) for k, v in payload["nrm"].items()},
            lta=LtaFit.from_dict(payload["lta"]),
            validation=dict(payload.get("validation") or {}),
            settings=FamilyFitSettings(**{k: v for k, v in settings_payload.items()
                                          if k in FamilyFitSettings.__dataclass_fields__}),
            source=dict(payload.get("source") or {}),
            version=str(payload.get("version") or FAMILY_FIT_VERSION),
        )


def fit_families(
    triples: Sequence[TripleData],
    subjects: Sequence[SubjectData],
    settings: FamilyFitSettings,
    *,
    source: Mapping[str, Any],
    progress: Any = None,
) -> FamilyFits:
    """Fit every family on the fit split and score all of them on the held-out split."""

    say = progress or (lambda message: None)
    fit_split = [t.split(held_out=False) for t in triples]
    held_out = [t.split(held_out=True) for t in triples]
    say(f"lca refit on {sum(t.n for t in fit_split)} fit sequences")
    lca_triples = fit_lca(fit_split, settings)
    lca_by_index: dict[int, TripleFit] = {}
    by_key = {(t.subject_id, t.questions): t for t in fit_split}
    for fit in lca_triples:
        lca_by_index[by_key[(fit.subject_id, fit.questions)].index] = fit
    lca = lca_response_fit(lca_triples, seed=settings.seed, source={**dict(source), "split": "fit"})
    say(f"cdm on {len(subjects)} subjects")
    cdm = {s.subject_id: fit_cdm_subject(s, settings) for s in subjects if s.users.shape[0] >= 50}
    say(f"nrm on {len(fit_split)} triples")
    payloads = [(t, settings) for t in fit_split if t.n >= 30]
    if settings.workers > 1:
        with ProcessPoolExecutor(max_workers=settings.workers) as pool:
            nrm_list = list(pool.map(fit_nrm_triple, payloads, chunksize=4))
    else:
        nrm_list = [fit_nrm_triple(p) for p in payloads]
    nrm = {f.triple_index: f for f in nrm_list}
    say("lta (learning family)")
    lta = fit_lta(fit_split, lca_by_index, settings)
    say("held-out validation")
    validation = validate_families(held_out, fit_split, lca_by_index, cdm, subjects, nrm, lta, settings)
    return FamilyFits(
        lca=lca, cdm=cdm, nrm=nrm, lta=lta, validation=validation, settings=settings,
        source={**dict(source), "fit_sequences": int(sum(t.n for t in fit_split)),
                "held_out_sequences": int(sum(t.n for t in held_out))},
    )


def validate_families(
    held_out: Sequence[TripleData],
    fit_split: Sequence[TripleData],
    lca: Mapping[int, TripleFit],
    cdm: Mapping[int, CdmSubjectFit],
    subjects: Sequence[SubjectData],
    nrm: Mapping[int, NrmTripleFit],
    lta: LtaFit,
    settings: FamilyFitSettings,
) -> dict[str, Any]:
    """Score every family on the same held-out predictions (triples every family fitted)."""

    marginal = fit_marginal(fit_split)
    position_of: dict[int, tuple[int, int]] = {}
    for subject in subjects:
        for position, index in enumerate(subject.triple_indices):
            position_of[index] = (subject.subject_id, position)
    families = ("marginal",) + FAMILIES
    preds = {name: Predictions() for name in families}
    common = 0
    for triple in held_out:
        index = triple.index
        located = position_of.get(index)
        if (triple.n == 0 or index not in lca or index not in nrm or index not in lta.start
                or located is None or located[0] not in cdm):
            continue
        common += 1
        roles = triple.role_options()
        preds["marginal"].add(np.repeat(marginal[index][None, :, :], triple.n, axis=0), roles, triple.users)
        preds["lca"].add(predict_lca(lca[index], roles), roles, triple.users)
        preds["cdm"].add(predict_cdm(cdm[located[0]], located[1], roles), roles, triple.users)
        preds["nrm"].add(predict_nrm(nrm[index], roles, settings.nrm_nodes), roles, triple.users)
        preds["lta"].add(predict_lta(lta, triple), roles, triple.users)
    rng = np.random.default_rng(settings.seed)
    forecast, realized, users = preds["marginal"].stacked()
    forecast = np.clip(forecast, 1e-9, 1.0)
    category = np.minimum(realized, 2)
    three_p = np.stack([forecast[:, 0], forecast[:, 1], forecast[:, 2] + forecast[:, 3]], axis=1)
    baseline_three = -np.log(three_p[np.arange(realized.size), category])
    out: dict[str, Any] = {"triples": common, "families": {}}
    for name in families:
        f, r, u = preds[name].stacked()
        out["families"][name] = score_predictions(
            f, r, u, baseline_three=None if name == "marginal" else baseline_three,
            rng=np.random.default_rng(rng.integers(1 << 32)), draws=settings.bootstrap,
        )
    return out


__all__ = [
    "FAMILIES",
    "CdmSubjectFit",
    "FamilyFitSettings",
    "FamilyFits",
    "LtaFit",
    "NrmTripleFit",
    "cdm_profiles",
    "fit_cdm_subject",
    "fit_families",
    "fit_lca",
    "fit_lta",
    "fit_nrm_triple",
    "gauss_hermite_grid",
    "nrm_logits",
    "predict_cdm",
    "predict_lca",
    "predict_lta",
    "predict_nrm",
    "validate_families",
]

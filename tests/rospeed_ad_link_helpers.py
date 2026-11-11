"""What other test files use from ``tests/test_rospeed_ad_link.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from dataclasses import replace

import numpy as np

from learnloop.adaptive_difficulty import model as ADM
from learnloop.adaptive_difficulty import priors as ADP
from learnloop.router_objective import memory as M
from learnloop.router_objective import value as V
from learnloop.router_objective.memory import logit, perform, sigmoid
from learnloop.scheduling.fsrs import FSRS6_DEFAULT_WEIGHTS


LINK = V.AdLink(lapse=float(ADP.LAPSE), spread=float(ADP.A * ADP.TAU0), nodes=tuple(float(x) for x in ADM.X32),
                weights=tuple(float(w) for w in ADM.W32))


# -- the code at 516db1d862 (value.py), verbatim but for names ----------------------------------------------------


def _old_p(self, eta):
    e = np.asarray(eta, dtype=np.float64)[..., None] - self._shift
    return (1.0 - self.lapse) * (self._w * sigmoid(e)).sum(-1)


def _old_slope(self, eta):
    s = sigmoid(np.asarray(eta, dtype=np.float64)[..., None] - self._shift)
    return (1.0 - self.lapse) * (self._w * s * (1.0 - s)).sum(-1)


def _old_logit_and_slope(self, eta):
    with np.errstate(over="ignore"):
        s = sigmoid(np.asarray(eta, dtype=np.float64)[..., None] - self._shift)
    keep = 1.0 - self.lapse
    f = keep * (self._w * s).sum(-1)
    df = keep * (self._w * s * (1.0 - s)).sum(-1)
    tiny = ~(f > 1e-300)
    safe = np.where(tiny, 1.0, f)
    out = np.log(safe) - np.log1p(-safe)
    slope = df / safe + df / (1.0 - safe)
    if np.any(tiny):
        log_out, log_slope = self._logit_and_slope_logspace(np.asarray(eta, dtype=np.float64)[tiny])
        out = np.array(out, copy=True)
        slope = np.array(slope, copy=True)
        out[tiny], slope[tiny] = log_out, log_slope
    return out, slope


def _old_logit_p(self, eta):
    f = _old_p(self, eta)
    tiny = ~(f > 1e-300)
    safe = np.where(tiny, 1.0, f)
    out = np.log(safe) - np.log1p(-safe)
    if np.any(tiny):
        out = np.array(out, copy=True)
        out[tiny] = self._logit_and_slope_logspace(np.asarray(eta, dtype=np.float64)[tiny])[0]
    return out


def _old_performance(self, state, at, *, belief=False):
    when = np.asarray(at, dtype=np.float64)
    if when.ndim == 1:
        when = when[:, None]
    r = self.fsrs.retrievability(state.s, when - state.last)
    eta = state.bel if belief else state.eta
    if self.link is not None:
        eta = _old_logit_p(self.link, eta)
    return perform(self.theta.coef, eta, r, state.practiced)


def _old_graded(self, eta, bel, bel_var, stability, practiced, elapsed, coef, u, cells=None):
    if self.link is not None:
        return _old_graded_linked(self, eta, bel, bel_var, stability, practiced, elapsed, coef, u)
    if not self.consistent:
        good = u < sigmoid(eta)
        p_bel = sigmoid(bel)
        var = 1.0 / (1.0 / bel_var + p_bel * (1 - p_bel))
        return good, bel + var * (good.astype(np.float64) - p_bel), var
    a0, a_eta, a_r = coef[:, 0], coef[:, 1], coef[:, 2]
    lr = logit(self.fsrs.retrievability(stability, elapsed))
    p_true = np.where(practiced, sigmoid(a0 + a_eta * eta + a_r * (lr - eta)), sigmoid(eta))
    p_bel = np.where(practiced, sigmoid(a0 + a_eta * bel + a_r * (lr - bel)), sigmoid(bel))
    slope = np.where(practiced, a_eta - a_r, 1.0)
    good = u < p_true
    var = 1.0 / (1.0 / bel_var + slope * slope * p_bel * (1 - p_bel))
    return good, bel + var * slope * (good.astype(np.float64) - p_bel), var


def _old_graded_linked(self, eta, bel, bel_var, stability, practiced, elapsed, coef, u):
    link = self.link
    f_true, f_bel = _old_p(link, eta), _old_p(link, bel)
    eb, deb = _old_logit_and_slope(link, bel)
    if self.consistent:
        e, _de = _old_logit_and_slope(link, eta)
        a0, a_eta, a_r = coef[:, 0], coef[:, 1], coef[:, 2]
        lr = logit(self.fsrs.retrievability(stability, elapsed))
        p_true = np.where(practiced, sigmoid(a0 + a_eta * e + a_r * (lr - e)), f_true)
        p_bel = np.where(practiced, sigmoid(a0 + a_eta * eb + a_r * (lr - eb)), f_bel)
        slope = np.where(practiced, (a_eta - a_r) * deb, deb)
    else:
        p_true, p_bel, slope = f_true, f_bel, deb
    good = u < p_true
    var = 1.0 / (1.0 / bel_var + slope * slope * p_bel * (1 - p_bel))
    return good, bel + var * slope * (good.astype(np.float64) - p_bel), var


def _old_observe(self, state, lo, u, mask, observed=None):
    if self.link is not None:
        link = self.link
        _eb, deb = _old_logit_and_slope(link, state.bel[:, lo])
        good = (u < _old_p(link, state.eta[:, lo]) if observed is None else np.asarray(observed, dtype=bool))
        p_bel = _old_p(link, state.bel[:, lo])
        var = 1.0 / (1.0 / state.bel_var[:, lo] + deb * deb * p_bel * (1 - p_bel))
        bel = state.bel[:, lo] + var * deb * (good.astype(np.float64) - p_bel)
        state.bel[:, lo] = np.where(mask, bel, state.bel[:, lo])
        state.bel_var[:, lo] = np.where(mask, var, state.bel_var[:, lo])
        return good
    good = u < sigmoid(state.eta[:, lo]) if observed is None else np.asarray(observed, dtype=bool)
    p_bel = sigmoid(state.bel[:, lo])
    var = 1.0 / (1.0 / state.bel_var[:, lo] + p_bel * (1 - p_bel))
    bel = state.bel[:, lo] + var * (good.astype(np.float64) - p_bel)
    state.bel[:, lo] = np.where(mask, bel, state.bel[:, lo])
    state.bel_var[:, lo] = np.where(mask, var, state.bel_var[:, lo])
    return good


def _landing_code(monkeypatch) -> None:
    """Put the landing's link and its readers back (``AdLink``'s four methods, the model's four)."""

    for name, old in (("p", _old_p), ("slope", _old_slope), ("logit_and_slope", _old_logit_and_slope),
                      ("logit_p", _old_logit_p)):
        monkeypatch.setattr(V.AdLink, name, old)
    for name, old in (("performance", _old_performance), ("_graded", _old_graded),
                      ("_graded_linked", _old_graded_linked), ("_observe", _old_observe)):
        monkeypatch.setattr(V._Model, name, old)


def _inputs(n: int, *, items: int = 3, dated: tuple = (), seed: int = 0, link: V.AdLink | None = LINK,
            eta_shift: float = 0.0) -> V.Inputs:
    rng = np.random.default_rng(seed)
    topics = tuple(V.Topic(lo=f"lo{i}", eta_mean=float(rng.normal(0, 1)) + eta_shift, eta_var=0.5,
                           practiced=bool(i % 3), difficulty=float(rng.uniform(2, 8)),
                           stability=float(rng.uniform(1, 20)) if i % 3 else 0.0,
                           elapsed_days=float(rng.uniform(0, 10)) if i % 3 else 0.0, undated_density=1 / 90,
                           reading_count=float(i % 2),
                           eta_latent=(float(rng.normal(0, 1)) + eta_shift, 0.4) if i % 4 == 0 else None)
                   for i in range(n))
    return V.Inputs(topics=topics, dated=dated, session_minutes=5.0, price=V.Price(kappa0=0.0003, remembered=30.0),
                    tail_block_minutes=10.0, tail_block_items=items, horizon_days=60.0,
                    fsrs_weights=tuple(FSRS6_DEFAULT_WEIGHTS), return_gaps_days=(1.0, 2.0, 1.0),
                    return_slope=(0.1, 0.04), combiner=M.monotone_prior(), ad_link=link)


def _actions(n: int) -> list[V.Action]:
    lo = [f"lo{i}" for i in range(n)]
    review = V.Action(ref="a", kind=V.REVIEW, item_los=tuple(lo[1:4]), minutes=10.0, minutes_log_sd=0.3)
    reading = V.Action(ref="d", kind=V.READING, item_los=(lo[min(2, n - 1)],), minutes=12.0)
    return [V.Action(ref="stop_for_today", kind=V.STOP), review,
            V.Action(ref="b", kind=V.NEW_PRACTICE, item_los=(lo[0],), minutes=8.0, accept=(3.0, 2.0)),
            V.Action(ref="c", kind=V.PROBE, item_los=(lo[-1],), minutes=4.0,
                     repair=V.Action(ref="c:repair", kind=V.REPAIR, item_los=(lo[-1],), minutes=4.0)),
            reading, V.Action(ref="e", kind=V.LESSON, item_los=(lo[min(3, n - 1)],), minutes=6.0, mass=2.0),
            V.Action(ref="f", kind=V.SEQUENCE, steps=(replace(review, ref="f1"), replace(reading, ref="f2")),
                     item_los=(*review.item_los, *reading.item_los), minutes=22.0)]


#: The batch's rollout options, each with the held link on (``held_ad_link``, its kill switch; Codex review F1): the
#: landing code put back ignores it, so each test compares the held link with the landing's quadratures.
OPTIONS = {"every_switch_on": dict(merged_sessions=True, consistent_review_draw=True, held_ad_link=True),
           "per_block_loop_ad_draw": dict(merged_sessions=False, consistent_review_draw=False, held_ad_link=True),
           "merged_ad_draw": dict(merged_sessions=True, consistent_review_draw=False, held_ad_link=True)}


def _rows(evaluation: V.Evaluation) -> list[tuple]:
    rows = [*evaluation.valued, *((evaluation.reference,) if evaluation.reference is not None else ())]
    return [(row.ref, np.asarray(row.q_draws, dtype=np.float64).tobytes(),
             {key: float(value).hex() for key, value in row.terms.items()}, repr(row.extra)) for row in rows]

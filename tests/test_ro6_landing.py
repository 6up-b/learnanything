"""Router objective RO6's landing onto main: the orchestrator's rulings, each reproduced by a test (Codex's final
verify, job 20261105-152054-h2C3A5, for R1-R3; each fails on the source before its fix).

* **R1** (F1 reopened): every term of a window's realized return whose measurement can be missing (an exam result
  not known as of the window's closure, a use with no check support, a forced draw with no return) is carried as
  missing through calibration, bounded by its structural range, and ``ŵ`` reads the slope and rank at the fill least
  favourable to the residual (Manski's worst case): selectively missing outcomes never move ``ŵ`` above zero, and
  with no missing term the estimate is the unbounded one exactly;
* **R2** (F8): the objective's definition is hashed into each trace and is part of the generator key; a transition
  whose two decisions carry different objective hashes is censored ``objective_changed``;
* **R3** (F9): the carried valuation never runs on the learner's serving path: the no-model branch answers within
  its first pass's time, and the transition into it is censored ``cutoff_unmatched``;
* **R4**: a stop-coin draw that the waiting-follow-up rule superseded after the draw (the ledger logs the forced block
  deterministic; the coin's row and the trace keep the drawn arm and the coin's served candidate with its exact
  probability, as RO5's landing records) is used intent-to-treat: its contrast is by the assignment drawn, never by
  the action served.

Fakes only; no model request.
"""

from __future__ import annotations

import math
import random

import pytest

from learnloop.router_objective import checks as C
from learnloop.router_objective import learned_tail as LT
from learnloop.router_objective import scores as S
from learnloop.router_objective import stop_coin as SC
from learnloop.router_objective import tail_data as TD
from learnloop.router_objective import tail_serve as TS

from tests.test_ro6_codex_review import CFG, FAR, STOP, _logged, _quiet, _row, _trace, utc  # noqa: F401

RATE = 0.05


def _superseded(decision_id: str, created: str, arm: str, served: str, *, chosen: str | None = None) -> TD.Logged:
    """A forced draw whose block the waiting-follow-up rule replaced after the draw. The trace is frozen before the
    rule runs, so it carries the coin's arm and served candidate; ``chosen`` stands in for a record that named the
    action the learner was actually served (the follow-up block) instead."""

    coin = {"arm": arm, "rate": RATE, "served": served, "served_propensity": 0.5,
            "superseded_by": "forced:followup"}
    return _logged(_row(decision_id, created, closes="2026-10-15T10:00:00Z"),
                   _trace(q={STOP: 0.0, "a": 1.0}, chosen=chosen or served, residual={STOP: 0.0, "a": 0.5}, coin=coin))


def _contrasts(monkeypatch, rows: list[TD.Logged], returns: dict[str, float]):
    monkeypatch.setattr(TD, "_with_traces", lambda _connection, found: [dict(row.row) for row in found])
    monkeypatch.setattr(TD.S, "observed_returns",
                        lambda *_a, **_k: {key: (value, None) for key, value in returns.items()})
    return TD.contrasts(None, CFG, rows, at=FAR)


def test_r4_a_coin_draw_superseded_by_a_waiting_follow_up_is_used_intent_to_treat(monkeypatch):
    rows = [_superseded("d1", "2026-10-01T10:00:00Z", SC.OFFER_STOP, STOP),
            _superseded("d2", "2026-10-01T11:00:00Z", SC.PRESENT_NEXT, "a")]
    found, record = _contrasts(monkeypatch, rows, {"d1": 2.0, "d2": 3.0})
    by_id = {row.decision_id: row for row in found}
    assert record["status"] == "identified" and record["assigned"] == {SC.OFFER_STOP: 1, SC.PRESENT_NEXT: 1}
    # By the assignment drawn: offer stop +Ĝ/p, present next −Ĝ/p, each forced with P(forced) = 2p.
    assert by_id["d1"].realized == pytest.approx(2.0 / RATE) and by_id["d1"].forced
    assert by_id["d2"].realized == pytest.approx(-3.0 / RATE) and by_id["d2"].forced
    assert by_id["d1"].forced_probability == pytest.approx(2 * RATE)
    # Never by the action served: a record naming the follow-up block that was served gives the same contrasts.
    served = [_superseded("d1", "2026-10-01T10:00:00Z", SC.OFFER_STOP, STOP, chosen="a"),
              _superseded("d2", "2026-10-01T11:00:00Z", SC.PRESENT_NEXT, "a", chosen=STOP)]
    again, _record = _contrasts(monkeypatch, served, {"d1": 2.0, "d2": 3.0})
    assert [(row.decision_id, row.realized, row.tail, row.residual) for row in again] == \
        [(row.decision_id, row.realized, row.tail, row.residual) for row in found]


# -- R1: missing terms carried as missing, bounded, and ŵ at the least favourable fill ---------------------------

AT = "2026-11-01T00:00:00Z"
DAY = "2026-10-02"


def _sigmoid(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))


def _selective(monkeypatch, n: int = 8000, *, seed: int = 11, rate: float = 0.05, censor: float = 0.6,
               mode: str = "dated", planted: float | None = None) -> tuple[list, dict]:
    """Codex's final-verify reproduction (job 20261105-152054-h2C3A5, F1) through the real path
    ``scores.observed_returns(complete=True) → tail_data.contrasts → learned_tail.residual_weight``, with synthetic
    read adapters: a balanced coin at ``rate``, the residual's predicted contrast ``x``, zero costs and baselines,
    and each window's one term ``Y``: identical potential outcomes ``sigmoid(x)`` in both arms (``planted``: the
    control, ``Y = 0.5 ± planted·x/2`` by arm, complete, so the true contrast is ``planted·x``). With probability
    ``censor`` the term goes missing for negative-``x`` offer-stop draws and positive-``x`` present-next draws:
    ``mode`` ``dated`` (an exam result not known as of the window's closure) or ``unsupported`` (the window's undated
    use has no check support, ``r = 0``)."""

    rng = random.Random(seed)
    rows, traces, exams, support, resolved = [], {}, {}, {}, {}
    for i in range(n):
        x = rng.gauss(0.0, 1.0)
        u = rng.random()
        arm = SC.OFFER_STOP if u < rate else (SC.PRESENT_NEXT if u < 2 * rate else SC.POLICY)
        lost = (arm == SC.OFFER_STOP and x < 0) or (arm == SC.PRESENT_NEXT and x > 0)
        missing = lost and rng.random() < censor
        tail = rng.gauss(0.0, 1.0)
        if planted is None:
            y = _sigmoid(x)
        else:
            sign = 1.0 if arm == SC.OFFER_STOP else (-1.0 if arm == SC.PRESENT_NEXT else 0.0)
            y = min(max(0.5 + sign * planted * x / 2.0, 0.0), 1.0)
        decision_id, lo = f"c{i:05d}", f"lo_{i:05d}"
        rows.append(_logged(_row(decision_id, "2026-10-01T10:00:00Z", closes="2026-10-02T10:00:00Z"),
                            _trace(q={STOP: tail, "a": 0.0}, residual={STOP: x, "a": 0.0}, chosen="a",
                                   coin={"arm": arm, "rate": rate})))
        if mode == "dated":
            uses = {"topics": [], "dated": [{"goal_id": "g", "lo": lo, "due_at": "2026-10-02T09:00:00Z",
                                             "omega": 1.0, "m0": 0.0}]}
            exams[lo] = None if missing else y
        else:
            uses = {"topics": [{"lo": lo, "c": 1.0, "m0": [0.0]}], "dated": []}
            if not missing:
                support[lo] = 1.0
                resolved[(DAY, lo)] = C.Resolved(assignment_id=f"a{i}", local_date=DAY, topic=lo, r=1.0,
                                                  status=C.COMPLETED, outcome=y)
        traces[decision_id] = {"evaluation": {"window_days": 1, "c0": 0.0, "uses": uses}}

    def context(_connection, *, at=None):
        return lambda closes_at: S.AsOf(closure=C.Closure.at(closes_at), resolved=resolved, rate=1.0,
                                        r_lookup=lambda day: dict(support) if day == DAY else {}, prices={})

    monkeypatch.setattr(S, "_context", context)
    monkeypatch.setattr(S, "window_cost", lambda *_a, **_k: 0.0)
    monkeypatch.setattr(S, "exam_result_known", lambda _c, _config, lo, _on, _at, _closure=None: exams.get(lo))
    monkeypatch.setattr(TD, "_with_traces",
                        lambda _connection, found: [{**dict(row.row), "trace": traces[row.decision_id]} for row in found])
    return TD.contrasts(None, CFG, rows, at=AT)


@pytest.mark.parametrize("mode", ["dated", "unsupported"])
def test_r1_selectively_missing_terms_never_move_w_hat(monkeypatch, mode):
    found, record = _selective(monkeypatch, mode=mode)
    weight = LT.residual_weight(found, prior_sd=1.0, at=AT)
    # Before the fix: the missing terms were read as zero (the complete return), status identified, and ŵ ≈ 0.2
    # from the observation pattern alone (Codex: 0.201, slope 0.201 ± 0.031).
    assert weight.w_hat == 0.0
    as_dict = weight.as_dict()
    assert as_dict["bound"] == LT.LEAST_FAVOURABLE and as_dict["missing"]["contrasts"] > 0
    # The unbounded estimate (the missing terms left out, the pre-fix reading) is shown beside the bound.
    assert as_dict["unbounded"]["w_hat"] > 0.1 and as_dict["slope_mean"] < as_dict["unbounded"]["slope_mean"]
    assert record["status"] == "identified" and record["missing"]["terms"] == as_dict["missing"]["terms"]
    window = record["missing"]["by_window"][0]
    assert window["missing"] == 1 and window["arm"] in (SC.OFFER_STOP, SC.PRESENT_NEXT)
    assert window["hi"] - window["lo"] == pytest.approx(1.0)  # performance in [0, 1] times the weight 1


def test_r1_complete_outcomes_recover_the_planted_slope_and_equal_the_unbounded_estimate(monkeypatch):
    found, record = _selective(monkeypatch, censor=0.0, planted=0.4)
    weight = LT.residual_weight(found, prior_sd=1.0, at=AT)
    assert abs(weight.slope_mean - 0.4) < 4 * weight.slope_sd and weight.w_hat > 0.25
    # No missing term: the estimate is the unbounded one exactly.
    as_dict = weight.as_dict()
    assert as_dict["bound"] == "none" and as_dict["missing"]["contrasts"] == 0
    assert (as_dict["unbounded"]["w_hat"], as_dict["unbounded"]["slope_mean"]) == (weight.w_hat, weight.slope_mean)
    # Identical arms, complete: no contrast (Codex's complete-outcome control, ŵ = 0 within noise).
    found, _record = _selective(monkeypatch, censor=0.0)
    null = LT.residual_weight(found, prior_sd=1.0, at=AT)
    assert null.w_hat < 0.15 and abs(null.slope_mean) < 3 * null.slope_sd + 1e-9

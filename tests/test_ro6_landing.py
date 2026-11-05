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

from tests.test_ro6_codex_review import (CFG, FAR, STOP, _logged, _quiet, _row, _trace, _value_actions,  # noqa: F401
                                         _value_inputs, utc)

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


def block_drawing_seed():
    """R8: a pinned decision seed (``fake_runtime(seed=…)``) whose draws serve a block at every boundary: the mix's
    first uniform past the floor and inside the first live component's share (the LLM policy with both models, staged
    with none), its second below every first option's share, and the stop coin's uniform on the ``policy`` arm. So a
    chooser test that needs two decisions gets them deterministically, never by retrying."""

    from learnloop.router.mixture import uniform

    for index in range(100_000):
        seed = f"ro6-landing-{index}"
        if (0.3 <= uniform(seed, "component") < 0.45 and uniform(seed, "candidate") < 0.02
                and uniform(seed, "stop_coin") >= 0.5):
            return lambda _key, _decision_id, seed=seed: seed
    raise AssertionError("no seed found")


def _sigmoid(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))


def _selective(monkeypatch, n: int = 8000, *, seed: int = 11, rate: float = 0.05, censor: float = 0.6,
               mode: str = "dated", planted: float | None = None, beside: int = 0,
               lost_in_arm: str | None = None, completion: float = 1.0) -> tuple[list, dict]:
    """Codex's final-verify reproduction (job 20261105-152054-h2C3A5, F1) through the real path
    ``scores.observed_returns(complete=True) → tail_data.contrasts → learned_tail.residual_weight``, with synthetic
    read adapters: a balanced coin at ``rate``, the residual's predicted contrast ``x``, zero costs and baselines,
    and each window's one term ``Y``: identical potential outcomes ``sigmoid(x)`` in both arms (``planted``: the
    control, ``Y = 0.5 ± planted·x/2`` by arm, complete, so the true contrast is ``planted·x``). With probability
    ``censor`` the term goes missing for negative-``x`` offer-stop draws and positive-``x`` present-next draws:
    ``mode`` ``dated`` (an exam result not known as of the window's closure) or ``unsupported`` (the window's undated
    use had check support at the draw, frozen in the trace as the serve freezes it, and has none on its day,
    ``r = 0``: support lost after the draw). R7: ``beside`` undated uses per window whose topics had no check support
    at the draw (nor on the day); ``lost_in_arm``: the support of every window of that arm is lost after the draw.
    R10: ``mode`` ``skipped`` keeps every topic's support on its day and represents the same selective losses as
    drawn checks that were skipped (Codex's scoped verify, job 20261105-170936-WEjALK); ``completion``: the pooled
    completion rate the as-of reader carries (Codex: 1, and 7742/8000)."""

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
        elif mode == "skipped":
            uses = {"topics": [{"lo": lo, "c": 1.0, "m0": [0.0]}], "dated": []}
            support[lo] = 1.0
            resolved[(DAY, lo)] = C.Resolved(assignment_id=f"a{i}", local_date=DAY, topic=lo, r=1.0,
                                              status=C.SKIPPED if missing else C.COMPLETED,
                                              outcome=None if missing else y)
        else:
            others = [f"u_{i:05d}_{j}" for j in range(beside)]
            uses = {"topics": [{"lo": topic, "c": 1.0, "m0": [0.0]} for topic in (lo, *others)], "dated": []}
            if not missing and arm != lost_in_arm:
                support[lo] = 1.0
                resolved[(DAY, lo)] = C.Resolved(assignment_id=f"a{i}", local_date=DAY, topic=lo, r=1.0,
                                                  status=C.COMPLETED, outcome=y)
        traces[decision_id] = {"evaluation": {"window_days": 1, "c0": 0.0, "uses": uses}}
        if mode != "dated":
            # The support as of the draw, frozen by the serve (residual.measurable): this window's own topic only.
            traces[decision_id]["residual"] = {"measurable": {"support": {lo: 1.0}}}

    def context(_connection, *, at=None):
        return lambda closes_at: S.AsOf(closure=C.Closure.at(closes_at), resolved=resolved, rate=completion,
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


# -- R7: terms unsupported at the draw are outside the measurable target, not missing ------------------------------


def test_r7_a_planted_slope_on_supported_terms_is_recovered_beside_many_unsupported_at_the_draw(monkeypatch):
    found, record = _selective(monkeypatch, censor=0.0, planted=0.4, mode="unsupported", beside=30)
    weight = LT.residual_weight(found, prior_sd=1.0, at=AT)
    # Before the fix: the 30 unsupported uses of each forced window were bounded missing terms (width 30), the
    # least favourable fill sent the slope far below zero and ŵ was 0.
    assert abs(weight.slope_mean - 0.4) < 4 * weight.slope_sd and weight.w_hat > 0.25
    as_dict = weight.as_dict()
    assert as_dict["bound"] == "none" and as_dict["missing"]["terms"] == 0
    forced = record["assigned"][SC.OFFER_STOP] + record["assigned"][SC.PRESENT_NEXT]
    assert record["excluded"]["terms"] == 30 * forced and record["missing"]["terms"] == 0
    assert as_dict["excluded"]["terms"] == 30 * forced and "measurable part" in as_dict["target"]


def test_r7_codexs_reproductions_still_give_w_hat_zero(monkeypatch):
    # Support at the draw, lost afterwards selectively (and an exam not known at closure): still missing, bounded.
    for mode in ("dated", "unsupported"):
        found, record = _selective(monkeypatch, mode=mode, beside=5 if mode == "unsupported" else 0)
        weight = LT.residual_weight(found, prior_sd=1.0, at=AT)
        assert weight.w_hat == 0.0 and weight.as_dict()["bound"] == LT.LEAST_FAVOURABLE, mode


def test_r7_support_removed_after_the_draw_in_one_arm_only_stays_bounded(monkeypatch):
    found, record = _selective(monkeypatch, censor=0.0, mode="unsupported", beside=3, lost_in_arm=SC.OFFER_STOP)
    offers = record["assigned"][SC.OFFER_STOP]
    windows = [entry for entry in record["missing"]["by_window"] if entry["missing"]]
    assert len(windows) == offers and all(entry["arm"] == SC.OFFER_STOP and entry["missing"] == 1
                                          and entry["hi"] - entry["lo"] == pytest.approx(1.0) for entry in windows)
    assert all(entry["excluded"] == 3 for entry in record["missing"]["by_window"])  # beside, both arms alike
    weight = LT.residual_weight(found, prior_sd=1.0, at=AT)
    assert weight.as_dict()["bound"] == LT.LEAST_FAVOURABLE and weight.missing_terms == offers


def test_r7_the_rollouts_keep_each_unmeasured_topics_share_apart_on_the_same_paths():
    from learnloop.router_objective import value as V

    inputs, actions = _value_inputs(), _value_actions()
    plain = V.evaluate(inputs, actions, draws=16, seed="r7")
    los = [topic.lo for topic in inputs.topics]
    by_one = [V.evaluate(inputs, actions, draws=16, seed="r7", unmeasured={lo}) for lo in los]
    both = V.evaluate(inputs, actions, draws=16, seed="r7", unmeasured=set(los))
    none = V.evaluate(inputs, actions, draws=16, seed="r7", unmeasured=set())
    for i, row in enumerate(plain.valued):
        # Q̄ and the choice are unchanged; mvp-0.48's terms carry no new key.
        assert [one.valued[i].q for one in by_one] == [row.q] * len(los) and both.valued[i].q == row.q
        assert "unmeasured_reward" not in row.terms and none.valued[i].terms["unmeasured_reward"] == 0.0
        # By term: the topics' shares add up to the share of both, on the same paths.
        assert sum(one.valued[i].terms["unmeasured_reward"] for one in by_one) == pytest.approx(
            both.valued[i].terms["unmeasured_reward"], rel=1e-9, abs=1e-12)
    assert any(both.valued[i].terms["unmeasured_reward"] > 0 for i in range(len(plain.valued)))


def test_r7_a_served_decision_freezes_its_support_and_the_measurable_tail(tmp_path):
    from learnloop.algorithm_versions import ROUTER_LEARNED_TAIL_ALGORITHM_VERSION
    from learnloop.db.stores import router_objective as store

    from tests.router_mixture_helpers import mixture_env, run
    from tests.router_model_fakes import FakeLLM, fake_runtime
    from tests.test_ro4_objective_serving import policy_answer

    env = mixture_env(tmp_path, fake_runtime(llm=FakeLLM(answer=policy_answer)),
                      version=ROUTER_LEARNED_TAIL_ALGORITHM_VERSION)
    run(env, steps=4)
    with env.repository.connection() as connection:
        rows = [(row, store.trace(connection, row["decision_id"])["trace"]) for row in store.traces(connection)
                if row["decision_kind"] == "plan_block"]
        logged = {row.decision_id: row for row in TD.logged(connection, env.vault.config, at="2100-01-01T00:00:00Z")}
        for row, trace in rows:
            measurable = trace["residual"]["measurable"]
            assert measurable["support"] == pytest.approx(C.support_at(connection, row["created_at"])[0], abs=1e-6)
            assert all(entry["terms"]["unmeasured_reward"] is not None for entry in trace["candidates"].values())
            q = {ref: entry["terms"]["q"] - entry["terms"]["unmeasured_reward"]
                 for ref, entry in trace["candidates"].items()}
            assert logged[row["decision_id"]].q_measurable == pytest.approx(q)


# -- R10: every post-draw loss is a missing term; one classification -----------------------------------------------


@pytest.mark.parametrize("completion", [1.0, 7742 / 8000], ids=["no_pooled_rate", "pooled_rate"])
def test_r10_selectively_skipped_checks_never_move_w_hat(monkeypatch, completion):
    """Codex's scoped-verify reproduction: the seed-11 draws with support kept and the same selective losses as
    drawn checks that were skipped. Before the fix: missing 0, bound none, ŵ 0.201373 (0.208070 with the pooled
    completion rate 7742/8000)."""

    found, record = _selective(monkeypatch, mode="skipped", completion=completion)
    weight = LT.residual_weight(found, prior_sd=1.0, at=AT)
    assert weight.w_hat == 0.0
    assert weight.as_dict()["bound"] == LT.LEAST_FAVOURABLE and record["missing"]["terms"] > 0
    assert record["missing"]["by_reason"] == {C.SKIPPED: record["missing"]["terms"]}


def _loss_kinds() -> set[str]:
    """Every status the ledger gives a drawn check other than a labelled completion, read from ``checks`` itself:
    the noncompletion reasons and every ``excluded:*`` grade exclusion (with the held grade's)."""

    from learnloop.outcome_contract import GRADE_HELD_FOR_REVIEW

    kinds = {C.NO_SESSION, C.NO_PRACTICE_SLOT, C.DISPLACED, C.SKIPPED, C.NOT_ANSWERED, C.OPEN,
             f"{C.EXCLUDED_PREFIX}{GRADE_HELD_FOR_REVIEW}"}
    kinds |= {value for name, value in vars(C).items() if name.startswith("EXCLUDED_") and name != "EXCLUDED_PREFIX"}
    return kinds


def test_r10_the_ledger_gives_no_status_the_enumeration_misses():
    """The enumeration is the ledger's: every status ``Ledger.resolve`` writes and every reason ``exclusion``
    returns is a name the enumeration holds (a new loss kind fails here first)."""

    import ast
    import inspect

    tree = ast.parse(inspect.getsource(C))
    named: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name in ("resolve", "exclusion"):
            for inner in ast.walk(node):
                values = []
                if isinstance(inner, ast.keyword) and inner.arg == "status":
                    values = [inner.value]
                elif isinstance(inner, ast.Return) and node.name == "exclusion" and inner.value is not None:
                    values = [inner.value]
                for value in values:
                    named |= {sub.id for sub in ast.walk(value) if isinstance(sub, ast.Name) and sub.id.isupper()}
    known = {name for name, value in vars(C).items() if isinstance(value, str) and value in _loss_kinds()}
    assert named - {"COMPLETED", "EXCLUDED_PREFIX", "GRADE_HELD_FOR_REVIEW"} <= known, named - known


def test_r10_one_function_classifies_every_term_of_a_window():
    row ={"decision_id": "d", "created_at": "2026-10-01T10:00:00Z", "local_date": "2026-10-01"}

    def classify(status: str | None, *, r: float = 0.5, drawn: bool = True, support: float | None = 1.0,
                 outcome: float | None = 1.0):
        trace = {"evaluation": {"window_days": 1, "uses": {"topics": [{"lo": "L", "c": 1.0, "m0": [0.0]}]}}}
        resolved = ({} if status is None else
                    {(DAY, "L"): C.Resolved(assignment_id="a", local_date=DAY, topic="L", r=r, status=status,
                                            outcome=outcome)})
        (term,) = S.classify_window(None, row, trace, resolved=resolved, r_lookup=lambda _day: {"L": r},
                                    support=None if support is None else {"L": support},
                                    drawn=lambda _day: drawn)
        return term

    observed = classify(C.COMPLETED)
    assert (observed.kind, observed.outcome) == (S.OBSERVED, 1.0)
    for kind in sorted(_loss_kinds()):
        term = classify(kind, outcome=None)
        assert (term.kind, term.reason, term.drawn) == (S.MISSING, kind, True), kind
        assert term.bounds() == pytest.approx((0.0, 2.0))  # c·[0, 1]/r with r = 0.5
    unlabelled = classify(C.COMPLETED, outcome=None)
    assert (unlabelled.kind, unlabelled.reason) == (S.MISSING, f"{C.COMPLETED}:no_label")
    assert classify(None).kind == S.DESIGN_ZERO  # the day's draw took another topic: the design's zero
    no_draw = classify(None, drawn=False)
    assert (no_draw.kind, no_draw.reason) == (S.MISSING, S.RO6_NO_DRAW_DAY) and no_draw.bounds() == pytest.approx(
        (0.0, 2.0))
    lost = classify(None, r=0.0)
    assert (lost.kind, lost.reason) == (S.MISSING, S.RO6_NO_CHECK_SUPPORT) and lost.bounds() == (0.0, 1.0)
    assert classify(C.SKIPPED, support=0.0).kind == S.EXCLUDED_AT_DRAW  # R7 before anything after the draw
    dated = {"evaluation": {"window_days": 0, "uses": {"topics": [], "dated": [
        {"goal_id": "g", "lo": "L", "due_at": "2026-10-02T09:00:00Z", "omega": 2.0, "m0": 0.5}]}}}
    known, = S.classify_window(None, row, dated, resolved={}, r_lookup=lambda _d: {}, exam_result=lambda *_a: 0.8)
    unknown, = S.classify_window(None, row, dated, resolved={}, r_lookup=lambda _d: {}, exam_result=lambda *_a: None)
    assert (known.kind, unknown.kind, unknown.reason) == (S.OBSERVED, S.MISSING, S.RO6_DATED_MISSING)
    assert unknown.bounds() == pytest.approx((-1.0, 1.0))  # ω·([0, 1] − m⁰)


# -- R9: a trace does not grow with the log ------------------------------------------------------------------------


def _residual_with_windows(monkeypatch, windows: int) -> dict:
    """``tail_serve.residual`` with its reads replaced: ``windows`` forced windows each with one bounded missing
    term and two excluded, no fit, no features (only the calibration's size varies)."""

    from types import SimpleNamespace

    draws = [LT.CoinDraw(decision_id=f"w{i:05d}", decided_at="2026-10-01T10:00:00Z",
                         window_closes_at="2026-10-15T10:00:00Z", arm=SC.OFFER_STOP if i % 2 else SC.PRESENT_NEXT,
                         rate=0.05, value=0.5, reason="no_check_support:1", tail=0.1 * (i % 7), residual=0.01 * i,
                         lo=0.0, hi=1.0, missing=1, excluded=2) for i in range(windows)]

    class _Repository:
        def connection(self):
            from contextlib import nullcontext

            return nullcontext(None)

    monkeypatch.setattr(TS, "features", lambda *_a, **_k: ({}, {}))
    monkeypatch.setattr(TD, "logged", lambda *_a, **_k: [])
    monkeypatch.setattr(TD, "fits", lambda *_a, **_k: TD.Fits(by_generator={}, order=(), steps=TD.Steps((), {}, (), {}),
                                                            decisions=0))
    monkeypatch.setattr(TD, "contrasts", lambda *_a, **_k: LT.coin_contrasts(draws))
    now = "2026-11-01T10:00:00Z"
    return TS.residual(_Repository(), CFG, inputs=SimpleNamespace(cutoff=90.0), actions=(), now_iso=now,
                       generator_now="g", frozen={"at": now})


def test_r9_the_trace_keeps_a_summary_of_the_calibration_whatever_the_logs_length(monkeypatch):
    import json

    small, large = _residual_with_windows(monkeypatch, 10), _residual_with_windows(monkeypatch, 1000)
    assert small["status"] == large["status"] == "applied"
    # Before the fix: the per-window bounds were kept in the trace (residual.contrasts.censored.missing.by_window),
    # about 100 bytes a forced window, so the trace grew with the log.
    sizes = [len(json.dumps(record, sort_keys=True, default=str)) for record in (small, large)]
    assert sizes[1] - sizes[0] < 64, sizes
    summary = large["contrasts"]
    assert "by_window" not in json.dumps(summary)
    assert (summary["n"], summary["missing"]["windows"], summary["missing"]["terms"], summary["excluded"]) == (
        1000, 1000, 1000, {"windows": 1000, "terms": 2000})
    assert summary["at"] == "2026-11-01T10:00:00Z" and len(summary["inputs_hash"]) == 16
    weight = large["weight"]
    assert {"w_hat", "slope_mean", "rank", "p_rank", "bound", "unbounded", "missing", "excluded"} <= set(weight)


# -- R2: the objective's definition is part of the generator; a change censors objective_changed ----------------


def _objective_trace(decision_id: str, *, goals: dict, previous: dict | None = None) -> dict:
    width = len(LT.NAMES)
    trace = _trace(q={STOP: 0.0, "a": 0.0}, cutoff_days=6.0, previous=previous)
    trace["versions"] = {"horizon_days": 6.0}
    trace["inputs_sources"] = {"goals": goals}
    trace["residual"]["candidates"] = {ref: {"features": [0.0] * width, "v_residual": 0.0} for ref in (STOP, "a")}
    return trace


def test_r2_a_goal_added_between_two_decisions_censors_the_transition_objective_changed(monkeypatch, utc):
    """Codex's F8: two decisions one day apart, ``H = 6``, zero costs and undated density; between them a goal three
    days away with weight 10 and predicted performance 0.78. Under the earlier objective the carried cutoff's value
    is 0; with the later inputs it is 7.8, and before the fix the backup accepted 7.8 under one generator."""

    width = len(LT.NAMES)
    _quiet(monkeypatch, {"d1": "d2"})
    goal = {"g": {"dated": 10.0, "undated_density": 0.0, "per_lo": {}, "source": "contract",
                  "contract_version_id": None, "due_at": "2026-10-05T10:00:00Z", "days_to_date": 3.0, "scope": 1,
                  "los": ["lo_a"]}}
    first = _logged(_row("d1", "2026-10-01T10:00:00Z"), _objective_trace("d1", goals={}))
    carried = {"decision_id": "d1", "cutoff_days": repr(5.0), "status": "carried", "q_status": "valued",
               "q": {STOP: 7.8, "a": 7.8}, "features": {STOP: [0.0] * width, "a": [0.0] * width}}
    second = _logged(_row("d2", "2026-10-02T10:00:00Z"), _objective_trace("d2", goals=goal, previous=carried))
    steps = TD.transitions(None, CFG, [first, second], at=FAR)
    # Before the fix: one transition, next_v_tail 7.8, the two under one generator.
    assert steps.transitions == () and steps.censored == {TD.OBJECTIVE_CHANGED: 1, TD.NO_LATER_DECISION: 1}
    assert first.objective != second.objective and first.generator != second.generator
    assert [point["reason"] for point in steps.change_points] == [TD.OBJECTIVE_CHANGED]
    # The same goal on both sides: one objective, the backup reads the carried value.
    same = _logged(_row("d1", "2026-10-01T10:00:00Z"), _objective_trace("d1", goals=goal))
    kept = TD.transitions(None, CFG, [same, second], at=FAR)
    assert len(kept.transitions) == 1 and kept.transitions[0].next_v_tail == pytest.approx(7.8)
    # The hash ignores what moves with time alone (days to the date) and reads what defines the objective.
    later = {"g": {**goal["g"], "days_to_date": 2.0}}
    weights = {"g": {**goal["g"], "per_lo": {"lo_a": 3.0}}}
    assert TD.objective_hash(later, 6.0) == TD.objective_hash(goal, 6.0)
    assert TD.objective_hash(weights, 6.0) != TD.objective_hash(goal, 6.0)
    assert TD.objective_hash(goal, 7.0) != TD.objective_hash(goal, 6.0)


def test_r2_a_served_decision_logs_its_objective_under_the_generator_it_served(tmp_path):
    from learnloop.algorithm_versions import ROUTER_LEARNED_TAIL_ALGORITHM_VERSION
    from learnloop.db.stores import router_objective as store

    from tests.router_mixture_helpers import mixture_env, run
    from tests.router_model_fakes import FakeLLM, fake_runtime
    from tests.test_ro4_objective_serving import policy_answer

    env = mixture_env(tmp_path, fake_runtime(llm=FakeLLM(answer=policy_answer)),
                      version=ROUTER_LEARNED_TAIL_ALGORITHM_VERSION)
    run(env, steps=4)
    with env.repository.connection() as connection:
        traces = [store.trace(connection, row["decision_id"])["trace"] for row in store.traces(connection)
                  if row["decision_kind"] == "plan_block"]
    assert traces
    for trace in traces:
        residual = trace["residual"]
        assert residual["objective"]["hash"] == TD.trace_objective_hash(trace)
        assert residual["generator"] == TD.generator(trace, ROUTER_LEARNED_TAIL_ALGORITHM_VERSION)


# -- R3: the carried valuation never runs on the learner's serving path ----------------------------------------


def test_r3_the_no_model_branch_answers_within_the_first_pass_and_censors_the_carried_backup(tmp_path, monkeypatch):
    """Codex's F9 with an instrumented clock: 100 ms for each evaluation at the decision's own cutoff, 472 ms for one at
    a carried cutoff. Before the fix the no-model branch ran both before answering (572 ms); now its answer returns
    within the first pass's time, the carried valuation is not run on the serving path, and the transition into the
    decision is censored ``cutoff_unmatched``."""

    from learnloop.algorithm_versions import ROUTER_LEARNED_TAIL_ALGORITHM_VERSION
    from learnloop.daily_plan import objective_chooser as OC
    from learnloop.db.stores import router_objective as store

    from tests.router_mixture_helpers import mixture_env, run
    from tests.router_model_fakes import fake_runtime

    clock = {"ms": 0.0, "first_pass": 0.0}
    real = OC.V.evaluate

    def instrumented(*args, **kwargs):
        if kwargs.get("cutoff") is not None:
            clock["ms"] += 472.0
        else:
            clock["ms"] += 100.0
            clock["first_pass"] += 100.0
        return real(*args, **kwargs)

    monkeypatch.setattr(OC.V, "evaluate", instrumented)
    served: list[tuple[float, float]] = []
    real_run = OC.run_numeric

    def timed(*args, **kwargs):
        before, first = clock["ms"], clock["first_pass"]
        policy = real_run(*args, **kwargs)
        # (the serve's time on the instrumented clock, its evaluations at the decision's own cutoff alone)
        served.append((clock["ms"] - before, clock["first_pass"] - first))
        return policy

    monkeypatch.setattr(OC, "run_numeric", timed)
    # R8: the seed is pinned to one that draws a block at every boundary (two decisions at least, deterministically).
    env = mixture_env(tmp_path, fake_runtime(seed=block_drawing_seed()), version=ROUTER_LEARNED_TAIL_ALGORITHM_VERSION)
    run(env, steps=16)
    with env.repository.connection() as connection:
        traces = [store.trace(connection, row["decision_id"])["trace"] for row in store.traces(connection)
                  if row["decision_kind"] == "plan_block"]
    assert len(traces) >= 2 and all(trace["policies"]["numeric"]["status"] == "answered" for trace in traces)
    later = [trace["residual"]["previous"] for trace in traces[1:]]
    assert all(previous["status"] == TS.CARRIED for previous in later)
    # Before the fix: each decision after the first answered after its first pass plus 472 ms (Codex: 572 ms).
    assert len(served) == len(traces) and all(spent == first for spent, first in served), served
    assert all(previous["q_status"] == TS.NOT_ON_THE_SERVING_PATH and "q" not in previous for previous in later)
    with env.repository.connection() as connection:
        steps = TD.fits(connection, env.vault.config, at="2100-01-01T00:00:00Z").steps
    assert not any(step.detail.get("cutoff") == "previous_cutoff" for step in steps.transitions)
    assert steps.censored.get(TD.CUTOFF_UNMATCHED, 0) >= 1

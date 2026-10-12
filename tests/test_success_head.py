"""T8 success-head arms and the pre-registered analysis: synthetic, store-free."""
from dataclasses import replace
from datetime import datetime, timedelta, timezone
import json

import numpy as np
import pytest

from learnloop.field.evaluation import (
    ReplayArrays, _loss, cluster_t_interval, evaluate, paired_bootstrap,
)
from learnloop.field.predictors import is_calibrated_predictor
from learnloop.field.success_head import (
    EXPLICIT_ARMS, PREREGISTRATION, AttemptContent, ContentIndex, HeadPriors, LogisticHead,
    newton_map, preregistration_hash, success_head_arms,
)
from learnloop.field.success_head_analysis import make_t8_analysis, summary_lines
from learnloop.field.types import AttemptRow, ItemFeatures


def _rows_and_content(n=80, n_items=20, seed=0, strength=2.0, **feature_kwargs):
    rng = np.random.default_rng(seed)
    direction = rng.normal(size=32)
    direction /= np.linalg.norm(direction)
    vectors = {f"item{i}": rng.normal(size=32) + 2.0 for i in range(n_items)}
    rows, entries = [], {}
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    for k in range(n):
        item = f"item{rng.integers(n_items)}"
        lo = f"lo{int(item[4:]) % 3}"
        at = (start + timedelta(hours=9 * k)).isoformat().replace("+00:00", "Z")
        v = vectors[item]
        outcome = float(rng.random() < 1 / (1 + np.exp(-strength * float((v - 2.0) @ direction))))
        rows.append(AttemptRow(f"a{k:04}", ItemFeatures(item, lo, at, **feature_kwargs), outcome, 1.0))
        entries[(item, at)] = AttemptContent(
            stem=f"stem of {item}", stem_source="exact_snapshot", kcs=(lo,),
            vectors={"stem": tuple(v / np.linalg.norm(v))},
        )
    return rows, ContentIndex(entries, embedding_model="fake-embed", views=("stem",))


def _capture(rows, arms, **kwargs):
    captured = {}

    def keep(arrays):
        captured["arrays"] = arrays
        return {}

    report = evaluate(rows, arms=arms, bootstrap_samples=20, analyses={"keep": keep}, **kwargs)
    return report, captured["arrays"]


def test_newton_map_is_the_stationary_point_and_matches_a_direct_optimizer():
    from scipy.optimize import minimize

    rng = np.random.default_rng(3)
    X = rng.normal(size=(60, 5))
    y = rng.uniform(size=60)  # fractional rubric outcomes are cross-entropy targets
    s = rng.uniform(.2, 1, size=60)
    mean, precision = np.array([0, 1, 0, 0, -1.]), np.array([1, 4, 4, 4, 4.])
    w, hessian = newton_map(X, y, s, mean, precision, np.zeros(5))

    def objective(v):
        eta = X @ v
        return s @ (np.logaddexp(0, eta) - y * eta) + .5 * precision @ (v - mean) ** 2

    direct = minimize(objective, np.zeros(5), method="BFGS", options={"gtol": 1e-10}).x
    assert np.allclose(w, direct, atol=1e-5)
    p = 1 / (1 + np.exp(-X @ w))
    assert np.allclose(X.T @ (s * (p - y)) + precision * (w - mean), 0, atol=1e-8)
    assert np.all(np.linalg.eigvalsh(hessian) > 0)


def test_prediction_never_sees_the_current_or_a_later_outcome():
    rows, content = _rows_and_content()
    _, base = _capture(rows, success_head_arms(content))
    flipped = [replace(r, outcome=1 - r.outcome) if i >= 40 else r for i, r in enumerate(rows)]
    _, changed = _capture(flipped, success_head_arms(content))
    for name in ("tag_logistic", "emb_ridge", "success_head"):
        assert np.array_equal(base.predictions[name][:41], changed.predictions[name][:41])
        assert not np.array_equal(base.predictions[name][41:], changed.predictions[name][41:])


def test_future_content_entries_never_change_a_prediction():
    rows, content = _rows_and_content()
    past = rows[:30]
    keys = {(r.features.item_id, r.features.observed_at) for r in past}
    narrow = ContentIndex({k: v for k, v in content._entries.items() if k in keys},
                          embedding_model="fake-embed", views=("stem",))
    _, full = _capture(past, success_head_arms(content))
    _, only_past = _capture(past, success_head_arms(narrow))
    for name in ("emb_ridge", "success_head"):
        assert np.array_equal(full.predictions[name], only_past.predictions[name])


def test_deterministic_rebuild_and_no_store_or_network(monkeypatch):
    import socket
    import sqlite3

    monkeypatch.setattr(sqlite3, "connect", lambda *a, **k: pytest.fail("store access"))
    monkeypatch.setattr(socket, "socket", lambda *a, **k: pytest.fail("network access"))
    rows, content = _rows_and_content()
    first, a = _capture(rows, success_head_arms(content))
    second, b = _capture(rows, success_head_arms(content))
    for name in a.predictions:
        assert np.array_equal(a.predictions[name], b.predictions[name])
    assert first["manifest"]["arm_hashes"] == second["manifest"]["arm_hashes"]


def test_embeddings_help_when_the_text_carries_the_signal():
    rows, content = _rows_and_content(n=300, strength=3.0, seed=1)
    report, _ = _capture(rows, success_head_arms(content))
    arms = report["report1"]["arms"]
    assert arms["emb_ridge"]["overall"]["log_loss"]["mean"] < arms["tag_logistic"]["overall"]["log_loss"]["mean"]


def test_llm_labelled_difficulty_never_reaches_t8_arms():
    rows, content = _rows_and_content()
    labelled = [replace(r, features=replace(r.features, b=2.5, a=1.7, difficulty_source="llm_estimate",
                                            difficulty_variance=1.0)) for r in rows]
    _, neutral = _capture(rows, success_head_arms(content))
    _, llm = _capture(labelled, success_head_arms(content))
    for name in ("tag_logistic", "emb_ridge", "success_head"):
        assert np.array_equal(neutral.predictions[name], llm.predictions[name])


def test_difficulty_arm_abstains_without_solver_panel_and_uses_it_with():
    rows, content = _rows_and_content()
    arms = success_head_arms(content, include_difficulty=True)
    report, arrays = _capture(rows, arms)
    assert np.isnan(arrays.predictions["success_head+difficulty"]).all()
    assert report["report1"]["arms"]["success_head+difficulty"]["unscored_attempts"] == len(rows)
    head = LogisticHead(name="success_head+difficulty", views=("stem",), content=content,
                        moderated=True, difficulty=True)
    easy = replace(rows[0].features, difficulty_source="solver_panel", b=-1.5)
    hard = replace(easy, b=1.5)
    assert head.covers(easy) and not head.covers(rows[0].features)
    assert head.predict(easy) > head.predict(hard)


def test_moderation_shrinks_toward_half_and_more_off_support():
    rows, content = _rows_and_content(n=120, strength=3.0)
    point = LogisticHead(name="emb_ridge", views=("stem",), content=content)
    moderated = LogisticHead(name="success_head", views=("stem",), content=content, moderated=True)
    for row in rows:
        point.observe(row)
        moderated.observe(row)
    for row in rows[:20]:
        p, q = point.predict(row.features), moderated.predict(row.features)
        assert abs(q - .5) <= abs(p - .5) + 1e-12
    # A brand-new LO tag carries only its prior variance: wider than a known LO.
    known = rows[0].features
    unseen = replace(known, lo_id="never-seen-lo")
    assert moderated._covariance.size
    x_known, unseen_known = moderated._design_row(moderated._explicit(known), moderated._raw(known))
    x_new, unseen_new = moderated._design_row(moderated._explicit(unseen), moderated._raw(known))
    assert not unseen_known and unseen_new  # the new LO tag is off-support
    variance = lambda x, extra: float(x @ moderated._covariance @ x) + sum(v * v * s for v, _, s in extra)
    assert variance(x_new, unseen_new) > variance(x_known, unseen_known)


def test_abstention_is_never_a_synthetic_prediction():
    rows, content = _rows_and_content()
    missing = {(r.features.item_id, r.features.observed_at) for r in rows[::4]}
    partial = ContentIndex(
        {k: (replace(v, vectors={}) if k in missing else v) for k, v in content._entries.items()},
        embedding_model="fake-embed", views=("stem",))
    report, arrays = _capture(rows, success_head_arms(partial))
    assert np.isnan(arrays.predictions["emb_ridge"][::4]).all()
    assert np.isfinite(arrays.predictions["tag_logistic"]).all()
    assert report["report1"]["arms"]["emb_ridge"]["unscored_attempts"] == len(rows[::4])
    assert set(report["report1"]["arms"]["emb_ridge"]["splits"]["item_position"]) == {
        "first_unseen_item", "repeat_item"}


def test_t8_arms_are_never_activatable():
    rows, content = _rows_and_content(n=5)
    for arm in success_head_arms(content, include_difficulty=True):
        assert arm.calibrated_uncertainty is False
        assert not is_calibrated_predictor(arm)


def test_content_index_rejects_mismatched_views_and_takes_only_features():
    with pytest.raises(ValueError, match="views and dimensions"):
        ContentIndex({("i", "t"): AttemptContent(vectors={"stem": (1.0,) * 31})})
    with pytest.raises(ValueError, match="views"):
        ContentIndex({("i", "t"): AttemptContent(vectors={"skeleton": (1.0,) * 32})})
    with pytest.raises(TypeError):
        ContentIndex({}).get(("i", "t"))


def test_priors_are_a_priori_and_recorded():
    assert PREREGISTRATION["priors"] == {
        "bias_variance": 1.0, "ability_mean": 1.0, "ability_variance": .25,
        "feature_variance": .25, "tag_variance": .25, "embedding_variance": .25,
        "difficulty_mean": -1.0, "difficulty_variance": .25, "recency_half_life_days": 1.0,
    }
    assert PREREGISTRATION["margin_nats_per_attempt"] == 0.0
    assert PREREGISTRATION["explicit_arms"] == list(EXPLICIT_ARMS)
    assert len(preregistration_hash()) == 64
    with pytest.raises(ValueError):
        HeadPriors(embedding_variance=0)


# -- the pre-registered analysis ------------------------------------------------

V2_HASH = "746e4938a258896ac884aeaf95d544d3a148e26429a86b9307f83532a1e142ee"
# v3 as first staged, with the six-item cutoff that review F2 removed.
V3_STAGED_HASH = "e7a174f459e7613857e072a59d00c92b5dd495047e31f7bf01c9729117dc9976"
V3_HASH = "a2beed27c4ee19db039c55d112e732850c223c2e6cbb277ee6cbdd9278cc1372"
DELTA = .005
T_METHOD, BOOTSTRAP_METHOD = "cluster_robust_t_cr1", "item_bootstrap_percentile"
ADDS_VALUE, NULL, NOISY_NULL = (.05, .02), (.01, .02), (.01, .2)  # (mean gain, per-attempt sd)


def _arrays(n, gains, *, extra=None, samples=200, seed=0, labels=None, per_item=2):
    """Synthetic scored rows, ``per_item`` attempts per item in attempt order.

    ``gains`` maps an arm to its per-attempt loss reduction from 0.5, either a
    mean (sd 0.02) or ``(mean, sd)``; the best explicit arm, ``lo_general``,
    gains exactly 0.01, so an arm's gain over e* is its mean minus 0.01.
    """
    rng = np.random.default_rng(5)
    y = rng.integers(0, 2, size=n).astype(float)
    base = np.full(n, .5)

    def improved(gain):
        # Shift toward the outcome so the per-attempt loss falls by ``gain``.
        return np.where(y == 1, .5 * np.exp(gain), 1 - .5 * np.exp(gain))

    predictions = {name: base.copy() for name in EXPLICIT_ARMS}
    predictions["lo_general"] = improved(np.full(n, .01))  # the best explicit arm
    for name, gain in gains.items():
        mean, sd = gain if isinstance(gain, tuple) else (gain, .02)
        predictions[name] = improved(mean + rng.normal(0, sd, n))
    predictions.update(extra or {})
    labels = labels or tuple({"item_position": "first_unseen_item" if i % 3 == 0 else "repeat_item",
                              "attempt_position": "later"} for i in range(n))
    items = np.arange(n) // per_item
    return ReplayArrays(y, predictions, labels, np.ones(n, dtype=bool), samples, seed, items, "item")


def _primary(arrays):
    return make_t8_analysis()(arrays)["primary"]["verdict"]


def test_kill_rule_picks_the_best_explicit_arm_and_kills_without_a_gain():
    analysis = make_t8_analysis()(_arrays(400, {"emb_ridge": NULL, "success_head": .02}))
    primary = analysis["primary"]
    assert primary["comparison"]["baseline"] == "lo_general"
    assert primary["comparison"]["log_loss_gain"]["mean"] == pytest.approx(0, abs=.003)
    assert primary["verdict"]["decision"] == "kill"
    assert primary["verdict"]["reason_code"] == "upper_bound_below_delta"
    assert primary["verdict"]["ci95"][1] < PREREGISTRATION["smallest_worthwhile_gain_nats_per_attempt"]
    assert analysis["gated"]["success_head"]["interpretation"] == "not_interpreted"
    assert analysis["activates"] is False


def test_embeddings_add_value_opens_the_gate():
    analysis = make_t8_analysis()(_arrays(400, {"emb_ridge": ADDS_VALUE, "success_head": .06}))
    assert analysis["primary"]["verdict"]["decision"] == "embeddings_add_value"
    gated = analysis["gated"]["success_head"]
    assert gated["interpretation"] == "interpreted" and gated["verdict"] == "embeddings_add_value"
    splits = analysis["primary"]["comparison"]["splits"]["item_position"]
    assert splits["first_unseen_item"]["n"] + splits["repeat_item"]["n"] == 400


def test_a_large_effect_is_decided_with_fewer_than_100_attempts():
    # v2 answered insufficient_data below a fixed 100 attempts; v3 has no floor.
    verdict = _primary(_arrays(40, {"emb_ridge": .2}, samples=1000))
    assert verdict["n"] == 40 and verdict["item_clusters"] == 20
    assert verdict["ci95"][0] > PREREGISTRATION["margin_nats_per_attempt"]
    assert verdict["decision"] == "embeddings_add_value"
    assert verdict["reason_code"] == "lower_bound_above_margin"
    assert verdict["reason"].startswith("lower bound ")


def test_a_null_effect_is_undecided_until_the_upper_bound_falls_below_delta():
    delta = PREREGISTRATION["smallest_worthwhile_gain_nats_per_attempt"]
    # 150 attempts: v2 would kill (n >= 100, lower bound <= 0); v3 cannot rule
    # out a gain worth building, so it makes no decision.
    small = _primary(_arrays(150, {"emb_ridge": (.01, .1)}, samples=1000))
    assert small["ci95"][0] <= 0 and small["ci95"][1] >= delta
    assert small["decision"] == "insufficient_data" and small["reason_code"] == "undecided"
    assert small["reason"].startswith("undecided: ")
    # The same null effect with enough data: the whole interval is below delta.
    large = _primary(_arrays(8000, {"emb_ridge": (.01, .1)}, samples=1000))
    assert large["ci95"][1] < delta
    assert large["ci95"][0] <= 0
    assert large["decision"] == "kill" and large["reason_code"] == "upper_bound_below_delta"
    assert large["reason"].startswith("upper bound ")


def test_a_real_gain_below_delta_is_kill_with_its_reason():
    # v4 (owner, 2026-10-12): an interval wholly inside (0, delta) is a real
    # gain too small to build on. v3 called it embeddings_add_value.
    verdict = _primary(_arrays(8000, {"emb_ridge": (.0125, .05)}, samples=1000))
    assert 0 < verdict["ci95"][0] and verdict["ci95"][1] < DELTA
    assert verdict["decision"] == "kill"
    assert verdict["reason_code"] == "real_gain_below_delta"
    assert verdict["reason"].startswith("lower bound ")
    assert f"δ = {DELTA}" in verdict["reason"] and "smaller than the smallest worth building" in verdict["reason"]
    # The reason says which delta would have decided otherwise, so delta can be monitored.
    upper = float(f"{verdict['ci95'][1]:.4g}")
    assert f"it would be embeddings_add_value for any δ <= {upper:.4g})" in verdict["reason"]
    assert verdict["smallest_worthwhile_gain_nats_per_attempt"] == DELTA
    # A gated secondary in (0, delta) is kill too, and closes the gate.
    analysis = make_t8_analysis()(_arrays(8000, {
        "emb_ridge": ADDS_VALUE, "success_head": (.0125, .05), "success_head+difficulty": ADDS_VALUE}))
    gated = analysis["gated"]["success_head"]
    assert (gated["verdict"], gated["verdict_reason_code"]) == ("kill", "real_gain_below_delta")
    assert analysis["gated"]["success_head+difficulty"]["interpretation"] == "not_interpreted"
    text = "\n".join(summary_lines(analysis))
    assert "kill (`real_gain_below_delta`)" in text


def test_no_interval_is_insufficient_data_with_the_reason():
    one_item = _primary(_arrays(40, {"emb_ridge": .2}, per_item=40))
    assert one_item["decision"] == "insufficient_data" and one_item["item_clusters"] == 1
    assert one_item["ci95"] is None
    assert one_item["reason"] == "no interval: one cluster: no between-cluster variance (df = 0)"
    assert one_item["reason_code"] == "no_interval"
    arrays = _arrays(400, {})
    same = make_t8_analysis()(_arrays(400, {}, extra={"emb_ridge": arrays.predictions["lo_general"]}))
    assert same["primary"]["verdict"]["reason"] == "no interval: zero variance across clusters"
    assert same["primary"]["verdict"]["decision"] == "insufficient_data"
    assert same["gated"]["success_head"]["status"] == "unavailable"
    missing = _primary(_arrays(40, {}))
    assert missing["decision"] == "insufficient_data" and missing["reason"] == "no interval: arm not run"


def test_five_items_with_a_clear_gain_are_decided():
    # Five items, 100 attempts each, gains 0.10-0.14 nats. There is no item
    # minimum: balanced clusters make the CR1 interval the t interval on the
    # five item means, df = 4 (v3's percentile bootstrap gave [0.108, 0.132]).
    item_gains = np.array([.10, .11, .12, .13, .14])
    gains = np.repeat(item_gains, 100) + .01  # over lo_general's 0.01
    verdict = _primary(_arrays(500, {"emb_ridge": (gains, 0.)}, per_item=100, samples=1000))
    half = 2.77644510519779 * item_gains.std(ddof=1) / np.sqrt(5)  # qt(.975, 4)
    assert (verdict["n"], verdict["item_clusters"], verdict["df"]) == (500, 5, 4)
    assert verdict["ci95"] == pytest.approx([.12 - half, .12 + half], abs=1e-6)
    assert verdict["decision"] == "embeddings_add_value"


def test_three_items_that_v3_killed_are_undecided_under_the_t_interval():
    # Three items whose mean gains are -0.045, -0.025 and -0.005. v3's
    # percentile bootstrap of three item means cannot exceed the largest, so it
    # stayed below delta and killed; with t(2) = 4.30 the interval reaches both
    # 0 and delta.
    gains = np.repeat([-.045, -.025, -.005], 8) + .01  # over lo_general's 0.01
    arrays = _arrays(24, {"emb_ridge": (gains, 0.)}, per_item=8, samples=1000)
    verdict = _primary(arrays)
    assert (verdict["item_clusters"], verdict["df"]) == (3, 2)
    assert verdict["ci95"][0] < 0 and verdict["ci95"][1] > DELTA
    assert verdict["decision"] == "insufficient_data" and verdict["reason_code"] == "undecided"
    differences = _loss(arrays.outcomes, arrays.predictions["lo_general"]) - _loss(
        arrays.outcomes, arrays.predictions["emb_ridge"])
    v3 = paired_bootstrap(differences, samples=1000, seed=0, clusters=arrays.item_clusters)
    assert v3["ci95"][1] < DELTA  # v3's rule: kill


@pytest.mark.parametrize("items", [2, 3, 5])
def test_a_few_items_are_decided_by_their_interval_alone(items):
    # Every item favours e* by 0.2 nats (sd 0.02 per attempt): even t with
    # items - 1 degrees of freedom stays below delta, and there is no item floor.
    verdict = _primary(_arrays(8 * items, {"emb_ridge": -.2}, per_item=8, samples=1000))
    assert verdict["item_clusters"] == items
    assert verdict["ci95"][1] < 0
    assert verdict["decision"] == "kill" and verdict["reason"].startswith("upper bound ")


def test_every_interval_in_the_t8_report_clusters_items_and_names_its_method():
    # Review F1: 60 attempts on three items. The whole T8 report, not only
    # analyses.t8, clusters on items (report 1 metrics, splits and the incumbent
    # comparisons included), and the manifest says so. v4: the verdict
    # intervals are cluster-robust t; every other interval stays a percentile
    # item bootstrap, and each one in the analysis names its method.
    rows, content = _rows_and_content(n=60, n_items=3)
    captured = {}

    def keep(arrays):
        captured["arrays"] = arrays
        return {}

    report = evaluate(rows, arms=("base_rate_lo", "mastery_ekf", "lo_general", *success_head_arms(content)),
                      bootstrap_samples=50, bootstrap_unit="item",
                      analyses={"t8": make_t8_analysis(), "keep": keep})
    arrays = captured["arrays"]
    assert arrays.bootstrap_unit == "item"
    assert report["manifest"]["bootstrap"]["unit"] == "item"
    intervals = []
    stack = [report]
    while stack:
        value = stack.pop()
        if isinstance(value, dict):
            intervals += [value] if "ci95" in value else []
            stack.extend(value.values())
        elif isinstance(value, list):
            stack.extend(value)
    assert len(intervals) > 100
    # The verdict repeats the primary interval under ``item_clusters``.
    counts = [interval.get("clusters", interval.get("item_clusters")) for interval in intervals
              if interval["n"]]
    assert counts and all(1 <= count <= 3 for count in counts)
    y, clusters = arrays.outcomes, arrays.item_clusters
    loss = {name: _loss(y, arrays.predictions[name]) for name in ("mastery_ekf", "emb_ridge")}
    scored = np.isfinite(loss["emb_ridge"])
    assert report["report1"]["arms"]["emb_ridge"]["overall"]["log_loss"] == paired_bootstrap(
        loss["emb_ridge"][scored], samples=50, seed=0, clusters=clusters[scored])
    difference = loss["mastery_ekf"] - loss["emb_ridge"]
    finite = np.isfinite(difference)
    assert report["report1"]["comparisons"]["emb_ridge"]["log_loss_improvement"] == paired_bootstrap(
        difference[finite], samples=50, seed=0, clusters=clusters[finite])
    t8 = report["analyses"]["t8"]
    verdict = t8["primary"]["verdict"]
    assert verdict["item_clusters"] == 3 and verdict["ci95"] is not None  # no item floor (F2)
    assert verdict["method"] == T_METHOD
    assert t8["primary"]["comparison"]["log_loss_gain"] == cluster_t_interval(
        _loss(y, arrays.predictions[t8["primary"]["comparison"]["baseline"]])[scored]
        - loss["emb_ridge"][scored],
        clusters[scored])
    assert t8["gated"]["success_head"]["log_loss_gain"]["method"] == T_METHOD
    methods = []
    stack = [t8]
    while stack:
        value = stack.pop()
        if isinstance(value, dict):
            methods += [value.get("method")] if "ci95" in value else []
            stack.extend(value.values())
        elif isinstance(value, list):
            stack.extend(value)
    assert set(methods) == {T_METHOD, BOOTSTRAP_METHOD}
    descriptive = t8["descriptive"]["emb_ridge_vs_tag_logistic"]
    assert descriptive["log_loss_gain"]["method"] == BOOTSTRAP_METHOD
    assert all(split["method"] == BOOTSTRAP_METHOD
               for split in t8["primary"]["comparison"]["splits"]["item_position"].values())
    assert "verdict intervals name their method" in report["manifest"]["bootstrap"]["scope"]


def test_t8_refuses_a_harness_that_resamples_attempts():
    rows, content = _rows_and_content(n=40, n_items=10)
    with pytest.raises(ValueError, match="bootstrap_unit"):
        evaluate(rows, arms=("base_rate_lo", "mastery_ekf", "lo_general", *success_head_arms(content)),
                 bootstrap_samples=10, analyses={"t8": make_t8_analysis()})


GATE_INPUTS = {"embeddings_add_value": ADDS_VALUE, "kill": NULL, "insufficient_data": NOISY_NULL}


@pytest.mark.parametrize("primary", GATE_INPUTS)
def test_only_embeddings_add_value_opens_the_gate(primary):
    analysis = make_t8_analysis()(_arrays(400, {
        "emb_ridge": GATE_INPUTS[primary], "success_head": ADDS_VALUE,
        "success_head+difficulty": ADDS_VALUE}))
    assert analysis["primary"]["verdict"]["decision"] == primary
    expected = "interpreted" if primary == "embeddings_add_value" else "not_interpreted"
    for arm in ("success_head", "success_head+difficulty"):
        gated = analysis["gated"][arm]
        assert gated["verdict"] == "embeddings_add_value"  # still computed and printed
        assert gated["interpretation"] == expected


@pytest.mark.parametrize("secondary", GATE_INPUTS)
def test_each_secondary_verdict_gates_the_next_comparison(secondary):
    # Primary passes; success_head gets each verdict; success_head+difficulty
    # would win, but is read only after an embeddings_add_value (review F2).
    analysis = make_t8_analysis()(_arrays(400, {
        "emb_ridge": ADDS_VALUE, "success_head": GATE_INPUTS[secondary],
        "success_head+difficulty": ADDS_VALUE}))
    assert analysis["primary"]["verdict"]["decision"] == "embeddings_add_value"
    first, second = (analysis["gated"][arm] for arm in ("success_head", "success_head+difficulty"))
    assert first["interpretation"] == "interpreted" and first["verdict"] == secondary
    assert first["verdict_reason"]
    assert second["verdict"] == "embeddings_add_value"
    assert second["interpretation"] == ("interpreted" if secondary == "embeddings_add_value"
                                        else "not_interpreted")


def test_the_report_shows_how_far_the_data_is_from_a_decision():
    analysis = make_t8_analysis()(_arrays(150, {"emb_ridge": NOISY_NULL}))
    verdict = analysis["primary"]["verdict"]
    assert {key: verdict[key] for key in ("decision", "n", "item_clusters", "margin_nats_per_attempt",
                                          "smallest_worthwhile_gain_nats_per_attempt", "df")} == {
        "decision": "insufficient_data", "n": 150, "item_clusters": 75,
        "margin_nats_per_attempt": 0.0, "smallest_worthwhile_gain_nats_per_attempt": .005, "df": 74}
    assert verdict["ci95"] == analysis["primary"]["comparison"]["log_loss_gain"]["ci95"]
    text = "\n".join(summary_lines(analysis))
    for expected in ("n = 150 common attempts in 75 item clusters",
                     "95% cluster-robust t interval (CR1 over items, df = 74, t = 1.993) [",
                     "m = 0.0", "δ = 0.005", "**Decision: insufficient_data** (`undecided`): undecided: "):
        assert expected in text


def test_delta_and_the_interval_are_recorded_in_every_report():
    # The owner monitors whether delta itself needs changing: every T8 report
    # records the delta in force, m, n, the item count, the interval and its
    # method, in the JSON and in the markdown.
    analysis = make_t8_analysis()(_arrays(400, {"emb_ridge": ADDS_VALUE, "success_head": NULL}))
    rule = analysis["decision_rule"]
    assert rule == {
        "smallest_worthwhile_gain_nats_per_attempt": DELTA, "margin_nats_per_attempt": 0.0,
        "interval": {"method": T_METHOD, "level": .95, "unit": "item",
                     "degrees_of_freedom": "items - 1"},
        "kill": "upper bound < δ (real_gain_below_delta when the lower bound is also > m)",
        "embeddings_add_value": "otherwise, lower bound > m",
        "insufficient_data": "otherwise, or no interval",
    }
    verdict = analysis["primary"]["verdict"]
    assert {"n", "item_clusters", "mean", "se", "df", "t_critical", "ci95", "method",
            "margin_nats_per_attempt", "smallest_worthwhile_gain_nats_per_attempt"} <= set(verdict)
    assert verdict["smallest_worthwhile_gain_nats_per_attempt"] == DELTA
    gated = analysis["gated"]["success_head"]
    assert gated["verdict_reason_code"] == "upper_bound_below_delta"
    assert gated["log_loss_gain"]["method"] == T_METHOD and gated["log_loss_gain"]["df"] == 199
    assert json.loads(json.dumps(analysis, allow_nan=False)) == analysis
    text = "\n".join(summary_lines(analysis))
    for expected in ("δ in force: 0.005 nats per attempt (m = 0.0)",
                     "n = 400 common attempts in 200 item clusters",
                     "cluster-robust t interval (CR1 over items, df = 199",
                     "Gated `success_head` (interpreted): kill (`upper_bound_below_delta`)",
                     "percentile item bootstrap"):
        assert expected in text, expected


def test_the_verdict_interval_does_not_depend_on_bootstrap_settings():
    arrays = _arrays(200, {"emb_ridge": NOISY_NULL})
    verdicts = [_primary(replace(arrays, bootstrap_samples=samples, seed=seed))
                for samples, seed in ((200, 0), (37, 9))]
    assert verdicts[0] == verdicts[1]
    differences = _loss(arrays.outcomes, arrays.predictions["lo_general"]) - _loss(
        arrays.outcomes, arrays.predictions["emb_ridge"])
    assert verdicts[0]["ci95"] == cluster_t_interval(differences, arrays.item_clusters)["ci95"]


def test_partial_coverage_is_flagged():
    arrays = _arrays(400, {"emb_ridge": ADDS_VALUE})
    arrays.predictions["emb_ridge"][:150] = np.nan
    flagged = make_t8_analysis()(arrays)
    assert flagged["primary"]["comparison"]["n"] == 250
    assert flagged["primary"]["verdict"]["caveats"] == ["partial_coverage"]


def test_preregistration_v4_changes_the_hash_and_every_report_carries_it():
    from learnloop.field.evaluation import ZERO_SPREAD

    assert PREREGISTRATION["version"] == "t8-preregistration-v4"
    assert "min_common_attempts" not in PREREGISTRATION
    assert PREREGISTRATION["margin_nats_per_attempt"] == 0.0
    assert PREREGISTRATION["smallest_worthwhile_gain_nats_per_attempt"] == .005
    assert PREREGISTRATION["bootstrap"]["unit"] == "item"
    assert {k: PREREGISTRATION["bootstrap"][k] for k in ("samples", "seed")} == {"samples": 1000, "seed": 0}
    assert PREREGISTRATION["bootstrap"]["scope"].startswith("descriptive intervals only")
    # v4: the verdict interval is cluster-robust t (CR1), df = items - 1.
    assert PREREGISTRATION["decision_interval"]["method"] == T_METHOD
    assert PREREGISTRATION["decision_interval"]["degrees_of_freedom"] == "items - 1"
    assert PREREGISTRATION["decision_rule"]["kill"].startswith("ci95 upper bound < smallest_worthwhile_gain")
    # Review F2: no minimum item count; only degenerate inputs have no interval.
    assert PREREGISTRATION["no_interval"]["zero_spread_nats"] == ZERO_SPREAD
    assert "min_clusters" not in json.dumps(dict(PREREGISTRATION))
    digest = preregistration_hash()
    assert digest not in (V2_HASH, V3_STAGED_HASH, V3_HASH)
    analysis = make_t8_analysis()(_arrays(100, {"emb_ridge": ADDS_VALUE}))
    assert analysis["preregistration"] == {"version": "t8-preregistration-v4", "hash": digest,
                                           "deviations": ["bootstrap_samples"]}
    text = "\n".join(summary_lines(analysis))
    assert f"`t8-preregistration-v4` (hash `{digest[:16]}`)" in text


def test_the_harness_hands_item_clusters_and_t8_resamples_items():
    rows, content = _rows_and_content(n=80, n_items=20)
    report, arrays = _capture(rows, ("base_rate_lo", "mastery_ekf", "lo_general",
                                     *success_head_arms(content)), bootstrap_unit="item")
    items = [row.features.item_id for row in rows]
    assert len(arrays.item_clusters) == len(arrays.outcomes) == len(rows)
    # One opaque integer per item, in first-appearance order; never an id.
    assert arrays.item_clusters.tolist() == [list(dict.fromkeys(items)).index(i) for i in items]
    verdict = make_t8_analysis()(arrays)["primary"]["verdict"]
    assert verdict["n"] == len(rows) and verdict["item_clusters"] == len(set(items))
    assert "item_clusters" not in json.dumps(report)


def test_unavailable_arms_and_deviations_are_reported():
    arrays = _arrays(200, {"emb_ridge": .05}, samples=10, seed=3)
    analysis = make_t8_analysis(unavailable={
        "success_head+difficulty": "no solver_panel difficulty",
        "llm_zero_data": "not run", "llm_zero_data:recalibrated": "not run",
    })(arrays)
    assert analysis["gated"]["success_head+difficulty"] == {
        "status": "unavailable", "reason": "no solver_panel difficulty"}
    assert analysis["gated"]["success_head"]["status"] == "unavailable"  # arm absent
    assert analysis["descriptive"]["llm_zero_data"]["status"] == "unavailable"
    assert analysis["preregistration"]["deviations"] == ["bootstrap_samples", "seed"]
    text = "\n".join(summary_lines(analysis))
    assert "Decision:" in text and "deviations: bootstrap_samples, seed" in text


def test_llm_arms_are_descriptive_against_explicit_and_embedding_arms():
    n = 200
    arrays = _arrays(n, {"emb_ridge": .03, "llm_zero_data": .04})
    analysis = make_t8_analysis(unavailable={"llm_zero_data:recalibrated": "not run"})(arrays)
    llm = analysis["descriptive"]["llm_zero_data"]
    assert llm["vs_best_explicit"]["baseline"] == "lo_general"
    assert llm["vs_emb_ridge"]["baseline"] == "emb_ridge"
    assert llm["vs_emb_ridge"]["log_loss_gain"]["mean"] == pytest.approx(.01, abs=.004)
    assert llm["vs_emb_ridge"]["log_loss_gain"]["clusters"] == n // 2  # items, not attempts


def test_recency_running_sum_equals_the_full_weighted_sum():
    from learnloop.clock import parse_utc

    rows, content = _rows_and_content(n=12)
    head = LogisticHead(name="tag_logistic")
    for row in rows:
        head.observe(row)
    when = parse_utc(rows[-1].observed_at) + timedelta(hours=5)
    weights = [0.5 ** ((when - parse_utc(r.observed_at)).total_seconds() / 86400) for r in rows]
    expected = sum(w * (r.outcome - .5) for w, r in zip(weights, rows)) / (sum(weights) + 1)
    assert head._recency(when) == pytest.approx(expected, rel=1e-12)

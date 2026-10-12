"""T8 success-head arms and the pre-registered analysis: synthetic, store-free."""
from dataclasses import replace
from datetime import datetime, timedelta, timezone

import numpy as np
import pytest

from learnloop.field.evaluation import ReplayArrays, evaluate
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

def _arrays(n, gains, *, extra=None, samples=200, seed=0, labels=None):
    rng = np.random.default_rng(5)
    y = rng.integers(0, 2, size=n).astype(float)
    base = np.full(n, .5)

    def improved(gain):
        # Shift toward the outcome so the per-attempt loss falls by ``gain``.
        return np.where(y == 1, .5 * np.exp(gain), 1 - .5 * np.exp(gain))

    predictions = {name: base.copy() for name in EXPLICIT_ARMS}
    predictions["lo_general"] = improved(.01)  # the best explicit arm
    for name, gain in gains.items():
        predictions[name] = improved(gain)
    predictions.update(extra or {})
    labels = labels or tuple({"item_position": "first_unseen_item" if i % 3 == 0 else "repeat_item",
                              "attempt_position": "later"} for i in range(n))
    return ReplayArrays(y, predictions, labels, np.ones(n, dtype=bool), samples, seed)


def test_kill_rule_picks_the_best_explicit_arm_and_kills_without_a_gain():
    analysis = make_t8_analysis()(_arrays(400, {"emb_ridge": .01, "success_head": .02}))
    primary = analysis["primary"]
    assert primary["comparison"]["baseline"] == "lo_general"
    assert primary["comparison"]["log_loss_gain"]["mean"] == pytest.approx(0, abs=1e-12)
    assert primary["verdict"]["decision"] == "kill"
    assert analysis["gated"]["success_head"]["interpretation"] == "not_interpreted"
    assert analysis["activates"] is False


def test_embeddings_add_value_opens_the_gate():
    analysis = make_t8_analysis()(_arrays(400, {"emb_ridge": .05, "success_head": .06}))
    assert analysis["primary"]["verdict"]["decision"] == "embeddings_add_value"
    gated = analysis["gated"]["success_head"]
    assert gated["interpretation"] == "interpreted" and gated["verdict"] == "embeddings_add_value"
    splits = analysis["primary"]["comparison"]["splits"]["item_position"]
    assert splits["first_unseen_item"]["n"] + splits["repeat_item"]["n"] == 400


def test_too_few_common_attempts_is_no_decision_and_partial_coverage_is_flagged():
    small = make_t8_analysis()(_arrays(60, {"emb_ridge": .2}))
    assert small["primary"]["verdict"]["decision"] == "insufficient_data"
    arrays = _arrays(400, {"emb_ridge": .05})
    arrays.predictions["emb_ridge"][:150] = np.nan
    flagged = make_t8_analysis()(arrays)
    assert flagged["primary"]["comparison"]["n"] == 250
    assert flagged["primary"]["verdict"]["caveats"] == ["partial_coverage"]


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
    assert llm["vs_emb_ridge"]["log_loss_gain"]["mean"] == pytest.approx(.01, abs=1e-9)


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

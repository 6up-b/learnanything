"""Synthetic store-free tests; never open a working fixture or a model route."""
from dataclasses import replace
from datetime import datetime, timedelta, timezone
import json
from math import log

import numpy as np
import pytest

from learnloop.field.evaluation import (
    cluster_t_interval, evaluate, family_arms, paired_bootstrap, report_digest, write_reports,
)
from learnloop.field.types import AttemptRow, FacetRow, ItemFeatures, RegionEstimate, SignalRow


def attempt(n, lo="lo", outcome=1., **kwargs):
    return AttemptRow(str(n), ItemFeatures(f"item{n}", lo, f"2026-01-{n:02}T00:00:00Z"),
                      outcome, 1., **kwargs)


class Spy:
    granularity = "attempt"
    version_hash = "fake-v1"
    calibrated_uncertainty = True

    def __init__(self, name="mastery_ekf", p=.5, log=None, mean=5):
        self.name, self.p, self.log, self.mean = name, p, log if log is not None else [], mean
        self.seen = set()

    def predict(self, features):
        assert isinstance(features, ItemFeatures)
        assert not hasattr(features, "outcome")
        assert not hasattr(features, "effective_mass")
        self.log.append(("predict", self.name, features.item_id))
        return self.p

    def observe(self, row):
        self.log.append(("observe", self.name, row.lo_id))
        if isinstance(row, AttemptRow):
            self.seen.add(row.lo_id)

    def region_estimates(self):
        return {lo: RegionEstimate(self.mean, .01, 2, False) for lo in self.seen}


def run(rows, arms=None, **kwargs):
    return evaluate(rows, arms=arms or [Spy()], bootstrap_samples=30, **kwargs)


def test_predict_before_any_arm_observes_and_chronological():
    log_events = []
    run([attempt(2), attempt(1)], [Spy("a", log=log_events), Spy("b", log=log_events)])
    assert log_events[:4] == [
        ("predict", "a", "item1"), ("predict", "b", "item1"),
        ("observe", "a", "lo"), ("observe", "b", "lo"),
    ]


def test_no_store_access(monkeypatch):
    import sqlite3
    import socket
    monkeypatch.setattr(sqlite3, "connect", lambda *a, **kw: pytest.fail("store access"))
    monkeypatch.setattr(socket, "socket", lambda *a, **kw: pytest.fail("network access"))
    report = run([attempt(1), attempt(2)], ["mastery_ekf", "lo_general", "base_rate_lo"])
    assert report["counts"]["scored_attempts"] == 2


def test_assistance_only_zero_reaches_hint_replacement_arm():
    from learnloop.field.predictors import create_predictor

    hinted = replace(attempt(1), effective_mass=0, hints_used=5, mass_without_assistance=1)
    hint_arm = create_predictor("lo_general+hints")
    incumbent = create_predictor("mastery_ekf")
    before = incumbent.snapshot_bytes()
    report = run([hinted], [incumbent, hint_arm])
    assert report["counts"]["scored_attempts"] == 1
    assert incumbent.snapshot_bytes() == before
    assert hint_arm.region_estimates(["lo"])["lo"].mean < 0


def test_first_unseen_split_counts_excluded_encounters_but_not_signals():
    rows = [attempt(1, revision_status="excluded"), attempt(2), attempt(3, "new")]
    rows += [SignalRow("s", "new", "2026-01-01T00:00:00Z", "prerequisite")]
    report = run(rows)
    splits = report["report1"]["arms"]["mastery_ekf"]["splits"]["attempt_position"]
    assert splits["first_unseen_lo"]["n"] == 1
    assert splits["later"]["n"] == 1
    assert report["counts"]["excluded_attempts"] == 1


def test_manifest_determinism_hashes_inputs_config_and_no_text(tmp_path):
    rows = [attempt(1, "PRIVATE TOPIC"), attempt(2)]
    report = run(rows, config={"algorithms": {"algorithm_version": "mvp-test"}})
    assert report == run(reversed(rows), config={"algorithms": {"algorithm_version": "mvp-test"}})
    assert report["manifest"]["algorithm"] == "mvp-test"
    assert report["manifest"]["kernel"] == "not_used"
    assert report["manifest"]["bootstrap"]["unit"] == "attempt"
    assert report["manifest"]["data_snapshot"] != run([replace(rows[0], outcome=0)])["manifest"]["data_snapshot"]
    paths = write_reports(report, tmp_path)
    assert "PRIVATE TOPIC" not in json.dumps(report)
    assert set(paths) == {"json", "markdown"}
    assert "PRIVATE TOPIC" not in (tmp_path / "evaluation.md").read_text()


def test_facet_predictions_aggregate_before_observe_not_multiply_attempts():
    class Facets(Spy):
        granularity = "facet"

        def predict(self, features):
            assert not self.seen
            return .2 if features.facet_id == "a" else .8

    row = attempt(1)
    facets = [FacetRow(**{f: getattr(row, f) for f in row.__dataclass_fields__},
                       facet_id=name, facet_share=share)
              for name, share in [("a", .25), ("b", .75)]]
    report = run([row, *facets], [Facets()])
    metrics = report["report1"]["arms"]["mastery_ekf"]["overall"]
    assert metrics["n"] == 1
    assert metrics["log_loss"]["mean"] == pytest.approx(-log(.65))
    assert metrics["log_loss"]["ci95"] == pytest.approx([-log(.65)] * 2)


def test_missing_facets_abstain_without_dropping_attempt_arms():
    report = run([attempt(1)], ["mastery_ekf", "facet_beta"])
    arms = report["report1"]["arms"]
    assert arms["mastery_ekf"]["overall"]["n"] == 1
    assert arms["facet_beta"]["overall"]["n"] == 0
    assert arms["facet_beta"]["missing_facet_exclusions"] == 1
    json.dumps(report, allow_nan=False)


def test_paired_bootstrap_is_deterministic_and_keeps_attempt_differences_paired():
    a = paired_bootstrap([.1, .1, .1], samples=100, seed=2)
    assert a["ci95"] == pytest.approx([.1, .1])
    assert a == paired_bootstrap([.1, .1, .1], samples=100, seed=2)


def _rich_stream(n=90, seed=11):
    """Repeats, fractional outcomes, hints, zero mass, retrievals, families, facets, signals."""
    rng = np.random.default_rng(seed)
    start = datetime(2026, 3, 1, tzinfo=timezone.utc)
    rows = []
    for k in range(n):
        item = int(rng.integers(12))
        at = (start + timedelta(hours=7 * k)).isoformat().replace("+00:00", "Z")
        family = f"fam{item % 4}" if item % 3 else None
        features = ItemFeatures(
            f"item{item}", f"lo{item % 4}", at, capability="apply" if item % 2 else "recall",
            family_id=family,
            variant_relation=("same_target", "isomorph", "near")[item % 3] if family else None,
            retrievability=float(rng.uniform(.3, .95)) if k % 2 else None,
        )
        outcome = float(rng.choice([0.0, 0.5, 1.0], p=[.3, .2, .5]))
        rows.append(AttemptRow(
            f"a{k:03}", features, outcome, 0.0 if k % 17 == 5 else 1.0,
            hints_used=int(k % 9 == 4), mass_without_assistance=1.0 if k % 9 == 4 else None,
            fsrs_rating=int(rng.integers(1, 5)) if k % 3 == 0 else None, retrieval_cold=k % 3 == 0,
            preceded_by_question=k % 11 == 3,
        ))
        if k % 10 == 7:
            rows.append(FacetRow(f"a{k:03}", features, outcome, 1.0, facet_id="f1", facet_share=.6))
            rows.append(FacetRow(f"a{k:03}", features, outcome, 1.0, facet_id="f2", facet_share=.4))
        if k % 13 == 2:
            rows.append(SignalRow(f"s{k:03}", f"lo{item % 4}", at, "question"))
    return rows


#: What the offline answer-signal arms (owner 2026-10-13) add to a report: the
#: arms themselves, the Brier split on every metric block, two split
#: dimensions, four counts and one limitation block. Everything else is
#: unchanged.
_ANSWER_SIGNAL_SPLITS = ("answer_confidence", "answer_hedging")
_ANSWER_SIGNAL_COUNTS = ("answer_confidence_present", "answer_hedging_read",
                         "answer_confidence_share", "answer_hedging_share")


def _without_answer_signals(report):
    """The report as the harness wrote it before the answer-signal arms."""
    import copy

    from learnloop.field.answer_signals import ARM_NAMES, default_pairs
    from learnloop.field.evaluation import ANSWER_SIGNAL_LIMITATIONS

    added = {*ARM_NAMES.values(), *(challenger for _, challenger in default_pairs())}
    out = copy.deepcopy(report)

    def strip(metrics):
        metrics.pop("brier_decomposition", None)
        return metrics

    for name in list(out["report1"]["arms"]):
        if name in added:
            del out["report1"]["arms"][name]
            continue
        values = out["report1"]["arms"][name]
        strip(values["overall"])
        for dimension in _ANSWER_SIGNAL_SPLITS:
            values["splits"].pop(dimension, None)
        for groups in values["splits"].values():
            for metrics in groups.values():
                strip(metrics)
    for section in (out["report2"]["arms"], out["report1"]["comparisons"],
                    out["manifest"]["arm_hashes"], out["manifest"]["arm_models"]):
        for name in added:
            section.pop(name, None)
    for key in _ANSWER_SIGNAL_COUNTS:
        out["counts"].pop(key, None)
    out["report1"]["limitations"] = [
        text for text in out["report1"]["limitations"] if text not in ANSWER_SIGNAL_LIMITATIONS
    ]
    return out


def test_the_cluster_option_leaves_every_other_report_byte_identical():
    # Digests and the interval recorded on the pre-change harness (d154f85e):
    # the item-cluster bootstrap is additive and only T8 passes clusters. The
    # answer-signal arms (owner 2026-10-13) are additive too: stripped of what
    # they add, every report still hashes to the digest recorded before them.
    rows = _rich_stream()
    default = evaluate(rows, bootstrap_samples=50, seed=3)
    assert report_digest(_without_answer_signals(default)) == (
        "06818d9c2536a66097d342d9b7bccdd86a948951c3b3f056199f38296e05dd96")
    attempt_unit = evaluate(rows, bootstrap_samples=50, seed=3, bootstrap_unit="attempt")
    assert report_digest(_without_answer_signals(attempt_unit)) == (
        "06818d9c2536a66097d342d9b7bccdd86a948951c3b3f056199f38296e05dd96")
    assert report_digest(attempt_unit) == report_digest(default)
    families = evaluate(rows, arms=family_arms(), bootstrap_samples=50, seed=3)
    assert report_digest(_without_answer_signals(families)) == (
        "f2f30485ff38a9bd9c8d5360579a2e502542c60cb83fc289a5f08e452960c74e")
    values = np.random.default_rng(4).normal(size=37)
    recorded = {"n": 37, "mean": -0.07428148868918777,
                "ci95": [-0.40560308393180383, 0.26478138828214304]}
    assert paired_bootstrap(values, samples=200, seed=9) == recorded
    assert paired_bootstrap(values, samples=200, seed=9, clusters=None) == recorded


def test_cluster_bootstrap_is_at_least_as_wide_as_the_attempt_bootstrap_on_clustered_data():
    rng = np.random.default_rng(7)
    items = np.repeat(np.arange(30), 8)
    # A shared per-item effect: attempts on one item are not independent.
    values = rng.normal(0, .1, 30)[items] + rng.normal(0, .02, len(items))
    attempt = paired_bootstrap(values, samples=1000, seed=0)
    cluster = paired_bootstrap(values, samples=1000, seed=0, clusters=items)
    width = lambda result: result["ci95"][1] - result["ci95"][0]  # noqa: E731
    assert (cluster["n"], cluster["clusters"], cluster["degenerate"]) == (240, 30, None)
    assert cluster["mean"] == attempt["mean"]
    assert width(cluster) >= width(attempt)
    assert width(cluster) > 2 * width(attempt)  # the design effect, here about sqrt(8)
    # Singleton clusters in attempt order reproduce the attempt bootstrap.
    singletons = paired_bootstrap(values, samples=1000, seed=0, clusters=np.arange(len(values)))
    assert singletons["ci95"] == pytest.approx(attempt["ci95"], abs=1e-12)


def test_cluster_bootstrap_reports_no_interval_only_when_every_draw_is_the_same():
    # Review F2: no minimum cluster count. Only genuinely degenerate inputs
    # (no attempts, one cluster, equal cluster means) have no interval.
    one = paired_bootstrap([.1, .3, .2], samples=50, clusters=["i", "i", "i"])
    assert (one["clusters"], one["ci95"]) == (1, None)
    assert one["degenerate"] == "one cluster: every resample is the same"
    two = paired_bootstrap([.1, .2, .3, .4], samples=200, clusters=[0, 0, 1, 1])
    assert two["degenerate"] is None and two["ci95"] == pytest.approx([.15, .35])
    five = paired_bootstrap([.1, .2, .3, .4, .5], samples=50, clusters=[0, 1, 2, 3, 4])
    assert five["clusters"] == 5 and five["degenerate"] is None
    assert .1 <= five["ci95"][0] < five["ci95"][1] <= .5
    flat = paired_bootstrap([.1] * 12, samples=50, clusters=np.arange(12) // 2)
    assert flat["ci95"] is None and flat["degenerate"] == "zero variance across clusters"
    empty = paired_bootstrap([], clusters=[])
    assert (empty["mean"], empty["ci95"], empty["degenerate"]) == (None, None, "no attempts")
    with pytest.raises(ValueError, match="one label per difference"):
        paired_bootstrap([.1, .2], clusters=[0])



# -- the cluster-robust t interval (T8 pre-registration v4) --------------------

def test_cluster_t_interval_is_the_cr1_sandwich_with_items_minus_one_degrees_of_freedom():
    values = np.array([1., 2., 4., 3., 5., 7.])
    clusters = ["a", "a", "b", "c", "c", "c"]
    result = cluster_t_interval(values, clusters)
    mean = values.mean()
    # The sandwich for an intercept-only fit: residuals summed within each
    # cluster, then the CR1 factor G / (G - 1) (Stata's, with k = 1).
    sums = np.array([1 + 2 - 2 * mean, 4 - mean, 3 + 5 + 7 - 3 * mean])
    se = np.sqrt(3 / 2 * float(sums @ sums)) / 6
    assert (result["n"], result["clusters"], result["df"]) == (6, 3, 2)
    assert result["mean"] == pytest.approx(mean) and result["se"] == pytest.approx(se)
    assert result["t_critical"] == pytest.approx(4.30265272974946, abs=1e-9)
    assert result["ci95"] == pytest.approx([mean - 4.30265272974946 * se, mean + 4.30265272974946 * se])
    assert (result["method"], result["degenerate"]) == ("cluster_robust_t_cr1", None)


def test_cluster_t_interval_reduces_to_the_one_sample_t_interval():
    rng = np.random.default_rng(3)
    values = rng.normal(.02, .1, 24)
    # Singleton clusters: the ordinary t interval on attempts, df = n - 1.
    singletons = cluster_t_interval(values, np.arange(24))
    half = 2.06865761041905 * values.std(ddof=1) / np.sqrt(24)  # qt(.975, 23)
    assert singletons["ci95"] == pytest.approx([values.mean() - half, values.mean() + half])
    # Balanced clusters: the ordinary t interval on the cluster means, df = G - 1.
    balanced = cluster_t_interval(values, np.arange(24) // 4)
    means = values.reshape(6, 4).mean(axis=1)
    half = 2.57058183563631 * means.std(ddof=1) / np.sqrt(6)  # qt(.975, 5)
    assert balanced["ci95"] == pytest.approx([means.mean() - half, means.mean() + half])


def test_cluster_t_interval_has_no_cluster_minimum_only_degenerate_guards():
    two = cluster_t_interval([.1, .2, .3, .4], [0, 0, 1, 1])
    assert two["degenerate"] is None and two["df"] == 1
    assert two["ci95"] == pytest.approx([.25 - 12.7062047361747 * .1, .25 + 12.7062047361747 * .1])
    one = cluster_t_interval([.1, .3, .2], ["i", "i", "i"])
    assert (one["clusters"], one["ci95"], one["df"]) == (1, None, None)
    assert one["degenerate"] == "one cluster: no between-cluster variance (df = 0)"
    flat = cluster_t_interval([.1] * 12, np.arange(12) // 2)
    assert flat["ci95"] is None and flat["degenerate"] == "zero variance across clusters"
    empty = cluster_t_interval([], [])
    assert (empty["mean"], empty["ci95"], empty["degenerate"]) == (None, None, "no attempts")
    with pytest.raises(ValueError, match="one label per difference"):
        cluster_t_interval([.1, .2], [0])


def _clustered(rng, items):
    """T8-shaped differences: a shared effect per item, 1-4 attempts per item."""
    # Attempts per item as on the tracked linear_algebra fixture (37 items:
    # 25 seen once, 9 twice, 2 three times, 1 four times).
    sizes = rng.choice([1, 2, 3, 4], size=items, p=[25 / 37, 9 / 37, 2 / 37, 1 / 37])
    labels = np.repeat(np.arange(items), sizes)
    return rng.normal(0, .1, items)[labels] + rng.normal(0, .1, len(labels)), labels


def test_the_t_interval_covers_where_the_v3_percentile_item_bootstrap_does_not():
    # 400 replications per item count; the true mean gain is 0. v3's interval
    # is the harness's own percentile item bootstrap (B = 1000).
    replications, table = 400, {}
    for items in (3, 6, 20):
        rng = np.random.default_rng(items)
        hits = {"percentile": 0, "t": 0}
        for replication in range(replications):
            values, labels = _clustered(rng, items)
            for name, result in (
                ("percentile", paired_bootstrap(values, samples=1000, seed=replication, clusters=labels)),
                ("t", cluster_t_interval(values, labels)),
            ):
                hits[name] += result["ci95"][0] <= 0 <= result["ci95"][1]
        table[items] = {name: count / replications for name, count in hits.items()}
    print("95% coverage by item count:", table)
    for items, coverage in table.items():
        assert coverage["t"] >= .92, (items, coverage)  # nominal .95, MC sd about .011
        assert coverage["t"] >= coverage["percentile"], (items, coverage)
    assert table[3]["percentile"] < .80 and table[6]["percentile"] < .90
    assert table[3]["t"] - table[3]["percentile"] > .1


def _intervals(value):
    """Every bootstrap result (a dict with ``ci95``) anywhere in a report."""
    if isinstance(value, dict):
        if "ci95" in value:
            yield value
        for child in value.values():
            yield from _intervals(child)
    elif isinstance(value, list):
        for child in value:
            yield from _intervals(child)


def _rotating_items(n=24, items=4):
    """One LO, items served in rotation: two clean starts, then mixed outcomes."""
    return [AttemptRow(str(k), ItemFeatures(f"item{k % items}", "lo", f"2026-01-{k + 1:02}T00:00:00Z"),
                       1. if k < 2 else float(k % 3 != 0), 1.) for k in range(n)]


def test_the_item_unit_resamples_items_in_every_interval_and_the_manifest_says_so():
    # Review F1: a report run with bootstrap_unit="item" (the T8 report) has no
    # attempt-resampled interval left: report 1 metrics and splits, the
    # incumbent comparisons and report 2's miss rates all draw whole items.
    rows = _rotating_items()
    items = [k % 4 for k in range(len(rows))]
    report = evaluate(rows, arms=[Spy(), Spy("lo_general", p=.7)], bootstrap_samples=40,
                      bootstrap_unit="item")
    bootstrap = report["manifest"]["bootstrap"]
    assert {key: bootstrap[key] for key in ("unit", "paired", "samples", "seed")} == {
        "unit": "item", "paired": True, "samples": 40, "seed": 0}
    assert "each drawn item brings all its scored attempts" in bootstrap["resample"]
    assert "Wilson intervals are analytic" in bootstrap["scope"]
    intervals = list(_intervals(report))
    assert len(intervals) > 20 and all("clusters" in interval for interval in intervals)
    y = np.array([row.outcome for row in rows])
    loss = -y * np.log(.7) - (1 - y) * np.log1p(-.7)
    arms = report["report1"]["arms"]
    assert arms["lo_general"]["overall"]["log_loss"] == paired_bootstrap(
        loss, samples=40, seed=0, clusters=items)
    assert arms["lo_general"]["overall"]["log_loss"]["clusters"] == 4
    comparison = report["report1"]["comparisons"]["lo_general"]
    assert comparison["log_loss_improvement"] == paired_bootstrap(
        np.log(2) - loss, samples=40, seed=0, clusters=items)
    assert comparison["report2_miss_improvement"]["clusters"] == 4
    # Both arms fast-track the LO after two clean answers; every later
    # attempt is scored, and its miss rate resamples items too.
    later = range(2, len(rows))
    assert report["report2"]["arms"]["mastery_ekf"]["miss_rate"] == paired_bootstrap(
        [float(k % 3 == 0) for k in later], samples=40, seed=0, clusters=[items[k] for k in later])
    # The default is unchanged and says so.
    default = evaluate(rows, arms=[Spy(), Spy("lo_general", p=.7)], bootstrap_samples=40)
    assert default["manifest"]["bootstrap"] == {"unit": "attempt", "paired": True, "samples": 40,
                                                "seed": 0}
    assert not any("clusters" in interval for interval in _intervals(default))
    with pytest.raises(ValueError, match="bootstrap_unit"):
        evaluate(rows, arms=[Spy()], bootstrap_unit="lo")


def test_fast_track_requires_two_initial_clean_correct_and_scores_only_later():
    report = run([attempt(1), attempt(2), attempt(3, outcome=0)])
    fast = report["report2"]["arms"]["mastery_ekf"]
    assert fast["assumed_los"] == 1
    assert fast["later_attempts"] == fast["later_failures"] == 1
    assert fast["miss_rate"]["mean"] == 1
    assert fast["miss_rate_wilson_ci95"][0] > 0
    assert run([attempt(1)])["report2"]["arms"]["mastery_ekf"]["assumed_los"] == 0


@pytest.mark.parametrize("change", [
    {"outcome": 0}, {"hints_used": 1}, {"assisted": True}, {"help_before_work": True},
    {"effective_mass": 0}, {"features": ItemFeatures("i", "lo", "2026-01-01T00:00:00Z", cold=False)},
])
def test_unclean_initial_answer_never_fast_tracks(change):
    rows = [replace(attempt(1), **change), attempt(2), attempt(3)]
    assert run(rows)["report2"]["arms"]["mastery_ekf"]["assumed_los"] == 0


def test_confusion_blocks_but_curiosity_does_not():
    for kind, expected in [("prerequisite", 0), ("other", 1)]:
        rows = [SignalRow("s", "lo", "2025-12-31T00:00:00Z", kind),
                attempt(1), attempt(2), attempt(3)]
        assert run(rows)["report2"]["arms"]["mastery_ekf"]["assumed_los"] == expected


@pytest.mark.parametrize("signal", [
    SignalRow("s", "lo", "2025-12-31T00:00:00Z", "reader_confusion"),
    SignalRow("s", "lo", "2025-12-31T00:00:00Z", "hint", outcome=.3),
    SignalRow("s", "lo", "2025-12-31T00:00:00Z", "strategy"),
    SignalRow("s", "lo", "2025-12-31T00:00:00Z", "other", help_before_work=True),
    SignalRow("s", "lo", "2025-12-31T00:00:00Z", "other", leak_suspected=True),
])
def test_report2_shares_the_confusion_blocking_predicate(signal):
    """Review F6: the harness and confusion_blocks_fast_track agree on every signal."""
    from learnloop.field.signals import confusion_blocks_fast_track

    assert confusion_blocks_fast_track([signal], lo_id="lo", as_of="2026-01-03T00:00:00Z")
    rows = [signal, attempt(1), attempt(2), attempt(3)]
    # The spy predictor crosses the threshold; the blocking signal still wins.
    assert run(rows)["report2"]["arms"]["mastery_ekf"]["assumed_los"] == 0
    curiosity = replace(signal, signal_type="other", help_before_work=False, leak_suspected=False)
    assert not confusion_blocks_fast_track([curiosity], lo_id="lo", as_of="2026-01-03T00:00:00Z")
    assert run([curiosity, *rows[1:]])["report2"]["arms"]["mastery_ekf"]["assumed_los"] == 1


def test_ability_threshold_is_not_item_prediction_and_thin_default_is_conservative():
    # N(logit(.75)+.105,.01): tail probability ~.853; q=.8 passes, .9 fails.
    rows = [attempt(1), attempt(2), attempt(3)]
    report = run(rows, [Spy(p=.99, mean=log(3) + .105)])
    assert report["report2"]["arms"]["mastery_ekf"]["assumed_los"] == 0
    report = run(rows, [Spy(p=.1, mean=log(3) + .105)], fast_track_q=.8)
    assert report["report2"]["arms"]["mastery_ekf"]["assumed_los"] == 1


def test_switch_requires_both_splits_and_report2_never_activates():
    rows = [attempt(1), attempt(2), attempt(3)]
    report = run(rows, [Spy(), Spy("lo_general", .8)])
    assert report["recommendation"]["candidates"] == ["lo_general"]
    assert report["recommendation"]["activates"] is False
    report = run(rows[:2], [Spy(), Spy("lo_general", .8)])
    assert report["recommendation"]["decision"] == "keep_incumbent"
    report = run(rows, [Spy(), Spy("lo_general", .5)])
    assert report["recommendation"]["decision"] == "keep_incumbent"


def test_overall_improvement_without_first_improvement_cannot_recommend():
    class LaterOnly(Spy):
        def predict(self, features):
            return .5 if not self.seen else .9
    report = run([attempt(1), attempt(2), attempt(3)], [Spy(), LaterOnly("lo_general")])
    comparison = report["report1"]["comparisons"]["lo_general"]
    assert comparison["log_loss_improvement"]["mean"] > 0
    assert comparison["first_log_loss_improvement"]["mean"] == 0
    assert report["recommendation"]["decision"] == "keep_incumbent"


def test_auc_reliability_and_fractional_outcomes():
    rows = [attempt(1, outcome=0), attempt(2, outcome=.5), attempt(3)]
    m = run(rows)["report1"]["arms"]["mastery_ekf"]["overall"]
    assert m["auc"] == .5
    assert m["auc_binary_n"] == 2
    assert m["brier"]["mean"] == pytest.approx(1 / 6)
    assert sum(b["n"] for b in m["reliability"]) == 3


def test_llm_off_by_default_and_sweeps_available():
    from learnloop.field.predictors import registered_predictors
    names = registered_predictors()
    assert "llm_probability" not in names
    assert "lo_general+retrievability:beta=0.5" in names
    assert "lo_general+tutor_signals:scale=2" in names
    assert "lo_general+hints:step=0.1" in names
    report = evaluate([], bootstrap_samples=2)
    assert "llm_probability" not in report["report1"]["arms"]


def test_phase2_numeric_llm_probability_arm_is_retired():
    """Owner decision 2026-10-12: the V1-V3 arms replace Phase 2's numeric arm."""
    import importlib

    for module in ("learnloop.field.offline_llm", "learnloop.cli.field_llm"):
        with pytest.raises(ModuleNotFoundError):
            importlib.import_module(module)

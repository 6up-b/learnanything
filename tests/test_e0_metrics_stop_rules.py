"""E0 metrics (spec §5.2) and stop rules S1-S4 (spec §7), computed by code."""
from __future__ import annotations

import pytest

from learnloop.experiments.contextual_embeddings import metrics as M
from learnloop.experiments.contextual_embeddings import stop_rules as S
from learnloop.experiments.contextual_embeddings.report import assert_aggregate, render

from tests.e0_fakes import verified_prices  # noqa: F401 - the fixture below

#: Every metered pin priced as verified (E0 admission refuses unverified prices; fix round 4).
pytestmark = pytest.mark.usefixtures("verified_prices")


A = ("e", "s1", 0, 100)
B = ("e", "s2", 0, 50)
C = ("e", "s3", 0, 80)


def test_complete_evidence_needs_every_required_span_of_one_set():
    sets = [[A, B], [C]]  # (A AND B) OR C
    assert M.complete_evidence([A], sets) == 0.0
    assert M.complete_evidence([A, B], sets) == 1.0
    assert M.complete_evidence([C], sets) == 1.0
    assert M.complete_evidence([A], []) is None


def test_offsets_count_and_cuts_do_not_cover_the_rest():
    assert M.complete_evidence([("e", "s1", 0, 60), ("e", "s1", 60, 100)], [[A]]) == 1.0
    assert M.complete_evidence([("e", "s1", 0, 60)], [[A]]) == 0.0
    assert M.complete_evidence([("e", "s1", 10, 100)], [[A]]) == 0.0


def test_duplicates_never_earn_extra_recall_and_ties_take_the_first_set():
    assert M.support_recall([A, A, A], [[A, B]]) == 0.5
    assert M.support_recall([A], [[A, B], [A, C]]) == 0.5
    assert M.answer_recall([B], [A, B]) == 0.5


def test_ranking_metrics():
    labels = {"u1": "required", "u2": "helpful", "u3": "unrelated"}
    assert M.mrr(["u3", "u2"], labels) == 0.5
    assert M.ndcg(["u1", "u2"], labels) == pytest.approx(1.0)
    assert M.ndcg(["u3", "u2", "u1"], labels) < 1.0
    assert M.unknown_share(["u1", "u9"], labels) == 0.5


def test_cohen_kappa_and_confusion():
    categories = ("unrelated", "background", "helpful", "required")
    perfect = M.cohen_kappa([("required", "required"), ("unrelated", "unrelated")], categories)
    assert perfect["kappa"] == 1.0 and perfect["confusion"][3][3] == 1
    mixed = M.cohen_kappa([("required", "required"), ("required", "helpful"), ("unrelated", "unrelated"),
                           ("unrelated", "background")], categories)
    assert 0 < mixed["kappa"] < 1 and mixed["weighted_kappa"] > mixed["kappa"]


def test_paired_bootstrap_is_deterministic_and_clustered():
    rows = [{"family": f"f{i % 3}", "a": 0.0, "b": 1.0 if i % 2 else 0.0} for i in range(30)]
    first = M.paired_bootstrap(rows, a="a", b="b", resamples=2000)
    assert first == M.paired_bootstrap(rows, a="a", b="b", resamples=2000)
    assert first["clusters"] == 3 and first["exploratory"] is True
    assert first["ci95"][0] <= first["difference"] <= first["ci95"][1]
    assert M.paired_bootstrap([], a="a", b="b")["difference"] is None


def _interval(difference, low, high, n=40, clusters=6):
    return {"difference": difference, "macro_difference": difference, "ci95": [low, high], "n": n,
            "clusters": clusters, "exploratory": False}


def test_s1_stops_verdicts_and_blocks_the_rest():
    decisions = S.decide(
        s1_inputs={"kappa": 0.55, "unresolved_sets": 0, "extraction_failures": 0, "policy_failures": 0,
                   "arm_completion": {"R1": 1.0}},
        s2_inputs={"direct": {}, "latency_fits": {}}, s3_inputs={"context_gain": {}, "qwen_vs_hosted": None},
        s4_inputs={"finalist_vs_one_model": None, "answer_gain": None, "latency_ok": True, "independent_families": 9})
    assert decisions["S1"]["decision"] == "stop_verdicts"
    assert all(decisions[rule]["decision"] == "blocked_by_S1" for rule in ("S2", "S3", "S4"))
    assert decisions["production_adoption"] == "not_authorized_by_e0"
    incomplete = S.s1(kappa=0.8, unresolved_sets=0, extraction_failures=0, policy_failures=0,
                      arm_completion={"R4_grouped": 0.5, "R1": 1.0})
    assert incomplete["decision"] == "stop_verdicts" and "R4_grouped" in incomplete["reasons"][0]


def test_s2_superior_noninferior_and_inconclusive():
    result = S.s2({"D2": _interval(0.05, 0.01, 0.09), "D3": _interval(-0.01, -0.019, 0.02)},
                  latency_fits={"D2": True, "D3": True})
    assert result["arms"]["D2"]["verdict"] == "superior"
    assert result["arms"]["D3"]["verdict"] == "non_inferior"
    assert result["decision"] == "prefer_direct_reading_for_known_location:D2,D3"
    zero = S.s2({"D2": _interval(0.0, -0.05, 0.05)}, latency_fits={"D2": True})
    assert zero["arms"]["D2"]["verdict"] == "inconclusive"
    slow = S.s2({"D2": _interval(0.05, 0.01, 0.09)}, latency_fits={"D2": False})
    assert slow["decision"] == "no_direct_reading_preference"


def test_s3_context_gain_and_qwen_within_two_points():
    result = S.s3(context_gain={"R4": _interval(0.01, -0.02, 0.025), "R5": _interval(0.01, -0.06, 0.08)},
                  qwen_vs_hosted=_interval(0.01, -0.03, 0.05))
    assert result["families"]["R4"]["claim"].startswith("context adds less")
    assert result["families"]["R5"]["claim"] == "insufficient evidence to expand"
    assert result["decision"] == "no_local_escalation"
    ahead = S.s3(context_gain={"R4": _interval(0.08, 0.04, 0.12)}, qwen_vs_hosted=_interval(0.09, 0.05, 0.13))
    assert ahead["decision"] == "screen_supports_hosted_context"


def test_s4_needs_five_points_ci_answers_latency_and_power():
    good = dict(finalist_vs_one_model=_interval(0.07, 0.02, 0.12), answer_gain=_interval(0.03, -0.01, 0.07),
                latency_ok=True)
    assert S.s4(**good, independent_families=8)["decision"] == "consider_e1"
    assert S.s4(**good, independent_families=2)["decision"] == "defer_e1_underpowered"
    weak = {**good, "finalist_vs_one_model": _interval(0.06, -0.01, 0.12)}
    assert S.s4(**weak, independent_families=8)["decision"] == "no_e1"
    slow = {**good, "latency_ok": False}
    assert S.s4(**slow, independent_families=8)["decision"] == "no_e1"


def test_the_report_template_renders_incomplete_runs_and_refuses_private_fields():
    text = render({"status": "incomplete", "incomplete_reason": "budget: labels", "run_id": "e0_x",
                   "failures": [{"item": "R4_grouped", "kind": "budget", "reason": "cap", "denominator": 80}]})
    assert "Incomplete" in text and "R4_grouped" in text and "not_computed_no_results" in text
    assert "not production authorization" in text
    with pytest.raises(ValueError, match="private field"):
        assert_aggregate({"retrieval": {"R1": {"question": "secret question"}}})


def test_an_unpinned_reader_latency_budget_fails_closed():
    unknown = S.s2({"D2": _interval(0.05, 0.01, 0.09)}, latency_fits={"D2": None})
    assert unknown["decision"] == "no_direct_reading_preference" and unknown["arms"]["D2"]["latency_fits"] is None
    gate = S.s4(finalist_vs_one_model=_interval(0.07, 0.02, 0.12), answer_gain=_interval(0.03, -0.01, 0.07),
                latency_ok=None, independent_families=8)
    assert gate["decision"] == "no_e1" and "Reader latency budget not pinned" in gate["reasons"]
    assert M.latency_summary([1.0, 2.0, 3.0, 4.0])["p50"] == 2.5

"""AD2+AD3's simulation gates (spec_adaptive_difficulty_v1 §14; pre-registration in
docs/reviews/adaptive-difficulty-ad23.md §1.5-1.9).

Each test runs its gate's pre-registered scenarios (``learnloop.sim.ad_gates``, the
real model and selection rule on synthetic learners with known truth, fixed seeds)
and asserts the pre-registered pass conditions. Each failed before AD2+AD3 because
no model, selection rule or simulation existed.

**Gates that fail as pre-registered are marked ``xfail(strict=True)``** with the
reason: the review file reports them as failed gates for the owner (§3 there), and
a strict xfail turns red the day the gate starts passing, so the marker cannot
outlive the finding. Nothing was tuned to pass. Fakes only; no model is called.
"""

from __future__ import annotations

import pytest

from learnloop.adaptive_difficulty import priors as P
from learnloop.sim import ad_gates as G

FAILED_GATE = "pre-registered gate fails (docs/reviews/adaptive-difficulty-ad23.md §3): "


def _assert_pass(result: dict) -> None:
    failed = [name for name, ok in result["pass"].items() if not ok]
    assert not failed, f"failed conditions {failed}: {result}"


# -- AD2 ---------------------------------------------------------------------------------------


def test_confound_detected_under_monotone_schedule():
    """G-AD2-7: true growth, no feature effect, monotonically harder points: the dimensions the
    ladder raises are labelled "confounded" (``|r| > 0.6``)."""

    _assert_pass(G.g_ad2_7())


def test_feature_effects_recovered_under_overlap():
    """G-AD2-8: under ``ad_select_v1`` each identified ``β`` is within 2 posterior sd in >= 90% of
    200 seeds; directions aliased by design are reported prior-dependent, not recovered."""

    _assert_pass(G.g_ad2_8())


def test_help_and_reveal_are_censored_not_dropped():
    """G-AD2-14 (the estimand): help and reveals more often the lower the ability; AD's predicted
    unassisted success within 2 posterior sd in >= 90%; dropping assisted attempts overestimates."""

    _assert_pass(G.g_ad2_14())


@pytest.mark.xfail(strict=True, reason=FAILED_GATE + "band mode never engages (the learning rate's uncertainty "
                   "keeps the predictive sd near 0.95 > 0.74), and an oracle hits the band on only 0.33 of answers "
                   "16-30 with the pre-registered pools (< 0.35)")
def test_time_to_usable_one_cell():
    """G-AD2-18, one LO and one cell: band mode by the 15th answer for >= 80% of learners and a
    band-hit rate >= 0.35 over answers 16-30."""

    _assert_pass(G.g_ad2_18("one_cell"))


@pytest.mark.xfail(strict=True, reason=FAILED_GATE + "the wrong-prior band-hit rate is 0.09 (< 0.30); the oracle "
                   "bound is 0.33")
def test_time_to_usable_wrong_prior():
    """G-AD2-18, wrong prior (true subject level +-1.5): band-hit rate >= 0.30 over answers 16-30."""

    _assert_pass(G.g_ad2_18("wrong_prior"))


@pytest.mark.xfail(strict=True, reason=FAILED_GATE + "AD's band hits beat the incumbent's and the no-update "
                   "arm's, but its trivial-success rate (0.016) is above the incumbent's (0.0)")
def test_time_to_usable_plan_flow():
    """G-AD2-18, the plan's flow in the subject view: band hits at least the incumbent waypoint
    ladder's and AD-without-updates', trivial successes no more than the incumbent's."""

    _assert_pass(G.g_ad2_18("plan_flow"))


# -- AD3 ---------------------------------------------------------------------------------------

_G_AD3_6_PASS = {"0.75/0/0.25", "0.75/0.25/0.25", "0.75/0.5/0.25", "1.5/0/0", "1.5/0/0.25", "1.5/0.25/0.25",
                 "1.5/0.5/0", "1.5/0.5/0.25", "1.5/0.75/0.25", "2.25/0/0.25", "2.25/0.25/0.25", "2.25/0.5/0.25"}


@pytest.mark.parametrize("point", P.hyper_grid(), ids=lambda p: p.key())
def test_hyperparameters_learned_on_synthetic_vaults(request, point):
    """G-AD3-6 (synthetic part): on vaults generated at each grid point (25 seeds, 300
    first-surface answers over 12 LOs), at least half the posterior weight on the generating point
    and its grid neighbours in >= 80% of seeds."""

    if point.key() not in _G_AD3_6_PASS:
        request.applymarker(pytest.mark.xfail(strict=True, reason=FAILED_GATE + "the grid's edges are weakly "
                                              "identified from one learner's 300 answers"))
    _assert_pass(G.g_ad3_6(point))


@pytest.mark.xfail(strict=True, reason=FAILED_GATE + "first-attempt log loss on the mates is lower (interval "
                   "excludes 0) and the unrelated LO is not dragged, but band mode never engages on a mate in "
                   "either arm (the 2-fewer-answers condition)")
def test_related_topics_adapt_faster_practice_correct():
    """G-AD3-7, 15 answers on A then its mates, correct proposal: a mate engages band mode with at
    least 2 fewer own answers (median) and its first-attempt log loss is lower, interval excluding
    0; the unrelated LO is not dragged."""

    _assert_pass(G.g_ad3_7("practice", "correct"))


@pytest.mark.parametrize("proposal", ["noisy", "wrong"])
@pytest.mark.xfail(strict=True, reason=FAILED_GATE + "the unrelated LO's first attempt is dragged: +0.026 nats "
                   "(noisy) and +0.240 nats (wrong) against uniform sharing (> 0.02); band hits are not")
def test_unrelated_topics_not_dragged(proposal):
    """G-AD3-7, noisy and wrong proposals: cluster 2's A no worse than uniform sharing by more than
    0.02 nats on its first attempt nor 0.03 in band hits over its own 15 answers."""

    _assert_pass(G.g_ad3_7("practice", proposal))


def test_related_topics_after_reading():
    """G-AD3-7, 5 sections read on A (no answer there), correct proposal: the mates' first-attempt
    log loss is lower (amendment A10: the band-mode criterion needs answers on A), and the
    unrelated LO is not dragged."""

    _assert_pass(G.g_ad3_7("reading", "correct"))


@pytest.mark.xfail(strict=True, reason=FAILED_GATE + "the weight on chi_C = 0 reaches 0.5 within 100 first attempts "
                   "in 47% of seeds (< 80%), and the coupling flag fires in none (< 80%): the mixture discounts "
                   "the wrong coupling before the sequence can separate the arms")
def test_wrong_proposal_shrinks():
    """G-AD3-7, a wrong proposal on 210 LOs: weight on ``χ_C = 0`` reaches 0.5 within 100 first
    attempts in >= 80% of seeds, and the coupling flag fires within 200 in >= 80%."""

    _assert_pass(G.g_ad3_7_shrink("wrong"))


def test_correct_proposal_raises_no_coupling_flag():
    """G-AD3-7, the correct proposal on the same vault: the coupling flag fires in <= 5% of seeds."""

    _assert_pass(G.g_ad3_7_shrink("correct"))


@pytest.mark.xfail(strict=True, reason=FAILED_GATE + "with no true rise the reading kind's full effect stays at "
                   "0.24 (a section read every window is collinear with the practice increment); the rise and "
                   "the flag conditions hold")
def test_reading_raises_prediction_synthetic():
    """G-AD3-8 (synthetic part): with a true rise of 0.3 per section, first-attempt log loss after
    reading lower with reading on (interval excluding 0); with none, the full effect below 0.05 in
    >= 90% of seeds and the reading flag in <= 5%."""

    _assert_pass(G.g_ad3_8())


def test_auto_flags_fire_on_synthetic_logs():
    """G-AD3-9: every flag fires when its condition holds (>= 80%), each naming its switch, and
    none fires when nothing is worse in >= 95% of seeds."""

    result = G.g_ad3_9()
    _assert_pass(result)
    from learnloop.adaptive_difficulty import monitoring as MON

    assert result["recommends"] == MON.FLAG_SWITCHES


@pytest.mark.parametrize("floor", [0.10, 0.30])
@pytest.mark.xfail(strict=True, reason=FAILED_GATE + "5000 windows barely contract the dose curves (posterior sd "
                   "0.07 against a prior 0.10): the no-effect kind stays at its prior (coverage 0.73-0.78, full "
                   "effect below 0.05 in 5-7%)")
def test_reading_kind_effects_and_saturation_recovered(floor):
    """G-AD3-11, recovery: each kind's fitted curve within 2 posterior sd at doses 1-5 in >= 90%
    of seeds, ``n*`` within one event in >= 80%, the no-effect kind's full effect below 0.05."""

    _assert_pass(G.g_ad3_11("base", floor=floor))


@pytest.mark.xfail(strict=True, reason=FAILED_GATE + "the worked-example downturn is found in 0% of seeds "
                   "(< 80%)")
def test_reading_downturn_found():
    """G-AD3-11, the expertise-reversal scenario: the worked-example curve's maximum before dose 5
    in >= 80% of seeds."""

    _assert_pass(G.g_ad3_11("downturn"))


@pytest.mark.parametrize("floor", [0.10, 0.30])
def test_randomized_offers_unconfounded(floor):
    """G-AD3-11, confounding (no true effect, more reading after a failure): the randomized offer
    estimate's 95% interval covers 0 in 90-100% of seeds, and no line is labelled "tested by
    randomized offers" in more than 5% (amendment A3)."""

    _assert_pass(G.g_ad3_11("confounding", floor=floor))


@pytest.mark.xfail(strict=True, reason=FAILED_GATE + "with verdicts carrying no signal both lambda stay at "
                   "|mean| 0.07 with sd 0.12 (> 0.05, > 0.1); misses predicting cold failure are recovered")
def test_self_check_verdicts_learned_synthetic():
    """G-AD3-15 (6): no signal: |posterior mean| of both ``λ`` <= 0.05 with sd <= 0.1 in >= 90%;
    misses predicting cold failure: ``λ_missed`` negative with its 95% interval excluding 0 in >= 90%."""

    _assert_pass(G.g_ad3_15())

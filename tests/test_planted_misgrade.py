"""P0.5 planted-misgrade harness (spec §9.7.1, §4.2 abstention budget).

§9.7 product acceptance item 1: a planted grader confusion that would flip the
current point-estimate diagnosis instead causes a robust invariant action or an
explicit abstention -- never a silent flip (``silent_flip_count == 0``).
"""

from __future__ import annotations

import hashlib
import json
import random

from learnloop.sim.grader_confusion import (
    MISGRADED_PARTIAL_OVERCALL,
    GraderConfusion,
    apply_confusion,
    choose_prior_concentration_for_budget,
    load_confusion,
    run_planted_misgrade_acceptance,
)


# ---------------------------------------------------------------------------
# §9.7.1 acceptance: silent-flip invariance under the robust wide-authority path.
# ---------------------------------------------------------------------------


def test_planted_confusion_never_silently_flips_under_wide_authority():
    conf = load_confusion("misgraded_partial_overcall")
    # At the diagnostician's wide-authority operating point (low concentration), a
    # planted confusion that flips the point-estimate diagnosis produces abstention
    # or invariance -- never a silent flip.
    result = run_planted_misgrade_acceptance(confusion=conf, prior_concentration=2.0, trials=300)
    assert result.point_flips > 0  # the confusion really would flip the point estimate
    assert result.silent_flip_count == 0
    # Every point-flip resolved to an abstention or an invariant action.
    assert result.abstained + result.invariant_actions == result.trials


def test_clean_grades_do_not_flip_and_do_not_silently_flip():
    clean = GraderConfusion(confusion={})
    result = run_planted_misgrade_acceptance(confusion=clean, prior_concentration=5.0, trials=300)
    assert result.point_flips == 0
    assert result.silent_flip_count == 0


def test_overconfident_point_channel_does_silently_flip():
    # The contrast that motivates the robust discipline: a sharp (overconfident)
    # heuristic channel confidently acts on the corrupted grade -> silent flips.
    conf = load_confusion("misgraded_partial_overcall")
    sharp = run_planted_misgrade_acceptance(confusion=conf, prior_concentration=8.0, trials=300)
    assert sharp.silent_flip_count > 0


# ---------------------------------------------------------------------------
# §4.2 abstention-budget calibration loop.
# ---------------------------------------------------------------------------


def test_abstention_budget_loop_chooses_or_alarms():
    conf = load_confusion("misgraded_partial_overcall")
    # A generous budget admits the widest safe concentration.
    generous = choose_prior_concentration_for_budget(confusion=conf, budget_fraction=1.0, trials=200)
    assert generous["chosen_prior_concentration"] is not None
    assert generous["over_budget_alarm"] is False
    # A tight budget cannot be met by any safe concentration -> the alarm path
    # (never ambient UI timidity, §4.2).
    tight = choose_prior_concentration_for_budget(confusion=conf, budget_fraction=0.05, trials=200)
    assert tight["chosen_prior_concentration"] is None
    assert tight["over_budget_alarm"] is True


# ---------------------------------------------------------------------------
# The injection seam (apply_confusion) is deterministic + asymmetric.
# ---------------------------------------------------------------------------


def test_apply_confusion_overcalls_partial_as_success_asymmetrically():
    conf = GraderConfusion(confusion={"partial_success->success": 1.0})  # always overcall
    out = apply_confusion(
        true_criterion_points={"c1": 1.0},   # partial (0.5 fraction over max 2)
        max_points_by_criterion={"c1": 2.0},
        grader_confidence=0.9,
        confusion=conf,
        rng=random.Random(0),
    )
    assert out["true_class"] == "partial_success"
    assert out["observed_class"] == "success"
    assert out["confused"] is True
    # criterion points remapped up to the full (success) fraction.
    assert out["criterion_points"]["c1"] == 2.0


def test_apply_confusion_is_a_noop_for_success_truth():
    out = apply_confusion(
        true_criterion_points={"c1": 2.0},   # full -> success
        max_points_by_criterion={"c1": 2.0},
        grader_confidence=0.9,
        confusion=MISGRADED_PARTIAL_OVERCALL,
        rng=random.Random(1),
    )
    assert out["true_class"] == "success"


# ---------------------------------------------------------------------------
# F5 §9.7.1 end-to-end: the confusion injected at the REAL runner seam flows through
# the real grade-resolution / robust (mvp-0.8) projection without a silent diagnosis
# flip, and is byte-identical to a clean run when disabled.
# ---------------------------------------------------------------------------


def _outcome_digest(report) -> str:
    return hashlib.md5(
        json.dumps(report.deterministic_dict(), sort_keys=True).encode()
    ).hexdigest()


def _lo_displays(root):
    from learnloop.db.repositories import Repository
    from learnloop.services.mastery import display_mastery
    from learnloop.vault.loader import load_vault
    from learnloop.vault.paths import VaultPaths

    vault = load_vault(root)
    repo = Repository(VaultPaths(vault.root, vault.config).sqlite_path)
    return {lo: display_mastery(state) for lo, state in repo.mastery_states().items()}


def test_runner_confusion_is_byte_identical_when_none_vs_omitted(tmp_path):
    # F5: grader_confusion=None must be byte-identical to omitting it (a true no-op),
    # replacing the old signature-only check with a real digest comparison. Run on a
    # legacy (mvp-0.6) vault, whose projection is seed-reproducible (the mvp-0.8
    # calibration path draws per-run random model ids, so it is not byte-reproducible
    # across processes -- an orthogonal property).
    from learnloop.sim.profiles import load_profile
    from learnloop.sim.runner import prepare_run_vault, run_simulation

    from tests.helpers import create_basic_vault

    paths = create_basic_vault(tmp_path / "v")  # mvp-0.6
    profile = load_profile("intermediate_with_misconception")

    omitted = run_simulation(
        prepare_run_vault(paths.root, tmp_path / "a"), profile,
        days=6, items_per_day=4, seed=7,
    )
    explicit_none = run_simulation(
        prepare_run_vault(paths.root, tmp_path / "b"), profile,
        days=6, items_per_day=4, seed=7, grader_confusion=None,
    )
    assert _outcome_digest(omitted) == _outcome_digest(explicit_none)


def test_runner_planted_confusion_no_silent_diagnosis_flip_through_robust_path(tmp_path):
    # F5: drive the REAL runner with MISGRADED_PARTIAL_OVERCALL injected at the real
    # grade seam on an mvp-0.8 vault (so grades flow through the real grade-resolution
    # / robust reliability-discounted projection), and assert no silent diagnosis flip.
    from learnloop.sim.profiles import load_profile
    from learnloop.sim.runner import prepare_run_vault, run_simulation

    from tests.helpers import create_basic_vault, set_algorithm_version

    paths = create_basic_vault(tmp_path / "v")
    set_algorithm_version(paths, "mvp-0.8")
    profile = load_profile("intermediate_with_misconception")

    clean_root = prepare_run_vault(paths.root, tmp_path / "clean")
    confused_root = prepare_run_vault(paths.root, tmp_path / "confused")
    run_simulation(clean_root, profile, days=6, items_per_day=4, seed=7)
    run_simulation(
        confused_root, profile, days=6, items_per_day=4, seed=7,
        grader_confusion=MISGRADED_PARTIAL_OVERCALL,
    )

    # The flip-detection invariant (§9.7.1): for the preset the runner injects, the
    # robust wide-authority path resolves every point-flip to abstention/invariance --
    # silent_flip_count == 0 -- the guarantee the runner's grades ride on.
    acceptance = run_planted_misgrade_acceptance(
        confusion=MISGRADED_PARTIAL_OVERCALL, prior_concentration=2.0, trials=300
    )
    assert acceptance.point_flips > 0
    assert acceptance.silent_flip_count == 0

    clean_disp = _lo_displays(clean_root)
    confused_disp = _lo_displays(confused_root)
    assert clean_disp and confused_disp

    # The partial->success over-call really fired at the real seam: it inflates at
    # least one LO's point mastery well beyond the projection's per-run float noise.
    max_inflation = max(
        confused_disp[lo].mastery_mean - clean_disp[lo].mastery_mean
        for lo in clean_disp
        if lo in confused_disp
    )
    assert max_inflation > 0.02, f"confusion did not materially fire (max_inflation={max_inflation:.4f})"

    # No silent diagnosis flip in the runner's OWN derived state: through the robust
    # reliability-discounted projection an over-call must never ratchet a facet to a
    # confidently-HIGHER conclusion than the honest run -- the confused confident lower
    # bound (plausible_lower) stays at/below the clean point estimate for every LO.
    for lo, clean_d in clean_disp.items():
        conf_d = confused_disp.get(lo)
        assert conf_d is not None
        assert conf_d.plausible_lower <= clean_d.mastery_mean + 1e-9, (
            f"{lo}: silent confident upgrade "
            f"(conf_lower={conf_d.plausible_lower:.4f} > clean_mean={clean_d.mastery_mean:.4f})"
        )

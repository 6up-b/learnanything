# Phase 1 fix round, group FR-E: tests and the structure ratchet's parser

Rows T2, T3, T4, T6, T7 (= P8), T8. Tests, test helpers and `scripts/refactor_measures.py` only; no production code changed.
Each "mutation" below was a temporary edit of production code in the worktree, reverted with `git checkout src`.

## T6: distribution tests under the default pin

Mutation (missed today): `checks.day_seed` re-drawn until `uniform(seed, "slot:0") < 0.25`, a biased seed derivation. The
default pin replaces every production seed by a node-keyed one (one-to-one), so a test under the pin never sees production's
seeds. All 12 tests of `tests/test_ro5_checks.py` passed with the mutation. The same shape on
`lesson_suggestions.seed_for` (re-drawn until `uniform(seed, "component") < 0.1`, and separately `"show"`) passed all 20 tests
of the two TE1b files.

Marked `real_draws` (each now fails under its mutation):
- `tests/test_ro5_checks.py::test_the_draw_is_uniform_over_topics_across_dates` (fails under the check-seed mutation)
- `tests/test_teacher_te1b_review_fixes.py::test_logged_propensities_give_no_effect_when_targets_differ_and_the_card_does_nothing` (fails under the lesson-seed mutation, both variants)
- `tests/test_teacher_te1b_rereview_fixes.py::test_the_mixture_floor_draws_a_non_staged_target_with_its_exact_propensity` (fails under the "component" variant; the "show" variant leaves it passing, as that stage does not enter its assertions)

Audit of every other test that counts or compares draws over many seeds:
- `test_teacher_te1b_review_fixes.py::test_the_draw_logs_the_joint_target_and_arm_probability` (40 `LS.seed_for` draws): asserts per-draw identities (propensity = pi * arm), no frequency. Left under the pin.
- `test_ih5_successor.py` lines 166 (literal seeds `offer-{n}`), 141 and 237/266 (`mix.seed_for` fed to `recompute` and a rule-change replay): the claims are about the mix's maths or identities between two rules on the same seed, not the seed's spread. Left.
- `test_router_g3_propensity.py::test_the_two_stage_marginal_is_the_mixture` (20,000 draws): passes literal seeds `s{index}` straight to `mx.draw`, which no wrapper touches: already measures production's draw. Left.
- `test_ro5_landing.py` (400 follow-up decisions): sets `runtime.seed` itself (a test's own pin wins). Left.
- `test_data_capture_a6_delayed_pick.py` (300 `pick_with_receipt`), `test_learner_blindness_relax.py` (400 `PA.assign`), `test_ad3_dose_arm.py` / `test_ad_guard.py` (`S.seed_for` of the AD module): their seed derivations are not among `SEED_SOURCES`, so the pin does not reach them. Left.
- `test_ro5_codex_rereview.py`, `test_ro5_codex_review.py`, `test_ro5_checks.py` sims at lines 228/259: seeded `random.Random`, no production seed. Left.

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

## T8: the ratchet's import visitor and `TYPE_CHECKING`

`scripts/refactor_measures.py::_Imports.visit_If` skipped the body of every `if` whose unparsed condition contained the
text `TYPE_CHECKING`. Fail-first: `test_the_import_visitor_reads_the_body_of_not_type_checking_and_skips_its_else` and
`test_the_import_visitor_reads_both_branches_of_any_other_condition` (added to `tests/test_refactor_measures.py`, on small
source strings) fail against the old visitor (`if not TYPE_CHECKING:` and `TYPE_CHECKING or flag` imports vanished);
`test_the_import_visitor_skips_only_the_positive_type_checking_body` passes before and after (guards the behaviour kept).

Fix: `_type_checking_guard(test)` recognizes the bare `TYPE_CHECKING` and `typing.TYPE_CHECKING` structurally (True), its
`not` (False), anything else (None). Positive: visit the else only; negated: visit the body only; other: both branches.

Siblings checked: `visit_If` is the only visitor in the script that reads a condition; `grep TYPE_CHECKING src` shows every
use is the bare positive guard, so no import edge and no measure changed. Rerunning `tests/test_structure_ratchets.py --write`
with the new and with the old script gives the same file: two comment-line counts one lower than the golden
(`comment_lines_naming_a_stage_artifact` 2398 -> 2397, `content/pipeline/jobs.py` 33 -> 32), a drift already present at this tip
and unrelated to imports (the ratchet tolerates a fall). I did not write it: the golden is unchanged by this row.

## T7 / P8: identity pin C3 and the boundary the chooser assembles

`C3.boundary.*` hashed `_boundary()`, a dictionary the test wrote out, so a change to what `ObjectiveChooser.choose`
assembles (a field, an order, `BlockCandidate.log_row`'s fields) moved nothing. Mutation: a field added to `log_row` (reverted):
all 216 existing pins passed.

New pin `C3b.chooser` (new site C3b in `tests/identity_pins_helpers.py`): `_chooser_boundary()` builds a new vault at the head,
a fake runtime with both models ready, an `ObjectiveChooser(start_only=True)` with `_start_objective` stubbed (the job it
starts is not what is pinned), and drives `choose` on a fixed `PlanState` and two fixed candidates; the dictionary the
chooser hands to `_hash` is captured, and the pin holds it, its key and `numeric_seed` of it. With the same mutation only
`test_identity_pin[C3b.chooser]` fails. The existing `C3.*` values are untouched (the golden diff is the one added line); I only
corrected `_boundary`'s docstring and the module docstring, which said the hand-written literal was what production builds.
`test_identity_pin` is already `real_draws`, so `numeric_seed` is production's.
`as_of` is null in this vault (no attempts), `plan_id` is the state's own, so nothing volatile is in the identity.

Not covered: the preference and miss-cause marks (`_preference_mark`, `_miss_cause_mark`) are empty at this config; the pin
does not exercise them.

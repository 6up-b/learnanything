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

## T4: `test_stuck_prompt_replay` and the other files the mechanical re-tag touched

Commit 9006b0f9fb took `test_historical_dont_know_rows_replay_unchanged_under_the_successor` to a head-to-head check (its
`set_algorithm_version(paths, "mvp-0.13")` was removed) and left no test of replay at a tag other than the one that wrote the rows.

Mutation (missed by every test in the old file, 4 passed): `replay`'s reconstructed draft ignores the stored flag
(`declared_stuck=False` where `attempts.py` rebuilds the draft from the ledger row). The stuck answer's coverage trace then
re-derives `response_engagement_factor` 0.5 (a blank) instead of 1.0 (an engaged empty "I'm stuck" answer). A second mutation,
`declared_stuck=... and stuck_prompt_active(vault)`, is caught by the old kill-switch test, as it should be, and by the new test.

New tests in `tests/test_stuck_prompt_replay.py`:
- `test_a_recorded_stuck_answer_replays_as_stuck_under_a_tag_that_does_not_offer_the_prompt`: records two stuck answers (one empty)
  at the head, moves the vault to `mvp-0.12` (not in `STUCK_PROMPT_VERSIONS`), rebuilds twice; the stored flags, the stuck
  read-back, the field rows and each attempt's recorded engagement factor are what the live grade wrote. Fails under the first
  mutation (and under dropping `not replay and` from the validation, which the old file also caught).
- `test_an_attempt_an_older_tag_wrote_replays_with_no_stuck_declaration_at_the_head`: rows written at `mvp-0.12` with `declared_stuck = 0`,
  rebuilt at the head where the prompt is offered, stay ordinary attempts (no stuck row appears, the ledger rows are byte-equal).
- `test_historical_dont_know_rows_replay_unchanged_under_the_successor` restored to its transition: the rows are written at
  `mvp-0.12`, rebuilt at the head. It no longer compares whole derived snapshots across tags (they differ by the version stamp
  and by every change between the tags); it compares the attempt rows, the field rows of the two `dont_know` attempts and
  the configured 0.7 mass. I did not find a mutation specific to this one that the head-to-head version missed.

Audit of the other files 9006b0f9fb touched (56 files; list the test names and docstrings that say replay, upgrade, historical,
legacy, "below the tag", "written at", and read the old version argument in the diff):
- `tests/test_followup_reserved_only.py::test_the_mint_and_batch_paths_refuse_a_reserved_question_at_the_tag_only`: LOSS, and
  a weakness older than the re-tag. Its "below" vault was a different vault (without the reserved question), so it passed
  with or without the tag gate; the re-tag made it the head. Mutation `generate_and_serve_on` ignoring the version: the test
  passed. Now the same vault with only its tag lowered (`BELOW_THE_TAG = "mvp-0.44"`, asserted outside
  `FOLLOWUP_SERVE_VERSIONS`); it fails under the mutation.
- `test_field_split_outcomes::test_blind_grades_diagnoses_and_regrades_keep_the_epoch_contract`: the joint twin at mvp-0.9 became a head vault. Its subject is blind-versus-joint grading, set by `split_enabled`, not the tag. Fine (the first line `split_vault(... version=LATEST)` is also a joint-vs-split pair at the same tag, as before).
- `test_stuck_prompt_replay.py` (the three above); `test_hint_telemetry::test_an_empty_stuck_answer_attaches_the_rows_too` (0.13 to head): subject is the stuck answer's telemetry rows. Fine.
- `test_recurrence_benchmarks` (b3 replays), `test_observation_ledger_bulk` (p0 replays bulk load), `test_projection_evidence_polarity`, `test_required_method_*` (`gated_successor`, replay under the frozen field): the tag was a setup choice (the first tag where a feature exists); each asserts the feature's own behaviour, which the head has. Fine.
- The `_mvp07_vault`-style helpers (`test_characterization_*`, `test_conjunctive_instruments`, `test_scoreboard`, `test_contract_frontier_coverage`, `test_coverage_denominator_boundary`, `test_discrimination_profiles`, `test_error_hunt_items`, `test_laddered_stems`, `test_contrast_pairs`, `test_km5_sim_gates`, `test_causal_attribution_exhibit`, `capability_residual_helpers`, `identifiability_doctor_helpers`): "legacy" in their text means a vault without blueprints or targets, not an older tag. The helper names `_mvp07_vault`, and docstrings saying "mvp-0.7", are now wrong. I did not rename them (a rename across 13 files is outside this row).
- `test_ro4_trace_report`, `test_ro5_codex_review`, `test_rofu_ad_latent`, `test_instruct_handoff_ih1`, `test_router_offer_log`, `test_router_why_copy`, `test_sidecar_close_cancels_jobs`, `test_planted_misgrade`, `test_grading_cli`, `test_tier1_decider`, `test_hypothesis_marks`, `test_daily_plan_composition`, `test_learner_protection_predicates`, `test_placement_*`, `test_reader_cues`, `test_intent_fix_round5/7`, `test_teacher_*`, `test_mobile_v3_codex_review`: tag was setup for a chooser or feature; none names a below-the-tag, replay or upgrade subject in its assertions. Read from the diff and test names only; I did not run each against a tag-dependent mutation.

## T3: production's refinement controller

Mutations in `objective_chooser.py` (the `keep_going` the job hands `run_numeric`), each reverted:
(a) `lambda: False`; (b) the LLM-outstanding clause dropped (`LLM in entry.events and runtime.clock() < entry.deadline`).
(b) against `test_ro4_codex_review`, `test_rofu_carried`, `test_ih_numeric_seed` (the files that run the threaded job with a gated
LLM): 29 passed. By construction the default pin replaces `keep_going` for every test not marked `real_draws`, and
`test_rospeed2_connections` supplies its own.

New `tests/test_objective_refinement.py` (module-wide `real_draws`): the real job on a threaded `RouterRuntime`, `FakeLLM(gate=...)`
blocking until released, a runtime clock (real monotonic plus an offset the test moves). `V.evaluate` is wrapped to read each
completed batch from `on_complete` and to hold the job at batch 2 (so the next `keep_going()` call happens at a point the test controls).
- `test_refinement_runs_another_batch_while_the_llm_is_out_and_stops_when_it_answers`: batches 8 then 16 complete with the LLM
  gate closed; the gate opens, the job is released, the final evaluation is the 16-draw batch and no third batch follows. Fails
  under (a) (never reaches batch 2) and (b) (a third batch).
- `test_refinement_stops_at_the_deadline_with_the_llm_still_out`: the clock moves past the entry's deadline at batch 2; the job stops
  at 16 draws with the LLM still out. Fails under (a). It passes if only the deadline clause of `keep_going` is removed:
  `V.evaluate` has its own `clock() > deadline` check on the same line, so that clause is redundant and not observable
  from outside; the test pins the behaviour (stops at the deadline), not that clause.
Assertions use bounded waits (60 s) on events and a 0.2 s settle for "no further batch"; 3 consecutive runs passed (4.3 s each).
No production seam was missing. `advance(env, serve=False)` with `check_rate = "off"` starts the first boundary's job (a check block otherwise precedes it).

## T2: the phone's stop-and-handoff journeys on the objective path

New `tests/test_mobile_v2_objective_stop.py`: the three F7 journeys of `tests/test_mobile_v2_rereview_fixes.py` (the pending stop
offered on the phone, *Keep going* overriding it in place, *Done for today* leaving the held work to the desktop) on a vault whose
Today is chosen by the objective (`plan_toml` empty, not `STAGED_ROUTER`). The staged file is untouched.

Determinism, and what varied. Without help the first journey failed 3 of 3: the objective's own stop coin drew a stop at the first
boundary (`'done'` with the objective's stop reason instead of the forced one). The file takes `never_stop_or_offer_draws(monkeypatch,
fixed_numeric_seed=True)` (the helper made for a test that needs the same block order every run), so the only stop is the one forced
at `engine.decide`, as in the staged journeys, and the numeric policy's Monte Carlo has one seed. The boundary prefetch is waited for:
`_settle()` joins the `learnloop-router-*` / `learnloop-objective-*` threads before each phone request and after the last answer.
With those, 50 consecutive runs of the three journeys passed (150 of 150). So D-28's block-order variation did not show up in these
journeys with the numeric seed fixed (it is the `fixed_numeric_seed` that removed it; I did not find what else varied and I did not try without it
beyond the first failure above, which was the stop coin). The phone's `plan_prefetch` needs a model to start a job, so a fixture
installs a fake-model runtime as the process's default (`router_runtime._DEFAULT`).

New assertion the staged frame cannot make: at the pending stop, `plan_prefetch` answers `reason == "stop_pending"`, not started.
Mutation: the `stop_pending` return removed from `engine.prefetch_boundary` (reverted): all 7 staged journeys passed; the objective
journey fails (`'started' == 'stop_pending'`).

Not covered: the objective chooser's own stop (as opposed to a stop forced at `decide`) reaching a pending stop on the phone;
and a stop pending while the prefetch's models answer late. After the final change (the prefetch call and runtime fixture) the
journeys passed 12 consecutive runs (the loop was cut by a timeout), not 50.

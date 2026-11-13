FINDINGS

1. HIGH — Recovery lost its tests for misleading completion receipts

Where: tests/test_upgrades.py:539 and tests/test_rebuild_equivalence_review.py:275. Deletion: d8678ad0bd; replacement: 6eeac48ee1.

Before, recovery tests supplied a startup-projection receipt or a partial rebuild at the target tag and required recovery to finish the whole-vault activation. Those tests were deleted. The replacement checks absence of a receipt and presence of a valid receipt, but never a wrong-scope receipt.

The distinction remains live: src/learnloop/ops/upgrades.py:263 skips activation when committed() succeeds; its implementation delegates at :89 to src/learnloop/db/repositories.py:7410, whose query requires scope = 'all'.

Regression missed: accepting any target-tag receipt as completion, leaving incompletely rebuilt learner state in service.

Smallest restoration: parameterize the replacement recovery test with canonical_projection_startup and per-LO receipts, asserting that activation still runs and repairs state.

Confidence: certain coverage deletion; the proposed regression was not executed.

2. HIGH — Phone stop-and-handoff checks now exclude objective boundary prefetch

Where: tests/mobile_v2_plan_helpers.py:45 and :55; tests/test_mobile_v2_rereview_fixes.py:158, :172 and :214. Commit: bc27fa5b20.

The shared fixture now forces router.mode = "staged". The stop-offer, Keep going, and desktop-handoff assertions survive, but only on that fallback. Production defaults to mixture at src/learnloop/config/schema.py:4043. Staging bypasses ObjectiveChooser through src/learnloop/daily_plan/policy.py:96 and disables objective prefetch at :150.

The cited replacement coverage, tests/test_ih3_phone_host.py:39, defaults to draw.never_stop = True. It does not replace these pending-stop journeys.

Regression missed: objective prefetch consuming, duplicating or losing the stop drawn beyond desktop-held work. The live pending-stop handling remains at src/learnloop/daily_plan/engine.py:5404 and :5418. This is a coverage gap beyond D-28’s recorded ordering instability.

Smallest restoration: run the F7 stop/handoff journey in objective mode with controlled job events and a forced objective stop.

Confidence: likely; no objective-mode reproduction was run.

3. HIGH — The production refinement controller is bypassed even by the dedicated refinement proof

Where: tests/pinned_draws.py:142; tests/test_rospeed2_connections.py:332 and :364. Commit: 3ec84cfcff.

T3 overwrites every unmarked run_numeric call’s keep_going argument with None. Production’s controller—continue while the LLM is outstanding and the deadline remains—is supplied at src/learnloop/daily_plan/objective_chooser.py:905.

The marked refinement test does exercise multiple batches, but supplies its own keep_going=lambda: refine. Its draw-count assertions concern those replays, not the live job’s controller.

Regression missed: the production controller permanently returning false, so serving silently stops refining after the first batch. The default hook erases that distinction, while the dedicated proof replaces the controller.

Smallest restoration: add a real_draws integration case with a blocked fake LLM and deterministic clock, asserting that the actual job completes another batch and stops when the event or deadline changes.

Confidence: likely; controller mutation and integration execution were not performed.

4. MEDIUM — Historical replay became a head-to-head idempotence test

Where: tests/test_stuck_prompt_replay.py:121–160. Commit: 9006b0f9fb.

Previously this created dont_know history at mvp-0.12, changed to mvp-0.13, and compared replayed state. It now creates history at LATEST_ALGORITHM_VERSION (:126), removes the version transition, reloads the same configuration (:143), and compares another replay. The old version normalization at :146 no longer establishes a transition.

Historical interpretation remains live: src/learnloop/attempts/attempts.py:1451 reconstructs persisted declarations, explicitly preserving the recorded stuck flag rather than consulting today’s switch.

Regression missed: older persisted dont_know rows acquiring different evidence or interpretation when replayed by current code. Same-version idempotence does not check that.

Smallest restoration: seed representative historical ledger rows with their original provenance and assert their expected replayed meaning at the head.

Confidence: certain loss of historical coverage; historical fixtures were not executed.

5. MEDIUM — The mixed-model guard test no longer tests rejection

Where: tests/test_recurrence_commands.py:375–394. Commit: d8678ad0bd.

Before, after model A judged everything and configured model B judged only three negatives, the test asserted rejection and the exact number of missing B judgments. Those assertions disappeared with the upgrade call.

Now its only final check calls guard_status(repository) without judge_model and asserts missing == []. It never asks the live model-specific branch at src/learnloop/diagnosis/recurrence/guard.py:495 to reject the incomplete B set.

Regression missed: allowing a partially represented configured model to borrow the remaining verdicts from another model. The surviving zero-verdict tests do not cover this mixed case.

Smallest restoration: call guard_status(repository, judge_model="deepseek-v4-pro@high"), assert passed is false, and assert the exact remaining case IDs.

Confidence: certain; no mutation test was run.

6. MEDIUM — Distribution tests measure substituted seeds

Where: tests/test_ro5_checks.py:47 and tests/test_teacher_te1b_review_fixes.py:124. Commits: 3ec84cfcff and 3a3383a9d4.

These tests still measure topic frequencies and inverse-propensity agreement across thousands of seeds, but neither has real_draws. T3 replaces each distinct production seed with an ordinal-derived hash at tests/pinned_draws.py:60. The synthetic check dates explicitly enter that replacement branch at :85.

Before, the assertions exercised production seed derivation composed with production sampling. Now they exercise the replacement derivation composed with sampling. Production checks consume day_seed directly at src/learnloop/router_objective/checks.py:138.

Regression missed: a biased seed derivation that still produces distinct seeds; the replacement discards those values and can restore the expected distribution.

Smallest restoration: mark these statistical tests real_draws and audit the other spread/propensity tests for the same omission.

Confidence: certain substitution; no biased-derivation mutation was executed.

7. MEDIUM — C3 pins a reconstructed identity, not the serving identity

Where: tests/identity_pins_helpers.py:820–843; tests/test_identity_pins.py:83. Commit: e1884dd311.

The boundary pin constructs its own dictionary, then calls production hashing and numeric_seed. Production assembles the actual boundary separately at src/learnloop/daily_plan/objective_chooser.py:1422, including rounded state, candidate log rows, preference marks and miss-cause marks.

Regression missed: changing production boundary assembly—such as its rounding, support serialization or included fields—can change cache keys and numeric seeds without changing the pinned dictionary. The golden remains green. The existing speed-switch comparison derives its baseline from the current production identity, so it does not supply a fixed historical pin for this gap.

Smallest restoration: capture the identity emitted by ObjectiveChooser on fixed inputs, or extract one production boundary builder and pin its output.

Confidence: certain structural gap; no identity mutation was run.

8. MEDIUM — The structure ratchet discards runtime imports containing TYPE_CHECKING

Where: tests/test_structure_ratchets.py:132; scripts/refactor_measures.py:469. Commits: ae19881e5d and 9042ca91f3.

The import visitor treats every condition whose unparsed text contains TYPE_CHECKING as false and visits only its else branch.

For example, imports inside “if not TYPE_CHECKING:” execute at runtime but disappear from the measured graph. The same problem affects compound conditions that can be true at runtime.

Regression missed: new import edges or cycles can increase without increasing the ratcheted measurements.

Smallest restoration: recognize the specific positive TYPE_CHECKING guard structurally; handle negation correctly and conservatively traverse unresolved compound conditions.

Confidence: certain parser loophole; I found no current production occurrence establishing an existing miscount and ran no parser mutation.

CHECKED AND FOUND SOUND

D-20’s shared frozen clock retains the compared rows rather than filtering away discrepancies.
D-27’s facet_uncertainty carve-out matches the incumbent-state exception; direct AD reads remain denied as an unclassified table.
The inspected identity-golden changes add pins or identify the deliberate mvp-0.59 changes; no unexplained replacement of an existing digest was found.
The structure-golden increases identify the added modules; the D3 reduction lowers the recorded limits.
The known D-17 strict xfail remains explicit rather than silently passing.
The below-floor blanket allowance has teardown reset; registered roots intentionally persist, so that persistence alone is not a newly discovered leak.
T3’s identity-pin tests explicitly use real_draws, and its check-day mapping preserves relative date offsets.

COULD NOT CHECK

No tests, application code, mutation probes, subprocesses or network operations were run, and no files were written.

Runtime verification remains necessary for thread-dependent seed assignment, shared-fixture ordering across marked and unmarked tests, spawned-process pin propagation, allowance teardown ordering, and the objective phone/refinement scenarios above. The proposed missed regressions are static coverage findings, not reproduced production failures.
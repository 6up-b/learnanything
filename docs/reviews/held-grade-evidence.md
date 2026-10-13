# Held grades are no evidence: one predicate for every reader

Stage: `held-grade-evidence`, on `merge/proof-alternatives` (worktree
`learnanything-merge`, base `a9a030bf`: main `3192d0c9` plus the proofs route
check as `mvp-0.17`).

Input: an independent Codex verification of the proof-alternatives fixes (job
`20261013-051715-m5ErbP`, read-only, at `ad2cf77d`). It reopened F1 and F9 of
the stage's re-review and found eleven defects, three High. The common cause:
a grade the route check holds for review (nothing assessed and nothing
validated, re-review F9) was a flag on the blind record, and each reader
decided for itself whether an attempt counts. Some read the hold, some read
PF-c's nothing-assessed state, and most read the attempt's `correctness` or
`rubric_score`, which for a held grade is the grader's own provisional score.

All eleven reproduced (fail-first, below) and were fixed. None was rejected.
No paid call was made.

## The predicate

**One rule** (`outcome_contract.grade_is_held`):

> An attempt's grade is held for review when its LATEST blind grade record
> holds it (`outcome_contract.grade_held_for_review`) AND nothing in its
> current (non-superseded) grading evidence is assessed.

- The record half is the merge's: `status = checked`, `held_for_review`, a
  gate version after `proof-route-check-v2`. It now also accepts a hold that a
  failed regrade check kept (`hold_kept_from`, F2).
- The evidence half makes releases real. A regrade that validates the route
  writes a record without the hold. An owner adjudication (Ruling A's
  evidence revision) writes assessed tier-4 rows over the held ones. Either
  one releases the hold at once, in every reader, not only on the next replay
  (F5).
- A held grade is ⊂ PF-c's nothing-assessed state, so every reader that
  already excluded nothing-assessed evidence (the field, the projection,
  placement's unassessed answers, cold verification, pinned-probe features)
  excludes it too. The new readers are the ones that read the attempt's
  score or correctness directly: for a PF-c nothing-assessed answer that
  score is a verified 4/4 ("correct for scheduling"), for a held one it is a
  provisional guess.

**Two evaluations, one function.** Every reader reads one of them:

| Where | What | Used by |
|---|---|---|
| In flight | `attempts._compute_resolved_grade_application` evaluates `grade_is_held(record_held=…, anything_assessed=bool(assessed criterion points))` for the grade being applied and puts it on `AttemptApplication.grade_held` | the attempt step's own readers: FSRS, surprise, error events, item quality, auto-resolution, the certification cold probe, the probe episode. The live door writes the blind record AFTER this step, so the ledger cannot answer yet |
| Ledger | `learnloop.held_grades.held_for_review_attempts(connection, ids)` (and `held_attempt_ids`, `attempt_grade_held`, `mark_held_attempts`) | every reader of a persisted attempt |

- `learnloop.held_grades` is a new leaf module. It imports only
  `outcome_contract`, so learner, placement and scheduling code read it
  without a new edge into `substrate`. The frozen-cycles import contract
  refused `learner -> substrate` and `placement -> substrate`.
- `substrate.canonical_projection` re-exports it under the merge's name
  (`held_for_review_attempts`), and a test pins that they are one function.
- PF-c's row stamp (`UNVERIFIED_CRITERION_BLOCK`, the interpretation key,
  `unassessed_evidence_row`) moved, unchanged, into the dependency-free
  `outcome_contract`, which the predicate reads. `canonical_projection`
  re-exports every name, so no importer changed.
- `mark_held_attempts` tags rows with `HELD_ROW_KEY` (`grade_held_for_review`).
  It is for readers that keep a held attempt as an exposure (familiarity, the
  item's last-attempt time) but never read its score.
- The ledger query reads only each attempt's latest blind record, prefiltered
  on `"held_for_review":true` with the `(attempt_id, created_at, id)` index.
  An empty id list reads nothing.

## Findings

| ID | Severity | Title | Fix | Tests (`tests/test_held_grade_evidence.py`) |
|---|---|---|---|---|
| F1 | High | A blank criterion id bypasses whole-answer rescoping | The gate reads only this rubric's criterion ids (`proof_check._criteria_of`): a blank, whitespace or unknown id (or a criterion `target_ref` with none) names no criterion, as validation will keep it, so an unlocated attribution is rescoped like any whole-answer claim. After validation, `revalidated_support` recomputes `assessed_shortfall` from the persisted record (live door and regrade) | `test_f1_a_blank_or_unknown_criterion_id_names_no_criterion[blank, whitespace, unknown]`, `test_f1_live_a_blank_criterion_id_keeps_no_shortfall_and_queues_no_diagnosis`, `test_f1_the_shortfall_is_recomputed_over_the_validated_grade` |
| F2 | High | A checker failure during regrade releases the hold unvalidated | A regrade of a held attempt (the ledger predicate) whose check did not run (`status = unavailable`: provider error, invalid output, no client, no reading) keeps the hold (`proof_check.kept_hold_run`): every criterion unassessed, the grader's own score, attributions rescoped, `hold_kept_from` = the replaced record | `test_f2_a_regrade_whose_check_fails_keeps_the_hold[regrade, clarification]` |
| F3 | High | Certification cold probes score held attempts as ground truth | The attempt step passes its in-flight hold; a held probe abstains: `indeterminate`, `grade_unavailable`, no correctness, out of the denominator | `test_f3_a_held_cold_probe_abstains_from_certification_validation[held_zero, held_full]` |
| F4 | Medium | A validating regrade supersedes tier 1 only, leaving stale tier-3 unassessed rows | A regrade of a held attempt (release or kept hold) supersedes tiers 1 and 3, as the clarification regrade already did | `test_f4_a_validating_regrade_leaves_no_stale_unassessed_row` |
| F5 | Medium | Owner adjudication does not release the post-attempt suppression | `post_attempt` reads the ledger predicate, whose evidence half sees the adjudication's assessed rows | `test_f5_an_adjudication_releases_the_follow_up_suppression` |
| F6 | Medium | Dataset `R_cold` (and `R_next`) export held scores as observed | `outcome_records` reads the predicate: a held outcome is status `grade_held_for_review` with no value, in `R_next` (plus the retention exclusion) and `R_cold` | `test_f6_the_dataset_exports_no_held_score_as_observed` |
| F7 | Medium | Exam calibration treats held correctness as observed | Held attempts leave the item curve, the facet pairs, the duel and the confidence denominator | `test_f7_exam_calibration_reads_no_held_outcome` |
| F8 | Medium | `review_log` reconstructs a review that never happened for the FSRS fitter | `reconstruct_review_log` marks held observations `applies_review = False`; `review_log_loss` neither scores nor applies them (the elapsed time still counts from them, as on the live schedule) | `test_f8_the_fsrs_fitter_never_fits_a_review_that_never_happened` |
| F9 | Medium | Held attempts build a same-item failure streak | The streak skips a held attempt: neither a failure nor the success that ends a streak | `test_f9_f10_held_grades_build_no_failure_streak_and_move_no_item_quality` |
| F10 | Medium | Held attempts move item-quality suspicion | A held grade writes no quality row, and an earlier held attempt is no recent failure | same |
| F11 | Medium | A held probe answer records its observation from the grader's score | The answered presentation is consumed and recorded with no outcome (`observed_outcome = None`), no posterior move, `updates_belief = false`, not qualifying, no dual-written probe grade; `episode_posterior` skips held attempts in both channels (an incidental held attempt too) | `test_f11_a_held_probe_answer_moves_no_episode_posterior` |

Also new, beside the findings:

- A held grade writes **no error event and no error type**. Its
  attributions stay on the blind record and in the feedback. An active
  error from a grade nothing validated would steer the scheduler's repair
  boost, probe selection and the severity of later answers. It is also how
  F9's streak and F10's quality read a held attempt as a failure. A grade
  with a located whole-answer claim and every criterion unlocated can be
  held with an attribution still in force.
- A held grade is **not a clean attempt** for error-event auto-resolution
  (`_auto_resolve_clean_error_events`; a held grade can carry a provisional
  4/4 by rounding), and an earlier held attempt is not counted as clean.
- A held grade **needs no diagnosis** (`split.live.needs_diagnosis`).
  Before, only `assessed_shortfall = False` kept it out.

### Reproduction first

`tests/test_held_grade_evidence.py` was run against the base source
(`git archive a9a030bf src migrations calibration_bundles`, put ahead of the
editable install with `-o pythonpath=`). The result was **28 failed, 8
passed** (log: `fixtures-local/held-grade-evidence/failfirst-at-a9a030bf.log`):

- F1: the stored attribution stayed `valid_measurement`, and the live
  support kept `assessed_shortfall = True`.
- F2: the regrade's record had no hold (`KeyError: 'held_for_review'`),
  through both doors.
- F3: the held 0/4 probe was `failed`, and the held 4/4 was `held`.
- F4: four live rows (`['result', 'result', 'setup', 'setup']`).
- F5: the predicate still held the attempt after the adjudication.
- F6: `R_next` was `observed`.
- F7: one item outcome.
- F8: `applies_review` was True.
- F9: the streak was 2.
- F10: quality moved.
- F11: the held probe observation updated belief.
- Guard: 10 of 18 readers failed (below), and so did the world check: the
  held 0/4 wrote `error_type = conceptual_slip`.
- The 8 that passed on base: the predicate test and `revalidated_support`
  failed on import. The guard readers that passed already excluded a held
  grade (schedule, mastery, projection, field, placement, data-quality
  labels) or this world cannot exercise them (duel, scoreboard). They are
  kept as pins.

## The guard

`test_guard_no_listed_reader_reads_a_held_grades_score[*]` builds one
`mvp-0.17` vault (the split diagnosis vault, seeded history, one validated
4/4). It then makes two backup-API copies that differ only in the held
grade's provisional score:

- one copy holds a 0/4 that carries a grader error claim;
- the other holds a 4/4 with no claim.

Each copy then gets one ordinary failed answer with a located error on the
same item. That answer's severity, quality, streak, familiarity and labels
all look back across the held grade.

Every listed reader must return the same value in both copies. A held grade
that reached any of them would change it. `test_guard_the_worlds_hold_the_grade`
pins that both copies hold the grade and that it wrote no error.

| Reader (guard id) | Base | Branch |
|---|---|---|
| `fsrs_schedule` (difficulty, stability, due) | equal (re-review F9) | equal |
| `mastery` | equal (nothing assessed) | equal |
| `item_quality` | **differs** | equal |
| `failure_streak` | **differs** | equal |
| `active_errors` | **differs** | equal |
| `later_attempt_surprise_severity_familiarity` | **differs** | equal |
| `facet_projection_certification` (facet x capability cells, credit) | equal | equal |
| `learner_field` | equal | equal |
| `fsrs_fitter` (`review_log_loss` of the reconstructed log) | **differs** | equal |
| `retention_evaluation` (`learnloop eval` retention) | **differs** | equal |
| `prediction_coverage` (`learnloop eval` coverage) | **differs** | equal |
| `dataset_outcomes` (`outcome_records`) | **differs** | equal |
| `data_quality_report` (retention labels) | equal (PF-c exclusion) | equal |
| `exam_calibration_duel` | equal (no duel rows here; F7 covers it) | equal |
| `item_difficulty_calibration` | **differs** | equal |
| `placement` (`load_answers`) | equal | equal |
| `cold_success_scoreboard` | equal (an earlier success here) | equal |
| `question_signal_base_rate` | **differs** | equal |

Router R1 and the EVSI report keep their composition tests
(`test_proof_check_composition.py`). Certification probes, exam calibration,
the probe episode and the regrade paths have the dedicated tests above.

## Every reader, and its handling

Method: `grep -rn "correctness\|rubric_score"` over `src/` (outside config,
authoring prompts and the simulator), plus the consumers of attempt rows
(`list_*attempts*`, `fetch_practice_attempt`, repository report queries),
error events, probe observations, labels and FSRS logs. Each reader below is
listed with its handling. **Routed** means it now calls the predicate.
**⊂ nothing assessed** means it already excluded PF-c's nothing-assessed
evidence, which contains every held grade.

### The attempt step (in flight, `AttemptApplication.grade_held`)

| Reader | Handling |
|---|---|
| FSRS review, due date (`apply_review`) | not applied (re-review F9); now through `grade_is_held` |
| Surprise direction, interval factor | `none`, 1.0 (re-review F9) |
| Mastery EKF, EB difficulty, coverage, facet outcomes, facet recall and uncertainty | ⊂ nothing assessed (no update) |
| Error events, the attempt's `error_type`, error severity of its own events | routed: none written |
| Item quality (`build_quality_state_update_from_prior`) | routed: no row (F10) |
| Recent same-item failures for quality (prior attempts) | routed: `HELD_ROW_KEY` skipped (F10) |
| Error severity from recent attempts (`event_local_severity_from_attempts`) | routed: held rows skipped |
| Familiarity / independent-evidence discount (`familiarity_discount_from_attempts`) | routed: a held row's score reads as unknown (weight 1.0); the exposure counts |
| Error-event auto-resolution (`_auto_resolve_clean_error_events`, `count_clean_attempts_since`) | routed: a held grade is never clean; earlier held attempts are excluded from the count |
| Certification cold probe label (`_record_probe_outcome`) | routed (F3) |
| Probe episode observation and posterior (`_record_presentation_observation`, `episode_posterior`) | routed (F11) |
| Grade-channel dual write (raw grade event + calibrated interpretation) | kept. It is the grader's output, and grader calibration against adjudication needs exactly these. Criterion classes are empty (all unassessed). No reader turns a nothing-assessed attempt's interpretation into learner evidence: the field drops the attempt, and certification needs assessed criteria |
| Ability transition audit | kept: an audit of practice done, `applied_to_* = false`, no reader |
| Causal episode, repair factor (`_open_repair_factor`) | routed (ledger). A blind grade materializes only with a diagnosis, and a held grade gets none |
| Repair cold verification (`record_delayed_cold_verification`) | ⊂ nothing assessed (refuses, `cold_attempt_unassessed`) |
| Learning outcome labels (stored, derived) | written with the attempt's recorded correctness, as a candidate pair. Every reader applies `retention_exclusions` with `outcome_grade_held_for_review` (below) |

### Doors that write or release the hold

| Door | Handling |
|---|---|
| Live grade (`_complete_blind_graded_attempt`) | `checked_run`, then `revalidated_support` (F1), then the record flag into the step; the blind record is written after the step |
| Regrade (`regrade_attempt`, both clarification paths, `trigger_regrade`) | reads the prior hold from the ledger; a failed check keeps it (F2); a held prior supersedes tiers 1 and 3 (F4); `revalidated_support` (F1) |
| Replay (`replay_existing_attempt`) | the latest record's flag; the step adds the evidence half |
| Adjudication (`append_adjudication_evidence_revision`) | writes assessed tier-4 rows: releases (F5) |
| Post-attempt pipeline (`run_post_attempt_pipeline`) | routed (ledger, F5); suppresses follow-up insertion while held |

### Scheduling, serving, fitting

| Reader | Handling |
|---|---|
| Scheduler exposure discount (`build_due_queue`, `recent_attempts_by_lo`) | routed: rows marked; exposure kept, score unread |
| Scheduler repair boost (`_recent_error`, active errors) | no error event for a held grade |
| FSRS fitter (`reconstruct_review_log`, `review_log_loss`) | routed (F8) |
| `learnloop eval` predictions (`chosen_candidate_outcomes`) | routed: excluded |
| `learnloop eval` interval coverage (`prediction_interval_rows`) | routed: excluded |
| `learnloop eval` retention: FSRS replay and labels | routed: no review applied, label excluded |
| Router R1 outcomes, coldness candidates, the `predicted_retrievability` covariate | the merge's composition; the held set now comes from the evidence-aware predicate (an adjudication releases) |

### Diagnosis and probes

| Reader | Handling |
|---|---|
| Diagnosis need (`needs_diagnosis`, jobs, planning) | routed (record): a held grade needs none |
| Diagnoser history (`split.history`) | routed: a held attempt stays in the history (it happened) with no score; its criteria are neither failed nor passed (⊂ nothing assessed) |
| Learner-text gaps diagnosis source | the merge's composition, evidence-aware now |
| Follow-up intervention gate (`evaluate_attempt_intervention_followup`) | insertion suppressed with the typed reason `grade_held_for_review` (ledger, F5); the held grade's surprise is `none`, so no gate fires on it |
| Follow-up failure streak (`current_same_item_failure_streak`), also read by practice generation | routed (F9) |
| Episode posterior (`episode_posterior`), both channels | routed (F11) |
| Legacy probe-phase posterior (`probes._probe_phase_attempts`) | routed: held attempts skipped |
| Diagnostic pack, calibration sessions, probe blocks' qualifying counts, inspector | read the held observation's flags: `updates_belief = false`, not qualifying |
| Probe audit: downstream outcomes | routed: excluded |
| Probe audit: replay check | skips `updates_belief = false` |
| Pinned-probe features (`deterministic_probe_features`) | ⊂ nothing assessed (no feature) |
| Contrast-pair order effect (`contrast_pairs`) | routed: excluded |
| Error-hunt metric (`error_hunt`) | routed: excluded |
| Cold-success scoreboard (`cold_success_trajectories`) | routed: served, never the success |
| Recurrence report, next attempt correct | routed: excluded |
| Offline diagnosis review sample (`offline_review.eligible_attempts`) | routed: a held grade is not a "graded wrong answer" |
| EVSI calibration report | the merge's composition, evidence-aware now |

### Goals, learner, placement, tutor, curriculum

| Reader | Handling |
|---|---|
| Certification cold probe | routed (F3) |
| Goal certification, canonical facet x capability ledger | ⊂ nothing assessed |
| Exam calibration (items, facets, duel, confidence share) | routed (F7) |
| Forecast resolution (`forecast_ledger._cold_outcomes`) | routed: a held grade resolves no forecast |
| Exam session (`exam_session`) | n/a: reads its own `exam_answers` from the exam door, which runs no route check |
| Item difficulty miscalibration (`difficulty_miscalibration_flags`) | routed: excluded |
| Facet evidence timeline | ⊂ nothing assessed |
| Learner field (`field.outcomes`) | ⊂ nothing assessed (dropped); its review-log covariate takes the held set |
| Placement answers (`load_answers`) | routed: a held answer is unassessed (never a clean correct answer, never a graded miss) |
| Placement signals (`blocking_signals_by_lo`) | the blocking rule reads help and leaks, not the outcome |
| Tutor question signal (base failure rate, post-question outcome, facet success times) | routed: excluded |
| Graph-edit direction evidence (`_direction_evidence`) | routed: excluded on both sides |

### Datasets and reports

| Reader | Handling |
|---|---|
| Dataset `R_next`, `R_cold` (`outcome_records`) | routed (F6) |
| Data-quality report, retention labels | routed: `outcome_grade_held_for_review` |
| Grader-calibration bootstrap frame (`calibration_streams`) | kept: it stratifies the grader's output for owner adjudication, and a held grade is exactly such a candidate. It is not learner evidence |
| Offline grader evaluations (`pfc_report`, `spot_check`, `embedding_compare`) | kept: they compare grader outputs, not learner outcomes |

### Display only

These show the grader's provisional score with the review reason
`proof_route_check_flag`. None feeds a decision:

- the sidecar feedback bundle, attempt history and knowledge-map chronicle
  (`serializers`, `knowledge_map`);
- the TUI feedback screen and the CLI attempt printout;
- the adjudication, teach-back and exam handlers;
- clarification results, quick-check results, block-end released feedback
  and the tutor's feedback context.

Naming the held state on these screens is a frontend change outside this
stage (open question 1).

## Successor, playbook and parity

- **No new tag.** The change is only for held grades. Held grades exist only
  under `mvp-0.17` with the check on (`proof-route-check-v3`; v1 and v2
  records replay as written). Below `mvp-0.17`, or with the kill switch on,
  no record holds anything, the predicate is empty, and every routed reader
  is a no-op. `mvp-0.17` is unreleased (merge pending), so no tag bump. The
  gate version stays `proof-route-check-v3`: records already written read
  the same, and only the F1 rescope and the F2 kept hold change new records.
- **No migration, no schema or config change.** F3 reuses migration 139's
  `grade_unavailable` reason, because its CHECK fixes the vocabulary. A
  dedicated `grade_held_for_review` reason would need migration 189 (open
  question 3).
- **Parity on backup-API copies.** Run on backup-API copies (`learnloop.db.copies`) of the
  tracked `linear_algebra`, `probability` and `arxiv_v2` vaults, under
  `fixtures-local/hge-parity/` (scripts and logs there; no model call).
  - **Method.** Each copy was upgraded with the BASE code (`a9a030bf`, from
    `git archive`, ahead on `PYTHONPATH`): `mvp-0.8 -> mvp-0.9 -> mvp-0.16`,
    then `-> mvp-0.17` with `[proof_check] enabled = false`.
  - **Rebuilds.** At each stage, three further copies ran
    `rebuild-derived-state`: two with the base code, one with this branch.
  - **Comparison.** Every table (313) was hashed with generated ids, content
    ids derived from them and wall-clock stamps scrubbed, and its JSON
    canonicalized. Raw hashes cannot compare runs: two base runs already
    differ in 19 tables on fresh ULIDs and `now` stamps.
  - **Result.**

    | Vault | `mvp-0.16`: base vs base | `mvp-0.16`: base vs branch | `mvp-0.17`, switch off: base vs base | `mvp-0.17`, switch off: base vs branch |
    |---|---|---|---|---|
    | `linear_algebra` (70 attempts) | 0 tables | **0 tables** | 0 tables | **0 tables** |
    | `probability` | 0 | **0** | 0 | **0** |
    | `arxiv_v2` | 2 (\*) | 2, the same (\*) | 2 (\*) | 2, the same (\*) |

    (\*) In `arxiv_v2`, two base runs already disagree in
    `grade_interpretations` and `measurement_events`. The differences are in
    the grade-channel calibration-model columns (`calibration_model_hash`,
    `credible_interval_json` and their ids), which are rebuilt with generated
    ids. The branch differs from base in exactly those columns. With them
    dropped, every comparison is 0 tables.
  - **Kill switch.** `mvp-0.17` with the switch off equals `mvp-0.16` on
    every table once version labels are dropped, except the two upgrade
    ledgers: `derived_state_rebuilds` (one more upgrade receipt) and
    `parameter_registry_manifests` (one more captured manifest).
  - **Tests.** `test_the_kill_switch_and_the_predecessor_grade_exactly_as_mvp016`
    still pins kill-switch grading, and passes.

## Gate

Run at `dd704cf6` (the last code and reference commit; the record commit
after it is docs only), with `TMPDIR` set to the worktree's
`fixtures-local/tmp`.

| Step | Result |
|---|---|
| `uv sync --extra dev --extra mobile`, then `uv pip install pypdfium2` | done |
| `uv run lint-imports --no-cache` | **15 kept, 0 broken** (the frozen-cycles contract was the reason for the `held_grades` leaf) |
| Full suite: `flock /tmp/learnloop-fullsuite.lock uv run pytest -n auto` | **9248 passed**, 0 failed, 46 warnings, 6 min 0 s. This stage adds 36 tests (`test_held_grade_evidence.py`) and changes no existing test. An earlier run of the same code gave the same count (7 min 18 s) |
| Durability lane: `flock /tmp/learnloop-fullsuite.lock uv run pytest -m durability` | **95 passed**, 9153 deselected |
| DB and config reference: `db_generate_reference.py`, then `db_validate_reference.py` | **errors: []**. Schema head 185, 308 table notes, 367 owned notes, 4072 wikilinks checked. The schema and config did not change; the reference cites moved source lines and the new reader `held_grades.py` (29 notes). Restamp-only churn was dropped (326 notes) |

- **Not applicable.** No file under `apps/learnloop-tauri` changed, so the
  npm and cargo steps do not apply.
- **Mobile allowlist.** No sidecar RPC was added.
- **Test flags.** Both pytest runs also passed `-q -p no:cacheprovider`.

## Paid calls

None. Every test uses fakes; the parity runs make no model call.

## Decisions taken here

1. **Error events.** A held grade writes none, and its attempt has no
   `error_type`. The attributions stay on the blind record and in the
   feedback. A hold settled by a regrade writes the new grade's events. A
   hold settled by adjudication writes none, because the adjudication names
   no error type.
2. **Kill switch.** A regrade with `proof_check.enabled = false` (or of an
   item no longer read as proof-like) is graded as `mvp-0.16` grades and
   releases a hold. Only a check that was meant to run and did not keeps it.
3. **Probe observations are written once.** A held probe answer stays a
   non-updating, non-qualifying observation after a release. Probe
   observations are never re-recorded by a regrade. The episode had already
   selected and stopped without that observation.
4. **Certification probe labels are written once.** A held probe stays
   `indeterminate` after a release, as a withdrawn certificate's does.

## Open questions

1. **Show the held state.** The feedback screen, the attempt history and the
   knowledge-map chronicle show the grader's provisional score, the raw reason
   `proof_route_check_flag`, and an FSRS rating that was never applied.
   Should they say "held for review: not counted"? That is a frontend change.
2. **Stale tier-3 rows on ordinary blind regrades.** F4 is fixed for held
   grades. A blind regrade of a non-held attempt still supersedes tier 1
   only, so its original tier-3 rows stay live beside the new ones. That has
   been true since the split (mvp-0.10). It is not touched here, to keep
   `mvp-0.10`-`mvp-0.16` byte-identical. Should every blind regrade supersede
   tier 3, behind a successor?
3. **A dedicated abstention reason.** A held cold probe records
   `grade_unavailable` (migration 139's vocabulary). Is
   `grade_held_for_review` worth migration 189?
4. **Re-review open question 4 stands.** One validated criterion lifts the
   hold, even when another is unlocated and the final answer is not
   verified. Should the hold cover any unlocated criterion when nothing is
   assessed?

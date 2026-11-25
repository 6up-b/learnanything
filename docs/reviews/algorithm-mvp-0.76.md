# mvp-0.76: review round 3's outcome fixes

The successor of mvp-0.75 for the review-round-3 fixes that change what is derived from stored rows (ledger
`docs/reviews/refactor-bug-ledger.md`, "Review round 3"). One constant (`OUTCOME_FIXES_ALGORITHM_VERSION` in
`algorithm_versions.py`), one upgrade row (`ops/upgrades.py`: a whole-vault rebuild), one test row
(`tests/test_upgrades.py`). No migration. Below the tag every reader is mvp-0.75's.

## What changes at the tag

- FR3-4 (class 5): an answer mastery did not apply is no lesson outcome. A verified alternative with every criterion
  unassessed has `correctness` 1, no review hold and a recorded mastery application with `applied` false. Up to
  mvp-0.75 it qualified as the first cold answer after a lesson, so the lesson-weight fit trained on a success, the
  retained-forecast report scored the forecast with it and the router's miss-cause learning credited the lesson. From
  the tag the one outcome reader (`lesson_weight.qualifying_outcomes`) reads the record through
  `mastery_applications(...).applied` and drops it; all three readers take the next assessed cold answer. An answer
  without a record (below the facts' tag, or a malformed one) is read as before. Test:
  `tests/test_lesson_outcome_assessed.py::test_an_unapplied_answer_resolves_no_lesson_check_from_the_tag` (both sides
  of the tag). The router's miss-cause learning end to end:
  `test_the_routers_miss_cause_learning_credits_no_lesson_with_an_unapplied_answer` (both sides of the tag).
- FR3-16 (class 8): without mastery's IRT link, the forecast surprise is scored against is clipped by the configured
  `mastery.irt.p_clip` once, after a primed answer's shift (`forecast_clipped_after_shift`), and the residual and
  `p_scored` read that one probability, as the IRT link already did. Up to mvp-0.75 an interior forecast outside the
  clip (0.95 at a clip of 0.10) was scored unclipped. Changes stored surprise (`attempt_surprise`) only on a vault with
  `mastery.irt.enabled = false` and a forecast beyond the clip. Test:
  `tests/test_surprise_forecast_scoring.py::test_without_the_irt_link_the_configured_clip_holds_after_the_priming_shift_from_the_tag`
  (both sides of the tag).
- FR3-11 (class 8): an inline answer's forecast eligibility reads the contract its original grade cites
  (`answered_revision.first_grade_contract`), never a regrade epoch's (`inline_guard_reads_first_grade`). Up to
  mvp-0.75 a regrade of an mvp-0.73 inline check (open-time contract without a revision) snapshotted the current item
  and its epoch's contract made the old grade receipt eligible, live at the regrade and on every later rebuild. Changes
  stored surprise only for a regraded inline answer whose original contract froze no revision: it reads mastery.
  Test: `tests/test_selected_forecast.py::test_a_regrade_does_not_make_an_old_inline_forecast_eligible` (both sides
  of the tag).
- FR3-15 (class 8): a landed node's retention forecast (and the lesson check mass weighed against it) names the item
  the commitment will give that node: one allocation (`teacher.delayed.retention_picks`, landing order, each pick
  excluded from later nodes) is read by the commitment and by `teacher.checks.cold_reference`, which is given the
  nodes landed before the node and records the pick's receipt (its logged propensity) on the reference
  (`retention_forecast_shares_allocation`). Up to mvp-0.75 the second of two nodes on one learning object forecast
  against a pick from every candidate, the first node's reserved item included. A live forecast input; replay reads
  the recorded mass. Test:
  `tests/test_data_capture_a6_delayed_pick.py::test_each_landed_nodes_retention_forecast_targets_the_item_it_is_committed`
  (both sides of the tag).
- FR3-5's timing half (class 6, the cutoff guard): from the tag the grade-time forecast's later-evidence guard counts
  only the visible answers the forecast read, by the time their grade became known (their current grading rows' and
  latest adjudication's recording time; `MaterialView.grade_known_after`, `cutoff_reads_the_view`). Up to mvp-0.75 it
  compares the time each raw grade event carries, so a regrade's replacement event, dated at the regraded answer's
  time, let the corrected score into an earlier-dated forecast. A live forecast decision (which answers get a
  grade-time receipt); replay reads the stored receipts. Test:
  `tests/test_surprise_reads_ad_forecast.py::test_a_later_regrade_never_enters_an_earlier_forecast` (both sides of the
  tag).

## Fixed without the tag

- FR3-17: `mastery_applications` checks every field's type. A null or unparsable instant, a missing evidence-clock
  key, a non-boolean flag or a non-finite number makes the record no record, so the fit takes its labelled
  first-order form (`outcome_record_missing`), never an exception (a null instant had become the string `"None"`) and
  never a silently accepted chain (a missing clock key had read as a recorded null clock). Well-formed records read
  exactly as before. Test: `tests/test_lesson_outcome_assessed.py::test_a_malformed_application_record_is_a_labelled_gap`.
- FR3-10: the grade-time receipt passes the vault's tag to the receipt writer on its own, not the vault, so the
  diagnosis receipts' switch (`diagnosis.forecast_receipts`) no longer discards adaptive difficulty's grade-time
  forecast (it was stored at the label retirement, whose writer passed no vault). A live write; a rebuild computes no
  grade receipt, it reads the stored one. Test:
  `tests/test_surprise_reads_ad_forecast.py::test_the_diagnosis_receipt_switch_does_not_discard_the_grade_time_forecast`.
- FR3-18: a teacher correction re-send's receipt records the request gate's estimate of its own prompt (the first
  prompt with the correction appended), not the first send's, so the next context-compaction forecast measures growth
  from the prompt that was actually sent. A receipt note; nothing replays it. Test:
  `tests/test_teacher_te5_compaction.py::test_a_correction_receipt_records_its_own_prompt_estimate`.
- FR3-12: a submit whose retry key has a saved draft naming a presentation of the same item binds that presentation,
  not an older one the restored client sends (the older one is never consumed). The attempt stores the presentation
  it bound and replay reads it, so the decision is the live one on both sides. Test:
  `tests/test_answer_door_sessions.py::test_a_restored_drafts_checkpoint_wins_over_an_older_presentation_it_sends`.
- FR3-5's protection half, at every tag: the guard runs in the forecast's own read snapshot, through adaptive
  difficulty's view, so a held-out answer's grade never withholds a public answer's forecast (below the tag
  `MaterialView.raw_grade_after` reads the raw grade events of visible attempts only; before, the caller read every raw
  grade on its own connection, and a copy with protected material differed from one without). Test:
  `tests/test_answered_revision_protection.py::test_a_later_held_out_grade_does_not_change_an_unrelated_public_answers_forecast`
  (mvp-0.75 and 0.76, against the absent copy).
- FR3-24 and FR3-25 (two flakes, fixed at their source): the reading-opportunity test reads values instead of
  searching the dump for digits a hash can spell; a post-attempt slot's busy backoff waits on the stop, so shutdown
  ends it, and the phone journeys close the desktops they open and wait for their slots.

## Round 4 (Astra verification of review round 3; ledger "Review round 4", R4-S1..)

### Same-day corrections

(Fixes to rules introduced at this tag, made inside it: no vault was at mvp-0.76 when they landed.)

- R4-S6, FR3-16's rule: after the shift and the configured clip, the centre is the exact logit of the clipped
  probability. As first landed it took mastery's `logit`, which holds any value to [0.02, 0.98], so with the default
  clip (1e-4) a forecast of 0.99 (or below 0.02) was scored at 0.98 (0.02), outside the recorded rule and unlike
  mvp-0.75. Now a forecast inside the configured clip scores exactly as at mvp-0.75, and only one beyond it moves
  (what the owner-copy procedure's `beyond_clip_irt_off` count already assumed). Test:
  `tests/test_surprise_forecast_scoring.py::test_without_the_irt_link_a_clip_below_two_percent_is_the_only_clip`
  (both tails). No golden moved.

### Fixed without the tag

- R4-S1: a lesson check's or probe's answer refused by the lesson's budget is kept: the budget close writes the
  learner's answer turn (once per check or probe, `assessed: false`, `unassessed_because: budget`) in the close's
  transaction; a retried check whose answer turn an earlier build left behind grades under that turn's attempt
  reference and appends no second turn. A live write. Tests: `tests/test_lesson_answer_turns.py` (three cases).
- R4-S2: the activity backfill's history boundary is each writer's own first live record (ordinary practice, probes,
  an exam sitting, an exam import; probe presentations by the first live diagnostic administration), not the vault's
  first live administration of any purpose, so a practice answer recorded after a live probe but before practice
  began recording is history again (backfilled with its duration event; replay may record its grade). Where a writer
  never recorded live the vault-wide boundary stays, and the backfill report and doctor say the provenance is unknown.
  FR3-6's decision (no tag). Tests: `tests/test_activity_backfill.py` (two cases).
- R4-S3: `doctor --fix-state` records a missing grade record with the live grade's inputs read back from durable
  facts (`attempts.recover_grade_channel`: run, fatal errors, blind or joint identity), applied to the repaired answer
  only; an answer whose inputs are not on record, and a once-graded exam sitting answer (now reported), stay listed
  with `unrecoverable`. Tests: `tests/test_rebuild_writes_no_grade_record.py` (three cases). Stopped for a call:
  R4-S3b (replay drops fatal errors, a rule from mvp-0.60).
- R4-S4 (FR3-12's residue): a draft's saved plan presentation is bound to the item and retry key it was saved for
  (`planPresentationFor` in the practice envelope); a checkpoint patch that changes either without naming the
  replacement drops it, so a submit never binds an abandoned presentation. Test:
  `tests/test_answer_door_sessions.py::test_a_key_only_checkpoint_patch_drops_the_drafts_old_presentation`.
- R4-S5 (and FR3-8's residue): an exam sitting answer's instant is read inside its own write transaction; below
  mvp-0.65 (where replay breaks a same-second tie by attempt id) the sitting applies its answers in attempt-id order.
  Tests: `tests/test_one_instant_per_grade.py` (reverse submission below 0.65; an ordinary grade interleaved with
  finish). Residue, stopped for a call (changing it touches either the legacy replay rule or the exam attempt's id):
  below mvp-0.65 an ordinary grade committed in the same second just before a sitting answer replays after it,
  because the sitting answer's id carries its staged time. Options: (a) at legacy tags only, wait inside the write
  transaction for the next second when the current one already holds a later-sorting attempt (no future time; up to
  one second's stall); (b) at legacy tags, mint the sitting answer's id after the newest stored id
  (`ids.new_ulid_after`) inside the transaction, re-keying its forecast receipt; (c) accept it: it reaches only a
  vault left below mvp-0.65, and live sequences rule from the tag on. Recommendation: (c), since every owner vault
  is upgraded past mvp-0.65 and no write below it records a sequence to correct.
- R4-S7 (FR3-1, FR3-2 and FR3-5's protection residue, every tag): an unknown answered revision (no saved snapshot
  and not the item's current revision, or a presentation or selection that froze none) is withheld unless its item has
  no protected material on record (`MaterialView.unknown_revision_withheld`); a presentation that froze no revision
  follows the same rule. Tests: `tests/test_answered_revision_protection.py` (two cases) and both shapes in the
  absent-copy contract (`tests/ad23_contract_helpers._protect_r4`).
- R4-S8 (FR3-17's residue): an integer beyond a float in a mastery application record is malformed (the labelled
  gap), never an `OverflowError`. Test: a fifth case of
  `tests/test_lesson_outcome_assessed.py::test_a_malformed_application_record_is_a_labelled_gap`.
- R4-S9 (FR3-23's residue): the given-points rows' ids escape their parts, so `(A:B, C)` and `(A, B:C)` differ; an id
  without `:` or `%` is unchanged. Test:
  `tests/test_one_instant_per_grade.py::test_given_points_row_ids_never_collide_across_attempt_and_criterion_ids`.
- R4-S10 (FR3-9 / FR3-21's residue): a retried exam import finds its imported answer by its import identity (item,
  type, exam date) and replays the object that answer was written under. Test:
  `tests/test_exam_seeding.py::test_a_retried_import_finds_its_answers_by_their_import_identity_and_replays_their_own_object`.

## Pins and goldens

`tests/cli_surface.json`: only the `upgrade --to` default moves to mvp-0.76. Chain-pinned tests shift mechanically.

## The owner-copy procedure (for the orchestrator, from an mvp-0.75 copy; counts and digests only)

Make a backup-API copy of an mvp-0.75 vault for `COPY` (`COPY_DB` its `state.sqlite`). Run the 0.75 record's
payload, mastery and trace digests on it, then `learnloop upgrade --vault "$COPY" --to mvp-0.76`, the same digests
again and the queries below. Expected:

- payloads, `learning_object_mastery`, `facet_recall_state` and `attempt_surprise` differ only in `algorithm_version`,
  except `attempt_surprise` rows of the second query's two counts: a regraded inline answer whose original contract
  froze no revision (FR3-11) reads mastery, and with `mastery.irt.enabled = false` a forecast beyond the clip (FR3-16)
  is scored at the clip (the default clip is 1e-4, so on most vaults both counts are 0 and nothing moves);
- on a copy with lesson checks, the weight and pool updates differ only where an unapplied answer had resolved a
  check (the first query's count); on a copy with none, the trace is unchanged.

```sh
sqlite3 -readonly -header "$COPY_DB" <<'SQL'
SELECT count(*) AS cold_unapplied
FROM practice_attempts a JOIN attempt_debug_payloads p ON p.attempt_id = a.id
WHERE a.attempt_type IN ('independent_attempt', 'open_text', 'diagnostic_probe', 'exam_attempt')
  AND json_extract(p.payload_json, '$.mastery_application.applied') = 0;
SELECT kind, count(*) AS updates FROM lesson_weight_trace WHERE kind IN ('weight_update', 'pool_update')
GROUP BY 1 ORDER BY 1;
SELECT count(DISTINCT a.id) AS regraded_inline
FROM practice_attempts a JOIN grading_evidence e ON e.attempt_id = a.id
WHERE a.submission_id LIKE 'inline:%' AND COALESCE(e.grading_revision, 0) > 0;
SELECT count(*) AS beyond_clip_irt_off
FROM attempt_surprise
WHERE json_extract(predicted_score_dist_json, '$.p_ad') IS NOT NULL
  AND (json_extract(predicted_score_dist_json, '$.p_ad') < 0.0001
       OR json_extract(predicted_score_dist_json, '$.p_ad') > 0.9999);
SQL
```

Both counts are upper bounds (the first does not check the original contract); the second applies only where the vault's config has `mastery.irt.enabled = false`
(and the default clip; with another clip compare against it). FR3-5, FR3-10, FR3-12, FR3-15 and FR3-18 change live
decisions and live receipts only, so the rebuild digests do not move for them.

Run `learnloop rebuild-derived-state --vault "$COPY" --json` twice; the payload, mastery and trace digests must match
after each run.

## The owner-copy run (Nov 25 2026, orchestrator; counts and digests only)

Backup-API copies of the three floor-set vaults walked to `mvp-0.75` with this tip, then a second copy to
`mvp-0.76`. The copies were deleted afterwards.

| | vault 1 | vault 2 | vault 3 |
|---|---|---|---|
| mastery changed; surprise changed; direction changed; due items moved | 0 of 34; 0 of 3; 0; 0 | 0 of 21; 0 of 70; 0; 0 | 0 of 18; 0 of 3; 0; 0 |
| queue Spearman, top-10 overlap | 1.0, 10 | 1.0, 10 | 1.0, 10 |
| surprise by source after | mastery 3 | mastery 70 | mastery 3 |
| curves, forecast receipts and grading evidence digests, 0.75 against 0.76 | same | same | same |
| answers with an unapplied facts block | 1 | 1 | 0 |
| `answers:grade_record_missing` from the doctor | 0 | 0 | 0 |
| grading evidence rows of tier 0 (points given with the grade) | 0 | 0 | 0 |
| payload, mastery and surprise digests after rebuild 1 and 2 | same as after the upgrade | same | same |
| integrity; foreign-key violations; schema head; fence rows | ok; 0; 276; 1 | ok; 0; 276; 1 | ok; 0; 276; 1 |

- Between the 0.75 copy and its 0.76 upgrade only `algorithm_version` (and `updated_at` on facet recall rows) differs
  in `learning_object_mastery`, `facet_recall_state`, `facet_uncertainty` and `attempt_surprise`.
- The narrower activity backfill loses nothing here: the doctor names no answer as missing its grade record, and no
  raw grade row is created by the upgrade or by either rebuild.
- **Not exercised here:** no copy holds a lesson check, a forecast-scored surprise row, an inline check or a regrade
  after an edit, so none of the tag's changed rules is reached; the two unapplied answers resolve no lesson because
  there is none. A vault with those gets this procedure again before its live upgrade, and the doctor's
  `answers:grade_record_missing` count should be read on fresh copies of the live vaults first.
- The landing gate's owner-vault lane was rerun on this tip after the backfill test's setup fix: 92 passed.

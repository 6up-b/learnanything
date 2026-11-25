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
  of the tag).
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
- FR3-5 (class 6, the cutoff guard): the grade-time forecast's later-evidence guard runs in the forecast's own read
  snapshot and through adaptive difficulty's view (`MaterialView.grade_known_after`, `cutoff_reads_the_view`): only
  the visible answers the forecast read count, by the time their grade became known (their current grading rows'
  and latest adjudication's recording time). Up to mvp-0.75 the caller read the newest raw grade event of any item,
  held-out ones included, on its own connection: a later held-out grade withheld an unrelated public answer's
  forecast (a copy with protected material differed from one without), and a regrade's replacement event, dated at
  the regraded answer's time, let the corrected score into an earlier-dated forecast. A live forecast decision (which
  answers get a grade-time receipt); replay reads the stored receipts. Tests:
  `tests/test_answered_revision_protection.py::test_a_later_held_out_grade_does_not_change_an_unrelated_public_answers_forecast`,
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

## Pins and goldens

`tests/cli_surface.json`: only the `upgrade --to` default moves to mvp-0.76. Chain-pinned tests shift mechanically.

## The owner-copy procedure (for the orchestrator, from an mvp-0.75 copy; counts and digests only)

Make a backup-API copy of an mvp-0.75 vault for `COPY` (`COPY_DB` its `state.sqlite`). Run the 0.75 record's
payload, mastery and trace digests on it, then `learnloop upgrade --vault "$COPY" --to mvp-0.76`, the same digests
again and the queries below. Expected:

- payloads, `learning_object_mastery`, `facet_recall_state` and `attempt_surprise` differ only in `algorithm_version`;
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
SQL
```

Run `learnloop rebuild-derived-state --vault "$COPY" --json` twice; the payload, mastery and trace digests must match
after each run.

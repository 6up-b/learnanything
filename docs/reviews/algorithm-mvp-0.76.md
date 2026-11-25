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

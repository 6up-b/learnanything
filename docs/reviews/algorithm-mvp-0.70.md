# mvp-0.70 · Lesson-weight replay inputs

**Proposed, pending the historical-input decision and implementation.** If the owner chooses a policy, the L4-2 successor is mvp-0.70. The Reader owns mvp-0.69. This checkout starts at mvp-0.68. It contains no mvp-0.70 upgrade link.

## What changes

L4-2 concerns the response curve used to fit a lesson check's mass against a later cold outcome. The intervening grade applied `resolve_item_irt_params`, including the item's empirical difficulty, then subtracted the priming offset for a primed attempt. `learner/lesson_weight.py::recorded_trajectory` instead reads the item and LO as they exist at fit time. The resolving item's parameters in `_outcome_item_params` have the same dependence on current content. Improving the fit changes future masses and can change the weight and pool posteriors derived from history. Historical checks retain their recorded `mass_applied`.

## Version and activation decision

The grade passes the effective parameters to both the mastery update and the surprise calculation. The latter writes them as `a` and `b` in `attempt_surprise.predicted_score_dist_json`. There is a provenance limit. The table is DERIVED, owned by `learning_state`, and replay rebuilds it before `lesson_weight`. A row from a previous rebuild can therefore be a reconstruction. A successful fit against this table alone cannot establish that its parameters were observed at grading.

Both choices would append one immutable input per newly applied grade epoch. Key it by attempt and grading revision, record the effective discrimination and difficulty actually passed to mastery after empirical-difficulty and priming adjustments, the algorithm version and provenance `graded`. A superseding grade adds a capture. Replay selects the applicable epoch with the existing grade-epoch rules, joins the captured pair to the recorded observation and delta, and uses the resolving attempt's pair for the cold probability. Applying the priming adjustment twice would distort the trajectory. The journal and the grader's existing evidence remain immutable.

| Owner choice | What activation writes | What replay reads | What the copy comparison should show |
|---|---|---|---|
| **1. Start at upgrade.** Keep the predecessor's interpretation of old attempts. | No historical captures or replacement fits. Start writing grade captures on the successor. Use the playbook's idempotent projection link. | For pre-tag epochs run the predecessor parameter lookup, including its dependence on the then-current authored item. For successor epochs use their grade captures. Record which source each segment used in new or mixed fits. An absent capture for a successor epoch is a missing input, never silently classified as pre-tag. | On identical content, before any new grade, the same check rows, weight/pool parameters and legacy trace. Zero historical captures. After a synthetic successor grade and an item edit, its captured curve stays fixed through two rebuilds. A legacy portion can still drift after an edit. |
| **2. Freeze the historical reconstruction at upgrade.** Refit old checks. | Before clearing any projections, snapshot the predecessor surprise row's numeric pair per existing attempt/epoch with provenance `reconstructed_at_upgrade`, or persist an explicit missing marker. Include still-unresolved histories and pool-only endpoints. Retry reuses the first snapshot. Rebuild derived state from it before publishing the successor. | Read the immutable snapshot for a historical epoch and the grade capture for a successor. Missing intervening inputs select the existing first-order check calculation. For a missing resolving pair, the check calculation uses its stored sensitivity pair and the pool uses its forecast-time `p_a`. Label these fallbacks in the trace. | Historical capture and missing counts reconcile to the snapshot. Trace each changed fit to an epoch and captured or fallback input. Weight/pool parameters may differ, or agree where the old and reconstructed inputs coincide. Applied check masses and raw receipt hashes stay identical. A second rebuild reproduces successor traces and posteriors even after the surprise projection is cleared. |

The first choice preserves historical results at activation and keeps the historical defect. The second pays a capture and replay cost per vault and gives stable historical inputs of limited provenance. Even full numeric coverage cannot prove grade-time provenance on an owner copy that has previously rebuilt its surprise projection. Either choice that needs new storage first requires a migration allocation.

## Pins and tests

The playbook requires the constant, linear-chain entry after mvp-0.69, upgrade row, matching expected activation, regenerated effective defaults and identity changes attributable to the tag. These changes and their tests are pending. No kill switch is specified.

The existing reproduction is `tests/test_teacher_te1_review_fixes.py::test_f6_the_trajectory_at_the_recorded_mass_reproduces_the_outcomes_recorded_prior`. Extend it with an intervening empirical difficulty update, a primed answer and an authored-item edit after grading. Compare the reconstructed effective curves and the posterior at recorded mass with the grade records. Exercise missing historical input, old-version replay, upgrade failure/retry and a second rebuild.

## Owner-copy procedure

Use consistent SQLite backup-API copies. The following inspection is for the orchestrator. Supply the path of a **copy database** in `COPY_DB`. Both commands open their input read-only. The first reports coverage among the attempts between each recorded lesson check and its resolving outcome, including both endpoints. Resolving attempts for pool-only updates are included. Each attempt counts once across overlapping windows. These counts describe fitted windows through the last answered lesson check. An option 2 activation would additionally snapshot attempts outside those windows for future outcomes.

```sh
sqlite3 -readonly -header "$COPY_DB" <<'SQL'
PRAGMA query_only = ON;
WITH windows AS (
  SELECT p.created_at AS starts, p.id AS start_id, o.created_at AS ends, o.id AS end_id,
         c.learning_object_id AS lo
  FROM lesson_weight_trace t
  JOIN lesson_checks c ON c.id = t.lesson_check_id
  JOIN practice_attempts p ON p.id = c.attempt_id
  JOIN practice_attempts o ON o.id = t.resolving_attempt_id
  WHERE t.kind = 'weight_update'
), members AS (
  SELECT a.id, a.primed
  FROM windows w JOIN practice_attempts a ON a.learning_object_id = w.lo
    AND (a.created_at, a.id) >= (w.starts, w.start_id)
    AND (a.created_at, a.id) <= (w.ends, w.end_id)
  UNION
  SELECT a.id, a.primed FROM lesson_weight_trace t
  JOIN practice_attempts a ON a.id = t.resolving_attempt_id WHERE t.kind = 'pool_update'
), curves AS (
  SELECT m.primed,
    CASE WHEN json_valid(s.predicted_score_dist_json) THEN
      json_type(s.predicted_score_dist_json, '$.a') IN ('integer','real') AND
      json_type(s.predicted_score_dist_json, '$.b') IN ('integer','real')
    END AS available
  FROM members m LEFT JOIN attempt_surprise s ON s.attempt_id = m.id
)
SELECT (SELECT count(*) FROM windows) AS fitted_checks, count(*) AS attempts,
       count(*) FILTER (WHERE primed) AS primed,
       count(*) FILTER (WHERE available IS 1) AS with_curve,
       count(*) FILTER (WHERE available IS NOT 1) AS missing_curve FROM curves;
SELECT count(*) AS foreign_key_violations FROM pragma_foreign_key_check;
PRAGMA integrity_check;
SQL
```

For each inspection point, fingerprint the semantic state including the trace, excluding its surrogate row ID. Capture the raw check receipt digest separately. Publish counts and digests only.

```sh
set -o pipefail
sqlite3 -readonly -json "$COPY_DB" 'SELECT * FROM lesson_checks ORDER BY id' | sha256sum
sqlite3 -readonly -json "$COPY_DB" 'SELECT * FROM lesson_weight_state ORDER BY family' | sha256sum
sqlite3 -readonly -json "$COPY_DB" 'SELECT seq,kind,lesson_check_id,resolving_attempt_id,learning_object_id,at,detail_json FROM lesson_weight_trace ORDER BY seq' | sha256sum
```

After the implementation lands, run the following on disposable copies of the same predecessor backup.

1. Record the original database hash. Run the inspections on the mvp-0.69 copy and capture the predecessor's `learnloop rebuild --shadow --json` report.
2. Upgrade a separate mvp-0.69 copy with `learnloop upgrade --vault "$COPY" --to mvp-0.70`. Run `learnloop doctor --vault "$COPY"`, the inspections above and the successor shadow rebuild. Explain each changed weight/pool family, and report mastery, facet, due-date and queue deltas.
3. Rebuild the upgraded copy again. The semantic weight and trace digests must agree with the first successor rebuild. The check receipt digest must agree at every point. Verify the original database hash and report results before upgrading a live vault.

The diagnostic SQL has a synthetic-fixture check in the TE5 record. Owner-copy measurements, activation and rebuild equivalence are pending.

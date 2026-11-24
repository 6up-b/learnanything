# mvp-0.70 · Lesson-weight replay inputs

**Owner decision, 2026-11-23. Option 2.** Freeze the historical reconstruction at upgrade and refit the lesson weights and forecast pools. Future grades capture the curve used by mastery. Measured item difficulty (`mastery.irt.eb_difficulty_enabled`) stays off by default. The tag has no kill switch.

## What ships

Migration 271 creates `attempt_grade_curves`, an append-only RAW_LEDGER table. Each row identifies its attempt, epoch key, nullable grading revision, effective discrimination and difficulty, source algorithm version and provenance. Update, delete and duplicate-key replacement are refused. Adaptive difficulty has no read access. The replayer registry has no clearing owner for a raw ledger.

- **Grading.** In the grade transaction the writer records the exact `a` and `b` shared by mastery and surprise, after any empirical difficulty lookup and priming offset. A replacement grade applies at its historical position during the LO replay. Only the newly applied regrade or adjudication receives a `graded` capture. The other epochs keep their rows.
- **Activation.** Before clearing any projection, freeze all practice attempts, including unresolved checks and pool-only outcomes. Use the canonical grading-epoch rules. A revisioned grade has key `revision:N`, an older unstamped grade has `legacy:<write stamp>`, and an attempt without criterion rows has `no_evidence`. The one predecessor surprise row can supply a finite JSON-number pair for the current epoch. Its provenance is `reconstructed_at_upgrade` even when it coincides with the original grade. Superseded epochs and absent or unusable pairs get `missing_at_upgrade` with both values NULL. A numeric row names the surprise row's algorithm version. A missing marker names the predecessor at the freeze.
- **Retry and publication.** The snapshot transaction commits before replay. The activation rechecks coverage under the SQLite writer lock, committing any newly uncovered epochs before it clears anything. A retry leaves all prior snapshots and missing markers intact. A vault born at the successor has its grade captures. The whole-vault rebuild, its receipt and config publication use the existing journal and commit protocol.
- **Fit.** Select the current epoch for each check, intervening answer and resolving answer. Join its frozen curve to the recorded observation weight and posterior delta. Mastery replay uses an available frozen pair when it regenerates those deltas, including the priming adjustment exactly once. Where a curve is unavailable, mastery can still rebuild its ordinary projection. The lesson fit records that gap independently of any regenerated surprise pair.
- **Missing data.** A missing trajectory input selects the existing first-order calculation. An unavailable resolving curve selects the check's stored sensitivity for the weight and forecast-time `p_a` for the pool. Each update trace records the resolving input, and a weight update also records its trajectory inputs. They name the attempt, epoch, version, provenance and values. An absent row is labelled `missing_capture`. The trace names the fallback. Below the tag the fit still uses the predecessor's authored-parameter lookup and trace format.

The historical refit can change weight and pool posteriors and hence future check masses. The check ledger retains every `mass_applied`. Option 1, starting capture only at the upgrade, was considered and declined because fitting old windows would continue to depend on content edits.

## Integration and tests

**Rebase onto main after the Reader lands mvp-0.69 and migration 270.** The production upgrade row requires mvp-0.69 as its predecessor. This checkout has mvp-0.68 and schema 269. It contains the mvp-0.70 constant, chain entry, activation, expected activation and migration 271. The earlier successors' exact chain assertions target the merged order. The orchestrator must upgrade `fixtures/migration_head` after the rebase, then run the actual 0.69 → 0.70 table tests and fixture-backed rebuild tests. The worker left the fixture untouched.

The extended F6 reproduction in `tests/test_teacher_te1_review_fixes.py` runs with measured difficulty off and on. It checks the empirical update, primed repeat, authored edits to an intervening item and the endpoint, each grade's effective curve, and the prior mean and variance at the recorded mass. `tests/test_teacher_te5_grade_curves.py` covers complete and missing predecessor inputs, failed preparation and retry after the source changes, current and superseded epochs, old-version fitting, replacement grades and repeated rebuilds. The local activation exercise uses the previous tag available in the test tree. `tests/test_grading_cli.py` checks adjudication capture and rollback. `tests/test_grade_curves_migration.py` applies 271 on a backup-API copy and checks the exact schema addition, existing attempts, immutability, constraints and integrity.

## Owner-copy procedure

Use consistent SQLite backup-API copies. The following inspection is for the orchestrator. Supply the path of a **copy database** in `COPY_DB`. Both commands open their input read-only. The first reports coverage among the attempts between each recorded lesson check and its resolving outcome, including both endpoints. Resolving attempts for pool-only updates are included. Each attempt counts once across overlapping windows. These counts describe fitted windows through the last answered lesson check. Activation also covers every attempt outside these windows, including unresolved histories. Run this window inspection before the upgrade. A successor surprise row has already been replayed.

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
sqlite3 -readonly -json "$COPY_DB" 'SELECT * FROM lesson_receipts ORDER BY lesson_id' | sha256sum
sqlite3 -readonly -json "$COPY_DB" "SELECT * FROM forecast_receipts WHERE kind LIKE 'lesson_%' ORDER BY id" | sha256sum
sqlite3 -readonly -json "$COPY_DB" 'SELECT * FROM lesson_weight_state ORDER BY family' | sha256sum
sqlite3 -readonly -json "$COPY_DB" 'SELECT seq,kind,lesson_check_id,resolving_attempt_id,learning_object_id,at,detail_json FROM lesson_weight_trace ORDER BY seq' | sha256sum
```

On disposable copies of the same quiescent predecessor backup, with identical authored content and effective settings, use the following sequence. Keep the original and its WAL hash for the final comparison.

1. With the predecessor binary, record the checks, raw receipts, semantic state and trace digests above. Record the total expected epoch count using the query below. Save `learnloop rebuild --vault "$COPY" --shadow --json`. Use a second untouched backup for the upgrade. A shadow run with a version override alone does not run the activation snapshot.
2. On the second copy use the rebased binary and run `learnloop upgrade --vault "$COPY" --to mvp-0.70`, then `learnloop doctor --vault "$COPY"`. Record the version, schema head, integrity, foreign keys and the same digests. Run the successor-only queries below. The number of reconstructed rows plus missing markers must equal the predecessor epoch count. Every pre-upgrade epoch must have a row. At this point the graded count must be zero.
3. Compare each changed weight or pool update against its predecessor by kind, check/forecast and resolving attempt. Use `detail_json.trajectory_inputs`, `resolving_input`, `likelihood` and `resolving_fallback` to account for the difference. Compare mastery means/variances, facets, due dates and queue counts across copies, and run the successor shadow report. Keep tag-only differences separate from value changes. The check, lesson receipt and forecast receipt digests must match across copies.
4. On the upgraded copy run `learnloop rebuild-derived-state --vault "$COPY" --json` twice, taking all successor digests after each run. Both rebuilds must match activation for the curves, lesson weights, pools, trace and raw receipts. Verify the shadow reports' input hashes and the original database/WAL hash. Report counts, digests and explained deltas for review before any live upgrade.

Before the upgrade, derive the expected snapshot digest directly from the unmodified predecessor database. The one live epoch is selected by the grade ledger's ordering, including older unstamped regrades. SQL casts integer JSON numbers to the REAL type used in the capture. The last check excludes infinite values from overflowed JSON exponents. Set `PRED_DB` to the predecessor backup and `COPY_DB` to the upgraded copy.

```sh
set -o pipefail
sqlite3 -readonly -json "$PRED_DB" <<'SQL' | sha256sum
WITH evidence AS (
  SELECT attempt_id, id, superseded_at, created_at, grading_revision,
         CASE WHEN grading_revision IS NULL THEN 'legacy:' || created_at
              ELSE 'revision:' || grading_revision END AS epoch_key FROM grading_evidence
), epochs AS (
  SELECT DISTINCT a.id AS attempt_id, coalesce(e.epoch_key,'no_evidence') AS epoch_key, e.grading_revision
  FROM practice_attempts a LEFT JOIN evidence e ON e.attempt_id = a.id
), live AS (
  SELECT attempt_id, epoch_key, row_number() OVER (
    PARTITION BY attempt_id ORDER BY (grading_revision IS NULL) DESC, grading_revision DESC, created_at DESC, id DESC
  ) AS position FROM evidence WHERE superseded_at IS NULL
), sources AS (
  SELECT e.*, s.algorithm_version AS source_version,
    CASE WHEN (e.epoch_key = l.epoch_key OR e.epoch_key = 'no_evidence')
              AND json_valid(s.predicted_score_dist_json) THEN s.predicted_score_dist_json END AS dist
  FROM epochs e LEFT JOIN live l ON l.attempt_id = e.attempt_id AND l.position = 1
  LEFT JOIN attempt_surprise s ON s.attempt_id = e.attempt_id
), pairs AS (
  SELECT *, CAST(json_extract(dist,'$.a') AS REAL) AS a, CAST(json_extract(dist,'$.b') AS REAL) AS b,
    json_type(dist,'$.a') IN ('real','integer') AND json_type(dist,'$.b') IN ('real','integer') AS numeric
  FROM sources
), checked AS (
  SELECT *, numeric AND abs(a) < 1e999 AND abs(b) < 1e999 AS available FROM pairs
)
SELECT attempt_id, epoch_key, grading_revision, CASE WHEN available THEN a END AS item_a,
       CASE WHEN available THEN b END AS item_b,
       CASE WHEN available THEN coalesce(nullif(source_version,''),'mvp-0.69') ELSE 'mvp-0.69' END AS algorithm_version,
       CASE WHEN available THEN 'reconstructed_at_upgrade' ELSE 'missing_at_upgrade' END AS provenance
FROM checked ORDER BY attempt_id,epoch_key;
SQL
sqlite3 -readonly -json "$COPY_DB" 'SELECT * FROM attempt_grade_curves ORDER BY attempt_id,epoch_key' | sha256sum
sqlite3 -readonly -header "$COPY_DB" 'SELECT provenance,algorithm_version,count(*) AS epochs FROM attempt_grade_curves GROUP BY provenance,algorithm_version ORDER BY 1,2'
sqlite3 -readonly "$COPY_DB" 'PRAGMA integrity_check; PRAGMA foreign_key_check;'
```

The first two digests must agree immediately after activation. For the independent count in steps 1 and 2, run the predecessor query with `SELECT count(*) AS epochs FROM epochs` in place of its final SELECT. Group `checked` by `available IS 1` to reconcile the numeric and missing counts.

Owner-copy results are pending. A numeric historical row describes the predecessor projection at the freeze. Only a successor grade transaction establishes grade-time provenance.

The pre-rebase identity gate found nine tag-dependent differences and 362 passes. The predecessor-label control reproduced all nine existing digests. The worker stopped at that gate and left the identity goldens for review on the merged tree. The exact sites and test results are in [the TE5 verification record](teacher-te5.md#part-d-verification).

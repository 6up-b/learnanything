# mvp-0.71 · Lesson-weight replay inputs

**Owner decision, 2026-11-23. Option 2.** Freeze the historical reconstruction at upgrade and refit the lesson weights and forecast pools. Future grades capture the curve used by mastery. Measured item difficulty (`mastery.irt.eb_difficulty_enabled`) stays off by default. The tag has no kill switch.

## What ships

Migration 274 creates `attempt_grade_curves`, an append-only RAW_LEDGER table. Each row identifies its attempt, epoch key, nullable grading revision, effective discrimination and difficulty, source algorithm version and provenance. Update, delete and duplicate-key replacement are refused. Adaptive difficulty has no read access. The replayer registry has no clearing owner for a raw ledger.

- **Grading.** In the grade transaction the writer records the exact `a` and `b` shared by mastery and surprise, after any empirical difficulty lookup and priming offset. A replacement grade applies at its historical position during the LO replay. Only the newly applied regrade or adjudication receives a `graded` capture. The other epochs keep their rows.
- **Activation.** Before clearing any projection, freeze all practice attempts, including unresolved checks and pool-only outcomes. Use the canonical grading-epoch rules. A revisioned grade has key `revision:N`, an older unstamped grade has `legacy:<write stamp>`, and an attempt without criterion rows has `no_evidence`. The one predecessor surprise row can supply a finite JSON-number pair for the current epoch. Its provenance is `reconstructed_at_upgrade` even when it coincides with the original grade. Superseded epochs and absent or unusable pairs get `missing_at_upgrade` with both values NULL. A numeric row names the surprise row's algorithm version. A missing marker names the predecessor at the freeze.
- **Retry and publication.** The snapshot transaction commits before replay. The activation rechecks coverage under the SQLite writer lock, committing any newly uncovered epochs before it clears anything. A retry leaves all prior snapshots and missing markers intact. A vault born at the successor has its grade captures. The whole-vault rebuild, its receipt and config publication use the existing journal and commit protocol.
- **Fit.** Select the current epoch for each check, intervening answer and resolving answer. Join its frozen curve to the recorded observation weight and posterior delta. Mastery replay uses an available frozen pair when it regenerates those deltas, including the priming adjustment exactly once. Where a curve is unavailable, mastery can still rebuild its ordinary projection. The lesson fit records that gap independently of any regenerated surprise pair.
- **Missing data.** A missing trajectory input selects the existing first-order calculation. An unavailable resolving curve selects the check's stored sensitivity for the weight and forecast-time `p_a` for the pool. Each update trace records the resolving input, and a weight update also records its trajectory inputs. They name the attempt, epoch, version, provenance and values. An absent row is labelled `missing_capture`. The trace names the fallback. Below the tag the fit still uses the predecessor's authored-parameter lookup and trace format.

The historical refit can change weight and pool posteriors and hence future check masses. The check ledger retains every `mass_applied`. Option 1, starting capture only at the upgrade, was considered and declined because fitting old windows would continue to depend on content edits.

## Integration and tests

**Integrated on main as `mvp-0.71` and migration 274** (it was built as `mvp-0.70` and 271 on an older main; see "Integration on main" below).

The extended F6 reproduction in `tests/test_teacher_te1_review_fixes.py` runs with measured difficulty off and on. It checks the empirical update, primed repeat, authored edits to an intervening item and the endpoint, each grade's effective curve, and the prior mean and variance at the recorded mass. `tests/test_teacher_te5_grade_curves.py` covers complete and missing predecessor inputs, failed preparation and retry after the source changes, current and superseded epochs, old-version fitting, replacement grades and repeated rebuilds. The local activation exercise uses the previous tag available in the test tree. `tests/test_grading_cli.py` checks adjudication capture and rollback. `tests/test_grade_curves_migration.py` applies 274 on a backup-API copy and checks the exact schema addition, existing attempts, immutability, constraints and integrity.

## Integration on main

L4-2 was built on main as of `60e21faadf` (latest tag `mvp-0.68`, migration head 269), proposing `mvp-0.70` and
migration 271. Main has since taken the inline checks (`mvp-0.69`, migrations 270 and 271), the probe router
(`mvp-0.70`, with its fix rounds) and the Reader's retirement (272). G2's second fix round takes 273. The integration
is a merge of origin/main into `teacher/te5-consolidation`:

- **The tag is `mvp-0.71`**: one constant (`LESSON_WEIGHT_CURVES_ALGORITHM_VERSION`), the chain entry after
  `PROBE_ROUTER_ALGORITHM_VERSION`, one upgrade row and one test row.
- **The migration is 274** (`274_attempt_grade_curves.sql`). Its table keeps its role: `attempt_grade_curves` is
  RAW_LEDGER. Each row is a fact captured when its grade is applied. Replay reads it and never writes it
  (`tests/test_replay_writes_no_ledger.py` passes). The one capture made from the replay module is the live
  application of a replacement grade (`applying_grade_to`), which a rebuild never passes.
- **A Codex defect, removed.** To publish from `mvp-0.69` on a chain that did not have it yet, the build added
  `Link.after` (a predecessor override) and a predecessor check in the upgrade walk. On main the chain is whole, so the
  override and the check are gone: the row's predecessor is the chain's, `mvp-0.70`. Kept, the override could have
  let an upgrade skip a tag's activation.
- **The activation, re-checked against what main gained:**
  - Before any projection is cleared, the snapshot freezes every practice attempt's grading epochs. This covers
    attempts the inline checks administer (ordinary attempts through the one attempt service) and the grade channel's
    epochs (the canonical grading-epoch rules).
  - The probe router's records are raw ledgers that the whole-vault rebuild does not clear: its decisions, its coin's
    assignments, its traces with their replay payloads. Nothing in the snapshot reads them.
  - The rebuild-history fixes still hold. Replay carries the follow-up gate records and reuses stored hypothesis
    versions; L4-2's replay change reads the frozen curve and touches neither.
  - The missing markers and the owner-copy query below name the predecessor `mvp-0.70`.
- **H3** (lands after this): the capture point stays where it was built. `if reads.recorded_curve is None:` in
  `attempts.py` takes an `or retired` clause there.
- **The head fixture.** `fixtures/migration_head` is upgraded to 274 last, once 273 is on main, per CLAUDE.md. Until
  then the migration tests that read the head fixture apply 274 on top of it and fail; they are named in the
  integration report. `tests/test_grade_curves_migration.py` applies 274 on the fixture at 272 and passes.

## Review fix round (the adversarial review of 2026-11-24)

The review of `7e5c3dcb2e` found 1 blocker, 10 majors and 2 minors, plus a second "blocker" (273 missing, the fixture
at 272) that the merge of G2 round 2 and the fixture step had already fixed. Every finding was checked against the
code. Ledger rows are L42-R1 to L42-R14.

| Finding | Disposition |
|---|---|
| Blocker: a grader holding the predecessor's config commits after another process completed the activation; its epoch stays uncaptured for good | **Fixed (L42-R1)**: every applied grade now records its curve, whatever tag the writing process loaded (`record_attempt`; the replacement grade's capture in `replay_learning_object` likewise). The decision no longer reads a config at all. Below the tag nothing reads these rows, and the activation freezes only the epochs no grade recorded. Fail-first: `tests/test_grade_curves_capture_integrity.py` (a predecessor-config grade; a grade committed by a stale process after another upgraded). The TE5 upgrade tests now build an owner's history as the old code wrote it (`forget_captures`). |
| The same stale-config class elsewhere on the grade path | **Recorded, not fixed (L42-R2):** every successor gate on the grade path reads the writing process's loaded `vault.config`. This is a wider, pre-existing class: the tag lives in `learnloop.toml`, not in the database, so a process that loaded an older config applies that tag's rules until it reloads. Its fix is one seam: the tag stored in SQLite by the activation and read under the writer lock. It needs a schema change and touches every gate, so it is not this step's. |
| 273 missing, fixture at 272 | Already fixed: G2 round 2 merged, fixture at 274. |
| Major: a replacing insert naming an existing rowid deletes a capture past the guards | **Fixed (L42-R3)** in migration 274 itself (not landed): the replacement guard also refuses an existing rowid. `WITHOUT ROWID` was tried and set aside, because every row-snapshot helper in the test goldens keys rows by rowid. The head fixture was redone from the 273 file. Fail-first: `test_no_replacing_insert_can_remove_a_capture`. |
| Major: the evidence-only adjudication writer before the upgrade; the snapshot attributes revision 0's pair to revision 1 | **Open (L42-R4):** the snapshot must establish that the projection applied the current revision. The surprise row carries no revision. Plan: compare the surprise row's observed score bucket with the current epoch's score, and write `missing_at_upgrade` when they disagree. |
| Major: a concurrent regrade between the fit's reads | **Open (L42-R5):** read the scores, holds, epochs and curves in one snapshot transaction. |
| Major: same-second ordering by id | **Open (L42-R6):** use `attempt_order_for(vault.config)` for the trajectory's bounds and first use, and in the owner-copy window query. |
| Major: the coverage variance floor | **Open (L42-R7):** recover the noise from the pre-floor update and apply the recorded floor per step. |
| Major: a regraded pre-check attempt or a re-anchoring claim inside the window | **Open (L42-R8):** start from the check's replayed pre-update state, or mark the trajectory unavailable. |
| Major: a calibration import changes replayed interpretation variance | **Open (L42-R9):** bind the applied interpretation variance to the epoch. |
| Major: `mastery.irt.enabled=false` reads a full-credit check as zero | **Open (L42-R10):** pass the recorded score and maximum through the fit. |
| Major: the derived lesson state is stale after a replacement grade | **Open (L42-R11):** refresh or invalidate the lesson state in the replacement transaction. |
| Major (TE5 B): the forecast drops the current prompt's estimate | **Open (L42-R12):** add the known current input before the output allowance. |
| Major: empirical difficulty reseeded from an edited authored value | **Open (L42-R13):** seed the first replayed update from the recorded cold difficulty. |
| Minor: a flat response (a = 0) records almost no mass | **Open (L42-R14):** detect a flat inverse and keep the learned mass. |
| Minor: the window query counted an overflowed pair as available | **Fixed:** the query above uses the finite-pair predicate. |

**For the owner-copy run:** a copy opened by this code before its upgrade records `graded` rows for any grade made
meanwhile. The expected-snapshot digest below assumes no such rows, so run it on copies no newer code has graded.

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
      json_type(s.predicted_score_dist_json, '$.b') IN ('integer','real') AND
      abs(json_extract(s.predicted_score_dist_json, '$.a')) < 1e999 AND
      abs(json_extract(s.predicted_score_dist_json, '$.b')) < 1e999
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
2. On the second copy use the rebased binary and run `learnloop upgrade --vault "$COPY" --to mvp-0.71` (from an `mvp-0.69` copy the walk passes through `mvp-0.70`'s idempotent projection first), then `learnloop doctor --vault "$COPY"`. Record the version, schema head, integrity, foreign keys and the same digests. Run the successor-only queries below. The number of reconstructed rows plus missing markers must equal the predecessor epoch count. Every pre-upgrade epoch must have a row. At this point the graded count must be zero.
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
       CASE WHEN available THEN coalesce(nullif(source_version,''),'mvp-0.70') ELSE 'mvp-0.70' END AS algorithm_version,
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

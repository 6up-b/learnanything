# mvp-0.72 · Lesson-weight replay inputs

**Owner decision, 2026-11-23. Option 2.** Freeze the historical reconstruction at upgrade and refit the lesson weights and forecast pools. Future grades capture the curve used by mastery. Measured item difficulty (`mastery.irt.eb_difficulty_enabled`) stays off by default. The tag has no kill switch.

## What ships

Migration 274 creates `attempt_grade_curves`, an append-only RAW_LEDGER table. Each row identifies its attempt, epoch key, nullable grading revision, effective discrimination and difficulty, source algorithm version and provenance. Update, delete and duplicate-key replacement are refused. Adaptive difficulty has no read access. The replayer registry has no clearing owner for a raw ledger.

- **Grading.** In the grade transaction the writer records the exact `a` and `b` shared by mastery and surprise, after any empirical difficulty lookup and priming offset. A replacement grade applies at its historical position during the LO replay. Only the newly applied regrade or adjudication receives a `graded` capture. The other epochs keep their rows.
- **Activation.** Before clearing any projection, freeze all practice attempts, including unresolved checks and pool-only outcomes. Use the canonical grading-epoch rules. A revisioned grade has key `revision:N`, an older unstamped grade has `legacy:<write stamp>`, and an attempt without criterion rows has `no_evidence`. The one predecessor surprise row can supply a finite JSON-number pair for the current epoch. Its provenance is `reconstructed_at_upgrade` even when it coincides with the original grade. Superseded epochs and absent or unusable pairs get `missing_at_upgrade` with both values NULL. A numeric row names the surprise row's algorithm version. A missing marker names the predecessor at the freeze.
- **Retry and publication.** The snapshot transaction commits before replay. The activation rechecks coverage under the SQLite writer lock, committing any newly uncovered epochs before it clears anything. A retry leaves all prior snapshots and missing markers intact. A vault born at the successor has its grade captures. The whole-vault rebuild, its receipt and config publication use the existing journal and commit protocol.
- **Fit.** Select the current epoch for each check, intervening answer and resolving answer. Join its frozen curve to the recorded observation weight and posterior delta. Mastery replay uses an available frozen pair when it regenerates those deltas, including the priming adjustment exactly once. Where a curve is unavailable, mastery can still rebuild its ordinary projection. The lesson fit records that gap independently of any regenerated surprise pair.
- **Missing data.** A missing trajectory input selects the existing first-order calculation. An unavailable resolving curve selects the check's stored sensitivity for the weight and forecast-time `p_a` for the pool. Each update trace records the resolving input, and a weight update also records its trajectory inputs. They name the attempt, epoch, version, provenance and values. An absent row is labelled `missing_capture`. The trace names the fallback. Below the tag the fit still uses the predecessor's lookup (the seam for the vault's tag, label-free at `mvp-0.71`) and trace format.

The historical refit can change weight and pool posteriors and hence future check masses. The check ledger retains every `mass_applied`. Option 1, starting capture only at the upgrade, was considered and declined because fitting old windows would continue to depend on content edits.

## Integration and tests

**Integrated as `mvp-0.72` and migration 274, on top of the difficulty label's retirement (H3, `mvp-0.71`)**. It was built as `mvp-0.70` and 271 on an older main, then integrated as `mvp-0.71` before H3 landed first; see "Integration on main" and "Integration on the label's retirement" below.

The extended F6 reproduction in `tests/test_teacher_te1_review_fixes.py` runs with measured difficulty off and on. It checks the empirical update, primed repeat, authored edits to an intervening item and the endpoint, each grade's effective curve, and the prior mean and variance at the recorded mass. `tests/test_teacher_te5_grade_curves.py` covers complete and missing predecessor inputs, failed preparation and retry after the source changes, current and superseded epochs, old-version fitting, replacement grades and repeated rebuilds. The local activation exercise uses the previous tag available in the test tree. `tests/test_grading_cli.py` checks adjudication capture and rollback. `tests/test_grade_curves_migration.py` applies 274 on a backup-API copy and checks the exact schema addition, existing attempts, immutability, constraints and integrity. The review fix round adds `tests/test_grade_curves_capture_integrity.py`, `tests/test_lesson_weight_fit_reads.py` and `tests/test_lesson_weight_fit_trajectory.py`, and runs the owner-copy queries below in tests.

## Integration on main

L4-2 was built on main as of `60e21faadf` (latest tag `mvp-0.68`, migration head 269), proposing `mvp-0.70` and
migration 271. Main has since taken the inline checks (`mvp-0.69`, migrations 270 and 271), the probe router
(`mvp-0.70`, with its fix rounds) and the Reader's retirement (272). G2's second fix round takes 273. The integration
is a merge of origin/main into `teacher/te5-consolidation`:

- **The tag is `mvp-0.72`**: one constant (`LESSON_WEIGHT_CURVES_ALGORITHM_VERSION`), the chain entry after
  `LABEL_RETIRED_ALGORITHM_VERSION`, one upgrade row and one test row.
- **The migration is 274** (`274_attempt_grade_curves.sql`). Its table keeps its role: `attempt_grade_curves` is
  RAW_LEDGER. Each row is a fact captured when its grade is applied. Replay reads it and never writes it
  (`tests/test_replay_writes_no_ledger.py` passes). The one capture made from the replay module is the live
  application of a replacement grade (`applying_grade_to`), which a rebuild never passes.
- **A Codex defect, removed.** To publish from `mvp-0.69` on a chain that did not have it yet, the build added
  `Link.after` (a predecessor override) and a predecessor check in the upgrade walk. On main the chain is whole, so the
  override and the check are gone: the row's predecessor is the chain's (now `mvp-0.71`). Kept, the override could have
  let an upgrade skip a tag's activation.
- **The activation, re-checked against what main gained:**
  - Before any projection is cleared, the snapshot freezes every practice attempt's grading epochs. This covers
    attempts the inline checks administer (ordinary attempts through the one attempt service) and the grade channel's
    epochs (the canonical grading-epoch rules).
  - The probe router's records are raw ledgers that the whole-vault rebuild does not clear: its decisions, its coin's
    assignments, its traces with their replay payloads. Nothing in the snapshot reads them.
  - The rebuild-history fixes still hold. Replay carries the follow-up gate records and reuses stored hypothesis
    versions; L4-2's replay change reads the frozen curve and touches neither.
  - The missing markers and the owner-copy query below name the predecessor `mvp-0.71`.
- **H3** (lands after this): the capture point stays where it was built. `if reads.recorded_curve is None:` in
  `attempts.py` takes an `or retired` clause there.
- **The head fixture.** `fixtures/migration_head` is at 274, redone from the tracked 273 file after the fix round's
  change to 274's replacement guard (its README section names it).

## Integration on the label's retirement (H3, `mvp-0.71`)

H3 landed first as `mvp-0.71`; L4-2 merged on top of it (`a17cba6132`) and became `mvp-0.72`, migration 274
unchanged. The resolution follows H3's record ("For L4-2's integrator").

**Which read takes which pair:**

| Reader | Pair it uses | Why |
|---|---|---|
| Live grade, any tag | the seam's pair for the vault's tag; recorded as the epoch's `graded` curve | one capture point, right after `record_attempt_outcome`; it reads the surprise row's `predicted_score_dist`, which H3 keeps as mastery's pair (never AD's `b_scored`) |
| Mastery's replay (`_grade_evidence`) | the label-free seam whenever `reads.recorded_curve is None or label_retired(tag)` | from `mvp-0.71` the seam has no item term, so it re-derives every epoch's pair. Curves are read only at `mvp-0.72` and later, all retired, so mastery's replay never applies a recorded curve now; the branch stays for the order the integration fixed |
| The upgrade's freeze (`mvp-0.71` → `mvp-0.72`) | the predecessor's surprise row | at `mvp-0.71` those rows are label-free: the retirement's whole-vault rebuild re-derived them, and an older copy walks through that rebuild before the freeze. Tested: `test_a_copy_graded_with_the_label_freezes_the_label_free_curve_after_the_walk` |
| The lesson-weight fit (trajectory, resolving input) | the frozen pair | the owner's option 2. It agrees with mastery's replay wherever the frozen pair is label-free (every epoch graded or reconstructed at `mvp-0.71` or later) |
| The predecessor fit (below `mvp-0.72`) | the seam for the vault's tag | `item_irt_params(..., algorithm_version=)`: at `mvp-0.71` no authored difficulty reaches it |

**Where they can disagree, and what happens:**
- A `graded` curve written by this branch's code below `mvp-0.71` (every grade records one) holds the label's pair, while mastery's replay at `mvp-0.72` uses the label-free pair. The fit's reproduction check (L42-R8) then fails, and the window is labelled and takes the first-order form.
  - Owner vaults were graded by main's code, which records no curve, so they hold none of these.
- A later change to `mastery.irt.discrimination_default` or `priming_b_offset` moves mastery's replay but not the frozen pairs. The same check labels the affected windows.
- The four-way replay (`scripts/difficulty_four_way.py`) and `scripts/label_retirement_counts.py` replay mastery. With `or retired`, arm (f) at `mvp-0.71` and the recorded curve at `mvp-0.72` name the same pair for an attempt: the label-free one, minus the priming offset when primed. `tests/test_difficulty_four_way.py` and `tests/test_label_retirement_counts.py` pass (L42-R16 fixed).

**What the merge changed in behaviour:**
- The predecessor fit no longer depends on authored difficulty edits. The TE5 upgrade test, the regrade test and F6 now assert this instead of the opposite.
- Measured difficulty does not run from `mvp-0.71`. L42-R13's seed change is unreachable and gave way to main's form.
- The surprise rows the freeze reads are label-free, so for owner copies the reconstructed pairs are `(discrimination_default, 0)`, or `(discrimination_default, −priming_b_offset)` when primed.

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
| Major: the evidence-only adjudication writer before the upgrade; the snapshot attributes revision 0's pair to revision 1 | **Fixed (L42-R4).** Verified: the CLI below the grade channel fixes (`mvp-0.60`) appends the revision without replaying, and the surprise row carries no revision. The freeze now attributes the surprise row's pair to the current epoch only when its observed score bucket is the current grade's (`attempts.surprise.score_bucket` of the attempt's correctness, passed in because the store layer cannot import it); otherwise `missing_at_upgrade`. An adjudication writes one of the coarse response schema's fractions (0, 1/2, 1) rounded to the rubric's points; any two distinct resulting scores lie in different buckets, so an adjudication that changed the score is always detected. Accepted residual: a held grade released at the same score keeps the reconstruction, whose pair is the same item's curve at grade time. The owner-copy expected-snapshot query applies the same rule. Fail-first: `test_an_unapplied_adjudication_before_the_upgrade_is_not_given_the_applied_epochs_curve`, which also runs the record's query on the predecessor and compares it with what the freeze wrote. |
| Major: a concurrent regrade between the fit's reads | **Fixed (L42-R5).** Verified: each `repository.connection()` in `replay_state` opened its own connection, so its reads spanned commits; the live check read the prior, weighed the check and applied it in three transactions. `replay_state` now reads in one snapshot (one pinned connection, `read_snapshot`); the live check weighs, records and applies the check in one `BEGIN IMMEDIATE` transaction. Fail-first: `tests/test_lesson_weight_fit_reads.py` (a regrade committed from another thread mid-fit, in the durability lane's WAL; another process's grade committed between the weighing and the check's application). |
| Major: same-second ordering by id | **Fixed (L42-R6)** at `mvp-0.72` only (below it the predecessor's order stands): the trajectory's window and order, an item's first use in `qualifying_outcomes`, and same-instant outcome and calibration events follow `attempt_order_for(vault.config)`. The owner-copy window query orders by application sequence too. Fail-first: `test_an_update_applied_before_the_outcome_in_its_second_is_in_the_window` (also runs the record's window query) and `test_an_items_first_use_is_the_attempt_applied_first_in_its_second`. |
| Major: the coverage variance floor | **Fixed (L42-R7).** Each recorded update carries its debug payload's `mastery_variance_floor`, and the recomputation applies it after the update. An update whose variance the floor set has no recorded variance step, so its noise is not recoverable: the trajectory input says `variance_floor_bound` and the fit takes the first-order form. Fail-first: `tests/test_lesson_weight_fit_trajectory.py` (floor bound; floor applied at another mass). |
| Major: a regraded pre-check attempt or a re-anchoring claim inside the window | **Fixed (L42-R8).** The recomputation starts from the state the check's own update replayed from (its recorded `mu_before`, `P_before`) with the recorded evidence clock. At the recorded mass it must then reproduce every recorded update and the outcome's recorded prior to numerical resolution (`_REPRODUCTION_TOLERANCE`, 1e-9, registered; the mass guard reads it too). A transition the attempt updates do not carry (a re-anchoring claim, another writer of the state, a changed evidence clock) fails that check: the input says `prior_not_reproduced`, `update_not_reproduced` or `outcome_prior_not_reproduced`, and the first-order form runs. Fail-first: the regraded-earlier-answer and the claim-inside-the-window tests in the same file. |
| Major: a calibration import changes replayed interpretation variance | **Not this step's (L42-R9, open as a wider class).** Verified: replay recomputes the interpretation variance from the latest matching calibration model (`resolve_calibration_model`, latest-wins by design: a retuned or imported model re-interprets past grades), so a rebuild after an import changes mastery itself, not only the fit; an import triggers no rebuild, so mastery's stored state is as stale as the fit's. The fit reads mastery's replayed deltas and stays consistent with it: two rebuilds agree, and the recomputation reproduces each replayed update. Binding the noise to the epoch would change the calibration channel's retroactive design for mastery; that is an owner call, recorded in the ledger. |
| Major: `mastery.irt.enabled=false` reads a full-credit check as zero | **Fixed (L42-R10)** at `mvp-0.72`: the fit's observations carry the recorded score as the rubric fraction (`rubric_score / max_points` is the recorded correctness exactly), which the logit-space update reads. Fail-first: `test_with_irt_off_the_recomputed_trajectory_reads_full_and_partial_credit`. |
| Major: the derived lesson state is stale after a replacement grade | **Fixed (L42-R11):** a replacement grade (`applying_grade_to`: a regrade, a CLI adjudication that revised) refreshes the lesson-weight tables in its own transaction with the replayer's function, whatever the tag (they are DERIVED and keep their meaning). Fail-first: `test_a_regrade_leaves_the_lesson_weight_tables_as_a_rebuild_would`. |
| Major (TE5 B): the forecast drops the current prompt's estimate | **Fixed (L42-R12).** The current prompt is already rendered. With a measured last send the current input is that send's measured count plus the estimated growth of its prompt since (the root receipt's `input_text`, estimated by the request gate's own estimator, so only the difference is estimated); with that text withheld, the count alone; with no measured send, the estimate. The forecast is the larger of the learned need and the current input plus the most this lesson's answers have needed (the output allowance before any is measured). The decision's facts add `current_input`, `current_input_basis` and `output_need`. Fail-first: `test_a_long_current_reply_after_short_measured_sends_is_forecast`. |
| Major: empirical difficulty reseeded from an edited authored value | **Fixed (L42-R13), then superseded by the label's retirement:** the fix seeded measured difficulty's first update from the `b` the grade's mastery update used. From `mvp-0.71` measured difficulty does not run at all, so on the merge the seed change gave way to main's form (it is unreachable at every tag that reads curves). Test, now: `test_measured_difficulty_stays_off_at_the_curves_tag_and_an_edit_moves_no_curve`. |
| Minor: a flat response (a = 0) records almost no mass | **Fixed (L42-R14)** at `mvp-0.72`: when every mass predicts the same success the pool identifies no mass; the check keeps its learned mass and its pool record says `implied: flat_response`. Fail-first: `test_a_flat_response_keeps_the_learned_mass`. |
| Minor: the window query counted an overflowed pair as available | **Fixed:** the query above uses the finite-pair predicate. |
| Found by the fix round's affected-set run: the scoreboard's certification replay pruned a scratch copy without dropping its append-only delete guards, so a captured curve failed every prefix | **Fixed (L42-R15):** the copy drops them with goal history's function first. Test: `test_certification_replay_prunes_past_an_adjudicated_attempt` (failed on the branch before). Also found there, tag-only: `tests/goldens/placement_stored_misses.json` still said `mvp-0.70` (an integration miss); regenerated, the tag its only change. |
| Found by the same run, pre-existing on the branch: the H2 four-way replay's label-off arm is inert where mastery's replay reads a recorded curve (`tests/test_difficulty_four_way.py`, two tests) | **Fixed in the H3 merge (L42-R16):** mastery's replay takes the label-free seam whenever the label is retired; see "Integration on the label's retirement". The four-way and label-retirement-count tests pass, and the walk test checks the frozen pair is the label-free one. |

Each fail-first test was run on the source before its fix and failed there (the R7/R8 tests on the commit before theirs). All fit changes except R5's snapshot and R11's refresh are gated on the curves' tag (now `mvp-0.72`); those two change no predecessor output (one snapshot reads the same rows; the refreshed tables are what a rebuild writes).

**For the owner-copy run:** a copy opened by this code before its upgrade records `graded` rows for any grade made
meanwhile. The expected-snapshot digest below assumes no such rows, so run it on copies no newer code has graded.

## Owner-copy procedure

Start from an `mvp-0.71` copy (H3's tag, after its whole-vault rebuild). Use consistent SQLite backup-API copies. Everything below prints counts or digests only. The rest goes to files that are not printed. The following inspection is for the orchestrator. Supply the path of a **copy database** in `COPY_DB`. Both commands open their input read-only. The first reports coverage among the attempts between each recorded lesson check and its resolving outcome, including both endpoints. Resolving attempts for pool-only updates are included. Each attempt counts once across overlapping windows. These counts describe fitted windows through the last answered lesson check. Activation also covers every attempt outside these windows, including unresolved histories. Run this window inspection before the upgrade. A successor surprise row has already been replayed.

```sh
sqlite3 -readonly -header "$COPY_DB" <<'SQL'
PRAGMA query_only = ON;
WITH ordered AS (
  SELECT a.id, a.primed, a.created_at, a.learning_object_id,
         coalesce(q.sequence, 9223372036854775807) AS seq
  FROM practice_attempts a LEFT JOIN attempt_application_order q ON q.attempt_id = a.id
), windows AS (
  SELECT p.created_at AS starts, p.seq AS start_seq, p.id AS start_id,
         o.created_at AS ends, o.seq AS end_seq, o.id AS end_id, c.learning_object_id AS lo
  FROM lesson_weight_trace t
  JOIN lesson_checks c ON c.id = t.lesson_check_id
  JOIN ordered p ON p.id = c.attempt_id
  JOIN ordered o ON o.id = t.resolving_attempt_id
  WHERE t.kind = 'weight_update'
), members AS (
  SELECT a.id, a.primed
  FROM windows w JOIN ordered a ON a.learning_object_id = w.lo
    AND (a.created_at, a.seq, a.id) >= (w.starts, w.start_seq, w.start_id)
    AND (a.created_at, a.seq, a.id) <= (w.ends, w.end_seq, w.end_id)
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

On disposable copies of the same quiescent `mvp-0.71` backup, with identical authored content and effective settings, use the following sequence. Keep the original and its WAL hash for the final comparison.

1. With the predecessor binary, record the checks, raw receipts, semantic state and trace digests above. Record the total expected epoch count using the query below. Save `learnloop rebuild --vault "$COPY" --shadow --json` to a file (do not print it). Use a second untouched backup for the upgrade. A shadow run with a version override alone does not run the activation snapshot.
2. On the second copy use the rebased binary and run `learnloop upgrade --vault "$COPY" --to mvp-0.72` from an `mvp-0.71` copy (an older copy walks through `mvp-0.71`'s whole-vault rebuild first, which re-derives every surprise row without the label before the freeze reads them), then `learnloop doctor --vault "$COPY"`. Record the version, schema head, integrity, foreign keys and the same digests. Run the successor-only queries below. The number of reconstructed rows plus missing markers must equal the predecessor epoch count. Every pre-upgrade epoch must have a row. At this point the graded count must be zero.
3. Compare each changed weight or pool update against its predecessor by kind, check/forecast and resolving attempt. Use `detail_json.trajectory_inputs`, `resolving_input`, `likelihood` and `resolving_fallback` to account for the difference. Count the successor's likelihoods and the labels that sent a trajectory to the first-order form (the label query below). Compare mastery means/variances, facets, due dates and queue counts across copies, and run the successor shadow report. Keep tag-only differences separate from value changes. The check, lesson receipt and forecast receipt digests must match across copies.
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
  SELECT DISTINCT a.id AS attempt_id, a.correctness, coalesce(e.epoch_key,'no_evidence') AS epoch_key,
         e.grading_revision
  FROM practice_attempts a LEFT JOIN evidence e ON e.attempt_id = a.id
), live AS (
  SELECT attempt_id, epoch_key, row_number() OVER (
    PARTITION BY attempt_id ORDER BY (grading_revision IS NULL) DESC, grading_revision DESC, created_at DESC, id DESC
  ) AS position FROM evidence WHERE superseded_at IS NULL
), sources AS (
  SELECT e.*, s.algorithm_version AS source_version,
    CASE WHEN (e.epoch_key = l.epoch_key OR e.epoch_key = 'no_evidence')
              AND json_valid(s.predicted_score_dist_json)
              AND (e.correctness IS NULL OR (json_valid(s.observed_joint_bucket_json)
                   AND json_extract(s.observed_joint_bucket_json, '$.score_bucket') IS
                       CASE WHEN 4.0 * e.correctness <= 1 THEN 'low' WHEN 4.0 * e.correctness <= 3 THEN 'mid'
                            ELSE 'high' END))
         THEN s.predicted_score_dist_json END AS dist
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
       CASE WHEN available THEN coalesce(nullif(source_version,''),'mvp-0.71') ELSE 'mvp-0.71' END AS algorithm_version,
       CASE WHEN available THEN 'reconstructed_at_upgrade' ELSE 'missing_at_upgrade' END AS provenance
FROM checked ORDER BY attempt_id,epoch_key;
SQL
sqlite3 -readonly -json "$COPY_DB" 'SELECT * FROM attempt_grade_curves ORDER BY attempt_id,epoch_key' | sha256sum
sqlite3 -readonly -header "$COPY_DB" 'SELECT provenance,algorithm_version,count(*) AS epochs FROM attempt_grade_curves GROUP BY provenance,algorithm_version ORDER BY 1,2'
sqlite3 -readonly "$COPY_DB" 'PRAGMA integrity_check; PRAGMA foreign_key_check;'
```

The successor's likelihoods, first-order labels and resolving fallbacks (counts only; run on the upgraded copy after each rebuild):

```sh
sqlite3 -readonly -header "$COPY_DB" <<'SQL'
SELECT json_extract(detail_json, '$.likelihood') AS likelihood, count(*) AS updates
FROM lesson_weight_trace WHERE kind = 'weight_update' GROUP BY 1 ORDER BY 1;
SELECT j.key AS label, count(DISTINCT t.seq) AS updates
FROM lesson_weight_trace t, json_each(t.detail_json, '$.trajectory_inputs') i, json_each(i.value) j
WHERE t.kind = 'weight_update' AND j.key IN ('missing_observation_or_delta', 'variance_floor_bound',
  'prior_not_reproduced', 'update_not_reproduced', 'outcome_prior_not_reproduced')
GROUP BY 1 ORDER BY 1;
SELECT kind, json_extract(detail_json, '$.resolving_fallback') AS fallback, count(*) AS updates
FROM lesson_weight_trace WHERE json_extract(detail_json, '$.resolving_fallback') IS NOT NULL
GROUP BY 1, 2 ORDER BY 1, 2;
SQL
```

The first two digests must agree immediately after activation. For the independent count in steps 1 and 2, run the predecessor query with `SELECT count(*) AS epochs FROM epochs` in place of its final SELECT. Group `checked` by `available IS 1` to reconcile the numeric and missing counts.

A numeric historical row describes the predecessor projection at the freeze. Only a successor grade transaction establishes grade-time provenance.

The pre-rebase identity gate found nine tag-dependent differences and 362 passes. The predecessor-label control reproduced all nine existing digests. The worker stopped at that gate and left the identity goldens for review on the merged tree. The exact sites and test results are in [the TE5 verification record](teacher-te5.md#part-d-verification).

## The owner-copy run (Nov 24 2026, orchestrator; counts and digest prefixes only)

The procedure above on backup-API copies of the three floor-set vaults, walked to `mvp-0.71` with this tip, then one
copy each upgraded to `mvp-0.72`. The copies were deleted afterwards; every original's `sha256sum -c` read OK.

| | vault 1 | vault 2 | vault 3 |
|---|---|---|---|
| attempts; lesson checks; weight trace rows | 3; 0; 0 | 70; 0; 0 | 3; 0; 0 |
| predecessor epochs: with a pair, without | 3, 1 | 70, 7 | 3, 0 |
| curves after the upgrade: reconstructed, missing, graded | 3, 1, 0 | 70, 7, 0 | 3, 0, 0 |
| expected snapshot digest = curves digest | yes (`d1b1c739`) | yes (`08431c96`) | yes (`16f0b678`) |
| curves digest after rebuild 1 and rebuild 2 | same | same | same |
| mastery, facet, surprise and item-state rows whose values changed | 0 | 0 | 0 |
| integrity; foreign-key violations; schema head | ok; 0; 274 | ok; 0; 274 | ok; 0; 274 |

- Between the `mvp-0.71` copy and its upgrade, only `algorithm_version` (and `updated_at` on facet recall rows) differs
  in `learning_object_mastery`, `facet_recall_state`, `facet_uncertainty` and `attempt_surprise`; `practice_item_state`
  is identical.
- **Not exercised here:** none of the three copies holds a lesson check, so the check, receipt, weight-state and trace
  digests are those of empty tables on both sides, and the label queries return no rows. The refit from frozen pairs
  ran on no owner data in this run; its evidence is the test suite. A vault with lesson checks should get this
  procedure again before its live upgrade.
- The doctor exits 1 on each copy on the content errors that predate this tag (see H3's record).

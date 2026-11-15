# Arc D close fixes, group 3: what a rebuild leaves behind (D-36, D-35)

Branch `fix/arc-d-close-3`, based on main `6fffbc20c8`. Investigation, then a stop: replay appends history, and two readers compute something different after a rebuild. One commit adds the fail-first tests (strict xfails); no source change. D-35 was not started (the brief's stop rule); its producer is located below.

| Row | Commit | Kind |
|---|---|---|
| D-36 | `9d5e4c89c1` | tests only: three strict xfails, the fail-first tests of the design handed back below |
| D-35 | none | not started; the clock-dropping producer is named below |

## D-36: each rebuild appends every practice answer's grade chain again

**Counts.** Live `learnloop rebuild-derived-state`, twice, each copy made with `learnloop.db.copies` (`copy_tree_with_databases`) under the worktree's `fixtures-local/`. Base code (this branch changes no source).

| Vault | Attempts | Table | Before | After 1 | After 2 |
|---|---|---|---|---|---|
| `fixtures/mvp017_route_check_replay`, copy retagged `mvp-0.58` | 18 | `activity_observations` | 65 | 82 | 99 |
| | | `raw_grade_events` | 65 | 82 | 99 |
| | | `grade_interpretations` | 65 | 82 | 99 |
| | | `measurement_events` | 265 | 333 | 401 |
| head-written synthetic vault (`tests/rebuild_equivalence_helpers._vault`, 17 self-graded answers) | 17 | `activity_observations` | 17 | 34 | 51 |
| | | `raw_grade_events` | 17 | 34 | 51 |
| | | `grade_interpretations` | 17 | 34 | 51 |
| | | `measurement_events` | 76 | 144 | 212 |
| owner copy `linear_algebra` (`mvp-0.58`) | 70 | `activity_observations` | 499 | 537 | 575 |
| | | `raw_grade_events` | 482 | 520 | 558 |
| | | `grade_interpretations` | 481 | 519 | 557 |
| | | `measurement_events` | 1,996 | 2,148 | 2,300 |
| owner copy `probability` | 3 | the four tables | 23 / 23 / 23 / 94 | 26 / 26 / 26 / 106 | 29 / 29 / 29 / 118 |
| owner copy `arxiv_v2` | 3 | the four tables | 21 / 21 / 21 / 90 | 23 / 23 / 23 / 98 | 25 / 25 / 25 / 106 |

`activity_administrations` does not grow (administrations are reused: 5, 8, 85, 2, 6). Every other table's count is equal after the second rebuild and the first, apart from the rebuild receipt (`derived_state_rebuilds`, one per rebuild) and the FTS5 shadow tables `source_block_fts_data` / `_idx`, whose segment counts move from rebuild to rebuild while `source_block_fts` itself is equal. The first rebuild of the fixture copy also migrates it and adds what the fixture's own test expects (one causal-hypothesis version, one `practice_item_state` row).

So the growth is one chain per re-applied practice answer, at every rebuild, on vaults written at the head as on old rows: 17 of the fixture's 18 attempts (the one whose grade contract is unrecorded is skipped), all 17 synthetic ones, 38 of `linear_algebra`'s 70, 3 and 2 (the rest are answers `_dual_write_grade_channel` skips: probe and exam answers, which their own paths write once, a grade whose contract is unrecorded, an item no longer in the vault; not broken down per copy).

**The code that appends.** `attempts/attempts.py:3263`: `_apply_attempt_in_transaction` calls `_dual_write_grade_channel` for every application, replay's (`replace_existing`) included. That calls `record_grade_dual_write` (`attempts/grade_resolution.py:565`) without an observation id, so `ensure_administration_identity` (`grade_resolution.py:529`) reuses the item's administration and appends a new observation (`substrate/activities.py:762` `append_observation`: the observation and a `response_appended` measurement event), and `resolve_grade` appends a raw grade event (`grade_resolution.py:188`), two measurement events (`raw_grade_appended`, `grade_classified`), an interpretation (`grade_resolution.py:275`), repoints the new observation's head, and a fourth measurement event (`grade_interpreted`). One observation, one raw event, one interpretation and four measurement events per answer: the 17 / 17 / 17 / 68 of the ledger row. The activity backfill is not it (`substrate/compat/activity_backfill.py:260` keys on an existing observation), and the bounded ledger read is not involved.

This is known in the code and the tests, and was taken as intended: `diagnosis/probe_episodes.py:2431` says "an ordinary practice answer's are re-minted by `attempts._dual_write_grade_channel` on every application", and `tests/test_mvp017_route_check_replay.py` compares `raw_grade_events` with `DISTINCT` because "every rebuild appends one event per replayed grade".

**What the tables are.** All four are `RAW_LEDGER` in `db/table_roles.py` (`activity_observations` line 88, `grade_interpretations` 320, `measurement_events` 440, `raw_grade_events` 535): history a rebuild never clears. Replay appending to them is the brief's stop condition, and against playbook item 2 (raw ledgers immutable; a new meaning is a reinterpretation event, not a second copy of the evidence).

**Repeats already in the owner's vaults** (rows equal to an earlier row of the same attempt but for surrogate ids and stamps; JSON payload keys ending in `_id` left out), on fresh copies of the base:

| Copy | Rebuild receipts | `activity_observations` | `raw_grade_events` | `grade_interpretations` | `measurement_events` | most observations of one attempt |
|---|---|---|---|---|---|---|
| `linear_algebra` | 58 | 388 of 499 | 406 of 482 | 387 of 481 | 1,626 of 1,927 | 15 |
| `probability` | 58 | 18 of 23 | 18 of 23 | 19 of 23 | 79 of 92 | 9 |
| `arxiv_v2` | 56 | 15 of 21 | 14 of 21 | 14 of 21 | 68 of 84 | 9 |
| the tracked `mvp-0.17` fixture | 2 | 47 of 65 | 45 of 65 | 46 of 65 | 187 of 260 | 4 |

(`measurement_events` here counts only events joined to an attempt's observation.) No owner copy holds a grade adjudication or a flagged or quarantined interpretation (0, 0, 0).

## The readers: what N rebuilds change

Every reader of the four tables, and what it sees:

| Reader | Reads | After N rebuilds |
|---|---|---|
| `db/stores/observation_ledger.load_authoritative_observation_ledger` (the canonical projection, `EffectiveObservation`, AD's material view, `field.outcomes.measurement_masses`) | each attempt's newest observation (`ROW_NUMBER() ... ORDER BY created_at DESC, id DESC`), its head, its newest adjudication | equal: the newest copy's values are the same as the last one's |
| `field/outcomes._grader_models` | the newest observation's raw events | equal |
| `router_objective/checks._quarantined` | the newest observation's head | equal |
| `Repository.latest_raw_grade_identity` (`attempts.py:1637`) | the newest primary raw event | equal (replay writes the same identity) |
| `goals/goal_contracts.py:833` (`observations_for_administration`) | all of an administration's observations, "terminal iff every one is" | equal (repeats do not change an "every") |
| `adaptive_difficulty/material_view.py:504` | attempts of an administration's observations, "withheld iff every one is" | equal |
| `Repository.observation_by_attempt` (contest flow `learnloop_sidecar/handlers/feedback.py:725`, `learnloop grading receipt`, `attempts/calibration_streams.py:140`) | `LIMIT 1` with no `ORDER BY`; the partial index `idx_activity_observations_attempt (attempt_id, created_at DESC, id DESC)` makes it the newest | equal, but by the query plan, not by the query (its docstring says "an attempt is replayed at most once") |
| `grade_resolution.resolve_grade`'s review check (`raw_grade_events_for_observation`) | the new observation's own events | equal |
| `Repository.pending_grade_reviews` (`learnloop grading reviews`) | every observation's head, any copy | **grows**: one row per rebuild for each flagged grade |
| an owner adjudication (`learnloop grading adjudicate`, `append_adjudication`) | written on the observation it names | **lost** after one rebuild: the rebuild's new observation, unadjudicated, is the one the ledger reads |
| `measurement_events` | `Repository.measurement_events_for_administration` has no caller | none |

Calibration (`grader_calibration`) reads calibration models and alphas, never raw grade events; no calibration row grows with a rebuild.

**Numbers.** On every copy the projections are equal after the second rebuild and the first: every `DERIVED` table, `practice_item_state` (due dates) and `practice_attempts` row for row with `created_at` / `updated_at` left out, and the authoritative ledger's per-attempt values (certainty bound, discount, review flag, quarantine, adjudication), on the fixture copy, the synthetic vault and the three owner copies. Mastery, facet state and due dates do not move. Two readers do:

- **Review queue**, synthetic vault with one self-grade at confidence 1 (grader confidence below 0.4, so `review_flag`): `pending_grade_reviews` returns 1 row before any rebuild, 2 after one, 3 after two, all for the same attempt. The owner copies hold no flagged grade, so their queue is empty at every step.
- **Adjudication**, a fresh synthetic vault: an answer graded `partial_success` (certainty bound 0.6958) confirmed by `learnloop grading adjudicate --resolved-class partial_success` (no direction flip, so no `grading_evidence` revision). Projected after the adjudication: the bound reads 1.0, and the facet row's direct positive mass moves 2.1743 -> 2.2314 and negative mass 4.6965 -> 4.7155. After one `rebuild-derived-state`: the ledger reads no adjudication, the bound is 0.6958 again, and the facet row equals the unadjudicated one. By reading (not run), a contest flag (`flag_observation_for_review`) behaves the same: the flag stays on the superseded observation, where the queue still lists it and where an adjudication from the queue never reaches the projection.

These are what the brief asks to be reported before any fix.

## Fail-first tests (`tests/test_rebuild_history_appends.py`, strict xfails)

On a head-written vault (`_vault` and `_answer` from `tests/rebuild_equivalence_helpers.py`, five graded answers), under a frozen clock. With `--runxfail` at this tip:

- `test_a_second_rebuild_appends_no_history_row`: every `RAW_LEDGER` table as a multiset of rows without surrogate ids and stamps, after one rebuild and after two: `{'activity_observations': 5, 'grade_interpretations': 5, 'measurement_events': 20, 'raw_grade_events': 5}` grown, expected `{}`.
- `test_the_review_queue_lists_a_flagged_grade_once_after_rebuilds`: `assert 3 == 1`.
- `test_an_adjudication_survives_a_rebuild`: the adjudication moves the facet row, then after one rebuild `active_adjudication` is `None`.

A fourth test (the contest flow finds the observation the projection reads) passed and was dropped: `observation_by_attempt` returns the newest copy through the index.

## Design handed back (D-36)

**What is appended, and why.** Replay re-applies each practice answer through the live write path, and the live path's grade-channel dual write mints a fresh observation and chain each time. The re-mint is how a rebuild re-interprets old grades under the current calibration and projection versions, and how a regrade's new grade reaches the channel (`probe_episodes.py:2431`; the probe path publishes its own regrade dual-write instead).

**Smallest fix (recommended).** On replay, `_dual_write_grade_channel` reuses the attempt's newest observation, its administration and surface (`record_grade_dual_write` already takes all three), and appends only what changed:

1. a raw grade event only when the grade differs from that observation's newest raw event (a regrade); otherwise none;
2. an interpretation only when it differs from the head (another calibration model hash or projection version); and not over an adjudicated, flagged or quarantined head unless step 1 appended (whether a regrade supersedes an adjudication of the old grade is an owner call);
3. measurement events only with an append.

With it a second rebuild appends nothing, the first rebuild of a head-written vault appends nothing, adjudications and flags survive, and a regrade still lands. No migration, no new table. Separately, `pending_grade_reviews` reads each attempt's newest observation (the ranked query `observation_ledger` already uses), which clears the queue's repeats in vaults already rebuilt with no cleanup, and `observation_by_attempt` gets the `ORDER BY` its callers rely on.

**Persisted meaning.** On a vault with no adjudication or flag (all three owner copies) no reader value moves: the projection reads the newest copy, which equals the last. On a vault with an adjudication made since its last rebuild, the fix keeps the adjudication the base code drops, so projected evidence differs from the base code's after a rebuild: by playbook item 1 that is a new tag (a `whole_vault_rebuild` link) unless the owner rules it an amendment of `mvp-0.59` like the two recorded ones, which the owner copies (no adjudications) would allow. The review-queue read is not persisted meaning.

**The alternative.** Skip the dual write on replay altogether, as the probe path does. Simpler, but a rebuild would no longer re-interpret old grades when calibration or the projection version moves, and the practice regrade would need its own dual write before its replay. More meaning changes; not recommended.

**Already-duplicated rows.** Doctor can see them with:

```sql
SELECT COUNT(*) - COUNT(DISTINCT attempt_id || '|' || role || '|' || grader_identity_hash || '|' ||
       raw_output_json || '|' || COALESCE(criterion_evidence_json, '') || '|' || observed_class)
  FROM raw_grade_events WHERE attempt_id IS NOT NULL;
```

(and the like for observations per attempt, interpretations through their raw event, and measurement events through their observation; the counts are in the repeats table above). A cleanup would delete, per attempt, every observation but the one the ledger reads whose raw event repeats one of the read observation's, with its interpretations and measurement events. It deletes rows of four `RAW_LEDGER` tables, which no rebuild may do, and `calibration_stream_samples` and `grade_adjudications` hold observation ids. Recommendation: no cleanup. With the fix and the queue read, the repeats are inert, and doctor reports their count. Not written in this step.

## D-35 (not started)

The brief's stop rule ("replay appends history") came first, so no D-35 change was made. Read-only, the producer that drops the clock: `substrate/replay.py:412`, `replay_learning_object`'s closing `project_canonical_facet_state(vault, repository)`. `rebuild_derived_state(clock=...)` (`replay.py:420`) never passes its clock down, and `replay_learning_object` has no clock parameter, so the direct path's closing projection stamps the wall clock. Also seen, and under the same rule: every rebuild rewrites `subject_identifiability_watermarks.checked_at` with the rebuild's clock (the identifiability replayer clears the table and upserts), so that table differs after the second rebuild and the first on every copy, by that stamp alone. Not done: the fix, the list of stamp readers, the umbrella's write-on-change, the strict xfail's removal.

## Ledger

D-35 and D-36 updated, with D-36's fail-first tests and the design above. New rows: D-52 (an adjudication is lost at the next rebuild) and D-53 (the review queue lists a flagged grade once per rebuild).

## Not verified

- The owner's live vaults (only the `mvp-0.58` copies). Adjudications or flags made in a live vault after those copies were taken would be lost at its next rebuild; the copies hold none.
- P-shadow with an upgrade, base against branch: the branch changes no source, so there is nothing to compare.
- The durability lane and the owner lane: no source and no owner-lane test changed.
- Whether sync, backups or exports grow with the repeats (they hold the rows; nothing was measured).
- The quarantine path (`quarantine_observation` has no caller outside tests); it would lose its quarantine at a rebuild the same way.

## Gates

`tests/test_rebuild_history_appends.py` (3 xfailed; 3 failed with `--runxfail`), `test_identity_pins`, `test_retired_config_identities`, `test_architecture`, `test_test_layout`, `test_effective_defaults_golden`, `test_cli_help_snapshot`, `test_structure_ratchets`, `test_mvp017_route_check_replay`, `test_rebuild_orchestrator`, `test_rebuild_equivalence`: 409 passed, 4 xfailed (`-n 6`). `scripts/affected_tests.py` on the diff selects only the new file. `lint-imports --no-cache`: 42 kept. `ruff check`: clean. The four vault validators pass (desktop reproducible byte for byte); `generate_all.py` after the test commit changed only the references (`282675c600`), and a second run changed nothing. `scripts/check_gate_partition.py`: 30,992 collected, landing 30,927 + arc_close 65.

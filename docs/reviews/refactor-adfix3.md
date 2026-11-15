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

# Step b: the fix as decided, stopped at the proof

Same branch, continued from `201e3ce999`. The orchestrator decided the design above (reuse the newest observation, append only on change), its own kill switch in `mvp-0.59`, the two reader fixes outside it, and D-35's rule (a rebuild does not re-stamp a cell whose value did not change). Everything below is committed and its tests pass; the proof on the owner copies then hit the brief's first stop condition (**reusing the newest observation changes DERIVED values on two owner copies**), so the docs, the vault references and the full affected sweep were not done. Section "The stop" has the numbers and the choices.

| Commit | Row | What |
|---|---|---|
| `c53b2650c2` | D-36 | the switch `replay.grade_channel_fixes` (default true): schema field, kill-switch row at `mvp-0.59`, registry rule, the one tag line `GRADE_CHANNEL_FIX_VERSIONS = FACET_BELIEF_FIX_VERSIONS`, the effective-defaults line, the retired-config digests' additions |
| `22ac042f67` | D-53 | `pending_grade_reviews` lists each attempt's newest observation's head; `observation_by_attempt` orders by `(created_at, id)` descending. Not behind the switch |
| `cf96a8c566` | D-36, D-52 | replay reuses the observation and appends only what changed, behind the switch |
| `414dbe47c7` | D-35 | the direct replay's closing projection takes the caller's clock |
| `5248ce8a36` | D-35 | a rebuild re-stamps no cell whose value it left as it was, on both paths |

## The switch and the tag

`replay.grade_channel_fixes`: the `[replay]` section is the one the config has for how replay writes and reads (there is no grade-channel section), and the `<thing>_fixes` name follows the two other fix groups in `mvp-0.59` (`facet_diagnostic.canonical_belief_fixes`, `probe.episode.robust_gate_fixes`). Its only reader is `attempts.grade_resolution.grade_channel_fixes_on(config)`, over the one tag set `algorithm_versions.GRADE_CHANNEL_FIX_VERSIONS`. Not a projection switch (`projection_switches` and doctor's stale-switch check do not name it): it changes what history a rebuild appends, and the projection reads the newest observation either way.

**To make it `mvp-0.60`** (if a vault reaches `mvp-0.59` before this lands):

1. `src/learnloop/algorithm_versions.py`: a constant `GRADE_CHANNEL_FIX_ALGORITHM_VERSION = "mvp-0.60"` with its comment after line 925, appended to `SUCCESSOR_CHAIN` after line 983, and line 1036 becomes `GRADE_CHANNEL_FIX_VERSIONS = successors_from(GRADE_CHANNEL_FIX_ALGORITHM_VERSION)`. No call site changes.
2. `src/learnloop/ops/upgrades.py` `UPGRADES`, after line 121: `Link(GRADE_CHANNEL_FIX_ALGORITHM_VERSION, whole_vault_rebuild)` (the first rebuild under it appends the re-interpretations "The stop" counts and moves the projection where it does); `tests/test_upgrades.py` `EXPECTED_ACTIVATIONS` (line 58) its row.
3. Text naming the tag: `config/kill_switches.py:137`, the schema comment above `config/schema.py:4513`, the registry rule `params/parameter_registry.py:2629`, the docstring of `grade_channel_fixes_on` (`attempts/grade_resolution.py:491`), the test module docstring of `tests/test_rebuild_history_appends.py`.
4. Goldens and pins as at `mvp-0.59`: the `algorithms.algorithm_version` line of `tests/goldens/effective_defaults.toml`, the identity pins that move by tag (`python tests/test_identity_pins.py --write`, with the reason), the version pins naming the latest tag (`test_facet_belief_successor.py`'s first test and its siblings).
5. `tests/test_rebuild_history_appends.py`: the floor twin's version becomes `FACET_BELIEF_FIX_ALGORITHM_VERSION`.

## D-36, D-52: what replay does now (`cf96a8c566`)

`attempts._dual_write_grade_channel`, on replay with the switch on, takes `Repository.observation_by_attempt` (the newest, the ledger's order) and calls `grade_resolution.record_replayed_grade` (fail-safe like `record_grade_dual_write`); with no observation, or switched off, or below the tag, it calls `record_grade_dual_write` as before. `resolve_grade` is split into `read_grade` (classification, calibration, posterior, certainty, LCB: no writes but the outcome schema's) and its appends, in the same write order; its output is unchanged (the grade-application goldens and identity pins pass).

- The comparison basis is the raw event the head interprets. **Regraded** when any of the raw event's columns but its ids, stamp and `agent_run_id` differ (`_RAW_GRADE_COLUMNS`; the run id names the live model run, which replay does not carry). Then a raw event, its two measurement events, an interpretation and `grade_interpreted` are appended to the observation, whatever the head.
- Otherwise an interpretation is appended only when it differs from the head on `_INTERPRETATION_COLUMNS`, and never when a review wrote the head: `Repository.grade_head_review` names an adjudication's result, a quarantined head, or a head an `interpretation_activated` event activated (the contest flag).
- An adjudication that flips the direction also writes a grading-evidence revision and the attempt's grade, so replay's grade differs from the raw event; when the current epoch is that adjudication's revision (`evidence = adjudicated:<id>`) it is not taken for a regrade.
- The review flag is the response's own (unclassifiable, low confidence), as on the fresh observation the predecessor minted: the observation's earlier raw events are grades this one replaced, not a second grader.

**Callers and siblings.** `_dual_write_grade_channel` is called from `_apply_attempt_in_transaction` only (live and replay); live writes are unchanged. Replay's entries: `rebuild_derived_state`, the umbrella, `regrade._publish_regrade` (its LO replay now appends the regraded answer's new grade to its observation, one raw event and interpretation, and nothing for the LO's other answers), `integration_backfill`. Other dual writers: the probe path and `publish_regraded_probe_grade` (write once, never on replay: unchanged), `exam_session` (own path), `_record_lesson_probe` (live only). Comments that said replay re-mints: `regrade.py` (above `publish_regraded_probe_grade`), `probe_episodes.publish_regraded_probe_grade`'s docstring, `_dual_write_grade_channel`'s docstring.

**Fail-first.** Each new on-switch test fails with the switch default flipped off (a temporary, uncommitted edit), which is the predecessor: a second rebuild grows the four tables by 5 / 5 / 5 / 20; the first rebuild of a head-written vault by the same; the queue test's observation count is 3; a regrade's LO replay grows by 8 chains; the projection-version change re-mints 5; the contest flag, the adjudication (twice) and the flipping adjudication are gone after one rebuild. The three strict xfails are gone. The switched-off and floor (`mvp-0.58`) twins assert the predecessor's growth exactly (one chain per answer per rebuild) and the adjudication's loss.

**Tests added** (`tests/test_rebuild_history_appends.py`): the first rebuild of a head-written vault appends no grade-channel row; off and at the floor every rebuild re-mints; the queue twice (switch on and off); a regrade then two rebuilds (one raw event and interpretation, at the regrade's own replay, on the same observation; nothing after); a projection-version change (one interpretation per answer, then none); a contest flag kept across two rebuilds; an adjudication kept across two rebuilds with the projection's values kept (and its switched-off twin, where it is lost); a direction-flipping adjudication kept. `tests/rebuild_equivalence_helpers._vault` takes a version. The first rebuild of a fresh vault also backfills activity cards and surfaces for the items nobody answered (5 tables, 6 rows each, both codes): those tests compare the grade channel's tables.

## D-53 (`22ac042f67`)

Fail-first, switch off (re-minted copies, as vaults rebuilt before the fix hold them): the queue listed 3 rows after two rebuilds; with the index `idx_activity_observations_attempt` dropped, `observation_by_attempt` returned the oldest copy. Readers of the two methods: `learnloop grading reviews` (`cli/grading.py:19`), `learnloop grading receipt` (`cli/grading.py:98`), the contest flow (`learnloop_sidecar/handlers/feedback.py:725`), `calibration_streams.py:140`, the activity backfill's idempotency key, the umbrella's accounting: all want the newest.

## D-35 (`414dbe47c7`, `5248ce8a36`)

**The clock.** `replay_learning_object` takes a `clock` and its closing projection uses it; `rebuild_derived_state`, the regrade's replay and the integration backfill's replay pass theirs. The six other callers of `project_canonical_facet_state` already passed one. Fail-first: under a frozen clock the direct rebuild left `2026-11-15T12:36:22Z` (the wall clock) on canonical rows.

**The rule.** Writing on change is not enough at the head: a learning object's replay folds the vault-wide canonical cache through each attempt's position (the bounded folds, the state its live write read) before its closing projection, so every cell is rewritten, or deleted and re-inserted, on the way; the umbrella also clears the three tables before projecting. Fail-first: on a head vault a second rebuild under a later clock re-stamped `facet_recall_state` and `facet_capability_evidence` on both paths (and `subject_identifiability_watermarks.checked_at` on the umbrella). The fix is local: each path snapshots the cells before (`Repository.rebuild_stamp_snapshot`: the direct replay per learning object, the three canonical tables, when it runs its closing projection; the umbrella once around every replayer pass, those and the watermarks) and gives each cell that ends with the same values the stamps it had (`keep_unchanged_rebuild_stamps`; a recall row's projected `created_at` counts as a value). The umbrella keeps its clears, so stale rows still go; changed, new and vanished cells keep what the rebuild wrote. Not behind the switch: stamps are not persisted meaning (the shadow rebuild and the equivalence tests leave them out), and the floor and switched-off runs below show it at both tags.

**Readers of the stamps.** `facet_recall_state.created_at` / `updated_at`: `learner/facet_state_reader._fold` folds them into `FacetRecallState` (min / max); no reader of `FacetRecallState.created_at` / `updated_at` was found (grep for attribute and key reads across `src/`), apart from `recall_coverage.build_facet_recall_updates_from_prior`, which copies `created_at` into legacy rows at `mvp-0.6` only. `facet_capability_evidence`: `FacetCapabilityEvidence` carries no stamp. `capability_residual_state`: the row dict carries them; its readers (`residual_diagnostics`, doctor) read none. `goals/certification_cold_probe.py:464` already dates a certificate from attempt times, not from `updated_at`. The AD column classes list them as columns only. Nothing orders, expires, syncs or displays by them; under the rule each says when its cell's value last changed, and "when was this rebuilt" is the receipt's (`derived_state_rebuilds`). `subject_identifiability_watermarks.checked_at`: no reader (doctor's identifiability check compares `registry_hash` only); treated by the same rule so a second rebuild changes nothing.

**The strict xfail.** `test_golden_projection_survives_one_umbrella_rebuild_exactly_and_stale_rows_clear` failed at the base on four tables: the canonical two (the dropped clock) and two the golden producer never produced (`hypothesis_recurrence_state`, `subject_identifiability_watermarks`, written only by umbrella replayers). It passes after the clock fix with the golden producer completed by those two replayers through their direct APIs (the recurrence groups refreshed before learner replay and again after it, as the umbrella reconciles them; the watermarks from the identifiability report). That is a judgment call: the assertion is unchanged and still covers every DERIVED table byte for byte; the test was comparing two tables against a producer that never wrote them.

## The proof, and the stop

Fresh backup-API copies (`copy_tree_with_databases`) under `fixtures-local/adfix3/`, since deleted. Four runs per vault: **base** (main `6fffbc20c8`'s source, run by `PYTHONPATH` from a `git archive` with its `migrations/`), **branch**, **floor** (branch code, left at `mvp-0.58`), **off** (branch code, `[replay] grade_channel_fixes = false`). Each: migrate, `learnloop upgrade --to mvp-0.59` (not for floor; its activation is a whole-vault rebuild), then `rebuild-derived-state` twice, a dump after each step. The `mvp-0.17` fixture copy was retagged `mvp-0.58` first. Counts of `activity_observations` / `raw_grade_events` / `grade_interpretations` / `measurement_events` (administrations never move: 5, 85, 2, 6):

| Vault | Run | Copy | Upgrade | Rebuild 1 | Rebuild 2 |
|---|---|---|---|---|---|
| fixture | base | 65 / 65 / 65 / 265 | 82 / 82 / 82 / 333 | 99 / 99 / 99 / 401 | 116 / 116 / 116 / 469 |
| | branch | same | 65 / 65 / 65 / 265 | same | same |
| | floor | same | (none) | 82 / 82 / 82 / 333 | 99 / 99 / 99 / 401 |
| | off | same | 82 / 82 / 82 / 333 | 99 / 99 / 99 / 401 | 116 / 116 / 116 / 469 |
| `linear_algebra` | base | 499 / 482 / 481 / 1,996 | +38 / +38 / +38 / +152 | +38 each | +38 each |
| | branch | same | 499 / 482 / **488** / **2,003** | same | same |
| | floor | same | (none) | +38 / +38 / +38 / +152 | +38 each |
| | off | same | +38 / +38 / +38 / +152 | +38 each | +38 each |
| `probability` | base, off | 23 / 23 / 23 / 94 | +3 / +3 / +3 / +12 | +3 each | +3 each |
| | branch | same | 23 / **24** / **24** / **97** | same | same |
| | floor | same | (none) | +3 / +3 / +3 / +12 | +3 each |
| `arxiv_v2` | base, off | 21 / 21 / 21 / 90 | +2 / +2 / +2 / +8 | +2 each | +2 each |
| | branch | same | 21 / **23** / **23** / **96** | same | same |
| | floor | same | (none) | +2 / +2 / +2 / +8 | +2 each |

("+n each": every step adds that many to each table again; "same": the count of the step before.)

Floor and off reproduce the investigation's counts exactly on all four (the fixture 65 → 82 → 99; +38, +3, +2 per rebuild on the owner copies). On the branch the four tables never grow at a second rebuild, nor at the first after the upgrade; the upgrade's own rebuild appends 7 interpretations (`linear_algebra`), one raw event and interpretation (`probability`), two of each (`arxiv_v2`), nothing on the fixture.

Base against branch after the upgrade and after each rebuild, every DERIVED table, `practice_item_state` and `practice_attempts`: on the fixture and `probability`, equal but for stamps (`facet_recall_state` 11 and 2 rows, `facet_capability_evidence` 4 and 1, `subject_identifiability_watermarks` 1: the base re-stamps them at every rebuild, the branch keeps them; and on the fixture one `practice_item_state` row, the one its first rebuild creates, stamped with each run's wall clock). Branch rebuild 1 against rebuild 2: every dumped table identical, stamps included, on all four (only the receipt and the FTS shadow segments move); likewise floor and off (D-35's rule is not gated).

**The stop.** On `linear_algebra` and `arxiv_v2` the branch's canonical facet state differs from the base's in value: `linear_algebra` 3 of 36 `facet_capability_evidence` rows (`direct_positive_mass`, `certification_credit`, `direct_certification_credit`) and 9 of 76 `facet_recall_state` rows (`recall_alpha`, `recall_mean`, `recall_variance`, `raw_coverage_mass`, 4 also `independent_evidence_mass`); `arxiv_v2` 2 of 2 and 4 of 4. `learning_object_mastery`, `practice_item_state` (due dates), `practice_attempts` and every other DERIVED table are equal.

The cause is a base defect the fix exposes, not the reuse itself. A live answer's dual write stamps its observation one to two seconds after the attempt row's `created_at`, while replay re-mints at the attempt's `created_at` (its frozen clock). For those attempts every base re-mint sorts *before* the live observation, so the authoritative ledger reads the live observation forever: the base never re-interprets them (and a practice regrade's grade channel never reaches the projection; its direction still does, through grading evidence). On the copies: 13 of 85 observed attempts in `linear_algebra`, 2 of 3 in `arxiv_v2`, 1 of 3 in `probability`, 0 of 18 on the fixture. The branch reuses exactly that observation (the newest by the ledger's order) and compares it with today's reading: for 7 of the 13 and both of `arxiv_v2` the calibration model has changed since the live grade, so it appends the current interpretation, and the projection moves; every attempt the branch appended to is one of these. For `probability`'s one and `arxiv_v2`'s two the raw event also differs, in `raw_output_json.max_points` only (live wrote the item's maximum, replay the cited contract's, which the regrade-contract successor made the classification basis; same observed class), so they count as regraded. On every other attempt the newest observation already held replay's chain and the branch appended nothing.

Choices (owner or orchestrator):

1. **Accept, recommended.** The branch's values are the ones the design intends (a rebuild re-reads every old grade under the current calibration); the base's are the defect's. The change lands in `mvp-0.59`'s activation (a whole-vault rebuild) and its counts are the table above. If a vault is already at `mvp-0.59`, apply the recipe above and it is `mvp-0.60`'s activation instead.
2. **Reproduce the base exactly.** Not possible without reproducing the defect: the branch would have to skip re-interpretation for exactly the attempts whose live observation sorts after replay's clock.
3. **Narrow the fix.** Keep the reuse but never append an interpretation-only re-reading (append only on a regrade): no value moves on the copies' re-interpreted attempts, but calibration and projection-version changes would never reach any attempt again, which the orchestrator ruled out.

Ledger D-54 records the defect; with choice 1 it is fixed by `cf96a8c566`.

## Adjudications made before the fix

A vault adjudicated and then rebuilt by the base keeps its adjudication on a superseded observation, unread after the fix too. Not repaired here (ledger D-55). Doctor could list them:

```sql
SELECT ga.id AS adjudication_id, o.attempt_id
  FROM grade_adjudications AS ga
  JOIN activity_observations AS o ON o.id = ga.observation_id
 WHERE o.attempt_id IS NOT NULL
   AND o.id <> (SELECT n.id FROM activity_observations AS n
                 WHERE n.attempt_id = o.attempt_id
                 ORDER BY n.created_at DESC, n.id DESC LIMIT 1);
```

No owner copy holds an adjudication.

## Other findings

- `tests/test_mvp017_route_check_replay.py` passes; at `mvp-0.59` on the branch a rebuild appends no raw grade event, so the `DISTINCT` it compares with collapses only the fixture's own earlier repeats (47 of 65), which are the same before and after: it no longer hides anything a rebuild adds. Assertion left as it is.
- The first rebuild of a freshly built vault backfills activity cards, card versions, families, family versions and surfaces for unanswered items (6 rows each on the synthetic vault); both codes; history a rebuild appends once, not per rebuild.

## Not done (the stop)

The playbook, Algorithm Versions / Version Registry notes and the vault's rebuild and replay notes; the vault references regeneration; `scripts/affected_tests.py` on the whole diff and its chunked sweep; the four vault validators; `check_gate_partition.py`; the owner lane. Done: `test_rebuild_history_appends` (13), the rebuild, regrade, grade-resolution, adjudication, grading-CLI, UX phase 4, projection, shadow and upgrade files (871 passed, 6 skipped, 4 xfailed), `test_identity_pins` and the other targeted gates (427 passed; no pin moved, no golden but the effective-defaults line changed, no ratchet rose), the durability lane on the four rebuild files (69 passed), `ruff check`, `lint-imports` (42 kept).

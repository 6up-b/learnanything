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

`attempts._dual_write_grade_channel`, on replay with the switch on, takes `Repository.observation_by_attempt` (the newest, the ledger's order) and calls `grade_resolution.record_replayed_grade` (fail-safe like `record_grade_dual_write`); with no observation, or switched off, or below the tag, it calls `record_grade_dual_write` as before. `resolve_grade` is split into `read_grade` (classification, calibration, posterior, certainty, LCB: no writes but the outcome schema's) and its appends, in the same write order; its output is unchanged (the identity pins pass; the grade-application golden's applications are unchanged, but its row record moves with the fix: step c, "The grade-application golden").

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

Ledger D-55 records the defect; with choice 1 it is fixed by `cf96a8c566`.

## Adjudications made before the fix

A vault adjudicated and then rebuilt by the base keeps its adjudication on a superseded observation, unread after the fix too. Not repaired here (ledger D-56). Doctor could list them:

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

# Step c: what D-36/D-52 move on the owner's copies, and the rest of the step

The orchestrator upheld the stop: the delta is the owner's to read before D-36 and D-52 land. This step adds the sizes (no behaviour changed) and finishes what the stop left. Fresh backup-API copies of the three owner copies under `fixtures-local/adfix3/`, each upgraded to `mvp-0.59` and rebuilt once by the base code and by this branch, compared by a read-only script (numbers and column names only; its raw output is the gitignored `fixtures-local/adfix3/deltas.md`, which the orchestrator copies out). The copies are deleted.

## The deltas, per vault

| | `linear_algebra` | `arxiv_v2` | `probability` |
|---|---|---|---|
| attempts with an observation | 85 | 3 | 3 |
| attempts the base never re-reads (D-55) | 13 | 2 | 1 |
| attempts the branch appends to (all among those) | 7: interpretation only | 2: raw event + interpretation | 1: raw event + interpretation |
| why | another calibration model than at live grading (model hash, reference priors, posterior, certainty, LCB, interval, influence flag; same fallback reason, same leading class) | `raw_output_json.max_points` (live: the item's maximum; replay: the cited contract's), and then another calibration model | `max_points` only; the interpretation equals the base's |
| attempts whose read interpretation differs from the base's | 7 | 2 | 0 |
| learning objects they belong to | 2 | 2 | 0 |
| canonical facets with a changed row | 3 | 2 | 0 |
| certainty LCB (the evidence-mass factor), branch − base | +0.3106 to +0.3317, all 7 up | +0.3267, both up | — |
| certainty (posterior), branch − base | +0.2775 each | +0.2775 each | — |
| leading true class or review flag changes | 0 | 0 | 0 |
| influence flag (certainty < 0.5) cleared | 7 | 2 | 0 |

Every changed reading is **more certain** than the one read today (9 up, 0 down): more mass, the same direction.

**`facet_capability_evidence`** (rows changed / |change| min, median, max / largest relative change; no sign changes):

| Column | `linear_algebra` (3 of 36 rows) | `arxiv_v2` (2 of 2) |
|---|---|---|
| `direct_positive_mass` | 3 / 0.1802, 0.3883, 0.3883 / 39.0% | 2 / 0.0092, 0.0098, 0.0105 / 88.5% |
| `certification_credit`, `direct_certification_credit` | the same | the same |
| `direct_negative_mass` | unchanged | 2 / 0.0276, 0.0295, 0.0315 / 88.5% |

**`facet_recall_state`**:

| Column | `linear_algebra` (9 of 76 rows) | `arxiv_v2` (4 of 4) |
|---|---|---|
| `recall_mean` | 9 / 0.0033, 0.0170, 0.0525 / 8.7% | 4 / 0.0043, 0.0046, 0.0049 / 1.0% |
| `recall_alpha` | 9 / 0.0249, 0.1802, 0.3883 / 25.3% | 4 / 0.0092, 0.0098, 0.0105 / 1.0% |
| `recall_beta` | unchanged | 4 / 0.0276, 0.0295, 0.0315 / 3.0% |
| `recall_variance` | 9 / 0.0007, 0.0028, 0.0102 / 15.1% | 4 / 0.0010, 0.0011, 0.0011 / 1.4% |
| `independent_evidence_mass` | 4 / 0.3106 each / 80.6% | 4 / 0.0368, 0.0394, 0.0420 / 88.5% |
| `raw_coverage_mass` | 9 / 0.0995, 0.3106, 0.7207 / 80.6% | 4 / as `independent_evidence_mass` |
| `consecutive_failures` | unchanged | unchanged |

**Boundaries checked**, base against branch, every cell, LO or facet: the Demonstrated flag (`certification_credit >= 1.0`, `goals.certification`): **1 cell crosses on `linear_algebra`, 0.9946 → 1.3829 (one facet's capability becomes Demonstrated)**, none elsewhere; credit > 0 (the coverage rollup): 0; the facet labels (`facet_state_label` through `mastery_diagnostic_view`, unexamined / uncertain / known_gap / solid, which threshold `independent_evidence_mass` against `recall_coverage.min_facet_evidence_mass`): 0 change; LO certification (`lo_certification`, the goal check and the headline's demonstrated class): 0 of 21 / 34 / 18; the Today headline (`classify_learning_objects`, `today_headline` at a fixed time): 0; LO blueprint readiness (the goal banner and recipe tree): 2 and 1 LOs, by at most 0.0094 and 0.0081, no bottleneck facet changes; the follow-up cold start (sums `independent_evidence_mass` per LO against `followups.cold_start_min_lo_evidence`): not computed separately, the mass moves up only. No product decision thresholds `recall_mean` itself (the router and Ready blend it continuously); as a size, 1 row crosses 0.6 and 2 cross 0.7 on `linear_algebra`, none on `arxiv_v2`.

**Equal**: of the 29 tables compared (every DERIVED table, `practice_item_state`, `practice_attempts`), 26 are byte-equal base against branch on every copy (641 / 4,693 / 1,833 rows, `probability` / `arxiv_v2` / `linear_algebra`), among them `learning_object_mastery` and `practice_item_state` (due dates); `subject_identifiability_watermarks` differs by its stamp; the two canonical tables as above (by stamps only on `probability`). No due date and no mastery value moves, so nothing in the due queue.

**What a learner would see** (the sidecar's own handlers run on both copies, numbers compared leaf by leaf):

- **Knowledge model** (`get_knowledge_map`): `linear_algebra` 23 of 3,468 numbers move: `predictedCorrect` on 11 items by at most 0.0245, `ready` on 3 facets by at most 0.0254, `readyGhost` 3 by 0.0383, `readyVariance` 3 by 0.0082, `evidenceMass` 2 by 0.3106, one `delta` by 0.0249. `arxiv_v2` 11 of 2,523: `ready` 2 by 0.0025, `readyGhost` 2 by 0.0049, `predictedCorrect` 3 by 0.0023, `evidenceMass` 2 by 0.042, `readyVariance` 2 by 0.0011. `probability`: none.
- **Facet detail** (`get_facet_detail`, Ready and the capability ledger): 3 facets on `linear_algebra` (Ready by at most 0.0074, evidence mass by 0.3106, **one capability's Demonstrated flag false → true**), 2 on `arxiv_v2` (Ready by 0.0085, evidence mass by 0.042, no flag), none on `probability`.
- **The evidence timeline's Demonstrated** (`facet_evidence_timelines`): 3 facets' latest value on `linear_algebra` (max 0.3883; the same facet's curve crosses 1.0, 0.9946 → 1.3829; 16 points differ), 2 on `arxiv_v2` (max 0.0105), none on `probability`. The session learning diff and "since last time" read these curves, so they show the same moves.
- **Today**: the headline and the LO classes do not move. The scheduler's selection reads `predicted_facet_recall` continuously (the `predictedCorrect` moves above); I did not build a Today plan on the copies, so whether an item's rank changes is not determined.
- The review queue's order reads the influence flag: 9 grades lose it, but none of them is flagged for review, so the queue is empty on every copy either way.

## D-55 for the owner

Since `mvp-0.8` (commit `02c3e6e10f`, 2026-07-21, which added the grade channel's dual write; the code tagged `pre-floor` has it), every answer's attempt row and its grade observation are stamped by the wall clock at whole seconds, in one transaction, with the observation written last. When that transaction crosses a second boundary, the observation is stamped one or two seconds after the attempt. A rebuild re-mints the observation at the attempt's own time, so for those answers every re-mint sorts before the live observation, and the projection, which reads each answer's newest observation, kept reading the one written when the answer was graded. A rebuild has therefore never re-interpreted those answers under a newer calibration model (13 of 85 answers on `linear_algebra`, 2 of 3 on `arxiv_v2`, 1 of 3 on `probability`), and a practice regrade of one of them would have reached the projection's grade channel only through its grading-evidence direction, not through its interpretation. On the three copies that second fault did no harm: 8 answers were regraded (7, 1, 0), 1 of them is such an answer, and every answer's read grade channel carries its current score at the base (0 of 91 differ, base and branch alike). Nothing else reads the observation's order: mastery, due dates, every other derived table and the review queue are unaffected. With D-36's fix those answers are re-read once, at the first rebuild under `mvp-0.59`, which is what moves the facet cells above.

## The rest of the step

See the gates below.

## The grade-application golden

Step b's record said the grade-application golden passed; it was not in step b's targeted run, and the sweep below found it moved. `tests/goldens/grade_application/history.json` pins every `AttemptApplication` of one graded history (live and in a rebuild) and every row each phase adds or removes, table by table, with ids numbered in order of first appearance. With the fix:

- **The applications are unchanged**: live, byte for byte; the rebuild's 18, byte for byte once ids are compared by place (fewer ids are minted, so every later `<ulid:n>` and `<uuid:n>` number shifts; that renumbering is also the whole difference in `judgment_ledger` and every other table not named here).
- **The grade channel's rows** are what the fix changes. Live (the history includes a regrade, which replays its learning object): `activity_observations` 26 → 11 added, `raw_grade_events` and `grade_interpretations` 26 → 12 (one per answer and the regrade's new grade), `measurement_events` 104 → 47. In the rebuild: 18 / 18 / 18 / 72 re-minted rows → 1 raw grade event, 1 interpretation and 3 measurement events, for the one answer whose grade an adjudication's correction revised without an adjudication head (`self`: `raw_output_json` and `criterion_observed_classes_json` differ, a changed grade by the rule), and that observation's row rewritten (its head repointed, a remove-and-add in the record).
- **The canonical facet rows** are rewritten fewer times (live 3 → 2 and 9 → 6, rebuild 4 → 1 and 11 → 2 remove-and-add pairs), by D-35's rule; the net change of their values in each phase is identical.

Regenerated deliberately (`GRADE_APPLICATION_GOLDEN_WRITE=1`) in `5be5bcf816`, as the test's own docstring says a change meant to change what is written does. The due-queue and figure goldens and the identity pins do not move. This is a golden the brief's stop list names: the orchestrator decides whether the regeneration stands.

## Gates (step c)

- `scripts/affected_tests.py --base 6fffbc20c8`: the full suite (`db/repositories.py` is imported by `tests/conftest.py`). Run as 15 chunks of up to 100 of the 1,428 test files at `-n 4 -m "not arc_close"`, each behind `flock /tmp/learnloop-fullsuite.lock`, in a 5 GB scope through the empty-home wrapper: **30,766 passed, 103 skipped, 11 xfailed, 0 failed** (chunk 5 first failed on the grade-application golden, above; rerun after its regeneration, 1,517 passed).
- Owner lane: copies made with the gate's `owner_copy_make.py`, `-m owner_vaults` over the 31 files that use the marker: 92 passed, 8 skipped (copies the set does not hold: `conic-sections`, `linear_algebra_legacy`, `arxiv` ×2; `test_why_real_cases` cases 1-4 need a backup newer than the copies'). Copies deleted.
- `scripts/check_gate_partition.py`: 31,005 collected, landing 30,940 + arc_close 65. `ruff check` clean; `lint-imports --no-cache` 42 kept.
- Docs: the playbook's `mvp-0.59` amendments, the Algorithm Versions and Reproducibility note and the Version Registry say `mvp-0.59` also holds the grade channel fixes; the rebuild workflow note says what a rebuild now appends and that unchanged cells keep their stamps. No vault note said replay re-mints the grade channel.
- The vault references are regenerated once after these commits, and a second run changes nothing (next commit).

# Step d: `mvp-0.60`, no kill switch, ready to land

The owner, 2026-11-17: "I accept the rebuild fix's value changes, ship it as mvp-0.60". One of the owner's vaults is already at `mvp-0.59`, so the fix cannot amend that tag; and by the owner's rule of 2026-11-16 a new successor ships without a kill switch. This step merges main, gives the fix its own tag, removes its switch, and re-runs the owner-copy check on the final code.

| Commit | What |
|---|---|
| `6392f6a938` | merge main `c1e3706164` |
| `7ba9105988` | the merge's follow-up: two of the branch's edits to code main moved, and the renumbered rows in the record and the Algorithm Versions note (the merge commit's index left these four files out) |
| `01cb5925af` | the tag `mvp-0.60`, its upgrade row and test row, and the pins that name the newest tag |
| `005bbfa9b3` | the kill switch `replay.grade_channel_fixes` removed |
| `24a625b404` | the diagnosis journey golden: the decision state's config hash after the switch's removal |
| `dedadedab5` | what the affected sweep found: the joint-grading builders' golden (main's) at `mvp-0.60`, and one more facet-belief test that reads its row's tag |
| (the next commit) | the record, the ledger, the docs |

## The merge

37 files conflicted. 33 are generated vault references; every reference note the branch had changed (51) takes main's side, to be regenerated at landing (`Reference/Version Registry.md` is hand-written: taken from main and then edited for `mvp-0.60`, below). The other four:

- `docs/reviews/refactor-bug-ledger.md`: main has its own D-54 (a fork flake in `test_apply_recovery`). Both sides kept; this branch's D-54 and D-55 are renumbered (below).
- `src/learnloop/attempts/regrade.py`: one comment; main renamed "the joint door" to "the vault door", the branch rewrote the comment's last sentence. Both kept.
- `src/learnloop/diagnosis/probe_episodes.py`: main split the module. The branch's one edit there, the docstring of `dual_write_regraded_probe_grade`, is made where the function now lives, `diagnosis/probe_evidence.py`.
- `src/learnloop/db/repositories.py`: main moved the activity methods to `db/stores/activity.py`. The conflict was the moved block, which held one of the branch's changed methods.

The branch's changes to `repositories.py`, checked against `git diff 6fffbc20c8 6ea1d8d6ca` method by method, and where each lives at the tip:

| Branch change | Lives in |
|---|---|
| `_RebuildStamps`, `_REBUILD_STAMPED_TABLES`, `CANONICAL_STAMPED_TABLES`, `REBUILD_STAMPED_TABLES` (D-35) | `db/repositories.py` (module level) |
| `Repository.rebuild_stamp_snapshot`, `Repository.keep_unchanged_rebuild_stamps` (D-35) | `db/repositories.py` |
| `Repository.grade_head_review` (D-36, D-52) | `db/repositories.py` |
| `Repository.pending_grade_reviews`, newest observation's head only (D-53) | `db/repositories.py` |
| `Repository.observation_by_attempt`, `ORDER BY created_at DESC, id DESC` (D-53) | `db/stores/activity.py` (`ActivityStoreMixin`), the same edit |

Line counts agree: the branch changed `repositories.py` by +135 / -4; at the tip `repositories.py` +128 / -2 and `stores/activity.py` +7 / -2 against main. Every other file the branch changed merged cleanly with its diff against main unchanged in size. No conflict marker is left in the tree.

## Renumbered ledger rows

Main's next free D-numbers: this branch's D-54 (the live observation a re-mint never supersedes) is now **D-55**, and D-55 (adjudications made before the fix) is now **D-56**, in the ledger (rows and D-36's reference), steps b and c of this record and the Algorithm Versions note. No code or test named them.

## The tag

The recipe of step b, "To make it `mvp-0.60`", as written: `GRADE_CHANNEL_FIX_ALGORITHM_VERSION = "mvp-0.60"` with its comment, appended to `SUCCESSOR_CHAIN`; `GRADE_CHANNEL_FIX_VERSIONS = successors_from(it)`; `UPGRADES` gains `Link(GRADE_CHANNEL_FIX_ALGORITHM_VERSION, whole_vault_rebuild)` and `tests/test_upgrades.py`'s `EXPECTED_ACTIVATIONS` its row. The activation is a whole-vault rebuild under the tag, as for `0.58 -> 0.59`: its first rebuild re-reads the answers whose live observation earlier rebuilds never superseded (D-55), which moves canonical facet cells. A vault at `mvp-0.58` walks both rows (the upgrade table's `test_the_floor_reaches_each_tag_through_the_table` runs `0.58 -> 0.60` and checks both receipts; the owner copies below did the same). The `mvp-0.59` activation runs below the new tag, so it re-mints each answer's chain once, as `mvp-0.59` always did; the `mvp-0.60` activation then reuses the newest observation.

What names the newest tag followed, by the playbook's rules:

- `tests/goldens/effective_defaults.toml`: the `algorithms.algorithm_version` line.
- `tests/cli_surface.json`: `upgrade --to`'s default (the same line `--write` produces).
- The latest-tag and chain-position pins in 37 earlier successors' test files, mechanically: each negative chain index one further, `"mvp-0.60"` where they pin the latest and appended to the chain tails and version sets they pin, new vaults' tag. `test_facet_belief_successor`'s first test says `mvp-0.59` is now the second-to-last tag, and three tests that read the tag a facet-uncertainty row carries (two there, one in `test_facet_belief_successor_derivation`, `dedadedab5`) now set their vault to that successor's tag (a vault at the latest stamps `mvp-0.60`).
- `tests/goldens/placement_stored_misses.json`: the manifest's tag.
- `tests/fixtures/diagnosis_journey_golden.json`: 303 tag strings and the decision state's config and snapshot hashes, nothing else (regenerated with `DIAGNOSIS_JOURNEY_WRITE_GOLDEN=1`).
- `tests/goldens/identities.toml`: the five identity pins computed on a new vault at the head moved (`A1-A4.manifest_hash.init`, `C3.boundary.init`, `C3b.chooser`, `C5.init`, `C6.init`); with the chain cut back to end at `mvp-0.59`, all 340 pins hold, so the tag alone moves them. Regenerated with `tests/test_identity_pins.py --write`.
- The templates (`config.template`), new vaults and the default test vault follow `LATEST_ALGORITHM_VERSION` with no edit; `fixtures/migration_head` (at `mvp-0.6`, below the floor) has no tag expectation that moves.
- `tests/test_upgrades.py::test_a_jump_is_refused_and_nothing_changes` took "the tag below the link's predecessor" for "a vault below the floor", true only for the first row; it now takes the tag below the floor, as its comment says (judgment call; for the `mvp-0.59` row the vault is the same).

## No kill switch

Removed: the field `ReplayConfig.grade_channel_fixes` and its comment, its row in `config/kill_switches.py`, its registry rule, its `effective_defaults.toml` line, and the two retired-config identity additions (`ADDED_SINCE_BASE`, `ADDED_SINCE_SWITCHES_BASE`). The field was never on main: no identity pin moved with its removal, and `test_retired_config_identities` holds at main's lists. `grade_resolution.grade_channel_fixes_on` reads the vault's tag and nothing else. Below the tag the predecessor's path is untouched: replay calls `record_grade_dual_write` exactly as before. 11 files, +40 / -57 (comments and docstrings that named the switch now name the tag: `algorithm_versions.py`, `attempts.py`, `regrade.py`, `probe_evidence.py`).

Tests (`tests/test_rebuild_history_appends.py`): every switched-off arm moved to a vault below the tag, where it proves the predecessor is kept, which the tag arm does not: the review queue twin (`[mvp-0.59]`, re-minted copies listed once), the adjudication twin (`[mvp-0.59]`, the adjudication lost and the facet row the unadjudicated one, exactly), the observation read whatever the query plan (re-minted copies). The re-mint test runs at the floor `mvp-0.58` and at `mvp-0.59`, the two tags a vault below the fix can hold, in place of "switched off" and one tag; its assertions (one chain per answer per rebuild, exactly) are unchanged. No assertion was loosened. Removing the field also moved one line of the diagnosis journey golden (the decision state's config hash, `24a625b404`).

## The golden

`tests/goldens/grade_application/history.json` did not change on main since this branch's base (`git diff 6fffbc20c8 c1e3706164` on it is empty), and it passes at the tip unregenerated, at `mvp-0.60`. So every difference from main's version is the fix's, as step c accounts for them ("The grade-application golden"); nothing comes from main.

One golden that main added since this branch's base did move: `tests/goldens/joint_grading_builder.json` (D7's builders of joint grades), whose history includes a regrade that replays its learning object. At `mvp-0.60` its `raw_grade_events` go from 29 rows to 7: every row left equals one of main's but for id numbering, and the 22 gone are the replays' re-mints. Every other table it pins (8) is equal but for id numbering. With `GRADE_CHANNEL_FIX_VERSIONS` emptied (a temporary, uncommitted edit) main's golden holds exactly, so the fix alone moves it. Regenerated from the test's own rows (`dedadedab5`).

## The owner-copy check on the final code

The Nov 12 backup-API copies (`mvp-0.58`), copied again with `copy_tree_with_databases` under `fixtures-local/adfix3c/` (deleted afterwards). Five runs per vault: (i) **base**, main `c1e3706164` (its `git archive`, `src` first on the path, its `migrations/`), upgraded to `mvp-0.59` and rebuilt once; (ii) **branch at 0.60**, upgraded `0.58 -> 0.59 -> 0.60` and rebuilt once; (iii) **branch at 0.59**, upgraded to `mvp-0.59` and rebuilt once; (iv) (ii) rebuilt a second time; (v) base and branch left at `mvp-0.58`, rebuilt once. Every DERIVED table, `practice_item_state` and `practice_attempts` dumped after each step and compared, and the step-c deltas script (`ll_deltas.py`, unchanged but for leaving each row's `algorithm_version` out of the value comparison) run on (i) against (ii). Rows at `mvp-0.60` carry the tag in their `algorithm_version` column (8 tables); the comparisons of (ii) with (i) read it as `mvp-0.59`.

| | `linear_algebra` | `arxiv_v2` | `probability` | accepted (step c) |
|---|---|---|---|---|
| attempts the `mvp-0.60` rebuild appends to | 7, interpretation only | 2, raw event + interpretation (`max_points`) | 1, raw event + interpretation (`max_points`) | the same |
| attempts whose read interpretation differs from the base's | 7 (2 LOs) | 2 (2 LOs) | 0 | the same |
| `facet_capability_evidence` rows with a value change | 3 of 36 | 2 of 2 | 0 of 1 | the same |
| `facet_recall_state` rows with a value change | 9 of 76 | 4 of 4 | 0 of 2 | the same |
| Demonstrated crossings | 1 (0.9946 -> 1.3829) | 0 | 0 | the same |
| every column's rows changed, min / median / max, largest relative change, sign changes | as step c's tables, digit for digit | as step c's tables | none | the same |
| direction | every changed reading more certain (LCB up 7 of 7, +0.3106 to +0.3317) | up 2 of 2 (+0.3267) | | the same |
| every other dumped table, (ii) against (i) | equal (`subject_identifiability_watermarks` by its stamp) | equal (the same) | equal (the same; the canonical two by stamps) | the same |
| (iii) at `mvp-0.59` against (i) | values equal; the canonical two and the watermarks by stamps | the same | the same | must equal |
| grade-channel counts, (iii) against (i) | equal (575 / 558 / 557 / 2,300) | equal | equal | |
| (iv) second rebuild at `mvp-0.60` | no row and no count changes (only the receipt and the FTS segments) | the same | the same | no growth |
| (v) at `mvp-0.58`, branch against base | values equal; stamps as (iii) | the same | the same | |

What a learner would see matches step c too: the knowledge map changes 23 of 3,468 numbers on `linear_algebra` and 11 of 2,523 on `arxiv_v2` (none on `probability`), the same fields and counts; its largest `ready` change reads 0.0253 and 0.0024 here against 0.0254 and 0.0025 in step c, which is the read time (Ready decays with the clock; the facet detail's largest Ready change, read the same way, is 0.0074 and 0.0085 in both). Facet detail, the evidence timeline (16 and 2 points), LO certifications (0), the Today headline (0), blueprint readiness (2 and 1 LOs, by 0.0094 and 0.0081) and the diagnostic labels (0) are identical to step c's.

The grade-channel counts differ from step c's, as they must: the `mvp-0.59` activation now runs below the fix and re-mints each answer once (+38, +2, +3 chains), then the `mvp-0.60` activation appends the re-readings (`linear_algebra` 537 / 520 / 526 / 2,155 observations / raw events / interpretations / measurement events; `arxiv_v2` 23 / 25 / 25 / 104; `probability` 26 / 27 / 27 / 109), and a further rebuild adds nothing.

The stamps of (iii) and (v): the canonical cells and the watermark differ between the base and this branch below the tag because D-35's rule (a rebuild keeps the stamps of a cell it left unchanged; step b) is not gated by the tag, and the two runs ran at different wall-clock times; the values are equal. D-35 was fixed on this branch in step b and is not part of the tag's meaning (stamps are not persisted meaning).

## Docs

The playbook's `mvp-0.59` amendments paragraph is main's again, with one sentence saying the grade channel fixes became `mvp-0.60` the way it describes, without a switch. The Algorithm Versions and Reproducibility note's `mvp-0.59` row is main's again, and a `mvp-0.60` row, the successor sets and the upgrade table (two rows) say what the tag holds; the Version Registry names `mvp-0.60` and the two rows; the rebuild workflow note says the fixes start at `mvp-0.60` with no switch and what the upgrade's rebuild re-reads. Each of the three notes' `implementation_version` is `mvp-0.60`.

## Ledger

D-36 and D-52: fixed at `mvp-0.60` when this branch lands. D-35 and D-53: fixed, as in step b (D-53's test id is now `[mvp-0.59]`). D-55: fixed with D-36, the owner having accepted the re-reading as `mvp-0.60`'s activation. D-56: open (arc D close), as in step b.

## Tests (step d)

All through the worktree's isolated wrappers, each in a 5 GB scope, `-n 3`, one command at a time.

- Named: `test_rebuild_history_appends`, `test_rebuild_orchestrator`, `test_upgrades`, `test_identity_pins`, `test_retired_config_identities`, `test_structure_ratchets`, `test_architecture`, `test_cli_help_snapshot`, `test_diagnosis_journey_golden`, `test_grade_application_golden`, with `test_joint_grading_builder`, `test_effective_defaults_golden`, `test_kill_switches`, `test_test_layout`: **545 passed** at the tip (the first run, before `24a625b404`, failed the journey golden's `fg1_wait` on the config hash).
- `scripts/affected_tests.py --base main` answers `tests` (`db/repositories.py` is imported by `tests/conftest.py`), so the sweep is every `tests/test_*.py` naming rebuild, replay, regrade, grade_resolution, grade_interpretation, raw_grade, algorithm_version, upgrade or SUCCESSOR: 622 files in 11 chunks of at most 60, `-m "not arc_close"`: **19,328 passed, 69 skipped, 8 xfailed, 2 failed** (`test_facet_belief_successor_derivation::test_s1_explicit_criterion_targets_place_the_uncertainty_without_an_items_map`, `test_joint_grading_builder::test_the_builders_rows_match_their_golden`; both fixed in `dedadedab5`); the two failing chunks rerun after it: **2,485 passed, 11 skipped, 2 xfailed**.
- Durability: the five rebuild and upgrade files with `--durable-sqlite`: **152 passed, 1 xfailed**; `-m durability` on them: 2 passed.
- `ruff check`: clean. `lint-imports --no-cache`: 42 kept, 0 broken. `scripts/check_gate_partition.py`: 31,066 collected, landing 31,001 + arc_close 65.

## Not verified

- The vault references are not regenerated, and the vault validators were not run (the orchestrator regenerates at landing).
- The owner lane (`-m owner_vaults`) and the whole suite (the landing gate's); the owner-copy check above covers the three copies' rebuilds.
- The `mvp017_route_check_replay` fixture's live rebuild at `mvp-0.60` (step b ran it at the tag then called `mvp-0.59`; `test_mvp017_route_check_replay` is in the sweep below).

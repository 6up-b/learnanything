# Router speed stage 2: the Codex review and its fixes (`router/ro-speed2`)

Codex reviewed the stage at `a95e354cf3` (gpt-6.1-sol; job `20261107-030149-8GoJF9`). It raised two Medium findings
(F1 and F2), one Low finding (F3) and three claims that don't hold. All three findings reproduced here first, each
with a failing test, and all three are fixed. No finding was High. Fakes only: no paid call and no model request. No
owner vault or tracked working vault was opened. Every script outside pytest ran under `env -i` with an empty `HOME`,
`CODEX_HOME` and `LEARNLOOP_CONFIG_DIR`.

## Findings

| Id | Severity | Title | Verdict | Commit | Test or reason |
|---|---|---|---|---|---|
| F1 | Medium | Cache hits miss source edits committed during a map walk | **fixed** | `e820e07988` | `tests/test_rospeed2_section_map.py::test_a_source_edit_committed_between_two_held_reads_of_one_map_is_read[canonical_uri, alias]` (both failed on `a95e354cf3`) |
| F2 | Medium | Connection pooling changes deadline-bound choices without serving versioning | **fixed** (two kill switches, generator payload, prefetch key; no algorithm version, as stage 1's F1 ruling) | `e820e07988` | `tests/test_rospeed2_connections.py::test_the_pool_completes_more_draws_by_one_deadline_and_switched_off_is_mains`, `test_the_pool_and_the_held_map_follow_their_switches`, `test_switched_off_the_job_opens_a_connection_at_every_connect`; `tests/test_rospeed2_section_map.py::test_switched_off_the_map_is_mains_and_reads_nothing_of_the_hold`; `test_rofu_generator_switches`, `test_rofu_switch_key` (parametrized over the switch list), `test_rofu_successor` |
| F3 | Low | Fingerprint encoding loses text after embedded NULs | **fixed** | `e820e07988` | `tests/test_rospeed2_section_map.py::test_an_embedded_nul_in_a_stored_cell_is_part_of_the_held_key` (failed on `a95e354cf3`: 6 distinct digests of 8 cells) |

### F1: a held lookup re-reads the reading's metadata first

**Reproduced.** The test vault gains the book's canonical note (`note_book`) and a reference from `lo_m5` to unit u4
through it (by quote, no source id), so the source's stored canonical URI decides whether u4 maps to `lo_m5`. Every
mapping is held first. A new map then reads u0, a write commits on another connection, and the map reads every
other section and span. With the canonical URI edited, main mapped `ext_m1/u4` and its spans to
`[lo_m3, lo_m4, lo_m5]`; the branch returned the held `[lo_m3, lo_m4]`. With a manual alias recorded onto the
reading, main mapped u3 and its spans with `lo_m0`, while the branch did not. This is Codex's case.

**Why.** Main loads a reading's IR once per map (`_irs`), but `learning_objects_for_section_in_ir` reads the reading's
run, revision and source, and the aliases onto it (`span_reanchors_between`), at every mapping. The held map read
its key once per map and reading, and a hit skipped `_holdable`.

**Fixed.**
- Before every lookup that main would compute (a section or span not yet mapped in this map),
  `VaultReadingMap._still_keyed` checks that the reading's metadata and aliases still equal its key's. The
  reading's first lookup in a map is exempt, because its key was read for it.
- Once they differ, the map maps that reading through main's own calls (`learning_objects_for_section_in_ir` /
  `learning_objects_for_span_in_ir`) for the rest of the map, over the IR it loads once, as main does. Nothing more
  of that reading is held, so nothing computed from the edited rows is published under the earlier key. The test
  undoes the edit after each walk and checks that the earlier key serves main's values.
- **Cost.** The check is a database commit version (`reading_cache.commit_version`: `PRAGMA data_version` of a
  read-only watcher, the pattern of `objective_inputs._DecisionReads.version` and `reading_choice.fingerprint`). It
  is read before the key and before each re-read. A lookup after no commit anywhere needs no read. After any commit,
  the metadata digest is read again and compared. The watcher runs only that pragma, in autocommit, so it holds no
  lock and no snapshot. One watcher per database is shared under a lock, so it never crosses a thread unlocked. It
  reads no table, so the AD guard has nothing of it to check.
- **Without the version** (the first fix, a digest at every lookup), the `la` job rose from 1396 to 1590 ms and the
  join outside a job from 115 to 666 ms (276 metadata digests a job, each opening a connection outside the pool).
  The timings below are with the version.
- **Main's per-map IR is kept.** One race remains, and it can't arise in production: a completed reading's stored
  structure rewritten in place between a map's first held lookup and its first computed one. The full key is
  verified after that computation, so nothing would be held from it. Readings never change once completed
  (`span_aliases._computed` relies on the same fact), so the race needs a write the system does not make.

### F2: both items are serving changes, each behind its own switch

**Reproduced.** The test replays one prefetch job's numeric policy (the real `run_numeric`, evaluator and pool) on
the job's own inputs, with the LLM still out. The clock is deterministic: one unit per sigmoid element, as stage 1's
F1 clock, plus a fixed price per SQLite connection opened on the job's thread (one open priced as main's whole first
batch of rollouts). The deadline admits main's first batch and no more.

| Code | Connections opened | Completed draws | Choice |
|---|---:|---:|---|
| Main's (no pool, `held_reading_map` off) | 20 | 8 | `repair:1c3060a44b67ba3c` |
| The branch (both on) | 2 | 64 | `new:0348b860fad015f9` |
| The branch at 8 draws, no deadline | | 8 | `repair:1c3060a44b67ba3c`, every `Q` equal bit for bit |

This is Codex's effect (its isolated case: 8 draws and stop, 16 draws and `a`). Item 1 shortens the same input
builds, so it has the same effect, and Codex's reasoning applies to it too.

**Fixed** (stage 1's F1 ruling, applied the same way):
- `[router_objective] held_reading_map` (item 1) and `pooled_connections` (item 4), both default on. They sit at the
  follow-up batch's tag through `followup_on`, like `held_ad_link`. Off, or below the tag:
  - `pooled_connections` off: `_objective_job` opens no pool (`objective_chooser._pooled`: a `nullcontext`);
  - `held_reading_map` off: `VaultReadingMap` and `MaterialView.section_spans` run main's code and read nothing of
    `reading_cache` (no digest, no held value, no watcher). A test fails if any of it is called.
- Both are in `FOLLOWUP_GENERATOR_SWITCHES`. That puts them in RO6's generator payload and the trace's
  `versions.serving_switches` (a flip is a change point) and, through `FOLLOWUP_SWITCHES`, in the prefetch boundary
  key.
- Both are classified in the parameter registry as structural kill switches. All 44 defaults snapshots were
  recomputed. The three successor tests that freeze an older digest drop the two keys
  (`tests/test_rofu_successor.drop_rospeed2_keys`). The spec's §8 paragraph on R8 names both.
- **No algorithm version**, for stage 1's reason. The switches, the generator payload and the prefetch key are how
  the follow-up batch versions a serving change at its tag. The owner's decisions in force are live changes behind
  kill switches and frictionless defaults.

**What the owner sees.** Decisions logged before the landing have no `held_reading_map` or `pooled_connections` in
`serving_switches`; new ones have both. RO6's generator therefore changes once, when the new code first serves:
one change point, which censors the transition that spans it.

### F3: TEXT cells are encoded by all their bytes

**Reproduced.** In SQLite 3.53.1, `quote('book\0old')`, `quote('book\0new')` and `quote('book')` are all `'book'`.
Of eight one-cell tables (the three strings, a blob, a string spelling a blob literal, 7, 7.0 and NULL), the old
encoding gave 6 distinct digests. At the mapping level, the note's canonical URI is `book\0new` and the source's is
`book\0old`. After the source was edited to `book\0new`, main mapped u4 with `lo_m5`; the branch still served the
held `[lo_m3, lo_m4]`.

**Fixed.** `_table_rows_digest` now encodes a TEXT cell as `t` plus the hex of all its bytes
(`hex(CAST(x AS BLOB))`). A real is `r` plus 17 significant digits. Anything else is SQLite's `quote`, which is
complete for NULL, integers and blobs. All eight digests now differ, and the mapping test serves main's values.

## Claims that don't hold (corrected in `docs/reviews/router-speed2.md`)

- **"Every served value … is main's" and "no new switch."** These hold at a fixed number of draws only. Under the
  serving deadline both items complete more draws. Both items are now switched and versioned (F2), and the stage
  record says so.
- **"A held value is never stale."** This now holds within a map too (F1), and for every stored cell (F3).
- **"Every cell is encoded injectively."** This is now true (F3).

## Spec conformance notes (Codex's table)

Items 2, 3 and 5 stay as the stage record describes them (not built, with the smallest finishes recorded there). The
review raised no finding on them. AD's protection, migrations, spend, grading and evidence: unchanged by these
fixes. The fixes add no table, no request, no writer and no read of protected rows. The watcher reads one pragma.

## Timings (before and after the fixes)

These come from the stage's scratch `measure.py`, on the same synthetic copy-shaped vaults and with the same
method as `router-speed2.md`: the objective job's median over three journey days, dwell 0, in ms, run behind
`/tmp/learnloop-fullsuite.lock`. "Off" sets both new switches to false in the copy's `learnloop.toml`. The fixed
runs of the `la` shape started at load average 6-7, after another worktree's full suite. The reviewed branch's runs
started at about 1.

| Shape | Code | Job (p90) | Numeric ready | Builds | Join (alone) | `los_for_section` / `los_for_span` (calls) | SQLite opens a job |
|---|---|---:|---:|---:|---:|---:|---:|
| `la` | main `e9ceaf8d44` | 4775 (5059) | 4567 | 3719 | 3362 (1703) | 973 / 2129 (84 / 192) | 908 |
| | reviewed `a95e354cf3` (item 4) | 1396 (1542) | 1125 | 320 | 156 (115) | 11 / 1 | 5 |
| | **fixed, switches on** | 1508 (1647) | 1240 | 361 | 173 (122) | 15 / 4 | 5 |
| | fixed, switches off | 4863 (5118) | 4602 | 3759 | 3399 (1701) | 969 / 2116 | 908 |
| `ax` | main | 2764 (2896) | 2521 | 1796 | 1399 (713) | 499 / 576 (36 / 56) | 436 |
| | reviewed (item 4) | 1247 (1312) | 999 | 303 | 134 (169) | 20 / 3 | 5 |
| | **fixed, switches on** | 1248 (1340) | 985 | 312 | 140 (170) | 24 / 5 | 5 |
| | fixed, switches off | 2756 (2868) | 2523 | 1798 | 1400 (716) | 501 / 576 | 436 |

- **Switched off is main.** The opens match main exactly (908 and 436), and every timing is within noise of main's.
- **F1's check costs a few ms a job with the commit version.** On `ax` the fixed branch is the reviewed branch's
  time. On `la`, under the higher load, the job is about 8% longer: `los_for_*` adds about 7 ms and the join
  alone 7 ms. The first fix, which read the metadata digest at every lookup, cost 1590 ms a job and 666 ms for the
  join alone on `la`. That is why it reads the commit version first.
- The stage's estimate for the owner's copy is unchanged (1.6-1.9 s against the 2.4 s target). The landing gate's
  smoke should still time the pinned week on the copies.

## The gate (this step)

The full suite, the whole durability lane and the whole vitest run belong to the landing gate. Nothing changed in
the frontend, `src-tauri` or the schema, so there was no npm, vitest, cargo or migration step. `db/connection.py` is
unchanged here. The new watcher is a raw read-only connection in `reading_cache`, so the two stage test files also
ran under `--durable-sqlite` (WAL).

| Step | What ran | Result |
|---|---|---|
| Setup | `uv sync --extra dev --extra mobile`, `uv pip install --offline pypdfium2==5.14.0` | ok |
| Import contracts | `lint-imports --no-cache` (under `env -i`), after the fixes | 43 kept, 0 broken |
| Reproduction | the F1 and F3 tests on `a95e354cf3`'s code | 3 failed (as expected) |
| Iterating | `test_rospeed2_section_map`, `test_rospeed2_connections`, `-n 6` | 19 passed |
| Durable lane | the same two files, `--durable-sqlite`, `-n 6` | 19 passed |
| Switches and snapshots | every test file naming the switch lists, `serving_switches` or the defaults snapshots (50 files), plus `test_registry_audit` and `test_cli_help_snapshot`, `-n 6` | 1031 passed, 12 skipped, 3 xfailed |
| References | `module_generate` / `module_validate` (PASS), `db_generate_reference` / `db_validate_reference` (errors `[]` after the two prose leaf counts 1183 -> 1185), `validate_vault` (passed) | ok |
| **Targeted set** | 143 files (listed below), `-n 6`, behind `flock /tmp/learnloop-fullsuite.lock`, on the final tree | **11296 passed, 14 skipped, 3 xfailed, 0 failed** (52 min 42 s) |

Every test ran inside `systemd-run --user --scope -p MemoryMax=5G -p MemorySwapMax=1G`, at most `-n 6`, one run at a
time.

The targeted set contains every file of the stage's earlier set (`router-speed2.md`), every file naming the switch
lists or the defaults snapshots, and the item 1 files. That includes the display-label audit
(`test_router_why_copy`, `test_key_ladder_labels`, `test_measurement_state_labels`, `test_rw5c_labels`), the CLI
help snapshot, the frozen cycles (`test_architecture`), the process-launch allowlist (`test_codex_lockdown_round3`,
`test_ai_tool_isolation`, `test_e0_isolation`, `test_codex_tool_lockdown`), and the contract set (config defaults,
serializer snapshot, desktop RPC contract, mobile allowlist, table roles, coordinated migrations, tracked fixture
databases, registry audit, module catalog inventory, public tip guards, SQLite file copies). The files:

test_ad1_fix_round4, test_ad1_reading_opportunities, test_ad23_contract, test_ad23_fix_r7, test_ad23_fix_r8,
test_ad23_fix_r9, test_ad23_fix_review, test_ad23_inversion, test_ad23_successor, test_ad2_serving,
test_ad3_dose_arm, test_ad3_reading, test_ad3_subject_view, test_ad_epoch, test_ad_guard_offer_receipts,
test_ad_guard, test_ad_guard_reachable_reads, test_ad_projection, test_ad_protected_readings,
test_ad_protected_tables, test_ai_tool_isolation, test_architecture, test_attempt_content_state_successor,
test_batch3_landing, test_cli_help_snapshot, test_codex_lockdown_round3, test_codex_tool_lockdown,
test_cold_retry_reschedule, test_config_refactor, test_coordinated_migrations, test_curriculum_c0b_landing,
test_curriculum_c1_plan_follows_path, test_data_capture_codex_review, test_data_capture_successor,
test_desktop_rpc_contract, test_diagnosis_input_provenance, test_e0_isolation, test_exam_protection_landing,
test_field_workbench_signals, test_followup_successor, test_help_fold_attach_successor, test_intent_codex_rereview,
test_key_ladder_labels, test_learner_report_superseded, test_lp_claim_fixes, test_measurement_state_labels,
test_method_explicit_upgrade, test_mobile_allowlist, test_module_catalog_inventory, test_mvp010_upgrade,
test_mvp011_upgrade, test_mvp013_upgrade, test_mvp014_upgrade, test_mvp015_upgrade, test_mvp016_upgrade,
test_mvp017_upgrade, test_mvp018_upgrade, test_mvp020_upgrade, test_mvp021_upgrade, test_mvp022_upgrade,
test_mvp023_upgrade, test_mvp024_upgrade, test_plan_determinism, test_plan_follows_path, test_public_tip_guards,
test_reader_ca2_one_ask, test_reader_ca5a_find_section, test_reader_followups_successor,
test_reader_question_note_id_placement, test_reading_step_switch, test_rebuild_equivalence_review,
test_recurrence_commands, test_registry_audit, test_regrade_contract_successor, test_repository_scopes,
test_ro1_successor, test_ro2_ad_document_ir, test_ro2_ad_raw_document_reads, test_ro2_history_protection,
test_ro2_history_resolve, test_ro4_codex_review, test_ro4_goals, test_ro4_objective_serving, test_ro4_price,
test_ro4_successor, test_ro4_trace_report, test_ro4_traces_migration, test_ro4_value, test_ro4_weight,
test_ro5_calibration, test_ro5_checks, test_ro5_codex_rereview, test_ro5_codex_review, test_ro5_landing,
test_ro5_picks, test_ro5_stop_coin, test_ro5_successor, test_ro6_codex_rereview, test_ro6_codex_review,
test_ro6_landing, test_ro6_learned_tail, test_ro6_serving, test_ro6_successor, test_ro6_tail_data,
test_rofu_ad_latent, test_rofu_ad_link, test_rofu_ad_stable, test_rofu_carried, test_rofu_generator_switches,
test_rofu_learning, test_rofu_monotone, test_rofu_review_draw, test_rofu_scope, test_rofu_speed,
test_rofu_successor, test_rofu_switch_key, test_rospeed2_connections, test_rospeed2_section_map,
test_rospeed_ad_link, test_rospeed_join, test_rospeed_watcher, test_router_why_copy, test_rw5c_labels,
test_salience_firewall, test_serve_eligibility_review, test_sidecar_serializer_snapshot, test_sqlite_file_copies,
test_sqlite_test_mode, test_sqlite_wal_lifecycle, test_sqlite_wal, test_table_roles, test_te3a_lesson_opportunity,
test_te3a_successor, test_te3b_clock, test_te3b_offers, test_te3b_population, test_te3b_successor,
test_teacher_te1b_review_fixes, test_teacher_te1b_suggestions, test_teacher_te1_successor,
test_teacher_te2_successor, test_tracked_fixture_databases, test_ux_phase1_landing.

Files changed by these fixes (for the landing gate): `src/learnloop/adaptive_difficulty/{reading,reading_cache,
material_view}.py`, `src/learnloop/config/{schema,template}.py`, `src/learnloop/daily_plan/objective_chooser.py`,
`src/learnloop/params/parameter_registry.py`, `src/learnloop/router_objective_switches.py`,
`docs/specs/spec_router_objective_v1.md`, `docs/reviews/router-speed2.md`; tests `test_rospeed2_section_map`,
`test_rospeed2_connections`, `test_rofu_successor`, `test_te3a_successor`, `test_te3b_successor`,
`test_teacher_te2_successor`; the regenerated references.

## Open items

- Merge main before the stage ends. Phone V3 was landing during this step. These fixes add two config keys, so the
  snapshots and the prose leaf counts need recomputing if phone V3 adds keys too.
- The landing gate's smoke should time the pinned linear_algebra week on the copies (unchanged from the stage
  record).

## The scoped verify and the landing rulings R1-R4

Codex's scoped verify of the fixes (job `20261107-055534-pCJUwT`, at `8d1e02e12e`) reopened F1, the protection
qualification, F2 and F3, and raised a new N1 (pooled pragma state). The orchestrator ruled R1-R6 (verbatim in
`router-speed2.md`, "Landing onto main"). Main (`ccb6573987`, phone V3) was merged first (`ec158e8c36`). Each ruling is
its own commit, reproduce-first: every new test below failed on the commit before its fix.

| Ruling | Codex's item | Commit | What changed | Tests (failed before the fix) |
|---|---|---|---|---|
| R1 | F1 (mid-walk vault edits, edit-and-undo contamination, the deferred IR load), the protection qualification | `2716ba9ea3` | The held map lives only within one objective job's `decision_reads` scope (`reading_cache.job_scope`), a snapshot as of the job's first read, discarded at its end. The job loads a reading's IR once and computes every mapping over it. Every memo return (the job's hold, the map's own section and span memos, the view's `section_spans` memo) is preceded by the withheld rule asked of the view fresh. A different epoch within the job drops what the job held. The digests, the commit-version watcher, the key re-reads and the process-wide bound are gone. | `test_rospeed2_section_map.py::test_r1_*` (6 cases) |
| R2 | F2 (the false switch entries move the numeric seed) | `bc1ceab278` | `objective_chooser.numeric_seed`: the numeric seed comes from the boundary identity less `SEED_NEUTRAL_SWITCHES` (`held_reading_map`, `pooled_connections`) at the block boundary, the follow-up interrupt and the objective follow-up. Both stay in the key, the generator payload and `serving_switches`. | `test_rospeed2_connections.py::test_r2_the_numeric_seed_is_mains_whatever_the_speed_switches[off, on]` |
| R3 | F3 (REAL `-0.0` and `0.0` digest alike) | none | **Not built: superseded by R1.** R1 removed the stored-row digest (`_table_rows_digest`, `MaterialView.reading_structure_digest`), so no held value is keyed by an encoding of stored cells. A changed cell, `-0.0` included, is read by the next job because nothing outlives a job. | `test_an_edit_behind_an_embedded_nul_is_read_by_the_next_job` (F3's mapping-level case, re-scoped) |
| R4 | N1 (`query_only` / `reverse_unordered_selects` leak to the next user) | `a24216bed3` | Pooled connections are `_PooledSqlite`. Every authorizer a checkout installs is wrapped. A PRAGMA with an argument (`SQLITE_PRAGMA` with one) or any statement other than a read marks the connection, and so does an API call or attribute that changes its own state. A marked connection is closed at release. The release no longer restores pragmas. | `test_rospeed2_connections.py::test_r4_*` (3 cases) |

### R1: what it reproduced and what it costs

- **Reproduced** (Codex's three F1 cases and the protection one, as tests):
  - an in-place vault edit made and undone within one map reached a later walk;
  - an LO unlinked mid-walk of the next job got the earlier job's held `[lo_m0, lo_m1]` where main gave `[lo_m1]`;
  - an IR rewrite after a held hit gave the branch the rewritten mapping and main the snapshot's (same job and
    earlier job);
  - a reading withheld from the same view still returned `['lo_m0', 'lo_m5']` from the memos;
  - a new job held everything from the last one (12 mappings computed once across two jobs).
- **The within-job residual R1 accepts.** Within one job a section is computed once, at its first read. A reading's
  run, revision, source or alias edited between two of a job's lookups reaches the lookups computed after it and
  not the held ones. The IR is the job's snapshot throughout. The next job reads all of it.
- **Cost against the cross-call cache** (the stage's `measure.py`, the synthetic copy-shaped vaults, three journey
  days, dwell 0, median per objective job in ms, behind `/tmp/learnloop-fullsuite.lock`; `ec158e8c36` is the
  merged tip with the cross-call cache, `a24216bed3` is R1-R4):

  | Shape | Code | Job (p90) | Numeric ready | Builds | Join (alone) | `los_for_section` / `los_for_span` | SQLite opens a job |
  |---|---|---:|---:|---:|---:|---:|---:|
  | `la` | cross-call cache `ec158e8c36` | 1444 (1573) | 1169 | 332 | 166 (119) | 14 / 4 | 5 |
  | | **R1-R4 `a24216bed3`** | **1501** (1706) | 1225 | 400 | 223 (1711) | 30 / 9 | 17 |
  | `ax` | cross-call cache | 1257 (1329) | 998 | 311 | 140 (171) | 24 / 5 | 5 |
  | | **R1-R4** | **1284** (1373) | 1037 | 318 | 145 (750) | 7 / 4 | 17 |

  Holding only within a job costs about 4% of a job on `la` (+57 ms) and 2% on `ax` (+28 ms). Each job now
  computes the mapping of its readings once, at the first build, instead of reading what an earlier job held. Main's
  job was 4775 and 2764 ms. Load average 1.3-1.9.

  R4 adds the opens in the last column: the repositories' `PRAGMA table_info` column checks and the job's
  model-call receipt writes now close their connections. "Join alone" is the join outside any job. Nothing is held
  there now, so it is main's cost; inside a job the second build still reads the job's hold.

### R2

With both switches off at the tag, the boundary identity differed from main's only by the two `false` entries in its
switch snapshot, so the numeric seed differed. On the journey's prefetch job before the fix, main's seed chose
`maintain:6664b3b0ed770a23` at eight draws and the branch's chose `repair:1c3060a44b67ba3c`: Codex's "main `a`,
branch `b`". After the fix every job's seed is main's (main's switch list is frozen in the test), and its eight-draw
evaluation equals main's bit for bit, with both off and with both on. The mixture's own draw (`mix.seed_for(key,
decision_id)`) still names the full key, as the stop coin does. They are keyed by the decision id, so neither
replays across processes; R2 names the numeric policy's seed only.

### R4

- **Reproduced.** Checkout A set `query_only = ON` and `reverse_unordered_selects = ON` and gave the connection back.
  Checkout B read `query_only = 1` (writable and read-only alike). An `INSERT` checkout's connection was pooled again.
- **Detection.** The authorizer slot is the AD guard's (it installs and re-installs its own hook on the raw
  connection), so the pool cannot hold that slot itself. Its connections are a `sqlite3.Connection` subclass whose
  `set_authorizer` wraps whatever is installed with a watcher. The watcher records any action outside the reads
  (`SELECT`, `READ`, `FUNCTION`, `RECURSIVE`, transaction control and savepoints, which the release rolls back), and
  any `SQLITE_PRAGMA` carrying an argument. The checkout's own `set_authorizer` expires every statement prepared
  before it, so each statement of the checkout is prepared again and seen. The pool's resets and the connection
  hook's install run unwatched.
- **The fast test lane.** `tests/conftest.py` applies `synchronous = OFF` and the journal mode once per pooled
  connection, unwatched, as part of its open. Otherwise every writable pooled connection would close at its first
  release in the fast lane. Production and the durability lane apply no pragma after the open.

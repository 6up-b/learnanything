# Teacher TE2-log: item 5's logging for lessons (`teacher/te2-log`, base `c2e810f940`)

Built from `docs/specs/spec_teacher_v1.md` revision 5: §20's TE2-log row and §24's build plan, with §8.3 (`episodes`,
`minutes`), §9 (`note_detour`, `write_plan`'s `p_held`), §11.3 (`lesson_node_held`), §11.6 (minutes), §11.7 (detours),
§11.9 (the episode log), §11.10 (the report) and §12.2 (a new forecaster family). No successor and no tag: additive
receipts behind `[teacher] episode_log`, as RO0's logging. Migration 247 (renumbered at landing if the router
follow-up batch lands 247 first). **No model request is added** (0 paid calls a day; no paid call was made by this
stage). No reader or writer of the old item difficulty scalar is added.

## Commits

| Part | Commit | What |
|---|---|---|
| 1 | `586a53eca7` | Migration 247 (`lesson_episodes`, `lesson_activity_intervals`), `table_roles` (RECEIPT, no replayer), AD `protected_tables`/`column_classes` (DENIED), head fixture `migration_head_247` |
| 2 | `84ec7ab399` | `teacher.episode_log`; `TeacherTurnEpisodesV1`; the doctrine's episode paragraph and its forecaster family; `note_detour`, the `unlogged` detour, a detour's close |
| 3 | `c2c40773f3` | `lesson.activity` (sidecar, Rust, client, DTOs), the screen's intervals (`lessonActivity.ts`), the minutes |
| 4 | `54da4d9c68` | `p_held` → `lesson_node_held` forecast receipts, resolved by the forecast report |
| 5 | `b6c516e589` | The receipt's `episodes`, `minutes`, `node_held_forecasts`; a refused detour row is a receipt warning |
| 6 | `49f359311a` | `learnloop teacher report`'s §11.10 lines, the pool weight's trajectory included |
| 7 | (this commit) | Spec §20 "As built", this file, the regenerated references |

## What exists now

| Spec | Where | Code |
|---|---|---|
| §11.9 episode log | `lesson_episodes` (RECEIPT; inserted at the opening, closing fields set once) | `teacher/episodes.py` (`open_episode`, `close_episodes`, `prior_belief`, `origin_ids`), `db/stores/lessons.py` |
| §11.7 `note_detour` | the turn's request; a `note_detour` `lesson_turns` entry holding the words; one `detour` row | `teacher/service.py` (`_note_detour`, `_plan_episodes`, `_logged`) |
| §11.6 minutes | `lesson_activity_intervals` (RECEIPT, append-only); `lesson.activity` | `episodes.record_intervals`, `episodes.minutes`, `handlers/lesson.py`, `screens/lessonActivity.ts`, `LessonScreen.tsx` |
| §11.3 `p_held` | `forecast_receipts` kind `lesson_node_held` | `episodes.node_held_receipts`, `scheduling/forecast_receipts.py`, `evsi_calibration/forecast_report.py` |
| §8.3 receipt | `episodes`, `minutes`, `node_held_forecasts` (absent off) | `service._receipt_episode_fields` |
| §11.10 report | `learnloop teacher report` | `teacher/report.py` (`lesson_report`), `learner/lesson_weight.pool_trajectory` |
| §12.2 family | `teacher_doctrine_v1+teacher_episodes_v1:<model>` | `episodes.doctrine_family`, `service._family_of` |
| Doctrine | `teacher/doctrine/episodes/v1.md`, prompt version `teacher_turn.v1+episodes-v1` | `episodes.instructions`, `episodes.prompt_version` |

**Switch.** `TeacherConfig.episode_log`, default true, classified structural/operational in the parameter registry
(`_ConfigRule`, like `teacher.visuals`). All 40 defaults snapshots were recomputed (the effective config gains the key;
no version's meaning changed); the seven tests that pin a pre-key digest pop it (TE1, TE1b, data capture, RO1, RO4,
RO5, RO6 successor tests). Off: TE1's prompt (doctrine and `PROMPT_VERSION` byte for byte, TE1's pinned schema and
doctrine SHA-256), TE1's turn schema, TE1's forecaster family, no row in either table, no `episodes` key in any turn
payload, no new receipt key, no `activity_log` in the view (so the screen sends nothing), and `lesson.activity`
writes nothing (`tests/test_teacher_te2log_episodes.py::test_switch_off_keeps_te1s_lesson_byte_identical`).

**No new constant.** The detour repair list is §18.4's `keep` vocabulary. The screen's idle gap is the Reader's
`VISIT_IDLE_MS` (reused). λ for the new family starts from §12.2's seeded Beta(1, 4) (the existing prior). Nothing
else is a number.

**Readers.** Nothing serving, scheduling, certification or replay reads any of it. The forecast report resolves
`lesson_node_held` (read-only), the teacher report reads everything (read-only), and the lesson weight's pool reads
`lesson_step_retained` only (unchanged).

## The turn schema, before and after

Strict output schema (`ai.strict_schema.strict_output_schema`, JSON, sorted keys):

| Turn | Bytes | SHA-256 (first 12) |
|---|---|---|
| `TeacherTurnV1` (TE1; off) | 3438 | `9668bbc1796b` (unchanged: the visuals tests' pin) |
| `TeacherTurnEpisodesV1` (on, no visuals) | 3866 (+428, +12.4%) | `c8f5e59836ed` |
| `TeacherTurnVisualsV1` (visuals on, episodes off) | 4518 | `cf732d340e1d` |
| `TeacherTurnVisualsEpisodesV1` (both on: the defaults with a figure host) | 4860 (+342) | `5cd36e9026ff` |

The episode paragraph adds 1463 characters to the instructions (about 350 tokens per teacher call). Same calls, no
new call.

## Rows per kind on a synthetic lesson

`tests/test_teacher_te2log_receipt.py`'s lesson (a plan with `p_held` on three nodes, one of them on no topic; a
missed check followed by a `note_detour`; a revised plan inserting a foundation with no note; two screen intervals
with seq 2 missing; a close):

| Table / kind | Rows |
|---|---|
| `lesson_episodes`, kind `detour` | 2 (repair `reteach` with hypothesis count 1, `unlogged` with count 0) |
| `lesson_episodes`, kinds `probe`, `gap`, `goal_lo` | 0 (TE2 writes them) |
| `lesson_activity_intervals` | 2 |
| `forecast_receipts`, kind `lesson_node_held` | 4 (two plan versions × two nodes on a topic; the topicless node writes none) |
| receipt `minutes` | active 4.0, elapsed 10.0, unreported 4.0, missing 1, intervals 2, source `lesson_activity` |

## What the teacher report prints

On that lesson, after one cold answer on `lo_det` (`tests/test_teacher_te2log_report.py`), TE1's lines and then:

```
lessons: 1 opened, 0 open; closed: goal_reached 1
lesson minutes: active 4.0 (over 1 lesson(s) with intervals; 0 with none, active unknown) · elapsed 10.0 · 1 interval(s) missing
delayed checks: 0 committed, 0 due, 0 answered
episodes: probe 0, detour 2, gap 0, goal_lo 0
probes: 0 generated, 0 refused, 0 retired unused, 0 answered
detours by repair: reteach 1, unlogged 1 (1 unlogged)
gaps: none
probe forecasts (lesson_probe_correct) against their grades: none scored yet
placement forecasts (lesson_node_held, 4 receipt(s)) against natural outcomes (self-selected): 2 scored, mean forecast 0.80 against 1.00 right, Brier 0.040, log loss 0.223 nats
placement forecasts against RO5's randomized checks (randomized): none scored yet
coverage of item 5's fields over 2 episode(s): hypothesis 1/2, repair_class 2/2, teacher_p 1/2, predicted_success 2/2, mastery 1/2, open_misconceptions_and_hypotheses 2/2, elapsed_minutes 2/2, active_minutes 2/2, origin 2/2, objective_trace 0/2, experiment_assignments 0/2, outcome 0/2
```

With pool updates it also prints, per forecaster, `pool weight trajectory <family>: prior λ̂ 0.181 ± 0.167, <date>
λ̂ … ± …` (the seeded prior's discretized mean is 0.181, not 0.2: the 21-point grid with the endpoint floor). With a
randomized check landing on a placement forecast's LO the third forecast line reads `(randomized, r 0.250, …)`.

## What could not be built as written, and the smallest alternative

1. **"Append-only" episode rows.** §11.9's row holds the opening's prior belief and the closing's minutes and outcome
   refs, and §11.9 lists `closed_at`. A pure insert-only row would have to wait for the close, losing every episode of a
   lesson that never closes. Built: the row is inserted at the opening and its closing fields move from NULL **once**
   (a close-once trigger, as `lessons.closed_at` and RO0's fill-once guards); nothing else updates, nothing deletes.
2. **Experiment ids "in force for the lesson's session".** A lesson has no session id. Built: every RO5 assignment
   (stop coin, randomized checks, open picks) made on the opening's local day, no later than the opening. Smallest
   alternative if a session link is wanted: record the session in force at the lesson's open (RO0 row 4's rule).
3. **"Refused by reason" for probes.** Rows hold no text, and TE2 defines the refusal reasons. Built: the count of
   probes closed `refused`. TE2's migration (248) can add a `refusal_reason` enum column; the report then groups by it.
4. **`lesson_probe_correct`.** TE2's kind (it needs `serve_probe`). The report already scores receipts of that kind;
   none exist yet.
5. **The prior belief's "AD readiness or the active predictor".** The brief's predicted success is the active
   predictor's (AD exposes no per-LO prediction at a check's level, TE1 as built); the row records the brief's own
   prediction, interval and source, so no new item-parameter read (the Nov 5 rule) is added.
6. **"A turn that inserts a foundation".** Built as: a revised plan with a new node placed before a node the previous
   plan had, and no `note_detour` in the same turn (appended nodes and a first plan are not detours). A note in an
   earlier turn is not matched to a later plan revision.
7. **The `lesson.activity` pin.** `tests/test_mobile_allowlist.py` pins `LESSON_RPCS` exactly, and that file carries
   the owner's uncommitted phone edits in the main checkout. The RPC is therefore in its own `LESSON_ACTIVITY_RPCS`,
   pinned desktop-only in `tests/test_teacher_te2log_activity.py`; the allowlist's blanket test denies it. At landing it
   can join `TEACHER_TE1_RPCS` once the owner's file lands.
8. **Receipt minutes.** The receipt counts the intervals received by the close (the screen flushes before every step,
   the closing one included); the report recomputes from the table, so a late interval appears there.
9. **The head-fixture rename.** The rename's mechanical substitutions (the fixture path in 67 files, `, 245, 246]` →
   `, 245, 246, 247]` in version lists, the `== 246` head pins and the `TE2LOG_ADDED_OBJECTS` subtraction and import
   next to every `RO4_ADDED_OBJECTS`) and the 40 recomputed fingerprints were applied with `sed` over exact patterns
   (no interpreter, no network), then read back through `git diff` and the migration tests; every other edit used the
   Edit tool.

## Reviewer notes

- A hypothesis passes the same output guards as displayed text (answer keys, the open check's solution, citations)
  before it is stored; a hit withholds the turn and nothing is logged. The row holds only its count and hash.
- Every row is written in its own savepoint of the action's transaction (`episodes._guarded`): a refused row rolls
  back alone with a warning; the turn, its other effects and the plan stand (tests for an episode, an interval and a
  `lesson_node_held` receipt). A refused detour row is also named in the receipt's warnings.
- Active and elapsed are reported side by side and never combined; with no interval, active is null (unknown), and the
  uncovered elapsed time is `unreported`.
- The visuals tests that pin TE1's exact prompt now switch `teacher.episode_log` off; the visuals lesson's schema at
  the defaults carries the episode fields; the visuals family test switches it off to compare TE1's and the visuals
  family.

## Gate (targeted; the full suite, the whole durability lane and the whole vitest run are the landing gate's)

Every pytest, vitest, npm and cargo command ran inside `systemd-run --user --scope --quiet -p MemoryMax=5G -p
MemorySwapMax=1G`, pytest at `-n 6`, vitest at `--maxWorkers=4`, one test run at a time; every other Python or CLI
under `env -i` with empty `HOME`, `CODEX_HOME` and `LEARNLOOP_CONFIG_DIR`. No model call, no paid call.

| Command | Result |
|---|---|
| `uv sync --extra dev --extra mobile`, `uv pip install --offline pypdfium2==5.14.0` | ok |
| `uv run lint-imports --no-cache` | 43 kept, 0 broken |
| pytest, part 1: the 64 test files the head rename touched, `test_teacher_te2log_migration`, `test_table_roles`, `test_ad_protected_tables`, `test_tracked_fixture_databases` | 843 passed, 3 skipped |
| pytest, the gate: 173 files (every test file added or changed on the branch; every test file naming `teacher`, `lesson_weight`, `forecast_receipts` or `forecast_report`; every defaults-fingerprint parity test; the contract set below) | 3301 passed, 26 skipped, 3 xfailed, 1 failed: `test_module_catalog_inventory` (the new `teacher/episodes.md` note was untracked until part 7's commit) |
| pytest after part 7's commit: `test_module_catalog_inventory`, `test_public_tip_guards`, `test_tracked_fixture_databases`; `lint-imports` again | 26 passed; 43 kept, 0 broken |
| pytest `-m durability` on the 32 touched migration test files that carry durability tests | 35 passed |
| `npm install`; `npm run typecheck` | ok |
| `npx vitest run --maxWorkers=4 src/screens/lessonActivity.test.ts src/screens/LessonScreen.test.tsx` | 21 passed (2 files) |
| `npm run frontend:build` | ok (the existing chunk-size warning) |
| `cargo check --manifest-path apps/learnloop-tauri/src-tauri/Cargo.toml` | ok |
| `db_generate_reference.py`, `db_validate_reference.py` (`SCHEMA_HEAD` 247) | 0 errors, schema head 247 |
| `desktop_generate.py`, `desktop_validate.py` (inventory 320 TS/TSX, 309 entry-build, ACTIVE 326) | passed, reproducible |
| `module_generate.py`, `module_validate.py` | PASS, 1237/1237 |

The contract set inside the gate: `test_architecture` (frozen cycles), `test_table_roles`, `test_registry_audit`,
`test_module_catalog_inventory`, `test_ad_protected_tables`, `test_cli_help_snapshot`, the display-label audit
(`test_router_why_copy`, `test_key_ladder_labels`, `test_measurement_state_labels`, `test_rw5c_labels`), the
process-launch allowlist (`test_ai_tool_isolation`, `test_e0_isolation`, `test_codex_tool_lockdown`,
`test_codex_lockdown_round3`), `test_sqlite_file_copies`, `test_public_tip_guards`, `test_config_refactor`,
`test_desktop_rpc_contract`, `test_sidecar_serializer_snapshot`, `test_sidecar_contract`, `test_sidecar_registry`,
`test_mobile_allowlist`, `test_desktop_activation_audit`, `test_coordinated_migrations`,
`test_tracked_fixture_databases`, `test_migrations`.

New test files: `tests/test_teacher_te2log_migration.py` (18), `tests/test_teacher_te2log_episodes.py` (13),
`tests/test_teacher_te2log_activity.py` (7), `tests/test_teacher_te2log_node_held.py` (4),
`tests/test_teacher_te2log_receipt.py` (3), `tests/test_teacher_te2log_report.py` (4),
`apps/learnloop-tauri/src/screens/lessonActivity.test.ts` (5). Changed: the 64 head-rename test files, the seven
fingerprint parity tests, `tests/test_reader_rw5d_p4b_teacher_visuals.py`, `LessonScreen.test.tsx` (+2).

## Landing notes

- Migration 247 and `migration_head_247`: if the router follow-up batch lands 247 first, renumber this file to the
  next free number, rebuild the head from main's head with only it applied, and repeat the substitutions of item 9.
- `lesson.activity` can join `TEACHER_TE1_RPCS` in `tests/test_mobile_allowlist.py` once the owner's phone edits land.
- The owner's vaults gain the two empty tables at their next migration; nothing else changes for them.

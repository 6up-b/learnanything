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

## Landing onto main

Main stayed at `c2e810f940` (the base) throughout, so no merge was needed and migration 247 keeps its number (the
router follow-up batch adds no migration).

### Orchestrator rulings (verbatim)

- R1: "F1's two residual paths are fixed structurally: (a) the identifier guard on every model-supplied field that reaches a log row or a receipt (note_detour's node, plan node ids, lo_id, receipt keys and inputs) checks against the vault's protected and reserved keys across the whole vault, including LOs a plan adds in the same turn, not only the initial brief's; (b) every contract refusal names the offending field by its location (request and node index), never by its text, so no untrusted identifier enters the transcript before the guard. Codex's two reproductions are tests (failing on the pre-fix source). No further Codex round on this class; I read the diff before landing."
- R2: "TE1's own forecast action copies request.node into its receipts unchecked: it gets the same node resolution and identifier guard, with a test, and TE1 lessons with teacher.episode_log off stay byte-identical apart from a refusal that now fires where protected text would have been written."
- R3: "Accepted as recorded: episode rows closed once by a trigger, as lessons.closed_at (§11.9's append-only read as insert-then-close-once); experiment ids taken from the lesson's local day up to its opening (a lesson has no session id); lesson.activity pinned in its own LESSON_ACTIVITY_RPCS tuple while tests/test_mobile_allowlist.py holds the owner's edits; probe refusal reasons left to TE2; the head-rename substitutions done by sed (mechanical, test pins only)."
- R4: "Owner, Nov 5: the old item difficulty scalar is to be retired in the refactor. TE2-log adds no new reader or writer of it; the landing checks this with a grep of the diff against main for the difficulty columns, mastery.irt.difficulty_from_prior and surprise's b, and records the result."

### Step 1: R1 and R2, reproduced first

Each fix's tests failed on the source before it. The details are in `docs/reviews/teacher-te2-log-codex-review.md`
("Scoped verify and the landing's rulings R1, R2").

| Ruling | Commit | What |
|---|---|---|
| R1 | `c301f12a6f` | (a) `guards.identifier_guard` checks every model-supplied field a log row, a receipt or a note's payload copies against every answer key the vault records, on any LO, with no exemption (`guards.key_sets` reads the KeyBook once for both key sets). (b) Every contract refusal (`service._contract_problem`, `visuals.contract_problem`) and every schema refusal (`service._schema_detail`: the location and pydantic's message, never the input) names the field by its location |
| R2 | `1c4bb43506` | TE1's `forecast`: a node its receipt copies must resolve (a plan node, a node of a plan the turn writes, a brief LO), else it is refused by location; the node and the LO its receipt will hold (`service._forecast_lo`) pass the guards |
| R1 (a) and R2, found at the smoke | `c1bfacd662` | With the switch off, TE1's own plan node ids and `lo_id` reached a receipt (the lesson receipt's `nodes`), `lesson_plans` and the transcript unguarded, as on main. They, and a posed check's and prediction's node (a visual's record in the receipt), now pass the identifier guard on every turn. A refusal fires only where protected text would have been written |

One wording change is visible with the switch off: a contract or schema refusal's detail line (the transcript's
`refused` entry) names a location instead of echoing the model's text. Two TE1 and visuals pins moved for it. Nothing
else of a TE1 lesson changes (the smoke's identity below).

### Steps 2 and 3: early checks and references

- `test_measurement_state_labels`, `test_cli_help_snapshot`, `test_codex_lockdown_round3`, `test_desktop_rpc_contract`,
  `test_sidecar_serializer_snapshot` and the rest of step 1's set (52 files, `-n 6`): 786 passed. `lint-imports
  --no-cache`: 43 kept, 0 broken.
- References (`6dec0ef3a9`, `7de9d232ed`): `db_generate_reference` / `db_validate_reference` (errors []),
  `desktop_generate` / `desktop_validate` (320/320 TS/TSX, 6/6 Rust), `module_generate` / `module_validate` (PASS),
  `validate_vault.py` (passed). Stamp-only churn was left out. No defaults snapshot's fingerprint moved.

### Step 4: the gate (at `7de9d232ed`)

| Lane | Result |
|---|---|
| Setup | `uv sync --extra dev --extra mobile`, `uv pip install --offline pypdfium2==5.14.0`: ok |
| Import contracts | 43 kept, 0 broken |
| Full suite (`-n 8`, 10G scope, under the shared lock) | 26717 passed, 90 skipped, 47 xfailed, 0 failed in 54.9 min (`test_regrade_contract_successor::test_a_held_unrecorded_grade_is_no_evidence` did not flake) |
| Durability lane (`-m durability`) | 403 passed, 1 skipped |
| Owner lane (fresh backup-API copies of `owner-copies-mvp035` in `fixtures-local/landing-te2log/`, since deleted) | 83 passed, 4 skipped, and the 2 known failures: `test_activity_backfill::test_backfill_logs_attempt_duration_interaction_events` and `test_placement_fixture_copies[arxiv_v2]` |
| Desktop | typecheck ok; whole vitest at `--maxWorkers=4`: 2763 passed; `frontend:build` ok |
| Rust | `cargo check`: ok |
| Mobile | typecheck ok, build ok |

A first gate run at `6dec0ef3a9` was stopped at 22% of the full suite when the smoke's finding (`c1bfacd662`) changed
the source; the gate above ran whole on the final source.

### Step 5: the smoke

**Setup.**
- Fresh backup-API copies of `~/learnloop-backups/mvp043-20261103-copy` (arxiv_v2, linear_algebra, probability) under
  `fixtures-local/landing-te2log-smoke/`, since deleted.
- Every AI route pointed at 127.0.0.1:9. The teacher, its inline grader and retrieval were the tests' `TeacherFake`
  (a `StructuredClientFake`; a schema failure reported as the providers report it: `AIInvalidOutput` chained from the
  `ValidationError`). The Today driver is RO6's (`drive5.py`: router LLM and Decider fakes, `BlindRivalClient`,
  `AuthorFake`).
- Main `c2e810f940` and branch `c1bfacd662` code were each `git archive`d with `migrations/`.
- Upgrades on main code, as RO6's record says: mvp-0.45, rebuild, mvp-0.46, mvp-0.47, rebuild, mvp-0.48, then the
  default to mvp-0.49 (head 246). Each copy was then opened once with branch code: **migration 247 applied on open**
  (head 247, algorithm still mvp-0.49).
- Lessons went through the real sidecar handlers (`lesson.turn`, `lesson.view`, `lesson.activity`), ids seeded and
  the clock frozen (one minute per action). LOs: `lo_compute_scaled_causal_self_attention`,
  `lo_add_vectors_coordinate_by_coordinate`, `lo_construct_a_complete_sample_space`.

**Switch off: identical to main on all three copies.** The script: a plan, a check with its forecast, a missed
answer, a revised plan inserting a foundation with a retention forecast, the close. Main's lesson against the branch's
with `teacher.episode_log = false`:
- the 6 teacher prompts, byte for byte;
- the schema (`TeacherTurnVisualsV1`, 4518 bytes, `cf732d340e1d`, TE1's visuals pin);
- the transcript, every view and the final view;
- every written row in every table (ledger, plans, checks, receipt, forecast receipts, reveals and grading rows);
- no refusal on either side.

**Switch on** (defaults). The script: `p_held` on two plan nodes; a `note_detour` after the miss; a revised plan
inserting a foundation with no note (unlogged); the screen's intervals in three batches (seq 1, 2 background, 4, 5; seq
3 never sent); a re-check on the node; the close. The same on every copy:

| Rows per kind | |
|---|---|
| `lesson_episodes`, kind `detour` | 2: `reteach` (hypothesis count 1, `teacher_p` 0.6, closed `rechecked`) and `unlogged` (count 0, closed `lesson_closed`) |
| `lesson_episodes`, kinds `probe`, `gap`, `goal_lo` | 0 |
| `lesson_activity_intervals` | 4 |
| `forecast_receipts` | `lesson_node_held` 4 (two plan versions × two nodes), `lesson_check_correct` 2, `lesson_step_retained` 1 |

- The receipt's `episodes`: 2 detour ids.
- The receipt's minutes: active 2.0, elapsed 9.0, unreported 6.6, 1 interval missing, 4 intervals, source
  `lesson_activity`. Active and elapsed are given apart. The first interval is clipped to the lesson's opening; the
  background one is covered but not active.
- Per episode: the detour has active 48 s over 240 s elapsed; the unlogged one 42 s over 300 s.

`learnloop teacher report` exits 0. Its new lines on linear_algebra:

```
lessons: 1 opened, 0 open; closed: goal_reached 1
lesson minutes: active 2.0 (over 1 lesson(s) with intervals; 0 with none, active unknown) · elapsed 9.0 · 1 interval(s) missing
delayed checks: 0 committed, 0 due, 0 answered
episodes: probe 0, detour 2, gap 0, goal_lo 0
probes: 0 generated, 0 refused, 0 retired unused, 0 answered
detours by repair: reteach 1, unlogged 1 (1 unlogged)
gaps: none
probe forecasts (lesson_probe_correct) against their grades: none scored yet
placement forecasts (lesson_node_held, 4 receipt(s)) against natural outcomes (self-selected): none scored yet
placement forecasts against RO5's randomized checks (randomized): none scored yet
coverage of item 5's fields over 2 episode(s): hypothesis 1/2, repair_class 2/2, teacher_p 1/2, predicted_success 2/2, mastery 2/2, open_misconceptions_and_hypotheses 2/2, elapsed_minutes 2/2, active_minutes 2/2, origin 2/2, objective_trace 0/2, experiment_assignments 0/2, outcome 1/2
```

**Protection.** KEY is a real answer key on an LO outside the lesson's brief:
- linear_algebra: an exam-reserved item's key (`pi_axiom_commutative_recall_02`, 22 characters);
- arxiv_v2 and probability: no reserved items, so another LO's item key (142 and 41 characters).

With the switch on, three turns each carried KEY:
- a revised plan with KEY as an inserted node's id and another node's `lo_id`;
- the same plan with only the `lo_id`;
- a `note_detour` whose hypothesis is KEY.

Each was refused by location:
- `requests[0].plan[0].id`: the identifier guard; on arxiv_v2 the schema's 80-character limit, since KEY is longer;
- `requests[0].plan[2].lo_id`;
- `requests[0].hypothesis`.

No episode row, interval, forecast receipt, plan, lesson receipt, later prompt, transcript or view holds KEY. Only the
refused turns' own `lesson_turn_payloads` rows keep the model's raw turn (2 or 3 rows), as TE1 does for every
withheld or invalid turn. That record is write-only: neither the transcript, the view nor any report reads a refused
turn's `turn`.

**R2 (switch off, TE1).** The script: a forecast on node KEY, then a plan with KEY as `n2`'s `lo_id` and a forecast
on `n2`.
- **Main** wrote KEY into `forecast_receipts` (1-2), `lesson_plans`, `lesson_receipts`, the later prompts and the
  views. On arxiv_v2 main's schema refusal echoed it into the transcript.
- **Branch:**
  - the forecast was refused by location: `requests[0].node`, contract, or schema on arxiv_v2;
  - the plan was refused: `requests[0].plan[1].lo_id`;
  - KEY is in no receipt, plan, prompt, transcript or view, only in the refused turns' raw payloads (1 or 2);
  - the later forecast on `n2` was written normally.

**Today, Next and the follow-up gate are unchanged against main.** RO6's driver ran one day per copy at mvp-0.49,
the seed pinned, the second served item missed with FG1's follow-up, the first stop declined. The branch (migration
247, switch on) against main was IDENTICAL on all three copies (ids and times aside):
- Today and the plan;
- every step and every written row, the RO6 traces included;
- the 5 router LLM requests and the 5 Decider requests;
- the follow-up gate (`insert_now`, `no_room_to_wait`).

The trace comparison sets aside the timing field `fit_ms`, which RO6's comparer did not list.

**Shadow and survival** (each lesson copy, branch code):
- `rebuild --shadow`: facet 0, schedule 0, mastery 33 / 20 / 17, every one stamp-only (`algorithm_version` alone);
  the live database unchanged.
- Every `lesson_episodes` and `lesson_activity_intervals` row is identical after `rebuild-derived-state` and a
  state sync.

**R4.** `git diff c2e810f940...HEAD -- src migrations` adds no line matching "difficulty" or "surprise". The only `b`
in an added line is a local interval bound in `episodes._overlap` (`a, b = max(start, lo), min(end, hi)`), not
surprise's `b`. So no reader or writer of the difficulty columns, `mastery.irt.difficulty_from_prior` or surprise's
`b` is added.

**Isolation.**
- The lessons wrote no `model_call_receipts`. The Today runs' 20 per copy came from the fakes (`fake`, `fake_llm`,
  `fake_decider`). probability's chatgpt and openrouter receipts are the backup's own, from Oct 25.
- The socket watch logged no connect at all and no non-loopback address.
- The only subprocesses were `powerprofilesctl get` (24) and `git -C` (6, the code stamp). No Codex process was
  started.

### What the owner runs after the fast-forward

No successor and no tag: the vaults stay at mvp-0.49. Migration 247 adds two empty RECEIPT tables
(`lesson_episodes`, `lesson_activity_intervals`).

For each vault (`~/learnloop-vaults/<name>`), after RO6's commands:

```bash
learnloop doctor --vault ~/learnloop-vaults/<name>   # or just open the vault in the app: migration 247 applies on open
```

Then rebuild the desktop app (the lesson screen sends its activity intervals) and restart the phone host.

**To turn the episode log off**, add this to the vault's `learnloop.toml`. Lessons are then TE1's exactly (TE1's
prompt, schema and forecaster family; no episode or interval row), apart from the location-only refusal wording above:

```toml
[teacher]
episode_log = false
```

### Open items

1. **A refused turn's raw record.** The refused turn's own ledger payload still records the model's raw turn,
   protected text included when that is why it was refused. This is TE1's design for every withheld message, and
   nothing reads it. Redacting it would change TE1's ledger, so it is left for the owner to decide.
2. **Wording.** The identifier guard's refusal reads "…use a plain id such as n1, and never an answer" for a
   hypothesis too; a field-neutral sentence is a one-line follow-up.
3. **Carried over:** `lesson.activity` can join `TEACHER_TE1_RPCS` once the owner's phone edits land; the probe
   refusal reason is TE2's (R3).

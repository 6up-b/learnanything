# RE0: capture (active seconds and the cue label)

Stage RE0 of `docs/specs/spec_recognition_and_effort_v1.md` (§4 is the scope, §2's rules apply). Branch `capture/re0`, built on main `6c8962ce95` plus the spec commit. **Capture only: no serving, scoring, scheduling or projection change, and no successor.**

## Playbook ruling: no successor

`docs/algorithm-change-playbook.md` step 1 asks whether the change alters persisted meaning. It does not:

- `practice_attempts.active_seconds` is a new nullable column on a `RAW_LEDGER` table (migration 252). Nothing that grades, schedules, projects, replays or certifies reads it, and replay never writes it (the raw ledger's graded columns are updated in place, this one is not among them). A reader of an old vault sees null, as for every attempt before this stage.
- `attempt_cue_v1` is derived: a pure function of existing records, with no table, no migration and no stored value. Nothing serving reads it.
- The report section is read-only.

So no `algorithm_version` is added, `SUCCESSOR_CHAIN` and the defaults fingerprint are untouched, and there is no kill switch: with nothing sending `activeSeconds` the system behaves exactly as before. Migration 252 adds no table, so `db/table_roles.py` needs no entry (`practice_attempts` is already `RAW_LEDGER`). `test_re0_capture.py` checks that `adaptive_difficulty/` never reads the column or the label, and that the column is classified `content` in `adaptive_difficulty/column_classes.py` (so an AD operation can reach it only through the rules, which never hand it out) and in `protected_tables.py`.

## Step 0: which surfaces send latency, and what they send now

"Latency" is `latency_seconds`: wall-clock seconds since the problem opened, not idle-adjusted. "Active" is `active_seconds` (below). Checked against the code on this branch.

| Surface | Wrote `latency_seconds` before | Now sends `activeSeconds` | Notes |
|---|---|---|---|
| Desktop practice screen, Submit (`PracticeScreen.tsx`, `submit_attempt`) | yes | **yes** | Carried across resumes under the draft's submission key |
| Desktop practice screen, "I'm stuck" with no text / don't know (`submit_dont_know`) | yes | **yes** | Same clock |
| Desktop workbench (`Workbench.tsx`, `workbench.submit`) | yes | **yes** | Carried under `workbench:<session id>` |
| Desktop dialogue probe turns (`DialogueProbe.tsx`, `submit_attempt` and `submit_dont_know`) | yes (per turn) | **yes** (per turn) | A turn is one open; nothing to carry |
| Desktop teach-back conversation (`submit_teach_back_turn`, `handlers/teach_back.py`) | **no** (the handler accepts `latency_seconds` but the client never sent it) | **yes**, on every turn; the server reads it only at the turn that finishes the conversation | Carried under `teach_back:<session>:<item>`. Latency is still not sent: out of scope |
| Phone question (`apps/learnloop-mobile/src/practice/QuestionScreen.tsx`, `submit_attempt`; its request contract `contract/submit_attempt.json`) | yes | **yes** | The phone imports the desktop's clock. Carried under `phone:<session>:<item>`; the contract file and its test now carry `activeSeconds` |
| Phone `submit_dont_know` | the phone sends none today (`SubmitInput` has no such wrapper) | n/a | The server accepts it; nothing on the phone calls it |
| **Lesson checks** (`teacher/checks.py`, drawn through the lesson action `answer_check`) | **no**: the attempt has no session and no latency | **no** | The lesson action carries no timing. The lesson's time is already on RO's clock through `lesson_activity_intervals` (a different measure: foreground intervals of the whole lesson). Smallest way to finish: derive a check's active seconds from those intervals at the report, or add a field to the lesson action and time it in `LessonScreen`. Deferred, because mixing the two measures is exactly what the two-clocks rule forbids |
| Lesson probes (`teacher/probes.py`) | no | no | Same as lesson checks |
| Exam sittings (`goals/exam_session.py`, `ExamScreen`) and imported exam answers (`exam_seeding`) | no | no | A sitting is timed as a whole; an import has no clock |
| CLI practice (`cli/app.py`, `cli_practice`) and the TUI (`tui/screens/practice.py`) | no | no | No clock on either; a terminal has no touch events worth trusting. Missing, never imputed |
| Observations, recall calibration, rung re-requests, MCP | no | no | Not timed practice |
| Simulator (`sim/runner.py`) | yes (simulated) | no | `evidence_origin = simulator`; the report counts it as missing |

`AttemptDraft` carries `active_seconds`, so any future surface that can send it only has to pass it.

## The active clock

Defined once, as the router objective's own clock, not a second one: the Reader's visit clock (`screens/reader/visitClock.ts`), whose close event `router_objective.price.activity_spans` reads for RO's `m_a`. A gap between two touches shorter than `VISIT_IDLE_MS` (two minutes) is active time; a longer gap counts for nothing. `screens/attemptClock.ts` applies it to an attempt (pure); `screens/useAttemptClock.ts` listens for `keydown`, `pointerdown`, `wheel`, `scroll` and `input` on the window.

- **Sums across resumes.** The active milliseconds so far are kept in `localStorage` under the draft's identity, written at most every five seconds while touching (an operational throttle, not a model constant) and on leaving, and read when the draft reopens. The clock restarts at "now" on every open, so time the draft sat closed (a pause, a night, a day) adds nothing. The entry is removed once the submit is acknowledged.
- **Never blended with latency.** Two columns, two request fields; no code subtracts, divides or substitutes one for the other. `latency_seconds` is untouched. The report prints both counts and takes the mean of active seconds over the attempts that sent it.
- **Where the server stores it.** `AttemptDraft.active_seconds` (validated non-negative) -> `attempt_record` -> after the row's insert, `db/stores/router_objective.fill_receipt("practice_attempts", ...)` in its own savepoint, as RO0 wrote its columns on older tables: a refused write leaves the attempt standing with null, a vault below 252 has no such column and the fill is a no-op, and null is never written. `RECEIPT_FIELDS`, `_RECEIPT_KEYS` and `_RECEIPT_WHAT` carry the new table.
- **Limits, stated plainly.** The carry-over lives on the device (`localStorage`); a draft resumed on another device starts from zero there. A draft's key is its submission id (desktop), its session and item (phone) or its workbench session; a key that is replaced (a failed phone submit gets a new key) restarts the carry on the desktop, not on the phone. A browser that blocks storage only loses the carry; the open's own seconds are still sent. Not verified against a real Tauri webview or a real phone: vitest in jsdom only.

## The cue label (`learnloop/recognition/cue.py`)

`attempt_cue_v1(attempt, ledger) -> AttemptCue`: pure, derived, no table. The ledger (`CueLedger`) is plain records, gathered by `recognition/ledger.py` from existing tables only. The seven fields as built:

| Field | Rule |
|---|---|
| `same_lo_before`, `same_concept_before` | The previous practice attempt in the session (same `session_id`; an attempt with no session reads the router objective's `session_gap_minutes`, passed in) is on the same learning object / concept. Self-reports, skips and imported exam answers are never "previous" |
| `after_reading` | A Reader exposure on the attempt's learning object (data capture's one read, `reading_exposures.read`) or any `reveal_events` row on it, within the warmth window before the attempt began. A reveal tied to this attempt, or after it began, is help and does not count |
| `after_lesson` | A `lessons` row naming the learning object, from when it opened (never when it closed), within the window |
| `method_stated` | The attempt's pinned assessment contract froze a `required_method` (`contract_required_method`). No pinned contract: unreadable, listed, not read as false |
| `followup_of_miss` | `followup_tasks.consumed_attempt_id`, or the attempt that answered a `followup_workflows` presentation, or the first other attempt on its item after the workflow was made |
| `randomized_check` | An attempt `router_objective.checks.resolve` ties to a drawn slot (reads `policy_experiment_assignments`) |

Uncued = every field false. `label` is `uncued`, `cued` or `unlabelled` (an imported exam answer has no ledger at all, so it is not "uncued"). `unreadable` lists fields the records could not speak to.

**Two readings I had to choose, recorded so the owner can overrule them.**

1. *The warmth window.* The spec says "within the warmth window". AD's `WARMTH_HOURS` (6) is the time constant of a decay, not a window, and importing it made `lint-imports` report a new cycle (`recognition -> adaptive_difficulty`, then `ops -> adaptive_difficulty`). I used the outcome contract's retention minimum, `RETENTION_MIN_DELAY_SECONDS` (24 hours): the delay under which a read is not a delayed one, so "warm" means what the delayed outcomes already mean by it, and no constant is invented. The window is a parameter of the ledger; changing it is one line.
2. *"Goal-date reads".* The spec's wording is ambiguous. The goal-date read's data is the exam answers and sittings its transfer slope is fitted on (`router_objective/goal_read.py`: `exam_evidence` and `exam_attempt` rows). The section reports those as `goal_date_reads`, split the same way. Imported exam answers are `unlabelled`. The section also reports `practice_pool` (all practice attempts, which is what the pool forecast reads), so the cells a goal-date read depends on are all visible.

## The report section

`learnloop data-capture report` gains `recognition_and_effort` (JSON key and a text block): practice attempts by label, how often each cue was present, unreadable fields, `unlabelled_for_an_unreadable_field`, active seconds sent and missing by surface, and, for `method_selection`, the practice pool and the goal-date reads, each split uncued / cued / unlabelled with attempts, mean correctness, active seconds sent, missing and mean, and latency sent. Labelled **observational**: attempts were not randomized to cues. A null `active_seconds` is counted as missing, the mean is over what was sent, nothing is imputed. Read-only; no model call.

## Migration and what is left for the landing

Migration **252** (`migrations/252_attempt_active_seconds.sql`): `ALTER TABLE practice_attempts ADD COLUMN active_seconds INTEGER CHECK (active_seconds IS NULL OR active_seconds >= 0)`. IH claims 251 and lands first; the runner is set-based, so the gap is fine. **I did not upgrade or rename `fixtures/migration_head_*`** (IH will rename it too). Steps left for the landing, after IH lands:

1. Take IH's head fixture (`migration_head_251`), apply 252 to a backup-API copy of it (`learnloop.db.copies`), keep it in rollback mode (`PRAGMA journal_mode=DELETE`), integrity ok, and rename it `fixtures/migration_head_252`; update its `README.md`.
2. Update the 5 hard-coded paths: 3 tests (`test_migrations.py`, `test_tracked_fixture_databases.py`, `test_public_tip_guards.py` name it, plus every `test_*migration*.py` and `test_mvpNNN_upgrade.py` that names `migration_head_250` or its successor: about 65 files in this branch's tree) and the 2 DB reference scripts (`docs/learnloop-architecture-vault/_scripts/db_generate_reference.py` names it 3 times, `db_validate_reference.py` once), plus `scripts/sanitize_migration_head_fixture.py`'s example and the Database Catalog note.
3. Re-run `db_generate_reference.py` and `db_validate_reference.py`.
4. Every head pin and version list (`max(names) == 250`, "lists ending at 250") moves to 252. Note `test_mobile_v3_migration.py` and `test_ro1_availability.py` assert the exact list of migrations applied on top of a downgraded 250 head: they become `[250]`-relative-to-251/252 checks and need IH's value.
5. Regenerate the module catalog (`docs/learnloop-architecture-vault/_scripts/module_generate.py`): I committed only the five new `learnloop/recognition` notes and the package description line in the generator. A full regeneration churns about 60 unrelated notes (provenance and line numbers), so I left them for the landing, where they will churn anyway.
6. The CLI help snapshot (`tests/cli_help_snapshot.json`) changed for `data-capture` and `data-capture report` (the report's docstring). If IH's landing also changes the snapshot, regenerate it with `python tests/test_cli_help_snapshot.py --write`.
7. Full gate: full pytest, the durability lane, `lint-imports`, vitest for both apps.

**Tests that fail until step 1 and 4** (the head fixture is at 250 while the migrations now end at 252): see the run below; all fail because the downgraded-head upgrade now applies 252 as well, or because a head pin says 250. None fails for another reason.

## Tests

See the end of this file for the run numbers.

### Run numbers (this branch, tip below)

- `tests/test_re0_capture.py`: 31 passed with the catalog inventory (21 original + 1 window test + capture/inventory neighbours); alone 22.
- Targeted Python (each `-n 4`, memory-capped): architecture, data-capture report, AD protected tables, table roles, RO migration, display-label audit (`test_sidecar_measurement`, `test_router_why_copy`, `test_key_ladder_labels`, `test_measurement_state_labels`, `test_rw5c_labels`), RPC contract, config refactor, sqlite file copies, mobile allowlist, registry audit, module catalog, serializer snapshot: 585 passed. Attempts, RO0 report/receipt files, teach-back, daily-plan RPC, phone contract and sidecar contract: 286 passed, 5 skipped.
- **Head-pinned set** (91 files naming `migration_head_250`, `discover_migrations`, `applied_versions`): 1095 passed, 94 failed, 4 skipped, 2 xfailed. Every failure I inspected fails with `UncoordinatedMigrationError ... is at migration 250 and this LearnLoop needs migration 252`, or a pin of 250; I saved only the last 45 lines of the failure list, so the full list is the set above minus the passes, and only the first-listed 45 were individually named. They all clear with the head step. The same set at the base would be expected to pass; I did not run it at base.
- `lint-imports --no-cache`: 43 kept, 0 broken.
- CLI help snapshot: regenerated, passes.
- Vitest, desktop: 277 files, 2794 passed. Phone: 29 files, 337 passed. Typecheck clean for both.

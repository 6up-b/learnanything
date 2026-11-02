# Reader RW5d P4b: the teacher's manipulatives (stage record)

- **Spec:** `docs/specs/spec_reader_show_me_figures_v1.md` rev 2, phase P4b: §6.5, §7.1, §7.2 (the "Predictions on" row), §10.4, §12.3, and the P4b row of §14. Also `docs/specs/spec_teacher_v1.md` §8.2 and §10 ("Instruments over description"). The as-built notes are in figures §10.4 and teacher §8.2.
- **Branch:** `reader/rw5d-p4b-teacher-visuals` in `learnanything-merge2`, base `1a33bb5db3` (TE1 + C4, mvp-0.41, migration 234).
- **Migration:** none. Migration 224 already allows origin `teacher` and `goal_author = 'teacher'`; `figure_requests.policy` and `caller_kind` carry no CHECK.
- **Successor:** none (§1). Uses TE1's tag; below mvp-0.41 no lesson can open.
- **Switch:** `teacher.visuals`, default true, classified in `params/parameter_registry.py` (structural, operational). It takes effect only with `figures.enabled` and `figures.show_me_enabled` on, and only where the lesson's host supplies a figure builder (the desktop's `lesson.turn`).
- **Live calls:** none. In every test the teacher, the grader and the figure author are fakes (`TeacherFake`, `AuthorFake`). No CLI or paid command ran, and no vault or copy was opened outside pytest. The only Python run outside pytest was the snapshot recompute (`defaults_fingerprint_for_version`). It ran under `env -i` with an empty, existing HOME, CODEX_HOME and LEARNLOOP_CONFIG_DIR.

## 1. Successor decision (`docs/algorithm-change-playbook.md` step 1): no successor

| Change | Existing records | New records | Persisted meaning? |
|---|---|---|---|
| A lesson turn may carry a figure | No `visual` entry exists before this stage | One `lesson_turns` row (`action = 'visual'`), plus the figure service's `figure_requests` and `interactive_figures` rows (origin `teacher`), all allowed by 224's CHECKs | **No.** It is content and display. No scoring, scheduling, projection or serving code reads it |
| The figure's words are the lesson's exposure | — | `tutor_answer` reveal rows with basis `lesson:<id>`. These are TE1's own reveal rows for teaching text, with that existing meaning. The figure's words also join the lesson's displayed text, which the delayed-check picker and the receipt's `shown_items` read (exclusion only) | **No.** TE1's existing rule, applied to one more displayed field |
| The teacher's prompt and turn schema with visuals on | TE1's prompt is unchanged: off, it is byte-identical (pinned) | Prompt version `teacher_turn.v1+visuals-v1`, the visuals paragraph, and `TeacherTurnVisualsV1`. Forecast receipts record the prompt version the forecasting turn ran under | **No.** The forecaster identity (`forecaster_version` = model family) is unchanged |
| A lesson check posed beside a figure | — | It is graded on its question text only, at the learned mass, as TE1 grades it. The figure is never a help row and never evidence | **No** |

Stop rule: nothing here reclassifies an attempt, and nothing writes evidence, mastery, FSRS or AD state. No `mvp-0.N` is minted. All 32 defaults snapshots moved, only because the effective config gains `teacher.visuals`. They were recomputed with `defaults_fingerprint_for_version`, and dropping the key reproduces main's values (`test_teacher_te1_successor`'s parity test now pops `visuals` too).

## 2. What P4b ships

### 2.1 The contract (`teacher/contracts.py`)
- **`TeacherTurnV1` is untouched.** Its strict-schema hash is pinned in the tests: `9668bbc1…42dc0`, as at `1a33bb5db3`.
- **With visuals on,** the turn is `TeacherTurnVisualsV1`, which adds `visual: TeacherVisualV1 | None`. A visual is either:
  - `{goal, anchors, planned_node: null}`: anchors are 1 to 3 delivered passage aliases. The cap is `VISUAL_ANCHORS = 3`, the figure service's `GROUNDING_PASSAGES` (keep: prompt size); or
  - `{goal: "", anchors: [], planned_node}`: the node's planned visual.
- **`write_plan`'s request becomes `ActionRequestVisualsV1`,** whose nodes (`PlanNodeVisualsV1`) may carry a planned `visual: {goal, anchors}`.
- **Code fills in the rest** (`teacher/visuals.py`, `figure_request`):
  - origin `teacher` and `goal_author` `teacher`;
  - host `{lesson_id, node_id}`, where the node is the planned node, else the turn's check or prediction node;
  - caller `actions.caller_for(state)`: kind `teacher`, policy `reading`, or `assisted_practice` bound to the minted item while a lesson check is open;
  - `grounding_keys` from the named passages' `(extraction_id, span_id)`;
  - no anchor spans and no reading position.

  The teacher writes words and aliases, never a request field.
- **Correctable refusals** (`visuals.contract_problem`, inside TE1's `_contract_problem`):
  - an undelivered or revoked alias;
  - a visual with no anchors, or with an empty goal;
  - a `planned_node` with no planned visual;
  - `planned_node` together with a goal or anchors;
  - a planned visual whose anchors are undelivered.

  Each refusal goes back to the teacher. Three in a row close the lesson `teacher_contract_failure`, as in TE1.
- **Guards.** Each turn's visual goal and every planned goal is a displayed field (`_displayed`), because the figure's line quotes its goal. So each passes TE1's three guards before the turn is accepted.

### 2.2 Building it (`teacher/service.py` `_visual`, `teacher/visuals.py`)
- **When it runs.** The visual is an effect of the accepted turn. It runs after the prediction or check and before the requests, marked `refs.effect = 'visual'`, so recovery resumes it idempotently.
- **It is a model call outside any ledger transaction.** It runs inside the action's `_lesson_spend` envelope, so the lesson's grant and per-lesson cap admit its requests, on top of the figures' own `FiguresGate` and daily envelope. A refusal by the lesson's envelope propagates, and the lesson closes `budget` as TE1 closes it.
- **The builder is the host's** (`Clients.figures`). The desktop's `lesson.turn` attaches `_figure_builder`: `FS.build_figure` with the injected author in tests, the live vault for the gate, and `spawn_rich=None`. With no builder (any other host), `V.on()` is false, so the prompt is TE1's and no visual exists.
- **Outcomes.** A figure that can't be built, or whose route is unavailable, is recorded `failed` or `unavailable` with the reason. A held-out input is recorded `withheld`. The lesson's turn goes on either way: a figure never fails a turn.
- **The figure's words** are `figures.help.reveal_text`, P3's text: what it demonstrates, assumptions, labels and prompts, a sketch's strings, and a grammar figure's displayed values at the defaults. Before the figure is shown, they pass:
  - TE1's key guard (a vault item's answer on the lesson's LOs; an unreadable KeyBook fails closed);
  - the open check's solution guard, which covers a check posed in this same turn.

  On a hit the figure is recorded `withheld` (code `answer_key` or `open_check_solution`) and not shown.
- **A shown figure's words** go into the same transaction as its record. They are written as reveal rows (`_record_reveals`, basis `lesson:<id>`, TE1's strict writer) and kept on the record (`shown_text`). They then count as the lesson's displayed text: the delayed checks never pick a vault item the figure reproduced, and the receipt's `exposure.shown_items` lists it.
- **What the teacher hears.** The transcript tells the next call what the figure turned out to be: its tier, what it demonstrates and its controls (name, label, range, default), or why it isn't shown.
- **The receipt** gains `visuals` (node, figure id, status, version) only when the lesson had any. Otherwise it is TE1's receipt, key for key.

### 2.3 The figure service (`figures/service.py`)
- **`teacher` joins `ORIGINS`.** `RESERVED_ORIGINS` is now `("prefetch",)`, and a new `SERVICE_ORIGINS = ("teacher", "prefetch")` is refused by `figure.request` and `reader.figure_request` (`_request_figure`).
- **`_validated_request` accepts origin `teacher` only with:**
  - a teacher caller;
  - `host_ref.lesson_id`;
  - fixed grounding keys;
  - no spans, region or `supersedes_id`;
  - `teacher.visuals` on (else `teacher_visuals_disabled`).

  The goal's author must be `teacher`. A lesson request has no reading position, so `extraction_id` is NULL and it has no home. A "not right?" of a lesson figure from an RPC is therefore refused: its revision has no teacher caller.
- **`key_for` adds `teacher.visuals`** for a lesson request, so switching it off stops a build in flight.
- **`build_figure` drops any rich spawner for a lesson request** (`LESSON_TIERS = ("grammar", "sketch")`), whatever the caller passes. A test with every rich tier patched ready, plus a spawner, shows no rich job, no `+rich-v1` prompt and no rich tier recorded. With the override removed, the test fails (mutation-checked).
- **Unchanged:** the request hash names `goal_author`, so a teacher's goal is its own input, separate from the same words typed by the learner. Exam protection runs through the one predicate: `check_request` refuses the whole request when any grounding key is held-out material (`exam_material`), before any job or call; `ground()` rechecks each key, and `figure_withheld` rechecks at every delivery and view.

### 2.4 The lesson's view and the desktop
- **`view()`** shows each `visual` entry as `{kind: "figure", node, goal, status, figure}`. The `figure` is `visuals.lesson_view`, which returns:
  - the figure service's view with `predictions: []`, `fuller: null` and `host: "lesson"`;
  - or None (status `withheld`) when the figure is held out now, gone, rich, or not shown.

  While visuals are off, no figure entry appears: TE1's view.
- **`LessonScreen.tsx`** draws a shown figure inline in its turn with the Reader's `FigureInline`, expanded, through a lesson controller:
  - the contract is `{predictions: false, region: false, revisions: false}`;
  - nothing is requested, predicted or revised;
  - the figure's predictions are stripped again client-side.

  A figure that isn't drawn says why in one quiet line (`LESSON_FIGURE_COPY`). `FigureGoal` voices a teacher's goal like a tutor's: "◇ … (AI-written)".
- **DTOs:** `LessonFeedEntryDto` gains the `figure` entry and `LessonFigureStatus`. `FigureViewDto.origin` gains `ask` and `teacher`, `goalAuthor` gains `teacher`, and there is a new optional `host`.
- **No new RPC, no new frontend file, no `src-tauri` change.** So there is no desktop catalog regeneration and no cargo check.

### 2.5 The doctrine paragraph
`src/learnloop/teacher/doctrine/visuals/v1.md` (`VISUALS_VERSION = teacher_visuals_v1`) is written in our own words. It covers:
- when a manipulative helps;
- writing the goal: what to move, what stays fixed, what to watch;
- anchors;
- planned visuals and `planned_node`;
- that the figure is an illustration, never graded, and its own prompts are off in a lesson;
- not putting a check's answer in it;
- that most turns need none.

It sits outside `doctrine/v1/`, so TE1's doctrine text and hash (`ecec5db5…96ea`) are unchanged. It is appended only while visuals are on.

## 3. Decisions recorded here (spec defaults where it had one)

- **D1. Lesson host tiers are grammar and sketch.** This follows the teacher spec's doctrine row ("grammar or sketch tier"), P3's ruling R1 and §6.5 (the turn waits on its figure). The spec's rev-2 line, "a rich medium chosen for a later step is usually ready by then", belongs to P5's quiet prebuilds of planned visuals and is recorded as open item 1.
- **D2. A lesson figure has no home.** Spec §7.2 says "Home: anchor, else reading_at, else the host". For a lesson, the host is the lesson. So it is not listed in the Reader and gets no Reader "not right?", which would need a lesson's teacher caller.
- **D3. Grounding is the teacher's delivered passages, as fixed keys,** and at least one is required. Nothing is retrieved: no extra metered search, no new retrieval surface, and §6.5's "anchored to the lesson's sections" is enforced structurally.
- **D4. Predictions are suppressed by host, not by origin.** It is the lesson's view and the lesson's controller that carry none. `record_prediction` is a Reader RPC with no lesson host.
- **D5. The figure's words pass the lesson's key guard and open-check guard.** On a hit the figure is withheld, not shown, and the check stays valid: the teacher's own messages get the same two guards. The citation guard does not apply, because a figure cites no alias.
- **D6. Visuals take effect only with "show me" on** (§7.1: "a goal alone needs `figures.show_me_enabled`"), so the teacher is never offered a visual the service would refuse.
- **D7. A figure failure never fails the turn,** and plan-down is recorded as `unavailable`. No separate T1 offer is made for the figure: the turn's own teacher call has just succeeded on the same plan, and a granted lesson already covers the build (§12.3: keyed by the lesson's method).
- **D8. P3's chooser may offer a lesson figure as `explore_figure` on a practice item.** P3's qualifying rule allows it: the figure's passages treat the item's LO, it is not built from the item's own blocks, and its words don't overlap the key. It is then recorded and counted as P3 records any figure. This is help, never certification. It was left as P3 built it.

## 4. Gate (this step; the full suite, durability lane and whole vitest are the landing gate's)

| Command | Result |
|---|---|
| `uv sync --extra dev --extra mobile`; `uv pip install pypdfium2` | ok |
| `uv run lint-imports --no-cache` | **42 kept, 0 broken** (41 on main + the new `lesson-checks-never-read-figures`, `allow_indirect_imports = false`) |
| `systemd-run --user --scope --quiet -p MemoryMax=5G -p MemorySwapMax=1G -- uv run pytest -n 6 <the files below>` | **1339 passed, 1 skipped** (179.6 s). The one skip is a pre-existing environment or golden-ordering skip in the figure suites (`needs_sandbox` / `test_figures_switch_off`'s golden order under xdist) |
| the same, `tests/test_public_tip_guards.py tests/test_diagnosis_input_provenance.py` (docs and tracked-file guards, after the docs were written) | **96 passed** |
| `npm install`; `npm run typecheck` (in `apps/learnloop-tauri`, memory-capped) | ok, no errors |
| `npx vitest run --maxWorkers=4 src/screens/LessonScreen.test.tsx src/screens/reader/figures/FigureInline.test.tsx src/screens/reader/figures/showMe.test.tsx src/components/askFigures.test.tsx` (memory-capped) | **48 passed** (4 files) |
| `npm run frontend:build` (memory-capped) | built (the existing chunk-size warning only) |
| cargo check | not run: nothing under `src-tauri` changed |
| DB reference generate/validate, durability | not run: no migration, schema, DB or connection change |

**Test files run** (pytest): `tests/test_reader_rw5d_p4b_teacher_visuals.py` (new, 15 tests), `tests/test_teacher_te1_*.py` (lesson, review_fixes, curriculum_c4, weight, successor, migration), `tests/test_teacher_te0_*.py`, `tests/test_figure*.py`, `tests/test_figures*.py`, `tests/test_help_assist_figures_migration.py`, `tests/test_help_assists_schema.py`, `tests/test_hint_service.py`, `tests/test_manim_figure_checks.py`, `tests/test_reader_rw5d_p4a_figures_follow.py`, `tests/test_architecture.py`, `tests/test_registry_audit.py`, `tests/test_config_refactor.py`, `tests/test_mobile_allowlist.py`, `tests/test_desktop_rpc_contract.py`, `tests/test_sidecar_serializer_snapshot.py`, `tests/test_cli_help_snapshot.py`, `tests/test_judge_routes.py`.

**The new tests** (`test_reader_rw5d_p4b_teacher_visuals.py`), all with fakes:
- **A visual turn builds a teacher figure.** The request's origin and author are `teacher`, with the lesson as host, caller `teacher` and policy `reading`. Tiers are within `LESSON_TIERS`. There is no home. The figure is shown inline with `predictions: []` although its stored spec has its own, and no `figure_predictions` row is written. The next teacher call is told the figure's controls. The prompt carries the paragraph and version.
- **The figure never reaches the grader,** and is never a help row. A figure built while a check is open is under `assisted_practice`. The receipt's `visuals` are present and the doctrine hash is unchanged.
- **Figure words that give the open check's solution away** are withheld (`open_check_solution`).
- **A figure reproducing a vault question** is in `shown_items`, and no delayed check picks that item (mutation-checked).
- **A planned visual is the identical request:** the second request is reused with no call.
- **Undeliverable visuals are refused back to the teacher:** an unknown alias, a node with no planned visual, both forms at once.
- **Switch off:** with `teacher.visuals` off, show me off, figures off, or no builder, TE1's prompt is rebuilt byte for byte, the TE1 schema hash and doctrine hash are pinned, and no `visual` key is stored in turns or plans.
- **Switching off later** hides a lesson's figures, and the service refuses a new build with `teacher_visuals_disabled` before any call.
- **Held-out inputs are refused before any call.** The lesson goes on, and the figure is `withheld` with no row. A figure held out since is no longer shown.
- **Origin `teacher` is refused** without a teacher caller, a lesson host, fixed keys or the teacher's authorship, or with a passage selection or revision.
- **No rich job is ever spawned from a lesson** (mutation-checked).
- **`lesson.view` never builds a pending figure** (no model call). The next action builds it.
- **The desktop RPC `lesson.turn`** builds the visual through the figure service (camel-cased view, `goalAuthor: teacher`, no predictions).
- **Structurally,** `teacher.checks`, `teacher.delayed` and `teacher.guards` import no figure code.

**Vitest** (`LessonScreen.test.tsx`, two new tests):
- the teacher's figure is drawn inline and open, with a teacher goal voice, no prediction of its own (although the DTO carries one), no "not right?", and no predict or request call;
- `failed`, `withheld` and `unavailable` each render one quiet line and no figure.

## 5. Owner items (not part of this stage)

1. **The real-lesson / real-figure checkpoint.** Run one lesson with a visual on a backup-API copy under `fixtures-local/`, on the plan. Look at whether the teacher uses visuals sparingly and well, whether the figures are the manipulative the goal asked for, and whether the doctrine paragraph needs editing (a doctrine edit is behaviour, not code).
2. **`teacher.visuals` ships on by default** under the frictionless-defaults rule. Off restores TE1's prompt exactly.

## 6. Open items

1. **P5: planned visuals prebuilt quietly** on the plan only (Q25), and a rich medium for a later planned step. `figures/prefetch.py` is in flight in `learnanything-dl2`. The lesson trigger needs the accepted plan's nodes that carry `visual`; the request P5 builds must be `visuals.figure_request`'s exactly, or it will miss the turn's input hash.
2. **"Not right?" inside a lesson** is not offered in P4b. A lesson revision would need the lesson service to own it, with the teacher caller and the lesson's envelope.
3. **Landing merges.**
   - `figures/service.py` is also touched by followups-nov2 (learner-state provenance) and by P5.
   - The defaults snapshots (all 32) and the "moves it too" comment lines will need recomputing after whichever lands first.
   - TE1b (`learnanything-astrafix`) may touch `teacher/service.py` and `teacher_fakes.py`. The fake now validates with the requested `result_model`.

## Landing onto main

The branch is `reader/rw5d-p4b-teacher-visuals` (tip `ef5c183623` before this record) in `learnanything-merge2`. The orchestrator does the fast-forward and push.

### Codex re-review (job `20261102-055647-VOyp5J`): CLEAN

> "F1-F4 CONFIRMED-FIXED. No new defects found."

### Merges and conflicts

- **None needed.** Main `1a33bb5db3` (TE1 + C4 landing record) was already an ancestor of the branch, and main did not move during the landing. It was checked before the full gate and again before this commit.
- followups-nov2 had not landed. So `figures/service.py`, the 32 defaults snapshots and the generated references needed no merge, recompute or regeneration.
- **No migration and no schema change.** `migration_head_234` is untouched. There is no successor (§1): the vault version stays `mvp-0.41`.

### Gate (tree `ef5c183623`, on main `1a33bb5db3`)

| Step | Result |
|---|---|
| `uv run lint-imports --no-cache` | **42 kept, 0 broken** |
| Targeted (`pytest -n 6`, 5G): the P4b file, `test_teacher_te1_*`, `test_teacher_te0_*`, `test_figure*`, `test_figures*`, `test_hint_*`, `test_help_*`, `test_notes_never_read`, `test_architecture`, `test_import_split_parity`, `test_public_tip_guards`, `test_config_refactor`, `test_registry_audit`, `test_sidecar_registry`, `test_sidecar_contract`, `test_sidecar_serializer_snapshot`, `test_desktop_rpc_contract`, `test_cli_help_snapshot`, `test_vault_template` (79 files) | **1351 passed, 6 skipped** |
| Targeted vitest (`LessonScreen`, `FigureInline`, `showMe`, `askFigures`) | **48 passed** (4 files) |
| Full pytest (`flock /tmp/learnloop-fullsuite.lock systemd-run --user --scope -p MemoryMax=10G -p MemorySwapMax=2G -- <env -i> uv run --no-sync pytest -n 8 -p no:cacheprovider --dist worksteal --durations=50 -o faulthandler_timeout=600 --junitxml=…`) | **23815 passed, 90 skipped, 47 xfailed, 0 failed** (44:18) |
| Durability lane (`pytest -m durability -n 6`, 5G) | **185 passed, 1 skipped** |
| Owner lane (`pytest -m owner_vaults -n 6`). `LEARNLOOP_OWNER_VAULTS` is a fresh `copy_tree_with_databases` copy of the mvp035 owner copies in the gitignored `fixtures-local/landing-p4b/owner-lane`. | **83 passed, 2 failed, 4 skipped.** Both failures are the known ones: `test_activity_backfill::test_backfill_logs_attempt_duration_interaction_events` and `test_placement_fixture_copies::…[arxiv_v2]` |
| Frontend: `npm install`, `npm run typecheck`, whole vitest (`--maxWorkers=4`, 5G), `npm run frontend:build` | install ok, typecheck ok. Vitest: **257 files, 2447 passed, 1 failed** (see below). Build ok (the existing chunk-size warning only). |
| `cargo check` | not run: nothing under `src-tauri` differs from main |

**Unexpected failure, rerun alone.** One vitest test failed in the whole run: `sketchSandboxReview.test.tsx` › "keeps the checks when every tested read on the page matches the verifier's, played to t_max at the defaults". It failed with `expected 't = 0 / 100' to contain 't = 100 / 100'` after 12 s, a playback timing race under the full 4-worker load. P4b does not touch that file or the sketch sandbox. It passed **3 of 3** when rerun alone.

### Smoke on fresh owner copies (`fixtures-local/landing-p4b-smoke/`, drivers `scripts/smoke.sh` and `scripts/capture.sh`)

**Setup.**

- **Copies.** Fresh backup-API copies of the three mvp035 owner copies.
- **Routes.** Each copy was neutralized under its own side's code (`neutralize3.py`): every AI route at the `127.0.0.1:9` blackhole with the key variable unset, the teacher route included; rewrite, rerank, dense and embeddings off.
- **Environment.** `env -i` with an empty `HOME`, `CODEX_HOME` and config, and `LEARNLOOP_NOTES_TEND=off`.
- **Audit hook.** `run.py` logs every process start and refuses Codex starts and non-loopback sockets. A self-test confirmed it refuses a `1.1.1.1:443` connect and a `codex` start.
- **Code.** `git archive` of main `1a33bb5db3` and of the branch `ef5c183623`, each with `src/`, `migrations/` and `tests/`.

Each copy, under its side's code, ran a bare `upgrade` (mvp-0.35 → mvp-0.41 on both sides, head 234), the primary desktop start, `migrate_vault` (0 applied) and `rebuild-derived-state`.

**The prompt capture (`prompt_capture.py`).**

- It opens a lesson through the sidecar's own `lesson.turn` at a frozen clock with deterministic ids.
- The teacher service's `execute_structured_operation` is replaced by a capture. The capture writes the rendered prompt and the strict result model's JSON schema, then raises, so no transport is ever reached.
- `teacher.enabled = true` on every capture copy.
- "Off" means `teacher.visuals = false`. "On" is the default.

| Check | linear_algebra | probability | arxiv_v2 |
|---|---|---|---|
| Today, branch (defaults: `teacher.visuals` on) vs main | byte-identical (525266 B) | byte-identical (740827 B) | byte-identical (344204 B) |
| Plan dump, branch vs main | byte-identical (84699 B) | byte-identical (124024 B) | byte-identical (32436 B) |
| Teacher prompt, visuals off vs main | byte-identical (20916 B) | byte-identical (22465 B) | byte-identical (18351 B) |
| Turn schema, visuals off vs main | byte-identical (`TeacherTurnV1`, 6760 B) | byte-identical | byte-identical |
| Visuals on (default) | `prompt_version: teacher_turn.v1+visuals-v1`, schema `TeacherTurnVisualsV1` with `visual` | same | same |
| Lesson start (`lesson.turn` open), routes blackholed | refused `plan_unavailable` before any call; lessons/turns/receipts (0,0,0) → (0,0,0) | refused; (0,0,56) → (0,0,56) | refused; (0,0,0) → (0,0,0) |
| `rebuild --shadow` (branch) | 0/0/0, live unchanged | 0/0/0, live unchanged | 0/0/0, live unchanged |

- **What changes with visuals on.** Against visuals off, the visuals-on prompt differs in exactly two lines: the version line, and the instructions with the visuals paragraph appended. The context is identical. The capture runs left `interactive_figures` and `model_call_receipts` unchanged.
- **Model calls.** 0 new model-call receipts across the 18 compared databases. Probability keeps its 56 historical rows.
- **Audit log.** It is empty after the smoke and the capture runs: no process start, no socket and no Codex process.
- **The first capture pass.** It refused with `plan_unavailable` before capturing, because the stub did not pass `_require_metered_settings`. The stub was then marked as an in-process fake, and the captures above are from the corrected script (`capture.sh` reran linear_algebra).
- **No real lesson** and no real figure were run.

### Rulings (verbatim)

- **R1:** "Lesson figures are grammar and sketch only (the turn waits on its figure), following the teacher spec and P3's R1. Accepted."
- **R2:** "teacher.visuals ships on by default (frictionless defaults); the owner may override at the first real-lesson checkpoint. Off restores TE1's prompt and schema byte for byte."
- **R3:** "D8: P3's chooser may offer a lesson figure as explore_figure help on a qualifying practice item; it is counted and reveal-checked like any P3 figure, help never certification. Accepted as built."
- **R4:** "'Not right?' inside a lesson is out of scope for P4b; queued as a follow-up only if the owner wants it after the checkpoint."

### Owner items

1. **A real lesson with a visual** on a `fixtures-local` backup copy, on the plan (§5 item 1). Check that the teacher uses visuals sparingly and well, and that the figure is the manipulative the goal asked for. Edit the doctrine paragraph if needed. It was not run here.
2. **The `teacher.visuals` default** (R2). It ships on. The owner may turn it off at that checkpoint; off restores TE1's prompt and schema byte for byte, as the smoke confirms on all three vaults.

### Open items

- **P5 prebuilds of planned visuals** must send exactly `teacher.visuals.figure_request`'s request, or they miss the turn's input hash and the figure is built twice.
- **"Not right?" inside a lesson** (R4). It is queued only if the owner wants it after the checkpoint.
- **followups-nov2 and P5 still to merge.** followups-nov2 (learner-state provenance, recorded-input reuse keys, mvp-0.42, migration 235) and P5 both touch `figures/service.py` and will merge on top of this. Lesson figures (teacher origin, fixed grounding, no rich spawner) must carry nov2's learner-state provenance rules where they apply.
- **`V._budget_refused` is too broad** (from the Codex fix record). A figure refused by the figures' *own* daily envelope (`FigureRefused("capped")` from `SpendLimitExceeded`) would close the lesson `budget` instead of recording the figure `unavailable`. Narrowing it to the lesson gate's refusal is a small follow-up.
- **The sketch-sandbox vitest timing race** above (`sketchSandboxReview.test.tsx`, t_max playback under full load). It is pre-existing and outside P4b.

### Checks

- **Ancestry.** Main `1a33bb5db3` is an ancestor of the tip.
- **Tracked databases and binaries.** None added or changed against main.
- **Untouched files.** `.gitignore` and `README.md` are unchanged.
- **`fixtures-local`.** Nothing from it is tracked.

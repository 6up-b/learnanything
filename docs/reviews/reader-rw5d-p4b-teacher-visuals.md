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

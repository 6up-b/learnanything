# Teacher TE1: the first good lesson (with curriculum C4)

**Stage:** `teacher-te1-first-lesson`, branch `teacher/te1-first-lesson` (worktree `learnanything-astrafix`), base
`02614cfddd` (main: `mvp-0.40`, migration head 229). **Specs:** `docs/specs/spec_teacher_v1.md` §20's TE1 contents
list (with §8, §9, §12, §13, §17, §18, §19), and `docs/specs/spec_deliverable_curriculum_v1.md` §8.2 / §12's C4 row
(folded in: TE1 was unlanded, so TE1's successor carries it). **No paid or live call was made**: every model is a
fake (`tests/teacher_fakes.TeacherFake`: a scripted teacher and a blind grader; C2's `NoteLinkFake` and fake tend for
C4); every ad-hoc script ran under `env -i` with an empty, existing `HOME`, `CODEX_HOME` and `LEARNLOOP_CONFIG_DIR`
(`scratchpad/te1/iso.sh`). No owner vault was opened, `~/.config/learnloop` was not read, the real `tend` was never
run, and nothing ran against `fixtures/linear_algebra`, `fixtures/probability` or `fixtures/arxiv_v2`.

**A successor**: `mvp-0.41` after `mvp-0.40` (ONE constant, `TEACHER_ALGORITHM_VERSION`). **One migration**: 230
(learner/data-relax-2 and curriculum C5 may claim 230/231 first: renumber at the merge; the head fixture is
`migration_head_230`).

## What was built

| Piece | Where |
|---|---|
| The tag `TEACHER_ALGORITHM_VERSION = "mvp-0.41"`, appended to `SUCCESSOR_CHAIN`; `TEACHER_VERSIONS` | `src/learnloop/algorithm_versions.py` |
| The upgrade (the mvp-0.36…0.40 pattern): accepts mvp-0.40 or mvp-0.9 onwards through the chain; one journalled `BEGIN IMMEDIATE` activation; `complete_interrupted_activation` hands an earlier link's journal down; the CLI's and the sidecar's installed completion is this link's; `learnloop upgrade --to mvp-0.41` and the bare upgrade's target | `src/learnloop/teacher_upgrade.py`, `cli/app.py`, `cli/runtime.py`, `learnloop_sidecar/context.py`, `activation_journal.py`, `pyproject.toml` |
| Config `[teacher]`: `enabled` (the successor's kill switch), `weight.learned`, `weight.source` (`pool`/`parametric`), `brief.depth` (keep), `brief.use_deliverable` (C4), `context.sources_tokens` (keep), `delayed.*` (R* = 0.9 published; 3 and 7 days legacy; 14-day keep), `metered_price_per_million`, `max_lesson_cost_usd`; all classified in the parameter registry; every defaults snapshot mvp-0.9…mvp-0.40 recomputed with a note (the keys are present and inert below the tag; dropping them reproduces main's values, tested) and mvp-0.41 recorded | `config/schema.py`, `config/template.py`, `params/parameter_registry.py` |
| The `teacher` AITask (operation `teacher_turn`), default route the plan's medium tier (keep), `METERED_PRICE_SETTINGS["teacher"] = teacher.metered_price_per_million` (no OpenRouter offer until set), the disclosure | `ai/routing.py`, `config/schema.py`, `ai/plan_fallback.py`, `ai/disclosures.py` |
| Migration 230: `lessons`, `lesson_turns`, `lesson_plans` (RAW_LEDGER; a lesson closes once), `lesson_turn_payloads` (WORKFLOW), `lesson_checks`, `lesson_receipts` (RECEIPT, append-only), `lesson_weight_state`, `lesson_weight_trace`, `confidence_calibration_state` (DERIVED, one replayer); `source_tool_calls.caller_kind` widened with `teacher` (a temp-then-rename rebuild as 208/212); every table classified in `table_roles`, AD's `protected_tables` (DENIED) and `column_classes` | `migrations/230_teacher_lessons.sql`, `db/table_roles.py`, `adaptive_difficulty/protected_tables.py`, `adaptive_difficulty/column_classes.py`, `fixtures/migration_head_230/` |
| `learnloop.teacher`: contracts (`LessonBriefV1`, `TeacherTurnV1`, `LessonReceiptV1`, the strict action model), doctrine v1 (our own words, `teacher/doctrine/v1/*.md`, version and hash on every lesson and receipt), the brief, the read actions, the guards, the checks, the delayed checks, the service, the report | `src/learnloop/teacher/` |
| The lesson store | `db/stores/lessons.py` |
| The learned lesson-check weight (§12.1), the forecast pool (§12.2) and the tap/hedge recalibration (LP-min), with the neutral ADF numerics factored out of AD's model (AD now imports them; numerics identical, pinned) | `learner/lesson_weight.py`, `adf_numeric.py`, `adaptive_difficulty/model.py` |
| The one seam into mastery: the attempt step reads a lesson check's recorded mass (`lesson_check_mass`, only for `reconstruction_after_walkthrough`) for both the reliability factor and `MasteryObservation.attempt_evidence_mass`, live and in replay | `attempts/attempts.py`, `learner/recall_coverage.py` |
| The DERIVED replayer `lesson_weight` (depends on `learning_state`) | `substrate/rebuild_orchestrator.py` |
| Two forecast kinds `lesson_check_correct` (bound to the check's attempt) and `lesson_step_retained` (bound to the first qualifying cold outcome on the node's LO), scopes `lesson_check`/`lesson_node`, decision kind `lesson` | `scheduling/forecast_receipts.py` |
| Caller kind `teacher` (reading; assisted practice bound to an open check's minted item); recorded and model-written in `source_tool_calls` | `source_retrieval/policy.py`, `instructional/tools.py` |
| The lesson hold: a minted check item (`provenance.mechanism = teacher_lesson_v1`) is never served by a routine door | `vault/lifecycle.py` |
| `lesson.turn` (open, reply, answer_prediction, answer_check, stop: ONE origin action, so a T1 grant covers the lesson and its inline grading) and `lesson.view` (resume, no model call); desktop only | `learnloop_sidecar/handlers/lesson.py`, `handlers/__init__.py` |
| `learnloop teacher report` (the weight's report lines) | `cli/teacher.py`, `teacher/report.py` |
| The desktop lesson screen (document typography, interjection cards, the plan map as positions, predictions open, checks collapsed, the thinking field and the tap after a draft, the close card promising only committed checks, an inspector strip), "Teach me this" on the LO inspector and on a Reader selection, the quick-check button at open; `teacher.lessons` in the UI config (absent while off) | `apps/learnloop-tauri/src/screens/LessonScreen.tsx`, `components/InspectorOverlay.tsx`, `screens/ReaderScreen.tsx`, `screens/reader/NotesRail.tsx`, `app/App.tsx`, `app/algoConfig.ts`, `api/client.ts`, `api/dto.ts`, `src-tauri/src/{commands,main}.rs` |
| The teacher layering contract (no evidence writer, no AD internals) | `pyproject.toml` |
| Generated references (DB, config, desktop) regenerated; validators' pinned counts moved (schema head 230; 1118 config leaves; 303 TS sources) | `docs/learnloop-architecture-vault/` |
| Spec "as built" notes (§20 and the C4 amendment in §8.1; the curriculum spec's §8.2) | `docs/specs/spec_teacher_v1.md`, `docs/specs/spec_deliverable_curriculum_v1.md` |

## How it works (the decisions taken here)

1. **The lesson loop.** Each learner action runs one teacher call. A turn that asks for read actions gets exactly one
   further call with their results; read actions that call asks for run too and their results ride with the next
   learner action (a structural bound: no count was chosen). A turn that fails the schema, the contract (a second
   open check, an anchor that does not resolve, an empty turn) or a guard is refused back to the model with its
   reason; three consecutive refusals close the lesson `teacher_contract_failure` (keep, §18.4).
2. **The output guards** (§9.3) run on the message, its choices and any posed prediction or check text: keys
   (`leaks_key` over every recorded key on the brief's LOs, the lesson's own check items exempt; an unreadable
   KeyBook withholds everything), the open check's solution (and the solution of the check the same turn poses), and
   citations (`[S3]` must name a delivered passage; a quote before a citation must be in it).
3. **Checks.** Posing mints a held item (one YAML per check; its committed solution the key, its criteria the rubric;
   span `source_refs` for anchors; `anchored: false` shows "LearnLoop's answer"). Answering grades the answer only
   through `request_vault_grading_proposal` (blind in a split vault), records one `lesson_checks` row (the mass and
   every weight input) and then the `reconstruction_after_walkthrough` attempt in the same transaction; the attempt
   step reads the row. The thinking note goes to the teacher only (tested against every grading prompt).
4. **The learned mass (§12.1).** A Gaussian over `(η₀, β_c, β_p, u_L…)` per τ point {0.1, 0.2, 0.4}, from seeded
   priors (lp_priors_v1, every one labelled in the registry). A qualifying outcome is a graded attempt on the LO, of
   AD's cold types, unprimed, unhinted, the item's first, with no reveal on the item before it, after the check. Its
   likelihood is the mastery model's own update recomputed for the check's mass σ(η) from the check's recorded prior
   state, item parameters and grade, with the drift to the outcome by `mastery.sigma2_drift` (the moderated
   logistic). **First order:** the observations between the check and the outcome are not re-folded (they would
   shrink the check's share; this overstates a late outcome's information a little, never its direction). An outcome
   resolving `n` checks enters each factor at power `1/n` (it counts once). Filtering: the mass applied is the
   posterior mean of σ(η) as of the check (events strictly before it); the replay recomputes it and the trace keeps
   both (`mass_mismatches` is empty, tested).
5. **The pool (§12.2).** Beta(1, 4) on 21 points per forecaster (doctrine version + model). A check on a node whose
   retention the teacher already forecast in this lesson enters at the pool-implied mass (a bisection on the logit
   scale for the mass at which the mastery prediction equals `λ̂·p_B + (1−λ̂)·p_A`); no forecast yet: §12.1's mass.
   `p_A` is recorded with the forecast as the LO's predicted success (the cold item is unknown when a node lands).
6. **`z_c` and `z_p`.** `z_c` is the recalibrated tap (else the hedge read) on the logit scale, centred on chance;
   `z_p` is the active predictor's success on the LO, centred at AD's band middle: AD exposes no per-LO prediction at
   the check's level (§5.7: no public API), so the brief shows AD's readiness line beside the predictor's.
7. **The DERIVED tables** are written only once a lesson check exists (the live path after each check, the replayer
   on rebuild), so a lessonless vault's rebuild writes nothing: zero shadow deltas, tested; with lessons, the rebuild
   reproduces the live tables row for row, tested.
8. **Reveals (§12).** After a shown message, each vault item on the brief's LOs (the lesson's own items excepted)
   gets a `tutor_answer` row at the tutor's own overlap measure, and a `source_review` row for what a cited passage
   exposes, basis `lesson:<id>`. Note: the tutor's measure counts common words, so teaching text on a topic can
   prime its items over a lesson; that is the spec's rule (`as at tutor_qa`), and the delayed-check picker excludes
   items this lesson exposed.
9. **Help during a check.** A learner reply while a check is open is help: a `help_assists` row (surface `tutor`,
   never folded into an attempt); the reply is not withheld, and when it overlaps the committed solution at the
   auto-prime threshold the check is withdrawn (no attempt) and the learner told.
10. **Delayed checks (§13).** Code picks: per landed node (a `lesson_step_retained` forecast or a fully right check)
    an unattempted, servable, unwithheld vault item of its LO with no reveal from this lesson (nor exposure elsewhere
    at the auto-prime sum), pitched nearest AD's band middle; one transfer item on a downstream LO, else another goal
    LO item. **Deviation:** not `find_practice`'s ranking, which may call a paid rerank model. Dates from the FSRS
    stability the lesson's checks left on the LO at R* (else the seeded fallbacks), capped at 14 days. A missing item
    is recorded on the receipt.
11. **Spend (§17).** A plan route needs nothing; a metered route needs `teacher.metered_price_per_million` **and**
    `teacher.max_lesson_cost_usd` (unset: refused before sending), and the lesson's recorded usage is held to the cap.
12. **C4.** The deliverable is the nearest active one whose resolution names a lesson LO; the brief takes its sentence,
    the resolution's phrase per LO, the path's primaries whole and alternates as outline; `your_notes` are C2's
    effective links' headers; `read_note` returns a stored snapshot (no tend call during a lesson). Off: none of it.

## Not built in TE1 (open)

- Compaction (§7): no `teacher.context.compact_at` key (a key nothing reads would be dead); TE1 lessons fit the budget.
- The turn's `visual` (RW5d's `FigureRequestV1` with origin `teacher`).
- TE1b (router suggestions, `router_suggestion_responses`), TE2 (probes, typed goals, `propose_gap`, resume UI).
- A retention pruner for `lesson_turn_payloads` (WORKFLOW).

## Owner items for the landing

1. **One real lesson on a `fixtures-local` backup copy** (the spec's TE1 gate; it needs a plan call).
2. **`teacher.max_lesson_cost_usd`** from that dry run (Q7), and the teacher route's tier.
3. The working vaults upgraded to the chain's head before the first real lesson (Q12).

## Renumbering at landing

The tag is ONE constant; if another successor lands first, move `TEACHER_ALGORITHM_VERSION`, the pins in the tests
named `mvp-0.41`, the snapshot entry and its notes, and the CLI text. The migration: rename `230_teacher_lessons.sql`,
rebuild `migration_head_<N>` from main's head with it, and move the fixture paths and the reference scripts'
`SCHEMA_HEAD`.

## Gate (this step; the full suite, the whole durability lane and the whole vitest run are the landing's)

Every pytest/vitest/npm/cargo command ran inside `systemd-run --user --scope --quiet -p MemoryMax=5G
-p MemorySwapMax=1G`, pytest at `-n 6`, vitest at `--maxWorkers=4`, one run at a time; the big targeted run behind
`flock /tmp/learnloop-fullsuite.lock`.

- `uv sync --extra dev --extra mobile`, `uv pip install pypdfium2`: ok.
- `uv run lint-imports --no-cache`: **38 kept, 0 broken** (with the new teacher layering contract and the notes
  contract's teacher sources).
- **Targeted pytest, wide set** (256 files: every new TE1 file and every existing file that names a changed module,
  table or contract: the version chain and its pins, the defaults snapshot, routing/price/disclosures, the
  orchestrator and table roles, AD's protected tables and model, forecast receipts, attempts and replay, the
  lifecycle hold, the instructional dispatcher and source tool calls, the head-fixture and migration tests, notes
  guards, the sidecar contract, the CLI help snapshot, architecture, public-tip, tracked fixtures, sqlite copies):
  **10424 passed, 57 failed, 16 skipped, 8 xfailed** in 45 min. Every failure was an expectation this stage moves
  (the chain's latest and its slices, the head at 230 and the earlier migrations' "nothing else" diffs, the
  disclosure list, the notes guards' allowed readers) or the Codex turn sweep flagging `S.turn(...)` (renamed
  `take_turn`); all fixed (`tests/test_teacher_te1_migration.py` exports `TE1_ADDED_OBJECTS` /
  `TE1_ALTERED_TABLES` for the diffs; the notes are reached only through `teacher.notes`, never by the minting).
- **Rerun of the 32 failing files + the TE1 migration test + session ownership: 400 passed, 6 skipped, 1 xfailed.**
- **Rerun of the touched set after the last refactor** (the four TE1 files, the migration test, notes guards and
  linking, the Codex sweep, judge routes, architecture, mobile allowlist, desktop RPC contract, the moved pins,
  registry audit, CLI help snapshot, config refactor): **673 passed, 6 skipped, 1 xfailed**.
- Durability: `-m durability` over the TE1 files and every migration/head-fixture file above: **15 passed**;
  the TE1 files with `--durable-sqlite`: **53 passed**.
- Frontend (`apps/learnloop-tauri`): `npm install` ok; `npm run typecheck` ok; `npx vitest run --maxWorkers=4
  src/app/lessonsConfig.test.ts src/screens/LessonScreen.test.tsx src/components/InspectorOverlay.phase4.test.tsx`:
  **11 passed (3 files)**; `npm run frontend:build` ok.
- `cargo check --manifest-path apps/learnloop-tauri/src-tauri/Cargo.toml`: ok.
- References: `db_generate_reference.py` + `db_validate_reference.py`: errors `[]` (schema head 230, 369 table
  notes, 1118 config leaves); `desktop_generate.py` + `desktop_validate.py`: passed (303 TS + 6 Rust).

TE1 test files (for the landing gate): `tests/test_teacher_te1_lesson.py` (lifecycle, every action, guards,
protection sentinels, withdrawal, reveals, switches), `tests/test_teacher_te1_weight.py` (the weight, the pool,
the recalibration, DERIVED replay equivalence, the attempt-step seam, the report),
`tests/test_teacher_te1_successor.py` (the tag, defaults parity, byte-identical practice with the switch off or below
the tag, shadow rebuild zero deltas, the whole rebuild, upgrades, RPCs, the price gate),
`tests/test_teacher_te1_curriculum_c4.py` (the deliverable brief, notes and `read_note`, C4 off), and
`tests/test_teacher_te1_migration.py`; the fakes are `tests/teacher_fakes.py`.

**No paid call; no live call.** Every model was a fake; every ad-hoc script ran isolated (`env -i`, empty `HOME`,
`CODEX_HOME`, `LEARNLOOP_CONFIG_DIR`).

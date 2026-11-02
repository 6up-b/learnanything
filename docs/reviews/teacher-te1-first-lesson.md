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
   both (`mass_mismatches` is empty, tested). *Codex review F2/F6 (`teacher-te1-first-lesson-codex-review.md`):
   held grades are excluded, and the likelihood now recomputes the LO's recorded trajectory (the check's own
   observation factors and every intervening update), the first-order form only as a named fallback.*
5. **The pool (§12.2).** Beta(1, 4) on 21 points per forecaster (doctrine version + model). A check on a node whose
   retention the teacher already forecast in this lesson enters at the pool-implied mass (a bisection on the logit
   scale for the mass at which the mastery prediction equals `λ̂·p_B + (1−λ̂)·p_A`); no forecast yet: §12.1's mass.
   `p_A` is recorded with the forecast as the LO's predicted success (the cold item is unknown when a node lands).
   *Codex review F5: `p_A` and the inversion are now both for the committed cold item at its horizon.*
6. **`z_c` and `z_p`.** `z_c` is the recalibrated tap (else the hedge read) on the logit scale, centred on chance;
   `z_p` is the active predictor's success on the LO, centred at AD's band middle: AD exposes no per-LO prediction at
   the check's level (§5.7: no public API), so the brief shows AD's readiness line beside the predictor's.
7. **The DERIVED tables** are written only once a lesson check exists (the live path after each check, the replayer
   on rebuild), so a lessonless vault's rebuild writes nothing: zero shadow deltas, tested; with lessons, the rebuild
   reproduces the live tables row for row, tested. *Codex review: both are now bounded at the latest answered check,
   so a later cold outcome no longer separates them.*
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

## Landing onto main

Branch `teacher/te1-first-lesson` (worktree `learnanything-astrafix`), from `15a001d7ad`. The orchestrator
fast-forwards and pushes.

How every run was made:

- **Isolation.** Every Python or CLI run outside pytest ran under `env -i`, with an empty `HOME`, `CODEX_HOME` and
  `LEARNLOOP_CONFIG_DIR` and `TMPDIR` outside the worktree.
- **Memory scopes.** pytest, vitest, npm and cargo ran in `systemd-run --user --scope`. The full suite ran at 10G
  under `flock /tmp/learnloop-fullsuite.lock`; the rest ran at 5G, with vitest at `--maxWorkers=4`.
- **No model calls, no real lesson.** No live model call was made, and no real lesson ran: that is R6's owner item.
- **Notes.** The owner's real `tend` was never run, and no note of the owner's was read.
- **Vaults.** No owner vault was opened. Only fresh backup-API copies of
  `learnanything-ad1/fixtures-local/owner-copies-mvp035` were used.

### Step 0: Codex re-review 2, directed fixes (`c00622f91e`, `9543d8c96d`)

Codex job `20261101-222330-VW72um` and the latest re-review confirmed these fixed: F1, F2, F14 and F15, and F5–F13
from round 1. They reopened F3 and F4 and raised F16 (Medium). The regression tests were written first and committed
alone (`c00622f91e`). All five failed on `15a001d7ad`, each for its finding's own reason. The record is
`teacher-te1-first-lesson-codex-review.md`, "Re-review 2".

- **F3 (R2): reveals use the strict writer.** `_record_reveals` now writes through
  `attempts.reveal_ledger.record_reveal_strict`, inside the accepted turn's transaction. A failed reveal write rolls
  back the accepted turn, its delivered results and every reveal row together. `resume` then makes the call again.
  Test: `test_r3_f3_a_failed_reveal_write_leaves_the_turn_unaccepted`.
- **F4 (R1): structural; this is the third round on saved-context protection.**
  - **What is recorded.** `teacher.brief.protection_state` is recorded in the lesson's `open` entry with its brief.
    It holds two digests:
    - a vault digest of the section library's protection key, plus every item that exam or held-out material or a
      live reservation withholds;
    - a digest of why each item the brief names (its probes and the items behind its history entries) is withheld
      now.
  - **When the lesson ends.** The check runs before every model call of an action: in `take_turn` and before each
    call in `_teach_loop`, a read follow-up included. The lesson closes `protection_changed` when any of these holds:
    - the state differs from the recorded one;
    - the state cannot be read;
    - a delivered passage is no longer teachable.
  - **What is kept.** Every earlier ledger entry stays. The close runs as every close does: delayed checks under the
    current protection, the receipt, the row and the entry in one transaction. The notice offers a fresh lesson, and
    the screen's **Start a fresh lesson** opens one on the same topics with a fresh brief.
  - **When the lesson opens.** The state is read before and after `build_brief`. A change in between refuses the
    opening, with nothing saved.
  - **What was removed.** The word-matching redaction path is gone because it is redundant: nothing saved under an
    older state is ever resent. The removed code: `revalidate_material`, `_redact`, `_redacted_transcript`,
    `_protected_texts`, `_scrub`, `WITHDRAWN` and `LessonState.withheld_items`.
  - **What was kept, and why.** These guard delivery, not resending: `SourceBook.revoked`, `read_source`'s
    teachability refusal and the citation guard.
  - **What the state does not cover.** A cold hold on an item that only a `find_practice` result listed; the old
    redaction did not cover it either. Its exposure is in the reveal rows the cold lane reads.
  - **Schema and contracts.** `lessons.close_reason` and `contracts.CLOSE_REASONS` gain `protection_changed`.
  - **Tests.** Four `test_r3_f4_*` tests replace the four redaction tests.
- **F16 (R3): ruled Low; no change, queued follow-up.**

Step 0's gate: lint-imports 38 kept; the targeted 20 files 561 passed, plus 4 `test_registry_audit` failures for a new
module constant, which was removed (rerun 88 passed); typecheck ok; `LessonScreen` vitest 10 passed.

### Merges

Main moved four times while this landed. TE1's migration was renumbered at each merge that added one: **230 → 232 → 233 → 234**. The head fixture was rebuilt every time from main's tracked, sanitized head, with only TE1's migration applied. The rebuild steps each time:

1. a backup-API copy under the gitignored `fixtures-local/landing-te1/`;
2. `apply_migrations` under `UPGRADE_SCRATCH_COPY`;
3. `wal_checkpoint(TRUNCATE)` (0, 0, 0) and `journal_mode=DELETE` (header 1/1);
4. `integrity_check` ok and `foreign_key_check` empty;
5. copied into place with the backup API, with no companion files.

Against main's head, only the nine lesson tables were added (with their indexes, triggers and autoindexes, no rows), only `source_tool_calls` changed, and only `schema_migrations` gained a row. The companion files are byte-identical to main's, and the README gains a TE1 section above main's latest.

| Commit | What |
|---|---|
| `4ac280e348` | **Merge of main `de73fbda51`.** It brought learner-blindness relax, data-relax 2 (migration 230), curriculum C5 (migration 231), followups-nov1c, the sketch compartment, C3 and C2. TE1 moved 230 → 232 and `migration_head_232` was rebuilt from main's `migration_head_231`. In 53 test files, the sanitizer and the two reference scripts, these were updated: head paths, `SCHEMA_HEAD`, chain lists and the composed sets (`DR2 \| C5 \| TE1`). `template.py`: both sides' notes kept, every fingerprint recomputed after clearing `.pyc`, second pass 0. Rust and TS: `lesson_turn`/`lesson_view` placed beside `notes_hidden`/`notes_set_gaps`; `desktop_validate.py` composed. Generated references: main's side, regenerated. |
| `97636d581b` | The defaults parity test pins main's snapshot values. The codex-review record names the step-0 commit. |
| `446a0cf899` | **Merge of main `67c05ed37c`** (Reader RW5d P4a: no migration, no config change). The only conflicts were generated references, which were regenerated. Targeted figures/correspondents set: 782 passed. |
| `e74f3156e0` | **Merge of main `947200afee`** (Reader RW5d P3: migration 232). TE1 moved 232 → 233 and `migration_head_233` was rebuilt from P3's `migration_head_232`. The composed sets became `P3 \| TE1`; P3's own migration test and data-relax 2's `_later()` compose TE1. `algoConfig.ts`: `ask.figures` beside `teacher.lessons`. |
| `95dd20a1d4` | Data-relax 2's migration test composes only TE1's objects that have SQL, since its schema reader skips autoindexes. Parity pins moved. |
| `6975ac1949` | **Merge of main `19c72752b3`** (curriculum C2b, vault-native notes: migration 233). **TE1 moved 233 → 234** and `fixtures/migration_head_234` was rebuilt from C2b's `migration_head_233` (main `19c72752b3`). `SCHEMA_HEAD` is 234 and the chain lists run `[..., 232, 233, 234]`. C2b's and P3's migration tests compose TE1. `teacher/notes.py` now uses C2b's API: `note_links.effective(repository, rows, vault=...)`, whose vault-native snapshots withhold a note whose anchor now sits beside protected material. The tend wording is gone from TE1's code and tests. Note text is learner text (owner, Nov 1); `read_note` returns the linked snapshot's text, not a live re-read. The C4 test uses C2b's `_deliverable`. `template.py`: C2b's and TE1's notes kept, every fingerprint recomputed (second pass 0). TE1's code comments and the spec's §20 note now name migration 234. |
| `9c8d758f27` | The defaults parity test pins main's values at `19c72752b3`. |

State after the last merge:

- `db_validate_reference`: errors `[]` (369 table notes, 1119 leaves; the prose counts in `Database.md` and `Configuration.md` were moved);
- `desktop_validate`: 307/307 TS + 6/6 Rust, ACTIVE 313, reproducible byte for byte;
- `validate_vault`: passed (1388 notes);
- defaults fingerprints: all 32 equal `defaults_fingerprint_for_version`.

The manual Python resolutions were limited to: head paths, chain lists and composed sets (the data a migration renumber needs); snapshot data; the two test pins; and the C2b notes adaptation (`teacher/notes.py`, the C4 test). The full suite ran on the final tree, after all of them.

**Final: migration 234, successor `mvp-0.41`.** The chain on main ends at `mvp-0.40`; RW5d P3 and C2b added no successor. followups-nov2 lands after this as `mvp-0.42` with migration 235.

### Gate (final tree `9c8d758f27`, on main `19c72752b3`)

| Step | Result |
|---|---|
| `uv run lint-imports --no-cache` | **41 kept, 0 broken** |
| Targeted head-fixture, migration, TE1 and notes set after the C2b merge (105 files) | 1687 passed, 12 skipped, 3 xfailed, 1 failed. The failure was the defaults parity pin, re-pinned in `9c8d758f27`; that file then passed 13. |
| Full pytest (`flock /tmp/learnloop-fullsuite.lock systemd-run --user --scope -p MemoryMax=10G -p MemorySwapMax=2G -- <env -i> uv run --no-sync pytest -n 8 -p no:cacheprovider --dist worksteal --durations=50 -o faulthandler_timeout=600 --junitxml=…`) | **23793 passed, 90 skipped, 47 xfailed, 0 failed** (40:58) |
| Durability lane (`pytest -m durability -n 6`, 5G) | **185 passed, 1 skipped** |
| Owner lane (`pytest -m owner_vaults -n 6`; `LEARNLOOP_OWNER_VAULTS` = fresh `copy_tree_with_databases` copies of the mvp035 owner copies in the gitignored `fixtures-local/landing-te1/owner-lane`) | **83 passed, 2 failed, 4 skipped.** Both failures are the known ones: `test_activity_backfill::test_backfill_logs_attempt_duration_interaction_events` and `test_placement_fixture_copies::…[arxiv_v2]`. 0 new receipts; probability keeps its 56 historical rows. |
| Frontend: `npm install`, `npm run typecheck`, whole vitest (`--maxWorkers=4`, 5G), `npm run frontend:build` | install ok, typecheck ok, **257 files, 2446 passed**, build ok |
| `cargo check --manifest-path src-tauri/Cargo.toml` | ok |

Earlier runs:

- **Stopped full gates.** Two full gates (on `97636d581b` and on `446a0cf899`) were stopped unfinished because main moved under them; their results are not counted.
- **Unexpected failure, rerun alone.** One unexpected failure on the merged tree, `test_ux_phase1_round2_rereview::test_f8_a_keep_ahead_that_failed_is_retried_off_the_rpc_path` ("cannot join thread before it is started", a thread race in a file TE1 does not touch), passed 3 of 3 when rerun alone.

### Smoke on fresh owner copies (`fixtures-local/landing-te1-smoke4/`, driver `scripts/smoke.sh`)

**Setup.**

- **Copies and routes.** Fresh backup-API copies of the three mvp035 owner copies. Each was neutralized under its own side's code (`neutralize3.py`): every AI route at the `127.0.0.1:9` blackhole with the key variable unset, the teacher route included; rewrite, rerank, dense and embeddings off.
- **Environment.** `env -i` with an empty `HOME`, `CODEX_HOME` and config.
- **Audit hook.** It logs every process start and refuses any non-loopback socket. A self-test confirmed it catches both kinds.
- **Code.** `git archive` of main `19c72752b3` (mvp-0.40) and of the branch `9c8d758f27`, each **with `src/`, `migrations/` and `tests/`**.

Each copy ran under its own side's code:

1. a bare `upgrade`: mvp-0.35 → mvp-0.40 on main (head 233), mvp-0.35 → **mvp-0.41** on the branch (head 234);
2. the primary desktop start;
3. `migrate_vault`;
4. `rebuild-derived-state`.

| Check | linear_algebra | probability | arxiv_v2 |
|---|---|---|---|
| Today, `teacher.enabled = false` vs main | byte-identical (525266 B) | byte-identical (740827 B) | byte-identical (344204 B) |
| Today, `teacher.enabled = true`, no lessons, vs main | byte-identical | byte-identical | byte-identical |
| Plan dump, teacher off vs on (branch) | byte-identical | byte-identical | byte-identical |
| Plan dump vs main | differs only in the version label | same | same |
| Lesson start (`lesson.turn` open), routes blackholed | refused `plan_unavailable`, no call; lessons/turns/receipts (0,0,0) → (0,0,0) | refused; (0,0,56) → (0,0,56) | refused; (0,0,0) → (0,0,0) |
| `rebuild --shadow` | 0/0/0, live unchanged | 0/0/0, live unchanged | 0/0/0, live unchanged |

**Plan dump vs main, in detail.** The plan dump differs from main only in the version label:

- `algorithm_version` and `plan.algorithmVersion`: `mvp-0.40` → `mvp-0.41`;
- the version strings inside the router decisions' and AD selections' `versions_json` and `detail_json`;
- the card, snapshot and payload hashes computed over them.

With the label replaced and those hashes dropped, the dump is identical for all three vaults (`plan_norm.py`). Today has no version label and is byte-identical.

**Model calls and sockets.**

- 0 new model-call receipts across 15 compared databases.
- The audit log is empty: no non-loopback socket, and in fact no socket and no process start at all. The blackholed lesson start is refused before any request.
- No real lesson was run (R6).

The same smoke ran clean on the three earlier trees as well:

- `97636d581b` vs main `de73fbda51`;
- `446a0cf899` vs `67c05ed37c`;
- `95dd20a1d4` vs `947200afee`.

### Rulings (verbatim)

- **R1:** "F4 class closed structurally: a lesson whose vault protection state changed since its brief was built is ended with protection_changed and must restart with a fresh brief; no saved-context redaction is attempted."
- **R2:** "F3 fixed with the strict reveal writer; acceptance and exposure accounting commit or roll back together."
- **R3:** "F16 (one extra follow-up call on resume after a completed help action) is ruled Low under the proportionate bar: one extra plan call, metered calls stay under the lesson cap, no evidence or exposure effect. Queued follow-up."
- **R4:** "The lesson-check weight likelihood replays the topic's recorded mastery updates with only the check's mass varied (F6). Accepted."
- **R5:** "A metered lesson needs both teacher.price_per_million and teacher.max_lesson_cost_usd; until set, OpenRouter is refused (plan route unaffected). Owner item: set the cap after the first real lesson."
- **R6:** "The first real lesson on a fixtures-local copy (spec §20 gate) is an owner item: it needs one ChatGPT-plan call and the owner's go-ahead."

(The config key R5 calls `teacher.price_per_million` is `teacher.metered_price_per_million` in the schema.)

### Owner items

1. **The first real lesson** on a `fixtures-local` backup copy (R6; spec §20). It needs one ChatGPT-plan call and the owner's go-ahead. It was not run here.
2. **`teacher.max_lesson_cost_usd`.** Set it, together with `teacher.metered_price_per_million`, after that first lesson (R5; Q7). Until both are set, OpenRouter is refused for lessons; the plan route is unaffected.
3. **The working vaults** are upgraded to the chain's head (`mvp-0.41` from mvp-0.35 through the chain: back up, run `learnloop upgrade`, then `rebuild-derived-state`) before the first real lesson (Q12).

### Open items

- **Compaction (§7).** There is no `teacher.context.compact_at` key; TE1 lessons fit the budget.
- **The turn's `visual`.** RW5d's `FigureRequestV1` with origin `teacher` is not built.
- **Uncited-claim rejection.** A source claim the turn makes without a citation is not rejected; only quotes before a citation are checked.
- **Today entry.** There is no Today entry for lessons; they are reachable from the LO inspector and the Reader only.
- **Practice-now close offer.** The close card offers no "practice now".
- **The adopted §11 couplings.** They are not yet in the brief's nodes.
- **F16 follow-up (R3).** `_owes_followup` treats `check_withdrawn` as an action boundary, so resume can make one extra follow-up call after a completed help action.
- **TE1b.** Router suggestions and `router_suggestion_responses`. TE2 (probes, typed goals, `propose_gap`, resume UI) is also open.
- **Payload retention.** There is no retention pruner for `lesson_turn_payloads` (WORKFLOW).
- **Small copy fix.** When the teacher's client cannot be built at a lesson's *opening*, the sidecar's `plan_unavailable` message says "your lesson is saved", though nothing was saved (seen in the smoke; the refusal itself is correct). The wording should depend on whether a lesson id exists.
- **Cold holds outside the brief.** The R1 protection state does not cover a cold hold on an item that only a `find_practice` result listed, and the earlier redaction did not either; its exposure is in the reveal rows.

### Checks

- **Ancestry.** Main `19c72752b3` is an ancestor of the tip.
- **Tracked databases and binaries.** The only tracked database or binary change against main is the head fixture rename and rebuild (`migration_head_233` → `migration_head_234`, `state.sqlite` rebuilt; the companion `.bin` is a pure rename).
- **Untouched files.** `.gitignore` and `README.md` are unchanged.
- **`fixtures-local`.** Nothing from it is tracked.

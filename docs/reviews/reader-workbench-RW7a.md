# Reader workbench RW7a: reading paths in the Guide, display only (stage `reader-rw7a`)

Branch `reader/rw7a` (worktree `learnanything-rw4b`), base `main` at
`a76c8358a` (the RW4e landing; migration head 215; AD1, RW2b+H3, RW1c, RW4b,
DL2 (successor mvp-0.29), RW3b, RW4d and RW4e on main). Spec:
`docs/specs/spec_reader_workbench_v1.md` §1's RW7a line and §10.1 in full,
§11 (`reader_path_sections`, `[reading_paths]`, route `reading_path_judge`,
ledger task `reading_path_role`), §12's row (display, no successor), §14 G47
(RW7a's part), §15's reading-path measures, §18's DL2 note ("DL2's depth
intents map onto RW7a's depth choice as one setting"). UX
`docs/specs/ux_reader_workbench_v1.md` §4.11 (the path card, role chips,
"why", overrides), §2 Moment 0, wireframe W1, §4.0 (the seven states of a
model-backed action).

## 0. Plan (written before the code)

**Scope.** RW7a only: per source and depth, the Guide's *your path* card
shows each section as core, prerequisite, enrichment, already shown or
assumed, each with a one-line why and *read it anyway* / *skip it*; one
exercise worth trying per core section; the suggested next activity line;
the goal it serves (named, never created). Not here: RW7b (the plan following
the path; `reading_paths.plan_uses_path` is RW7b's key and is not added), the
sources spec's searched exercise candidates (below).

**Display only (G47, orchestrator note 1).** Nothing in the plan, evidence,
mastery, scheduling, projection or serving reads RW7a's tables. With RW7a on
and paths, depths and overrides stored, `get_daily_plan` and
`get_today_queue` answer the bytes a golden recorded on `a76c8358a` holds
(test). An override or *skip it* writes one `judgment_ledger` `learner_card`
row and one `reader_path_sections` row, nothing else (table diff test).
*Skip it* marks nothing as known.

**Data: migration 217** (AD2+AD3 holds 214, RW5a 216; the runner is
set-based). Two WORKFLOW tables, append-only by trigger, never replayed:
- `reader_path_sections` (the spec's columns): `id`, `extraction_id`,
  `depth`, `section_id`, `label`, `reason`, `exercise_span_id`,
  `learner_override` (`read_anyway` | `skip` | `none` = cleared; NULL on a
  judge row), `ledger_id`, `state_key`, `model`, `prompt_version`,
  `created_at`. A judge row per (extraction, depth, state_key, section),
  unique among judge rows (a partial unique index: a second process judging
  the same state writes nothing); an override row per learner press, the
  newest per (extraction, depth, section) standing across re-judgments
  ("is kept").
- `reader_path_depths`: the Guide's depth choice per source (`id`,
  `source_id`, `depth`, `created_at`), the newest standing. Orchestrator note
  7 allows "its own per-source row"; a depth is a source's, not a
  section's, so it is not folded into `reader_path_sections`.

**Depth and DL2: one setting, display-level mapping only (note 7).** The
Guide never writes DL2's tables. The depth shown is the newer of (a) the
Guide's own choice for the source and (b) DL2's intent-control choice on the
source scope (its own commitment for `{"kind": "source", "id": source}` or
for one of the source's readings), mapped Master -> fluency, Learn -> learn
to use it, Keep and Light touch -> get the idea; Check once, Reference,
Pause, Let go and no setting map to nothing. Neither exists: the Guide asks
once ("How deep do you want to go?") and makes no call until answered. So the
two read as one setting (whichever the learner set last governs the path),
while DL2's stored intent and everything it serves stay exactly
`a76c8358a`'s (test: a depth change leaves `commitments` and
`commitment_versions` untouched). Chosen because writing DL2 from the Guide
would change what DL2 serves (a serving change, F3) and DL2's control
already owns the source scope's commitments.

**Labels: one call per source and depth** (route `reading_path_judge`, a
chat task registered like the other Reader routes: `AITask`,
`ROUTE_FOR_OPERATION`, `ai.routing.reading_path_judge`, a disclosure). The
prompt carries only what the spec lists: the section list (labels, in book
order), each section's roles (ingest `role_hint` plus RW4e's visible
proposals through `source_roles.best_roles`), the linked LOs' titles and the
learner's status on each (demonstrated / assumed / learning / new), the depth
and the goal's title. No passage text, no learner free text. Withheld
sections (`exam_material(...).withheld`, held-out included) are never sent;
a reading that is exam material whole has no path. Spend: metered routes are
held to `reading_paths.max_daily_cost_usd` (0.50, a new key: the spec names
none but the orchestrator requires a cap) at
`source_retrieval.llm_price_per_million`, checked before the call (refused
when unpriced or used up); Codex is `estimated_only`.
`LEARNLOOP_READING_PATH_MODELS=off` in the suite.

**Honest labels in code after the model (G47, note 2).** `already_shown`
stands only when the section teaches at least one LO and every LO it
teaches is demonstrated (`lo_certification(...).demonstrated`); `assumed`
only when every LO is demonstrated or has an open `assumption_decisions` row
(`placement.state.load_placement_state(...).open_by_lo`) and at least one is
assumed; otherwise the label becomes `core` with a code-written reason. The
same rule runs again at display against the statuses of that moment.

**Cache and re-judging.** `state_key` = hash(prompt version, depth, the
sendable section list's hash, every linked LO's status, the goal id). Guide
open with a fresh path: no call. A changed depth, section list or LO status
gives a new key and one new call; an older path is shown meanwhile (labels
re-checked for honesty) and marked as being updated.

**Ledger.** One `llm` verdict per section (task `reading_path_role`, left
`reading_path` = `<extraction>:<depth>`, right `reader_section` = section id,
input hash = state key; the rationale keeps the model's label, the shown
label and whether code changed it). An override is a `learner_card` verdict
on the same question.

**Exercise worth trying.** For each core section, the first exercise region
(`content.sources.exercise_statements.exercise_regions`) whose lead block is
in the section and whose statement the one statement reader
(`read_exercise_statement`, fail closed on exam and held-out material) still
reads. Stored as `exercise_span_id`; re-read at display (a region held out
since is not named). *Try it* opens it in the workbench through RW4b's
fallback path (`workbench.open` with the Reader's `import_request`,
`work_through`, the book shown). **Deviation:** the sources spec's searched
candidate (`instructional.exercises.exercise_candidates`) is not used: it is
a search with paid steps (query embedding, rewrite) and has no
section-to-exercise mapping; `learnloop.reader` cannot import
`learnloop.instructional` either (the import contract). Recorded as an open
question.

**Suggested next activity, no model.** The first core or prerequisite
section in book order (a *read it anyway* counts as core; a *skip it*
leaves it out) not completed (`reader_section_progress`), with, at *learn to
use it* and *fluency*, its exercise: "Next: read §5.4 Mixtures, then try
Exercise 5.14 · about 6 min of reading" (reading minutes from the section's
words at 200 a minute).

**Sidecar** (`learnloop_sidecar/handlers/reading_paths.py`, desktop only):
`reader.reading_path` (the view; starts the judge in the background when the
depth is known and the cached path is not fresh; the Reader polls),
`reader.reading_path_set_depth`, `reader.reading_path_override`. Every one
refuses `reading_paths_disabled` while off. `reader.prompt_contract` gains
`reading_paths` only while on. RW1b's palette gains Orient's *what matters
here?* (effect `reading_path`, opens the Guide's path; needs
`reading_paths`), absent while off.

**Frontend.** New `screens/reader/ReadingPathCard.tsx` and `readingPath.ts`;
`GuideRail` gains an optional `path` node shown in place of the goal card
(absent: today's Guide); `ReaderScreen` passes it while the contract has
`readingPaths`, and handles the `reading_path` effect.

**Config.** `[reading_paths] enabled = true`, `max_daily_cost_usd = 0.5`;
`ai.routing.reading_path_judge` (empty = the active provider). Modelled
defaults, classified in the parameter registry, every defaults snapshot
recomputed with a "no scoring, scheduling, projection or serving change"
note. **Successor:** none.

**Tests planned** (fakes only): `tests/test_reading_paths.py` (honest labels
for each label, the display-only plan/Today golden from `a76c8358a`, the
override and skip table diffs, the cache key and each re-judge trigger, no
call on a fresh path or while off, the spend cap before the call, the
exercise pick and exam exercises never named, the suggested next line
without a model, depth memory and the DL2 mapping with DL2's rows
unchanged, withheld sections never sent and stored rows withheld later not
shown, the ledger rows); `tests/test_reading_paths_switch_off.py` (guide
plan, prompt contract and palette pinned to `a76c8358a` with the switch
off); table roles, migration and head fixture tests; the mobile allowlist pin;
the parameter registry; vitest `ReadingPathCard.test.tsx` and a GuideRail pin.
Plus the RW4e role-reader, RW4d source-object and RW4b exercise pins in
every gate.

## 1. What was built

### 1.1 Data (migration 217)

`migrations/217_reader_reading_paths.sql`: `reader_path_sections` (the spec's
thirteen columns; CHECKs on `depth`, `label` and `learner_override`;
`ledger_id` references `judgment_ledger(id)`; a partial unique index makes a
judge row unique per (reading, depth, state key, section); append-only by
trigger) and `reader_path_depths` (`id`, `source_id`, `depth`, `created_at`;
append-only by trigger). Both WORKFLOW in `db/table_roles.py`; no DERIVED
table, so no replayer. SQL lives in `src/learnloop/db/stores/reading_paths.py`
(a registered SQL owner in `tests/test_architecture.py`).
`fixtures/migration_head_215` was renamed `migration_head_217` and its
`state.sqlite` rebuilt: a backup-API copy of the base's 215 head with only 217
applied (`UPGRADE_SCRATCH_COPY`, `wal_checkpoint(TRUNCATE)` (0, 0, 0),
`journal_mode=DELETE`, header bytes 1/1, `integrity_check` ok,
`foreign_key_check` empty, no companions), placed with the backup API; README
updated; every hard-coded path moved (33 test files, the two reference
scripts with `SCHEMA_HEAD = 217`, `docs/decider-tier1-migration.md`); the five
earlier migration tests that diff "nothing else changed" on the way to head
subtract `RW7A_ADDED_OBJECTS` and expect 217 as head.

### 1.2 The path (`src/learnloop/source_retrieval/reading_paths.py`, new)

- **Inputs** (`path_inputs`): the reading's sections (`reader_guidance.extraction_sections`,
  the Guide's own), each with its linked LOs (`reader_progression.learning_objects_by_section`,
  RW6a's reader), its ingest roles (`role_hint`, ordinary prose left out) and
  RW4e's visible proposals (`source_roles.best_roles`: head versions, RW4d's
  `hidden_source_objects` applied, empty while `roles.positive_filter_enabled`
  is off), its word count; every linked LO's status (`lo_statuses`:
  `demonstrated` = `lo_certification(...).demonstrated`, `assumed` = an open
  row in `load_placement_state(...).open_by_lo`, `learning` = any mastery
  evidence, else `new`); the goal (`goal_for_source`: the Guide's
  `goal_for_item` over each linked LO, highest priority; RW7a creates none).
  The exam predicate (`exam_material(...)`) is asked once: a reading covered
  whole raises `withheld`; sections with any withheld span are dropped (never
  sent, never shown); an unreadable predicate shows no path (fail closed).
- **State key** (`PathInputs.state_key`): sha256 of the prompt version, the
  depth, the sent section list's hash (ids, titles, linked LOs), every linked
  LO's status and the goal id.
- **The judge** (`judge`, route `reading_path_judge`): no call when judge rows
  for the current key exist; otherwise `JudgeRoute.problem()` before anything
  is sent (`LEARNLOOP_READING_PATH_MODELS=off`, unrouted, a metered route
  without `source_retrieval.llm_price_per_million`, today's
  `reading_paths.max_daily_cost_usd` used up), then one `PaidCalls.call` inside
  the `SharedDailyEnvelope` (owner kind `reading_path_judge`, receipts in
  `model_call_receipts`). The prompt (`build_prompt`, `reading_path_judge.v1`)
  carries only `depth`, `depth_means`, the goal's title and, per section,
  `section_id`, `title`, `book_roles`, `proposed_roles` and `topics`
  (`title`, `status`): no passage text, no learner text.
- **Honest labels** (`honest_label`, `validate`, `shown_reason`): after the
  model and again at display (`path_view`). A model's `already_shown` or
  `assumed` without the evidence becomes `core` with code's line ("Not
  everything here is shown on your own yet, so it stays core."); a kept
  `already_shown` / `assumed` gets code's evidence line ("You've shown this on
  your own: …", "Assumed known (not tested): …"); unknown labels and sections
  the model left out are `core`; unknown section ids are dropped.
- **Ledger and rows**: in one transaction, one `llm` verdict per section
  (task `reading_path_role`, left `reading_path` / `<extraction>:<depth>`,
  right `reader_section` / section id, input hash = the prompt's hash,
  rationale = model label, shown label, whether code changed it, reason,
  state key; superseding the question's previous verdict) and one row citing
  it. A concurrent writer of the same state is detected inside the
  `BEGIN IMMEDIATE` (and by the unique index): nothing is written twice.
- **Overrides** (`override`): one `learner_card` verdict on the same question
  and one row with `learner_override` (`read_anyway` | `skip` | `none` to
  clear), per depth, the newest standing across re-judgments. Nothing else is
  written; `skip` marks nothing as known.
- **One exercise worth trying** (`pick_exercises`, `exercise_view`): per
  section, the first exercise region (`exercise_statements.exercise_regions`)
  whose lead block is in the section and that the one statement reader
  (`read_exercise_statement`, which asks `exam_withheld` about the whole
  region and fails closed) still reads; kept for every section, named only
  while the section is core (a "read it anyway" counts), read again at display
  (a region withheld since is never named). *Try it* carries the Reader's own
  `import_request` (`selection_nodes` of the statement).
- **The next line** (`next_activity`): no model; the first core or
  prerequisite section in book order that is not completed
  (`reader_section_progress`), a "read it anyway" counting as core and a
  "skip it" leaving it out, with its exercise at "learn to use it" and
  "fluency" and "about N min of reading" (200 words a minute).
- **The depth** (`depth_choice`, `set_depth`): the newer (as instants) of the
  Guide's newest `reader_path_depths` row and DL2's own intent-control
  commitment on the source scope (the source id or any of its readings;
  `intent.control.own_commitments` over `load_snapshots`, read only), mapped
  by `INTENT_DEPTH`; none: the Guide asks.
- **The view** (`path_view`): `ask_depth`, `ready`, `judging` (an older path
  shown meanwhile), `stale`, `pending`, `failed` (with the reason and the
  learner's line), `withheld`, `no_sections`; the goal line ("toward your
  goal: …" or "No active goal covers this book: the path follows the depth
  you chose."); sections with chip, why, override, effective label, exercise.

### 1.3 The sidecar (`src/learnloop_sidecar/handlers/reading_paths.py`, new; desktop only)

`reader.reading_path` (`judge`, `retry`), `reader.reading_path_set_depth`,
`reader.reading_path_override`; each refuses `reading_paths_disabled` while
off (and `reader_disabled`, a source opted out of the Reader, as the Guide
does). The judgment runs in a background thread on its own repository under
`record_model_calls` (`ctx.reading_path_inline` runs it inline in tests); an
in-memory registry per (reading, depth, state key) keeps one judgment in
flight and remembers a failure until *try again* (`retry`), so a failure
never loops. `reader.prompt_contract` gains `reading_paths` (`enabled`, the
three depths) only while on.

### 1.4 Orient's "what matters here?" (`reader/reader_intent.py`)

`IntentAction("what_matters_here", "orient", ..., {"kind": "reading_path"},
needs=("reading_paths",), model=False)`, first in Orient; `Availability`
gains `reading_paths` from `reading_paths.enabled`. Off, the palette and the
Decider's options are `a76c8358a`'s. It shows nothing to a model.

### 1.5 Config, routes, registry, report

`ReadingPathsConfig` (`enabled = true`, `max_daily_cost_usd = 0.5`) and
`ai.routing.reading_path_judge` (AITask, `ROUTE_FOR_OPERATION`, a disclosure
in `ai/disclosures.py` naming what is sent); both keys classified
structural/operational in `params/parameter_registry.py`; all 20
`DEFAULTS_SNAPSHOT_BY_ALGORITHM` entries recomputed with the "no scoring,
scheduling, projection or serving change" note (no successor).
`learnloop reader report` gains `reading_paths` (judged labels by kind,
overrides by the label they overrode, depth choices). `tests/conftest.py`
sets `LEARNLOOP_READING_PATH_MODELS=off`.

### 1.6 The Reader (frontend)

`screens/reader/ReadingPathCard.tsx` and `readingPath.ts` (new): the depth
question ("How deep do you want to go?", the three depths with what each
means), the heading "your path · learn to use it" with *change*, the plan
setting it came from ("from your Learn setting for this book"), the goal
line, the next line, per section a chip (core · prerequisite · enrichment ·
already shown ● · assumed) with *why ▸* (the model's line marked "model's
reading" with the ◇ dotted rule; code's evidence lines in the source rule),
*read it anyway* / *skip it* / *undo* ("you're skipping it · nothing is
marked as known"), "one exercise worth trying: Exercise 5.14 *Try it ▸*"
(or *open in the book ▸* without the workbench), the pending, updating,
failed (*try again ↵*, none for a used budget, models off, unrouted or
unpriced) and withheld states; the card reads the path again every 1.5 s
while judging. `GuideRail` gains an optional `path` node rendered in place of
the goal card (absent: today's Guide byte for byte); `ReaderScreen` passes
the card while the contract carries `readingPaths`, handles the
`reading_path` effect (Guide tab, the card scrolled into view) and *Try it*
through `wbCtl.openSelection` (RW2a's selected-problem import, book shown).
The three RPCs are wired in `client.ts`, `commands.rs` and `main.rs`; DTOs in
`dto.ts`; the intent fixture regenerated from the sidecar's palette.

## 2. Deviations (each with its reason)

1. **The module lives in `learnloop.source_retrieval`, not `learnloop.reader`.**
   In `reader` it closed three sibling cycles (reader -> intent, practice_index,
   source_retrieval) that the frozen acyclic-siblings contract refuses;
   `source_retrieval` already holds the Reader's other judged features
   (`library_ask`, `passage_cues`, `kept_comparisons`).
2. **A second table, `reader_path_depths`**, in the same migration: the depth
   is a source's (orchestrator note 7 allows "its own per-source row").
3. **No `path_depth_set` / `path_override` interaction events** (spec §11's
   event list): orchestrator note 1 says an override writes only
   `reader_path_sections` and the `learner_card` verdict; the depth is in its
   own row. The report counts both from the tables.
4. **`reading_paths.max_daily_cost_usd`** (0.50) is new: the spec's
   `[reading_paths]` lists only `enabled` (and RW7b's `plan_uses_path`, not
   added), but note 4 requires a spend cap before the call. Priced at
   `source_retrieval.llm_price_per_million`, as RW3b's judge.
5. **The state key also hashes the goal id and the prompt version** (the
   spec names depth, section list and statuses): the goal changes the
   reasons the path shows; a prompt change must re-judge.
6. **The exercise is the section's own exercise block only.** The sources
   spec's candidate (`instructional.exercises.exercise_candidates`) is a
   search with paid steps (query embedding, rewrite) and no
   section-to-exercise mapping, and the instructional service may be reached
   only by injection (`instructional-service-is-a-composition-layer`).
   Textbooks with exercises only in end-of-chapter units get no exercise per
   section (open question 3).
7. **Overrides are per depth** (the table's key carries `depth`): skipping a
   section at "learn to use it" does not skip it at "fluency".
8. **Earlier stages' switch-off pins keep RW7a off** rather than being
   re-recorded: `test_reader_intent` (both off contracts),
   `test_compare_keep_switch_off`, `test_reader_tutor_switch_off`,
   `libraryAskSwitchOff.test.tsx` (strips the `reading_path` action with the
   library ones); `test_rw4_kill_switches` now expects Orient to keep only
   "what matters here?"; `test_reader_intentions` gains the `reading_path`
   effect kind; `test_judge_routes` the new route.

## 3. Tests (fakes only; no live call, no paid call, no smoke run)

New:
- `tests/test_reading_paths.py` (40): G47's honest labels (already shown,
  assumed with an open row and closed by a return, unknown and missing
  labels, the pure rule, the display re-check of a stored already shown);
  display only (with depths, judgments, overrides and a skip stored,
  `get_daily_plan`, `get_today_queue` and `reader.guide_plan` equal the
  golden recorded on `a76c8358a` before any RW7a code:
  `tests/fixtures/reading_paths_base_a76c8358a.json`); an override's table
  diff (only `judgment_ledger` +1 and `reader_path_sections` +1) and skip
  marks nothing known; overrides kept across a re-judgment and cleared; the
  depth asked first with no call; one call per depth and no call on a fresh
  path or a new sidecar; each re-judge trigger (depth, an LO status, the
  section list) and the cached path on returning to a judged state; the
  state key; a failed judgment and *try again*; the price and the cap checked
  before the call (no receipt); models off without an injected client; the
  ledger rows and supersession; the prompt's exact keys and no passage text;
  the goal named or the depth-only line; the exercise block, the import
  request, a read-anyway naming its exercise, an exam or held-out exercise
  never named (stored or not); a held-out section never sent and a stored
  one withheld later not shown; an exam reading and an unreadable predicate
  (no path, no call); the next line without a model (progress, skip, depth);
  the depth remembered per source; DL2's choices mapped (master, learn, keep,
  light touch, pause, reference) with `commitments` and
  `commitment_versions` unchanged by the Guide; instants compared; refused
  depths and choices; roles from `role_hint` and visible RW4e proposals
  (none with the positive filter off); the reader report; the switch-off pins
  (plan, Today, guide, contract equal the golden; every RPC refuses; no
  call; no table change); the contract and palette gain only RW7a's keys;
  every `reading_paths.*` key and the route classified.
- `tests/test_reader_rw7a_migration.py` (4, one durability): 215 -> 217 adds
  exactly the two tables and alters nothing; CHECKs, FK, unique judge rows,
  append-only; WORKFLOW; the head fixture at 217 in rollback mode, empty.
- `tests/reading_path_fixtures.py` (the vault, the fake judge, `normalized`).
- `tests/test_mobile_allowlist.py`: `READER_RW7A_RPCS` pinned desktop-only.
- vitest: `ReadingPathCard.test.tsx` (9), `readingPathsReader.test.tsx` (2),
  `readingPathsSwitchOff.test.tsx` (1; its snapshot written against
  `a76c8358a`'s frontend files checked out over the stage's, then restored).

### 3.1 Gate (this step; the full suite runs once, in the landing gate)

| Check | Result |
|---|---|
| `uv sync --extra dev --extra mobile`, `uv pip install pypdfium2` | ok |
| `uv run lint-imports --no-cache` | 28 kept, 0 broken |
| targeted `pytest -n auto` over 184 files (listed below; TMPDIR = `fixtures-local/tmp`, template `.pyc` cleared) | **3,864 passed, 1 skipped, 2 xfailed** |
| `pytest -m durability` over the migration files and `test_reading_paths.py` | 6 passed |
| `--durable-sqlite` over `test_reading_paths.py`, `test_reader_rw7a_migration.py` | 44 passed |
| `npm install`, `npm run typecheck` | ok |
| vitest, 28 Reader files (the three new, every file using the intent fixture or a Reader switch-off snapshot) | **226 passed** |
| `npm run frontend:build` | ok |
| `cargo check` (src-tauri) | ok |
| `db_generate_reference.py` / `db_validate_reference.py` | 945 leaves in 68 sections, 337 table notes, head 217, **0 errors** |
| `validate_vault.py` | passed (1,139 notes) |

`desktop_validate.py` stops on a file that predates this stage
(`components/pdfSelection/testing/syntheticBook.ts`, unclassified); not run
by earlier stages either; recorded, not fixed here.

Python test files run (184):

```
test_ad1_codex_review_fixes.py test_ad1_migration.py test_ai_config.py test_ai_runtime.py 
test_ai_tool_isolation.py test_approach_map_replay.py test_approach_maps_schema.py test_architecture.py 
test_blueprint_projection.py test_characterization_mastery_reliability.py test_chatgpt_plan_provider.py 
test_chatgpt_plan_workspace.py test_cli_generate_practice.py test_cli_help_snapshot.py 
test_cold_start_revision.py test_compare_keep_switch_off.py test_compare_sources_keep.py 
test_config_refactor.py test_constraint_engine.py test_coordinated_migrations.py test_daily_plan_reading.py 
test_daily_plan_replay.py test_decider_landing.py test_desktop_rpc_contract.py test_diagnosis_context.py 
test_diagnosis_history_modes.py test_diagnosis_input_provenance_landing.py test_diagnosis_input_provenance.py 
test_diagnosis_replay.py test_diagnostic_pack.py test_exam_protection.py test_exam_protection_review.py 
test_exercise_authoring.py test_facet_identity_actions.py test_facet_identity_composition.py 
test_facet_reword_confirm_review.py test_field_config.py test_field_priors.py 
test_forecast_receipts_landing.py test_forecast_receipts.py test_gate_fit.py test_glm_ocr.py 
test_grading_cli.py test_help_assists_schema.py test_hint_feedback_widening.py test_hint_telemetry.py 
test_ingest_m3.py test_instructional_layering.py test_intent_codex_rereview.py 
test_intent_orchestrator_rulings.py test_item_parameters.py test_judge_routes.py test_kinship_feature.py 
test_label_roles_cli.py test_learner_text_source_widening.py test_library_ask.py test_library_ask_review.py 
test_library_asks_migration.py test_library_exercises.py test_method_explicit_landing.py 
test_method_explicit_upgrade.py test_migrations.py test_mobile_allowlist.py test_mvp010_upgrade.py 
test_mvp011_upgrade.py test_mvp013_upgrade.py test_mvp014_upgrade.py test_mvp015_upgrade.py 
test_mvp016_upgrade.py test_mvp017_route_check_replay.py test_mvp017_upgrade.py test_mvp018_upgrade.py 
test_mvp020_upgrade.py test_mvp021_upgrade.py test_mvp022_upgrade.py test_mvp023_upgrade.py 
test_mvp024_upgrade.py test_openai_embedding_client.py test_open_world_gate.py test_p0_cutover_mvp08.py 
test_passage_links.py test_pfc_unverified_unassessed.py test_plan_determinism.py 
test_practice_proposal_caller_columns.py test_probability_cli.py test_project_atomicity.py 
test_project_blindness.py test_project_capture.py test_project_cli.py test_project_experiment_store.py 
test_project_hooks.py test_project_probes.py test_project_redaction.py test_project_report.py 
test_provider_resolution_parity.py test_reader_active_reading.py test_reader_cue_holdout.py 
test_reader_cues_cli_report.py test_reader_cues.py test_reader_cue_value.py test_reader_dialogue.py 
test_reader_find_sources_callers.py test_reader_formative_texts.py test_reader_guidance.py 
test_reader_inquiry_kill_switch.py test_reader_intentions.py test_reader_intent.py 
test_reader_passage_check.py test_reader_progression.py test_reader_quick_check.py test_reader_recap.py 
test_reader_reconnect.py test_reader_reconstruct.py test_reader_report.py test_reader_restoration.py 
test_reader_rw1b_final_verify.py test_reader_rw1b_fix_round4.py test_reader_rw1b_rereview.py 
test_reader_rw1b_review.py test_reader_rw1c_review.py test_reader_rw2b_review.py test_reader_rw3a_landing.py 
test_reader_rw3b_fix_round4.py test_reader_rw3b_fix_round5.py test_reader_rw3b_migration.py 
test_reader_rw3b_protection.py test_reader_rw3b_review_fixes.py test_reader_rw3b_switch_off.py 
test_reader_rw7a_migration.py test_reader_try_first.py test_reader_tutor_offers.py 
test_reader_tutor_switch_off.py test_reader_workbench_rw2a.py test_reading_hardening_landing.py 
test_reading_paths.py test_reading_step_switch.py test_rebuild_orchestrator.py test_recall_calibration.py 
test_recurrence_commands.py test_recurrence_live.py test_registry_audit.py test_regrade_contract_successor.py 
test_regrade_contract_upgrade.py test_required_method_items.py test_required_method_round3.py 
test_reread_safety_landing.py test_reread_safety.py test_roles_concurrency.py test_roles_judges.py 
test_roles_switch_off_legacy_parity.py test_roles_switch_off.py test_router_offer_log.py 
test_router_probe_ties.py test_route_rules_in_grader.py test_rw1a_composition.py 
test_rw4d_rw3b_composition.py test_rw4_kill_switches.py test_scheduler.py 
test_self_attributed_misconceptions.py test_sensitivity_certificates.py test_serve_eligibility_review.py 
test_shadow_rebuild.py test_sidecar_reader_p3_slice2.py test_sidecar_reader.py 
test_sidecar_serializer_snapshot.py test_sim_teach_back.py test_simulation.py test_source_block_fts.py 
test_source_objects.py test_source_roles.py test_sqlite_file_copies.py test_stuck_prompt_replay.py 
test_surprise.py test_table_roles.py test_tier1_decider.py test_tracked_fixture_databases.py 
test_ux_phase1_landing.py test_ux_phase1_round2_review.py test_ux_phase1_usability_round1.py 
test_ux_phase4_feedback.py test_ux_phase4_landing.py test_voi_merge_composition.py test_voi_stopping.py 
test_voi_v2.py ```

Pins of other readers included in the gate: RW4b's exercise readers
(`test_library_exercises.py`), RW4d's source objects (`test_source_objects.py`,
`test_rw4d_rw3b_composition.py`, `test_compare_sources_keep.py`), RW4e's role
readers (`test_source_roles.py`, `test_roles_judges.py`,
`test_roles_switch_off.py`, `test_roles_switch_off_legacy_parity.py`,
`test_label_roles_cli.py`, `test_roles_concurrency.py`), RW6a's section LO
reader (`test_reader_restoration.py`, `test_reader_recap.py`).

## 4. Files

New: `migrations/217_reader_reading_paths.sql`,
`src/learnloop/source_retrieval/reading_paths.py`,
`src/learnloop/db/stores/reading_paths.py`,
`src/learnloop_sidecar/handlers/reading_paths.py`,
`apps/learnloop-tauri/src/screens/reader/ReadingPathCard.tsx`,
`apps/learnloop-tauri/src/screens/reader/readingPath.ts`, the tests above,
`tests/fixtures/reading_paths_base_a76c8358a.json`,
`fixtures/migration_head_217/` (renamed from 215, database rebuilt).
Changed: `src/learnloop/ai/{routing,disclosures}.py`,
`src/learnloop/config/{schema,template}.py`, `src/learnloop/db/table_roles.py`,
`src/learnloop/params/parameter_registry.py`,
`src/learnloop/reader/{reader_intent,reader_report}.py`,
`src/learnloop_sidecar/handlers/{__init__,reader}.py`,
`apps/learnloop-tauri/src/{api/client.ts,api/dto.ts,fixtures/readerIntentContract.ts,screens/ReaderScreen.tsx,screens/reader/GuideRail.tsx}`,
`apps/learnloop-tauri/src-tauri/src/{commands,main}.rs`, `tests/conftest.py`,
the earlier tests named in §2 item 8 and §1.1, the references
(`docs/learnloop-architecture-vault/...`, `_scripts/db_generate_reference.py`
gains the `reading_paths` description, `Maps/LearnLoop Pipeline Map.md` an
RW7a bullet).

## 5. Owner-run commands (none paid; on a backup copy only)

No paid or live command was run in this stage. To look at it on a copy:

```bash
# a backup-API copy of a working vault into the gitignored fixtures-local/
uv run python -c "from learnloop.db.copies import copy_tree_with_databases; copy_tree_with_databases('fixtures/probability', 'fixtures-local/rw7a-probability')"
uv run learnloop doctor --fix-state --vault fixtures-local/rw7a-probability   # applies 217 through the coordinator
LEARNLOOP_VAULT=$PWD/fixtures-local/rw7a-probability npm run dev           # apps/learnloop-tauri: open a book, Guide tab
uv run learnloop reader report --vault fixtures-local/rw7a-probability --json   # reading_paths counts
```

Choosing a depth makes one `reading_path_judge` call on the active provider
(Codex: estimated only); a metered route needs
`source_retrieval.llm_price_per_million` and is capped by
`reading_paths.max_daily_cost_usd`. Off: `[reading_paths] enabled = false`.

## 6. Open questions (with the defaults in force)

1. **"Already shown" on LOs without blueprints.** `lo_certification` is
   `demonstrated = False` for an LO without authored blueprints, so such
   sections are never "already shown" (honest, conservative). Default: keep
   (the binding note names `lo_certification`); the Today headline's facet
   rule could widen it later.
2. **"Assumed" with demonstrated LOs mixed in.** Default: assumed when every
   LO is demonstrated or open-assumed and at least one is assumed.
3. **Exercises outside the section** (end-of-chapter units). Default: none
   named for that section; a later phase may map the sources spec's
   candidates to sections by LO (a search, so its spend and an injection
   point need deciding).
4. **The judge's cap.** Default `reading_paths.max_daily_cost_usd = 0.50`.
5. **Overrides per depth.** Default: per depth (the table's key).
6. **The judge runs automatically on Guide open** when the depth is known
   (including a depth preselected from DL2) and the cached path is stale.
   Default: yes (frictionless); one call per state.

## 7. Friction notes

For **RW7b** (the plan follows the path):
- Read the effective label from `path_view(...)["sections"]` (or the same
  helpers: newest judge rows for the current state key, honest label
  re-applied, the newest override per depth): a "read it anyway" is core and
  a "skip it" is out. The depth for planning is `depth_choice` (the Guide's
  row or DL2's mapped intent, whichever is newer).
- `reader_path_sections` rows are per extraction; DL1's reading block names
  an extraction and a section id from `extraction_sections`, the same ids.
- A path may be stale (an older state key); RW7b should decide whether to
  plan from a stale path or fall back to book order (default suggestion:
  fall back, with the receipt naming it).
- `state_key` hashes LO statuses, so evidence changes re-judge the path on
  the next Guide open; a plan build must not trigger a call (read only).

For **RW6b** (digest, follow-ups):
- The path's ledger task `reading_path_role` and the `learner_card`
  overrides are there for "what you skipped" lines; skip marks nothing known,
  so a follow-up must not treat a skipped section as read.
- `reader_section_progress` is what the next line reads for "done".

Process notes (this stage): three short commands ran `python3`
outside `env -i` (a one-line edit of `db/table_roles.py`, a read of the
golden JSON and a bare `print()`), and one `git stash list` (read-only) slipped into a compound
command; none touched a vault, a credential
or the network, and every other Python run outside pytest used `env -i` with empty HOME,
CODEX_HOME and LEARNLOOP_CONFIG_DIR.

## 8. Landing onto main

Landed in the `learnanything-merge2` worktree on branch `merge/rw7a-onto-main`, cut from main at `a76c8358a` (the
RW4e landing record: migration head 215 with `migration_head_215`, 20 defaults snapshots, 942 configuration leaves).
The stage tip is `669329dd7` (base `a76c8358a`, so main had not moved), unchanged. The orchestrator's verify (Codex
job `20261021-090616-cajqKL` on `669329dd7`) is **clean**. Main was neither fast-forwarded nor pushed here.

### Commits and conflicts

- `ab0649c7e`: a `--no-ff` merge of `reader/rw7a` onto `a76c8358a`. **No conflict**: the stage branched from main's
  tip, so `config/template.py` (all 20 snapshots), the parameter registry, `test_mobile_allowlist`, the CLI help, the
  RPC pins, `ReaderScreen.tsx`, `dto.ts` / `client.ts`, `commands.rs` / `main.rs`, the head-fixture rename and its 33
  test paths came in as the stage left them. The generated references were the stage's, made on the stage's own
  commits, and were regenerated in the next commit.
- `603c1b45a`: the regeneration (below). This is the gate head.
- This record (docs only).

**Migration numbering.** 217 lands with gaps. Main's head is 215; AD2+AD3 holds 214 and RW5a holds 216, both on
their own branches. `db/migrate.py` applies every migration not yet applied, so a vault at 215 takes 217 now and 214
and 216 later. Every test, script and reference generator accepts the gaps:
- the full suite and the durability lane pass with `migration_head_217`, which has no 214 or 216;
- `db_generate_reference.py` and `db_validate_reference.py` run with `SCHEMA_HEAD = 217` and report 0 errors;
- no test or script under `src`, `tests`, `docs` (outside the reviews and generated references), `scripts` or the
  app still names `migration_head_215`;
- parity (a) opens real vault copies from 165 straight to 217: 50 migrations, with no 214 and no 216.

### Regeneration

- **References.** `db_generate_reference.py` ran, then `db_validate_reference.py`:
  - **0 errors**, `schema_head` **217**, **337** table notes;
  - **945** configuration leaves in **68** sections;
  - 407 files changed, and the only change is the commit labels (`source_commit` and its timestamp);
  - the two prose counts (`Configuration.md`, `Database.md`) already said 945 / 68 / 337.
- **Defaults snapshots.** The template's `.pyc` was cleared and the check run with `-B`. All **20**
  `DEFAULTS_SNAPSHOT_BY_ALGORITHM` entries equal `defaults_fingerprint_for_version` on the merged tree: **0
  mismatches**, nothing to rewrite.
- **CLI help snapshot and RPC pins.** A pin run of 15 files passed: **540 passed**, and no snapshot needed rewriting.
  The files: `test_cli_help_snapshot`, `test_sidecar_serializer_snapshot`, `test_desktop_rpc_contract`,
  `test_mobile_allowlist`, `test_sidecar_contract`, `test_config_refactor`, `test_registry_audit`, `test_architecture`,
  `test_table_roles`, `test_tracked_fixture_databases`, `test_sqlite_file_copies`, `test_coordinated_migrations`,
  `test_migrations`, `test_rebuild_orchestrator`, `test_reading_paths`. RW7a's three RPCs stay desktop-only.
- **Head fixture 217.** Main's `fixtures/migration_head_215/state.sqlite` blob was placed with the backup API and
  only 217 applied under `UPGRADE_SCRATCH_COPY` (`wal_checkpoint(TRUNCATE)` (0, 0, 0), then `journal_mode=DELETE`).
  The result is **identical** to the tracked `fixtures/migration_head_217/state.sqlite`:
  - in schema: 1,438 objects;
  - in every row of all 342 tables, apart from `schema_migrations.applied_at`.

  Both have header bytes 1/1, `integrity_check` ok and an empty `foreign_key_check`. There is no `-wal` or `-shm`
  beside the fixture. The fixture was not rebuilt.
- **`validate_vault.py`**: passes (1,139 notes, 1,137/1,137 reachable).
- **Known failures from before this stage, not fixed:**
  - `desktop_validate.py` still stops on `components/pdfSelection/testing/syntheticBook.ts`;
  - `module_validate.py` reports **968** issues (962 at the RW4e landing). RW7a adds modules without module notes:
    `source_retrieval/reading_paths.py`, `db/stores/reading_paths.py` and the sidecar handler.

Every script outside pytest ran under `env -i` (`fixtures-local/landing-rw7a/scripts/iso.sh`). That covers the
generators, the validators, the snapshot check and the head-fixture check. The environment was only `PATH`, `TMPDIR`
and `LANG`, an empty `HOME`, `CODEX_HOME` and `LEARNLOOP_CONFIG_DIR`, and the model switches
`LEARNLOOP_CUE_JUDGE_MODELS=off`, `LEARNLOOP_ROLE_LABELLER_MODELS=off` and `LEARNLOOP_READING_PATH_MODELS=off`.

### Gate

Setup:
- Python 3.12.14.
- `TMPDIR` was merge2's `fixtures-local/tmp`.
- Every command after the install ran as `uv run --no-sync`.
- Both suite lanes ran under `flock /tmp/learnloop-fullsuite.lock` on `603c1b45a`.
- The AD2+AD3 (`learnanything-ad1`), RW5a (`learnanything-dl2`) and RW7a stage (`learnanything-rw4b`) worktrees and
  their processes were not touched.
- Every test uses fakes.

**This is the first full run over RW7a's code**: the stage, its Codex review and re-review rounds and the
orchestrator's fix round ran targeted tests only.

| Check | Result |
|---|---|
| `uv sync --extra dev --extra mobile` + `uv pip install pypdfium2` | ok (pypdfium2 5.14.0) |
| `lint-imports --no-cache` | **28 kept**, 0 broken |
| full suite `pytest -n auto` | **15,114 passed, 1 skipped, 2 xfailed, 0 failed** (25 min 16 s; `fixtures-local/rw7a-landing/fullsuite.log`). The RW4e landing ran 15,054. The skip is RW4e's base-only golden recorder |
| `pytest -m durability` | **118 passed**, 14,999 deselected (4 min 8 s; `fixtures-local/rw7a-landing/durability.log`). The RW4e landing had 117 |
| `npm install`, `npm run typecheck` | ok; clean |
| `npm test` (the whole vitest run) | **165 files, 1,292 tests passed** (RW4e's landing: 161 / 1,274). The first run, made while the full suite was loading the machine, also reported **1 unhandled error** (finding 1). Rerun: `libraryExercisesReader.test.tsx` alone 3 times, then the whole vitest run once more after the suite: all clean, 165 / 1,292 and no error |
| `npm run frontend:build` | built (the usual chunk-size warning) |
| `cargo check --manifest-path src-tauri/Cargo.toml` | ok (RW7a's three passthroughs in `commands.rs` / `main.rs`) |
| thread, lock and timing tests | all passed on the first run, including `test_reading_paths.py`'s concurrent-sidecar claim test, so none was rerun |
| tracked fixtures, worktree | `git status` clean after both lanes and the frontend runs; no `-wal` / `-shm` beside a fixture |

No real failure, so no landing fix.

### Parity (backup-API copies; no model call completed)

**Setup.** The scripts are in `fixtures-local/landing-rw7a/scripts/`, adapted from the RW4e landing's; the new ones
are `ab_rw7a.sh`, `c_rw7a.sh`, `path_run.py` and `pcmp.py`.
- **Copies.**
  - `fixtures/linear_algebra` and `fixtures/probability` were copied once, with `copy_tree_with_databases`, from the
    main checkout into `fixtures-local/landing-rw7a/orig/`.
  - Every other copy came from `orig/`, or from its upgraded copies, through the same helper.
  - `arxiv_v2` was not opened.
  - Both vaults start at schema 165, label `mvp-0.8`, with 0 `model_call_receipts`.
- **Code.** Main's code is `git archive a76c8358a`; the merge's is `git archive 603c1b45a`.
- **Environment.** Every run went through `env -i` with only `PATH`, `HOME`, `CODEX_HOME`, `LEARNLOOP_CONFIG_DIR`,
  `TMPDIR` and `LANG`. `HOME`, `CODEX_HOME` and `LEARNLOOP_CONFIG_DIR` were empty, and were checked empty afterwards.
- **Routes.** `neutralize3.py` ran under each code:
  - every route field went to `127.0.0.1:9`: 57 on main and 58 on the merge, where `reading_path_judge` is the new
    one;
  - the active provider went to that loopback profile, with no fallback;
  - `query_rewrite`, `tutor_query_rewrite`, `tutor_rerank`, `dense`, `[embedding]` and `[learner_text_gaps]` were
    off;
  - `build_on_serve` and outcome placement were off.
- **Route check.** `routes.py` resolved all 60 `AITask`s on main's code and all 61 on the merge's. Nothing resolved
  outside the loopback profiles except `embedding`, which is disabled and keyless. `reading_path_judge` resolved to
  `blackhole` (`openai_chat` at `http://127.0.0.1:9/v1`), including on the mvp-0.27 and mvp-0.29 copies that main's
  code neutralized, where the route is unset and follows the loopback active provider.

**(a) Migration 217**

| Check | linear_algebra | probability |
|---|---|---|
| open (migrate), main's code / the merge's | 165 → 215 (49 applied) / 165 → **217** (50 applied, no 214, no 216) | the same |
| schema, main@215 vs merge@217 | merge-only objects are exactly **11**: `reader_path_sections`, `reader_path_depths`, their 3 named indexes (`idx_reader_path_sections_judged`, the partial unique one; `idx_reader_path_sections_reading`; `idx_reader_path_depths_source`), 2 `sqlite_autoindex` indexes and 4 triggers (`*_no_update`, `*_no_delete`). None is main-only, and no shared object's SQL differs (1,428 → 1,439) | the same 11 (1,427 → 1,438) |
| rows of every existing table (340), all columns | **identical** (16,540 rows). `schema_migrations` gains 217, and the common rows differ only in `applied_at`. Both new tables are empty | **identical** (7,638 rows; the same) |
| `foreign_key_check` / `integrity_check` | 0 / ok, both sides | the same |
| `rebuild --shadow --json`, main@215 vs merge@217 | **0 differences** after normalisation (facet 0, mastery 2, schedule 8 on both); the live database is unchanged on both | **0 differences** (0 / 1 / 1) |
| `doctor --json`, main@215 vs merge@217 | **0 differences** after normalisation (57 issues, 1 error) | **0 differences** (101 issues, 48 errors) |

**(b) Nothing served changes.** The merge ran at its defaults, so RW7a was **on**. The frozen clock was 2026-10-19
09:00 UTC. The checks: certification with recipe gaps and curves; the Today queue with no session, with a session
and greedy; and the daily plan, read, served twice and read again.

| Check | linear_algebra | probability |
|---|---|---|
| at `mvp-0.8` (the copies' label) | cert **byte-identical** (132,860 bytes), Today **byte-identical** (504,488), plan byte-identical (off below mvp-0.14) | cert (17,494), Today (709,910), plan: all **byte-identical** |
| upgraded by main's code to `mvp-0.27` (`--to mvp-0.9`, `--to mvp-0.27`, `rebuild-derived-state` twice; all rc 0), opened by each code | cert **byte-identical** (129,651), Today **byte-identical** (528,665) | cert (17,495), Today (741,269): **byte-identical** |
| then upgraded by main's code to `mvp-0.29` (`--to mvp-0.29`, `rebuild-derived-state` twice; all rc 0), opened by each code | cert and Today **byte-identical** (the same sizes) | the same |
| the daily plan at mvp-0.27 and at mvp-0.29 | identical except `router_decisions.card_hash`, `snapshot_hash` and the card hash inside `detail_json`. A second run of main's code on a fresh copy differs from the first in exactly these three (`plan_repeat.sh`), as at the RW3b, DL2, RW4d and RW4e landings | the same |

**(c) The real sidecar.** It ran over stdio, with `SystemClock` frozen at 2026-10-19 09:00 UTC through
`sidecar_clock.py`. The driver is `path_run.py`, compared by `pcmp.py` with run-generated ids normalised. All runs
used copies of main's mvp-0.29 vaults:
- (i) `cm`: main's code;
- (ii) `coff`: the merge with `[reading_paths] enabled = false`;
- (iii) `cdef`: the merge at its defaults.

Each run made these calls:
1. `initialize`;
2. `reader.prompt_contract`;
3. `reader.guide_plan` on an opened reading (probability `ext_01KYMSJJNJQ0W9QHZ9ZMFD88NY`, 10 sections; linear_algebra
   `ext_01KY2YGNVCCVEQCGCE4RH3BWHQ`, 39 sections);
4. `reader.reading_path` (`judge: true`), polled while `judging`;
5. in (iii) only: `reader.reading_path_set_depth` (`learn_to_use_it`), polled, then `reader.reading_path_override`
   (`read_anyway` on the guide plan's first section), then `reader.reading_path` with `retry`;
6. `reader.reading_path` read-only;
7. the guide plan again;
8. on probability, a manual-graded attempt on `pi_prob_derive_complement`;
9. `shutdown`;
10. then `learnloop reader report --json` on the same copy.

| Step | (i) main vs (ii) switch off | (iii) defaults, every difference from (i) |
|---|---|---|
| `initialize` | the method list differs: **the three RW7a RPCs register while off**. Also the vault path and `health.database` (`latestMigration` 215 vs 217, `migrationsApplied` 201 vs 202) | the same |
| `reader.prompt_contract` | **identical** | gains `readingPaths` (`enabled`, the three depths). Orient's palette gains **"what matters here?"** (`what_matters_here`, effect `reading_path`, `model: false`) first; "what do I need first?" is unchanged, second |
| `reader.guide_plan` (both reads) | **identical** | **identical** |
| `reader.reading_path` | (i) `method_not_found`; (ii) refused, `reading_paths_disabled` ("Reading paths are off (reading_paths.enabled = false)."), the registry difference above | `ask_depth` (no depth chosen, no DL2 intent on these sources), goal line "No active goal covers this book: the path follows the depth you chose.", **no call** |
| `reader.reading_path_set_depth` | — | one `reader_path_depths` row (`learn_to_use_it`, origin `guide`). The answer is `judging`, then **`failed`, reason `unpriced`** ("A metered reading-path route needs source_retrieval.llm_price_per_million."): refused before any call. The retry read is refused the same way |
| `reader.reading_path_override` | — | refused, `validation_error` "That section has no label yet." (nothing was judged, so nothing can be overridden); nothing written |
| the attempt (probability) | every call **identical** (ids normalised); the rows it added in 23 tables are identical across (i), (ii), (iii) and (iv) once ids (the attempt id in `response_ref`) are normalised | identical |
| `learnloop reader report --json` | identical apart from `window.until` (the CLI's wall clock) | gains `reading_paths`: `depth_choices {learn_to_use_it: 1}`, `judged_sections 0`, `labels {}`, `overrides {}` |
| rows written beyond the attempt and the open-time derived refresh | none on either | `reader_path_depths` 1. No `reader_path_sections`, `reading_path_role` ledger, `judgment_work_claims`, `source_service_spend` or `model_call_receipts` row |

So (i) and (ii) are identical call by call, apart from the method registry (and so the off refusal code of
`reader.reading_path`), the vault path and the migration head. Attempt evidence is unchanged.

**(iv) The route actually tried** (probability only). This was (iii) plus `source_retrieval.llm_price_per_million =
1.0` and a dummy key in the loopback profile's variable, so the metered judge sends to `127.0.0.1:9`. The result:
- **6** requests (the initial judgment, then *try again*; 3 attempts each under the caps);
- 12 `model_call_receipts`, every one **`failed`**: 6 `reading_path_judge` (`AIProviderUnavailable`) and 6
  transport children (`APIConnectionError`);
- the view `failed`, reason `judge_failed`, "Couldn't read a path for this book just now. Try again ↵";
- the failure is remembered: the read-only read stays failed with no new request;
- one `judgment_work_claims` row, `released` (epoch 2);
- 6 `source_service_spend` rows under `reading_paths.max_daily_cost_usd`, each **settled at its $0.022089 estimate**
  (finding 2);
- no `reader_path_sections` row and no ledger row; the override is refused the same way.

**`model_call_receipts`.** 38 learner databases under `landing-rw7a/` carry the table. **No row completed** in any of
them. The only rows are (iv)'s 12 failed ones.

### New findings

1. **A vitest unhandled error under load (Low, from before this stage).** On the first whole vitest run, made while
   `pytest -n auto` loaded the machine, `libraryExercisesReader.test.tsx` (RW4b's) reported an uncaught `TypeError`.
   The library page's 300 ms search debounce fired after the test, and the test's `readerSearchSources: vi.fn()`
   returns `undefined` (`ReaderScreen.tsx:725`). The tests passed. Neither this test file nor the search effect
   changed in RW7a, and the error did not come back in four reruns. **Follow-up:** the mock should resolve
   (`vi.fn().mockResolvedValue(...)`).
2. **A transport failure is charged its estimate against the day's cap (Low).** In (iv), each refused connection
   settled its full estimate ($0.022089) in `reading_paths.max_daily_cost_usd`. A failed judgment and one *try
   again* used $0.13 of the $0.50 a day. This is the shared `PaidCalls` / `SharedDailyEnvelope` accounting
   (`max(estimate, reported)`, conservative when nothing is reported), not RW7a's code, and the cap still bounds
   repeated *try again*. On Codex (the owner's default) the route is `estimated_only` and not capped.
3. **No composition work.** The stage branched from main's tip, so the merge was clean, and the gate and parity found
   nothing to fix.

### For the owner

- **Migration 217 applies on the next open** of a vault by the merged code, through the coordinator. **Close the
  app, the MCP server and the mobile host, and back up first.** It adds two empty append-only tables
  (`reader_path_sections`, `reader_path_depths`). No existing row changes, and nothing served moves: certification,
  the Today queue and the daily plan were byte-identical on your copies (parity (a), (b)). Your algorithm version is
  unchanged; there is no successor.
- **What you see.** In the Reader's Guide, a book you open asks "How deep do you want to go?" (get the idea · learn
  to use it · fluency). If you set a depth intent for the book in your Learn setting (DL2), it is preselected. Once
  you pick, the Guide shows your path:
  - each section labelled core, prerequisite, enrichment, already shown ● (only with your own evidence) or assumed
    (only with an open assumption), with a one-line *why*;
  - *read it anyway* and *skip it* on each section; skipping marks nothing as known;
  - one exercise worth trying per core section, with *Try it*;
  - a "next" line computed without a model.

  Orient gains "what matters here?", which opens the path.
- **The cost.** The judge makes one `reading_path_judge` call per book, depth and state. The state changes when the
  sections, your evidence on their LOs, the goal or the prompt change. The judge runs automatically when the Guide
  opens with a known depth and the cached path is out of date. On Codex (the default) the call is `estimated_only`. A
  metered route needs `source_retrieval.llm_price_per_million` and is capped at `reading_paths.max_daily_cost_usd`
  (**$0.50 a day**). The prompt carries section titles, roles and LO titles with your status on each: no passage text
  and none of your text.
- **The switch.** `[reading_paths] enabled = false` turns it off: every RW7a RPC refuses, the Guide and the prompt
  contract are `a76c8358a`'s, Orient has no "what matters here?", and the reader report has no `reading_paths`
  block. On your copies, the sidecar then answered exactly as main (parity (c)). Settings, the disclosure registry and
  `eval judges` still list the route (open items).

### Open questions (defaults in force)

1. *"Already shown" on LOs without authored blueprints?* **Never**: `lo_certification` is not demonstrated without
   blueprints, so such a section stays core.
2. *"Assumed" with demonstrated LOs mixed in?* **Assumed** when every LO is demonstrated or open-assumed and at least
   one is assumed.
3. *Exercises outside the section (end-of-chapter units)?* **None named** for that section; no end-of-chapter mapping.
4. *The judge's cap?* **`reading_paths.max_daily_cost_usd = 0.50`** (metered routes; Codex is `estimated_only`).
5. *Overrides per depth?* **Yes**: a skip at "learn to use it" does not skip at "fluency".
6. *The judge runs automatically when the Guide opens with a known depth* (a DL2-preselected depth included) and the
   cached path is stale? **Yes**, once per state.
7. *RW7b's stale-path fallback?* The suggested default for RW7b is to **fall back to book order** when the path is
   stale, with the receipt naming it. A plan build never triggers a call (§7).

### Open items

- **The card's "next" can stay stale after a transient refresh failure (ruled Low).** If a re-read of the path fails
  transiently, the mounted card keeps its earlier "next" line until the next landed progress save re-reads it, and
  then it recovers.
- **Configured routes listed while off (ruled Low, V3).** Settings (`get_settings`), the disclosure registry and
  `learnloop eval judges` list `reading_path_judge` while `reading_paths.enabled` is false, because they list
  configured routes. The switch governs behaviour (no call, every RPC refuses, no contract key, no palette action, no
  report block), not route metadata.
- **Findings 1 and 2** above (Low).
- **From the stage, not built:** no `path_depth_set` / `path_override` interaction events (§2 item 3); exercises from
  the sources spec's candidates (§2 item 6, open question 3); RW7b's `plan_uses_path`.
- **From before this stage:** `desktop_validate.py` (`syntheticBook.ts`) and `module_validate.py` (968 issues).

**Process note (landing).** Every Python and CLI run outside pytest went through `env -i` with an empty HOME,
CODEX_HOME and LEARNLOOP_CONFIG_DIR, with one exception. A `python3 -` with an empty here-document (it executed no
code) was started outside `env -i` while editing a script. It read nothing, opened no vault, made no network call and
used no credential. No stash was used, no fixture vault was opened except through `learnloop.db.copies`, and no git
command ran in the main checkout.

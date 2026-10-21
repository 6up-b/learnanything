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

Process notes (this stage): two early edit/read commands ran `python3`
outside `env -i` (a one-line edit of `db/table_roles.py` and a read of the
golden JSON), and one `git stash list` (read-only) slipped into a compound
command before the rule was applied; neither touched a vault, a credential
or the network, and every later run used `env -i` with empty HOME,
CODEX_HOME and LEARNLOOP_CONFIG_DIR.

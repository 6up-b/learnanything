# Adaptive hints H1: approach maps (stage `hints-h1`)

Branch `hints/h1` (worktree `learnanything-merge4`), base `main` at
`cdcd70601` (H0 landed; migration head 210). Spec:
`docs/specs/spec_adaptive_hints_v1.md` §2, §3, §4.3 and §4.3.1, §4.4 (checkpoint
links and "no map"), §7.2-7.4, §9 (`approach_maps`, config), §10 (H1 row,
order, §10.1), §11 (G-H1 maps clause, G-H9, G-H10, G-H11, G-H13, the H1 tests),
§13 (the diagnoser-reads-map row), §15, §16.4; `docs/reviews/adaptive-hints-H0.md`
§9 friction note 1; `spec_reader_workbench_v1.md` §17 "Full solution graphs" as
the hints spec's §8.2 item 10 amends it.

## 0. Plan (written before the code)

**Scope.** H1 only: maps are built, validated, stored, merged and reported. Not
here: the hint service, chooser, writer or `practice.request_hint` (H2);
workbench help (RW2b/H3); any UI; any evidence, grading, scheduling, serving
or replay change. Nothing in H1 shows a map to the learner or renders one
(Reader §17 as amended: RW2b reads maps when present).

**Migration 211** (`211_approach_maps.sql`): `approach_maps`, WORKFLOW (paid
output, never rebuilt, no replayer), §9's columns plus the revision keys
`seeds_hash` (every seed) and `structure_hash` (the item-side seeds
`practice_item_hash` does not cover: trace contract, PF skeletons, authored
hints) and `trigger` (serve | inline | cli | merge). Rows are immutable
(no-update and no-delete triggers): a revised item, changed seeds or a learner
merge is a new row with `version + 1` and `supersedes_id`, never an UPDATE of
`map_json`. `UNIQUE(practice_item_id, version)` and
`UNIQUE(practice_item_id, practice_item_hash, seeds_hash)` de-duplicate racing
builders across processes. `help_assists.map_id` stays a soft reference (H0
friction note 1): a store helper validates it in code; no FK. Classified in
`db/table_roles.py`; `fixtures/migration_head_210` -> `_211` (backup-API copy,
only 211 applied, rollback journal) and every hard-coded path; the reference
scripts' head.

**Package `learnloop.hints`** (still under `hints-never-write-evidence`):
- `maps.py`: `ApproachMapV1` (nodes with role given/step/goal, label, state,
  recognizers, checkpoint_id, leak; edges with technique, principle,
  facet_ids; routes with name, path, origin, learner attempt ids) as a wire
  model, and the validator in code (§4.3): structure, DAG, every route from a
  given to the goal along edges, facets belong to the item, labels non-empty
  and free of any expression from a leak node (code marks a node `leak` when
  its state gives the expected answer away; the goal always), checkpoint and
  origin references resolve against the seeds, the goal agrees with the
  expected answer by exact key where one exists (`answer_check`), else stored
  with `verified_goal = false`. Failures by reason.
- `map_seeds.py`: the seeds (§4.3 items 1-3): reference solution, rubric,
  authored hints; trace-contract recipes (alternative recipes are alternative
  routes); PF skeletons (`item_skeletons` by `skeleton_content_hash`); the
  learner's textbook worked examples for the item's LO through T6's
  `find_sources_for_caller` under the item-bound practice caller
  (`assisted_practice`: the item-bound exclusions, exam withholding and the
  answer-overlap filter), `roles = ("worked_example",)`, rank only, no query
  rewrite; the learner's own correct solutions to the item and its family
  siblings (graded fully correct, or PF-c valid alternative via placement's
  `pfc_unverified_attempt_ids`). Missing seeds are simply absent.
- `map_builder.py`: one structured chat call on route `approach_map` through
  `PaidCalls` (receipts, checkpoints, `estimated_only` on Codex and the ChatGPT
  plan) inside a `SharedDailyEnvelope` named `hints.maps.max_daily_cost_usd`
  (atomic, every process); a failing map re-asked once with its reasons, then
  not stored; each validation appended to `judgment_ledger` (task
  `approach_map_valid`, judge `verifier`). Family template: a sibling's
  builder receives the family's latest map. Triggers: `schedule_build_on_serve`
  (a daemon thread started after the serve's response is built; one build per
  item in flight, de-duplicated; never raises into, waits on or changes the
  serve), `build_map_inline` (H2's synchronous entry: waits for an in-flight
  build, then builds; tested, wired to no RPC), `merge_learner_routes` (lazy:
  new attempts matched to a route gain its attempt id, or form a route with
  origin `learner:<attempt ids>`; a new version row), and `current_map`
  (the one reader; None with the kill switch off).

**Route `approach_map`**: `AITask`, `ROUTE_FOR_OPERATION`, `AIRoutingConfig`
(unset -> `ai.active_provider`, the spec's fallback; any profile including
`codex_low`); `LEARNLOOP_AI_PROVIDER` may override it like any chat route, and
the cap then still applies because admission follows the resolved route's
billing. A disclosure row (the route sends the learner's own correct answers
in the background). No Settings UI change.

**Config** `[hints] price_per_million` (unset: a metered map build is refused
before sending, as every spend role does) and `[hints.maps] enabled`,
`build_on_serve`, `max_daily_cost_usd = 0.50`. Every
`DEFAULTS_SNAPSHOT_BY_ALGORITHM` entry recomputed with the "no scoring,
scheduling, projection or serving change" note.

**Sidecar.** `get_practice_item` with a session (the practice screen's serve)
calls `schedule_build_on_serve` after the response is built (try/except,
nothing returned to the response). A test guard env var
`LEARNLOOP_APPROACH_MAP_BUILDS=off` (set in `tests/conftest.py`, as
`LEARNLOOP_ROUTER_MODELS=off` is) stops an unfaked background build from
resolving a real client in any test.

**CLI** `learnloop hints maps build [--item | --family | --lo] [--limit]
[--dry-run] [--json] --vault`: the dry run opens the database read-only,
retrieves nothing, makes no call and writes nothing, and prints per item the
plan and the estimate (sources at their cap); a real run builds the items
without a current map, stops on a capped day and says so. `learnloop hints
report` gains a `maps` section: maps stored and current, served items
(attempted) with and without a current map, validation failures by reason,
builds not stored, route counts by origin, receipts and today's spend against
the cap.

**Boundaries.** A new import-linter contract: `learnloop.attempts` and
`learnloop.diagnosis` (every grading and diagnosis prompt builder) import
neither `learnloop.hints` nor the map store; a test scans their sources for
`approach_maps` and checks a graded submit with a stored map never touches
the map store. The pure reads `hints` needs from forbidden packages
(`attempts.answer_check`, `placement.state.pfc_unverified_attempt_ids`) are
`ignore_imports` lines with their reasons.

**Tests** (fakes only, `StructuredClientFake` subclasses):
`tests/test_approach_maps.py`, `tests/test_approach_map_replay.py` (G-H10),
`tests/test_approach_maps_schema.py` (migration, durability lane, roles),
`tests/test_approach_map_boundaries.py` (grader/diagnoser).

**Owner question recorded (not changed):** build-on-serve defaults ON per the
spec, so every newly served item revision makes one background model call on
the owner's vaults; the CLI and report show the counts and spend.

## 1. What was built

### 1.1 Migration 211 (`migrations/211_approach_maps.sql`)

`approach_maps`, WORKFLOW (`db/table_roles.py`): §9's fourteen columns (`id`,
`practice_item_id`, `practice_item_hash`, `family_id`, `version`, `map_json`,
`seeds_json`, `validation_json`, `verified_goal`, `model`, `prompt_version`,
`input_hash`, `created_at`, `supersedes_id`) plus three H1 uses: the revision
keys `seeds_hash` (every seed) and `structure_hash` (the item-side seeds
`practice_item_hash` does not cover: the trace contract, the PF skeletons, the
authored hints and, since review F5, the resolved rubric an item may inherit
from its practice mode's default), and `trigger` (`serve` | `inline` | `cli` | `merge`).
CHECKs: `version >= 1`, `verified_goal` 0/1, `trigger`, `supersedes_id != id`;
`supersedes_id` -> `approach_maps(id)`; `UNIQUE(practice_item_id, version)` and
`UNIQUE(practice_item_id, practice_item_hash, seeds_hash)` (a last line only:
cross-process builds are claimed durably and their commits fenced; see
`hints-h1-codex-review.md` F3). Two indexes (item+version, family+time), two
triggers: no update (rows are immutable: a new version is a new row) and no
delete (paid output). No replayer, no DERIVED table; nothing in replay,
rebuild, scoring, scheduling, serving or grading reads it.
`help_assists.map_id` stays a soft reference: `store.map_exists` is the code
check (H0 friction note 1); no foreign key was added.

Head fixture: `fixtures/migration_head_210` -> `fixtures/migration_head_211`
(git rename), a backup-API copy of the base's 210 database with only 211
applied under `upgrade_allowance(UPGRADE_TEST_HELPER)`,
`wal_checkpoint(TRUNCATE)` -> `(0, 0, 0)`, `journal_mode=DELETE` (header bytes
18-19 are 1/1), `integrity_check` ok, `foreign_key_check` empty, copied into
place with the backup API, no companion files; README gains the 211 paragraph
and the chain. Every path naming `_210` now names `_211` (27 test files, both
reference scripts with `SCHEMA_HEAD = 211`, `docs/decider-tier1-migration.md`,
the Database Catalog); `test_route_rules_in_grader.py`'s head assertion is 211;
`test_help_assists_schema.py` and `test_library_asks_migration.py` tolerate
211's objects on the way to head and read the head at 211.

### 1.2 Store (`src/learnloop/db/stores/approach_maps.py`)

Registered SQL owner (`tests/test_architecture.py`): `COLUMNS`, `insert_map`
(refuses unknown columns), `latest_map`, `current_map` (newest version for an
item revision and structure hash), `next_version` (version + the row it
supersedes), `family_template`, `map_row`, `map_exists`, `all_maps`; every
read tolerates a database without the table (a dry run or report on an older
vault, which is never migrated).

### 1.3 `learnloop.hints` (under `hints-never-write-evidence`)

- `maps.py`: `ApproachMapV1` (nodes: id, role given/step/goal, label, state,
  recognizers, checkpoint_id, leak; edges: from_node, to_node, technique,
  principle, facet_ids; routes: id, name, path, origin, learner_attempt_ids;
  goal_node_id; goal_answer) and `LearnerRouteMergeV1` as wire models; the
  validator `validate_map` (reasons: `malformed`, `cycle`, `no_route`,
  `no_reference_route`, `route_not_given_to_goal`, `foreign_facet`,
  `empty_label`, `label_leak`, `unknown_checkpoint`, `unknown_origin`,
  `goal_mismatch`, plus the merge's `merge_unknown_attempt`,
  `merge_unplaced_attempt`, `merge_unknown_route`, `merge_node_collision`);
  `apply_merge`; `route_counts`. Leak control: a node is marked `leak` by code
  when its state gives the answer away (`span_leaks_expected` against the
  expected answer and against its exact key), and the goal always is; a label
  fails when it contains an expression (math segment, formula, multi-digit or
  fractional number) of any leak node's state or of `goal_answer`, unless the
  question itself states it, or when it gives the answer away (a lone-digit
  exact key matched as a number token of its own: review F1). The goal agrees
  by exact key (`answer_check.parse_answer` / `reference_final_answer`) where
  one exists: the declaration and the goal node's own conclusion are both
  checked, a decidable difference in either -> `goal_mismatch` (review F2),
  else equal -> `verified_goal`, otherwise (no key, no `goal_answer`,
  undecidable) stored unverified with the basis named. Every seeded learner
  solution must sit on exactly one route (`unplaced_attempt`, review F4).
- `map_seeds.py`: `assemble_seeds` (item side: reference solution, rubric via
  `vault.rubric_for_item`, authored hints, the trace contract when it has
  recipes, PF skeletons from `item_skeletons` by `skeleton_content_hash`;
  sources: `find_sources_for_caller` with the item-bound practice caller
  `CallerContext(kind="code", context="practice", item_id=...)`, so the derived
  policy is `assisted_practice` with T6's item-bound exclusions, exam
  withholding and the answer-overlap filter, `intent="explain"`,
  `roles=("worked_example",)`, `verify=False`, `rewrite=False`, at most 4
  passages of 1500 characters; attempts: the item's and its family siblings'
  answers graded fully correct, or PF-c valid (`pfc_unverified_attempt_ids`),
  never a held grade or a non-answer attempt type, newest first, at most 6 of
  2000 characters), `item_revision` (the cheap serve-side key), `seeds_hash`,
  `record()` (ids, never texts).
- `map_builder.py`: `build_map` (one structured call on `approach_map`
  through `PaidCalls`; the shared envelope `hints.maps.max_daily_cost_usd`
  around every metered call; client, price and a spent day checked before any
  retrieval; re-ask once with the reasons, details and previous answer; each
  validation appended to `judgment_ledger`, task `approach_map_valid`, judge
  `verifier`, verdict `valid` / `invalid_reasked` / `invalid_not_stored`,
  question `(practice_item, approach_map_revision: <item hash>:<structure hash>)`;
  the version row written in one BEGIN IMMEDIATE transaction);
  `schedule_build_on_serve`; `build_map_inline`; `new_learner_attempts` and
  `merge_learner_routes`; `current_map` (the one reader); `backfill`,
  `plan_item`, `select_items`; `maps_envelope`, `maps_spend_today`;
  `wait_for_background_builds`.
- `map_report.py`: the report's `maps` section.

### 1.4 Route, config, sidecar, CLI

- Route `approach_map`: `AITask`, `ROUTE_FOR_OPERATION` (`approach_map`,
  `approach_map_merge`), `AIRoutingConfig.approach_map` (unset ->
  `ai.active_provider`, the spec's fallback); a disclosure row in
  `ai/disclosures.py` (consumer `approach_maps`: the question, its reference
  solution, rubric, hints, recipes, the learner's book passages and own
  correct answers go to the route's provider in the background). No Settings
  UI change.
- Config: `[hints] price_per_million` (unset) and `[hints.maps] enabled = true`,
  `build_on_serve = true`, `max_daily_cost_usd = 0.50` (modelled defaults, out
  of the decision-only template). All 19 `DEFAULTS_SNAPSHOT_BY_ALGORITHM`
  entries recomputed after clearing the template `.pyc`, with the "no scoring,
  scheduling, projection or serving change" note (mvp-0.9 paragraph and one
  line under every other version).
- `find_sources` gains `rewrite: bool | None = None`, passed to `search_spans`
  (None keeps every existing caller byte-identical).
- Sidecar: `get_practice_item` with a session calls `schedule_build_on_serve`
  after the response is built (a failure is a debug log event, never an
  error); `ctx.approach_map_client` injects a client (tests). No new RPC.
- `tests/conftest.py` sets `LEARNLOOP_APPROACH_MAP_BUILDS=off`: a serve starts
  no build unless a client was injected (the `LEARNLOOP_ROUTER_MODELS=off`
  precedent), so no unfaked test can reach Codex on this machine.
- CLI: `learnloop hints maps build --vault <v> [--item | --family | --lo]
  [--limit N] [--dry-run] [--json]`; `learnloop hints report` gains `maps`.
  CLI help snapshot rewritten.

### 1.5 Boundaries

- New import-linter contract `graders-never-read-approach-maps`:
  `learnloop.attempts` and `learnloop.diagnosis` import neither
  `learnloop.hints` nor `learnloop.db.stores.approach_maps`.
- `hints-never-write-evidence` gains two `ignore_imports` lines, each a pure
  read: `learnloop.hints.maps -> learnloop.attempts.answer_check` (the exact
  key) and `learnloop.hints.map_seeds -> learnloop.placement.state` (PF-c valid
  alternatives).

## 2. Gates and where they are tested

| Gate | Test |
|---|---|
| Seeds (§4.3 items 1-3) | `test_approach_maps.py::test_seeds_carry_the_trace_contract_skeleton_rubric_and_authored_hints`, `::test_a_seed_the_item_lacks_is_simply_absent`, `::test_worked_examples_come_from_t6_under_the_item_bound_policy` (the real T6 on the canonical-sources textbook vault: only the worked-example span, never an exercise or solution span, policy `assisted_practice`, no rewrite, no verification, zero receipts), `::test_only_the_learners_own_correct_or_pfc_valid_solutions_in_the_family_are_seeds` |
| G-H9 validator, every rule; never stored when failing | `::test_every_validation_rule_rejects_its_case` (17 cases), `::test_a_valid_map_passes_and_code_marks_the_leaks`, `::test_links_to_existing_checkpoints_recipes_and_question_values_pass`, `::test_a_goal_without_an_exact_key_is_stored_unverified`, `::test_a_failing_map_is_reasked_once_with_its_reasons_then_not_stored`, `::test_a_map_failing_once_is_stored_from_the_reask` |
| Revision keys, supersession, immutability | `::test_a_revised_item_or_changed_seeds_gets_a_new_row_never_an_update`, `test_approach_maps_schema.py` |
| Family templates | `::test_a_siblings_builder_receives_the_familys_map_as_its_template` |
| Build on serve: background, de-duplicated, never blocks/fails/changes a serve | `::test_a_serve_starts_one_background_build_and_never_waits_for_it`, `::test_a_read_only_open_builds_nothing`, `::test_a_failing_or_raising_build_never_reaches_the_serve`, `::test_without_an_injected_client_the_test_guard_starts_no_build` |
| Inline build (wired to no RPC) | `::test_the_inline_build_builds_now_and_stores`, `::test_the_inline_build_waits_for_a_build_in_flight_and_never_builds_twice`, `::test_no_rpc_reaches_the_inline_build_or_the_merge` |
| Learner-route merge; learner routes only from correct or PF-c-valid answers | `::test_new_correct_answers_gain_a_matching_route_or_open_a_learner_route`, `::test_a_merge_that_misplaces_an_answer_is_reasked_then_not_stored`, `::test_a_merge_needs_a_map` |
| G-H11 dry run writes nothing; spend caps; estimated_only | `::test_the_dry_run_prints_the_estimate_and_writes_nothing` (no client resolved, no retrieval, every vault file byte-identical), `::test_the_backfill_builds_selected_items_and_skips_current_ones`, `::test_a_metered_route_without_a_price_is_refused_before_sending`, `::test_the_daily_cap_holds_on_metered_routes_and_says_so`, `::test_a_metered_build_under_the_cap_reserves_and_settles_its_spend`, `::test_codex_is_estimated_only_and_never_capped`, `::test_the_route_falls_back_to_the_active_provider_and_an_override_keeps_the_cap` |
| G-H1 maps clause (kill switch) | `::test_the_kill_switch_builds_nothing_and_reads_nothing`, `::test_practice_rpcs_are_byte_identical_with_maps_on_or_off` (`get_practice_item` and `submit_attempt` through the real sidecar, maps on with a fake vs off) |
| G-H10 replay | `test_approach_map_replay.py` (rebuild and shadow replay with model, embedding and map-builder constructors forbidden and an SQLite authorizer refusing every read of `approach_maps`; derived state equal to a copy with both tables dropped; rows unchanged; the authorizer's own check; no substrate module names the table) |
| G-H13 boundaries | `lint-imports` (`hints-never-write-evidence`, `graders-never-read-approach-maps`), `test_approach_map_boundaries.py` (sources of every grading/diagnosis module, the contracts' content, rendered blind and joint grading prompts with a stored map carry none of it and read nothing from the table), `test_table_roles.py`, `test_approach_maps_schema.py::test_approach_maps_is_workflow` |
| Report (§10 "data it starts") | `::test_the_hints_report_shows_maps_failures_routes_and_spend`, `test_hint_telemetry.py::test_the_report_cli_reads_the_vault_read_only` |
| The soft `map_id` reference | `::test_help_assists_map_id_is_a_soft_reference_checked_in_code` |
| Migration and durability lane | `test_approach_maps_schema.py::test_211_adds_approach_maps_and_nothing_else`, `::test_211_on_the_durability_lane` |

## 3. Decisions and deviations

1. **Columns beyond §9.** `seeds_hash`, `structure_hash` and `trigger`: §9's
   "a hash of its seeds" and the task's revision keys need a column; the
   structure hash is what a serve can check without retrieval (computing the
   full seeds hash would mean a T6 search, with embeddings, on every serve).
   `trigger` tells the report what build-on-serve costs.
2. **When a map is current.** A map is current when it was built for the
   item's `practice_item_hash` and `structure_hash`. New source passages or new
   correct answers do not make a serve rebuild: answers reach the map through
   the lazy merge (§4.3.1 row 3), and a re-read library through the owner's
   CLI after the item revision changes. Recorded as open question 2.
3. **Wire field names.** `from_node` / `to_node` (the spec's `from; to`;
   `from` is a keyword); nodes carry `role` (given, step, goal), which "every
   route runs from a given to the goal" needs; the map carries
   `goal_node_id` and `goal_answer` (the builder's declaration the exact-key
   check compares); a route carries `learner_attempt_ids`, so a matching route
   "gains the attempt id" without rewriting its origin.
4. **Code-marked leaks.** The builder's `leak` marks are kept and widened:
   the goal is always a leak node, and any node whose state gives the answer
   away (span leak against the answer or its exact key) is marked by code and
   listed in `validation_json.leak_marked_by_code`.
5. **A label may name what the question states** ("Evaluate the CDF at 1/2"
   when the question asks for P(X <= 1/2)): expressions found in the item's
   prompt are not leak expressions. Without this the literal rule fails most
   maps on their own givens.
6. **`no_reference_route`** is a validation rule: the spec says the builder
   "records the reference route", and the no-map fallback and `book_way` (H2)
   are placed on it.
7. **Checkpoint and origin references must resolve** (`unknown_checkpoint`,
   `unknown_origin`): a node's `checkpoint_id` names a trace-contract or
   skeleton checkpoint, a `trace_contract:<recipe>` origin a recipe, a
   `source:` / `learner:` origin seeded passages or attempts (prompt refs are
   stored as span keys and attempt ids).
8. **Validation failures are ledger verdicts**, as §9 lists the task
   `approach_map_valid` (judge `verifier`): one row per validation round. A
   serve never retries a revision whose build was not stored (no spend per
   serve); the CLI retries it, and a retry recovers both paid answers from
   their checkpoints, so it costs nothing unless the seeds changed.
9. **Seeds through T6, unpaid.** `intent="explain"` with
   `roles=("worked_example",)` and `verify=False` (rank only) instead of
   `intent="worked_example"`, whose verification is a second paid call
   (`source_rerank`); `rewrite=False` through the new `find_sources` argument.
   Query embeddings still follow `embedding.enabled` (T6 as it is; their
   receipts are the embedding route's, outside the maps cap).
10. **Spend envelope.** RW4a's `SharedDailyEnvelope` in the shared spend
    ledger under its own envelope name and owner kind `approach_map`, entered
    through `spend_envelopes` so each metered call's reservation is named on
    its receipt and settled with its actual cost (RW4a's organizer reserves
    through an admit hook instead). Maps, merges (and, at H2, outcome
    placement) share it, as §7.3 says.
11. **Price key.** `hints.price_per_million` (§9 names it under `[hints]`),
    unset by default like every metered price in the vault: a metered
    `approach_map` route is refused before sending until the owner sets one.
12. **Disclosure.** The route sends the learner's own correct answers and book
    passages in the background, so it gets a disclosure row like RW4a's
    organizer (`get_settings` lists it; `test_judge_routes.py` updated).
13. **Background thread in a fresh context** (`contextvars.Context()`), not a
    copy of the serve's: no envelope, observer or deadline of the serving
    request leaks into the build.
14. **The build-on-serve hook is the practice screen's serve only**
    (`get_practice_item` with a session). The workbench (RW2b) and guided redo
    (H4) serves call `schedule_build_on_serve` when they land; probes never
    (no hint is served in a diagnostic block).
15. **The inline build is a separate call.** §4.3.1 row 2 has "the writer
    builds the map inline in the same call"; H1 has no writer, so
    `build_map_inline` is a standalone synchronous build (the task's scope). H2
    may fold the map into its writer's output (reusing `ApproachMapV1` and
    `validate_map`) or call this function; see friction note H2-1.
16. **The report reads stored maps whatever `hints.maps.enabled` says** (it is
    the owner's view, and says how the switch is set); no hint or serving path
    reads a map with the switch off (`current_map` answers None).
17. **§3's citations, re-verified on `cdcd70601`:** the substance holds; lines
    moved: `TraceRecipe` / `TraceContract` at `vault/models.py:418-447` (spec
    `:392-401`); `practice_item_hash` at `vault/hashes.py:46` (spec `:44-58`);
    `item_skeletons` at `migrations/174_pf_generation.sql:58`; the skeleton
    prompt at `content/authoring/pf_contracts.py:179` (spec `:173`), written by
    `ops/pf_generation.py:588` (spec `:458`); the "Hints" heading -> `solution`
    at `ingest/block_roles.py:88` (spec `:87`); `ITEM_BOUND_EXCLUDED_ROLE_HINTS`
    at `source_retrieval/corpus.py:160` (spec `:157`); `first_invalid_id` at
    `diagnosis/probe_blocks.py:302` (spec `:249-258`); guided redo's
    `changed_checkpoint_ids` at `diagnosis/guided_redo.py:322` (spec `:321`);
    `answer_leaks_expected` at `tutor/tutor_qa.py:975`;
    `instrument_expected_information_gain` at `diagnosis/probe_families.py:467`.

## 4. Successor

None (§10.1). Maps are stored help: no scoring, scheduling, projection,
serving, grading or replay path reads `approach_maps` or the new keys; serving
waits on nothing and returns the same bytes with the switch on or off.

## 5. Tests and counts

New: `tests/test_approach_maps.py` (51), `tests/test_approach_map_replay.py`
(3), `tests/test_approach_maps_schema.py` (6, one durability-marked),
`tests/test_approach_map_boundaries.py` (3), helpers
`tests/approach_map_fakes.py` (`MapFake`, a `StructuredClientFake`).
Changed: `tests/conftest.py` (the build guard), `tests/test_hint_telemetry.py`
(the report's `hints` and `maps`), `tests/test_help_assists_schema.py` and
`tests/test_library_asks_migration.py` (211 on the way to head),
`tests/test_route_rules_in_grader.py` (head 211), `tests/test_architecture.py`
(the store), `tests/test_judge_routes.py` (the disclosure),
`tests/cli_help_snapshot.json`, and the 27 test files whose head path moved.

## 6. Files

- Migration and fixture: `migrations/211_approach_maps.sql`;
  `fixtures/migration_head_211/` (renamed from `_210`, rebuilt, README).
- Python: `src/learnloop/hints/{maps,map_seeds,map_builder,map_report}.py`,
  `src/learnloop/db/stores/approach_maps.py`, `src/learnloop/db/table_roles.py`,
  `src/learnloop/cli/hints.py`, `src/learnloop/config/schema.py`,
  `src/learnloop/config/template.py`, `src/learnloop/ai/routing.py`,
  `src/learnloop/ai/disclosures.py`,
  `src/learnloop/source_retrieval/find_sources.py`,
  `src/learnloop_sidecar/handlers/practice.py`, `pyproject.toml`.
- Docs: this file; `docs/specs/spec_adaptive_hints_v1.md` §15 (the H1 note);
  `docs/learnloop-architecture-vault/_scripts/db_{generate,validate}_reference.py`
  (head 211, the `hints` section's concern); the regenerated references (new
  `Tables/approach_maps.md`, `Config - hints.md`, commit labels and line
  citations elsewhere; prose counts in `Configuration.md` and `Database.md`:
  886 leaves, 330 tables); `docs/decider-tier1-migration.md` (the head path).
- No frontend or Tauri change.

## 7. Open questions (with the default taken)

1. **Build on serve on the owner's vaults (owner decision).** The spec's
   default is On, so after this lands every newly served item revision makes
   one background model call on `ai.routing.approach_map` (unset: the active
   provider; on the owner's vaults Codex, `estimated_only`, with no daily
   bound; one Codex turn each, which the spec measured at 29-37 s for blind
   grading, §7.2). The dry run on a backup-API copy of
   `fixtures/probability` (section 9) counts 77 active items without a map and
   at most about 2.25 M tokens for one map each (28-36 k per build, an upper
   bound: 16 k output budget and the worked examples at their cap). Default
   taken: On, as the spec says; `learnloop hints report` shows versions by
   trigger, model calls and today's spend so the owner sees it. Alternatives:
   `build_on_serve = false` (maps only from the CLI backfill and, at H2, inline
   on a hint), or route `approach_map` to `codex_low`.
2. **Rebuild on new seeds.** A map is current for its item revision and
   item-side seeds; new book passages do not rebuild it, new correct answers
   reach it through the lazy merge. Default: as built; the CLI could gain a
   `--refresh` once H2 shows stale maps matter.
3. **Metered price.** `hints.price_per_million` is unset, so a metered
   (OpenRouter) map route is refused until the owner prices it. Default: unset.
4. **One envelope for maps and merges** ($0.50 a day metered). Default: as the
   spec says; H2's outcome placement joins it.
5. **A failed revision on serve** is not retried until its item revision
   changes or the owner runs the CLI. Default: as built (no repeated spend per
   serve).
6. **Settings exposure** of `[hints.maps]`. Default: none in H1 (no UI);
   modelled defaults in `learnloop.toml`.

## 8. Friction notes for H2, RW2b/H3 and the diagnoser-reads-map follow-up (§13)

**H2.**
1. Read maps only through `map_builder.current_map(vault, repository,
   item_id)` (None with the kill switch, or when the revision has none). Write
   the map's `id` on each `help_assists` row (`map_id`) and validate it with
   `store.map_exists`; node ids are stable only within one version, so a row
   names the map version with its node ids.
2. §4.3.1 row 2 (no map at the hint): either call `build_map_inline(...,
   deadline=...)` (a separate call on route `approach_map`, which may be Codex
   and slow: give it the hint's own route via `ai.routing.approach_map`, or
   skip it within the 8 s target and serve without waypoint kinds, §4.4), or
   fold `ApproachMapV1` into the writer's schema and pass the result through
   `validate_map` and the same store path (`_store` is private: lift it to a
   public `store_validated_map` when H2 needs it).
3. §4.3.1 row 3: after a hint is shown, `new_learner_attempts` is the "map
   predates the learner's latest correct answers" predicate; run
   `merge_learner_routes` in the background exactly as
   `schedule_build_on_serve` does (fresh context, per-item lock).
4. Waypoint and subgoal contracts read `node.leak` (code-widened) and
   `maps.label_leaks` / `maps.gives_away`; reuse them for G-H5 rather than a
   second leak rule.
5. `hints.price_per_million` is the spec's shared `[hints]` price: the writer
   and chooser can use it too; `hints.max_daily_cost_usd` needs its own
   `SharedDailyEnvelope` name (maps keep `hints.maps.max_daily_cost_usd`).
6. The import-linter contract now names two pure reads; H2's EIG ranking and
   state reads need lines of their own (H0 friction note 3).
7. (Fix round 3, R2.) The map's prose leak detection (`gives_away`,
   `label_leaks`, `states_answer` over states and labels) is best-effort
   defence in depth. The binding leak gate is H2's leak control on the
   written hint text (spec §4.6), which H2 must run on every hint, whatever
   the map's `leak` marks say. Rely on the structured fields first: a node's
   `value` and the goal's `conclusion` (with `unit`) are what code checks
   with `answer_check.answers_equal`. Prose that needs algebraic rewriting
   ("x times x" for `x^2`) is a known gap (Low).
8. (Fix rounds 3 and 5.) `verified_goal` comes only from the goal node's
   `conclusion` (with `unit`). `goal_answer` is informational. Quantities are
   never unit-reasoned (fix round 5): a quantity-shaped reference ("4 m",
   "2 x", "4 °C") or a conclusion with a unit verifies only when
   `norm(conclusion + " " + unit)` equals `norm(reference)` as a string, and
   is never a mismatch. **Unverified is common for quantity answers** (a
   different but equivalent unit spelling, `2*x` for "2 x", a unit on one
   side only). An unverified map (no exact key, no conclusion, a conclusion
   that does not parse, or a quantity that is not string-identical) is
   stored and usable; H2 must not treat unverified as invalid.

**RW2b / H3.**
1. "Check my work" can name `map_node_id` / `route_id` from
   `current_map(...)["map"]` (record the map id beside them, note 1 above);
   nothing in H1 renders a map, as the Reader's §17 row now reads.
2. Opening a workbench problem bound to an item (and guided redo, H4) should
   call `schedule_build_on_serve` like the practice serve does.
3. The `learner:` routes and `learner_attempt_ids` give the learner's route
   preference per family (§4.3); the workbench's own correct solutions reach
   the map once they are attempts of the item.

**The diagnoser reads the map (§13).** `graders-never-read-approach-maps`
forbids `learnloop.diagnosis` and `learnloop.attempts` together. That
follow-up must split the contract (keep `learnloop.attempts`, the blind
grader, forbidden; name the one diagnoser module allowed to read
`current_map`), add a prompt-version suffix, and keep
`test_approach_map_boundaries.py`'s blind-grading assertions.

## 9. Owner-run commands

```bash
# Dry run first: plans every active item without a map; retrieves, calls and writes nothing.
uv run learnloop hints maps build --vault <path> --dry-run --json
# Backfill (all items, or one --item / --family / --lo; --limit caps the run):
uv run learnloop hints maps build --vault <path> [--item ID | --family ID | --lo ID] [--limit N] --json
# What exists and what it cost (the maps section):
uv run learnloop hints report --vault <path> --json
# In the vault's learnloop.toml:
#   [hints.maps]
#   enabled = false          # kill switch: nothing built, nothing read
#   build_on_serve = false   # no background builds; the CLI still builds
#   max_daily_cost_usd = 0.5 # metered routes only
#   [hints]
#   price_per_million = 5.0  # needed before a metered approach_map route runs
#   [ai.routing]
#   approach_map = "codex_low"
# A sidecar run on a vault copy with no background builds: LEARNLOOP_APPROACH_MAP_BUILDS=off
```

Migration 211 is applied by the coordinator when the vault is next opened (it
only creates the empty table).

**The dry run on a copy (no model call).** A backup-API copy of the worktree's
tracked `fixtures/probability` in `fixtures-local/h1-prob`, with
`ai.active_provider = "manual"`, `embedding.enabled = false`,
`source_retrieval.query_rewrite = false`, `hints.maps.build_on_serve = false`,
`LEARNLOOP_CONFIG_DIR` pointed at an empty directory (no keys loaded) and
`LEARNLOOP_APPROACH_MAP_BUILDS=off`: `learnloop hints maps build --vault
fixtures-local/h1-prob --dry-run --json` exited 0, 77 items selected, 77
builds due, 154 calls at worst with every re-ask, about 2,251,632 estimated
tokens (28,197-35,542 per build), `estimated_usd` null (the copy's route was
`manual`, so no billing or price). `state.sqlite`'s sha256 was the same before
and after. The copy was then deleted.

**Model calls made in this stage: 0** (tests use fakes; the one manual run was
the dry run above).

## 10. Gate (this step; the full suite, the whole durability lane and the whole vitest run are the landing gate's)

Run in the worktree with `TMPDIR=fixtures-local/tmp`; `/tmp/learnloop-fullsuite.lock` was free throughout (`flock -n`).

- `uv sync --extra dev --extra mobile` and `uv pip install pypdfium2`: ok.
- `uv run lint-imports --no-cache`: **26 kept, 0 broken** (25 on the base plus `graders-never-read-approach-maps`).
- Targeted pytest, `uv run pytest -n auto <116 files>`: **2464 passed** (433 s), after clearing the template `.pyc`. The files: every new or changed test file, every file naming the head fixture, every file that serves an item through `get_practice_item`, every `find_sources` caller's tests, the config-defaults-snapshot files, the routing and disclosure tests, and the contract tests (CLI help snapshot, serializer snapshot, desktop RPC contract, mobile allowlist, architecture, table roles, coordinated migrations, tracked fixture databases, SQLite file copies, config, instructional layering):
    `tests/test_approach_map_boundaries.py` `tests/test_approach_map_replay.py` `tests/test_approach_maps.py` `tests/test_approach_maps_schema.py` `tests/test_architecture.py` `tests/test_canonical_exercise_serialization.py` `tests/test_causal_p2_acceptance.py` `tests/test_chatgpt_plan_workspace.py` `tests/test_cli_generate_practice.py` `tests/test_cli_help_snapshot.py` `tests/test_config_refactor.py` `tests/test_coordinated_migrations.py` `tests/test_daily_loop_lo_lifecycle_serving.py` `tests/test_daily_loop_reference_adoption.py` `tests/test_daily_plan_composition.py` `tests/test_daily_plan_replay.py` `tests/test_daily_plan_rpc.py` `tests/test_decider_landing.py` `tests/test_desktop_rpc_contract.py` `tests/test_diagnosis_async_router.py` `tests/test_diagnosis_input_provenance.py` `tests/test_diagnosis_replay.py` `tests/test_exam_protection_identity.py` `tests/test_exam_protection.py` `tests/test_exam_protection_review.py` `tests/test_facet_identity_actions.py` `tests/test_facet_identity_ingest.py` `tests/test_facet_locks_landing.py` `tests/test_family_proposals.py` `tests/test_field_config.py` `tests/test_find_sources_intents.py` `tests/test_forecast_receipts_landing.py` `tests/test_forecast_receipts.py` `tests/test_graph_nomination_ingest.py` `tests/test_help_assists_schema.py` `tests/test_hint_telemetry.py` `tests/test_instructional_layering.py` `tests/test_judge_routes.py` `tests/test_learner_pick_proposal.py` `tests/test_learner_text_source_widening.py` `tests/test_library_ask_expand.py` `tests/test_library_ask.py` `tests/test_library_asks_migration.py` `tests/test_mcp_c1a_narrow.py` `tests/test_mcp_c1a_review.py` `tests/test_mcp_cli.py` `tests/test_mcp_tools.py` `tests/test_method_explicit_landing.py` `tests/test_method_explicit_upgrade.py` `tests/test_migrations.py` `tests/test_mobile_allowlist.py` `tests/test_model_call_receipt_owners.py` `tests/test_mvp010_upgrade.py` `tests/test_mvp011_upgrade.py` `tests/test_mvp013_upgrade.py` `tests/test_mvp014_upgrade.py` `tests/test_mvp015_upgrade.py` `tests/test_mvp016_upgrade.py` `tests/test_mvp017_route_check_replay.py` `tests/test_mvp017_upgrade.py` `tests/test_mvp018_upgrade.py` `tests/test_mvp020_upgrade.py` `tests/test_mvp021_upgrade.py` `tests/test_mvp022_upgrade.py` `tests/test_mvp023_upgrade.py` `tests/test_mvp024_upgrade.py` `tests/test_openai_embedding_client.py` `tests/test_output_budget.py` `tests/test_patch_compiler.py` `tests/test_pf_cli.py` `tests/test_pfc_unverified_unassessed.py` `tests/test_plan_determinism.py` `tests/test_prescription_passages.py` `tests/test_project_cli.py` `tests/test_provider_resolution_parity.py` `tests/test_reader_find_sources_callers.py` `tests/test_reader_intent.py` `tests/test_reader_workbench_rw2a.py` `tests/test_reading_step_switch.py` `tests/test_rebuild_orchestrator.py` `tests/test_recurrence_commands.py` `tests/test_recurrence_live.py` `tests/test_regrade_contract_successor.py` `tests/test_regrade_contract_upgrade.py` `tests/test_required_method_round3_review.py` `tests/test_reread_safety_landing.py` `tests/test_reread_safety.py` `tests/test_retrieval_interventions_write_points.py` `tests/test_router_g4_restraint.py` `tests/test_router_presentations.py` `tests/test_route_rules_in_grader.py` `tests/test_serve_eligibility_review.py` `tests/test_settings_sidecar.py` `tests/test_shadow_rebuild.py` `tests/test_sidecar_contract.py` `tests/test_sidecar_item_authoring.py` `tests/test_sidecar_item_presentation.py` `tests/test_sidecar_serializer_snapshot.py` `tests/test_sidecar_teach_back.py` `tests/test_sidecar_trace_and_clarification.py` `tests/test_sidecar_tutor_qa.py` `tests/test_source_block_fts.py` `tests/test_sources_merge_composition.py` `tests/test_sqlite_file_copies.py` `tests/test_stuck_prompt.py` `tests/test_stuck_prompt_replay.py` `tests/test_table_roles.py` `tests/test_tier1_decider.py` `tests/test_tool_dispatch_policy.py` `tests/test_tool_registry.py` `tests/test_tool_results_withhold_answers.py` `tests/test_tools_cli.py` `tests/test_tracked_fixture_databases.py` `tests/test_tutor_tool_requests.py` `tests/test_ux_phase4_feedback.py` `tests/test_ux_phase4_landing.py`
- Durability: `uv run pytest -m durability tests/test_approach_maps_schema.py tests/test_help_assists_schema.py tests/test_library_asks_migration.py tests/test_learner_text_source_widening.py tests/test_migrations.py tests/test_tracked_fixture_databases.py tests/test_daily_plan_replay.py`: **6 passed** (67 deselected); and `uv run pytest -n auto --durable-sqlite tests/test_approach_maps.py tests/test_approach_map_replay.py tests/test_approach_maps_schema.py tests/test_approach_map_boundaries.py`: **63 passed** (production pragmas and WAL for every H1 test).
- Frontend and Tauri: unchanged, so npm, vitest, `frontend:build` and `cargo check` were not run.
- References: `db_generate_reference.py` (head 211; new `Tables/approach_maps.md`; `Config - hints.md`; commit labels and line citations elsewhere) and `db_validate_reference.py`: **0 errors** (330 table notes, 886 leaves); `validate_vault.py`: passed (1125 notes).
- Snapshots: `tests/cli_help_snapshot.json` rewritten (`hints`, `hints maps`, `hints maps build`); the template `.pyc` cleared before the defaults snapshots were recomputed and again before the targeted run.

## 11. Commits

- `3c2b23fe6` the stage (migration 211, head fixture, store, `learnloop.hints` maps, seeds, builder and report, route and config, the serve hook, CLI, import contracts, snapshots, tests, spec §15, this record).
- `ee2f49530` the references regenerated on `3c2b23fe6` (commit labels only; `db_validate_reference` 0 errors; `validate_vault` passed).
- This record's commit list (docs only).

## Landing onto main

Landed in the `learnanything-merge2` worktree on branch `merge/h1-onto-main`. Main's tip was `cdcd70601` (the H0 landing), which is the stage's base. The stage tip is `a4ffbc2b1`, unchanged. Codex's last verify round (job `20261018-042510-u6Qvyi`) is clean, with one Low recorded (below). Main was neither fast-forwarded nor pushed here.

**Commits:**
- `d9f2d70b9`: a real `--no-ff` merge of `hints/h1` onto `cdcd70601`. Main had not moved, so the merged tree is exactly the stage tip (`git diff a4ffbc2b1 d9f2d70b9` is empty).
- `0c9aad82f`: the references regenerated on the merged tree.
- `d49d18ffc`: **the gate fix** (below): the parameter registry classifies `hints.maps.max_daily_cost_usd`.
- `ac37ec432`: the references regenerated after the fix (commit labels and `parameter_registry.py` line citations).
- This record.

### Merge

- **No conflicts.** Migration 211 was still free (main's head was 210). `fixtures/migration_head_211` is in rollback mode: header bytes 18-19 are 1/1, `journal_mode` is `delete`, its last `schema_migrations` row is 211 and there is no `-wal` or `-shm`. `fixtures/migration_head_210` is gone; only the 211 fixture's README names it, as history.
- **No algorithm successor.** The vaults' labels and the Pipeline Map's `implementation_version` are unchanged.

### Regenerated

- **References.** `db_generate_reference.py`, then `db_validate_reference.py`: **0 errors**, `schema_head` 211, 330 table notes, on the merge (`0c9aad82f`: 393 notes, commit labels plus line citations that the six fix rounds had moved, and the new test helper and test file in the source lists) and again after the gate fix (`ac37ec432`: 393 notes, labels and the registry's line citations). No content change.
- **Defaults snapshots.** Deleted the template `.pyc` and touched `template.py`: all 19 `DEFAULTS_SNAPSHOT_BY_ALGORITHM` entries equal `defaults_fingerprint_for_version`, **0 mismatches** (checked on the merge and again after the fix).
- **CLI help snapshot.** `python tests/test_cli_help_snapshot.py --write`: no change (it already holds `hints maps build`).
- **`validate_vault.py`**: passes (1,125 notes, 1,123/1,123 reachable).

### Gate

Python 3.12.14, `TMPDIR` set to merge2's `fixtures-local/tmp`, `uv run --no-sync` after the install. Both suite lanes ran under `flock /tmp/learnloop-fullsuite.lock`. No paid call was made: every test uses fakes. **This is the first full run over the stage's code**; every stage step and every review round had run targeted tests only (owner rule 2026-10-17).

| Check | Result |
|---|---|
| `uv sync --extra dev --extra mobile` + `uv pip install pypdfium2` | ok (pypdfium2 5.14.0) |
| `lint-imports --no-cache` | **26 kept**, 0 broken (H0's 25 plus `graders-never-read-approach-maps`), on the merge and on the final tree |
| full suite, first run on `0c9aad82f` | **8 failed**, 13,376 passed, 2 xfailed (17 min 48 s; `fixtures-local/h1-landing-fullsuite.log`). One cause, real and in stage code: `hints.maps.max_daily_cost_usd` was not classified in the parameter registry (`AuditReport.unclassified_config = ['hints.maps.max_daily_cost_usd']`): `test_registry_audit.py` ×5, `test_grading_cli.py` ×2 (the registry audit and release-check CLIs), `test_p0_cutover_mvp08.py::test_mvp06_derived_output_is_byte_identical_across_p0_machinery` (it asserts the audit is clean). No stage test or targeted file had covered the registry audit |
| the fix (`d49d18ffc`) | one `_ConfigRule` in `params/parameter_registry.py`: `hints.maps.max_daily_cost_usd` is `structural` / `operational` (a money bound, no measurement authority), exactly as RW4a's `library_ask.max_daily_cost_usd`. The 8 tests failed on `0c9aad82f` when run alone (8 failed, 29 passed over the three files) and pass with the fix (37 passed). `hints.price_per_million` needed no rule (the audit did not list it). No schema, snapshot or serving change |
| full suite on `ac37ec432` (the final code tree) | **13,384 passed, 2 xfailed**, 0 failed (20 min 57 s; `fixtures-local/h1-landing-fullsuite2.log`). H0's landing ran 13,213; the +171 are H1's tests |
| `pytest -m durability` | **111 passed**, 13,275 deselected (2 min 2 s); H0's was 109, plus H1's two (`test_211_on_the_durability_lane`, the two-OS-process F3 claim test) |
| `npm install`, `npm run typecheck` | ok, clean |
| `npm test` (vitest) | first run: 1 failed, 1,000 passed (`FeedbackScreen.test.tsx` > "keeps the old Next where no live queue applies": a spy called 0 times). `apps/` is identical to main's, so this cannot be H1's: the file alone passed 3 times out of 3 (11/11), and the whole run again passed: **124 files, 1,001 tests** (`fixtures-local/h1-landing-vitest2.log`). A load-timing flake, recorded as such |
| `npm run frontend:build` | built (the usual chunk-size warning) |
| `cargo check` | not run: `git diff main -- apps` is empty (H1 does not touch `src-tauri`) |
| the H1 thread, lease and lifecycle tests | all passed in both full runs and the durability lane; nothing timing-looking failed, so no reruns were needed. The known `"8841"` flake in `test_mcp_c1a_review.py` did not fire |
| tracked fixtures | `git status` clean after both lanes and the frontend run |

### Parity (backup-API copies; no model call)

**Setup:**
- **Copies.** The owner's `fixtures/linear_algebra` and `fixtures/probability` (with probability's `.learnloop/state.sqlite`) were copied with `copy_tree_with_databases` from the main checkout into `fixtures-local/landing-h1/orig/`. Each original was read once. Every other copy came from `orig/` through the same helper. `arxiv_v2` was not opened. No copy holds a `.env`.
- **Code.** Main's code is `git archive cdcd70601` and the merge's is `git archive ac37ec432` (the final tree; a first pass on `0c9aad82f` gave the same results and is kept under `landing-h1/`, the tables below are the final pass under `landing-h1/r2/`), each containing only `src`, `migrations` and `pyproject.toml`, each put first on `sys.path`; every run printed the `learnloop` package it imported.
- **Environment.** Every run went through `env -i` with only `PATH`, `HOME`, `CODEX_HOME`, `LEARNLOOP_CONFIG_DIR`, `TMPDIR` and `LANG`: `HOME`, `CODEX_HOME` and `LEARNLOOP_CONFIG_DIR` were empty directories, so no `*_API_KEY`, `OPENROUTER*`, `OPENAI*`, `ANTHROPIC*` or `LEARNLOOP_AI_PROVIDER` variable, Codex login, ChatGPT-plan token or `settings.env` was reachable; every process started in a directory with no `.env`.
- **Model routes, before anything ran.** Every copy's `learnloop.toml` was rewritten first: `ai.active_provider` and every chat route went to a `blackhole` `openai_chat` profile at `http://127.0.0.1:9/v1` with an unset key variable (on the merge's copies `ai.routing.approach_map = "blackhole"` explicitly; on main's code the route does not exist), the fallback provider cleared, `[source_retrieval]` `query_rewrite`, `tutor_query_rewrite`, `tutor_rerank` and `dense` false, `[embedding]` `enabled`, `backfill_enabled` and `backfill_sources_on_extract` false. A resolver check over every `AITask` (51 on the merge, 50 on main) printed `blackhole` for every chat route including `approach_map`; the only others were the decider-only routes (code-default `openrouter_decider`) and `embedding` (disabled), all needing `OPENROUTER_API_KEY`, which no run had. `[hints.maps] build_on_serve = false` on every merge copy for (a)-(c).
- **Starting state.** Both vaults at schema 165, label `mvp-0.8`, **0** `model_call_receipts`.

| Check | linear_algebra | probability |
|---|---|---|
| **(a)** open (migrate), main's code / the merge's | 165 → 210 (45) / 165 → 211 (46) | 165 → 210 (45) / 165 → 211 (46) |
| schema objects, main vs merge | the only difference is the merge's `approach_maps` table, its two indexes (`idx_approach_maps_item`, `idx_approach_maps_family`) and two triggers (`approach_maps_no_update`, `approach_maps_no_delete`); every other table, index and trigger has identical SQL | same |
| rows of every table (334), on main's columns | **identical** (16,536 rows); `schema_migrations` differs only by the 211 row; `approach_maps` and `help_assists` empty | **identical** (7,634 rows); same |
| `rebuild --shadow --json`, main vs merge | **0 differences** (facet 0, mastery 2, schedule 8; live database unchanged on both) | **0 differences** (facet 0, mastery 1, schedule 1) |
| `doctor --json`, main vs merge | **0 differences** (57 issues, 1 error) | **0 differences** (101 issues, 48 errors) |
| **(b)** upgrade shadow: main's code migrates to 210, then the merge's code applies **211 only** | applied 1, head 211; `foreign_key_check` empty, `integrity_check` ok; all 334 tables' rows identical to the 210 copy; schema differs only by `approach_maps` and its indexes and triggers | same |
| `rebuild --shadow` and `doctor`: main's code on the 210 copy vs the merge's code on the upgraded copy | **0 differences** each | **0 differences** each |
| **(c)** at `mvp-0.8` (H0's method: every facet's `facet_evidence_timelines` with the eleven `TimelinePoint` fields, 40 single-facet curves, every LO's `recipe_gaps` and `lo_certification`) | **byte-identical JSON** (39 facets, 84 points, 2 corrections; 21 LOs, 23 recipes, 1 certified) | **byte-identical** (29 facets, 2 points; 18 LOs, 0 certified) |
| the Today queue: `build_due_queue` at a frozen clock (2026-10-18 09:00 UTC), `persist_explanations=False`, no session / a session / a greedy session | **byte-identical** (41 items each; head `pi_what_makes_function_axiom_strategy`) | **byte-identical** (67 items; head `pi_exercise_01kyn2kdf7h2kba1fp7wv7t3w5`) |
| the same on copies upgraded by main's code to `mvp-0.27` (`upgrade --to mvp-0.9`, `--to mvp-0.27`, `rebuild-derived-state` twice), then opened by each code (the merge's applies 211) | **byte-identical** certification and curves (82 points, 7 corrections, 1 LO certified) and Today queue (43 items), the same bytes as at H0 | **byte-identical** (29 facets, 2 points; 0 certified; Today queue 67 items) |

**(d) Practice through the real sidecar** (stdio: `initialize`, then the RPCs, then `shutdown`). Copies of probability at each code's head, on `pi_prob_derive_complement`, H0's sequence: `set_grading_provider manual`, `start_session`, `get_practice_item` (with the session: the serve that schedules a build), `get_probe_contract`, `practice.record_hint_reveal` (hint 0, submission key `landing-h1-k1`), `save_practice_draft`, `submit_attempt` (self-grade), `acknowledge_practice_submission`, `get_session`, `shutdown` (timed, then the process exit). Runs: (i) main's code; (ii) the merge with `[hints.maps] enabled = false` (`build_on_serve = true`); (iii) the merge with `enabled = true`, `build_on_serve = true`, the route at `127.0.0.1:9` with its key variable unset and no Codex login. Two extra runs of (iii) took the build further than the brief asks, still with no model anywhere: (iii-b) a dummy value in the key variable and `hints.price_per_million = 1.0`, so the build reached the transport and met a refused connection on port 9 (no listener: checked with `ss`); (iii-c) the same against a local socket this landing started on `127.0.0.1:18769` that accepts and never answers (it logged byte counts only, and was stopped after the run), so a build was still in its provider call at `shutdown`.

| Check | Result |
|---|---|
| every practice response, (i) vs (ii) and (i) vs (iii) | **identical** for all eleven calls: `set_grading_provider`, `get_probe_contract`, `save_practice_draft`, `acknowledge_practice_submission` and `shutdown` byte for byte; `initialize`, `start_session`, `get_practice_item` (11,559 bytes), `practice.record_hint_reveal`, `submit_attempt` (7,825 bytes) and `get_session` after normalizing only (1) ULIDs, including the `ha_` assist id (session, attempt, receipt and assist ids), (2) ISO timestamps, (3) the copy's own path in `initialize`'s `vault.root`, (4) `initialize`'s two schema-head fields, `health.database.latestMigration` and `migrationsApplied` (210/197 on main, 211/198 on the merge). In the database comparison, also `attempt_debug_payloads`' `dr_<hex>` id. Nothing else was normalized. (iii-b) and (iii-c) are identical too except `initialize`'s `health.ai` (`ready: true`, because their key variable holds a dummy value; not H1) |
| the database, (ii) vs (i) | the rows the run added or replaced (24 tables: the attempt, evidence, FSRS state, measurement events, the submission receipt, the `help_assists` row, ...) are **identical** after the normalization above. (ii) started no build (the switch returns before any thread) and wrote **nothing** H1-related: no `approach_maps`, `judgment_work_claims`, `judgment_ledger`, `model_call_receipts` or spend row |
| (iii): a build attempted in the background, failing closed | the sidecar log: `approach map on serve: {"status": "unavailable", "reason": "Environment variable LL_LANDING_NO_KEY is required.", "billing": "metered", "rounds": 0, "trigger": "serve"}`. The database differs from (i) by **one row only**: the durable claim `judgment_work_claims('approach_map_build:pi_prob_derive_complement')`, state `released`. No `approach_maps` row, no receipt, no ledger verdict, no spend row. `get_practice_item` took 0.21 s (0.17 s on main's code); `shutdown` answered at once (0.000 s) and the process exited at 0.32 s |
| (iii-b): refused connection | one admitted request (`APIConnectionError`), then `shutdown` fenced the build: status `stale`, "nothing more was paid for or stored". Rows: `model_call_receipts` 1 `failed` (its `chat_request` child) and 1 `started` whose finish was fenced and logged ("receipt (finish) not written"), **none succeeded**; the claim left `leased` (a fenced release by design, fix round 4 U3; it lapses on its own); one `source_service_spend` reservation settled at its estimate, $0.025; no `approach_maps` row, no ledger verdict. `shutdown` 0.15 s, exit 0.61 s |
| (iii-c): a provider that hangs | `get_practice_item` 0.25 s while the build's request sat on the socket (9,156 bytes sent, never answered): **the serve did not wait**. `shutdown` answered at **3.0 s**, the drain bound (`DRAIN_SECONDS`), and the process exited at 3.47 s (the daemon thread ended with it). The build was cancelled, not drained to completion: rows are 2 `started` receipts, a `leased` claim, one `in_flight` reservation ($0.025), and nothing else; no map, no verdict |
| `learnloop hints maps build --dry-run --json --limit 5` | exit 0, "Dry run: nothing was retrieved, called or written."; the copy's tree hash and `state.sqlite` sha256 identical before and after. It planned **77** items (see the new finding on `--limit`), 154 calls at worst, 2,298,405 estimated tokens (28,818-36,163 per build), `estimated_usd` null (the copy's route is metered and unpriced: "a metered route needs hints.price_per_million; this item would be skipped") |
| `learnloop hints report --json` | exit 0 on (iii), (iii-b) and (iii-c); each copy's tree hash unchanged. The `maps` section: `enabled`, `build_on_serve`, 0 versions stored, 0 current maps, served items 2 (both without a map), no validation verdicts; (iii-b) shows `model_calls.calls` 1 and `spend_today.metered_usd` 0.025377 of the $0.50 cap |

**`model_call_receipts` across the parity copies:** 0 on every copy of (a), (b), (c), (i), (ii), (iii), the dry-run copy and the `mvp-0.27` copies; only (iii-b) and (iii-c), the two runs built to reach a transport, hold receipts (none finished successfully; their endpoint was `127.0.0.1`). **`approach_maps` is empty on every copy.** The first pass's copies (`landing-h1/d/iiib`, `d/iiic`) are the same in kind: three admitted requests before the fence in `d/iiib`.

### For the owner

- **No upgrade command.** H1 has no successor; the vaults keep their label.
- **Migration 211 applies on the next open** (the desktop app, the CLI, the MCP runtime or the mobile host, whichever opens the vault first). It adds the empty `approach_maps` table, two indexes and two triggers (no update, no delete). **Close the app, the MCP runtime and the mobile host, and back up first**, as for any migration.
- **THE OWNER DECISION: build on serve is ON by default.** Once this lands, every newly served item revision (the practice screen's serve, with a session) starts **one background map call** on `ai.routing.approach_map`, which, unset, follows `ai.active_provider`: on your vaults that is **Codex**, billed `estimated_only`, so the `$0.50` `hints.maps.max_daily_cost_usd` cap (metered routes only) **does not bound it**. The implement-time dry run counted 77 items in the probability vault, up to about **2.25 M tokens** for one map each (this landing's dry run on a copy: 2.30 M, 28.8-36.2 k per build, an upper bound). The serve never waits on the build (checked above). A revision whose build was not stored is not retried by the serve. To change it, in the vault's `learnloop.toml`:

  ```toml
  [hints.maps]
  build_on_serve = false   # no background builds; the CLI still builds
  # enabled = false        # the kill switch: nothing built, nothing read

  [ai.routing]
  approach_map = "codex_low"   # or any profile; a metered one also needs [hints] price_per_million
  ```

  Backfill when you choose, dry run first:

  ```bash
  uv run learnloop hints maps build --vault <path> --dry-run --json     # plans only: retrieves, calls and writes nothing
  uv run learnloop hints maps build --vault <path> [--item ID | --family ID | --lo ID] [--limit N] --json
  ```

- **Reading the report.** `uv run learnloop hints report --vault <path> --json` (read-only) has a `maps` section: whether `enabled` and `build_on_serve` are on, the cap and price; `versions_stored` and `versions_by_trigger` (serve, inline, cli, merge: what build-on-serve has cost you in builds); `current_maps` and `items_with_a_map`; `served_items` (active items with at least one attempt, with and without a current map); `validation` (verdicts, failures by reason, builds not stored); `routes_by_origin` and `routes_per_current_map` (reference, trace-contract recipe, source, learner routes); `verified_goal` (maps whose goal matched the exact answer key; unverified is common and fine for quantity answers); `model_calls` (calls and tokens on the map receipts); `spend_today` (metered dollars against the cap, and the `estimated_only` Codex/ChatGPT-plan requests and tokens, never counted against it).
- **The recorded Lows** (none blocks):
  - the last Codex verify (job `20261018-042510-u6Qvyi`, clean): **the case-folded public-given exemption**: the C2 exemption (a label may name what the question states) compares through the case-folding answer check, so a question stating `X` can exempt a label stating `x`;
  - round 6, Codex item 3: prose leak detection still marks a false leak for a denominator in nested or square brackets ("x / ((4))", "x / [4]") or a spaced exponent ("m ^ 4");
  - round 3: prose that needs algebraic rewriting ("x times x" for `x^2`) is not detected; prose detection is best effort, and H2's text gate (spec §4.6) is the binding one;
  - round 5: monomials and quantities verify less often (`x*2` against `2x`, unit spellings): unverified, never rejected;
  - round 2: a fenced call's finish receipt and checkpoint are dropped (logged), while its spend reservation still settles.
- **Doc only:** the comment in `migrations/211_approach_maps.sql` describing what `structure_hash` covers omits the resolved rubric (added in review F5). The code and the stage record are right; the comment was left so the head fixture need not be rebuilt.
- **New at landing:**
  - **The gate fix** above (the registry classification). Small, no behaviour change; the stage's targeted files had not included the registry audit.
  - **`--dry-run` ignores `--limit`** (Low, not fixed here): `hints maps build --dry-run --limit 5` plans and estimates all 77 items, while the real run with `--limit 5` builds at most 5 (`backfill` applies the limit only on the real branch). Read a dry run's totals as "every item without a map". A one-line fix plus a test for the orchestrator to schedule.
  - **A failed metered request is charged its estimate in the maps envelope** (observation; shared spend-ledger behaviour, `_reported_usd` keeps the reservation when the provider reports nothing): in (iii-b) a refused connection still counted $0.025 against the $0.50 cap. Conservative and irrelevant on Codex; on a metered route, repeated transport failures eat the day's cap.
  - **A closed vault leaves the build's claim `leased`** until it lapses (2 minutes) when shutdown fences its release (by design, U3), and a build still in its provider call at shutdown is cut off at the 3 s bound, not finished (iii-c), leaving `started` receipts and an `in_flight` reservation, which the ledger's recovery resolves. Nothing is logged when the drain bound expires with a build still running; worth a log line later.
  - **The fenced-build reason string repeats itself** ("nothing more is paid for; nothing more was paid for or stored"; cosmetic).
  - **Not exercised here:** a real model build (no live call by rule), and a vault switch over the sidecar (covered by `test_m4_*`).
- **Open questions (defaults taken):** stage record §7: 1, build on serve (above, the owner's decision); 2, no rebuild on new seeds (a map is current for its item revision and item-side seeds); 3, `hints.price_per_million` unset (a metered map route is refused until priced); 4, one envelope for maps and merges; 5, a failed revision on serve is not retried; 6, no Settings exposure of `[hints.maps]`.

# Refactor K2.7: a job type is one row

Branch `refactor/k2.7-job-type-rows`, base `ba7884c102` (migration head 266, latest tag mvp-0.68).
Implements K2.7 of `k2-ingestion-strategy-2026-11-11.md` (findings KP2, KB6, KP6; the boundary row
"pipeline → retrieval"). Moves only, plus one table. No behaviour, prompt, config, schema, persisted-meaning or
identity change, and no model call.

## Judgment calls to read first

1. **The table has a fifth flag, `waits_for_ai_ok`.** The strategy (written Nov 11) names four lists beside
   `KNOWN_JOB_TYPES`. A fifth list that says what a type is, `WAITS_FOR_AI_OK_JOB_TYPES` in `runner.py`, landed
   after it. Leaving it would keep two places per type, so it became a column. The characterization pins it like
   the other four.
2. **No client factory was removed.** The strategy says "client factories where a route name serves". Each
   `RunnerServices` factory is the injection seam the tests and the sidecar's fakes use (about 40 test files),
   and each default differs from a bare route lookup in more than its route name: the inventory resolver's
   low-effort pin and error words, shared by three clients on `canonical_ingest`; the promotion pair's retryable
   wrapping; the video route read directly, so no fallback chain can redirect a billable video; the synthesis
   timeout. Only the rung-variant and animation defaults are pure route lookups, and replacing those two would
   move their seam in tests that patch module globals (`test_sidecar_animation`) for one line saved each. What
   the route name does do now: each row names its `client_routes`, and a test proves the row against the route
   each default client actually resolves (`test_a_rows_routes_are_the_routes_its_default_clients_resolve`).
3. **No import-linter contract.** The strategy names none, and `learnloop.content` is an implicit namespace
   package that grimp does not traverse, so a contract on `content.pipeline` would check nothing (the same reason
   `test_instructional_layering.py` and `test_e0_isolation.py` exist). The boundary is held by an AST test
   instead: the host imports only the four retrieval modules its index sweeps need (eight before), and the table
   imports none (it names retrieval's handlers in `source_retrieval.jobs`). `lint-imports` is unchanged and passes (52 kept).
4. **Where the figure and video handlers went.** K10 moved none: K10.3 changed `handle_figure_rich` in place in
   `jobs.py` (it opens its own trace scope and continues the press's trace), and the K10 strategy names no home
   ("before K2.7 moves the job handlers out of `jobs.py`, or after it in its new home"). Beside their features:
   `handle_figure_rich` to `figures/jobs.py` (its service is `figures/rich.py`), `handle_concept_animation` with
   its two clients to `content/authoring/jobs.py` (its service is `content/authoring/concept_animation.py`).
5. **What stays on the host.** `_queue_due_replay` (the nightly teacher replay) stays in `jobs.py`: it takes the
   host, starts its worker, and is called only from the host's deferred-index sweep, which the strategy keeps on
   the host ("retrieval's derived indexes stay on the job host; only handlers and rows move"). The obligations a
   completed extraction queues (`queue_source_vectors`, `queue_contextual_indexes`, `queue_coverage_on_extract`)
   are retrieval's and moved with its handlers; the import handlers call them there. `_LEGACY_JOB_TYPES` (the
   host's legacy-lane listing) and `_BUILD_WORKFLOWS` (workflow names, not job types) stay as they were.
6. **Three private names cross a module line.** Each had one definition and readers on both sides of a cut:
   `_optional_int` (import_jobs, read by `handle_inventory`), `_routed_task_client` (synthesis jobs, read by the
   authoring clients), `_reader_source_sets` (authoring jobs, read by the host's Reader enqueues). They are
   imported where read rather than copied or renamed, so every body stays byte-identical.
7. **The table names its handlers; the job contracts are a leaf; the cycle ratchet rises by 2.** Each row's
   `handler` is a `module:function` string that `resolve_handler` imports when the runner builds its default
   handlers (the runner, not only the host, resolves them: the CLI and the tests construct `IngestRunner` directly
   and rely on the defaults). `job_types.py` imports no LearnLoop module at run time (`Handler` only under
   `TYPE_CHECKING`), so the sidecar's reload checks and the runner's flag reads take a row's facts without loading
   any feature job module (a subprocess test checks it).
   The contracts a job module needs (`IngestRunnerError`, `JobCancelled`, `WaitingForInput`, `JobSpec`,
   `FetchedBytes`) moved from the runner to the leaf `content/pipeline/job_contracts.py`, bodies unchanged; the
   runner re-exports them, so every existing import keeps working and the classes are one set of objects (an
   identity test checks the runner's, the leaf's and every job module's names). The five job modules import the
   leaf, and `JobContext`, which they use only in annotations, under `TYPE_CHECKING`, so none imports the runner at
   run time. The runner loads the three job modules its services fall back on by module path
   (`runner._job_module`), as the table names its handlers.
   Measured `modules_in_an_import_cycle`: 226 with handlers imported into the table, 224 with handler names, 223
   with the contracts leaf (`source_retrieval/jobs.py` leaves), and 223 still with the defaults loaded by name;
   221 at the base. Set by hand with its reason beside it. What still closes the cycle (ledger K2-22) is no longer
   the runner but two back-imports from the pipeline into job modules: `add_source → authoring.jobs`
   (`start_waiting_sections`, function-local) while `authoring.jobs → add_source`, `synthesis.jobs → add_source`
   and `authoring.jobs → synthesis.jobs`; and `reread → import_jobs` (`_pdf_page_count`, function-local) while
   `import_jobs → reread`. With those two edges removed the measure gives 219 (simulated); that needs two more pure
   moves (`start_waiting_sections` and `practice_expansion_payload` into `add_source`, `_pdf_page_count` into
   `reread`), which this step stops short of. Loading the defaults by name changes the number only together with
   those moves: with the runner importing the job modules function-locally, the same cut still leaves 223. The only
   other members edited: `jobs.py`'s stage-comment count (32 → 13) and `handle_inventory`'s over-200 line, which
   names its new module. The new modules' stage-comment counts (import_jobs 9, authoring jobs 11) are not added
   to `[stage_comments_by_file]`; the ratchet's total fell (2,351 → 2,346).

## What moved where

`content/pipeline/jobs.py`: 6,195 → 2,106 lines (the strategy's target: "the host, under about 2,500"). 134
top-level definitions moved; three were deleted (`DEFAULT_HANDLERS`, `APPLYING_JOB_TYPES`,
`_PARALLEL_JOB_TYPES`); 23 remain.

| new module | lines | definitions | what |
|---|---|---|---|
| `content/pipeline/import_jobs.py` | 1,675 | 63 | `import`, `auto_study_map`, `legacy_ingest`/`exam_ingest`, `extraction_repair`; the acquisition and extraction defaults (fetch, extract, extraction identity, GLM-OCR consent, native media and audio routes, legacy one-shot) |
| `content/synthesis/jobs.py` | 845 | 22 | `inventory`, `bootstrap_synthesis`, `append_synthesis`; the inventory and synthesis clients, the parallel inventory mailbox |
| `content/authoring/jobs.py` | 1,237 | 38 | Reader quick checks (section, inquiry, selection), Reader and source exercise imports, practice expansion with AD commissions, goal population, question promotion, rung variants, concept animations; their clients |
| `figures/jobs.py` | 46 | 1 | `figure_rich` |
| `source_retrieval/jobs.py` | 318 | 10 | `source_embedding_backfill`, `local_source_index`, `source_fallback_backfill`, `curriculum_coverage_on_extract`; the three obligation queuers |
| `content/pipeline/job_types.py` | 126 | new | the table |

Other source edits: `runner.py` (1,509 → 1,480: the five lists out; lazy loaders `_job_types`, `_import_jobs`,
`_synthesis_jobs`, `_authoring_jobs` replace `_job_defaults`; the two flag reads use the row), the sidecar's
`handlers/queue.py` and `handlers/ingest.py` (read `applying_job_types()`), `add_source.py` and `reread.py` (one
function-local import each repointed), and two comments naming the old module (`ingest/source_kinds.py`,
`ingest/extractors/__init__.py`). The vault's hand-written `Architecture/Content Pipeline.md` gains a "Job types"
section and its modification guidance names the row; the generated references are left to the landing.

## The table

`JOB_TYPES` in `content/pipeline/job_types.py`, one frozen `JobType` per type, in the old `DEFAULT_HANDLERS`
order; `handler` is the function's `module:function` (judgment call 7). Readers: `default_handlers()` (the runner,
through `resolve_handler`), `job_type(name)` (the runner's two flag reads),
`applying_job_types()` (the host's bind and the sidecar's two reload checks), `parallel_job_types()` (the host's
lanes).

| type | handler | applies_vault | affects_queue | parallel | waits_for_ai_ok | client_routes |
|---|---|---|---|---|---|---|
| import | handle_import | | | | | |
| auto_study_map | handle_auto_study_map | | | | | |
| legacy_ingest | handle_legacy_ingest | yes | | | yes | canonical_ingest |
| exam_ingest | handle_legacy_ingest | yes | | | yes | canonical_ingest |
| inventory | handle_inventory | | | | yes | canonical_ingest |
| bootstrap_synthesis | handle_bootstrap_synthesis | yes | | | yes | canonical_ingest |
| append_synthesis | handle_append_synthesis | yes | | | yes | canonical_ingest |
| extraction_repair | handle_extraction_repair | | | | | |
| reader_quick_check | handle_reader_quick_check | | | yes | yes | canonical_ingest |
| reader_exercise_import | handle_reader_exercise_import | yes | yes | | yes | canonical_ingest |
| source_exercise_import | handle_source_exercise_import | yes | | | yes | canonical_ingest |
| practice_expansion | handle_practice_expansion | yes | yes | | yes | canonical_ingest |
| goal_population | handle_goal_population | yes | yes | | yes | canonical_ingest |
| question_promotion | handle_question_promotion | yes | yes | | yes | tutor_qa, authoring |
| rung_variant | handle_rung_variant | yes | yes | | yes | rung_variant |
| concept_animation | handle_concept_animation | | | | yes | animation, video_generation |
| figure_rich | handle_figure_rich | | | | yes | |
| source_embedding_backfill | handle_source_embedding_backfill | | | | yes | |
| curriculum_coverage_on_extract | handle_curriculum_coverage_on_extract | | | | | |
| local_source_index | handle_local_source_index | | | | | |
| source_fallback_backfill | handle_source_fallback_backfill | | | | | |

`client_routes` is empty where the handler asks the services for no model client (the import's extraction, the
rich figure and the embedding backfill resolve their own routes inside their features).

Deleted: `DEFAULT_HANDLERS`, `APPLYING_JOB_TYPES`, `_PARALLEL_JOB_TYPES` (`jobs.py`); `_QUEUE_AFFECTING_JOB_TYPES`,
`WAITS_FOR_AI_OK_JOB_TYPES`, `KNOWN_JOB_TYPES`, `KNOWN_WORKFLOW_TYPES` (`runner.py`).

## The characterization, written first

`tests/test_job_types.py` landed alone in the first commit (`07ff6e79fd`), before any source moved. Its
`EXPECTED` literal pins, for each of the 21 types, the handler's name and its membership in `APPLYING_JOB_TYPES`,
`_QUEUE_AFFECTING_JOB_TYPES`, `_PARALLEL_JOB_TYPES` and `WAITS_FOR_AI_OK_JOB_TYPES`, read from the lists
themselves (5 passed at that commit, with a check that no list names a type without a handler). The table commit
changed only the read side (`_observed()` reads the rows); `EXPECTED` is byte-identical, so the table equals the
old lists. Added beside it:
- every type has exactly one row, and every row's handler reference resolves to a callable of that module and
  name; the runner's default handlers are the table; reading the table loads no feature job module;
- every job type the source tree enqueues through `JobSpec` (a literal, or a constant resolved through the
  module's imports; 19 found, the one dynamic site is the legacy lane's `legacy_ingest`/`exam_ingest`) has a row:
  a new type queued without a row fails here (P-fail);
- each row's `client_routes` are routing tasks, and are the routes its default clients resolve (11 types through
  the services' client methods with the route lookup recorded, the legacy lane through its one-shot default);
- the pipeline's reach into retrieval (judgment call 3).

`tests/test_coverage_on_extract.py::test_the_handler_is_registered_and_known` read `DEFAULT_HANDLERS` and
`KNOWN_JOB_TYPES`; it now asserts the row's handler is retrieval's handler. The `KNOWN_JOB_TYPES` assertion is
gone with the list; the row is what "known" means now.

## Proofs

**P1, AST identity** (scratch `ast_move_check.py`: `ast.dump(..., include_attributes=False)` of each definition at
the base commit against its new home, plus each definition's source text with its leading comments found verbatim
there):

```
P1 learnloop.content.pipeline.import_jobs: 63/63 AST-identical and verbatim
P1 learnloop.content.synthesis.jobs: 22/22 AST-identical and verbatim
P1 learnloop.content.authoring.jobs: 38/38 AST-identical and verbatim
P1 learnloop.figures.jobs: 1/1 AST-identical and verbatim
P1 learnloop.source_retrieval.jobs: 10/10 AST-identical and verbatim
host: lost 137 definitions (134 moved, deleted: ['APPLYING_JOB_TYPES', 'DEFAULT_HANDLERS', '_PARALLEL_JOB_TYPES']); 23 remain, AST-different from base: ['DurableIngestJobs']
TOTAL: 134 AST-identical moves, 0 failures
```

At the move commit (`8a48af21c7`) the host's remaining definitions were all AST-identical to the base. At the tip
the one difference is `DurableIngestJobs`: its seven reads of `APPLYING_JOB_TYPES` / `_PARALLEL_JOB_TYPES` became
calls of `applying_job_types()` / `parallel_job_types()`, which return the same names (the characterization).

**P2, name resolution** (scratch `resolve_names.py`, the base table captured before any edit): for all 131
top-level functions and classes, every global name a body reads resolves at the tip to the same object as at the
base (sets compared as sets; a moved definition's own module mapped back). 0 differences at the move commit; at
the tip the only two are `DurableIngestJobs`'s reads of the deleted `APPLYING_JOB_TYPES` and
`_PARALLEL_JOB_TYPES`, which it now gets from the table's functions (P1). After the contracts leaf, the moved
bodies' reads of the five contracts resolve to the same classes, now defined in `job_contracts` (the runner's
names are those objects), and their `JobContext` names are annotations only (imported under `TYPE_CHECKING`; no
moved body reads it at run time, checked by an AST scan); nothing else differs. As designed,
`__name__` follows the new module in seven moved bodies that log through `logging.getLogger(__name__)`
(`_record_commission_skip`, `_record_reader_import_keys`, `_record_step`, `_verify_quietly`, `handle_import`,
`queue_coverage_on_extract`, `start_waiting_sections`); nothing in `src/`, `tests/` or `scripts/` selects a logger
or compares a `__module__` by the old name.

**P3, patches.** Every patch whose target was `content/pipeline/jobs.py` named a moved definition; each now
targets the module whose function reads the name (each is a repoint, listed): `default_synthesis_client`
(`test_ad23_fix_review`, `test_ad23_owner_decisions` ×2: the runner reads it from `content.synthesis.jobs` at call
time), `_MAX_INVENTORY_WORKERS` and `_RunnerMailbox.answer_pending` (`test_ingestion_checkpoints`,
`test_inventory_runner_mailbox`), `_extract_audio` and `_guard_file_upload` (`test_keep_local_retired`,
`test_ux_phase1_review_fixes`), `_refuse_held_out_reader_material` (`test_reader_active_reading`),
`_passage_check_spend`, `_pause_while_inquiry_held` and `INQUIRY_HELD_MAX_POLLS` (`test_reader_passage_check`),
`default_animation_client` and `default_video_client` (`test_sidecar_animation`). The patch of the host's own
`_iso` (`test_reading_request_sweep`) is unchanged. Nine more test files called a Reader or exercise-import
handler through the host (`jobs.handle_reader_exercise_import`, `jobs.handle_reader_quick_check`,
`jobs.handle_source_exercise_import`), which reached them only while the host imported them for
`DEFAULT_HANDLERS`; they now import `content.authoring.jobs` (`protection_matrix_helpers`,
`test_curriculum_c3_codex_review`, `test_exam_protection`, `test_exam_protection_review`,
`test_import_split_parity`, `test_library_exercises`, `test_protection_surface_matrix`,
`test_reading_hardening_landing`, `test_source_exercise_rpcs`). No assertion was changed in any of these.

**P4.** `tests/test_identity_pins.py` passes unchanged after each source commit (no `--write`).

**P6, stale references** (scratch `stale_scan.py`: AST scan of `src/`, `tests/`, `scripts/` and the vault
scripts for a from-import, an alias attribute, a `setattr`/`patch.object` string or a dotted string naming a name
the host no longer has): none left apart from four local variables that happen to be called `jobs`.

## Findings

- **K2-20** (ledger, queued, before arc K closes): three types that write scheduler-visible practice do not bump
  the queue revision when they complete: `source_exercise_import`, while its sibling `reader_exercise_import`
  does, and `legacy_ingest` / `exam_ingest`, whose proposals auto-apply items. The removed list's own comment
  ("these jobs can add or replace scheduler-visible practice") covered them, but it named neither, and their
  batches are not build workflows. A Today poll still reloads after them (`get_queue_revision` reloads after any
  applying job and answers `reloaded`). Kept as it ran: the rows say `affects_queue=False`.
- **K2-22** (ledger, queued, before arc K closes): three job modules sit in the add-source planner's import cycle
  through two back-imports (judgment call 7, with the chains and the measured fix).
- **K2-21** (ledger, fixed here): `KNOWN_JOB_TYPES` named `extract`, which no handler runs, and missed ten of
  the 21 types; `KNOWN_WORKFLOW_TYPES` was read by nothing. Only one test read the first, so nothing ran
  differently. Both are deleted.
- No other type's lists disagreed with how it ran. `bootstrap_synthesis` and `append_synthesis` apply vault
  content without `affects_queue`, but their batches' end bumps the revision through `_BUILD_WORKFLOWS`;
  `figure_rich` and `concept_animation` write their own rows, not vault content.

## Commands and results

All through the scratch wrapper (isolated home, config and temp dir), tests memory-capped at 3 GB with
`-n 1`, one command at a time.

| command | result |
|---|---|
| characterization at its own commit, `tests/test_job_types.py` | 5 passed |
| affected tests: `scripts/affected_tests.py --files <the 14 changed src files>` listed 816 files; name filter: the test files among them (or among all tests) that mention a changed or moved module or name (`pipeline.jobs`, `import_jobs`, `job_types`, the four new `jobs` modules, `pipeline.runner`, `RunnerServices`, `DurableIngestJobs`, `IngestJobManager`, `queue_revision`, `_pdf_page_count`, `start_waiting_sections`, `source_kinds`), plus the test files importing a helper that does: 165 files, 5 chunks of at most 40, `-m "not arc_close"` | chunk 0: 723 passed, 5 failed; chunk 1: 844 passed, 14 failed; chunk 2: 814 passed, 11 skipped; chunk 3: 624 passed, 6 skipped; chunk 4: 63 passed |
| the 19 failures (all `AttributeError: module 'learnloop.content.pipeline.jobs' has no attribute 'handle_…'`, the nine files above), rerun after the fix with the other edited files and `test_job_types.py` | 314 passed |
| `test_identity_pins.py`, `test_structure_ratchets.py`, `test_effective_defaults_golden.py`, `test_cli_help_snapshot.py`, `test_kill_switches.py`, `test_sqlite_file_copies.py` | 398 passed |
| `tests/test_test_layout.py` alone | 3 passed |
| `tests/test_architecture.py` alone | 18 passed |
| `ruff check` | All checks passed |
| `lint-imports --no-cache` | 52 kept, 0 broken |
| `scripts/check_gate_partition.py` | collected 33453: landing 33387 + arc_close 66 |
| `validate_vault.py` | passed (2,428 notes) |
| after the table took handler names (judgment call 7): `test_job_types.py`, `test_coverage_on_extract.py`, `test_ingest_runner.py`, `test_ingest_jobs.py`, `test_ingest_m3.py`, `test_quick_add.py`, `test_question_promotion_jobs.py`, `test_library_exercises.py` | 197 passed |
| then the 7 test files that read the sidecar's reload after an applying job (`get_queue_revision`, `needs_reload`, `completed_jobs_awaiting_reload`) | 255 passed, 5 skipped |
| then pins, ratchets, defaults golden, CLI snapshot, kill switches, SQLite copies; layout alone; architecture alone; `ruff check`; `lint-imports` | 398 passed; 3 passed; 18 passed; all checks passed; 52 kept |
| AST check at the tip | 134/134 moves AST-identical and verbatim; only `DurableIngestJobs` differs in the host (the table's functions) |
| after the contracts leaf and the defaults loaded by name (K2-22): the same 165-file affected set (the name filter extended with `IngestRunnerError`, `JobCancelled`, `WaitingForInput`, `FetchedBytes`, `JobSpec`, `job_contracts`, which added no file), 5 chunks, `-m "not arc_close"` | 728 passed; 861 passed; 814 passed, 11 skipped; 624 passed, 6 skipped; 63 passed |
| then pins, ratchets, defaults golden, CLI snapshot, kill switches, SQLite copies; layout alone; architecture alone; ratchets and pins with the 223 golden; `check_gate_partition.py`; `ruff check`; `lint-imports` | 398 passed; 3 passed; 18 passed; 360 passed; collected 33456 (landing 33390 + arc_close 66); all checks passed; 52 kept |
| AST check after K2-22 | 134/134 moves still AST-identical and verbatim |
| `module_validate.py` | the five new modules have no module note yet (the landing regenerates) |

## Not verified

- The whole suite, the durability lane and the arc-close gate (the landing runs them).
- K2-20's harm on a screen that reads only the queue revision: found by reading, not shown by a test.
- The vault's generated references for the five new modules (`module_validate.py` lists them as missing until
  the landing regenerates).

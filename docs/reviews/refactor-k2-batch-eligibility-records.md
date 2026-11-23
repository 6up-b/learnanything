# Refactor K2.11, K2.8, K2.12: ingest eligibility from the sidecar, one row per source kind, decision records

Branch `refactor/k2-batch-eligibility-records`, base `54be27df69` (migration head 264, tag mvp-0.66).
Implements K2.11, K2.8 and K2.12 of `k2-ingestion-strategy-2026-11-11.md` as one landing batch.

**No step changes persisted meaning** (`docs/algorithm-change-playbook.md` step 1): nothing here touches scoring,
scheduling, projections or admissibility. K2.11 changes replies and the desktop; K2.8 moves facts into a table with
every reader's answer unchanged; K2.12 writes `decision_records` rows, a RECEIPT that nothing replays
(`tests/test_provenance.py`), through the existing `write_decision`. No algorithm tag, no migration, no new table, no
config field, no model call, no prompt change. No identity pin moved.

## Judgment calls to read first

1. **K2.11, the role hint follows the matrix, so `notes` gains it.** The desktop's copy said `{exam, problem_set}`
   "never define concepts"; the backend's `ASSESSMENT_ONLY_ROLES` is `{exam}`. They are different rules: the backend
   set is the citation rule (an exam citation only aligns assessment), while the hint says what the matrix says when
   `semantic_contract` is false. By the matrix the hint is true of `problem_set`, `exam` and `notes` (a known role
   never takes a manual grant) and `syllabus` has its own line. So the desktop was right about `problem_set`, the
   backend constant is not the rule the hint states, and both missed `notes`. `get_source_roles` returns the whole
   matrix (`semantic_contract`, `assessment_alignment`, `assessment_only`, `scope_only`, `default_inventory_profile`)
   and the hint shows for `!semanticContract && !scopeOnly`. Learner-visible: picking `notes` now shows the hint.
2. **K2.11, `can_reuse_candidate` instead of the strategy's `can_repair`.** The host's check is whether the preserved
   candidate may be reused; repair is reuse plus ops (`repair_candidate` requires `reuse_candidate`). The batch view
   carries `can_retry_synthesis`, `retry_synthesis_job_id`, `retry_synthesis_refusal`, `can_reuse_candidate`,
   `reuse_candidate_refusal`; refusals are code constants whose words are `retry_synthesis`'s own
   (`SYNTHESIS_RECOVERY_REFUSALS`). The "auto-repair" button still shows only for `synthesis_gate_failed`: that is
   which kind of repair the card offers, not whether the host takes it.
3. **K2.11, the bounds come through `get_settings`.** Its `budget_bounds` now covers every `BUDGET_BOUNDS` field (the
   retry panel's `synthesis_output_tokens` was missing); the retry panel reads it through the shared `get_settings`
   cache key, only when a retry is offered. Until it loads, only a finite number passes and the sidecar refuses an
   out-of-range ceiling itself. The page-range rule is a list, `pdf_engines_refusing_page_ranges`, because
   `versioned()` camelizes mapping keys (`glm_ocr` would come back as `glmOcr`).
4. **K2.8, the desktop table is generated, not fetched.** The drop filter, the file picker and the paste check are
   synchronous (a paste's `preventDefault` cannot wait for a reply), so `apps/learnloop-tauri/src/api/sourceKinds.ts`
   is generated from `SOURCE_KINDS` (`python tests/test_source_kinds.py --write`) and `tests/test_source_kinds.py`
   fails when they differ. `classify_ingest_source` also returns the kind's display row (`label`, `noun`). The
   desktop keeps colours and icons per kind (presentation) and an offline guess (the arXiv and YouTube host checks;
   the suffixes are the table's). This is one new non-test TypeScript file: `desktop_validate.py`'s three counts
   moved (338 files, 327 entry-reachable, 344 ACTIVE).
5. **K2.8, "IR builder" and "extraction identity" are one `reader` column** (`document`, `html`, `captions`, `audio`,
   `text`) that `default_extract` and `default_extraction_identity` dispatch on: the strategy's "a plain table and a
   match". The content sniffs (a PDF served by a web URL, an HTML or transcript body under any kind) stay in the
   functions, in their order. A category no row names (`UNKNOWN_KIND`) behaves as each reader did before: text, a
   book, a reference, not a document, fetched as a web page.
6. **K2.8 deletes `ingest/fetchers.py` whole, not only its fetch path**: its pure helpers had no caller outside its
   own tests. The two live YouTube helpers moved to `ingest/youtube.py` (the HTTP-client audit in
   `tests/test_plan_first_transport.py` names the new module instead of the deleted one).
7. **K2.12 writes one record per decision, not one per item.** `ingest_auto_apply` is one record per run's apply
   step; each item left for review is an alternative with its reason (`lost_by`), capped at 50 with per-reason
   overflow counts (the existing `cap_alternatives`). `ingest_inventory_choice` is one record per synthesis run with a
   detail row per unit in `facts.units`. The brief's three choices only: the persona fallback (ledger K2-1) and the
   D2 summary stay out.
8. **K2.12, the trace.** The ingest drain opens no trace scope, so each record would otherwise get a fresh trace.
   The planner (`handle_auto_study_map`) now runs under `trace_scope(<its job id>)` and a synthesis job under its
   build's planner job id (`payload.auto_build.planner_job_id`), or its own id when there is none. So
   `learnloop why <planner job id>` reads the scope, the inventory rows and the apply of one build, and the
   synthesis jobs' model receipts carry that trace id too (receipt metadata only; no key reads it).
9. **The synthesis-tail goldens moved, by additions only.** Each case now holds the `decision_records` rows its build
   writes; every other byte of all 25 cases is unchanged (compared case by case with the `decision_records` table
   taken out, before regenerating). The goldens' `seeded_ids` fixture now seeds the records' own id stream
   (`provenance._RECORD_IDS`) beside the ULID stream, else the record ids are random. The structure ratchet's
   `golden_json_lines` rose by exactly those 1,748 lines (edited by hand; no other member rewritten).

## K2.11: the desktop asks instead of copying

Commits `48a4385074` (the sidecar answers) and `930ff865c3` (the desktop asks).

The strategy's eight copied rules, at this base:

| rule | was | now |
|---|---|---|
| role list (`OutlineAndPlan.tsx`, `AddToCollection.tsx`) | two copies of `KNOWN_ROLES` | `get_source_roles`, read once through `useSourceRoles` (`AddToCollection.tsx`) |
| roles that never define concepts | desktop `{exam, problem_set}`; backend constant `{exam}` | the matrix's `semantic_contract`, `scope_only` |
| retry-synthesis eligibility (`IngestActivity.tsx`) | failed only | the batch's `can_retry_synthesis` (failed, blocked or cancelled, every inventory complete) |
| candidate reuse | the job's `candidate_preserved` flag, then a fetch | the batch's `can_reuse_candidate` (also checks the run still holds the candidate) |
| budget bounds (`IngestActivity.tsx`) | hard-coded | `get_settings`' `budget_bounds` |
| source kind (`IngestScreen.tsx`) | a classifier map without `image` | the classifier's kind as it comes (K2.8 then removes the kind table) |
| native-PDF page ranges | disabled for every native engine | disabled for `pdf_engines_refusing_page_ranges`, the enqueue preflight's own judgement (`_native_pdf_road`) |
| page-range parsing (`PageRangeSelector.tsx`) | a copy | kept as the offline hint; the sidecar validates (unchanged) |

The strategy's `import_source` test: `importedSourceId` now follows the `import` job alone (ledger K2-19).

### The four disagreements: which side was right and what the learner saw

| disagreement | right side | what the learner saw |
|---|---|---|
| retry eligibility | backend | A cancelled (or blocked, behind complete inventories) synthesis offered "↻ resume", which reran it with its old ceilings; the synthesis-only retry with new ceilings was not offered. |
| roles that never define concepts | the matrix (neither copy): the desktop for `problem_set`, the matrix also for `notes` | Picking `notes` gave no hint that notes never define concepts. |
| the image kind | backend | Invisible in most cases: the screen fell back to its own guess, which knew `.png`/`.jpg`; a URL whose suffix sits before a `#fragment` was called a web page. There was no image chip at all (added). |
| native page ranges | backend | With the vault's or the chosen engine `native`, unready, and the fallback opted in, the import reads the PDF locally and honours a range, but the range field was disabled with "page ranges are ignored with the native engine". (The wording stays for the UX overhaul.) |

### Tests, fail-first

`tests/test_ingest_eligibility_contract.py` pins, for each reply, that the reply and the action agree (a retry is
offered exactly when `retry_synthesis` takes it, for failed, cancelled and blocked endings; candidate reuse exactly
when the host takes it, for a kept, a gone and an unpreserved candidate; `get_source_roles` equals `role_authority`
row by row and refuses params, `extra="forbid"`; the settings' bounds; page ranges refused by exactly the listed
engines, over four vault/fallback combinations). Run on an export of the base with the new names inlined as
literals: **`15 failed in 2.91s`**, every failure a missing reply field (`KeyError: 'can_retry_synthesis'`,
`method_not_found`, `KeyError: 'synthesisOutputTokens'`, `KeyError: 'pdfEnginesRefusingPageRanges'`).

Vitest, run on an export of the base frontend with the new test files copied in
(`IngestActivity.eligibility.test.tsx`, `sourceRoles.test.tsx`, `IngestScreen.eligibility.test.tsx`):
**`8 failed | 6 passed (14)`**. The failing ones: a cancelled synthesis offers retry, not resume; the retry
validates with the settings' bounds; no candidate revalidation when the host says it is gone; no outline link for an
exercise import; `notes` never defines concepts; the role vocabulary is asked for; the page range stays open under
a native vault default read locally; the classifier's image kind is shown. The six that passed on the base are the
cases where the two sides already agreed (resume when the host refuses the retry; the range closed under refused
engines; `problem_set`, `exam`, `primary_textbook`, `syllabus`).

Assertions changed: `AddToCollection.test.tsx` and `syllabusRole.test.tsx` gained a `getSourceRoles` mock (the
panel now asks for the vocabulary); `SettingsScreen.test.tsx`'s settings fixture gained the two new fields (type
check). No assertion was loosened. `tests/cli_surface.json` untouched (no CLI changed).

Shared desktop files edited (none of them Reader or desks code): `IngestScreen.tsx`, `IngestActivity.tsx`,
`OutlineAndPlan.tsx` (the role control only), `AddToCollection.tsx`, `api/client.ts` (one line), `api/dto.ts`,
`src-tauri/src/commands.rs` and `main.rs` (one command, `get_source_roles`).

## K2.8: a source kind is one row

Commits `b2e9013517` (the table and its readers), `0cc977fc53` (the desktop reads it), `b52c1beb64` (deletions).

`src/learnloop/ingest/source_kinds.py` holds `SOURCE_KINDS`: per category its label, learner noun, local and URL
suffixes, `fetch_as`, `document`, `reader`, suggested role and whether the guess is confident, and its legacy kind.
Readers now: `resolution.resolve_source` (suffix sets; the order of checks stays there), `jobs.default_fetch` and
`_fetch_metadata`, `jobs._is_document`, `jobs.default_extract`, `jobs.default_extraction_identity`,
`add_source.kind_noun` (was `_KIND_NOUN`), the automatic build's role (was `add_source._ROLE_BY_CATEGORY`), Quick
Add's role and ambiguity (were `quick_add._ROLE_BY_CATEGORY`, `_CONFIDENT_ROLE_CATEGORIES`) and
`source_ingestion.resolve_canonical_source` (the legacy mapping; the two refusals keep their words). The desktop:
the Ingest screen's chips and labels, its offline guess's suffixes, the drop filter, the file picker and the paste
check read the generated table; `dto.ts`' kind union is `SourceCategory` from it.

Deleted: `ingest/fetchers.py` (400 lines, its tests `tests/test_ingest_fetchers.py`), `ingest/detect.py`,
`source_ingestion.detect_source_kind`, the desktop's kind table, classifier map and two suffix lists. Tests that
called a deleted wrapper now call what it wrapped (`tests/test_ingest_detect.py`: `resolve_source(...).category`;
`tests/test_source_ingestion_adapters.py`: `resolve_canonical_source(...)[1]`); `youtube_video_id`'s tests moved to
`tests/test_ingest_youtube.py`; the oEmbed test patches `ingest.youtube`.

### No behaviour change: what was compared, on what

A probe outside the tree recorded every reader's answer on a fixed corpus, run once on an export of the base and
once on the worktree, both through the scratch wrapper, and diffed: **identical** (41,194 bytes each), after the
table commit and again after the deletions. The corpus:

- `resolve_source` and `resolve_canonical_source` (with and without learning objects) on 56 sources: URLs with every
  suffix, upper case, a query, a fragment, arXiv and YouTube hosts and look-alikes, bare and old-style arXiv ids,
  local paths with every suffix the classifier knows plus `.docx` and an unknown suffix, an existing extensionless
  text file, an existing binary and text file with an unknown suffix, empty and prose input;
- `kind_noun`, the automatic build's role and Quick Add's role and confidence for the seven categories, `None`, `""`
  and an unknown one;
- `default_fetch`: the `kind` it asks `fetch_source` for and the oEmbed title and authors, per category;
- `_is_document` over 10 categories x 7 content types x 2 leading byte strings (140 cases);
- `default_extraction_identity` and `default_extract` over 10 categories x 7 bodies (HTML typed and untyped, WebVTT,
  SRT, YouTube caption JSON, Markdown, a PDF), with the audio and document lanes stopped at their first call (the
  audio guard, the document config), so the lane each case takes is recorded; the others record the identity dict
  and a hash of the IR built.

The caller suites ran too (commands below). The desktop half is a behaviour change where the desktop lists had
drifted from the classifier (ledger K2-18): a drop, the picker and a paste accept exactly the classifier's suffixes.
Its vitest, `src/api/sourceKinds.test.ts` and the chips case in `IngestScreen.eligibility.test.tsx`, on the base
export: **`10 failed | 40 passed (50)`** (`.rst`, `.text`, `.mdown` dropped; those and `.png`, `.jpg`, `.jpeg`
pasted; the chips' order and labels).

Assertion changed: `tests/test_sidecar_contract.py::test_sidecar_ingest_source_classification_and_empty_job_list`
compares the classification reply whole; it now includes `label` and `noun` (a deliberate addition to the reply).

## K2.12: why x and not y at the three silent ingest choices

Commit `799810a00b`. All three go through `provenance.DecisionRecord` and `db.stores.provenance.write_decision`
(never raises; a record never changes its decision), in the existing `decision_records` table. No migration.

| kind | written by | status, rule | alternatives (`lost_by`) | facts |
|---|---|---|---|---|
| `ingest_build_scope` | the planner (`run_auto_study_map`), subject `job:<planner>` | `chosen` (`chapters_asked`, `whole_source`, `reading_order`) or `excluded` (the same rules with nothing left, or `whole_reading_exam_material`) | each withheld unit `exam_material`; each chapter `already_built` or `being_built` | source, revision, extraction, chosen chapter ids, unit count, whole source, withheld count, chapters left for later |
| `ingest_inventory_choice` | `open_synthesis_run` (both modes), detail `synthesis_runs:<run>` | `chosen`, `best_inventory` | each losing row with its unit: `unit_text`, `prompt_version`, `route`, `combined_profile`, `profile`, `newest` or `profile_unsatisfied` | mode; per unit its row (or none), the deciding rule (`only_row`, `no_row`, or the preference), candidates, whether the profile was satisfied; units without a row |
| `ingest_auto_apply` | the apply step: bootstrap's `apply_map` and the revalidation's apply, the append's `_apply_routine_items` | `chosen` (`applied`) or `deferred` (`apply_not_requested`, `nothing_new`, `nothing_routine`, or the gate's `auto_build_off`, `auto_apply_off`, `undone`, or `gate_closed` for a gate that names nothing) | each item left for review: the §10.3 condition that failed (`relation_not_routine`, `no_locator_or_target`, `assessment_alignment_target`, `target_changed`, `target_missing`, `span_unresolved`), `review_only:<item type>`, or the run's reason | mode, applied count, waiting count |

To make the reasons recordable without moving a decision: `best_inventory` now returns `inventory_choice(...).row`
(the same ranking, one implementation); `source_append._auto_applies` became `_auto_apply_refusal` (the same
conditions in the same order, returning the failed one); `add_source.auto_apply_allowed` is
`auto_apply_refusal(...) is None` (the same three checks, same order) and `AutoApplyGate` keeps the refusal it last
read; `_choose_scope` returns a `ScopeDecision` (its choice is what it returned before; the dry run reads
`.choice`). Proof that nothing else moved: the 25 synthesis-tail goldens are byte-identical outside the new
`decision_records` rows.

Fail-first: the three end-to-end tests of `tests/test_ingest_decision_records.py` (an automatic build records its
scope, its inventory rows and its apply under its planner's trace, and `learnloop why <planner job id>` reads them;
a build waiting for a look names each waiting item and why, so "why does this concept need a look?" is answered by
`read_naming`; reading on records the chapters skipped as built, and the append's records join that trace), on the
base export: **`3 failed in 7.43s`** (no records). The five plain-value tests exercise the new builders and refusal
codes, which do not exist on the base.

Ported test: `tests/test_ux_phase1_landing.py` reads `_choose_scope(...).choice`.

## Ledger

K2-5 (KB4) fixed. New: K2-18 (the desktop's suffix lists, fixed in K2.8) and K2-19 (the outline link on an exercise
import, fixed in K2.11). K2-1 (the persona gate's silent fallback) stays queued: the brief narrowed K2.12 to the
three choices.

## Commands and results

All Python and CLI runs went through the scratch wrapper (empty home, Codex home and config dir); every pytest
command was a script under the scratch directory checking its target list first, run in a `systemd-run` scope with
3 GB, at `-n 1`; frontend and Rust runs in a 5 GB scope with the shared npm and cargo caches.

`affected` is `scripts/affected_tests.py --files` over the 16 changed src files that still exist: it lists 1,389
test files (`content/pipeline/jobs.py` is imported almost everywhere). Following the brief, those were filtered by
name (the file name contains one of: ingest, source, quick_add, add_source, import, resolution, kind, study_map,
synthesis, append, extraction, inventory, role, eligib, decision_record, ux_phase1, settings_sidecar,
sidecar_contract, desktop_rpc, plan_first, youtube, why, provenance, auto_build, keep_ahead, collection, coverage,
exam_protection, reread, library): 168 files, run in five chunks of at most 40 with `-m "not arc_close"`. Every test
file this batch added or edited is in those 168.

| Command | Result line |
|---|---|
| `tests/test_ingest_eligibility_contract.py` on the base export (fail-first) | `15 failed in 2.91s` |
| the same, worktree | `15 passed` (with `test_ingest_jobs.py`, `test_settings_sidecar.py`, `test_desktop_rpc_contract.py`: `72 passed in 7.37s`) |
| vitest, the three K2.11 files on the base export | `Tests  8 failed \| 6 passed (14)` |
| K2.8 probe, base export against worktree (after the table commit, and after the deletions) | `diff`: identical, 41,194 bytes each |
| K2.8 caller suites (17 files: add-source, ingest detect, m3, runner, transcription, transcripts, native media, quick add x2, sidecar m3, source ingestion x3, v2lite, source kinds, ingest jobs) | `261 passed, 5 warnings in 22.58s` |
| K2.8 deletion suites (ingest detect, adapters, runner, plan-first transport, source kinds, youtube, sidecar reader) | `176 passed in 23.82s` |
| vitest `sourceKinds.test.ts` and the chips case on the base export | `Tests  10 failed \| 40 passed (50)` |
| `tests/test_ingest_decision_records.py`, three end-to-end tests, base export | `3 failed in 7.43s` |
| the same file, worktree | `8 passed in 7.41s` |
| synthesis-tail goldens before regenerating (actual records written aside and compared) | `22 failed, 3 passed`; all 22 differ only by `decision_records` rows |
| `SYNTHESIS_TAIL_GOLDEN_WRITE=1`, then twice without | `25 passed`, `25 passed`, `25 passed` |
| K2.12 suites (27 files: synthesis, append, why, provenance, auto build, landing, decision records ...) | `325 passed, 6 skipped in 113.27s` |
| affected, chunk 1 of 5 | `823 passed, 2 skipped, 3 xfailed in 308.77s` |
| affected, chunk 2 of 5 | `561 passed in 229.39s` |
| affected, chunk 3 of 5 | `1149 passed, 6 skipped, 5 warnings in 133.45s` |
| affected, chunk 4 of 5 | `454 passed in 158.58s` |
| affected, chunk 5 of 5 | `105 passed, 6 skipped in 73.59s` |
| identity pins, structure ratchets, effective defaults, CLI help snapshot, kill switches, sqlite file copies | `398 passed in 77.53s` |
| `tests/test_test_layout.py` alone | `3 passed in 21.24s` |
| `tests/test_architecture.py` alone | `18 passed in 32.10s` |
| `ruff check` | `All checks passed!` |
| `lint-imports --no-cache` | `Contracts: 52 kept, 0 broken.` |
| `scripts/check_gate_partition.py` | `collected 33185: landing 33119 + arc_close 66` |
| `npm run typecheck` | clean (no output after `tsc --noEmit`) |
| `npx vitest run --maxWorkers=2` on the 25 files touching what changed (the new and edited tests, Settings, the Add box, the outline flow, Library, the App shells) | `Test Files  25 passed (25)`, `Tests  242 passed (242)` |
| `cargo check --manifest-path src-tauri/Cargo.toml` | `Finished \`dev\` profile` |
| `desktop_validate.py` | the three counts pass; it still reports the generated notes for `api/sourceKinds.ts` and the touched modules as missing or stale (the landing regenerates them) |
| `git diff --check` | clean |

## Not verified

- No full suite, arc-close gate, durability lane or `--fresh-connections` run; the affected list was narrowed by name
  (1,389 to 168 files), so a test outside the filter that reads a batch reply, the settings reply or a removed name
  ran only if it is in the other gates above.
- No desktop app run, no browser: the desktop half is proved by vitest with mocked replies, typecheck and cargo
  check. The Rust command `get_source_roles` was compiled, not called.
- The K2.8 probe stops the audio and document lanes at their first call, so it proves which lane each case takes,
  not the audio transcription or PDF extraction identities themselves (their code did not change; the import
  suites cover them).
- No owner vault or owner copy was opened, so the counts below are not taken; the records' size on a real book
  (`ingest_inventory_choice.facts.units` holds one row per unit, uncapped) is unmeasured.
- `ingest_build_scope` is written by the planner only; the zero-call dry run (`preview_auto_build`) writes nothing,
  as before. Explicit `create_study_map`/`append_source` runs outside a job (CLI, RPC) write the inventory and apply
  records under whatever trace is current (the sidecar's per-RPC trace, or a fresh one).
- The vault references are not regenerated (the landing does).

## Owner-copy counts the orchestrator should take

On a backup-API copy of each owner vault, before and after the landing:

1. **Retry offers that change**: batches whose synthesis job is `cancelled` or `blocked` with every inventory
   `completed` (these now offer a synthesis-only retry instead of a resume), and batches with
   `candidate_preserved` whose run no longer holds `candidate_output` (these no longer offer revalidation).
2. **Roles**: source-set members and unit overrides with role `notes` (their pickers now show the hint).
3. **Kinds**: `source_artifacts.acquisition_kind` values outside the seven categories (they take `UNKNOWN_KIND`,
   which reads as before), and a `rebuild --shadow` diff of zero on extraction identities is the strong form of the
   probe above.
4. **Records after one automatic build** (e.g. `learnloop why <planner job id> --json`): the three kinds present
   under one trace; `ingest_inventory_choice.facts.units` length and the record's size for the largest source set
   (it holds a row per unit, uncapped); the rule distribution (how many units had more than one row, and on which
   preference the chosen one won; K3.1 expected near zero).

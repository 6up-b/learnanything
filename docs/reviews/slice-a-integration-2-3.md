# Slice A integration: daily-loop follow-ups, Phase 2 and Phase 3

**Branch:** `integrate/slice-a-2-3`, created from `main` at `94cf6bd6`. Nothing
was merged into `main` or pushed, and no source branch was rewritten.

**Result:** the three branches are merged. `learnloop eval` has a single
implementation. The owner-directed Codex change is in. Every required check
passes; the numbers are under Verification.

## Commits

| Commit | What |
|---|---|
| `7051a0d8` | Merge `fix/daily-loop-followups` (`421ba4be`). Clean merge |
| `907ab33d` | Merge `slice-a/phase-2` (`32dad609`). Clean textual merge; migration 167 kept |
| `ba8e3247` | Merge `slice-a/phase-3` (`c917f8ec`): conflicts resolved, migration renumbered to 168, `fixtures/migration_head_168`, references regenerated |
| `0c63463a` | Unify the offline evaluation harness behind one `learnloop eval` |
| `811866e4` | Owner-directed: `families propose` may run on Codex, with estimated-only cost |
| `4d3e2683` | Cross-check tests: daily-loop follow-ups against F1 and PF-a |
| `0e1265bf` | Regenerate the DB and config references for the final tree |
| this commit | This report |

## Conflict resolutions

The daily-loop merge and the Phase 2 merge had no textual conflicts. The
Phase 3 merge conflicted in these files:

| File | Decision |
|---|---|
| `migrations/167_activity_family_membership.sql` | Renamed to `168_activity_family_membership.sql`; Phase 2 keeps 167. See Migration renumbering |
| `fixtures/migration_head_167/{README.md,state.sqlite}` | Kept Phase 2's 167 head, upgraded it to 168 and renamed the directory. Phase 3's independently built 167 database was discarded |
| `src/learnloop/config/schema.py` | Kept both `field: FieldConfig` (Phase 2) and `families: FamiliesConfig` (Phase 3) |
| `src/learnloop/config/template.py` | Kept the union. The `mvp-0.9` defaults fingerprint was recomputed for the union: `ec9f1d59…4168` |
| `src/learnloop/substrate/rebuild_orchestrator.py` | Kept both replayers (`field_outcomes`, `family_memory`); each DERIVED table has exactly one owner |
| `src/learnloop/cli/__init__.py` | Registers `field`, `families` and the `eval` Typer group. Phase 2's `app.command("eval")` was replaced by the group |
| `tests/test_architecture.py` (SQL-owner registry) | Union: `db/stores/field.py`, `db/stores/families.py` and `substrate/family_memory.py` |
| `tests/cli_help_snapshot.json` | Regenerated; see Verification |
| ~293 generated files under `docs/learnloop-architecture-vault/Reference/` | Took one side, then **regenerated** with `db_generate_reference.py`. Nothing was hand-merged |

Several files merged cleanly but were checked by hand:

- **`table_roles.py`.** All five new tables are classified:
  - `facet_outcome_observations` and `family_memory_state`: DERIVED;
  - `question_classifications` and `family_proposals`: WORKFLOW;
  - `activity_family_membership_events`: RAW_LEDGER.
- **Parameter registry.** Phase 3's `families.*` rule (operational) is kept. Phase 2's `field.*` settings are booleans and literals, which need no numeric classification. The registry audit passes.
- **`pyproject.toml` import contracts.** Both phases' additions are kept. The unification changed them; see below.
- **`vault/loader.py`.** Phase 2's `load_environment` flag and Phase 3's activity-family loading both survive.
- **`db_*_reference.py`.** Both phases' config-section notes are kept.
- **Hand-written counts.** `Reference/Configuration/Configuration.md` and `Reference/Database/Database.md` now state 528 leaves, 30 sections and 266 table notes. The validator checks these counts.

## Migration renumbering and fixture

1. `git mv migrations/167_activity_family_membership.sql migrations/168_activity_family_membership.sql`. The SQL is unchanged.
2. Made a backup-API copy (`learnloop.db.copies.backup_database`) of Phase 2's `fixtures/migration_head_167/state.sqlite` and upgraded it through `learnloop.db.migrate.apply_migrations`, which applied only 168.
3. Ran `PRAGMA wal_checkpoint(TRUNCATE)` and then `PRAGMA journal_mode=DELETE`, and wrote the result back into the fixture through the backup API.
4. Checked the result:
   - `integrity_check` is `ok` and `foreign_key_check` is empty;
   - `max(version)=168`, with 167 `learner_field_outcomes` and 168 `activity_family_membership`;
   - the journal mode is `delete`, with no `-wal`/`-shm` and no `sqlite_sequence`;
   - its schema is exactly Phase 3's 167 schema plus Phase 2's two tables and one index;
   - the only data change from Phase 2's 167 head is the new `schema_migrations` row.
5. Renamed `fixtures/migration_head_167` to `fixtures/migration_head_168` and rewrote its `README.md`. Phase 2's `rubrics/.gitkeep` is kept.
6. Updated every hard-coded path:
   - `tests/test_migrations.py`, `tests/test_shadow_rebuild.py` and `tests/test_rebuild_orchestrator.py`;
   - `db_validate_reference.py` (path and `SCHEMA_HEAD`);
   - `db_generate_reference.py` (three paths and `SCHEMA_HEAD`).

   The sixth occurrence that Phase 1's audit found (`tests/test_embedding_store.py`) now globs `migration_head_*`, so it needed no change. A repository-wide search finds no other `migration_head_167`.
7. Regenerated and validated the DB/config references: schema 168, 266 table notes, 528 config leaves, **0 errors**.
8. Added integration notes to `slice-a-phase-3.md` and `pf-a-evaluation-integration.md`. Their history is otherwise unchanged.

## Harness unification

There is now one implementation, `learnloop.field.evaluation`. Each report is a choice of arms over one prequential replay loop.

**Deleted.**
- The `learnloop.evaluation` package (`harness.py`, `predictors.py`, `report.py`).
- `learnloop.offline_outcomes`.
- `learnloop.substrate.family_memory_rows`, the row adapter Phase 3 asked to have replaced.
- Phase 3's separate `IdeaHier` EKF.
- The seven `family_memory_rows` import-contract exemptions.

**Rows.**
- Phase 2's canonical outcome view (`field.outcomes`) supplies every row.
- With `retrieval=True` it also derives the fields the memory arms need, ported from Phase 3's adapter:
  - the persisted FSRS rating, rounded and capped, with the authored hint cap;
  - strict retrieval coldness: activity policy, final coldness receipts, and a strict reveal-ledger lookup since the previous attempt on the item;
  - the grader model and calibration status;
  - the resolved family-judge models.
- The family grouping is the **current authored assignment, applied retrospectively**, as Phase 3 designed it. It never retargets a row's LO, outcome or revision status.
- `enrich_attempts` also voids memory coldness when a suspected leak is linked to the attempt.

**Arms.**
- `learnloop.field.memory` registers the 12 memory arms in Phase 2's registry: memory keyed per item, family or LO, with the current fit or the defaults, each with and without the distance discount. They form the groups `memory` and `families`.
- The arms reuse the single pure FSRS fold, `scheduling.family_memory_model.FamilyMemory`. It now reads the field rows by attribute and imports nothing from `field`.
- **`idea_hier` is `lo_general` plus a `family` extension** on the shared EKF: an independent `family:<id>` effect with σ_F² = 0.5 (`ArmConstants.family_variance`). It keeps Phase 2's `a·(θ−b)` units, drift, step bounds and Joseph update. Without a family it is bit-identical to `lo_general`.
- Arm factories declare the frozen replay inputs they accept: `general_means`, `lo_priors`, `config`, `fsrs_weights`.
- The CLI resolves the current FSRS fit through a borrowed read snapshot and passes it in. No arm reads a store.
- `field.memory` is added to the `field-predictors-are-pure` contract, with two documented exemptions to the pure FSRS modules.

**Loop.**
- There is one replay, with **all arms predicting before any arm observes**.
- Ability arms score positive-mass attempts, as before. Memory arms score graded cold retrievals (`AttemptRow.memory_scored`). Each family abstains (NaN) on the other's rows, and paired comparisons use only common rows.
- Report 2 is unchanged for ability rows. A memory-only row is treated like an excluded row: it blocks fast-track.
- New counts: `ability_scored_attempts`, `memory_scored_attempts`, `memory_training_rows`, `missing_variant_distance` and `zero_ability_mass`.
- New splits: `relation`, `retrieval`, `grader_model`, `calibration_status` and `family_judge_model`.
- When memory arms run, the manifest gains a `memory` block: the weights and their hashes, the fit ID, `is_defaults`, the grouping and the distance source. Phase 3's limitations are reported.
- Memory arms are never recommended, and `validate_active_predictor` rejects them (G11).

**Projection.**
- `family_memory_state` folds the same view, with the `current_content` fallback. The orchestrator loads the rows through its already-exempted `field.outcomes` edge and passes a loader. A vault with no families still never reads outcomes.
- The `family_memory` replayer now depends on `learning_state`, as `field_outcomes` does, and the projection version is `family-memory-cold-v3`.

**CLI. One harness, and the existing commands still work.**
- `learnloop eval --vault X` is **the legacy calibration report again**, with the same output as `main`.
  - `--section all` means the five legacy sections.
  - Phase 2 had made `all` include `field`. That changed the default output and wrote report files into `./fixtures-local/reports`.
- `--section field`, or `all,field`, writes reports 1–2 with every registered arm, including `idea_hier` and the memory arms (field spec §7.2).
- **`learnloop eval families` stays a subcommand over the same harness.** It runs the `families` arm set (`mastery_ekf`, `lo_general`, `idea_hier` and the 12 memory arms) and writes content-addressed files, `pf-a-<hash>.json/.md`. `--output` and `--output-dir` are aliases. It no longer loads dotenv or global settings.
- `eval_command` in `cli/app.py` remains the legacy callable.

**One revision policy.**
- Phase 2's rule is kept. A row is `exact` only with:
  - a selection receipt and a content-hash-matched snapshot;
  - a matching grading contract;
  - a matching item, rubric, receipt and compiled contract;
  - a uniquely determined single-facet allocation.

  It uses the latest non-superseded grading epoch (field spec §3).
- **One explicit `--legacy-fallback`** (`exclude` | `current_content`) on `eval`, `eval families` and `field data-check`. It defaults to the vault's `field.legacy_fallback`, which is `exclude`. `current_content` rows are labelled `reconstructed_current`. The value used is reported in `data_check.legacy_fallback`.
- Dropped from Phase 3's adapter:
  - the regrade exclusion: spec §3 says to use the latest surviving epoch;
  - the `dont_know` mass = 1.0 override: Phase 2 resolved this to the configured attempt-type mass;
  - the `rubric_score` fallback for attempts with no `grading_evidence`. Those attempts have no outcome row; `data-check` now counts them in `attempts_without_outcome_row`.

**Tests.**
- `test_family_evaluation.py` and `test_family_memory_projection.py` were ported to the unified API. They keep Phase 3's invariants: the coldness and transfer gates, receipt windows, past-only reveals, a strict reveal failure, rating from the persisted score, the distance discount, zero-mass memory training, and aggregate-only output.
- New CLI tests cover:
  - the legacy default;
  - `eval families` being read-only and deterministic, with no compat-cache reads;
  - one `--legacy-fallback` for every report.

## Other unions

- **Config.** Both template sections are present. The fingerprint was recomputed. The reference validator counts 528 effective leaves in 30 top-level sections.
- **Import-linter.** 8 contracts, all kept. Phase 2 had 8 (it added two) and Phase 3 had 6.
- **SQL-owner registry and CLI help snapshot.** Both are unions. The final snapshot differs from Phase 2's merge state only in the intended commands: `<root>`, `eval`, `eval families`, `families`, `families propose`, `families undo` and `field data-check`.
- **Frontend.** Only Phase 2 changed the frontend: the map's untested state, `dto.ts` and the well and terrain views. It does not overlap with the daily-loop files that `main` changed.

## Daily-loop fixes against Phase 2

- **Overlap.** The follow-ups changed:
  - `repositories.py`: session end and last activity;
  - `reader_authoring.py`: adoption and retire;
  - the sidecar context: the adoption sweep after state sync;
  - the reader and golden-path handlers.

  The field package reads no sessions, and Phase 2 touched none of those files.
- **Behavioural checks,** in `tests/test_integration_daily_loop_field.py`:
  - A reference-only reader question adopted by the sidecar reload sweep serializes without family fields. It appears on the map with no facet claiming readiness, and it has no outcome row before an attempt.
  - A card retired through `reader.maintain` stops being a family candidate.
- **Existing tests.** All 13 follow-up tests and the daily-loop suites pass on the merged tree.

## Owner-directed changes

**Codex for paid PF roles.** Owner decision of 2026-10-12, recorded in Slice A spec §5 rule 6, "Subscription transports" (main `16db5ac5`). It is in commit `811866e4`.

- **`ai/spend.py`.**
  - `SpendBudget(subscription=True)` admits an unknown price, and it does not enforce the token or dollar caps.
  - The **candidate, pair, call and retry caps still apply**, so a runaway loop stops.
  - `budget_json` records the caps in force with `billing=subscription`, `cost_basis=estimated_only`, `physical_request_bound=false` and `not_enforced`.
  - `is_subscription_transport()` is true only for Codex profiles (`codex_sdk`, `http`) and clients (`codex_sdk`, `http_adapter`).
  - Metered budgets (OpenRouter, OpenAI API keys, embeddings) are byte-identical, with the full cap set.
- **`families propose`.**
  - A Codex `pf_family_judge` route is accepted. It runs without `single_request()` and does not need the bounded capability. Metered routes still need both.
  - The cost comes from the token usage Codex reports, or else from the input-plus-output estimate. It is priced only when `--price-per-million` is given.
  - `--dry-run` shows the estimate, and each receipt's `usage_json` carries it with `cost_basis=estimated_only` and the token source.
- **Tests.** In `test_family_proposals.py` and `test_spend_controls.py`:
  - a Codex-routed dry run, through the API and the CLI, with no client constructed and no price;
  - a fake Codex run through the route resolver, under a 1-token and $0 cap, whose receipts carry `estimated_only`;
  - the input-plus-output fallback;
  - the call cap still stopping a Codex run;
  - a metered route still enforcing its physical-request bound, the unknown-price refusal and the token cap;
  - a unit test of subscription admission.

The full gate was rerun after this commit (below).

## Verification (final tree)

| Check | Result |
|---|---|
| `uv sync --extra dev`, then `uv pip install pypdfium2` | OK. `uv sync` removes the extra package, so it was installed again afterwards |
| `uv run lint-imports --no-cache` | **8 kept, 0 broken** |
| `uv run pytest -n auto` | **6,677 passed**, 0 failed, 14 existing warnings (Python 3.12 fork and SQLite datetime-adapter); 157 s |
| `uv run pytest -m durability` | **64 passed**, 6,613 deselected |
| `npm install` | OK. Existing notices: npm audit, and esbuild's postinstall blocked by `allowScripts`; the build still succeeds |
| `npm run typecheck` | Passed (exit 0) |
| `npm test` (vitest) | **35 passed**, 11 files |
| `npm run frontend:build` | Passed; existing warning about a chunk over 500 kB |
| `db_generate_reference.py` / `db_validate_reference.py` | Schema **168**, 266 table notes, 528 config leaves, **0 errors** |
| `validate_vault.py` (extra) | Passed: 1,028 notes |
| Head fixture | `delete` journal, integrity `ok`, FK-clean, `max(version)=168`, no WAL companions |
| Tracked working vaults | Untouched; `git status` is clean |

Before the Codex commit, the unified tree had 6,669 passed and 1 failed. The failure was the PDF-page test, before `pypdfium2` was installed; after installing it the test passed.

## Smoke reports on `fixtures/linear_algebra`

The copy is `fixtures-local/la-smoke`, made from the worktree's clean tracked vault with the backup API. That vault is at schema 155, uses algorithm `mvp-0.8`, and has 70 attempts, all with grading evidence. No AI calls were made.

1. **Doctor.**
   - The first run reported 2 errors on the raw copy: migrations 156–168 missing, and the empty `rubrics/` directory, which Git does not track.
   - `mkdir rubrics` followed by `doctor --fix-state` migrated the copy to 168, in WAL mode.
   - `doctor` then reported **0 errors and 54 warnings**. All are existing authored-content warnings: contract cells, error types, proposals, config, concepts.
2. **Shadow rebuild.**
   - The first `rebuild --shadow` against the stale stored projection gave 22 facet, 6 mastery and 47 schedule deltas, with the source SHA unchanged.
   - After one `rebuild-derived-state`, the residual was 0 facet, **2 mastery and 8 schedule** deltas. The mastery logits differ by about 1e-5 and the due dates by a few seconds.
   - After a second `rebuild-derived-state`: **0 / 0 / 0**, at the same version `mvp-0.8`.
   - **This is pre-existing.** `main`'s code (`94cf6bd6`, exported read-only and run against its own backup copy) shows the same 2 and 8 after one rebuild, and 0 after the second. On this vault, derived state needs two rebuilds to reach a fixed point.
3. **`field data-check` and the reports.** Scored rows:

| Report | Policy | Attempts | Scored (any arm) | Ability-scored | Memory-scored | First-attempt rows | Report 2 later attempts |
|---|---|---:|---:|---:|---:|---:|---:|
| `field data-check` | `exclude` | 70 (all `excluded`) | n/a | 0 eligible | 0 | n/a | n/a |
| `field data-check` | `current_content` | 70 (`reconstructed_current`) | n/a | 54 eligible | 45 cold retrievals | n/a | n/a |
| `eval --section field` (33 arms) | `exclude` | 70 | **0** | 0 | 0 | 0 | 0 |
| `eval --section field` (33 arms) | `current_content` | 70 | **69** | **54** | **45** | **3** | **0** (0 assumed LOs) |
| `eval families` (15 arms) | `exclude` | 70 | **0** | 0 | 0 | 0 | 0 |
| `eval families` (15 arms) | `current_content` | 70 | **69** | **54** | **45** | 3 | 0 |

- **Other inputs.**
  - There are 11 interaction signals.
  - There are 10 claims, but none was made before the first attempt, so the priors are the zero default.
  - No families have been applied, so `idea_hier` equals `lo_general` and the family memory arms equal the item arms.
  - There is no fitted FSRS set, so the current-fit arms use the defaults.
- **Reconstructed log loss** (exploratory, current content):

  | Arm | Log loss |
  |---|---:|
  | `mastery_ekf` | 0.457 |
  | `lo_general` | 0.407 |
  | `lo_general+composite` | 0.375 |
  | `memory_item` | 0.663 |

  `lo_general` beats the incumbent overall by 0.050 (95% CI [0.019, 0.081], n = 54). The decision is still **keep_incumbent**: only 3 first-attempt rows exist, and report 2 has no later attempts.
- **Will reports 1–2 have enough rows on real data? Not under the default policy on this vault.**
  - Every attempt predates the item-snapshot receipts (migration 164), so strict `exact` matching excludes all 70.
  - Even reconstructed, the first-attempt split (3 rows) and report 2 (no fast-tracked LOs) are far too thin for D9.
  - Only attempts made after a vault reaches schema 164+, on scheduler-selected single-facet items, can become `exact`. Usable strict reports need weeks of new practice. They also need the receipt improvements Phase 2 proposed: a graded full-item hash and numeric criterion-to-facet weights.
- **Outputs** are in `fixtures-local/reports/la-smoke-{field,families}-{exclude,current_content}/`. They are not committed.

## Unresolved and follow-ups

1. **Thin data (product decision).**
   - The default strict reports are empty on `linear_algebra`.
   - The owner must decide whether to review the explicitly labelled `current_content` reports, or wait for exact rows.
   - The receipt improvement Phase 2 proposed (graded full-item hash and numeric criterion-facet weights) would widen `exact`.
2. **Copies migrated by the unmerged Phase 3 branch.**
   - Phase 3's own `fixtures-local` copies recorded version 167 as `activity_family_membership`, which is incompatible with this numbering.
   - Discard them and make fresh copies. Tracked vaults are unaffected: they are at 166 or below.
3. **Codex on Phase 2's paid routes.** `field classify-questions` and `eval --prepare-llm` still refuse non-`openai_chat`/`openrouter` profiles. Spec rule 6 now also allows Codex for the LLM-probability arms. This was outside the requested scope (families propose and shared spend code). It needs the same subscription-budget treatment in `cli/field_llm.py` and `cli/field_classification.py`.
4. **Spec choices made in integration.** Review them:
   - memory arms are in the default `--section field` arm set (spec §7.2: "every arm");
   - Phase 3's regrade exclusion and full-mass `dont_know` were dropped in favour of Phase 2 and spec §3;
   - attempts without `grading_evidence` give no outcome row in either policy; they are counted instead.
5. **Two rebuilds to a fixed point.** On `linear_algebra`, derived state needs two `rebuild-derived-state` runs before shadow deltas reach 0. This is pre-existing on `main`, so it is worth its own investigation.
6. **Module reference notes.** `module_validate.py` lists missing notes for every Slice A module (Phases 1–3) and for `main`'s `serving.py`/`lifecycle.py`. No phase regenerated module notes. Out of scope here.
7. **Main has moved.** It is at `16db5ac5`, with docs and spec changes only. The branch is not rebased; merging it into `main` brings the spec text that the Codex change cites.
8. **Not run.** `cargo check` was not required. Phase 2 reported a broken local `rustc`, and no Rust changed.

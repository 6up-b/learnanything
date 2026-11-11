# Refactor C3: calls and keys nothing uses

Arc C ("delete what's proven dead"), step C3 of `docs/specs/refactor_strategy_v3.md` §2.5. Branch
`refactor/c3-unused-calls`, based on main `88607cb3fe` (arcs A and B closed, T1 landed). C1 and C4 run in parallel
from the same base; this step stays out of their files (`ai/providers/`, `codex_lockdown.py`, `CodexConfig`, C1's
modules and `Repository` methods).

**Result.** Seven sidecar RPCs, 42 client methods and 47 Tauri commands that nothing called, and eight config keys
(15 effective leaves) that nothing read, are gone: 614 source lines removed. Every candidate held at this tip; none
moved to the owner's list. An old `learnloop.toml` still setting a removed key loads as if it did not (tested).
`scripts/vault_report.py`, the owner's read-only report for D1, is new. Proofs: typecheck, vitest (2,846 tests),
`cargo check`, the phone and desktop contract tests, 659 targeted test files (12,091 passed), `lint-imports`, `ruff`,
the four validators, and a regeneration fixed point. Seconds saved: about 1.7 s serial.

## Step 0: each candidate proved again at this tip

Method, per candidate: `git grep` over `src`, `tests`, `scripts`, `apps/learnloop-tauri/src` (TS),
`apps/learnloop-tauri/src-tauri/src` (Rust) and the vault's `_scripts`, for the quoted name (string dispatch:
`@method("…")`, `call("…")`, `sidecar_passthrough!`) and for the bare word (imports, attribute reads, `getattr`
strings); the phone allowlist (`src/learnloop_mobile/allowlist.py`, 60 methods) and MCP (`src/learnloop_mcp`, which
calls application services in `learnloop.remote`, never sidecar RPCs); `importlib` in `src/learnloop_sidecar`
(none); and the replay, rebuild and upgrade paths (no RPC handler or Tauri command is imported by
`substrate/`, `ops/doctor.py`, `activation_journal.py` or any upgrade module: handlers are reached only through
`METHOD_REGISTRY`, filled by `learnloop_sidecar/handlers/__init__.py`). The TS caller scan reads every property of
`export const api = {…}` in `client.ts` and looks for its name as a word in every non-test `.ts`/`.tsx` file
(dynamic `api[...]` access: none; the two `(api as {...}).name` reads name their method).

### Sidecar RPCs (the map's rows)

| RPC | Handler at this tip | Callers found | Verdict |
|---|---|---|---|
| `curriculum.cover` (word-matched: the quoted name, not the prefix of `curriculum.coverage_correct`) | `handlers/correspondents.py:367` | No Tauri command, no TS string, not phone-allowed (pinned desktop-only), not MCP. Tests: `test_section_coverage_rpcs` (its own), and as a setup step to seed judged coverage in `test_reader_ca5_also_in_books`, `test_reader_ca5_landing`, `test_reader_ca5a_find_section`, `test_reader_rw5d_p4a_figures_follow`, `test_section_coverage_review`. The same judgment stays reachable from `learnloop curriculum cover` (CLI, `SC.cover_source`) and the deliverable path's own job (`handlers/deliverables.py`). `COVER_ORIGIN` is a plan-fallback origin string and a `model_calls.owner_id` prefix: stored rows naming it are read by shape, nothing matches on it. | delete, with its job registry (`_Jobs`, `_jobs`, `_public`, `_job_for`, `_run`), which only it starts; `reader.correspondents` keeps its `job` field, always `null` (it was `null` whenever no job had been started, which is now every case) |
| `curriculum.cover_job` | `correspondents.py:413` | Same as above: tests only | delete |
| `reader.followups_plan` | `handlers/reader_followups.py:221` | Tests only (`test_reader_followups::test_the_plan_rpc_refuses_with_the_switch_off`, the desktop-only pin). Today's build plans the same work in the background (`prepare_followups`, kept). | delete |
| `get_practice_coverage` | `handlers/practice_index.py:144` | Tests only (`test_practice_index_adapters::test_sidecar_rpcs`' last two lines; the desktop-only pin). `coverage_report` stays (CLI `practice-index coverage`, `cli/embeddings.py`, `instructional/harvest.py`). | delete |
| `list_vault_epigraphs` | `handlers/epigraphs.py` (the whole module) | Tests only (`test_sidecar_epigraphs`, and `test_affected_tests` uses the module as its example of a handler reached through the registry). `recent_vault_epigraphs` stays (synthesis reads it). | delete the module |
| `source_outcomes` | `handlers/ingest.py:1266` | None. `analyze_source_outcomes` stays (CLI `source-outcomes`, maintenance feed). | delete |
| `rpc.health` | `handlers/app.py:96` | None (`get_runtime_health` is the live twin). | delete |

### Tauri commands with no TS string

All 415 `sidecar_passthrough!` commands and every `#[tauri::command]` function, against every quoted string in
`apps/learnloop-tauri/src` (tests included). Six have none at this tip (the map listed five;
`update_session_checkpoint` is new to the list and was never called from TS: `git log -S` finds no TS use):

| Command | Sidecar method | Verdict |
|---|---|---|
| `get_config` | `get_config` | delete the command (the RPC stays: not on the map's list; see open items) |
| `diagnostic_pack_assemble`, `diagnostic_pack_admit`, `diagnostic_pack_review` | `diagnostic.pack_*` | delete the commands (the RPCs belong to C5's Golden Path family) |
| `practice_pool_assemble` | `practice_pool.assemble` | delete the command (C5's family too) |
| `update_session_checkpoint` | `update_session_checkpoint` | delete the command; the RPC stays, phone-allowed (`allowlist.py:117`) |

After the 42 client methods below go, most of their Tauri commands have no TS string either, so they go too
(recomputed after the client edit: see the corrections below); `clear_session_checkpoint` and `get_attempt` keep
their client methods and commands. Rust: nothing else calls them
(`frame_guard.rs`, `sidecar.rs`, `vault_watcher.rs` and the capability file name no command); `cargo check` is the
proof. `tests/test_desktop_rpc_contract.py` keeps the four layers consistent.

### The 44 client methods with no production TS caller

Exactly the map's 44 at this tip (493 methods in `api`). Kept: `clearSessionCheckpoint` and `getAttempt` (their RPCs
are phone-allowed; the brief keeps them). The other 42 have no prod caller; only `workbenchGet` is named in tests,
as a `vi.fn()` key in eight PracticeScreen/ReaderScreen mocks (a mock key, never called through `api`).

| Client method | Tauri command (kind) | Sidecar RPC | Phone | Other `src` users of the RPC name | Verdict |
|---|---|---|---|---|---|
| `reloadVault` | `reload_vault` (fn) | `reload_vault` | no | none | delete method + command |
| `getRecentIngests` | `get_recent_ingests` (fn) | same | no | none | delete method + command |
| `startInventory` | `start_inventory` | same | no | none | delete method + command |
| `refreshRevision` | `refresh_revision` | same | no | none | delete method + command |
| `setGoalUseWeight` | `set_goal_use_weight` | same | no | none | delete method + command |
| `getPlacementState` | `get_placement_state` | same | no | none | delete method + command |
| `recordPracticeUsage` | `record_practice_usage` | same | no | `practice_index/usage.py` (the signal's writer) | delete method + command |
| `compareSources` | `compare_sources` | same | no | the tool name in `ai/tool_requests.py`, `instructional/*`, `source_retrieval/*` | delete method + command (the RPC and the tool stay) |
| `exportClaims`, `purgeClaims` | `export_claims`, `purge_claims` (fn) | same | no | none | delete methods + commands |
| `getRemediation` | `get_remediation` (fn) | same | no | none | delete method + command |
| `blueprintRegister` | `blueprint_register` | `blueprint.register` | no | none | delete method + command |
| `goldenPathBoundaryDiff` | `golden_path_boundary_diff` | `golden_path.boundary_diff` | no | none | delete method + command |
| `diagnosticBaselineEnter`, `diagnosticBoundaryView`, `diagnosticTriageOverride`, `diagnosticPackList` | `diagnostic_*` | `diagnostic.*` | no | none | delete methods + commands |
| `practicePoolStatus`, `practicePoolAdmitSurface` | `practice_pool_*` | `practice_pool.*` | no | none | delete methods + commands |
| 18 Reader methods: `readerRoutingPrior`, `readerBlockHealth`, `readerBlockOriginalRegion`, `readerTranslateSelection`, `readerCreateAnnotation`, `readerAnnotationHistory`, `readerOutboxStatus`, `readerEnqueueRequest`, `readerRequestStatus`, `readerCancelRequest`, `readerDrainRequests`, `readerReviewSourceObject`, `readerLinkRelation`, `readerSpanLearningObjects`, `readerMaintain`, `readerShrinkEnvelope`, `readerPrime`, `readerRestore` | `reader_*` | `reader.*` | no | none | delete methods + commands |
| `readerFollowups` | `reader_followups` | `reader.followups` | no | none | delete method + command |
| `curriculumPath`, `curriculumReady`, `curriculumCoverageCorrect` | `curriculum_*` | `curriculum.*` | no | none | delete methods + commands |
| `workbenchGet` | `workbench_get` | `workbench.get` | no | none | delete method + command |

The sidecar RPCs behind these 40 commands stay: the strategy names the client methods, not their handlers, and
several have tests or other callers. They are listed under open items.

### Config keys read by nothing

Raw-TOML readers checked too: `ops/doctor.py` reads the parsed TOML dict, not the model.

| Key (dotted) | Defined | Readers at this tip | Verdict |
|---|---|---|---|
| `locks.facet_lock_mass`, `locks.facet_surface_groups` (the whole `LocksConfig`) | `config/schema.py:1752` | None in `src`. `ops/doctor.py:838` warns on a `[locks]` table in the raw TOML (kept). The vault's `db_validate_reference.py:118` and `db_generate_reference.py:989` special-case it. Tests: the effective-defaults golden; `test_km2_sim_gates.py:85` asserts the unread default. | delete |
| `facet_identity.merge_locked_facets` | `schema.py:3570` | None in `src`; `doctor.py:839` warns on it in the raw TOML (kept); the two vault scripts special-case it. Tests: golden; `test_facet_identity_composition.py:109` asserts the unread default; `test_facet_identity_actions.py` checks doctor's warning (kept). | delete |
| `mastery.irt.discrimination_min`, `mastery.irt.discrimination_max` | `schema.py:149-150` | Only the parameter registry's rule names them (`parameter_registry.py:3008`, a dormant "decision" prior). | delete, and drop the names from the rule |
| `plan.pre_questions` | `schema.py:3866` | Only the registry's structural rule (`:2955`) and the vault generator's description. | delete, and drop the name from the rule and the description |
| `recall_coverage.severity_examples.*.target_error_type` | `schema.py:434`, `:468` (the `arithmetic_slip` example) | None: `recall_calibration.py` reads `expected_error_type` and `expected_severity_band` only. Test: `test_recall_calibration.py:29` asserts the unread value. | delete |
| `error_impacts.*.lo_mastery_delta` | `schema.py:1733`, and `-0.05` in two `setdefault`s at `:4988`, `:4992` | None: `learner/recall_coverage.py:414` reads `local_severity_gain`, `families` elsewhere. The registry's suffix rule (`:2820`) registers it as a "decision" shaping weight. | delete, and the rule |

Registry consequence, checked: `refresh` walks `decision_specs()` and upserts; it never deletes, so the stored
`parameter_registry` rows for the removed decision paths (`mastery.irt.discrimination_*`,
`error_impacts.*.lo_mastery_delta`) stay readable as they are. `freeze_manifest` reads all stored rows, so a
manifest frozen after this step still lists them with their last value hash; a manifest is frozen once per version,
so existing ones are unchanged. `audit` lists stored active rows without a certificate (the lo_mastery_delta rows
were already there). `controller_snapshot`'s manifest hash covers only controller-owned specs (no config path), so it
does not move. Whole-config hashes (`daily_plans.config_hash`, the router receipt's `versions.config`, report
`config_hash` fields) are provenance only (no code compares them) and change with this schema as with any other
config schema change.

Old configs: the nested models holding these keys are pydantic models with the default `extra="ignore"`, so a TOML
still setting a removed key loads and the value is dropped (the top-level `[locks]` table is the one exception, see
the corrections below); doctor already warns on `[locks]` and `merge_locked_facets`. A test loads a vault whose TOML
sets every removed key (below).

### Learner reach and fixed inputs

No candidate is on a learner path: no TS, phone or MCP caller, no replay, rebuild or upgrade import. No served item,
router draw, grade or replay reads a removed key. The step stops short of anything else.

**Corrections found while building.** `LearnLoopConfig` itself is `extra="allow"` (thirteen models are; none of
C3's nested ones), so an old TOML's top-level `[locks]` table stays on the loaded config as an unread extra, exactly
as any unknown top-level table does. Its dump for a vault that sets `[locks]` is therefore unchanged by this step.
Two more facts the step 0 scan did not show at first and the build did: `readerProblemCrops` (live) shares
`reader_block_original_region` with the deleted `readerBlockOriginalRegion`, so that Tauri command stays; and the
`compare_sources` Tauri command goes, because the string's other TS uses are the AI tool's name, never a `call`.
The command list was therefore recomputed after the client methods went, with the contract test's own parser
(`tests/test_desktop_rpc_contract.py`): 47 commands with no `call` string, every other one kept.

## What was deleted

| Where | What | Lines (removed / added) |
|---|---|---|
| `src/learnloop_sidecar/handlers/correspondents.py` | `curriculum.cover`, `curriculum.cover_job` and the job registry only they used (`_Jobs`, `_jobs`, `_public`, `_job_for`, `_run`, `COVER_ORIGIN`); `reader.correspondents` answers `job: null` | 216 / 5 |
| `src/learnloop_sidecar/handlers/epigraphs.py` | the module (`list_vault_epigraphs`) and its line in `handlers/__init__.py` | 48 / 0 |
| `src/learnloop_sidecar/handlers/reader_followups.py` | `reader.followups_plan` | 26 / 2 |
| `src/learnloop_sidecar/handlers/practice_index.py` | `get_practice_coverage` and its input model | 12 / 0 |
| `src/learnloop_sidecar/handlers/ingest.py` | `source_outcomes` | 15 / 0 |
| `src/learnloop_sidecar/handlers/app.py` | `rpc.health` | 6 / 0 |
| `apps/learnloop-tauri/src/api/client.ts` | the 42 client methods and the 18 type imports only they used | 101 / 2 |
| `apps/learnloop-tauri/src-tauri/src/commands.rs`, `main.rs` | 47 Tauri commands (41 passthroughs, 6 functions) and their handler-list lines | 130 / 5 |
| `src/learnloop/config/schema.py` | `LocksConfig` and `locks`, `merge_locked_facets`, `discrimination_min`/`_max`, `plan.pre_questions`, `target_error_type`, `lo_mastery_delta` (and its two `-0.05` defaults) | 36 / 4 |
| `src/learnloop/params/parameter_registry.py` | the `lo_mastery_delta` rule; the removed names in two rules | 5 / 1 |
| vault `_scripts/db_generate_reference.py`, `db_validate_reference.py` | the special cases for the removed keys | 19 / 2 |

Source total: 614 lines removed, 21 added (14 files). Tests: 253 lines removed, 56 added in place (17 files),
plus two new test files (`test_retired_config_keys_load.py`, `test_vault_report.py`) and `scripts/vault_report.py`.

Kept on purpose: every library function the deleted handlers called (`SC.cover`, `SC.section_learning_objects`,
`coverage_report`, `analyze_source_outcomes`, `recent_vault_epigraphs`, `RF.plan_ended_sessions`), each still used
elsewhere; the sidecar RPCs behind the deleted client methods (open items); the DTO types in `dto.ts` (exported, so
an unused one is not a type error; not on the strategy's list); doctor's raw-TOML warnings for `[locks]` and
`merge_locked_facets`.

## Tests removed, and seconds saved

Removed whole (timed once at the base, `pytest --durations=0`, serial):

| Test | Seconds |
|---|---:|
| `test_section_coverage_rpcs::test_a_pressed_check_judges_the_sections_los_then_correspondents_read_them` | 0.96 (0.74 of it the session's first vault setup) |
| `test_section_coverage_rpcs::test_a_failed_job_relays_an_openrouter_offer_keyed_by_curriculum_cover` | 0.36 |
| `test_section_coverage_rpcs::test_coverage_jobs_belong_to_the_vault_that_started_them` | 0.13 |
| `test_section_coverage_rpcs::test_a_vault_switch_during_a_job_keeps_nothing_in_the_old_vault` | 0.11 |
| `test_reader_followups::test_the_plan_rpc_refuses_with_the_switch_off` | 0.08 |
| `test_section_coverage_rpcs::test_a_check_with_models_off_starts_nothing` | 0.06 |
| `test_sidecar_epigraphs` (2 tests) | 0.03 |

About 1.7 s serial in all, or about 1.0 s once the shared first-vault setup is discounted. Small: these handlers
were thin, and their tests were too. Trimmed in place (assertions on a deleted call only): `test_practice_index_adapters::test_sidecar_rpcs`'
last two lines; `test_section_coverage_review::test_landing_f1_…` keeps its read-API refusal and loses the pressed
check's (renamed `test_landing_f1_the_read_api_refuses`); the switched-off loop in `test_section_coverage_rpcs`. Five
Reader test files seeded judged coverage through `curriculum.cover`; they now call `judge_section` in
`tests/section_coverage_fixtures.py`, which runs `SC.cover` over the section's LOs with the context's judge, as the
RPC's inline job did.

## The owner's script (strategy §2.6 D1)

`scripts/vault_report.py`, standalone (imports nothing from `learnloop`, so it reads a vault at any version),
read-only, over the vault directories named on the command line:

```
uv run python scripts/vault_report.py ~/learnloop-vaults/linear_algebra ~/learnloop-vaults/probability \
    ~/learnloop-vaults/arxiv_v2 ~/learnloop-retired/* [--json]
```

Per vault: the TOML's `algorithm_version`, the database's migration head, whether
`<database>.claim-fixes-activation` stands beside it (and the predecessor and target tags it names), and the keys
the TOML sets that a removal step drops: C3's (this step), C4's (a Codex provider named by a profile name, a
`codex_sdk`/`http` profile type, the active or fallback provider or a route; `ai.agent_harness_opt_in`; the retired
routes `field_llm_probability` and `proof_check`; the legacy `[codex]` table and its keys) and D7's (the map's 27
named kill switches at or below mvp-0.43, then the switches mvp-0.43 to mvp-0.55 name in `algorithm_versions.py`,
each printed with its tag). Every D7 name was checked to be a real config path at this tip. It prints names, tags
and one number; no value, id or learner text (the test plants sentinels in every value and finds none in the
output).

The database is opened with a `file:...?mode=ro` URI, and nothing is written, migrated, checkpointed or set. One
finding while building it: a read-only open of a WAL-mode database with no `-wal` creates empty `-wal` and `-shm`
files and leaves them (checked on a scratch database). So with no `-wal` beside a WAL-mode database the script adds
`immutable=1` (nothing is uncheckpointed, so the main file is the whole database, and no file appears); with both
companions present it reads them as they are; with a `-wal` and no `-shm` it does not open the database and says
so. Tests: `tests/test_vault_report.py` (a synthetic vault with every kind of key and a journal, a plain one, a
directory with no config, and a WAL-mode database read both checkpointed and with a writer holding the WAL; each
asserts the directory's files are byte-identical afterwards). It was never run on a real vault here; the owner runs
it.

## The owner's list

Nothing moved here: every candidate's claim held at this tip.

For the owner's decisions later (not this step's to act on):
- **The sidecar RPCs behind the 40 deleted client methods** stay. With the client methods and Tauri commands gone,
  none has a desktop caller; none is phone-allowed; none is an MCP tool. Some have other `src` users of the same
  name that are not RPC calls (`compare_sources` is also an AI tool name; `record_practice_usage` names the signal's
  writer). The Golden Path ones (`blueprint.register`, `golden_path.boundary_diff`, `diagnostic.*`,
  `practice_pool.*`) belong to C5. The rest (`reload_vault`, `get_recent_ingests`, `start_inventory`,
  `refresh_revision`, `set_goal_use_weight`, `get_placement_state`, `export_claims`, `purge_claims`,
  `get_remediation`, the 18 `reader.*` methods, `reader.followups`, `curriculum.path`, `curriculum.ready`,
  `curriculum.coverage_correct`, `workbench.get`) are candidates for a later removal or for the UX stage to wire
  up; several are features whose screen never landed (`reader.followups` is "Coming up", `curriculum.path` and
  `curriculum.ready` the deliverable's path and readiness, `reader.create_annotation` and `reader.annotation_history`
  the annotation API, `export_claims` and `purge_claims` the export and purge of the learner's claim events).
- **`get_config`** (the RPC) has no caller now that its Tauri command is gone.

## The UX list

No settings screen loses a backend: none of the removed calls had a production TS caller, and no removed config key
is shown on any screen (`git grep` over `apps/learnloop-tauri/src`, `src/learnloop_sidecar` and
`src/learnloop_mobile` for each key in snake and camel case finds none). For the UX stage, though: the RPCs listed
above are features with a backend and no screen (the annotation history, "Coming up" as a timeline, the
deliverable path and readiness, the claim events' export and purge), and `reader.correspondents` still answers a `job` key that
is now always `null` (the DTO in `dto.ts` never declared it).

## Proofs

All runs under `systemd-run --user --scope -p MemoryMax=5G -p MemorySwapMax=1G`, Python and CLI under an empty
`HOME`, `CODEX_HOME` and `LEARNLOOP_CONFIG_DIR`. No model call, no live vault.

| Proof | Result |
|---|---|
| `npm ci --prefer-offline` (offline cache sufficed) | installed |
| `npm run typecheck` | 0 errors |
| `npm test` (vitest, `--maxWorkers=4`) | 281 files, 2,846 tests passed, 60 s |
| `cargo check --offline --manifest-path src-tauri/Cargo.toml` (scratch target dir, deleted after) | finished, 0 warnings (an unused or missing command would warn or fail) |
| The phone's contract and allowlist tests (`tests/*mobile*`, 31 files, in the targeted run) | passed; the allowlist still has its 60 methods, `clear_session_checkpoint` and `get_attempt` included |
| `tests/test_desktop_rpc_contract.py` (TS `call` names ⊆ Tauri handlers = Rust declarations; every command reaches a registered method) | passed |
| Targeted pytest: 659 files (below), `-n 4` in four chunks | 12,091 passed, 43 skipped, 5 xfailed, 0 failed (4:45, 5:15, 3:24, 2:33) |
| `tests/test_retired_config_keys_load.py`, `tests/test_vault_report.py` | 2 and 3 passed |
| `lint-imports --no-cache` | 43 contracts kept, 0 broken |
| `ruff check` | all checks passed |

**The targeted list, and why it is not the selector's.** `scripts/affected_tests.py` on the diff falls back to the
whole suite, because two files are deleted (`handlers/epigraphs.py`, `tests/test_sidecar_epigraphs.py`: "the graph
no longer holds what imported it"); without the deletions it selects 1,300 files, since `config/schema.py` is a hub.
So the run used an explicit list: the selector's depth-1 selections for `handlers/correspondents.py` (532 files:
every test that loads the sidecar registry, which covers every edited handler and `handlers/__init__.py`),
`params/parameter_registry.py` (114), `learner/recall_calibration.py` and `ops/doctor.py`; every test file this
step edits or adds; `test_architecture`, `test_test_layout`, `test_cli_help_snapshot`, `test_cli_json`,
`test_effective_defaults_golden`, `test_desktop_rpc_contract`, `test_affected_tests`; every `tests/*mobile*` test;
every `test_*config*` and `test_*registry*` file. 659 files. A first run at `-n 6` was killed by the scope's OOM
killer at 36% (the machine was shared); the four-chunk `-n 4` rerun above is the result. The schema change's other
readers are covered by the step 0 grep (no test or source reads a removed key beyond the four edited tests), and
the full suite is the orchestrator's.

## Vault

- Regenerated once after the source commits with `_scripts/generate_all.py` (on `5b48f52eea`): 119 notes changed,
  mostly line anchors moving in `config/schema.py`, plus the Desktop notes for `client.ts`, `commands.rs` and
  `main.rs` (the step's named notes), the touched handler modules and the Configuration Field Catalog. No generator
  deletes a stale note, so the first run stopped at the db generator ("expected 80 config section notes, got 81");
  the step removes `Reference/Configuration/Fields/Config - locks.md` and
  `Reference/Modules/learnloop_sidecar/handlers/epigraphs.md` itself, then reran.
- Notes this step made false, fixed by hand: `Reference/Configuration/Configuration.md` and
  `Reference/Database/Database.md` stated 1196 effective leaves (now 1181: the 15 removed leaves); the first also
  said 79 top-level sections, which was already wrong (81 before, 80 now) and is now 80. No other hand-written note
  names a removed call or key.
- Validators: `module_validate` PASS; `desktop_validate` passed (330/330 TS/TSX, 6/6 Rust); `db_validate_reference`
  no errors after the two prose fixes (1,181 leaves, 80 section notes, 397 table notes); `validate_vault` passed
  (2,288 notes, 2,286/2,286 reachable).
- A second `generate_all.py` run on the committed references (`4267f6ea65`) changed nothing: a fixed point.

## Open items

- The 40 sidecar RPCs behind the deleted client methods, and `get_config` (above): left for the owner, C5 or a later
  removal.
- Unused exported DTO types in `dto.ts` (for example `ReaderFollowupsDto`, `PlacementStateDto`, `BoundaryDiffDto`,
  the reader request and annotation inputs): not on the strategy's list; a later sweep or the UX stage.
- `parameter_registry` rows for the removed decision paths stay in each vault (`refresh` never deletes, by design);
  `audit` keeps listing the active `lo_mastery_delta` rows as pending a certificate, as it did before.
- Whole-config hashes (`config_hash` in plans, receipts and reports) change value for a vault that does not set
  `[locks]`, as with any schema change; nothing compares them.
- `reader.correspondents`' always-null `job` key could go once the frontend contract is next revised.
- The owner runs `scripts/vault_report.py` over the live and retired vaults (D1's first step); C4 and D7 read its
  output.

## Unverified

- `scripts/vault_report.py` has never seen a real vault (by rule). Its key lists are this tip's: a key set under a
  spelling older than the compat layer's (`config/compat.py` normalizations) is reported only under the name it is
  written with.
- The full suite, durability lane and `--fresh-connections` run are the orchestrator's; this step ran the 659-file
  targeted list above.
- No desktop app launch (by rule): the TS side is proved by typecheck, vitest and the contract test only.

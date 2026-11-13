# Refactor D1: the oldest supported tag

Step D1 of arc D (`docs/specs/refactor_strategy_v3.md` §2.6), on branch `refactor/d1-floor`, based on main `16a9e3fd48`. A vault below the floor is refused where it is opened, with the vault's tag, the floor and the commands that bring it there; `learnloop upgrade` still opens it to upgrade it. Nothing is deleted.

**The floor is `mvp-0.58`**, the chain's head on main when this step started. It is one constant, `algorithm_versions.OLDEST_SUPPORTED` (set to `FIGURE_WAIT_ALGORITHM_VERSION`). The owner's Nov 12 report had the live vaults at mvp-0.54 to mvp-0.57; the owner has since upgraded all three to mvp-0.58, so the floor stands. A different floor is that one line; nothing else names it (the tests read the constant, and the record and notes say `mvp-0.58` in prose only: ADR-019, Algorithm Versions, this record).

The decision note is **ADR-019** "The oldest supported tag": the strategy named it ADR-018, but `Decisions/ADR-018 The Codex transport is retired.md` already holds that number on main (refactor C4). The strategy's ADR-019 for arc G's router decision moves to the next free number.

Rules held: no live model call; no migration; no identity pin moved; nothing deleted; no git tag created.

## 1. Step 0: where a vault is opened

| Door | How it opens the vault | Covered by |
|---|---|---|
| Every CLI command (`rebuild`, `rebuild --shadow`, `config effective`, `doctor`'s own load, offline review's source vault, ...) | `vault.loader.load_vault` (647 call sites in `src/` and `scripts/`; every command loads the vault before it opens the database) | the check in `load_vault` |
| Desktop sidecar `initialize` / `reload` | `SidecarContext.load` → `load_vault`, then `open_vault_repository` | `load_vault`; `initialize` maps the refusal to `SidecarError("vault_below_oldest_supported")` with the tag, floor and commands as details (unmapped it reached the desktop as `internal` with no message) |
| Phone host | `learnloop_mobile.host.attach` checks the schema and the journal without loading the vault; each request's worker then runs `SidecarContext.load_secondary` → `load_vault` | an explicit check first in `attach` (as the host's `SchemaMismatch`, exit 78), and `load_vault` per request |
| MCP server | `RemoteRuntime.attach` (`vault_sqlite_path` reads the config with `load_config`), then `runtime.vault()` → `load_vault` per request | `refuse_below_floor_as_mismatch` in `attach` (exit 78), and `vault()` maps a later refusal to `SchemaMismatch` |
| TUI, scripts | `load_vault` + `open_vault_repository` | `load_vault` |
| `learnloop doctor` | `run_doctor` loads the config itself, then with `--fix-state` migrates the database, recovers apply intents and facet actions, and only then calls `load_vault` (whose failure it reports as `vault:load_failed`) | an explicit check right after its config load, before any write |
| `learnloop rebuild-derived-state`, `rebuild --shadow` | `load_vault` | `load_vault`; a forced `--set algorithms.algorithm_version=` below the floor is refused in `build_candidate_config` |
| `learnloop upgrade` | each link's upgrade calls `load_vault` and `open_vault_repository` at the predecessor's tag | the allowance `version_floor.upgrading(root)`, entered by a decorator on the command for the vault it upgrades only |
| Offline review's scratch copy | a backup-API copy of the database upgraded under `UPGRADE_SCRATCH_COPY`; no vault config of its own | not a vault: its source vault was loaded (and checked) by the command |

Code below an entry point (`vault.repository.vault_repository(paths)`, the 26 upgrade modules' `load_vault` calls, services) holds a vault an entry point already loaded, so the `load_vault` check covers it. One check covers every door except the three that read the config without `load_vault` (doctor before its writes, the phone host's and the MCP server's attach), which call the same `version_floor.refuse_below_floor`.

**Activation journals.** `vault.repository.open_vault_repository` (every writing open, and `vault_repository` when a journal stands) calls `activation_journal.complete`, which runs the completer the CLI (`cli/runtime.py`) and the sidecar (`learnloop_sidecar/context.py`) install: `figure_wait_upgrade.complete_interrupted_activation`, the chain's latest, which completes its own journal and hands any other down the chain, link by link, to `claim_fixes_upgrade` (mvp-0.33). Every other attach (`Repository`, the MCP server, the phone host) refuses any journal (`refuse_if_interrupted`). The floor check sits in `activation_journal.complete`, before the completer: a journal whose `predecessor` is below the floor is refused with `BelowOldestSupported` (completing it would run that link's code), unless the upgrade command is completing it. A torn journal (unreadable) is left to the completion as before. `activation_journal` now imports `version_floor` (a leaf importing only `algorithm_versions`).

**Shadow rebuild's version forcing** (`substrate/shadow_rebuild.py`, `build_candidate_config`): any dotted assignment, `algorithms.algorithm_version` included, was applied and validated, so `--set algorithms.algorithm_version=mvp-0.9` replayed the vault at mvp-0.9 (the docstring's own example). Now a forced tag below the floor is a `ConfigOverrideError` (the CLI's `shadow_rebuild_failed`). Only a forced tag is judged; the baseline's tag was judged when the vault was loaded.

**`config/schema.py`'s `algorithm_version` default (`mvp-0.6`).** What it means: a config that names no version reads as the legacy model. Who relies on it:

- No real vault. `learnloop init` (and `bootstrap.create_vault`) writes the key from the template (`config/template.py`, `algorithm_version = "@ALGORITHM_VERSION@"`), and the upgrade writer only replaces an existing `algorithm_version = "<from>"` line (`ops/vault_upgrade._rewrite_algorithm_version` and `regrade_contract_upgrade.publish_algorithm_version` raise when it is missing), so no upgrade removes it. The owner's Nov 12 report shows a tag for every live and retired vault (the script reads the raw TOML and would print "unset").
- Production code, in one place that writes: `substrate/activities._algorithm_version(None)` falls back to `LearnLoopConfig().algorithms.algorithm_version`, and all four production callers of `open_administration` and `append_observation` (`attempts/grade_resolution.py`, `curriculum/golden_path_assessment.py` twice, `reader/reader_dialogue.py`) omit the tag, so every `activity_administrations` and `measurement_events` row is stamped `mvp-0.6` whatever the vault's tag. I found no reader of those two columns (ledger row D-23). `params/parameter_registry.py` builds `LearnLoopConfig()` three times for defaults of numeric leaves only (the tag is a string). `sim/runner.py` dumps a vault's own config.
- Identities: `tests/test_retired_config_identities.py` hashes `LearnLoopConfig()` and a keyless legacy TOML whole (`BASE_CONFIG_CONTENT_KEY`), and `tests/identity_pins_helpers.py`'s `legacy` config (also keyless) feeds its tag into the objective block's boundary identity and numeric seed.
- Tests: 118 `LearnLoopConfig()` constructions in 65 test files, plus test TOMLs written without the key.

## 2. The config default: required in the vault's file; the in-code default kept

Decided: **the key is required in a vault's `learnloop.toml`**, enforced at the door: `version_floor.refuse_below_floor` reads the tag only if the file set it (`"algorithm_version" in config.algorithms.model_fields_set`) and refuses a config that names none as below the floor (the message tells the owner to add `algorithm_version = "mvp-0.6"`, which is what such a vault is, and names the upgrade steps from there). The pydantic field keeps its `mvp-0.6` default, which now only ever serves configs built in code.

Why not the floor as default: a keyless file would then be served at the floor, silently skipping every upgrade, which is the "silent default flip" the field's comment forbids; and the default would move with every floor change, each time moving the activity stamps (persisted rows) and the keyless identities above. Why not a pydantic-required field: `LearnLoopConfig()` would stop constructing at 3 production and 118 test sites. Requiring it where a vault is read gives the property that matters (no vault is ever read at a tag it does not name) and keeps every identity's bytes: `test_identity_pins`, `test_retired_config_identities` and `tests/goldens/effective_defaults.toml` are unchanged.

What stays for later: in-code `LearnLoopConfig()` still means the legacy tag, so a test that builds one runs the legacy branch of any gate it reaches (strategy finding 3, for in-code configs). D4-D6 remove those gates; once they are gone the default is inert and can become the floor or go. The activity stamp is ledger row D-23.

## 3. The refusal

`learnloop/version_floor.py` (a leaf; imports only `algorithm_versions`):

- `is_below_floor(tag)`: a `mvp-0.N` tag with N below the floor's, or `None` (no tag named). A tag of another shape, or newer than this code knows, is not judged here (as before). Comparing numbers is the chain's order only while the chain counts up; `tests/test_version_floor.py` checks it does.
- `BelowOldestSupported(RuntimeError)`: `vault_root`, `tag`, `floor`, `journal` and `commands`; its message names all three parts, e.g. "`<vault>` is at mvp-0.57, older than mvp-0.58, the oldest version this LearnLoop opens. Upgrade it with `learnloop upgrade --vault <vault>`."
- `upgrade_commands(vault_root, tag)`: the one place that names the route. A vault older than the chain's first tag takes `--to mvp-0.7`, `--to mvp-0.8` and `--to mvp-0.9` first (the chained upgrade refuses anything older than mvp-0.9; the retired vaults at mvp-0.6 and mvp-0.8 need these). **D3 changes only this function** (to the `pre-floor` route).
- `upgrading(vault_root)`: the upgrade command's allowance, a context variable holding the one vault it upgrades. `cli/app.py` enters it with a decorator on the `upgrade` command (`_opens_the_vault_it_upgrades`), so the command's body and signature are unchanged (`tests/cli_surface.json` unchanged). The whole upgrade runs on the command's thread, so a context variable reaches every open it makes (shown on the real copies, §6).
- `may_open_below_floor(vault_root)`: the upgrade's vault, or the test allowance.

Judgment calls:
- The refusal is an exception, not a doctor issue: `run_doctor` raises it rather than reporting `vault:load_failed`, so `learnloop doctor` is refused like every other command (and before `--fix-state` writes).
- The CLI shows the typed exception as typer shows any uncaught exception (a traceback ending in the message), as it does today for `InterruptedActivation` and `ConfigLoadError`. Making it a clean exit needs a wrapper around the `learnloop` entry point; not done here.
- The desktop gets `vault_below_oldest_supported` from `initialize`; whether the desktop shows its message as written was not checked (no GUI allowed).
- The journal check refuses a journal whose `predecessor` is below the floor: with the floor at the chain's head, that is exactly an interrupted upgrade to the floor itself, whose config already names the floor. `learnloop upgrade` completes it (tested).

## 4. Tests that still open a vault below the floor

**The allowance.** `tests/helpers.py`'s `allow_below_floor(root)` is the suite's one allowance; it calls `version_floor.allow_below_floor_in_tests`, which nothing in `src/` or `scripts/` may name (`test_production_code_never_enters_the_test_allowance`, an AST scan, as `test_coordinated_migrations` pins `upgrade_allowance`). It registers the root (kept, for fixtures that outlive one test) and opens every vault for the rest of that test: such tests also open copies of their vault at roots nothing registered (their own copies, and production's scratch copies, e.g. an apply's dry run in a `learnloop-apply-*` temporary directory). `tests/conftest.py`'s autouse `end_below_floor_allowance` closes it after the test's background work has stopped. A process-wide flag, not a context variable, because the vault is opened later from worker threads. Child processes don't inherit it: the three tests that open their vault in another process register it there.

The smaller mechanism, a context variable like `upgrade_allowance`, failed first: worker threads start with an empty context. A per-root set alone failed next: hundreds of tests open copies of their vault.

**Who calls it.** `set_algorithm_version` and `pin_old_basic_vault` (through `_set_algorithm_version_at`, for a tag below the floor), so `create_placement_vault` and `create_daily_plan_vault` (d2c's functions, untouched) and every caller of the two are covered; `ux_phase1_support.set_config`, `serve_eligibility_helpers._at_version` and `followups_nov2_help_fold_helpers.hint_vault` for an old tag; the copies of the tracked fixtures (`fixtures/migration_head` is at mvp-0.6, `fixtures/mvp017_route_check_replay` at mvp-0.17); the golden-path fixture's builds (mvp-0.8) and the recall-calibration harness (mvp-0.6) (ledger D-24); two test-local rewriters in `test_receipt_derivation`/`test_receipt_exactness`; two `rewrite_algorithm_version` sites in `test_batch3_landing`; `simulation_helpers.build_sim_vault` (mvp-0.7) and one later test of `test_sim_teach_back`'s module-scoped sim vault; three child processes. The fixture copies and golden-path builds (17 files) were inserted by a mechanical script (`allow_below_floor(<destination>)` after each copy of a below-floor fixture, before each `build_golden_path_fixture(...)`); every other edit by hand.

**The count** (what D3, D5 and D7 must empty), from a census plugin over the whole landing selection that records each test the allowance let open a vault below the floor (not the upgrade command's own opens), plus the arc-close lane: **5,421 test cases (4,192 test functions) in 507 files.** That is far more than D2b's 45 pinned tests because the floor is at the head: every successor test's predecessor, every builder that pins a tag (`create_daily_plan_vault` mvp-0.14, `create_placement_vault` mvp-0.11, the reader follow-ups vault mvp-0.39, ...) and the tracked fixtures are below it. By the first matching kind (a file counts once):

| first matching kind | files | test cases |
|---|---|---|
| upgrade or successor test file (D3, D7) | 39 | 340 |
| uses `pin_old_basic_vault` (D3, D5) | 16 | 102 |
| daily-plan or placement builder at mvp-0.14 / mvp-0.11 (d2c, D2b part 2) | 109 | 1288 |
| tracked fixture, golden-path, sim or harness vault (D3, D-24) | 27 | 390 |
| another old tag, set by `set_algorithm_version` or a helper (D2b part 2, D7) | 316 | 3301 |
| **all** | **507** | **5421** |

`grep -rln "allow_below_floor\|set_algorithm_version\|pin_old_basic_vault\|create_placement_vault\|create_daily_plan_vault" tests/` names every file that can reach the allowance; the census below (Appendix) names the ones that do, with their counts. A test that stops opening an old vault leaves it by itself: rerun the census (a 30-line scratch plugin wrapping `version_floor.may_open_below_floor`, described here so D3 can rebuild it) to recount.

## 5. Fail-first evidence

`tests/test_version_floor.py` (23 tests) run against the base's `src/` and `migrations/` (a `git archive` of `16a9e3fd48`, plus only `version_floor.py` and the `OLDEST_SUPPORTED` line so the imports resolve, `-o pythonpath=` pointed at it): **12 failed, 10 passed** (the allowance-ends test was added later). The 12 are every refusal: each of the 8 doors, the keyless config, the journal, the forced shadow rebuild and the upgrade allowance's scope. The 10 that pass at base are the "keeps working" half: the upgrade upgrades and completes the journal, a vault at the floor or the head opens, a journal from the floor completes, the chain counts up, the commands, the AST scan. On the branch: 23 passed.

## 6. Proof on real shapes

The Nov 9 backup's three vaults, copied with `copy_tree_with_databases` under `fixtures-local/d1/` (skipping `probability/.learnloop/state.sqlite`), all at mvp-0.54, run through the empty-home wrapper with no model call. Counts and statuses only.

| | linear_algebra | probability | arxiv_v2 |
|---|---|---|---|
| refused at `config effective`, `doctor`, `rebuild --shadow` (tag, floor and command in the message) | yes, all three | yes | yes |
| `learnloop upgrade --vault` | exit 0, mvp-0.54 → mvp-0.58 | same | same |
| opens after | yes | yes | yes |
| doctor errors before (base code, read-only) → after | 2 codes → 1: `sqlite:migrations_missing` gone, `layout:missing_directory` stays | 3 → 2 (`migrations_missing` gone) | 3 → 2 (same) |
| new doctor codes after | none | none | none |
| shadow: facet / schedule / mastery rows changed | 0 / 0 / 21 | 0 / 0 / 18 | 0 / 9 / 36 |
| live database unchanged | yes | yes | yes |

The shadow rebuild is **not** identical, and the differences predate D1: the same copies upgraded and shadow-rebuilt with the base code give the same counts (21/18/36 mastery, 9 schedule on arxiv_v2). Read field by field: every mastery difference is the row's `algorithm_version` stamp (replay stamps the tag it ran at; the live rows carry the tag they were written at), with `logit_mean`/`logit_variance` equal to six decimals; the 9 schedule rows are `due_at` exactly one second earlier, interval ratio 1.0 (ledger D-25). `schedule_effects` reports those 9 as `due_dates_moved`, with queue due before = after. Warnings were unchanged codes. The copies are deleted.

## 7. Bug ledger rows added

D-23 (activity stamps say mvp-0.6), D-24 (two production harnesses build vaults below the floor: `learnloop goldenpath bootstrap` and `learnloop recall-calibration` now refuse their own scratch vaults), D-25 (the one-second replay difference). All due at arc D's close. The ids may collide with rows another parallel step adds; renumber at merge.

## 8. Docs

- `Decisions/ADR-019 The oldest supported tag.md` (new): the floor, the refusal at each door, the keyless rule, the journal and shadow rules, the restore route through `pre-floor` (created by the orchestrator at D3), the standing rule that the floor follows the vaults (strategy §2.18 L7: when the owner's `scripts/vault_report.py` shows every live vault at or past a tag, one chore step raises `OLDEST_SUPPORTED` and removes the gates and switches at or below it; the test listing such switches is D7's), and the test allowance.
- `Concepts/Algorithm Versions and Reproducibility.md`: a section "The oldest supported tag"; `version_floor.py` in its sources; the test listed.
- `Decisions/ADR-012 Freeze the compatibility substrate.md`: an "Amended" section (old vaults now means at or above the floor; shape readers stay).
- `Decisions/Design Decision Index.md`: ADR-019's row.
- References regenerated once after the source commits (§9).

## 9. Gates run

All under the empty-home wrapper, 5 GB scopes, `-n 4`, chunks of 100 files behind `flock /tmp/learnloop-fullsuite.lock`.

- **Every test file** (all 1,405, landing selection `-m "not arc_close"`), on `40b21c050e` with the census plugin: 30,752 passed, 104 skipped, 16 xfailed (the known strict xfails), 10 errors, all in the sim tests' fixtures (mvp-0.7 sim vault); fixed in `1a06e569c3`, then those three files: 17 passed. No failure otherwise. This covers `scripts/affected_tests.py`'s selection and every file this step edited, `test_identity_pins` (no pin moved, nothing `--write`), `test_retired_config_identities`, `test_architecture`, `test_test_layout`, `test_effective_defaults_golden` (golden unchanged), `test_cli_help_snapshot` (`cli_surface.json` unchanged), `test_e0_isolation` (the new module is in the experiments contract's list) and `test_module_catalog_inventory` (after the regeneration).
- **Arc-close lane** (`-m arc_close`, the 5 files that carry it): 24 passed, 36 xfailed (`test_ad23_sim`'s pre-registered strict xfails; `sim/ad_gates` opens no vault).
- How the failing set was found: a first sweep of 1,148 candidate files (those naming an old tag, a tag writer or a fixture) on `2d93f198bc`, then the other 257 files; about 350 failures and errors in the first sweep, all `BelowOldestSupported` (or the forced shadow refusal) from tests that open an old vault, none from a vault at the floor. Each was fixed by registering it (§4); no assertion was changed.
- `ruff check`: clean. `lint-imports --no-cache`: 42 kept, 0 broken. `scripts/check_gate_partition.py`: 31,002 collected, landing 30,942 + arc_close 60.
- Vault: the four validators pass (`db_validate_reference`, `desktop_validate`, `module_validate`, `validate_vault`). References regenerated after the source commits (`fb54687a63`: the new `version_floor` module note and the notes of the modules and config fields this step touched, plus `_generated.md`); a second run changed nothing; regenerated again after `1a06e569c3` (`2e2e591c6e`: only `_generated.md`'s rows), and a run after that changed nothing.
- Not run (the orchestrator's): the durability lane, `--fresh-connections`, vitest, the owner lane.

## 10. Open items

- **Everywhere the floor would also change** if the owner picks another tag: only `OLDEST_SUPPORTED`'s line. Prose that says `mvp-0.58`: ADR-019, the Algorithm Versions section, this record. `tests/test_version_floor.py` reads the constant (`BELOW` is the chain's tag before it). If the floor ever stops being a chain tag, `test_the_floor_is_a_tag_of_the_chain...` says so.
- **For dfb (mvp-0.59)**: nothing to do; the floor stays mvp-0.58 and `test_version_floor` follows `LATEST_ALGORITHM_VERSION`. Its successor tests at the predecessor mvp-0.58 are at the floor, so they need no allowance.
- **For d2c**: `create_placement_vault` and `create_daily_plan_vault` still pin mvp-0.11 / mvp-0.14 and reach the allowance through `set_algorithm_version`; moving them to the head empties a large part of the census.
- **D3** changes `version_floor.upgrade_commands` to name the `pre-floor` route, deletes the `upgrading` allowance's decorator with the upgrade command's chain if the command goes, and retires the upgrade/successor tests in the census. **D5/D7** retire the pinned old-path and predecessor tests. Each removal empties census rows; the allowance itself goes when nothing calls it.
- The in-code default (`mvp-0.6`) stays until D4-D6 remove the gates it reaches (§2).
- The owner-lane copies (`tests/owner_vaults.py`, `LEARNLOOP_OWNER_VAULTS`) are refused if made from a backup below the floor; copies made after the owner's upgrade are at mvp-0.58. Not run (owner lane).
- Not verified: the desktop's display of `vault_below_oldest_supported` (no GUI); the TUI door beyond `load_vault`; the arc-close lane.

## Appendix: tests that open a vault below the floor, by file

The census of §4 (test cases, parametrized ones counted), on `40b21c050e` plus the sim fix and the arc-close lane.

| file | test cases |
|---|---|
| `test_active_errors_overlay.py` | 1 |
| `test_ad1_codex_rereview_fixes.py` | 7 |
| `test_ad1_codex_review_fixes.py` | 11 |
| `test_ad1_fix_round4.py` | 5 |
| `test_ad1_fix_round5.py` | 8 |
| `test_ad1_fix_round6.py` | 6 |
| `test_ad1_fix_round7.py` | 2 |
| `test_ad1_fix_round8.py` | 10 |
| `test_ad1_fix_round9.py` | 4 |
| `test_ad1_outside_and_cli.py` | 8 |
| `test_ad1_send_guard.py` | 7 |
| `test_ad23_contract.py` | 17 |
| `test_ad23_fix_r5.py` | 7 |
| `test_ad23_fix_r6.py` | 3 |
| `test_ad23_fix_r7.py` | 5 |
| `test_ad23_fix_r8.py` | 13 |
| `test_ad23_fix_r9.py` | 4 |
| `test_ad23_fix_review.py` | 10 |
| `test_ad23_intent_compose.py` | 53 |
| `test_ad23_inversion.py` | 45 |
| `test_ad23_owner_decisions.py` | 5 |
| `test_ad23_pool_membership.py` | 42 |
| `test_ad23_successor.py` | 4 |
| `test_ad2_model.py` | 12 |
| `test_ad2_serving.py` | 30 |
| `test_ad3_monitoring.py` | 3 |
| `test_ad3_reading.py` | 2 |
| `test_ad3_relatedness.py` | 6 |
| `test_ad3_subject_view.py` | 5 |
| `test_adaptive_difficulty_ad1.py` | 12 |
| `test_ad_denial_log.py` | 10 |
| `test_ad_epoch.py` | 12 |
| `test_ad_guard_offer_receipts.py` | 5 |
| `test_ad_guard.py` | 37 |
| `test_ad_guard_reachable_reads.py` | 4 |
| `test_ad_projection.py` | 3 |
| `test_ad_protected_readings.py` | 154 |
| `test_ad_protected_tables.py` | 4 |
| `test_ai_compare.py` | 1 |
| `test_anti_double_count.py` | 6 |
| `test_arcb_close_fixes.py` | 5 |
| `test_assessment_contracts.py` | 5 |
| `test_assumed_known.py` | 38 |
| `test_attempt_chain_records.py` | 10 |
| `test_attempt_completion.py` | 4 |
| `test_attempt_content_state_race.py` | 6 |
| `test_attempt_content_state_successor.py` | 24 |
| `test_batch3_landing.py` | 22 |
| `test_block_chooser_interface.py` | 1 |
| `test_canonical_projection_rollout.py` | 3 |
| `test_capability_residual.py` | 3 |
| `test_causal_attribution_exhibit.py` | 2 |
| `test_causal_attribution_p0.py` | 3 |
| `test_causal_factor_deferral.py` | 14 |
| `test_causal_orchestrator.py` | 1 |
| `test_causal_p2_acceptance.py` | 16 |
| `test_causal_repair_mapping_p2.py` | 5 |
| `test_certification_cold_probe.py` | 25 |
| `test_characterization_assessment_exam.py` | 2 |
| `test_characterization_certification_ledger.py` | 4 |
| `test_chat_total_transport_deadline.py` | 1 |
| `test_cold_retry_reschedule.py` | 30 |
| `test_conjunctive_instruments.py` | 28 |
| `test_contract_frontier_coverage.py` | 2 |
| `test_contrast_pairs.py` | 12 |
| `test_coverage_denominator_boundary.py` | 6 |
| `test_curriculum_c0b_landing.py` | 2 |
| `test_curriculum_c1_codex_review_fixes.py` | 9 |
| `test_curriculum_c1_fix_round2.py` | 13 |
| `test_curriculum_c1_fix_round3.py` | 9 |
| `test_curriculum_c1_fix_round4.py` | 7 |
| `test_curriculum_c1_fix_round5.py` | 8 |
| `test_curriculum_c1_landing.py` | 7 |
| `test_curriculum_c1_plan_follows_path.py` | 37 |
| `test_curriculum_c1_round5_followups.py` | 6 |
| `test_daily_plan_build.py` | 14 |
| `test_daily_plan_composition.py` | 3 |
| `test_daily_plan_kill_switch.py` | 7 |
| `test_daily_plan_owner_decisions.py` | 6 |
| `test_daily_plan_reading.py` | 7 |
| `test_daily_plan_reentry.py` | 4 |
| `test_daily_plan_replay.py` | 2 |
| `test_daily_plan_review_regressions.py` | 28 |
| `test_daily_plan_rpc.py` | 10 |
| `test_data_capture_a1_prefilter.py` | 9 |
| `test_data_capture_a2_measurement.py` | 22 |
| `test_data_capture_a5_not_ready_floor.py` | 8 |
| `test_data_capture_a6_delayed_pick.py` | 8 |
| `test_data_capture_codex_rereview.py` | 24 |
| `test_data_capture_codex_review.py` | 8 |
| `test_data_capture_landing_review.py` | 24 |
| `test_data_capture_report.py` | 3 |
| `test_data_capture_successor.py` | 4 |
| `test_decider_landing.py` | 7 |
| `test_diagnosis_async_router.py` | 2 |
| `test_diagnosis_card.py` | 1 |
| `test_diagnosis_pipeline.py` | 2 |
| `test_diagnosis_replay.py` | 1 |
| `test_diagnostic_pack.py` | 10 |
| `test_discrimination_profiles.py` | 17 |
| `test_dl2_rw4b_keyed_pick_check.py` | 3 |
| `test_doctor.py` | 1 |
| `test_durable_promotion_arms.py` | 22 |
| `test_duration_estimates.py` | 2 |
| `test_embedding_store.py` | 1 |
| `test_error_hunt_items.py` | 13 |
| `test_evsi_router_composition.py` | 5 |
| `test_evsi_staged_binding.py` | 2 |
| `test_exam_protection_identity.py` | 4 |
| `test_exam_protection_landing.py` | 3 |
| `test_exam_protection.py` | 1 |
| `test_exam_protection_review.py` | 3 |
| `test_exam_session.py` | 3 |
| `test_facet_authority.py` | 3 |
| `test_facet_authority_rereview.py` | 10 |
| `test_facet_authority_review.py` | 10 |
| `test_facet_diagnostics_v03.py` | 6 |
| `test_facet_evidence_timeline.py` | 4 |
| `test_facet_identity_actions.py` | 28 |
| `test_facet_identity_composition.py` | 3 |
| `test_facet_outcome_view.py` | 28 |
| `test_facet_reword_confirm.py` | 33 |
| `test_facet_reword_confirm_review.py` | 8 |
| `test_facet_reword_paths.py` | 12 |
| `test_facet_rewords.py` | 6 |
| `test_facet_span_support.py` | 20 |
| `test_failure_triage_causal_gate.py` | 1 |
| `test_failure_triage.py` | 22 |
| `test_family_memory_projection.py` | 1 |
| `test_field_split_outcomes.py` | 1 |
| `test_field_workbench_signals.py` | 16 |
| `test_figures_prefetch_review_fixes.py` | 3 |
| `test_figure_wait_estimate.py` | 1 |
| `test_figure_wait_successor.py` | 5 |
| `test_followup_codex_review.py` | 80 |
| `test_followup_fg1c_codex_review.py` | 13 |
| `test_followup_fg1c_r1_exposure_independence.py` | 35 |
| `test_followup_fg1d_panel_read.py` | 8 |
| `test_followup_fg1d_probe_shadow.py` | 12 |
| `test_followup_generate_e2e.py` | 11 |
| `test_followup_journey.py` | 19 |
| `test_followup_live_shape.py` | 8 |
| `test_followup_next_matrix.py` | 71 |
| `test_followup_reserved_only.py` | 29 |
| `test_followup_rival_factor.py` | 22 |
| `test_followup_router.py` | 15 |
| `test_followups_batch5_lesson.py` | 7 |
| `test_followups_batch5_recap_dependencies.py` | 12 |
| `test_followups_batch5_recap_protection.py` | 7 |
| `test_followups_batch6_review_fixes.py` | 2 |
| `test_followups_batch6_router_report.py` | 2 |
| `test_followups_batch6_te1b_card.py` | 3 |
| `test_followups_batch7_prefetch_capped_resume.py` | 3 |
| `test_followup_single_use.py` | 8 |
| `test_followups_nov2_figure_provenance.py` | 1 |
| `test_followups_nov2_help_fold.py` | 6 |
| `test_followup_successor.py` | 3 |
| `test_followup_workflow.py` | 10 |
| `test_forced_withdrawal_records.py` | 12 |
| `test_forecast_receipts_landing.py` | 2 |
| `test_forecast_receipts.py` | 17 |
| `test_generated_item_gate.py` | 3 |
| `test_goal_certification_any_of.py` | 14 |
| `test_goal_frontier.py` | 1 |
| `test_goal_projection.py` | 1 |
| `test_golden_path_fixture.py` | 4 |
| `test_grading_cli.py` | 9 |
| `test_graph_editor_reads.py` | 8 |
| `test_held_grade_composition.py` | 5 |
| `test_held_grade_evidence.py` | 18 |
| `test_help_fold_attach_successor.py` | 19 |
| `test_hint_telemetry.py` | 1 |
| `test_hot_path_eligibility_cutover.py` | 3 |
| `test_hypothesis_marks_context.py` | 11 |
| `test_hypothesis_marks.py` | 35 |
| `test_identifiability_doctor.py` | 3 |
| `test_ih2_lessons_compete.py` | 40 |
| `test_ih2_offer_ceiling_and_unseen.py` | 23 |
| `test_ih2_one_open_offer.py` | 36 |
| `test_ih3_learner_preferences.py` | 16 |
| `test_ih3_phone_host.py` | 9 |
| `test_ih4_preferences_inform_router.py` | 34 |
| `test_ih5_successor.py` | 10 |
| `test_ih6_workbench_open_item.py` | 37 |
| `test_ih7_lesson_sources_follow_diagnosis.py` | 44 |
| `test_ih_lesson_candidate_after_cold_miss.py` | 28 |
| `test_ih_numeric_seed.py` | 12 |
| `test_instruct_handoff_ih0.py` | 1 |
| `test_instruct_handoff_ih1.py` | 6 |
| `test_instrument_servability_journeys.py` | 1 |
| `test_intent_checks.py` | 10 |
| `test_intent_codex_rereview.py` | 10 |
| `test_intent_codex_review.py` | 25 |
| `test_intent_exclusion.py` | 15 |
| `test_intent_fix_round4.py` | 30 |
| `test_intent_fix_round5.py` | 26 |
| `test_intent_fix_round6.py` | 44 |
| `test_intent_fix_round7.py` | 12 |
| `test_intent_goal_deadline.py` | 4 |
| `test_intent_orchestrator_rulings.py` | 9 |
| `test_intent_plan.py` | 11 |
| `test_intent_recall_targets.py` | 4 |
| `test_intent_resolution.py` | 22 |
| `test_intent_rpc.py` | 6 |
| `test_km1_doctor.py` | 5 |
| `test_km2_activation.py` | 7 |
| `test_km2b_consumer_rekey.py` | 56 |
| `test_km2_sim_gates.py` | 3 |
| `test_km2_write_path.py` | 9 |
| `test_km3_projections.py` | 6 |
| `test_km4_taxonomy.py` | 9 |
| `test_km5_sim_gates.py` | 2 |
| `test_laddered_stems.py` | 5 |
| `test_learner_blindness_relax.py` | 2 |
| `test_learner_pick_proposal.py` | 17 |
| `test_learner_protection_predicates.py` | 4 |
| `test_learner_report_superseded.py` | 57 |
| `test_learner_text_gaps_composition.py` | 7 |
| `test_learner_text_gaps_flow.py` | 13 |
| `test_learner_text_gaps.py` | 28 |
| `test_learner_text_gaps_rereview.py` | 18 |
| `test_learner_text_gaps_review.py` | 29 |
| `test_lp_claim_fixes.py` | 18 |
| `test_lp_claim_fixes_rereview.py` | 23 |
| `test_lp_claim_fixes_review.py` | 21 |
| `test_map_untested.py` | 3 |
| `test_mcp_c1a_landing.py` | 5 |
| `test_mcp_c1a_narrow.py` | 1 |
| `test_mcp_tools.py` | 1 |
| `test_measurement_corrections.py` | 2 |
| `test_measurement_rank.py` | 4 |
| `test_method_explicit_landing.py` | 2 |
| `test_method_explicit_upgrade.py` | 9 |
| `test_misconception_registry.py` | 7 |
| `test_mobile_two_process.py` | 1 |
| `test_mobile_v2_checks.py` | 4 |
| `test_mobile_v2_followup.py` | 6 |
| `test_mobile_v2_landing_fixes.py` | 8 |
| `test_mobile_v2_plan.py` | 13 |
| `test_mobile_v2_rereview_fixes.py` | 7 |
| `test_mobile_v2_review_fixes.py` | 12 |
| `test_mobile_v3_carried.py` | 4 |
| `test_mobile_v3_codex_review.py` | 15 |
| `test_mobile_v3_probes.py` | 11 |
| `test_mobile_v3_successor.py` | 5 |
| `test_mobile_v4_plan.py` | 6 |
| `test_mvp010_upgrade.py` | 5 |
| `test_mvp011_upgrade.py` | 8 |
| `test_mvp013_upgrade.py` | 8 |
| `test_mvp014_upgrade.py` | 7 |
| `test_mvp015_upgrade.py` | 7 |
| `test_mvp016_upgrade.py` | 7 |
| `test_mvp017_route_check_replay.py` | 3 |
| `test_mvp017_upgrade.py` | 8 |
| `test_mvp018_upgrade.py` | 7 |
| `test_mvp020_upgrade.py` | 8 |
| `test_mvp021_upgrade.py` | 9 |
| `test_mvp022_upgrade.py` | 9 |
| `test_mvp023_upgrade.py` | 10 |
| `test_mvp024_upgrade.py` | 10 |
| `test_mvp09_upgrade.py` | 3 |
| `test_narrative_rollback_overlap.py` | 4 |
| `test_observation_ledger_bulk.py` | 5 |
| `test_p0_cutover_mvp08.py` | 8 |
| `test_p0_projection_cutover.py` | 6 |
| `test_p2_acceptance.py` | 3 |
| `test_p2_leakage_suite.py` | 2 |
| `test_pfc_unassessed_readers.py` | 7 |
| `test_pfc_unverified_unassessed.py` | 190 |
| `test_placement_diagnosis_decides.py` | 32 |
| `test_placement_opening_probes.py` | 17 |
| `test_placement_report.py` | 5 |
| `test_placement_sidecar.py` | 8 |
| `test_placement_signals.py` | 5 |
| `test_placement_split_grades.py` | 10 |
| `test_placement_unevidenced_return.py` | 24 |
| `test_plan_determinism_landing.py` | 19 |
| `test_plan_determinism.py` | 12 |
| `test_plan_follows_path.py` | 16 |
| `test_planted_misgrade.py` | 1 |
| `test_pr4_superseded_claims_landing.py` | 4 |
| `test_practice_information.py` | 3 |
| `test_predictive_eig.py` | 1 |
| `test_probe_episodes.py` | 2 |
| `test_probe_robust_cutover.py` | 7 |
| `test_probe_targeting.py` | 4 |
| `test_projection_evidence_polarity.py` | 4 |
| `test_provenance.py` | 1 |
| `test_quick_add.py` | 2 |
| `test_quick_check.py` | 19 |
| `test_rbeq_pr2_landing.py` | 10 |
| `test_reader_ca1_as_printed.py` | 1 |
| `test_reader_ca2_astra_handoff.py` | 10 |
| `test_reader_ca2_astra_handoff_recovery.py` | 4 |
| `test_reader_ca2_codex_rereview.py` | 8 |
| `test_reader_ca2_codex_review.py` | 20 |
| `test_reader_ca2_fix_orchestrator.py` | 9 |
| `test_reader_ca2_one_ask.py` | 20 |
| `test_reader_ca5a_find_section.py` | 1 |
| `test_reader_cues.py` | 1 |
| `test_reader_dialogue.py` | 1 |
| `test_reader_digest_narrative.py` | 30 |
| `test_reader_followups.py` | 36 |
| `test_reader_followups_rereview.py` | 6 |
| `test_reader_followups_review.py` | 18 |
| `test_reader_followups_round3.py` | 6 |
| `test_reader_followups_round4.py` | 2 |
| `test_reader_followups_round5.py` | 3 |
| `test_reader_followups_round6.py` | 3 |
| `test_reader_followups_round7.py` | 3 |
| `test_reader_followups_round8.py` | 4 |
| `test_reader_followups_successor.py` | 16 |
| `test_reader_guidance.py` | 9 |
| `test_reader_question_note_id_placement.py` | 4 |
| `test_reader_recap_review.py` | 4 |
| `test_reader_recap_review_r2.py` | 2 |
| `test_reader_recap_review_r3.py` | 5 |
| `test_reader_rw1b_review.py` | 2 |
| `test_reader_rw3a_landing.py` | 5 |
| `test_reader_rw4b_admission_idempotency.py` | 5 |
| `test_reader_rw4b_fix6.py` | 10 |
| `test_reader_rw5d_p4b_teacher_visuals.py` | 21 |
| `test_reader_rw6b_landing.py` | 5 |
| `test_reader_rw6b_p2_landing.py` | 4 |
| `test_reader_workbench_rw2a.py` | 58 |
| `test_reading_paths.py` | 48 |
| `test_reading_step_switch.py` | 1 |
| `test_rebuild_equivalence.py` | 4 |
| `test_rebuild_equivalence_review.py` | 8 |
| `test_rebuild_orchestrator.py` | 6 |
| `test_recall_calibration.py` | 2 |
| `test_recall_coverage_interventions.py` | 2 |
| `test_receipt_derivation.py` | 2 |
| `test_receipt_exactness.py` | 4 |
| `test_recurrence_benchmarks.py` | 23 |
| `test_recurrence_commands.py` | 44 |
| `test_recurrence_deferral.py` | 3 |
| `test_recurrence_groups.py` | 11 |
| `test_recurrence_live.py` | 30 |
| `test_recurrence_merge_composition.py` | 5 |
| `test_reference_gate_imports.py` | 17 |
| `test_refusal_records.py` | 6 |
| `test_regrade_contract_successor.py` | 39 |
| `test_regrade_contract_upgrade.py` | 17 |
| `test_remaining_decision_records.py` | 4 |
| `test_required_method_authority.py` | 4 |
| `test_required_method_grading.py` | 19 |
| `test_required_method_reopened.py` | 4 |
| `test_required_method_rereview.py` | 4 |
| `test_required_method_round3_final_verify.py` | 10 |
| `test_required_method_round3.py` | 4 |
| `test_required_method_round3_rereview.py` | 4 |
| `test_required_method_round3_review.py` | 14 |
| `test_residual_diagnostics.py` | 2 |
| `test_ro0_codex_review.py` | 14 |
| `test_ro0_codex_verify.py` | 16 |
| `test_ro0_gate.py` | 5 |
| `test_ro0_report.py` | 3 |
| `test_ro0_row10_cold_timing.py` | 3 |
| `test_ro0_row12_trajectory.py` | 3 |
| `test_ro0_row3_ask_availability.py` | 7 |
| `test_ro0_rows7_8_sessions.py` | 4 |
| `test_ro0_rows9_13_decision_state.py` | 13 |
| `test_ro1_availability.py` | 7 |
| `test_ro1_availability_reads.py` | 21 |
| `test_ro1_interval_factor.py` | 7 |
| `test_ro1_projection.py` | 17 |
| `test_ro1_self_report.py` | 3 |
| `test_ro1_successor.py` | 5 |
| `test_ro1_upgrade_report.py` | 6 |
| `test_ro2_ad_document_ir.py` | 6 |
| `test_ro2_ad_raw_document_reads.py` | 3 |
| `test_ro2_history_forecaster.py` | 5 |
| `test_ro2_history_protection.py` | 8 |
| `test_ro2_history_resolve.py` | 11 |
| `test_ro4_codex_review.py` | 8 |
| `test_ro4_goals.py` | 4 |
| `test_ro4_objective_serving.py` | 6 |
| `test_ro4_successor.py` | 3 |
| `test_ro4_trace_report.py` | 3 |
| `test_ro5_calibration.py` | 5 |
| `test_ro5_checks.py` | 6 |
| `test_ro5_codex_rereview.py` | 5 |
| `test_ro5_codex_review.py` | 4 |
| `test_ro5_landing.py` | 10 |
| `test_ro5_picks.py` | 3 |
| `test_ro5_stop_coin.py` | 3 |
| `test_ro5_successor.py` | 4 |
| `test_ro6_codex_rereview.py` | 2 |
| `test_ro6_codex_review.py` | 2 |
| `test_ro6_landing.py` | 4 |
| `test_ro6_serving.py` | 5 |
| `test_ro6_successor.py` | 5 |
| `test_ro6_tail_data.py` | 7 |
| `test_rofu_ad_latent.py` | 1 |
| `test_rofu_ad_link.py` | 3 |
| `test_rofu_carried.py` | 5 |
| `test_rofu_generator_switches.py` | 12 |
| `test_rofu_learning.py` | 5 |
| `test_rofu_monotone.py` | 3 |
| `test_rofu_review_draw.py` | 3 |
| `test_rofu_speed.py` | 3 |
| `test_rofu_successor.py` | 14 |
| `test_rofu_switch_key.py` | 12 |
| `test_rofu_weeks.py` | 1 |
| `test_roles_switch_off.py` | 1 |
| `test_rospeed2_connections.py` | 8 |
| `test_rospeed2_section_map.py` | 16 |
| `test_rospeed_ad_link.py` | 1 |
| `test_rospeed_join.py` | 7 |
| `test_router_card.py` | 9 |
| `test_router_card_reading_gaps.py` | 7 |
| `test_router_failure_records.py` | 8 |
| `test_router_g1_feasibility.py` | 8 |
| `test_router_g3_propensity.py` | 2 |
| `test_router_g4_restraint.py` | 12 |
| `test_router_g7_fallback.py` | 3 |
| `test_router_offer_log.py` | 2 |
| `test_router_presentations.py` | 6 |
| `test_router_probe_ties.py` | 9 |
| `test_router_r1_composition.py` | 8 |
| `test_router_r2a_landing.py` | 4 |
| `test_router_r2a_serving.py` | 10 |
| `test_router_r2b_agreement.py` | 3 |
| `test_router_r2bc_landing.py` | 6 |
| `test_router_r2b_requests.py` | 1 |
| `test_router_r2b_serving.py` | 20 |
| `test_router_r2c_retrieval.py` | 8 |
| `test_router_r2c_teach_back.py` | 6 |
| `test_router_reader_activity.py` | 18 |
| `test_route_rules_in_grader.py` | 26 |
| `test_router_why_copy.py` | 1 |
| `test_rw5c_switch_off.py` | 1 |
| `test_rw7b_codex_review_fixes.py` | 10 |
| `test_rw7b_fix_round2.py` | 5 |
| `test_scoreboard.py` | 1 |
| `test_serve_eligibility.py` | 17 |
| `test_serve_eligibility_review.py` | 23 |
| `test_sg_slip_vs_gap.py` | 24 |
| `test_sg_successor.py` | 7 |
| `test_shadow_rebuild.py` | 4 |
| `test_sidecar_adjudication.py` | 7 |
| `test_sidecar_close_cancels_jobs.py` | 2 |
| `test_sidecar_contract.py` | 1 |
| `test_sidecar_knowledge_model.py` | 4 |
| `test_sim_goals.py` | 3 |
| `test_sim_probe_validation.py` | 1 |
| `test_sim_teach_back.py` | 3 |
| `test_simulation.py` | 4 |
| `test_slate_record.py` | 5 |
| `test_source_first_needs.py` | 17 |
| `test_source_set_synthesis.py` | 1 |
| `test_stuck_prompt_composition.py` | 6 |
| `test_stuck_prompt.py` | 46 |
| `test_stuck_prompt_replay.py` | 4 |
| `test_subject_registry.py` | 4 |
| `test_success_head_cli.py` | 8 |
| `test_t6_followup_composition.py` | 2 |
| `test_te3a_lesson_opportunity.py` | 16 |
| `test_te3a_successor.py` | 5 |
| `test_te3b_clock.py` | 1 |
| `test_te3b_codex_review.py` | 9 |
| `test_te3b_features.py` | 1 |
| `test_te3b_offers.py` | 9 |
| `test_te3b_population.py` | 2 |
| `test_te3b_successor.py` | 5 |
| `test_teach_back.py` | 5 |
| `test_teacher_exam_question_guard.py` | 33 |
| `test_teacher_te0_confidence_events.py` | 3 |
| `test_teacher_te0_review_fixes.py` | 3 |
| `test_teacher_te1b_landing_r2.py` | 9 |
| `test_teacher_te1b_rereview_fixes.py` | 5 |
| `test_teacher_te1b_review_fixes.py` | 7 |
| `test_teacher_te1b_suggestions.py` | 21 |
| `test_teacher_te1_curriculum_c4.py` | 3 |
| `test_teacher_te1_lesson.py` | 17 |
| `test_teacher_te1_review_fixes.py` | 30 |
| `test_teacher_te1_successor.py` | 9 |
| `test_teacher_te1_weight.py` | 10 |
| `test_teacher_te2_landing_r1.py` | 2 |
| `test_teacher_te2_lessons.py` | 13 |
| `test_teacher_te2log_activity.py` | 6 |
| `test_teacher_te2log_episodes.py` | 23 |
| `test_teacher_te2log_node_held.py` | 5 |
| `test_teacher_te2log_receipt.py` | 3 |
| `test_teacher_te2log_report.py` | 4 |
| `test_teacher_te2_probes.py` | 12 |
| `test_teacher_te2_review_fixes.py` | 15 |
| `test_teacher_te2_sidecar.py` | 2 |
| `test_teacher_te2_successor.py` | 5 |
| `test_tier1_decider.py` | 7 |
| `test_today_headline.py` | 3 |
| `test_unresolved_cause_gate.py` | 6 |
| `test_ux_phase1_landing.py` | 3 |
| `test_ux_phase1_round2_rereview.py` | 2 |
| `test_ux_phase1_round2_review.py` | 7 |
| `test_ux_phase3_today.py` | 4 |
| `test_ux_phase4_feedback.py` | 45 |
| `test_ux_phase4_landing.py` | 6 |
| `test_value_candidates.py` | 3 |
| `test_version_floor.py` | 1 |
| `test_voi_forecasts.py` | 4 |
| `test_voi_merge_composition.py` | 8 |
| `test_voi_stopping.py` | 34 |
| `test_voi_v2.py` | 22 |
| `test_why_cases.py` | 2 |
| `test_why_reader.py` | 5 |

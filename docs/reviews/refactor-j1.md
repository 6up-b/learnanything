# Refactor J1: the table review list

Step J1 of `docs/specs/refactor_strategy_v3.md` (§2.5, run inside arc C because the removals name the readers). Branch `refactor/j1-table-review`, based on main `c828893847` (arc C's batch: C1, C3 and C4). Commits: `7802439024` (script, test, role correction), `f930ecb2cf` (the review list and the vault notes), `ee3627f304` (references regenerated) and this record.

**What it delivers.** `scripts/table_review.py`, the tracked list `docs/reviews/table-review-2026-11-11.md` (names and code facts only), the private counts under the gitignored `fixtures-local/table-review/`, and one role correction: `practice_item_state` moves from COMPAT to WORKFLOW. **No table is decided or dropped.**

**Tip read.** All code facts are at `c828893847` plus J1. C2 and C5 were in flight on other branches. Rather than guess at them, the script reruns its scan as if each step's modules were deleted, and marks the 17 tables whose class would change "re-check after C2" or "re-check after C5" (group F of the list).

## Step 0

J1 deletes nothing, so step 0 covers two things: the role correction, and the claim behind each class.

### What each role changes

Every reader of `db/table_roles.py` in `src/`, `apps/`, `scripts/` and the vault's `_scripts/`, from an import and attribute grep (`table_roles`, `TABLE_ROLES`, `TableRole`, `tables_for_role`, `role_for_table`, and the role values as strings). No `importlib` or string dispatch names the module.

| Reader | Acts on | Effect of a role |
|---|---|---|
| `substrate/rebuild_orchestrator.py:251` (`validate_replayer_registry`) | DERIVED | needs exactly one replayer owner |
| `db/repositories.py:6098` (`clear_derived_projection_tables`) | DERIVED | the only tables the umbrella may clear |
| `substrate/dataset.py:670` (`_export_snapshot`) | RAW_LEDGER, RECEIPT (+ `_CAPTURED_WORKFLOW_TABLES`) | exported as `<table>.jsonl` |
| `db/stores/collection.py:16`, `:33` (`_check_evidence_reference`) | RAW_LEDGER, RECEIPT | allowed as adjudication evidence |
| `goals/goal_series_store.py:30`, `ops/debug_time_store.py:17` | any | registration check only |
| vault `_scripts/db_generate_reference.py`, `db_validate_reference.py:189` | COMPAT | prose; a COMPAT table needs a status classification |

COMPAT and WORKFLOW appear in none of the acting sets, so a move between them changes no output. DERIVED changes rebuild. RAW_LEDGER and RECEIPT change the dataset export and what evidence accepts.

| Table | Evidence | Verdict |
|---|---|---|
| `practice_item_state` | Written by every attempt (`db/repositories.py:5962`, `:5964`) and read by the objective (`daily_plan/objective_inputs.py:126`). Per-LO replay deletes and re-derives it but keeps `active` (`substrate/replay.py:327-336`), which state sync, retirement and the probe lifecycle set outside the attempt ledger. Rows are overwritten. | **WORKFLOW** (changed). DERIVED would lose `active` in a wholesale clear. RAW_LEDGER or RECEIPT would add an overwritten projection to export and evidence. |
| `hypothesis_sets` | Insert-only (`db/repositories.py:7698`). Written by four probe paths, read back at 11 call sites, FK parent of `causal_probe_candidates`, rows in 3 of 3 copies. | **Owner's list.** RAW_LEDGER is honest, but it adds `hypothesis_sets.jsonl` to the dataset export and admits the table as evidence: a change at a fixed input. Rebuild is unchanged. Only the vault's functionality status was corrected to "active". |

### The classes

A class claim is only as good as the scan behind it. The method and its limits are in the review file. In short: SQL in string constants and f-strings, constants resolved across modules, helpers that take a table as a parameter, name reachability from module-level seeds (registries, Typer decorators, `METHOD_REGISTRY`, `__all__`, decorated functions, dunders), and frontend reach through `METHOD_REGISTRY`'s strings. Each dead and retired row was hand-checked by grep at this tip:

- Every listed unreached site is in a function that nothing in `src/` names. These are the `Repository` methods C1 left because tests use them, plus `scheduling/controller_store.py`, `kinship_feature.py` and `shadow_components.py`, which are C6's candidates.
- No replayer owns a dead or retired table. `lo_probe_state` is read by `find_record` (`db/repositories.py:18467`), which is reached.
- No upgrade module names a dead or retired table.

## What was deleted

Nothing: J1 lists, and the owner answers. Lines: +1,735 / -11 over 9 files before the references, most of it the script (914 lines) and its test (260).

## Tests removed, and seconds saved

None removed, 0 s saved. Added: `tests/test_table_review.py` (6 tests) and one test in `tests/test_table_roles.py`.

## Proofs

- **The role move changes no output.** On fresh backup-API copies of all three vaults, I ran `learnloop rebuild --shadow --json` and `learnloop dataset-export` before and after the change. Only the run's freshly minted ids and timestamps were ignored. The shadow reports are identical on all three: `arxiv_v2` facet 23 unchanged, mastery 29 changed / 7 unchanged, schedule 9 changed / 41 unchanged; `linear_algebra` 76 / 21 / 99; `probability` 2 / 18 / 77. These deltas are the copies' existing mvp-0.54-versus-tip differences, the same both times. Export artifacts are identical, 270 files each on `linear_algebra` and `probability`; neither run exports `practice_item_state`. `test_the_role_consumers_treat_compat_and_workflow_alike` pins the sets.
- **The script.** Read-only (`mode=ro&immutable=1`; the test hashes the copy before and after and finds no companion file). Deterministic (two full runs give byte-identical tracked and JSON output). It refuses `~/learnloop-vaults`, `~/learnloop-retired`, `~/learnloop-books` and `~/learnloop-backups`. A full run takes about 54 s: four source scans plus three copies.
- **Privacy.** The tracked list carries no date, count, id or text from the vaults, only "k of 3" (148 tables at 0 of 3, 82 at 1, 58 at 2, 107 at 3) and the two tables absent from every copy.

- **Gates (targeted, no full suite).** The selector chose 1,283 test files from `table_roles.py`'s importers, effectively the whole suite, so an explicit list ran instead: `test_table_review`, `test_table_roles`, `test_architecture`, `test_test_layout`, `test_cli_help_snapshot`, `test_cli_json`, `test_effective_defaults_golden`, the role consumers' tests (`test_rebuild_orchestrator`, `test_shadow_rebuild`, `test_collection_dataset`, `test_diagnosis_adjudication`, `test_sidecar_adjudication`, `test_goal_series`, `test_debug_advance`), `practice_item_state`'s rebuild and replay tests (`test_card_lineage`, `test_doctor`, `test_attempt_content_state_successor`, `test_daily_plan_replay`, `test_diagnosis_replay`, `test_approach_map_replay`), and the vault's `test_generated_provenance` and `test_module_catalog_inventory`. **264 passed, 3 skipped in 78 s at `-n 2`** in a 5G scope. `lint-imports`: 42 contracts kept, 0 broken. `ruff check`: clean. Validators: `db_validate_reference` (no errors), `module_validate`, `desktop_validate` and `validate_vault` (2,281 notes) all pass. `test_table_review.py` takes about 2 s.

## The owner's list

The review file's groups A-G, in brief:

- **A. Dead (11, all empty):** `controller_constraint_manifests`, `controller_prequential_reports`, `controller_outcome_windows`, `familiarity_kernel_events`, `familiarity_kernel_features`, `shadow_component_events`, `angle_inventories`, `family_evidence_cap_policies`, `progression_policy_versions`, `source_exam_profiles`, `learner_theta`.
- **B. Retired but still read (9, all empty):** `activity_card_authoring`, `activity_family_authoring`, `activity_pattern_versions`, `activity_patterns`, `activity_surface_authoring`, `familiarity_kernel_models`, `soft_kinship_features`, `lo_probe_state`, `source_locator_schemes`.
- **C. COMPAT written behind a runtime gate (4, all empty):** `elicitation_events`, `evidence_facet_recall_state`, `facet_uncertainty`, `learner_state_beliefs`. Their writes would have to go first.
- **D.** `hypothesis_sets`: approve RAW_LEDGER?
- **E.** C1 took the last SQL of `controller_constraint_manifests` and `controller_prequential_reports`. C1, C3 and C4 removed 40 SQL sites in 31 tables, and no class changed.
- **F. Re-check after C5 (16) or C2 (1):** the diagnostic-pack, golden-path, practice-pool, task-blueprint and `p2_ladder_*` tables, `target_exemplars`, and `lapse_episodes`.
- **G. Write-only (5, information):** `card_lineages`, `controller_candidates`, `diagnostic_pack_events`, `goal_contract_drafts`, `retirement_records`.

FK chains tie some answers together: `progression_policy_versions` → `activity_family_authoring`; `activity_patterns` → `activity_pattern_versions` → the card and family authoring tables; `familiarity_kernel_models` → the two kernel tables.

## The UX list

Empty: no settings screen loses a backend.

## Vault

- `Reference/Database/Table Roles.md`: Compat section (9 tables, `hypothesis_sets` live despite its role, `practice_item_state` moved) and Workflow section.
- `Maps/LearnLoop Pipeline Map.md`: line 361.
- `_scripts/db_generate_reference.py` and `db_validate_reference.py`: `hypothesis_sets` is "active", not "legacy-preserved".
- References regenerated once with `generate_all.py` after the source commits (11 generated notes, 397 table notes, `uncommitted_inputs: 0`). A second run changed nothing: a fixed point.
- The rest of Table Roles' counts (schema head 165) and the Data and State Map's head-165 table were already stale. They're left for the vault rewrite (§5).

## Open items

1. The owner answers groups A-D and F. J2-J4 drop only what is approved, after the code goes.
2. `learnloop dataset-export` fails on the `arxiv_v2` copy at this tip, before and after J1: `TypeError: Object of type bytes is not JSON serializable`. Two exported tables hold BLOB values there: `decision_state_receipts.state_z` and `prefilter_payloads.content_z`. This is unrelated to J1, but dataset export is broken for that vault.
3. After C2 and C5 land, rerun `scripts/table_review.py` to settle group F. The vault copies were deleted after this run; make fresh ones from the backup with `copy_tree_with_databases`. The private output stays in this worktree's `fixtures-local/table-review/` (`table-review.json`, `table-review-private.md`).
4. The four other COMPAT tables in group C keep their role until the owner rules.

## Unverified

- "Tolerates absence" is a heuristic over the reader's own and enclosing functions. A caller's guard is missed.
- Name reachability can't see runtime gates (group C) and over-approximates through name collisions, so a "reached" reader may be dead in practice.
- Retired vaults aren't in the Nov 9 backup, so "empty" covers only the three live vaults.

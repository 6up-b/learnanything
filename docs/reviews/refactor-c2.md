# Refactor C2: registry-tied modules

Arc C's second step ("delete what's proven dead"), `docs/specs/refactor_strategy_v3.md` §2.5. Branch
`refactor/c2-registry-modules`, based on `6629597573` (main `9841893fe0` plus the arc C batch C1 + C3 + C4, merged and
regenerated). C5 (Golden Path) runs in parallel from the same base and also edits `scheduling/open_world_gate.py`;
C2 touches only the `predictive_targets` entry there.

## Step 0: the evidence at `6629597573`

Written and committed before any deletion.

### Method

- **`c2_closure.py`** (`docs/reviews/artifacts/refactor-c2/`) builds the same graph as C1's `c1_closure.py`: AST
  import edges over `src/` (module-level and function-local imports, `TYPE_CHECKING` included) plus a string edge for
  every string constant naming a module (dotted, short, or as the `src/learnloop/...py` path `MODULE_INVENTORY`
  uses). The full graph reaches every candidate by construction, because `MODULE_INVENTORY` names them. So it also
  walks a pruned graph: the string edges from `params.parameter_registry` and `scheduling.open_world_gate` into a
  candidate are dropped, and so are the edges from one candidate into another. A candidate counts as reached only
  if something outside the set imports it. Root sets: every entry point (`learnloop_sidecar`, `learnloop_mobile`,
  `learnloop_mcp`, `learnloop.cli`, `learnloop.tui`), the replay, rebuild and upgrade roots (`rebuild_orchestrator`,
  `shadow_rebuild`, `canonical_projection`, `attempts.attempts`, `daily_plan.engine`, `ops.doctor`, `db.migrate`),
  and the plan path (every module under `daily_plan`, `router` and `router_objective`).
- **Text search** over `src/` (all four packages), `tests/`, `scripts/`, the vault's `_scripts/`, `apps/` (TS, TSX,
  Rust, the phone's JS), `pyproject.toml`, `fixtures/`, `migrations/`: each module name, each public name, each
  registry path.
- **Dynamic dispatch:** every `import_module`, `__import__` and `importlib` site in `src` (`ai/__init__`'s export
  table, `scoreboard`'s producer, `valuation`'s named gaps, the fetchers, the PF sandbox, the registry,
  `open_world_gate`): only the registry and `open_world_gate` name a candidate. No `METHOD_REGISTRY` entry, Typer
  command, Tauri command or phone/MCP method names one.

### The closure

1,291 modules, 15,784 edges. Full graph: the entry points reach 1,287, the replay roots 1,119, the plan path 1,122,
and every candidate is reached in all three (through the registry). Pruned graph: 1,281 / 1,113 / 1,116, and no
candidate is reached from any root set.

| Module | Lines | Registry entries (decision / structural) | Importers in `src` | Pruned reach (entry / replay / plan) | Frontend, phone, MCP | Tests | Verdict |
|---|---:|---|---|---|---|---|---|
| `substrate/compat/substrate_cutover.py` | 720 | 0 / 2 (`P1_SCHEDULER_ALGORITHM_VERSION`, `PURPOSE_ADAPTERS_LIVE_FROM`) | registry only (a comment in `controller_cutover.py` names it) | no / no / no | none | `test_substrate_cutover.py` (all), `test_journey6.py` | delete |
| `scheduling/progression_policy.py` | 94 | 2 / 1 (`SIBLING_SUCCESS_SHRINKAGE`, `ORTHOGONAL_NEXT_DELAY_DAYS`; `PROGRESSION_POLICY_SCHEMA_VERSION`) | registry, `progression.py` | no / no / no | none | `test_progression.py`, 2 tests and a fixture line in `test_activity_contract_extensions.py` | delete |
| `scheduling/progression.py` | 341 | 3 / 0 (`MAX_EFFECTIVE_MASS_PER_CLUSTER`, `DIMINISHING_MASS_DECAY`, `POST_LAPSE_FOLLOWUP_DAYS`) | registry only | no / no / no | none | `test_progression.py`, `test_journey6.py`, `test_laddered_stems.py` (as the caller of `familiarity.evidence_cap_grouping`) | delete |
| `scheduling/reentry_adapter.py` | 287 | 2 / 0 (`REENTRY_QUESTION_CAP`, `REENTRY_RECOVERABLE_BAND`) | registry only | no / no / no | none (its docstring's "existing Today/continue entry points expose this adapter" is false: none does) | 3 tests in `test_reentry_short_session.py` | delete |
| `scheduling/predictive_targets.py` | 165 | 0 / 1 (`TARGET_SET_SCHEMA_VERSION`) | registry, `open_world_gate` (`_has_attrs(..., ("__name__",))`), `reentry_adapter` | no / no / no | none (`probe_episodes`' `predictive_targets` field and `voi_stopping`'s `getattr(eligible, "predictive_targets")` are a different, live thing of the same name) | `test_predictive_targets.py`, `test_architecture`'s dynamic-attribute list | delete |
| `scheduling/short_session.py` | 117 | 0 / 0 (in `MODULE_INVENTORY` with no entry) | registry only | no / no / no | none (`StartScreen.tsx`'s "short_session" string is the scheduler's mode label, `scheduler.short_session_minutes`) | 4 tests in `test_reentry_short_session.py` | delete |

**`open_world_gate._has_attrs`** imports nine modules by name at this tip: `administration_adapters`,
`golden_path_assessment`, `pattern_ladder`, `annotations`, `salience_firewall`, `constraint_engine`, `staged_policy`,
`predictive_targets`, `dispersion`, `interleaving` (and `kinship_feature` by an ordinary import). Only
`predictive_targets` is C2's. Its sub-check is a presence check (`("__name__",)`): the module was never wired into
the live EIG, which builds its own target pool in `probe_episodes`. Removing the sub-check leaves condition 5's
`met` unchanged (it still needs `constraint_engine`, `staged_policy` and the `controller_shadow_predictions`
table) and drops `predictive_targets=True; ` from its detail string. The gate is reached only from `learnloop
controller open-world-gate` (C6's CLI group, which stays); the overall gate is unmet before and after (condition 6,
the un-admitted kinship kernel). `golden_path_assessment` and `pattern_ladder` are left to C5.

**What reads their data.** `progression_policy` writes `progression_policy_versions`; `progression` reads
`angle_inventories` and writes `family_evidence_cap_policies` and `lapse_episodes`; `substrate_cutover` writes
administrations, exposures, observations and card state through `administration_adapters`, and
`derived_state_rebuilds` rows of scope `activity_card_state`; `reentry_adapter` and `short_session` write controller
decisions through `staged_policy.decide`; `predictive_targets` writes nothing. Every one of those tables has another
reader, a replayer that doesn't need these modules, or no reader at all (the first four are read only by these
modules and `Repository`); no replayer or upgrade imports a candidate. Tables stay in place for J1.

### Registry: what a stored row for a removed spec does

- **`refresh`** loops over `decision_specs()` (the code registry) and upserts one row per spec. It never deletes and
  never reads a row whose path has no spec, so a stored row for a removed spec stays as it was: readable, with its
  last value hash, status and lifecycle.
- **`freeze_manifest`** calls `refresh` and then reads every stored `decision` row from `parameter_registry`. A stale
  row is included with its stored value hash. So on an existing vault the next manifest still lists the removed
  paths, unchanged; only a vault created after C2 (no stale rows) freezes a manifest without them. The 45 frozen
  manifests in each copy are immutable rows and stay as they are.
- **`audit`** checks code specs against module constants (both lose the same names together) and, per vault, every
  stored active decision row's coverage certificate: a stale row is listed under `active_pending_certificate`, a
  warning that doesn't flip `clean`, exactly as it was before C2 (no copy has a certificate for these paths).
- **`doctor`** doesn't read `parameter_registry` at all (`ops/doctor.py` never names it).
- **`registry list` / `show`** call `refresh` and print stored rows: a stale row is listed and shown.
- **`_resolve_module_constant`** is reached only from `resolve_effective` over code specs, never from a stored path,
  so no stored row reaches the removed `MODULE_IMPORTS` names.
- **Real data:** all three copies of `~/learnloop-backups/20261109-copy` (`arxiv_v2`, `linear_algebra`,
  `probability`) hold the 7 decision rows (`progression_policy:` ×2, `progression:` ×3, `reentry_adapter:` ×2, all
  `heuristic`, `active`) among 408 stored rows. The structural entries never had rows (`refresh` writes decision
  specs only).
- **Other registry hashes:** `controller_snapshot._controller_param_manifest_hash` hashes only specs owned by
  `constraint_engine`, `staged_policy` and `controller_snapshot`, so administrations' `decision_params_hash` can't
  change.

### Tests

| File | What goes | What stays or moves |
|---|---|---|
| `test_substrate_cutover.py` | all 20 tests (17 functions, one over 4 write boundaries) | its one test of live code, `AA.hot_path_applies_practice_review` by version, is covered through the real attempt path by `test_hot_path_eligibility_cutover.py` |
| `test_journey6.py` | both tests | the journey's writer was `substrate_cutover.submit_administration_response`; the passive-action test duplicates `test_commitments::test_passive_action_cannot_create_commitment`; the live services it walks (commitments, card lineage forks, surface mint, depth transition, retire) have their own files |
| `test_progression.py` | all 8 tests | |
| `test_predictive_targets.py` | all 6 tests | |
| `test_activity_contract_extensions.py` | `test_resolve_progression_policy`, `test_progression_policy_is_content_addressed` | the fixture stops seeding a progression policy (no other test reads it) |
| `test_reentry_short_session.py` | the 3 re-entry tests | renamed `test_staged_policy_short_session.py`: the 4 short-session tests call `staged_policy.decide` directly (the adapter was a thin wrapper; the short-block rules they prove live in `staged_policy`, which stays), and the depth-edge-fit test already did |
| `test_laddered_stems.py` | nothing | its clustering tests call `familiarity.evidence_cap_grouping`, the function `progression.apply_evidence_cap` handed them to (they assert only the grouping) |
| `test_architecture.py` | `predictive_targets` from the dynamic-attribute list | |

The deleted tests, run once at the base (`-n 0`, `--durations=0`): **41 passed in 2.07 s wall, 1.44 s of setup,
call and teardown**.

### Verdict

All six go, each with its registry entries in the same commit: 11 `_reg_const` entries (7 decision, 4 structural)
and 6 `MODULE_INVENTORY` lines. None is reached from an entry point, the replay/rebuild/upgrade roots or the plan
path except through the registry's own string table; no frontend, phone or MCP caller; no stored row stops loading.
Nothing goes to the owner's list as "reached".

## What was deleted

Source: **1,979 lines deleted, 11 added** (net −1,968), in `11c3bfaa2b`.

| What | Lines |
|---|---:|
| `substrate/compat/substrate_cutover.py` | 720 |
| `scheduling/progression.py` | 341 |
| `scheduling/reentry_adapter.py` | 287 |
| `scheduling/predictive_targets.py` | 165 |
| `scheduling/short_session.py` | 117 |
| `scheduling/progression_policy.py` | 94 |
| `params/parameter_registry.py`: 6 `MODULE_INVENTORY` lines, 11 `_reg_const` entries (7 decision, 4 structural) and their comment headers | 63 (4 added: two comments reworded) |
| `db/repositories.py`: the 9 methods only these modules called (`ensure_progression_policy_version`, `progression_policy_version`, `insert_angle_inventory`, `angle_inventories_for_family`, `ensure_family_evidence_cap_policy`, `family_evidence_cap_policy`, `open_lapse_episode`, `lapse_episode`, `update_lapse_episode`) and an emptied section header | 168 (1 added) |
| `substrate/activities.py`: `resolve_progression_policy` (only `progression.py` called it) | 18 |
| `scheduling/open_world_gate.py`: the `predictive_targets` sub-check | 6 (6 added: a comment on the kept key) |
| `pyproject.toml`: the `substrate_cutover -> fsrs` ignore line | 1 |

The fixed point: after the modules went, a rerun of C1's `c1_scan.py` found the 10 newly orphaned names above (deleted);
a third run found only the four kept test-only names under Open items.

`tests/architecture_function_local_domain_imports.txt` lost its two frozen edges from the deleted modules (the ratchet
test asks for that).

## Tests removed and seconds saved

41 tests removed: `test_substrate_cutover.py` (20), `test_journey6.py` (2), `test_progression.py` (8),
`test_predictive_targets.py` (6), 2 in `test_activity_contract_extensions.py`, 3 re-entry tests. Run once at the base
(`-n 0`): **2.07 s wall, 1.44 s of setup, call and teardown**, so about 1.4 s off a serial suite. One test added
(`test_registry_audit::test_a_stored_row_for_a_removed_spec_stays_readable`, 1.8 s). The four short-session tests stay,
calling `staged_policy.decide` directly. Test lines: 1,090 deleted, 241 added (158 of them the rewritten short-session
file).

## Proofs

- **Step 0 before deletion:** committed alone (`ed3e5d19a4`); tests removed in their own commit (`f5ae567718`) before
  the source (`11c3bfaa2b`).
- **Closure** (`c2_closure.py`), base → tip: 1,291 → 1,285 modules, 15,784 → 15,717 edges. At the tip the full graph
  reaches 1,281 / 1,113 / 1,116 modules from the entry points / replay roots / plan path: exactly the base's pruned
  counts, so nothing but the six lost reach. Modules nothing reaches at the tip: `ai/providers/structured_output`,
  `figures/source_check_harness`, `sim/ad_gates`, `sim/ad_synthetic` (none C2's; see Open items).
- **P-shadow** (`learnloop rebuild --shadow --json`) on backup-API copies of `~/learnloop-backups/20261109-copy`
  (stale `probability/.learnloop/state.sqlite` removed; no upgrade needed, every copy is at mvp-0.54), base vs tip,
  ignoring `as_of` and `marker_id`:
  - `linear_algebra` (70 attempts replayed): 0 differences.
  - `probability` (3 replayed): 0 differences.
  - `arxiv_v2` (21 replayed): 16 differences, all fresh ULIDs that the activity-substrate replayer mints for 9 families
    and 7 surfaces on each run; two tip runs differ from each other in the same 16 places, and every count matches.
    0 other differences.
  - The live databases' SHA-256 is unchanged by every run. The learner-state diff and `schedule_effects` are identical
    at base and tip (the rebuild's own diff isn't empty on these copies at either side: `arxiv_v2` moves 9 due dates by
    −0.0 days, `interval_ratio` 1.0, the same before C2).
- **Stored rows on real copies,** base vs tip, on fresh backup-API copies of all three vaults: each holds the 7 removed
  decision rows among 408. At both sides, `registry list` lists 409 rows with all 7, `registry show
  progression:POST_LAPSE_FOLLOWUP_DAYS` exits 0, `registry audit` is clean with 372 pending certificates (the 7
  among them), and `freeze_manifest` freezes 409 parameters including the 7 with their stored hashes. The code
  registry has 402 decision specs at base and 395 at the tip. `learnloop doctor --json` gives the same exit code,
  error and warning counts (48/235, 2/56, 49/54) and the identical list of issue codes at both sides, and never names
  a removed path.
- **Registry test:** `test_registry_audit::test_a_stored_row_for_a_removed_spec_stays_readable` writes stored rows for
  the 7 removed paths into a fresh vault: refresh leaves them byte-identical, `freeze_manifest` takes them,
  `audit` stays clean, `registry show`/`list` print them, doctor's issues are unchanged.
- **No change at a fixed input:** nothing deleted is reached from serving, grading, the router, replay, rebuild or
  upgrade (closure), so served items, router draws, grades and replay can't change; the shadow rebuild confirms
  replay. The administrations' `decision_params_hash` hashes only `constraint_engine`, `staged_policy` and
  `controller_snapshot` specs. The one visible output change: `learnloop controller open-world-gate`'s condition 5
  detail loses `predictive_targets=True; ` and its description loses "target-distribution EIG"; its `met` and the
  gate's overall verdict are unchanged.
- **`lint-imports --no-cache`:** 42 kept, 0 broken (`unmatched_ignore_imports_alerting = "error"`, so the removed
  ignore line was the only one that went stale). **`ruff check`:** all checks passed.
- **Targeted tests:** the selector falls back to the whole suite (deleted modules, `pyproject.toml`,
  `db/repositories.py`, which conftest imports). So an explicit list of 357 files: the depth-0 selection for
  `parameter_registry`, `open_world_gate` and `activities` (114), every test file naming the registry, its manifest or
  its inventories (187), every test naming the open-world gate, staged policy, familiarity, administration adapters,
  card lineage, activities or the removed tables, every edited test file, `test_repositories`, `test_architecture`,
  `test_test_layout`, `test_cli_help_snapshot`, `test_cli_json`, `test_effective_defaults_golden`, `test_table_roles`,
  `test_open_world_gate`, `test_commitments`, `test_hot_path_eligibility_cutover`, `test_grade_resolution_pipeline`,
  `test_independent_group_counting`. **16,868 passed, 31 skipped, 6 xfailed, 1 failed in 835 s at `-n 4`**; the one
  failure was the frozen-edge ratchet asking for the two stale edges to go, which they did; `test_architecture`,
  `test_test_layout` and `test_registry_audit` then passed (40).

## Owner's list

Nothing was found reached on a learner path, so no candidate is held back. These are left for the owner:

1. **Four tables with no code left:** `progression_policy_versions`, `angle_inventories`, `family_evidence_cap_policies`
   (RAW_LEDGER) and `lapse_episodes` (WORKFLOW). Their only readers and writers were these modules and the deleted
   `Repository` methods. Left in place for J1. `activity_family_authoring.progression_policy_version_id` is still a
   column that authoring writes and nothing reads.
2. **The A2 laddered-stem kinship rule has no caller in `src`.** `familiarity.evidence_cap_grouping` and
   `tight_kinship_clusters` were reached only through `progression.apply_evidence_cap`, which nothing called either.
   `test_laddered_stems` and `test_familiarity` keep proving the rule. Wire it into an evidence cap when one is built,
   or delete it with those tests.
3. **`administration_adapters.project_administration`** is now test-only (`test_administration_adapters`): the deleted
   cutover writer was its one caller. The live path uses the same module's `hot_path_applies_practice_review`.
4. **Stale registry rows.** Every existing vault keeps the 7 removed decision rows, `active` and `heuristic`; every
   future manifest frozen on that vault carries them with their last hash, and the audit counts them as pending
   certificates (a warning). A vault created after C2 has none. If the owner wants a removed spec's row to say so,
   `refresh` could mark rows without a spec `lifecycle = 'deleted'` (the audit already skips non-active rows); that
   changes what the next manifest records, so it isn't done here.

## UX list

None. No candidate had a TS, Rust, phone or MCP caller, so no screen loses a backend.

## Open items

- **Doc strings that now name removed code,** left because they sit in other steps' files:
  `scheduling/controller_cutover.py:14` cites `substrate_cutover.run_cutover_gates` as its precedent (C6's module), and
  the registry rationale for `administration_adapters:P1_PURPOSE_ADAPTERS_ENABLED` says "step 9 flips it" (step 9 was
  the deleted cutover; the flag is still off).
- **Test-only `Repository` methods kept:** `lineage_for_card_version` (`test_card_lineage`) and
  `measurement_events_for_administration` (`test_grade_resolution_pipeline`) lost their `src` caller with
  `substrate_cutover`; their tests read persisted state through them, so they stay until a step moves them to a store.
- **`ai/providers/structured_output`** is unreached from every root at this base (not C2's; it looks like C4's area).
- **Merge with C5:** both edit `open_world_gate.py` (C2 only `_c5_controller`; C5 `_c3_p2`), `parameter_registry.py`
  (different `MODULE_INVENTORY` lines and entries), `test_architecture.py`'s dynamic-attribute list (C2 removed only
  the `predictive_targets` line) and possibly `db/repositories.py`, where C2's deletion ends just above the
  "P2 golden path" section header. The generated notes the orchestrator regenerates.
- **Vault:** hand-written notes first (`f225bb0067`: ADR-012 records `substrate_cutover`'s removal; three workflow and
  example notes name `test_staged_policy_short_session.py` and drop `short_session.py` from their source paths), then
  references regenerated once after the source commits (`4abead2050`, 67 files, the six deleted modules' notes removed
  by hand because the generator rewrites but doesn't delete). A second `generate_all.py` run changed nothing. The four
  validators pass: `validate_vault` (2,275 notes, 59,106 wikilinks), `module_validate` (1:1 coverage, 43,225 links),
  `desktop_validate` (330 + 6 modules), `db_validate_reference` (no errors). On the final tree, 115 passed:
  `test_desktop_activation_audit`, `test_generated_provenance`, `test_module_catalog_inventory`, `test_architecture`,
  `test_test_layout`, `test_cli_help_snapshot`, `test_cli_json`, `test_effective_defaults_golden`,
  `test_open_world_gate` and every edited test file; `lint-imports` 42 kept, `ruff check` clean.

## Unverified

- The full suite, the durability lane, `--fresh-connections` and the `arc_close` tests weren't run (the
  orchestrator's gate).
- P-draw wasn't run: C2 names P-shadow only, and the closure puts nothing deleted on a draw path.
- The name scan can't see a name built at run time from parts. The dynamic sites searched build none of these names,
  but sites C5 adds in parallel weren't seen.
- The base side of the real-copy registry and doctor checks ran the base source from a `git archive` of `src/` and
  `migrations/` under `fixtures-local/` (the editable install points at the tip), with the tip's environment.

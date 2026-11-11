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

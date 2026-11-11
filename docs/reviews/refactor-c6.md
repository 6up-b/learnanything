# Refactor C6: P4 controller, kinship, shadow components

Arc C ("delete what's proven dead"), step C6 of `docs/specs/refactor_strategy_v3.md` §2.5 (M, conditional). Branch
`refactor/c6-controller`, based on `5ba0fded47` (main `c828893847` with C1, C3 and C4, plus arc C batch 2: C7a, C2,
J1, the f10 test-clock fix and C5, merged and regenerated).

## Step 0: each candidate proved again at this tip

Written and committed before any deletion.

**Method.** `c6_closure.py` (`docs/reviews/artifacts/refactor-c6/`) is C2's `c2_closure.py` with C6's targets: AST
import edges over `src/` (module-level and function-local imports, `TYPE_CHECKING` included) plus a string edge for
every string constant naming a module (dotted, short, or as the `src/learnloop/...py` path `MODULE_INVENTORY` uses).
The pruned graph drops the string edges from `params.parameter_registry` and `scheduling.open_world_gate` into a
target and every edge from one target into another, so a target counts as reached only if something outside the set
imports it; for each reached target it prints one shortest import path from each root set. Roots: every entry point
(`learnloop_sidecar`, `learnloop_mobile`, `learnloop_mcp`, `learnloop.cli`, `learnloop.tui`), the replay, rebuild and
upgrade roots (`rebuild_orchestrator`, `shadow_rebuild`, `canonical_projection`, `attempts.attempts`,
`daily_plan.engine`, `ops.doctor`, `db.migrate`), and the plan path (every module under `daily_plan`, `router` and
`router_objective`). String dispatch: `git grep` for each module name and each public name over `src/` (all four
packages), `tests/`, `scripts/`, the vault's `_scripts/`, `apps/learnloop-tauri` (TS, TSX, Rust), `pyproject.toml`,
`fixtures/` and `migrations/`; no `METHOD_REGISTRY` entry, Typer command, Tauri command, phone allowlist entry or MCP
tool names any of them. The `importlib` sites in `src` that name a candidate are `MODULE_INVENTORY` and
`open_world_gate._has_attrs` (`staged_policy` only).

**The closure at `5ba0fded47`.** 1,278 modules, 15,628 edges. Full graph: the entry points reach 1,274, the replay
roots 1,111, the plan path 1,114. Pruned: 1,272 / 1,108 / 1,112. Modules no root reaches in the pruned graph:
`controller_cutover`, `state_signals` (both C6's), and four outside C6 (`ai/providers/structured_output`,
`figures/source_check_harness`, `sim/ad_gates`, `sim/ad_synthetic`, already on C1's and C2's lists).

### Modules

| Module (lines) | Importers in `src` at this tip | Pruned reach (entry / replay / plan) and one path | Registry | Frontend, phone, MCP, CLI | Tests | Verdict |
|---|---|---|---|---|---|---|
| `scheduling/controller_cutover.py` (653) | none (C5 removed `handlers/golden_path.py`, its only caller, through `golden_path.advance`) | no / no / no | `MODULE_INVENTORY` + 1 structural `_reg_const` (`controller_cutover:STAGED_POLICY_LIVE_FOR_P2`, `dormant`; structural, so `refresh` never wrote a row for it) | none; no Typer command; `migrations/101` names `advance_live` in a SQL comment (history) | `test_controller_cutover` (12), `test_router_staged_p2` (12) and its `router_staged_p2_helpers`, `test_data_capture_codex_review::test_f8_the_staged_decisions_receipt_commits_with_it`, `test_ro0_codex_review::test_f3_a_staged_decision_keeps_its_ad_numbers`; `test_cross_seam_exposure::test_same_surface_exactly_one_wins_via_shared_ledger` uses its `cross_seam_exposure_probe` as a test harness | **delete**, with its registry entries |
| `scheduling/state_signals.py` (217) | `controller_cutover` only. `daily_plan/staged_frame.py` builds its own `StateSignals` inline (its rung-3 value is a literal `1.0`, not `OPEN_EPISODE_ROBUST_VALUE`) | no / no / no | `MODULE_INVENTORY` (grouped with the cutover: "the live StateSignals adapters") + 1 decision `_reg_const` (`state_signals:OPEN_EPISODE_ROBUST_VALUE`; stored rows exist in vaults) | none | `test_state_signals` (15); the last four lines of `test_placement_opening_probes::test_an_ignored_episode_feeds_no_reader_that_scores_it` | **delete**, with its registry entries (the cutover's own adapter; unreached once the cutover goes, and unreached at this tip already) |
| `scheduling/controller_store.py` (459) | `staged_policy`, `randomization_layer`, `controller_snapshot`, `shadow_components`, `controller_cutover` | yes / yes / yes: `daily_plan.lesson_suggestion → scheduling.randomization_layer → controller_store` | not in `MODULE_INVENTORY` | none | many | **keep**: live (the staged frame's decisions, the randomization layer's assignments and outcome windows, snapshots, block events) |
| `scheduling/controller_snapshot.py` (414) | `staged_policy`, `constraint_engine`, `frame_constraints`, `dispersion`, `interleaving`, `state_signals`, `controller_cutover` | yes / yes / yes: `daily_plan.staged_frame → scheduling.frame_constraints → controller_snapshot` | entries kept | none | many | **keep**: live (every staged frame builds one) |
| `scheduling/shadow_components.py` (308, DESCOPED U-025) | `substrate/state_sync.py:225` (function-local: `retire_expired_telemetry`) | yes / yes / yes: `ops.doctor → substrate.state_sync → shadow_components`; plan: `daily_plan.router_reader → … → substrate.state_sync → shadow_components` | 2 decision entries | none | `test_shadow_components` | **keep** (owner's list): state sync calls `retire_expired_telemetry` on every sync, a live maintenance hook. Every other function (`predict_components`, `record_shadow_predictions`, `promote_component`, `promote_action_chooser`, `component_events`, `open_composed_selector_horizon`) has no `src` caller |
| `scheduling/kinship_feature.py` (525, DESCOPED U-026) | `scheduling/open_world_gate.py:184` (function-local: `is_admitted`) | yes / yes / yes, all through `learnloop.cli.controller → open_world_gate → kinship_feature` (the plan and replay paths reach `learnloop.cli` through function-local imports such as `ai.plan_fallback`; the runtime caller is the CLI command only) | 1 decision entry (`ADMISSION_MIN_DISCOUNT_SHIFT`); `sim/kinship_admission` names it as the certificate producer | the CLI `controller open-world-gate` (kept; in `tests/cli_surface.json`) | `test_kinship_feature`, `test_open_world_gate` | **keep** (owner's list): the kept CLI command's condition 6 reads `is_admitted`; removing it changes that command's output. `score_kinship`, `ensure_model`, `consulted_discount`, `run_admission_gate` have no `src` caller |

### Definitions the cutover was the only caller of

| Definition | Callers at this tip | Verdict |
|---|---|---|
| `router/decisions.py:507` `build_staged_p2_decision` (and its helper `_block_ref`) | `controller_cutover._log_staged_decision` only; tests: `test_router_staged_p2` (5 direct tests), two codex-review tests monkeypatch it | **delete** with the cutover; the readers of stored `staged_p2` rows (`router_decisions`, `decision_kind = 'staged_p2'`) are untouched |
| `router/why.py:163` `DEFERRALS`, `:171` `deferral_sentence` | none in `src`: its only caller was `handlers/golden_path.py:276` (C5). Test: `test_router_why_copy::test_the_deferral_and_details_lines_are_plain` (the `DETAILS_STAGED` half is live, `daily_plan/view.py:95`) | **delete**; the test keeps its `DETAILS_STAGED` assertion |
| `controller_ownership.assign_p2_run`, `rollback_to_legacy`, `resolve_owner`, `is_staged_owned`, `ownership_events` | after the cutover, no `src` caller outside the module; `test_controller_ownership`, `test_dual_authority_administration`, `test_cross_seam_exposure` seed and read ownership through them | **keep** (owner's list): the module is live (`staged_owned_practice_item_ids`, the serving exclusions, exam reservations), and the tests of those live readers seed state with these |
| `controller_store.decision_row` | after the cutover, tests only (3 files) | **keep**: a test reader in a live module, as C1 left `candidates_for_decision` and the others |
| `curriculum/golden_path_run` | still imported by `golden_path_assessment`, `golden_path_restoration`, `failure_triage` (kept by C5 for `reader.restore`) | keep |

### Replay, rebuild, upgrade, stored data

- No replayer, rebuild or upgrade module imports `controller_cutover` or `state_signals` (closure). The cutover wrote
  `golden_path_run_events` (through `golden_path_run.advance`), `router_decisions` rows of kind `staged_p2`, their
  prefilter and decision-state receipts, staged `controller_decisions` (through `staged_policy.decide`) and
  `controller_ownership_events`; every one of those tables keeps its other readers and writers, and no table is
  dropped (J1).
- Stored registry rows: `state_signals:OPEN_EPISODE_ROBUST_VALUE` is a decision spec, so existing vaults hold a row
  for it; C2's `test_a_stored_row_for_a_removed_spec_stays_readable` gets that path, and a structural path for the
  cutover's switch, to prove refresh, `freeze_manifest`, `audit`, `registry show/list` and doctor still take them.
- `administrations.decision_params_hash` (`controller_snapshot._controller_param_manifest_hash`) hashes only specs
  owned by `constraint_engine`, `staged_policy` and `controller_snapshot`, so removing `state_signals`' spec can't move
  it.

### The CLI group `controller`

One command, `controller open-world-gate`, which evaluates `open_world_gate` (kept: it reads `kinship_feature`,
`staged_policy`, `constraint_engine`, `dispersion`, `interleaving` and the vault's tables). The group drives live,
kept code, so it stays and `tests/cli_surface.json` doesn't change. Neither removed module is named by the gate.

### Verdict

Delete `controller_cutover` and `state_signals` with their `MODULE_INVENTORY` lines and `_reg_const` entries,
`build_staged_p2_decision`/`_block_ref`, and `why.deferral_sentence`/`DEFERRALS`. Keep `controller_store`,
`controller_snapshot`, `shadow_components` and `kinship_feature` (the last two on the owner's list). No candidate is
reached on a learner path; nothing moves to the owner's list as "reached but proposed".

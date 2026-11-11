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

## What was deleted

Tests first (`a27f1ea406`), then the source (`4857bd99ab`), then the table review (`eff7486a8f`) and the vault.

| What | Lines |
|---|---:|
| `scheduling/controller_cutover.py` | 653 |
| `scheduling/state_signals.py` | 217 |
| `router/decisions.py`: `build_staged_p2_decision`, `_block_ref`, the section header, `DESIGN_EPSILON_TIEBREAK`, `MODE_STAGED`, `STAGED_POLICY` (nothing else used them) and two `__all__` lines; the module docstring now says stored `staged_p2` rows are history (4 lines added) | 217 |
| `router/why.py`: `DEFERRALS`, `deferral_sentence` and their `__all__` lines | 24 |
| `params/parameter_registry.py`: 2 `MODULE_INVENTORY` lines, the structural `controller_cutover:STAGED_POLICY_LIVE_FOR_P2` and the decision `state_signals:OPEN_EPISODE_ROBUST_VALUE` `_reg_const` entries, comment headers reworded (2 added) | 20 |

Source: **1,131 lines deleted, 6 added** (`src/` only). Tests: 894 deleted, 48 added (the cross-seam probe moved into its
test, 29 lines; the registry test's structural path). The frozen function-local edge
`state_signals -> curriculum.commitments` left `tests/architecture_function_local_domain_imports.txt` (the ratchet asks
for it). `scripts/table_review.py`: `IN_FLIGHT` emptied (C2 and C5 have landed; its comment says how to add a step in
flight), 27 lines out, 4 in.

At the tip the closure has 1,276 modules and 15,592 edges, and its full graph reaches 1,272 / 1,108 / 1,112 modules
from the entry points / replay roots / plan path: exactly the base's pruned counts, so nothing but the two deleted
modules lost reach. Modules no root reaches: the four outside C6 named in step 0. `ruff check` clean, `lint-imports
--no-cache` 42 kept, 0 broken.

## Tests removed and seconds saved

Run once at the base (`-n 0`, `-p no:randomly`, JUnit times of setup + call + teardown) before deleting:

| Removed | Tests | Seconds (base) |
|---|---:|---:|
| `test_controller_cutover.py` | 12 | 1.164 |
| `test_router_staged_p2.py` (+ `router_staged_p2_helpers.py`, imported by nothing else) | 12 | 0.243 |
| `test_state_signals.py` | 15 | 1.017 |
| `test_ro0_codex_review.py::test_f3_a_staged_decision_keeps_its_ad_numbers` | 1 | 0.040 |
| `test_data_capture_codex_review.py::test_f8_the_staged_decisions_receipt_commits_with_it` | 1 | 0.028 |

**41 tests removed, 2.49 s serial.** Kept and edited: `test_cross_seam_exposure` (its two-controller race now uses a
local `_two_controllers_open`, the same barrier-and-count code the cutover module carried as a test harness; it still
proves the live in-lock recheck admits exactly one fresh administration), `test_router_why_copy`
(`test_the_details_line_is_plain` keeps the live `DETAILS_STAGED` check), `test_placement_opening_probes::
test_an_ignored_episode_feeds_no_reader_that_scores_it` (drops its four `state_signals` lines; the intervention trigger
and tutor Q&A checks stay). Extended: `test_registry_audit::test_a_stored_row_for_a_removed_spec_stays_readable` (the
`state_signals` decision path, and a structural `controller_cutover` path with `registry show`). `test_test_layout`'s
allowlist didn't name any removed file, so it is unchanged and passes.

## Proofs

- **Step 0 before deletion:** committed alone (`74128a8c8a`).
- **P-draw** (the router-speed harness scripts are not on disk, so C5's method with my own driver; the base side ran
  from this worktree at `74128a8c8a`, whose `src` is the base's): fresh backup-API copies of
  `~/learnloop-backups/20261109-copy` under `fixtures-local/`, the wall clock frozen (a `datetime` subclass installed
  before `learnloop` loads), ULIDs, `uuid4` and `SystemRandom` deterministic, the tests' `fake_runtime` (`FakeDecider`,
  `FakeLLM`, inline jobs, the mixture seed pinned to `c6-pinned:<key>`), the figure prefetch on its inline test seam (its
  background pass count otherwise depends on when the process stops), every non-loopback connect refused (none
  attempted), then `start_session`, `get_daily_plan` and three served `next_plan_item` calls. Every table compared row
  for row after masking ids, wall times, hex digests, `*_ms` measurements and the code-revision label, with compressed
  blobs decompressed first. Two base runs agree on all three vaults (the determinism check).

  | Vault | Router decisions / decision records / plans | Decider / LLM requests | Tables differing (of 402) |
  |---|---|---|---|
  | arxiv_v2 | 22 / 50 / 4 | 1 / 1 | 0 |
  | linear_algebra | 1 / 6 / 1 | 0 / 0 | 0 |
  | probability | 5 / 6 / 4 | 0 / 0 | 0 |

  The four replies are identical on every vault. Set aside: on arxiv_v2 `decision_state_receipts.stored_bytes`
  differs by 2 in one row: decompressing both receipts shows the only difference is `versions.code`
  (`git:74128a8…` vs `git:a27f1ea…`, the code label). The counts equal C5's on the same copies.
- **P-shadow:** `learnloop rebuild --shadow --json` on separate fresh copies, base and tip: 0 differences after masking
  ids and times on all three (raw differing lines 2, 2, 18: rebuild ids and `as_of`). `schedule_effects` identical after
  masking `as_of`; learner-state summaries identical (linear_algebra 70 attempts replayed, mastery 21 / schedule 0;
  probability 3, 18 / 0; arxiv_v2 21, 29 / 9, the copies' existing mvp-0.54-vs-tip deltas, as in C2 and J1); the live
  database unchanged on both sides.
- **Old data loads:** each copy holds the stored decision row `state_signals:OPEN_EPISODE_ROBUST_VALUE` (`heuristic`,
  `active`) among 409; none holds a `controller_cutover:` row (structural specs never get one). At base and tip alike:
  `registry list` exits 0 with 409 rows including it, `registry show state_signals:OPEN_EPISODE_ROBUST_VALUE` exits 0,
  `registry audit` is clean with 372 pending certificates. `learnloop doctor --json` gives the same exit code (1, as at
  base), the same error/warning counts (linear_algebra 2/56, probability 49/54, arxiv_v2 48/235) and the same issue
  codes. The extended registry test covers refresh, `freeze_manifest`, `audit`, `registry show/list` and doctor with
  both removed paths. Stored `staged_p2` router rows: no reader changed. No config key was removed.
- **Targeted tests.** The selector falls back to the whole suite (deleted modules), so an explicit list: the selector's
  picks for each surviving changed source file (`router/decisions.py` 9, `router/why.py` 96, `parameter_registry.py`
  112), every edited test file, every test file naming `staged_policy`, `controller_snapshot`, `controller_store`,
  `randomization_layer`, `parameter_registry`, `router.decisions`, `router.why`, `constraint_engine` or `staged_frame`,
  and `test_open_world_gate`, `test_controller_ownership`, `test_dual_authority_administration`,
  `test_shadow_components`, `test_kinship_feature`, `test_staged_policy_short_session`, `test_table_roles`,
  `test_architecture`, `test_test_layout`, `test_cli_help_snapshot`, `test_cli_json`, `test_effective_defaults_golden`:
  240 files, `-n 4 -m "not arc_close"`: **4,711 passed, 27 skipped, 3 xfailed, 1 failed** in 745 s. The failure,
  `test_ro5_stop_coin.py::test_serving_records_each_coin_with_its_exact_probability_and_availability`
  (`0.011184 == 0.011183673…`: the trace's rounded propensity against the ledger's, under `pytest.approx`'s default
  tolerance), draws from an unpinned `fake_runtime()` seeded by fresh ULIDs, so a small propensity appears only
  sometimes; it passed alone and in three whole-file reruns at the tip, and touches nothing C6 changed. After the
  source commit: `test_table_review`, `test_registry_audit`, `test_architecture`, `test_test_layout` 47 passed; after
  the regeneration: `test_generated_provenance`, `test_module_catalog_inventory`, `test_desktop_activation_audit`,
  `test_cli_help_snapshot`, `test_cli_json`, `test_effective_defaults_golden` 49 passed.
- **Table review:** rerun at the tip on fresh copies; two runs give byte-identical tracked and JSON output. A run on
  the base's `src` (`git archive 5ba0fded47`) gives the same class and flags for all 397 tables: C6 moved none.
- **Vault:** `generate_all.py` once after the source commits (58 files; the two deleted modules' notes removed by
  hand, since the generator removes none; no link names them); a second run changed nothing (fixed point).
  Validators: `validate_vault` passed (2,259 notes, 2,257/2,257 reachable), `module_validate` PASS (42,898 links),
  `desktop_validate` passed (324 + 6), `db_validate_reference` no errors. Hand-written: `Maps/LearnLoop Pipeline Map.md`
  (the P2 bridge sentence). `Concepts/Algorithm Versions and Reproducibility.md` describes what `mvp-0.23` brought and
  already says the RPC went with C5; left as history.

## The owner's list

Nothing was found reached on a learner path. Kept, with what is unreached inside them:

1. **`scheduling/shadow_components.py` (308, DESCOPED U-025).** State sync calls `retire_expired_telemetry` on every
   sync (`substrate/state_sync.py:225`), so the module is live. Nothing in `src` opens a horizon
   (`open_composed_selector_horizon` has no `src` caller), so the hook can only ever retire rows nobody wrote, and
   `predict_components`, `record_shadow_predictions`, `promote_component`, `promote_action_chooser` and
   `component_events` are test-only (`test_shadow_components`). Options: keep; or remove the state-sync hook with the
   module and its two decision entries (a change to a live path, so it would need the owner's yes and its own proof).
2. **`scheduling/kinship_feature.py` (525, DESCOPED U-026).** Only `is_admitted` is reached, from the kept CLI
   `controller open-world-gate` (condition 6). Its feature scoring, admission gate and `consulted_discount` have no `src`
   caller (`sim/kinship_admission` produces its certificate). Removing it changes that command's output, and the
   command is in `tests/cli_surface.json` (not among decision 7's 31). Options: keep; or retire the open-world gate's
   condition 6 with the module.
3. **The `controller` CLI group** stays: its one command drives live code (`open_world_gate` over the staged policy,
   constraint engine, dispersion, interleaving and the kinship check).
4. **`controller_ownership.assign_p2_run`, `rollback_to_legacy`, `resolve_owner`, `is_staged_owned`,
   `ownership_events`** lost their only `src` caller with the cutover. The module is live (the serving exclusions and
   exam reservations read its head), and tests of those readers seed ownership through these. No code assigns new
   staged ownership any more, so on a real vault the head only holds what was written before C5.
5. **Test-only readers in live modules:** `controller_store.decision_row` (with C1's `candidates_for_decision`,
   `shadow_predictions_for_decision`, `assignments_for_experiment`, `resolve_outcome_window`, `outcome_window_row`).
6. **Stale registry row:** every existing vault keeps `state_signals:OPEN_EPISODE_ROBUST_VALUE` (`active`,
   `heuristic`), as C2's seven: future manifests on those vaults carry it and the audit counts it as a pending
   certificate (C2's owner item 4 covers the option of marking such rows deleted).
7. **Tables (J1):** none dropped. The table review's group F is settled at this tip (7 dead, 3 retired but still read,
   7 live; the live seven move only if the owner retires what C5 kept).

## The UX list

None. No candidate had a TS, Rust, phone or MCP caller, so no screen loses a backend.

## Open items

- `daily_plan/staged_frame.py`'s docstring calls its rule "the P2 cutover's own rule, extended to Today"; that is
  where the rule came from and stays true, so it is left.
- `controller_ownership`'s docstring still describes the cutover window's arbitration (a P2 golden-path commitment
  goes to `staged`); accurate about the stored head, but nothing assigns it now (owner item 4).
- `test_ro5_stop_coin`'s unpinned seed makes the trace-propensity assertion flaky (above); not C6's, worth a pinned
  seed or a tolerance matching the trace's rounding.

## Unverified

- The full suite, durability lane, `--fresh-connections` run and `arc_close` tests are the orchestrator's (the
  targeted run left out `arc_close`).
- The P-draw driver is mine, not the router-speed harness; it drives the plan build and three served steps, not
  attempts, grading or a whole day. linear_algebra's and probability's plans were decided by rule, so only arxiv_v2
  exercised the objective's sampled draw and its model calls.
- The name and import scans can't see a module name built at run time from parts; the dynamic sites searched build
  none of these names.

## Rules I could not follow exactly

- Four patches were scripted rather than made with the Edit tool, each an exact-text or line-checked replacement:
  the deletion of `build_staged_p2_decision`'s contiguous range in `router/decisions.py` (printed and checked first,
  then `sed -i`), three `__all__`/ratchet single-line deletions guarded by their exact text, and the
  `test_placement_opening_probes` and `test_router_why_copy` edits (asserted exact matches in a Python script).

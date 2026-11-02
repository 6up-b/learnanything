---
title: "learnloop.figures.power"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/figures/power.py"
source_paths:
  - "src/learnloop/figures/power.py"
source_commit: "ec2060b5e053639a05d205609eb9d564cee70209"
source_commit_timestamp: "2026-11-02T07:07:21-05:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.figures"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.figures.power module"
  - "src/learnloop/figures/power.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-figures"
---

# `learnloop.figures.power`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/figures/_package|learnloop.figures]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.figures.power` exists within [[Reference/Modules/learnloop/figures/_package|learnloop.figures]] to own the behavior summarized by its module contract: Reader RW5d P5: the power condition of background figure work (spec_reader_show_me_figures_v1 §10b.4).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/figures/power.py](../../../../../../src/learnloop/figures/power.py) |
| Source lines | 248 |
| Owning package | [[Reference/Modules/learnloop/figures/_package|learnloop.figures]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `ec2060b5e053639a05d205609eb9d564cee70209` |
| Commit timestamp | `2026-11-02T07:07:21-05:00` |

## Public API

- `class PowerState` ([source](../../../../../../src/learnloop/figures/power.py), line 47)
- `linux_power_state(root: Path=SYSFS_ROOT, *, profile: Callable[[], str | None] | None=None) -> PowerState` ([source](../../../../../../src/learnloop/figures/power.py), line 79) — The Linux reading (module docstring); ``profile`` reads the power profile (tests inject it).
- `mac_power_state(run: Callable[..., Any] | None=None) -> PowerState` ([source](../../../../../../src/learnloop/figures/power.py), line 120)
- `windows_power_state() -> PowerState` ([source](../../../../../../src/learnloop/figures/power.py), line 135)
- `set_power_reader(reader: Callable[[], PowerState] | None) -> None` ([source](../../../../../../src/learnloop/figures/power.py), line 164) — Install a fixed reader (tests); None restores the platform's.
- `power_state() -> PowerState` ([source](../../../../../../src/learnloop/figures/power.py), line 171) — Whether this machine is on mains now (module docstring).
- `prefetch_switch(vault: Any) -> bool` ([source](../../../../../../src/learnloop/figures/power.py), line 194) — ``figures.enabled`` and ``figures.prefetch_enabled`` as configured on ``vault``.
- `background_hold(vault: Any, *, wait_foreground: float=0.0) -> str | None` ([source](../../../../../../src/learnloop/figures/power.py), line 210) — Why a background (prefetch) build may not make its next request now, or None: the switch, the power, then foreground work in flight (Codex review F7: a prebuild's every request yields to the learner; ``wait_foreground`` seconds it may wait for that work to end first, as the dura…

### Module constants

- `SYSFS_ROOT` ([src/learnloop/figures/power.py](../../../../../../src/learnloop/figures/power.py), line 38)
- `PROBE_TIMEOUT_SECONDS` ([src/learnloop/figures/power.py](../../../../../../src/learnloop/figures/power.py), line 41)
- `_OVERRIDE` ([src/learnloop/figures/power.py](../../../../../../src/learnloop/figures/power.py), line 159)
- `POWER_ENV` ([src/learnloop/figures/power.py](../../../../../../src/learnloop/figures/power.py), line 161)
- `SWITCHED_OFF` ([src/learnloop/figures/power.py](../../../../../../src/learnloop/figures/power.py), line 202)
- `NOT_ON_MAINS` ([src/learnloop/figures/power.py](../../../../../../src/learnloop/figures/power.py), line 203)
- `YIELDED` ([src/learnloop/figures/power.py](../../../../../../src/learnloop/figures/power.py), line 207)

### Explicit exports

`__all__` declares:

- `BATTERY`
- `MAINS`
- `NOT_ON_MAINS`
- `POWER_ENV`
- `POWER_SAVER`
- `PROBE_TIMEOUT_SECONDS`
- `SWITCHED_OFF`
- `SYSFS_ROOT`
- `UNKNOWN`
- `YIELDED`
- `PowerState`
- `background_hold`
- `linux_power_state`
- `mac_power_state`
- `power_state`
- `prefetch_switch`
- `set_power_reader`
- `windows_power_state`

## Internal implementation anchors

- `_read(path: Path) -> str | None` ([source](../../../../../../src/learnloop/figures/power.py), line 55)
- `_profile(run: Callable[..., Any] | None=None) -> str | None` ([source](../../../../../../src/learnloop/figures/power.py), line 62) — power-profiles-daemon's active profile, or None (no daemon, no tool, a failure).

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/figures/prefetch|learnloop.figures.prefetch]] — imports `module`; statically calls `background_hold`, `power_state`, `prefetch_switch`
- [[Reference/Modules/learnloop/figures/rich|learnloop.figures.rich]] — imports `NOT_ON_MAINS`, `SWITCHED_OFF`, `YIELDED`, `background_hold`; statically calls `background_hold`
- [[Reference/Modules/learnloop/figures/service|learnloop.figures.service]] — imports `background_hold`, `power_state`, `prefetch_switch`; statically calls `background_hold`, `power_state`, `prefetch_switch`
- [[Reference/Modules/learnloop_sidecar/handlers/figures|learnloop_sidecar.handlers.figures]] — imports `module`; statically calls `prefetch_switch`
- [[Reference/Modules/learnloop_sidecar/prefetch_runtime|learnloop_sidecar.prefetch_runtime]] — imports `module`; statically calls `prefetch_switch`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/figures/foreground|learnloop.figures.foreground]] — imports `module`; calls `busy`, `wait_idle`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `ctypes`, `dataclasses`, `os`, `pathlib`, `shutil`, `subprocess`, `sys`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/figures/prefetch|learnloop.figures.prefetch]], [[Reference/Modules/learnloop/figures/rich|learnloop.figures.rich]], [[Reference/Modules/learnloop/figures/service|learnloop.figures.service]], [[Reference/Modules/learnloop_sidecar/handlers/figures|learnloop_sidecar.handlers.figures]], [[Reference/Modules/learnloop_sidecar/prefetch_runtime|learnloop_sidecar.prefetch_runtime]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_figures_prefetch.py](../../../../../../tests/test_figures_prefetch.py) — direct import
  - `test_a_background_build_stops_off_mains_before_any_request`
  - `test_mac_power_state_reads_pmset`
  - `test_on_battery_nothing_starts_and_no_judge_is_asked`
  - `test_power_state_reads_linux_supplies_and_fails_closed`
- [tests/test_figures_prefetch_review_fixes.py](../../../../../../tests/test_figures_prefetch_review_fixes.py) — direct import
  - `test_f12_an_unknown_linux_power_inventory_fails_closed`
  - `test_f16_a_prebuilds_rich_request_rechecks_the_switch_after_waiting_for_foreground_work`
  - `test_f17_a_plan_wait_is_not_retried_off_mains_or_switched_off`
  - `test_f18_a_prebuilds_rich_job_is_pending_on_mains_only`
  - `test_f18_an_unstarted_decision_is_pending_only_while_a_pass_runs_and_never_on_battery`
  - `test_f5_a_deferred_decision_is_built_once_the_condition_clears`
  - `test_f7_a_prebuilds_rich_job_yields_to_foreground_work`
  - `test_f7_a_quick_prebuild_stops_before_its_request_while_the_learner_works`
  - `test_f9_an_ask_is_the_same_request_before_the_horizon`
  - `test_r1_a_pressed_fuller_keeps_its_pending_line_and_is_not_speculative`
  - `test_r1_an_unqueued_speculative_fuller_is_not_pending_on_battery`

## Modification guidance

- Make changes here when the responsibility remains power within learnloop.figures; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/figures/power.py](../../../../../../src/learnloop/figures/power.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

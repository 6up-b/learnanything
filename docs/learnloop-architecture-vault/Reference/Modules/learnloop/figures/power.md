---
title: "learnloop.figures.power"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/figures/power.py"
source_paths:
  - "src/learnloop/figures/power.py"
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
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/figures/_package|learnloop.figures]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.figures.power` exists within [[Reference/Modules/learnloop/figures/_package|learnloop.figures]] to own the behavior summarized by its module contract: Reader RW5d P5: the power condition of background figure work (spec_reader_show_me_figures_v1 §10b.4).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/figures/power.py](../../../../../../src/learnloop/figures/power.py) |
| Source lines | 317 |
| Owning package | [[Reference/Modules/learnloop/figures/_package|learnloop.figures]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class PowerState` ([source](../../../../../../src/learnloop/figures/power.py), line 63)
- `reset_probe_cache() -> None` ([source](../../../../../../src/learnloop/figures/power.py), line 121) — Forget every cached probe answer (tests; :func:`set_power_reader`).
- `linux_power_state(root: Path=SYSFS_ROOT, *, profile: Callable[[], str | None] | None=None) -> PowerState` ([source](../../../../../../src/learnloop/figures/power.py), line 128) — The Linux reading (module docstring); ``profile`` reads the power profile (tests inject it).
- `mac_power_state(run: Callable[..., Any] | None=None) -> PowerState` ([source](../../../../../../src/learnloop/figures/power.py), line 179) — ``pmset -g batt``; unset ``run``, its answer comes through the probe cache (no cheap change signal).
- `windows_power_state() -> PowerState` ([source](../../../../../../src/learnloop/figures/power.py), line 201)
- `set_power_reader(reader: Callable[[], PowerState] | None) -> None` ([source](../../../../../../src/learnloop/figures/power.py), line 230) — Install a fixed reader (tests); None restores the platform's.
- `power_state() -> PowerState` ([source](../../../../../../src/learnloop/figures/power.py), line 238) — Whether this machine is on mains now (module docstring).
- `prefetch_switch(vault: Any) -> bool` ([source](../../../../../../src/learnloop/figures/power.py), line 261) — ``figures.enabled`` and ``figures.prefetch_enabled`` as configured on ``vault``.
- `background_hold(vault: Any, *, wait_foreground: float=0.0) -> str | None` ([source](../../../../../../src/learnloop/figures/power.py), line 277) — Why a background (prefetch) build may not make its next request now, or None: the switch, the power, then foreground work in flight (Codex review F7: a prebuild's every request yields to the learner; ``wait_foreground`` seconds it may wait for that work to end first, as the dura…

### Module constants

- `SYSFS_ROOT` ([src/learnloop/figures/power.py](../../../../../../src/learnloop/figures/power.py), line 49)
- `PROBE_TIMEOUT_SECONDS` ([src/learnloop/figures/power.py](../../../../../../src/learnloop/figures/power.py), line 52)
- `PROBE_CACHE_SECONDS` ([src/learnloop/figures/power.py](../../../../../../src/learnloop/figures/power.py), line 57)
- `_PROBE_CACHE` ([src/learnloop/figures/power.py](../../../../../../src/learnloop/figures/power.py), line 96)
- `_PROBE_LOCK` ([src/learnloop/figures/power.py](../../../../../../src/learnloop/figures/power.py), line 99)
- `_OVERRIDE` ([src/learnloop/figures/power.py](../../../../../../src/learnloop/figures/power.py), line 225)
- `POWER_ENV` ([src/learnloop/figures/power.py](../../../../../../src/learnloop/figures/power.py), line 227)
- `SWITCHED_OFF` ([src/learnloop/figures/power.py](../../../../../../src/learnloop/figures/power.py), line 269)
- `NOT_ON_MAINS` ([src/learnloop/figures/power.py](../../../../../../src/learnloop/figures/power.py), line 270)
- `YIELDED` ([src/learnloop/figures/power.py](../../../../../../src/learnloop/figures/power.py), line 274)

### Explicit exports

`__all__` declares:

- `BATTERY`
- `MAINS`
- `NOT_ON_MAINS`
- `POWER_ENV`
- `POWER_SAVER`
- `PROBE_CACHE_SECONDS`
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
- `reset_probe_cache`
- `set_power_reader`
- `windows_power_state`

## Internal implementation anchors

- `_read(path: Path) -> str | None` ([source](../../../../../../src/learnloop/figures/power.py), line 71)
- `_profile(run: Callable[..., Any] | None=None) -> str | None` ([source](../../../../../../src/learnloop/figures/power.py), line 78) — power-profiles-daemon's active profile, or None (no daemon, no tool, a failure).
- `_cached_probe(name: str, key: object, probe: Callable[[], Any]) -> Any` ([source](../../../../../../src/learnloop/figures/power.py), line 104) — ``probe()``'s answer, reused while ``key`` is unchanged and younger than :data:`PROBE_CACHE_SECONDS`.
- `_mac_power_state(runner: Callable[..., Any]) -> PowerState` ([source](../../../../../../src/learnloop/figures/power.py), line 187)

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

- Standard library: `__future__`, `collections`, `ctypes`, `dataclasses`, `os`, `pathlib`, `shutil`, `subprocess`, `sys`, `threading`, `time`, `typing`
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
- [tests/test_followups_batch6_power_probe_cache.py](../../../../../../tests/test_followups_batch6_power_probe_cache.py) — direct import
  - `test_a_cached_power_saver_profile_keeps_background_work_off`
  - `test_a_failed_probe_is_cached_and_the_reading_still_fails_closed`
  - `test_a_power_supply_change_in_sysfs_probes_again_at_once`
  - `test_a_probe_that_raises_is_not_cached_and_reads_as_not_on_mains`
  - `test_concurrent_reads_share_one_probe`
  - `test_installing_a_reader_forgets_the_cached_probes`
  - `test_no_tool_starts_nothing_and_an_injected_profile_is_never_cached`
  - `test_pmset_is_cached_for_the_window_too`
  - `test_the_probe_answers_only_for_its_window`
  - `test_thirty_reads_start_the_profile_probe_once`
- [tests/test_followups_batch6_prefetch_next_section.py](../../../../../../tests/test_followups_batch6_prefetch_next_section.py) — direct import
- [tests/test_followups_batch6_prefetch_plan_wait.py](../../../../../../tests/test_followups_batch6_prefetch_plan_wait.py) — direct import
  - `test_the_pass_retries_only_on_mains_with_the_switch_on_and_the_plan_not_paused`
- [tests/test_followups_batch6_review_fixes.py](../../../../../../tests/test_followups_batch6_review_fixes.py) — direct import
- [tests/test_followups_batch6_verify_fixes.py](../../../../../../tests/test_followups_batch6_verify_fixes.py) — direct import
  - `test_v2_characterization_a_worker_origin_pass_still_runs_ordinary_builds`
- [tests/test_followups_batch7_prefetch_capped_resume.py](../../../../../../tests/test_followups_batch7_prefetch_capped_resume.py) — direct import
  - `test_a_resumed_planned_visual_is_the_lesson_steps_own_request`
  - `test_a_stored_request_is_linked_whatever_holds_new_builds_and_its_opening_is_observed`
  - `test_every_background_guard_a_power_deferred_resume_rechecks_holds_a_capped_one`
- [tests/test_followups_batch7_prefetch_link_served.py](../../../../../../tests/test_followups_batch7_prefetch_link_served.py) — direct import

## Modification guidance

- Make changes here when the responsibility remains power within learnloop.figures; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/figures/power.py](../../../../../../src/learnloop/figures/power.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

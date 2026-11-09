---
title: "learnloop.scheduling.serving_exclusions"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/scheduling/serving_exclusions.py"
source_paths:
  - "src/learnloop/scheduling/serving_exclusions.py"
source_commit: "b45e4414cdb7963772b12ecd3c8825b73e93266a"
source_commit_timestamp: "2026-11-03T21:51:14-05:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.scheduling"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Start a Learning Cycle"
  - "Continue a Learning Cycle"
aliases:
  - "learnloop.scheduling.serving_exclusions module"
  - "src/learnloop/scheduling/serving_exclusions.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-scheduling"
---

# `learnloop.scheduling.serving_exclusions`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/scheduling/_package|learnloop.scheduling]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.scheduling.serving_exclusions` exists within [[Reference/Modules/learnloop/scheduling/_package|learnloop.scheduling]] to own the behavior summarized by its module contract: Items routine serving never offers, shared by Today's queue, the quick check and ``find_practice``.

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/scheduling/serving_exclusions.py](../../../../../../src/learnloop/scheduling/serving_exclusions.py) |
| Source lines | 348 |
| Owning package | [[Reference/Modules/learnloop/scheduling/_package|learnloop.scheduling]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `b45e4414cdb7963772b12ecd3c8825b73e93266a` |
| Commit timestamp | `2026-11-03T21:51:14-05:00` |

## Public API

- `class ServingExclusions` ([source](../../../../../../src/learnloop/scheduling/serving_exclusions.py), line 79)
  - `item_ids(self) -> frozenset[str]` (line 99; public) — What routine serving never offers.
  - `out_of_timing_item_ids(self) -> frozenset[str]` (line 106; public) — What a selector outside the scheduler's timing never offers.
- `routine_serving_exclusions(vault: Any, repository: Repository) -> ServingExclusions` ([source](../../../../../../src/learnloop/scheduling/serving_exclusions.py), line 112) — The shared exclusion sets, each read once.
- `routine_withhold_reason(vault: Any, item: Any, state: Any, exclusions: ServingExclusions) -> str | None` ([source](../../../../../../src/learnloop/scheduling/serving_exclusions.py), line 131) — Why routine serving never offers ``item`` now, or None.
- `class BuildGates(Protocol)` ([source](../../../../../../src/learnloop/scheduling/serving_exclusions.py), line 232) — The build's per-item gates after the routine one.
  - `freshness_gate(self, item: Any, state: Any) -> str | None` (line 237; public) — A diagnostic_probe surface outside an in-progress, unblocked episode.
  - `device_gate(self, item: Any, state: Any) -> str | None` (line 240; public) — An item this build's device cannot answer (mobile PR-6, a phone's build).
  - `placement_gate(self, item: Any, state: Any) -> str | None` (line 243; public) — Placement's withholding of an unrequested item (assumed, maintained).
  - `cold_start_gate(self, item: Any, state: Any) -> str | None` (line 246; public) — An unrequested item on a never-practised LO with nothing to start it.
  - `probe_gate(self, item: Any, state: Any) -> str | None` (line 249; public) — A diagnostic_probe surface of an in-progress episode that is not a probe this build (surface seen, no binding, its value below its minutes, no information).
- `admission_reason(vault: Any, item: Any, state: Any, exclusions: ServingExclusions, gates: BuildGates | None, *, requested: bool, intent_gate: Any=None) -> str | None` ([source](../../../../../../src/learnloop/scheduling/serving_exclusions.py), line 255) — Why the build does not serve ``item`` now, or None: THE per-item admission predicate (orchestrator ruling R1).
- `out_of_timing_serving_exclusions(vault: Any, repository: Repository, *, cold_followup_kinds: Iterable[str], reveal_window: timedelta, clock: Clock | None=None, exclude_reveal_ids: Iterable[str] | None=None) -> ServingExclusions` ([source](../../../../../../src/learnloop/scheduling/serving_exclusions.py), line 306) — The routine sets plus the items reserved by open cold follow-up tasks of ``cold_followup_kinds`` and the items revealed within ``reveal_window`` (the cold retrieval delay), read once.

### Module constants

- `ROUTINE_GATES` ([src/learnloop/scheduling/serving_exclusions.py](../../../../../../src/learnloop/scheduling/serving_exclusions.py), line 190)
- `DEVICE_INELIGIBLE` ([src/learnloop/scheduling/serving_exclusions.py](../../../../../../src/learnloop/scheduling/serving_exclusions.py), line 208)
- `BUILD_GATES` ([src/learnloop/scheduling/serving_exclusions.py](../../../../../../src/learnloop/scheduling/serving_exclusions.py), line 211)
- `ADMISSION_GATES` ([src/learnloop/scheduling/serving_exclusions.py](../../../../../../src/learnloop/scheduling/serving_exclusions.py), line 226)
- `PROBE_RESERVED_GATES` ([src/learnloop/scheduling/serving_exclusions.py](../../../../../../src/learnloop/scheduling/serving_exclusions.py), line 229)

## Internal implementation anchors

- `_iso(value: Any) -> str` ([source](../../../../../../src/learnloop/scheduling/serving_exclusions.py), line 302)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/daily_plan/objective_inputs|learnloop.daily_plan.objective_inputs]] — imports `routine_serving_exclusions`; statically calls `routine_serving_exclusions`
- [[Reference/Modules/learnloop/daily_plan/slot_facts|learnloop.daily_plan.slot_facts]] — imports `out_of_timing_serving_exclusions`; statically calls `out_of_timing_serving_exclusions`
- [[Reference/Modules/learnloop/diagnosis/quick_check|learnloop.diagnosis.quick_check]] — imports `out_of_timing_serving_exclusions`; statically calls `out_of_timing_serving_exclusions`
- [[Reference/Modules/learnloop/practice_index/admission|learnloop.practice_index.admission]] — imports `out_of_timing_serving_exclusions`; statically calls `out_of_timing_serving_exclusions`
- [[Reference/Modules/learnloop/scheduling/scheduler|learnloop.scheduling.scheduler]] — imports `DEVICE_INELIGIBLE`, `PROBE_RESERVED_GATES`, `ServingExclusions`, `admission_reason`, `out_of_timing_serving_exclusions`, `routine_serving_exclusions`; statically calls `admission_reason`, `out_of_timing_serving_exclusions`, `routine_serving_exclusions`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `SystemClock`; calls `SystemClock`
- [[Reference/Modules/learnloop/content/sources/exam_material|learnloop.content.sources.exam_material]] — imports `held_out_items`, `held_out_selection_active`; calls `held_out_items`, `held_out_selection_active`
- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/stores/practice_index|learnloop.db.stores.practice_index]] — imports `items_revealed_between`; calls `items_revealed_between`
- [[Reference/Modules/learnloop/followup_serve/identity|learnloop.followup_serve.identity]] — imports `door_sets`, `generated_probe_ids`; calls `door_sets`, `generated_probe_ids`
- [[Reference/Modules/learnloop/goals/exam_pool|learnloop.goals.exam_pool]] — imports `reserved_item_ids`; calls `reserved_item_ids`
- [[Reference/Modules/learnloop/scheduling/controller_ownership|learnloop.scheduling.controller_ownership]] — imports `module`; calls `staged_owned_practice_item_ids`
- [[Reference/Modules/learnloop/substrate/instrument_serving|learnloop.substrate.instrument_serving]] — imports `unservable_reason`; calls `unservable_reason`
- [[Reference/Modules/learnloop/vault/lifecycle|learnloop.vault.lifecycle]] — imports `practice_item_servable`; calls `practice_item_servable`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `dataclasses`, `datetime`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Start a Learning Cycle]]
- [[Continue a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/daily_plan/objective_inputs|learnloop.daily_plan.objective_inputs]], [[Reference/Modules/learnloop/daily_plan/slot_facts|learnloop.daily_plan.slot_facts]], [[Reference/Modules/learnloop/diagnosis/quick_check|learnloop.diagnosis.quick_check]], [[Reference/Modules/learnloop/practice_index/admission|learnloop.practice_index.admission]], [[Reference/Modules/learnloop/scheduling/scheduler|learnloop.scheduling.scheduler]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_ad23_inversion.py](../../../../../../tests/test_ad23_inversion.py) — direct import
  - `test_the_codes_vocabulary_covers_the_incumbents_reasons`
- [tests/test_ad2_serving.py](../../../../../../tests/test_ad2_serving.py) — direct import
- [tests/test_attempt_content_state_successor.py](../../../../../../tests/test_attempt_content_state_successor.py) — direct import
- [tests/test_device_eligibility.py](../../../../../../tests/test_device_eligibility.py) — direct import
  - `test_a_check_once_asks_the_same_gate`
- [tests/test_exam_protection_review.py](../../../../../../tests/test_exam_protection_review.py) — direct import
  - `test_an_item_marked_held_out_after_its_import_leaves_routine_practice`
  - `test_with_the_switch_off_routine_practice_serves_held_out_material_as_before`
- [tests/test_followup_single_use.py](../../../../../../tests/test_followup_single_use.py) — direct import
  - `test_a_request_never_gets_one_even_unserved`
  - `test_the_gates_are_named`
- [tests/test_intent_codex_rereview.py](../../../../../../tests/test_intent_codex_rereview.py) — direct import
  - `test_f11_a_held_out_cold_sibling_never_suppresses_the_servable_candidate`
- [tests/test_intent_exclusion.py](../../../../../../tests/test_intent_exclusion.py) — direct import
- [tests/test_intent_fix_round6.py](../../../../../../tests/test_intent_fix_round6.py) — direct import
- [tests/test_intent_orchestrator_rulings.py](../../../../../../tests/test_intent_orchestrator_rulings.py) — direct import
  - `test_r1_every_gate_of_the_build_is_the_admission_predicates`
- [tests/test_placement_fixture_copies.py](../../../../../../tests/test_placement_fixture_copies.py) — direct import
- [tests/test_ro5_checks.py](../../../../../../tests/test_ro5_checks.py) — direct import
  - `test_no_protected_or_exam_reserved_item_is_ever_eligible`
- [tests/test_router_r2a_landing.py](../../../../../../tests/test_router_r2a_landing.py) — direct import
- [tests/test_teacher_te2_probes.py](../../../../../../tests/test_teacher_te2_probes.py) — direct import
  - `test_a_probe_is_generated_once_served_cold_and_never_again`
- [tests/test_ux_phase4_feedback.py](../../../../../../tests/test_ux_phase4_feedback.py) — direct import

## Modification guidance

- Change serving exclusions policy here when scheduling owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/scheduling/serving_exclusions.py](../../../../../../src/learnloop/scheduling/serving_exclusions.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

---
title: "learnloop.daily_plan.slot_facts"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/daily_plan/slot_facts.py"
source_paths:
  - "src/learnloop/daily_plan/slot_facts.py"
source_commit: "38c895e230ef534fc7b4a2eff18a51ca456a06a2"
source_commit_timestamp: "2026-10-24T10:23:24-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.daily_plan"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.daily_plan.slot_facts module"
  - "src/learnloop/daily_plan/slot_facts.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-daily-plan"
---

# `learnloop.daily_plan.slot_facts`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/daily_plan/_package|learnloop.daily_plan]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.daily_plan.slot_facts` exists within [[Reference/Modules/learnloop/daily_plan/_package|learnloop.daily_plan]] to own the behavior summarized by its module contract: The plan's verdicts on adaptive difficulty's slot, and its re-check of AD's choice (the final round).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/daily_plan/slot_facts.py](../../../../../../src/learnloop/daily_plan/slot_facts.py) |
| Source lines | 172 |
| Owning package | [[Reference/Modules/learnloop/daily_plan/_package|learnloop.daily_plan]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `38c895e230ef534fc7b4a2eff18a51ca456a06a2` |
| Commit timestamp | `2026-10-24T10:23:24-04:00` |

## Public API

- `class ChoiceRejected(RuntimeError)` ([source](../../../../../../src/learnloop/daily_plan/slot_facts.py), line 35) — AD's choice is not one the plan admits now (phase 4): roll back and serve the planned item.
- `for_slot(env: Any, record: Any, block: Any, slot: Any, built: Any, day: Sequence[Any], inputs: SlotInputs) -> SlotFacts` ([source](../../../../../../src/learnloop/daily_plan/slot_facts.py), line 92) — Phase 2 for one new-material slot.
- `for_deferrals(env: Any, record: Any, built: Any, inputs: SlotInputs, deferrals: Iterable[str]) -> SlotFacts` ([source](../../../../../../src/learnloop/daily_plan/slot_facts.py), line 132) — Phase 2 for the boundary's AD deferrals (each judged were it released).
- `accept(facts: SlotFacts, action: str, chosen_item_id: str | None) -> None` ([source](../../../../../../src/learnloop/daily_plan/slot_facts.py), line 150) — Phase 4: AD's slot decision re-checked by the plan.
- `accept_cleared(facts: SlotFacts, cleared: Iterable[str]) -> list[str]` ([source](../../../../../../src/learnloop/daily_plan/slot_facts.py), line 162) — Phase 4 for deferrals: every cleared item must be a member with no refusal (else none is).

### Module constants

- `FACTS_FAILED` ([src/learnloop/daily_plan/slot_facts.py](../../../../../../src/learnloop/daily_plan/slot_facts.py), line 30)
- `CHOICE_REJECTED` ([src/learnloop/daily_plan/slot_facts.py](../../../../../../src/learnloop/daily_plan/slot_facts.py), line 32)

### Explicit exports

`__all__` declares:

- `CHOICE_REJECTED`
- `ChoiceRejected`
- `FACTS_FAILED`
- `accept`
- `accept_cleared`
- `for_deferrals`
- `for_slot`

## Internal implementation anchors

- `_pool_item(item_id: str, learning_object_id: str, est_minutes: float, existing: PoolItem | None) -> PoolItem` ([source](../../../../../../src/learnloop/daily_plan/slot_facts.py), line 39)
- `_verdicts(env: Any, record: Any, built: Any, inputs: SlotInputs, *, slot_item_id: str | None, released: Iterable[str]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/daily_plan/slot_facts.py), line 46)
- `_admissible(facts: SlotFacts, item_id: str) -> bool` ([source](../../../../../../src/learnloop/daily_plan/slot_facts.py), line 143)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/daily_plan/engine|learnloop.daily_plan.engine]] — imports `FACTS_FAILED`, `module`; statically calls `accept`, `accept_cleared`, `for_deferrals`, `for_slot`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]] — imports `COLD_FOLLOWUP_TASK_KINDS`
- [[Reference/Modules/learnloop/daily_plan/engine|learnloop.daily_plan.engine]] — imports `admitted_new_material_ids`; calls `admitted_new_material_ids`
- [[Reference/Modules/learnloop/daily_plan/lanes|learnloop.daily_plan.lanes]] — imports `PoolItem`; calls `PoolItem`
- [[Reference/Modules/learnloop/daily_plan/policy|learnloop.daily_plan.policy]] — imports `router_active`; calls `router_active`
- [[Reference/Modules/learnloop/daily_plan/slot_facts_schema|learnloop.daily_plan.slot_facts_schema]] — imports `EXCLUSION_NAMES`, `SlotFacts`, `SlotInputs`; calls `SlotFacts`
- [[Reference/Modules/learnloop/daily_plan/staged_frame|learnloop.daily_plan.staged_frame]] — imports `StagedFrame`; calls `StagedFrame`
- [[Reference/Modules/learnloop/daily_plan/types|learnloop.daily_plan.types]] — imports `BLOCK_MAX_MINUTES`
- [[Reference/Modules/learnloop/diagnosis/remediation|learnloop.diagnosis.remediation]] — imports `COLD_RETRIEVAL_DELAY`
- [[Reference/Modules/learnloop/scheduling/scheduler|learnloop.scheduling.scheduler]] — imports `pool_admission`; calls `pool_admission`
- [[Reference/Modules/learnloop/scheduling/serving_exclusions|learnloop.scheduling.serving_exclusions]] — imports `out_of_timing_serving_exclusions`; calls `out_of_timing_serving_exclusions`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/daily_plan/engine|learnloop.daily_plan.engine]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_ad23_inversion.py](../../../../../../tests/test_ad23_inversion.py) — direct import
  - `test_a_sentinel_the_plan_plants_never_reaches_ad`
  - `test_property_a_buggy_deciders_pick_outside_the_facts_is_rolled_back`
- [tests/test_ad2_serving.py](../../../../../../tests/test_ad2_serving.py) — direct import
  - `test_support_respects_constraints_reversibility_and_admission`
- [tests/test_plan_follows_path.py](../../../../../../tests/test_plan_follows_path.py) — direct import
  - `test_the_path_is_read_only_when_the_plan_is_built_and_ad_slot_facts_read_the_record`

## Modification guidance

- Make changes here when the responsibility remains slot facts within learnloop.daily_plan; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/daily_plan/slot_facts.py](../../../../../../src/learnloop/daily_plan/slot_facts.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

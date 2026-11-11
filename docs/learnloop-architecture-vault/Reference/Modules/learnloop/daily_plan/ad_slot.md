---
title: "learnloop.daily_plan.ad_slot"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/daily_plan/ad_slot.py"
source_paths:
  - "src/learnloop/daily_plan/ad_slot.py"
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
  - "learnloop.daily_plan.ad_slot module"
  - "src/learnloop/daily_plan/ad_slot.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-daily-plan"
---

# `learnloop.daily_plan.ad_slot`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/daily_plan/_package|learnloop.daily_plan]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.daily_plan.ad_slot` exists within [[Reference/Modules/learnloop/daily_plan/_package|learnloop.daily_plan]] to own the behavior summarized by its module contract: The plan's side of AD's slot draw (spec_adaptive_difficulty_v1 §6.1, §10.2; AD2+AD3, switch ``selection``).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/daily_plan/ad_slot.py](../../../../../../src/learnloop/daily_plan/ad_slot.py) |
| Source lines | 398 |
| Owning package | [[Reference/Modules/learnloop/daily_plan/_package|learnloop.daily_plan]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class AdUnavailable(RuntimeError)` ([source](../../../../../../src/learnloop/daily_plan/ad_slot.py), line 72) — AD cannot decide this slot safely (the held-out predicate, the guard or the facts): the plan serves its planned item as the incumbent does.
- `class SlotNotAdmitted(AdUnavailable)` ([source](../../../../../../src/learnloop/daily_plan/ad_slot.py), line 77) — The slot's own item is no longer in the plan's admitted pool (the facts' ``slot_admitted``): AD refuses the slot and the incumbent's own handling decides (the compose fix round 3).
- `class SlotSession` ([source](../../../../../../src/learnloop/daily_plan/ad_slot.py), line 83) — Phase 1's result: what AD hands the plan (``inputs``), and the view phase 3 reuses.
- `take_guard_denials() -> tuple[dict[str, Any], ...]` ([source](../../../../../../src/learnloop/daily_plan/ad_slot.py), line 95) — What AD's guard refused in this context since the last call, as codes only (verb, table, reader, entry): the plan's record of an AD phase it found unavailable names them.
- `open_slot(vault: Any, repository: Any, *, slot_item_id: str) -> SlotSession` ([source](../../../../../../src/learnloop/daily_plan/ad_slot.py), line 154) — Phase 1 for a slot: the slot item and its never-attempted visible siblings at its capability.
- `decide(vault: Any, repository: Any, wire: str, *, session: SlotSession) -> Any` ([source](../../../../../../src/learnloop/daily_plan/ad_slot.py), line 182) — Phase 3 for a slot: the facts decoded against the schema (ids projected onto AD's view), the support's checks 0-4 from the facts and AD's own view, and the draw (``decide_slot``, which writes the ``ad_selections`` row).
- `open_deferrals(vault: Any, repository: Any, deferral_ids: Iterable[str]) -> SlotSession` ([source](../../../../../../src/learnloop/daily_plan/ad_slot.py), line 289) — Phase 1 for the boundary's AD deferrals: the deferred items AD's view shows.
- `deferrals_cleared(vault: Any, repository: Any, wire: str, *, session: SlotSession) -> list[str]` ([source](../../../../../../src/learnloop/daily_plan/ad_slot.py), line 306) — Phase 3 for deferrals: the deferred members whose check 0 (pre-exposure aside) and the plan's verdicts all pass now.
- `eligibility_failures(vault: Any, repository: Any, now_iso: str, item: Any, *, slot_facets: Iterable[str], capability: str, exclusions: Any, view: Any) -> list[str]` ([source](../../../../../../src/learnloop/daily_plan/ad_slot.py), line 344) — Check 0 for one candidate: why it is not in the cell pool now, or why it may not be served.

### Module constants

- `_EPS` ([src/learnloop/daily_plan/ad_slot.py](../../../../../../src/learnloop/daily_plan/ad_slot.py), line 69)

### Explicit exports

`__all__` declares:

- `AdUnavailable`
- `SlotNotAdmitted`
- `SlotSession`
- `decide`
- `deferrals_cleared`
- `eligibility_failures`
- `open_deferrals`
- `open_slot`
- `take_guard_denials`

## Internal implementation anchors

- `_unavailable(code: str) -> AdUnavailable` ([source](../../../../../../src/learnloop/daily_plan/ad_slot.py), line 91)
- `_guarded(run: Any) -> Any` ([source](../../../../../../src/learnloop/daily_plan/ad_slot.py), line 107) — Run an AD phase; any failure becomes :class:`AdUnavailable` carrying only a code, raised OUTSIDE the ``except`` clause (no cause, no context, no inner frames: the final round's codec).
- `_estimator(vault: Any, repository: Any, view: Any) -> Any` ([source](../../../../../../src/learnloop/daily_plan/ad_slot.py), line 123) — AD's candidate estimates (Codex verify F28): the plan's estimator rule on duration evidence read through the slot's material view, so a withheld answer's latency never moves a candidate's estimate or its block-budget check.
- `_inputs(vault: Any, repository: Any, view: Any, items: Sequence[Any], *, slot_visible: bool=True) -> SlotInputs` ([source](../../../../../../src/learnloop/daily_plan/ad_slot.py), line 139)
- `_request(vault: Any, repository: Any, view: Any, facts: SlotFacts, session: SlotSession) -> Any` ([source](../../../../../../src/learnloop/daily_plan/ad_slot.py), line 209)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/daily_plan/engine|learnloop.daily_plan.engine]] — imports `module`; statically calls `decide`, `deferrals_cleared`, `open_deferrals`, `open_slot`, `take_guard_denials`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/adaptive_difficulty/operation|learnloop.adaptive_difficulty.operation]] — imports `ad_operation`, `is_denial`, `take_denials`; calls `ad_operation`, `is_denial`, `take_denials`
- [[Reference/Modules/learnloop/adaptive_difficulty/predict|learnloop.adaptive_difficulty.predict]] — imports `module`; calls `capability`, `facet_weights`
- [[Reference/Modules/learnloop/adaptive_difficulty/selection|learnloop.adaptive_difficulty.selection]] — imports `within_envelope`; calls `within_envelope`
- [[Reference/Modules/learnloop/adaptive_difficulty/serve_inputs|learnloop.adaptive_difficulty.serve_inputs]] — imports `pre_exposed`; calls `pre_exposed`
- [[Reference/Modules/learnloop/adaptive_difficulty/serving|learnloop.adaptive_difficulty.serving]] — imports `SlotCandidate`, `SlotRequest`, `decide_slot`; calls `SlotCandidate`, `SlotRequest`, `decide_slot`
- [[Reference/Modules/learnloop/daily_plan/admission|learnloop.daily_plan.admission]] — imports `new_item_daily_cost`; calls `new_item_daily_cost`
- [[Reference/Modules/learnloop/daily_plan/estimates|learnloop.daily_plan.estimates]] — imports `Estimator`, `load_duration_evidence`; calls `Estimator`, `load_duration_evidence`
- [[Reference/Modules/learnloop/daily_plan/slot_facts_schema|learnloop.daily_plan.slot_facts_schema]] — imports `SlotFacts`, `SlotFactsError`, `SlotInputs`, `decode`, `exclusion_sets`; calls `SlotInputs`, `decode`, `exclusion_sets`
- [[Reference/Modules/learnloop/vault/lifecycle|learnloop.vault.lifecycle]] — imports `practice_item_serving_block`; calls `practice_item_serving_block`

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

- [tests/ad23_contract_helpers.py](../../../../../../tests/ad23_contract_helpers.py) — direct import
- [tests/ad_guard_helpers.py](../../../../../../tests/ad_guard_helpers.py) — direct import
- [tests/test_ad23_intent_compose.py](../../../../../../tests/test_ad23_intent_compose.py) — direct import
  - `test_the_incumbent_hands_ad_only_verdicts`
- [tests/test_ad23_inversion.py](../../../../../../tests/test_ad23_inversion.py) — direct import
  - `test_a_sentinel_the_plan_plants_never_reaches_ad`
  - `test_ad_never_takes_the_plans_objects`
  - `test_high1_a_malformed_stored_context_quoting_held_out_text_never_reaches_ad_or_the_log`
  - `test_property_a_buggy_deciders_pick_outside_the_facts_is_rolled_back`
- [tests/test_forced_withdrawal_records.py](../../../../../../tests/test_forced_withdrawal_records.py) — direct import
  - `test_a_guard_denial_is_recorded_beside_the_jsonl_log_the_report_still_reads`

## Modification guidance

- Make changes here when the responsibility remains ad slot within learnloop.daily_plan; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/daily_plan/ad_slot.py](../../../../../../src/learnloop/daily_plan/ad_slot.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

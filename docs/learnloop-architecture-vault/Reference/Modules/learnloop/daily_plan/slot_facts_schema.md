---
title: "learnloop.daily_plan.slot_facts_schema"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/daily_plan/slot_facts_schema.py"
source_paths:
  - "src/learnloop/daily_plan/slot_facts_schema.py"
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
  - "learnloop.daily_plan.slot_facts_schema module"
  - "src/learnloop/daily_plan/slot_facts_schema.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-daily-plan"
---

# `learnloop.daily_plan.slot_facts_schema`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/daily_plan/_package|learnloop.daily_plan]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.daily_plan.slot_facts_schema` exists within [[Reference/Modules/learnloop/daily_plan/_package|learnloop.daily_plan]] to own the behavior summarized by its module contract: The facts the plan hands adaptive difficulty's slot, and their wire format (the final round: inversion).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/daily_plan/slot_facts_schema.py](../../../../../../src/learnloop/daily_plan/slot_facts_schema.py) |
| Source lines | 256 |
| Owning package | [[Reference/Modules/learnloop/daily_plan/_package|learnloop.daily_plan]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `38c895e230ef534fc7b4a2eff18a51ca456a06a2` |
| Commit timestamp | `2026-10-24T10:23:24-04:00` |

## Public API

- `class SlotFactsError(ValueError)` ([source](../../../../../../src/learnloop/daily_plan/slot_facts_schema.py), line 56) — The wire record does not satisfy the schema (AD is unavailable for the slot).
- `class SlotInputs` ([source](../../../../../../src/learnloop/daily_plan/slot_facts_schema.py), line 61) — What AD's phase 1 hands the plan (AD to the incumbent): the candidates AD's view shows (the slot item and its never-attempted visible siblings at its capability, or the deferred items), their learning objects and AD's estimates, the item states as AD's view reads them and the re…
- `class SlotFacts` ([source](../../../../../../src/learnloop/daily_plan/slot_facts_schema.py), line 76) — The plan's verdicts on one slot (``kind = "slot"``) or on the boundary's AD deferrals (``kind = "deferrals"``, the slot fields None).
- `code_for(prefix: str, raw: Any) -> str` ([source](../../../../../../src/learnloop/daily_plan/slot_facts_schema.py), line 106) — A refusal's code in the closed vocabulary (``constraint:<key>`` or ``pool:<reason>``).
- `encode(facts: SlotFacts) -> str` ([source](../../../../../../src/learnloop/daily_plan/slot_facts_schema.py), line 114) — Canonical JSON (sorted keys).
- `decode(wire: str, *, visible: Iterable[str], learning_objects: Iterable[str]=()) -> SlotFacts` ([source](../../../../../../src/learnloop/daily_plan/slot_facts_schema.py), line 154) — The facts as AD may read them: schema-checked, every item id projected onto ``visible`` (the items AD's own view shows), the slot's LO id onto ``learning_objects`` (those AD's own phase 1 saw), every reason in the closed vocabulary.
- `exclusion_sets(facts: SlotFacts) -> Any` ([source](../../../../../../src/learnloop/daily_plan/slot_facts_schema.py), line 247) — The routine exclusions as AD's check 0 reads them (``ServingExclusions``' attribute names).

### Module constants

- `VERSION` ([src/learnloop/daily_plan/slot_facts_schema.py](../../../../../../src/learnloop/daily_plan/slot_facts_schema.py), line 23)
- `CONSTRAINT_CODES` ([src/learnloop/daily_plan/slot_facts_schema.py](../../../../../../src/learnloop/daily_plan/slot_facts_schema.py), line 27)
- `POOL_CODES` ([src/learnloop/daily_plan/slot_facts_schema.py](../../../../../../src/learnloop/daily_plan/slot_facts_schema.py), line 34)
- `EXCLUSION_NAMES` ([src/learnloop/daily_plan/slot_facts_schema.py](../../../../../../src/learnloop/daily_plan/slot_facts_schema.py), line 44)
- `BUDGET_FIELDS` ([src/learnloop/daily_plan/slot_facts_schema.py](../../../../../../src/learnloop/daily_plan/slot_facts_schema.py), line 49)
- `_ID` ([src/learnloop/daily_plan/slot_facts_schema.py](../../../../../../src/learnloop/daily_plan/slot_facts_schema.py), line 53)
- `_KEYS` ([src/learnloop/daily_plan/slot_facts_schema.py](../../../../../../src/learnloop/daily_plan/slot_facts_schema.py), line 101)

### Explicit exports

`__all__` declares:

- `BUDGET_FIELDS`
- `CONSTRAINT_CODES`
- `EXCLUSION_NAMES`
- `POOL_CODES`
- `SlotFacts`
- `SlotFactsError`
- `SlotInputs`
- `VERSION`
- `code_for`
- `decode`
- `encode`
- `exclusion_sets`

## Internal implementation anchors

- `_id(value: Any, what: str) -> str` ([source](../../../../../../src/learnloop/daily_plan/slot_facts_schema.py), line 132)
- `_optional_id(value: Any, what: str) -> str | None` ([source](../../../../../../src/learnloop/daily_plan/slot_facts_schema.py), line 138)
- `_number(value: Any, what: str) -> float` ([source](../../../../../../src/learnloop/daily_plan/slot_facts_schema.py), line 142)
- `_items(value: Any, what: str, visible: frozenset[str]) -> tuple[str, ...]` ([source](../../../../../../src/learnloop/daily_plan/slot_facts_schema.py), line 148)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/daily_plan/ad_slot|learnloop.daily_plan.ad_slot]] — imports `SlotFacts`, `SlotFactsError`, `SlotInputs`, `decode`, `exclusion_sets`; statically calls `SlotInputs`, `decode`, `exclusion_sets`
- [[Reference/Modules/learnloop/daily_plan/engine|learnloop.daily_plan.engine]] — imports `encode`; statically calls `encode`
- [[Reference/Modules/learnloop/daily_plan/slot_facts|learnloop.daily_plan.slot_facts]] — imports `EXCLUSION_NAMES`, `SlotFacts`, `SlotInputs`; statically calls `SlotFacts`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `datetime`, `json`, `math`, `re`, `types`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/daily_plan/ad_slot|learnloop.daily_plan.ad_slot]], [[Reference/Modules/learnloop/daily_plan/engine|learnloop.daily_plan.engine]], [[Reference/Modules/learnloop/daily_plan/slot_facts|learnloop.daily_plan.slot_facts]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_ad23_intent_compose.py](../../../../../../tests/test_ad23_intent_compose.py) — direct import
  - `test_the_incumbent_hands_ad_only_verdicts`
- [tests/test_ad23_inversion.py](../../../../../../tests/test_ad23_inversion.py) — direct import
  - `test_property_the_wire_is_refused_or_projected`
  - `test_the_codes_vocabulary_covers_the_incumbents_reasons`
  - `test_valid_facts_round_trip`

## Modification guidance

- Make changes here when the responsibility remains slot facts schema within learnloop.daily_plan; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/daily_plan/slot_facts_schema.py](../../../../../../src/learnloop/daily_plan/slot_facts_schema.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

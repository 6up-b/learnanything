---
title: "learnloop.scheduling.intent.model"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/scheduling/intent/model.py"
source_paths:
  - "src/learnloop/scheduling/intent/model.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.scheduling.intent"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Start a Learning Cycle"
  - "Continue a Learning Cycle"
aliases:
  - "learnloop.scheduling.intent.model module"
  - "src/learnloop/scheduling/intent/model.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-scheduling-intent"
---

# `learnloop.scheduling.intent.model`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/scheduling/intent/_package|learnloop.scheduling.intent]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.scheduling.intent.model` exists within [[Reference/Modules/learnloop/scheduling/intent/_package|learnloop.scheduling.intent]] to own the behavior summarized by its module contract: The intent vocabulary (``spec_daily_loop_v1.md`` §5.2) and its snapshots.

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/scheduling/intent/model.py](../../../../../../../src/learnloop/scheduling/intent/model.py) |
| Source lines | 148 |
| Owning package | [[Reference/Modules/learnloop/scheduling/intent/_package|learnloop.scheduling.intent]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `choice_for(action: str, depth_preset: str, disposition: str) -> str` ([source](../../../../../../../src/learnloop/scheduling/intent/model.py), line 77) — The control's word for a commitment's current state.
- `class ChoiceStamp` ([source](../../../../../../../src/learnloop/scheduling/intent/model.py), line 88) — When a commitment was last chosen: ``created_at`` then the row's ULID (insertion order within a second).
- `class CommitmentSnapshot` ([source](../../../../../../../src/learnloop/scheduling/intent/model.py), line 98) — One commitment as resolution reads it (head targets, folded events).
  - `intent_control(self) -> bool` (line 118; public)
  - `scope(self) -> Mapping[str, Any] | None` (line 122; public)
  - `covers_items(self) -> bool` (line 127; public)

### Module constants

- `CHOICES` ([src/learnloop/scheduling/intent/model.py](../../../../../../../src/learnloop/scheduling/intent/model.py), line 16)
- `CHOICE_PRESET` ([src/learnloop/scheduling/intent/model.py](../../../../../../../src/learnloop/scheduling/intent/model.py), line 28)
- `PRESET_CHOICE` ([src/learnloop/scheduling/intent/model.py](../../../../../../../src/learnloop/scheduling/intent/model.py), line 34)
- `CHOICE_DISPOSITION` ([src/learnloop/scheduling/intent/model.py](../../../../../../../src/learnloop/scheduling/intent/model.py), line 37)
- `CHOICE_LABEL` ([src/learnloop/scheduling/intent/model.py](../../../../../../../src/learnloop/scheduling/intent/model.py), line 44)
- `EXCLUDING_DISPOSITIONS` ([src/learnloop/scheduling/intent/model.py](../../../../../../../src/learnloop/scheduling/intent/model.py), line 57)
- `INTENT_CONTROL_VIA` ([src/learnloop/scheduling/intent/model.py](../../../../../../../src/learnloop/scheduling/intent/model.py), line 60)
- `DEADLINE_CHANGE_REASON` ([src/learnloop/scheduling/intent/model.py](../../../../../../../src/learnloop/scheduling/intent/model.py), line 64)
- `SCOPE_KINDS` ([src/learnloop/scheduling/intent/model.py](../../../../../../../src/learnloop/scheduling/intent/model.py), line 68)
- `TIER_PUSH` ([src/learnloop/scheduling/intent/model.py](../../../../../../../src/learnloop/scheduling/intent/model.py), line 71)
- `TIER_KEEP` ([src/learnloop/scheduling/intent/model.py](../../../../../../../src/learnloop/scheduling/intent/model.py), line 72)
- `TIER_UNCOMMITTED` ([src/learnloop/scheduling/intent/model.py](../../../../../../../src/learnloop/scheduling/intent/model.py), line 73)
- `TIER_LIGHT` ([src/learnloop/scheduling/intent/model.py](../../../../../../../src/learnloop/scheduling/intent/model.py), line 74)

### Explicit exports

`__all__` declares:

- `CHOICES`
- `CHOICE_DISPOSITION`
- `CHOICE_LABEL`
- `CHOICE_PRESET`
- `ChoiceStamp`
- `CommitmentSnapshot`
- `DEADLINE_CHANGE_REASON`
- `EXCLUDING_DISPOSITIONS`
- `INTENT_CONTROL_VIA`
- `PRESET_CHOICE`
- `SCOPE_KINDS`
- `TIER_KEEP`
- `TIER_LIGHT`
- `TIER_PUSH`
- `TIER_UNCOMMITTED`
- `choice_for`

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/daily_plan/engine|learnloop.daily_plan.engine]] — imports `CHOICE_PRESET`, `TIER_KEEP`, `TIER_LIGHT`, `TIER_PUSH`
- [[Reference/Modules/learnloop/daily_plan/intent_cost|learnloop.daily_plan.intent_cost]] — imports `CHOICE_DISPOSITION`
- [[Reference/Modules/learnloop/intent/control|learnloop.intent.control]] — imports `CHOICES`, `CHOICE_DISPOSITION`, `CHOICE_LABEL`, `CHOICE_PRESET`, `ChoiceStamp`, `CommitmentSnapshot`, `INTENT_CONTROL_VIA`, `choice_for`; statically calls `ChoiceStamp`, `CommitmentSnapshot`, `choice_for`
- [[Reference/Modules/learnloop/intent/deadline|learnloop.intent.deadline]] — imports `CHOICE_LABEL`, `DEADLINE_CHANGE_REASON`, `choice_for`; statically calls `choice_for`
- [[Reference/Modules/learnloop/scheduling/intent/resolution|learnloop.scheduling.intent.resolution]] — imports `ChoiceStamp`, `CommitmentSnapshot`, `DEADLINE_CHANGE_REASON`, `EXCLUDING_DISPOSITIONS`, `INTENT_CONTROL_VIA`, `TIER_KEEP`, `TIER_LIGHT`, `TIER_PUSH`, `TIER_UNCOMMITTED`, `choice_for`; statically calls `ChoiceStamp`, `CommitmentSnapshot`, `choice_for`
- [[Reference/Modules/learnloop/scheduling/intent/serving|learnloop.scheduling.intent.serving]] — imports `CommitmentSnapshot`
- [[Reference/Modules/learnloop/source_retrieval/reading_paths|learnloop.source_retrieval.reading_paths]] — imports `CHOICE_LABEL`, `choice_for`; statically calls `choice_for`
- [[Reference/Modules/learnloop_sidecar/handlers/intent|learnloop_sidecar.handlers.intent]] — imports `SCOPE_KINDS`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Start a Learning Cycle]]
- [[Continue a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/daily_plan/engine|learnloop.daily_plan.engine]], [[Reference/Modules/learnloop/daily_plan/intent_cost|learnloop.daily_plan.intent_cost]], [[Reference/Modules/learnloop/intent/control|learnloop.intent.control]], [[Reference/Modules/learnloop/intent/deadline|learnloop.intent.deadline]], [[Reference/Modules/learnloop/scheduling/intent/resolution|learnloop.scheduling.intent.resolution]] and 3 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_ad23_inversion.py](../../../../../../../tests/test_ad23_inversion.py) — direct import
  - `test_the_codes_vocabulary_covers_the_incumbents_reasons`
- [tests/test_ad23_pool_membership.py](../../../../../../../tests/test_ad23_pool_membership.py) — direct import
- [tests/test_intent_codex_review.py](../../../../../../../tests/test_intent_codex_review.py) — direct import
  - `test_f6_the_chooser_takes_the_master_block_first_in_re_entry`
- [tests/test_intent_resolution.py](../../../../../../../tests/test_intent_resolution.py) — direct import
  - `test_check_dates_read_the_due_hint_then_the_default_delay`
  - `test_ties_go_to_the_item_level_then_the_higher_target`

## Modification guidance

- Change model policy here when scheduling owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/scheduling/intent/model.py](../../../../../../../src/learnloop/scheduling/intent/model.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

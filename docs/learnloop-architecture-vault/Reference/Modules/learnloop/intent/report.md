---
title: "learnloop.intent.report"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/intent/report.py"
source_paths:
  - "src/learnloop/intent/report.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.intent"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.intent.report module"
  - "src/learnloop/intent/report.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-intent"
---

# `learnloop.intent.report`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/intent/_package|learnloop.intent]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.intent.report` exists within [[Reference/Modules/learnloop/intent/_package|learnloop.intent]] to own the behavior summarized by its module contract: Intent in ``learnloop plan report`` (spec §5.3): what is committed, and the recall-target fallbacks.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/intent/report.py](../../../../../../src/learnloop/intent/report.py) |
| Source lines | 74 |
| Owning package | [[Reference/Modules/learnloop/intent/_package|learnloop.intent]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `intent_report(vault: Any, connection: Any) -> dict[str, Any]` ([source](../../../../../../src/learnloop/intent/report.py), line 22)

### Explicit exports

`__all__` declares:

- `intent_report`

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/plan|learnloop.cli.plan]] — imports `intent_report`; statically calls `intent_report`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/scheduling/fsrs|learnloop.scheduling.fsrs]] — imports `FSRS6_DEFAULT_WEIGHTS`
- [[Reference/Modules/learnloop/scheduling/intent/recall_targets|learnloop.scheduling.intent.recall_targets]] — imports `effective_due`, `load_anchors`; calls `effective_due`, `load_anchors`
- [[Reference/Modules/learnloop/scheduling/intent/resolution|learnloop.scheduling.intent.resolution]] — imports `Resolution`, `load_snapshots`; calls `Resolution`, `load_snapshots`
- [[Reference/Modules/learnloop/scheduling/intent/serving|learnloop.scheduling.intent.serving]] — imports `intent_enabled`; calls `intent_enabled`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/plan|learnloop.cli.plan]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_intent_plan.py](../../../../../../tests/test_intent_plan.py) — direct import
  - `test_plan_report_counts_the_recall_target_fallbacks`

## Modification guidance

- Make changes here when the responsibility remains report within learnloop.intent; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/intent/report.py](../../../../../../src/learnloop/intent/report.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

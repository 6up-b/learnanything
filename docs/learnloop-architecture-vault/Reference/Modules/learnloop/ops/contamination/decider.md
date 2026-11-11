---
title: "learnloop.ops.contamination.decider"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/ops/contamination/decider.py"
source_paths:
  - "src/learnloop/ops/contamination/decider.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.ops.contamination"
layer: "domain"
concepts:
  - "State and Persistence"
  - "Configuration"
workflows:
  - "Doctor Migrations and Recovery"
aliases:
  - "learnloop.ops.contamination.decider module"
  - "src/learnloop/ops/contamination/decider.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-ops-contamination"
---

# `learnloop.ops.contamination.decider`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/ops/contamination/_package|learnloop.ops.contamination]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.ops.contamination.decider` exists within [[Reference/Modules/learnloop/ops/contamination/_package|learnloop.ops.contamination]] to own the behavior summarized by its module contract: The Decider's leak / reveal verdict (Tier 1, mvp-0.22).

The authoritative system-level explanation remains in [[State and Persistence]], [[Configuration]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/ops/contamination/decider.py](../../../../../../../src/learnloop/ops/contamination/decider.py) |
| Source lines | 57 |
| Owning package | [[Reference/Modules/learnloop/ops/contamination/_package|learnloop.ops.contamination]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `question(task: str) -> ChoiceQuestion` ([source](../../../../../../../src/learnloop/ops/contamination/decider.py), line 24)
- `judge(vault: Any, repository: Any, request: JudgeRequest, budget: Any, *, run_id: str, candidates: int=0, pairs: int=0) -> bool` ([source](../../../../../../../src/learnloop/ops/contamination/decider.py), line 33) — Ledger the Decider's verdict for ``request``; False hands it to the LLM judge.

### Explicit exports

`__all__` declares:

- `judge`
- `question`

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/ops/contamination/judge|learnloop.ops.contamination.judge]] — imports `module`; statically calls `judge`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/decisions|learnloop.ai.decisions]] — imports `ChoiceQuestion`; calls `ChoiceQuestion`
- [[Reference/Modules/learnloop/ai/execution|learnloop.ai.execution]] — imports `content_key`; calls `content_key`
- [[Reference/Modules/learnloop/ai/review_spend|learnloop.ai.review_spend]] — imports `ReviewSpend`; calls `ReviewSpend`
- [[Reference/Modules/learnloop/decider_judgments|learnloop.decider_judgments]] — imports `decide`; calls `decide`
- [[Reference/Modules/learnloop/ops/contamination/judge|learnloop.ops.contamination.judge]] — imports `JudgeRequest`, `OPERATIONS`, `ledger_verdict`; calls `ledger_verdict`

### Platform and third-party dependencies

- Standard library: `__future__`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Doctor Migrations and Recovery]]

Static participation evidence comes from [[Reference/Modules/learnloop/ops/contamination/judge|learnloop.ops.contamination.judge]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

No test imports this module directly. These tests exercise a direct production consumer:

- [tests/contamination_report_helpers.py](../../../../../../../tests/contamination_report_helpers.py) — imports consumer [[Reference/Modules/learnloop/ops/contamination/judge|learnloop.ops.contamination.judge]]
- [tests/test_tier1_decider.py](../../../../../../../tests/test_tier1_decider.py) — imports consumer [[Reference/Modules/learnloop/ops/contamination/judge|learnloop.ops.contamination.judge]]

## Modification guidance

- Make changes here when the responsibility remains decider within learnloop.ops.contamination; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/ops/contamination/decider.py](../../../../../../../src/learnloop/ops/contamination/decider.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

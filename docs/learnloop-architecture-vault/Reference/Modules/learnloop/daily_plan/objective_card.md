---
title: "learnloop.daily_plan.objective_card"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/daily_plan/objective_card.py"
source_paths:
  - "src/learnloop/daily_plan/objective_card.py"
source_commit: "838d8ee1fcee48de3b5b41f59e451f042ec9a690"
source_commit_timestamp: "2026-11-05T04:03:05-05:00"
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
  - "learnloop.daily_plan.objective_card module"
  - "src/learnloop/daily_plan/objective_card.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-daily-plan"
---

# `learnloop.daily_plan.objective_card`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/daily_plan/_package|learnloop.daily_plan]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.daily_plan.objective_card` exists within [[Reference/Modules/learnloop/daily_plan/_package|learnloop.daily_plan]] to own the behavior summarized by its module contract: Router objective RO4 (spec §8.3): the LLM policy's card, a decision-level variant of RO2's H3 card.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/daily_plan/objective_card.py](../../../../../../src/learnloop/daily_plan/objective_card.py) |
| Source lines | 110 |
| Owning package | [[Reference/Modules/learnloop/daily_plan/_package|learnloop.daily_plan]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `838d8ee1fcee48de3b5b41f59e451f042ec9a690` |
| Commit timestamp | `2026-11-05T04:03:05-05:00` |

## Public API

- `decision_card(vault: Any, repository: Any, candidates: Sequence[Any], *, served_at: str, goals: Mapping[str, Any], session: Mapping[str, Any], budget: int) -> dict[str, Any]` ([source](../../../../../../src/learnloop/daily_plan/objective_card.py), line 77) — The frozen card (the state), its evidence ids and what the budget left out.

### Module constants

- `CARD_VERSION` ([src/learnloop/daily_plan/objective_card.py](../../../../../../src/learnloop/daily_plan/objective_card.py), line 22)
- `_SECTION_ORDER` ([src/learnloop/daily_plan/objective_card.py](../../../../../../src/learnloop/daily_plan/objective_card.py), line 24)

### Explicit exports

`__all__` declares:

- `CARD_VERSION`
- `decision_card`

## Internal implementation anchors

- `_size(state: Mapping[str, Any]) -> int` ([source](../../../../../../src/learnloop/daily_plan/objective_card.py), line 30)
- `_merged(built: Sequence[Mapping[str, Any]]) -> tuple[dict[str, list[dict[str, Any]]], list[str], list[str]]` ([source](../../../../../../src/learnloop/daily_plan/objective_card.py), line 34)
- `_trim(state: dict[str, Any], budget: int) -> dict[str, dict[str, int]]` ([source](../../../../../../src/learnloop/daily_plan/objective_card.py), line 55) — Oldest first within each section, one entry per non-empty section per round, until it fits.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/daily_plan/objective_chooser|learnloop.daily_plan.objective_chooser]] — imports `decision_card`; statically calls `decision_card`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/adaptive_difficulty/history_card|learnloop.adaptive_difficulty.history_card]] — imports `module`; calls `decision_sections_entry`
- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `json`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/daily_plan/objective_chooser|learnloop.daily_plan.objective_chooser]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_ro4_trace_report.py](../../../../../../tests/test_ro4_trace_report.py) — direct import
  - `test_protection_holds_on_the_llm_policys_card`

## Modification guidance

- Make changes here when the responsibility remains objective card within learnloop.daily_plan; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/daily_plan/objective_card.py](../../../../../../src/learnloop/daily_plan/objective_card.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

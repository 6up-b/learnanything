---
title: "learnloop.diagnosis.offline_review.decider_links"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/diagnosis/offline_review/decider_links.py"
source_paths:
  - "src/learnloop/diagnosis/offline_review/decider_links.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.diagnosis.offline_review"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Process Model Output"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.diagnosis.offline_review.decider_links module"
  - "src/learnloop/diagnosis/offline_review/decider_links.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-diagnosis-offline-review"
---

# `learnloop.diagnosis.offline_review.decider_links`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/diagnosis/offline_review/_package|learnloop.diagnosis.offline_review]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.diagnosis.offline_review.decider_links` exists within [[Reference/Modules/learnloop/diagnosis/offline_review/_package|learnloop.diagnosis.offline_review]] to own the behavior summarized by its module contract: The Decider's pattern-link verdicts in the offline review (Tier 1, mvp-0.22).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/diagnosis/offline_review/decider_links.py](../../../../../../../src/learnloop/diagnosis/offline_review/decider_links.py) |
| Source lines | 83 |
| Owning package | [[Reference/Modules/learnloop/diagnosis/offline_review/_package|learnloop.diagnosis.offline_review]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `link_question(label: str) -> ChoiceQuestion` ([source](../../../../../../../src/learnloop/diagnosis/offline_review/decider_links.py), line 38)
- `judge_links(vault: Any, repository: Any, spend: Any, prompt: str, labels: Mapping[str, str], left_id: str, fallback: Callable[[], LinkJudgment], *, llm_model: str, admit: Admit | None=None) -> tuple[LinkJudgment, Producers]` ([source](../../../../../../../src/learnloop/diagnosis/offline_review/decider_links.py), line 46) — The deciding verdict of every label; ``fallback()`` is the LLM's batch call.

### Module constants

- `LINK_TASK` ([src/learnloop/diagnosis/offline_review/decider_links.py](../../../../../../../src/learnloop/diagnosis/offline_review/decider_links.py), line 28)
- `LINK_OPTIONS` ([src/learnloop/diagnosis/offline_review/decider_links.py](../../../../../../../src/learnloop/diagnosis/offline_review/decider_links.py), line 29)

### Explicit exports

`__all__` declares:

- `LINK_OPTIONS`
- `LINK_TASK`
- `Producers`
- `judge_links`
- `link_question`

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/diagnosis/offline_review/runner|learnloop.diagnosis.offline_review.runner]] — imports `module`; statically calls `judge_links`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/decisions|learnloop.ai.decisions]] — imports `ChoiceQuestion`; calls `ChoiceQuestion`
- [[Reference/Modules/learnloop/decider_judgments|learnloop.decider_judgments]] — imports `Admit`, `Decision`, `decide`, `log_llm`; calls `decide`, `log_llm`
- [[Reference/Modules/learnloop/diagnosis/offline_review/judge|learnloop.diagnosis.offline_review.judge]] — imports `LinkJudgment`, `LinkVerdict`; calls `LinkJudgment`, `LinkVerdict`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/diagnosis/offline_review/runner|learnloop.diagnosis.offline_review.runner]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_tier1_decider.py](../../../../../../../tests/test_tier1_decider.py) — direct import
  - `test_link_judgments`
  - `test_links_the_decider_answered_are_never_paid_for_again_when_the_fallback_failed`

## Modification guidance

- Change decider links policy here when diagnosis owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/diagnosis/offline_review/decider_links.py](../../../../../../../src/learnloop/diagnosis/offline_review/decider_links.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

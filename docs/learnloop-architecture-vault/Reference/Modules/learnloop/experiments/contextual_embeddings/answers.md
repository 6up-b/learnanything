---
title: "learnloop.experiments.contextual_embeddings.answers"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/experiments/contextual_embeddings/answers.py"
source_paths:
  - "src/learnloop/experiments/contextual_embeddings/answers.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.experiments.contextual_embeddings"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.experiments.contextual_embeddings.answers module"
  - "src/learnloop/experiments/contextual_embeddings/answers.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-experiments-contextual-embeddings"
---

# `learnloop.experiments.contextual_embeddings.answers`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/experiments/contextual_embeddings/_package|learnloop.experiments.contextual_embeddings]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.experiments.contextual_embeddings.answers` exists within [[Reference/Modules/learnloop/experiments/contextual_embeddings/_package|learnloop.experiments.contextual_embeddings]] to own the behavior summarized by its module contract: Blind answer evaluation for the E0 finalists (spec §5.2, §5.3).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/experiments/contextual_embeddings/answers.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/answers.py) |
| Source lines | 190 |
| Owning package | [[Reference/Modules/learnloop/experiments/contextual_embeddings/_package|learnloop.experiments.contextual_embeddings]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class TutorAnswer(WireModel)` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/answers.py), line 41)
- `class AnswerScore(WireModel)` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/answers.py), line 47)
- `class ScoredAnswer` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/answers.py), line 55)
  - `passes(self) -> bool | None` (line 76; public)
- `tutor_prompt(question: BankQuestion, delivered: Delivered) -> tuple[str, dict[str, tuple[str, str]]]` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/answers.py), line 82)
- `judge_prompt(question: BankQuestion, delivered: Delivered, answer: TutorAnswer, *, order_salt: int) -> str` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/answers.py), line 92)
- `answer_and_judge(question: BankQuestion, arm: str, delivered: Delivered, caller: Any, *, retrieval_latency_s: float | None=None) -> ScoredAnswer` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/answers.py), line 117) — Answer and judge one delivery.
- `summarize_answers(scored: Sequence[ScoredAnswer], planned: Mapping[str, int] | None=None) -> dict[str, dict[str, Any]]` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/answers.py), line 158) — Per delivered arm: the pass share and components over the answers made, with the PLANNED denominator beside them (``planned``: answers the frozen plan owes each planned arm; a fallback counts under its own name and as missing for the arm it stood in for: Codex review F17).

### Module constants

- `TUTOR_INSTRUCTIONS` ([src/learnloop/experiments/contextual_embeddings/answers.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/answers.py), line 28)
- `JUDGE_INSTRUCTIONS` ([src/learnloop/experiments/contextual_embeddings/answers.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/answers.py), line 32)

## Internal implementation anchors

- `_measured(caller: Any, fallback: float) -> tuple[float, bool]` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/answers.py), line 101)
- `_record(caller: Any, question: BankQuestion, arm: str, verdict: Mapping[str, str], role: str) -> None` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/answers.py), line 108)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/experiments/contextual_embeddings/paid|learnloop.experiments.contextual_embeddings.paid]] — imports `ScoredAnswer`, `answer_and_judge`, `summarize_answers`; statically calls `answer_and_judge`, `summarize_answers`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/schemas|learnloop.ai.schemas]] — imports `WireModel`
- [[Reference/Modules/learnloop/ai/transport|learnloop.ai.transport]] — imports `render_structured_prompt`; calls `render_structured_prompt`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/bank|learnloop.experiments.contextual_embeddings.bank]] — imports `BankQuestion`, `stable_order`; calls `stable_order`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/delivery|learnloop.experiments.contextual_embeddings.delivery]] — imports `Delivered`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/pins|learnloop.experiments.contextual_embeddings.pins]] — imports `module`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `json`, `time`, `typing`
- Third party: `pydantic`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/experiments/contextual_embeddings/paid|learnloop.experiments.contextual_embeddings.paid]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_e0_review_round1.py](../../../../../../../tests/test_e0_review_round1.py) — direct import
  - `test_f10_verdicts_enter_judgment_ledger_once`
  - `test_f6_deictic_questions_carry_their_own_selection_to_every_role`
- [tests/test_e0_review_round2.py](../../../../../../../tests/test_e0_review_round2.py) — direct import
  - `test_f6_a_rejected_quote_never_reaches_delivery_tutor_or_judges`

## Modification guidance

- Make changes here when the responsibility remains answers within learnloop.experiments.contextual_embeddings; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/experiments/contextual_embeddings/answers.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/answers.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

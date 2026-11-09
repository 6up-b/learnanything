---
title: "learnloop.diagnosis.text_gaps.tier1"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/diagnosis/text_gaps/tier1.py"
source_paths:
  - "src/learnloop/diagnosis/text_gaps/tier1.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.diagnosis.text_gaps"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Process Model Output"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.diagnosis.text_gaps.tier1 module"
  - "src/learnloop/diagnosis/text_gaps/tier1.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-diagnosis-text-gaps"
---

# `learnloop.diagnosis.text_gaps.tier1`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/diagnosis/text_gaps/_package|learnloop.diagnosis.text_gaps]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.diagnosis.text_gaps.tier1` exists within [[Reference/Modules/learnloop/diagnosis/text_gaps/_package|learnloop.diagnosis.text_gaps]] to own the behavior summarized by its module contract: Learner-text gaps with the Decider as the authoritative judge (Tier 1, mvp-0.22).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/diagnosis/text_gaps/tier1.py](../../../../../../../src/learnloop/diagnosis/text_gaps/tier1.py) |
| Source lines | 305 |
| Owning package | [[Reference/Modules/learnloop/diagnosis/text_gaps/_package|learnloop.diagnosis.text_gaps]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class ArgmaxPairExecutor(DeciderPairExecutor)` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/tier1.py), line 90) — The Decider as the authoritative pair judge: the argmax of its distribution decides.
  - `__init__(self, budget: TextBudget, client: Any) -> None` (line 100; internal)
  - `__call__(self, prompt: str, result_model: type[SameOrDifferent], purpose: str) -> tuple[SameOrDifferent, str]` (line 104; internal)
- `judge_all(repository: Repository, kind: Any, pairs: list, *, budget: TextBudget, clients: PipelineClients) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/tier1.py), line 138) — The Decider's verdict on every pair, the LLM's where it gave none (see the module doc).
- `ask_needed(vault: LoadedVault, repository: Repository, budget: TextBudget, *, context: Mapping[str, Any], learning_object_id: str, practice_item_id: str, clients: PipelineClients) -> dict[str, dict[str, Any]]` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/tier1.py), line 208) — The Decider's "needed?" verdict, else the LLM judge's; ``selected`` is the deciding one.
- `decide_kind(vault: LoadedVault, repository: Repository, text: LearnerText, budget: TextBudget, clients: PipelineClients, progress: Mapping[str, Any], checkpoint: Callable[..., None]) -> tuple[GapReading | None, DeciderKind, str, str]` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/tier1.py), line 266) — The Decider's kind, authoritative; the context model names the gap (``pipeline._decide``).

### Module constants

- `JUDGE_SWITCH` ([src/learnloop/diagnosis/text_gaps/tier1.py](../../../../../../../src/learnloop/diagnosis/text_gaps/tier1.py), line 82)
- `KIND_SWITCH` ([src/learnloop/diagnosis/text_gaps/tier1.py](../../../../../../../src/learnloop/diagnosis/text_gaps/tier1.py), line 83)
- `ARGMAX_PRODUCER_SUFFIX` ([src/learnloop/diagnosis/text_gaps/tier1.py](../../../../../../../src/learnloop/diagnosis/text_gaps/tier1.py), line 87)

### Explicit exports

`__all__` declares:

- `ARGMAX_PRODUCER_SUFFIX`
- `ArgmaxPairExecutor`
- `JUDGE_SWITCH`
- `KIND_SWITCH`
- `ask_needed`
- `decide_kind`
- `judge_all`

## Internal implementation anchors

- `_failure_status(pair: JudgedPair) -> str` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/tier1.py), line 118)
- `_record_failures(repository: Repository, kind: Any, pairs: Sequence[Any], *, model: str, statuses: Mapping[int, tuple[str, str | None]]) -> None` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/tier1.py), line 128)
- `_recorded_kind(repository: Repository, text: LearnerText) -> Decision | None` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/tier1.py), line 233) — The Decider's Tier-1 answer already on the ledger for this text's kind, or None.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/diagnosis/text_gaps/pipeline|learnloop.diagnosis.text_gaps.pipeline]] — imports `module`; statically calls `ask_needed`, `decide_kind`, `judge_all`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/decisions|learnloop.ai.decisions]] — imports `choice_probabilities`; calls `choice_probabilities`
- [[Reference/Modules/learnloop/ai/errors|learnloop.ai.errors]] — imports `AIInterrupted`
- [[Reference/Modules/learnloop/ai/execution|learnloop.ai.execution]] — imports `content_key`; calls `content_key`
- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/decider_judgments|learnloop.decider_judgments]] — imports `Decision`, `FAILURE_VERDICTS`, `NoClearAnswer`, `VERSION`, `argmax`, `decide`, `record_failure`; calls `Decision`, `NoClearAnswer`, `argmax`, `decide`, `record_failure`
- [[Reference/Modules/learnloop/diagnosis/recurrence/judging|learnloop.diagnosis.recurrence.judging]] — imports `estimate_tokens`; calls `estimate_tokens`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/contract|learnloop.diagnosis.text_gaps.contract]] — imports `DECIDER_PAIR_QUESTION_SET`, `DECIDER_ROUTE`, `GapReading`, `KIND_QUESTION`, `LearnerText`, `NEEDED_QUESTION`, `NEEDED_TASK`; calls `GapReading`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/judges|learnloop.diagnosis.text_gaps.judges]] — imports `DeciderKind`, `DeciderPairExecutor`, `LLMPairExecutor`, `TextBudget`, `ask_needed`, `decider_rationale`, `kind_input_hash`, `kind_state`, `log_reading`, `needed_prompt`, `read_text`; calls `DeciderKind`, `LLMPairExecutor`, `ask_needed`, `decider_rationale`, `kind_input_hash`, `kind_state`, `log_reading`, `needed_prompt`, `read_text`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/pipeline|learnloop.diagnosis.text_gaps.pipeline]] — imports `PipelineClients`, `ReadingDeferred`, `_stopped`, `_unsettled`, `_verdicts`, `_with_standing`, `authoritative`; calls `ReadingDeferred`, `_stopped`, `_unsettled`, `_verdicts`, `_with_standing`, `authoritative`
- [[Reference/Modules/learnloop/matching/judge|learnloop.matching.judge]] — imports `JudgedPair`, `SameOrDifferent`, `judge_pairs`, `pair_input_hash`; calls `judge_pairs`, `pair_input_hash`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `json`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/diagnosis/text_gaps/pipeline|learnloop.diagnosis.text_gaps.pipeline]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_tier1_decider.py](../../../../../../../tests/test_tier1_decider.py) — direct import

## Modification guidance

- Change tier1 policy here when diagnosis owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/diagnosis/text_gaps/tier1.py](../../../../../../../src/learnloop/diagnosis/text_gaps/tier1.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

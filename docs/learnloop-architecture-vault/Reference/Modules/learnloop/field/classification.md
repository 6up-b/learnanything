---
title: "learnloop.field.classification"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/field/classification.py"
source_paths:
  - "src/learnloop/field/classification.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.field"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.field.classification module"
  - "src/learnloop/field/classification.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-field"
---

# `learnloop.field.classification`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/field/_package|learnloop.field]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.field.classification` exists within [[Reference/Modules/learnloop/field/_package|learnloop.field]] to own the behavior summarized by its module contract: Explicit, bounded paid classification; never imported by signal replay.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/field/classification.py](../../../../../../src/learnloop/field/classification.py) |
| Source lines | 232 |
| Owning package | [[Reference/Modules/learnloop/field/_package|learnloop.field]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `load_cached_classifications(connection: Any) -> tuple[dict[str, Any], ...]` ([source](../../../../../../src/learnloop/field/classification.py), line 61)
- `classify_missing_questions(repository: Any, events: Iterable[Mapping[str, Any]], *, model: str, classify: Callable[[dict[str, Any]], Mapping[str, Any]], estimate_per_question: SpendEstimate, caps: SpendCaps, enabled: bool=False, dry_run: bool=False, cancelled: Callable[[], bool] | None=None, subscription: bool=False, decider: Callable | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/field/classification.py), line 72) — Classify missing information, recording every returned verdict.

### Module constants

- `PROMPT_VERSION` ([src/learnloop/field/classification.py](../../../../../../src/learnloop/field/classification.py), line 37)
- `TASK` ([src/learnloop/field/classification.py](../../../../../../src/learnloop/field/classification.py), line 38)

## Internal implementation anchors

- `_validated(raw: Mapping[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/field/classification.py), line 41)
- `_price_per_token(estimate: SpendEstimate) -> float | None` ([source](../../../../../../src/learnloop/field/classification.py), line 55)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/field_classification|learnloop.cli.field_classification]] — imports `PROMPT_VERSION`, `TASK`, `classify_missing_questions`; statically calls `classify_missing_questions`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/errors|learnloop.ai.errors]] — imports `AIInterrupted`
- [[Reference/Modules/learnloop/ai/execution|learnloop.ai.execution]] — imports `observe_model_calls`; calls `observe_model_calls`
- [[Reference/Modules/learnloop/ai/spend|learnloop.ai.spend]] — imports `ESTIMATED_ONLY`, `SpendBudget`, `SpendCaps`, `SpendEstimate`, `SpendLimitExceeded`, `subscription_usage_estimate`; calls `SpendBudget`, `SpendEstimate`, `SpendLimitExceeded`, `subscription_usage_estimate`
- [[Reference/Modules/learnloop/db/stores/field|learnloop.db.stores.field]] — imports `insert_question_classification`; calls `insert_question_classification`
- [[Reference/Modules/learnloop/db/stores/judgments|learnloop.db.stores.judgments]] — imports `append_judgment`; calls `append_judgment`
- [[Reference/Modules/learnloop/field/signals|learnloop.field.signals]] — imports `QUESTION_TYPES`, `classification_input`, `input_hash`; calls `classification_input`, `input_hash`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `datetime`, `hashlib`, `json`, `typing`, `uuid`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/field_classification|learnloop.cli.field_classification]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_field_signal_production_paths.py](../../../../../../tests/test_field_signal_production_paths.py) — direct import
- [tests/test_interaction_signals.py](../../../../../../tests/test_interaction_signals.py) — direct import
  - `test_invalid_verdict_logged_not_cached`
  - `test_missing_only_cache_resume_ledger_and_no_replay_calls`
- [tests/test_tier1_decider.py](../../../../../../tests/test_tier1_decider.py) — direct import
  - `test_field_question_classification`

## Modification guidance

- Make changes here when the responsibility remains classification within learnloop.field; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/field/classification.py](../../../../../../src/learnloop/field/classification.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

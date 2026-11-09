---
title: "learnloop.diagnosis.offline_review.probes"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/diagnosis/offline_review/probes.py"
source_paths:
  - "src/learnloop/diagnosis/offline_review/probes.py"
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
  - "learnloop.diagnosis.offline_review.probes module"
  - "src/learnloop/diagnosis/offline_review/probes.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-diagnosis-offline-review"
---

# `learnloop.diagnosis.offline_review.probes`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/diagnosis/offline_review/_package|learnloop.diagnosis.offline_review]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.diagnosis.offline_review.probes` exists within [[Reference/Modules/learnloop/diagnosis/offline_review/_package|learnloop.diagnosis.offline_review]] to own the behavior summarized by its module contract: E1 grader probes (Slice 1 §13, added 2026-10-11).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/diagnosis/offline_review/probes.py](../../../../../../../src/learnloop/diagnosis/offline_review/probes.py) |
| Source lines | 289 |
| Owning package | [[Reference/Modules/learnloop/diagnosis/offline_review/_package|learnloop.diagnosis.offline_review]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class ValidAlternativeDraft(WireModel)` ([source](../../../../../../../src/learnloop/diagnosis/offline_review/probes.py), line 69)
- `class SyntheticErrorDraft(WireModel)` ([source](../../../../../../../src/learnloop/diagnosis/offline_review/probes.py), line 75)
- `class ParaphraseDraft(WireModel)` ([source](../../../../../../../src/learnloop/diagnosis/offline_review/probes.py), line 85)
- `valid_alternative_prompt(vault: LoadedVault, item: PracticeItem) -> str` ([source](../../../../../../../src/learnloop/diagnosis/offline_review/probes.py), line 108)
- `synthetic_error_prompt(vault: LoadedVault, item: PracticeItem) -> str` ([source](../../../../../../../src/learnloop/diagnosis/offline_review/probes.py), line 127)
- `paraphrase_prompt(vault: LoadedVault, item: PracticeItem, answer: str) -> str` ([source](../../../../../../../src/learnloop/diagnosis/offline_review/probes.py), line 147)
- `request_valid_alternative(client: OperationClient, prompt: str) -> ValidAlternativeDraft` ([source](../../../../../../../src/learnloop/diagnosis/offline_review/probes.py), line 163)
- `request_synthetic_error(client: OperationClient, prompt: str) -> SyntheticErrorDraft` ([source](../../../../../../../src/learnloop/diagnosis/offline_review/probes.py), line 167)
- `request_paraphrase(client: OperationClient, prompt: str) -> ParaphraseDraft` ([source](../../../../../../../src/learnloop/diagnosis/offline_review/probes.py), line 171)
- `verify_alternative(item: PracticeItem, draft: ValidAlternativeDraft) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/diagnosis/offline_review/probes.py), line 179) — A deterministic check of the SUBMITTED derivation; never the model's word.
- `verify_synthetic_error(vault: LoadedVault, item: PracticeItem, draft: SyntheticErrorDraft) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/diagnosis/offline_review/probes.py), line 218) — Establish a synthetic answer's outcome independently of its generator.
- `is_reference_bearing(item: PracticeItem) -> bool` ([source](../../../../../../../src/learnloop/diagnosis/offline_review/probes.py), line 263)

### Module constants

- `PROBE_PROMPT_VERSION` ([src/learnloop/diagnosis/offline_review/probes.py](../../../../../../../src/learnloop/diagnosis/offline_review/probes.py), line 65)
- `PROBES` ([src/learnloop/diagnosis/offline_review/probes.py](../../../../../../../src/learnloop/diagnosis/offline_review/probes.py), line 66)
- `_CHECKABLE_STEPS` ([src/learnloop/diagnosis/offline_review/probes.py](../../../../../../../src/learnloop/diagnosis/offline_review/probes.py), line 101)

### Explicit exports

`__all__` declares:

- `PROBES`
- `PROBE_PROMPT_VERSION`
- `ParaphraseDraft`
- `RelationCheck`
- `SyntheticErrorDraft`
- `ValidAlternativeDraft`
- `asserted_conclusion`
- `check_relations`
- `final_answer_check`
- `is_reference_bearing`
- `paraphrase_prompt`
- `request_paraphrase`
- `request_synthetic_error`
- `request_valid_alternative`
- `safe_math_text`
- `synthetic_error_prompt`
- `valid_alternative_prompt`
- `verify_alternative`
- `verify_synthetic_error`

## Internal implementation anchors

- `_item_payload(vault: LoadedVault, item: PracticeItem) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/diagnosis/offline_review/probes.py), line 89)
- `_expected_text(item: PracticeItem) -> str` ([source](../../../../../../../src/learnloop/diagnosis/offline_review/probes.py), line 175)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/diagnosis/offline_review/runner|learnloop.diagnosis.offline_review.runner]] — imports `module`; statically calls `is_reference_bearing`, `paraphrase_prompt`, `synthetic_error_prompt`, `valid_alternative_prompt`, `verify_alternative`, `verify_synthetic_error`
- [[Reference/Modules/learnloop/diagnosis/split/pfc_report|learnloop.diagnosis.split.pfc_report]] — imports `is_reference_bearing`, `request_valid_alternative`, `valid_alternative_prompt`, `verify_alternative`; statically calls `is_reference_bearing`, `request_valid_alternative`, `valid_alternative_prompt`, `verify_alternative`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/schemas|learnloop.ai.schemas]] — imports `WireModel`
- [[Reference/Modules/learnloop/ai/transport|learnloop.ai.transport]] — imports `OperationClient`, `execute_structured_operation`, `render_structured_prompt`; calls `execute_structured_operation`, `render_structured_prompt`
- [[Reference/Modules/learnloop/attempts/answer_check|learnloop.attempts.answer_check]] — imports `RelationCheck`, `answers_differ`, `answers_equal`, `asserted_answer`, `asserted_conclusion`, `check_relations`, `final_answer_check`, `reference_answers`, `safe_math_text`; calls `answers_differ`, `answers_equal`, `asserted_answer`, `asserted_conclusion`, `check_relations`, `reference_answers`
- [[Reference/Modules/learnloop/attempts/grading|learnloop.attempts.grading]] — imports `resolved_rubric`; calls `resolved_rubric`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`, `PracticeItem`
- [[Reference/Modules/learnloop/vault/required_method|learnloop.vault.required_method]] — imports `presented_prompt`; calls `presented_prompt`

### Platform and third-party dependencies

- Standard library: `__future__`, `json`, `typing`
- Third party: `pydantic`

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/diagnosis/offline_review/runner|learnloop.diagnosis.offline_review.runner]], [[Reference/Modules/learnloop/diagnosis/split/pfc_report|learnloop.diagnosis.split.pfc_report]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/diagnosis_fakes.py](../../../../../../../tests/diagnosis_fakes.py) — direct import
- [tests/test_diagnose_review.py](../../../../../../../tests/test_diagnose_review.py) — direct import
  - `test_a_synthetic_error_is_known_only_when_the_planted_error_is_verified`
  - `test_a_valid_alternative_is_verified_on_its_submitted_derivation`
  - `test_every_relation_in_an_alternative_is_checked_never_skipped`
  - `test_numeric_checks_keep_unary_signs_and_whole_expressions`
  - `test_sympy_never_sees_model_text_outside_a_safe_math_alphabet`
  - `test_the_asserted_conclusion_is_parsed_not_found_as_a_token`

## Modification guidance

- Change probes policy here when diagnosis owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/diagnosis/offline_review/probes.py](../../../../../../../src/learnloop/diagnosis/offline_review/probes.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

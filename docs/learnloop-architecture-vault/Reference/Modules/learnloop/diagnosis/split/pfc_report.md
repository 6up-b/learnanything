---
title: "learnloop.diagnosis.split.pfc_report"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/diagnosis/split/pfc_report.py"
source_paths:
  - "src/learnloop/diagnosis/split/pfc_report.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.diagnosis.split"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Process Model Output"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.diagnosis.split.pfc_report module"
  - "src/learnloop/diagnosis/split/pfc_report.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-diagnosis-split"
---

# `learnloop.diagnosis.split.pfc_report`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/diagnosis/split/_package|learnloop.diagnosis.split]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.diagnosis.split.pfc_report` exists within [[Reference/Modules/learnloop/diagnosis/split/_package|learnloop.diagnosis.split]] to own the behavior summarized by its module contract: PF-c before/after report (Slice 2 §5.5, §5.7: an E1-style report after S1.3).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/diagnosis/split/pfc_report.py](../../../../../../../src/learnloop/diagnosis/split/pfc_report.py) |
| Source lines | 437 |
| Owning package | [[Reference/Modules/learnloop/diagnosis/split/_package|learnloop.diagnosis.split]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `checkable_reference(item: Any) -> bool` ([source](../../../../../../../src/learnloop/diagnosis/split/pfc_report.py), line 78) — A bare parseable answer, or a worked solution with a numeric conclusion.
- `plan_pfc(vault: LoadedVault, repository: Repository, *, max_items: int=40, max_real: int=40, seed: int=0) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/diagnosis/split/pfc_report.py), line 87) — Seeded, LO-stratified reference-bearing items + owner-adjudicated answers.
- `estimate_pfc(vault: LoadedVault, repository: Repository, plan: Mapping[str, Any], spend: ReviewSpend) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/diagnosis/split/pfc_report.py), line 132)
- `run_pfc(vault: LoadedVault, repository: Repository, *, plan: Mapping[str, Any], generator_client: Any, grading_client: Any, caps: SpendCaps=DEFAULT_CAPS, price_per_million: float | None=None, cancelled: Callable[[], bool] | None=None, record_judgments: bool=True) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/diagnosis/split/pfc_report.py), line 234)
- `summarize_pfc(alt_rows: Sequence[Mapping[str, Any]], real_rows: Sequence[Mapping[str, Any]], *, statuses: Mapping[str, int], spend: Mapping[str, Any], plan: Mapping[str, Any], vault: LoadedVault) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/diagnosis/split/pfc_report.py), line 346)
- `render_pfc_markdown(report: Mapping[str, Any]) -> str` ([source](../../../../../../../src/learnloop/diagnosis/split/pfc_report.py), line 400)

### Module constants

- `PFC_REPORT_VERSION` ([src/learnloop/diagnosis/split/pfc_report.py](../../../../../../../src/learnloop/diagnosis/split/pfc_report.py), line 61)
- `ARMS` ([src/learnloop/diagnosis/split/pfc_report.py](../../../../../../../src/learnloop/diagnosis/split/pfc_report.py), line 62)
- `ARM_PROMPTS` ([src/learnloop/diagnosis/split/pfc_report.py](../../../../../../../src/learnloop/diagnosis/split/pfc_report.py), line 63)
- `DEFAULT_CAPS` ([src/learnloop/diagnosis/split/pfc_report.py](../../../../../../../src/learnloop/diagnosis/split/pfc_report.py), line 64)

### Explicit exports

`__all__` declares:

- `ARMS`
- `DEFAULT_CAPS`
- `PFC_REPORT_VERSION`
- `estimate_pfc`
- `plan_pfc`
- `render_pfc_markdown`
- `run_pfc`
- `summarize_pfc`

## Internal implementation anchors

- `_tokens(text: str) -> int` ([source](../../../../../../../src/learnloop/diagnosis/split/pfc_report.py), line 74)
- `_grade(vault: LoadedVault, client: Any, spend: ReviewSpend, *, item_id: str, attempt_id: str, answer: str, arm: str) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/diagnosis/split/pfc_report.py), line 178)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/diagnose|learnloop.cli.diagnose]] — imports `estimate_pfc`, `plan_pfc`, `render_pfc_markdown`, `run_pfc`; statically calls `estimate_pfc`, `plan_pfc`, `render_pfc_markdown`, `run_pfc`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/execution|learnloop.ai.execution]] — imports `content_key`; calls `content_key`
- [[Reference/Modules/learnloop/ai/spend|learnloop.ai.spend]] — imports `SpendCaps`; calls `SpendCaps`
- [[Reference/Modules/learnloop/attempts/answer_check|learnloop.attempts.answer_check]] — imports `parse_answer`, `reference_final_answer`; calls `parse_answer`, `reference_final_answer`
- [[Reference/Modules/learnloop/attempts/blind_grading|learnloop.attempts.blind_grading]] — imports `BLIND_GRADING_PROMPT_VERSION`, `blind_grading_context`, `blind_grading_prompt`, `validate_blind_grading_proposal`; calls `blind_grading_context`, `blind_grading_prompt`, `validate_blind_grading_proposal`
- [[Reference/Modules/learnloop/attempts/grading|learnloop.attempts.grading]] — imports `GradingValidationError`, `resolved_rubric`; calls `resolved_rubric`
- [[Reference/Modules/learnloop/attempts/grading_support|learnloop.attempts.grading_support]] — imports `REFERENCE_POLICY_PROMPT_VERSION`, `reference_policy`, `request_blind_grading_run`; calls `reference_policy`, `request_blind_grading_run`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/stores/judgments|learnloop.db.stores.judgments]] — imports `append_judgment`; calls `append_judgment`
- [[Reference/Modules/learnloop/diagnosis/diagnostic_augmentation|learnloop.diagnosis.diagnostic_augmentation]] — imports `diagnostic_verifier_observations`; calls `diagnostic_verifier_observations`
- [[Reference/Modules/learnloop/diagnosis/offline_review/probes|learnloop.diagnosis.offline_review.probes]] — imports `is_reference_bearing`, `request_valid_alternative`, `valid_alternative_prompt`, `verify_alternative`; calls `is_reference_bearing`, `request_valid_alternative`, `valid_alternative_prompt`, `verify_alternative`
- [[Reference/Modules/learnloop/diagnosis/offline_review/report|learnloop.diagnosis.offline_review.report]] — imports `wilson`; calls `wilson`
- [[Reference/Modules/learnloop/diagnosis/offline_review/spend|learnloop.diagnosis.offline_review.spend]] — imports `ReviewSpend`; calls `ReviewSpend`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `json`, `random`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/diagnose|learnloop.cli.diagnose]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_diagnosis_reports.py](../../../../../../../tests/test_diagnosis_reports.py) — direct import
  - `test_pfc_report_compares_before_and_after_and_records_verdicts`

## Modification guidance

- Change pfc report policy here when diagnosis owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/diagnosis/split/pfc_report.py](../../../../../../../src/learnloop/diagnosis/split/pfc_report.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

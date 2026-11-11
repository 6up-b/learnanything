---
title: "learnloop.diagnosis.split.diagnoser"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/diagnosis/split/diagnoser.py"
source_paths:
  - "src/learnloop/diagnosis/split/diagnoser.py"
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
  - "learnloop.diagnosis.split.diagnoser module"
  - "src/learnloop/diagnosis/split/diagnoser.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-diagnosis-split"
---

# `learnloop.diagnosis.split.diagnoser`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/diagnosis/split/_package|learnloop.diagnosis.split]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.diagnosis.split.diagnoser` exists within [[Reference/Modules/learnloop/diagnosis/split/_package|learnloop.diagnosis.split]] to own the behavior summarized by its module contract: One diagnosis: assemble the context, call the diagnoser, validate (§5).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/diagnosis/split/diagnoser.py](../../../../../../../src/learnloop/diagnosis/split/diagnoser.py) |
| Source lines | 250 |
| Owning package | [[Reference/Modules/learnloop/diagnosis/split/_package|learnloop.diagnosis.split]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class DiagnosisOutcome` ([source](../../../../../../../src/learnloop/diagnosis/split/diagnoser.py), line 48)
  - `unknown_id_count(self) -> int` (line 73; public)
- `supports_snapshot(client: Any) -> bool` ([source](../../../../../../../src/learnloop/diagnosis/split/diagnoser.py), line 77)
- `run_diagnosis(client: OperationClient, *, vault: LoadedVault, item: PracticeItem, rubric: Rubric, store: HistoryStore, current: CurrentAttempt, settings: DiagnosisSettings, mode: HistoryMode | None=None, retriever: HistoryRetriever | None=None, guard: CallGuard | None=None, snapshot_parent: Path | None=None, token_budget: int | None=None, registry_retriever: RegistryRetriever | None=None, prior_analysis: Any=None) -> DiagnosisOutcome` ([source](../../../../../../../src/learnloop/diagnosis/split/diagnoser.py), line 102) — Diagnose one blind-graded attempt in one history mode.

### Module constants

- `SKIPPED_NO_WORKSPACE` ([src/learnloop/diagnosis/split/diagnoser.py](../../../../../../../src/learnloop/diagnosis/split/diagnoser.py), line 44)

### Explicit exports

`__all__` declares:

- `CallGuard`
- `DiagnosisOutcome`
- `SKIPPED_NO_WORKSPACE`
- `run_diagnosis`
- `supports_snapshot`

## Internal implementation anchors

- `_call(client: OperationClient, assembled: AssembledContext, *, guard: CallGuard | None, workspace: Path | None) -> tuple[Any, int]` ([source](../../../../../../../src/learnloop/diagnosis/split/diagnoser.py), line 82)
- `_workspace_bytes(root: Path) -> int` ([source](../../../../../../../src/learnloop/diagnosis/split/diagnoser.py), line 98)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/ai_compare|learnloop.cli.ai_compare]] — imports `run_diagnosis`; statically calls `run_diagnosis`
- [[Reference/Modules/learnloop/diagnosis/offline_review/runner|learnloop.diagnosis.offline_review.runner]] — imports `DiagnosisOutcome`, `run_diagnosis`, `supports_snapshot`; statically calls `run_diagnosis`, `supports_snapshot`
- [[Reference/Modules/learnloop/diagnosis/split/jobs|learnloop.diagnosis.split.jobs]] — imports `DiagnosisOutcome`, `run_diagnosis`; statically calls `DiagnosisOutcome`, `run_diagnosis`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/errors|learnloop.ai.errors]] — imports `AIInterrupted`, `AIProviderUnavailable`
- [[Reference/Modules/learnloop/ai/spend|learnloop.ai.spend]] — imports `SpendLimitExceeded`
- [[Reference/Modules/learnloop/ai/transport|learnloop.ai.transport]] — imports `OperationClient`, `READ_ONLY_WORKSPACE`
- [[Reference/Modules/learnloop/diagnosis/split/context|learnloop.diagnosis.split.context]] — imports `AssembledContext`, `CurrentAttempt`, `HistoryRetriever`, `RegistryRetriever`, `assemble_diagnosis_context`; calls `assemble_diagnosis_context`
- [[Reference/Modules/learnloop/diagnosis/split/contract|learnloop.diagnosis.split.contract]] — imports `diagnosis_prompt`, `diagnosis_prompt_version`, `request_diagnosis_proposal`; calls `diagnosis_prompt`, `diagnosis_prompt_version`, `request_diagnosis_proposal`
- [[Reference/Modules/learnloop/diagnosis/split/history|learnloop.diagnosis.split.history]] — imports `HistoryStore`
- [[Reference/Modules/learnloop/diagnosis/split/provenance|learnloop.diagnosis.split.provenance]] — imports `frozen_record`, `served_entries`, `snapshot_reads`, `snapshot_record`; calls `frozen_record`, `served_entries`, `snapshot_reads`, `snapshot_record`
- [[Reference/Modules/learnloop/diagnosis/split/settings|learnloop.diagnosis.split.settings]] — imports `DIAGNOSIS_PROMPT_VERSION`, `DiagnosisSettings`, `HistoryMode`
- [[Reference/Modules/learnloop/diagnosis/split/snapshot|learnloop.diagnosis.split.snapshot]] — imports `snapshot_workspace`; calls `snapshot_workspace`
- [[Reference/Modules/learnloop/diagnosis/split/validation|learnloop.diagnosis.split.validation]] — imports `validate_diagnosis_proposal`; calls `validate_diagnosis_proposal`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`, `PracticeItem`, `Rubric`

### Platform and third-party dependencies

- Standard library: `__future__`, `contextlib`, `dataclasses`, `pathlib`, `time`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/ai_compare|learnloop.cli.ai_compare]], [[Reference/Modules/learnloop/diagnosis/offline_review/runner|learnloop.diagnosis.offline_review.runner]], [[Reference/Modules/learnloop/diagnosis/split/jobs|learnloop.diagnosis.split.jobs]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_chatgpt_plan_workspace.py](../../../../../../../tests/test_chatgpt_plan_workspace.py) — direct import
  - `test_a_snapshot_diagnosis_on_the_plan_records_exactly_what_it_read`
- [tests/test_diagnosis_history_modes.py](../../../../../../../tests/test_diagnosis_history_modes.py) — direct import
  - `test_every_mode_keeps_s3_and_validates_evidence_ids`
  - `test_snapshot_is_unavailable_without_the_capability`
  - `test_snapshot_workspace_is_deleted_on_success_and_on_failure`

## Modification guidance

- Change diagnoser policy here when diagnosis owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/diagnosis/split/diagnoser.py](../../../../../../../src/learnloop/diagnosis/split/diagnoser.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

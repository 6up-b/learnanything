---
title: "learnloop.diagnosis.split.contract"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/diagnosis/split/contract.py"
source_paths:
  - "src/learnloop/diagnosis/split/contract.py"
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
  - "learnloop.diagnosis.split.contract module"
  - "src/learnloop/diagnosis/split/contract.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-diagnosis-split"
---

# `learnloop.diagnosis.split.contract`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/diagnosis/split/_package|learnloop.diagnosis.split]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.diagnosis.split.contract` exists within [[Reference/Modules/learnloop/diagnosis/split/_package|learnloop.diagnosis.split]] to own the behavior summarized by its module contract: The ``DiagnosisProposal`` contract and the diagnoser prompt (Slice 1 §5.3).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/diagnosis/split/contract.py](../../../../../../../src/learnloop/diagnosis/split/contract.py) |
| Source lines | 350 |
| Owning package | [[Reference/Modules/learnloop/diagnosis/split/_package|learnloop.diagnosis.split]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class RegistryMatch(WireModel)` ([source](../../../../../../../src/learnloop/diagnosis/split/contract.py), line 44) — Replaces the ``misconception_match`` call (§5.3, §7.3).
- `class HistoryChangedCause(WireModel)` ([source](../../../../../../../src/learnloop/diagnosis/split/contract.py), line 58)
- `class EventDiagnosis(WireModel)` ([source](../../../../../../../src/learnloop/diagnosis/split/contract.py), line 66) — One per blind-grade error attribution, keyed by its index.
- `class DiagnosisRepairSuggestion(WireModel)` ([source](../../../../../../../src/learnloop/diagnosis/split/contract.py), line 93) — The instructional repair fields the grader no longer owns (§4.2).
  - `validate_eliciting(self) -> 'DiagnosisRepairSuggestion'` (line 115; public)
- `class Citation(WireModel)` ([source](../../../../../../../src/learnloop/diagnosis/split/contract.py), line 125)
- `class PatternClaim(WireModel)` ([source](../../../../../../../src/learnloop/diagnosis/split/contract.py), line 130) — A cross-attempt claim; shadow in S1 (§8).
- `class PrerequisiteGapHypothesis(WireModel)` ([source](../../../../../../../src/learnloop/diagnosis/split/contract.py), line 139)
- `class Abstention(WireModel)` ([source](../../../../../../../src/learnloop/diagnosis/split/contract.py), line 146)
- `class DiagnosisProposal(WireModel)` ([source](../../../../../../../src/learnloop/diagnosis/split/contract.py), line 151) — ``exact`` order: the analysis first.
- `class RecitingDiagnosisProposal(WireModel)` ([source](../../../../../../../src/learnloop/diagnosis/split/contract.py), line 163) — ``full`` / ``snapshot`` / ``hybrid`` order: recite the evidence first.
- `proposal_model_for(mode: str) -> type[DiagnosisProposal] | type[RecitingDiagnosisProposal]` ([source](../../../../../../../src/learnloop/diagnosis/split/contract.py), line 175)
- `as_diagnosis_proposal(value: DiagnosisProposal | RecitingDiagnosisProposal) -> DiagnosisProposal` ([source](../../../../../../../src/learnloop/diagnosis/split/contract.py), line 179)
- `diagnosis_task(mode: str) -> str` ([source](../../../../../../../src/learnloop/diagnosis/split/contract.py), line 261)
- `diagnosis_prompt_version(assembled: AssembledContext) -> str` ([source](../../../../../../../src/learnloop/diagnosis/split/contract.py), line 268) — The prompt version; ``+workbench-v1`` only when the current attempt carries a workbench step trace (RW2b, spec §5.4); then ``+prior-analysis-v1`` only in the prior-analysis arm's ``on`` arm (learner-blindness relax).
- `diagnosis_prompt(assembled: AssembledContext) -> str` ([source](../../../../../../../src/learnloop/diagnosis/split/contract.py), line 289) — The stable instructions first, then the cache-ordered context (§5.2).
- `request_diagnosis_proposal(client: OperationClient, assembled: AssembledContext, *, workspace: Path | None=None) -> DiagnosisProposal` ([source](../../../../../../../src/learnloop/diagnosis/split/contract.py), line 308) — Run the diagnoser.

### Module constants

- `CAUSAL_CLASSES` ([src/learnloop/diagnosis/split/contract.py](../../../../../../../src/learnloop/diagnosis/split/contract.py), line 37)
- `PATTERN_RELATIONS` ([src/learnloop/diagnosis/split/contract.py](../../../../../../../src/learnloop/diagnosis/split/contract.py), line 38)
- `CAUSE_REF_PREFIX` ([src/learnloop/diagnosis/split/contract.py](../../../../../../../src/learnloop/diagnosis/split/contract.py), line 41)
- `_TASK` ([src/learnloop/diagnosis/split/contract.py](../../../../../../../src/learnloop/diagnosis/split/contract.py), line 185)
- `_RECITE_FIRST` ([src/learnloop/diagnosis/split/contract.py](../../../../../../../src/learnloop/diagnosis/split/contract.py), line 244)
- `_ANALYSIS_FIRST` ([src/learnloop/diagnosis/split/contract.py](../../../../../../../src/learnloop/diagnosis/split/contract.py), line 249)
- `_SNAPSHOT_RULES` ([src/learnloop/diagnosis/split/contract.py](../../../../../../../src/learnloop/diagnosis/split/contract.py), line 250)

### Explicit exports

`__all__` declares:

- `CAUSAL_CLASSES`
- `CAUSE_REF_PREFIX`
- `PATTERN_RELATIONS`
- `Abstention`
- `Citation`
- `DiagnosisProposal`
- `DiagnosisRepairSuggestion`
- `EventDiagnosis`
- `HistoryChangedCause`
- `PatternClaim`
- `PrerequisiteGapHypothesis`
- `RecitingDiagnosisProposal`
- `RegistryMatch`
- `as_diagnosis_proposal`
- `diagnosis_prompt`
- `diagnosis_task`
- `proposal_model_for`
- `request_diagnosis_proposal`

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/ai_compare|learnloop.cli.ai_compare]] — imports `diagnosis_prompt`; statically calls `diagnosis_prompt`
- [[Reference/Modules/learnloop/diagnosis/offline_review/runner|learnloop.diagnosis.offline_review.runner]] — imports `diagnosis_prompt`; statically calls `diagnosis_prompt`
- [[Reference/Modules/learnloop/diagnosis/split/diagnoser|learnloop.diagnosis.split.diagnoser]] — imports `diagnosis_prompt`, `diagnosis_prompt_version`, `request_diagnosis_proposal`; statically calls `diagnosis_prompt`, `diagnosis_prompt_version`, `request_diagnosis_proposal`
- [[Reference/Modules/learnloop/diagnosis/split/jobs|learnloop.diagnosis.split.jobs]] — imports `diagnosis_prompt`; statically calls `diagnosis_prompt`
- [[Reference/Modules/learnloop/diagnosis/split/validation|learnloop.diagnosis.split.validation]] — imports `CAUSE_REF_PREFIX`, `DiagnosisProposal`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/schemas|learnloop.ai.schemas]] — imports `AttributionTargetRef`, `CandidateCause`, `WireModel`
- [[Reference/Modules/learnloop/ai/transport|learnloop.ai.transport]] — imports `OperationClient`, `execute_structured_operation`; calls `execute_structured_operation`
- [[Reference/Modules/learnloop/attempts/ai_contracts|learnloop.attempts.ai_contracts]] — imports `ELICITING_REVEAL_BUDGET_DEFAULT`, `PostdictiveClaim`, `RepairVerificationRequest`
- [[Reference/Modules/learnloop/diagnosis/split/context|learnloop.diagnosis.split.context]] — imports `AssembledContext`
- [[Reference/Modules/learnloop/diagnosis/split/figure_trace|learnloop.diagnosis.split.figure_trace]] — imports `SUFFIX`
- [[Reference/Modules/learnloop/diagnosis/split/prior_analysis|learnloop.diagnosis.split.prior_analysis]] — imports `ARM_ON`, `SUFFIX`
- [[Reference/Modules/learnloop/diagnosis/split/settings|learnloop.diagnosis.split.settings]] — imports `DIAGNOSIS_PROMPT_VERSION`
- [[Reference/Modules/learnloop/diagnosis/split/workbench_trace|learnloop.diagnosis.split.workbench_trace]] — imports `SUFFIX`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `json`, `pathlib`, `typing`
- Third party: `pydantic`

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/ai_compare|learnloop.cli.ai_compare]], [[Reference/Modules/learnloop/diagnosis/offline_review/runner|learnloop.diagnosis.offline_review.runner]], [[Reference/Modules/learnloop/diagnosis/split/diagnoser|learnloop.diagnosis.split.diagnoser]], [[Reference/Modules/learnloop/diagnosis/split/jobs|learnloop.diagnosis.split.jobs]], [[Reference/Modules/learnloop/diagnosis/split/validation|learnloop.diagnosis.split.validation]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/split_live_helpers.py](../../../../../../../tests/split_live_helpers.py) — direct import
- [tests/test_codex_lockdown_round3.py](../../../../../../../tests/test_codex_lockdown_round3.py) — direct import
  - `test_a_snapshot_diagnosis_on_codex_is_inlined_and_gives_the_same_structured_output`
- [tests/test_diagnosis_contract.py](../../../../../../../tests/test_diagnosis_contract.py) — direct import
  - `test_generation_order_differs_by_mode_and_normalizes`
  - `test_prompt_rules_by_mode`
- [tests/test_diagnosis_embeddings.py](../../../../../../../tests/test_diagnosis_embeddings.py) — direct import
  - `test_the_diagnoser_may_match_a_shortlisted_belief_from_outside_the_neighborhood`
- [tests/test_diagnosis_pipeline.py](../../../../../../../tests/test_diagnosis_pipeline.py) — direct import
- [tests/test_figures_help.py](../../../../../../../tests/test_figures_help.py) — direct import
  - `test_the_context_hashes_as_before_without_a_figure_trace`
- [tests/test_learner_blindness_relax.py](../../../../../../../tests/test_learner_blindness_relax.py) — direct import
  - `test_the_off_arm_is_todays_context_and_the_on_arm_refeeds_earlier_analyses`
- [tests/test_pfc_unassessed_readers.py](../../../../../../../tests/test_pfc_unassessed_readers.py) — direct import
  - `test_a_later_diagnosis_cannot_cite_an_unassessed_shortfall_as_a_recurrence`
- [tests/test_recurrence_live.py](../../../../../../../tests/test_recurrence_live.py) — direct import
- [tests/test_workbench_trace.py](../../../../../../../tests/test_workbench_trace.py) — direct import
  - `test_a_workbench_attempt_carries_its_trace_under_the_suffix_and_never_a_map`
  - `test_every_other_attempt_renders_exactly_as_before`

## Modification guidance

- Change contract policy here when diagnosis owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/diagnosis/split/contract.py](../../../../../../../src/learnloop/diagnosis/split/contract.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

---
title: "learnloop.ai.schemas"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/ai/schemas.py"
source_paths:
  - "src/learnloop/ai/schemas.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.ai"
layer: "infrastructure"
concepts:
  - "AI Architecture"
  - "Architecture Overview"
workflows:
  - "Configure AI Providers"
  - "Process Model Output"
aliases:
  - "learnloop.ai.schemas module"
  - "src/learnloop/ai/schemas.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-ai"
---

# `learnloop.ai.schemas`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/ai/_package|learnloop.ai]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

This module keeps schemas behavior inside its owning package, [[Reference/Modules/learnloop/ai/_package|learnloop.ai]]. Its public surface centers on `WireModel`, `UndeclaredWireFieldError`, `undeclared_wire_fields`, `describe_wire_validation_error`, `FacetCapabilityTargetRef`, `CriterionTargetRef`, `ItemStepTargetRef`, `AnswerSpanTargetRef` and 2 more public symbols.

The authoritative system-level explanation remains in [[AI Architecture]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/ai/schemas.py](../../../../../../src/learnloop/ai/schemas.py) |
| Source lines | 209 |
| Owning package | [[Reference/Modules/learnloop/ai/_package|learnloop.ai]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |

## Public API

- `class WireModel(BaseModel)` ([source](../../../../../../src/learnloop/ai/schemas.py), line 38) — Base for every payload that crosses the provider boundary.
- `class UndeclaredWireFieldError(ValueError)` ([source](../../../../../../src/learnloop/ai/schemas.py), line 61) — A payload carried a field the wire contract does not declare.
  - `__init__(self, model: type[BaseModel], fields: list[str]) -> None` (line 70; internal)
- `undeclared_wire_fields(exc: ValidationError) -> list[str]` ([source](../../../../../../src/learnloop/ai/schemas.py), line 81) — Dotted paths of every ``extra="forbid"`` rejection inside ``exc``.
- `describe_wire_validation_error(model: type[BaseModel], exc: BaseException) -> str` ([source](../../../../../../src/learnloop/ai/schemas.py), line 99) — One actionable line for a failed wire parse, naming model and fields.
- `class FacetCapabilityTargetRef(WireModel)` ([source](../../../../../../src/learnloop/ai/schemas.py), line 108)
- `class CriterionTargetRef(WireModel)` ([source](../../../../../../src/learnloop/ai/schemas.py), line 114)
- `class ItemStepTargetRef(WireModel)` ([source](../../../../../../src/learnloop/ai/schemas.py), line 119)
- `class AnswerSpanTargetRef(WireModel)` ([source](../../../../../../src/learnloop/ai/schemas.py), line 125)
  - `validate_offsets(self) -> 'AnswerSpanTargetRef'` (line 132; public)
- `class NoTargetRef(WireModel)` ([source](../../../../../../src/learnloop/ai/schemas.py), line 144)
- `class CandidateCause(WireModel)` ([source](../../../../../../src/learnloop/ai/schemas.py), line 156) — One free-text candidate explanation of an observed failure.
  - `validate_statement(self) -> 'CandidateCause'` (line 206; public)

### Module constants

- `EXTRA_FORBIDDEN_ERROR_TYPE` ([src/learnloop/ai/schemas.py](../../../../../../src/learnloop/ai/schemas.py), line 58)

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/adaptive_difficulty/feature_audit|learnloop.adaptive_difficulty.feature_audit]] — imports `WireModel`
- [[Reference/Modules/learnloop/adaptive_difficulty/history_forecast|learnloop.adaptive_difficulty.history_forecast]] — imports `WireModel`
- [[Reference/Modules/learnloop/adaptive_difficulty/outside|learnloop.adaptive_difficulty.outside]] — imports `WireModel`
- [[Reference/Modules/learnloop/adaptive_difficulty/relatedness|learnloop.adaptive_difficulty.relatedness]] — imports `WireModel`
- [[Reference/Modules/learnloop/ai/providers/codex|learnloop.ai.providers.codex]] — imports `describe_wire_validation_error`; statically calls `describe_wire_validation_error`
- [[Reference/Modules/learnloop/ai/providers/codex_http|learnloop.ai.providers.codex_http]] — imports `describe_wire_validation_error`; statically calls `describe_wire_validation_error`
- [[Reference/Modules/learnloop/ai/strict_schema|learnloop.ai.strict_schema]] — imports `WireModel`
- [[Reference/Modules/learnloop/ai/tool_requests|learnloop.ai.tool_requests]] — imports `WireModel`
- [[Reference/Modules/learnloop/ai/transport|learnloop.ai.transport]] — imports `WireModel`
- [[Reference/Modules/learnloop/attempts/ai_contracts|learnloop.attempts.ai_contracts]] — imports `AttributionTargetRef`, `CandidateCause`, `WireModel`
- [[Reference/Modules/learnloop/attempts/blind_grading|learnloop.attempts.blind_grading]] — imports `AttributionTargetRef`, `WireModel`
- [[Reference/Modules/learnloop/attempts/grading_support|learnloop.attempts.grading_support]] — imports `WireModel`
- [[Reference/Modules/learnloop/attempts/stuck|learnloop.attempts.stuck]] — imports `WireModel`
- [[Reference/Modules/learnloop/cli/ai|learnloop.cli.ai]] — imports `WireModel`
- [[Reference/Modules/learnloop/cli/field_classification|learnloop.cli.field_classification]] — imports `WireModel`
- [[Reference/Modules/learnloop/content/authoring/ai_contracts|learnloop.content.authoring.ai_contracts]] — imports `WireModel`
- [[Reference/Modules/learnloop/content/authoring/pf_contracts|learnloop.content.authoring.pf_contracts]] — imports `WireModel`
- [[Reference/Modules/learnloop/content/authoring/source_exercise_import|learnloop.content.authoring.source_exercise_import]] — imports `WireModel`
- [[Reference/Modules/learnloop/content/facet_identity/judge|learnloop.content.facet_identity.judge]] — imports `WireModel`
- [[Reference/Modules/learnloop/content/proposals/ai_contracts|learnloop.content.proposals.ai_contracts]] — imports `WireModel`, `describe_wire_validation_error`; statically calls `describe_wire_validation_error`
- [[Reference/Modules/learnloop/content/proposals/method_phrasing|learnloop.content.proposals.method_phrasing]] — imports `WireModel`
- [[Reference/Modules/learnloop/content/proposals/method_statement_judge|learnloop.content.proposals.method_statement_judge]] — imports `WireModel`
- [[Reference/Modules/learnloop/content/synthesis/ai_contracts|learnloop.content.synthesis.ai_contracts]] — imports `WireModel`
- [[Reference/Modules/learnloop/curriculum/ai_contracts|learnloop.curriculum.ai_contracts]] — imports `WireModel`
- [[Reference/Modules/learnloop/daily_plan/router_teach_back|learnloop.daily_plan.router_teach_back]] — imports `WireModel`
- [[Reference/Modules/learnloop/diagnosis/ai_contracts|learnloop.diagnosis.ai_contracts]] — imports `WireModel`
- [[Reference/Modules/learnloop/diagnosis/diagnostic_augmentation|learnloop.diagnosis.diagnostic_augmentation]] — imports `CandidateCause`; statically calls `CandidateCause`
- [[Reference/Modules/learnloop/diagnosis/offline_review/judge|learnloop.diagnosis.offline_review.judge]] — imports `WireModel`
- [[Reference/Modules/learnloop/diagnosis/offline_review/planted|learnloop.diagnosis.offline_review.planted]] — imports `WireModel`
- [[Reference/Modules/learnloop/diagnosis/offline_review/probes|learnloop.diagnosis.offline_review.probes]] — imports `WireModel`
- [[Reference/Modules/learnloop/diagnosis/recurrence/benchmarks|learnloop.diagnosis.recurrence.benchmarks]] — imports `WireModel`
- [[Reference/Modules/learnloop/diagnosis/recurrence/escalation|learnloop.diagnosis.recurrence.escalation]] — imports `WireModel`
- [[Reference/Modules/learnloop/diagnosis/split/contract|learnloop.diagnosis.split.contract]] — imports `AttributionTargetRef`, `CandidateCause`, `WireModel`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/contract|learnloop.diagnosis.text_gaps.contract]] — imports `WireModel`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/answers|learnloop.experiments.contextual_embeddings.answers]] — imports `WireModel`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/bank|learnloop.experiments.contextual_embeddings.bank]] — imports `WireModel`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/supplement|learnloop.experiments.contextual_embeddings.e1.supplement]] — imports `WireModel`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/retrieval|learnloop.experiments.contextual_embeddings.retrieval]] — imports `WireModel`
- [[Reference/Modules/learnloop/field/probability_prep|learnloop.field.probability_prep]] — imports `WireModel`
- [[Reference/Modules/learnloop/figures/prefetch|learnloop.figures.prefetch]] — imports `WireModel`
- [[Reference/Modules/learnloop/figures/routes|learnloop.figures.routes]] — imports `WireModel`
- [[Reference/Modules/learnloop/hints/maps|learnloop.hints.maps]] — imports `WireModel`
- [[Reference/Modules/learnloop/hints/outcome|learnloop.hints.outcome]] — imports `WireModel`
- [[Reference/Modules/learnloop/hints/workbench|learnloop.hints.workbench]] — imports `WireModel`
- [[Reference/Modules/learnloop/hints/writer|learnloop.hints.writer]] — imports `WireModel`
- [[Reference/Modules/learnloop/instructional/exposure|learnloop.instructional.exposure]] — imports `WireModel`
- [[Reference/Modules/learnloop/instructional/reader_digest|learnloop.instructional.reader_digest]] — imports `WireModel`
- [[Reference/Modules/learnloop/instructional/screen|learnloop.instructional.screen]] — imports `WireModel`
- [[Reference/Modules/learnloop/matching/judge|learnloop.matching.judge]] — imports `WireModel`
- [[Reference/Modules/learnloop/ops/contamination/judge|learnloop.ops.contamination.judge]] — imports `WireModel`
- [[Reference/Modules/learnloop/ops/family_proposals|learnloop.ops.family_proposals]] — imports `WireModel`
- [[Reference/Modules/learnloop/practice_index/contracts|learnloop.practice_index.contracts]] — imports `WireModel`
- [[Reference/Modules/learnloop/projects/ai_contracts|learnloop.projects.ai_contracts]] — imports `WireModel`
- [[Reference/Modules/learnloop/reader/ai_contracts|learnloop.reader.ai_contracts]] — imports `WireModel`
- [[Reference/Modules/learnloop/reader/source_roles|learnloop.reader.source_roles]] — imports `WireModel`
- [[Reference/Modules/learnloop/router/requests|learnloop.router.requests]] — imports `WireModel`
- [[Reference/Modules/learnloop/source_retrieval/compare|learnloop.source_retrieval.compare]] — imports `WireModel`
- [[Reference/Modules/learnloop/source_retrieval/contracts|learnloop.source_retrieval.contracts]] — imports `WireModel`
- [[Reference/Modules/learnloop/source_retrieval/deliverable_path|learnloop.source_retrieval.deliverable_path]] — imports `WireModel`
- [[Reference/Modules/learnloop/source_retrieval/deliverables|learnloop.source_retrieval.deliverables]] — imports `WireModel`
- [[Reference/Modules/learnloop/source_retrieval/find_sources|learnloop.source_retrieval.find_sources]] — imports `WireModel`
- [[Reference/Modules/learnloop/source_retrieval/library_ask|learnloop.source_retrieval.library_ask]] — imports `WireModel`
- [[Reference/Modules/learnloop/source_retrieval/note_links|learnloop.source_retrieval.note_links]] — imports `WireModel`
- [[Reference/Modules/learnloop/source_retrieval/passage_cues|learnloop.source_retrieval.passage_cues]] — imports `WireModel`
- [[Reference/Modules/learnloop/source_retrieval/reading_paths|learnloop.source_retrieval.reading_paths]] — imports `WireModel`
- [[Reference/Modules/learnloop/source_retrieval/role_labeller|learnloop.source_retrieval.role_labeller]] — imports `WireModel`
- [[Reference/Modules/learnloop/source_retrieval/section_coverage|learnloop.source_retrieval.section_coverage]] — imports `WireModel`
- [[Reference/Modules/learnloop/source_retrieval/student_data|learnloop.source_retrieval.student_data]] — imports `WireModel`
- [[Reference/Modules/learnloop/teacher/contracts|learnloop.teacher.contracts]] — imports `WireModel`
- [[Reference/Modules/learnloop/tutor/ai_contracts|learnloop.tutor.ai_contracts]] — imports `CandidateCause`, `WireModel`
- [[Reference/Modules/learnloop/workbench/check|learnloop.workbench.check]] — imports `WireModel`
- [[Reference/Modules/learnloop/workbench/compare_methods|learnloop.workbench.compare_methods]] — imports `WireModel`

### Repository tooling consumers

- [scripts/benchmark_chatgpt_plan_latency.py](../../../../../../scripts/benchmark_chatgpt_plan_latency.py)

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `typing`
- Third party: `pydantic`

## Larger workflow participation

Use this module in context through:

- [[Configure AI Providers]]
- [[Process Model Output]]

Static participation evidence comes from [[Reference/Modules/learnloop/adaptive_difficulty/feature_audit|learnloop.adaptive_difficulty.feature_audit]], [[Reference/Modules/learnloop/adaptive_difficulty/history_forecast|learnloop.adaptive_difficulty.history_forecast]], [[Reference/Modules/learnloop/adaptive_difficulty/outside|learnloop.adaptive_difficulty.outside]], [[Reference/Modules/learnloop/adaptive_difficulty/relatedness|learnloop.adaptive_difficulty.relatedness]], [[Reference/Modules/learnloop/ai/providers/codex|learnloop.ai.providers.codex]] and 67 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/recurrence_fakes.py](../../../../../../tests/recurrence_fakes.py) — direct import
- [tests/test_ai_single_request.py](../../../../../../tests/test_ai_single_request.py) — direct import
- [tests/test_chat_total_transport_deadline.py](../../../../../../tests/test_chat_total_transport_deadline.py) — direct import
- [tests/test_chatgpt_plan_provider.py](../../../../../../tests/test_chatgpt_plan_provider.py) — direct import
- [tests/test_chatgpt_plan_workspace.py](../../../../../../tests/test_chatgpt_plan_workspace.py) — direct import
- [tests/test_codex_output_schema.py](../../../../../../tests/test_codex_output_schema.py) — direct import
  - `test_runtime_validation_and_strict_schema_agree_on_what_is_admissible`
  - `test_undeclared_wire_field_is_rejected_by_name`
- [tests/test_ingestion_checkpoints.py](../../../../../../tests/test_ingestion_checkpoints.py) — direct import
- [tests/test_model_call_receipt_owners.py](../../../../../../tests/test_model_call_receipt_owners.py) — direct import
  - `test_a_database_below_the_receipt_schema_lets_the_model_call_run_unrecorded`
- [tests/test_model_usage_report.py](../../../../../../tests/test_model_usage_report.py) — direct import
- [tests/test_output_budget.py](../../../../../../tests/test_output_budget.py) — direct import
  - `test_codex_turns_take_the_routes_effort_for_that_turn_only`
- [tests/test_plan_first_transport.py](../../../../../../tests/test_plan_first_transport.py) — direct import
- [tests/test_recurrence_live.py](../../../../../../tests/test_recurrence_live.py) — direct import
- [tests/test_structured_transport_parity.py](../../../../../../tests/test_structured_transport_parity.py) — direct import
- [tests/test_teacher_te2log_episodes.py](../../../../../../tests/test_teacher_te2log_episodes.py) — direct import
  - `test_a_schema_refusal_names_fields_by_location_never_by_their_input`

## Modification guidance

- Change provider-neutral transport/routing policy here; do not move feature prompts or feature result models into the shared AI layer.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/ai/schemas.py](../../../../../../src/learnloop/ai/schemas.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

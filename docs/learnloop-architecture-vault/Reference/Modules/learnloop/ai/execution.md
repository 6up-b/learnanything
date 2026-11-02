---
title: "learnloop.ai.execution"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/ai/execution.py"
source_paths:
  - "src/learnloop/ai/execution.py"
source_commit: "2d11fc7113d296b712971538e8684e070ca2664d"
source_commit_timestamp: "2026-11-01T21:42:01-05:00"
source_worktree_state: "clean"
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
  - "learnloop.ai.execution module"
  - "src/learnloop/ai/execution.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-ai"
---

# `learnloop.ai.execution`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/ai/_package|learnloop.ai]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.ai.execution` exists within [[Reference/Modules/learnloop/ai/_package|learnloop.ai]] to own the behavior summarized by its module contract: Request-scoped limits and durable call observations, without storage coupling.

The authoritative system-level explanation remains in [[AI Architecture]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/ai/execution.py](../../../../../../src/learnloop/ai/execution.py) |
| Source lines | 434 |
| Owning package | [[Reference/Modules/learnloop/ai/_package|learnloop.ai]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `2d11fc7113d296b712971538e8684e070ca2664d` |
| Commit timestamp | `2026-11-01T21:42:01-05:00` |

## Public API

- `withhold_receipt_input()` ([source](../../../../../../src/learnloop/ai/execution.py), line 45) — Calls started in this context keep no prompt text on their receipts.
- `call_labels(**labels: str | None)` ([source](../../../../../../src/learnloop/ai/execution.py), line 64) — Label every model call started in this context on its receipt.
- `single_request()` ([source](../../../../../../src/learnloop/ai/execution.py), line 86) — Disable hidden paid retries/repairs for a caller-budgeted transport call.
- `single_request_active() -> bool` ([source](../../../../../../src/learnloop/ai/execution.py), line 102)
- `annotate_calls(**notes: Any)` ([source](../../../../../../src/learnloop/ai/execution.py), line 107) — Add ``notes`` to the ``budget_json`` of every root receipt started here.
- `requested_reasoning_effort(effort: str | None)` ([source](../../../../../../src/learnloop/ai/execution.py), line 123) — Ask every request started here for ``effort`` (None keeps the profile's).
- `reasoning_effort_request() -> str | None` ([source](../../../../../../src/learnloop/ai/execution.py), line 138)
- `truncation_retry_allowed()` ([source](../../../../../../src/learnloop/ai/execution.py), line 143) — Let the transport retry a truncated answer once at double the budget.
- `truncation_retry_permitted() -> bool` ([source](../../../../../../src/learnloop/ai/execution.py), line 160)
- `report_call_usage(values: dict[str, Any]) -> None` ([source](../../../../../../src/learnloop/ai/execution.py), line 164)
- `content_key(payload: Any) -> str` ([source](../../../../../../src/learnloop/ai/execution.py), line 174)
- `model_settings(client: Any) -> dict[str, Any]` ([source](../../../../../../src/learnloop/ai/execution.py), line 178) — The client settings that change what a request produces.
- `observe_model_calls(observer: Callable[[str, dict[str, Any]], Any])` ([source](../../../../../../src/learnloop/ai/execution.py), line 199)
- `tee_model_calls(observer: Callable[[str, dict[str, Any]], Any])` ([source](../../../../../../src/learnloop/ai/execution.py), line 208) — Also observe model calls with ``observer``, keeping the context's own observer.
- `class RequestGate(Protocol)` ([source](../../../../../../src/learnloop/ai/execution.py), line 233) — Admission for each physical model request made in a context.
  - `admit(self, client: Any, *, purpose: str, prompt: Any, budget: int | None) -> Any` (line 245; public)
  - `settle(self, admission: Any, usage: dict[str, Any]) -> None` (line 248; public)
- `gate_model_requests(gate: RequestGate)` ([source](../../../../../../src/learnloop/ai/execution.py), line 253) — Admit every physical model request started in this context through ``gate``.
- `active_request_gate() -> RequestGate | None` ([source](../../../../../../src/learnloop/ai/execution.py), line 263) — The request gate installed in this context, if any: a caller adding a check of its own composes with it instead of replacing it.
- `class ModelEventStore(Protocol)` ([source](../../../../../../src/learnloop/ai/execution.py), line 270)
  - `record_model_event(self, action: str, event: dict[str, Any], *, owner_kind: str, owner_id: str) -> None` (line 271; public)
- `record_model_calls(store: ModelEventStore, *, owner_kind: str, owner_id: str)` ([source](../../../../../../src/learnloop/ai/execution.py), line 275) — Observe every model call in this context into ``store`` under one owner.
- `declared_budgets(budgets: dict[str, Any])` ([source](../../../../../../src/learnloop/ai/execution.py), line 288) — Record the token budgets an operation runs under on its root receipts.
- `generation_limit(output_tokens: int | None)` ([source](../../../../../../src/learnloop/ai/execution.py), line 303)
- `output_limit() -> int | None` ([source](../../../../../../src/learnloop/ai/execution.py), line 315)
- `observed_sdk_turn(function)` ([source](../../../../../../src/learnloop/ai/execution.py), line 319)
- `model_call(client: Any, *, purpose: str, prompt: Any=None, schema: Any=None, budget: int | None=None, wrapper: bool=False)` ([source](../../../../../../src/learnloop/ai/execution.py), line 330) — One model call: a receipt for the observer and, unless ``wrapper`` (an operation around the physical requests a provider makes), admission through the context's request gate before anything is sent.

### Module constants

- `CALL_LABELS` ([src/learnloop/ai/execution.py](../../../../../../src/learnloop/ai/execution.py), line 40)
- `JUDGE_LABELS` ([src/learnloop/ai/execution.py](../../../../../../src/learnloop/ai/execution.py), line 41)

## Internal implementation anchors

- `_observed_call(client: Any, *, purpose: str, prompt: Any, schema: Any, budget: int | None, collect_usage: bool=False)` ([source](../../../../../../src/learnloop/ai/execution.py), line 364)
- `_failure_status(exc: BaseException) -> str` ([source](../../../../../../src/learnloop/ai/execution.py), line 415)
- `_record_finish(observer: Callable[[str, dict[str, Any]], Any], call_id: str, metadata: dict[str, Any]) -> None` ([source](../../../../../../src/learnloop/ai/execution.py), line 423) — Best-effort: the durable start is the safety guarantee, the finish is telemetry.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/adaptive_difficulty/feature_audit|learnloop.adaptive_difficulty.feature_audit]] — imports `content_key`; statically calls `content_key`
- [[Reference/Modules/learnloop/adaptive_difficulty/outside|learnloop.adaptive_difficulty.outside]] — imports `content_key`; statically calls `content_key`
- [[Reference/Modules/learnloop/adaptive_difficulty/sending|learnloop.adaptive_difficulty.sending]] — imports `active_request_gate`, `gate_model_requests`; statically calls `active_request_gate`, `gate_model_requests`
- [[Reference/Modules/learnloop/ai/output_budget|learnloop.ai.output_budget]] — imports `annotate_calls`; statically calls `annotate_calls`
- [[Reference/Modules/learnloop/ai/providers/chatgpt_plan|learnloop.ai.providers.chatgpt_plan]] — imports `model_call`, `report_call_usage`, `single_request_active`; statically calls `model_call`, `report_call_usage`, `single_request_active`
- [[Reference/Modules/learnloop/ai/providers/codex|learnloop.ai.providers.codex]] — imports `generation_limit`, `observed_sdk_turn`, `output_limit`, `report_call_usage`, `single_request_active`; statically calls `generation_limit`, `output_limit`, `report_call_usage`, `single_request_active`
- [[Reference/Modules/learnloop/ai/providers/codex_http|learnloop.ai.providers.codex_http]] — imports `report_call_usage`; statically calls `report_call_usage`
- [[Reference/Modules/learnloop/ai/providers/decider|learnloop.ai.providers.decider]] — imports `model_call`, `report_call_usage`; statically calls `model_call`, `report_call_usage`
- [[Reference/Modules/learnloop/ai/providers/openai_chat|learnloop.ai.providers.openai_chat]] — imports `model_call`, `report_call_usage`, `single_request_active`, `truncation_retry_permitted`; statically calls `model_call`, `report_call_usage`, `single_request_active`, `truncation_retry_permitted`
- [[Reference/Modules/learnloop/ai/providers/openai_embedding|learnloop.ai.providers.openai_embedding]] — imports `model_call`, `report_call_usage`; statically calls `model_call`, `report_call_usage`
- [[Reference/Modules/learnloop/ai/providers/voyage_contextual|learnloop.ai.providers.voyage_contextual]] — imports `model_call`, `report_call_usage`; statically calls `model_call`, `report_call_usage`
- [[Reference/Modules/learnloop/ai/review_spend|learnloop.ai.review_spend]] — imports `generation_limit`, `observe_model_calls`, `truncation_retry_allowed`; statically calls `generation_limit`, `observe_model_calls`, `truncation_retry_allowed`
- [[Reference/Modules/learnloop/ai/spend|learnloop.ai.spend]] — imports `declared_budgets`; statically calls `declared_budgets`
- [[Reference/Modules/learnloop/ai/transport|learnloop.ai.transport]] — imports `model_call`, `output_limit`, `reasoning_effort_request`; statically calls `model_call`, `output_limit`, `reasoning_effort_request`
- [[Reference/Modules/learnloop/cli/ai|learnloop.cli.ai]] — imports `generation_limit`, `single_request`; statically calls `generation_limit`, `single_request`
- [[Reference/Modules/learnloop/cli/ai_compare|learnloop.cli.ai_compare]] — imports `annotate_calls`, `content_key`, `generation_limit`, `tee_model_calls`; statically calls `annotate_calls`, `content_key`, `generation_limit`, `tee_model_calls`
- [[Reference/Modules/learnloop/cli/field_classification|learnloop.cli.field_classification]] — imports `generation_limit`; statically calls `generation_limit`
- [[Reference/Modules/learnloop/cli/probability_arms|learnloop.cli.probability_arms]] — imports `call_labels`, `observe_model_calls`; statically calls `call_labels`, `observe_model_calls`
- [[Reference/Modules/learnloop/cli/receipts|learnloop.cli.receipts]] — imports `observe_model_calls`; statically calls `observe_model_calls`
- [[Reference/Modules/learnloop/content/authoring/source_exercise_import|learnloop.content.authoring.source_exercise_import]] — imports `content_key`, `generation_limit`, `observe_model_calls`, `record_model_calls`, `requested_reasoning_effort`, `single_request`; statically calls `content_key`, `generation_limit`, `observe_model_calls`, `record_model_calls`, `requested_reasoning_effort`, `single_request`
- [[Reference/Modules/learnloop/content/facet_identity/actions|learnloop.content.facet_identity.actions]] — imports `content_key`; statically calls `content_key`
- [[Reference/Modules/learnloop/content/facet_identity/judge|learnloop.content.facet_identity.judge]] — imports `call_labels`, `content_key`, `generation_limit`, `model_settings`, `observe_model_calls`, `requested_reasoning_effort`, `single_request`; statically calls `call_labels`, `content_key`, `generation_limit`, `model_settings`, `observe_model_calls`, `requested_reasoning_effort`, `single_request`
- [[Reference/Modules/learnloop/content/facet_identity/plan|learnloop.content.facet_identity.plan]] — imports `content_key`; statically calls `content_key`
- [[Reference/Modules/learnloop/content/facet_identity/span_support|learnloop.content.facet_identity.span_support]] — imports `content_key`; statically calls `content_key`
- [[Reference/Modules/learnloop/content/pipeline/add_source|learnloop.content.pipeline.add_source]] — imports `content_key`, `gate_model_requests`; statically calls `content_key`, `gate_model_requests`
- [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]] — imports `observe_model_calls`; statically calls `observe_model_calls`
- [[Reference/Modules/learnloop/content/pipeline/runner|learnloop.content.pipeline.runner]] — imports `record_model_calls`; statically calls `record_model_calls`
- [[Reference/Modules/learnloop/content/pipeline/source_ingestion|learnloop.content.pipeline.source_ingestion]] — imports `content_key`; statically calls `content_key`
- [[Reference/Modules/learnloop/content/proposals/method_statement_judge|learnloop.content.proposals.method_statement_judge]] — imports `content_key`; statically calls `content_key`
- [[Reference/Modules/learnloop/content/synthesis/graph_nomination|learnloop.content.synthesis.graph_nomination]] — imports `observe_model_calls`; statically calls `observe_model_calls`
- [[Reference/Modules/learnloop/content/synthesis/source_set_synthesis|learnloop.content.synthesis.source_set_synthesis]] — imports `content_key`, `declared_budgets`, `generation_limit`, `model_settings`; statically calls `content_key`, `declared_budgets`, `generation_limit`, `model_settings`
- [[Reference/Modules/learnloop/content/synthesis/source_unit_inventory|learnloop.content.synthesis.source_unit_inventory]] — imports `content_key`, `generation_limit`, `model_settings`; statically calls `content_key`, `generation_limit`, `model_settings`
- [[Reference/Modules/learnloop/curriculum/subject_registry|learnloop.curriculum.subject_registry]] — imports `content_key`; statically calls `content_key`
- [[Reference/Modules/learnloop/daily_plan/router_runtime|learnloop.daily_plan.router_runtime]] — imports `call_labels`, `gate_model_requests`, `generation_limit`, `observe_model_calls`, `requested_reasoning_effort`; statically calls `call_labels`, `gate_model_requests`, `generation_limit`, `observe_model_calls`, `requested_reasoning_effort`
- [[Reference/Modules/learnloop/decider_judgments|learnloop.decider_judgments]] — imports `call_labels`, `content_key`; statically calls `call_labels`, `content_key`
- [[Reference/Modules/learnloop/diagnosis/offline_review/runner|learnloop.diagnosis.offline_review.runner]] — imports `model_settings`; statically calls `model_settings`
- [[Reference/Modules/learnloop/diagnosis/recurrence/backlog|learnloop.diagnosis.recurrence.backlog]] — imports `record_model_calls`; statically calls `record_model_calls`
- [[Reference/Modules/learnloop/diagnosis/recurrence/benchmarks|learnloop.diagnosis.recurrence.benchmarks]] — imports `content_key`, `generation_limit`, `record_model_calls`; statically calls `content_key`, `generation_limit`, `record_model_calls`
- [[Reference/Modules/learnloop/diagnosis/recurrence/guard|learnloop.diagnosis.recurrence.guard]] — imports `content_key`, `record_model_calls`; statically calls `content_key`, `record_model_calls`
- [[Reference/Modules/learnloop/diagnosis/recurrence/judging|learnloop.diagnosis.recurrence.judging]] — imports `model_settings`; statically calls `model_settings`
- [[Reference/Modules/learnloop/diagnosis/split/card|learnloop.diagnosis.split.card]] — imports `content_key`; statically calls `content_key`
- [[Reference/Modules/learnloop/diagnosis/split/jobs|learnloop.diagnosis.split.jobs]] — imports `content_key`, `record_model_calls`; statically calls `content_key`, `record_model_calls`
- [[Reference/Modules/learnloop/diagnosis/split/pfc_report|learnloop.diagnosis.split.pfc_report]] — imports `content_key`; statically calls `content_key`
- [[Reference/Modules/learnloop/diagnosis/split/reports|learnloop.diagnosis.split.reports]] — imports `content_key`; statically calls `content_key`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/actions|learnloop.diagnosis.text_gaps.actions]] — imports `content_key`; statically calls `content_key`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/jobs|learnloop.diagnosis.text_gaps.jobs]] — imports `gate_model_requests`; statically calls `gate_model_requests`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/judges|learnloop.diagnosis.text_gaps.judges]] — imports `content_key`; statically calls `content_key`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/pipeline|learnloop.diagnosis.text_gaps.pipeline]] — imports `active_request_gate`, `gate_model_requests`; statically calls `active_request_gate`, `gate_model_requests`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/tier1|learnloop.diagnosis.text_gaps.tier1]] — imports `content_key`; statically calls `content_key`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/anthropic_api|learnloop.experiments.contextual_embeddings.anthropic_api]] — imports `active_request_gate`, `model_call`, `report_call_usage`; statically calls `active_request_gate`, `model_call`, `report_call_usage`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/callers|learnloop.experiments.contextual_embeddings.callers]] — imports `gate_model_requests`, `generation_limit`, `requested_reasoning_effort`, `tee_model_calls`, `truncation_retry_allowed`; statically calls `gate_model_requests`, `generation_limit`, `requested_reasoning_effort`, `tee_model_calls`, `truncation_retry_allowed`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/records|learnloop.experiments.contextual_embeddings.records]] — imports `content_key`, `record_model_calls`; statically calls `content_key`, `record_model_calls`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/system_arms|learnloop.experiments.contextual_embeddings.system_arms]] — imports `gate_model_requests`; statically calls `gate_model_requests`
- [[Reference/Modules/learnloop/field/classification|learnloop.field.classification]] — imports `observe_model_calls`; statically calls `observe_model_calls`
- [[Reference/Modules/learnloop/field/probability_prep|learnloop.field.probability_prep]] — imports `call_labels`, `generation_limit`, `observe_model_calls`, `single_request`; statically calls `call_labels`, `generation_limit`, `observe_model_calls`, `single_request`
- [[Reference/Modules/learnloop/figure_admission|learnloop.figure_admission]] — imports `active_request_gate`, `content_key`; statically calls `active_request_gate`, `content_key`
- [[Reference/Modules/learnloop/figures/learner_state|learnloop.figures.learner_state]] — imports `content_key`; statically calls `content_key`
- [[Reference/Modules/learnloop/figures/rich|learnloop.figures.rich]] — imports `content_key`, `gate_model_requests`; statically calls `content_key`, `gate_model_requests`
- [[Reference/Modules/learnloop/figures/service|learnloop.figures.service]] — imports `content_key`, `gate_model_requests`; statically calls `content_key`, `gate_model_requests`
- [[Reference/Modules/learnloop/hints/chooser|learnloop.hints.chooser]] — imports `content_key`; statically calls `content_key`
- [[Reference/Modules/learnloop/hints/map_builder|learnloop.hints.map_builder]] — imports `content_key`; statically calls `content_key`
- [[Reference/Modules/learnloop/hints/map_seeds|learnloop.hints.map_seeds]] — imports `content_key`; statically calls `content_key`
- [[Reference/Modules/learnloop/hints/outcome|learnloop.hints.outcome]] — imports `content_key`; statically calls `content_key`
- [[Reference/Modules/learnloop/hints/service|learnloop.hints.service]] — imports `call_labels`, `content_key`; statically calls `call_labels`, `content_key`
- [[Reference/Modules/learnloop/ingest/extractors/glm_ocr|learnloop.ingest.extractors.glm_ocr]] — imports `model_call`; statically calls `model_call`
- [[Reference/Modules/learnloop/instructional/exposure|learnloop.instructional.exposure]] — imports `content_key`; statically calls `content_key`
- [[Reference/Modules/learnloop/instructional/practice|learnloop.instructional.practice]] — imports `content_key`; statically calls `content_key`
- [[Reference/Modules/learnloop/instructional/reader_digest|learnloop.instructional.reader_digest]] — imports `content_key`; statically calls `content_key`
- [[Reference/Modules/learnloop/instructional/reader_followups|learnloop.instructional.reader_followups]] — imports `content_key`; statically calls `content_key`
- [[Reference/Modules/learnloop/instructional/screen|learnloop.instructional.screen]] — imports `content_key`; statically calls `content_key`
- [[Reference/Modules/learnloop/instructional/tools|learnloop.instructional.tools]] — imports `content_key`; statically calls `content_key`
- [[Reference/Modules/learnloop/instructional/valuation|learnloop.instructional.valuation]] — imports `content_key`; statically calls `content_key`
- [[Reference/Modules/learnloop/matching/judge|learnloop.matching.judge]] — imports `content_key`; statically calls `content_key`
- [[Reference/Modules/learnloop/ops/contamination/decider|learnloop.ops.contamination.decider]] — imports `content_key`; statically calls `content_key`
- [[Reference/Modules/learnloop/ops/contamination/judge|learnloop.ops.contamination.judge]] — imports `content_key`, `generation_limit`, `observe_model_calls`, `single_request`; statically calls `content_key`, `generation_limit`, `observe_model_calls`, `single_request`
- [[Reference/Modules/learnloop/ops/contamination/report|learnloop.ops.contamination.report]] — imports `content_key`; statically calls `content_key`
- [[Reference/Modules/learnloop/ops/embedding_backfill|learnloop.ops.embedding_backfill]] — imports `content_key`, `observe_model_calls`; statically calls `content_key`, `observe_model_calls`
- [[Reference/Modules/learnloop/ops/embedding_compare|learnloop.ops.embedding_compare]] — imports `content_key`; statically calls `content_key`
- [[Reference/Modules/learnloop/ops/family_proposals|learnloop.ops.family_proposals]] — imports `content_key`, `generation_limit`, `observe_model_calls`, `single_request`; statically calls `content_key`, `generation_limit`, `observe_model_calls`, `single_request`
- [[Reference/Modules/learnloop/ops/pf_calls|learnloop.ops.pf_calls]] — imports `content_key`, `generation_limit`, `model_settings`, `observe_model_calls`, `requested_reasoning_effort`, `single_request`; statically calls `content_key`, `generation_limit`, `model_settings`, `observe_model_calls`, `requested_reasoning_effort`, `single_request`
- [[Reference/Modules/learnloop/ops/pf_generation|learnloop.ops.pf_generation]] — imports `content_key`; statically calls `content_key`
- [[Reference/Modules/learnloop/ops/pf_publish|learnloop.ops.pf_publish]] — imports `content_key`; statically calls `content_key`
- [[Reference/Modules/learnloop/ops/pf_reports|learnloop.ops.pf_reports]] — imports `content_key`; statically calls `content_key`
- [[Reference/Modules/learnloop/ops/pf_verify|learnloop.ops.pf_verify]] — imports `content_key`; statically calls `content_key`
- [[Reference/Modules/learnloop/practice_index/dossiers|learnloop.practice_index.dossiers]] — imports `content_key`; statically calls `content_key`
- [[Reference/Modules/learnloop/practice_index/evaluation|learnloop.practice_index.evaluation]] — imports `content_key`; statically calls `content_key`
- [[Reference/Modules/learnloop/practice_index/listwise|learnloop.practice_index.listwise]] — imports `content_key`; statically calls `content_key`
- [[Reference/Modules/learnloop/practice_index/paid|learnloop.practice_index.paid]] — imports `content_key`, `generation_limit`, `observe_model_calls`, `requested_reasoning_effort`, `single_request`; statically calls `content_key`, `generation_limit`, `observe_model_calls`, `requested_reasoning_effort`, `single_request`
- [[Reference/Modules/learnloop/practice_index/query_vectors|learnloop.practice_index.query_vectors]] — imports `observe_model_calls`; statically calls `observe_model_calls`
- [[Reference/Modules/learnloop/practice_index/retrieval|learnloop.practice_index.retrieval]] — imports `content_key`; statically calls `content_key`
- [[Reference/Modules/learnloop/practice_index/usage|learnloop.practice_index.usage]] — imports `content_key`; statically calls `content_key`
- [[Reference/Modules/learnloop/projects/ai_runtime|learnloop.projects.ai_runtime]] — imports `declared_budgets`, `generation_limit`, `observe_model_calls`, `truncation_retry_allowed`; statically calls `declared_budgets`, `generation_limit`, `observe_model_calls`, `truncation_retry_allowed`
- [[Reference/Modules/learnloop/reader/reader_intent|learnloop.reader.reader_intent]] — imports `content_key`; statically calls `content_key`
- [[Reference/Modules/learnloop/reader/reader_quick_check|learnloop.reader.reader_quick_check]] — imports `content_key`, `generation_limit`, `observe_model_calls`, `requested_reasoning_effort`, `single_request`; statically calls `content_key`, `generation_limit`, `observe_model_calls`, `requested_reasoning_effort`, `single_request`
- [[Reference/Modules/learnloop/reader/reader_requests|learnloop.reader.reader_requests]] — imports `record_model_calls`; statically calls `record_model_calls`
- [[Reference/Modules/learnloop/source_retrieval/b4|learnloop.source_retrieval.b4]] — imports `content_key`; statically calls `content_key`
- [[Reference/Modules/learnloop/source_retrieval/compare|learnloop.source_retrieval.compare]] — imports `content_key`; statically calls `content_key`
- [[Reference/Modules/learnloop/source_retrieval/compare_scope|learnloop.source_retrieval.compare_scope]] — imports `content_key`; statically calls `content_key`
- [[Reference/Modules/learnloop/source_retrieval/deliverable_path|learnloop.source_retrieval.deliverable_path]] — imports `content_key`; statically calls `content_key`
- [[Reference/Modules/learnloop/source_retrieval/deliverables|learnloop.source_retrieval.deliverables]] — imports `call_labels`, `content_key`, `gate_model_requests`; statically calls `call_labels`, `content_key`, `gate_model_requests`
- [[Reference/Modules/learnloop/source_retrieval/dense|learnloop.source_retrieval.dense]] — imports `content_key`; statically calls `content_key`
- [[Reference/Modules/learnloop/source_retrieval/evaluation|learnloop.source_retrieval.evaluation]] — imports `content_key`; statically calls `content_key`
- [[Reference/Modules/learnloop/source_retrieval/fallback_space|learnloop.source_retrieval.fallback_space]] — imports `observe_model_calls`; statically calls `observe_model_calls`
- [[Reference/Modules/learnloop/source_retrieval/find_sources|learnloop.source_retrieval.find_sources]] — imports `content_key`; statically calls `content_key`
- [[Reference/Modules/learnloop/source_retrieval/library_ask|learnloop.source_retrieval.library_ask]] — imports `content_key`; statically calls `content_key`
- [[Reference/Modules/learnloop/source_retrieval/note_links|learnloop.source_retrieval.note_links]] — imports `active_request_gate`, `content_key`; statically calls `active_request_gate`, `content_key`
- [[Reference/Modules/learnloop/source_retrieval/passage_cues|learnloop.source_retrieval.passage_cues]] — imports `content_key`; statically calls `content_key`
- [[Reference/Modules/learnloop/source_retrieval/queries|learnloop.source_retrieval.queries]] — imports `content_key`; statically calls `content_key`
- [[Reference/Modules/learnloop/source_retrieval/reading_paths|learnloop.source_retrieval.reading_paths]] — imports `call_labels`, `content_key`; statically calls `call_labels`, `content_key`
- [[Reference/Modules/learnloop/source_retrieval/section_coverage|learnloop.source_retrieval.section_coverage]] — imports `active_request_gate`, `call_labels`, `content_key`, `gate_model_requests`; statically calls `active_request_gate`, `call_labels`, `content_key`, `gate_model_requests`
- [[Reference/Modules/learnloop/substrate/families|learnloop.substrate.families]] — imports `content_key`; statically calls `content_key`
- [[Reference/Modules/learnloop/teacher/checks|learnloop.teacher.checks]] — imports `content_key`; statically calls `content_key`
- [[Reference/Modules/learnloop/teacher/service|learnloop.teacher.service]] — imports `gate_model_requests`; statically calls `gate_model_requests`
- [[Reference/Modules/learnloop/tui/state|learnloop.tui.state]] — imports `record_model_calls`; statically calls `record_model_calls`
- [[Reference/Modules/learnloop/tutor/tutor_qa|learnloop.tutor.tutor_qa]] — imports `content_key`; statically calls `content_key`
- [[Reference/Modules/learnloop/workbench/check|learnloop.workbench.check]] — imports `call_labels`, `content_key`; statically calls `call_labels`, `content_key`
- [[Reference/Modules/learnloop/workbench/compare_methods|learnloop.workbench.compare_methods]] — imports `call_labels`, `content_key`; statically calls `call_labels`, `content_key`
- [[Reference/Modules/learnloop_sidecar/background_jobs|learnloop_sidecar.background_jobs]] — imports `active_request_gate`, `gate_model_requests`; statically calls `active_request_gate`, `gate_model_requests`
- [[Reference/Modules/learnloop_sidecar/handlers/correspondents|learnloop_sidecar.handlers.correspondents]] — imports `record_model_calls`; statically calls `record_model_calls`
- [[Reference/Modules/learnloop_sidecar/handlers/deliverables|learnloop_sidecar.handlers.deliverables]] — imports `record_model_calls`; statically calls `record_model_calls`
- [[Reference/Modules/learnloop_sidecar/handlers/hints|learnloop_sidecar.handlers.hints]] — imports `record_model_calls`; statically calls `record_model_calls`
- [[Reference/Modules/learnloop_sidecar/handlers/library_ask|learnloop_sidecar.handlers.library_ask]] — imports `record_model_calls`; statically calls `record_model_calls`
- [[Reference/Modules/learnloop_sidecar/handlers/notes|learnloop_sidecar.handlers.notes]] — imports `content_key`, `record_model_calls`; statically calls `content_key`, `record_model_calls`
- [[Reference/Modules/learnloop_sidecar/handlers/reader_cue_discovery|learnloop_sidecar.handlers.reader_cue_discovery]] — imports `record_model_calls`; statically calls `record_model_calls`
- [[Reference/Modules/learnloop_sidecar/handlers/reading_paths|learnloop_sidecar.handlers.reading_paths]] — imports `record_model_calls`; statically calls `record_model_calls`
- [[Reference/Modules/learnloop_sidecar/server|learnloop_sidecar.server]] — imports `record_model_calls`; statically calls `record_model_calls`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/errors|learnloop.ai.errors]] — imports `AIInterrupted`, `AIOutputTruncated`

### Platform and third-party dependencies

- Standard library: `__future__`, `contextlib`, `contextvars`, `datetime`, `functools`, `hashlib`, `json`, `logging`, `typing`, `uuid`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Configure AI Providers]]
- [[Process Model Output]]

Static participation evidence comes from [[Reference/Modules/learnloop/adaptive_difficulty/feature_audit|learnloop.adaptive_difficulty.feature_audit]], [[Reference/Modules/learnloop/adaptive_difficulty/outside|learnloop.adaptive_difficulty.outside]], [[Reference/Modules/learnloop/adaptive_difficulty/sending|learnloop.adaptive_difficulty.sending]], [[Reference/Modules/learnloop/ai/output_budget|learnloop.ai.output_budget]], [[Reference/Modules/learnloop/ai/providers/chatgpt_plan|learnloop.ai.providers.chatgpt_plan]] and 121 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/ad23_fakes.py](../../../../../../tests/ad23_fakes.py) — direct import
- [tests/ad_fakes.py](../../../../../../tests/ad_fakes.py) — direct import
- [tests/approach_map_fakes.py](../../../../../../tests/approach_map_fakes.py) — direct import
- [tests/decider_fakes.py](../../../../../../tests/decider_fakes.py) — direct import
- [tests/deliverable_fixtures.py](../../../../../../tests/deliverable_fixtures.py) — direct import
- [tests/diagnosis_fakes.py](../../../../../../tests/diagnosis_fakes.py) — direct import
- [tests/e0_fakes.py](../../../../../../tests/e0_fakes.py) — direct import
- [tests/embedding_fakes.py](../../../../../../tests/embedding_fakes.py) — direct import
- [tests/figure_fixtures.py](../../../../../../tests/figure_fixtures.py) — direct import
- [tests/hint_fakes.py](../../../../../../tests/hint_fakes.py) — direct import
- [tests/library_ask_fixtures.py](../../../../../../tests/library_ask_fixtures.py) — direct import
- [tests/local_embeddings_fakes.py](../../../../../../tests/local_embeddings_fakes.py) — direct import
- [tests/notes_fixtures.py](../../../../../../tests/notes_fixtures.py) — direct import
- [tests/passage_cue_fakes.py](../../../../../../tests/passage_cue_fakes.py) — direct import
- [tests/pf_fakes.py](../../../../../../tests/pf_fakes.py) — direct import
- [tests/practice_index_fakes.py](../../../../../../tests/practice_index_fakes.py) — direct import
- [tests/query_student_fakes.py](../../../../../../tests/query_student_fakes.py) — direct import
- [tests/reader_tutor_fakes.py](../../../../../../tests/reader_tutor_fakes.py) — direct import
- [tests/reading_path_fixtures.py](../../../../../../tests/reading_path_fixtures.py) — direct import
- [tests/router_model_fakes.py](../../../../../../tests/router_model_fakes.py) — direct import
- [tests/section_coverage_fixtures.py](../../../../../../tests/section_coverage_fixtures.py) — direct import
- [tests/source_retrieval_fakes.py](../../../../../../tests/source_retrieval_fakes.py) — direct import
- [tests/source_service_fakes.py](../../../../../../tests/source_service_fakes.py) — direct import
- [tests/test_ad1_fix_round6.py](../../../../../../tests/test_ad1_fix_round6.py) — direct import
  - `test_the_last_confirmation_runs_after_the_outer_gate_and_the_receipt`
- [tests/test_ad1_fix_round7.py](../../../../../../tests/test_ad1_fix_round7.py) — direct import
  - `test_a_refusal_at_the_deciders_start_receipt_stops_the_request`
- [tests/test_ad23_contract.py](../../../../../../tests/test_ad23_contract.py) — direct import
- [tests/test_agent_run_tokens.py](../../../../../../tests/test_agent_run_tokens.py) — direct import
  - `test_usage_readers_leave_the_open_receipt_alone`
- [tests/test_ai_compare.py](../../../../../../tests/test_ai_compare.py) — direct import
  - `test_a_json_repair_carries_the_budget_of_the_request_it_repairs`
- [tests/test_ai_single_request.py](../../../../../../tests/test_ai_single_request.py) — direct import
  - `test_codex_single_request_disables_regeneration_and_repair_only_in_scope`
  - `test_codex_single_request_fails_closed_before_sdk_startup`
  - `test_openai_single_request_disables_retry_and_repair_only_in_scope`
  - `test_single_request_is_nested_context_local_and_restored_after_failure`
- [tests/test_chatgpt_plan_provider.py](../../../../../../tests/test_chatgpt_plan_provider.py) — direct import
  - `test_a_401_under_single_request_fails_and_the_next_call_refreshes`
  - `test_a_json_repair_is_sent_with_the_budget_of_the_request_it_repairs`
  - `test_incomplete_truncated_and_broken_streams`
  - `test_output_budget_rides_in_the_prompt_never_as_max_output_tokens`
  - `test_receipts_name_the_provider_model_and_answering_model`
  - `test_single_request_never_repairs_or_retries`
- [tests/test_chatgpt_plan_workspace.py](../../../../../../tests/test_chatgpt_plan_workspace.py) — direct import
  - `test_a_workspace_turn_never_runs_under_a_single_request_budget`
  - `test_inline_mode_sends_every_file_and_records_every_file`
  - `test_tool_rounds_serve_files_and_record_each_served_entry`
- [tests/test_codex_tool_lockdown.py](../../../../../../tests/test_codex_tool_lockdown.py) — direct import
  - `test_a_failure_before_any_usage_reports_nothing_new`
  - `test_a_guardian_review_is_counted_and_refuses_the_answer`
  - `test_an_ordinary_turn_reports_exactly_what_it_did_before`
  - `test_sub_agent_threads_are_refused_and_their_tokens_counted`
  - `test_tokens_reported_before_an_ordinary_failure_reach_the_receipt_and_the_settle`
- [tests/test_contamination_report.py](../../../../../../tests/test_contamination_report.py) — direct import
- [tests/test_decider_client.py](../../../../../../tests/test_decider_client.py) — direct import
  - `test_a_malformed_paid_answer_keeps_its_usage_on_the_receipt`
  - `test_receipt_carries_body_usage_cost_model_and_labels`
- [tests/test_decider_landing.py](../../../../../../tests/test_decider_landing.py) — direct import
  - `test_inside_an_automatic_builds_request_gate_the_span_check_is_admitted_and_settled`
- [tests/test_diagnose_review_spend.py](../../../../../../tests/test_diagnose_review_spend.py) — direct import
- [tests/test_e0_review_round3.py](../../../../../../tests/test_e0_review_round3.py) — direct import
  - `test_f21_omitted_embedding_usage_keeps_the_reservation_through_the_real_wrapper`
- [tests/test_e0_review_round5.py](../../../../../../tests/test_e0_review_round5.py) — direct import
  - `test_the_key_is_in_one_header_only_and_errors_are_allowlisted`
- [tests/test_e0_review_round6.py](../../../../../../tests/test_e0_review_round6.py) — direct import
  - `test_l1_a_redirect_is_a_contract_failure_that_is_never_retried`
- [tests/test_e0_review_round8.py](../../../../../../tests/test_e0_review_round8.py) — direct import
- [tests/test_embedding_backfill.py](../../../../../../tests/test_embedding_backfill.py) — direct import
- [tests/test_embedding_compare.py](../../../../../../tests/test_embedding_compare.py) — direct import
- [tests/test_facet_identity_composition.py](../../../../../../tests/test_facet_identity_composition.py) — direct import
- [tests/test_family_proposals.py](../../../../../../tests/test_family_proposals.py) — direct import
  - `test_codex_estimate_falls_back_to_input_plus_output_tokens`
  - `test_explicit_revision_invalidates_alias_cache_but_reports_resolved_model`
- [tests/test_figure_offers.py](../../../../../../tests/test_figure_offers.py) — direct import
- [tests/test_figure_rich_rereview_fixes.py](../../../../../../tests/test_figure_rich_rereview_fixes.py) — direct import
  - `test_a_different_kind_hashes_apart_from_the_ordinary_correction`
- [tests/test_figures_rw5b_fix_round2.py](../../../../../../tests/test_figures_rw5b_fix_round2.py) — direct import
  - `test_the_tutors_explorable_rows_hash_the_input_not_the_verdict`
- [tests/test_figures_scope_redesign.py](../../../../../../tests/test_figures_scope_redesign.py) — direct import
- [tests/test_figures_show_me.py](../../../../../../tests/test_figures_show_me.py) — direct import
  - `test_an_rw5ab_request_hashes_and_prompts_exactly_as_before`
- [tests/test_figures_show_me_codex_review.py](../../../../../../tests/test_figures_show_me_codex_review.py) — direct import
- [tests/test_followups_batch5_lesson.py](../../../../../../tests/test_followups_batch5_lesson.py) — direct import
- [tests/test_glm_ocr.py](../../../../../../tests/test_glm_ocr.py) — direct import
  - `test_429_and_5xx_retry_with_their_own_admission_and_receipt`
  - `test_missing_usage_is_charged_at_the_labelled_estimate`
  - `test_q4_the_recorded_arxiv_answer_reads_cleanly`
  - `test_receipts_carry_usage_and_cost_and_never_the_key_or_file`
  - `test_spend_refusals_send_nothing_and_no_ok_sends_nothing`
  - `test_the_daily_gate_prices_glm_receipts_and_local_runs_cost_nothing`
  - `test_the_local_backend_renders_pdf_pages_for_a_real_http_server`
- [tests/test_held_grade_composition.py](../../../../../../tests/test_held_grade_composition.py) — direct import
  - `test_the_hardcase_harness_retries_a_truncated_grade_once_at_double`
- [tests/test_hint_outcome.py](../../../../../../tests/test_hint_outcome.py) — direct import
- [tests/test_ingestion_checkpoints.py](../../../../../../tests/test_ingestion_checkpoints.py) — direct import
  - `test_codex_does_not_repair_when_reported_output_consumed_the_budget`
  - `test_retry_policy_records_each_failed_request_with_unknown_usage`
  - `test_truncation_or_exhausted_repair_budget_records_usage_without_repaying`
- [tests/test_interaction_signals.py](../../../../../../tests/test_interaction_signals.py) — direct import
  - `test_hidden_physical_retry_blocked_before_network`
- [tests/test_judge_routes.py](../../../../../../tests/test_judge_routes.py) — direct import
  - `test_call_labels_reach_the_start_event_and_refuse_unknown_labels`
  - `test_receipts_store_labels_and_unlabelled_calls_work_below_175`
- [tests/test_knowledge_map_text_neighbors.py](../../../../../../tests/test_knowledge_map_text_neighbors.py) — direct import
  - `test_render_never_calls_a_model_or_writes`
- [tests/test_label_roles_cli.py](../../../../../../tests/test_label_roles_cli.py) — direct import
- [tests/test_model_call_receipt_owners.py](../../../../../../tests/test_model_call_receipt_owners.py) — direct import
  - `test_a_database_below_the_receipt_schema_lets_the_model_call_run_unrecorded`
- [tests/test_model_usage_report.py](../../../../../../tests/test_model_usage_report.py) — direct import
  - `test_runs_are_compared_with_the_budgets_recorded_on_their_receipts`
- [tests/test_notes_as_learner_text.py](../../../../../../tests/test_notes_as_learner_text.py) — direct import
- [tests/test_openai_chat_client.py](../../../../../../tests/test_openai_chat_client.py) — direct import
  - `test_failed_receipt_finish_keeps_the_paid_response`
  - `test_observer_control_exceptions_propagate_unchanged`
- [tests/test_openai_embedding_client.py](../../../../../../tests/test_openai_embedding_client.py) — direct import
  - `test_batched_openrouter_request_mrl_order_and_receipt`
  - `test_gemini_embedding_2_embeds_page_images_through_openrouter_multimodal_input`
  - `test_invalid_paid_response_still_records_usage`
  - `test_receipt_admission_failure_prevents_request`
- [tests/test_output_budget.py](../../../../../../tests/test_output_budget.py) — direct import
  - `test_a_profile_maximum_is_never_exceeded_by_the_retry`
  - `test_a_route_effort_reaches_openrouter_as_reasoning_effort`
  - `test_a_second_truncation_fails_and_is_never_accepted`
  - `test_an_admitting_caller_lets_the_transport_retry_a_truncation_at_double`
  - `test_an_owner_set_budget_is_never_exceeded_and_its_truncation_is_logged`
  - `test_inside_a_caller_budget_the_transport_leaves_the_retry_to_the_caller`
  - `test_the_route_effort_wins_over_a_profile_that_disables_thinking`
- [tests/test_pf_generation.py](../../../../../../tests/test_pf_generation.py) — direct import
  - `test_a_codex_pf_turn_starts_outside_the_vault_with_tools_off_and_never_reuses_unisolated_work`
- [tests/test_pf_verify_extraction_parity.py](../../../../../../tests/test_pf_verify_extraction_parity.py) — direct import
- [tests/test_plan_first_transport.py](../../../../../../tests/test_plan_first_transport.py) — direct import
  - `test_admission_equals_wire_and_every_body_keeps_the_grammar`
- [tests/test_probability_prep.py](../../../../../../tests/test_probability_prep.py) — direct import
- [tests/test_project_cli.py](../../../../../../tests/test_project_cli.py) — direct import
- [tests/test_reader_ca3_compare_anywhere.py](../../../../../../tests/test_reader_ca3_compare_anywhere.py) — direct import
- [tests/test_reader_digest_narrative.py](../../../../../../tests/test_reader_digest_narrative.py) — direct import
- [tests/test_reader_passage_check.py](../../../../../../tests/test_reader_passage_check.py) — direct import
  - `test_a_metered_check_is_one_admitted_physical_request_held_to_its_output_allowance`
- [tests/test_recurrence_benchmarks.py](../../../../../../tests/test_recurrence_benchmarks.py) — direct import
  - `test_b1_ignores_cache_rows_without_a_writer`
- [tests/test_required_method_authority.py](../../../../../../tests/test_required_method_authority.py) — direct import
- [tests/test_router_r2b_serving.py](../../../../../../tests/test_router_r2b_serving.py) — direct import
  - `test_the_daily_guard_counts_todays_router_receipts`
- [tests/test_rw1a_composition.py](../../../../../../tests/test_rw1a_composition.py) — direct import
- [tests/test_sidecar_close_cancels_jobs.py](../../../../../../tests/test_sidecar_close_cancels_jobs.py) — direct import
  - `test_a_closed_contexts_job_has_its_next_physical_request_refused`
- [tests/test_sidecar_contract.py](../../../../../../tests/test_sidecar_contract.py) — direct import
  - `test_model_call_receipts_are_owned_by_the_normalized_submission_key`
- [tests/test_source_service_spend_accounting.py](../../../../../../tests/test_source_service_spend_accounting.py) — direct import
  - `test_a_finished_request_counts_its_reported_cost_once`
  - `test_a_released_reservation_cannot_start_its_request`
  - `test_a_request_settled_without_its_cost_counts_a_lower_reported_cost`
  - `test_a_request_settled_without_its_reported_cost_counts_its_receipt`
- [tests/test_source_service_spend_envelopes.py](../../../../../../tests/test_source_service_spend_envelopes.py) — direct import
  - `test_a_settled_request_is_counted_once_not_by_its_receipt_and_its_reservation`
- [tests/test_sources_merge_composition.py](../../../../../../tests/test_sources_merge_composition.py) — direct import
  - `test_authoring_runs_at_the_policy_budget_and_retries_a_truncation_once_at_double`
- [tests/test_spend_controls.py](../../../../../../tests/test_spend_controls.py) — direct import
  - `test_declared_caps_persist_on_real_receipt_for_success_and_failure`
  - `test_dry_run_is_nonmutating_and_does_not_emit_model_receipts`
- [tests/test_stuck_prompt.py](../../../../../../tests/test_stuck_prompt.py) — direct import
- [tests/test_t6_followup_composition.py](../../../../../../tests/test_t6_followup_composition.py) — direct import
  - `test_the_seed_unit_is_admitted_at_the_policy_budget`
- [tests/test_teacher_te1_review_fixes.py](../../../../../../tests/test_teacher_te1_review_fixes.py) — direct import
- [tests/test_tier1_decider.py](../../../../../../tests/test_tier1_decider.py) — direct import
  - `test_contamination_one_routes_switch_restores_its_old_checkpoints_budget_check_and_ledger`
  - `test_decider_receipt_and_spend_ignore_llm_output_budget`
- [tests/test_ux_phase1_review_fixes.py](../../../../../../tests/test_ux_phase1_review_fixes.py) — direct import
  - `test_f2_rereview_a_transport_retry_is_refused_when_the_failed_attempt_used_the_room`
  - `test_f2_rereview_append_reconciliation_calls_are_admitted_one_by_one`
  - `test_f2_rereview_every_physical_attempt_is_admitted_retries_and_repairs_included`
- [tests/text_gap_fakes.py](../../../../../../tests/text_gap_fakes.py) — direct import
- [tests/workbench_help_fakes.py](../../../../../../tests/workbench_help_fakes.py) — direct import

## Modification guidance

- Change provider-neutral transport/routing policy here; do not move feature prompts or feature result models into the shared AI layer.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/ai/execution.py](../../../../../../src/learnloop/ai/execution.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

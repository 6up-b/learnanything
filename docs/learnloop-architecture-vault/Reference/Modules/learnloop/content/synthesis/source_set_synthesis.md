---
title: "learnloop.content.synthesis.source_set_synthesis"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/content/synthesis/source_set_synthesis.py"
source_paths:
  - "src/learnloop/content/synthesis/source_set_synthesis.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.content.synthesis"
layer: "domain"
concepts:
  - "Learning System"
  - "AI Architecture"
workflows:
  - "Import Canonical Sources"
  - "Build a Study Map"
aliases:
  - "learnloop.content.synthesis.source_set_synthesis module"
  - "src/learnloop/content/synthesis/source_set_synthesis.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-content-synthesis"
---

# `learnloop.content.synthesis.source_set_synthesis`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/content/synthesis/_package|learnloop.content.synthesis]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.content.synthesis.source_set_synthesis` exists within [[Reference/Modules/learnloop/content/synthesis/_package|learnloop.content.synthesis]] to own the behavior summarized by its module contract: Bootstrap synthesis: brief -> sharded synthesis -> dependency-closed proposal -> applied study map (source-ingestion v2 §8, ING M6).

The authoritative system-level explanation remains in [[Learning System]], [[AI Architecture]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/content/synthesis/source_set_synthesis.py](../../../../../../../src/learnloop/content/synthesis/source_set_synthesis.py) |
| Source lines | 3897 |
| Owning package | [[Reference/Modules/learnloop/content/synthesis/_package|learnloop.content.synthesis]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class StudyMapError(ValueError)` ([source](../../../../../../../src/learnloop/content/synthesis/source_set_synthesis.py), line 123) — A typed bootstrap-synthesis failure (gate hard-fail, budget, missing input).
  - `__init__(self, code: str, message: str, *, diagnostics: list[dict[str, Any]] | None=None, synthesis_run_id: str | None=None, candidate_preserved: bool=False)` (line 126; internal)
- `request_source_set_synthesis(client: StructuredTransport, context: SourceSetSynthesisContext) -> SourceSetSynthesis` ([source](../../../../../../../src/learnloop/content/synthesis/source_set_synthesis.py), line 136) — Synthesize one source-set shard through the shared transport.
- `request_concept_graph_structuring(client: StructuredTransport, context: ConceptGraphContext) -> ConceptGraphStructuring` ([source](../../../../../../../src/learnloop/content/synthesis/source_set_synthesis.py), line 149) — Structure a merged candidate graph through the shared transport.
- `structuring_checkpoint(repository: Any, context: ConceptGraphContext, settings: dict[str, Any]) -> ModelCheckpoint[ConceptGraphStructuring]` ([source](../../../../../../../src/learnloop/content/synthesis/source_set_synthesis.py), line 176) — The structuring call's checkpoint: the request key of its rendered prompt and of the result schema it asks for (with or without registry merges), under the run's settings.
- `class StudyMapResult` ([source](../../../../../../../src/learnloop/content/synthesis/source_set_synthesis.py), line 191)
  - `as_dict(self) -> dict[str, Any]` (line 214; public)
- `manifest_inputs(inputs: _SynthesisInputs) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/synthesis/source_set_synthesis.py), line 487) — The source-side fields of a run's manifest: what it read, exactly.
- `resolve_subject_id(source_set: Any, vault: LoadedVault) -> str` ([source](../../../../../../../src/learnloop/content/synthesis/source_set_synthesis.py), line 1912) — The subject a synthesized study map belongs to: the source set's own subject_id (§4.3 — sets are subject-scoped), never "first subject in the vault", which misfires on multi-subject vaults and crashes on fresh ones.
- `create_study_map(root: Path, source_set_id: str, *, client: Any, brief: dict[str, Any] | None=None, mode: str='auto', apply: bool=False, apply_gate: Callable[[], bool] | None=None, create_goal: bool=False, repository: Repository | None=None, clock: Clock | None=None, budget_overrides: dict[str, int] | None=None, unlimited_token_budget: bool=False, progress: ProgressFn | None=None, embedding_client_factory: Callable[[], Any] | None=None, facet_identity_client: Any=None) -> StudyMapResult` ([source](../../../../../../../src/learnloop/content/synthesis/source_set_synthesis.py), line 2037) — ``embedding_client_factory`` replaces the ``ai.routing.embedding`` client for Slice 2 T5 nominations (tests); used only when nominations are on.
- `facet_identity_result(root: Path, repository: Repository, plan: FacetIdentityPlan | None, run_id: str | None) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/content/synthesis/source_set_synthesis.py), line 2104) — The run's facet-identity summary and its actions with their undo state.
- `plan_study_map_embedding(root: Path, source_set_id: str) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/synthesis/source_set_synthesis.py), line 2126) — Dry run of one bootstrap synthesis's Slice 2 T5 embedding spend.
- `bootstrap_scope(vault: LoadedVault, brief: Any, *, nominator: GraphNominator | None, facet_identity_client: Any=None) -> Any` ([source](../../../../../../../src/learnloop/content/synthesis/source_set_synthesis.py), line 2146) — The ``scope`` a bootstrap synthesis records in its manifest: the brief's scope and, while they are on, what the nominator and the facet-identity judge run under.
- `resolve_brief(vault: LoadedVault, brief: Mapping[str, Any] | None) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/synthesis/source_set_synthesis.py), line 2170) — The brief a bootstrap or an append reads and records, resolved before its manifest is built.
- `derive_candidate_repairs(candidate: dict[str, Any]) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/content/synthesis/source_set_synthesis.py), line 2588) — Mechanically-safe repair ops for a preserved synthesis candidate.
- `apply_candidate_repairs(candidate: dict[str, Any], ops: list[dict[str, Any]]) -> tuple[dict[str, Any], list[dict[str, Any]]]` ([source](../../../../../../../src/learnloop/content/synthesis/source_set_synthesis.py), line 2637) — Apply typed repair ops to a candidate dict; returns (repaired, log).
- `revalidate_synthesis_candidate(root: Path, synthesis_run_id: str, *, apply: bool=False, create_goal: bool=False, repair: bool=False, repair_ops: list[dict[str, Any]] | None=None, repository: Repository | None=None, clock: Clock | None=None, progress: ProgressFn | None=None, apply_gate: Callable[[], bool] | None=None) -> StudyMapResult` ([source](../../../../../../../src/learnloop/content/synthesis/source_set_synthesis.py), line 2687) — Re-run normalization, gates, and persistence over a preserved candidate with ZERO model calls.

### Module constants

- `SYNTHESIS_AGENT_PURPOSE` ([src/learnloop/content/synthesis/source_set_synthesis.py](../../../../../../../src/learnloop/content/synthesis/source_set_synthesis.py), line 119)
- `BOOTSTRAP_PROPOSAL_PURPOSE` ([src/learnloop/content/synthesis/source_set_synthesis.py](../../../../../../../src/learnloop/content/synthesis/source_set_synthesis.py), line 120)
- `STRUCTURING_PURPOSE` ([src/learnloop/content/synthesis/source_set_synthesis.py](../../../../../../../src/learnloop/content/synthesis/source_set_synthesis.py), line 165)
- `_SHARD_PREFIX_RE` ([src/learnloop/content/synthesis/source_set_synthesis.py](../../../../../../../src/learnloop/content/synthesis/source_set_synthesis.py), line 2582)
- `_CANDIDATE_ITEM_FIELDS` ([src/learnloop/content/synthesis/source_set_synthesis.py](../../../../../../../src/learnloop/content/synthesis/source_set_synthesis.py), line 2585)

## Internal implementation anchors

- `_structuring_result_model(context: ConceptGraphContext) -> type[ConceptGraphStructuring]` ([source](../../../../../../../src/learnloop/content/synthesis/source_set_synthesis.py), line 168)
- `class _SynthesisInputs` ([source](../../../../../../../src/learnloop/content/synthesis/source_set_synthesis.py), line 240)
- `_assessment_signal_spans(inventory: dict[str, Any], *, held_out_only: bool) -> set[str]` ([source](../../../../../../../src/learnloop/content/synthesis/source_set_synthesis.py), line 265)
- `_collect_inputs(repo: Repository, vault: LoadedVault, source_set: SourceSet) -> _SynthesisInputs` ([source](../../../../../../../src/learnloop/content/synthesis/source_set_synthesis.py), line 275)
- `_chosen_row(row: Mapping[str, Any]) -> dict[str, str]` ([source](../../../../../../../src/learnloop/content/synthesis/source_set_synthesis.py), line 475) — Which inventory row was read: its own id and extraction, which can be an earlier reading than the one the entry's citations resolve against, and a hash of its content (a row updated in place keeps its id).
- `_registry_index(vault: LoadedVault) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/synthesis/source_set_synthesis.py), line 506) — A compact existing-registry index for the prompt (never full contracts).
- `_notify(progress: ProgressFn | None, stage: str, message: str, *, current: int | None=None, total: int | None=None) -> None` ([source](../../../../../../../src/learnloop/content/synthesis/source_set_synthesis.py), line 523)
- `_shards(unit_inventories: list[dict[str, Any]], shard_input_tokens: int) -> list[list[dict[str, Any]]]` ([source](../../../../../../../src/learnloop/content/synthesis/source_set_synthesis.py), line 535)
- `_resolve_span_requests(repo: Repository, requests: list[dict[str, Any]], inputs: _SynthesisInputs, *, max_count: int, char_cap: int) -> tuple[list[dict[str, Any]], list[str]]` ([source](../../../../../../../src/learnloop/content/synthesis/source_set_synthesis.py), line 557) — One bounded span-request round (§8.5).
- `_slug(prefix: str, text: str, fallback: str) -> str` ([source](../../../../../../../src/learnloop/content/synthesis/source_set_synthesis.py), line 608)
- `class _Normalized` ([source](../../../../../../../src/learnloop/content/synthesis/source_set_synthesis.py), line 614)
- `_span_refs(refs: list[Any], inputs: _SynthesisInputs, *, default_relation: str) -> tuple[list[ProvenanceRef], list[dict[str, Any]], list[str]]` ([source](../../../../../../../src/learnloop/content/synthesis/source_set_synthesis.py), line 634) — Build gate ProvenanceRefs + YAML source_refs from synth span refs.
- `_unresolved_citations(gate_refs: list[ProvenanceRef]) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/content/synthesis/source_set_synthesis.py), line 695) — The citations of a candidate that did not resolve, by their ids (they support nothing).
- `_joined_contribution(candidate: Mapping[str, Any]) -> facet_meaning.Contribution` ([source](../../../../../../../src/learnloop/content/synthesis/source_set_synthesis.py), line 706) — What a retired candidate offers the survivor its meaning joins (in-run consolidation or attach).
- `_support_citations(gate_refs: list[ProvenanceRef]) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/content/synthesis/source_set_synthesis.py), line 723) — The validated citations of a candidate, as a proposal's ``meaning_support`` carries them.
- `_normalize(synth: Any, inputs: _SynthesisInputs, vault: LoadedVault, now: str, *, subject_id: str, items_off: bool=False, nominator: Any=None, facet_identity_plan: Any=None) -> _Normalized` ([source](../../../../../../../src/learnloop/content/synthesis/source_set_synthesis.py), line 734)
- `_facet_identity_actions(retired_targets: Mapping[str, tuple[str, str, Any, dict[str, Any]]], *, pre_union: Mapping[str, dict[str, Any]], minted_payload_by_id: Mapping[str, dict[str, Any]], registered_before: Mapping[str, dict[str, Any]], rows: Sequence[Mapping[str, Any]], vault: LoadedVault, aliased: set[str] | None=None, contract_notes: Mapping[str, Sequence[str]] | None=None) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/content/synthesis/source_set_synthesis.py), line 1817) — One undoable action per survivor the proposal changes (facet identity).
- `_keep_sibling_criterion_dependencies(item_id: str, criteria: list[dict[str, Any]], dropped_diagnostics: list[dict[str, Any]]) -> None` ([source](../../../../../../../src/learnloop/content/synthesis/source_set_synthesis.py), line 1929) — Keep each criterion's ``depends_on`` to sibling criterion ids (in place).
- `_method_target_view(vault: LoadedVault, rows: list[dict[str, Any]]) -> Any` ([source](../../../../../../../src/learnloop/content/synthesis/source_set_synthesis.py), line 1980) — The registry plus this batch's concepts, facets and learning objects, as :func:`learnloop.vault.required_method.method_targets` reads them.
- `_row(item_type: str, entity_id: str, payload: dict[str, Any], depends_on: list[str], *, client_id: str, now: str, target_entity_id: str | None=None, target_entity_type: str | None=None) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/synthesis/source_set_synthesis.py), line 2011)
- `_facet_identity_plan(candidate: Any, vault: LoadedVault, repository: Repository, run_id: str, *, nominator: Any=None, client: Any=None, progress: ProgressFn | None=None, attach_enabled: bool=True) -> FacetIdentityPlan | None` ([source](../../../../../../../src/learnloop/content/synthesis/source_set_synthesis.py), line 2079) — Facet identity for one run's candidates (``None`` when switched off).
- `_gate_open(apply_gate: Callable[[], bool] | None) -> bool` ([source](../../../../../../../src/learnloop/content/synthesis/source_set_synthesis.py), line 2122)
- `_create_study_map(vault: LoadedVault, repository: Repository, root: Path, source_set_id: str, *, client: Any, brief: dict[str, Any], mode: str, apply: bool, create_goal: bool, clock: Clock | None, budget_overrides: dict[str, int] | None=None, unlimited_token_budget: bool=False, progress: ProgressFn | None=None, embedding_client_factory: Callable[[], Any] | None=None, facet_identity_client: Any=None, apply_gate: Callable[[], bool] | None=None) -> StudyMapResult` ([source](../../../../../../../src/learnloop/content/synthesis/source_set_synthesis.py), line 2190)
- `_gate_and_persist(vault: LoadedVault, repository: Repository, source_set: SourceSet, merged: Any, inputs: _SynthesisInputs, *, subject_id: str, agent_run_id: str | None, synthesis_run_id: str, now: str, usage: dict[str, Any] | None, resolved_hashes: list[str], clock: Clock | None, progress: ProgressFn | None=None, items_off: bool=False, token_usage: TokenUsage | None=None, grading_client: Any=None, nominator: Any=None, facet_identity_plan: Any=None, fresh_answers: bool=False) -> tuple[str, list[dict[str, Any]], list[dict[str, Any]], _Normalized, ProposalMatch | None]` ([source](../../../../../../../src/learnloop/content/synthesis/source_set_synthesis.py), line 2408) — Normalize -> §8.7 gates -> persist proposal, over a merged candidate.
- `class _SynthesisBudget` ([source](../../../../../../../src/learnloop/content/synthesis/source_set_synthesis.py), line 2813) — One synthesis run's spend against its ingest token budgets.
- `class _SavedAnswers` ([source](../../../../../../../src/learnloop/content/synthesis/source_set_synthesis.py), line 2876) — The saved model answers one synthesis run's candidate came from: each shard's result and each pass's checkpoint, fresh or reused.
- `_run_synthesis(transport, repository, inputs, vault, source_set, brief, budgets, *, clock, client: Any=None, provider: str | None=None, model: str | None=None, manifest_hash: str | None=None, unlimited_token_budget: bool=False, progress: ProgressFn | None=None, nominator: Any=None, one_facet_per_skill: bool=False, answers: _SavedAnswers | None=None)` ([source](../../../../../../../src/learnloop/content/synthesis/source_set_synthesis.py), line 2900)
- `_synthesis_pass_key(prompt: str, schema: dict[str, Any], settings: dict[str, Any], *, purpose: str='synthesis_pass') -> str` ([source](../../../../../../../src/learnloop/content/synthesis/source_set_synthesis.py), line 3069) — Checkpoint identity of one synthesis pass: the request key of the exact prompt and schema sent, under the provider settings that shape the answer, with no budget in it.
- `_result_tokens(result: Any) -> int` ([source](../../../../../../../src/learnloop/content/synthesis/source_set_synthesis.py), line 3080) — Rough output-token estimate: characters of the JSON the model wrote / 4.
- `_merge_synthesis(base: Any, extra: Any) -> Any` ([source](../../../../../../../src/learnloop/content/synthesis/source_set_synthesis.py), line 3097)
- `_namespace_synthesis_shard(result: Any, ordinal: int) -> Any` ([source](../../../../../../../src/learnloop/content/synthesis/source_set_synthesis.py), line 3103) — Make model-authored client ids local to one synthesis shard.
- `_consolidate_same_title_concepts(result: Any) -> Any` ([source](../../../../../../../src/learnloop/content/synthesis/source_set_synthesis.py), line 3144) — Deterministic pass: fold concepts whose normalized titles are identical.
- `_source_skeletons(repository: Repository, inputs: _SynthesisInputs) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/content/synthesis/source_set_synthesis.py), line 3169) — Compact per-source big-picture views from already-paid-for artifacts.
- `_model_graph_structuring(merged: Any, client: Any, source_set: Any, inputs: _SynthesisInputs, repository: Repository, vault: LoadedVault, *, shard_count: int, input_tokens_estimate: int, total_input_ceiling: int | None, output_budget_tokens: int | None=None, progress: ProgressFn | None=None, nominator: Any=None, settings: dict[str, Any] | None=None, answers: _SavedAnswers | None=None) -> tuple[Any, dict[str, Any]]` ([source](../../../../../../../src/learnloop/content/synthesis/source_set_synthesis.py), line 3226) — One bounded model pass over the WHOLE merged candidate (§8.5): folds semantic duplicate concepts AND authors the big-picture concept relations (part_of hierarchy, prerequisites, confusables) across every shard and source, using the compact source skeletons as whole-span context.
- `_registry_concept_nominations(nominator: Any, concepts: list[Any]) -> tuple[dict[str, list[Any]], dict[str, Any]]` ([source](../../../../../../../src/learnloop/content/synthesis/source_set_synthesis.py), line 3411) — Each candidate's top-k registry concepts by definition embedding.
- `_registry_nomination_context(nominations: dict[str, list[Any]], vault: LoadedVault) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]` ([source](../../../../../../../src/learnloop/content/synthesis/source_set_synthesis.py), line 3427) — Titles and definitions for the nominated registry concepts (not ids alone).
- `_validated_registry_merges(outcome: Any, merged: Any, mapping: dict[str, str], nominations: dict[str, list[Any]], vault: LoadedVault) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/content/synthesis/source_set_synthesis.py), line 3457) — Every registry merge the model decided, with whether the guards allow it.
- `_record_registry_merge_verdicts(repository: Repository, client: Any, decisions: list[dict[str, Any]], candidate_queries: dict[str, Any], vault: LoadedVault, *, source_set_id: str) -> str | None` ([source](../../../../../../../src/learnloop/content/synthesis/source_set_synthesis.py), line 3511) — Append each registry-merge decision to ``judgment_ledger`` (task ``same_concept``).
- `_fold_into_registry_concepts(result: Any, mapping: dict[str, str]) -> Any` ([source](../../../../../../../src/learnloop/content/synthesis/source_set_synthesis.py), line 3561) — Drop candidates decided to BE registry concepts; point references at them.
- `_validated_merge_mapping(consolidation: Any, result: Any) -> dict[str, str]` ([source](../../../../../../../src/learnloop/content/synthesis/source_set_synthesis.py), line 3623) — duplicate client id -> canonical client id, from validated merge groups.
- `_apply_concept_merges(result: Any, mapping: dict[str, str]) -> Any` ([source](../../../../../../../src/learnloop/content/synthesis/source_set_synthesis.py), line 3649) — Fold duplicate concepts into their canonical and rewrite all references.
- `_duplicate_client_id_diagnostics(rows: list[dict[str, Any]]) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/content/synthesis/source_set_synthesis.py), line 3722)
- `_gate_context(vault, repository, inputs, findings, nominator=None) -> GateContext` ([source](../../../../../../../src/learnloop/content/synthesis/source_set_synthesis.py), line 3737)
- `_findings_to_diagnostics(findings) -> list[GateDiagnostic]` ([source](../../../../../../../src/learnloop/content/synthesis/source_set_synthesis.py), line 3760)
- `_persist_generation_needs(repository, subject_id, source_set_id, synthesis_run_id, findings, *, clock)` ([source](../../../../../../../src/learnloop/content/synthesis/source_set_synthesis.py), line 3775)
- `_count_items(rows: list[dict[str, Any]]) -> dict[str, int]` ([source](../../../../../../../src/learnloop/content/synthesis/source_set_synthesis.py), line 3801)
- `_is_exam_prep(brief: dict[str, Any]) -> bool` ([source](../../../../../../../src/learnloop/content/synthesis/source_set_synthesis.py), line 3808)
- `_apply_and_wire_goal(root: Path, repository: Repository, result: StudyMapResult, *, brief: dict[str, Any], create_goal: bool, clock: Clock | None, facet_ids: list[str] | None=None, progress: ProgressFn | None=None) -> None` ([source](../../../../../../../src/learnloop/content/synthesis/source_set_synthesis.py), line 3813) — Accept the proposal, then create the exam-prep Goal when asked.
- `_create_goal_from_brief(root: Path, brief: dict[str, Any], facet_ids: list[str], *, clock: Clock | None, provenance_key: str | None=None) -> str | None` ([source](../../../../../../../src/learnloop/content/synthesis/source_set_synthesis.py), line 3847)
- `_create_goal_from_brief_locked(root: Path, brief: dict[str, Any], facet_ids: list[str], *, clock: Clock | None, provenance_key: str | None) -> str | None` ([source](../../../../../../../src/learnloop/content/synthesis/source_set_synthesis.py), line 3853) — Create a Goal wired to the freshly minted facets (§5.1), after acceptance.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]] — imports `StudyMapError`, `create_study_map`, `derive_candidate_repairs`, `plan_study_map_embedding`, `revalidate_synthesis_candidate`; statically calls `create_study_map`, `derive_candidate_repairs`, `plan_study_map_embedding`, `revalidate_synthesis_candidate`
- [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]] — imports `StudyMapError`, `create_study_map`, `revalidate_synthesis_candidate`; statically calls `create_study_map`, `revalidate_synthesis_candidate`
- [[Reference/Modules/learnloop/content/synthesis/source_append|learnloop.content.synthesis.source_append]] — imports `StudyMapError`, `_collect_inputs`, `_facet_identity_plan`, `_gate_context`, `_normalize`, `_resolve_span_requests`, `_result_tokens`, `_row`, `_span_refs`, `_support_citations`, `_synthesis_pass_key`, `facet_identity_result`, `manifest_inputs`, `resolve_brief`; statically calls `StudyMapError`, `_collect_inputs`, `_facet_identity_plan`, `_gate_context`, `_normalize`, `_resolve_span_requests`, `_result_tokens`, `_row`, `_span_refs`, `_support_citations`, `_synthesis_pass_key`, `facet_identity_result`, `manifest_inputs`, `resolve_brief`
- [[Reference/Modules/learnloop_sidecar/handlers/ingest|learnloop_sidecar.handlers.ingest]] — imports `StudyMapError`, `create_study_map`; statically calls `create_study_map`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/execution|learnloop.ai.execution]] — imports `ModelCheckpoint`, `checkpointed`, `content_key`, `declared_budgets`, `generation_limit`, `model_settings`, `request_key`; calls `ModelCheckpoint`, `checkpointed`, `content_key`, `declared_budgets`, `generation_limit`, `model_settings`, `request_key`
- [[Reference/Modules/learnloop/ai/runs|learnloop.ai.runs]] — imports `finish_agent_run`; calls `finish_agent_run`
- [[Reference/Modules/learnloop/ai/transport|learnloop.ai.transport]] — imports `StructuredTransport`, `execute_structured_operation`; calls `execute_structured_operation`
- [[Reference/Modules/learnloop/ai/usage|learnloop.ai.usage]] — imports `TokenUsage`, `UsageMeter`, `consume_client_usage`; calls `TokenUsage`, `UsageMeter`, `consume_client_usage`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/content/authoring/authoring_gates|learnloop.content.authoring.authoring_gates]] — imports `build_instrument_gates`; calls `build_instrument_gates`
- [[Reference/Modules/learnloop/content/facet_identity/actions|learnloop.content.facet_identity.actions]] — imports `describe`, `list_actions`, `record_proposed_actions`; calls `describe`, `list_actions`, `record_proposed_actions`
- [[Reference/Modules/learnloop/content/facet_identity/authority|learnloop.content.facet_identity.authority]] — imports `module`; calls `CitationProblem`, `Contribution`, `check_meaning_write`, `join_candidate`, `meaning_policy`, `overlay`, `support_entries`
- [[Reference/Modules/learnloop/content/facet_identity/judge|learnloop.content.facet_identity.judge]] — imports `manifest_identity`; calls `manifest_identity`
- [[Reference/Modules/learnloop/content/facet_identity/plan|learnloop.content.facet_identity.plan]] — imports `FacetIdentityPlan`, `build_plan`, `ingest_dry_run`; calls `FacetIdentityPlan`, `build_plan`, `ingest_dry_run`
- [[Reference/Modules/learnloop/content/facet_identity/views|learnloop.content.facet_identity.views]] — imports `UNION_LIST_FIELDS`
- [[Reference/Modules/learnloop/content/proposals/patches|learnloop.content.proposals.patches]] — imports `apply_accepted_items`, `compute_target_hash`; calls `apply_accepted_items`, `compute_target_hash`
- [[Reference/Modules/learnloop/content/sources/exam_material|learnloop.content.sources.exam_material]] — imports `module`; calls `exam_material`
- [[Reference/Modules/learnloop/content/sources/role_authority|learnloop.content.sources.role_authority]] — imports `is_scope_only_role`, `role_authority`; calls `is_scope_only_role`, `role_authority`
- [[Reference/Modules/learnloop/content/sources/source_outline|learnloop.content.sources.source_outline]] — imports `resolve_extraction_id`; calls `resolve_extraction_id`
- [[Reference/Modules/learnloop/content/synthesis/ai_contracts|learnloop.content.synthesis.ai_contracts]] — imports `CONCEPT_GRAPH_REGISTRY_PROMPT_VERSION`, `ConceptGraphContext`, `ConceptGraphStructuring`, `ConceptGraphStructuringWithRegistry`, `SourceSetSynthesis`, `SourceSetSynthesisContext`, `concept_graph_has_registry_nominations`, `concept_graph_structuring_prompt`, `source_set_synthesis_prompt`, `source_set_synthesis_prompt_version`; calls `ConceptGraphContext`, `SourceSetSynthesis`, `SourceSetSynthesisContext`, `concept_graph_has_registry_nominations`, `concept_graph_structuring_prompt`, `source_set_synthesis_prompt`, `source_set_synthesis_prompt_version`
- [[Reference/Modules/learnloop/content/synthesis/brief|learnloop.content.synthesis.brief]] — imports `validate_brief`; calls `validate_brief`
- [[Reference/Modules/learnloop/content/synthesis/exam_profile|learnloop.content.synthesis.exam_profile]] — imports `ExamUnitEntry`, `aggregate_exam_profile`; calls `ExamUnitEntry`, `aggregate_exam_profile`
- [[Reference/Modules/learnloop/content/synthesis/facet_mint_gate|learnloop.content.synthesis.facet_mint_gate]] — imports `MintDisposition`, `judge_facet_mints`, `mint_diagnostic`; calls `judge_facet_mints`, `mint_diagnostic`
- [[Reference/Modules/learnloop/content/synthesis/graph_nomination|learnloop.content.synthesis.graph_nomination]] — imports `CONCEPT_RECIPE`, `GraphNominator`, `annotate_mint_report`, `concept_query`, `plan_ingest_embedding`; calls `annotate_mint_report`, `concept_query`, `plan_ingest_embedding`
- [[Reference/Modules/learnloop/content/synthesis/proposal_match|learnloop.content.synthesis.proposal_match]] — imports `ProposalMatch`, `RejectedProposalMatch`, `match_proposal`; calls `RejectedProposalMatch`, `match_proposal`
- [[Reference/Modules/learnloop/content/synthesis/source_unit_inventory|learnloop.content.synthesis.source_unit_inventory]] — imports `choose_unit_inventory`, `current_inventory_identity`; calls `choose_unit_inventory`, `current_inventory_identity`
- [[Reference/Modules/learnloop/content/synthesis/source_unit_selection|learnloop.content.synthesis.source_unit_selection]] — imports `compute_effective_units`, `effective_scope_groups`; calls `compute_effective_units`, `effective_scope_groups`
- [[Reference/Modules/learnloop/content/synthesis/synthesis_gates|learnloop.content.synthesis.synthesis_gates]] — imports `ATTACH_GROWABLE_FIELDS`, `GateContext`, `GateDiagnostic`, `GateItem`, `GateProposal`, `ProvenanceRef`, `run_synthesis_gates`; calls `GateContext`, `GateDiagnostic`, `GateItem`, `GateProposal`, `ProvenanceRef`, `run_synthesis_gates`
- [[Reference/Modules/learnloop/content/synthesis/synthesis_manifests|learnloop.content.synthesis.synthesis_manifests]] — imports `agent_run_input_context_hash`, `build_manifest`, `content_hash`, `persist_manifest`; calls `agent_run_input_context_hash`, `build_manifest`, `content_hash`, `persist_manifest`
- [[Reference/Modules/learnloop/content/synthesis/vault_epigraphs|learnloop.content.synthesis.vault_epigraphs]] — imports `digest_from_proposal_rows`, `generate_vault_epigraphs`; calls `digest_from_proposal_rows`, `generate_vault_epigraphs`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/stores/judgments|learnloop.db.stores.judgments]] — imports `append_judgment`; calls `append_judgment`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`, `snake_case`; calls `new_ulid`, `snake_case`
- [[Reference/Modules/learnloop/learner/capability_mapping|learnloop.learner.capability_mapping]] — imports `CAPABILITY_VOCABULARY`
- [[Reference/Modules/learnloop/learner/identifiability|learnloop.learner.identifiability]] — imports `analyze_identifiability`, `build_proposal_view`; calls `analyze_identifiability`, `build_proposal_view`
- [[Reference/Modules/learnloop/learner/learner_profile|learnloop.learner.learner_profile]] — imports `read_learner_profile`; calls `read_learner_profile`
- [[Reference/Modules/learnloop/vault/embedding_recipes|learnloop.vault.embedding_recipes]] — imports `concept_definition_text`; calls `concept_definition_text`
- [[Reference/Modules/learnloop/vault/loader|learnloop.vault.loader]] — imports `load_vault`; calls `load_vault`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `Goal`, `LoadedVault`, `SourceSet`
- [[Reference/Modules/learnloop/vault/paths|learnloop.vault.paths]] — imports `VaultPaths`; calls `VaultPaths`
- [[Reference/Modules/learnloop/vault/repository|learnloop.vault.repository]] — imports `vault_repository`; calls `vault_repository`
- [[Reference/Modules/learnloop/vault/required_method|learnloop.vault.required_method]] — imports `advisory_statement_flag`, `method_targets`, `normalize_required_method`; calls `advisory_statement_flag`, `method_targets`, `normalize_required_method`
- [[Reference/Modules/learnloop/vault/yaml_io|learnloop.vault.yaml_io]] — imports `read_yaml`, `write_yaml`; calls `read_yaml`, `write_yaml`
- [[Reference/Modules/learnloop/vault_lock|learnloop.vault_lock]] — imports `vault_mutation_lock`; calls `vault_mutation_lock`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `copy`, `dataclasses`, `hashlib`, `json`, `pathlib`, `re`, `sqlite3`, `types`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Import Canonical Sources]]
- [[Build a Study Map]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]], [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]], [[Reference/Modules/learnloop/content/synthesis/source_append|learnloop.content.synthesis.source_append]], [[Reference/Modules/learnloop_sidecar/handlers/ingest|learnloop_sidecar.handlers.ingest]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/facet_authority_helpers.py](../../../../../../../tests/facet_authority_helpers.py) — direct import
- [tests/identity_pins_helpers.py](../../../../../../../tests/identity_pins_helpers.py) — direct import
- [tests/source_append_helpers.py](../../../../../../../tests/source_append_helpers.py) — direct import
- [tests/test_collection_append_units.py](../../../../../../../tests/test_collection_append_units.py) — direct import
  - `test_a_wholly_new_member_keeps_the_unfiltered_append`
- [tests/test_contamination_report.py](../../../../../../../tests/test_contamination_report.py) — direct import
  - `test_exam_leakage_shortlists_nearest_held_out_spans_for_the_judge`
- [tests/test_curriculum_c3_exam_scoping.py](../../../../../../../tests/test_curriculum_c3_exam_scoping.py) — direct import
  - `test_a_syllabus_is_never_inventoried_for_a_study_map`
- [tests/test_decider_landing.py](../../../../../../../tests/test_decider_landing.py) — direct import
- [tests/test_exam_protection.py](../../../../../../../tests/test_exam_protection.py) — direct import
  - `test_a_held_out_textbook_unit_never_feeds_synthesis_as_teaching`
- [tests/test_exam_readiness_and_conflict.py](../../../../../../../tests/test_exam_readiness_and_conflict.py) — direct import
  - `test_conflict_resolution_notation_mapping_materializes_mapping`
  - `test_conflict_resolution_preserves_locators_and_audit`
  - `test_exam_readiness_predicted_score_distribution_is_analytic`
  - `test_exam_readiness_report_is_deterministic_and_labels_ready_vs_demonstrated`
- [tests/test_facet_authority.py](../../../../../../../tests/test_facet_authority.py) — direct import
  - `test_a_bootstrap_candidate_carrying_a_registered_id_rewords_it_uncited_only_with_the_owners_confirm`
  - `test_a_citations_locator_is_derived_from_its_validated_ids`
  - `test_a_cited_bootstrap_candidate_carrying_a_registered_id_rewords_it_as_a_checked_update`
  - `test_a_provenance_link_to_an_unselected_unit_is_dropped`
  - `test_an_exam_and_notes_reword_hard_fails_exam_authority`
  - `test_an_exam_override_inside_a_textbook_extraction_is_exam_material`
  - `test_an_unselected_span_never_corroborates_exam_material`
  - `test_citations_take_the_units_role_override`
- [tests/test_facet_identity.py](../../../../../../../tests/test_facet_identity.py) — direct import
  - `test_an_undone_in_run_merge_stays_apart_when_the_run_is_planned_again`
- [tests/test_facet_identity_composition.py](../../../../../../../tests/test_facet_identity_composition.py) — direct import
- [tests/test_facet_identity_ingest.py](../../../../../../../tests/test_facet_identity_ingest.py) — direct import
  - `test_a_candidate_matching_a_registered_facet_becomes_its_alias`
  - `test_a_duplicate_candidate_is_merged_before_the_gates_and_undo_re_mints_it`
  - `test_an_unapplied_proposal_records_the_merge_without_an_undo`
  - `test_an_unavailable_judge_keeps_the_candidates_and_says_so`
  - `test_revalidation_replays_the_plan_without_a_judge_call`
  - `test_revalidation_with_the_switch_off_replays_no_stored_plan`
  - `test_the_desktop_lists_a_runs_merges_and_undoes_one`
  - `test_the_kill_switch_restores_the_prompt_and_never_calls_the_judge`
  - `test_the_run_summary_names_its_run_and_each_action_its_evidence_and_undo_limits`
  - `test_the_synthesize_dry_run_plans_the_ingest_judge`
  - `test_two_sets_on_one_in_run_survivor_are_one_action_that_undoes_both`
- [tests/test_facet_mint_gate.py](../../../../../../../tests/test_facet_mint_gate.py) — direct import
  - `test_ingest_aliases_a_collapsing_candidate_into_a_registered_facet`
- [tests/test_facet_reword_confirm.py](../../../../../../../tests/test_facet_reword_confirm.py) — direct import
  - `test_a_bootstrap_candidate_carrying_a_registered_id_uncited_is_kept_for_confirm`
  - `test_a_bootstrap_reword_citing_exam_material_under_the_wrong_unit_is_dropped_not_held`
  - `test_an_exam_only_append_reword_still_hard_fails`
  - `test_an_exam_only_bootstrap_candidate_carrying_a_registered_id_is_dropped_not_held`
- [tests/test_facet_reword_paths.py](../../../../../../../tests/test_facet_reword_paths.py) — direct import
  - `test_an_exam_only_facet_reword_hard_fails_the_exam_authority_gate`
- [tests/test_graph_nomination_ingest.py](../../../../../../../tests/test_graph_nomination_ingest.py) — direct import
  - `test_bootstrap_dry_run_plans_ingest_embedding_without_a_client`
  - `test_kill_switch_never_reuses_a_nominated_bootstrap_cached_before_the_fix`
  - `test_revalidation_reuses_paid_vectors_and_makes_no_embedding_call`
- [tests/test_ingest_instrument_gates.py](../../../../../../../tests/test_ingest_instrument_gates.py) — direct import
  - `test_apply_stamps_coverage_boundary_and_later_rebuilds_add_nothing`
  - `test_explicit_capabilities_produce_no_capability_diagnostics`
  - `test_omitted_component_capability_defaults_with_diagnostic`
  - `test_omitted_criterion_target_capability_defaults_with_diagnostic`
  - `test_reachability_summary_reports_minted_cells`
  - `test_single_alternative_any_of_gets_review_diagnostic`
  - `test_synthesis_lane_blocks_selected_response_items`
  - `test_synthesis_lane_records_persona_gate_outcome`
  - `test_vacuous_recipe_hard_fails_at_the_gate`
- [tests/test_ingest_runner.py](../../../../../../../tests/test_ingest_runner.py) — direct import
  - `test_append_synthesis_preserves_gate_failure_code_and_diagnostics`
- [tests/test_ingestion_checkpoints.py](../../../../../../../tests/test_ingestion_checkpoints.py) — direct import
  - `test_synthesis_pass_key_changes_with_each_provider_setting`
  - `test_synthesis_pass_key_changes_with_prompt_and_schema`
- [tests/test_inventory_choice.py](../../../../../../../tests/test_inventory_choice.py) — direct import
  - `test_a_reinventory_by_a_newer_model_reaches_the_synthesis_prompt`
  - `test_a_row_under_the_current_prompt_label_beats_an_older_label`
  - `test_coverage_reads_the_row_synthesis_reads`
- [tests/test_inventory_merge_parallel.py](../../../../../../../tests/test_inventory_merge_parallel.py) — direct import
  - `test_synthesis_gather_folds_merged_group_once_with_member_fallback`
- [tests/test_maintenance_feed.py](../../../../../../../tests/test_maintenance_feed.py) — direct import
  - `test_dismiss_and_snooze_do_not_change_curriculum`
  - `test_maintenance_notice_aging_policies`
  - `test_maintenance_notice_deterministic_generation`
- [tests/test_model_usage_report.py](../../../../../../../tests/test_model_usage_report.py) — direct import
  - `test_synthesis_purposes_match_the_synthesis_operations`
- [tests/test_model_work_checkpoints.py](../../../../../../../tests/test_model_work_checkpoints.py) — direct import
  - `test_a_gate_failure_drops_the_structuring_answer_it_judged`
  - `test_synthesis_pass_checkpoint_that_no_longer_validates_is_discarded`
- [tests/test_outer_cache_keys.py](../../../../../../../tests/test_outer_cache_keys.py) — direct import
- [tests/test_practice_leakage.py](../../../../../../../tests/test_practice_leakage.py) — direct import
- [tests/test_required_method_items.py](../../../../../../../tests/test_required_method_items.py) — direct import
  - `test_synthesis_keeps_a_required_method_only_on_a_procedure_target`
  - `test_synthesis_publishes_a_required_method_presented_with_the_canonical_sentence`
- [tests/test_rerun_proposals.py](../../../../../../../tests/test_rerun_proposals.py) — direct import
  - `test_a_changed_payload_is_not_a_match`
  - `test_a_partly_rejected_proposal_is_returned_with_its_rejections_kept`
  - `test_a_repaired_candidate_equal_to_a_rejected_proposal_is_refused`
  - `test_a_retry_after_an_apply_failure_applies_the_proposal_it_persisted`
- [tests/test_retired_config_identities.py](../../../../../../../tests/test_retired_config_identities.py) — direct import
  - `test_a_bootstrap_run_completed_before_arc_c_is_reused_for_the_same_request`
  - `test_bootstrap_manifest_hashes_the_facet_identity_config_as_before_arc_c`
- [tests/test_revision_refresh.py](../../../../../../../tests/test_revision_refresh.py) — direct import
  - `test_new_revision_pinned_membership_requires_confirmation`
  - `test_unchanged_spans_keep_links_changed_spans_go_stale`
- [tests/test_source_append.py](../../../../../../../tests/test_source_append.py) — direct import
  - `test_a_retry_after_an_append_gate_failure_pays_for_a_fresh_answer`
  - `test_an_append_budget_failure_leaves_both_run_rows_failed`
  - `test_an_append_over_its_input_ceiling_is_refused_before_any_call`
  - `test_an_over_budget_append_answer_is_checkpointed_and_the_retry_does_not_repay`
  - `test_append_context_bounded_by_neighborhood`
  - `test_n_sources_append_linear_inventory_and_bounded_context`
  - `test_planted_full_map_resend_fails_scaling_gate`
- [tests/test_source_outcome_analytics.py](../../../../../../../tests/test_source_outcome_analytics.py) — direct import
- [tests/test_source_set_synthesis.py](../../../../../../../tests/test_source_set_synthesis.py) — direct import
  - `test_a_fresh_synthesis_after_a_gate_failure_pays_for_a_fresh_answer`
  - `test_a_vault_whose_facets_used_to_be_locked_still_bootstraps`
  - `test_apply_candidate_repairs_vocabulary`
  - `test_auto_repair_drops_criterion_id_dependencies`
  - `test_bootstrap_canonicalizes_prerequisite_and_confusable_concepts`
  - `test_bootstrap_end_to_end_applies_learnable_map`
  - `test_bootstrap_epigraph_failure_leaves_the_synthesis_unchanged`
  - `test_bootstrap_mints_concept_for_unanchored_learning_object`
  - `test_bootstrap_persists_vault_epigraphs`
  - `test_bootstrap_tolerates_unresolved_concept_relationships`
  - `test_cached_generation_resume_creates_goal_without_new_model_calls`
  - `test_cached_generation_resumes_apply_after_failure_without_new_model_calls`
  - `test_complete_base_request_budget_is_checked_before_paying`
  - `test_cross_shard_same_title_concepts_consolidate_deterministically`
  - `test_derive_candidate_repairs_only_targets_criterion_refs`
  - `test_evidence_pass_retry_reuses_first_paid_pass`
  - `test_exam_prep_apply_creates_goal_wired_to_applied_facets`
  - `test_exam_shifts_blueprint_distribution`
  - `test_facets_cite_textbook_not_exam_and_held_out_wording_absent`
  - `test_graph_structuring_merges_near_duplicates_and_authors_relations`
  - `test_graph_structuring_relations_become_concept_edges`
  - `test_integration_at_coordination_is_kept_but_flagged`
  - `test_integration_below_coordination_is_kept_silently`
  - `test_integration_without_capability_is_dropped_not_defaulted`
  - `test_invalid_structuring_nomination_is_a_noop`
  - `test_legacy_vault_acceptance_refused`
  - `test_lo_prerequisites_derive_concept_edges_without_model_relations`
  - `test_manifest_cache_hit_writes_no_epigraphs`
  - `test_manifest_idempotency_cache_zero_new_calls`
  - `test_non_ascii_output_is_charged_by_characters_not_escapes`
  - `test_over_budget_pass_is_checkpointed_and_reused_under_a_larger_budget`
  - `test_replay_identical_after_apply`
  - `test_resolve_subject_id_prefers_source_set_over_vault`
  - `test_revalidate_requires_a_preserved_candidate`
  - `test_revalidate_saved_candidate_completes_without_model`
  - `test_revalidation_creates_the_exam_goal_from_the_manifest_brief`
  - `test_shard_checkpoints_survive_post_generation_failure`
  - `test_synthesis_can_disable_local_token_ceilings`
  - `test_synthesis_progress_reports_shard_and_stage_messages`
  - `test_synthesis_shards_namespace_declarations_and_references`
- [tests/test_structured_transport_parity.py](../../../../../../../tests/test_structured_transport_parity.py) — direct import
- [tests/test_subject_registry.py](../../../../../../../tests/test_subject_registry.py) — direct import
- [tests/test_synthesis_answer_reuse.py](../../../../../../../tests/test_synthesis_answer_reuse.py) — direct import
  - `test_a_bootstrap_rejection_keeps_a_fresh_answer_another_run_saved`
  - `test_a_rejected_reused_shard_drops_its_span_round_answer`
  - `test_an_append_rejection_keeps_a_fresh_answer_another_run_saved`
- [tests/test_synthesis_criterion_dependencies.py](../../../../../../../tests/test_synthesis_criterion_dependencies.py) — direct import
  - `test_normalize_keeps_only_sibling_criterion_dependencies`
- [tests/test_synthesis_eval.py](../../../../../../../tests/test_synthesis_eval.py) — direct import
  - `test_canned_synthesis_scores_perfect_against_matching_gold`
- [tests/test_synthesis_identifiability.py](../../../../../../../tests/test_synthesis_identifiability.py) — direct import
  - `test_non_identifiable_bootstrap_persists_generation_need`
- [tests/test_ux_phase1_usability_round1.py](../../../../../../../tests/test_ux_phase1_usability_round1.py) — direct import
  - `test_u1_a_new_books_questions_are_not_refused_for_another_subjects_locks`
  - `test_u1_a_subject_with_a_goal_scoped_facet_rebuilds_too`
- [tests/tutor_citations_helpers.py](../../../../../../../tests/tutor_citations_helpers.py) — direct import

## Modification guidance

- Change source set synthesis policy here when content owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/content/synthesis/source_set_synthesis.py](../../../../../../../src/learnloop/content/synthesis/source_set_synthesis.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

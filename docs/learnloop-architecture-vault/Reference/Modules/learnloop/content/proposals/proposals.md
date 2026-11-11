---
title: "learnloop.content.proposals.proposals"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/content/proposals/proposals.py"
source_paths:
  - "src/learnloop/content/proposals/proposals.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.content.proposals"
layer: "domain"
concepts:
  - "Learning System"
  - "AI Architecture"
workflows:
  - "Import Canonical Sources"
  - "Build a Study Map"
aliases:
  - "learnloop.content.proposals.proposals module"
  - "src/learnloop/content/proposals/proposals.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-content-proposals"
---

# `learnloop.content.proposals.proposals`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/content/proposals/_package|learnloop.content.proposals]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

This module keeps proposals behavior inside its owning package, [[Reference/Modules/learnloop/content/proposals/_package|learnloop.content.proposals]]. Its public surface centers on `request_authoring_proposal`, `AuthoringRequestRefused`, `context_sources`, `dispatch_authoring_request`, `list_proposals`, `build_authoring_context`, `authoring_context_stats`, `authoring_context_hash` and 20 more public symbols.

The authoritative system-level explanation remains in [[Learning System]], [[AI Architecture]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/content/proposals/proposals.py](../../../../../../../src/learnloop/content/proposals/proposals.py) |
| Source lines | 2536 |
| Owning package | [[Reference/Modules/learnloop/content/proposals/_package|learnloop.content.proposals]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `request_authoring_proposal(client: AIProviderClient, context: AuthoringContext) -> AuthoringProposal` ([source](../../../../../../../src/learnloop/content/proposals/proposals.py), line 54) — Run the feature-owned authoring operation on a structured provider.
- `class AuthoringRequestRefused(ValueError)` ([source](../../../../../../../src/learnloop/content/proposals/proposals.py), line 70) — A guarded authoring request was refused before it was sent (adaptive difficulty's A8 revalidation): a refusal, never an ordinary provider or repair failure.
- `context_sources(context: AuthoringContext) -> list[dict[str, str | None]]` ([source](../../../../../../../src/learnloop/content/proposals/proposals.py), line 80) — The source identities an authoring context quotes (fix rounds 11-12, F34/F40): each source ref's extraction and spans (``{"kind": "span", ...}``; the whole extraction when it names no span) and each note it includes (``{"kind": "note", "note_id": ...}``: a canonical note is a so…
- `dispatch_authoring_request(client: AIProviderClient, context: AuthoringContext, *, request_guard: Callable[..., None] | None=None, commissioned: bool=False) -> AuthoringProposal` ([source](../../../../../../../src/learnloop/content/proposals/proposals.py), line 110) — The one place an authoring request is sent (fix round 10, R5): the first request and every repair.
- `list_proposals(root: Path) -> list[dict]` ([source](../../../../../../../src/learnloop/content/proposals/proposals.py), line 131)
- `build_authoring_context(vault: LoadedVault, *, subjects: list[str] | None=None, note_ids: list[str] | None=None, source_refs: list[dict] | None=None, instructions: str | None=None, focus_concepts: list[str] | None=None, focus_facets: list[str] | None=None) -> AuthoringContext` ([source](../../../../../../../src/learnloop/content/proposals/proposals.py), line 145) — Assemble a deterministic authoring context from selected vault sources.
- `authoring_context_stats(context: AuthoringContext) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/proposals/proposals.py), line 275)
- `authoring_context_hash(context: AuthoringContext) -> str` ([source](../../../../../../../src/learnloop/content/proposals/proposals.py), line 315)
- `class DiagnosticTarget` ([source](../../../../../../../src/learnloop/content/proposals/proposals.py), line 334) — Relational review context for a diagnostic-authoring proposal (spec §5.3).
- `diagnostic_target_from_need(need: dict[str, Any]) -> DiagnosticTarget` ([source](../../../../../../../src/learnloop/content/proposals/proposals.py), line 353) — Build a :class:`DiagnosticTarget` from an intervention need row (spec §5.3).
- `diagnostic_review_errors(item: AuthoringProposalItem, context: DiagnosticTarget | None) -> list[str]` ([source](../../../../../../../src/learnloop/content/proposals/proposals.py), line 382) — Hard §5.3 validation errors for a diagnostic-authoring item.
- `diagnostic_review_warnings(item: AuthoringProposalItem, context: DiagnosticTarget | None) -> list[str]` ([source](../../../../../../../src/learnloop/content/proposals/proposals.py), line 412) — Soft §5.3 warnings: footprint exceeds implicated set / hits demonstrated facets.
- `evaluate_review_policy(item: AuthoringProposalItem, vault: LoadedVault, *, source_refs: list[SourceRef] | None=None, context: DiagnosticTarget | None=None) -> str` ([source](../../../../../../../src/learnloop/content/proposals/proposals.py), line 429) — Resolve an item's effective review route under the auto-apply-low-risk policy.
- `generate_authoring_proposal(root: Path, codex_client: AIProviderClient, *, subjects: list[str] | None=None, note_ids: list[str] | None=None, source_refs: list[dict[str, Any]] | None=None, instructions: str | None=None, focus_concepts: list[str] | None=None, focus_facets: list[str] | None=None, model: str | None=None, codex_revision: str | None=None, merge_context_source_refs: bool=False, row_transform: Callable[[list[dict[str, Any]]], None] | None=None, prompt_version: str | None=None, clock: Clock | None=None, vault_view: Callable[[LoadedVault, Any], LoadedVault] | None=None, request_guard: Callable[..., None] | None=None) -> str` ([source](../../../../../../../src/learnloop/content/proposals/proposals.py), line 489) — Run authoring generation through a AIProviderClient and persist the result.
- `build_diagnostic_authoring_context(vault: LoadedVault, repository: Repository, need: dict[str, Any]) -> AuthoringContext` ([source](../../../../../../../src/learnloop/content/proposals/proposals.py), line 604) — Package ⟨belief, learner answer, grader evidence, source item⟩ for authoring (spec §5.1).
- `generate_diagnostic_proposal(root: Path, client: AIProviderClient, *, need_id: str, model: str | None=None, clock: Clock | None=None) -> str` ([source](../../../../../../../src/learnloop/content/proposals/proposals.py), line 753) — Author a discriminating diagnostic from a pending misconception need (spec §5/§6).
- `persist_authoring_proposal(root: Path, proposal: AuthoringProposal, *, provider: str='import', model: str | None=None, clock: Clock | None=None) -> str` ([source](../../../../../../../src/learnloop/content/proposals/proposals.py), line 898)
- `maybe_promote_self_tagged_fatal_error(vault: LoadedVault, repository: Repository, *, item: PracticeItem, error_type: str | None, clock: Clock | None=None) -> str | None` ([source](../../../../../../../src/learnloop/content/proposals/proposals.py), line 968) — Queue a reviewed proposal to add a repeatedly self-tagged misconception ``E`` to an item's rubric ``fatal_errors`` (spec §12.4 — durable-probe promotion).
- `reject_items(root: Path, patch_id: str, item_ids: list[str] | None=None) -> int` ([source](../../../../../../../src/learnloop/content/proposals/proposals.py), line 1061)
- `edit_proposal_item(root: Path, patch_id: str, item_id: str, edited_payload: dict[str, Any], *, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/proposals/proposals.py), line 1220)
- `refresh_proposal_item_validation(root: Path, patch_id: str, item_id: str, *, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/proposals/proposals.py), line 1260)
- `repair_proposal_item_audit(root: Path, patch_id: str, item_id: str, audit: dict[str, Any], *, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/proposals/proposals.py), line 1300) — Replace a pending item's audit and revalidate the complete proposal item.
- `delete_proposal_item(root: Path, patch_id: str, item_id: str) -> bool` ([source](../../../../../../../src/learnloop/content/proposals/proposals.py), line 1347) — Permanently remove a single proposal item from the inbox.
- `accept_items(root: Path, patch_id: str, item_ids: list[str] | None=None, *, clock: Clock | None=None) -> PatchApplyResult` ([source](../../../../../../../src/learnloop/content/proposals/proposals.py), line 1366)
- `queue_accepted_diagnostic_followups(repository: Repository, *, patch_id: str | None=None) -> int` ([source](../../../../../../../src/learnloop/content/proposals/proposals.py), line 1407) — Backfill queued follow-up actions for accepted diagnostic proposals.
- `reset_items(root: Path, patch_id: str, item_ids: list[str] | None=None, *, clock: Clock | None=None) -> int` ([source](../../../../../../../src/learnloop/content/proposals/proposals.py), line 1484) — Undo a decision: send rejected-but-never-applied items back to ``pending``.
- `proposal_item_row(item: AuthoringProposalItem, now: str, *, vault: LoadedVault, proposal: AuthoringProposal, provider: str) -> dict` ([source](../../../../../../../src/learnloop/content/proposals/proposals.py), line 1503)
- `auto_apply_rows(root: Path, patch_id: str, rows: list[dict[str, Any]]) -> None` ([source](../../../../../../../src/learnloop/content/proposals/proposals.py), line 1687)

### Module constants

- `REFUSED_MESSAGE` ([src/learnloop/content/proposals/proposals.py](../../../../../../../src/learnloop/content/proposals/proposals.py), line 77)
- `_TEACH_BACK_PRACTICE_MODE` ([src/learnloop/content/proposals/proposals.py](../../../../../../../src/learnloop/content/proposals/proposals.py), line 1984)
- `_RUBRIC_CRITERION_TIERS` ([src/learnloop/content/proposals/proposals.py](../../../../../../../src/learnloop/content/proposals/proposals.py), line 1985)
- `_CRITERION_TARGET_ROLES` ([src/learnloop/content/proposals/proposals.py](../../../../../../../src/learnloop/content/proposals/proposals.py), line 1989)

## Internal implementation anchors

- `_check_request(request_guard: Callable[..., None], context: AuthoringContext) -> None` ([source](../../../../../../../src/learnloop/content/proposals/proposals.py), line 102)
- `_excerpt(text: str, limit: int=280) -> str` ([source](../../../../../../../src/learnloop/content/proposals/proposals.py), line 140)
- `_vault_evidence_facet_unions(vault: LoadedVault) -> dict[str, list[str]]` ([source](../../../../../../../src/learnloop/content/proposals/proposals.py), line 246) — Per-LO union of canonical evidence facet ids across blueprints and items.
- `_vault_surface_family_unions(vault: LoadedVault) -> dict[str, list[str]]` ([source](../../../../../../../src/learnloop/content/proposals/proposals.py), line 267)
- `_diagnostic_payload_fatal_misconception_ids(payload: dict[str, Any]) -> set[str]` ([source](../../../../../../../src/learnloop/content/proposals/proposals.py), line 371)
- `_has_id_collision(item: AuthoringProposalItem, vault: LoadedVault) -> bool` ([source](../../../../../../../src/learnloop/content/proposals/proposals.py), line 473)
- `_diagnostic_proposal_item_row(item: AuthoringProposalItem, now: str, *, vault: LoadedVault, proposal: AuthoringProposal, provider: str, context: DiagnosticTarget) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/proposals/proposals.py), line 671) — Persisted row for a diagnostic-authoring item: base validation + §5.3 checks.
- `_gate_target_record(payload: dict[str, Any], target: DiagnosticTarget, records_by_id: dict[str, MisconceptionRecord]) -> MisconceptionRecord | None` ([source](../../../../../../../src/learnloop/content/proposals/proposals.py), line 710) — The registry belief a generated item is gated against (its keyed fatal, else first).
- `_reopen_need_after_gate_failure(repository: Repository, *, need_id: str, patch_id: str, item_id: str | None, results: list[GateResult], need: dict[str, Any]) -> None` ([source](../../../../../../../src/learnloop/content/proposals/proposals.py), line 727) — Reopen the need with the sim estimates attached (spec §6 reopen).
- `_proposal_with_context_source_refs(proposal: AuthoringProposal, context_source_refs: list[dict[str, Any]]) -> AuthoringProposal` ([source](../../../../../../../src/learnloop/content/proposals/proposals.py), line 876)
- `_agent_provider_fields(client: AIProviderClient, *, model: str | None, provider_revision: str | None) -> dict[str, str | None]` ([source](../../../../../../../src/learnloop/content/proposals/proposals.py), line 948)
- `_diagnostic_reopen_candidates(repository: Repository, patch_id: str, item_ids: list[str] | None) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/content/proposals/proposals.py), line 1072)
- `_is_diagnostic_probe_item(item: dict[str, Any]) -> bool` ([source](../../../../../../../src/learnloop/content/proposals/proposals.py), line 1087)
- `_normalize_diagnostic_probe_mode(vault: LoadedVault, repository: Repository, patch_id: str, diagnostic_items: list[dict[str, Any]], *, clock: Clock | None=None) -> None` ([source](../../../../../../../src/learnloop/content/proposals/proposals.py), line 1104) — Stamp ``practice_mode: diagnostic_probe`` on accepted diagnostic items.
- `_reopen_diagnostic_needs_for_rejected_items(repository: Repository, patch_id: str, candidate_items: list[dict[str, Any]]) -> None` ([source](../../../../../../../src/learnloop/content/proposals/proposals.py), line 1155)
- `_need_ids_for_diagnostic_item(item: dict[str, Any], queued_by_id: dict[str, dict[str, Any]], patch_id: str) -> list[str]` ([source](../../../../../../../src/learnloop/content/proposals/proposals.py), line 1196)
- `_queue_accepted_diagnostic_followups_for_patch(repository: Repository, patch_id: str, diagnostic_items: list[dict[str, Any]]) -> int` ([source](../../../../../../../src/learnloop/content/proposals/proposals.py), line 1437)
- `_accepted_practice_item_id(item: dict[str, Any]) -> str | None` ([source](../../../../../../../src/learnloop/content/proposals/proposals.py), line 1458)
- `_append_intervention_queued_action(repository: Repository, attempt_id: str, practice_item_id: str) -> bool` ([source](../../../../../../../src/learnloop/content/proposals/proposals.py), line 1466)
- `_hold_required_method_to_rule(payload: dict[str, Any], item: AuthoringProposalItem, vault: LoadedVault) -> list[str]` ([source](../../../../../../../src/learnloop/content/proposals/proposals.py), line 1547) — Method-explicit items (owner rule 2026-10-13) on a generated practice item.
- `_repair_invalid_proposal_items(codex_client: AIProviderClient, context: AuthoringContext, proposal: AuthoringProposal, rows: list[dict[str, Any]], *, vault: LoadedVault, provider: str, now: str, request_guard: Callable[..., None] | None=None) -> tuple[AuthoringProposal, list[dict[str, Any]]]` ([source](../../../../../../../src/learnloop/content/proposals/proposals.py), line 1604) — One-shot self-repair for items that failed deterministic validation.
- `_source_refs_for_item(source_refs: list[SourceRef], source_ref_ids: list[str]) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/content/proposals/proposals.py), line 1694)
- `_provenance_for_refs(source_refs: list[dict[str, Any]], provider: str) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/proposals/proposals.py), line 1703)
- `_backfill_practice_item_facet_weights(item: AuthoringProposalItem, vault: LoadedVault) -> None` ([source](../../../../../../../src/learnloop/content/proposals/proposals.py), line 1712) — Derive only facet-weight links that are logically unambiguous.
- `_has_direct_grounding(source_refs: list[SourceRef], source_ref_ids: list[str]) -> bool` ([source](../../../../../../../src/learnloop/content/proposals/proposals.py), line 1757)
- `_validation_errors(item: AuthoringProposalItem, vault: LoadedVault, source_refs: list[SourceRef], *, proposal: AuthoringProposal | None=None) -> list[str]` ([source](../../../../../../../src/learnloop/content/proposals/proposals.py), line 1763)
- `_source_statement_edit_errors(vault: LoadedVault, payload: dict[str, Any], entity_id: Any) -> list[str]` ([source](../../../../../../../src/learnloop/content/proposals/proposals.py), line 1811) — An update that would rewrite a statement whose required method was decided on its wording (review F15; ``rewrites_decided_statement``).
- `_validation_warnings(item: AuthoringProposalItem, vault: LoadedVault, *, proposal: AuthoringProposal | None=None) -> list[str]` ([source](../../../../../../../src/learnloop/content/proposals/proposals.py), line 1821)
- `_instrument_gate_errors(payload: dict[str, Any], vault: LoadedVault, repository: Repository | None=None) -> list[str]` ([source](../../../../../../../src/learnloop/content/proposals/proposals.py), line 1838) — Report-only instrument-gate verdicts for the edit/refresh door.
- `_edited_payload_validation_errors(item: dict[str, Any], edited_payload: dict[str, Any], vault: LoadedVault, *, batch_source_refs: list[dict[str, Any]] | None=None, repository: Repository | None=None) -> list[str]` ([source](../../../../../../../src/learnloop/content/proposals/proposals.py), line 1867)
- `_payload_source_ref_validation_errors(payload: dict[str, Any], vault: LoadedVault, batch_source_refs: list[dict[str, Any]] | None) -> list[str]` ([source](../../../../../../../src/learnloop/content/proposals/proposals.py), line 1907)
- `_payload_source_ref_dicts(payload: dict[str, Any]) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/content/proposals/proposals.py), line 1930)
- `_dedupe_preserve_order(values: list[str]) -> list[str]` ([source](../../../../../../../src/learnloop/content/proposals/proposals.py), line 1940)
- `_required_create_payload_errors(item_type: str, payload: dict[str, Any], vault: LoadedVault, proposal: AuthoringProposal | None) -> list[str]` ([source](../../../../../../../src/learnloop/content/proposals/proposals.py), line 1951)
- `_missing(value: Any) -> bool` ([source](../../../../../../../src/learnloop/content/proposals/proposals.py), line 1992)
- `_attempt_type_validation_errors(payload: dict[str, Any]) -> list[str]` ([source](../../../../../../../src/learnloop/content/proposals/proposals.py), line 1996)
- `_practice_item_metadata_errors(payload: dict[str, Any], vault: LoadedVault, proposal: AuthoringProposal | None, *, generated: bool) -> list[str]` ([source](../../../../../../../src/learnloop/content/proposals/proposals.py), line 2003)
- `_teach_back_rubric_errors(payload: dict[str, Any], evidence_facets: list[str], criterion_facet_weights: dict[str, dict[str, float]]) -> list[str]` ([source](../../../../../../../src/learnloop/content/proposals/proposals.py), line 2078) — Structural checks for teach_back rubrics beyond the generic rubric rules.
- `_criterion_target_errors(criterion: dict[str, Any], *, criterion_ids: set[str], single_criterion: bool) -> list[str]` ([source](../../../../../../../src/learnloop/content/proposals/proposals.py), line 2116) — Structural checks on A1's authored criterion targets (Meas §3.A1).
- `_practice_item_rubric_errors(payload: dict[str, Any]) -> list[str]` ([source](../../../../../../../src/learnloop/content/proposals/proposals.py), line 2173)
- `_practice_item_metadata_warnings(payload: dict[str, Any], vault: LoadedVault, proposal: AuthoringProposal | None, *, generated: bool) -> list[str]` ([source](../../../../../../../src/learnloop/content/proposals/proposals.py), line 2235)
- `_generated_practice_reward_metadata_errors(payload: dict[str, Any], evidence_facets: list[str], vault: LoadedVault, proposal: AuthoringProposal | None) -> list[str]` ([source](../../../../../../../src/learnloop/content/proposals/proposals.py), line 2286)
- `_rubric_criterion_ids(payload: dict[str, Any], vault: LoadedVault, proposal: AuthoringProposal | None) -> set[str]` ([source](../../../../../../../src/learnloop/content/proposals/proposals.py), line 2321)
- `_rubric_fatal_error_ids(payload: dict[str, Any], vault: LoadedVault, proposal: AuthoringProposal | None) -> set[str]` ([source](../../../../../../../src/learnloop/content/proposals/proposals.py), line 2340)
- `_string_list(value: Any) -> list[str]` ([source](../../../../../../../src/learnloop/content/proposals/proposals.py), line 2359)
- `_float_map(value: Any) -> dict[str, float]` ([source](../../../../../../../src/learnloop/content/proposals/proposals.py), line 2365)
- `_nested_float_map(value: Any) -> dict[str, dict[str, float]]` ([source](../../../../../../../src/learnloop/content/proposals/proposals.py), line 2377)
- `_generated_practice_audit_error(item: AuthoringProposalItem) -> str | None` ([source](../../../../../../../src/learnloop/content/proposals/proposals.py), line 2386)
- `_looks_source_linked_generated(item: AuthoringProposalItem) -> bool` ([source](../../../../../../../src/learnloop/content/proposals/proposals.py), line 2401)
- `_available_concept_ids(vault: LoadedVault, proposal: AuthoringProposal | None) -> set[str]` ([source](../../../../../../../src/learnloop/content/proposals/proposals.py), line 2422)
- `_available_learning_object_ids(vault: LoadedVault, proposal: AuthoringProposal | None) -> set[str]` ([source](../../../../../../../src/learnloop/content/proposals/proposals.py), line 2438)
- `_concept_edge_validation_errors(payload: dict[str, Any], vault: LoadedVault, proposal: AuthoringProposal | None) -> list[str]` ([source](../../../../../../../src/learnloop/content/proposals/proposals.py), line 2450)
- `_default_edge_id(payload: dict[str, Any]) -> str | None` ([source](../../../../../../../src/learnloop/content/proposals/proposals.py), line 2478)
- `_unresolved_source_ref_ids(vault: LoadedVault, source_refs: list[SourceRef], source_ref_ids: list[str]) -> list[str]` ([source](../../../../../../../src/learnloop/content/proposals/proposals.py), line 2489)
- `_source_ref_resolves(vault: LoadedVault, source: SourceRef) -> bool` ([source](../../../../../../../src/learnloop/content/proposals/proposals.py), line 2503)
- `_path_matches(source_path: str | None, note_path: str | None) -> bool` ([source](../../../../../../../src/learnloop/content/proposals/proposals.py), line 2535)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]] — imports `maybe_promote_self_tagged_fatal_error`; statically calls `maybe_promote_self_tagged_fatal_error`
- [[Reference/Modules/learnloop/cli/runtime|learnloop.cli.runtime]] — imports `accept_items`, `authoring_context_stats`, `build_authoring_context`, `edit_proposal_item`, `generate_authoring_proposal`, `list_proposals`, `persist_authoring_proposal`, `reject_items`
- [[Reference/Modules/learnloop/content/authoring/practice_generation|learnloop.content.authoring.practice_generation]] — imports `generate_authoring_proposal`; statically calls `generate_authoring_proposal`
- [[Reference/Modules/learnloop/content/authoring/rung_variants|learnloop.content.authoring.rung_variants]] — imports `accept_items`, `generate_authoring_proposal`; statically calls `accept_items`, `generate_authoring_proposal`
- [[Reference/Modules/learnloop/content/pipeline/add_source|learnloop.content.pipeline.add_source]] — imports `reject_items`; statically calls `reject_items`
- [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]] — imports `accept_items`; statically calls `accept_items`
- [[Reference/Modules/learnloop/content/pipeline/source_ingestion|learnloop.content.pipeline.source_ingestion]] — imports `auto_apply_rows`, `proposal_item_row`; statically calls `auto_apply_rows`, `proposal_item_row`
- [[Reference/Modules/learnloop/curriculum/graph_edit_proposals|learnloop.curriculum.graph_edit_proposals]] — imports `auto_apply_rows`, `proposal_item_row`; statically calls `auto_apply_rows`, `proposal_item_row`
- [[Reference/Modules/learnloop/followup_run/jobs|learnloop.followup_run.jobs]] — imports `accept_items`; statically calls `accept_items`
- [[Reference/Modules/learnloop/tutor/promotions|learnloop.tutor.promotions]] — imports `generate_authoring_proposal`; statically calls `generate_authoring_proposal`
- [[Reference/Modules/learnloop_sidecar/handlers/feedback|learnloop_sidecar.handlers.feedback]] — imports `accept_items`; statically calls `accept_items`
- [[Reference/Modules/learnloop_sidecar/handlers/proposals|learnloop_sidecar.handlers.proposals]] — imports `accept_items`, `delete_proposal_item`, `edit_proposal_item`, `refresh_proposal_item_validation`, `reject_items`, `reset_items`; statically calls `accept_items`, `delete_proposal_item`, `edit_proposal_item`, `refresh_proposal_item_validation`, `reject_items`, `reset_items`
- [[Reference/Modules/learnloop_sidecar/handlers/queue|learnloop_sidecar.handlers.queue]] — imports `queue_accepted_diagnostic_followups`; statically calls `queue_accepted_diagnostic_followups`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/client|learnloop.ai.client]] — imports `AIProviderClient`
- [[Reference/Modules/learnloop/ai/errors|learnloop.ai.errors]] — imports `CodexInterrupted`, `CodexTurnTimeout`, `CodexUnavailable`
- [[Reference/Modules/learnloop/ai/runs|learnloop.ai.runs]] — imports `finish_agent_run`; calls `finish_agent_run`
- [[Reference/Modules/learnloop/ai/strict_schema|learnloop.ai.strict_schema]] — imports `strict_output_schema`; calls `strict_output_schema`
- [[Reference/Modules/learnloop/ai/transport|learnloop.ai.transport]] — imports `execute_structured_operation`; calls `execute_structured_operation`
- [[Reference/Modules/learnloop/ai/usage|learnloop.ai.usage]] — imports `consume_client_usage`; calls `consume_client_usage`
- [[Reference/Modules/learnloop/attempt_types|learnloop.attempt_types]] — imports `unsupported_attempt_types`; calls `unsupported_attempt_types`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/content/authoring/authoring_gates|learnloop.content.authoring.authoring_gates]] — imports `selected_response_reasons`; calls `selected_response_reasons`
- [[Reference/Modules/learnloop/content/authoring/persona_gate|learnloop.content.authoring.persona_gate]] — imports `GateDecision`, `PersonaGate`; calls `PersonaGate`
- [[Reference/Modules/learnloop/content/proposals/ai_contracts|learnloop.content.proposals.ai_contracts]] — imports `AUTHORING_PROMPT_VERSION`, `AuthoringContext`, `AuthoringProposal`, `AuthoringProposalItem`, `DIAGNOSTIC_AUTHORING_PROMPT`, `DIAGNOSTIC_AUTHORING_PROMPT_VERSION`, `ProposalItemAudit`, `SourceRef`, `authoring_prompt`; calls `AuthoringContext`, `authoring_prompt`
- [[Reference/Modules/learnloop/content/proposals/patches|learnloop.content.proposals.patches]] — imports `PatchApplyResult`, `apply_accepted_items`, `reject_applied_items`; calls `apply_accepted_items`, `reject_applied_items`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `MisconceptionRecord`, `Repository`
- [[Reference/Modules/learnloop/diagnosis/diagnostic_gate|learnloop.diagnosis.diagnostic_gate]] — imports `GateResult`, `run_discrimination_gate`; calls `run_discrimination_gate`
- [[Reference/Modules/learnloop/diagnosis/missing_vocabulary|learnloop.diagnosis.missing_vocabulary]] — imports `record_authoring_facet_abstention_notes`; calls `record_authoring_facet_abstention_notes`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`, `snake_case`; calls `new_ulid`, `snake_case`
- [[Reference/Modules/learnloop/vault/loader|learnloop.vault.loader]] — imports `load_vault`; calls `load_vault`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `CAPABILITY_VOCABULARY`, `LoadedVault`, `PracticeItem`, `learning_object_facet_union`; calls `learning_object_facet_union`
- [[Reference/Modules/learnloop/vault/paths|learnloop.vault.paths]] — imports `VaultPaths`; calls `VaultPaths`
- [[Reference/Modules/learnloop/vault/repository|learnloop.vault.repository]] — imports `vault_repository`; calls `vault_repository`
- [[Reference/Modules/learnloop/vault/required_method|learnloop.vault.required_method]] — imports `is_source_statement`, `learning_object_method_targets`, `method_targets`, `normalize_required_method`, `rewrites_decided_statement`, `same_statement`; calls `is_source_statement`, `learning_object_method_targets`, `method_targets`, `normalize_required_method`, `rewrites_decided_statement`, `same_statement`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `hashlib`, `json`, `math`, `pathlib`, `typing`
- Third party: `pydantic`

## Larger workflow participation

Use this module in context through:

- [[Import Canonical Sources]]
- [[Build a Study Map]]

Static participation evidence comes from [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]], [[Reference/Modules/learnloop/cli/runtime|learnloop.cli.runtime]], [[Reference/Modules/learnloop/content/authoring/practice_generation|learnloop.content.authoring.practice_generation]], [[Reference/Modules/learnloop/content/authoring/rung_variants|learnloop.content.authoring.rung_variants]], [[Reference/Modules/learnloop/content/pipeline/add_source|learnloop.content.pipeline.add_source]] and 8 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/ad23_contract_helpers.py](../../../../../../../tests/ad23_contract_helpers.py) — direct import
- [tests/test_ad23_contract.py](../../../../../../../tests/test_ad23_contract.py) — direct import
  - `test_a_commissioned_repair_after_protection_changed_mid_call_is_refused`
- [tests/test_agent_runs.py](../../../../../../../tests/test_agent_runs.py) — direct import
  - `test_generate_authoring_proposal_with_fake_client_has_lineage`
  - `test_persist_authoring_proposal_records_agent_run`
- [tests/test_authoring_context.py](../../../../../../../tests/test_authoring_context.py) — direct import
  - `test_authoring_context_carries_focus_concepts_and_facets`
  - `test_authoring_context_filters_by_subject`
  - `test_authoring_context_includes_blueprint_facets_before_items_exist`
  - `test_authoring_context_includes_explicit_source_refs`
  - `test_authoring_context_is_deterministic_and_hashable`
  - `test_authoring_context_stats_report_request_size`
- [tests/test_authoring_contract.py](../../../../../../../tests/test_authoring_contract.py) — direct import
  - `test_misconception_answer_with_keyed_fatal_error_is_valid`
  - `test_misconception_answer_without_keyed_fatal_error_is_invalid`
  - `test_no_misconception_answer_owes_nothing`
  - `test_refresh_door_never_remediates`
  - `test_refresh_door_passes_the_remediated_payload`
  - `test_refresh_door_reports_the_same_errors_as_the_generation_door`
- [tests/test_cli_generate_practice.py](../../../../../../../tests/test_cli_generate_practice.py) — direct import
  - `test_accepting_diagnostic_proposal_queues_today_followup`
- [tests/test_codex_output_schema.py](../../../../../../../tests/test_codex_output_schema.py) — direct import
  - `test_sdk_authoring_path_passes_strict_schema_to_codex`
- [tests/test_conjunctive_instruments.py](../../../../../../../tests/test_conjunctive_instruments.py) — direct import
- [tests/test_diagnostic_generation.py](../../../../../../../tests/test_diagnostic_generation.py) — direct import
  - `test_generate_diagnostic_accepted_and_reviewed`
  - `test_generate_diagnostic_gate_failure_reopens_need`
- [tests/test_diagnostic_review_policy.py](../../../../../../../tests/test_diagnostic_review_policy.py) — direct import
  - `test_context_none_unchanged`
  - `test_hard_error_missing_consistent_answer`
  - `test_hard_error_no_keyed_fatal`
  - `test_hard_error_surface_family_matches_source`
  - `test_missing_context_is_hard_error`
  - `test_soft_warnings_footprint`
  - `test_valid_diagnostic_reviews`
- [tests/test_doctor.py](../../../../../../../tests/test_doctor.py) — direct import
  - `test_doctor_warns_on_duplicate_diagnostic_practice_proposals`
- [tests/test_e2e_codex_mock.py](../../../../../../../tests/test_e2e_codex_mock.py) — direct import
  - `test_codex_mocked_end_to_end`
- [tests/test_exercise_authoring.py](../../../../../../../tests/test_exercise_authoring.py) — direct import
  - `test_missing_weights_are_not_uniformly_backfilled_and_smears_are_flagged`
- [tests/test_followup_generate_e2e.py](../../../../../../../tests/test_followup_generate_e2e.py) — direct import
  - `test_a_recorded_need_fills_textbook_first_without_a_click`
- [tests/test_ingest_runner.py](../../../../../../../tests/test_ingest_runner.py) — direct import
  - `test_goal_population_handler_generates_and_applies_practice`
- [tests/test_method_phrasing_report.py](../../../../../../../tests/test_method_phrasing_report.py) — direct import
  - `test_f3_a_repair_refuses_a_rubric_edited_before_acceptance`
  - `test_f3_an_accepted_repair_writes_no_proposal_only_key`
  - `test_f5_the_required_methods_own_criteria_are_never_ledgered_as_verdicts`
  - `test_repairs_are_pending_proposals_applied_only_on_accept`
- [tests/test_patch_applier.py](../../../../../../../tests/test_patch_applier.py) — direct import
  - `test_reject_accepted_concept_create_blocks_when_referenced`
  - `test_reject_accepted_concept_create_removes_concept`
  - `test_reject_proposal_item_does_not_mutate_yaml`
- [tests/test_proposal_persistence.py](../../../../../../../tests/test_proposal_persistence.py) — direct import
  - `test_accept_learning_object_create_adds_missing_concept_for_graph`
  - `test_ai_proposal_acceptance_records_ai_origin`
  - `test_auto_apply_batches_dependency_order_for_new_lo_and_practice_item`
  - `test_canonical_source_refs_flow_into_learning_object_provenance`
  - `test_create_payload_missing_required_fields_is_invalid`
  - `test_edit_proposal_item_updates_payload_and_refreshes_duplicate_validation`
  - `test_failed_repair_call_keeps_original_invalid_item`
  - `test_generate_persists_one_item_per_proposal_item`
  - `test_generated_item_local_criterion_may_honestly_omit_facets`
  - `test_generated_practice_missing_evidence_facets_is_invalid`
  - `test_generated_practice_missing_evidence_weights_is_not_smeared`
  - `test_generated_practice_missing_reward_metadata_is_invalid`
  - `test_generated_practice_rejects_unknown_metadata_keys`
  - `test_generated_practice_rubric_criterion_total_defines_grading_scale`
  - `test_generated_practice_single_facet_backfills_criterion_facet_weights`
  - `test_invalid_concept_edge_proposal_is_persisted_invalid`
  - `test_invalid_generated_item_gets_one_repair_round_trip`
  - `test_manual_practice_missing_evidence_weights_is_warning`
  - `test_practice_item_without_resolved_rubric_is_invalid_until_edited`
  - `test_registry_backed_vault_rejects_unknown_evidence_facet`
  - `test_reject_route_item_is_persisted_invalid_and_not_applied`
  - `test_source_grounded_auto_apply_accepts_low_risk_create`
  - `test_source_linked_generated_practice_missing_audit_is_invalid`
  - `test_source_linked_generated_practice_with_passed_audit_auto_applies`
  - `test_timed_out_repair_fails_without_persisting_first_pass`
  - `test_unresolved_source_ref_is_persisted_invalid`
  - `test_update_learning_object_proposal_preserves_existing_required_fields`
  - `test_update_practice_item_proposal_preserves_existing_learning_object`
  - `test_valid_proposal_skips_repair_round_trip`
- [tests/test_proposal_review_policy.py](../../../../../../../tests/test_proposal_review_policy.py) — direct import
  - `test_concept_changes_are_not_auto_applied`
  - `test_generated_practice_item_failed_audit_requires_review`
  - `test_generated_practice_item_missing_audit_requires_review`
  - `test_generated_practice_item_passed_audit_can_auto_apply`
  - `test_id_collision_requires_review`
  - `test_low_risk_create_can_auto_apply`
  - `test_manual_context_auto_apply_route_still_requires_review`
  - `test_missing_source_refs_requires_review`
  - `test_modification_requires_review`
  - `test_reject_route_stays_reject`
  - `test_source_grounded_existing_concept_edge_can_auto_apply`
- [tests/test_required_method_authority.py](../../../../../../../tests/test_required_method_authority.py) — direct import
  - `test_a_generated_proposal_never_changes_a_source_items_field`
  - `test_the_owner_override_on_a_generated_item_changes_only_the_field`
  - `test_the_owner_overrides_a_source_decision_and_clears_it_through_proposals`
- [tests/test_required_method_items.py](../../../../../../../tests/test_required_method_items.py) — direct import
  - `test_an_authoring_proposal_keeps_a_required_method_only_on_a_method_target`
  - `test_the_authoring_context_names_method_targets_only_where_they_are`
- [tests/test_required_method_reopened.py](../../../../../../../tests/test_required_method_reopened.py) — direct import
  - `test_f15_a_generated_items_new_prompt_is_stored_as_generated`
  - `test_f15_a_generated_update_renaming_the_method_changes_only_the_field`
  - `test_f15_a_generated_update_that_rewrites_a_judged_source_statement_is_refused`
  - `test_f15_a_whitespace_only_restatement_keeps_the_verbatim_statement_and_applies`
  - `test_f15_an_owner_edit_of_a_pending_update_cannot_rewrite_the_statement_either`
  - `test_f16_a_generated_items_override_is_ledgered_and_the_write_is_idempotent`
  - `test_f16_a_generated_update_is_no_owner_verdict`
  - `test_f16_an_accepted_override_appends_the_owners_verdict_superseding_the_judgment`
- [tests/test_required_method_round3.py](../../../../../../../tests/test_required_method_round3.py) — direct import
  - `test_f14_a_generated_update_quoting_the_sentence_is_stored_verbatim_and_the_block_rendered`
  - `test_f21_clearing_or_renaming_never_edits_the_statement`
- [tests/test_required_method_round3_review.py](../../../../../../../tests/test_required_method_round3_review.py) — direct import
- [tests/test_show.py](../../../../../../../tests/test_show.py) — direct import
  - `test_show_inspects_every_deterministic_id`
- [tests/test_source_ingestion.py](../../../../../../../tests/test_source_ingestion.py) — direct import
  - `test_composite_note_id_locator_source_ref_resolves`
  - `test_regrounded_update_clears_active_source_span_events`
  - `test_reject_auto_applied_ingest_items_deactivates_created_entities`
  - `test_section_level_source_ref_resolves_to_child_chunks`
  - `test_youtube_missing_source_ref_accepts_registered_note_timecoded_id`
  - `test_youtube_missing_source_ref_is_reconstructed_from_timecoded_id`
  - `test_youtube_missing_source_ref_without_timecoded_id_stays_invalid`
  - `test_youtube_time_range_source_refs_can_span_caption_cues`
- [tests/test_structured_transport_parity.py](../../../../../../../tests/test_structured_transport_parity.py) — direct import
- [tests/test_teach_back_generation.py](../../../../../../../tests/test_teach_back_generation.py) — direct import
  - `test_rubric_errors_reject_bad_tier_value`
  - `test_teach_back_item_missing_core_criterion_for_facet_is_invalid`
  - `test_teach_back_item_with_unmapped_criterion_is_invalid`
  - `test_teach_back_item_without_rubric_is_invalid_despite_default_rubrics`
  - `test_well_formed_teach_back_item_is_valid`
- [tests/test_tutor_promotion_service.py](../../../../../../../tests/test_tutor_promotion_service.py) — direct import
  - `test_accepting_reviewed_promotion_makes_original_request_schedulable`
  - `test_rejecting_and_resetting_review_updates_promotion_request_state`
- [tests/test_ux_phase2_error_type_proposals.py](../../../../../../../tests/test_ux_phase2_error_type_proposals.py) — direct import

## Modification guidance

- Change proposals policy here when content owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/content/proposals/proposals.py](../../../../../../../src/learnloop/content/proposals/proposals.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

---
title: "learnloop.content.synthesis.source_append"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/content/synthesis/source_append.py"
source_paths:
  - "src/learnloop/content/synthesis/source_append.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop.content.synthesis"
layer: "domain"
concepts:
  - "Learning System"
  - "AI Architecture"
workflows:
  - "Import Canonical Sources"
  - "Build a Study Map"
aliases:
  - "learnloop.content.synthesis.source_append module"
  - "src/learnloop/content/synthesis/source_append.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-content-synthesis"
---

# `learnloop.content.synthesis.source_append`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/content/synthesis/_package|learnloop.content.synthesis]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.content.synthesis.source_append` exists within [[Reference/Modules/learnloop/content/synthesis/_package|learnloop.content.synthesis]] to own the behavior summarized by its module contract: Append reconciliation: safe increments to an existing study map (ING M7, §10).

The authoritative system-level explanation remains in [[Learning System]], [[AI Architecture]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/content/synthesis/source_append.py](../../../../../../../src/learnloop/content/synthesis/source_append.py) |
| Source lines | 674 |
| Owning package | [[Reference/Modules/learnloop/content/synthesis/_package|learnloop.content.synthesis]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `request_append_reconciliation(client: StructuredTransport, context: AppendReconciliationContext) -> AppendReconciliation` ([source](../../../../../../../src/learnloop/content/synthesis/source_append.py), line 70) — Reconcile one bounded append context through the shared transport.
- `subject_has_applied_study_map(vault: LoadedVault, subject_id: str) -> bool` ([source](../../../../../../../src/learnloop/content/synthesis/source_append.py), line 83) — The bootstrap-vs-append discriminator (§8/§10).
- `class AppendResult` ([source](../../../../../../../src/learnloop/content/synthesis/source_append.py), line 100)
  - `as_dict(self) -> dict[str, Any]` (line 117; public)
- `append_source(root: Path, source_set_id: str, *, client: Any, new_revision_ids: list[str] | None=None, change_kind: str='source_added', revision_diff: dict[str, Any] | None=None, brief: dict[str, Any] | None=None, auto_apply: bool=True, repository: Repository | None=None, clock: Clock | None=None, budget_overrides: dict[str, int] | None=None, unlimited_token_budget: bool=False) -> AppendResult` ([source](../../../../../../../src/learnloop/content/synthesis/source_append.py), line 140) — Run bounded append reconciliation and (by policy) auto-apply routine items.

### Module constants

- `APPEND_AGENT_PURPOSE` ([src/learnloop/content/synthesis/source_append.py](../../../../../../../src/learnloop/content/synthesis/source_append.py), line 66)
- `APPEND_PROPOSAL_PURPOSE` ([src/learnloop/content/synthesis/source_append.py](../../../../../../../src/learnloop/content/synthesis/source_append.py), line 67)
- `_AUTO_APPLY_RELATIONS` ([src/learnloop/content/synthesis/source_append.py](../../../../../../../src/learnloop/content/synthesis/source_append.py), line 96)

## Internal implementation anchors

- `_append(vault: LoadedVault, repository: Repository, root: Path, source_set_id: str, *, client: Any, new_revision_ids: list[str] | None, change_kind: str, revision_diff: dict[str, Any], brief: dict[str, Any], auto_apply: bool, clock: Clock | None, budget_overrides: dict[str, int] | None=None, unlimited_token_budget: bool=False) -> AppendResult` ([source](../../../../../../../src/learnloop/content/synthesis/source_append.py), line 170)
- `_run_reconciliation(client, repository, inputs, new_inventories, neighborhood, source_set, subject_id, change_kind, revision_diff, brief, budgets, *, clock, unlimited_token_budget: bool=False)` ([source](../../../../../../../src/learnloop/content/synthesis/source_append.py), line 413)
- `_output_tokens(result: Any) -> int` ([source](../../../../../../../src/learnloop/content/synthesis/source_append.py), line 446)
- `_normalize_append(reconciliation, inputs, vault, neighborhood, now, *, subject_id, items_off: bool=False)` ([source](../../../../../../../src/learnloop/content/synthesis/source_append.py), line 456) — Map an AppendReconciliation to proposal rows + gate items + auto-apply ids.
- `_relation_for_intent(intent: str | None) -> str` ([source](../../../../../../../src/learnloop/content/synthesis/source_append.py), line 591)
- `_hash_type(target_type: str) -> str` ([source](../../../../../../../src/learnloop/content/synthesis/source_append.py), line 599)
- `_target_type(target_type: str) -> str` ([source](../../../../../../../src/learnloop/content/synthesis/source_append.py), line 603)
- `_auto_applies(payload, gate_refs, vault, current_hash, target_type) -> bool` ([source](../../../../../../../src/learnloop/content/synthesis/source_append.py), line 609) — §10.3 auto-apply predicate for a provenance_link.
- `_span_yaml(span, inputs) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/synthesis/source_append.py), line 639)
- `_count(rows) -> dict[str, int]` ([source](../../../../../../../src/learnloop/content/synthesis/source_append.py), line 646)
- `_snapshot(repository: Repository, vault: LoadedVault) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/synthesis/source_append.py), line 656)
- `_link_count(repository: Repository) -> int` ([source](../../../../../../../src/learnloop/content/synthesis/source_append.py), line 666)
- `_diff_from_snapshot(repository, vault_after, before, patch_id) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/synthesis/source_append.py), line 671)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]] — imports `append_source`; statically calls `append_source`
- [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]] — imports `append_source`, `subject_has_applied_study_map`; statically calls `append_source`, `subject_has_applied_study_map`
- [[Reference/Modules/learnloop/content/pipeline/revision_refresh|learnloop.content.pipeline.revision_refresh]] — imports `append_source`; statically calls `append_source`
- [[Reference/Modules/learnloop_sidecar/handlers/ingest|learnloop_sidecar.handlers.ingest]] — imports `append_source`, `subject_has_applied_study_map`; statically calls `append_source`, `subject_has_applied_study_map`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/runs|learnloop.ai.runs]] — imports `finish_agent_run`; calls `finish_agent_run`
- [[Reference/Modules/learnloop/ai/transport|learnloop.ai.transport]] — imports `StructuredTransport`, `execute_structured_operation`; calls `execute_structured_operation`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/content/authoring/authoring_gates|learnloop.content.authoring.authoring_gates]] — imports `build_instrument_gates`; calls `build_instrument_gates`
- [[Reference/Modules/learnloop/content/proposals/patches|learnloop.content.proposals.patches]] — imports `apply_accepted_items`, `compute_target_hash`; calls `apply_accepted_items`, `compute_target_hash`
- [[Reference/Modules/learnloop/content/synthesis/ai_contracts|learnloop.content.synthesis.ai_contracts]] — imports `APPEND_RECONCILIATION_PROMPT_VERSION`, `AppendReconciliation`, `AppendReconciliationContext`, `SourceSetSynthesis`, `SynthSpanRef`, `append_reconciliation_prompt`; calls `AppendReconciliationContext`, `SourceSetSynthesis`, `append_reconciliation_prompt`
- [[Reference/Modules/learnloop/content/synthesis/append_neighborhood|learnloop.content.synthesis.append_neighborhood]] — imports `Neighborhood`, `select_neighborhood`; calls `select_neighborhood`
- [[Reference/Modules/learnloop/content/synthesis/facet_doctor|learnloop.content.synthesis.facet_doctor]] — imports `near_duplicate_facet_review`; calls `near_duplicate_facet_review`
- [[Reference/Modules/learnloop/content/synthesis/source_set_synthesis|learnloop.content.synthesis.source_set_synthesis]] — imports `StudyMapError`, `_collect_inputs`, `_gate_context`, `_normalize`, `_resolve_span_requests`, `_row`, `_span_refs`; calls `StudyMapError`, `_collect_inputs`, `_gate_context`, `_normalize`, `_resolve_span_requests`, `_row`, `_span_refs`
- [[Reference/Modules/learnloop/content/synthesis/study_map_diff|learnloop.content.synthesis.study_map_diff]] — imports `compute_study_map_diff`; calls `compute_study_map_diff`
- [[Reference/Modules/learnloop/content/synthesis/synthesis_gates|learnloop.content.synthesis.synthesis_gates]] — imports `GateItem`, `GateProposal`, `ProvenanceRef`, `run_synthesis_gates`; calls `GateItem`, `GateProposal`, `run_synthesis_gates`
- [[Reference/Modules/learnloop/content/synthesis/synthesis_manifests|learnloop.content.synthesis.synthesis_manifests]] — imports `agent_run_input_context_hash`, `build_manifest`, `persist_manifest`; calls `agent_run_input_context_hash`, `build_manifest`, `persist_manifest`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`; calls `Repository`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/vault/loader|learnloop.vault.loader]] — imports `load_vault`; calls `load_vault`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`, `SourceSet`
- [[Reference/Modules/learnloop/vault/paths|learnloop.vault.paths]] — imports `VaultPaths`; calls `VaultPaths`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `json`, `pathlib`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Import Canonical Sources]]
- [[Build a Study Map]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]], [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]], [[Reference/Modules/learnloop/content/pipeline/revision_refresh|learnloop.content.pipeline.revision_refresh]], [[Reference/Modules/learnloop_sidecar/handlers/ingest|learnloop_sidecar.handlers.ingest]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_build_study_map_routing.py](../../../../../../../tests/test_build_study_map_routing.py) — direct import
  - `test_helper_detects_applied_study_map`
- [tests/test_ingest_instrument_gates.py](../../../../../../../tests/test_ingest_instrument_gates.py) — direct import
  - `test_append_authors_items_when_upfront`
  - `test_append_respects_items_off`
- [tests/test_source_append.py](../../../../../../../tests/test_source_append.py) — direct import
  - `test_append_budget_overrides_reach_the_manifest`
  - `test_append_provenance_link_auto_applies_without_rewriting_lo_yaml`
  - `test_append_vocabulary_auto_apply_rules`
  - `test_conflict_accept_creates_open_row_reject_creates_none`
  - `test_conflict_reject_creates_no_row`
  - `test_n_sources_append_linear_inventory_and_bounded_context`
  - `test_narrow_adjunct_deterministically_drops_model_restructures`
  - `test_post_append_near_duplicate_is_aliased_at_mint_and_never_auto_merged`
  - `test_replay_identical_after_append_apply`
  - `test_specialized_side_effects_recover_idempotently`
  - `test_study_map_diff_reports_changes`
- [tests/test_structured_transport_parity.py](../../../../../../../tests/test_structured_transport_parity.py) — direct import

## Modification guidance

- Change source append policy here when content owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/content/synthesis/source_append.py](../../../../../../../src/learnloop/content/synthesis/source_append.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

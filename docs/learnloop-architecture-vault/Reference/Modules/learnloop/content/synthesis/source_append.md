---
title: "learnloop.content.synthesis.source_append"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/content/synthesis/source_append.py"
source_paths:
  - "src/learnloop/content/synthesis/source_append.py"
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
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/content/synthesis/_package|learnloop.content.synthesis]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.content.synthesis.source_append` exists within [[Reference/Modules/learnloop/content/synthesis/_package|learnloop.content.synthesis]] to own the behavior summarized by its module contract: Append reconciliation: safe increments to an existing study map (ING M7, §10).

The authoritative system-level explanation remains in [[Learning System]], [[AI Architecture]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/content/synthesis/source_append.py](../../../../../../../src/learnloop/content/synthesis/source_append.py) |
| Source lines | 1117 |
| Owning package | [[Reference/Modules/learnloop/content/synthesis/_package|learnloop.content.synthesis]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `request_append_reconciliation(client: StructuredTransport, context: AppendReconciliationContext) -> AppendReconciliation` ([source](../../../../../../../src/learnloop/content/synthesis/source_append.py), line 83) — Reconcile one bounded append context through the shared transport.
- `select_new_inventories(entries: list[dict[str, Any]], revision_ids: Collection[str], new_unit_ids: Mapping[str, Sequence[str]] | None) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/content/synthesis/source_append.py), line 96) — The inventory entries an append sends as new.
- `append_scope(vault: LoadedVault, *, change_kind: str, revision_ids: Collection[str], neighborhood: dict[str, Any], new_unit_ids: Mapping[str, Sequence[str]] | None=None, facet_identity_client: Any=None) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/synthesis/source_append.py), line 121) — The append manifest's ``scope``.
- `subject_has_applied_study_map(vault: LoadedVault, subject_id: str) -> bool` ([source](../../../../../../../src/learnloop/content/synthesis/source_append.py), line 151) — The bootstrap-vs-append discriminator (§8/§10).
- `class AppendResult` ([source](../../../../../../../src/learnloop/content/synthesis/source_append.py), line 168)
  - `as_dict(self) -> dict[str, Any]` (line 187; public)
- `append_source(root: Path, source_set_id: str, *, client: Any, new_revision_ids: list[str] | None=None, new_unit_ids: Mapping[str, Sequence[str]] | None=None, change_kind: str='source_added', revision_diff: dict[str, Any] | None=None, brief: dict[str, Any] | None=None, auto_apply: bool=True, repository: Repository | None=None, clock: Clock | None=None, budget_overrides: dict[str, int] | None=None, unlimited_token_budget: bool=False, embedding_client_factory: Callable[[], Any] | None=None, facet_identity_client: Any=None, apply_gate: Callable[[], bool] | None=None) -> AppendResult` ([source](../../../../../../../src/learnloop/content/synthesis/source_append.py), line 211) — Run bounded append reconciliation and (by policy) auto-apply routine items.
- `plan_append_embedding(root: Path, source_set_id: str, *, new_revision_ids: list[str] | None=None, new_unit_ids: Mapping[str, Sequence[str]] | None=None) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/synthesis/source_append.py), line 254) — Dry run of one append's Slice 2 T5 embedding spend.

### Module constants

- `APPEND_AGENT_PURPOSE` ([src/learnloop/content/synthesis/source_append.py](../../../../../../../src/learnloop/content/synthesis/source_append.py), line 79)
- `APPEND_PROPOSAL_PURPOSE` ([src/learnloop/content/synthesis/source_append.py](../../../../../../../src/learnloop/content/synthesis/source_append.py), line 80)
- `_AUTO_APPLY_RELATIONS` ([src/learnloop/content/synthesis/source_append.py](../../../../../../../src/learnloop/content/synthesis/source_append.py), line 164)

## Internal implementation anchors

- `_append(vault: LoadedVault, repository: Repository, root: Path, source_set_id: str, *, client: Any, new_revision_ids: list[str] | None, change_kind: str, revision_diff: dict[str, Any], new_unit_ids: Mapping[str, Sequence[str]] | None=None, brief: dict[str, Any], auto_apply: bool, clock: Clock | None, budget_overrides: dict[str, int] | None=None, unlimited_token_budget: bool=False, embedding_client_factory: Callable[[], Any] | None=None, facet_identity_client: Any=None, apply_gate: Callable[[], bool] | None=None) -> AppendResult` ([source](../../../../../../../src/learnloop/content/synthesis/source_append.py), line 282)
- `_run_reconciliation(client, repository, inputs, new_inventories, neighborhood, source_set, subject_id, change_kind, revision_diff, brief, budgets, *, clock, unlimited_token_budget: bool=False, one_facet_per_skill: bool=False)` ([source](../../../../../../../src/learnloop/content/synthesis/source_append.py), line 585)
- `_output_tokens(result: Any) -> int` ([source](../../../../../../../src/learnloop/content/synthesis/source_append.py), line 620)
- `_normalize_append(reconciliation, inputs, vault, neighborhood, now, *, subject_id, items_off: bool=False, nominator=None, facet_identity_plan=None)` ([source](../../../../../../../src/learnloop/content/synthesis/source_append.py), line 630) — Map an AppendReconciliation to proposal rows + gate items + auto-apply ids.
- `class _FacetReword` ([source](../../../../../../../src/learnloop/content/synthesis/source_append.py), line 857) — A facet restructure, normalized: its proposal payload and the citations the gates judge.
- `_facet_reword(obj: dict[str, Any], vault: LoadedVault, inputs: Any, operation: str, target_id: str) -> _FacetReword` ([source](../../../../../../../src/learnloop/content/synthesis/source_append.py), line 874) — Normalize a facet restructure: a reword of a registered facet.
- `_checked_reword(target_id: str, current: dict[str, Any], payload: dict[str, Any], gate_refs: list[ProvenanceRef], support: Any, unresolved: list[str], inputs: Any, policy: facet_meaning.MeaningPolicy=facet_meaning.REWORD_CONFIRM) -> _FacetReword` ([source](../../../../../../../src/learnloop/content/synthesis/source_append.py), line 984) — A reword, judged in advance by the chokepoint the apply runs again.
- `_span_problem(span: dict[str, Any], inputs) -> str | None` ([source](../../../../../../../src/learnloop/content/synthesis/source_append.py), line 1019) — Why a cited span cannot attach, or None when it can.
- `_relation_for_intent(intent: str | None) -> str` ([source](../../../../../../../src/learnloop/content/synthesis/source_append.py), line 1034)
- `_hash_type(target_type: str) -> str` ([source](../../../../../../../src/learnloop/content/synthesis/source_append.py), line 1042)
- `_target_type(target_type: str) -> str` ([source](../../../../../../../src/learnloop/content/synthesis/source_append.py), line 1046)
- `_auto_applies(payload, gate_refs, vault, current_hash, target_type) -> bool` ([source](../../../../../../../src/learnloop/content/synthesis/source_append.py), line 1052) — §10.3 auto-apply predicate for a provenance_link.
- `_span_yaml(span, inputs) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/synthesis/source_append.py), line 1082)
- `_count(rows) -> dict[str, int]` ([source](../../../../../../../src/learnloop/content/synthesis/source_append.py), line 1089)
- `_snapshot(repository: Repository, vault: LoadedVault) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/synthesis/source_append.py), line 1099)
- `_link_count(repository: Repository) -> int` ([source](../../../../../../../src/learnloop/content/synthesis/source_append.py), line 1109)
- `_diff_from_snapshot(repository, vault_after, before, patch_id) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/synthesis/source_append.py), line 1114)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]] — imports `append_source`, `plan_append_embedding`; statically calls `append_source`, `plan_append_embedding`
- [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]] — imports `append_source`, `subject_has_applied_study_map`; statically calls `append_source`, `subject_has_applied_study_map`
- [[Reference/Modules/learnloop/content/pipeline/revision_refresh|learnloop.content.pipeline.revision_refresh]] — imports `append_source`; statically calls `append_source`
- [[Reference/Modules/learnloop_sidecar/handlers/ingest|learnloop_sidecar.handlers.ingest]] — imports `append_source`, `subject_has_applied_study_map`; statically calls `append_source`, `subject_has_applied_study_map`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/runs|learnloop.ai.runs]] — imports `finish_agent_run`; calls `finish_agent_run`
- [[Reference/Modules/learnloop/ai/transport|learnloop.ai.transport]] — imports `StructuredTransport`, `execute_structured_operation`; calls `execute_structured_operation`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/content/authoring/authoring_gates|learnloop.content.authoring.authoring_gates]] — imports `build_instrument_gates`; calls `build_instrument_gates`
- [[Reference/Modules/learnloop/content/facet_identity/actions|learnloop.content.facet_identity.actions]] — imports `record_proposed_actions`; calls `record_proposed_actions`
- [[Reference/Modules/learnloop/content/facet_identity/authority|learnloop.content.facet_identity.authority]] — imports `module`; calls `authority_changes`, `check_meaning_write`, `contributions`, `meaning_policy`, `overlay`, `support_entries`
- [[Reference/Modules/learnloop/content/facet_identity/judge|learnloop.content.facet_identity.judge]] — imports `manifest_identity`; calls `manifest_identity`
- [[Reference/Modules/learnloop/content/facet_identity/plan|learnloop.content.facet_identity.plan]] — imports `ingest_dry_run`; calls `ingest_dry_run`
- [[Reference/Modules/learnloop/content/proposals/patches|learnloop.content.proposals.patches]] — imports `apply_accepted_items`, `compute_target_hash`; calls `apply_accepted_items`, `compute_target_hash`
- [[Reference/Modules/learnloop/content/synthesis/ai_contracts|learnloop.content.synthesis.ai_contracts]] — imports `AppendReconciliation`, `AppendReconciliationContext`, `SourceSetSynthesis`, `append_reconciliation_prompt`, `append_reconciliation_prompt_version`; calls `AppendReconciliationContext`, `SourceSetSynthesis`, `append_reconciliation_prompt`, `append_reconciliation_prompt_version`
- [[Reference/Modules/learnloop/content/synthesis/append_neighborhood|learnloop.content.synthesis.append_neighborhood]] — imports `select_neighborhood`; calls `select_neighborhood`
- [[Reference/Modules/learnloop/content/synthesis/facet_doctor|learnloop.content.synthesis.facet_doctor]] — imports `near_duplicate_facet_review`; calls `near_duplicate_facet_review`
- [[Reference/Modules/learnloop/content/synthesis/graph_nomination|learnloop.content.synthesis.graph_nomination]] — imports `GraphNominator`, `plan_ingest_embedding`; calls `plan_ingest_embedding`
- [[Reference/Modules/learnloop/content/synthesis/source_set_synthesis|learnloop.content.synthesis.source_set_synthesis]] — imports `StudyMapError`, `_collect_inputs`, `_facet_identity_plan`, `_gate_context`, `_normalize`, `_resolve_span_requests`, `_row`, `_span_refs`, `_support_citations`, `facet_identity_result`; calls `StudyMapError`, `_collect_inputs`, `_facet_identity_plan`, `_gate_context`, `_normalize`, `_resolve_span_requests`, `_row`, `_span_refs`, `_support_citations`, `facet_identity_result`
- [[Reference/Modules/learnloop/content/synthesis/study_map_diff|learnloop.content.synthesis.study_map_diff]] — imports `compute_study_map_diff`; calls `compute_study_map_diff`
- [[Reference/Modules/learnloop/content/synthesis/synthesis_gates|learnloop.content.synthesis.synthesis_gates]] — imports `ASSESSMENT_ONLY_ROLES`, `GateItem`, `GateProposal`, `ProvenanceRef`, `run_synthesis_gates`; calls `GateItem`, `GateProposal`, `run_synthesis_gates`
- [[Reference/Modules/learnloop/content/synthesis/synthesis_manifests|learnloop.content.synthesis.synthesis_manifests]] — imports `agent_run_input_context_hash`, `build_manifest`, `persist_manifest`; calls `agent_run_input_context_hash`, `build_manifest`, `persist_manifest`
- [[Reference/Modules/learnloop/content/synthesis/vault_epigraphs|learnloop.content.synthesis.vault_epigraphs]] — imports `digest_for_append`, `generate_vault_epigraphs`; calls `digest_for_append`, `generate_vault_epigraphs`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/vault/loader|learnloop.vault.loader]] — imports `load_vault`; calls `load_vault`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/vault/paths|learnloop.vault.paths]] — imports `VaultPaths`; calls `VaultPaths`
- [[Reference/Modules/learnloop/vault/repository|learnloop.vault.repository]] — imports `vault_repository`; calls `vault_repository`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `json`, `pathlib`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Import Canonical Sources]]
- [[Build a Study Map]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]], [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]], [[Reference/Modules/learnloop/content/pipeline/revision_refresh|learnloop.content.pipeline.revision_refresh]], [[Reference/Modules/learnloop_sidecar/handlers/ingest|learnloop_sidecar.handlers.ingest]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/facet_identity_ingest_helpers.py](../../../../../../../tests/facet_identity_ingest_helpers.py) — direct import
- [tests/identity_pins_helpers.py](../../../../../../../tests/identity_pins_helpers.py) — direct import
- [tests/test_build_study_map_routing.py](../../../../../../../tests/test_build_study_map_routing.py) — direct import
  - `test_helper_detects_applied_study_map`
- [tests/test_facet_authority.py](../../../../../../../tests/test_facet_authority.py) — direct import
  - `test_a_provenance_link_to_an_unselected_unit_is_dropped`
  - `test_a_reword_citing_a_span_outside_its_unit_drops_the_citation`
  - `test_an_exam_and_notes_reword_hard_fails_exam_authority`
  - `test_an_exam_override_inside_a_textbook_extraction_is_exam_material`
  - `test_an_uncited_append_facet_carrying_a_registered_id_never_rewrites_it`
  - `test_an_unselected_span_never_corroborates_exam_material`
- [tests/test_facet_identity_ingest.py](../../../../../../../tests/test_facet_identity_ingest.py) — direct import
  - `test_append_attaches_a_new_facet_to_the_registered_one_it_restates`
  - `test_the_append_dry_run_plans_the_ingest_judge`
- [tests/test_facet_reword_confirm.py](../../../../../../../tests/test_facet_reword_confirm.py) — direct import
  - `test_a_notes_cited_append_reword_reaches_the_owner_as_a_confirm`
  - `test_an_append_reword_citing_exam_material_under_the_wrong_unit_is_dropped_not_held`
  - `test_an_exam_only_append_reword_still_hard_fails`
  - `test_an_uncited_append_reword_reaches_the_owner_as_a_confirm`
- [tests/test_facet_reword_confirm_review.py](../../../../../../../tests/test_facet_reword_confirm_review.py) — direct import
  - `test_an_attach_absorbing_an_exam_span_cited_under_the_wrong_unit_never_grows_the_facet`
  - `test_with_the_kill_switch_an_uncited_absorbed_example_joins_as_an_alias_only`
  - `test_with_the_kill_switch_the_append_lane_drops_an_uncited_reword`
- [tests/test_facet_reword_paths.py](../../../../../../../tests/test_facet_reword_paths.py) — direct import
  - `test_a_cited_facet_reword_records_its_spans_in_the_facets_provenance`
  - `test_a_facet_reword_an_explanatory_span_corroborates_passes_the_gate`
  - `test_a_facet_reword_citation_that_does_not_resolve_is_dropped_not_fatal`
  - `test_an_append_facet_restructure_applies_as_a_facet_version_with_undo`
  - `test_an_append_facet_restructure_refuses_when_the_facet_changed_since`
  - `test_an_append_facet_restructure_that_cannot_apply_is_dropped_with_a_diagnostic`
  - `test_an_exam_only_facet_reword_hard_fails_the_exam_authority_gate`
  - `test_an_uncited_facet_reword_waits_for_the_owners_confirm`
- [tests/test_graph_nomination_ingest.py](../../../../../../../tests/test_graph_nomination_ingest.py) — direct import
  - `test_append_dry_run_estimates_known_queries_without_a_client`
  - `test_append_neighbourhood_records_embedding_nominations`
  - `test_identical_append_reuses_its_completed_run`
- [tests/test_ingest_instrument_gates.py](../../../../../../../tests/test_ingest_instrument_gates.py) — direct import
  - `test_append_authors_items_when_upfront`
  - `test_append_respects_items_off`
- [tests/test_keep_ahead_append_units.py](../../../../../../../tests/test_keep_ahead_append_units.py) — direct import
  - `test_the_unit_filter_applies_per_revision`
- [tests/test_retired_config_identities.py](../../../../../../../tests/test_retired_config_identities.py) — direct import
  - `test_an_append_run_completed_before_arc_c_is_reused_for_the_same_request`
  - `test_append_manifest_hashes_the_facet_identity_config_as_before_arc_c`
- [tests/test_source_append.py](../../../../../../../tests/test_source_append.py) — direct import
  - `test_append_budget_overrides_reach_the_manifest`
  - `test_append_epigraph_failure_leaves_the_append_unchanged`
  - `test_append_persists_vault_epigraphs`
  - `test_append_provenance_link_auto_applies_without_rewriting_lo_yaml`
  - `test_append_vocabulary_auto_apply_rules`
  - `test_conflict_accept_creates_open_row_reject_creates_none`
  - `test_conflict_reject_creates_no_row`
  - `test_n_sources_append_linear_inventory_and_bounded_context`
  - `test_narrow_adjunct_deterministically_drops_model_restructures`
  - `test_post_append_near_duplicate_is_aliased_at_mint_and_never_auto_merged`
  - `test_provenance_link_span_without_a_unit_id_still_resolves`
  - `test_provenance_links_without_a_resolvable_span_are_dropped_not_hard_failed`
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

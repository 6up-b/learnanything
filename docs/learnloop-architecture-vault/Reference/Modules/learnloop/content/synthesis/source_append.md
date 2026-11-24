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
| Source lines | 1310 |
| Owning package | [[Reference/Modules/learnloop/content/synthesis/_package|learnloop.content.synthesis]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `request_append_reconciliation(client: StructuredTransport, context: AppendReconciliationContext, *, receipt_checkpoint: tuple[str, int] | None=None) -> AppendReconciliation` ([source](../../../../../../../src/learnloop/content/synthesis/source_append.py), line 82) — Reconcile one bounded append context through the shared transport.
- `append_checkpoint_key(prompt: str, settings: dict[str, Any]) -> str` ([source](../../../../../../../src/learnloop/content/synthesis/source_append.py), line 102) — Model-work checkpoint identity of one append call (the first call or its span round): a bootstrap pass's key under the append's purpose.
- `select_new_inventories(entries: list[dict[str, Any]], revision_ids: Collection[str], new_unit_ids: Mapping[str, Sequence[str]] | None) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/content/synthesis/source_append.py), line 181) — The inventory entries an append sends as new.
- `units_not_yet_sent(root: Path, source_set_id: str) -> tuple[list[str], dict[str, list[str]]]` ([source](../../../../../../../src/learnloop/content/synthesis/source_append.py), line 246) — What an append that names no revision sends (the CLI's ``synthesize``): the set's units no kept synthesis of it has sent (:func:`_sent_units`), as ``(new_revision_ids, new_unit_ids)`` for :func:`append_source`.
- `append_scope(vault: LoadedVault, *, change_kind: str, revision_ids: Collection[str], neighborhood: dict[str, Any], new_unit_ids: Mapping[str, Sequence[str]] | None=None, facet_identity_client: Any=None, revision_diff: Mapping[str, Any] | None=None) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/synthesis/source_append.py), line 278) — The append manifest's ``scope``: what changed and what the append read around it.
- `subject_has_applied_study_map(vault: LoadedVault, subject_id: str) -> bool` ([source](../../../../../../../src/learnloop/content/synthesis/source_append.py), line 311) — The bootstrap-vs-append discriminator (§8/§10).
- `class AppendResult` ([source](../../../../../../../src/learnloop/content/synthesis/source_append.py), line 328)
  - `as_dict(self) -> dict[str, Any]` (line 351; public)
- `append_source(root: Path, source_set_id: str, *, client: Any, new_revision_ids: list[str] | None=None, new_unit_ids: Mapping[str, Sequence[str]] | None=None, change_kind: str='source_added', revision_diff: dict[str, Any] | None=None, brief: dict[str, Any] | None=None, auto_apply: bool=True, repository: Repository | None=None, clock: Clock | None=None, budget_overrides: dict[str, int] | None=None, unlimited_token_budget: bool=False, embedding_client_factory: Callable[[], Any] | None=None, facet_identity_client: Any=None, apply_gate: Callable[[], bool] | None=None) -> AppendResult` ([source](../../../../../../../src/learnloop/content/synthesis/source_append.py), line 376) — Run bounded append reconciliation and (by policy) auto-apply routine items.
- `plan_append_embedding(root: Path, source_set_id: str, *, new_revision_ids: list[str] | None=None, new_unit_ids: Mapping[str, Sequence[str]] | None=None) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/synthesis/source_append.py), line 419) — Dry run of one append's Slice 2 T5 embedding spend.

### Module constants

- `APPEND_AGENT_PURPOSE` ([src/learnloop/content/synthesis/source_append.py](../../../../../../../src/learnloop/content/synthesis/source_append.py), line 78)
- `APPEND_PROPOSAL_PURPOSE` ([src/learnloop/content/synthesis/source_append.py](../../../../../../../src/learnloop/content/synthesis/source_append.py), line 79)
- `APPEND_INPUT_OVER_CEILING` ([src/learnloop/content/synthesis/source_append.py](../../../../../../../src/learnloop/content/synthesis/source_append.py), line 99)
- `_AUTO_APPLY_RELATIONS` ([src/learnloop/content/synthesis/source_append.py](../../../../../../../src/learnloop/content/synthesis/source_append.py), line 324)
- `_APPEND_LISTS` ([src/learnloop/content/synthesis/source_append.py](../../../../../../../src/learnloop/content/synthesis/source_append.py), line 922)
- `APPEND_CALL` ([src/learnloop/content/synthesis/source_append.py](../../../../../../../src/learnloop/content/synthesis/source_append.py), line 982)
- `APPEND` ([src/learnloop/content/synthesis/source_append.py](../../../../../../../src/learnloop/content/synthesis/source_append.py), line 997)

## Internal implementation anchors

- `class _AppendBudget` ([source](../../../../../../../src/learnloop/content/synthesis/source_append.py), line 113) — An append's spend against its budgets (the shard runner's ``spend``).
- `_over_ceiling(tokens: int, ceiling: int) -> StudyMapError` ([source](../../../../../../../src/learnloop/content/synthesis/source_append.py), line 161)
- `_units_by_revision(unit_keys: Collection[str], revision_ids: Collection[str]) -> dict[str, set[str]]` ([source](../../../../../../../src/learnloop/content/synthesis/source_append.py), line 206) — ``{revision: units}`` from a manifest's ``"revision:unit"`` keys.
- `_sent_units(repository: Repository, source_set_id: str, revision_ids: Collection[str]) -> dict[str, set[str]]` ([source](../../../../../../../src/learnloop/content/synthesis/source_append.py), line 216) — The units each kept synthesis of the set sent, per revision.
- `_append(vault: LoadedVault, repository: Repository, root: Path, source_set_id: str, *, client: Any, new_revision_ids: list[str] | None, change_kind: str, revision_diff: dict[str, Any], new_unit_ids: Mapping[str, Sequence[str]] | None=None, brief: dict[str, Any], auto_apply: bool, clock: Clock | None, budget_overrides: dict[str, int] | None=None, unlimited_token_budget: bool=False, embedding_client_factory: Callable[[], Any] | None=None, facet_identity_client: Any=None, apply_gate: Callable[[], bool] | None=None) -> AppendResult` ([source](../../../../../../../src/learnloop/content/synthesis/source_append.py), line 447) — The append opens its run with the shared head (:func:`open_synthesis_run`); its scope step selects the new inventories and the bounded neighbourhood around them, which the manifest records and the request reads.
- `_apply_routine_items(root: Path, repository: Repository, vault: LoadedVault, outcome: SynthesisOutcome, *, auto_apply: bool, apply_gate: Callable[[], bool] | None, clock: Clock | None, synthesis_run_id: str | None=None) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/synthesis/source_append.py), line 526) — The append's apply step: which of the proposal's items wait for review, and §10.3's lane, where routine span/assessment attachments apply under the vault lock; everything else stays a pending review proposal.
- `_lane_refusal(auto_apply: bool, auto_ids: Sequence[str], apply_gate: Callable[[], bool] | None) -> str` ([source](../../../../../../../src/learnloop/content/synthesis/source_append.py), line 582) — Why §10.3's lane applied nothing this run: not asked, nothing routine, or the gate's own refusal.
- `_waiting_reasons(items: Sequence[Mapping[str, Any]], applied: set[str], refusals: Mapping[str, str], *, lane_refusal: str | None) -> list[tuple[str, str]]` ([source](../../../../../../../src/learnloop/content/synthesis/source_append.py), line 592) — Each item left for review and why: its §10.3 condition, an item kind the lane never applies, or (for an item the lane would have applied) why the lane applied nothing.
- `class _AppendState` ([source](../../../../../../../src/learnloop/content/synthesis/source_append.py), line 615) — What the append's own item kinds share: the answer and the inputs it is read against, and the rows, gate items, review records and auto-apply ids built so far (the bootstrap normalizer's rows come first).
- `_provenance_links(st: _AppendState) -> None` ([source](../../../../../../../src/learnloop/content/synthesis/source_append.py), line 631) — Provenance links: dropped with a review record when their span does not resolve or is exam material aimed at a facet; those ``_auto_apply_refusal`` finds nothing against join ``auto_apply_ids``.
- `_notation_mappings(st: _AppendState) -> None` ([source](../../../../../../../src/learnloop/content/synthesis/source_append.py), line 711) — Notation mappings (review-required).
- `_source_conflicts(st: _AppendState) -> None` ([source](../../../../../../../src/learnloop/content/synthesis/source_append.py), line 737) — Source conflicts (always reviewed).
- `_restructures(st: _AppendState) -> None` ([source](../../../../../../../src/learnloop/content/synthesis/source_append.py), line 761) — Restructures (update or deactivate; review and lock-checked); a facet reword goes through its own check.
- `_normalize_append(reconciliation, inputs, vault, now, *, subject_id, items_off: bool=False, nominator=None, facet_identity_plan=None) -> Normalized` ([source](../../../../../../../src/learnloop/content/synthesis/source_append.py), line 829) — Map an AppendReconciliation to proposal rows and gate items: the bootstrap normalizer over its new coverage, then the append's own item kinds after it, with the client ids §10.3 auto-applies.
- `class _AppendContext` ([source](../../../../../../../src/learnloop/content/synthesis/source_append.py), line 869) — What an append's request reads beyond the source set's inputs (``SynthesisRun.context``).
- `_append_passes(run: Any) -> list[list[dict[str, Any]]]` ([source](../../../../../../../src/learnloop/content/synthesis/source_append.py), line 879) — The append's units of work: the new inventories whole when their request fits ``append_input_ceiling``, as before; otherwise split, in order (``select_new_inventories``': revision, then unit order), into passes of whole inventories, each as large as fits under the ceiling with r…
- `_append_contexts(run: Any)` ([source](../../../../../../../src/learnloop/content/synthesis/source_append.py), line 896)
- `_merge_append(merged: Any, answer: Any) -> Any` ([source](../../../../../../../src/learnloop/content/synthesis/source_append.py), line 927) — Two passes' answers as one: their items in pass order, their summaries each once.
- `_within_the_brief(run: Any, answer: Any, *, shard_count: int=1, **_unused: Any) -> tuple[Any, dict[str, Any], list[dict[str, Any]]]` ([source](../../../../../../../src/learnloop/content/synthesis/source_append.py), line 940)
- `_one_restructure_per_target(run: Any, answer: Any) -> tuple[Any, list[dict[str, Any]]]` ([source](../../../../../../../src/learnloop/content/synthesis/source_append.py), line 951) — A split append's restructures, the first per target: two updates of one entity in one proposal would conflict at apply, so the later ones are dropped with a review record naming them.
- `_append_digest(rows: list[dict[str, Any]], context: _AppendContext, summary: str) -> Any` ([source](../../../../../../../src/learnloop/content/synthesis/source_append.py), line 978)
- `_within_preset(reconciliation: Any, brief: Mapping[str, Any]) -> tuple[Any, list[dict[str, Any]]]` ([source](../../../../../../../src/learnloop/content/synthesis/source_append.py), line 1028) — The answer the brief's authoring preset allows, with a review record of what it dropped.
- `class _FacetReword` ([source](../../../../../../../src/learnloop/content/synthesis/source_append.py), line 1054) — A facet restructure, normalized: its proposal payload and the citations the gates judge.
- `_facet_reword(obj: dict[str, Any], vault: LoadedVault, inputs: Any, operation: str, target_id: str) -> _FacetReword` ([source](../../../../../../../src/learnloop/content/synthesis/source_append.py), line 1071) — Normalize a facet restructure: a reword of a registered facet.
- `_checked_reword(target_id: str, current: dict[str, Any], payload: dict[str, Any], gate_refs: list[ProvenanceRef], support: Any, unresolved: list[str], inputs: Any, policy: facet_meaning.MeaningPolicy=facet_meaning.REWORD_CONFIRM) -> _FacetReword` ([source](../../../../../../../src/learnloop/content/synthesis/source_append.py), line 1181) — A reword, judged in advance by the chokepoint the apply runs again.
- `_span_problem(span: dict[str, Any], inputs) -> str | None` ([source](../../../../../../../src/learnloop/content/synthesis/source_append.py), line 1216) — Why a cited span cannot attach, or None when it can.
- `_relation_for_intent(intent: str | None) -> str` ([source](../../../../../../../src/learnloop/content/synthesis/source_append.py), line 1231)
- `_hash_type(target_type: str) -> str` ([source](../../../../../../../src/learnloop/content/synthesis/source_append.py), line 1239)
- `_target_type(target_type: str) -> str` ([source](../../../../../../../src/learnloop/content/synthesis/source_append.py), line 1243)
- `_auto_apply_refusal(payload, gate_refs, current_hash, target_type) -> str | None` ([source](../../../../../../../src/learnloop/content/synthesis/source_append.py), line 1249) — §10.3 auto-apply predicate for a provenance_link: ``None`` when it applies, else the condition that failed (the run's auto-apply record names it).
- `_span_yaml(span, inputs) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/synthesis/source_append.py), line 1282)
- `_snapshot(repository: Repository, vault: LoadedVault) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/synthesis/source_append.py), line 1292)
- `_link_count(repository: Repository) -> int` ([source](../../../../../../../src/learnloop/content/synthesis/source_append.py), line 1302)
- `_diff_from_snapshot(repository, vault_after, before, patch_id) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/synthesis/source_append.py), line 1307)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]] — imports `append_source`, `plan_append_embedding`, `units_not_yet_sent`; statically calls `append_source`, `plan_append_embedding`, `units_not_yet_sent`
- [[Reference/Modules/learnloop/content/pipeline/add_source|learnloop.content.pipeline.add_source]] — imports `APPEND_INPUT_OVER_CEILING`
- [[Reference/Modules/learnloop/content/pipeline/revision_refresh|learnloop.content.pipeline.revision_refresh]] — imports `append_source`; statically calls `append_source`
- [[Reference/Modules/learnloop/content/synthesis/jobs|learnloop.content.synthesis.jobs]] — imports `APPEND_INPUT_OVER_CEILING`, `append_source`, `subject_has_applied_study_map`; statically calls `append_source`, `subject_has_applied_study_map`
- [[Reference/Modules/learnloop_sidecar/handlers/ingest|learnloop_sidecar.handlers.ingest]] — imports `append_source`, `subject_has_applied_study_map`, `units_not_yet_sent`; statically calls `append_source`, `subject_has_applied_study_map`, `units_not_yet_sent`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/transport|learnloop.ai.transport]] — imports `StructuredTransport`, `execute_structured_operation`; calls `execute_structured_operation`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`
- [[Reference/Modules/learnloop/content/facet_identity/authority|learnloop.content.facet_identity.authority]] — imports `module`; calls `authority_changes`, `check_meaning_write`, `contributions`, `meaning_policy`, `overlay`, `support_entries`
- [[Reference/Modules/learnloop/content/facet_identity/judge|learnloop.content.facet_identity.judge]] — imports `manifest_identity`; calls `manifest_identity`
- [[Reference/Modules/learnloop/content/facet_identity/plan|learnloop.content.facet_identity.plan]] — imports `ingest_dry_run`; calls `ingest_dry_run`
- [[Reference/Modules/learnloop/content/proposals/patches|learnloop.content.proposals.patches]] — imports `apply_accepted_items`, `compute_target_hash`; calls `apply_accepted_items`, `compute_target_hash`
- [[Reference/Modules/learnloop/content/synthesis/ai_contracts|learnloop.content.synthesis.ai_contracts]] — imports `AppendReconciliation`, `AppendReconciliationContext`, `SourceSetSynthesis`, `append_reconciliation_prompt`, `append_reconciliation_prompt_version`; calls `AppendReconciliationContext`, `SourceSetSynthesis`, `append_reconciliation_prompt`
- [[Reference/Modules/learnloop/content/synthesis/append_budget|learnloop.content.synthesis.append_budget]] — imports `append_groups`, `append_input_tokens`; calls `append_groups`, `append_input_tokens`
- [[Reference/Modules/learnloop/content/synthesis/append_neighborhood|learnloop.content.synthesis.append_neighborhood]] — imports `select_neighborhood`; calls `select_neighborhood`
- [[Reference/Modules/learnloop/content/synthesis/facet_doctor|learnloop.content.synthesis.facet_doctor]] — imports `near_duplicate_facet_review`; calls `near_duplicate_facet_review`
- [[Reference/Modules/learnloop/content/synthesis/graph_nomination|learnloop.content.synthesis.graph_nomination]] — imports `GraphNominator`, `plan_ingest_embedding`; calls `plan_ingest_embedding`
- [[Reference/Modules/learnloop/content/synthesis/normalize|learnloop.content.synthesis.normalize]] — imports `Normalized`, `_dump`, `_row`, `_span_refs`, `_support_citations`, `normalize`; calls `_dump`, `_row`, `_span_refs`, `_support_citations`, `normalize`
- [[Reference/Modules/learnloop/content/synthesis/source_set_synthesis|learnloop.content.synthesis.source_set_synthesis]] — imports `RunScope`, `StudyMapError`, `SynthesisCall`, `SynthesisMode`, `SynthesisOutcome`, `_collect_inputs`, `_consolidate_same_title_concepts`, `_count_items`, `_result_tokens`, `_synthesis_pass_key`, `finish_synthesis_run`, `gate_refusal`, `open_synthesis_run`, `record_auto_apply`; calls `RunScope`, `StudyMapError`, `SynthesisCall`, `SynthesisMode`, `_collect_inputs`, `_consolidate_same_title_concepts`, `_count_items`, `_result_tokens`, `_synthesis_pass_key`, `finish_synthesis_run`, `gate_refusal`, `open_synthesis_run`, `record_auto_apply`
- [[Reference/Modules/learnloop/content/synthesis/study_map_diff|learnloop.content.synthesis.study_map_diff]] — imports `compute_study_map_diff`; calls `compute_study_map_diff`
- [[Reference/Modules/learnloop/content/synthesis/synthesis_gates|learnloop.content.synthesis.synthesis_gates]] — imports `ASSESSMENT_ONLY_ROLES`, `GateItem`, `ProvenanceRef`; calls `GateItem`
- [[Reference/Modules/learnloop/content/synthesis/synthesis_manifests|learnloop.content.synthesis.synthesis_manifests]] — imports `content_hash`; calls `content_hash`
- [[Reference/Modules/learnloop/content/synthesis/vault_epigraphs|learnloop.content.synthesis.vault_epigraphs]] — imports `digest_for_append`; calls `digest_for_append`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/vault/loader|learnloop.vault.loader]] — imports `load_vault`; calls `load_vault`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/vault/paths|learnloop.vault.paths]] — imports `VaultPaths`; calls `VaultPaths`
- [[Reference/Modules/learnloop/vault/repository|learnloop.vault.repository]] — imports `vault_repository`; calls `vault_repository`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `pathlib`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Import Canonical Sources]]
- [[Build a Study Map]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]], [[Reference/Modules/learnloop/content/pipeline/add_source|learnloop.content.pipeline.add_source]], [[Reference/Modules/learnloop/content/pipeline/revision_refresh|learnloop.content.pipeline.revision_refresh]], [[Reference/Modules/learnloop/content/synthesis/jobs|learnloop.content.synthesis.jobs]], [[Reference/Modules/learnloop_sidecar/handlers/ingest|learnloop_sidecar.handlers.ingest]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/facet_identity_ingest_helpers.py](../../../../../../../tests/facet_identity_ingest_helpers.py) — direct import
- [tests/identity_pins_helpers.py](../../../../../../../tests/identity_pins_helpers.py) — direct import
- [tests/test_append_split_passes.py](../../../../../../../tests/test_append_split_passes.py) — direct import
  - `test_a_crash_at_any_pass_resumes_at_that_pass_and_applies_once`
  - `test_a_single_unit_over_the_ceiling_is_still_refused_before_any_call`
  - `test_a_split_appends_answers_merge_once_per_concept_and_restructure`
  - `test_an_append_over_its_ceiling_is_split_and_applies_what_one_unsplit_append_would`
  - `test_an_append_that_fits_is_one_request_as_before`
  - `test_completed_receipt_survives_crash_before_pass_checkpoint`
  - `test_each_pass_is_its_own_paid_request_under_the_appends_limits`
  - `test_every_pass_shares_its_prompt_through_the_neighbourhood_so_providers_can_cache_it`
  - `test_later_cited_reword_survives_invalid_first_edit`
  - `test_passes_hold_as_many_units_as_fit_with_room_for_a_span_round`
  - `test_singleton_lower_bound_checked_before_neighborhood_nomination`
  - `test_span_round_with_no_room_keeps_the_base_answer`
  - `test_split_conflict_and_other_pass_disposition_have_distinct_local_names`
  - `test_split_preserves_distinct_concepts_with_the_same_title`
  - `test_split_summary_remembers_distinct_original_multiline_summaries`
- [tests/test_build_study_map_routing.py](../../../../../../../tests/test_build_study_map_routing.py) — direct import
  - `test_helper_detects_applied_study_map`
- [tests/test_cli_append_units.py](../../../../../../../tests/test_cli_append_units.py) — direct import
  - `test_a_partly_sent_member_sends_only_its_new_units`
  - `test_a_wholly_rejected_append_leaves_its_units_new`
- [tests/test_collection_append_units.py](../../../../../../../tests/test_collection_append_units.py) — direct import
  - `test_an_inventoried_unit_a_kept_synthesis_sent_is_not_sent_again`
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
- [tests/test_ingest_decision_records.py](../../../../../../../tests/test_ingest_decision_records.py) — direct import
  - `test_the_append_lane_says_which_condition_kept_a_link_back`
- [tests/test_ingest_instrument_gates.py](../../../../../../../tests/test_ingest_instrument_gates.py) — direct import
  - `test_append_authors_items_when_upfront`
  - `test_append_respects_items_off`
- [tests/test_keep_ahead_append_units.py](../../../../../../../tests/test_keep_ahead_append_units.py) — direct import
  - `test_the_unit_filter_applies_per_revision`
- [tests/test_normalize_cases.py](../../../../../../../tests/test_normalize_cases.py) — direct import
- [tests/test_rerun_proposals.py](../../../../../../../tests/test_rerun_proposals.py) — direct import
- [tests/test_retired_config_identities.py](../../../../../../../tests/test_retired_config_identities.py) — direct import
  - `test_an_append_run_completed_before_arc_c_is_reused_for_the_same_request`
  - `test_append_manifest_hashes_the_facet_identity_config_as_before_arc_c`
- [tests/test_source_append.py](../../../../../../../tests/test_source_append.py) — direct import
  - `test_a_retry_after_an_append_gate_failure_pays_for_a_fresh_answer`
  - `test_an_append_budget_failure_leaves_both_run_rows_failed`
  - `test_an_append_over_its_input_ceiling_is_refused_before_any_call`
  - `test_an_over_budget_append_answer_is_checkpointed_and_the_retry_does_not_repay`
  - `test_append_budget_overrides_reach_the_manifest`
  - `test_append_epigraph_failure_leaves_the_append_unchanged`
  - `test_append_output_is_counted_without_escaping_non_ascii`
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
  - `test_the_append_call_runs_under_its_output_limit`
- [tests/test_structured_transport_parity.py](../../../../../../../tests/test_structured_transport_parity.py) — direct import
- [tests/test_synthesis_answer_reuse.py](../../../../../../../tests/test_synthesis_answer_reuse.py) — direct import
  - `test_an_append_rejection_keeps_a_fresh_answer_another_run_saved`
- [tests/test_synthesis_tail_golden.py](../../../../../../../tests/test_synthesis_tail_golden.py) — direct import
  - `test_append_an_unknown_source_set_is_refused_before_any_write`

## Modification guidance

- Change source append policy here when content owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/content/synthesis/source_append.py](../../../../../../../src/learnloop/content/synthesis/source_append.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

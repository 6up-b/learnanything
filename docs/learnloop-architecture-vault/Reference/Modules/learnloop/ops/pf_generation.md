---
title: "learnloop.ops.pf_generation"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/ops/pf_generation.py"
source_paths:
  - "src/learnloop/ops/pf_generation.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.ops"
layer: "domain"
concepts:
  - "State and Persistence"
  - "Configuration"
workflows:
  - "Doctor Migrations and Recovery"
aliases:
  - "learnloop.ops.pf_generation module"
  - "src/learnloop/ops/pf_generation.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-ops"
---

# `learnloop.ops.pf_generation`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/ops/_package|learnloop.ops]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.ops.pf_generation` exists within [[Reference/Modules/learnloop/ops/_package|learnloop.ops]] to own the behavior summarized by its module contract: PF-b: generate many, verify, filter, select, publish (Slice 2 §5.3-§5.4).

The authoritative system-level explanation remains in [[State and Persistence]], [[Configuration]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/ops/pf_generation.py](../../../../../../src/learnloop/ops/pf_generation.py) |
| Source lines | 2201 |
| Owning package | [[Reference/Modules/learnloop/ops/_package|learnloop.ops]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class PFRefused(ValueError)` ([source](../../../../../../src/learnloop/ops/pf_generation.py), line 142) — A configuration the spec forbids (e.g.
- `class GenerationOptions` ([source](../../../../../../src/learnloop/ops/pf_generation.py), line 147)
- `class Candidate` ([source](../../../../../../src/learnloop/ops/pf_generation.py), line 161)
  - `alive(self) -> bool` (line 180; public)
  - `expected_answer(self) -> str` (line 184; public)
  - `content_hash(self) -> str` (line 188; public)
- `selection_state(rows: list[Mapping[str, Any]]) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/ops/pf_generation.py), line 217) — How far a mint request's selection got, from its persisted candidates.
- `panel_difficulty(parent_difficulty: float | None, parent_rate: tuple[int, int], variant_rate: tuple[int, int], scale: float) -> float` ([source](../../../../../../src/learnloop/ops/pf_generation.py), line 254) — Per-variant offset from the parent on the 2PL difficulty scale.
- `family_targets(vault: LoadedVault, options: GenerationOptions) -> list[tuple[ActivityFamily, PracticeItem]]` ([source](../../../../../../src/learnloop/ops/pf_generation.py), line 311) — Families with an active member, each with its parent (anchor) item.
- `class RequiredMethodJudgmentIncomplete(RuntimeError)` ([source](../../../../../../src/learnloop/ops/pf_generation.py), line 398) — A selected variant has no required-method verdict yet (review F17): the family's job stays retryable instead of completing.
- `generate_practice(vault: LoadedVault, *, caps: SpendCaps, options: GenerationOptions=GenerationOptions(), dry_run: bool=False, price_per_million: float | None=None, cancelled: Callable[[], bool] | None=None, clients: Mapping[str, Any] | None=None, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/ops/pf_generation.py), line 1960) — Plan (and unless ``dry_run``, run) PF-b generation; aggregate-only report.
- `publish_backlog(vault: LoadedVault, *, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/ops/pf_generation.py), line 2157) — Publish selected-but-capped candidates under today's cap; no model calls.
- `pf_status(vault: LoadedVault, *, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/ops/pf_generation.py), line 2174)

### Module constants

- `_LOGGER` ([src/learnloop/ops/pf_generation.py](../../../../../../src/learnloop/ops/pf_generation.py), line 111)
- `PATHS` ([src/learnloop/ops/pf_generation.py](../../../../../../src/learnloop/ops/pf_generation.py), line 113)
- `RELATIONS` ([src/learnloop/ops/pf_generation.py](../../../../../../src/learnloop/ops/pf_generation.py), line 114)
- `GENERATOR_VERSIONS` ([src/learnloop/ops/pf_generation.py](../../../../../../src/learnloop/ops/pf_generation.py), line 115)
- `GATE_POLICY_VERSION` ([src/learnloop/ops/pf_generation.py](../../../../../../src/learnloop/ops/pf_generation.py), line 119)
- `MMR_SELECTION_POLICY` ([src/learnloop/ops/pf_generation.py](../../../../../../src/learnloop/ops/pf_generation.py), line 121)
- `FILTER_ORDER` ([src/learnloop/ops/pf_generation.py](../../../../../../src/learnloop/ops/pf_generation.py), line 122)
- `NOT_APPLICABLE_FILTERS` ([src/learnloop/ops/pf_generation.py](../../../../../../src/learnloop/ops/pf_generation.py), line 127)
- `MIN_QUOTE_WORDS` ([src/learnloop/ops/pf_generation.py](../../../../../../src/learnloop/ops/pf_generation.py), line 131)
- `PF_AGREEMENT_KEYS` ([src/learnloop/ops/pf_generation.py](../../../../../../src/learnloop/ops/pf_generation.py), line 134)
- `PLAN_ROLES` ([src/learnloop/ops/pf_generation.py](../../../../../../src/learnloop/ops/pf_generation.py), line 136)
- `LEASE_SECONDS` ([src/learnloop/ops/pf_generation.py](../../../../../../src/learnloop/ops/pf_generation.py), line 138)
- `DIFFICULTY_BOUNDS` ([src/learnloop/ops/pf_generation.py](../../../../../../src/learnloop/ops/pf_generation.py), line 139)
- `SELECTION_ORDER_KEY` ([src/learnloop/ops/pf_generation.py](../../../../../../src/learnloop/ops/pf_generation.py), line 213)
- `SELECTION_COMPLETE_KEY` ([src/learnloop/ops/pf_generation.py](../../../../../../src/learnloop/ops/pf_generation.py), line 214)

### Explicit exports

`__all__` declares:

- `FILTER_ORDER`
- `GATE_POLICY_VERSION`
- `GENERATOR_VERSIONS`
- `GenerationOptions`
- `MMR_SELECTION_POLICY`
- `PATHS`
- `PFRefused`
- `RequiredMethodJudgmentIncomplete`
- `family_targets`
- `generate_practice`
- `panel_difficulty`
- `pf_run_lock`
- `pf_status`
- `publish_backlog`

## Internal implementation anchors

- `_candidate_from_row(row: dict[str, Any]) -> Candidate` ([source](../../../../../../src/learnloop/ops/pf_generation.py), line 192) — A persisted candidate as the run holds it (review F20: a resumed job).
- `_sha(payload: Any) -> str` ([source](../../../../../../src/learnloop/ops/pf_generation.py), line 246)
- `_logit(probability: float) -> float` ([source](../../../../../../src/learnloop/ops/pf_generation.py), line 250)
- `_item_context(item: PracticeItem, vault: LoadedVault | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/ops/pf_generation.py), line 272) — Item-side material only; the resolved rubric (item or practice-mode default).
- `_family_context(family: ActivityFamily) -> dict[str, Any]` ([source](../../../../../../src/learnloop/ops/pf_generation.py), line 286)
- `_run_lock(root: Path) -> Iterator[None]` ([source](../../../../../../src/learnloop/ops/pf_generation.py), line 292)
- `_resolve_path(vault: LoadedVault, family: ActivityFamily, requested: str) -> str` ([source](../../../../../../src/learnloop/ops/pf_generation.py), line 336)
- `class _Context` ([source](../../../../../../src/learnloop/ops/pf_generation.py), line 344)
- `class _FamilyRun` ([source](../../../../../../src/learnloop/ops/pf_generation.py), line 403)
- `_job_angle(family_id: str, path: str, relation: str, round_id: str, tier: str | None, count: int) -> dict[str, Any]` ([source](../../../../../../src/learnloop/ops/pf_generation.py), line 1668) — A family job's requested angle: its mint request's identity (with the parent's card version) and its generation seed.
- `_resumable_job(vault: LoadedVault, repository: Repository, family: ActivityFamily, parent: PracticeItem, path: str, options: GenerationOptions, round_id: str, now_iso: str) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/ops/pf_generation.py), line 1676) — A job of this round whose selection already started, read-only (round 3, F17/F20/F22).
- `_plan_resume(vault: LoadedVault, family: ActivityFamily, parent: PracticeItem, path: str, options: GenerationOptions, roles: Mapping[str, list[RoleClient]], resume: Mapping[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/ops/pf_generation.py), line 1747) — The plan of a resumable job: only its unfinished work (round 3, F17/F20/F22).
- `_tier_routes(vault: LoadedVault, tier: str | None) -> list[str] | None` ([source](../../../../../../src/learnloop/ops/pf_generation.py), line 1809)
- `_plan_family(vault: LoadedVault, family: ActivityFamily, parent: PracticeItem, path: str, options: GenerationOptions, roles: Mapping[str, list[RoleClient]], repository: Repository | None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/ops/pf_generation.py), line 1818)
- `_plan_estimates(plans: list[dict[str, Any]], caller: PFCaller, roles: Mapping[str, list[RoleClient]]) -> tuple[SpendEstimate, SpendEstimate]` ([source](../../../../../../src/learnloop/ops/pf_generation.py), line 1901)
- `_seed_families(vault: LoadedVault, repository: Repository, seed_items: tuple[str, ...], clock: Clock | None) -> LoadedVault` ([source](../../../../../../src/learnloop/ops/pf_generation.py), line 1935) — Owner-requested single-item families (an authored record; P12).
- `_publish_slots(vault: LoadedVault, repository: Repository, clock: Clock | None) -> int` ([source](../../../../../../src/learnloop/ops/pf_generation.py), line 2132)
- `_results_by_model(repository: Repository, run_id: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/ops/pf_generation.py), line 2144) — Every PF report splits by model id (Slice 2 §13).

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/pf|learnloop.cli.pf]] — imports `GenerationOptions`, `generate_practice`, `pf_status`, `publish_backlog`; statically calls `GenerationOptions`, `generate_practice`, `pf_status`, `publish_backlog`
- [[Reference/Modules/learnloop/ops/pf_reports|learnloop.ops.pf_reports]] — imports `FILTER_ORDER`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/errors|learnloop.ai.errors]] — imports `AIInterrupted`, `AIProviderUnavailable`
- [[Reference/Modules/learnloop/ai/execution|learnloop.ai.execution]] — imports `content_key`; calls `content_key`
- [[Reference/Modules/learnloop/ai/output_budget|learnloop.ai.output_budget]] — imports `output_budget`; calls `output_budget`
- [[Reference/Modules/learnloop/ai/spend|learnloop.ai.spend]] — imports `SpendCaps`, `SpendEstimate`, `SpendLimitExceeded`; calls `SpendEstimate`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/content/authoring/authoring_gates|learnloop.content.authoring.authoring_gates]] — imports `build_instrument_gates`; calls `build_instrument_gates`
- [[Reference/Modules/learnloop/content/authoring/pf_contracts|learnloop.content.authoring.pf_contracts]] — imports `module`; calls `closed_book_prompt`, `equivalence_prompt`, `freshness_prompt`, `generator_program_prompt`, `panel_solve_prompt`, `proposer_prompt`, `selection_prompt`, `skeleton_prompt`, `source_anchored_prompt`, `span_support_prompt`, `structure_prompt`
- [[Reference/Modules/learnloop/content/authoring/pf_sandbox|learnloop.content.authoring.pf_sandbox]] — imports `GENERATOR_PROTOCOL`, `SandboxLimits`, `SandboxUnavailable`, `check_generator_answers`, `equivalence_confirmations`, `require_sandbox`, `run_equivalence_checks`, `run_generator_tests`, `sandbox_available`; calls `check_generator_answers`, `require_sandbox`, `run_generator_tests`, `sandbox_available`
- [[Reference/Modules/learnloop/content/authoring/practice_leakage|learnloop.content.authoring.practice_leakage]] — imports `build_cross_source_spans`, `build_held_out_inventory`, `screen_practice_payload`; calls `build_cross_source_spans`, `build_held_out_inventory`, `screen_practice_payload`
- [[Reference/Modules/learnloop/content/proposals/method_statement_judge|learnloop.content.proposals.method_statement_judge]] — imports `LazyStatementJudge`, `planned_tokens`, `recorded_verdict`, `resolve_statement_judge`; calls `LazyStatementJudge`, `planned_tokens`, `recorded_verdict`, `resolve_statement_judge`
- [[Reference/Modules/learnloop/content/sources/exam_material|learnloop.content.sources.exam_material]] — imports `exam_material`, `source_ref_protected`; calls `exam_material`, `source_ref_protected`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/stores/pf|learnloop.db.stores.pf]] — imports `module`; calls `candidate`, `candidates`, `insert_candidate`, `insert_skeleton`, `skeletons_for_hashes`, `update_candidate`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/ops/pf_calls|learnloop.ops.pf_calls]] — imports `PFCaller`, `PFUnavailable`, `ROLE_TASKS`, `RoleClient`, `distinct_models`, `estimate_tokens`, `planned_role_clients`, `resolve_role_clients`; calls `PFCaller`, `distinct_models`, `estimate_tokens`, `planned_role_clients`, `resolve_role_clients`
- [[Reference/Modules/learnloop/ops/pf_publish|learnloop.ops.pf_publish]] — imports `TRACE_RELATIONS`, `judge_variant_stem`, `judged_inputs`, `publish_selected`, `remaining_publish_slots`, `stale_inputs`; calls `judge_variant_stem`, `judged_inputs`, `publish_selected`, `remaining_publish_slots`, `stale_inputs`
- [[Reference/Modules/learnloop/ops/pf_selection|learnloop.ops.pf_selection]] — imports `DIVERSITY_BASIS`, `mmr_order`, `similarity`, `vendi_contributions`, `vendi_score`; calls `mmr_order`, `similarity`, `vendi_contributions`, `vendi_score`
- [[Reference/Modules/learnloop/ops/pf_verify|learnloop.ops.pf_verify]] — imports `module`; calls `VerifierEnv`, `agreement`, `panel_solves`, `span_support`
- [[Reference/Modules/learnloop/substrate/activities|learnloop.substrate.activities]] — imports `resolve_legacy_item`; calls `resolve_legacy_item`
- [[Reference/Modules/learnloop/substrate/families|learnloop.substrate.families]] — imports `apply_family`, `family_operation_lock`, `sync_authored_families`; calls `apply_family`, `family_operation_lock`, `sync_authored_families`
- [[Reference/Modules/learnloop/substrate/item_fingerprints|learnloop.substrate.item_fingerprints]] — imports `EXACT_COMPONENTS`, `FINGERPRINT_VERSION`, `final_answer_text`, `fingerprint_keys`, `item_fingerprint_keys`, `published_candidate_payloads`, `render_expected_answer`, `shared_keys`, `skeleton_content_hash`; calls `final_answer_text`, `fingerprint_keys`, `item_fingerprint_keys`, `published_candidate_payloads`, `render_expected_answer`, `shared_keys`, `skeleton_content_hash`
- [[Reference/Modules/learnloop/vault/loader|learnloop.vault.loader]] — imports `load_vault`; calls `load_vault`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `ActivityFamily`, `FamilyReference`, `LoadedVault`, `PracticeItem`; calls `ActivityFamily`, `FamilyReference`
- [[Reference/Modules/learnloop/vault/paths|learnloop.vault.paths]] — imports `VaultPaths`; calls `VaultPaths`
- [[Reference/Modules/learnloop/vault/repository|learnloop.vault.repository]] — imports `vault_repository`; calls `vault_repository`
- [[Reference/Modules/learnloop/vault/writer|learnloop.vault.writer]] — imports `upsert_activity_family`; calls `upsert_activity_family`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `copy`, `dataclasses`, `datetime`, `fcntl`, `hashlib`, `json`, `logging`, `math`, `pathlib`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Doctor Migrations and Recovery]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/pf|learnloop.cli.pf]], [[Reference/Modules/learnloop/ops/pf_reports|learnloop.ops.pf_reports]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_exam_protection_review.py](../../../../../../tests/test_exam_protection_review.py) — direct import
- [tests/test_item_fingerprints.py](../../../../../../tests/test_item_fingerprints.py) — direct import
  - `test_a_published_item_later_used_as_the_parent_rebuilds`
  - `test_generic_rotation_claims_never_take_pf_generation_jobs`
  - `test_rebuild_recomputes_fingerprints_without_any_model_or_generator`
- [tests/test_pf_generation.py](../../../../../../tests/test_pf_generation.py) — direct import
  - `test_a_selection_whose_parent_contract_changed_is_never_published`
  - `test_every_filter_and_selection_decision_is_ledgered`
  - `test_generation_fails_closed_without_bubblewrap_before_any_paid_call`
  - `test_panel_difficulty_is_a_logit_offset_from_the_parent`
  - `test_publish_cap_holds_per_utc_day_and_the_backlog_publishes_next_day`
- [tests/test_pf_reports.py](../../../../../../tests/test_pf_reports.py) — direct import
  - `test_each_scaling_tier_runs_its_own_program_writer_on_identical_inputs`
  - `test_scaling_tier_without_routes_is_refused`
  - `test_suspect_acceptance_is_descriptive_and_never_ranks_a_tier`
- [tests/test_pf_verify_extraction_parity.py](../../../../../../tests/test_pf_verify_extraction_parity.py) — direct import
  - `test_the_pf_run_keeps_its_report_shape`
- [tests/test_required_method_authority.py](../../../../../../tests/test_required_method_authority.py) — direct import
  - `test_a_variant_with_no_verdict_or_an_edited_stem_is_not_published`
  - `test_pf_judges_each_selected_variant_once_and_publication_reads_the_verdict`
- [tests/test_required_method_reopened.py](../../../../../../tests/test_required_method_reopened.py) — direct import
  - `test_f17_a_failed_judgment_leaves_the_job_retryable_and_a_rerun_resumes_without_regenerating`
- [tests/test_required_method_round3.py](../../../../../../tests/test_required_method_round3.py) — direct import
  - `test_f22_an_interrupted_selection_is_finished_before_any_judgment`
- [tests/test_required_method_round3_review.py](../../../../../../tests/test_required_method_round3_review.py) — direct import
  - `test_f6_a_job_whose_every_verdict_is_recorded_publishes_without_a_judge`

## Modification guidance

- Make changes here when the responsibility remains pf generation within learnloop.ops; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/ops/pf_generation.py](../../../../../../src/learnloop/ops/pf_generation.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

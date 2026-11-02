---
title: "learnloop.practice_index.dossiers"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/practice_index/dossiers.py"
source_paths:
  - "src/learnloop/practice_index/dossiers.py"
source_commit: "1ef2f14ebf6f15de8b60736f60650017d40712d3"
source_commit_timestamp: "2026-10-15T12:39:41-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.practice_index"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.practice_index.dossiers module"
  - "src/learnloop/practice_index/dossiers.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-practice-index"
---

# `learnloop.practice_index.dossiers`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/practice_index/_package|learnloop.practice_index]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.practice_index.dossiers` exists within [[Reference/Modules/learnloop/practice_index/_package|learnloop.practice_index]] to own the behavior summarized by its module contract: Facet dossiers: one grounded, LLM-written retrieval text per facet.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/practice_index/dossiers.py](../../../../../../src/learnloop/practice_index/dossiers.py) |
| Source lines | 579 |
| Owning package | [[Reference/Modules/learnloop/practice_index/_package|learnloop.practice_index]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `1ef2f14ebf6f15de8b60736f60650017d40712d3` |
| Commit timestamp | `2026-10-15T12:39:41-04:00` |

## Public API

- `class DossierPlan` ([source](../../../../../../src/learnloop/practice_index/dossiers.py), line 98)
- `build_plans(vault: LoadedVault, repository: Repository, *, facet_ids: list[str] | None=None) -> list[DossierPlan]` ([source](../../../../../../src/learnloop/practice_index/dossiers.py), line 224) — Grounding and model-independent prompt for every registered facet.
- `render_dossier(draft: FacetDossierDraft, neighbor_titles: dict[str, str]) -> dict[str, str]` ([source](../../../../../../src/learnloop/practice_index/dossiers.py), line 298) — Canonical text of each field; this is what is embedded and keyword-indexed.
- `select_dossier(rows: list[DossierRow], *, source_hash: str | None, model_id: str, prompt_version: str=DOSSIER_PROMPT_VERSION) -> tuple[DossierRow, str]` ([source](../../../../../../src/learnloop/practice_index/dossiers.py), line 373) — The revision that serves, and how well it matches the current key.
- `intended_model(vault: LoadedVault) -> str` ([source](../../../../../../src/learnloop/practice_index/dossiers.py), line 392) — The dossier model generation would use now (ai.routing.practice_dossier).
- `select_current_dossiers(vault: LoadedVault, repository: Repository, *, plans: list[DossierPlan] | None=None) -> dict[str, tuple[DossierRow, str]]` ([source](../../../../../../src/learnloop/practice_index/dossiers.py), line 397) — Per registered facet with a dossier: the serving revision and its state.
- `dossier_status(vault: LoadedVault, repository: Repository) -> dict[str, Any]` ([source](../../../../../../src/learnloop/practice_index/dossiers.py), line 430) — Per registered facet: current, stale (sources changed) or missing.
- `generate_dossiers(vault: LoadedVault, *, caps: SpendCaps, dry_run: bool=False, price_per_million: float | None=None, facet_ids: list[str] | None=None, client: Any | None=None, cancelled: Callable[[], bool] | None=None, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/practice_index/dossiers.py), line 442) — Plan (dry run: no client, no writes) or write the missing dossiers.

### Module constants

- `DOSSIER_PROMPT_VERSION` ([src/learnloop/practice_index/dossiers.py](../../../../../../src/learnloop/practice_index/dossiers.py), line 67)
- `MAX_SPANS` ([src/learnloop/practice_index/dossiers.py](../../../../../../src/learnloop/practice_index/dossiers.py), line 70)
- `SPAN_CHARS` ([src/learnloop/practice_index/dossiers.py](../../../../../../src/learnloop/practice_index/dossiers.py), line 71)
- `MAX_ITEMS` ([src/learnloop/practice_index/dossiers.py](../../../../../../src/learnloop/practice_index/dossiers.py), line 72)
- `ITEM_CHARS` ([src/learnloop/practice_index/dossiers.py](../../../../../../src/learnloop/practice_index/dossiers.py), line 73)
- `MAX_CRITERIA` ([src/learnloop/practice_index/dossiers.py](../../../../../../src/learnloop/practice_index/dossiers.py), line 74)
- `MAX_NEIGHBORS` ([src/learnloop/practice_index/dossiers.py](../../../../../../src/learnloop/practice_index/dossiers.py), line 75)
- `MAX_BULLETS` ([src/learnloop/practice_index/dossiers.py](../../../../../../src/learnloop/practice_index/dossiers.py), line 76)
- `BULLET_CHARS` ([src/learnloop/practice_index/dossiers.py](../../../../../../src/learnloop/practice_index/dossiers.py), line 77)
- `_SOURCE_RELATIONS` ([src/learnloop/practice_index/dossiers.py](../../../../../../src/learnloop/practice_index/dossiers.py), line 78)
- `_INSTRUCTIONS` ([src/learnloop/practice_index/dossiers.py](../../../../../../src/learnloop/practice_index/dossiers.py), line 80)

### Explicit exports

`__all__` declares:

- `DOSSIER_PROMPT_VERSION`
- `DossierPlan`
- `build_plans`
- `dossier_status`
- `generate_dossiers`
- `intended_model`
- `render_dossier`
- `select_current_dossiers`
- `select_dossier`

## Internal implementation anchors

- `_clip(text: str | None, limit: int) -> str` ([source](../../../../../../src/learnloop/practice_index/dossiers.py), line 107)
- `class _SpanReader` ([source](../../../../../../src/learnloop/practice_index/dossiers.py), line 112) — Resolve block-span locators to text, loading each extraction once.
- `_spans(repository: Repository, reader: _SpanReader, facet: EvidenceFacet) -> list[str]` ([source](../../../../../../src/learnloop/practice_index/dossiers.py), line 143)
- `_grounding_items(vault: LoadedVault, items: list[PracticeItem]) -> list[PracticeItem]` ([source](../../../../../../src/learnloop/practice_index/dossiers.py), line 166)
- `_criteria(vault: LoadedVault, facet_id: str, items: list[PracticeItem]) -> list[str]` ([source](../../../../../../src/learnloop/practice_index/dossiers.py), line 172)
- `_neighbors(vault: LoadedVault, facet_id: str, facets: dict[str, EvidenceFacet], los_by_facet: dict[str, set[str]]) -> list[str]` ([source](../../../../../../src/learnloop/practice_index/dossiers.py), line 192)
- `_structured(facet: EvidenceFacet) -> dict[str, Any]` ([source](../../../../../../src/learnloop/practice_index/dossiers.py), line 209)
- `_bullets(values: list[str]) -> list[str]` ([source](../../../../../../src/learnloop/practice_index/dossiers.py), line 293)
- `_generation_lock(root: Path) -> Iterator[None]` ([source](../../../../../../src/learnloop/practice_index/dossiers.py), line 321)
- `_pending(sqlite_path: Path, plans: list[DossierPlan], model_id: str) -> list[DossierPlan]` ([source](../../../../../../src/learnloop/practice_index/dossiers.py), line 337)
- `_checkpoint_key(route, plan: DossierPlan) -> str` ([source](../../../../../../src/learnloop/practice_index/dossiers.py), line 350)
- `_recoverable(sqlite_path: Path, route, pending: list[DossierPlan]) -> set[str]` ([source](../../../../../../src/learnloop/practice_index/dossiers.py), line 355) — Facets whose paid answer is checkpointed, or left on a completed receipt whose checkpoint never committed, but whose row never committed.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/practice_index|learnloop.cli.practice_index]] — imports `dossier_status`, `generate_dossiers`; statically calls `dossier_status`, `generate_dossiers`
- [[Reference/Modules/learnloop/practice_index/retrieval|learnloop.practice_index.retrieval]] — imports `select_current_dossiers`; statically calls `select_current_dossiers`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/errors|learnloop.ai.errors]] — imports `AIInterrupted`, `AIInvalidOutput`, `AIProviderUnavailable`; calls `AIInvalidOutput`
- [[Reference/Modules/learnloop/ai/execution|learnloop.ai.execution]] — imports `content_key`; calls `content_key`
- [[Reference/Modules/learnloop/ai/spend|learnloop.ai.spend]] — imports `SpendBudget`, `SpendCaps`, `SpendLimitExceeded`; calls `SpendBudget`
- [[Reference/Modules/learnloop/ai/transport|learnloop.ai.transport]] — imports `render_structured_prompt`; calls `render_structured_prompt`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/stores/practice_index|learnloop.db.stores.practice_index]] — imports `DossierRow`, `checkpointed_keys`, `dossier_candidates`, `dossier_exists`, `insert_dossier`; calls `checkpointed_keys`, `dossier_candidates`, `dossier_exists`, `insert_dossier`
- [[Reference/Modules/learnloop/goals/exam_pool|learnloop.goals.exam_pool]] — imports `reserved_item_ids`; calls `reserved_item_ids`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/ingest/locators|learnloop.ingest.locators]] — imports `parse_block_span`; calls `parse_block_span`
- [[Reference/Modules/learnloop/practice_index/catalog|learnloop.practice_index.catalog]] — imports `DIAGNOSTIC_MODES`, `facet_items`, `facet_label`, `item_facets`, `registered_facets`; calls `facet_items`, `facet_label`, `item_facets`, `registered_facets`
- [[Reference/Modules/learnloop/practice_index/contracts|learnloop.practice_index.contracts]] — imports `FacetDossierDraft`
- [[Reference/Modules/learnloop/practice_index/paid|learnloop.practice_index.paid]] — imports `PaidCalls`, `checkpoint_key`, `estimated_call_tokens`, `plan_route`, `planning_repository`, `receipt_answer`, `resolve_client`, `transport_problem`; calls `PaidCalls`, `checkpoint_key`, `estimated_call_tokens`, `plan_route`, `planning_repository`, `receipt_answer`, `resolve_client`, `transport_problem`
- [[Reference/Modules/learnloop/vault/embedding_recipes|learnloop.vault.embedding_recipes]] — imports `facet_content_hash`; calls `facet_content_hash`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `EvidenceFacet`, `LoadedVault`, `PracticeItem`
- [[Reference/Modules/learnloop/vault/paths|learnloop.vault.paths]] — imports `VaultPaths`; calls `VaultPaths`
- [[Reference/Modules/learnloop/vault/required_method|learnloop.vault.required_method]] — imports `fit_presented_prompt`; calls `fit_presented_prompt`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `dataclasses`, `fcntl`, `pathlib`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/practice_index|learnloop.cli.practice_index]], [[Reference/Modules/learnloop/practice_index/retrieval|learnloop.practice_index.retrieval]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_practice_index_adapters.py](../../../../../../tests/test_practice_index_adapters.py) — direct import
  - `test_batch_dry_runs_never_migrate_an_older_rollback_database`
  - `test_cli_eval_dry_run_find_coverage_status_and_tool_spec`
- [tests/test_practice_index_dossiers.py](../../../../../../tests/test_practice_index_dossiers.py) — direct import
  - `test_a_paid_answer_survives_a_failed_write_and_is_not_paid_again`
  - `test_a_paid_answer_whose_checkpoint_failed_is_recovered_from_its_receipt`
  - `test_a_receipt_for_another_request_or_an_invalid_answer_is_not_recovered`
  - `test_an_unusable_answer_is_retried_then_reported_per_facet`
  - `test_call_caps_still_bind_a_subscription_route`
  - `test_dossier_fields_are_embedding_recipes`
  - `test_dry_run_estimates_without_a_client_or_writes`
  - `test_generation_is_capped_idempotent_and_receipted`
  - `test_grounding_excludes_answers_diagnostic_surfaces_and_exam_reserves`
  - `test_rebuild_preserves_dossiers_and_calls_no_model`
  - `test_regenerated_only_when_the_facet_or_its_sources_change`
  - `test_reverting_sources_selects_the_matching_earlier_dossier`
  - `test_select_dossier_prefers_current_sources_then_the_intended_model`
  - `test_switch_off_and_unknown_metered_price_fail_closed`
- [tests/test_practice_index_find.py](../../../../../../tests/test_practice_index_find.py) — direct import
  - `test_an_alternative_embedding_model_takes_an_explicit_price`
  - `test_changed_index_content_voids_an_earlier_evaluation_approval`
- [tests/test_practice_index_paid.py](../../../../../../tests/test_practice_index_paid.py) — direct import
  - `test_a_metered_invalid_answer_gets_no_hidden_repair_request`
  - `test_a_metered_timeout_sends_no_request_the_caps_did_not_admit`
  - `test_a_metered_transport_that_cannot_bound_requests_fails_closed`
  - `test_each_metered_retry_is_admitted_and_charged_separately`

## Modification guidance

- Make changes here when the responsibility remains dossiers within learnloop.practice_index; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/practice_index/dossiers.py](../../../../../../src/learnloop/practice_index/dossiers.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

---
title: "learnloop.instructional.harvest"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/instructional/harvest.py"
source_paths:
  - "src/learnloop/instructional/harvest.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.instructional"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.instructional.harvest module"
  - "src/learnloop/instructional/harvest.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-instructional"
---

# `learnloop.instructional.harvest`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/instructional/_package|learnloop.instructional]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.instructional.harvest` exists within [[Reference/Modules/learnloop/instructional/_package|learnloop.instructional]] to own the behavior summarized by its module contract: Owner-run batch work over textbook exercises (spec_source_practice_and_probes_v1 §7.2).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/instructional/harvest.py](../../../../../../src/learnloop/instructional/harvest.py) |
| Source lines | 318 |
| Owning package | [[Reference/Modules/learnloop/instructional/_package|learnloop.instructional]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `harvest_targets(vault: LoadedVault, repository: Repository, *, learning_object_ids: tuple[str, ...]=(), facet_ids: tuple[str, ...]=(), extra_facets: tuple[str, ...]=(), clock: Clock | None=None) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/instructional/harvest.py), line 61) — Thin facets (fewest admissible items first), narrowed by --lo/--facet.
- `harvest(vault: LoadedVault, repository: Repository, *, dry_run: bool, max_cost_usd: float | None, learning_object_ids: tuple[str, ...]=(), facet_ids: tuple[str, ...]=(), clients: Mapping[str, Any] | None=None, rerank_client: Any | None=None, embedder: Any | None=None, clock: Clock | None=None, on_progress: Callable[[str], None] | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/instructional/harvest.py), line 139)
- `verification_targets(vault: LoadedVault, repository: Repository, item_ids: tuple[str, ...]=()) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/instructional/harvest.py), line 238) — Exercise imports whose current content is not verified.
- `verify(vault: LoadedVault, repository: Repository, *, dry_run: bool, max_cost_usd: float | None, item_ids: tuple[str, ...]=(), clients: Mapping[str, Any] | None=None, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/instructional/harvest.py), line 263)

### Module constants

- `_FILTER_MEANINGS` ([src/learnloop/instructional/harvest.py](../../../../../../src/learnloop/instructional/harvest.py), line 111)

### Explicit exports

`__all__` declares:

- `harvest`
- `harvest_targets`
- `verification_targets`
- `verify`

## Internal implementation anchors

- `_query(vault: LoadedVault, facet_id: str) -> str` ([source](../../../../../../src/learnloop/instructional/harvest.py), line 94)
- `_spend(vault: LoadedVault, repository: Repository, started: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/instructional/harvest.py), line 103)
- `_skip(facet_id: str, result: Mapping[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/instructional/harvest.py), line 119) — Why a target imported nothing, in the report's own words (honest labels).
- `_sum_plans(plans: list[dict[str, Any]]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/instructional/harvest.py), line 133)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/sources|learnloop.cli.sources]] — imports `harvest`, `verify`; statically calls `harvest`, `verify`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/output_budget|learnloop.ai.output_budget]] — imports `output_budget`; calls `output_budget`
- [[Reference/Modules/learnloop/ai/spend|learnloop.ai.spend]] — imports `spend_envelopes`; calls `spend_envelopes`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/content/authoring/source_exercise_import|learnloop.content.authoring.source_exercise_import]] — imports `import_source_exercise`, `plan_import_cost`, `verify_item_key`; calls `import_source_exercise`, `plan_import_cost`, `verify_item_key`
- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/stores/source_service|learnloop.db.stores.source_service]] — imports `VERIFIED_STATUSES`, `effective_key_status`, `imports_for_item`, `is_exercise_import`, `reference_content_hash`, `spend_since`; calls `effective_key_status`, `imports_for_item`, `is_exercise_import`, `reference_content_hash`, `spend_since`
- [[Reference/Modules/learnloop/instructional/validation|learnloop.instructional.validation]] — imports `draft_validator`; calls `draft_validator`
- [[Reference/Modules/learnloop/instructional/wiring|learnloop.instructional.wiring]] — imports `disabled_reason`, `find_practice_injections`; calls `disabled_reason`, `find_practice_injections`
- [[Reference/Modules/learnloop/practice_index/catalog|learnloop.practice_index.catalog]] — imports `facet_label`, `registered_facets`; calls `facet_label`, `registered_facets`
- [[Reference/Modules/learnloop/practice_index/coverage|learnloop.practice_index.coverage]] — imports `coverage_targets`; calls `coverage_targets`
- [[Reference/Modules/learnloop/practice_index/paid|learnloop.practice_index.paid]] — imports `FRAMING_TOKENS`
- [[Reference/Modules/learnloop/practice_index/retrieval|learnloop.practice_index.retrieval]] — imports `PracticeConstraints`, `find_practice`; calls `PracticeConstraints`, `find_practice`
- [[Reference/Modules/learnloop/source_retrieval/service_spend|learnloop.source_retrieval.service_spend]] — imports `batch_envelope`, `service_spend`, `subscription_providers`; calls `batch_envelope`, `service_spend`, `subscription_providers`
- [[Reference/Modules/learnloop/vault/loader|learnloop.vault.loader]] — imports `load_vault`; calls `load_vault`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/sources|learnloop.cli.sources]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_exam_protection.py](../../../../../../tests/test_exam_protection.py) — direct import
  - `test_harvest_dry_run_prices_the_rerank_at_its_own_setting`
- [tests/test_source_exercise_rpcs.py](../../../../../../tests/test_source_exercise_rpcs.py) — direct import
  - `test_a_harvest_says_why_picked_exercises_were_not_imported`
  - `test_harvest_and_verify_dry_runs_send_and_write_nothing`
  - `test_harvest_imports_judged_exercises_for_thin_facets`
- [tests/test_source_first_needs.py](../../../../../../tests/test_source_first_needs.py) — direct import
  - `test_batch_commands_honour_their_switches`
- [tests/test_source_service_spend_envelopes.py](../../../../../../tests/test_source_service_spend_envelopes.py) — direct import
  - `test_a_dry_run_reports_numerical_estimates`
  - `test_a_harvest_never_passes_its_max_cost`

## Modification guidance

- Make changes here when the responsibility remains harvest within learnloop.instructional; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/instructional/harvest.py](../../../../../../src/learnloop/instructional/harvest.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

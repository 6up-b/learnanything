---
title: "learnloop.ops.family_proposals"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/ops/family_proposals.py"
source_paths:
  - "src/learnloop/ops/family_proposals.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.ops"
layer: "domain"
concepts:
  - "State and Persistence"
  - "Configuration"
workflows:
  - "Import Canonical Sources"
  - "Build a Study Map"
aliases:
  - "learnloop.ops.family_proposals module"
  - "src/learnloop/ops/family_proposals.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-ops"
---

# `learnloop.ops.family_proposals`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/ops/_package|learnloop.ops]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.ops.family_proposals` exists within [[Reference/Modules/learnloop/ops/_package|learnloop.ops]] to own the behavior summarized by its module contract: Bounded two-pass retrieval-target judgments; never a scheduling authority.

The authoritative system-level explanation remains in [[State and Persistence]], [[Configuration]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/ops/family_proposals.py](../../../../../../src/learnloop/ops/family_proposals.py) |
| Source lines | 638 |
| Owning package | [[Reference/Modules/learnloop/ops/_package|learnloop.ops]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class FamilyVerdict(WireModel)` ([source](../../../../../../src/learnloop/ops/family_proposals.py), line 64)
- `class PairPass` ([source](../../../../../../src/learnloop/ops/family_proposals.py), line 73)
  - `judgment_id(self) -> str` (line 82; public)
- `pair_passes(vault: LoadedVault, pairs: list[tuple[str, str]], settings: dict[str, Any]) -> list[PairPass]` ([source](../../../../../../src/learnloop/ops/family_proposals.py), line 109)
- `unanimous_groups(pairs: list[tuple[str, str]], passes: list[PairPass], saved: dict[str, dict[str, Any]]) -> tuple[list[list[str]], list[list[str]]]` ([source](../../../../../../src/learnloop/ops/family_proposals.py), line 226) — Only complete unanimous components survive; no transitive chaining.
- `propose_families(vault: LoadedVault, *, caps: SpendCaps, dry_run: bool=False, price_per_million: float | None=None, learning_object_id: str | None=None, cancelled: Callable[[], bool] | None=None, client: Any | None=None, judge_revision: str='1') -> dict[str, Any]` ([source](../../../../../../src/learnloop/ops/family_proposals.py), line 277) — Propose, auto-apply unanimous families, and expose only aggregate output.

### Module constants

- `PROMPT_VERSIONS` ([src/learnloop/ops/family_proposals.py](../../../../../../src/learnloop/ops/family_proposals.py), line 57)
- `JUDGE_ROUTE` ([src/learnloop/ops/family_proposals.py](../../../../../../src/learnloop/ops/family_proposals.py), line 60)
- `METERED_JUDGE_TYPES` ([src/learnloop/ops/family_proposals.py](../../../../../../src/learnloop/ops/family_proposals.py), line 61)

## Internal implementation anchors

- `_proposal_lock(root: Path) -> Iterator[None]` ([source](../../../../../../src/learnloop/ops/family_proposals.py), line 87)
- `_item_context(vault: LoadedVault, item: PracticeItem) -> dict[str, Any]` ([source](../../../../../../src/learnloop/ops/family_proposals.py), line 105)
- `_pairs(vault: LoadedVault, items: list[PracticeItem], sqlite_path: Path) -> tuple[list[tuple[str, str]], int]` ([source](../../../../../../src/learnloop/ops/family_proposals.py), line 151)
- `_saved(sqlite_path: Path, passes: list[PairPass]) -> dict[str, dict[str, Any]]` ([source](../../../../../../src/learnloop/ops/family_proposals.py), line 194)
- `_estimate(passes: list[PairPass], price: float | None) -> SpendEstimate` ([source](../../../../../../src/learnloop/ops/family_proposals.py), line 213)
- `_settings(vault: LoadedVault, provider: str, model: str | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/ops/family_proposals.py), line 268)
- `_record_unusable(repository: Repository, current: PairPass, verdict: FamilyVerdict, *, model: str, reason: str, run_id: str, attempt: int) -> None` ([source](../../../../../../src/learnloop/ops/family_proposals.py), line 543) — Ledger a returned verdict that failed semantic admission (review F9).
- `_subscription_estimate(event: dict[str, Any], current: PairPass | None, price_per_million: float | None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/ops/family_proposals.py), line 565) — Codex receipt estimate: reported tokens, else the input-plus-output plan.
- `_apply_groups(vault, repository, pairs, passes, saved, report, cancelled)` ([source](../../../../../../src/learnloop/ops/family_proposals.py), line 575)
- `_reject(repository, group, saved, reason)` ([source](../../../../../../src/learnloop/ops/family_proposals.py), line 624)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/families|learnloop.cli.families]] — imports `propose_families`; statically calls `propose_families`
- [[Reference/Modules/learnloop/content/authoring/source_exercise_import|learnloop.content.authoring.source_exercise_import]] — imports `FamilyVerdict`, `pair_passes`; statically calls `pair_passes`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/errors|learnloop.ai.errors]] — imports `AIInterrupted`, `AIOutputTruncated`, `AIProviderUnavailable`; calls `AIInterrupted`, `AIProviderUnavailable`
- [[Reference/Modules/learnloop/ai/execution|learnloop.ai.execution]] — imports `content_key`, `generation_limit`, `observe_model_calls`, `single_request`; calls `content_key`, `generation_limit`, `observe_model_calls`, `single_request`
- [[Reference/Modules/learnloop/ai/output_budget|learnloop.ai.output_budget]] — imports `TruncationRetry`, `output_budget`, `output_ceiling`; calls `TruncationRetry`, `output_budget`, `output_ceiling`
- [[Reference/Modules/learnloop/ai/routing|learnloop.ai.routing]] — imports `provider_for_task`, `ready_client_for_task`; calls `provider_for_task`, `ready_client_for_task`
- [[Reference/Modules/learnloop/ai/schemas|learnloop.ai.schemas]] — imports `WireModel`
- [[Reference/Modules/learnloop/ai/spend|learnloop.ai.spend]] — imports `ESTIMATED_ONLY`, `SpendBudget`, `SpendCaps`, `SpendEstimate`, `SpendLimitExceeded`, `is_subscription_transport`, `subscription_usage_estimate`; calls `SpendBudget`, `SpendEstimate`, `is_subscription_transport`, `subscription_usage_estimate`
- [[Reference/Modules/learnloop/ai/transport|learnloop.ai.transport]] — imports `BOUNDED_STRUCTURED_COMPLETION`, `execute_structured_operation`, `render_structured_prompt`; calls `execute_structured_operation`, `render_structured_prompt`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/config/schema|learnloop.config.schema]] — imports `DEFAULT_OUTPUT_TOKENS`
- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/stores/embedding_vectors|learnloop.db.stores.embedding_vectors]] — imports `get_vector`, `retrieve`; calls `get_vector`, `retrieve`
- [[Reference/Modules/learnloop/db/stores/judgments|learnloop.db.stores.judgments]] — imports `append_judgment`; calls `append_judgment`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/substrate/families|learnloop.substrate.families]] — imports `FAMILY_JUDGE_PROMPTS`, `GROUPING_POLICY_VERSION`, `apply_family`, `family_item_input`, `sync_authored_families`; calls `apply_family`, `family_item_input`, `sync_authored_families`
- [[Reference/Modules/learnloop/vault/embedding_recipes|learnloop.vault.embedding_recipes]] — imports `embedding_records`; calls `embedding_records`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `ActivityFamily`, `LoadedVault`, `PracticeItem`; calls `ActivityFamily`
- [[Reference/Modules/learnloop/vault/paths|learnloop.vault.paths]] — imports `VaultPaths`; calls `VaultPaths`
- [[Reference/Modules/learnloop/vault/repository|learnloop.vault.repository]] — imports `vault_repository`; calls `vault_repository`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `dataclasses`, `fcntl`, `itertools`, `json`, `math`, `pathlib`, `typing`
- Third party: `pydantic`

## Larger workflow participation

Use this module in context through:

- [[Import Canonical Sources]]
- [[Build a Study Map]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/families|learnloop.cli.families]], [[Reference/Modules/learnloop/content/authoring/source_exercise_import|learnloop.content.authoring.source_exercise_import]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/source_service_fakes.py](../../../../../../tests/source_service_fakes.py) — direct import
- [tests/test_family_proposals.py](../../../../../../tests/test_family_proposals.py) — direct import
  - `test_codex_estimate_falls_back_to_input_plus_output_tokens`
  - `test_codex_route_dry_run_shows_an_estimate_without_a_price`
  - `test_codex_run_still_stops_a_runaway_at_the_call_cap`
  - `test_route_availability_never_changes_preview_model`
- [tests/test_integration_daily_loop_field.py](../../../../../../tests/test_integration_daily_loop_field.py) — direct import
  - `test_retired_reader_card_is_never_a_family_candidate`

## Modification guidance

- Make changes here when the responsibility remains family proposals within learnloop.ops; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/ops/family_proposals.py](../../../../../../src/learnloop/ops/family_proposals.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

---
title: "learnloop.daily_plan.router_retrieval"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/daily_plan/router_retrieval.py"
source_paths:
  - "src/learnloop/daily_plan/router_retrieval.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.daily_plan"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.daily_plan.router_retrieval module"
  - "src/learnloop/daily_plan/router_retrieval.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-daily-plan"
---

# `learnloop.daily_plan.router_retrieval`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/daily_plan/_package|learnloop.daily_plan]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.daily_plan.router_retrieval` exists within [[Reference/Modules/learnloop/daily_plan/_package|learnloop.daily_plan]] to own the behavior summarized by its module contract: Router R2c: similar past decisions (``decision/context`` embeddings, spec §5).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/daily_plan/router_retrieval.py](../../../../../../src/learnloop/daily_plan/router_retrieval.py) |
| Source lines | 422 |
| Owning package | [[Reference/Modules/learnloop/daily_plan/_package|learnloop.daily_plan]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `context_text(card_json: Mapping[str, Any]) -> str` ([source](../../../../../../src/learnloop/daily_plan/router_retrieval.py), line 74) — The decision's canonical context (deterministic; no ids, no times).
- `content_hash(text: str) -> str` ([source](../../../../../../src/learnloop/daily_plan/router_retrieval.py), line 105)
- `decision_context_records(connection: Any) -> list[Any]` ([source](../../../../../../src/learnloop/daily_plan/router_retrieval.py), line 110) — The ``decision/context`` records of every ``plan_block`` decision whose card is stored.
- `include_coin(boundary_key: str, rate: float) -> tuple[float, bool]` ([source](../../../../../../src/learnloop/daily_plan/router_retrieval.py), line 137) — The decision's inclusion coin: ``(u, u < rate)``, seeded by its boundary key.
- `similar_decisions(connection: Any, *, query: Sequence[float], model_id: str, decision_time: str, session_id: str | None, plan_id: str | None, limit: int, vault: Any=None, repository: Any=None) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/daily_plan/router_retrieval.py), line 215) — The top ``limit`` matured similar decisions (G5), each with the line shown to the models.
- `prepare(*, vault: Any, repository: Any, embedding_client: Any, card_json: Mapping[str, Any] | None, boundary_key: str, decision_time: str, session_id: str | None, plan_id: str | None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/daily_plan/router_retrieval.py), line 281) — The prefetch's retrieval: embed the context, retrieve, flip the coin.
- `backfill(vault: Any, repository: Any, *, caps: Any, dry_run: bool, limit: int | None=None, batch_size: int=32, price_per_million: float | None=None, client_factory: Any=None, cancelled: Any=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/daily_plan/router_retrieval.py), line 357) — Embed the ``decision/context`` of every logged decision that has no vector yet.

### Module constants

- `LOG` ([src/learnloop/daily_plan/router_retrieval.py](../../../../../../src/learnloop/daily_plan/router_retrieval.py), line 49)
- `RECORD_KIND` ([src/learnloop/daily_plan/router_retrieval.py](../../../../../../src/learnloop/daily_plan/router_retrieval.py), line 51)
- `FIELD` ([src/learnloop/daily_plan/router_retrieval.py](../../../../../../src/learnloop/daily_plan/router_retrieval.py), line 52)
- `RECIPE` ([src/learnloop/daily_plan/router_retrieval.py](../../../../../../src/learnloop/daily_plan/router_retrieval.py), line 53)
- `VERSION` ([src/learnloop/daily_plan/router_retrieval.py](../../../../../../src/learnloop/daily_plan/router_retrieval.py), line 54)
- `TASK_PREFIX` ([src/learnloop/daily_plan/router_retrieval.py](../../../../../../src/learnloop/daily_plan/router_retrieval.py), line 55)
- `DISABLED` ([src/learnloop/daily_plan/router_retrieval.py](../../../../../../src/learnloop/daily_plan/router_retrieval.py), line 57)
- `INCLUDED` ([src/learnloop/daily_plan/router_retrieval.py](../../../../../../src/learnloop/daily_plan/router_retrieval.py), line 58)
- `WITHHELD` ([src/learnloop/daily_plan/router_retrieval.py](../../../../../../src/learnloop/daily_plan/router_retrieval.py), line 59)
- `UNAVAILABLE` ([src/learnloop/daily_plan/router_retrieval.py](../../../../../../src/learnloop/daily_plan/router_retrieval.py), line 60)

### Explicit exports

`__all__` declares:

- `DISABLED`
- `FIELD`
- `INCLUDED`
- `RECIPE`
- `RECORD_KIND`
- `TASK_PREFIX`
- `UNAVAILABLE`
- `VERSION`
- `WITHHELD`
- `backfill`
- `content_hash`
- `context_text`
- `decision_context_records`
- `include_coin`
- `prepare`
- `similar_decisions`

## Internal implementation anchors

- `_bucket(value: Any, edges: Sequence[float], labels: Sequence[str]) -> str` ([source](../../../../../../src/learnloop/daily_plan/router_retrieval.py), line 63)
- `_matured(connection: Any, decision_time: str, candidate_ids: set[str], vault: Any, repository: Any=None) -> dict[str, dict[str, Any]]` ([source](../../../../../../src/learnloop/daily_plan/router_retrieval.py), line 146) — Of ``candidate_ids``, the decisions whose R_next or R_cold was observed strictly before ``decision_time``, with those outcomes.
- `_outcome_words(value: Any) -> str` ([source](../../../../../../src/learnloop/daily_plan/router_retrieval.py), line 189)
- `_describe(row: Mapping[str, Any], observed: Mapping[str, Any], titles: Mapping[str, str]) -> str` ([source](../../../../../../src/learnloop/daily_plan/router_retrieval.py), line 201)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/router|learnloop.cli.router]] — imports `module`; statically calls `backfill`
- [[Reference/Modules/learnloop/daily_plan/router_chooser|learnloop.daily_plan.router_chooser]] — imports `module`; statically calls `prepare`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/embedding|learnloop.ai.embedding]] — imports `embedding_request_timeout`; calls `embedding_request_timeout`
- [[Reference/Modules/learnloop/daily_plan/router_runtime|learnloop.daily_plan.router_runtime]] — imports `EMBEDDING_TIMEOUT_SECONDS`, `SpendRefused`
- [[Reference/Modules/learnloop/data_capture/reading_exposures|learnloop.data_capture.reading_exposures]] — imports `module`; calls `for_version`
- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/db/stores/embedding_vectors|learnloop.db.stores.embedding_vectors]] — imports `get_vector`, `retrieve`; calls `get_vector`, `retrieve`
- [[Reference/Modules/learnloop/ops/embedding_backfill|learnloop.ops.embedding_backfill]] — imports `backfill_embeddings`; calls `backfill_embeddings`
- [[Reference/Modules/learnloop/router/mixture|learnloop.router.mixture]] — imports `uniform`; calls `uniform`
- [[Reference/Modules/learnloop/router/outcomes|learnloop.router.outcomes]] — imports `derive_router_outcomes`, `outcome_version_for`, `servable_items_by_learning_object`; calls `derive_router_outcomes`, `outcome_version_for`, `servable_items_by_learning_object`
- [[Reference/Modules/learnloop/substrate/canonical_projection|learnloop.substrate.canonical_projection]] — imports `held_for_review_attempts`, `pfc_assessments`; calls `held_for_review_attempts`, `pfc_assessments`
- [[Reference/Modules/learnloop/vault/embedding_recipes|learnloop.vault.embedding_recipes]] — imports `EmbeddingRecord`; calls `EmbeddingRecord`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `hashlib`, `json`, `logging`, `sqlite3`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/router|learnloop.cli.router]], [[Reference/Modules/learnloop/daily_plan/router_chooser|learnloop.daily_plan.router_chooser]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_router_r2c_retrieval.py](../../../../../../tests/test_router_r2c_retrieval.py) — direct import
  - `test_only_matured_decisions_from_another_session_and_plan_are_similar`
  - `test_the_backfill_dry_runs_and_then_embeds_what_is_missing`
  - `test_the_backfill_is_held_to_its_money_cap`
  - `test_the_context_text_has_no_ids_or_times`
  - `test_the_inclusion_coin_is_seeded_logged_and_honours_its_rate`

## Modification guidance

- Make changes here when the responsibility remains router retrieval within learnloop.daily_plan; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/daily_plan/router_retrieval.py](../../../../../../src/learnloop/daily_plan/router_retrieval.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

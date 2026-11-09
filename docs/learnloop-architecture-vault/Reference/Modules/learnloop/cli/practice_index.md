---
title: "learnloop.cli.practice_index"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/cli/practice_index.py"
source_paths:
  - "src/learnloop/cli/practice_index.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.cli"
layer: "adapter"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
  - "Import Canonical Sources"
  - "Inspect Persistent State"
aliases:
  - "learnloop.cli.practice_index module"
  - "src/learnloop/cli/practice_index.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/adapter"
  - "package/learnloop-cli"
---

# `learnloop.cli.practice_index`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/cli/_package|learnloop.cli]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.cli.practice_index` exists within [[Reference/Modules/learnloop/cli/_package|learnloop.cli]] to own the behavior summarized by its module contract: `learnloop practice-index`: facet dossiers, find_practice, coverage and the evaluation.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/cli/practice_index.py](../../../../../../src/learnloop/cli/practice_index.py) |
| Source lines | 295 |
| Owning package | [[Reference/Modules/learnloop/cli/_package|learnloop.cli]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |

## Public API

- `practice_index_dossiers(vault: Annotated[Path, typer.Option('--vault', help='Explicit vault root; use a fixtures-local copy.')], dry_run: Annotated[bool, typer.Option('--dry-run', help='Estimate calls, tokens and cost; no client, migration or data changes.')]=False, facet: Annotated[list[str] | None, typer.Option('--facet', help='Only this facet id; repeatable. Default: every registered facet.')]=None, max_candidates: Annotated[int, typer.Option('--max-candidates', min=0, help='Facets to write in this run.')]=100, max_calls: Annotated[int, typer.Option('--max-calls', min=0)]=100, max_retries: Annotated[int, typer.Option('--max-retries', min=0)]=2, max_tokens: Annotated[int, typer.Option('--max-tokens', min=0, help='Metered routes only.')]=1000000, max_cost_usd: Annotated[float, typer.Option('--max-cost-usd', min=0, help='Metered routes only.')]=1.0, price_per_million: Annotated[float | None, typer.Option('--price-per-million', min=0, help=_PRICE_HELP)]=None, json_output: Annotated[bool, typer.Option('--json')]=False) -> None` ([source](../../../../../../src/learnloop/cli/practice_index.py), line 64) — Write missing or stale facet dossiers (route ai.routing.practice_dossier).
- `practice_index_find(query: Annotated[str, typer.Argument(help='What you want to practise.')], vault: Annotated[Path | None, typer.Option('--vault', help='Vault root.')]=None, limit: Annotated[int | None, typer.Option('--limit', min=1, max=20)]=None, learning_object: Annotated[list[str] | None, typer.Option('--learning-object', help='Repeatable.')]=None, facet: Annotated[list[str] | None, typer.Option('--facet', help='Repeatable.')]=None, mode: Annotated[list[str] | None, typer.Option('--mode', help='Practice mode; repeatable.')]=None, exclude: Annotated[list[str] | None, typer.Option('--exclude', help='Item id; repeatable.')]=None, rerank: Annotated[bool | None, typer.Option('--rerank/--no-rerank', help='Override practice_index.rerank_enabled.')]=None, dry_run: Annotated[bool, typer.Option('--dry-run', help='Plan the query embedding and rerank (cache hits, calls, tokens, cost, caps); no client, migration, request or receipt.')]=False, json_output: Annotated[bool, typer.Option('--json')]=False) -> None` ([source](../../../../../../src/learnloop/cli/practice_index.py), line 104) — Propose practice items for a request (the find_practice agent tool).
- `practice_index_coverage(vault: Annotated[Path | None, typer.Option('--vault', help='Vault root.')]=None, min_eligible: Annotated[int | None, typer.Option('--min-eligible', min=0, help='Default: practice_index.coverage_min_eligible.')]=None, json_output: Annotated[bool, typer.Option('--json')]=False) -> None` ([source](../../../../../../src/learnloop/cli/practice_index.py), line 163) — Facets with few admissible items: the targets for generating more practice.
- `practice_index_status(vault: Annotated[Path | None, typer.Option('--vault', help='Vault root.')]=None, json_output: Annotated[bool, typer.Option('--json')]=False) -> None` ([source](../../../../../../src/learnloop/cli/practice_index.py), line 177) — Dossier freshness, index completeness, the chosen path and usage counts.
- `practice_index_usage(proposal: Annotated[str, typer.Option('--proposal', help='A find_practice proposal id.')], item: Annotated[str, typer.Option('--item', help='A proposed practice item id.')], signal: Annotated[str, typer.Option('--signal', help='practised | skipped | too_easy | not_what_i_asked')], vault: Annotated[Path | None, typer.Option('--vault', help='Vault root.')]=None, json_output: Annotated[bool, typer.Option('--json')]=False) -> None` ([source](../../../../../../src/learnloop/cli/practice_index.py), line 211) — Record a learner's usage signal on a proposed item (judgment_ledger).
- `practice_index_eval(vault: Annotated[Path, typer.Option('--vault', help='Explicit vault root; use a fixtures-local copy.')], dry_run: Annotated[bool, typer.Option('--dry-run', help='Estimate calls, tokens and cost; no client, migration or data changes.')]=False, queries: Annotated[int, typer.Option('--queries', min=0, help='Target size of the LLM-written held-out query set.')]=40, logged_queries: Annotated[int, typer.Option('--logged-queries', min=0, help='Real find_practice requests to include.')]=20, seed: Annotated[int, typer.Option('--seed')]=0, bootstrap_samples: Annotated[int, typer.Option('--bootstrap-samples', min=1)]=1000, output_dir: Annotated[Path, typer.Option('--output-dir', help='Aggregate-only report destination.')]=Path('fixtures-local/reports'), max_candidates: Annotated[int, typer.Option('--max-candidates', min=0)]=500, max_pairs: Annotated[int, typer.Option('--max-pairs', min=0, help='Query-item label pairs.')]=4000, max_calls: Annotated[int, typer.Option('--max-calls', min=0)]=400, max_retries: Annotated[int, typer.Option('--max-retries', min=0)]=4, max_tokens: Annotated[int, typer.Option('--max-tokens', min=0, help='Metered routes only.')]=4000000, max_cost_usd: Annotated[float, typer.Option('--max-cost-usd', min=0, help='Metered routes only.')]=1.0, price_per_million: Annotated[float | None, typer.Option('--price-per-million', min=0, help=_PRICE_HELP)]=None, embedding_price_per_million: Annotated[float | None, typer.Option('--embedding-price-per-million', min=0, help=_EMBEDDING_PRICE_HELP)]=None, json_output: Annotated[bool, typer.Option('--json')]=False) -> None` ([source](../../../../../../src/learnloop/cli/practice_index.py), line 232) — Retrieval evaluation: dossier two-level search vs direct item search.
- `practice_index_tool_spec() -> None` ([source](../../../../../../src/learnloop/cli/practice_index.py), line 291) — Print the find_practice agent-tool declaration (JSON schema).

### Module constants

- `_PRICE_HELP` ([src/learnloop/cli/practice_index.py](../../../../../../src/learnloop/cli/practice_index.py), line 30)
- `_EMBEDDING_PRICE_HELP` ([src/learnloop/cli/practice_index.py](../../../../../../src/learnloop/cli/practice_index.py), line 36)

## Internal implementation anchors

- `_emit(report: dict[str, Any], json_output: bool) -> None` ([source](../../../../../../src/learnloop/cli/practice_index.py), line 42)
- `_loaded(vault: Path)` ([source](../../../../../../src/learnloop/cli/practice_index.py), line 47)
- `_exit_for(report: dict[str, Any], ok: set[str]) -> None` ([source](../../../../../../src/learnloop/cli/practice_index.py), line 56)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/__init__|learnloop.cli]] — imports `practice_index_app`
- [[Reference/Modules/learnloop/cli/evaluation|learnloop.cli.evaluation]] — imports `practice_index_eval`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/spend|learnloop.ai.spend]] — imports `SpendCaps`; calls `SpendCaps`
- [[Reference/Modules/learnloop/cli/embeddings|learnloop.cli.embeddings]] — imports `_cancellation`; calls `_cancellation`
- [[Reference/Modules/learnloop/cli/runtime|learnloop.cli.runtime]] — imports `_repository`, `_root`; calls `_repository`, `_root`
- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/db/stores/practice_index|learnloop.db.stores.practice_index]] — imports `latest_evaluation`; calls `latest_evaluation`
- [[Reference/Modules/learnloop/practice_index/coverage|learnloop.practice_index.coverage]] — imports `coverage_report`; calls `coverage_report`
- [[Reference/Modules/learnloop/practice_index/dossiers|learnloop.practice_index.dossiers]] — imports `dossier_status`, `generate_dossiers`; calls `dossier_status`, `generate_dossiers`
- [[Reference/Modules/learnloop/practice_index/evaluation|learnloop.practice_index.evaluation]] — imports `run_retrieval_evaluation`; calls `run_retrieval_evaluation`
- [[Reference/Modules/learnloop/practice_index/paid|learnloop.practice_index.paid]] — imports `planning_repository`; calls `planning_repository`
- [[Reference/Modules/learnloop/practice_index/retrieval|learnloop.practice_index.retrieval]] — imports `PracticeConstraints`, `choose_path`, `find_practice`, `load_snapshot`, `plan_find_practice`; calls `PracticeConstraints`, `choose_path`, `find_practice`, `load_snapshot`, `plan_find_practice`
- [[Reference/Modules/learnloop/practice_index/tool|learnloop.practice_index.tool]] — imports `FIND_PRACTICE_TOOL`
- [[Reference/Modules/learnloop/practice_index/usage|learnloop.practice_index.usage]] — imports `record_practice_usage`, `usage_summary`; calls `record_practice_usage`, `usage_summary`
- [[Reference/Modules/learnloop/vault/loader|learnloop.vault.loader]] — imports `load_vault`; calls `load_vault`
- [[Reference/Modules/learnloop/vault/paths|learnloop.vault.paths]] — imports `VaultPaths`; calls `VaultPaths`

### Platform and third-party dependencies

- Standard library: `__future__`, `contextlib`, `json`, `pathlib`, `typing`
- Third party: `typer`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]
- [[Import Canonical Sources]]
- [[Inspect Persistent State]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/__init__|learnloop.cli]], [[Reference/Modules/learnloop/cli/evaluation|learnloop.cli.evaluation]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

No test imports this module directly. These tests exercise a direct production consumer:

- [tests/test_cli_generate_practice.py](../../../../../../tests/test_cli_generate_practice.py) — imports consumer [[Reference/Modules/learnloop/cli/__init__|learnloop.cli]]
- [tests/test_cli_ingest.py](../../../../../../tests/test_cli_ingest.py) — imports consumer [[Reference/Modules/learnloop/cli/__init__|learnloop.cli]]
- [tests/test_facet_identity_ingest.py](../../../../../../tests/test_facet_identity_ingest.py) — imports consumer [[Reference/Modules/learnloop/cli/__init__|learnloop.cli]]
- [tests/test_graph_nomination_ingest.py](../../../../../../tests/test_graph_nomination_ingest.py) — imports consumer [[Reference/Modules/learnloop/cli/__init__|learnloop.cli]]
- [tests/test_model_call_receipt_owners.py](../../../../../../tests/test_model_call_receipt_owners.py) — imports consumer [[Reference/Modules/learnloop/cli/__init__|learnloop.cli]]
- [tests/test_route_rules_in_grader.py](../../../../../../tests/test_route_rules_in_grader.py) — imports consumer [[Reference/Modules/learnloop/cli/__init__|learnloop.cli]]
- [tests/test_stuck_prompt.py](../../../../../../tests/test_stuck_prompt.py) — imports consumer [[Reference/Modules/learnloop/cli/__init__|learnloop.cli]]
- [tests/test_teach_back_generation.py](../../../../../../tests/test_teach_back_generation.py) — imports consumer [[Reference/Modules/learnloop/cli/__init__|learnloop.cli]]

## Modification guidance

- Change request/response adaptation or presentation here. Put reusable learning policy in its domain package, not in the adapter.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/cli/practice_index.py](../../../../../../src/learnloop/cli/practice_index.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

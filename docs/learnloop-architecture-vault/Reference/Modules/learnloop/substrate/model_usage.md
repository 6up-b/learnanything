---
title: "learnloop.substrate.model_usage"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/substrate/model_usage.py"
source_paths:
  - "src/learnloop/substrate/model_usage.py"
source_commit: "5b1184a8a7c8932f6468766c2f59599d01f1b8cc"
source_commit_timestamp: "2026-09-23T16:08:23-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-09-23"
package: "learnloop.substrate"
layer: "domain"
concepts:
  - "Learning System"
  - "State and Persistence"
workflows:
  - "Inspect Persistent State"
  - "Rebuild and Shadow Compare"
aliases:
  - "learnloop.substrate.model_usage module"
  - "src/learnloop/substrate/model_usage.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-substrate"
---

# `learnloop.substrate.model_usage`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/substrate/_package|learnloop.substrate]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.substrate.model_usage` exists within [[Reference/Modules/learnloop/substrate/_package|learnloop.substrate]] to own the behavior summarized by its module contract: Read-only model-usage report over the durable model-call receipts.

The authoritative system-level explanation remains in [[Learning System]], [[State and Persistence]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/substrate/model_usage.py](../../../../../../src/learnloop/substrate/model_usage.py) |
| Source lines | 338 |
| Owning package | [[Reference/Modules/learnloop/substrate/_package|learnloop.substrate]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `5b1184a8a7c8932f6468766c2f59599d01f1b8cc` |
| Commit timestamp | `2026-09-23T16:08:23-04:00` |

## Public API

- `model_usage_report(sqlite_path: Path, *, budgets: Mapping[str, int | None], since: datetime | None=None, purpose_prefix: str | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/substrate/model_usage.py), line 69) — Read every receipt in one read-only transaction and summarize it.
- `read_receipts(connection: sqlite3.Connection) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/substrate/model_usage.py), line 86) — All receipts, with columns an older schema lacks read as NULL.
- `build_usage_report(receipts: Iterable[Mapping[str, Any]], *, budgets: Mapping[str, int | None], since: datetime | None=None, purpose_prefix: str | None=None, generated_at: str | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/substrate/model_usage.py), line 97) — Summarize receipts by root purpose, by synthesis run, and by coverage.
- `distribution(values: Iterable[int | float | None]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/substrate/model_usage.py), line 173) — Mean, median, nearest-rank p95 and max over the known values only.

### Module constants

- `REPORT_VERSION` ([src/learnloop/substrate/model_usage.py](../../../../../../src/learnloop/substrate/model_usage.py), line 31)
- `SYNTHESIS_PASS_PURPOSE` ([src/learnloop/substrate/model_usage.py](../../../../../../src/learnloop/substrate/model_usage.py), line 37)
- `GRAPH_STRUCTURING_PURPOSE` ([src/learnloop/substrate/model_usage.py](../../../../../../src/learnloop/substrate/model_usage.py), line 38)
- `SYNTHESIS_RUN_PURPOSES` ([src/learnloop/substrate/model_usage.py](../../../../../../src/learnloop/substrate/model_usage.py), line 39)
- `SYNTHESIS_BUDGET_FIELDS` ([src/learnloop/substrate/model_usage.py](../../../../../../src/learnloop/substrate/model_usage.py), line 41)
- `TOKEN_FIELDS` ([src/learnloop/substrate/model_usage.py](../../../../../../src/learnloop/substrate/model_usage.py), line 47)
- `STATUSES` ([src/learnloop/substrate/model_usage.py](../../../../../../src/learnloop/substrate/model_usage.py), line 48)
- `_RECEIPT_COLUMNS` ([src/learnloop/substrate/model_usage.py](../../../../../../src/learnloop/substrate/model_usage.py), line 50)

## Internal implementation anchors

- `class _Chains` ([source](../../../../../../src/learnloop/substrate/model_usage.py), line 57) — Each receipt's root and whether it is a leaf (a request with usage).
- `_link_chains(receipts: Iterable[Mapping[str, Any]]) -> _Chains` ([source](../../../../../../src/learnloop/substrate/model_usage.py), line 140)
- `_root_in_scope(root: Mapping[str, Any], *, since: datetime | None, purpose_prefix: str | None) -> bool` ([source](../../../../../../src/learnloop/substrate/model_usage.py), line 159)
- `_usage_unknown(request: Mapping[str, Any]) -> bool` ([source](../../../../../../src/learnloop/substrate/model_usage.py), line 169)
- `_provider_and_model(request: Mapping[str, Any], root: Mapping[str, Any]) -> tuple[str | None, str | None]` ([source](../../../../../../src/learnloop/substrate/model_usage.py), line 190)
- `_by_purpose(requests: list[dict[str, Any]], chains: _Chains) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/substrate/model_usage.py), line 194)
- `_synthesis_runs(in_scope_roots: set[str], chains: _Chains, budgets: Mapping[str, int | None]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/substrate/model_usage.py), line 219)
- `_run_budgets(roots: list[dict[str, Any]], config_budgets: Mapping[str, int | None]) -> tuple[dict[str, Any], str]` ([source](../../../../../../src/learnloop/substrate/model_usage.py), line 231) — The budgets the run declared on its receipts, else the current config.
- `_synthesis_run(owner: tuple[str, str], roots: list[dict[str, Any]], chains: _Chains, config_budgets: Mapping[str, int | None]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/substrate/model_usage.py), line 247)
- `_coverage(requests: list[dict[str, Any]], chains: _Chains) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/substrate/model_usage.py), line 287) — Where usage goes unreported, by root purpose, request purpose and provider.
- `_known_sum(requests: Iterable[Mapping[str, Any]], field: str) -> int | None` ([source](../../../../../../src/learnloop/substrate/model_usage.py), line 324) — The sum of the reported values, or None when no request reported one.
- `_ratio(value: int | None, budget: int | None) -> float | None` ([source](../../../../../../src/learnloop/substrate/model_usage.py), line 331)
- `_sort_key(values: tuple[Any, ...]) -> tuple[str, ...]` ([source](../../../../../../src/learnloop/substrate/model_usage.py), line 337)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/data|learnloop.cli.data]] — imports `SYNTHESIS_BUDGET_FIELDS`, `model_usage_report`; statically calls `model_usage_report`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `parse_utc`, `utc_now_iso`; calls `parse_utc`, `utc_now_iso`
- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `dataclasses`, `datetime`, `json`, `math`, `pathlib`, `sqlite3`, `statistics`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Inspect Persistent State]]
- [[Rebuild and Shadow Compare]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/data|learnloop.cli.data]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_model_usage_report.py](../../../../../../tests/test_model_usage_report.py) — direct import
  - `test_cli_reads_budgets_from_the_effective_config_and_opens_read_only`
  - `test_distribution_uses_nearest_rank_p95`
  - `test_openai_requests_are_attributed_to_their_root_purpose`
  - `test_purpose_prefix_and_since_filter_whole_chains`
  - `test_report_ordering_is_deterministic`
  - `test_runs_are_compared_with_the_budgets_recorded_on_their_receipts`
  - `test_synthesis_purposes_match_the_synthesis_operations`
  - `test_synthesis_runs_compare_measured_tokens_with_the_budgets`
- [tests/test_sqlite_wal.py](../../../../../../tests/test_sqlite_wal.py) — direct import
  - `test_read_only_reports_work_in_a_read_only_vault`

## Modification guidance

- Change model usage policy here when substrate owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/substrate/model_usage.py](../../../../../../src/learnloop/substrate/model_usage.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

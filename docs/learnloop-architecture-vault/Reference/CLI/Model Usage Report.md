---
title: "Model Usage Report"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
config_schema_version: 2
schema_head: 165
source_commit: "922f2d187b5839289a7de8ea6d73ce679998e7e8"
source_commit_timestamp: "2026-09-23T15:53:48-04:00"
last_verified: "2026-09-23"
aliases:
  - "learnloop usage"
  - "Token usage report"
source_paths:
  - "src/learnloop/substrate/model_usage.py"
  - "src/learnloop/cli/data.py"
  - "src/learnloop/ai/execution.py"
  - "src/learnloop/reader/reader_requests.py"
  - "src/learnloop/cli/receipts.py"
  - "src/learnloop/tui/state.py"
  - "migrations/165_model_call_budgets.sql"
  - "tests/test_model_usage_report.py"
  - "tests/test_model_call_receipt_owners.py"
tags:
  - "learnloop/cli/inspection"
  - "learnloop/ai/usage"
  - "learnloop/status/active"
---

# Model Usage Report

`learnloop usage` summarizes the [[model_call_receipts]] table so that token budgets can be sized from measured usage. It opens the database read-only and reads every receipt in one transaction, the same way `data-quality` does, so it never changes the vault. ^usage-contract

## Command

```bash
uv run learnloop usage --vault "$VAULT"                  # terminal summary
uv run learnloop usage --vault "$VAULT" --json           # stable JSON (report_version 2)
uv run learnloop usage --vault "$VAULT" --since 2026-09-01 --purpose source_set
```

- `--since` takes an ISO date or time. A value without an offset is read as UTC. It keeps operations whose root receipt started at or after that moment.
- `--purpose` keeps operations whose root purpose starts with the prefix. Request purposes such as `chat_request` are not filter keys.

## How receipts are counted

Receipts form chains through `parent_call_id`. The root is the feature operation (for example `source_set_synthesis` or `tutor_qa`). The leaves are the physical requests: `chat_request` for the OpenAI-compatible adapter, `<purpose>:sdk_turn` for the Codex SDK. The Codex HTTP adapter reports usage on the operation's own receipt, so there the root is also the request. Only requests carry usage, and each request is counted under its root's purpose. The JSON keeps the request purposes under `request_purposes`.

NULL usage means the provider did not report it; it is not zero. Each token statistic has a `known` count of the requests it covers, and `usage_unknown` counts requests that reported neither input nor output tokens.

## Sections

1. **`by_purpose`**, one row per root purpose, provider and model:
   - request and operation counts;
   - status counts (`completed`, `failed`, `truncated`, `interrupted`, and `started` for unfinished);
   - mean, median, nearest-rank p95 and max for input, output, cached-input, cache-write and reasoning tokens;
   - total cost where the provider reported it.
2. **`synthesis_runs`**: the `source_set_synthesis` and `concept_graph_structuring` operations that share one receipt owner (an ingest job, a sidecar request or a CLI command run). Each run lists its passes, total input and output tokens, and its largest synthesis pass. These are divided by the run's budgets: `synthesis_total_input_ceiling`, `synthesis_output_tokens`, `synthesis_shard_input_tokens` and `synthesis_shard_output_tokens`.
   - The budgets come from the run's own receipts (`budget_source: "receipt"`). `create_study_map` records the budgets in force, including per-request overrides, in `model_call_receipts.budget_json` on each operation's root receipt.
   - A run whose receipts carry no budgets is compared with the vault's current effective `[ingest.budgets]` (`budget_source: "config"`).
   - An unlimited run records only its shard input size, so its ceiling ratios are empty.
3. **`coverage`**: request counts by root purpose, request purpose and provider. When a completed request reports no usage, the provider path is not reporting it. The terminal summary lists only the groups with such gaps.

## Limits

- Receipts exist only where an observer is installed. That covers every sidecar RPC, the ingest runner and its inventory workers, each drained reader preset request, every CLI command run (`owner_kind` `cli`, owner id `<command path>:<ulid>`) and each TUI session (`owner_kind` `tui`). See [[AI Architecture#Provenance and usage]].
- A CLI command whose vault database is below migration 165 cannot record receipts. Its model calls still run. The command prints one line to stderr naming the current migration and asking you to run `learnloop upgrade --vault <root>`.
- The budgets govern the synthesis code's own pre-request estimates. The report divides the provider's reported tokens by the same budgets, so a ratio near 1 means the run came close to its ceiling. It does not mean the run was refused.

## Related notes

- [[Inspect Persistent State]]
- [[Build a Study Map]]
- [[model_call_receipts]]

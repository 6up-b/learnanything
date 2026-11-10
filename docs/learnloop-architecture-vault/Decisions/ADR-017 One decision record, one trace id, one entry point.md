---
title: ADR-017 One decision record, one trace id, one entry point
aliases:
  - Decision record
  - decision_records
  - Why x and not y
status: active
doc_version: 1.0.0
implementation_version: mvp-0.57
decision_date: 2026-11-10
decision_status: accepted
last_reviewed: 2026-11-10
source_commit: 0f11cb1053075cf6a271edf65355265f5732a059
source_commit_timestamp: "2026-11-10T04:17:59-05:00"
source_paths:
  - docs/specs/refactor_strategy_v3.md
  - src/learnloop/db/table_roles.py
  - src/learnloop/adaptive_difficulty/protected_tables.py
  - src/learnloop/ai/execution.py
  - src/learnloop/db/stores/model_calls.py
  - src/learnloop/cli/app.py
tags:
  - learnloop/decision
  - learnloop/debugging
  - learnloop/persistence
---

# ADR-017 One decision record, one trace id, one entry point

## Context

The owner's question about any choice LearnLoop makes is "why x and not y?". In November 2026 four real cases could not be answered from stored data alone (`docs/specs/refactor_strategy_v3.md` §3.6): router LLM answers discarded by the 8 s timeout, an offer withdrawn with `forced_items`, a figure stored failed for a bad prediction, and automatic figure pre-builds that started after a run of skips.

The architecture map (`docs/reviews/architecture-map-2026-11-08.md` §4.3, §4.6) found why:

- **No common trace id.** A model call's receipt names the router's boundary key, so a decision reaches its calls only through a manual JSON join (break 2). A plan decision names no triggering attempt (break 1). Pending reads have no id (break 3).
- **Failure paths are where records stop.** A chooser crash, a timeout, a provider failure, a filter's exclusions and a refused request leave no row.
- **Inspection is per subsystem,** and `learnloop why` ran `sync_vault_state` and startup maintenance before it read, so asking a question wrote to the vault.

## Decision

**One record, one trace id, one entry point.** It is the one new concept the refactor adds, because no existing mechanism can answer the four cases.

### The record

`decision_records` (migration 253) holds one row per meaningful decision boundary. A decision-producing function returns a `provenance.DecisionRecord` (a frozen dataclass) and the imperative shell writes it. Rich domain rows stay where they are (replay and the playbook depend on them) and the record points to them. For failures, exclusions and refusals, which have no domain row, the record is the row.

| Column | What it holds |
|---|---|
| `id` | ULID; the record's handle in `why` |
| `trace_id` | One learner-visible action and its background work |
| `parent_id` | The record that caused this one, possibly in an earlier trace |
| `kind` | `plan_block`, `model_answer`, `offer_withdrawn`, `slate`, `figure_prebuild`, `figure_author`, `grade`, ...: constants beside the code that writes them |
| `status` | One of `chosen`, `fallback`, `excluded`, `withdrawn`, `timeout`, `discarded`, `failed`, `refused`, `deferred` (a CHECK) |
| `subject_kind`, `subject_id` | `attempt`, `item`, `block`, `offer`, `figure`, `job`: how a learner-visible thing finds its records |
| `chosen_ref` | What won, or null |
| `decided_by` | The rule, policy or route (`lane_quota`, `mixture`, `router_llm`, `prefetch_eu_v1`) |
| `rule` | Why, as a named code (`chooser_error`, `forced_items`, `no_measured_latency`) |
| `alternatives_json` | `[{ref, p, score, lost_by}]`, capped at 50 with an overflow count per rule |
| `facts_json` | The inputs as of then, as numbers, ids and codes |
| `versions_json` | Tag, policy or prompt version, model id, seed, and the switches that changed this decision |
| `detail_table`, `detail_id` | The rich row (`router_decisions`, `ad_selections`, `interactive_figures`, ...) |
| `error_type`, `error_where` | On failure: the exception class and `module:function:line`. No message: a traceback can quote what the code read, so it goes to the log at DEBUG with the trace id |
| `created_at` | |

"What happened next" is not a column: it is the next record whose `parent_id` is this one, the detail row's own outcome, or a presentation and attempt reached from the subject.

**A record never changes a decision.** `provenance.write(connection, record)` joins the caller's transaction; `db.stores.provenance.write_decision` takes its own short one. Either way a failed write logs a warning with the trace id and returns; it never raises into the decision. A record holds no prose: no learner text, item text, prompt or model output (`provenance.check_no_prose`, and a test that plants item text). Payloads stay in `model_call_receipts`, under their existing retention.

### The trace id

A ULID in a `ContextVar` (`provenance.current_trace()`), **born** once per learner-visible action:

- the desktop sidecar, per RPC (`learnloop_sidecar.server._handle`);
- the phone host, per request (`learnloop_mobile.runtime.MobileRuntime._dispatch`, which hands its trace to the same `_handle`);
- the MCP server, per tool call (`learnloop_mcp.server`'s `run`);
- the CLI, per command (the root callback).

It is **carried** by the `ContextVar`: threads started in a copied context (the router's jobs, background exam grading) inherit it. The post-attempt worker's long-lived threads give each job a trace of its own, so a job never carries the RPC that first woke the worker. Until a job's enqueue writes a `job_enqueued` record (B7), a background job's trace is its own.

**Model calls** carry it in a real column, `model_call_receipts.trace_id` (nullable), set when the call starts (`ai.execution`) and written by `record_model_event`. That closes break 2 without moving the decision id, which feeds the mix's seed. **Logs** carry it: the sidecar's `log_event` adds `trace_id` to every structured event.

### Replay and persisted meaning

Writing a record changes no replayed meaning, each with a test (`tests/test_provenance.py`):

- the role is `RECEIPT` (`db/table_roles.py`): append-only (two triggers refuse UPDATE and DELETE), never cleared by rebuild;
- no replay or rebuild code can reach the table: the import closure of the rebuild orchestrator and the upgrade chain never imports `learnloop.provenance` or the store, and no module in that closure names `decision_records`;
- AD's guard classifies it `DENIED` (`adaptive_difficulty/protected_tables.py`), so no AD operation reads it;
- `model_call_receipts.trace_id` is nullable and no projection reads it.

No successor tag: the table is a receipt and the column is accounting (`docs/algorithm-change-playbook.md` applies to persisted meaning, which neither carries). Old decisions keep their rows and get **no backfilled records**: a record written now would claim to know inputs nobody stored. `why` labels what it reconstructs from old rows instead.

### The entry point

`learnloop why [TARGET] [--kind K] [--json] --vault V` is a **pure read**: `Repository.attach(..., read_only=True)`, no `sync_vault_state`, no startup maintenance. `TARGET` is `latest` (the default), a trace id, a record id, `<subject_kind>:<id>`, or a practice item id (today's scheduler explanation, kept). For a trace it lists the records and the trace's model calls, joined by `trace_id` (ids, purposes, statuses, times; never payloads). Rows with no `trace_id` (every call before migration 253) are not joined; the old boundary-key reading stays where it is (`learnloop router trace`) until B9 folds it in as a "reconstructed" view.

B9 completes it: the sidecar's read-only `why.get` RPC (ids, numbers and codes; not on the phone's allowlist), `--payload` on the desktop CLI, and `learnloop router trace` and `trace-evidence` as views over the same reader.

### Storage and protection

Rows are small: ids, numbers and capped lists, exclusions aggregated by rule. The strategy's estimate is at most about 1 KB a row and about 30 rows per attempt cycle; B6 measures it on a copy-shaped journey, and tightens what it records by rule if growth passes 5% of a vault's database a month. `router.payload_retention_days` may prune `alternatives_json` and `facts_json` on old rows and keep the row. No model context reads the table and no grader context can.

## Consequences

- One `why` answers from new rows once each boundary writes its record (arc B, B2-B8, in order of debugging value). B1 writes none; it builds the table, the trace and the reader.
- Every receipt from a traced action carries its trace, so "which calls belong to this decision" is a join on one column, and "which calls finished after the decision" is a comparison of times (S4, S5 derive at read, with no new write).
- A writer inside an AD operation must write outside the operation or add the table to `AD_WRITABLE` (write only): the guard would otherwise poison the operation, which would change what is served.
- `decision_records` is never the system of record: ledgers and receipts stay immutable and authoritative, and nothing replays from it.

## What it replaces

- **Kept:** `router_decisions` and payloads, `router_objective_traces`, `ad_selections` (the model for the shape), `judgment_ledger`, `plan_presentations`, the causal receipts.
- **Gone:** the manual JSON join from decision to receipt (for new rows), `why`'s writes, and, as B2-B9 land, free-text `owner_id` as the join, AD's JSONL denial log if nothing else reads it, and per-subsystem entry points as separate code.
- **Not done:** trace spans or OpenTelemetry (a dependency and a concept for a single-user app), a record at every function or per protection read, prompts or free text in records, and renaming "decision" elsewhere (`router_decisions` stays).

## B8: boundaries with no record, and why not

B8 reads the remaining boundaries (teacher lessons and checks, Reader retrieval, ingest routing, AI route fallback, retries, re-read and alias resolution, curriculum path, FSRS rating and elapsed) and writes here, for each one it leaves without a record, why not. Until B8 lands this list is open.

## Related notes

- [[ADR-003 Explicit table roles govern rebuild]]
- [[ADR-007 Immutable evidence and append-only correction]]
- [[Inspect Persistent State]]
- [[Design Decision Index]]

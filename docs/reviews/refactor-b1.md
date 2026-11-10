# Refactor B1: the record, the trace id, the entry point

Step B1 of `docs/specs/refactor_strategy_v3.md` (§2.4, design in §3), the first step of arc B ("why x and not y"). Branch `refactor/b1-decision-record`, based on main `0f11cb1053` (arc A landed and closed). Decision: `Decisions/ADR-017 One decision record, one trace id, one entry point` (written first, committed alone).

**Result.** One table, one dataclass, one `ContextVar` and one read function exist, every learner-visible action runs under a trace that reaches its model calls and logs, and `learnloop why` is a pure read. B1 writes no record from production code: B2-B8 add the writers, each at its boundary. Nothing served changes: the shadow rebuild and the draw-for-draw replay match main on all three vault copies, apart from generated ids, wall times and the new column.

## The shape as built

**`src/learnloop/provenance.py`** (a leaf: it imports only `learnloop.ids`, pinned by an AST test and the import-linter `primitives-have-no-internal-dependencies` contract, which now lists it):

| Name | What it is |
|---|---|
| `DecisionRecord` | Frozen dataclass with §3.2's columns (`alternatives`, `facts`, `versions` as Python values). `id`, `trace_id` and `created_at` fill in at write time when `None` |
| `current_trace()`, `trace_scope(trace_id=None)` | The trace `ContextVar`; `trace_scope` sets a given trace or births a ULID, and restores the previous value on exit |
| `write(connection, record)` | Never raises. Checks the status against `STATUSES` and every value with `check_no_prose`, caps alternatives at 50 (the overflow counted per `lost_by` in `facts.alternatives_overflow`), then inserts inside `SAVEPOINT decision_record`: it joins the caller's transaction, or is its own short one; a failed insert rolls back to the savepoint alone. Any failure logs `decision record <kind> not written (trace <id>): <ExceptionType>` and returns `None` |
| `read(connection, target="latest", kind=None)` | `latest` (the newest record's trace), `<subject_kind>:<id>`, a record id (its trace) or a trace id; oldest first; empty below migration 253 |
| `check_no_prose`, `where`, `cap_alternatives` | A value is an id, a number or a code constant (`[A-Za-z0-9_.:/@+#=-]{1,160}`, so no whitespace); `where(exc)` gives `module:function:line` of the raising frame, never the message |

**Migration 253** (`253_decision_records.sql`): `decision_records` with §3.2's columns, `status` CHECKed against the nine statuses, the three JSON columns CHECKed `json_valid` with `[]`/`{}` defaults, four indexes (trace, subject, parent, kind; each ordered by `created_at, id`) and two triggers refusing UPDATE and DELETE. `model_call_receipts.trace_id TEXT` (nullable) with a partial index `WHERE trace_id IS NOT NULL`. RECEIPT in `db/table_roles.py`; DENIED in AD's `protected_tables.py` and not in `AD_WRITABLE`; columns classed in `column_classes.py` (the JSON columns as content, though the check keeps them to ids and numbers); `trace_id` added to `model_call_receipts`' metadata columns. No successor tag: a receipt table and an accounting column carry no persisted meaning (`docs/algorithm-change-playbook.md` governs scoring, scheduling and projections, none of which reads either).

**`src/learnloop/db/stores/provenance.py`**: `write_decision(repository, record)` (joins the repository's pinned or atomic connection, or takes its own short transaction; never raises) and `trace_model_calls(connection, trace_ids)` (receipt metadata only: ids, owner, purpose, provider, model, status, error type, times, tokens, cost; never `input_text`, `schema_json` or `output_text`).

**The head fixture** was upgraded in place to 253 by CLAUDE.md's procedure (backup-API copy, `apply_migrations` under `UPGRADE_SCRATCH_COPY` applying `[253]` only, `wal_checkpoint(TRUNCATE)` (0, 0, 0), `journal_mode=DELETE`, header bytes 1/1, `integrity_check` ok, `foreign_key_check` empty, no companion files), with a README section. Seventeen earlier migrations' "nothing else changed" diffs now subtract `B1_ADDED_OBJECTS`, and sixteen read `B1_ALTERED_TABLES` (`model_call_receipts`): an exact-pattern scripted edit beside the existing `IH3_ADDED_OBJECTS` and `TE1_ALTERED_TABLES` terms, each placement checked for operator precedence first. `test_architecture`'s SQL-writer registry lists `src/learnloop/provenance.py`.

## Entry points wired

| Where | Map line | At this tip | How |
|---|---|---|---|
| Desktop sidecar, per RPC | `learnloop_sidecar/server.py:55` | `_handle` | `_handle(ctx, request, *, trace_id=None)` runs the old body (now `_handle_request`) inside `trace_scope(trace_id)` |
| Phone host, per request | `learnloop_mobile/runtime.py:250` | `HostRuntime._dispatch` | births the trace before the context load and `refresh_if_content_changed`, and hands it to `_handle(..., trace_id=)` so the handler continues it |
| MCP, per tool call | `learnloop_mcp/server.py:364` | `ToolCalls.run` | `run` wraps the old body (now `_run`) in `trace_scope()` |
| CLI, per command | the root callback; `cli/app.py:2407` (`why`, now at 2451) | `_record_command_model_calls` | `ctx.with_resource(provenance.trace_scope())` first, so it ends when the command's context closes (two `CliRunner` invocations in one test get two traces and leave none behind) |
| Model calls | `ai/execution.py`, `record_model_event` (`db/stores/model_calls.py:45`) | `_observed_call`, `ModelCallStoreMixin.record_model_event` | the start event carries `trace_id: current_trace()`; the store writes the column only when it is set, so an untraced call still records on a database below 253 (the labels' pattern) |
| Logs | `learnloop_sidecar/logging.py:84` | `log_event` | `fields.setdefault("trace_id", current_trace())`; a `None` is dropped with the other `None` fields |
| Post-attempt jobs (not on the map's list) | | `PostAttemptWorker._with_busy_retry` | each job runs under a trace of its own. The worker's slots are long-lived threads started in a copy of the RPC context that first woke them (`post_attempt_worker.py:102`), so without this every diagnosis, gap and follow-up job would carry that one request's trace forever. B7's `job_enqueued` record replaces "its own" with "the enqueuer's" |

Threads that already start in a copied context (the router's jobs at `router_runtime.py:495`, `objective_chooser.py:849`, `router_chooser.py:238`, the exam grader) inherit the trace with no change; a bare `threading.Thread` starts with none (tested).

## What `why` reads

`learnloop why [TARGET] [--kind K] [--json] --vault V`. The positional keeps its name `practice_item_id` (renaming a positional is an incompatible CLI change); it became optional with a `None` default, and `--kind` is a new optional option, both compatible (`tests/cli_surface.json` unchanged).

- **Pure read.** `Repository.attach(sqlite_path, read_only=True)`; the `sync_vault_state` and `run_startup_maintenance` calls are deleted. Scheduler explanations already ran with `persist_explanations=False`. A practice item id still prints today's scheduler explanation (the JSON shape is unchanged, so `test_cli_json`'s exact key set holds), or the latest stored one.
- **New rows.** `latest` (the default), a trace id, a record id or `<kind>:<id>` read `decision_records` through `provenance.read`, plus the traces' model calls through `trace_model_calls`, joined on `model_call_receipts.trace_id`. This is the join that replaces, for new rows, the manual JSON join from a router decision's `detail_json.boundary_key` to the receipts' `owner_id`. `item:<id>` gives the item's explanation and its records.
- **Old rows.** No code joined a decision to its receipts before (the map's "manual JSON join" was the owner's SQL), so nothing is deleted there. A receipt with a NULL `trace_id`, which is every receipt before 253, is never joined by trace. An old router decision still reaches its calls by the boundary key, by hand, until B9 adds that join as the reader labelled "reconstructed" (`tests/test_why_real_cases.py`). `learnloop router trace` is unchanged; it reads `router_objective_traces`, not receipts.
- **A vault below the code's head** is read as it stands (attach never migrates). The records path returns empty below 253; the scheduler path needs the columns it reads, so a vault no command has opened since an upgrade must be opened once first. Before B1, `why` migrated it.

## Proofs

**P-tests** (`tests/test_provenance.py`, 32 tests; `tests/test_decision_records_migration.py`, 4):

- The record: written with id, trace and time filled; six bad records (prose in facts, a rule with spaces, prose in an alternative, a NaN, a sentence as a key, an unknown status) dropped with a warning naming the trace, never raised; item text planted from the head fixture's attempts refused at `alternatives[0].lost_by` and `facts.answer`; a write on a database with no `decision_records` returns `None` and leaves the caller's pending insert committed; a write rolled back with its caller's transaction; a duplicate id failing inside the savepoint without undoing the caller's earlier record; a read-only connection; `write_decision` joining `atomic()` (rolled back with it) or taking its own transaction; the cap at 50 with the overflow counted per rule; UPDATE and DELETE refused; `where` naming the frame and never the message; `read` by latest, kind, trace, record and subject.
- The trace: births, nesting and restore; a copied context inherits it and a bare thread does not; a receipt carries the trace it started under (and NULL outside one); two sidecar RPCs get two traces and a handed-in one is kept; the phone's load, refresh and handler share one trace and it ends with the request; two MCP tool calls get two traces; two post-attempt jobs under one RPC's trace each get their own; `log_event` adds `trace_id` and drops it outside a trace; two CLI commands get two traces and leave none behind.
- Replay (below), and the role and AD class.
- **Fail-first:** `test_why_is_a_pure_read` patches `sync_vault_state` and `run_startup_maintenance` to raise and checks a digest of every row before and after three `why` calls. The same check run on main's code (`0f11cb1053`, a scratch script with the test's body) fails with `AssertionError: why wrote to the vault`; on this branch it passes.

**Replay never reaches the table** (`test_decision_records_is_unreachable_from_replay`, `test_a_rebuild_never_calls_the_record_and_keeps_its_rows`):

- The import closure (grimp, static, function-local imports included) of the live and shadow rebuilds, the replay, the migration coordinator, `db.migrate` and all 43 `*_upgrade` modules (48 roots) has 510 modules. `learnloop.provenance` is in it, through `ai.execution`, which reads the trace for receipts. The store and the CLI are not.
- In that closure, no module other than the leaf names `decision_records`, except the three registries that classify every table by name (`table_roles`: RECEIPT, never cleared; `protected_tables` and `column_classes`: DENIED). None imports or calls `provenance.write`, `read`, `cap_alternatives` or `check_no_prose`; only `current_trace`, `trace_scope`, `DecisionRecord` and `STATUSES` are allowed. A later writer inside this closure has to bring its own proof that replay never calls it, and widen this test on purpose.
- At run time, a live `rebuild_all_derived_state` on the head fixture, with `provenance.write`/`read` and the store's two functions patched to raise, completes, and a record written before it survives byte-identical.

**P-shadow.** `learnloop rebuild --shadow --json` on fresh backup-API copies (`copy_tree_with_databases`, `database_names=("state.sqlite",)`; the stale 4 KB `probability/.learnloop/state.sqlite` deleted from the copy) of `~/learnloop-backups/20261109-copy` (all three at migration 250, mvp-0.54), separate copies for main `0f11cb1053` and this branch, under `fixtures-local/b1-shadow/`. The outputs were compared after masking ULIDs and ISO times:

| Vault | JSON leaves | Differing after masking | Raw differences masked (marker ids, rebuild ids, `as_of`) |
|---|---|---|---|
| arxiv_v2 | 1,037 | 0 | 18 |
| linear_algebra | 999 | 0 | 2 |
| probability | 633 | 0 | 2 |

`schedule_effects` match main exactly. They are not empty on either side. On arxiv_v2, 9 `practice_item_state` due dates count as moved, with every shift 0.0 days and every interval ratio 1.0, which is rounding. linear_algebra and probability move none. The mastery "changes" (29, 21, 18 rows) are the stamps from mvp-0.46 to mvp-0.54 that the strategy's earlier landings recorded, identical on both sides.

**P-draw.** The router speed stages' draw-for-draw harness (`docs/reviews/router-speed2.md`, "Identity"). The drivers come from the IH landing (`drive5.py`, `compare7.py`, `fakes4.py`, `neutralize.py`, `premigrate.py`, copied into the step's scratch directory). Two adaptations: each handler call runs under `trace_scope()` on the branch, as `_handle` does per RPC (a `nullcontext` on main), and the comparison sets aside `model_call_receipts.trace_id` and reports `decision_records` apart. Each side ran on its own fresh copy of the same backup, premigrated with its own code (main to 252, the branch to 253) and neutralized: every AI route at `http://127.0.0.1:9`, the router LLM and Decider in-process fakes, grading and diagnosis the tests' `BlindRivalClient`, FG1's author the tests' `AuthorFake`. The mixture seed was pinned to the decision id (`SMOKE_PIN_SEED=1`) and the key left unpinned (same tag on both sides). Each run was one day of 40 steps at most, the second served item missed, the first stop declined.

| Vault | Served | Router decisions | LLM / Decider requests | Gates | New receipts | Result |
|---|---|---|---|---|---|---|
| arxiv_v2 | 12 | 15 | 15 / 15 identical | 1 identical | 50 | **IDENTICAL** (ids and times aside) |
| linear_algebra | 9 | 9 | 5 / 5 identical | 1 identical | 20 | **IDENTICAL** |
| probability | 14 | 13 | 11 / 11 identical | 1 identical | 38 | **IDENTICAL** |

Prompts (14, 11 and 16 grader and diagnoser prompts), Today, the plan, every step, every submit and feedback, the traces (22, 5, 10) and every other table's new rows matched, as did the removed-row counts. `decision_records` held 0 rows on the branch (B1 writes none). On the branch, 42 of 50, 15 of 20 and 30 of 38 new receipts carry a trace (14, 5 and 10 distinct): every router decision, router LLM and Decider call made inside a handler call, including those in the router's prefetch threads. The untraced ones are the driver's direct `drain()` and follow-up job calls, plus one router prefetch made by `ctx.load()`, all outside any entry point in the driver. In the app, `load` runs inside an RPC and those jobs in the post-attempt worker, which now gives each job a trace.

**No real model, no network.** Every new receipt in all six runs came from a fake provider (`fake_llm`, `fake_decider`, `fake`): 0 new receipts from a real model. The net watch (`sitecustomize`) logged no non-loopback connect or resolve. It logged 12 subprocesses, all `powerprofilesctl get` and `git rev-parse HEAD`, and no Codex process.

## Tests

- Targeted lane, `-n 6` under the 5 GB scope (every test file added or edited, `test_migrations`, every `test_*migration*.py`, `test_table_roles`, `test_tracked_fixture_databases`, `test_public_tip_guards`, `test_architecture`, `test_cli_help_snapshot`, `test_cli_json`, `test_effective_defaults_golden`, `test_cli_commands`, `test_cli_attempt`, `test_cli_entrypoint`, `test_ad_protected_tables`, and every test file importing the sidecar server, logging or post-attempt worker, the phone runtime, the MCP server, `ai.execution`, the receipt store or AD's registries: 223 files). Final run: **12,362 passed, 9 skipped, 2 xfailed** in 4:09. The first full run found the 22 "nothing else changed" pins and the SQL-writer registry above. `scripts/affected_tests.py` picked 1,310 files for the source changes alone (the CLI and table roles reach nearly everything), and the migration and fixture fall back to the whole suite, so the lane above stands in, as the brief allows.
- `lint-imports --no-cache`: 43 kept, 0 broken. `ruff check src tests scripts`: clean.
- Vault: ADR-017 and the index; `Workflows/Inspect Persistent State` (the `why` targets, a "why a decision went the way it did" section, the SQL join). The references were regenerated once after the source commit (`generate_all.py`: one new table note, two new module notes, `model_call_receipts`, and line-number shifts) and committed, and a second run changed nothing. The four validators pass.

## Storage

B1 writes no records, so there is nothing to measure per week yet. On a scratch copy of arxiv_v2 at 253, 2,000 inserts each of three representative shapes:

| Shape | Bytes per row (table and indexes) |
|---|---|
| `model_answer` (timeout, two facts, two versions) | 660 |
| `plan_block` (10 alternatives with p and score, five facts, three versions, detail and parent ids) | 2,443 |
| `slate` (50 alternatives, exclusions counted per rule with three ids) | 4,928 |
| `model_call_receipts.trace_id` and its index | 57 per receipt |

The copy's busiest recent weeks held 13 attempts and 379 model calls. At the strategy's assumed 30 records per attempt cycle and about 2.4 KB each, that is about 0.95 MB a week, plus about 22 KB for the trace column: about 0.35% of this 278 MB vault a week, about 1.5% a month. That is under §3.7's 5% bound but above its 1 KB-a-row assumption. Records with long alternative lists are the cost, which is where B6 (slates, the largest writer) measures on a copy-shaped journey and trims by rule.

## Open items for B2-B9

- **Writers inside an AD operation** (B3's AD denials) must add `decision_records` to `AD_WRITABLE` (write only) or write outside the operation. Otherwise the guard poisons the operation, which changes what is served.
- **A writer in the replay closure** (likely B2's in `daily_plan`) must widen `test_decision_records_is_unreachable_from_replay` on purpose and show replay never calls it.
- **A record's own transaction can wait on the write lock** (busy timeout 5 s) when no caller transaction is open. In a router path with a wall-clock budget that wait could turn into a timeout. Write in the caller's transaction there, or after the decision is returned.
- **`job_enqueued`** (§3.3, "across a queue"): today a post-attempt job gets a fresh trace. B7 links it to its enqueuer, and the worker then passes that trace to `trace_scope`.
- **Prefetched decisions**: a router decision prefetched in one RPC and served in the next carries the prefetching request's trace on its calls. B2's `plan_block` record should name both (the serving trace, with the prefetch's trace in `facts`).
- **Retention**: §3.7's pruning of `alternatives_json` and `facts_json` on old rows needs the no-update trigger relaxed for exactly those two columns, by a migration of its own.
- **Old rows**: B9's "reconstructed" reader (boundary-key join; `why.get` RPC; `--payload`; `router trace` and `trace-evidence` as views).
- **Late answers** (S4, S5): derived at read from `trace_model_calls` and the record's `created_at`; B2 adds the comparison to `why`.

## Unverified

- The phone host and MCP server were not run end to end (both are wired through tested units: `HostRuntime._dispatch` with a fake worker, `ToolCalls.run` with a stub body).
- Durability lane (WAL) not run for the new tests; the savepoint path is SQLite-level and mode-independent, and the landing gate runs durability.

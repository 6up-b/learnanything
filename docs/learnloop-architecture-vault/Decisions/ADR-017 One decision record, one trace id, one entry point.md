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
  - src/learnloop/provenance.py
  - src/learnloop/db/stores/provenance.py
  - migrations/253_decision_records.sql
  - src/learnloop/db/table_roles.py
  - src/learnloop/adaptive_difficulty/protected_tables.py
  - src/learnloop/ai/execution.py
  - src/learnloop/db/stores/model_calls.py
  - src/learnloop/cli/app.py
  - tests/test_provenance.py
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

**A record never changes a decision.** `provenance.write(connection, record)` joins the caller's transaction in a savepoint. `db.stores.provenance.write_decision` (and `refusal_records.write`; both are `provenance.write_through`) writes through a repository: it joins a transaction the caller holds on a pinned or atomic connection without ever committing it, and takes a short one of its own otherwise (arc B fix 2). A path on a wall-clock budget holding no transaction uses `write_decision_without_waiting`, a connection of its own with no busy wait, so a lock held elsewhere drops the record rather than holding the decision (the router's spend guard, arc B fix 1). Either way a failed write logs a warning with the trace id and returns; it never raises into the decision. Record and trace ids come from a ULID stream of their own (`provenance.new_record_id`), never from `ids.new_ulid`, which also mints the router's decision id and so its draw seed: a record never moves the next decision's id (arc B fix 3). A record holds no prose: no learner text, item text, prompt or model output (`provenance.check_no_prose`, and a test that plants item text). Payloads stay in `model_call_receipts`, under their existing retention.

### The trace id

A ULID in a `ContextVar` (`provenance.current_trace()`), **born** once per learner-visible action:

- the desktop sidecar, per RPC (`learnloop_sidecar.server._handle`);
- the phone host, per request (`learnloop_mobile.runtime.MobileRuntime._dispatch`, which hands its trace to the same `_handle`);
- the MCP server, per tool call (`learnloop_mcp.server`'s `run`);
- the CLI, per command (the root callback).

It is **carried** by the `ContextVar`: threads started in a copied context (the router's jobs, background exam grading) inherit it, and the sidecar's request-started jobs (`BackgroundJobs.spawn`: hints, Reader cue discovery, library asks, reading paths) run under the trace of the request that started them, as does each queued figure prefetch trigger under the trace that queued it (arc B fix 7). The post-attempt worker's long-lived threads open one scope per job, so a job never carries the RPC that first woke the worker. **Across a queue** (B7): each enqueue that inserts a row (`post_attempt_jobs`, `learner_text_gap_jobs`, `followup_generation_jobs`, and IH2's requeue) writes a `job_enqueued` record (`subject = job:<id>`) in its transaction, and the job's processor, once it has leased the row, continues that record's trace (`db.stores.provenance.continue_job_trace`, which switches the worker's scope in place with `provenance.continue_trace`). The record is the job's cause (`provenance.current_cause()`), so the job's own records name it as their `parent_id`. Submit, grade, diagnosis and follow-up generation therefore share one trace; a job queued before B7, or whose record did not write, keeps a trace of its own.

**Model calls** carry it in a real column, `model_call_receipts.trace_id` (nullable), set when the call starts (`ai.execution`) and written by `record_model_event`. That closes break 2 without moving the decision id, which feeds the mix's seed. **Logs** carry it: the sidecar's `log_event` adds `trace_id` to every structured event.

### Replay and persisted meaning

Writing a record changes no replayed meaning, each with a test (`tests/test_provenance.py`):

- the role is `RECEIPT` (`db/table_roles.py`): append-only (two triggers refuse DELETE and every UPDATE but retention's, below), never cleared by rebuild;
- no replay or rebuild code can reach the table: the import closure of the rebuild orchestrator and the upgrade chain never imports `learnloop.provenance` or the store, and no module in that closure names `decision_records`;
- AD's guard classifies it `DENIED` (`adaptive_difficulty/protected_tables.py`), so no AD operation reads it;
- `model_call_receipts.trace_id` is nullable and no projection reads it.

No successor tag: the table is a receipt and the column is accounting (`docs/algorithm-change-playbook.md` applies to persisted meaning, which neither carries). Old decisions keep their rows and get **no backfilled records**: a record written now would claim to know inputs nobody stored. `why` labels what it reconstructs from old rows instead.

### The entry point

`learnloop why [TARGET] [--kind K] [--first-build] [--payload] [--json] --vault V` is a **pure read**: `Repository.attach(..., read_only=True)`, no `sync_vault_state`, no startup maintenance. `TARGET` is `latest` (the default), a trace id, a record id, `<subject_kind>:<id>`, or a practice item id (today's scheduler explanation, kept). For a trace it lists the records and the trace's model calls, joined by `trace_id` (ids, purposes, statuses, times; never payloads), and, per decision, what was chosen, the alternatives with their chances and losing rules, the inputs, who decided with versions and seed, what came next and what was discarded. One reader answers it, `learnloop.why.reader.answer`. Decisions older than their records (every decision before migration 253) answer through `learnloop.why.reconstructed`, from the rows they left: a router decision's calls through its boundary key (`router_decisions.detail_json` to `model_call_receipts.owner_id`), an offer's `expired` response, a figure's verification, the pre-build ledger. Every such answer is labelled `reconstructed`, and a field found only by ordering rows in time is named `inferred`. The how-to is [[Debug a decision]].

The same reader serves the sidecar's read-only `why.get` RPC (ids, numbers and codes only, never a payload; not on the phone's allowlist), and `learnloop router trace` and `trace-evidence` are views over it. `--payload` (the prompt and output from each named call's receipt) exists on the desktop CLI only.

### Storage and protection

Rows are small: ids, numbers and capped lists, exclusions aggregated by rule. The strategy's estimate is at most about 1 KB a row and about 30 rows per attempt cycle; B6 measures it on a copy-shaped journey, and tightens what it records by rule if growth passes 5% of a vault's database a month. `router.payload_retention_days` prunes `alternatives_json` and `facts_json` on old rows and keeps the row (migration 254, arc B fix 8): the no-update trigger lets through only an update that sets those two columns to their fixed placeholders (`[]` and `{"payload_pruned":true}`) on a row over a day old, with every identity column unchanged; deletes stay refused. `db.stores.provenance.prune_old_decision_payloads` runs it from startup maintenance with the vault's setting. No model context reads the table and no grader context can.

## Consequences

- One `why` answers from new rows once each boundary writes its record (arc B, B2-B8, in order of debugging value). B1 writes none; it builds the table, the trace and the reader.
- Every receipt from a traced action carries its trace, so "which calls belong to this decision" is a join on one column, and "which calls finished after the decision" is a comparison of times (S4, S5 derive at read, with no new write).
- A writer inside an AD operation must write outside the operation or add the table to `AD_WRITABLE` (write only): the guard would otherwise poison the operation, which would change what is served.
- `decision_records` is never the system of record: ledgers and receipts stay immutable and authoritative, and nothing replays from it.

## What it replaces

- **Kept:** `router_decisions` and payloads, `router_objective_traces`, `ad_selections` (the model for the shape), `judgment_ledger`, `plan_presentations`, the causal receipts.
- **Gone:** the manual JSON join from decision to receipt (for new rows), `why`'s writes, and, as B2-B9 land, free-text `owner_id` as the join and per-subsystem entry points as separate code.
- **Kept beside the records:** AD's JSONL denial log (`ad_guard_denials.jsonl`). `learnloop ad report` counts it and a successful `learnloop upgrade` archives it, so B3 left it in place and added the `ad_slot` record (the incumbent's fallback, naming what the guard refused as verb, table and reader). The plan writes that record after every AD operation has closed, in its own transaction, so the guard never sees it and `decision_records` stays out of `AD_WRITABLE`.
- **Not done:** trace spans or OpenTelemetry (a dependency and a concept for a single-user app), a record at every function or per protection read, prompts or free text in records, and renaming "decision" elsewhere (`router_decisions` stays).

## B8: boundaries with no record, and why not

B8 read the remaining boundaries (teacher lessons and checks, Reader retrieval, ingest routing, AI route fallback, retries, re-read and alias resolution, curriculum path, FSRS rating and elapsed) and the leftovers B3-B7 handed on. The rule: a record where a real question had no stored answer; for the rest, the row that already answers it, or why a record isn't worth it. With B2-B7's records, this is the inventory with no silent gap (`docs/specs/refactor_strategy_v3.md` §3.8).

**Records B8 added** (`docs/reviews/refactor-b8.md` has what each carries):

| Site | Record | The question it answers |
|---|---|---|
| A plan decision's logger raised (`daily_plan/engine.py` `_log_plan_decision`, `_log_interrupt`; S13's other half) | `router_decision_row`, `failed`, `logger_error`, on the block | Why does this block have no ledger row? (Before: a warning line.) |
| A shared daily cap refused (`SharedDailyEnvelope.reserve`: the source service's, hints', hint maps', figures', the Reader's follow-ups and digest, reading paths, deliverables, library ask, passage cues, workbench check) | `spend_admission`, `refused`, `envelope_cap` | Why did my comparison, path, hint or figure come back capped or empty today? Each caller turned the refusal into its own status, nothing was sent, and the exception named no numbers. AD's own envelope records none (below) |
| A lesson closed with `budget` (`teacher/service.py`) | `spend_admission`, `refused`, by `lesson_envelope` | Which request hit the lesson's cap, at what estimate against what limit? The gate's refusal was kept nowhere |
| The curriculum path's daily re-judgment (`deliverable_path.refresh_for_plan`) | `curriculum_path_refresh` (`chosen`, `refused`, `excluded`, `deferred`, `discarded`, `failed`; none for `none` or `fresh`) | Why was the stale path not judged again today? (Before: the sidecar's memory and a log line) |
| An AD commission's job that generated nothing (`content/pipeline/jobs.py`) | `ad_commission_skip`, `excluded`: `commission_closed`, `view_unavailable` or `guard_denied` | Did the commission close, or could AD not read it? The job's result says "no longer open" for all three, and still does |
| A figure prediction's gap reading stopped by the figure gate (`diagnosis/text_gaps/jobs.py`) | B5's `figure_admission`, now with the job's repository | Why did the reading stop? The job row kept prose only |
| The FSRS review (`attempts/attempts.py`) | `grade.facts.fsrs` on B7's record | Why is this card due then? The rating before and after the hint cap, elapsed days, the state before and after, the interval and its factor, the due time, or why no review applied. The state row is overwritten by the next review and the elapsed time was never stored |

**Boundaries left without a record, and why:**

| Site | The question | Why no record |
|---|---|---|
| Teacher, inside a lesson: turns, invalid or withheld turns, visuals, read refusals, checks, closes | What did the teacher do and why did the lesson end? | `lesson_turns` (with payloads), `lesson_receipts` and `lessons.close_reason` hold each one |
| Teacher, an open refused before the lesson row (topics refused, lesson refused, protection unreadable, teacher route not ready) | Why did "Teach me this" open nothing? | Learner-initiated and synchronous: the code and message are shown at that moment, and nothing was decided on the learner's behalf |
| Teacher, a provider failure mid-lesson | Why did the teacher not answer? | The call's receipt (`status`, `error_type`) carries the RPC's trace (B1), so `why <trace>` joins it |
| Teacher brief: an unreadable deliverable or AD readiness (`brief.py`) | Was there no deliverable, or did reading it fail? | Low value: the brief is stored on the open turn; open item below |
| Reader retrieval: embedding refused or failed, pool fallback, rewrite, verification | Why lexical, why no passages? | `question_events.source_context.source_retrieval` keeps the whole manifest (statuses and reasons); `find_practice` keeps `signals` on its proposal receipt |
| Re-read carry-over | Did the old reading carry over? | `source_span_reanchors`, the import job's `result_json.carried_over`, and `carry_over_for`/`carry_over_done` |
| Alias resolution (spans, LOs, facets) | Which span does this old reference mean? | A pure function of `source_span_reanchors` and the stored document IRs, so it recomputes; LO and facet aliases are deterministic maps |
| Margin cues and re-read suggestions | Why was this cue shown? | Display-only and derived from stored error rows and configuration; taps are in `judgment_ledger` (`passage_cue`) |
| Curriculum path choice and the plan's use of it | Which section, and why did the plan fall back? | Path rows and `judgment_ledger` (`reason_by`, alternates); the plan row's `split_json.reading_path` (status, `chosen_by`, the deliverables consulted). `validate`'s dropped LOs are deterministic from `state_key` |
| Ingest routing (extractor choice and fallback, Quick Add scope) | Which extractor read this, and was it a fallback? | `source_extraction_runs.extractor`, `model_versions_json.fallback_from` and `health_json`'s flags. Not a served decision. The primary extractor's exception class and the Quick Add "nothing matched" fallback are lost: open item |
| AI route fallback (`ai/routing.py`) | Which provider answered, and was it a fallback? | The receipt names the provider and model that answered, and the Decider, spend, figure and grade records name a fallback where it changed a decision. Which route fell back, and why the primary wasn't ready, is not stored: routing holds no connection and runs inside router paths with a time budget, where a record's own transaction could wait on the write lock (B1's rule). Open item: carry it on the receipt (a nullable column, its own migration) |
| Retries (transport, truncation, JSON repair) | How many attempts, which failed, with what? | Each physical attempt is a child receipt (`parent_call_id`, `status` `failed` or `truncated`, `error_type`, output budget); a record per retry would duplicate them |
| FSRS: the causal-activity or eligibility skip | Why did this attempt not move the schedule? | Now `grade.facts.fsrs.skipped` (above); it was also derivable from the attempt row under the same tag |
| Device eligibility's failure | Why did the phone not show this? | B6's slate record counts `device_ineligible` by rule; the media predicate fails closed (the item waits for the desktop), so a failed read and "not served" look alike, at no cost to the learner |
| Spend refusals in content generation (follow-up generation) | Why did the follow-up not appear? | `followup_generation_jobs.last_error`, the workflow's `failed` reason, and B5's `spend_admission` from the router guard |
| AD's sending (forecasts, audits, relatedness) | Why no forecast? | Forecast receipts carry `refused_spend` or `skipped:<reason>`; the audit's Decider verdicts are in `judgment_ledger`. AD's envelope writes no refusal record: it is reserved inside AD operations, whose guard denies the table, and a denied write would poison the operation |
| Reader intent, Reader quick check, Reader follow-ups, hint writer, grading | Why did it fall back or stop? | Reader intent: `judgment_ledger` verdict `refused`. Quick check: `ingest_jobs.error_json` with the cap's numbers. Follow-ups: the digest receipt's `reason=budget`. Hint writer: `help_assists.contract_failures_json` (`capped`, `unrouted`, ...). Grading: the `agent_runs` row `failed`. The shared caps among them now also write the envelope record |
| Hint outcome placement refused | Why no placement verdict? | Measurement-only and retried next pass; the missing verdict is itself visible |
| `hints.chooser_enabled = false`; a tied Decider judgment (B5) | Why the default help style? Why no choice? | The help row's `chooser_reason = chooser_disabled` (a switch, not a refusal); the ledger's `tied` verdict with its probabilities |
| Background AD denials (preparation, forecasts, audits, relatedness, generation; B3) | Why was this item never prepared or forecast? | `ad_guard_denials.jsonl` (counted by `learnloop ad report`, archived by an upgrade; owner, 2026-10-21: logged, counted, no UI). A record needs a write after each operation closes, in each of about seven background callers; the commission job, whose result mislabelled the denial, got one (above) |
| `commission_point`'s denial inside generation | Why the incumbent's rung? | It runs inside the caller's AD view, where the table is denied; the JSONL holds the denial |
| Quick check and `find_practice` exclusions (B6) | Why was this item not offered? | Learner-initiated selectors: the quick check's served items are presentations; `find_practice`'s results are on screen with its receipt's signals. The exclusions are the shared predicate the slate record counts per build, and `why item:<id>` re-derives them |
| The TUI's probe door (B7) | Why no `probe_value`? | The TUI is rebuilt as a frontend after the refactor (C7) |
| AD generation refusal; the hint ladder's missing client (B7) | Why no generated item? Why the authored hint? | `ingest_jobs` `failed` with `error_json` (`AuthoringRequestRefused`, `ad_models_off`); `help_assists.contract_failures_json.reason` and `chooser_reason`, plus B5's `decider_judgment` |
| Rich figure jobs' attempts (B4) | What went wrong on attempt 1? | Each attempt's call is a receipt (`metadata.attempt`, status); the stored figure keeps the last failure; a retry refused by the figures' cap is now the envelope record. Per-attempt problem codes are an open item |
| Learner protection, a per-call read | | Recorded only where it excludes something from a decision (B4, B6), per the strategy |

**Open items from the inventory:** the AI route's fallback on the receipt (a migration); the ingest extractor's primary failure class and per-attempt job history (`ingest_jobs.error_json` is reset when a job is leased again); the Quick Add scope fallback; the teacher brief's swallowed reads; rich figure attempts' problem codes (B4's `AuthorAttempts`, wired through `figures/rich.py`'s several exits).

## Related notes

- [[ADR-003 Explicit table roles govern rebuild]]
- [[ADR-007 Immutable evidence and append-only correction]]
- [[Inspect Persistent State]]
- [[Design Decision Index]]

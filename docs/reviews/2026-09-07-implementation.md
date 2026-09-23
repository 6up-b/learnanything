# Recovery, ingestion and collection fixes

PR #4 was merged as `472128f527b9b4b02aa6581cc26b4a623870b371`. The follow-up branch is `fix/review-recovery-and-telemetry`. This implements the actionable P1/P2 findings in the September 6 reviews and data recommendations 1–5. Preserving useful Python descendants across debugging restarts remains intentional.

## Durable behavior

An attempt and its completion work now commit together. Recovery reuses the saved grade, resumes local post-processing, and returns the frozen completed route. It does not grade twice or infer permission to show diagnostic feedback from an attempt ID alone. A legacy attempt without completion information still fails closed. A post-commit annotation error cannot create a second fallback attempt.

Live rebuild deletion, replay and publication now share one transaction. Nested repository operations use savepoints, and their historical commits cannot expose partial projections. SQLite serializes concurrent evidence writers against that transaction. This deliberately favors consistency; a large live rebuild can hold the single writer for its duration. Shadow rebuild remains available for inspection.

Ingest completion and stale recovery compare status, worker identity and attempt generation. A surviving owner can keep renewing its lease; a replaced owner cannot publish canonical database or locked vault writes, including the source note and goal linkage. The drain loop expires stale leases on each tick but never fails an attempt whose handler is still running in the same process. Losing ownership interrupts only that attempt's own transport, not the replacement's batch or unrelated descendants.

A late provider response can finish only its own previously started call receipt and save its own model checkpoint, even after lease loss. These narrow writes retain known spending and paid work while canonical publication remains fenced.

## Token-preserving ingestion

- Each validated inventory window, synthesis pass and completed shard has a durable checkpoint keyed by its rendered prompt, schema and provider settings (provider, model, endpoint, reasoning effort, thinking and response format). A checkpoint that no longer validates is discarded and the call is made again. An interrupted evidence expansion reuses the first pass. Completed model work survives later application errors.
- Inventory uses a bounded work queue with one client per worker. The runner accepts receipt/checkpoint events before acknowledging workers. Failures stop new work, interrupt active peers, and drain pending acknowledgements before shutdown.
- Stable task instructions precede changing context. Evidence expansion follows the full inventory prefix. This enables cache reuse; actual hit rate and cost improvements still require provider measurements.
- OpenAI-compatible SDK retries are disabled; the adapter owns the retry policy. It retries connection errors and timeouts and HTTP 408, 409, 429 and 5xx, at most 3 attempts. It honours `retry-after-ms` and `Retry-After` (seconds or an HTTP date) and gives up when the server asks for more than 60 s. Otherwise it backs off with a ceiling of 1 s, then 2 s (capped at 8 s), jittered between 50% and 100% of the ceiling. The request timeout bounds the whole loop, each attempt gets the remaining time, and no attempt starts with less than 1 s left. Truncation is recorded before parsing and does not trigger an identical repair. Repair output usage counts toward the operation's remaining budget.
- Synthesis preflights the complete prompt/schema for every uncached base pass, reserves remaining base input before evidence expansion, and checks cumulative output. Provider usage increases estimates when reported. Graph structuring receives only the remaining output budget. With the default budgets (40k shard input, 48k total input ceiling), the complete-request preflight rejects a single near-full shard once the registry holds roughly 230 ids: the fixed prompt overhead is about 6.1k tokens and each registry id adds about 9.8. Packing shards to leave room for the overhead makes the total larger, so this is a question of default budgets for the owner. The refusal states the estimate, the ceiling and how to proceed.
- Codex receives an advisory output target and local budget checks. Its app-server protocol does not expose a documented hard per-turn output-token cap; this is not a billing guarantee. JSON repair stops when reported output has exhausted the available budget. [Codex app-server protocol](https://learn.chatgpt.com/docs/app-server).
- Cached study-map generation can resume apply/goal creation. Goal identity is stable for the same proposal. Legacy ingestion identity includes instructions, subject, purpose, prompt version and provider/model. A v2-lite retry (attempt count above 1, with retained IR) resumes from the retained extraction and original bytes; a first attempt always fetches, so captions, labels and source metadata are kept. A retry does not recover that fetch-only metadata. Concurrent original-byte writers use separate temporary files.

## Desktop and local performance

Repository connections close deterministically. Queue computation and bulk DTO serialization reuse a connection during short local work. Native vault metadata has its own short mutex, resource handlers run file I/O off the request thread, and media requests read only the requested range. Same-vault reconnection restores the grading override; configured manual grading is healthy.

Reader hydrates each new terminal request while other requests continue, retries hydration failures, and keeps one poll in flight. Scope identities reject stale A→B→A results. Late close-listener registration is disposed. PDF fetches/workers are cleaned up on failure or vault change. Practice saves before vault selection and suppresses old-vault unmount writes; a failed save keeps the old vault open.

Large screens and pdf.js load on demand. The measured main JS chunk is 1,251.12 kB (370.82 kB gzip), compared with 2,150.96 kB (630.24 kB gzip) at the base commit 472128f, a reduction of 899.84 kB (41.8%). After the September 23 review fixes it is 1,252.29 kB (371.26 kB gzip). This is a bundle-size measurement, not an end-to-end startup benchmark; the main chunk still exceeds Vite's advisory threshold.

Queue measurements on disposable fixture copies, production connection settings, a fixed September 6 clock and no persisted explanations:

| Fixture | Unpinned, 3 samples | Reused connection, 3 samples | Returned items |
|---|---:|---:|---:|
| Migration-head conic sections | 55.0–63.1 ms | 3.19–3.21 ms | 5 |
| Linear algebra | 34.6–73.4 ms | 4.65–4.67 ms | 41 |

The complete serialized queues had identical SHA-256 hashes across modes. Unpinned ran first; these samples are illustrative, not a latency SLO. Raw results are in [queue-connections.json](artifacts/queue-connections.json).

The September 23 review fixes pinned one connection for the remaining per-item loops. Medians of 5 on a fresh copy of `fixtures/linear_algebra` with a frozen clock, serialized results byte-identical before and after:

| Sidecar call | Before | After |
|---|---:|---:|
| `get_today_queue` | 191.6 ms, 86 connections | 38.6 ms, 7 connections |
| `get_practice_item` | 26.2 ms, 12 connections | 5.8 ms, 1 connection |
| `get_feedback` | 70.5 ms, 36 connections | 10.5 ms, 4 connections |
| knowledge map | 1,171 ms | 521 ms |
| facet mastery | 211 ms | 17 ms |

These calls do more than the queue build above (backfill, serialization, feedback bundles), so the numbers are not comparable with the first table.

## Collection and dataset contract

Keep `state.sqlite` as the transactional store for evidence, immutable receipts, workflow state and rebuildable projections. Splitting telemetry into another database would add a consistency boundary. Original source/media bytes remain in the content-addressed file store.

Migrations 159–164 add completion work, model-call receipts/checkpoints, immutable submission/offer provenance, collection metadata, append-only false-remediation adjudications, and content-addressed item snapshots. Migration 164 also rebuilds the adjudication table without its foreign key to `practice_attempts`: scratch replays truncate attempts by walking that foreign-key graph, and the table's no-delete trigger would abort the walk. The store checks that the attempt exists instead. Historical attempts remain `legacy-unversioned`; missing fields are not backfilled with guessed observations.

The desktop carries the actual offered candidate into its durable submission identity. Refreshing the queue cannot retarget it. Final offers record adapter filtering. Pre-action selection features are immutable; the earlier base draw probability is retained separately from the composed offer. Final learner-choice propensity is unavailable, so these rows cannot be used for inverse-propensity evaluation; `learnloop eval` reports their readiness as `UNAVAILABLE`.

Selection features are compact: the learner's ability vector for the item's learning object and the item's scored demand vector, with the item referenced by the SHA-256 of its canonical JSON. `practice_item_snapshots` stores each scored revision once. Measured over 5 persisted queue builds on a copy of `fixtures/linear_algebra` (99 items, 41 candidates), a build stores about 100 KB more than on main (it was about 475 KB with full item dumps in every feature row). The first build also writes a one-time 151 KB of item snapshots (41 rows); later builds of unchanged items add none.

Call receipts record start before execution and capture completion/failure, text output, schema/input hashes, textual root requests, provider identity, response ID, finish reason, duration, reported token/cache/reasoning usage and cost. Raw provider usage is retained where available; missing cost and incomplete calls remain unknown. Inline media payloads and credentials are not copied into prompt columns. Coverage currently includes desktop RPCs, durable ingest jobs, and CLI practice grading. Other direct service/CLI/TUI paths may still have only aggregate agent-run accounting; the presence of receipt tables does not establish universal capture.

`learnloop-events-v1` and `learnloop-outcomes-v1` define these exported views:

| View | Meaning |
|---|---|
| `R_next` | Next observed attempt for the learning object, its delay/item/origin, and explicit retention exclusions. Pending is distinct from failure. |
| `R_cold` | Numeric retrieval outcomes require qualified final coldness receipts. Repair terminal dispositions preserve success/failure/censoring/refusal and verification references separately; do not count the two receipt kinds as independent measurements. |
| `Q` | Directly linked question counts. Missing links remain unavailable, not zero. |
| `B` | Recorded attempt wall-clock latency, with total burden explicitly unavailable. Restored screen timers are not presented as complete episode duration. |
| `F` | Explicit evidence-backed human or machine adjudication with verifier version. No automatic causal label is inferred from later success. |

Delayed retention excludes hints, priming, insufficient delay, same-session outcomes, intervening practice, unresolved grades and missing correctness. Dataset views also expose non-human outcome exclusions. Delayed unassisted retention does not establish certified coldness or a causal treatment effect.

## Commands

```bash
uv run learnloop doctor --data-quality --vault /path/to/vault
uv run learnloop data-quality --vault /path/to/vault
uv run learnloop dataset-export /path/to/new-dataset --vault /path/to/vault
uv run learnloop adjudicate-remediation ATTEMPT_ID --false-remediation \
  --evidence evidence.json --verifier-version human-review-v1 --vault /path/to/vault
```

`evidence.json` is a list of retained references, such as `[{"table":"practice_attempts","id":"ATTEMPT_ID"}]`. The adjudication validates references and appends a new record; evidence quality remains the adjudicator's responsibility. Use `--appropriate-remediation` for a negative F label.

Quality reports are read-only and group coverage by collection version, entry surface and origin. They report offer/grade/contract links, incomplete work, chosen probability validity, usage/duration availability, cold opportunities/dispositions and retention exclusions. Legacy-unavailable fields do not become current-version alerts.

Exports require a new directory. SQLite's backup API writes a full copy of the database to `snapshot.sqlite`; the JSONL files hold every RAW_LEDGER and RECEIPT table (including `model_call_receipts` prompt and response text), seven captured workflow tables, and the versioned outcome and split views. Each artifact is hashed while written and fsynced. The manifest is written last to a temporary file, fsynced, renamed into place, and the directory is fsynced, so the manifest is the completion marker. It includes snapshot/schema/artifact/code hashes, migrations, versions, snapshot times, source-asset references and missingness. A failed export removes the directory it created. Corrections produce a new export.

Splits use chronological timestamp buckets and connected content-lineage groups: item, learning object, contract blueprint, evidence-fingerprint source family and shared stimulus, and cited source spans. The presentation-format `surface_family` never joins groups. Only human attempts with content provenance are eligible, and only they set the cutoffs and the buckets a group occupies, so non-human rows cannot quarantine a human group. Groups crossing boundaries are quarantined. Simulator and machine labels remain distinguishable. On a copy of `fixtures/linear_algebra` with every attempt treated as human, this gives 23 train, 47 quarantined and no validation or test rows. A small n=1 dataset can legitimately have no usable held-out partition. Inspect coverage before training; these changes do not certify a production dataset's completeness.

## SQLite concurrency decision

Run `uv run python scripts/benchmark_sqlite_concurrency.py --iterations 200 --directory <parent>` to reproduce the disposable benchmark. It uses FULL synchronous durability and a 5 s busy timeout (the production value), one writer, two readers, 200 operations per worker, 2 KB writes and 2 ms held read snapshots. For WAL it keeps one connection open for the whole run, so the final checkpoint measures a real log. [Raw results](artifacts/sqlite-concurrency.json) are from 2026-09-23 on btrfs (`~/.cache`), SQLite 3.50.4:

| Mode | Elapsed | Writer p95 | Reader busy failures | Integrity | WAL checkpoint |
|---|---:|---:|---|---|---|
| DELETE | 7.94 s | 39.28 ms | 2, each a full 5,000 ms stall | ok | n/a |
| WAL | 1.96 s | 10.01 ms | 0 | ok | PASSIVE checkpointed 599 of 599 frames; TRUNCATE not busy |

The earlier recorded run (10.04 s against 2.66 s) reported "checkpoint completed" from a checkpoint that ran after every connection had closed, so it had no log to move and proved nothing. On tmpfs, where fsync is cheap, both modes take about 0.4 s with no busy failures, so the gap is the cost of fsync and reader starvation and depends on the disk.

Production remains DELETE. The numbers favour WAL, but this synthetic result does not qualify WAL's checkpoint, crash, copy and read-only lifecycle for how LearnLoop opens and publishes vault databases. The accepted cost is that a DELETE-mode reader can stall for the full busy timeout and then fail. [ADR-014](../learnloop-architecture-vault/Decisions/ADR-014%20SQLite%20stays%20in%20DELETE%20journal%20mode.md) records the decision and the checks a switch needs. Functional test settings (`synchronous=OFF`, memory journaling) never become production configuration.

## Test changes and verification

The basic-vault template is built once, checked for root-specific paths, and copied into each test's private directory. Fresh initialization/migration paths remain real: `create_basic_vault(..., fresh=True)` builds a vault from scratch, and so does every test in the durability lane. `uv run pytest -m durability` uses production SQLite settings, and `--durable-sqlite` opts any selected tests into that lane; both apply to fixtures of every scope. Markers are strict (`--strict-markers`), and `durability` is the only custom marker.

Source/AST reads are shared. Duplicate schema and capability declarations were removed while unique negative cases remain. Resolver policy matrices stay at the resolver; adapter tests cover wiring and meaningful success/manual paths. Overlapping diagnostic and teach-back simulation runs share results without sharing mutable test state.

The new regression cases exercise interrupted completion/rebuild, ownership interleavings, window/evidence retry reuse, cumulative repair budgets, exact offer binding, immutable features/adjudication, consistent live backup, source-byte concurrency, and real React lifecycle ordering.

Final test totals and remaining limits are recorded in [implementation-progress.md](implementation-progress.md). The September 23 review and its fixes are recorded in [2026-09-23-review-fixes.md](2026-09-23-review-fixes.md).

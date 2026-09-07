# Recovery, ingestion and collection fixes

PR #4 was merged as `472128f527b9b4b02aa6581cc26b4a623870b371`. The follow-up branch is `fix/review-recovery-and-telemetry`. This implements the actionable P1/P2 findings in the September 6 reviews and data recommendations 1–5. Preserving useful Python descendants across debugging restarts remains intentional.

## Durable behavior

An attempt and its completion work now commit together. Recovery reuses the saved grade, resumes local post-processing, and returns the frozen completed route. It does not grade twice or infer permission to show diagnostic feedback from an attempt ID alone. A legacy attempt without completion information still fails closed. A post-commit annotation error cannot create a second fallback attempt.

Live rebuild deletion, replay and publication now share one transaction. Nested repository operations use savepoints, and their historical commits cannot expose partial projections. SQLite serializes concurrent evidence writers against that transaction. This deliberately favors consistency; a large live rebuild can hold the single writer for its duration. Shadow rebuild remains available for inspection.

Ingest completion and stale recovery compare status, worker identity and attempt generation. A surviving owner can keep renewing its lease; a replaced owner cannot publish canonical database or locked vault writes. The runner checks expiry periodically after a fast restart. Losing ownership interrupts only that runner's active transport, not the replacement's batch or unrelated descendants.

A late provider response can finish only its own previously started call receipt, even after lease loss. This narrow observation write retains known spending while canonical publication remains fenced.

## Token-preserving ingestion

- Each validated inventory window, synthesis pass and completed shard has a durable checkpoint keyed by its actual inputs, schema and provider identity. An interrupted evidence expansion reuses the first pass. Completed model work survives later application errors.
- Inventory uses a bounded work queue with one client per worker. The runner accepts receipt/checkpoint events before acknowledging workers. Failures stop new work, interrupt active peers, and drain pending acknowledgements before shutdown.
- Stable task instructions precede changing context. Evidence expansion follows the full inventory prefix. This enables cache reuse; actual hit rate and cost improvements still require provider measurements.
- OpenAI-compatible SDK retries are disabled; the adapter owns the bounded 429/5xx retry policy. Truncation is recorded before parsing and does not trigger an identical repair. Repair output usage counts toward the operation's remaining budget.
- Synthesis preflights the complete prompt/schema for every uncached base pass, reserves remaining base input before evidence expansion, and checks cumulative output. Provider usage increases estimates when reported. Graph structuring receives only the remaining output budget.
- Codex receives an advisory output target and local budget checks. Its app-server protocol does not expose a documented hard per-turn output-token cap; this is not a billing guarantee. JSON repair stops when reported output has exhausted the available budget. [Codex app-server protocol](https://learn.chatgpt.com/docs/app-server).
- Cached study-map generation can resume apply/goal creation. Goal identity is stable for the same proposal. Legacy ingestion identity includes instructions, subject, purpose, prompt version and provider/model; v2-lite reuses the retained extraction and original bytes. Concurrent original-byte writers use separate temporary files.

## Desktop and local performance

Repository connections close deterministically. Queue computation and bulk DTO serialization reuse a connection during short local work. Native vault metadata has its own short mutex, resource handlers run file I/O off the request thread, and media requests read only the requested range. Same-vault reconnection restores the grading override; configured manual grading is healthy.

Reader hydrates each new terminal request while other requests continue, retries hydration failures, and keeps one poll in flight. Scope identities reject stale A→B→A results. Late close-listener registration is disposed. PDF fetches/workers are cleaned up on failure or vault change. Practice saves before vault selection and suppresses old-vault unmount writes; a failed save keeps the old vault open.

Large screens and pdf.js load on demand. The measured main JS chunk is 1,251.12 kB (370.82 kB gzip), compared with 2,126.66 kB in the review build. This is a bundle-size measurement, not an end-to-end startup benchmark; the main chunk still exceeds Vite's advisory threshold.

Queue measurements on disposable fixture copies, production connection settings, a fixed September 6 clock and no persisted explanations:

| Fixture | Unpinned, 3 samples | Reused connection, 3 samples | Returned items |
|---|---:|---:|---:|
| Migration-head conic sections | 55.0–63.1 ms | 3.19–3.21 ms | 5 |
| Linear algebra | 34.6–73.4 ms | 4.65–4.67 ms | 41 |

The complete serialized queues had identical SHA-256 hashes across modes. Unpinned ran first; these samples are illustrative, not a latency SLO. Raw results are in [queue-connections.json](artifacts/queue-connections.json).

## Collection and dataset contract

Keep `state.sqlite` as the transactional store for evidence, immutable receipts, workflow state and rebuildable projections. Splitting telemetry into another database would add a consistency boundary. Original source/media bytes remain in the content-addressed file store.

Migrations 159–163 add completion work, model-call receipts/checkpoints, immutable submission/offer provenance, collection metadata, and append-only false-remediation adjudications. Historical attempts remain `legacy-unversioned`; missing fields are not backfilled with guessed observations.

The desktop carries the actual offered candidate into its durable submission identity. Refreshing the queue cannot retarget it. Final offers record adapter filtering. Pre-action selection features are immutable; the earlier base draw probability is retained separately from the composed offer. Final learner-choice propensity is unavailable, so these rows cannot be used for inverse-propensity evaluation.

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

Exports require a new directory. SQLite's backup API establishes the snapshot; JSONL files contain selected evidence/receipts, candidate workflow records and versioned outcome/split views. The manifest is the completion marker and includes snapshot/schema/artifact/code hashes, migrations, versions, snapshot times, source-asset references and missingness. An interrupted export has no completion manifest. Corrections produce a new export.

Splits use chronological timestamp buckets and connected item/learning-object/source/family groups. Groups crossing boundaries are quarantined. Unknown origins or source provenance are ineligible; simulator and machine labels remain distinguishable. A small n=1 dataset can legitimately have no usable held-out partition. Inspect coverage before training; these changes do not certify a production dataset's completeness.

## SQLite concurrency decision

Run `uv run python scripts/benchmark_sqlite_concurrency.py --iterations 200 --directory .pytest_tmp` to reproduce the disposable benchmark. It uses FULL synchronous durability, one writer, two readers, 200 operations per worker, 2 KB writes and 2 ms held read snapshots. [Raw results](artifacts/sqlite-concurrency.json).

| Mode | Elapsed | Writer p95 | Busy failures | Integrity |
|---|---:|---:|---:|---|
| DELETE | 10.04 s | 68.38 ms | 2 reader operations | ok |
| WAL | 2.66 s | 23.45 ms | 0 | ok; checkpoint completed |

Production remains DELETE. WAL is promising, but this synthetic result does not qualify its production checkpoint, crash and backup lifecycle. Functional test settings (`synchronous=OFF`, memory journaling) never become production configuration.

## Test changes and verification

The basic-vault template is built once, checked for root-specific paths, and copied into each test's private directory. Fresh initialization/migration paths remain real. `fresh_vault` and `durability` markers bypass the template where required; `uv run pytest -m durability` uses production SQLite settings, and `--durable-sqlite` opts any selected tests into that lane.

Source/AST reads are shared. Duplicate schema and capability declarations were removed while unique negative cases remain. Resolver policy matrices stay at the resolver; adapter tests cover wiring and meaningful success/manual paths. Overlapping diagnostic and teach-back simulation runs share results without sharing mutable test state.

The new regression cases exercise interrupted completion/rebuild, ownership interleavings, window/evidence retry reuse, cumulative repair budgets, exact offer binding, immutable features/adjudication, consistent live backup, source-byte concurrency, and real React lifecycle ordering.

Final test totals and remaining limits are recorded in [implementation-progress.md](implementation-progress.md).

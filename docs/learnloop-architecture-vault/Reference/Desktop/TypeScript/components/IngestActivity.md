---
title: "Desktop module · src/components/IngestActivity.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.components.IngestActivity"
language: "TypeScript"
area: "TypeScript/components"
source_path: "apps/learnloop-tauri/src/components/IngestActivity.tsx"
source_paths:
  - "apps/learnloop-tauri/src/components/IngestActivity.tsx"
source_commit: "64d39668a1d275c2910f98388ac612ae5391d694"
source_commit_timestamp: "2026-07-27T19:00:47-05:00"
source_worktree_state: "clean"
activation_kind: "entry-reachable build graph"
activation_evidence: "A static TypeScript import path reaches this file from the Vite entry src/main.tsx."
generated: true
generated_at: "2026-08-18"
tags:
  - "learnloop/docs"
  - "learnloop/reference/module"
  - "learnloop/desktop"
  - "learnloop/desktop/typescript"
  - "refactor/active"
---

# `src/components/IngestActivity.tsx`

Area: [[Reference/Desktop/TypeScript/components/_area|TypeScript/components]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides the reusable `IngestActivity` interaction surface used by one or more desktop workflows.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/components/IngestActivity.tsx](../../../../../../apps/learnloop-tauri/src/components/IngestActivity.tsx) |
| Source lines | 786 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/components/_area|TypeScript/components]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `64d39668a1d275c2910f98388ac612ae5391d694` |
| Commit timestamp | `2026-07-27T19:00:47-05:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/IngestScreen|src/screens/IngestScreen.tsx]] → [[Reference/Desktop/TypeScript/components/IngestActivity|src/components/IngestActivity.tsx]]

## Public API

- `export function IngestActivityStack(` — function, line 107

## Internal implementation anchors

- `const STATUS_PILL: Record<DurableIngestStatus, PillColor> =` — const, line 19
- `const STATUS_COLOR: Record<DurableIngestStatus, string> =` — const, line 29
- `function statusLabel(status: DurableIngestStatus): string` — function, line 39
- `function isActive(status: DurableIngestStatus): boolean` — function, line 43
- `function relativeWhen(iso: string | null): string` — function, line 48
- `const then = Date.parse(iso)` — const, line 50
- `const seconds = Math.max(0, (Date.now() - then) / 1000)` — const, line 52
- `function Card(` — function, line 60
- `function batchTitle(batch: IngestBatchDto): string` — function, line 82
- `const title = job.result?.title` — const, line 84
- `const source = batch.jobs.find((job)` — const, line 87
- `function importedSourceId(batch: IngestBatchDto): string | null` — function, line 94
- `const isImport = (job: IngestJobView)` — const, line 96
- `const id = job.result.sourceId ?? job.result.source_id` — const, line 100
- `const reportedError = useRef(false)` — const, line 124
- `const onErrorRef = useRef(onError)` — const, line 125
- `const onBatchSettledRef = useRef(onBatchSettled)` — const, line 126
- `const seededBatchRef = useRef<IngestBatchDto | null>(null)` — const, line 127
- `const previousStatuses = useRef<Map<string, DurableIngestStatus>>(new Map())` — const, line 128
- `const upsertBatch = useCallback((next: IngestBatchDto)` — const, line 132
- `const index = prev.findIndex((batch)` — const, line 137
- `const updated = [...prev]` — const, line 139
- `let cancelled = false` — let, line 158
- `let cancelled = false` — let, line 174
- `let timer: number | undefined` — let, line 175
- `const poll = async ()` — const, line 176
- `const snapshot = await api.listIngestBatches(30)` — const, line 178
- `const seed = seededBatchRef.current` — const, line 180
- `let visibleBatches = snapshot.batches` — let, line 181
- `const active = visibleBatches.some((batch)` — const, line 192
- `const nextStatuses = new Map(previousStatuses.current)` — const, line 213
- `const previous = previousStatuses.current.get(batch.id)` — const, line 215
- `const patchBatch = useCallback((next: IngestBatchDto)` — const, line 225
- `const reportError = useCallback((message: string)` — const, line 229
- `const byNewest = (a: IngestBatchDto, b: IngestBatchDto)` — const, line 235
- `const act = batches.filter((batch)` — const, line 237
- `const fin = batches .filter((batch)` — const, line 238
- `function toggle(batchId: string)` — function, line 245
- `const next = new Set(prev)` — const, line 247
- `const open = expanded.has(batch.id) || batch.id === focusBatchId` — const, line 275
- `function CollapsedRow(` — function, line 295
- `const done = batch.jobs.filter((job)` — const, line 296
- `function BatchCard(` — function, line 333
- `const ref = useRef<HTMLDivElement>(null)` — const, line 348
- `const active = isActive(batch.status)` — const, line 349
- `const failedSynthesis = batch.jobs.find( (job)` — const, line 350
- `const inventoryOutputEstimate = batch.jobs .filter((job)` — const, line 355
- `const suggestedSynthesisCeiling = Math.max( 100_000, Math.ceil((inventoryOutputEstimate * 2) / 10_000) * 10_000 )` — const, line 358
- `const candidatePreserved = Boolean(failedSynthesis?.error?.details?.candidate_preserved)` — const, line 368
- `const synthesisCeilingValid = unlimitedTokenBudget || (synthesisCeiling >= 10_000 && synthesisCeiling <= 2_000_000)` — const, line 369
- `const synthesisOutputValid = unlimitedTokenBudget || (synthesisShardOutput >= 1_000 && synthesisShardOutput <= 200_000 && synthesisOutput >= 1_000 && synthesisOutput <= 200_000)` — const, line 370
- `const resumable = (batch.status === "failed" || batch.status === "cancelled") && !failedSynthesis` — const, line 372
- `const sourceId = importedSourceId(batch)` — const, line 373
- `let cancelled = false` — let, line 391
- `async function cancel()` — function, line 405
- `async function resume()` — function, line 413
- `async function retrySynthesis()` — function, line 421
- `async function revalidateCandidate(repairCandidate = false)` — function, line 439
- `function JobRow(` — function, line 606
- `const borderColor = STATUS_COLOR[job.status]` — const, line 607
- `function synthesisRecoveryMessage(code?: string): string` — function, line 638
- `function IngestErrorPanel(` — function, line 651
- `const diagnostics = error.details?.diagnostics ?? []` — const, line 652
- `const hardFailures = diagnostics.filter((item)` — const, line 653
- `function CheckpointLadder(` — function, line 692
- `const activeIndex = phase ? ladder.indexOf(phase) : -1` — const, line 701
- `const finished = status === "completed"` — const, line 705
- `const done = activeIndex >= 0 && (index < activeIndex || (finished && index === activeIndex))` — const, line 709
- `const current = !finished && index === activeIndex` — const, line 710
- `const failed = current && (status === "failed" || status === "blocked" || status === "cancelled")` — const, line 711
- `const color = failed ? COLOR.red : current ? COLOR.cyan : done ? COLOR.green : COLOR.textFaint` — const, line 712
- `function TokenBars(` — function, line 727
- `const keys = Array.from(new Set([...Object.keys(usage ||` — const, line 728
- `const actual = usage?.[key] ?? 0` — const, line 733
- `const est = estimate?.[key] ?? 0` — const, line 734
- `const denom = Math.max(actual, est, 1)` — const, line 735
- `const actualPct = Math.min(100, (actual / denom) * 100)` — const, line 736
- `function WaitingCard(` — function, line 754

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/IngestScreen|src/screens/IngestScreen.tsx]] — import-or-re-export: `IngestActivityStack`; references `IngestActivityStack`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `CommandError`, `DurableIngestStatus`, `IngestBatchDto`, `IngestJobView`, `SynthesisCandidateSummary`
- [[Reference/Desktop/TypeScript/components/sourceTail|src/components/sourceTail.ts]] — import-or-re-export; imports `readableSourceTail`
- [[Reference/Desktop/TypeScript/components/term|src/components/term.tsx]] — import-or-re-export; imports `COLOR`, `FONT_MONO`, `Faint`, `Pill`, `PillColor`, `TermCheckbox`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Import Canonical Sources|Import Canonical Sources]] — owns import sequencing.
- [[Architecture/Content Pipeline#Durable checkpoint ladder|content checkpoint ladder]] — owns pipeline persistence semantics.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [tests/test_sidecar_ingest_m3.py](../../../../../../tests/test_sidecar_ingest_m3.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_source_ingestion.py](../../../../../../tests/test_source_ingestion.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_ingest_runner.py](../../../../../../tests/test_ingest_runner.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_init.py](../../../../../../tests/test_init.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/components/IngestActivity.tsx](../../../../../../apps/learnloop-tauri/src/components/IngestActivity.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

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
| Source lines | 818 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/components/_area|TypeScript/components]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/IngestScreen|src/screens/IngestScreen.tsx]] → [[Reference/Desktop/TypeScript/components/IngestActivity|src/components/IngestActivity.tsx]]

## Public API

- `export function IngestActivityStack(` — function, line 110

## Internal implementation anchors

- `const STATUS_PILL: Record<DurableIngestStatus, PillColor> =` — const, line 23
- `const STATUS_COLOR: Record<DurableIngestStatus, string> =` — const, line 33
- `function statusLabel(status: DurableIngestStatus): string` — function, line 43
- `function isActive(status: DurableIngestStatus): boolean` — function, line 47
- `function relativeWhen(iso: string | null): string` — function, line 52
- `const then = Date.parse(iso)` — const, line 54
- `const seconds = Math.max(0, (Date.now() - then) / 1000)` — const, line 56
- `function Card(` — function, line 64
- `function batchTitle(batch: IngestBatchDto): string` — function, line 86
- `const title = job.result?.title` — const, line 88
- `const source = batch.jobs.find((job)` — const, line 91
- `function importedSourceId(batch: IngestBatchDto): string | null` — function, line 99
- `const id = job.result.sourceId ?? job.result.source_id` — const, line 103
- `const reportedError = useRef(false)` — const, line 127
- `const onErrorRef = useRef(onError)` — const, line 128
- `const onBatchSettledRef = useRef(onBatchSettled)` — const, line 129
- `const seededBatchRef = useRef<IngestBatchDto | null>(null)` — const, line 130
- `const previousStatuses = useRef<Map<string, DurableIngestStatus>>(new Map())` — const, line 131
- `const upsertBatch = useCallback((next: IngestBatchDto)` — const, line 135
- `const index = prev.findIndex((batch)` — const, line 140
- `const updated = [...prev]` — const, line 142
- `let cancelled = false` — let, line 161
- `let cancelled = false` — let, line 177
- `let timer: number | undefined` — let, line 178
- `const poll = async ()` — const, line 179
- `const snapshot = await api.listIngestBatches(30)` — const, line 181
- `const seed = seededBatchRef.current` — const, line 183
- `let visibleBatches = snapshot.batches` — let, line 184
- `const active = visibleBatches.some((batch)` — const, line 195
- `const nextStatuses = new Map(previousStatuses.current)` — const, line 216
- `const previous = previousStatuses.current.get(batch.id)` — const, line 218
- `const patchBatch = useCallback((next: IngestBatchDto)` — const, line 228
- `const reportError = useCallback((message: string)` — const, line 232
- `const byNewest = (a: IngestBatchDto, b: IngestBatchDto)` — const, line 238
- `const act = batches.filter((batch)` — const, line 240
- `const fin = batches .filter((batch)` — const, line 241
- `function toggle(batchId: string)` — function, line 248
- `const next = new Set(prev)` — const, line 250
- `const open = expanded.has(batch.id) || batch.id === focusBatchId` — const, line 278
- `function CollapsedRow(` — function, line 298
- `const done = batch.jobs.filter((job)` — const, line 299
- `function BatchCard(` — function, line 336
- `const ref = useRef<HTMLDivElement>(null)` — const, line 351
- `const active = isActive(batch.status)` — const, line 352
- `const failedSynthesis = batch.canRetrySynthesis ? batch.jobs.find((job)` — const, line 355
- `const settingsQuery = useCachedQuery(["get_settings"], ()` — const, line 358
- `const bounds = settingsQuery.data?.ingest.budgetBounds` — const, line 362
- `const inventoryOutputEstimate = batch.jobs .filter((job)` — const, line 363
- `const suggestedSynthesisCeiling = Math.max( 100_000, Math.ceil((inventoryOutputEstimate * 2) / 10_000) * 10_000 )` — const, line 366
- `const candidatePreserved = failedSynthesis !== undefined && batch.canReuseCandidate` — const, line 376
- `const synthesisCeilingValid = unlimitedTokenBudget || withinBounds(bounds, "synthesisTotalInputCeiling", synthesisCeiling)` — const, line 377
- `const synthesisOutputValid = unlimitedTokenBudget || (withinBounds(bounds, "synthesisShardOutputTokens", synthesisShardOutput) && withinBounds(bounds, "synthesisOutputTokens", synthesisOutput))` — const, line 378
- `const resumable = (batch.status === "failed" || batch.status === "cancelled") && !failedSynthesis` — const, line 380
- `const sourceId = importedSourceId(batch)` — const, line 381
- `const facetIdentity = batch.jobs .filter( (job)` — const, line 382
- `let cancelled = false` — let, line 407
- `async function cancel()` — function, line 421
- `async function resume()` — function, line 429
- `async function retrySynthesis()` — function, line 437
- `async function revalidateCandidate(repairCandidate = false)` — function, line 455
- `function JobRow(` — function, line 624
- `const borderColor = STATUS_COLOR[job.status]` — const, line 625
- `function withinBounds( bounds: IngestBudgetBoundsDto | undefined, field: keyof IngestBudgetBoundsDto, value: number ): boolean` — function, line 658
- `function synthesisRecoveryMessage(code?: string): string` — function, line 667
- `function IngestErrorPanel(` — function, line 683
- `const diagnostics = error.details?.diagnostics ?? []` — const, line 684
- `const hardFailures = diagnostics.filter((item)` — const, line 685
- `function CheckpointLadder(` — function, line 724
- `const activeIndex = phase ? ladder.indexOf(phase) : -1` — const, line 733
- `const finished = status === "completed"` — const, line 737
- `const done = activeIndex >= 0 && (index < activeIndex || (finished && index === activeIndex))` — const, line 741
- `const current = !finished && index === activeIndex` — const, line 742
- `const failed = current && (status === "failed" || status === "blocked" || status === "cancelled")` — const, line 743
- `const color = failed ? COLOR.red : current ? COLOR.cyan : done ? COLOR.green : COLOR.textFaint` — const, line 744
- `function TokenBars(` — function, line 759
- `const keys = Array.from(new Set([...Object.keys(usage ||` — const, line 760
- `const actual = usage?.[key] ?? 0` — const, line 765
- `const est = estimate?.[key] ?? 0` — const, line 766
- `const denom = Math.max(actual, est, 1)` — const, line 767
- `const actualPct = Math.min(100, (actual / denom) * 100)` — const, line 768
- `function WaitingCard(` — function, line 786

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/IngestScreen|src/screens/IngestScreen.tsx]] — import-or-re-export: `IngestActivityStack`; references `IngestActivityStack`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `CommandError`, `DurableIngestStatus`, `IngestBatchDto`, `IngestBudgetBoundsDto`, `IngestJobView`, `SynthesisCandidateSummary`
- [[Reference/Desktop/TypeScript/api/queryTags|src/api/queryTags.ts]] — import-or-re-export; imports `TAG`
- [[Reference/Desktop/TypeScript/api/useCachedQuery|src/api/useCachedQuery.ts]] — import-or-re-export; imports `useCachedQuery`
- [[Reference/Desktop/TypeScript/components/FacetIdentityPanel|src/components/FacetIdentityPanel.tsx]] — import-or-re-export; imports `FacetIdentityPanel`, `facetIdentityOf`
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

- [apps/learnloop-tauri/src/components/IngestActivity.eligibility.test.tsx](../../../../../../apps/learnloop-tauri/src/components/IngestActivity.eligibility.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [tests/test_sidecar_ingest_m3.py](../../../../../../tests/test_sidecar_ingest_m3.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_source_ingestion.py](../../../../../../tests/test_source_ingestion.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_ingest_runner.py](../../../../../../tests/test_ingest_runner.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_init.py](../../../../../../tests/test_init.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/components/IngestActivity.tsx](../../../../../../apps/learnloop-tauri/src/components/IngestActivity.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

---
title: "Desktop module · src/screens/reader/useCueImpressions.ts"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.reader.useCueImpressions"
language: "TypeScript"
area: "TypeScript/screens/reader"
source_path: "apps/learnloop-tauri/src/screens/reader/useCueImpressions.ts"
source_paths:
  - "apps/learnloop-tauri/src/screens/reader/useCueImpressions.ts"
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

# `src/screens/reader/useCueImpressions.ts`

Area: [[Reference/Desktop/TypeScript/screens/reader/_area|TypeScript/screens/reader]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides `IMPRESSION_FLUSH_MS`, `IMPRESSION_RETRY_MS`, `CUE_REFLOW_SETTLE_MS`, `passageThresholds` and related exports within the desktop's TypeScript/screens/reader ownership area.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/reader/useCueImpressions.ts](../../../../../../../apps/learnloop-tauri/src/screens/reader/useCueImpressions.ts) |
| Source lines | 353 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/reader/_area|TypeScript/screens/reader]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]] → [[Reference/Desktop/TypeScript/screens/reader/useReaderCues|src/screens/reader/useReaderCues.ts]] → [[Reference/Desktop/TypeScript/screens/reader/useCueImpressions|src/screens/reader/useCueImpressions.ts]]

## Public API

- `export const IMPRESSION_FLUSH_MS = 800` — const, line 34
- `export const IMPRESSION_RETRY_MS = 4_000` — const, line 36
- `export const CUE_REFLOW_SETTLE_MS = 150` — const, line 41
- `export function passageThresholds(passageHeight: number, areaHeight: number): number[]` — function, line 54
- `export interface CueImpressionsInput` — interface, line 61
- `export interface CueImpressions` — interface, line 75
- `export function passageInView(seen: IntersectionObserverEntry): boolean` — function, line 102
- `export function useCueImpressions(input: CueImpressionsInput): CueImpressions` — function, line 112

## Internal implementation anchors

- `const SEEN_THRESHOLD = 0.5` — const, line 38
- `const THRESHOLDS = [0, 0.25, 0.5, 0.75, 1]` — const, line 39
- `const SEEN_SLACK_PX = 1` — const, line 43
- `const needed = Math.min(1, (SEEN_THRESHOLD * areaHeight) / passageHeight)` — const, line 56
- `interface Queued` — interface, line 90
- `const visible = seen.intersectionRect?.height ?? 0` — const, line 105
- `const area = seen.rootBounds?.height ?? 0` — const, line 106
- `const discoveredCue = (cue: ReaderCueDto)` — const, line 110
- `const textAttribute = input.spanAttribute ?? "data-span-id"` — const, line 114
- `const discovery = cues?.discovery ?? null` — const, line 115
- `const localVisitRef = useRef<` — const, line 116
- `const sentRef = useRef<Set<string>>(new Set())` — const, line 117
- `const firstPlanRef = useRef<Map<string, string>>(new Map())` — const, line 119
- `const queueRef = useRef<Queued[]>([])` — const, line 120
- `const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null)` — const, line 121
- `const visitSourceRef = useRef<string | null>(extractionId)` — const, line 128
- `const currentVisit = useCallback((): string | null` — const, line 139
- `const flushRef = useRef<()` — const, line 148
- `const flush = useCallback(()` — const, line 149
- `const items = queueRef.current` — const, line 151
- `const batches = new Map<string, Queued[]>()` — const, line 153
- `const key = `$` — const, line 155
- `const retry = batch.filter((item)` — const, line 164
- `const queue = useCallback((key: string, entry: ReaderCueImpressionInput, seenOn?: string | null)` — const, line 174
- `const visit = currentVisit()` — const, line 175
- `const seenKey = `$` — const, line 182
- `const planId = firstPlanRef.current.get(seenKey) ?? seenOn ?? discovery.planId` — const, line 183
- `const once = `$` — const, line 185
- `const servedPlanId = discovery?.planId ?? null` — const, line 201
- `const rememberSeen = useCallback((cue: ReaderCueDto, planId?: string | null)` — const, line 206
- `const visit = currentVisit()` — const, line 207
- `const plan = planId ?? servedPlanId` — const, line 208
- `const seenKey = `$` — const, line 210
- `const planFor = useCallback((cue: ReaderCueDto): string | null` — const, line 213
- `const visit = currentVisit()` — const, line 214
- `const first = visit && extractionId ? firstPlanRef.current.get(`$` — const, line 215
- `const noteShown = useCallback((cue: ReaderCueDto, planId?: string | null)` — const, line 222
- `const noteFewer = useCallback((cue: ReaderCueDto)` — const, line 229
- `type Pending =` — type, line 237
- `const pending: Pending[] = []` — const, line 238
- `const pendingKey = pending.map((` — const, line 247
- `const pendingRef = useRef(pending)` — const, line 248
- `const hub = useListenerHub()` — const, line 250
- `const activityAllowed = useReadingActivityAllowed()` — const, line 253
- `const body = bodyRef.current` — const, line 256
- `const items = pendingRef.current` — const, line 257
- `const attribute = surface === "watch" ? "data-transcript-span" : textAttribute` — const, line 259
- `const bySpan = new Map<Element, Pending[]>()` — const, line 260
- `const element = body.querySelector(`[$` — const, line 262
- `const elements = [...bySpan.keys()]` — const, line 267
- `const counted = new Set<Element>()` — const, line 270
- `const thresholdsOf = (element: Element)` — const, line 272
- `const queueForPlan = queue` — const, line 277
- `const generation = observerGeneration()` — const, line 281
- `let keyOf = new Map<Element, string>()` — let, line 282
- `const build = ()` — const, line 285
- `const byThresholds = new Map<string,` — const, line 288
- `const thresholds = thresholdsOf(element)` — const, line 291
- `const key = thresholds.join(",")` — const, line 292
- `const group = byThresholds.get(key) ??` — const, line 294
- `let settle: ReturnType<typeof setTimeout> | null = null` — let, line 317
- `const recheck = ()` — const, line 318
- `const scheduleRecheck = ()` — const, line 327
- `const resizes = typeof ResizeObserver === "undefined" ? null : new ResizeObserver(scheduleRecheck)` — const, line 331
- `const offResize = hub.listen("window", "resize", scheduleRecheck)` — const, line 336

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/reader/useReaderCues|src/screens/reader/useReaderCues.ts]] — import-or-re-export: `useCueImpressions`; references `useCueImpressions`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `ReaderCueDto`, `ReaderCueImpressionInput`, `ReaderCuesDto`
- [[Reference/Desktop/TypeScript/screens/desks/lifecycle|src/screens/desks/lifecycle.tsx]] — import-or-re-export; imports `useListenerHub`, `useReadingActivityAllowed`
- [[Reference/Desktop/TypeScript/screens/reader/activity|src/screens/reader/activity.ts]] — import-or-re-export; imports `newActivityId`
- [[Reference/Desktop/TypeScript/screens/reader/cues|src/screens/reader/cues.ts]] — import-or-re-export; imports `CuePlacement`
- [[Reference/Desktop/TypeScript/screens/reader/observerGeneration|src/screens/reader/observerGeneration.ts]] — import-or-re-export; imports `observerGeneration`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Reader to Practice Workflow|Reader to Practice Workflow]] — owns the end-to-end reader sequence.
- [[Concepts/Reader Tutor and Teach-Back#Reader|Reader model]] — owns reader semantics.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/reader/rw3bReview.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/rw3bReview.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [tests/test_sidecar_reader.py](../../../../../../../tests/test_sidecar_reader.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_sidecar_reader_pdf_view.py](../../../../../../../tests/test_sidecar_reader_pdf_view.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_reader_render_views.py](../../../../../../../tests/test_reader_render_views.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_reader_requests.py](../../../../../../../tests/test_reader_requests.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/screens/reader/useCueImpressions.ts](../../../../../../../apps/learnloop-tauri/src/screens/reader/useCueImpressions.ts) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

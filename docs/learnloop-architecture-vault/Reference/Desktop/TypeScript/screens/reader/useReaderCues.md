---
title: "Desktop module · src/screens/reader/useReaderCues.ts"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.reader.useReaderCues"
language: "TypeScript"
area: "TypeScript/screens/reader"
source_path: "apps/learnloop-tauri/src/screens/reader/useReaderCues.ts"
source_paths:
  - "apps/learnloop-tauri/src/screens/reader/useReaderCues.ts"
source_commit: "c94882abe7a8f5a7cde491603d6abba8a4c0e2db"
source_commit_timestamp: "2026-10-22T16:58:30-04:00"
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

# `src/screens/reader/useReaderCues.ts`

Area: [[Reference/Desktop/TypeScript/screens/reader/_area|TypeScript/screens/reader]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides `CueCheckMeRequest`, `CueRequestOrigin`, `CueSurface`, `ReaderCuesInput` and related exports within the desktop's TypeScript/screens/reader ownership area.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/reader/useReaderCues.ts](../../../../../../../apps/learnloop-tauri/src/screens/reader/useReaderCues.ts) |
| Source lines | 545 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/reader/_area|TypeScript/screens/reader]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `c94882abe7a8f5a7cde491603d6abba8a4c0e2db` |
| Commit timestamp | `2026-10-22T16:58:30-04:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]] → [[Reference/Desktop/TypeScript/screens/reader/useReaderCues|src/screens/reader/useReaderCues.ts]]

## Public API

- `export interface CueCheckMeRequest` — interface, line 56
- `export interface CueRequestOrigin` — interface, line 64
- `export type CueSurface = "text" | "pdf" | "watch" | "none"` — type, line 69
- `export interface ReaderCuesInput` — interface, line 71
- `export interface ReaderCues` — interface, line 107
- `export function useReaderCues(input: ReaderCuesInput): ReaderCues` — function, line 167

## Internal implementation anchors

- `type CuePlacement, type CueSuppression, type PdfPageLayout, } from "./cues"` — type, line 48
- `interface PlacedIds` — interface, line 143
- `const NO_PLACEMENT: PlacedIds =` — const, line 151
- `const FOCUS_RETRIES = 10` — const, line 152
- `function sameHeldOut(a: PlacedIds, b: PlacedIds): boolean` — function, line 154
- `const left = [...(a.heldOutPlaced ?? []), ...(a.heldOutSuppressed ?? []).map((entry)` — const, line 155
- `const right = [...(b.heldOutPlaced ?? []), ...(b.heldOutSuppressed ?? []).map((entry)` — const, line 156
- `function samePlacement(a: PlacedIds, b: PlacedIds): boolean` — function, line 160
- `const working = input.working ?? false` — const, line 173
- `const cues = render && !offline && guidePlan?.cues && guidePlan.extractionId === render.extractionId ? guidePlan.cues : null` — const, line 174
- `const loggedRef = useRef<Set<string>>(new Set())` — const, line 183
- `const marksKey = [...(cues?.marks ?? []), ...(cues?.discovery?.heldOut ?? []).map((cue)` — const, line 184
- `const extractionId = render?.extractionId ?? null` — const, line 190
- `const visitRef = useRef(0)` — const, line 191
- `const sameVisit = useCallback((visit: number)` — const, line 198
- `const onResize = ()` — const, line 210
- `const heldOut = cues?.discovery?.heldOut` — const, line 218
- `const body = bodyRef.current` — const, line 223
- `let viewportHeight = body?.clientHeight ?? 0` — let, line 224
- `let positionOf: (spanId: string)` — let, line 225
- `const element = body.querySelector(`[data-span-id="$` — const, line 228
- `const tops = pdfPageTops(pdfLayout)` — const, line 234
- `const block = (pdfBlocks ?? []).find((entry)` — const, line 236
- `const scroller = body.querySelector("[data-transcript-scroller]")` — const, line 240
- `const element = body.querySelector(`[data-transcript-span="$` — const, line 243
- `const next = placeCueMarks(` — const, line 247
- `const ids: PlacedIds =` — const, line 257
- `const placement = useMemo<CuePlacement>(()` — const, line 272
- `const byId = new Map((cues?.marks ?? []).map((cue)` — const, line 273
- `const heldById = new Map((cues?.discovery?.heldOut ?? []).map((cue)` — const, line 274
- `const cue = byId.get(cueId)` — const, line 278
- `const cue = heldById.get(cueId)` — const, line 284
- `const discovery = cues?.discovery ?? null` — const, line 292
- `const funnelVisit = useCallback(()` — const, line 294
- `const impressions = useCueImpressions(` — const, line 295
- `const cuesRef = useRef(cues)` — const, line 299
- `const noteSeen = useCallback((cue: ReaderCueDto, planId?: string | null)` — const, line 301
- `const current = cuesRef.current` — const, line 302
- `const shownBySpan = useMemo(()` — const, line 316
- `const markOn = useCallback((spanId: string)` — const, line 317
- `const shownRef = useRef<ReaderCueDto[]>([])` — const, line 325
- `const focusMark = useCallback((cue: ReaderCueDto)` — const, line 327
- `const find = ()` — const, line 328
- `const present = find()` — const, line 335
- `let tries = 0` — let, line 341
- `const retry = ()` — const, line 342
- `const element = find()` — const, line 344
- `const onKey = (event: KeyboardEvent)` — const, line 352
- `const target = event.target` — const, line 356
- `const shown = shownRef.current` — const, line 358
- `const direction = event.key === "ArrowDown" ? 1 : -1` — const, line 360
- `const focused = (document.activeElement as HTMLElement | null)?.dataset?.cueMark ?? null` — const, line 361
- `let from = focused ? shown.findIndex((cue)` — let, line 362
- `const here = spanOrder.get(readingSpan ?? "") ?? -1` — const, line 364
- `const order = shown.map((cue)` — const, line 365
- `const at = direction === 1 ? order.findIndex((index)` — const, line 366
- `const next = stepMark(shown.length, from, direction)` — const, line 369
- `const tap = useCallback(async (cue: ReaderCueDto, action: "opened" | "check_me" | "not_relevant" | "not_relevant_undone", text?: string)` — const, line 378
- `const planId = impressions.planFor(cue) ?? cuesRef.current.discovery.planId` — const, line 384
- `const setPreferences = useCallback(async (change:` — const, line 391
- `const visit = visitRef.current` — const, line 393
- `const openEarlier = useCallback((cue: ReaderCueDto)` — const, line 405
- `const checkMe = useCallback((cue: ReaderCueDto)` — const, line 409
- `const visit = visitRef.current` — const, line 411
- `const origin: CueRequestOrigin =` — const, line 412
- `const check = result.check` — const, line 418
- `const notRelevant = useCallback((cue: ReaderCueDto, text: string)` — const, line 432
- `const visit = visitRef.current` — const, line 433
- `const receipt: CueReceipt =` — const, line 438
- `const density = cues?.density ?? "normal"` — const, line 459
- `const fewer = useCallback(()` — const, line 460
- `const previous = density` — const, line 461
- `const next = stepDown(previous)` — const, line 462
- `const offBook = useCallback(()` — const, line 475
- `const offEverywhere = useCallback(()` — const, line 488
- `const previous = density` — const, line 489
- `const setDensity = useCallback((next: CueDensity)` — const, line 503
- `const turnOnBook = useCallback(()` — const, line 509
- `const canTryFirst = Boolean(onTryFirst) && Boolean(discovery?.tryFirst)` — const, line 516
- `const tryFirst = useCallback((cue: ReaderCueDto)` — const, line 517
- `const planId = impressions.planFor(cue) ?? cuesRef.current?.discovery?.planId` — const, line 521
- `const fewerOn = useCallback((cue: ReaderCueDto)` — const, line 526
- `const discoveredTryFirst = discovery ? discovery.tryFirst : null` — const, line 530
- `const discovered = useMemo( ()` — const, line 531
- `const checkPhase = useCallback((cueId: string)` — const, line 534
- `const receipts = useMemo( ()` — const, line 535

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]] — import-or-re-export: `CueCheckMeRequest`, `CueRequestOrigin`, `useReaderCues`; references `CueCheckMeRequest`, `CueRequestOrigin`, `useReaderCues`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `CueDensity`, `ReaderCueDto`, `ReaderCuesDto`, `ReaderGuidePlanDto`, `ReaderPdfBlockDto`, `ReaderRenderViewDto`
- [[Reference/Desktop/TypeScript/app/keymap|src/app/keymap.ts]] — import-or-re-export; imports `screenLeavesKey`
- [[Reference/Desktop/TypeScript/errors|src/errors.ts]] — import-or-re-export; imports `errorMessage`
- [[Reference/Desktop/TypeScript/screens/reader/MarginMark|src/screens/reader/MarginMark.tsx]] — import-or-re-export; imports `CueCheckPhase`, `CueReceipt`
- [[Reference/Desktop/TypeScript/screens/reader/activity|src/screens/reader/activity.ts]] — import-or-re-export; imports `logReaderAction`
- [[Reference/Desktop/TypeScript/screens/reader/cues|src/screens/reader/cues.ts]] — import-or-re-export; imports `CUE_COPY`, `CuePlacement`, `CueSuppression`, `PdfPageLayout`, `pdfPageTops`, `pdfPassageTop`, `placeCueMarks`, `stepDown`, `stepMark`
- [[Reference/Desktop/TypeScript/screens/reader/useCueDiscovery|src/screens/reader/useCueDiscovery.ts]] — import-or-re-export; imports `useCueDiscovery`
- [[Reference/Desktop/TypeScript/screens/reader/useCueImpressions|src/screens/reader/useCueImpressions.ts]] — import-or-re-export; imports `useCueImpressions`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Reader to Practice Workflow|Reader to Practice Workflow]] — owns the end-to-end reader sequence.
- [[Concepts/Reader Tutor and Teach-Back#Reader|Reader model]] — owns reader semantics.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

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

1. Modify [apps/learnloop-tauri/src/screens/reader/useReaderCues.ts](../../../../../../../apps/learnloop-tauri/src/screens/reader/useReaderCues.ts) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

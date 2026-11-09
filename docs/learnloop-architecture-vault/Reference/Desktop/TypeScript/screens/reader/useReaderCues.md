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
| Source lines | 577 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/reader/_area|TypeScript/screens/reader]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]] → [[Reference/Desktop/TypeScript/screens/reader/useReaderCues|src/screens/reader/useReaderCues.ts]]

## Public API

- `export interface CueCheckMeRequest` — interface, line 57
- `export interface CueRequestOrigin extends SourceIdentity` — interface, line 69
- `export type CueSurface = "text" | "pdf" | "watch" | "none"` — type, line 74
- `export interface ReaderCuesInput` — interface, line 76
- `export interface ReaderCues` — interface, line 130
- `export function useReaderCues(input: ReaderCuesInput): ReaderCues` — function, line 190

## Internal implementation anchors

- `type CuePlacement, type CueSuppression, type PdfPageLayout, } from "./cues"` — type, line 49
- `interface PlacedIds` — interface, line 166
- `const NO_PLACEMENT: PlacedIds =` — const, line 174
- `const FOCUS_RETRIES = 10` — const, line 175
- `function sameHeldOut(a: PlacedIds, b: PlacedIds): boolean` — function, line 177
- `const left = [...(a.heldOutPlaced ?? []), ...(a.heldOutSuppressed ?? []).map((entry)` — const, line 178
- `const right = [...(b.heldOutPlaced ?? []), ...(b.heldOutSuppressed ?? []).map((entry)` — const, line 179
- `function samePlacement(a: PlacedIds, b: PlacedIds): boolean` — function, line 183
- `const spanAttribute = input.spanAttribute ?? "data-span-id"` — const, line 196
- `const working = input.working ?? false` — const, line 198
- `const cues = render && !offline && guidePlan?.cues && guidePlan.extractionId === render.extractionId ? guidePlan.cues : null` — const, line 199
- `const loggedRef = useRef<Set<string>>(new Set())` — const, line 208
- `const marksKey = [...(cues?.marks ?? []), ...(cues?.discovery?.heldOut ?? []).map((cue)` — const, line 209
- `const extractionId = render?.extractionId ?? null` — const, line 215
- `const visitRef = useRef(0)` — const, line 216
- `const sameVisit = useCallback((visit: number)` — const, line 223
- `const onResize = ()` — const, line 235
- `const heldOut = cues?.discovery?.heldOut` — const, line 243
- `const body = bodyRef.current` — const, line 248
- `let viewportHeight = body?.clientHeight ?? 0` — let, line 249
- `let positionOf: (spanId: string)` — let, line 250
- `const element = body.querySelector(`[$` — const, line 253
- `const tops = pdfPageTops(pdfLayout)` — const, line 259
- `const block = (pdfBlocks ?? []).find((entry)` — const, line 261
- `const scroller = body.querySelector("[data-transcript-scroller]")` — const, line 265
- `const element = body.querySelector(`[data-transcript-span="$` — const, line 268
- `const next = placeCueMarks(` — const, line 272
- `const ids: PlacedIds =` — const, line 282
- `const placement = useMemo<CuePlacement>(()` — const, line 297
- `const byId = new Map((cues?.marks ?? []).map((cue)` — const, line 298
- `const heldById = new Map((cues?.discovery?.heldOut ?? []).map((cue)` — const, line 299
- `const cue = byId.get(cueId)` — const, line 303
- `const cue = heldById.get(cueId)` — const, line 309
- `const discovery = cues?.discovery ?? null` — const, line 317
- `const funnelVisit = useCallback(()` — const, line 322
- `const impressions = useCueImpressions(` — const, line 323
- `const cuesRef = useRef(cues)` — const, line 330
- `const noteSeen = useCallback((cue: ReaderCueDto, planId?: string | null)` — const, line 332
- `const current = cuesRef.current` — const, line 333
- `const shownBySpan = useMemo(()` — const, line 347
- `const markOn = useCallback((spanId: string)` — const, line 348
- `const shownRef = useRef<ReaderCueDto[]>([])` — const, line 356
- `const focusMark = useCallback((cue: ReaderCueDto)` — const, line 358
- `const find = ()` — const, line 359
- `const present = find()` — const, line 366
- `let tries = 0` — let, line 372
- `const retry = ()` — const, line 373
- `const element = find()` — const, line 375
- `const onKey = (event: KeyboardEvent)` — const, line 383
- `const target = event.target` — const, line 388
- `const shown = shownRef.current` — const, line 390
- `const direction = event.key === "ArrowDown" ? 1 : -1` — const, line 392
- `const focused = (document.activeElement as HTMLElement | null)?.dataset?.cueMark ?? null` — const, line 393
- `let from = focused ? shown.findIndex((cue)` — let, line 394
- `const here = spanOrder.get(readingSpan ?? "") ?? -1` — const, line 396
- `const order = shown.map((cue)` — const, line 397
- `const at = direction === 1 ? order.findIndex((index)` — const, line 398
- `const next = stepMark(shown.length, from, direction)` — const, line 401
- `const tap = useCallback(async (cue: ReaderCueDto, action: "opened" | "check_me" | "not_relevant" | "not_relevant_undone", text?: string)` — const, line 410
- `const planId = impressions.planFor(cue) ?? cuesRef.current.discovery.planId` — const, line 416
- `const setPreferences = useCallback(async (change:` — const, line 423
- `const visit = visitRef.current` — const, line 425
- `const openEarlier = useCallback((cue: ReaderCueDto)` — const, line 437
- `const checkMe = useCallback((cue: ReaderCueDto)` — const, line 441
- `const visit = visitRef.current` — const, line 443
- `const origin: CueRequestOrigin =` — const, line 444
- `const check = result.check` — const, line 450
- `const notRelevant = useCallback((cue: ReaderCueDto, text: string)` — const, line 464
- `const visit = visitRef.current` — const, line 465
- `const receipt: CueReceipt =` — const, line 470
- `const density = cues?.density ?? "normal"` — const, line 491
- `const fewer = useCallback(()` — const, line 492
- `const previous = density` — const, line 493
- `const next = stepDown(previous)` — const, line 494
- `const offBook = useCallback(()` — const, line 507
- `const offEverywhere = useCallback(()` — const, line 520
- `const previous = density` — const, line 521
- `const setDensity = useCallback((next: CueDensity)` — const, line 535
- `const turnOnBook = useCallback(()` — const, line 541
- `const canTryFirst = Boolean(onTryFirst) && Boolean(discovery?.tryFirst)` — const, line 548
- `const tryFirst = useCallback((cue: ReaderCueDto)` — const, line 549
- `const planId = impressions.planFor(cue) ?? cuesRef.current?.discovery?.planId` — const, line 553
- `const fewerOn = useCallback((cue: ReaderCueDto)` — const, line 558
- `const discoveredTryFirst = discovery ? discovery.tryFirst : null` — const, line 562
- `const discovered = useMemo( ()` — const, line 563
- `const checkPhase = useCallback((cueId: string)` — const, line 566
- `const receipts = useMemo( ()` — const, line 567

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]] — import-or-re-export: `CueCheckMeRequest`, `CueRequestOrigin`, `useReaderCues`; references `CueCheckMeRequest`, `CueRequestOrigin`, `useReaderCues`
- [[Reference/Desktop/TypeScript/screens/reader/useSidePane|src/screens/reader/useSidePane.ts]] — import-or-re-export: `CueCheckMeRequest`, `CueRequestOrigin`, `useReaderCues`; references `CueCheckMeRequest`, `CueRequestOrigin`, `useReaderCues`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `CueDensity`, `ReaderCueDto`, `ReaderCuesDto`, `ReaderGuidePlanDto`, `ReaderPdfBlockDto`, `ReaderRenderViewDto`, `SourceIdentity`
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

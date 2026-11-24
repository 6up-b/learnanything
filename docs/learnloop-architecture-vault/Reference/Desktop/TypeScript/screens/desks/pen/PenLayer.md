---
title: "Desktop module · src/screens/desks/pen/PenLayer.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.desks.pen.PenLayer"
language: "TypeScript"
area: "TypeScript/screens/desks/pen"
source_path: "apps/learnloop-tauri/src/screens/desks/pen/PenLayer.tsx"
source_paths:
  - "apps/learnloop-tauri/src/screens/desks/pen/PenLayer.tsx"
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

# `src/screens/desks/pen/PenLayer.tsx`

Area: [[Reference/Desktop/TypeScript/screens/desks/pen/_area|TypeScript/screens/desks/pen]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Implements the `PenLayer` routed desktop screen and coordinates its learner-facing workflow state.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/desks/pen/PenLayer.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/desks/pen/PenLayer.tsx) |
| Source lines | 861 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/desks/pen/_area|TypeScript/screens/desks/pen]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/DeskShell|src/screens/desks/DeskShell.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/windows/SourceWindow|src/screens/desks/windows/SourceWindow.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/pen/PenLayer|src/screens/desks/pen/PenLayer.tsx]]

## Public API

- `export const PEN_WIDTH = 2.2` — const, line 42
- `export const STRIKE_WORDS = "I disagree / doesn't make sense"` — const, line 43
- `export function PenLayer(` — function, line 247

## Internal implementation anchors

- `type LocalRect, } from "./geometry"` — type, line 37
- `const WHOLE_BLOCK = 1_000_000` — const, line 45
- `type MarkKind = Exclude<StrokeKind, "ink">` — type, line 47
- `interface InkStroke` — interface, line 49
- `interface Mark` — interface, line 56
- `interface NoteState` — interface, line 71
- `function localStroke(host: HTMLElement, samples: Sample[], id: string): InkStroke` — function, line 82
- `const at = toLocal(host, s.x, s.y)` — const, line 86
- `function round(value: number): number` — function, line 94
- `function pathOf(points: ReadonlyArray<readonly number[]>): string` — function, line 98
- `const STROKE_CLASS: Record<Mark["kind"], string> =` — const, line 102
- `function chipAt(kind: MarkKind | "ink", box: Box): Point` — function, line 107
- `function chipOf(body: HTMLElement, kind: MarkKind | "ink", box: Box, text: string): NonNullable<Mark["chip"]>` — function, line 119
- `const at = chipAt(kind, box)` — const, line 120
- `const local = toLocal(body, at.x, at.y)` — const, line 121
- `function boxFrom(x0: number, y0: number, x1: number, y1: number): Box` — function, line 125
- `function grown(box: Box, by: number): Box` — function, line 129
- `function overlaps(a: Box, b: Box): boolean` — function, line 133
- `function union(a: Box, b: Box): Box` — function, line 137
- `function lineHeightOf(passage: HTMLElement): number` — function, line 143
- `const computed = parseFloat(passage.ownerDocument.defaultView?.getComputedStyle(passage).lineHeight ?? "")` — const, line 144
- `const walker = passage.ownerDocument.createTreeWalker(passage, NodeFilter.SHOW_TEXT)` — const, line 146
- `const range = passage.ownerDocument.createRange()` — const, line 149
- `const height = range.getClientRects()[0]?.height ?? 0` — const, line 152
- `const NOTE_BOX_WIDTH = 230` — const, line 159
- `function notePlace(body: HTMLElement, box: Box): Point` — function, line 163
- `const at = toLocal(body, box.x0, box.y1 + 4)` — const, line 164
- `const room = body.clientWidth + body.scrollLeft - NOTE_BOX_WIDTH` — const, line 165
- `interface ListedRow` — interface, line 169
- `interface ListedAnnotation` — interface, line 177
- `function anchorSegments(row: ListedRow): ListedAnnotation["segments"]` — function, line 186
- `const placed = row.placement` — const, line 187
- `const segments = (placed ? placed.segments : row.segments) ?? []` — const, line 190
- `const found = segments.flatMap((segment)` — const, line 191
- `function fold(text: string): string` — function, line 195
- `function moved(strokes: InkStroke[], dx: number, dy: number): InkStroke[]` — function, line 199
- `function restoreMark(body: HTMLElement, surface: PenSurface, annotationId: string, strokes: InkStroke[], annotation: ListedAnnotation): Omit<Mark, "inkId"> | null` — function, line 208
- `const client = (list: InkStroke[])` — const, line 209
- `const box = boxOf(client(strokes))` — const, line 210
- `const base =` — const, line 211
- `const segments = annotation.segments` — const, line 212
- `const element = (spanId: string)` — const, line 213
- `const place = (kind: Mark["kind"], dx: number, dy: number, rects: LocalRect[])` — const, line 214
- `const shifted = moved(strokes, dx, dy)` — const, line 215
- `const anchored = segments ? element(segments[0].spanId) : null` — const, line 219
- `const tall = box.y1 - box.y0 >= RECOGNIZER.bracket.minHeight && box.x1 - box.x0 <= RECOGNIZER.bracket.maxWidth` — const, line 224
- `const spanned = (segments ?? []).flatMap((segment)` — const, line 226
- `const rects = localRects(body, spanned.map((each)` — const, line 227
- `const today = passagesSpanned(body, box)` — const, line 228
- `const same = spanned.length === today.length && spanned.every((each, index)` — const, line 229
- `const kind = annotation.type === "disposition" ? "strike" : "underline"` — const, line 232
- `const ranges = (segments ?? []).flatMap((segment)` — const, line 233
- `const rects = ranges.flatMap((range)` — const, line 234
- `const first = ranges[0]?.getClientRects()[0]` — const, line 235
- `const middle = (box.y0 + box.y1) / 2` — const, line 238
- `const lineY = kind === "strike" ? middle : middle - RECOGNIZER.underlineAbove` — const, line 239
- `const today = rangeBetween(body,` — const, line 240
- `const todayText = today ? fold(today.toString()) : ""` — const, line 241
- `const target = first.top + first.height / 2 + (kind === "strike" ? 0 : RECOGNIZER.underlineAbove)` — const, line 243
- `const host = usePenHost()` — const, line 248
- `function PenLayerOn(` — function, line 253
- `const body = surface.body` — const, line 254
- `const lifecycle = useWindowLifecycle()` — const, line 255
- `const paused = useWindowPaused()` — const, line 256
- `const hostRef = useRef(host)` — const, line 260
- `const pausedRef = useRef(paused)` — const, line 262
- `const marksRef = useRef(marks)` — const, line 264
- `const input = useMemo(()` — const, line 266
- `const update = useCallback((id: string, change: (mark: Mark)` — const, line 268
- `const next = change(mark)` — const, line 271
- `const previous = body.style.isolation` — const, line 278
- `const measure = ()` — const, line 281
- `const observer = typeof ResizeObserver === "undefined" ? null : new ResizeObserver(measure)` — const, line 283
- `const penTypeRef = useRef<"pen" | "mouse">("pen")` — const, line 292
- `const openNote = useRef<` — const, line 294
- `const endNoteRef = useRef<(learnerText?: string)` — const, line 296
- `const undone = useRef(new Set<string>())` — const, line 298
- `const disposed = useRef(false)` — const, line 300
- `const removeAnnotation = useCallback((mark: Mark, annotationId: string)` — const, line 309
- `const text = "couldn't take this mark back · undo to try again"` — const, line 312
- `const persist = useCallback(async (mark: Mark, nodes: ReaderRawSelectionNode[], action: "highlight" | "disposition" | "interpretation", learnerText: string)` — const, line 317
- `const h = hostRef.current` — const, line 318
- `const inkId = h.mintId("ink")` — const, line 319
- `const receipt = await h.api.readerCapture(` — const, line 321
- `const annotationId = receipt.annotationId` — const, line 328
- `const finish = useCallback((samples: Sample[], pointerType: "pen" | "mouse")` — const, line 350
- `const points = samples.map((s)` — const, line 352
- `const recognition = recognize(points, pageOf(body))` — const, line 353
- `const h = hostRef.current` — const, line 355
- `const stroke = localStroke(body, samples, h.mintId("stroke"))` — const, line 356
- `const box = recognition.box` — const, line 357
- `const id = h.mintId("mark")` — const, line 358
- `const chipFor = (kind: MarkKind | "ink", text: string)` — const, line 359
- `const base: Mark =` — const, line 360
- `const open = openNote.current` — const, line 365
- `const beside = recognition.kind === "note" ? passageBeside(body, box) : null` — const, line 366
- `const at = notePlace(body, open.box)` — const, line 370
- `const grownBox = open.box` — const, line 371
- `const plainInk = (why: string)` — const, line 376
- `const inkId = h.mintId("ink")` — const, line 377
- `const range = wordsInLoop(body, points)` — const, line 384
- `const selection = body.ownerDocument.getSelection()` — const, line 389
- `const y = recognition.lineY ?? (box.y0 + box.y1) / 2` — const, line 397
- `const range = rangeBetween(body,` — const, line 398
- `const kind = recognition.kind` — const, line 403
- `const mark: Mark =` — const, line 404
- `const spanned = passagesSpanned(body, box)` — const, line 410
- `const mark: Mark =` — const, line 415
- `const nodes: ReaderRawSelectionNode[] = spanned.flatMap((element)` — const, line 418
- `const at = notePlace(body, box)` — const, line 428
- `const mark: Mark =` — const, line 429
- `const polls = useRef(new Map<string, ()` — const, line 446
- `const jobs = useRef(new Map<string, string>())` — const, line 448
- `const gone = (markId: string)` — const, line 449
- `const readNote = useCallback(async (markId: string, inkId: string)` — const, line 450
- `const h = hostRef.current` — const, line 451
- `const apply = (job: InkTranscribeJobDto): boolean` — const, line 460
- `const note = mark.note` — const, line 464
- `const words = job.result.latexMd` — const, line 466
- `const nothing = job.result.confidenceLabel === "nothing_read"` — const, line 467
- `const code = job.error?.code ?? job.status` — const, line 471
- `const refusal = inkRefusal(code)` — const, line 472
- `const first = await h.api.inkTranscribe(` — const, line 481
- `const jobId = first.jobId` — const, line 488
- `const remove = h.poller.register<InkTranscribeJobDto>(` — const, line 490
- `const done = apply(job)` — const, line 495
- `const code = error && typeof error === "object" && "code" in error ? String((error as` — const, line 510
- `const stopReading = useCallback((markId: string)` — const, line 517
- `const jobId = jobs.current.get(markId)` — const, line 520
- `const open = openNote.current` — const, line 530
- `const mark = marksRef.current.find((each)` — const, line 533
- `const kept: Mark =` — const, line 535
- `const nodes: ReaderRawSelectionNode[] = [` — const, line 537
- `const onKey = (event: KeyboardEvent)` — const, line 544
- `const target = event.target as Element | null` — const, line 546
- `const doc = body.ownerDocument` — const, line 550
- `const eraseStrokes = useCallback((mark: Mark, strokeIds: string[])` — const, line 560
- `const strokes = current.strokes.filter((stroke)` — const, line 563
- `const dropFromOpenNote = useCallback((mark: Mark, strokeIds: string[])` — const, line 569
- `const open = openNote.current` — const, line 570
- `const strokes = open.strokes` — const, line 579
- `const box = open.box` — const, line 580
- `const undo = useCallback((mark: Mark)` — const, line 584
- `const open = openNote.current` — const, line 589
- `const keepNote = useCallback((mark: Mark, text: string)` — const, line 602
- `const words = text.trim()` — const, line 603
- `let live = true` — let, line 619
- `const h = hostRef.current` — const, line 620
- `const known = new Map<string, ListedAnnotation>()` — const, line 624
- `const id = row?.annotation?.id` — const, line 626
- `const restored: Mark[] = []` — const, line 629
- `const strokes: InkStroke[] = owner.strokes.map((stroke)` — const, line 632
- `const box = boxOf(strokes.flatMap((stroke)` — const, line 633
- `const annotation = known.get(owner.ownerId)` — const, line 638
- `const saved = restoreMark(body, surface, owner.ownerId, owner.strokes.map((stroke)` — const, line 640
- `const mark: Mark =` — const, line 642
- `const at = notePlace(body, mark.box)` — const, line 644
- `const reading = owner.transcription` — const, line 645
- `const asPointer = (event: PointerEvent): PointerLike` — const, line 659
- `const erased = new Set<string>()` — const, line 660
- `const onDown = (event: PointerEvent)` — const, line 661
- `const target = event.target as Element | null` — const, line 664
- `const outcome = input.down(asPointer(event), hostRef.current.on)` — const, line 666
- `const onMove = (event: PointerEvent)` — const, line 677
- `const samples = input.move(asPointer(event))` — const, line 683
- `const onUp = (event: PointerEvent)` — const, line 691
- `const stroke = input.up(asPointer(event))` — const, line 692
- `const onCancel = ()` — const, line 697
- `const erase = (samples: Sample[])` — const, line 701
- `const at = toLocal(body, sample.x, sample.y)` — const, line 703
- `const hit = mark.strokes.filter((stroke)` — const, line 706
- `const lassoShown = marks.some((mark)` — const, line 739
- `const layer: ReactNode = ( <> <div className="desk-pen-marks" aria-hidden="true" style=` — const, line 753
- `function Chip(` — function, line 794
- `const ref = useRef<HTMLDivElement | null>(null)` — const, line 795
- `const width = ref.current?.offsetWidth ?? 0` — const, line 798
- `const left = Math.max(body.scrollLeft, Math.min(x, body.clientWidth + body.scrollLeft - width))` — const, line 799
- `const top = left < x ? Math.max(y, below) : y` — const, line 801
- `function NoteBox(` — function, line 807
- `const note = mark.note!` — const, line 808
- `const dirtyRef = useRef(dirty)` — const, line 813
- `const offered = dirty && note.source === "reading" && note.text && note.text !== text ? note.text : null` — const, line 818
- `const keep = (words: string)` — const, line 819
- `const label = note.readingLabel ?? (note.reading === "reading" ? "reading your handwriting…" : mark.state === "saving" ? "keeping your note…" : "handwritten")` — const, line 823

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/desks/windows/SourceWindow|src/screens/desks/windows/SourceWindow.tsx]] — import-or-re-export: `PenLayer`; references `PenLayer`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `InkTranscribeJobDto`, `ReaderRawSelectionNode`
- [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]] — import-or-re-export; imports `PenSurface`
- [[Reference/Desktop/TypeScript/screens/desks/lifecycle|src/screens/desks/lifecycle.tsx]] — import-or-re-export; imports `useWindowLifecycle`, `useWindowPaused`
- [[Reference/Desktop/TypeScript/screens/desks/pen/geometry|src/screens/desks/pen/geometry.ts]] — import-or-re-export; imports `LocalRect`, `distanceToPolyline`, `localRects`, `pageOf`, `passageBeside`, `passages`, `passagesSpanned`, `rangeBetween`, `rangeOfQuote`, `toClient`, `toLocal`, `wordsInLoop`
- [[Reference/Desktop/TypeScript/screens/desks/pen/host|src/screens/desks/pen/host.ts]] — import-or-re-export; imports `PenHost`, `usePenHost`
- [[Reference/Desktop/TypeScript/screens/desks/pen/inkCache|src/screens/desks/pen/inkCache.ts]] — import-or-re-export; imports `inkRefusal`
- [[Reference/Desktop/TypeScript/screens/desks/pen/input|src/screens/desks/pen/input.ts]] — import-or-re-export; imports `PenInput`, `PointerLike`, `Sample`
- [[Reference/Desktop/TypeScript/screens/desks/pen/recognizer|src/screens/desks/pen/recognizer.ts]] — import-or-re-export; imports `Box`, `Point`, `RECOGNIZED_AS`, `RECOGNIZER`, `StrokeKind`, `boxOf`, `recognize`

### Assets, platform, and third-party dependencies

- Local asset: [apps/learnloop-tauri/src/screens/desks/pen/pen.css](../../../../../../../../apps/learnloop-tauri/src/screens/desks/pen/pen.css)
- Imported packages/crates: `react`, `react-dom`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/desks/pen/PenLayer.test.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/desks/pen/PenLayer.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/screens/desks/pen/PenLayer.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/desks/pen/PenLayer.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

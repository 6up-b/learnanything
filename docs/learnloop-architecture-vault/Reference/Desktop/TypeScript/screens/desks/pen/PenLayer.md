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
| Source lines | 859 |
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

- `export const PEN_WIDTH = 2.2` — const, line 41
- `export const STRIKE_WORDS = "I disagree / doesn't make sense"` — const, line 42
- `export function PenLayer(` — function, line 246

## Internal implementation anchors

- `type LocalRect, } from "./geometry"` — type, line 36
- `const WHOLE_BLOCK = 1_000_000` — const, line 44
- `type MarkKind = Exclude<StrokeKind, "ink">` — type, line 46
- `interface InkStroke` — interface, line 48
- `interface Mark` — interface, line 55
- `interface NoteState` — interface, line 70
- `function localStroke(host: HTMLElement, samples: Sample[], id: string): InkStroke` — function, line 81
- `const at = toLocal(host, s.x, s.y)` — const, line 85
- `function round(value: number): number` — function, line 93
- `function pathOf(points: ReadonlyArray<readonly number[]>): string` — function, line 97
- `const STROKE_CLASS: Record<Mark["kind"], string> =` — const, line 101
- `function chipAt(kind: MarkKind | "ink", box: Box): Point` — function, line 106
- `function chipOf(body: HTMLElement, kind: MarkKind | "ink", box: Box, text: string): NonNullable<Mark["chip"]>` — function, line 118
- `const at = chipAt(kind, box)` — const, line 119
- `const local = toLocal(body, at.x, at.y)` — const, line 120
- `function boxFrom(x0: number, y0: number, x1: number, y1: number): Box` — function, line 124
- `function grown(box: Box, by: number): Box` — function, line 128
- `function overlaps(a: Box, b: Box): boolean` — function, line 132
- `function union(a: Box, b: Box): Box` — function, line 136
- `function lineHeightOf(passage: HTMLElement): number` — function, line 142
- `const computed = parseFloat(passage.ownerDocument.defaultView?.getComputedStyle(passage).lineHeight ?? "")` — const, line 143
- `const walker = passage.ownerDocument.createTreeWalker(passage, NodeFilter.SHOW_TEXT)` — const, line 145
- `const range = passage.ownerDocument.createRange()` — const, line 148
- `const height = range.getClientRects()[0]?.height ?? 0` — const, line 151
- `const NOTE_BOX_WIDTH = 230` — const, line 158
- `function notePlace(body: HTMLElement, box: Box): Point` — function, line 162
- `const at = toLocal(body, box.x0, box.y1 + 4)` — const, line 163
- `const room = body.clientWidth + body.scrollLeft - NOTE_BOX_WIDTH` — const, line 164
- `interface ListedRow` — interface, line 168
- `interface ListedAnnotation` — interface, line 176
- `function anchorSegments(row: ListedRow): ListedAnnotation["segments"]` — function, line 185
- `const placed = row.placement` — const, line 186
- `const segments = (placed ? placed.segments : row.segments) ?? []` — const, line 189
- `const found = segments.flatMap((segment)` — const, line 190
- `function fold(text: string): string` — function, line 194
- `function moved(strokes: InkStroke[], dx: number, dy: number): InkStroke[]` — function, line 198
- `function restoreMark(body: HTMLElement, surface: PenSurface, annotationId: string, strokes: InkStroke[], annotation: ListedAnnotation): Omit<Mark, "inkId"> | null` — function, line 207
- `const client = (list: InkStroke[])` — const, line 208
- `const box = boxOf(client(strokes))` — const, line 209
- `const base =` — const, line 210
- `const segments = annotation.segments` — const, line 211
- `const element = (spanId: string)` — const, line 212
- `const place = (kind: Mark["kind"], dx: number, dy: number, rects: LocalRect[])` — const, line 213
- `const shifted = moved(strokes, dx, dy)` — const, line 214
- `const anchored = segments ? element(segments[0].spanId) : null` — const, line 218
- `const tall = box.y1 - box.y0 >= RECOGNIZER.bracket.minHeight && box.x1 - box.x0 <= RECOGNIZER.bracket.maxWidth` — const, line 223
- `const spanned = (segments ?? []).flatMap((segment)` — const, line 225
- `const rects = localRects(body, spanned.map((each)` — const, line 226
- `const today = passagesSpanned(body, box)` — const, line 227
- `const same = spanned.length === today.length && spanned.every((each, index)` — const, line 228
- `const kind = annotation.type === "disposition" ? "strike" : "underline"` — const, line 231
- `const ranges = (segments ?? []).flatMap((segment)` — const, line 232
- `const rects = ranges.flatMap((range)` — const, line 233
- `const first = ranges[0]?.getClientRects()[0]` — const, line 234
- `const middle = (box.y0 + box.y1) / 2` — const, line 237
- `const lineY = kind === "strike" ? middle : middle - RECOGNIZER.underlineAbove` — const, line 238
- `const today = rangeBetween(body,` — const, line 239
- `const todayText = today ? fold(today.toString()) : ""` — const, line 240
- `const target = first.top + first.height / 2 + (kind === "strike" ? 0 : RECOGNIZER.underlineAbove)` — const, line 242
- `const host = usePenHost()` — const, line 247
- `function PenLayerOn(` — function, line 252
- `const body = surface.body` — const, line 253
- `const lifecycle = useWindowLifecycle()` — const, line 254
- `const paused = useWindowPaused()` — const, line 255
- `const hostRef = useRef(host)` — const, line 259
- `const pausedRef = useRef(paused)` — const, line 261
- `const marksRef = useRef(marks)` — const, line 263
- `const input = useMemo(()` — const, line 265
- `const update = useCallback((id: string, change: (mark: Mark)` — const, line 267
- `const next = change(mark)` — const, line 270
- `const previous = body.style.isolation` — const, line 277
- `const measure = ()` — const, line 280
- `const observer = typeof ResizeObserver === "undefined" ? null : new ResizeObserver(measure)` — const, line 282
- `const penTypeRef = useRef<"pen" | "mouse">("pen")` — const, line 291
- `const openNote = useRef<` — const, line 293
- `const endNoteRef = useRef<(learnerText?: string)` — const, line 295
- `const undone = useRef(new Set<string>())` — const, line 297
- `const disposed = useRef(false)` — const, line 299
- `const removeAnnotation = useCallback((mark: Mark, annotationId: string)` — const, line 308
- `const text = "couldn't take this mark back · undo to try again"` — const, line 311
- `const persist = useCallback(async (mark: Mark, nodes: ReaderRawSelectionNode[], action: "highlight" | "disposition" | "interpretation", learnerText: string)` — const, line 316
- `const h = hostRef.current` — const, line 317
- `const inkId = h.mintId("ink")` — const, line 318
- `const receipt = await h.api.readerCapture(` — const, line 320
- `const annotationId = receipt.annotationId` — const, line 327
- `const finish = useCallback((samples: Sample[], pointerType: "pen" | "mouse")` — const, line 349
- `const points = samples.map((s)` — const, line 351
- `const recognition = recognize(points, pageOf(body))` — const, line 352
- `const h = hostRef.current` — const, line 354
- `const stroke = localStroke(body, samples, h.mintId("stroke"))` — const, line 355
- `const box = recognition.box` — const, line 356
- `const id = h.mintId("mark")` — const, line 357
- `const chipFor = (kind: MarkKind | "ink", text: string)` — const, line 358
- `const base: Mark =` — const, line 359
- `const open = openNote.current` — const, line 364
- `const beside = recognition.kind === "note" ? passageBeside(body, box) : null` — const, line 365
- `const at = notePlace(body, open.box)` — const, line 369
- `const grownBox = open.box` — const, line 370
- `const plainInk = (why: string)` — const, line 375
- `const inkId = h.mintId("ink")` — const, line 376
- `const range = wordsInLoop(body, points)` — const, line 383
- `const selection = body.ownerDocument.getSelection()` — const, line 388
- `const y = recognition.lineY ?? (box.y0 + box.y1) / 2` — const, line 396
- `const range = rangeBetween(body,` — const, line 397
- `const kind = recognition.kind` — const, line 402
- `const mark: Mark =` — const, line 403
- `const spanned = passagesSpanned(body, box)` — const, line 409
- `const mark: Mark =` — const, line 414
- `const nodes: ReaderRawSelectionNode[] = spanned.flatMap((element)` — const, line 417
- `const at = notePlace(body, box)` — const, line 427
- `const mark: Mark =` — const, line 428
- `const polls = useRef(new Map<string, ()` — const, line 445
- `const jobs = useRef(new Map<string, string>())` — const, line 447
- `const gone = (markId: string)` — const, line 448
- `const readNote = useCallback(async (markId: string, inkId: string)` — const, line 449
- `const h = hostRef.current` — const, line 450
- `const apply = (job: InkTranscribeJobDto): boolean` — const, line 459
- `const note = mark.note` — const, line 463
- `const words = job.result.latexMd` — const, line 465
- `const nothing = job.result.confidenceLabel === "nothing_read"` — const, line 466
- `const code = job.error?.code ?? job.status` — const, line 470
- `const first = await h.api.inkTranscribe(` — const, line 479
- `const jobId = first.jobId` — const, line 486
- `const remove = h.poller.register<InkTranscribeJobDto>(` — const, line 488
- `const done = apply(job)` — const, line 493
- `const code = error && typeof error === "object" && "code" in error ? String((error as` — const, line 508
- `const stopReading = useCallback((markId: string)` — const, line 515
- `const jobId = jobs.current.get(markId)` — const, line 518
- `const open = openNote.current` — const, line 528
- `const mark = marksRef.current.find((each)` — const, line 531
- `const kept: Mark =` — const, line 533
- `const nodes: ReaderRawSelectionNode[] = [` — const, line 535
- `const onKey = (event: KeyboardEvent)` — const, line 542
- `const target = event.target as Element | null` — const, line 544
- `const doc = body.ownerDocument` — const, line 548
- `const eraseStrokes = useCallback((mark: Mark, strokeIds: string[])` — const, line 558
- `const strokes = current.strokes.filter((stroke)` — const, line 561
- `const dropFromOpenNote = useCallback((mark: Mark, strokeIds: string[])` — const, line 567
- `const open = openNote.current` — const, line 568
- `const strokes = open.strokes` — const, line 577
- `const box = open.box` — const, line 578
- `const undo = useCallback((mark: Mark)` — const, line 582
- `const open = openNote.current` — const, line 587
- `const keepNote = useCallback((mark: Mark, text: string)` — const, line 600
- `const words = text.trim()` — const, line 601
- `let live = true` — let, line 617
- `const h = hostRef.current` — const, line 618
- `const known = new Map<string, ListedAnnotation>()` — const, line 622
- `const id = row?.annotation?.id` — const, line 624
- `const restored: Mark[] = []` — const, line 627
- `const strokes: InkStroke[] = owner.strokes.map((stroke)` — const, line 630
- `const box = boxOf(strokes.flatMap((stroke)` — const, line 631
- `const annotation = known.get(owner.ownerId)` — const, line 636
- `const saved = restoreMark(body, surface, owner.ownerId, owner.strokes.map((stroke)` — const, line 638
- `const mark: Mark =` — const, line 640
- `const at = notePlace(body, mark.box)` — const, line 642
- `const reading = owner.transcription` — const, line 643
- `const asPointer = (event: PointerEvent): PointerLike` — const, line 657
- `const erased = new Set<string>()` — const, line 658
- `const onDown = (event: PointerEvent)` — const, line 659
- `const target = event.target as Element | null` — const, line 662
- `const outcome = input.down(asPointer(event), hostRef.current.on)` — const, line 664
- `const onMove = (event: PointerEvent)` — const, line 675
- `const samples = input.move(asPointer(event))` — const, line 681
- `const onUp = (event: PointerEvent)` — const, line 689
- `const stroke = input.up(asPointer(event))` — const, line 690
- `const onCancel = ()` — const, line 695
- `const erase = (samples: Sample[])` — const, line 699
- `const at = toLocal(body, sample.x, sample.y)` — const, line 701
- `const hit = mark.strokes.filter((stroke)` — const, line 704
- `const lassoShown = marks.some((mark)` — const, line 737
- `const layer: ReactNode = ( <> <div className="desk-pen-marks" aria-hidden="true" style=` — const, line 751
- `function Chip(` — function, line 792
- `const ref = useRef<HTMLDivElement | null>(null)` — const, line 793
- `const width = ref.current?.offsetWidth ?? 0` — const, line 796
- `const left = Math.max(body.scrollLeft, Math.min(x, body.clientWidth + body.scrollLeft - width))` — const, line 797
- `const top = left < x ? Math.max(y, below) : y` — const, line 799
- `function NoteBox(` — function, line 805
- `const note = mark.note!` — const, line 806
- `const dirtyRef = useRef(dirty)` — const, line 811
- `const offered = dirty && note.source === "reading" && note.text && note.text !== text ? note.text : null` — const, line 816
- `const keep = (words: string)` — const, line 817
- `const label = note.readingLabel ?? (note.reading === "reading" ? "reading your handwriting…" : mark.state === "saving" ? "keeping your note…" : "handwritten")` — const, line 821

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

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
| Source lines | 605 |
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

- `export const PEN_WIDTH = 2.2` — const, line 39
- `export const STRIKE_WORDS = "I disagree / doesn't make sense"` — const, line 40
- `export function PenLayer(` — function, line 126

## Internal implementation anchors

- `type LocalRect, } from "./geometry"` — type, line 34
- `const WHOLE_BLOCK = 1_000_000` — const, line 42
- `type MarkKind = Exclude<StrokeKind, "ink">` — type, line 44
- `interface InkStroke` — interface, line 46
- `interface Mark` — interface, line 53
- `interface NoteState` — interface, line 68
- `function localStroke(host: HTMLElement, samples: Sample[], id: string): InkStroke` — function, line 79
- `const at = toLocal(host, s.x, s.y)` — const, line 83
- `function round(value: number): number` — function, line 91
- `function pathOf(points: ReadonlyArray<readonly number[]>): string` — function, line 95
- `const STROKE_CLASS: Record<Mark["kind"], string> =` — const, line 99
- `function chipAt(kind: MarkKind | "ink", box: Box): Point` — function, line 104
- `const NOTE_BOX_WIDTH = 230` — const, line 116
- `function notePlace(body: HTMLElement, box: Box): Point` — function, line 120
- `const at = toLocal(body, box.x0, box.y1 + 4)` — const, line 121
- `const room = body.clientWidth + body.scrollLeft - NOTE_BOX_WIDTH` — const, line 122
- `const host = usePenHost()` — const, line 127
- `function PenLayerOn(` — function, line 132
- `const body = surface.body` — const, line 133
- `const lifecycle = useWindowLifecycle()` — const, line 134
- `const paused = useWindowPaused()` — const, line 135
- `const hostRef = useRef(host)` — const, line 139
- `const pausedRef = useRef(paused)` — const, line 141
- `const marksRef = useRef(marks)` — const, line 143
- `const input = useMemo(()` — const, line 145
- `const update = useCallback((id: string, change: (mark: Mark)` — const, line 147
- `const next = change(mark)` — const, line 150
- `const previous = body.style.isolation` — const, line 157
- `const measure = ()` — const, line 160
- `const observer = typeof ResizeObserver === "undefined" ? null : new ResizeObserver(measure)` — const, line 162
- `const penTypeRef = useRef<"pen" | "mouse">("pen")` — const, line 171
- `const persist = useCallback(async (mark: Mark, nodes: ReaderRawSelectionNode[], action: "highlight" | "disposition" | "interpretation", learnerText: string)` — const, line 172
- `const h = hostRef.current` — const, line 173
- `const inkId = h.mintId("ink")` — const, line 174
- `const receipt = await h.api.readerCapture(` — const, line 176
- `const annotationId = receipt.annotationId` — const, line 183
- `const finish = useCallback((samples: Sample[], pointerType: "pen" | "mouse")` — const, line 199
- `const points = samples.map((s)` — const, line 201
- `const recognition = recognize(points, pageOf(body))` — const, line 202
- `const h = hostRef.current` — const, line 204
- `const stroke = localStroke(body, samples, h.mintId("stroke"))` — const, line 205
- `const box = recognition.box` — const, line 206
- `const id = h.mintId("mark")` — const, line 207
- `const chipFor = (kind: MarkKind | "ink", text: string)` — const, line 208
- `const at = chipAt(kind, box)` — const, line 209
- `const local = toLocal(body, at.x, at.y)` — const, line 210
- `const base: Mark =` — const, line 213
- `const plainInk = (why: string)` — const, line 216
- `const inkId = h.mintId("ink")` — const, line 217
- `const range = wordsInLoop(body, points)` — const, line 224
- `const selection = body.ownerDocument.getSelection()` — const, line 229
- `const y = recognition.lineY ?? (box.y0 + box.y1) / 2` — const, line 237
- `const range = rangeBetween(body,` — const, line 238
- `const kind = recognition.kind` — const, line 243
- `const mark: Mark =` — const, line 244
- `const spanned = passagesSpanned(body, box)` — const, line 250
- `const mark: Mark =` — const, line 255
- `const nodes: ReaderRawSelectionNode[] = spanned.flatMap((element)` — const, line 258
- `const beside = passageBeside(body, box)` — const, line 263
- `const at = notePlace(body, box)` — const, line 268
- `const mark: Mark =` — const, line 269
- `const nodes: ReaderRawSelectionNode[] = [` — const, line 274
- `const polls = useRef(new Map<string, ()` — const, line 289
- `const readNote = useCallback(async (markId: string, inkId: string)` — const, line 290
- `const h = hostRef.current` — const, line 291
- `const apply = (job: InkTranscribeJobDto): boolean` — const, line 297
- `const note = mark.note` — const, line 301
- `const words = job.result.latexMd` — const, line 303
- `const nothing = job.result.confidenceLabel === "nothing_read"` — const, line 304
- `const code = job.error?.code ?? job.status` — const, line 308
- `const first = await h.api.inkTranscribe(` — const, line 317
- `const jobId = first.jobId` — const, line 319
- `const remove = h.poller.register<InkTranscribeJobDto>(` — const, line 320
- `const done = apply(job)` — const, line 325
- `const code = error && typeof error === "object" && "code" in error ? String((error as` — const, line 337
- `const eraseStrokes = useCallback((mark: Mark, strokeIds: string[])` — const, line 347
- `const strokes = current.strokes.filter((stroke)` — const, line 350
- `const undo = useCallback((mark: Mark)` — const, line 355
- `const h = hostRef.current` — const, line 356
- `const keepNote = useCallback((mark: Mark, text: string)` — const, line 368
- `const words = text.trim()` — const, line 370
- `let live = true` — let, line 378
- `const h = hostRef.current` — const, line 379
- `const sourceId = surface.identity.sourceId` — const, line 380
- `const kinds = new Map<string,` — const, line 383
- `const restored: Mark[] = []` — const, line 387
- `const strokes: InkStroke[] = owner.strokes.map((stroke)` — const, line 390
- `const box = boxOf(strokes.flatMap((stroke)` — const, line 391
- `const known = kinds.get(owner.ownerId)` — const, line 396
- `const strokes: InkStroke[] = owner.strokes.map((stroke)` — const, line 398
- `const client = strokes.flatMap((stroke)` — const, line 399
- `const box = boxOf(client)` — const, line 400
- `const base: Mark =` — const, line 401
- `const at = notePlace(body, box)` — const, line 403
- `const reading = owner.transcription` — const, line 404
- `const recognition = recognize(client, pageOf(body))` — const, line 407
- `const y = recognition.lineY ?? (box.y0 + box.y1) / 2` — const, line 411
- `const range = rangeBetween(body,` — const, line 412
- `const asPointer = (event: PointerEvent): PointerLike` — const, line 428
- `const erased = new Set<string>()` — const, line 429
- `const onDown = (event: PointerEvent)` — const, line 430
- `const target = event.target as Element | null` — const, line 433
- `const outcome = input.down(asPointer(event), hostRef.current.on)` — const, line 435
- `const onMove = (event: PointerEvent)` — const, line 446
- `const samples = input.move(asPointer(event))` — const, line 452
- `const onUp = (event: PointerEvent)` — const, line 460
- `const stroke = input.up(asPointer(event))` — const, line 461
- `const onCancel = ()` — const, line 466
- `const erase = (samples: Sample[])` — const, line 470
- `const at = toLocal(body, sample.x, sample.y)` — const, line 472
- `const hit = mark.strokes.filter((stroke)` — const, line 475
- `const lassoShown = marks.some((mark)` — const, line 504
- `const layer: ReactNode = ( <> <div className="desk-pen-marks" aria-hidden="true" style=` — const, line 518
- `function Chip(` — function, line 559
- `const ref = useRef<HTMLDivElement | null>(null)` — const, line 560
- `const width = ref.current?.offsetWidth ?? 0` — const, line 563
- `const left = Math.max(body.scrollLeft, Math.min(x, body.clientWidth + body.scrollLeft - width))` — const, line 564
- `const top = left < x ? Math.max(y, below) : y` — const, line 566
- `function NoteBox(` — function, line 572
- `const note = mark.note!` — const, line 573
- `const label = note.readingLabel ?? (note.reading === "reading" ? "reading your handwriting…" : mark.state === "saving" ? "keeping your note…" : "handwritten")` — const, line 576

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/desks/windows/SourceWindow|src/screens/desks/windows/SourceWindow.tsx]] — import-or-re-export: `PenLayer`; references `PenLayer`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `InkTranscribeJobDto`, `ReaderRawSelectionNode`
- [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]] — import-or-re-export; imports `PenSurface`
- [[Reference/Desktop/TypeScript/screens/desks/lifecycle|src/screens/desks/lifecycle.tsx]] — import-or-re-export; imports `useWindowLifecycle`, `useWindowPaused`
- [[Reference/Desktop/TypeScript/screens/desks/pen/geometry|src/screens/desks/pen/geometry.ts]] — import-or-re-export; imports `LocalRect`, `distanceToPolyline`, `localRects`, `pageOf`, `passageBeside`, `passagesSpanned`, `rangeBetween`, `toClient`, `toLocal`, `wordsInLoop`
- [[Reference/Desktop/TypeScript/screens/desks/pen/host|src/screens/desks/pen/host.ts]] — import-or-re-export; imports `PenHost`, `usePenHost`
- [[Reference/Desktop/TypeScript/screens/desks/pen/input|src/screens/desks/pen/input.ts]] — import-or-re-export; imports `PenInput`, `PointerLike`, `Sample`
- [[Reference/Desktop/TypeScript/screens/desks/pen/recognizer|src/screens/desks/pen/recognizer.ts]] — import-or-re-export; imports `Box`, `Point`, `RECOGNIZED_AS`, `StrokeKind`, `boxOf`, `recognize`

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

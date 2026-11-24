---
title: "Desktop module · src/screens/reader/YouTubeWatchPanel.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.reader.YouTubeWatchPanel"
language: "TypeScript"
area: "TypeScript/screens/reader"
source_path: "apps/learnloop-tauri/src/screens/reader/YouTubeWatchPanel.tsx"
source_paths:
  - "apps/learnloop-tauri/src/screens/reader/YouTubeWatchPanel.tsx"
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

# `src/screens/reader/YouTubeWatchPanel.tsx`

Area: [[Reference/Desktop/TypeScript/screens/reader/_area|TypeScript/screens/reader]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Implements the `YouTubeWatchPanel` routed desktop screen and coordinates its learner-facing workflow state.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/reader/YouTubeWatchPanel.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/YouTubeWatchPanel.tsx) |
| Source lines | 661 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/reader/_area|TypeScript/screens/reader]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/source/types|src/screens/desks/source/types.ts]] → [[Reference/Desktop/TypeScript/screens/reader/YouTubeWatchPanel|src/screens/reader/YouTubeWatchPanel.tsx]]

## Public API

- `export interface WatchLens` — interface, line 111
- `export interface VideoExtras` — interface, line 122
- `export interface WatchPanelHandle` — interface, line 129
- `export const YouTubeWatchPanel = forwardRef<WatchPanelHandle,` — const, line 136

## Internal implementation anchors

- `const CUE_LOOKAHEAD_S = 0.15` — const, line 15
- `const SEEK_LANDING_EARLY_S = CUE_LOOKAHEAD_S` — const, line 22
- `const SEEK_LANDING_LATE_S = 2.5` — const, line 23
- `const SEEK_LANDING_WAIT_MS = 10_000` — const, line 24
- `const YT_ORIGIN = "https://www.youtube-nocookie.com"` — const, line 33
- `function parseTimeLocator(value?: string | null): [number, number] | null` — function, line 35
- `const match = /^t=(\d+(?:\.\d+)?)-(\d+(?:\.\d+)?)$/.exec(value.trim())` — const, line 37
- `function formatClock(seconds: number): string` — function, line 41
- `const total = Math.max(0, Math.floor(seconds))` — const, line 42
- `const h = Math.floor(total / 3600)` — const, line 43
- `const m = Math.floor((total % 3600) / 60)` — const, line 44
- `const sec = total % 60` — const, line 45
- `interface TranscriptCue` — interface, line 49
- `function cueAt(cues: TranscriptCue[], time: number): TranscriptCue | null` — function, line 59
- `let active: TranscriptCue | null = null` — let, line 60
- `interface TranscriptSection` — interface, line 68
- `function groupTranscriptCues(cues: TranscriptCue[]): TranscriptSection[]` — function, line 78
- `const sections: TranscriptSection[] = []` — const, line 79
- `const textLength = cue.block.markdown.trim().length` — const, line 81
- `const current = sections[sections.length - 1]` — const, line 82
- `const previous = current.cues[current.cues.length - 1]` — const, line 88
- `const gap = cue.start - previous.end` — const, line 89
- `const projectedDuration = Math.max(current.end, cue.end) - current.start` — const, line 90
- `const previousEndsSentence = /[.!?]["')\]]?$/.test(previous.block.markdown.trim())` — const, line 91
- `const shouldStartSection = gap >= 3 || projectedDuration > 18 || current.characters + textLength + 1 > 260 || (previous.end - current.start >= 10 && previousEndsSentence)` — const, line 92
- `const iframeRef = useRef<HTMLIFrameElement | null>(null)` — const, line 181
- `const transcriptRef = useRef<HTMLDivElement | null>(null)` — const, line 182
- `const resumeSpanRef = useRef(resumeSpan)` — const, line 186
- `const playingRef = useRef<boolean | null>(null)` — const, line 190
- `const seekUntilRef = useRef(0)` — const, line 191
- `const seekRef = useRef<` — const, line 196
- `const placementRef = useRef<string | null | undefined>(undefined)` — const, line 199
- `const cuesRef = useRef<TranscriptCue[]>([])` — const, line 200
- `const noteSeek = useCallback((spanId: string | null, target: number)` — const, line 201
- `const now = Date.now()` — const, line 202
- `const acceptPlayerTime = useCallback((time: number): boolean` — const, line 210
- `const seek = seekRef.current` — const, line 211
- `const now = Date.now()` — const, line 213
- `const landed = time >= seek.target - SEEK_LANDING_EARLY_S && time <= seek.target + SEEK_LANDING_LATE_S` — const, line 215
- `const findInputRef = useRef<HTMLInputElement | null>(null)` — const, line 233
- `const transcriptCues = useMemo<TranscriptCue[]>(()` — const, line 235
- `const cues: TranscriptCue[] = []` — const, line 236
- `const range = parseTimeLocator(block.extractorBlockId)` — const, line 238
- `const transcriptSections = useMemo(()` — const, line 246
- `const duration = transcriptCues.length ? transcriptCues[transcriptCues.length - 1].end : 0` — const, line 248
- `const timeOf = useCallback((spanIds: string[])` — const, line 249
- `const wanted = new Set(spanIds)` — const, line 250
- `const cues = transcriptCues.filter((cue)` — const, line 251
- `const firstFolded = fold ? transcriptCues.find((cue)` — const, line 254
- `const activeCue = useMemo(()` — const, line 256
- `const onClockRef = useRef(video?.onClock)` — const, line 261
- `const checkHeld = useCheckHeld()` — const, line 268
- `const checkHeldRef = useRef(checkHeld)` — const, line 269
- `const post = useCallback((func: string, args: unknown[] = [])` — const, line 271
- `const handshake = useCallback(()` — const, line 278
- `const resumeCue = transcriptCues.find((cue)` — const, line 280
- `const hub = useListenerHub()` — const, line 289
- `const onMessage = (event: MessageEvent)` — const, line 291
- `const frame = iframeRef.current?.contentWindow ?? null` — const, line 295
- `let data:` — let, line 297
- `const paused = useWindowPaused() || checkHeld` — const, line 324
- `const spanId = activeCue?.block.spanId ?? null` — const, line 335
- `const seek = seekRef.current` — const, line 336
- `const placement = placementRef.current` — const, line 341
- `const placing = placement !== undefined && placement === spanId` — const, line 343
- `const scroller = transcriptRef.current` — const, line 347
- `const cue = scroller?.querySelector(`[data-transcript-span="$` — const, line 348
- `const scrollerRect = scroller.getBoundingClientRect()` — const, line 355
- `const cueRect = cue.getBoundingClientRect()` — const, line 356
- `const top = scroller.scrollTop + cueRect.top - scrollerRect.top - (scroller.clientHeight - cueRect.height) / 2` — const, line 357
- `const pauseAndAsk = useCallback(()` — const, line 363
- `let best: string | null = null` — let, line 365
- `const range = parseTimeLocator(block.extractorBlockId)` — const, line 367
- `const seekToCue = useCallback((cue: TranscriptCue)` — const, line 375
- `const selection = window.getSelection()` — const, line 376
- `const findNeedle = findQuery.trim().toLowerCase()` — const, line 386
- `const findMatches = useMemo(()` — const, line 387
- `const scrollToFindMatch = useCallback((index: number)` — const, line 398
- `const cue = findMatches[index]` — const, line 399
- `const scroller = transcriptRef.current` — const, line 400
- `const el = scroller.querySelector(`[data-transcript-span="$` — const, line 405
- `const scrollerRect = scroller.getBoundingClientRect()` — const, line 407
- `const rect = el.getBoundingClientRect()` — const, line 408
- `const top = scroller.scrollTop + rect.top - scrollerRect.top - (scroller.clientHeight - rect.height) / 2` — const, line 409
- `const gotoFindMatch = useCallback((delta: number)` — const, line 413
- `const openFind = useCallback(()` — const, line 422
- `const closeFind = useCallback(()` — const, line 427
- `const handler = (event: KeyboardEvent)` — const, line 434
- `const cue = transcriptCues.find((c)` — const, line 450
- `const player = ( <iframe ref=` — const, line 461
- `const activeSpanId = activeCue?.block.spanId` — const, line 574
- `const active = section.cues.some((cue)` — const, line 575
- `const annotated = section.cues.some((cue)` — const, line 576
- `const guided = section.cues.some((cue)` — const, line 577
- `const sectionKey = section.cues[0].block.spanId ?? `t-$` — const, line 578
- `const groupSpans = section.cues.map((cue)` — const, line 579
- `const spanId = cue.block.spanId ?? ""` — const, line 596
- `const cueActive = activeSpanId === spanId` — const, line 612
- `const cueAnnotated = annotatedSpans.has(spanId)` — const, line 613
- `const cueGuided = guidanceSpans.has(spanId)` — const, line 614
- `const cueFindHit = findOpen && findNeedle.length >= 2 && (cue.block.markdown ?? "").toLowerCase().includes(findNeedle)` — const, line 615
- `const cueCurrentFind = cueFindHit && findMatches[matchIdx]?.block.spanId === spanId` — const, line 617
- `const sel = window.getSelection()` — const, line 629
- `const quote = sel && !sel.isCollapsed ? sel.toString().replace(/\s+/g, " ").trim() : ""` — const, line 630

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/desks/goal/marks|src/screens/desks/goal/marks.tsx]] — import-or-re-export: `WatchLens`; references `WatchLens`
- [[Reference/Desktop/TypeScript/screens/desks/source/ScopedSource|src/screens/desks/source/ScopedSource.tsx]] — import-or-re-export: `WatchPanelHandle`, `YouTubeWatchPanel`; references `WatchPanelHandle`, `YouTubeWatchPanel`
- [[Reference/Desktop/TypeScript/screens/desks/source/types|src/screens/desks/source/types.ts]] — import-or-re-export: `VideoExtras`, `WatchLens`; references `VideoExtras`, `WatchLens`
- [[Reference/Desktop/TypeScript/screens/desks/video/VideoWindow|src/screens/desks/video/VideoWindow.tsx]] — import-or-re-export: `VideoExtras`; references `VideoExtras`
- [[Reference/Desktop/TypeScript/screens/desks/windows/SourceWindow|src/screens/desks/windows/SourceWindow.tsx]] — import-or-re-export: `VideoExtras`; references `VideoExtras`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `ReaderRenderBlockDto`, `ReaderWatchPlanDto`
- [[Reference/Desktop/TypeScript/app/keymap|src/app/keymap.ts]] — import-or-re-export; imports `screenLeavesKey`
- [[Reference/Desktop/TypeScript/components/PdfReaderPane|src/components/PdfReaderPane.tsx]] — import-or-re-export; imports `TagMenuRequest`
- [[Reference/Desktop/TypeScript/components/goldenpath/shared|src/components/goldenpath/shared.tsx]] — import-or-re-export; imports `SecondaryButton`
- [[Reference/Desktop/TypeScript/components/term|src/components/term.tsx]] — import-or-re-export; imports `COLOR`, `Card`, `FONT_MONO`, `Faint`, `Meta`, `Pill`
- [[Reference/Desktop/TypeScript/screens/desks/checks/holdContext|src/screens/desks/checks/holdContext.ts]] — import-or-re-export; imports `useCheckHeld`
- [[Reference/Desktop/TypeScript/screens/desks/lifecycle|src/screens/desks/lifecycle.tsx]] — import-or-re-export; imports `useListenerHub`, `useWindowPaused`
- [[Reference/Desktop/TypeScript/screens/reader/useReadingProgress|src/screens/reader/useReadingProgress.ts]] — import-or-re-export; imports `SEEN_SETTLE_MS`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Reader to Practice Workflow|Reader to Practice Workflow]] — owns the end-to-end reader sequence.
- [[Concepts/Reader Tutor and Teach-Back#Reader|Reader model]] — owns reader semantics.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/reader/YouTubeWatchPanel.instance.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/YouTubeWatchPanel.instance.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/desks/video/video.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/desks/video/video.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/desks/goal/watch.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/desks/goal/watch.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [tests/test_rw5c_block_policy.py](../../../../../../../tests/test_rw5c_block_policy.py) — cross-boundary name contract: references uniquely owned exported name `YouTubeWatchPanel`; it does **not** directly execute this source module.
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

1. Modify [apps/learnloop-tauri/src/screens/reader/YouTubeWatchPanel.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/YouTubeWatchPanel.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

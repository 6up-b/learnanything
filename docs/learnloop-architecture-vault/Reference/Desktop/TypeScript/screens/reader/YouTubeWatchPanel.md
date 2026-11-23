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
| Source lines | 577 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/reader/_area|TypeScript/screens/reader]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]] → [[Reference/Desktop/TypeScript/screens/reader/YouTubeWatchPanel|src/screens/reader/YouTubeWatchPanel.tsx]]

## Public API

- `export interface WatchPanelHandle` — interface, line 108
- `export const YouTubeWatchPanel = forwardRef<WatchPanelHandle,` — const, line 115

## Internal implementation anchors

- `const CUE_LOOKAHEAD_S = 0.15` — const, line 14
- `const SEEK_LANDING_EARLY_S = CUE_LOOKAHEAD_S` — const, line 21
- `const SEEK_LANDING_LATE_S = 2.5` — const, line 22
- `const SEEK_LANDING_WAIT_MS = 10_000` — const, line 23
- `const YT_ORIGIN = "https://www.youtube-nocookie.com"` — const, line 32
- `function parseTimeLocator(value?: string | null): [number, number] | null` — function, line 34
- `const match = /^t=(\d+(?:\.\d+)?)-(\d+(?:\.\d+)?)$/.exec(value.trim())` — const, line 36
- `function formatClock(seconds: number): string` — function, line 40
- `const total = Math.max(0, Math.floor(seconds))` — const, line 41
- `const h = Math.floor(total / 3600)` — const, line 42
- `const m = Math.floor((total % 3600) / 60)` — const, line 43
- `const sec = total % 60` — const, line 44
- `interface TranscriptCue` — interface, line 48
- `function cueAt(cues: TranscriptCue[], time: number): TranscriptCue | null` — function, line 58
- `let active: TranscriptCue | null = null` — let, line 59
- `interface TranscriptSection` — interface, line 67
- `function groupTranscriptCues(cues: TranscriptCue[]): TranscriptSection[]` — function, line 77
- `const sections: TranscriptSection[] = []` — const, line 78
- `const textLength = cue.block.markdown.trim().length` — const, line 80
- `const current = sections[sections.length - 1]` — const, line 81
- `const previous = current.cues[current.cues.length - 1]` — const, line 87
- `const gap = cue.start - previous.end` — const, line 88
- `const projectedDuration = Math.max(current.end, cue.end) - current.start` — const, line 89
- `const previousEndsSentence = /[.!?]["')\]]?$/.test(previous.block.markdown.trim())` — const, line 90
- `const shouldStartSection = gap >= 3 || projectedDuration > 18 || current.characters + textLength + 1 > 260 || (previous.end - current.start >= 10 && previousEndsSentence)` — const, line 91
- `const iframeRef = useRef<HTMLIFrameElement | null>(null)` — const, line 154
- `const transcriptRef = useRef<HTMLDivElement | null>(null)` — const, line 155
- `const resumeSpanRef = useRef(resumeSpan)` — const, line 159
- `const playingRef = useRef<boolean | null>(null)` — const, line 163
- `const seekUntilRef = useRef(0)` — const, line 164
- `const seekRef = useRef<` — const, line 169
- `const placementRef = useRef<string | null | undefined>(undefined)` — const, line 172
- `const cuesRef = useRef<TranscriptCue[]>([])` — const, line 173
- `const noteSeek = useCallback((spanId: string | null, target: number)` — const, line 174
- `const now = Date.now()` — const, line 175
- `const acceptPlayerTime = useCallback((time: number): boolean` — const, line 183
- `const seek = seekRef.current` — const, line 184
- `const now = Date.now()` — const, line 186
- `const landed = time >= seek.target - SEEK_LANDING_EARLY_S && time <= seek.target + SEEK_LANDING_LATE_S` — const, line 188
- `const findInputRef = useRef<HTMLInputElement | null>(null)` — const, line 206
- `const transcriptCues = useMemo<TranscriptCue[]>(()` — const, line 208
- `const cues: TranscriptCue[] = []` — const, line 209
- `const range = parseTimeLocator(block.extractorBlockId)` — const, line 211
- `const transcriptSections = useMemo(()` — const, line 219
- `const firstFolded = fold ? transcriptCues.find((cue)` — const, line 220
- `const activeCue = useMemo(()` — const, line 222
- `const post = useCallback((func: string, args: unknown[] = [])` — const, line 224
- `const handshake = useCallback(()` — const, line 230
- `const resumeCue = transcriptCues.find((cue)` — const, line 232
- `const hub = useListenerHub()` — const, line 241
- `const onMessage = (event: MessageEvent)` — const, line 243
- `const frame = iframeRef.current?.contentWindow ?? null` — const, line 247
- `let data:` — let, line 249
- `const paused = useWindowPaused()` — const, line 272
- `const spanId = activeCue?.block.spanId ?? null` — const, line 283
- `const seek = seekRef.current` — const, line 284
- `const placement = placementRef.current` — const, line 289
- `const placing = placement !== undefined && placement === spanId` — const, line 291
- `const scroller = transcriptRef.current` — const, line 295
- `const cue = scroller?.querySelector(`[data-transcript-span="$` — const, line 296
- `const scrollerRect = scroller.getBoundingClientRect()` — const, line 303
- `const cueRect = cue.getBoundingClientRect()` — const, line 304
- `const top = scroller.scrollTop + cueRect.top - scrollerRect.top - (scroller.clientHeight - cueRect.height) / 2` — const, line 305
- `const pauseAndAsk = useCallback(()` — const, line 311
- `let best: string | null = null` — let, line 313
- `const range = parseTimeLocator(block.extractorBlockId)` — const, line 315
- `const seekToCue = useCallback((cue: TranscriptCue)` — const, line 323
- `const selection = window.getSelection()` — const, line 324
- `const findNeedle = findQuery.trim().toLowerCase()` — const, line 334
- `const findMatches = useMemo(()` — const, line 335
- `const scrollToFindMatch = useCallback((index: number)` — const, line 346
- `const cue = findMatches[index]` — const, line 347
- `const scroller = transcriptRef.current` — const, line 348
- `const el = scroller.querySelector(`[data-transcript-span="$` — const, line 353
- `const scrollerRect = scroller.getBoundingClientRect()` — const, line 355
- `const rect = el.getBoundingClientRect()` — const, line 356
- `const top = scroller.scrollTop + rect.top - scrollerRect.top - (scroller.clientHeight - rect.height) / 2` — const, line 357
- `const gotoFindMatch = useCallback((delta: number)` — const, line 361
- `const openFind = useCallback(()` — const, line 370
- `const closeFind = useCallback(()` — const, line 375
- `const handler = (event: KeyboardEvent)` — const, line 382
- `const cue = transcriptCues.find((c)` — const, line 398
- `const activeSpanId = activeCue?.block.spanId` — const, line 496
- `const active = section.cues.some((cue)` — const, line 497
- `const annotated = section.cues.some((cue)` — const, line 498
- `const guided = section.cues.some((cue)` — const, line 499
- `const sectionKey = section.cues[0].block.spanId ?? `t-$` — const, line 500
- `const spanId = cue.block.spanId ?? ""` — const, line 515
- `const cueActive = activeSpanId === spanId` — const, line 531
- `const cueAnnotated = annotatedSpans.has(spanId)` — const, line 532
- `const cueGuided = guidanceSpans.has(spanId)` — const, line 533
- `const cueFindHit = findOpen && findNeedle.length >= 2 && (cue.block.markdown ?? "").toLowerCase().includes(findNeedle)` — const, line 534
- `const cueCurrentFind = cueFindHit && findMatches[matchIdx]?.block.spanId === spanId` — const, line 536
- `const sel = window.getSelection()` — const, line 545
- `const quote = sel && !sel.isCollapsed ? sel.toString().replace(/\s+/g, " ").trim() : ""` — const, line 546

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]] — import-or-re-export: `WatchPanelHandle`, `YouTubeWatchPanel`; references `WatchPanelHandle`, `YouTubeWatchPanel`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `ReaderRenderBlockDto`, `ReaderWatchPlanDto`
- [[Reference/Desktop/TypeScript/app/keymap|src/app/keymap.ts]] — import-or-re-export; imports `screenLeavesKey`
- [[Reference/Desktop/TypeScript/components/PdfReaderPane|src/components/PdfReaderPane.tsx]] — import-or-re-export; imports `TagMenuRequest`
- [[Reference/Desktop/TypeScript/components/goldenpath/shared|src/components/goldenpath/shared.tsx]] — import-or-re-export; imports `SecondaryButton`
- [[Reference/Desktop/TypeScript/components/term|src/components/term.tsx]] — import-or-re-export; imports `COLOR`, `Card`, `FONT_MONO`, `Faint`, `Meta`, `Pill`
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

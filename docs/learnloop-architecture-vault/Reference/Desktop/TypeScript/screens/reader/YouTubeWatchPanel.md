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
| Source lines | 563 |
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
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]] → [[Reference/Desktop/TypeScript/screens/reader/YouTubeWatchPanel|src/screens/reader/YouTubeWatchPanel.tsx]]

## Public API

- `export interface WatchPanelHandle` — interface, line 107
- `export const YouTubeWatchPanel = forwardRef<WatchPanelHandle,` — const, line 112

## Internal implementation anchors

- `const CUE_LOOKAHEAD_S = 0.15` — const, line 13
- `const SEEK_LANDING_EARLY_S = CUE_LOOKAHEAD_S` — const, line 20
- `const SEEK_LANDING_LATE_S = 2.5` — const, line 21
- `const SEEK_LANDING_WAIT_MS = 10_000` — const, line 22
- `const YT_ORIGIN = "https://www.youtube-nocookie.com"` — const, line 31
- `function parseTimeLocator(value?: string | null): [number, number] | null` — function, line 33
- `const match = /^t=(\d+(?:\.\d+)?)-(\d+(?:\.\d+)?)$/.exec(value.trim())` — const, line 35
- `function formatClock(seconds: number): string` — function, line 39
- `const total = Math.max(0, Math.floor(seconds))` — const, line 40
- `const h = Math.floor(total / 3600)` — const, line 41
- `const m = Math.floor((total % 3600) / 60)` — const, line 42
- `const sec = total % 60` — const, line 43
- `interface TranscriptCue` — interface, line 47
- `function cueAt(cues: TranscriptCue[], time: number): TranscriptCue | null` — function, line 57
- `let active: TranscriptCue | null = null` — let, line 58
- `interface TranscriptSection` — interface, line 66
- `function groupTranscriptCues(cues: TranscriptCue[]): TranscriptSection[]` — function, line 76
- `const sections: TranscriptSection[] = []` — const, line 77
- `const textLength = cue.block.markdown.trim().length` — const, line 79
- `const current = sections[sections.length - 1]` — const, line 80
- `const previous = current.cues[current.cues.length - 1]` — const, line 86
- `const gap = cue.start - previous.end` — const, line 87
- `const projectedDuration = Math.max(current.end, cue.end) - current.start` — const, line 88
- `const previousEndsSentence = /[.!?]["')\]]?$/.test(previous.block.markdown.trim())` — const, line 89
- `const shouldStartSection = gap >= 3 || projectedDuration > 18 || current.characters + textLength + 1 > 260 || (previous.end - current.start >= 10 && previousEndsSentence)` — const, line 90
- `const iframeRef = useRef<HTMLIFrameElement | null>(null)` — const, line 151
- `const transcriptRef = useRef<HTMLDivElement | null>(null)` — const, line 152
- `const resumeSpanRef = useRef(resumeSpan)` — const, line 156
- `const playingRef = useRef<boolean | null>(null)` — const, line 160
- `const seekUntilRef = useRef(0)` — const, line 161
- `const seekRef = useRef<` — const, line 166
- `const placementRef = useRef<string | null | undefined>(undefined)` — const, line 169
- `const cuesRef = useRef<TranscriptCue[]>([])` — const, line 170
- `const noteSeek = useCallback((spanId: string | null, target: number)` — const, line 171
- `const now = Date.now()` — const, line 172
- `const acceptPlayerTime = useCallback((time: number): boolean` — const, line 180
- `const seek = seekRef.current` — const, line 181
- `const now = Date.now()` — const, line 183
- `const landed = time >= seek.target - SEEK_LANDING_EARLY_S && time <= seek.target + SEEK_LANDING_LATE_S` — const, line 185
- `const findInputRef = useRef<HTMLInputElement | null>(null)` — const, line 203
- `const transcriptCues = useMemo<TranscriptCue[]>(()` — const, line 205
- `const cues: TranscriptCue[] = []` — const, line 206
- `const range = parseTimeLocator(block.extractorBlockId)` — const, line 208
- `const transcriptSections = useMemo(()` — const, line 216
- `const firstFolded = fold ? transcriptCues.find((cue)` — const, line 217
- `const activeCue = useMemo(()` — const, line 219
- `const post = useCallback((func: string, args: unknown[] = [])` — const, line 221
- `const handshake = useCallback(()` — const, line 227
- `const resumeCue = transcriptCues.find((cue)` — const, line 229
- `const onMessage = (event: MessageEvent)` — const, line 239
- `let data:` — let, line 241
- `const spanId = activeCue?.block.spanId ?? null` — const, line 269
- `const seek = seekRef.current` — const, line 270
- `const placement = placementRef.current` — const, line 275
- `const placing = placement !== undefined && placement === spanId` — const, line 277
- `const scroller = transcriptRef.current` — const, line 281
- `const cue = scroller?.querySelector(`[data-transcript-span="$` — const, line 282
- `const scrollerRect = scroller.getBoundingClientRect()` — const, line 289
- `const cueRect = cue.getBoundingClientRect()` — const, line 290
- `const top = scroller.scrollTop + cueRect.top - scrollerRect.top - (scroller.clientHeight - cueRect.height) / 2` — const, line 291
- `const pauseAndAsk = useCallback(()` — const, line 297
- `let best: string | null = null` — let, line 299
- `const range = parseTimeLocator(block.extractorBlockId)` — const, line 301
- `const seekToCue = useCallback((cue: TranscriptCue)` — const, line 309
- `const selection = window.getSelection()` — const, line 310
- `const findNeedle = findQuery.trim().toLowerCase()` — const, line 320
- `const findMatches = useMemo(()` — const, line 321
- `const scrollToFindMatch = useCallback((index: number)` — const, line 332
- `const cue = findMatches[index]` — const, line 333
- `const scroller = transcriptRef.current` — const, line 334
- `const el = scroller.querySelector(`[data-transcript-span="$` — const, line 339
- `const scrollerRect = scroller.getBoundingClientRect()` — const, line 341
- `const rect = el.getBoundingClientRect()` — const, line 342
- `const top = scroller.scrollTop + rect.top - scrollerRect.top - (scroller.clientHeight - rect.height) / 2` — const, line 343
- `const gotoFindMatch = useCallback((delta: number)` — const, line 347
- `const openFind = useCallback(()` — const, line 356
- `const closeFind = useCallback(()` — const, line 361
- `const handler = (event: KeyboardEvent)` — const, line 368
- `const cue = transcriptCues.find((c)` — const, line 385
- `const activeSpanId = activeCue?.block.spanId` — const, line 482
- `const active = section.cues.some((cue)` — const, line 483
- `const annotated = section.cues.some((cue)` — const, line 484
- `const guided = section.cues.some((cue)` — const, line 485
- `const sectionKey = section.cues[0].block.spanId ?? `t-$` — const, line 486
- `const spanId = cue.block.spanId ?? ""` — const, line 501
- `const cueActive = activeSpanId === spanId` — const, line 517
- `const cueAnnotated = annotatedSpans.has(spanId)` — const, line 518
- `const cueGuided = guidanceSpans.has(spanId)` — const, line 519
- `const cueFindHit = findOpen && findNeedle.length >= 2 && (cue.block.markdown ?? "").toLowerCase().includes(findNeedle)` — const, line 520
- `const cueCurrentFind = cueFindHit && findMatches[matchIdx]?.block.spanId === spanId` — const, line 522
- `const sel = window.getSelection()` — const, line 531
- `const quote = sel && !sel.isCollapsed ? sel.toString().replace(/\s+/g, " ").trim() : ""` — const, line 532

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
- [[Reference/Desktop/TypeScript/screens/reader/useReadingProgress|src/screens/reader/useReadingProgress.ts]] — import-or-re-export; imports `SEEN_SETTLE_MS`

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

1. Modify [apps/learnloop-tauri/src/screens/reader/YouTubeWatchPanel.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/YouTubeWatchPanel.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

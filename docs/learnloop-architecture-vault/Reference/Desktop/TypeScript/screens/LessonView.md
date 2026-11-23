---
title: "Desktop module · src/screens/LessonView.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.LessonView"
language: "TypeScript"
area: "TypeScript/screens"
source_path: "apps/learnloop-tauri/src/screens/LessonView.tsx"
source_paths:
  - "apps/learnloop-tauri/src/screens/LessonView.tsx"
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

# `src/screens/LessonView.tsx`

Area: [[Reference/Desktop/TypeScript/screens/_area|TypeScript/screens]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Implements the `LessonView` routed desktop screen and coordinates its learner-facing workflow state.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/LessonView.tsx](../../../../../../apps/learnloop-tauri/src/screens/LessonView.tsx) |
| Source lines | 802 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/_area|TypeScript/screens]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/LessonScreen|src/screens/LessonScreen.tsx]] → [[Reference/Desktop/TypeScript/screens/LessonView|src/screens/LessonView.tsx]]

## Public API

- `export type LessonEntry = |` — type, line 64
- `export const PROBE_POLL_MS = DIAGNOSIS_POLL_MS` — const, line 78
- `export type LessonFrame = "screen" | "window"` — type, line 98
- `export interface LessonViewProps` — interface, line 100
- `export function LessonView(` — function, line 125
- `export const LESSON_FIGURE_COPY: Readonly<Record<Exclude<LessonFigureStatus, "shown">, string>> = Object.freeze(` — const, line 672
- `export const LESSON_FIGURE_CONTRACT: FiguresContract = Object.freeze(` — const, line 679

## Internal implementation anchors

- `const TAP_LABELS = ["1", "2", "3", "4", "5"]` — const, line 80
- `const CLOSE_WORDS: Record<string, string> =` — const, line 81
- `function dueWords(due: string): string` — function, line 90
- `const day = new Date(`$` — const, line 91
- `const days = Math.max(0, Math.round((day.getTime() - Date.now()) / 86_400_000))` — const, line 93
- `const windowed = frame === "window"` — const, line 137
- `const paused = useWindowPaused()` — const, line 139
- `const pausedRef = useRef(paused)` — const, line 140
- `const whenLive = useWhenLive()` — const, line 142
- `const hub = useListenerHub()` — const, line 143
- `const onViewRef = useRef(onView)` — const, line 145
- `const setView = useCallback((next: LessonViewDto)` — const, line 147
- `const onBusyRef = useRef(onBusy)` — const, line 152
- `const lastFailure = useRef<"error" | "unavailable" | null>(null)` — const, line 166
- `const activity = useRef<LessonActivityTracker | null>(null)` — const, line 175
- `const run = useCallback(async (input: LessonTurnInput)` — const, line 184
- `const next = await api.lessonTurn(input)` — const, line 193
- `const err = getCommandError(error)` — const, line 197
- `const code = err?.code ?? ""` — const, line 198
- `const message = err?.message ?? String(error)` — const, line 199
- `const existing = ((err?.details ??` — const, line 200
- `const details = (err?.details ??` — const, line 213
- `const saved = details.lesson_id ?? details.lessonId` — const, line 214
- `const lessonId = typeof saved === "string" && saved ? saved : input.action === "open" ? undefined : input.lessonId` — const, line 218
- `const sendShown = useCallback(async (input: LessonTurnInput, text: string, restore: (text: string)` — const, line 239
- `const next = await run(input)` — const, line 241
- `let cancelled = false` — let, line 247
- `const start = ()` — const, line 248
- `const lessonId = view?.lessonId` — const, line 272
- `const openCheck = view?.openCheck ?? null` — const, line 273
- `const activityLog = Boolean(view?.activityLog)` — const, line 274
- `const inForeground = ()` — const, line 278
- `const tracker = createLessonActivity(` — const, line 279
- `const onInput = ()` — const, line 284
- `const onForeground = ()` — const, line 285
- `const inputs = ["keydown", "pointerdown", "wheel", "scroll"] as const` — const, line 286
- `const removals = [ ...inputs.map((name)` — const, line 289
- `const probe = view?.probe ?? null` — const, line 311
- `const probeOpen = Boolean(probe && probe.status === "open")` — const, line 312
- `const timer = window.setTimeout(()` — const, line 321
- `const findGoal = useCallback(async ()` — const, line 327
- `const text = goalText.trim()` — const, line 328
- `const found = await api.lessonGoal(` — const, line 333
- `const startTyped = useCallback(async ()` — const, line 344
- `const text = goalText.trim()` — const, line 345
- `const accepted = Object.entries(addTopics).filter(([, yes])` — const, line 347
- `const submitProbe = useCallback(async ()` — const, line 352
- `const teachAnyway = useCallback(async ()` — const, line 358
- `const send = useCallback(async ()` — const, line 363
- `const text = reply.trim()` — const, line 365
- `const submitCheck = useCallback(async ()` — const, line 370
- `const submitPrediction = useCallback(async ()` — const, line 376
- `const value = predictionAnswer.trim()` — const, line 378
- `const stop = useCallback(async ()` — const, line 384
- `const startFresh = useCallback(async ()` — const, line 390
- `const learningObjectIds = view?.learningObjectIds ?? []` — const, line 391
- `const feed = useMemo(()` — const, line 396
- `const title = entry.kind === "open" ? entry.title : undefined` — const, line 401
- `const look = windowed ? WINDOW_LOOK : SCREEN_LOOK` — const, line 402
- `const heading = view?.goal ?? title ?? null` — const, line 403
- `function LessonRoot(` — function, line 639
- `type Look = Record<"bar" | "body" | "article" | "plan",` — type, line 649
- `const SCREEN_LOOK: Look =` — const, line 651
- `const WINDOW_LOOK: Look =` — const, line 658
- `function Prose(` — function, line 666
- `function useLessonFigureCtl(figure: FigureViewDto): FiguresCtl` — function, line 682
- `function LessonFigure(` — function, line 707
- `const shown = useMemo(()` — const, line 709
- `const ctl = useLessonFigureCtl(shown)` — const, line 710
- `function FeedEntry(` — function, line 714
- `const open = item.checkRef === openCheckRef` — const, line 733

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/fixtures/desks/harness|src/fixtures/desks/harness.tsx]] — import-or-re-export: `LessonEntry`; references `LessonEntry`
- [[Reference/Desktop/TypeScript/screens/LessonScreen|src/screens/LessonScreen.tsx]] — import-or-re-export: `LESSON_FIGURE_CONTRACT`, `LESSON_FIGURE_COPY`, `LessonEntry`, `LessonView`, `LessonViewProps`, `PROBE_POLL_MS`; references `LessonView`, `LessonViewProps`
- [[Reference/Desktop/TypeScript/screens/desks/DeskShell|src/screens/desks/DeskShell.tsx]] — import-or-re-export: `LessonEntry`; references `LessonEntry`
- [[Reference/Desktop/TypeScript/screens/desks/lesson/LessonPaper|src/screens/desks/lesson/LessonPaper.tsx]] — import-or-re-export: `LessonEntry`, `LessonView`; references `LessonEntry`, `LessonView`
- [[Reference/Desktop/TypeScript/screens/desks/lesson/host|src/screens/desks/lesson/host.ts]] — import-or-re-export: `LessonEntry`; references `LessonEntry`
- [[Reference/Desktop/TypeScript/screens/desks/menu/verbs|src/screens/desks/menu/verbs.ts]] — import-or-re-export: `LessonEntry`; references `LessonEntry`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `FigureViewDto`, `LessonFeedEntryDto`, `LessonFigureStatus`, `LessonGoalDto`, `LessonTurnInput`, `LessonViewDto`
- [[Reference/Desktop/TypeScript/components/DiagnosisCard|src/components/DiagnosisCard.tsx]] — import-or-re-export; imports `DIAGNOSIS_POLL_MS`
- [[Reference/Desktop/TypeScript/components/Waiting|src/components/Waiting.tsx]] — import-or-re-export; imports `Waiting`
- [[Reference/Desktop/TypeScript/components/term|src/components/term.tsx]] — import-or-re-export; imports `COLOR`, `FONT_MONO`, `Faint`
- [[Reference/Desktop/TypeScript/copy/waiting|src/copy/waiting.ts]] — import-or-re-export; imports `WAITING_COPY`
- [[Reference/Desktop/TypeScript/errors|src/errors.ts]] — import-or-re-export; imports `getCommandError`
- [[Reference/Desktop/TypeScript/render/MarkdownMath|src/render/MarkdownMath.tsx]] — import-or-re-export; imports `MarkdownMath`
- [[Reference/Desktop/TypeScript/screens/desks/fitMath|src/screens/desks/fitMath.tsx]] — import-or-re-export; imports `FitMath`
- [[Reference/Desktop/TypeScript/screens/desks/lifecycle|src/screens/desks/lifecycle.tsx]] — import-or-re-export; imports `useListenerHub`, `useWhenLive`, `useWindowPaused`
- [[Reference/Desktop/TypeScript/screens/lessonActivity|src/screens/lessonActivity.ts]] — import-or-re-export; imports `LessonActivityTracker`, `createLessonActivity`
- [[Reference/Desktop/TypeScript/screens/reader/figures/FigureInline|src/screens/reader/figures/FigureInline.tsx]] — import-or-re-export; imports `FigureInline`
- [[Reference/Desktop/TypeScript/screens/reader/figures/useFigures|src/screens/reader/figures/useFigures.ts]] — import-or-re-export; imports `FiguresContract`, `FiguresCtl`, `figurePlacementKey`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/desks/lesson/deskLessons.test.tsx](../../../../../../apps/learnloop-tauri/src/screens/desks/lesson/deskLessons.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/screens/LessonView.tsx](../../../../../../apps/learnloop-tauri/src/screens/LessonView.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

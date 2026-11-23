---
title: "Desktop module · src/screens/LessonScreen.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.LessonScreen"
language: "TypeScript"
area: "TypeScript/screens"
source_path: "apps/learnloop-tauri/src/screens/LessonScreen.tsx"
source_paths:
  - "apps/learnloop-tauri/src/screens/LessonScreen.tsx"
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

# `src/screens/LessonScreen.tsx`

Area: [[Reference/Desktop/TypeScript/screens/_area|TypeScript/screens]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Implements the `LessonScreen` routed desktop screen and coordinates its learner-facing workflow state.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/LessonScreen.tsx](../../../../../../apps/learnloop-tauri/src/screens/LessonScreen.tsx) |
| Source lines | 702 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/_area|TypeScript/screens]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/LessonScreen|src/screens/LessonScreen.tsx]]

## Public API

- `export type LessonEntry = |` — type, line 54
- `export const PROBE_POLL_MS = DIAGNOSIS_POLL_MS` — const, line 68
- `export function LessonScreen(` — function, line 87
- `export const LESSON_FIGURE_COPY: Readonly<Record<Exclude<LessonFigureStatus, "shown">, string>> = Object.freeze(` — const, line 572
- `export const LESSON_FIGURE_CONTRACT: FiguresContract = Object.freeze(` — const, line 579

## Internal implementation anchors

- `const TAP_LABELS = ["1", "2", "3", "4", "5"]` — const, line 70
- `const CLOSE_WORDS: Record<string, string> =` — const, line 71
- `function dueWords(due: string): string` — function, line 80
- `const day = new Date(`$` — const, line 81
- `const days = Math.max(0, Math.round((day.getTime() - Date.now()) / 86_400_000))` — const, line 83
- `const lastFailure = useRef<"error" | "unavailable" | null>(null)` — const, line 119
- `const activity = useRef<LessonActivityTracker | null>(null)` — const, line 128
- `const run = useCallback(async (input: LessonTurnInput)` — const, line 137
- `const next = await api.lessonTurn(input)` — const, line 146
- `const err = getCommandError(error)` — const, line 150
- `const code = err?.code ?? ""` — const, line 151
- `const message = err?.message ?? String(error)` — const, line 152
- `const existing = ((err?.details ??` — const, line 153
- `const details = (err?.details ??` — const, line 166
- `const saved = details.lesson_id ?? details.lessonId` — const, line 167
- `const lessonId = typeof saved === "string" && saved ? saved : input.action === "open" ? undefined : input.lessonId` — const, line 171
- `const sendShown = useCallback(async (input: LessonTurnInput, text: string, restore: (text: string)` — const, line 192
- `const next = await run(input)` — const, line 194
- `let cancelled = false` — let, line 200
- `const lessonId = view?.lessonId` — const, line 219
- `const openCheck = view?.openCheck ?? null` — const, line 220
- `const activityLog = Boolean(view?.activityLog)` — const, line 221
- `const inForeground = ()` — const, line 224
- `const tracker = createLessonActivity(` — const, line 225
- `const onInput = ()` — const, line 230
- `const onForeground = ()` — const, line 231
- `const inputs = ["keydown", "pointerdown", "wheel", "scroll"] as const` — const, line 232
- `const probe = view?.probe ?? null` — const, line 252
- `const probeOpen = Boolean(probe && probe.status === "open")` — const, line 253
- `const timer = window.setTimeout(()` — const, line 261
- `const findGoal = useCallback(async ()` — const, line 267
- `const text = goalText.trim()` — const, line 268
- `const found = await api.lessonGoal(` — const, line 273
- `const startTyped = useCallback(async ()` — const, line 284
- `const text = goalText.trim()` — const, line 285
- `const accepted = Object.entries(addTopics).filter(([, yes])` — const, line 287
- `const submitProbe = useCallback(async ()` — const, line 292
- `const teachAnyway = useCallback(async ()` — const, line 298
- `const send = useCallback(async ()` — const, line 303
- `const text = reply.trim()` — const, line 305
- `const submitCheck = useCallback(async ()` — const, line 310
- `const submitPrediction = useCallback(async ()` — const, line 316
- `const value = predictionAnswer.trim()` — const, line 318
- `const stop = useCallback(async ()` — const, line 324
- `const startFresh = useCallback(async ()` — const, line 330
- `const learningObjectIds = view?.learningObjectIds ?? []` — const, line 331
- `const feed = useMemo(()` — const, line 336
- `const title = entry.kind === "open" ? entry.title : undefined` — const, line 341
- `function useLessonFigureCtl(figure: FigureViewDto): FiguresCtl` — function, line 582
- `function LessonFigure(` — function, line 607
- `const shown = useMemo(()` — const, line 609
- `const ctl = useLessonFigureCtl(shown)` — const, line 610
- `function FeedEntry(` — function, line 614
- `const open = item.checkRef === openCheckRef` — const, line 633

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] — dynamic import: `LessonEntry`; references `LessonEntry`
- [[Reference/Desktop/TypeScript/app/checkHandoff|src/app/checkHandoff.ts]] — import-or-re-export: `LessonEntry`; references `LessonEntry`
- [[Reference/Desktop/TypeScript/screens/FeedbackScreen|src/screens/FeedbackScreen.tsx]] — import-or-re-export: `LessonEntry`; references `LessonEntry`
- [[Reference/Desktop/TypeScript/screens/TodayScreen|src/screens/TodayScreen.tsx]] — import-or-re-export: `LessonEntry`; references `LessonEntry`
- [[Reference/Desktop/TypeScript/screens/desks/DeskShell|src/screens/desks/DeskShell.tsx]] — import-or-re-export: `LessonScreen`; references `LessonScreen`
- [[Reference/Desktop/TypeScript/screens/today/ContinueLessonCard|src/screens/today/ContinueLessonCard.tsx]] — import-or-re-export: `LessonEntry`; references `LessonEntry`
- [[Reference/Desktop/TypeScript/screens/today/DailyPlanView|src/screens/today/DailyPlanView.tsx]] — import-or-re-export: `LessonEntry`; references `LessonEntry`
- [[Reference/Desktop/TypeScript/screens/today/LessonOfferBlock|src/screens/today/LessonOfferBlock.tsx]] — import-or-re-export: `LessonEntry`; references `LessonEntry`
- [[Reference/Desktop/TypeScript/screens/today/LessonOfferPage|src/screens/today/LessonOfferPage.tsx]] — import-or-re-export: `LessonEntry`; references `LessonEntry`
- [[Reference/Desktop/TypeScript/screens/today/LessonSuggestionCard|src/screens/today/LessonSuggestionCard.tsx]] — import-or-re-export: `LessonEntry`; references `LessonEntry`
- [[Reference/Desktop/TypeScript/screens/today/SomethingElse|src/screens/today/SomethingElse.tsx]] — import-or-re-export: `LessonEntry`; references `LessonEntry`
- [[Reference/Desktop/TypeScript/screens/today/TodayPlace|src/screens/today/TodayPlace.tsx]] — import-or-re-export: `LessonEntry`; references `LessonEntry`

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
- [[Reference/Desktop/TypeScript/screens/lessonActivity|src/screens/lessonActivity.ts]] — import-or-re-export; imports `LessonActivityTracker`, `createLessonActivity`
- [[Reference/Desktop/TypeScript/screens/reader/figures/FigureInline|src/screens/reader/figures/FigureInline.tsx]] — import-or-re-export; imports `FigureInline`
- [[Reference/Desktop/TypeScript/screens/reader/figures/useFigures|src/screens/reader/figures/useFigures.ts]] — import-or-re-export; imports `FiguresContract`, `FiguresCtl`, `figurePlacementKey`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/today/LessonSuggestionCard.test.tsx](../../../../../../apps/learnloop-tauri/src/screens/today/LessonSuggestionCard.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/LessonScreen.waiting.test.tsx](../../../../../../apps/learnloop-tauri/src/screens/LessonScreen.waiting.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/LessonScreen.test.tsx](../../../../../../apps/learnloop-tauri/src/screens/LessonScreen.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/LessonScreen.te2.test.tsx](../../../../../../apps/learnloop-tauri/src/screens/LessonScreen.te2.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/LessonScreen.brokenControls2.test.tsx](../../../../../../apps/learnloop-tauri/src/screens/LessonScreen.brokenControls2.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/app/checkHandoff.test.tsx](../../../../../../apps/learnloop-tauri/src/app/checkHandoff.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/screens/LessonScreen.tsx](../../../../../../apps/learnloop-tauri/src/screens/LessonScreen.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

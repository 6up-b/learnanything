---
title: "Desktop module · src/screens/desks/goal/controller.ts"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.desks.goal.controller"
language: "TypeScript"
area: "TypeScript/screens/desks/goal"
source_path: "apps/learnloop-tauri/src/screens/desks/goal/controller.ts"
source_paths:
  - "apps/learnloop-tauri/src/screens/desks/goal/controller.ts"
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

# `src/screens/desks/goal/controller.ts`

Area: [[Reference/Desktop/TypeScript/screens/desks/goal/_area|TypeScript/screens/desks/goal]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides `GoalTransport`, `LIVE_GOAL_TRANSPORT`, `BAND_RECHECK_MS`, `watchStateChanges` and related exports within the desktop's TypeScript/screens/desks/goal ownership area.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/desks/goal/controller.ts](../../../../../../../../apps/learnloop-tauri/src/screens/desks/goal/controller.ts) |
| Source lines | 306 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/desks/goal/_area|TypeScript/screens/desks/goal]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/DeskShell|src/screens/desks/DeskShell.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/goal/controller|src/screens/desks/goal/controller.ts]]

## Public API

- `export interface GoalTransport` — interface, line 23
- `export const LIVE_GOAL_TRANSPORT: GoalTransport =` — const, line 38
- `export const BAND_RECHECK_MS = 6000` — const, line 52
- `export function watchStateChanges(onChange: ()` — function, line 61
- `export function primaryGoalId(goals: GoalsListSnapshot["goals"] | null): string | null` — function, line 76
- `export interface WhyState` — interface, line 98
- `export interface GoalLensState` — interface, line 107
- `export function useGoalLens(` — function, line 129

## Internal implementation anchors

- `const LONGEST_TIMER_MS = 2 ** 31 - 1` — const, line 54
- `const WATCH_KEY = ["goal-lens:state-changes"] as const` — const, line 58
- `const WATCH_TAGS = [TAG.goals, TAG.queue, TAG.sources, TAG.vault, TAG.graph]` — const, line 59
- `let seen = peek(WATCH_KEY).invalidatedAt` — let, line 63
- `const state = peek(WATCH_KEY)` — const, line 65
- `const DIM_KEY = "learnloop.desks.goalDim"` — const, line 73
- `const active = (goals ?? []).filter((goal)` — const, line 77
- `function readDim(): boolean` — function, line 82
- `function writeDim(on: boolean): void` — function, line 90
- `const asked = useRef(new Set<string>())` — const, line 146
- `const tickets = useRef(new Map<string, number>())` — const, line 149
- `const ticket = useRef(0)` — const, line 150
- `const goalRef = useRef<string | null>(null)` — const, line 151
- `const started = useRef(new Set<string>())` — const, line 155
- `const onErrorRef = useRef(onError)` — const, line 157
- `const report = useCallback((message: string)` — const, line 159
- `const judged = useRef(new Set<string>())` — const, line 160
- `let live = true` — let, line 163
- `const goalId = off ? null : deskGoalId ?? (goals ? primaryGoalId(goals) : null)` — const, line 169
- `let live = true` — let, line 192
- `const covering = Boolean(band.coverage?.covering)` — const, line 210
- `const owed = !covering && (band.status === "pending" || band.status === "stale")` — const, line 211
- `const key = `$` — const, line 212
- `let live = true` — let, line 215
- `const handle = timers.set(()` — const, line 220
- `const due = band?.nextCheckDue ? Date.parse(band.nextCheckDue) : NaN` — const, line 226
- `const wait = Math.max(0, due - timers.now())` — const, line 228
- `const handle = timers.set(()` — const, line 229
- `const readingsKey = [...new Set(readings)].sort().join("|")` — const, line 234
- `const shown = new Set(readingsKey ? readingsKey.split("|") : [])` — const, line 237
- `const mine = ++ticket.current` — const, line 243
- `const current = ()` — const, line 245
- `const indexes = useMemo(()` — const, line 253
- `const out: Record<string, LensIndex | null> =` — const, line 254
- `const indexFor = useCallback((extractionId: string)` — const, line 258
- `const whyNow = useMemo(()` — const, line 261
- `const section = indexes[why.extractionId]?.sections.find((each)` — const, line 263
- `const refresh = useCallback(()` — const, line 267
- `const toggleDim = useCallback(()` — const, line 268
- `const setDepth = useCallback((depth: ReadingPathDepth)` — const, line 270
- `const readAnyway = useCallback((extractionId: string, sectionId: string, on: boolean)` — const, line 275
- `const override = useCallback((learningObjectId: string, choice: DeliverablePathChoice, sectionRef?: string)` — const, line 281
- `const mapIt = useCallback(()` — const, line 287
- `const addPhrase = useCallback((phrase: string)` — const, line 293
- `const correctScope = useCallback((text: string)` — const, line 299

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/desks/DeskShell|src/screens/desks/DeskShell.tsx]] — import-or-re-export: `GoalTransport`, `LIVE_GOAL_TRANSPORT`; references `GoalTransport`, `LIVE_GOAL_TRANSPORT`
- [[Reference/Desktop/TypeScript/screens/desks/goal/GoalLayer|src/screens/desks/goal/GoalLayer.tsx]] — import-or-re-export: `GoalTransport`, `WhyState`, `useGoalLens`; references `GoalTransport`, `WhyState`, `useGoalLens`
- [[Reference/Desktop/TypeScript/screens/desks/goal/marks|src/screens/desks/goal/marks.tsx]] — import-or-re-export: `WhyState`; references `WhyState`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `DeliverablePathChoice`, `GoalBandDto`, `GoalLensDto`, `GoalLensInput`, `GoalLensSectionDto`, `GoalSectionChoiceDto`, `GoalSectionChoiceInput`, `GoalsListSnapshot`, `ReadingPathDepth`
- [[Reference/Desktop/TypeScript/api/queryCache|src/api/queryCache.ts]] — import-or-re-export; imports `peek`, `setQueryData`, `subscribe`
- [[Reference/Desktop/TypeScript/api/queryTags|src/api/queryTags.ts]] — import-or-re-export; imports `TAG`
- [[Reference/Desktop/TypeScript/screens/desks/goal/model|src/screens/desks/goal/model.ts]] — import-or-re-export; imports `LensIndex`, `indexLens`
- [[Reference/Desktop/TypeScript/screens/desks/keys/router|src/screens/desks/keys/router.ts]] — import-or-re-export; imports `Timers`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Goals Exams and Certification Workflow|Goals, Exams, and Certification Workflow]] — owns the end-to-end goal path.
- [[Concepts/Goals and Certification|Goals and Certification]] — owns goal and certification semantics.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/desks/video/deskVideo.test.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/desks/video/deskVideo.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/desks/lesson/deskLessons.test.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/desks/lesson/deskLessons.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/desks/goal/freshness.test.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/desks/goal/freshness.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/desks/goal/components.test.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/desks/goal/components.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/desks/goal/GoalDesk.test.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/desks/goal/GoalDesk.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [tests/test_sidecar_goals.py](../../../../../../../../tests/test_sidecar_goals.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_sidecar_exams.py](../../../../../../../../tests/test_sidecar_exams.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_goal_projection.py](../../../../../../../../tests/test_goal_projection.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_exam_session.py](../../../../../../../../tests/test_exam_session.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/screens/desks/goal/controller.ts](../../../../../../../../apps/learnloop-tauri/src/screens/desks/goal/controller.ts) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

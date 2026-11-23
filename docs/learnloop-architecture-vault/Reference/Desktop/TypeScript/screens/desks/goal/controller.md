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

Provides `GoalTransport`, `LIVE_GOAL_TRANSPORT`, `BAND_RECHECK_MS`, `primaryGoalId` and related exports within the desktop's TypeScript/screens/desks/goal ownership area.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/desks/goal/controller.ts](../../../../../../../../apps/learnloop-tauri/src/screens/desks/goal/controller.ts) |
| Source lines | 225 |
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

- `export interface GoalTransport` — interface, line 21
- `export const LIVE_GOAL_TRANSPORT: GoalTransport =` — const, line 36
- `export const BAND_RECHECK_MS = 6000` — const, line 50
- `export function primaryGoalId(goals: GoalsListSnapshot["goals"] | null): string | null` — function, line 54
- `export interface WhyState` — interface, line 76
- `export interface GoalLensState` — interface, line 85
- `export function useGoalLens(` — function, line 105

## Internal implementation anchors

- `const DIM_KEY = "learnloop.desks.goalDim"` — const, line 51
- `const active = (goals ?? []).filter((goal)` — const, line 55
- `function readDim(): boolean` — function, line 60
- `function writeDim(on: boolean): void` — function, line 68
- `const asked = useRef(new Set<string>())` — const, line 122
- `const onErrorRef = useRef(onError)` — const, line 124
- `const report = useCallback((message: string)` — const, line 126
- `const judged = useRef(new Set<string>())` — const, line 127
- `let live = true` — let, line 130
- `const goalId = off ? null : deskGoalId ?? (goals ? primaryGoalId(goals) : null)` — const, line 136
- `let live = true` — let, line 149
- `const waiting = band.status === "judging" || band.status === "pending" || Boolean(band.coverage?.covering)` — const, line 165
- `const handle = timers.set(()` — const, line 167
- `const readingsKey = [...new Set(readings)].sort().join("|")` — const, line 172
- `const indexes = useMemo(()` — const, line 185
- `const out: Record<string, LensIndex | null> =` — const, line 186
- `const indexFor = useCallback((extractionId: string)` — const, line 190
- `const refresh = useCallback(()` — const, line 192
- `const toggleDim = useCallback(()` — const, line 193
- `const setDepth = useCallback((depth: ReadingPathDepth)` — const, line 195
- `const readAnyway = useCallback((extractionId: string, sectionId: string, on: boolean)` — const, line 200
- `const override = useCallback((learningObjectId: string, choice: DeliverablePathChoice, sectionRef?: string)` — const, line 206
- `const mapIt = useCallback(()` — const, line 212
- `const addPhrase = useCallback((phrase: string)` — const, line 218

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

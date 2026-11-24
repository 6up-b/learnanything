---
title: "Desktop module · src/screens/desks/goal/GoalLayer.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.desks.goal.GoalLayer"
language: "TypeScript"
area: "TypeScript/screens/desks/goal"
source_path: "apps/learnloop-tauri/src/screens/desks/goal/GoalLayer.tsx"
source_paths:
  - "apps/learnloop-tauri/src/screens/desks/goal/GoalLayer.tsx"
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

# `src/screens/desks/goal/GoalLayer.tsx`

Area: [[Reference/Desktop/TypeScript/screens/desks/goal/_area|TypeScript/screens/desks/goal]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Implements the `GoalLayer` routed desktop screen and coordinates its learner-facing workflow state.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/desks/goal/GoalLayer.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/desks/goal/GoalLayer.tsx) |
| Source lines | 292 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/desks/goal/_area|TypeScript/screens/desks/goal]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/DeskShell|src/screens/desks/DeskShell.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/goal/GoalLayer|src/screens/desks/goal/GoalLayer.tsx]]

## Public API

- `export interface GoalReading` — interface, line 37
- `export interface GoalPadAnchor` — interface, line 47
- `export interface GoalDesk` — interface, line 55
- `export function useGoalDesk(` — function, line 73

## Internal implementation anchors

- `function readFlag(key: string | null): boolean` — function, line 18
- `function writeFlag(key: string | null, on: boolean): void` — function, line 27
- `const asked = useMemo(()` — const, line 91
- `const chooseGoal = useCallback((goalId: string | null)` — const, line 97
- `const goal = useGoalLens(` — const, line 102
- `const pending = useRef<unknown>(null)` — const, line 106
- `const shownRef = useRef<WhyState | null>(null)` — const, line 107
- `const handlers = useMemo<MarkHandlers>(()` — const, line 109
- `const now = shownRef.current` — const, line 117
- `const lenses = useMemo(()` — const, line 128
- `const out = new Map<string, ReaderLens | null>()` — const, line 129
- `const lensFor = useCallback((windowId: string)` — const, line 138
- `const focusedWindowId = focused?.windowId ?? null` — const, line 143
- `const focusedReading = focused?.extractionId ?? null` — const, line 144
- `let frame = 0` — let, line 148
- `const read = ()` — const, line 149
- `const host = document.querySelector(`[$` — const, line 151
- `const line = host.getBoundingClientRect().top + 80` — const, line 153
- `const passages = [...host.querySelectorAll<HTMLElement>("[data-span-id]")]` — const, line 154
- `const at = passages.find((element)` — const, line 155
- `const span = at?.getAttribute("data-span-id") ?? null` — const, line 156
- `const schedule = ()` — const, line 159
- `const remove = hubFor(focusedWindowId).listen("document", "scroll", schedule, true)` — const, line 160
- `const handle = timers.set(schedule, 600)` — const, line 162
- `const focusedIndex: LensIndex | null = focused?.extractionId ? indexFor(focused.extractionId) : null` — const, line 167
- `const here: HereView | null = focused ? (focused.extractionId ? hereLine(focusedIndex, topSpan ?? focused.readingSpan, topSpan ? null : focused.where, band) :` — const, line 168
- `const togglePath = useCallback(()` — const, line 173
- `const openLo = useCallback((learningObjectId: string)` — const, line 179
- `const dot = band?.learningObjects?.find((each)` — const, line 180
- `const onNext = useCallback(()` — const, line 184
- `const next = band?.next` — const, line 185
- `const host = (next.check?.host ?? null) as` — const, line 189
- `const notNeeded = useMemo<NotNeeded[]>(()` — const, line 194
- `const out: NotNeeded[] = []` — const, line 195
- `const seen = new Set<string>()` — const, line 196
- `const padLine = useCallback((padIds: readonly string[])` — const, line 207
- `const wanted = new Set(padIds)` — const, line 209
- `const rank = ["core", "supporting", "later", "already_shown", "partial", "skippable", "unmapped"]` — const, line 210
- `let best:` — let, line 211
- `const section = indexFor(anchor.extractionId)?.bySpan.get(anchor.spanId)` — const, line 214
- `const lo = section.learningObjects.find((entry)` — const, line 219
- `const kind = markKind(section.level)` — const, line 220
- `const text = section.held ? "a cold check is due on what these pads link to" : section.level === "skippable" ? `not needed for your goal · $` — const, line 221
- `const hasBand = Boolean(band)` — const, line 232
- `const bandNode = band ? ( <GoalBand band=` — const, line 233
- `const topChip = !goal.goalId && goal.goals !== null ? <GoalTopChip goals=` — const, line 248
- `const overlays = ( <>` — const, line 249
- `const rowGoal = useCallback((extractionId: string | null, padIds: readonly string[]): ShelfGoal | null` — const, line 269
- `const wanted = new Set(padIds)` — const, line 273
- `const rank = ["core", "supporting", "later", "already_shown", "partial", "skippable", "unmapped"]` — const, line 274
- `let best: ReturnType<LensIndex["bySpan"]["get"]> = undefined` — let, line 275
- `const section = indexFor(anchor.extractionId)?.bySpan.get(anchor.spanId)` — const, line 278
- `const lo = best.learningObjects.find((entry)` — const, line 282
- `const mark = markKind(best.level)` — const, line 283
- `const primaryFor = useCallback((learningObjectId: string)` — const, line 287
- `const primary = band?.learningObjects?.find((dot)` — const, line 288

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/desks/DeskShell|src/screens/desks/DeskShell.tsx]] — import-or-re-export: `GoalReading`, `useGoalDesk`; references `GoalReading`, `useGoalDesk`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `DeliverableSectionDto`
- [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]] — import-or-re-export; imports `ReaderLens`
- [[Reference/Desktop/TypeScript/screens/desks/goal/GoalBand|src/screens/desks/goal/GoalBand.tsx]] — import-or-re-export; imports `GoalBand`, `GoalTopChip`, `HereView`
- [[Reference/Desktop/TypeScript/screens/desks/goal/PathView|src/screens/desks/goal/PathView.tsx]] — import-or-re-export; imports `NotNeeded`, `PathView`
- [[Reference/Desktop/TypeScript/screens/desks/goal/controller|src/screens/desks/goal/controller.ts]] — import-or-re-export; imports `GoalTransport`, `WhyState`, `useGoalLens`
- [[Reference/Desktop/TypeScript/screens/desks/goal/marks|src/screens/desks/goal/marks.tsx]] — import-or-re-export; imports `MarkHandlers`, `WHY_HIDE_MS`, `WHY_OPEN_MS`, `WhyCard`, `readerLens`
- [[Reference/Desktop/TypeScript/screens/desks/goal/model|src/screens/desks/goal/model.ts]] — import-or-re-export; imports `LensIndex`, `ShelfGoal`, `hereLine`, `markKind`, `shelfGoal`
- [[Reference/Desktop/TypeScript/screens/desks/keys/listeners|src/screens/desks/keys/listeners.ts]] — import-or-re-export; imports `WINDOW_ATTRIBUTE`
- [[Reference/Desktop/TypeScript/screens/desks/keys/router|src/screens/desks/keys/router.ts]] — import-or-re-export; imports `Timers`
- [[Reference/Desktop/TypeScript/screens/desks/lifecycle|src/screens/desks/lifecycle.tsx]] — import-or-re-export; imports `ListenerHub`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Goals Exams and Certification Workflow|Goals, Exams, and Certification Workflow]] — owns the end-to-end goal path.
- [[Concepts/Goals and Certification|Goals and Certification]] — owns goal and certification semantics.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/desks/goal/components.test.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/desks/goal/components.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
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

1. Modify [apps/learnloop-tauri/src/screens/desks/goal/GoalLayer.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/desks/goal/GoalLayer.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

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
| Source lines | 289 |
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
- `export interface GoalDesk` — interface, line 53
- `export function useGoalDesk(` — function, line 71

## Internal implementation anchors

- `function readFlag(key: string | null): boolean` — function, line 18
- `function writeFlag(key: string | null, on: boolean): void` — function, line 27
- `const asked = useMemo(()` — const, line 89
- `const chooseGoal = useCallback((goalId: string | null)` — const, line 95
- `const goal = useGoalLens(` — const, line 100
- `const pending = useRef<unknown>(null)` — const, line 104
- `const shownRef = useRef<WhyState | null>(null)` — const, line 105
- `const handlers = useMemo<MarkHandlers>(()` — const, line 107
- `const now = shownRef.current` — const, line 115
- `const lenses = useMemo(()` — const, line 126
- `const out = new Map<string, ReaderLens | null>()` — const, line 127
- `const lensFor = useCallback((windowId: string)` — const, line 136
- `const focusedWindowId = focused?.windowId ?? null` — const, line 141
- `const focusedReading = focused?.extractionId ?? null` — const, line 142
- `let frame = 0` — let, line 146
- `const read = ()` — const, line 147
- `const host = document.querySelector(`[$` — const, line 149
- `const line = host.getBoundingClientRect().top + 80` — const, line 151
- `const passages = [...host.querySelectorAll<HTMLElement>("[data-span-id]")]` — const, line 152
- `const at = passages.find((element)` — const, line 153
- `const span = at?.getAttribute("data-span-id") ?? null` — const, line 154
- `const schedule = ()` — const, line 157
- `const remove = hubFor(focusedWindowId).listen("document", "scroll", schedule, true)` — const, line 158
- `const handle = timers.set(schedule, 600)` — const, line 160
- `const focusedIndex: LensIndex | null = focused?.extractionId ? indexFor(focused.extractionId) : null` — const, line 165
- `const here: HereView | null = focused ? (focused.extractionId ? hereLine(focusedIndex, topSpan ?? focused.readingSpan, topSpan ? null : focused.where, band) :` — const, line 166
- `const togglePath = useCallback(()` — const, line 171
- `const openLo = useCallback((learningObjectId: string)` — const, line 177
- `const dot = band?.learningObjects?.find((each)` — const, line 178
- `const onNext = useCallback(()` — const, line 182
- `const next = band?.next` — const, line 183
- `const host = (next.check?.host ?? null) as` — const, line 187
- `const notNeeded = useMemo<NotNeeded[]>(()` — const, line 192
- `const out: NotNeeded[] = []` — const, line 193
- `const seen = new Set<string>()` — const, line 194
- `const padLine = useCallback((padIds: readonly string[])` — const, line 205
- `const wanted = new Set(padIds)` — const, line 207
- `const rank = ["core", "supporting", "later", "already_shown", "partial", "skippable", "unmapped"]` — const, line 208
- `let best:` — let, line 209
- `const section = indexFor(anchor.extractionId)?.bySpan.get(anchor.spanId)` — const, line 212
- `const lo = section.learningObjects.find((entry)` — const, line 217
- `const kind = markKind(section.level)` — const, line 218
- `const text = section.held ? "a cold check is due on what these pads link to" : section.level === "skippable" ? `not needed for your goal · $` — const, line 219
- `const hasBand = Boolean(band)` — const, line 230
- `const bandNode = band ? ( <GoalBand band=` — const, line 231
- `const topChip = !goal.goalId && goal.goals !== null ? <GoalTopChip goals=` — const, line 246
- `const overlays = ( <>` — const, line 247
- `const rowGoal = useCallback((extractionId: string | null, padIds: readonly string[]): ShelfGoal | null` — const, line 266
- `const wanted = new Set(padIds)` — const, line 270
- `const rank = ["core", "supporting", "later", "already_shown", "partial", "skippable", "unmapped"]` — const, line 271
- `let best: ReturnType<LensIndex["bySpan"]["get"]> = undefined` — let, line 272
- `const section = indexFor(anchor.extractionId)?.bySpan.get(anchor.spanId)` — const, line 275
- `const lo = best.learningObjects.find((entry)` — const, line 279
- `const mark = markKind(best.level)` — const, line 280
- `const primaryFor = useCallback((learningObjectId: string)` — const, line 284
- `const primary = band?.learningObjects?.find((dot)` — const, line 285

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

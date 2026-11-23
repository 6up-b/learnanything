---
title: "Desktop module · src/screens/desks/goal/marks.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.desks.goal.marks"
language: "TypeScript"
area: "TypeScript/screens/desks/goal"
source_path: "apps/learnloop-tauri/src/screens/desks/goal/marks.tsx"
source_paths:
  - "apps/learnloop-tauri/src/screens/desks/goal/marks.tsx"
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

# `src/screens/desks/goal/marks.tsx`

Area: [[Reference/Desktop/TypeScript/screens/desks/goal/_area|TypeScript/screens/desks/goal]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Implements the `marks` routed desktop screen and coordinates its learner-facing workflow state.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/desks/goal/marks.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/desks/goal/marks.tsx) |
| Source lines | 174 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/desks/goal/_area|TypeScript/screens/desks/goal]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/DeskShell|src/screens/desks/DeskShell.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/goal/GoalLayer|src/screens/desks/goal/GoalLayer.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/goal/marks|src/screens/desks/goal/marks.tsx]]

## Public API

- `export const WHY_OPEN_MS = 120` — const, line 12
- `export const WHY_HIDE_MS = 160` — const, line 13
- `export interface MarkHandlers` — interface, line 15
- `export function readerLens(` — function, line 27
- `export function WhyCard(` — function, line 133

## Internal implementation anchors

- `function rectOf(event: ReactMouseEvent<HTMLElement>): WhyState["rect"]` — function, line 21
- `const box = event.currentTarget.getBoundingClientRect()` — const, line 22
- `const markFor = (spanId: string, extra = "")` — const, line 38
- `const section = index.bySpan.get(spanId)` — const, line 39
- `const kind = section ? markKind(section.level) : null` — const, line 40
- `const why = (event: ReactMouseEvent<HTMLElement>): WhyState` — const, line 42
- `const classFor = (spanId: string, keep: boolean)` — const, line 56
- `const section = index.bySpan.get(spanId)` — const, line 57
- `const kind = markKind(section.level)` — const, line 59
- `const section = index.starts.get(spanId)` — const, line 68
- `const callout = section ? calloutFor(section) : null` — const, line 69
- `function clock(seconds: number): string` — function, line 88
- `const whole = Math.max(0, Math.floor(seconds))` — const, line 89
- `function watchLens(index: LensIndex, classFor: (spanId: string, keep: boolean)` — function, line 95
- `const onPath = index.sections.filter((section)` — const, line 97
- `const classes = spanIds.length ? classFor(spanIds[0], false) : undefined` — const, line 100
- `const first = onPath[0]` — const, line 106
- `const range = timeOf(first.spanIds)` — const, line 108
- `const lo = first.learningObjects.find((entry)` — const, line 109
- `const role = first.reasonKey === "primary" ? "primary for" : first.reasonKey === "alternate" ? "another way for" : first.reasonKey === "prerequisite" ? "background for" : "supporting"` — const, line 110
- `const skippable = index.sections.find((section)` — const, line 120
- `const ref = useRef<HTMLDivElement | null>(null)` — const, line 134
- `const card = ref.current` — const, line 139
- `const width = card.offsetWidth` — const, line 141
- `const height = card.offsetHeight` — const, line 142
- `let left = why.rect.right + 10` — let, line 143
- `const top = Math.max(46, Math.min(why.rect.top - 6, window.innerHeight - height - 34))` — const, line 145
- `const frame = requestAnimationFrame(()` — const, line 150
- `const kind = markKind(section.level)` — const, line 153
- `const legend = kind === "later" || kind === "shown" ? "skip" : kind === "partial" ? "partial" : kind` — const, line 154
- `const reason = section.reasonMd.replace(/\.?\s*$/, ".")` — const, line 155

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/desks/goal/GoalLayer|src/screens/desks/goal/GoalLayer.tsx]] — import-or-re-export: `MarkHandlers`, `WHY_HIDE_MS`, `WHY_OPEN_MS`, `WhyCard`, `readerLens`; references `MarkHandlers`, `WHY_HIDE_MS`, `WHY_OPEN_MS`, `WhyCard`, `readerLens`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `GoalBandDto`
- [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]] — import-or-re-export; imports `ReaderLens`
- [[Reference/Desktop/TypeScript/screens/desks/goal/controller|src/screens/desks/goal/controller.ts]] — import-or-re-export; imports `WhyState`
- [[Reference/Desktop/TypeScript/screens/desks/goal/model|src/screens/desks/goal/model.ts]] — import-or-re-export; imports `LensIndex`, `calloutFor`, `goalShort`, `isDimmed`, `markKind`, `whyLevelLine`
- [[Reference/Desktop/TypeScript/screens/reader/YouTubeWatchPanel|src/screens/reader/YouTubeWatchPanel.tsx]] — import-or-re-export; imports `WatchLens`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Goals Exams and Certification Workflow|Goals, Exams, and Certification Workflow]] — owns the end-to-end goal path.
- [[Concepts/Goals and Certification|Goals and Certification]] — owns goal and certification semantics.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/desks/goal/watch.test.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/desks/goal/watch.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
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

1. Modify [apps/learnloop-tauri/src/screens/desks/goal/marks.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/desks/goal/marks.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

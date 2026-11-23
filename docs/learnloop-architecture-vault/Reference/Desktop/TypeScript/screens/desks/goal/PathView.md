---
title: "Desktop module · src/screens/desks/goal/PathView.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.desks.goal.PathView"
language: "TypeScript"
area: "TypeScript/screens/desks/goal"
source_path: "apps/learnloop-tauri/src/screens/desks/goal/PathView.tsx"
source_paths:
  - "apps/learnloop-tauri/src/screens/desks/goal/PathView.tsx"
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

# `src/screens/desks/goal/PathView.tsx`

Area: [[Reference/Desktop/TypeScript/screens/desks/goal/_area|TypeScript/screens/desks/goal]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Implements the `PathView` routed desktop screen and coordinates its learner-facing workflow state.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/desks/goal/PathView.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/desks/goal/PathView.tsx) |
| Source lines | 182 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/desks/goal/_area|TypeScript/screens/desks/goal]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/DeskShell|src/screens/desks/DeskShell.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/goal/GoalLayer|src/screens/desks/goal/GoalLayer.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/goal/PathView|src/screens/desks/goal/PathView.tsx]]

## Public API

- `export interface NotNeeded` — interface, line 10
- `export function PathView(` — function, line 33

## Internal implementation anchors

- `type Line = NonNullable<GoalBandDto["path"]>["lines"][number]` — type, line 16
- `function readiness(dot: GoalBandLoDto): string` — function, line 18
- `function paceLine(band: GoalBandDto): string` — function, line 24
- `const pace = band.pace` — const, line 25
- `const ref = useRef<HTMLDivElement | null>(null)` — const, line 44
- `const lines = new Map<string, Line>((band.path?.lines ?? []).map((line)` — const, line 46
- `const dots = band.learningObjects ?? []` — const, line 47
- `const needed = dots.filter((dot)` — const, line 48
- `const prerequisites = dots.filter((dot)` — const, line 49
- `const depthLabel = band.depths?.find((depth)` — const, line 50
- `const onKeyDown = (event: ReactKeyboardEvent)` — const, line 51
- `const line = lines.get(dot.learningObjectId)` — const, line 97
- `const later = dot.kind === "later"` — const, line 98

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/desks/goal/GoalLayer|src/screens/desks/goal/GoalLayer.tsx]] — import-or-re-export: `NotNeeded`, `PathView`; references `NotNeeded`, `PathView`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `DeliverableSectionDto`, `GoalBandDto`, `GoalBandLoDto`, `GoalLensSectionDto`, `ReadingPathDepth`
- [[Reference/Desktop/TypeScript/screens/desks/goal/model|src/screens/desks/goal/model.ts]] — import-or-re-export; imports `formatDay`, `goalLabel`

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

1. Modify [apps/learnloop-tauri/src/screens/desks/goal/PathView.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/desks/goal/PathView.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

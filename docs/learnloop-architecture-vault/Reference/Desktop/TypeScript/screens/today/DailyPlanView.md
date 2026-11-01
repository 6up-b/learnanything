---
title: "Desktop module · src/screens/today/DailyPlanView.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.today.DailyPlanView"
language: "TypeScript"
area: "TypeScript/screens/today"
source_path: "apps/learnloop-tauri/src/screens/today/DailyPlanView.tsx"
source_paths:
  - "apps/learnloop-tauri/src/screens/today/DailyPlanView.tsx"
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

# `src/screens/today/DailyPlanView.tsx`

Area: [[Reference/Desktop/TypeScript/screens/today/_area|TypeScript/screens/today]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Implements the `DailyPlanView` routed desktop screen and coordinates its learner-facing workflow state.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/today/DailyPlanView.tsx](../../../../../../../apps/learnloop-tauri/src/screens/today/DailyPlanView.tsx) |
| Source lines | 440 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/today/_area|TypeScript/screens/today]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `c94882abe7a8f5a7cde491603d6abba8a4c0e2db` |
| Commit timestamp | `2026-10-22T16:58:30-04:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/StartScreen|src/screens/StartScreen.tsx]] → [[Reference/Desktop/TypeScript/screens/today/DailyPlanView|src/screens/today/DailyPlanView.tsx]]

## Public API

- `export function PlanSplitLine(` — function, line 46
- `export function PlanBlockLine(` — function, line 73
- `export function PlanHeadline(` — function, line 106
- `export function PlanReentryPanel(` — function, line 116
- `export interface DailyPlanViewProps` — interface, line 163
- `export function DailyPlanView(` — function, line 181
- `export function PlanDone(` — function, line 366

## Internal implementation anchors

- `const LANE_COLOR: Record<PlanLane, string> =` — const, line 14
- `function laneColor(lane: PlanLane | null | undefined): string` — function, line 21
- `const linkButton: CSSProperties =` — const, line 25
- `const actionButton = (primary = false): CSSProperties` — const, line 35
- `const total = Math.max(plan.blockCountEstimate, block.ordinal)` — const, line 75
- `const label = block.reading ? `reading $` — const, line 76
- `const names = reentry.slippedNames.length ? ` ($` — const, line 117
- `function BlockItems(` — function, line 131
- `const next = block.items.find((item)` — const, line 132
- `const current = item === next` — const, line 136
- `const finished = item.state === "done" || item.state === "skipped"` — const, line 137
- `const plan = data.plan` — const, line 195
- `const done = plan ? plan.status !== "open" : false` — const, line 196
- `const current = plan?.blocks.find((block)` — const, line 197
- `const waiting = !done && !current && plan?.waiting ? plan.waiting : null` — const, line 199
- `const onKey = (event: KeyboardEvent)` — const, line 202
- `const tag = (event.target as HTMLElement | null)?.tagName?.toLowerCase()` — const, line 204
- `const choices = plan.minuteChoices` — const, line 218
- `const index = choices.indexOf(plan.rememberedMinutes)` — const, line 219
- `const next = choices[Math.max(0, Math.min(choices.length - 1, (index < 0 ? 0 : index) + (event.key === "ArrowLeft" ? -1 : 1)))]` — const, line 220
- `const day = data.day` — const, line 229
- `const streak = data.streak` — const, line 230
- `const upcoming = plan.projected[0] ?? null` — const, line 231
- `const selected = minutes === plan.rememberedMinutes` — const, line 245
- `const next = current.items.find((item)` — const, line 307
- `const plan = data.plan!` — const, line 387
- `const empty = (day?.plannedItems ?? 0) === 0 && (day?.readingBlocks ?? 0) === 0` — const, line 388
- `const reentry = plan.kind === "reentry"` — const, line 389
- `const title = empty ? "Nothing due today" : reentry ? "Re-entry done. Keep going?" : "Today complete"` — const, line 390

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/StartScreen|src/screens/StartScreen.tsx]] — import-or-re-export: `PlanSplitLine`; references `PlanSplitLine`
- [[Reference/Desktop/TypeScript/screens/TodayScreen|src/screens/TodayScreen.tsx]] — import-or-re-export: `DailyPlanView`; references `DailyPlanView`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `DailyPlanDto`, `PlanBlockDto`, `PlanLane`, `TodayHeadlineDto`
- [[Reference/Desktop/TypeScript/app/dailyPlan|src/app/dailyPlan.ts]] — import-or-re-export; imports `aboutMinutes`, `minutesPerDay`, `waitingLine`, `waitingMinutes`, `wholeMinutes`
- [[Reference/Desktop/TypeScript/app/keymap|src/app/keymap.ts]] — import-or-re-export; imports `screenLeavesKey`
- [[Reference/Desktop/TypeScript/components/term|src/components/term.tsx]] — import-or-re-export; imports `COLOR`, `FONT_MONO`, `KeyBar`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Start a Learning Cycle#Desktop|desktop learning cycle]] — shows the user-facing session path.
- [[Concepts/Learning System#One attempt|one-attempt model]] — owns learning semantics.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/today/DailyPlanView.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/today/DailyPlanView.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/screens/today/DailyPlanView.tsx](../../../../../../../apps/learnloop-tauri/src/screens/today/DailyPlanView.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

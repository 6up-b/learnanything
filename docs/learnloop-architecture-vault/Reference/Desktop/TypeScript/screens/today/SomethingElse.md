---
title: "Desktop module · src/screens/today/SomethingElse.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.today.SomethingElse"
language: "TypeScript"
area: "TypeScript/screens/today"
source_path: "apps/learnloop-tauri/src/screens/today/SomethingElse.tsx"
source_paths:
  - "apps/learnloop-tauri/src/screens/today/SomethingElse.tsx"
source_commit: "2437f516e5448a5296dbef18eae04d6969512be4"
source_commit_timestamp: "2026-11-08T23:26:15-05:00"
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

# `src/screens/today/SomethingElse.tsx`

Area: [[Reference/Desktop/TypeScript/screens/today/_area|TypeScript/screens/today]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Implements the `SomethingElse` routed desktop screen and coordinates its learner-facing workflow state.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/today/SomethingElse.tsx](../../../../../../../apps/learnloop-tauri/src/screens/today/SomethingElse.tsx) |
| Source lines | 157 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/today/_area|TypeScript/screens/today]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `2437f516e5448a5296dbef18eae04d6969512be4` |
| Commit timestamp | `2026-11-08T23:26:15-05:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/today/SomethingElse|src/screens/today/SomethingElse.tsx]]

## Public API

- `export type SomethingElseSurface = "feedback" | "offer_page" | "today"` — type, line 16
- `export const SOMETHING_ELSE_LINK = "Something else would help"` — const, line 19
- `export function useSomethingElseOn(sessionId: string | null, enabled?: boolean): boolean` — function, line 22
- `export function lessonEntryFor(result: SomethingElseChosenDto): LessonEntry | null` — function, line 28
- `export function SomethingElse(` — function, line 45

## Internal implementation anchors

- `const plan = useDailyPlan(sessionId, enabled === undefined && Boolean(sessionId))` — const, line 23
- `const lesson = result.preference?.outcome === "lesson" ? result.preference.lesson : null` — const, line 29
- `function newKey(): string` — function, line 35
- `const c = (globalThis as` — const, line 36
- `const linkStyle =` — const, line 40
- `const on = useSomethingElseOn(sessionId, enabled)` — const, line 69
- `const key = useRef<string | null>(null)` — const, line 76
- `async function show()` — function, line 79
- `async function choose(option: SomethingElseOptionDto)` — function, line 93
- `const result = await api.planSomethingElse(` — const, line 98
- `const shown = (options?.options ?? []).filter( (option)` — const, line 113

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] — import-or-re-export: `lessonEntryFor`; references `lessonEntryFor`
- [[Reference/Desktop/TypeScript/screens/FeedbackScreen|src/screens/FeedbackScreen.tsx]] — import-or-re-export: `SomethingElse`, `lessonEntryFor`; references `SomethingElse`, `lessonEntryFor`
- [[Reference/Desktop/TypeScript/screens/TodayScreen|src/screens/TodayScreen.tsx]] — import-or-re-export: `lessonEntryFor`; references `lessonEntryFor`
- [[Reference/Desktop/TypeScript/screens/today/DailyPlanView|src/screens/today/DailyPlanView.tsx]] — import-or-re-export: `SomethingElse`; references `SomethingElse`
- [[Reference/Desktop/TypeScript/screens/today/LessonOfferPage|src/screens/today/LessonOfferPage.tsx]] — import-or-re-export: `SomethingElse`; references `SomethingElse`
- [[Reference/Desktop/TypeScript/screens/today/TodayPlace|src/screens/today/TodayPlace.tsx]] — import-or-re-export: `SomethingElse`, `lessonEntryFor`; references `SomethingElse`, `lessonEntryFor`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `SomethingElseChosenDto`, `SomethingElseOptionDto`, `SomethingElseOptionsDto`
- [[Reference/Desktop/TypeScript/app/dailyPlan|src/app/dailyPlan.ts]] — import-or-re-export; imports `useDailyPlan`
- [[Reference/Desktop/TypeScript/components/term|src/components/term.tsx]] — import-or-re-export; imports `COLOR`, `FONT_MONO`
- [[Reference/Desktop/TypeScript/errors|src/errors.ts]] — import-or-re-export; imports `getCommandError`
- [[Reference/Desktop/TypeScript/screens/LessonScreen|src/screens/LessonScreen.tsx]] — import-or-re-export; imports `LessonEntry`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Start a Learning Cycle#Desktop|desktop learning cycle]] — shows the user-facing session path.
- [[Concepts/Learning System#One attempt|one-attempt model]] — owns learning semantics.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/today/SomethingElse.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/today/SomethingElse.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [tests/test_ih3_phone_host.py](../../../../../../../tests/test_ih3_phone_host.py) — cross-boundary name contract: references uniquely owned exported name `SomethingElse`; it does **not** directly execute this source module.

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/screens/today/SomethingElse.tsx](../../../../../../../apps/learnloop-tauri/src/screens/today/SomethingElse.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

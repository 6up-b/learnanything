---
title: "Desktop module · src/screens/workbench/RouteExample.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.workbench.RouteExample"
language: "TypeScript"
area: "TypeScript/screens/workbench"
source_path: "apps/learnloop-tauri/src/screens/workbench/RouteExample.tsx"
source_paths:
  - "apps/learnloop-tauri/src/screens/workbench/RouteExample.tsx"
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

# `src/screens/workbench/RouteExample.tsx`

Area: [[Reference/Desktop/TypeScript/screens/workbench/_area|TypeScript/screens/workbench]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Implements the `RouteExample` routed desktop screen and coordinates its learner-facing workflow state.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/workbench/RouteExample.tsx](../../../../../../../apps/learnloop-tauri/src/screens/workbench/RouteExample.tsx) |
| Source lines | 304 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/workbench/_area|TypeScript/screens/workbench]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/PracticeScreen|src/screens/PracticeScreen.tsx]] → [[Reference/Desktop/TypeScript/screens/workbench/Workbench|src/screens/workbench/Workbench.tsx]] → [[Reference/Desktop/TypeScript/screens/workbench/RouteExample|src/screens/workbench/RouteExample.tsx]]

## Public API

- `export const EXAMPLE_COPY =` — const, line 26
- `export interface ExampleState` — interface, line 35
- `export interface RouteExamples` — interface, line 59
- `export function useRouteExamples(options:` — function, line 79
- `export function PassageExtras(` — function, line 257
- `export function ShowMeExample(` — function, line 283

## Internal implementation anchors

- `const FIRST_POLL_MS = 350` — const, line 41
- `const MAX_POLL_MS = 1500` — const, line 42
- `function sleep(ms: number): Promise<void>` — function, line 44
- `function viewOf(result: NonNullable<WorkbenchHelpJobDto["result"]>, hintAssistId: string | null): WorkbenchExampleViewDto | null` — function, line 48
- `const beforeRef = useRef(options.beforeRequest)` — const, line 89
- `const alive = useRef(true)` — const, line 97
- `const whenLive = useWhenLive()` — const, line 98
- `const poll = useCallback(async (started: WorkbenchHelpJobDto): Promise<WorkbenchHelpJobDto>` — const, line 107
- `let job = started` — let, line 108
- `let wait = FIRST_POLL_MS` — let, line 109
- `const followExample = useCallback((hintAssistId: string, jobId: string)` — const, line 121
- `const job = await poll(await api.workbenchHelpJob(jobId))` — const, line 126
- `const view = job.result ? viewOf(job.result, hintAssistId) : null` — const, line 128
- `const next =` — const, line 131
- `const next =` — const, line 138
- `const restore = useCallback((state: WorkbenchHelpStateDto)` — const, line 146
- `const restored: Record<string, ExampleState> =` — const, line 149
- `const showMe = useCallback(async (focusedStepId: string | null)` — const, line 157
- `const job = await poll(await api.workbenchShowExample(` — const, line 168
- `const result = job.result` — const, line 170
- `const view = result ? viewOf(result, null) : null` — const, line 171
- `const bridgeFor = useCallback((hintAssistId: string, bridge: BridgeState | undefined)` — const, line 182
- `const anotherBridge = useCallback(async (hintAssistId: string, bridge: BridgeState)` — const, line 186
- `const picked = await api.workbenchAnotherPassage(` — const, line 189
- `const view = picked.passage` — const, line 191
- `const anotherExample = useCallback(async (key:` — const, line 203
- `const picked = await api.workbenchAnotherPassage(` — const, line 206
- `const next: ExampleState =` — const, line 208
- `function targetOf(view: WorkbenchExampleViewDto): PassageTarget` — function, line 224
- `function ExampleLine(` — function, line 228
- `const view = state.view` — const, line 239
- `const example = rw2c.underHint[hintAssistId]` — const, line 263
- `const anotherBridge = rw2c.passageDraw && bridge?.status === "ready" && bridge.alternatives ? bridge : null` — const, line 264

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/workbench/Workbench|src/screens/workbench/Workbench.tsx]] — import-or-re-export: `PassageExtras`, `ShowMeExample`, `useRouteExamples`; references `PassageExtras`, `ShowMeExample`, `useRouteExamples`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `PassageTarget`, `WorkbenchExampleViewDto`, `WorkbenchHelpJobDto`, `WorkbenchHelpStateDto`
- [[Reference/Desktop/TypeScript/components/PlainParts|src/components/PlainParts.tsx]] — import-or-re-export; imports `quietLine`, `quietLink`
- [[Reference/Desktop/TypeScript/errors|src/errors.ts]] — import-or-re-export; imports `errorMessage`
- [[Reference/Desktop/TypeScript/screens/desks/lifecycle|src/screens/desks/lifecycle.tsx]] — import-or-re-export; imports `useWhenLive`
- [[Reference/Desktop/TypeScript/screens/reader/voices|src/screens/reader/voices.tsx]] — import-or-re-export; imports `MeaningLabel`
- [[Reference/Desktop/TypeScript/screens/workbench/useWorkbenchHelp|src/screens/workbench/useWorkbenchHelp.ts]] — import-or-re-export; imports `BridgeState`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Goals Exams and Certification Workflow|Goals, Exams, and Certification Workflow]] — owns the end-to-end goal path.
- [[Concepts/Goals and Certification|Goals and Certification]] — owns goal and certification semantics.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/workbench/rw2cFixRound2.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/workbench/rw2cFixRound2.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/workbench/RouteExample.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/workbench/RouteExample.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [tests/test_sidecar_goals.py](../../../../../../../tests/test_sidecar_goals.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_sidecar_exams.py](../../../../../../../tests/test_sidecar_exams.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_goal_projection.py](../../../../../../../tests/test_goal_projection.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_exam_session.py](../../../../../../../tests/test_exam_session.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/screens/workbench/RouteExample.tsx](../../../../../../../apps/learnloop-tauri/src/screens/workbench/RouteExample.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

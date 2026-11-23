---
title: "Desktop module · src/screens/desks/notebook/NotebookFrame.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.desks.notebook.NotebookFrame"
language: "TypeScript"
area: "TypeScript/screens/desks/notebook"
source_path: "apps/learnloop-tauri/src/screens/desks/notebook/NotebookFrame.tsx"
source_paths:
  - "apps/learnloop-tauri/src/screens/desks/notebook/NotebookFrame.tsx"
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

# `src/screens/desks/notebook/NotebookFrame.tsx`

Area: [[Reference/Desktop/TypeScript/screens/desks/notebook/_area|TypeScript/screens/desks/notebook]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Implements the `NotebookFrame` routed desktop screen and coordinates its learner-facing workflow state.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/desks/notebook/NotebookFrame.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/desks/notebook/NotebookFrame.tsx) |
| Source lines | 261 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/desks/notebook/_area|TypeScript/screens/desks/notebook]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/DeskShell|src/screens/desks/DeskShell.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/notebook/NotebookFrame|src/screens/desks/notebook/NotebookFrame.tsx]]

## Public API

- `export interface NotebookBridgeHost` — interface, line 22
- `export const NotebookBridgeContext = createContext<NotebookBridgeHost | null>(null)` — const, line 27
- `export interface NotebookApi` — interface, line 30
- `export const POLL_MS =` — const, line 37
- `export interface NotebookError` — interface, line 39
- `export type FrameView = |` — type, line 45
- `export function frameView(session: NotebookSessionDto | null, error: NotebookError | null): FrameView` — function, line 55
- `export function statusLine(view: FrameView): string` — function, line 85
- `export interface NotebookFrameProps` — interface, line 112
- `export function NotebookFrame(` — function, line 129

## Internal implementation anchors

- `const STOPPED_WORDS: Record<string, string> =` — const, line 75
- `function errorOf(error: unknown): NotebookError` — function, line 104
- `const record = error as` — const, line 106
- `const lifecycle = useWindowLifecycle()` — const, line 130
- `const paused = isPaused(lifecycle.state)` — const, line 131
- `const whenLive = useWhenLive()` — const, line 132
- `const hub = useListenerHub()` — const, line 133
- `const host = useContext(NotebookBridgeContext)` — const, line 134
- `const frameRef = useRef<HTMLIFrameElement | null>(null)` — const, line 138
- `const preview = lifecycle.state === "preview"` — const, line 139
- `const onSessionRef = useRef(onSession)` — const, line 140
- `const readyPollRef = useRef(readyPoll)` — const, line 142
- `let cancelled = false` — let, line 151
- `let timer: ReturnType<typeof setTimeout> | null = null` — let, line 152
- `const follow = async (sessionId: string)` — const, line 153
- `const next = await calls.notebookStatus(` — const, line 157
- `const opened = await calls.notebookOpen(path === undefined ?` — const, line 171
- `const current = frameView(session, error)` — const, line 186
- `const frameUrl = current.kind === "ready" ? current.frameUrl : session?.state === "restarting" ? session.frameUrl : null` — const, line 187
- `const origin = frameUrl ? frameOrigin(frameUrl) : null` — const, line 188
- `const frame = frameRef.current` — const, line 194
- `const message = parseBridgeMessage(event.data)` — const, line 196
- `const box = frame.getBoundingClientRect()` — const, line 198
- `const placed = toPage(message,` — const, line 199
- `const frame = frameRef.current` — const, line 211
- `const retry = useCallback(()` — const, line 217
- `const line = statusLine(current)` — const, line 230
- `const action = current.kind === "stopped" ? "resume" : current.kind === "failed" || current.kind === "unavailable" ? "try again" : null` — const, line 231

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/fixtures/desks/harness|src/fixtures/desks/harness.tsx]] — import-or-re-export: `NotebookBridgeContext`, `NotebookBridgeHost`, `NotebookFrame`; references `NotebookBridgeContext`, `NotebookBridgeHost`, `NotebookFrame`
- [[Reference/Desktop/TypeScript/screens/desks/DeskShell|src/screens/desks/DeskShell.tsx]] — import-or-re-export: `NotebookBridgeContext`, `NotebookBridgeHost`; references `NotebookBridgeContext`, `NotebookBridgeHost`
- [[Reference/Desktop/TypeScript/screens/desks/notebook/LessonNotebook|src/screens/desks/notebook/LessonNotebook.tsx]] — import-or-re-export: `NotebookApi`, `NotebookFrame`; references `NotebookApi`, `NotebookFrame`
- [[Reference/Desktop/TypeScript/screens/desks/notebook/PadCell|src/screens/desks/notebook/PadCell.tsx]] — import-or-re-export: `NotebookFrame`; references `NotebookFrame`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `NotebookOpenInput`, `NotebookOwner`, `NotebookSessionDto`
- [[Reference/Desktop/TypeScript/screens/desks/lifecycle|src/screens/desks/lifecycle.tsx]] — import-or-re-export; imports `isPaused`, `useListenerHub`, `useWhenLive`, `useWindowLifecycle`
- [[Reference/Desktop/TypeScript/screens/desks/notebook/bridge|src/screens/desks/notebook/bridge.ts]] — import-or-re-export; imports `BridgeMessage`, `frameOrigin`, `fromFrame`, `parseBridgeMessage`, `toPage`

### Assets, platform, and third-party dependencies

- Local asset: [apps/learnloop-tauri/src/screens/desks/notebook/notebook.css](../../../../../../../../apps/learnloop-tauri/src/screens/desks/notebook/notebook.css)
- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/desks/notebook/NotebookFrame.test.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/desks/notebook/NotebookFrame.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/desks/notebook/LessonNotebook.test.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/desks/notebook/LessonNotebook.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/screens/desks/notebook/NotebookFrame.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/desks/notebook/NotebookFrame.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

---
title: "Desktop module · src/screens/desks/lifecycle.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.desks.lifecycle"
language: "TypeScript"
area: "TypeScript/screens/desks"
source_path: "apps/learnloop-tauri/src/screens/desks/lifecycle.tsx"
source_paths:
  - "apps/learnloop-tauri/src/screens/desks/lifecycle.tsx"
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

# `src/screens/desks/lifecycle.tsx`

Area: [[Reference/Desktop/TypeScript/screens/desks/_area|TypeScript/screens/desks]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Implements the `lifecycle` routed desktop screen and coordinates its learner-facing workflow state.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/desks/lifecycle.tsx](../../../../../../../apps/learnloop-tauri/src/screens/desks/lifecycle.tsx) |
| Source lines | 175 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/desks/_area|TypeScript/screens/desks]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/lifecycle|src/screens/desks/lifecycle.tsx]]

## Public API

- `export type WindowState = "active" | "visible" | "offscreen" | "hidden" | "preview"` — type, line 16
- `export interface WindowLifecycle` — interface, line 18
- `export const WindowLifecycleContext = createContext<WindowLifecycle>(SINGLE_SURFACE)` — const, line 26
- `export function useWindowLifecycle(): WindowLifecycle` — function, line 28
- `export function isPaused(state: WindowState): boolean` — function, line 33
- `export function mayLogReading(state: WindowState): boolean` — function, line 39
- `export function useWindowPaused(): boolean` — function, line 43
- `export function useWhenLive(): ()` — function, line 51
- `export function useReadingActivityAllowed(): boolean` — function, line 66
- `export function useReadingActivityRef():` — function, line 71
- `export interface WindowStateInput` — interface, line 78
- `export function windowState(input: WindowStateInput): WindowState` — function, line 88
- `export type ListenTarget = "window" | "document"` — type, line 98
- `export interface ListenerHub` — interface, line 100
- `export const DIRECT_HUB: ListenerHub =` — const, line 106
- `export const ListenerHubContext = createContext<ListenerHub>(DIRECT_HUB)` — const, line 115
- `export function useListenerHub(): ListenerHub` — function, line 117
- `export function useHubListener<E extends Event = Event>( target: ListenTarget, type: string, handler: (event: E)` — function, line 122
- `export type ClaimedScope = "menu" | "check" | "typing"` — type, line 145
- `export interface ScopeClaims` — interface, line 147
- `export const ScopeClaimsContext = createContext<ScopeClaims>(NO_CLAIMS)` — const, line 153
- `export function useScopeClaim(scope: ClaimedScope, open: boolean): void` — function, line 158
- `export function WindowScope(` — function, line 167

## Internal implementation anchors

- `const SINGLE_SURFACE: WindowLifecycle =` — const, line 24
- `const paused = useWindowPaused()` — const, line 52
- `const pausedRef = useRef(paused)` — const, line 53
- `const waiters = useRef<Array<()` — const, line 55
- `const ready = waiters.current` — const, line 58
- `const allowed = useReadingActivityAllowed()` — const, line 72
- `const ref = useRef(allowed)` — const, line 73
- `const node: EventTarget = target === "window" ? window : document` — const, line 108
- `const listener = handler as EventListener` — const, line 109
- `const hub = useListenerHub()` — const, line 128
- `const handlerRef = useRef(handler)` — const, line 129
- `const capture = options?.capture ?? false` — const, line 131
- `const passive = options?.passive` — const, line 132
- `const enabled = options?.enabled ?? true` — const, line 133
- `const onEvent = (event: E)` — const, line 136
- `const NO_CLAIMS: ScopeClaims =` — const, line 151
- `const claims = useContext(ScopeClaimsContext)` — const, line 159
- `const owner = useId()` — const, line 160

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/components/PdfReaderPane|src/components/PdfReaderPane.tsx]] — import-or-re-export: `useListenerHub`; references `useListenerHub`
- [[Reference/Desktop/TypeScript/fixtures/desks/harness|src/fixtures/desks/harness.tsx]] — import-or-re-export: `DIRECT_HUB`, `WindowScope`, `WindowState`; references `DIRECT_HUB`, `WindowScope`, `WindowState`
- [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]] — import-or-re-export: `ListenerHub`, `ScopeClaims`, `WindowLifecycle`, `WindowScope`, `isPaused`, `useListenerHub`, `useScopeClaim`, `useWindowLifecycle`, `useWindowPaused`; references `ListenerHub`, `ScopeClaims`, `WindowLifecycle`, `WindowScope`, `isPaused`, `useListenerHub`, `useScopeClaim`, `useWindowLifecycle`, `useWindowPaused`
- [[Reference/Desktop/TypeScript/screens/desks/DeskShell|src/screens/desks/DeskShell.tsx]] — import-or-re-export: `ClaimedScope`, `ListenerHub`, `ScopeClaims`, `WindowLifecycle`, `WindowScope`, `isPaused`, `windowState`; references `ClaimedScope`, `ListenerHub`, `ScopeClaims`, `WindowLifecycle`, `WindowScope`, `isPaused`, `windowState`
- [[Reference/Desktop/TypeScript/screens/desks/keys/listeners|src/screens/desks/keys/listeners.ts]] — import-or-re-export: `ListenTarget`, `ListenerHub`; references `ListenTarget`, `ListenerHub`
- [[Reference/Desktop/TypeScript/screens/reader/ComparePointTable|src/screens/reader/ComparePointTable.tsx]] — import-or-re-export: `useListenerHub`; references `useListenerHub`
- [[Reference/Desktop/TypeScript/screens/reader/DeliverableSliceCard|src/screens/reader/DeliverableSliceCard.tsx]] — import-or-re-export: `useWhenLive`; references `useWhenLive`
- [[Reference/Desktop/TypeScript/screens/reader/LibraryPane|src/screens/reader/LibraryPane.tsx]] — import-or-re-export: `useListenerHub`; references `useListenerHub`
- [[Reference/Desktop/TypeScript/screens/reader/PreparingView|src/screens/reader/PreparingView.tsx]] — import-or-re-export: `useWindowPaused`; references `useWindowPaused`
- [[Reference/Desktop/TypeScript/screens/reader/ReaderNotes|src/screens/reader/ReaderNotes.tsx]] — import-or-re-export: `useWhenLive`; references `useWhenLive`
- [[Reference/Desktop/TypeScript/screens/reader/ReaderWorkingPosture|src/screens/reader/ReaderWorkingPosture.tsx]] — import-or-re-export: `useListenerHub`; references `useListenerHub`
- [[Reference/Desktop/TypeScript/screens/reader/ReadingPathCard|src/screens/reader/ReadingPathCard.tsx]] — import-or-re-export: `useWhenLive`; references `useWhenLive`
- [[Reference/Desktop/TypeScript/screens/reader/WrapUpPanel|src/screens/reader/WrapUpPanel.tsx]] — import-or-re-export: `useListenerHub`, `useScopeClaim`; references `useListenerHub`, `useScopeClaim`
- [[Reference/Desktop/TypeScript/screens/reader/YouTubeWatchPanel|src/screens/reader/YouTubeWatchPanel.tsx]] — import-or-re-export: `useListenerHub`, `useWindowPaused`; references `useListenerHub`, `useWindowPaused`
- [[Reference/Desktop/TypeScript/screens/reader/bareAlt|src/screens/reader/bareAlt.ts]] — import-or-re-export: `useListenerHub`; references `useListenerHub`
- [[Reference/Desktop/TypeScript/screens/reader/figures/FigureInline|src/screens/reader/figures/FigureInline.tsx]] — import-or-re-export: `useWindowPaused`; references `useWindowPaused`
- [[Reference/Desktop/TypeScript/screens/reader/figures/useFigures|src/screens/reader/figures/useFigures.ts]] — import-or-re-export: `useWhenLive`; references `useWhenLive`
- [[Reference/Desktop/TypeScript/screens/reader/guidePlan|src/screens/reader/guidePlan.ts]] — import-or-re-export: `useWhenLive`; references `useWhenLive`
- [[Reference/Desktop/TypeScript/screens/reader/useActiveReading|src/screens/reader/useActiveReading.ts]] — import-or-re-export: `useWhenLive`; references `useWhenLive`
- [[Reference/Desktop/TypeScript/screens/reader/useCueDiscovery|src/screens/reader/useCueDiscovery.ts]] — import-or-re-export: `useWhenLive`; references `useWhenLive`
- [[Reference/Desktop/TypeScript/screens/reader/useCueImpressions|src/screens/reader/useCueImpressions.ts]] — import-or-re-export: `useListenerHub`, `useReadingActivityAllowed`; references `useListenerHub`, `useReadingActivityAllowed`
- [[Reference/Desktop/TypeScript/screens/reader/useIntentBox|src/screens/reader/useIntentBox.ts]] — import-or-re-export: `useListenerHub`, `useScopeClaim`; references `useListenerHub`, `useScopeClaim`
- [[Reference/Desktop/TypeScript/screens/reader/useLibraryAsk|src/screens/reader/useLibraryAsk.ts]] — import-or-re-export: `useWhenLive`; references `useWhenLive`
- [[Reference/Desktop/TypeScript/screens/reader/useLibraryExercises|src/screens/reader/useLibraryExercises.ts]] — import-or-re-export: `useWhenLive`; references `useWhenLive`
- [[Reference/Desktop/TypeScript/screens/reader/useReaderCues|src/screens/reader/useReaderCues.ts]] — import-or-re-export: `useListenerHub`; references `useListenerHub`
- [[Reference/Desktop/TypeScript/screens/reader/useReaderInquiry|src/screens/reader/useReaderInquiry.ts]] — import-or-re-export: `useListenerHub`, `useScopeClaim`, `useWindowPaused`; references `useListenerHub`, `useScopeClaim`, `useWindowPaused`
- [[Reference/Desktop/TypeScript/screens/reader/useReaderRecap|src/screens/reader/useReaderRecap.ts]] — import-or-re-export: `useListenerHub`, `useWhenLive`; references `useListenerHub`, `useWhenLive`
- [[Reference/Desktop/TypeScript/screens/reader/useReaderRequests|src/screens/reader/useReaderRequests.ts]] — import-or-re-export: `useWhenLive`; references `useWhenLive`
- [[Reference/Desktop/TypeScript/screens/reader/useReaderVisit|src/screens/reader/useReaderVisit.ts]] — import-or-re-export: `useReadingActivityAllowed`; references `useReadingActivityAllowed`
- [[Reference/Desktop/TypeScript/screens/reader/useReaderWorkbench|src/screens/reader/useReaderWorkbench.ts]] — import-or-re-export: `useListenerHub`; references `useListenerHub`
- [[Reference/Desktop/TypeScript/screens/reader/useReadingProgress|src/screens/reader/useReadingProgress.ts]] — import-or-re-export: `useListenerHub`, `useReadingActivityRef`, `useWindowPaused`; references `useListenerHub`, `useReadingActivityRef`, `useWindowPaused`
- [[Reference/Desktop/TypeScript/screens/reader/useSideBySide|src/screens/reader/useSideBySide.ts]] — import-or-re-export: `useListenerHub`; references `useListenerHub`
- [[Reference/Desktop/TypeScript/screens/workbench/RouteExample|src/screens/workbench/RouteExample.tsx]] — import-or-re-export: `useWhenLive`; references `useWhenLive`
- [[Reference/Desktop/TypeScript/screens/workbench/Workbench|src/screens/workbench/Workbench.tsx]] — import-or-re-export: `useWindowPaused`; references `useWindowPaused`
- [[Reference/Desktop/TypeScript/screens/workbench/useWorkbenchHelp|src/screens/workbench/useWorkbenchHelp.ts]] — import-or-re-export: `useWhenLive`; references `useWhenLive`
- [[Reference/Desktop/TypeScript/screens/workbench/useWorkbenchSession|src/screens/workbench/useWorkbenchSession.ts]] — import-or-re-export: `useWindowPaused`; references `useWindowPaused`

## Dependencies

### Desktop source modules

No local TypeScript/TSX or Rust module dependency was detected.

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/reader/scopeClaims.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/scopeClaims.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/reader/pausedProducers.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/pausedProducers.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/reader/YouTubeWatchPanel.instance.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/YouTubeWatchPanel.instance.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/reader/ReadingPathCard.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/ReadingPathCard.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/desks/windows/SourceWindow.recap.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/desks/windows/SourceWindow.recap.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/desks/windows/SourceWindow.lifecycle.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/desks/windows/SourceWindow.lifecycle.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/desks/DeskShell.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/desks/DeskShell.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/ReaderScreen.discoveredCues.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/ReaderScreen.discoveredCues.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/screens/desks/lifecycle.tsx](../../../../../../../apps/learnloop-tauri/src/screens/desks/lifecycle.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

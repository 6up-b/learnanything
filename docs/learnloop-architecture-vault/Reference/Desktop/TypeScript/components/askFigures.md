---
title: "Desktop module · src/components/askFigures.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.components.askFigures"
language: "TypeScript"
area: "TypeScript/components"
source_path: "apps/learnloop-tauri/src/components/askFigures.tsx"
source_paths:
  - "apps/learnloop-tauri/src/components/askFigures.tsx"
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

# `src/components/askFigures.tsx`

Area: [[Reference/Desktop/TypeScript/components/_area|TypeScript/components]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides the reusable `askFigures` interaction surface used by one or more desktop workflows.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/components/askFigures.tsx](../../../../../../apps/learnloop-tauri/src/components/askFigures.tsx) |
| Source lines | 324 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/components/_area|TypeScript/components]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/components/AskOverlay|src/components/AskOverlay.tsx]] → [[Reference/Desktop/TypeScript/components/askFigures|src/components/askFigures.tsx]]

## Public API

- `export const PANEL_FIGURE_COPY =` — const, line 27
- `export function clearPanelFigures(): void` — function, line 84
- `export function panelFiguresOn(target: AskTarget | null): boolean` — function, line 90
- `export function figureHostRef(target: AskTarget): FigureHostRef | null` — function, line 97
- `export function figureCostLine(target: AskTarget, cold: boolean, converted: boolean): string` — function, line 106
- `export interface PanelFigureLine` — interface, line 111
- `export interface PanelFigureEvent` — interface, line 121
- `export function usePanelFigures(target: AskTarget | null,` — function, line 144
- `export type PanelFigures = ReturnType<typeof usePanelFigures>` — type, line 290
- `export function PanelFigureThreadLine(` — function, line 295

## Internal implementation anchors

- `const FIGURE_POLL_MS = 400` — const, line 47
- `interface PanelFigureHostState` — interface, line 54
- `const NO_FIGURES: PanelFigureHostState =` — const, line 62
- `const panelFigureHosts = new Map<string, PanelFigureHostState>()` — const, line 63
- `const panelFigureListeners = new Set<()` — const, line 64
- `function updateHost(hostKey: string, change: (state: PanelFigureHostState)` — function, line 66
- `function keptTokenOf(hostKey: string):` — function, line 74
- `function subscribeHosts(listener: ()` — function, line 78
- `function sleep(ms: number): Promise<void>` — function, line 129
- `async function settle(start: ()` — function, line 133
- `let job = await start()` — let, line 134
- `const enabled = chooser ? Boolean(target?.practiceItemId) : panelFiguresOn(target)` — const, line 151
- `const hostRef = target ? figureHostRef(target) : null` — const, line 153
- `const hostKey = enabled && hostRef ? `$` — const, line 154
- `const hostState = useSyncExternalStore(subscribeHosts, ()` — const, line 155
- `const setLines = useCallback((change: (list: PanelFigureLine[])` — const, line 157
- `const onEventRef = useRef(onEvent)` — const, line 159
- `const attemptKey = target ? `$` — const, line 161
- `const land = useCallback((key: string, result: FigureBuildResultDto | null, host: string)` — const, line 163
- `const figure = result?.figure ?? null` — const, line 165
- `const help = result?.help ?? null` — const, line 166
- `const shown = figure !== null && figure.shown` — const, line 167
- `const send = useCallback(async (goal: string)` — const, line 179
- `const words = goal.trim()` — const, line 180
- `const hostRef = figureHostRef(target)` — const, line 182
- `const host = hostKey` — const, line 185
- `const key = `fig:$` — const, line 186
- `let takeStepToken: string | null = null` — let, line 189
- `const keptToken = keptTokenOf(host)` — const, line 192
- `const step = await api.figureTakeStep(` — const, line 196
- `const kept =` — const, line 201
- `const result = await settle(()` — const, line 208
- `const open = useCallback(async (figureId: string, label: string)` — const, line 216
- `const hostRef = figureHostRef(target)` — const, line 218
- `const host = hostKey` — const, line 220
- `const key = `open:$` — const, line 221
- `const keptToken = keptTokenOf(host)` — const, line 225
- `const opened = await api.figureOpen(` — const, line 226
- `const contract: FiguresContract = useMemo(()` — const, line 233
- `const ctl: FiguresCtl = useMemo(()` — const, line 234
- `const patch = (found:` — const, line 235
- `const key = lines.find((line)` — const, line 249
- `const host = hostKey` — const, line 251
- `const hostRef = target ? figureHostRef(target) : null` — const, line 255
- `const keptToken = keptTokenOf(host)` — const, line 256
- `const takeStepToken = keptToken?.key === attemptKey ? keptToken.token : null` — const, line 257
- `const found = await api.readerFigurePredict(` — const, line 263
- `const found = await api.readerFigureExplain(` — const, line 269
- `const dismiss = (key: string)` — const, line 286
- `const link =` — const, line 292
- `const counted = line.help?.countsAsHint === true` — const, line 297

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/components/AskOverlay|src/components/AskOverlay.tsx]] — import-or-re-export: `PANEL_FIGURE_COPY`, `PanelFigureEvent`, `PanelFigureThreadLine`, `figureCostLine`, `usePanelFigures`; references `PANEL_FIGURE_COPY`, `PanelFigureEvent`, `PanelFigureThreadLine`, `figureCostLine`, `usePanelFigures`
- [[Reference/Desktop/TypeScript/screens/PracticeScreen|src/screens/PracticeScreen.tsx]] — import-or-re-export: `PANEL_FIGURE_COPY`, `PanelFigureEvent`; references `PANEL_FIGURE_COPY`, `PanelFigureEvent`
- [[Reference/Desktop/TypeScript/screens/practice/HintPanel|src/screens/practice/HintPanel.tsx]] — import-or-re-export: `PANEL_FIGURE_COPY`, `PanelFigureEvent`, `PanelFigureThreadLine`, `usePanelFigures`; references `PANEL_FIGURE_COPY`, `PanelFigureEvent`, `PanelFigureThreadLine`, `usePanelFigures`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `FigureBuildResultDto`, `FigureHelpDto`, `FigureHostRef`, `FigureViewDto`, `LibraryJobDto`
- [[Reference/Desktop/TypeScript/app/algoConfig|src/app/algoConfig.ts]] — import-or-re-export; imports `algoConfig`
- [[Reference/Desktop/TypeScript/components/AskOverlay|src/components/AskOverlay.tsx]] — import-or-re-export; imports `AskTarget`
- [[Reference/Desktop/TypeScript/components/term|src/components/term.tsx]] — import-or-re-export; imports `COLOR`, `FONT_MONO`
- [[Reference/Desktop/TypeScript/errors|src/errors.ts]] — import-or-re-export; imports `errorMessage`
- [[Reference/Desktop/TypeScript/screens/reader/figures/FigureInline|src/screens/reader/figures/FigureInline.tsx]] — import-or-re-export; imports `FigureInline`
- [[Reference/Desktop/TypeScript/screens/reader/figures/showMe|src/screens/reader/figures/showMe.ts]] — import-or-re-export; imports `showMeSourceLine`
- [[Reference/Desktop/TypeScript/screens/reader/figures/useFigures|src/screens/reader/figures/useFigures.ts]] — import-or-re-export; imports `FiguresContract`, `FiguresCtl`, `figurePlacementKey`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/components/askFigures.test.tsx](../../../../../../apps/learnloop-tauri/src/components/askFigures.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/components/askFigures.tsx](../../../../../../apps/learnloop-tauri/src/components/askFigures.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

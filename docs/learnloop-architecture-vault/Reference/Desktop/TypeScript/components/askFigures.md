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
| Source lines | 328 |
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
- `export interface PanelFigureEvent` — interface, line 126
- `export function usePanelFigures(target: AskTarget | null,` — function, line 149
- `export type PanelFigures = ReturnType<typeof usePanelFigures>` — type, line 294
- `export function PanelFigureThreadLine(` — function, line 299

## Internal implementation anchors

- `const FIGURE_POLL_MS = 400` — const, line 47
- `interface PanelFigureHostState` — interface, line 54
- `const NO_FIGURES: PanelFigureHostState =` — const, line 62
- `const panelFigureHosts = new Map<string, PanelFigureHostState>()` — const, line 63
- `const panelFigureListeners = new Set<()` — const, line 64
- `function updateHost(hostKey: string, change: (state: PanelFigureHostState)` — function, line 66
- `function keptTokenOf(hostKey: string):` — function, line 74
- `function subscribeHosts(listener: ()` — function, line 78
- `function quickOnly(figure: FigureViewDto | null): FigureViewDto | null` — function, line 121
- `function sleep(ms: number): Promise<void>` — function, line 134
- `async function settle(start: ()` — function, line 138
- `let job = await start()` — let, line 139
- `const enabled = chooser ? Boolean(target?.practiceItemId) : panelFiguresOn(target)` — const, line 156
- `const hostRef = target ? figureHostRef(target) : null` — const, line 158
- `const hostKey = enabled && hostRef ? `$` — const, line 159
- `const hostState = useSyncExternalStore(subscribeHosts, ()` — const, line 160
- `const setLines = useCallback((change: (list: PanelFigureLine[])` — const, line 162
- `const onEventRef = useRef(onEvent)` — const, line 164
- `const attemptKey = target ? `$` — const, line 166
- `const land = useCallback((key: string, result: FigureBuildResultDto | null, host: string)` — const, line 168
- `const figure = quickOnly(result?.figure ?? null)` — const, line 169
- `const help = result?.help ?? null` — const, line 170
- `const shown = figure !== null && (figure.verification === "verified" || figure.verification === "illustrative")` — const, line 171
- `const send = useCallback(async (goal: string)` — const, line 183
- `const words = goal.trim()` — const, line 184
- `const hostRef = figureHostRef(target)` — const, line 186
- `const host = hostKey` — const, line 189
- `const key = `fig:$` — const, line 190
- `let takeStepToken: string | null = null` — let, line 193
- `const keptToken = keptTokenOf(host)` — const, line 196
- `const step = await api.figureTakeStep(` — const, line 200
- `const kept =` — const, line 205
- `const result = await settle(()` — const, line 212
- `const open = useCallback(async (figureId: string, label: string)` — const, line 220
- `const hostRef = figureHostRef(target)` — const, line 222
- `const host = hostKey` — const, line 224
- `const key = `open:$` — const, line 225
- `const keptToken = keptTokenOf(host)` — const, line 229
- `const opened = await api.figureOpen(` — const, line 230
- `const contract: FiguresContract = useMemo(()` — const, line 237
- `const ctl: FiguresCtl = useMemo(()` — const, line 238
- `const patch = (found:` — const, line 239
- `const key = lines.find((line)` — const, line 253
- `const host = hostKey` — const, line 255
- `const hostRef = target ? figureHostRef(target) : null` — const, line 259
- `const keptToken = keptTokenOf(host)` — const, line 260
- `const takeStepToken = keptToken?.key === attemptKey ? keptToken.token : null` — const, line 261
- `const found = await api.readerFigurePredict(` — const, line 267
- `const found = await api.readerFigureExplain(` — const, line 273
- `const dismiss = (key: string)` — const, line 290
- `const link =` — const, line 296
- `const counted = line.help?.countsAsHint === true` — const, line 301

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

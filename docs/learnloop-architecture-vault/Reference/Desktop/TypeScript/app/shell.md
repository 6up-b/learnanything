---
title: "Desktop module · src/app/shell.ts"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.app.shell"
language: "TypeScript"
area: "TypeScript/app"
source_path: "apps/learnloop-tauri/src/app/shell.ts"
source_paths:
  - "apps/learnloop-tauri/src/app/shell.ts"
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

# `src/app/shell.ts`

Area: [[Reference/Desktop/TypeScript/app/_area|TypeScript/app]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides `ShellMode`, `shellMode`, `simpleShell`, `Place` and related exports within the desktop's TypeScript/app ownership area.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/app/shell.ts](../../../../../../apps/learnloop-tauri/src/app/shell.ts) |
| Source lines | 173 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/app/_area|TypeScript/app]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/app/shell|src/app/shell.ts]]

## Public API

- `export type ShellMode = "simple" | "classic"` — type, line 15
- `export function shellMode(): ShellMode` — function, line 18
- `export function simpleShell(): boolean` — function, line 24
- `export type Place = "today" | "library" | "reader" | "progress"` — type, line 30
- `export const PLACES: ReadonlyArray<` — const, line 32
- `export function placeOfTab(tab: TopTab): Place | "underhood" | null` — function, line 42
- `export function tabForPlace(place: Place, hasSession: boolean): TopTab` — function, line 54
- `export type UthToolId = | "ingest" | "proposals" | "registry" | "graph-editor" | "analyst" | "mistakes" | "calibration" | "maintain" | "data" | "files" | "inspector" | "spend"` — type, line 62
- `export interface UthTool` — interface, line 76
- `export const UTH_TOOLS: ReadonlyArray<UthTool> = [` — const, line 86
- `export function visibleUthTools(): UthTool[]` — function, line 102
- `export function isTabTool(tool: UthToolId): tool is "ingest" | "proposals" | "registry" | "maintain"` — function, line 109
- `export function uthTool(id: UthToolId): UthTool` — function, line 113
- `export function uthToolOfTab(tab: TopTab, current: UthToolId): UthToolId` — function, line 119
- `export function rememberPlace(place: Place | "underhood"): void` — function, line 146
- `export function rememberedPlace(): Place | "underhood" | null` — function, line 150
- `export function rememberTool(tool: UthToolId): void` — function, line 155
- `export function rememberedTool(): UthToolId` — function, line 159
- `export function rememberBook(vaultRoot: string, sourceId: string | null): void` — function, line 166
- `export function rememberedBook(vaultRoot: string): string | null` — function, line 170

## Internal implementation anchors

- `const UNDER_THE_HOOD_TABS: ReadonlySet<TopTab> = new Set<TopTab>(["ingest", "proposals", "registry", "maintain", "underhood"])` — const, line 39
- `const TAB_TOOLS: ReadonlySet<UthToolId> = new Set<UthToolId>(["ingest", "proposals", "registry", "maintain"])` — const, line 107
- `const PLACE_KEY = "learnloop.place"` — const, line 126
- `const TOOL_KEY = "learnloop.underhood.tool"` — const, line 127
- `const BOOK_KEY_PREFIX = "learnloop.reader.book:"` — const, line 128
- `function read(key: string): string | null` — function, line 130
- `function write(key: string, value: string): void` — function, line 138
- `const value = read(PLACE_KEY)` — const, line 151
- `const value = read(TOOL_KEY)` — const, line 160
- `const tool = visibleUthTools().find((candidate)` — const, line 161
- `const value = read(BOOK_KEY_PREFIX + vaultRoot)` — const, line 171

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] — import-or-re-export: `Place`, `ShellMode`, `UthToolId`, `isTabTool`, `placeOfTab`, `rememberBook`, `rememberPlace`, `rememberTool`, `rememberedBook`, `rememberedPlace`, `rememberedTool`, `tabForPlace`, `uthTool`, `uthToolOfTab`, `visibleUthTools`; references `Place`, `ShellMode`, `UthToolId`, `isTabTool`, `placeOfTab`, `rememberBook`, `rememberPlace`, `rememberTool`, `rememberedBook`, `rememberedPlace`, `rememberedTool`, `tabForPlace`, `uthTool`, `uthToolOfTab`, `visibleUthTools`
- [[Reference/Desktop/TypeScript/app/keymap|src/app/keymap.ts]] — import-or-re-export: `Place`, `ShellMode`, `UthToolId`; references `Place`, `ShellMode`, `UthToolId`
- [[Reference/Desktop/TypeScript/components/CommandPalette|src/components/CommandPalette.tsx]] — import-or-re-export: `ShellMode`; references `ShellMode`
- [[Reference/Desktop/TypeScript/components/KeyboardHelp|src/components/KeyboardHelp.tsx]] — import-or-re-export: `ShellMode`; references `ShellMode`
- [[Reference/Desktop/TypeScript/components/OutlineAndPlan|src/components/OutlineAndPlan.tsx]] — import-or-re-export: `simpleShell`; references `simpleShell`
- [[Reference/Desktop/TypeScript/components/ShellNav|src/components/ShellNav.tsx]] — import-or-re-export: `PLACES`, `Place`; references `PLACES`, `Place`
- [[Reference/Desktop/TypeScript/screens/KnowledgeMapScreen|src/screens/KnowledgeMapScreen.tsx]] — import-or-re-export: `simpleShell`; references `simpleShell`
- [[Reference/Desktop/TypeScript/screens/LibraryScreen|src/screens/LibraryScreen.tsx]] — import-or-re-export: `ShellMode`, `shellMode`, `simpleShell`; references `ShellMode`, `shellMode`, `simpleShell`
- [[Reference/Desktop/TypeScript/screens/ProposalsScreen|src/screens/ProposalsScreen.tsx]] — import-or-re-export: `simpleShell`; references `simpleShell`
- [[Reference/Desktop/TypeScript/screens/SqliteBrowser|src/screens/SqliteBrowser.tsx]] — import-or-re-export: `simpleShell`; references `simpleShell`
- [[Reference/Desktop/TypeScript/screens/UnderTheHoodScreen|src/screens/UnderTheHoodScreen.tsx]] — import-or-re-export: `UthToolId`, `uthTool`, `visibleUthTools`; references `UthToolId`, `uthTool`, `visibleUthTools`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/app/algoConfig|src/app/algoConfig.ts]] — import-or-re-export; imports `algoConfig`
- [[Reference/Desktop/TypeScript/components/ui|src/components/ui.tsx]] — import-or-re-export; imports `TopTab`

### Assets, platform, and third-party dependencies

No explicit asset, standard-library, package, or crate dependency was detected.

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/app/shell.test.ts](../../../../../../apps/learnloop-tauri/src/app/shell.test.ts) — vitest test: imports and executes this module under jsdom (`npm test`).

## Modification guidance

- Change this source at its stated ownership boundary, then check every inbound consumer and outbound dependency listed above.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/app/shell.ts](../../../../../../apps/learnloop-tauri/src/app/shell.ts) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

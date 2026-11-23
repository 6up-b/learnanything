---
title: "Desktop module · src/components/useSourceFileDrop.ts"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.components.useSourceFileDrop"
language: "TypeScript"
area: "TypeScript/components"
source_path: "apps/learnloop-tauri/src/components/useSourceFileDrop.ts"
source_paths:
  - "apps/learnloop-tauri/src/components/useSourceFileDrop.ts"
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

# `src/components/useSourceFileDrop.ts`

Area: [[Reference/Desktop/TypeScript/components/_area|TypeScript/components]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides shared `useSourceFileDrop` state or utility behavior for desktop components.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/components/useSourceFileDrop.ts](../../../../../../apps/learnloop-tauri/src/components/useSourceFileDrop.ts) |
| Source lines | 120 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/components/_area|TypeScript/components]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/components/useSourceFileDrop|src/components/useSourceFileDrop.ts]]

## Public API

- `export function isSupportedSourceFile(path: string): boolean` — function, line 49
- `export async function pickSourceFile(): Promise<string | null>` — function, line 62
- `export async function pickSourceFiles(): Promise<string[]>` — function, line 77
- `export function useSourceFileDrop(` — function, line 91

## Internal implementation anchors

- `const SOURCE_EXTENSIONS = SOURCE_FILE_EXTENSIONS` — const, line 8
- `type Subscriber =` — type, line 10
- `const subscribers = new Map<symbol, Subscriber>()` — const, line 17
- `let unlistenPromise: Promise<UnlistenFn> | null = null` — let, line 18
- `function activeSubscriber(): Subscriber | null` — function, line 20
- `function setDragging(active: Subscriber | null, dragging: boolean)` — function, line 26
- `function ensureNativeListener()` — function, line 32
- `const active = activeSubscriber()` — const, line 35
- `const supported = event.payload.paths.filter(isSupportedSourceFile)` — const, line 43
- `const lower = path.toLowerCase()` — const, line 50
- `const selected = await openDialog(` — const, line 63
- `const selected = await openDialog(` — const, line 78
- `const callbackRef = useRef(onDrop)` — const, line 101
- `const id = Symbol("source-file-drop")` — const, line 105

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] — import-or-re-export: `pickSourceFiles`, `useSourceFileDrop`; references `pickSourceFiles`, `useSourceFileDrop`
- [[Reference/Desktop/TypeScript/components/AddSource|src/components/AddSource.tsx]] — import-or-re-export: `pickSourceFiles`; references `pickSourceFiles`
- [[Reference/Desktop/TypeScript/components/NewVaultWizard|src/components/NewVaultWizard.tsx]] — import-or-re-export: `pickSourceFile`, `useSourceFileDrop`; references `pickSourceFile`, `useSourceFileDrop`
- [[Reference/Desktop/TypeScript/components/QuickAddDialog|src/components/QuickAddDialog.tsx]] — import-or-re-export: `pickSourceFile`, `useSourceFileDrop`; references `pickSourceFile`, `useSourceFileDrop`
- [[Reference/Desktop/TypeScript/screens/IngestScreen|src/screens/IngestScreen.tsx]] — import-or-re-export: `useSourceFileDrop`; references `useSourceFileDrop`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/sourceKinds|src/api/sourceKinds.ts]] — import-or-re-export; imports `SOURCE_FILE_EXTENSIONS`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `@tauri-apps/api/event`, `@tauri-apps/api/webview`, `@tauri-apps/plugin-dialog`, `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Import Canonical Sources|Import Canonical Sources]] — owns import sequencing.
- [[Architecture/Content Pipeline#Durable checkpoint ladder|content checkpoint ladder]] — owns pipeline persistence semantics.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/api/sourceKinds.test.ts](../../../../../../apps/learnloop-tauri/src/api/sourceKinds.test.ts) — vitest test: imports and executes this module under jsdom (`npm test`).
- [tests/test_sidecar_ingest_m3.py](../../../../../../tests/test_sidecar_ingest_m3.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_source_ingestion.py](../../../../../../tests/test_source_ingestion.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_ingest_runner.py](../../../../../../tests/test_ingest_runner.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_init.py](../../../../../../tests/test_init.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/components/useSourceFileDrop.ts](../../../../../../apps/learnloop-tauri/src/components/useSourceFileDrop.ts) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

---
title: "Desktop module · src/screens/LibraryPlace.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.LibraryPlace"
language: "TypeScript"
area: "TypeScript/screens"
source_path: "apps/learnloop-tauri/src/screens/LibraryPlace.tsx"
source_paths:
  - "apps/learnloop-tauri/src/screens/LibraryPlace.tsx"
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

# `src/screens/LibraryPlace.tsx`

Area: [[Reference/Desktop/TypeScript/screens/_area|TypeScript/screens]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Implements the `LibraryPlace` routed desktop screen and coordinates its learner-facing workflow state.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/LibraryPlace.tsx](../../../../../../apps/learnloop-tauri/src/screens/LibraryPlace.tsx) |
| Source lines | 268 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/_area|TypeScript/screens]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/LibraryPlace|src/screens/LibraryPlace.tsx]]

## Public API

- `export type LibraryView = "books" | "files"` — type, line 20
- `export function LibraryPlace(` — function, line 62

## Internal implementation anchors

- `const LibraryScreen = lazy(()` — const, line 16
- `const POLL_MS = 3000` — const, line 18
- `function tabStyle(active: boolean): CSSProperties` — function, line 22
- `const confirmButton: CSSProperties =` — const, line 35
- `const cancelButton: CSSProperties =` — const, line 46
- `function busyShelf(sources: SourceLibraryCard[] | undefined, pending: PendingAddDto[] | undefined): boolean` — function, line 58
- `const library = useCachedQuery(["get_source_library"], ()` — const, line 100
- `const sources = library.data?.sources` — const, line 102
- `const pending = library.data?.pending ?? []` — const, line 103
- `const refetchRef = useRef(library.refetch)` — const, line 104
- `const working = busyShelf(sources, pending) || openWhenReady !== null` — const, line 108
- `const timer = window.setInterval(()` — const, line 111
- `const card = sources.find((entry)` — const, line 117
- `const run = useCallback(async (input:` — const, line 134
- `const result = await api.sourceAction(input)` — const, line 144
- `const onAction = useCallback( (kind: SourceActionKind, card: SourceLibraryCard)` — const, line 155
- `const chosen = confirming` — const, line 214
- `const binding = chosen.confirmation.proposalHash ?` — const, line 219

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] — import-or-re-export: `LibraryPlace`, `LibraryView`; references `LibraryPlace`, `LibraryView`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `AiConnectionDto`, `PendingAddDto`, `SourceActionConfirmationDto`, `SourceActionKind`, `SourceLibraryCard`
- [[Reference/Desktop/TypeScript/api/queryTags|src/api/queryTags.ts]] — import-or-re-export; imports `TAG`
- [[Reference/Desktop/TypeScript/api/useCachedQuery|src/api/useCachedQuery.ts]] — import-or-re-export; imports `useCachedQuery`
- [[Reference/Desktop/TypeScript/components/AddSource|src/components/AddSource.tsx]] — import-or-re-export; imports `AddOptions`
- [[Reference/Desktop/TypeScript/components/BookShelf|src/components/BookShelf.tsx]] — import-or-re-export; imports `BookShelf`
- [[Reference/Desktop/TypeScript/components/term|src/components/term.tsx]] — import-or-re-export; imports `COLOR`, `FONT_MONO`
- [[Reference/Desktop/TypeScript/copy/ingestErrors|src/copy/ingestErrors.ts]] — import-or-re-export; imports `plainError`
- [[Reference/Desktop/TypeScript/screens/LibraryScreen|src/screens/LibraryScreen.tsx]] — dynamic import

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Import Canonical Sources|Import Canonical Sources]] — owns import sequencing.
- [[Architecture/Content Pipeline#Durable checkpoint ladder|content checkpoint ladder]] — owns pipeline persistence semantics.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/LibraryPlace.reread.test.tsx](../../../../../../apps/learnloop-tauri/src/screens/LibraryPlace.reread.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/screens/LibraryPlace.tsx](../../../../../../apps/learnloop-tauri/src/screens/LibraryPlace.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

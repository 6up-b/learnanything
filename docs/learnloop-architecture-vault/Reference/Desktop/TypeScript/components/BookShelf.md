---
title: "Desktop module · src/components/BookShelf.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.components.BookShelf"
language: "TypeScript"
area: "TypeScript/components"
source_path: "apps/learnloop-tauri/src/components/BookShelf.tsx"
source_paths:
  - "apps/learnloop-tauri/src/components/BookShelf.tsx"
source_commit: "8cbd71da082d024e480a31b888ef7c2d3be10dda"
source_commit_timestamp: "2026-10-13T10:33:06-04:00"
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

# `src/components/BookShelf.tsx`

Area: [[Reference/Desktop/TypeScript/components/_area|TypeScript/components]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides the reusable `BookShelf` interaction surface used by one or more desktop workflows.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/components/BookShelf.tsx](../../../../../../apps/learnloop-tauri/src/components/BookShelf.tsx) |
| Source lines | 125 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/components/_area|TypeScript/components]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `8cbd71da082d024e480a31b888ef7c2d3be10dda` |
| Commit timestamp | `2026-10-13T10:33:06-04:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/LibraryPlace|src/screens/LibraryPlace.tsx]] → [[Reference/Desktop/TypeScript/components/BookShelf|src/components/BookShelf.tsx]]

## Public API

- `export function BookShelf(` — function, line 11

## Internal implementation anchors

- `const empty = sources.length === 0 && pending.length === 0` — const, line 66
- `const aiLine = aiConnection && aiConnection.needs === "connect" ? ( <div style=` — const, line 67

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/LibraryPlace|src/screens/LibraryPlace.tsx]] — import-or-re-export: `BookShelf`; references `BookShelf`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `AiConnectionDto`, `PendingAddDto`, `SourceActionKind`, `SourceLibraryCard`
- [[Reference/Desktop/TypeScript/components/AddSource|src/components/AddSource.tsx]] — import-or-re-export; imports `AddOptions`, `AddSourceBox`
- [[Reference/Desktop/TypeScript/components/BookCard|src/components/BookCard.tsx]] — import-or-re-export; imports `BookCard`, `PendingCard`
- [[Reference/Desktop/TypeScript/components/term|src/components/term.tsx]] — import-or-re-export; imports `COLOR`, `FONT_MONO`

### Assets, platform, and third-party dependencies

No explicit asset, standard-library, package, or crate dependency was detected.

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/copy/denyList.test.tsx](../../../../../../apps/learnloop-tauri/src/copy/denyList.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/components/BookShelf.test.tsx](../../../../../../apps/learnloop-tauri/src/components/BookShelf.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/components/BookShelf.tsx](../../../../../../apps/learnloop-tauri/src/components/BookShelf.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

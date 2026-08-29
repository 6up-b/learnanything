---
title: "Desktop module · src/components/AsciiLoadingBar.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.components.AsciiLoadingBar"
language: "TypeScript"
area: "TypeScript/components"
source_path: "apps/learnloop-tauri/src/components/AsciiLoadingBar.tsx"
source_paths:
  - "apps/learnloop-tauri/src/components/AsciiLoadingBar.tsx"
source_commit: "02c3e6e10f5ca37e16cef05657ee693b33502fb7"
source_commit_timestamp: "2026-07-21T13:26:14-04:00"
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

# `src/components/AsciiLoadingBar.tsx`

Area: [[Reference/Desktop/TypeScript/components/_area|TypeScript/components]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides the reusable `AsciiLoadingBar` interaction surface used by one or more desktop workflows.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/components/AsciiLoadingBar.tsx](../../../../../../apps/learnloop-tauri/src/components/AsciiLoadingBar.tsx) |
| Source lines | 42 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/components/_area|TypeScript/components]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `02c3e6e10f5ca37e16cef05657ee693b33502fb7` |
| Commit timestamp | `2026-07-21T13:26:14-04:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/components/QuickAddDialog|src/components/QuickAddDialog.tsx]] → [[Reference/Desktop/TypeScript/components/AsciiLoadingBar|src/components/AsciiLoadingBar.tsx]]

## Public API

- `export function AsciiLoadingBar(` — function, line 4

## Internal implementation anchors

- `const id = window.setInterval(()` — const, line 8
- `const span = Math.max(2, width * 2 - 2)` — const, line 12
- `const offset = frame % span` — const, line 13
- `const position = offset < width ? offset : span - offset` — const, line 14
- `const movingRight = offset < width` — const, line 15
- `const cells = Array.from(` — const, line 16
- `const trail = position + (movingRight ? -distance : distance)` — const, line 19

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/components/QuickAddDialog|src/components/QuickAddDialog.tsx]] — import-or-re-export: `AsciiLoadingBar`; references `AsciiLoadingBar`
- [[Reference/Desktop/TypeScript/screens/IngestScreen|src/screens/IngestScreen.tsx]] — import-or-re-export: `AsciiLoadingBar`; references `AsciiLoadingBar`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/components/term|src/components/term.tsx]] — import-or-re-export; imports `COLOR`, `FONT_MONO`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- No repository test directly names this source path or a uniquely owned export. `npm run typecheck` and `npm run frontend:build` are the executable frontend gates; add a focused test when changing behavior.

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/components/AsciiLoadingBar.tsx](../../../../../../apps/learnloop-tauri/src/components/AsciiLoadingBar.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

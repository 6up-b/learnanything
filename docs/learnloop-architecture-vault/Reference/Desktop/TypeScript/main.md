---
title: "Desktop module · src/main.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.main"
language: "TypeScript"
area: "TypeScript"
source_path: "apps/learnloop-tauri/src/main.tsx"
source_paths:
  - "apps/learnloop-tauri/src/main.tsx"
source_commit: "8fd580b328a77be6448ea1eca544298b4379ccc5"
source_commit_timestamp: "2026-07-22T21:50:36-05:00"
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

# `src/main.tsx`

Area: [[Reference/Desktop/TypeScript/_area|TypeScript]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Bootstraps React, applies the persisted palette before first paint, and mounts the desktop application shell.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/main.tsx](../../../../../apps/learnloop-tauri/src/main.tsx) |
| Source lines | 19 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/_area|TypeScript]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `8fd580b328a77be6448ea1eca544298b4379ccc5` |
| Commit timestamp | `2026-07-22T21:50:36-05:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]]

## Public API

No exported declaration; this file executes as the Vite renderer entry point.

## Internal implementation anchors

- `const storedPalette = localStorage.getItem("learnloop.palette")` — const, line 9

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [apps/learnloop-tauri/index.html](../../../../../apps/learnloop-tauri/index.html) — Vite HTML entry loads `/src/main.tsx`.

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] — import-or-re-export; imports `App`

### Assets, platform, and third-party dependencies

- Local asset: [apps/learnloop-tauri/src/styles/app.css](../../../../../apps/learnloop-tauri/src/styles/app.css)
- Local asset: [apps/learnloop-tauri/src/styles/palettes.css](../../../../../apps/learnloop-tauri/src/styles/palettes.css)
- Imported packages/crates: `react`, `react-dom/client`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Architecture/Architecture Overview#Runtime composition|runtime composition]] — shows this entry point in the whole process graph.
- [[Workflows/Initialize a Vault|Initialize a Vault]] — owns first-run behavior.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- No repository test directly names this source path or a uniquely owned export. `npm run typecheck` and `npm run frontend:build` are the executable frontend gates; add a focused test when changing behavior.

## Modification guidance

- Change this source at its stated ownership boundary, then check every inbound consumer and outbound dependency listed above.
- Run `npm run typecheck` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/main.tsx](../../../../../apps/learnloop-tauri/src/main.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

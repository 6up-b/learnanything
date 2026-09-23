---
title: "Desktop module · src/api/queryTags.ts"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.api.queryTags"
language: "TypeScript"
area: "TypeScript/api"
source_path: "apps/learnloop-tauri/src/api/queryTags.ts"
source_paths:
  - "apps/learnloop-tauri/src/api/queryTags.ts"
source_commit: "ad991418ef3cb163828f9b1cf1ad9da9cce7549a"
source_commit_timestamp: "2026-09-03T10:55:39-07:00"
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

# `src/api/queryTags.ts`

Area: [[Reference/Desktop/TypeScript/api/_area|TypeScript/api]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides `TAG`, `KnownTag`, `READER_PREFIX`, `readerTag` within the desktop's TypeScript/api ownership area.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/api/queryTags.ts](../../../../../../apps/learnloop-tauri/src/api/queryTags.ts) |
| Source lines | 44 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/api/_area|TypeScript/api]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `ad991418ef3cb163828f9b1cf1ad9da9cce7549a` |
| Commit timestamp | `2026-09-03T10:55:39-07:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] → [[Reference/Desktop/TypeScript/api/queryTags|src/api/queryTags.ts]]

## Public API

- `export const TAG =` — const, line 10
- `export type KnownTag = (typeof TAG)[keyof typeof TAG]` — type, line 37
- `export const READER_PREFIX = "reader:"` — const, line 40
- `export function readerTag(sourceId: string): string` — function, line 42

## Internal implementation anchors

No non-exported declaration anchor was detected by the static extractor.

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export: `READER_PREFIX`, `TAG`; references `READER_PREFIX`, `TAG`
- [[Reference/Desktop/TypeScript/components/SourceLibrarySidebar|src/components/SourceLibrarySidebar.tsx]] — import-or-re-export: `TAG`; references `TAG`
- [[Reference/Desktop/TypeScript/queueEvents|src/queueEvents.ts]] — import-or-re-export: `TAG`; references `TAG`
- [[Reference/Desktop/TypeScript/screens/GraphScreen|src/screens/GraphScreen.tsx]] — import-or-re-export: `TAG`; references `TAG`
- [[Reference/Desktop/TypeScript/screens/IngestScreen|src/screens/IngestScreen.tsx]] — import-or-re-export: `TAG`; references `TAG`
- [[Reference/Desktop/TypeScript/screens/KnowledgeMapScreen|src/screens/KnowledgeMapScreen.tsx]] — import-or-re-export: `TAG`; references `TAG`
- [[Reference/Desktop/TypeScript/screens/LibraryScreen|src/screens/LibraryScreen.tsx]] — import-or-re-export: `TAG`; references `TAG`
- [[Reference/Desktop/TypeScript/screens/MaintenanceScreen|src/screens/MaintenanceScreen.tsx]] — import-or-re-export: `TAG`; references `TAG`
- [[Reference/Desktop/TypeScript/screens/ProposalsScreen|src/screens/ProposalsScreen.tsx]] — import-or-re-export: `TAG`; references `TAG`
- [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]] — import-or-re-export: `TAG`, `readerTag`; references `TAG`, `readerTag`
- [[Reference/Desktop/TypeScript/screens/RegistryReviewScreen|src/screens/RegistryReviewScreen.tsx]] — import-or-re-export: `TAG`; references `TAG`
- [[Reference/Desktop/TypeScript/screens/SettingsScreen|src/screens/SettingsScreen.tsx]] — import-or-re-export: `TAG`; references `TAG`
- [[Reference/Desktop/TypeScript/screens/StartScreen|src/screens/StartScreen.tsx]] — import-or-re-export: `TAG`; references `TAG`
- [[Reference/Desktop/TypeScript/screens/TodayScreen|src/screens/TodayScreen.tsx]] — import-or-re-export: `TAG`; references `TAG`

## Dependencies

### Desktop source modules

No local TypeScript/TSX or Rust module dependency was detected.

### Assets, platform, and third-party dependencies

No explicit asset, standard-library, package, or crate dependency was detected.

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Architecture/Adapter Architecture#Sidecar structure|sidecar structure]] — owns the four-layer RPC contract.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- No repository test directly names this source path or a uniquely owned export. `npm run typecheck`, `npm test` and `npm run frontend:build` are the executable frontend gates; add a focused test when changing behavior.

## Modification guidance

- Add or change an RPC in all four layers: DTO, client facade, Rust command/registration, and Python sidecar handler/registry.
- Preserve camelCase wire names and typed error behavior; exercise `tests/test_desktop_rpc_contract.py` plus the feature's sidecar tests.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/api/queryTags.ts](../../../../../../apps/learnloop-tauri/src/api/queryTags.ts) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

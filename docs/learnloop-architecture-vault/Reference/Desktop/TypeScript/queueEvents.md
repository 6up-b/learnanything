---
title: "Desktop module · src/queueEvents.ts"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.queueEvents"
language: "TypeScript"
area: "TypeScript"
source_path: "apps/learnloop-tauri/src/queueEvents.ts"
source_paths:
  - "apps/learnloop-tauri/src/queueEvents.ts"
source_commit: "388f3ce6b9e89c35532881182dabb2d08272d445"
source_commit_timestamp: "2026-07-24T09:24:46-04:00"
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

# `src/queueEvents.ts`

Area: [[Reference/Desktop/TypeScript/_area|TypeScript]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides the in-window event boundary that tells independent surfaces the practice queue changed.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/queueEvents.ts](../../../../../apps/learnloop-tauri/src/queueEvents.ts) |
| Source lines | 10 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/_area|TypeScript]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `388f3ce6b9e89c35532881182dabb2d08272d445` |
| Commit timestamp | `2026-07-24T09:24:46-04:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/queueEvents|src/queueEvents.ts]]

## Public API

- `export function notifyQueueChanged(): void` — function, line 3
- `export function subscribeQueueChanged(listener: ()` — function, line 7

## Internal implementation anchors

- `const QUEUE_CHANGED_EVENT = "learnloop:queue-changed"` — const, line 1

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] — import-or-re-export: `notifyQueueChanged`, `subscribeQueueChanged`; references `notifyQueueChanged`, `subscribeQueueChanged`
- [[Reference/Desktop/TypeScript/components/AskOverlay|src/components/AskOverlay.tsx]] — import-or-re-export: `notifyQueueChanged`; references `notifyQueueChanged`
- [[Reference/Desktop/TypeScript/components/QuestionQueue|src/components/QuestionQueue.tsx]] — import-or-re-export: `notifyQueueChanged`, `subscribeQueueChanged`; references `notifyQueueChanged`, `subscribeQueueChanged`
- [[Reference/Desktop/TypeScript/screens/ProposalsScreen|src/screens/ProposalsScreen.tsx]] — import-or-re-export: `notifyQueueChanged`; references `notifyQueueChanged`
- [[Reference/Desktop/TypeScript/screens/TodayScreen|src/screens/TodayScreen.tsx]] — import-or-re-export: `notifyQueueChanged`, `subscribeQueueChanged`; references `notifyQueueChanged`, `subscribeQueueChanged`

## Dependencies

### Desktop source modules

No local TypeScript/TSX or Rust module dependency was detected.

### Assets, platform, and third-party dependencies

No explicit asset, standard-library, package, or crate dependency was detected.

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Start a Learning Cycle#Desktop|desktop learning cycle]] — shows the user-facing session path.
- [[Concepts/Learning System#One attempt|one-attempt model]] — owns learning semantics.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [tests/test_desktop_rpc_contract.py](../../../../../tests/test_desktop_rpc_contract.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_sidecar_contract.py](../../../../../tests/test_sidecar_contract.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.

## Modification guidance

- Change this source at its stated ownership boundary, then check every inbound consumer and outbound dependency listed above.
- Run `npm run typecheck` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/queueEvents.ts](../../../../../apps/learnloop-tauri/src/queueEvents.ts) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

---
title: "Desktop module · src/app/sessionMoved.ts"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.app.sessionMoved"
language: "TypeScript"
area: "TypeScript/app"
source_path: "apps/learnloop-tauri/src/app/sessionMoved.ts"
source_paths:
  - "apps/learnloop-tauri/src/app/sessionMoved.ts"
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

# `src/app/sessionMoved.ts`

Area: [[Reference/Desktop/TypeScript/app/_area|TypeScript/app]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides `SessionMoved`, `sessionMovedFrom`, `setSessionMoved`, `useSessionMoved` and related exports within the desktop's TypeScript/app ownership area.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/app/sessionMoved.ts](../../../../../../apps/learnloop-tauri/src/app/sessionMoved.ts) |
| Source lines | 58 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/app/_area|TypeScript/app]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/app/sessionMoved|src/app/sessionMoved.ts]]

## Public API

- `export interface SessionMoved` — interface, line 10
- `export function sessionMovedFrom(snapshot: SessionSnapshot): SessionMoved | null` — function, line 19
- `export function setSessionMoved(next: SessionMoved | null): void` — function, line 29
- `export function useSessionMoved(): SessionMoved | null` — function, line 41
- `export function noteSessionMovedError(error: unknown): void` — function, line 46

## Internal implementation anchors

- `const ownership =` — const, line 20
- `let moved: SessionMoved | null = null` — let, line 26
- `const movedListeners = new Set<()` — const, line 27
- `function subscribeSessionMoved(listener: ()` — function, line 35
- `const candidate = error as` — const, line 47
- `const details = candidate.details ??` — const, line 49
- `const sessionId = details.session_id` — const, line 50

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export: `noteSessionMovedError`; references `noteSessionMovedError`
- [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] — import-or-re-export: `SessionMoved`, `setSessionMoved`, `useSessionMoved`; references `SessionMoved`, `setSessionMoved`, `useSessionMoved`
- [[Reference/Desktop/TypeScript/app/sessionHandoff|src/app/sessionHandoff.ts]] — import-or-re-export: `SessionMoved`; references `SessionMoved`
- [[Reference/Desktop/TypeScript/app/useQueueRevisionPoll|src/app/useQueueRevisionPoll.ts]] — import-or-re-export: `SessionMoved`, `const`, `sessionMovedFrom`, `setSessionMoved`, `useSessionMoved`; references `const`, `sessionMovedFrom`, `setSessionMoved`
- [[Reference/Desktop/TypeScript/components/SessionMovedBanner|src/components/SessionMovedBanner.tsx]] — import-or-re-export: `SessionMoved`; references `SessionMoved`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `SessionSnapshot`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- No repository test directly names this source path or a uniquely owned export. `npm run typecheck`, `npm test` and `npm run frontend:build` are the executable frontend gates; add a focused test when changing behavior.

## Modification guidance

- Change this source at its stated ownership boundary, then check every inbound consumer and outbound dependency listed above.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/app/sessionMoved.ts](../../../../../../apps/learnloop-tauri/src/app/sessionMoved.ts) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

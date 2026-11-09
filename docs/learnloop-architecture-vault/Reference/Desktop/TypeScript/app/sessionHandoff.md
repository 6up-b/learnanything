---
title: "Desktop module · src/app/sessionHandoff.ts"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.app.sessionHandoff"
language: "TypeScript"
area: "TypeScript/app"
source_path: "apps/learnloop-tauri/src/app/sessionHandoff.ts"
source_paths:
  - "apps/learnloop-tauri/src/app/sessionHandoff.ts"
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

# `src/app/sessionHandoff.ts`

Area: [[Reference/Desktop/TypeScript/app/_area|TypeScript/app]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides `ElsewhereChoice`, `ElsewhereQuestion`, `useElsewhereQuestion`, `adoptMovedSession` and related exports within the desktop's TypeScript/app ownership area.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/app/sessionHandoff.ts](../../../../../../apps/learnloop-tauri/src/app/sessionHandoff.ts) |
| Source lines | 82 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/app/_area|TypeScript/app]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/app/sessionHandoff|src/app/sessionHandoff.ts]]

## Public API

- `export type ElsewhereChoice = "adopt" | "fresh" | "cancel"` — type, line 13
- `export interface ElsewhereQuestion` — interface, line 15
- `export function useElsewhereQuestion(): ElsewhereQuestion | null` — function, line 28
- `export function adoptMovedSession(moved: SessionMoved): Promise<SessionSnapshot>` — function, line 58
- `export async function startSessionOrAsk(input: SessionStartInput): Promise<SessionSnapshot | null>` — function, line 67

## Internal implementation anchors

- `let question: ElsewhereQuestion | null = null` — let, line 20
- `const listeners = new Set<()` — const, line 21
- `function setQuestion(next: ElsewhereQuestion | null): void` — function, line 23
- `function ask(details: SessionElsewhereDetails): Promise<ElsewhereChoice>` — function, line 38
- `async function adopted(sessionId: string, expectedGeneration: number): Promise<SessionSnapshot>` — function, line 53
- `let replace = input.replace ?? null` — let, line 68
- `const command = getCommandError(error)` — const, line 73
- `const details = command.details as unknown as SessionElsewhereDetails` — const, line 75
- `const choice = await ask(details)` — const, line 76

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] — import-or-re-export: `adoptMovedSession`, `startSessionOrAsk`; references `adoptMovedSession`, `startSessionOrAsk`
- [[Reference/Desktop/TypeScript/components/SessionElsewherePrompt|src/components/SessionElsewherePrompt.tsx]] — import-or-re-export: `useElsewhereQuestion`; references `useElsewhereQuestion`
- [[Reference/Desktop/TypeScript/screens/StartScreen|src/screens/StartScreen.tsx]] — import-or-re-export: `startSessionOrAsk`; references `startSessionOrAsk`
- [[Reference/Desktop/TypeScript/screens/TodayScreen|src/screens/TodayScreen.tsx]] — import-or-re-export: `startSessionOrAsk`; references `startSessionOrAsk`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `SessionElsewhereDetails`, `SessionSnapshot`, `SessionStartInput`
- [[Reference/Desktop/TypeScript/app/sessionMoved|src/app/sessionMoved.ts]] — import-or-re-export; imports `SessionMoved`
- [[Reference/Desktop/TypeScript/errors|src/errors.ts]] — import-or-re-export; imports `getCommandError`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/app/sessionHandoff.test.tsx](../../../../../../apps/learnloop-tauri/src/app/sessionHandoff.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).

## Modification guidance

- Change this source at its stated ownership boundary, then check every inbound consumer and outbound dependency listed above.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/app/sessionHandoff.ts](../../../../../../apps/learnloop-tauri/src/app/sessionHandoff.ts) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

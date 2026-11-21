---
title: "Desktop module · src/app/aiOk.ts"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.app.aiOk"
language: "TypeScript"
area: "TypeScript/app"
source_path: "apps/learnloop-tauri/src/app/aiOk.ts"
source_paths:
  - "apps/learnloop-tauri/src/app/aiOk.ts"
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

# `src/app/aiOk.ts`

Area: [[Reference/Desktop/TypeScript/app/_area|TypeScript/app]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides `waitForAiOk`, `askForAiOk`, `answerAiOk`, `useAiOkAsked` and related exports within the desktop's TypeScript/app ownership area.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/app/aiOk.ts](../../../../../../apps/learnloop-tauri/src/app/aiOk.ts) |
| Source lines | 59 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/app/_area|TypeScript/app]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/app/aiOk|src/app/aiOk.ts]]

## Public API

- `export function waitForAiOk(): Promise<boolean>` — function, line 27
- `export function askForAiOk(): void` — function, line 35
- `export function answerAiOk(accepted: boolean): void` — function, line 40
- `export function useAiOkAsked(): boolean` — function, line 52
- `export function isWaitingForOk(error: unknown): boolean` — function, line 57

## Internal implementation anchors

- `type Answer = (accepted: boolean)` — type, line 10
- `let asking = false` — let, line 12
- `const waiting: Answer[] = []` — const, line 13
- `const listeners = new Set<()` — const, line 14
- `function notify(): void` — function, line 16
- `function setAsking(next: boolean): void` — function, line 20
- `const answers = waiting.splice(0, waiting.length)` — const, line 41
- `function subscribe(listener: ()` — function, line 46

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export: `isWaitingForOk`, `waitForAiOk`; references `isWaitingForOk`, `waitForAiOk`
- [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] — import-or-re-export: `answerAiOk`, `useAiOkAsked`; references `answerAiOk`, `useAiOkAsked`
- [[Reference/Desktop/TypeScript/components/AddSource|src/components/AddSource.tsx]] — import-or-re-export: `askForAiOk`; references `askForAiOk`
- [[Reference/Desktop/TypeScript/screens/reader/ReadingPathCard|src/screens/reader/ReadingPathCard.tsx]] — import-or-re-export: `askForAiOk`, `useAiOkAsked`; references `askForAiOk`, `useAiOkAsked`

## Dependencies

### Desktop source modules

No local TypeScript/TSX or Rust module dependency was detected.

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/app/aiOk.test.ts](../../../../../../apps/learnloop-tauri/src/app/aiOk.test.ts) — vitest test: imports and executes this module under jsdom (`npm test`).

## Modification guidance

- Change this source at its stated ownership boundary, then check every inbound consumer and outbound dependency listed above.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/app/aiOk.ts](../../../../../../apps/learnloop-tauri/src/app/aiOk.ts) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

---
title: "Desktop module · src/screens/desks/companion/asks.ts"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.desks.companion.asks"
language: "TypeScript"
area: "TypeScript/screens/desks/companion"
source_path: "apps/learnloop-tauri/src/screens/desks/companion/asks.ts"
source_paths:
  - "apps/learnloop-tauri/src/screens/desks/companion/asks.ts"
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

# `src/screens/desks/companion/asks.ts`

Area: [[Reference/Desktop/TypeScript/screens/desks/companion/_area|TypeScript/screens/desks/companion]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides `CompanionApi`, `ExchangeStatus`, `CompanionExchange`, `DeskWritesSettled` and related exports within the desktop's TypeScript/screens/desks/companion ownership area.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/desks/companion/asks.ts](../../../../../../../../apps/learnloop-tauri/src/screens/desks/companion/asks.ts) |
| Source lines | 353 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/desks/companion/_area|TypeScript/screens/desks/companion]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/DeskShell|src/screens/desks/DeskShell.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/companion/asks|src/screens/desks/companion/asks.ts]]

## Public API

- `export interface CompanionApi` — interface, line 14
- `export type ExchangeStatus = "waiting" | "asking" | "answered" | "failed" | "cancelled" | "interrupted"` — type, line 20
- `export interface CompanionExchange` — interface, line 22
- `export type DeskWritesSettled = "saved" | "unsaved"` — type, line 49
- `export interface AskRequest` — interface, line 51
- `export function threadKey(deskId: string | null): string` — function, line 82
- `export class CompanionAsks` — class, line 86
- `export function forgetCompanionAsks(vaultKey: string, owner: object): void` — function, line 334
- `export function companionAsksFor(vaultKey: string, owner: object, make: ()` — function, line 341

## Internal implementation anchors

- `function errorOf(error: unknown):` — function, line 64
- `const record = error as` — const, line 66
- `const UNSAVED =` — const, line 76
- `const index = list.findIndex((exchange)` — const, line 123
- `const next = [...list]` — const, line 125
- `const list = this.thread(request.deskId)` — const, line 135
- `const exchange = list[index]` — const, line 137
- `const parent = this.parentFor(request)` — const, line 147
- `const input: Omit<CompanionAskInput, "requestId"> =` — const, line 148
- `const requestId = this.mintRequestId()` — const, line 163
- `const exchange: CompanionExchange =` — const, line 164
- `const key = threadKey(exchange.deskId)` — const, line 183
- `const go = ()` — const, line 186
- `const exchange = [...this.threads.values()].flat().find((each)` — const, line 215
- `const remove = this.poller.register<CompanionAskJobDto>(` — const, line 244
- `const reason = errorOf(error)` — const, line 257
- `const remove = this.polls.get(requestId)` — const, line 270
- `const sent = current.sent || (job.sent ?? (job.status === "running" || job.status === "done" || job.kept))` — const, line 281
- `const base =` — const, line 282
- `const held = [...this.held]` — const, line 316
- `const STORES = new WeakMap<object, Map<string, CompanionAsks>>()` — const, line 331
- `const byVault = STORES.get(owner)` — const, line 335
- `let byVault = STORES.get(owner)` — let, line 342
- `let store = byVault.get(vaultKey)` — let, line 347

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/desks/DeskShell|src/screens/desks/DeskShell.tsx]] — import-or-re-export: `CompanionApi`, `CompanionAsks`, `CompanionExchange`, `companionAsksFor`, `forgetCompanionAsks`; references `CompanionApi`, `CompanionAsks`, `CompanionExchange`, `companionAsksFor`, `forgetCompanionAsks`
- [[Reference/Desktop/TypeScript/screens/desks/companion/Companion|src/screens/desks/companion/Companion.tsx]] — import-or-re-export: `CompanionExchange`; references `CompanionExchange`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `CompanionAskInput`, `CompanionAskJobDto`, `CompanionAskStatus`, `CompanionAskSurface`, `ReaderAnswerDto`
- [[Reference/Desktop/TypeScript/api/poller|src/api/poller.ts]] — import-or-re-export; imports `Poller`

### Assets, platform, and third-party dependencies

No explicit asset, standard-library, package, or crate dependency was detected.

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/desks/companion/asks.test.ts](../../../../../../../../apps/learnloop-tauri/src/screens/desks/companion/asks.test.ts) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/desks/companion/Companion.test.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/desks/companion/Companion.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/screens/desks/companion/asks.ts](../../../../../../../../apps/learnloop-tauri/src/screens/desks/companion/asks.ts) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

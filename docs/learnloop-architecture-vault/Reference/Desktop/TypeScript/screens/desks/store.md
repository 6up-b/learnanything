---
title: "Desktop module · src/screens/desks/store.ts"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.desks.store"
language: "TypeScript"
area: "TypeScript/screens/desks"
source_path: "apps/learnloop-tauri/src/screens/desks/store.ts"
source_paths:
  - "apps/learnloop-tauri/src/screens/desks/store.ts"
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

# `src/screens/desks/store.ts`

Area: [[Reference/Desktop/TypeScript/screens/desks/_area|TypeScript/screens/desks]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides `DeskStoreTransport`, `DeskNotice`, `FLUSH_IDLE_MS`, `DeskStore` and related exports within the desktop's TypeScript/screens/desks ownership area.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/desks/store.ts](../../../../../../../apps/learnloop-tauri/src/screens/desks/store.ts) |
| Source lines | 399 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/desks/_area|TypeScript/screens/desks]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/DeskShell|src/screens/desks/DeskShell.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/store|src/screens/desks/store.ts]]

## Public API

- `export interface DeskStoreTransport extends OutboxTransport` — interface, line 19
- `export type DeskNotice = |` — type, line 25
- `export const FLUSH_IDLE_MS = 250` — const, line 34
- `export class DeskStore` — class, line 61
- `export function deskStoreFor(vaultKey: string, transport: DeskStoreTransport, timers: Timers, clientId: ()` — function, line 387

## Internal implementation anchors

- `function keptBothRedirects(batch:` — function, line 37
- `const redirects: KeptBothRedirects = new Map()` — const, line 38
- `const result = results[index]` — const, line 40
- `function keptLabel(now: string): string` — function, line 49
- `const at = new Date(now)` — const, line 50
- `const time = Number.isNaN(at.getTime()) ? "" : ` · $` — const, line 51
- `function errorText(error: unknown): string` — function, line 55
- `const known = this.padReads.get(padId)` — const, line 111
- `const read = this.transport.padGet(` — const, line 114
- `const state = this.pads[padId]` — const, line 141
- `const blocks = state.blocks.map((block)` — const, line 143
- `let pads = this.pads` — let, line 155
- `const run = this.flushChain.then(()` — const, line 236
- `const kind = await this.flushReporting()` — const, line 252
- `const outcome = await this.outbox.flush()` — const, line 261
- `const redirects = keptBothRedirects(outcome.batch, outcome.reply.results)` — const, line 266
- `const kept = redirects.size` — const, line 267
- `const dropped = outcome.reply.results.filter((result)` — const, line 268
- `const redirects = keptBothRedirects(outcome.batch, outcome.reply.results)` — const, line 273
- `const kept = redirects.size` — const, line 275
- `let state: DeskStateDto` — let, line 296
- `const snapshot = this.outbox.queued()` — const, line 304
- `const taken = new Set(snapshot.map((batch)` — const, line 305
- `const queued: BatchBody[] = [...(first ? [first] : []), ...snapshot]` — const, line 306
- `const head = state.serverSeq.find((entry)` — const, line 307
- `let ws: Workspace =` — let, line 308
- `const still = entries.filter((entry)` — const, line 310
- `let pads: Pads =` — let, line 314
- `const padIds = [...new Set([...Object.keys(this.pads), ...queued.flatMap((batch)` — const, line 315
- `const read = async (ids: string[])` — const, line 316
- `const reads = await Promise.all(ids.map((padId)` — const, line 317
- `const tail = this.outbox.queued().filter((batch)` — const, line 326
- `const unread = [...new Set(tail.flatMap((batch)` — const, line 330
- `const now = new Date().toISOString()` — const, line 335
- `let lost = 0` — let, line 336
- `const rebased: BatchBody[] = []` — const, line 337
- `const padOps: PadOpDto[] = []` — const, line 340
- `const next = restampPadOp(pads, batch.pad.padId, op, now, redirects)` — const, line 343
- `const ops: DeskOpDto[] = []` — const, line 354
- `const next = restampOp(ws, op)` — const, line 357
- `const STORES = new WeakMap<object, Map<string, DeskStore>>()` — const, line 384
- `let byVault = STORES.get(transport)` — let, line 388
- `let store = byVault.get(vaultKey)` — let, line 393

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/fixtures/desks/harness|src/fixtures/desks/harness.tsx]] — import-or-re-export: `DeskStore`; references `DeskStore`
- [[Reference/Desktop/TypeScript/screens/desks/DeskShell|src/screens/desks/DeskShell.tsx]] — import-or-re-export: `deskStoreFor`; references `deskStoreFor`
- [[Reference/Desktop/TypeScript/screens/desks/pads/host|src/screens/desks/pads/host.ts]] — import-or-re-export: `DeskStore`; references `DeskStore`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `DeskOpDto`, `DeskStateDto`, `PadBlockSubmissionDto`, `PadOpDto`, `PadViewDto`, `WriteOpResultDto`
- [[Reference/Desktop/TypeScript/screens/desks/keys/router|src/screens/desks/keys/router.ts]] — import-or-re-export; imports `Timers`
- [[Reference/Desktop/TypeScript/screens/desks/model/workspace|src/screens/desks/model/workspace.ts]] — import-or-re-export; imports `EMPTY_WORKSPACE`, `OpRefusal`, `Step`, `Workspace`, `fromDeskState`, `restampOp`
- [[Reference/Desktop/TypeScript/screens/desks/outbox|src/screens/desks/outbox.ts]] — import-or-re-export; imports `BatchBody`, `DeskOutbox`, `FlushOutcome`, `MemoryOutboxStore`, `OutboxTransport`
- [[Reference/Desktop/TypeScript/screens/desks/pads/model|src/screens/desks/pads/model.ts]] — import-or-re-export; imports `KeptBothRedirects`, `PadOpRefusal`, `Pads`, `applyPadOp`, `fromPadView`, `restampPadOp`

### Assets, platform, and third-party dependencies

No explicit asset, standard-library, package, or crate dependency was detected.

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/desks/store.test.ts](../../../../../../../apps/learnloop-tauri/src/screens/desks/store.test.ts) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/desks/pads/PadStackWindow.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/desks/pads/PadStackWindow.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/screens/desks/store.ts](../../../../../../../apps/learnloop-tauri/src/screens/desks/store.ts) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

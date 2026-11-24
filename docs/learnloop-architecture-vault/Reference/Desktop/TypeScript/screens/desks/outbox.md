---
title: "Desktop module · src/screens/desks/outbox.ts"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.desks.outbox"
language: "TypeScript"
area: "TypeScript/screens/desks"
source_path: "apps/learnloop-tauri/src/screens/desks/outbox.ts"
source_paths:
  - "apps/learnloop-tauri/src/screens/desks/outbox.ts"
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

# `src/screens/desks/outbox.ts`

Area: [[Reference/Desktop/TypeScript/screens/desks/_area|TypeScript/screens/desks]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides `InkSaveBody`, `InkEraseBody`, `Batch`, `BatchBody` and related exports within the desktop's TypeScript/screens/desks ownership area.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/desks/outbox.ts](../../../../../../../apps/learnloop-tauri/src/screens/desks/outbox.ts) |
| Source lines | 268 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/desks/_area|TypeScript/screens/desks]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/DeskShell|src/screens/desks/DeskShell.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/outbox|src/screens/desks/outbox.ts]]

## Public API

- `export type InkSaveBody = Omit<InkSaveInput, "clientId" | "seq">` — type, line 13
- `export type InkEraseBody = Omit<InkEraseInput, "clientId" | "seq">` — type, line 15
- `export interface Batch` — interface, line 18
- `export type BatchBody =` — type, line 27
- `export interface OutboxStore` — interface, line 35
- `export class MemoryOutboxStore implements OutboxStore` — class, line 42
- `export interface OutboxTransport` — interface, line 59
- `export type FlushOutcome = |` — type, line 69
- `export function isPermanentRefusal(code: string): boolean` — function, line 91
- `export function clientIdFor(vaultKey: string, storage: Pick<Storage, "getItem" | "setItem"> | null, mint: ()` — function, line 107
- `export class DeskOutbox` — class, line 120

## Internal implementation anchors

- `function emptyBody(body: BatchBody): boolean` — function, line 29
- `const PERMANENT_REFUSALS = new Set(["validation_error", "stale_sidecar_schema"])` — const, line 89
- `function errorText(error: unknown): string` — function, line 95
- `const key = `learnloop.desks.client.$` — const, line 108
- `const stored = storage?.getItem(key)` — const, line 110
- `const minted = mint()` — const, line 112
- `const head = state.serverSeq.find((entry)` — const, line 132
- `const pending = this.store.load()` — const, line 133
- `const maxPending = pending.length ? pending[pending.length - 1].seq : 0` — const, line 134
- `let seq = fromSeq` — let, line 152
- `const body: BatchBody = Array.isArray(each) ?` — const, line 154
- `const seq = this.nextSeq` — const, line 178
- `const seq = this.nextSeq` — const, line 186
- `const seq = this.nextSeq` — const, line 194
- `const seq = this.nextSeq` — const, line 203
- `let last: FlushOutcome =` — let, line 220
- `let reply: DeskApplyDto | PadApplyDto | InkSaveDto | InkEraseDto` — let, line 224
- `const message = errorText(error)` — const, line 239
- `const code = error && typeof error === "object" && "code" in error ? String((error as` — const, line 240
- `const rest = this.store.load().map((each): BatchBody` — const, line 249

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/desks/DeskShell|src/screens/desks/DeskShell.tsx]] — import-or-re-export: `OutboxTransport`, `clientIdFor`; references `OutboxTransport`, `clientIdFor`
- [[Reference/Desktop/TypeScript/screens/desks/pen/host|src/screens/desks/pen/host.ts]] — import-or-re-export: `InkEraseBody`, `InkSaveBody`; references `InkEraseBody`, `InkSaveBody`
- [[Reference/Desktop/TypeScript/screens/desks/store|src/screens/desks/store.ts]] — import-or-re-export: `BatchBody`, `DeskOutbox`, `FlushOutcome`, `InkEraseBody`, `InkSaveBody`, `MemoryOutboxStore`, `OutboxTransport`; references `BatchBody`, `DeskOutbox`, `FlushOutcome`, `InkEraseBody`, `InkSaveBody`, `MemoryOutboxStore`, `OutboxTransport`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `DeskApplyDto`, `DeskApplyInput`, `DeskOpDto`, `DeskStateDto`, `InkEraseDto`, `InkEraseInput`, `InkSaveDto`, `InkSaveInput`, `PadApplyDto`, `PadApplyInput`, `PadOpDto`

### Assets, platform, and third-party dependencies

No explicit asset, standard-library, package, or crate dependency was detected.

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/desks/pen/inkOutbox.test.ts](../../../../../../../apps/learnloop-tauri/src/screens/desks/pen/inkOutbox.test.ts) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/desks/outbox.test.ts](../../../../../../../apps/learnloop-tauri/src/screens/desks/outbox.test.ts) — vitest test: imports and executes this module under jsdom (`npm test`).

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/screens/desks/outbox.ts](../../../../../../../apps/learnloop-tauri/src/screens/desks/outbox.ts) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

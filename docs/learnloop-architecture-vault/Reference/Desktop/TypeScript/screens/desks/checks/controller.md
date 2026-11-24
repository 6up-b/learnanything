---
title: "Desktop module · src/screens/desks/checks/controller.ts"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.desks.checks.controller"
language: "TypeScript"
area: "TypeScript/screens/desks/checks"
source_path: "apps/learnloop-tauri/src/screens/desks/checks/controller.ts"
source_paths:
  - "apps/learnloop-tauri/src/screens/desks/checks/controller.ts"
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

# `src/screens/desks/checks/controller.ts`

Area: [[Reference/Desktop/TypeScript/screens/desks/checks/_area|TypeScript/screens/desks/checks]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides `CheckTransport`, `LIVE_CHECK_TRANSPORT`, `DueCheck`, `OpenCheck` and related exports within the desktop's TypeScript/screens/desks/checks ownership area.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/desks/checks/controller.ts](../../../../../../../../apps/learnloop-tauri/src/screens/desks/checks/controller.ts) |
| Source lines | 315 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/desks/checks/_area|TypeScript/screens/desks/checks]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/DeskShell|src/screens/desks/DeskShell.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/checks/controller|src/screens/desks/checks/controller.ts]]

## Public API

- `export interface CheckTransport` — interface, line 9
- `export const LIVE_CHECK_TRANSPORT: CheckTransport =` — const, line 19
- `export type DueCheck = ChecksDueDto["checks"][number]` — type, line 29
- `export interface OpenCheck` — interface, line 31
- `export const ARRIVING_GROUP = "just opened"` — const, line 75
- `export class CheckDesk` — class, line 77

## Internal implementation anchors

- `function messageOf(error: unknown): string` — function, line 52
- `function codeOf(error: unknown): string | null` — function, line 56
- `const REFUSED: Record<string, string> =` — const, line 61
- `function judgedKey(window: CheckVisibleDto["windows"][number]): string` — function, line 70
- `const open = this.current` — const, line 123
- `const opened = new Set(open.opened)` — const, line 125
- `const host = this.hostOf(commitmentId)` — const, line 205
- `const card = await this.transport.begin(` — const, line 208
- `const open = this.current` — const, line 223
- `const key = visibleKey(visible)` — const, line 225
- `const unjudged = visible.windows.filter((window)` — const, line 230
- `const fresh = unjudged.map((window)` — const, line 231
- `const out = await this.transport.protectMore(` — const, line 237
- `const now = this.current` — const, line 241
- `const known = new Set(now.veiled.map(refKey))` — const, line 242
- `const open = this.current` — const, line 253
- `const out = await this.transport.expose(` — const, line 256
- `const now = this.current` — const, line 258
- `const open = this.current` — const, line 274
- `const reply = await this.transport.submit(` — const, line 279
- `const open = this.current` — const, line 294

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/desks/DeskShell|src/screens/desks/DeskShell.tsx]] — import-or-re-export: `CheckDesk`, `CheckTransport`, `LIVE_CHECK_TRANSPORT`; references `CheckDesk`, `CheckTransport`, `LIVE_CHECK_TRANSPORT`
- [[Reference/Desktop/TypeScript/screens/desks/checks/CheckCard|src/screens/desks/checks/CheckCard.tsx]] — import-or-re-export: `CheckDesk`, `DueCheck`, `OpenCheck`; references `CheckDesk`, `DueCheck`, `OpenCheck`
- [[Reference/Desktop/TypeScript/screens/desks/checks/VeilLayer|src/screens/desks/checks/VeilLayer.tsx]] — import-or-re-export: `CheckDesk`; references `CheckDesk`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `CheckCardDto`, `CheckExposureKind`, `CheckSubmitDto`, `CheckVeilRefDto`, `CheckVisibleDto`, `ChecksDueDto`
- [[Reference/Desktop/TypeScript/screens/desks/checks/model|src/screens/desks/checks/model.ts]] — import-or-re-export; imports `CheckReason`, `refKey`, `visibleKey`

### Assets, platform, and third-party dependencies

No explicit asset, standard-library, package, or crate dependency was detected.

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/desks/checks/deskChecks.test.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/desks/checks/deskChecks.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/desks/checks/checks.test.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/desks/checks/checks.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/screens/desks/checks/controller.ts](../../../../../../../../apps/learnloop-tauri/src/screens/desks/checks/controller.ts) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

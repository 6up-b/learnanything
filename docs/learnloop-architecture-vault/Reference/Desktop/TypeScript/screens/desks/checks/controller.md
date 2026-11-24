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
| Source lines | 541 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/desks/checks/_area|TypeScript/screens/desks/checks]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/checks/controller|src/screens/desks/checks/controller.ts]]

## Public API

- `export interface CheckTransport` — interface, line 13
- `export const LIVE_CHECK_TRANSPORT: CheckTransport =` — const, line 23
- `export type DueCheck = ChecksDueDto["checks"][number]` — type, line 33
- `export interface OpenCheck` — interface, line 35
- `export type CheckRecovery = "pending" | "known" | "failed"` — type, line 57
- `export function codeOf(error: unknown): string | null` — function, line 63
- `export const CHECK_OPEN_WORDS = "finish or set aside the check first"` — const, line 68
- `export function checkOpenRefusal(error: unknown): string | null` — function, line 71
- `export function regionRef(region: string, windowId: string | null): CheckVeilRefDto` — function, line 88
- `export interface DraftStore` — interface, line 95
- `export const BROWSER_DRAFTS: DraftStore =` — const, line 102
- `export class CheckDesk` — class, line 120

## Internal implementation anchors

- `function messageOf(error: unknown): string` — function, line 59
- `const REFUSED: Record<string, string> =` — const, line 76
- `const inWindow = region.startsWith("window:")` — const, line 89
- `const DRAFT_PREFIX = "learnloop.checks.draft."` — const, line 100
- `const open = this.current` — const, line 179
- `const opened = new Set(open.opened)` — const, line 181
- `const draft = this.drafts.get(card.administrationToken) ?? ""` — const, line 286
- `const seen = new Set<string>()` — const, line 287
- `const veiled = [...card.protection.veiled, ...card.protection.opened].filter((ref)` — const, line 289
- `const key = refKey(ref)` — const, line 290
- `const key = `$` — const, line 311
- `const spans = this.judged.get(key) ?? new Set<string>()` — const, line 312
- `const host = this.hostOf(commitmentId)` — const, line 327
- `const card = await this.transport.begin(` — const, line 330
- `const code = codeOf(error)` — const, line 335
- `const open = this.current` — const, line 350
- `const key = visibleKey(visible)` — const, line 352
- `const out = await this.transport.protectMore(` — const, line 358
- `const now = this.current` — const, line 359
- `const revision = typeof out.revision === "number" ? out.revision : this.revision` — const, line 361
- `const opened = new Set(now.opened)` — const, line 363
- `const openedRefs = now.veiled.filter((ref)` — const, line 364
- `const standing = out.standing ?? [...now.veiled.filter((ref)` — const, line 365
- `const seen = new Set<string>()` — const, line 366
- `const veiled = [...openedRefs, ...standing].filter((ref)` — const, line 367
- `const each = refKey(ref)` — const, line 368
- `const reveiled = standing.map(refKey).filter((each)` — const, line 374
- `const key = refKey(ref)` — const, line 393
- `const ok = await this.record(key, ref, "opened_veil")` — const, line 394
- `const now = this.current` — const, line 395
- `const ref = regionRef(region, windowId)` — const, line 407
- `const ok = await this.record(`region:$` — const, line 408
- `const now = this.current` — const, line 409
- `const open = this.current` — const, line 424
- `const opened = new Set(open.opened)` — const, line 426
- `let changed = this.regions.delete(key)` — let, line 432
- `const open = this.current` — const, line 441
- `const exposureId = this.exposureIds.get(key) ?? this.mintId("cexp")` — const, line 443
- `const out = await this.transport.expose(` — const, line 446
- `const now = this.current` — const, line 447
- `const now = this.current` — const, line 453
- `const open = this.current` — const, line 473
- `const send = ()` — const, line 477
- `let reply: CheckSubmitDto` — let, line 480
- `const now = this.current ?? open` — const, line 496
- `const visible = this.visibleSource?.()` — const, line 504
- `const open = this.current` — const, line 515

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] — import-or-re-export: `CheckDesk`, `LIVE_CHECK_TRANSPORT`; references `CheckDesk`, `LIVE_CHECK_TRANSPORT`
- [[Reference/Desktop/TypeScript/app/checkGate|src/app/checkGate.tsx]] — import-or-re-export: `CheckDesk`; references `CheckDesk`
- [[Reference/Desktop/TypeScript/screens/desks/DeskShell|src/screens/desks/DeskShell.tsx]] — import-or-re-export: `CheckDesk`, `CheckTransport`, `LIVE_CHECK_TRANSPORT`, `checkOpenRefusal`; references `CheckDesk`, `CheckTransport`, `LIVE_CHECK_TRANSPORT`, `checkOpenRefusal`
- [[Reference/Desktop/TypeScript/screens/desks/checks/CheckCard|src/screens/desks/checks/CheckCard.tsx]] — import-or-re-export: `CheckDesk`, `DueCheck`, `OpenCheck`; references `CheckDesk`, `DueCheck`, `OpenCheck`
- [[Reference/Desktop/TypeScript/screens/desks/checks/VeilLayer|src/screens/desks/checks/VeilLayer.tsx]] — import-or-re-export: `CheckDesk`; references `CheckDesk`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `CheckCardDto`, `CheckExposeReplyDto`, `CheckExposureKind`, `CheckProtectReplyDto`, `CheckSubmitDto`, `CheckVeilRefDto`, `CheckVisibleDto`, `ChecksDueDto`
- [[Reference/Desktop/TypeScript/screens/desks/checks/model|src/screens/desks/checks/model.ts]] — import-or-re-export; imports `CheckReason`, `refKey`, `visibleKey`

### Assets, platform, and third-party dependencies

No explicit asset, standard-library, package, or crate dependency was detected.

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/desks/readingReport.test.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/desks/readingReport.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/desks/checks/holdSurfaces.test.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/desks/checks/holdSurfaces.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/desks/checks/deskChecks.test.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/desks/checks/deskChecks.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/desks/checks/contract.test.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/desks/checks/contract.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
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

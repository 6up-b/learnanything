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
| Source lines | 557 |
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

- `export interface CheckTransport` — interface, line 14
- `export const LIVE_CHECK_TRANSPORT: CheckTransport =` — const, line 24
- `export type DueCheck = ChecksDueDto["checks"][number]` — type, line 34
- `export interface OpenCheck` — interface, line 36
- `export type CheckRecovery = "pending" | "known" | "failed"` — type, line 58
- `export function codeOf(error: unknown): string | null` — function, line 64
- `export const CHECK_OPEN_WORDS = "finish or set aside the check first"` — const, line 69
- `export function checkOpenRefusal(error: unknown): string | null` — function, line 72
- `export function regionRef(region: string, windowId: string | null): CheckVeilRefDto` — function, line 90
- `export interface DraftStore` — interface, line 97
- `export const BROWSER_DRAFTS: DraftStore =` — const, line 104
- `export class CheckDesk` — class, line 122

## Internal implementation anchors

- `function messageOf(error: unknown): string` — function, line 60
- `const REFUSED: Record<string, string> =` — const, line 77
- `const inWindow = region.startsWith("window:")` — const, line 91
- `const DRAFT_PREFIX = "learnloop.checks.draft."` — const, line 102
- `const open = this.current` — const, line 181
- `const opened = new Set(open.opened)` — const, line 183
- `const draft = this.drafts.get(card.administrationToken) ?? ""` — const, line 289
- `const seen = new Set<string>()` — const, line 290
- `const veiled = [...card.protection.veiled, ...card.protection.opened].filter((ref)` — const, line 292
- `const key = refKey(ref)` — const, line 293
- `const key = `$` — const, line 314
- `const spans = this.judged.get(key) ?? new Set<string>()` — const, line 315
- `let chosen = handle ?? this.dueChecks()[0]?.handle ?? null` — let, line 332
- `const open = (each: string)` — const, line 333
- `let card: CheckCardDto` — let, line 336
- `const code = codeOf(error)` — const, line 352
- `const open = this.current` — const, line 367
- `const key = visibleKey(visible)` — const, line 369
- `const out = await this.transport.protectMore(` — const, line 375
- `const now = this.current` — const, line 376
- `const revision = typeof out.revision === "number" ? out.revision : this.revision` — const, line 378
- `const opened = new Set(now.opened)` — const, line 380
- `const openedRefs = now.veiled.filter((ref)` — const, line 381
- `const standing = out.standing ?? [...now.veiled.filter((ref)` — const, line 382
- `const seen = new Set<string>()` — const, line 383
- `const veiled = [...openedRefs, ...standing].filter((ref)` — const, line 384
- `const each = refKey(ref)` — const, line 385
- `const reveiled = standing.map(refKey).filter((each)` — const, line 391
- `const key = refKey(ref)` — const, line 410
- `const ok = await this.record(key, ref, "opened_veil")` — const, line 411
- `const now = this.current` — const, line 412
- `const ref = regionRef(region, windowId)` — const, line 424
- `const ok = await this.record(`region:$` — const, line 425
- `const now = this.current` — const, line 426
- `const open = this.current` — const, line 441
- `const opened = new Set(open.opened)` — const, line 443
- `let changed = this.regions.delete(key)` — let, line 449
- `const open = this.current` — const, line 458
- `const exposureId = this.exposureIds.get(key) ?? this.mintId("cexp")` — const, line 460
- `const out = await this.transport.expose(` — const, line 463
- `const now = this.current` — const, line 464
- `const now = this.current` — const, line 470
- `const open = this.current` — const, line 490
- `const send = ()` — const, line 494
- `let reply: CheckSubmitDto` — let, line 497
- `const now = this.current ?? open` — const, line 510
- `const visible = this.visibleSource?.()` — const, line 518
- `const open = this.current` — const, line 529

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] — import-or-re-export: `CheckDesk`, `LIVE_CHECK_TRANSPORT`; references `CheckDesk`, `LIVE_CHECK_TRANSPORT`
- [[Reference/Desktop/TypeScript/app/checkGate|src/app/checkGate.tsx]] — import-or-re-export: `CheckDesk`; references `CheckDesk`
- [[Reference/Desktop/TypeScript/screens/desks/DeskShell|src/screens/desks/DeskShell.tsx]] — import-or-re-export: `CheckDesk`, `CheckTransport`, `LIVE_CHECK_TRANSPORT`, `checkOpenRefusal`; references `CheckDesk`, `CheckTransport`, `LIVE_CHECK_TRANSPORT`, `checkOpenRefusal`
- [[Reference/Desktop/TypeScript/screens/desks/checks/CheckCard|src/screens/desks/checks/CheckCard.tsx]] — import-or-re-export: `CheckDesk`, `OpenCheck`; references `CheckDesk`, `OpenCheck`
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

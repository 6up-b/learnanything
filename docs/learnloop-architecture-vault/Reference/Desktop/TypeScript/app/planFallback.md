---
title: "Desktop module · src/app/planFallback.ts"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.app.planFallback"
language: "TypeScript"
area: "TypeScript/app"
source_path: "apps/learnloop-tauri/src/app/planFallback.ts"
source_paths:
  - "apps/learnloop-tauri/src/app/planFallback.ts"
source_commit: "127327ea5f73498611e3895e33768091b22c2567"
source_commit_timestamp: "2026-10-23T22:32:47-04:00"
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

# `src/app/planFallback.ts`

Area: [[Reference/Desktop/TypeScript/app/_area|TypeScript/app]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides `PlanFallbackOffer`, `extractFallbackOffer`, `noteFallbackOffer`, `currentFallbackOffer` and related exports within the desktop's TypeScript/app ownership area.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/app/planFallback.ts](../../../../../../apps/learnloop-tauri/src/app/planFallback.ts) |
| Source lines | 110 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/app/_area|TypeScript/app]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `127327ea5f73498611e3895e33768091b22c2567` |
| Commit timestamp | `2026-10-23T22:32:47-04:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] → [[Reference/Desktop/TypeScript/app/planFallback|src/app/planFallback.ts]]

## Public API

- `export interface PlanFallbackOffer` — interface, line 16
- `export function extractFallbackOffer(value: unknown): PlanFallbackOffer | null` — function, line 59
- `export function noteFallbackOffer(value: unknown): void` — function, line 76
- `export function currentFallbackOffer(): PlanFallbackOffer | null` — function, line 85
- `export function declineFallbackOffer(origin: string | null): void` — function, line 90
- `export function resetDeclinedFallbackOrigins(): void` — function, line 96
- `export function clearFallbackOffer(): void` — function, line 100
- `export function subscribeFallbackOffer(listener: Listener): ()` — function, line 105

## Internal implementation anchors

- `type Listener = (offer: PlanFallbackOffer | null)` — type, line 28
- `let current: PlanFallbackOffer | null = null` — let, line 30
- `const listeners = new Set<Listener>()` — const, line 31
- `const declinedOrigins = new Set<string>()` — const, line 33
- `function stringList(value: unknown): string[]` — function, line 35
- `function fromRecord(record: Record<string, unknown>): PlanFallbackOffer | null` — function, line 39
- `const kind = record.fallback_available ?? record.fallbackAvailable` — const, line 40
- `const tasks = stringList(record.fallback_tasks ?? record.fallbackTasks)` — const, line 42
- `const profile = record.fallback_profile ?? record.fallbackProfile` — const, line 44
- `const signedOut = (record.plan_signed_out ?? record.planSignedOut) === true` — const, line 45
- `const offerId = record.fallback_offer_id ?? record.fallbackOfferId` — const, line 46
- `const origin = record.fallback_origin ?? record.fallbackOrigin` — const, line 47
- `const record = value as Record<string, unknown>` — const, line 61
- `const details = record.details` — const, line 62
- `const fromDetails = fromRecord(details as Record<string, unknown>)` — const, line 64
- `const offer = extractFallbackOffer(value)` — const, line 77

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export: `noteFallbackOffer`; references `noteFallbackOffer`
- [[Reference/Desktop/TypeScript/components/PlanFallbackOffer|src/components/PlanFallbackOffer.tsx]] — import-or-re-export: `Offer`, `clearFallbackOffer`, `currentFallbackOffer`, `declineFallbackOffer`, `subscribeFallbackOffer`; references `Offer`, `clearFallbackOffer`, `currentFallbackOffer`, `declineFallbackOffer`, `subscribeFallbackOffer`

## Dependencies

### Desktop source modules

No local TypeScript/TSX or Rust module dependency was detected.

### Assets, platform, and third-party dependencies

No explicit asset, standard-library, package, or crate dependency was detected.

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/components/PlanFallbackOffer.test.tsx](../../../../../../apps/learnloop-tauri/src/components/PlanFallbackOffer.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).

## Modification guidance

- Change this source at its stated ownership boundary, then check every inbound consumer and outbound dependency listed above.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/app/planFallback.ts](../../../../../../apps/learnloop-tauri/src/app/planFallback.ts) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

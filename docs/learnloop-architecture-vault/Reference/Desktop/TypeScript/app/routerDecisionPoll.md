---
title: "Desktop module · src/app/routerDecisionPoll.ts"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.app.routerDecisionPoll"
language: "TypeScript"
area: "TypeScript/app"
source_path: "apps/learnloop-tauri/src/app/routerDecisionPoll.ts"
source_paths:
  - "apps/learnloop-tauri/src/app/routerDecisionPoll.ts"
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

# `src/app/routerDecisionPoll.ts`

Area: [[Reference/Desktop/TypeScript/app/_area|TypeScript/app]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides `ROUTER_DECISION_POLL_FIRST_MS`, `ROUTER_DECISION_POLL_TRIES`, `nextDiagnosticItem` within the desktop's TypeScript/app ownership area.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/app/routerDecisionPoll.ts](../../../../../../apps/learnloop-tauri/src/app/routerDecisionPoll.ts) |
| Source lines | 27 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/app/_area|TypeScript/app]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/DiagnosticReviewScreen|src/screens/DiagnosticReviewScreen.tsx]] → [[Reference/Desktop/TypeScript/app/routerDecisionPoll|src/app/routerDecisionPoll.ts]]

## Public API

- `export const ROUTER_DECISION_POLL_FIRST_MS = 500` — const, line 7
- `export const ROUTER_DECISION_POLL_TRIES = 6` — const, line 8
- `export async function nextDiagnosticItem( learningObjectId: string, episodeId?: string | null, cancelled: ()` — function, line 14

## Internal implementation anchors

- `let next = await api.getNextProbeItem(learningObjectId, episodeId)` — let, line 19

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/components/CausalAttribution|src/components/CausalAttribution.tsx]] — import-or-re-export: `ROUTER_DECISION_POLL_FIRST_MS`, `ROUTER_DECISION_POLL_TRIES`, `function`, `if (!ref) return "no typed target";
  if (ref.kind === "facet_capability") {
    return [ref.facetId`, `ref.capability].filter(Boolean).join(" · ") || "facet capability";`; references `ROUTER_DECISION_POLL_FIRST_MS`, `ROUTER_DECISION_POLL_TRIES`, `function`
- [[Reference/Desktop/TypeScript/screens/DiagnosticReviewScreen|src/screens/DiagnosticReviewScreen.tsx]] — import-or-re-export: `nextDiagnosticItem`; references `nextDiagnosticItem`
- [[Reference/Desktop/TypeScript/screens/PracticeScreen|src/screens/PracticeScreen.tsx]] — import-or-re-export: `nextDiagnosticItem`; references `nextDiagnosticItem`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `GetNextProbeItemDto`

### Assets, platform, and third-party dependencies

No explicit asset, standard-library, package, or crate dependency was detected.

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/DiagnosticReviewScreen.routerContinue.test.tsx](../../../../../../apps/learnloop-tauri/src/screens/DiagnosticReviewScreen.routerContinue.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).

## Modification guidance

- Change this source at its stated ownership boundary, then check every inbound consumer and outbound dependency listed above.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/app/routerDecisionPoll.ts](../../../../../../apps/learnloop-tauri/src/app/routerDecisionPoll.ts) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

---
title: "Desktop module · src/fixtures/retryRequests.ts"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.fixtures.retryRequests"
language: "TypeScript"
area: "TypeScript/fixtures"
source_path: "apps/learnloop-tauri/src/fixtures/retryRequests.ts"
source_paths:
  - "apps/learnloop-tauri/src/fixtures/retryRequests.ts"
activation_kind: "vitest-support"
activation_evidence: "Outside the Vite build graph: test support imported only by vitest files, directly or through other test support; it runs under `npm test` and is never in the app bundle."
generated: true
generated_at: "2026-08-18"
tags:
  - "learnloop/docs"
  - "learnloop/reference/module"
  - "learnloop/desktop"
  - "learnloop/desktop/typescript"
  - "refactor/active"
---

# `src/fixtures/retryRequests.ts`

Area: [[Reference/Desktop/TypeScript/fixtures/_area|TypeScript/fixtures]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Exposes deterministic `retryRequests` fixture data for a reproducible desktop scenario.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/fixtures/retryRequests.ts](../../../../../../apps/learnloop-tauri/src/fixtures/retryRequests.ts) |
| Source lines | 34 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/fixtures/_area|TypeScript/fixtures]] |
| Refactor status | `ACTIVE` |
| Activation kind | `vitest-support` |

## Activation and status evidence

> [!success] ACTIVE
> Outside the Vite build graph: test support imported only by vitest files, directly or through other test support; it runs under `npm test` and is never in the app bundle.
>
> Test-import chain (from a vitest file): [[Reference/Desktop/TypeScript/fixtures/retryRequests|src/fixtures/retryRequests.ts]]

## Public API

- `export interface ReportedRetry` — interface, line 10
- `export function reportFor(onError: Mock, message: string): ReportedRetry` — function, line 16
- `export async function expectRetryIssuesRequest( report: ReportedRetry, request: Mock, outcome: "fails" | "succeeds" ): Promise<void>` — function, line 22

## Internal implementation anchors

- `const calls = onError.mock.calls.filter((call)` — const, line 17
- `const before = request.mock.calls.length` — const, line 29
- `const result = report.retry!()` — const, line 30

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

No live desktop source file directly imports this module. Do not infer dormancy: it can still be an implicit entry, worker, ambient declaration, fixture, or runtime-dispatched surface.

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/errors|src/errors.ts]] — import-or-re-export; imports `RETRY_RAN`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `vitest`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/retryWiring.test.tsx](../../../../../../apps/learnloop-tauri/src/screens/retryWiring.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).

## Modification guidance

- Change this source at its stated ownership boundary, then check every inbound consumer and outbound dependency listed above.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/fixtures/retryRequests.ts](../../../../../../apps/learnloop-tauri/src/fixtures/retryRequests.ts) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

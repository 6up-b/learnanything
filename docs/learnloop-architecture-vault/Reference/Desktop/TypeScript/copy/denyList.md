---
title: "Desktop module · src/copy/denyList.ts"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.copy.denyList"
language: "TypeScript"
area: "TypeScript/copy"
source_path: "apps/learnloop-tauri/src/copy/denyList.ts"
source_paths:
  - "apps/learnloop-tauri/src/copy/denyList.ts"
source_commit: "58703c76c4954a133f0675d8ee6d0baa36bb3c4d"
source_commit_timestamp: "2026-10-13T01:11:10-04:00"
source_worktree_state: "clean"
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

# `src/copy/denyList.ts`

Area: [[Reference/Desktop/TypeScript/copy/_area|TypeScript/copy]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides `DenyTerm`, `DENY_TERMS`, `findJargon` within the desktop's TypeScript/copy ownership area.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/copy/denyList.ts](../../../../../../apps/learnloop-tauri/src/copy/denyList.ts) |
| Source lines | 77 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/copy/_area|TypeScript/copy]] |
| Refactor status | `ACTIVE` |
| Activation kind | `vitest-support` |
| Worktree state | `clean` |
| Source commit | `58703c76c4954a133f0675d8ee6d0baa36bb3c4d` |
| Commit timestamp | `2026-10-13T01:11:10-04:00` |

## Activation and status evidence

> [!success] ACTIVE
> Outside the Vite build graph: test support imported only by vitest files, directly or through other test support; it runs under `npm test` and is never in the app bundle.
>
> Test-import chain (from a vitest file): [[Reference/Desktop/TypeScript/copy/denyList|src/copy/denyList.ts]]

## Public API

- `export interface DenyTerm` — interface, line 7
- `export const DENY_TERMS: readonly DenyTerm[] = [` — const, line 19
- `export function findJargon(text: string, exemptions: Record<string, string> =` — function, line 72

## Internal implementation anchors

- `function term(name: string, plain: string, pattern?: RegExp): DenyTerm` — function, line 15
- `const allowed = new Set(Object.keys(exemptions).map((name)` — const, line 73

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

No live desktop source file directly imports this module. Do not infer dormancy: it can still be an implicit entry, worker, ambient declaration, fixture, or runtime-dispatched surface.

## Dependencies

### Desktop source modules

No local TypeScript/TSX or Rust module dependency was detected.

### Assets, platform, and third-party dependencies

No explicit asset, standard-library, package, or crate dependency was detected.

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/today/TodayPlace.test.tsx](../../../../../../apps/learnloop-tauri/src/screens/today/TodayPlace.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/today/SomethingElse.test.tsx](../../../../../../apps/learnloop-tauri/src/screens/today/SomethingElse.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/reader/readerKeys.test.ts](../../../../../../apps/learnloop-tauri/src/screens/reader/readerKeys.test.ts) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/reader/DeliverableScope.syllabus.test.tsx](../../../../../../apps/learnloop-tauri/src/screens/reader/DeliverableScope.syllabus.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/copy/denyList.test.tsx](../../../../../../apps/learnloop-tauri/src/copy/denyList.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/copy/denyList.phase4.test.tsx](../../../../../../apps/learnloop-tauri/src/copy/denyList.phase4.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/components/syllabusRole.test.tsx](../../../../../../apps/learnloop-tauri/src/components/syllabusRole.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/components/pdfPages.test.ts](../../../../../../apps/learnloop-tauri/src/components/pdfPages.test.ts) — vitest test: imports and executes this module under jsdom (`npm test`).

## Modification guidance

- Change this source at its stated ownership boundary, then check every inbound consumer and outbound dependency listed above.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/copy/denyList.ts](../../../../../../apps/learnloop-tauri/src/copy/denyList.ts) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

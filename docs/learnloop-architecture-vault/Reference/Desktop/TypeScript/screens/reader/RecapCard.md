---
title: "Desktop module · src/screens/reader/RecapCard.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.reader.RecapCard"
language: "TypeScript"
area: "TypeScript/screens/reader"
source_path: "apps/learnloop-tauri/src/screens/reader/RecapCard.tsx"
source_paths:
  - "apps/learnloop-tauri/src/screens/reader/RecapCard.tsx"
source_commit: "e18e9fb8b5f903f06535b1d65a98ebad905273af"
source_commit_timestamp: "2026-10-31T14:17:21-04:00"
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

# `src/screens/reader/RecapCard.tsx`

Area: [[Reference/Desktop/TypeScript/screens/reader/_area|TypeScript/screens/reader]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Implements the `RecapCard` routed desktop screen and coordinates its learner-facing workflow state.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/reader/RecapCard.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/RecapCard.tsx) |
| Source lines | 205 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/reader/_area|TypeScript/screens/reader]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `e18e9fb8b5f903f06535b1d65a98ebad905273af` |
| Commit timestamp | `2026-10-31T14:17:21-04:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]] → [[Reference/Desktop/TypeScript/screens/reader/RecapCard|src/screens/reader/RecapCard.tsx]]

## Public API

- `export interface RecapCardProps` — interface, line 17
- `export const recapLinkStyle: CSSProperties =` — const, line 40
- `export function RecapLink(` — function, line 51
- `export function Quoted(` — function, line 60
- `export function RecapCard(` — function, line 77

## Internal implementation anchors

- `const headingStyle: CSSProperties =` — const, line 45
- `const listStyle: CSSProperties =` — const, line 48
- `const lineStyle: CSSProperties =` — const, line 49
- `function Section(` — function, line 68
- `const continueLabel = recap.continueAt?.label ? `continue at $` — const, line 83
- `const minutes = aboutMinutes(recap.session.minutes)` — const, line 92
- `const gains = sinceLastTime.demonstrated.length > 0 || sinceLastTime.checksRetired.length > 0` — const, line 94
- `const isKept = kept.has(line.rootExchangeId)` — const, line 114
- `const abandoned = line.status === "abandoned"` — const, line 140

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]] — import-or-re-export: `RecapCard`; references `RecapCard`
- [[Reference/Desktop/TypeScript/screens/reader/WrapUpPanel|src/screens/reader/WrapUpPanel.tsx]] — import-or-re-export: `Quoted`, `RecapLink`; references `Quoted`, `RecapLink`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `ReaderRecapCardDto`
- [[Reference/Desktop/TypeScript/components/term|src/components/term.tsx]] — import-or-re-export; imports `COLOR`, `FONT_MONO`
- [[Reference/Desktop/TypeScript/screens/reader/ComingUp|src/screens/reader/ComingUp.tsx]] — import-or-re-export; imports `ComingUp`
- [[Reference/Desktop/TypeScript/screens/reader/recapCopy|src/screens/reader/recapCopy.ts]] — import-or-re-export; imports `RECAP_COPY`, `aboutMinutes`, `fullDay`, `observationLine`, `retiredCheckLine`, `shortDay`, `stepsLabel`
- [[Reference/Desktop/TypeScript/screens/reader/voices|src/screens/reader/voices.tsx]] — import-or-re-export; imports `MeaningLabel`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Reader to Practice Workflow|Reader to Practice Workflow]] — owns the end-to-end reader sequence.
- [[Concepts/Reader Tutor and Teach-Back#Reader|Reader model]] — owns reader semantics.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/reader/recapReview.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/recapReview.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/reader/RecapCard.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/RecapCard.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/reader/ComingUp.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/ComingUp.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [tests/test_sidecar_reader.py](../../../../../../../tests/test_sidecar_reader.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_sidecar_reader_pdf_view.py](../../../../../../../tests/test_sidecar_reader_pdf_view.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_reader_render_views.py](../../../../../../../tests/test_reader_render_views.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_reader_requests.py](../../../../../../../tests/test_reader_requests.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/screens/reader/RecapCard.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/RecapCard.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

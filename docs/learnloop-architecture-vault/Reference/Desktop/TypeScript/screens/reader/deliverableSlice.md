---
title: "Desktop module · src/screens/reader/deliverableSlice.ts"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.reader.deliverableSlice"
language: "TypeScript"
area: "TypeScript/screens/reader"
source_path: "apps/learnloop-tauri/src/screens/reader/deliverableSlice.ts"
source_paths:
  - "apps/learnloop-tauri/src/screens/reader/deliverableSlice.ts"
source_commit: "7c6d96da07f27bb90fe30d604207c5d8fa273013"
source_commit_timestamp: "2026-10-31T15:58:02-04:00"
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

# `src/screens/reader/deliverableSlice.ts`

Area: [[Reference/Desktop/TypeScript/screens/reader/_area|TypeScript/screens/reader]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides `DELIVERABLE_COPY`, `DELIVERABLE_POLL_MS`, `shouldPollSlice`, `sliceShown` and related exports within the desktop's TypeScript/screens/reader ownership area.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/reader/deliverableSlice.ts](../../../../../../../apps/learnloop-tauri/src/screens/reader/deliverableSlice.ts) |
| Source lines | 81 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/reader/_area|TypeScript/screens/reader]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `7c6d96da07f27bb90fe30d604207c5d8fa273013` |
| Commit timestamp | `2026-10-31T15:58:02-04:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]] → [[Reference/Desktop/TypeScript/screens/reader/DeliverableSliceCard|src/screens/reader/DeliverableSliceCard.tsx]] → [[Reference/Desktop/TypeScript/screens/reader/deliverableSlice|src/screens/reader/deliverableSlice.ts]]

## Public API

- `export const DELIVERABLE_COPY =` — const, line 8
- `export const DELIVERABLE_POLL_MS = 1500` — const, line 45
- `export function shouldPollSlice(slice: DeliverableSliceDto | null): boolean` — function, line 48
- `export function sliceShown(slice: DeliverableSliceDto | null): boolean` — function, line 54
- `export function sliceHeading(slice: DeliverableSliceDto): string` — function, line 59
- `export function offeredChoices(line: DeliverableLineDto): Array<"read_anyway" | "skip" | "check_later">` — function, line 66
- `export function sectionMarker(title: string): string` — function, line 74
- `export function sectionRef(section:` — function, line 79

## Internal implementation anchors

- `const title = slice.goal ? DELIVERABLE_COPY.forGoal(slice.goal.title) : ""` — const, line 60

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/reader/DeliverableSliceCard|src/screens/reader/DeliverableSliceCard.tsx]] — import-or-re-export: `COPY`, `DELIVERABLE_POLL_MS`, `offeredChoices`, `sectionMarker`, `sectionRef`, `shouldPollSlice`, `sliceHeading`, `sliceShown`; references `COPY`, `DELIVERABLE_POLL_MS`, `offeredChoices`, `sectionMarker`, `sectionRef`, `shouldPollSlice`, `sliceHeading`, `sliceShown`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `DeliverableLineDto`, `DeliverableSliceDto`

### Assets, platform, and third-party dependencies

No explicit asset, standard-library, package, or crate dependency was detected.

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Reader to Practice Workflow|Reader to Practice Workflow]] — owns the end-to-end reader sequence.
- [[Concepts/Reader Tutor and Teach-Back#Reader|Reader model]] — owns reader semantics.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/reader/DeliverableSliceCard.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/DeliverableSliceCard.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
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

1. Modify [apps/learnloop-tauri/src/screens/reader/deliverableSlice.ts](../../../../../../../apps/learnloop-tauri/src/screens/reader/deliverableSlice.ts) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

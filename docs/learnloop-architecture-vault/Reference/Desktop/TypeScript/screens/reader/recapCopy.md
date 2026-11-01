---
title: "Desktop module · src/screens/reader/recapCopy.ts"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.reader.recapCopy"
language: "TypeScript"
area: "TypeScript/screens/reader"
source_path: "apps/learnloop-tauri/src/screens/reader/recapCopy.ts"
source_paths:
  - "apps/learnloop-tauri/src/screens/reader/recapCopy.ts"
source_commit: "c89c84851bd6efb2023a8365288d63d797f70a63"
source_commit_timestamp: "2026-10-17T15:04:44-04:00"
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

# `src/screens/reader/recapCopy.ts`

Area: [[Reference/Desktop/TypeScript/screens/reader/_area|TypeScript/screens/reader]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides `RECAP_COPY`, `fullDay`, `shortDay`, `aboutMinutes` and related exports within the desktop's TypeScript/screens/reader ownership area.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/reader/recapCopy.ts](../../../../../../../apps/learnloop-tauri/src/screens/reader/recapCopy.ts) |
| Source lines | 73 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/reader/_area|TypeScript/screens/reader]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `c89c84851bd6efb2023a8365288d63d797f70a63` |
| Commit timestamp | `2026-10-17T15:04:44-04:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]] → [[Reference/Desktop/TypeScript/screens/reader/recapCopy|src/screens/reader/recapCopy.ts]]

## Public API

- `export const RECAP_COPY =` — const, line 6
- `export function fullDay(iso: string): string` — function, line 28
- `export function shortDay(iso: string, now: Date = new Date()): string` — function, line 35
- `export function aboutMinutes(minutes: number): string | null` — function, line 44
- `export function observationLine(kind: ReaderObservationKind | string, quoted?: string | null, observed?: Record<string, unknown> | null): string` — function, line 51
- `export function stepsLabel(count: number): string` — function, line 71

## Internal implementation anchors

- `const DAYS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]` — const, line 24
- `const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]` — const, line 25
- `const when = new Date(iso)` — const, line 29
- `const when = new Date(iso)` — const, line 36
- `const days = (now.getTime() - when.getTime()) / 86_400_000` — const, line 38
- `const whose = observed?.answerBasis === "model" ? "LearnLoop's model's answer" : "the book's"` — const, line 54

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]] — import-or-re-export: `RECAP_COPY`; references `RECAP_COPY`
- [[Reference/Desktop/TypeScript/screens/reader/RecapCard|src/screens/reader/RecapCard.tsx]] — import-or-re-export: `RECAP_COPY`, `aboutMinutes`, `fullDay`, `observationLine`, `shortDay`, `stepsLabel`; references `RECAP_COPY`, `aboutMinutes`, `fullDay`, `observationLine`, `shortDay`, `stepsLabel`
- [[Reference/Desktop/TypeScript/screens/reader/WrapUpOffer|src/screens/reader/WrapUpOffer.tsx]] — import-or-re-export: `RECAP_COPY`; references `RECAP_COPY`
- [[Reference/Desktop/TypeScript/screens/reader/WrapUpPanel|src/screens/reader/WrapUpPanel.tsx]] — import-or-re-export: `RECAP_COPY`, `observationLine`; references `RECAP_COPY`, `observationLine`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `ReaderObservationKind`

### Assets, platform, and third-party dependencies

No explicit asset, standard-library, package, or crate dependency was detected.

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Reader to Practice Workflow|Reader to Practice Workflow]] — owns the end-to-end reader sequence.
- [[Concepts/Reader Tutor and Teach-Back#Reader|Reader model]] — owns reader semantics.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/reader/recapCopyBasis.test.ts](../../../../../../../apps/learnloop-tauri/src/screens/reader/recapCopyBasis.test.ts) — vitest test: imports and executes this module under jsdom (`npm test`).
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

1. Modify [apps/learnloop-tauri/src/screens/reader/recapCopy.ts](../../../../../../../apps/learnloop-tauri/src/screens/reader/recapCopy.ts) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

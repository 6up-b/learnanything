---
title: "Desktop module · src/screens/reader/sideBySide.ts"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.reader.sideBySide"
language: "TypeScript"
area: "TypeScript/screens/reader"
source_path: "apps/learnloop-tauri/src/screens/reader/sideBySide.ts"
source_paths:
  - "apps/learnloop-tauri/src/screens/reader/sideBySide.ts"
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

# `src/screens/reader/sideBySide.ts`

Area: [[Reference/Desktop/TypeScript/screens/reader/_area|TypeScript/screens/reader]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides `SIDE_BY_SIDE_MIN_WIDTH`, `Pane`, `PaneTarget`, `targetOf` and related exports within the desktop's TypeScript/screens/reader ownership area.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/reader/sideBySide.ts](../../../../../../../apps/learnloop-tauri/src/screens/reader/sideBySide.ts) |
| Source lines | 108 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/reader/_area|TypeScript/screens/reader]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]] → [[Reference/Desktop/TypeScript/screens/reader/sideBySide|src/screens/reader/sideBySide.ts]]

## Public API

- `export const SIDE_BY_SIDE_MIN_WIDTH = 1040` — const, line 13
- `export type Pane = "main" | "side"` — type, line 15
- `export interface PaneTarget` — interface, line 18
- `export function targetOf(hit: CorrespondentSectionDto): PaneTarget` — function, line 30
- `export function judgedInOrder(view: CorrespondentsDto | null): CorrespondentSectionDto[]` — function, line 43
- `export function firstJudgedIn(view: CorrespondentsDto | null, sourceId: string): CorrespondentSectionDto | null` — function, line 51
- `export function firstCorrespondent(view: CorrespondentsDto | null): CorrespondentSectionDto | null` — function, line 58
- `export function sectionShort(title: string): string` — function, line 70
- `export function crumbLabel(target: Pick<PaneTarget, "sourceTitle" | "title">): string` — function, line 76
- `export function isNarrowWindow(width: number): boolean` — function, line 80
- `export function readSplit(): number` — function, line 87
- `export function writeSplit(value: number): void` — function, line 97
- `export function clampSplit(value: number): number` — function, line 106

## Internal implementation anchors

- `const judged = judgedInOrder(view).find((section)` — const, line 59
- `const hit = source.sections.find((section)` — const, line 63
- `const numbered = title.match(/^§?\s*(\d[\dA-Za-z]*(?:\.[\dA-Za-z]+)*)\b/)` — const, line 71
- `const SPLIT_KEY = "learnloop.reader.side-by-side-split"` — const, line 84
- `const value = Number(window.localStorage.getItem(SPLIT_KEY))` — const, line 89

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]] — import-or-re-export: `clampSplit`, `crumbLabel`, `readSplit`, `sideBySideTarget`, `writeSplit`; references `clampSplit`, `crumbLabel`, `readSplit`, `sideBySideTarget`, `writeSplit`
- [[Reference/Desktop/TypeScript/screens/reader/returnStack|src/screens/reader/returnStack.ts]] — import-or-re-export: `PaneTarget`; references `PaneTarget`
- [[Reference/Desktop/TypeScript/screens/reader/useReaderInquiry|src/screens/reader/useReaderInquiry.ts]] — import-or-re-export: `PaneTarget`; references `PaneTarget`
- [[Reference/Desktop/TypeScript/screens/reader/useSideBySide|src/screens/reader/useSideBySide.ts]] — import-or-re-export: `Pane`, `PaneTarget`, `crumbLabel`, `firstCorrespondent`, `firstJudgedIn`, `isNarrowWindow`, `targetOf`; references `Pane`, `PaneTarget`, `crumbLabel`, `firstCorrespondent`, `firstJudgedIn`, `isNarrowWindow`, `targetOf`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `CorrespondentSectionDto`, `CorrespondentsDto`

### Assets, platform, and third-party dependencies

No explicit asset, standard-library, package, or crate dependency was detected.

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Reader to Practice Workflow|Reader to Practice Workflow]] — owns the end-to-end reader sequence.
- [[Concepts/Reader Tutor and Teach-Back#Reader|Reader model]] — owns reader semantics.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/reader/useSideBySide.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/useSideBySide.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
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

1. Modify [apps/learnloop-tauri/src/screens/reader/sideBySide.ts](../../../../../../../apps/learnloop-tauri/src/screens/reader/sideBySide.ts) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

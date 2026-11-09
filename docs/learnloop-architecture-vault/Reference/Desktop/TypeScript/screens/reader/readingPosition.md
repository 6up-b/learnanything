---
title: "Desktop module · src/screens/reader/readingPosition.ts"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.reader.readingPosition"
language: "TypeScript"
area: "TypeScript/screens/reader"
source_path: "apps/learnloop-tauri/src/screens/reader/readingPosition.ts"
source_paths:
  - "apps/learnloop-tauri/src/screens/reader/readingPosition.ts"
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

# `src/screens/reader/readingPosition.ts`

Area: [[Reference/Desktop/TypeScript/screens/reader/_area|TypeScript/screens/reader]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides `ReadingPosition`, `readingPositionIn`, `spanAtPosition`, `pagePositionAt` and related exports within the desktop's TypeScript/screens/reader ownership area.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/reader/readingPosition.ts](../../../../../../../apps/learnloop-tauri/src/screens/reader/readingPosition.ts) |
| Source lines | 122 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/reader/_area|TypeScript/screens/reader]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]] → [[Reference/Desktop/TypeScript/screens/reader/readingPosition|src/screens/reader/readingPosition.ts]]

## Public API

- `export interface ReadingPosition` — interface, line 6
- `export function readingPositionIn(scroller: HTMLElement | null): ReadingPosition | null` — function, line 16
- `export function spanAtPosition(blocks: ReaderPdfBlockDto[], position: ReadingPosition): string | null` — function, line 41
- `export function pagePositionAt(scroller: HTMLElement | null, fraction: number): ReadingPosition | null` — function, line 55
- `export function spanOnPage( pageSpans: ReadonlyArray<` — function, line 75
- `export interface SectionHistory` — interface, line 89
- `export function resumeSpanFromHistory( sections: ReadonlyArray<` — function, line 104

## Internal implementation anchors

- `const top = scroller.getBoundingClientRect().top` — const, line 18
- `const pages = Array.from(scroller.querySelectorAll<HTMLElement>("[data-pdf-page]"))` — const, line 19
- `const rect = pageEl.getBoundingClientRect()` — const, line 21
- `const page = Number(pageEl.dataset.pdfPage)` — const, line 26
- `const widthPoints = Number(pageEl.dataset.widthPoints)` — const, line 28
- `const scale = widthPoints > 0 && rect.width > 0 ? rect.width / widthPoints : 0` — const, line 29
- `const onPage = blocks .filter((block)` — const, line 42
- `const height = position.pageHeightPoints ?? Math.max(...onPage.map((block)` — const, line 46
- `const edge = position.offset * height` — const, line 47
- `const below = onPage.find((block)` — const, line 48
- `const box = scroller.getBoundingClientRect()` — const, line 57
- `const marker = box.top + box.height * fraction` — const, line 58
- `const pages = Array.from(scroller.querySelectorAll<HTMLElement>("[data-pdf-page]"))` — const, line 59
- `let last: ReadingPosition | null = null` — let, line 60
- `const rect = pageEl.getBoundingClientRect()` — const, line 62
- `const page = Number(pageEl.dataset.pdfPage)` — const, line 63
- `const onPage = pageSpans.filter((entry)` — const, line 79
- `const index = Math.min(onPage.length - 1, Math.floor(position.offset * onPage.length))` — const, line 81
- `const before = pageSpans.filter((entry)` — const, line 84
- `const byId = new Map(history.map((row)` — const, line 108
- `let furthest = -1` — let, line 109
- `const row = byId.get(section.id)` — const, line 111
- `const section = sections[furthest]` — const, line 115
- `const row = byId.get(section.id)!` — const, line 116
- `const count = section.spanIds.length` — const, line 117
- `const finished = Boolean(row.completedAt) || row.spansSeen >= count` — const, line 118
- `const next = sections.slice(furthest + 1).find((entry)` — const, line 120

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]] — import-or-re-export: `ReadingPosition`; references `ReadingPosition`
- [[Reference/Desktop/TypeScript/screens/reader/PreparingView|src/screens/reader/PreparingView.tsx]] — import-or-re-export: `ReadingPosition`, `readingPositionIn`; references `ReadingPosition`, `readingPositionIn`
- [[Reference/Desktop/TypeScript/screens/reader/useReadingProgress|src/screens/reader/useReadingProgress.ts]] — import-or-re-export: `ReadingPosition`, `SectionHistory`, `pagePositionAt`, `resumeSpanFromHistory`, `spanAtPosition`, `spanOnPage`; references `ReadingPosition`, `SectionHistory`, `pagePositionAt`, `resumeSpanFromHistory`, `spanAtPosition`, `spanOnPage`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `ReaderPdfBlockDto`

### Assets, platform, and third-party dependencies

No explicit asset, standard-library, package, or crate dependency was detected.

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Reader to Practice Workflow|Reader to Practice Workflow]] — owns the end-to-end reader sequence.
- [[Concepts/Reader Tutor and Teach-Back#Reader|Reader model]] — owns reader semantics.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/reader/readingPosition.test.ts](../../../../../../../apps/learnloop-tauri/src/screens/reader/readingPosition.test.ts) — vitest test: imports and executes this module under jsdom (`npm test`).
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

1. Modify [apps/learnloop-tauri/src/screens/reader/readingPosition.ts](../../../../../../../apps/learnloop-tauri/src/screens/reader/readingPosition.ts) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

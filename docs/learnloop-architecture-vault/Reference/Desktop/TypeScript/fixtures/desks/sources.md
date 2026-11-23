---
title: "Desktop module · src/fixtures/desks/sources.ts"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.fixtures.desks.sources"
language: "TypeScript"
area: "TypeScript/fixtures/desks"
source_path: "apps/learnloop-tauri/src/fixtures/desks/sources.ts"
source_paths:
  - "apps/learnloop-tauri/src/fixtures/desks/sources.ts"
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

# `src/fixtures/desks/sources.ts`

Area: [[Reference/Desktop/TypeScript/fixtures/desks/_area|TypeScript/fixtures/desks]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Exposes deterministic `sources` fixture data for a reproducible desktop scenario.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/fixtures/desks/sources.ts](../../../../../../../apps/learnloop-tauri/src/fixtures/desks/sources.ts) |
| Source lines | 246 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/fixtures/desks/_area|TypeScript/fixtures/desks]] |
| Refactor status | `ACTIVE` |
| Activation kind | `vitest-support` |

## Activation and status evidence

> [!success] ACTIVE
> Outside the Vite build graph: test support imported only by vitest files, directly or through other test support; it runs under `npm test` and is never in the app bundle.
>
> Test-import chain (from a vitest file): [[Reference/Desktop/TypeScript/fixtures/desks/sources|src/fixtures/desks/sources.ts]]

## Public API

- `export const FIXTURE_VIDEO_IDS =` — const, line 209
- `export const FIXTURE_SOURCES =` — const, line 211
- `export const FIXTURE_VIEWS: Record<string, ReaderRenderViewDto> =` — const, line 218
- `export const FIXTURE_GUIDES: Record<string, ReaderGuidePlanDto> =` — const, line 225
- `export const FIXTURE_WATCH: Record<string, ReaderWatchPlanDto> =` — const, line 230
- `export const FIXTURE_LIBRARY: SourceLibraryCard[] = [ card(FIXTURE_SOURCES.book.sourceId, "Softmax, a short book", "book", "fixture://softmax-book"), card(FIXTURE_SOURCES.paper.sourceId, "Attention as averaging (a note)", "paper", "fixture://attention-note"),…` — const, line 241

## Internal implementation anchors

- `function block(spanId: string, blockType: string, markdown: string, extractorBlockId?: string): ReaderRenderBlockDto` — function, line 13
- `interface Section` — interface, line 27
- `const SOFTMAX_SECTIONS: Section[] = [` — const, line 33
- `const PAPER_SECTIONS: Section[] = [` — const, line 92
- `function bookView(sourceId: string, extractionId: string, sections: Section[]): ReaderRenderViewDto` — function, line 118
- `const blocks: ReaderRenderBlockDto[] = []` — const, line 119
- `function guideOf(view: ReaderRenderViewDto, sections: Section[]): ReaderGuidePlanDto` — function, line 139
- `const out: ReaderGuideSectionDto[] = sections.map((section)` — const, line 140
- `const spanIds = view.blocks.filter((each)` — const, line 141
- `const CUE_TEXT = [` — const, line 147
- `function transcriptView(sourceId: string, extractionId: string): ReaderRenderViewDto` — function, line 180
- `const blocks = CUE_TEXT.map((text, index)` — const, line 181
- `const start = index * 6` — const, line 182
- `function card(sourceId: string, title: string, kindNoun: string, canonicalUri: string): SourceLibraryCard` — function, line 200

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/fixtures/desks/companion|src/fixtures/desks/companion.ts]] — import-or-re-export: `FIXTURE_LIBRARY`, `FIXTURE_SOURCES`, `FIXTURE_VIEWS`; references `FIXTURE_LIBRARY`, `FIXTURE_SOURCES`, `FIXTURE_VIEWS`
- [[Reference/Desktop/TypeScript/fixtures/desks/fakeCore|src/fixtures/desks/fakeCore.ts]] — import-or-re-export: `FIXTURE_GUIDES`, `FIXTURE_LIBRARY`, `FIXTURE_SOURCES`, `FIXTURE_VIEWS`, `FIXTURE_WATCH`; references `FIXTURE_GUIDES`, `FIXTURE_LIBRARY`, `FIXTURE_SOURCES`, `FIXTURE_VIEWS`, `FIXTURE_WATCH`
- [[Reference/Desktop/TypeScript/fixtures/desks/goal|src/fixtures/desks/goal.ts]] — import-or-re-export: `FIXTURE_SOURCES`, `FIXTURE_VIEWS`; references `FIXTURE_SOURCES`, `FIXTURE_VIEWS`
- [[Reference/Desktop/TypeScript/fixtures/desks/harness|src/fixtures/desks/harness.tsx]] — import-or-re-export: `FIXTURE_LIBRARY`, `FIXTURE_SOURCES`; references `FIXTURE_LIBRARY`, `FIXTURE_SOURCES`
- [[Reference/Desktop/TypeScript/fixtures/desks/pads|src/fixtures/desks/pads.ts]] — import-or-re-export: `FIXTURE_SOURCES`; references `FIXTURE_SOURCES`
- [[Reference/Desktop/TypeScript/fixtures/desks/video|src/fixtures/desks/video.ts]] — import-or-re-export: `FIXTURE_SOURCES`; references `FIXTURE_SOURCES`
- [[Reference/Desktop/TypeScript/fixtures/desks/workspace|src/fixtures/desks/workspace.ts]] — import-or-re-export: `FIXTURE_SOURCES`; references `FIXTURE_SOURCES`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `ReaderGuidePlanDto`, `ReaderGuideSectionDto`, `ReaderRenderBlockDto`, `ReaderRenderViewDto`, `ReaderWatchPlanDto`, `SourceLibraryCard`

### Assets, platform, and third-party dependencies

No explicit asset, standard-library, package, or crate dependency was detected.

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Import Canonical Sources|Import Canonical Sources]] — owns import sequencing.
- [[Architecture/Content Pipeline#Durable checkpoint ladder|content checkpoint ladder]] — owns pipeline persistence semantics.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/desks/video/deskVideo.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/desks/video/deskVideo.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/desks/pen/penMode.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/desks/pen/penMode.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/desks/lesson/deskLessons.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/desks/lesson/deskLessons.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/desks/goal/watch.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/desks/goal/watch.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/desks/goal/shelf.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/desks/goal/shelf.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/desks/goal/model.test.ts](../../../../../../../apps/learnloop-tauri/src/screens/desks/goal/model.test.ts) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/desks/goal/components.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/desks/goal/components.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/desks/goal/GoalDesk.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/desks/goal/GoalDesk.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [tests/test_sidecar_ingest_m3.py](../../../../../../../tests/test_sidecar_ingest_m3.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_source_ingestion.py](../../../../../../../tests/test_source_ingestion.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_ingest_runner.py](../../../../../../../tests/test_ingest_runner.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_init.py](../../../../../../../tests/test_init.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.

## Modification guidance

- Change this source at its stated ownership boundary, then check every inbound consumer and outbound dependency listed above.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/fixtures/desks/sources.ts](../../../../../../../apps/learnloop-tauri/src/fixtures/desks/sources.ts) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

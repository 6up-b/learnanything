---
title: "Desktop module · src/screens/reader/readingReports.ts"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.reader.readingReports"
language: "TypeScript"
area: "TypeScript/screens/reader"
source_path: "apps/learnloop-tauri/src/screens/reader/readingReports.ts"
source_paths:
  - "apps/learnloop-tauri/src/screens/reader/readingReports.ts"
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

# `src/screens/reader/readingReports.ts`

Area: [[Reference/Desktop/TypeScript/screens/reader/_area|TypeScript/screens/reader]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides `SEEN_REPORT_MS`, `SeenSave`, `SeenSaved`, `seenSaveFor` and related exports within the desktop's TypeScript/screens/reader ownership area.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/reader/readingReports.ts](../../../../../../../apps/learnloop-tauri/src/screens/reader/readingReports.ts) |
| Source lines | 168 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/reader/_area|TypeScript/screens/reader]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/DeskShell|src/screens/desks/DeskShell.tsx]] → [[Reference/Desktop/TypeScript/screens/reader/readingReports|src/screens/reader/readingReports.ts]]

## Public API

- `export const SEEN_REPORT_MS = 1500` — const, line 14
- `export interface SeenSave` — interface, line 21
- `export type SeenSaved = (extractionId: string, sectionId: string, result: ReaderMarkProgressResultDto | null)` — type, line 47
- `export function seenSaveFor(saves: Map<string, SeenSave>, extractionId: string): SeenSave` — function, line 52
- `export function releaseSeenSaves(saves: Map<string, SeenSave>): void` — function, line 80
- `export function sendSeenCounts(saves: Map<string, SeenSave>, extractionId: string, onSaved?: SeenSaved): void` — function, line 92
- `export async function flushReadingReports(): Promise<void>` — function, line 151

## Internal implementation anchors

- `const SEEN_RETRY_LIMIT = 3` — const, line 16
- `const kept = new Set<SeenSave>()` — const, line 50
- `let save = saves.get(extractionId)` — let, line 53
- `function owes(save: SeenSave): boolean` — function, line 67
- `function settle(save: SeenSave): void` — function, line 75
- `const save = saves.get(extractionId)` — const, line 93
- `function sendSave(save: SeenSave, onSaved?: SeenSaved): Promise<unknown>[]` — function, line 97
- `const sent: Promise<unknown>[] = []` — const, line 100
- `const sectionIds = new Set([...Object.keys(save.wanted), ...Object.keys(save.passages), ...save.ends])` — const, line 101
- `const counts = save.wanted[sectionId]` — const, line 103
- `const countNew = counts !== undefined && counts.spansSeen > Math.max(save.acknowledged[sectionId] ?? 0, save.sending[sectionId] ?? 0)` — const, line 104
- `const passages = [...(save.passages[sectionId] ?? [])] .filter((spanId)` — const, line 106
- `const end = save.ends.has(sectionId) && !save.acknowledgedEnds.has(sectionId) && !save.sendingEnds.has(sectionId)` — const, line 108
- `const request: Promise<unknown> = api.readerNoteReadingProgress(` — const, line 113
- `const key = vaultKey()` — const, line 152
- `const sent: Promise<unknown>[] = []` — const, line 153

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/desks/DeskShell|src/screens/desks/DeskShell.tsx]] — import-or-re-export: `flushReadingReports`; references `flushReadingReports`
- [[Reference/Desktop/TypeScript/screens/reader/useReadingProgress|src/screens/reader/useReadingProgress.ts]] — import-or-re-export: `SEEN_REPORT_MS`, `SeenSave`, `const`, `releaseSeenSaves`, `seenSaveFor`, `sendSeenCounts`; references `SEEN_REPORT_MS`, `SeenSave`, `const`, `releaseSeenSaves`, `seenSaveFor`, `sendSeenCounts`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `ReaderMarkProgressResultDto`
- [[Reference/Desktop/TypeScript/app/vaultTransition|src/app/vaultTransition.ts]] — import-or-re-export; imports `onVaultActive`, `registerVaultDraft`, `vaultKey`

### Assets, platform, and third-party dependencies

No explicit asset, standard-library, package, or crate dependency was detected.

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Reader to Practice Workflow|Reader to Practice Workflow]] — owns the end-to-end reader sequence.
- [[Concepts/Reader Tutor and Teach-Back#Reader|Reader model]] — owns reader semantics.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/desks/source/ScopedSource.followsLearner.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/desks/source/ScopedSource.followsLearner.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
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

1. Modify [apps/learnloop-tauri/src/screens/reader/readingReports.ts](../../../../../../../apps/learnloop-tauri/src/screens/reader/readingReports.ts) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

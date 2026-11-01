---
title: "Desktop module · src/screens/reader/readerShared.ts"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.reader.readerShared"
language: "TypeScript"
area: "TypeScript/screens/reader"
source_path: "apps/learnloop-tauri/src/screens/reader/readerShared.ts"
source_paths:
  - "apps/learnloop-tauri/src/screens/reader/readerShared.ts"
source_commit: "589b0196e3f27734e1c37460c3f063c634e801e1"
source_commit_timestamp: "2026-10-20T19:39:38-04:00"
source_worktree_state: "staged-or-mixed"
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

# `src/screens/reader/readerShared.ts`

Area: [[Reference/Desktop/TypeScript/screens/reader/_area|TypeScript/screens/reader]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides `ANSWER_MODE_OPTIONS`, `answerModeLabel`, `clip`, `SelectionNode` and related exports within the desktop's TypeScript/screens/reader ownership area.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/reader/readerShared.ts](../../../../../../../apps/learnloop-tauri/src/screens/reader/readerShared.ts) |
| Source lines | 136 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/reader/_area|TypeScript/screens/reader]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `staged-or-mixed` |
| Source commit | `589b0196e3f27734e1c37460c3f063c634e801e1` |
| Commit timestamp | `2026-10-20T19:39:38-04:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/components/AskOverlay|src/components/AskOverlay.tsx]] → [[Reference/Desktop/TypeScript/screens/reader/readerShared|src/screens/reader/readerShared.ts]]

## Public API

- `export const ANSWER_MODE_OPTIONS = [` — const, line 4
- `export function answerModeLabel(mode: string): string` — function, line 12
- `export function clip(text: string, max: number): string` — function, line 16
- `export interface SelectionNode` — interface, line 23
- `export interface ReaderSelection` — interface, line 40
- `export function passageKeys(reading: string, spanIds: ReadonlyArray<string | null | undefined>): string[]` — function, line 57
- `export function selectionNodes(sel:` — function, line 61
- `export interface AnnotationSegment` — interface, line 69
- `export interface MarginAnnotation` — interface, line 79
- `export function placedSpanIds(annotation: MarginAnnotation): string[]` — function, line 94
- `export function groundingProtected(protection: ReaderProtectionDto | null | undefined, spanIds: readonly string[]): boolean` — function, line 107
- `export function selectionProtected( protection: ReaderProtectionDto | null | undefined, selection:` — function, line 117
- `export function askGroundingSpans( parent:` — function, line 128

## Internal implementation anchors

- `const held = new Set(protection.heldOutSpanIds)` — const, line 111

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/components/AskOverlay|src/components/AskOverlay.tsx]] — import-or-re-export: `passageKeys`; references `passageKeys`
- [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]] — import-or-re-export: `AnnotationSegment`, `MarginAnnotation`, `ReaderSelection`, `askGroundingSpans`, `clip`, `groundingProtected`, `passageKeys`, `placedSpanIds`, `selectionNodes`, `selectionProtected`; references `AnnotationSegment`, `MarginAnnotation`, `ReaderSelection`, `askGroundingSpans`, `clip`, `groundingProtected`, `passageKeys`, `placedSpanIds`, `selectionNodes`, `selectionProtected`
- [[Reference/Desktop/TypeScript/screens/reader/AlsoInBooks|src/screens/reader/AlsoInBooks.tsx]] — import-or-re-export: `clip`; references `clip`
- [[Reference/Desktop/TypeScript/screens/reader/AskRail|src/screens/reader/AskRail.tsx]] — import-or-re-export: `ANSWER_MODE_OPTIONS`, `ReaderSelection`, `answerModeLabel`, `clip`; references `ANSWER_MODE_OPTIONS`, `ReaderSelection`, `answerModeLabel`, `clip`
- [[Reference/Desktop/TypeScript/screens/reader/FindSection|src/screens/reader/FindSection.tsx]] — import-or-re-export: `clip`; references `clip`
- [[Reference/Desktop/TypeScript/screens/reader/GuideRail|src/screens/reader/GuideRail.tsx]] — import-or-re-export: `clip`; references `clip`
- [[Reference/Desktop/TypeScript/screens/reader/NotesRail|src/screens/reader/NotesRail.tsx]] — import-or-re-export: `MarginAnnotation`, `ReaderSelection`, `clip`, `selectionNodes`; references `MarginAnnotation`, `ReaderSelection`, `clip`, `selectionNodes`
- [[Reference/Desktop/TypeScript/screens/reader/ReaderAskBranches|src/screens/reader/ReaderAskBranches.tsx]] — import-or-re-export: `answerModeLabel`; references `answerModeLabel`
- [[Reference/Desktop/TypeScript/screens/reader/ReconnectLine|src/screens/reader/ReconnectLine.tsx]] — import-or-re-export: `clip`; references `clip`
- [[Reference/Desktop/TypeScript/screens/reader/SideBySidePane|src/screens/reader/SideBySidePane.tsx]] — import-or-re-export: `clip`; references `clip`
- [[Reference/Desktop/TypeScript/screens/reader/TutorOffers|src/screens/reader/TutorOffers.tsx]] — import-or-re-export: `clip`; references `clip`
- [[Reference/Desktop/TypeScript/screens/reader/figures/useFigures|src/screens/reader/figures/useFigures.ts]] — import-or-re-export: `passageKeys`; references `passageKeys`
- [[Reference/Desktop/TypeScript/screens/reader/returnStack|src/screens/reader/returnStack.ts]] — import-or-re-export: `ReaderSelection`; references `ReaderSelection`
- [[Reference/Desktop/TypeScript/screens/reader/useActiveReading|src/screens/reader/useActiveReading.ts]] — import-or-re-export: `passageKeys`; references `passageKeys`
- [[Reference/Desktop/TypeScript/screens/reader/useIntentBox|src/screens/reader/useIntentBox.ts]] — import-or-re-export: `passageKeys`; references `passageKeys`
- [[Reference/Desktop/TypeScript/screens/reader/useLibraryAsk|src/screens/reader/useLibraryAsk.ts]] — import-or-re-export: `passageKeys`; references `passageKeys`
- [[Reference/Desktop/TypeScript/screens/reader/useReaderInquiry|src/screens/reader/useReaderInquiry.ts]] — import-or-re-export: `MarginAnnotation`, `ReaderSelection`, `clip`, `passageKeys`, `selectionNodes`; references `MarginAnnotation`, `ReaderSelection`, `clip`, `passageKeys`, `selectionNodes`
- [[Reference/Desktop/TypeScript/screens/reader/useReaderWorkbench|src/screens/reader/useReaderWorkbench.ts]] — import-or-re-export: `passageKeys`; references `passageKeys`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `ReaderAnnotationPlacementDto`, `ReaderProtectionDto`

### Assets, platform, and third-party dependencies

No explicit asset, standard-library, package, or crate dependency was detected.

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Reader to Practice Workflow|Reader to Practice Workflow]] — owns the end-to-end reader sequence.
- [[Concepts/Reader Tutor and Teach-Back#Reader|Reader model]] — owns reader semantics.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

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

1. Modify [apps/learnloop-tauri/src/screens/reader/readerShared.ts](../../../../../../../apps/learnloop-tauri/src/screens/reader/readerShared.ts) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

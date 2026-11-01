---
title: "Desktop module · src/screens/reader/returnStack.ts"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.reader.returnStack"
language: "TypeScript"
area: "TypeScript/screens/reader"
source_path: "apps/learnloop-tauri/src/screens/reader/returnStack.ts"
source_paths:
  - "apps/learnloop-tauri/src/screens/reader/returnStack.ts"
source_commit: "42fc3a995cf040e1c4fd84e7656601631e56cb84"
source_commit_timestamp: "2026-10-31T19:41:54-04:00"
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

# `src/screens/reader/returnStack.ts`

Area: [[Reference/Desktop/TypeScript/screens/reader/_area|TypeScript/screens/reader]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides `DetourKind`, `RailTab`, `ReturnEntry`, `ReturnStack` and related exports within the desktop's TypeScript/screens/reader ownership area.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/reader/returnStack.ts](../../../../../../../apps/learnloop-tauri/src/screens/reader/returnStack.ts) |
| Source lines | 145 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/reader/_area|TypeScript/screens/reader]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `42fc3a995cf040e1c4fd84e7656601631e56cb84` |
| Commit timestamp | `2026-10-31T19:41:54-04:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]] → [[Reference/Desktop/TypeScript/screens/reader/returnStack|src/screens/reader/returnStack.ts]]

## Public API

- `export type DetourKind = "branch" | "peek" | "citation" | "source" | "side_by_side"` — type, line 14
- `export type RailTab = "guide" | "ask" | "notes"` — type, line 15
- `export interface ReturnEntry` — interface, line 17
- `export interface ReturnStack` — interface, line 36
- `export const EMPTY_STACK: ReturnStack =` — const, line 45
- `export function hasDetour(stack: ReturnStack): boolean` — function, line 48
- `export function canGoBack(stack: ReturnStack): boolean` — function, line 52
- `export function canGoForward(stack: ReturnStack): boolean` — function, line 56
- `export function pushDetour(stack: ReturnStack, origin: ReturnEntry, entry: ReturnEntry): ReturnStack` — function, line 65
- `export function goTo(stack: ReturnStack, index: number):` — function, line 87
- `export function back(stack: ReturnStack):` — function, line 92
- `export function forward(stack: ReturnStack):` — function, line 96
- `export function stackInquiryExchange(stack: ReturnStack): string | null` — function, line 101
- `export function openDetours(stack: ReturnStack): ReturnEntry[]` — function, line 106
- `export function unreturnedDetours(stack: ReturnStack): ReturnEntry[]` — function, line 112
- `export function markReturned(stack: ReturnStack, ids: readonly string[]): ReturnStack` — function, line 118
- `export function dropCurrent(stack: ReturnStack, id: string): ReturnStack` — function, line 127
- `export function replaceCurrent(stack: ReturnStack, id: string, patch: Partial<Pick<ReturnEntry, "label" | "sideBySide">>): ReturnStack` — function, line 139

## Internal implementation anchors

- `const current = stack.entries[stack.cursor]` — const, line 69
- `const entries = [...stack.entries.slice(0, stack.cursor + 1), entry]` — const, line 82
- `const returned = new Set(stack.returned ?? [])` — const, line 113
- `const current = stack.entries[stack.cursor]` — const, line 128
- `const entries = stack.entries.slice(0, stack.cursor)` — const, line 130
- `const current = stack.entries[stack.cursor]` — const, line 140
- `const entries = stack.entries.slice()` — const, line 142

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]] — import-or-re-export: `stackGoTo`; references `stackGoTo`
- [[Reference/Desktop/TypeScript/screens/reader/DetourStrip|src/screens/reader/DetourStrip.tsx]] — import-or-re-export: `ReturnStack`, `hasDetour`; references `ReturnStack`, `hasDetour`
- [[Reference/Desktop/TypeScript/screens/reader/useReaderInquiry|src/screens/reader/useReaderInquiry.ts]] — import-or-re-export: `EMPTY_STACK`, `RailTab`, `ReturnEntry`, `ReturnStack`, `dropCurrent`, `hasDetour`, `markReturned`, `pushDetour`, `replaceCurrent`, `stackBack`, `stackForward`, `stackInquiryExchange`, `unreturnedDetours`; references `EMPTY_STACK`, `RailTab`, `ReturnEntry`, `ReturnStack`, `dropCurrent`, `hasDetour`, `markReturned`, `pushDetour`, `replaceCurrent`, `stackBack`, `stackForward`, `stackInquiryExchange`, `unreturnedDetours`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/screens/reader/readerShared|src/screens/reader/readerShared.ts]] — import-or-re-export; imports `ReaderSelection`
- [[Reference/Desktop/TypeScript/screens/reader/sideBySide|src/screens/reader/sideBySide.ts]] — import-or-re-export; imports `PaneTarget`

### Assets, platform, and third-party dependencies

No explicit asset, standard-library, package, or crate dependency was detected.

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Reader to Practice Workflow|Reader to Practice Workflow]] — owns the end-to-end reader sequence.
- [[Concepts/Reader Tutor and Teach-Back#Reader|Reader model]] — owns reader semantics.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/reader/returnStack.test.ts](../../../../../../../apps/learnloop-tauri/src/screens/reader/returnStack.test.ts) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/reader/readerHooks.parity.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/readerHooks.parity.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/reader/inquiryComponents.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/inquiryComponents.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
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

1. Modify [apps/learnloop-tauri/src/screens/reader/returnStack.ts](../../../../../../../apps/learnloop-tauri/src/screens/reader/returnStack.ts) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

---
title: "Desktop module · src/screens/desks/pads/model.ts"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.desks.pads.model"
language: "TypeScript"
area: "TypeScript/screens/desks/pads"
source_path: "apps/learnloop-tauri/src/screens/desks/pads/model.ts"
source_paths:
  - "apps/learnloop-tauri/src/screens/desks/pads/model.ts"
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

# `src/screens/desks/pads/model.ts`

Area: [[Reference/Desktop/TypeScript/screens/desks/pads/_area|TypeScript/screens/desks/pads]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides `EDITABLE_KINDS`, `PadState`, `Pads`, `PadOpRefusal` and related exports within the desktop's TypeScript/screens/desks/pads ownership area.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/desks/pads/model.ts](../../../../../../../../apps/learnloop-tauri/src/screens/desks/pads/model.ts) |
| Source lines | 286 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/desks/pads/_area|TypeScript/screens/desks/pads]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/DeskShell|src/screens/desks/DeskShell.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/pads/model|src/screens/desks/pads/model.ts]]

## Public API

- `export const EDITABLE_KINDS: ReadonlySet<PadBlockKind> = new Set(["text", "note", "sketch", "cell", "ink", "check_cell"])` — const, line 8
- `export interface PadState` — interface, line 10
- `export type Pads = Record<string, PadState>` — type, line 17
- `export class PadOpRefusal extends Error` — class, line 19
- `export class PadOpConflict extends Error` — class, line 25
- `export function fromPadView(view: PadViewDto): PadState` — function, line 31
- `export function keyBetween(a: string | null, b: string | null): string` — function, line 46
- `export function keyAfter(blocks: PadBlockDto[], after: string | null): string` — function, line 70
- `export function applyPadOp(pads: Pads, padId: string, op: PadOpDto, now: string): Pads` — function, line 123
- `export function anchorHead(state: PadState, blockId: string, extractionId: string, spanId: string): string | null` — function, line 222
- `export type KeptBothRedirects = Map<string,` — type, line 232
- `export function restampPadOp(pads: Pads, padId: string, op: PadOpDto, now: string, redirects?: KeptBothRedirects):` — function, line 237
- `export function isLearnersWords(block: PadBlockDto): boolean` — function, line 271
- `export function firstLine(text: string): string` — function, line 278
- `export function plainLine(text: string): string` — function, line 284

## Internal implementation anchors

- `function sortBlocks(blocks: PadBlockDto[]): PadBlockDto[]` — function, line 35
- `const DIGITS = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"` — const, line 41
- `function midpoint(a: string, b: string | null): string` — function, line 51
- `let n = 0` — let, line 54
- `const low = a ? DIGITS.indexOf(a[0]) : 0` — const, line 61
- `const high = b !== null ? DIGITS.indexOf(b[0]) : DIGITS.length` — const, line 62
- `const index = blocks.findIndex((block)` — const, line 72
- `const here = blocks[index]?.positionKey ?? blocks[blocks.length - 1]?.positionKey ?? null` — const, line 73
- `const next = index >= 0 ? blocks[index + 1]?.positionKey ?? null : null` — const, line 74
- `function replace(pads: Pads, padId: string, state: PadState): Pads` — function, line 80
- `function requirePad(pads: Pads, padId: string): PadState` — function, line 84
- `const state = pads[padId]` — const, line 85
- `function requireHead(state: PadState, blockId: string, expected: string): PadBlockDto` — function, line 90
- `const block = state.blocks.find((each)` — const, line 91
- `function withBlock(state: PadState, block: PadBlockDto): PadState` — function, line 97
- `function keepBoth(pads: Pads, padId: string, state: PadState, op: Extract<PadOpDto,` — function, line 101
- `const keep = op.keepBoth as NonNullable<typeof op.keepBoth>` — const, line 102
- `const kind = head?.kind ?? "text"` — const, line 104
- `const kept: PadBlockDto =` — const, line 106
- `const state = requirePad(pads, padId)` — const, line 132
- `const pad =` — const, line 138
- `const block: PadBlockDto =` — const, line 145
- `const current = state.blocks.find((block)` — const, line 152
- `const head = requireHead(state, op.blockId, op.expectedHead)` — const, line 156
- `const next: PadBlockDto =` — const, line 158
- `const head = requireHead(state, op.blockId, op.expectedHead)` — const, line 173
- `const head = requireHead(state, op.blockId, op.expectedHead)` — const, line 177
- `const lifted: PadBlockDto =` — const, line 179
- `const stub: PadBlockDto =` — const, line 180
- `const created: PadState =` — const, line 184
- `const current = anchorHead(state, op.blockId, op.extractionId, op.spanId)` — const, line 194
- `const others = state.anchors.filter((anchor)` — const, line 196
- `const anchor: PadAnchorDto =` — const, line 201
- `const block = state.blocks.find((each)` — const, line 206
- `const next: PadBlockDto =` — const, line 212
- `const found = state.anchors.filter((anchor)` — const, line 223
- `const state = pads[padId]` — const, line 238
- `let stamped: PadOpDto = op` — let, line 239
- `const moved = redirects?.get(op.expectedHead)` — const, line 243
- `const target = stamped as Extract<PadOpDto,` — const, line 246
- `const head = state.blocks.find((block)` — const, line 247
- `const head = state.blocks.find((block)` — const, line 256

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/fixtures/desks/workspace|src/fixtures/desks/workspace.ts]] — import-or-re-export: `PadOpConflict`, `PadOpRefusal`, `Pads`, `applyPadOp`, `fromPadView`; references `PadOpConflict`, `PadOpRefusal`, `Pads`, `applyPadOp`, `fromPadView`
- [[Reference/Desktop/TypeScript/screens/desks/DeskShell|src/screens/desks/DeskShell.tsx]] — import-or-re-export: `keyAfter`; references `keyAfter`
- [[Reference/Desktop/TypeScript/screens/desks/pads/PadOverlays|src/screens/desks/pads/PadOverlays.tsx]] — import-or-re-export: `PadState`, `isLearnersWords`; references `PadState`, `isLearnersWords`
- [[Reference/Desktop/TypeScript/screens/desks/pads/PadStackWindow|src/screens/desks/pads/PadStackWindow.tsx]] — import-or-re-export: `EDITABLE_KINDS`, `PadState`, `firstLine`, `isLearnersWords`, `keyAfter`, `plainLine`; references `EDITABLE_KINDS`, `PadState`, `firstLine`, `isLearnersWords`, `keyAfter`, `plainLine`
- [[Reference/Desktop/TypeScript/screens/desks/store|src/screens/desks/store.ts]] — import-or-re-export: `KeptBothRedirects`, `PadOpRefusal`, `Pads`, `applyPadOp`, `fromPadView`, `restampPadOp`; references `KeptBothRedirects`, `PadOpRefusal`, `Pads`, `applyPadOp`, `fromPadView`, `restampPadOp`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `PadAnchorDto`, `PadBlockDto`, `PadBlockKind`, `PadDto`, `PadOpDto`, `PadProvenance`, `PadViewDto`

### Assets, platform, and third-party dependencies

No explicit asset, standard-library, package, or crate dependency was detected.

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/desks/pads/model.test.ts](../../../../../../../../apps/learnloop-tauri/src/screens/desks/pads/model.test.ts) — vitest test: imports and executes this module under jsdom (`npm test`).

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/screens/desks/pads/model.ts](../../../../../../../../apps/learnloop-tauri/src/screens/desks/pads/model.ts) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

---
title: "Desktop module · src/fixtures/desks/pads.ts"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.fixtures.desks.pads"
language: "TypeScript"
area: "TypeScript/fixtures/desks"
source_path: "apps/learnloop-tauri/src/fixtures/desks/pads.ts"
source_paths:
  - "apps/learnloop-tauri/src/fixtures/desks/pads.ts"
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

# `src/fixtures/desks/pads.ts`

Area: [[Reference/Desktop/TypeScript/fixtures/desks/_area|TypeScript/fixtures/desks]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Exposes deterministic `pads` fixture data for a reproducible desktop scenario.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/fixtures/desks/pads.ts](../../../../../../../apps/learnloop-tauri/src/fixtures/desks/pads.ts) |
| Source lines | 139 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/fixtures/desks/_area|TypeScript/fixtures/desks]] |
| Refactor status | `ACTIVE` |
| Activation kind | `vitest-support` |

## Activation and status evidence

> [!success] ACTIVE
> Outside the Vite build graph: test support imported only by vitest files, directly or through other test support; it runs under `npm test` and is never in the app bundle.
>
> Test-import chain (from a vitest file): [[Reference/Desktop/TypeScript/fixtures/desks/pads|src/fixtures/desks/pads.ts]]

## Public API

- `export const FIXTURE_PAD_IDS =` — const, line 14
- `export function fixturePads(): PadViewDto[]` — function, line 16
- `export const FIXTURE_MATH =` — const, line 65
- `export function fixtureMathPad(): PadViewDto` — function, line 73
- `export const FIXTURE_INK_PAD = "fx_pad_hand"` — const, line 91
- `export function fixtureInkPad(): PadViewDto` — function, line 106
- `export function fixtureInkOwners(): import("../../api/dto").InkOwnerViewDto[]` — function, line 118
- `export function fixtureCellsPad(cells: Array<` — function, line 132

## Internal implementation anchors

- `const T = "2026-11-22T09:00:00Z"` — const, line 7
- `const T2 = "2026-11-23T09:00:00Z"` — const, line 8
- `function block(over: Partial<PadBlockDto> & Pick<PadBlockDto, "blockId" | "kind" | "provenance" | "positionKey">): PadBlockDto` — function, line 10
- `const runningBlocks: PadBlockDto[] = [ block(` — const, line 17
- `const anchors: PadAnchorDto[] = [` — const, line 36
- `const derivingBlocks: PadBlockDto[] = [ block(` — const, line 39
- `const TEX =` — const, line 54
- `const display = (tex: string)` — const, line 63
- `const m = FIXTURE_MATH` — const, line 74
- `const at = (n: number)` — const, line 75
- `const blocks: PadBlockDto[] = [ block(` — const, line 76
- `function inkStrokes(line: string, words: number): Array<` — function, line 94
- `const points: Array<[number, number, number, number, number, number]> = []` — const, line 96
- `const x = 12 + w * 64 + i * 3.6` — const, line 98
- `const y = 30 + Math.sin(i * 0.9 + w) * 9 + (i % 5 === 0 ? -4 : 0)` — const, line 99
- `const at = (n: number)` — const, line 107
- `const reading = (id: string, hash: string)` — const, line 108
- `const blocks: PadBlockDto[] = [ block(` — const, line 109
- `const owner = (blockId: string, hash: string, words: number, transcription:` — const, line 119
- `const at = (n: number)` — const, line 133
- `const blocks: PadBlockDto[] = [ block(` — const, line 134

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/fixtures/desks/companion|src/fixtures/desks/companion.ts]] — import-or-re-export: `FIXTURE_MATH`; references `FIXTURE_MATH`
- [[Reference/Desktop/TypeScript/fixtures/desks/fakeCore|src/fixtures/desks/fakeCore.ts]] — import-or-re-export: `FIXTURE_INK_PAD`, `fixtureInkPad`, `fixturePads`; references `FIXTURE_INK_PAD`, `fixtureInkPad`, `fixturePads`
- [[Reference/Desktop/TypeScript/fixtures/desks/harness|src/fixtures/desks/harness.tsx]] — import-or-re-export: `fixtureCellsPad`, `fixtureMathPad`; references `fixtureCellsPad`, `fixtureMathPad`
- [[Reference/Desktop/TypeScript/fixtures/desks/workspace|src/fixtures/desks/workspace.ts]] — import-or-re-export: `FIXTURE_INK_PAD`, `fixtureInkOwners`, `fixturePads`; references `FIXTURE_INK_PAD`, `fixtureInkOwners`, `fixturePads`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — dynamic import; imports `PadAnchorDto`, `PadBlockDto`, `PadViewDto`
- [[Reference/Desktop/TypeScript/fixtures/desks/sources|src/fixtures/desks/sources.ts]] — import-or-re-export; imports `FIXTURE_SOURCES`

### Assets, platform, and third-party dependencies

No explicit asset, standard-library, package, or crate dependency was detected.

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/desks/pen/inkPad.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/desks/pen/inkPad.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/desks/lesson/lessonWindows.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/desks/lesson/lessonWindows.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).

## Modification guidance

- Change this source at its stated ownership boundary, then check every inbound consumer and outbound dependency listed above.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/fixtures/desks/pads.ts](../../../../../../../apps/learnloop-tauri/src/fixtures/desks/pads.ts) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

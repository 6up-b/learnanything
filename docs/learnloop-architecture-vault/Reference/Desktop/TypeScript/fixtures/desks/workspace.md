---
title: "Desktop module · src/fixtures/desks/workspace.ts"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.fixtures.desks.workspace"
language: "TypeScript"
area: "TypeScript/fixtures/desks"
source_path: "apps/learnloop-tauri/src/fixtures/desks/workspace.ts"
source_paths:
  - "apps/learnloop-tauri/src/fixtures/desks/workspace.ts"
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

# `src/fixtures/desks/workspace.ts`

Area: [[Reference/Desktop/TypeScript/fixtures/desks/_area|TypeScript/fixtures/desks]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Exposes deterministic `workspace` fixture data for a reproducible desktop scenario.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/fixtures/desks/workspace.ts](../../../../../../../apps/learnloop-tauri/src/fixtures/desks/workspace.ts) |
| Source lines | 209 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/fixtures/desks/_area|TypeScript/fixtures/desks]] |
| Refactor status | `ACTIVE` |
| Activation kind | `vitest-support` |

## Activation and status evidence

> [!success] ACTIVE
> Outside the Vite build graph: test support imported only by vitest files, directly or through other test support; it runs under `npm test` and is never in the app bundle.
>
> Test-import chain (from a vitest file): [[Reference/Desktop/TypeScript/fixtures/desks/workspace|src/fixtures/desks/workspace.ts]]

## Public API

- `export function fixtureDeskState(): DeskStateDto` — function, line 13
- `export function toDeskState(ws: Workspace, serverSeq: DeskStateDto["serverSeq"]): DeskStateDto` — function, line 51
- `export class FixtureDeskServer` — class, line 74

## Internal implementation anchors

- `const window = ws.windows[id]` — const, line 62
- `const blocks = new Set((this.pads[padId]?.blocks ?? []).map((block)` — const, line 85
- `const owners = new Map<string, InkOwnerViewDto>((padId === FIXTURE_INK_PAD ? fixtureInkOwners() : []).map((owner)` — const, line 86
- `const owner = owners.get(save.blockId) ??` — const, line 89
- `const strokes = owner.strokes.filter((stroke)` — const, line 94
- `const state = this.pads[padId]` — const, line 108
- `const last = this.seqs.get(input.clientId) ?? 0` — const, line 115
- `const results: WriteOpResultDto[] = []` — const, line 118
- `const heads:` — const, line 119
- `const now = new Date().toISOString()` — const, line 120
- `const before = op.op === "edit_block" && op.keepBoth ? this.pads[input.padId]?.blocks.find((block)` — const, line 124
- `const keeps = op.op === "edit_block" && op.keepBoth !== undefined && (!before || before.headVersionId !== op.expectedHead)` — const, line 125
- `const head = Object.values(this.pads).flatMap((pad)` — const, line 128
- `const kept = this.pads[input.padId].blocks.find((block)` — const, line 132
- `const last = this.seqs.get(input.clientId) ?? 0` — const, line 152
- `const last = this.seqs.get(input.clientId) ?? 0` — const, line 161
- `const results: WriteOpResultDto[] = []` — const, line 164
- `const touched = new Set<string>()` — const, line 165
- `const conflict = this.stale(op)` — const, line 167
- `const runningBefore = new Set(this.ws.runningPadIds ?? [])` — const, line 173
- `const now = new Date().toISOString()` — const, line 177
- `const desk = deskById(this.ws, op.deskId)` — const, line 200
- `const to = deskById(this.ws, op.toDeskId)` — const, line 204

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/fixtures/desks/fakeCore|src/fixtures/desks/fakeCore.ts]] — import-or-re-export: `FixtureDeskServer`, `fixtureDeskState`; references `FixtureDeskServer`, `fixtureDeskState`
- [[Reference/Desktop/TypeScript/fixtures/desks/harness|src/fixtures/desks/harness.tsx]] — import-or-re-export: `FixtureDeskServer`; references `FixtureDeskServer`
- [[Reference/Desktop/TypeScript/fixtures/desks/realApp|src/fixtures/desks/realApp.tsx]] — import-or-re-export: `FixtureDeskServer`, `fixtureDeskState`; references `FixtureDeskServer`, `fixtureDeskState`
- [[Reference/Desktop/TypeScript/fixtures/desks/realDesk|src/fixtures/desks/realDesk.tsx]] — import-or-re-export: `FixtureDeskServer`, `fixtureDeskState`; references `FixtureDeskServer`, `fixtureDeskState`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `DeskApplyDto`, `DeskApplyInput`, `DeskOpDto`, `DeskStateDto`, `InkOwnerViewDto`, `InkStrokeDto`, `PadApplyDto`, `PadApplyInput`, `PadViewDto`, `WriteOpResultDto`
- [[Reference/Desktop/TypeScript/fixtures/desks/pads|src/fixtures/desks/pads.ts]] — import-or-re-export; imports `FIXTURE_INK_PAD`, `fixtureInkOwners`, `fixturePads`
- [[Reference/Desktop/TypeScript/fixtures/desks/sources|src/fixtures/desks/sources.ts]] — import-or-re-export; imports `FIXTURE_SOURCES`
- [[Reference/Desktop/TypeScript/screens/desks/model/workspace|src/screens/desks/model/workspace.ts]] — import-or-re-export; imports `OpRefusal`, `Workspace`, `applyDeskOp`, `deskById`, `fromDeskState`
- [[Reference/Desktop/TypeScript/screens/desks/pads/model|src/screens/desks/pads/model.ts]] — import-or-re-export; imports `PadOpConflict`, `PadOpRefusal`, `Pads`, `applyPadOp`, `fromPadView`

### Assets, platform, and third-party dependencies

No explicit asset, standard-library, package, or crate dependency was detected.

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/desks/windows/SourceWindow.reread.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/desks/windows/SourceWindow.reread.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/desks/video/deskVideo.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/desks/video/deskVideo.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/desks/store.test.ts](../../../../../../../apps/learnloop-tauri/src/screens/desks/store.test.ts) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/desks/readingReport.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/desks/readingReport.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/desks/pen/penMode.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/desks/pen/penMode.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/desks/pen/inkPad.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/desks/pen/inkPad.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/desks/pads/PadStackWindow.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/desks/pads/PadStackWindow.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/desks/overview/links.test.ts](../../../../../../../apps/learnloop-tauri/src/screens/desks/overview/links.test.ts) — vitest test: imports and executes this module under jsdom (`npm test`).

## Modification guidance

- Change this source at its stated ownership boundary, then check every inbound consumer and outbound dependency listed above.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/fixtures/desks/workspace.ts](../../../../../../../apps/learnloop-tauri/src/fixtures/desks/workspace.ts) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

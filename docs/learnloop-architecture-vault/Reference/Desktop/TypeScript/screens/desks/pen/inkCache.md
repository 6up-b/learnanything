---
title: "Desktop module · src/screens/desks/pen/inkCache.ts"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.desks.pen.inkCache"
language: "TypeScript"
area: "TypeScript/screens/desks/pen"
source_path: "apps/learnloop-tauri/src/screens/desks/pen/inkCache.ts"
source_paths:
  - "apps/learnloop-tauri/src/screens/desks/pen/inkCache.ts"
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

# `src/screens/desks/pen/inkCache.ts`

Area: [[Reference/Desktop/TypeScript/screens/desks/pen/_area|TypeScript/screens/desks/pen]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides `InkCacheApi`, `ReadingStatus`, `LineReading`, `InkLine` and related exports within the desktop's TypeScript/screens/desks/pen ownership area.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/desks/pen/inkCache.ts](../../../../../../../../apps/learnloop-tauri/src/screens/desks/pen/inkCache.ts) |
| Source lines | 229 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/desks/pen/_area|TypeScript/screens/desks/pen]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/DeskShell|src/screens/desks/DeskShell.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/pen/inkCache|src/screens/desks/pen/inkCache.ts]]

## Public API

- `export interface InkCacheApi` — interface, line 11
- `export type ReadingStatus = "reading" | "read" | "kept_yours" | "nothing" | "cannot" | "failed" | "cancelled"` — type, line 18
- `export interface LineReading` — interface, line 20
- `export interface InkLine` — interface, line 27
- `export interface PadInk` — interface, line 36
- `export interface InkCacheDeps` — interface, line 45
- `export class InkCache` — class, line 62

## Internal implementation anchors

- `const EMPTY: PadInk =` — const, line 43
- `function codeOf(error: unknown): string` — function, line 54
- `function messageOf(error: unknown): string` — function, line 58
- `const known = this.loads.get(padId)` — const, line 93
- `const read = this.deps.api.inkList(` — const, line 95
- `const lines: Record<string, InkLine> =` — const, line 98
- `const server = lines[blockId]` — const, line 105
- `const line = pad.lines[blockId] ??` — const, line 123
- `const before = this.writing.get(padId)` — const, line 130
- `const line = pad.lines[blockId]` — const, line 138
- `const line = this.pad(padId).lines[blockId]` — const, line 150
- `const last = line?.strokes[line.strokes.length - 1]` — const, line 151
- `const current = this.pad(padId).readings[blockId]` — const, line 153
- `let first: InkTranscribeJobDto` — let, line 160
- `const jobId = first.jobId` — const, line 168
- `const remove = this.deps.poller.register<InkTranscribeJobDto>(` — const, line 170
- `const done = this.settle(padId, blockId, job)` — const, line 175
- `const reading = this.pad(padId).readings[blockId]` — const, line 191
- `const result = job.result` — const, line 208
- `const status: ReadingStatus = result.confidenceLabel === "nothing_read" ? "nothing" : result.applied ? "read" : result.reason === "kept_your_correction" ? "kept_yours" : "read"` — const, line 209
- `const line = pad.lines[blockId]` — const, line 212
- `const code = job.error?.code ?? job.status` — const, line 219

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/desks/DeskShell|src/screens/desks/DeskShell.tsx]] — import-or-re-export: `InkCache`; references `InkCache`
- [[Reference/Desktop/TypeScript/screens/desks/pen/host|src/screens/desks/pen/host.ts]] — import-or-re-export: `InkCache`; references `InkCache`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `InkOwnerViewDto`, `InkReadingDto`, `InkStrokeDto`, `InkTranscribeJobDto`
- [[Reference/Desktop/TypeScript/api/poller|src/api/poller.ts]] — import-or-re-export; imports `Poller`

### Assets, platform, and third-party dependencies

No explicit asset, standard-library, package, or crate dependency was detected.

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/desks/pen/inkPad.test.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/desks/pen/inkPad.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/desks/pen/PenLayer.test.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/desks/pen/PenLayer.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/screens/desks/pen/inkCache.ts](../../../../../../../../apps/learnloop-tauri/src/screens/desks/pen/inkCache.ts) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

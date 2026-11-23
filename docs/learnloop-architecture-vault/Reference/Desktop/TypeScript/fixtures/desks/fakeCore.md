---
title: "Desktop module · src/fixtures/desks/fakeCore.ts"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.fixtures.desks.fakeCore"
language: "TypeScript"
area: "TypeScript/fixtures/desks"
source_path: "apps/learnloop-tauri/src/fixtures/desks/fakeCore.ts"
source_paths:
  - "apps/learnloop-tauri/src/fixtures/desks/fakeCore.ts"
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

# `src/fixtures/desks/fakeCore.ts`

Area: [[Reference/Desktop/TypeScript/fixtures/desks/_area|TypeScript/fixtures/desks]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Exposes deterministic `fakeCore` fixture data for a reproducible desktop scenario.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/fixtures/desks/fakeCore.ts](../../../../../../../apps/learnloop-tauri/src/fixtures/desks/fakeCore.ts) |
| Source lines | 213 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/fixtures/desks/_area|TypeScript/fixtures/desks]] |
| Refactor status | `ACTIVE` |
| Activation kind | `vitest-support` |

## Activation and status evidence

> [!success] ACTIVE
> Outside the Vite build graph: test support imported only by vitest files, directly or through other test support; it runs under `npm test` and is never in the app bundle.
>
> Test-import chain (from a vitest file): [[Reference/Desktop/TypeScript/fixtures/desks/fakeCore|src/fixtures/desks/fakeCore.ts]]

## Public API

- `export type InvokeArgs = Record<string, unknown>` — type, line 10
- `export interface HarnessCall` — interface, line 12
- `export async function invoke<T>(command: string, args: InvokeArgs =` — function, line 205
- `export function convertFileSrc(filePath: string, protocol = "asset"): string` — function, line 211

## Internal implementation anchors

- `function harnessDeskState(): DeskStateDto` — function, line 20
- `const state = fixtureDeskState()` — const, line 21
- `const extra: Record<string, string> =` — const, line 22
- `const padId = extra[desk.deskId]` — const, line 24
- `function harnessPads(): PadViewDto[]` — function, line 32
- `const at = "2026-11-23T09:00:00Z"` — const, line 33
- `const empty = (padId: string, deskId: string): PadViewDto` — const, line 34
- `const server = new FixtureDeskServer(harnessDeskState(), harnessPads())` — const, line 38
- `const companion = new FixtureCompanion()` — const, line 39
- `const carried: Array<` — const, line 41
- `function fixtureProposals(padId: string)` — function, line 48
- `function fixtureDrain(deskId: string)` — function, line 59
- `const pads = Object.values(server.pads).filter((pad)` — const, line 60
- `const words = pad.blocks.map((block)` — const, line 62
- `const last = words[words.length - 1] ?? ""` — const, line 63
- `const calls: HarnessCall[] = []` — const, line 67
- `interface Window` — interface, line 70
- `function viewFor(id: string)` — function, line 76
- `const CONTRACT =` — const, line 80
- `function answer(command: string, input: Record<string, unknown>): unknown` — function, line 95
- `const view = viewFor(String(input.extractionId))` — const, line 106
- `const guide = FIXTURE_GUIDES[String(input.extractionId)]` — const, line 111
- `const view = viewFor(String(input.extractionId))` — const, line 112
- `const plan = FIXTURE_WATCH[String(input.sourceId)]` — const, line 120
- `const extractionId = String(input.extractionId)` — const, line 150
- `const bySpan = new Map<string, Array<Record<string, unknown>>>()` — const, line 151
- `const block = pad.blocks.find((each)` — const, line 155
- `const extractionId = String(input.extractionId)` — const, line 163
- `const view = viewFor(extractionId)` — const, line 164
- `const spanId = String(input.fromSpanId ?? "")` — const, line 165
- `const block = view?.blocks.find((each)` — const, line 166
- `const question =` — const, line 175
- `const question = carried.find((each)` — const, line 182
- `const input = (args.input as Record<string, unknown> | undefined) ?? args` — const, line 206

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

No live desktop source file directly imports this module. Do not infer dormancy: it can still be an implicit entry, worker, ambient declaration, fixture, or runtime-dispatched surface.

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `DeskApplyInput`, `DeskStateDto`, `PadViewDto`
- [[Reference/Desktop/TypeScript/fixtures/desks/companion|src/fixtures/desks/companion.ts]] — import-or-re-export; imports `FixtureCompanion`
- [[Reference/Desktop/TypeScript/fixtures/desks/pads|src/fixtures/desks/pads.ts]] — import-or-re-export; imports `fixturePads`
- [[Reference/Desktop/TypeScript/fixtures/desks/sources|src/fixtures/desks/sources.ts]] — import-or-re-export; imports `FIXTURE_GUIDES`, `FIXTURE_LIBRARY`, `FIXTURE_VIEWS`, `FIXTURE_WATCH`
- [[Reference/Desktop/TypeScript/fixtures/desks/workspace|src/fixtures/desks/workspace.ts]] — import-or-re-export; imports `FixtureDeskServer`, `fixtureDeskState`

### Assets, platform, and third-party dependencies

No explicit asset, standard-library, package, or crate dependency was detected.

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/fixtures/desks/fakeCore.test.ts](../../../../../../../apps/learnloop-tauri/src/fixtures/desks/fakeCore.test.ts) — vitest test: imports and executes this module under jsdom (`npm test`).

## Modification guidance

- Change this source at its stated ownership boundary, then check every inbound consumer and outbound dependency listed above.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/fixtures/desks/fakeCore.ts](../../../../../../../apps/learnloop-tauri/src/fixtures/desks/fakeCore.ts) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

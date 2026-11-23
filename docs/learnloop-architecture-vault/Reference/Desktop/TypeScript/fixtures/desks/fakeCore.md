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
| Source lines | 316 |
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

- `export type InvokeArgs = Record<string, unknown>` — type, line 11
- `export interface HarnessCall` — interface, line 13
- `export async function invoke<T>(command: string, args: InvokeArgs =` — function, line 308
- `export function convertFileSrc(filePath: string, protocol = "asset"): string` — function, line 314

## Internal implementation anchors

- `function harnessDeskState(): DeskStateDto` — function, line 21
- `const state = fixtureDeskState()` — const, line 22
- `const extra: Record<string, string> =` — const, line 23
- `const padId = extra[desk.deskId]` — const, line 25
- `const INK_PAD_SHOWN = typeof window !== "undefined" && new URLSearchParams(window.location.search).get("inkpad") === "1"` — const, line 41
- `function harnessPads(): PadViewDto[]` — function, line 43
- `const at = "2026-11-23T09:00:00Z"` — const, line 44
- `const empty = (padId: string, deskId: string): PadViewDto` — const, line 45
- `const server = new FixtureDeskServer(harnessDeskState(), harnessPads())` — const, line 49
- `const companion = new FixtureCompanion()` — const, line 50
- `const goal = new FixtureGoal()` — const, line 51
- `const carried: Array<` — const, line 53
- `function fixtureProposals(padId: string)` — function, line 60
- `function fixtureDrain(deskId: string)` — function, line 71
- `const pads = Object.values(server.pads).filter((pad)` — const, line 72
- `const words = pad.blocks.map((block)` — const, line 74
- `const last = words[words.length - 1] ?? ""` — const, line 75
- `const calls: HarnessCall[] = []` — const, line 79
- `interface Window` — interface, line 82
- `function viewFor(id: string)` — function, line 88
- `const CONTRACT =` — const, line 92
- `const promotedJobs = new Map<string,` — const, line 109
- `let promotedJobCount = 0` — let, line 110
- `function cheapRows(input: Record<string, unknown>): Array<Record<string, unknown>>` — function, line 112
- `const spanId = typeof input.spanId === "string" ? input.spanId : null` — const, line 113
- `function emptyUnion(spanId: string): Record<string, unknown>` — function, line 119
- `const pen:` — const, line 124
- `function answer(command: string, input: Record<string, unknown>): unknown` — function, line 126
- `const view = viewFor(String(input.extractionId))` — const, line 137
- `const guide = FIXTURE_GUIDES[String(input.extractionId)]` — const, line 142
- `const view = viewFor(String(input.extractionId))` — const, line 143
- `const plan = FIXTURE_WATCH[String(input.sourceId)]` — const, line 151
- `const annotationId = `fx_ann_$` — const, line 160
- `const applied = server.applyInk(` — const, line 173
- `const extractionId = String(input.extractionId)` — const, line 205
- `const bySpan = new Map<string, Array<Record<string, unknown>>>()` — const, line 206
- `const block = pad.blocks.find((each)` — const, line 210
- `const extractionId = String(input.extractionId)` — const, line 218
- `const view = viewFor(extractionId)` — const, line 219
- `const spanId = String(input.fromSpanId ?? "")` — const, line 220
- `const block = view?.blocks.find((each)` — const, line 221
- `const rows = cheapRows(input)` — const, line 228
- `const jobId = typeof input.spanId === "string" ? `pj_$` — const, line 229
- `const job = promotedJobs.get(String(input.jobId))` — const, line 234
- `const paper = FIXTURE_SOURCES.paper` — const, line 239
- `const job = promotedJobs.get(String(input.jobId))` — const, line 247
- `const spanId = typeof input.spanId === "string" ? input.spanId : null` — const, line 252
- `const extractionId = typeof input.extractionId === "string" ? input.extractionId : null` — const, line 253
- `const question =` — const, line 259
- `const question = carried.find((each)` — const, line 266
- `const input = (args.input as Record<string, unknown> | undefined) ?? args` — const, line 309

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

No live desktop source file directly imports this module. Do not infer dormancy: it can still be an implicit entry, worker, ambient declaration, fixture, or runtime-dispatched surface.

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `DeskApplyInput`, `DeskStateDto`, `PadViewDto`
- [[Reference/Desktop/TypeScript/fixtures/desks/companion|src/fixtures/desks/companion.ts]] — import-or-re-export; imports `FixtureCompanion`
- [[Reference/Desktop/TypeScript/fixtures/desks/goal|src/fixtures/desks/goal.ts]] — import-or-re-export; imports `FixtureGoal`
- [[Reference/Desktop/TypeScript/fixtures/desks/pads|src/fixtures/desks/pads.ts]] — import-or-re-export; imports `FIXTURE_INK_PAD`, `fixtureInkOwners`, `fixtureInkPad`, `fixturePads`
- [[Reference/Desktop/TypeScript/fixtures/desks/sources|src/fixtures/desks/sources.ts]] — import-or-re-export; imports `FIXTURE_GUIDES`, `FIXTURE_LIBRARY`, `FIXTURE_SOURCES`, `FIXTURE_VIEWS`, `FIXTURE_WATCH`
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

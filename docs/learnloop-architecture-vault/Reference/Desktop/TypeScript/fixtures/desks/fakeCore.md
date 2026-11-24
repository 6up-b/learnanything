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
| Source lines | 415 |
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

- `export type InvokeArgs = Record<string, unknown>` — type, line 14
- `export interface HarnessCall` — interface, line 16
- `export async function invoke<T>(command: string, args: InvokeArgs =` — function, line 407
- `export function convertFileSrc(filePath: string, protocol = "asset"): string` — function, line 413

## Internal implementation anchors

- `const LESSON_PAGE = typeof window !== "undefined" && new URLSearchParams(window.location.search).get("lesson") === "1"` — const, line 23
- `function harnessDeskState(): DeskStateDto` — function, line 27
- `const state = fixtureDeskState()` — const, line 28
- `const extra: Record<string, string> =` — const, line 29
- `const padId = extra[desk.deskId]` — const, line 31
- `const stack = state.desks.find((desk)` — const, line 45
- `const INK_PAD_SHOWN = typeof window !== "undefined" && new URLSearchParams(window.location.search).get("inkpad") === "1"` — const, line 51
- `function harnessPads(): PadViewDto[]` — function, line 53
- `const at = "2026-11-23T09:00:00Z"` — const, line 54
- `const empty = (padId: string, deskId: string): PadViewDto` — const, line 55
- `const server = new FixtureDeskServer(harnessDeskState(), harnessPads())` — const, line 60
- `const companion = new FixtureCompanion()` — const, line 61
- `const goal = new FixtureGoal()` — const, line 62
- `const lessons = new FixtureLessons()` — const, line 63
- `const videoFixture = new FixtureVideo(typeof window !== "undefined" && new URLSearchParams(window.location.search).get("video") === "1")` — const, line 65
- `const checksMode = typeof window === "undefined" ? null : new URLSearchParams(window.location.search).get("checks")` — const, line 68
- `const checks = new FixtureChecks(checksMode === "open" ? "open" : checksMode === "1" ? "due" : "off")` — const, line 69
- `const carried: Array<` — const, line 71
- `function fixtureProposals(padId: string)` — function, line 78
- `function fixtureDrain(deskId: string)` — function, line 89
- `const pads = Object.values(server.pads).filter((pad)` — const, line 90
- `const words = pad.blocks.map((block)` — const, line 92
- `const last = words[words.length - 1] ?? ""` — const, line 93
- `const calls: HarnessCall[] = []` — const, line 97
- `interface Window` — interface, line 100
- `function viewFor(id: string)` — function, line 106
- `const CONTRACT =` — const, line 110
- `const promotedJobs = new Map<string,` — const, line 127
- `let promotedJobCount = 0` — let, line 128
- `function cheapRows(input: Record<string, unknown>): Array<Record<string, unknown>>` — function, line 130
- `const spanId = typeof input.spanId === "string" ? input.spanId : null` — const, line 131
- `function emptyUnion(spanId: string): Record<string, unknown>` — function, line 137
- `const pen:` — const, line 142
- `function answer(command: string, input: Record<string, unknown>): unknown` — function, line 144
- `const view = viewFor(String(input.extractionId))` — const, line 155
- `const guide = FIXTURE_GUIDES[String(input.extractionId)]` — const, line 160
- `const view = viewFor(String(input.extractionId))` — const, line 161
- `const plan = FIXTURE_WATCH[String(input.sourceId)]` — const, line 169
- `const annotationId = `fx_ann_$` — const, line 178
- `const applied = server.applyInk(` — const, line 191
- `const extractionId = String(input.extractionId)` — const, line 223
- `const bySpan = new Map<string, Array<Record<string, unknown>>>()` — const, line 224
- `const block = pad.blocks.find((each)` — const, line 228
- `const sectionOf = (spanId: string)` — const, line 234
- `const extractionId = String(input.extractionId)` — const, line 239
- `const view = viewFor(extractionId)` — const, line 240
- `const spanId = String(input.fromSpanId ?? "")` — const, line 241
- `const block = view?.blocks.find((each)` — const, line 242
- `const rows = cheapRows(input)` — const, line 249
- `const jobId = typeof input.spanId === "string" ? `pj_$` — const, line 250
- `const job = promotedJobs.get(String(input.jobId))` — const, line 255
- `const paper = FIXTURE_SOURCES.paper` — const, line 260
- `const job = promotedJobs.get(String(input.jobId))` — const, line 268
- `const spanId = typeof input.spanId === "string" ? input.spanId : null` — const, line 273
- `const extractionId = typeof input.extractionId === "string" ? input.extractionId : null` — const, line 274
- `const question =` — const, line 280
- `const question = carried.find((each)` — const, line 287
- `interface Window` — interface, line 377
- `function notebookLesson(view: LessonViewDto): LessonViewDto` — function, line 385
- `const mode = typeof window === "undefined" ? null : new URLSearchParams(window.location.search).get("nblesson")` — const, line 386
- `function notebookSession(command: string, input: Record<string, unknown>)` — function, line 392
- `const forced = new URLSearchParams(window.location.search).get("nbstate")` — const, line 393
- `const real = window.__notebookHarness` — const, line 394
- `const state = forced && forced !== "ready" ? forced : "ready"` — const, line 398
- `const input = (args.input as Record<string, unknown> | undefined) ?? args` — const, line 408

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

No live desktop source file directly imports this module. Do not infer dormancy: it can still be an implicit entry, worker, ambient declaration, fixture, or runtime-dispatched surface.

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `DeskApplyInput`, `DeskStateDto`, `LessonViewDto`, `PadViewDto`
- [[Reference/Desktop/TypeScript/fixtures/desks/checks|src/fixtures/desks/checks.ts]] — import-or-re-export; imports `FixtureChecks`
- [[Reference/Desktop/TypeScript/fixtures/desks/companion|src/fixtures/desks/companion.ts]] — import-or-re-export; imports `FixtureCompanion`
- [[Reference/Desktop/TypeScript/fixtures/desks/goal|src/fixtures/desks/goal.ts]] — import-or-re-export; imports `FixtureGoal`
- [[Reference/Desktop/TypeScript/fixtures/desks/lessons|src/fixtures/desks/lessons.ts]] — import-or-re-export; imports `FIXTURE_LESSON_ID`, `FixtureLessons`, `fixtureAdditionsPad`
- [[Reference/Desktop/TypeScript/fixtures/desks/pads|src/fixtures/desks/pads.ts]] — import-or-re-export; imports `FIXTURE_INK_PAD`, `fixtureInkPad`, `fixturePads`
- [[Reference/Desktop/TypeScript/fixtures/desks/sources|src/fixtures/desks/sources.ts]] — import-or-re-export; imports `FIXTURE_GUIDES`, `FIXTURE_LIBRARY`, `FIXTURE_SOURCES`, `FIXTURE_VIEWS`, `FIXTURE_WATCH`
- [[Reference/Desktop/TypeScript/fixtures/desks/video|src/fixtures/desks/video.ts]] — import-or-re-export; imports `FixtureVideo`
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

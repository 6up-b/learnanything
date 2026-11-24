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
| Source lines | 543 |
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

- `export type InvokeArgs = Record<string, unknown>` — type, line 16
- `export interface HarnessCall` — interface, line 18
- `export const FIXTURE_PREPARING_CARD =` — const, line 32
- `export async function invoke<T>(command: string, args: InvokeArgs =` — function, line 535
- `export function convertFileSrc(filePath: string, protocol = "asset"): string` — function, line 541

## Internal implementation anchors

- `const LESSON_PAGE = typeof window !== "undefined" && new URLSearchParams(window.location.search).get("lesson") === "1"` — const, line 25
- `const PREPARING_PAGE = typeof window !== "undefined" && new URLSearchParams(window.location.search).get("preparing") === "1"` — const, line 31
- `function harnessDeskState(): DeskStateDto` — function, line 38
- `const state = fixtureDeskState()` — const, line 39
- `const extra: Record<string, string> =` — const, line 44
- `const padId = extra[desk.deskId]` — const, line 46
- `const stack = state.desks.find((desk)` — const, line 60
- `const INK_PAD_SHOWN = typeof window !== "undefined" && new URLSearchParams(window.location.search).get("inkpad") === "1"` — const, line 66
- `function harnessPads(): PadViewDto[]` — function, line 68
- `const at = "2026-11-23T09:00:00Z"` — const, line 69
- `const empty = (padId: string, deskId: string): PadViewDto` — const, line 70
- `const server = new FixtureDeskServer(harnessDeskState(), harnessPads())` — const, line 75
- `const companion = new FixtureCompanion()` — const, line 76
- `const goal = new FixtureGoal()` — const, line 77
- `const lessons = new FixtureLessons()` — const, line 78
- `const videoFixture = new FixtureVideo(typeof window !== "undefined" && new URLSearchParams(window.location.search).get("video") === "1")` — const, line 80
- `const checksMode = typeof window === "undefined" ? null : new URLSearchParams(window.location.search).get("checks")` — const, line 83
- `const checks = new FixtureChecks(checksMode === "open" ? "open" : checksMode === "1" ? "due" : "off")` — const, line 84
- `const carried: Array<` — const, line 86
- `function fixtureProposals(padId: string)` — function, line 93
- `function fixtureDrain(deskId: string)` — function, line 104
- `const pads = Object.values(server.pads).filter((pad)` — const, line 105
- `const words = pad.blocks.map((block)` — const, line 107
- `const last = words[words.length - 1] ?? ""` — const, line 108
- `const calls: HarnessCall[] = []` — const, line 112
- `interface Window` — interface, line 115
- `function viewFor(id: string)` — function, line 121
- `const PAIRS = typeof window !== "undefined" && new URLSearchParams(window.location.search).get("pairs") === "1"` — const, line 125
- `function pairCorrespondents(input:` — function, line 129
- `const n = input.extractionId === book.extractionId ? Number(/_s(\d+)$/.exec(input.sectionId)?.[1] ?? NaN) : NaN` — const, line 131
- `const section = `$` — const, line 133
- `const view = FIXTURE_VIEWS[paper.sourceId]` — const, line 134
- `const first = view?.blocks.find((block)` — const, line 135
- `const CONTRACT =` — const, line 144
- `const workbench = new FixtureWorkbench()` — const, line 167
- `const promotedJobs = new Map<string,` — const, line 170
- `let promotedJobCount = 0` — let, line 171
- `function cheapRows(input: Record<string, unknown>): Array<Record<string, unknown>>` — function, line 173
- `const spanId = typeof input.spanId === "string" ? input.spanId : null` — const, line 174
- `function emptyUnion(spanId: string): Record<string, unknown>` — function, line 180
- `const INK_HELP_LINES = ["$\\sum_k p_k = \\sum_k e^` — const, line 186
- `const inkHelpRead = new Map<string, number>()` — const, line 187
- `function inkHelpReading(inkId: string): Record<string, unknown> | null` — function, line 189
- `const save = pen.inks.find((each)` — const, line 191
- `const blockId = save?.owner?.blockId` — const, line 192
- `const padId = Object.keys(server.pads).find((id)` — const, line 194
- `const index = inkHelpRead.get(blockId) ?? inkHelpRead.size` — const, line 196
- `const text = INK_HELP_LINES[index % INK_HELP_LINES.length]` — const, line 198
- `const state = server.pads[padId]` — const, line 199
- `const headVersionId = `fx_ink_read_$` — const, line 200
- `const pen:` — const, line 209
- `function answer(command: string, input: Record<string, unknown>): unknown` — function, line 211
- `const fromWorkbench = workbench.answer(command, input)` — const, line 212
- `const view = viewFor(String(input.extractionId))` — const, line 224
- `const guide = FIXTURE_GUIDES[String(input.extractionId)]` — const, line 229
- `const view = viewFor(String(input.extractionId))` — const, line 230
- `const plan = FIXTURE_WATCH[String(input.sourceId)]` — const, line 245
- `const annotationId = `fx_ann_$` — const, line 254
- `const nodes = ((input.rawSelection as` — const, line 256
- `const segments = nodes.map((node)` — const, line 257
- `const applied = server.applyInk(` — const, line 278
- `const read = inkHelpReading(String(input.inkId))` — const, line 286
- `const extractionId = String(input.extractionId)` — const, line 320
- `const bySpan = new Map<string, Array<Record<string, unknown>>>()` — const, line 321
- `const block = pad.blocks.find((each)` — const, line 325
- `const sectionOf = (spanId: string)` — const, line 331
- `const extractionId = String(input.extractionId)` — const, line 336
- `const view = viewFor(extractionId)` — const, line 337
- `const spanId = String(input.fromSpanId ?? "")` — const, line 338
- `const block = view?.blocks.find((each)` — const, line 339
- `const rows = cheapRows(input)` — const, line 346
- `const jobId = typeof input.spanId === "string" ? `pj_$` — const, line 347
- `const job = promotedJobs.get(String(input.jobId))` — const, line 352
- `const paper = FIXTURE_SOURCES.paper` — const, line 357
- `const job = promotedJobs.get(String(input.jobId))` — const, line 365
- `const spanId = typeof input.spanId === "string" ? input.spanId : null` — const, line 370
- `const extractionId = typeof input.extractionId === "string" ? input.extractionId : null` — const, line 371
- `const question =` — const, line 377
- `const question = carried.find((each)` — const, line 384
- `function recapAnswer(command: string, input: Record<string, unknown>): unknown` — function, line 481
- `const extractionId = String(input.extractionId ?? "")` — const, line 482
- `const ours = extractionId === FIXTURE_SOURCES.book.extractionId` — const, line 484
- `const session =` — const, line 485
- `const open = [` — const, line 486
- `interface Window` — interface, line 505
- `function notebookLesson(view: LessonViewDto): LessonViewDto` — function, line 513
- `const mode = typeof window === "undefined" ? null : new URLSearchParams(window.location.search).get("nblesson")` — const, line 514
- `function notebookSession(command: string, input: Record<string, unknown>)` — function, line 520
- `const forced = new URLSearchParams(window.location.search).get("nbstate")` — const, line 521
- `const real = window.__notebookHarness` — const, line 522
- `const state = forced && forced !== "ready" ? forced : "ready"` — const, line 526
- `const input = (args.input as Record<string, unknown> | undefined) ?? args` — const, line 536

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/fixtures/desks/realDesk|src/fixtures/desks/realDesk.tsx]] — import-or-re-export: `fixtureFileSrc`, `fixtureInvoke`; references `fixtureFileSrc`, `fixtureInvoke`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `DeskApplyInput`, `DeskStateDto`, `LessonViewDto`, `PadViewDto`, `SourceLibraryCard`
- [[Reference/Desktop/TypeScript/fixtures/desks/checks|src/fixtures/desks/checks.ts]] — import-or-re-export; imports `FixtureChecks`
- [[Reference/Desktop/TypeScript/fixtures/desks/companion|src/fixtures/desks/companion.ts]] — import-or-re-export; imports `FixtureCompanion`
- [[Reference/Desktop/TypeScript/fixtures/desks/figures|src/fixtures/desks/figures.ts]] — import-or-re-export; imports `fixtureFigure`
- [[Reference/Desktop/TypeScript/fixtures/desks/goal|src/fixtures/desks/goal.ts]] — import-or-re-export; imports `FixtureGoal`
- [[Reference/Desktop/TypeScript/fixtures/desks/lessons|src/fixtures/desks/lessons.ts]] — import-or-re-export; imports `FIXTURE_LESSON_ID`, `FixtureLessons`, `fixtureAdditionsPad`
- [[Reference/Desktop/TypeScript/fixtures/desks/pads|src/fixtures/desks/pads.ts]] — import-or-re-export; imports `FIXTURE_INK_PAD`, `fixtureInkPad`, `fixturePads`
- [[Reference/Desktop/TypeScript/fixtures/desks/sources|src/fixtures/desks/sources.ts]] — import-or-re-export; imports `FIXTURE_GUIDES`, `FIXTURE_LIBRARY`, `FIXTURE_SOURCES`, `FIXTURE_VIEWS`, `FIXTURE_WATCH`
- [[Reference/Desktop/TypeScript/fixtures/desks/video|src/fixtures/desks/video.ts]] — import-or-re-export; imports `FixtureVideo`
- [[Reference/Desktop/TypeScript/fixtures/desks/workbench|src/fixtures/desks/workbench.ts]] — import-or-re-export; imports `FixtureWorkbench`
- [[Reference/Desktop/TypeScript/fixtures/desks/workspace|src/fixtures/desks/workspace.ts]] — import-or-re-export; imports `FixtureDeskServer`, `fixtureDeskState`

### Assets, platform, and third-party dependencies

No explicit asset, standard-library, package, or crate dependency was detected.

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/desks/windows/SourceWindow.retired.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/desks/windows/SourceWindow.retired.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/fixtures/desks/fakeCore.test.ts](../../../../../../../apps/learnloop-tauri/src/fixtures/desks/fakeCore.test.ts) — vitest test: imports and executes this module under jsdom (`npm test`).

## Modification guidance

- Change this source at its stated ownership boundary, then check every inbound consumer and outbound dependency listed above.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/fixtures/desks/fakeCore.ts](../../../../../../../apps/learnloop-tauri/src/fixtures/desks/fakeCore.ts) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

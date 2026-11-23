---
title: "Desktop module · src/fixtures/desks/goal.ts"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.fixtures.desks.goal"
language: "TypeScript"
area: "TypeScript/fixtures/desks"
source_path: "apps/learnloop-tauri/src/fixtures/desks/goal.ts"
source_paths:
  - "apps/learnloop-tauri/src/fixtures/desks/goal.ts"
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

# `src/fixtures/desks/goal.ts`

Area: [[Reference/Desktop/TypeScript/fixtures/desks/_area|TypeScript/fixtures/desks]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Exposes deterministic `goal` fixture data for a reproducible desktop scenario.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/fixtures/desks/goal.ts](../../../../../../../apps/learnloop-tauri/src/fixtures/desks/goal.ts) |
| Source lines | 228 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/fixtures/desks/_area|TypeScript/fixtures/desks]] |
| Refactor status | `ACTIVE` |
| Activation kind | `vitest-support` |

## Activation and status evidence

> [!success] ACTIVE
> Outside the Vite build graph: test support imported only by vitest files, directly or through other test support; it runs under `npm test` and is never in the app bundle.
>
> Test-import chain (from a vitest file): [[Reference/Desktop/TypeScript/fixtures/desks/goal|src/fixtures/desks/goal.ts]]

## Public API

- `export const FIXTURE_GOAL_ID = "fx_goal_softmax"` — const, line 14
- `export class FixtureGoal` — class, line 65

## Internal implementation anchors

- `const BOOK = FIXTURE_SOURCES.book` — const, line 15
- `const PAPER = FIXTURE_SOURCES.paper` — const, line 16
- `const VIDEO = FIXTURE_SOURCES.video` — const, line 17
- `const DEPTHS: Array<` — const, line 18
- `interface FixtureLo` — interface, line 24
- `const LOS: FixtureLo[] = [` — const, line 32
- `type Place = "primary" | "alternate" | "elsewhere" | "out_of_scope" | "not_about"` — type, line 41
- `const BOOK_SECTIONS: Array<[string, string | null, string, string, Place]> = [` — const, line 42
- `const PAPER_SECTIONS: Array<[string, string | null, string, string, Place]> = [ ["p1", "lo_fx_attend", "introduces", "The definition you'll implement, as one line of matrices.", "primary"], ["p2", "lo_fx_temp", "mentions", "Why the square root: a temperature…` — const, line 50
- `const VIDEO_SECTIONS: Array<[string, number, number, string | null, string, string, Place]> = [ ["v0", 1, 3, null, "", "the setup, before any score: no LO your goal needs", "out_of_scope"], ["v1", 4, 11, "lo_fx_softmax", "develops", "the same recipe spoken: e…` — const, line 57
- `const view = Object.values(FIXTURE_VIEWS).find((each)` — const, line 86
- `const heading = view?.blocks.find((block)` — const, line 87
- `const title = String(heading?.markdown ?? "").replace(/^#+\s*/, "")` — const, line 88
- `const dots: GoalBandLoDto[] = LOS.map((lo, ordinal)` — const, line 100
- `const at = this.sectionOf(lo.id)` — const, line 101
- `const kind = this.kind(lo)` — const, line 102
- `const within = dots.filter((dot)` — const, line 107
- `const lines = dots.filter((dot)` — const, line 108
- `const at = this.sectionOf(dot.learningObjectId)!` — const, line 109
- `const row = [...BOOK_SECTIONS, ...PAPER_SECTIONS].find(([section, lo])` — const, line 110
- `const primary = dot.primary!` — const, line 111
- `const depthSize = (depth: ReadingPathDepth)` — const, line 127
- `const count = LOS.filter((lo)` — const, line 128
- `const view = Object.values(FIXTURE_VIEWS).find((each)` — const, line 154
- `const spanIds = cues ? Array.from(` — const, line 155
- `const ref = `$` — const, line 158
- `const choice = (this.choices.get(ref) ?? null) as "read_anyway" | null` — const, line 159
- `const fixtureLo = lo ? LOS.find((each)` — const, line 160
- `const kind = fixtureLo ? this.kind(fixtureLo) : null` — const, line 161
- `let level: GoalLensSectionDto["level"]` — let, line 162
- `let reasonKey: GoalLensSectionDto["reasonKey"]` — let, line 163
- `let reasonMd = reason` — let, line 164
- `const heading = view.blocks.find((block)` — const, line 182
- `const verb =` — const, line 183
- `const role = kind === "needed" ? "a goal LO" : kind === "later" ? "needed at a deeper depth" : "a prerequisite"` — const, line 184
- `const where = place === "primary" ? "its primary section" : place === "alternate" ? "another way" : "not on your path here"` — const, line 185
- `const table = extractionId === BOOK.extractionId ? BOOK_SECTIONS : extractionId === PAPER.extractionId ? PAPER_SECTIONS : []` — const, line 200
- `const levels = extractionId === VIDEO.extractionId ? VIDEO_SECTIONS.map(([section, from, to, lo, treatment, reason, place])` — const, line 201
- `const ref = `$` — const, line 209
- `const replayed = this.operations.has(input.operationId)` — const, line 210

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/fixtures/desks/fakeCore|src/fixtures/desks/fakeCore.ts]] — import-or-re-export: `FixtureGoal`; references `FixtureGoal`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `GoalBandDto`, `GoalBandLoDto`, `GoalLensDto`, `GoalLensSectionDto`, `GoalsListSnapshot`, `ReadingPathDepth`
- [[Reference/Desktop/TypeScript/fixtures/desks/sources|src/fixtures/desks/sources.ts]] — import-or-re-export; imports `FIXTURE_SOURCES`, `FIXTURE_VIEWS`

### Assets, platform, and third-party dependencies

No explicit asset, standard-library, package, or crate dependency was detected.

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Goals Exams and Certification Workflow|Goals, Exams, and Certification Workflow]] — owns the end-to-end goal path.
- [[Concepts/Goals and Certification|Goals and Certification]] — owns goal and certification semantics.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/desks/goal/watch.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/desks/goal/watch.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/desks/goal/shelf.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/desks/goal/shelf.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/desks/goal/model.test.ts](../../../../../../../apps/learnloop-tauri/src/screens/desks/goal/model.test.ts) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/desks/goal/components.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/desks/goal/components.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/desks/goal/GoalDesk.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/desks/goal/GoalDesk.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [tests/test_sidecar_goals.py](../../../../../../../tests/test_sidecar_goals.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_sidecar_exams.py](../../../../../../../tests/test_sidecar_exams.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_goal_projection.py](../../../../../../../tests/test_goal_projection.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_exam_session.py](../../../../../../../tests/test_exam_session.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.

## Modification guidance

- Change this source at its stated ownership boundary, then check every inbound consumer and outbound dependency listed above.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/fixtures/desks/goal.ts](../../../../../../../apps/learnloop-tauri/src/fixtures/desks/goal.ts) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

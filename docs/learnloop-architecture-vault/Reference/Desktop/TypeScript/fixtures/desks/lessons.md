---
title: "Desktop module · src/fixtures/desks/lessons.ts"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.fixtures.desks.lessons"
language: "TypeScript"
area: "TypeScript/fixtures/desks"
source_path: "apps/learnloop-tauri/src/fixtures/desks/lessons.ts"
source_paths:
  - "apps/learnloop-tauri/src/fixtures/desks/lessons.ts"
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

# `src/fixtures/desks/lessons.ts`

Area: [[Reference/Desktop/TypeScript/fixtures/desks/_area|TypeScript/fixtures/desks]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Exposes deterministic `lessons` fixture data for a reproducible desktop scenario.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/fixtures/desks/lessons.ts](../../../../../../../apps/learnloop-tauri/src/fixtures/desks/lessons.ts) |
| Source lines | 112 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/fixtures/desks/_area|TypeScript/fixtures/desks]] |
| Refactor status | `ACTIVE` |
| Activation kind | `vitest-support` |

## Activation and status evidence

> [!success] ACTIVE
> Outside the Vite build graph: test support imported only by vitest files, directly or through other test support; it runs under `npm test` and is never in the app bundle.
>
> Test-import chain (from a vitest file): [[Reference/Desktop/TypeScript/fixtures/desks/lessons|src/fixtures/desks/lessons.ts]]

## Public API

- `export const FIXTURE_LESSON_ID = "fx_lesson_softmax"` — const, line 7
- `export const FIXTURE_ADDITIONS_PAD_ID = "fx_pad_lesson_adds"` — const, line 8
- `export const FIXTURE_LESSON_VIEW: LessonViewDto =` — const, line 11
- `export const FIXTURE_LESSON_SUMMARY: LessonSummaryDto =` — const, line 36
- `export function fixtureAdditionsPad(): PadViewDto` — function, line 48
- `export class FixtureLessons` — class, line 74

## Internal implementation anchors

- `const T = "2026-11-21T10:00:00Z"` — const, line 9
- `const block: PadBlockDto =` — const, line 49
- `function openingView(lessonId: string, goal: string): LessonViewDto` — function, line 64
- `const lessonId = `fx_lesson_opened_$` — const, line 88
- `const view = openingView(lessonId, "temperature in softmax")` — const, line 89
- `const view = this.views.get(String(input.lessonId)) ?? FIXTURE_LESSON_VIEW` — const, line 95
- `const view = this.views.get(input.lessonId)` — const, line 101
- `const all = [...this.summaries.values()].reverse()` — const, line 108

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/fixtures/desks/fakeCore|src/fixtures/desks/fakeCore.ts]] — import-or-re-export: `FIXTURE_LESSON_ID`, `FixtureLessons`, `fixtureAdditionsPad`; references `FIXTURE_LESSON_ID`, `FixtureLessons`, `fixtureAdditionsPad`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `LessonSummaryDto`, `LessonTurnInput`, `LessonViewDto`, `PadBlockDto`, `PadViewDto`

### Assets, platform, and third-party dependencies

No explicit asset, standard-library, package, or crate dependency was detected.

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/desks/notebook/LessonNotebook.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/desks/notebook/LessonNotebook.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/desks/lesson/lessonWindows.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/desks/lesson/lessonWindows.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/desks/lesson/deskLessons.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/desks/lesson/deskLessons.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).

## Modification guidance

- Change this source at its stated ownership boundary, then check every inbound consumer and outbound dependency listed above.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/fixtures/desks/lessons.ts](../../../../../../../apps/learnloop-tauri/src/fixtures/desks/lessons.ts) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

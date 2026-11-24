---
title: "Desktop module · src/screens/reader/activity.ts"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.reader.activity"
language: "TypeScript"
area: "TypeScript/screens/reader"
source_path: "apps/learnloop-tauri/src/screens/reader/activity.ts"
source_paths:
  - "apps/learnloop-tauri/src/screens/reader/activity.ts"
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

# `src/screens/reader/activity.ts`

Area: [[Reference/Desktop/TypeScript/screens/reader/_area|TypeScript/screens/reader]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides `setReaderActivityEnabled`, `readerActivityEnabled`, `newActivityId`, `flushReaderActivity` and related exports within the desktop's TypeScript/screens/reader ownership area.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/reader/activity.ts](../../../../../../../apps/learnloop-tauri/src/screens/reader/activity.ts) |
| Source lines | 120 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/reader/_area|TypeScript/screens/reader]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/reader/activity|src/screens/reader/activity.ts]]

## Public API

- `export function setReaderActivityEnabled(on: boolean): void` — function, line 26
- `export function readerActivityEnabled(): boolean` — function, line 35
- `export function newActivityId(): string` — function, line 39
- `export function flushReaderActivity(): void` — function, line 47
- `export function logReaderActivity(event: ReaderActivityEvent): void` — function, line 64
- `export function setNextReaderVisitInitiator(initiator: string, extractionId: string | null = null): void` — function, line 78
- `export function takeReaderVisitInitiator(extractionId: string | null = null): string` — function, line 82
- `export function logReaderAction( event: NonNullable<ReaderActivityEvent["event"]>, payload: ReaderActivityEvent["payload"], ): void` — function, line 90
- `export function noteLearnerActivity(kind: keyof typeof counters): void` — function, line 97
- `export function learnerActivitySnapshot(): Readonly<typeof counters>` — function, line 101
- `export function activitySince(before: Readonly<typeof counters>): Record<string, boolean>` — function, line 106
- `export function resetReaderActivityForTests(): void` — function, line 115

## Internal implementation anchors

- `const FLUSH_MS = 1500` — const, line 13
- `const MAX_BATCH = 200` — const, line 14
- `let enabled = false` — let, line 16
- `let queue: Array<` — let, line 19
- `let timer: ReturnType<typeof setTimeout> | null = null` — let, line 20
- `const counters =` — const, line 24
- `const key = vaultKey()` — const, line 50
- `const batch = queue.splice(0, MAX_BATCH).map((entry)` — const, line 53
- `const send = (api as` — const, line 55
- `let nextVisitInitiator:` — let, line 76
- `const pending = nextVisitInitiator` — const, line 83
- `const out: Record<string, boolean> =` — const, line 107

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] — import-or-re-export: `setNextReaderVisitInitiator`; references `setNextReaderVisitInitiator`
- [[Reference/Desktop/TypeScript/screens/desks/DeskShell|src/screens/desks/DeskShell.tsx]] — import-or-re-export: `logReaderAction`; references `logReaderAction`
- [[Reference/Desktop/TypeScript/screens/desks/companion/companionFigures|src/screens/desks/companion/companionFigures.tsx]] — import-or-re-export: `logReaderAction`; references `logReaderAction`
- [[Reference/Desktop/TypeScript/screens/desks/source/ScopedSource|src/screens/desks/source/ScopedSource.tsx]] — import-or-re-export: `activitySince`, `learnerActivitySnapshot`, `logReaderAction`, `logReaderActivity`, `newActivityId`; references `activitySince`, `learnerActivitySnapshot`, `logReaderAction`, `logReaderActivity`, `newActivityId`
- [[Reference/Desktop/TypeScript/screens/reader/SideBySidePane|src/screens/reader/SideBySidePane.tsx]] — import-or-re-export: `newActivityId`; references `newActivityId`
- [[Reference/Desktop/TypeScript/screens/reader/TutorOffers|src/screens/reader/TutorOffers.tsx]] — import-or-re-export: `logReaderAction`; references `logReaderAction`
- [[Reference/Desktop/TypeScript/screens/reader/correspondenceEvents|src/screens/reader/correspondenceEvents.ts]] — import-or-re-export: `logReaderAction`; references `logReaderAction`
- [[Reference/Desktop/TypeScript/screens/reader/figures/FigureInline|src/screens/reader/figures/FigureInline.tsx]] — import-or-re-export: `logReaderAction`; references `logReaderAction`
- [[Reference/Desktop/TypeScript/screens/reader/figures/sketch/SketchFigure|src/screens/reader/figures/sketch/SketchFigure.tsx]] — import-or-re-export: `logReaderAction`; references `logReaderAction`
- [[Reference/Desktop/TypeScript/screens/reader/useCueDiscovery|src/screens/reader/useCueDiscovery.ts]] — import-or-re-export: `newActivityId`; references `newActivityId`
- [[Reference/Desktop/TypeScript/screens/reader/useCueImpressions|src/screens/reader/useCueImpressions.ts]] — import-or-re-export: `newActivityId`; references `newActivityId`
- [[Reference/Desktop/TypeScript/screens/reader/useReaderCues|src/screens/reader/useReaderCues.ts]] — import-or-re-export: `logReaderAction`; references `logReaderAction`
- [[Reference/Desktop/TypeScript/screens/reader/useReaderInquiry|src/screens/reader/useReaderInquiry.ts]] — import-or-re-export: `activitySince`, `learnerActivitySnapshot`, `logReaderAction`, `logReaderActivity`, `newActivityId`, `noteLearnerActivity`; references `activitySince`, `learnerActivitySnapshot`, `logReaderAction`, `logReaderActivity`, `newActivityId`, `noteLearnerActivity`
- [[Reference/Desktop/TypeScript/screens/reader/useReaderVisit|src/screens/reader/useReaderVisit.ts]] — import-or-re-export: `flushReaderActivity`, `logReaderAction`, `logReaderActivity`, `newActivityId`, `noteLearnerActivity`, `setReaderActivityEnabled`, `takeReaderVisitInitiator`; references `flushReaderActivity`, `logReaderAction`, `logReaderActivity`, `newActivityId`, `noteLearnerActivity`, `setReaderActivityEnabled`, `takeReaderVisitInitiator`
- [[Reference/Desktop/TypeScript/screens/reader/useSideBySide|src/screens/reader/useSideBySide.ts]] — import-or-re-export: `logReaderAction`, `newActivityId`; references `logReaderAction`, `newActivityId`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `ReaderActivityEvent`
- [[Reference/Desktop/TypeScript/app/vaultTransition|src/app/vaultTransition.ts]] — import-or-re-export; imports `registerVaultDraft`, `vaultKey`

### Assets, platform, and third-party dependencies

No explicit asset, standard-library, package, or crate dependency was detected.

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Reader to Practice Workflow|Reader to Practice Workflow]] — owns the end-to-end reader sequence.
- [[Concepts/Reader Tutor and Teach-Back#Reader|Reader model]] — owns reader semantics.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/reader/useSideBySide.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/useSideBySide.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/reader/tutorSwitchOff.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/tutorSwitchOff.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/reader/tutorReader.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/tutorReader.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/reader/tutorExercises.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/tutorExercises.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/reader/tutorBoundAsk.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/tutorBoundAsk.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/reader/sideBySideReader.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/sideBySideReader.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/reader/sideBySideIntent.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/sideBySideIntent.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/reader/sideBySideCorrespondence.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/sideBySideCorrespondence.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [tests/test_sidecar_reader.py](../../../../../../../tests/test_sidecar_reader.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_sidecar_reader_pdf_view.py](../../../../../../../tests/test_sidecar_reader_pdf_view.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_reader_render_views.py](../../../../../../../tests/test_reader_render_views.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_reader_requests.py](../../../../../../../tests/test_reader_requests.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/screens/reader/activity.ts](../../../../../../../apps/learnloop-tauri/src/screens/reader/activity.ts) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

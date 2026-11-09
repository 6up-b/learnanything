---
title: "Desktop module · src/components/AsPrinted.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.components.AsPrinted"
language: "TypeScript"
area: "TypeScript/components"
source_path: "apps/learnloop-tauri/src/components/AsPrinted.tsx"
source_paths:
  - "apps/learnloop-tauri/src/components/AsPrinted.tsx"
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

# `src/components/AsPrinted.tsx`

Area: [[Reference/Desktop/TypeScript/components/_area|TypeScript/components]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides the reusable `AsPrinted` interaction surface used by one or more desktop workflows.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/components/AsPrinted.tsx](../../../../../../apps/learnloop-tauri/src/components/AsPrinted.tsx) |
| Source lines | 470 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/components/_area|TypeScript/components]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/FeedbackScreen|src/screens/FeedbackScreen.tsx]] → [[Reference/Desktop/TypeScript/components/AsPrinted|src/components/AsPrinted.tsx]]

## Public API

- `export const AS_PRINTED_COPY =` — const, line 25
- `export const AS_PRINTED_OPEN_KEY = "learnloop.asPrinted.open"` — const, line 45
- `export function useAsPrinted(practiceItemId: string | null | undefined): AsPrintedViewDto | null` — function, line 90
- `export type OriginalPageTarget =` — type, line 107
- `export function useProblemCrops( extractionId: string | null | undefined, spanIds: string[] | null | undefined, region?: PrintRegionDto | null, ): PrintedCropsDto | null` — function, line 115
- `export function printedPageInReader(page: OriginalPageTarget): IntentRestorationDto` — function, line 141
- `export function originalPageOfCrops(crops: PrintedCropsDto | null, sourceId?: string | null): OriginalPageTarget | null` — function, line 147
- `export function printedPageLabel(view: AsPrintedViewDto | null): string | null` — function, line 155
- `export function OriginalPageLink(` — function, line 160
- `export function AsPrinted(` — function, line 276
- `export function BlocksAsPrinted(` — function, line 376
- `export function PrintedAfterFeedback(` — function, line 434

## Internal implementation anchors

- `const ZOOMS = [1, 1.5, 2, 3] as const` — const, line 47
- `const linkStyle: CSSProperties =` — const, line 49
- `const toggleStyle: CSSProperties =` — const, line 61
- `function rememberedOpen(): boolean` — function, line 63
- `function rememberOpen(open: boolean): void` — function, line 71
- `function maybe<T>(run: ()` — function, line 80
- `const promise = run()` — const, line 82
- `let alive = true` — let, line 94
- `const promise = maybe(()` — const, line 95
- `const ids = spanIds ?? []` — const, line 120
- `const key = extractionId && ids.length ? `$` — const, line 121
- `let alive = true` — let, line 125
- `const promise = maybe(()` — const, line 126
- `const crops = key && state.key === key ? state.crops : null` — const, line 134
- `const first = crops.crops[0]` — const, line 149
- `const outline = crops.crops.filter((crop)` — const, line 150
- `const target = view.originalPage` — const, line 171
- `type Crop =` — type, line 180
- `function PrintedFrame(` — function, line 182
- `const images = crops.filter((crop)` — const, line 184
- `const said = notice ?? (status === "no_geometry" ? AS_PRINTED_COPY.noCrop : status === "no_original" || status === "not_found" ? AS_PRINTED_COPY.noOriginal : AS_PRINTED_COPY.failed)` — const, line 188
- `function TranscriptionReport(` — function, line 220
- `const send = async ()` — const, line 224
- `function photoDate(capturedAt: string | null | undefined): string | null` — function, line 268
- `const date = new Date(capturedAt)` — const, line 270
- `const asked = useRef<string | null>(null)` — const, line 292
- `const kind = view?.kind ?? "none"` — const, line 293
- `const figure = kind === "figure"` — const, line 294
- `const key = `$` — const, line 300
- `const promise = maybe(()` — const, line 304
- `const toggle = ()` — const, line 316
- `const taken = kind === "photo" ? photoDate(view.photo?.capturedAt) : null` — const, line 322
- `const label = kind === "photo" ? `$` — const, line 323
- `const rendered = crops.view && crops.view.kind === kind ? crops.view : null` — const, line 327
- `function PhotoFrame(` — function, line 349
- `let alive = true` — let, line 353
- `const promise = maybe(()` — const, line 354
- `const own = useProblemCrops(probe === undefined ? extractionId : null, spanIds, region)` — const, line 393
- `const known = probe === undefined ? own : probe` — const, line 394
- `const key = `$` — const, line 397
- `const asked = useRef<string | null>(null)` — const, line 398
- `const promise = maybe(()` — const, line 403
- `const view = useAsPrinted(practiceItemId)` — const, line 444
- `const locator = view.kind === "page" && view.locator ? [view.locator.exerciseLabel?.trim(), `$` — const, line 447

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/FeedbackScreen|src/screens/FeedbackScreen.tsx]] — import-or-re-export: `PrintedAfterFeedback`, `printedPageInReader`; references `PrintedAfterFeedback`, `printedPageInReader`
- [[Reference/Desktop/TypeScript/screens/MaintenanceScreen|src/screens/MaintenanceScreen.tsx]] — import-or-re-export: `AsPrinted`, `useAsPrinted`; references `AsPrinted`, `useAsPrinted`
- [[Reference/Desktop/TypeScript/screens/PracticeScreen|src/screens/PracticeScreen.tsx]] — import-or-re-export: `AS_PRINTED_COPY`, `AsPrinted`, `OriginalPageLink`, `printedPageLabel`, `useAsPrinted`; references `AS_PRINTED_COPY`, `AsPrinted`, `OriginalPageLink`, `printedPageLabel`, `useAsPrinted`
- [[Reference/Desktop/TypeScript/screens/feedback/CompareMethods|src/screens/feedback/CompareMethods.tsx]] — import-or-re-export: `AS_PRINTED_COPY`, `BlocksAsPrinted`; references `AS_PRINTED_COPY`, `BlocksAsPrinted`
- [[Reference/Desktop/TypeScript/screens/reader/ExerciseCandidates (tsx)|src/screens/reader/ExerciseCandidates.tsx]] — import-or-re-export: `BlocksAsPrinted`; references `BlocksAsPrinted`
- [[Reference/Desktop/TypeScript/screens/workbench/Workbench|src/screens/workbench/Workbench.tsx]] — import-or-re-export: `AS_PRINTED_COPY`, `AsPrinted`, `BlocksAsPrinted`, `OriginalPageTarget`, `originalPageOfCrops`, `useAsPrinted`, `useProblemCrops`; references `AS_PRINTED_COPY`, `AsPrinted`, `BlocksAsPrinted`, `OriginalPageTarget`, `originalPageOfCrops`, `useAsPrinted`, `useProblemCrops`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `AsPrintedViewDto`, `IntentRestorationDto`, `PrintRegionDto`, `PrintedCropsDto`
- [[Reference/Desktop/TypeScript/components/OpenInSource|src/components/OpenInSource.tsx]] — import-or-re-export; imports `OpenInSource`
- [[Reference/Desktop/TypeScript/components/term|src/components/term.tsx]] — import-or-re-export; imports `COLOR`, `FONT_MONO`
- [[Reference/Desktop/TypeScript/errors|src/errors.ts]] — import-or-re-export; imports `errorMessage`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/components/AsPrinted.test.tsx](../../../../../../apps/learnloop-tauri/src/components/AsPrinted.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/components/AsPrinted.tsx](../../../../../../apps/learnloop-tauri/src/components/AsPrinted.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

---
title: "Desktop module · src/screens/reader/TutorOffers.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.reader.TutorOffers"
language: "TypeScript"
area: "TypeScript/screens/reader"
source_path: "apps/learnloop-tauri/src/screens/reader/TutorOffers.tsx"
source_paths:
  - "apps/learnloop-tauri/src/screens/reader/TutorOffers.tsx"
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

# `src/screens/reader/TutorOffers.tsx`

Area: [[Reference/Desktop/TypeScript/screens/reader/_area|TypeScript/screens/reader]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Implements the `TutorOffers` routed desktop screen and coordinates its learner-facing workflow state.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/reader/TutorOffers.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/TutorOffers.tsx) |
| Source lines | 602 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/reader/_area|TypeScript/screens/reader]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]] → [[Reference/Desktop/TypeScript/screens/reader/TutorOffers|src/screens/reader/TutorOffers.tsx]]

## Public API

- `export const OFFER_COPY =` — const, line 68
- `export const MAX_SHOWN = 3` — const, line 92
- `export type OfferKind = "practice" | "passages" | "compare" | "try_next_step" | "make_explorable" | "show_me"` — type, line 94
- `export interface OfferItem` — interface, line 97
- `export interface TutorOfferStore` — interface, line 141
- `export function createTutorOfferStore(): TutorOfferStore` — function, line 148
- `export const defaultTutorOfferStore = createTutorOfferStore()` — const, line 170
- `export interface TutorOffersProps` — interface, line 172
- `export function compareTableFromRun(run: SourceToolRunDto): CompareTableDto` — function, line 276
- `export function TutorOffers(props: TutorOffersProps)` — function, line 367

## Internal implementation anchors

- `interface Lookup` — interface, line 102
- `interface Offer` — interface, line 117
- `interface ExchangeOffersState` — interface, line 129
- `const STORE_CAP = 200` — const, line 146
- `const states = new Map<string, ExchangeOffersState>()` — const, line 149
- `let state = states.get(exchangeId)` — let, line 152
- `const oldest = states.keys().next().value` — const, line 157
- `function offersFor(props: TutorOffersProps): Offer[]` — function, line 201
- `const requests = props.toolRequests ?? []` — const, line 202
- `const offers: Offer[] = []` — const, line 203
- `const practiceRequests = requests.filter((request)` — const, line 204
- `const goal = (props.buttons ?? []).find((button)` — const, line 237
- `function uncheckedBecause(status: string): string | null` — function, line 247
- `function succeeded(status: string | undefined): boolean` — function, line 257
- `function practiceLookup(items: OfferItem[], proposalId: string | null, status: string | undefined, run?: SourceToolRunDto, practice?: FindPracticeResultDto): Lookup` — function, line 261
- `const visible = items.slice(0, MAX_SHOWN)` — const, line 263
- `const kept = practice ?` — const, line 264
- `const result = run.result` — const, line 277
- `const sources = result.sources ?? []` — const, line 278
- `const byRef = new Map(sources.map((source)` — const, line 279
- `const relations = (result.relations ?? []) as Array<Record<string, unknown>>` — const, line 280
- `const text = (value: unknown)` — const, line 281
- `const rows = sources.map((source)` — const, line 282
- `const assumes: CompareTableDto["rows"][number]["assumes"] = []` — const, line 283
- `const differs: CompareTableDto["rows"][number]["differs"] = []` — const, line 284
- `const left = text(relation.leftRef)` — const, line 286
- `const right = text(relation.rightRef)` — const, line 287
- `const otherRef = left === source.ref ? right : left` — const, line 289
- `const cell =` — const, line 290
- `const status = result.status ?? "ok"` — const, line 312
- `async function runLookup(offer: Offer, withExercises: boolean): Promise<Lookup>` — function, line 328
- `const result: FindPracticeResultDto = await api.findPractice(` — const, line 330
- `const items = result.items.map((item)` — const, line 331
- `const run = await api.runSourceTool(offer.toolCallId ?? "")` — const, line 334
- `const status = run.result.status` — const, line 335
- `const items = (run.result.items ?? []).map((item)` — const, line 337
- `const passages = run.result.passages ?? []` — const, line 342
- `const table = compareTableFromRun(run)` — const, line 352
- `const missing = run.result.missingPerspectives ?? []` — const, line 353
- `const buttonStyle =` — const, line 358
- `function notify(state: ExchangeOffersState)` — function, line 363
- `const store = props.store ?? defaultTutorOfferStore` — const, line 368
- `const state = store.get(props.exchangeId)` — const, line 369
- `const offers = offersFor(props)` — const, line 370
- `const settle = (key: string, lookup: Lookup)` — const, line 373
- `const start = (offer: Offer)` — const, line 378
- `const lookup = state.lookups[offer.key]` — const, line 413
- `const press = (offer: Offer)` — const, line 432
- `const lookup = state.lookups[offer.key]` — const, line 433
- `const opensBeside = offer.kind === "compare" && Boolean(props.onCompare)` — const, line 434
- `const query = offer.request.arguments?.query` — const, line 456
- `const retry = lookup?.phase === "failed" || lookup?.phase === "unchecked"` — const, line 469
- `const lookup = state.lookups[offer.key]` — const, line 476
- `const isPressed = state.pressed.has(offer.key)` — const, line 477
- `const retryable = lookup?.phase === "failed" || lookup?.phase === "unchecked"` — const, line 501
- `function OfferResult(` — function, line 539
- `const withExercises = Boolean(exercises && lookup.practice)` — const, line 544

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]] — import-or-re-export: `createTutorOfferStore`; references `createTutorOfferStore`
- [[Reference/Desktop/TypeScript/screens/reader/TutorAnswer|src/screens/reader/TutorAnswer.tsx]] — import-or-re-export: `OfferItem`, `TutorOfferStore`, `TutorOffers`; references `OfferItem`, `TutorOfferStore`, `TutorOffers`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `CompareTableDto`, `FindPracticeResultDto`, `PracticeRequestDto`, `ReaderTutorButtonDto`, `SourcePassageDto`, `SourceToolRequestDto`, `SourceToolRunDto`
- [[Reference/Desktop/TypeScript/components/term|src/components/term.tsx]] — import-or-re-export; imports `COLOR`, `FONT_MONO`
- [[Reference/Desktop/TypeScript/screens/reader/CompareKeep|src/screens/reader/CompareKeep.tsx]] — import-or-re-export; imports `CompareKeep`
- [[Reference/Desktop/TypeScript/screens/reader/LibraryAnswer|src/screens/reader/LibraryAnswer.tsx]] — import-or-re-export; imports `CompareTable`
- [[Reference/Desktop/TypeScript/screens/reader/ProposalExercises|src/screens/reader/ProposalExercises.tsx]] — import-or-re-export; imports `LibraryExercisesProps`, `ProposalExercises`
- [[Reference/Desktop/TypeScript/screens/reader/activity|src/screens/reader/activity.ts]] — import-or-re-export; imports `logReaderAction`
- [[Reference/Desktop/TypeScript/screens/reader/exerciseCandidates (ts)|src/screens/reader/exerciseCandidates.ts]] — import-or-re-export; imports `practiceFromToolRun`
- [[Reference/Desktop/TypeScript/screens/reader/readerShared|src/screens/reader/readerShared.ts]] — import-or-re-export; imports `clip`
- [[Reference/Desktop/TypeScript/screens/reader/voices|src/screens/reader/voices.tsx]] — import-or-re-export; imports `MeaningLabel`, `ModelVoice`, `SourceVoice`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Reader to Practice Workflow|Reader to Practice Workflow]] — owns the end-to-end reader sequence.
- [[Concepts/Reader Tutor and Teach-Back#Reader|Reader model]] — owns reader semantics.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/reader/tutorReview.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/tutorReview.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/reader/tutorExercises.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/tutorExercises.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/reader/figures/tutorOfferPress.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/figures/tutorOfferPress.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/reader/figures/showMe.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/figures/showMe.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/reader/figures/advancedPanels.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/figures/advancedPanels.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/reader/compareScope.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/compareScope.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/reader/compareKeepSwitchOff.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/compareKeepSwitchOff.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/reader/compareKeep.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/compareKeep.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
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

1. Modify [apps/learnloop-tauri/src/screens/reader/TutorOffers.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/TutorOffers.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

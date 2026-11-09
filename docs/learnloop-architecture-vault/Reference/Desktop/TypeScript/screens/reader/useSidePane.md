---
title: "Desktop module · src/screens/reader/useSidePane.ts"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.reader.useSidePane"
language: "TypeScript"
area: "TypeScript/screens/reader"
source_path: "apps/learnloop-tauri/src/screens/reader/useSidePane.ts"
source_paths:
  - "apps/learnloop-tauri/src/screens/reader/useSidePane.ts"
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

# `src/screens/reader/useSidePane.ts`

Area: [[Reference/Desktop/TypeScript/screens/reader/_area|TypeScript/screens/reader]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides `PaneCaptureTarget`, `SidePaneInput`, `useSidePane`, `SidePane` and related exports within the desktop's TypeScript/screens/reader ownership area.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/reader/useSidePane.ts](../../../../../../../apps/learnloop-tauri/src/screens/reader/useSidePane.ts) |
| Source lines | 330 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/reader/_area|TypeScript/screens/reader]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]] → [[Reference/Desktop/TypeScript/screens/reader/useSidePane|src/screens/reader/useSidePane.ts]]

## Public API

- `export interface PaneCaptureTarget` — interface, line 46
- `export interface SidePaneInput` — interface, line 57
- `export function useSidePane(input: SidePaneInput)` — function, line 95
- `export type SidePane = ReturnType<typeof useSidePane>` — type, line 197
- `export function inSidePane(target: EventTarget | null): boolean` — function, line 328

## Internal implementation anchors

- `const noop = ()` — const, line 93
- `const extractionId = shown && section ? section.extractionId : null` — const, line 99
- `const sourceId = shown && section ? section.sourceId : null` — const, line 100
- `const sectionKey = extractionId && section ? `$` — const, line 101
- `const box = useIntentBox(` — const, line 104
- `const noteSelection = useCallback((picked: PaneSelection | null)` — const, line 121
- `const releaseKeys = useCallback(()` — const, line 129
- `const showPath = useCallback(()` — const, line 149
- `const closePath = useCallback(()` — const, line 154
- `const pathShown = pathFor !== null && pathFor === extractionId` — const, line 155
- `const active = useActiveReading(` — const, line 157
- `const figures = useFigures(` — const, line 163
- `const target: PaneCaptureTarget | null = section && extractionId && selection && section.revisionId ?` — const, line 165
- `const fold = useCallback((spanIds: string[], foldBlocks: number): string[]` — const, line 172
- `const blocks = section?.blocks ?? []` — const, line 173
- `const positions = spanIds.map((spanId)` — const, line 174
- `const last = Math.max(...positions)` — const, line 176
- `const marksChanged = useCallback(()` — const, line 182
- `const cues = useSidePaneCues(` — const, line 184
- `function useSidePaneCues(` — function, line 210
- `const generation = useRef(0)` — const, line 230
- `const readFor = useRef<string | null>(null)` — const, line 235
- `const reloadPending = useRef(false)` — const, line 241
- `const read = useCallback(async (force: boolean)` — const, line 242
- `const mine = generation.current` — const, line 244
- `const next = await readGuidePlan(sourceId, extractionId, force ?` — const, line 250
- `const again = readFor.current === extractionId && extractionId !== null` — const, line 258
- `const pending = extractionId !== null && reloadPending.current` — const, line 261
- `const reloadPlan = useCallback(()` — const, line 265
- `const reloadBoth = useCallback(async ()` — const, line 268
- `const body = hostRef.current` — const, line 278
- `let last: string | null = null` — let, line 280
- `const observer = new ResizeObserver(()` — const, line 281
- `const size = `$` — const, line 282
- `const render = useMemo(()` — const, line 292
- `const spanOrder = useMemo( ()` — const, line 294
- `const blocksKey = (blocks ?? []).map((block)` — const, line 296
- `const jumpToSpan = useCallback((spanId: string)` — const, line 298
- `const node = Array.from(hostRef.current?.querySelectorAll<HTMLElement>("[data-sbs-span]") ?? []) .find((element)` — const, line 299
- `const ownsKey = useCallback((event: KeyboardEvent)` — const, line 304
- `const sideVisitPayload = useCallback(()` — const, line 306
- `const ownVisit = useCallback(()` — const, line 310
- `const cueCtl = useReaderCues(` — const, line 312

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]] — import-or-re-export: `PaneCaptureTarget`, `SidePane`, `inSidePane`, `useSidePane`; references `PaneCaptureTarget`, `SidePane`, `inSidePane`, `useSidePane`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `ReaderGuidePlanDto`, `ReaderIntentActionDto`, `ReaderIntentContractDto`, `SideBySideSectionDto`
- [[Reference/Desktop/TypeScript/screens/reader/SideBySidePane|src/screens/reader/SideBySidePane.tsx]] — import-or-re-export; imports `PaneSelection`
- [[Reference/Desktop/TypeScript/screens/reader/figures/useFigures|src/screens/reader/figures/useFigures.ts]] — import-or-re-export; imports `FiguresContract`, `useFigures`
- [[Reference/Desktop/TypeScript/screens/reader/guidePlan|src/screens/reader/guidePlan.ts]] — import-or-re-export; imports `readGuidePlan`
- [[Reference/Desktop/TypeScript/screens/reader/useActiveReading|src/screens/reader/useActiveReading.ts]] — import-or-re-export; imports `useActiveReading`
- [[Reference/Desktop/TypeScript/screens/reader/useIntentBox|src/screens/reader/useIntentBox.ts]] — import-or-re-export; imports `IntentCancel`, `IntentRunHandle`, `IntentRunHow`, `useIntentBox`
- [[Reference/Desktop/TypeScript/screens/reader/useReaderCues|src/screens/reader/useReaderCues.ts]] — import-or-re-export; imports `CueCheckMeRequest`, `CueRequestOrigin`, `useReaderCues`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Reader to Practice Workflow|Reader to Practice Workflow]] — owns the end-to-end reader sequence.
- [[Concepts/Reader Tutor and Teach-Back#Reader|Reader model]] — owns reader semantics.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

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

1. Modify [apps/learnloop-tauri/src/screens/reader/useSidePane.ts](../../../../../../../apps/learnloop-tauri/src/screens/reader/useSidePane.ts) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

---
title: "Desktop module · src/screens/reader/useIntentBox.ts"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.reader.useIntentBox"
language: "TypeScript"
area: "TypeScript/screens/reader"
source_path: "apps/learnloop-tauri/src/screens/reader/useIntentBox.ts"
source_paths:
  - "apps/learnloop-tauri/src/screens/reader/useIntentBox.ts"
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

# `src/screens/reader/useIntentBox.ts`

Area: [[Reference/Desktop/TypeScript/screens/reader/_area|TypeScript/screens/reader]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides `SHOW_AFTER_MS`, `IntentRunHow`, `IntentRunHandle`, `IntentCancel` and related exports within the desktop's TypeScript/screens/reader ownership area.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/reader/useIntentBox.ts](../../../../../../../apps/learnloop-tauri/src/screens/reader/useIntentBox.ts) |
| Source lines | 456 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/reader/_area|TypeScript/screens/reader]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]] → [[Reference/Desktop/TypeScript/screens/reader/useIntentBox|src/screens/reader/useIntentBox.ts]]

## Public API

- `export const SHOW_AFTER_MS = 150` — const, line 30
- `export type IntentRunHow =` — type, line 36
- `export interface IntentRunHandle` — interface, line 39
- `export interface IntentCancel` — interface, line 45
- `export interface IntentBoxPosition` — interface, line 51
- `export const FALLBACK_ASK: ReaderIntentActionDto =` — const, line 58
- `export interface UseIntentBoxArgs` — interface, line 69
- `export function useIntentBox(args: UseIntentBoxArgs)` — function, line 90
- `export type IntentBoxController = ReturnType<typeof useIntentBox>` — type, line 456

## Internal implementation anchors

- `const POLL_WAIT_MS = 250` — const, line 32
- `const BOX_WIDTH = 360` — const, line 33
- `const BOX_HEIGHT = 86` — const, line 34
- `interface Speculation` — interface, line 62
- `function isEditable(target: EventTarget | null): boolean` — function, line 86
- `const enabled = contract !== null && extractionId !== null` — const, line 92
- `const inputRef = useRef<HTMLInputElement | null>(null)` — const, line 101
- `const boxRef = useRef<HTMLDivElement | null>(null)` — const, line 102
- `const showTimer = useRef<number | null>(null)` — const, line 103
- `const specTimer = useRef<number | null>(null)` — const, line 104
- `const speculation = useRef<Speculation | null>(null)` — const, line 105
- `const lastRun = useRef<Promise<IntentRunHandle | null>>(Promise.resolve(null))` — const, line 106
- `const focusPalette = useRef(false)` — const, line 107
- `const epoch = useRef(0)` — const, line 108
- `const latest = useRef(` — const, line 109
- `const groups = contract ? visiblePalette(contract,` — const, line 112
- `const actionsRef = useRef<ReaderIntentActionDto[]>([])` — const, line 113
- `const clearTimers = useCallback(()` — const, line 116
- `const discard = useCallback((spec: Speculation | null)` — const, line 126
- `const discardSpeculation = useCallback(()` — const, line 132
- `const spec = speculation.current` — const, line 133
- `const reset = useCallback(()` — const, line 138
- `const close = useCallback(()` — const, line 150
- `const place = useCallback(()` — const, line 159
- `const host = hostRef.current` — const, line 160
- `const hostRect = host.getBoundingClientRect()` — const, line 162
- `let rect: DOMRect | null = null` — let, line 163
- `const sel = window.getSelection()` — const, line 164
- `const range = sel.getRangeAt(0)` — const, line 166
- `const last = latest.current.spanIds[latest.current.spanIds.length - 1]` — const, line 170
- `const element = last // Reader CA6b: the second pane marks its passages data-sbs-span. ? Array.from(host.querySelectorAll<HTMLElement>("[data-span-id], [data-sbs-span]")).find((node)` — const, line 171
- `const above = rect.bottom + BOX_HEIGHT + 8 > hostRect.bottom && rect.top - BOX_HEIGHT - 8 > hostRect.top` — const, line 178
- `const top = (above ? rect.top - BOX_HEIGHT - 6 : rect.bottom + 6) - hostRect.top + host.scrollTop` — const, line 179
- `const maxLeft = Math.max(8, host.clientWidth - BOX_WIDTH - 8)` — const, line 180
- `const left = Math.min(Math.max(8, rect.left - hostRect.left + host.scrollLeft), maxLeft)` — const, line 181
- `const show = useCallback(()` — const, line 185
- `const noteSelection = useCallback(()` — const, line 192
- `const noteSelectionCleared = useCallback(()` — const, line 204
- `const settle = useCallback(async (first: ReaderIntentRoutingDto): Promise<ReaderIntentRoutingDto | null>` — const, line 210
- `const deadline = Date.now() + ((contract?.timeoutSeconds ?? 4) + 1) * 1000` — const, line 211
- `let current = first` — let, line 212
- `const speculate = useCallback((words: string)` — const, line 219
- `const where = latest.current` — const, line 220
- `const first = api .readerRouteIntent(` — const, line 222
- `const started = first.then((answer)` — const, line 227
- `const result = first.then((answer)` — const, line 228
- `const setText = useCallback((value: string)` — const, line 232
- `const words = value.trim()` — const, line 236
- `const actionFor = useCallback((routing: ReaderIntentRoutingDto | null):` — const, line 247
- `const offered = actionsRef.current.find((action)` — const, line 249
- `const submit = useCallback(async ()` — const, line 253
- `const words = text.trim()` — const, line 254
- `const ask = actionsRef.current.find((action)` — const, line 258
- `const mine = ++epoch.current` — const, line 266
- `let routing: ReaderIntentRoutingDto | null = null` — let, line 269
- `const spec = speculation.current` — const, line 271
- `const where = latest.current` — const, line 280
- `const first = await api.readerRouteIntent(` — const, line 281
- `const ran = substituted ? null : routing` — const, line 302
- `const openPalette = useCallback(()` — const, line 308
- `const change = useCallback(()` — const, line 322
- `const pick = useCallback((action: ReaderIntentActionDto)` — const, line 331
- `const words = text.trim()` — const, line 335
- `const hub = useListenerHub()` — const, line 346
- `const onKey = (event: KeyboardEvent)` — const, line 349
- `const input = inputRef.current` — const, line 351
- `const inBox = input !== null && event.target === input` — const, line 352
- `const onPaletteButton = event.target instanceof HTMLButtonElement && (boxRef.current?.contains(event.target) ?? false)` — const, line 355
- `const buttons = Array.from(boxRef.current?.querySelectorAll<HTMLButtonElement>("[data-intent-action]") ?? [])` — const, line 357
- `const at = onPaletteButton ? buttons.indexOf(event.target as HTMLButtonElement) : -1` — const, line 361
- `const step = event.key === "ArrowDown" || event.key === "ArrowRight" ? 1 : -1` — const, line 362
- `const target = event.target` — const, line 371
- `const onReading = !(target instanceof Element) || target === document.body || (hostRef.current?.contains(target) ?? false)` — const, line 372
- `const onDown = (event: MouseEvent)` — const, line 435

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]] — import-or-re-export: `IntentCancel`, `IntentRunHandle`, `IntentRunHow`, `useIntentBox`; references `IntentCancel`, `IntentRunHandle`, `IntentRunHow`, `useIntentBox`
- [[Reference/Desktop/TypeScript/screens/reader/IntentBox|src/screens/reader/IntentBox.tsx]] — import-or-re-export: `IntentBoxController`; references `IntentBoxController`
- [[Reference/Desktop/TypeScript/screens/reader/SideBySidePane|src/screens/reader/SideBySidePane.tsx]] — import-or-re-export: `IntentBoxController`; references `IntentBoxController`
- [[Reference/Desktop/TypeScript/screens/reader/useSidePane|src/screens/reader/useSidePane.ts]] — import-or-re-export: `IntentCancel`, `IntentRunHandle`, `IntentRunHow`, `useIntentBox`; references `IntentCancel`, `IntentRunHandle`, `IntentRunHow`, `useIntentBox`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `ReaderIntentActionDto`, `ReaderIntentContractDto`, `ReaderIntentRoutingDto`
- [[Reference/Desktop/TypeScript/app/keymap|src/app/keymap.ts]] — import-or-re-export; imports `screenLeavesKey`
- [[Reference/Desktop/TypeScript/screens/desks/lifecycle|src/screens/desks/lifecycle.tsx]] — import-or-re-export; imports `useListenerHub`
- [[Reference/Desktop/TypeScript/screens/reader/ModelActionState|src/screens/reader/ModelActionState.tsx]] — import-or-re-export; imports `ModelActionPhase`, `phaseForError`
- [[Reference/Desktop/TypeScript/screens/reader/intentPalette|src/screens/reader/intentPalette.ts]] — import-or-re-export; imports `paletteActions`, `visiblePalette`
- [[Reference/Desktop/TypeScript/screens/reader/readerShared|src/screens/reader/readerShared.ts]] — import-or-re-export; imports `passageKeys`

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

1. Modify [apps/learnloop-tauri/src/screens/reader/useIntentBox.ts](../../../../../../../apps/learnloop-tauri/src/screens/reader/useIntentBox.ts) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

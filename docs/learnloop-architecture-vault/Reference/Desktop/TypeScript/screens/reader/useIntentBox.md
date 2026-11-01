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
source_commit: "0c5bc9546b622e4d87b7075f53b026c74b9e5462"
source_commit_timestamp: "2026-11-01T02:25:38-05:00"
source_worktree_state: "clean"
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
| Source lines | 453 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/reader/_area|TypeScript/screens/reader]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `0c5bc9546b622e4d87b7075f53b026c74b9e5462` |
| Commit timestamp | `2026-11-01T02:25:38-05:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]] → [[Reference/Desktop/TypeScript/screens/reader/useIntentBox|src/screens/reader/useIntentBox.ts]]

## Public API

- `export const SHOW_AFTER_MS = 150` — const, line 28
- `export type IntentRunHow =` — type, line 34
- `export interface IntentRunHandle` — interface, line 37
- `export interface IntentCancel` — interface, line 43
- `export interface IntentBoxPosition` — interface, line 49
- `export const FALLBACK_ASK: ReaderIntentActionDto =` — const, line 56
- `export interface UseIntentBoxArgs` — interface, line 67
- `export function useIntentBox(args: UseIntentBoxArgs)` — function, line 88
- `export type IntentBoxController = ReturnType<typeof useIntentBox>` — type, line 453

## Internal implementation anchors

- `const POLL_WAIT_MS = 250` — const, line 30
- `const BOX_WIDTH = 360` — const, line 31
- `const BOX_HEIGHT = 86` — const, line 32
- `interface Speculation` — interface, line 60
- `function isEditable(target: EventTarget | null): boolean` — function, line 84
- `const enabled = contract !== null && extractionId !== null` — const, line 90
- `const inputRef = useRef<HTMLInputElement | null>(null)` — const, line 99
- `const boxRef = useRef<HTMLDivElement | null>(null)` — const, line 100
- `const showTimer = useRef<number | null>(null)` — const, line 101
- `const specTimer = useRef<number | null>(null)` — const, line 102
- `const speculation = useRef<Speculation | null>(null)` — const, line 103
- `const lastRun = useRef<Promise<IntentRunHandle | null>>(Promise.resolve(null))` — const, line 104
- `const focusPalette = useRef(false)` — const, line 105
- `const epoch = useRef(0)` — const, line 106
- `const latest = useRef(` — const, line 107
- `const groups = contract ? visiblePalette(contract,` — const, line 110
- `const actionsRef = useRef<ReaderIntentActionDto[]>([])` — const, line 111
- `const clearTimers = useCallback(()` — const, line 114
- `const discard = useCallback((spec: Speculation | null)` — const, line 124
- `const discardSpeculation = useCallback(()` — const, line 130
- `const spec = speculation.current` — const, line 131
- `const reset = useCallback(()` — const, line 136
- `const close = useCallback(()` — const, line 148
- `const place = useCallback(()` — const, line 157
- `const host = hostRef.current` — const, line 158
- `const hostRect = host.getBoundingClientRect()` — const, line 160
- `let rect: DOMRect | null = null` — let, line 161
- `const sel = window.getSelection()` — const, line 162
- `const range = sel.getRangeAt(0)` — const, line 164
- `const last = latest.current.spanIds[latest.current.spanIds.length - 1]` — const, line 168
- `const element = last // Reader CA6b: the second pane marks its passages data-sbs-span. ? Array.from(host.querySelectorAll<HTMLElement>("[data-span-id], [data-sbs-span]")).find((node)` — const, line 169
- `const above = rect.bottom + BOX_HEIGHT + 8 > hostRect.bottom && rect.top - BOX_HEIGHT - 8 > hostRect.top` — const, line 176
- `const top = (above ? rect.top - BOX_HEIGHT - 6 : rect.bottom + 6) - hostRect.top + host.scrollTop` — const, line 177
- `const maxLeft = Math.max(8, host.clientWidth - BOX_WIDTH - 8)` — const, line 178
- `const left = Math.min(Math.max(8, rect.left - hostRect.left + host.scrollLeft), maxLeft)` — const, line 179
- `const show = useCallback(()` — const, line 183
- `const noteSelection = useCallback(()` — const, line 190
- `const noteSelectionCleared = useCallback(()` — const, line 202
- `const settle = useCallback(async (first: ReaderIntentRoutingDto): Promise<ReaderIntentRoutingDto | null>` — const, line 208
- `const deadline = Date.now() + ((contract?.timeoutSeconds ?? 4) + 1) * 1000` — const, line 209
- `let current = first` — let, line 210
- `const speculate = useCallback((words: string)` — const, line 217
- `const where = latest.current` — const, line 218
- `const first = api .readerRouteIntent(` — const, line 220
- `const started = first.then((answer)` — const, line 224
- `const result = first.then((answer)` — const, line 225
- `const setText = useCallback((value: string)` — const, line 229
- `const words = value.trim()` — const, line 233
- `const actionFor = useCallback((routing: ReaderIntentRoutingDto | null):` — const, line 244
- `const offered = actionsRef.current.find((action)` — const, line 246
- `const submit = useCallback(async ()` — const, line 250
- `const words = text.trim()` — const, line 251
- `const ask = actionsRef.current.find((action)` — const, line 255
- `const mine = ++epoch.current` — const, line 263
- `let routing: ReaderIntentRoutingDto | null = null` — let, line 266
- `const spec = speculation.current` — const, line 268
- `const where = latest.current` — const, line 277
- `const first = await api.readerRouteIntent(` — const, line 278
- `const ran = substituted ? null : routing` — const, line 298
- `const openPalette = useCallback(()` — const, line 304
- `const change = useCallback(()` — const, line 318
- `const pick = useCallback((action: ReaderIntentActionDto)` — const, line 327
- `const words = text.trim()` — const, line 331
- `const onKey = (event: KeyboardEvent)` — const, line 344
- `const input = inputRef.current` — const, line 346
- `const inBox = input !== null && event.target === input` — const, line 347
- `const onPaletteButton = event.target instanceof HTMLButtonElement && (boxRef.current?.contains(event.target) ?? false)` — const, line 350
- `const buttons = Array.from(boxRef.current?.querySelectorAll<HTMLButtonElement>("[data-intent-action]") ?? [])` — const, line 352
- `const at = onPaletteButton ? buttons.indexOf(event.target as HTMLButtonElement) : -1` — const, line 356
- `const step = event.key === "ArrowDown" || event.key === "ArrowRight" ? 1 : -1` — const, line 357
- `const target = event.target` — const, line 366
- `const onReading = !(target instanceof Element) || target === document.body || (hostRef.current?.contains(target) ?? false)` — const, line 367
- `const onDown = (event: MouseEvent)` — const, line 431

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
- [[Reference/Desktop/TypeScript/screens/reader/ModelActionState|src/screens/reader/ModelActionState.tsx]] — import-or-re-export; imports `ModelActionPhase`, `phaseForError`
- [[Reference/Desktop/TypeScript/screens/reader/intentPalette|src/screens/reader/intentPalette.ts]] — import-or-re-export; imports `paletteActions`, `visiblePalette`

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

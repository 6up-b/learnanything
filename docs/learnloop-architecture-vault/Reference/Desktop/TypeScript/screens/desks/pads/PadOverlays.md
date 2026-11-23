---
title: "Desktop module · src/screens/desks/pads/PadOverlays.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.desks.pads.PadOverlays"
language: "TypeScript"
area: "TypeScript/screens/desks/pads"
source_path: "apps/learnloop-tauri/src/screens/desks/pads/PadOverlays.tsx"
source_paths:
  - "apps/learnloop-tauri/src/screens/desks/pads/PadOverlays.tsx"
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

# `src/screens/desks/pads/PadOverlays.tsx`

Area: [[Reference/Desktop/TypeScript/screens/desks/pads/_area|TypeScript/screens/desks/pads]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Implements the `PadOverlays` routed desktop screen and coordinates its learner-facing workflow state.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/desks/pads/PadOverlays.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/desks/pads/PadOverlays.tsx) |
| Source lines | 366 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/desks/pads/_area|TypeScript/screens/desks/pads]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/DeskShell|src/screens/desks/DeskShell.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/pads/PadStackWindow|src/screens/desks/pads/PadStackWindow.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/pads/PadOverlays|src/screens/desks/pads/PadOverlays.tsx]]

## Public API

- `export interface MenuRequest` — interface, line 10
- `export function PadMenu(` — function, line 41
- `export function ArrangeOverlay(` — function, line 208
- `export function SubmitSheet(` — function, line 301

## Internal implementation anchors

- `type InsertBlock =` — type, line 18
- `interface Row` — interface, line 20
- `function anchorsOf(state: PadState | null, blockId: string | null): Array<` — function, line 30
- `const block = state.blocks.find((each)` — const, line 32
- `const fromLinks = state.anchors.filter((anchor)` — const, line 33
- `const p = (block?.payload ??` — const, line 34
- `const block: PadBlockDto | null = state?.blocks.find((each)` — const, line 51
- `const anchors = anchorsOf(state, request.blockId)` — const, line 52
- `const pieces = useMemo(()` — const, line 53
- `const text = request.text.trim()` — const, line 55
- `const close = (then?: ()` — const, line 56
- `const textRows: Row[] = text ? [` — const, line 60
- `const insertRows: Row[] = [ // §9.2 gives this row the letter k, but an open menu's j/k move the selection (§5.4's matrix): moving // wins, so the row is chosen with ↑↓ ↵ (or alt+d from the pad) and shows no letter.` — const, line 75
- `const rows = [...textRows, ...insertRows,` — const, line 91
- `const runnable = rows.filter((row)` — const, line 92
- `const hub = useListenerHub()` — const, line 94
- `const lifecycle = useWindowLifecycle()` — const, line 96
- `const onKey = (event: KeyboardEvent)` — const, line 102
- `const row = runnable.find((each)` — const, line 118
- `const onDown = (event: MouseEvent)` — const, line 125
- `const offs = [hub.listen("window", "keydown", onKey), hub.listen("window", "mousedown", onDown, true)]` — const, line 128
- `const rowView = (row: Row)` — const, line 135
- `const selected = runnable[index] === row` — const, line 136
- `const at = runnable.indexOf(row)` — const, line 139
- `function PracticeSheet(` — function, line 160
- `let live = true` — let, line 167
- `const first = anchors[0]` — const, line 168
- `const ids = [...new Set(union.sections.flatMap((section)` — const, line 172
- `function messageOf(error: unknown): string` — function, line 203
- `const hub = useListenerHub()` — const, line 218
- `const onKey = (event: KeyboardEvent)` — const, line 220
- `const id = order[index]` — const, line 233
- `const next = [...now]` — const, line 238
- `const next = [...now]` — const, line 245
- `const next = new Set(now)` — const, line 252
- `const titles = new Map(pads.map((pad)` — const, line 266
- `const lines = new Map(pads.map((pad)` — const, line 267
- `const next = new Set(now)` — const, line 284
- `const block = state?.blocks.find((each)` — const, line 302
- `const anchors = anchorsOf(state, blockId)` — const, line 307
- `let live = true` — let, line 309
- `const p = block.payload as Record<string, unknown>` — const, line 311
- `const found = out.problems.find((problem)` — const, line 315
- `const first = anchors[0]` — const, line 319
- `const submit = async (as: "attempt" | "teach_back", item: ()` — const, line 332
- `const sessionId = host.practiceSessionId` — const, line 333
- `const current = host.store.pads[state.pad.padId]?.blocks.find((each)` — const, line 342
- `const practiceItemId = await item()` — const, line 343
- `const reply = await host.api.padSubmitBlock(` — const, line 344

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/desks/pads/PadStackWindow|src/screens/desks/pads/PadStackWindow.tsx]] — import-or-re-export: `ArrangeOverlay`, `MenuRequest`, `PadMenu`, `SubmitSheet`; references `ArrangeOverlay`, `MenuRequest`, `PadMenu`, `SubmitSheet`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `PadBlockDto`, `PadBlockKind`, `PadProvenance`
- [[Reference/Desktop/TypeScript/app/keymap|src/app/keymap.ts]] — import-or-re-export; imports `screenLeavesKey`
- [[Reference/Desktop/TypeScript/screens/desks/lifecycle|src/screens/desks/lifecycle.tsx]] — import-or-re-export; imports `useListenerHub`, `useWindowLifecycle`
- [[Reference/Desktop/TypeScript/screens/desks/pads/host|src/screens/desks/pads/host.ts]] — import-or-re-export; imports `PadsHost`
- [[Reference/Desktop/TypeScript/screens/desks/pads/model|src/screens/desks/pads/model.ts]] — import-or-re-export; imports `PadState`, `isLearnersWords`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- No repository test directly names this source path or a uniquely owned export. `npm run typecheck`, `npm test` and `npm run frontend:build` are the executable frontend gates; add a focused test when changing behavior.

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/screens/desks/pads/PadOverlays.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/desks/pads/PadOverlays.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

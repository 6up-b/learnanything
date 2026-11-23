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
| Source lines | 497 |
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

- `export interface MenuRequest` — interface, line 14
- `export function PadMenu(` — function, line 75
- `export function ArrangeOverlay(` — function, line 221
- `export function stateQuestion(state: StoredTeachBackState | null | undefined, practiceItemId: string): string | null` — function, line 342
- `export function pendingTeachBackQuestion(currentAnswer: string | null | undefined, practiceItemId: string): string | null` — function, line 351
- `export function SubmitSheet(` — function, line 364

## Internal implementation anchors

- `type InsertBlock =` — type, line 28
- `interface Row` — interface, line 30
- `async function insertPiece(host: PadsHost, onInsert: (block: InsertBlock)` — function, line 41
- `const content = await host.api.passageContent(` — const, line 43
- `const span = content.spans.find((each)` — const, line 44
- `function anchorsOf(state: PadState | null, blockId: string | null): Array<` — function, line 62
- `const block = state.blocks.find((each)` — const, line 64
- `const fromLinks = state.anchors.filter((anchor)` — const, line 65
- `const p = (block?.payload ??` — const, line 66
- `const block: PadBlockDto | null = state?.blocks.find((each)` — const, line 88
- `const anchors = anchorsOf(state, request.blockId)` — const, line 89
- `const pieces = useMemo(()` — const, line 90
- `const hub = useListenerHub()` — const, line 92
- `const text = request.text.trim()` — const, line 93
- `const close = (then?: ()` — const, line 94
- `const lifecycle = useWindowLifecycle()` — const, line 99
- `const object: MenuObjectInput | null = request.blockId ?` — const, line 103
- `const textRows: Row[] = text ? [` — const, line 104
- `const insertRows: Row[] = [ // §9.2 gives this row the letter k, but an open menu's j/k move the selection (§5.4's matrix): moving // wins, so the row is chosen with ↑↓ ↵ (or alt+d from the pad) and shows no letter.` — const, line 122
- `const spanId = row.kind === "result" ? row.target?.spanId : undefined` — const, line 135
- `const tailRows: Row[] = [ ...(request.blockId && host.menu ? [` — const, line 143
- `const toRow = (section: MenuRow["section"])` — const, line 147
- `const rows: MenuRow[] = [...textRows.map(toRow("verb")), ...insertRows.map(toRow("insert")), ...tailRows.map(toRow("tail"))]` — const, line 152
- `function PracticeSheet(` — function, line 173
- `let live = true` — let, line 180
- `const first = anchors[0]` — const, line 181
- `const ids = [...new Set(union.sections.flatMap((section)` — const, line 185
- `function messageOf(error: unknown): string` — function, line 216
- `const hub = useListenerHub()` — const, line 231
- `const onKey = (event: KeyboardEvent)` — const, line 233
- `const id = order[index]` — const, line 246
- `const next = [...now]` — const, line 251
- `const next = [...now]` — const, line 258
- `const next = new Set(now)` — const, line 265
- `const titles = new Map(pads.map((pad)` — const, line 279
- `const lines = new Map(pads.map((pad)` — const, line 280
- `const next = new Set(now)` — const, line 297
- `interface FrozenSubmission` — interface, line 315
- `const FROZEN = new WeakMap<object, Map<string, FrozenSubmission>>()` — const, line 322
- `function frozenFor(store: object): Map<string, FrozenSubmission>` — function, line 324
- `let map = FROZEN.get(store)` — let, line 325
- `interface TeachBackTurn` — interface, line 334
- `type StoredTeachBackState =` — type, line 339
- `const item = state.practice_item_id ?? state.practiceItemId` — const, line 344
- `const last = state.turns?.[state.turns.length - 1]` — const, line 346
- `const envelope = JSON.parse(currentAnswer) as` — const, line 354
- `const block = state?.blocks.find((each)` — const, line 365
- `const anchors = anchorsOf(state, blockId)` — const, line 372
- `let live = true` — let, line 374
- `const p = block.payload as Record<string, unknown>` — const, line 376
- `const found = out.problems.find((problem)` — const, line 380
- `const first = anchors[0]` — const, line 384
- `const padId = state.pad.padId` — const, line 397
- `const submit = async (as: "attempt" | "teach_back", key: string, item: ()` — const, line 399
- `const sessionId = host.practiceSessionId` — const, line 400
- `const frozen = frozenFor(host.store)` — const, line 407
- `const slot = `$` — const, line 408
- `const current = host.store.pads[padId]?.blocks.find((each)` — const, line 412
- `let request = frozen.get(slot)` — let, line 413
- `const answered = await host.api.padSubmitBlock(` — const, line 419
- `const entry = answered.entry as` — const, line 425
- `let question: string | null = entry && entry.done === false ? entry.questionMd ?? null : null` — let, line 426
- `const session = await host.api.getSession(sessionId).catch(()` — const, line 431
- `const answerTurn = async (finish: boolean)` — const, line 448
- `const sessionId = host.practiceSessionId` — const, line 449
- `const next = await host.api.submitTeachBackTurn(` — const, line 454

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/desks/pads/PadStackWindow|src/screens/desks/pads/PadStackWindow.tsx]] — import-or-re-export: `ArrangeOverlay`, `MenuRequest`, `PadMenu`, `SubmitSheet`; references `ArrangeOverlay`, `MenuRequest`, `PadMenu`, `SubmitSheet`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `MenuObjectInput`, `PadBlockDto`, `PadBlockKind`, `PadProvenance`
- [[Reference/Desktop/TypeScript/app/keymap|src/app/keymap.ts]] — import-or-re-export; imports `screenLeavesKey`
- [[Reference/Desktop/TypeScript/screens/desks/lifecycle|src/screens/desks/lifecycle.tsx]] — import-or-re-export; imports `useListenerHub`, `useWindowLifecycle`
- [[Reference/Desktop/TypeScript/screens/desks/menu/ContextMenu|src/screens/desks/menu/ContextMenu.tsx]] — import-or-re-export; imports `ContextMenu`
- [[Reference/Desktop/TypeScript/screens/desks/menu/model|src/screens/desks/menu/model.ts]] — import-or-re-export; imports `MenuRow`
- [[Reference/Desktop/TypeScript/screens/desks/notebook/menuBridge|src/screens/desks/notebook/menuBridge.ts]] — import-or-re-export; imports `MARIMO_CELL_INSERT`, `MARIMO_CELL_ROW`
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

---
title: "Desktop module · src/screens/desks/keys/router.ts"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.desks.keys.router"
language: "TypeScript"
area: "TypeScript/screens/desks/keys"
source_path: "apps/learnloop-tauri/src/screens/desks/keys/router.ts"
source_paths:
  - "apps/learnloop-tauri/src/screens/desks/keys/router.ts"
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

# `src/screens/desks/keys/router.ts`

Area: [[Reference/Desktop/TypeScript/screens/desks/keys/_area|TypeScript/screens/desks/keys]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides `DeskScope`, `SCOPE_ORDER`, `DeskAction`, `Chord` and related exports within the desktop's TypeScript/screens/desks/keys ownership area.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/desks/keys/router.ts](../../../../../../../../apps/learnloop-tauri/src/screens/desks/keys/router.ts) |
| Source lines | 372 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/desks/keys/_area|TypeScript/screens/desks/keys]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/DeskShell|src/screens/desks/DeskShell.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/keys/router|src/screens/desks/keys/router.ts]]

## Public API

- `export type DeskScope = "notebook" | "check" | "menu" | "typing" | "arrange" | "strip" | "pen" | "overview" | "focus" | "reading"` — type, line 9
- `export const SCOPE_ORDER: readonly DeskScope[] = ["notebook", "check", "menu", "typing", "arrange", "strip", "pen", "overview", "focus", "reading"]` — const, line 12
- `export type DeskAction = |` — type, line 14
- `export interface Chord` — interface, line 50
- `export interface DeskBinding` — interface, line 60
- `export const DESK_BINDINGS: readonly DeskBinding[] = [ alt("move.left", "alt+h", "window left", "KeyH",` — const, line 88
- `export interface ScopeState` — interface, line 154
- `export function openScopes(state: ScopeState): DeskScope[]` — function, line 172
- `export interface KeyLike` — interface, line 176
- `export interface Resolution` — interface, line 224
- `export const SELECTION_SHORTCUTS: ReadonlySet<string> = new Set(["reading.companion", "reading.companion-dock", "reading.search"])` — const, line 235
- `export function resolveKey(event: KeyLike, state: ScopeState, mods:` — function, line 237
- `export class ModifierTracker` — class, line 258
- `export const WHICH_KEY_HOLD_MS = 400` — const, line 285
- `export interface Timers` — interface, line 287
- `export const REAL_TIMERS: Timers =` — const, line 293
- `export type AltOutcome = "tap" | "hold" | "chord" | "cancelled"` — type, line 300
- `export class BareAltTracker` — class, line 305
- `export function isTypingTarget(target: EventTarget | null): boolean` — function, line 368

## Internal implementation anchors

- `const ALT_TYPING: readonly DeskScope[] = ["typing", "focus", "reading"]` — const, line 76
- `const READING: readonly DeskScope[] = ["reading"]` — const, line 77
- `function alt(id: string, keys: string, label: string, code: string, action: DeskAction, scopes: readonly DeskScope[], extra: Partial<DeskBinding> =` — function, line 79
- `function bare(id: string, keys: string, label: string, key: string, action: DeskAction, scopes: readonly DeskScope[], extra: Partial<DeskBinding> =` — function, line 83
- `const letter = "hjkl"[index]` — const, line 131
- `const arrow =` — const, line 132
- `function chordMatches(chord: Chord, event: KeyLike, mods:` — function, line 185
- `const altDown = mods.alt` — const, line 186
- `const ctrlDown = mods.ctrl || event.metaKey` — const, line 187
- `function passesThrough(scope: DeskScope, binding: DeskBinding): boolean` — function, line 199
- `const unclaimed = resolveKey(event, rest, mods)` — const, line 240
- `const matching = DESK_BINDINGS.filter((binding)` — const, line 244
- `const owned = matching.find((binding)` — const, line 247
- `const held = this.held || this.timers.now() - this.pressedAt >= WHICH_KEY_HOLD_MS` — const, line 336
- `const outcome: AltOutcome = this.spoiled ?? (held ? "hold" : "tap")` — const, line 337
- `const wasHeld = this.held` — const, line 348

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/fixtures/desks/harness|src/fixtures/desks/harness.tsx]] — import-or-re-export: `REAL_TIMERS`; references `REAL_TIMERS`
- [[Reference/Desktop/TypeScript/screens/desks/DeskShell|src/screens/desks/DeskShell.tsx]] — import-or-re-export: `BareAltTracker`, `DESK_BINDINGS`, `DeskAction`, `ModifierTracker`, `REAL_TIMERS`, `Timers`, `isTypingTarget`, `resolveKey`; references `BareAltTracker`, `DESK_BINDINGS`, `DeskAction`, `ModifierTracker`, `REAL_TIMERS`, `Timers`, `isTypingTarget`, `resolveKey`
- [[Reference/Desktop/TypeScript/screens/desks/companion/Companion|src/screens/desks/companion/Companion.tsx]] — import-or-re-export: `Timers`; references `Timers`
- [[Reference/Desktop/TypeScript/screens/desks/goal/GoalLayer|src/screens/desks/goal/GoalLayer.tsx]] — import-or-re-export: `Timers`; references `Timers`
- [[Reference/Desktop/TypeScript/screens/desks/goal/controller|src/screens/desks/goal/controller.ts]] — import-or-re-export: `Timers`; references `Timers`
- [[Reference/Desktop/TypeScript/screens/desks/search/SearchPanel|src/screens/desks/search/SearchPanel.tsx]] — import-or-re-export: `Timers`; references `Timers`
- [[Reference/Desktop/TypeScript/screens/desks/store|src/screens/desks/store.ts]] — import-or-re-export: `Timers`; references `Timers`
- [[Reference/Desktop/TypeScript/screens/reader/bareAlt|src/screens/reader/bareAlt.ts]] — import-or-re-export: `WHICH_KEY_HOLD_MS`; references `WHICH_KEY_HOLD_MS`

## Dependencies

### Desktop source modules

No local TypeScript/TSX or Rust module dependency was detected.

### Assets, platform, and third-party dependencies

No explicit asset, standard-library, package, or crate dependency was detected.

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/desks/store.test.ts](../../../../../../../../apps/learnloop-tauri/src/screens/desks/store.test.ts) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/desks/search/SearchPanel.test.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/desks/search/SearchPanel.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/desks/pen/inkPad.test.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/desks/pen/inkPad.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/desks/pads/PadStackWindow.test.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/desks/pads/PadStackWindow.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/desks/keys/router.test.ts](../../../../../../../../apps/learnloop-tauri/src/screens/desks/keys/router.test.ts) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/desks/goal/components.test.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/desks/goal/components.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/desks/companion/Companion.test.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/desks/companion/Companion.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/app/keymap.test.ts](../../../../../../../../apps/learnloop-tauri/src/app/keymap.test.ts) — vitest test: imports and executes this module under jsdom (`npm test`).

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/screens/desks/keys/router.ts](../../../../../../../../apps/learnloop-tauri/src/screens/desks/keys/router.ts) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

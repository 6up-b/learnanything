---
title: "Desktop module · src/screens/desks/notebook/bridge.ts"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.desks.notebook.bridge"
language: "TypeScript"
area: "TypeScript/screens/desks/notebook"
source_path: "apps/learnloop-tauri/src/screens/desks/notebook/bridge.ts"
source_paths:
  - "apps/learnloop-tauri/src/screens/desks/notebook/bridge.ts"
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

# `src/screens/desks/notebook/bridge.ts`

Area: [[Reference/Desktop/TypeScript/screens/desks/notebook/_area|TypeScript/screens/desks/notebook]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides `BridgeKind`, `BridgeRect`, `BridgeMessage`, `BRIDGE_TEXT_MAX` and related exports within the desktop's TypeScript/screens/desks/notebook ownership area.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/desks/notebook/bridge.ts](../../../../../../../../apps/learnloop-tauri/src/screens/desks/notebook/bridge.ts) |
| Source lines | 113 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/desks/notebook/_area|TypeScript/screens/desks/notebook]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/DeskShell|src/screens/desks/DeskShell.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/notebook/bridge|src/screens/desks/notebook/bridge.ts]]

## Public API

- `export type BridgeKind = "companion" | "menu" | "click" | "escape"` — type, line 9
- `export interface BridgeRect` — interface, line 11
- `export type BridgeMessage = |` — type, line 18
- `export const BRIDGE_TEXT_MAX = 4000` — const, line 25
- `export function parseBridgeMessage(data: unknown): BridgeMessage | null` — function, line 55
- `export function frameOrigin(frameUrl: string): string | null` — function, line 75
- `export interface BridgeSource` — interface, line 84
- `export function fromFrame(event: Pick<MessageEvent, "source" | "origin">, frame: BridgeSource): boolean` — function, line 92
- `export function toPage(message: BridgeMessage, frameBox:` — function, line 101

## Internal implementation anchors

- `const KEYS: Record<BridgeKind, readonly string[]> =` — const, line 27
- `function plainObject(value: unknown): value is Record<string, unknown>` — function, line 34
- `const proto = Object.getPrototypeOf(value)` — const, line 36
- `function finite(value: unknown): value is number` — function, line 40
- `function rectOf(value: unknown): BridgeRect | null | undefined` — function, line 44
- `const keys = Object.keys(value).sort().join(",")` — const, line 47
- `const kind = data.ll` — const, line 57
- `const keys = Object.keys(data)` — const, line 59
- `const text = data.text` — const, line 62
- `const rect = rectOf(data.rect)` — const, line 64
- `const url = new URL(frameUrl)` — const, line 77
- `function clamp(value: number, low: number, high: number): number` — function, line 96
- `const rect = (r: BridgeRect | null): BridgeRect | null` — const, line 102
- `const x = clamp(r.x, 0, frameBox.width)` — const, line 104
- `const y = clamp(r.y, 0, frameBox.height)` — const, line 105

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/fixtures/desks/harness|src/fixtures/desks/harness.tsx]] — import-or-re-export: `BridgeMessage`; references `BridgeMessage`
- [[Reference/Desktop/TypeScript/screens/desks/DeskShell|src/screens/desks/DeskShell.tsx]] — import-or-re-export: `BridgeMessage`; references `BridgeMessage`
- [[Reference/Desktop/TypeScript/screens/desks/notebook/NotebookFrame|src/screens/desks/notebook/NotebookFrame.tsx]] — import-or-re-export: `BridgeMessage`, `frameOrigin`, `fromFrame`, `parseBridgeMessage`, `toPage`; references `BridgeMessage`, `frameOrigin`, `fromFrame`, `parseBridgeMessage`, `toPage`
- [[Reference/Desktop/TypeScript/screens/desks/notebook/menuBridge|src/screens/desks/notebook/menuBridge.ts]] — import-or-re-export: `BridgeMessage`; references `BridgeMessage`

## Dependencies

### Desktop source modules

No local TypeScript/TSX or Rust module dependency was detected.

### Assets, platform, and third-party dependencies

No explicit asset, standard-library, package, or crate dependency was detected.

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/desks/notebook/bridge.test.ts](../../../../../../../../apps/learnloop-tauri/src/screens/desks/notebook/bridge.test.ts) — vitest test: imports and executes this module under jsdom (`npm test`).

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/screens/desks/notebook/bridge.ts](../../../../../../../../apps/learnloop-tauri/src/screens/desks/notebook/bridge.ts) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

---
title: "Desktop module · src/screens/desks/pen/recognizer.ts"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.desks.pen.recognizer"
language: "TypeScript"
area: "TypeScript/screens/desks/pen"
source_path: "apps/learnloop-tauri/src/screens/desks/pen/recognizer.ts"
source_paths:
  - "apps/learnloop-tauri/src/screens/desks/pen/recognizer.ts"
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

# `src/screens/desks/pen/recognizer.ts`

Area: [[Reference/Desktop/TypeScript/screens/desks/pen/_area|TypeScript/screens/desks/pen]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides `Point`, `Box`, `LineBox`, `RecognizerPage` and related exports within the desktop's TypeScript/screens/desks/pen ownership area.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/desks/pen/recognizer.ts](../../../../../../../../apps/learnloop-tauri/src/screens/desks/pen/recognizer.ts) |
| Source lines | 128 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/desks/pen/_area|TypeScript/screens/desks/pen]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/DeskShell|src/screens/desks/DeskShell.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/windows/SourceWindow|src/screens/desks/windows/SourceWindow.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/pen/PenLayer|src/screens/desks/pen/PenLayer.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/pen/recognizer|src/screens/desks/pen/recognizer.ts]]

## Public API

- `export interface Point` — interface, line 19
- `export interface Box` — interface, line 24
- `export interface LineBox` — interface, line 34
- `export interface RecognizerPage` — interface, line 40
- `export type StrokeKind = "lasso" | "bracket" | "note" | "strike" | "underline" | "ink"` — type, line 47
- `export interface Recognition` — interface, line 49
- `export const RECOGNIZER =` — const, line 56
- `export function boxOf(points: readonly Point[]): Box` — function, line 73
- `export function isClosedLoop(points: readonly Point[], box: Box = boxOf(points)): boolean` — function, line 83
- `export function inMargin(box: Box, column:` — function, line 90
- `export function throughTheMiddle(box: Box, page: RecognizerPage): boolean` — function, line 96
- `export function recognize(points: readonly Point[], page: RecognizerPage): Recognition | null` — function, line 106
- `export const RECOGNIZED_AS: Record<Exclude<StrokeKind, "ink">, string> =` — const, line 122

## Internal implementation anchors

- `const xs = points.map((p)` — const, line 74
- `const ys = points.map((p)` — const, line 75
- `const x0 = Math.min(...xs)` — const, line 76
- `const x1 = Math.max(...xs)` — const, line 77
- `const y0 = Math.min(...ys)` — const, line 78
- `const y1 = Math.max(...ys)` — const, line 79
- `const first = points[0]` — const, line 84
- `const last = points[points.length - 1]` — const, line 85
- `const mid = (box.y0 + box.y1) / 2` — const, line 97
- `const cx = box.x0 + box.w / 2` — const, line 98
- `const above = page.lineAt(cx, mid - RECOGNIZER.lineProbeAbove)` — const, line 99
- `const at = page.lineAt(cx, mid)` — const, line 102
- `const box = boxOf(points)` — const, line 108
- `const margin = inMargin(box, page.textColumn())` — const, line 110
- `const mid = (box.y0 + box.y1) / 2` — const, line 114

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/desks/pen/PenLayer|src/screens/desks/pen/PenLayer.tsx]] — import-or-re-export: `Box`, `Point`, `RECOGNIZED_AS`, `StrokeKind`, `boxOf`, `recognize`; references `Box`, `Point`, `RECOGNIZED_AS`, `StrokeKind`, `boxOf`, `recognize`
- [[Reference/Desktop/TypeScript/screens/desks/pen/geometry|src/screens/desks/pen/geometry.ts]] — import-or-re-export: `Box`, `LineBox`, `Point`, `RECOGNIZER`, `RecognizerPage`; references `Box`, `LineBox`, `Point`, `RECOGNIZER`, `RecognizerPage`

## Dependencies

### Desktop source modules

No local TypeScript/TSX or Rust module dependency was detected.

### Assets, platform, and third-party dependencies

No explicit asset, standard-library, package, or crate dependency was detected.

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/desks/pen/recognizer.test.ts](../../../../../../../../apps/learnloop-tauri/src/screens/desks/pen/recognizer.test.ts) — vitest test: imports and executes this module under jsdom (`npm test`).
- [tests/test_re0_capture.py](../../../../../../../../tests/test_re0_capture.py) — cross-boundary name contract: references uniquely owned exported name `Recognition`; it does **not** directly execute this source module.

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/screens/desks/pen/recognizer.ts](../../../../../../../../apps/learnloop-tauri/src/screens/desks/pen/recognizer.ts) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

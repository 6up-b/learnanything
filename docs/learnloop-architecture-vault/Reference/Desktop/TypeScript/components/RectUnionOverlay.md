---
title: "Desktop module · src/components/RectUnionOverlay.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.components.RectUnionOverlay"
language: "TypeScript"
area: "TypeScript/components"
source_path: "apps/learnloop-tauri/src/components/RectUnionOverlay.tsx"
source_paths:
  - "apps/learnloop-tauri/src/components/RectUnionOverlay.tsx"
source_commit: "0e91c7ba1b7ff32d5d093dd62826890b70445d3f"
source_commit_timestamp: "2026-08-03T22:04:38-04:00"
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

# `src/components/RectUnionOverlay.tsx`

Area: [[Reference/Desktop/TypeScript/components/_area|TypeScript/components]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides the reusable `RectUnionOverlay` interaction surface used by one or more desktop workflows.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/components/RectUnionOverlay.tsx](../../../../../../apps/learnloop-tauri/src/components/RectUnionOverlay.tsx) |
| Source lines | 88 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/components/_area|TypeScript/components]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `0e91c7ba1b7ff32d5d093dd62826890b70445d3f` |
| Commit timestamp | `2026-08-03T22:04:38-04:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]] → [[Reference/Desktop/TypeScript/components/RectUnionOverlay|src/components/RectUnionOverlay.tsx]]

## Public API

- `export function rectUnionPaths(rects: number[][]): RectUnionPaths | null` — function, line 23
- `export function RectUnionOverlay(` — function, line 59

## Internal implementation anchors

- `interface RectUnionPaths` — interface, line 3
- `function normalizedRects(rects: number[][]): number[][]` — function, line 8
- `const normalized = normalizedRects(rects)` — const, line 24
- `const xs = [...new Set(normalized.flatMap((rect)` — const, line 26
- `const ys = [...new Set(normalized.flatMap((rect)` — const, line 27
- `const occupied = Array.from(` — const, line 28
- `const cx = (xs[column] + xs[column + 1]) / 2` — const, line 30
- `const cy = (ys[row] + ys[row + 1]) / 2` — const, line 31
- `const outline: string[] = []` — const, line 37
- `const x0 = xs[column]` — const, line 41
- `const x1 = xs[column + 1]` — const, line 42
- `const y0 = ys[row]` — const, line 43
- `const y1 = ys[row + 1]` — const, line 44
- `const paths = useMemo(()` — const, line 60

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/components/PdfReaderPane|src/components/PdfReaderPane.tsx]] — import-or-re-export: `RectUnionOverlay`; references `RectUnionOverlay`
- [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]] — import-or-re-export: `RectUnionOverlay`; references `RectUnionOverlay`

## Dependencies

### Desktop source modules

No local TypeScript/TSX or Rust module dependency was detected.

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- No repository test directly names this source path or a uniquely owned export. `npm run typecheck` and `npm run frontend:build` are the executable frontend gates; add a focused test when changing behavior.

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/components/RectUnionOverlay.tsx](../../../../../../apps/learnloop-tauri/src/components/RectUnionOverlay.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

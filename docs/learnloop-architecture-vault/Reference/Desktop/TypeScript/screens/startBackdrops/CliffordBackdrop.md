---
title: "Desktop module · src/screens/startBackdrops/CliffordBackdrop.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.startBackdrops.CliffordBackdrop"
language: "TypeScript"
area: "TypeScript/screens/startBackdrops"
source_path: "apps/learnloop-tauri/src/screens/startBackdrops/CliffordBackdrop.tsx"
source_paths:
  - "apps/learnloop-tauri/src/screens/startBackdrops/CliffordBackdrop.tsx"
source_commit: "e3c6871bd2ed939ab9dcdf98d0ae9bdb19ded1ec"
source_commit_timestamp: "2026-07-23T15:53:16-05:00"
source_worktree_state: "clean"
activation_kind: "entry-reachable build graph"
activation_evidence: "Imported through StartScreen's supported optional backdrop paths reachable from src/main.tsx."
generated: true
generated_at: "2026-08-18"
tags:
  - "learnloop/docs"
  - "learnloop/reference/module"
  - "learnloop/desktop"
  - "learnloop/desktop/typescript"
  - "refactor/active"
---

# `src/screens/startBackdrops/CliffordBackdrop.tsx`

Area: [[Reference/Desktop/TypeScript/screens/startBackdrops/_area|TypeScript/screens/startBackdrops]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Implements the `CliffordBackdrop` start-screen visualization or its rendering support.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/startBackdrops/CliffordBackdrop.tsx](../../../../../../../apps/learnloop-tauri/src/screens/startBackdrops/CliffordBackdrop.tsx) |
| Source lines | 122 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/startBackdrops/_area|TypeScript/screens/startBackdrops]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `e3c6871bd2ed939ab9dcdf98d0ae9bdb19ded1ec` |
| Commit timestamp | `2026-07-23T15:53:16-05:00` |

## Activation and status evidence

> [!success] ACTIVE
> Imported through StartScreen's supported optional backdrop paths reachable from src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/StartScreen|src/screens/StartScreen.tsx]] → [[Reference/Desktop/TypeScript/screens/startBackdrops/CliffordBackdrop|src/screens/startBackdrops/CliffordBackdrop.tsx]]

## Public API

- `export function CliffordBackdrop()` — function, line 13

## Internal implementation anchors

- `const POINTS_PER_FRAME = 1500` — const, line 10
- `const STATIC_POINTS = 40_000` — const, line 11
- `const ref = useRef<HTMLCanvasElement>(null)` — const, line 14
- `const canvas = ref.current` — const, line 17
- `const ctx = canvas.getContext("2d")` — const, line 19
- `const P = readPaletteColors()` — const, line 22
- `const bgDeep = rgba(mixRgb(P.bg, BLACK, 0.55), 1)` — const, line 23
- `const dotColors = [rgba(P.amber, 0.6), rgba(P.cyan, 0.45), rgba(P.pink, 0.45)]` — const, line 24
- `const reduce = prefersReducedMotion()` — const, line 25
- `let raf = 0` — let, line 27
- `let dpr = Math.min(window.devicePixelRatio || 1, 2)` — let, line 28
- `let x = 0.1` — let, line 29
- `let y = 0` — let, line 30
- `function params(t: number)` — function, line 32
- `function plotPoints(t: number, count: number)` — function, line 41
- `const w = canvas!.width / dpr` — const, line 42
- `const h = canvas!.height / dpr` — const, line 43
- `const scale = Math.min(w, h) / 4.8` — const, line 46
- `const cx = w / 2` — const, line 47
- `const cy = h / 2` — const, line 48
- `const nx = Math.sin(a * y) + c * Math.cos(a * x)` — const, line 52
- `const ny = Math.sin(b * x) + d * Math.cos(b * y)` — const, line 53
- `function prime()` — function, line 70
- `const w = canvas!.width / dpr` — const, line 71
- `const h = canvas!.height / dpr` — const, line 72
- `function resize()` — function, line 78
- `const rect = canvas!.getBoundingClientRect()` — const, line 79
- `const ro = new ResizeObserver(()` — const, line 91
- `function frame(ts: number)` — function, line 100
- `const w = canvas!.width / dpr` — const, line 101
- `const h = canvas!.height / dpr` — const, line 102

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/StartScreen|src/screens/StartScreen.tsx]] — import-or-re-export: `CliffordBackdrop`; references `CliffordBackdrop`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/screens/startBackdrops/shared|src/screens/startBackdrops/shared.ts]] — import-or-re-export; imports `BLACK`, `mixRgb`, `prefersReducedMotion`, `readPaletteColors`, `rgba`

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

1. Modify [apps/learnloop-tauri/src/screens/startBackdrops/CliffordBackdrop.tsx](../../../../../../../apps/learnloop-tauri/src/screens/startBackdrops/CliffordBackdrop.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

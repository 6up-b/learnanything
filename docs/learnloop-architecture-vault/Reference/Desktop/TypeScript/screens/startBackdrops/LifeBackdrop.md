---
title: "Desktop module · src/screens/startBackdrops/LifeBackdrop.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.startBackdrops.LifeBackdrop"
language: "TypeScript"
area: "TypeScript/screens/startBackdrops"
source_path: "apps/learnloop-tauri/src/screens/startBackdrops/LifeBackdrop.tsx"
source_paths:
  - "apps/learnloop-tauri/src/screens/startBackdrops/LifeBackdrop.tsx"
source_commit: "971d7c274e09873d726d43578cd080e4d8865571"
source_commit_timestamp: "2026-07-27T06:01:19-04:00"
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

# `src/screens/startBackdrops/LifeBackdrop.tsx`

Area: [[Reference/Desktop/TypeScript/screens/startBackdrops/_area|TypeScript/screens/startBackdrops]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Implements the `LifeBackdrop` start-screen visualization or its rendering support.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/startBackdrops/LifeBackdrop.tsx](../../../../../../../apps/learnloop-tauri/src/screens/startBackdrops/LifeBackdrop.tsx) |
| Source lines | 227 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/startBackdrops/_area|TypeScript/screens/startBackdrops]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `971d7c274e09873d726d43578cd080e4d8865571` |
| Commit timestamp | `2026-07-27T06:01:19-04:00` |

## Activation and status evidence

> [!success] ACTIVE
> Imported through StartScreen's supported optional backdrop paths reachable from src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/StartScreen|src/screens/StartScreen.tsx]] → [[Reference/Desktop/TypeScript/screens/startBackdrops/LifeBackdrop|src/screens/startBackdrops/LifeBackdrop.tsx]]

## Public API

- `export function LifeBackdrop(` — function, line 20

## Internal implementation anchors

- `const STEP_MS = 75` — const, line 14
- `const SOUP_DENSITY = 0.28` — const, line 15
- `const RESEED_AFTER_MS = 90_000` — const, line 16
- `const GLYPHS = ":*#@"` — const, line 18
- `const containerRef = useRef<HTMLDivElement>(null)` — const, line 21
- `const canvasRef = useRef<HTMLCanvasElement>(null)` — const, line 22
- `const container = containerRef.current` — const, line 25
- `const canvas = canvasRef.current` — const, line 26
- `const ctx = canvas.getContext("2d")` — const, line 28
- `const reduce = prefersReducedMotion()` — const, line 31
- `let cols = 80` — let, line 33
- `let rows = 40` — let, line 34
- `let width = 0` — let, line 35
- `let height = 0` — let, line 36
- `let dpr = Math.min(window.devicePixelRatio || 1, 2)` — let, line 37
- `let atlas: MonospaceGlyphAtlas | null = null` — let, line 38
- `let cells = new Uint16Array(0)` — let, line 39
- `let oldCode = 0` — let, line 40
- `let matureCode = 0` — let, line 41
- `let youngCode = 0` — let, line 42
- `let newbornCode = 0` — let, line 43
- `let grid = new Uint8Array(0)` — let, line 44
- `let next = new Uint8Array(0)` — let, line 45
- `let hashes: number[] = []` — let, line 46
- `let seededAt = 0` — let, line 47
- `let prevCols = 0` — let, line 48
- `let prevRows = 0` — let, line 49
- `function seed()` — function, line 51
- `function alloc()` — function, line 59
- `const fresh = new Uint8Array(cols * rows)` — const, line 60
- `const copyCols = Math.min(prevCols, cols)` — const, line 64
- `const copyRows = Math.min(prevRows, rows)` — const, line 65
- `function gridHash(): number` — function, line 88
- `let h = 0x811c9dc5` — let, line 90
- `function step()` — function, line 98
- `let population = 0` — let, line 99
- `const up = ((y - 1 + rows) % rows) * cols` — const, line 101
- `const mid = y * cols` — const, line 102
- `const down = ((y + 1) % rows) * cols` — const, line 103
- `const l = (x - 1 + cols) % cols` — const, line 105
- `const r = (x + 1) % cols` — const, line 106
- `const n = (grid[up + l] > 0 ? 1 : 0) + (grid[up + x] > 0 ? 1 : 0) + (grid[up + r] > 0 ? 1 : 0) + (grid[mid + l] > 0 ? 1 : 0) + (grid[mid + r] > 0 ? 1 : 0) + (grid[down + l] > 0 ? 1 : 0) + (grid[down + x] > 0 ? 1 : 0) + (grid[down + r] > 0 ? 1 : 0)` — const, line 107
- `const alive = grid[mid + x] > 0` — const, line 111
- `const swap = grid` — const, line 120
- `const h = gridHash()` — const, line 126
- `const stagnant = hashes.length >= 2 && (h === hashes[hashes.length - 1] || h === hashes[hashes.length - 2])` — const, line 127
- `const collapsed = population < grid.length * 0.02` — const, line 130
- `const expired = performance.now() - seededAt > RESEED_AFTER_MS` — const, line 131
- `function rebuildAtlas()` — function, line 135
- `function renderFrame()` — function, line 149
- `const age = grid[i]` — const, line 151
- `function resize()` — function, line 163
- `const rect = container!.getBoundingClientRect()` — const, line 164
- `const nextDpr = Math.min(window.devicePixelRatio || 1, 2)` — const, line 167
- `const dprChanged = nextDpr !== dpr` — const, line 168
- `const ro = new ResizeObserver(()` — const, line 185
- `let raf = 0` — let, line 197
- `let last = 0` — let, line 198
- `function frame(ts: number)` — function, line 199

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/StartScreen|src/screens/StartScreen.tsx]] — import-or-re-export: `LifeBackdrop`; references `LifeBackdrop`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/screens/startBackdrops/glyphAtlas|src/screens/startBackdrops/glyphAtlas.ts]] — import-or-re-export; imports `FULLSCREEN_CANVAS_STYLE`, `MonospaceGlyphAtlas`, `readAmberAtlasPalette`
- [[Reference/Desktop/TypeScript/screens/startBackdrops/shared|src/screens/startBackdrops/shared.ts]] — import-or-re-export; imports `CHAR_H`, `CHAR_W`, `prefersReducedMotion`

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

1. Modify [apps/learnloop-tauri/src/screens/startBackdrops/LifeBackdrop.tsx](../../../../../../../apps/learnloop-tauri/src/screens/startBackdrops/LifeBackdrop.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
